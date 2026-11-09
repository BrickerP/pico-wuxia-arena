"""Prepare a CC0 greybox character and in-place action candidates.

Run with Blender 4.5 LTS. The source GLB is Quaternius's UAL2 Standard, not a
finished wuxia character. Root translation is removed from candidate clips;
two short project-authored reactions are based on poses from the same rig.
The review-only blade and studio are not exported.
"""

import math
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


OUT = Path(__file__).resolve().parent
SOURCE = OUT / "source" / "UAL2_Standard.glb"
FPS = 30
SELECT = {
    "Idle_Shield_Loop": "Graybox_Idle_Shield",
    "Sword_Regular_A": "Sword_A_InPlace",
    "Sword_Regular_A_Rec": "Sword_A_Recovery_InPlace",
    "Sword_Regular_B": "Sword_B_InPlace",
    "Sword_Regular_B_Rec": "Sword_B_Recovery_InPlace",
    "TreeChopping_Loop": "Overhead_Chop_Candidate",
    "Sword_Block": "Sword_Block_InPlace",
}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.render.fps = FPS
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
rig = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
body = next(obj for obj in bpy.data.objects if obj.type == "MESH" and
            any(mod.type == "ARMATURE" and mod.object == rig for mod in obj.modifiers))

source_actions = {action.name: action for action in bpy.data.actions}
missing = set(SELECT) - set(source_actions)
if missing:
    raise ValueError("source clips missing: " + ", ".join(sorted(missing)))
rig.animation_data.action = None
for action in list(bpy.data.actions):
    if action.name not in SELECT:
        bpy.data.actions.remove(action)

actions = {}
for source_name, output_name in SELECT.items():
    action = source_actions[source_name]
    action.name = output_name
    action.use_fake_user = True
    # The published Standard clips contain cumulative root offsets even for
    # names without an _RM suffix. The fixed-position greybox needs root
    # translation removed; all other bone channels remain unchanged.
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(action.slots[0])
            if bag is None:
                continue
            for curve in bag.fcurves:
                if curve.data_path == 'pose.bones["root"].location':
                    for key in curve.keyframe_points:
                        key.co.y = key.handle_left.y = key.handle_right.y = 0.0
                    curve.update()
    actions[output_name] = action


def bind(action):
    rig.animation_data.action = action
    rig.animation_data.action_slot = action.slots[0]


def pose_at(action, frame):
    bind(action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return {bone.name: (bone.location.copy(), bone.rotation_quaternion.copy(), bone.scale.copy())
            for bone in rig.pose.bones}


def make_reaction(name, baseline, frames):
    """Key a small, visible torso recoil while keeping the original skeleton."""
    rig.animation_data.action = None
    for frame, amplitude in frames:
        for bone in rig.pose.bones:
            location, rotation, scale = baseline[bone.name]
            bone.rotation_mode = "QUATERNION"
            bone.location = location
            bone.scale = scale
            bend = {"spine_02": -.14, "spine_03": -.10, "Head": .10,
                    "upperarm_l": .06, "upperarm_r": -.06}.get(bone.name, 0)
            bone.rotation_quaternion = rotation @ Quaternion((1, 0, 0), bend*amplitude)
            bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
            bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)
    result = rig.animation_data.action
    result.name = name
    result.use_fake_user = True
    actions[name] = result
    return result


idle_pose = pose_at(actions["Graybox_Idle_Shield"], 0)

# The source combo steps substantially even after root translation is removed.
# For the fixed-position greybox, keep the pelvis and both legs at the sampled
# idle pose while retaining the source torso/arm attack channels. This is a
# rough candidate for testing, not a final footwork or combat animation.
lower_body = {"pelvis", "thigh_l", "calf_l", "foot_l", "ball_l", "ball_leaf_l",
              "thigh_r", "calf_r", "foot_r", "ball_r", "ball_leaf_r"}
for name in ("Sword_A_InPlace", "Sword_A_Recovery_InPlace",
             "Sword_B_InPlace", "Sword_B_Recovery_InPlace"):
    action = actions[name]
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(action.slots[0])
            if bag is None:
                continue
            for curve in bag.fcurves:
                for bone_name in lower_body:
                    prefix = 'pose.bones["%s"].' % bone_name
                    if not curve.data_path.startswith(prefix):
                        continue
                    prop = curve.data_path[len(prefix):]
                    values = {"location": idle_pose[bone_name][0],
                              "rotation_quaternion": idle_pose[bone_name][1],
                              "scale": idle_pose[bone_name][2]}.get(prop)
                    if values is None:
                        continue
                    value = values[curve.array_index]
                    for key in curve.keyframe_points:
                        key.co.y = key.handle_left.y = key.handle_right.y = value
                    curve.update()

