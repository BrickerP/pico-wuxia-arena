#!/usr/bin/env python3
"""Four source-fixed closed Right surface renders; Root starts Blender only.

Host --verify-only records the two closed source ROI centers/normals and all
input pins. A later single Blender run renders source/candidate with exactly
the same cameras, lights, materials, pose, roots, and dao visibility.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REFINEMENT = HERE.parent
NATIVE = REFINEMENT.parent
REPO = NATIVE.parents[3]
OUT = HERE / "previews"
MANIFEST = OUT / "render_manifest.json"
COMPANION = HERE / "make_companion.py"
COMMON = NATIVE / "render_hands.py"
STUDIO = REPO / "ArtSource/refinement/grip/render_grip_candidates.py"
SHARED = REPO / "ArtSource/refinement/pbr-compression/compress_pbr.py"
CAMERA_REFERENCE = REFINEMENT / "previews_v2/render_manifest.json"
ROI_REFERENCE = HERE / "roi_delta.json"
DAO = REPO / "ArtSource/tripo-warrior/library/dao_grip.glb"
DAO_SHA = "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0"
DAO_DECODED = NATIVE / "compression/decoded/dao_grip_decoded.glb"
DAO_DECODED_SHA = "f983ee7463db688febcec5fd75b90109eb13afa2c4c5564d221659b98a12aa0c"
DAO_MANIFEST = NATIVE / "compression/decoded/dao_grip_decoded.manifest.json"
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


def blender_vector(vector):
    require(len(vector) == 3 and all(math.isfinite(v) for v in vector), "ROI coordinates must be three finite numbers")
    return [float(vector[0]), -float(vector[2]), float(vector[1])]


def camera_plans(roi, lens_mm, dao_visible):
    require(math.isfinite(lens_mm) and 15. <= lens_mm <= 100., "unexpected review lens")
    require(set(roi) == {"dorsal_back", "wrist_cuff"}, "expected exactly dorsal and hand-side wrist ROIs")
    plans = []
    for stage in ("before", "after"):
        for name in ("dorsal_back", "wrist_cuff"):
            center = blender_vector(roi[name]["center_gltf_metres"])
            normal = blender_vector(roi[name]["normal_gltf"])
            length = math.sqrt(sum(v*v for v in normal))
            require(.9 <= length <= 1.1, "expected unit outward source ROI normal")
            direction = [v / length for v in normal]
            position = [center[i] + .3 * direction[i] for i in range(3)]
            distance = math.sqrt(sum((position[i]-center[i])**2 for i in range(3)))
            require(abs(distance-.3) < 1e-12, "camera must be .3m from source ROI focus")
            plans.append({"stage": stage, "view": name, "grip_seconds": 1., "dao_visible": bool(dao_visible),
                          "file": rel(OUT / (stage + "_" + name + "_closed1_0.3m.png")),
                          "camera_blender_metres": position, "camera_target_blender_metres": center,
                          "camera_distance_to_source_roi_focus_metres": distance,
                          "camera_distance_to_common_grip_metres": math.sqrt(sum(v*v for v in position)),
                          "distance_reference": "source closed ROI focus, not Grip origin",
                          "lens_mm": lens_mm, "sensor_width_mm": 36., "camera_track": "-Z", "camera_up": "Y"})
    return plans


def read_roi_guides(candidate_pin, source_pin):
    reference = json.loads(ROI_REFERENCE.read_text())
    require(reference["source_sha256"] == source_pin and reference["candidate_sha256"] == candidate_pin,
            "ROI guide candidate/source pin differs")
    guides = reference["render_guides"]
    roi = {}
    for view, key in (("dorsal_back", "dorsal"), ("wrist_cuff", "cuff")):
        guide = guides[key]
        require(guide["grip_time"] == 1. and guide["camera_distance_m"] == .3, "ROI guide pose/distance changed")
        ids = guide["source_roi_vertex_ids"]
        require(len(ids) >= 3 and all(type(i) is int and 0 <= i < reference["source_vertex_count"] for i in ids),
                "ROI guide has invalid source surface vertex IDs")
        roi[view] = {"center_gltf_metres": guide["center_canonical_m"], "normal_gltf": guide["outward_canonical_unit"],
                     "source_roi_vertex_ids": ids}
    return roi


def preflight(candidate_pin, lens_mm=50., dao_visible=False):
    companion = load("surface_companion_proof", COMPANION)
    driver, p, proof = companion.verify_existing(candidate_pin)
    roi = read_roi_guides(candidate_pin, companion.SOURCE_SHA)
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
    inputs = [companion.CANDIDATE, companion.OUTPUT, companion.MANIFEST, companion.SOURCE, companion.SOURCE_DECODED,
              driver.BASELINE, driver.PROVENANCE, DAO, DAO_DECODED, DAO_MANIFEST, COMPANION, companion.DRIVER,
              COMMON, STUDIO, SHARED, CAMERA_REFERENCE, ROI_REFERENCE, Path(__file__).resolve()]
    inputs += [REPO / record["png_path"] for record in proof["images"] + provenance["images"]]
    return {"schema": 1, "status": "inputs_verified_render_not_started", "images": [],
            "planned_images": camera_plans(roi, lens_mm, dao_visible), "input_pins": {rel(path): sha(path) for path in inputs},
            "source_sha256": companion.SOURCE_SHA, "source_decoded_sha256": companion.SOURCE_DECODED_SHA,
            "candidate_sha256": candidate_pin, "decoded_sha256": proof["output"]["sha256"],
            "fresh_candidate_companion_proof": proof, "dao_preservation": preservation, "dao_actual_ktx_pixels": pixels,
            "renderer": {"path": rel(Path(__file__).resolve()), "sha256": sha(Path(__file__).resolve())},
            "source_fixed_ROI": copy.deepcopy(roi), "roi_reference_source_sha256": companion.SOURCE_SHA,
            "roi_reference": {"path": rel(ROI_REFERENCE), "sha256": sha(ROI_REFERENCE), "field": "render_guides"},
            "roi_reference_pose": "source Right actual grip animation at 1 second; all glTF roots retained",
            "camera_reference": rel(CAMERA_REFERENCE),
            "camera_rule": "Explicit closed source ROI center + .3m outward normal; reused verbatim for candidate; no after-geometry recentering",
            "wrist_focus_rule": "R_Hand interface / first hand-side cuff band; never remote forearm cut cap",
            "lens_mm": lens_mm, "dao_visible": bool(dao_visible),
            "hand_root_from_common_grip_gltf": IDENTITY, "dao_root_from_common_grip_gltf": IDENTITY,
            "coordinate_scope": "glTF importer basis conversion only; added roots identity; no app mapping or model reflection",
            "additional_neutral_dorsal_fill": FILL, "expected_light_count": 4,
            "resolution": [1200, 900], "cycles_samples": 24, "threads": 2,
            "materials_overridden": False, "models_mirrored_by_renderer": False, "pico_device_verified": False,
            "scope": "Four actual offline 3D renders, source and fresh surface candidate closed Right; no runtime or continuous-clearance claim."}


def write_manifest(report):
    OUT.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def verify_pins(report):
    require(report["renderer"]["sha256"] == sha(Path(__file__).resolve()), "renderer changed; rerun host --verify-only")
    for path, pin in report["input_pins"].items():
        require(sha(REPO / path) == pin, "input changed since host proof: " + path)
    require(report["planned_images"] == camera_plans(report["source_fixed_ROI"], report["lens_mm"], report["dao_visible"]),
            "source-fixed camera plan changed")
    require(report["hand_root_from_common_grip_gltf"] == IDENTITY and report["dao_root_from_common_grip_gltf"] == IDENTITY,
            "both added roots must share common G identity")


def run_render(report):
    import bpy
    from mathutils import Matrix, Vector

    verify_pins(report)
    common = load("surface_native_renderer", COMMON)
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
    hand_roots = {}
    visibility = {}
    for stage, path in (("before", REFINEMENT / "right_hand_refined_v2_decoded.glb"),
                        ("after", HERE / "right_hand_surface_decoded.glb")):
        hand, rigs = common.import_at(path, "Surface_" + stage + "_at_CommonGrip", (0, 0, 0))
        hand.matrix_world = Matrix.Identity(4)
        common.pose(rigs, scene, 1.)
        hand_roots[stage] = hand
        visibility[stage] = {obj: obj.hide_render for obj in [hand, *hand.children_recursive]}
    dao, _ = common.import_at(DAO_DECODED, "ExactDao_at_CommonGrip", (0, 0, 0))
    dao.matrix_world = Matrix.Identity(4)
    dao_visibility = {obj: obj.hide_render for obj in [dao, *dao.children_recursive]}
    report["lighting"] = [{"name": obj.name, "matrix_world": [list(row) for row in obj.matrix_world],
                           "energy": obj.data.energy, "color": list(obj.data.color), "size": obj.data.size}
                          for obj in sorted(scene.objects, key=lambda obj: obj.name) if obj.type == "LIGHT"]
    require(len(report["lighting"]) == 4, "expected existing studio plus neutral dorsal fill")
    report.update({"status": "rendering", "blender_version": bpy.app.version_string, "images": [],
                   "blender_input_hashes_match_host_semantic_and_pixel_proof": True})
    write_manifest(report)
    for plan in report["planned_images"]:
        stage = plan["stage"]
        for group, objects in visibility.items():
            for obj, hidden in objects.items():
                obj.hide_render = hidden if stage == group else True
        for obj, hidden in dao_visibility.items():
            obj.hide_render = hidden if plan["dao_visible"] else True
        camera.location = Vector(plan["camera_blender_metres"])
        camera.rotation_euler = (Vector(plan["camera_target_blender_metres"]) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.lens = plan["lens_mm"]
        bpy.context.view_layer.update()
        geometry = common.evaluated_geometry(hand_roots[stage])
        scene.render.filepath = str(REPO / plan["file"])
        bpy.ops.render.render(write_still=True)
        verify_pins(report)
        hand_matrix = [list(row) for row in hand_roots[stage].matrix_world]
        dao_matrix = [list(row) for row in dao.matrix_world]
        require(hand_matrix == dao_matrix == IDENTITY, "common identity roots changed during animation")
        report["images"].append({**plan, "sha256": sha(REPO / plan["file"]),
                                  "camera_matrix_world_blender": [list(row) for row in camera.matrix_world],
                                  "hand_root_matrix_world_blender": hand_matrix,
                                  "dao_root_matrix_world_blender": dao_matrix,
                                  "evaluated_hand_geometry": geometry,
                                  "rendered_hand_decoded_sha256": report["source_decoded_sha256"] if stage == "before" else report["decoded_sha256"]})
        write_manifest(report)
        print("READY", plan["file"], flush=True)
    require(len(report["images"]) == 4, "expected exactly four actual renders")
    for before, after in zip(report["images"][:2], report["images"][2:]):
        require(before["view"] == after["view"] and before["camera_matrix_world_blender"] == after["camera_matrix_world_blender"],
                "before/after camera mismatch")
        require(before["evaluated_hand_geometry"]["position_digest"] != after["evaluated_hand_geometry"]["position_digest"],
                "before/after evaluated geometry is identical")
    report["status"] = "four_matched_closed_right_actual_3d_renders_complete"
    write_manifest(report)


def self_test():
    roi = {"dorsal_back": {"center_gltf_metres": [.01, -.02, .03], "normal_gltf": [0., -1., 0.]},
           "wrist_cuff": {"center_gltf_metres": [.08, .01, -.01], "normal_gltf": [0., -1., 0.]}}

    class RenderTests(unittest.TestCase):
        def test_four_source_fixed_closed_roi_views(self):
            plans = camera_plans(roi, 50., False)
            self.assertEqual(len(plans), 4)
            self.assertEqual([p["stage"] for p in plans], ["before", "before", "after", "after"])
            for before, after in zip(plans[:2], plans[2:]):
                for key in ("camera_blender_metres", "camera_target_blender_metres", "lens_mm", "dao_visible"):
                    self.assertEqual(before[key], after[key])
                self.assertAlmostEqual(before["camera_distance_to_source_roi_focus_metres"], .3)
                self.assertEqual(before["grip_seconds"], 1.)
                self.assertNotAlmostEqual(before["camera_distance_to_common_grip_metres"], .3)

        def test_bad_roi_and_zero_normal_rejected(self):
            broken = copy.deepcopy(roi)
            broken["wrist_cuff"]["normal_gltf"] = [0., 0., 0.]
            with self.assertRaisesRegex(ValueError, "unit outward"):
                camera_plans(broken, 50., False)
            broken = copy.deepcopy(roi)
            broken["dorsal_back"]["center_gltf_metres"][0] = float("nan")
            with self.assertRaisesRegex(ValueError, "finite"):
                camera_plans(broken, 50., False)

        def test_stale_proof_rejected(self):
            report = {"renderer": {"sha256": sha(Path(__file__).resolve())},
                      "input_pins": {rel(COMPANION): "0" * 64}}
            with self.assertRaisesRegex(ValueError, "input changed since host proof"):
                verify_pins(report)

    return unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(RenderTests)).wasSuccessful()


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--candidate-sha256")
    parser.add_argument("--lens-mm", type=float, default=50.)
    parser.add_argument("--dao-visible", action="store_true")
    options = parser.parse_args(args)
    if options.self_test:
        raise SystemExit(0 if self_test() else 1)
    if options.verify_only:
        if not options.candidate_sha256:
            parser.error("host preflight requires candidate SHA; closed source ROI vectors come from pinned roi_delta.json")
        write_manifest(preflight(options.candidate_sha256, options.lens_mm, options.dao_visible))
        print("PREFLIGHT_PASS four source-fixed closed views; Blender has not been started", flush=True)
    else:
        run_render(json.loads(MANIFEST.read_text()))


if __name__ == "__main__":
    main()
