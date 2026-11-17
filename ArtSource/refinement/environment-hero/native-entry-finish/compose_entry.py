"""Append real timber replacement to the fixed full PNG and KTX scene."""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ENV = HERE.parent
ROOT = ENV.parents[2]
sys.path[:0] = [str(ENV), str(ENV / 'stage2'), str(ENV / 'single-window-integration-2026-11-12'),
               str(ENV / 'facade-polish')]
from verify_environment import read, rows
from create_candidate import components, encode, tangents
from build_courtyard import Output
from build_facade import budget

SOURCES = {
    'png': (ENV / 'native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_png.glb',
            'd935d8185dff6750838bc1d5d98c0b1f07bdce4b0a25249e42957bc501fbe06d'),
    'ktx': (ENV / 'native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_ktx.glb',
            'c7f2e2b2833cdd84fbc73918fdcd2f9036dee582a46c29d8db67df806e77fc78'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_removed(doc, blob):
    removed = {}
    p = doc['meshes'][22]['primitives'][0]
    pos = rows(doc, blob, p['attributes']['POSITION'])
    ix = rows(doc, blob, p['indices']).reshape(-1, 3)
    chosen = set()
    counts = []
    for side in [-1, 1]:
        matches = []
        for group in components(pos, ix):
            lo, hi = pos[group].min(0), pos[group].max(0)
            if np.allclose(lo, [side * 1.4 - .115, .285, -5.385], atol=2e-5, rtol=0) and np.allclose(
                    hi, [side * 1.4 + .115, 4.9, -5.095], atol=2e-5, rtol=0):
                matches.append(group)
        if len(matches) != 1:
            raise ValueError('Original full-height post selection is ambiguous')
        chosen.update(int(v) for v in matches[0])
    mask = np.isin(ix, list(chosen)).any(axis=1)
    if int(mask.sum()) != 76:
        raise ValueError('Frozen two-post triangle count changed: ' + str(mask.sum()))
    removed[(22, 0)] = mask
    # Exact old three-part bracket domains, excluding all door leaves, jambs,
    # paper, iron, stone piers, transom and lanterns.
    offset = np.array(doc['nodes'][52]['translation'])
    for pi in [0, 1]:
        prim = doc['meshes'][36]['primitives'][pi]
        pos = rows(doc, blob, prim['attributes']['POSITION']) + offset
        ix = rows(doc, blob, prim['indices']).reshape(-1, 3)
        tris = pos[ix]
        mask = np.zeros(len(ix), dtype=bool)
        for side in [-1, 1]:
            lo = np.array([side * 1.4 - .112, 2.43, -5.105])
            hi = np.array([side * 1.4 + .112, 3.021, -4.78])
            mask |= np.all(tris >= lo - 2e-5, axis=(1, 2)) & np.all(tris <= hi + 2e-5, axis=(1, 2))
        removed[(36, pi)] = mask
    return removed


def compose(source, expected, module, mb):
    if sha(source) != expected:
        raise ValueError('Pinned full scene identity changed')
    doc, blob = read(source)
    out = Output(copy.deepcopy(doc), blob)
    masks = select_removed(doc, blob)
    removed = []
    for (mi, pi), mask in masks.items():
        source_prim = doc['meshes'][mi]['primitives'][pi]
        ix = rows(doc, blob, source_prim['indices']).reshape(-1, 3)
        out.doc['meshes'][mi]['primitives'][pi]['indices'] = out.accessor(ix[~mask].reshape(-1, 1), 'SCALAR', True)
        removed.append({'mesh': mi, 'primitive': pi, 'removed_triangles': int(mask.sum()),
                        'kept_index_sha256': hashlib.sha256(ix[~mask].astype('<u4').tobytes()).hexdigest()})
    views, accessors, meshes, nodes = {}, {}, {}, {}
    def view(index):
        if index not in views:
            src = module['bufferViews'][index]
            start = src.get('byteOffset', 0)
            views[index] = out.view(mb[start:start + src['byteLength']], src.get('target'))
            if 'byteStride' in src:
                out.doc['bufferViews'][-1]['byteStride'] = src['byteStride']
        return views[index]
    def accessor(index):
        if index not in accessors:
            item = copy.deepcopy(module['accessors'][index])
            item['bufferView'] = view(item['bufferView'])
            out.doc['accessors'].append(item)
            accessors[index] = len(out.doc['accessors']) - 1
        return accessors[index]
    def mesh(index):
        if index not in meshes:
            item = copy.deepcopy(module['meshes'][index])
            for prim in item['primitives']:
                attributes = prim['attributes'].copy()
                source_indices = prim['indices']
                prim['attributes'] = {name: accessor(value) for name, value in prim['attributes'].items()}
                prim['indices'] = accessor(prim['indices'])
                if 'TANGENT' not in attributes:
                    positions = rows(module, mb, attributes['POSITION']).astype(float)
                    normals = rows(module, mb, attributes['NORMAL']).astype(float)
                    uv = rows(module, mb, attributes['TEXCOORD_0']).astype(float)
                    indices = rows(module, mb, source_indices).reshape(-1, 3)
                    fallback = np.zeros((len(positions), 4), dtype=float)
                    fallback[:, 0] = 1
                    fallback[:, 3] = 1
                    values = tangents(positions, normals, uv, indices, fallback)
                    prim['attributes']['TANGENT'] = out.accessor(values, 'VEC4')
                material_name = module['materials'][prim['material']]['name']
                prim['material'] = {'Method | CC0 directional wood .8m': 29,
                                    'Method | original endgrain .25m': 30}[material_name]
            out.doc['meshes'].append(item)
            meshes[index] = len(out.doc['meshes']) - 1
        return meshes[index]
    def node(index):
        if index not in nodes:
            item = copy.deepcopy(module['nodes'][index])
            out.doc['nodes'].append(item)
            nodes[index] = len(out.doc['nodes']) - 1
            if 'mesh' in item:
                item['mesh'] = mesh(item['mesh'])
            if 'children' in item:
                item['children'] = [node(child) for child in item['children']]
        return nodes[index]
    root = out.doc['scenes'][out.doc.get('scene', 0)]['nodes'][0]
    roots = [node(i) for i in module['scenes'][module.get('scene', 0)]['nodes']]
    out.doc['nodes'].append({'name': 'NativeEntryFinish_Root', 'children': roots,
                             'extras': {'role': 'fixed existing doorway timber joinery finish; no light or gameplay'}})
    out.doc['nodes'][root]['children'].append(len(out.doc['nodes']) - 1)
    data = encode(out.doc, out.blob)
    return data, removed, budget(out.doc, out.blob)


def main():
    module, blob = read(HERE / 'entry_module.glb')
    outputs = {}
    for label, (source, expected) in SOURCES.items():
        data, removed, cost = compose(source, expected, module, blob)
        if cost['node_expanded_triangles'] > 270000:
            raise ValueError('Full expanded scene exceeds the explicit 270k specimen budget')
        path = HERE / ('courtyard_entry_finish_' + label + '.glb')
        path.write_bytes(data)
        outputs[label] = {'file': path.name, 'sha256': sha(path), 'bytes': len(data),
                          'source_sha256': expected, 'removed': removed, 'budget': cost}
    (HERE / 'composition.json').write_text(json.dumps({'status': 'private_full_scene_first_specimen',
        'module_sha256': sha(HERE / 'entry_module.glb'), 'outputs': outputs,
        'materials_images_textures_unchanged': True}, indent=2) + '\n')
    print('ENTRY_FULL_COMPOSITION_COMPLETE', json.dumps(outputs), flush=True)


if __name__ == '__main__':
    main()
