"""Check the greybox rig and real action movement in Blender and GLB.

This does not validate a PICO loader, VR grip, combat timing or performance.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
REQUIRED = {
    "Graybox_Idle_Shield", "Sword_A_InPlace", "Sword_A_Recovery_InPlace",
    "Sword_B_InPlace", "Sword_B_Recovery_InPlace", "Overhead_Chop_Candidate",
    "Sword_Block_InPlace", "Graybox_Guard_Hold", "Graybox_Hit_Recoil",
    "Graybox_Parry_Stagger",
}
ATTACKS = {"Sword_A_InPlace", "Sword_B_InPlace", "Overhead_Chop_Candidate"}
PLANTED = ATTACKS | {"Sword_A_Recovery_InPlace", "Sword_B_Recovery_InPlace"}


def require_actions(actions):
    missing = REQUIRED - set(actions)
    if missing:
        raise ValueError("missing actions: " + ", ".join(sorted(missing)))


def check(label, exported):
    scene = bpy.context.scene
    scene.render.fps = 30
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if len(rigs) != 1:
        raise ValueError("expected one rig, got %d" % len(rigs))
    rig = rigs[0]
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and
              any(m.type == "ARMATURE" and m.object == rig for m in obj.modifiers)]
    if len(meshes) != 1:
        raise ValueError("expected one skinned body")
    if exported and any(obj.type in {"LIGHT", "CAMERA"} or obj.name.startswith("Review-only")
                        for obj in bpy.data.objects):
        raise ValueError("review studio leaked into GLB")
    body = meshes[0]
    bones = rig.data.bones
    for name in ("root", "pelvis", "spine_02", "spine_03", "Head", "hand_r", "hand_l"):
        if name not in bones:
            raise ValueError("required bone missing: " + name)
    if not 1.5 < body.dimensions.z < 2.1:
        raise ValueError("unexpected rest-scale height: %.3f" % body.dimensions.z)
    if not body.data.vertices or not body.data.polygons:
        raise ValueError("empty body mesh")
    if any(not vertex.groups for vertex in body.data.vertices):
        raise ValueError("body contains unweighted vertices")
    for vertex in body.data.vertices:
        weights = [group.weight for group in vertex.groups if group.weight > 1e-6]
        if len(weights) > 4 or abs(sum(weights)-1) > .02:
            raise ValueError("skin weights exceed four or are not normalized at vertex %d" % vertex.index)
    actions = {action.name: action for action in bpy.data.actions}
    require_actions(actions)
    try:
        require_actions({name: a for name, a in actions.items() if name != "Graybox_Guard_Hold"})
    except ValueError as error:
        if "Graybox_Guard_Hold" not in str(error):
            raise
    else:
        raise AssertionError("missing guard action was accepted")
    results = {}
    for name in sorted(REQUIRED):
        action = actions[name]
        if not action.slots:
            raise ValueError("action has no slot: " + name)
        rig.animation_data.action = action
        rig.animation_data.action_slot = action.slots[0]
        start, end = action.frame_range
        if end <= start:
            raise ValueError("empty action: " + name)
        frames = range(math.floor(start), math.ceil(end)+1)
        roots, hands, heads, right_feet, left_feet, snapshots = [], [], [], [], [], []
        for frame in frames:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            roots.append((rig.matrix_world @ rig.pose.bones["root"].head).copy())
            hands.append((rig.matrix_world @ rig.pose.bones["hand_r"].head).copy())
            heads.append((rig.matrix_world @ rig.pose.bones["Head"].head).copy())
            right_feet.append((rig.matrix_world @ rig.pose.bones["foot_r"].head).copy())
            left_feet.append((rig.matrix_world @ rig.pose.bones["foot_l"].head).copy())
            snapshot = {}
            for pose_bone in rig.pose.bones:
                matrix = rig.matrix_world @ pose_bone.matrix
                snapshot[pose_bone.name] = (matrix.translation.copy(), matrix.to_quaternion())
            snapshots.append(snapshot)
        root_delta = max((point-roots[0]).length for point in roots)
        hand_delta = max((point-hands[0]).length for point in hands)
        head_delta = max((point-heads[0]).length for point in heads)
        foot_delta = max(max((point-right_feet[0]).length for point in right_feet),
                         max((point-left_feet[0]).length for point in left_feet))
        if root_delta > .002:
            raise ValueError("unexpected root motion in %s: %.4f m" % (name, root_delta))
        if name in ATTACKS and hand_delta < .08:
            raise ValueError("attack has no visible arm motion: " + name)
        if name == "Graybox_Hit_Recoil" and head_delta < .015:
            raise ValueError("hit recoil has no visible head motion")
        if name in PLANTED and foot_delta > .03:
            raise ValueError("planted candidate shifts a foot unexpectedly: " + name)
        results[name] = {"duration": (end-start)/scene.render.fps,
                         "root_delta": root_delta, "hand_delta": hand_delta,
                         "foot_delta": foot_delta, "snapshots": snapshots}
    body.data.calc_loop_triangles()
    materials = {slot.material.name for slot in body.material_slots if slot.material}
    print("PASS %s: %d bones, %d body triangles, %d materials, %d actions" %
          (label, len(bones), len(body.data.loop_triangles), len(materials), len(REQUIRED)))
    for name in sorted(ATTACKS | {"Graybox_Hit_Recoil", "Graybox_Guard_Hold"}):
        result = results[name]
        print("  %s: %.3fs root %.4fm hand %.3fm max foot %.3fm" %
              (name, result["duration"], result["root_delta"],
               result["hand_delta"], result["foot_delta"]))
    return results


bpy.ops.wm.open_mainfile(filepath=str(HERE / "graybox_candidate.blend"), load_ui=False)
source = check("Blender source", False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(HERE / "graybox_candidate.glb"))
exported = check("graybox_candidate.glb", True)
for name in REQUIRED:
    if abs(source[name]["duration"] - exported[name]["duration"]) > .04:
        raise ValueError("action duration changed in GLB: " + name)
    a, b = source[name]["snapshots"], exported[name]["snapshots"]
    if len(a) != len(b):
        raise ValueError("action frame count changed in GLB: " + name)
    max_position, max_angle = 0.0, 0.0
    for sa,sb in zip(a,b):
        if sa.keys() != sb.keys():
            raise ValueError("action bone set changed in GLB: " + name)
        for bone in sa:
            pa,qa = sa[bone]
            pb,qb = sb[bone]
            max_position = max(max_position, (pa-pb).length)
            dot = min(1.0, abs(qa.normalized().dot(qb.normalized())))
            max_angle = max(max_angle, 2*math.acos(dot))
    if max_position > .005 or max_angle > .01:
        raise ValueError("action joints changed in GLB: %s %.4f m %.4f rad" %
                         (name, max_position, max_angle))
print("PASS source/GLB: all joint transforms match within 5 mm and 0.01 rad on every integer frame")
