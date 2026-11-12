"""Validate sharing, kept scene contracts and construction of the facade asset."""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE));from verify_environment import read,rows,active_nodes,world_primitives
sys.path.insert(0,str(BASE/'method-study-2026-11-12'));from verify_sample import ray
sys.path.insert(0,str(HERE));from build_facade import GROUND,UPPER,budget
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    m=json.loads((HERE/'candidate_manifest.json').read_text());source=BASE/'single-window-integration-2026-11-12/courtyard_one_window.glb'
    target=HERE/m['candidate'];assert sha(source)==m['source_sha256'];assert sha(target)==m['sha256']
    old,ob=read(source);d,b=read(target);length=old['buffers'][0]['byteLength'];assert ob[:length]==b[:length]
    for key in ['materials','images','textures','samplers']:assert d[key]==old[key],key
    for key in ['accessors','bufferViews']:assert d[key][:len(old[key])]==old[key],key
    assert d['scenes']==old['scenes'];assert len(active_nodes(d))==len(d['nodes'])
    for i,n in enumerate(old['nodes']):
        a=copy.deepcopy(n);c=copy.deepcopy(d['nodes'][i])
        if i in [37,40]:assert c.pop('children')[:len(a['children'])]==a.pop('children')
        assert a==c,n.get('name')
    allowed={(4,i) for i in range(4)}|{(23,0),(20,1)}
    for mi,mesh in enumerate(old['meshes']):
        if mi==31:
            assert d['meshes'][31]['primitives']==mesh['primitives'][:1];continue
        for pi,p in enumerate(mesh['primitives']):
            if (mi,pi) not in allowed:assert d['meshes'][mi]['primitives'][pi]==p,(mi,pi)
    targets=[(x,1.7,1.34,1.5,-5.44,-5.31) for x,_,_ in GROUND]
    targets += [(x,3.97,1.45,1.12,-5.46,-5.33) for x,_,_ in UPPER]
    removed=[]
    for pi,p in enumerate(old['meshes'][4]['primitives']):
        v=rows(old,ob,p['attributes']['POSITION']);ix=rows(old,ob,p['indices']).reshape(-1,3);t=v[ix];mask=np.zeros(len(ix),dtype=bool)
        for x,y,w,h,z0,z1 in targets:
            lo=np.array([x-w/2-.06,y-h/2-.06,z0]);hi=np.array([x+w/2+.06,y+h/2+.06,z1])
            mask|=np.all(t.min(axis=1)>=lo-2e-5,axis=1)&np.all(t.max(axis=1)<=hi+2e-5,axis=1)
        current=rows(d,b,d['meshes'][4]['primitives'][pi]['indices']).reshape(-1,3)
        np.testing.assert_array_equal(current,ix[~mask]);removed.append(int(mask.sum()))
    assert removed==[1408,3168,352,0],removed
    ground=m['ground_core'];upper=m['upper_core'];assert len(ground['nodes'])==4 and len(upper['nodes'])==5
    assert d['meshes'][ground['mesh']]['primitives']==old['meshes'][31]['primitives'][1:]
    for group in [ground,upper]:
        for i in group['nodes']:
            n=d['nodes'][i];assert n['mesh']==group['mesh'];assert n.get('scale',[1,1,1])==[1,1,1]
    walls=[]
    for doc,blob in [(old,ob),(d,b)]:
        p=doc['meshes'][23]['primitives'][0];v=rows(doc,blob,p['attributes']['POSITION']);ix=rows(doc,blob,p['indices']).reshape(-1,3);walls.append(v[ix])
    expected_area=2*(sum((hi-lo)*2.25 for _,lo,hi in GROUND)+sum((hi-lo)*1.48 for _,lo,hi in UPPER))
    area=lambda t:float(np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).sum()*.5)
    removed_area=area(walls[0])-area(walls[1]);assert abs(removed_area-expected_area)<3e-4,(removed_area,expected_area)
    for x,y,_,_,_,_ in targets:
        for triangles,expect in [(walls[0],True),(walls[1],False)]:
            hits=ray(np.array([x,y,-4.5]),np.array([0.,0,-1]),triangles)
            assert bool(((hits>.9)&(hits<1.31)).any())==expect,(x,y,expect)
    new_parts=[part for part in world_primitives(d,b) if part[0].startswith('Facade_')]
    lo,hi=np.array([-1.35,.05,-3]),np.array([1.35,2.4,.8])
    for name,p,v,ix in new_parts:
        assert np.isfinite(v).all(),name
        tri=v[ix];intersect=np.all(tri.max(axis=1)>lo,axis=1)&np.all(tri.min(axis=1)<hi,axis=1)
        assert not intersect.any(),name
    generated=[]
    for mi in [33,34,35]:
        for pi,p in enumerate(d['meshes'][mi]['primitives']):
            v=rows(d,b,p['attributes']['POSITION']).astype(np.float32);ix=rows(d,b,p['indices']).reshape(-1,3)
            t=v[ix].astype(float);areas=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
            assert np.all(areas>1e-14),(mi,pi,'zero-area f32 face')
            n=rows(d,b,p['attributes']['NORMAL']);np.testing.assert_allclose(np.linalg.norm(n,axis=1),1,atol=2e-5)
            if 'normalTexture' in d['materials'][p['material']]:
                tangent=rows(d,b,p['attributes']['TANGENT']);assert np.isfinite(tangent).all()
                np.testing.assert_allclose(np.linalg.norm(tangent[:,:3],axis=1),1,atol=2e-5)
                np.testing.assert_allclose(np.sum(n*tangent[:,:3],axis=1),0,atol=2e-5)
            generated.append({'mesh':mi,'primitive':pi,'triangles':len(ix),'min_double_area_m2':float(areas.min())})
    # Retargeted horizontal/vertical mullions keep their thickness while their
    # spans change. This rejects a global nonuniform scaling shortcut.
    for part in upper['parts']:
        if 'Vertical' in part['name'] or 'Horizontal' in part['name']:
            old_size=np.diff(np.array(part['source_bounds']),axis=0)[0];new_size=np.diff(np.array(part['upper_bounds']),axis=0)[0]
            axis=0 if 'Vertical' in part['name'] else 1
            assert abs(old_size[axis]-new_size[axis])<2e-6,part['name']
    assert budget(old,ob)==m['source_budget'] and budget(d,b)==m['candidate_budget']
    report={'status':'passed asset construction/sharing/contract checks; native remains Root-owned',
      'candidate_sha256':m['sha256'],'source_sha256':m['source_sha256'],'source_bin_prefix_bytes':length,
      'removed_window_triangles':removed,'removed_window_count':8,'ground_instance_count':4,'upper_instance_count':5,
      'removed_old_wall_surface_area_m2':removed_area,'expected_removed_area_m2':expected_area,
      'zero_new_images_materials':True,'door_ground_receiver_anchor_combat_contracts_preserved':True,
      'new_primitive_checks':generated,'source_budget':m['source_budget'],'candidate_budget':m['candidate_budget']}
    (HERE/'review/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
