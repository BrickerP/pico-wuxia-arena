"""Candidate-only head graft; preserve the complete raw rig binary as a prefix.

The replacement GLB must already use the body's mesh-local frame (+Y up) and
identity node transforms. No source file or production pipeline is modified.
"""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct


COMPONENTS = {5120: ('b', 1), 5121: ('B', 1), 5122: ('h', 2),
              5123: ('H', 2), 5125: ('I', 4), 5126: ('f', 4)}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
HEAD_EXTENSIONS = {'KHR_texture_transform', 'KHR_materials_unlit',
                   'KHR_materials_clearcoat', 'KHR_materials_transmission',
                   'KHR_materials_volume', 'KHR_materials_ior',
                   'KHR_materials_specular', 'KHR_materials_sheen',
                   'KHR_materials_iridescence', 'KHR_materials_anisotropy',
                   'KHR_materials_emissive_strength', 'KHR_materials_dispersion',
                   'KHR_materials_pbrSpecularGlossiness'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 28 or struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError('Expected a complete GLB v2: ' + str(path))
    size, kind = struct.unpack_from('<II', data, 12)
    end = 20 + size
    if kind != 0x4E4F534A or end + 8 > len(data):
        raise ValueError('Invalid GLB JSON chunk')
    document = json.loads(data[20:end])
    binary_size, binary_kind = struct.unpack_from('<II', data, end)
    if binary_kind != 0x004E4942 or end + 8 + binary_size != len(data):
        raise ValueError('Expected exactly one embedded BIN chunk')
    binary = data[end + 8:]
    validate_document(document, binary)
    return document, binary


def encode_glb(document, binary):
    document = copy.deepcopy(document)
    document['buffers'][0]['byteLength'] = len(binary)
    payload = json.dumps(document, separators=(',', ':'), allow_nan=False).encode()
    payload += b' ' * (-len(payload) % 4)
    binary += b'\0' * (-len(binary) % 4)
    return (struct.pack('<4sII', b'glTF', 2, 28 + len(payload) + len(binary))
            + struct.pack('<II', len(payload), 0x4E4F534A) + payload
            + struct.pack('<II', len(binary), 0x004E4942) + binary)


def validate_document(document, binary):
    buffers = document.get('buffers', [])
    if len(buffers) != 1 or 'uri' in buffers[0] or buffers[0]['byteLength'] > len(binary):
        raise ValueError('External or multiple buffers are unsupported')
    def walk(value):
        if isinstance(value, dict):
            extensions = value.get('extensions', {})
            if any(name in extensions for name in ('KHR_draco_mesh_compression', 'EXT_meshopt_compression')):
                raise ValueError('Compressed Draco/meshopt data is unsupported')
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(document)
    if {'KHR_draco_mesh_compression', 'EXT_meshopt_compression'} & (set(document.get('extensionsUsed', [])) | set(document.get('extensionsRequired', []))):
        raise ValueError('Compressed Draco/meshopt extensions are unsupported')
    for accessor in document.get('accessors', []):
        if 'sparse' in accessor or 'bufferView' not in accessor:
            raise ValueError('Sparse or bufferless accessors are unsupported')
    for view in document.get('bufferViews', []):
        start, length = view.get('byteOffset', 0), view['byteLength']
        if view.get('buffer', 0) != 0 or start < 0 or length < 0 or start + length > buffers[0]['byteLength']:
            raise ValueError('Invalid bufferView bounds or buffer reference')
    for image in document.get('images', []):
        if 'uri' in image or 'bufferView' not in image:
            raise ValueError('External images are unsupported; embed head textures in GLB')


def accessor_rows(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    code, component_bytes = COMPONENTS[accessor['componentType']]
    count = WIDTHS[accessor['type']]
    width = count * component_bytes
    stride = view.get('byteStride', width)
    offset = accessor.get('byteOffset', 0)
    rows = accessor['count']
    if rows < 1 or stride < width or offset < 0 or offset + (rows - 1) * stride + width > view['byteLength']:
        raise ValueError('Invalid accessor bounds/stride/count')
    start = view.get('byteOffset', 0) + offset
    return [struct.unpack_from('<' + code * count, binary, start + i * stride) for i in range(rows)]


def stream_bytes(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    width = COMPONENTS[accessor['componentType']][1] * WIDTHS[accessor['type']]
    stride = view.get('byteStride', width)
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    accessor_rows(document, binary, index)
    return b''.join(binary[start + i * stride:start + i * stride + width] for i in range(accessor['count']))


def append_accessor(document, binary, payload, component_type, value_type, count, target):
    binary.extend(b'\0' * (-len(binary) % 4))
    view_index = len(document.setdefault('bufferViews', []))
    document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary),
                                   'byteLength': len(payload), 'target': target})
    binary.extend(payload)
    index = len(document.setdefault('accessors', []))
    document['accessors'].append({'bufferView': view_index, 'componentType': component_type,
                                  'count': count, 'type': value_type})
    return index


