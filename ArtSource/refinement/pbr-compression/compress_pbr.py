#!/usr/bin/env python3
"""Private, hash-pinned GLB image-only UASTC candidate builder.

Never publishes app/library assets. Unsupported or ambiguous input fails closed.
"""
import argparse
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import tempfile

from PIL import Image
import PIL
import numpy as np

BASIS = "KHR_texture_basisu"
SETTINGS = {
    "codec": "uastc", "uastc_quality": 3, "threads": 2,
    "zstd": 18, "mipmap_filter": "lanczos4", "full_mips": True,
    "normal_mode": False, "normalize": False, "rdo": False,
    "orientation": "top-left", "pixel_resize": False,
    "mip_source": {"same_axis": "ktx-cli-generate-mipmap", "different_axes": "explicit-axis-lanczos4-v1"},
    "axis_mips": {"version": 1, "precision": "float64", "support": 4,
                  "centers": "half-pixel", "antialias": "support-scaled-by-source/target",
                  "sequence": "S-then-T-recursive-unquantized-clipped-linear",
                  "color_filter": "IEC-sRGB-EOTF-linear-filter-OETF", "alpha_filter": "linear-straight",
                  "quantization": "clip-0-1-round-half-up-uint8", "top": "original-decoded-pixels"},
}
WRAPS = {10497: "wrap", 33071: "clamp"}
ENCODER_SHA = "abd30109cbf84859b2f34951f7967e801111abadaac588468d98ed075100ad37"
LIBKTX_SHA = "bd26f0747b7a800384b7b3c9221dafeb3943ef565a560ab98238cade597c0947"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_glb(data):
    require(len(data) >= 28, "truncated GLB")
    magic, version, length = struct.unpack_from("<III", data)
    require(magic == 0x46546C67 and version == 2 and length == len(data), "invalid GLB header")
    chunks, offset = [], 12
    while offset < len(data):
        require(offset + 8 <= len(data), "truncated chunk header")
        size, kind = struct.unpack_from("<II", data, offset)
        require(size % 4 == 0 and offset + 8 + size <= len(data), "invalid chunk size")
        chunks.append((kind, data[offset + 8:offset + 8 + size]))
        offset += 8 + size
    require([c[0] for c in chunks] == [0x4E4F534A, 0x004E4942], "require JSON and one BIN chunk only")
    doc = json.loads(chunks[0][1])
    require(doc.get("asset", {}).get("version") == "2.0", "require glTF 2.0")
    buffers = doc.get("buffers", [])
    require(len(buffers) == 1 and "uri" not in buffers[0], "require one embedded buffer")
    require(0 <= len(chunks[1][1]) - buffers[0]["byteLength"] <= 3, "buffer length mismatch")
    binary = chunks[1][1][:buffers[0]["byteLength"]]
    for bv in doc.get("bufferViews", []):
        start = bv.get("byteOffset", 0)
        require(bv.get("buffer", 0) == 0 and start >= 0 and bv["byteLength"] > 0
                and start + bv["byteLength"] <= len(binary), "invalid bufferView")
    return doc, binary


def write_glb(doc, binary):
    doc = copy.deepcopy(doc)
    doc["buffers"][0]["byteLength"] = len(binary)
    js = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(binary))
            + struct.pack("<II", len(js), 0x4E4F534A) + js
            + struct.pack("<II", len(binary), 0x004E4942) + binary)


def view_bytes(doc, binary, index):
    v = doc["bufferViews"][index]
    start = v.get("byteOffset", 0)
    return binary[start:start + v["byteLength"]]


