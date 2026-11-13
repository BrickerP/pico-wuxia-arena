"""Render the refined native hand using the exact three accepted r1 cameras."""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SPEC = importlib.util.spec_from_file_location("grip_render_r1", HERE / "render_grip.py")
PREVIOUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREVIOUS)
COMMON = PREVIOUS.COMMON


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import bpy
    from mathutils import Vector

    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--decoded-sha256", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    candidate = HERE / "right_hand_refined_v2.glb"
    decoded = HERE / "right_hand_refined_v2_decoded.glb"
    dao = HERE.parent / "compression/decoded/dao_grip_decoded.glb"
    old_cameras = HERE / "previews/render_manifest.json"
    previous = json.loads(old_cameras.read_text())
    if len(previous["images"]) != 3:
        raise ValueError("Expected the exact r1 three-view camera set")
    pins = [(candidate, args.candidate_sha256), (decoded, args.decoded_sha256),
            (HERE / "right_hand_refined.glb", "0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef"),
            (dao, "f983ee7463db688febcec5fd75b90109eb13afa2c4c5564d221659b98a12aa0c"),
            (old_cameras, sha(old_cameras))]
    for path, expected in pins:
        if sha(path) != expected:
            raise ValueError("Changed input: " + str(path))
    scene, camera = COMMON.STUDIO.setup_scene(1200, 24)
    scene.render.resolution_y = 900
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.cycles.device = "CPU"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    camera.data.type = "PERSP"
    camera.data.sensor_width = 36
    camera.data.clip_start = .005
    hand, rigs = COMMON.import_at(decoded, "RightGripRoot_RefinementV2", (0, 0, 0))
    COMMON.import_at(dao, "Formal_Dao_ActualKTX", (0, 0, 0))
    COMMON.pose(rigs, scene, 1.)
    manifest = {
        "scope": "native hand v2 closed contact evidence; APK/Emulator validation belongs to Root",
        "candidate_sha256": args.candidate_sha256, "decoded_sha256": args.decoded_sha256,
        "camera_source": str(old_cameras.relative_to(REPO)), "camera_source_sha256": sha(old_cameras),
        "cameras_identical_to_r1": True, "threads": 2,
        "hand_and_dao_pixels": "actual KTX level0 decoded companions",
        "materials_overridden": False, "root_and_model_scale_changed": False,
        "pose_seconds": 1., "surface_geometry": COMMON.evaluated_geometry(hand), "images": [],
    }
    out = HERE / "previews_v2"
    out.mkdir(exist_ok=True)
    for source_view in previous["images"]:
        name = source_view["view"]
        camera.location = Vector(source_view["camera_blender_metres"])
        target = Vector(source_view["camera_target_blender_metres"])
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.lens = source_view["lens_mm"]
        path = out / ("grip_0.3m_" + name + ".png")
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        manifest["images"].append({
            "view": name, "file": str(path.relative_to(REPO)), "sha256": sha(path),
            "camera_blender_metres": list(camera.location),
            "camera_target_blender_metres": list(target),
            "camera_distance_to_grip_metres": camera.location.length,
            "lens_mm": camera.data.lens,
        })
        (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print("READY", path.name, flush=True)
    for path, expected in pins:
        if sha(path) != expected:
            raise ValueError("Input changed during rendering: " + str(path))


if __name__ == "__main__":
    main()
