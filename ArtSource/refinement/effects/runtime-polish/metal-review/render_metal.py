"""Nine-frame offline steel-contact comparison at 1.5m.

Actual actor/effect GLBs, same camera and light. Contact-frame directions are a
labelled example (T=Stage+X, B=+Y, N=+Z), never claimed as recorded SDK input.
"""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
CONTACT = HERE.parents[1] / 'contact-polish'
sys.path.insert(0, str(CONTACT))
from offline_opacity import independent_alpha_controls, ownership_report
from contact_motion import interpolate

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 4
scene.cycles.use_denoising = True
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new('Fixed same-light steel study')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.055, .065, .078, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .50

actor_path = REPO / 'app/src/main/assets/models/opponents/base.glb'
bpy.ops.import_scene.gltf(filepath=str(actor_path))
actor_objects = list(bpy.context.selected_objects)
for obj in actor_objects:
    if obj.type == 'ARMATURE' and obj.animation_data:
        obj.animation_data.action = None
        for track in obj.animation_data.nla_tracks:
            track.mute = track.name != 'idle'
scene.frame_set(12)
bpy.context.view_layer.update()
graph = bpy.context.evaluated_depsgraph_get()
steel = []
for obj in actor_objects:
    if obj.type != 'MESH':
        continue
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    try:
        for face in mesh.polygons:
            material = mesh.materials[face.material_index].name
            if 'Steel | forged body' not in material and 'Steel | sharpened edge' not in material:
                continue
            center = evaluated.matrix_world @ face.center
            normal = (evaluated.matrix_world.to_3x3().inverted().transposed() @ face.normal).normalized()
            if normal.y < -.1:
                steel.append((center.copy(), normal.copy(), material))
    finally:
        evaluated.to_mesh_clear()
if not steel:
    raise ValueError('No front-facing steel surface found on the current runtime actor')
steel_center = sum((face[0] for face in steel), Vector()) / len(steel)
point, actual_normal, material_name = min(steel, key=lambda face: (face[0] - steel_center).length_squared)
# Explicit example basis; glTF Stage +Z becomes Blender -Y.
anchor = point + Vector((0, -.008, 0))


def imported_effect(path, name):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = list(bpy.context.selected_objects)
    parent = bpy.data.objects.new(name, None)
    scene.collection.objects.link(parent)
    parent.location = anchor
    meshes = {}
    for obj in objects:
        if obj.parent is None:
            obj.parent = parent
        if obj.type == 'MESH':
            meshes[obj.name.split('.')[0]] = (obj, independent_alpha_controls(obj))
    return objects, meshes


baseline_path = REPO / 'app/src/main/assets/models/effects/metal_contact.glb'
candidate_path = CONTACT / 'metal/metal_contact_polish.glb'
old_objects, old_meshes = imported_effect(baseline_path, 'Old whole debris layer')
normal_objects, normal_meshes = imported_effect(candidate_path, 'Ordinary independent steel particles')
parry_objects, parry_meshes = imported_effect(candidate_path, 'Parry independent steel particles')
motion = json.loads((CONTACT / 'metal/motion.json').read_text())
all_effects = [old_objects, normal_objects, parry_objects]
SIZE = 1.019


def stage(value):
    return Vector((value[0], -value[2], value[1]))


def alpha(controls, value):
    for control in controls:
        control.default_value = max(0, min(1, value))


