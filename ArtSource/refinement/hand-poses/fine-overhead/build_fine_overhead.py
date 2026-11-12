"""Private continuous-native overhead study. Never publishes runtime assets."""
import copy
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PRODUCER = REPO / 'ArtSource/tripo-warrior'
CANDIDATE = HERE / 'candidate/v7'
sys.path.insert(0, str(PRODUCER))
sys.path.insert(0, str(HERE.parent / 'attack-keyposes'))
from mathutils import Matrix, Quaternion, Vector
import numpy as np
import prepare_character_library as library
import build_keyposes as author

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
stance = module('fine_stance', HERE.parent / 'attack-keyposes/stage4/build_overhead.py')
DURATION = 1.75
RATE = 120
WARP_X = [0., .65, .90, 1., 1.1, 1.55, 1.75]
WARP_Y = [1.55, 1.90, 2.03, 2.117, 2.15, 3.40, 3.40]
FIXED_PINS = {
    PRODUCER / 'refined-base60k/rig.glb': '43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6',
    PRODUCER / 'refined-base60k/slash.glb': '98e785d73a5d6cb767cebd5b79ec2bb9af9a2b717ae2d2576f3a0b7e07ea370a',
    HERE.parent / 'attack-keyposes/stage5/candidate/overhead_aligned_raw.glb': '377bcfc1197d1ae84d2c1784dc1de4004b68d09189528025786578c0b95987b9',
    REPO / 'app/src/main/assets/models/opponents/base.glb': 'ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20',
}
RIGHT_FINGERS = author.RIGHT_FINGERS

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def output(name):
    path = CANDIDATE / name
    if path.resolve().parent != CANDIDATE.resolve():
        raise ValueError('output escapes fine candidate')
    return path

def write(name, value):
    output(name).write_text(json.dumps(value, indent=2) + '\n')

def smooth(value):
    value = max(0., min(1., value))
    return max(0., min(1., value**3 * (10. + value * (-15. + 6. * value))))

def warp_slopes(x, y):
    if len(x) != len(y) or len(x) < 2 or not all(math.isfinite(v) for v in x+y):
        raise ValueError('invalid timewarp knots')
    if any(b <= a for a,b in zip(x,x[1:])) or any(b < a for a,b in zip(y,y[1:])):
        raise ValueError('timewarp must be monotonic')
    h = [b-a for a,b in zip(x,x[1:])]
    d = [(b-a)/s for a,b,s in zip(y,y[1:],h)]
    m = [d[0]]
    for i in range(1,len(x)-1):
        if d[i-1] * d[i] <= 0:
            m.append(0.)
        else:
            w1,w2 = 2*h[i]+h[i-1],h[i]+2*h[i-1]
            m.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
    m.append(d[-1])
    return m
WARP_M = warp_slopes(WARP_X, WARP_Y)

def native_time(time):
    if isinstance(time,bool) or not isinstance(time,(int,float)) or not math.isfinite(time) or not 0 <= time <= DURATION:
        raise ValueError('output time must lie in source 0–1.75 seconds')
    i = next((i for i in range(len(WARP_X)-1) if time <= WARP_X[i+1]),len(WARP_X)-2)
    h = WARP_X[i+1]-WARP_X[i]
    s = (time-WARP_X[i])/h
    return ((2*s**3-3*s*s+1)*WARP_Y[i] + (s**3-2*s*s+s)*h*WARP_M[i]
            +(-2*s**3+3*s*s)*WARP_Y[i+1]+(s**3-s*s)*h*WARP_M[i+1])

def sample(rig, tracks, time):
    return {i:list(library.sampled_local(node,i,tracks,time).decompose()) for i,node in enumerate(rig['nodes'])}

def blend(a,b,amount):
    return {i:[a[i][0].lerp(b[i][0],amount),a[i][1].slerp(b[i][1],amount),a[i][2].lerp(b[i][2],amount)] for i in a}

def body_lean(world,names,norm):
    torso = (norm@world[names['Head']]).translation-(norm@world[names['Hip']]).translation
    return math.degrees(math.atan2(torso.z,torso.y))

