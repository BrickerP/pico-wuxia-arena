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
import os
import struct
import subprocess
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
        rotation.normalize()
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
    if source_contract not in {'motion41', 'attack78', 'locomotion78'}:
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
        raise ValueError(source_contract + ' requires the complete same-name 78-joint rig')
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
            interpolation = 'LINEAR'
            if source_contract == 'locomotion78':
                source_track = tracks[mapping[index], path]
                interpolation = source_track[2]
                if interpolation == 'STEP':
                    # A locked source TRS remains exact after world-rest transfer.
                    # Remove only float roundoff from repeated matrix decomposition.
                    if max(abs(value - rows[0][axis]) for row in rows
                           for axis, value in enumerate(row)) > 1e-5:
                        raise ValueError('locked locomotion track changed under retarget: ' +
                                         target['nodes'][index]['name'] + '/' + path)
                    rows = [rows[0]] * len(rows)
            accessor = append_accessor(rows, 'VEC4' if path == 'rotation' else 'VEC3')
            sampler = len(animation['samplers'])
            animation['samplers'].append({'input': time_accessor, 'output': accessor, 'interpolation': interpolation})
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
              'target_rest_sha256': canonical_hash(target['nodes']),
              'target_skin_sha256': canonical_hash(target['skins']),
              'target_inverse_binds_sha256': canonical_hash(inverse_bind_values(target, target_binary)),
              'target_mesh_sha256': canonical_hash(target['meshes']),
              'interpolation_policy': 'preserved locked STEP and six moving leg LINEAR rotations'
                                      if source_contract == 'locomotion78' else 'LINEAR',
              'maximum_quaternion_step_radians': maximum_rotation_step}
    return encode_glb(result, bytes(packed)), record


ATTACK_CLIPS = {'OVERHEAD': 'attack_overhead', 'LEFT': 'attack_left', 'RIGHT': 'attack_right'}
ATTACK_PHASES = {'start': 0.0, 'preparation_end': .65, 'startup_end': .90,
                 'active_end': 1.10, 'recovery_end': 1.75, 'contact': 1.0}
MOTION_CLIPS = {'fall', 'turn', 'hit_body', 'hit_head', 'hit_side'}
LOCOMOTION_CLIPS = {'idle', 'walk'}
MOVING_LEGS = {side + bone for side in ('L_', 'R_') for bone in ('Thigh', 'Calf', 'Foot')}
HAND_POLICY = {'version': 1, 'right': 'target native grip sample, then right-only offsets once',
               'movement_left': LEFT_HAND_POSES, 'movement_left_thumb_multiplier': .55,
               'attack_left': 'authored dynamic source transferred by world-rest delta',
               'locomotion_left': 'frozen canonical source transferred by world-rest delta'}
TEXTURE_SETTINGS = {'codec': 'uastc', 'uastc_quality': 3, 'threads': 2,
                    'zstd': 18, 'mipmap_filter': 'lanczos4', 'full_mips': True,
                    'normal_mode': False, 'normalize': False, 'rdo': False,
                    'orientation': 'top-left', 'pixel_resize': False,
                    'mip_source': {'same_axis': 'ktx-cli-generate-mipmap', 'different_axes': 'explicit-axis-lanczos4-v1'},
                    'axis_mips': {'version': 1, 'precision': 'float64', 'support': 4,
                                  'centers': 'half-pixel', 'antialias': 'support-scaled-by-source/target',
                                  'sequence': 'S-then-T-recursive-unquantized-clipped-linear',
                                  'color_filter': 'IEC-sRGB-EOTF-linear-filter-OETF', 'alpha_filter': 'linear-straight',
                                  'quantization': 'clip-0-1-round-half-up-uint8', 'top': 'original-decoded-pixels'}}
ENCODER_SHA = 'abd30109cbf84859b2f34951f7967e801111abadaac588468d98ed075100ad37'
LIBKTX_SHA = 'bd26f0747b7a800384b7b3c9221dafeb3943ef565a560ab98238cade597c0947'
TEXTURE_HELPER_SHA = 'ba05ede986707b9924181e944079f7770252a96d1a40bdb3f412246c021277c4'


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


