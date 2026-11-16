"""Reconstruct the dorsal/wrist surface from the accepted Right v2, not prior trials."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('hand_surface_tools', HERE.parent / 'build_surface.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def unit(value):
    size = np.linalg.norm(value, axis=-1, keepdims=True)
    return value / np.maximum(size, 1e-20)


def quadratic(u, v):
    U, V = u / .04, (v - .07) / .04
    return np.column_stack((np.ones_like(U), U, V, U*U, U*V, V*V))


def fit_surface(local, selected):
    matrix = quadratic(local[selected, 0], local[selected, 1])
    depth = local[selected, 2]
    weights = np.ones(len(depth))
    # Three fixed robust-fit steps reject isolated sculpt/scan ridges without a parameter search.
    for _ in range(3):
        coef = np.linalg.lstsq(matrix * weights[:, None], depth * weights, rcond=None)[0]
        residual = depth - matrix @ coef
        scale = max(float(np.median(abs(residual - np.median(residual)))) * 1.4826, .0005)
        weights = np.minimum(1., 1.5 * scale / np.maximum(abs(residual), 1e-12))
    return coef


def feasible_normal(constraints, preferred):
    constraints = unit(np.asarray(constraints))
    normal = unit(np.asarray(preferred))
    for _ in range(24):
        dots = constraints @ normal
        if dots.min() >= .003:
            return normal, True
        for vector in constraints[dots < .003]:
            normal = unit(normal + (.003 - float(vector @ normal)) * vector)
    return normal, bool((constraints @ normal).min() >= 1e-5)


def main():
    assert hashlib.sha256(b.SOURCE.read_bytes()).hexdigest() == b.SOURCE_SHA
    doc, binary = b.h.read(b.SOURCE)
    prim = doc['meshes'][0]['primitives'][0]
    attrs = {k: b.h.values(doc, binary, v) for k, v in prim['attributes'].items()}
    op, on, ouv = [attrs[k].astype(float) for k in ('POSITION', 'NORMAL', 'TEXCOORD_0')]
    oj, ow = attrs['JOINTS_0'].astype(np.uint16), attrs['WEIGHTS_0'].astype(float)
    of = b.h.values(doc, binary, prim['indices']).reshape(-1, 3).astype(np.uint32)
    origin, axes, world = b.basis(doc, binary)
    transform = b.blended_transforms(doc, binary, oj, ow, world)
    opened = np.einsum('vij,vj->vi', transform, np.column_stack((op, np.ones(len(op)))))[:, :3]
    local = (opened-origin) @ axes.T
    normals = unit(np.einsum('vij,vj->vi', np.linalg.inv(transform[:, :3, :3]).transpose(0,2,1), on))
    names = [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
    palettes = [i for i,n in enumerate(names) if n.startswith(('R_Thumb','R_Index','R_Mid','R_Ring','R_Pinky'))]
    digit = sum((ow*(oj==i)).sum(1) for i in palettes)
    u, v, depth = local.T
    facing = normals @ (-axes[2])
    fit_mask = (v>.035)&(v<.108)&(abs(u)<.045)&(facing>.2)&(digit<.2)&(depth<-.006)
    assert fit_mask.sum() >= 12
    coef = fit_surface(local, fit_mask)
    dorsal = (b.smoothstep(.039,.055,v)*(1-b.smoothstep(.086,.102,v))*
              (1-b.smoothstep(.026,.043,abs(u)))*b.smoothstep(.20,.65,facing)*
              (1-b.smoothstep(.08,.18,digit))*b.smoothstep(.007,.014,-depth))
    _, cuff, _, _ = b.original_brush(doc,binary,op,on,oj,ow,origin,axes,world)
    cuff *= 1-b.smoothstep(.08,.18,digit)
    # Welded UV duplicates share an identical geometric control and brush.
    groups = b.weld(op)
    for group in np.unique(groups):
        ids = np.flatnonzero(groups == group)
        dorsal[ids], cuff[ids] = dorsal[ids].max(), cuff[ids].max()
    # One measured repair: the mid-pose child of this thin wrist fan became
    # near-degenerate. Retain its original surface and one-ring exactly rather
    # than forcing a new normal or exempting it from validation.
    failure_face = 1226
    seeds = groups[of[failure_face]]
    fan_faces = np.flatnonzero(np.isin(groups[of], seeds).any(1))
    retained_groups = np.unique(groups[of[fan_faces]])
    retained = np.isin(groups, retained_groups)
    dorsal[retained] = 0.;cuff[retained] = 0.
    active = np.maximum(dorsal, cuff) > .001
    source_roi_faces = np.flatnonzero(active[of].any(1))
    support = np.unique(of[source_roi_faces])
    allowed = active.copy()
    allowed[support[(digit[support] < .15) & ((local[support,2]<-.006)|(local[support,1]<.045))]] = True
    protected = np.flatnonzero(~allowed)
    bind = b.h.values(doc,binary,doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    sampled = [b.h.sampled_worlds(doc,binary,'grip',t) for t in [0.,.5,1.]]
    safety = {'source_points':np.asarray([b.h.skin(doc,binary,prim,w) for w in sampled]),
              'transforms':np.asarray([np.asarray([w[i] for i in doc['skins'][0]['joints']])@bind for w in sampled]),'passes':[]}
    provenance = [{i:1.} for i in range(len(op))]
    p,n,uv,j,w,f,fm,provenance,brushes = b.subdivide(op,on,ouv,oj,ow,of,np.arange(len(of)),provenance,
        (dorsal,cuff),op,oj,ow,0,safety)
    assert len(f) < 7900
    # Reconstruct from source barycentric control points, discard the old Loop displacement.
    base = np.asarray([sum(op[idx]*weight for idx,weight in row.items()) for row in provenance])
    blends = b.blended_transforms(doc,binary,j,w,world)
    points = np.einsum('vij,vj->vi',blends,np.column_stack((base,np.ones(len(base)))))[:,:3]
    loc = (points-origin) @ axes.T
    dbrush, cbrush = map(np.asarray, brushes)
    target = loc.copy()
    target[:,2] += np.clip(quadratic(loc[:,0],loc[:,1]) @ coef - loc[:,2], -.003, .003) * dbrush
    # The first cuff lip keeps its axial folds; circular controls round only its polygonal perimeter.
    weld, controls, neighbors, _ = b.adjacency(base,f)
    radial = np.column_stack((loc[:,0],loc[:,2]))
    for group in np.unique(weld):
        ids = np.flatnonzero(weld==group)
        strength = float(cbrush[ids].max())
        if strength<=0 or len(neighbors[group])<3:
            continue
        adjacent = np.flatnonzero(np.isin(weld,list(neighbors[group])))
        average = radial[adjacent].mean(0)
        center = radial[ids].mean(0)
        move = np.clip(average-center,-.0015,.0015) * .65*strength
        target[ids,0] += move[0]
        target[ids,2] += move[1]
    desired = origin + target @ axes
    inverse = np.linalg.inv(blends)
    p = np.einsum('vij,vj->vi',inverse,np.column_stack((desired,np.ones(len(desired)))))[:,:3]
    # Zero-brush originals remain byte-identical; weld controls remove arithmetic split gaps.
    p[:len(op)][~active] = op[~active]
    for group in np.unique(weld):
        ids=np.flatnonzero(weld==group)
        if len(ids)>1:
            if any(i<len(op) and not active[i] for i in ids):
                fixed=next(i for i in ids if i<len(op) and not active[i]);p[ids]=p[fixed]
            else:p[ids]=p[ids].mean(0)
    p = p.astype('<f4').astype(float)
    posed, inverse_blends = [], []
    for time in [None,0.,.5,1.]:
        worlds=b.h.sampled_worlds(doc,binary,None if time is None else 'grip',0 if time is None else time)
        blend=b.blended_transforms(doc,binary,j,w,worlds)
        posed.append(np.einsum('vij,vj->vi',blend,np.column_stack((p,np.ones(len(p)))))[:,:3])
        inverse_blends.append(np.linalg.inv(blend[:,:3,:3]))
    face_normals=[unit(np.cross(q[f[:,1]]-q[f[:,0]],q[f[:,2]]-q[f[:,0]])) for q in posed]
    roi_candidate=np.isin(fm,source_roi_faces)
    incident=[[] for _ in p]
    for fi,face in enumerate(f):
        for vertex in face:incident[int(vertex)].append(fi)
    normals = on.tolist()+n[len(op):].tolist()
    positions,uvs,joints,weights = map(list,(p,uv,j,w))
    vertex_map=list(range(len(op)))+[-1]*(len(p)-len(op))
    normal_splits=[]
    unresolved=[]
    def corner_constraints(vertex, face_ids):
        return [inverse_blends[t][vertex] @ face_normals[t][fi] for t in range(4) for fi in face_ids]
    for vertex,fs in enumerate(incident):
        selected=[fi for fi in fs if roi_candidate[fi]]
        if not selected or (vertex<len(op) and not allowed[vertex]):continue
        constraints=corner_constraints(vertex,fs)
        normal,good=feasible_normal(constraints,np.sum(unit(np.asarray(constraints)),axis=0))
        if good and all(roi_candidate[fi] for fi in fs):
            normals[vertex]=normal
            continue
        # Duplicate only the affected corners, preserving all indexed attributes and geometric welds.
        for fi in selected:
            constraints=corner_constraints(vertex,[fi])
            normal,good=feasible_normal(constraints,np.sum(unit(np.asarray(constraints)),axis=0))
            if not good:unresolved.append({'vertex':vertex,'face':fi});continue
            new=len(positions)
            positions.append(p[vertex].copy());uvs.append(uv[vertex].copy());joints.append(j[vertex].copy());weights.append(w[vertex].copy());normals.append(normal)
            provenance.append(dict(provenance[vertex]));vertex_map.append(vertex_map[vertex]);normal_splits.append(new)
            f[fi,f[fi]==vertex]=new
    if unresolved:raise ValueError('Pose geometry has no coherent corner normal: '+str(unresolved[:5]))
    p,n,uv,j,w = np.asarray(positions,dtype='<f4'),np.asarray(normals,dtype='<f4'),np.asarray(uvs,dtype='<f4'),np.asarray(joints,dtype='<u2'),np.asarray(weights,dtype='<f4')
    out=copy.deepcopy(doc);packed=bytearray(binary);outprim=out['meshes'][0]['primitives'][0]
    for name,array,kind,component in [('POSITION',p,'VEC3',5126),('NORMAL',n,'VEC3',5126),('TEXCOORD_0',uv,'VEC2',5126),('JOINTS_0',j,'VEC4',5123),('WEIGHTS_0',w,'VEC4',5126)]:
        outprim['attributes'][name]=b.append_stream(out,packed,array,kind,component)
    outprim['indices']=b.append_stream(out,packed,f.astype('<u4').reshape(-1),'SCALAR',5125)
    packed.extend(b'\0'*(-len(packed)%4));out['buffers'][0]['byteLength']=len(packed)
    path=HERE/'right_hand_patch.glb';path.write_bytes(b.encode_glb(out,bytes(packed)))
    source_faces_by_vertex=[set() for _ in op]
    for fi,face in enumerate(of):
        for vertex in face:source_faces_by_vertex[vertex].add(fi)
    added=[]
    for i,mapping in enumerate(vertex_map):
        if mapping!=-1:continue
        prov=provenance[i];parent=min(set.intersection(*(source_faces_by_vertex[v] for v in prov)))
        verts=of[parent].tolist();added.append({'candidate_vertex_id':i,'source_face_id':int(parent),
            'source_vertex_ids':verts,'barycentric':[prov.get(v,0.) for v in verts]})
    closed=b.h.skin(doc,binary,prim,b.h.sampled_worlds(doc,binary,'grip',1.))
    guides={}
    for label,brush in [('dorsal',dorsal),('cuff',cuff)]:
        ids=np.flatnonzero(brush>.01)
        if label=='cuff':ids=ids[local[ids,2]<-.006]
        guides[label]={'center_canonical_m':closed[ids].mean(0).tolist(),'outward_canonical_unit':(-axes[2]).tolist(),
                       'source_roi_vertex_ids':ids.tolist(),'camera_distance_m':.3,'grip_time':1.}
    delta={'schema':'right-production-patch-v1','source':str(b.SOURCE.relative_to(b.REPO)),'source_sha256':b.SOURCE_SHA,
        'candidate':str(path.relative_to(b.REPO)),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_vertex_count':len(op),'source_face_count':len(of),'candidate_vertex_to_source':vertex_map,
        'candidate_face_to_source':fm.tolist(),'candidate_added_vertices':added,'modified_source_vertices':np.flatnonzero(allowed).tolist(),
        'protected_source_vertices':protected.tolist(),'ROI_faces':source_roi_faces.tolist(),'normal_split_vertices':normal_splits,
        'actual_moved_source_vertices':np.flatnonzero(np.linalg.norm(p[:len(op)]-op,axis=1)>0).tolist(),
        'render_guides':guides,'surface_fit':{'source_fit_vertices':np.flatnonzero(fit_mask).tolist(),'quadratic_coefficients':coef.tolist(),
            'projection_cap_m':.003,'source_control_space':'open-hand anatomical u/v/dorsal','method':'robust quadratic reconstruction, one conforming support pass, selective per-corner normals'},
        'source_protection':'No digit/palmar contact edits, no rig/IBM/key/material/texture changes; static normal seams duplicate identical skin/UV/position attributes.',
        'builder':{'path':str(Path(__file__).relative_to(b.REPO)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        'localized_repair':{'attempt1_sha256':'b1bade2971ee1d4247b1d1a675f03d2ebefa9b488f057748daf7a17581008b5c',
            'source_face':failure_face,'reason':'Actual mid-pose child1244 became a thin turned triangle; retain this original mixed-skin fan and its one-ring without remeshing, no validation exclusion.',
            'source_faces_retained':fan_faces.tolist(),'source_vertices_retained':np.flatnonzero(retained).tolist()},
        'source_total_triangles':4936,'candidate_total_triangles':len(f)+doc['accessors'][doc['meshes'][0]['primitives'][1]['indices']]['count']//3}
    (HERE/'patch_delta.json').write_text(json.dumps(delta,indent=2)+'\n')
    print(json.dumps({k:delta[k] for k in ['source_sha256','candidate_sha256','source_total_triangles','candidate_total_triangles']},indent=2))
    print('moved',len(delta['actual_moved_source_vertices']),'normal seams',len(normal_splits))


if __name__=='__main__':main()
