"""Private natural canonical guard and small closed-loop breathing idle authoring.
No production/family/runtime changes. Right native grip is unbaked in RAW.
"""
import copy,hashlib,importlib.util,json,math,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[3]
OUT=HERE/'candidate/v1';PRODUCER=REPO/'ArtSource/tripo-warrior';FINE=REPO/'ArtSource/refinement/hand-poses/fine-overhead'
sys.path.insert(0,str(FINE));import build_fine_overhead as base
library,author,stance=base.library,base.author,base.stance
from mathutils import Quaternion,Vector
import numpy as np
SOURCE=HERE.parent/'native-weighted-overhead/candidate/v5/weighted_overhead_raw.glb'
SOURCE_SHA='85d633ec61534c62f59269c1d9f02854e829d1b84db33a91e3a3afac2e779076'
RIG=PRODUCER/'refined-base60k/rig.glb';RIG_SHA='43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6'
DURATION=1.5;RATE=120

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def identity(path):
 p=Path(path);return {'file':str(p.relative_to(REPO)),'sha256':digest(p),'bytes':p.stat().st_size}
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def breath(time):
 if isinstance(time,bool) or not isinstance(time,(int,float)) or not math.isfinite(time) or not 0<=time<=DURATION:raise ValueError('finite idle source0..1.5 time required')
 if time==0 or time==DURATION:return 0.
 return .5-.5*math.cos(2*math.pi*time/DURATION)

def encode(rig,binary,poses,times,name,old_tracks,guard_tracks=None):
 data=author.encode_clip(rig,binary,poses,times);size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);packed=bytearray(data[28+size:])
 changed_rotations={'L_Clavicle','R_Clavicle','L_Upperarm','L_Forearm','L_Hand','R_Upperarm','R_Forearm','R_Hand','Spine01','Head'}|{n for n in library.joint_nodes(rig) if n.startswith(('L_Thumb','L_Index','L_Mid','L_Ring','L_Pinky'))}
 for c in doc['animations'][0]['channels']:
  node,path=c['target']['node'],c['target']['path'];name_=rig['nodes'][node]['name'];sampler=doc['animations'][0]['samplers'][c['sampler']];a=doc['accessors'][sampler['output']];v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0);width=4 if path=='rotation' else 3
  if path!='rotation' or name_ not in changed_rotations or name_ in base.RIGHT_FINGERS:
   value=old_tracks[node,path][1][0]
   for k in range(a['count']):struct.pack_into('<'+'f'*width,packed,start+k*width*4,*value)
  if guard_tracks:
   value=guard_tracks[node,path][1][0]
   for k in (0,a['count']-1):struct.pack_into('<'+'f'*width,packed,start+k*width*4,*value)
  sampler['interpolation']='LINEAR'
 doc['animations'][0]['name']=name
 doc['extras']={'natural_guard':{'stage':'authored_raw','right_calibration_baked':False,'right_finger_offset_applications':0,'parent_sha256':SOURCE_SHA,'intent':'canonical reference' if name=='guard_pose' else 'closed small breathing idle'}}
 return library.encode_glb(doc,packed)

