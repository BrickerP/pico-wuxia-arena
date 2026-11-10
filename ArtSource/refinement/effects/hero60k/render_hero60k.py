"""Frozen 60k actor and production contact resources, offline fixed-camera study."""
import hashlib, json, math, shutil, struct, subprocess, tempfile
from pathlib import Path
import bpy
from mathutils import Vector
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ACTOR = ROOT / 'app/src/main/assets/models/opponents/base.glb'
EXPECTED_SHA = '53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641'
assert hashlib.sha256(ACTOR.read_bytes()).hexdigest() == EXPECTED_SHA
SOURCE_SECONDS = 2.1
EFFECT_SECONDS = 0.055
STRENGTH = 0.7
SIZE = 0.72 + STRENGTH * 0.46
FPS = 24
DURATION = 2.75
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 3
scene.cycles.use_denoising = True
scene.render.resolution_x = 960
scene.render.resolution_y = 640
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.fps = 30
scene.world = bpy.data.worlds.new('Neutral offline world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.045, 0.055, 0.07, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45

def caption_material():
    mat = bpy.data.materials.new('Offline annotations')
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (0.78, 0.82, 0.85, 1)
    shader.inputs['Emission Color'].default_value = (0.78, 0.82, 0.85, 1)
    shader.inputs['Emission Strength'].default_value = 0.6
    return mat
captions = caption_material()
font = bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')

def label(text, position, size=0.045):
    data = bpy.data.curves.new(text, 'FONT')
    data.body = text
    data.font = font
    data.align_x = 'CENTER'
    data.size = size
    obj = bpy.data.objects.new(text, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (math.pi / 2, 0, 0)
    data.materials.append(captions)

def actor(x):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(ACTOR))
    objects = list(bpy.context.selected_objects)
    for obj in objects:
        if obj.type != 'ARMATURE':
            continue
        data = obj.animation_data
        if data is None:
            raise RuntimeError('Runtime actor has no imported animation')
        data.action = None
        found = False
        for track in data.nla_tracks:
            track.mute = track.name != 'slash'
            if not track.mute:
                found = True
                track.strips[0].frame_start = 64 - SOURCE_SECONDS * scene.render.fps
                track.strips[0].influence = 1
        if not found:
            raise RuntimeError('Runtime slash is absent')
    placement = bpy.data.objects.new('Actor placement', None)
    scene.collection.objects.link(placement)
    placement.location.x = x
    for obj in objects:
        if obj.parent is None:
            obj.parent = placement
    return objects

def attach_effect(name, point, normal):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(ROOT / 'app/src/main/assets/models/effects' / (name + '.glb')))
    objects = list(bpy.context.selected_objects)
    placement = bpy.data.objects.new('Actual ' + name, None)
    scene.collection.objects.link(placement)
    placement.location = point + normal * 0.008
    placement.rotation_mode = 'QUATERNION'
    placement.rotation_quaternion = Vector((0, -1, 0)).rotation_difference(normal)
    placement.scale = (SIZE, SIZE, SIZE)
    duration = 0.62 if name == 'soft_contact' else 0.54
    progress = EFFECT_SECONDS / duration
    for obj in objects:
        if obj.parent is None:
            obj.parent = placement
        if obj.type != 'MESH':
            continue
        key = obj.name.split('.')[0]
        if key == 'core':
            scale = (0.7 + EFFECT_SECONDS * 3) * (1.3 if name == 'metal_contact' else 1)
            obj.scale = (scale, 1, scale)
            alpha = 1 - EFFECT_SECONDS / (0.22 if name == 'metal_contact' else 0.18)
        elif key == 'debris':
            scale = 0.22 + progress * 1.1
            obj.scale = (scale, 1, scale)
            obj.location.z = -0.32 * EFFECT_SECONDS ** 2
            obj.location.y = -0.14 * EFFECT_SECONDS
            alpha = (1 - progress) ** 2
        else:
            obj.scale = (1, 1, min(1, max(0.08, (duration - EFFECT_SECONDS) / 0.3)))
            obj.location.y = -0.004
            alpha = min(1, max(0, (duration - EFFECT_SECONDS) / 0.24))
        for mat in obj.data.materials:
            shader = next((node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'))
            destination = shader.inputs['Alpha']
            multiplier = mat.node_tree.nodes.new('ShaderNodeMath')
            multiplier.operation = 'MULTIPLY'
            multiplier.label = 'RuntimeOpacity'
            link = destination.links[0]
            original = link.from_socket
            mat.node_tree.links.remove(link)
            mat.node_tree.links.new(original, multiplier.inputs[0])
            multiplier.inputs[1].default_value = alpha
            mat.node_tree.links.new(multiplier.outputs[0], destination)
    return (placement, objects)
raw = ACTOR.read_bytes()
document = json.loads(raw[20:20 + struct.unpack_from('<I', raw, 12)[0]])
clip_starts = {a['name']: min((document['accessors'][s['input']]['min'][0] for s in a['samplers'])) for a in document['animations']}
objects = actor(0)
armatures = [obj for obj in objects if obj.type == 'ARMATURE']
scene.frame_set(63)
bpy.context.view_layer.update()
mappings = {}

def pose(clip, seconds):
    for arm in armatures:
        arm.animation_data.action = None
        for track in arm.animation_data.nla_tracks:
            track.mute = track.name != clip
            if not track.mute:
                strip = track.strips[0]
                start = float(strip.action.frame_range[0])
                target = start + (seconds - clip_starts[clip]) * scene.render.fps
                strip.frame_start = 63 - (target - strip.action_frame_start) * strip.scale
                strip.influence = 1
                mappings[clip] = {'source_start_seconds': clip_starts[clip], 'action_frame_start': start, 'strip_action_frame_start': float(strip.action_frame_start), 'strip_scale': float(strip.scale)}
    scene.frame_set(63)
    bpy.context.view_layer.update()
pose('slash', 2.1)
depsgraph = bpy.context.evaluated_depsgraph_get()
arm = armatures[0]
head_center = arm.matrix_world @ arm.pose.bones['Head'].matrix.translation
head_faces = []
blade_faces = []
for obj in objects:
    if obj.type != 'MESH':
        continue
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        for poly in mesh.polygons:
            point = evaluated.matrix_world @ poly.center
            normal = (evaluated.matrix_world.to_3x3() @ poly.normal).normalized()
            if normal.y > -0.15:
                continue
            material_name = mesh.materials[poly.material_index].name
            if material_name.startswith(('Steel | forged body', 'Steel | sharpened edge')):
                blade_faces.append((point.copy(), normal.copy(), material_name))
            if poly.material_index == 0 and abs(point.x - head_center.x) < 0.14 and head_center.z - 0.04 < point.z < head_center.z + 0.22:
                head_faces.append((point.copy(), normal.copy()))
    finally:
        evaluated.to_mesh_clear()
assert head_faces and blade_faces
head_target = head_center + Vector((0, -0.08, 0.08))
head_contact = min(head_faces, key=lambda pair: (pair[0] - head_target).length_squared)
blade_center = sum((face[0] for face in blade_faces), Vector()) / len(blade_faces)
blade_face = min(blade_faces, key=lambda face: (face[0] - blade_center).length_squared)
blade_contact = (blade_face[0], blade_face[1])
blade_material = blade_face[2]
fx = []
for (name, contact) in (('soft_contact', head_contact), ('metal_contact', blade_contact)):
    (placement, meshes) = attach_effect(name, *contact)
    controls = []
    for obj in meshes:
        if obj.type != 'MESH':
            continue
        alpha = [n.inputs[1] for mat in obj.data.materials for n in mat.node_tree.nodes if n.label == 'RuntimeOpacity']
        controls.append((obj, obj.name.split('.')[0], alpha))
    fx.append((placement, meshes, controls))
points = []
for (clip, seconds) in (('slash', 1.35), ('slash', 1.85), ('slash', 2.1), ('hit_head', 0.65), ('hit_body', 0.65)):
    pose(clip, seconds)
    for a in armatures:
        for name in ('Head', 'L_Hand', 'R_Hand'):
            points.append(a.matrix_world @ a.pose.bones[name].matrix.translation)
    for obj in objects:
        if obj.type != 'MESH':
            continue
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        try:
            ids = {i for p in mesh.polygons if p.material_index in (1, 2, 3) for i in p.vertices}
            points.extend((evaluated.matrix_world @ mesh.vertices[i].co for i in ids))
        finally:
            evaluated.to_mesh_clear()
min_x = min((p.x for p in points)) - 0.23
max_x = max((p.x for p in points)) + 0.23
min_z = min((p.z for p in points)) - 0.22
max_z = max((p.z for p in points)) + 0.38
height = max_z - min_z
width = max(max_x - min_x, height * 1.5)
center = Vector(((min_x + max_x) / 2, 0, (min_z + max_z) / 2))
camera_data = bpy.data.cameras.new('Fixed asset camera')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = width
camera = bpy.data.objects.new('Fixed asset camera', camera_data)
scene.collection.objects.link(camera)
camera.location = center + Vector((0, -5, 0))
camera.rotation_euler = (center - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
for (name, position, power, color) in (('Wide key', (-3, -4, 4), 650, (1, 0.84, 0.7)), ('Wide fill', (3, -2, 2.5), 420, (0.64, 0.78, 1))):
    light_data = bpy.data.lights.new(name, 'AREA')
    light_data.energy = power
    light_data.size = 5
    light_data.color = color
    light = bpy.data.objects.new(name, light_data)
    scene.collection.objects.link(light)
    light.location = position
    light.rotation_euler = (Vector((0, 0, 1)) - light.location).to_track_quat('-Z', 'Y').to_euler()
label('离线资产动效预演 · 冻结60k现役刀客', (center.x, -1, max_z - 0.09), width * 0.025)
label('固定镜头 · 正式PBR / FX / WAV · 制作切段，非运行自动过渡', (center.x, -1, min_z + 0.045), width * 0.017)
label('裸头SOFT 80ms / 刀刃PARRY 90ms · recoil 220ms', (center.x, -1, min_z + 0.12), width * 0.016)

def sequence(t):
    if t < 0.75:
        return ('slash', 1.35 + t)
    if t < 0.83:
        return ('slash', 2.1)
    if t < 1.5:
        return ('hit_head', 0.05 + (t - 0.83) * (0.67 / 0.67))
    if t < 1.75:
        return ('slash', 1.85 + t - 1.5)
    if t < 1.84:
        return ('slash', 2.1)
    return ('hit_side', min(1.18, 0.05 + (t - 1.84) * (1.13 / 0.91)))

def update(t):
    (clip, seconds) = sequence(t)
    pose(clip, seconds)
    offset = Vector()
    for (onset, contact, stop, direction) in ((0.75, head_contact, 0.08, -1), (1.75, blade_contact, 0.09, 1)):
        p = max(0, min(1, (t - onset - stop) / 0.22))
        away = Vector((contact[1].x * direction, contact[1].y * direction, 0))
        if away.length > 1e-08:
            away.normalize()
        offset += away * ((0.025 + 0.055 * STRENGTH) * 4 * p * (1 - p))
    roots = [obj for obj in objects if obj.parent and obj.parent.name.startswith('Actor placement')]
    for obj in roots:
        obj.parent.location = offset
    for (index, (placement, meshes, controls)) in enumerate(fx):
        onset = (0.75, 1.75)[index]
        duration = (0.62, 0.54)[index]
        age = t - onset
        for obj in meshes:
            obj.hide_render = not 0 <= age < duration
        if not 0 <= age < duration:
            continue
        p = age / duration
        for (obj, key, alphas) in controls:
            if key == 'core':
                scale = (0.7 + age * 3) * (1.3 if index == 1 else 1)
                obj.scale = (scale, 1, scale)
                alpha = max(0, 1 - age / (0.22 if index == 1 else 0.18))
            elif key == 'debris':
                scale = 0.22 + p * 1.1
                obj.scale = (scale, 1, scale)
                obj.location.z = -0.32 * age * age
                obj.location.y = -0.14 * age
                alpha = (1 - p) ** 2
            else:
                obj.scale = (1, 1, min(1, max(0.08, (duration - age) / 0.3)))
                obj.location.y = -0.004
                alpha = min(1, max(0, (duration - age) / 0.24))
            for a in alphas:
                a.default_value = alpha
    return (clip, seconds)
rows = []
with tempfile.TemporaryDirectory(prefix='hero60k-frames-') as temporary:
    frames = Path(temporary)
    for frame in range(66):
        t = frame / FPS
        (clip, seconds) = update(t)
        rows.append({'frame': frame, 'output_seconds': t, 'clip': clip, 'source_seconds': seconds})
        scene.render.filepath = str(frames / f'{frame:03d}.png')
        bpy.ops.render.render(write_still=True)
        if frame == 43:
            shutil.copy2(frames / f'{frame:03d}.png', HERE / 'hero60k_contact.png')
    ffmpeg = shutil.which('ffmpeg')
    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '24', '-i', str(frames / '%03d.png'), '-i', str(ROOT / 'app/src/main/res/raw/arena_hit.wav'), '-i', str(ROOT / 'app/src/main/res/raw/arena_parry.wav'), '-filter_complex', '[1:a]adelay=750:all=1[a];[2:a]adelay=1750:all=1[b];[a][b]amix=inputs=2:normalize=0,apad=whole_dur=2.75[m]', '-map', '0:v', '-map', '[m]', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-t', '2.75', '-movflags', '+faststart', str(HERE / 'hero60k_preview.mp4')], check=True)
assert hashlib.sha256(ACTOR.read_bytes()).hexdigest() == EXPECTED_SHA
contacts = []
for name, onset, contact, material, asset, wav, stop, direction in (
    ('bare_head_SOFT', 0.75, head_contact, document['materials'][0]['name'], 'soft_contact.glb', 'arena_hit.wav', 0.08, -1),
    ('blade_PARRY', 1.75, blade_contact, blade_material, 'metal_contact.glb', 'arena_parry.wav', 0.09, 1),
):
    point, normal = contact
    recoil_direction = Vector((normal.x * direction, normal.y * direction, 0))
    if recoil_direction.length > 1e-8:
        recoil_direction.normalize()
    contacts.append({
        'kind': name, 'material': material, 'onset_output_seconds': onset,
        'onset_frame': round(onset * FPS), 'hitstop_seconds': stop,
        'point_actor_gltf_metres': [point.x, point.z, -point.y],
        'normal_actor_gltf': [normal.x, normal.z, -normal.y],
        'fx_asset': asset, 'wav': wav, 'strength': STRENGTH, 'scale': SIZE,
        'normal_offset_metres': 0.008,
        'recoil': {'delay_seconds': stop, 'duration_seconds': 0.22,
            'amplitude_metres': 0.025 + 0.055 * STRENGTH, 'envelope': '4*p*(1-p)',
            'direction_actor_gltf': [recoil_direction.x, 0, -recoil_direction.y]},
        'fx_duration_seconds': 0.62 if name == 'bare_head_SOFT' else 0.54,
        'core_duration_seconds': 0.18 if name == 'bare_head_SOFT' else 0.22,
        'core_size_multiplier': 1 if name == 'bare_head_SOFT' else 1.3,
        'fx_sha256': hashlib.sha256((ROOT / 'app/src/main/assets/models/effects' / asset).read_bytes()).hexdigest(),
        'wav_sha256': hashlib.sha256((ROOT / 'app/src/main/res/raw' / wav).read_bytes()).hexdigest(),
    })
(HERE / 'timeline.json').write_text(json.dumps({
    'label': '离线资产动效预演', 'contact_label': '裸头SOFT / 刀刃PARRY',
    'actor_sha256_before_after': EXPECTED_SHA,
    'seconds': DURATION, 'fps': FPS, 'frame_count': 66, 'image_output_seconds': 43 / FPS,
    'image_frame': 43, 'sampled_pause_frames': {'head': [18, 19], 'parry': [42, 43, 44]},
    'source_mapping_formula': 'targetActionFrame=action.frame_range[0]+(sourceSeconds-glTF_source_min)*sceneFPS; strip.frame_start=63-(targetActionFrame-strip.action_frame_start)*strip.scale',
    'imported_action_mappings': {key: value for key, value in mappings.items() if key in {'slash', 'hit_head', 'hit_side'}},
    'camera_bounds_sampling': [['slash', 1.35], ['slash', 1.85], ['slash', 2.1], ['hit_head', .65], ['hit_body', .65]],
    'camera': {'position_blender': list(camera.location), 'ortho_scale': camera_data.ortho_scale, 'unchanged_from_first_version': True},
    'contacts': contacts,
    'fx_clock': 'wall/output seconds since onset; continues during pose hitstop',
    'pose_holds': [[0.75, 0.83], [1.75, 1.84]],
    'limitations': ['制作切段，无NLA跨片混合', '离线GLB材质与时序展示，非PICO运行验收', '24fps对80/90ms停顿以相邻采样帧表现'],
    'frames': rows,
}, ensure_ascii=False, indent=2) + '\n')
print('HERO60K PARRY COMPLETE', EXPECTED_SHA)
