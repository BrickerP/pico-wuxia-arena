"""Build the first editable dao study and a standalone glTF preview.

Run in a separate Blender process: blender -b --python build_dao.py
The Blender scene's lights and cameras are for the offline review only.
"""

import math
import random
from array import array
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector


OUT = Path(__file__).resolve().parent
random.seed(84)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

asset = bpy.data.collections.new("DAO_ASSET")
scene.collection.children.link(asset)
studio = bpy.data.collections.new("REVIEW_STUDIO")
scene.collection.children.link(studio)


def mesh_object(name, vertices, faces, materials, indices=None):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    asset.objects.link(obj)
    for material in materials:
        mesh.materials.append(material)
    if indices is not None:
        for face, index in zip(mesh.polygons, indices):
            face.material_index = index
    return obj


def material(name, color, metallic, roughness):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return result


steel = material("Steel | forged body", (0.32, 0.36, 0.38), 0.92, 0.32)
edge = material("Steel | sharpened edge", (0.52, 0.55, 0.55), 0.98, 0.22)
spine = material("Steel | dark spine", (0.15, 0.17, 0.17), 0.90, 0.4)
scar = material("Steel | uneven wear", (0.17, 0.20, 0.20), 0.85, 0.52)
brass = material("Brass | aged", (0.30, 0.19, 0.075), 0.78, 0.39)
brass_edge = material("Brass | polished ridges", (0.48, 0.32, 0.12), 0.84, 0.28)
leather = material("Grip | dark oxblood leather", (0.065, 0.024, 0.015), 0.0, 0.82)
cord = material("Grip | worn cord", (0.18, 0.105, 0.061), 0.0, 0.9)


def empty(name, point):
    obj = bpy.data.objects.new(name, None)
    obj.location = point
    obj.empty_display_type = "SPHERE"
    obj.empty_display_size = 0.009
    asset.objects.link(obj)
    return obj


root = empty("DAO_Root", (0, 0, 0))
root["units"] = "metres"
root["contract"] = "proposed anchors; verify orientation and timing with combat"
for name, location in (
    ("Grip", (0, 0, -0.114)),
    ("Blade_Base", (0.022, 0, 0.015)),
    ("Blade_Tip", (0.0122, 0, 0.735)),
):
    empty(name, location).parent = root

# Each ring runs from the spine, across the bevel, around the cutting edge.
# The last sections curve subtly toward the edge, ending in a narrow tip.
sections = [
    (0.015, -0.020, 0.022, 0.0032),
    (0.055, -0.022, 0.025, 0.0032),
    (0.160, -0.023, 0.027, 0.0030),
    (0.330, -0.022, 0.028, 0.0028),
    (0.500, -0.020, 0.029, 0.0026),
    (0.610, -0.014, 0.030, 0.0023),
    (0.680, -0.002, 0.026, 0.0018),
    (0.720, 0.008, 0.019, 0.0010),
    (0.735, 0.0118, 0.0122, 0.0001),
]
vertices = []
for z, back, cutting, half_thickness in sections:
    ridge = back + (cutting - back) * 0.69
    vertices.extend([
        (back, -half_thickness * 0.72, z),
        (ridge, -half_thickness, z),
        (cutting, 0, z),
        (ridge, half_thickness, z),
        (back, half_thickness * 0.72, z),
    ])
faces, indices = [], []
for i in range(len(sections) - 1):
    for j in range(5):
        faces.append((i * 5 + j, i * 5 + (j + 1) % 5,
                      (i + 1) * 5 + (j + 1) % 5, (i + 1) * 5 + j))
        indices.append((0, 1, 1, 0, 2)[j])
faces.extend([(4, 3, 2, 1, 0), tuple((len(sections) - 1) * 5 + j for j in range(5))])
indices.extend([2, 1])
blade = mesh_object("Blade", vertices, faces, [steel, edge, spine], indices)
blade.parent = root

