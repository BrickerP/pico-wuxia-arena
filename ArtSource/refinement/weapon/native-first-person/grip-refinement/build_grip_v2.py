"""Pose-only second piece: separate proximal fingers, then fit a supported tip.

Only the v2 outputs are written. The frozen v1 model and its metadata are inputs.
No Blender, geometry rebuild, atlas edit, SDK or runtime rule is involved.
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
SOURCE = HERE / 'right_hand_refined.glb'
SOURCE_SHA = '0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef'
sys.path.insert(0, str(HERE))
import build_grip as pose
import verify_grip as audit
import numpy as np


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch(source, binary, deltas):
    result = copy.deepcopy(source)
    packed = bytearray(binary)
    clip, channels = pose.rotation_channels(source)
    target = next(c for c in result['animations'] if c['name'] == 'grip')
    changes = {}
    for name, delta in deltas.items():
        node, sampler = channels[name]
        old = clip['samplers'][sampler]
        values = pose.helpers.values(source, binary, old['output']).copy()
        original_closed = values[-1].copy()
        closed = pose.multiply(original_closed, delta)
        if closed @ values[0] < 0:
            closed = -closed
        values[-1] = closed.astype('<f4')
        packed.extend(b'\0' * (-len(packed) % 4))
        view = len(result['bufferViews'])
        result['bufferViews'].append({'buffer': 0, 'byteOffset': len(packed), 'byteLength': values.nbytes})
        packed.extend(values.tobytes())
        output = len(result['accessors'])
        result['accessors'].append({'bufferView': view, 'componentType': 5126, 'count': 2, 'type': 'VEC4'})
        target['samplers'][sampler]['output'] = output
        result['nodes'][node]['rotation'] = values[-1].tolist()
        changes[name] = {'source_closed_xyzw': original_closed.tolist(),
                         'source_open_xyzw': values[0].tolist(),
                         'q_delta_post_xyzw': pose.unit(delta).tolist(),
                         'new_closed_xyzw': values[-1].tolist()}
    result['buffers'][0]['byteLength'] = len(packed)
    delta = {'source_sha256': SOURCE_SHA, 'changes': changes}
    contract = audit.verify_contract(source, binary, result, bytes(packed), delta)
    return result, bytes(packed), delta, contract


def weld_self(document, binary, points, faces):
    raw = audit.finger_self_contact(document, binary, points, faces)
    _, welded = pose.helpers.weld_positions(points, epsilon=1e-7)
    result = {}
    for name, record in raw['pairs'].items():
        pairs = [pair for pair in record['native_face_pairs']
                 if not (set(welded[faces[pair[0]]]) & set(welded[faces[pair[1]]]))]
        result[name] = {'count': len(pairs), 'native_face_pairs': pairs}
    return result


def evaluate(document, binary, geometry, pad_indices=None, time=1):
    points, faces, names, samples, table = audit.hand_samples(document, binary)
    if time != 1:
        primitive = document['meshes'][0]['primitives'][0]
        points = pose.helpers.skin(
            document, binary, primitive,
            pose.helpers.sampled_worlds(document, binary, 'grip', time),
        )
        samples = np.array([
            sum(points[index] * coefficient for index, coefficient in
                zip(row['native_vertex_ids'], row['barycentric']))
            for row in table
        ])
    core, core_faces = geometry['Handle core']
    cord, cord_faces = geometry['Grip | cord wrap']
    core_gap, _, _ = audit.nearest(samples, core[core_faces])
    inside = np.array([audit.contains(p, core[core_faces]) if gap > 1e-7 else False
                       for p, gap in zip(samples, core_gap)])
    signed = core_gap * np.where(inside, -1, 1) * 1000
    cord_gap, _, _ = audit.nearest(samples, cord[cord_faces])
    cord_gap *= 1000
    self_contact = weld_self(document, binary, points, faces)
    tip = np.array([row['dominant_joint'] == 'R_Pinky3' for row in table])
    summary = {'whole_hand': audit.depth_distribution(signed),
               'pinky': audit.summarize_group(np.array([r['dominant_joint'].startswith('R_Pinky') for r in table]), signed, cord_gap),
               'pinky3': audit.summarize_group(tip, signed, cord_gap),
               'weld_self_contact': self_contact,
               'same_source_samples': len(table)}
    if pad_indices is not None:
        selected = cord_gap[pad_indices]
        summary['stable_tip_patch'] = {'sample_indices': pad_indices.tolist(),
                                       'minimum_cord_mm': float(selected.min()),
                                       'median_cord_mm': float(np.median(selected)),
                                       'p95_cord_mm': float(np.percentile(selected, 95)),
                                       'samples_within_3mm': int((selected <= 3).sum())}
    summary['grip_time'] = time
    return summary


def protected_surface_check(source, binary, actual, actual_binary):
    h = pose.helpers
    primitive = source['meshes'][0]['primitives'][0]
    original_points = h.skin(source, binary, primitive, h.sampled_worlds(source, binary, 'grip', 1))
    actual_points = h.skin(actual, actual_binary, actual['meshes'][0]['primitives'][0],
                           h.sampled_worlds(actual, actual_binary, 'grip', 1))
    attrs = primitive['attributes']
    joints = h.values(source, binary, attrs['JOINTS_0']).astype(int)
    weights = h.values(source, binary, attrs['WEIGHTS_0'])
    names = [source['nodes'][i].get('name') for i in source['skins'][0]['joints']]
    result = {}
    for digit in ('Thumb', 'Index', 'Mid', 'Ring'):
        palette = [i for i, name in enumerate(names) if name.startswith('R_' + digit)]
        influence = sum((weights * (joints == i)).sum(axis=1) for i in palette)
        ids = np.flatnonzero(influence > .5)
        maximum = float(np.max(np.linalg.norm(original_points[ids] - actual_points[ids], axis=1)))
        result[digit] = {'native_vertex_ids': ids.tolist(), 'maximum_actual_LBS_displacement_m': maximum}
        if digit in ('Thumb', 'Index'):
            assert maximum == 0, 'accepted Thumb/Index actual surface moved'
    result['mixed_weight_note'] = 'Unchanged Ring/Mid bone curves still share original Pinky skin weights at the web; their small actual skin motion is reported, not claimed fixed.'
    return result


def fit_supported_tip(document, binary, geometry, conflict_faces):
    """Fit linked local rotations with actual core and separation clearances."""
    h = pose.helpers
    points, faces, names, samples, table = audit.hand_samples(document, binary)
    primitive = document['meshes'][0]['primitives'][0]
    attrs = primitive['attributes']
    raw = h.values(document, binary, attrs['POSITION'])
    palettes = h.values(document, binary, attrs['JOINTS_0']).astype(int)
    weights = h.values(document, binary, attrs['WEIGHTS_0']).astype(float)
    joints = document['skins'][0]['joints']
    worlds = h.sampled_worlds(document, binary, 'grip', 1)
    nodes = {node.get('name'): i for i, node in enumerate(document['nodes'])}
    parents = {child: i for i, node in enumerate(document['nodes']) for child in node.get('children', [])}
    bind = h.values(document, binary, document['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    transforms = np.array([worlds[i] for i in joints]) @ bind
    blended = np.sum(transforms[palettes] * weights[:, :, None, None], axis=1)
    normals = h.values(document, binary, attrs['NORMAL'])
    world_normals = np.array([np.linalg.inv(m[:3, :3]).T @ n for m, n in zip(blended, normals)])
    world_normals /= np.linalg.norm(world_normals, axis=1)[:, None]
    sample_normals = np.array([sum(world_normals[v] * a for v, a in zip(r['native_vertex_ids'], r['barycentric'])) for r in table])
    sample_normals /= np.linalg.norm(sample_normals, axis=1)[:, None]
    tip_ids = np.array([i for i, r in enumerate(table) if r['dominant_joint'] == 'R_Pinky3'])
    cord, cord_faces = geometry['Grip | cord wrap']
    gap, _, nearest = audit.nearest(samples[tip_ids], cord[cord_faces])
    toward = nearest - samples[tip_ids]
    toward /= np.linalg.norm(toward, axis=1)[:, None]
    facing = np.einsum('ij,ij->i', sample_normals[tip_ids], toward) > .1
    valid = np.flatnonzero(facing)
    if len(valid) < 6:
        raise ValueError('not enough actual inward-facing distal skin samples')
    ordered = valid[np.argsort(gap[valid])]
    chosen = ordered[:min(24, len(ordered))]
    pad_ids = tip_ids[chosen]
    target_motion = toward[chosen] * np.minimum(np.maximum(gap[chosen] - .0015, 0), .005)[:, None]
    bone_names = ('R_Pinky1', 'R_Pinky2', 'R_Pinky3')
    bone_nodes = [nodes[name] for name in bone_names]

    def radius(row, bone):
        pivot = worlds[bone][:3, 3]
        result = np.zeros(3)
        for vertex, coefficient in zip(row['native_vertex_ids'], row['barycentric']):
            for slot, weight in zip(palettes[vertex], weights[vertex]):
                ancestor = joints[slot]
                while ancestor != bone and ancestor in parents:
                    ancestor = parents[ancestor]
                if ancestor == bone and weight > 0:
                    contribution = (transforms[slot] @ np.r_[raw[vertex], 1])[:3]
                    result += coefficient * weight * (contribution - pivot)
        return result

    core, core_faces = geometry['Handle core']
    protected = np.array([i for i, r in enumerate(table) if r['dominant_joint'] in ('R_Pinky1', 'R_Pinky2')])
    core_gap, _, core_nearest = audit.nearest(samples[protected], core[core_faces])
    near = np.argsort(core_gap)[:min(48, len(protected))]
    core_ids = protected[near]
    outward = samples[core_ids] - core_nearest[near]
    outward /= np.linalg.norm(outward, axis=1)[:, None]
    # The first three fixed hinges over-constrained the proximal segments and
    # spent nearly the whole correction in the DIP. Use one physical 9-DOF
    # rotational Jacobian instead; only actual clearance constraints are active.
    basis = np.eye(3)

    def jacobian(row):
        return np.column_stack([
            np.cross(axis, radius(row, bone))
            for bone in bone_nodes for axis in basis
        ])

    matrices = [jacobian(table[i]) for i in pad_ids]
    matrix = np.concatenate(matrices, axis=0)
    target = target_motion.reshape(-1)
    inequalities, lower = [], []
    for i, normal, clearance in zip(core_ids, outward, core_gap[near]):
        inequalities.append(normal @ jacobian(table[i]))
        lower.append(-max(float(clearance) - .0004, 0.0))
    constraint_source = json.loads((HERE / 'constraints_v2.json').read_text())
    for witness in constraint_source['constraints']:
        vertex = witness['pinky_constraint_native_vertex']
        row = {'native_vertex_ids': [vertex], 'barycentric': [1.0]}
        normal = np.array(witness['ring_face_outward_canonical_unit'])
        face = faces[witness['ring_native_face']]
        clearance = normal @ (points[vertex] - points[face[0]])
        inequalities.append(normal @ jacobian(row))
        lower.append(.0004 - clearance)
    bounds = np.array(inequalities)
    lower = np.array(lower)
    # Distal motion costs more than a linked proximal correction. This is a
    # single active-constraint solve, not a Cartesian joint-angle scan.
    regularizer = np.diag(np.repeat([.006, .005, .010], 3))
    solve_matrix = np.concatenate([matrix, regularizer], axis=0)
    solve_target = np.r_[target, np.zeros(9)]
    rotation = np.linalg.lstsq(solve_matrix, solve_target, rcond=None)[0]
    for _ in range(6):
        active = bounds @ rotation < lower
        if not active.any():
            break
        rotation = np.linalg.lstsq(
            np.concatenate([solve_matrix, bounds[active] * 20], axis=0),
            np.r_[solve_target, lower[active] * 20], rcond=None,
        )[0]
    rotation = rotation.reshape(3, 3)
    angles = np.linalg.norm(rotation, axis=1)
    limits = np.radians([10, 23, 12])
    ratios = [limit / angle for angle, limit in zip(angles, limits) if angle > 1e-12]
    common_limit = min([1.0] + ratios)
    rotation *= common_limit
    angles = np.linalg.norm(rotation, axis=1)
    axes = [value / angle if angle > 1e-12 else np.array([1., 0., 0.])
            for value, angle in zip(rotation, angles)]
    local_axes = [h.rigid(worlds[node])[:3, :3].T @ axis
                  for node, axis in zip(bone_nodes, axes)]
    return bone_names, local_axes, angles, pad_ids, {
        'method': 'one 9DOF linked local rotational Jacobian, six bounded active-clearance updates, no parameter grid',
        'stable_pad_sample_indices': pad_ids.tolist(),
        'pad_selection': 'nearest24 actual R_Pinky3 samples with outward normal facing the actual cord',
        'protected_core_sample_indices': core_ids.tolist(),
        'protected_proximal_face_ids': conflict_faces,
        'minimum_linearized_core_and_ring_clearance_m': .0004,
        'local_hinge_axes': {name: axis.tolist() for name, axis in zip(bone_names, local_axes)},
        'canonical_hinge_axes': {name: axis.tolist() for name, axis in zip(bone_names, axes)},
        'limited_joint_angles_degrees': {name: math.degrees(value) for name, value in zip(bone_names, angles)},
        'common_limit_preserves_joint_step_ratio': common_limit,
        'joint_angle_limits_degrees': [10, 23, 12],
    }


def build():
    if sha(SOURCE.read_bytes()) != SOURCE_SHA:
        raise ValueError('frozen v1 source identity changed')
    source, binary = pose.helpers.read(SOURCE)
    source_audit = json.loads((HERE / 'verification.json').read_text())
    if source_audit['candidate_sha256'] != SOURCE_SHA:
        raise ValueError('v1 comparison audit identity differs')
    pairs = source_audit['position_weld_self_contact']['models']['candidate']['Ring_Pinky']['native_face_pairs']
    conflicts = sorted({pair[1] for pair in pairs})
    nodes = {n.get('name'): i for i, n in enumerate(source['nodes'])}
    worlds = pose.helpers.sampled_worlds(source, binary, 'grip', 1)
    canonical_axis = np.array([.938, .347, 0.0])
    canonical_axis /= np.linalg.norm(canonical_axis)
    local_axis = pose.helpers.rigid(worlds[nodes['R_Pinky1']])[:3, :3].T @ canonical_axis
    separation = {'R_Pinky1': pose.axis_rotation(local_axis, 2)}
    separated, separated_binary, _, _ = patch(source, binary, separation)
    geometry = audit.dao_geometry()
    bones, axes, angles, pad_ids, fit = fit_supported_tip(separated, separated_binary, geometry, conflicts)
    probes = []
    choices = []
    original_self = source_audit['position_weld_self_contact']['models']['candidate']
    for fraction in (0.0, .5, 1.0):
        deltas = dict(separation)
        for name, axis, angle in zip(bones, axes, angles):
            step = pose.axis_rotation(axis, math.degrees(angle) * fraction)
            deltas[name] = pose.multiply(deltas[name], step) if name in deltas else step
        deltas = {name: value for name, value in deltas.items() if np.linalg.norm(value[:3]) > 1e-10}
        document, data, delta, contract = patch(source, binary, deltas)
        summary = evaluate(document, data, geometry, pad_ids)
        summary['fraction_of_single_fit'] = fraction
        counts = summary['weld_self_contact']
        self_ok = counts['Ring_Pinky']['count'] == 0 and all(
            record['count'] <= original_self[name]['confirmed_nonadjacent_after_position_weld']
            for name, record in counts.items() if name != 'Ring_Pinky'
        )
        core_ok = summary['whole_hand']['maximum_depth_mm'] <= .25
        score = (not (self_ok and core_ok), counts['Ring_Pinky']['count'],
                 -summary['stable_tip_patch']['samples_within_3mm'],
                 summary['stable_tip_patch']['median_cord_mm'])
        summary['closed_core_and_self_guards_passed'] = self_ok and core_ok
        probes.append(summary)
        choices.append((score, document, data, delta, contract, summary))
        print('V2_FINITE_CONFIRMATION ' + json.dumps({'fraction': fraction,
              'core_max_mm': summary['whole_hand']['maximum_depth_mm'],
              'Ring_Pinky': counts['Ring_Pinky']['count'], 'pad': summary['stable_tip_patch']}), flush=True)
    _, result, result_binary, delta, contract, selected = min(choices, key=lambda item: item[0])
    if not selected['closed_core_and_self_guards_passed']:
        raise ValueError('no finite confirmation satisfies closed core/self constraints')
    path = HERE / 'right_hand_refined_v2.glb'
    path.write_bytes(pose.encode_glb(result, result_binary))
    actual, actual_binary = pose.helpers.read(path)
    if actual != result or actual_binary != result_binary:
        raise AssertionError('v2 serialized candidate differs')
    _, channels = pose.rotation_channels(source)
    protected = [name for name in channels if not name.startswith('R_Pinky')]
    result_clip, result_channels = pose.rotation_channels(actual)
    source_clip, _ = pose.rotation_channels(source)
    for name in protected:
        node, sampler = channels[name]
        actual_node, actual_sampler = result_channels[name]
        assert source['nodes'][node] == actual['nodes'][actual_node]
        assert source_clip['samplers'][sampler] == result_clip['samplers'][actual_sampler]
    boundary = {}
    for time in (0, .5):
        before = evaluate(source, binary, geometry, pad_ids, time)
        after = evaluate(actual, actual_binary, geometry, pad_ids, time)
        boundary[str(time)] = {'source_v1': before, 'candidate_v2': after}
        if time == 0:
            source_points = pose.helpers.skin(
                source, binary, source['meshes'][0]['primitives'][0],
                pose.helpers.sampled_worlds(source, binary, 'grip', 0),
            )
            actual_points = pose.helpers.skin(
                actual, actual_binary, actual['meshes'][0]['primitives'][0],
                pose.helpers.sampled_worlds(actual, actual_binary, 'grip', 0),
            )
            # The shared sampler normalizes/interpolates even at time0, so
            # the different second key can cause sub-femtometre FP rounding.
            error = float(np.max(np.abs(source_points - actual_points)))
            assert error < 1e-12, 'source open endpoint actual LBS changed'
            assert before['weld_self_contact'] == after['weld_self_contact']
            boundary[str(time)]['actual_LBS_max_coordinate_error_m'] = error
    delta.update(application='0c44 closed q @ v2 post delta once; complete asset consumers apply no extra delta',
                 separation={'bone': 'R_Pinky1', 'degrees': 2, 'canonical_axis': canonical_axis.tolist(),
                             'local_axis': local_axis.tolist()},
                 support_fit=fit, selected_fraction=selected['fraction_of_single_fit'])
    (HERE / 'pose_delta_v2.json').write_text(json.dumps(delta, indent=2) + '\n')
    manifest = {'source': str(SOURCE.relative_to(REPO)), 'source_sha256': SOURCE_SHA,
                'candidate': str(path.relative_to(REPO)), 'candidate_sha256': sha(path.read_bytes()),
                'geometry_or_weights_changed': False, 'open0_state_byte_exact': True,
                'accepted_v1_Thumb1_2_3_locked': True, 'source_contract': contract,
                'separation_and_one_fit_probes': probes, 'selected_probe': selected,
                'actual_serialized_open_mid_comparison': boundary,
                'actual_closed_protected_surface_check': protected_surface_check(source, binary, actual, actual_binary),
                'protected_non_Pinky_closed_channels_exact': protected,
                'producer': str(Path(__file__).resolve().relative_to(REPO)),
                'producer_sha256': sha(Path(__file__).read_bytes()),
                'pose_delta_sha256': sha((HERE / 'pose_delta_v2.json').read_bytes()),
                'rebuild_command': 'python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/build_grip_v2.py',
                'self_checks': ['source_SHA_pin', 'source_BIN_prefix_and_nonpose_JSON_exact',
                                'all15_open0_rows_exact', 'all_non_Pinky_channels_exact',
                                'serialized_GLB_roundtrip', '7167_same_samples_closed_core_and_welded_self',
                                'actual_Thumb_and_Index_dominant_skin_vertex_positions_exact',
                                'actual_serialized_open_mid_LBS_and_contact_comparison'],
                'camera_guides': pose.camera_guides(actual, actual_binary),
                'limitations': [
                    'Closed contact and sampled noncoplanar self-intersections are numerical evidence; actual visual review remains required.',
                    'The unchanged source open pose and interpolated midpoint have existing DAO intrusion; closed clearance does not certify the whole animation.',
                    'Contact is measured at 7167 stable vertices/centroids/edge midpoints, not a continuous collision-free surface proof.',
                ],
                'status': '实现阶段结束，等待 Root review；independent audit and actual views pending'}
    (HERE / 'manifest_v2.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('V2_CANDIDATE_READY ' + manifest['candidate_sha256'], flush=True)


if __name__ == '__main__':
    build()
