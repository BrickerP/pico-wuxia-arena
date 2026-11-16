"""Verify the image-only material candidate and the two permitted generated maps."""
from pathlib import Path
from io import BytesIO
import copy
import hashlib
import json
import sys
import unittest

import numpy as np
from PIL import Image

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
SOURCE=ROOT/'ArtSource/refinement/environment-hero/native-fight-entrance/courtyard_native_entrance.glb';PNG=HERE/'courtyard_wet_stone_png.glb';KTX=HERE/'courtyard_wet_stone_ktx.glb'
EXPECTED='96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d'
sys.path[:0]=[str(ROOT/'ArtSource/refinement/environment-hero'),str(ROOT/'ArtSource/refinement/environment-hero/facade-polish'),str(ROOT/'ArtSource/refinement/pbr-compression')]
from verify_environment import read,active_nodes
from build_facade import budget
import compress_pbr as pbr

BASE_IMAGE=10;MR_IMAGE=11;NORMAL_IMAGE=9;BASE_TEX=10;MR_TEX=11;MAT=8
def sha(v):return hashlib.sha256(v.read_bytes() if isinstance(v,Path) else v).hexdigest()
def view(doc,blob,index):
    v=doc['bufferViews'][index];o=v.get('byteOffset',0);return bytes(blob[o:o+v['byteLength']])
def image(doc,blob,index):return view(doc,blob,doc['images'][index]['bufferView'])
def scrub(doc,kind):
    d=copy.deepcopy(doc);d['buffers'][0].pop('byteLength',None)
    for v in d['bufferViews']:v.pop('byteOffset',None)
    for index in [BASE_IMAGE,MR_IMAGE]:
        d['images'][index].pop('mimeType',None);d['bufferViews'][d['images'][index]['bufferView']].pop('byteLength',None)
    if kind=='ktx':
        for index in [BASE_TEX,MR_TEX]:
            d['textures'][index]['source']=d['textures'][index]['extensions'].pop('KHR_texture_basisu')['source']
            d['textures'][index].pop('extensions')
        d.pop('extensionsUsed');d.pop('extensionsRequired')
    return d

class WetStone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sd,cls.sb=read(SOURCE);cls.pd,cls.pb=read(PNG);cls.kd,cls.kb=read(KTX)
        cls.provenance=json.loads((HERE/'texture_provenance.json').read_text())
    def test_source_identity_and_scene_identity(self):
        self.assertEqual(sha(SOURCE),EXPECTED)
        self.assertEqual(self.provenance['input']['path'],str(SOURCE.relative_to(ROOT)))
        self.assertEqual(self.provenance['build_execution']['script_sha256'],sha(HERE/'build_wet_stone.py'))
        for d in [self.pd,self.kd]:
            self.assertEqual(d['scenes'],self.sd['scenes']);self.assertEqual(d['nodes'],self.sd['nodes']);self.assertEqual(d['meshes'],self.sd['meshes'])
            self.assertEqual(len(active_nodes(d)),len(d['nodes']))
            self.assertEqual(len(d['materials']),32);self.assertEqual(len(d['images']),50);self.assertEqual(len(d['textures']),50)
            self.assertEqual(budget(d,self.pb if d is self.pd else self.kb),budget(self.sd,self.sb))
    def test_only_two_image_payloads_and_texture_bindings_change(self):
        for d,b,kind in [(self.pd,self.pb,'png'),(self.kd,self.kb,'ktx')]:
            self.assertEqual(scrub(self.sd,'source'),scrub(d,kind))
            for i in range(50):
                if i not in {BASE_IMAGE,MR_IMAGE}:self.assertEqual(image(self.sd,self.sb,i),image(d,b,i),i)
            self.assertEqual(d['materials'][MAT],self.sd['materials'][MAT])
            self.assertEqual(image(d,b,NORMAL_IMAGE),image(self.sd,self.sb,NORMAL_IMAGE))
        self.assertEqual(self.pd['images'][BASE_IMAGE]['mimeType'],'image/png')
        self.assertEqual(self.kd['images'][BASE_IMAGE]['mimeType'],'image/ktx2')
        self.assertEqual(set(self.kd['textures'][BASE_TEX]['extensions']),{'KHR_texture_basisu'})
        self.assertNotIn('source',self.kd['textures'][BASE_TEX])
        self.assertEqual(self.kd['extensionsRequired'],['KHR_texture_basisu'])
    def test_two_maps_are_1024_nonuniform_and_neutral(self):
        color=Image.open(HERE/'textures/wet_stone_basecolor_1024.png').convert('RGB');mr=Image.open(HERE/'textures/wet_stone_metallic_roughness_1024.png').convert('RGB')
        self.assertEqual(color.size,(1024,1024));self.assertEqual(mr.size,(1024,1024))
        c=np.asarray(color,dtype=float)/255.;m_uint=np.asarray(mr);m=m_uint.astype(float)/255.
        original=np.asarray(Image.open(BytesIO(image(self.sd,self.sb,BASE_IMAGE))).convert('RGB').resize((1024,1024),Image.Resampling.LANCZOS),dtype=float)/255.
        self.assertGreater(float(np.std(c-original)),.009);self.assertGreater(float(m[:,:,1].std()),.025)
        self.assertLess(float(np.abs(c[:,:,1]-c.mean(axis=2)).mean()),.075) # no green albedo cast
        self.assertGreaterEqual(float(m[:,:,1].min()),.18);self.assertLess(float(m[:,:,1].mean()),.48)
        self.assertTrue(np.array_equal(m_uint[:,:,0],np.asarray(Image.open(BytesIO(image(self.pd,self.pb,MR_IMAGE))).convert('RGB'))[:,:,0]))
        self.assertTrue(np.array_equal(m_uint[:,:,2],np.asarray(Image.open(BytesIO(image(self.pd,self.pb,MR_IMAGE))).convert('RGB'))[:,:,2]))
    def test_ktx_headers_and_official_records(self):
        for i,domain in [(BASE_IMAGE,'srgb'),(MR_IMAGE,'linear')]:
            data=image(self.kd,self.kb,i);header=pbr.check_ktx(data,domain,(1024,1024))
            self.assertEqual(header['levels'],11)
        images={r['image']:r for r in self.provenance['compression'].values() if isinstance(r,dict) and 'image' in r}
        self.assertEqual(set(images),{BASE_IMAGE,MR_IMAGE})
        for record in images.values():
            self.assertGreaterEqual(len(record['mip_inputs']),1);self.assertEqual(record['ktx2']['levels'],11)
    def test_no_runtime_side_effects_or_budget_change(self):
        for d in [self.pd,self.kd]:
            self.assertFalse(d.get('cameras'));self.assertFalse(d.get('animations'));self.assertNotIn('KHR_lights_punctual',d.get('extensions',{}))
            self.assertEqual(d['materials'][MAT]['name'],'EH Stone | walked granite')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(WetStone))
    report={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'source_sha256':sha(SOURCE),'png_candidate_sha256':sha(PNG),'ktx_candidate_sha256':sha(KTX),'budget':budget(WetStone.kd,WetStone.kb),'execution':{'script':str(Path(__file__).resolve().relative_to(ROOT)),'script_sha256':sha(Path(__file__)),'input':str(SOURCE.relative_to(ROOT))},'scope':'Image-only GLB, KTX and source-provenance checks. No native PICO material, lighting, collision or performance proof.'}
    (HERE/'review/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
