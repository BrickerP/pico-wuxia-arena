"""Read-only Paving + actual ground candidates. Offline example movement, not a trigger test."""
import argparse
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
ROOT = HERE.parents[5]
REVIEW = HERE / 'review'
REVIEW.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parents[1]))
from contact_motion import sample_ground_particle
from offline_opacity import independent_alpha_controls, ownership_report

PAVING = ROOT / 'app/src/main/assets/models/forecourt.glb'
FROZEN_V1 = HERE.parent / 'review/invalid_shared_alpha/render_manifest.json'
frozen = json.loads(FROZEN_V1.read_text())
source_hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (PAVING,)}
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
for kind, directory, motion_file in (
    ('v1_dodge', HERE.parent, 'dodge_motion.json'),
    ('v2_dodge', HERE, 'dodge_motion.json'),
    ('v2_landing', HERE, 'landing_motion.json'),
):
    motion_path = directory / motion_file
    motion = json.loads(motion_path.read_text())
    asset = directory / motion['asset']
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

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--video', action='store_true', help='Render the 0.7s clip after the 100ms review')
arguments = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
assert list(contact) == frozen['contact_source_blender_m']
assert source_face == frozen['source_polygon_index']
assert list(camera.location) == frozen['camera_blender_m']
assert abs(camera_data.ortho_scale - frozen['ortho_width_m']) < 1e-8
for milliseconds in (100, 300):
    for kind in ('v1_dodge', 'v2_dodge', 'v2_landing'):
        update(kind, milliseconds / 1000)
        scene.render.filepath = str(REVIEW / f'{kind}_{milliseconds}ms.png')
        bpy.ops.render.render(write_still=True)

if arguments.video:
    with tempfile.TemporaryDirectory(prefix='ground-visibility-v2-') as temporary:
        frames = Path(temporary)
        for frame in range(21):
            age = frame / 30
            for kind in ('v1_dodge', 'v2_dodge', 'v2_landing'):
                update(kind, age)
                scene.render.filepath = str(frames / f'{kind}_{frame:03d}.png')
                bpy.ops.render.render(write_still=True)
        subprocess.run([shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-y',
                        '-framerate', '30', '-i', str(frames / 'v1_dodge_%03d.png'),
                        '-framerate', '30', '-i', str(frames / 'v2_dodge_%03d.png'),
                        '-framerate', '30', '-i', str(frames / 'v2_landing_%03d.png'),
                        '-filter_complex', '[0:v][1:v][2:v]hstack=inputs=3[v]', '-map', '[v]',
                        '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                        str(REVIEW / 'visibility_v2_raw.mp4')], check=True)
for path, expected in source_hashes.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
manifest = {
    'label': 'visibility-v2 下一轮离线候选；旧FAIL素材结论撤回重新审校',
    'source_hashes': source_hashes,
    'paving_source_polygon_index': source_face,
    'contact_source_blender_m': list(contact),
    'display_translation_m': list(-contact),
    'camera_blender_m': list(camera.location),
    'ortho_width_m': camera_data.ortho_scale,
    'same_v1_camera_contact_lighting_exposure_resolution': True,
    'opacity_renderer_fix': 'One copied material and one alpha multiplier per particle; old shared-material串乘 evidence invalid',
    'light_profile': 'v1 Wide cool key450 + Low warm fill220, world .45, no exposure/tone change',
    'ground_normal_stage': [0, 1, 0],
    'example_player_tangent_stage': [1, 0, 0],
    'anchor_normal_offset_m': .002,
    'sampler': 'sample_ground_particle; fixed TBN, Stage gravity, base clamp',
    'minimum_sampled_base_height_m': minimum_base,
    'first_review_age_s': .100,
    'video_seconds': .7 if arguments.video else None,
    'candidate_inputs': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for _, _, _, asset in cases for path in (asset, asset.with_name(asset.name.replace('_ground_polish.glb', '_motion.json')))
                         if path.exists()},
    'limitations': ['下一轮候选，不把v1标通过', '真实闪避/骨骼落地触发未接', '离线同灯可见性不替代PICO验收'],
}
(REVIEW / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
subprocess.run(['python3', str(REVIEW / 'assemble_visibility.py')], check=True)
print('VISIBILITY_V2_REVIEW_COMPLETE')