def host_python_command(config, arguments):
    environment = dict(os.environ)
    for key in ('PYTHONHOME', 'PYTHONPATH'):
        environment.pop(key, None)
    result = subprocess.run([str(HERE / config['host_python']['source']), *map(str, arguments)],
                            cwd=HERE.parent.parent, env=environment, text=True, capture_output=True)
    if result.returncode:
        raise ValueError('host texture encoding failed:\n' + result.stdout + '\n' + result.stderr)
    return result.stdout


def validate_texture_encoding(config):
    if (not isinstance(config, dict) or config.get('format') != 'KHR_texture_basisu' or
            config.get('settings') != TEXTURE_SETTINGS):
        raise ValueError('schema 3 requires fixed full-resolution UASTC3/Zstd18 runtime_texture_encoding')
    for field in ('helper', 'encoder', 'release_identity', 'host_python'):
        entry = config.get(field)
        if not isinstance(entry, dict) or not {'source', 'source_sha256'}.issubset(entry):
            raise ValueError('texture encoding requires explicit pinned ' + field)
        if hashlib.sha256((HERE / entry['source']).read_bytes()).hexdigest() != entry['source_sha256']:
            raise ValueError('texture encoding tool identity changed: ' + field)
    if (config['encoder']['source_sha256'] != ENCODER_SHA or
            config['encoder'].get('version') != 'ktx version: v4.4.2' or
            config['encoder'].get('libktx_sha256') != LIBKTX_SHA):
        raise ValueError('runtime encoding requires the verified official KTX-Software 4.4.2 binaries')
    if config['helper']['source_sha256'] != TEXTURE_HELPER_SHA:
        raise ValueError('runtime encoding requires the reviewed image-only preservation helper')
    identity = json.loads(host_python_command(config, ['-c',
        'import json,sys,PIL,numpy; print(json.dumps({"version":sys.version.split()[0],"pillow_version":PIL.__version__,"numpy_version":numpy.__version__}))']))
    if any(identity[field] != config['host_python'].get(field) for field in ('version', 'pillow_version', 'numpy_version')):
        raise ValueError('host Python/Pillow/NumPy identity differs from runtime encoding contract')


def encode_runtime_glb(source, output, config):
    """Use the pinned host encoder; geometry authors retain the original PNG GLB."""
    raw_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    print('ENCODING', source.name, '->', output.name, flush=True)
    host_python_command(config, [HERE / config['helper']['source'], '--input', source,
        '--sha256', raw_sha, '--output', output, '--encoder', HERE / config['encoder']['source']])
    report_path = output.with_suffix('.manifest.json')
    report = json.loads(report_path.read_text())
    encoded_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    if (report['input']['sha256'] != raw_sha or report['output']['sha256'] != encoded_sha or
            report['settings'] != TEXTURE_SETTINGS or report['encoder']['sha256'] != ENCODER_SHA or
            report['encoder']['libktx_sha256'] != LIBKTX_SHA or
            report['preservation']['non_image_json_semantics_identical'] is not True):
        raise ValueError('encoded GLB does not match the source, tool or preservation contract')
    before, raw = read_glb(source)
    after, encoded = read_glb(output)
    for field in ('nodes', 'skins', 'meshes', 'accessors', 'animations', 'scenes', 'scene', 'materials', 'samplers'):
        if before.get(field) != after.get(field):
            raise ValueError('runtime image encoding changed non-image GLB field: ' + field)
    before_clips = {clip['name']: animation_signature(before, raw, clip) for clip in before.get('animations', [])}
    after_clips = {clip['name']: animation_signature(after, encoded, clip) for clip in after.get('animations', [])}
    if before_clips != after_clips:
        raise ValueError('runtime image encoding changed animation geometry semantics')
    report['input']['path'] = source.name
    report['output']['path'] = output.name
    report['host_python'] = copy.deepcopy(config['host_python'])
    report['helper'] = copy.deepcopy(config['helper'])
    report['release_identity'] = copy.deepcopy(config['release_identity'])
    report['animation_semantic_signatures'] = after_clips
    print('ENCODED', output.name, raw_sha, encoded_sha, flush=True)
    return report


