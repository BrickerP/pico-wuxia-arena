"""Split the project's existing dry soft-contact mesh into independent particles.

No Blender, external package, or generated geometry is needed. This is a bounded
GLB data transformation; the root publishes selected candidates to app assets.
"""
import copy
import hashlib
import json
import math
import random
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCE = REPO / 'app/src/main/assets/models/effects/soft_contact.glb'
SELECTED = (0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 14)


def read_glb(path):
    raw = Path(path).read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20 + size])
    length, kind = struct.unpack_from('<II', raw, 20 + size)
    assert kind == 0x004E4942
    return document, raw[28 + size:28 + size + length]


def accessor(document, binary, index):
    item = document['accessors'][index]
    view = document['bufferViews'][item['bufferView']]
    dimensions = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[item['type']]
    code = {5123: 'H', 5125: 'I', 5126: 'f'}[item['componentType']]
    size = struct.calcsize('<' + code * dimensions)
    stride = view.get('byteStride', size)
    start = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    return [struct.unpack_from('<' + code * dimensions, binary, start + i * stride) for i in range(item['count'])]


def mesh_data(document, binary, node):
    primitive = document['meshes'][node['mesh']]['primitives'][0]
    attributes = {name: accessor(document, binary, index) for name, index in primitive['attributes'].items()}
    indices = [row[0] for row in accessor(document, binary, primitive['indices'])]
    return attributes, indices, primitive['material']


def components(indices):
    # Existing source puffs and streaks share their own vertex indices only.
    adjacent = {}
    for a, b, c in zip(indices[::3], indices[1::3], indices[2::3]):
        for v in (a, b, c):
            adjacent.setdefault(v, set()).update((a, b, c))
    pending = set(adjacent)
    result = []
    while pending:
        seed = min(pending)
        group, queue = set(), [seed]
        while queue:
            value = queue.pop()
            if value not in group:
                group.add(value)
                queue.extend(adjacent[value] - group)
        pending -= group
        result.append(sorted(group))
    return result


