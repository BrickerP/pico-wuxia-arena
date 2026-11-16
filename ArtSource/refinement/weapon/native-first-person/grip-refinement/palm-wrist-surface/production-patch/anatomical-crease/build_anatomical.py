"""Repair the measured MCP-proximal dorsal skinning crease; preserve true fingers."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
spec=importlib.util.spec_from_file_location('healthy_surface_builder',PARENT/'build_patch.py')
tools=importlib.util.module_from_spec(spec);spec.loader.exec_module(tools)
b=tools.b


def main():
    source_path=PARENT.parents[1]/'right_hand_refined_v2.glb'
    assert hashlib.sha256(source_path.read_bytes()).hexdigest()==b.SOURCE_SHA
    source,sb=b.h.read(source_path);master=PARENT/'right_hand_patch.glb'
    assert hashlib.sha256(master.read_bytes()).hexdigest()=='3000b6be1abdfb9b003f8d67048fae39a63a3400eb48d4b37adf4b3e46a5d01c'
    doc,binary=b.h.read(master);delta=json.loads((PARENT/'patch_delta.json').read_text())
    prim=doc['meshes'][0]['primitives'][0];a={k:b.h.values(doc,binary,v) for k,v in prim['attributes'].items()}
    sp=source['meshes'][0]['primitives'][0];sa={k:b.h.values(source,sb,v) for k,v in sp['attributes'].items()}
    sf=b.h.values(source,sb,sp['indices']).reshape(-1,3).astype(int)
    f=b.h.values(doc,binary,prim['indices']).reshape(-1,3).astype(int)
    p,n,uv,j,w=[a[k].copy() for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']]
    vm=list(delta['candidate_vertex_to_source']);fm=np.asarray(delta['candidate_face_to_source'])
    origin,axes,sworld=b.basis(source,sb)
    sop=b.h.skin(source,sb,sp,sworld);slocal=(sop-origin)@axes.T
    names=[source['nodes'][i]['name'] for i in source['skins'][0]['joints']]
    hand=names.index('R_Hand')
    source_names={node.get('name'):i for i,node in enumerate(source['nodes'])}
    mcp=[]
    for name in ['R_Pinky1','R_Mid1','R_Index1']:
        mcp.append((sworld[source_names[name]][:3,3]-origin)@axes.T)
    mcp=np.asarray(sorted(mcp,key=lambda r:r[0]));boundary=np.interp(slocal[:,0],mcp[:,0],mcp[:,1])
    seeds=np.unique(sf[[1101,1075]])
    fan=np.flatnonzero(np.isin(sf,seeds).any(1));domain=np.unique(sf[fan])
    valid=(slocal[:,2]<-.01)&(slocal[:,1]<boundary-.003)&(slocal[:,1]>.05)
    approved=np.asarray([v for v in domain if valid[v]],int)
    strength=np.zeros(len(slocal));strength[approved]=.55;strength[seeds[valid[seeds]]]=1.
    strength*=b.smoothstep(.003,.008,boundary-slocal[:,1])
    # An equal-position source seam must keep identical skin/position controls.
    weld=b.weld(sa['POSITION'])
    for g in np.unique(weld):
        ids=np.flatnonzero(weld==g)
        if strength[ids].max()>0:
            if valid[ids].all():strength[ids]=strength[ids].max()
            else:strength[ids]=0
    approved=np.flatnonzero(strength>0)
    oldj=j.copy();oldw=w.copy()
    world=b.h.sampled_worlds(doc,binary,'grip',0.)
    old_blend=b.blended_transforms(doc,binary,j.astype(int),w.astype(float),world)
    old_open=np.einsum('vij,vj->vi',old_blend,np.column_stack((p,np.ones(len(p)))))[:,:3]
    for index,src in enumerate(vm):
        if src<0 or strength[src]<=0:continue
        weights={int(k):float(v) for k,v in zip(j[index],w[index]) if v>0}
        removed=0.
        for joint in list(weights):
            if names[joint].startswith(('R_Thumb','R_Index','R_Mid','R_Ring','R_Pinky')):
                amount=weights[joint]*.94*strength[src];weights[joint]-=amount;removed+=amount
        weights[hand]=weights.get(hand,0.)+removed
        pairs=sorted(weights.items(),key=lambda r:-r[1])[:4]
        while len(pairs)<4:pairs.append((0,0.))
        j[index]=[x[0] for x in pairs];w[index]=np.asarray([x[1] for x in pairs])/sum(x[1] for x in pairs)
    new_blend=b.blended_transforms(doc,binary,j.astype(int),w.astype(float),world)
    changed=np.flatnonzero(np.any(j!=oldj,axis=1)|np.any(w!=oldw,axis=1))
    # Preserve the actual open surface. Closing fingers no longer drag proximal metacarpal skin 10–15mm.
    p[changed]=np.einsum('vij,vj->vi',np.linalg.inv(new_blend[changed]),np.column_stack((old_open[changed],np.ones(len(changed)))))[:,:3]
    changed_source=np.unique([vm[i] for i in changed if vm[i]>=0])
    roi=np.flatnonzero(np.isin(sf,changed_source).any(1))
    active_faces=np.isin(fm,roi)
    posed=[];inverse=[]
    for time in [None,0.,.5,1.]:
        worlds=b.h.sampled_worlds(doc,binary,None if time is None else 'grip',0 if time is None else time)
        blend=b.blended_transforms(doc,binary,j.astype(int),w.astype(float),worlds)
        posed.append(np.einsum('vij,vj->vi',blend,np.column_stack((p,np.ones(len(p)))))[:,:3])
        inverse.append(np.linalg.inv(blend[:,:3,:3]))
    norms=[tools.unit(np.cross(q[f[:,1]]-q[f[:,0]],q[f[:,2]]-q[f[:,0]])) for q in posed]
    data=[list(p),list(n),list(uv),list(j),list(w)]
    added={r['candidate_vertex_id']:r for r in delta['candidate_added_vertices']}
    splits=[]
    for vertex in range(len(p)):
        if vm[vertex]<0 or vm[vertex] not in changed_source:continue
        incident=np.flatnonzero((f==vertex).any(1))
        constraints=[inverse[t][vertex]@norms[t][fi] for t in range(4) for fi in incident]
        normal,ok=tools.feasible_normal(constraints,np.sum(tools.unit(np.asarray(constraints)),axis=0))
        if ok:
            data[1][vertex]=normal
            continue
        for fi in incident:
            constraints=[inverse[t][vertex]@norms[t][fi] for t in range(4)]
            normal,ok=tools.feasible_normal(constraints,np.sum(tools.unit(np.asarray(constraints)),axis=0))
            if not ok:raise ValueError('No valid four-pose normal for reconstructed metacarpal corner')
            idx=len(data[0])
            for arr,old in zip(data,[p,n,uv,j,w]):arr.append(old[vertex].copy())
            data[1][-1]=normal;vm.append(vm[vertex]);splits.append(idx);f[fi,f[fi]==vertex]=idx
    p,n,uv,j,w=[np.asarray(v,dtype=t) for v,t in zip(data,['<f4','<f4','<f4','<u2','<f4'])]
    output=copy.deepcopy(doc);packed=bytearray(binary);out=output['meshes'][0]['primitives'][0]
    for semantic,arr,kind,component in [('POSITION',p,'VEC3',5126),('NORMAL',n,'VEC3',5126),('TEXCOORD_0',uv,'VEC2',5126),('JOINTS_0',j,'VEC4',5123),('WEIGHTS_0',w,'VEC4',5126)]:out['attributes'][semantic]=b.append_stream(output,packed,arr,kind,component)
    out['indices']=b.append_stream(output,packed,f.astype('<u4').reshape(-1),'SCALAR',5125)
    packed.extend(b'\0'*(-len(packed)%4));output['buffers'][0]['byteLength']=len(packed)
    path=HERE/'right_hand_patch.glb';path.write_bytes(b.encode_glb(output,bytes(packed)))
    delta['candidate']=str(path.relative_to(b.REPO));delta['candidate_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    delta['source']=str(source_path.relative_to(b.REPO))
    delta['candidate_vertex_to_source']=vm;delta['candidate_added_vertices']=list(added.values())
    delta['normal_split_vertices']+=splits
    delta['modified_source_vertices']=sorted(set(delta['modified_source_vertices'])|set(changed_source.tolist()))
    delta['protected_source_vertices']=sorted(set(range(delta['source_vertex_count']))-set(delta['modified_source_vertices']))
    delta['ROI_faces']=sorted(set(delta['ROI_faces'])|set(roi.tolist()))
    delta['anatomical_metacarpal_vertices']=changed_source.tolist()
    delta['anatomical_proof']={'seeds_source_faces':[1101,1075],'one_ring_faces':fan.tolist(),'mcp_local_points':mcp.tolist(),'margin_m':.003,'minimum_dorsal_depth_m':-.01,'redistribution':'Reduce finger spill94% at seed controls,55% feather on necessary one-ring; all removed mass goes to R_Hand; preserve actual grip0 surface.'}
    delta['builder']={'path':str(Path(__file__).relative_to(b.REPO)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (HERE/'patch_delta.json').write_text(json.dumps(delta,indent=2)+'\n')
    print('ANATOMICAL_PATCH',delta['candidate_sha256'],'source controls',changed_source.tolist(),'triangles',delta['candidate_total_triangles'])


if __name__=='__main__':main()
