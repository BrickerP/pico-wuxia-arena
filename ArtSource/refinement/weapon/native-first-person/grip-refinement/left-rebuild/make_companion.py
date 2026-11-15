#!/usr/bin/env python3
"""Derive the frozen rebuilt left hand's actual-KTX PNG render companion.

Only this directory's decoded GLB and decode manifest are written. Geometry,
rig, animation, accessors and every non-image byte come from the rebuilt left.
"""
import argparse
import importlib.util
import json
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REFINEMENT = HERE.parent
CANDIDATE = HERE / "left_hand_rebuilt.glb"
CANDIDATE_SHA = "d8e9c3cb034f465e4527c13aad84e7ba283c3efcc537ab254c6295717cd1bbfd"
RIGHT = REFINEMENT / "right_hand_refined_v2.glb"
RIGHT_SHA = "3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0"
RIGHT_DECODED = REFINEMENT / "right_hand_refined_v2_decoded.glb"
RIGHT_DECODED_SHA = "ad2463fa1379faecca84e8f6b72ffca978d4e282cf7bce0e0dd77222729051d3"
OUTPUT = HERE / "left_hand_rebuilt_decoded.glb"
MANIFEST = HERE / "decode_manifest.json"
DRIVER = REFINEMENT / "make_render_companion.py"


def load_driver():
    spec = importlib.util.spec_from_file_location("left_rebuild_companion_driver", DRIVER)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.OUTPUT = OUTPUT
    return driver


def derive(driver, p, raw, pin):
    p.require(pin == CANDIDATE_SHA and p.sha(raw) == CANDIDATE_SHA, "rebuilt left candidate pin changed")
    p.require(p.sha(RIGHT.read_bytes()) == RIGHT_SHA, "accepted right source changed")
    p.require(p.sha(RIGHT_DECODED.read_bytes()) == RIGHT_DECODED_SHA, "accepted right pixel cache changed")
    result, report = driver.build_companion(p, raw, pin)
    source, binary = p.load_glb(raw)
    decoded, decoded_binary = p.load_glb(result)
    right, right_binary = p.load_glb(RIGHT_DECODED.read_bytes())
    roots = source["scenes"][source.get("scene", 0)]["nodes"]
    for index in roots:
        node = source["nodes"][index]
        p.require(node.get("translation", [0, 0, 0]) == [0, 0, 0] and
                  node.get("rotation", [0, 0, 0, 1]) == [0, 0, 0, 1] and
                  node.get("scale", [1, 1, 1]) == [1, 1, 1] and "matrix" not in node,
                  "rebuilt left outer root must be identity")
    p.require(source["nodes"] != right["nodes"] and source["meshes"] != right["meshes"],
              "fresh rebuilt left geometry/rig was replaced by right data")
    for key in ("nodes", "meshes", "skins", "animations", "accessors"):
        p.require(source[key] == decoded[key], "rebuilt left " + key + " changed in companion")
    for i, image in enumerate(decoded["images"]):
        p.require(p.view_bytes(decoded, decoded_binary, image["bufferView"]) ==
                  p.view_bytes(right, right_binary, right["images"][i]["bufferView"]),
                  "actual-KTX pixel cache mismatch")
    report["candidate_path"] = driver.relative(CANDIDATE)
    report["reused_driver"] = {"path": driver.relative(DRIVER), "sha256": p.sha(DRIVER.read_bytes())}
    report["pixel_cache_reference"] = {"path": driver.relative(RIGHT_DECODED),
                                        "sha256": RIGHT_DECODED_SHA,
                                        "all_three_embedded_PNG_payloads_byte_identical": True}
    report["source_right"] = {"path": driver.relative(RIGHT), "sha256": RIGHT_SHA}
    report["preservation"].update({"fresh_rebuilt_left_nodes_meshes_skins_animations_exact": True,
                                   "outer_root_identity": True,
                                   "scope": "All non-image JSON and bytes are from frozen rebuilt Left, never legacy Left or Right cache."})
    return result, report


def verify_existing():
    driver = load_driver()
    p = driver.helper()
    result, expected = derive(driver, p, CANDIDATE.read_bytes(), CANDIDATE_SHA)
    p.require(OUTPUT.read_bytes() == result, "decoded output differs from freshly derived rebuilt Left")
    report = json.loads(MANIFEST.read_text())
    p.require(report == expected, "decode manifest differs from fresh proof")
    return driver, p, report


def self_test():
    driver = load_driver()
    p = driver.helper()

    class CompanionTests(unittest.TestCase):
        def test_fresh_rebuilt_left_all_data(self):
            result, report = derive(driver, p, CANDIDATE.read_bytes(), CANDIDATE_SHA)
            document, _ = p.load_glb(result)
            self.assertEqual(report["preservation"]["candidate_all_accessors_identical"], len(document["accessors"]))
            self.assertEqual(document["nodes"][document["scenes"][0]["nodes"][0]]["name"], "LeftGripRoot")

        def test_right_geometry_cannot_substitute(self):
            with self.assertRaisesRegex(ValueError, "candidate pin changed"):
                derive(driver, p, RIGHT.read_bytes(), RIGHT_SHA)

        def test_changed_image_cannot_reuse_pixels(self):
            document, binary = p.load_glb(CANDIDATE.read_bytes())
            binary = bytearray(binary)
            view = document["bufferViews"][document["images"][0]["bufferView"]]
            binary[view["byteOffset"] + view["byteLength"] - 1] ^= 1
            raw = p.write_glb(document, bytes(binary))
            with self.assertRaisesRegex(ValueError, "KTX image 0 changed"):
                driver.build_companion(p, raw, p.sha(raw))

    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompanionTests)).wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    options = parser.parse_args()
    if options.self_test:
        raise SystemExit(0 if self_test() else 1)
    if options.verify_only:
        _, _, report = verify_existing()
        print(json.dumps(report["output"]))
        return
    if not options.candidate_sha256:
        parser.error("--candidate-sha256 is required")
    driver = load_driver()
    p = driver.helper()
    raw = CANDIDATE.read_bytes()
    result, report = derive(driver, p, raw, options.candidate_sha256)
    p.require(CANDIDATE.read_bytes() == raw, "candidate changed during derivation")
    OUTPUT.write_bytes(result)
    MANIFEST.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    verify_existing()
    print(json.dumps(report["output"]), flush=True)


if __name__ == "__main__":
    main()
