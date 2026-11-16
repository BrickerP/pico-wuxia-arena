#!/usr/bin/env python3
"""Build only this surface candidate's fresh, actual-KTX PNG companion.

All non-image JSON and bufferViews come from the candidate, including added
topology, attributes, skin, and animation. The old decoded Right is pixel proof,
never a source of mesh data. No Blender process is started by this program.
"""
import argparse
import copy
import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REFINEMENT = HERE.parent
CANDIDATE = HERE / "right_hand_surface.glb"
OUTPUT = HERE / "right_hand_surface_decoded.glb"
MANIFEST = HERE / "decode_manifest.json"
SOURCE = REFINEMENT / "right_hand_refined_v2.glb"
SOURCE_SHA = "3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0"
SOURCE_DECODED = REFINEMENT / "right_hand_refined_v2_decoded.glb"
SOURCE_DECODED_SHA = "ad2463fa1379faecca84e8f6b72ffca978d4e282cf7bce0e0dd77222729051d3"
DRIVER = REFINEMENT / "make_render_companion.py"


def load_driver():
    spec = importlib.util.spec_from_file_location("surface_actual_ktx_driver", DRIVER)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.OUTPUT = OUTPUT
    return driver


def mesh_payloads(p, document, binary):
    records = []
    for mesh in document["meshes"]:
        primitives = []
        for primitive in mesh["primitives"]:
            fields = {**primitive["attributes"], "indices": primitive["indices"]}
            record = {}
            for name, index in sorted(fields.items()):
                accessor = document["accessors"][index]
                views = [accessor.get("bufferView")]
                if "sparse" in accessor:
                    views += [accessor["sparse"][part]["bufferView"] for part in ("indices", "values")]
                record[name] = {"accessor": copy.deepcopy(accessor),
                                "payloads": [p.sha(p.view_bytes(document, binary, view)) for view in views if view is not None]}
            primitives.append(record)
        records.append(primitives)
    return records


def derive(driver, p, raw, pin):
    p.require(p.sha(raw) == pin, "surface candidate SHA differs from frozen pin")
    p.require(p.sha(SOURCE.read_bytes()) == SOURCE_SHA, "source Right changed")
    p.require(p.sha(SOURCE_DECODED.read_bytes()) == SOURCE_DECODED_SHA, "source actual-KTX companion changed")
    source, source_binary = p.load_glb(SOURCE.read_bytes())
    source_png, source_png_binary = p.load_glb(SOURCE_DECODED.read_bytes())
    source_preservation = p.verify_preserved(SOURCE_DECODED.read_bytes(), SOURCE.read_bytes())
    candidate, binary = p.load_glb(raw)
    before = mesh_payloads(p, source, source_binary)
    after = mesh_payloads(p, candidate, binary)
    p.require(before != after, "surface candidate geometry/attributes are unchanged from source Right")
    result, report = driver.build_companion(p, raw, pin)
    decoded, decoded_binary = p.load_glb(result)
    for key in ("nodes", "meshes", "skins", "animations", "accessors"):
        p.require(candidate.get(key) == decoded.get(key), "fresh surface " + key + " changed in companion")
    p.require(mesh_payloads(p, decoded, decoded_binary) == after, "fresh surface mesh payloads changed in companion")
    for index, image in enumerate(candidate["images"]):
        p.require(p.view_bytes(candidate, binary, image["bufferView"]) ==
                  p.view_bytes(source, source_binary, source["images"][index]["bufferView"]),
                  "surface KTX differs from source Right")
        p.require(p.view_bytes(decoded, decoded_binary, decoded["images"][index]["bufferView"]) ==
                  p.view_bytes(source_png, source_png_binary, source_png["images"][index]["bufferView"]),
                  "surface PNG differs from source Right actual-KTX pixels")
    report["candidate_path"] = driver.relative(CANDIDATE)
    report["reused_driver"] = {"path": driver.relative(DRIVER), "sha256": p.sha(DRIVER.read_bytes())}
    report["companion_builder"] = {"path": driver.relative(Path(__file__).resolve()), "sha256": p.sha(Path(__file__).read_bytes())}
    report["source_right"] = {"path": driver.relative(SOURCE), "sha256": SOURCE_SHA,
                              "decoded_path": driver.relative(SOURCE_DECODED), "decoded_sha256": SOURCE_DECODED_SHA,
                              "actual_ktx_preservation": source_preservation}
    report["geometry_change"] = {"candidate_mesh_attribute_data_changed_from_source": True,
                                 "source_mesh_payloads": before, "candidate_mesh_payloads": after,
                                 "source_accessor_count": len(source["accessors"]),
                                 "candidate_accessor_count": len(candidate["accessors"]),
                                 "source_mesh_metadata_reused_as_candidate": False}
    report["preservation"].update({"fresh_candidate_nodes_meshes_skins_animations_accessors_exact": True,
                                    "all_three_embedded_PNG_payloads_match_source_actual_KTX": True,
                                    "scope": "Fresh surface candidate owns every non-image JSON field and bufferView; no source mesh substitution."})
    return result, report


