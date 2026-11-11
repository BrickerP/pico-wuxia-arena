"""Build the runtime character library from local, hash-pinned Tripo sources.

Run with Blender Python after the CLI downloads have completed. The motion
source may use a different biped rest frame. Body rotations are transferred
through world-space rest deltas, while each target keeps its own geometry,
bone lengths, weights and inverse binds. Weapon fingers retain the native grip;
empty-hand fingers are authored independently for each retargeted clip.
"""

import argparse
import copy
import hashlib
import json
import math
import struct
import tempfile
import sys
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_rigged_warrior import (
    HERE,
    accessor_bytes,
    animation_signature,
    encode_glb,
    local_matrix,
    normalization_frame,
    prepare_character,
    publish_outputs,
    read_glb,
    sample_track,
    world_matrix,
)


def pinned_source(entry):
    path = HERE / entry['source']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry['source_sha256']:
        raise ValueError('source hash differs from manifest: ' + str(path))
    return path, *read_glb(path)


def joint_nodes(document):
    if len(document.get('skins', [])) != 1:
        raise ValueError('expected exactly one character skin')
    joints = document['skins'][0]['joints']
    names = {document['nodes'][index].get('name'): index for index in joints}
    if None in names or len(names) != len(joints):
        raise ValueError('character joints require unique names')
    return names


def node_order(document):
    parents = {child: parent for parent, node in enumerate(document['nodes'])
               for child in node.get('children', [])}
    order = []
    visiting = set()
    visited = set()

    def visit(index):
        if index in visiting:
            raise ValueError('cyclic character hierarchy')
        if index in visited:
            return
        visiting.add(index)
        if index in parents:
            visit(parents[index])
        visiting.remove(index)
        visited.add(index)
        order.append(index)

    for index in range(len(document['nodes'])):
        visit(index)
    return parents, order


def decode_animation(document, binary):
    if len(document.get('animations', [])) != 1:
        raise ValueError('expected exactly one source animation')
    animation = document['animations'][0]
    tracks = {}
    timeline = set()
    for channel in animation['channels']:
        target = channel['target']
        path = target['path']
        if path not in {'translation', 'rotation', 'scale'}:
            raise ValueError('unsupported biped animation channel: ' + path)
        sampler = animation['samplers'][channel['sampler']]
        interpolation = sampler.get('interpolation', 'LINEAR')
        if interpolation not in {'LINEAR', 'STEP'}:
            raise ValueError('source interpolation requires a dedicated retarget path: ' + interpolation)
        times = [value[0] for value in struct.iter_unpack(
            '<f', accessor_bytes(document, binary, sampler['input']))]
        width = 4 if path == 'rotation' else 3
        values = list(struct.iter_unpack('<' + 'f' * width,
                                       accessor_bytes(document, binary, sampler['output'])))
        if len(values) != len(times) or any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError('source animation key times must be strictly increasing')
        if not all(math.isfinite(value) for row in values for value in row):
            raise ValueError('source animation contains non-finite values')
        key = (target['node'], path)
        if key in tracks:
            raise ValueError('duplicate source animation target')
        tracks[key] = (times, values, interpolation)
        timeline.update(times)
    if not timeline or not all(math.isfinite(time) and time >= 0 for time in timeline):
        raise ValueError('source animation has no finite nonnegative timeline')
    return tracks, sorted(timeline)


def sampled_local(node, index, tracks, time):
    location, rotation, scale = local_matrix(node).decompose()
    translation_track = tracks.get((index, 'translation'))
    rotation_track = tracks.get((index, 'rotation'))
    scale_track = tracks.get((index, 'scale'))
    if translation_track is not None:
        location = Vector(sample_track(translation_track, time, False))
    if rotation_track is not None:
        x, y, z, w = sample_track(rotation_track, time, True)
        rotation = Quaternion((w, x, y, z))
    if scale_track is not None:
        scale = Vector(sample_track(scale_track, time, False))
    return Matrix.LocRotScale(location, rotation, scale)


