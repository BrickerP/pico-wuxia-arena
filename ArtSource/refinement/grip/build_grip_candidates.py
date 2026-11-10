"""Offline finger-only GLB candidates. Public assets and original Tripo files stay pinned."""
import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PUBLIC = REPO / 'ArtSource/tripo-warrior'
sys.path.insert(0, str(PUBLIC))
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from prepare_character_library import decode_animation, node_order, sampled_local
from prepare_rigged_warrior import encode_glb, read_glb
from refine_character_grips import accessor, measurements

FINGERS = ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
POSES = [('slash', t) for t in sorted({1.55, 2.117, 3.4, *[f / 30 for f in range(47, 103)]})]
POSES += [('idle', 1.0), ('walk', .6), ('turn', .6), ('hit_body', .35),
          ('hit_head', .35), ('hit_side', .35), ('fall', .6)]


def rotation_delta(angles):
    return Quaternion((1, 0, 0), math.radians(angles[0])) @ Quaternion((0, 0, 1), math.radians(angles[1]))


class Samples:
    def __init__(self, document, binary, alignment):
        self.document = document
        self.joints = document['skins'][0]['joints']
        self.names = [document['nodes'][i]['name'] for i in self.joints]
        self.parents, self.order = node_order(document)
        self.hand = next(i for i in self.joints if document['nodes'][i]['name'] == 'R_Hand')
        self.mount = Matrix(np.array(alignment['grip_local_matrix_gltf']).reshape(4, 4).T.tolist())
        self.binds = accessor(document, binary, document['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        fingers = {finger: [i for i, name in enumerate(self.names) if name.startswith('R_' + finger)] for finger in FINGERS}
        selected = [self.names.index('R_Hand')] + [i for indices in fingers.values() for i in indices]
        mesh_node = next(n for n in document['nodes'] if n.get('name') == 'TripoBody_Mesh')
        streams, seen = [], set()
        for pi in alignment['body_primitive_indices']:
            attrs = document['meshes'][mesh_node['mesh']]['primitives'][pi]['attributes']
            key = tuple(attrs[k] for k in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
            if key in seen:
                continue
            seen.add(key)
            p = accessor(document, binary, attrs['POSITION']).astype(float)
            joints = accessor(document, binary, attrs['JOINTS_0']).astype(int)
            weights = accessor(document, binary, attrs['WEIGHTS_0']).astype(float)
            weights /= weights.sum(axis=1)[:, None]
            region = sum(np.sum(weights * (joints == i), axis=1) for i in selected) > .5
            masks = {f: sum(np.sum(weights * (joints == i), axis=1) for i in indices) > .25 for f, indices in fingers.items()}
            streams.append((p[region], joints[region], weights[region], {f: m[region] for f, m in masks.items()}))
        points = np.concatenate([s[0] for s in streams])
        self.points = np.column_stack((points, np.ones(len(points))))
        self.palettes = np.concatenate([s[1] for s in streams])
        self.weights = np.concatenate([s[2] for s in streams])
        self.masks = {f: np.concatenate([s[3][f] for s in streams]) for f in FINGERS}
        self.locals = {}
        for clip in document['animations']:
            tracks, _ = decode_animation({**document, 'animations': [clip]}, binary)
            for name, time in POSES:
                if name == clip['name']:
                    self.locals[(name, time)] = [sampled_local(n, i, tracks, time) for i, n in enumerate(document['nodes'])]

    def evaluate(self, pose, deltas):
        world = {}
        for i in self.order:
            local = self.locals[pose][i]
            if i in deltas:
                position, rotation, scale = local.decompose()
                local = Matrix.LocRotScale(position, rotation @ rotation_delta(deltas[i]), scale)
            parent = self.parents.get(i)
            world[i] = world[parent] @ local if parent is not None else local
        transforms = np.array([list(world[i]) for i in self.joints]) @ self.binds
        blended = np.sum(transforms[self.palettes] * self.weights[:, :, None, None], axis=1)
        skin = np.einsum('vij,vj->vi', blended, self.points)
        grip = world[self.hand] @ self.mount
        cloud = (skin @ np.array(list(grip.inverted())).T)[:, :3]
        return measurements(cloud, self.masks), world


def admissible(new, baseline):
    return (new['max_radial_penetration_mm'] <= baseline['max_radial_penetration_mm'] + .05 and
            new['mean_radial_penetration_mm'] <= baseline['mean_radial_penetration_mm'] + .001 and
            new['vertices_deeper_than_2mm'] <= baseline['vertices_deeper_than_2mm'] and
            new['surface_samples_within_3mm'] >= baseline['surface_samples_within_3mm'] * .9 and
            all(new['finger_nearest_core_surface_mm'][f] <= baseline['finger_nearest_core_surface_mm'][f] + 1.0 for f in FINGERS))


def objective(row, deltas):
    gaps = list(row['finger_nearest_core_surface_mm'].values())
    return (row['max_radial_penetration_mm'] ** 2 + 4 * row['mean_radial_penetration_mm'] ** 2 +
            2 * max(gaps) ** 2 + .3 * sum(g * g for g in gaps) +
            .02 * sum(a * a for angles in deltas.values() for a in angles))


def optimize(samples):
    pose = ('slash', 2.117)
    baseline, _ = samples.evaluate(pose, {})
    best, deltas = baseline, {}
    bones = [i for i in samples.joints if samples.document['nodes'][i]['name'].startswith(tuple('R_' + f for f in FINGERS))]
    for step in (6.0, 3.0, 1.5):
        for _ in range(2):
            changed = False
            for bone in bones:
                for axis in range(2):
                    selected = None
                    best_score = objective(best, deltas)
                    for sign in (-1, 1):
                        trial = {k: list(v) for k, v in deltas.items()}
                        angles = trial.setdefault(bone, [0.0, 0.0])
                        angles[axis] += sign * step
                        if math.hypot(*angles) > 18:
                            continue
                        row, _ = samples.evaluate(pose, trial)
                        if admissible(row, baseline) and objective(row, trial) < best_score - 1e-6:
                            selected = row, trial
                            best_score = objective(row, trial)
                    if selected is not None:
                        best, deltas = selected
                        changed = True
            if not changed:
                break
    return {i: v for i, v in deltas.items() if any(v)}, baseline, best


def patch_rotations(document, binary, deltas):
    result, packed = copy.deepcopy(document), bytearray(binary)
    changed = 0
    for clip in result['animations']:
        for channel in clip['channels']:
            target = channel['target']
            if target['path'] != 'rotation' or target['node'] not in deltas:
                continue
            sampler = clip['samplers'][channel['sampler']]
            if sampler.get('interpolation', 'LINEAR') not in ('LINEAR', 'STEP'):
                raise ValueError('unhandled quaternion interpolation')
            rows = accessor(document, binary, sampler['output'])
            delta = rotation_delta(deltas[target['node']])
            output = []
            for x, y, z, w in rows:
                q = (Quaternion((w, x, y, z)) @ delta).normalized()
                output.append((q.x, q.y, q.z, q.w))
            packed.extend(b'\0' * (-len(packed) % 4))
            offset = len(packed)
            for row in output:
                packed.extend(struct.pack('<4f', *row))
            view = len(result['bufferViews'])
            result['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(output) * 16})
            out = len(result['accessors'])
            result['accessors'].append({'bufferView': view, 'componentType': 5126, 'count': len(output), 'type': 'VEC4'})
            sampler['output'] = out
            changed += 1
    result['buffers'][0]['byteLength'] = len(packed)
    assert result['nodes'] == document['nodes']
    assert result['skins'] == document['skins'] and result['meshes'] == document['meshes']
    assert packed[:len(binary)] == binary
    for old, new in zip(document['animations'], result['animations']):
        assert old['channels'] == new['channels']
        for a, b in zip(old['samplers'], new['samplers']):
            assert a['input'] == b['input'] and a.get('interpolation') == b.get('interpolation')
    return result, bytes(packed), changed


def build(replay=None, keys=('base', 'indigo', 'veteran')):
    (HERE / 'candidates').mkdir(parents=True, exist_ok=True)
    report = {'method': 'finger-local X/Z rotation only; posed hand-surface versus existing elliptical handle-core proxy',
              'scope': 'offline candidate, no production publication', 'poses_per_character': len(POSES), 'characters': []}
    calibration = {'application': 'postmultiply sampled local rotation q by Qx(x_degrees) @ Qz(z_degrees)',
                   'preserved': ['nodes/rest transforms', 'bone translations/lengths', 'skins/inverse binds', 'mesh/weights',
                                 'nonfinger tracks', 'all key times', 'wrist and rigid weapon trajectories'], 'characters': []}
    pinned = {c['id']: c for c in json.loads(replay.read_text())['characters']} if replay else None
    if set(keys) != {'base', 'indigo', 'veteran'}:
        report['characters'] = [r for r in json.loads((HERE / 'report.json').read_text())['characters'] if r['id'] not in keys]
        calibration['characters'] = [r for r in json.loads((HERE / 'calibration.json').read_text())['characters'] if r['id'] not in keys]
    for key in keys:
        path = PUBLIC / 'library' / (key + '.glb')
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        document, binary = read_glb(path)
        alignment = json.loads((PUBLIC / 'library' / (key + '_alignment.json')).read_text())
        samples = Samples(document, binary, alignment)
        if pinned is None:
            deltas, before, after = optimize(samples)
            left = json.loads((HERE / 'left_offsets.json').read_text())
            left_named = left['offsets_by_character'][key]
            if left_named:
                if left['validation'][key]['input_sha256'] != source_hash:
                    raise ValueError('left-finger calibration source changed: ' + key)
                deltas.update({i: left_named[n['name']] for i, n in enumerate(document['nodes']) if n.get('name') in left_named})
        else:
            entry = pinned[key]
            if entry['source_sha256'] != source_hash:
                raise ValueError('replay source hash differs from reviewed calibration: ' + key)
            named = entry['local_finger_offsets']
            deltas = {i: [named[n['name']]['x_degrees'], named[n['name']]['z_degrees']]
                      for i, n in enumerate(document['nodes']) if n.get('name') in named}
            if len(deltas) != len(named) or any(not document['nodes'][i]['name'].startswith(tuple(s + f for s in ('R_', 'L_') for f in FINGERS))
                                               or not all(math.isfinite(a) for a in v) or math.hypot(*v) > 18.00001 for i, v in deltas.items()):
                raise ValueError('replay contains an invalid finger correction')
            before, _ = samples.evaluate(('slash', 2.117), {})
            after, _ = samples.evaluate(('slash', 2.117), deltas)
        expected_left = {'base': {}, 'indigo': {'L_Ring2': [-9.0, 0.0]}, 'veteran': {'L_Pinky1': [0.0, -18.0]}}[key]
        actual_left = {document['nodes'][i]['name']: list(a) for i, a in deltas.items() if document['nodes'][i]['name'].startswith('L_')}
        if actual_left != expected_left or any(not all(math.isfinite(x) for x in a) or math.hypot(*a) > 18.00001 for a in deltas.values()):
            raise ValueError('finger correction differs from the reviewed bounds/left set')
        rows = []
        maximum_fixed_path_error = 0.0
        for pose in POSES:
            old, old_world = samples.evaluate(pose, {})
            new, new_world = samples.evaluate(pose, deltas)
            if not admissible(new, old):
                raise ValueError(f'candidate regresses sampled pose: {key}/{pose}')
            for i in samples.order:
                if not document['nodes'][i].get('name', '').startswith(tuple(side + f for side in ('R_', 'L_') for f in FINGERS)):
                    maximum_fixed_path_error = max(maximum_fixed_path_error, max(abs(old_world[i][r][c] - new_world[i][r][c]) for r in range(4) for c in range(4)))
            rows.append({'clip': pose[0], 'time_seconds': pose[1], 'before': old, 'after': new})
        output_doc, output_bin, changed = patch_rotations(document, binary, deltas)
        output = encode_glb(output_doc, output_bin)
        if pinned is not None and hashlib.sha256(output).hexdigest() != pinned[key]['candidate_sha256']:
            raise ValueError('replay differs from the reviewed candidate hash: ' + key)
        candidate = HERE / 'candidates' / (key + '.glb')
        candidate.write_bytes(output)
        # Measure the serialized float32 candidate as a consumer will read it.
        actual_doc, actual_bin = read_glb(candidate)
        actual = Samples(actual_doc, actual_bin, alignment)
        for row in rows:
            serialized, _ = actual.evaluate((row['clip'], row['time_seconds']), {})
            if not admissible(serialized, row['before']):
                raise ValueError('serialized candidate regresses a sampled pose')
            row['after'] = serialized
        after, _ = actual.evaluate(('slash', 2.117), {})
        assert maximum_fixed_path_error <= 1e-7, 'wrist or rigid weapon path changed'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source_hash, 'public source changed during generation'
        rotation_rows = {document['nodes'][i]['name']: {'x_degrees': a[0], 'z_degrees': a[1]} for i, a in sorted(deltas.items())}
        record = {'id': key, 'source': str(path.relative_to(REPO)), 'source_sha256': source_hash,
                  'candidate': str(candidate.relative_to(REPO)), 'candidate_sha256': hashlib.sha256(output).hexdigest(),
                  'joint_count': len(document['skins'][0]['joints']), 'clips': [c['name'] for c in document['animations']],
                  'modified_rotation_tracks': changed, 'local_finger_offsets': rotation_rows,
                  'contact_pose_before': before, 'contact_pose_after': after,
                  'maximum_nonfinger_world_matrix_component_error': maximum_fixed_path_error,
                  'left_hand_pose': 'finger-only correction' if any(document['nodes'][i]['name'].startswith('L_') for i in deltas) else 'unchanged', 'pose_measurements': rows}
        report['characters'].append(record)
        calibration['characters'].append({k: record[k] for k in ('id', 'source', 'source_sha256', 'candidate_sha256', 'local_finger_offsets')})
        print(json.dumps({k: record[k] for k in ('id', 'contact_pose_before', 'contact_pose_after', 'maximum_nonfinger_world_matrix_component_error')}), flush=True)
    report['characters'].sort(key=lambda r: ('base', 'indigo', 'veteran').index(r['id']))
    calibration['characters'].sort(key=lambda r: ('base', 'indigo', 'veteran').index(r['id']))
    (HERE / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if replay is None:
        (HERE / 'calibration.json').write_text(json.dumps(calibration, indent=2) + '\n')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay', type=Path)
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    build(parser.parse_args(args).replay)
