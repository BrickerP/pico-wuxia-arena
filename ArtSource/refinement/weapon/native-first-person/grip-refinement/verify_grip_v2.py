"""Independent v2 numeric constraints and asset verification; frozen v1 read-only."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_grip as v1
h = v1.h
V1_SHA = '0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef'
V1_AUDIT_SHA = '3260bd13278665e1f8dc97f01b301dc9d175afc92818c7ede12f76617bd10bc4'


def frozen_inputs():
    model = HERE/'right_hand_refined.glb'
    audit = HERE/'verification.json'
    h.require(h.digest(model) == V1_SHA and h.digest(audit) == V1_AUDIT_SHA, 'Frozen v1 provenance changed')
    return model, json.loads(audit.read_text())


def sample_points(points, table):
    return np.asarray([np.asarray(row['barycentric']) @ points[row['native_vertex_ids']] for row in table])


def mesh_state(document, binary, time=1):
    primitive = document['meshes'][0]['primitives'][0]
    world = h.sampled_worlds(document,binary,'grip',time)
    points = h.skin(document,binary,primitive,world)
    faces = h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
    return world,points,faces


def closed_contact(document,binary,table,time=1,region_document=None,region_binary=None):
    _,points,faces = mesh_state(document,binary,time)
    samples = sample_points(points,table)
    dao = v1.dao_geometry()
    core,core_faces = dao['Handle core']
    cord,cord_faces = dao['Grip | cord wrap']
    distances,near_faces,near_points = v1.nearest(samples,core[core_faces])
    inside = np.array([v1.contains(point,core[core_faces]) if gap>1e-7 else False for point,gap in zip(samples,distances)])
    signed = distances*np.where(inside,-1,1)*1000
    gap,_,_ = v1.nearest(samples,cord[cord_faces])
    gap *= 1000
    result = {}
    for label in ['whole_hand','Thumb','Index','Mid','Ring','Pinky']:
        mask = np.ones(len(table),bool) if label=='whole_hand' else np.array([row['dominant_joint'].startswith('R_'+label) for row in table])
        result[label] = v1.summarize_group(mask,signed,gap)
    mask = np.array([row['dominant_joint']=='R_Pinky3' for row in table])
    result['R_Pinky3'] = v1.summarize_group(mask,signed,gap)
    raw = v1.finger_self_contact(region_document if region_document is not None else document, region_binary if region_binary is not None else binary, points,faces)
    _,weld = h.weld_positions(points,epsilon=1e-7)
    pairs = {}
    for label,record in raw['pairs'].items():
        pairs[label] = [pair for pair in record['native_face_pairs'] if not(set(weld[faces[pair[0]]]) & set(weld[faces[pair[1]]]))]
    return {'time':time,'groups':result,'position_weld_self_pairs':pairs,'signed_core_mm':np.round(signed,6).tolist(),
            'cord_gap_mm':np.round(gap,6).tolist(),'scope':'Frozen v1 indexed vertex/edge-mid/centroid layout; actual core winding+nearest triangles, cord unsigned surface. Not continuous max or visibility proof.'}


def replace_closed(document,binary,name,quaternion):
    changed = copy.deepcopy(document)
    packed = bytearray(binary)
    node = next(i for i,n in enumerate(changed['nodes']) if n['name']==name)
    channel = next(c for c in changed['animations'][0]['channels'] if c['target']=={'node':node,'path':'rotation'})
    sampler = changed['animations'][0]['samplers'][channel['sampler']]
    accessor = changed['accessors'][sampler['output']]
    view = changed['bufferViews'][accessor['bufferView']]
    h.require(accessor['count']==2 and accessor['componentType']==5126, 'Unexpected grip channel shape')
    quaternion = np.asarray(quaternion,dtype='<f4')
    offset = view.get('byteOffset',0)+accessor.get('byteOffset',0)+16
    packed[offset:offset+16] = quaternion.tobytes()
    changed['nodes'][node]['rotation'] = quaternion.tolist()
    return changed,bytes(packed)


def point_jacobian(document,binary,world,vertex,bone):
    primitive = document['meshes'][0]['primitives'][0]
    attributes = primitive['attributes']
    points = h.values(document,binary,attributes['POSITION'])
    palettes = h.values(document,binary,attributes['JOINTS_0']).astype(int)
    weights = h.values(document,binary,attributes['WEIGHTS_0'])
    joints = document['skins'][0]['joints']
    binds = h.values(document,binary,document['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    node = next(i for i,n in enumerate(document['nodes']) if n['name']==bone)
    parent = {child:i for i,n in enumerate(document['nodes']) for child in n.get('children',[])}
    radius = np.zeros(3)
    fraction = 0.
    pivot = world[node][:3,3]
    for palette,weight in zip(palettes[vertex],weights[vertex]):
        current = joints[palette]
        while current!=node and current in parent:
            current=parent[current]
        if current!=node:
            continue
        p = (world[joints[palette]]@binds[palette]@np.r_[points[vertex],1])[:3]
        radius += weight*(p-pivot)
        fraction += weight
    rotation = h.rigid(world[node])[:3,:3]
    jacobian = np.column_stack([np.cross(rotation[:,index],radius) for index in range(3)])
    return jacobian,rotation,float(fraction)


def constraints():
    source,audit = frozen_inputs()
    document,binary = h.read(source)
    table = audit['candidate_contact']['sample_table']
    pairs = audit['position_weld_self_contact']['models']['candidate']['Ring_Pinky']['native_face_pairs']
    world,points,faces = mesh_state(document,binary,1)
    axis = np.array([.938,.347,0.])
    axis /= np.linalg.norm(axis)
    p1 = next(i for i,n in enumerate(document['nodes']) if n['name']=='R_Pinky1')
    rotation = h.rigid(world[p1])[:3,:3]
    local_axis = rotation.T@axis
    angle = np.radians(2.)
    delta = np.r_[local_axis*np.sin(angle/2),np.cos(angle/2)]
    channel = next(c for c in document['animations'][0]['channels'] if c['target']=={'node':p1,'path':'rotation'})
    old = h.values(document,binary,document['animations'][0]['samplers'][channel['sampler']]['output'])[-1]
    probe,pb = replace_closed(document,binary,'R_Pinky1',v1.qmul(old,delta))
    _,probe_points,_ = mesh_state(probe,pb,1)
    evidence = []
    source_ids = np.load(v1.NATIVE/'selection.npz')['R_p0_source_vertex_ids']
    for ring_face,pinky_face in pairs:
        ring = points[faces[ring_face]]
        normal = np.cross(ring[1]-ring[0],ring[2]-ring[0])
        normal /= np.linalg.norm(normal)
        signed = (points[faces[pinky_face]]-ring[0])@normal
        corner = int(signed.argmin())
        vertex = int(faces[pinky_face][corner])
        gradients = {}
        for bone in ['R_Pinky1','R_Pinky2','R_Ring2']:
            jac,rot,fraction = point_jacobian(document,binary,world,vertex,bone)
            gradient = jac.T@normal
            ring_jac=[point_jacobian(document,binary,world,int(v),bone)[0] for v in faces[ring_face]]
            edge1,edge2=ring[1]-ring[0],ring[2]-ring[0]
            cross_length=np.linalg.norm(np.cross(edge1,edge2))
            normal_jac=np.column_stack([(np.eye(3)-np.outer(normal,normal))@(np.cross(ring_jac[1][:,i]-ring_jac[0][:,i],edge2)+np.cross(edge1,ring_jac[2][:,i]-ring_jac[0][:,i]))/cross_length for i in range(3)])
            full_gradient=normal_jac.T@(points[vertex]-ring[0])+(jac-ring_jac[0]).T@normal
            gradients[bone] = {'point_displacement_J_metres_per_radian':jac.tolist(),
                               'outward_local_post_axis_unit':(gradient/np.linalg.norm(gradient)).tolist() if np.linalg.norm(gradient)>1e-12 else None,
                               'maximum_outward_plane_derivative_metres_per_radian':float(np.linalg.norm(gradient)),
                               'full_moving_Ring_plane_gradient_metres_per_radian':full_gradient.tolist(),
                               'full_support_separating_local_post_axis_unit':(full_gradient/np.linalg.norm(full_gradient)).tolist() if np.linalg.norm(full_gradient)>1e-12 else None,
                               'affected_skin_fraction':fraction}
        jac,rot,_ = point_jacobian(document,binary,world,vertex,'R_Pinky1')
        predicted = float(signed[corner]+angle*(normal@jac@local_axis))
        actual = float((probe_points[vertex]-ring[0])@normal)
        evidence.append({'ring_native_face':ring_face,'pinky_native_face':pinky_face,'pinky_constraint_native_vertex':vertex,
                         'source_vertex':int(source_ids[vertex]),'point_canonical_m':points[vertex].tolist(),
                         'ring_face_outward_canonical_unit':normal.tolist(),'source_signed_infinite_plane_mm':float(signed[corner]*1000),
                         'Pinky1_2deg_predicted_plane_mm':predicted*1000,'Pinky1_2deg_actual_same_plane_mm':actual*1000,
                         'prediction_error_mm':(actual-predicted)*1000,'actual_ring_triangle_move_max_mm':float(np.linalg.norm(probe_points[faces[ring_face]]-ring,axis=1).max()*1000),
                         'local_rotation_jacobians':gradients})
    before = closed_contact(document,binary,table)
    after = closed_contact(probe,pb,table,region_document=document,region_binary=binary)
    boundaries={str(time):{'source':closed_contact(document,binary,table,time),'given_Pinky1_2deg':closed_contact(probe,pb,table,time,document,binary)} for time in (0,.5)}
    result = {'source_v1_sha256':V1_SHA,'frozen_v1_audit_sha256':V1_AUDIT_SHA,
              'probe_scope':'One given Pinky1 canonical-axis2deg check in RAM only; no model written, no angle search.',
              'given_canonical_axis_unit':axis.tolist(),'actual_local_post_axis_unit':local_axis.tolist(),
              'angle_degrees':2,'constraints':evidence,'open_mid_given_step_boundaries':boundaries,'before':before,'after_given_2deg':after,
              'plane_note':'Signed infinite Ring-face support plane distance, not finite-face penetration depth. Ring vertex motion separately reported; actual full-mesh intersections/core are authoritative.'}
    h.require(h.digest(source)==V1_SHA and h.digest(HERE/'verification.json')==V1_AUDIT_SHA,'Frozen v1 mutated')
    (HERE/'constraints_v2.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'Pinky1_local_axis':local_axis.tolist(),'source_self_counts':{k:len(v) for k,v in before['position_weld_self_pairs'].items()},
                      'probe_self_counts':{k:len(v) for k,v in after['position_weld_self_pairs'].items()},
                      'source_Pinky':before['groups']['Pinky'],'probe_Pinky':after['groups']['Pinky'],
                      'source_Pinky3':before['groups']['R_Pinky3'],'probe_Pinky3':after['groups']['R_Pinky3'],
                      'plane_min_before_mm':min(x['source_signed_infinite_plane_mm'] for x in evidence),
                      'plane_min_probe_mm':min(x['Pinky1_2deg_actual_same_plane_mm'] for x in evidence),
                      'max_linear_prediction_error_mm':max(abs(x['prediction_error_mm']) for x in evidence)},indent=2))
    return result


def regions(document,binary):
    primitive=document['meshes'][0]['primitives'][0]
    attributes=primitive['attributes']
    faces=h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
    positions=h.values(document,binary,attributes['POSITION']).astype(float)
    palettes=h.values(document,binary,attributes['JOINTS_0']).astype(int)
    weights=h.values(document,binary,attributes['WEIGHTS_0']).astype(float)
    names=[document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    influence={digit:sum(np.sum(weights*(palettes==i),axis=1) for i,name in enumerate(names) if name.startswith('R_'+digit)) for digit in ('Thumb','Index','Mid','Ring','Pinky')}
    # Source bind-position equivalence is frozen. A new coincident collision
    # cannot become "adjacent" merely because the candidate folds onto itself.
    _,adjacency=h.weld_positions(positions,epsilon=1e-7)
    return {'faces':faces,'positions':positions,'palettes':palettes,'weights':weights,'names':names,'influence':influence,'adjacency':adjacency,
            'digit_faces':{digit:np.flatnonzero((value[faces]>.5).any(axis=1)) for digit,value in influence.items()}}


def narrow_self(points,region,changed_names):
    faces=region['faces']
    tri=points[faces]
    low,high=tri.min(axis=1),tri.max(axis=1)
    def pair_set(first,second):
        pairs=[]
        for a in first:
            candidates=second[((high[second]>=low[a]-1e-7)&(low[second]<=high[a]+1e-7)).all(axis=1)]
            for b in candidates:
                if set(region['adjacency'][faces[a]])&set(region['adjacency'][faces[b]]):continue
                if v1.triangles_cross(tri[a],tri[b]):pairs.append([int(a),int(b)])
        return sorted(pairs)
    result={}
    digits=list(region['digit_faces'])
    for index,first in enumerate(digits):
        for second in digits[index+1:]:
            result[first+'_'+second]=pair_set(region['digit_faces'][first],region['digit_faces'][second])
    moving=sum(np.sum(region['weights']*(region['palettes']==i),axis=1) for i,name in enumerate(region['names']) if name in changed_names)>0
    palm_palette=region['names'].index('R_Hand')
    palm=np.sum(region['weights']*(region['palettes']==palm_palette),axis=1)>.5
    static_palm=np.flatnonzero(palm[faces].any(axis=1)&(~moving[faces]).all(axis=1))
    moving_pinky_faces=np.flatnonzero(moving[faces].any(axis=1))
    result['MovingPinky_StaticPalm']=pair_set(moving_pinky_faces,static_palm)
    return result


def normal_geometry(document,binary,time,region,roi_faces):
    world,points,faces=mesh_state(document,binary,time)
    primitive=document['meshes'][0]['primitives'][0]
    attributes=primitive['attributes']
    palettes=h.values(document,binary,attributes['JOINTS_0']).astype(int)
    weights=h.values(document,binary,attributes['WEIGHTS_0']).astype(float)
    joints=document['skins'][0]['joints']
    binds=h.values(document,binary,document['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    matrices=np.array([world[i] for i in joints])@binds
    blend=np.sum(matrices[palettes]*weights[:,:,None,None],axis=1)
    normals=h.values(document,binary,attributes['NORMAL'])
    normals=np.einsum('vij,vj->vi',np.linalg.inv(blend[:,:3,:3]).transpose(0,2,1),normals)
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    triangles=points[faces[roi_faces]]
    cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    area=np.linalg.norm(cross,axis=1)*.5
    direction=cross/np.maximum(2*area[:,None],1e-30)
    dot=np.einsum('ij,ij->i',direction,normals[faces[roi_faces]].mean(axis=1))
    return points,area,direction,dot


def support(document,binary,time,region,table):
    world,points,faces=mesh_state(document,binary,time)
    samples=sample_points(points,table)
    mask=np.array([row['dominant_joint']=='R_Thumb3' for row in table])
    gap,_,_=v1.nearest(samples[mask],points[faces[region['digit_faces']['Index']]])
    ids=np.flatnonzero(mask)
    return {'near1_ids':ids[gap<=.001].tolist(),'near3_ids':ids[gap<=.003].tolist(),'minimum_gap_mm':float(gap.min()*1000),'samples':samples,'points':points,'world':world}


def verify_final(filename,expected_sha):
    source,audit=frozen_inputs()
    a,ab=h.read(source);b,bb=h.read(filename)
    h.require(h.digest(filename)==expected_sha,'V2 candidate pin mismatch')
    delta_file=HERE/'pose_delta_v2.json'
    h.require(h.digest(delta_file)=='f61ebc7b69caa4d85796bc6af47f8ec1e1c9979220e61b85d3a3232fcc666db0','Frozen v2 delta pin mismatch')
    h.require(h.digest(HERE/'manifest_v2.json')=='40de115857d058617cfdb2f907050b78782855a04444bd201fb39ed8459457cc','Frozen v2 manifest pin mismatch')
    delta=json.loads(delta_file.read_text())
    report={'source_v1_sha256':V1_SHA,'frozen_v1_audit_sha256':V1_AUDIT_SHA,'candidate_v2_sha256':expected_sha,'errors':[],'blocking_regressions':[]}
    try:
        h.require(delta['source_sha256']==V1_SHA,'V2 delta not relative frozen v1')
        allowed={'R_'+digit+str(i) for digit in ('Ring','Pinky') for i in (1,2,3)}
        h.require(set(delta['changes'])<=allowed,'V2 changed joints outside Ring/Pinky')
        geometry_diff={}
        pa,pb=a['meshes'][0]['primitives'][0],b['meshes'][0]['primitives'][0]
        for name,index in pa['attributes'].items():
            old=h.values(a,ab,index);new=h.values(b,bb,pb['attributes'][name])
            if old.shape!=new.shape:
                geometry_diff[name]={'shape_source':list(old.shape),'shape_candidate':list(new.shape)}
            elif not np.array_equal(old,new):
                ids=np.flatnonzero((old!=new).any(axis=1))
                geometry_diff[name]={'changed_native_vertex_ids':ids.tolist(),'maximum_component_delta':float(abs(old.astype(float)-new).astype(float).max())}
        report['actual_geometry_weight_attribute_diff']=geometry_diff
        h.require(not geometry_diff,'Authorized local geometry/weights were detected and listed; this frozen pose-only contract cannot certify them without a declared edit scope and open/mid/closed shape review')
        report['structural_contract']=v1.verify_contract(a,ab,b,bb,delta)
        protected_digits={'R_'+digit+str(i) for digit in ('Thumb','Index') for i in (1,2,3)}
        for i,node in enumerate(a['nodes']):
            if node['name'] in protected_digits:
                h.require(node==b['nodes'][i],'Frozen Thumb/Index default node changed')
        for channel in a['animations'][0]['channels']:
            name=a['nodes'][channel['target']['node']]['name']
            if name in protected_digits:
                i=channel['sampler']
                h.require(a['animations'][0]['samplers'][i]==b['animations'][0]['samplers'][i],'Frozen Thumb/Index sampler changed')
        report['Thumb_Index_default_and_curve_descriptors_frozen_exact']=True
        report['negative_contract_tests']=v1.contract_negative_tests(a,ab,b,bb,delta)
        test_before={(1,2),(3,4)};test_after={(1,2),(5,6)}
        h.require(len(test_before)==len(test_after) and test_after-test_before=={(5,6)},'Equal-count replacement set control failed')
        report['face_set_policy_control']={'equal_count_new_pair_detected':True}
        default=h.sampled_worlds(b,bb);endpoint=h.sampled_worlds(b,bb,'grip',1)
        default_error=max(float(np.linalg.norm(h.skin(b,bb,p,default)-h.skin(b,bb,p,endpoint),axis=1).max()) for p in b['meshes'][0]['primitives'])
        h.require(default_error<1e-6,'Actual V2 default skin differs from closed1')
        report['actual_default_closed1_LBS_max_error_metres']=default_error
        region=regions(a,ab)
        table=audit['candidate_contact']['sample_table']
        roi=np.unique(np.r_[region['digit_faces']['Ring'],region['digit_faces']['Pinky']])
        report['boundary_checks']=[]
        for time in (0,.5,1):
            old=closed_contact(a,ab,table,time,a,ab);new=closed_contact(b,bb,table,time,a,ab)
            old_support=support(a,ab,time,region,table);new_support=support(b,bb,time,region,table)
            old_pairs=narrow_self(old_support['points'],region,set(delta['changes']))
            new_pairs=narrow_self(new_support['points'],region,set(delta['changes']))
            pairs={}
            for name,actual in new_pairs.items():
                before={tuple(pair) for pair in old_pairs[name]};after={tuple(pair) for pair in actual}
                added=sorted(after-before);removed=sorted(before-after)
                pairs[name]={'source':len(before),'candidate':len(after),'added_face_pairs':added,'removed_face_pairs':removed,'candidate_face_pairs':actual}
                if added:report['blocking_regressions'].append(str(time)+' new '+name+' face pairs '+str(len(added)))
            if new_pairs['Ring_Pinky']:
                report['blocking_regressions'].append(str(time)+' RingPinky not cleared')
            lost=sorted(set(old_support['near1_ids'])-set(new_support['near1_ids']))
            if lost:report['blocking_regressions'].append(str(time)+' Thumb3/Index support samples lost')
            thumb_error=float(np.linalg.norm(old_support['samples'][[r['dominant_joint'].startswith('R_Thumb') for r in table]]-new_support['samples'][[r['dominant_joint'].startswith('R_Thumb') for r in table]],axis=1).max())
            h.require(thumb_error<1e-10,'Actual frozen Thumb skin moves')
            oa=np.array(old['signed_core_mm']);na=np.array(new['signed_core_mm'])
            entered=np.flatnonzero((oa>=-1e-4)&(na<-1e-4))
            worsened=np.flatnonzero((oa<-1e-4)&(na<oa-1e-4))
            if len(entered) or len(worsened):report['blocking_regressions'].append(str(time)+' new/worsened core sample depth')
            op,area_old,normal_old,dot_old=normal_geometry(a,ab,time,region,roi)
            np_,area_new,normal_new,dot_new=normal_geometry(b,bb,time,region,roi)
            degenerate=roi[(area_new<=1e-12)&(area_old>1e-12)]
            inversion=roi[(np.einsum('ij,ij->i',normal_old,normal_new)<0)&(area_new>1e-12)]
            negative=roi[(dot_new<-1e-5)&(dot_old>=-1e-5)]
            if len(degenerate) or len(inversion) or len(negative):report['blocking_regressions'].append(str(time)+' new geometry/normal folding')
            protected=max(float(abs(old_support['world'][i]-new_support['world'][i]).max()) for i,n in enumerate(a['nodes']) if not n['name'].startswith(('R_Pinky','R_Ring')))
            h.require(protected<1e-12,'Wrist/root/Grip/left/non-target matrices changed')
            pad_ids=np.asarray(delta['support_fit']['stable_pad_sample_indices'],int)
            h.require(len(pad_ids)==len(np.unique(pad_ids))==24 and all(table[i]['dominant_joint']=='R_Pinky3' for i in pad_ids),'Fixed pad sample identity invalid')
            pad_before=np.array(old['cord_gap_mm'])[pad_ids];pad_after=np.array(new['cord_gap_mm'])[pad_ids]
            pad={'fixed_sample_ids':pad_ids.tolist(),'source':{'minimum_mm':float(pad_before.min()),'median_mm':float(np.median(pad_before)),'p95_mm':float(np.percentile(pad_before,95)),'within3mm':int((pad_before<=3).sum())},'candidate':{'minimum_mm':float(pad_after.min()),'median_mm':float(np.median(pad_after)),'p95_mm':float(np.percentile(pad_after,95)),'within3mm':int((pad_after<=3).sum())}}
            def bend(world):
                nodes={n['name']:i for i,n in enumerate(a['nodes'])}
                p1,p2,p3=[world[nodes['R_Pinky'+str(i)]][:3,3] for i in (1,2,3)]
                def angle(u,v):return float(np.degrees(np.arccos(np.clip(u@v/(np.linalg.norm(u)*np.linalg.norm(v)),-1,1))))
                return {'joint1_2_vs2_3_degrees':angle(p2-p1,p3-p2),'distal_axis_proxy_degrees':angle(p3-p2,world[nodes['R_Pinky3']][:3,1]),'scope':'Actual bone origins and joint3 +Y proxy, not a mesh fingertip marker or automatic natural-pose proof'}
            row={'fixed_Pinky3_pad_support':pad,'Pinky_bend_distribution':{'source':bend(old_support['world']),'candidate':bend(new_support['world'])},'time':time,'source_contact':old,'candidate_contact':new,'self_face_set_comparison':pairs,
                 'Thumb3_Index_support':{'source_near1_sample_ids':old_support['near1_ids'],'candidate_near1_sample_ids':new_support['near1_ids'],'lost_sample_ids':lost,'source_minimum_mm':old_support['minimum_gap_mm'],'candidate_minimum_mm':new_support['minimum_gap_mm'],'actual_Thumb_sample_max_displacement_m':thumb_error},
                 'core_change':{'new_inside_sample_ids':entered.tolist(),'worsened_inside_sample_ids':worsened.tolist(),'numerical_boundary_classification_epsilon_mm':1e-4},
                 'Ring_Pinky_geometry':{'source_native_face_ids':roi.tolist(),'new_degenerate_faces':degenerate.tolist(),'normal_orientation_change_negative_faces':inversion.tolist(),'new_negative_signed_average_normal_face_dot_faces':negative.tolist(),'minimum_face_area_ratio':float((area_new/area_old).min()),'maximum_face_area_ratio':float((area_new/area_old).max()),'normal_transport':'Inverse transpose blended world skin affine; offline diagnostic, not an SDK shader verification','source_negative_dot_faces':roi[dot_old<-1e-5].tolist(),'candidate_negative_dot_faces':roi[dot_new<-1e-5].tolist()},
                 'non_target_matrices_max_error':protected}
            report['boundary_checks'].append(row)
        decoded=json.loads((HERE/'decode_manifest_v2.json').read_text())
        companion=h.path(decoded['output']['path'])
        h.require(decoded['candidate_sha256']==expected_sha and h.digest(companion)==decoded['output']['sha256'],'V2 decoded companion pin mismatch')
        dd,db=h.read(companion)
        report['decoded_companion']={'sha256':decoded['output']['sha256'],'non_image_equivalence':h.image_variant_equivalence(b,bb,dd,db)}
    except Exception as error:
        report['errors'].append(str(error))
    report['frozen_v1_unchanged']=h.digest(source)==V1_SHA and h.digest(HERE/'verification.json')==V1_AUDIT_SHA
    report['candidate_stable']=h.digest(filename)==expected_sha
    report['verification_passed']=not report['errors'] and not report['blocking_regressions'] and report['frozen_v1_unchanged'] and report['candidate_stable']
    report['visible_natural_grip_accepted']=False
    report['verification_cli']='python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/verify_grip_v2.py --candidate ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined_v2.glb --sha256 '+expected_sha
    report['verifier_source_sha256']=h.digest(Path(__file__))
    report['scope']='Offline fixed-source face/sample regions and fixed-source seam equivalence at0/.5/1; new geometry/weights listed separately if present. Root exact-camera views decide natural support and hook-like shape; no SDK/device/Blender executed.'
    (HERE/'verification_v2.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'verification_passed':report['verification_passed'],'candidate':expected_sha,'errors':report['errors'],'blocking_regressions':report['blocking_regressions']}))
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--constraints',action='store_true')
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--sha256')
    args=parser.parse_args()
    if args.constraints:
        constraints()
    elif args.candidate:
        h.require(bool(args.sha256),'Frozen v2 SHA required')
        result=verify_final(args.candidate.resolve(),args.sha256)
        return 0 if result['verification_passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
