"""Render five timed poses and optional frame sequences from a real source clip.

Run with Blender 4.5 Python. Source files, animation curves and skin data are
read only. The same display normalization and studio as render_review are used.
"""

import argparse
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_review import VIEWS, bounds, import_character, set_camera, studio

sys.path.insert(0, str(HERE.parents[1] / "tripo-warrior"))
from prepare_rigged_warrior import accessor_bytes, read_glb


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--clip")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--yaw", type=float, default=-90)
    parser.add_argument("--size", type=int, default=768)
    parser.add_argument("--fractions", nargs="+", type=float, default=[0, .25, .5, .75, 1])
    parser.add_argument("--video", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    if not args.source.is_file():
        parser.error(f"source does not exist: {args.source}")
    if not 64 <= args.size <= 4096:
        parser.error("--size must be between 64 and 4096")
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in args.fractions):
        parser.error("--fractions must be finite values between 0 and 1")
    if not math.isfinite(args.yaw):
        parser.error("--yaw must be finite")
    return args


def source_clip(path, requested):
    document, binary = read_glb(path)
    animations = document.get("animations", [])
    if requested is None:
        if len(animations) != 1:
            raise ValueError("Pass --clip when the source does not contain exactly one clip")
        animation = animations[0]
    else:
        matches = [item for item in animations if item.get("name") == requested]
        if len(matches) != 1:
            raise ValueError(f"Expected one source clip named {requested!r}")
        animation = matches[0]
    if not animation.get("name"):
        raise ValueError("The source clip must have a name for exact NLA selection")
    times = []
    for index in {sampler["input"] for sampler in animation["samplers"]}:
        if document["accessors"][index]["type"] != "SCALAR":
            raise ValueError("Animation timestamps must be SCALAR")
        times.extend(value for value, in struct.iter_unpack("<f", accessor_bytes(document, binary, index)))
    if not times or any(not math.isfinite(value) for value in times):
        raise ValueError("Source clip has invalid timestamps")
    start, end = min(times), max(times)
    if end <= start:
        raise ValueError("Source clip must have a positive duration")
    return animation["name"], start, end


def enable_clip(name, fps):
    owners = []
    hand = []
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            if "R_Hand" in obj.pose.bones:
                hand.append((obj, obj.pose.bones["R_Hand"]))
        data = obj.animation_data
        if data is None:
            continue
        data.action = None
        data.use_nla = True
        tracks = []
        for track in data.nla_tracks:
            track.mute = track.name != name
            track.is_solo = False
            if track.mute:
                continue
            if len(track.strips) != 1:
                raise ValueError(f"Expected one source strip in {obj.name}/{name}")
            strip = track.strips[0]
            if strip.scale != 1 or strip.repeat != 1:
                raise ValueError("Source NLA strip unexpectedly scales or repeats time")
            strip.frame_start = strip.action_frame_start
            strip.influence = 1
            tracks.append({
                "name": track.name,
                "action": strip.action.name,
                "action_frames": [strip.action_frame_start, strip.action_frame_end],
                "source_seconds": [strip.action_frame_start / fps, strip.action_frame_end / fps],
            })
        if tracks:
            owners.append({"object": obj.name, "tracks": tracks})
    if not owners:
        raise ValueError(f"No imported NLA track matches source clip {name!r}")
    if len(hand) != 1:
        raise ValueError("Expected exactly one R_Hand pose bone for the hand closeup")
    return owners, hand[0]


def set_time(scene, seconds):
    frame = seconds * scene.render.fps
    whole = math.floor(frame)
    scene.frame_set(whole, subframe=frame - whole)
    bpy.context.view_layer.update()
    return frame


def main():
    args = arguments()
    clip, start, end = source_clip(args.source, args.clip)
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # glTF converts source seconds to Blender frames using the import-time FPS.
    bpy.context.scene.render.fps = 30
    record = import_character(args.source, args.yaw, preserve_animation=True)
    scene, camera = studio(args.size)
    scene.render.fps = 30
    owners, (armature, hand) = enable_clip(clip, scene.render.fps)
    head = armature.pose.bones.get("Head")
    if head is None:
        raise ValueError("Expected the Head pose bone for the head closeup")
    meshes = [obj for obj in scene.objects if obj.name in record["mesh_names"]]
    manifest = {
        "scope": "offline actual source clip review",
        "source": record,
        "clip": clip,
        "source_time_range_seconds": [start, end],
        "duration_seconds": end - start,
        "fps": scene.render.fps,
        "nla": owners,
        "samples": [],
        "hand_bone": {"object": armature.name, "name": hand.name},
        "head_bone": {"object": armature.name, "name": head.name},
    }
    for index, fraction in enumerate(args.fractions):
        seconds = start + fraction * (end - start)
        frame = set_time(scene, seconds)
        image = args.output / f"pose_{index:02d}.png"
        target, position, scale = VIEWS["whole"]
        set_camera(camera, target, position, scale)
        scene.render.filepath = str(image.resolve())
        bpy.ops.render.render(write_still=True)
        centre = armature.matrix_world @ hand.matrix.translation
        set_camera(camera, centre, centre + Vector((0, -.65, .60)), .48)
        hand_image = args.output / f"hand_{index:02d}.png"
        scene.render.filepath = str(hand_image.resolve())
        bpy.ops.render.render(write_still=True)
        head_target = armature.matrix_world @ ((head.head + head.tail) * .5)
        set_camera(camera, head_target, head_target + Vector((0, -1.6, .15)), .55)
        head_image = args.output / f"head_{index:02d}.png"
        scene.render.filepath = str(head_image.resolve())
        bpy.ops.render.render(write_still=True)
        low, high = bounds(meshes)
        manifest["samples"].append({
            "fraction": fraction, "source_seconds": seconds, "scene_frame": frame,
            "whole_image": str(image.resolve()), "hand_image": str(hand_image.resolve()),
            "head_image": str(head_image.resolve()), "head_target": list(head_target),
            "right_hand_world_metres": list(centre),
            "animated_bounds_metres": [list(low), list(high)],
        })
    if args.video:
        frames = args.output / "frames"
        frames.mkdir(exist_ok=True)
        count = math.ceil((end - start) * scene.render.fps) + 1
        target, position, scale = VIEWS["whole"]
        set_camera(camera, target, position, scale)
        for index in range(count):
            seconds = min(start + index / scene.render.fps, end)
            set_time(scene, seconds)
            scene.render.filepath = str((frames / f"{index:04d}.png").resolve())
            bpy.ops.render.render(write_still=True)
        manifest["video"] = {"frames": str(frames.resolve()), "fps": 30,
                             "frame_count": count, "first_source_second": start,
                             "last_source_second": end}
    (args.output / "motion_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
