"""Export attack anchors from the final prepared actor's actual glTF curves."""

import math
import struct

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


def export_attack_profiles(document, binary, attack_clips):
    """Return JSON-ready prepared actor-root anchors for the three supplied bank labels.

    Blade markers follow the same R_Hand mount used to bake rigid weapon skinning.
    Radius selection and player-view LEFT/RIGHT classification belong to the caller.
    """
    if set(attack_clips) != {'OVERHEAD', 'LEFT', 'RIGHT'} or len(set(attack_clips.values())) != 3:
        raise ValueError('attack profile requires distinct OVERHEAD, LEFT and RIGHT clips')
    root, parents, order = hierarchy(document)
    landmarks = landmark_indices(document, root, parents)
    animations = {animation['name']: animation for animation in document.get('animations', [])}
    if len(animations) != len(document.get('animations', [])):
        raise ValueError('attack clip names must be unique')
    if 'idle' not in animations:
        raise ValueError('attack proxy calibration requires the final idle clip')
    idle_tracks, idle_times = animation_tracks(document, binary, animations['idle'], require_attack_range=False)
    if not min(idle_times) <= 1.0 <= max(idle_times):
        raise ValueError('idle proxy reference must include source 1.0 seconds')
    idle_world = pose_world(document, idle_tracks, 1.0, parents, order)
    targets = {'head': ('Head', Vector((0, 1.62, 0))),
               'body_bottom': ('Hip', Vector((0, .55, 0))),
               'body_top': ('Spine02', Vector((0, 1.4, 0)))}
    offsets = {field: idle_world[landmarks[name]].inverted() @ desired
               for field, (name, desired) in targets.items()}
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
        samples = []
        for time in times:
            world = pose_world(document, tracks, time, parents, order)
            row = {'time_seconds': time, 'source_seconds': time}
            for field, name in LANDMARKS.items():
                position = list(world[landmarks[name]].translation)
                if not all(math.isfinite(value) for value in position):
                    raise ValueError('attack profile contains a non-finite landmark')
                row[field] = position
            row['head_origin'] = list(row['head'])
            for field, (name, _) in targets.items():
                row[field] = list(world[landmarks[name]] @ offsets[field])
            row['bone_rotation_xyzw'] = {}
            for name in ('Head', 'Spine02', 'Hip'):
                q = world[landmarks[name]].to_quaternion().normalized()
                row['bone_rotation_xyzw'][name] = [q.x, q.y, q.z, q.w]
            row['torso_lower'] = list(row['hip'])
            row['torso_upper'] = list(row['spine02'])
            samples.append(row)
        profiles[direction] = {
            'clip': clip, 'source_range_seconds': [0.0, 1.75],
            'source_phase_seconds': [0.0, .65, .90, 1.10, 1.75], 'contact_source_seconds': 1.0,
            'animation_semantics_sha256': animation_signature(document, binary, animation),
            'samples': samples,
        }
    return {
        'schema_version': 2, 'units': 'metres', 'space': 'prepared actor root',
        'axes': {'up': '+Y', 'forward': '+Z', 'actor_left': '+X'},
        'landmark_nodes': dict(LANDMARKS),
        'torso_anchor_nodes': {'lower': 'Hip', 'upper': 'Spine02'},
        'proxy_calibration': {'clip': 'idle', 'source_seconds': 1.0,
                              'idle_centres_metres': {field: list(point) for field, (_, point) in targets.items()},
                              'bone_local_offsets': {field: list(point) for field, point in offsets.items()}},
        'idle_reference': {field: list(idle_world[landmarks[name]].translation)
                           for field, name in LANDMARKS.items() if name in ('Head', 'Spine02', 'Hip')},
        'phase_markers_seconds': dict(ATTACK_PHASES),
        'phase_sample_times_seconds': {name: float32(time) for name, time in ATTACK_PHASES.items()},
        'sample_rate_hz': 60, 'time_encoding': 'float32 source-key/60Hz/phase union',
        'direction_labels': 'caller supplied; player-view incoming side requires geometric review',
        'attacks': profiles,
    }
