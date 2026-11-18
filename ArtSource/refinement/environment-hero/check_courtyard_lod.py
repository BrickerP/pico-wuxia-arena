"""Compare two GLBs with Blender's BVH; run blender -b -t 1 -P this_file -- source.glb candidate.glb."""
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from mathutils.bvhtree import BVHTree


def load(path):
    data = Path(path).read_bytes()
    end = 20 + struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:end])
    assert data[:4] == b'glTF' and len(data) == struct.unpack_from('<I', data, 8)[0]
    return doc, memoryview(data)[end+8:]


def view(bank, index):
    item = bank[0]['bufferViews'][index]
    start = item.get('byteOffset', 0)
    return bank[1][start:start+item['byteLength']]


def accessor(bank, index):
    item = bank[0]['accessors'][index]
    dtype = {5123:'<u2',5125:'<u4',5126:'<f4'}[item['componentType']]
    return np.frombuffer(view(bank, item['bufferView']), dtype=dtype).reshape(item['count'], -1)


def mesh(bank, primitive):
    positions = accessor(bank, primitive['attributes']['POSITION'])
    indices = accessor(bank, primitive['indices']).reshape(-1, 3)
    assert np.isfinite(positions).all() and indices.max() < len(positions)
    return positions, indices


def surface_error(vertices, triangles, other_vertices, other_triangles):
    tree = BVHTree.FromPolygons(other_vertices.tolist(), other_triangles.tolist(), all_triangles=True)
    referenced = vertices[np.unique(triangles)]
    centers = vertices[triangles].mean(axis=1)
    return max(tree.find_nearest(point)[3] for points in (referenced, centers) for point in points)


def vertex_records(bank, primitive, names):
    rows = np.concatenate([accessor(bank,primitive['attributes'][name]) for name in names], axis=1)
    return set(map(bytes, rows))


def main(source_path, output_path):
    source, out = load(source_path), load(output_path)
    first, second = source[0], out[0]
    for key in ('nodes','scene','scenes','materials','textures','samplers','extensionsUsed','extensionsRequired'):
        assert first[key] == second[key], key
    assert len(first['images']) == len(second['images'])
    for old, new in zip(first['images'], second['images']):
        assert dict(old,bufferView=0) == dict(new,bufferView=0)
        assert view(source, old['bufferView']) == view(out, new['bufferView'])
    report = []
    totals = np.zeros(2, dtype=np.int64)
    assert len(first['meshes']) == len(second['meshes'])
    for index, (old, new) in enumerate(zip(first['meshes'], second['meshes'])):
        name = old['name']
        assert name == new['name'] and len(old['primitives']) == len(new['primitives'])
        count = sum(node.get('mesh') == index for node in first['nodes'])
        for a, b in zip(old['primitives'], new['primitives']):
            assert a['material'] == b['material'] and a['attributes'].keys() == b['attributes'].keys()
            pos_a, tri_a = mesh(source, a)
            pos_b, tri_b = mesh(out, b)
            totals += np.array([len(tri_a),len(tri_b)]) * count
            if len(tri_a) == len(tri_b):
                assert np.array_equal(tri_a,tri_b)
                for key in a['attributes']:
                    assert np.array_equal(accessor(source,a['attributes'][key]),accessor(out,b['attributes'][key]))
                continue
            assert name.startswith(('EH_EastRoof','EH_WestRoof','EH_TavernMainRoof','EH_TavernPorchRoof',
                'EH_TownLowerEave','EH_TownRoof','EH_SideGalleryWindows','Facade_SharedGroundWindowCore',
                'Facade_UpperWindowCore','Facade_BatchedTileEnds'))
            names = sorted(a['attributes'])
            assert vertex_records(out,b,names) <= vertex_records(source,a,names), name
            errors = [surface_error(pos_a,tri_a,pos_b,tri_b),surface_error(pos_b,tri_b,pos_a,tri_a)]
            tolerance = .005 if 'Window' in name else .015
            assert max(errors) <= tolerance, (name, a['material'], errors)
            report.append({'mesh':name,'material':a['material'],'samples_to_new_m':errors[0],'samples_to_old_m':errors[1]})
    assert totals[1] <= .75 * totals[0]
    print(json.dumps({'output_sha256':hashlib.sha256(Path(output_path).read_bytes()).hexdigest(),
                      'node_triangles':totals.tolist(),'changed_primitives':len(report),
                      'worst_bidirectional_sample_m':max(max(p['samples_to_new_m'],p['samples_to_old_m']) for p in report),
                      'surfaces':report}))


if __name__ == '__main__':
    main(*sys.argv[sys.argv.index('--')+1:])
