"""Private v9 neck-only patch of frozen v7 GLBs; no producer or rig rebuild.

--analyze-only computes the exact float32 patch in memory without writing a
candidate. Run without that flag only after Root's generation gate opens.
"""
import argparse
import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
import numpy as np

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PARENT = HERE / 'candidate/v7'
OUTPUT = HERE / 'candidate/v9'
GAIN = .20
NECK01_SHARE = .45
ENTRY_START = .50
ENTRY_END = .65
EXIT_START = 1.30
EXIT_END = 1.75
PATCH_JOINTS = ('NeckTwist01', 'NeckTwist02')
PARENT_PINS = {
    'fine_overhead_raw.glb': '87c5fd566a63bba551cbbdfaa5841f519a7ed865cbbffc7da929c65219c9ef26',
    'fine_overhead_body.glb': 'f6390ce0ee6d32b7210c29bb20b38d2ccf1dd379d9875f3f5d19f383f9e2debb',
    'fine_overhead_preview.glb': '285d3e34e94e335d2e5f3705d77483fabbe3a297ccfbdec08153bcab1b13a21c',
    'fine_overhead_metadata.json': '1d395763496e4d9be2c36521575eb1eea2e5ccb906867212dbeba1b5656d8241',
    'fine_overhead_alignment.json': '2ce9f3a80d70683651a61e02aed4bbc3ed28aa62aee3be66e9bb508fd78ee6d0',
}


def digest(value):
    data = value if isinstance(value, (bytes, bytearray)) else Path(value).read_bytes()
    return hashlib.sha256(data).hexdigest()


def identity(path):
    path = Path(path)
    return {'file': str(path.relative_to(REPO)), 'sha256': digest(path), 'bytes': path.stat().st_size}


def read_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 28 or struct.unpack_from('<III', data) != (0x46546c67, 2, len(data)):
        raise ValueError('invalid complete GLB2 file')
    size, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4e4f534a or size % 4 or 28 + size > len(data):
        raise ValueError('invalid embedded GLB JSON chunk')
    binary_size, binary_kind = struct.unpack_from('<II', data, 20 + size)
    if binary_kind != 0x004e4942 or 28 + size + binary_size != len(data):
        raise ValueError('expected exactly one complete embedded binary chunk')
    return json.loads(data[20:20 + size]), data[28 + size:], 28 + size, data


def accessor(doc, binary, index):
    item = doc['accessors'][index]
    view = doc['bufferViews'][item['bufferView']]
    if 'sparse' in item or view.get('buffer', 0) != 0 or item['componentType'] != 5126:
        raise ValueError('animation accessor must be embedded nonsparse float32')
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[item['type']]
    stride = view.get('byteStride', width * 4)
    start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    end = start + (item['count'] - 1) * stride + width * 4
    if item['count'] < 1 or stride < width * 4 or end > len(binary) or end > view.get('byteOffset', 0) + view['byteLength']:
        raise ValueError('animation accessor exceeds its buffer view')
    result = np.ndarray((item['count'], width), dtype='<f4', buffer=binary,
                        offset=start, strides=(stride, 4)).astype(float)
    if not np.isfinite(result).all():
        raise ValueError('nonfinite animation accessor')
    return result


def tracks(doc, binary):
    if len(doc.get('animations', [])) != 1:
        raise ValueError('expected one attack_overhead animation')
    animation = doc['animations'][0]
    if animation.get('name') != 'attack_overhead':
        raise ValueError('unexpected animation identity')
    result = {}
    for channel in animation['channels']:
        target = channel['target']
        key = target['node'], target['path']
        sampler = animation['samplers'][channel['sampler']]
        mode = sampler.get('interpolation', 'LINEAR')
        if key in result or mode not in ('LINEAR', 'STEP'):
            raise ValueError('duplicate animation target or unsupported interpolation')
        times = accessor(doc, binary, sampler['input'])[:, 0]
        values = accessor(doc, binary, sampler['output'])
        if len(times) != len(values) or not np.all(np.diff(times) > 0) or times[0] < 0:
            raise ValueError('invalid animation timeline')
        result[key] = times, values, mode, sampler['output']
    return result


