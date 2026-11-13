"""Render one pinned native right-hand candidate in three 0.3m contact views.

One Blender process, two CPU threads. Materials come from actual KTX level-0
decoded companions; the runtime GLB keeps its original KTX payloads.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
PARENT = HERE.parent
SPEC = importlib.util.spec_from_file_location("native_hand_render", PARENT / "render_hands.py")
COMMON = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMMON)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import bpy
    from mathutils import Vector

    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--decoded-sha256", required=True)
    parser.add_argument("--palm-normal", type=float, nargs=3, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    candidate = HERE / "right_hand_refined.glb"
    decoded = HERE / "right_hand_refined_decoded.glb"
    dao = PARENT / "compression/decoded/dao_grip_decoded.glb"
    formal = REPO / "ArtSource/tripo-warrior/library/dao_grip.glb"
    baseline = PARENT / "right_hand.glb"
    pins = [(candidate, args.candidate_sha256), (decoded, args.decoded_sha256),
            (baseline, "5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d"),
            (formal, "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0"),
            (dao, "f983ee7463db688febcec5fd75b90109eb13afa2c4c5564d221659b98a12aa0c")]
    for path, expected in pins:
        if sha(path) != expected:
            raise ValueError("Changed render input: " + str(path))
    scene, camera = COMMON.STUDIO.setup_scene(1200, 24)
    scene.render.resolution_y = 900
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.cycles.device = "CPU"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    camera.data.type = "PERSP"
    camera.data.lens = 30
    camera.data.sensor_width = 36
    camera.data.clip_start = .005
    hand, rigs = COMMON.import_at(decoded, "Refined_Right_GripRoot", (0, 0, 0))
    COMMON.import_at(dao, "Actual_Formal_Dao", (0, 0, 0))
    COMMON.pose(rigs, scene, 1.)

    # glTF +Y-up coordinates become Blender +Z-up on import.
    def blender_vector(vector):
        return Vector((vector.x, -vector.z, vector.y))

    normal = Vector(args.palm_normal)
    if not all(abs(v) < 2 for v in normal) or normal.length < .9:
        raise ValueError("Expected a finite unit anatomical palm normal")
    normal.normalize()
    shaft = Vector((0, 0, 1))
    up = Vector((0, 1, 0))
    directions = [("front", normal + shaft * .18 + up * .15),
                  ("back", -normal + shaft * .50 + up * .30),
                  ("oblique", normal * .60 - shaft * .65 + up * .45 + Vector((-.35, 0, 0)))]
    manifest = {
        "scope": "native APK right-hand grip candidate contact evidence; no device claim",
        "threads": 2, "blender_version": bpy.app.version_string,
        "pose": "actual grip animation sampled at 1 second",
        "hand_pixels": "actual unchanged 1536 KTX level 0 decoded companion",
        "dao_pixels": "actual formal db28 KTX level 0 decoded companion",
        "materials_overridden": False, "model_scale_changed": False,
        "root_and_dao": "both identity at actual RightGripRoot/dao Grip",
        "candidate_sha256": args.candidate_sha256,
        "decoded_sha256": args.decoded_sha256,
        "palm_normal_player": list(normal),
        "surface_geometry": COMMON.evaluated_geometry(hand), "images": [],
    }
    out = HERE / "previews"
    out.mkdir(exist_ok=True)
    for name, direction in directions:
        camera.location = blender_vector(direction.normalized()) * .3
        target = Vector((0, 0, 0))
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = out / ("grip_0.3m_" + name + ".png")
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        manifest["images"].append({
            "view": name, "file": str(path.relative_to(REPO)), "sha256": sha(path),
            "camera_blender_metres": list(camera.location),
            "camera_distance_to_grip_metres": camera.location.length,
            "camera_target_blender_metres": list(target), "lens_mm": camera.data.lens,
        })
        (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print("READY", path.name, flush=True)
    for path, expected in pins:
        if sha(path) != expected:
            raise ValueError("Render input changed during rendering: " + str(path))


if __name__ == "__main__":
    main()