def set_prepared_point(local,index,wanted,world,parents,norm):
    raw = norm.inverted()@wanted
    parent = world[parents[index]] if index in parents else Matrix.Identity(4)
    local[index][0] = parent.inverted()@raw

def ground(local, guard_world, geometry, settings, rig,norm,names,parents,order):
    feet = {side:list((norm@guard_world[names[side+'Foot']]).translation) for side in ('L_','R_')}
    rotations = {side:guard_world[names[side+'Foot']].to_quaternion() for side in ('L_','R_')}
    return stance.ground_legs(rig,local,geometry,feet,rotations,settings,norm,names,parents,order)

def build():
    CANDIDATE.mkdir(parents=True,exist_ok=True)
    for path,sha in FIXED_PINS.items():
        if digest(path) != sha:
            raise ValueError('pinned formal/native/guard source changed: '+str(path))
    manifest_path = PRODUCER/'motion_library.json'
    manifest = json.loads(manifest_path.read_text())
    character = next(row for row in manifest['characters'] if row['id']=='base')
    body_path,target,target_binary = library.pinned_source(character)
    weapon_path,weapon_doc,weapon_binary = library.pinned_source(manifest['weapon_source'])
    rig_path,native_path,guard_path,_ = FIXED_PINS
    rig,binary = library.read_glb(rig_path)
    native,native_binary = library.read_glb(native_path)
    guard_doc,guard_binary = library.read_glb(guard_path)
    for doc in (native,guard_doc,target):
        library.require_same_rest(rig,doc)
    tracks,timeline = library.decode_animation(native,native_binary)
    guard_tracks,_ = library.decode_animation(guard_doc,guard_binary)
    guard = sample(rig,guard_tracks,0.)
    hands = library.sample_native_hands(rig,native,native_binary,2.117)
    parents,order = library.node_order(rig)
    names = {n.get('name'):i for i,n in enumerate(rig['nodes'])}
    norm = library.normalization_frame(target,character.get('height_metres',1.78))[0]
    guard_world = author.worlds(rig,guard,parents,order)
    native_start_world = author.worlds(rig,sample(rig,tracks,WARP_Y[0]),parents,order)
    geometry = stance.foot_geometry(rig,binary)
    formal_alignment_path = PRODUCER/'library/base_alignment.json'
    formal_alignment = json.loads(formal_alignment_path.read_text())
    grounding = formal_alignment['canonical_root_grounding']
    mount = library.local_matrix({'matrix':formal_alignment['grip_local_matrix_gltf']})
    weapon_names = {node.get('name'):i for i,node in enumerate(weapon_doc['nodes'])}
    blade_base = library.world_matrix(weapon_doc['nodes'],weapon_names['Blade_Base']).translation
    blade_tip = library.world_matrix(weapon_doc['nodes'],weapon_names['Blade_Tip']).translation
    blade_axis_local = (mount.to_3x3()@(blade_tip-blade_base)).normalized()
    roll_path = output('blade_roll_solution.json')
    roll_solution = json.loads(roll_path.read_text())
    roll_samples = roll_solution['samples']
    if len(roll_samples)!=211 or roll_solution['source_sha256']!='8cda9f95e0af2461893ad7246f3b9da644cac1744b209aab2adac17773ea6f15':
        raise ValueError('expected frozen v3 actual-binding continuous roll solution')
    regions_path = HERE.parent/'attack-keyposes/stage5/candidate/overhead_aligned_metadata.json'
    regions = json.loads(regions_path.read_text())['shoe_contact_regions']
    for side,region in geometry[2].items():
        for key,label in [('heel_mask','heel_indices'),('front_mask','front_indices')]:
            mask = np.zeros(len(region['positions']),dtype=bool)
            mask[regions[side][label]] = True
            region[key] = mask
    canonical_feet = stance.foot_measurements(geometry,guard_world,norm)
    settings = {'foot_centres_metres':{side:canonical_feet[side]['centre_metres'] for side in canonical_feet},
                'leg_poles_metres':{'L_':[.18,.50,.48],'R_':[-.18,.50,.32]}}
    dependencies = [manifest_path,formal_alignment_path,roll_path,body_path,weapon_path,regions_path,rig_path,native_path,guard_path,
                    Path(library.__file__),PRODUCER/'prepare_rigged_warrior.py',PRODUCER/'refine_character_grips.py',HERE.parent/'run_blender.py',Path(author.__file__),Path(stance.__file__),Path(__file__)]
    pins = {str(path.relative_to(REPO)):digest(path) for path in dependencies}
    times = [i/RATE for i in range(round(DURATION*RATE)+1)]
    poses,rows = [],[]
    for time in times:
        source_time = native_time(time)
        local = sample(rig,tracks,source_time)
        native_world = author.worlds(rig,local,parents,order)
        native_lean = body_lean(native_world,names,norm)
        # Keep the mocap's yaw, lateral response and spine articulation. Only
        # subtract its excessive global sagittal bend, at the pelvis carrier.
        desired_lean = 23.*math.tanh(native_lean/32.)
        correction = Quaternion((norm.inverted().to_3x3()@Vector((1,0,0))).normalized(),math.radians(desired_lean-native_lean))
        author.set_world_rotation(local,names['Hip'],correction@native_world[names['Hip']].to_quaternion(),native_world,parents)
        world = author.worlds(rig,local,parents,order)
        hip = (norm@guard_world[names['Hip']]).translation.copy()
        native_hip = (norm@native_world[names['Hip']]).translation
        initial_hip = (norm@native_start_world[names['Hip']]).translation
        hip.y += -.035+max(-.018,min(0.,(native_hip.y-initial_hip.y)*.30))
        hip.z += .025 * smooth(time/.9) * (1-smooth((time-1.25)/.5))
        shift = hip-(norm@world[names['Hip']]).translation
        local[names['BoneRoot']][0] += norm.inverted().to_3x3()@shift
        # Reconstruct each arm from that frame's native world rotations. This
        # retains the native moving elbow plane and wrist roll, without a
        # fixed elbow pole and without rotating the weapon with the torso cap.
        for side in ('L_','R_'):
            for bone in ('Upperarm','Forearm','Hand'):
                world = author.worlds(rig,local,parents,order)
                author.set_world_rotation(local,names[side+bone],native_world[names[side+bone]].to_quaternion(),world,parents)
        # Clear the head during the backward blade lift, retaining the
        # per-frame native elbow plane and the native wrist roll.
        world = author.worlds(rig,local,parents,order)
        envelope = smooth((time-.12)/.40)*(1.-smooth((time-.72)/.26))
        if envelope > 0.:
            shoulder = (norm@world[names['R_Upperarm']]).translation
            elbow = (norm@world[names['R_Forearm']]).translation
            wrist = (norm@world[names['R_Hand']]).translation
            wanted = wrist + Vector((-.14,.25,-.10))*envelope
            direction = wanted-shoulder
            reach = (elbow-shoulder).length+(wrist-elbow).length
            if direction.length > reach*.975:
                wanted = shoulder+direction.normalized()*reach*.975
            pole = elbow.copy()
            pole.x = min(pole.x,shoulder.x-.10*envelope)
            author.solve_arm(rig,local,'R_',norm.inverted()@wanted,norm.inverted()@pole,names,parents,order)
            world = author.worlds(rig,local,parents,order)
            author.set_world_rotation(local,names['R_Hand'],native_world[names['R_Hand']].to_quaternion(),world,parents)
        # The empty hand follows an independent protective arc. Its moving
        # native elbow, rather than a single static pole, determines the bend.
        world = author.worlds(rig,local,parents,order)
        native_pole = (norm@world[names['L_Forearm']]).translation
        left_target = (norm@guard_world[names['L_Hand']]).translation.copy()
        shoulder_delta = (norm@world[names['L_Upperarm']]).translation-(norm@guard_world[names['L_Upperarm']]).translation
        left_target += shoulder_delta
        left_target.y += .025*math.sin(math.pi*smooth(time/1.3))
        left_target.z -= .075*math.sin(math.pi*smooth(time/DURATION))
        native_pole.x = max(.34,native_pole.x)
        native_pole.z = min(.15,native_pole.z)
        author.solve_arm(rig,local,'L_',norm.inverted()@left_target,norm.inverted()@native_pole,names,parents,order)
        world = author.worlds(rig,local,parents,order)
        author.set_world_rotation(local,names['L_Hand'],guard_world[names['L_Hand']].to_quaternion(),world,parents)
        hand_pose = library.hand_pose_for_clip(rig,hands,'hit_head',min(1.,time/DURATION))
        for name,matrix in hand_pose.items():
            local[names[name]] = list(matrix.decompose())
        # Quintic guard joins keep entry/exit velocities at zero. Body and
        # limbs inside the attack continue to sample the 234 native tracks.
        amount = smooth(time/.28)*(1.-smooth((time-1.30)/.45))
        local = blend(guard,local,amount)
        # One rigid reorientation of forearm+hand preserves their native
        # relative wrist rotation. Let the wrist move onto the exact shoulder
        # sphere rather than forcing an impossible 150-degree wrist swing.
        world = author.worlds(rig,local,parents,order)
        roll_envelope = smooth((time-.25)/.50)*(1.-smooth((time-1.20)/.55))
        roll_degrees = roll_samples[round(time*RATE)]['roll_degrees_unwrapped'] if time<1. else 157.39068771161152
        roll_angle = math.radians(roll_degrees)*roll_envelope
        pitch_angle = math.radians(45.)*smooth((time-.75)/.25)*(1.-smooth((time-1.15)/.45))
        if roll_envelope>0. or pitch_angle>0.:
            shoulder,elbow,wrist = [world[names['R_'+bone]].translation.copy() for bone in ('Upperarm','Forearm','Hand')]
            upper,lower = (elbow-shoulder).length,(wrist-elbow).length
            blade_axis = (world[names['R_Hand']].to_3x3()@blade_axis_local).normalized()
            pitch_axis = (norm.inverted().to_3x3()@Vector((1,0,0))).normalized()
            delta = Quaternion(pitch_axis,pitch_angle)@Quaternion(blade_axis,roll_angle)
            pre_axis_weight = smooth((time-.25)/.20)*(1.-smooth((time-.70)/.20))
            if pre_axis_weight>0.:
                current_axis = (delta@blade_axis).normalized()
                raised_axis = (norm.inverted().to_3x3()@Vector((0.,.85,-.5267826876))).normalized()
                lift = current_axis.rotation_difference(raised_axis)
                delta = Quaternion((1.,0.,0.,0.)).slerp(lift,pre_axis_weight)@delta
            wanted_forearm = (delta@(wrist-elbow)).normalized()
            sphere_centre = shoulder+lower*wanted_forearm
            # The legal shoulder sphere also permits a deliberate lateral
            # clearance arc during entry and return, keeping the steel outside
            # the head/coat instead of retaining an unsafe nearest-body path.
            clear_pre = smooth((time-.35)/.10)*(1.-smooth((time-.65)/.15))
            clear_return = smooth((time-1.25)/.12)*(1.-smooth((time-1.50)/.20))
            clearance = norm.inverted().to_3x3()@(Vector((-.65,.30,.25))*clear_pre+Vector((-.65,.10,.25))*clear_return)
            nearest = wrist+clearance-sphere_centre
            if nearest.length<1e-8:
                raise ValueError('natural wrist sphere has an indeterminate nearest direction')
            wanted_elbow = shoulder+upper*nearest.normalized()
            wanted_wrist = wanted_elbow+lower*wanted_forearm
            forearm_rotation = delta@world[names['R_Forearm']].to_quaternion()
            hand_rotation = delta@world[names['R_Hand']].to_quaternion()
            author.aim_segment(rig,local,'R_Upperarm','R_Forearm',wanted_elbow,names,parents,order)
            world = author.worlds(rig,local,parents,order)
            author.set_world_rotation(local,names['R_Forearm'],forearm_rotation,world,parents)
            world = author.worlds(rig,local,parents,order)
            author.set_world_rotation(local,names['R_Hand'],hand_rotation,world,parents)
            world = author.worlds(rig,local,parents,order)
            if (world[names['R_Hand']].translation-wanted_wrist).length>1e-5:
                raise ValueError('natural wrist shoulder-sphere reconstruction error')
        for name in RIGHT_FINGERS:
            local[names[name]] = list(hands[name].decompose())
        if time == 0. or time == DURATION:
            local = copy.deepcopy(guard)
        try:
            feet = ground(local,guard_world,geometry,settings,rig,norm,names,parents,order)
        except ValueError as error:
            raise ValueError(f'output {time:.6f} native {source_time:.6f}: {error}') from error
        if time == 0. or time == DURATION:
            local = copy.deepcopy(guard)
        world = author.worlds(rig,local,parents,order)
        rows.append({'output_seconds':time,'native_seconds':source_time,'native_weight':amount,
                     'native_torso_lean_degrees':native_lean,'final_torso_lean_degrees':body_lean(world,names,norm),
                     'right_hand_metres':list((norm@world[names['R_Hand']]).translation),
                     'left_hand_metres':list((norm@world[names['L_Hand']]).translation),
                     'foot_surfaces':feet})
        poses.append(local)
    encoded = author.encode_clip(rig,binary,poses,times)
    size = struct.unpack_from('<I',encoded,12)[0]
    doc = json.loads(encoded[20:20+size]);packed = bytearray(encoded[28+size:])
    # Preserve the exact source float32 guard endpoints, without a repeated
    # TRS matrix decomposition changing their canonical scale/quaternion bits.
    for channel in doc['animations'][0]['channels']:
        target = channel['target'];sampler = doc['animations'][0]['samplers'][channel['sampler']]
        expected = guard_tracks[(target['node'],target['path'])][1][0]
        item = doc['accessors'][sampler['output']];view = doc['bufferViews'][item['bufferView']]
        start = view.get('byteOffset',0)+item.get('byteOffset',0)
        indices = range(item['count']) if rig['nodes'][target['node']].get('name') in RIGHT_FINGERS else (0,item['count']-1)
        for key in indices:
            struct.pack_into('<'+'f'*len(expected),packed,start+key*len(expected)*4,*expected)
    doc['animations'][0]['name'] = 'attack_overhead'
    for sampler in doc['animations'][0]['samplers']:
        sampler['interpolation']='LINEAR'
    doc['extras'] = {'fine_overhead':{'stage':'authored_raw','right_calibration_baked':False,
                    'native_source_sha256':digest(native_path),'sample_count':len(times)}}
    raw = output('fine_overhead_raw.glb')
    raw.write_bytes(library.encode_glb(doc,packed))
    lexical = PRODUCER/('../refinement/hand-poses/fine-overhead/'+str(raw.relative_to(HERE)))
    preview = output('fine_overhead_preview.glb')
    body = output('fine_overhead_body.glb')
    alignment_path = output('fine_overhead_alignment.json')
    alignment = library.prepare_character(body_path,character['source_sha256'],[('attack_overhead',lexical,digest(raw))],
                body,preview,alignment_path,height=character.get('height_metres',1.78),grip_frame=character['grip_frame'],
                finger_rotation_offsets=character.get('finger_rotation_offsets'),weapon_source=manifest['weapon_source'])
    # Apply precisely the formal producer's one constant guard root shift.
    # The raw authoring artifact remains in the canonical source frame.
    root_shift = grounding['constant_local_root_shift']
    for prepared_path in (body,preview):
        prepared,prepared_binary = library.read_glb(prepared_path)
        prepared_binary = bytearray(prepared_binary)
        root = next(i for i,n in enumerate(prepared['nodes']) if n.get('name')=='BoneRoot')
        for channel in prepared['animations'][0]['channels']:
            if channel['target'] != {'node':root,'path':'translation'}:
                continue
            sampler = prepared['animations'][0]['samplers'][channel['sampler']]
            item = prepared['accessors'][sampler['output']]
            view = prepared['bufferViews'][item['bufferView']]
            start = view.get('byteOffset',0)+item.get('byteOffset',0)
            for i in range(item['count']):
                row = struct.unpack_from('<3f',prepared_binary,start+i*12)
                struct.pack_into('<3f',prepared_binary,start+i*12,*[a+b for a,b in zip(row,root_shift)])
        prepared_path.write_bytes(library.encode_glb(prepared,prepared_binary))
    alignment['canonical_root_grounding'] = {k:grounding[k] for k in ('policy','constant_world_root_shift_metres','constant_local_root_shift')}
    alignment['outputs'] = [{'file':p.name,'sha256':digest(p),'bytes':p.stat().st_size} for p in (body,preview)]
    alignment_path.write_text(json.dumps(alignment,indent=2)+'\n')
    for relative,sha in pins.items():
        if digest(REPO/relative)!=sha:
            raise ValueError('source changed while building: '+relative)
    record = {'completion':'candidate_ready','clip':'attack_overhead','duration_seconds':DURATION,'sample_rate_hz':RATE,
              'sample_count':len(times),'source_range_seconds':[0.,DURATION],'interpolation':'LINEAR','formal_baseline_sha256':FIXED_PINS[REPO/'app/src/main/assets/models/opponents/base.glb'],
              'phase_markers':manifest['attack_source']['phase_markers'],'ACTIVE_phase_elapsed_ms':100,
              'source_pins':pins,'native_channel_count':len(tracks),'native_timewarp':{'output_seconds':WARP_X,'native_seconds':WARP_Y,'slopes':WARP_M,'interpolation':'monotone cubic Hermite'},
              'native_basis':'Each output frame samples all234 native channels; no dense_poses/keypose basis. Native body articulation, sagittal pelvis cap, independent open left guard and canonical shoe-surface IK. Right arm uses actual blade-axis roll and45deg sagittal cut, shared rigid forearm/hand reorientation, closest legal shoulder sphere; preserves wrist-local rotation rather than impossible wrist-only blade flip.',
              'blade_direction_correction':{'roll_solution_sha256':digest(roll_path),'roll_tail_after_contact_degrees':157.39068771161152,'native_active_end_seconds':2.15,'shoulder_sphere_clearance_goal_metres':{'pre':[-.65,.30,.25],'pre_blade_axis':[0.,.85,-.5267826876],'pre_axis_envelope':[.25,.45,.70,.90],'return':[-.65,.10,.25]},'roll_envelope':[.25,.75,1.2,1.75],'pitch_peak_degrees':45.,'pitch_envelope':[.75,1.,1.15,1.60],'wrist_policy':'forearm and hand share full rigid delta; closest wrist on real upperarm shoulder sphere, exact native wrist-local preserved in active source'},
              'right_lift_clearance':'Native moving elbow pole IK; C2 envelope raw prepared displacement(-140,+250,-100)mm limited to97.5% actual reach; wrist world quaternion remains native; correction ends at.98s.',
              'root_policy':'Horizontal native drift removed; native vertical pelvis response scaled 0.30 with -35mm pressure sink and max additional -18mm; forward pressure envelope 25mm.',
              'foot_contact_phases':{'L_':[[0,DURATION,'flat planted']],'R_':[[0,DURATION,'flat planted']]},
              'hand_policy':{'raw_right':'native at 2.117s, constant UNBAKED','left':'reviewed hit_head protective open curve','entry_exit':'exact stage5 canonical guard'},
              'calibration_stages':{'raw':{'right_calibration_baked':False,'right_applications':0},'preview':{'right_calibration_baked':True,'right_applications':1,'offsets':character.get('finger_rotation_offsets')}},
              'preview_grounding':alignment['canonical_root_grounding'],
              'body_source':character,'weapon_source':manifest['weapon_source'],
              'raw_output':{'file':raw.name,'sha256':digest(raw)},
              'preview_outputs':[{'file':path.name,'sha256':digest(path)} for path in (body,preview,alignment_path)],
              'frames':rows,'verification':'pending numerical and rendered surface review'}
    write('fine_overhead_metadata.json',record)
    print('FINE_OVERHEAD_READY',str(preview),digest(preview),flush=True)

if __name__=='__main__':
    build()
