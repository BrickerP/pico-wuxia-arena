"""Private natural-guard canonical-family RAW migration. No public writes.
Keep accepted breathing idle intact, preserve walk legs and attack interiors,
and migrate only the canonical pose using bounded local guard deltas.
"""
import copy,hashlib,importlib.util,json,math,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[3]
OUT=HERE/'candidate/family-v1';PRODUCER=REPO/'ArtSource/tripo-warrior'
FINE=REPO/'ArtSource/refinement/hand-poses/fine-overhead'
sys.path.insert(0,str(FINE));import build_fine_overhead as base
library,author=base.library,base.author
from mathutils import Quaternion,Vector
import numpy as np
GUARD=HERE/'candidate/v1/guard_raw.glb';GUARD_SHA='c9a9673852343f922c7c5cfc026dc63a5c21b89b037f2729c5ea42cdf9a23ee4'
IDLE=HERE/'candidate/v1/idle_raw.glb';IDLE_SHA='0cac7c29e9fd9445e3b1e1825c60e885323b870181df33c5242fc0b6b40d95a6'
RIG=PRODUCER/'refined-base60k/rig.glb'
RIG_SHA='43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6'
ATTACKS=('attack_overhead','attack_left','attack_right')
CLIPS=('idle','walk',*ATTACKS)
MOVING_LEGS={s+b for s in ('L_','R_') for b in ('Thigh','Calf','Foot')}

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def identity(path):
 p=Path(path);return {'file':str(p.relative_to(REPO)),'sha256':digest(p),'bytes':p.stat().st_size}
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def correction_weight(t):
 if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or not 0<=t<=1.75:raise ValueError('finite attack source0..1.75 required')
 if t==0 or t==1.75:return 1.
 if t<.20:return 1.-base.smooth(t/.20)
 if t>1.50:return base.smooth((t-1.50)/.25)
 return 0.
def patch_row(doc,binary,channel,k,row):
 a=doc['accessors'][doc['animations'][0]['samplers'][channel['sampler']]['output']];v=doc['bufferViews'][a['bufferView']];width=4 if channel['target']['path']=='rotation' else 3
 assert a['componentType']==5126 and v.get('byteStride',width*4)==width*4
 offset=v.get('byteOffset',0)+a.get('byteOffset',0)+k*width*4
 struct.pack_into('<'+'f'*width,binary,offset,*row)
def quat(row):return Quaternion((row[3],row[0],row[1],row[2])).normalized()
def tupleq(q):return (q.x,q.y,q.z,q.w)

def migrate_attack(path,name,guard_tracks):
 doc,binary=library.read_glb(path);tracks,times=library.decode_animation(doc,binary);packed=bytearray(binary);names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
 changed=[];correction_angles={};before_end=[]
 for c in doc['animations'][0]['channels']:
  key=c['target']['node'],c['target']['path'];node,path_=key;bone=doc['nodes'][node]['name'];old=tracks[key][1][0];new=guard_tracks[key][1][0]
  if tracks[key][1][0]!=tracks[key][1][-1]:raise ValueError(name+' old guard endpoints not exact:'+bone+'/'+path_)
  if path_=='rotation':
   delta=quat(new)@quat(old).inverted()
   if delta.w<0:delta.negate()
   active=math.degrees(delta.angle)>1e-5
   if active:correction_angles[bone]=math.degrees(delta.angle)
  else:active=max(abs(x-y) for x,y in zip(new,old))>0.
  altered=[]
  for k,t in enumerate(times):
   w=correction_weight(float(t));original=tracks[key][1][k]
   if k in (0,len(times)-1):result=new
   elif not w or not active:continue
   elif path_=='rotation':
    q=Quaternion((1,0,0,0)).slerp(delta,w)@quat(original);q.normalize();result=tupleq(q)
    if sum(x*y for x,y in zip(result,original))<0:result=tuple(-x for x in result)
   else:result=tuple(x+w*(b-a) for x,a,b in zip(original,old,new))
   if result!=original:patch_row(doc,packed,c,k,result);altered.append(k)
  if altered:changed.append({'node':bone,'path':path_,'key_indices':altered})
 doc.setdefault('extras',{})['natural_guard_family']={'stage':'authored_raw','right_calibration_baked':False,'parent_sha256':digest(path),'guard_sha256':GUARD_SHA,'guard_delta_windows_seconds':[[0,.20],[1.50,1.75]],'interior_key_payloads_preserved':True}
 doc['animations'][0]['name']=name;out=OUT/(name+'_raw.glb');out.write_bytes(library.encode_glb(doc,packed))
 return out,{'method':'Per-joint local minimum-angle delta(new_guard * old_guard^-1), faded only in canonical entry/return; original per-key motion is retained underneath.','guard_correction_rotation_degrees':correction_angles,'changed_streams':changed,'nominal_correction_windows_seconds':[[0,.20],[1.50,1.75]],'source_timeline':times,'interior_range_seconds':[.20,1.50],'interior_key_payloads_byte_identical':True,'guard_endpoints_exact_234':True,'interpolation':'original LINEAR unchanged; C2 refers only to analytic scalar correction weight'}

