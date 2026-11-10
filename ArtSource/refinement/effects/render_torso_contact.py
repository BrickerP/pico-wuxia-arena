"""Offline same-camera contact study using the active first-opponent runtime GLB.

Blender 4.5 public RNA help was checked for evaluated_get/to_mesh and
mathutils.Vector.rotation_difference. Runtime assets are opened read-only.
"""

import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ACTOR = ROOT / "app/src/main/assets/models/opponents/base.glb"
SOURCE_SECONDS = 2.117
EFFECT_SECONDS = .055
STRENGTH = .65
SIZE = .72 + STRENGTH * .46

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1440
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.fps = 30
scene.world = bpy.data.worlds.new("Offline contact studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.045, .055, .07, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45


def caption_material():
    mat = bpy.data.materials.new("Offline annotations")
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (.78, .82, .85, 1)
    shader.inputs["Emission Color"].default_value = (.78, .82, .85, 1)
    shader.inputs["Emission Strength"].default_value = .6
    return mat


captions = caption_material()
font = bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")


def label(text, position, size=.045):
    data = bpy.data.curves.new(text, "FONT")
    data.body = text
    data.font = font
    data.align_x = "CENTER"
    data.size = size
    obj = bpy.data.objects.new(text, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (math.pi / 2, 0, 0)
    data.materials.append(captions)


def actor(x):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(ACTOR))
    objects = list(bpy.context.selected_objects)
    for obj in objects:
        if obj.type != "ARMATURE":
            continue
        data = obj.animation_data
        if data is None:
            raise RuntimeError("Runtime actor has no imported animation")
        data.action = None
        found = False
        for track in data.nla_tracks:
            track.mute = track.name != "slash"
            if not track.mute:
                found = True
                track.strips[0].frame_start = 64 - SOURCE_SECONDS * scene.render.fps
                track.strips[0].influence = 1
        if not found:
            raise RuntimeError("Runtime slash is absent")
    placement = bpy.data.objects.new("Actor placement", None)
    scene.collection.objects.link(placement)
    placement.location.x = x
    for obj in objects:
        if obj.parent is None:
            obj.parent = placement
    return objects


actors = [actor(-.65), actor(.65)]
scene.frame_set(63)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()


def contact_faces(objects, x):
    cloth, steel = [], []
    for obj in objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            for polygon in mesh.polygons:
                center = evaluated.matrix_world @ polygon.center
                normal = (evaluated.matrix_world.to_3x3() @ polygon.normal).normalized()
                name = mesh.materials[polygon.material_index].name
                if normal.y > -.10:
                    continue
                if ("Steel | forged body" in name or "Steel | sharpened edge" in name) and .80 < center.z < 1.01:
                    steel.append((center.copy(), normal.copy(), name))
                elif .66 < center.z < .88 and abs(center.x - x - .17) < .07:
                    cloth.append((center.copy(), normal.copy(), name))
        finally:
            evaluated.to_mesh_clear()
    if not cloth or not steel:
        raise RuntimeError("Could not resolve actual cloth and steel surfaces")
    # Actual evaluated mesh surface centroids, with a front-facing normal.
    soft = min(cloth, key=lambda face: (face[0].x - x - .17) ** 2 +
               (face[0].z - .76) ** 2 + .1 * (face[0].y + .13) ** 2)
    steel_center = sum((face[0] for face in steel), Vector()) / len(steel)
    metal = min(steel, key=lambda face: (face[0] - steel_center).length_squared)
    return soft, metal


def attach_effect(name, point, normal):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(ROOT / "app/src/main/assets/models/effects" / (name + ".glb")))
    objects = list(bpy.context.selected_objects)
    placement = bpy.data.objects.new("Actual " + name, None)
    scene.collection.objects.link(placement)
    placement.location = point + normal * .008
    placement.rotation_mode = "QUATERNION"
    placement.rotation_quaternion = Vector((0, -1, 0)).rotation_difference(normal)
    placement.scale = (SIZE, SIZE, SIZE)
    duration = .62 if name == "soft_contact" else .44
    progress = EFFECT_SECONDS / duration
    for obj in objects:
        if obj.parent is None:
            obj.parent = placement
        if obj.type != "MESH":
            continue
        key = obj.name.split(".")[0]
        if key == "core":
            scale = .7 + EFFECT_SECONDS * 3
            obj.scale = (scale, 1, scale)
            alpha = 1 - EFFECT_SECONDS / .18
        elif key == "debris":
            scale = .22 + progress * 1.1
            obj.scale = (scale, 1, scale)
            obj.location.z = -.32 * EFFECT_SECONDS ** 2
            obj.location.y = -.14 * EFFECT_SECONDS
            alpha = (1 - progress) ** 2
        else:
            obj.scale = (1, 1, min(1, max(.08, (duration - EFFECT_SECONDS) / .30)))
            obj.location.y = -.004
            alpha = min(1, max(0, (duration - EFFECT_SECONDS) / .24))
        for mat in obj.data.materials:
            shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
            destination = shader.inputs["Alpha"]
            multiplier = mat.node_tree.nodes.new("ShaderNodeMath")
            multiplier.operation = "MULTIPLY"
            link = destination.links[0]
            original = link.from_socket
            mat.node_tree.links.remove(link)
            mat.node_tree.links.new(original, multiplier.inputs[0])
            multiplier.inputs[1].default_value = alpha
            mat.node_tree.links.new(multiplier.outputs[0], destination)


contacts = [contact_faces(objects, x) for objects, x in zip(actors, (-.65, .65))]
for x, pair in zip((-.65, .65), contacts):
    for number, (point, normal, _) in enumerate(pair, 1):
        label(str(number), point + Vector((.11, -.10, .015)), .040)
attach_effect("soft_contact", contacts[1][0][0], contacts[1][0][1])
attach_effect("metal_contact", contacts[1][1][0], contacts[1][1][1])

for name, position, energy, color in (("Wide key", (-3, -4, 4), 650, (1, .84, .70)),
                                      ("Wide fill", (3, -2, 2.5), 420, (.64, .78, 1))):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = 5
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, .9)) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("Identical before after camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 2.5
camera = bpy.data.objects.new("Identical before after camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (0, -5, 1.0)
camera.rotation_euler = (Vector((0, 0, 1.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = camera
label("现役试刀客 · 接触比例与遮挡", (0, -.65, 1.67), .075)
label("同机位 before / after · slash 2.117s · 接触核心55ms · strength 0.65", (0, -.65, 1.56), .041)
label("Before · 正式资产原姿态", (-.65, -.65, .32), .052)
label("After · ①衣料躯干 ②正式钢刀", (.65, -.65, .32), .052)
label("离线制作预览 · 实际GLB / PBR · 法线外移8mm · PICO运行观感待验", (0, -.65, .21), .044)
scene.render.filepath = str(HERE / "torso_contact_before_after.png")
bpy.ops.render.render(write_still=True)
print(json.dumps({
    "actor": str(ACTOR.relative_to(ROOT)), "actorSha256": hashlib.sha256(ACTOR.read_bytes()).hexdigest(),
    "clip": "slash", "sourceSeconds": SOURCE_SECONDS, "effectSeconds": EFFECT_SECONDS,
    "strength": STRENGTH, "sizeFactor": SIZE,
    "contactsBlenderSpace": [{"surface": name, "point": list(p), "normal": list(n), "material": mat}
                             for name, (p, n, mat) in zip(("cloth", "steel"), contacts[1])],
}, indent=2))