def require_same_rest(source, reference):
    source_joints = joint_nodes(source)
    reference_joints = joint_nodes(reference)
    if source_joints.keys() != reference_joints.keys():
        raise ValueError('motion or grip source differs from its declared rig')
    source_parents, _ = node_order(source)
    reference_parents, _ = node_order(reference)
    for name, index in source_joints.items():
        other = reference_joints[name]
        a = local_matrix(source['nodes'][index])
        b = local_matrix(reference['nodes'][other])
        difference = max(abs(a[row][column] - b[row][column])
                         for row in range(4) for column in range(4))
        parent = source_parents.get(index)
        other_parent = reference_parents.get(other)
        parent_name = source['nodes'][parent].get('name') if parent is not None else None
        other_parent_name = reference['nodes'][other_parent].get('name') if other_parent is not None else None
        if difference > 0.0001 or parent_name != other_parent_name:
            raise ValueError('motion or grip rest frame differs at ' + name)


LEFT_HAND_POSES = {
    'idle': ('relaxed', ((0.0, 0.18), (0.5, 0.22), (1.0, 0.18))),
    'walk': ('loose moving guard', ((0.0, 0.22), (0.5, 0.30), (1.0, 0.22))),
    'turn': ('loose turning guard', ((0.0, 0.20), (0.5, 0.28), (1.0, 0.20))),
    'hit_body': ('protect the body', ((0.0, 0.18), (0.22, 0.52), (0.6, 0.32), (1.0, 0.18))),
    'hit_head': ('open protective palm', ((0.0, 0.18), (0.22, 0.10), (0.55, 0.16), (1.0, 0.18))),
    'hit_side': ('soft protective curl', ((0.0, 0.18), (0.22, 0.38), (0.6, 0.26), (1.0, 0.18))),
    'fall': ('release the empty hand', ((0.0, 0.18), (0.4, 0.12), (1.0, 0.04))),
}


def sample_native_hands(target, grip, binary, time):
    """Sample the target's authored reference, keeping left/right decisions separate."""
    require_same_rest(grip, target)
    tracks, timeline = decode_animation(grip, binary)
    if (isinstance(time, bool) or not isinstance(time, (int, float)) or
            not math.isfinite(time) or not timeline[0] <= time <= timeline[-1]):
        raise ValueError('native hand reference time must be inside the finite source timeline')
    pose = {}
    for name, index in joint_nodes(grip).items():
        if name.startswith(('L_Thumb', 'L_Index', 'L_Mid', 'L_Ring', 'L_Pinky',
                            'R_Thumb', 'R_Index', 'R_Mid', 'R_Ring', 'R_Pinky')):
            pose[name] = sampled_local(grip['nodes'][index], index, tracks, time)
    if len(pose) != 30:
        raise ValueError('native grip requires all 30 target finger joints')
    return pose


def hand_pose_for_clip(target, native_hands, name, progress):
    """Author empty-hand rotations while preserving reviewed weapon-hand transforms."""
    if name not in LEFT_HAND_POSES:
        raise ValueError('clip has no authored hand pose: ' + str(name))
    if (isinstance(progress, bool) or not isinstance(progress, (int, float)) or
            not math.isfinite(progress) or not 0.0 <= progress <= 1.0):
        raise ValueError('hand pose progress must be finite and between zero and one')
    expected = {side + finger + str(segment) for side in ('L_', 'R_')
                for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
                for segment in (1, 2, 3)}
    if set(native_hands) != expected:
        raise ValueError('hand pose requires all 15 joints of each hand')
    _, keys = LEFT_HAND_POSES[name]
    weight = keys[-1][1]
    for (before, before_weight), (after, after_weight) in zip(keys, keys[1:]):
        if progress <= after:
            fraction = (progress - before) / (after - before)
            weight = before_weight + (after_weight - before_weight) * fraction
            break
    joints = joint_nodes(target)
    if not expected.issubset(joints):
        raise ValueError('target rig lacks a required finger joint')
    result = {}
    for joint_name, native in native_hands.items():
        if not all(math.isfinite(native[row][column]) for row in range(4) for column in range(4)):
            raise ValueError('native hand pose contains non-finite values: ' + joint_name)
        if abs(native.determinant()) <= 1e-12:
            raise ValueError('native hand pose is singular: ' + joint_name)
        if joint_name.startswith('R_'):
            result[joint_name] = native.copy()
            continue
        location, curled, scale = native.decompose()
        relaxed = local_matrix(target['nodes'][joints[joint_name]]).to_quaternion().normalized()
        curled.normalize()
        finger_weight = weight * (0.55 if joint_name.startswith('L_Thumb') else 1.0)
        rotation = relaxed.slerp(curled, finger_weight).normalized()
        result[joint_name] = Matrix.LocRotScale(location, rotation, scale)
    return result


