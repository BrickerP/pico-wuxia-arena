"""Private full-body weighted overhead authoring. No production writes."""
import copy, hashlib, importlib.util, json, math, struct, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
FINE=REPO/'ArtSource/refinement/hand-poses/fine-overhead'
OUT=HERE/'candidate/v3'
sys.path.insert(0,str(FINE))
import build_fine_overhead as base
from mathutils import Matrix,Quaternion,Vector
import numpy as np
library,author,stance=base.library,base.author,base.stance
DURATION=1.75
RATE=120
SOURCE=FINE/'candidate/v9/fine_overhead_raw.glb'
SOURCE_SHA='66a56edc4a2bfd4e83c29866a9ce93a854d2d64f1a215e433dc1ac54dc16d750'
RIG=base.PRODUCER/'refined-base60k/rig.glb'
RIG_SHA='43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(p):return {'file':str(Path(p).relative_to(REPO)),'sha256':digest(p),'bytes':Path(p).stat().st_size}
def write(name,value): (OUT/name).write_text(json.dumps(value,indent=2)+'\n')

def curve(t,knots):
    x=[r[0] for r in knots]; y=[r[1] for r in knots]
    if isinstance(y[0],(list,tuple)):
        return Vector([curve(t,[(a,b[i]) for a,b in knots]) for i in range(len(y[0]))])
    # Shape-preserving cubic, allowing signed/nonmonotonic authored controls.
    h=np.diff(x);d=np.diff(y)/h;m=[float(d[0])]
    for i in range(1,len(x)-1):
        if d[i-1]*d[i]<=0:m.append(0.)
        else:
            w1,w2=2*h[i]+h[i-1],h[i]+2*h[i-1]
            m.append(float((w1+w2)/(w1/d[i-1]+w2/d[i])))
    m.append(float(d[-1]));m[0]=m[-1]=0.
    i=next((i for i in range(len(x)-1) if t<=x[i+1]),len(x)-2)
    s=(t-x[i])/h[i]
    return float((2*s**3-3*s*s+1)*y[i]+(s**3-2*s*s+s)*h[i]*m[i]+(-2*s**3+3*s*s)*y[i+1]+(s**3-s*s)*h[i]*m[i+1])

