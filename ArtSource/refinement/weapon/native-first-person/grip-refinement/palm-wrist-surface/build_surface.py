"""Two bounded geometric surface edits of the accepted native right hand.

Run with host Python 3. No DCC, texture conversion, producer rebuild or pose edit.
The pinned accepted GLB BIN is retained verbatim; replacement surface streams are
appended. Local conforming subdivision rounds the dorsal and cuff lip topology.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import numpy as np
HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
REPO = HERE.parents[5]
sys.path.insert(0, str(NATIVE))
import verify_hands as h
sys.path.insert(0, str(NATIVE.parent))
from build_weapon import encode_glb
SOURCE = REPO / 'app/src/main/assets/models/player_hands/right_hand.glb'
SOURCE_SHA = '3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0'


def smoothstep(a, b, x):
    t = np.clip((x-a)/(b-a), 0., 1.)
    return t*t*(3.-2.*t)


def basis(document, binary):
    world = h.sampled_worlds(document, binary, 'grip', 0)
    names = {node.get('name'):i for i,node in enumerate(document['nodes'])}
    joint = lambda name: world[names[name]][:3,3]
    origin = joint('R_Hand')
    forward = (joint('R_Index1')+joint('R_Mid1')+joint('R_Pinky1'))/3-origin
    forward /= np.linalg.norm(forward)
    radial = joint('R_Index1')-joint('R_Pinky1')
    radial -= forward*(forward@radial)
    radial /= np.linalg.norm(radial)
    palm = np.cross(radial,forward)
    palm /= np.linalg.norm(palm)
    return origin,np.asarray([radial,forward,palm]),world


def blended_transforms(document,binary,joints,weights,world):
    skin=document['skins'][0]
    bind=h.values(document,binary,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    transforms=np.asarray([world[i] for i in skin['joints']])@bind
    return np.sum(transforms[joints]*weights[:,:,None,None],axis=1)


def weld(points):
    # Exact source seams and their recursively inserted edge midpoints share a
    # geometric control position, while UV and authored normal discontinuities
    # retain separate indexed vertices.
    return np.unique(np.round(points,8),axis=0,return_inverse=True)[1]


def adjacency(points,faces):
    groups=weld(points)
    count=int(groups.max())+1
    representative=np.zeros((count,3));sizes=np.bincount(groups)
    np.add.at(representative,groups,points);representative/=sizes[:,None]
    neighbors=[set() for _ in range(count)]
    opposites={}
    for face in groups[faces]:
        for a,b,c in [(face[0],face[1],face[2]),(face[1],face[2],face[0]),(face[2],face[0],face[1])]:
            if a==b:continue
            neighbors[a].add(b);neighbors[b].add(a)
            opposites.setdefault(tuple(sorted((int(a),int(b)))),[]).append(int(c))
    return groups,representative,neighbors,opposites


def geometric_normals(points,faces):
    groups=weld(points);normal=np.zeros((int(groups.max())+1,3))
    tri=points[faces];face=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    for slot in range(3):np.add.at(normal,groups[faces[:,slot]],face)
    length=np.linalg.norm(normal,axis=1);normal/=np.maximum(length[:,None],1e-18)
    return normal[groups]


def interpolate_weights(ids,coefficients,joints,weights):
    values={}
    for vertex,coefficient in zip(ids,coefficients):
        for joint,weight in zip(joints[vertex],weights[vertex]):
            values[int(joint)]=values.get(int(joint),0.)+float(coefficient*weight)
    pairs=sorted(values.items(),key=lambda row:(-row[1],row[0]))[:4]
    while len(pairs)<4:pairs.append((0,0.))
    j=np.asarray([row[0] for row in pairs],dtype=np.uint16)
    w=np.asarray([row[1] for row in pairs],dtype=float)
    w/=w.sum()
    return j,w


def original_brush(document,binary,positions,normals,joints,weights,origin,axes,world):
    transform=blended_transforms(document,binary,joints,weights,world)
    opened=np.einsum('vij,vj->vi',transform,np.column_stack((positions,np.ones(len(positions)))))[:,:3]
    local=(opened-origin)@axes.T
    normal=np.einsum('vij,vj->vi',np.linalg.inv(transform[:,:3,:3]).transpose(0,2,1),normals)
    normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-18)
    facing=normal@(-axes[2])
    u,v,depth=local.T
    names=[document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    digit_palettes=[i for i,n in enumerate(names) if n.startswith(('R_Thumb','R_Index','R_Mid','R_Ring','R_Pinky'))]
    digit=sum((weights*(joints==j)).sum(1) for j in digit_palettes)
    # Dorsal metacarpal skin, bounded above the cloth lip and below knuckles.
    dorsal=(smoothstep(.046,.057,v)*(1-smoothstep(.090,.103,v))*
            (1-smoothstep(.028,.040,np.abs(u)))*smoothstep(.35,.75,facing)*
            (1-smoothstep(.45,.68,digit))*smoothstep(.007,.012,-depth))
    # Only the first sleeve lip at the skin interface, not the other wrist wraps
    # or the distant open sleeve cut/cap. The contour is slightly bowed in v.
    lip_forward=.046-.006*(np.clip(np.abs(u)/.045,0,1)**2)
    cuff=(smoothstep(lip_forward-.013,lip_forward-.007,v)*
          (1-smoothstep(lip_forward+.001,lip_forward+.006,v))*
          (1-smoothstep(.2,.48,digit)))
    # A top-lip ring includes its underside; palm-facing skin above it is locked.
    cuff=np.where(v<lip_forward+.0025,cuff,0.)
    return dorsal,cuff,local,normal


def subdivide(points,normals,uv,joints,weights,faces,face_source,provenance,
              brushes,original_points,original_joints,original_weights,pass_index,safety):
    groups,representative,neighbors,opposites=adjacency(points,faces)
    palm,cuff=brushes
    # The support is explicitly enumerated. Edges on patch borders split on
    # both incident faces so no T junction or UV seam crack is introduced.
    group_brush=np.zeros((len(representative),2))
    for g in range(len(representative)):
        ids=np.flatnonzero(groups==g)
        group_brush[g]=[palm[ids].max(),cuff[ids].max()]
    palm,cuff=group_brush[groups].T
    active=(palm>.01)|(cuff>.01)
    edges=set()
    safety_errors=[]
    for face in faces:
        for a,b in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:
            key=tuple(sorted((int(groups[a]),int(groups[b]))))
            if key in edges or not (active[a] and active[b]):continue
            # Interpolated P and skin weights do not commute with LBS. Avoid
            # long mixed-bone edges, rather than hide their closed-pose drift.
            prov={}
            for vertex in [a,b]:
                for native,coefficient in provenance[vertex].items():
                    prov[native]=prov.get(native,0.)+.5*coefficient
            ids=list(prov);coeff=np.asarray(list(prov.values()))
            if len(ids)>3:continue
            sj,sw=interpolate_weights(ids,coeff,original_joints,original_weights)
            raw=coeff@original_points[ids]
            target=np.einsum('i,tij->tj',coeff,safety['source_points'][:,ids,:])
            blended=np.sum(safety['transforms'][:,sj]*sw[None,:,None,None],axis=1)
            actual=np.einsum('tij,j->ti',blended,np.r_[raw,1])[:,:3]
            error=float(np.linalg.norm(actual-target,axis=1).max())
            if error<=.00015:
                edges.add(key);safety_errors.append(error)
    old_count=len(points)
    output_p=list(points.copy());output_n=list(normals.copy());output_uv=list(uv.copy())
    output_j=list(joints.copy());output_w=list(weights.copy());output_prov=list(provenance)
    output_palm=list(palm);output_cuff=list(cuff)
    edge_index={}
    original_geo=geometric_normals(points,faces)
    group_normal=np.zeros_like(representative)
    np.add.at(group_normal,groups,original_geo)
    group_normal/=np.maximum(np.linalg.norm(group_normal,axis=1)[:,None],1e-18)
    group_strength=group_brush
    # Loop's one-ring limit direction, projected to the local normal on bare
    # skin so the metacarpal width and length cannot contract.
    group_delta=np.zeros_like(representative)
    for g,adj in enumerate(neighbors):
        if len(adj)<3:continue
        pstrength,cstrength=group_strength[g]
        if max(pstrength,cstrength)==0:continue
        n=len(adj);beta=3/16 if n==3 else 3/(8*n)
        d=beta*(representative[list(adj)].sum(0)-n*representative[g])
        if pstrength>=cstrength:d=group_normal[g]*(d@group_normal[g])*.92*pstrength
        else:d*=.56*cstrength
        cap=.0012 if pstrength>=cstrength else .00065
        length=np.linalg.norm(d)
        if length>cap:d*=cap/length
        group_delta[g]=d
    moved=points+group_delta[groups]
    for i in range(old_count):output_p[i]=moved[i]
    def midpoint(a,b):
        indexed=tuple(sorted((int(a),int(b))))
        if indexed in edge_index:return edge_index[indexed]
        ga,gb=groups[[a,b]];key=tuple(sorted((int(ga),int(gb))))
        if key not in edges:return None
        prov={}
        for vertex in [a,b]:
            for native,coefficient in provenance[vertex].items():
                prov[native]=prov.get(native,0.)+.5*coefficient
        # Every refined point has an exact barycentric origin on a source face.
        ids=list(prov);coeff=np.asarray(list(prov.values()))
        assert len(ids)<=3
        pj,pw=interpolate_weights(ids,coeff,original_joints,original_weights)
        base=(points[a]+points[b])*.5
        oppos=list(dict.fromkeys(opposites.get(key,[])))
        target=base.copy()
        if len(oppos)==2:
            target=.375*(representative[ga]+representative[gb])+.125*representative[oppos].sum(0)
        pstrength=.5*(palm[a]+palm[b]);cstrength=.5*(cuff[a]+cuff[b])
        delta=target-base
        normal=group_normal[ga]+group_normal[gb];normal/=max(np.linalg.norm(normal),1e-18)
        if pstrength>=cstrength:delta=normal*(delta@normal)*.92*pstrength
        else:delta*=.56*cstrength
        cap=.0012 if pstrength>=cstrength else .00065
        length=np.linalg.norm(delta)
        if length>cap:delta*=cap/length
        index=len(output_p);edge_index[indexed]=index
        output_p.append(base+delta)
        nm=normals[a]+normals[b];nm/=max(np.linalg.norm(nm),1e-18)
        output_n.append(nm);output_uv.append((uv[a]+uv[b])*.5)
        output_j.append(pj);output_w.append(pw);output_prov.append(prov)
        output_palm.append(pstrength);output_cuff.append(cstrength)
        return index
    out_faces=[];out_source=[]
    for face,source in zip(faces,face_source):
        a,b,c=map(int,face);ab,bc,ca=midpoint(a,b),midpoint(b,c),midpoint(c,a)
        count=sum(x is not None for x in [ab,bc,ca])
        if count==0:sub=[(a,b,c)]
        elif count==3:sub=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
        elif count==1:
            if ab is not None:sub=[(a,ab,c),(ab,b,c)]
            elif bc is not None:sub=[(b,bc,a),(bc,c,a)]
            else:sub=[(c,ca,b),(ca,a,b)]
        elif ab is None:sub=[(c,ca,bc),(ca,a,b),(ca,b,bc)]
        elif bc is None:sub=[(a,ab,ca),(ab,b,c),(ab,c,ca)]
        else:sub=[(b,bc,ab),(bc,c,a),(bc,a,ab)]
        out_faces.extend(sub);out_source.extend([int(source)]*len(sub))
    result=[np.asarray(x) for x in [output_p,output_n,output_uv,output_j,output_w,out_faces,out_source]]
    result[3]=result[3].astype(np.uint16);result[5]=result[5].astype(np.uint32)
    new_geo=geometric_normals(result[0],result[5])
    # Rotate the authored normal by the true geometric surface-normal change.
    # This preserves the source's shading character and all untouched normals.
    old_extended=np.vstack((original_geo,np.asarray([original_geo[a]+original_geo[b] for a,b in edge_index])))
    # Added order is insertion order of edge_index, matching output arrays.
    old_extended/=np.maximum(np.linalg.norm(old_extended,axis=1)[:,None],1e-18)
    changed=(np.linalg.norm(new_geo-old_extended,axis=1)>1e-10)
    normal_strength=np.maximum(output_palm,output_cuff)
    for i in np.flatnonzero(changed & (np.asarray(normal_strength)>0)):
        old,new=old_extended[i],new_geo[i]
        axis=np.cross(old,new);cosine=np.clip(old@new,-1,1)
        if cosine>-.99999:
            original=result[1][i]
            rotated=original+np.cross(axis,original)+np.cross(axis,np.cross(axis,original))/(1+cosine)
            result[1][i]=rotated/max(np.linalg.norm(rotated),1e-18)
    # Position-equivalent source UV splits must remain welded after both rounds.
    safety['passes'].append({'pass':pass_index+1,'accepted_welded_edges':len(edges),
                             'maximum_undeformed_interpolation_error_mm':max(safety_errors,default=0.)*1000})
    return (*result,output_prov,(np.asarray(output_palm),np.asarray(output_cuff)))


def append_stream(document,packed,array,kind,component_type):
    array=np.ascontiguousarray(array)
    packed.extend(b'\0'*(-len(packed)%4))
    view=len(document['bufferViews']);offset=len(packed)
    document['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':array.nbytes})
    packed.extend(array.tobytes())
    accessor={'bufferView':view,'componentType':component_type,'count':len(array),'type':kind}
    if kind=='VEC3' and component_type==5126:
        accessor['min']=array.min(0).tolist();accessor['max']=array.max(0).tolist()
    index=len(document['accessors']);document['accessors'].append(accessor)
    return index


def main():
    data=SOURCE.read_bytes();assert hashlib.sha256(data).hexdigest()==SOURCE_SHA
    document,binary=h.read(SOURCE);actual=copy.deepcopy(document);packed=bytearray(binary)
    primitive=document['meshes'][0]['primitives'][0];a=primitive['attributes']
    old_p=h.values(document,binary,a['POSITION']).astype(float)
    old_n=h.values(document,binary,a['NORMAL']).astype(float)
    old_uv=h.values(document,binary,a['TEXCOORD_0']).astype(float)
    old_j=h.values(document,binary,a['JOINTS_0']).astype(np.uint16)
    old_w=h.values(document,binary,a['WEIGHTS_0']).astype(float)
    old_f=h.values(document,binary,primitive['indices']).reshape(-1,3).astype(np.uint32)
    origin,axes,world=basis(document,binary)
    palm,cuff,source_local,source_normal=original_brush(document,binary,old_p,old_n,old_j,old_w,origin,axes,world)
    source_faces_by_vertex=[set() for _ in old_p]
    for fi,face in enumerate(old_f):
        for vertex in face:source_faces_by_vertex[vertex].add(fi)
    p,n,uv,j,w,f,fs=old_p,old_n,old_uv,old_j,old_w,old_f,np.arange(len(old_f))
    provenance=[{i:1.} for i in range(len(old_p))]
    brushes=(palm,cuff)
    bind=h.values(document,binary,document['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    sampled=[h.sampled_worlds(document,binary,'grip',time) for time in [0.,.5,1.]]
    safety={'source_points':np.asarray([h.skin(document,binary,primitive,worlds) for worlds in sampled]),
            'transforms':np.asarray([np.asarray([worlds[i] for i in document['skins'][0]['joints']])@bind for worlds in sampled]),
            'passes':[]}
    passes=[]
    for pass_index in range(2):
        p,n,uv,j,w,f,fs,provenance,brushes=subdivide(p,n,uv,j,w,f,fs,provenance,brushes,old_p,old_j,old_w,pass_index,safety)
        passes.append({'pass':pass_index+1,'vertices':len(p),'triangles':len(f)})
    # Float32 is the actual exported contract, including equality of old vertices.
    p=p.astype('<f4');n=n.astype('<f4');uv=uv.astype('<f4');w=w.astype('<f4')
    j=j.astype('<u2');f=f.astype('<u4')
    assert np.isfinite(p).all() and np.max(np.abs(w.sum(1)-1))<1e-6
    output_primitive=actual['meshes'][0]['primitives'][0]
    for semantic,array,kind,component in [('POSITION',p,'VEC3',5126),('NORMAL',n,'VEC3',5126),('TEXCOORD_0',uv,'VEC2',5126),('JOINTS_0',j,'VEC4',5123),('WEIGHTS_0',w,'VEC4',5126)]:
        output_primitive['attributes'][semantic]=append_stream(actual,packed,array,kind,component)
    output_primitive['indices']=append_stream(actual,packed,f.reshape(-1),'SCALAR',5125)
    packed.extend(b'\0'*(-len(packed)%4));actual['buffers'][0]['byteLength']=len(packed)
    output=encode_glb(actual,bytes(packed));candidate=HERE/'right_hand_surface.glb';candidate.write_bytes(output)
    added=[]
    for i in range(len(old_p),len(p)):
        prov=provenance[i];ids=list(prov)
        common=set.intersection(*(source_faces_by_vertex[v] for v in ids))
        assert common, 'Added point has no source triangle barycentric origin'
        face=min(common);vertices=old_f[face].tolist()
        added.append({'candidate_vertex_id':i,'source_face_id':face,'source_vertex_ids':vertices,
                      'barycentric':[prov.get(v,0.) for v in vertices]})
    changed=np.linalg.norm(p[:len(old_p)]-old_p,axis=1)>0
    normal_changed=np.linalg.norm(n[:len(old_p)]-old_n,axis=1)>0
    def region(label,brush):
        original=np.flatnonzero(brush>0)
        candidate_vertices=np.flatnonzero(brushes[0 if label=='dorsal' else 1]>0)
        cf=np.flatnonzero(np.isin(f,candidate_vertices).any(1))
        sf=np.unique(fs[cf])
        boundary=np.setdiff1d(np.unique(old_f[sf]),original)
        candidate_boundary=np.setdiff1d(np.unique(f[cf]),candidate_vertices)
        # All subdivision support faces are inside the declared exact ROI set.
        return {'source_vertex_ids':original.tolist(),'source_face_ids':sf.tolist(),
                'candidate_vertex_ids':candidate_vertices.tolist(),'candidate_face_ids':cf.tolist(),
                'source_boundary_vertex_ids':boundary.tolist(),
                'candidate_boundary_vertex_ids':candidate_boundary.tolist(),
                'original_moved_vertex_ids':np.flatnonzero(changed&(brush>0)).tolist(),
                'source_open_center_canonical_m':h.skin(document,binary,primitive,world)[original].mean(0).tolist()}
    rois={'dorsal':region('dorsal',palm),'cuff':region('cuff',cuff)}
    closed=h.skin(document,binary,primitive,h.sampled_worlds(document,binary,'grip',1))
    render_guides={}
    for label,roi in rois.items():
        ids=np.asarray(roi['source_vertex_ids'])
        if label=='cuff':
            ids=ids[((closed[ids]-origin)@axes.T)[:,2]<-.006]
        render_guides[label]={'grip_time':1.,'center_canonical_m':closed[ids].mean(0).tolist(),
                              'outward_canonical_unit':(-axes[2]).tolist(),
                              'camera_distance_m':.3,'source_roi_vertex_ids':ids.tolist()}
    all_support=np.unique(fs[np.bincount(fs,minlength=len(old_f))[fs]>1])
    affected_faces=np.unique(np.r_[all_support,np.flatnonzero(changed[old_f].any(1))])
    affected_vertices=np.unique(old_f[affected_faces])
    baseline_points=np.asarray([sum(old_p[vertex]*coefficient for vertex,coefficient in prov.items())
                                for prov in provenance])
    baseline_groups=weld(baseline_points)
    seam_groups=[np.flatnonzero(baseline_groups==group).tolist()
                 for group in np.flatnonzero(np.bincount(baseline_groups)>1)]
    touched_seams=[ids for ids in seam_groups
                   if any(vertex>=len(old_p) or changed[vertex] for vertex in ids)]
    maximum_seam_gap=max((float(np.linalg.norm(p[ids]-p[ids[0]],axis=1).max())
                          for ids in touched_seams),default=0.)
    delta={'schema':'palm-wrist-surface-v1','source':str(SOURCE.relative_to(REPO)),'source_sha256':SOURCE_SHA,
           'candidate':str(candidate.relative_to(REPO)),'candidate_sha256':hashlib.sha256(output).hexdigest(),
           'coordinate_frame':{'space':'actual openHand / grip0 LBS canonical root, metres','wrist_origin':origin.tolist(),
                               'radial_unit':axes[0].tolist(),'finger_forward_unit':axes[1].tolist(),
                               'palm_outward_unit':axes[2].tolist(),'dorsal_outward_unit':(-axes[2]).tolist()},
           'rois':rois,'render_guides':render_guides,'source_primitive_index':0,'candidate_primitive_index':0,
           'source_vertex_count':len(old_p),'source_face_count':len(old_f),
           'candidate_vertex_count':len(p),'candidate_face_count':len(f),
           'source_support_vertex_ids':affected_vertices.tolist(),'source_support_face_ids':affected_faces.tolist(),
           'original_moved_vertex_ids':np.flatnonzero(changed).tolist(),
           'original_normal_changed_vertex_ids':np.flatnonzero(normal_changed).tolist(),
           'candidate_vertex_to_source':list(range(len(old_p)))+[-1]*(len(p)-len(old_p)),
           'candidate_added_vertices':added,'candidate_face_to_source_face':fs.tolist(),
           'seam_protection':{'candidate_source_position_equivalence_groups_touched':touched_seams,
                              'maximum_raw_bind_seam_gap_m':maximum_seam_gap,
                              'note':'Equivalent source-position UV splits retain separate UVs and authored normals, while welded Loop controls keep their actual positions coincident. Boundary vertex IDs above are outside each individual brush; overlapping dorsal/cuff brushes are enumerated independently.'},
           'passes':passes,'interpolation_safety':safety['passes'],'method':{'geometry':'Two deterministic conforming local Loop curvature rounds; normal-only bare-dorsal displacement and bounded full-vector first-cuff-lip relaxation. Welded geometric seams share controls. Feathered per-source-vertex brush excludes palmar skin, fingers, other cuff bands and remote sleeve cut. Subdivide only edges with both endpoints in a brush and undeformed source-bary LBS residual <=0.15mm at open/mid/closed; no zero-brush support points.',
               'normal':'Rotate authored normals by the local geometric area-normal change, only in the two brushes; no all-hand averaging.',
               'tangent':'No source TANGENT attribute exists. UVs remain exact for old vertices and barycentric for inserted ones; renderer derives tangent basis from changed positions and unchanged UV charts.',
               'uv':'Original values exact; inserted edge points interpolate within each original UV chart, retaining split seams.',
               'weights':'Original JOINTS_0 and WEIGHTS_0 exact; inserted vertices barycentric from original face, strongest four merged palette weights normalized.',
               'boundary':'Only local incident support faces are subdivided; all neighbor faces sharing each selected welded edge are conformingly split. Original vertices at zero brush remain bitwise exact.',
               'limits':'Each old/midpoint round raw-source displacement <=1.2mm dorsal / .65mm cuff; no animation, node, bone, inverse-bind, closure, material or embedded KTX changes.'}}
    (HERE/'roi_delta.json').write_text(json.dumps(delta,indent=2)+'\n')
    state=[]
    for time in [None,0.,.5,1.]:
        worlds=h.sampled_worlds(document,binary,None if time is None else 'grip',0 if time is None else time)
        before=h.skin(document,binary,primitive,worlds);after=h.skin(actual,bytes(packed),output_primitive,worlds)
        displacement=np.linalg.norm(after[:len(old_p)]-before,axis=1)
        tri=after[f];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5
        state.append({'state':'default' if time is None else time,'maximum_original_vertex_displacement_mm':float(displacement.max()*1000),
                      'original_vertex_ids_changed':np.flatnonzero(displacement>1e-9).tolist(),'minimum_triangle_area_m2':float(areas.min()),
                      'all_finite':bool(np.isfinite(after).all())})
    total_faces=len(f)+document['accessors'][document['meshes'][0]['primitives'][1]['indices']]['count']//3
    assert total_faces<=8000
    manifest={'source_sha256':SOURCE_SHA,'candidate_sha256':hashlib.sha256(output).hexdigest(),
              'candidate':str(candidate.relative_to(REPO)),'source_total_triangles':4936,'candidate_total_triangles':total_faces,
              'bytes':len(output),'source_binary_is_exact_prefix':bytes(packed).startswith(binary),'passes':passes,
              'curves_nodes_skin_materials_images_exact':all(actual[k]==document[k] for k in ['animations','nodes','skins','materials','images','textures']),
              'closure_primitive_exact':actual['meshes'][0]['primitives'][1]==document['meshes'][0]['primitives'][1],
              'original_uv_joints_weights_exact':bool(np.array_equal(uv[:len(old_p)],old_uv) and np.array_equal(j[:len(old_p)],old_j) and np.array_equal(w[:len(old_p)],old_w)),
              'old_vertices_moved':int(changed.sum()),'old_normals_changed':int(normal_changed.sum()),
              'original_position_maximum_displacement_bind_mm':float(np.linalg.norm(p[:len(old_p)]-old_p,axis=1).max()*1000),
              'state_geometry':state,'verification_note':'Producer finite/area/preservation checks only. Independent full actual LBS source-vs-candidate core/self checks and matched physical-light renders remain required.'}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='state_geometry'},indent=2))


if __name__=='__main__':main()
