"""Canonical candidate: constrain one target LEFT wrist during prepared asset production.

No historical model, camera, app or formal-bank dependency. The incoming prepared
asset itself supplies the unmodified wrist reference before any mutation.
"""
import copy
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from attack_profiles import (
    animation_tracks, hierarchy, pose_world, sample_track, skin_attribute,
)
from prepare_rigged_warrior import (
    local_matrix, animation_signature, read_glb, encode_glb,
)
BONES = ('R_Upperarm', 'R_Forearm', 'R_Hand')
STEEL_VERTEX_COUNT = 5533

def require(value, message):
    if not value:
        raise ValueError(message)

def smooth(value):
    value = max(0.0, min(1.0, value))
    return max(0.0, min(1.0, value ** 3 * (10.0 + value * (-15.0 + 6.0 * value))))

def amount(time, window):
    (start, a, b, end) = window
    if time <= start or time >= end:
        return 0.0
    if time < a:
        return smooth((time - start) / (a - start))
    if time <= b:
        return 1.0
    return 1.0 - smooth((time - b) / (end - b))

def validate_recipe(recipe):
    expected = {'schema_version', 'character_id', 'clip', 'arm_bones', 'swivel_degrees', 'window_source_seconds', 'local_sample_rate_hz', 'key_steel_budget_metres', 'subkey_steel_budget_metres', 'reference'}
    require(isinstance(recipe, dict) and set(recipe) == expected, 'Prepared wrist recipe fields differ')
    require(recipe['schema_version'] == 1 and recipe['character_id'] == 'veteran' and (recipe['clip'] == 'attack_left') and (tuple(recipe['arm_bones']) == BONES), 'Unsupported real target/clip/bones')
    require(recipe['reference'] == 'unconstrained_same_target_prepared_fk', 'External or mutable wrist reference is forbidden')
    require(recipe['local_sample_rate_hz'] == 120, 'Current accepted local density is120Hz')
    window = recipe['window_source_seconds']
    require(len(window) == 4 and all((type(v) in (int, float) and math.isfinite(v) for v in window)) and (0 <= window[0] < window[1] <= window[2] < window[3] <= 1.75), 'Invalid constrained interval')
    require(type(recipe['swivel_degrees']) in (int, float) and math.isfinite(recipe['swivel_degrees']), 'Finite real elbow swivel required')
    require(recipe['key_steel_budget_metres'] == 5e-06 and recipe['subkey_steel_budget_metres'] == 0.001, 'Do not relax accepted wrist/steel budgets')
    return recipe

def sampled_locals(doc, tracks, time):
    result = {}
    for (i, node) in enumerate(doc['nodes']):
        t = Vector(node.get('translation', (0, 0, 0)))
        q = node.get('rotation', (0, 0, 0, 1))
        q = Quaternion((q[3], *q[:3]))
        s = Vector(node.get('scale', (1, 1, 1)))
        if (i, 'translation') in tracks:
            t = Vector(sample_track(tracks[i, 'translation'], time, False))
        if (i, 'rotation') in tracks:
            v = sample_track(tracks[i, 'rotation'], time, True)
            q = Quaternion((v[3], *v[:3]))
        if (i, 'scale') in tracks:
            s = Vector(sample_track(tracks[i, 'scale'], time, False))
        result[i] = [t, q, s]
    return result

def exact_worlds(doc, local, parents, order):
    result = {}
    for i in order:
        # Preserve exact prepared normalization matrices without decomposition.
        m = local_matrix(doc['nodes'][i]) if 'matrix' in doc['nodes'][i] else Matrix.LocRotScale(*local[i])
        result[i] = result[parents[i]] @ m if i in parents else m
    return result

def append_accessor(doc, binary, values, kind):
    width = len(values[0])
    packed = bytearray(binary)
    packed.extend(b'\x00' * (-len(packed) % 4))
    start = len(packed)
    for row in values:
        packed.extend(struct.pack('<' + 'f' * width, *row))
    view = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(packed) - start})
    index = len(doc['accessors'])
    doc['accessors'].append({'bufferView': view, 'componentType': 5126, 'type': kind, 'count': len(values), 'min': [min((x[i] for x in values)) for i in range(width)], 'max': [max((x[i] for x in values)) for i in range(width)]})
    doc['buffers'][0]['byteLength'] = len(packed)
    return (bytes(packed), index)