def update(age, kind):
    active_index = {'old': 0, 'normal': 1, 'parry': 2}[kind]
    for index, objects in enumerate(all_effects):
        for obj in objects:
            obj.hide_render = index != active_index
    if kind == 'old':
        progress = age / .44
        core, controls = old_meshes['core']
        s = (.7 + age * 3) * SIZE
        core.scale = (s, SIZE, s)
        core.hide_render = age >= .065
        alpha(controls, 1 - age / .065)
        debris, controls = old_meshes['debris']
        spread = (.22 + progress * 1.1) * SIZE
        debris.scale = (spread, SIZE, spread)
        debris.location = stage((0, -.32 * age * age, .14 * age)) * SIZE
        alpha(controls, (1 - progress) ** 2)
        scar, controls = old_meshes['scar']
        value = max(0, 1 - age / .1)
        scar.scale = (SIZE, SIZE, max(.08, value) * SIZE)
        scar.location = stage((0, 0, .004)) * SIZE
        alpha(controls, value)
        return
    meshes = parry_meshes if kind == 'parry' else normal_meshes
    parry = kind == 'parry'
    velocity_gain = 1.8 if parry else 1
    particle_size = SIZE * (1.65 if parry else 1.25)
    gravity = Vector((0, 0, -9.81))
    for particle in motion['particles']:
        obj, controls = meshes[particle['node']]
        obj.hide_render = age >= particle['lifetime_s']
        velocity = stage(particle['initial_velocity_local_mps']) * velocity_gain
        obj.location = stage(particle['initial_position_local_m']) + velocity * age + gravity * (.5 * age * age)
        obj.scale = (particle_size, particle_size, particle_size)
        direction = (velocity + gravity * age).normalized()
        width_axis = Vector((0, -1, 0)).cross(direction).normalized()
        depth_axis = width_axis.cross(direction).normalized()
        obj.rotation_mode = 'QUATERNION'
        # Imported glTF local X is streak length; source local Y maps to Blender Z.
        obj.rotation_quaternion = Matrix((direction, depth_axis, width_axis)).transposed().to_quaternion()
        alpha(controls, interpolate(particle['opacity_keys'], age))
    for core in motion['cores']:
        obj, controls = meshes[core['node']]
        profile = core['parry' if parry else 'normal']
        obj.hide_render = age >= profile['lifetime_s']
        obj.location = stage(core['initial_position_local_m'])
        growth = (.85 + min(age, .09) * 3) * SIZE * (2.6 if parry else 1.9)
        obj.scale = (growth, growth, growth)
        alpha(controls, interpolate(profile['opacity_keys'], age))


for name, position, energy, color in [('Wide key', (-3, -4, 4), 650, (1, .84, .70)),
                                      ('Wide fill', (3, -2, 2.5), 420, (.64, .78, 1))]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = energy, 5, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
camera_data = bpy.data.cameras.new('Fixed 1.5m steel contact camera')
camera_data.type = 'PERSP'
camera_data.lens_unit = 'FOV'
camera_data.angle = math.radians(80)
camera = bpy.data.objects.new('Fixed 1.5m steel contact camera', camera_data)
scene.collection.objects.link(camera)
camera.location = (point.x, point.y - 1.5, point.z)
camera.rotation_euler = (point - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
manifest = {'scope': 'OFFLINE actual actor and GLBs; labelled synthetic contact basis; not SDK evidence',
            'actor': str(actor_path.relative_to(REPO)), 'actor_sha256': hashlib.sha256(actor_path.read_bytes()).hexdigest(),
            'baseline_sha256': hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
            'motion_sha256': hashlib.sha256((CONTACT / 'metal/motion.json').read_bytes()).hexdigest(),
            'contact_point_blender_m': list(point), 'actual_surface_normal_blender': list(actual_normal), 'material': material_name,
            'basis_stage': {'T': [1, 0, 0], 'B': [0, 1, 0], 'N': [0, 0, 1]},
            'basis_policy': 'Explicit synthetic basis; actual surface normal recorded only, not claimed to match this example.',
            'distance_m': 1.5, 'horizontal_fov_degrees': 80, 'stage_gravity_mps2': [0, -9.81, 0],
            'normal_core_scale': '(.85 + min(age,.09)*3)*1.019*1.9', 'parry_core_scale': '(.85 + min(age,.09)*3)*1.019*2.6',
            'core_calibration': 'Independent ordinary=1.9/parry=2.6; parry does not multiply the old 1.7 again',
            'normal_particle_scale': 1.019*1.25, 'parry_particle_scale': 1.019*1.65, 'parry_velocity_extra': 1.8,
            'scale_gravity': False, 'core_seconds': {'normal': .065, 'parry': .090}, 'images': []}
for age in (1/30, 2/30, 5/30):
    for kind in ('old', 'normal', 'parry'):
        update(age, kind)
        name = f'metal_{round(age*1000):03d}ms_{kind}.png'
        scene.render.filepath = str(HERE / name)
        bpy.ops.render.render(write_still=True)
        manifest['images'].append(name)
manifest['opacity_ownership'] = ownership_report([obj for meshes in (old_meshes, normal_meshes, parry_meshes) for obj, _ in meshes.values()])
(HERE / 'render_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print('METAL_1_5M_TIMELINE_COMPLETE')
