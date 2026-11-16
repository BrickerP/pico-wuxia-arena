"""Author five upright, grounded overhead keyposes on the existing skinned rig."""

import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CANDIDATE = HERE / 'candidate'
PRODUCER = REPO / 'ArtSource/tripo-warrior'
STAGE2 = REPO / 'ArtSource/refinement/slash-refinement/candidate'
sys.path.insert(0, str(PRODUCER))
import prepare_character_library as library
from prepare_rigged_warrior import prepare_character, publish_outputs, output_info
from refine_character_grips import accessor
from mathutils import Matrix, Quaternion, Vector
import numpy as np

PINS = {
    'rig': (PRODUCER / 'refined-base60k/rig.glb', '43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6'),
    'slash': (STAGE2 / 'slash_guard_raw.glb', '43e0ca0b0501f4be4dc066e045d1b60092e3bd65aea228bc3a2a32405f826391'),
    'idle': (HERE.parent / 'candidate/retargeted/idle.glb', '304eeee2f521879044d33218fc48f688f164fd4b7003df2a1bfc84b36d8c0139'),
    'snapshot': (STAGE2 / 'input_snapshot.json', 'b4c6585c55f32019b09cef510246735a90fc9b417b681fb8213aef08bcd8de8d'),
    'weapon_reference': (STAGE2 / 'slash_guard_preview.glb', '34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896'),
    'weapon_alignment': (STAGE2 / 'slash_guard_alignment.json', '32e96e4e65183f0c1ea3b68737b32c52d917c5649172ab71a0f72eeaca49fc9a'),
    'native_grip': (PRODUCER / 'refined-base60k/slash.glb', '98e785d73a5d6cb767cebd5b79ec2bb9af9a2b717ae2d2576f3a0b7e07ea370a'),
    'dao': (REPO / 'ArtSource/dao/dao_study.glb', '0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616'),
}
RIGHT_FINGERS = {f'R_{finger}{part}' for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky') for part in (1, 2, 3)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_path(name):
    path = CANDIDATE / name
    if path.resolve().parent != CANDIDATE.resolve():
        raise ValueError('output must remain within keypose candidate')
    return path


def load_inputs():
    for name, (path, expected) in PINS.items():
        if digest(path) != expected:
            raise ValueError('frozen keypose input changed: ' + name)
    snapshot = json.loads(PINS['snapshot'][0].read_text())
    for name, expected in snapshot['producer_code_sha256'].items():
        if digest(PRODUCER / name) != expected:
            raise ValueError('frozen producer changed: ' + name)
    rig, binary = library.read_glb(PINS['rig'][0])
    idle, idle_binary = library.read_glb(PINS['idle'][0])
    slash, slash_binary = library.read_glb(PINS['slash'][0])
    return rig, binary, idle, idle_binary, slash, slash_binary, snapshot


def worlds(rig, local, parents, order):
    result = {}
    for index in order:
        matrix = Matrix.LocRotScale(*local[index])
        result[index] = result[parents[index]] @ matrix if index in parents else matrix
    return result


def sample_locals(rig, doc, binary, time):
    tracks, _ = library.decode_animation(doc, binary)
    return {index: list(library.sampled_local(node, index, tracks, time).decompose())
            for index, node in enumerate(rig['nodes'])}


def native_finger_components(doc, binary, names):
    tracks, _ = library.decode_animation(doc, binary)
    result = {}
    for name, index in names.items():
        if not isinstance(name, str) or not name.startswith(('R_Thumb','R_Index','R_Mid','R_Ring','R_Pinky',
                                                           'L_Thumb','L_Index','L_Mid','L_Ring','L_Pinky')):
            continue
        location = Vector(library.sample_track(tracks[(index,'translation')],2.117,False))
        x,y,z,w = library.sample_track(tracks[(index,'rotation')],2.117,True)
        rotation = Quaternion((w,x,y,z))
        scale = Vector(library.sample_track(tracks[(index,'scale')],2.117,False))
        result[index] = [location,rotation,scale]
    return result


def set_world_rotation(local, index, wanted, world, parents):
    parent = world[parents[index]].to_quaternion() if index in parents else Quaternion((1, 0, 0, 0))
    local[index][1] = (parent.inverted() @ wanted).normalized()


def aim_segment(rig, local, name, child, wanted, names, parents, order):
    world = worlds(rig, local, parents, order)
    index, end = names[name], names[child]
    current = (world[end].translation-world[index].translation).normalized()
    direction = (wanted-world[index].translation).normalized()
    delta = current.rotation_difference(direction)
    set_world_rotation(local, index, delta @ world[index].to_quaternion(), world, parents)


def solve_arm(rig, local, side, target, pole, names, parents, order):
    chain = [names[side+name] for name in ('Upperarm', 'Forearm', 'Hand')]
    world = worlds(rig, local, parents, order)
    shoulder, elbow, wrist = [world[index].translation for index in chain]
    upper, lower = (elbow-shoulder).length, (wrist-elbow).length
    distance = (target-shoulder).length
    if not all(math.isfinite(value) for vector in (target, pole) for value in vector):
        raise ValueError('IK targets must be finite')
    if not abs(upper-lower)+1e-5 < distance < upper+lower-1e-5:
        raise ValueError(f'{side} wrist target unreachable: distance {distance:.6f}, reach {upper+lower:.6f}')
    direction = (target-shoulder).normalized()
    along = (upper*upper-lower*lower+distance*distance)/(2*distance)
    height = math.sqrt(max(0, upper*upper-along*along))
    bend = pole-shoulder
    bend -= direction*bend.dot(direction)
    if bend.length <= 1e-8:
        raise ValueError('IK elbow pole is collinear')
    wanted_elbow = shoulder+direction*along+bend.normalized()*height
    aim_segment(rig, local, side+'Upperarm', side+'Forearm', wanted_elbow, names, parents, order)
    aim_segment(rig, local, side+'Forearm', side+'Hand', target, names, parents, order)
    result = worlds(rig, local, parents, order)
    error = (result[chain[-1]].translation-target).length
    if error > 1e-5:
        raise ValueError('IK reconstruction error exceeds tolerance')
    return error


def blade_frame():
    doc, binary = library.read_glb(PINS['weapon_reference'][0])
    alignment = json.loads(PINS['weapon_alignment'][0].read_text())
    names = [doc['nodes'][index]['name'] for index in doc['skins'][0]['joints']]
    inverse = accessor(doc, binary, doc['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    bind = Matrix(inverse[names.index('R_Hand')].tolist())
    mesh = next(doc['meshes'][node['mesh']] for node in doc['nodes'] if node.get('name') == 'TripoBody_Mesh')
    points = []
    for source in alignment['weapon_binding']['primitive_sources']:
        if source['source_node'].startswith('Blade') and source['source_node'] != 'Blade collar':
            primitive = mesh['primitives'][source['target_primitive']]
            for row in accessor(doc, binary, primitive['attributes']['POSITION']):
                point = bind @ Vector(row)
                points.append(point)
    if not points:
        raise ValueError('reference has no real blade vertices')
    tip = max(points, key=lambda point: point.length)
    base = min(points, key=lambda point: point.length)
    dao, _ = library.read_glb(PINS['dao'][0])
    blade = next(index for index,node in enumerate(dao['nodes']) if node.get('name') == 'Blade')
    grip = next(node for node in doc['nodes'] if node.get('name') == 'HandGrip_R')
    mount = library.local_matrix(grip)
    blade_world = library.world_matrix(dao['nodes'], blade)
    edge = mount.to_3x3() @ blade_world.to_3x3() @ Vector((1, 0, 0))
    return tip, base, edge.normalized()


def foot_surface_heights(rig, binary, world, norm):
    joints = rig['skins'][0]['joints']
    joint_names = [rig['nodes'][index]['name'] for index in joints]
    bind = accessor(rig, binary, rig['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    transforms = np.array([list(world[index]) for index in joints]) @ bind
    primitive = next(rig['meshes'][node['mesh']]['primitives'][0] for node in rig['nodes'] if 'skin' in node)
    attributes = primitive['attributes']
    positions = accessor(rig,binary,attributes['POSITION']).astype(float)
    palettes = accessor(rig,binary,attributes['JOINTS_0']).astype(int)
    weights = accessor(rig,binary,attributes['WEIGHTS_0']).astype(float)
    weights /= weights.sum(axis=1)[:,None]
    combined = np.sum(transforms[palettes]*weights[:,:,None,None],axis=1)
    posed = np.einsum('vij,vj->vi',combined,np.column_stack((positions,np.ones(len(positions)))))
    prepared = posed @ np.array(norm).T
    heights = {}
    for side in ('L_', 'R_'):
        foot_palette = [i for i,name in enumerate(joint_names) if name in {side+'Foot',side+'ToeBase'}]
        mask = sum(np.sum(weights*(palettes==index),axis=1) for index in foot_palette) > .5
        if not mask.any():
            raise ValueError('weighted foot surface unavailable')
        heights[side] = float(prepared[mask,1].min())
    return heights


def validate_parameters(parameters):
    look = parameters['look_target_metres']
    if len(look) != 3 or not all(math.isfinite(value) for value in look):
        raise ValueError('look target must contain three finite values')
    if not math.isfinite(parameters['contact_plane_z_metres']):
        raise ValueError('contact plane must be finite')
    poses = parameters.get('poses', [])
    if len(poses) != 5:
        raise ValueError('exactly five keyposes are required')
    times = [pose['time_seconds'] for pose in poses]
    if not all(math.isfinite(time) and time >= 0 for time in times) or any(b <= a for a,b in zip(times,times[1:])):
        raise ValueError('keypose times must be finite and increasing')
    for pose in poses:
        if not math.isfinite(pose['torso_lean_degrees']) or not 0 <= pose['torso_lean_degrees'] <= 20:
            raise ValueError('torso lean must be finite and within the authored upright range')
        seed_time = pose['native_seed_seconds']
        if not math.isfinite(seed_time) or not .0333333 <= seed_time <= 6.6:
            raise ValueError('native seed time lies outside the frozen slash')
        for key in ('right_hand_metres', 'left_hand_metres', 'blade_direction', 'right_elbow_pole_metres', 'left_elbow_pole_metres'):
            value = pose[key]
            if len(value) != 3 or not all(math.isfinite(v) for v in value):
                raise ValueError('invalid keypose vector: ' + key)
        if Vector(pose['blade_direction']).length < 1e-8:
            raise ValueError('blade direction must be nonzero')


def author_poses(rig, idle, idle_binary, slash, slash_binary, snapshot, parameters):
    validate_parameters(parameters)
    parents, order = library.node_order(rig)
    names = {node.get('name'): index for index,node in enumerate(rig['nodes'])}
    norm = library.local_matrix({'matrix': snapshot['stage1_alignment']['normalization_matrix_gltf']})
    inverse_norm = norm.inverted()
    reference = {index: list(library.local_matrix(node).decompose()) for index,node in enumerate(rig['nodes'])}
    reference_world = worlds(rig, reference, parents, order)
    base = sample_locals(rig, idle, idle_binary, 1.0)
    world = worlds(rig, base, parents, order)
    hip = (norm@world[names['Hip']]).translation
    rebase = inverse_norm.to_3x3() @ Vector((-hip.x, 0, -hip.z))
    base[names['BoneRoot']][0] += rebase
    base_world = worlds(rig,base,parents,order)
    rig_binary = library.read_glb(PINS['rig'][0])[1]
    initial_soles = foot_surface_heights(rig,rig_binary,base_world,norm)
    ground_shift = inverse_norm.to_3x3() @ Vector((0,-min(initial_soles.values()),0))
    base[names['BoneRoot']][0] += ground_shift
    rebase += ground_shift
    native_doc,native_binary = library.read_glb(PINS['native_grip'][0])
    native = native_finger_components(native_doc,native_binary,names)
    for name in RIGHT_FINGERS:
        base[names[name]] = copy.deepcopy(native[names[name]])
    for name,index in names.items():
        if isinstance(name,str) and name.startswith(('L_Thumb','L_Index','L_Mid','L_Ring','L_Pinky')):
            weight = .22*(.55 if name.startswith('L_Thumb') else 1)
            base[index][0] = native[index][0].copy()
            base[index][2] = native[index][2].copy()
            base[index][1] = reference[index][1].normalized().slerp(native[index][1].normalized(),weight).normalized()
    tip_local, blade_base_local, edge_local = blade_frame()
    results, measurements = [], []
    for pose in parameters['poses']:
        local = copy.deepcopy(base)
        seed = sample_locals(rig, slash, slash_binary, pose['native_seed_seconds'])
        seed_world = worlds(rig, seed, parents, order)
        for name in ('Waist', 'Spine01', 'Spine02', 'NeckTwist01', 'NeckTwist02', 'Head'):
            world = worlds(rig, local, parents, order)
            set_world_rotation(local, names[name], reference_world[names[name]].to_quaternion(), world, parents)
        raw_axis = (inverse_norm.to_3x3() @ Vector((1,0,0))).normalized()
        for name,fraction in [('Waist',.2),('Spine01',.5),('Spine02',1.0)]:
            world = worlds(rig,local,parents,order)
            delta = Quaternion(raw_axis,math.radians(pose['torso_lean_degrees']*fraction))
            set_world_rotation(local,names[name],delta@reference_world[names[name]].to_quaternion(),world,parents)
        for name in ('NeckTwist01','NeckTwist02','Head'):
            world = worlds(rig,local,parents,order)
            set_world_rotation(local,names[name],reference_world[names[name]].to_quaternion(),world,parents)
        world = worlds(rig,local,parents,order)
        head_position = (norm@world[names['Head']]).translation
        look = inverse_norm.to_3x3() @ (Vector(parameters['look_target_metres'])-head_position)
        gaze_delta = Vector((1,0,0)).rotation_difference(look.normalized())
        set_world_rotation(local,names['Head'],gaze_delta@reference_world[names['Head']].to_quaternion(),world,parents)
        for side in ('R_', 'L_'):
            for name in ('Upperarm', 'Forearm', 'Hand'):
                local[names[side+name]][1] = seed[names[side+name]][1].copy()
        right_target = inverse_norm @ Vector(pose['right_hand_metres'])
        left_target = inverse_norm @ Vector(pose['left_hand_metres'])
        errors = {}
        for side, target, pole_key in [('R_',right_target,'right_elbow_pole_metres'), ('L_',left_target,'left_elbow_pole_metres')]:
            errors[side] = solve_arm(rig,local,side,target,inverse_norm@Vector(pose[pole_key]),names,parents,order)
        world = worlds(rig,local,parents,order)
        wanted_direction = inverse_norm.to_3x3() @ Vector(pose['blade_direction']).normalized()
        seed_rotation = seed_world[names['R_Hand']].to_quaternion()
        current_direction = seed_rotation @ (tip_local-blade_base_local)
        delta = current_direction.rotation_difference(wanted_direction)
        wanted_rotation = delta@seed_rotation
        blade_axis = wanted_direction.normalized()
        edge = wanted_rotation@edge_local
        edge = (edge-blade_axis*edge.dot(blade_axis)).normalized()
        prepared_direction = Vector(pose['blade_direction']).normalized()
        cut_prepared = Vector((0,-prepared_direction.z,prepared_direction.y)).normalized()
        cut = (inverse_norm.to_3x3()@cut_prepared).normalized()
        cut = (cut-blade_axis*cut.dot(blade_axis)).normalized()
        cross = Vector((edge.y*cut.z-edge.z*cut.y,edge.z*cut.x-edge.x*cut.z,edge.x*cut.y-edge.y*cut.x))
        roll = math.atan2(blade_axis.dot(cross),edge.dot(cut))
        wanted_rotation = Quaternion(blade_axis,roll)@wanted_rotation
        set_world_rotation(local,names['R_Hand'],wanted_rotation,world,parents)
        # Keep the empty palm facing its native protective reference while moving the arm.
        world = worlds(rig,local,parents,order)
        set_world_rotation(local,names['L_Hand'],seed_world[names['L_Hand']].to_quaternion(),world,parents)
        world = worlds(rig,local,parents,order)
        hand = norm@world[names['R_Hand']]
        tip = hand@tip_local
        blade_base = hand@blade_base_local
        contact_fraction = (parameters['contact_plane_z_metres']-blade_base.z)/(tip.z-blade_base.z) if abs(tip.z-blade_base.z)>1e-8 else None
        contact = blade_base+(tip-blade_base)*contact_fraction if contact_fraction is not None else None
        head = (norm@world[names['Head']]).translation
        pelvis = (norm@world[names['Hip']]).translation
        spine_up_local = reference_world[names['Spine02']].to_quaternion().inverted() @ Vector((0,1,0))
        spine_up = (norm.to_3x3() @ (world[names['Spine02']].to_quaternion() @ spine_up_local)).normalized()
        actual_lean = math.degrees(math.atan2(spine_up.z,spine_up.y))
        head_forward_local = reference_world[names['Head']].to_quaternion().inverted() @ Vector((1,0,0))
        head_forward = (norm.to_3x3() @ (world[names['Head']].to_quaternion() @ head_forward_local)).normalized()
        desired_gaze = (Vector(parameters['look_target_metres'])-head).normalized()
        actual_edge = (hand.to_3x3()@edge_local).normalized()
        actual_axis = (tip-blade_base).normalized()
        edge_projected = (actual_edge-actual_axis*actual_edge.dot(actual_axis)).normalized()
        measurements.append({'label':pose['label'],'time_seconds':pose['time_seconds'],
            'right_hand_metres':list(hand.translation),'blade_tip_metres':list(tip),
            'blade_base_metres':list(blade_base),
            'blade_edge_direction_metres':list((hand.to_3x3()@edge_local).normalized()),
            'blade_axis_direction_cosine':actual_axis.dot(prepared_direction),
            'blade_edge_cut_tangent_cosine':edge_projected.dot(cut_prepared),
            'contact_plane_intersection_metres':list(contact) if contact is not None else None,
            'contact_plane_intersection_kind':'base-to-tip chord approximation',
            'real_surface_contact':parameters['real_surface_contact'] if pose['label']=='contact_guard' else None,
            'contact_intersection_on_blade_segment':contact_fraction is not None and 0<=contact_fraction<=1,
            'target_lean_degrees':pose['torso_lean_degrees'],
            'actual_lean_degrees':actual_lean,
            'lean_error_degrees':actual_lean-pose['torso_lean_degrees'],
            'head_gaze_cosine':head_forward.dot(desired_gaze),
            'right_hand_target_error_metres':(hand.translation-Vector(pose['right_hand_metres'])).length,
            'left_hand_target_error_metres':((norm@world[names['L_Hand']]).translation-Vector(pose['left_hand_metres'])).length,
            'left_hand_metres':list((norm@world[names['L_Hand']]).translation),
            'feet_world_gltf_m': {
                'left': list((norm@world[names['L_Foot']]).translation),
                'right': list((norm@world[names['R_Foot']]).translation),
            },
            'head_metres':list(head),'hip_metres':list(pelvis),
            'head_hip_forward_offset_metres':head.z-pelvis.z,
            'foot_surface_heights_metres':foot_surface_heights(rig,rig_binary,world,norm),
            'ik_error_metres':{key:value*snapshot['stage1_alignment']['uniform_scale'] for key,value in errors.items()}})
        results.append(local)
    return results, measurements, {'tip_local':list(tip_local),'base_local':list(blade_base_local),'source_x_edge_local':list(edge_local)}, list(rebase)


def encode_clip(rig, binary, poses, times):
    doc = copy.deepcopy(rig)
    packed = bytearray(binary)

    def append(rows, kind):
        packed.extend(b'\0' * (-len(packed) % 4))
        offset = len(packed)
        for row in rows:
            packed.extend(struct.pack('<' + 'f' * len(row), *row))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append({
            'buffer': 0, 'byteOffset': offset, 'byteLength': len(packed) - offset,
        })
        index = len(doc['accessors'])
        item = {'bufferView': view, 'componentType': 5126, 'type': kind, 'count': len(rows)}
        if kind == 'SCALAR':
            item.update(min=[rows[0][0]], max=[rows[-1][0]])
        doc['accessors'].append(item)
        return index

    time_index = append([(time,) for time in times], 'SCALAR')
    animation = {'name': 'overhead_keyposes', 'channels': [], 'samplers': []}
    for index in rig['skins'][0]['joints']:
        for path, slot, kind in [('translation', 0, 'VEC3'), ('rotation', 1, 'VEC4'), ('scale', 2, 'VEC3')]:
            rows = []
            for pose in poses:
                value = pose[index][slot]
                row = (value.x, value.y, value.z, value.w) if path == 'rotation' else tuple(value)
                if rows and path == 'rotation' and sum(a * b for a, b in zip(rows[-1], row)) < 0:
                    row = tuple(-value for value in row)
                rows.append(row)
            output = append(rows, kind)
            animation['channels'].append({
                'sampler': len(animation['samplers']), 'target': {'node': index, 'path': path},
            })
            animation['samplers'].append({
                'input': time_index, 'output': output, 'interpolation': 'STEP',
            })
    doc['animations'] = [animation]
    doc['buffers'][0]['byteLength'] = len(packed)
    doc.setdefault('extras', {})['attack_keyposes'] = {
        'stage': 'authored_raw', 'right_calibration_baked': False, 'sample_count': 5,
    }
    return library.encode_glb(doc, bytes(packed))


def main():
    output_path('verification.json').unlink(missing_ok=True)
    rig, binary, idle, idle_binary, slash, slash_binary, snapshot = load_inputs()
    parameters = json.loads(output_path('keypose_parameters.json').read_text())
    poses, measurements, blade, rebase = author_poses(
        rig, idle, idle_binary, slash, slash_binary, snapshot, parameters,
    )
    output_path('metadata.json').write_text(json.dumps({'completion': 'in_progress'}, indent=2) + '\n')
    raw = output_path('overhead_keyposes_raw.glb')
    times = [pose['time_seconds'] for pose in parameters['poses']]
    raw.write_bytes(encode_clip(rig, binary, poses, times))
    lexical = PRODUCER / '../refinement/hand-poses/attack-keyposes/candidate/overhead_keyposes_raw.glb'
    if lexical.resolve() != raw.resolve():
        raise ValueError('candidate clip path escaped')
    character = snapshot['base_configuration']
    body = output_path('overhead_keyposes_body.glb')
    preview = output_path('overhead_keyposes_preview.glb')
    alignment = output_path('overhead_keyposes_alignment.json')
    record = prepare_character(
        PINS['rig'][0], PINS['rig'][1], [('overhead_keyposes', lexical, digest(raw))],
        body, preview, alignment, height=character['height_metres'],
        grip_frame=character['grip_frame'], finger_rotation_offsets=character['finger_rotation_offsets'],
    )
    outputs = []
    for path in (body, preview):
        doc, packed = library.read_glb(path)
        doc.setdefault('extras', {})['attack_keyposes'] = {
            'stage': 'preview_baked', 'right_calibration_applications': 1, 'raw_sha256': digest(raw),
        }
        outputs.append((path, library.encode_glb(doc, packed)))
    record['outputs'] = [output_info(path, data) for path, data in outputs]
    outputs.append((alignment, (json.dumps(record, indent=2) + '\n').encode()))
    publish_outputs(outputs)
    metadata = {
        'completion': 'complete', 'clip': 'overhead_keyposes', 'sample_count': 5,
        'source_pins': {
            name: {'path': str(path.relative_to(REPO)), 'sha256': expected}
            for name, (path, expected) in PINS.items()
        },
        'producer_code_sha256': snapshot['producer_code_sha256'],
        'parameters_sha256': digest(output_path('keypose_parameters.json')),
        'raw_stage': 'authored rotations; fixed idle lower body; right calibration UNBAKED',
        'preview_stage': 'original base eight right offsets applied ONCE',
        'right_calibration': record['finger_rotation_calibration'], 'actual_blade_frame': blade,
        'actor_rebase_source': rebase, 'measurements': measurements,
        'raw_output': output_info(raw, raw.read_bytes()), 'preview_outputs': record['outputs'],
        'real_surface_contact': parameters['real_surface_contact'],
        'approximate_chord_contact': parameters['approximate_chord_contact'],
        'scope': 'five independent STEP keypose holds for review; complete action timing awaits review',
    }
    output_path('metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('KEYPOSES_READY', digest(preview), preview, flush=True)
    print(json.dumps(measurements, indent=2), flush=True)


if __name__ == '__main__':
    main()
