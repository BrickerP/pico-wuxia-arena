"""Check frozen source preservation, local material changes and stage2 GLB."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE))
from verify_environment import read,rows,active_nodes,world_primitives
sys.path.insert(0,str(HERE))
from create_candidate import EXPECTED,SOURCE,components,assert_frozen

class Stage2Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=HERE/'courtyard_materials_stage2.glb'
        cls.doc,cls.blob=read(cls.path);cls.old,cls.oldblob=read(SOURCE)
        cls.manifest=json.loads((HERE/'candidate_manifest.json').read_text())
        cls.parts=list(world_primitives(cls.doc,cls.blob))

    def test_frozen_source_app_producer_and_all_input_maps_unchanged(self):
        for p in [SOURCE,ROOT/'app/src/main/assets/models/courtyard_hero.glb']:
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),EXPECTED,str(p))
        self.assertEqual(hashlib.sha256((BASE/'build_environment.py').read_bytes()).hexdigest(),
                         '14f77c3292d95abe27f95dd2775455dea1850755fad515899dd0cf38d13971b1')
        m=json.loads((BASE/'texture_manifest.json').read_text())
        for name,digest in m['maps'].items():
            self.assertEqual(hashlib.sha256((BASE/'textures'/name).read_bytes()).hexdigest(),digest,name)

    def test_identity_and_original_binary_prefix_are_exact(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),self.manifest['sha256'])
        length=self.old['buffers'][0]['byteLength']
        self.assertEqual(self.blob[:length],self.oldblob[:length])
        self.assertEqual(len(active_nodes(self.doc)),len(self.doc['nodes']))
        self.assertEqual(self.doc['scenes'],self.old['scenes'])
        self.assertEqual(len(self.doc['nodes']),len(self.old['nodes'])+1)

    def test_all_existing_node_transforms_geometry_and_anchors_are_preserved(self):
        for index,n in enumerate(self.old['nodes']):
            new=copy.deepcopy(self.doc['nodes'][index]);old=copy.deepcopy(n)
            if index==self.old['scenes'][self.old.get('scene',0)]['nodes'][0]:
                self.assertEqual(new.pop('children')[:-1],old.pop('children'))
            self.assertEqual(new,old,n['name'])
        for mi,mesh in enumerate(self.old['meshes']):
            for pi,p in enumerate(mesh['primitives']):
                new=self.doc['meshes'][mi]['primitives'][pi]
                for attr in ['POSITION','NORMAL']:
                    self.assertEqual(new['attributes'][attr],p['attributes'][attr])
                self.assertEqual(new['indices'],p['indices'])
        self.assertEqual(self.doc['materials'][3],self.old['materials'][3])

    def test_receiver_and_clearance_contract(self):
        ground=np.concatenate([v for n,p,v,i in self.parts if n=='EH_GroundReceiver'])
        self.assertAlmostEqual(float(ground[:,1].max()),0,places=6)
        lo,hi=np.array([-1.35,.05,-3]),np.array([1.35,2.4,.8])
        for n,p,v,i in self.parts:
            t=v[i];overlap=np.all(t.max(axis=1)>lo,axis=1)&np.all(t.min(axis=1)<hi,axis=1)
            self.assertFalse(overlap.any(),n)
        names={n['name'] for n in self.doc['nodes']}
        self.assertTrue(set(self.manifest['ground_receivers']).issubset(names))

    def test_paper_atlas_has_23_separate_metre_scaled_sheets(self):
        sheets=self.manifest['paper_sheets'];self.assertEqual(len(sheets),23)
        self.assertEqual({s['atlas_tile'] for s in sheets},{0,1,2,3})
        for sheet in sheets:
            width,height=sheet['paper_width_height_m']
            self.assertTrue(.4<width<1.6,(width,height))
            self.assertTrue(.4<height<1.8,(width,height))
            uv=np.array(sheet['uv_bounds'])
            self.assertTrue((uv>0).all() and (uv<1).all())
            np.testing.assert_allclose(uv[1]-uv[0],[1007/2048]*2,atol=1e-6)
        for mi,mesh in enumerate(self.doc['meshes']):
            for p in mesh['primitives']:
                name=self.doc['materials'][p['material']]['name']
                if not name.startswith('EH S2 Windows'):continue
                pos=rows(self.doc,self.blob,p['attributes']['POSITION'])
                uv=rows(self.doc,self.blob,p['attributes']['TEXCOORD_0'])
                inds=rows(self.doc,self.blob,p['indices']).reshape(-1,3)
                for group in components(pos,inds):
                    # glTF PNG V runs down while SDK height runs up.
                    self.assertLess(np.corrcoef(pos[group,1],uv[group,1])[0,1],-.999)

    def test_added_tangents_are_valid_for_normal_maps(self):
        for mesh in self.doc['meshes']:
            for p in mesh['primitives']:
                material=self.doc['materials'][p['material']]
                if not material['name'].startswith('EH S2') and mesh['name']!='EH_S2_TimberJointFaces_Mesh':continue
                if 'normalTexture' not in material:continue
                n=rows(self.doc,self.blob,p['attributes']['NORMAL'])
                t=rows(self.doc,self.blob,p['attributes']['TANGENT'])
                self.assertTrue(np.isfinite(t).all())
                np.testing.assert_allclose(np.linalg.norm(t[:,:3],axis=1),1,atol=2e-5)
                np.testing.assert_allclose(np.sum(t[:,:3]*n,axis=1),0,atol=2e-5)
                self.assertTrue(np.isin(t[:,3],[-1,1]).all())

    def test_emission_is_portable_opaque_and_distant_values_are_subdued(self):
        for i in [4,10,len(self.doc['materials'])-3]:
            m=self.doc['materials'][i]
            self.assertIn('emissiveTexture',m)
            self.assertTrue(all(0<x<=1 for x in m['emissiveFactor']))
            self.assertEqual(m.get('alphaMode','OPAQUE'),'OPAQUE')
            self.assertNotIn('KHR_materials_transmission',m.get('extensions',{}))
            self.assertIn('normalTexture',m)
            self.assertIn('metallicRoughnessTexture',m['pbrMetallicRoughness'])
        self.assertLess(sum(self.doc['materials'][-3]['emissiveFactor']),sum(self.doc['materials'][4]['emissiveFactor']))
        for image in self.doc['images']:
            self.assertIn('bufferView',image);self.assertNotIn('uri',image)
        self.assertNotIn('KHR_lights_punctual',self.doc.get('extensions',{}))

    def test_small_structure_addition_and_no_window_lattice_growth(self):
        old_tris=sum(len(i) for n,p,v,i in world_primitives(self.old,self.oldblob))
        new_tris=sum(len(i) for n,p,v,i in self.parts)
        self.assertTrue(0<new_tris-old_tris<2500,new_tris-old_tris)
        self.assertEqual(len(self.manifest['added_joinery']),33)
        self.assertEqual(len(self.doc['meshes']),len(self.old['meshes'])+1)
        for mi in [4,16]:
            self.assertEqual(len(self.doc['meshes'][mi]['primitives']),len(self.old['meshes'][mi]['primitives']))

    def test_texture_variation_and_lantern_horizontal_seam(self):
        for name in ['paper_atlas_emissive.png','lantern_emissive.png']:
            rgb=np.asarray(Image.open(HERE/'textures'/name).convert('RGB'),dtype=float)/255
            self.assertGreater(float(rgb.std()),.04,name)
        for name in ['lantern_basecolor.png','lantern_normal.png','lantern_roughness.png','lantern_emissive.png']:
            a=np.asarray(Image.open(HERE/'textures'/name));np.testing.assert_array_equal(a[:,0],a[:,-1])

    def test_missing_or_wrong_frozen_source_is_rejected(self):
        # Exercise the actual producer guard, including a missing input path.
        with tempfile.TemporaryDirectory(dir=HERE/'review') as directory:
            path=Path(directory)/'wrong.glb';path.write_bytes(b'not the frozen model')
            with self.assertRaises(ValueError):assert_frozen(path)
            with self.assertRaises(FileNotFoundError):assert_frozen(Path(directory)/'missing.glb')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Stage2Checks))
    d,b=read(HERE/'courtyard_materials_stage2.glb')
    report={'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,
       'failures':len(result.failures),'errors':len(result.errors),
       'sha256':hashlib.sha256((HERE/'courtyard_materials_stage2.glb').read_bytes()).hexdigest(),
       'nodes':len(d['nodes']),'meshes':len(d['meshes']),'materials':len(d['materials']),
       'embedded_images':len(d['images']),'triangles':sum(len(i) for n,p,v,i in world_primitives(d,b)),
       'scope':'actual GLB and frozen input invariants; not native brightness/performance proof'}
    (HERE/'review'/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
