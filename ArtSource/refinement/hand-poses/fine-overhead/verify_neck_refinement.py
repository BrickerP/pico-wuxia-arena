"""Verify the two-neck patch without rebuilding or changing frozen inputs.

Run with host Python and --host-only for byte/FK checks. Run through the
shared Blender wrapper without that flag for the additional fresh BVH scan.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_neck_refinement as build

NECK_NAMES = ('NeckTwist01', 'NeckTwist02')
FILES = ('fine_overhead_raw.glb', 'fine_overhead_body.glb', 'fine_overhead_preview.glb')
FROZEN_METADATA_SHA256 = '1d395763496e4d9be2c36521575eb1eea2e5ccb906867212dbeba1b5656d8241'
GAIN = .20
FIRST_NECK_SHARE = .45


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smooth(value):
    value = min(1., max(0., value))
    return min(1., max(0., value**3 * (10. + value * (-15. + 6. * value))))


def rotation(matrix):
    u, _, vh = np.linalg.svd(np.asarray(matrix)[:3, :3])
    result = u @ vh
    require(np.linalg.det(result) > 0., 'reflected skeletal rotation')
    return result


def rotation_angle(a, b):
    relative = rotation(a).T @ rotation(b)
    sine = np.linalg.norm((relative - relative.T)[[2, 0, 1], [1, 2, 0]]) / 2.
    cosine = np.clip((np.trace(relative) - 1.) / 2., -1., 1.)
    return math.degrees(math.atan2(float(sine), float(cosine)))


def axis_rotation(axis, angle):
    x, y, z = np.asarray(axis, dtype=float)
    cross = np.array(((0., -z, y), (z, 0., -x), (-y, x, 0.)))
    return np.eye(3) + math.sin(angle) * cross + (1. - math.cos(angle)) * (cross @ cross)


def row_intervals(doc, accessor_index):
    item = doc['accessors'][accessor_index]
    view = doc['bufferViews'][item['bufferView']]
    require('sparse' not in item, 'sparse animation accessor is unsupported')
    require(item['componentType'] == 5126, 'animation must retain FLOAT payloads')
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[item['type']] * 4
    stride = view.get('byteStride', width)
    require(stride >= width, 'animation accessor stride is too short')
    start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    return [(start + i * stride, start + i * stride + width) for i in range(item['count'])]


def row_bytes(doc, binary, accessor_index):
    return [bytes(binary[a:b]) for a, b in row_intervals(doc, accessor_index)]


def compare_outside_intervals(old, new, intervals):
    require(len(old) == len(new), 'GLB file size changed')
    cursor = 0
    for start, end in sorted(intervals):
        require(0 <= start < end <= len(old), 'neck output interval exceeds GLB')
        require(start >= cursor, 'neck output accessors overlap')
        require(old[cursor:start] == new[cursor:start], f'non-neck GLB bytes changed near {cursor}')
        cursor = end
    require(old[cursor:] == new[cursor:], 'non-neck GLB tail changed')


def descendants(doc, index):
    result = {index}
    pending = [index]
    while pending:
        for child in doc['nodes'][pending.pop()].get('children', []):
            require(child not in result, 'cycle or multiply-parented neck subtree')
            result.add(child)
            pending.append(child)
    return result


def extent(values, times):
    values = np.asarray(values, dtype=float)
    require(np.isfinite(values).all(), 'non-finite measured value')
    low, high = int(np.argmin(values)), int(np.argmax(values))
    return {'minimum': float(values[low]), 'minimum_seconds': float(times[low]),
            'maximum': float(values[high]), 'maximum_seconds': float(times[high])}


def angular_motion_stats(matrices, times):
    """Differentiate shortest rotation vectors in a fixed reference frame."""
    times = np.asarray(times, dtype=float)
    require(len(matrices) == len(times) and len(times) >= 3, 'angular dynamics needs at least three poses')
    intervals = np.diff(times)
    require(np.isfinite(times).all() and (intervals > 0.).all(), 'invalid angular dynamics timeline')
    rotations = [rotation(matrix) for matrix in matrices]
    vectors = []
    for before, after in zip(rotations, rotations[1:]):
        q = build.matrix_quaternion(after @ before.T)
        if q[3] < 0.:
            q = -q
        sine = float(np.linalg.norm(q[:3]))
        angle = 2. * math.atan2(sine, float(q[3]))
        vectors.append(np.degrees(q[:3] * (angle / sine if sine > 1e-12 else 2.)))
    vectors = np.asarray(vectors)
    velocities = vectors / intervals[:, None]
    velocity_times = (times[:-1] + times[1:]) / 2.
    accelerations = np.diff(velocities, axis=0) / np.diff(velocity_times)[:, None]
    return {
        'adjacent_angle_degrees': extent(np.linalg.norm(vectors, axis=1), times[1:]),
        'angular_speed_degrees_per_second': extent(np.linalg.norm(velocities, axis=1), velocity_times),
        'angular_acceleration_degrees_per_second_squared': extent(np.linalg.norm(accelerations, axis=1), times[1:-1]),
        'derivative_definition': 'Shortest SO(3) spatial rotation vectors per interval; vector angular acceleration from adjacent interval velocities. Local uses parent axes, world uses prepared scene axes. Acceleration is discrete, not the instantaneous derivative at LINEAR interpolation knots.',
    }


def angular_motion_comparison(old_local, new_local, old_world, new_world, times):
    return {bone: {
        'local': {'parent_v7': angular_motion_stats(old_local[bone], times), 'candidate': angular_motion_stats(new_local[bone], times)},
        'world_prepared': {'parent_v7': angular_motion_stats(old_world[bone], times), 'candidate': angular_motion_stats(new_world[bone], times)},
    } for bone in (*NECK_NAMES, 'Head')}


def normalized_worlds(world, normalization):
    return np.asarray(world) if normalization is None else normalization @ np.asarray(world)


def frozen_metadata():
    path = build.PARENT / 'fine_overhead_metadata.json'
    require(digest(path) == FROZEN_METADATA_SHA256, 'frozen v7 metadata identity changed')
    metadata = json.loads(path.read_text())
    identities = {metadata['raw_output']['file']: metadata['raw_output']['sha256']}
    identities.update({row['file']: row['sha256'] for row in metadata['preview_outputs']})
    for name in identities:
        require(digest(build.PARENT / name) == identities[name], f'frozen v7 source changed: {name}')
    return metadata


def canonical_neck_rows(metadata):
    relative = 'ArtSource/refinement/hand-poses/attack-keyposes/stage5/candidate/overhead_aligned_raw.glb'
    path = build.REPO / relative
    require(digest(path) == metadata['source_pins'][relative], 'original canonical guard changed')
    doc, binary, _, _ = build.read_glb(path)
    names = {node.get('name'): i for i, node in enumerate(doc['nodes'])}
    result = {}
    for channel in doc['animations'][0]['channels']:
        target = channel['target']
        for name in NECK_NAMES:
            if target == {'node': names[name], 'path': 'rotation'}:
                sampler = doc['animations'][0]['samplers'][channel['sampler']]
                require(build.accessor(doc, binary, sampler['input'])[0, 0] == 0., 'canonical guard does not begin at source zero')
                result[name] = row_bytes(doc, binary, sampler['output'])[0]
    require(set(result) == set(NECK_NAMES), 'canonical guard lacks neck channels')
    return result


def verify_pair(name, normalization, guard_rows):
    old_doc, old_binary, old_start, old_encoded = build.read_glb(build.PARENT / name)
    new_doc, new_binary, new_start, new_encoded = build.read_glb(build.OUTPUT / name)
    require(old_doc == new_doc, f'{name}: GLB JSON changed')
    require(old_start == new_start, f'{name}: BIN layout changed')
    require(len(old_binary) == len(new_binary), f'{name}: BIN length changed')
    old_tracks, new_tracks = build.tracks(old_doc, old_binary), build.tracks(new_doc, new_binary)
    require(old_tracks.keys() == new_tracks.keys(), f'{name}: channel targets changed')
    require(len(new_tracks) == 234, f'{name}: expected all 234 TRS channels')
    names = {node.get('name'): i for i, node in enumerate(new_doc['nodes'])}
    neck_keys = {(names[bone], 'rotation') for bone in NECK_NAMES}
    times = next(iter(old_tracks.values()))[0]
    grid = np.arange(211, dtype=float) / 120.
    require(np.array_equal(times, grid.astype(np.float32).astype(times.dtype)), f'{name}: key grid changed')
    allowed = []
    for key, old_track in old_tracks.items():
        new_track = new_tracks[key]
        require(np.array_equal(old_track[0], new_track[0]), f'{name}: input times changed: {key}')
        require(old_track[2] == new_track[2] == 'LINEAR', f'{name}: interpolation changed: {key}')
        require(old_track[3] == new_track[3], f'{name}: output accessor changed: {key}')
        before = row_bytes(old_doc, old_binary, old_track[3])
        after = row_bytes(new_doc, new_binary, new_track[3])
        if key in neck_keys:
            require(before[0] == after[0] and before[-1] == after[-1], f'{name}: guard neck endpoint bytes changed')
            bone = new_doc['nodes'][key[0]]['name']
            require(after[0] == after[-1] == guard_rows[bone], f'{name}: endpoint differs from original canonical guard: {bone}')
            require(before != after, f'{name}: neck rotation was not refined: {key}')
            allowed.extend((old_start + a, old_start + b) for a, b in row_intervals(old_doc, old_track[3]))
        else:
            require(before == after, f'{name}: non-neck float32 payload changed: {key}')
    compare_outside_intervals(old_encoded, new_encoded, allowed)
    subtree = descendants(new_doc, names['NeckTwist01'])
    outside = [i for i in range(len(new_doc['nodes'])) if i not in subtree]
    parents = {child: parent for parent, node in enumerate(new_doc['nodes']) for child in node.get('children', [])}
    probes = sorted(set(times.tolist() + ((times[:-1] + times[1:]) / 2.).tolist()))
    bone_error = 0.
    old_neck, new_neck, new_head = {bone: [] for bone in (*NECK_NAMES, 'Head')}, {bone: [] for bone in (*NECK_NAMES, 'Head')}, []
    old_world_neck, new_world_neck = {bone: [] for bone in old_neck}, {bone: [] for bone in old_neck}
    for time in probes:
        old_local, old_world = build.pose(old_doc, old_tracks, time)
        new_local, new_world = build.pose(new_doc, new_tracks, time)
        require(np.array_equal(old_world[outside], new_world[outside]), f'{name}: non-neck world matrices changed at {time}')
        require(np.array_equal(old_local[names['Head']], new_local[names['Head']]), f'{name}: Head local matrix changed at {time}')
        old_prepared, new_prepared = normalized_worlds(old_world, normalization), normalized_worlds(new_world, normalization)
        for index in new_doc['skins'][0]['joints']:
            if index not in parents:
                continue
            parent = parents[index]
            old_length = np.linalg.norm(old_prepared[index, :3, 3] - old_prepared[parent, :3, 3])
            new_length = np.linalg.norm(new_prepared[index, :3, 3] - new_prepared[parent, :3, 3])
            bone_error = max(bone_error, abs(float(new_length - old_length)))
    for time in times:
        before, before_world = build.pose(old_doc, old_tracks, float(time))
        after, after_world = build.pose(new_doc, new_tracks, float(time))
        before_world, after_world = normalized_worlds(before_world, normalization), normalized_worlds(after_world, normalization)
        for bone in old_neck:
            old_neck[bone].append(before[names[bone]])
            new_neck[bone].append(after[names[bone]])
            old_world_neck[bone].append(before_world[names[bone]])
            new_world_neck[bone].append(after_world[names[bone]])
        new_head.append(after_world[names['Head']])
    require(bone_error < 2e-6, f'{name}: bone length changed {bone_error} metres')
    require(new_doc['nodes'][names['NeckTwist01']]['children'] == old_doc['nodes'][names['NeckTwist01']]['children'], 'neck hierarchy changed')
    guard_local, _ = build.pose(old_doc, old_tracks, 0.)
    local_stats = {}
    for bone in old_neck:
        guard = guard_local[names[bone]]
        prior, current = old_neck[bone], new_neck[bone]
        local_stats[bone] = {
            'old_from_guard_degrees': extent([rotation_angle(guard, value) for value in prior], times),
            'new_from_guard_degrees': extent([rotation_angle(guard, value) for value in current], times),
            'old_adjacent_step_degrees': extent([rotation_angle(a, b) for a, b in zip(prior, prior[1:])], times[1:]),
            'new_adjacent_step_degrees': extent([rotation_angle(a, b) for a, b in zip(current, current[1:])], times[1:]),
        }
    return {'file': name, 'parent_sha256': digest(build.PARENT / name), 'sha256': digest(build.OUTPUT / name),
            'json_header_rest_mesh_skin_materials_and_all_other_bytes_identical': True,
            'non_neck_channel_payloads_float32_identical': True, 'head_local_payload_identical': True,
            'neck_guard_endpoint_rows_identical': True, 'neck_descendant_nodes': [new_doc['nodes'][i].get('name', str(i)) for i in sorted(subtree)],
            'world_keys_and_midpoints_sample_count': len(probes), 'non_neck_subtree_world_matrices_bit_identical': True,
            'maximum_bone_length_change_from_parent_metres': bone_error, 'local_rotation_statistics': local_stats,
            'angular_dynamics_all_211_keys': angular_motion_comparison(old_neck, new_neck, old_world_neck, new_world_neck, times),
            'new_head_world_adjacent_step_degrees': extent([rotation_angle(a, b) for a, b in zip(new_head, new_head[1:])], times[1:])}, (old_doc, old_tracks, new_doc, new_tracks, times)


def verify_head_plan(data, normalization):
    old_doc, old_tracks, new_doc, new_tracks, times = data
    before = build.head_metrics(old_doc, old_tracks, times, normalization=normalization)
    after = build.head_metrics(new_doc, new_tracks, times, normalization=normalization)
    require(len(before) == len(after) == 211, 'Head metrics must cover all 211 keys')
    metrics = ('guard_calibrated_pitch_degrees', 'yaw_degrees', 'anatomical_roll_degrees', 'ear_line_elevation_degrees')
    summary = {key: {'old': extent([row[key] for row in before], times), 'new': extent([row[key] for row in after], times)} for key in metrics}
    errors, yaw_errors, roll_errors, extensions, share_errors = [], [], [], [], {bone: 0. for bone in NECK_NAMES}
    names = {node.get('name'): i for i, node in enumerate(old_doc['nodes'])}
    for k, (old, new) in enumerate(zip(before, after)):
        time = k / 120.
        amount = smooth((time-build.ENTRY_START)/(build.ENTRY_END-build.ENTRY_START)) * (1.-smooth((time-build.EXIT_START)/(build.EXIT_END-build.EXIT_START)))
        pitch = old['guard_calibrated_pitch_degrees']
        expected = pitch * (1. - (1. - GAIN) * amount)
        errors.append(abs(new['guard_calibrated_pitch_degrees'] - expected))
        extensions.append(new['guard_calibrated_pitch_degrees'] - pitch)
        yaw_errors.append(abs((new['yaw_degrees'] - old['yaw_degrees'] + 180.) % 360. - 180.))
        roll_errors.append(abs((new['anatomical_roll_degrees'] - old['anatomical_roll_degrees'] + 180.) % 360. - 180.))
        yaw = math.radians(old['yaw_degrees'])
        right = np.array((math.cos(yaw), 0., -math.sin(yaw)))
        theta = math.radians((1. - GAIN) * pitch * amount)
        _, old_world = build.pose(old_doc, old_tracks, float(times[k]))
        _, new_world = build.pose(new_doc, new_tracks, float(times[k]))
        old_world, new_world = normalized_worlds(old_world, normalization), normalized_worlds(new_world, normalization)
        for bone, fraction in zip(NECK_NAMES, (FIRST_NECK_SHARE, 1.)):
            wanted = axis_rotation(right, theta * fraction) @ rotation(old_world[names[bone]])
            error = rotation_angle(wanted, new_world[names[bone]])
            share_errors[bone] = max(share_errors[bone], error)
    require(max(errors) < 1e-4, f'Head pitch plan error {max(errors)} degrees')
    require(max(yaw_errors) < 1e-4 and max(roll_errors) < 1e-4, 'anatomical yaw or roll changed')
    require(max(share_errors.values()) < 1e-4, f'45/55 neck distribution changed: {share_errors}')
    summary.update({'pitch_gain': GAIN, 'neck_increment_shares': [.45, .55],
                    'maximum_pitch_target_error_degrees': max(errors), 'maximum_yaw_change_degrees': max(yaw_errors),
                    'maximum_anatomical_roll_change_degrees': max(roll_errors), 'neck_world_target_error_degrees': share_errors,
                    'total_head_extension_degrees': extent(extensions, times),
                    'literal_ear_elevation_maximum_change_degrees': max(abs(a['ear_line_elevation_degrees'] - b['ear_line_elevation_degrees']) for a, b in zip(before, after)),
                    'frame': 'prepared canonical guard Head defines forward +Z, right +X and up +Y; positive pitch looks up',
                    'samples': [{'source_seconds': float(times[k]), 'old': before[k], 'new': after[k]} for k in (0, 19, 34, 78, 108, 109, 118, 120, 132, 140, 156, 180, 210)]})
    return summary


def body_geometry(metadata, preview, helper):
    source = build.REPO / 'ArtSource/tripo-warrior' / metadata['body_source']['source']
    require(digest(source) == metadata['body_source']['source_sha256'], 'body geometry source changed')
    doc, binary, _, _ = build.read_glb(source)
    mesh_nodes = [node for node in doc['nodes'] if 'mesh' in node]
    require(len(mesh_nodes) == 1, 'expected the single frozen body mesh')
    mesh = doc['meshes'][mesh_nodes[0]['mesh']]
    positions, palettes, weights, faces, pools, offset = [], [], [], [], {}, 0
    for primitive in mesh['primitives']:
        attrs = primitive['attributes']
        identity = tuple(attrs[key] for key in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
        if identity not in pools:
            points = helper.accessor(doc, binary, attrs['POSITION']).astype(float)
            pools[identity] = offset
            positions.append(points)
            palettes.append(helper.accessor(doc, binary, attrs['JOINTS_0']).astype(int))
            weights.append(helper.accessor(doc, binary, attrs['WEIGHTS_0']).astype(float))
            offset += len(points)
        faces.append(helper.accessor(doc, binary, primitive['indices']).reshape(-1, 3).astype(int) + pools[identity])
    names = {node.get('name'): i for i, node in enumerate(preview['nodes'])}
    joints = [names[doc['nodes'][i]['name']] for i in doc['skins'][0]['joints']]
    weights = np.concatenate(weights)
    require(np.isfinite(weights).all() and (weights.sum(axis=1) > 0.).all(), 'invalid body skin weights')
    weights /= weights.sum(axis=1)[:, None]
    return {'positions': np.column_stack((np.concatenate(positions), np.ones(offset))), 'palettes': np.concatenate(palettes),
            'weights': weights, 'faces': np.concatenate(faces), 'joints': joints,
            'inverse_bind': helper.accessor(doc, binary, doc['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1),
            'primitive_count': len(mesh['primitives']), 'unique_vertex_pool_count': len(pools)}


def skin_points(geometry, world):
    transforms = np.asarray(world)[geometry['joints']] @ geometry['inverse_bind']
    blended = np.sum(transforms[geometry['palettes']] * geometry['weights'][:, :, None, None], axis=1)
    return np.einsum('vij,vj->vi', blended, geometry['positions'])[:, :3]


def surface_sample_times():
    full = {index / 60. for index in range(106)}
    local = {index / 240. for index in range(math.ceil(.45 * 240), math.floor(.72 * 240) + 1)}
    return sorted(full | local | {.72})


def scan_surfaces(metadata):
    from mathutils.bvhtree import BVHTree
    import verify_fine_overhead as helper

    old_doc, old_binary, _, _ = build.read_glb(build.PARENT / FILES[2])
    doc, binary, _, _ = build.read_glb(build.OUTPUT / FILES[2])
    old_tracks, tracks = build.tracks(old_doc, old_binary), build.tracks(doc, binary)
    body = body_geometry(metadata, doc, helper)
    blade = helper.surface(doc, binary)
    foot_masks = {}
    for side in ('L_', 'R_'):
        ids = [i for i, index in enumerate(body['joints']) if doc['nodes'][index].get('name') in (side + 'Foot', side + 'ToeBase')]
        mask = sum(np.sum(body['weights'] * (body['palettes'] == i), axis=1) for i in ids) > .5
        require(mask.any(), f'actual weighted shoe region absent: {side}')
        foot_masks[side] = mask
    rows, contact, sole_error, shoe_change = [], None, 0., 0.
    source_times = surface_sample_times()
    for time in source_times:
        _, old_world = build.pose(old_doc, old_tracks, time)
        _, world = build.pose(doc, tracks, time)
        old_parts, parts = helper.steel_points(blade, old_world), helper.steel_points(blade, world)
        for old, new in zip(old_parts, parts):
            require(np.array_equal(old[2], new[2]), f'actual steel path changed at {time}')
        steel = np.concatenate([part[2] for part in parts])
        points, old_points = skin_points(body, world), skin_points(body, old_world)
        for mask in foot_masks.values():
            sole_error = max(sole_error, abs(float(points[mask, 1].min()) + .028))
            shoe_change = max(shoe_change, float(np.abs(points[mask] - old_points[mask]).max()))
        triangles = points[body['faces']]
        low, high = steel.min(axis=0) - 1e-5, steel.max(axis=0) + 1e-5
        selected = body['faces'][((triangles.min(axis=1) <= high) & (triangles.max(axis=1) >= low)).all(axis=1)]
        overlaps = []
        if len(selected):
            body_bvh = BVHTree.FromPolygons(points.tolist(), selected.tolist(), all_triangles=True, epsilon=0.)
            for primitive, material, blade_points, blade_faces in parts:
                blade_bvh = BVHTree.FromPolygons(blade_points.tolist(), blade_faces.tolist(), all_triangles=True, epsilon=0.)
                hit = blade_bvh.overlap(body_bvh)
                if hit:
                    vertices = selected[[pair[1] for pair in hit]].ravel()
                    dominant = body['palettes'][vertices, np.argmax(body['weights'][vertices], axis=1)]
                    regions = Counter(doc['nodes'][body['joints'][int(i)]]['name'] for i in dominant)
                    overlaps.append({'primitive': primitive, 'material': material, 'triangle_pair_count': len(hit), 'body_joint_regions': dict(regions)})
        rows.append({'source_seconds': time, 'body_broadphase_triangles': len(selected), 'actual_steel_body_triangle_overlaps': overlaps})
        if time == 1.:
            contact = {'source_seconds': time, 'contact_plane_z_0p9_intersections': helper.true_contact(parts, .9)}
    require(sole_error < 2e-5 and shoe_change < 2e-6, 'actual shoe surface moved or left the formal sole plane')
    return {'status': 'scanned', 'scope': 'one union scan: full 0–1.75 seconds at 60Hz, plus 240Hz keys in 0.45–0.72 seconds and the exact 0.72 boundary; all body primitives and unique vertex pools',
            'sample_count': len(rows), 'source_times_seconds': source_times,
            'full_60hz_sample_count': 106, 'focused_window_seconds': [.45, .72],
            'focused_window_sample_count': sum(.45 <= time <= .72 for time in source_times),
            'focused_240hz_grid_sample_count': math.floor(.72 * 240) - math.ceil(.45 * 240) + 1,
            'explicit_focused_window_endpoint_seconds': .72,
            'body_primitive_count': body['primitive_count'], 'body_unique_vertex_pool_count': body['unique_vertex_pool_count'],
            'actual_steel_points_bit_identical_to_v7_at_all_scan_times': True,
            'actual_shoe_sole_plane_error_max_metres': sole_error, 'actual_shoe_surface_max_component_change_from_v7_metres': shoe_change,
            'overlap_sample_count': sum(bool(row['actual_steel_body_triangle_overlaps']) for row in rows), 'samples': rows, 'true_contact_sample': contact,
            'limits': 'Discrete triangle intersections do not prove continuous collision freedom or measure cloth volume.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-only', action='store_true', help='check frozen bytes and FK without importing Blender or claiming surface clearance')
    if '--' in sys.argv:
        arguments = sys.argv[sys.argv.index('--') + 1:]
    elif '--python' in sys.argv or '--python-expr' in sys.argv:
        arguments = []
    else:
        arguments = sys.argv[1:]
    args = parser.parse_args(arguments)
    metadata = frozen_metadata()
    guard_rows = canonical_neck_rows(metadata)
    alignment = json.loads((build.PARENT / 'fine_overhead_alignment.json').read_text())
    normalization = np.asarray(alignment['normalization_matrix_gltf'], dtype=float).reshape(4, 4).T
    results, plans, neck_payloads, neck_values = [], {}, [], []
    for index, name in enumerate(FILES):
        frame = normalization if index == 0 else None
        result, data = verify_pair(name, frame, guard_rows)
        results.append(result)
        plans[name] = verify_head_plan(data, frame)
        doc, binary, _, _ = build.read_glb(build.OUTPUT / name)
        tracks = build.tracks(doc, binary)
        names = {node.get('name'): i for i, node in enumerate(doc['nodes'])}
        neck_payloads.append([row_bytes(doc, binary, tracks[names[bone], 'rotation'][3]) for bone in NECK_NAMES])
        neck_values.append([tracks[names[bone], 'rotation'][1] for bone in NECK_NAMES])
    cross_error = 0.
    for other in neck_values[1:]:
        for raw, prepared in zip(neck_values[0], other):
            for a, b in zip(raw, prepared):
                cross_error = max(cross_error, rotation_angle(build.quaternion_matrix(a), build.quaternion_matrix(b)))
    require(cross_error < 1e-4, f'raw/body/preview neck rotations differ: {cross_error} degrees')
    head = plans[FILES[2]]
    surface = {'status': 'not_run', 'reason': '--host-only; a fresh Blender BVH scan remains required'} if args.host_only else scan_surfaces(metadata)
    passed = surface.get('overlap_sample_count', 0) == 0
    result = {'completion': ('host_checks_passed_surface_pending' if args.host_only else 'verified' if passed else 'failed_surface_overlap'),
              'clip': 'attack_overhead', 'duration_seconds': 1.75, 'contact_source_seconds': 1., 'sample_count': 211,
              'changed_channels_only': [bone + '.rotation' for bone in NECK_NAMES], 'files': results, 'head': head, 'head_plans_by_file': plans, 'surface_scan': surface,
              'new_neck_streams_identical_across_raw_body_preview': neck_payloads[0] == neck_payloads[1] == neck_payloads[2],
              'maximum_cross_file_neck_rotation_error_degrees': cross_error,
              'source_pins': {str(path.relative_to(build.REPO)): digest(path) for path in (build.PARENT / 'fine_overhead_metadata.json', build.PARENT / 'fine_overhead_alignment.json', Path(build.__file__), Path(__file__))},
              'limits': 'Anatomical roll is deliberately retained; ear-line elevation can change as pitch changes. Visual anatomy and SDK/device playback require separate review.'}
    path = build.OUTPUT / 'fine_overhead_neck_verification.json'
    require(path.resolve().parent == build.OUTPUT.resolve(), 'verification output escaped v9')
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'completion': result['completion'], 'output': str(path), 'surface_scan_status': surface['status'],
                      'overlap_sample_count': surface.get('overlap_sample_count'), 'head_pitch': head['guard_calibrated_pitch_degrees']}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
