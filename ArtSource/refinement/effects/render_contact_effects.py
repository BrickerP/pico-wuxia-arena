"""Render actual effect GLBs offline with the runtime's transform/opacity envelopes."""

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 8
scene.cycles.use_denoising = True
scene.render.resolution_x = 1440
scene.render.resolution_y = 680
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.fps = 30
scene.world = bpy.data.worlds.new("Offline contact material study")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (.035, .045, .06, 1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .4


def material(name, color):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = .9
    return result


def opacity_control(obj):
    controls = []
    for mat in obj.data.materials:
        shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
        alpha = shader.inputs["Alpha"]
        factor = mat.node_tree.nodes.new("ShaderNodeMath")
        factor.operation = "MULTIPLY"
        if alpha.is_linked:
            original = alpha.links[0]
            source = original.from_socket
            mat.node_tree.links.remove(original)
            mat.node_tree.links.new(source, factor.inputs[0])
        else:
            factor.inputs[0].default_value = alpha.default_value
        mat.node_tree.links.new(factor.outputs[0], alpha)
        factor.inputs[1].default_value = 1
        controls.append(factor.inputs[1])
    return controls


actors = []
names = ("blade_arc", "soft_contact", "metal_contact", "force_contact")
for index, name in enumerate(names):
    path = ROOT / "ArtSource/effects/blade_arc.glb" if index == 0 else HERE / (name + ".glb")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = list(bpy.context.selected_objects)
    placement = bpy.data.objects.new("Preview_" + name, None)
    scene.collection.objects.link(placement)
    placement.location = ((index - 1.5) * 1.05, 0, .75)
    for obj in imported:
        if obj.animation_data:
            obj.animation_data_clear()
            obj.scale = (1, 1, 1)
        if obj.parent is None:
            obj.parent = placement
    meshes = [obj for obj in imported if obj.type == "MESH"]
    layers = {obj.name.split(".")[0]: (obj, opacity_control(obj)) for obj in meshes}
    actors.append((name, placement, layers))

    # A common matte panel makes all four views comparable at metre scale.
    bpy.ops.mesh.primitive_plane_add(size=1, location=((index - 1.5) * 1.05, .11, .75),
                                     rotation=(math.pi / 2, 0, 0))
    panel = bpy.context.object
    panel.scale = (.88, .95, 1)
    panel.data.materials.append(material("Cloth study panel " + name, (.065, .08, .105)))

for name, position, energy, color in (("Key", (-2, -3, 4), 240, (1, .84, .65)),
                                      ("Fill", (3, -2, 2), 160, (.6, .72, 1))):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.size = 5
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, .75)) - obj.location).to_track_quat("-Z", "Y").to_euler()

camera_data = bpy.data.cameras.new("Contact comparison camera")
camera_data.type = "ORTHO"
camera_data.ortho_scale = 4.5
camera = bpy.data.objects.new("Contact comparison camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (0, -5, .75)
camera.rotation_euler = (Vector((0, 0, .75)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = camera

caption_material = material("Offline caption", (.72, .77, .81))
caption_shader = caption_material.node_tree.nodes.get("Principled BSDF")
caption_shader.inputs["Emission Color"].default_value = (.72, .77, .81, 1)
caption_shader.inputs["Emission Strength"].default_value = .7
font = bpy.data.fonts.load("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")


def label(text, x, z, size):
    data = bpy.data.curves.new(text, "FONT")
    data.body = text
    data.font = font
    data.align_x = "CENTER"
    data.size = size
    obj = bpy.data.objects.new(text, data)
    scene.collection.objects.link(obj)
    obj.location = (x, -.12, z)
    obj.rotation_euler = (math.pi / 2, 0, 0)
    data.materials.append(caption_material)


label("接触材质 · 静态网格与运行时包络", 0, 1.52, .10)
label("相同米制比例 · 每格宽 0.88 m · 阴影环境中的实际 GLB 网格", 0, 1.39, .051)
for index, text in enumerate(("旧普通命中 · 刃光理论峰值", "软体 / 衣物 · 尘屑 + 短刀痕",
                               "金属 · 白热核心 + 火星", "破势 / 处决 · 冲击环 + 刀痕")):
    label(text, (index - 1.5) * 1.05, .17, .050)
label("离线素材观感 · Entity 缩放 / Opacity 时序复现 · PICO 实际画面待主控验收", 0, -.04, .051)


def set_frame(seconds):
    for index, (name, placement, layers) in enumerate(actors):
        if index == 0:
            opacity = max(0, 1 - seconds / .18)
            for obj, controls in layers.values():
                obj.scale = (1, 1, 1)
                for control in controls:
                    control.default_value = opacity
            continue
        duration = {"soft_contact": .62, "metal_contact": .44, "force_contact": .72}[name]
        progress = min(1, seconds / duration)
        for key, (obj, controls) in layers.items():
            if key == "core":
                scale = .7 + seconds * 3
                obj.scale = (scale, 1, scale)
                alpha = max(0, 1 - seconds / .18)
            elif key == "debris":
                scale = .22 + progress * 1.1
                # Imported glTF +Y maps to Blender +Z; glTF +Z maps to -Y.
                obj.scale = (scale, 1, scale)
                obj.location.z = -.32 * seconds * seconds
                obj.location.y = -.14 * seconds
                alpha = (1 - progress) ** 2
            else:
                obj.scale = (1, 1, min(1, max(.08, (duration - seconds) / .30)))
                obj.location.y = -.004
                alpha = min(1, max(0, (duration - seconds) / .24))
            for control in controls:
                control.default_value = alpha if seconds < duration else 0


def render(seconds, path):
    set_frame(seconds)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    render(.055, HERE / "contact_materials_comparison.png")
    scene.render.resolution_x = 1152
    scene.render.resolution_y = 544
    with tempfile.TemporaryDirectory(prefix="pico-contact-preview-") as temporary:
        frames = Path(temporary)
        for frame in range(25):
            render(frame / 30, frames / f"{frame:03d}.png")
        subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
                        "-framerate", "30", "-i", str(frames / "%03d.png"), "-c:v", "libx264",
                        "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        str(HERE / "contact_materials_preview.mp4")], check=True)
    for frame, label_ms in ((8, 267), (14, 467)):
        subprocess.run([shutil.which("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y",
                        "-i", str(HERE / "contact_materials_preview.mp4"),
                        "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1",
                        str(HERE / f"contact_materials_{label_ms}ms.png")], check=True)