def rotation3(matrix):
    u, _, vt = np.linalg.svd(np.asarray(matrix)[:3, :3])
    result = u @ vt
    if np.linalg.det(result) < .999999:
        raise ValueError('rotation frame has reflection or singular scale')
    return result


def quaternion_matrix(value):
    q = np.asarray(value, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all() or np.linalg.norm(q) < 1e-12:
        raise ValueError('invalid quaternion')
    x, y, z, w = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def matrix_quaternion(matrix):
    m = rotation3(matrix)
    trace = float(np.trace(m))
    if trace > 0:
        s = math.sqrt(trace + 1.) * 2
        q = np.array([(m[2, 1]-m[1, 2])/s, (m[0, 2]-m[2, 0])/s,
                      (m[1, 0]-m[0, 1])/s, .25*s])
    else:
        i = int(np.argmax(np.diag(m)))
        j, k = (i+1) % 3, (i+2) % 3
        s = math.sqrt(max(0., 1.+m[i, i]-m[j, j]-m[k, k])) * 2
        if s < 1e-12:
            raise ValueError('indeterminate rotation quaternion')
        q = np.zeros(4)
        q[i], q[j], q[k] = .25*s, (m[j, i]+m[i, j])/s, (m[k, i]+m[i, k])/s
        q[3] = (m[k, j]-m[j, k])/s
    return q / np.linalg.norm(q)


def sample(track, time):
    times, values, mode = track[:3]
    after = int(np.searchsorted(times, time, side='right'))
    if after == 0:
        return values[0]
    if after == len(times) or mode == 'STEP':
        return values[after-1]
    before = after-1
    amount = (time-times[before])/(times[after]-times[before])
    a, b = values[before], values[after]
    if values.shape[1] != 4:
        return a+(b-a)*amount
    a, b = a/np.linalg.norm(a), b/np.linalg.norm(b)
    dot = float(a @ b)
    if dot < 0:
        b, dot = -b, -dot
    if dot > .9995:
        value = a+(b-a)*amount
        return value/np.linalg.norm(value)
    angle = math.acos(max(-1., min(1., dot)))
    return (math.sin((1-amount)*angle)*a+math.sin(amount*angle)*b)/math.sin(angle)


def pose(doc, animation_tracks=None, time=0.):
    local = np.tile(np.eye(4), (len(doc['nodes']), 1, 1))
    for index, node in enumerate(doc['nodes']):
        if 'matrix' in node:
            local[index] = np.array(node['matrix']).reshape(4, 4).T
            continue
        values = {}
        for path, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
            key = index, path
            values[path] = sample(animation_tracks[key], time) if animation_tracks and key in animation_tracks else np.array(node.get(path, default))
        local[index, :3, :3] = quaternion_matrix(values['rotation']) @ np.diag(values['scale'])
        local[index, :3, 3] = values['translation']
    parents = {child: index for index, node in enumerate(doc['nodes']) for child in node.get('children', [])}
    world = np.empty_like(local)
    done, active = set(), set()
    def visit(index):
        if index in active:
            raise ValueError('cyclic rig')
        if index in done:
            return world[index]
        active.add(index)
        world[index] = visit(parents[index]) @ local[index] if index in parents else local[index]
        active.remove(index)
        done.add(index)
        return world[index]
    for index in range(len(local)):
        visit(index)
    return local, world


def smooth(value):
    value = min(1., max(0., float(value)))
    return min(1., max(0., value**3*(10.+value*(-15.+6.*value))))


def correction_weight(time):
    if isinstance(time, bool) or not isinstance(time, (int, float, np.floating)) or not math.isfinite(time) or not 0 <= time <= 1.75:
        raise ValueError('neck sample must lie in finite source0–1.75 seconds')
    return smooth((time-ENTRY_START)/(ENTRY_END-ENTRY_START))*(1.-smooth((time-EXIT_START)/(EXIT_END-EXIT_START)))


def axis_rotation(axis, angle):
    axis = np.asarray(axis, dtype=float)
    if axis.shape != (3,) or not np.isfinite(axis).all() or np.linalg.norm(axis) < 1e-10 or not math.isfinite(angle):
        raise ValueError('invalid neck swing axis/angle')
    x, y, z = axis/np.linalg.norm(axis)
    skew = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return np.eye(3)+math.sin(angle)*skew+(1.-math.cos(angle))*(skew @ skew)


def head_metrics(doc, animation_tracks, times, normalization=None):
    norm = np.eye(4) if normalization is None else np.asarray(normalization)
    names = {node.get('name'): index for index, node in enumerate(doc['nodes'])}
    _, guard = pose(doc, animation_tracks, 0.)
    _, rest = pose(doc)
    qg = rotation3(norm @ guard[names['Head']])
    qr = rotation3(norm @ rest[names['Head']])
    forward_local, right_local = qg.T @ np.array([0., 0., 1.]), qg.T @ np.array([1., 0., 0.])
    fixed_forward = qr.T @ np.array([0., 0., 1.])
    result = []
    for time in times:
        _, world = pose(doc, animation_tracks, float(time))
        head = norm @ world[names['Head']]
        rotation = rotation3(head)
        forward, ear = rotation @ forward_local, rotation @ right_local
        horizontal = np.array([forward[0], 0., forward[2]])
        if np.linalg.norm(horizontal) < 1e-8:
            raise ValueError('head yaw/roll indeterminate at a vertical forward axis')
        horizontal /= np.linalg.norm(horizontal)
        right = np.cross(np.array([0., 1., 0.]), horizontal)
        up = np.cross(forward, right)
        fixed = rotation @ fixed_forward
        result.append({'source_seconds': float(time),
          'guard_calibrated_pitch_degrees': math.degrees(math.atan2(forward[1], math.hypot(forward[0], forward[2]))),
          'yaw_degrees': math.degrees(math.atan2(forward[0], forward[2])),
          'anatomical_roll_degrees': math.degrees(math.atan2(float(ear @ up), float(ear @ right))),
          'ear_line_elevation_degrees': math.degrees(math.asin(float(np.clip(ear[1], -1., 1.)))),
          'fixed_rest_axis_pitch_degrees': math.degrees(math.atan2(fixed[1], math.hypot(fixed[0], fixed[2]))),
          'head_origin_metres': head[:3, 3].tolist()})
    return result


def patched_bytes(path, normalization=None, gain=GAIN, neck01_share=NECK01_SHARE):
    if not math.isfinite(gain) or not 0 < gain <= 1 or not math.isfinite(neck01_share) or not 0 <= neck01_share <= 1:
        raise ValueError('invalid fixed neck gain/share')
    doc, binary, bin_start, encoded = read_glb(path)
    animation_tracks = tracks(doc, binary)
    names = {node.get('name'): index for index, node in enumerate(doc['nodes'])}
    if any(name not in names for name in (*PATCH_JOINTS, 'Spine02', 'Head')):
        raise ValueError('required neck hierarchy absent')
    parents = {child: index for index, node in enumerate(doc['nodes']) for child in node.get('children', [])}
    if parents[names['NeckTwist01']] != names['Spine02'] or parents[names['NeckTwist02']] != names['NeckTwist01'] or parents[names['Head']] != names['NeckTwist02']:
        raise ValueError('unexpected neck-only isolation hierarchy')
    norm = np.eye(4) if normalization is None else np.asarray(normalization)
    time_values = animation_tracks[names['NeckTwist01'], 'rotation'][0]
    if len(time_values) != 211 or time_values[0] != 0 or time_values[-1] != 1.75:
        raise ValueError('expected frozen211-key/120Hz source0–1.75')
    old_metrics = head_metrics(doc, animation_tracks, time_values, norm)
    new_rows = {joint: animation_tracks[names[joint], 'rotation'][1].copy() for joint in PATCH_JOINTS}
    for frame, (time, metrics) in enumerate(zip(time_values, old_metrics)):
        if frame in (0, len(time_values)-1):
            continue
        _, world = pose(doc, animation_tracks, float(time))
        yaw = math.radians(metrics['yaw_degrees'])
        right_axis = np.array([math.cos(yaw), 0., -math.sin(yaw)])
        # A positive rotation about this horizontal right axis pitches forward
        # downward, so raising the old negative pitch uses a negative angle.
        angle = math.radians((1.-gain)*metrics['guard_calibrated_pitch_degrees']*correction_weight(float(time)))
        old01 = rotation3(norm @ world[names['NeckTwist01']])
        old02 = rotation3(norm @ world[names['NeckTwist02']])
        parent_rotation = rotation3(norm @ world[names['Spine02']])
        new01 = axis_rotation(right_axis, angle*neck01_share) @ old01
        new02 = axis_rotation(right_axis, angle) @ old02
        for joint, rotation in [('NeckTwist01', parent_rotation.T @ new01), ('NeckTwist02', new01.T @ new02)]:
            q = matrix_quaternion(rotation)
            if q @ new_rows[joint][frame-1] < 0:
                q = -q
            new_rows[joint][frame] = q
    output = bytearray(encoded)
    changed_ranges = []
    for joint, rows in new_rows.items():
        track = animation_tracks[names[joint], 'rotation']
        item = doc['accessors'][track[3]]
        view = doc['bufferViews'][item['bufferView']]
        if item['type'] != 'VEC4' or view.get('byteStride', 16) != 16:
            raise ValueError('neck output must be tightly packed VEC4 float32')
        if sum(value[3] == track[3] for value in animation_tracks.values()) != 1:
            raise ValueError('neck accessor is shared with a non-target track')
        offset = bin_start+view.get('byteOffset', 0)+item.get('byteOffset', 0)
        encoded_rows = np.asarray(rows, dtype='<f4').tobytes()
        output[offset:offset+len(encoded_rows)] = encoded_rows
        changed_ranges.append([offset, offset+len(encoded_rows)])
    patched_binary = bytes(output[bin_start:])
    new_tracks = tracks(doc, patched_binary)
    return bytes(output), {'old_head_frames': old_metrics,
                           'head_frames': head_metrics(doc, new_tracks, time_values, norm),
                           'changed_byte_ranges': changed_ranges}


def main(analyze_only=False):
    for name, sha in PARENT_PINS.items():
        if digest(PARENT/name) != sha:
            raise ValueError('frozen v7 parent changed: '+name)
    alignment = json.loads((PARENT/'fine_overhead_alignment.json').read_text())
    parent_meta = json.loads((PARENT/'fine_overhead_metadata.json').read_text())
    norm = np.array(alignment['normalization_matrix_gltf']).reshape(4, 4).T
    outputs, metrics = {}, {}
    for name in ('fine_overhead_raw.glb', 'fine_overhead_body.glb', 'fine_overhead_preview.glb'):
        output, report = patched_bytes(PARENT/name, norm if name.endswith('_raw.glb') else None)
        outputs[name], metrics[name] = output, report
    summary = {'analyze_only': analyze_only, 'generated_candidates': False, 'clip': 'attack_overhead',
      'gain': GAIN, 'neck01_share': NECK01_SHARE, 'neck02_share': 1.-NECK01_SHARE,
      'patch_joints': list(PATCH_JOINTS), 'Head_local_untouched': True,
      'predicted_output_sha256': {name: digest(value) for name, value in outputs.items()},
      'pitch_range_degrees': [min(row['guard_calibrated_pitch_degrees'] for row in metrics['fine_overhead_preview.glb']['head_frames']),
                              max(row['guard_calibrated_pitch_degrees'] for row in metrics['fine_overhead_preview.glb']['head_frames'])]}
    if analyze_only:
        print(json.dumps(summary, indent=2))
        return
    if OUTPUT.exists():
        raise ValueError('new v9 output already exists; do not overwrite a staged candidate')
    profile = REPO/'app/src/main/assets/models/opponents/base_attack_profiles.json'
    formal = REPO/'app/src/main/assets/models/opponents/base.glb'
    current_inputs = {name: identity(PARENT/name) for name in PARENT_PINS}
    phase_inputs = {'profile': identity(profile), 'model': identity(formal), 'builder': identity(Path(__file__))}
    metadata = {'completion': 'candidate_ready_for_surface_and_visual_verification', 'clip': 'attack_overhead',
      'duration_seconds': 1.75, 'source_range_seconds': [0., 1.75], 'sample_rate_hz': 120, 'sample_count': 211,
      'phase_markers': parent_meta['phase_markers'], 'parent_v7': current_inputs, 'current_phase_inputs': phase_inputs,
      'patch_policy': {'joints': list(PATCH_JOINTS), 'channels': ['rotation'], 'Head_local_unchanged': True,
        'all_other_glb_bytes_unchanged': True, 'gain': GAIN, 'neck01_share': NECK01_SHARE,
        'neck02_share': 1.-NECK01_SHARE, 'C2_envelope_seconds': [ENTRY_START, ENTRY_END, EXIT_START, EXIT_END],
        'guard_endpoints_original_float32_bytes': True},
      'head_frame_definitions': {'prepared_axes': '+Y up/+Z forward; positions metres; angles degrees',
        'guard_calibrated': 'Qg is source0 prepared Head world rotation; F_local=Qg^-1 Z, ear/right_local=Qg^-1 X, guard pitch/roll0; positive pitch up',
        'fixed_rest_axis': 'rest Head world rotation calibrates prepared+Z; equivalent to former raw+X rest anatomical forward; guard here is approximately+4.48deg, not0',
        'anatomical_roll': 'ear/right vector angle in the level-heading right and forward/world-up reference; retained by the sagittal swing',
        'ear_line_elevation': 'asin(world ear/right Y); this literal line elevation can change with pitch even when anatomical roll is retained'},
      'head_metrics': metrics['fine_overhead_preview.glb'],
      'chest_and_body_policy': 'Spine02 and all nodes outside the complete NeckTwist01 subtree retain v7 world matrices; Head-Hip lean may change and is not proof of chest correction.',
      'calibration_stages': parent_meta['calibration_stages'], 'preview_grounding': parent_meta['preview_grounding'],
      'foot_samples_source': {'parent_metadata': current_inputs['fine_overhead_metadata.json'], 'json_path': '$.frames[*].foot_surfaces', 'frame': 'prepared source before formal root shift; feet unchanged'},
      'raw_output': {'file': 'fine_overhead_raw.glb', 'sha256': digest(outputs['fine_overhead_raw.glb'])},
      'preview_outputs': [{'file': name, 'sha256': digest(outputs[name])} for name in ('fine_overhead_body.glb', 'fine_overhead_preview.glb')],
      'limits': ['Native yaw and anatomical roll are retained; existing lateral head tilt is not flattened.',
                 'The new head/neck surface requires fresh full-body/steel BVH and visual verification.',
                 'No SDK/device behavior is validated by this private neck patch.']}
    # Stage all data only after every immutable input and phase identity is read.
    for name, sha in PARENT_PINS.items():
        if digest(PARENT/name) != sha:
            raise ValueError('parent changed during neck computation')
    OUTPUT.mkdir()
    for name, value in outputs.items():
        (OUTPUT/name).write_bytes(value)
    (OUTPUT/'fine_overhead_metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print(json.dumps({**summary, 'analyze_only': False, 'generated_candidates': True, 'output': str(OUTPUT)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze-only', action='store_true')
    main(parser.parse_args().analyze_only)