def attack_source_contracts(attacks):
    """Bind each source to its pinned three-attack authoring row, including its exact grid."""
    authoring = attacks['authoring_manifest']
    path = HERE / authoring['source']
    if hashlib.sha256(path.read_bytes()).hexdigest() != authoring['source_sha256']:
        raise ValueError('frozen attack input manifest hash changed')
    frozen = json.loads(path.read_text())
    if frozen['rig_sha256'] != attacks['source_sha256']:
        raise ValueError('attack raw rig differs from the frozen authoring rig')
    aliases = {'OVERHEAD': 'overhead', 'LEFT': 'slash_to_left', 'RIGHT': 'slash_to_right'}
    rows = frozen['clips']
    if len(rows) != 3 or {row['clip'] for row in rows} != set(aliases.values()):
        raise ValueError('attack authoring requires exactly its three direction-specific rows')
    result = {}
    for entry in attacks['clips']:
        row = next(row for row in rows if row['clip'] == aliases[entry['direction']])
        raw = row['raw']
        if (raw.get('right_finger_calibration_baked') is not False or
                raw['sha256'] != entry['source_sha256'] or
                (HERE.parent.parent / raw['path']).resolve() != (HERE / entry['source']).resolve()):
            raise ValueError('attack clip differs from its frozen unbaked authoring source: ' + entry['name'])
        rate, count = row['sample_rate_hz'], row['sample_count']
        if (row['source_range_seconds'] != [0, 1.75] or
                type(rate) is not int or rate <= 0 or type(count) is not int or count < 2 or
                1.75 * rate != count - 1 or row['interpolation'] != 'LINEAR' or
                row['contact_source_seconds'] != ATTACK_PHASES['contact']):
            raise ValueError('attack authoring has an inconsistent 0..1.75s time contract: ' + entry['name'])
        result[entry['name']] = row
    return result


def validate_source_clip(document, binary, rig, rig_binary, contract, clip_name=None, sample_contract=None):
    require_same_rest(document, rig)
    source_joints = joint_nodes(document)
    expected_count = {'motion41': 41, 'attack78': 78, 'locomotion78': 78}[contract]
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
    if contract in {'attack78', 'locomotion78'}:
        if contract == 'attack78':
            if sample_contract is None:
                raise ValueError('attack78 requires its pinned authoring time contract')
            rate, count = sample_contract['sample_rate_hz'], sample_contract['sample_count']
            if (sample_contract['source_range_seconds'] != [0, 1.75] or
                    type(rate) is not int or rate <= 0 or type(count) is not int or count < 2 or
                    1.75 * rate != count - 1 or sample_contract['interpolation'] != 'LINEAR'):
                raise ValueError('attack78 has an inconsistent authoring time contract')
            expected_times = [struct.unpack('<f', struct.pack('<f', index / rate))[0] for index in range(count)]
            if times != expected_times:
                raise ValueError('attack78 source key count/time grid differs from its pinned authoring time contract')
            if any(track[2] != sample_contract['interpolation'] for track in tracks.values()):
                raise ValueError('attack78 interpolation differs from its pinned authoring time contract')
        if contract == 'locomotion78':
            if clip_name not in LOCOMOTION_CLIPS:
                raise ValueError('locomotion78 requires an explicit idle/walk alias')
            count = 91 if clip_name == 'idle' else 185
            if len(times) != count or times[0] != 0 or abs(times[-1] - 1.5) > 1e-7:
                raise ValueError('locomotion78 requires its frozen 91/185-key 0..1.5s raw source')
        if any(track[0] != times for track in tracks.values()):
            raise ValueError(contract + ' joint tracks must share the source time grid')
        for name, index in source_joints.items():
            location, _, scale = local_matrix(document['nodes'][index]).decompose()
            for path, rest in (('translation', location), ('scale', scale)):
                if path == 'translation' and name in {'BoneRoot', 'Hip'}:
                    continue
                if any(abs(value - rest[axis]) > 1e-5
                       for row in tracks[index, path][1] for axis, value in enumerate(row)):
                    raise ValueError(contract + ' contains authored non-root translation/scale outside its contract: ' + name)
            if contract == 'locomotion78':
                for path in ('translation', 'rotation', 'scale'):
                    _, values, interpolation = tracks[index, path]
                    moving = clip_name == 'walk' and path == 'rotation' and name in MOVING_LEGS
                    if interpolation != ('LINEAR' if moving else 'STEP'):
                        raise ValueError('locomotion78 interpolation differs from frozen locked/leg semantics: ' + name)
                    if not moving and any(row != values[0] for row in values):
                        raise ValueError('locomotion78 locked track varies: ' + name + '/' + path)
    return tracks


