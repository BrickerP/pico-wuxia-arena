"""Bounded checks of the private natural guard and its breathing idle.

Execute with hand-poses/run_blender.py -b --factory-startup --threads 2.
This reads only the base context and writes verification JSON in candidate/v1.
"""
import copy
import hashlib
import json
import math
import struct
import sys
import traceback
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OUT = HERE / 'candidate/v1'
FINE = REPO / 'ArtSource/refinement/hand-poses/fine-overhead'
PRODUCER = REPO / 'ArtSource/tripo-warrior'
RIG = PRODUCER / 'refined-base60k/rig.glb'
SOURCE = HERE.parent / 'native-weighted-overhead/candidate/v5/weighted_overhead_raw.glb'
SOURCE_SHA = '85d633ec61534c62f59269c1d9f02854e829d1b84db33a91e3a3afac2e779076'
RIG_SHA = '43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6'
DURATION = 1.5
RATE = 120
sys.path.insert(0, str(FINE))
import build_fine_overhead as base
import verify_fine_overhead as utility
from prepare_rigged_warrior import apply_finger_rotation_offsets
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
import numpy as np

library, author, stance = base.library, base.author, base.stance


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(path):
    path = Path(path)
    return {'file': str(path.relative_to(REPO)), 'sha256': digest(path), 'bytes': path.stat().st_size}


def validate_pin(path, expected):
    require(digest(path) == expected, 'SHA mismatch: ' + str(path))


def validate_time(seconds):
    require(not isinstance(seconds, bool) and isinstance(seconds, (int, float, np.floating))
            and math.isfinite(seconds) and 0 <= seconds <= DURATION,
            'finite source time in 0–1.5 seconds required')


def pin_for(metadata, filename):
    """Find the declared identity, independent of the author's grouping labels."""
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
    require(found and len(set(found)) == 1, 'missing/ambiguous authoring identity: ' + filename)
    return found[0]


def validate_contract(doc, binary, clip, count, guard_tracks=None, source_tracks=None):
    require(len(doc.get('animations', [])) == 1 and doc['animations'][0]['name'] == clip,
            'one explicitly named clip required: ' + clip)
    joints = doc['skins'][0]['joints']
    require(len(joints) == len(set(joints)) == 78, '78 unique skin joints required')
    tracks, keys = library.decode_animation(doc, binary)
    wanted = {(index, path) for index in joints for path in ('translation', 'rotation', 'scale')}
    require(set(tracks) == wanted and len(tracks) == 234, 'complete 234 skin-joint TRS channels required')
    require(len(keys) == count, 'unexpected key count for ' + clip)
    expected = np.asarray([0., DURATION] if count == 2 else [i / RATE for i in range(count)], dtype='<f4')
    require(np.array_equal(np.asarray(keys), expected), 'timeline must be the exact declared float32 grid')
    for time in keys:
        validate_time(time)
    for (index, path), row in tracks.items():
        values = np.asarray(row[1])
        require(row[0] == keys and row[2] == 'LINEAR', 'per-channel timeline/interpolation mismatch')
        require(np.isfinite(values).all(), 'nonfinite exported track')
        require(row[1][0] == row[1][-1], 'exported endpoints do not close exactly')
        if clip == 'guard_pose':
            require(all(value == row[1][0] for value in row[1]), 'guard_pose must be static')
        if guard_tracks is not None:
            require(row[1][0] == guard_tracks[index, path][1][0], 'idle endpoint differs from new guard float32 values')
        if path == 'rotation':
            require(np.max(np.abs(np.linalg.norm(values, axis=1) - 1.)) < 2e-5, 'invalid exported quaternion norm')
        if source_tracks is not None and doc['nodes'][index].get('name') in base.RIGHT_FINGERS:
            expected_hand = source_tracks[index, path][1][0]
            require(all(value == expected_hand for value in row[1]), 'R15 must remain the exact constant v5 UNBAKED grip')
    return tracks, keys


def verify_raw_static(doc, binary, rig, rig_binary):
    for field in ('nodes', 'skins', 'meshes', 'materials', 'textures', 'images'):
        require(doc[field] == rig[field], 'raw rest/static ' + field + ' changed')
    require(binary[:len(rig_binary)] == rig_binary, 'raw original rig payload changed')


