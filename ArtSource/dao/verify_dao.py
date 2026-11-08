"""Check source, FBX and glTF scale, geometry, materials and named anchors.

Run: blender -b --factory-startup --python-exit-code 1 --python verify_dao.py
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
ANCHORS = {"DAO_Root", "Grip", "Blade_Base", "Blade_Tip"}


def check_anchors(objects):
    missing = ANCHORS - set(objects)
    if missing:
        raise ValueError("missing anchors: " + ", ".join(sorted(missing)))
    base = objects["Blade_Base"].matrix_world.translation
    tip = objects["Blade_Tip"].matrix_world.translation
    grip = objects["Grip"].matrix_world.translation
    if not 0.70 < (tip - base).length < 0.74:
        raise ValueError("blade length is not approximately 0.72 m")
    if not 0.10 < (grip - base).length < 0.16:
        raise ValueError("grip-to-blade distance is not approximately 0.13 m")
    return base, tip


def check_edge_positions(blade, base, tip):
    edge_slots = {i for i, material in enumerate(blade.data.materials)
                  if material and material.name.startswith("Steel | sharpened edge")}
    edge_vertices = {index for face in blade.data.polygons
                     if face.material_index in edge_slots for index in face.vertices}
    if not edge_vertices:
        raise ValueError("sharpened edge geometry missing")
    positions = [blade.matrix_world @ blade.data.vertices[index].co for index in edge_vertices]
    for anchor_name, anchor in (("Blade_Base", base), ("Blade_Tip", tip)):
        if min((position - anchor).length for position in positions) > .0005:
            raise ValueError(anchor_name + " no longer sits on the sharpened edge")


def check(label, exported):
    bpy.context.view_layer.update()
    objects = {obj.name: obj for obj in bpy.data.objects}
    base, tip = check_anchors(objects)
    # Exercise the failure path so a missing blade-tip node cannot pass silently.
    try:
        check_anchors({name: obj for name, obj in objects.items() if name != "Blade_Tip"})
    except ValueError as error:
        if "Blade_Tip" not in str(error):
            raise
    else:
        raise AssertionError("missing-anchor case was accepted")

    meshes = [obj for obj in objects.values() if obj.type == "MESH"]
    if not 8 <= len(meshes) <= 25:
        raise ValueError("unexpected mesh count: %d" % len(meshes))
    if exported and any(obj.type in {"LIGHT", "CAMERA"} for obj in objects.values()):
        raise ValueError("the review studio leaked into the asset")
    blade = objects.get("Blade")
    if blade is None or not blade.data.materials:
        raise ValueError("blade or blade material missing")
    check_edge_positions(blade, base, tip)
    try:
        check_edge_positions(blade, base, tip + Vector((.01, 0, 0)))
    except ValueError as error:
        if "Blade_Tip" not in str(error):
            raise
    else:
        raise AssertionError("off-edge blade tip was accepted")
    steel = blade.data.materials[0]
    if not steel.use_nodes:
        raise ValueError("blade material has no shader nodes")
    textures = [node for node in steel.node_tree.nodes
                if node.type == "TEX_IMAGE" and node.image]
    linked = [node for node in textures if any(
        link.from_node == node and link.to_node.type == "BSDF_PRINCIPLED"
        for link in steel.node_tree.links
    )]
    # Packed images can be lazy-loaded after opening a .blend. Reading a pixel
    # forces loading instead of misclassifying an unopened image as absent.
    try:
        valid_image = any(len(node.image.pixels) > 0 and
                          math.isfinite(node.image.pixels[0]) for node in linked)
    except (RuntimeError, IndexError):
        valid_image = False
    if not valid_image:
        raise ValueError("brushed-steel texture did not survive import")
    points = []
    triangles = 0
    for obj in meshes:
        if not obj.data.vertices or not obj.data.polygons:
            raise ValueError("empty mesh: " + obj.name)
        if not obj.data.materials or any(slot.material is None for slot in obj.material_slots):
            raise ValueError("missing material: " + obj.name)
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        points.extend(obj.matrix_world @ vertex.co for vertex in obj.data.vertices)
    if not all(math.isfinite(component) for p in points for component in p):
        raise ValueError("non-finite vertex coordinate")
    if not 0 < triangles < 15000:
        raise ValueError("unexpected triangle count: %d" % triangles)
    # Bounding box diagonal catches unit or axis conversion mistakes without
    # assuming that every importer represents the same axis as 'up'.
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    if not .95 < (high - low).length < 1.05:
        raise ValueError("weapon bounds are not approximately one metre")
    print("PASS %s: %d meshes, %d triangles, blade %.4f m, bounds %.4f m" %
          (label, len(meshes), triangles, (tip - base).length, (high - low).length))


bpy.ops.wm.open_mainfile(filepath=str(HERE / "dao_study.blend"))
check("Blender source", False)
for name, importer in (("dao_study.fbx", bpy.ops.import_scene.fbx),
                       ("dao_study.glb", bpy.ops.import_scene.gltf)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importer(filepath=str(HERE / name))
    check(name, True)
