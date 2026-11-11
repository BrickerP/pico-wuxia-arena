"""Normal-distance source comparison, fixed 60-degree perspective, independent alpha."""
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
ROOT = HERE.parents[4]
REVIEW = HERE / 'review'
REVIEW.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parent))
from offline_opacity import independent_alpha_controls, ownership_report
from contact_motion import contact_basis, sample_particle, interpolate

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 3
scene.cycles.use_denoising = True
scene.render.resolution_x = 640
scene.render.resolution_y = 480
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.fps = 30
scene.world = bpy.data.worlds.new('Fixed source-viewing studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.045, .055, .07, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45
ACTOR = ROOT / 'app/src/main/assets/models/opponents/base.glb'
actor_sha = hashlib.sha256(ACTOR.read_bytes()).hexdigest()
bpy.ops.import_scene.gltf(filepath=str(ACTOR))
reference = list(bpy.context.selected_objects)
raw = ACTOR.read_bytes()
import struct
actor_doc = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
idle = next(a for a in actor_doc['animations'] if a['name'] == 'idle')
source_start = min(actor_doc['accessors'][s['input']]['min'][0] for s in idle['samplers'])
for obj in reference:
    if obj.type != 'ARMATURE':
        continue
    obj.animation_data.action = None
    for track in obj.animation_data.nla_tracks:
        track.mute = track.name != 'idle'
        if not track.mute:
            strip = track.strips[0]
            target = float(strip.action.frame_range[0]) + (1.0 - source_start) * scene.render.fps
            strip.frame_start = 63 - (target - strip.action_frame_start) * strip.scale
            strip.influence = 1
scene.frame_set(63)
bpy.context.view_layer.update()
anchor = (0, 1.20, .358)
normal = (0, 0, 1)
tangent = (1, 0, 0)


def stage(value):
    return Vector((value[0], -value[2], value[1]))


cases = []
input_hashes = {}
for kind, folder in (('old_metal', HERE.parent / 'metal'), ('hero_metal', HERE / 'metal'),
                      ('old_wet', HERE.parent / 'wet'), ('hero_wet', HERE / 'wet')):
    motion_path = folder / 'motion.json'
    motion_bytes = motion_path.read_bytes()
    motion = json.loads(motion_bytes)
    asset = folder / motion['asset']
    input_hashes[str(motion_path.relative_to(ROOT))] = hashlib.sha256(motion_bytes).hexdigest()
    input_hashes[str(asset.relative_to(ROOT))] = hashlib.sha256(asset.read_bytes()).hexdigest()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(asset))
    imported = list(bpy.context.selected_objects)
    meshes = {}
    for obj in imported:
        if obj.type == 'MESH':
            obj.parent = None
            name = obj.name.split('.')[0]
            assert name not in meshes, f'Duplicate mesh node in {kind}: {name}'
            meshes[name] = (obj, independent_alpha_controls(obj))
    driven = [row['node'] for section in ('particles', 'cores', 'accents') for row in motion.get(section, [])]
    assert len(driven) == len(set(driven)) and set(driven) == set(meshes), f'Undriven or duplicate nodes in {kind}'
    cases.append((kind, motion, meshes, asset, motion_path))
ownership = ownership_report([obj for _, _, meshes, _, _ in cases for obj, _ in meshes.values()])
(REVIEW / 'opacity_ownership.json').write_text(json.dumps(ownership, indent=2) + '\n')
for name, position, power, color in (('Same wide key', (-3, -4, 4), 650, (1, .84, .70)),
                                     ('Same wide fill', (3, -2, 2.5), 420, (.64, .78, 1))):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = power, 5, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
