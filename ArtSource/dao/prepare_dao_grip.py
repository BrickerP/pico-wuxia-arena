"""Derive the player grip frame while preserving the original GLB payload.

Run with Python 3. Geometry, materials and embedded images remain unchanged.
The Grip root is identity, glTF uses +Y up, and the blade extends toward -Z.
"""

import copy
import json
import math
import struct
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'dao_study.glb'
OUTPUT = HERE / 'dao_grip.glb'


def prepare():
    data = SOURCE.read_bytes()
    magic, version, total = struct.unpack_from('<4sII', data)
    json_length, kind = struct.unpack_from('<II', data, 12)
    if magic != b'glTF' or version != 2 or total != len(data) or kind != 0x4E4F534A:
        raise ValueError('source must be a valid GLB 2.0 container')
    original = json.loads(data[20:20+json_length])
    if original.get('skins') or original.get('animations'):
        raise ValueError('this coordinate derivation expects the static dao source')
    doc = copy.deepcopy(original)
    nodes = doc['nodes']
    root_index = next(i for i, node in enumerate(nodes) if node.get('name') == 'DAO_Root')
    grip_index = next(i for i, node in enumerate(nodes) if node.get('name') == 'Grip')
    root = nodes[root_index]
    if any(key in root for key in ('matrix', 'translation', 'rotation', 'scale')):
        raise ValueError('source dao root must have an identity transform')
    if grip_index not in root['children']:
        raise ValueError('source Grip must be a direct root child')
    source_grip = nodes[grip_index]['translation']
    half_sqrt = math.sqrt(.5)
    rotation = [-half_sqrt, 0, 0, half_sqrt]
    for index in root['children']:
        if index == grip_index:
            continue
        node = nodes[index]
        if 'matrix' in node or node.get('rotation', [0,0,0,1]) != [0,0,0,1]:
            raise ValueError('source child rotation contract changed: ' + node.get('name', ''))
        position = node.get('translation', [0,0,0])
        x, y, z = (position[i]-source_grip[i] for i in range(3))
        node['translation'] = [x, z, -y]
        node['rotation'] = rotation.copy()
    root['name'] = 'Grip'
    root['extras'] = {'units': 'metres', 'origin': 'grip centre',
                      'frame': 'glTF +Y up, blade forward -Z'}
    root['children'].remove(grip_index)
    index_map = {old: new for new, old in enumerate(i for i in range(len(nodes)) if i != grip_index)}
    doc['nodes'] = [node for i, node in enumerate(nodes) if i != grip_index]
    for node in doc['nodes']:
        if 'children' in node:
            node['children'] = [index_map[i] for i in node['children']]
    for scene in doc['scenes']:
        scene['nodes'] = [index_map[i] for i in scene['nodes']]
    if any(doc.get(key) != original.get(key) for key in
           ('meshes', 'materials', 'images', 'textures', 'samplers', 'accessors', 'bufferViews', 'buffers')):
        raise AssertionError('asset content changed beyond the node frame')
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    payload = data[20+json_length:]
    output = struct.pack('<4sII', b'glTF', 2, 20+len(encoded)+len(payload))
    output += struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + payload
    by_name = {node.get('name'): node for node in doc['nodes']}
    for name in ('Blade_Base', 'Blade_Tip'):
        print(name, by_name[name]['translation'])
    if by_name['Blade_Tip']['translation'][2] >= 0:
        raise AssertionError('blade tip must point toward -Z')
    if len([node for node in doc['nodes'] if node.get('name') == 'Grip']) != 1:
        raise AssertionError('grip root must be unique')
    temporary = OUTPUT.with_suffix('.pending.glb')
    temporary.write_bytes(output)
    temporary.replace(OUTPUT)
    print('PASS Grip identity root, unchanged mesh/material/image definitions and binary payload')
    print('Saved', OUTPUT)


if __name__ == '__main__':
    prepare()