def preview_expected(raw, binary, preview, preview_binary, metadata):
    """Apply the producer operation once to independent in-memory raw bytes."""
    expected_doc = copy.deepcopy(raw)
    calibrated, _ = apply_finger_rotation_offsets(expected_doc, binary, metadata['body_source'].get('finger_rotation_offsets'))
    expected, keys = library.decode_animation(expected_doc, calibrated)
    actual, actual_keys = library.decode_animation(preview, preview_binary)
    require(len(actual) == 234 and actual_keys == keys, 'preview channels/keys differ from raw')
    names = {node.get('name'): index for index, node in enumerate(preview['nodes'])}
    shift = metadata['preview_grounding']['constant_local_root_shift']
    maximum = 0.
    for (index, path), track in expected.items():
        name = raw['nodes'][index].get('name')
        require(name in names, 'missing preview joint ' + str(name))
        other = actual[names[name], path]
        require(other[2] == 'LINEAR' and len(other[1]) == len(track[1]), 'preview stream mismatch')
        for a, b in zip(track[1], other[1]):
            if name == 'BoneRoot' and path == 'translation':
                a = struct.unpack('<3f', struct.pack('<3f', *[x + y for x, y in zip(a, shift)]))
            maximum = max(maximum, utility.maximum_row_delta(a, b, path))
    require(maximum < 1e-7, 'preview differs from once-only finger calibration and root shift: ' + str(maximum))
    return actual, maximum


