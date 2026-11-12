"""Verify the specimen's construction claims, metric UV and frozen baseline."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE))
from verify_environment import read,rows,world_primitives

def ray(origin,direction,triangles):
    e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    q=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,q)
    ok=np.abs(det)>1e-10;inverse=np.divide(1.,det,out=np.zeros_like(det),where=ok)
    s=origin-triangles[:,0];u=np.einsum('ij,ij->i',s,q)*inverse
    r=np.cross(s,e1);v=np.einsum('j,ij->i',direction,r)*inverse;t=np.einsum('ij,ij->i',e2,r)*inverse
    return np.sort(t[ok&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-7)])
def inside(point,triangles):
    values=ray(np.array(point),np.array([.8381,.3117,.4483]),triangles)
    return len(np.unique(np.round(values,7)))%2==1

def main():
    source=BASE/'stage2/courtyard_materials_stage2.glb';expected='8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b'
    for p in [source,ROOT/'app/src/main/assets/models/courtyard_hero.glb']:
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,str(p)
    old,ob=read(HERE/'before_bay_with_context.glb');new,nb=read(HERE/'window_infill_construction.glb')
    runtime,rb=read(HERE/'window_infill_candidate.glb')
    oldparts=list(world_primitives(old,ob));parts=list(world_primitives(new,nb))
    runtime_parts=list(world_primitives(runtime,rb))
    assert sum(len(i) for n,p,v,i in parts)==sum(len(i) for n,p,v,i in runtime_parts)
    assert oldparts and parts,'comparison assets must be nonempty'
    named={}
    for name,p,v,i in parts:named.setdefault(name,[]).extend(v[i])
    named={n:np.array(t) for n,t in named.items()}
    oldwall=np.concatenate([v[i] for n,p,v,i in oldparts if n=='Before_EH_TavernWalls'])
    origin=np.array([.03,1.7,.8]);direction=np.array([0.,0.,-1.])
    assert len(ray(origin,direction,oldwall))>0,'original solid wall baseline must exist'
    assert len(ray(origin,direction,named['OpeningWall']))==0,'new wall aperture must be a real void'
    for name,p,v,i in parts:
        if name!='OpeningWall':continue
        normals=rows(new,nb,p['attributes']['NORMAL']);uv=rows(new,nb,p['attributes']['TEXCOORD_0'])
        front=(np.abs(v[:,2])<1e-5)&(normals[:,2]>.95)
        assert front.any(),'wall front UV audit needs real vertices'
        np.testing.assert_allclose(uv[front,0],(v[front,0]-2.5)/2.5,atol=2e-6)
        np.testing.assert_allclose(uv[front,1],1-v[front,1]/5.5,atol=2e-6)
    old_window_triangles=sum(len(i) for n,p,v,i in oldparts if n=='Before_EH_EntryDoorsWindows')
    assert old_window_triangles==616,old_window_triangles
    for n,p,v,i in oldparts:
        assert np.all(v.min(axis=0)>=[-1.22001,-.00001,-.39001]),n
        assert np.all(v.max(axis=0)<=[1.22001,3.23001,1.16001]),n
    vertical=named['LeftSash_Vertical'];horizontal=named['LeftSash_Horizontal.001']
    x=-.2725-.088
    assert inside([x,1.7,-.101],vertical)
    assert not inside([x,1.7,-.112],vertical)
    assert not inside([x,1.7,-.101],horizontal)
    assert inside([x,1.7,-.112],horizontal)
    sill=named['SlopedSill']
    front=ray(np.array([0,1.1,.130]),np.array([0.,-1.,0.]),sill)
    back=ray(np.array([0,1.1,-.220]),np.array([0.,-1.,0.]),sill)
    assert front[0]>back[0],'sill must drain toward courtyard'
    assert not inside([0,.820,.095],sill),'underside drip groove must be a void'
    assert inside([0,.820,.055],sill),'adjacent underside must remain solid'
    paper=named['LeftSash_Paper'].reshape(-1,3)
    assert np.ptp(paper[:,2])<.003,'paper must remain thin, not a 35mm box'
    densities={}
    for name,p,v,indices in parts:
        assert np.isfinite(v).all(),name
        normals=rows(new,nb,p['attributes']['NORMAL'])
        np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1,atol=.002)
        mat=new['materials'][p['material']];material=mat['name']
        if not material.startswith('Method | CC0') and not material.startswith('Method | original'):continue
        uv=rows(new,nb,p['attributes']['TEXCOORD_0'])
        image_pixels=1024 if material.startswith('Method | CC0') else 512
        values=[]
        for tri in indices:
            edges=v[tri][1:]-v[tri][0];delta=uv[tri][1:]-uv[tri][0]
            gram=edges@edges.T
            if np.linalg.det(gram)<1e-18 or np.linalg.cond(gram)>1e9:continue
            eigen=np.linalg.eigvals(np.linalg.solve(gram,delta@delta.T)).real
            if eigen.min()<=0:continue
            area=np.linalg.norm(np.cross(edges[0],edges[1]))*.5
            values.extend((float(x),float(area)) for x in np.sqrt(eigen)*image_pixels)
        densities.setdefault(material,[]).extend(values)
    density_summary={}
    for material,values in densities.items():
        expected_density=1280 if material.startswith('Method | CC0') else 2048
        array=np.array(values);order=np.argsort(array[:,0]);cdf=np.cumsum(array[order,1])
        q=np.interp(np.array([0,.01,.05,.5,.95,.99,1])*cdf[-1],cdf,array[order,0])
        assert abs(q[3]/expected_density-1)<.003,(material,q)
        assert abs(q[1]/expected_density-1)<.005 and abs(q[5]/expected_density-1)<.005,(material,q)
        density_summary[material]={'surface_area_weighted_percentiles_0_1_5_50_95_99_100_px_per_m':q.tolist(),
          'raw_triangle_percentiles_0_5_50_95_100':np.percentile(array[:,0],[0,5,50,95,100]).tolist(),
          'target':expected_density,'note':'Orthonormal metric projection on main faces; tiny curved/bevel polygons retain local projection distortion, reported rather than hidden.'}
    info={'status':'verified construction and UV, visual acceptance separate',
      'source_sha256':expected,'candidate_sha256':hashlib.sha256((HERE/'window_infill_candidate.glb').read_bytes()).hexdigest(),
      'real_wall_opening':True,'half_lap_contact_no_crossing_volume':True,'sloped_sill_and_drip_void':True,
      'old_window_triangles':old_window_triangles,'before_with_context_triangles':sum(len(i) for n,p,v,i in oldparts),
      'candidate_triangles':sum(len(i) for n,p,v,i in runtime_parts),'candidate_meshes':len(runtime['meshes']),
      'candidate_materials':len(runtime['materials']),'candidate_embedded_images':len(runtime.get('images',[])),
      'metric_uv':density_summary,'source_unchanged':True}
    (HERE/'review/construction_and_uv.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))

if __name__=='__main__':main()