def production_binding(manifest):
    from attack_grounding import GROUNDING_POLICY
    return {'schema_version': 3, 'motion_source': manifest['motion_source'],
            'locomotion_source': manifest['locomotion_source'],
            'body_coverage_calibration': manifest['body_coverage_calibration'],
            'runtime_texture_encoding': manifest['runtime_texture_encoding'],
            'player_weapon_source': manifest['player_weapon_source'],
            'attack_source': manifest['attack_source'], 'hand_policy': HAND_POLICY,
            'canonical_root_grounding': GROUNDING_POLICY,
            'weapon_source': manifest['weapon_source'],
            'characters': [{key: character.get(key) for key in
                            ('id', 'name', 'source', 'source_sha256', 'grip_source',
                             'height_metres', 'output', 'grip_frame', 'finger_rotation_offsets')}
                           for character in manifest['characters']]}


def canonical_source_evidence(sources, frozen_locomotion):
    """Check the pinned raw family's exact guard markers and locked ancestor TRS."""
    by_name = {entry['name']: (document, binary) for entry, document, binary, _, _ in sources}
    reference, reference_binary = by_name['attack_overhead']
    reference_tracks, _ = decode_animation(reference, reference_binary)
    reference_names = {node['name']: index for index, node in enumerate(reference['nodes'])}
    reports = {}
    for profile in frozen_locomotion['profiles']:
        name = profile['clip_alias']
        document, binary = by_name[name]
        tracks, times = decode_animation(document, binary)
        names = {node['name']: index for index, node in enumerate(document['nodes'])}
        markers = [min(times, key=lambda value: abs(value - marker)) for marker in (0, 1/3, 1.5)]
        for joint in joint_nodes(document):
            for path in ('translation', 'rotation', 'scale'):
                expected = reference_tracks[reference_names[joint], path][1][0]
                if any(tuple(tracks[names[joint], path][1][times.index(time)]) != tuple(expected)
                       for time in markers):
                    raise ValueError('locomotion raw guard marker differs from canonical attack: ' + name + '/' + joint)
        sample_times = sorted([*times, *((a+b)/2 for a, b in zip(times, times[1:]))])
        for joint in profile['locked_head_ancestor_chain']:
            for path in ('translation', 'rotation', 'scale'):
                key = names[joint], path
                reference_key = reference_names[joint], path
                if key not in tracks:
                    if local_matrix(document['nodes'][names[joint]]) != local_matrix(reference['nodes'][reference_names[joint]]):
                        raise ValueError('locomotion raw static ancestor differs from canonical guard: ' + joint)
                    continue
                expected = reference_tracks[reference_key][1][0]
                if any(tuple(sample_track(tracks[key], time, path == 'rotation')) != tuple(expected)
                       for time in sample_times):
                    raise ValueError('locomotion raw ancestor differs from canonical guard: ' + name + '/' + joint)
        reports[name] = {'canonical_clip': 'attack_overhead', 'canonical_source_seconds': 0,
                         'canonical_234_trs_markers_exact': True, 'marker_source_seconds': markers,
                         'locked_ancestor_local_trs_exact': True,
                         'locked_ancestor_chain': profile['locked_head_ancestor_chain'],
                         'source_key_count': len(times), 'key_and_midpoint_count': len(sample_times)}
    return reports