def retarget_clip(source, source_binary, motion_rig, target, target_binary, native_hands, name,
                  source_contract='motion41'):
    if source_contract not in {'motion41', 'attack78'}:
        raise ValueError('unknown motion source contract: ' + str(source_contract))
    if source_contract == 'motion41' and name not in LEFT_HAND_POSES:
        raise ValueError('retarget clip has no hand-pose policy: ' + str(name))
    require_same_rest(source, motion_rig)
    source_joints = joint_nodes(source)
    target_joints = joint_nodes(target)
    if len(target_joints) != 78 or 'BoneRoot' not in target_joints:
        raise ValueError('runtime retarget requires the target 78-joint Tripo rig')
    mapping = {node: source_joints[joint_name] for joint_name, node in target_joints.items()
               if joint_name in source_joints}
    if source_contract == 'motion41':
        if len(source_joints) != 41 or 'Root' not in source_joints:
            raise ValueError('motion41 requires the original 41-joint Root rig')
        mapping[target_joints['BoneRoot']] = source_joints['Root']
    elif source_joints.keys() != target_joints.keys() or len(source_joints) != 78:
        raise ValueError('attack78 requires the complete same-name 78-joint rig')
    if len(mapping) != len(source_joints):
        raise ValueError('source joint mapping is incomplete')
    source_parents, source_order = node_order(source)
    target_parents, target_order = node_order(target)
    source_bind = {index: world_matrix(source['nodes'], index) for index in source_joints.values()}
    target_bind = {index: world_matrix(target['nodes'], index) for index in target_joints.values()}
    source_bind_rotations = {index: value.to_quaternion().normalized() for index, value in source_bind.items()}
    target_bind_rotations = {index: value.to_quaternion().normalized() for index, value in target_bind.items()}
    target_locals = {index: local_matrix(node).decompose() for index, node in enumerate(target['nodes'])}
    _, source_scale, _, _, _ = normalization_frame(motion_rig, 1.78)
    _, target_scale, _, _, _ = normalization_frame(target, 1.78)
    translation_scale = source_scale / target_scale
    tracks, timeline = decode_animation(source, source_binary)
    if timeline[-1] <= timeline[0]:
        raise ValueError('retarget clip requires a positive time span')
    curves = {index: {'translation': [], 'rotation': [], 'scale': []} for index in target_joints.values()}
    shared_joints = {
        'L_ElbowShareBone': ('L_Upperarm', 'L_Forearm'),
        'R_ElbowShareBone': ('R_Upperarm', 'R_Forearm'),
        'L_KneeShareBone': ('L_Thigh', 'L_Calf'),
        'R_KneeShareBone': ('R_Thigh', 'R_Calf'),
    }
    maximum_rotation_step = 0.0
    for time in timeline:
        if source_contract == 'motion41':
            hand_pose = hand_pose_for_clip(target, native_hands, name,
                                          (time - timeline[0]) / (timeline[-1] - timeline[0]))
        else:
            hand_pose = {joint: pose for joint, pose in native_hands.items() if joint.startswith('R_')}
        source_world = {}
        for index in source_order:
            local = sampled_local(source['nodes'][index], index, tracks, time)
            parent = source_parents.get(index)
            source_world[index] = source_world[parent] @ local if parent is not None else local
        target_world = {}
        for index in target_order:
            node = target['nodes'][index]
            parent = target_parents.get(index)
            parent_world = target_world[parent] if parent is not None else Matrix.Identity(4)
            location, rotation, scale = target_locals[index]
            location, rotation, scale = location.copy(), rotation.copy(), scale.copy()
            source_index = mapping.get(index)
            if node.get('name') in hand_pose:
                location, _, scale = native_hands[node['name']].decompose()
                _, rotation, _ = hand_pose[node['name']].decompose()
            elif source_index is not None:
                animated_rotation = source_world[source_index].to_quaternion().normalized()
                delta = animated_rotation @ source_bind_rotations[source_index].inverted()
                wanted_world_rotation = delta @ target_bind_rotations[index]
                rotation = parent_world.to_quaternion().inverted() @ wanted_world_rotation
                rotation.normalize()
                if node.get('name') in {'BoneRoot', 'Hip'}:
                    offset = (source_world[source_index].translation - source_bind[source_index].translation) * translation_scale
                    wanted_world_position = target_bind[index].translation + offset
                    location = parent_world.inverted() @ wanted_world_position
            elif source_contract == 'motion41' and node.get('name') in shared_joints:
                before, after = shared_joints[node['name']]
                a, b = source_joints[before], source_joints[after]
                delta_a = source_world[a].to_quaternion() @ source_bind_rotations[a].inverted()
                delta_b = source_world[b].to_quaternion() @ source_bind_rotations[b].inverted()
                delta_a.normalize()
                delta_b.normalize()
                wanted_world_rotation = delta_a.slerp(delta_b, 0.5) @ target_bind_rotations[index]
                rotation = parent_world.to_quaternion().inverted() @ wanted_world_rotation
                rotation.normalize()
            local = Matrix.LocRotScale(location, rotation, scale)
            target_world[index] = parent_world @ local
            if index not in curves:
                continue
            rows = curves[index]
            if rows['rotation']:
                previous = Quaternion((rows['rotation'][-1][3], *rows['rotation'][-1][:3]))
                if previous.dot(rotation) < 0:
                    rotation.negate()
                maximum_rotation_step = max(maximum_rotation_step, previous.rotation_difference(rotation).angle)
            rows['translation'].append(tuple(location))
            rows['rotation'].append((rotation.x, rotation.y, rotation.z, rotation.w))
            rows['scale'].append(tuple(scale))
    result = copy.deepcopy(target)
    packed = bytearray(target_binary)

    def append_accessor(rows, kind):
        width = len(rows[0])
        packed.extend(b'\0' * (-len(packed) % 4))
        byte_offset = len(packed)
        for row in rows:
            packed.extend(struct.pack('<' + 'f' * width, *row))
        view = len(result['bufferViews'])
        result['bufferViews'].append({'buffer': 0, 'byteOffset': byte_offset,
                                     'byteLength': len(rows) * width * 4})
        accessor = len(result['accessors'])
        result['accessors'].append({'bufferView': view, 'componentType': 5126,
                                    'count': len(rows), 'type': kind,
                                    'min': [min(row[axis] for row in rows) for axis in range(width)],
                                    'max': [max(row[axis] for row in rows) for axis in range(width)]})
        return accessor

    time_accessor = append_accessor([(value,) for value in timeline], 'SCALAR')
    animation = {'name': name, 'samplers': [], 'channels': []}
    for index, channels in curves.items():
        for path, rows in channels.items():
            accessor = append_accessor(rows, 'VEC4' if path == 'rotation' else 'VEC3')
            sampler = len(animation['samplers'])
            animation['samplers'].append({'input': time_accessor, 'output': accessor, 'interpolation': 'LINEAR'})
            animation['channels'].append({'sampler': sampler, 'target': {'node': index, 'path': path}})
    result['animations'] = [animation]
    result['buffers'][0]['byteLength'] = len(packed)
    record = {'method': 'world-space bind-rotation delta, target local bone lengths preserved',
              'source_joints': len(source_joints), 'target_joints': len(target_joints),
              'mapped_body_joints': len(mapping), 'fixed_native_right_finger_joints': 15,
              'source_contract': source_contract,
              'left_hand_policy': {'intent': LEFT_HAND_POSES[name][0], 'curl_keys': LEFT_HAND_POSES[name][1],
                                   'thumb_curl_multiplier': 0.55} if source_contract == 'motion41' else 'authored source curves',
              'sample_count': len(timeline), 'time_range_seconds': [timeline[0], timeline[-1]],
              'translation_scale': translation_scale,
              'maximum_quaternion_step_radians': maximum_rotation_step}
    return encode_glb(result, bytes(packed)), record


