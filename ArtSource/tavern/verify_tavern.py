"""Check modular roots, metre scale, geometry and textures after round trips.

Run with Blender 4.5 LTS and --python-exit-code 1. This checks interchange in
Blender, not PICO runtime rendering, device performance, or collider behavior.
"""

import math
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
MODULES = {
    "Structure_Root": "Structure",
    "Door_Left_Root": "Door_Left",
    "Door_Right_Root": "Door_Right",
    "Paving_Root": "Paving",
    "Lantern_Root": "Lantern",
}
PIVOTS = {
    "Door_Left_Root": (-.925, 0, 0),
    "Door_Right_Root": (.925, 0, 0),
    "Lantern_Root": (-1.43, -.42, 2.865),
}


def require_modules(objects):
    missing = (set(MODULES) | set(MODULES.values()) | {"Tavern_Root"}) - set(objects)
    if missing:
        raise ValueError("missing asset modules: " + ", ".join(sorted(missing)))
    for parent_name, mesh_name in MODULES.items():
        obj = objects[mesh_name]
        if obj.type != "MESH" or obj.parent is None or obj.parent.name != parent_name:
            raise ValueError("wrong module parent for " + mesh_name)
        parent = objects[parent_name].parent
        if parent is None or parent.name != "Tavern_Root":
            raise ValueError("module is detached from Tavern_Root: " + parent_name)
    for name, expected in PIVOTS.items():
        if (objects[name].matrix_world.translation - Vector(expected)).length > .001:
            raise ValueError("module pivot changed: " + name)


def bounds(obj):
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    if not points or not all(math.isfinite(n) for p in points for n in p):
        raise ValueError("missing or non-finite mesh vertices: " + obj.name)
    low = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    return high - low