def migrate_walk(path,guard_tracks):
 doc,binary=library.read_glb(path);tracks,times=library.decode_animation(doc,binary);packed=bytearray(binary);changed=[]
 for c in doc['animations'][0]['channels']:
  key=c['target']['node'],c['target']['path'];node,path_=key;bone=doc['nodes'][node]['name']
  if bone in MOVING_LEGS and path_=='rotation':continue
  value=guard_tracks[key][1][0]
  if any(tuple(row)!=tuple(value) for row in tracks[key][1]):
   changed.append(bone+'.'+path_)
   for k in range(len(times)):patch_row(doc,packed,c,k,value)
 doc.setdefault('extras',{})['natural_guard_family']={'stage':'authored_raw','right_calibration_baked':False,'parent_sha256':digest(path),'guard_sha256':GUARD_SHA,'method':'new canonical upper body and static support transforms; original six moving leg curves untouched'}
 doc['animations'][0]['name']='walk';out=OUT/'walk_raw.glb';out.write_bytes(library.encode_glb(doc,packed))
 return out,{'changed_streams':changed,'original_six_leg_rotation_payloads_and_interpolation_unchanged':True,'source_timeline':times,'guard_markers_seconds':[0,1/3,1.5],'source_loop_seconds':[1/3,1.5],'source_loop_duration_seconds':7/6}

