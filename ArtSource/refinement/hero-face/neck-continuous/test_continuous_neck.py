"""Continuous source/head neck contracts, including posed LBS seam equality."""

import copy
from collections import Counter, defaultdict
from io import BytesIO
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

HERE = Path(__file__).resolve().parent
CUT_C = .8223


def cut_field(point):
    return point[1] + .6 * point[0]

sys.path.insert(0, str(HERE.parent))
import graft_head as glb
import build_continuous_neck as continuous


def decode(data):
    size = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + size]), data[28 + size:]


def ring_cylinder(heights, radii, segments=8):
    points, faces = [], []
    for y, radius in zip(heights, radii):
        points.extend((radius * math.cos(2 * math.pi * i / segments), y,
                       radius * math.sin(2 * math.pi * i / segments)) for i in range(segments))
    for ring in range(len(heights) - 1):
        for i in range(segments):
            a, b = ring * segments + i, (ring + 1) * segments + i
            c, d = (ring + 1) * segments + (i + 1) % segments, ring * segments + (i + 1) % segments
            faces.extend(((a, b, c), (a, c, d)))
    lower, upper = len(points), len(points) + 1
    points.extend(((0, heights[0], 0), (0, heights[-1], 0)))
    for i in range(segments):
        faces.append((lower, i, (i + 1) % segments))
    last = (len(heights) - 1) * segments
    for i in range(segments):
        faces.append((upper, last + (i + 1) % segments, last + i))
    return points, faces


def tetra(center, scale=.003):
    x, y, z = center
    points = [(x+scale, y+scale, z+scale), (x-scale, y-scale, z+scale),
              (x-scale, y+scale, z-scale), (x+scale, y-scale, z-scale)]
    return points, [(0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)]


def base_document(skinned):
    document = {'asset': {'version': '2.0'}, 'buffers': [{'byteLength': 0}],
        'bufferViews': [], 'accessors': [], 'images': [], 'textures': [], 'samplers': [],
        'materials': [], 'meshes': [{'primitives': []}], 'scene': 0,
        'nodes': [], 'scenes': [{'nodes': []}]}
    if skinned:
        document['nodes'] = [{'name': 'Hip', 'children': [2]}, {'name': 'Head', 'children': [3, 4]},
            {'name': 'Spine02', 'children': [1]}, {'name': 'L_Eye'}, {'name': 'R_Eye'},
            {'name': 'body', 'mesh': 0, 'skin': 0}]
        document['skins'] = [{'joints': [0, 1, 2, 3, 4]}]
        document['scenes'][0]['nodes'] = [0, 5]
    else:
        document['nodes'] = [{'name': 'static_head', 'mesh': 0}]
        document['scenes'][0]['nodes'] = [0]
    return document, bytearray()


def add_maps(document, binary, skinned):
    # Shared source atlas: gray cloth in left texel, skin in right texel.
    base = Image.new('RGB', (2, 2))
    base.putdata([(82, 84, 82), (184, 124, 94)] * 2 if skinned else [(174, 118, 92)] * 4)
    for image, name in ((base, 'Color'), (Image.new('RGB', (2, 2), (255, 176, 0)), 'MR'),
                        (Image.new('RGB', (2, 2), (128, 128, 255)), 'Normal')):
        stream = BytesIO()
        image.save(stream, format='PNG')
        payload = stream.getvalue()
        view = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(payload)})
        binary.extend(payload)
        document['images'].append({'bufferView': view, 'mimeType': 'image/png', 'name': name})
        document['textures'].append({'source': len(document['images']) - 1})
    document['materials'].append({'name': 'tripo_body' if skinned else 'tripo_head_skin',
        'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'metallicRoughnessTexture': {'index': 1},
                                'roughnessFactor': 1, 'metallicFactor': 1},
        'normalTexture': {'index': 2}})