def set_world_rotation(local, index, wanted, world, parents):
    parent = world[parents[index]].to_quaternion() if index in parents else Quaternion((1, 0, 0, 0))
    local[index][1] = (parent.inverted() @ wanted).normalized()

def aim_segment(doc, local, index, end, wanted, parents, order):
    world = exact_worlds(doc, local, parents, order)
    current = (world[end].translation - world[index].translation).normalized()
    direction = (wanted - world[index].translation).normalized()
    set_world_rotation(local, index, current.rotation_difference(direction) @ world[index].to_quaternion(), world, parents)

def solve_arm(doc, local, target, pole, names, parents, order):
    chain = [names[n] for n in BONES]
    world = exact_worlds(doc, local, parents, order)
    (s, e, w) = [world[i].translation for i in chain]
    (upper, lower) = ((e - s).length, (w - e).length)
    distance = (target - s).length
    require(abs(upper - lower) + 1e-05 < distance < upper + lower - 1e-05, 'Target wrist is unreachable without changing bone length')
    axis = (target - s).normalized()
    along = (upper * upper - lower * lower + distance * distance) / (2 * distance)
    height = math.sqrt(max(0, upper * upper - along * along))
    bend = pole - s
    bend -= axis * bend.dot(axis)
    require(bend.length > 1e-08, 'Collinear elbow pole')
    elbow = s + axis * along + bend.normalized() * height
    aim_segment(doc, local, chain[0], chain[1], elbow, parents, order)
    aim_segment(doc, local, chain[1], chain[2], target, parents, order)
    require((exact_worlds(doc, local, parents, order)[chain[-1]].translation - target).length <= 1e-05, 'Target IK reconstruction error')

def combined_steel_hand_points(doc, binary):
    """Require the actual combined weapon and return its rigid hand-local points."""
    names = {node['name']: i for i, node in enumerate(doc['nodes'])}
    hand = names['R_Hand']
    skin = doc['skins'][0]
    palette = skin['joints'].index(hand)
    inverse_bind = skin_attribute(doc, binary, skin['inverseBindMatrices'])
    hand_inverse_bind = inverse_bind[palette].reshape(4, 4).T
    points = []
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            material = doc['materials'][primitive['material']]
            if 'Steel' not in material.get('name', ''):
                continue
            attributes = primitive['attributes']
            positions = skin_attribute(doc, binary, attributes['POSITION'])
            joints = skin_attribute(doc, binary, attributes['JOINTS_0'])
            weights = skin_attribute(doc, binary, attributes['WEIGHTS_0'])
            require(np.all(np.isfinite(positions)), 'Combined Steel positions are not finite')
            require(np.all(np.isfinite(weights)) and np.all(weights >= 0),
                    'Combined Steel weights are invalid')
            require(np.all(joints < len(skin['joints'])),
                    'Combined Steel joint indices escape the palette')
            require(np.max(np.abs(weights.sum(axis=1) - 1)) <= 1e-6,
                    'Combined Steel weights are not normalized')
            outside_hand = np.sum(weights * (joints != palette), axis=1)
            require(np.max(outside_hand) <= 1e-6,
                    'Combined Steel is not rigid to R_Hand')
            homogeneous = np.column_stack((positions, np.ones(len(positions))))
            points.append((hand_inverse_bind @ homogeneous.T).T)
    require(points, 'Combined PNG has no Steel weapon surface')
    result = np.concatenate(points)
    require(len(result) == STEEL_VERTEX_COUNT,
            'Combined PNG Steel vertex count differs from the pinned weapon')
    return result


def wrist_orientation_error(old_frame, new_frame):
    """Return the complete wrist rigid-orientation difference, without acos rounding."""
    old = np.asarray(old_frame.to_quaternion(), dtype=np.float64)
    new = np.asarray(new_frame.to_quaternion(), dtype=np.float64)
    old /= np.linalg.norm(old)
    new /= np.linalg.norm(new)
    if np.dot(old, new) < 0:
        new = -new
    return 4 * math.atan2(np.linalg.norm(new - old), np.linalg.norm(new + old))


