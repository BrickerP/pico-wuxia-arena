"""Keep the five canonical guard clips on one measured target grounding frame."""

import copy
import struct

import numpy as np
from mathutils import Vector

from attack_profiles import animation_tracks, hierarchy, pose_world
from prepare_rigged_warrior import animation_signature


GROUNDING_POLICY = {
    'version': 2,
    'method': 'one constant prepared +Y BoneRoot translation from target idle at source zero',
    'target_plane_metres': -.028,
    'region': 'body vertices with total same-side Foot/Toe skin weight greater than 0.5',
    'canonical_clip': 'idle',
    'canonical_source_seconds': 0.0,
    'scope': 'idle, walk and three attacks share one target guard shift; no per-frame grounding or IK',
    'residual_policy': 'measure keys and midpoints without modifying authored relative foot heights',
    'runtime_entity_lift_metres': .028,
    'runtime_entity_lift_application_count': 1,
}


def read_attribute(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    if 'sparse' in accessor or view['buffer'] != 0:
        raise ValueError('grounding requires embedded nonsparse skin attributes')
    dtype = np.dtype({5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[accessor['componentType']])
    width = {'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[accessor['type']]
    stride = view.get('byteStride', width * dtype.itemsize)
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    end = start + (accessor['count'] - 1) * stride + width * dtype.itemsize
    if (accessor['count'] < 1 or stride < width * dtype.itemsize or
            end > view.get('byteOffset', 0) + view['byteLength'] or end > len(binary)):
        raise ValueError('grounding skin attribute exceeds its buffer view')
    values = np.ndarray((accessor['count'], width), dtype=dtype, buffer=binary,
                        offset=start, strides=(stride, dtype.itemsize)).copy()
    if accessor.get('normalized'):
        values = values.astype(float) / np.iinfo(dtype).max
    if not np.isfinite(values).all():
        raise ValueError('grounding skin attributes must be finite')
    return values


def foot_surface(document, binary, parents, root):
    skin = document['skins'][0]
    joints = skin['joints']
    for joint in joints:
        ancestor = joint
        while ancestor != root and ancestor in parents:
            ancestor = parents[ancestor]
        if ancestor != root:
            raise ValueError('whole-body grounding requires all skin joints below BoneRoot')
    foot_joints = {side: [palette for palette, index in enumerate(joints)
                          if document['nodes'][index]['name'].startswith((side + '_Foot', side + '_Toe'))]
                   for side in ('L', 'R')}
    mesh_nodes = [node for node in document['nodes'] if 'mesh' in node]
    if len(mesh_nodes) != 1 or mesh_nodes[0].get('skin') != 0:
        raise ValueError('grounding requires the one body mesh before dao append')
    points, palettes, weights, masks = [], [], [], {'L': [], 'R': []}
    seen = set()
    for primitive in document['meshes'][mesh_nodes[0]['mesh']]['primitives']:
        attributes = primitive['attributes']
        identity = tuple(attributes[name] for name in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
        if identity in seen:
            continue
        seen.add(identity)
        positions = read_attribute(document, binary, attributes['POSITION']).astype(float)
        palette = read_attribute(document, binary, attributes['JOINTS_0']).astype(int)
        weight = read_attribute(document, binary, attributes['WEIGHTS_0']).astype(float)
        if (palette.shape != weight.shape or len(palette) != len(positions) or
                palette.min() < 0 or palette.max() >= len(joints) or weight.min() < 0 or
                np.max(np.abs(weight.sum(axis=1) - 1)) > 1e-4):
            raise ValueError('grounding requires normalized nonnegative four-weight skinning')
        weight /= weight.sum(axis=1)[:, None]
        side_masks = {side: np.sum(weight * np.isin(palette, indices), axis=1) > .5
                      for side, indices in foot_joints.items()}
        selected = side_masks['L'] | side_masks['R']
        points.append(positions[selected])
        palettes.append(palette[selected])
        weights.append(weight[selected])
        for side in masks:
            masks[side].append(side_masks[side][selected])
    points = np.concatenate(points)
    masks = {side: np.concatenate(rows) for side, rows in masks.items()}
    if not all(mask.any() for mask in masks.values()):
        raise ValueError('grounding requires measured surface vertices on both feet')
    binds = read_attribute(document, binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    if len(binds) != len(joints):
        raise ValueError('grounding inverse-bind count differs from joint count')
    return (np.column_stack((points, np.ones(len(points)))), np.concatenate(palettes),
            np.concatenate(weights), masks, binds)


def surface_heights(document, world, surface):
    points, palettes, weights, masks, binds = surface
    matrices = np.array([list(world[index]) for index in document['skins'][0]['joints']]) @ binds
    heights = np.sum(np.einsum('vsj,vj->vs', matrices[palettes, 1, :], points) * weights, axis=1)
    return {side: float(heights[mask].min()) for side, mask in masks.items()}


CANONICAL_CLIPS = ('idle', 'walk', 'attack_overhead', 'attack_left', 'attack_right')
LOCKED_CHAIN = ('Armature', 'BoneRoot', 'Hip', 'Waist', 'Spine01', 'Spine02',
                'NeckTwist01', 'NeckTwist02', 'Head')


def grounding_tracks(document, binary, animation, root, expected_times):
    name = animation['name']
    locomotion = name in {'idle', 'walk'}
    tracks, timeline = animation_tracks(document, binary, animation, require_attack_range=not locomotion)
    if sorted(timeline) != list(expected_times):
        raise ValueError('grounding requires the frozen source timeline: ' + name)
    key = root, 'translation'
    channels = [channel for channel in animation['channels'] if
                (channel['target']['node'], channel['target']['path']) == key]
    if len(channels) != 1 or key not in tracks:
        raise ValueError('grounding requires one BoneRoot translation channel')
    times, values, interpolation = tracks[key]
    expected_interpolation = 'STEP' if locomotion else 'LINEAR'
    if set(times) != timeline or interpolation != expected_interpolation:
        raise ValueError('grounding requires unchanged ' + expected_interpolation + ' root keys: ' + name)
    return tracks, times, values, channels[0]['sampler']


def ground_canonical_guard_feet(document, binary, clip_timelines):
    """Shift the whole canonical family by its target idle's one measured +Y offset.

    Only BoneRoot translation outputs are appended. Keeping the same constant
    shift on every source key preserves authored head locks, guard endpoints and
    relative foot heights, including any residual from different target shapes.
    """
    clips = {animation['name']: animation for animation in document['animations']}
    if len(clips) != len(document['animations']):
        raise ValueError('grounding requires unique clip names')
    if (not isinstance(clip_timelines, dict) or set(clip_timelines) != set(CANONICAL_CLIPS) or
            not set(clip_timelines).issubset(clips)):
        raise ValueError('grounding requires the five distinct canonical guard clips')
    _, parents, order = hierarchy(document)
    roots = [index for index, node in enumerate(document['nodes']) if node.get('name') == 'BoneRoot']
    if len(roots) != 1 or roots[0] not in parents:
        raise ValueError('grounding requires one parented BoneRoot')
    root = roots[0]
    surface = foot_surface(document, binary, parents, root)
    decoded = {name: grounding_tracks(document, binary, clips[name], root, clip_timelines[name])
               for name in CANONICAL_CLIPS}
    canonical_world = pose_world(document, decoded['idle'][0], 0.0, parents, order)
    canonical_heights = surface_heights(document, canonical_world, surface)
    plane = GROUNDING_POLICY['target_plane_metres']
    shift = plane - min(canonical_heights.values())
    parent_frame = canonical_world[parents[root]].to_3x3()
    local_shift = parent_frame.inverted() @ Vector((0, shift, 0))
    packed = bytearray(binary)
    reports = []
    idle_tracks, idle_times, idle_values, _ = decoded['idle']
    grounded_idle_tracks = copy.copy(idle_tracks)
    grounded_idle_tracks[root, 'translation'] = (idle_times,
        [struct.unpack('<3f', struct.pack('<3f', *(Vector(row) + local_shift))) for row in idle_values], 'STEP')
    grounded_canonical_world = pose_world(document, grounded_idle_tracks, 0.0, parents, order)
    chain = {node.get('name'): index for index, node in enumerate(document['nodes'])
             if node.get('name') in LOCKED_CHAIN}
    guard_nodes = {node.get('name'): index for index, node in enumerate(document['nodes'])
                   if node.get('name') in {'BoneRoot', 'Hip', 'Spine02', 'Head', 'L_Hand', 'R_Hand'}}
    for name in CANONICAL_CLIPS:
        animation = clips[name]
        tracks, times, original, sampler_index = decoded[name]
        interpolation = tracks[root, 'translation'][2]
        # Store FLOAT values before measurement so the report describes encoded curves.
        values = [struct.unpack('<3f', struct.pack('<3f', *(Vector(location) + local_shift)))
                  for location in original]
        corrected = copy.copy(tracks)
        corrected[root, 'translation'] = times, values, interpolation
        samples = sorted([*times, *((a + b) / 2 for a, b in zip(times, times[1:]))])
        report = {'clip': name, 'before_semantics_sha256': animation_signature(document, binary, animation),
                  'foot_vertex_counts': {side: int(mask.sum()) for side, mask in surface[3].items()},
                  'key_count': len(times), 'midpoint_count': len(times) - 1,
                  'root_interpolation': interpolation, 'constant_world_root_shift_metres': shift,
                  'constant_local_root_shift': list(local_shift), 'samples': [], 'guard_endpoints': [],
                  'maximum_locked_chain_difference_from_idle_guard': {joint: 0.0 for joint in chain},
                  'maximum_grounded_locked_chain_difference_from_idle_guard': {joint: 0.0 for joint in chain}}
        for time in samples:
            before_world = pose_world(document, tracks, time, parents, order)
            if max(abs(before_world[parents[root]][row][col] - parent_frame[row][col])
                   for row in range(3) for col in range(3)) > 1e-6:
                raise ValueError('one canonical root shift requires a fixed root parent frame: ' + name)
            after_world = pose_world(document, corrected, time, parents, order)
            before = surface_heights(document, before_world, surface)
            after = surface_heights(document, after_world, surface)
            report['samples'].append({'source_seconds': time, 'source_key': time in times,
                                      'before_foot_min_metres': before, 'after_foot_min_metres': after,
                                      'foot_plane_residual_metres': {side: height - plane for side, height in after.items()},
                                      'root_shift_metres': min(after.values()) - min(before.values()),
                                      'opposite_foot_above_plane_metres': max(after.values()) - plane})
            for joint, index in chain.items():
                difference = max(abs(before_world[index][row][col] - canonical_world[index][row][col])
                                 for row in range(4) for col in range(4))
                report['maximum_locked_chain_difference_from_idle_guard'][joint] = max(
                    report['maximum_locked_chain_difference_from_idle_guard'][joint], difference)
                grounded_difference = max(abs(after_world[index][row][col] - grounded_canonical_world[index][row][col])
                                          for row in range(4) for col in range(4))
                report['maximum_grounded_locked_chain_difference_from_idle_guard'][joint] = max(
                    report['maximum_grounded_locked_chain_difference_from_idle_guard'][joint], grounded_difference)
            if time == times[0] or time == times[-1]:
                report['guard_endpoints'].append({'source_seconds': time,
                    'before_foot_min_metres': before, 'after_foot_min_metres': after,
                    'world_position_difference_from_idle_guard_metres': {
                        joint: list(before_world[index].translation - canonical_world[index].translation)
                        for joint, index in guard_nodes.items()},
                    'grounded_world_position_difference_from_idle_guard_metres': {
                        joint: list(after_world[index].translation - grounded_canonical_world[index].translation)
                        for joint, index in guard_nodes.items()}})
        report['maximum_plane_error_metres'] = max(
            abs(min(sample['after_foot_min_metres'].values()) - plane) for sample in report['samples'])
        report['maximum_opposite_foot_height_metres'] = max(
            sample['opposite_foot_above_plane_metres'] for sample in report['samples'])
        packed.extend(b'\0' * (-len(packed) % 4))
        start = len(packed)
        for location in values:
            packed.extend(struct.pack('<3f', *location))
        view = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(values) * 12})
        accessor = len(document['accessors'])
        document['accessors'].append({'bufferView': view, 'componentType': 5126, 'type': 'VEC3',
                                      'count': len(values),
                                      'min': [min(row[axis] for row in values) for axis in range(3)],
                                      'max': [max(row[axis] for row in values) for axis in range(3)]})
        animation['samplers'][sampler_index]['output'] = accessor
        report['after_semantics_sha256'] = animation_signature(document, packed, animation)
        reports.append(report)
    document['buffers'][0]['byteLength'] = len(packed)
    return bytes(packed), {'policy': copy.deepcopy(GROUNDING_POLICY),
                           'canonical_foot_min_metres_before': canonical_heights,
                           'constant_world_root_shift_metres': shift,
                           'constant_local_root_shift': list(local_shift), 'clips': reports}