def append_primitive(document, binary, points, faces, weights=None, head_faces=(), tag=None):
    # Expand every triangle to create true coincident UV seams. Geometry and
    # weights must remain coincident even though their source IDs differ.
    expanded, normals, uvs, joints, values = [], [], [], [], []
    source_points, source_face_ids = [], []
    for face_index, face in enumerate(faces):
        for vertex in face:
            point = points[vertex]
            expanded.append(point)
            radius = math.hypot(point[0], point[2])
            normals.append((point[0]/radius, 0, point[2]/radius) if radius else (0, 1, 0))
            uvs.append((.65 + point[0] * 2, .5 + point[2] * 2) if weights is None
                       else (.75 if face_index in head_faces else .25, .5))
            source_points.append(vertex)
            source_face_ids.append(face_index)
            if weights is not None:
                distribution = weights[vertex]
                active = list(distribution.items())
                joints.append(tuple([item[0] for item in active] + [0] * (4-len(active))))
                values.append(tuple([item[1] for item in active] + [0.] * (4-len(active))))
    attributes = {}
    streams = [('POSITION', expanded, 5126, 'f', 3), ('NORMAL', normals, 5126, 'f', 3),
               ('TEXCOORD_0', uvs, 5126, 'f', 2)]
    if weights is not None:
        streams.extend([('JOINTS_0', joints, 5123, 'H', 4), ('WEIGHTS_0', values, 5126, 'f', 4)])
    for semantic, rows, component_type, code, width in streams:
        attributes[semantic] = glb.append_accessor(document, binary,
            b''.join(struct.pack('<' + code * width, *row) for row in rows), component_type,
            f'VEC{width}', len(rows), 34962)
    indices = glb.append_accessor(document, binary,
        struct.pack('<' + 'H' * len(expanded), *range(len(expanded))), 5123, 'SCALAR', len(expanded), 34963)
    primitive = {'attributes': attributes, 'indices': indices, 'material': 0}
    if tag:
        primitive['extras'] = {'rig_joint': tag}
    document['meshes'][0]['primitives'].append(primitive)
    return expanded, source_points, source_face_ids


def fixture():
    body, binary = base_document(True)
    points, faces = ring_cylinder((.760, .800, .850), (.025, .020, .018))
    head_faces = list(range(16, 32)) + list(range(40, 48))
    kept_faces = list(range(16)) + list(range(32, 40))
    extra_points, extra_faces = tetra((.10, .72, .10))
    offset = len(points)
    points += extra_points
    faces += [tuple(offset + index for index in face) for face in extra_faces]
    # The detached tetra must survive even though it is outside body-side flood.
    weights = [{0: 1.} if point[1] < .799 else ({0: .45, 1: .30, 2: .25} if point[1] < .801 else {1: 1.})
               for point in points]
    expanded, source_point_ids, _ = append_primitive(body, binary, points, faces, weights, head_faces)
    add_maps(body, binary, True)
    identity = tuple(float(i % 5 == 0) for i in range(16))
    inverse_bind = glb.append_accessor(body, binary, struct.pack('<16f', *identity) * 5,
                                        5126, 'MAT4', 5, 34962)
    body['skins'][0]['inverseBindMatrices'] = inverse_bind
    body_bytes = glb.encode_glb(body, binary)
    body, body_binary = decode(body_bytes)
    # Follow the exact source halfedges, but order the loop opposite the retained
    # body face winding, as the actual 52-node authoring audit does.
    point_ring = [8] + list(range(15, 8, -1))
    ring = []
    for index, vertex in enumerate(point_ring):
        following = point_ring[(index + 1) % len(point_ring)]
        representative = source_point_ids.index(vertex)
        halfedge = None
        body_face = None
        for face_id in kept_faces:
            for j in range(3):
                if faces[face_id][j] == following and faces[face_id][(j+1)%3] == vertex:
                    halfedge = [face_id * 3 + j, face_id * 3 + (j+1)%3]
                    body_face = face_id
                    break
            if halfedge:
                break
        if halfedge is None:
            raise AssertionError('Synthetic ring source edge missing')
        ring.append({'representative_source_vertex_id': representative,
            'position_raw_gltf': list(struct.unpack('<3f', struct.pack('<3f', *points[vertex]))),
            'weights': {name: struct.unpack('<f', struct.pack('<f', value))[0]
                        for name, value in (('Hip', .45), ('Head', .30), ('Spine02', .25))},
            'source_body_halfedge_ids': halfedge, 'source_body_face': body_face,
            'loop_direction_matches_body_halfedge': False})
    audit = {'source_sha256': glb.sha(body_bytes),
        'protected_03_lapel_path_faces': [{'source_face': 0}, {'source_face': 1}],
        'source_edge_loop52_proposal': {'directed_vertices': ring,
            'head_side_original_face_ids': head_faces, 'body_side_original_face_ids': kept_faces,
            'all13_protected03faces_in_body_side': True}}
    head, hbinary = base_document(False)
    hp, hf = ring_cylinder((.790, .840, .900), (.019, .020, .024), segments=12)
    append_primitive(head, hbinary, hp, hf)
    for name, sign in (('L_Eye', -1), ('R_Eye', 1)):
        ep, ef = tetra((.026, .860, sign*.018), .001)
        append_primitive(head, hbinary, ep, ef, tag=name)
    add_maps(head, hbinary, False)
    head_bytes = glb.encode_glb(head, hbinary)
    head, head_binary = decode(head_bytes)
    return body, body_binary, head, head_binary, audit, body_bytes, head_bytes