guard_pose = pose_at(actions["Sword_Block_InPlace"], 12)
make_reaction("Graybox_Hit_Recoil", idle_pose, [(1, 0), (4, 1), (10, 0)])
make_reaction("Graybox_Parry_Stagger", idle_pose, [(1, 0), (5, 1.5), (12, .6), (18, 0)])
make_reaction("Graybox_Guard_Hold", guard_pose, [(1, 0), (15, .12), (30, 0)])

# Keep the rig and skinned mannequin together; the project owns no gameplay
# controller here. The source joint hand_r is only an attachment candidate.
asset = bpy.data.collections.new("GRAYBOX_ASSET")
scene.collection.children.link(asset)
for obj in (rig, body):
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    asset.objects.link(obj)
rig["source"] = "Quaternius Universal Animation Library 2 Standard, CC0"
rig["attachment_candidate"] = "hand_r; grip alignment not yet validated"

studio = bpy.data.collections.new("REVIEW_STUDIO")
scene.collection.children.link(studio)
world = bpy.data.worlds.new("Review neutral")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (.12, .15, .18, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45
scene.world = world


def area(name, position, target, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = size
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat("-Z", "Y").to_euler()


area("Review key", (2,-3,4), (0,0,1), 250, 3.0)
area("Review fill", (-2,-1,2), (0,0,1), 90, 2.0)
camera_data = bpy.data.cameras.new("Review camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 2.5
camera = bpy.data.objects.new("Review camera", camera_data)
studio.objects.link(camera)
camera.location = (2.2,-4.0,2.0)
camera.rotation_euler = (Vector((0,0,1.0))-camera.location).to_track_quat("-Z","Y").to_euler()
scene.camera = camera

# Simple blade-shaped pointer attached only for pose inspection. Its position
# is not a validated grip or gameplay attachment and it is excluded from GLB.
blade_mesh = bpy.data.meshes.new("Review pointer mesh")
blade_mesh.from_pydata([(-.018,0,-.004),(.018,0,-.004),(.014,.72,-.002),
                        (-.014,.72,-.002),(-.018,0,.004),(.018,0,.004),
                        (.014,.72,.002),(-.014,.72,.002)], [],
                       [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
blade_mesh.update()
pointer = bpy.data.objects.new("Review-only blade pointer", blade_mesh)
studio.objects.link(pointer)
pointer.parent = rig
pointer.parent_type = "BONE"
pointer.parent_bone = "hand_r"
pointer.location = (0,0,0)
pointer_material = bpy.data.materials.new("Review pointer | pale steel")
pointer_material.diffuse_color = (.48,.52,.54,1)
pointer_material.use_nodes = True
pointer_material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (.48,.52,.54,1)
blade_mesh.materials.append(pointer_material)

# Orient the review pointer once in the hand's local space so that the guard
# pose reads as a blade crossing the body. This is not the final dao grip.
bind(actions["Graybox_Guard_Hold"])
scene.frame_set(1)
bpy.context.view_layer.update()
world_direction = Vector((.65, -.06, .55)).normalized()
local_direction = pointer.matrix_world.to_quaternion().inverted() @ world_direction
pointer.rotation_mode = "QUATERNION"
pointer.rotation_quaternion = Vector((0,1,0)).rotation_difference(local_direction)

scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 720
scene.render.resolution_y = 850
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
bind(actions["Graybox_Guard_Hold"])
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "graybox_candidate.blend"))

bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
body.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(OUT / "graybox_candidate.glb"),
                          export_format="GLB", use_selection=True,
                          export_yup=True, export_animations=True,
                          export_animation_mode="BROADCAST", export_extras=True)

for action_name, frame, scale, filename in (
    ("Graybox_Guard_Hold", 1, 2.7, "graybox_review_guard.png"),
    ("Sword_A_InPlace", 7, 3.0, "graybox_review_attack_a.png"),
    ("Sword_B_InPlace", 8, 3.6, "graybox_review_attack_b.png"),
    ("Overhead_Chop_Candidate", 0, 3.2, "graybox_review_overhead_raise.png"),
    ("Overhead_Chop_Candidate", 7, 3.2, "graybox_review_overhead_impact.png"),
    ("Graybox_Hit_Recoil", 4, 2.7, "graybox_review_hit.png"),
):
    bind(actions[action_name])
    scene.frame_set(frame)
    camera_data.ortho_scale = scale
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
