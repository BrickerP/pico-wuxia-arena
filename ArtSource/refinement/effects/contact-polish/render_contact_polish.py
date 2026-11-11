"""Offline candidate GLB/motion rendering. Example tangent basis, not runtime input."""
import hashlib
import json
import math
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
REVIEW = HERE / 'review'
REVIEW.mkdir(exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
from offline_opacity import independent_alpha_controls, ownership_report
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 4
scene.cycles.use_denoising = True
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('Neutral contact study')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.035, .045, .055, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35


def stage(value):
    return Vector((value[0], -value[2], value[1]))


def opacity_controls(obj):
    return independent_alpha_controls(obj)


actors = []
for index, (kind, filename) in enumerate((('normal', 'metal'), ('parry', 'metal'), ('wet', 'wet'))):
    motion_path = HERE / filename / 'motion.json'
    motion = json.loads(motion_path.read_text())
    asset = motion_path.parent / motion['asset']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(asset))
    imported = list(bpy.context.selected_objects)
    placement = bpy.data.objects.new(f'Column {kind}', None)
    scene.collection.objects.link(placement)
    placement.location = ((index - 1) * .55 - .10, 0, .10)
    for obj in imported:
        if obj.parent is None:
            obj.parent = placement
    meshes = {obj.name.split('.')[0]: (obj, opacity_controls(obj)) for obj in imported if obj.type == 'MESH'}
    actors.append((kind, motion, meshes))

caption_material = bpy.data.materials.new('Offline caption')
caption_material.use_nodes = True
shader = caption_material.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.75, .8, .84, 1)
shader.inputs['Emission Color'].default_value = (.75, .8, .84, 1)
shader.inputs['Emission Strength'].default_value = .5
font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')


def label(text, x, z, size):
    data = bpy.data.curves.new(text, 'FONT')
    data.body = text
    data.font = font
    data.align_x = 'CENTER'
    data.size = size
    obj = bpy.data.objects.new(text, data)
    scene.collection.objects.link(obj)
    obj.location = (x, -.05, z)
    obj.rotation_euler = (math.pi / 2, 0, 0)
    data.materials.append(caption_material)
    return data


label('独立接触粒子 · 离线素材预演', 0, .245, .036)
label('示例 T=Stage +X / B=+Y / N=+Z；重力为 Stage −Y，未接真实刀尖轨迹', 0, -.49, .018)
clock_label = label('0 ms', .72, .19, .024)
for index, text in enumerate(('金属普通 · 核心65ms', '刀刃弹反 · 核心90ms', '湿布 · 8滴 + 2纤维')):
    center = (index - 1) * .55
    label(text, center, .185, .022)
    # Exact 100mm ruler in the same physical coordinate system.
    mesh = bpy.data.meshes.new('100mm ruler')
    mesh.from_pydata([(center - .05, -.04, -.42), (center + .05, -.04, -.42),
                      (center + .05, -.04, -.418), (center - .05, -.04, -.418)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new('10cm scale bar', mesh)
    scene.collection.objects.link(obj)
    mesh.materials.append(caption_material)
    label('10 cm', center, -.455, .020)
for name, position, energy, color in (('Wide key', (-2, -3, 3), 380, (1, .86, .72)),
                                      ('Wide fill', (3, -2, 1), 300, (.7, .82, 1))):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = energy, 3, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, -.10)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
camera_data = bpy.data.cameras.new('Fixed contact camera')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 1.78
camera = bpy.data.objects.new('Fixed contact camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (0, -3, -.11)
camera.rotation_euler = (Vector((0, 0, -.11)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera


def alpha_at(keys, age):
    for first, second in zip(keys, keys[1:]):
        if age <= second[0]:
            progress = max(0, (age - first[0]) / (second[0] - first[0]))
            return first[1] + (second[1] - first[1]) * progress
    return keys[-1][1]


def update(age):
    clock_label.body = f'{age * 1000:.0f} ms'
    for kind, motion, meshes in actors:
        for particle in motion['particles']:
            obj, controls = meshes[particle['node']]
            obj.hide_render = age >= particle['lifetime_s']
            initial = Vector(particle['initial_position_local_m'])
            velocity = Vector(particle['initial_velocity_local_mps'])
            gravity = Vector(motion['gravity_stage_mps2'])
            position = initial + velocity * age + gravity * (.5 * age * age)
            obj.location = stage(position)
            instantaneous = stage(velocity + gravity * age)
            if particle['type'] == 'metal_spark':
                direction = instantaneous.normalized()
                width_axis = Vector((0, -1, 0)).cross(direction).normalized()
                depth_axis = width_axis.cross(direction).normalized()
                obj.rotation_mode = 'QUATERNION'
                obj.rotation_quaternion = Matrix((direction, depth_axis, width_axis)).transposed().to_quaternion()
            else:
                obj.rotation_mode = 'QUATERNION'
                obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(instantaneous)
            for control in controls:
                control.default_value = alpha_at(particle['opacity_keys'], age)
        for core in motion.get('cores', []):
            obj, controls = meshes[core['node']]
            profile = core[kind]
            obj.location = stage(core['initial_position_local_m'])
            obj.hide_render = age >= profile['lifetime_s']
            for control in controls:
                control.default_value = alpha_at(profile['opacity_keys'], age)


opacity_ownership = ownership_report([obj for _, _, meshes in actors for obj, _ in meshes.values()])
(REVIEW / 'opacity_ownership.json').write_text(json.dumps(opacity_ownership, indent=2) + '\n')

with tempfile.TemporaryDirectory(prefix='contact-polish-preview-') as temporary:
    frames = Path(temporary)
    for frame in range(15):
        age = frame / 30
        update(age)
        scene.render.filepath = str(frames / f'{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
        if frame in (0, 1, 2, 5, 8):
            shutil.copy2(frames / f'{frame:03d}.png', REVIEW / f'contact_{frame:02d}.png')
    subprocess.run([shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '30',
                    '-i', str(frames / '%03d.png'), '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(REVIEW / 'contact_polish_preview.mp4')], check=True)
subprocess.run(['python3', '-c', "from PIL import Image; from pathlib import Path; p=Path(r'" + str(REVIEW) + "'); fs=[Image.open(p/f'contact_{i:02d}.png').convert('RGB') for i in (0,1,2,5,8)]; out=Image.new('RGB',(fs[0].width,fs[0].height*len(fs))); [out.paste(im,(0,n*im.height)) for n,im in enumerate(fs)]; out.save(p/'contact_timeline.png')"], check=True)
manifest = {'scope': 'Offline candidate GLBs and motion; example tangent basis, not SDK/runtime evidence',
            'seconds': .5, 'fps': 30, 'frames': 15, 'sample_frames': [0, 1, 2, 5, 8],
            'basis_stage': {'tangent': [1, 0, 0], 'binormal': [0, 1, 0], 'normal': [0, 0, 1]},
            'gravity_stage_mps2': [0, -9.81, 0], 'ruler_m': .1,
            'assets': [{'kind': kind, 'asset': motion['asset']} for kind, motion, _ in actors]}
(REVIEW / 'render_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('CONTACT_POLISH_REVIEW_COMPLETE')