def triangles(document, binary, primitive):
    if primitive.get('mode', 4) != 4 or primitive.get('targets'):
        raise ValueError('Only triangle primitives without morph targets are supported')
    position_index = primitive['attributes']['POSITION']
    position_accessor = document['accessors'][position_index]
    if position_accessor['componentType'] != 5126 or position_accessor['type'] != 'VEC3':
        raise ValueError('POSITION must be FLOAT VEC3')
    points = accessor_rows(document, binary, position_index)
    if not all(math.isfinite(value) for point in points for value in point):
        raise ValueError('Non-finite vertex positions')
    if 'indices' in primitive:
        accessor = document['accessors'][primitive['indices']]
        if accessor['componentType'] not in (5121, 5123, 5125) or accessor['type'] != 'SCALAR':
            raise ValueError('Indices must be unsigned SCALAR')
        indices = [row[0] for row in accessor_rows(document, binary, primitive['indices'])]
    else:
        indices = list(range(len(points)))
    if len(indices) % 3 or any(index >= len(points) for index in indices):
        raise ValueError('Invalid triangle indices')
    return points, [indices[i:i + 3] for i in range(0, len(indices), 3)]



def head_influences(document, binary, primitive, head_joint, joint_count, vertex_count):
    """Decode the source skin without treating high collar geometry as head."""
    attributes = primitive['attributes']
    if 'JOINTS_0' not in attributes or 'WEIGHTS_0' not in attributes:
        raise ValueError('Body primitive requires JOINTS_0 and WEIGHTS_0')
    if any(name.startswith(('JOINTS_', 'WEIGHTS_')) and name not in ('JOINTS_0', 'WEIGHTS_0')
           for name in attributes):
        raise ValueError('Additional body skin influence sets are unsupported')
    joints = document['accessors'][attributes['JOINTS_0']]
    weights = document['accessors'][attributes['WEIGHTS_0']]
    if (joints['type'] != 'VEC4' or joints['componentType'] not in (5121, 5123)
            or joints.get('normalized', False)):
        raise ValueError('JOINTS_0 must be non-normalized unsigned BYTE/SHORT VEC4')
    if (weights['type'] != 'VEC4' or weights['componentType'] not in (5121, 5123, 5126)
            or weights.get('normalized', False) != (weights['componentType'] != 5126)):
        raise ValueError('WEIGHTS_0 must be FLOAT or normalized unsigned BYTE/SHORT VEC4')
    if joints['count'] != vertex_count or weights['count'] != vertex_count:
        raise ValueError('Body skin attribute counts differ from POSITION')
    joint_rows = accessor_rows(document, binary, attributes['JOINTS_0'])
    weight_rows = accessor_rows(document, binary, attributes['WEIGHTS_0'])
    divisor = {5121: 255, 5123: 65535, 5126: 1}[weights['componentType']]
    influences = []
    for indices, values in zip(joint_rows, weight_rows):
        values = [value / divisor for value in values]
        if any(index >= joint_count for index in indices):
            raise ValueError('JOINTS_0 references a joint outside the body skin')
        if any(not math.isfinite(value) or value < 0 or value > 1 for value in values):
            raise ValueError('WEIGHTS_0 must contain finite values between zero and one')
        influences.append(sum(weight for index, weight in zip(indices, values) if index == head_joint))
    return influences


