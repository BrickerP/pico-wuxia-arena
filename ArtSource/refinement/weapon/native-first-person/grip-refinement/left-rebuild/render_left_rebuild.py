#!/usr/bin/env python3
"""Render three closed-grip Left views with both hand and dao at common G.

Run --verify-only in host Python first. Root alone starts one Blender process,
with two CPU threads. No app transforms or legacy left-root offsets are used.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
import traceback
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REFINEMENT = HERE.parent
HAND = REFINEMENT.parent
REPO = HAND.parents[3]
OUT = HERE / "previews"
MANIFEST = OUT / "render_manifest.json"
COMPANION = HERE / "make_companion.py"
COMMON = HAND / "render_hands.py"
STUDIO = REPO / "ArtSource/refinement/grip/render_grip_candidates.py"
SHARED = REPO / "ArtSource/refinement/pbr-compression/compress_pbr.py"
CAMERAS = REFINEMENT / "previews_v2/render_manifest.json"
DAO = REPO / "ArtSource/tripo-warrior/library/dao_grip.glb"
DAO_SHA = "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0"
DAO_DECODED = HAND / "compression/decoded/dao_grip_decoded.glb"
DAO_DECODED_SHA = "f983ee7463db688febcec5fd75b90109eb13afa2c4c5564d221659b98a12aa0c"
DAO_MANIFEST = HAND / "compression/decoded/dao_grip_decoded.manifest.json"
DAO_MANIFEST_SHA = "6944ebc820f957118c05bab1d3b1b443741cb97421baa6cb4e30bfd35c4a4a56"
IDENTITY = [[1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.]]
FILL = {"name": "Neutral dorsal readability fill", "type": "AREA", "shape": "DISK",
        "position_blender_metres": [0., -.25, -.60], "target_blender_metres": [0., 0., 0.],
        "power_watts": 45., "size_metres": .65, "color_linear_rgb": [1., 1., 1.]}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(REPO))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def camera_plans():
    previous = json.loads(CAMERAS.read_text())
    require([image["view"] for image in previous["images"]] == ["front", "back", "oblique"], "v2 three-camera contract changed")
    plans = []
    for image in previous["images"]:
        # Reflect only the camera position/target across common X to inspect
        # the rebuilt Left from matched anatomical directions. Dao stays exact.
        position = list(image["camera_blender_metres"])
        target = list(image["camera_target_blender_metres"])
        position[0], target[0] = -position[0], -target[0]
        plans.append({"view": image["view"], "grip_seconds": 1., "dao_visible": True,
                      "file": rel(OUT / ("left_closed_" + image["view"] + ".png")),
                      "camera_blender_metres": position, "camera_target_blender_metres": target,
                      "camera_distance_to_common_grip_metres": math.sqrt(sum(v*v for v in position)),
                      "lens_mm": image["lens_mm"], "sensor_width_mm": 36.})
    return plans


def preflight():
    companion = load("rebuilt_left_companion_proof", COMPANION)
    driver, p, proof = companion.verify_existing()
    for path, pin in ((DAO, DAO_SHA), (DAO_DECODED, DAO_DECODED_SHA), (DAO_MANIFEST, DAO_MANIFEST_SHA)):
        require(sha(path) == pin, "dao input pin changed: " + rel(path))
    preservation = p.verify_preserved(DAO_DECODED.read_bytes(), DAO.read_bytes())
    dao, dao_binary = p.load_glb(DAO.read_bytes())
    decoded, decoded_binary = p.load_glb(DAO_DECODED.read_bytes())
    provenance = json.loads(DAO_MANIFEST.read_text())
    require(provenance["compressed_input_sha256"] == DAO_SHA and provenance["sha256"] == DAO_DECODED_SHA and
            provenance["decoded_from_actual_ktx_top_mip"], "dao actual-KTX provenance changed")
    pixels = []
    for index, record in enumerate(provenance["images"]):
        require(record["image"] == index, "dao image provenance order changed")
        png = p.view_bytes(decoded, decoded_binary, decoded["images"][index]["bufferView"])
        require(p.sha(png) == record["png_sha256"] == sha(REPO / record["png_path"]), "dao embedded PNG provenance changed")
        pixels.append({"image": index, "ktx_sha256": p.sha(p.view_bytes(dao, dao_binary, dao["images"][index]["bufferView"])),
                       "png_sha256": p.sha(png)})
    inputs = [companion.CANDIDATE, companion.OUTPUT, companion.MANIFEST, companion.RIGHT,
              companion.RIGHT_DECODED, driver.BASELINE, driver.PROVENANCE, DAO, DAO_DECODED, DAO_MANIFEST,
              CAMERAS, COMPANION, companion.DRIVER,
              COMMON, STUDIO, SHARED, Path(__file__).resolve()]
    inputs += [REPO / record["png_path"] for record in proof["images"] + provenance["images"]]
    return {"schema": 1, "status": "inputs_verified_render_not_started", "images": [],
            "planned_images": camera_plans(), "input_pins": {rel(path): sha(path) for path in inputs},
            "candidate_sha256": companion.CANDIDATE_SHA, "decoded_sha256": proof["output"]["sha256"],
            "left_fresh_companion_proof": proof, "dao_preservation": preservation, "dao_actual_ktx_pixels": pixels,
            "renderer": {"path": rel(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
            "camera_source": rel(CAMERAS), "camera_rule": "v2 front/back/oblique; camera X reflected for anatomical Left, no model/dao mirror",
            "hand_root_from_common_grip_gltf": IDENTITY, "dao_root_from_common_grip_gltf": IDENTITY,
            "coordinate_scope": "glTF importer performs basis conversion only; both added roots identity; no app C, B, DerivedGrip or old offset",
            "additional_neutral_dorsal_fill": FILL, "expected_light_count": 4,
            "resolution": [1200, 900], "cycles_samples": 24, "threads": 2,
            "materials_overridden": False, "models_mirrored_by_renderer": False, "pico_device_verified": False,
            "scope": "Actual 3D offline closed-left contact evidence. Root reviews all three images; runtime checks remain separate."}


def write_manifest(report):
    OUT.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def verify_pins(report):
    require(report["renderer"]["sha256"] == sha(Path(__file__).resolve()), "renderer changed; rerun host --verify-only")
    for path, pin in report["input_pins"].items():
        require(sha(REPO / path) == pin, "input changed since host proof: " + path)
    require(report["planned_images"] == camera_plans(), "camera plan changed")
    require(report["hand_root_from_common_grip_gltf"] == IDENTITY and report["dao_root_from_common_grip_gltf"] == IDENTITY,
            "both roots must share common G identity")


def run_render(report):
    import bpy
    from mathutils import Matrix, Vector

    verify_pins(report)
    common = load("left_rebuild_native_renderer", COMMON)
    scene, camera = common.STUDIO.setup_scene(1200, 24)
    scene.render.resolution_y = 900
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.cycles.device = "CPU"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    camera.data.type = "PERSP"
    camera.data.clip_start = .005
    camera.data.sensor_width = 36
    fill_data = bpy.data.lights.new(FILL["name"], FILL["type"])
    fill_data.shape, fill_data.energy, fill_data.size = FILL["shape"], FILL["power_watts"], FILL["size_metres"]
    fill_data.color = FILL["color_linear_rgb"]
    fill = bpy.data.objects.new(FILL["name"], fill_data)
    scene.collection.objects.link(fill)
    fill.location = FILL["position_blender_metres"]
    fill.rotation_euler = (Vector(FILL["target_blender_metres"]) - fill.location).to_track_quat("-Z", "Y").to_euler()
    hand, rigs = common.import_at(HERE / "left_hand_rebuilt_decoded.glb", "RebuiltLeft_at_CommonGrip", (0, 0, 0))
    dao, _ = common.import_at(DAO_DECODED, "ExactDao_at_CommonGrip", (0, 0, 0))
    hand.matrix_world = Matrix.Identity(4)
    dao.matrix_world = Matrix.Identity(4)
    common.pose(rigs, scene, 1.)
    require(hand.matrix_world.to_3x3().determinant() > 0 and dao.matrix_world.to_3x3().determinant() > 0, "render root reflection")
    report["lighting"] = [{"name": obj.name, "matrix_world": [list(row) for row in obj.matrix_world],
                           "energy": obj.data.energy, "color": list(obj.data.color), "size": obj.data.size}
                          for obj in sorted(scene.objects, key=lambda obj: obj.name) if obj.type == "LIGHT"]
    require(len(report["lighting"]) == 4, "expected existing studio plus one neutral fill")
    report.update({"status": "rendering", "blender_version": bpy.app.version_string, "images": [],
                   "blender_fresh_input_hashes_match_host_semantic_and_pixel_proof": True})
    write_manifest(report)
    for plan in report["planned_images"]:
        camera.location = Vector(plan["camera_blender_metres"])
        target = Vector(plan["camera_target_blender_metres"])
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.lens = plan["lens_mm"]
        bpy.context.view_layer.update()
        geometry = common.evaluated_geometry(hand)
        scene.render.filepath = str(REPO / plan["file"])
        bpy.ops.render.render(write_still=True)
        verify_pins(report)
        require([list(row) for row in hand.matrix_world] == IDENTITY and [list(row) for row in dao.matrix_world] == IDENTITY,
                "common identity roots changed during animation")
        report["images"].append({**plan, "sha256": sha(REPO / plan["file"]),
                                  "camera_matrix_world_blender": [list(row) for row in camera.matrix_world],
                                  "hand_root_matrix_world_blender": [list(row) for row in hand.matrix_world],
                                  "dao_root_matrix_world_blender": [list(row) for row in dao.matrix_world],
                                  "evaluated_hand_geometry": geometry})
        write_manifest(report)
        print("READY", plan["file"], flush=True)
    require(len(report["images"]) == 3, "expected three actual renders")
    report["status"] = "three_closed_left_actual_3d_renders_complete"
    write_manifest(report)


def self_test():
    class RenderTests(unittest.TestCase):
        def test_fresh_inputs_and_three_closed_views(self):
            report = preflight()
            self.assertEqual(len(report["planned_images"]), 3)
            self.assertTrue(all(row["grip_seconds"] == 1. and row["dao_visible"] for row in report["planned_images"]))
            verify_pins(report)

        def test_stale_proof_is_rejected(self):
            report = preflight()
            report["input_pins"][rel(HERE / "left_hand_rebuilt.glb")] = "0" * 64
            with self.assertRaisesRegex(ValueError, "input changed since host proof"):
                verify_pins(report)

    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RenderTests)).wasSuccessful()


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    options = parser.parse_args(args)
    if options.self_test:
        raise SystemExit(0 if self_test() else 1)
    if options.verify_only:
        write_manifest(preflight())
        print("PREFLIGHT_PASS: three closed views; Blender has not been started", flush=True)
    else:
        run_render(json.loads(MANIFEST.read_text()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
