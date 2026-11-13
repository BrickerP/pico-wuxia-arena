"""Independent, Blender-free verification of one pinned private specimen.

Run: python3 -B verify_specimen.py
Writes verify-report.json and exits nonzero if any contract fails. A revision
requires explicit --expect-component-sha and --expect-candidate-sha arguments.
Only the JSON report is written; all authoring and GLB inputs remain untouched.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import struct

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


HERE = Path(__file__).resolve().parent
PINS = {
    'before': 'b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09',
    'component': '88e07feacb84860726f7f208e1d8908f4f473bb6107e85e0fbbb7cacbc66eb39',
    'candidate': '446f3faa672d68c289caca3fa571caa92e3972cc56c0eb9f7bf82bfed4f91a4e',
}
DTYPES = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Glb:
    def __init__(self, path):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        self.sha256 = sha(self.raw)
        magic, version, length = struct.unpack_from('<4sII', self.raw)
        if (magic, version, length) != (b'glTF', 2, len(self.raw)):
            raise ValueError('Invalid GLB header: ' + str(path))
        chunks, offset = {}, 12
        while offset < len(self.raw):
            size, kind = struct.unpack_from('<II', self.raw, offset)
            offset += 8
            if kind in chunks or offset + size > len(self.raw):
                raise ValueError('Invalid or duplicate GLB chunk')
            chunks[kind] = self.raw[offset:offset + size]
            offset += size
        self.doc = json.loads(chunks[0x4e4f534a])
        self.binary = chunks[0x004e4942]
        if len(self.doc['buffers']) != 1 or self.doc['buffers'][0].get('uri'):
            raise ValueError('Expected one embedded GLB buffer')

    def accessor(self, index):
        item = self.doc['accessors'][index]
        if 'sparse' in item:
            raise ValueError('Sparse accessor requires a separate verifier')
        view = self.doc['bufferViews'][item['bufferView']]
        dtype = np.dtype(DTYPES[item['componentType']])
        width = WIDTHS[item['type']]
        values = np.ndarray((item['count'], width), dtype, self.binary,
                            view.get('byteOffset', 0) + item.get('byteOffset', 0),
                            (view.get('byteStride', dtype.itemsize * width), dtype.itemsize))
        if item.get('normalized') and item['componentType'] != 5126:
            info = np.iinfo(dtype)
            values = values.astype(np.float64) / info.max
            if info.min < 0:
                values = np.maximum(values, -1)
        return values

    def primitive(self, mesh, primitive):
        return self.doc['meshes'][mesh]['primitives'][primitive]

    def image(self, index):
        image = self.doc['images'][index]
        if 'uri' in image:
            raise ValueError('External image in private GLB')
        view = self.doc['bufferViews'][image['bufferView']]
        offset = view.get('byteOffset', 0)
        return self.binary[offset:offset + view['byteLength']]


def geometry(glb, primitive):
    if primitive.get('mode', 4) != 4:
        raise ValueError('Expected triangles')
    vertices = glb.accessor(primitive['attributes']['POSITION'])
    faces = glb.accessor(primitive['indices']).reshape(-1, 3)
    return vertices, faces


def welded_topology(vertices, faces):
    # One float32 ULP near raw Y=.95 is about 6e-8 m. Geometric seam copies
    # therefore share seven-decimal bins; no UV or normal seams are welded in GLB.
    _, first, inverse = np.unique(np.round(vertices, 7), axis=0,
                                  return_index=True, return_inverse=True)
    positions = vertices[first]
    faces = inverse[faces]
    directed = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges, edge_ids, counts = np.unique(np.sort(directed, axis=1), axis=0,
                                       return_inverse=True, return_counts=True)
    signs = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    winding = np.bincount(edge_ids, weights=signs)
    adjacency = [[] for _ in positions]
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    seen, components = set(), 0
    for start in np.unique(faces):
        if int(start) in seen:
            continue
        components += 1
        stack = [int(start)]
        seen.add(int(start))
        while stack:
            for target in adjacency[stack.pop()]:
                if int(target) not in seen:
                    seen.add(int(target))
                    stack.append(int(target))
    return positions, edges, counts, {
        'position_weld_decimals': 7, 'vertices': len(seen), 'edges': len(edges),
        'triangles': len(faces), 'connected_components': components,
        'edges_not_two_faces': int(np.count_nonzero(counts != 2)),
        'inconsistent_edge_winding': int(np.count_nonzero(winding)),
        'euler_characteristic': len(seen) - len(edges) + len(faces),
    }


def primitive_metrics(glb, primitive):
    vertices, faces = geometry(glb, primitive)
    used = np.unique(faces)
    attrs = {name: glb.accessor(index) for name, index in primitive['attributes'].items()}
    uv, normal, tangent = (attrs[name] for name in ('TEXCOORD_0', 'NORMAL', 'TANGENT'))
    area = np.linalg.norm(np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]],
                                   vertices[faces[:, 2]] - vertices[faces[:, 0]]), axis=1) / 2
    ua, ub = uv[faces[:, 1]] - uv[faces[:, 0]], uv[faces[:, 2]] - uv[faces[:, 0]]
    uv_area = np.abs(ua[:, 0] * ub[:, 1] - ua[:, 1] * ub[:, 0]) / 2
    nlen = np.linalg.norm(normal[used], axis=1)
    tlen = np.linalg.norm(tangent[used, :3], axis=1)
    dot = np.abs(np.sum(normal[used] * tangent[used, :3], axis=1))
    _, _, _, stats = welded_topology(vertices, faces)
    stats.update({
        'finite_attributes': all(bool(np.isfinite(rows[used]).all()) for rows in attrs.values()),
        'minimum_triangle_area_raw_m2': float(area.min()),
        'minimum_uv_triangle_area': float(uv_area.min()),
        'uv_within_unit_square': bool(((uv[used] >= 0) & (uv[used] <= 1)).all()),
        'normal_length_range': [float(nlen.min()), float(nlen.max())],
        'tangent_length_range': [float(tlen.min()), float(tlen.max())],
        'maximum_abs_normal_dot_tangent': float(dot.max()),
        'tangent_w_values': np.unique(tangent[used, 3]).tolist(),
    })
    stats['passed'] = bool(
        stats['finite_attributes'] and stats['connected_components'] == 1
        and stats['edges_not_two_faces'] == 0 and stats['inconsistent_edge_winding'] == 0
        and area.min() > 1e-15 and uv_area.min() > 1e-12 and stats['uv_within_unit_square']
        and np.max(np.abs(nlen - 1)) < 1e-3 and np.max(np.abs(tlen - 1)) < 1e-3
        and dot.max() < 1e-3 and np.all(np.abs(np.abs(tangent[used, 3]) - 1) < 1e-6))
    return stats


def contains(point, triangles):
    relative = triangles.astype(np.float64) - point
    a, b, c = relative[:, 0], relative[:, 1], relative[:, 2]
    la, lb, lc = (np.linalg.norm(v, axis=1) for v in (a, b, c))
    numerator = np.einsum('ij,ij->i', a, np.cross(b, c))
    denominator = (la * lb * lc + np.einsum('ij,ij->i', a, b) * lc
                   + np.einsum('ij,ij->i', b, c) * la + np.einsum('ij,ij->i', c, a) * lb)
    return bool(abs(np.sum(2 * np.arctan2(numerator, denominator)) / (4 * np.pi)) > .5)


def surface_distance(point, triangles):
    a, ab, ac = triangles[:, 0], triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
    normal = np.cross(ab, ac)
    projected = point - (np.sum((point - a) * normal, axis=1)
                         / np.sum(normal * normal, axis=1))[:, None] * normal
    offset = projected - a
    d00, d01, d11 = np.sum(ab * ab, axis=1), np.sum(ab * ac, axis=1), np.sum(ac * ac, axis=1)
    d20, d21 = np.sum(offset * ab, axis=1), np.sum(offset * ac, axis=1)
    denominator = d00 * d11 - d01 * d01
    u, v = (d11 * d20 - d01 * d21) / denominator, (d00 * d21 - d01 * d20) / denominator
    inside = (u >= 0) & (v >= 0) & (u + v <= 1)
    distance = np.full(len(triangles), np.inf)
    distance[inside] = np.linalg.norm(projected[inside] - point, axis=1)
    for i, j in ((0, 1), (1, 2), (2, 0)):
        start, delta = triangles[:, i], triangles[:, j] - triangles[:, i]
        fraction = np.clip(np.sum((point - start) * delta, axis=1) / np.sum(delta * delta, axis=1), 0, 1)
        distance = np.minimum(distance, np.linalg.norm(start + fraction[:, None] * delta - point, axis=1))
    return float(distance.min())


def root_containment(candidate, head, components):
    vertices, faces = geometry(candidate, head)
    positions, edges, counts, _ = welded_topology(vertices, faces)
    field = positions[:, 1] - .35 * positions[:, 0] - .966
    cut = edges[(counts == 1) & np.all(np.abs(field[edges]) < 2e-7, axis=1)]
    degree = Counter(int(index) for index in cut.ravel())
    # Check connectivity on the cut itself; the full old head has other boundaries.
    neighbors = {index: [] for index in degree}
    for a, b in cut:
        neighbors[int(a)].append(int(b))
        neighbors[int(b)].append(int(a))
    visited, stack = set(), [int(cut[0, 0])] if len(cut) else []
    while stack:
        index = stack.pop()
        if index not in visited:
            visited.add(index)
            stack.extend(neighbors[index])
    samples = np.vstack([positions[cut[:, 0]] * (1 - f) + positions[cut[:, 1]] * f
                         for f in (0, .25, .5, .75)]) if len(cut) else np.empty((0, 3))
    triangles = [geometry(candidate, p)[0][geometry(candidate, p)[1]].astype(np.float64) for p in components]
    membership = np.array([[contains(point, tri) for tri in triangles] for point in samples], dtype=bool)
    outside = samples[~membership.any(axis=1)] if len(samples) else samples
    distances = [min(surface_distance(point, tri) for tri in triangles) for point in outside]
    result = {
        'field': 'rawY - .35*rawX = .966', 'plane_tolerance_raw_m': 2e-7,
        'cut_edges': len(cut), 'cut_vertices': len(degree),
        'one_closed_loop': bool(len(degree) and len(visited) == len(degree) and set(degree.values()) == {2}),
        'fractions_per_edge': [0, .25, .5, .75], 'samples': len(samples),
        'inside_per_component': membership.sum(axis=0).tolist() if len(samples) else [],
        'outside_union': len(outside), 'outside_points_raw': outside.tolist(),
        'maximum_gap_to_new_surface_raw_m': max(distances, default=0),
        'worst_point_raw': outside[int(np.argmax(distances))].tolist() if distances else None,
    }
    result['passed'] = bool(result['one_closed_loop'] and len(cut) == 151 and len(samples) == 604 and not len(outside))
    return result


def triangle_keys(glb, primitive, selected=None):
    _, faces = geometry(glb, primitive)
    if selected is not None:
        faces = faces[selected]
    streams = [glb.accessor(index)[faces] for _, index in sorted(primitive['attributes'].items())]
    return Counter(sha(b''.join(stream[index].tobytes() for stream in streams)) for index in range(len(faces)))


def material_signature(glb, primitive):
    def resolve(value):
        if isinstance(value, list):
            return [resolve(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {}
        for key, item in value.items():
            if key.endswith('Texture') and isinstance(item, dict) and 'index' in item:
                texture = glb.doc['textures'][item['index']]
                image = glb.image(texture['source'])
                sampler = glb.doc['samplers'][texture['sampler']] if 'sampler' in texture else None
                result[key] = {k: resolve(v) for k, v in item.items() if k != 'index'}
                result[key]['resource'] = {'image_sha256': sha(image), 'sampler': sampler,
                    'texture_metadata': {k: v for k, v in texture.items() if k not in ('source', 'sampler')}}
            else:
                result[key] = resolve(item)
        return result
    return sha(json.dumps(resolve(glb.doc['materials'][primitive['material']]),
                          sort_keys=True, separators=(',', ':')).encode())


def map_metrics(component, hair, snapshot):
    material = component.doc['materials'][hair['material']]
    pbr = material['pbrMetallicRoughness']
    roles = {'hair-basecolor.png': pbr['baseColorTexture'],
             'hair-mr.png': pbr['metallicRoughnessTexture'], 'hair-normal.png': material['normalTexture']}
    vertices, faces = geometry(component, hair)
    uv = component.accessor(hair['attributes']['TEXCOORD_0'])
    mask = Image.new('L', (2048, 2048))
    draw = ImageDraw.Draw(mask)
    for triangle in uv[faces]:
        draw.polygon([tuple(point * 2047) for point in triangle], fill=255)
    interior = np.asarray(mask.filter(ImageFilter.MinFilter(5))) > 0
    results = {}
    for name, texture in roles.items():
        image_index = component.doc['textures'][texture['index']]['source']
        payload = component.image(image_index)
        image = Image.open(io.BytesIO(payload))
        pixels = np.asarray(image)
        if image.size != (2048, 2048) or pixels.ndim != 3 or pixels.shape[2] < 3:
            raise ValueError('Unexpected baked image dimensions/channels')
        rgb = pixels[interior, :3]
        result = {'sha256': sha(payload), 'embedded_matches_png': payload == snapshot[name],
                  'size': list(image.size), 'texcoord': texture.get('texCoord', 0),
                  'uv_coverage_fraction': float((np.asarray(mask) > 0).mean()),
                  'interior_texels': len(rgb), 'black_interior_texels': int(np.count_nonzero(rgb.max(axis=1) == 0)),
                  'rgb_min': rgb.min(axis=0).tolist(), 'rgb_max': rgb.max(axis=0).tolist()}
        passed = bool(result['embedded_matches_png'] and result['texcoord'] == 0
                      and result['uv_coverage_fraction'] >= .80 and len(rgb))
        if name == 'hair-normal.png':
            normal = rgb.astype(np.float64) / 127.5 - 1
            lengths = np.linalg.norm(normal, axis=1)
            result.update({'nonpositive_z_texels': int(np.count_nonzero(normal[:, 2] <= 0)),
                           'normal_length_range': [float(lengths.min()), float(lengths.max())]})
            passed = bool(passed and not result['black_interior_texels']
                          and not result['nonpositive_z_texels'] and np.max(np.abs(lengths - 1)) < .03)
        if name == 'hair-mr.png':
            result['metallic_nonzero_texels'] = int(np.count_nonzero(rgb[:, 2]))
            passed = bool(passed and not result['metallic_nonzero_texels'])
        result['passed'] = passed
        results[name] = result
    return results


def verify(args):
    before, component, candidate = (Glb(path) for path in (args.before, args.component, args.candidate))
    expected = dict(zip(('before', 'component', 'candidate'),
                        (args.expect_before_sha, args.expect_component_sha, args.expect_candidate_sha)))
    sources = dict(zip(('before', 'component', 'candidate'), (before, component, candidate)))
    report = {'created_utc': datetime.now(timezone.utc).isoformat(), 'verifier_sha256': sha(Path(__file__).read_bytes()),
              'inputs': {name: {'path': str(glb.path.resolve()), 'expected_sha256': expected[name],
                                'actual_sha256': glb.sha256} for name, glb in sources.items()},
              'checks': {}, 'limitations': [
                  'Offline asset contracts only; no aesthetic, native rendering, or animation pose pass.',
                  'Root containment samples four points per edge; it is not an exact continuous Boolean or self-intersection proof.',
                  'Normal-map coverage excludes a two-pixel boundary erosion; visual bake/cage quality still needs rendered comparison.',
                  'The old clipped head remains open; new component topology and sampled occlusion are assessed separately.',
              ]}
    checks = report['checks']
    checks['pinned_inputs'] = all(glb.sha256 == expected[name] for name, glb in sources.items())
    if not checks['pinned_inputs']:
        report['passed'] = False
        report['failure'] = 'Pinned input differs; refusing to verify a stale or unreviewed revision.'
        return report
    original = before.primitive(0, 1)
    clipped = candidate.primitive(0, 1)
    originals = before.doc['meshes'][0]['primitives']
    added = candidate.doc['meshes'][0]['primitives'][len(originals):]
    authored = [p for mesh in component.doc['meshes'] for p in mesh['primitives']]
    checks['exactly_two_authored_and_appended_primitives'] = len(authored) == len(added) == 2
    checks['component_identity_frame'] = not component.doc.get('skins') and not component.doc.get('animations') and all(
        node.get('translation', [0, 0, 0]) == [0, 0, 0] and node.get('rotation', [0, 0, 0, 1]) == [0, 0, 0, 1]
        and node.get('scale', [1, 1, 1]) == [1, 1, 1]
        and node.get('matrix', np.eye(4).ravel().tolist()) == np.eye(4).ravel().tolist()
        for node in component.doc['nodes'])
    preservation = {key: candidate.doc.get(key) == before.doc.get(key) for key in ('nodes', 'skins', 'animations')}
    preservation.update({
        'binary_prefix': candidate.binary[:len(before.binary)] == before.binary,
        'accessor_prefix': candidate.doc['accessors'][:len(before.doc['accessors'])] == before.doc['accessors'],
        'buffer_view_prefix': candidate.doc['bufferViews'][:len(before.doc['bufferViews'])] == before.doc['bufferViews'],
        'other_primitives': all(candidate.primitive(0, i) == p for i, p in enumerate(originals) if i != 1),
        'source_materials': candidate.doc['materials'][:len(before.doc['materials'])] == before.doc['materials'],
        'head_primitive_metadata': {k: v for k, v in clipped.items() if k not in ('attributes', 'indices')}
                                  == {k: v for k, v in original.items() if k not in ('attributes', 'indices')},
    })
    for key in ('images', 'textures', 'samplers'):
        preservation['source_' + key] = candidate.doc.get(key, [])[:len(before.doc.get(key, []))] == before.doc.get(key, [])
    positions, faces = geometry(before, original)
    kept = np.max(positions[faces, 1] - .35 * positions[faces, 0] - .966, axis=1) <= 1e-7
    missing = triangle_keys(before, original, kept) - triangle_keys(candidate, clipped)
    preservation['all_wholly_retained_triangles_and_attributes'] = not bool(missing)
    clipped_positions, clipped_faces = geometry(candidate, clipped)
    used_positions = clipped_positions[np.unique(clipped_faces)]
    preservation['no_used_old_head_vertices_above_cut'] = bool(np.all(
        used_positions[:, 1] - .35 * used_positions[:, 0] - .966 <= 1e-7))
    report['source_preservation'] = preservation
    checks['source_preservation'] = all(preservation.values())
    report['components'] = []
    for index, (source, output) in enumerate(zip(authored, added)):
        stats = primitive_metrics(component, source)
        stats['expected_euler_characteristic'] = [2, 0][index]
        stats['passed'] = bool(stats['passed'] and stats['euler_characteristic'] == [2, 0][index])
        stats['candidate_attributes_exact'] = all(np.array_equal(component.accessor(accessor),
            candidate.accessor(output['attributes'][name])) for name, accessor in source['attributes'].items())
        stats['candidate_indices_exact'] = np.array_equal(component.accessor(source['indices']), candidate.accessor(output['indices']))
        stats['material_signature_sha256'] = material_signature(component, source)
        stats['candidate_material_exact'] = stats['material_signature_sha256'] == material_signature(candidate, output)
        material = component.doc['materials'][source['material']]
        stats['opaque_material'] = material.get('alphaMode', 'OPAQUE') == 'OPAQUE'
        stats['double_sided_material'] = material.get('doubleSided', False)
        stats['passed'] = bool(stats['passed'] and stats['candidate_attributes_exact']
                               and stats['candidate_indices_exact'] and stats['candidate_material_exact'] and stats['opaque_material'])
        report['components'].append(stats)
    checks['component_geometry_uv_normal_tangent'] = len(report['components']) == 2 and all(p['passed'] for p in report['components'])
    mesh_nodes = [node for node in candidate.doc['nodes'] if node.get('mesh') == 0 and 'skin' in node]
    skin = candidate.doc['skins'][mesh_nodes[0]['skin']]
    head = [i for i, node in enumerate(skin['joints']) if candidate.doc['nodes'][node].get('name') == 'Head']
    bindings = []
    for primitive in added:
        joints = candidate.accessor(primitive['attributes']['JOINTS_0'])
        weights = candidate.accessor(primitive['attributes']['WEIGHTS_0'])
        bindings.append(bool(head == [26] and np.all(joints[:, 0] == head[0])
                             and np.all(weights == [1, 0, 0, 0])))
    checks['rigid_head_binding'] = len(mesh_nodes) == 1 and len(bindings) == 2 and all(bindings)
    report['head_binding'] = {'skin_joint_indices_named_head': head, 'component_binding_passes': bindings}
    report['root_containment'] = root_containment(candidate, clipped, added)
    checks['root_containment'] = report['root_containment']['passed']
    maps = {name: (args.component.parent / name).read_bytes() for name in ('hair-basecolor.png', 'hair-mr.png', 'hair-normal.png')}
    report['maps'] = map_metrics(component, authored[0], maps)
    checks['map_embedding_coverage_and_normal_values'] = all(item['passed'] for item in report['maps'].values())
    # Candidate image remapping must preserve actual payloads, not merely filenames.
    checks['candidate_image_payloads_exact'] = all(component.image(i) == candidate.image(len(before.doc['images']) + i)
                                                      for i in range(len(component.doc['images'])))
    checks['inputs_stable_during_verification'] = all(sha(glb.path.read_bytes()) == glb.sha256 for glb in sources.values())
    checks['maps_stable_during_verification'] = all((args.component.parent / name).read_bytes() == data for name, data in maps.items())
    report['passed'] = all(checks.values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, default=HERE.parent / 'skin-bake/native-v3-source.glb')
    parser.add_argument('--component', type=Path, default=HERE / 'topknot-low.glb')
    parser.add_argument('--candidate', type=Path, default=HERE / 'candidate-private.glb')
    parser.add_argument('--output', type=Path, default=HERE / 'verify-report.json')
    for name, value in PINS.items():
        parser.add_argument('--expect-' + name + '-sha', default=value)
    args = parser.parse_args()
    try:
        report = verify(args)
    except (ValueError, KeyError, IndexError, OSError, struct.error) as error:
        report = {'passed': False, 'failure': str(error), 'error_type': type(error).__name__}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'report': str(args.output.resolve()),
                      'failed_checks': [key for key, value in report.get('checks', {}).items() if not value],
                      'root_containment': report.get('root_containment')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
