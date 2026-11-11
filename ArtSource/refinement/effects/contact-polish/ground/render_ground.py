"""Read-only Paving + actual ground candidates. Offline example movement, not a trigger test."""
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
REVIEW = HERE / 'review'
REVIEW.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent))
from contact_motion import sample_ground_particle
from offline_opacity import independent_alpha_controls, ownership_report

PAVING = ROOT / 'app/src/main/assets/models/forecourt.glb'
LEGACY = ROOT / 'app/src/main/assets/models/effects/ground_dust.glb'
source_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (PAVING, LEGACY)}
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 3
scene.cycles.use_denoising = True
scene.render.resolution_x = 640
scene.render.resolution_y = 420
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('Ground candidate neutral study')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.065, .075, .09, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45
bpy.ops.import_scene.gltf(filepath=str(PAVING))
imported = list(bpy.context.selected_objects)
paving = next(obj for obj in imported if obj.type == 'MESH' and obj.name.split('.')[0] == 'Paving')
for obj in imported:
    if obj.type == 'MESH' and obj != paving:
        obj.hide_render = True
bpy.context.view_layer.update()
flat_faces = []
for polygon in paving.data.polygons:
    normal = (paving.matrix_world.to_3x3() @ polygon.normal).normalized()
    point = paving.matrix_world @ polygon.center
    if normal.z > .99999:
        flat_faces.append((point, polygon.index))
assert flat_faces
contact, source_face = max(flat_faces, key=lambda item: item[0].z)
contact = contact.copy()
display = bpy.data.objects.new('Read-only Paving display translation', None)
scene.collection.objects.link(display)
for obj in imported:
    if obj.parent is None:
        obj.parent = display
display.location = -contact
bpy.context.view_layer.update()
max_floor = max((paving.matrix_world @ vertex.co).z for vertex in paving.data.vertices)
assert max_floor <= .002 + 1e-5
rotation = Matrix.Rotation(-math.pi / 2, 4, 'X')


def stage(vector):
    return Vector((vector[0], -vector[2], vector[1]))


def alpha_controls(obj):
    return independent_alpha_controls(obj)


cases = []
for kind in ('legacy', 'dodge', 'landing'):
    motion = None if kind == 'legacy' else json.loads((HERE / f'{kind}_motion.json').read_text())
    asset = LEGACY if kind == 'legacy' else HERE / motion['asset']
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(asset))
    objects = list(bpy.context.selected_objects)
    meshes = {}
    for obj in objects:
        if obj.type != 'MESH':
            continue
        obj.parent = None
        meshes[obj.name.split('.')[0]] = (obj, alpha_controls(obj))
    cases.append((kind, motion, meshes, asset))

caption_mat = bpy.data.materials.new('Offline measured labels')
caption_mat.use_nodes = True
shader = caption_mat.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.8, .83, .85, 1)
shader.inputs['Emission Color'].default_value = (.8, .83, .85, 1)
shader.inputs['Emission Strength'].default_value = .5
font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')