# A small, original brushed-steel colour map is packed into the .blend and
# exported with both interchange files. It is intentionally quiet enough to
# keep the blade silhouette and edge legible at combat distance.
width, height = 256, 1024
grain_rng = random.Random(721)
columns = [grain_rng.uniform(-.025, .025) for _ in range(width)]
streaks = [(grain_rng.randrange(width), grain_rng.randrange(height - 80),
            grain_rng.randrange(35, 200)) for _ in range(75)]
pixels = array("f")
for py in range(height):
    for px in range(width):
        grain = columns[px] + grain_rng.uniform(-.012, .012)
        if any(abs(px - sx) <= 1 and sy <= py < sy + length
               for sx, sy, length in streaks):
            grain -= .055
        value = max(.12, min(.65, .48 + grain))
        pixels.extend((value * .94, value * .99, value, 1.0))
image = bpy.data.images.new("DAO | brushed steel", width=width, height=height)
image.pixels.foreach_set(pixels)
image.filepath_raw = str(OUT / "dao_steel_color.png")
image.file_format = "PNG"
image.save()
image.pack()
nodes = steel.node_tree.nodes
texture = nodes.new("ShaderNodeTexImage")
texture.name = "Original brushed steel"
texture.image = image
steel.node_tree.links.new(texture.outputs["Color"], nodes.get("Principled BSDF").inputs["Base Color"])
uv = blade.data.uv_layers.new(name="BladeUV")
for polygon in blade.data.polygons:
    for loop_index in polygon.loop_indices:
        vertex = blade.data.vertices[blade.data.loops[loop_index].vertex_index].co
        uv.data[loop_index].uv = ((vertex.x + .023) / .054, (vertex.z - .015) / .72)


def elliptical_lathe(name, rings, mat, segments=32):
    points, polygons = [], []
    for z, rx, ry in rings:
        for j in range(segments):
            a = 2 * math.pi * j / segments
            points.append((rx * math.cos(a), ry * math.sin(a), z))
    for i in range(len(rings) - 1):
        for j in range(segments):
            k = (j + 1) % segments
            polygons.append((i * segments + j, i * segments + k,
                             (i + 1) * segments + k, (i + 1) * segments + j))
    polygons.append(tuple(reversed(range(segments))))
    polygons.append(tuple((len(rings) - 1) * segments + j for j in range(segments)))
    obj = mesh_object(name, points, polygons, [mat])
    obj.parent = root
    for polygon in obj.data.polygons[:-2]:
        polygon.use_smooth = True
    return obj


elliptical_lathe("Guard | flared oval", [
    (-0.014, .032, .014), (-0.011, .041, .018), (-0.005, .045, .019),
    (0.000, .039, .017), (0.004, .026, .011)], brass)
elliptical_lathe("Guard | outer rim", [
    (-0.0075, .042, .0185), (-0.006, .046, .0195),
    (-0.0045, .0455, .0195), (-0.003, .042, .0185)], brass_edge)
elliptical_lathe("Blade collar", [
    (0.002, .022, .008), (0.005, .023, .009), (0.018, .022, .008),
    (0.021, .021, .007)], brass)
grip_rings = [
    (-0.218, .012, .010), (-0.210, .016, .012), (-0.165, .017, .013),
    (-0.070, .016, .012), (-0.022, .014, .011), (-0.016, .012, .009)]
elliptical_lathe("Handle core", grip_rings, leather)
elliptical_lathe("Pommel | brass", [
    (-0.232, .009, .008), (-0.229, .015, .012), (-0.223, .018, .014),
    (-0.217, .016, .012), (-0.214, .014, .011)], brass)
for label, z, rx, ry in (("Pommel ring", -0.219, .0175, .0135),
                          ("Grip ferrule", -0.023, .0158, .0122)):
    elliptical_lathe(label, [(z - .002, rx * .97, ry * .97),
                              (z, rx, ry), (z + .002, rx * .97, ry * .97)], brass_edge)

# A continuous, slightly irregular cord wrap makes the grip easy to read in VR.
points, polygons = [], []
segments = 320