def prepare(raw,stem,character,manifest,body_path,grounding):
 body=OUT/(stem+'_body.glb');preview=OUT/(stem+'_preview.glb');alignment_path=OUT/(stem+'_alignment.json')
 lexical=PRODUCER/('../refinement/combat-direction/natural-guard/'+str(raw.relative_to(HERE)))
 clip='guard_pose' if stem=='guard' else 'idle'
 alignment=library.prepare_character(body_path,character['source_sha256'],[(clip,lexical,digest(raw))],body,preview,alignment_path,height=character['height_metres'],grip_frame=character['grip_frame'],finger_rotation_offsets=character.get('finger_rotation_offsets'),weapon_source=manifest['weapon_source'])
 shift=grounding['constant_local_root_shift']
 for path in (body,preview):
  doc,b=library.read_glb(path);b=bytearray(b);root=next(i for i,n in enumerate(doc['nodes']) if n.get('name')=='BoneRoot')
  for c in doc['animations'][0]['channels']:
   if c['target']!={'node':root,'path':'translation'}:continue
   a=doc['accessors'][doc['animations'][0]['samplers'][c['sampler']]['output']];v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0)
   for k in range(a['count']):
    row=struct.unpack_from('<3f',b,offset+k*12);struct.pack_into('<3f',b,offset+k*12,*[x+y for x,y in zip(row,shift)])
  path.write_bytes(library.encode_glb(doc,b))
 alignment['canonical_root_grounding']={k:grounding[k] for k in ('policy','constant_world_root_shift_metres','constant_local_root_shift')}
 alignment['private_natural_guard_preview']={'raw':identity(raw),'target':'base','right_finger_calibration_applications':1,'target_canonical_root_shift_applications':1,'direct_same_rest_source_prepare':True,'not_a_runtime_family_or_RAW':True}
 alignment['outputs']=[identity(p) for p in (body,preview)];alignment_path.write_text(json.dumps(alignment,indent=2)+'\n')
 return preview,alignment_path

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 assert digest(SOURCE)==SOURCE_SHA and digest(RIG)==RIG_SHA
 rig,binary=library.read_glb(RIG);source,sb=library.read_glb(SOURCE);library.require_same_rest(rig,source)
 tracks,_=library.decode_animation(source,sb);parents,order=library.node_order(rig);names={n.get('name'):i for i,n in enumerate(rig['nodes'])}
 manifest_path=PRODUCER/'motion_library.json';manifest=json.loads(manifest_path.read_text());character=next(c for c in manifest['characters'] if c['id']=='base');body_path,target,tb=library.pinned_source(character);library.require_same_rest(rig,target)
 norm=library.normalization_frame(target,character['height_metres'])[0];inv=norm.inverted();old=base.sample(rig,tracks,0.);old_world=author.worlds(rig,old,parents,order)
 rest={i:list(library.local_matrix(n).decompose()) for i,n in enumerate(rig['nodes'])}
 grip_path,grip,gb=library.pinned_source(character['grip_source']);hands=library.sample_native_hands(rig,grip,gb,character['grip_source'].get('time_seconds',2.117))
 zaxis=(inv.to_3x3()@Vector((0,0,1))).normalized();xaxis=(inv.to_3x3()@Vector((1,0,0))).normalized()
 new=copy.deepcopy(old)
 # Small clavicle release; the actual hand/dao frame is reconstructed below.
 for side,sign in [('L_',-1.),('R_',1.)]:
  w=author.worlds(rig,new,parents,order)
  author.set_world_rotation(new,names[side+'Clavicle'],Quaternion(zaxis,math.radians(3.*sign))@w[names[side+'Clavicle']].to_quaternion(),w,parents)
 right_target=(norm@old_world[names['R_Hand']]).translation.copy();right_pole=(norm@old_world[names['R_Forearm']]).translation.copy();right_q=old_world[names['R_Hand']].to_quaternion()
 left_target=Vector((.24,1.24,.25));left_pole=Vector((.40,1.14,.10))
 for side,wrist,pole in [('R_',right_target,right_pole),('L_',left_target,left_pole)]:author.solve_arm(rig,new,side,inv@wrist,inv@pole,names,parents,order)
 w=author.worlds(rig,new,parents,order);author.set_world_rotation(new,names['R_Hand'],right_q,w,parents)
 # Neutral wrist uses the actual rest forearm->hand relation, replacing the
 # inherited downward world-hand orientation; no arbitrary wrist-only flip.
 new[names['L_Hand']][1]=rest[names['L_Hand']][1].copy()
 curl={}
 for name,matrix in hands.items():
  if not name.startswith('L_'):continue
  index=names[name];native_q=matrix.to_quaternion();rest_q=rest[index][1]
  finger=next(f for f in ('Thumb','Index','Mid','Ring','Pinky') if name.startswith('L_'+f))
  amount=.30 if finger=='Thumb' else .18+.03*('Index','Mid','Ring','Pinky').index(finger)
  new[index][1]=rest_q.slerp(native_q,amount);curl[name]=amount
 guard=copy.deepcopy(new);guard_world=author.worlds(rig,guard,parents,order)
 left_guard=(norm@guard_world[names['L_Hand']]).translation.copy();left_guard_pole=(norm@guard_world[names['L_Forearm']]).translation.copy()
 poses=[];frames=[]
 for k in range(181):
  t=k/RATE;b=breath(t);local=copy.deepcopy(guard)
  w=author.worlds(rig,local,parents,order)
  author.set_world_rotation(local,names['Spine01'],Quaternion(xaxis,math.radians(-.7*b))@w[names['Spine01']].to_quaternion(),w,parents)
  for side,sign in [('L_',1.),('R_',-1.)]:
   w=author.worlds(rig,local,parents,order);author.set_world_rotation(local,names[side+'Clavicle'],Quaternion(zaxis,math.radians(.18*sign*b))@w[names[side+'Clavicle']].to_quaternion(),w,parents)
  for side,wrist,pole in [('R_',right_target,right_pole),('L_',left_guard+Vector((0,.001,.0015))*b,left_guard_pole+Vector((0,.001,.0015))*b)]:author.solve_arm(rig,local,side,inv@wrist,inv@pole,names,parents,order)
  w=author.worlds(rig,local,parents,order);author.set_world_rotation(local,names['R_Hand'],right_q,w,parents);local[names['L_Hand']][1]=rest[names['L_Hand']][1].copy()
  w=author.worlds(rig,local,parents,order);author.set_world_rotation(local,names['Head'],guard_world[names['Head']].to_quaternion(),w,parents)
  if t in (0.,DURATION):local=copy.deepcopy(guard)
  poses.append(local);w=author.worlds(rig,local,parents,order)
  frames.append({'source_seconds':t,'breath_weight':b,'chest_metres':list((norm@w[names['Spine02']]).translation),'L_hand_metres':list((norm@w[names['L_Hand']]).translation),'R_hand_metres':list((norm@w[names['R_Hand']]).translation)})
 guard_raw=OUT/'guard_raw.glb';guard_raw.write_bytes(encode(rig,binary,[guard,guard],[0.,DURATION],'guard_pose',tracks))
 gd,gb_=library.read_glb(guard_raw);guard_tracks,_=library.decode_animation(gd,gb_)
 idle_raw=OUT/'idle_raw.glb';idle_raw.write_bytes(encode(rig,binary,poses,[k/RATE for k in range(181)],'idle',tracks,guard_tracks))
 print('NATURAL_RAW_READY',digest(guard_raw),digest(idle_raw),flush=True)
 alignment_before_path=PRODUCER/'library/base_alignment.json';grounding=json.loads(alignment_before_path.read_text())['canonical_root_grounding']
 guard_preview,guard_align=prepare(guard_raw,'guard',character,manifest,body_path,grounding);idle_preview,idle_align=prepare(idle_raw,'idle',character,manifest,body_path,grounding)
 current_before=PRODUCER/'library/base_prepared_png.glb'
 dependencies=[Path(__file__),SOURCE,RIG,manifest_path,PRODUCER/'production_contract.py',Path(library.__file__),PRODUCER/'prepare_rigged_warrior.py',PRODUCER/'refine_character_grips.py',Path(author.__file__),Path(base.__file__),body_path,grip_path,alignment_before_path,FINE.parent/'run_blender.py']
 record={'status':'source_guard_and_breathing_idle_ready_pending_bounded_checks_and_visual_review','stage':'authored_raw','right_calibration_baked':False,'right_finger_calibration_applications':0,'body_source':character,'weapon_source':manifest['weapon_source'],'normalization_matrix_gltf':library.matrix_values(norm) if hasattr(library,'matrix_values') else [norm[r][c] for c in range(4) for r in range(4)],'preview_grounding':{k:grounding[k] for k in ('policy','constant_world_root_shift_metres','constant_local_root_shift')},'raws':[identity(guard_raw),identity(idle_raw)],'previews':[identity(guard_preview),identity(idle_preview)],'alignments':[identity(guard_align),identity(idle_align)],'before':{'asset':identity(current_before),'clip':'idle','source_seconds':0},'guard':{'clip':'guard_pose','role':'canonical reference pose only; not a new runtime guard clip or mode','sample_count':2,'source_range_seconds':[0,1.5]},'idle':{'clip':'idle','duration_seconds':1.5,'sample_rate_hz':120,'sample_count':181,'curve':'one small periodic1.5s inhale/exhale, exact closed guard endpoints; scalar cosine is smooth, exported glTF LINEAR is not globally C2','breath_peak_spine_pitch_degrees':-.7,'breath_peak_clavicle_lift_degrees':.18,'left_wrist_target_follow_metres':[0,.001,.0015]},'guard_authoring':{'clavicle_release_degrees':3.,'left_wrist_target_metres':list(left_target),'left_elbow_pole_metres':list(left_pole),'left_wrist':'actual rest forearm->hand local relation, no old dangling world Q','left_finger_native_curl_blend':curl,'right_wrist_and_weapon':'original v5guard world hand position/quaternion held through shoulder release and every breath sample','foot_policy':'all original root/hip/leg/foot local TRS payloads fixed, no root travel or foot IK drift'},'native_grip':identity(grip_path),'parent_v5_frozen':identity(SOURCE),'preview_policy':'Private base same-rest direct prepare only, target right-finger offsets once and existing target canonical root shift once; never use preview as RAW. Actual weapon binding including source Grip shift is handled by existing prepare_character.','production_boundary':{'HAND_POLICY':'Imported from production_contract.py; attack78/locomotion78 override native right15 only, left follows authored source.','retarget_interpolation':'Existing retarget_clip preserves source interpolation; it does not silently force this breath to STEP.','current_rejection_gates':'validate_source_clip requires locomotion idle91/walk185 keys, locked non-leg STEP and constant tracks; canonical_source_evidence locks the declared head ancestor chain and shared guard markers. New idle181/LINEAR-body breath is not represented as accepted current locomotion78.','Root_followup':'After source acceptance Root must coherently replace old locked source constraints, migrate idle/walk/three attack canonical guard, typed/proxy/binding and actual time consumer; no compatibility branch added.','actual_runtime_chain':'ArenaSession.effectiveEnemyPose -> ArenaOpponents.selectEnemyPose(IDLE/guardedHIT) -> LocomotionProfile.sourceSeconds(moving=false) returns idle.samples.first().sourceSeconds; EnemyAnimator alive pauses and setTime(state.enemyPoseSourceSeconds). A simulation/idle clock must drive both profile/proxy and SDK; repeat(-1) alone will not breathe.','contact_anchor_requirement':'Current LocomotionProfile expects idle contact/blade anchors constant. This candidate holds actual right hand/knife fixed; body/head motion still requires Root to migrate locked-body assumptions and drive one shared source clock.'},'frames':frames,'source_pins':{str(p.relative_to(REPO)):digest(p) for p in dependencies},'limits':['Source candidate and private base preview only; no published canonical family, runtime clock change, native playback or three-target acceptance.','Small breath amplitude does not imply continuous collision proof; bounded real surface tests and actual same-camera review remain required.']}
 write('natural_guard_authoring.json',record)
 print('NATURAL_PREVIEW_READY',str(guard_preview),digest(guard_preview),str(idle_preview),digest(idle_preview),flush=True)

if __name__=='__main__':build()
