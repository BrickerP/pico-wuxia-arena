"""Canonical candidate: constrain one target LEFT wrist during prepared asset production.

No historical model, camera, app or formal-bank dependency. The incoming prepared
asset itself supplies the unmodified wrist reference before any mutation.
"""
import copy
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from attack_profiles import (
    animation_tracks, hierarchy, pose_world, sample_track, skin_attribute,
)
from prepare_rigged_warrior import (
    local_matrix, animation_signature, read_glb, encode_glb,
)
BONES = ('R_Upperarm', 'R_Forearm', 'R_Hand')
STEEL_VERTEX_COUNT = 5533

def require(value, message):
    if not value:
        raise ValueError(message)

def smooth(value):
    value = max(0.0, min(1.0, value))
    return max(0.0, min(1.0, value ** 3 * (10.0 + value * (-15.0 + 6.0 * value))))

def amount(time, window):
    (start, a, b, end) = window
    if time <= start or time >= end:
        return 0.0
    if time < a:
        return smooth((time - start) / (a - start))
    if time <= b:
        return 1.0
    return 1.0 - smooth((time - b) / (end - b))

def validate_right_recipe(recipe):
    expected = {'schema_version', 'character_id', 'clip', 'arm_bones', 'swivel_degrees', 'window_source_seconds', 'local_sample_rate_hz', 'key_steel_budget_metres', 'subkey_steel_budget_metres', 'reference'}
    require(isinstance(recipe, dict) and set(recipe) == expected, 'Prepared wrist recipe fields differ')
    require(recipe['schema_version'] == 1 and recipe['character_id'] == 'veteran' and (recipe['clip'] == 'attack_left') and (tuple(recipe['arm_bones']) == BONES), 'Unsupported real target/clip/bones')
    require(recipe['reference'] == 'unconstrained_same_target_prepared_fk', 'External or mutable wrist reference is forbidden')
    require(recipe['local_sample_rate_hz'] == 120, 'Current accepted local density is120Hz')
    window = recipe['window_source_seconds']
    require(len(window) == 4 and all((type(v) in (int, float) and math.isfinite(v) for v in window)) and (0 <= window[0] < window[1] <= window[2] < window[3] <= 1.75), 'Invalid constrained interval')
    require(type(recipe['swivel_degrees']) in (int, float) and math.isfinite(recipe['swivel_degrees']), 'Finite real elbow swivel required')
    require(recipe['key_steel_budget_metres'] == 5e-06 and recipe['subkey_steel_budget_metres'] == 0.001, 'Do not relax accepted wrist/steel budgets')
    return recipe

def sampled_locals(doc, tracks, time):
    result = {}
    for (i, node) in enumerate(doc['nodes']):
        t = Vector(node.get('translation', (0, 0, 0)))
        q = node.get('rotation', (0, 0, 0, 1))
        q = Quaternion((q[3], *q[:3]))
        s = Vector(node.get('scale', (1, 1, 1)))
        if (i, 'translation') in tracks:
            t = Vector(sample_track(tracks[i, 'translation'], time, False))
        if (i, 'rotation') in tracks:
            v = sample_track(tracks[i, 'rotation'], time, True)
            q = Quaternion((v[3], *v[:3]))
        if (i, 'scale') in tracks:
            s = Vector(sample_track(tracks[i, 'scale'], time, False))
        result[i] = [t, q, s]
    return result

def exact_worlds(doc, local, parents, order):
    result = {}
    for i in order:
        # Preserve exact prepared normalization matrices without decomposition.
        m = local_matrix(doc['nodes'][i]) if 'matrix' in doc['nodes'][i] else Matrix.LocRotScale(*local[i])
        result[i] = result[parents[i]] @ m if i in parents else m
    return result

def append_accessor(doc, binary, values, kind):
    width = len(values[0])
    packed = bytearray(binary)
    packed.extend(b'\x00' * (-len(packed) % 4))
    start = len(packed)
    for row in values:
        packed.extend(struct.pack('<' + 'f' * width, *row))
    view = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(packed) - start})
    index = len(doc['accessors'])
    doc['accessors'].append({'bufferView': view, 'componentType': 5126, 'type': kind, 'count': len(values), 'min': [min((x[i] for x in values)) for i in range(width)], 'max': [max((x[i] for x in values)) for i in range(width)]})
    doc['buffers'][0]['byteLength'] = len(packed)
    return (bytes(packed), index)

def set_world_rotation(local, index, wanted, world, parents):
    parent = world[parents[index]].to_quaternion() if index in parents else Quaternion((1, 0, 0, 0))
    local[index][1] = (parent.inverted() @ wanted).normalized()

def aim_segment(doc, local, index, end, wanted, parents, order):
    world = exact_worlds(doc, local, parents, order)
    current = (world[end].translation - world[index].translation).normalized()
    direction = (wanted - world[index].translation).normalized()
    set_world_rotation(local, index, current.rotation_difference(direction) @ world[index].to_quaternion(), world, parents)

def solve_arm(doc, local, target, pole, names, parents, order):
    chain = [names[n] for n in BONES]
    world = exact_worlds(doc, local, parents, order)
    (s, e, w) = [world[i].translation for i in chain]
    (upper, lower) = ((e - s).length, (w - e).length)
    distance = (target - s).length
    require(abs(upper - lower) + 1e-05 < distance < upper + lower - 1e-05, 'Target wrist is unreachable without changing bone length')
    axis = (target - s).normalized()
    along = (upper * upper - lower * lower + distance * distance) / (2 * distance)
    height = math.sqrt(max(0, upper * upper - along * along))
    bend = pole - s
    bend -= axis * bend.dot(axis)
    require(bend.length > 1e-08, 'Collinear elbow pole')
    elbow = s + axis * along + bend.normalized() * height
    aim_segment(doc, local, chain[0], chain[1], elbow, parents, order)
    aim_segment(doc, local, chain[1], chain[2], target, parents, order)
    require((exact_worlds(doc, local, parents, order)[chain[-1]].translation - target).length <= 1e-05, 'Target IK reconstruction error')

def combined_steel_hand_points(doc, binary):
    """Require the actual combined weapon and return its rigid hand-local points."""
    names = {node['name']: i for i, node in enumerate(doc['nodes'])}
    hand = names['R_Hand']
    skin = doc['skins'][0]
    palette = skin['joints'].index(hand)
    inverse_bind = skin_attribute(doc, binary, skin['inverseBindMatrices'])
    hand_inverse_bind = inverse_bind[palette].reshape(4, 4).T
    points = []
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            material = doc['materials'][primitive['material']]
            if 'Steel' not in material.get('name', ''):
                continue
            attributes = primitive['attributes']
            positions = skin_attribute(doc, binary, attributes['POSITION'])
            joints = skin_attribute(doc, binary, attributes['JOINTS_0'])
            weights = skin_attribute(doc, binary, attributes['WEIGHTS_0'])
            require(np.all(np.isfinite(positions)), 'Combined Steel positions are not finite')
            require(np.all(np.isfinite(weights)) and np.all(weights >= 0),
                    'Combined Steel weights are invalid')
            require(np.all(joints < len(skin['joints'])),
                    'Combined Steel joint indices escape the palette')
            require(np.max(np.abs(weights.sum(axis=1) - 1)) <= 1e-6,
                    'Combined Steel weights are not normalized')
            outside_hand = np.sum(weights * (joints != palette), axis=1)
            require(np.max(outside_hand) <= 1e-6,
                    'Combined Steel is not rigid to R_Hand')
            homogeneous = np.column_stack((positions, np.ones(len(positions))))
            points.append((hand_inverse_bind @ homogeneous.T).T)
    require(points, 'Combined PNG has no Steel weapon surface')
    result = np.concatenate(points)
    require(len(result) == STEEL_VERTEX_COUNT,
            'Combined PNG Steel vertex count differs from the pinned weapon')
    return result


