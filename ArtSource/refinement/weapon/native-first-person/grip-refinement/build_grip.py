"""Closed-only native right-grip correction on the pinned published KTX asset.

No Blender or asset rebuild. Original BIN is an exact prefix; only new closed
rotation streams and the matching finger node defaults are appended/patched.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCE = HERE.parent / 'right_hand.glb'
SOURCE_SHA = '5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d'
DAO = REPO / 'app/src/main/assets/models/dao_grip.glb'
DAO_SHA = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'
PRIOR = HERE.parents[1] / 'right-grip/candidate2_manifest.json'
sys.path.insert(0, str(HERE.parent))
import verify_hands as helpers
sys.path.insert(0, str(HERE.parents[1]))
from build_weapon import encode_glb
import numpy as np


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unit(q):
    value = np.asarray(q, dtype=float)
    length = float(np.linalg.norm(value))
    if not np.isfinite(value).all() or length <= 1e-12:
        raise ValueError('invalid quaternion')
    return value / length


def multiply(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return unit(np.concatenate((a[3] * b[:3] + b[3] * a[:3] + np.cross(a[:3], b[:3]),
                                [a[3] * b[3] - a[:3] @ b[:3]])))


def axis_rotation(axis, degrees):
    axis = np.asarray(axis, dtype=float)
    axis /= np.linalg.norm(axis)
    half = math.radians(degrees) / 2
    return np.concatenate((axis * math.sin(half), [math.cos(half)]))


def angular_error_degrees(first, second):
    first, second = unit(first), unit(second)
    if first @ second < 0:
        second = -second
    return math.degrees(4 * math.atan2(np.linalg.norm(first - second), np.linalg.norm(first + second)))


def rotation_channels(document):
    clip = next(clip for clip in document['animations'] if clip['name'] == 'grip')
    result = {}
    for channel in clip['channels']:
        target = channel['target']
        name = document['nodes'][target['node']]['name']
        if target['path'] != 'rotation' or not name.startswith('R_'):
            raise ValueError('source grip must contain only R finger rotations')
        result[name] = (target['node'], channel['sampler'])
    if len(result) != 15:
        raise ValueError('source grip requires the actual 15 finger channels')
    if len({sampler for _, sampler in result.values()}) != 15:
        raise ValueError('pinned grip requires independent source finger samplers')
    return clip, result


def camera_guides(document, binary):
    worlds = helpers.sampled_worlds(document, binary)
    names = {node.get('name'): i for i, node in enumerate(document['nodes'])}
    wrist = worlds[names['R_Hand']][:3, 3]
    index = worlds[names['R_Index1']][:3, 3]
    pinky = worlds[names['R_Pinky1']][:3, 3]
    middle = worlds[names['R_Mid3']][:3, 3]
    forward = (index + pinky + middle) / 3 - wrist
    forward /= np.linalg.norm(forward)
    radial = index - pinky
    radial /= np.linalg.norm(radial)
    palm = np.cross(radial, forward)
    palm /= np.linalg.norm(palm)
    primitive = document['meshes'][0]['primitives'][0]
    positions = helpers.skin(document, binary, primitive, worlds)
    palettes = helpers.values(document, binary, primitive['attributes']['JOINTS_0']).astype(int)
    weights = helpers.values(document, binary, primitive['attributes']['WEIGHTS_0']).astype(float)
    joint_names = [document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    selected = [i for i, name in enumerate(joint_names) if name == 'R_Hand' or any(name.startswith('R_' + digit) for digit in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky'))]
    mask = sum(np.sum(weights * (palettes == i), axis=1) for i in selected) > .5
    low, high = positions[mask].min(axis=0), positions[mask].max(axis=0)
    oblique = palm + radial * .55 + forward * .25
    oblique /= np.linalg.norm(oblique)
    return {'space': 'canonical player Dao root, metres',
            'basis': 'R palm outward = cross(Index1-Pinky1, mean(Index1,Pinky1,Mid3)-R_Hand)',
            'palm_outward_unit': palm.tolist(), 'dorsal_outward_unit': (-palm).tolist(),
            'oblique_outward_unit': oblique.tolist(),
            'bone_palm_center_metres': ((wrist + index + pinky + middle) / 4).tolist(),
            'skin_hand_finger_center_metres': ((low + high) / 2).tolist(),
            'skin_hand_finger_bounds_metres': [low.tolist(), high.tolist()]}


def directed_distal_curl(document, binary, node_name, degrees):
    worlds = helpers.sampled_worlds(document, binary)
    names = {node.get('name'): i for i, node in enumerate(document['nodes'])}
    bone = names[node_name]
    parent = names[node_name[:-1] + '2']
    pivot = worlds[bone][:3, 3]
    direction = pivot - worlds[parent][:3, 3]
    direction /= np.linalg.norm(direction)
    primitive = document['meshes'][0]['primitives'][0]
    positions = helpers.skin(document, binary, primitive, worlds)
    joints = helpers.values(document, binary, primitive['attributes']['JOINTS_0']).astype(int)
    weights = helpers.values(document, binary, primitive['attributes']['WEIGHTS_0'])
    palette = document['skins'][0]['joints'].index(bone)
    ids = np.flatnonzero((weights * (joints == palette)).sum(axis=1) > .5)
    score = (positions[ids] - pivot) @ direction
    tip = positions[ids[score >= np.percentile(score, 85)]].mean(axis=0)
    inward = np.array([-tip[0], -tip[1], 0.0])
    inward /= np.linalg.norm(inward)
    axis_world = np.cross(tip - pivot, inward)
    axis_world /= np.linalg.norm(axis_world)
    axis_local = helpers.rigid(worlds[bone])[:3, :3].T @ axis_world
    return axis_rotation(axis_local, degrees), {
        'node': node_name, 'extra_degrees': degrees, 'axis_local': axis_local.tolist(),
        'axis_canonical': axis_world.tolist(), 'pivot_canonical_metres': pivot.tolist(),
        'distal_skin_point_metres': tip.tolist(),
        'reason': 'one bounded distal flexion toward actual canonical handle radial axis after supported retreat',
    }


def build():
    if digest(SOURCE.read_bytes()) != SOURCE_SHA or digest(DAO.read_bytes()) != DAO_SHA:
        raise ValueError('published source hand/Dao identity changed')
    source, binary = helpers.read(SOURCE)
    clip, channels = rotation_channels(source)
    prior_bytes = PRIOR.read_bytes()
    prior = json.loads(prior_bytes)
    if prior['candidate_sha256'] != '1656ddc663ec6d11114c7cf4b404a926fab25001b50290a2cd38663ef1bf6064':
        raise ValueError('previous reviewed correction identity changed')
    corrected = copy.deepcopy(source)
    deltas, changes = {}, {}
    for name, contract in prior['rotation_contracts']['bones'].items():
        node, sampler_id = channels[name]
        sampler = clip['samplers'][sampler_id]
        rows = helpers.values(source, binary, sampler['output'])
        if abs(unit(rows[-1]) @ unit(contract['source_prepared_rotation_xyzw'])) < 1 - 1e-8:
            raise ValueError('native closed pose is not the reviewed correction source: ' + name)
        delta = unit(contract['q_delta_post_xyzw'])
        closed = multiply(rows[-1], delta)
        corrected['nodes'][node]['rotation'] = closed.tolist()
        deltas[name] = delta
        changes[name] = {'source_open_xyzw': rows[0].tolist(), 'source_closed_xyzw': rows[-1].tolist(),
                         'q_delta_post_xyzw': delta.tolist(),
                         'reviewed_source_prepared_q_xyzw': contract['source_prepared_rotation_xyzw'],
                         'source_closed_to_reviewed_source_error_degrees': angular_error_degrees(rows[-1], contract['source_prepared_rotation_xyzw']),
                         'reused_prior_field': 'rotation_contracts.bones.' + name + '.q_delta_post_xyzw',
                         'reason': 'same-source previously measured support/retreat correction, applied once after already baked source pose'}
    extra, curl = directed_distal_curl(corrected, binary, 'R_Pinky3', 18)
    node, sampler_id = channels['R_Pinky3']
    rows = helpers.values(source, binary, clip['samplers'][sampler_id]['output'])
    deltas['R_Pinky3'] = extra
    corrected['nodes'][node]['rotation'] = multiply(rows[-1], extra).tolist()
    changes['R_Pinky3'] = {'source_open_xyzw': rows[0].tolist(), 'source_closed_xyzw': rows[-1].tolist(),
                           'q_delta_post_xyzw': extra.tolist(), 'reason': curl}
    result = copy.deepcopy(source)
    packed = bytearray(binary)
    result_clip = next(c for c in result['animations'] if c['name'] == 'grip')
    for name, delta in deltas.items():
        node, sampler_id = channels[name]
        sampler = clip['samplers'][sampler_id]
        descriptor = source['accessors'][sampler['output']]
        if descriptor['componentType'] != 5126 or descriptor['type'] != 'VEC4' or descriptor['count'] != 2:
            raise ValueError('source grip rotation stream must be two FLOAT VEC4 keys')
        rows = helpers.values(source, binary, sampler['output']).copy()
        original_open = rows[0].tobytes()
        closed = multiply(rows[-1], delta)
        if closed @ rows[0] < 0:
            closed = -closed
        rows[-1] = closed.astype('<f4')
        if rows[0].tobytes() != original_open:
            raise AssertionError('original open key changed')
        packed.extend(b'\0' * (-len(packed) % 4))
        view = len(result['bufferViews'])
        result['bufferViews'].append({'buffer': 0, 'byteOffset': len(packed), 'byteLength': rows.nbytes})
        packed.extend(rows.tobytes())
        accessor = len(result['accessors'])
        result['accessors'].append({'bufferView': view, 'componentType': 5126, 'count': 2, 'type': 'VEC4'})
        result_clip['samplers'][sampler_id]['output'] = accessor
        result['nodes'][node]['rotation'] = rows[-1].tolist()
        changes[name]['new_closed_xyzw'] = rows[-1].tolist()
        changes[name]['new_closed_error_to_single_application_degrees'] = angular_error_degrees(rows[-1], multiply(changes[name]['source_closed_xyzw'], delta))
        changes[name]['new_closed_distance_to_double_application_degrees'] = angular_error_degrees(rows[-1], multiply(multiply(changes[name]['source_closed_xyzw'], delta), delta))
        changes[name]['incremental_applications'] = 1
        if changes[name]['new_closed_error_to_single_application_degrees'] > 1e-4 or changes[name]['new_closed_distance_to_double_application_degrees'] < .1:
            raise AssertionError('single-application quaternion proof failed')
    result['buffers'][0]['byteLength'] = len(packed)
    if bytes(packed[:len(binary)]) != binary:
        raise AssertionError('source BIN prefix changed')
    for key in ('meshes', 'skins', 'materials', 'textures', 'images', 'scenes', 'scene'):
        if result.get(key) != source.get(key):
            raise AssertionError('protected source JSON changed: ' + key)
    for name, (node, sampler_id) in channels.items():
        before = helpers.values(source, binary, clip['samplers'][sampler_id]['output'])
        after = helpers.values(result, packed, result_clip['samplers'][sampler_id]['output'])
        if before[0].tobytes() != after[0].tobytes():
            raise AssertionError('grip@0 changed: ' + name)
        if name not in deltas and before.tobytes() != after.tobytes():
            raise AssertionError('unselected finger animation changed')
        if not np.array_equal(np.asarray(result['nodes'][node]['rotation'], dtype='<f4'), after[-1]):
            raise AssertionError('default closed differs from grip@1')
    for node, (before, after) in enumerate(zip(source['nodes'], result['nodes'])):
        permitted = source['nodes'][node].get('name') in deltas
        if {k: v for k, v in before.items() if not (permitted and k == 'rotation')} != {k: v for k, v in after.items() if not (permitted and k == 'rotation')}:
            raise AssertionError('protected wrist/frame/bone node changed')
    HERE.mkdir(parents=True, exist_ok=True)
    output = HERE / 'right_hand_refined.glb'
    output.write_bytes(encode_glb(result, bytes(packed)))
    actual, actual_binary = helpers.read(output)
    if actual != result or actual_binary != bytes(packed):
        raise AssertionError('written candidate roundtrip differs')
    delta_report = {'source_sha256': SOURCE_SHA, 'prior_correction_manifest': str(PRIOR.relative_to(REPO)),
                    'prior_manifest_sha256': digest(prior_bytes), 'application': 'source closed q @ q_delta_post exactly once; do not reapply native baked offsets',
                    'consumer_contract': 'Complete candidate GLB already contains changes; asset consumers do not apply pose_delta again. Rebuild only from exact source_sha256 closed q, postmultiply each delta once.',
                    'changes': changes}
    (HERE / 'pose_delta.json').write_text(json.dumps(delta_report, indent=2) + '\n')
    report = {'source': str(SOURCE.relative_to(REPO)), 'source_sha256': SOURCE_SHA,
              'formal_dao': str(DAO.relative_to(REPO)), 'formal_dao_sha256': DAO_SHA,
              'candidate': str(output.relative_to(REPO)), 'candidate_sha256': digest(output.read_bytes()),
              'source_bin_prefix_bytes': len(binary), 'source_bin_prefix_sha256': digest(binary),
              'preserved': {'original_BIN_prefix': True, 'grip0_every_finger_byte_exact': True,
                            'default_equals_grip1': True, 'geometry_UV_skin_IBM_material_images_exact': True,
                            'wrist_grip_root_bone_lengths_and_other_node_data_exact': True},
              'modified_closed_rotation_tracks': len(deltas), 'closed_only': True,
              'modified_closed_bones': list(changes),
              'pose_delta_sha256': digest((HERE / 'pose_delta.json').read_bytes()),
              'single_application_proof': {
                  'all_nine_bones_match_once': True,
                  'max_once_error_degrees': max(c['new_closed_error_to_single_application_degrees'] for c in changes.values()),
                  'min_double_application_distance_degrees': min(c['new_closed_distance_to_double_application_degrees'] for c in changes.values()),
                  'native_baked_offsets_reapplied': False,
              },
              'camera_guides': camera_guides(actual, actual_binary),
              'status': 'initial candidate awaiting actual contact and Root visible review'}
    (HERE / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'candidate_sha256': report['candidate_sha256'], 'camera_guides': report['camera_guides']}), flush=True)


if __name__ == '__main__':
    build()
