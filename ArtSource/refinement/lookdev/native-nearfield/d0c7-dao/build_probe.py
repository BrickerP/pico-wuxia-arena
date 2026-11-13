"""One private native diagnostic: forged material0 metallicFactor=217/255.

Standard-library only. No texture decode, GPU codec, producer, or formal writes.
All runtime BIN bytes, views, and eighteen KTX payloads stay bit-identical.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RUNTIME = ROOT / "app/src/main/assets/models/dao_grip.glb"
RUNTIME_SHA = "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0"
SOURCE = ROOT / "ArtSource/refinement/weapon/stage2/dao_grip_refined.glb"
SOURCE_SHA = "a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637"
FACTOR = 217 / 255
POINTER = "/materials/0/pbrMetallicRoughness/metallicFactor"
CANDIDATE = HERE / "dao_grip_forged_factor217_runtime.glb"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_glb_bytes(data):
    require(len(data) >= 28, "Truncated GLB")
    require(struct.unpack_from("<4sII", data) == (b"glTF", 2, len(data)), "Invalid GLB magic/version/length")
    json_length, kind = struct.unpack_from("<I4s", data, 12)
    stop = 20 + json_length
    require(kind == b"JSON" and json_length % 4 == 0 and stop + 8 <= len(data), "Invalid GLB JSON chunk")
    document = json.loads(data[20:stop])
    binary_length, kind = struct.unpack_from("<I4s", data, stop)
    require(kind == b"BIN\0" and binary_length % 4 == 0 and stop + 8 + binary_length == len(data), "Invalid GLB BIN chunk")
    require(document.get("asset", {}).get("version") == "2.0", "Expected glTF2")
    require(len(document.get("buffers", [])) == 1 and "uri" not in document["buffers"][0], "Expected one embedded BIN")
    binary = data[stop + 8:]
    declared = document["buffers"][0]["byteLength"]
    require(0 <= len(binary) - declared <= 3 and not any(binary[declared:]), "Invalid BIN length/padding")
    for view in document.get("bufferViews", []):
        start, length = view.get("byteOffset", 0), view.get("byteLength", -1)
        require(view.get("buffer", 0) == 0 and start >= 0 and length > 0 and start + length <= declared, "Invalid bufferView")
    return document, binary


def write_glb(document, binary):
    require(len(binary) % 4 == 0, "Original complete BIN chunk must remain aligned")
    raw = json.dumps(document, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    raw += b" " * (-len(raw) % 4)
    return (struct.pack("<4sII", b"glTF", 2, 28 + len(raw) + len(binary)) +
            struct.pack("<I4s", len(raw), b"JSON") + raw + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def image_payload(document, binary, index):
    view = document["bufferViews"][document["images"][index]["bufferView"]]
    start = view.get("byteOffset", 0)
    return binary[start:start + view["byteLength"]]


def validate_material(document):
    require(len(document.get("materials", [])) > 0 and document["materials"][0].get("name") == "Steel | forged body", "Wrong source material0 role")
    pbr = document["materials"][0].get("pbrMetallicRoughness", {})
    require(pbr.get("metallicFactor", 1) == 1, "Source forged metallicFactor is not the expected effective default1")
    require(pbr.get("metallicRoughnessTexture", {}).get("index") == 1 and
            document["meshes"][0]["primitives"][0].get("material") == 0, "Wrong forged texture/primitive binding")
    return pbr


def make_candidate(runtime_bytes):
    require(sha(runtime_bytes) == RUNTIME_SHA, "Runtime source SHA mismatch")
    document, binary = read_glb_bytes(runtime_bytes)
    validate_material(document)
    candidate = copy.deepcopy(document)
    candidate["materials"][0]["pbrMetallicRoughness"]["metallicFactor"] = FACTOR
    return write_glb(candidate, binary)


def verify_runtime_delta(runtime_bytes, candidate_bytes):
    require(sha(runtime_bytes) == RUNTIME_SHA, "Runtime source SHA mismatch")
    original, original_bin = read_glb_bytes(runtime_bytes)
    candidate, candidate_bin = read_glb_bytes(candidate_bytes)
    pbr = validate_material(original)
    expected = copy.deepcopy(original)
    expected["materials"][0]["pbrMetallicRoughness"]["metallicFactor"] = FACTOR
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    require(canonical(candidate) == canonical(expected), "Unexpected JSON delta beyond forged metallicFactor pointer")
    require(candidate_bin == original_bin, "Complete runtime BIN changed")
    require(candidate["bufferViews"] == original["bufferViews"], "Runtime bufferViews changed")
    require(len(original["images"]) == 18, "Expected all18 formal dao images")
    images = []
    for index in range(len(original["images"])):
        payload = image_payload(original, original_bin, index)
        require(original["images"][index].get("mimeType") == "image/ktx2" and payload.startswith(b"\xabKTX 20\xbb\r\n\x1a\n"), "Expected unchanged KTX2 image")
        require(payload == image_payload(candidate, candidate_bin, index), "Runtime KTX payload changed")
        images.append({"image": index, "name": original["images"][index].get("name"), "sha256": sha(payload), "bytes": len(payload)})
    return {"only_JSON_pointer_changed": POINTER, "previous_explicit_factor": "metallicFactor" in pbr,
            "source_effective_factor": pbr.get("metallicFactor", 1), "candidate_factor": FACTOR,
            "complete_BIN_bytes_bit_exact": len(original_bin), "BIN_sha256": sha(original_bin),
            "all_bufferViews_bit_exact": len(original["bufferViews"]), "accessors_and_all_payloads_bit_exact": len(original.get("accessors", [])),
            "all18_KTX_payloads_bit_exact": images, "all_other_JSON_exact": True,
            "geometry_UV_N_T_anchors_morphs_textures_samplers_all_other_material_factors_exact": True}


def build():
    runtime_bytes, png_source_bytes = RUNTIME.read_bytes(), SOURCE.read_bytes()
    require(sha(png_source_bytes) == SOURCE_SHA, "Formal PNG source SHA mismatch")
    candidate = make_candidate(runtime_bytes)
    verification = verify_runtime_delta(runtime_bytes, candidate)
    CANDIDATE.write_bytes(candidate)
    require(sha(RUNTIME.read_bytes()) == RUNTIME_SHA and sha(SOURCE.read_bytes()) == SOURCE_SHA, "Formal source changed during build")
    report = {"schema": "d0c7-dao-one-JSON-metallicFactor217", "status": "PRIVATE_DIAGNOSTIC_JSON_FACTOR_ONLY",
              "purpose": "Single-runtime-variable effective-metallic hypothesis; not a scalar-metalness bug claim or production decision",
              "input": {"runtime_path": str(RUNTIME.relative_to(ROOT)), "runtime_sha256": RUNTIME_SHA,
                        "source_PNG_GLB_path": str(SOURCE.relative_to(ROOT)), "source_PNG_GLB_sha256": SOURCE_SHA, "source_PNG_GLB_unchanged": True},
              "change": {"JSON_pointer": POINTER, "material": "Steel | forged body", "mesh_primitive": [0, 0],
                         "previous_effective_factor": 1, "previous_factor_is_glTF_default": True, "new_factor": FACTOR,
                         "numerator": 217, "denominator": 255,
                         "effective_metallic": "unchanged MR B/255 multiplied by217/255; median approximately0.851 for the near255 source median",
                         "intentional_modulation": True,
                         "difference_from_rejected_cap": "This scales every B texel, including values below217. The abandoned source edit used min(B,217) and left lower values intact. This is a clean multiplier control, not an identical cap operation."},
              "verification": verification, "codec_invocations": 0, "decoded_R_G_change": "zero; all encoded KTX bytes are unchanged",
              "output": {"path": str(CANDIDATE.relative_to(ROOT)), "sha256": sha(candidate), "bytes": len(candidate)},
              "builder_sha256": sha(Path(__file__).read_bytes()), "rejected_previous_route": "rejected-reencode-budget.json",
              "unchanged": ["all18 KTX images and MR R/G/B source bytes", "all BIN bytes/views/accessors", "albedo", "roughness G", "edge/spine/normal", "all other material factors", "geometry/UV/N/T/anchors/morphs", "lights/IBL/exposure"],
              "native_visual_status": "UNTESTED. Root may privately swap only the player dao for a fixed-light comparison; no formal publication is made here."}
    (HERE / "probe_recipe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "change": report["change"], "output": report["output"],
                      "all18_KTX_unchanged": True, "codec_invocations": 0}, indent=2), flush=True)
    return report


if __name__ == "__main__":
    build()
