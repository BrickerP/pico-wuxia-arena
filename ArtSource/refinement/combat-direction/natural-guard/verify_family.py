"""Independent family endpoint checks, then one bounded private-base scan.

The default endpoint phase runs with ordinary Python/numpy. Use --surfaces
only via hand-poses/run_blender.py -b --factory-startup --threads 2.
"""
import copy
import hashlib
import importlib.util
import json
import math
import struct
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE / 'candidate/family-v1'
PRODUCER = REPO / 'ArtSource/tripo-warrior'
RIG = PRODUCER / 'refined-base60k/rig.glb'
MASTER = HERE / 'candidate/v1/guard_raw.glb'
FINE = REPO / 'ArtSource/refinement/hand-poses/fine-overhead'
CLIPS = ('idle', 'walk', 'attack_overhead', 'attack_left', 'attack_right')
LEGS = ('L_Thigh', 'L_Calf', 'L_Foot', 'R_Thigh', 'R_Calf', 'R_Foot')
SOURCES = {
    'idle': (HERE / 'candidate/v1/idle_raw.glb', '0cac7c29e9fd9445e3b1e1825c60e885323b870181df33c5242fc0b6b40d95a6'),
    'walk': (FINE.parent / 'attack-keyposes/stage10/candidate/locked_guard_walk_raw.glb', '0e3a6c60c557cfbdfa979ffd9c98098c4d0306474f8e18dc7ae46f327ceb534e'),
    'attack_overhead': (HERE.parent / 'native-weighted-overhead/candidate/v5/weighted_overhead_raw.glb', '85d633ec61534c62f59269c1d9f02854e829d1b84db33a91e3a3afac2e779076'),
    'attack_left': (FINE.parent / 'attack-keyposes/stage5/candidate/slash_to_left_raw.glb', 'd0c850d4cb3fba0bff744a2714cc3310f98df4cc6e694d5b34dfc60cb815de65'),
    'attack_right': (FINE.parent / 'attack-keyposes/stage5/candidate/slash_to_right_raw.glb', 'a4ae7f07c11f96c5a2d9b81c571a5eaedd01cd628983146708926e516768263a'),
}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


