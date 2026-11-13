"""Pinned material-response-only dao candidate and physical-source measurements.

All geometry, anchors, image payloads and non-material JSON remain exact.
Run from the project repository with ordinary Python 3.
"""
import copy
import hashlib
import json
import math
import statistics
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / 'ArtSource/dao/dao_study.glb'
SOURCE_SHA = '0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616'
PLAYER_SOURCE = REPO / 'ArtSource/dao/dao_grip.glb'
PLAYER_SOURCE_SHA = 'a2a5eae94ef6f577697d6c91a5cd4d7fe22e09e2f8b8e4411cd53768751739fc'
UPDATES = {
    'Steel | forged body': {'roughnessFactor': .30},
    'Steel | sharpened edge': {'roughnessFactor': .19, 'metallicFactor': 1.0},
    'Steel | dark spine': {'roughnessFactor': .45},
    'Brass | aged': {'roughnessFactor': .55},
    'Brass | polished ridges': {'roughnessFactor': .35},
    'Grip | worn cord': {'roughnessFactor': .80},
    'Grip | dark oxblood leather': {'roughnessFactor': .72},
}


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or length != len(data):
        raise ValueError('invalid source GLB')
    json_size, json_kind = struct.unpack_from('<II', data, 12)
    binary_size, binary_kind = struct.unpack_from('<II', data, 20 + json_size)
    if json_kind != 0x4E4F534A or binary_kind != 0x004E4942:
        raise ValueError('expected JSON and embedded binary chunks')
    return json.loads(data[20:20 + json_size]), data[28 + json_size:28 + json_size + binary_size]


def encode_glb(document, binary):
    encoded = json.dumps(document, separators=(',', ':'), ensure_ascii=False).encode()
    encoded += b' ' * (-len(encoded) % 4)
    if len(binary) % 4:
        raise ValueError('source binary chunk must retain its original alignment')
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary)) +
            struct.pack('<II', len(encoded), 0x4E4F534A) + encoded +
            struct.pack('<II', len(binary), 0x004E4942) + binary)


def typed(document, binary, index):
    acc = document['accessors'][index]
    view = document['bufferViews'][acc['bufferView']]
    component = {5121: ('B', 1), 5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}[acc['componentType']]
    width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[acc['type']]
    offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
    stride = view.get('byteStride', component[1] * width)
    return [struct.unpack_from('<' + component[0] * width, binary, offset + i * stride) for i in range(acc['count'])]


def geometry(document, binary, node_name):
    node = next(n for n in document['nodes'] if n.get('name') == node_name)
    if 'rotation' in node or 'matrix' in node:
        raise ValueError('measurement requires an explicit transform path for this source')
    translation, scale = node.get('translation', [0, 0, 0]), node.get('scale', [1, 1, 1])
    rows = []
    for primitive in document['meshes'][node['mesh']]['primitives']:
        p = typed(document, binary, primitive['attributes']['POSITION'])
        p = [tuple(v[i] * scale[i] + translation[i] for i in range(3)) for v in p]
        faces = typed(document, binary, primitive['indices'])
        index = [row[0] for row in faces]
        rows.append({'material': document['materials'][primitive['material']]['name'], 'positions': p,
                     'faces': [tuple(index[i:i+3]) for i in range(0, len(index), 3)]})
    return rows


def bounds(points):
    low = [min(p[a] for p in points) for a in range(3)]
    high = [max(p[a] for p in points) for a in range(3)]
    return {'min_metres': low, 'max_metres': high, 'size_mm': [(b-a)*1000 for a, b in zip(low, high)]}


def section(rows, height):
    groups = {}
    for row in rows:
        points = []
        for face in row['faces']:
            triangle = [row['positions'][i] for i in face]
            for a, b in zip(triangle, triangle[1:] + triangle[:1]):
                if abs(a[1] - height) < 1e-8:
                    points.append(a)
                if (a[1] - height) * (b[1] - height) < 0:
                    t = (height - a[1]) / (b[1] - a[1])
                    points.append(tuple(x + (y-x)*t for x, y in zip(a, b)))
        if points:
            groups[row['material']] = bounds(points)
    total = [tuple(v) for row in groups.values() for v in (row['min_metres'], row['max_metres'])]
    return {'blade_axis_y_metres': height, 'combined': bounds(total), 'material_sections': groups}


