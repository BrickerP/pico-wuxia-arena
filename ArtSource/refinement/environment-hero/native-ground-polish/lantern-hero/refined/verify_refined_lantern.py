"""Verify refined module quality constraints against the formal bd5d wet-stone scene."""
from pathlib import Path
import hashlib,json,sys,unittest
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
SOURCE=ROOT/'app/src/main/assets/models/courtyard_hero.glb';MODULE=HERE/'lantern_refined_module.glb';EXPECTED='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667'
sys.path[:0]=[str(ROOT/'ArtSource/refinement/environment-hero'),str(ROOT/'ArtSource/refinement/environment-hero/facade-polish')]
from verify_environment import read,rows,active_nodes
from build_facade import budget
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def triangles(d,b,p):return rows(d,b,p['indices']).reshape(-1,3)
def count_module(d):return sum(d['accessors'][p['indices']]['count']//3 for m in d['meshes'] for p in m['primitives'])
def old_front(d,b):
    total=0;parts={}
    for mi,pi,name in [(6,0,'wood'),(6,1,'bronze'),(7,0,'paper')]:
        p=d['meshes'][mi]['primitives'][pi];v=rows(d,b,p['attributes']['POSITION']);ix=triangles(d,b,p);mask=np.zeros(len(ix),bool)
        for x in [-2.15,2.15]:
            q=v[ix];mask|=np.all(abs(q[:,:,0]-x)<.29,1)&np.all((q[:,:,1]>2.06)&(q[:,:,1]<3.46),1)&np.all((q[:,:,2]>-5.05)&(q[:,:,2]<-4.51),1)
        parts[name]=int(mask.sum());total+=parts[name]
    return parts,total
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.sd,c.sb=read(SOURCE);c.d,c.b=read(MODULE);c.m=json.loads((HERE/'module_manifest.json').read_text())
 def test_identity_and_source_contract(self):
  self.assertEqual(sha(SOURCE),EXPECTED);self.assertEqual(self.m['formal_source_sha256'],EXPECTED);self.assertEqual(self.m['module_sha256'],sha(MODULE));self.assertEqual(self.m['paper_segments'],48);self.assertEqual(self.m['ribs'],12);self.assertTrue(self.m['ribs_are_continuous'])
 def test_existing_materials_and_no_runtime_content(self):
  names=[m['name'] for m in self.d['materials']];self.assertEqual(set(names),{'EH S2 Lantern | graded paper emission','EH Timber | aged grain','EH Fittings | aged bronze','Rope | twisted hemp'});self.assertEqual(self.m['source_materials'],{'paper':10,'wood':0,'bronze':7,'rope':24});self.assertFalse(self.d.get('cameras'));self.assertFalse(self.d.get('animations'));self.assertNotIn('KHR_lights_punctual',self.d.get('extensions',{}))
 def test_smooth_geometry_uv_and_tangents(self):
  self.assertEqual(len(active_nodes(self.d)),len(self.d['nodes']));self.assertGreater(count_module(self.d),2500)
  for mesh in self.d['meshes']:
   for p in mesh['primitives']:
    a=p['attributes'];v=rows(self.d,self.b,a['POSITION']);ix=triangles(self.d,self.b,p);self.assertTrue(np.isfinite(v).all());self.assertIn('TEXCOORD_0',a);self.assertIn('NORMAL',a);q=v[ix].astype(float);self.assertTrue(np.all(np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)>1e-10));mat=self.d['materials'][p['material']]
    if 'normalTexture' in mat:self.assertIn('TANGENT',a)
 def test_envelope_instances_budget_and_anchors(self):
  lo=np.array(self.m['module_bounds_stage_local_m']['min']);hi=np.array(self.m['module_bounds_stage_local_m']['max']);self.assertTrue(np.all(lo>=[-.29,-.64,-.29]));self.assertTrue(np.all(hi<=[.29,.76,.29]));self.assertEqual(self.m['instances'][0]['translation_stage_m'],[-2.15,2.70,-4.78]);self.assertEqual(self.m['instances'][1]['translation_stage_m'],[2.15,2.70,-4.78])
  old,total=old_front(self.sd,self.sb);new=count_module(self.d)*2;self.assertLessEqual(new-total,6000);self.assertLessEqual(budget(self.sd,self.sb)['node_expanded_triangles']+new-total,250000);self.assertGreater(old['paper'],900);self.assertTrue({'EH_Light_Lantern_01','EH_Light_Lantern_02'}.issubset({n['name'] for n in self.sd['nodes']}))
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));old,total=old_front(Checks.sd,Checks.sb);module=count_module(Checks.d);base=budget(Checks.sd,Checks.sb);out={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'formal_source_sha256':sha(SOURCE),'module_sha256':sha(MODULE),'module_triangles':module,'two_instance_triangles':module*2,'removed_old_triangles':old,'net_expanded_triangles':module*2-total,'preview_expanded_triangle_budget':base['node_expanded_triangles']+module*2-total,'formal_budget':base,'scope':'Module plus planned composition invariants; native KTX lighting/load and actual composition are unverified.'};(HERE/'review/verification.json').write_text(json.dumps(out,indent=2)+'\n');raise SystemExit(0 if result.wasSuccessful() else 1)
