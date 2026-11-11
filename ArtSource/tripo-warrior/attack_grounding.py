"""Constrain each derived attack's lowest skinned sole with one root translation."""

import copy
import struct

import numpy as np
from mathutils import Vector

from attack_profiles import animation_tracks, hierarchy, pose_world
from prepare_rigged_warrior import animation_signature


GROUNDING_POLICY = {
    'version': 1,
    'method': 'prepared +Y whole BoneRoot translation at unchanged source keys',
    'target_plane_metres': -.028,
    'region': 'body vertices with total same-side Foot/Toe skin weight greater than 0.5',
    'midpoint_tolerance_metres': .001,
    'scope': 'three attacks only; no per-foot IK or horizontal slip correction',
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


def ground_attack_feet(document, binary, clip_names):
    """Return appended bytes and evidence, changing only attack root translation outputs.

    The lower of the two measured foot surfaces is constrained. A raised opposite
    foot retains its authored relative height, and horizontal foot slip is unchanged.
    """
    _, parents, order = hierarchy(document)
    roots = [index for index, node in enumerate(document['nodes']) if node.get('name') == 'BoneRoot']
    if len(roots) != 1 or roots[0] not in parents:
        raise ValueError('grounding requires one parented BoneRoot')
    root = roots[0]
    surface = foot_surface(document, binary, parents, root)
    clips = {animation['name']: animation for animation in document['animations']}
    if len(set(clip_names)) != 3 or not set(clip_names).issubset(clips):
        raise ValueError('grounding requires the three distinct derived attack clips')
    packed = bytearray(binary)
    reports = []
    plane = GROUNDING_POLICY['target_plane_metres']
    for name in clip_names:
        animation = clips[name]
        tracks, timeline = animation_tracks(document, packed, animation)
        if len(timeline) != 106:
            raise ValueError('grounding requires the frozen 106-key attack timeline')
        key = (root, 'translation')
        channels = [channel for channel in animation['channels'] if
                    (channel['target']['node'], channel['target']['path']) == key]
        if len(channels) != 1 or key not in tracks:
            raise ValueError('grounding requires one BoneRoot translation channel')
        times, original, interpolation = tracks[key]
        if set(times) != timeline or interpolation != 'LINEAR':
            raise ValueError('grounding requires LINEAR root translation at all source keys')
        report = {'clip': name, 'before_semantics_sha256': animation_signature(document, packed, animation),
                  'foot_vertex_counts': {side: int(mask.sum()) for side, mask in surface[3].items()},
                  'key_count': len(times), 'midpoint_count': len(times) - 1, 'samples': []}
        values, before_heights = [], {}
        for time, location in zip(times, original):
            world = pose_world(document, tracks, time, parents, order)
            heights = surface_heights(document, world, surface)
            before_heights[time] = heights
            shift = plane - min(heights.values())
            local_shift = world[parents[root]].to_3x3().inverted() @ Vector((0, shift, 0))
            values.append(tuple(Vector(location) + local_shift))
        corrected = copy.copy(tracks)
        corrected[key] = (times, values, interpolation)
        samples = sorted([*times, *((a + b) / 2 for a, b in zip(times, times[1:]))])
        max_error = 0.0
        for time in samples:
            before = before_heights.get(time)
            if before is None:
                before = surface_heights(document, pose_world(document, tracks, time, parents, order), surface)
            after = surface_heights(document, pose_world(document, corrected, time, parents, order), surface)
            error = abs(min(after.values()) - plane)
            max_error = max(max_error, error)
            report['samples'].append({'source_seconds': time, 'source_key': time in timeline,
                                      'before_foot_min_metres': before, 'after_foot_min_metres': after,
                                      'root_shift_metres': min(after.values()) - min(before.values()),
                                      'opposite_foot_above_plane_metres': max(after.values()) - plane})
        if max_error > GROUNDING_POLICY['midpoint_tolerance_metres']:
            raise ValueError('root-only grounding exceeds midpoint plane tolerance: ' + name)
        report['maximum_plane_error_metres'] = max_error
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
        animation['samplers'][channels[0]['sampler']]['output'] = accessor
        report['after_semantics_sha256'] = animation_signature(document, packed, animation)
        reports.append(report)
    document['buffers'][0]['byteLength'] = len(packed)
    return bytes(packed), {'policy': copy.deepcopy(GROUNDING_POLICY), 'clips': reports}
