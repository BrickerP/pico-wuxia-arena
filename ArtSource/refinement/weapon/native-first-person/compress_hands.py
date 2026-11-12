"""Thin hand-asset driver for the existing, pinned image-only PBR compressor.

Default inputs come from the producer's rig_manifest.json. --job replays an
explicit frozen input job. Work, validation and actual KTX-decoded companions
stay under compression/. Final aliases require --publish, both explicit approved
pins, and a matching current producer. No encoder or mip filter is reimplemented.
"""

import argparse
import copy
import hashlib
import importlib.util
import io
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
COMPRESSION = HERE / "compression"
SHARED = REPO / "ArtSource/refinement/pbr-compression/compress_pbr.py"
ENCODER = REPO / "ArtSource/refinement/pbr-compression/tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx"


def helper():
    spec = importlib.util.spec_from_file_location("shared_pbr_compressor", SHARED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def snapshot_job(p):
    manifest_path = HERE / "rig_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    job = {key: manifest[key] for key in ("formal_source", "formal_sha256", "png_source", "png_sha256")}
    job["rig_manifest_sha256"] = p.sha(manifest_path.read_bytes())
    job["sides"] = {}
    for side, key in (("right", "R"), ("left", "L")):
        record = manifest["sides"][key]
        source = REPO / record["path"]
        raw = source.read_bytes()
        p.require(p.sha(raw) == record["sha256"], "producer hand source changed during capture")
        target = COMPRESSION / "sources" / f"{side}-{record['sha256']}.glb"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            p.require(p.sha(target.read_bytes()) == record["sha256"], "snapshot integrity failure")
        else:
            target.write_bytes(raw)
        job["sides"][side] = {"path": str(target.relative_to(REPO)), "sha256": record["sha256"],
                              "producer_path": record["path"]}
    return job


def preflight(p, source, pin):
    raw = source.read_bytes()
    p.require(p.sha(raw) == pin, "hand source pin mismatch")
    document, binary = p.load_glb(raw)
    contracts = p.image_contracts(document)
    triangles = 0
    for mesh in document.get("meshes", []):
        for primitive in mesh["primitives"]:
            p.require(primitive.get("mode", 4) == 4, "hand mesh must use triangle lists")
            index = primitive.get("indices", primitive["attributes"]["POSITION"])
            count = document["accessors"][index]["count"]
            p.require(count % 3 == 0, "hand triangle count is not integral")
            triangles += count // 3
    images = []
    for image, contract in zip(document["images"], contracts):
        with Image.open(io.BytesIO(p.view_bytes(document, binary, image["bufferView"]))) as value:
            p.require(max(value.size) <= 2048, "hand image exceeds the 2K contract; do not compress old 4K inputs")
            images.append({"dimensions": list(value.size), **contract})
    return {"triangles": triangles, "images": images}


def producer_current(p, job):
    try:
        current = json.loads((HERE / "rig_manifest.json").read_text())
        return all(current["sides"][key]["sha256"] == job["sides"][side]["sha256"] and
                   p.sha((REPO / current["sides"][key]["path"]).read_bytes()) == job["sides"][side]["sha256"]
                   for side, key in (("right", "R"), ("left", "L")))
    except (OSError, KeyError, ValueError):
        return False


def validate_and_budget(p, candidate):
    document, binary = p.load_glb(candidate.read_bytes())
    records = []
    for index, image in enumerate(document["images"]):
        p.require(image.get("mimeType") == "image/ktx2" and "uri" not in image, "final image must be embedded KTX2")
        payload = p.view_bytes(document, binary, image["bufferView"])
        header = p.ktx_header(payload)
        path = candidate.parent / f"image-{index}.ktx2"
        path.write_bytes(payload)
        p.run([ENCODER, "validate", "--gltf-basisu", "--warnings-as-errors", path])
        blocks = sum(math.ceil(width / 4) * math.ceil(height / 4) * 16
                     for width, height in p.mip_sizes((header["width"], header["height"])))
        p.require(blocks == header["level_uncompressed_bytes"], "computed full-mip UASTC blocks differ from KTX header")
        records.append({"image": index, "ktx2_bytes": len(payload), "ktx_header": header,
                        "estimated_full_mip_uastc_4x4_block_bytes": blocks, "ktx_validate_passed": True})
    p.require(document.get("extensionsRequired") == [p.BASIS], "KHR_texture_basisu must be required")
    p.require(all("source" not in texture for texture in document["textures"]), "final PNG fallback forbidden")
    return records


def decode_companion(p, source, output):
    raw = source.read_bytes()
    compressed, binary = p.load_glb(raw)
    document = copy.deepcopy(compressed)
    document.pop("extensionsUsed", None)
    document.pop("extensionsRequired", None)
    for texture in document["textures"]:
        p.require(set(texture.get("extensions", {})) == {p.BASIS}, "unexpected texture extension")
        texture["source"] = texture.pop("extensions")[p.BASIS]["source"]
    replacements, decoded_records = {}, []
    output.parent.mkdir(parents=True, exist_ok=True)
    for index, image in enumerate(document["images"]):
        ktx = output.parent / f"{output.stem}-image-{index}.ktx2"
        png = output.parent / f"{output.stem}-image-{index}.png"
        ktx.write_bytes(p.view_bytes(compressed, binary, image["bufferView"]))
        if png.exists():
            png.unlink()
        p.run([ENCODER, "extract", "--transcode", "rgba8", "--level", "0", ktx, png])
        with Image.open(png) as value:
            value.load()
            if value.mode == "RGBA" and value.getchannel("A").getextrema() == (255, 255):
                value.convert("RGB").save(png)
        payload = png.read_bytes()
        replacements[image["bufferView"]] = payload
        image["mimeType"] = "image/png"
        decoded_records.append({"image": index, "png_sha256": p.sha(payload), "png_path": str(png.relative_to(REPO))})
    packed = bytearray()
    for index, view in enumerate(document["bufferViews"]):
        packed.extend(b"\0" * (-len(packed) % 4))
        payload = replacements[index] if index in replacements else p.view_bytes(compressed, binary, index)
        view["byteOffset"], view["byteLength"] = len(packed), len(payload)
        packed.extend(payload)
    result = p.write_glb(document, bytes(packed))
    decoded, decoded_binary = p.load_glb(result)
    p.require(p.semantic_snapshot(compressed, True) == p.semantic_snapshot(decoded, False), "decoded companion non-image semantics changed")
    image_views = {image["bufferView"] for image in compressed["images"]}
    for index in range(len(compressed["bufferViews"])):
        if index not in image_views:
            p.require(p.view_bytes(compressed, binary, index) == p.view_bytes(decoded, decoded_binary, index), "decoded companion geometry/skin/animation bytes changed")
    output.write_bytes(result)
    return {"path": str(output.relative_to(REPO)), "sha256": p.sha(result), "bytes": len(result),
            "compressed_input_sha256": p.sha(raw), "decoded_from_actual_ktx_top_mip": True,
            "non_image_semantics_and_buffer_views_preserved": True, "images": decoded_records}


def run_hands(job_path, decode, publish, right_pin=None, left_pin=None):
    p = helper()
    identity = p.encoder_identity(ENCODER)
    job = json.loads(job_path.read_text()) if job_path else snapshot_job(p)
    if right_pin is not None or left_pin is not None:
        p.require(right_pin is not None and left_pin is not None, "both explicit hand pins are required")
        p.require(job["sides"]["right"]["sha256"] == right_pin and job["sides"]["left"]["sha256"] == left_pin,
                  "producer/job differs from explicitly approved hand pins")
    version = p.sha(json.dumps({side: row["sha256"] for side, row in job["sides"].items()}, sort_keys=True).encode())[:20]
    folder = COMPRESSION / "versions" / version
    folder.mkdir(parents=True, exist_ok=True)
    write_json(folder / "source_job.json", job)
    checks = {side: preflight(p, REPO / row["path"], row["sha256"]) for side, row in job["sides"].items()}
    p.require(sum(row["triangles"] for row in checks.values()) <= 20000, "combined hand triangles exceed 20K")
    report = {"status": "offline_validation_in_progress", "version": version, "source_job": job,
              "helper": {"path": str(SHARED.relative_to(REPO)), "sha256": p.sha(SHARED.read_bytes())},
              "settings": p.SETTINGS, "encoder": identity, "hands": {},
              "native_gpu_format_and_memory_measured": False,
              "memory_scope": "UASTC full-mip block estimate and KTX storage bytes; not measured GPU memory or runtime transcode format"}
    for side in ("right", "left"):
        row = job["sides"][side]
        source = REPO / row["path"]
        output = folder / (side + "_hand.glb")
        if not output.exists():
            built = p.build(source, row["sha256"], output, ENCODER, COMPRESSION / "cache")
        else:
            built = json.loads(output.with_suffix(".manifest.json").read_text())
            p.require(built["input"]["sha256"] == row["sha256"] and built["settings"] == p.SETTINGS, "stale version build metadata")
        preservation = p.verify_preserved(source.read_bytes(), output.read_bytes())
        images = validate_and_budget(p, output)
        record = {"source_sha256": row["sha256"], "artifact": {"path": str(output.relative_to(REPO)),
                  "sha256": p.sha(output.read_bytes()), "bytes": output.stat().st_size},
                  "preflight": checks[side], "preservation": preservation, "images": images}
        if decode:
            record["decoded_companion"] = decode_companion(p, output, COMPRESSION / "decoded" / version / (side + "_hand_decoded.glb"))
        report["hands"][side] = record
        write_json(folder / "compression_manifest.json", report)
        print("HAND_VERSION_READY", side, record["artifact"], flush=True)
    report["total_ktx2_image_bytes"] = sum(image["ktx2_bytes"] for hand in report["hands"].values() for image in hand["images"])
    report["estimated_full_mip_uastc_4x4_block_bytes"] = sum(image["estimated_full_mip_uastc_4x4_block_bytes"] for hand in report["hands"].values() for image in hand["images"])
    current = producer_current(p, job)
    report["source_pins_match_current_producer"] = current
    report["aliases_published"] = bool(current and publish)
    report["status"] = ("offline_validated_native_validation_pending" if publish and current else
                        "validated_before_version_source_superseded" if not current else
                        "offline_validated_private_version_not_published")
    if current and publish:
        for side, record in report["hands"].items():
            shutil.copyfile(REPO / record["artifact"]["path"], HERE / (side + "_hand.glb"))
            if decode:
                shutil.copyfile(REPO / record["decoded_companion"]["path"], COMPRESSION / "decoded" / (side + "_hand_decoded.glb"))
    write_json(folder / "compression_manifest.json", report)
    write_json(HERE / "compression_manifest.json", report)
    print(json.dumps({"status": report["status"], "version": version,
                      "ktx2_image_bytes": report["total_ktx2_image_bytes"],
                      "estimated_uastc_blocks": report["estimated_full_mip_uastc_4x4_block_bytes"]}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=Path)
    parser.add_argument("--skip-decode", action="store_true")
    parser.add_argument("--decode-dao", type=Path)
    parser.add_argument("--dao-sha256")
    parser.add_argument("--publish", action="store_true", help="publish aliases only for an explicitly approved current source pair")
    parser.add_argument("--right-sha256")
    parser.add_argument("--left-sha256")
    options = parser.parse_args()
    COMPRESSION.mkdir(parents=True, exist_ok=True)
    if options.decode_dao:
        p = helper()
        p.encoder_identity(ENCODER)
        p.require(options.dao_sha256 and p.sha(options.decode_dao.read_bytes()) == options.dao_sha256, "formal dao source pin mismatch")
        record = decode_companion(p, options.decode_dao, COMPRESSION / "decoded" / "dao_grip_decoded.glb")
        write_json(COMPRESSION / "decoded/dao_grip_decoded.manifest.json", record)
        print(json.dumps(record["path"]), flush=True)
    else:
        if options.publish and not (options.right_sha256 and options.left_sha256):
            parser.error("--publish requires explicit --right-sha256 and --left-sha256")
        run_hands(options.job, not options.skip_decode, options.publish,
                  options.right_sha256, options.left_sha256)


if __name__ == "__main__":
    main()