def grip_radii(z):
    for a, b in zip(grip_rings, grip_rings[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return (a[1] + (b[1] - a[1]) * t + .0005,
                    a[2] + (b[2] - a[2]) * t + .0005)
    raise ValueError("wrap outside handle")


for i in range(segments + 1):
    t = i / segments
    a = t * math.pi * 2 * 8.5
    z = -0.207 + t * 0.178
    for offset in (-.0031, .0031):
        height_at_edge = z + offset
        rx, ry = grip_radii(height_at_edge)
        points.append((rx * math.cos(a), ry * math.sin(a), height_at_edge))
for i in range(segments):
    polygons.append((2*i, 2*i + 1, 2*i + 3, 2*i + 2))
wrap = mesh_object("Grip | cord wrap", points, polygons, [cord])
wrap.parent = root
for face in wrap.data.polygons:
    face.use_smooth = True

# A restrained set of irregular scars, only on one side, is intentionally not
# mirrored. Geometry rather than procedural shader nodes survives glTF export.
points, polygons = [], []
def front_surface(z, x):
    for a, b in zip(sections, sections[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            back = a[1] + (b[1] - a[1]) * t
            cutting = a[2] + (b[2] - a[2]) * t
            half = a[3] + (b[3] - a[3]) * t
            across = (x - back) / ((cutting - back) * .69)
            return -half * (.72 + .28 * across) - .00004
    raise ValueError("wear outside blade")


for _ in range(27):
    z = random.uniform(.06, .57)
    x = random.uniform(-.014, .007)
    length = random.uniform(.008, .038)
    width = random.uniform(.00012, .00040)
    drift = random.uniform(-.001, .001)
    start = len(points)
    outline = [(x, z), (x + width, z + length * .12),
               (x + drift + width * .35, z + length),
               (x + drift - width * .25, z + length * .9)]
    points.extend((px, front_surface(pz, px), pz) for px, pz in outline)
    polygons.append(tuple(range(start, start + 4)))
wear = mesh_object("Blade | asymmetric wear", points, polygons, [scar])
wear.parent = root

# Round pinheads on the front of the guard.
for i, x in enumerate((-.027, .027)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6,
                                        location=(x, -.017, -.006))
    obj = bpy.context.object
    obj.name = "Guard pin %d" % (i + 1)
    obj.scale = (.0027, .0015, .0027)
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    asset.objects.link(obj)
    obj.data.materials.append(brass_edge)
    obj.parent = root


def area_light(name, location, energy, size, target, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, scale, roll):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = location
    rotation = (Vector(target) - obj.location).to_track_quat("-Z", "Y")
    obj.rotation_euler = (rotation @ Quaternion((0, 0, 1), roll)).to_euler()
    return obj


world = bpy.data.worlds.new("Review neutral")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (.12, .15, .17, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = .4
scene.world = world
area_light("Cool broadbox", (-.8, -1.1, .9), 18, 1.2, (0, 0, .25), (.72, .82, 1))
area_light("Warm rim", (.7, .35, .65), 24, .8, (0, 0, .25), (1, .68, .4))
area_light("Long reflection", (.4, -.6, .2), 12, .6, (0, 0, .3), (1, .95, .82))
full = camera("Review | full", (.52, -2.1, .45), (0, 0, .25), 1.12, -.24)
detail = camera("Review | guard detail", (.25, -1.3, .04), (0, 0, -.045), .27, -.16)
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1000
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.camera = full

# Save a directly editable .blend and export only the asset, never the studio.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "dao_study.blend"))
bpy.ops.object.select_all(action="DESELECT")
for obj in asset.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=str(OUT / "dao_study.glb"), export_format="GLB",
                          use_selection=True, export_extras=True,
                          export_yup=True, export_animations=False)
bpy.ops.export_scene.fbx(filepath=str(OUT / "dao_study.fbx"), use_selection=True,
                         object_types={"EMPTY", "MESH"}, bake_anim=False,
                         axis_forward="-Z", axis_up="Y", use_custom_props=True,
                         path_mode="COPY", embed_textures=True)
scene.render.filepath = str(OUT / "dao_review_full.png")
bpy.ops.render.render(write_still=True)
scene.camera = detail
scene.render.resolution_x = 1000
scene.render.resolution_y = 1000
scene.render.filepath = str(OUT / "dao_review_detail.png")
bpy.ops.render.render(write_still=True)