def apply_constraint(doc, binary, recipe, steel_points):
    validate_recipe(recipe)
    require(isinstance(steel_points, np.ndarray) and steel_points.shape == (STEEL_VERTEX_COUNT, 4),
            'The validated combined Steel reference is required')
    before = copy.deepcopy(doc)
    old_animation = next((a for a in before['animations'] if a['name'] == recipe['clip']))
    (tracks, times) = animation_tracks(before, binary, old_animation)
    times = sorted(times)
    (_, parents, order) = hierarchy(before)
    names = {n['name']: i for (i, n) in enumerate(before['nodes'])}
    require(times[0] == 0 and times[-1] == 1.75, 'Prepared attack duration changed')
    window = [struct.unpack('<f', struct.pack('<f', v))[0] for v in recipe['window_source_seconds']]
    rate = recipe['local_sample_rate_hz']
    dense = [struct.unpack('<f', struct.pack('<f', i / rate))[0] for i in range(math.ceil(window[0] * rate), math.floor(window[3] * rate) + 1)]
    # Include original boundary keys despite float32 rounding at 0.9/1.3.
    dense += [struct.unpack('<f', struct.pack('<f', v))[0] for v in (recipe['window_source_seconds'][0], recipe['window_source_seconds'][3])]
    newtimes = sorted(set(times) | set(dense))
    curves = {n: [] for n in BONES}
    replay = 0.0
    goal_frames = []
    for time in newtimes:
        local = sampled_locals(before, tracks, time)
        world = pose_world(before, tracks, time, parents, order)
        again = exact_worlds(before, local, parents, order)
        replay = max(replay, max((float(np.max(np.abs(np.asarray(world[i]) - np.asarray(again[i])))) for i in world)))
        require(replay == 0, 'Prepared baseline replay is not exact')
        value = amount(time, window)
        if value:
            shoulder = world[names[BONES[0]]].translation
            elbow = world[names[BONES[1]]].translation
            wrist = world[names[BONES[2]]].translation
            orientation = world[names[BONES[2]]].to_quaternion()
            axis = (wrist - shoulder).normalized()
            pole = shoulder + Quaternion(axis, math.radians(recipe['swivel_degrees']) * value) @ (elbow - shoulder)
            solve_arm(before, local, wrist, pole, names, parents, order)
            set_world_rotation(local, names[BONES[2]], orientation, exact_worlds(before, local, parents, order), parents)
        goal_frames.append([time, *[v for row in world[names[BONES[2]]] for v in row]])
        for bone in BONES:
            old = tracks[names[bone], 'rotation']
            if not value and time in old[0]:
                q = old[1][old[0].index(time)]
            else:
                q = local[names[bone]][1]
                q = (q.x, q.y, q.z, q.w)
                reference = sample_track(old, time, True)
                if sum((a * b for (a, b) in zip(q, reference))) < 0:
                    q = tuple((-v for v in q))
            curves[bone].append(q)
    (packed, time_accessor) = append_accessor(doc, binary, [(t,) for t in newtimes], 'SCALAR')
    animation = next((a for a in doc['animations'] if a['name'] == recipe['clip']))
    for bone in BONES:
        (packed, index) = append_accessor(doc, packed, curves[bone], 'VEC4')
        channel = next((c for c in animation['channels'] if c['target'] == {'node': names[bone], 'path': 'rotation'}))
        sampler = animation['samplers'][channel['sampler']]
        sampler['input'] = time_accessor
        sampler['output'] = index
    (actual, newgrid) = animation_tracks(doc, packed, animation)
    for (key, track) in tracks.items():
        if key[0] in {names[n] for n in BONES} and key[1] == 'rotation':
            continue
        require(track == actual[key], 'Untouched prepared LEFT track changed')
    old_signatures = {a['name']: animation_signature(before, binary, a) for a in before['animations']}
    new_signatures = {a['name']: animation_signature(doc, packed, a) for a in doc['animations']}
    require(all((v == new_signatures[k] for (k, v) in old_signatures.items() if k != recipe['clip'])), 'Another prepared clip changed')
    points = steel_points
    keymax = 0.0
    submax = 0.0
    wristmax = 0.0
    bone_max = 0.0
    sub_wrist_max = 0.0
    key_orientation_max = 0.0
    sub_orientation_max = 0.0
    key_orientation_displacement = 0.0
    sub_orientation_displacement = 0.0
    for time in sorted(set(newtimes) | {(a + b) / 2 for (a, b) in zip(newtimes, newtimes[1:])}):
        old = pose_world(before, tracks, time, parents, order)
        new = pose_world(doc, actual, time, parents, order)
        hand = names[BONES[2]]
        pos = (new[hand].translation - old[hand].translation).length
        old_points = (np.asarray(old[hand]) @ points.T).T[:, :3]
        new_points = (np.asarray(new[hand]) @ points.T).T[:, :3]
        error = float(np.max(np.linalg.norm(new_points - old_points, axis=1)))
        orientation = wrist_orientation_error(old[hand], new[hand])
        wrist_origin = np.asarray(old[hand].translation, dtype=np.float64)
        steel_radius = float(np.max(np.linalg.norm(old_points - wrist_origin, axis=1)))
        # Express full wrist orientation in the same accepted spatial budget,
        # at the actual weapon's furthest radius, rather than inventing an angle epsilon.
        orientation_displacement = 2 * steel_radius * math.sin(orientation / 2)
        if time in newtimes:
            keymax = max(keymax, error)
            wristmax = max(wristmax, pos)
            key_orientation_max = max(key_orientation_max, orientation)
            key_orientation_displacement = max(key_orientation_displacement, orientation_displacement)
        else:
            submax = max(submax, error)
            sub_wrist_max = max(sub_wrist_max, pos)
            sub_orientation_max = max(sub_orientation_max, orientation)
            sub_orientation_displacement = max(sub_orientation_displacement, orientation_displacement)
        for name in ('Head', 'BoneRoot', 'Hip', 'L_Foot', 'R_Foot'):
            require(np.array_equal(np.asarray(old[names[name]]), np.asarray(new[names[name]])), 'Protected head/root/foot changed')
        for (a, b) in zip(BONES[:2], BONES[1:]):
            bone_max = max(bone_max, abs((new[names[b]].translation - new[names[a]].translation).length - (old[names[b]].translation - old[names[a]].translation).length))
    require(bone_max <= 1e-06, 'Target bone length changed')
    require(keymax <= recipe['key_steel_budget_metres'] and wristmax <= recipe['key_steel_budget_metres'], 'Target key wrist/steel constraint failed')
    require(submax <= recipe['subkey_steel_budget_metres'] and
            sub_wrist_max <= recipe['subkey_steel_budget_metres'],
            'Target subkey wrist/steel constraint failed')
    require(key_orientation_displacement <= recipe['key_steel_budget_metres'],
            'Target key wrist orientation constraint failed')
    require(sub_orientation_displacement <= recipe['subkey_steel_budget_metres'],
            'Target subkey wrist orientation constraint failed')
    for time in (0, 1.75):
        old = pose_world(before, tracks, time, parents, order)
        new = pose_world(doc, actual, time, parents, order)
        require(all((np.array_equal(np.asarray(old[i]), np.asarray(new[i])) for i in old)), 'Prepared endpoint changed')
    goal_identity = hashlib.sha256(
        json.dumps(goal_frames, separators=(',', ':')).encode()
    ).hexdigest()
    proof = {
        'applied': True,
        'recipe': recipe,
        'unconstrained_same_target_wrist_sha256': goal_identity,
        'before_animation_semantics_sha256': old_signatures[recipe['clip']],
        'after_animation_semantics_sha256': new_signatures[recipe['clip']],
        'baseline_replay_error': replay,
        'original_key_union_count': len(times),
        'prepared_key_union_count': len(newgrid),
        'changed_rotation_streams': list(BONES),
        'untouched_LEFT_TRS_tracks': 231,
        'other9_clips_unchanged': True,
        'steel_reference': 'validated_combined_png_hand_local',
        'full_steel_reference_vertex_count': len(points),
        'key_wrist_max_m': wristmax,
        'subkey_wrist_max_m': sub_wrist_max,
        'key_full_steel_max_m': keymax,
        'subkey_full_steel_max_m': submax,
        'key_wrist_orientation_max_radians': key_orientation_max,
        'subkey_wrist_orientation_max_radians': sub_orientation_max,
        'key_wrist_orientation_at_steel_radius_m': key_orientation_displacement,
        'subkey_wrist_orientation_at_steel_radius_m': sub_orientation_displacement,
        'bone_world_length_max_delta_m': bone_max,
    }
    return packed, proof


