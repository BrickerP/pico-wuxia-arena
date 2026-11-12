"""Export motion anchors and mesh-calibrated proxies from the final prepared actor."""

import copy
import math
import struct

import numpy as np
from mathutils import Matrix, Vector

from prepare_rigged_warrior import accessor_bytes, animation_signature, local_matrix, sample_track


ATTACK_PHASES = {
    'start': 0.0,
    'preparation_end': .65,
    'startup_end': .90,
    'contact': 1.0,
    'active_end': 1.10,
    'recovery_end': 1.75,
}
REACTION_PLAYBACK = {'hit_body': (.05, .72), 'hit_head': (.05, .72), 'hit_side': (.05, 1.18)}

LANDMARKS = {
    'head': 'Head',
    'spine02': 'Spine02',
    'hip': 'Hip',
    'blade_base': 'Blade_Base',
    'blade_tip': 'Blade_Tip',
}


def float32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def hierarchy(document):
    nodes = document['nodes']
    parents = {}
    for index, node in enumerate(nodes):
        for child in node.get('children', []):
            if not isinstance(child, int) or not 0 <= child < len(nodes) or child in parents:
                raise ValueError('attack profile requires a single-parent node hierarchy')
            parents[child] = index
    roots = document['scenes'][document.get('scene', 0)]['nodes']
    if (len(roots) != 1 or not isinstance(roots[0], int) or
            not 0 <= roots[0] < len(nodes) or roots[0] in parents):
        raise ValueError('attack profile requires one prepared scene root')
    root = roots[0]
    identity = Matrix.Identity(4)
    actual = local_matrix(nodes[root])
    if max(abs(actual[row][column] - identity[row][column])
           for row in range(4) for column in range(4)) > 1e-6:
        raise ValueError('prepared actor root must have an identity local transform')
    order, visited, visiting = [], set(), set()

    def visit(index):
        if index in visiting:
            raise ValueError('attack profile hierarchy is cyclic')
        if index in visited:
            return
        visiting.add(index)
        if index in parents:
            visit(parents[index])
        visiting.remove(index)
        visited.add(index)
        order.append(index)

    for index in range(len(nodes)):
        visit(index)
    return root, parents, order


def landmark_indices(document, root, parents):
    nodes = document['nodes']
    result = {}
    for name in [*LANDMARKS.values(), 'R_Hand']:
        matches = [index for index, node in enumerate(nodes) if node.get('name') == name]
        if len(matches) != 1:
            raise ValueError('attack profile requires one landmark node: ' + name)
        result[name] = matches[0]
    if len(document.get('skins', [])) != 1:
        raise ValueError('attack profile requires one actor skin')
    joints = set(document['skins'][0]['joints'])
    if not {result[name] for name in ('Head', 'Spine02', 'Hip', 'R_Hand')}.issubset(joints):
        raise ValueError('body landmarks must belong to the actor skin')
    for name, index in result.items():
        ancestors = set()
        current = index
        while current in parents:
            current = parents[current]
            ancestors.add(current)
        if root not in ancestors:
            raise ValueError('landmark is outside the prepared actor root: ' + name)
        if name in ('Blade_Base', 'Blade_Tip') and result['R_Hand'] not in ancestors:
            raise ValueError('blade landmarks must follow the mounted R_Hand hierarchy')
    return result


def animation_tracks(document, binary, animation, require_attack_range=True):
    tracks, timeline = {}, set()
    for channel in animation['channels']:
        target = channel['target']
        index, path = target['node'], target['path']
        if not 0 <= index < len(document['nodes']) or path not in {'translation', 'rotation', 'scale'}:
            raise ValueError('unsupported attack animation target')
        if 'matrix' in document['nodes'][index]:
            raise ValueError('animated glTF nodes require TRS transforms')
        key = index, path
        if key in tracks:
            raise ValueError('duplicate attack animation target')
        sampler = animation['samplers'][channel['sampler']]
        interpolation = sampler.get('interpolation', 'LINEAR')
        if interpolation not in {'LINEAR', 'STEP'}:
            raise ValueError('attack profile requires LINEAR or STEP source curves')
        if document['accessors'][sampler['input']]['type'] != 'SCALAR':
            raise ValueError('attack key times must be scalar')
        width = 4 if path == 'rotation' else 3
        if document['accessors'][sampler['output']]['type'] != ('VEC4' if width == 4 else 'VEC3'):
            raise ValueError('attack animation output type differs from its target')
        times = [row[0] for row in struct.iter_unpack('<f', accessor_bytes(document, binary, sampler['input']))]
        values = list(struct.iter_unpack('<' + 'f' * width, accessor_bytes(document, binary, sampler['output'])))
        if (not times or len(times) != len(values) or
                not all(math.isfinite(value) and value >= 0 for value in times) or
                any(after <= before for before, after in zip(times, times[1:])) or
                not all(math.isfinite(value) for row in values for value in row)):
            raise ValueError('attack curves require finite values and strictly increasing key times')
        if path == 'rotation' and any(sum(value * value for value in row) <= 1e-12 for row in values):
            raise ValueError('attack curve contains a zero quaternion')
        tracks[key] = times, values, interpolation
        timeline.update(times)
    if not timeline:
        raise ValueError('profile reference animation has no source timeline')
    if require_attack_range and (min(timeline) != 0.0 or max(timeline) != float32(1.75)):
        raise ValueError('attack profile source range must be 0 to 1.75 seconds')
    return tracks, timeline


