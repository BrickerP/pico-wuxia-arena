"""Validate actual delivered GLB, including clearance and roof winding."""
import hashlib
import json
from pathlib import Path
import struct
import unittest

import numpy as np

HERE = Path(__file__).resolve().parent

def read(path):
    data=path.read_bytes()
    if data[:4]!=b'glTF' or struct.unpack_from('<I',data,8)[0]!=len(data):
        raise ValueError('Not a complete GLB')
    length=struct.unpack_from('<I',data,12)[0]
    document=json.loads(data[20:20+length])
    binary=data[28+length:]
    return document,binary

def rows(doc,blob,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
    count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    stride=v.get('byteStride',np.dtype(dtype).itemsize*count)
    return np.ndarray((a['count'],count),dtype=dtype,buffer=blob,offset=start,
                      strides=(stride,np.dtype(dtype).itemsize)).copy()

def local_matrix(node):
    if 'matrix' in node:return np.array(node['matrix']).reshape(4,4).T
    x,y,z,w=node.get('rotation',[0,0,0,1])
    m=np.eye(4)
    m[:3,:3]=[[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],
               [2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],
               [2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]]
    m[:3,:3]=m[:3,:3]@np.diag(node.get('scale',[1,1,1]))
    m[:3,3]=node.get('translation',[0,0,0])
    return m

def active_nodes(doc):
    active={}
    def walk(index,parent):
        if index in active:raise ValueError('Shared/cyclic node graph')
        frame=parent@local_matrix(doc['nodes'][index]);active[index]=frame
        for child in doc['nodes'][index].get('children',[]):walk(child,frame)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']:walk(index,np.eye(4))
    return active

def world_primitives(doc,blob):
    for index,frame in active_nodes(doc).items():
        node=doc['nodes'][index]
        if 'mesh' not in node:continue
        for p in doc['meshes'][node['mesh']]['primitives']:
            v=rows(doc,blob,p['attributes']['POSITION'])
            v=(np.column_stack((v,np.ones(len(v))))@frame.T)[:,:3]
            indices=rows(doc,blob,p['indices']).reshape(-1,3)
            yield node['name'],p,v,indices

class CandidateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=HERE/'courtyard_hero.glb'
        cls.doc,cls.blob=read(cls.path)
        cls.primitives=list(world_primitives(cls.doc,cls.blob))
        cls.manifest=json.loads((HERE/'candidate_manifest.json').read_text())

    def test_complete_identity_and_no_orphan_nodes(self):
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),self.manifest['sha256'])
        self.assertEqual(len(active_nodes(self.doc)),len(self.doc['nodes']))
        roots=self.doc['scenes'][self.doc.get('scene',0)]['nodes']
        self.assertEqual(len(roots),1)
        self.assertEqual(self.doc['nodes'][roots[0]]['name'],'EnvironmentHero_Root')
        np.testing.assert_allclose(local_matrix(self.doc['nodes'][roots[0]]),np.eye(4),atol=1e-7)

    def test_ground_top_is_zero_and_covers_combat_rectangle(self):
        ground=np.concatenate([v for name,p,v,i in self.primitives if name=='EH_GroundReceiver'])
        self.assertAlmostEqual(float(ground[:,1].max()),0,places=6)
        self.assertLessEqual(float(ground[:,0].min()),-1.35)
        self.assertGreaterEqual(float(ground[:,0].max()),1.35)
        self.assertLessEqual(float(ground[:,2].min()),-3)
        self.assertGreaterEqual(float(ground[:,2].max()),.8)

    def test_combat_volume_has_no_decoration_triangles(self):
        lo,hi=np.array([-1.35,.05,-3.0]),np.array([1.35,2.4,.8])
        intruders=[]
        for name,p,v,i in self.primitives:
            tris=v[i];tlo,tmax=tris.min(axis=1),tris.max(axis=1)
            intersects=np.all(tmax>lo,axis=1)&np.all(tlo<hi,axis=1)
            if intersects.any():intruders.append(name)
        self.assertEqual(intruders,[])

    def test_roof_rolled_caps_point_outward(self):
        for name,p,v,i in self.primitives:
            if 'Roof' not in name and 'Eave' not in name:continue
            mat=self.doc['materials'][p['material']]['name']
            if mat!='EH Roof | rolled tile caps':continue
            t=v[i];vertical=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0])[:,1].sum()
            self.assertGreater(float(vertical),0,name)

    def test_materials_and_textures_survive_export(self):
        for name,p,v,i in self.primitives:
            self.assertEqual(p.get('mode',4),4)
            self.assertTrue(np.isfinite(v).all(),name)
            self.assertIn('NORMAL',p['attributes'],name)
            self.assertIn('TEXCOORD_0',p['attributes'],name)
        for im in self.doc['images']:
            self.assertIn('bufferView',im)
            self.assertNotIn('uri',im)
        for material in self.doc['materials']:
            if material['name'].startswith(('EH Roof | fired','EH Stone','EH Timber | aged','EH Wall')):
                self.assertIn('normalTexture',material,material['name'])
                self.assertIn('metallicRoughnessTexture',material['pbrMetallicRoughness'],material['name'])

    def test_no_runtime_lights_cameras_or_animations_are_bundled(self):
        self.assertFalse(self.doc.get('cameras'))
        self.assertFalse(self.doc.get('animations'))
        self.assertNotIn('KHR_lights_punctual',self.doc.get('extensions',{}))
        names={n['name'] for n in self.doc['nodes']}
        self.assertTrue(set(self.manifest['ground_receivers']).issubset(names))
        self.assertTrue(set(self.manifest['anchors']).issubset(names))

    def test_partial_glb_is_rejected(self):
        # Exercise the failure path against a genuine truncated deliverable.
        path=HERE/'review'/'invalid_partial_glb.fixture'
        path.write_bytes(self.path.read_bytes()[:100])
        try:
            with self.assertRaises(ValueError):read(path)
        finally:path.unlink()

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CandidateChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    d,b=read(HERE/'courtyard_hero.glb')
    report={'status':'passed' if result.wasSuccessful() else 'failed',
      'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
      'sha256':hashlib.sha256((HERE/'courtyard_hero.glb').read_bytes()).hexdigest(),
      'active_nodes':len(active_nodes(d)),'meshes':len(d['meshes']),
      'materials':len(d['materials']),'embedded_images':len(d['images']),
      'triangles':sum(len(i) for n,p,v,i in world_primitives(d,b)),
      'scope':'GLB structure/geometry invariants; not headset performance or VR feel'}
    (HERE/'review'/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
