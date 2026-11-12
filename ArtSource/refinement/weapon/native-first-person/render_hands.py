"""Render the actual private skinned hand candidates beside the pinned dao.

Run in Blender background. PNG companions carry identical non-image data to
the KTX2 candidates. This is offline asset evidence, not a PICO screenshot.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SPEC = importlib.util.spec_from_file_location(
    "hand_review_studio", REPO / "ArtSource/refinement/grip/render_grip_candidates.py"
)
STUDIO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STUDIO)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_at(path, name, position):
    import bpy

    before = set(bpy.data.objects)
    # Blender's glTF importer otherwise creates a hidden 1m-radius icosphere
    # as a bone display shape. It is not part of the asset/rendered surface.
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    objects = set(bpy.data.objects) - before
    parent = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(parent)
    for obj in objects:
        if obj.parent not in objects:
            obj.parent = parent
    parent.location = position
    return parent, [obj for obj in objects if obj.type == "ARMATURE"]


def pose(rigs, scene, seconds):
    import bpy

    for rig in rigs:
        animation = rig.animation_data
        if animation is None:
            raise ValueError("Candidate has no actual skeletal animation")
        animation.action = None
        animation.use_nla = True
        tracks = [track for track in animation.nla_tracks if track.name == "grip"]
        if len(tracks) != 1:
            raise ValueError("Expected exactly one grip animation track")
        for track in animation.nla_tracks:
            track.mute = track != tracks[0]
            track.is_solo = False
        strip = tracks[0].strips[0]
        # Move the entire strip, not just its start boundary, so the sampled
        # endpoint is genuinely time 0/1 rather than a HOLD extrapolation.
        strip.frame_start_ui = 63 + strip.action_frame_start - seconds * scene.render.fps
        strip.influence = 1
        strip.mute = False
    scene.frame_set(62)
    scene.frame_set(63)
    bpy.context.view_layer.update()


def evaluated_geometry(root):
    import bpy

    depsgraph = bpy.context.evaluated_depsgraph_get()
    points = []
    loose_vertices = 0
    for obj in root.children_recursive:
        if (obj.type != "MESH" or obj.hide_render or
                (obj.users_collection and all(c.hide_render for c in obj.users_collection))):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            # Blender may add loose helper vertices for retained unused joints.
            # Only face-referenced vertices describe the visible hand surface.
            used = {index for face in mesh.polygons for index in face.vertices}
            loose_vertices += len(mesh.vertices) - len(used)
            points.extend(evaluated.matrix_world @ mesh.vertices[index].co for index in sorted(used))
        finally:
            evaluated.to_mesh_clear()
    if not points:
        raise ValueError("No evaluated hand geometry")
    return {
        "face_referenced_vertices": len(points),
        "ignored_loose_vertices": loose_vertices,
        "bounds_min": [min(p[i] for p in points) for i in range(3)],
        "bounds_max": [max(p[i] for p in points) for i in range(3)],
        "position_digest": hashlib.sha256(
            ";".join(",".join(f"{v:.8f}" for v in point) for point in points).encode()
        ).hexdigest(),
    }


def main():
    import bpy
    from mathutils import Vector

    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--decoded", action="store_true")
    args = parser.parse_args(arguments)
    output = HERE / ("previews_ktx" if args.decoded else "previews")
    output.mkdir(exist_ok=True)
    dao_reference_png = REPO / "ArtSource/refinement/weapon/stage2/dao_grip_refined.glb"
    dao = (HERE / "compression/decoded/dao_grip_decoded.glb" if args.decoded
           else dao_reference_png)
    formal_dao = REPO / "ArtSource/tripo-warrior/library/dao_grip.glb"
    if digest(dao_reference_png) != "a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637":
        raise ValueError("Pinned dao PNG source changed")
    if digest(formal_dao) != "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0":
        raise ValueError("Pinned formal dao changed")
    inputs = {
        side: HERE / (f"compression/decoded/{name}_hand_decoded.glb" if args.decoded
                      else f"{name}_hand_png.glb")
        for side, name in (("R", "right"), ("L", "left"))
    }
    identities = {side: {"path": str(path.relative_to(REPO)), "sha256": digest(path)}
                  for side, path in inputs.items()}
    manifest = {
        "scope": ("offline actual final KTX-decoded hand and formal dao companions"
                  if args.decoded else "offline actual skinned hand PNG companions and formal dao PNG companion"),
        "hand_pixels_from_final_ktx": args.decoded,
        "dao_pixels_from_final_ktx": args.decoded,
        "pico_device_verified": False,
        "blender_version": bpy.app.version_string,
        "import_bone_shapes_disabled": True,
        "coordinate_frame": "Blender import of glTF +Y up/-Z forward; no model rescaling",
        "hand_inputs": identities,
        "dao_render_input": {"path": str(dao.relative_to(REPO)), "sha256": digest(dao)},
        "dao_formal": {"path": str(formal_dao.relative_to(REPO)), "sha256": digest(formal_dao)},
        "camera_distance_reference": "Euclidean distance from camera to actual right Grip",
        "near_view": "0.3m hand/contact crop; blade tip intentionally outside frame",
        "lighting": "offline neutral studio, AgX, no viewport-only material overrides",
        "images": [],
    }
    right_position = Vector((.11, 0, 0))
    left_position = Vector((-.14, -.08, -.015))
    states = (("equipped_default", {"R": 1., "L": 0.}),
              ("open", {"R": 0., "L": 0.}),
              ("closed", {"R": 1., "L": 1.}))
    for label, hand_times in states:
        scene, camera = STUDIO.setup_scene(1200, 32)
        scene.render.resolution_y = 900
        scene.render.threads_mode = "FIXED"
        scene.render.threads = 4
        scene.view_settings.view_transform = "AgX"
        camera.data.type = "PERSP"
        camera.data.clip_start = .005
        camera.data.lens = 22
        camera.data.sensor_width = 36
        parents, rigs = {}, {}
        for side, position in (("R", right_position), ("L", left_position)):
            parent, armatures = import_at(inputs[side], "Candidate_" + side, position)
            parents[side] = parent
            rigs[side] = armatures
        import_at(dao, "Formal_Dao_PNG_Companion", right_position)
        for side, armatures in rigs.items():
            pose(armatures, scene, hand_times[side])
        geometry = {side: evaluated_geometry(parent) for side, parent in parents.items()}
        for distance, view, offset in ((.3, "front", (.12, -.94, .32)),
                                       (1., "front", (.12, -.94, .32)),
                                       (1., "reverse", (.65, .65, .40))):
            direction = Vector(offset).normalized()
            camera.location = right_position + direction * distance
            target = Vector((-.005, .025 if distance == .3 else .27, 0))
            camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
            suffix = "" if view == "front" else "_" + view
            path = output / f"hands_dao_{label}_{distance:.1f}m{suffix}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            manifest["images"].append({
                "file": str(path.relative_to(REPO)), "sha256": digest(path),
                "grip_seconds_by_hand": hand_times, "state": label, "view": view,
                "pose_semantics": ("equipped R holds dao closed; L relaxed open"
                                   if label == "equipped_default" else "animation boundary study; not default equipped display"),
                "distance_to_right_grip_metres": (camera.location - right_position).length,
                "camera_location": list(camera.location), "camera_target": list(target),
                "lens_mm": camera.data.lens, "sensor_mm": camera.data.sensor_width,
                "right_grip_world": list(right_position), "left_wrist_world": list(left_position),
                "evaluated_hand_geometry": geometry,
            })
            (output / "render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            print("READY", path.name, flush=True)
    for side, path in inputs.items():
        if digest(path) != identities[side]["sha256"]:
            raise ValueError("Hand input changed during rendering")
    if digest(dao) != manifest["dao_render_input"]["sha256"]:
        raise ValueError("Dao input changed during rendering")


if __name__ == "__main__":
    main()
