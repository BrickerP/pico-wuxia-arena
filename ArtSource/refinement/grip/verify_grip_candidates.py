"""Verify reviewed finger-only candidates and exercise boundary rejection without Blender."""
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def read(path):
    data = path.read_bytes()
    magic, version, size = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or size != len(data):
        raise ValueError('invalid GLB header')
    length, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4E4F534A:
        raise ValueError('missing JSON')
    doc = json.loads(data[20:20 + length])
    n, kind = struct.unpack_from('<II', data, 20 + length)
    if kind != 0x004E4942:
        raise ValueError('missing embedded buffer')
    return doc, data[28 + length:28 + length + n]


def values(doc, binary, index, kind, width):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    if a['componentType'] != 5126 or a['type'] != kind or 'sparse' in a or a.get('normalized'):
        raise ValueError('invalid typed animation accessor')
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride', width * 4)
    if v.get('buffer', 0) != 0 or stride < width * 4 or a['count'] < 1 or offset + (a['count'] - 1) * stride + width * 4 > len(binary):
        raise ValueError('animation accessor out of bounds')
    rows = [struct.unpack_from('<' + 'f' * width, binary, offset + i * stride) for i in range(a['count'])]
    if not all(math.isfinite(x) for row in rows for x in row):
        raise ValueError('nonfinite animation data')
    return rows


def multiply(a, b):
    x, y, z, w = a
    X, Y, Z, W = b
    return (w*X+x*W+y*Z-z*Y, w*Y-x*Z+y*W+z*X, w*Z+x*Y-y*X+z*W, w*W-x*X-y*Y-z*Z)


