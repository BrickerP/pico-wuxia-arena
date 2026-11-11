"""Same-camera normal-distance offline soft-contact comparison on the runtime actor.

Uses actual GLB geometry and PBR. Sample tangent is explicit and synthetic;
this is not a PICO screenshot or proof of actual collision/material selection.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
REVIEW = HERE.parent / 'review'
REVIEW.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE.parents[1] / 'contact-polish'))
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
scene.world = bpy.data.worlds.new('Same-light contact study')
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
faces = []
for obj in actor_objects:
    if obj.type != 'MESH':
        continue
    evaluated = obj.evaluated_get(graph)
    mesh = evaluated.to_mesh()
    try:
        for face in mesh.polygons:
            center = evaluated.matrix_world @ face.center
            normal = (evaluated.matrix_world.to_3x3().inverted().transposed() @ face.normal).normalized()
            if normal.y < -.30 and 1.00 < center.z < 1.28 and abs(center.x - .10) < .15:
                faces.append((center.copy(), normal.copy(), mesh.materials[face.material_index].name))
    finally:
        evaluated.to_mesh_clear()
if not faces:
    raise ValueError('No front torso surface found on the current runtime actor')
point, normal, surface = min(faces, key=lambda item: (item[0].x - .10) ** 2 + (item[0].z - 1.12) ** 2)
anchor = point + normal * .008
placement_rotation = Vector((0, -1, 0)).rotation_difference(normal)
SIZE = .72 + .65 * .46


def imported_effect(path, name):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = list(bpy.context.selected_objects)
    parent = bpy.data.objects.new(name, None)
    scene.collection.objects.link(parent)
    parent.location = anchor
    parent.rotation_mode = 'QUATERNION'
    parent.rotation_quaternion = placement_rotation
    # Particle world gravity is converted through the actual parent rotation.
    meshes = {}
    for obj in imported:
        if obj.parent is None:
            obj.parent = parent
        if obj.type == 'MESH':
            meshes[obj.name.split('.')[0]] = (obj, independent_alpha_controls(obj))
    return parent, imported, meshes


before_parent, before_objects, before = imported_effect(REPO / 'app/src/main/assets/models/effects/soft_contact.glb', 'Before current runtime layers')
after_parent, after_objects, after = imported_effect(HERE / 'soft_contact_polish.glb', 'After independent dry soft particles')
motion = json.loads((HERE / 'motion.json').read_text())


def stage(value):
    return Vector((value[0], -value[2], value[1]))


def set_alpha(controls, value):
    for control in controls:
        control.default_value = max(0, min(1, value))


def update(age, mode):
    for obj in before_objects:
        obj.hide_render = mode != 'before'
    for obj in after_objects:
        obj.hide_render = mode != 'after'
    if mode == 'before':
        progress = age / .62
        core, controls = before['core']
        s = (.7 + age * 3) * SIZE
        core.scale = (s, SIZE, s)
        set_alpha(controls, 1 - age / .05)
        core.hide_render = age >= .05
        debris, controls = before['debris']
        spread = (.22 + progress * 1.1) * SIZE
        debris.scale = (spread, SIZE, spread)
        debris.location = stage((0, -.32 * age * age, .14 * age)) * SIZE
        set_alpha(controls, (1 - progress) ** 2)
        scar, controls = before['scar']
        alpha = max(0, 1 - age / .10)
        scar.scale = (SIZE, SIZE, max(.08, alpha) * SIZE)
        scar.location = stage((0, 0, .004)) * SIZE
        set_alpha(controls, alpha)
        return
    # Placement local frame is contact TBN. Gravity remains Blender Stage -Z.
    gravity_local = placement_rotation.inverted() @ Vector((0, 0, -9.81))
    for particle in motion['particles']:
        obj, controls = after[particle['node']]
        obj.hide_render = age >= particle['lifetime_s']
        local = stage(particle['initial_position_local_m']) + stage(particle['initial_velocity_local_mps']) * age + gravity_local * (.5 * age * age)
        obj.location = local
        obj.scale = (SIZE, SIZE, SIZE)
        set_alpha(controls, interpolate(particle['opacity_keys'], age))
    for core in motion['cores']:
        obj, controls = after[core['node']]
        profile = core['normal']
        obj.hide_render = age >= profile['lifetime_s']
        obj.location = stage(core['initial_position_local_m'])
        obj.scale = (SIZE, SIZE, SIZE)
        set_alpha(controls, interpolate(profile['opacity_keys'], age))


for name, position, energy, color in [('Wide key', (-3, -4, 4), 650, (1, .84, .70)),
                                      ('Wide fill', (3, -2, 2.5), 420, (.64, .78, 1))]:
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.size, data.color = energy, 5, color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()

camera_data = bpy.data.cameras.new('Normal distance fixed camera')
camera_data.type = 'PERSP'
camera_data.lens_unit = 'FOV'
camera_data.angle = math.radians(80)
camera = bpy.data.objects.new('Normal distance fixed camera', camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
manifest = {'scope': 'OFFLINE actual actor and GLBs; synthetic tangent; not PICO runtime evidence',
            'actor': str(actor_path.relative_to(REPO)), 'actor_sha256': hashlib.sha256(actor_path.read_bytes()).hexdigest(),
            'source_glb_sha256': hashlib.sha256((REPO / 'app/src/main/assets/models/effects/soft_contact.glb').read_bytes()).hexdigest(),
            'candidate_glb_sha256': hashlib.sha256((HERE / 'soft_contact_polish.glb').read_bytes()).hexdigest(),
            'contact_point_blender_m': list(point), 'contact_normal_blender': list(normal), 'surface_material': surface,
            'gravity_blender_mps2': [0, 0, -9.81], 'strength': .65, 'horizontal_fov_degrees': 80,
            'distances_m': [.8, 1.5, 3], 'ages_s': [1/30, .1, 7/30], 'images': []}
for distance in (.8, 1.5, 3):
    camera.location = (point.x, point.y - distance, point.z)
    camera.rotation_euler = (point - camera.location).to_track_quat('-Z', 'Y').to_euler()
    for age in (1/30, .1, 7/30):
        for mode in ('before', 'after'):
            update(age, mode)
            filename = f'soft_{distance:.1f}m_{round(age*1000):03d}ms_{mode}.png'
            scene.render.filepath = str(REVIEW / filename)
            bpy.ops.render.render(write_still=True)
            manifest['images'].append(filename)
manifest['opacity_ownership'] = ownership_report([obj for obj, _ in [*before.values(), *after.values()]])
(REVIEW / 'soft_render_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('SOFT_NORMAL_DISTANCE_REVIEW_COMPLETE')