def apply_prepared_character(character_id, body_path, png_path, recipe):
    validate_recipe(recipe)
    combined_doc, combined_binary = read_glb(Path(png_path))
    steel_points = combined_steel_hand_points(combined_doc, combined_binary)
    if character_id != recipe['character_id']:
        return {
            'applied': False,
            'reason': 'Constraint only targets ' + recipe['character_id'],
            'combined_rigid_steel_vertex_count': len(steel_points),
        }

    body_doc, body_binary = read_glb(Path(body_path))
    prepared = []
    inputs = (
        ('body', Path(body_path), body_doc, body_binary),
        ('combined_png', Path(png_path), combined_doc, combined_binary),
    )
    for role, path, doc, binary in inputs:
        packed, proof = apply_constraint(doc, binary, recipe, steel_points)
        proof.update(file=path.name, asset_role=role)
        prepared.append((path, encode_glb(doc, packed), proof))

    body_proof, combined_proof = [entry[2] for entry in prepared]
    require(body_proof['unconstrained_same_target_wrist_sha256'] ==
            combined_proof['unconstrained_same_target_wrist_sha256'],
            'Body/combined baseline wrist frames differ')
    require(body_proof['after_animation_semantics_sha256'] ==
            combined_proof['after_animation_semantics_sha256'],
            'Body/combined target constraint curves differ')
    # Complete validation precedes either write, so a bad combined weapon or a
    # mismatched body cannot leave a partly updated prepared pair.
    for path, data, proof in prepared:
        path.write_bytes(data)
    return {
        'applied': True,
        'prepared_space': 'after canonical normalization/finger/root grounding; before KTX/profile',
        'combined_rigid_steel_vertex_count': len(steel_points),
        'body_and_combined_share_wrist_reference': True,
        'assets': [entry[2] for entry in prepared],
    }