def image_contracts(doc):
    """Classify every image from real material slots, including sampler wrap."""
    require(not doc.get("extensionsUsed") and not doc.get("extensionsRequired"),
            "input glTF extensions require explicit support; do not infer extension texture roles")
    images, textures = doc.get("images", []), doc.get("textures", [])
    require(images and textures, "no textures")
    roles = [set() for _ in textures]
    for material in doc.get("materials", []):
        require(not material.get("extensions"), "unsupported material extension")
        slots = [(material.get("pbrMetallicRoughness", {}), "baseColorTexture", "baseColor", "srgb"),
                 (material.get("pbrMetallicRoughness", {}), "metallicRoughnessTexture", "metallicRoughness", "linear"),
                 (material, "normalTexture", "normal", "linear"),
                 (material, "occlusionTexture", "occlusion", "linear"),
                 (material, "emissiveTexture", "emissive", "srgb")]
        for owner, key, role, domain in slots:
            if key in owner:
                index = owner[key]["index"]
                require(type(index) is int and 0 <= index < len(textures), "invalid material texture index")
                require(not owner[key].get("extensions"), "unsupported textureInfo extension")
                roles[index].add((role, domain))
    contracts = [{"roles": set(), "domains": set(), "wraps": set()} for _ in images]
    for ti, texture in enumerate(textures):
        require(roles[ti], f"unclassified/unreferenced texture {ti}")
        require(not texture.get("extensions"), "input texture extension unsupported")
        source = texture.get("source")
        require(type(source) is int and 0 <= source < len(images), "invalid texture source")
        sampler_index = texture.get("sampler")
        if sampler_index is None:
            sampler = {}
        else:
            require(type(sampler_index) is int and 0 <= sampler_index < len(doc.get("samplers", [])), "invalid sampler")
            sampler = doc["samplers"][sampler_index]
        ws, wt = sampler.get("wrapS", 10497), sampler.get("wrapT", 10497)
        require(ws in WRAPS and wt in WRAPS, "unsupported sampler wrap mode; only REPEAT and CLAMP_TO_EDGE are supported")
        contracts[source]["wraps"].add((WRAPS[ws], WRAPS[wt]))
        for role, domain in roles[ti]:
            contracts[source]["roles"].add(role)
            contracts[source]["domains"].add(domain)
    image_views = []
    for ii, (image, contract) in enumerate(zip(images, contracts)):
        require("uri" not in image and "bufferView" in image, "require embedded image")
        require(image.get("mimeType") in ("image/png", "image/jpeg"), "input must be PNG or JPEG")
        require(not image.get("extensions"), "input image extension unsupported")
        require(0 <= image["bufferView"] < len(doc["bufferViews"]), "invalid image bufferView")
        require(len(contract["domains"]) == 1, f"image {ii} has mixed color domains or no classified role")
        require(len(contract["wraps"]) == 1, f"image {ii} has mixed sampler wraps")
        image_views.append(image["bufferView"])
        contract["domain"] = next(iter(contract.pop("domains")))
        contract["wrap_s"], contract["wrap_t"] = next(iter(contract.pop("wraps")))
        contract["roles"] = sorted(contract["roles"])
    require(len(set(image_views)) == len(image_views), "multiple images share one bufferView; split explicitly first")
    image_views = set(image_views)
    for accessor in doc.get("accessors", []):
        used = [accessor.get("bufferView")]
        if "sparse" in accessor:
            used += [accessor["sparse"][k]["bufferView"] for k in ("indices", "values")]
        require(not image_views.intersection(used), "image bufferView also used by accessor")
    return contracts


