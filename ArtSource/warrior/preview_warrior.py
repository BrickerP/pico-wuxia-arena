"""Check and render a continuous offline review of the attached dao.

The interpolation here is a Blender review experiment, not a runtime
controller or a certified combat animation. Run with --render to write MP4;
without it only the per-sample grip and selected torso surface check runs.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Matrix
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
SEQUENCE = (
    ("Guard", "Graybox_Guard_Hold"),
    ("Slash A", "Sword_A_InPlace"),
    ("Recovery A", "Sword_A_Recovery_InPlace"),
    ("Slash B", "Sword_B_InPlace"),
    ("Recovery B", "Sword_B_Recovery_InPlace"),
    ("Overhead", "Overhead_Chop_Candidate"),
    ("Guard", "Graybox_Guard_Hold"),
    ("Hit recoil", "Graybox_Hit_Recoil"),
    ("Guard", "Graybox_Guard_Hold"),
)
TORSO_BONES = {"pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head"}
FPS = 15
BLEND_SAMPLES = 4


def pose_at(rig, action, frame):
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {bone.name: bone.matrix_basis.copy().decompose() for bone in rig.pose.bones}


def interpolate(a, b, weight):
    return {name: (loc.lerp(b[name][0], weight), rot.slerp(b[name][1], weight),
                   scale.lerp(b[name][2], weight))
            for name, (loc, rot, scale) in a.items()}


def sequence_poses(rig):
    sequence = []
    for title, name in SEQUENCE:
        action = bpy.data.actions[name]
        start, end = map(int, action.frame_range)
        frames = list(range(start, end + 1, 2))
        if frames[-1] != end:
            frames.append(end)
        poses = [pose_at(rig, action, frame) for frame in frames]
        if sequence:
            previous = sequence[-1][1]
            for i in range(1, BLEND_SAMPLES + 1):
                sequence.append((title + " transition",
                                 interpolate(previous, poses[0], i / (BLEND_SAMPLES + 1))))
        sequence.extend((title, pose) for pose in poses)
    rig.animation_data.action = None
    return sequence


def torso_face_map(objects):
    result = {}
    for obj in objects:
        indices = {group.index for group in obj.vertex_groups if group.name in TORSO_BONES}
        faces = []
        for face in obj.data.polygons:
            weight = sum(sum(g.weight for g in obj.data.vertices[index].groups if g.group in indices)
                         for index in face.vertices) / len(face.vertices)
            if weight > .5:
                faces.append(tuple(face.vertices))
        if not faces:
            raise ValueError("no weighted torso faces in " + obj.name)
        result[obj.name] = faces
    return result


def check_pose(rig, objects, faces, blade, grip):
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    vertices, polygons = [], []
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        offset = len(vertices)
        vertices.extend(evaluated.matrix_world @ vertex.co for vertex in mesh.vertices)
        polygons.extend(tuple(index + offset for index in face) for face in faces[obj.name])
        evaluated.to_mesh_clear()
    torso = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated = blade.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    blade_tree = BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices],
                                      [tuple(p.vertices) for p in mesh.polygons],
                                      all_triangles=False)
    overlaps = len(torso.overlap(blade_tree))
    evaluated.to_mesh_clear()
    gap = (grip.matrix_world.translation - (rig.matrix_world @ rig.pose.bones["hand_r"].tail)).length
    return overlaps, gap


def apply_pose(rig, pose):
    for name, (loc, rot, scale) in pose.items():
        rig.pose.bones[name].matrix_basis = Matrix.LocRotScale(loc, rot, scale)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--glb", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if args.glb:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.scene.render.fps = 30
        bpy.ops.import_scene.gltf(filepath=str(HERE / "warrior_candidate.glb"))
        if args.render:
            raise ValueError("the review studio exists only in the Blender source")
    else:
        bpy.ops.wm.open_mainfile(filepath=str(HERE / "warrior_candidate.blend"), load_ui=False)
    scene = bpy.context.scene
    rig = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
    objects = [bpy.data.objects["Mannequin"], bpy.data.objects["Warrior garments"]]
    blade, grip = bpy.data.objects["Blade"], bpy.data.objects["Grip"]
    faces = torso_face_map(objects)
    sequence = sequence_poses(rig)
    max_gap, hit_frames = 0.0, []
    for i, (title, pose) in enumerate(sequence):
        apply_pose(rig, pose)
        overlaps, gap = check_pose(rig, objects, faces, blade, grip)
        max_gap = max(max_gap, gap)
        if overlaps:
            hit_frames.append((i, title, overlaps))
    print("PREVIEW %s: %d samples at %d fps, %d blended samples; max grip gap %.6f m; "
          "torso-surface overlap samples %s" %
          ("GLB" if args.glb else "Blender", len(sequence), FPS,
           (len(SEQUENCE)-1)*BLEND_SAMPLES, max_gap, hit_frames))
    if max_gap > .002 or hit_frames:
        raise ValueError("preview grip or sampled torso intersection failed")
    if not args.render:
        return
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for the review MP4")
    scene.render.resolution_x, scene.render.resolution_y = 560, 650
    scene.render.resolution_percentage = 100
    scene.camera.data.ortho_scale = 3.8
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    text_curve = bpy.data.curves.new("Review-only action label", "FONT")
    text_curve.align_x = "LEFT"
    text_curve.size = .095
    text_obj = bpy.data.objects.new("Review-only action label", text_curve)
    scene.collection.objects.link(text_obj)
    text_obj.parent = scene.camera
    text_obj.location = (-1.57, -1.65, -2.0)
    label_material = bpy.data.materials.new("Review label")
    label_material.use_nodes = True
    label_shader = label_material.node_tree.nodes.get("Principled BSDF")
    label_shader.inputs["Base Color"].default_value = (.9, .9, .9, 1)
    label_shader.inputs["Emission Color"].default_value = (.9, .9, .9, 1)
    label_shader.inputs["Emission Strength"].default_value = 1
    text_curve.materials.append(label_material)
    with tempfile.TemporaryDirectory(prefix="pico-warrior-preview-") as temp:
        for i, (title, pose) in enumerate(sequence):
            apply_pose(rig, pose)
            text_curve.body = title + "   |   Blender offline study"
            scene.render.filepath = str(Path(temp) / ("frame_%04d.png" % i))
            bpy.ops.render.render(write_still=True)
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-framerate", str(FPS), "-i", str(Path(temp) / "frame_%04d.png"),
                        "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(HERE / "warrior_review_sequence.mp4")],
                       check=True)
    print("Saved", HERE / "warrior_review_sequence.mp4")


if __name__ == "__main__":
    main()