import numpy as np
native = module('family_numpy_fk', FINE / 'build_neck_refinement.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(path):
    path = Path(path)
    return {'file': str(path.relative_to(REPO)), 'sha256': sha(path), 'bytes': path.stat().st_size}


def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')


def pin(path, expected):
    require(sha(path) == expected, 'SHA mismatch: ' + str(path))


def output_pin(metadata, filename):
    found = []
    def visit(value):
        if isinstance(value, dict):
            if isinstance(value.get('file'), str) and Path(value['file']).name == filename and 'sha256' in value:
                found.append(value['sha256'])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(metadata)
    require(found and len(set(found)) == 1, 'missing/ambiguous output pin: ' + filename)
    return found[0]


def decode(doc, binary):
    # Reuse the strict float32 decoder, retaining the actual name separately.
    require(len(doc.get('animations', [])) == 1, 'exactly one raw animation required')
    alias = {**doc, 'animations': [{**doc['animations'][0], 'name': 'attack_overhead'}]}
    return native.tracks(alias, binary)


def check_time(value, duration):
    require(not isinstance(value, bool) and isinstance(value, (int, float, np.floating))
            and math.isfinite(value) and 0 <= value <= duration, 'invalid finite clip time')


def check_raw(doc, binary, clip, original, guard_tracks, rig, rig_binary):
    require(doc['animations'][0]['name'] == clip, 'incorrect raw alias: ' + clip)
    for field in ('nodes', 'skins', 'meshes', 'materials', 'textures', 'images'):
        require(doc[field] == rig[field], 'raw rest/static drift: ' + clip + '/' + field)
    require(binary[:len(rig_binary)] == rig_binary, 'raw rig payload drift: ' + clip)
    joints = doc['skins'][0]['joints']
    require(len(joints) == len(set(joints)) == 78, '78 unique joints required')
    tracks = decode(doc, binary)
    require(set(tracks) == {(index, path) for index in joints for path in ('translation', 'rotation', 'scale')}, 'complete234 TRS required')
    keys = next(iter(tracks.values()))[0]
    old_keys = next(iter(original.values()))[0]
    require(np.array_equal(keys, old_keys), 'original full time grid changed: ' + clip)
    count = 181 if clip == 'idle' else 185 if clip == 'walk' else 211 if clip == 'attack_overhead' else 106
    duration = 1.5 if clip in ('idle', 'walk') else 1.75
    require(len(keys) == count and keys[0] == 0 and keys[-1] == duration, 'key/duration contract mismatch: ' + clip)
    markers = (0., 1/3, 1.5) if clip == 'walk' else (0., duration)
    marker_indices = [int(np.argmin(np.abs(keys - time))) for time in markers]
    require(all(abs(keys[index] - time) < 1e-7 for index, time in zip(marker_indices, markers)), 'canonical marker absent')
    for time in keys:
        check_time(time, duration)
    for (index, path), track in tracks.items():
        times, values, mode = track[:3]
        require(np.array_equal(times, keys) and np.isfinite(values).all(), 'invalid complete track')
        expected_mode = original[index, path][2]
        require(mode == expected_mode, 'source interpolation changed: ' + clip)
        require(all(np.array_equal(values[key], guard_tracks[index, path][1][0]) for key in marker_indices),
                'canonical float32 endpoint mismatch: ' + str((clip, doc['nodes'][index]['name'], path)))
        if path == 'rotation':
            error = float(np.max(np.abs(np.linalg.norm(values, axis=1) - 1.)))
            inherited = float(np.max(np.abs(np.linalg.norm(original[index, path][1], axis=1) - 1.)))
            require(error <= max(2e-5, inherited) + 1e-7, 'quaternion norm worsened beyond the frozen source')
        name = doc['nodes'][index].get('name', '')
        if name.startswith(('R_Thumb', 'R_Index', 'R_Mid', 'R_Ring', 'R_Pinky')):
            require(np.all(values == guard_tracks[index, path][1][0]), 'R15 UNBAKED grip drift')
        if clip == 'idle' or clip == 'walk' and name in LEGS:
            require(np.array_equal(values, original[index, path][1]), 'frozen idle/six-leg curve changed: ' + str((clip, name, path)))
        if clip.startswith('attack_'):
            interior = (keys >= .2) & (keys <= 1.5)
            require(np.array_equal(values[interior], original[index, path][1][interior]), 'attack interior changed outside endpoint windows')
    return tracks


def angle(a, b):
    a, b = np.asarray(a), np.asarray(b)
    dot = abs(float(a @ b) / float(np.linalg.norm(a) * np.linalg.norm(b)))
    return math.degrees(2 * math.acos(min(1., max(0., dot))))


def joint_steps(doc, tracks, first, second):
    a, b = native.pose(doc, tracks, first)[1], native.pose(doc, tracks, second)[1]
    local, world, negative = [], [], []
    for index in doc['skins'][0]['joints']:
        name = doc['nodes'][index]['name']
        qa, qb = native.sample(tracks[index, 'rotation'], first), native.sample(tracks[index, 'rotation'], second)
        local.append((angle(qa, qb), name))
        world.append((angle(native.matrix_quaternion(a[index]), native.matrix_quaternion(b[index])), name))
        # Storage sign is measured separately, never interpreted as a 360deg pose.
        times, values = tracks[index, 'rotation'][:2]
        ia, ib = int(np.argmin(abs(times - first))), int(np.argmin(abs(times - second)))
        if values[ia] @ values[ib] < 0:
            negative.append(name)
    return {'maximum_local_shortest_angle_degrees': max(local)[0], 'maximum_world_shortest_angle_degrees': max(world)[0],
            'top_local_joints': [{'joint': name, 'degrees': value} for value, name in sorted(local, reverse=True)[:6]],
            'top_world_joints': [{'joint': name, 'degrees': value} for value, name in sorted(world, reverse=True)[:6]],
            'stored_float32_Q_negative_dot_joints': negative}


def joins(doc, tracks, old_doc, old_tracks, clip):
    keys = next(iter(tracks.values()))[0]
    pairs = {(0, 1), (len(keys) - 2, len(keys) - 1)}
    for time in ((1/3,) if clip == 'walk' else (.2, 1.5) if clip.startswith('attack_') else (.75,)):
        index = int(np.argmin(abs(keys - time)))
        for first, second in ((index - 1, index), (index, index + 1)):
            if 0 <= first < second < len(keys):
                pairs.add((first, second))
    return [{'key_indices': [first, second], 'source_seconds': [float(keys[first]), float(keys[second])],
             'old': joint_steps(old_doc, old_tracks, float(keys[first]), float(keys[second])),
             'new': joint_steps(doc, tracks, float(keys[first]), float(keys[second]))}
            for first, second in sorted(pairs)]


def stored_sign_events(doc, tracks):
    events = []
    for (index, path), row in tracks.items():
        if path != 'rotation':
            continue
        times, values = row[:2]
        dots = np.sum(values[:-1] * values[1:], axis=1)
        for key in np.flatnonzero(dots < 0):
            events.append({'joint': doc['nodes'][index]['name'], 'key_indices': [int(key), int(key + 1)],
                           'source_seconds': [float(times[key]), float(times[key + 1])],
                           'stored_float32_Q_dot': float(dots[key]),
                           'shortest_orientation_angle_degrees': angle(values[key], values[key + 1])})
    return events


def quaternion_norm_deviations(doc, old, new):
    result = []
    for (index, path), row in new.items():
        if path == 'rotation':
            before = float(np.max(abs(np.linalg.norm(old[index, path][1], axis=1) - 1.)))
            after = float(np.max(abs(np.linalg.norm(row[1], axis=1) - 1.)))
            if max(before, after) >= 2e-5:
                result.append({'joint': doc['nodes'][index]['name'], 'old_maximum_norm_deviation': before,
                               'new_maximum_norm_deviation': after, 'whole_track_float32_values_unchanged': np.array_equal(old[index, path][1], row[1])})
    return result


def rejections(assets, originals, guard, rig, rig_binary):
    rejected = []
    for value in (float('nan'), True, -.001, 1.751):
        try:
            check_time(value, 1.75)
        except ValueError:
            rejected.append('invalid time ' + repr(value))
        else:
            raise AssertionError('invalid time accepted')
    try:
        pin(OUT / 'idle_raw.glb', '0' * 64)
    except ValueError:
        rejected.append('actual idle file wrong SHA')
    else:
        raise AssertionError('wrong SHA accepted')
    doc, binary, _ = assets['attack_overhead']
    animation = doc['animations'][0]
    channel = next(row for row in animation['channels'] if row['target']['path'] == 'translation')
    sampler = animation['samplers'][channel['sampler']]
    for slot, amount, description in (('output', .01, 'actual exported last endpoint +10mm'), ('input', .1, 'actual exported last timeline +100ms')):
        accessor = doc['accessors'][sampler[slot]]
        view = doc['bufferViews'][accessor['bufferView']]
        width = 12 if slot == 'output' else 4
        offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0) + (accessor['count'] - 1) * width
        bad = bytearray(binary)
        struct.pack_into('<f', bad, offset, struct.unpack_from('<f', bad, offset)[0] + amount)
        try:
            check_raw(doc, bad, 'attack_overhead', originals['attack_overhead'][2], guard, rig, rig_binary)
        except ValueError:
            rejected.append(description)
        else:
            raise AssertionError('corrupted actual export accepted')
    return rejected