class BodySurface:
    """All actual body material pools plus explicit nonadjacent anatomy."""
    def __init__(self, target, target_binary, preview):
        skin = target['skins'][0]
        preview_names = {node.get('name'): index for index, node in enumerate(preview['nodes'])}
        joint_names = [target['nodes'][index]['name'] for index in skin['joints']]
        self.joints = [preview_names[name] for name in joint_names]
        self.bind = utility.accessor(target, target_binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        mesh = target['meshes'][next(node['mesh'] for node in target['nodes'] if 'mesh' in node)]
        positions, palettes, weights, faces, materials, pools = [], [], [], [], [], {}
        offset = 0
        for primitive in mesh['primitives']:
            attrs = primitive['attributes']
            key = tuple(attrs[name] for name in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
            if key not in pools:
                points = utility.accessor(target, target_binary, attrs['POSITION']).astype(float)
                pools[key] = offset
                positions.append(points)
                palettes.append(utility.accessor(target, target_binary, attrs['JOINTS_0']).astype(int))
                weights.append(utility.accessor(target, target_binary, attrs['WEIGHTS_0']).astype(float))
                offset += len(points)
            face = utility.accessor(target, target_binary, primitive['indices']).reshape(-1, 3).astype(int) + pools[key]
            faces.append(face)
            materials.extend([target['materials'][primitive['material']].get('name', '')] * len(face))
        self.position = np.column_stack((np.concatenate(positions), np.ones(offset)))
        self.palette, self.weights, self.faces = np.concatenate(palettes), np.concatenate(weights), np.concatenate(faces)
        self.weights /= self.weights.sum(axis=1)[:, None]
        self.materials = np.asarray(materials)
        self.dominant = np.asarray(joint_names)[self.palette[np.arange(offset), np.argmax(self.weights, axis=1)]]
        groups = {'head': {'Head', 'L_Eye', 'R_Eye', 'FacialBone'}, 'chest': {'Waist', 'Spine01', 'Spine02'}}
        for side in ('R_', 'L_'):
            groups[side + 'forearm'] = {side + name for name in ('Forearm', 'ForearmTwist01', 'ForearmTwist02', 'ElbowShareBone')}
            groups[side + 'hand'] = {name for name in joint_names if name == side + 'Hand' or name.startswith(tuple(side + finger for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')))}
        self.regions = {}
        for label, names in groups.items():
            subset = self.faces[np.isin(self.dominant, list(names))[self.faces].all(axis=1)]
            indices, remap = np.unique(subset, return_inverse=True)
            require(len(subset) > 0, 'empty actual body semantic region: ' + label)
            self.regions[label] = indices, remap.reshape(-1, 3)

    def points(self, world):
        transforms = np.asarray([list(world[index]) for index in self.joints]) @ self.bind
        blend = np.sum(transforms[self.palette] * self.weights[:, :, None, None], axis=1)
        return np.einsum('vij,vj->vi', blend, self.position)[:, :3]

    def collisions(self, points, steel_parts):
        steel = np.concatenate([part[2] for part in steel_parts])
        triangles = points[self.faces]
        low, high = steel.min(axis=0) - .00001, steel.max(axis=0) + .00001
        selected_indices = np.flatnonzero(((triangles.min(axis=1) <= high) & (triangles.max(axis=1) >= low)).all(axis=1))
        selected = self.faces[selected_indices]
        overlaps = []
        if len(selected):
            tree = BVHTree.FromPolygons(points.tolist(), selected.tolist(), all_triangles=True, epsilon=0.)
            for primitive, material, part_points, faces in steel_parts:
                hits = BVHTree.FromPolygons(part_points.tolist(), faces.tolist(), all_triangles=True, epsilon=0.).overlap(tree)
                if hits:
                    actual_faces = selected_indices[[pair[1] for pair in hits]]
                    overlaps.append({'steel_primitive': primitive, 'steel_material': material, 'triangle_pair_count': len(hits),
                                     'body_materials': dict(Counter(self.materials[actual_faces])),
                                     'dominant_body_joint_vertices': dict(Counter(self.dominant[self.faces[actual_faces].ravel()]))})
        trees = {label: BVHTree.FromPolygons(points[indices].tolist(), faces.tolist(), all_triangles=True, epsilon=0.)
                 for label, (indices, faces) in self.regions.items()}
        region_hits = {}
        for limb in ('R_forearm', 'R_hand', 'L_forearm', 'L_hand'):
            for core in ('head', 'chest'):
                region_hits[limb + '__' + core] = len(trees[limb].overlap(trees[core]))
        return overlaps, region_hits


def rejection_tests(raw, binary, guard_tracks, source_tracks):
    rejected = []
    for time in (float('nan'), -0.001, 1.501, True):
        try:
            validate_time(time)
        except ValueError:
            rejected.append('invalid source time ' + repr(time))
        else:
            raise AssertionError('invalid time accepted')
    try:
        validate_pin(OUT / 'idle_raw.glb', '0' * 64)
    except ValueError:
        rejected.append('wrong SHA of actual exported idle')
    else:
        raise AssertionError('incorrect SHA accepted')
    animation = raw['animations'][0]
    channel = next(row for row in animation['channels'] if row['target']['path'] == 'translation')
    sampler = animation['samplers'][channel['sampler']]
    output = raw['accessors'][sampler['output']]
    view = raw['bufferViews'][output['bufferView']]
    offset = view.get('byteOffset', 0) + output.get('byteOffset', 0) + (output['count'] - 1) * 12
    bad = bytearray(binary)
    struct.pack_into('<f', bad, offset, struct.unpack_from('<f', bad, offset)[0] + .01)
    try:
        validate_contract(raw, bad, 'idle', 181, guard_tracks, source_tracks)
    except ValueError:
        rejected.append('actual exported last guard translation mutated by 10mm')
    else:
        raise AssertionError('broken endpoint accepted')
    bad = bytearray(binary)
    time = raw['accessors'][sampler['input']]
    view = raw['bufferViews'][time['bufferView']]
    offset = view.get('byteOffset', 0) + time.get('byteOffset', 0) + (time['count'] - 1) * 4
    struct.pack_into('<f', bad, offset, 1.6)
    try:
        validate_contract(raw, bad, 'idle', 181, guard_tracks, source_tracks)
    except ValueError:
        rejected.append('actual exported final timeline key mutated to 1.6s')
    else:
        raise AssertionError('bad actual time grid accepted')
    return rejected


def existing_production_gate(raw, binary, rig, rig_binary):
    """Probe the unchanged gate; never alter keys/interpolation to pass it."""
    try:
        library.validate_source_clip(raw, binary, rig, rig_binary, 'locomotion78', 'idle')
    except ValueError as error:
        reason = str(error)
        require('frozen 91/185-key' in reason, 'unexpected existing producer rejection: ' + reason)
    else:
        raise AssertionError('181-key breathing source unexpectedly accepted by current frozen locomotion78 gate')
    return {'actual_call': 'validate_source_clip(actual idle_raw, original rig, locomotion78, idle)',
            'actual_result': 'rejected', 'actual_rejection': reason,
            'additional_existing_gate_from_source_inspection':
                'Current idle requires every track STEP and constant; moving leg LINEAR is allowed only for walk. '
                'The breathing body LINEAR curves also need a coherent contract replacement. '
                'This later gate was not reached because the actual181-key source fails the91-key check first.',
            'source_keys_and_interpolation_modified_for_probe': False,
            'production_source': identity(Path(library.__file__))}


def verify():
    meta_path = OUT / 'natural_guard_authoring.json'
    metadata = json.loads(meta_path.read_text())
    validate_pin(SOURCE, SOURCE_SHA)
    validate_pin(RIG, RIG_SHA)
    for relative, sha in metadata['source_pins'].items():
        validate_pin(REPO / relative, sha)
    assets = {}
    for filename in ('guard_raw.glb', 'idle_raw.glb', 'guard_preview.glb', 'idle_preview.glb'):
        validate_pin(OUT / filename, pin_for(metadata, filename))
        assets[filename] = library.read_glb(OUT / filename)
    rig, rig_binary = library.read_glb(RIG)
    source, source_binary = library.read_glb(SOURCE)
    source_tracks, _ = library.decode_animation(source, source_binary)
    guard, guard_binary = assets['guard_raw.glb']
    raw, raw_binary = assets['idle_raw.glb']
    for doc, binary in ((guard, guard_binary), (raw, raw_binary)):
        verify_raw_static(doc, binary, rig, rig_binary)
    guard_tracks, _ = validate_contract(guard, guard_binary, 'guard_pose', 2, source_tracks=source_tracks)
    tracks, _ = validate_contract(raw, raw_binary, 'idle', 181, guard_tracks, source_tracks)
    producer_rejection = existing_production_gate(raw, raw_binary, rig, rig_binary)
    interior_changed_channels = {}
    for key in (60, 120):
        changed = [raw['nodes'][index]['name'] + '.' + path
                   for (index, path), row in tracks.items()
                   if row[1][key] != guard_tracks[index, path][1][0]]
        require(changed, 'one-third/two-thirds breath samples must not be frozen to guard')
        interior_changed_channels[str(key / RATE)] = changed
    changed_guard_channels = [guard['nodes'][index]['name'] + '.' + path
                              for (index, path), row in guard_tracks.items()
                              if row[1][0] != source_tracks[index, path][1][0]]
    require(any(name.startswith(('L_Upperarm.', 'L_Forearm.', 'L_Hand.')) for name in changed_guard_channels),
            'new guard must actually change the inherited left-arm pose')
    rejected = rejection_tests(raw, raw_binary, guard_tracks, source_tracks)
    guard_preview, guard_preview_binary = assets['guard_preview.glb']
    preview, preview_binary = assets['idle_preview.glb']
    _, guard_bake = preview_expected(guard, guard_binary, guard_preview, guard_preview_binary, metadata)
    preview_tracks, idle_bake = preview_expected(raw, raw_binary, preview, preview_binary, metadata)
    formal, formal_binary = library.read_glb(PRODUCER / 'library/base_prepared_png.glb')
    expected_meshes = utility.mesh_signature(formal, formal_binary)
    for doc, binary in ((guard_preview, guard_preview_binary), (preview, preview_binary)):
        meshes = utility.mesh_signature(doc, binary)
        require(len(meshes) == len(expected_meshes), 'base preview primitive count drift')
        for index, (actual, expected) in enumerate(zip(meshes, expected_meshes)):
            require(actual.keys() == expected.keys(), 'base preview attribute set drift')
            for key in actual:
                equal = actual[key] == expected[key] if key == 'material' else np.array_equal(actual[key], expected[key])
                require(equal, 'base preview geometry/material drift: ' + str((index, key)))
    raw_parents, raw_order = library.node_order(raw)
    parents, order = library.node_order(preview)
    names = {node.get('name'): index for index, node in enumerate(raw['nodes'])}
    preview_names = {node.get('name'): index for index, node in enumerate(preview['nodes'])}
    norm = library.local_matrix({'matrix': metadata['normalization_matrix_gltf']})
    raw_guard = author.worlds(raw, base.sample(raw, tracks, 0.), raw_parents, raw_order)
    preview_guard = author.worlds(preview, base.sample(preview, preview_tracks, 0.), parents, order)
    joints = set(raw['skins'][0]['joints'])
    bone_reference = {index: (raw_guard[index].translation - raw_guard[raw_parents[index]].translation).length
                      for index in joints if index in raw_parents and raw_parents[index] in joints
                      and raw['nodes'][index].get('name') not in ('BoneRoot', 'Hip')}
    target, target_binary = library.read_glb(PRODUCER / metadata['body_source']['source'])
    body = BodySurface(target, target_binary, preview)
    foot_geometry = stance.foot_geometry(preview, preview_binary)
    steel_surface = utility.surface(preview, preview_binary)
    steel_guard_parts = utility.steel_points(steel_surface, preview_guard)
    steel_guard = np.concatenate([part[2] for part in steel_guard_parts])
    feet_guard = stance.foot_measurements(foot_geometry, preview_guard, Matrix.Identity(4))
    floor = -.028
    times = sorted(set([index / 30 for index in range(46)] + [.375, .75, 1.125]))
    motion_names = ('Hip', 'Spine02', 'R_Upperarm', 'L_Upperarm', 'R_Hand', 'L_Hand')
    displacements = {name: 0. for name in motion_names}
    rotations = {name: 0. for name in motion_names}
    sole = foot_motion = bone = steel_motion = 0.
    rows = []
    for time in times:
        validate_time(time)
        raw_world = author.worlds(raw, base.sample(raw, tracks, time), raw_parents, raw_order)
        world = author.worlds(preview, base.sample(preview, preview_tracks, time), parents, order)
        feet = stance.foot_measurements(foot_geometry, world, Matrix.Identity(4))
        for side, measurement in feet.items():
            sole = max(sole, abs(measurement['sole_height_metres'] - floor))
            foot_motion = max(foot_motion, float(np.linalg.norm(np.asarray(measurement['centre_metres']) - feet_guard[side]['centre_metres'])))
        for index, reference in bone_reference.items():
            actual = (raw_world[index].translation - raw_world[raw_parents[index]].translation).length
            bone = max(bone, abs(actual - reference) * norm.to_scale()[0])
        for name in motion_names:
            index = preview_names[name]
            displacements[name] = max(displacements[name], (world[index].translation - preview_guard[index].translation).length)
            rotations[name] = max(rotations[name], utility.angle(world[index].to_quaternion(), preview_guard[index].to_quaternion()))
        steel_parts = utility.steel_points(steel_surface, world)
        steel = np.concatenate([part[2] for part in steel_parts])
        steel_motion = max(steel_motion, float(np.linalg.norm(steel - steel_guard, axis=1).max()))
        overlaps, regions = body.collisions(body.points(world), steel_parts)
        rows.append({'source_seconds': time, 'foot_surfaces': feet,
                     'joint_origins_metres': {name: list(world[preview_names[name]].translation) for name in motion_names},
                     'steel_bounds_metres': {'min': steel.min(axis=0).tolist(), 'max': steel.max(axis=0).tolist()},
                     'actual_steel_body_triangle_overlaps': overlaps, 'nonadjacent_region_triangle_pairs': regions})
        print('NATURAL_GUARD_CHECK', time, 'steel', sum(row['triangle_pair_count'] for row in overlaps),
              'self', sum(regions.values()), flush=True)
    collision_frames = [row for row in rows if row['actual_steel_body_triangle_overlaps'] or any(row['nonadjacent_region_triangle_pairs'].values())]
    breath_names = ('Spine02', 'R_Upperarm', 'L_Upperarm')
    checks = {
        'nonstatic_chest_or_shoulder': any(displacements[name] >= .0002 or rotations[name] >= .05 for name in breath_names),
        'small_chest_and_shoulder_motion': all(displacements[name] <= .025 and rotations[name] <= 3. for name in breath_names),
        'stable_right_wrist': displacements['R_Hand'] <= .015 and rotations['R_Hand'] <= 3.,
        'stable_actual_steel_vertices': steel_motion <= .030,
        'actual_shoe_floor': sole <= .00002,
        'actual_shoe_centres': foot_motion <= .0001,
        'bone_lengths': bone <= .000003,
        'sampled_steel_and_nonadjacent_regions_clear': not collision_frames,
    }
    for relative, sha in metadata['source_pins'].items():
        validate_pin(REPO / relative, sha)
    for filename in assets:
        validate_pin(OUT / filename, pin_for(metadata, filename))
    return {'status': 'bounded_base_source_checks_passed' if all(checks.values()) else 'bounded_base_source_checks_failed',
            'checks': checks, 'scope': 'Private base target only. Static guard plus full idle 0–1.5s at30Hz and .375/.75/1.125s breathing samples.',
            'assets': {name: identity(OUT / name) for name in assets}, 'authoring': identity(meta_path),
            'source_v5': identity(SOURCE), 'sample_count': len(times), 'overlap_sample_count': len(collision_frames),
            'new_guard_changed_channels_from_source_v5_guard': changed_guard_channels,
            'interior_changed_channels_from_guard': interior_changed_channels,
            'existing_production_locomotion78_gate': producer_rejection,
            'contract': {'raw_skin_joints': 78, 'raw_TRS_channels': 234, 'guard_keys': 2, 'idle_keys': 181,
                         'idle_rate_hz': 120, 'duration_seconds': DURATION, 'exact_float32_endpoints_match_new_guard': True,
                         'R15_exact_constant_source_v5_UNBAKED': True, 'raw_rest_static_payload_unchanged': True,
                         'base_preview_mesh_and_materials_unchanged': True},
            'once_finger_calibration_and_once_root_shift_max_component_error': {'guard': guard_bake, 'idle': idle_bake},
            'maximum_guard_relative_joint_displacement_metres': displacements,
            'maximum_guard_relative_joint_rotation_degrees': rotations,
            'maximum_actual_steel_vertex_motion_metres': steel_motion,
            'maximum_actual_shoe_sole_plane_error_metres': sole,
            'actual_shoe_reference_plane_metres': floor,
            'maximum_actual_shoe_centre_motion_metres': foot_motion,
            'maximum_bone_length_change_metres': bone,
            'semantic_region_triangle_counts': {label: len(faces) for label, (_, faces) in body.regions.items()},
            'rejection_cases_actually_run': rejected,
            'limits': ['Discrete posed triangle surfaces do not prove continuous-time or volume clearance.',
                       'Anatomical regions require all three vertices to have dominant joints within the named region; adjacent upperarm/neck seams and within-region cloth layers are excluded.',
                       'No family retarget, runtime blend, PICO playback or device acceptance is claimed.',
                       'Small breathing amplitude checks do not approve the rendered aesthetic.'],
            'frames': rows, 'verification_source_pins': {str(path.relative_to(REPO)): digest(path) for path in
                (Path(__file__), Path(base.__file__), Path(utility.__file__), Path(author.__file__), Path(stance.__file__),
                 Path(library.__file__), PRODUCER / 'prepare_rigged_warrior.py')}}


def main():
    require('--threads' in sys.argv and sys.argv[sys.argv.index('--threads') + 1] == '2', 'host two-thread Blender argument required')
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        result = verify()
    except Exception as error:
        result = {'status': 'bounded_base_source_checks_failed', 'error': str(error),
                  'traceback': traceback.format_exc(), 'verification_script': identity(Path(__file__))}
    path = OUT / 'verification_natural_guard.json'
    path.write_text(json.dumps(result, indent=2) + '\n')
    print('NATURAL_GUARD_VERIFICATION', json.dumps({key: value for key, value in result.items() if key not in ('frames', 'verification_source_pins')}, indent=2), flush=True)
    if result['status'].endswith('failed'):
        raise SystemExit(2)


if __name__ == '__main__':
    main()