def check_textures(name, minimum):
    mat = bpy.data.materials.get(name)
    if mat is None or not mat.use_nodes:
        raise ValueError("textured material missing: " + name)
    nodes = [n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
    valid = 0
    for node in nodes:
        try:
            if len(node.image.pixels) > 0 and math.isfinite(node.image.pixels[0]):
                valid += 1
        except (RuntimeError, IndexError):
            pass
    if valid < minimum:
        raise ValueError("incomplete texture maps in %s: %s" % (name, valid))
    shader = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    required = ("Base Color", "Roughness", "Normal") if minimum == 3 else ("Base Color",)
    if shader is None or any(not shader.inputs[channel].is_linked for channel in required):
        raise ValueError("texture is not connected to required shader inputs: " + name)


def check_nonuniform_roughness(name):
    mat = bpy.data.materials[name]
    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    pending = [link.from_node for link in shader.inputs["Roughness"].links]
    visited = set()
    images = []
    while pending:
        node = pending.pop()
        if node.name in visited:
            continue
        visited.add(node.name)
        if node.type == "TEX_IMAGE" and node.image:
            images.append(node.image)
        for socket in node.inputs:
            pending.extend(link.from_node for link in socket.links)
    if not images:
        raise ValueError("roughness has no upstream image: " + name)
    image = images[0]
    width, height = image.size
    if width < 16 or height < 16:
        raise ValueError("roughness image too small: " + name)
    samples = [image.pixels[4*(int(y*height/16)*width + int(x*width/16)) + 1]
               for y in range(16) for x in range(16)]
    if max(samples) - min(samples) < .08:
        raise ValueError("wetness roughness is unexpectedly uniform: " + name)


def count_separate_slabs(obj):
    # Weld positions only for the check: glTF can split vertices at UV seams.
    coords = [tuple(round(float(n), 6) for n in vertex.co) for vertex in obj.data.vertices]
    parent = {point: point for point in coords}

    def find(point):
        while parent[point] != point:
            parent[point] = parent[parent[point]]
            point = parent[point]
        return point

    for edge in obj.data.edges:
        a, b = (find(coords[index]) for index in edge.vertices)
        if a != b:
            parent[a] = b
    groups = {}
    for point in parent:
        groups.setdefault(find(point), []).append(point)
    slabs = 0
    for group in groups.values():
        if len(group) < 16:
            continue
        extent = [max(p[i] for p in group) - min(p[i] for p in group) for i in range(3)]
        if .45 < extent[0] < .65 and .37 < extent[1] < .49 and .04 < extent[2] < .06:
            slabs += 1
    return slabs


def compare_wet_map(label, source_file, wet_file):
    images = []
    for path in (HERE / "textures" / source_file, HERE / wet_file):
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = "Non-Color"
        images.append(image)
    sample_sets = []
    for image in images:
        width, height = image.size
        samples = [image.pixels[4*(int(y*height/32)*width + int(x*width/32))]
                   for y in range(32) for x in range(32)]
        sample_sets.append(samples)
    dry, wet = sample_sets
    dry_mean, wet_mean = sum(dry)/len(dry), sum(wet)/len(wet)
    if dry_mean-wet_mean < .05 or max(wet)-min(wet) < .08:
        raise ValueError("wetness map is not lower and spatially varied: " + label)
    print("PASS %s roughness samples: source mean %.3f, wet mean %.3f, range %.3f..%.3f" %
          (label, dry_mean, wet_mean, min(wet), max(wet)))
    for image in images:
        bpy.data.images.remove(image)


def check(label, exported):
    bpy.context.view_layer.update()
    objects = {obj.name: obj for obj in bpy.data.objects}
    require_modules(objects)
    try:
        require_modules({name: obj for name, obj in objects.items() if name != "Lantern_Root"})
    except ValueError as error:
        if "Lantern_Root" not in str(error):
            raise
    else:
        raise AssertionError("missing lantern module was accepted")
    if exported and any(obj.type in {"LIGHT", "CAMERA"} for obj in objects.values()):
        raise ValueError("review studio leaked into export")
    structure = bounds(objects["Structure"])
    paving = bounds(objects["Paving"])
    lamp = bounds(objects["Lantern"])
    if not (4.0 < structure.x < 4.6 and 2.9 < structure.z < 3.4):
        raise ValueError("structure scale changed: " + str(structure))
    if not (4.0 < paving.x < 4.5 and 2.8 < paving.y < 3.2):
        raise ValueError("paving scale changed: " + str(paving))
    slabs = count_separate_slabs(objects["Paving"])
    if slabs != 42:
        raise ValueError("expected 42 separate flagstones, found %d" % slabs)
    if not (.30 < lamp.x < .5 and .55 < lamp.z < .85):
        raise ValueError("lantern scale changed: " + str(lamp))
    for name in ("Door_Left", "Door_Right"):
        if not 2.2 < bounds(objects[name]).z < 2.5:
            raise ValueError("door scale changed: " + name)
    for name, count in (("Wood | aged scanned grain", 3),
                        ("Stone | grey scanned granite", 3),
                        ("Plaster | weathered wall", 1),
                        ("Lantern | vermilion paper", 1)):
        check_textures(name, count)
    for name in ("Wood | aged scanned grain", "Stone | grey scanned granite"):
        check_nonuniform_roughness(name)
    triangles = 0
    used = set()
    for mesh_name in MODULES.values():
        obj = objects[mesh_name]
        if not obj.data.polygons or not obj.data.uv_layers:
            raise ValueError("missing faces or UVs: " + mesh_name)
        if any(face.area < 1e-10 for face in obj.data.polygons):
            raise ValueError("zero-area face: " + mesh_name)
        copy = obj.data.copy()
        try:
            invalid = copy.validate(verbose=False, clean_customdata=False)
        finally:
            bpy.data.meshes.remove(copy)
        if invalid:
            raise ValueError("invalid mesh: " + mesh_name)
        obj.data.calc_loop_triangles()
        triangles += len(obj.data.loop_triangles)
        for face in obj.data.polygons:
            if face.material_index >= len(obj.data.materials):
                raise ValueError("invalid material index: " + mesh_name)
            material = obj.data.materials[face.material_index]
            if material is None:
                raise ValueError("empty material: " + mesh_name)
            used.add(material.name)
    print("PASS %s: %d modules, %d separate slabs, %d triangles, %d used materials, "
          "structure %.2f x %.2f m" %
          (label, len(MODULES), slabs, triangles, len(used), structure.x, structure.z))


bpy.ops.wm.open_mainfile(filepath=str(HERE / "tavern_slice.blend"))
check("Blender source", False)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE / "tavern_slice.glb"))
check("tavern_slice.glb", True)
compare_wet_map("wood", "fine_grained_wood_rough_1k.jpg", "tavern_wood_wet_rough.png")
compare_wet_map("stone", "granite_tile_rough_1k.jpg", "tavern_stone_wet_rough.png")