def pose_world(document, tracks, time, parents, order):
    sampled = {}
    for (index, path), track in tracks.items():
        node = sampled.setdefault(index, dict(document['nodes'][index]))
        node[path] = sample_track(track, time, path == 'rotation')
    world = {}
    for index in order:
        node = sampled.get(index, document['nodes'][index])
        local = local_matrix(node)
        parent = parents.get(index)
        world[index] = world[parent] @ local if parent is not None else local
    return world


def skin_attribute(document, binary, index):
    """Read the embedded skin streams, including normalized integer weights."""
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    if ('sparse' in accessor or view['buffer'] != 0 or
            accessor['componentType'] not in {5121, 5123, 5125, 5126} or
            accessor['type'] not in {'SCALAR', 'VEC3', 'VEC4', 'MAT4'}):
        raise ValueError('proxy calibration requires embedded nonsparse skin attributes')
    dtype = np.dtype({5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[accessor['componentType']])
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[accessor['type']]
    stride = view.get('byteStride', width * dtype.itemsize)
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    end = start + (accessor['count'] - 1) * stride + width * dtype.itemsize
    if (accessor['count'] < 1 or stride < width * dtype.itemsize or start < 0 or
            end > view.get('byteOffset', 0) + view['byteLength'] or end > len(binary)):
        raise ValueError('proxy skin attribute exceeds its buffer view')
    values = np.ndarray((accessor['count'], width), dtype=dtype, buffer=binary,
                        offset=start, strides=(stride, dtype.itemsize)).copy()
    if accessor.get('normalized'):
        if dtype.kind != 'u':
            raise ValueError('normalized proxy skin data must use unsigned integers')
        values = values.astype(float) / np.iinfo(dtype).max
    if not np.isfinite(values).all():
        raise ValueError('proxy skin attributes must be finite')
    return values


def mesh_proxy_calibration(document, binary, world, landmarks, parents):
    """Measure the final LBS body; the appended same-skin dao is excluded explicitly."""
    skin = document['skins'][0]
    joints = skin['joints']
    mesh_nodes = [node for node in document['nodes'] if 'mesh' in node]
    if len(mesh_nodes) != 1 or mesh_nodes[0].get('skin') != 0:
        raise ValueError('proxy calibration requires the one prepared skinned body mesh')
    mesh = document['meshes'][mesh_nodes[0]['mesh']]
    body_indices = mesh.get('extras', {}).get('body_primitive_indices')
    if (not isinstance(body_indices, list) or not body_indices or
            any(type(index) is not int or not 0 <= index < len(mesh['primitives']) for index in body_indices) or
            len(set(body_indices)) != len(body_indices)):
        raise ValueError('proxy calibration requires explicit body primitive indices excluding the dao')
    streams = {}
    for index in body_indices:
        primitive = mesh['primitives'][index]
        if primitive.get('mode', 4) != 4 or primitive.get('targets'):
            raise ValueError('proxy calibration requires triangle body primitives without morph targets')
        attributes = primitive['attributes']
        identity = tuple(attributes[name] for name in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
        positions = document['accessors'][identity[0]]
        palettes = document['accessors'][identity[1]]
        weights = document['accessors'][identity[2]]
        if (positions['type'] != 'VEC3' or positions['componentType'] != 5126 or positions.get('normalized') or
                palettes['type'] != 'VEC4' or palettes['componentType'] not in {5121, 5123} or palettes.get('normalized') or
                weights['type'] != 'VEC4' or weights['componentType'] not in {5121, 5123, 5126} or
                (weights['componentType'] != 5126 and not weights.get('normalized')) or
                'JOINTS_1' in attributes or 'WEIGHTS_1' in attributes):
            raise ValueError('proxy calibration requires normalized nonnegative four-weight skinning')
        if 'indices' in primitive:
            accessor = document['accessors'][primitive['indices']]
            if accessor['type'] != 'SCALAR' or accessor['componentType'] not in {5121, 5123, 5125} or accessor.get('normalized'):
                raise ValueError('proxy body triangle indices must be unsigned integers')
            indices = skin_attribute(document, binary, primitive['indices']).reshape(-1)
            if len(indices) % 3 or indices.max() >= positions['count']:
                raise ValueError('proxy body triangle indices exceed the position stream')
        else:
            indices = range(positions['count'])
            if positions['count'] % 3:
                raise ValueError('proxy body requires complete triangles')
        streams.setdefault(identity, set()).update(int(index) for index in indices)
    points, palettes, weights = [], [], []
    for identity, selected in streams.items():
        p, j, w = (skin_attribute(document, binary, index) for index in identity)
        if (len(p) != len(j) or j.shape != w.shape or j.min() < 0 or j.max() >= len(joints) or
                w.min() < 0 or np.max(np.abs(w.sum(axis=1) - 1)) > 1e-4):
            raise ValueError('proxy calibration requires normalized nonnegative four-weight skinning')
        selected = sorted(selected)
        points.append(p[selected])
        palettes.append(j[selected].astype(int))
        weights.append(w[selected].astype(float) / w[selected].sum(axis=1)[:, None])
    points, palettes, weights = np.concatenate(points), np.concatenate(palettes), np.concatenate(weights)
    inverse = document['accessors'][skin['inverseBindMatrices']]
    if inverse['type'] != 'MAT4' or inverse['componentType'] != 5126 or inverse.get('normalized'):
        raise ValueError('proxy calibration requires FLOAT inverse bind matrices')
    binds = skin_attribute(document, binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    if len(binds) != len(joints):
        raise ValueError('proxy inverse-bind count differs from joint count')
    matrices = np.array([list(world[index]) for index in joints]) @ binds
    homogeneous = np.column_stack((points, np.ones(len(points))))
    deformed = np.sum(np.einsum('vsij,vj->vsi', matrices[palettes], homogeneous) * weights[:, :, None], axis=1)[:, :3]
    if not np.isfinite(deformed).all():
        raise ValueError('proxy calibration produced non-finite LBS surface positions')
    head_nodes = {landmarks['Head']}
    for index in joints:
        current = index
        while current in parents and current not in head_nodes:
            current = parents[current]
        if current in head_nodes:
            head_nodes.add(index)
    regions = {'head': head_nodes,
               'body': {index for index in joints if document['nodes'][index]['name'] in
                        {'Hip', 'Waist', 'Spine01', 'Spine02'}}}
    bounds, centres = {}, {}
    for name, nodes in regions.items():
        palette_indices = [palette for palette, index in enumerate(joints) if index in nodes]
        mask = np.sum(weights * np.isin(palettes, palette_indices), axis=1) > .5
        if not mask.any():
            raise ValueError('proxy calibration requires measured ' + name + ' surface vertices')
        low, high = deformed[mask].min(axis=0), deformed[mask].max(axis=0)
        centre = (low + high) / 2
        bounds[name] = {'min': low.tolist(), 'max': high.tolist(), 'vertex_count': int(mask.sum()),
                        'joint_names': [document['nodes'][index]['name'] for index in joints if index in nodes]}
        if name == 'head':
            centres['head'] = Vector(centre)
        else:
            centres['body_bottom'] = Vector((centre[0], low[1], centre[2]))
            centres['body_top'] = Vector((centre[0], high[1], centre[2]))
    return centres, {'method': 'final idle LBS anatomical-region AABB; head centre and torso vertical-axis endpoints',
                     'region_selection': 'rendered body vertices with summed selected-joint skin weight > 0.5',
                     'body_primitive_indices': list(body_indices), 'anatomical_bounds_metres': bounds,
                     'scope': 'mesh proxy calibration only; damage radii and contact rules are unchanged'}


def locomotion_source_contract(frozen):
    """Use the locked manifest's six-step contract without accepting legacy gait timing."""
    if not isinstance(frozen, dict):
        raise ValueError('profile schema 3 requires the frozen locomotion source contract')
    runtime = frozen.get('runtime_contract', {})
    rows = frozen.get('profiles', [])
    profiles = {row.get('clip_alias'): row for row in rows}
    if len(rows) != 2 or set(profiles) != {'idle', 'walk'}:
        raise ValueError('locomotion source contract requires exactly idle and walk profiles')
    walk = profiles['walk']
    expected = {'WALK_STRIDE_METERS': 1.45, 'WALK_LOOP_START': 1 / 3,
                'WALK_LOOP_DURATION': 7 / 6, 'physical_steps_per_loop': 6}
    if any(runtime.get(name) != value for name, value in expected.items()):
        raise ValueError('locomotion profile requires the locked six-step stride and loop timing')
    phase_intervals = walk.get('stance_intervals_seconds', {})
    phase_times = [1 / 3 + index * (7 / 6) / 6 for index in range(7)]
    for side, offset in [('L_', 0), ('R_', 1)]:
        intervals = phase_intervals.get(side, [])
        wanted = [[phase_times[index], phase_times[index + 1]] for index in range(offset, 6, 2)]
        if (len(intervals) != 3 or any(len(actual) != 2 or any(
                not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value - desired) > 1e-9
                for value, desired in zip(actual, target)) for actual, target in zip(intervals, wanted))):
            raise ValueError('locomotion source contract has invalid six-step contact phases')
    for name, row in profiles.items():
        if (row.get('source_range_seconds') != [0, 1.5] or
                row.get('source_loop_seconds') != [1 / 3, 1.5] or
                row.get('source_loop_duration_seconds') != 7 / 6 or
                row.get('raw', {}).get('right_finger_calibration_baked') is not False):
            raise ValueError('locomotion profile requires the unbaked locked source domain: ' + name)
    return {'contract': 'locomotion78', 'source_rig_sha256': frozen['source_rig']['sha256'],
            'raw_source_sha256': {name: row['raw']['sha256'] for name, row in profiles.items()},
            'source_range_seconds': [0.0, 1.5],
            'loop_start_seconds': 1 / 3, 'loop_end_seconds': 1.5, 'loop_duration_seconds': 7 / 6,
            'stride_metres': 1.45, 'steps_per_loop': 6, 'step_pairs_per_loop': 3,
            'distance_per_step_metres': 1.45 / 6,
            'contact_phases': copy.deepcopy(phase_intervals),
            'contact_source_seconds': phase_times,
            'swing_intervals_seconds': copy.deepcopy(walk['swing_intervals_seconds']),
            'source_time_formula': runtime['source_time_formula']}, profiles


def preserve_body_coverage(centres, world, landmarks, contract):
    """Rebind the existing capsule's bone-relative Y coverage; measure XZ on the mesh."""
    if not isinstance(contract, dict) or contract.get('space') != 'prepared actor root':
        raise ValueError('body coverage requires an explicit prepared actor root source contract')
    source = contract.get('source_profile', {})
    if (not isinstance(source.get('path'), str) or not source['path'] or
            any(not isinstance(source.get(field), str) or len(source[field]) != 64 or
                any(character not in '0123456789abcdef' for character in source[field])
                for field in ('sha256', 'model_sha256'))):
        raise ValueError('body coverage requires pinned prior profile and model identities')
    previous = contract.get('idle_centres_metres', {})
    reference = contract.get('idle_reference', {})
    bindings = {'body_bottom': ('Hip', 'hip'), 'body_top': ('Spine02', 'spine02')}
    if any(not isinstance(values.get(key), (list, tuple)) or len(values[key]) != 3 or
           any(type(value) not in (int, float) or not math.isfinite(value) for value in values[key])
           for field, (_, reference_key) in bindings.items()
           for values, key in ((previous, field), (reference, reference_key))):
        raise ValueError('body coverage requires finite prior idle centres and bone anchors')
    if previous['body_bottom'][1] >= previous['body_top'][1]:
        raise ValueError('body coverage requires ordered prior vertical endpoints')
    result = {field: point.copy() for field, point in centres.items()}
    anchors = {}
    for field, (name, reference_key) in bindings.items():
        current_y = float(world[landmarks[name]].translation.y)
        prior_y = reference[reference_key][1]
        result[field].y = previous[field][1] + current_y - prior_y
        anchors[field] = {'bone': name, 'prior_idle_bone_y_metres': prior_y,
                          'canonical_guard_bone_y_metres': current_y,
                          'prior_coverage_y_metres': previous[field][1],
                          'adopted_coverage_y_metres': float(result[field].y)}
    if result['body_bottom'].y >= result['body_top'].y:
        raise ValueError('rebound body coverage has crossed vertical endpoints')
    return result, {
        'method': 'prior coverage Y + current canonical guard bone Y - prior idle bone Y; no clamp',
        'horizontal_policy': 'XZ measured from final idle LBS torso-region AABB axis',
        'space': 'prepared actor root before the runtime entity transform and its one +0.028m lift',
        'canonical_reference': {'clip': 'idle', 'source_seconds': 0.0},
        'source_contract': copy.deepcopy(contract), 'anchors': anchors,
        'source_identity_role': 'historical provenance; source_profile.path is not read during production',
        'scope': 'preserves existing bone-relative body Y coverage; does not claim vertical mesh fit or alter damage radii/rules',
    }


def profile_sample(document, tracks, time, parents, order, landmarks, offsets):
    world = pose_world(document, tracks, time, parents, order)
    row = {'time_seconds': time, 'source_seconds': time}
    for field, name in LANDMARKS.items():
        position = list(world[landmarks[name]].translation)
        if not all(math.isfinite(value) for value in position):
            raise ValueError('motion profile contains a non-finite landmark')
        row[field] = position
    row['head_origin'] = list(row['head'])
    for field, name in {'head': 'Head', 'body_bottom': 'Hip', 'body_top': 'Spine02'}.items():
        row[field] = list(world[landmarks[name]] @ offsets[field])
    row['bone_rotation_xyzw'] = {}
    for name in ('Head', 'Spine02', 'Hip'):
        q = world[landmarks[name]].to_quaternion().normalized()
        row['bone_rotation_xyzw'][name] = [q.x, q.y, q.z, q.w]
    row['torso_lower'] = list(row['hip'])
    row['torso_upper'] = list(row['spine02'])
    return row


def export_reaction_profiles(document, binary, root, parents, order, landmarks, offsets):
    """Sample the existing hurt clips with the same frozen bone-local proxy calibration."""
    animations = {animation['name']: animation for animation in document.get('animations', [])}
    if len(animations) != len(document.get('animations', [])):
        raise ValueError('motion clip names must be unique')
    result = {}
    for name, playback in REACTION_PLAYBACK.items():
        if name not in animations:
            raise ValueError('reaction clip is absent from the prepared actor: ' + name)
        animation = animations[name]
        tracks, keys = animation_tracks(document, binary, animation, require_attack_range=False)
        if any(index == root for index, _ in tracks):
            raise ValueError('prepared actor root cannot be animated')
        start, end = min(keys), max(keys)
        if start > playback[0] or end < playback[1]:
            raise ValueError('reaction source does not cover its current playback window: ' + name)
        times = sorted({float32(time) for time in [*keys, *playback,
            *[frame / 60 for frame in range(math.ceil(start * 60), math.floor(end * 60) + 1)]]})
        result[name] = {
            'clip': name, 'source_range_seconds': [start, end],
            'playback_range_seconds': list(playback),
            'animation_semantics_sha256': animation_signature(document, binary, animation),
            'samples': [profile_sample(document, tracks, time, parents, order, landmarks, offsets) for time in times],
        }
    return result


def export_attack_profiles(document, binary, attack_clips, locomotion_contract, body_coverage_contract):
    """Return schema-3 motion and hurt anchors with one final-idle mesh calibration.

    Blade markers follow the same R_Hand mount used to bake rigid weapon skinning.
    Radius selection and player-view LEFT/RIGHT classification belong to the caller.
    """
    if set(attack_clips) != {'OVERHEAD', 'LEFT', 'RIGHT'} or len(set(attack_clips.values())) != 3:
        raise ValueError('attack profile requires distinct OVERHEAD, LEFT and RIGHT clips')
    source_contract, frozen_profiles = locomotion_source_contract(locomotion_contract)
    root, parents, order = hierarchy(document)
    landmarks = landmark_indices(document, root, parents)
    animations = {animation['name']: animation for animation in document.get('animations', [])}
    if len(animations) != len(document.get('animations', [])):
        raise ValueError('motion clip names must be unique')
    if not {'idle', 'walk'}.issubset(animations):
        raise ValueError('schema 3 proxy calibration requires final idle and walk clips')
    idle_tracks, idle_times = animation_tracks(document, binary, animations['idle'], require_attack_range=False)
    if min(idle_times) != 0 or max(idle_times) != float32(1.5):
        raise ValueError('locomotion profile source range must be 0 to 1.5 seconds')
    idle_world = pose_world(document, idle_tracks, 0.0, parents, order)
    surface_centres, measurement = mesh_proxy_calibration(document, binary, idle_world, landmarks, parents)
    measurement['surface_axis_centres_metres'] = {field: list(point) for field, point in surface_centres.items()}
    centres, coverage = preserve_body_coverage(surface_centres, idle_world, landmarks, body_coverage_contract)
    targets = {'head': 'Head', 'body_bottom': 'Hip', 'body_top': 'Spine02'}
    offsets = {field: idle_world[landmarks[name]].inverted() @ centres[field] for field, name in targets.items()}
    profiles = {}
    for direction, clip in attack_clips.items():
        if clip not in animations:
            raise ValueError('attack clip is absent from the prepared actor: ' + clip)
        animation = animations[clip]
        tracks, source_times = animation_tracks(document, binary, animation)
        if any(index == root for index, _ in tracks):
            raise ValueError('prepared actor root cannot be animated')
        times = sorted({float32(time) for time in
                        [*source_times, *ATTACK_PHASES.values(), *[frame / 60 for frame in range(106)]]})
        profiles[direction] = {
            'clip': clip, 'source_range_seconds': [0.0, 1.75],
            'source_phase_seconds': [0.0, .65, .90, 1.10, 1.75], 'contact_source_seconds': 1.0,
            'animation_semantics_sha256': animation_signature(document, binary, animation),
            'samples': [profile_sample(document, tracks, time, parents, order, landmarks, offsets) for time in times],
        }
    locomotion = {}
    for name in ('idle', 'walk'):
        animation = animations[name]
        tracks, source_times = animation_tracks(document, binary, animation, require_attack_range=False)
        if min(source_times) != 0 or max(source_times) != float32(1.5):
            raise ValueError('locomotion profile source range must be 0 to 1.5 seconds')
        if any(index == root for index, _ in tracks):
            raise ValueError('prepared actor root cannot be animated')
        keys = sorted(source_times)
        times = sorted({float32(time) for time in
                        [*keys, *((a + b) / 2 for a, b in zip(keys, keys[1:])),
                         *source_contract['contact_source_seconds'], *[frame / 60 for frame in range(91)]]})
        source = frozen_profiles[name]
        locomotion[name] = {'clip': name, 'source_range_seconds': [0.0, 1.5],
                            'source_loop_seconds': [1 / 3, 1.5], 'source_loop_duration_seconds': 7 / 6,
                            'stance_intervals_seconds': copy.deepcopy(source['stance_intervals_seconds']),
                            'swing_intervals_seconds': copy.deepcopy(source['swing_intervals_seconds']),
                            'animation_semantics_sha256': animation_signature(document, binary, animation),
                            'samples': [profile_sample(document, tracks, time, parents, order, landmarks, offsets)
                                        for time in times]}
    return {
        'schema_version': 3, 'units': 'metres', 'space': 'prepared actor root',
        'axes': {'up': '+Y', 'forward': '+Z', 'actor_left': '+X'},
        'landmark_nodes': dict(LANDMARKS),
        'torso_anchor_nodes': {'lower': 'Hip', 'upper': 'Spine02'},
        'proxy_calibration': {'clip': 'idle', 'source_seconds': 0.0,
                              'idle_centres_metres': {field: list(point) for field, point in centres.items()},
                              'bone_local_offsets': {field: list(point) for field, point in offsets.items()},
                              'measurement': measurement, 'body_coverage': coverage,
                              'coordinate_frame': 'prepared actor root; bone_local_offsets are local to the named bones'},
        'idle_reference': {field: list(idle_world[landmarks[name]].translation)
                           for field, name in LANDMARKS.items() if name in ('Head', 'Spine02', 'Hip')},
        'phase_markers_seconds': dict(ATTACK_PHASES),
        'phase_sample_times_seconds': {name: float32(time) for name, time in ATTACK_PHASES.items()},
        'sample_rate_hz': 60, 'time_encoding': 'float32 source-key/60Hz/phase union; locomotion includes source-key midpoints',
        'direction_labels': 'caller supplied; player-view incoming side requires geometric review',
        'source_contract': source_contract, 'locomotion': locomotion, 'attacks': profiles,
        'reactions': export_reaction_profiles(document, binary, root, parents, order, landmarks, offsets),
    }