def measurements(document, binary):
    blade = geometry(document, binary, 'Blade')
    wrap = geometry(document, binary, 'Grip | cord wrap')[0]
    # The source exports each authored strip quad as two consecutive triangles.
    centres = []
    for a, b in zip(wrap['faces'][::2], wrap['faces'][1::2]):
        vertices = sorted(set(a + b))
        if len(vertices) != 4:
            raise ValueError('wrap topology no longer matches paired source quads')
        centres.append(tuple(sum(wrap['positions'][i][axis] for i in vertices) / 4 for axis in range(3)))
    centres.sort(key=lambda p: p[1])
    angles = [math.atan2(p[2], p[0]) for p in centres]
    steps = [(b-a + math.pi) % (2*math.pi) - math.pi for a, b in zip(angles, angles[1:])]
    turns = abs(sum(steps)) / (2*math.pi)
    all_points = [p for node in document['nodes'] if 'mesh' in node
                  for row in geometry(document, binary, node['name']) for p in row['positions']]
    anchors = {n['name']: n.get('translation', [0, 0, 0]) for n in document['nodes'] if n.get('name') in ('Grip', 'Blade_Base', 'Blade_Tip')}
    segment = math.dist(anchors['Blade_Base'], anchors['Blade_Tip'])
    return {'coordinate_space': 'native glTF metres, +Y blade length, X edge width, Z thickness',
        'geometry_changed': False, 'mesh_count': len(document['meshes']), 'material_count': len(document['materials']),
        'triangle_count': sum(len(typed(document, binary, p['indices'])) // 3 for m in document['meshes'] for p in m['primitives']),
        'whole_weapon_bounds': bounds(all_points), 'anchors_metres': anchors, 'blade_marker_segment_mm': segment * 1000,
        'blade_cross_sections': [section(blade, y) for y in (.03, .15, .35, .55, .70)],
        'guard_main_bounds': bounds([p for r in geometry(document, binary, 'Guard | flared oval') for p in r['positions']]),
        'guard_rim_bounds': bounds([p for r in geometry(document, binary, 'Guard | outer rim') for p in r['positions']]),
        'wrap': {'triangle_pairs': len(centres), 'observed_quad_centre_turns': turns,
                 'endpoint_half_step_corrected_turns_approx': turns + abs(statistics.median(steps)) / (2*math.pi),
                 'centreline_span_mm': (centres[-1][1] - centres[0][1]) * 1000,
                 'scope': 'winding of actual paired-quad centres in exported mesh; endpoint extrapolation approximate'}}


def candidate_document(source, updates=UPDATES):
    result = copy.deepcopy(source)
    materials = {m['name']: m for m in result['materials']}
    for name, values in updates.items():
        if name not in materials:
            raise ValueError('source material missing: ' + name)
        for field, value in values.items():
            if field not in ('roughnessFactor', 'metallicFactor') or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('unsupported or invalid material scalar')
            materials[name]['pbrMetallicRoughness'][field] = value
    a, b = copy.deepcopy(source), copy.deepcopy(result)
    del a['materials']; del b['materials']
    assert a == b, 'non-material JSON changed'
    for old, new in zip(source['materials'], result['materials']):
        expected = copy.deepcopy(old)
        expected['pbrMetallicRoughness'].update(updates.get(old['name'], {}))
        assert expected == new
    return result


def build():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('dao source identity changed')
    if hashlib.sha256(PLAYER_SOURCE.read_bytes()).hexdigest() != PLAYER_SOURCE_SHA:
        raise ValueError('player grip source identity changed')
    source, binary = read_glb(SOURCE)
    player_source, player_binary = read_glb(PLAYER_SOURCE)
    if len(source['materials']) != 8 or player_source['materials'] != source['materials']:
        raise ValueError('player/NPC material contracts differ')
    result = candidate_document(source)
    output = encode_glb(result, binary)
    HERE.mkdir(parents=True, exist_ok=True)
    candidate = HERE / 'dao_response.glb'
    candidate.write_bytes(output)
    decoded, actual = read_glb(candidate)
    assert actual == binary and decoded == result
    delta = [{'name': old['name'], 'before': old['pbrMetallicRoughness'],
              'after': new['pbrMetallicRoughness'], 'changed_scalars': UPDATES.get(old['name'], {})}
             for old, new in zip(source['materials'], result['materials'])]
    rejected = []
    for name, update in [('unknown_material', {'missing': {'roughnessFactor': .5}}),
                         ('out_of_range', {'Steel | forged body': {'roughnessFactor': -1}}),
                         ('nonfinite', {'Steel | forged body': {'roughnessFactor': float('nan')}}),
                         ('geometry_field', {'Steel | forged body': {'position': .5}})]:
        try:
            candidate_document(source, update)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('invalid update accepted: ' + name)
    shared = {'source': str(SOURCE.relative_to(REPO)), 'source_sha256': SOURCE_SHA,
              'candidate': str(candidate.relative_to(REPO)), 'candidate_sha256': hashlib.sha256(output).hexdigest(),
              'source_binary_sha256': hashlib.sha256(binary).hexdigest(), 'binary_exact': True,
              'all_nonmaterial_json_exact': True, 'source_bytes': SOURCE.stat().st_size,
              'candidate_bytes': len(output)}
    player_result = candidate_document(player_source)
    player_output = encode_glb(player_result, player_binary)
    player_candidate = HERE / 'dao_grip_response.glb'
    player_candidate.write_bytes(player_output)
    player_decoded, player_actual = read_glb(player_candidate)
    assert player_actual == player_binary and player_decoded == player_result
    assert player_result['materials'] == result['materials']
    anchors = {n['name']: copy.deepcopy(n) for n in player_source['nodes']
               if n.get('name') in ('Grip', 'Blade_Base', 'Blade_Tip')}
    if len(anchors) != 3 or any(k in anchors['Grip'] for k in ('matrix', 'translation', 'rotation', 'scale')):
        raise ValueError('player Grip identity-root contract changed')
    if anchors['Blade_Tip']['translation'][2] >= 0:
        raise ValueError('player blade must retain forward -Z')
    player = {'source': str(PLAYER_SOURCE.relative_to(REPO)), 'source_sha256': PLAYER_SOURCE_SHA,
        'candidate': str(player_candidate.relative_to(REPO)), 'candidate_sha256': hashlib.sha256(player_output).hexdigest(),
        'source_bytes': PLAYER_SOURCE.stat().st_size, 'candidate_bytes': len(player_output),
        'source_binary_sha256': hashlib.sha256(player_binary).hexdigest(), 'binary_exact': True,
        'all_nonmaterial_json_exact': True, 'material_response_identical_to_npc': True,
        'same_binary_as_npc_source': player_binary == binary, 'candidate_roundtrip': True,
        'coordinate_space': 'player Grip identity root; glTF +Y up; blade extends toward -Z',
        'anchors_exact': anchors}
    (HERE / 'material_delta.json').write_text(json.dumps({**shared, 'material_changes': delta,
        'player_frame': player,
        'validation': {'candidate_roundtrip': True, 'rejected_boundary_cases': rejected},
        'scope': 'material response only; all geometry/anchors/textures preserved; visual quality pending same-camera review'}, indent=2) + '\n')
    (HERE / 'source_measurements.json').write_text(json.dumps({**shared, **measurements(source, binary),
        'player_frame': player}, indent=2) + '\n')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    assert hashlib.sha256(PLAYER_SOURCE.read_bytes()).hexdigest() == PLAYER_SOURCE_SHA
    print(json.dumps({**shared, 'player_frame': player}), flush=True)


if __name__ == '__main__':
    build()