def wrist_orientation_error(old_frame, new_frame):
    """Return the complete wrist rigid-orientation difference, without acos rounding."""
    old = np.asarray(old_frame.to_quaternion(), dtype=np.float64)
    new = np.asarray(new_frame.to_quaternion(), dtype=np.float64)
    old /= np.linalg.norm(old)
    new /= np.linalg.norm(new)
    if np.dot(old, new) < 0:
        new = -new
    return 4 * math.atan2(np.linalg.norm(new - old), np.linalg.norm(new + old))


def apply_constraint(doc, binary, recipe, steel_points):
    validate_right_recipe(recipe)
    require(isinstance(steel_points, np.ndarray) and steel_points.shape == (STEEL_VERTEX_COUNT, 4),
            'The validated combined Steel reference is required')
    before = copy.deepcopy(doc)
    old_animation = next((a for a in before['animations'] if a['name'] == recipe['clip']))
    (tracks, times) = animation_tracks(before, binary, old_animation)
    times = sorted(times)
    (_, parents, order) = hierarchy(before)
    names = {n['name']: i for (i, n) in enumerate(before['nodes'])}
    require(times[0] == 0 and times[-1] == 1.75, 'Prepared attack duration changed')
    window = [struct.unpack('<f', struct.pack('<f', v))[0] for v in recipe['window_source_seconds']]
    rate = recipe['local_sample_rate_hz']
    dense = [struct.unpack('<f', struct.pack('<f', i / rate))[0] for i in range(math.ceil(window[0] * rate), math.floor(window[3] * rate) + 1)]
    # Include original boundary keys despite float32 rounding at 0.9/1.3.
    dense += [struct.unpack('<f', struct.pack('<f', v))[0] for v in (recipe['window_source_seconds'][0], recipe['window_source_seconds'][3])]
    newtimes = sorted(set(times) | set(dense))
    curves = {n: [] for n in BONES}
    replay = 0.0
    goal_frames = []
    for time in newtimes:
        local = sampled_locals(before, tracks, time)
        world = pose_world(before, tracks, time, parents, order)
        again = exact_worlds(before, local, parents, order)
        replay = max(replay, max((float(np.max(np.abs(np.asarray(world[i]) - np.asarray(again[i])))) for i in world)))
        require(replay == 0, 'Prepared baseline replay is not exact')
        value = amount(time, window)
        if value:
            shoulder = world[names[BONES[0]]].translation
            elbow = world[names[BONES[1]]].translation
            wrist = world[names[BONES[2]]].translation
            orientation = world[names[BONES[2]]].to_quaternion()
            axis = (wrist - shoulder).normalized()
            pole = shoulder + Quaternion(axis, math.radians(recipe['swivel_degrees']) * value) @ (elbow - shoulder)
            solve_arm(before, local, wrist, pole, names, parents, order)
            set_world_rotation(local, names[BONES[2]], orientation, exact_worlds(before, local, parents, order), parents)
        goal_frames.append([time, *[v for row in world[names[BONES[2]]] for v in row]])
        for bone in BONES:
            old = tracks[names[bone], 'rotation']
            if not value and time in old[0]:
                q = old[1][old[0].index(time)]
            else:
                q = local[names[bone]][1]
                q = (q.x, q.y, q.z, q.w)
                reference = sample_track(old, time, True)
                if sum((a * b for (a, b) in zip(q, reference))) < 0:
                    q = tuple((-v for v in q))
            curves[bone].append(q)
    (packed, time_accessor) = append_accessor(doc, binary, [(t,) for t in newtimes], 'SCALAR')
    animation = next((a for a in doc['animations'] if a['name'] == recipe['clip']))
    for bone in BONES:
        (packed, index) = append_accessor(doc, packed, curves[bone], 'VEC4')
        channel = next((c for c in animation['channels'] if c['target'] == {'node': names[bone], 'path': 'rotation'}))
        sampler = animation['samplers'][channel['sampler']]
        sampler['input'] = time_accessor
        sampler['output'] = index
    (actual, newgrid) = animation_tracks(doc, packed, animation)
    for (key, track) in tracks.items():
        if key[0] in {names[n] for n in BONES} and key[1] == 'rotation':
            continue
        require(track == actual[key], 'Untouched prepared LEFT track changed')
    old_signatures = {a['name']: animation_signature(before, binary, a) for a in before['animations']}
    new_signatures = {a['name']: animation_signature(doc, packed, a) for a in doc['animations']}
    require(all((v == new_signatures[k] for (k, v) in old_signatures.items() if k != recipe['clip'])), 'Another prepared clip changed')
    points = steel_points
    keymax = 0.0
    submax = 0.0
    wristmax = 0.0
    bone_max = 0.0
    sub_wrist_max = 0.0
    key_orientation_max = 0.0
    sub_orientation_max = 0.0
    key_orientation_displacement = 0.0
    sub_orientation_displacement = 0.0
    for time in sorted(set(newtimes) | {(a + b) / 2 for (a, b) in zip(newtimes, newtimes[1:])}):
        old = pose_world(before, tracks, time, parents, order)
        new = pose_world(doc, actual, time, parents, order)
        hand = names[BONES[2]]
        pos = (new[hand].translation - old[hand].translation).length
        old_points = (np.asarray(old[hand]) @ points.T).T[:, :3]
        new_points = (np.asarray(new[hand]) @ points.T).T[:, :3]
        error = float(np.max(np.linalg.norm(new_points - old_points, axis=1)))
        orientation = wrist_orientation_error(old[hand], new[hand])
        wrist_origin = np.asarray(old[hand].translation, dtype=np.float64)
        steel_radius = float(np.max(np.linalg.norm(old_points - wrist_origin, axis=1)))
        # Express full wrist orientation in the same accepted spatial budget,
        # at the actual weapon's furthest radius, rather than inventing an angle epsilon.
        orientation_displacement = 2 * steel_radius * math.sin(orientation / 2)
        if time in newtimes:
            keymax = max(keymax, error)
            wristmax = max(wristmax, pos)
            key_orientation_max = max(key_orientation_max, orientation)
            key_orientation_displacement = max(key_orientation_displacement, orientation_displacement)
        else:
            submax = max(submax, error)
            sub_wrist_max = max(sub_wrist_max, pos)
            sub_orientation_max = max(sub_orientation_max, orientation)
            sub_orientation_displacement = max(sub_orientation_displacement, orientation_displacement)
        for name in ('Head', 'BoneRoot', 'Hip', 'L_Foot', 'R_Foot'):
            require(np.array_equal(np.asarray(old[names[name]]), np.asarray(new[names[name]])), 'Protected head/root/foot changed')
        for (a, b) in zip(BONES[:2], BONES[1:]):
            bone_max = max(bone_max, abs((new[names[b]].translation - new[names[a]].translation).length - (old[names[b]].translation - old[names[a]].translation).length))
    require(bone_max <= 1e-06, 'Target bone length changed')
    require(keymax <= recipe['key_steel_budget_metres'] and wristmax <= recipe['key_steel_budget_metres'], 'Target key wrist/steel constraint failed')
    require(submax <= recipe['subkey_steel_budget_metres'] and
            sub_wrist_max <= recipe['subkey_steel_budget_metres'],
            'Target subkey wrist/steel constraint failed')
    require(key_orientation_displacement <= recipe['key_steel_budget_metres'],
            'Target key wrist orientation constraint failed')
    require(sub_orientation_displacement <= recipe['subkey_steel_budget_metres'],
            'Target subkey wrist orientation constraint failed')
    for time in (0, 1.75):
        old = pose_world(before, tracks, time, parents, order)
        new = pose_world(doc, actual, time, parents, order)
        require(all((np.array_equal(np.asarray(old[i]), np.asarray(new[i])) for i in old)), 'Prepared endpoint changed')
    goal_identity = hashlib.sha256(
        json.dumps(goal_frames, separators=(',', ':')).encode()
    ).hexdigest()
    proof = {
        'applied': True,
        'recipe': recipe,
        'unconstrained_same_target_wrist_sha256': goal_identity,
        'before_animation_semantics_sha256': old_signatures[recipe['clip']],
        'after_animation_semantics_sha256': new_signatures[recipe['clip']],
        'baseline_replay_error': replay,
        'original_key_union_count': len(times),
        'prepared_key_union_count': len(newgrid),
        'changed_rotation_streams': list(BONES),
        'untouched_LEFT_TRS_tracks': 231,
        'other9_clips_unchanged': True,
        'steel_reference': 'validated_combined_png_hand_local',
        'full_steel_reference_vertex_count': len(points),
        'key_wrist_max_m': wristmax,
        'subkey_wrist_max_m': sub_wrist_max,
        'key_full_steel_max_m': keymax,
        'subkey_full_steel_max_m': submax,
        'key_wrist_orientation_max_radians': key_orientation_max,
        'subkey_wrist_orientation_max_radians': sub_orientation_max,
        'key_wrist_orientation_at_steel_radius_m': key_orientation_displacement,
        'subkey_wrist_orientation_at_steel_radius_m': sub_orientation_displacement,
        'bone_world_length_max_delta_m': bone_max,
    }
    return packed, proof



