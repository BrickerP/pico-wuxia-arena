"""Validate source/GLB motion, blade provenance and sampled torso clearance.

A discrete surface test does not establish swept-volume, full-body, hand-grip,
or device/runtime collision. Use preview_warrior.py for blend transitions.
"""

import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
REQUIRED = {
    "Graybox_Idle_Shield", "Sword_A_InPlace", "Sword_A_Recovery_InPlace",
    "Sword_B_InPlace", "Sword_B_Recovery_InPlace", "Overhead_Chop_Candidate",
    "Sword_Block_InPlace", "Graybox_Guard_Hold", "Graybox_Hit_Recoil",
    "Graybox_Parry_Stagger",
}
TORSO_BONES = {"pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head"}
CHECKED = {"Sword_A_InPlace", "Sword_B_InPlace", "Overhead_Chop_Candidate",
           "Graybox_Guard_Hold", "Graybox_Hit_Recoil"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blade_points():
    root = bpy.data.objects["DAO_Root"]
    blade = bpy.data.objects["Blade"]
    transform = root.matrix_world.inverted() @ blade.matrix_world
    points = [tuple(round(v, 5) for v in transform @ vertex.co) for vertex in blade.data.vertices]
    blade.data.calc_loop_triangles()
    triangles = {tuple(sorted(points[index] for index in tri.vertices))
                 for tri in blade.data.loop_triangles}
    markers = {name: tuple(round(v, 5) for v in
                           root.matrix_world.inverted() @ bpy.data.objects[name].matrix_world.translation)
               for name in ("Grip", "Blade_Base", "Blade_Tip")}
    return set(points), triangles, markers


def face_map(objects):
    result = {}
    for obj in objects:
        indices = {group.index for group in obj.vertex_groups if group.name in TORSO_BONES}
        result[obj.name] = [tuple(poly.vertices) for poly in obj.data.polygons
                            if sum(sum(g.weight for g in obj.data.vertices[index].groups
                                       if g.group in indices) for index in poly.vertices)
                            / len(poly.vertices) > .5]
        require(result[obj.name], "empty selected torso on " + obj.name)
    return result


def torso_overlap(objects, faces, blade):
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
                                      [tuple(p.vertices) for p in mesh.polygons], all_triangles=False)
    count = len(torso.overlap(blade_tree))
    evaluated.to_mesh_clear()
    return count


