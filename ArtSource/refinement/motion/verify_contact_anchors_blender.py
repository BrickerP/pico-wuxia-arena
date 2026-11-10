"""Cross-check the JSON evaluator against Blender's imported NLA bone poses."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
report = json.loads((HERE / "proxy_alignment_profiles.json").read_text())
results = []
for actor in report["actors"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(ROOT / actor["source"]))
    armature = next(obj for obj in scene.objects if obj.type == "ARMATURE")
    root = scene.objects.get("TripoWarrior_Root")
    if root is None:
        raise RuntimeError("character root missing after import")
    animation_data = armature.animation_data
    animation_data.action = None
    def select(clip, seconds):
        selected = None
        for track in animation_data.nla_tracks:
            track.mute = track.name != clip
            if not track.mute:
                selected = track.strips[0]
        if selected is None:
            raise RuntimeError("imported NLA track missing: " + clip)
        # glTF time zero is action frame zero. Imported NLA strips start at
        # scene/action frame one, so mapping source seconds must subtract
        # action_frame_start rather than adding an extra frame.
        timeline_frame = selected.frame_start + (
            seconds * scene.render.fps - selected.action_frame_start
        ) * selected.scale
        whole_frame = math.floor(timeline_frame)
        scene.frame_set(whole_frame, subframe=timeline_frame - whole_frame)

    select("idle", 1.0)
    local_points = {}
    for role, point in actor["calibration"]["legacy_points_metres"].items():
        bone_name = actor["keyposes"][0]["proxies"][role]["owner_bone"]
        bone = armature.pose.bones[bone_name]
        bone_to_root = root.matrix_world.inverted() @ armature.matrix_world @ bone.matrix
        x, y, z = point
        # Bone-local bases are altered by Blender's importer. Calibrate them
        # independently in Blender instead of assuming a global axis swap.
        local_points[role] = bone_to_root.inverted() @ Vector((x, -z, y))
    maximum_error = 0.0
    for key in actor["keyposes"]:
        select("slash", key["source_seconds"])
        for role, proxy in key["proxies"].items():
            bone = armature.pose.bones[proxy["owner_bone"]]
            point_blender = root.matrix_world.inverted() @ armature.matrix_world @ bone.matrix @ local_points[role]
            point_gltf = (point_blender.x, point_blender.z, -point_blender.y)
            expected = proxy["root_position_metres"]
            error = math.sqrt(sum((a - b) ** 2 for a, b in zip(point_gltf, expected)))
            maximum_error = max(maximum_error, error)
    results.append({"actor": actor["actor"], "maximum_proxy_position_error_metres": maximum_error})
    print(results[-1])

output = {"blender_version": bpy.app.version_string, "source_evaluator": "measure_contact_anchors.py",
          "comparison": "all seven slash keyposes, three independently calibrated bone-local points per actor",
          "frame_mapping": "strip.frame_start + (sourceSeconds * fps - strip.action_frame_start) * strip.scale",
          "bone_basis": "calibrate local points in imported idle@1.0 bone matrices; imported bone bases differ from glTF joint bases",
          "diagnostic_tolerance_metres": 0.001,
          "passed": all(item["maximum_proxy_position_error_metres"] <= 0.001 for item in results),
          "results": results}
(HERE / "blender_crosscheck.json").write_text(json.dumps(output, indent=2) + "\n")
if not output["passed"]:
    raise RuntimeError("source/Blender keypose comparison exceeds 1 mm diagnostic threshold")