HIP_POS=[(0,[0,.870,0]),(.30,[-.008,.842,-.015]),(.67,[-.025,.795,-.040]),(.82,[-.010,.824,.012]),(1.,[.018,.833,.105]),(1.16,[.022,.782,.115]),(1.34,[.005,.803,.075]),(1.56,[0,.846,.025]),(1.75,[0,.870,0])]
HIP_YAW=[(0,0),(.67,-12),(.80,2),(1.,14),(1.16,11),(1.4,3),(1.75,0)]
HIP_PITCH=[(0,0),(.67,-5),(.85,0),(1.,6),(1.16,10),(1.4,3),(1.75,0)]
CHEST_YAW=[(0,0),(.69,-5),(.84,-3),(1.02,7),(1.18,4),(1.48,-2),(1.75,0)]
CHEST_PITCH=[(0,0),(.67,-8),(.86,-7),(1.02,-3),(1.16,4),(1.5,-3),(1.75,0)]
RIGHT_POS=[(0,[-.13,1.27,.27]),(.25,[-.23,1.48,.17]),(.50,[-.31,1.60,.065]),(.70,[-.30,1.61,.035]),(.82,[-.26,1.57,.10]),(.93,[-.20,1.38,.30]),(1.0,[-.17,1.22,.40]),(1.16,[-.22,1.06,.36]),(1.32,[-.43,1.14,.36]),(1.42,[-.43,1.18,.35]),(1.55,[-.26,1.26,.28]),(1.75,[-.13,1.27,.27])]
RIGHT_POLE=[(0,[-.35,1.20,.08]),(.67,[-.49,1.36,.04]),(.87,[-.48,1.42,.30]),(1.,[-.49,1.30,.34]),(1.16,[-.44,1.17,.26]),(1.45,[-.48,1.15,.12]),(1.75,[-.35,1.20,.08])]
LEFT_POS=[(0,[.20,1.27,.20]),(.40,[.21,1.29,.25]),(.70,[.23,1.30,.27]),(1.,[.21,1.26,.32]),(1.18,[.22,1.19,.28]),(1.48,[.20,1.25,.22]),(1.75,[.20,1.27,.20])]
LEFT_POLE=[(0,[.48,1.04,.12]),(.70,[.48,1.04,.12]),(1.0,[.48,1.07,.36]),(1.16,[.48,.99,.40]),(1.40,[.46,1.08,.35]),(1.75,[.48,1.04,.12])]
ARM_CLOCK=[(0,0),(.30,.30),(.60,.60),(.75,.85),(.82,.92),(.90,.97),(1.,1.02),(1.15,1.20),(1.45,1.50),(1.75,1.75)]
BODY_CLOCK=[(0,0),(.40,.38),(.72,.68),(.86,.93),(1.,1.04),(1.16,1.18),(1.5,1.5),(1.75,1.75)]


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    assert digest(SOURCE)==SOURCE_SHA and digest(RIG)==RIG_SHA,'frozen native/raw input drift'
    rig,binary=library.read_glb(RIG);raw,rawb=library.read_glb(SOURCE)
    library.require_same_rest(rig,raw)
    tracks,timeline=library.decode_animation(raw,rawb)
    assert len(tracks)==234 and len(timeline)==211
    manifest=json.loads((base.PRODUCER/'motion_library.json').read_text())
    character=next(c for c in manifest['characters'] if c['id']=='base')
    body_path,target,tb=library.pinned_source(character)
    norm=library.normalization_frame(target,character.get('height_metres',1.78))[0]
    inv=norm.inverted(); parents,order=library.node_order(rig)
    names={n.get('name'):i for i,n in enumerate(rig['nodes'])}
    guard=base.sample(rig,tracks,0.);gw=author.worlds(rig,guard,parents,order)
    geometry=stance.foot_geometry(rig,binary)
    regions=json.loads((FINE.parent/'attack-keyposes/stage5/candidate/overhead_aligned_metadata.json').read_text())['shoe_contact_regions']
    for side,region in geometry[2].items():
        for key,label in [('heel_mask','heel_indices'),('front_mask','front_indices')]:
            mask=np.zeros(len(region['positions']),dtype=bool);mask[regions[side][label]]=True;region[key]=mask
    feet0=stance.foot_measurements(geometry,gw,norm)
    settings={'foot_centres_metres':{side:feet0[side]['centre_metres'] for side in feet0},'leg_poles_metres':{'L_':[.24,.47,.48],'R_':[-.24,.45,.32]}}
    axis={a:(inv.to_3x3()@Vector(v)).normalized() for a,v in [('yaw',(0,1,0)),('pitch',(1,0,0))]}
    weapon_path,weapon,weapon_binary=library.pinned_source(manifest['weapon_source'])
    wn={n.get('name'):i for i,n in enumerate(weapon['nodes'])}
    mount=library.local_matrix({'matrix':json.loads((base.PRODUCER/'library/base_alignment.json').read_text())['grip_local_matrix_gltf']})
    blade_axis_local=(mount.to_3x3()@(library.world_matrix(weapon['nodes'],wn['Blade_Tip']).translation-library.world_matrix(weapon['nodes'],wn['Blade_Base']).translation)).normalized()
    guard_axis=(norm.to_3x3()@(gw[names['R_Hand']].to_quaternion()@blade_axis_local)).normalized()
    lift_local=base.sample(rig,tracks,.50);lift_world=author.worlds(rig,lift_local,parents,order)
    lift_axis=(norm.to_3x3()@(lift_world[names['R_Hand']].to_quaternion()@blade_axis_local)).normalized()
    lift_axis_controls=[(0,list(guard_axis)),(.18,[0,.72,.69]),(.35,[0,.95,-.31]),(.50,list(lift_axis))]
    poses=[];rows=[]
    for step in range(211):
        t=step/RATE; bt=curve(t,BODY_CLOCK);at=curve(t,ARM_CLOCK)
        local=base.sample(rig,tracks,bt); arm=base.sample(rig,tracks,at);aw=author.worlds(rig,arm,parents,order)
        world=author.worlds(rig,local,parents,order)
        hip_delta=Quaternion(axis['yaw'],math.radians(curve(t,HIP_YAW)))@Quaternion(axis['pitch'],math.radians(curve(t,HIP_PITCH)))
        author.set_world_rotation(local,names['Hip'],hip_delta@world[names['Hip']].to_quaternion(),world,parents)
        world=author.worlds(rig,local,parents,order)
        wanted=curve(t,HIP_POS);wanted+=Vector((0,(norm@gw[names['Hip']]).translation.y-.870,0))
        shift=wanted-(norm@world[names['Hip']]).translation
        local[names['BoneRoot']][0]+=inv.to_3x3()@shift
        # Chest lags the leg/hip drive; shoulders keep the guard's relaxed
        # clavicle placement instead of inheriting v9's both-elbows-high hunch.
        chest_delta=Quaternion(axis['yaw'],math.radians(curve(t,CHEST_YAW)))@Quaternion(axis['pitch'],math.radians(curve(t,CHEST_PITCH)))
        world=author.worlds(rig,local,parents,order)
        author.set_world_rotation(local,names['Spine02'],chest_delta@world[names['Spine02']].to_quaternion(),world,parents)
        for side in ('L_','R_'):local[names[side+'Clavicle']]=copy.deepcopy(guard[names[side+'Clavicle']])
        # An independent open protective hand with a low elbow.
        for side,wanted,pole in [('R_',curve(t,RIGHT_POS),curve(t,RIGHT_POLE)),('L_',curve(t,LEFT_POS),curve(t,LEFT_POLE))]:
            world=author.worlds(rig,local,parents,order)
            shoulder=(norm@world[names[side+'Upperarm']]).translation
            elbow=(norm@world[names[side+'Forearm']]).translation
            wrist=(norm@world[names[side+'Hand']]).translation
            reach=(elbow-shoulder).length+(wrist-elbow).length
            direction=wanted-shoulder
            if direction.length>reach*.975:wanted=shoulder+direction.normalized()*reach*.975
            author.solve_arm(rig,local,side,inv@wanted,inv@pole,names,parents,order)
            world=author.worlds(rig,local,parents,order)
            rotation=aw[names['R_Hand']].to_quaternion() if side=='R_' else gw[names['L_Hand']].to_quaternion()
            if side=='R_' and 0<t<.50:
                # The v9 early lift sweeps sideways through the upright head.
                # Swing actual blade geometry up in the sagittal lane beside
                # the right temple, then join the unchanged loaded blade axis.
                current_axis=(norm.to_3x3()@(rotation@blade_axis_local)).normalized()
                target_axis=curve(t,lift_axis_controls).normalized()
                swing=(inv.to_3x3()@current_axis).normalized().rotation_difference((inv.to_3x3()@target_axis).normalized())
                rotation=swing@rotation
            author.set_world_rotation(local,names[side+'Hand'],rotation,world,parents)
        # Retain v9's target-facing world gaze while rebuilding the body chain.
        # No inherited low-head-before-.5 avoidance mechanism is required.
        world=author.worlds(rig,local,parents,order)
        head_guard=gw[names['Head']].to_quaternion()
        author.set_world_rotation(local,names['Head'],head_guard,world,parents)
        join=base.smooth(t/.20)*(1-base.smooth((t-1.50)/.25))
        local=base.blend(guard,local,join)
        if t in (0.,DURATION):local=copy.deepcopy(guard)
        feet=base.ground(local,gw,geometry,settings,rig,norm,names,parents,order)
        if t in (0.,DURATION):local=copy.deepcopy(guard)
        w=author.worlds(rig,local,parents,order)
        rows.append({'source_seconds':t,'body_basis_seconds':bt,'blade_orientation_basis_seconds':at,'hip_metres':list((norm@w[names['Hip']]).translation),'chest_metres':list((norm@w[names['Spine02']]).translation),'R_hand_metres':list((norm@w[names['R_Hand']]).translation),'L_hand_metres':list((norm@w[names['L_Hand']]).translation),'foot_surfaces':feet})
        poses.append(local)
    encoded=author.encode_clip(rig,binary,poses,[i/RATE for i in range(211)])
    size=struct.unpack_from('<I',encoded,12)[0];doc=json.loads(encoded[20:20+size]);packed=bytearray(encoded[28+size:])
    # Exact original unbaked R15 and guard endpoint float32 payloads.
    for channel in doc['animations'][0]['channels']:
        target=channel['target'];sampler=doc['animations'][0]['samplers'][channel['sampler']]
        expected=tracks[target['node'],target['path']][1][0]
        item=doc['accessors'][sampler['output']];view=doc['bufferViews'][item['bufferView']]
        start=view.get('byteOffset',0)+item.get('byteOffset',0)
        indices=range(item['count']) if rig['nodes'][target['node']].get('name') in base.RIGHT_FINGERS else (0,item['count']-1)
        for key in indices:struct.pack_into('<'+'f'*len(expected),packed,start+key*len(expected)*4,*expected)
        sampler['interpolation']='LINEAR'
    doc['animations'][0]['name']='attack_overhead'
    doc['extras']={'weighted_overhead':{'stage':'authored_raw','right_calibration_baked':False,'sample_count':211,'parent_sha256':SOURCE_SHA}}
    output=OUT/'weighted_overhead_raw.glb';output.write_bytes(library.encode_glb(doc,packed))
    print('WEIGHTED_RAW_READY',str(output),digest(output),flush=True)
    formal_alignment=json.loads((base.PRODUCER/'library/base_alignment.json').read_text()); grounding=formal_alignment['canonical_root_grounding']
    body=OUT/'weighted_overhead_body.glb';preview=OUT/'weighted_overhead_preview.glb';alignment_path=OUT/'weighted_overhead_alignment.json'
    lexical=base.PRODUCER/('../refinement/combat-direction/native-weighted-overhead/'+str(output.relative_to(HERE)))
    alignment=library.prepare_character(body_path,character['source_sha256'],[('attack_overhead',lexical,digest(output))],body,preview,alignment_path,height=character.get('height_metres',1.78),grip_frame=character['grip_frame'],finger_rotation_offsets=character.get('finger_rotation_offsets'),weapon_source=manifest['weapon_source'])
    shift=grounding['constant_local_root_shift']
    for path in (body,preview):
        d,b=library.read_glb(path);b=bytearray(b);root=next(i for i,n in enumerate(d['nodes']) if n.get('name')=='BoneRoot')
        for channel in d['animations'][0]['channels']:
            if channel['target']!={'node':root,'path':'translation'}:continue
            sampler=d['animations'][0]['samplers'][channel['sampler']];a=d['accessors'][sampler['output']];v=d['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0)
            for i in range(a['count']):
                row=struct.unpack_from('<3f',b,offset+i*12);struct.pack_into('<3f',b,offset+i*12,*[x+y for x,y in zip(row,shift)])
        path.write_bytes(library.encode_glb(d,b))
    alignment['canonical_root_grounding']={k:grounding[k] for k in ('policy','constant_world_root_shift_metres','constant_local_root_shift')}
    alignment['outputs']=[identity(p) for p in (body,preview)];alignment_path.write_text(json.dumps(alignment,indent=2)+'\n')
    record={'schema_version':1,'status':'RAW_ready_visual_and_limited_checks_pending','clip':'attack_overhead','stage':'authored_raw','right_calibration_baked':False,'right_calibration_applications':0,'contract':'attack78','duration_seconds':1.75,'sample_rate_hz':120,'sample_count':211,'channel_count':234,'joint_count':78,'raw':identity(output),'raw_output':{'file':output.name,'sha256':digest(output)},'preview_outputs':[{'file':p.name,'sha256':digest(p)} for p in (body,preview,alignment_path)],'internal_preview_policy':'PRIVATE ONLY; target finger offsets once + formal canonical root shift once. Never import as raw.','parent':identity(SOURCE),'native_rig':identity(RIG),'body_source':character,'weapon_source':manifest['weapon_source'],'preview_grounding':alignment['canonical_root_grounding'],'normalization_matrix_gltf':alignment['normalization_matrix_gltf'],'authored_controls':{'hip_position_metres':HIP_POS,'hip_yaw_delta_degrees':HIP_YAW,'hip_pitch_delta_degrees':HIP_PITCH,'chest_yaw_delta_degrees':CHEST_YAW,'chest_pitch_delta_degrees':CHEST_PITCH,'right_wrist_metres':RIGHT_POS,'right_elbow_poles_metres':RIGHT_POLE,'left_guard_wrist_metres':LEFT_POS,'left_elbow_poles_metres':LEFT_POLE,'blade_orientation_clock':ARM_CLOCK,'body_clock':BODY_CLOCK,'early_lift_actual_blade_axis':lift_axis_controls},'intent':'Rear-loaded sink then hip drive leads chest/shoulder, high outside-temple right grip with upward/back blade, low left elbow protective guard, forward/down hand and actual steel path, post-contact lower-body absorption then guard.','foot_contact_phases':{'L_':[[0,1.75,'flat planted support']],'R_':[[0,1.75,'flat planted pressure/drive; knee and hip articulation']]} ,'contact':{'cue_source_seconds':1.0,'actual_damage_time':'Root owns actual new steel/target intersection; cue is not collision proof','old_v9_actual_path_preserved':False},'endpoint_policy':'exact parent-v9 guard float32 TRS first/last keys','hand_policy':'R15 exact parent-v9 unbaked values, no finger corrections in raw; left open native curve inherited','retarget_instruction':'Import complete RAW234-channel/78-joint animation using each target rig. Recompute actual weapon/contact profiles; retain target once-only finger calibration and canonical root grounding. No patch onto old formal model.','limits':['Source candidate only; no APK/runtime/native acceptance claimed.','Sampled sole and triangle checks do not prove continuous collision freedom.'],'frames':rows,'source_pins':{str(p.relative_to(REPO)):digest(p) for p in [Path(__file__),SOURCE,RIG,Path(base.__file__),Path(author.__file__),Path(stance.__file__),Path(library.__file__),base.PRODUCER/'refine_character_grips.py',FINE.parent/'run_blender.py']}}
    write('weighted_overhead_authoring.json',record)
    print('WEIGHTED_PREVIEW_READY',str(preview),digest(preview),flush=True)

if __name__=='__main__':build()