def bake_empty_hand(doc, binary):
    _, parents, order = hierarchy(doc)
    names = {node.get('name'): index for index, node in enumerate(doc['nodes'])}
    fore, hand, middle = [names[name] for name in ('L_Forearm', 'L_Hand', 'L_Mid1')]
    limit = math.radians(38)
    for clip in doc['animations']:
        tracks, times = animation_tracks(doc, binary, clip, require_attack_range=False)
        grid = set(times) | {frame / 60 for frame in range(math.ceil(min(times)*60), math.floor(max(times)*60)+1)}
        grid = sorted({struct.unpack('<f', struct.pack('<f', time))[0] for time in grid})
        curves = {hand: []}
        if clip['name'] in ('attack_right', 'attack_overhead'):
            curves[fore] = []
        for time in grid:
            world = pose_world(doc, tracks, time, parents, order)
            lower = world[hand].translation - world[fore].translation
            palm = world[middle].translation - world[hand].translation
            require(min(lower.length, palm.length) > 1e-5, 'Empty-hand rig has a degenerate palm or forearm')
            swing = lower.normalized().rotation_difference(palm.normalized())
            fixed = {}
            if swing.angle > limit:
                turn = Quaternion().slerp(swing.inverted(), 1-limit/swing.angle)
                fixed[hand] = (world[fore].to_quaternion().inverted() @ turn @ world[hand].to_quaternion()).normalized()
            bend_start, bend_length, outward = ((.55, .68, .10) if clip['name'] == 'attack_right'
                                                else (1.03, .62, .065))
            if fore in curves and bend_start < time < bend_start + bend_length:
                envelope = math.sin(math.pi*(time-bend_start)/bend_length)**2
                turn = lower.rotation_difference(lower + Vector((outward, 0, .025))*envelope)
                fixed[fore] = (world[parents[fore]].to_quaternion().inverted() @ turn @ world[fore].to_quaternion()).normalized()
            for index, curve in curves.items():
                if index in fixed:
                    quat = fixed[index]
                    row = (quat.x, quat.y, quat.z, quat.w)
                else:
                    row = tuple(sample_track(tracks[index, 'rotation'], time, True))
                if curve and sum(a*b for a,b in zip(row,curve[-1])) < 0:
                    row = tuple(-v for v in row)
                curve.append(row)
        binary, times_index = append_accessor(doc, binary, [(time,) for time in grid], 'SCALAR')
        for channel in clip['channels']:
            index = channel['target']['node']
            if channel['target']['path'] == 'rotation' and index in curves:
                binary, values = append_accessor(doc, binary, curves[index], 'VEC4')
                channel['sampler'] = len(clip['samplers'])
                clip['samplers'].append({'input':times_index, 'output':values, 'interpolation':'LINEAR'})
    return binary