def validate_manifest(manifest):
    if manifest.get('schema_version') != 3:
        raise ValueError('the canonical ten-clip bank requires manifest schema_version 3; v2 is retired')
    validate_texture_encoding(manifest.get('runtime_texture_encoding'))
    player_weapon = manifest.get('player_weapon_source')
    if (not isinstance(player_weapon, dict) or set(player_weapon) != {'source', 'source_sha256'} or
            player_weapon['source_sha256'] != 'a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637'):
        raise ValueError('schema 3 requires the explicit reviewed player_weapon_source grip GLB')
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
    if 'dao_grip.glb' in outputs:
        raise ValueError('character output collides with the explicit player weapon')
    coverage_entry = manifest.get('body_coverage_calibration')
    if not isinstance(coverage_entry, dict) or set(coverage_entry) != {'source', 'source_sha256'}:
        raise ValueError('schema 3 requires an explicit frozen body coverage calibration JSON')
    coverage_path = HERE / coverage_entry['source']
    if hashlib.sha256(coverage_path.read_bytes()).hexdigest() != coverage_entry['source_sha256']:
        raise ValueError('frozen body coverage calibration hash changed')
    coverage = json.loads(coverage_path.read_text())
    if (coverage.get('schema_version') != 1 or coverage.get('space') != 'prepared actor root' or
            set(coverage.get('characters', {})) != {row['id'] for row in characters}):
        raise ValueError('body coverage calibration requires the same explicit targets and prepared actor frame')
    movement = manifest['motion_source']
    locomotion = manifest.get('locomotion_source')
    attacks = manifest.get('attack_source')
    if not attacks:
        raise ValueError('three frozen authored_raw attack descriptors are required before candidate generation')
    if (movement['contract'] != 'motion41' or attacks['contract'] != 'attack78' or
            not locomotion or locomotion['contract'] != 'locomotion78'):
        raise ValueError('motion/locomotion/attack require explicit motion41/locomotion78/attack78 contracts')
    names = [clip['name'] for clip in movement['clips']]
    if len(names) != 5 or set(names) != MOTION_CLIPS:
        raise ValueError('motion41 bank requires exactly the five reaction/turn/fall clips')
    loco_rows = locomotion['clips']
    if len(loco_rows) != 2 or {row['name'] for row in loco_rows} != LOCOMOTION_CLIPS:
        raise ValueError('locomotion78 requires exactly idle and walk')
    for row in loco_rows:
        if row.get('stage') != 'authored_raw' or row.get('right_calibration_baked') is not False:
            raise ValueError('locomotion sources must explicitly identify unbaked authored raw curves')
    loco_authoring = locomotion['authoring_manifest']
    loco_path = HERE / loco_authoring['source']
    if hashlib.sha256(loco_path.read_bytes()).hexdigest() != loco_authoring['source_sha256']:
        raise ValueError('frozen locomotion input manifest hash changed')
    frozen_locomotion = json.loads(loco_path.read_text())
    if (frozen_locomotion.get('source_assets_frozen') is not True or
            frozen_locomotion['source_rig']['sha256'] != locomotion['source_sha256'] or
            frozen_locomotion['source_rig']['skin_joint_count'] != 78):
        raise ValueError('locomotion raw rig differs from its frozen 78-joint authoring rig')
    frozen_rows = {row['clip_alias']: row for row in frozen_locomotion['profiles']}
    if set(frozen_rows) != LOCOMOTION_CLIPS or any(
            frozen_rows[row['name']]['raw']['sha256'] != row['source_sha256'] or
            frozen_rows[row['name']]['raw']['right_finger_calibration_baked'] is not False
            for row in loco_rows):
        raise ValueError('locomotion bank differs from frozen unbaked source identities')
    runtime = frozen_locomotion['runtime_contract']
    if (runtime['WALK_LOOP_START'] != 1/3 or runtime['WALK_LOOP_DURATION'] != 7/6 or
            runtime['WALK_STRIDE_METERS'] != 1.45 or runtime['physical_steps_per_loop'] != 6):
        raise ValueError('locomotion requires the six-step 1.45m canonical loop contract')
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
    attack_source_contracts(attacks)
    for character in characters:
        retired = {'finger_rotation_review', 'offhand_rotation_envelope', 'offhand_rotation_review'}
        if retired.intersection(character):
            raise ValueError('retired slash calibration cannot authorize the new hand policy')
        allowed = {'R_' + finger + str(segment) for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
                   for segment in (1, 2, 3)}
        if not set(character.get('finger_rotation_offsets', {})).issubset(allowed):
            raise ValueError('the bank permits reviewed right-finger offsets only')
    return frozen_locomotion, coverage['characters']


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
    if review.get('player_weapon') != request.get('player_weapon'):
        raise ValueError('production review differs from the encoded player weapon')