def endpoints():
    meta_path = OUT / 'family_authoring.json'
    metadata = json.loads(meta_path.read_text())
    def has_old_lock(value):
        if isinstance(value, dict):
            return 'locked_head_ancestor_chain' in value or any(has_old_lock(child) for child in value.values())
        return isinstance(value, list) and any(has_old_lock(child) for child in value)
    require(not has_old_lock(metadata), 'new family cannot advertise the old head-chain lock')
    pin(RIG, '43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6')
    pin(MASTER, 'c9a9673852343f922c7c5cfc026dc63a5c21b89b037f2729c5ea42cdf9a23ee4')
    rig, rig_binary, *_ = native.read_glb(RIG)
    guard_doc, guard_binary, *_ = native.read_glb(MASTER)
    guard = decode(guard_doc, guard_binary)
    assets, originals, rows = {}, {}, {}
    for clip in CLIPS:
        path = OUT / (clip + '_raw.glb')
        pin(path, output_pin(metadata, path.name))
        source_path, source_sha = SOURCES[clip]
        pin(source_path, source_sha)
        old_doc, old_binary, *_ = native.read_glb(source_path)
        old_tracks = decode(old_doc, old_binary)
        doc, binary, *_ = native.read_glb(path)
        tracks = check_raw(doc, binary, clip, old_tracks, guard, rig, rig_binary)
        assets[clip], originals[clip] = (doc, binary, tracks), (old_doc, old_binary, old_tracks)
        rows[clip] = {'raw': identity(path), 'source': identity(source_path), 'channel_count': len(tracks),
                      'key_count': len(next(iter(tracks.values()))[0]), 'exact_master_guard_markers_seconds': [0., 1/3, 1.5] if clip == 'walk' else [0., 1.5 if clip == 'idle' else 1.75],
                      'stored_Q_negative_dot_events_all_adjacent_keys': {'old': stored_sign_events(old_doc, old_tracks), 'new': stored_sign_events(doc, tracks)},
                      'inherited_quaternion_norm_deviations_at_or_above_2e_minus5': quaternion_norm_deviations(doc, old_tracks, tracks),
                      'join_neighbor_key_measurements': joins(doc, tracks, old_doc, old_tracks, clip)}
        print('FAMILY_ENDPOINT_PASS', clip, flush=True)
    idle = assets['idle'][2]
    changed = [guard_doc['nodes'][index]['name'] + '.' + path for (index, path), row in idle.items()
               if not np.array_equal(native.sample(row, 1/3), guard[index, path][1][0])]
    require(changed, 'breathing idle at absolute1/3 must not be frozen to guard')
    rejected = rejections(assets, originals, guard, rig, rig_binary)
    report = {'status': 'all_five_raw_endpoints_passed', 'authoring': identity(meta_path), 'master_guard': identity(MASTER),
              'clips': rows, 'idle': {'source_loop_seconds': [0., 1.5], 'loop_duration_seconds': 1.5, 'keys': 181,
                                     'interpolation': 'LINEAR', 'absolute_one_third_changed_channels': changed},
              'walk': {'source_loop_seconds': [1/3, 1.5], 'loop_duration_seconds': 7/6,
                       'six_original_leg_TRS_curves_and_time_grid_exact': True, 'original_mixed_interpolation_preserved': True},
              'all_raw_original_rest_and_payload_exact': True, 'all_234_TRS_marker_values_float32_exact': True,
              'constant_R15_master_UNBAKED_exact': True, 'three_attack_interiors_0p20_to1p50_exact_source': True,
              'rejection_cases_actually_run': rejected,
              'Q_measurement_semantics': 'Shortest orientation angle uses abs(normalized Q dot). Stored negative Q dot is separately listed; q and -q encode the same orientation. Adjacent source keys are measured, not interpolated coarse30Hz frames.',
              'limits': ['Endpoint/source preservation proof only; joins are measured rather than declared aesthetically approved.',
                         'No production family gate, native SDK playback, blend, retarget or device acceptance.'],
              'verification_source_pins': {str(p.relative_to(REPO)): sha(p) for p in (Path(__file__), Path(native.__file__))}}
    save('verification_endpoints.json', report)
    return report, metadata, assets, originals