def author_mounted_wrist(doc, binary, tip_local, clip):
    _, parents, order = hierarchy(doc)
    names = {node.get('name'): i for i, node in enumerate(doc['nodes'])}
    upper, fore, hand, knuckle = [names[name] for name in ('R_Upperarm', 'R_Forearm', 'R_Hand', 'R_Mid1')]
    tracks, original = animation_tracks(doc, binary, clip, require_attack_range=False)
    times = sorted({struct.unpack('<f', struct.pack('<f', t))[0] for t in
                    list(original) + [frame/60 for frame in range(math.ceil(min(original)*60), math.floor(max(original)*60)+1)]})
    curves = {upper: [], hand: []}
    for time in times:
        world = pose_world(doc, tracks, time, parents, order)
        shoulder, elbow, wrist, middle = [world[i].translation for i in (upper, fore, hand, knuckle)]
        lower, palm = wrist - elbow, middle - wrist
        turn = palm.rotation_difference(lower)
        weight = (1. - amount(time, (.10, .42, 1.21, 1.69))
                  if clip['name'] in ('attack_overhead', 'attack_right') else 1.)
        straightening = Quaternion().slerp(turn, weight * max(0., 1. - math.radians(55) / max(turn.angle, 1e-8)))
        tip = world[hand] @ tip_local
        rotated_tip = wrist + straightening @ (tip - wrist)
        aim = (rotated_tip - shoulder).rotation_difference(tip - shoulder)
        for index, delta in ((upper, aim), (hand, straightening)):
            if weight == 0.:
                row = tuple(sample_track(tracks[index, 'rotation'], time, True))
            else:
                quat = (world[parents[index]].to_quaternion().inverted() @ delta @ world[index].to_quaternion()).normalized()
                row = (quat.x, quat.y, quat.z, quat.w)
            if curves[index] and sum(x*y for x,y in zip(curves[index][-1], row)) < 0:
                row = tuple(-value for value in row)
            curves[index].append(row)
    binary, grid = append_accessor(doc, binary, [(t,) for t in times], 'SCALAR')
    for channel in clip['channels']:
        index = channel['target']['node']
        if channel['target']['path'] == 'rotation' and index in curves:
            binary, values = append_accessor(doc, binary, curves[index], 'VEC4')
            channel['sampler'] = len(clip['samplers'])
            clip['samplers'].append({'input':grid, 'output':values, 'interpolation':'LINEAR'})
    return binary


def prepare_character_hands(body_path, combined_path):
    mounted, mounted_binary = read_glb(combined_path)
    _, parents, order = hierarchy(mounted)
    names = {node.get('name'): i for i, node in enumerate(mounted['nodes'])}
    clip = next(a for a in mounted['animations'] if a['name'] == 'attack_left')
    tracks, _ = animation_tracks(mounted, mounted_binary, clip)
    world = pose_world(mounted, tracks, 0., parents, order)
    tip_local = world[names['R_Hand']].inverted() @ world[names['Blade_Tip']].translation
    outputs = []
    signatures = None
    for path in (body_path, combined_path):
        doc, binary = read_glb(path)
        binary = bake_empty_hand(doc, binary)
        for clip in doc['animations']:
            if clip['name'] in ('idle', 'walk', 'attack_left', 'attack_right', 'attack_overhead'):
                binary = author_mounted_wrist(doc, binary, tip_local, clip)
        current = {a['name']:animation_signature(doc, binary, a) for a in doc['animations']}
        require(signatures is None or signatures == current, 'Body and mounted weapon have different animation curves')
        signatures = current
        outputs.append((path, encode_glb(doc, binary)))
    for path, data in outputs:
        path.write_bytes(data)
    return signatures
