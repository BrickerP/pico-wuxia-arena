"""Read-only native grip contact + bounded candidate preservation verification.

Host Python only: no Blender/SDK/device execution. Surface helpers are loaded
from existing verified NumPy implementations without importing their pipelines.
"""
import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import numpy as np
HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
REPO = HERE.parents[4]
sys.path.insert(0, str(NATIVE))
import verify_hands as h
BASELINE_SHA = '5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d'
DAO_SHA = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'


def load_pure_function(filename, name):
    tree = ast.parse(filename.read_text())
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = {'np': np, 'math': math}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(filename), 'exec'), namespace)
    return namespace[name]


closest = load_pure_function(REPO/'ArtSource/refinement/character/design/upperbody-2026-11-12/source-prep/prepare_source.py', 'point_triangle_candidates')
contains = load_pure_function(REPO/'ArtSource/refinement/hero-face/method-study-2026-11-12/verify_specimen.py', 'contains')
point_in_triangle = load_pure_function(REPO/'ArtSource/refinement/grip/measure_weapon_surface.py', '_point_in_triangle')
triangles_cross = load_pure_function(REPO/'ArtSource/refinement/grip/measure_weapon_surface.py', '_triangles_cross')
triangles_cross.__globals__['_point_in_triangle'] = point_in_triangle


def nearest(points, triangles):
    distances, face_ids, locations = [], [], []
    for start in range(0, len(points), 64):
        batch = points[start:start+64]
        repeated = np.broadcast_to(triangles, (len(batch), *triangles.shape))
        faces, gap, bary = closest(batch, repeated)
        distances.extend(gap)
        face_ids.extend(faces)
        locations.extend(np.einsum('vi,vij->vj', bary, triangles[faces]))
    return np.asarray(distances), np.asarray(face_ids), np.asarray(locations)


def surface_control_tests():
    triangle = np.array([[[0.,0,0],[1,0,0],[0,1,0]]])
    distances, _, _ = nearest(np.array([[.2,.2,.1],[2,0,0]]), triangle)
    h.require(np.allclose(distances, [.1,1], atol=1e-12), 'Existing closest-point helper control failed')
    p = np.array([[0.,0,0],[1,0,0],[0,1,0],[0,0,1]])
    faces = np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]])
    h.require(contains(np.array([.1,.1,.1]), p[faces]), 'Inside control failed')
    h.require(not contains(np.array([-1.,0,0]), p[faces]), 'Outside control failed')
    return {'passed': True, 'cases': ['triangle interior nearest', 'edge nearest', 'closed inside winding', 'outside winding']}


def dao_geometry():
    filename = REPO/'ArtSource/tripo-warrior/library/dao_grip.glb'
    h.require(h.digest(filename) == DAO_SHA, 'Formal dao identity changed')
    document, binary = h.read(filename)
    world = h.sampled_worlds(document, binary)
    result = {}
    for index, node in enumerate(document['nodes']):
        if node.get('name') not in ('Handle core', 'Grip | cord wrap'):
            continue
        points, faces, offset = [], [], 0
        for primitive in document['meshes'][node['mesh']]['primitives']:
            p = h.values(document,binary,primitive['attributes']['POSITION']).astype(float)
            p = (np.column_stack((p,np.ones(len(p))))@world[index].T)[:,:3]
            f = h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
            points.append(p); faces.append(f+offset); offset += len(p)
        result[node['name']] = (np.concatenate(points), np.concatenate(faces))
    return result