def check(label, expected_weapon, exported):
    scene = bpy.context.scene
    scene.render.fps = 30
    rig = next(obj for obj in bpy.data.objects if obj.type == "ARMATURE")
    require(len(rig.data.bones) == 65, "expected same 65-bone rig")
    objects = [bpy.data.objects["Mannequin"], bpy.data.objects["Warrior garments"]]
    for obj in objects:
        require(any(mod.type == "ARMATURE" and mod.object == rig for mod in obj.modifiers),
                "mesh is not skinned to shared rig: " + obj.name)
        for vertex in obj.data.vertices:
            weights = [group.weight for group in vertex.groups if group.weight > 1e-6]
            require(0 < len(weights) <= 4 and abs(sum(weights)-1) <= .02,
                    "%s vertex %d has invalid skin weights" % (obj.name, vertex.index))
    if exported:
        require(not any(obj.type in {"LIGHT", "CAMERA"} or obj.name.startswith("Review-only")
                        for obj in bpy.data.objects), "review studio leaked into GLB")
    missing = REQUIRED - set(bpy.data.actions.keys())
    require(not missing, "missing actions: " + ", ".join(sorted(missing)))
    dao, grip, blade = (bpy.data.objects[name] for name in ("DAO_Root", "Grip", "Blade"))
    require(dao.parent == rig and dao.parent_type == "BONE" and dao.parent_bone == "hand_r",
            "dao must be attached to hand_r")
    require(blade_points() == expected_weapon, "blade geometry or dao marker differs from original dao GLB")
    faces = face_map(objects)
    results = {}
    total_triangles = 0
    for obj in (objects + [blade, bpy.data.objects["Dao fittings and wear"]]):
        obj.data.calc_loop_triangles()
        total_triangles += len(obj.data.loop_triangles)
    for name in sorted(REQUIRED):
        action = bpy.data.actions[name]
        require(bool(action.slots), "no animation slot for " + name)
        rig.animation_data.action, rig.animation_data.action_slot = action, action.slots[0]
        start, end = action.frame_range
        require(end > start, "empty animation " + name)
        snapshots, tip_x, grip_max, hit_frames = [], [], 0.0, []
        for frame in range(math.floor(start), math.ceil(end) + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            snapshot = {}
            for bone in rig.pose.bones:
                matrix = rig.matrix_world @ bone.matrix
                snapshot[bone.name] = (matrix.translation.copy(), matrix.to_quaternion())
            snapshot["Grip"] = (grip.matrix_world.translation.copy(), grip.matrix_world.to_quaternion())
            snapshot["Blade_Tip"] = (bpy.data.objects["Blade_Tip"].matrix_world.translation.copy(),
                                     bpy.data.objects["Blade_Tip"].matrix_world.to_quaternion())
            snapshots.append(snapshot)
            tip_x.append((frame, snapshot["Blade_Tip"][0].x))
            gap = (grip.matrix_world.translation - (rig.matrix_world @ rig.pose.bones["hand_r"].tail)).length
            grip_max = max(grip_max, gap)
            if name in CHECKED and torso_overlap(objects, faces, blade):
                hit_frames.append(frame)
        require(grip_max <= .002, "%s grip offset %.6f m" % (name, grip_max))
        require(not hit_frames, "%s blade/torso sampled intersections %s" % (name, hit_frames))
        results[name] = {"snapshots": snapshots, "duration": (end-start)/30,
                         "grip_max": grip_max, "tip_x": tip_x}
    print("PASS %s: %d joints, %d asset triangles, %d actions; original dao geometry and markers match" %
          (label, len(rig.data.bones), total_triangles, len(results)))
    for name in sorted(CHECKED):
        result = results[name]
        low = min(result["tip_x"], key=lambda p: p[1])
        high = max(result["tip_x"], key=lambda p: p[1])
        print("  %s: %d integer frames, max grip gap %.6fm, selected torso intersections 0; "
              "tip X min %.3fm@%d max %.3fm@%d" %
              (name, len(result["snapshots"]), result["grip_max"], low[1], low[0], high[1], high[0]))
    return results


def negative_tests(expected_weapon):
    """Corrupt only the in-memory scene to prove checks reject real failures."""
    action = bpy.data.actions["Graybox_Guard_Hold"]
    old_name = action.name
    action.name = "_missing_guard_test"
    try:
        try:
            check("missing guard negative", expected_weapon, False)
        except ValueError as error:
            require("missing actions" in str(error), "unexpected missing-action failure: " + str(error))
        else:
            raise AssertionError("missing guard action was accepted")
    finally:
        action.name = old_name
    marker = bpy.data.objects["Blade_Tip"]
    old_location = marker.location.copy()
    marker.location.x += .02
    bpy.context.view_layer.update()
    try:
        try:
            check("moved tip negative", expected_weapon, False)
        except ValueError as error:
            require("blade geometry or dao marker" in str(error), "unexpected marker failure: " + str(error))
        else:
            raise AssertionError("moved blade marker was accepted")
    finally:
        marker.location = old_location
        bpy.context.view_layer.update()
    dao = bpy.data.objects["DAO_Root"]
    old_location = dao.location.copy()
    dao.location.x += .05
    bpy.context.view_layer.update()
    try:
        try:
            check("shifted grip negative", expected_weapon, False)
        except ValueError as error:
            require("grip offset" in str(error), "unexpected grip failure: " + str(error))
        else:
            raise AssertionError("shifted dao grip was accepted")
    finally:
        dao.location = old_location
        bpy.context.view_layer.update()
    print("PASS negative cases: missing guard, moved blade tip and 5 cm grip shift rejected")


def compare(source, exported):
    maximum_position, maximum_angle = 0.0, 0.0
    for name in REQUIRED:
        a, b = source[name], exported[name]
        require(abs(a["duration"] - b["duration"]) < .04, "duration differs for " + name)
        require(len(a["snapshots"]) == len(b["snapshots"]), "frame count differs for " + name)
        for snapshot_a, snapshot_b in zip(a["snapshots"], b["snapshots"]):
            require(snapshot_a.keys() == snapshot_b.keys(), "bone/marker set differs for " + name)
            for key, (pa, qa) in snapshot_a.items():
                pb, qb = snapshot_b[key]
                maximum_position = max(maximum_position, (pa-pb).length)
                dot = min(1.0, abs(qa.normalized().dot(qb.normalized())))
                maximum_angle = max(maximum_angle, 2*math.acos(dot))
    require(maximum_position <= .005 and maximum_angle <= .01,
            "source/GLB transform difference too large")
    print("PASS source/GLB: all joints, Grip and Blade_Tip at every integer frame; "
          "max difference %.6f m / %.6f rad" % (maximum_position, maximum_angle))


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE.parent / "dao" / "dao_study.glb"))
expected_weapon = blade_points()
require(len(expected_weapon[0]) > 10, "original blade geometry unexpectedly empty")
bpy.ops.wm.open_mainfile(filepath=str(HERE / "warrior_candidate.blend"), load_ui=False)
source = check("Blender source", expected_weapon, False)
negative_tests(expected_weapon)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30
bpy.ops.import_scene.gltf(filepath=str(HERE / "warrior_candidate.glb"))
exported = check("GLB reimport", expected_weapon, True)
compare(source, exported)
