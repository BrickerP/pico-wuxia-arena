"""Render actual character GLBs in a shared, normalized offline review studio.

Blender -b --factory-startup --threads 4 --python render_review.py -- \
    --before path/to/before.glb --after path/to/after.glb --output review

GLB materials and geometry are preserved. The display-only parent establishes
metre scale and front direction. All views use identical camera transforms.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


VIEWS = {
    "whole": ((0, 0, .94), (3.8, -7, 2.6), 2.40),
    "head": ((0, -.015, 1.61), (.36, -2, 1.76), .50),
    "collar": ((0, -.015, 1.27), (.30, -2, 1.50), .65),
    "right_hand": ((-.77, 0, 1.31), (-.77, -2, 1.66), .52),
    "left_hand": ((.77, 0, 1.31), (.77, -2, 1.66), .52),
    "right_hand_top": ((-.77, 0, 1.31), (-.77, -.08, 2.7), .48),
    "left_hand_top": ((.77, 0, 1.31), (.77, -.08, 2.7), .48),
}


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--before-yaw", type=float, default=0)
    parser.add_argument("--after-yaw", type=float, default=0)
    parser.add_argument("--size", type=int, default=960)
    parser.add_argument("--views", nargs="+", choices=tuple(VIEWS), default=list(VIEWS))
    parser.add_argument("--clay", action="store_true", help="display both sources in neutral grey")
    parser.add_argument("--turntable", action="store_true")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    if args.before is None and args.after is None:
        parser.error("at least one of --before or --after is required")
    if args.size < 64 or args.size > 4096:
        parser.error("--size must be between 64 and 4096")
    for path in (args.before, args.after):
        if path is not None and not path.is_file():
            parser.error(f"source does not exist: {path}")
    return args


def bounds(meshes):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners = [evaluated.matrix_world @ Vector(corner)
               for obj in meshes
               for evaluated in (obj.evaluated_get(depsgraph),)
               for corner in evaluated.bound_box]
    low = Vector(tuple(min(point[axis] for point in corners) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in corners) for axis in range(3)))
    return low, high


def import_character(path, yaw, preserve_animation=False):
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    imported = list(bpy.context.selected_objects)
    meshes = []
    animation_states = []
    for obj in imported:
        if preserve_animation and obj.animation_data is not None:
            data = obj.animation_data
            animation_states.append((obj, data.action, data.use_nla))
            data.action = None
            data.use_nla = False
        elif not preserve_animation:
            obj.animation_data_clear()
        if obj.type == "ARMATURE":
            obj.data.pose_position = "REST"
        if obj.type == "MESH":
            helper = "icosphere" in obj.name.lower() or "icosphere" in obj.data.name.lower()
            obj.hide_render = helper
            if not helper:
                meshes.append(obj)
        elif obj.type in {"CAMERA", "LIGHT"}:
            obj.hide_render = True
    if not meshes:
        raise ValueError(f"No character meshes found in {path}")

    placement = bpy.data.objects.new("Review normalization", None)
    bpy.context.scene.collection.objects.link(placement)
    for obj in imported:
        if obj.parent is None:
            obj.parent = placement
    placement.rotation_euler.z = math.radians(yaw)
    bpy.context.view_layer.update()
    source_low, source_high = bounds(meshes)
    height = source_high.z - source_low.z
    if not math.isfinite(height) or height <= 0:
        raise ValueError(f"Invalid character height in {path}: {height}")
    scale = 1.78 / height
    placement.scale = (scale,) * 3
    placement.location = (
        -(source_low.x + source_high.x) * scale / 2,
        -(source_low.y + source_high.y) * scale / 2,
        -source_low.z * scale,
    )
    bpy.context.view_layer.update()
    low, high = bounds(meshes)
    record = {
        "source": str(path.resolve()),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "yaw_degrees": yaw,
        "uniform_scale": scale,
        "translation_metres": list(placement.location),
        "normalized_bounds_metres": [list(low), list(high)],
        "rest_pose": not preserve_animation,
        "normalization_pose": "REST",
        "mesh_names": [obj.name for obj in meshes],
    }
    if preserve_animation:
        for obj, action, use_nla in animation_states:
            obj.animation_data.action = action
            obj.animation_data.use_nla = use_nla
        for obj in imported:
            if obj.type == "ARMATURE":
                obj.data.pose_position = "POSE"
        bpy.context.view_layer.update()
    return record


def studio(size):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.film_transparent = False
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.fps = 12
    world = bpy.data.worlds.new("Offline character review studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (.07, .09, .12, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = .42
    scene.world = world
    for name, position, power, diameter, color in (
        ("Warm key", (-3, -4.5, 5.5), 900, 5, (1, .84, .69)),
        ("Cool fill", (4.2, -2, 3.5), 650, 4, (.62, .76, 1)),
        ("Edge", (1.2, 3, 4), 1100, 3, (.88, .94, 1)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = power
        data.shape = "DISK"
        data.size = diameter
        data.color = color
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0, 0, 1.2)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -.015))
    floor = bpy.context.object
    mat = bpy.data.materials.new("Studio charcoal floor")
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (.035, .041, .048, 1)
    shader.inputs["Roughness"].default_value = .72
    floor.data.materials.append(mat)
    data = bpy.data.cameras.new("Shared review camera")
    data.type = "ORTHO"
    camera = bpy.data.objects.new("Shared review camera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera


def set_camera(camera, target, position, scale):
    camera.location = position
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = scale


def render_source(stage, path, yaw, args):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    record = import_character(path, yaw)
    if args.clay:
        clay = bpy.data.materials.new("Display-only neutral clay")
        clay.use_nodes = True
        shader = clay.node_tree.nodes.get("Principled BSDF")
        shader.inputs["Base Color"].default_value = (.38, .38, .38, 1)
        shader.inputs["Roughness"].default_value = .7
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH" and not obj.hide_render:
                if not obj.data.materials:
                    obj.data.materials.append(clay)
                for index in range(len(obj.data.materials)):
                    obj.data.materials[index] = clay
    scene, camera = studio(args.size)
    record["renders"] = {}
    for name in args.views:
        target, position, scale = VIEWS[name]
        set_camera(camera, target, position, scale)
        image_path = args.output / f"{stage}_{name}.png"
        scene.render.filepath = str(image_path.resolve())
        bpy.ops.render.render(write_still=True)
        record["renders"][name] = str(image_path.resolve())
    if args.turntable:
        frames = args.output / f"{stage}_turntable"
        frames.mkdir(exist_ok=True)
        target, position, scale = VIEWS["whole"]
        offset = Vector(position) - Vector(target)
        for frame in range(24):
            angle = frame * math.tau / 24
            orbit = Vector((offset.x * math.cos(angle) - offset.y * math.sin(angle),
                            offset.x * math.sin(angle) + offset.y * math.cos(angle),
                            offset.z))
            set_camera(camera, target, Vector(target) + orbit, scale)
            scene.render.filepath = str((frames / f"{frame:04d}.png").resolve())
            bpy.ops.render.render(write_still=True)
        record["turntable"] = {
            "frames": str(frames.resolve()), "fps": 12, "frame_count": 24,
            "motion": "camera orbit about normalized character centre",
        }
    return record


def main():
    args = arguments()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "scope": "offline source GLB rest-pose review",
        "blender_version": bpy.app.version_string,
        "engine": "BLENDER_EEVEE_NEXT",
        "resolution": [args.size, args.size],
        "display_height_metres": 1.78,
        "material_display": "neutral grey clay" if args.clay else "original GLB materials",
        "view_cameras": VIEWS,
        "sources": {},
    }
    for stage, path, yaw in (("before", args.before, args.before_yaw),
                             ("after", args.after, args.after_yaw)):
        if path is not None:
            manifest["sources"][stage] = render_source(stage, path, yaw, args)
            (args.output / "render_manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