# Public Camera RNA descriptions were checked for HORIZONTAL fit, lens and sensor_width.
camera_data = bpy.data.cameras.new('Fixed FOV60 perspective')
camera_data.type = 'PERSP'
camera_data.sensor_fit = 'HORIZONTAL'
camera_data.sensor_width = 36
camera_data.lens = 36 / (2 * math.tan(math.radians(60) / 2))
camera = bpy.data.objects.new('Fixed FOV60 perspective', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
# Real half-metre scale, near the emission plane, with no source scaling.
ruler_material = bpy.data.materials.new('Scale label')
ruler_material.use_nodes = True
shader = ruler_material.node_tree.nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (.72, .76, .8, 1)
shader.inputs['Emission Color'].default_value = (.72, .76, .8, 1)
shader.inputs['Emission Strength'].default_value = .3
mesh = bpy.data.meshes.new('Half metre ruler')
mesh.from_pydata([(-.25, -.36, .63), (.25, -.36, .63), (.25, -.36, .633), (-.25, -.36, .633)], [], [(0, 1, 2, 3)])
obj = bpy.data.objects.new('0.5m scale bar', mesh)
scene.collection.objects.link(obj)
mesh.materials.append(ruler_material)


def fixed_layer(obj, initial):
    obj.matrix_world = Matrix.Translation(stage(tuple(anchor[i] + initial[i] for i in range(3))))


def update(kind, age, profile):
    for case, motion, meshes, _, _ in cases:
        for obj, _ in meshes.values():
            obj.hide_render = case != kind
        if case != kind:
            continue
        for particle in motion['particles']:
            obj, controls = meshes[particle['node']]
            sample = sample_particle(particle, age, anchor, normal, tangent)
            obj.hide_render = sample is None
            if sample is None:
                continue
            obj.matrix_world = Matrix.Translation(stage(sample['position_stage_m']))
            if particle['type'] == 'metal_spark':
                basis = contact_basis(normal, tangent)
                local_velocity = particle['initial_velocity_local_mps']
                velocity = Vector(tuple(sum(basis[i][axis] * local_velocity[i] for i in range(3))
                                        for axis in range(3))) + Vector((0, -9.81, 0)) * age
                direction = stage(velocity).normalized()
                width_axis = Vector((0, -1, 0)).cross(direction).normalized()
                depth_axis = width_axis.cross(direction).normalized()
                obj.rotation_mode = 'QUATERNION'
                obj.rotation_quaternion = Matrix((direction, depth_axis, width_axis)).transposed().to_quaternion()
            else:
                # Both wet generations retain their source TBN, as the runtime does.
                # Imported geometry already carries the glTF-to-Blender axis conversion.
                if 'orientation_axis_local' in particle:
                    axis = particle['orientation_axis_local']
                    assert len(axis) == 3 and all(math.isfinite(v) for v in axis)
                    assert abs(math.hypot(*axis) - 1) < 1e-6
            for control in controls:
                control.default_value = sample['opacity']
        for core in motion.get('cores', []):
            obj, controls = meshes[core['node']]
            envelope = core[profile]
            obj.hide_render = age < 0 or age >= envelope['lifetime_s']
            fixed_layer(obj, core['initial_position_local_m'])
            for control in controls:
                control.default_value = max(0, interpolate(envelope['opacity_keys'], age))
        for accent in motion.get('accents', []):
            obj, controls = meshes[accent['node']]
            obj.hide_render = age < 0 or age >= accent['lifetime_s']
            fixed_layer(obj, accent['initial_position_local_m'])
            for control in controls:
                control.default_value = max(0, interpolate(accent['opacity_keys'], age))


def set_camera(distance):
    target = stage(anchor)
    camera.location = target + Vector((0, -distance, 0))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    assert abs((camera.location - target).length - distance) < 1e-6


def render(kind, age, profile, path):
    update(kind, age, profile)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


# First produce normal-distance physical stills before spending time on video.
for centimetres in (150, 250):
    set_camera(centimetres / 100)
    for profile, age in (('normal', .040), ('parry', .050)):
        for kind, _, _, _, _ in cases:
            render(kind, age, profile, REVIEW / f'{kind}_{profile}_{centimetres}cm.png')
subprocess.run(['python3', str(REVIEW / 'assemble_visibility.py')], check=True)
print('NORMAL_DISTANCE_STILLS_READY', flush=True)
with tempfile.TemporaryDirectory(prefix='hero-v3-normal-distance-') as temporary:
    frames = Path(temporary)
    for centimetres in (150, 250):
        set_camera(centimetres / 100)
        for frame in range(21):
            seconds = frame / 24
            age = seconds if seconds < .4 else seconds - .4
            profile = 'normal' if seconds < .4 else 'parry'
            for kind, _, _, _, _ in cases:
                render(kind, age, profile, frames / f'{centimetres}_{kind}_{frame:03d}.png')
        args = [shutil.which('ffmpeg'), '-hide_banner', '-loglevel', 'error', '-y']
        for kind, _, _, _, _ in cases:
            args += ['-framerate', '24', '-i', str(frames / f'{centimetres}_{kind}_%03d.png')]
        args += ['-filter_complex', '[0:v][1:v][2:v][3:v]hstack=inputs=4[v]', '-map', '[v]',
                 '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                 str(REVIEW / f'distance_{centimetres}cm_raw.mp4')]
        subprocess.run(args, check=True)
assert hashlib.sha256(ACTOR.read_bytes()).hexdigest() == actor_sha
for relative, expected_sha in input_hashes.items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected_sha, f'Render input changed: {relative}'
manifest = {'label': '正常战斗视距离线源资产预演，示例TBN发射；参考角色仅用于比例，非实际碰撞或SDK验收',
            'actor': str(ACTOR.relative_to(ROOT)), 'actor_sha256': actor_sha, 'actor_pose': 'idle source1.0s static sample',
            'horizontal_fov_degrees': 60, 'sensor_fit': 'HORIZONTAL', 'sensor_width_mm': 36,
            'focal_length_mm': camera_data.lens, 'contact_distances_m': [1.5, 2.5],
            'per_panel_resolution': [640, 480], 'reference_ruler_m': .5,
            'anchor_stage_m': anchor, 'normal_stage': normal, 'tangent_stage': tangent, 'gravity_stage_mps2': [0, -9.81, 0],
            'still_samples': {'normal': .040, 'parry': .050}, 'movie_fps': 24, 'movie_frames': 21,
            'movie_seconds': 21 / 24, 'movie_example_onsets_s': [0, .4],
            'wet_orientation': 'Both old/new wet retain source TBN; v3 local long axes validated, no velocity realignment',
            'final_sample': 'time=20/24s; second-contact age=0.43333s, all source layers expired',
            'mesh_names': 'Duplicate mesh node names explicitly rejected before dictionary insertion',
            'movie_profiles': ['normal', 'parry; wet repeats same source envelope'],
            'accents': 'Static short contact arcs fully consumed; not real blade-tip ribbon',
            'fatal_profile': '150ms proposed to Root/08, not demonstrated in these normal/parry images',
            'inputs': input_hashes,
            'runtime_validation': 'not performed'}
(REVIEW / 'render_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
subprocess.run(['python3', str(REVIEW / 'assemble_visibility.py')], check=True)
print('HERO_V3_DISTANCE_REVIEW_COMPLETE')