ATTACK_CLIPS = {'OVERHEAD': 'attack_overhead', 'LEFT': 'attack_left', 'RIGHT': 'attack_right'}
ATTACK_PHASES = {'start': 0.0, 'preparation_end': .65, 'startup_end': .90,
                 'active_end': 1.10, 'recovery_end': 1.75, 'contact': 1.0}
HAND_POLICY = {'version': 1, 'right': 'target native grip sample, then right-only offsets once',
               'movement_left': LEFT_HAND_POSES, 'movement_left_thumb_multiplier': .55,
               'attack_left': 'authored dynamic source transferred by world-rest delta'}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


def inverse_bind_values(document, binary):
    index = document['skins'][0]['inverseBindMatrices']
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    if accessor['componentType'] != 5126 or accessor['type'] != 'MAT4' or 'sparse' in accessor:
        raise ValueError('source contract requires FLOAT inverse bind matrices')
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', 64)
    values = {document['nodes'][joint]['name']: struct.unpack_from('<16f', binary, start + row * stride)
              for row, joint in enumerate(document['skins'][0]['joints'])}
    if not all(math.isfinite(value) for matrix in values.values() for value in matrix):
        raise ValueError('source inverse binds contain non-finite values')
    return values


def validate_source_clip(document, binary, rig, rig_binary, contract):
    require_same_rest(document, rig)
    source_joints = joint_nodes(document)
    expected_count = {'motion41': 41, 'attack78': 78}[contract]
    if len(source_joints) != expected_count:
        raise ValueError('source joint count differs from its explicit contract')
    source_binds, rig_binds = inverse_bind_values(document, binary), inverse_bind_values(rig, rig_binary)
    rig_joints = joint_nodes(rig)
    for name, index in source_joints.items():
        a, b = world_matrix(document['nodes'], index), world_matrix(rig['nodes'], rig_joints[name])
        if not all(math.isfinite(matrix[row][col]) for matrix in (a, b) for row in range(4) for col in range(4)):
            raise ValueError('source world rest contains non-finite values')
        if max(abs(a[row][col] - b[row][col]) for row in range(4) for col in range(4)) > .0001:
            raise ValueError('source world rest differs from its raw rig: ' + name)
        if max(abs(a - b) for a, b in zip(source_binds[name], rig_binds[name])) > .0001:
            raise ValueError('source inverse binds differ from its raw rig: ' + name)
    tracks, times = decode_animation(document, binary)
    expected = {(index, path) for index in source_joints.values() for path in ('translation', 'rotation', 'scale')}
    if set(tracks) != expected:
        raise ValueError('source requires one complete TRS track per joint')
    if contract == 'attack78':
        if len(times) != 106 or abs(times[0]) > 1e-7 or abs(times[-1] - 1.75) > 1e-6:
            raise ValueError('attack78 requires the frozen 106-key 0..1.75s raw source')
        if any(len(track[0]) != 106 or track[0] != times for track in tracks.values()):
            raise ValueError('attack78 joint tracks must share the source time grid')
        for name, index in source_joints.items():
            location, _, scale = local_matrix(document['nodes'][index]).decompose()
            for path, rest in (('translation', location), ('scale', scale)):
                if path == 'translation' and name in {'BoneRoot', 'Hip'}:
                    continue
                if any(abs(value - rest[axis]) > 1e-5
                       for row in tracks[index, path][1] for axis, value in enumerate(row)):
                    raise ValueError('attack78 contains authored non-root translation/scale outside its contract: ' + name)
    return tracks