def surfaces(metadata, assets, originals):
    require('--threads' in sys.argv and sys.argv[sys.argv.index('--threads') + 1] == '2', 'host Blender2threads required')
    sys.path.insert(0, str(HERE))
    tools = module('family_natural_guard_surfaces', HERE / 'verify_natural_guard.py')
    library, author, base, utility = tools.library, tools.author, tools.base, tools.utility
    preview_path = OUT / 'base_family_preview.glb'
    pin(preview_path, output_pin(metadata, preview_path.name))
    preview, preview_binary = library.read_glb(preview_path)
    require({a['name'] for a in preview['animations']} == set(CLIPS) and len(preview['animations']) == 5, 'private preview must contain precisely five family clips')
    formal_path = PRODUCER / 'library/base_prepared_png.glb'
    formal, formal_binary = library.read_glb(formal_path)
    for field in ('nodes', 'skins', 'scenes'):
        require(preview[field] == formal[field], 'private base static ' + field + ' drift')
    actual_meshes, expected_meshes = utility.mesh_signature(preview, preview_binary), utility.mesh_signature(formal, formal_binary)
    require(len(actual_meshes) == len(expected_meshes), 'private base primitive count drift')
    for a, b in zip(actual_meshes, expected_meshes):
        require(a.keys() == b.keys(), 'private base attribute set drift')
        for key in a:
            require(a[key] == b[key] if key == 'material' else np.array_equal(a[key], b[key]), 'private base geometry/material drift: ' + key)
    target, target_binary = library.read_glb(PRODUCER / metadata['body_source']['source'])
    body = tools.BodySurface(target, target_binary, preview)
    steel_surface = utility.surface(preview, preview_binary)
    parents, order = library.node_order(preview)
    names = {node.get('name'): index for index, node in enumerate(preview['nodes'])}
    shift = metadata['preview_grounding']['constant_local_root_shift']
    result = {'status': 'finite_base_scan_in_progress', 'preview': identity(preview_path), 'authoring': identity(OUT / 'family_authoring.json'),
              'same_base_rest_mesh_skin_materials_verified_against': identity(formal_path),
              'clips': {}, 'semantic_region_triangle_counts': {name: len(faces) for name, (_, faces) in body.regions.items()},
              'scope': 'Actual private base preview: full30Hz for each of the five clips plus endpoint-window/loop seams. Actual posed steel/body triangles and R/L hands/forearms versus head/chest.',
              'limits': ['No continuous-time or volume proof; dominant-joint regions exclude adjacent neck/upperarm seams and within-region cloth layers.',
                         'Original source overlaps are shown in the identical base context when candidate overlap is found; they are not silently waived.',
                         'No three-target retarget or native device acceptance.']}
    all_clear = True
    for clip in CLIPS:
        raw, raw_binary, _ = assets[clip]
        animation = next(a for a in preview['animations'] if a['name'] == clip)
        single = {**preview, 'animations': [animation]}
        actual, keys = library.decode_animation(single, preview_binary)
        expected_doc = copy.deepcopy(raw)
        expected_binary, _ = tools.apply_finger_rotation_offsets(expected_doc, raw_binary, metadata['body_source'].get('finger_rotation_offsets'))
        expected, expected_keys = library.decode_animation(expected_doc, expected_binary)
        require(keys == expected_keys and len(actual) == 234, 'preview time/channels changed')
        maximum = 0.
        for (index, path), row in expected.items():
            name = raw['nodes'][index]['name']
            other = actual[names[name], path]
            require(other[2] == row[2] and other[0] == row[0], 'preview interpolation/times changed')
            for a, b in zip(row[1], other[1]):
                if name == 'BoneRoot' and path == 'translation':
                    a = struct.unpack('<3f', struct.pack('<3f', *[x + y for x, y in zip(a, shift)]))
                maximum = max(maximum, utility.maximum_row_delta(a, b, path))
        require(maximum < 1e-7, 'private preview must apply finger offsets/root shift once')
        old_doc, old_binary, _ = originals[clip]
        old_calibrated = copy.deepcopy(old_doc)
        old_binary, _ = tools.apply_finger_rotation_offsets(old_calibrated, old_binary, metadata['body_source'].get('finger_rotation_offsets'))
        old_raw_tracks, _ = library.decode_animation(old_calibrated, old_binary)
        old_tracks = {}
        for (index, path), row in old_raw_tracks.items():
            name = old_doc['nodes'][index]['name']
            values = row[1]
            if name == 'BoneRoot' and path == 'translation':
                values = [struct.unpack('<3f', struct.pack('<3f', *[x + y for x, y in zip(value, shift)])) for value in values]
            old_tracks[names[name], path] = (row[0], values, row[2])
        duration = 1.5 if clip in ('idle', 'walk') else 1.75
        times = sorted(set([index / 30 for index in range(math.floor(duration * 30) + 1)] +
                           [time for time in (0., 1/3, .18333333333333332, .2, .21666666666666667, 1.4833333333333334, 1.5, 1.5166666666666666, duration) if time <= duration]))
        rows = []
        for time in times:
            world = author.worlds(preview, base.sample(preview, actual, time), parents, order)
            parts = utility.steel_points(steel_surface, world)
            overlaps, regions = body.collisions(body.points(world), parts)
            row = {'source_seconds': time, 'actual_steel_body_triangle_overlaps': overlaps, 'nonadjacent_region_triangle_pairs': regions}
            if overlaps or any(regions.values()):
                old_world = author.worlds(preview, base.sample(preview, old_tracks, time), parents, order)
                old_overlaps, old_regions = body.collisions(body.points(old_world), utility.steel_points(steel_surface, old_world))
                row['same_time_original_in_same_base_context'] = {'actual_steel_body_triangle_overlaps': old_overlaps, 'nonadjacent_region_triangle_pairs': old_regions}
            rows.append(row)
        failures = [row for row in rows if row['actual_steel_body_triangle_overlaps'] or any(row['nonadjacent_region_triangle_pairs'].values())]
        all_clear = all_clear and not failures
        result['clips'][clip] = {'sample_count': len(times), 'overlap_sample_count': len(failures),
                                 'once_finger_calibration_and_root_shift_max_component_error': maximum, 'frames': rows}
        save('verification_surfaces.json', result)
        print('FAMILY_SURFACE_CLIP', clip, 'samples', len(times), 'overlap_samples', len(failures), flush=True)
    result['status'] = 'finite_base_scan_passed' if all_clear else 'finite_base_scan_completed_with_overlaps'
    pin(preview_path, output_pin(metadata, preview_path.name))
    for clip in CLIPS:
        pin(OUT / (clip + '_raw.glb'), output_pin(metadata, clip + '_raw.glb'))
    result['verification_source_pins'] = {str(path.relative_to(REPO)): sha(path) for path in
        (Path(__file__), Path(tools.__file__), Path(utility.__file__), Path(library.__file__), Path(author.__file__), PRODUCER / 'prepare_rigged_warrior.py')}
    save('verification_surfaces.json', result)
    return result


def main():
    phase = 'surfaces' if '--surfaces' in sys.argv else 'endpoints'
    try:
        report, metadata, assets, originals = endpoints()
        if phase == 'surfaces':
            report = surfaces(metadata, assets, originals)
        print('FAMILY_VERIFICATION', phase, report['status'], flush=True)
        if report['status'] == 'finite_base_scan_completed_with_overlaps':
            raise SystemExit(2)
    except Exception as error:
        save('verification_' + phase + '_failure.json', {'status': 'failed', 'error': str(error), 'traceback': traceback.format_exc(), 'verifier': identity(Path(__file__))})
        raise


if __name__ == '__main__':
    main()
