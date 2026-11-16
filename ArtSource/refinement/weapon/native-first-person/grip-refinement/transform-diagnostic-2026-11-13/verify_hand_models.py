"""Actual GLB/skin/IBM/anatomical geometry diagnostic, without Blender or SDK.

Normal vectors below come from actual skinned triangle surfaces. Palmar-side
selection uses the observed skin flexion from open0 to closed1; it is an asset
reference, not a human-controller or SDK calibration.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import unittest

sys.dont_write_bytecode = True
import numpy as np
HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
REPO = HERE.parents[5]
sys.path.insert(0, str(NATIVE))
sys.path.insert(0, str(HERE.parent))
import verify_hands as h
import verify_grip as contact_helper

PINS = {
    'R': '3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0',
    'L': 'cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541',
    'dao': 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0',
}
LEFT_T = np.array([-.07659299626489029, -.03611927411734743, .015453077800029198])
LEFT_Q = np.array([.618749841086593, -.04408467375520302, -.7842483000710747, .012640392827866855])
DIGITS = ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')


def unit(vector):
    length = np.linalg.norm(vector)
    h.require(np.isfinite(vector).all() and length > 1e-12, 'Degenerate/nonfinite reference vector')
    return np.asarray(vector, float) / length


def pose_matrix(position, quaternion):
    h.require(np.isfinite(position).all() and np.isfinite(quaternion).all(), 'Nonfinite external pose')
    h.require(abs(np.linalg.norm(quaternion)-1) < 1e-8, 'External quaternion is not unit')
    result = h.quat_matrix(quaternion)
    result[:3, 3] = position
    return result


def side_influence(names, palettes, weights, prefix):
    ids = [i for i, name in enumerate(names) if name.startswith(prefix)]
    return sum(np.sum(weights * (palettes == i), axis=1) for i in ids)


def inspect_asset(document, binary, side):
    h.accessor_storage(document, binary)
    h.require(len(document.get('skins', [])) == 1, 'Require one real skin')
    skin = document['skins'][0]
    h.require(len(skin['joints']) == 78 and len(set(skin['joints'])) == 78, 'Invalid actual 78-joint palette')
    names = [document['nodes'][i]['name'] for i in skin['joints']]
    h.require(len(set(names)) == 78, 'Ambiguous bone names')
    inverse = h.values(document, binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    h.require(inverse.shape == (78, 4, 4) and np.isfinite(inverse).all(), 'Invalid actual IBM payload')
    h.require(np.all(np.linalg.det(inverse[:, :3, :3]) > 0), 'Reflected/singular IBM')
    determinants = []
    for node in document['nodes']:
        if 'scale' in node:
            h.require(np.all(np.asarray(node['scale']) > 0), 'Negative/zero node scale')
        if 'rotation' in node:
            q = np.array(node['rotation'])
            h.require(np.isfinite(q).all() and abs(np.linalg.norm(q)-1) < 1e-4, 'Invalid node quaternion')
        h.require(not ('matrix' in node and any(k in node for k in ('translation','rotation','scale'))), 'Mixed matrix/TRS')
        matrix = h.local(node)
        determinant = float(np.linalg.det(matrix[:3, :3]))
        h.require(np.isfinite(matrix).all() and determinant > 0, 'Mirrored/nonfinite/singular local transform')
        determinants.append(determinant)
    h.require(len(document['animations']) == 1 and document['animations'][0]['name'] == 'grip', 'Actual grip clip missing')
    clip = document['animations'][0]
    expected = {side+'_'+digit+str(i) for digit in DIGITS for i in (1,2,3)}
    actual = set()
    for channel in clip['channels']:
        node = document['nodes'][channel['target']['node']]['name']
        h.require(node in expected and channel['target']['path'] == 'rotation', 'Wrong-side/non-finger animation')
        actual.add(node)
        sampler = clip['samplers'][channel['sampler']]
        times = h.values(document,binary,sampler['input']).reshape(-1)
        q = h.values(document,binary,sampler['output'])
        h.require(np.array_equal(times, [0.,1.]) and q.shape == (2,4), 'Invalid grip endpoint storage')
        h.require(np.isfinite(q).all() and np.max(abs(np.linalg.norm(q,axis=1)-1)) < 1e-4, 'Invalid animation quaternion')
    h.require(len(clip['channels']) == 15 and actual == expected, 'Not actual 15-joint grip')
    worlds = {t: h.sampled_worlds(document,binary,'grip',t) for t in (0,1)}
    named = {t: {node['name']: worlds[t][i] for i,node in enumerate(document['nodes'])} for t in (0,1)}
    all_points = {0: [], 1: []}
    all_faces = []
    all_weights = []
    all_palettes = []
    offset = 0
    ibm_errors = []
    blend_determinants = []
    for node_index,node in enumerate(document['nodes']):
        if 'mesh' not in node:
            continue
        h.require(node.get('skin') == 0, 'Unskinned rendered hand mesh')
        mesh_world = worlds[0][node_index]
        rest_skin = np.array([worlds[0][i] for i in skin['joints']]) @ inverse
        error = float(abs(rest_skin - mesh_world).max())
        ibm_errors.append(error)
        # A GLB default/open pose is not necessarily its bind pose. Do not
        # mistake nonidentity skin matrices for an asset defect; the actual
        # IBM is instead checked finite/invertible, with real LBS below.
        for primitive in document['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            p = h.values(document,binary,attrs['POSITION'])
            faces = h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
            palettes = h.values(document,binary,attrs['JOINTS_0']).astype(int)
            weights = h.values(document,binary,attrs['WEIGHTS_0']).astype(float)
            h.require(palettes.shape == weights.shape == (len(p),4), 'Skin attribute count mismatch')
            h.require(np.isfinite(p).all() and np.isfinite(weights).all() and np.all(weights >= 0), 'Nonfinite/negative geometry or weights')
            h.require(palettes.min() >= 0 and palettes.max() < 78, 'Actual decoded JOINTS out of palette')
            h.require(np.max(abs(weights.sum(axis=1)-1)) < 1e-4, 'Weights not normalized')
            h.require(len(faces)>0 and faces.min()>=0 and faces.max()<len(p), 'Actual topology invalid')
            for time in (0,1):
                matrices=np.array([worlds[time][i] for i in skin['joints']])@inverse
                blended=np.sum(matrices[palettes]*weights[:,:,None,None],axis=1)
                determinants_skin=np.linalg.det(blended[:,:3,:3])
                h.require(np.isfinite(determinants_skin).all() and determinants_skin.min()>0,'Actual blended skin affine reflects or collapses geometry')
                blend_determinants.extend([float(determinants_skin.min()),float(determinants_skin.max())])
                points = h.skin(document,binary,primitive,worlds[time])
                h.require(np.isfinite(points).all(), 'Nonfinite actual LBS output')
                all_points[time].append(points)
            all_faces.append(faces + offset)
            all_weights.append(weights)
            all_palettes.append(palettes)
            offset += len(p)
    points = {t: np.concatenate(v) for t,v in all_points.items()}
    faces = np.concatenate(all_faces)
    weights, palettes = np.concatenate(all_weights), np.concatenate(all_palettes)
    used = np.unique(faces)
    dominant = palettes[np.arange(len(weights)), weights.argmax(axis=1)]
    actual_side = np.array([names[i].startswith(side+'_') for i in dominant[used]])
    h.require(actual_side.all(), 'Rendered surface dominant bones belong to wrong anatomical side')
    source_conversion = next(node for node in document['nodes'] if node['name'] == 'SourceHandRigidConversion')
    undo = np.linalg.inv(h.local(source_conversion))
    # Recover the common prepared body frame. Geometry, rather than the presence
    # of unused R/L bones, must occupy the matching side of the original body.
    source_open = (np.column_stack((points[0][used],np.ones(len(used)))) @ undo.T)[:,:3]
    hip = (undo @ np.r_[named[0]['Hip'][:3,3],1])[:3]
    offset_x = source_open[:,0] - hip[0]
    sign = -1 if side == 'R' else 1
    correct = sign*offset_x > 0
    h.require(correct.mean() > .99, 'Actual mesh lies on wrong common-body side: mirrored/relabelled geometry')
    wrist = named[0][side+'_Hand'][:3,3]
    mcp = np.mean([named[0][side+'_'+digit+'1'][:3,3] for digit in DIGITS[1:]],axis=0)
    forward = unit(mcp-wrist)
    radial = named[0][side+'_Index1'][:3,3]-named[0][side+'_Pinky1'][:3,3]
    radial = unit(radial-forward*(radial@forward))
    cross = unit(np.cross(radial,forward))
    finger_geometry = {}
    distal_motion = []
    for digit in DIGITS:
        influence = side_influence(names,palettes,weights,side+'_'+digit)
        mask = (influence>.5)
        h.require(mask.any(), 'Missing actual weighted '+digit+' geometry')
        finger_geometry[digit] = {t: points[t][mask].mean(axis=0) for t in (0,1)}
        if digit != 'Thumb':
            palette = names.index(side+'_'+digit+'3')
            distal = np.sum(weights*(palettes==palette),axis=1)>.5
            h.require(distal.any(), 'Missing distal mesh weighting')
            distal_motion.append((points[1][distal]-points[0][distal]).mean(axis=0))
    flex = np.mean(distal_motion,axis=0)
    flex_normal_component = float(flex@cross)
    h.require(abs(flex_normal_component) > .001, 'No measurable actual skin flexion side')
    palmar_reference = cross*np.sign(flex_normal_component)
    hand_palette = names.index(side+'_Hand')
    palm_weight = np.sum(weights*(palettes==hand_palette),axis=1)
    surface = {}
    for time in (0,1):
        triangles = points[time][faces]
        normal = np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        area = np.linalg.norm(normal,axis=1)*.5
        direction = normal/np.maximum(2*area[:,None],1e-30)
        centers = triangles.mean(axis=1)
        along = (centers-wrist)@forward
        length = np.linalg.norm(mcp-wrist)
        roi = (palm_weight[faces]>.5).any(axis=1) & (along>.1*length) & (along<1.1*length) & (area>1e-12)
        palmar = roi & (direction@palmar_reference>.35)
        dorsal = roi & (direction@palmar_reference<-.35)
        h.require(palmar.any() and dorsal.any(), 'Actual palm/dorsal skin surfaces unavailable')
        palm_n = unit(np.sum(normal[palmar],axis=0))
        dorsal_n = unit(np.sum(normal[dorsal],axis=0))
        surface[time] = {'palmar_normal':palm_n,'dorsal_normal':dorsal_n,
                         'palmar_center':np.average(centers[palmar],axis=0,weights=area[palmar]),
                         'dorsal_center':np.average(centers[dorsal],axis=0,weights=area[dorsal]),
                         'palmar_faces':int(palmar.sum()),'dorsal_faces':int(dorsal.sum()),
                         'signed_chirality':float(np.cross(radial,forward)@palm_n)}
    thumb_radial = float((finger_geometry['Thumb'][0]-mcp)@radial)
    h.require(thumb_radial > 0, 'Actual open thumb geometry is not on Index/radial side')
    expected_chirality = 1 if side=='R' else -1
    h.require(surface[0]['signed_chirality']*expected_chirality > .5, 'Skin-derived anatomical chirality inconsistent with side')
    summary = {
        'actual_78_palette_and_IBM_valid':True,'actual_blended_skin_determinant_range':[min(blend_determinants),max(blend_determinants)],'open_pose_is_not_assumed_to_equal_bind_pose':True,'maximum_open_skin_vs_mesh_world_difference_not_a_bind_pose_requirement':max(ibm_errors),
        'all_local_transform_determinants_positive':True,'local_determinant_range':[min(determinants),max(determinants)],
        'actual_referenced_surface_vertices':len(used),'triangles':len(faces),
        'dominant_geometry_bones':{name:int((dominant[used]==i).sum()) for i,name in enumerate(names) if np.any(dominant[used]==i)},
        'correct_common_source_body_side_fraction':float(correct.mean()),'common_body_relative_x_range': [float(offset_x.min()),float(offset_x.max())],
        'actual_open_thumb_radial_offset_metres':thumb_radial,'skin_distal_open_closed_mean_displacement':flex.tolist(),
        'skin_flexion_dot_radial_cross_forward_metres':flex_normal_component,
        'anatomy_method':'Actual referenced skin, weighted geometry centroids, bone origins, and observed flexion side; palm/dorsal actual area-normal clusters. Does not establish a human/SDK calibration.',
    }
    return {'summary':summary,'named':named,'points':points,'faces':faces,'forward':forward,'radial':radial,
            'surface':surface,'finger_geometry':finger_geometry}


def transformed_point(matrix, point):
    return (matrix@np.r_[point,1])[:3].tolist()


def world_reference(asset, side, root, time):
    named = asset['named'][time]
    surface = asset['surface'][time]
    rotation = root[:3,:3]
    wrist = named[side+'_Hand'][:3,3]
    return {
        'hand_root_world_rowmajor':root.tolist(),'root_determinant':float(np.linalg.det(rotation)),
        'wrist_world':transformed_point(root,wrist),
        'finger_joint_world':{digit:[transformed_point(root,named[side+'_'+digit+str(i)][:3,3]) for i in (1,2,3)] for digit in DIGITS},
        'actual_skin_finger_centroids_world':{digit:transformed_point(root,asset['finger_geometry'][digit][time]) for digit in DIGITS},
        'wrist_to_MCP_fingers_unit_world':unit(rotation@asset['forward']).tolist(),
        'thumb_index_radial_unit_world':unit(rotation@asset['radial']).tolist(),
        'actual_geometric_palmar_normal_world':unit(rotation@surface['palmar_normal']).tolist(),
        'actual_geometric_dorsal_normal_world':unit(rotation@surface['dorsal_normal']).tolist(),
        'palmar_surface_center_world':transformed_point(root,surface['palmar_center']),
        'signed_chirality':float(surface['signed_chirality']),
        'palmar_dorsal_normal_selection_scope':'Actual surface clusters selected by measured skin flexion side, not image semantic labels or raw SDK pose physiology.'}


def run_audit():
    mapping_path = HERE/'runtime_mapping.json'
    mapping = json.loads(mapping_path.read_text())
    h.require(h.digest(mapping_path)=='187dd700f34ed50ab6af3e47c5b76a5923a3f03535fa685101a77a33982be9ba','Runtime mapping snapshot differs')
    offset = pose_matrix(LEFT_T,LEFT_Q)
    h.require(np.allclose(offset,mapping['hand_root_from_grip_gltf']['L'],atol=1e-12), 'Provided constants and mapping disagree')
    h.require(np.allclose(mapping['hand_root_from_grip_gltf']['R'],np.eye(4),atol=1e-12),'Right root mapping is not G')
    assets = {}
    inputs = {}
    loaded = {}
    for side,name in [('R','right'),('L','left')]:
        filename=REPO/'app/src/main/assets/models/player_hands'/(name+'_hand.glb')
        h.require(h.digest(filename)==PINS[side],'Pinned formal hand changed')
        d,b=h.read(filename)
        assets[side]=inspect_asset(d,b,side)
        loaded[side]=(d,b)
        inputs[side]={'path':str(filename.relative_to(REPO)),'sha256':PINS[side]}
    dao=REPO/'app/src/main/assets/models/dao_grip.glb'
    h.require(h.digest(dao)==PINS['dao'],'Formal dao changed')
    # Nontrivial proper rotation built from Euler-axis quaternions in xyzw.
    def axis_q(axis,angle):return np.r_[np.asarray(axis)*math.sin(angle/2),math.cos(angle/2)]
    def multiply(a,b):
        q=np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]),a[3]*b[3]-a[:3]@b[:3]]
        return q/np.linalg.norm(q)
    rotated=multiply(multiply(axis_q([0,1,0],math.radians(60)),axis_q([1,0,0],math.radians(-25))),axis_q([0,0,1],math.radians(15)))
    scenarios=[('identity',np.zeros(3),np.array([0.,0,0,1])),('proper_rotated',np.array([1.25,1.4,-2.1]),rotated)]
    result={'input_assets':inputs,'dao_sha256':PINS['dao'],'runtime_mapping_sha256':h.digest(mapping_path),
            'asset_checks':{side:asset['summary'] for side,asset in assets.items()},'scenarios':[],
            'scope':'Offline actual GLB/skin/IBM/anatomy references, no tests of SDK tracking/pose conventions and no images/Blender/device execution.'}
    for label,p,q in scenarios:
        G=pose_matrix(p,q)
        root={'R':G,'L':G@offset}
        data={'name':label,'synthetic_finalGrip_position':p.tolist(),'synthetic_finalGrip_rotation_xyzw':q.tolist(),
              'note':'Same declared synthetic finalGrip is supplied to each side for comparison; it is not asserted to be a physiological raw SDK ControllerPose.', 'poses':{}}
        for time in (0,1):
            data['poses'][str(time)]={side:world_reference(assets[side],side,root[side],time) for side in ('R','L')}
        derived=assets['L']['named'][0]['DerivedHandGrip_L']@h.rotation_x(math.pi/2)
        reconnected=root['L']@h.rigid(derived)
        data['derived_anchor_algebra_only']={'maximum_matrix_difference_from_G':float(abs(reconnected-G).max()),
            'warning':'Algebraic DerivedHandGrip_L reconnection only; not authored anatomical contact, optical fit or SDK calibration.'}
        result['scenarios'].append(data)
    core,core_faces,core_topology=actual_dao_core()
    result['actual_closed_core_contact']={'formal_dao_sha256':PINS['dao'],'actual_core_topology':core_topology,'core_bounds_Grip_metres':[core.min(axis=0).tolist(),core.max(axis=0).tolist()],'hands':{side:closed_core_contact(*loaded[side],side,np.eye(4) if side=='R' else offset,core,core_faces) for side in ('R','L')}}
    result['contact_interpretation']='Bone/IBM/quaternion/TRS and intrinsic chirality consistency do not establish physiological correctness of derived closed1. A proper rigid Left offset preserves pairwise distances and triangle area; it cannot itself create local skin tearing, while it can change alignment relative to the dao. Signed core overlap is reported independently.'
    result['definite_contact_overlap_detected']=any(record['summary']['maximum_sampled_penetration_mm']>.001 for record in result['actual_closed_core_contact']['hands'].values())
    result['numeric_asset_consistency_passed']=True
    result['SDK_calibration_claimed']=False
    return result


def actual_dao_core():
    filename=REPO/'app/src/main/assets/models/dao_grip.glb'
    h.require(h.digest(filename)==PINS['dao'],'Actual contact dao pin changed')
    document,binary=h.read(filename)
    world=h.sampled_worlds(document,binary)
    index,node=next((i,n) for i,n in enumerate(document['nodes']) if n.get('name')=='Handle core')
    points=[];faces=[];offset=0
    for primitive in document['meshes'][node['mesh']]['primitives']:
        p=h.values(document,binary,primitive['attributes']['POSITION']).astype(float)
        p=(np.column_stack((p,np.ones(len(p))))@world[index].T)[:,:3]
        f=h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
        points.append(p);faces.append(f+offset);offset+=len(p)
    points,faces=np.concatenate(points),np.concatenate(faces)
    topology,_,_=h.edge_topology(points,faces)
    h.require(topology['open_edges']==topology['nonmanifold_edges']==0,'Actual Handle core is not closed')
    return points,faces,topology


def signed_actual_surface(points,triangles):
    gap,ids,nearest=contact_helper.nearest(points,triangles)
    inside=np.array([contact_helper.contains(point,triangles) if distance>1e-7 else False for point,distance in zip(points,gap)])
    signed=gap*np.where(inside,-1,1)*1000
    signed[gap<=1e-7]=0
    return signed,ids,nearest


def contact_summary(values):
    inside=values<-1e-4
    return {'samples':len(values),'inside_samples':int(inside.sum()),
            'maximum_sampled_penetration_mm':float(max(0,-values.min())),
            'inside_depth_p95_mm':float(np.percentile(-values[inside],95)) if inside.any() else 0.,
            'positive_outside_samples':int((values>1e-4).sum()),
            'depth_count_thresholds_mm':{str(value):int((values < -value).sum()) for value in (.25,1,2,5)}}


def closed_core_contact(document,binary,side,root,core,core_faces):
    primitive=document['meshes'][0]['primitives'][0]
    attributes=primitive['attributes']
    world0=h.sampled_worlds(document,binary,'grip',0)
    world1=h.sampled_worlds(document,binary,'grip',1)
    open_points=h.skin(document,binary,primitive,world0)
    closed_points=h.skin(document,binary,primitive,world1)
    open_points=(np.column_stack((open_points,np.ones(len(open_points))))@root.T)[:,:3]
    closed_points=(np.column_stack((closed_points,np.ones(len(closed_points))))@root.T)[:,:3]
    faces=h.values(document,binary,primitive['indices']).reshape(-1,3).astype(int)
    joints=h.values(document,binary,attributes['JOINTS_0']).astype(int)
    weights=h.values(document,binary,attributes['WEIGHTS_0']).astype(float)
    names=[document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    included=[i for i,name in enumerate(names) if name==side+'_Hand' or name.startswith(tuple(side+'_'+digit for digit in DIGITS))]
    influence=sum(np.sum(weights*(joints==i),axis=1) for i in included)
    vertices=np.flatnonzero(influence>.5)
    face_ids=np.flatnonzero((influence[faces]>.5).any(axis=1))
    chosen=faces[face_ids]
    points=np.concatenate((closed_points[vertices],closed_points[chosen].mean(axis=1)))
    old=np.concatenate((open_points[vertices],open_points[chosen].mean(axis=1)))
    dense=np.zeros((len(closed_points),78))
    for slot in range(4):np.add.at(dense,(np.arange(len(closed_points)),joints[:,slot]),weights[:,slot])
    sample_weights=np.concatenate((dense[vertices],dense[chosen].mean(axis=1)))
    dominant=np.argmax(sample_weights,axis=1)
    signed,near_faces,nearest=signed_actual_surface(points,core[core_faces])
    source_ids=np.load(NATIVE/'selection.npz')
    original_vertices=source_ids[side+'_p0_source_vertex_ids']
    original_faces=source_ids[side+'_p0_source_face_ids']
    table=[]
    for vertex in vertices:table.append({'kind':'actual_skin_vertex','native_vertex_ids':[int(vertex)],'native_face_ids':[],'source_vertex_ids':[int(original_vertices[vertex])],'barycentric':[1.]})
    for face_id,triangle in zip(face_ids,chosen):table.append({'kind':'actual_skin_face_centroid','native_vertex_ids':triangle.tolist(),'native_face_ids':[int(face_id)],'source_face_ids':[int(original_faces[face_id])],'source_vertex_ids':original_vertices[triangle].tolist(),'barycentric':[1/3]*3})
    for i,row in enumerate(table):row.update(sample_index=i,dominant_joint=names[int(dominant[i])])
    groups={}
    for digit in DIGITS:
        mask=np.array([row['dominant_joint'].startswith(side+'_'+digit) for row in table])
        groups[digit]=contact_summary(signed[mask])
    thumb=np.array([row['dominant_joint'].startswith(side+'_Thumb') for row in table])
    witnesses=[]
    for index in np.flatnonzero(thumb)[np.argsort(signed[thumb])[:12]]:
        witnesses.append({**table[index], 'point_common_Grip_metres':points[index].tolist(),
            'source_open_point_common_Grip_metres':old[index].tolist(),
            'open_closed_skin_displacement_mm':float(np.linalg.norm(points[index]-old[index])*1000),
            'signed_core_distance_mm':float(signed[index]),'nearest_actual_core_point_metres':nearest[index].tolist(),
            'nearest_core_triangle':int(near_faces[index]),
            'actual_skin_support':{names[i]:float(w) for i,w in enumerate(sample_weights[index]) if w>1e-5}})
    tri0,tri1=open_points[chosen],closed_points[chosen]
    area0=np.linalg.norm(np.cross(tri0[:,1]-tri0[:,0],tri0[:,2]-tri0[:,0]),axis=1)*.5
    area1=np.linalg.norm(np.cross(tri1[:,1]-tri1[:,0],tri1[:,2]-tri1[:,0]),axis=1)*.5
    thumb_faces=np.array([any(names[int(i)].startswith(side+'_Thumb') and w>.5 for vertex in face for i,w in zip(joints[vertex],weights[vertex])) for face in chosen])
    ratio=area1[thumb_faces]/np.maximum(area0[thumb_faces],1e-30)
    native_triangles=h.skin(document,binary,primitive,world1)[chosen]
    native_areas=np.linalg.norm(np.cross(native_triangles[:,1]-native_triangles[:,0],native_triangles[:,2]-native_triangles[:,0]),axis=1)*.5
    rigid_area_error=float(abs(area1-native_areas).max())
    return {'pose':'actual grip@1 skin, runtime root from declared neutral finalGrip G=I',
            'actual_root_from_Grip_rowmajor':root.tolist(),'summary':contact_summary(signed),'by_digit':groups,
            'Thumb_actual_vertex_samples':int(sum(thumb[:len(vertices)])),'Thumb_actual_face_centroid_samples':int(sum(thumb[len(vertices):])),
            'Thumb_worst_actual_samples':witnesses,
            'rigid_root_preserves_closed_triangle_area_max_error_m2':rigid_area_error,
            'Thumb_open_closed_triangle_area_ratio':{'minimum':float(ratio.min()),'maximum':float(ratio.max()),'scope':'Actual face area ratio, not tissue thickness or penetration depth'},
            'sample_table':table,'signed_actual_core_distance_mm_by_sample':np.round(signed,6).tolist(),
            'metric':'Negative = classified inside actual closed Handle core by generalized winding and actual nearest finite triangle distance. Zero boundary epsilon=1e-7m; positive = outside.',
            'scope':'Finite mesh vertices and face centroids, no continuous maximum proof. No unsigned-gap-to-penetration inference. No solver, asset edits or SDK calibration.'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tests',action='store_true')
    args=parser.parse_args()
    result=run_audit()
    if args.tests:
        suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_*.py')
        tests=unittest.TextTestRunner(verbosity=2).run(suite)
        result['tests']={'ran':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'passed':tests.wasSuccessful(),'scope':'Actual pinned R/L GLBs, normal +6 damaged boundary cases in RAM only'}
        h.require(tests.wasSuccessful(),'Boundary tests failed')
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'numeric_asset_consistency_passed':result['numeric_asset_consistency_passed'],
                      'chirality':{s:result['scenarios'][0]['poses']['0'][s]['signed_chirality'] for s in ('R','L')},
                      'identity_world':{s:{k:v for k,v in result['scenarios'][0]['poses']['0'][s].items() if k in ['wrist_world','wrist_to_MCP_fingers_unit_world','thumb_index_radial_unit_world','actual_geometric_palmar_normal_world']} for s in ('R','L')},'closed_core':{side:record['by_digit']['Thumb'] for side,record in result['actual_closed_core_contact']['hands'].items()}},indent=2))

if __name__=='__main__':
    main()
