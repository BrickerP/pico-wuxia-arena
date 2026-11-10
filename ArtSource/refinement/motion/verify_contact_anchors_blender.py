"""Cross-check the JSON evaluator against Blender's imported NLA bone poses."""

import json
import math
import argparse
import hashlib
import sys
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
report = json.loads((HERE / "proxy_alignment_profiles.json").read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--actor", choices=("base", "indigo", "veteran"))
arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
args = parser.parse_args(arguments)
results = []
for actor in report["actors"]:
    if args.actor and actor["actor"] != args.actor:
        continue
    source = ROOT / actor["source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != actor["sha256"]:
        raise RuntimeError("source hash differs from measured profile: " + actor["actor"])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(source))
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
    results.append({"actor": actor["actor"], "source_sha256": actor["sha256"],
                    "verified_proxy_points": sum(len(key["proxies"]) for key in actor["keyposes"]),
                    "maximum_proxy_position_error_metres": maximum_error})
    print(results[-1])

retained_sources = []
if args.actor:
    previous = json.loads((HERE / "blender_crosscheck.json").read_text())
    replacement = results[0]
    results = [replacement if item["actor"] == args.actor else item for item in previous["results"]]
    retained_sources = [{"actor": actor["actor"], "profile_source_sha256": actor["sha256"],
                         "verification_source_sha256": next(
                             (item.get("source_sha256") for item in previous["results"]
                              if item["actor"] == actor["actor"]), None),
                         "status": "Prior numerical result retained; this actor was not rechecked."}
                        for actor in report["actors"] if actor["actor"] != args.actor]

output = {"blender_version": bpy.app.version_string, "source_evaluator": "measure_contact_anchors.py",
          "comparison": "all seven slash keyposes, three independently calibrated bone-local points per actor",
          "frame_mapping": "strip.frame_start + (sourceSeconds * fps - strip.action_frame_start) * strip.scale",
          "bone_basis": "calibrate local points in imported idle@1.0 bone matrices; imported bone bases differ from glTF joint bases",
          "diagnostic_tolerance_metres": 0.001,
          "rechecked_actors": [args.actor] if args.actor else [actor["actor"] for actor in report["actors"]],
          "retained_prior_result_sources": retained_sources,
          "passed": all(item["maximum_proxy_position_error_metres"] <= 0.001 for item in results),
          "results": results}
(HERE / "blender_crosscheck.json").write_text(json.dumps(output, indent=2) + "\n")
if not output["passed"]:
    raise RuntimeError("source/Blender keypose comparison exceeds 1 mm diagnostic threshold")
