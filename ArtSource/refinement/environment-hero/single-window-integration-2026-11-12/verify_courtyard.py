"""Independent full-scene preservation checks for the one-window integration."""
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

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    m=json.loads((HERE/'candidate_manifest.json').read_text())
    source=BASE/'stage2/courtyard_materials_stage2.glb';module=BASE/'method-study-2026-11-12/window_infill_candidate.glb'
    candidate=HERE/m['candidate'];assert sha(candidate)==m['sha256'];assert sha(source)==m['source_sha256'];assert sha(module)==m['module_sha256']
    old,ob=read(source);new,nb=read(candidate);mold,mb=read(module)
    original_length=old['buffers'][0]['byteLength'];assert ob[:original_length]==nb[:original_length]
    for key in ['accessors','bufferViews','materials','images','textures','samplers']:
        assert new[key][:len(old[key])]==old[key],key+' source prefix changed'
    root=old['scenes'][old.get('scene',0)]['nodes'][0]
    for i,node in enumerate(old['nodes']):
        n=copy.deepcopy(new['nodes'][i]);o=copy.deepcopy(node)
        if i==root:assert n.pop('children')[:-1]==o.pop('children')
        assert n==o,node['name']
    assert len(active_nodes(new))==len(new['nodes']);assert new['scenes']==old['scenes']
    changed=[]
    for mi,mesh in enumerate(old['meshes']):
        for pi,p in enumerate(mesh['primitives']):
            n=new['meshes'][mi]['primitives'][pi]
            if n!=p:changed.append([mi,pi])
    assert changed==[[4,0],[4,1],[4,2],[23,0]],changed
    lo=np.array([-3.2,.89,-5.44]);hi=np.array([-1.74,2.51,-5.31]);removed=[]
    for pi,primitive in enumerate(old['meshes'][4]['primitives']):
        v=rows(old,ob,primitive['attributes']['POSITION']);before=rows(old,ob,primitive['indices']).reshape(-1,3)
        t=v[before];inside=np.all(t.min(axis=1)>=lo-2e-5,axis=1)&np.all(t.max(axis=1)<=hi+2e-5,axis=1)
        after=rows(new,nb,new['meshes'][4]['primitives'][pi]['indices']).reshape(-1,3)
        np.testing.assert_array_equal(after,before[~inside]);removed.append(int(inside.sum()))
    assert removed==[176,396,44,0],removed
    wall=[]
    for doc,blob in [(old,ob),(new,nb)]:
        p=doc['meshes'][23]['primitives'][0];v=rows(doc,blob,p['attributes']['POSITION']);ix=rows(doc,blob,p['indices']).reshape(-1,3);tri=v[ix]
        wall.append(tri)
    area=lambda t:np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1).sum()*.5
    difference=float(area(wall[0])-area(wall[1]));assert abs(difference-2*1.97*2.25)<1e-4,difference
    o=np.array([-2.47,1.7,-4.5]);direction=np.array([0.,0.,-1.])
    old_hits=ray(o,direction,wall[0]);new_hits=ray(o,direction,wall[1])
    assert ((old_hits>.9)&(old_hits<1.31)).any()
    assert not ((new_hits>.9)&(new_hits<1.31)).any(),'old coplanar wall skin remains'
    assert m['module_resource_maps']['material']['0']==25 and m['module_resource_maps']['material']['3']==4
    assert len(new['images'])-len(old['images'])==5 and len(new['materials'])-len(old['materials'])==3
    parts=list(world_primitives(new,nb));lo=np.array([-1.35,.05,-3]);hi=np.array([1.35,2.4,.8])
    for name,p,v,ix in parts:
        assert np.isfinite(v).all(),name
        t=v[ix];overlap=np.all(t.max(axis=1)>lo,axis=1)&np.all(t.min(axis=1)<hi,axis=1)
        assert not overlap.any(),name+' enters combat volume'
    # The module's world placement must exactly equal its approved local asset
    # translated into the selected bay, with no scale or normal conversion.
    module_parts=list(world_primitives(mold,mb));new_mesh=len(old['meshes'])
    node=next(i for i,n in enumerate(new['nodes']) if n.get('mesh')==new_mesh);frame=active_nodes(new)[node]
    for pi,(name,p,v,ix) in enumerate(module_parts):
        target=new['meshes'][new_mesh]['primitives'][pi]
        raw=rows(new,nb,target['attributes']['POSITION']);world=(np.column_stack((raw,np.ones(len(raw))))@frame.T)[:,:3]
        np.testing.assert_allclose(world,v+np.array([-2.5,0,-5.51]),atol=2e-6)
    actor=ROOT/'ArtSource/tripo-warrior/library/base_prepared_png.glb';formal=ROOT/'app/src/main/assets/models/opponents/base.glb'
    ad,ab=read(actor);fd,fb=read(formal)
    assert ad['animations']==fd['animations'] and ad['skins']==fd['skins']
    for a,f in zip(ad['meshes'],fd['meshes']):
        for ap,fp in zip(a['primitives'],f['primitives']):
            for attr in ['POSITION','JOINTS_0','WEIGHTS_0']:
                if attr in ap['attributes']:
                    np.testing.assert_array_equal(rows(ad,ab,ap['attributes'][attr]),rows(fd,fb,fp['attributes'][attr]))
    report={'status':'passed full-scene construction/preservation checks; native remains Root gate',
       'candidate_sha256':m['sha256'],'source_sha256':m['source_sha256'],'module_sha256':m['module_sha256'],
       'source_bin_prefix_bytes':original_length,'changed_source_primitives':changed,'removed_window_triangles':removed,
       'wall_surface_area_removed_m2':difference,'expected_wall_surface_area_removed_m2':8.865,
       'old_wall_pane_ray_skin_removed':True,'ground_anchors_and_combat_clearance_preserved':True,
       'current_guard_png_geometry_skin_animation_matches_formal_ktx':True,
       'budget':m['budget'],'published_app_sha256_observed':sha(ROOT/'app/src/main/assets/models/courtyard_hero.glb')}
    (HERE/'review').mkdir(parents=True, exist_ok=True)
    (HERE/'review/verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
