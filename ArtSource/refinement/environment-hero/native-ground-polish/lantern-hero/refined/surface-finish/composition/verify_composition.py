"""Full private composition invariants, including normal and negative input guards."""
from pathlib import Path
import hashlib,json,sys,unittest
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[7]
FORMAL=ROOT/'app/src/main/assets/models/courtyard_hero.glb';PNG=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';KTX=HERE/'courtyard_lantern_surface_ktx.glb';OUT=HERE/'courtyard_lantern_surface_png.glb';FORMAL_SHA='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667';PNG_SHA='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392';FIBER=HERE.parent/'textures/paper_fiber_1024x512.png'
sys.path[:0]=[str(ROOT/'ArtSource/refinement/environment-hero'),str(ROOT/'ArtSource/refinement/environment-hero/facade-polish'),str(ROOT/'ArtSource/refinement/pbr-compression')]
from verify_environment import read,rows,active_nodes
from build_facade import budget
import compress_pbr as pbr
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def view(d,b,i):
 v=d['bufferViews'][i];o=v.get('byteOffset',0);return bytes(b[o:o+v['byteLength']])
def image(d,b,i):return view(d,b,d['images'][i]['bufferView'])
def tris(d,b,p):return rows(d,b,p['indices']).reshape(-1,3)
def require_input(actual,expected):
 if actual!=expected:raise ValueError('frozen input identity mismatch')
class Checks(unittest.TestCase):
 @classmethod
 def setUpClass(c):c.fd,c.fb=read(FORMAL);c.pd,c.pb=read(PNG);c.kd,c.kb=read(KTX);c.od,c.ob=read(OUT);c.m=json.loads((HERE/'composition_manifest.json').read_text())
 def test_normal_and_negative_input_guards(self):
  self.assertEqual(sha(FORMAL),FORMAL_SHA);self.assertEqual(sha(PNG),PNG_SHA);require_input(sha(FORMAL),FORMAL_SHA)
  with self.assertRaises(ValueError):require_input('wrong',FORMAL_SHA)
  with self.assertRaises(ValueError):require_input(FORMAL_SHA,'wrong')
 def test_material_texture_image_contract(self):
  for source,d,b,mode in [(self.fd,self.kd,self.kb,'ktx'),(self.pd,self.od,self.ob,'png')]:
   self.assertEqual(len(d['materials']),32);self.assertEqual(len(d['images']),50);expected_textures=json.loads(json.dumps(source['textures']))
   if mode=='ktx':expected_textures[41]['extensions']={'KHR_texture_basisu':{'source':expected_textures[41].pop('source')}}
   self.assertEqual(d['textures'],expected_textures);self.assertEqual(d['samplers'],source['samplers'])
   for i,(a,z) in enumerate(zip(source['materials'],d['materials'])):
    if i==10:
     expected=json.loads(json.dumps(a));expected['pbrMetallicRoughness']['baseColorTexture']['index']=41;expected['emissiveTexture']['index']=41;self.assertEqual(z,expected)
    else:self.assertEqual(z,a)
   for i in range(50):
    if i==41:continue
    self.assertEqual(image(source,self.fb if mode=='ktx' else self.pb,i),image(d,b,i),i)
  self.assertEqual(image(self.od,self.ob,41),FIBER.read_bytes());pbr.check_ktx(image(self.kd,self.kb,41),'srgb',(1024,512))
 def test_non_targets_and_node_transforms_preserved(self):
  for source,d,b in [(self.fd,self.kd,self.kb),(self.pd,self.od,self.ob)]:
   for mi,m in enumerate(source['meshes']):
    if mi in {6,7}:continue
    self.assertEqual(d['meshes'][mi],m)
   for ni,n in enumerate(source['nodes']):
    if ni==source['scenes'][source.get('scene',0)]['nodes'][0]:continue
    self.assertEqual(d['nodes'][ni],n)
   self.assertEqual(len(active_nodes(d)),len(d['nodes']))
 def test_exact_removal_addition_and_budget(self):
  for d,b in [(self.kd,self.kb),(self.od,self.ob)]:
   self.assertEqual(len(d['meshes']),41);self.assertEqual(len(d['nodes']),64);self.assertEqual(budget(d,b)['node_expanded_triangles'],249958);self.assertLessEqual(budget(d,b)['node_expanded_triangles'],250000)
   # original target primitive indices shrink by the audited amounts
   self.assertEqual(len(tris(self.fd if d is self.kd else self.pd,self.fb if d is self.kd else self.pb,(self.fd if d is self.kd else self.pd)['meshes'][6]['primitives'][0]))-len(tris(d,b,d['meshes'][6]['primitives'][0]),),2936)
   self.assertEqual(len(tris(self.fd if d is self.kd else self.pd,self.fb if d is self.kd else self.pb,(self.fd if d is self.kd else self.pd)['meshes'][6]['primitives'][1]))-len(tris(d,b,d['meshes'][6]['primitives'][1]),),504)
   self.assertEqual(len(tris(self.fd if d is self.kd else self.pd,self.fb if d is self.kd else self.pb,(self.fd if d is self.kd else self.pd)['meshes'][7]['primitives'][0]))-len(tris(d,b,d['meshes'][7]['primitives'][0]),),960)
 def test_new_module_geometry_is_valid_and_lights_not_added(self):
  for d,b in [(self.kd,self.kb),(self.od,self.ob)]:
   for mesh in d['meshes'][37:]:
    for p in mesh['primitives']:
     a=p['attributes'];v=rows(d,b,a['POSITION']);ix=tris(d,b,p);self.assertTrue(np.isfinite(v).all());self.assertIn('NORMAL',a);self.assertIn('TEXCOORD_0',a);self.assertIn('TANGENT',a);q=v[ix].astype(float);self.assertTrue(np.all(np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)>1e-10))
   self.assertNotIn('KHR_lights_punctual',d.get('extensions',{}));self.assertFalse(d.get('cameras'));self.assertFalse(d.get('animations'))
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));out={'status':'passed' if r.wasSuccessful() else 'failed','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'formal_sha256':sha(FORMAL),'png_candidate_sha256':sha(OUT),'ktx_candidate_sha256':sha(KTX),'budget':budget(Checks.kd,Checks.kb),'scope':'Full private composition structural contract, not native KTX/device/light/performance proof.'};(HERE/'review/verification.json').write_text(json.dumps(out,indent=2)+'\n');raise SystemExit(0 if r.wasSuccessful() else 1)
