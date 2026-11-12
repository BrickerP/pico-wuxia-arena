"""Build a narrow, source-bound TANGENT JSON delta; never write a GLB.

Zero +U directions come from indexed UV/geometric fans on the main head.
Only main-head rows whose normalized |N.T| exceeds .001 are orthogonalized.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import graft_head as glb

ORTHOGONALITY_TRIGGER = .001
REPAIRED_ORTHOGONALITY_LIMIT = 2e-6


def rows(document, binary, accessor):
    return np.asarray(glb.accessor_rows(document, binary, accessor), dtype=np.float64)


def unit(vector, label):
    vector = np.asarray(vector, dtype=np.float64)
    length = np.linalg.norm(vector)
    if not np.all(np.isfinite(vector)) or length <= 1e-12:
        raise ValueError('Cannot derive stable ' + label)
    return vector / length


def indices(document, binary, primitive):
    if primitive.get('mode', 4) != 4:
        raise ValueError('Head must use indexed triangles')
    if 'indices' in primitive:
        result = rows(document, binary, primitive['indices']).astype(np.int64).reshape(-1)
    else:
        result = np.arange(document['accessors'][primitive['attributes']['POSITION']]['count'])
    if len(result) % 3:
        raise ValueError('Invalid head triangle index count')
    return result.reshape(-1, 3)


def stream_hash(document, binary, accessor):
    return glb.sha(glb.stream_bytes(document, binary, accessor))


def tangent_matches(document, binary, stream):
    referenced = {p['attributes']['TANGENT'] for mesh in document['meshes']
                  for p in mesh['primitives'] if 'TANGENT' in p['attributes']}
    matches = [i for i in referenced if document['accessors'][i].get('componentType') == 5126
               and document['accessors'][i].get('type') == 'VEC4'
               and document['accessors'][i]['count'] == stream['vertex_count']
               and stream_hash(document, binary, i) == stream['old_stream_sha256']]
    if len(matches) != 1:
        raise ValueError('Expected one TANGENT stream matching old SHA/count; found ' + str(len(matches)))
    return matches[0]


def byte_offset(document, accessor_index, vertex):
    accessor = document['accessors'][accessor_index]
    view = document['bufferViews'][accessor['bufferView']]
    return view.get('byteOffset', 0) + accessor.get('byteOffset', 0) + vertex * view.get('byteStride', 16)


def apply_delta(document, binary, delta, source_sha256):
    if source_sha256 not in delta.get('verified_source_sha256', [delta['source_sha256']]):
        raise ValueError('Source SHA does not match the verified delta source')
    patched = bytearray(binary)
    writes = {}
    for stream in delta['streams']:
        accessor = tangent_matches(document, binary, stream)
        old_rows = rows(document, binary, accessor)
        for change in stream['changes']:
            vertex = change['vertex']
            if type(vertex) is not int or not 0 <= vertex < len(old_rows):
                raise ValueError('Invalid delta vertex')
            if not np.array_equal(old_rows[vertex], np.asarray(change['old'], dtype=np.float64)):
                raise ValueError('Delta old value does not match source vertex')
            new = np.asarray(change['new'], dtype=np.float64)
            if new.shape != (4,) or not np.all(np.isfinite(new)) or new[3] != old_rows[vertex, 3]:
                raise ValueError('Delta must preserve finite TANGENT W exactly')
            offset = byte_offset(document, accessor, vertex)
            payload = struct.pack('<3f', *new[:3])
            if offset in writes and writes[offset] != payload:
                raise ValueError('Conflicting delta changes to shared row')
            writes[offset] = payload
    for offset, payload in writes.items():
        patched[offset:offset + 12] = payload
    return bytes(patched)


def derive_zero_tangent(main, vertex):
    normal = unit(main['NORMAL'][vertex], 'vertex normal')
    incident = np.flatnonzero(np.any(main['faces'] == vertex, axis=1))
    candidates, evidence, neighbors = [], [], []
    for face_id in incident:
        face = main['faces'][face_id]
        position, uv = main['POSITION'][face], main['TEXCOORD_0'][face]
        edge1, edge2 = position[1] - position[0], position[2] - position[0]
        uv1, uv2 = uv[1] - uv[0], uv[2] - uv[0]
        determinant = float(uv1[0] * uv2[1] - uv2[0] * uv1[1])
        area2 = float(np.linalg.norm(np.cross(edge1, edge2)))
        if abs(determinant) <= 1e-14 or area2 <= 1e-14:
            continue
        derivative = (edge1 * uv2[1] - edge2 * uv1[1]) / determinant
        projected = derivative - np.dot(derivative, normal) * normal
        corner = int(np.flatnonzero(face == vertex)[0])
        other = [i for i in range(3) if i != corner]
        edge_a, edge_b = position[other[0]] - position[corner], position[other[1]] - position[corner]
        denominator = np.linalg.norm(edge_a) * np.linalg.norm(edge_b)
        angle = float(np.arccos(np.clip(np.dot(edge_a, edge_b) / denominator, -1, 1)))
        weight = area2 * angle
        info = {'triangle': int(face_id), 'vertex_ids': face.tolist(), 'uv_determinant': determinant,
                'twice_geometric_area': area2, 'corner_angle_radians': angle,
                'uv_positive_u_derivative': derivative.tolist(), 'projected_derivative': projected.tolist()}
        evidence.append(info)
        if np.linalg.norm(projected) > 1e-12:
            candidates.append((unit(projected, 'UV +U tangent'), weight, info))
        for neighbor in face:
            if neighbor == vertex or main['TANGENT'][neighbor, 3] != main['TANGENT'][vertex, 3]:
                continue
            tangent = main['TANGENT'][neighbor, :3]
            projected_neighbor = tangent - np.dot(tangent, normal) * normal
            if np.all(np.isfinite(projected_neighbor)) and np.linalg.norm(projected_neighbor) > 1e-12:
                neighbors.append((unit(projected_neighbor, 'chart neighbor tangent'), area2,
                                  {'vertex': int(neighbor), 'triangle': int(face_id), 'old_tangent': main['TANGENT'][neighbor].tolist()}))
    if candidates:
        total = sum(direction * weight for direction, weight, _ in candidates)
        weight_sum = sum(weight for _, weight, _ in candidates)
        if np.linalg.norm(total) > 1e-8 * weight_sum:
            return unit(total, 'weighted +U fan'), {'method': 'area_times_corner_angle_weighted_uv_fan', 'faces': evidence}
        selected = max(candidates, key=lambda candidate: candidate[1])
        return selected[0], {'method': 'largest_stable_uv_facet_after_fan_cancellation', 'selected_face': selected[2], 'faces': evidence}
    if neighbors:
        selected = max(neighbors, key=lambda candidate: candidate[1])
        return selected[0], {'method': 'valid_same_chart_neighbor', 'selected_neighbor': selected[2], 'faces': evidence}
    raise ValueError('Cannot derive stable +U from the incident UV/geometric fan for vertex ' + str(vertex))


def audit_stream(document, binary, accessor, primitive_records):
    tangent = rows(document, binary, accessor)
    used = np.unique(np.concatenate([indices(document, binary, p).reshape(-1) for _, _, p in primitive_records]))
    normal = rows(document, binary, primitive_records[0][2]['attributes']['NORMAL'])
    length = np.linalg.norm(tangent[:, :3], axis=1)
    nl = np.linalg.norm(normal, axis=1)
    valid = np.all(np.isfinite(tangent), axis=1) & (length > 1e-12) & (nl > 1e-12)
    dot = np.full(len(tangent), np.nan)
    dot[valid] = np.abs(np.sum(normal[valid] * tangent[valid, :3], axis=1)) / (nl[valid] * length[valid])
    return {'vertices': len(tangent), 'used_vertices': len(used),
            'zero_xyz_all': int(np.sum(np.all(tangent[:, :3] == 0, axis=1))),
            'nonfinite_all': int(np.sum(~np.all(np.isfinite(tangent), axis=1))),
            'w_zero_all': int(np.sum(tangent[:, 3] == 0)),
            'used_abs_normal_tangent_dot_max': float(np.nanmax(dot[used])) if len(used) else None,
            'used_abs_dot_gt_0_001': int(np.sum(dot[used] > ORTHOGONALITY_TRIGGER)),
            'used_abs_dot_gt_2e_6': int(np.sum(dot[used] > REPAIRED_ORTHOGONALITY_LIMIT))}


def primitive_fingerprint(document, binary, primitive):
    result = {name: stream_hash(document, binary, primitive['attributes'][name])
              for name in ('POSITION', 'NORMAL', 'TEXCOORD_0')}
    result['indices'] = stream_hash(document, binary, primitive['indices']) if 'indices' in primitive else None
    return result


def build_delta(source, raw=None):
    source = Path(source).resolve()
    source_bytes = source.read_bytes()
    document, binary = glb.read_glb(source)
    json_before = json.dumps(document, sort_keys=True)
    skinned = [node for node in document['nodes'] if 'mesh' in node and 'skin' in node]
    if len(skinned) != 1:
        raise ValueError('Expected one skinned head/body mesh')
    mesh_index = skinned[0]['mesh']
    primitives = document['meshes'][mesh_index]['primitives']
    main_primitive = primitives[1]
    main_material = main_primitive['material']
    material = document['materials'][main_material]
    if (main_material == primitives[0].get('material') or not material.get('name', '').startswith('tripo_')
            or material.get('normalTexture', {}).get('scale', 1) <= 0):
        raise ValueError('Primitive 1 must be the active head-skin material')
    main = {name: rows(document, binary, main_primitive['attributes'][name])
            for name in ('POSITION', 'NORMAL', 'TEXCOORD_0', 'TANGENT')}
    main['faces'] = indices(document, binary, main_primitive)
    main_accessor = main_primitive['attributes']['TANGENT']
    groups = defaultdict(list)
    for pi, primitive in enumerate(primitives):
        if primitive.get('material') == main_material:
            if 'TANGENT' not in primitive['attributes']:
                raise ValueError('Head/rim primitive lacks TANGENT')
            groups[primitive['attributes']['TANGENT']].append((mesh_index, pi, primitive))
    delta = {'schema_version': 1, 'source': str(source), 'source_sha256': glb.sha(source_bytes),
             'raw_geometry_sha256': None, 'verified_source_sha256': [glb.sha(source_bytes)],
             'streams': [], 'limits': 'JSON tangent-only delta; no GLB written. Missing TANGENT streams and degenerate UVs can still cause native-generated invalid tangents; this is not a native fix claim.'}
    allowed_bytes, repaired_dot = set(), []
    for accessor, primitive_records in groups.items():
        definition = document['accessors'][accessor]
        if definition['componentType'] != 5126 or definition['type'] != 'VEC4':
            raise ValueError('Expected FLOAT VEC4 tangent stream')
        old = rows(document, binary, accessor)
        normal = rows(document, binary, primitive_records[0][2]['attributes']['NORMAL'])
        changes = {}
        for vertex in np.flatnonzero(np.all(old[:, :3] == 0, axis=1)):
            vertex = int(vertex)
            for name in ('POSITION', 'NORMAL', 'TEXCOORD_0'):
                mapped = rows(document, binary, primitive_records[0][2]['attributes'][name])
                if vertex >= len(main[name]) or not np.array_equal(mapped[vertex], main[name][vertex]):
                    raise ValueError('Head/rim logical vertex mapping mismatch')
            direction, evidence = derive_zero_tangent(main, vertex)
            changes[vertex] = (direction, 'zero_xyz_from_main_uv_fan', evidence)
        if accessor == main_accessor:
            used = np.unique(main['faces'])
            lengths = np.linalg.norm(old[:, :3], axis=1) * np.linalg.norm(normal, axis=1)
            dots = np.abs(np.sum(old[:, :3] * normal, axis=1)) / np.maximum(lengths, 1e-30)
            for vertex in used[dots[used] > ORTHOGONALITY_TRIGGER]:
                vertex = int(vertex)
                n = unit(normal[vertex], 'vertex normal')
                direction = unit(old[vertex, :3] - np.dot(old[vertex, :3], n) * n, 'orthogonalized tangent (normal-parallel source rejected)')
                changes[vertex] = (direction, 'normal_orthogonalization', {'old_normalized_abs_dot': float(dots[vertex]), 'normal': normal[vertex].tolist()})
        stream = {'old_stream_sha256': stream_hash(document, binary, accessor), 'vertex_count': len(old),
                  'accessors': [accessor], 'role_primitives': [{'mesh': mi, 'primitive': pi, 'material': p['material']}
                    for mi, pi, p in primitive_records], 'changes': [],
                  'before': audit_stream(document, binary, accessor, primitive_records)}
        for vertex, (direction, reason, evidence) in sorted(changes.items()):
            new = np.asarray([*direction, old[vertex, 3]], dtype=np.float32).astype(np.float64)
            stream['changes'].append({'vertex': vertex, 'old': old[vertex].tolist(), 'new': new.tolist(), 'reason': reason, 'evidence': evidence})
            allowed_bytes.update(range(byte_offset(document, accessor, vertex), byte_offset(document, accessor, vertex) + 12))
            repaired_dot.append(abs(float(np.dot(unit(normal[vertex], 'normal'), unit(new[:3], 'rounded tangent')))))
        delta['streams'].append(stream)
    patched = apply_delta(document, binary, delta, delta['source_sha256'])
    changed_bytes = np.flatnonzero(np.frombuffer(binary, dtype=np.uint8) != np.frombuffer(patched, dtype=np.uint8))
    other_attributes_equal = all(stream_hash(document, binary, a) == stream_hash(document, patched, a)
        for mesh in document['meshes'] for p in mesh['primitives'] for name, a in p['attributes'].items() if name != 'TANGENT')
    w_equal = True
    for stream in delta['streams']:
        accessor = tangent_matches(document, binary, stream)
        refs = groups[accessor]
        stream['new_stream_sha256'] = stream_hash(document, patched, accessor)
        stream['after'] = audit_stream(document, patched, accessor, refs)
        w_equal &= bool(np.array_equal(rows(document, binary, accessor)[:, 3], rows(document, patched, accessor)[:, 3]))
    verification = {'json_unchanged': json.dumps(document, sort_keys=True) == json_before,
        'binary_length_unchanged': len(binary) == len(patched),
        'byte_diff_only_listed_tangent_xyz': all(int(offset) in allowed_bytes for offset in changed_bytes),
        'all_other_attributes_unchanged': other_attributes_equal, 'all_w_exact_unchanged': w_equal,
        'whole_head_streams_zero_and_nonfinite_free': all(s['after']['zero_xyz_all'] == s['after']['nonfinite_all'] == 0 for s in delta['streams']),
        'repaired_rows_abs_dot_le_2e_6': max(repaired_dot, default=0) <= REPAIRED_ORTHOGONALITY_LIMIT,
        'repaired_abs_dot_max': max(repaired_dot, default=0), 'changed_byte_count': len(changed_bytes),
        'changed_row_count': sum(len(s['changes']) for s in delta['streams']),
        'all_used_abs_dot_le_2e_6': all(s['after']['used_abs_dot_gt_2e_6'] == 0 for s in delta['streams']),
        'all_used_abs_dot_le_0_001': all(s['after']['used_abs_dot_gt_0_001'] == 0 for s in delta['streams'])}
    required = ['json_unchanged', 'binary_length_unchanged', 'byte_diff_only_listed_tangent_xyz', 'all_other_attributes_unchanged',
                'all_w_exact_unchanged', 'whole_head_streams_zero_and_nonfinite_free', 'repaired_rows_abs_dot_le_2e_6', 'all_used_abs_dot_le_0_001']
    if not all(verification[key] for key in required):
        raise ValueError('In-memory tangent delta verification failed')
    delta['verification'] = verification
    native_risks = []
    for mi, mesh in enumerate(document['meshes']):
        for pi, primitive in enumerate(mesh['primitives']):
            missing = 'TANGENT' not in primitive['attributes']
            degenerate = 0
            if 'TEXCOORD_0' in primitive['attributes'] and primitive.get('mode', 4) == 4:
                uv = rows(document, binary, primitive['attributes']['TEXCOORD_0'])
                faces = indices(document, binary, primitive)
                du, dv = uv[faces[:, 1]] - uv[faces[:, 0]], uv[faces[:, 2]] - uv[faces[:, 0]]
                determinant = du[:, 0] * dv[:, 1] - du[:, 1] * dv[:, 0]
                degenerate = int(np.sum((np.abs(determinant) <= 1e-12) | ~np.isfinite(determinant)))
            if missing or degenerate:
                material = document['materials'][primitive['material']]
                normal_texture = material.get('normalTexture')
                native_risks.append({'mesh': mi, 'primitive': pi, 'material': primitive['material'],
                    'material_name': material.get('name'), 'missing_tangent': missing,
                    'active_normal_texture': bool(normal_texture and normal_texture.get('scale', 1) > 0),
                    'uv_degenerate_or_nonfinite_indexed_triangles': degenerate})
    delta['untouched_native_tangent_generation_risks'] = native_risks
    if raw is not None:
        raw = Path(raw).resolve()
        raw_bytes = raw.read_bytes()
        rd, rb = glb.read_glb(raw)
        mappings = []
        for stream in delta['streams']:
            raw_accessor = tangent_matches(rd, rb, stream)
            formal_accessor = tangent_matches(document, binary, stream)
            formal_refs = [p for mesh in document['meshes'] for p in mesh['primitives'] if p['attributes'].get('TANGENT') == formal_accessor]
            raw_refs = [p for mesh in rd['meshes'] for p in mesh['primitives'] if p['attributes'].get('TANGENT') == raw_accessor]
            formal_fingerprints = sorted(json.dumps(primitive_fingerprint(document, binary, p), sort_keys=True) for p in formal_refs)
            raw_fingerprints = sorted(json.dumps(primitive_fingerprint(rd, rb, p), sort_keys=True) for p in raw_refs)
            if formal_fingerprints != raw_fingerprints:
                raise ValueError('Raw/formal head POSITION/NORMAL/UV/index mapping mismatch')
            mappings.append({'old_stream_sha256': stream['old_stream_sha256'], 'formal_accessor': formal_accessor,
                             'raw_accessor': raw_accessor, 'core_geometry_and_indices_equal': True})
        delta.update({'raw_geometry': str(raw), 'raw_geometry_sha256': glb.sha(raw_bytes),
                      'raw_head_stream_mapping': mappings, 'raw_formal_head_streams_equivalent': True})
        delta['verified_source_sha256'].append(glb.sha(raw_bytes))
        raw_patched = apply_delta(rd, rb, delta, glb.sha(raw_bytes))
        delta['raw_cross_apply_tangent_streams_match'] = all(stream_hash(rd, raw_patched, mapping['raw_accessor']) == stream['new_stream_sha256']
            for mapping, stream in zip(mappings, delta['streams']))
        if raw.read_bytes() != raw_bytes:
            raise ValueError('Raw source changed during audit')
    if source.read_bytes() != source_bytes:
        raise ValueError('Formal source changed during audit')
    delta['source_files_sha_unchanged'] = True
    return delta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for source in (args.source, args.raw):
        if source and (source.resolve() == args.output.resolve() or
                       (source.exists() and args.output.exists() and source.samefile(args.output))):
            parser.error('Output must differ from every frozen source, including aliases')
    delta = build_delta(args.source, args.raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(delta, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(args.output), 'changed_rows': delta['verification']['changed_row_count'],
                      'whole_head_streams_zero_and_nonfinite_free': delta['verification']['whole_head_streams_zero_and_nonfinite_free'],
                      'native_fixed': False}))


if __name__ == '__main__':
    main()
