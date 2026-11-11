"""Offline geometry, motion coverage and normal-distance size checks for wet v3."""
import hashlib
import importlib.util
import json
import math
import struct
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OLD = HERE.parents[1] / 'wet/verify_wet.py'
spec = importlib.util.spec_from_file_location('readonly_wet_streams', OLD)
streams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(streams)


def coverage(document, motion):
    meshes = [n['name'] for n in document['nodes'] if 'mesh' in n]
    driven = [n['node'] for key in ('particles', 'cores', 'accents') for n in motion[key]]
    if len(driven) != len(set(driven)) or sorted(meshes) != sorted(driven):
        raise ValueError('Every visible mesh must be driven exactly once')


class MotionChecks(unittest.TestCase):
    def test_complete_node_coverage(self):
        coverage({'nodes': [{'name': 'drop', 'mesh': 0}]},
                 {'particles': [{'node': 'drop'}], 'cores': [], 'accents': []})

    def test_missing_and_duplicate_node_are_rejected(self):
        document = {'nodes': [{'name': 'drop', 'mesh': 0}]}
        for particles in ([], [{'node': 'drop'}, {'node': 'drop'}]):
            with self.assertRaises(ValueError):
                coverage(document, {'particles': particles, 'cores': [], 'accents': []})

    def test_particle_lifetime_boundary(self):
        keys = [[0, 0], [.008, .98], [.08, .74], [.2, 0]]
        self.assertGreater(streams.sample_opacity(keys, .05), 0)
        for age in (-.01, .2, .4):
            self.assertEqual(0, streams.sample_opacity(keys, age))


def verify():
    path = HERE / 'wet_cloth_contact.glb';raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size = struct.unpack_from('<I', raw, 12)[0];document = json.loads(raw[20:20+size])
    binary_length = struct.unpack_from('<I', raw, 20+size)[0];binary = raw[28+size:28+size+binary_length]
    motion = json.loads((HERE / 'motion.json').read_text())
    assert motion['schema'] == 'contact-particle-motion/v2'
    coverage(document, motion)
    assert not document.get('animations') and not document.get('extensionsUsed')
    assert len(document['meshes']) == len(motion['particles']) == 23
    assert motion['gravity_stage_mps2'] == [0, -9.81, 0]
    assert sum(p['type']=='droplet' for p in motion['particles']) == 18
    assert sum(p['type']=='fiber' for p in motion['particles']) == 5
    triangles = 0;measurements = []
    for p in motion['particles']:
        node = next(n for n in document['nodes'] if n['name'] == p['node'])
        assert node['translation'] == p['initial_position_local_m']
        primitive = document['meshes'][node['mesh']]['primitives'][0]
        vertices = streams.stream(document, binary, primitive['attributes']['POSITION'])
        normals = streams.stream(document, binary, primitive['attributes']['NORMAL'])
        indices = [r[0] for r in streams.stream(document, binary, primitive['indices'])]
        assert all(0 <= i < len(vertices) for i in indices)
        assert all(math.isfinite(v) for row in vertices for v in row)
        assert all(abs(math.sqrt(sum(v*v for v in n))-1)<1e-5 for n in normals)
        extent = [max(v[a] for v in vertices)-min(v[a] for v in vertices) for a in range(3)]
        if p['type']=='droplet':
            for a,b,c in zip(indices[0::3], indices[1::3], indices[2::3]):
                u=[vertices[b][i]-vertices[a][i] for i in range(3)];v=[vertices[c][i]-vertices[a][i] for i in range(3)]
                cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                center=[(vertices[a][i]+vertices[b][i]+vertices[c][i])/3 for i in range(3)]
                assert sum(cross[i]*center[i] for i in range(3))>0
            if p['shape']=='stretched':
                assert abs(extent[0]-p['length_m'])<1e-8
                assert abs(extent[1]-p['cross_section_diameter_m'])<1e-8
            else:
                assert p['shape']=='round' and abs(max(extent)-p['diameter_m'])<1e-8
        else:
            assert p['shape']=='ribbon_cross' and abs(extent[0]-p['length_m'])<1e-8
            assert abs(extent[1]-p['width_m'])<1e-8
        assert .18 <= p['lifetime_s'] <= .40
        keys=p['opacity_keys'];assert keys[0][0]==0 and keys[-1]==[p['lifetime_s'],0]
        assert all(a[0]<b[0] for a,b in zip(keys,keys[1:]))
        assert all(0<=alpha<=1 for _,alpha in keys)
        assert p['priority'] in (45,55,80,85,100)
        assert len(p['orientation_axis_local'])==3
        triangles += len(indices)//3
        measurements.append({'node':p['node'],'type':p['type'],'shape':p['shape'],'tier':p['tier'],'bbox_extent_m':extent})
    assert triangles==596
    for m in document['materials']:
        assert m['alphaMode']=='BLEND' and m['pbrMetallicRoughness']['metallicFactor']==0
        assert m['emissiveFactor']==[0,0,0]
    focal=1280/(2*math.tan(math.radians(60)/2))
    budget={str(distance):{'hero9mm_px':focal*.009/distance,'main7mm_px':focal*.007/distance,
                           'fine3mm_px':focal*.003/distance,'stretched18mm_length_px':focal*.018/distance,
                           'stretched4_5mm_width_px':focal*.0045/distance} for distance in (1.5,2.5)}
    report={'status':'OFFLINE_SOURCE_CHECKS_PASS','visual_status':'Root normal-distance renderer and PICO review pending',
            'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'schema':motion['schema'],
            'droplets':18,'fibers':5,'driven_mesh_nodes':23,'triangles':triangles,'materials':3,
            'all_meshes_driven_exactly_once':True,'normals_and_closed_drop_winding':'PASS',
            'measurement':measurements,'projected_on_axis_budget_1280px_hfov60':budget}
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='measurement'},indent=2))


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(MotionChecks))
    if not result.wasSuccessful():raise SystemExit(1)
    verify()
