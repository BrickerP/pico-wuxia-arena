#!/usr/bin/env python3
"""Derive a PNG render companion from a pinned grip candidate, without encoding.

The three PNGs are the published hand's actual KTX level-0 decode. They may be
reused only while the candidate embeds the exact same KTX payloads. All mesh,
skin, node, accessor and animation data come from the new candidate.
"""

import argparse
import copy
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
HAND = HERE.parent
REPO = HAND.parents[3]
SHARED = REPO / "ArtSource/refinement/pbr-compression/compress_pbr.py"
VERSION = "71c39091c0859a357ed6"
BASELINE = HAND / "compression/versions" / VERSION / "right_hand.glb"
PROVENANCE = BASELINE.parent / "compression_manifest.json"
BASELINE_SHA = "5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d"
PROVENANCE_SHA = "86c145ff2b9bab8bcd68634d073d584f2e3b0bb803400e27c08c259c1795964f"
OUTPUT = HERE / "right_hand_refined_decoded.glb"
MANIFEST = HERE / "decode_manifest.json"


def helper():
    spec = importlib.util.spec_from_file_location("shared_pbr_companion", SHARED)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relative(path):
    return str(path.resolve().relative_to(REPO))


def build_companion(p, candidate_raw, candidate_pin):
    p.require(p.sha(candidate_raw) == candidate_pin, "candidate SHA differs from frozen pin")
    baseline_raw = BASELINE.read_bytes()
    provenance_raw = PROVENANCE.read_bytes()
    p.require(p.sha(baseline_raw) == BASELINE_SHA, "published KTX baseline SHA changed")
    p.require(p.sha(provenance_raw) == PROVENANCE_SHA, "published decode provenance SHA changed")
    provenance = json.loads(provenance_raw)["hands"]["right"]
    p.require(provenance["artifact"]["sha256"] == BASELINE_SHA, "decode provenance has wrong compressed source")
    decoded_record = provenance["decoded_companion"]
    p.require(decoded_record["compressed_input_sha256"] == BASELINE_SHA and
              decoded_record["decoded_from_actual_ktx_top_mip"], "PNG provenance is not an actual KTX decode")
    baseline, baseline_binary = p.load_glb(baseline_raw)
    candidate, binary = p.load_glb(candidate_raw)
    p.semantic_snapshot(candidate, True)  # Reject fallback or unknown extensions.
    p.require(len(candidate["images"]) == len(baseline["images"]) == 3, "expected exactly three hand atlas images")
    for key in ("images", "textures", "materials", "samplers"):
        p.require(candidate[key] == baseline[key], f"candidate changed published {key} contract")
    png_records = decoded_record["images"]
    p.require([record["image"] for record in png_records] == [0, 1, 2], "ambiguous PNG provenance order")

    document = copy.deepcopy(candidate)
    document.pop("extensionsUsed")
    document.pop("extensionsRequired")
    for texture in document["textures"]:
        texture["source"] = texture.pop("extensions")[p.BASIS]["source"]

    replacements, image_records = {}, []
    image_views = {image["bufferView"] for image in candidate["images"]}
    p.require(len(image_views) == 3, "atlas images must have separate bufferViews")
    for index, accessor in enumerate(candidate["accessors"]):
        views = [accessor.get("bufferView")]
        if "sparse" in accessor:
            views.extend(accessor["sparse"][part]["bufferView"] for part in ("indices", "values"))
        p.require(not image_views.intersection(views), f"accessor {index} aliases an image bufferView")
    for index, (image, record) in enumerate(zip(candidate["images"], png_records)):
        p.require(image.get("mimeType") == "image/ktx2" and "uri" not in image, "expected embedded KTX2")
        ktx = p.view_bytes(candidate, binary, image["bufferView"])
        old_ktx = p.view_bytes(baseline, baseline_binary, baseline["images"][index]["bufferView"])
        p.require(ktx == old_ktx, f"candidate KTX image {index} changed; cached PNG cannot be reused")
        png_path = (REPO / record["png_path"]).resolve()
        p.require(png_path.parent == (HAND / "compression/decoded" / VERSION).resolve(), "PNG provenance outside frozen decode")
        png = png_path.read_bytes()
        p.require(p.sha(png) == record["png_sha256"], f"actual decoded PNG {index} SHA changed")
        header = p.ktx_header(ktx)
        with p.Image.open(io.BytesIO(png)) as decoded_image:
            decoded_image.load()
            p.require(decoded_image.format == "PNG" and decoded_image.size == (1536, 1536), "unexpected decoded PNG format/dimensions")
            p.require(decoded_image.size == (header["width"], header["height"]), "decoded PNG dimensions differ from KTX")
        replacements[image["bufferView"]] = png
        document["images"][index]["mimeType"] = "image/png"
        image_records.append({"image": index, "name": image.get("name"),
                              "ktx_sha256": p.sha(ktx), "ktx_bytes": len(ktx),
                              "source_and_candidate_ktx_byte_identical": True,
                              "png_path": relative(png_path), "png_sha256": p.sha(png),
                              "dimensions": [1536, 1536], "actual_ktx_decode_level": 0,
                              "decode_reused_without_reencoding_or_resampling": True})

    packed = bytearray()
    for index, view in enumerate(document["bufferViews"]):
        packed.extend(b"\0" * (-len(packed) % 4))
        payload = replacements[index] if index in replacements else p.view_bytes(candidate, binary, index)
        view["byteOffset"], view["byteLength"] = len(packed), len(payload)
        packed.extend(payload)
    result = p.write_glb(document, bytes(packed))
    decoded, decoded_binary = p.load_glb(result)
    p.require(p.semantic_snapshot(candidate, True) == p.semantic_snapshot(decoded, False), "candidate non-image semantics changed")
    p.require(candidate["accessors"] == decoded["accessors"], "candidate accessors changed")
    view_records = []
    for index in range(len(candidate["bufferViews"])):
        if index not in image_views:
            payload = p.view_bytes(candidate, binary, index)
            p.require(payload == p.view_bytes(decoded, decoded_binary, index), f"candidate non-image bufferView {index} changed")
            view_records.append({"bufferView": index, "bytes": len(payload), "sha256": p.sha(payload)})
    # Also checks per-material color domains and the unchanged clamp samplers.
    contracts = p.image_contracts(decoded)
    p.verify_preserved(result, candidate_raw)
    report = {"schema": 1, "status": "offline_companion_verified_render_pending",
              "candidate_sha256": candidate_pin,
              "baseline": {"path": relative(BASELINE), "sha256": BASELINE_SHA},
              "decode_provenance": {"path": relative(PROVENANCE), "sha256": PROVENANCE_SHA,
                                    "decoder": "official KTX-Software 4.4.2 extract --transcode rgba8 --level 0"},
              "helper": {"path": relative(SHARED), "sha256": p.sha(SHARED.read_bytes())},
              "output": {"path": relative(OUTPUT), "sha256": p.sha(result), "bytes": len(result)},
              "images": [{**row, **contract} for row, contract in zip(image_records, contracts)],
              "preservation": {"candidate_non_image_json_semantics_identical": True,
                               "candidate_all_accessors_identical": len(candidate["accessors"]),
                               "candidate_non_image_bufferViews_byte_identical": len(view_records),
                               "non_image_bufferViews": view_records},
              "scope": "Offline PNG companion uses actual compressed top-mip pixels and the new candidate mesh/skin/nodes/animations. Native runtime appearance remains unverified."}
    return result, report