def prepare_preview(raws,character,manifest):
 body_path,target,tb=library.pinned_source(character)
 for path in raws.values():doc,_=library.read_glb(path);library.require_same_rest(target,doc)
 body=OUT/'base_family_body.glb';preview=OUT/'base_family_preview.glb';alignment_path=OUT/'base_family_alignment.json'
 def lexical(p):return PRODUCER/('../refinement/combat-direction/natural-guard/'+str(p.relative_to(HERE)))
 clips=[(name,lexical(raws[name]),digest(raws[name])) for name in CLIPS]
 alignment=library.prepare_character(body_path,character['source_sha256'],clips,body,preview,alignment_path,height=character['height_metres'],grip_frame=character['grip_frame'],finger_rotation_offsets=character.get('finger_rotation_offsets'),weapon_source=manifest['weapon_source'])
 grounding_path=PRODUCER/'library/base_alignment.json';g=json.loads(grounding_path.read_text())['canonical_root_grounding'];shift=g['constant_local_root_shift']
 for path in (body,preview):
  doc,binary=library.read_glb(path);binary=bytearray(binary);root=next(i for i,n in enumerate(doc['nodes']) if n.get('name')=='BoneRoot')
  for animation in doc['animations']:
   for c in animation['channels']:
    if c['target']!={'node':root,'path':'translation'}:continue
    a=doc['accessors'][animation['samplers'][c['sampler']]['output']];v=doc['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0)
    for k in range(a['count']):row=struct.unpack_from('<3f',binary,start+k*12);struct.pack_into('<3f',binary,start+k*12,*[x+y for x,y in zip(row,shift)])
  path.write_bytes(library.encode_glb(doc,binary))
 alignment['canonical_root_grounding']={k:g[k] for k in ('policy','constant_world_root_shift_metres','constant_local_root_shift')}
 alignment['private_natural_family']={'raws':{name:identity(path) for name,path in raws.items()},'direct_same_rest_base_prepare':True,'right_finger_offset_applications':1,'target_existing_constant_root_shift_applications':1,'source_guard':identity(GUARD),'not_published_family':True}
 alignment['outputs']=[identity(p) for p in (body,preview)];alignment_path.write_text(json.dumps(alignment,indent=2)+'\n')
 return preview,alignment_path,alignment,body_path

def build():
 OUT.mkdir(parents=True,exist_ok=True)
 for path,expected in [(GUARD,GUARD_SHA),(IDLE,IDLE_SHA),(RIG,RIG_SHA)]:
  if digest(path)!=expected:raise ValueError('frozen source identity changed:'+str(path))
 guard,gb=library.read_glb(GUARD);guard_tracks,_=library.decode_animation(guard,gb);rig,rigb=library.read_glb(RIG);library.require_same_rest(guard,rig)
 mp=PRODUCER/'motion_library.json';manifest=json.loads(mp.read_text());inputs={};raws={};changes={}
 for family in ('locomotion_source','attack_source'):
  for entry in manifest[family]['clips']:
   path,doc,binary=library.pinned_source(entry);library.require_same_rest(doc,rig);inputs[entry['name']]=identity(path)
 # Accepted breathing idle is copied without re-encoding or downsampling.
 idle=OUT/'idle_raw.glb';idle.write_bytes(IDLE.read_bytes());raws['idle']=idle;inputs['idle']=identity(IDLE)
 walk=REPO/inputs['walk']['file'];raws['walk'],changes['walk']=migrate_walk(walk,guard_tracks)
 for name in ATTACKS:raws[name],changes[name]=migrate_attack(REPO/inputs[name]['file'],name,guard_tracks)
 rows={}
 for name,path in raws.items():
  d,b=library.read_glb(path);t,keys=library.decode_animation(d,b)
  endpoint_delta=0.;names={n.get('name'):i for i,n in enumerate(d['nodes'])}
  for key,track in t.items():
   for value in (track[1][0],track[1][-1]):endpoint_delta=max(endpoint_delta,max(abs(x-y) for x,y in zip(value,guard_tracks[key][1][0])))
  if endpoint_delta!=0.:raise ValueError(name+' new canonical endpoint float32 mismatch:'+str(endpoint_delta))
  rows[name]={'raw':identity(path),'clip':name,'track_count':len(t),'joint_count':len(d['skins'][0]['joints']),'sample_count':len(keys),'source_range_seconds':[keys[0],keys[-1]],'endpoint_max_component_difference_from_natural_guard':endpoint_delta}
  if name=='idle':rows[name].update(source_loop_seconds=[0.,1.5],source_loop_duration_seconds=1.5,interpolation='LINEAR')
  if name=='walk':rows[name].update(source_loop_seconds=[1/3,1.5],source_loop_duration_seconds=7/6)
  print('FAMILY_RAW',name,digest(path),'keys',len(keys),'endpoint_delta',endpoint_delta,flush=True)
 early={'status':'five_RAWs_ready_exact_canonical_endpoints_finite_pending','guard':identity(GUARD),'inputs':inputs,'outputs':rows,'changes':changes}
 write('family_raw_identity.json',early)
 character=next(c for c in manifest['characters'] if c['id']=='base')
 preview,alignment_path,alignment,body_path=prepare_preview(raws,character,manifest)
 metadata={**early,'status':'private_family_candidate_ready_pending_independent_finite_review','stage':'authored_raw','right_calibration_baked':False,'R15_policy':'original native2.117 constant UNBAKED; target calibration only in private preview once','normalization_matrix_gltf':alignment['normalization_matrix_gltf'],'body_source':character,'weapon_source':manifest['weapon_source'],'preview_grounding':alignment['canonical_root_grounding'],'preview':identity(preview),'alignment':identity(alignment_path),'clock_contract':{'idle':{'source_loop_seconds':[0.,1.5],'source_loop_duration_seconds':1.5,'driver':'existing enemyMotionNanos modulo1.5 source seconds; same profile/proxy/SDK source sample'},'walk':{'source_loop_seconds':[1/3,1.5],'source_loop_duration_seconds':7/6,'driver':'existing signed gait distance'},'shared_idle_motion_time':'idle preparation and countdown share enemyMotionNanos; user pause/hit-stop/sustained steel contact freeze the same clock','SDK':'EnemyAnimator remains manual shared-source setTime, never independent repeat'},'production_boundary':{'canonical_guard':'guard_pose is reference only, no new runtime mode or clip','handoff_for_Root':'Root updates existing canonical family gate/profiles/typed/binding as one path; no91/STEP downgrade and no old/new fallback','head_policy':'No locked-head ancestor constraint is emitted or migrated for idle. Breathing body/head evaluated at the shared source time.','source_marker_policy':'idle0/1.5 match new guard; idle absolute1/3 is intentionally breathing. Walk0/1/3/1.5 and attack0/1.75 match canonical reference.'},'source_pins':{str(p.relative_to(REPO)):digest(p) for p in [Path(__file__),GUARD,IDLE,RIG,mp,Path(library.__file__),PRODUCER/'prepare_rigged_warrior.py',PRODUCER/'production_contract.py',Path(author.__file__),Path(base.__file__),body_path,PRODUCER/'library/base_alignment.json',FINE.parent/'run_blender.py']},'limits':['Source/base private candidate only; no producer/public/runtime/device changes or three-target acceptance.','Finite surfaces and transition steps require independent evidence; endpoint equality alone is not pose quality or continuous clearance.']}
 write('family_authoring.json',metadata)
 print('FAMILY_PREVIEW_READY',str(preview),digest(preview),flush=True)
if __name__=='__main__':build()