def ktx_header(data):
    require(len(data) >= 104 and data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n", "not KTX2")
    h = struct.unpack_from("<13I2Q", data, 12)
    vk, typesize, width, height, depth, layers, faces, levels, scheme, dfd, dfdlen, kvd, kvdlen, sgd, sgdlen = h
    require(dfd + dfdlen <= len(data) and dfdlen >= 28, "invalid DFD")
    return {"vk_format": vk, "type_size": typesize, "width": width, "height": height,
            "depth": depth, "layers": layers, "faces": faces, "levels": levels,
            "supercompression": scheme, "dfd_model": data[dfd + 12],
            "dfd_primaries": data[dfd + 13], "dfd_transfer": data[dfd + 14],
            "level_uncompressed_bytes": sum(struct.unpack_from("<QQQ", data, 80 + i * 24)[2]
                                            for i in range(levels))}


def check_ktx(data, domain, size):
    h = ktx_header(data)
    require((h["width"], h["height"]) == tuple(size), "image dimensions changed")
    require(h["width"] % 4 == 0 and h["height"] % 4 == 0, "glTF Basis image dimensions must be multiples of four")
    require(h["depth"] == h["layers"] == 0 and h["faces"] == 1, "require 2D non-array KTX2")
    require(h["vk_format"] == 0 and h["type_size"] == 1 and h["dfd_model"] == 166
            and h["supercompression"] == 2, "require UASTC + lossless Zstd KTX2")
    require(h["levels"] == int(math.log2(max(size))) + 1, "require full mip chain")
    require((h["dfd_primaries"], h["dfd_transfer"]) == ((1, 2) if domain == "srgb" else (0, 1)),
            "incorrect KHR_texture_basisu color metadata")
    return h


def semantic_snapshot(doc, compressed):
    doc = copy.deepcopy(doc)
    doc["buffers"][0].pop("byteLength", None)
    for bv in doc["bufferViews"]:
        bv.pop("byteOffset", None)
    for image in doc["images"]:
        doc["bufferViews"][image["bufferView"]].pop("byteLength", None)
        image.pop("mimeType", None)
    if compressed:
        for texture in doc["textures"]:
            require("source" not in texture, "PNG/JPEG fallback texture.source is forbidden")
            require(set(texture.get("extensions", {})) == {BASIS}, "unexpected texture extension")
            texture["source"] = texture.pop("extensions")[BASIS]["source"]
        for field in ("extensionsUsed", "extensionsRequired"):
            require(doc.get(field) == [BASIS], f"{field} must require KHR_texture_basisu")
            del doc[field]
    return doc


def verify_preserved(source, candidate):
    src, sb = load_glb(source)
    dst, db = load_glb(candidate)
    contracts = image_contracts(src)
    require(semantic_snapshot(src, False) == semantic_snapshot(dst, True), "non-image glTF semantics changed")
    images = {image["bufferView"] for image in src["images"]}
    for i in range(len(src["bufferViews"])):
        if i not in images:
            require(view_bytes(src, sb, i) == view_bytes(dst, db, i), f"non-image BIN bufferView {i} changed")
    report = []
    for i, contract in enumerate(contracts):
        require(dst["images"][i]["mimeType"] == "image/ktx2", "not embedded KTX2")
        with Image.open(io.BytesIO(view_bytes(src, sb, src["images"][i]["bufferView"]))) as image:
            size = image.size
        data = view_bytes(dst, db, dst["images"][i]["bufferView"])
        report.append(check_ktx(data, contract["domain"], size))
    return {"non_image_bufferViews_byte_identical": len(src["bufferViews"]) - len(images),
            "accessors_semantics_and_payloads_unchanged": len(src.get("accessors", [])),
            "non_image_json_semantics_identical": True, "images": report}


def run(args):
    env = dict(os.environ)
    env.pop("TOKTX_OPTIONS", None)
    result = subprocess.run([str(x) for x in args], env=env, text=True, capture_output=True)
    require(result.returncode == 0, f"command failed {args}:\n{result.stdout}\n{result.stderr}")
    return (result.stdout + result.stderr).strip()


def encoder_identity(encoder):
    encoder = Path(encoder).resolve()
    require(sha(encoder.read_bytes()) == ENCODER_SHA, "encoder binary SHA differs from verified official Darwin arm64 release")
    version = run([encoder, "--version"])
    require(version == "ktx version: v4.4.2", "encoder version must be official KTX v4.4.2")
    lib = encoder.parent.parent / "lib/libktx.4.4.2.dylib"
    require(lib.is_file(), "isolated official libktx missing")
    require(sha(lib.read_bytes()) == LIBKTX_SHA, "libktx SHA differs from verified official release")
    return {"path": str(encoder), "version": version,
            "sha256": sha(encoder.read_bytes()), "libktx_sha256": sha(lib.read_bytes())}


def mip_sizes(size):
    """glTF/KTX legal dimensions, including each axis reaching one independently."""
    require(len(size) == 2 and all(type(n) is int and n > 0 for n in size), "invalid image dimensions")
    return [(max(size[0] >> level, 1), max(size[1] >> level, 1))
            for level in range(max(size).bit_length())]


def _resample_axis(data, target, axis, wrap):
    """Separable antialiased Lanczos4 with actual glTF boundary extension."""
    require(wrap in WRAPS.values() and axis in (0, 1), "invalid mip axis/wrap")
    count = data.shape[axis]
    require(0 < target <= count, "mip target must be positive and cannot upsample")
    if target == count:
        return data
    scale = count / target
    centers = (np.arange(target, dtype=np.float64) + 0.5) * scale - 0.5
    radius = 4 * scale
    left = np.ceil(centers - radius).astype(np.int64)
    indices = left[:, None] + np.arange(math.ceil(2 * radius) + 1, dtype=np.int64)[None, :]
    distance = (indices - centers[:, None]) / scale
    weights = np.where(np.abs(distance) < 4, np.sinc(distance) * np.sinc(distance / 4), 0.0)
    weights /= weights.sum(axis=1, keepdims=True)
    if wrap == "wrap":
        indices %= count
    else:
        indices = np.clip(indices, 0, count - 1)
    shape = list(data.shape)
    shape[axis] = target
    result = np.zeros(shape, dtype=np.float64)
    coefficient_shape = [1, 1, 1]
    coefficient_shape[axis] = target
    # One tap at a time bounds temporary memory even for 4K RGB inputs.
    for tap in range(indices.shape[1]):
        result += np.take(data, indices[:, tap], axis=axis) * weights[:, tap].reshape(coefficient_shape)
    return result


def axis_mips(image, domain, wrap_s, wrap_t):
    """Keep level zero verbatim; filter lower levels without PNG quantization feedback."""
    require(image.mode in ("RGB", "RGBA") and domain in ("srgb", "linear"), "invalid mip image mode/domain")
    require(wrap_s in WRAPS.values() and wrap_t in WRAPS.values(), "invalid mip wrap")
    levels = [image.copy()]
    linear = np.asarray(image, dtype=np.float64) / 255.0
    if domain == "srgb":
        rgb = linear[:, :, :3]
        linear[:, :, :3] = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    for width, height in mip_sizes(image.size)[1:]:
        linear = _resample_axis(_resample_axis(linear, width, 1, wrap_s), height, 0, wrap_t)
        linear = np.clip(linear, 0.0, 1.0)
        encoded = linear.copy()
        if domain == "srgb":
            rgb = encoded[:, :, :3]
            encoded[:, :, :3] = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)
        quantized = np.floor(np.clip(encoded, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
        levels.append(Image.fromarray(quantized))
    return levels


def encode_image(raw, contract, encoder, identity, cache):
    with Image.open(io.BytesIO(raw)) as image:
        require(image.format in ("PNG", "JPEG") and image.mode in ("RGB", "RGBA"), "require RGB/RGBA PNG/JPEG")
        require(getattr(image, "n_frames", 1) == 1, "animated image unsupported")
        require(image.width % 4 == image.height % 4 == 0, "image dimensions not divisible by four")
        image.load()
        mode, size = image.mode, image.size
        pixels_sha = sha(image.tobytes())
        source_image = image.copy()
    explicit = contract["wrap_s"] != contract["wrap_t"]
    mip_provenance = {"source": SETTINGS["mip_source"]["different_axes" if explicit else "same_axis"],
                      "wrap_s": contract["wrap_s"], "wrap_t": contract["wrap_t"]}
    if explicit:
        mip_provenance.update({"generator_sha256": sha(Path(__file__).read_bytes()),
                               "numpy_version": np.__version__, "pillow_version": PIL.__version__,
                               "settings": SETTINGS["axis_mips"]})
    command = [str(encoder), "create", "--format", "R8G8B8" + ("A8" if mode == "RGBA" else "")
               + ("_SRGB" if contract["domain"] == "srgb" else "_UNORM"),
               "--assign-tf", contract["domain"], "--assign-primaries", "bt709" if contract["domain"] == "srgb" else "none",
               "--assign-texcoord-origin", "top-left"]
    command += (["--levels", str(len(mip_sizes(size)))] if explicit else
                ["--generate-mipmap", "--mipmap-filter", "lanczos4", "--mipmap-wrap", contract["wrap_s"]])
    command += ["--encode", "uastc", "--uastc-quality", "3",
               "--threads", "2", "--zstd", "18", "--testrun"]
    key = sha(json.dumps({"raw_sha256": sha(raw), "decoded_pixels_sha256": pixels_sha,
                          "mode": mode, "command": command[1:], "settings": SETTINGS,
                          "mip_provenance": mip_provenance,
                          "encoder": {k: v for k, v in identity.items() if k != "path"}}, sort_keys=True).encode())
    cached = cache / (key + ".ktx2")
    if not cached.exists():
        with tempfile.TemporaryDirectory(dir=cache) as temp:
            levels = axis_mips(source_image, contract["domain"], contract["wrap_s"], contract["wrap_t"]) if explicit else [source_image]
            sources, level_records = [], []
            for level, image in enumerate(levels):
                path = Path(temp) / f"level-{level}.png"
                image.save(path, format="PNG")
                sources.append(path)
                level_records.append({"level": level, "size": list(image.size), "pixels_sha256": sha(image.tobytes())})
            output = Path(temp) / "encoded.ktx2"
            log = run(command + sources + [output])
            data = output.read_bytes()
            check_ktx(data, contract["domain"], size)
            run([encoder, "validate", "--gltf-basisu", "--warnings-as-errors", output])
            cached.write_bytes(data)
            cached.with_suffix(".json").write_text(json.dumps({"sha256": sha(data), "encoder_output": log,
                                                               "mip_inputs": level_records}, indent=2) + "\n")
    data = cached.read_bytes()
    cache_record = json.loads(cached.with_suffix(".json").read_text())
    require(sha(data) == cache_record["sha256"], "cache integrity failure")
    header = check_ktx(data, contract["domain"], size)
    validation = run([encoder, "validate", "--gltf-basisu", "--warnings-as-errors", cached])
    return data, {**contract, "source_sha256": sha(raw), "decoded_pixels_sha256": pixels_sha,
                  "source_mode": mode, "width": size[0], "height": size[1], "sha256": sha(data),
                  "ktx2_bytes": len(data), "ktx2": header, "validation": validation,
                  "mip_provenance": mip_provenance, "mip_inputs": cache_record["mip_inputs"],
                  "command_template": command + ([f"<level-{i}.png>" for i in range(len(mip_sizes(size)))] if explicit
                                                  else ["<losslessly-decoded-source.png>"]) + ["<output.ktx2>"], "cache_key": key}


def build(source, expected_sha, output, encoder, cache):
    raw = source.read_bytes()
    require(sha(raw) == expected_sha, "source SHA256 does not match pin")
    require(source.resolve() != output.resolve() and not output.exists(), "output must be a new private candidate file")
    doc, binary = load_glb(raw)
    contracts = image_contracts(doc)
    identity = encoder_identity(encoder)
    cache.mkdir(parents=True, exist_ok=True)
    replacements, records = {}, []
    for i, (image, contract) in enumerate(zip(doc["images"], contracts)):
        print(f"encoding image {i + 1}/{len(contracts)} {image.get('name', '')} {contract}", flush=True)
        data, record = encode_image(view_bytes(doc, binary, image["bufferView"]), contract, encoder, identity, cache)
        replacements[image["bufferView"]] = data
        records.append({"image": i, "name": image.get("name"), **record})
    dst = copy.deepcopy(doc)
    packed = bytearray()
    for i, view in enumerate(dst["bufferViews"]):
        packed.extend(b"\0" * (-len(packed) % 4))
        data = replacements[i] if i in replacements else view_bytes(doc, binary, i)
        view["byteOffset"], view["byteLength"] = len(packed), len(data)
        packed.extend(data)
    for image in dst["images"]:
        image["mimeType"] = "image/ktx2"
    for texture in dst["textures"]:
        texture["extensions"] = {BASIS: {"source": texture.pop("source")}}
    dst["extensionsUsed"] = dst["extensionsRequired"] = [BASIS]
    candidate = write_glb(dst, bytes(packed))
    verification = verify_preserved(raw, candidate)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    report = {"schema": 1, "status": "offline_validated_private_candidate_native_validation_pending",
              "input": {"path": str(source.resolve()), "sha256": expected_sha, "bytes": len(raw)},
              "output": {"path": str(output.resolve()), "sha256": sha(candidate), "bytes": len(candidate)},
              "encoder": identity, "settings": SETTINGS, "images": records, "preservation": verification,
              "decoder": {"name": "Pillow", "version": PIL.__version__},
              "native_gpu_format_and_memory_measured": False,
              "notice": "KTX2 bytes and estimated block bytes are not native GPU memory measurements; no OOM claim."}
    output.with_suffix(".manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["output"]), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--encoder", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path(__file__).resolve().parent / "cache")
    args = parser.parse_args()
    try:
        build(args.input, args.sha256, args.output, args.encoder, args.cache)
    except (ValueError, KeyError, IndexError, TypeError, struct.error, OSError) as error:
        parser.exit(1, f"compression rejected: {error}\n")


if __name__ == "__main__":
    main()