def label(text, location, size):
    data = bpy.data.curves.new(text, 'FONT')
    data.body, data.font, data.align_x, data.size = text, font, 'CENTER', size
    obj = bpy.data.objects.new(text, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = camera.rotation_euler
    data.materials.append(caption_mat)
    return data


camera_data = bpy.data.cameras.new('Same Paving camera')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = .78
camera = bpy.data.objects.new('Same Paving camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (.32, -.64, .24)
camera.rotation_euler = (Vector((0, 0, .018)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
for name, position, energy, color in (('Wide cool key', (-2, -3, 4), 450, (.82, .9, 1)),
                                      ('Low warm fill', (2, -.5, 1), 220, (1, .79, .61))):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = energy, 3, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, 0)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
# A physical 300mm measuring bar on the original surface, outside the effect centre.
mesh = bpy.data.meshes.new('300mm measuring bar')
mesh.from_pydata([(-.15, -.20, .003), (.15, -.20, .003), (.15, -.198, .003), (-.15, -.198, .003)], [], [(0, 1, 2, 3)])
obj = bpy.data.objects.new('30cm ruler', mesh)
scene.collection.objects.link(obj)
mesh.materials.append(caption_mat)
label('30 cm', (0, -.235, .006), .018)
minimum_base = 1.0


def update(kind, age):
    global minimum_base
    for case, motion, meshes, asset in cases:
        for obj, controls in meshes.values():
            obj.hide_render = case != kind
        if case != kind:
            continue
        if kind == 'legacy':
            progress = min(1, age / .65)
            for name, (obj, controls) in meshes.items():
                if name == 'core':
                    scale, alpha = .7 + age * 3, max(0, 1 - age / .12)
                    local_offset = Vector((0, 0, 0))
                elif name == 'debris':
                    scale, alpha = .22 + progress * 1.1, (1 - progress) ** 2
                    local_offset = Vector((0, -.32 * age * age, .14 * age))
                else:
                    scale, alpha = 1, min(1, max(0, (.65 - age) / .24))
                    local_offset = Vector((0, 0, .004))
                obj.matrix_world = Matrix.Translation(Vector((local_offset.x, local_offset.y, .002 + local_offset.z))) @ rotation
                obj.scale = (scale, 1, scale)
                obj.hide_render = age >= .65
                for control in controls:
                    control.default_value = alpha
        else:
            for particle in motion['particles']:
                obj, controls = meshes[particle['node']]
                sample = sample_ground_particle(particle, age, (0, .002, 0), (0, 1, 0), (1, 0, 0))
                obj.hide_render = sample is None
                if sample is None:
                    continue
                position = stage(sample['position_stage_m'])
                minimum_base = min(minimum_base, position.z)
                assert position.z >= .002 - 1e-8
                obj.matrix_world = Matrix.Translation(position) @ rotation
                for control in controls:
                    control.default_value = sample['opacity']


opacity_ownership = ownership_report([obj for _, _, meshes, _ in cases for obj, _ in meshes.values()])
(REVIEW / 'opacity_ownership.json').write_text(json.dumps(opacity_ownership, indent=2) + '\n')

with tempfile.TemporaryDirectory(prefix='ground-polish-review-') as temporary:
    frames = Path(temporary)
    for frame in range(21):
        age = frame / 30
        for kind in ('legacy', 'dodge', 'landing'):
            update(kind, age)
            scene.render.filepath = str(frames / f'{kind}_{frame:03d}.png')
            bpy.ops.render.render(write_still=True)
        if frame in (3, 9):
            for kind in ('legacy', 'dodge', 'landing'):
                shutil.copy2(frames / f'{kind}_{frame:03d}.png', REVIEW / f'{kind}_{frame:02d}.png')
    subprocess.run([shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-y',
                    '-framerate', '30', '-i', str(frames / 'legacy_%03d.png'),
                    '-framerate', '30', '-i', str(frames / 'dodge_%03d.png'),
                    '-framerate', '30', '-i', str(frames / 'landing_%03d.png'),
                    '-filter_complex', '[0:v][1:v][2:v]hstack=inputs=3[v]', '-map', '[v]',
                    '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                    str(REVIEW / 'ground_preview_raw.mp4')], check=True)
for path, expected in source_hashes.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
manifest = {'label': '离线地面素材预演，非SDK或实际闪避/骨骼落地判定',
            'source_hashes': source_hashes, 'paving_node': 'Paving', 'source_polygon_index': source_face,
            'contact_source_blender_m': list(contact), 'display_translation_m': list(-contact),
            'ground_normal_stage': [0, 1, 0], 'example_player_ground_tangent_stage': [1, 0, 0],
            'binormal_stage': [0, 0, -1], 'anchor_normal_offset_m': .002,
            'gravity_stage_mps2': [0, -9.81, 0], 'orientation': 'Fixed TBN; no velocity tilt',
            'sampler': 'Root contact_motion.sample_ground_particle, base clamped above anchor plane',
            'minimum_sampled_base_height_m': minimum_base, 'maximum_displayed_paving_height_m': max_floor,
            'camera_blender_m': list(camera.location), 'ortho_width_m': camera_data.ortho_scale,
            'fps': 30, 'frames': 21, 'seconds': .7, 'ruler_m': .30,
            'limitations': ['旧栏仅资源理论包络', 'T为示例玩家地面位移，非真实触发', '真实成功闪避/骨骼落地由Root后接']}
(REVIEW / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print('GROUND_REVIEW_RENDER_COMPLETE')

subprocess.run(['python3', str(REVIEW / 'assemble_ground.py')], check=True)
