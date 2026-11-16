"""Build a wide grounded overhead stance and its continuous attack candidate."""

import argparse
import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parent
CANDIDATE = HERE / 'candidate'
sys.path.insert(0, str(STAGE3))
import build_keyposes as author
from mathutils import Matrix, Quaternion, Vector
import numpy as np

SOURCE_PINS = {
    STAGE3 / 'build_keyposes.py': '37a77531631e9cd883750b92ea6c9f1d5c3d4c64c7aed6dd7768094e1aad892e',
    STAGE3 / 'verify_keyposes.py': '4d73e98e5d64077e5c32d76fe651230e4d24f3936d6b0a6e3e89950ff0193aff',
    STAGE3 / 'candidate/keypose_parameters.json': 'ea696085c971283e1cdc0b6065d031cf4d2e6be18f9b099370e26b02d817f2d0',
    STAGE3 / 'candidate/metadata.json': '80e6fbb16746aacd2c3f4f729b7bb578235083339ac0c1da336a40bee87e08cb',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_path(name):
    path = CANDIDATE / name
    if path.resolve().parent != CANDIDATE.resolve():
        raise ValueError('stage4 output escaped candidate')
    return path


def load_inputs():
    for path, expected in SOURCE_PINS.items():
        if digest(path) != expected:
            raise ValueError('frozen stage3 source changed: ' + path.name)
    return author.load_inputs()


def validate_controls(parameters):
    author.validate_parameters(parameters)
    settings = parameters['stage4']
    for key in ('hip_yaw_degrees','shoulder_extra_yaw_degrees'):
        if len(settings[key]) != 5 or not all(math.isfinite(value) for value in settings[key]):
            raise ValueError('five finite body yaw controls are required')
    if len(settings['hip_targets_metres']) != 5:
        raise ValueError('five hip targets are required')
    for row in settings['hip_targets_metres']:
        if len(row) != 3 or not all(math.isfinite(value) for value in row):
            raise ValueError('hip target must have three finite values')
    for side in ('L_','R_'):
        if not all(math.isfinite(value) for value in settings['foot_centres_metres'][side]):
            raise ValueError('foot centres must be finite')
        if not math.isfinite(settings['foot_splay_degrees'][side]):
            raise ValueError('foot splay must be finite')
    if not 30 <= settings['sample_rate_hz'] <= 120:
        raise ValueError('sample rate must stay within the offline authoring range')


def foot_geometry(rig, binary):
    joints = rig['skins'][0]['joints']
    names = [rig['nodes'][index]['name'] for index in joints]
    bind = author.accessor(rig, binary, rig['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    primitive = next(rig['meshes'][node['mesh']]['primitives'][0] for node in rig['nodes'] if 'skin' in node)
    attributes = primitive['attributes']
    positions = author.accessor(rig,binary,attributes['POSITION']).astype(float)
    palettes = author.accessor(rig,binary,attributes['JOINTS_0']).astype(int)
    weights = author.accessor(rig,binary,attributes['WEIGHTS_0']).astype(float)
    weights /= weights.sum(axis=1)[:,None]
    triangles = author.accessor(rig,binary,primitive['indices']).reshape(-1,3).astype(int)
    node_names = {node.get('name'):index for index,node in enumerate(rig['nodes'])}
    regions = {}
    for side in ('L_', 'R_'):
        palette = [index for index,name in enumerate(names) if name in {side+'Foot',side+'ToeBase'}]
        mask = sum(np.sum(weights*(palettes==index),axis=1) for index in palette) > .5
        if not mask.any():
            raise ValueError('weighted shoe region absent')
        remap = np.full(len(positions),-1,dtype=int)
        remap[mask] = np.arange(mask.sum())
        faces = remap[triangles[mask[triangles].all(axis=1)]]
        regions[side] = {'positions':positions[mask],'palettes':palettes[mask],'weights':weights[mask],
                         'faces':faces,'foot_index':node_names[side+'Foot'],'toe_index':node_names[side+'ToeBase'],
                         'heel_mask':None,'front_mask':None}
    return joints,bind,regions


def foot_measurements(geometry, world, norm):
    joints,bind,regions = geometry
    transforms = np.array([list(world[index]) for index in joints]) @ bind
    result = {}
    for side,region in regions.items():
        positions,palettes,weights = region['positions'],region['palettes'],region['weights']
        blended = np.sum(transforms[palettes]*weights[:,:,None,None],axis=1)
        points = np.einsum('vij,vj->vi',blended,np.column_stack((positions,np.ones(len(positions)))))
        points = (points @ np.array(norm).T)[:,:3]
        low,high = points.min(axis=0),points.max(axis=0)
        forward = (norm@world[region['toe_index']]).translation-(norm@world[region['foot_index']]).translation
        forward.y = 0
        forward.normalize()
        along = points @ np.array(forward)
        if region['heel_mask'] is None:
            width = along.max()-along.min()
            region['heel_mask'] = along <= along.min()+.25*width
            region['front_mask'] = along >= along.max()-.25*width
        heel_min = float(points[region['heel_mask'],1].min())
        front_min = float(points[region['front_mask'],1].min())
        covariance = np.cov(points[:,[0,2]],rowvar=False)
        _,axes = np.linalg.eigh(covariance)
        shoe_axis = Vector((axes[0,-1],0,axes[1,-1]))
        if shoe_axis.dot(forward)<0:
            shoe_axis = -shoe_axis
        heading = math.degrees(math.atan2(shoe_axis.x,shoe_axis.z))
        faces = points[region['faces']]
        normals = np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
        lengths = np.linalg.norm(normals,axis=1)
        valid = (lengths>1e-12)&(normals[:,1]/np.maximum(lengths,1e-12)<-.6)&(faces.mean(axis=1)[:,1]<low[1]+.1)
        normal = normals[valid].sum(axis=0)
        normal /= np.linalg.norm(normal)
        lateral = np.array((forward.z,0,-forward.x))
        roll = math.degrees(math.atan2(float(normal@lateral),float(-normal[1])))
        result[side] = {'centre_metres':[(low[0]+high[0])/2,low[1],(low[2]+high[2])/2],
                        'sole_height_metres':float(low[1]),'surface_vertex_count':len(positions),
                        'heel_minimum_metres':heel_min,'front_minimum_metres':front_min,
                        'heel_front_height_difference_metres':heel_min-front_min,
                        'actual_shoe_pca_heading_degrees':heading,'sole_normal_roll_degrees':roll,
                        'sole_area_weighted_normal':normal.tolist()}
    return result


def solve_leg(rig, local, side, target, pole, names, parents, order):
    mapped = dict(names)
    for arm,leg in [('Upperarm','Thigh'),('Forearm','Calf'),('Hand','Foot')]:
        mapped[side+arm] = names[side+leg]
    return author.solve_arm(rig,local,side,target,pole,mapped,parents,order)


def ground_legs(rig, local, geometry, feet, foot_rotations, parameters, norm, names, parents, order):
    inverse = norm.inverted()
    targets = {side:Vector(feet[side]) for side in feet}
    for _ in range(5):
        for side in ('L_', 'R_'):
            pole = inverse @ Vector(parameters['leg_poles_metres'][side])
            solve_leg(rig,local,side,inverse@targets[side],pole,names,parents,order)
            world = author.worlds(rig,local,parents,order)
            author.set_world_rotation(local,names[side+'Foot'],foot_rotations[side],world,parents)
        world = author.worlds(rig,local,parents,order)
        measured = foot_measurements(geometry,world,norm)
        maximum = 0.0
        for side in ('L_', 'R_'):
            desired = parameters['foot_centres_metres'][side]
            centre = measured[side]['centre_metres']
            error = Vector((desired[0]-centre[0],-centre[1],desired[2]-centre[2]))
            maximum = max(maximum,error.length)
            targets[side] += error
        if maximum < 2e-6:
            break
    if maximum > 2e-5:
        raise ValueError('actual shoe-surface grounding did not converge')
    return measured


def gaze(rig, local, norm, look_target, rest_world, names, parents, order):
    for name in ('NeckTwist01','NeckTwist02','Head'):
        world = author.worlds(rig,local,parents,order)
        author.set_world_rotation(local,names[name],rest_world[names[name]].to_quaternion(),world,parents)
    world = author.worlds(rig,local,parents,order)
    head = (norm@world[names['Head']]).translation
    look = norm.inverted().to_3x3() @ (Vector(look_target)-head)
    delta = Vector((1,0,0)).rotation_difference(look.normalized())
    author.set_world_rotation(local,names['Head'],delta@rest_world[names['Head']].to_quaternion(),world,parents)


def solve_upper(rig, local, pose, hand_rotations, norm, names, parents, order):
    inverse = norm.inverted()
    for side,key,pole in [('R_','right_hand_metres','right_elbow_pole_metres'),('L_','left_hand_metres','left_elbow_pole_metres')]:
        author.solve_arm(rig,local,side,inverse@Vector(pose[key]),inverse@Vector(pose[pole]),names,parents,order)
        world = author.worlds(rig,local,parents,order)
        author.set_world_rotation(local,names[side+'Hand'],hand_rotations[side],world,parents)


def build_v2(rig,binary,idle,idle_binary,slash,slash_binary,snapshot,parameters):
    validate_controls(parameters)
    base,_,blade,_ = author.author_poses(rig,idle,idle_binary,slash,slash_binary,snapshot,parameters)
    parents,order = author.library.node_order(rig)
    names = {node.get('name'):index for index,node in enumerate(rig['nodes'])}
    norm = author.library.local_matrix({'matrix':snapshot['stage1_alignment']['normalization_matrix_gltf']})
    inverse = norm.inverted()
    rest = {index:list(author.library.local_matrix(node).decompose()) for index,node in enumerate(rig['nodes'])}
    rest_world = author.worlds(rig,rest,parents,order)
    geometry = foot_geometry(rig,binary)
    settings = parameters['stage4']
    # Freeze the analyzer's quarter-foot regions before its final levelling pitch.
    roi_pose = copy.deepcopy(base[0])
    normalization_rotation = norm.to_quaternion().normalized()
    for side in ('L_','R_'):
        yaw = math.radians(settings['foot_splay_degrees'][side])
        lateral = Vector((math.cos(yaw),0,-math.sin(yaw)))
        pitch = Quaternion(lateral,math.radians(settings['heel_front_levelling_pitch_degrees'][side]))
        flat_yaw = pitch.inverted()@Quaternion(settings['flattened_prepared_foot_quaternions'][side])
        world = author.worlds(rig,roi_pose,parents,order)
        author.set_world_rotation(roi_pose,names[side+'Foot'],normalization_rotation.inverted()@flat_yaw,world,parents)
    foot_measurements(geometry,author.worlds(rig,roi_pose,parents,order),norm)
    result = []
    for index,(local,pose) in enumerate(zip(base,parameters['poses'])):
        world = author.worlds(rig,local,parents,order)
        hands = {side:world[names[side+'Hand']].to_quaternion() for side in ('L_','R_')}
        normalization_rotation = norm.to_quaternion().normalized()
        rotations = {side:normalization_rotation.inverted()@Quaternion(settings['flattened_prepared_foot_quaternions'][side])
                     for side in ('L_','R_')}
        feet = copy.deepcopy(settings['initial_ankle_targets_metres'])
        current_hip = (norm@world[names['Hip']]).translation
        hip_shift = Vector(settings['hip_targets_metres'][index])-current_hip
        local[names['BoneRoot']][0] += inverse.to_3x3()@hip_shift
        world = author.worlds(rig,local,parents,order)
        upright = world
        yaw_axis = (inverse.to_3x3()@Vector((0,1,0))).normalized()
        hip_forward_local = rest_world[names['Hip']].to_quaternion().inverted()@Vector((1,0,0))
        hip_forward = norm.to_3x3()@(world[names['Hip']].to_quaternion()@hip_forward_local)
        idle_heading = math.degrees(math.atan2(hip_forward.x,hip_forward.z))
        hip_delta = Quaternion(yaw_axis,math.radians(settings['hip_yaw_degrees'][index]-idle_heading))
        author.set_world_rotation(local,names['Hip'],hip_delta@world[names['Hip']].to_quaternion(),world,parents)
        for name,fraction in [('Waist',.2),('Spine01',.6),('Spine02',1.0)]:
            world = author.worlds(rig,local,parents,order)
            total_yaw = settings['hip_yaw_degrees'][index]+settings['shoulder_extra_yaw_degrees'][index]*fraction
            delta = Quaternion(yaw_axis,math.radians(total_yaw))
            author.set_world_rotation(local,names[name],delta@upright[names[name]].to_quaternion(),world,parents)
        ground_legs(rig,local,geometry,feet,rotations,settings,norm,names,parents,order)
        solve_upper(rig,local,pose,hands,norm,names,parents,order)
        gaze(rig,local,norm,parameters['look_target_metres'],rest_world,names,parents,order)
        result.append(local)
    result[-1] = copy.deepcopy(result[0])
    context = rig,geometry,norm,names,parents,order,rest_world
    return result,blade,context


def phase_amount(time, times):
    for index,(start,end) in enumerate(zip(times,times[1:])):
        if time <= end:
            amount = max(0,min(1,(time-start)/(end-start)))
            if index == 1:
                return index,amount*amount
            if index == 2:
                return index,1-(1-amount)*(1-amount)
            return index,amount*amount*(3-2*amount)
    return len(times)-2,1.0


def dense_poses(keyposes,parameters,context):
    rig,geometry,norm,names,parents,order,rest_world = context
    times = [pose['time_seconds'] for pose in parameters['poses']]
    rate = parameters['stage4']['sample_rate_hz']
    sampled = sorted({*times,*[frame/rate for frame in range(round(times[-1]*rate)+1)]})
    result = []
    key_worlds = [author.worlds(rig,pose,parents,order) for pose in keyposes]
    for time in sampled:
        index,amount = phase_amount(time,times)
        phase = max(0,min(1,(time-times[index])/(times[index+1]-times[index])))
        if index in (1,2):
            body_amount = 1-(1-phase)*(1-phase)
        else:
            early = min(1,phase*1.12)
            body_amount = early*early*(3-2*early)
        a,b = keyposes[index:index+2]
        local = {node:[a[node][0].lerp(b[node][0],body_amount),a[node][1].slerp(b[node][1],body_amount),
                       a[node][2].lerp(b[node][2],body_amount)] for node in a}
        for name in author.RIGHT_FINGERS:
            local[names[name]] = copy.deepcopy(keyposes[0][names[name]])
        pose = copy.deepcopy(parameters['poses'][index])
        for key in ('right_hand_metres','left_hand_metres','right_elbow_pole_metres','left_elbow_pole_metres'):
            pose[key] = list(Vector(parameters['poses'][index][key]).lerp(Vector(parameters['poses'][index+1][key]),amount))
        world = author.worlds(rig,local,parents,order)
        feet = {side:list((norm@world[names[side+'Foot']]).translation) for side in ('L_','R_')}
        feet_rotations = {side:key_worlds[0][names[side+'Foot']].to_quaternion() for side in ('L_','R_')}
        hand_rotations = {side:key_worlds[index][names[side+'Hand']].to_quaternion().slerp(
            key_worlds[index+1][names[side+'Hand']].to_quaternion(),amount) for side in ('L_','R_')}
        ground_legs(rig,local,geometry,feet,feet_rotations,parameters['stage4'],norm,names,parents,order)
        solve_upper(rig,local,pose,hand_rotations,norm,names,parents,order)
        gaze(rig,local,norm,parameters['look_target_metres'],rest_world,names,parents,order)
        result.append(local)
    return result,sampled


def metrics(poses,times,parameters,blade,context):
    rig,geometry,norm,names,parents,order,rest_world = context
    result = []
    for local,time in zip(poses,times):
        world = author.worlds(rig,local,parents,order)
        hip = (norm@world[names['Hip']]).translation
        hand = norm@world[names['R_Hand']]
        head = (norm@world[names['Head']]).translation
        row = {'time_seconds':time,'hip_metres':list(hip),'head_metres':list(head),
               'right_hand_metres':list(hand.translation),'left_hand_metres':list((norm@world[names['L_Hand']]).translation),
               'blade_tip_metres':list(hand@Vector(blade['tip_local'])),'blade_base_metres':list(hand@Vector(blade['base_local'])),
               'foot_surfaces':foot_measurements(geometry,world,norm),'knee_flexion_degrees':{}}
        row['label'] = next((pose['label'] for pose in parameters['poses'] if pose['time_seconds']==time),'sample')
        row['feet_world_gltf_m'] = {label:row['foot_surfaces'][side]['centre_metres'] for label,side in [('left','L_'),('right','R_')]}
        row['foot_surface_heights_metres'] = {side:row['foot_surfaces'][side]['sole_height_metres'] for side in ('L_','R_')}
        row['body_yaw_degrees'] = {}
        for name in ('Hip','Spine02'):
            forward_local = rest_world[names[name]].to_quaternion().inverted()@Vector((1,0,0))
            forward = (norm.to_3x3()@(world[names[name]].to_quaternion()@forward_local)).normalized()
            row['body_yaw_degrees'][name] = math.degrees(math.atan2(forward.x,forward.z))
        for side in ('L_','R_'):
            thigh,knee,foot = [world[names[side+name]].translation for name in ('Thigh','Calf','Foot')]
            cosine = (thigh-knee).normalized().dot((foot-knee).normalized())
            row['knee_flexion_degrees'][side] = 180-math.degrees(math.acos(max(-1,min(1,cosine))))
        result.append(row)
    return result


def main(dense=False):
    prefix = 'overhead' if dense else 'overhead_v2_keyposes'
    output_path(prefix+'_verification.json').unlink(missing_ok=True)
    rig,binary,idle,idle_binary,slash,slash_binary,snapshot = load_inputs()
    parameters = json.loads(output_path('overhead_parameters.json').read_text())
    keyposes,blade,context = build_v2(rig,binary,idle,idle_binary,slash,slash_binary,snapshot,parameters)
    poses,times = dense_poses(keyposes,parameters,context) if dense else (keyposes,[pose['time_seconds'] for pose in parameters['poses']])
    metadata_path = output_path('overhead_metadata.json' if dense else 'v2_metadata.json')
    metadata_path.write_text(json.dumps({'completion':'in_progress'},indent=2)+'\n')
    encoded = author.encode_clip(rig,binary,poses,times)
    size = struct.unpack_from('<I',encoded,12)[0]
    doc = json.loads(encoded[20:20+size])
    packed = encoded[28+size:]
    doc['animations'][0]['name'] = prefix
    for sampler in doc['animations'][0]['samplers']:
        sampler['interpolation'] = 'LINEAR' if dense else 'STEP'
    doc['extras'] = {'overhead_stage4':{'stage':'raw','right_calibration_baked':False,'sample_count':len(times)}}
    raw = output_path(prefix+'_raw.glb')
    raw.write_bytes(author.library.encode_glb(doc,packed))
    lexical = author.PRODUCER / ('../refinement/hand-poses/attack-keyposes/stage4/candidate/'+raw.name)
    if lexical.resolve() != raw.resolve():
        raise ValueError('raw stage4 path escaped candidate')
    body = output_path(prefix+'_body.glb')
    preview = output_path(prefix+'_preview.glb')
    alignment_path = output_path(prefix+'_alignment.json')
    character = snapshot['base_configuration']
    alignment = author.prepare_character(author.PINS['rig'][0],author.PINS['rig'][1],[(prefix,lexical,digest(raw))],
        body,preview,alignment_path,height=character['height_metres'],grip_frame=character['grip_frame'],
        finger_rotation_offsets=character['finger_rotation_offsets'])
    outputs = []
    for path in (body,preview):
        prepared,buffer = author.library.read_glb(path)
        prepared.setdefault('extras',{})['overhead_stage4'] = {'stage':'preview_baked','right_calibration_applications':1,'raw_sha256':digest(raw)}
        outputs.append((path,author.library.encode_glb(prepared,buffer)))
    alignment['outputs'] = [author.output_info(path,data) for path,data in outputs]
    outputs.append((alignment_path,(json.dumps(alignment,indent=2)+'\n').encode()))
    author.publish_outputs(outputs)
    metadata = {'completion':'complete','clip':prefix,'interpolation':'LINEAR' if dense else 'STEP',
        'sample_count':len(times),'duration_seconds':times[-1],'parameters_sha256':digest(output_path('overhead_parameters.json')),
        'source_pins':{str(path.relative_to(author.REPO)):sha for path,sha in SOURCE_PINS.items()},
        'underlying_source_pins':{key:sha for key,(_,sha) in author.PINS.items()},
        'producer_code_sha256':snapshot['producer_code_sha256'],'actual_blade_frame':blade,
        'real_surface_contact':parameters['real_surface_contact'],
        'shoe_contact_regions':{side:{
            'heel_indices':np.flatnonzero(region['heel_mask']).tolist(),
            'front_indices':np.flatnonzero(region['front_mask']).tolist(),
            'definition':'fixed heel/front longitudinal quarters after sole-normal flattening and initial bone yaw, before levelling pitch',
        } for side,region in context[1][2].items()},
        'recovery_rule':'final pose equals authored guard pose for a stable exit',
        'raw_stage':'authored raw; original native right grip; right offsets UNBAKED',
        'preview_stage':'original eight right offsets ONCE','right_calibration':alignment['finger_rotation_calibration'],
        'raw_output':author.output_info(raw,raw.read_bytes()),'preview_outputs':alignment['outputs'],
        'measurements':metrics(poses,times,parameters,blade,context),
        'phase_mapping_seconds':{'windup':[0,.65],'strike':[.65,.90],'active_follow':[.90,1.10],'recover':[1.10,1.75]},
        'scope':'dense continuous candidate requiring surface scan' if dense else 'five independent grounded v2 STEP keyposes'}
    metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
    print('STAGE4_READY',prefix,digest(preview),preview,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dense',action='store_true')
    argv = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    main(parser.parse_args(argv).dense)