def verify(source, original, candidate, binary, offsets, key):
    modified_names = set(offsets)
    expected_left = {'base': {}, 'indigo': {'L_Ring2': {'x_degrees': -9.0, 'z_degrees': 0.0}},
                     'veteran': {'L_Pinky1': {'x_degrees': 0.0, 'z_degrees': -18.0}}}[key]
    if {n: a for n, a in offsets.items() if n.startswith('L_')} != expected_left:
        raise ValueError('left correction outside reviewed set')
    for name, a in offsets.items():
        if not name.startswith(tuple(s+f for s in ('R_', 'L_') for f in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky'))) or not all(math.isfinite(v) for v in a.values()) or math.hypot(a['x_degrees'], a['z_degrees']) > 18.00001:
            raise ValueError('invalid finger correction')
    for field in ('nodes', 'skins', 'meshes', 'materials', 'images', 'textures'):
        if source.get(field) != candidate.get(field):
            raise ValueError('preserved field changed: ' + field)
    if binary[:len(original)] != original:
        raise ValueError('original binary changed, including bind/weight/mesh/time data')
    if candidate['accessors'][:len(source['accessors'])] != source['accessors']:
        raise ValueError('original accessor metadata changed')
    if len(source['animations']) != len(candidate['animations']):
        raise ValueError('clip count changed')
    changed = 0
    used_accessors, used_views = set(), set()
    seen_names = set()
    for old, new in zip(source['animations'], candidate['animations']):
        if old['name'] != new['name'] or old['channels'] != new['channels']:
            raise ValueError('clip channel or identity changed')
        if len(old['samplers']) != len(new['samplers']):
            raise ValueError('sampler count changed')
        for channel in old['channels']:
            i = channel['sampler']
            a, b = old['samplers'][i], new['samplers'][i]
            name = source['nodes'][channel['target']['node']].get('name')
            allowed = channel['target']['path'] == 'rotation' and name in modified_names
            if a['input'] != b['input'] or a.get('interpolation') != b.get('interpolation'):
                raise ValueError('timing or interpolation changed')
            if not allowed and a != b:
                raise ValueError('nonfinger animation changed')
            if allowed and a['output'] != b['output']:
                seen_names.add(name)
                index = b['output']
                if index < len(source['accessors']):
                    raise ValueError('corrected output was not appended')
                out = candidate['accessors'][index]
                view_index = out['bufferView']
                view = candidate['bufferViews'][view_index]
                if index in used_accessors or view_index in used_views or view_index < len(source['bufferViews']) or view.get('byteOffset', 0) < len(original):
                    raise ValueError('invalid appended rotation allocation')
                used_accessors.add(index)
                used_views.add(view_index)
                times = values(source, original, a['input'], 'SCALAR', 1)
                before = values(source, original, a['output'], 'VEC4', 4)
                after = values(candidate, binary, index, 'VEC4', 4)
                if len(before) != len(times) or len(after) != len(times) or view['byteLength'] != len(after)*16:
                    raise ValueError('rotation key count changed')
                ax, az = (math.radians(offsets[name][v]) / 2 for v in ('x_degrees', 'z_degrees'))
                delta = multiply((math.sin(ax), 0, 0, math.cos(ax)), (0, 0, math.sin(az), math.cos(az)))
                for q, actual in zip(before, after):
                    expected = multiply(q, delta)
                    norm = math.sqrt(sum(v*v for v in expected))
                    if norm < 1e-12 or abs(sum(v*v for v in actual)-1) > 1e-5 or max(abs(v/norm-w) for v, w in zip(expected, actual)) > 3e-6:
                        raise ValueError('rotation does not match reviewed q @ delta')
                changed += 1
            elif allowed:
                raise ValueError('missing corrected rotation output')
    if not changed:
        raise ValueError('no finger correction present')
    if seen_names != modified_names or len(candidate['accessors']) != len(source['accessors']) + changed or len(candidate['bufferViews']) != len(source['bufferViews']) + changed:
        raise ValueError('missing or unused appended rotation data')
    return changed


def main():
    calibration = json.loads((HERE / 'calibration.json').read_text())
    records = []
    for row in calibration['characters']:
        source_path = REPO / row['source']
        candidate_path = HERE / 'candidates' / (row['id'] + '.glb')
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != row['source_sha256']:
            raise ValueError('source identity mismatch')
        if hashlib.sha256(candidate_path.read_bytes()).hexdigest() != row['candidate_sha256']:
            raise ValueError('candidate identity mismatch')
        source, old_binary = read(source_path)
        candidate, binary = read(candidate_path)
        if len(candidate['skins'][0]['joints']) != 78 or len(candidate['animations']) != 8:
            raise ValueError('final character rig or clip count changed')
        modified = row['local_finger_offsets']
        changed = verify(source, old_binary, candidate, binary, modified, row['id'])
        rejected = []
        mutations = []
        mutated = copy.deepcopy(candidate)
        mutated['nodes'][source['skins'][0]['joints'][0]]['name'] += '_bad'
        mutations.append(('rest_node_mutation', mutated, binary))
        mutated = copy.deepcopy(candidate)
        mutated['animations'][0]['samplers'][0]['input'] += 1
        mutations.append(('time_accessor_mutation', mutated, binary))
        altered = bytearray(binary)
        altered[0] ^= 1
        mutations.append(('source_buffer_mutation', candidate, bytes(altered)))
        first = len(source['accessors'])
        appended = candidate['bufferViews'][candidate['accessors'][first]['bufferView']]['byteOffset']
        altered = bytearray(binary)
        struct.pack_into('<4f', altered, appended, 0, 0, 0, 0)
        mutations.append(('wrong_corrected_quaternion', candidate, bytes(altered)))
        altered = bytearray(binary)
        struct.pack_into('<f', altered, appended, float('nan'))
        mutations.append(('nonfinite_corrected_quaternion', candidate, bytes(altered)))
        mutated = copy.deepcopy(candidate)
        mutated['accessors'][first]['count'] += 1
        mutations.append(('rotation_key_count_mutation', mutated, binary))
        for name, doc, data in mutations:
            try:
                verify(source, old_binary, doc, data, modified, row['id'])
            except ValueError:
                rejected.append(name)
            else:
                raise AssertionError('accepted prohibited mutation: ' + name)
        forbidden = copy.deepcopy(modified)
        forbidden['L_Thumb1'] = {'x_degrees': 1.0, 'z_degrees': 0.0}
        try:
            verify(source, old_binary, candidate, binary, forbidden, row['id'])
        except ValueError:
            rejected.append('unreviewed_left_joint')
        else:
            raise AssertionError('accepted unreviewed left joint')
        records.append({'id': row['id'], 'modified_finger_rotation_tracks': changed,
                        'preservation_passed': True, 'rejected_boundary_cases': rejected})
    output = {'characters': records, 'happy_paths': len(records), 'boundary_rejections': sum(len(r['rejected_boundary_cases']) for r in records)}
    (HERE / 'verification.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output))


if __name__ == '__main__':
    main()