def build_library(manifest_path, candidate_dir=None):
    from attack_profiles import export_attack_profiles
    manifest = json.loads(manifest_path.read_text())
    frozen_locomotion, body_coverage = validate_manifest(manifest)
    formal = HERE / 'library'
    runtime = HERE.parent.parent / 'app/src/main/assets/models/opponents'
    destination = Path(candidate_dir).resolve() if candidate_dir is not None else formal
    if candidate_dir is not None and any(destination == path or path in destination.parents
                                         for path in (formal.resolve(), (HERE.parent.parent / 'app').resolve())):
        raise ValueError('candidate output must be separate from formal library and runtime assets')
    if candidate_dir is None and not manifest.get('production_review'):
        raise ValueError('create a private --candidate-dir and obtain Root production_review first')
    movement = manifest['motion_source']
    locomotion = manifest['locomotion_source']
    attacks = manifest['attack_source']
    attack_contracts = attack_source_contracts(attacks)
    weapon_source = manifest['weapon_source']
    texture_encoding = manifest['runtime_texture_encoding']
    player_weapon_source = manifest['player_weapon_source']
    pinned_source(weapon_source)
    player_source_path, _, _ = pinned_source(player_weapon_source)
    _, motion_rig, motion_binary = pinned_source(movement)
    _, locomotion_rig, locomotion_binary = pinned_source(locomotion)
    _, attack_rig, attack_binary = pinned_source(attacks)
    sources = []
    source_timelines = {}
    for family, rig, rig_binary in ((movement, motion_rig, motion_binary),
                                   (locomotion, locomotion_rig, locomotion_binary),
                                   (attacks, attack_rig, attack_binary)):
        for entry in family['clips']:
            _, document, binary = pinned_source(entry)
            tracks = validate_source_clip(document, binary, rig, rig_binary, family['contract'], entry['name'],
                                          attack_contracts[entry['name']] if family['contract'] == 'attack78' else None)
            if family['contract'] in {'attack78', 'locomotion78'}:
                source_timelines[entry['name']] = list(next(iter(tracks.values()))[0])
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
               'binding_sha256': canonical_hash(binding),
               'source_contract_evidence': canonical_source_evidence(sources, frozen_locomotion),
               'characters': []}
    with tempfile.TemporaryDirectory(prefix='.attack-bank-', dir=HERE) as temporary:
        stage = Path(temporary)
        output_folder = stage / 'outputs'
        output_folder.mkdir()
        files, summaries = [], []
        player_path = output_folder / 'dao_grip.glb'
        player_encoding = encode_runtime_glb(player_source_path, player_path, texture_encoding)
        player_encoding_bytes = (json.dumps(player_encoding, ensure_ascii=False, indent=2) + '\n').encode()
        player_manifest = {'schema_version': 1, 'source': player_weapon_source,
                           'runtime_texture_encoding': texture_encoding,
                           'output': {'file': player_path.name, 'bytes': player_path.stat().st_size,
                                      'sha256': hashlib.sha256(player_path.read_bytes()).hexdigest()},
                           'texture_encoding_manifest': {'file': 'dao_grip_texture_encoding.json',
                               'sha256': hashlib.sha256(player_encoding_bytes).hexdigest()}}
        player_manifest_bytes = (json.dumps(player_manifest, ensure_ascii=False, indent=2) + '\n').encode()
        request['player_weapon'] = {**player_manifest, 'manifest_sha256': hashlib.sha256(player_manifest_bytes).hexdigest()}
        files.extend((('dao_grip.glb', player_path.read_bytes()),
                      ('dao_grip_texture_encoding.json', player_encoding_bytes),
                      ('player_weapon_manifest.json', player_manifest_bytes)))
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
            prepared_png = output_folder / (stem + '_prepared_png.glb')
            record = prepare_character(source_path, character['source_sha256'], packed_clips,
                                       output_folder / (stem + '_body.glb'), prepared_png,
                                       output_folder / (stem + '_alignment.json'),
                                       height=character['height_metres'], grip_frame=character.get('grip_frame'),
                                       finger_rotation_offsets=character.get('finger_rotation_offsets'),
                                       canonical_grounding_clips=source_timelines,
                                       weapon_source=weapon_source)
            for animation, source in zip(record['animations'], retargeting):
                animation['source_glb'] = source['source']
                animation['source_sha256'] = source['source_sha256']
                animation['retargeted_clip_sha256'] = source['retargeted_clip_sha256']
            record.update(id=character['id'], name=character['name'], retargeting=retargeting,
                          grip_source=character['grip_source'], hand_policy=HAND_POLICY)
            model_path = output_folder / character['output']
            encoding = encode_runtime_glb(prepared_png, model_path, texture_encoding)
            encoding_bytes = (json.dumps(encoding, ensure_ascii=False, indent=2) + '\n').encode()
            record['prepared_png'] = record['outputs'][-1]
            record['outputs'].append({'file': character['output'], 'bytes': model_path.stat().st_size,
                                      'sha256': hashlib.sha256(model_path.read_bytes()).hexdigest()})
            record['runtime_texture_encoding'] = {'file': stem + '_texture_encoding.json',
                'sha256': hashlib.sha256(encoding_bytes).hexdigest(),
                'prepared_png_sha256': encoding['input']['sha256'],
                'encoded_sha256': encoding['output']['sha256'], 'preservation': encoding['preservation']}
            document, binary = read_glb(model_path)
            profiles = export_attack_profiles(document, binary, ATTACK_CLIPS, frozen_locomotion,
                                              body_coverage[character['id']])
            profiles.update(character_id=character['id'], model_sha256=record['outputs'][-1]['sha256'],
                            directions={entry['direction']: {key: entry[key] for key in
                                         ('incoming_guard_side', 'actor_travel_side', 'source_sha256')}
                                        for entry in attacks['clips']})
            profile_bytes = (json.dumps(profiles, ensure_ascii=False, indent=2) + '\n').encode()
            profile_name = stem + '_attack_profiles.json'
            record['attack_profiles'] = {'file': profile_name, 'sha256': hashlib.sha256(profile_bytes).hexdigest()}
            metadata = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode()
            files.extend(((stem + '_body.glb', (output_folder / (stem + '_body.glb')).read_bytes()),
                          (prepared_png.name, prepared_png.read_bytes()),
                          (character['output'], model_path.read_bytes()),
                          (stem + '_alignment.json', metadata), (profile_name, profile_bytes),
                          (stem + '_texture_encoding.json', encoding_bytes)))
            signatures = hand_track_signatures(document, binary)
            request['characters'].append({'id': character['id'], 'outputs': record['outputs'],
                                           'hand_track_signatures': signatures,
                                           'clip_semantic_signatures': {clip['name']: animation_signature(document, binary, clip)
                                                                        for clip in document['animations']},
                                           'texture_encoding_manifest_sha256': record['runtime_texture_encoding']['sha256'],
                                           'attack_profiles_sha256': record['attack_profiles']['sha256']})
            summaries.append({'id': character['id'], 'name': character['name'], 'output': character['output'],
                              'animations': [clip['name'] for clip in document['animations']],
                              'joint_count': record['joint_count'], 'outputs': record['outputs'],
                              'runtime_texture_encoding': record['runtime_texture_encoding'],
                              'attack_profiles': record['attack_profiles']})
        if candidate_dir is None:
            validate_production_review(manifest, request)
            request['status'] = 'approved_for_development_integration'
        request_bytes = (json.dumps(request, ensure_ascii=False, indent=2) + '\n').encode()
        files.extend((('characters.json', (json.dumps({'characters': summaries, 'player_weapon': request['player_weapon']}, ensure_ascii=False, indent=2) + '\n').encode()),
                      ('production_review_request.json', request_bytes)))
        destination.mkdir(parents=True, exist_ok=True)
        publication = [(destination / name, data) for name, data in files]
        if candidate_dir is None:
            runtime.mkdir(parents=True, exist_ok=True)
            publication.extend((runtime / name, data) for name, data in files
                               if name in {row['output'] for row in summaries} or name.endswith('_attack_profiles.json'))
            publication.append((runtime.parent / 'dao_grip.glb', player_path.read_bytes()))
        publish_outputs(tuple(publication))
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
