"""Verify smooth paper normals, one fiber texture and planned two-instance budget."""
from pathlib import Path
import hashlib,json,sys,unittest
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[6]
FORMAL=ROOT/'app/src/main/assets/models/courtyard_hero.glb';PNG=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';MODULE=HERE/'lantern_surface_module.glb';FORMAL_SHA='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667';PNG_SHA='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392'
sys.path[:0]=[str(ROOT/'ArtSource/refinement/environment-hero'),str(ROOT/'ArtSource/refinement/environment-hero/facade-polish')]
from verify_environment import read,rows,active_nodes
from build_facade import budget
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def tri(d,b,p):return rows(d,b,p['indices']).reshape(-1,3)
def count(d):return sum(d['accessors'][p['indices']]['count']//3 for m in d['meshes'] for p in m['primitives'])
def removed(d,b):
 total=0
 for mi,pi in [(6,0),(6,1),(7,0)]:
  p=d['meshes'][mi]['primitives'][pi];v=rows(d,b,p['attributes']['POSITION']);ix=tri(d,b,p);mask=np.zeros(len(ix),bool)
  for x in [-2.15,2.15]:
   q=v[ix];mask|=np.all(abs(q[:,:,0]-x)<.29,1)&np.all((q[:,:,1]>2.06)&(q[:,:,1]<3.46),1)&np.all((q[:,:,2]>-5.05)&(q[:,:,2]<-4.51),1)
  total+=int(mask.sum())
 return total
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.fd,c.fb=read(FORMAL);c.d,c.b=read(MODULE);c.m=json.loads((HERE/'module_manifest.json').read_text());c.f=json.loads((HERE/'fiber_provenance.json').read_text())
 def test_identity_contract_and_one_fiber_map(self):
  self.assertEqual(sha(FORMAL),FORMAL_SHA);self.assertEqual(sha(PNG),PNG_SHA);self.assertEqual(self.m['formal_source_sha256'],FORMAL_SHA);self.assertEqual(self.m['blender_png_equivalent_sha256'],PNG_SHA);self.assertEqual(self.m['module_sha256'],sha(MODULE));self.assertEqual(self.m['paper_segments'],48);self.assertEqual(self.m['longitudinal_rings'],17);self.assertTrue(self.m['paper_smooth_normals']);self.assertEqual(self.f['output']['size'],[1024,512]);self.assertEqual(self.f['output']['sha256'],sha(HERE/'textures/paper_fiber_1024x512.png'))
 def test_paper_smooth_normals_uv_tangents_and_finite_geometry(self):
  self.assertEqual(len(active_nodes(self.d)),len(self.d['nodes']));paper=None
  for mesh in self.d['meshes']:
   for p in mesh['primitives']:
    a=p['attributes'];v=rows(self.d,self.b,a['POSITION']);n=rows(self.d,self.b,a['NORMAL']);ix=tri(self.d,self.b,p);self.assertTrue(np.isfinite(v).all());self.assertTrue(np.isfinite(n).all());self.assertIn('TEXCOORD_0',a);q=v[ix].astype(float);self.assertTrue(np.all(np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)>1e-10));mat=self.d['materials'][p['material']]
    if 'normalTexture' in mat:self.assertIn('TANGENT',a)
    if 'surface finish preview' in mat['name']:paper=(v,n)
  self.assertIsNotNone(paper);v,n=paper;radius=np.linalg.norm(v[:,[0,2]],axis=1);mask=radius>.1;radial=np.column_stack((v[mask,0],np.zeros(mask.sum()),v[mask,2]));radial/=np.linalg.norm(radial,axis=1,keepdims=True);self.assertGreater(float(np.median(np.sum(radial*n[mask],axis=1))),.85);self.assertGreater(len(np.unique(np.round(n[mask],4),axis=0)),40)
 def test_existing_material_mapping_and_budget(self):
  names=[m['name'] for m in self.d['materials']];self.assertIn('EH S2 Lantern | graded paper emission | surface finish preview',names);self.assertEqual(self.m['source_materials'],{'paper_target_material':10,'wood':0,'bronze':7,'rope':24});self.assertEqual(self.m['one_new_image']['source_image_to_replace'],41);self.assertEqual(len(self.fd['materials']),32);self.assertEqual(len(self.fd['images']),50)
  module=count(self.d);old=removed(self.fd,self.fb);planned=budget(self.fd,self.fb)['node_expanded_triangles']+module*2-old;self.assertLessEqual(planned,250000);self.assertEqual(module,5500);self.assertFalse(self.d.get('cameras'));self.assertFalse(self.d.get('animations'))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));module=count(Checks.d);old=removed(Checks.fd,Checks.fb);base=budget(Checks.fd,Checks.fb);out={'status':'passed' if r.wasSuccessful() else 'failed','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'formal_source_sha256':sha(FORMAL),'module_sha256':sha(MODULE),'module_triangles':module,'two_instance_triangles':module*2,'removed_old_triangles':old,'net_expanded_triangles':module*2-old,'planned_expanded_triangle_budget':base['node_expanded_triangles']+module*2-old,'formal_budget':base,'scope':'Surface module and planned composition checks; not actual KTX composition/native lighting/device proof.'};(HERE/'review/verification.json').write_text(json.dumps(out,indent=2)+'\n');raise SystemExit(0 if r.wasSuccessful() else 1)