# Exact prepared-target data contract (inlined; no private runtime import).
import hashlib as left_asset_hashlib
import json as left_asset_json
import math as left_asset_math
import pathlib as left_asset_pathlib
import struct as left_asset_struct

LEFT_ASSET_CLIPS = ("attack_overhead", "attack_left", "attack_right")

LEFT_ASSET_BONES = ("L_Upperarm", "L_Forearm", "L_Hand")

LEFT_ASSET_RANGE = (0.0, 1.75)

LEFT_ASSET_COMPONENTS = {5120: ("b", 1), 5121: ("B", 1),
                         5122: ("h", 2), 5123: ("H", 2),
                         5125: ("I", 4), 5126: ("f", 4)}

LEFT_ASSET_WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4,
                     "MAT2": 4, "MAT3": 9, "MAT4": 16}

LEFT_ASSET_SCOPES = {
    "rest": (
        "v1 SHA256 of compact sorted-key UTF-8 JSON: ordered 78 joint_names, "
        "sorted bound_mesh_names, and name-sorted relevant frames. Each frame "
        "contains node name, parent name, and its original matrix (never "
        "decomposed) or explicit default-completed local TRS as float64 JSON "
        "numbers. Relevant frames are all joints, bound skinned mesh nodes, "
        "and all their ancestors. Node indices, children arrays, mesh/primitive "
        "references and buffer indices are excluded."
    ),
    "inverse_binds": (
        "SHA256 of the original de-strided, little-endian FLOAT MAT4 accessor "
        "payload, exactly 78 matrices in skin.joints palette order; buffer "
        "indices/offsets, JSON metadata and padding are excluded."
    ),
    "guard": (
        "SHA256 of little-endian float32 source values at an exact stored "
        "time key: 78 skin.joints in palette order, each translation xyz, "
        "rotation xyzw, scale xyz (234 complete TRS channels; 780 floats). "
        "No interpolation, quaternion normalization/sign change or rest fallback. "
        "Idle uses time 0; each attack uses entry 0 and exit 1.75 seconds."
    ),
}

def left_asset_check(condition, message):
    if not condition:
        raise ValueError(message)

def left_asset_sha(payload):
    return left_asset_hashlib.sha256(payload).hexdigest()

def left_asset_packed_f32(values):
    """Pack a flat iterable as little-endian float32 without normalization."""
    values = list(values)
    return left_asset_struct.pack("<" + "f" * len(values), *values)

def left_asset_accessor_bytes(doc, binary, index):
    """Return dense original element bytes with stride/padding removed.

    Sparse, normalized, external buffers and padded integer matrices are
    deliberately rejected; the rig and animation contract uses dense FLOAT.
    """
    left_asset_check(type(index) is int and 0 <= index < len(doc["accessors"]),
                     "accessor index is invalid")
    accessor = doc["accessors"][index]
    left_asset_check("sparse" not in accessor and not accessor.get("normalized"),
                     "sparse/normalized accessors are outside this contract")
    left_asset_check("bufferView" in accessor, "accessor has no dense bufferView")
    component = accessor.get("componentType")
    kind = accessor.get("type")
    left_asset_check(component in LEFT_ASSET_COMPONENTS and kind in LEFT_ASSET_WIDTHS,
                     "unsupported accessor format")
    width = LEFT_ASSET_WIDTHS[kind]
    component_bytes = LEFT_ASSET_COMPONENTS[component][1]
    left_asset_check(not kind.startswith("MAT") or component_bytes == 4,
                     "padded integer matrix accessors are outside this contract")
    size = width * component_bytes
    count = accessor.get("count")
    left_asset_check(type(count) is int and count >= 1, "accessor count is invalid")
    view_index = accessor["bufferView"]
    left_asset_check(type(view_index) is int and 0 <= view_index < len(doc["bufferViews"]),
                     "bufferView index is invalid")
    view = doc["bufferViews"][view_index]
    left_asset_check(view.get("buffer", 0) == 0, "accessor uses an external buffer")
    view_offset = view.get("byteOffset", 0)
    local_offset = accessor.get("byteOffset", 0)
    view_length = view.get("byteLength")
    stride = view.get("byteStride", size)
    left_asset_check(all(type(value) is int and value >= 0
                         for value in (view_offset, local_offset, view_length, stride)),
                     "accessor byte layout is invalid")
    left_asset_check(stride >= size and stride % component_bytes == 0,
                     "accessor byteStride is invalid")
    logical_length = doc["buffers"][0]["byteLength"]
    left_asset_check(view_offset + view_length <= min(logical_length, len(binary)),
                     "bufferView exceeds embedded buffer")
    end = local_offset + (count - 1) * stride + size
    left_asset_check(end <= view_length, "accessor exceeds its bufferView")
    start = view_offset + local_offset
    if stride == size:
        return bytes(binary[start:start + count * size])
    return b"".join(binary[start + i * stride:start + i * stride + size]
                    for i in range(count))