def static_head_meshes(document):
    if document.get('skins') or document.get('animations'):
        raise ValueError('Replacement head must be static and unskinned')
    declared = set(document.get('extensionsUsed', [])) | set(document.get('extensionsRequired', []))
    def extension_names(value):
        if isinstance(value, dict):
            declared.update(value.get('extensions', {}))
            for item in value.values():
                extension_names(item)
        elif isinstance(value, list):
            for item in value:
                extension_names(item)
    extension_names(document)
    unsupported = declared - HEAD_EXTENSIONS
    if unsupported:
        raise ValueError('Unsupported replacement extensions: ' + ', '.join(sorted(unsupported)))
    scenes = document.get('scenes', [])
    if not scenes:
        raise ValueError('Replacement head needs an active scene')
    roots = scenes[document.get('scene', 0)].get('nodes', [])
    meshes, seen = [], set()
    def visit(index):
        if index in seen:
            raise ValueError('Replacement scene contains repeated nodes/cycles')
        seen.add(index)
        node = document['nodes'][index]
        identity = {'translation': [0, 0, 0], 'scale': [1, 1, 1],
                    'matrix': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]}
        for key, expected in identity.items():
            if key in node and (len(node[key]) != len(expected) or
                any(not math.isfinite(a) or abs(a - b) > 1e-6 for a, b in zip(node[key], expected))):
                raise ValueError('Apply replacement node transforms into vertex coordinates first')
        rotation = node.get('rotation', [0, 0, 0, 1])
        if len(rotation) != 4 or any(not math.isfinite(x) for x in rotation) or max(abs(x) for x in rotation[:3]) > 1e-6 or abs(abs(rotation[3]) - 1) > 1e-6:
            raise ValueError('Apply replacement node rotation first')
        if 'skin' in node or node.get('weights'):
            raise ValueError('Replacement head must be unskinned and have no morph weights')
        if 'mesh' in node:
            meshes.append(node['mesh'])
        for child in node.get('children', []):
            visit(child)
    for root in roots:
        visit(root)
    if not meshes or len(meshes) != len(set(meshes)):
        raise ValueError('Expected at least one non-instanced replacement mesh')
    return meshes