class Writer:
    def __init__(self, source):
        self.binary = bytearray()
        self.document = {'asset': {'version': '2.0', 'generator': 'PICO Wuxia Arena soft contact component split'},
                         'scene': 0, 'scenes': [{'nodes': [0]}],
                         'nodes': [{'name': 'soft_contact_polish', 'children': [],
                                    'extras': {'units': 'metres', 'effectPlane': 'X tangent, Y binormal, Z outward normal',
                                               'driver': 'Independent Entity transforms and per-node opacity', 'durationSeconds': .30}}],
                         'meshes': [], 'materials': copy.deepcopy(source['materials']),
                         'accessors': [], 'bufferViews': [], 'buffers': [{'byteLength': 0}]}

    def accessor(self, rows, kind, component=5126, target=34962):
        while len(self.binary) % 4:
            self.binary.append(0)
        start = len(self.binary)
        code = 'f' if component == 5126 else 'H'
        self.binary.extend(struct.pack('<' + code * sum(map(len, rows)), *[v for row in rows for v in row]))
        view_index = len(self.document['bufferViews'])
        self.document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(self.binary) - start, 'target': target})
        item = {'bufferView': view_index, 'componentType': component, 'count': len(rows), 'type': kind}
        if kind in ('VEC3', 'SCALAR'):
            item['min'] = [min(row[axis] for row in rows) for axis in range(len(rows[0]))]
            item['max'] = [max(row[axis] for row in rows) for axis in range(len(rows[0]))]
        index = len(self.document['accessors'])
        self.document['accessors'].append(item)
        return index

    def node(self, name, attributes, indices, material):
        attributes = {key: self.accessor(rows, 'VEC4' if key == 'COLOR_0' else 'VEC3') for key, rows in attributes.items()}
        mesh = len(self.document['meshes'])
        self.document['meshes'].append({'name': name, 'primitives': [{'attributes': attributes,
            'indices': self.accessor([(i,) for i in indices], 'SCALAR', 5123, 34963), 'material': material, 'mode': 4}]})
        node = len(self.document['nodes'])
        self.document['nodes'].append({'name': name, 'mesh': mesh, 'translation': [0, 0, 0]})
        self.document['nodes'][0]['children'].append(node)

    def write(self, path):
        self.document['buffers'][0]['byteLength'] = len(self.binary)
        encoded = json.dumps(self.document, separators=(',', ':')).encode()
        encoded += b' ' * (-len(encoded) % 4)
        binary = bytes(self.binary) + b'\0' * (-len(self.binary) % 4)
        raw = (struct.pack('<4sII', b'glTF', 2, 28 + len(encoded) + len(binary)) +
               struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + struct.pack('<II', len(binary), 0x004E4942) + binary)
        path.write_bytes(raw)
        return {'file': path.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def build():
    document, binary = read_glb(SOURCE)
    writer = Writer(document)
    nodes = {node['name']: node for node in document['nodes']}
    cores = []
    for name, scale, duration in [('core', 1.85, .065), ('scar', 1.25, .085)]:
        attributes, indices, material = mesh_data(document, binary, nodes[name])
        attributes['POSITION'] = [tuple(p[axis] * (scale if axis < 2 else 1) for axis in range(3)) for p in attributes['POSITION']]
        writer.node(name, attributes, indices, material)
        profile = {'lifetime_s': duration, 'opacity_keys': [[0, 1], [.012, .90], [duration, 0]]}
        cores.append({'node': name, 'initial_position_local_m': [0, 0, 0], 'normal': profile, 'parry': profile})
    attributes, indices, material = mesh_data(document, binary, nodes['debris'])
    groups = components(indices)
    assert len(groups) == 30, f'Expected fifteen source puff/streak pairs, got {len(groups)}'
    particles, source_groups = [], []
    rng = random.Random(2026111108)
    for number, source_group in enumerate(SELECTED):
        vertices = sorted(groups[source_group * 2] + groups[source_group * 2 + 1])
        remap = {old: new for new, old in enumerate(vertices)}
        # The puff's source center is its first vertex, shared by its triangle fan.
        center = attributes['POSITION'][groups[source_group * 2][0]]
        subset = {key: [rows[i] for i in vertices] for key, rows in attributes.items()}
        subset['POSITION'] = [tuple(p[a] - center[a] for a in range(3)) for p in subset['POSITION']]
        next_indices = [remap[i] for start in range(0, len(indices), 3)
                        if indices[start] in remap for i in indices[start:start + 3]]
        name = f'chip_{number:02d}'
        writer.node(name, subset, next_indices, material)
        lifetime = .18 + number * .010
        velocity = [rng.uniform(.45, 1.25), rng.uniform(-.30, .48), rng.uniform(.12, .40)]
        particles.append({'node': name, 'type': 'dry_soft_debris', 'initial_position_local_m': [rng.uniform(-.008, .008), rng.uniform(-.008, .008), .004],
                          'initial_velocity_local_mps': velocity, 'lifetime_s': lifetime,
                          'opacity_keys': [[0, .95], [.018, 1], [lifetime * .50, .68], [lifetime, 0]]})
        source_groups.append({'node': name, 'source_debris_pair': source_group, 'source_origin_m': center,
                              'vertex_count': len(vertices), 'triangles': len(next_indices) // 3})
    info = writer.write(HERE / 'soft_contact_polish.glb')
    motion = {'schema': 'contact-particle-motion/v1', 'units': 'metres_seconds', 'asset': 'soft_contact_polish.glb',
              'basis': {'local_x': 'projected actual cutting tangent', 'local_y': 'normal cross tangent', 'local_z': 'outward normal'},
              'gravity_stage_mps2': [0, -9.81, 0], 'normal_offset_owner': 'Root anchor applies shared 8mm normal offset once; p0 does not include it',
              'orientation': 'Keep source particle contact-plane orientation; positions move independently in Stage gravity',
              'contact_semantics': 'Generic dry SOFT presentation only; no water, blood, or inferred wetness',
              'freshness': 'Sample actual presentation age; unborn or expired particles are hidden, never restarted',
              'particles': particles, 'cores': cores}
    (HERE / 'motion.json').write_text(json.dumps(motion, indent=2) + '\n')
    provenance = {'source': str(SOURCE.relative_to(REPO)), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  'candidate': info, 'material_policy': 'All source material objects copied verbatim; source COLOR_0 preserved verbatim',
                  'core_xy_scale': 1.85, 'scar_xy_scale': 1.25, 'source_components': len(groups), 'selected_source_pairs': list(SELECTED),
                  'source_groups': source_groups, 'mesh_count': len(writer.document['meshes']), 'triangles': sum(x['triangles'] for x in source_groups) + 18,
                  'animations': 0, 'publication': 'Review candidate only; no app resource published'}
    (HERE / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps(info))


if __name__ == '__main__':
    build()