def left_asset_accessor_values(doc, binary, index):
    """Decode dense accessor; SCALAR gives numbers, vectors/matrices give lists."""
    accessor = doc["accessors"][index]
    payload = left_asset_accessor_bytes(doc, binary, index)
    width = LEFT_ASSET_WIDTHS[accessor["type"]]
    code = LEFT_ASSET_COMPONENTS[accessor["componentType"]][0]
    rows = left_asset_struct.iter_unpack("<" + code * width, payload)
    return [row[0] for row in rows] if width == 1 else [list(row) for row in rows]

def left_asset_rig_nodes(doc):
    """Return (skin, palette, name->index, parents, bound mesh indices)."""
    skins = doc.get("skins", [])
    left_asset_check(len(skins) == 1, "expected exactly one prepared skin")
    skin = skins[0]
    joints = skin.get("joints", [])
    nodes = doc.get("nodes", [])
    left_asset_check(len(joints) == 78 and len(set(joints)) == 78,
                     "expected 78 distinct ordered joints")
    left_asset_check(all(type(i) is int and 0 <= i < len(nodes) for i in joints),
                     "skin joint index is invalid")
    names = {}
    parents = {}
    for index, node in enumerate(nodes):
        name = node.get("name")
        left_asset_check(isinstance(name, str) and name and name not in names,
                         "prepared nodes must have unique nonempty names")
        names[name] = index
        for child in node.get("children", []):
            left_asset_check(type(child) is int and 0 <= child < len(nodes) and
                             child not in parents, "node has invalid/multiple parents")
            parents[child] = index
    for index in range(len(nodes)):
        seen = set()
        while index in parents:
            left_asset_check(index not in seen, "node hierarchy has a cycle")
            seen.add(index)
            index = parents[index]
    bound = [i for i, node in enumerate(nodes) if node.get("skin") == 0 and "mesh" in node]
    left_asset_check(bool(bound), "skin is not bound to a mesh node")
    return skin, joints, names, parents, bound

def left_asset_animation(doc, clip):
    matches = [animation for animation in doc.get("animations", [])
               if animation.get("name") == clip]
    left_asset_check(len(matches) == 1, "clip must exist exactly once: " + str(clip))
    return matches[0]

def left_asset_channel(doc, clip, node_index, path):
    """Return the unique animation sampler for a node/path."""
    animation = left_asset_animation(doc, clip)
    channels = [channel for channel in animation["channels"]
                if channel.get("target", {}).get("node") == node_index and
                channel.get("target", {}).get("path") == path]
    left_asset_check(len(channels) == 1,
                     f"expected one {clip}/{node_index}/{path} channel")
    sampler_index = channels[0]["sampler"]
    left_asset_check(type(sampler_index) is int and
                     0 <= sampler_index < len(animation["samplers"]),
                     "channel sampler index is invalid")
    return animation["samplers"][sampler_index]

def left_asset_float_curve(doc, binary, sampler, width):
    """Return original FLOAT input times/output rows and verify dense LINEAR shape."""
    left_asset_check(sampler.get("interpolation", "LINEAR") == "LINEAR",
                     "curve must use LINEAR interpolation")
    inputs = doc["accessors"][sampler["input"]]
    outputs = doc["accessors"][sampler["output"]]
    left_asset_check(inputs.get("componentType") == 5126 and inputs.get("type") == "SCALAR",
                     "curve time accessor must be FLOAT SCALAR")
    left_asset_check(outputs.get("componentType") == 5126 and
                     outputs.get("type") == "VEC" + str(width) and
                     outputs.get("count") == inputs.get("count"),
                     "curve output accessor shape differs")
    times = left_asset_accessor_values(doc, binary, sampler["input"])
    values = left_asset_accessor_values(doc, binary, sampler["output"])
    left_asset_check(all(left_asset_math.isfinite(t) for t in times) and
                     all(a < b for a, b in zip(times, times[1:])),
                     "source key times must be finite and strictly increasing")
    left_asset_check(all(left_asset_math.isfinite(v) for row in values for v in row),
                     "source values must be finite")
    return times, values

def left_asset_guard_values(doc, binary, clip, time):
    """Read all 234 TRS source channels at an exact key; never interpolate."""
    _, joints, _, _, _ = left_asset_rig_nodes(doc)
    result = []
    for index in joints:
        for path, width in (("translation", 3), ("rotation", 4), ("scale", 3)):
            sampler = left_asset_channel(doc, clip, index, path)
            times, values = left_asset_float_curve(doc, binary, sampler, width)
            matches = [i for i, value in enumerate(times) if value == time]
            left_asset_check(len(matches) == 1,
                             f"guard requires exact source key: {clip}@{time}/{index}/{path}")
            result.extend(values[matches[0]])
    return result

def left_asset_guard_sha(doc, binary, clip, time):
    return left_asset_sha(left_asset_packed_f32(
        left_asset_guard_values(doc, binary, clip, time)))

def left_asset_local_frame(node):
    if "matrix" in node:
        left_asset_check(not any(path in node for path in ("translation", "rotation", "scale")),
                         "node mixes matrix with TRS")
        frame = {"matrix": node["matrix"]}
        widths = {"matrix": 16}
    else:
        frame = {"translation": node.get("translation", [0, 0, 0]),
                 "rotation": node.get("rotation", [0, 0, 0, 1]),
                 "scale": node.get("scale", [1, 1, 1])}
        widths = {"translation": 3, "rotation": 4, "scale": 3}
    for path, values in frame.items():
        left_asset_check(isinstance(values, list) and len(values) == widths[path] and
                         all(type(v) in (int, float) and left_asset_math.isfinite(v)
                             for v in values), "invalid node local transform")
        frame[path] = [float(v) for v in values]
    return frame