def graft(body, body_binary, head, head_binary, cut_y):
    """Return (GLB bytes, mapping report), leaving both input documents untouched."""
    if not math.isfinite(cut_y):
        raise ValueError('cut-y must be finite')
    validate_document(body, body_binary)
    validate_document(head, head_binary)
    head_meshes = static_head_meshes(head)
    skinned = [(i, node) for i, node in enumerate(body.get('nodes', [])) if 'mesh' in node and 'skin' in node]
    if len(skinned) != 1:
        raise ValueError('Body must contain exactly one skinned mesh node')
    body_node_index, body_node = skinned[0]
    skin = body['skins'][body_node['skin']]
    head_indices = [i for i, node_index in enumerate(skin['joints']) if body['nodes'][node_index].get('name') == 'Head']
    if len(head_indices) != 1:
        raise ValueError('Body skin must contain exactly one Head joint')
    head_joint = head_indices[0]
    if head_joint > 65535:
        raise ValueError('Head joint does not fit glTF JOINTS_0')
    result, binary = copy.deepcopy(body), bytearray(body_binary)
    old_primitives = body['meshes'][body_node['mesh']]['primitives']
    mappings, retained_primitives, retained_total, deleted_total = [], [], 0, 0
    for primitive_index, primitive in enumerate(old_primitives):
        points, faces = triangles(body, body_binary, primitive)
        influences = head_influences(body, body_binary, primitive, head_joint, len(skin['joints']), len(points))
        retained, deleted, index_values, preserved_high_collar = [], [], [], []
        for face_index, face in enumerate(faces):
            above_cut = sum(points[index][1] for index in face) / 3 > cut_y
            head_dominant = sum(influences[index] for index in face) / 3 >= .5
            if above_cut and head_dominant:
                deleted.append(face_index)
            else:
                retained.append(face_index)
                index_values.extend(face)
                if above_cut and not head_dominant:
                    preserved_high_collar.append(face_index)
        retained_total += len(retained)
        deleted_total += len(deleted)
        if retained:
            updated = copy.deepcopy(primitive)
            component_type, code = (5123, 'H') if max(index_values) < 65536 else (5125, 'I')
            payload = struct.pack('<' + code * len(index_values), *index_values)
            updated['indices'] = append_accessor(result, binary, payload, component_type, 'SCALAR', len(index_values), 34963)
            retained_primitives.append(updated)
        mappings.append({'original_primitive': primitive_index,
                         'output_primitive': len(retained_primitives) - 1 if retained else None,
                         'retained_triangle_ids': retained, 'deleted_triangle_ids': deleted,
                         'retained_above_cut_non_head_triangle_ids': preserved_high_collar})
    if deleted_total == 0 or retained_total == 0:
        raise ValueError('Cut must delete some but not all body triangles')

    binary.extend(b'\0' * (-len(binary) % 4))
    head_binary_offset = len(binary)
    binary.extend(head_binary)
    offsets = {name: len(result.setdefault(name, [])) for name in
               ('bufferViews', 'accessors', 'images', 'samplers', 'textures', 'materials')}
    for source in head.get('bufferViews', []):
        item = copy.deepcopy(source)
        item['buffer'], item['byteOffset'] = 0, head_binary_offset + source.get('byteOffset', 0)
        result['bufferViews'].append(item)
    for source in head.get('accessors', []):
        item = copy.deepcopy(source)
        item['bufferView'] += offsets['bufferViews']
        result['accessors'].append(item)
    for source in head.get('images', []):
        item = copy.deepcopy(source)
        item['bufferView'] += offsets['bufferViews']
        result['images'].append(item)
    result['samplers'].extend(copy.deepcopy(head.get('samplers', [])))
    for source in head.get('textures', []):
        item = copy.deepcopy(source)
        if 'source' not in item:
            raise ValueError('Replacement texture requires an embedded image source')
        item['source'] += offsets['images']
        if 'sampler' in item:
            item['sampler'] += offsets['samplers']
        result['textures'].append(item)
    def remap_material(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key.endswith('Texture') and isinstance(item, dict) and 'index' in item:
                    item['index'] += offsets['textures']
                remap_material(item)
        elif isinstance(value, list):
            for item in value:
                remap_material(item)
    for i, source in enumerate(head.get('materials', [])):
        item = copy.deepcopy(source)
        name = item.get('name', f'head_{i}')
        item['name'] = name if name.startswith('tripo_') else 'tripo_' + name
        remap_material(item)
        result['materials'].append(item)
    default_material = None
    head_mapping = []
    for mesh_index in head_meshes:
        for primitive_index, primitive in enumerate(head['meshes'][mesh_index]['primitives']):
            points, faces = triangles(head, head_binary, primitive)
            if any(name.startswith(('JOINTS_', 'WEIGHTS_')) for name in primitive['attributes']):
                raise ValueError('Replacement contains skin attributes')
            if any(head['accessors'][accessor]['count'] != len(points) for accessor in primitive['attributes'].values()):
                raise ValueError('Replacement vertex attribute counts differ')
            updated = copy.deepcopy(primitive)
            updated['attributes'] = {name: accessor + offsets['accessors'] for name, accessor in primitive['attributes'].items()}
            if 'indices' in updated:
                updated['indices'] += offsets['accessors']
            extras = primitive.get('extras', {})
            if not isinstance(extras, dict):
                raise ValueError('Replacement primitive extras must be an object')
            bound_name = 'Head'
            if 'rig_joint' in extras:
                if extras['rig_joint'] not in ('L_Eye', 'R_Eye'):
                    raise ValueError('Unsupported rig_joint tag; only L_Eye/R_Eye are allowed')
                bound_name = extras['rig_joint']
            matches = [i for i, node in enumerate(skin['joints']) if body['nodes'][node].get('name') == bound_name]
            if len(matches) != 1 or matches[0] > 65535:
                raise ValueError('Body skin needs exactly one supported ' + bound_name + ' joint')
            bound_joint = matches[0]
            joints = struct.pack('<4H', bound_joint, 0, 0, 0) * len(points)
            weights = struct.pack('<4f', 1, 0, 0, 0) * len(points)
            updated['attributes']['JOINTS_0'] = append_accessor(result, binary, joints, 5123, 'VEC4', len(points), 34962)
            updated['attributes']['WEIGHTS_0'] = append_accessor(result, binary, weights, 5126, 'VEC4', len(points), 34962)
            if 'material' in updated:
                updated['material'] += offsets['materials']
            else:
                if default_material is None:
                    default_material = len(result['materials'])
                    result['materials'].append({'name': 'tripo_head_default'})
                updated['material'] = default_material
            head_mapping.append({'head_mesh': mesh_index, 'head_primitive': primitive_index,
                                 'output_primitive': len(retained_primitives), 'vertices': len(points), 'triangles': len(faces),
                                 'bound_joint': bound_name, 'skin_joint_index': bound_joint,
                                 'skin_node_index': skin['joints'][bound_joint]})
            retained_primitives.append(updated)
    if not head_mapping:
        raise ValueError('Replacement head contains no triangle primitives')
    result['meshes'][body_node['mesh']]['primitives'] = retained_primitives
    for name in ('extensionsUsed', 'extensionsRequired'):
        merged = list(dict.fromkeys(body.get(name, []) + head.get(name, [])))
        if merged:
            result[name] = merged
    result['buffers'][0]['byteLength'] = len(binary)
    streams = []
    for i, accessor in enumerate(body.get('accessors', [])):
        before = sha(stream_bytes(body, body_binary, i))
        after = sha(stream_bytes(result, binary, i))
        streams.append({'accessor': i, 'sha256_before': before, 'sha256_after': after, 'equal': before == after})
    report = {'coordinate_contract': 'same body mesh-local coordinates; +Y up; identity replacement node transforms',
              'cut_y': cut_y, 'cut_rule': 'delete triangle when centroid Y > cut_y AND average Head influence >= 0.5',
              'retained_above_cut_non_head_triangles': sum(len(row['retained_above_cut_non_head_triangle_ids']) for row in mappings),
              'body_mesh_node': body_node_index, 'head_skin_joint_index': head_joint,
              'head_node_index': skin['joints'][head_joint], 'retained_body_triangles': retained_total,
              'deleted_body_triangles': deleted_total, 'body_triangle_mapping': mappings,
              'head_primitive_mapping': head_mapping, 'head_resource_index_offsets': offsets,
              'original_body_binary_sha256': sha(body_binary),
              'original_body_binary_prefix_equal': bytes(binary[:len(body_binary)]) == body_binary,
              'original_body_streams': streams,
              'all_original_body_streams_equal': all(row['equal'] for row in streams),
              'skin_json_equal': result['skins'] == body['skins'],
              'nodes_rest_json_equal': result['nodes'] == body['nodes'],
              'original_materials_json_equal': result['materials'][:len(body.get('materials', []))] == body.get('materials', []),
              'original_images_json_equal': result['images'][:len(body.get('images', []))] == body.get('images', [])}
    output = encode_glb(result, bytes(binary))
    report['output_sha256'] = sha(output)
    return output, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('body', 'head', 'output', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--cut-y', type=float, required=True)
    args = parser.parse_args()
    if len({path.resolve() for path in (args.body, args.head, args.output, args.report)}) != 4:
        parser.error('Body, head, output and report must be distinct paths')
    body, body_binary = read_glb(args.body)
    head, head_binary = read_glb(args.head)
    output, report = graft(body, body_binary, head, head_binary, args.cut_y)
    report.update({'body_source': str(args.body.resolve()), 'body_source_sha256': sha(args.body.read_bytes()),
                   'head_source': str(args.head.resolve()), 'head_source_sha256': sha(args.head.read_bytes())})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'sha256': report['output_sha256'],
                      'retained_triangles': report['retained_body_triangles'],
                      'deleted_triangles': report['deleted_body_triangles']}))


if __name__ == '__main__':
    main()