def self_test(p):
    """Exercise the real unchanged source and fail-closed input boundaries, in memory."""
    baseline_raw = BASELINE.read_bytes()

    class CompanionTests(unittest.TestCase):
        def test_actual_baseline_and_no_old_mesh_substitution(self):
            source, binary = p.load_glb(baseline_raw)
            node = next(node for node in source["nodes"] if node.get("name") == "R_Index1")
            node["rotation"] = [0.01, 0.0, 0.0, 0.9999499987499375]
            synthetic = p.write_glb(source, binary)
            result, report = build_companion(p, synthetic, p.sha(synthetic))
            decoded, _ = p.load_glb(result)
            self.assertEqual(source["nodes"], decoded["nodes"])
            self.assertEqual(report["preservation"]["candidate_non_image_bufferViews_byte_identical"], 29)
            self.assertEqual(report["preservation"]["candidate_all_accessors_identical"], 29)

        def test_wrong_candidate_pin_rejected(self):
            with self.assertRaisesRegex(ValueError, "candidate SHA"):
                build_companion(p, baseline_raw, "0" * 64)

        def test_changed_ktx_rejected(self):
            source, binary = p.load_glb(baseline_raw)
            mutated = bytearray(binary)
            view = source["bufferViews"][source["images"][0]["bufferView"]]
            mutated[view["byteOffset"] + view["byteLength"] - 1] ^= 1
            raw = p.write_glb(source, bytes(mutated))
            with self.assertRaisesRegex(ValueError, "KTX image 0 changed"):
                build_companion(p, raw, p.sha(raw))

        def test_changed_sampler_rejected(self):
            source, binary = p.load_glb(baseline_raw)
            source["samplers"][0]["wrapS"] = 10497
            raw = p.write_glb(source, binary)
            with self.assertRaisesRegex(ValueError, "samplers contract"):
                build_companion(p, raw, p.sha(raw))

    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompanionTests))
    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=HERE / "right_hand_refined.glb")
    parser.add_argument("--candidate-sha256", help="explicit frozen candidate SHA required before writing either output")
    parser.add_argument("--self-test", action="store_true", help="run real-source in-memory tests without writing outputs")
    options = parser.parse_args()
    p = helper()
    if options.self_test:
        raise SystemExit(0 if self_test(p) else 1)
    if not options.candidate_sha256:
        parser.error("--candidate-sha256 is required")
    try:
        candidate_raw = options.candidate.read_bytes()
        result, report = build_companion(p, candidate_raw, options.candidate_sha256)
        p.require(p.sha(options.candidate.read_bytes()) == options.candidate_sha256, "candidate changed during derivation")
        report["candidate_path"] = relative(options.candidate)
        OUTPUT.write_bytes(result)
        p.require(p.sha(OUTPUT.read_bytes()) == report["output"]["sha256"], "written companion SHA differs")
        MANIFEST.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(json.dumps(report["output"]), flush=True)
    except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
        parser.exit(1, f"companion rejected: {error}\n")


if __name__ == "__main__":
    main()