def hand_samples(document, binary):
    primitive = document['meshes'][0]['primitives'][0]
    points = h.skin(document,binary,primitive,h.sampled_worlds(document,binary,'grip',1))
    faces = h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
    palettes = h.values(document,binary,primitive['attributes']['JOINTS_0']).astype(int)
    weights = h.values(document,binary,primitive['attributes']['WEIGHTS_0']).astype(float)
    names = [document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    hand_palette = [i for i,n in enumerate(names) if n == 'R_Hand' or n.startswith(('R_Thumb','R_Index','R_Mid','R_Ring','R_Pinky'))]
    hand_weight = sum(np.sum(weights*(palettes==i),axis=1) for i in hand_palette)
    face_ids = np.flatnonzero((hand_weight[faces]>.5).any(axis=1))
    chosen = faces[face_ids]
    vertices = np.flatnonzero(hand_weight>.5)
    edges = np.unique(np.sort(np.concatenate((chosen[:,[0,1]],chosen[:,[1,2]],chosen[:,[2,0]])),axis=1),axis=0)
    dense = np.zeros((len(points),len(names)))
    for slot in range(4):
        np.add.at(dense,(np.arange(len(points)),palettes[:,slot]),weights[:,slot])
    sample_points = np.concatenate((points[vertices],points[chosen].mean(axis=1),points[edges].mean(axis=1)))
    sample_weights = np.concatenate((dense[vertices],dense[chosen].mean(axis=1),dense[edges].mean(axis=1)))
    source_vertex_ids = np.load(NATIVE/'selection.npz')['R_p0_source_vertex_ids']
    source_face_ids = np.load(NATIVE/'selection.npz')['R_p0_source_face_ids']
    table = []
    for index in vertices:
        table.append({'kind':'vertex','native_vertex_ids':[int(index)],'source_vertex_ids':[int(source_vertex_ids[index])],'native_face_ids':[],'barycentric':[1.]})
    for index,face in zip(face_ids,chosen):
        table.append({'kind':'face_centroid','native_vertex_ids':face.tolist(),'source_vertex_ids':source_vertex_ids[face].tolist(),'native_face_ids':[int(index)],'source_face_ids':[int(source_face_ids[index])],'barycentric':[1/3]*3})
    for edge in edges:
        table.append({'kind':'edge_midpoint','native_vertex_ids':edge.tolist(),'source_vertex_ids':source_vertex_ids[edge].tolist(),'native_face_ids':[],'barycentric':[.5,.5]})
    for index,row in enumerate(table):
        row['sample_index'] = index
        row['dominant_joint'] = names[int(sample_weights[index].argmax())]
    return points, faces, names, sample_points, table


def finger_self_contact(document,binary,points,faces):
    primitive=document['meshes'][0]['primitives'][0]
    attributes=primitive['attributes']
    palettes=h.values(document,binary,attributes['JOINTS_0']).astype(int)
    weights=h.values(document,binary,attributes['WEIGHTS_0'])
    names=[document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    groups={}
    for digit in ('Thumb','Index','Mid','Ring','Pinky'):
        palette=[i for i,name in enumerate(names) if name.startswith('R_'+digit)]
        influence=sum(np.sum(weights*(palettes==i),axis=1) for i in palette)
        groups[digit]=np.flatnonzero((influence[faces]>.5).any(axis=1))
    triangles=points[faces]
    low,high=triangles.min(axis=1),triangles.max(axis=1)
    result={}
    digits=list(groups)
    source_faces=np.load(NATIVE/'selection.npz')['R_p0_source_face_ids']
    for first_index,first in enumerate(digits):
        for second in digits[first_index+1:]:
            pairs=[]
            for a in groups[first]:
                candidates=groups[second][((high[groups[second]]>=low[a]-1e-7)&(low[groups[second]]<=high[a]+1e-7)).all(axis=1)]
                for b in candidates:
                    if set(faces[a])&set(faces[b]):continue
                    if triangles_cross(triangles[a],triangles[b]):pairs.append([int(a),int(b)])
            result[first+'_'+second]={'confirmed_noncoplanar_pairs':len(pairs),'native_face_pairs':pairs,'source_face_pairs':[[int(source_faces[a]),int(source_faces[b])] for a,b in pairs]}
    return {'metric':'Actual closed finger surfaces, weight>0.5 incident faces; original-index-adjacent pairs excluded, noncoplanar intersection confirmation. Coplanar/point-only contacts are not certified penetration.','pairs':result}


def summarize_group(mask, signed, cord):
    inside = signed[mask] < -1e-4
    return {
        'samples': int(mask.sum()),
        'maximum_core_penetration_mm': float(max(0,-signed[mask].min())),
        'inside_samples': int(inside.sum()),
        'inside_depth_p95_mm': float(np.percentile(-signed[mask][inside],95)) if inside.any() else 0.,
        'nearest_cord_mm': float(cord[mask].min()),
        'median_cord_mm': float(np.median(cord[mask])),
        'cord_gap_p95_mm': float(np.percentile(cord[mask],95)),
        'cord_samples_within_1mm': int((cord[mask]<=1).sum()),
        'cord_samples_within_3mm': int((cord[mask]<=3).sum()),
        'cord_samples_farther_than_10mm': int((cord[mask]>10).sum()),
    }


def contact(filename, expected_sha):
    h.require(h.digest(filename)==expected_sha,'Hand identity changed')
    document,binary = h.read(filename)
    points,faces,names,samples,table = hand_samples(document,binary)
    dao = dao_geometry()
    core,core_faces = dao['Handle core']
    cord,cord_faces = dao['Grip | cord wrap']
    topology,_,_ = h.edge_topology(core,core_faces)
    h.require(topology['open_edges']==topology['nonmanifold_edges']==0,'Actual handle core is not closed')
    gap,near_faces,near_points = nearest(samples,core[core_faces])
    inside = np.array([contains(point,core[core_faces]) if distance>1e-7 else False for point,distance in zip(samples,gap)])
    signed = gap*np.where(inside,-1,1)*1000
    cord_gap,_,_ = nearest(samples,cord[cord_faces])
    cord_gap *= 1000
    groups = {}
    for digit in ('Thumb','Index','Mid','Ring','Pinky'):
        groups[digit] = summarize_group(np.array([r['dominant_joint'].startswith('R_'+digit) for r in table]),signed,cord_gap)
        for segment in (1,2,3):
            name='R_'+digit+str(segment)
            groups[name]=summarize_group(np.array([r['dominant_joint']==name for r in table]),signed,cord_gap)
    world = h.named_worlds(document,binary,'grip',1)
    bones = {name:world[name][:3,3].tolist() for name in world if name.startswith(('R_Thumb','R_Index','R_Mid','R_Ring','R_Pinky'))}
    witnesses = []
    for index in np.argsort(signed)[:16]:
        witnesses.append({**table[int(index)],'point_player_metres':samples[index].tolist(),'signed_core_mm':float(signed[index]),'cord_gap_mm':float(cord_gap[index]),'nearest_actual_core_point_metres':near_points[index].tolist(),'nearest_core_triangle':int(near_faces[index])})
    h.require(h.digest(filename)==expected_sha,'Hand changed during audit')
    return {
        'source':str(filename.relative_to(REPO)), 'source_sha256':expected_sha, 'formal_dao_sha256':DAO_SHA,
        'pose':'actual grip@1 closed in canonical formal dao player frame',
        'metric':'Signed actual core surface distance (negative inside via existing winding helper); open cord only unsigned nearest triangle distance',
        'scope':'Finite original native mesh vertices + unique edge midpoints + incident face centroids; not continuous maximum or visible-pixel proof. Per-phalanx gaps do not require every fingertip to touch shaft; another finger can supply support.',
        'sample_count':len(samples), 'sample_kind_counts':{kind:sum(r['kind']==kind for r in table) for kind in ['vertex','edge_midpoint','face_centroid']},
        'core_topology':topology,'core_bounds_player_metres':[core.min(axis=0).tolist(),core.max(axis=0).tolist()],
        'handle_axis_note':'Actual player-frame core extends along Z; positive Z is pommel end. Compare bone/skin Z with actual bounds, not image orientation.',
        'groups':groups,'finger_joint_origins_player_metres':bones,'deepest_samples':witnesses,
        'self_contact':finger_self_contact(document,binary,points,faces),
        'distal_tail_witnesses':[{**table[int(index)],'point_player_metres':samples[index].tolist(),'cord_gap_mm':float(cord_gap[index]),'signed_core_mm':float(signed[index])} for index in [max((i for i,row in enumerate(table) if row['dominant_joint']=='R_'+digit+'3'),key=lambda i:samples[i,2]) for digit in ('Thumb','Index','Mid','Ring','Pinky')]],
        'sample_table':table,'signed_core_mm_by_sample':np.round(signed,6).tolist(),'cord_surface_gap_mm_by_sample':np.round(cord_gap,6).tolist(),
    }


def witness_rotation_gradients(document,binary,witness):
    world=h.sampled_worlds(document,binary,'grip',1)
    nodes={n['name']:i for i,n in enumerate(document['nodes'])}
    parents={child:i for i,n in enumerate(document['nodes']) for child in n.get('children',[])}
    joints=document['skins'][0]['joints']
    binds=h.values(document,binary,document['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    primitive=document['meshes'][0]['primitives'][0]
    a=primitive['attributes']
    positions=h.values(document,binary,a['POSITION'])
    palettes=h.values(document,binary,a['JOINTS_0']).astype(int)
    weights=h.values(document,binary,a['WEIGHTS_0'])
    point=np.asarray(witness['point_player_metres'])
    outward=np.asarray(witness['nearest_actual_core_point_metres'])-point
    outward/=np.linalg.norm(outward)
    result={}
    for name in ('R_Thumb1','R_Thumb2'):
        node=nodes[name]
        pivot=world[node][:3,3]
        radius=np.zeros(3)
        affected=0.0
        for vertex,coefficient in zip(witness['native_vertex_ids'],witness['barycentric']):
            for palette,weight in zip(palettes[vertex],weights[vertex]):
                current=joints[palette]
                while current!=node and current in parents:current=parents[current]
                if current!=node:continue
                transformed=(world[joints[palette]]@binds[palette]@np.r_[positions[vertex],1])[:3]
                radius+=coefficient*weight*(transformed-pivot)
                affected+=coefficient*weight
        axes=world[node][:3,:3].copy()
        axes/=np.linalg.norm(axes,axis=0)[None,:]
        jacobian=np.column_stack([np.cross(axes[:,i],radius) for i in range(3)])
        gradient=jacobian.T@outward
        result[name]={'local_post_rotation_outward_axis_unit':(gradient/np.linalg.norm(gradient)).tolist(),
                      'canonical_rotation_axis_unit':(axes@(gradient/np.linalg.norm(gradient))).tolist(),
                      'maximum_outward_derivative_metres_per_radian':float(np.linalg.norm(gradient)),
                      'affected_skin_weight_fraction':float(affected)}
    return {'canonical_outward_unit':outward.tolist(),'bones':result,'scope':'First-order local-post rotation Jacobian at actual closed skin witness, not a safe final angle/whole-finger solution.'}


def qmul(first,second):
    first,second=np.asarray(first,float),np.asarray(second,float)
    xyz=first[3]*second[:3]+second[3]*first[:3]+np.cross(first[:3],second[:3])
    result=np.r_[xyz,first[3]*second[3]-first[:3]@second[:3]]
    return result/np.linalg.norm(result)


def qdistance(first,second):
    first=np.asarray(first,float);first/=np.linalg.norm(first)
    second=np.asarray(second,float);second/=np.linalg.norm(second)
    return float(min(np.linalg.norm(first-second),np.linalg.norm(first+second)))


def verify_contract(source,source_binary,candidate,binary,delta):
    h.require(binary[:len(source_binary)]==source_binary,'Original BIN prefix changed')
    h.accessor_storage(candidate,binary)
    allowed={'R_'+digit+str(i) for digit in ('Thumb','Index','Mid','Ring','Pinky') for i in (1,2,3)}
    restored=copy.deepcopy(candidate)
    h.require(len(source['nodes'])==len(candidate['nodes']),'Node hierarchy changed')
    for index,node in enumerate(source['nodes']):
        if node['name'] in allowed:
            if 'rotation' in node:restored['nodes'][index]['rotation']=copy.deepcopy(node['rotation'])
            else:restored['nodes'][index].pop('rotation',None)
    h.require(len(source['animations'])==len(candidate['animations'])==1,'Grip animation count changed')
    a,b=source['animations'][0],candidate['animations'][0]
    h.require(a['name']==b['name']=='grip' and a['channels']==b['channels'],'Grip targets changed')
    h.require(len(a['channels'])==len(a['samplers'])==len(b['samplers'])==15,'Real15 finger channel layout changed')
    changed=[];new_outputs=[];maximum_delta_error=0.
    for channel in a['channels']:
        index=channel['sampler'];target=channel['target'];name=source['nodes'][target['node']]['name']
        h.require(name in allowed and target['path']=='rotation','Non-right-finger target')
        old,new=a['samplers'][index],b['samplers'][index]
        h.require({k:v for k,v in old.items() if k!='output'}=={k:v for k,v in new.items() if k!='output'},'Time/interpolation changed')
        old_values=h.values(source,source_binary,old['output'])
        new_values=h.values(candidate,binary,new['output'])
        h.require(old_values.shape==new_values.shape==(2,4),'Closed-only curve must retain2 quaternion rows')
        h.require(new_values[0].tobytes()==old_values[0].tobytes(),'Source open@0 changed: '+name)
        h.require(np.isfinite(new_values).all() and np.max(abs(np.linalg.norm(new_values,axis=1)-1))<1e-4,'Invalid closed quaternion')
        h.require(qdistance(candidate['nodes'][target['node']].get('rotation',[0,0,0,1]),new_values[1])<1e-6,'Default is not actual grip1 closed')
        modified=new_values[1].tobytes()!=old_values[1].tobytes()
        if modified:
            h.require(name in delta['changes'],'Modified closed track not declared')
            change=delta['changes'][name]
            h.require(qdistance(change['source_closed_xyzw'],old_values[1])<1e-6,'Delta source closed reference differs')
            expected=qmul(old_values[1],change['q_delta_post_xyzw'])
            error=qdistance(expected,new_values[1]);maximum_delta_error=max(maximum_delta_error,error)
            h.require(error<1e-6,'Incremental q is not source closed @ post delta once')
            changed.append(name);new_outputs.append(new['output'])
        else:
            h.require(old==new,'Unchanged finger unexpectedly repointed')
        restored['animations'][0]['samplers'][index]['output']=old['output']
    h.require(set(changed)==set(delta['changes']),'Declared/actual changed fingers differ')
    h.require(set(new_outputs)==set(range(len(source['accessors']),len(candidate['accessors']))),'Unexpected extra/reused output accessor')
    h.require(len(candidate['bufferViews'])-len(source['bufferViews'])==len(changed),'Unexpected appended views')
    restored['accessors']=restored['accessors'][:len(source['accessors'])]
    restored['bufferViews']=restored['bufferViews'][:len(source['bufferViews'])]
    restored['buffers']=copy.deepcopy(source['buffers'])
    h.require(restored==source,'Data outside allowed closed/default right-finger q changed')
    images=[]
    for index in range(len(source['images'])):
        a=h.image_bytes(source,source_binary,index);b=h.image_bytes(candidate,binary,index)
        h.require(a==b,'Actual KTX image payload changed')
        images.append(hashlib.sha256(b).hexdigest())
    return {'passed':True,'changed_closed_fingers':changed,'closed_track_count':len(changed),
            'all15_open0_rows_byte_exact':True,'source_original_BIN_prefix_exact':True,
            'all_nonpose_JSON_and_original_accessor_descriptors_exact':True,
            'root_wrist_bone_lengths_translation_scale_IBM_geometry_UV_material_KTX_and_left_bones_exact':True,
            'post_delta_applied_once_max_quaternion_chord_error':maximum_delta_error,'three_KTX_payload_sha256':images}


def pose_preservation(source,sb,candidate,binary):
    result=[]
    allowed={'R_'+digit+str(i) for digit in ('Thumb','Index','Mid','Ring','Pinky') for i in (1,2,3)}
    primitive=source['meshes'][0]['primitives'][0]
    palettes=h.values(source,sb,primitive['attributes']['JOINTS_0']).astype(int)
    weights=h.values(source,sb,primitive['attributes']['WEIGHTS_0'])
    names=[source['nodes'][i]['name'] for i in source['skins'][0]['joints']]
    influenced=sum(np.sum(weights*(palettes==i),axis=1) for i,name in enumerate(names) if name in allowed)>0
    for time in (0,.5,1):
        a=h.sampled_worlds(source,sb,'grip',time);b=h.sampled_worlds(candidate,binary,'grip',time)
        matrix_error=max(float(abs(a[i]-b[i]).max()) for i,node in enumerate(source['nodes']) if node['name'] not in allowed)
        h.require(matrix_error<1e-12,'Nonfinger/left/wrist/Grip matrix drifts')
        old=h.skin(source,sb,primitive,a);new=h.skin(candidate,binary,candidate['meshes'][0]['primitives'][0],b)
        protected=float(abs(old[~influenced]-new[~influenced]).max())
        h.require(protected<1e-12,'Uninfluenced original hand/palm/forearm moves')
        open_error=float(abs(old-new).max()) if time==0 else None
        if time==0:h.require(open_error<1e-12,'Actual skin at open0 changed beyond numeric evaluation roundoff')
        caps=[]
        for index,old_primitive in enumerate(source['meshes'][0]['primitives'][1:],1):
            old_cap=h.skin(source,sb,old_primitive,a);new_cap=h.skin(candidate,binary,candidate['meshes'][0]['primitives'][index],b)
            error=float(abs(old_cap-new_cap).max());h.require(error<1e-12,'Existing cuff cap moved')
            caps.append(error)
        result.append({'time':time,'all_nonfinger_and_left_bone_matrix_error':matrix_error,
                       'unaffected_skin_max_component_error_metres':protected,'open0_LBS_numeric_component_error_metres':open_error,'cuff_cap_skin_errors_metres':caps})
    default=h.sampled_worlds(candidate,binary);closed=h.sampled_worlds(candidate,binary,'grip',1)
    error=0.
    for primitive in candidate['meshes'][0]['primitives']:
        error=max(error,float(np.linalg.norm(h.skin(candidate,binary,primitive,default)-h.skin(candidate,binary,primitive,closed),axis=1).max()))
    h.require(error<1e-6,'Actual default skin not equal closed1')
    return {'poses':result,'actual_default_to_closed1_LBS_max_error_metres':error}


def contract_negative_tests(source,sb,candidate,binary,delta):
    rejected=[]
    for label in ('wrist_translation','open_row','KTX_byte'):
        changed=copy.deepcopy(candidate);payload=bytearray(binary)
        if label=='wrist_translation':
            node=next(n for n in changed['nodes'] if n['name']=='R_Hand')
            node['translation'][0]+=.001
        elif label=='open_row':
            sampler=changed['animations'][0]['samplers'][0]
            accessor=changed['accessors'][sampler['output']]
            view=changed['bufferViews'][accessor['bufferView']]
            offset=view.get('byteOffset',0)+accessor.get('byteOffset',0)
            payload[offset]^=1
        else:
            view=changed['bufferViews'][changed['images'][0]['bufferView']]
            payload[view.get('byteOffset',0)+100]^=1
        try:
            verify_contract(source,sb,changed,bytes(payload),delta)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError('Forbidden mutation accepted: '+label)
    return {'passed':True,'rejected':rejected,'scope':'Offline asset contract only; no SDK input/driver validation'}


def depth_distribution(values):
    inside=values<-1e-4
    return {'inside_samples':int(inside.sum()),'maximum_depth_mm':float(max(0,-values.min())),
            'inside_p95_depth_mm':float(np.percentile(-values[inside],95)) if inside.any() else 0.,
            'samples_deeper_than_mm':{str(t):int((values < -t).sum()) for t in (.25,1,2,5)}}


def comparative_diagnostics(source,sb,candidate,binary,baseline,actual):
    result={'same_sample_depth_distribution':{},'self_contact_comparison':{},
            'position_weld_self_contact':{'weld_epsilon_metres':1e-7,'scope':'Exclude physical shared-position vertices across legitimate UV/normal splits; original-index metric separately retained. These are surface intersection pairs, not penetration depth.','models':{}},
            'distal_other_finger_support':{}}
    table=baseline['sample_table']
    old_signed=np.array(baseline['signed_core_mm_by_sample'])
    new_signed=np.array(actual['signed_core_mm_by_sample'])
    for name in ('whole_right_hand','Thumb','Index','Mid','Ring','Pinky'):
        mask=np.ones(len(table),bool) if name=='whole_right_hand' else np.array([r['dominant_joint'].startswith('R_'+name) for r in table])
        result['same_sample_depth_distribution'][name]={'source':depth_distribution(old_signed[mask]),'candidate':depth_distribution(new_signed[mask])}
    for name,row in actual['self_contact']['pairs'].items():
        before=baseline['self_contact']['pairs'][name]
        a={tuple(pair) for pair in before['native_face_pairs']};b={tuple(pair) for pair in row['native_face_pairs']}
        result['self_contact_comparison'][name]={'source':before['confirmed_noncoplanar_pairs'],'candidate':row['confirmed_noncoplanar_pairs'],'kept_pairs':len(a&b),'added_native_face_pairs':sorted(b-a),'removed_native_face_pairs':sorted(a-b)}
    for label,document,data,payload in (('source',source,baseline,sb),('candidate',candidate,actual,binary)):
        points,faces,names,samples,rows=hand_samples(document,payload)
        _,weld=h.weld_positions(points,epsilon=1e-7)
        filtered={}
        for name,row in data['self_contact']['pairs'].items():
            pairs=[pair for pair in row['native_face_pairs'] if not(set(weld[faces[pair[0]]])&set(weld[faces[pair[1]]]))]
            filtered[name]={'confirmed_nonadjacent_after_position_weld':len(pairs),'native_face_pairs':pairs,'legal_weld_shared_vertex_pairs_excluded':row['confirmed_noncoplanar_pairs']-len(pairs)}
        result['position_weld_self_contact']['models'][label]=filtered
        attributes=document['meshes'][0]['primitives'][0]['attributes']
        palettes=h.values(document,payload,attributes['JOINTS_0']).astype(int)
        weights=h.values(document,payload,attributes['WEIGHTS_0'])
        support={}
        for digit,other in (('Pinky','Ring'),('Thumb','Index')):
            ids=[i for i,name in enumerate(names) if name.startswith('R_'+other)]
            influence=sum(np.sum(weights*(palettes==i),axis=1) for i in ids)
            other_faces=np.flatnonzero((influence[faces]>.5).any(axis=1))
            mask=np.array([row['dominant_joint']=='R_'+digit+'3' for row in rows])
            gap,_,_=nearest(samples[mask],points[faces[other_faces]])
            gap*=1000
            support[digit+'3_to_'+other]={'nearest_actual_surface_gap_mm':float(gap.min()),'samples_within_1mm':int((gap<=1).sum()),'samples_within_3mm':int((gap<=3).sum()),'scope':'Unsigned other-digit support proximity; self intersections separately reported.'}
        result['distal_other_finger_support'][label]=support
    return result


def verify_candidate(filename,expected_sha):
    baseline=json.loads((HERE/'baseline_contact.json').read_text())
    source,sb=h.read(NATIVE/'right_hand.glb')
    candidate,binary=h.read(filename)
    h.require(h.digest(NATIVE/'right_hand.glb')==BASELINE_SHA and h.digest(filename)==expected_sha,'Frozen source/candidate mismatch')
    delta=json.loads((HERE/'pose_delta.json').read_text())
    h.require(delta['source_sha256']==BASELINE_SHA,'Delta source model mismatch')
    report={'source_sha256':BASELINE_SHA,'candidate_sha256':expected_sha,'phase':'INDEPENDENT_CANDIDATE_CONTACT_AND_CONTRACT','errors':[]}
    try:
        report['structural_contract']=verify_contract(source,sb,candidate,binary,delta)
        report['pose_preservation']=pose_preservation(source,sb,candidate,binary)
        report['negative_contract_tests']=contract_negative_tests(source,sb,candidate,binary,delta)
        existing=json.loads((HERE/'verification.json').read_text()) if (HERE/'verification.json').exists() else {}
        actual=existing.get('candidate_contact') if existing.get('candidate_sha256')==expected_sha else None
        if actual is None:actual=contact(filename,expected_sha)
        h.require([(r['kind'],r['native_vertex_ids'],r['barycentric']) for r in baseline['sample_table']]==[(r['kind'],r['native_vertex_ids'],r['barycentric']) for r in actual['sample_table']],'Stable sample set changed')
        report['same7167_sample_identity_and_order']=True
        report['candidate_contact']=actual
        report['comparisons']={name:{'source':baseline['groups'][name],'candidate':actual['groups'][name]} for name in baseline['groups']}
        report.update(comparative_diagnostics(source,sb,candidate,binary,baseline,actual))
        if existing.get('candidate_sha256')==expected_sha:
            for key in ('Ring_Pinky_new_intersection_localization','extra_Pinky3_step_read_only_control'):
                if key in existing:report[key]=existing[key]
        decode=json.loads((HERE/'decode_manifest.json').read_text())
        companion=h.path(decode['output']['path'])
        h.require(decode['candidate_sha256']==expected_sha and h.digest(companion)==decode['output']['sha256'],'Decoded companion identity mismatch')
        cd,cb=h.read(companion)
        report['new_candidate_to_actual_decoded_companion']={'sha256':decode['output']['sha256'],'nonimage_equivalence':h.image_variant_equivalence(candidate,binary,cd,cb),'provenance_manifest_sha256':h.digest(HERE/'decode_manifest.json')}
    except Exception as error:
        report['errors'].append(str(error))
    report['stable_model_snapshot']=h.digest(NATIVE/'right_hand.glb')==BASELINE_SHA and h.digest(filename)==expected_sha
    report['verification_passed']=not report['errors'] and report['stable_model_snapshot']
    report['grip_quality_accepted']=False
    report['limits']=['Finite vertex/edge-mid/face-centroid samples do not prove continuous maximum; actual core is nonconvex.',
                      'Contact gap is not automatic floating-finger proof; support on other fingers and actual visibility remain Root PBR review.',
                      'Surface self-pair counts depend on the stated original-index adjacency/tolerance; compare this same canonical source/candidate metric.',
                      'No Blender/device/SDK/Gradle executed by this verifier.']
    (HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'candidate_sha256':expected_sha,'verification_passed':report['verification_passed'],'errors':report['errors']}))
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--sha256')
    args=parser.parse_args()
    if args.candidate:
        h.require(bool(args.sha256),'Candidate SHA is required')
        result=verify_candidate(args.candidate.resolve(),args.sha256)
        return 0 if result['verification_passed'] else 1
    controls=surface_control_tests()
    result=contact(NATIVE/'right_hand.glb',BASELINE_SHA)
    result['controls']=controls
    document,binary=h.read(NATIVE/'right_hand.glb')
    result['thumb_deepest_rotation_gradient']=witness_rotation_gradients(document,binary,result['deepest_samples'][0])
    (HERE/'baseline_contact.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sample_count':result['sample_count'],'groups':result['groups'],'joint3_origins':{n:p for n,p in result['finger_joint_origins_player_metres'].items() if n.endswith('3')}},indent=2))

if __name__=='__main__':
    raise SystemExit(main())