def verify_existing(expected_pin=None):
    driver = load_driver()
    p = driver.helper()
    saved = json.loads(MANIFEST.read_text())
    pin = expected_pin or saved["candidate_sha256"]
    p.require(saved["candidate_sha256"] == pin, "decode manifest candidate pin differs")
    result, expected = derive(driver, p, CANDIDATE.read_bytes(), pin)
    p.require(OUTPUT.read_bytes() == result, "decoded output differs from fresh surface derivation")
    p.require(saved == expected, "decode manifest differs from fresh surface proof")
    return driver, p, expected


def self_test():
    driver = load_driver()
    p = driver.helper()
    source_raw = SOURCE.read_bytes()

    class CompanionTests(unittest.TestCase):
        def test_new_topology_accessor_and_skin_preserved(self):
            document, binary = p.load_glb(source_raw)
            primitive = document["meshes"][0]["primitives"][0]
            old = document["accessors"][primitive["attributes"]["POSITION"]]
            p.require(old["componentType"] == 5126 and "sparse" not in old, "test expects dense FLOAT positions")
            payload = bytearray(p.view_bytes(document, binary, old["bufferView"]))
            offset = old.get("byteOffset", 0)
            struct.pack_into("<f", payload, offset, struct.unpack_from("<f", payload, offset)[0] + .0001)
            packed = bytearray(binary)
            packed.extend(b"\0" * (-len(packed) % 4))
            new_view = copy.deepcopy(document["bufferViews"][old["bufferView"]])
            new_view.update(byteOffset=len(packed), byteLength=len(payload))
            document["bufferViews"].append(new_view)
            packed.extend(payload)
            accessor = copy.deepcopy(old)
            accessor["bufferView"] = len(document["bufferViews"]) - 1
            document["accessors"].append(accessor)
            primitive["attributes"]["POSITION"] = len(document["accessors"]) - 1
            document["skins"][0]["extras"] = {"surface_companion_test": "fresh candidate skin retained"}
            synthetic = p.write_glb(document, bytes(packed))
            result, report = derive(driver, p, synthetic, p.sha(synthetic))
            decoded, _ = p.load_glb(result)
            self.assertEqual(decoded["meshes"], document["meshes"])
            self.assertEqual(decoded["skins"], document["skins"])
            self.assertEqual(len(decoded["accessors"]), len(document["accessors"]))
            self.assertTrue(report["geometry_change"]["candidate_mesh_attribute_data_changed_from_source"])

        def test_source_geometry_cannot_substitute(self):
            with self.assertRaisesRegex(ValueError, "unchanged from source"):
                derive(driver, p, source_raw, SOURCE_SHA)

        def test_wrong_candidate_pin_rejected(self):
            with self.assertRaisesRegex(ValueError, "candidate SHA"):
                derive(driver, p, source_raw, "0" * 64)

        def test_changed_ktx_rejected(self):
            document, binary = p.load_glb(source_raw)
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
        _, _, report = verify_existing(options.candidate_sha256)
    else:
        if not options.candidate_sha256:
            parser.error("--candidate-sha256 is required before writing")
        driver = load_driver()
        p = driver.helper()
        raw = CANDIDATE.read_bytes()
        result, report = derive(driver, p, raw, options.candidate_sha256)
        p.require(CANDIDATE.read_bytes() == raw, "candidate changed during derivation")
        OUTPUT.write_bytes(result)
        MANIFEST.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        verify_existing(options.candidate_sha256)
    print(json.dumps(report["output"]), flush=True)


if __name__ == "__main__":
    main()