def left_asset_rig_contract(doc, binary):
    """Fingerprint prepared rest frames, raw inverse binds and complete guards."""
    skin, joints, _, parents, bound = left_asset_rig_nodes(doc)
    nodes = doc["nodes"]
    relevant = set(joints) | set(bound)
    for node_index in list(relevant):
        while node_index in parents:
            node_index = parents[node_index]
            relevant.add(node_index)
    joint_names = [nodes[i]["name"] for i in joints]
    frames = [{"name": nodes[i]["name"],
               "parent": nodes[parents[i]]["name"] if i in parents else None,
               "local": left_asset_local_frame(nodes[i])}
              for i in sorted(relevant, key=lambda index: nodes[index]["name"])]
    rest = {"joint_names": joint_names,
            "bound_mesh_names": sorted(nodes[i]["name"] for i in bound), "frames": frames}
    rest_bytes = left_asset_json.dumps(rest, sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    inverse_index = skin["inverseBindMatrices"]
    inverse = doc["accessors"][inverse_index]
    left_asset_check(inverse.get("componentType") == 5126 and
                     inverse.get("type") == "MAT4" and inverse.get("count") == 78,
                     "inverse binds must be 78 FLOAT MAT4 values")
    inverse_bytes = left_asset_accessor_bytes(doc, binary, inverse_index)
    left_asset_check(all(left_asset_math.isfinite(value)
                         for row in left_asset_struct.iter_unpack("<16f", inverse_bytes)
                         for value in row), "inverse binds must be finite")
    return {
        "joint_names": joint_names,
        "rest_sha256": left_asset_sha(rest_bytes),
        "inverse_binds_sha256": left_asset_sha(inverse_bytes),
        "canonical_idle_guard_sha256": left_asset_guard_sha(doc, binary, "idle", 0.0),
        "clip_guard_sha256": {clip: {
            "entry": left_asset_guard_sha(doc, binary, clip, LEFT_ASSET_RANGE[0]),
            "exit": left_asset_guard_sha(doc, binary, clip, LEFT_ASSET_RANGE[1]),
        } for clip in LEFT_ASSET_CLIPS},
        "scope": dict(LEFT_ASSET_SCOPES),
    }

def left_asset_sha_field(value, label):
    left_asset_check(isinstance(value, str) and len(value) == 64 and
                     all(c in "0123456789abcdef" for c in value),
                     label + " must be a lowercase SHA256")

def left_asset_exact_f32(value):
    if type(value) not in (int, float) or not left_asset_math.isfinite(value):
        return False
    try:
        return left_asset_struct.unpack("<f", left_asset_packed_f32([value]))[0] == value
    except (OverflowError, left_asset_struct.error):
        return False

def left_asset_validate(asset):
    """Validate the exact nine-stream, finite float32 contract and payload hashes.

    This validates the self-contained artifact. Source GLB identity and guard
    provenance are separately checked by extraction and by the applying caller.
    """
    left_asset_check(isinstance(asset, dict) and set(asset) == {
        "schema_version", "stage", "character_id", "source_glb", "rig_contract", "clips"},
        "asset fields differ from schema v1")
    left_asset_check(type(asset["schema_version"]) is int and asset["schema_version"] == 1,
                     "asset schema_version must be 1")
    left_asset_check(asset["stage"] == "prepared_target_rotation_curves" and
                     asset["character_id"] == "veteran", "asset stage/character differs")
    source = asset["source_glb"]
    left_asset_check(isinstance(source, dict) and set(source) == {"path", "sha256", "bytes"},
                     "source_glb fields differ")
    left_asset_check(isinstance(source["path"], str) and source["path"].endswith(".glb") and
                     source["path"] and "\\" not in source["path"] and
                     ".." not in left_asset_pathlib.PurePosixPath(source["path"]).parts,
                     "source_glb path must identify a GLB without parent traversal")
    left_asset_check(type(source["bytes"]) is int and source["bytes"] > 0,
                     "source_glb bytes must be positive")
    left_asset_sha_field(source["sha256"], "source_glb.sha256")
    rig = asset["rig_contract"]
    left_asset_check(isinstance(rig, dict) and set(rig) == {
        "joint_names", "rest_sha256", "inverse_binds_sha256",
        "canonical_idle_guard_sha256", "clip_guard_sha256", "scope"},
        "rig_contract fields differ")
    names = rig["joint_names"]
    left_asset_check(isinstance(names, list) and len(names) == 78 and
                     all(isinstance(n, str) and n for n in names) and len(set(names)) == 78 and
                     set(LEFT_ASSET_BONES).issubset(names), "rig joint palette differs")
    left_asset_check(rig["scope"] == LEFT_ASSET_SCOPES, "rig signature scope differs")
    for field in ("rest_sha256", "inverse_binds_sha256", "canonical_idle_guard_sha256"):
        left_asset_sha_field(rig[field], "rig_contract." + field)
    guards = rig["clip_guard_sha256"]
    left_asset_check(isinstance(guards, dict) and set(guards) == set(LEFT_ASSET_CLIPS),
                     "guard clips differ")
    for clip, endpoints in guards.items():
        left_asset_check(isinstance(endpoints, dict) and set(endpoints) == {"entry", "exit"},
                         "guard endpoint fields differ: " + clip)
        for endpoint, digest in endpoints.items():
            left_asset_sha_field(digest, "guard " + clip + "/" + endpoint)
    clips = asset["clips"]
    left_asset_check(isinstance(clips, dict) and set(clips) == set(LEFT_ASSET_CLIPS),
                     "asset must contain exactly the three attack clips")
    for clip, animation in clips.items():
        left_asset_check(isinstance(animation, dict) and set(animation) == {
            "source_range_seconds", "rotations"}, "clip fields differ: " + clip)
        source_range = animation["source_range_seconds"]
        left_asset_check(isinstance(source_range, list) and len(source_range) == 2 and
                         all(left_asset_exact_f32(value) for value in source_range) and
                         source_range == list(LEFT_ASSET_RANGE),
                         "clip source range must be 0..1.75: " + clip)
        rotations = animation["rotations"]
        left_asset_check(isinstance(rotations, dict) and set(rotations) == set(LEFT_ASSET_BONES),
                         "clip must contain exactly three permitted bone rotations: " + clip)
        for bone, stream in rotations.items():
            label = clip + "/" + bone
            left_asset_check(isinstance(stream, dict) and set(stream) == {
                "interpolation", "samples", "time_payload_sha256", "rotation_payload_sha256"},
                "rotation stream fields differ: " + label)
            left_asset_check(stream["interpolation"] == "LINEAR", "expected LINEAR: " + label)
            samples = stream["samples"]
            left_asset_check(isinstance(samples, list) and len(samples) >= 2 and
                             all(isinstance(row, list) and len(row) == 5 for row in samples),
                             "expected [time,x,y,z,w] rows: " + label)
            left_asset_check(all(left_asset_exact_f32(value) for row in samples for value in row),
                             "samples must be finite exact float32 values: " + label)
            times = [row[0] for row in samples]
            left_asset_check(times[0] == LEFT_ASSET_RANGE[0] and
                             times[-1] == LEFT_ASSET_RANGE[1] and
                             all(a < b for a, b in zip(times, times[1:])),
                             "source times must strictly increase from 0 to 1.75: " + label)
            left_asset_check(all(abs(left_asset_math.sqrt(sum(v * v for v in row[1:])) - 1) <= 1e-5
                                 for row in samples), "quaternion norm differs: " + label)
            payloads = {
                "time_payload_sha256": left_asset_packed_f32(times),
                "rotation_payload_sha256": left_asset_packed_f32(
                    value for row in samples for value in row[1:]),
            }
            for field, payload in payloads.items():
                left_asset_sha_field(stream[field], label + "/" + field)
                left_asset_check(left_asset_sha(payload) == stream[field],
                                 "payload SHA256 differs: " + label + "/" + field)

"""Source appended to the one existing prepared constraint implementation.

This file is a patch component, not another producer. The generated prospective
target_wrist_constraint.py inlines the stdlib contract and this code.
"""

from prepare_rigged_warrior import HERE as LEFT_ASSET_SOURCE_BASE


def validate_recipe(recipe):
    """The only public recipe shape; original right policy remains nested intact."""
    require(isinstance(recipe, dict) and
            set(recipe) == {'schema_version', 'right_wrist', 'prepared_left_arm', 'prepared_reaction_guard'},
            'Prepared target recipe requires right_wrist and prepared_left_arm')
    require(recipe['schema_version'] == 3,
            'Prepared target recipe requires schema_version3')
    validate_right_recipe(recipe['right_wrist'])
    entry = recipe['prepared_left_arm']
    require(isinstance(entry, dict) and set(entry) == {'source', 'source_sha256', 'bytes'},
            'Prepared left asset requires source/SHA/bytes')
    require(isinstance(entry['source'], str) and entry['source'] and
            isinstance(entry['source_sha256'], str) and len(entry['source_sha256']) == 64 and
            all(c in '0123456789abcdef' for c in entry['source_sha256']) and
            type(entry['bytes']) is int and entry['bytes'] > 0,
            'Invalid pinned prepared left asset identity')
    validate_reaction_guard_policy(recipe['prepared_reaction_guard'])
    return recipe


def load_prepared_left_asset(entry):
    path = (LEFT_ASSET_SOURCE_BASE / entry['source']).resolve()
    require(path.is_relative_to(LEFT_ASSET_SOURCE_BASE.parent.parent.resolve()),
            'Prepared left asset escapes the canonical repository')
    payload = path.read_bytes()
    require(len(payload) == entry['bytes'] and hashlib.sha256(payload).hexdigest() == entry['source_sha256'],
            'Prepared left asset SHA/byte identity changed')
    asset = json.loads(payload)
    left_asset_validate(asset)
    return asset


def apply_prepared_left_curves(character_id, doc, binary, asset):
    """Set exact approved target-space rotation streams; never retarget or calibrate.

    A mismatched rig/IBM/guard is an error, not permission to transform the data.
    The caller receives new in-memory data only after all validations succeed.
    """
    left_asset_validate(asset)
    require(character_id == asset['character_id'] == 'veteran',
            'Prepared left curves target veteran only')
    actual = left_asset_rig_contract(doc, binary)
    require(actual == asset['rig_contract'], 'Prepared left rig/IBM/guard contract differs')
    before = copy.deepcopy(doc)
    result = copy.deepcopy(doc)
    packed = binary
    names = {node['name']: index for index, node in enumerate(doc['nodes'])}
    require(len(doc.get('animations', [])) == 10 and
            len({a['name'] for a in doc['animations']}) == 10,
            'Prepared left import requires the complete unique ten-clip bank')
    expected_channels = {(index, path) for index in doc['skins'][0]['joints']
                         for path in ('translation', 'rotation', 'scale')}
    for animation in doc['animations']:
        keys = [(channel['target']['node'], channel['target']['path'])
                for channel in animation['channels']]
        require(len(keys) == 234 and set(keys) == expected_channels and
                len(animation['samplers']) == 234 and
                {c['sampler'] for c in animation['channels']} == set(range(234)),
                'Prepared left import requires exactly234 unique joint TRS streams; animated ancestors/mesh frames are forbidden')
    changed = []
    for clip in LEFT_ASSET_CLIPS:
        animation = left_asset_animation(result, clip)
        for bone in LEFT_ASSET_BONES:
            row = asset['clips'][clip]['rotations'][bone]
            sampler = left_asset_channel(result, clip, names[bone], 'rotation')
            times = [sample[0] for sample in row['samples']]
            values = [sample[1:] for sample in row['samples']]
            same = (sampler.get('interpolation', 'LINEAR') == 'LINEAR' and
                    left_asset_accessor_bytes(result, packed, sampler['input']) == left_asset_packed_f32(times) and
                    left_asset_accessor_bytes(result, packed, sampler['output']) == left_asset_packed_f32(v for value in values for v in value))
            if not same:
                packed, input_index = append_accessor(result, packed, [(v,) for v in times], 'SCALAR')
                packed, output_index = append_accessor(result, packed, values, 'VEC4')
                sampler.update(input=input_index, output=output_index, interpolation='LINEAR')
                changed.append(clip + '/' + bone + '/rotation')

    # All old data remain byte-identical, and only the nine declared sampler
    # references may differ. This also protects every R-side/finger/TRS stream.
    require(packed[:len(binary)] == binary, 'Prepared left import changed original BIN payload')
    for old_animation, new_animation in zip(before['animations'], result['animations']):
        require(old_animation['name'] == new_animation['name'] and
                old_animation['channels'] == new_animation['channels'] and
                len(old_animation['samplers']) == len(new_animation['samplers']),
                'Prepared left import changed channel structure')
        for channel in old_animation['channels']:
            name = before['nodes'][channel['target']['node']]['name']
            allowed = (old_animation['name'] in LEFT_ASSET_CLIPS and
                       name in LEFT_ASSET_BONES and channel['target']['path'] == 'rotation')
            if not allowed:
                index = channel['sampler']
                require(old_animation['samplers'][index] == new_animation['samplers'][index],
                        'Prepared left import changed a protected sampler')
    require(left_asset_rig_contract(result, packed) == asset['rig_contract'],
            'Prepared left import changed REST/IBM/234-TRS guard signatures')
    for clip in LEFT_ASSET_CLIPS:
        for bone in LEFT_ASSET_BONES:
            row = asset['clips'][clip]['rotations'][bone]
            sampler = left_asset_channel(result, clip, names[bone], 'rotation')
            require(left_asset_sha(left_asset_accessor_bytes(result, packed, sampler['input'])) == row['time_payload_sha256'] and
                    left_asset_sha(left_asset_accessor_bytes(result, packed, sampler['output'])) == row['rotation_payload_sha256'],
                    'Prepared left output differs from approved source payload')
    return result, packed, {
        'applied': bool(changed), 'character_id': character_id,
        'stage': 'prepared_target_rotation_curves',
        'source_glb': asset['source_glb'], 'rig_contract': asset['rig_contract'],
        'changed_rotation_streams': changed, 'approved_rotation_streams': 9,
        'all_original_BIN_payloads_unchanged': True,
        'all_other_samplers_unchanged': True,
        'per_clip_key_counts': {clip: {bone: len(asset['clips'][clip]['rotations'][bone]['samples'])
                                      for bone in LEFT_ASSET_BONES} for clip in LEFT_ASSET_CLIPS},
    }


def apply_prepared_character(character_id, body_path, png_path, recipe):
    """Atomically validate strict wrist, prepared arm and common-guard reactions before either write."""
    validate_recipe(recipe)
    asset = load_prepared_left_asset(recipe['prepared_left_arm'])
    right = recipe['right_wrist']
    require(asset['character_id'] == right['character_id'], 'Right/left target characters differ')
    combined_doc, combined_binary = read_glb(Path(png_path))
    steel_points = combined_steel_hand_points(combined_doc, combined_binary)
    body_doc, body_binary = read_glb(Path(body_path))
    prepared = []
    for role, path, doc, binary in (
            ('body', Path(body_path), body_doc, body_binary),
            ('combined_png', Path(png_path), combined_doc, combined_binary)):
        if character_id == right['character_id']:
            require(left_asset_rig_contract(doc, binary) == asset['rig_contract'],
                    'Prepared target REST/IBM/guard differs before constraints')
            packed, right_proof = apply_constraint(doc, binary, right, steel_points)
            final_doc, packed, left_proof = apply_prepared_left_curves(character_id, doc, packed, asset)
        else:
            final_doc, packed = doc, binary
            right_proof = left_proof = {'applied': False, 'reason': 'Arm correction targets ' + right['character_id']}
        packed, reaction_proof = apply_reaction_guard(character_id, final_doc, packed,
            recipe['prepared_reaction_guard'], steel_points)
        final_signatures = {a['name']: animation_signature(final_doc, packed, a)
                            for a in final_doc['animations']}
        prepared.append((path, encode_glb(final_doc, packed), right_proof, left_proof,
                         reaction_proof, final_signatures))
    body, combined = prepared
    if character_id == right['character_id']:
        require(body[2]['unconstrained_same_target_wrist_sha256'] == combined[2]['unconstrained_same_target_wrist_sha256'],
                'Body/combined baseline wrist frames differ')
        require(body[2]['after_animation_semantics_sha256'] == combined[2]['after_animation_semantics_sha256'],
                'Body/combined strict right constraint curves differ')
    require(body[5] == combined[5], 'Body/combined final ten-clip curves differ')
    # All sources, geometry and both full-Steel endpoint checks pass before any output write.
    for entry in prepared:
        entry[0].write_bytes(entry[1])
    return {'applied': True,
            'prepared_space': 'after canonical normalization/finger/root grounding; before KTX/profile',
            'combined_rigid_steel_vertex_count': len(steel_points),
            'body_and_combined_share_wrist_reference': True,
            'prepared_left_asset': recipe['prepared_left_arm'],
            'prepared_reaction_guard': recipe['prepared_reaction_guard'],
            'assets': [{'file': entry[0].name, 'asset_role': role,
                        'right_wrist': entry[2], 'prepared_left': entry[3],
                        'reactions': entry[4], 'final_animation_signatures': entry[5]}
                       for role, entry in zip(('body', 'combined_png'), prepared)]}

from attack_profiles import REACTION_PLAYBACK, float32


def validate_reaction_guard_policy(policy):
    expected={'schema_version','method','playback_windows','sample_rate_hz','input_animation_signatures','head_relative_amplitude','head_neck_relative_amplitude'}
    require(isinstance(policy,dict) and set(policy)==expected,'Prepared reaction policy fields changed')
    require(policy['schema_version']==1 and policy['method']=='same_target_guard_rebased_reaction_delta_with_chest_relative_offhand', 'Unsupported reaction source operation')
    require(policy['sample_rate_hz']==120 and policy['playback_windows']=={k:list(v)for k,v in REACTION_PLAYBACK.items()}, 'Reaction playback windows or density changed')
    require(policy['head_relative_amplitude']==HEAD_AMPLITUDE and policy['head_neck_relative_amplitude']==HEAD_NECK_AMPLITUDE,'HEAD source amplitude differs from its prepared implementation')
    pins=policy['input_animation_signatures']
    require(isinstance(pins,dict) and set(pins)=={'base','indigo','veteran'},'Reaction targets changed')
    for values in pins.values():
        require(isinstance(values,dict) and set(values)=={'idle',*REACTION_PLAYBACK},'Reaction signatures missing')
        require(all(isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef'for c in s)for s in values.values()),'Reaction signature invalid')
    return policy

CAP_ROLL_DEGREES=-30.
HEAD_AMPLITUDE=.35
HEAD_NECK_AMPLITUDE=.11
WINDOWS={'hit_body':(.05,.72),'hit_head':(.05,.72),'hit_side':(.05,1.18)}

def reaction_smooth(x):
 x=max(0.,min(1.,x));return x*x*x*(10+x*(-15+6*x))
def envelope(t,start,end):
 u=(t-start)/(end-start)
 return reaction_smooth(u/.22)*(1-reaction_smooth((u-.48)/.52))
def q_of(row):return Quaternion((row[3],*row[:3])).normalized()
def q_row(q):return (q.x,q.y,q.z,q.w)
def support_foot(doc,binary,guard_world):
 from attack_profiles import skin_attribute
 skin=doc['skins'][0];joints=skin['joints'];jn=[doc['nodes'][i]['name']for i in joints]
 bind=skin_attribute(doc,binary,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 palette=np.array([list(guard_world[i])for i in joints])@bind
 lows={'L_':float('inf'),'R_':float('inf')};seen=set()
 for mesh in doc['meshes']:
  for primitive in mesh['primitives']:
   at=primitive['attributes'];key=tuple(at[n]for n in ('POSITION','JOINTS_0','WEIGHTS_0'))
   if key in seen:continue
   seen.add(key);p=skin_attribute(doc,binary,key[0]);j=skin_attribute(doc,binary,key[1]).astype(int);weights=skin_attribute(doc,binary,key[2]).astype(float)
   if np.min(weights)<0 or np.max(abs(weights.sum(axis=1)-1))>1e-6:raise ValueError('Invalid sole skin weights')
   weights/=weights.sum(axis=1)[:,None]
   for side in lows:
    mask=np.array([n.startswith((side+'Foot',side+'Toe'))for n in jn])[j]
    ids=np.flatnonzero((weights*mask).sum(axis=1)>.5)
    if len(ids):
     blend=(palette[j[ids]]*weights[ids,:,None,None]).sum(axis=1);points=np.einsum('vij,vj->vi',blend,np.c_[p[ids],np.ones(len(ids))])
     lows[side]=min(lows[side],float(points[:,1].min()))
 if not all(math.isfinite(x)for x in lows.values()):raise ValueError('Both actual skinned soles are required')
 return min(lows,key=lows.get),lows

def apply_reaction_guard(character_id,doc,binary,policy,steel_points):
 validate_reaction_guard_policy(policy)
 require(character_id in policy['input_animation_signatures'], 'Unknown prepared reaction target')
 original = {a['name']: animation_signature(doc,binary,a) for a in doc['animations']}
 require(all(original[name] == sig for name,sig in policy['input_animation_signatures'][character_id].items()), 'Prepared reaction/idle input signature changed')
 if dict(REACTION_PLAYBACK)!=WINDOWS:raise ValueError('Runtime reaction windows changed')
 before=copy.deepcopy(doc);names={i:n.get('name','')for i,n in enumerate(doc['nodes'])};by_name={v:k for k,v in names.items()};_,parents,order=hierarchy(doc)
 skin=doc['skins'][0];joints=skin['joints']
 if len(joints)!=78:raise ValueError('Prepared 78-joint target required')
 idle=next(a for a in doc['animations']if a['name']=='idle');guard,_=animation_tracks(doc,binary,idle,False)
 guard_world=pose_world(doc,guard,0.,parents,order)
 support,sole_heights=support_foot(doc,binary,guard_world);free='R_'if support=='L_'else'L_'
 out=binary;report={}
 for clip in WINDOWS:
  animation=next(a for a in doc['animations']if a['name']==clip)
  tracks,times=animation_tracks(before,binary,animation,False)
  if len(tracks)!=234 or set(tracks)!={(i,p)for i in joints for p in ('translation','rotation','scale')}:raise ValueError('Reaction requires complete234 joint TRS')
  start,end=WINDOWS[clip];first=float32(start);last=float32(end)
  grid=sorted(set(times)|{0.,first,last,max(times)}|{float32(i/120)for i in range(math.ceil(start*120),math.floor(end*120)+1)})
  # First/final actual playback samples are exactly the same serialized guard, not a new decomposition.
  curves={key:[]for key in tracks}
  for t in grid:
   w=envelope(t,first,last)if first<t<last else 0.
   amplitude=HEAD_AMPLITUDE if clip=='hit_head'else 1.
   for (i,path),tr in tracks.items():
    g=sample_track(guard[i,path],0.,path=='rotation');ref=sample_track(tr,first,path=='rotation');sample=sample_track(tr,t,path=='rotation')
    regional_amplitude=HEAD_NECK_AMPLITUDE if clip=='hit_head' and names[i].startswith(('Neck','Head','FacialBone','L_Eye','R_Eye'))else amplitude
    if w==0 or names[i]=='BoneRoot':
     # Preserve raw stored key so endpoint quaternion normalization is exactly guard's.
     g=guard[i,path][1][0];value=tuple(g)
    elif path=='rotation':
     q=(q_of(g)@Quaternion((1,0,0,0)).slerp(q_of(ref).inverted()@q_of(sample),w*regional_amplitude)).normalized()
     value=q_row(q)
    elif path=='translation':value=tuple(a+w*amplitude*(c-b)for a,b,c in zip(g,ref,sample))
    else:value=tuple(a*(1+w*amplitude*(c/b-1))for a,b,c in zip(g,ref,sample))
    if path=='rotation' and curves[i,path] and sum(a*b for a,b in zip(value,curves[i,path][-1]))<0:value=tuple(-a for a in value)
    curves[i,path].append(value)
   if w:
    local=sampled_locals(before,guard,0.)
    for i in joints:
     local[i]=[Vector(curves[i,'translation'][-1]),q_of(curves[i,'rotation'][-1]),Vector(curves[i,'scale'][-1])]
    world=exact_worlds(before,local,parents,order)
    chest=world[by_name['Spine02']]@guard_world[by_name['Spine02']].inverted()
    wrist=chest@guard_world[by_name['L_Hand']].translation+Vector((-.025*w,0,.025*w))
    pole=chest@guard_world[by_name['L_Forearm']].translation+Vector((-.04*w,0,.02*w))
    aliases={name:by_name['L_'+name[2:]]for name in BONES}
    solve_arm(before,local,wrist,pole,aliases,parents,order)
    set_world_rotation(local,by_name['L_Hand'],chest.to_quaternion()@guard_world[by_name['L_Hand']].to_quaternion(),exact_worlds(before,local,parents,order),parents)
    if clip=='hit_side':
     world=exact_worlds(before,local,parents,order);s,e,h=[world[by_name[x]].translation for x in BONES]
     orientation=world[by_name['R_Hand']].to_quaternion();axis=(h-s).normalized()
     pole=s+Quaternion(axis,math.radians(-45)*w)@(e-s)
     solve_arm(before,local,h,pole,by_name,parents,order)
     set_world_rotation(local,by_name['R_Hand'],orientation,exact_worlds(before,local,parents,order),parents)
    if clip=='hit_side' and character_id == 'veteran':
     world=exact_worlds(before,local,parents,order);u=by_name['L_Upperarm'];f=by_name['L_Forearm'];h=by_name['L_Hand']
     forearm_q=world[f].to_quaternion();hand_q=world[h].to_quaternion();axis=(world[f].translation-world[u].translation).normalized()
     set_world_rotation(local,u,Quaternion(axis,math.radians(CAP_ROLL_DEGREES)*w)@world[u].to_quaternion(),world,parents)
     set_world_rotation(local,f,forearm_q,exact_worlds(before,local,parents,order),parents)
     set_world_rotation(local,h,hand_q,exact_worlds(before,local,parents,order),parents)
    # Authored grounded weight response: fixed BoneRoot; hips absorb weight rather than hop.
    # The left sole is a support; the right leg keeps its original unloading step trajectory.
    world=exact_worlds(before,local,parents,order)
    free_foot=world[by_name[free+'Foot']].copy()
    hip=world[by_name['Hip']].translation.copy();hip.y=guard_world[by_name['Hip']].translation.y-.025*w
    local[by_name['Hip']][0]=world[parents[by_name['Hip']]].inverted()@hip
    curves[by_name['Hip'],'translation'][-1]=tuple(local[by_name['Hip']][0])
    for side in ('L_','R_'):
     target=guard_world[by_name[support+'Foot']].translation.copy() if side==support else free_foot.translation+Vector((0,.015*w,0))
     pole=guard_world[by_name[side+'Calf']].translation+Vector((0,0,.04*w))
     aliases={name:by_name[side+label] for name,label in zip(BONES,('Thigh','Calf','Foot'))}
     solve_arm(before,local,target,pole,aliases,parents,order)
     desired=guard_world[by_name[support+'Foot']].to_quaternion() if side==support else free_foot.to_quaternion()
     set_world_rotation(local,by_name[side+'Foot'],desired,exact_worlds(before,local,parents,order),parents)
    for name in (support+'ToeBase',):
     if name in by_name:local[by_name[name]][1]=q_of(guard[by_name[name],'rotation'][1][0])
    selected=('L_Upperarm','L_Forearm','L_Hand')+(BONES if clip=='hit_side'else())+tuple(side+bone for side in ('L_','R_')for bone in ('Thigh','Calf','Foot','ToeBase'))
    for bone in selected:
     key=by_name[bone],'rotation';value=q_row(local[by_name[bone]][1]);previous=curves[key][-2]if len(curves[key])>1 else curves[key][-1]
     if sum(a*b for a,b in zip(value,previous))<0:value=tuple(-x for x in value)
     curves[key][-1]=value
  out,ta=append_accessor(doc,out,[(t,)for t in grid],'SCALAR')
  for key,values in curves.items():
   out,va=append_accessor(doc,out,values,'VEC4'if key[1]=='rotation'else'VEC3')
   c=next(c for c in animation['channels']if(c['target']['node'],c['target']['path'])==key)
   s=animation['samplers'][c['sampler']];s.update(input=ta,output=va,interpolation='LINEAR')
  report[clip]={'keys':len(grid),'original_keys':len(times),'window':[first,last],'support_side':support,'guard_sole_height_m':sole_heights,'relative_motion':'guard_local * inverse(reaction_entry_local) * reaction_local; all234TRS source deltas; quintic envelope'}
 # Verify original nonreaction curves and every full-Steel join in final serialized float32 curves.
 _,parents,order=hierarchy(doc)
 guard_tracks,_=animation_tracks(doc,out,next(a for a in doc['animations']if a['name']=='idle'),False)
 guard_frame=pose_world(doc,guard_tracks,0.,parents,order)[by_name['R_Hand']]
 guard_points=(np.asarray(guard_frame)@steel_points.T).T[:,:3]
 endpoint_max=0.
 for clip in WINDOWS:
  tracks,_=animation_tracks(doc,out,next(a for a in doc['animations']if a['name']==clip),False)
  for time in (0.,*WINDOWS[clip],max(tracks[next(iter(tracks))][0])):
   frame=pose_world(doc,tracks,time,parents,order)[by_name['R_Hand']]
   endpoint_max=max(endpoint_max,float(np.max(np.linalg.norm((np.asarray(frame)@steel_points.T).T[:,:3]-guard_points,axis=1))))
 require(endpoint_max<=1e-6,'Reaction full-Steel join differs from canonical guard')
 after={a['name']:animation_signature(doc,out,a)for a in doc['animations']}
 require(all(after[n]==sig for n,sig in original.items()if n not in WINDOWS),'A protected nonreaction clip changed')
 return out,{'applied':True,'clips':report,'full_steel_endpoint_max_m':endpoint_max,'all_other7_clips_exact':True,'reference':'same_target_idle0',
             'left_hand_chest_offset_m':[-.025,0,.025],'left_elbow_chest_offset_m':[-.04,0,.02],'side_right_elbow_swivel_degrees':-45,'veteran_side_upperarm_axial_roll_degrees':-30,'support_foot_selection':'lowest actual same-target guard sole','hip_weight_absorption_m':.025,'free_foot_lift_m':.015}