def surface(document, binary):
    primitives = document['meshes'][0]['primitives']
    vertices, triangles, weights = [], [], []
    joint_names = [document['nodes'][index]['name'] for index in document['skins'][0]['joints']]
    for primitive in primitives:
        attrs = primitive['attributes']
        points = glb.accessor_rows(document, binary, attrs['POSITION'])
        indices = [row[0] for row in glb.accessor_rows(document, binary, primitive['indices'])]
        joints = glb.accessor_rows(document, binary, attrs['JOINTS_0'])
        values = glb.accessor_rows(document, binary, attrs['WEIGHTS_0'])
        offset = len(vertices)
        vertices.extend(points)
        for js, ws in zip(joints, values):
            distribution = defaultdict(float)
            for joint, weight in zip(js, ws):
                distribution[joint_names[joint]] += weight
            weights.append({joint: value for joint, value in distribution.items() if value})
        triangles.extend(tuple(offset + index for index in indices[i:i+3]) for i in range(0, len(indices), 3))
    return vertices, triangles, weights


def weld_edges(points, faces):
    groups = {}
    unique = []
    for point in points:
        if point not in groups:
            groups[point] = len(groups)
        unique.append(groups[point])
    edges = Counter()
    for face in faces:
        welded = [unique[index] for index in face]
        for a, b in zip(welded, welded[1:] + welded[:1]):
            edges[tuple(sorted((a, b)))] += 1
    return edges



def directed_edges(points, faces):
    edges = Counter()
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            edges[(points[a], points[b])] += 1
    return edges