def production_binding(manifest):
    from attack_grounding import GROUNDING_POLICY
    return {'schema_version': 2, 'motion_source': manifest['motion_source'],
            'attack_source': manifest['attack_source'], 'hand_policy': HAND_POLICY,
            'attack_root_grounding': GROUNDING_POLICY,
            'weapon_source': manifest['weapon_source'],
            'characters': [{key: character.get(key) for key in
                            ('id', 'name', 'source', 'source_sha256', 'grip_source',
                             'height_metres', 'output', 'grip_frame', 'finger_rotation_offsets')}
                           for character in manifest['characters']]}


def validate_manifest(manifest):
    if manifest.get('schema_version') != 2:
        raise ValueError('the ten-clip bank requires manifest schema_version 2')
    weapon = manifest.get('weapon_source')
    if (not isinstance(weapon, dict) or set(weapon) != {'source', 'source_sha256'} or
            not isinstance(weapon['source'], str) or not weapon['source'] or
            not isinstance(weapon['source_sha256'], str) or len(weapon['source_sha256']) != 64 or
            any(value not in '0123456789abcdef' for value in weapon['source_sha256'])):
        raise ValueError('manifest requires an explicit weapon_source path and SHA-256')
    characters = manifest['characters']
    if not characters or len({c['id'] for c in characters}) != len(characters):
        raise ValueError('manifest requires uniquely identified characters')
    outputs = [c['output'] for c in characters]
    if len(set(outputs)) != len(outputs) or any(Path(name).name != name or not name.endswith('.glb') for name in outputs):
        raise ValueError('characters require distinct local GLB output names')
    movement = manifest['motion_source']
    attacks = manifest.get('attack_source')
    if not attacks:
        raise ValueError('three frozen authored_raw attack descriptors are required before candidate generation')
    if movement['contract'] != 'motion41' or attacks['contract'] != 'attack78':
        raise ValueError('motion and attack rigs require explicit motion41/attack78 contracts')
    names = [clip['name'] for clip in movement['clips']]
    if len(names) != 7 or set(names) != set(LEFT_HAND_POSES):
        raise ValueError('movement bank requires exactly the seven authored motion/reaction clips')
    rows = attacks['clips']
    if len(rows) != 3 or {row['direction'] for row in rows} != set(ATTACK_CLIPS):
        raise ValueError('attack bank requires exactly OVERHEAD/LEFT/RIGHT sources')
    for row in rows:
        if row['name'] != ATTACK_CLIPS[row['direction']] or row['incoming_guard_side'] != row['direction']:
            raise ValueError('attack name and player incoming-guard side differ')
        if row['actor_travel_side'] not in {'DOWN', 'LEFT', 'RIGHT'}:
            raise ValueError('attack actor travel side is unspecified')
        if row.get('stage') != 'authored_raw' or row.get('right_calibration_baked') is not False:
            raise ValueError('attack sources must explicitly identify unbaked authored raw curves')
    if attacks['phase_markers'] != ATTACK_PHASES:
        raise ValueError('attack source phase markers differ from the 1.75s source contract')
    authoring = attacks['authoring_manifest']
    source = HERE / authoring['source']
    if hashlib.sha256(source.read_bytes()).hexdigest() != authoring['source_sha256']:
        raise ValueError('frozen attack input manifest hash changed')
    frozen = json.loads(source.read_text())
    if frozen['rig_sha256'] != attacks['source_sha256']:
        raise ValueError('attack raw rig differs from the frozen authoring rig')
    raw = {row['raw']['sha256'] for row in frozen['clips'] if row['raw']['right_finger_calibration_baked'] is False}
    if raw != {row['source_sha256'] for row in rows}:
        raise ValueError('attack bank differs from the frozen unbaked source identities')
    for character in characters:
        retired = {'finger_rotation_review', 'offhand_rotation_envelope', 'offhand_rotation_review'}
        if retired.intersection(character):
            raise ValueError('retired slash calibration cannot authorize the new hand policy')
        allowed = {'R_' + finger + str(segment) for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
                   for segment in (1, 2, 3)}
        if not set(character.get('finger_rotation_offsets', {})).issubset(allowed):
            raise ValueError('the bank permits reviewed right-finger offsets only')


