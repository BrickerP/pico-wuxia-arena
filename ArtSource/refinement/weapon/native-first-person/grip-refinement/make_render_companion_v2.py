#!/usr/bin/env python3
"""Render-only PNG companion for a frozen v2 hand; reuse verified KTX pixels.

Only this version's decoded GLB and manifest are written. All non-image data
come from the v2 candidate, including any new geometry, skin or animation data.
"""

import argparse
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "right_hand_refined_v2.glb"
OUTPUT = HERE / "right_hand_refined_v2_decoded.glb"
MANIFEST = HERE / "decode_manifest_v2.json"
REUSED_DRIVER = HERE / "make_render_companion.py"


def load_driver():
    spec = importlib.util.spec_from_file_location("verified_hand_companion_v1", REUSED_DRIVER)
    driver = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(driver)
    driver.OUTPUT = OUTPUT  # In-memory report destination; never write v1 outputs.
    return driver


def self_test(driver, p):
    if not driver.self_test(p):
        return False
    source, binary = p.load_glb(driver.BASELINE.read_bytes())
    accessor = source["accessors"][source["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    p.require(accessor["componentType"] == 5126, "geometry test expects source FLOAT POSITION")
    offset = source["bufferViews"][accessor["bufferView"]].get("byteOffset", 0) + accessor.get("byteOffset", 0)
    changed = bytearray(binary)
    struct.pack_into("<f", changed, offset, struct.unpack_from("<f", binary, offset)[0] + 0.0001)
    raw = p.write_glb(source, bytes(changed))
    decoded_raw, report = driver.build_companion(p, raw, p.sha(raw))
    decoded, decoded_binary = p.load_glb(decoded_raw)
    p.require(p.view_bytes(source, bytes(changed), accessor["bufferView"]) ==
              p.view_bytes(decoded, decoded_binary, accessor["bufferView"]), "v2 fresh geometry test failed")
    p.require(report["output"]["path"] == driver.relative(OUTPUT), "v2 report still points to v1")
    print("v2 fresh-geometry preservation and versioned output: PASS", flush=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-sha256", help="explicit frozen v2 candidate SHA required before writing")
    parser.add_argument("--self-test", action="store_true", help="exercise shared guards and v2 geometry preservation without writing")
    options = parser.parse_args()
    driver = load_driver()
    p = driver.helper()
    if options.self_test:
        raise SystemExit(0 if self_test(driver, p) else 1)
    if not options.candidate_sha256:
        parser.error("--candidate-sha256 is required")
    try:
        raw = CANDIDATE.read_bytes()
        result, report = driver.build_companion(p, raw, options.candidate_sha256)
        p.require(p.sha(CANDIDATE.read_bytes()) == options.candidate_sha256, "v2 candidate changed during derivation")
        report["candidate_path"] = driver.relative(CANDIDATE)
        report["reused_driver"] = {"path": driver.relative(REUSED_DRIVER), "sha256": p.sha(REUSED_DRIVER.read_bytes())}
        report["preservation"]["scope"] = "All non-image data preserved from the v2 candidate, not from the published baseline or v1."
        OUTPUT.write_bytes(result)
        p.require(p.sha(OUTPUT.read_bytes()) == report["output"]["sha256"], "written v2 companion SHA differs")
        MANIFEST.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(json.dumps(report["output"]), flush=True)
    except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
        parser.exit(1, f"v2 companion rejected: {error}\n")


if __name__ == "__main__":
    main()