def discontinuous_head_atlas(document, binary):
    """Same skin color on disjoint charts; gray pixels lie BETWEEN charts."""
    result = copy.deepcopy(document)
    changed = bytearray(binary)
    for primitive in result['meshes'][0]['primitives']:
        accessor = result['accessors'][primitive['attributes']['TEXCOORD_0']]
        view = result['bufferViews'][accessor['bufferView']]
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        stride = view.get('byteStride', 8)
        for index in range(accessor['count']):
            # Per-face UV duplication is deliberate: geometric neighbors can
            # belong to opposite atlas charts, with no valid UV interpolation.
            u = .05 if (index // 3) % 2 == 0 else .95
            struct.pack_into('<2f', changed, start + index * stride, u, .5)
    for image_index in (0, 1):
        image = Image.new('RGB', (256, 4))
        values = []
        for y in range(4):
            for x in range(256):
                skin = x < 38 or x >= 218
                values.append(((174, 118, 92) if skin else (20, 20, 20)) if image_index == 0
                              else ((255, 176, 0) if skin else (255, 20, 0)))
        image.putdata(values)
        stream = BytesIO()
        image.save(stream, format='PNG')
        payload = stream.getvalue()
        view_index = len(result['bufferViews'])
        result['bufferViews'].append({'buffer': 0, 'byteOffset': len(changed), 'byteLength': len(payload)})
        changed.extend(payload)
        result['images'][image_index]['bufferView'] = view_index
    encoded = glb.encode_glb(result, changed)
    result, changed = decode(encoded)
    return result, changed, encoded


def lbs(position, weights, transforms):
    point = (*position, 1)
    return tuple(sum(weight * sum(transforms[joint][axis][i] * point[i] for i in range(4))
                     for joint, weight in weights.items()) for axis in range(3))


class ContinuousNeckTests(unittest.TestCase):
    def setUp(self):
        (self.body, self.body_binary, self.head, self.head_binary, self.audit,
         self.body_bytes, self.head_bytes) = fixture()

    def build(self, audit=None, body_sha=None):
        return continuous.build(self.body, self.body_binary, self.head, self.head_binary,
            audit if audit is not None else self.audit,
            body_sha if body_sha is not None else glb.sha(self.body_bytes), glb.sha(self.head_bytes))

    def test_source_streams_protected_collar_and_detached_component_preserved(self):
        original_body, original_head, original_audit = copy.deepcopy(self.body), copy.deepcopy(self.head), copy.deepcopy(self.audit)
        output, report = self.build()
        document, binary = decode(output)
        self.assertEqual(binary[:len(self.body_binary)], self.body_binary)
        self.assertEqual(document['nodes'], self.body['nodes'])
        self.assertEqual(document['skins'], self.body['skins'])
        for index in range(len(self.body['accessors'])):
            self.assertEqual(glb.stream_bytes(document, binary, index), glb.stream_bytes(self.body, self.body_binary, index))
        original_faces = glb.triangles(self.body, self.body_binary, self.body['meshes'][0]['primitives'][0])[1]
        retained_faces = glb.triangles(document, binary, document['meshes'][0]['primitives'][0])[1]
        expected = [face for i, face in enumerate(original_faces)
                    if i not in set(self.audit['source_edge_loop52_proposal']['head_side_original_face_ids'])]
        self.assertEqual(retained_faces, expected)
        self.assertEqual(len(retained_faces), 28)
        self.assertIn(original_faces[0], retained_faces)
        self.assertIn(original_faces[1], retained_faces)
        for face in original_faces[-4:]:
            self.assertIn(face, retained_faces)
        self.assertEqual(self.body, original_body)
        self.assertEqual(self.head, original_head)
        self.assertEqual(self.audit, original_audit)
        self.assertEqual(report['loft']['rings'][1:-1], [128, 128, 128])
        self.assertEqual(report['loft']['zero_area_faces'], 0)

    def test_closed_geometric_interfaces_exact_weights_and_random_lbs(self):
        output, report = self.build()
        document, binary = decode(output)
        points, faces, distributions = surface(document, binary)
        edges = weld_edges(points, faces)
        self.assertEqual(Counter(edges.values()), {2: len(edges)})
        directions = directed_edges(points, faces)
        for first, second in directions:
            self.assertEqual(directions[first, second], 1)
            self.assertEqual(directions[second, first], 1, 'Coincident interface faces have equal winding')
        positions_to_weights = defaultdict(list)
        for index in {vertex for face in faces for vertex in face}:
            positions_to_weights[points[index]].append(distributions[index])
        for point, weights in positions_to_weights.items():
            for other in weights[1:]:
                self.assertEqual(other, weights[0], msg=f'Coincident skin weights differ at {point}')
        rng = random.Random(812)
        for _ in range(12):
            transforms = {name: [[rng.uniform(-1.5, 1.5) for _ in range(4)] for _ in range(3)]
                          for name in ('Hip', 'Head', 'Spine02', 'L_Eye', 'R_Eye')}
            for point, weights in positions_to_weights.items():
                if len(weights) > 1:
                    expected = lbs(point, weights[0], transforms)
                    for other in weights[1:]:
                        self.assertEqual(lbs(point, other, transforms), expected)
        # Endpoint identity is stronger than rest-space distance: the lower
        # bridge shares exact source FLOAT32 rows at all UV-split ring positions.
        source_points = glb.accessor_rows(self.body, self.body_binary,
            self.body['meshes'][0]['primitives'][0]['attributes']['POSITION'])
        for row in self.audit['source_edge_loop52_proposal']['directed_vertices']:
            point = source_points[row['representative_source_vertex_id']]
            self.assertIn(point, positions_to_weights)
            self.assertGreaterEqual(len(positions_to_weights[point]), 2)
        bridge = document['meshes'][0]['primitives'][report['loft']['primitive']]
        bridge_joints = glb.accessor_rows(document, binary, bridge['attributes']['JOINTS_0'])
        bridge_weights = glb.accessor_rows(document, binary, bridge['attributes']['WEIGHTS_0'])
        source_attrs = self.body['meshes'][0]['primitives'][0]['attributes']
        source_joints = glb.accessor_rows(self.body, self.body_binary, source_attrs['JOINTS_0'])
        source_weights = glb.accessor_rows(self.body, self.body_binary, source_attrs['WEIGHTS_0'])
        base_ids = report['loft']['base_source_vertex_ids']
        for index, source_id in enumerate(base_ids + base_ids[:1]):
            self.assertEqual(bridge_joints[index], source_joints[source_id])
            self.assertEqual(bridge_weights[index], source_weights[source_id])
        bridge_points = glb.accessor_rows(document, binary, bridge['attributes']['POSITION'])
        bridge_uv = glb.accessor_rows(document, binary, bridge['attributes']['TEXCOORD_0'])
        for point, uv in zip(bridge_points, bridge_uv):
            if uv[1] < 1:
                self.assertLess(cut_field(point), CUT_C, 'Loft crossed the new oblique head plane')
            else:
                self.assertAlmostEqual(cut_field(point), CUT_C, places=6)
        for row in self.audit['source_edge_loop52_proposal']['directed_vertices']:
            self.assertLess(cut_field(row['position_raw_gltf']), CUT_C)

    def test_bridge_material_baked_strip_and_independent_eyes(self):
        output, _ = self.build()
        document, binary = decode(output)
        bridge = [primitive for primitive in document['meshes'][0]['primitives']
                  if document['materials'][primitive['material']]['name'] == 'tripo_neck_continuous']
        self.assertEqual(len(bridge), 1)
        attrs = bridge[0]['attributes']
        uvs = glb.accessor_rows(document, binary, attrs['TEXCOORD_0'])
        self.assertEqual(min(row[0] for row in uvs), 0)
        self.assertEqual(max(row[0] for row in uvs), 1)
        self.assertEqual(min(row[1] for row in uvs), 0)
        self.assertEqual(max(row[1] for row in uvs), 1)
        pbr = document['materials'][bridge[0]['material']]['pbrMetallicRoughness']
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            texture = document['textures'][pbr[key]['index']]
            image = document['images'][texture['source']]
            view = document['bufferViews'][image['bufferView']]
            start = view.get('byteOffset', 0)
            with Image.open(BytesIO(binary[start:start+view['byteLength']])) as rendered:
                self.assertEqual(rendered.size, (1024, 256))
                if key == 'baseColorTexture':
                    for v in (0, rendered.height - 1):
                        red, green, blue = rendered.convert('RGB').getpixel((rendered.width // 2, v))
                        self.assertGreater(red, green * 1.12, 'Bridge sampled gray cloth instead of skin')
                        self.assertGreater(green, blue * 1.05)
        for name in ('L_Eye', 'R_Eye'):
            matched = [primitive for primitive in document['meshes'][0]['primitives']
                       if primitive.get('extras', {}).get('rig_joint') == name]
            self.assertEqual(len(matched), 1)
            original = next(primitive for primitive in self.head['meshes'][0]['primitives']
                            if primitive.get('extras', {}).get('rig_joint') == name)
            self.assertEqual(glb.accessor_rows(document, binary, matched[0]['attributes']['POSITION']),
                             glb.accessor_rows(self.head, self.head_binary, original['attributes']['POSITION']))

    def test_clipping_leaves_jaw_and_eye_geometry_and_exact_cut_loop(self):
        document, binary, report = continuous.clip_head(self.head, self.head_binary, cut_c=CUT_C)
        primary = document['meshes'][0]['primitives'][0]
        points, faces = glb.triangles(document, binary, primary)
        used = {index for face in faces for index in face}
        self.assertGreater(len(faces), 0)
        self.assertEqual(report['cut_c'], CUT_C)
        self.assertTrue(report['cut_field'])
        self.assertNotIn('cut_y', report)
        self.assertTrue(all(cut_field(points[index]) >= CUT_C - 6e-8 for index in used))
        cut = {points[index] for index in used if abs(cut_field(points[index])-CUT_C) < 1e-7}
        self.assertGreaterEqual(len(cut), 8)
        source_attrs = self.head['meshes'][0]['primitives'][0]['attributes']
        source_positions = glb.accessor_rows(self.head, self.head_binary, source_attrs['POSITION'])
        source_uv = glb.accessor_rows(self.head, self.head_binary, source_attrs['TEXCOORD_0'])
        result_uv = glb.accessor_rows(document, binary, primary['attributes']['TEXCOORD_0'])
        self.assertGreater(len(report['edge_interpolations']), 0)
        for mapping in report['edge_interpolations']:
            first, second = mapping['source_edge_vertex_ids']
            a, b = mapping['source_edge_barycentric']
            self.assertAlmostEqual(a + b, 1)
            expected = tuple(a*x + b*y for x, y in zip(source_positions[first], source_positions[second]))
            for actual, target in zip(points[mapping['output_vertex']], expected):
                self.assertAlmostEqual(actual, target, places=6)
            expected_uv = tuple(a*x + b*y for x, y in zip(source_uv[first], source_uv[second]))
            for actual, target in zip(result_uv[mapping['output_vertex']], expected_uv):
                self.assertAlmostEqual(actual, target, places=6)
        for old, new in zip(self.head['meshes'][0]['primitives'][1:], document['meshes'][0]['primitives'][1:]):
            self.assertEqual(old, new)
        source_primary = self.head['meshes'][0]['primitives'][0]
        source_points = glb.accessor_rows(self.head, self.head_binary, source_primary['attributes']['POSITION'])
        for point in source_points:
            if point[1] > .84:
                self.assertIn(point, {points[index] for index in used})

    def test_reversed_loft_interface_face_is_rejected(self):
        output, report = self.build()
        document, binary = decode(output)
        loft_index = report['loft']['primitive']
        continuous.verify_interfaces(document, binary, 0, 1, loft_index)
        primitive = document['meshes'][0]['primitives'][loft_index]
        accessor = document['accessors'][primitive['indices']]
        view = document['bufferViews'][accessor['bufferView']]
        code, size = glb.COMPONENTS[accessor['componentType']]
        stride = view.get('byteStride', size)
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        changed = bytearray(binary)
        second = struct.unpack_from('<' + code, changed, start + stride)[0]
        third = struct.unpack_from('<' + code, changed, start + 2 * stride)[0]
        struct.pack_into('<' + code, changed, start + stride, third)
        struct.pack_into('<' + code, changed, start + 2 * stride, second)
        with self.assertRaises(ValueError):
            continuous.verify_interfaces(document, changed, 0, 1, loft_index)

    def test_atlas_interpolates_sampled_colors_across_discontinuous_uv_charts(self):
        self.head, self.head_binary, self.head_bytes = discontinuous_head_atlas(self.head, self.head_binary)
        output, report = self.build()
        document, binary = decode(output)
        primitive = document['meshes'][0]['primitives'][report['loft']['primitive']]
        material = document['materials'][primitive['material']]['pbrMetallicRoughness']
        for slot in ('baseColorTexture', 'metallicRoughnessTexture'):
            texture = document['textures'][material[slot]['index']]
            image = document['images'][texture['source']]
            view = document['bufferViews'][image['bufferView']]
            start = view.get('byteOffset', 0)
            with Image.open(BytesIO(binary[start:start + view['byteLength']])) as original:
                baked = original.convert('RGB')
                for v in (0, baked.height // 2, baked.height - 1):
                    pixels = [baked.getpixel((x, v)) for x in range(baked.width)]
                    jumps = [max(abs(a-b) for a, b in zip(pixels[x], pixels[(x+1) % len(pixels)]))
                             for x in range(len(pixels))]
                    self.assertLessEqual(max(jumps), 8, 'Atlas jumped across a UV chart boundary')
                    if slot == 'baseColorTexture':
                        for red, green, blue in pixels:
                            self.assertGreater(red, green * 1.12, 'UV interpolation sampled non-skin chart gap')
                            self.assertGreater(green, blue * 1.05)
                    else:
                        self.assertTrue(all(abs(pixel[1]-176) <= 1 for pixel in pixels))

    def test_nonadjacent_crossed_3d_triangles_are_rejected(self):
        # One triangle lies in Y=.75; the other pierces it through Z=0.
        # No vertex or edge IDs are shared, and every point stays below the
        # oblique cut so the self-intersection guard is the only rejection.
        points = [(-.01, .75, -.01), (.01, .75, -.01), (0, .75, .01),
                  (-.005, .74, 0), (.005, .74, 0), (0, .76, 0)]
        self.assertTrue(all(cut_field(point) < CUT_C for point in points))
        with self.assertRaisesRegex(ValueError, 'self-intersects'):
            continuous.geometry_safety(points, [(0, 1, 2), (3, 4, 5)], [(0, .5)] * 6)

    def test_nonadjacent_coplanar_overlap_is_rejected(self):
        # The second coplanar triangle is strictly inside the first; segment
        # piercing alone cannot detect this overlap.
        points = [(-.01, .75, -.01), (.01, .75, -.01), (0, .75, .01),
                  (-.005, .75, -.002), (.005, .75, -.002), (0, .75, .008)]
        self.assertTrue(all(cut_field(point) < CUT_C for point in points))
        with self.assertRaisesRegex(ValueError, 'self-intersects'):
            continuous.geometry_safety(points, [(0, 1, 2), (3, 4, 5)], [(0, .5)] * 6)

    def test_invalid_source_or_mask_rejected(self):
        with self.assertRaises(ValueError):
            self.build(body_sha='wrong-source')
        for mutate in ('overlap', 'out_of_range', 'ring_position', 'protected_removed'):
            audit = copy.deepcopy(self.audit)
            proposal = audit['source_edge_loop52_proposal']
            if mutate == 'overlap':
                proposal['head_side_original_face_ids'].append(proposal['body_side_original_face_ids'][0])
            elif mutate == 'out_of_range':
                proposal['head_side_original_face_ids'].append(99999)
            elif mutate == 'ring_position':
                proposal['directed_vertices'][0]['position_raw_gltf'][0] += .01
            else:
                audit['protected_03_lapel_path_faces'] = [{'source_face': proposal['head_side_original_face_ids'][0]}]
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.build(audit=audit)

    def test_cli_preserves_input_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            body, head, audit, output, report = [folder / name for name in
                ('body.glb', 'head.glb', 'audit.json', 'out.glb', 'out.json')]
            body.write_bytes(self.body_bytes)
            head.write_bytes(self.head_bytes)
            audit.write_text(json.dumps(self.audit))
            original_audit = audit.read_bytes()
            subprocess.run([sys.executable, str(Path(continuous.__file__)), '--body', str(body), '--head', str(head),
                            '--audit', str(audit), '--output', str(output), '--report', str(report)],
                           check=True, capture_output=True)
            self.assertEqual(body.read_bytes(), self.body_bytes)
            self.assertEqual(head.read_bytes(), self.head_bytes)
            self.assertEqual(audit.read_bytes(), original_audit)
            document, binary = glb.read_glb(output)
            points, faces, _ = surface(document, binary)
            self.assertTrue(all(count == 2 for count in weld_edges(points, faces).values()))
            self.assertTrue(json.loads(report.read_text()))


if __name__ == '__main__':
    unittest.main()