def hand_track_signatures(document, binary):
    names = {side + finger + str(segment) for side in ('L_', 'R_')
             for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky') for segment in (1, 2, 3)}
    names.update({'L_Hand', 'R_Hand', 'L_Forearm', 'R_Forearm'})
    result = {}
    for clip in document['animations']:
        channels = [channel for channel in clip['channels']
                    if document['nodes'][channel['target']['node']].get('name') in names]
        result[clip['name']] = animation_signature(document, binary,
                                                 {'channels': channels, 'samplers': clip['samplers']})
    return result


def validate_production_review(manifest, request):
    entry = manifest.get('production_review')
    if not entry:
        raise ValueError('formal publication requires Root production_review after candidate inspection')
    path = HERE / entry['source']
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry['source_sha256']:
        raise ValueError('production review file hash changed')
    review = json.loads(path.read_text())
    if review.get('decision') != 'approved' or review.get('binding_sha256') != request['binding_sha256']:
        raise ValueError('production review does not approve the current sources and hand policy')
    if review.get('characters') != request['characters']:
        raise ValueError('production review differs from final outputs, hand tracks or attack profiles')


def build_library(manifest_path, candidate_dir=None):
    from attack_profiles import export_attack_profiles
    manifest = json.loads(manifest_path.read_text())
    validate_manifest(manifest)
    formal = HERE / 'library'
    runtime = HERE.parent.parent / 'app/src/main/assets/models/opponents'
    destination = Path(candidate_dir).resolve() if candidate_dir is not None else formal
    if candidate_dir is not None and any(destination == path or path in destination.parents
                                         for path in (formal.resolve(), (HERE.parent.parent / 'app').resolve())):
        raise ValueError('candidate output must be separate from formal library and runtime assets')
    if candidate_dir is None and not manifest.get('production_review'):
        raise ValueError('create a private --candidate-dir and obtain Root production_review first')
    movement = manifest['motion_source']
    attacks = manifest['attack_source']
    weapon_source = manifest['weapon_source']
    pinned_source(weapon_source)
    _, motion_rig, motion_binary = pinned_source(movement)
    _, attack_rig, attack_binary = pinned_source(attacks)
    sources = []
    for family, rig, rig_binary in ((movement, motion_rig, motion_binary), (attacks, attack_rig, attack_binary)):
        for entry in family['clips']:
            _, document, binary = pinned_source(entry)
            validate_source_clip(document, binary, rig, rig_binary, family['contract'])
            sources.append((entry, document, binary, rig, family['contract']))
    targets = []
    for character in manifest['characters']:
        source_path, target, binary = pinned_source(character)
        _, grip, grip_binary = pinned_source(character['grip_source'])
        native_hands = sample_native_hands(target, grip, grip_binary,
                                          character['grip_source'].get('time_seconds', 2.117))
        targets.append((character, source_path, target, binary, native_hands))
    binding = production_binding(manifest)
    request = {'schema_version': 1, 'status': 'pending_root_review', 'binding': binding,
               'binding_sha256': canonical_hash(binding), 'characters': []}
    with tempfile.TemporaryDirectory(prefix='.attack-bank-', dir=HERE) as temporary:
        stage = Path(temporary)
        output_folder = stage / 'outputs'
        output_folder.mkdir()
        files, summaries = [], []
        for character, source_path, target, target_binary, native_hands in targets:
            packed_clips, retargeting = [], []
            clip_folder = stage / character['id']
            clip_folder.mkdir()
            for entry, motion, binary, rig, contract in sources:
                output, details = retarget_clip(motion, binary, rig, target, target_binary,
                                                native_hands, entry['name'], source_contract=contract)
                path = clip_folder / (entry['name'] + '.glb')
                path.write_bytes(output)
                digest = hashlib.sha256(output).hexdigest()
                packed_clips.append((entry['name'], path, digest))
                retargeting.append({'name': entry['name'], 'source': entry['source'],
                                    'source_sha256': entry['source_sha256'], 'retargeted_clip_sha256': digest, **details})
            stem = Path(character['output']).stem
            record = prepare_character(source_path, character['source_sha256'], packed_clips,
                                       output_folder / (stem + '_body.glb'), output_folder / character['output'],
                                       output_folder / (stem + '_alignment.json'),
                                       height=character['height_metres'], grip_frame=character.get('grip_frame'),
                                       finger_rotation_offsets=character.get('finger_rotation_offsets'),
                                       attack_grounding_clips=list(ATTACK_CLIPS.values()),
                                       weapon_source=weapon_source)
            for animation, source in zip(record['animations'], retargeting):
                animation['source_glb'] = source['source']
                animation['source_sha256'] = source['source_sha256']
                animation['retargeted_clip_sha256'] = source['retargeted_clip_sha256']
            record.update(id=character['id'], name=character['name'], retargeting=retargeting,
                          grip_source=character['grip_source'], hand_policy=HAND_POLICY)
            model_path = output_folder / character['output']
            document, binary = read_glb(model_path)
            profiles = export_attack_profiles(document, binary, ATTACK_CLIPS)
            profiles.update(character_id=character['id'], model_sha256=record['outputs'][-1]['sha256'],
                            directions={entry['direction']: {key: entry[key] for key in
                                         ('incoming_guard_side', 'actor_travel_side', 'source_sha256')}
                                        for entry in attacks['clips']})
            profile_bytes = (json.dumps(profiles, ensure_ascii=False, indent=2) + '\n').encode()
            profile_name = stem + '_attack_profiles.json'
            record['attack_profiles'] = {'file': profile_name, 'sha256': hashlib.sha256(profile_bytes).hexdigest()}
            metadata = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode()
            files.extend(((stem + '_body.glb', (output_folder / (stem + '_body.glb')).read_bytes()),
                          (character['output'], model_path.read_bytes()),
                          (stem + '_alignment.json', metadata), (profile_name, profile_bytes)))
            signatures = hand_track_signatures(document, binary)
            request['characters'].append({'id': character['id'], 'outputs': record['outputs'],
                                           'hand_track_signatures': signatures,
                                           'clip_semantic_signatures': {clip['name']: animation_signature(document, binary, clip)
                                                                        for clip in document['animations']},
                                           'attack_profiles_sha256': record['attack_profiles']['sha256']})
            summaries.append({'id': character['id'], 'name': character['name'], 'output': character['output'],
                              'animations': [clip['name'] for clip in document['animations']],
                              'joint_count': record['joint_count'], 'outputs': record['outputs'],
                              'attack_profiles': record['attack_profiles']})
        if candidate_dir is None:
            validate_production_review(manifest, request)
            request['status'] = 'approved_for_development_integration'
        request_bytes = (json.dumps(request, ensure_ascii=False, indent=2) + '\n').encode()
        files.extend((('characters.json', (json.dumps({'characters': summaries}, ensure_ascii=False, indent=2) + '\n').encode()),
                      ('production_review_request.json', request_bytes)))
        destination.mkdir(parents=True, exist_ok=True)
        publish_outputs(tuple((destination / name, data) for name, data in files))
        if candidate_dir is None:
            runtime.mkdir(parents=True, exist_ok=True)
            publish_outputs(tuple((runtime / name, data) for name, data in files
                                  if name in {row['output'] for row in summaries} or name.endswith('_attack_profiles.json')))
    print(json.dumps({'output_dir': str(destination), 'status': request['status'],
                      'binding_sha256': request['binding_sha256'], 'characters': summaries}, ensure_ascii=False))
    return request


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--candidate-dir', type=Path)
    options = parser.parse_args(arguments)
    build_library(options.manifest.resolve(), options.candidate_dir)


if __name__ == '__main__':
    main()
