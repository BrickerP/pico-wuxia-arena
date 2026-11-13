"""Independent final-GLB invariants for the bounded entrance replacement."""
from pathlib import Path
import hashlib
import json
import sys
import unittest

import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
from verify_environment import read,rows,active_nodes,world_primitives
sys.path.insert(0,str(BASE/'facade-polish'))
from build_facade import budget

SOURCE=BASE/'facade-polish/courtyard_facade_polish.glb'
CANDIDATE=HERE/'courtyard_native_entrance.glb'

def payload(d,b,i):
    v=d['bufferViews'][d['images'][i]['bufferView']]
    a=v.get('byteOffset',0)
    return b[a:a+v['byteLength']]

def primitive_content(d,b,p):
    return {k:rows(d,b,a).tobytes() for k,a in p['attributes'].items()},rows(d,b,p['indices']).tobytes(),p.get('material')

class EntranceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s,cls.sb=read(SOURCE)
        cls.d,cls.b=read(CANDIDATE)
        cls.wp=list(world_primitives(cls.d,cls.b))

    def test_budget_and_single_environment(self):
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605')
        self.assertLessEqual(sum(len(ix) for _,_,_,ix in self.wp),250000)
        self.assertEqual(len(self.d['materials']),32)
        self.assertEqual(len(self.d['images']),50)
        roots=self.d['scenes'][self.d.get('scene',0)]['nodes']
        self.assertEqual(roots,self.s['scenes'][self.s.get('scene',0)]['nodes'])
        self.assertEqual(len(active_nodes(self.d)),len(self.d['nodes']))

    def test_all_materials_and_images_reused_exactly(self):
        self.assertEqual(self.s['materials'],self.d['materials'])
        self.assertEqual(self.s['textures'],self.d['textures'])
        for i in range(50):self.assertEqual(payload(self.s,self.sb,i),payload(self.d,self.b,i))

    def test_nine_windows_and_unaffected_meshes_unchanged(self):
        # The full source document survives, with only the audited four meshes
        # eligible for local subtraction. Compare actual streams, not just names.
        for mi,sm in enumerate(self.s['meshes']):
            if mi in {4,22,23,30}:continue
            cm=self.d['meshes'][mi]
            self.assertEqual(len(sm['primitives']),len(cm['primitives']),mi)
            for a,b in zip(sm['primitives'],cm['primitives']):
                self.assertEqual(primitive_content(self.s,self.sb,a),primitive_content(self.d,self.b,b),mi)
        # Wall plaster, already cut around the nine windows, must not be recut.
        self.assertEqual(primitive_content(self.s,self.sb,self.s['meshes'][23]['primitives'][0]),primitive_content(self.d,self.b,self.d['meshes'][23]['primitives'][0]))
        for ni in range(41,50):self.assertEqual(self.s['nodes'][ni],self.d['nodes'][ni])

    def test_ground_anchors_and_all_existing_transforms(self):
        for ni,node in enumerate(self.s['nodes']):
            for key in ['translation','rotation','scale','matrix','name','mesh']:
                self.assertEqual(node.get(key),self.d['nodes'][ni].get(key),(ni,key))
        ground=np.concatenate([v for n,_,v,_ in self.wp if n=='EH_GroundReceiver'])
        self.assertAlmostEqual(float(ground[:,1].max()),0,places=6)

    def test_combat_volume_remains_empty(self):
        lo=np.array([-1.35,.05,-3]);hi=np.array([1.35,2.4,.8])
        intruders=[]
        for name,_,v,ix in self.wp:
            t=v[ix]
            if np.any(np.all(t.max(axis=1)>lo,axis=1)&np.all(t.min(axis=1)<hi,axis=1)):intruders.append(name)
        self.assertEqual(intruders,[])

    def test_exposed_terrace_cuts_are_closed_and_face_inward(self):
        p=self.d['meshes'][23]['primitives'][1]
        v=rows(self.d,self.b,p['attributes']['POSITION'])
        ix=rows(self.d,self.b,p['indices']).reshape(-1,3)
        t=v[ix].astype(np.float64)
        for x,nx in [(-1.62,1),(1.62,-1)]:
            mask=np.all(np.abs(t[:,:,0]-x)<2e-6,axis=1)
            cap=t[mask]
            self.assertEqual(len(cap),6)
            area=np.cross(cap[:,1]-cap[:,0],cap[:,2]-cap[:,0])
            self.assertTrue(np.all(area[:,0]*nx>0))
            self.assertAlmostEqual(float(np.linalg.norm(area,axis=1).sum()/2),.105568,places=6)

    def test_new_geometry_finite_and_no_runtime_content(self):
        self.assertFalse(self.d.get('animations'))
        self.assertFalse(self.d.get('cameras'))
        self.assertNotIn('KHR_lights_punctual',self.d.get('extensions',{}))
        added=self.d['meshes'][len(self.s['meshes']):]
        self.assertTrue(added)
        for m in added:
            for p in m['primitives']:
                a=p['attributes'];v=rows(self.d,self.b,a['POSITION']);ix=rows(self.d,self.b,p['indices']).reshape(-1,3)
                for key,index in a.items():self.assertTrue(np.isfinite(rows(self.d,self.b,index)).all(),key)
                t=v[ix].astype(np.float64)
                self.assertTrue(np.all(np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)>1e-12))
                if 'normalTexture' in self.d['materials'][p['material']]:self.assertIn('TANGENT',a)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EntranceChecks))
    d,b=read(CANDIDATE)
    report={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'sha256':hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),'budget':budget(d,b),'scope':'Offline final-GLB invariants. No collision, navigation, native rendering or headset performance claim.'}
    (HERE/'review/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
