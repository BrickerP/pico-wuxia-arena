"""Read-only float64 FK/rigidity diagnosis; authoritative profile deltas are recorded separately."""
import json,struct,math,hashlib,sys
from pathlib import Path
import numpy as np

REPO=Path(__file__).resolve().parents[6]
HERE=REPO/'ArtSource/tripo-warrior'
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from production_contract import production_binding

def require(condition,message):
 if not condition:raise ValueError(message)

def file_identity(path):
 path=Path(path).resolve();data=path.read_bytes()
 return {'path':path.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def rotation(q):
 q=np.asarray(q,dtype=float);q=q/np.linalg.norm(q);x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def local(node):
 if 'matrix' in node:return np.asarray(node['matrix'],float).reshape(4,4).T
 m=np.eye(4);m[:3,:3]=rotation(node.get('rotation',[0,0,0,1]))@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m

def rigid(a):
 u,s,vh=np.linalg.svd(a[:3,:3]);r=u@vh
 if np.linalg.det(r)<0:u[:,-1]*=-1;r=u@vh
 m=np.eye(4);m[:3,:3]=r;m[:3,3]=a[:3,3];return m,s

def angle(a,b):
 ra,_=rigid(a);rb,_=rigid(b);return math.degrees(math.acos(float(np.clip((np.trace(rb[:3,:3]@ra[:3,:3].T)-1)/2,-1,1))))

class GLB:
 def __init__(self,path,clip=None):
  self.path=Path(path).resolve();data=self.path.read_bytes();n=struct.unpack_from('<I',data,12)[0]
  self.doc=json.loads(data[20:20+n]);self.binary=data[28+n:];self.sha256=hashlib.sha256(data).hexdigest()
  self.names={n['name']:i for i,n in enumerate(self.doc['nodes'])};self.parents={c:i for i,n in enumerate(self.doc['nodes']) for c in n.get('children',[])}
  self.tracks={}
  if clip is not None:
   a=next(a for a in self.doc['animations'] if a['name']==clip)
   for c in a['channels']:
    sampler=a['samplers'][c['sampler']];self.tracks[c['target']['node'],c['target']['path']]=(self.accessor(sampler['input'])[:,0],self.accessor(sampler['output']),sampler.get('interpolation','LINEAR'))
 def accessor(self,index):
  a=self.doc['accessors'][index];v=self.doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  dtype=np.dtype({5126:'<f4',5123:'<u2',5121:'u1',5125:'<u4'}[a['componentType']]);start=v.get('byteOffset',0)+a.get('byteOffset',0)
  return np.ndarray((a['count'],width),dtype=dtype,buffer=self.binary,offset=start,strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize)).astype(float)
 def sample(self,track,time,path):
  times,values,interp=track;k=int(np.searchsorted(times,time,side='right'))
  if k==0:q=values[0]
  elif k==len(times) or times[k-1]==time or interp=='STEP':q=values[k-1]
  else:
   x=(time-times[k-1])/(times[k]-times[k-1]);a=values[k-1].copy();b=values[k].copy()
   if path!='rotation':return a+(b-a)*x
   a/=np.linalg.norm(a);b/=np.linalg.norm(b);d=float(np.dot(a,b))
   if d<0:b=-b;d=-d
   if d>.9995:q=a+(b-a)*x
   else:
    theta=math.acos(np.clip(d,-1,1));q=(math.sin((1-x)*theta)*a+math.sin(x*theta)*b)/math.sin(theta)
  return q/np.linalg.norm(q) if path=='rotation' else q
 def worlds(self,time=None,local_overrides=None):
  result={}
  def one(i):
   if i in result:return result[i]
   node=dict(self.doc['nodes'][i])
   if time is not None:
    for path in ('translation','rotation','scale'):
     if (i,path) in self.tracks:node[path]=self.sample(self.tracks[i,path],time,path)
   m=local(node) if local_overrides is None or i not in local_overrides else local_overrides[i];result[i]=one(self.parents[i])@m if i in self.parents else m;return result[i]
  for i in range(len(self.doc['nodes'])):one(i)
  return result
 def frame(self,world,name):return world[self.names[name]]

def serial_frame(m):
 r,s=rigid(m);return {'affine':m.tolist(),'rigid':r.tolist(),'singular_values':s.tolist(),'affine_determinant':float(np.linalg.det(m[:3,:3]))}

def delta(a,b):return (b[:3,3]-a[:3,3])

def vector_row(v):return {'metres':v.tolist(),'length_mm':float(np.linalg.norm(v)*1000)}

def main():
 manifest=json.loads((HERE/'motion_library.json').read_text());request=json.loads((HERE/'library/production_review_request.json').read_text())
 bank_index=json.loads((HERE/'library/characters.json').read_text())
 indexed={row['id']:row for row in bank_index['characters']};reviewed={row['id']:row for row in request['characters']}
 from_binding=json.dumps(request['binding'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 require(hashlib.sha256(from_binding).hexdigest()==request['binding_sha256'],'Formal bank binding digest mismatch')
 current_binding=json.dumps(production_binding(manifest),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 require(current_binding==from_binding,'Current manifest sources differ from the measured formal bank')
 require(set(indexed)=={'base','indigo','veteran'} and set(reviewed)==set(indexed),'Expected exactly the three formal targets')
 locomotion_author_path=(HERE/manifest['locomotion_source']['authoring_manifest']['source']).resolve()
 locomotion_author_identity=file_identity(locomotion_author_path)
 require(locomotion_author_identity['sha256']==manifest['locomotion_source']['authoring_manifest']['source_sha256'],'Locomotion authoring identity mismatch')
 locomotion_author=json.loads(locomotion_author_path.read_text())
 family_identity=locomotion_author['source_verification']['authoring']
 family_author_path=(REPO/family_identity['file']).resolve()
 require(file_identity(family_author_path)['sha256']==family_identity['sha256'] and file_identity(family_author_path)['bytes']==family_identity['bytes'],'Family authoring identity mismatch')
 author=json.loads(family_author_path.read_text())
 source_entry=next(r for r in manifest['locomotion_source']['clips'] if r['name']=='idle')
 source=GLB(HERE/source_entry['source'],'idle');source_rig=GLB(HERE/manifest['locomotion_source']['source']);source_rest=source_rig.worlds()
 require(source.sha256==source_entry['source_sha256']==author['outputs']['idle']['raw']['sha256'] and source_rig.sha256==manifest['locomotion_source']['source_sha256'],'Source RAW or rig identity mismatch')
 ns=np.asarray(author['normalization_matrix_gltf']).reshape(4,4).T
 raw_times=sorted({float(t) for times,_,_ in source.tracks.values() for t in times})
 profile_times={float(row['source_seconds']) for cid in ('base','indigo','veteran') for row in json.loads((HERE/'library'/(cid+'_attack_profiles.json')).read_text())['locomotion']['idle']['samples']}
 times=sorted(set(raw_times)|profile_times)
 require(len(raw_times)==181 and len(times)==361,'Expected181 RAW keys and361 profile times')
 source_world={t:source.worlds(t) for t in times};sw={t:ns@source.frame(w,'R_Hand') for t,w in source_world.items()}
 report={'schema_version':1,'status':'reproduced_target_motion_engineering_review',
 'implementation':file_identity(__file__),
 'runtime':{'python':sys.version.split()[0],'numpy':np.__version__,'computation':'float64; no Blender or device runtime'},
 'inputs':{'motion_library_binding':{'manifest_path':'ArtSource/tripo-warrior/motion_library.json','sha256':request['binding_sha256'],
  'identity_scope':'production_contract.production_binding projection; production_review excluded to prevent a review-to-report hash cycle'},
  'binding_contract_implementation':file_identity(HERE/'production_contract.py'),
  'locomotion_authoring':locomotion_author_identity,
  'formal_bank_index':file_identity(HERE/'library/characters.json'),
  'formal_bank_review_request':file_identity(HERE/'library/production_review_request.json'),
  'source_family_authoring':file_identity(family_author_path),
  'source_idle':file_identity(source.path),'source_rig':file_identity(source_rig.path)},
 'method':'float64 GLB TRS FK with normalized shortest-arc SLERP; exact source/profile identities fixed. Not bit-identical to Blender float32; profile values are separately authoritative.',
 'derivation':{
  'retarget_rotation':'For joint i: Rt_i(t)=Ds_i(t)*Bt_i, where Ds_i(t)=Rs_i(t)*inverse(Bs_i). Target local translations and scales retain their own rest values.',
  'position':'For a parent-to-child edge, its translated contribution is A_parent(t)*local_translation_child. Equal source/target world rotations do not make unequal rest segment vectors cancel.',
  'independent_prediction':'delta_wrist_target = delta_wrist_source + sum[Nt*(Ds_parent(t)-Ds_parent(0))*Bt_parent_affine*local_t - Ns*(Ds_parent(t)-Ds_parent(0))*Bs_parent_affine*local_s].',
  'assumptions':'The idle root/hip are fixed, non-root local translations/scales are fixed, and source and target use the same prepared-axis rotation. Observed float32 retarget quantization is reported as prediction residual, not removed.'},
 'raw_key_count':len(raw_times),'evaluated_source_and_target_times':len(times),'binding_sha256':request['binding_sha256'],'source_idle_sha256':source.sha256,'source_rig_sha256':source_rig.sha256,
 'source_normalization_provenance':'actual family_authoring.normalization_matrix_gltf',
 'source_hand_frames':{str(t):serial_frame(sw[t]) for t in (0,.75,1.5)},'source_wrist_peak_delta':vector_row(delta(sw[0],sw[.75])),
 'maximum_source_wrist_displacement_m':max(float(np.linalg.norm(delta(sw[0],v))) for v in sw.values()),'source_peak_rigid_rotation_degrees':angle(sw[0],sw[.75]),'targets':{}}
 for character in manifest['characters']:
  cid=character['id'];target=GLB(HERE/'library'/character['output'],'idle');raw=GLB(HERE/character['source']);bind=raw.worlds()
  frames={t:target.worlds(t) for t in times};hand={t:target.frame(w,'R_Hand') for t,w in frames.items()};start=hand[0];peak=hand[.75]
  nt=local(target.doc['nodes'][target.names['TripoBody_Root']]);profile=json.loads((HERE/'library'/(cid+'_attack_profiles.json')).read_text())
  profile_identity=file_identity(HERE/'library'/(cid+'_attack_profiles.json'))
  model_entry=next(row for row in indexed[cid]['outputs'] if row['file']==character['output'])
  reviewed_model=next(row for row in reviewed[cid]['outputs'] if row['file']==character['output'])
  require(target.sha256==profile['model_sha256']==model_entry['sha256']==reviewed_model['sha256'] and raw.sha256==character['source_sha256'],'Target source or formal model identity mismatch: '+cid)
  require(profile_identity['sha256']==indexed[cid]['attack_profiles']['sha256']==reviewed[cid]['attack_profiles_sha256'],'Formal profile identity mismatch: '+cid)
  samples=profile['locomotion']['idle']['samples'];p0=samples[0];pm=min(samples,key=lambda r:abs(r['source_seconds']-.75))
  blade={name:{t:target.frame(w,name) for t,w in frames.items()} for name in ('Blade_Base','Blade_Tip')}
  lengths=[float(np.linalg.norm(blade['Blade_Tip'][t][:3,3]-blade['Blade_Base'][t][:3,3])) for t in times]
  wrist_delta=delta(start,peak);positions=[];mounts={}
  for name,field in [('Blade_Base','blade_base'),('Blade_Tip','blade_tip')]:
   mount=np.linalg.inv(start)@blade[name][0];m0=mount[:3,3]
   lever=(peak[:3,:3]-start[:3,:3])@m0;actual=delta(blade[name][0],blade[name][.75])
   mounts[name]={'maximum_trajectory_displacement_m':max(float(np.linalg.norm(delta(blade[name][0],blade[name][t]))) for t in times),'hand_local_marker_matrix':mount.tolist(),'mount_constancy_max_component':max(float(np.max(np.abs(np.linalg.inv(hand[t])@blade[name][t]-mount))) for t in times),
    'actual_delta':vector_row(actual),'wrist_translation_part':vector_row(wrist_delta),'rotation_affine_lever_part':vector_row(lever),
    'reconstruction_error_metres':float(np.linalg.norm(actual-wrist_delta-lever)),
    'authoritative_profile_delta':vector_row(np.asarray(pm[field])-p0[field])}
  chain=[];i=source.names['R_Hand']
  while i in source.parents:
   parent=source.parents[i];name=source.doc['nodes'][i]['name'];parent_name=source.doc['nodes'][parent]['name']
   if name in raw.names and parent_name in raw.names:
    q0,_=rigid(source.frame(source_world[0],parent_name));qt,_=rigid(source.frame(source_world[.75],parent_name));qr,_=rigid(source_rig.frame(source_rest,parent_name))
    d=(qt[:3,:3]-q0[:3,:3])@qr[:3,:3].T
    vs=local(source_rig.doc['nodes'][source_rig.names[name]])[:3,3];vt=local(raw.doc['nodes'][raw.names[name]])[:3,3]
    source_contribution=ns[:3,:3]@d@source_rig.frame(source_rest,parent_name)[:3,:3]@vs
    target_contribution=nt[:3,:3]@d@raw.frame(bind,parent_name)[:3,:3]@vt
    chain.append({'child':name,'parent':parent_name,'source_contribution':source_contribution.tolist(),'target_contribution':target_contribution.tolist(),
      'rest_vector_difference_contribution_mm':float(np.linalg.norm(target_contribution-source_contribution)*1000)})
   i=parent
  ps=sum((np.asarray(r['source_contribution']) for r in chain),np.zeros(3));pt=sum((np.asarray(r['target_contribution']) for r in chain),np.zeros(3))
  predicted=delta(sw[0],sw[.75])+pt-ps
  predictions=[]
  for time in times:
   residual=np.zeros(3)
   for edge in chain:
    child,parent=edge['child'],edge['parent']
    sr,_=rigid(source.frame(source_rest,parent));s0,_=rigid(source.frame(source_world[0],parent));st,_=rigid(source.frame(source_world[time],parent))
    rd=(st[:3,:3]-s0[:3,:3])@sr[:3,:3].T
    vs=local(source_rig.doc['nodes'][source_rig.names[child]])[:3,3];vt=local(raw.doc['nodes'][raw.names[child]])[:3,3]
    residual+=nt[:3,:3]@rd@raw.frame(bind,parent)[:3,:3]@vt-ns[:3,:3]@rd@source.frame(source_rest,parent)[:3,:3]@vs
   estimate=delta(sw[0],sw[time])+residual;actual=delta(start,hand[time])
   predictions.append({'source_seconds':time,'predicted_target_delta_m':estimate.tolist(),'actual_target_delta_m':actual.tolist(),'prediction_residual_m':float(np.linalg.norm(estimate-actual))})
  bones={}
  for a,b in [('R_Clavicle','R_Upperarm'),('R_Upperarm','R_Forearm'),('R_Forearm','R_Hand')]:
   source_length=float(np.linalg.norm((ns@source.frame(source_world[0],b))[:3,3]-(ns@source.frame(source_world[0],a))[:3,3]))
   target_lengths=[float(np.linalg.norm(target.frame(w,b)[:3,3]-target.frame(w,a)[:3,3])) for w in frames.values()]
   bones[a+'->'+b]={'source_length_m':source_length,'target_length_m':target_lengths[0],'target_source_ratio':target_lengths[0]/source_length,
      'max_temporal_length_change_m':max(abs(x-target_lengths[0]) for x in target_lengths)}
  singulars=[rigid(h)[1] for h in hand.values()];rotation_delta=angle(start,peak)
  hand_rs,_=rigid(source.frame(source_rest,'R_Hand'));hand_rt,_=rigid(raw.frame(bind,'R_Hand'))
  wanted0=nt[:3,:3]@rigid(source.frame(source_world[0],'R_Hand'))[0][:3,:3]@hand_rs[:3,:3].T@hand_rt[:3,:3]
  wanted1=nt[:3,:3]@rigid(source.frame(source_world[.75],'R_Hand'))[0][:3,:3]@hand_rs[:3,:3].T@hand_rt[:3,:3]
  actual_rotation_error=max(float(np.max(np.abs(rigid(hand[t])[0][:3,:3]-rigid(np.block([[wanted,np.zeros((3,1))],[np.zeros((1,3)),np.ones((1,1))]]))[0][:3,:3]))) for t,wanted in [(0,wanted0),(.75,wanted1)])
  head_delta=np.asarray(pm['head'])-p0['head'];body_delta=np.asarray(pm['body_top'])-p0['body_top']
  # These checks are reconstruction/rigidity checks, separate from the2mm authoring budget.
  def pair_invariants(first,second):
   errors=[]
   h0=target.frame(first,'R_Hand');h1=target.frame(second,'R_Hand')
   for marker in ('Blade_Base','Blade_Tip'):
    a=np.linalg.inv(h0)@target.frame(first,marker);b=np.linalg.inv(h1)@target.frame(second,marker)
    if np.max(np.abs(a-b))>1e-10:errors.append('hand_local_mount_varies:'+marker)
   for a,b in [('R_Clavicle','R_Upperarm'),('R_Upperarm','R_Forearm'),('R_Forearm','R_Hand')]:
    x=np.linalg.norm(target.frame(first,b)[:3,3]-target.frame(first,a)[:3,3]);y=np.linalg.norm(target.frame(second,b)[:3,3]-target.frame(second,a)[:3,3])
    if abs(x-y)>1e-6:errors.append('bone_length_varies:'+a+'->'+b)
   return errors
  normal_errors={str(t):pair_invariants(frames[0],frames[t]) for t in times if pair_invariants(frames[0],frames[t])}
  require(not normal_errors,'Temporal mount or bone rigidity check failed: '+str(normal_errors))
  grip_index=target.names['HandGrip_R'];bad_grip=local(target.doc['nodes'][grip_index]).copy();bad_grip[0,3]+=.005
  mount_errors=pair_invariants(frames[0],target.worlds(.75,{grip_index:bad_grip}))
  joint=target.names['R_Forearm'];parent=target.parents[joint];bad_bone=np.linalg.inv(frames[.75][parent])@frames[.75][joint];bad_bone[:3,3]*=1.01
  bone_errors=pair_invariants(frames[0],target.worlds(.75,{joint:bad_bone}))
  require(any(e.startswith('hand_local_mount_varies') for e in mount_errors),'Dynamic mount negative fixture was not rejected')
  require(any(e.startswith('bone_length_varies') for e in bone_errors),'Bone-length negative fixture was not rejected')
  exact_profile_loop=all(samples[0][field]==samples[-1][field] for field in ('head','body_bottom','body_top','blade_base','blade_tip'))
  require(exact_profile_loop,'Profile loop must close exactly: '+cid)
  marker_profile_errors={}
  for field,name in [('blade_base','Blade_Base'),('blade_tip','Blade_Tip')]:
   marker_profile_errors[field]=max(float(np.linalg.norm(target.frame(frames[row['source_seconds']],name)[:3,3]-row[field])) for row in samples)
  max_profile_drift={field:max(float(np.linalg.norm(np.asarray(row[field])-samples[0][field])) for row in samples) for field in ('head','body_top','blade_base','blade_tip')}
  require(max(max_profile_drift['blade_base'],max_profile_drift['blade_tip'])<=.002,'Target2mm micromotion authoring budget exceeded: '+cid)
  report['targets'][cid]={'formal_model':file_identity(target.path),'formal_profile':profile_identity,'raw_target':file_identity(raw.path),'model_sha256':target.sha256,'raw_target_sha256':raw.sha256,'raw_grip_frame':character['grip_frame'],
   'actual_grip_local_matrix':local(target.doc['nodes'][target.names['HandGrip_R']]).tolist(),
   'actual_grip_local_determinant':float(np.linalg.det(local(target.doc['nodes'][target.names['HandGrip_R']])[:3,:3])),
   'fixed_root_hip_max_translation_change_m':{name:max(float(np.linalg.norm(target.frame(w,name)[:3,3]-target.frame(frames[0],name)[:3,3])) for w in frames.values()) for name in ('BoneRoot','Hip')},
   'all_animated_local_translation_scale_max_component_change':max(float(np.max(np.abs(values-values[0]))) for (_,path),(_,values,_) in target.tracks.items() if path in ('translation','scale')),
   'hand_frames':{str(t):serial_frame(hand[t]) for t in (0,.75,1.5)},'raw_rest_hand_frame':serial_frame(raw.frame(bind,'R_Hand')),
   'wrist_peak_delta':vector_row(wrist_delta),'maximum_wrist_drift_m':max(float(np.linalg.norm(delta(start,h))) for h in hand.values()),
   'wrist_rigid_rotation_peak_degrees':rotation_delta,'source_world_rest_rotation_transfer_max_matrix_error':actual_rotation_error,
   'hand_affine_relative_singular_value_variation':max(float(np.max(np.abs(v/singulars[0]-1))) for v in singulars),
   'bones':bones,'markers':mounts,'blade_length_m':lengths[0],'blade_length_max_change_m':max(abs(v-lengths[0]) for v in lengths),
   'profile_head_delta':vector_row(head_delta),'profile_body_top_delta':vector_row(body_delta),
   'wrist_drift_fraction_of_head_motion':float(np.linalg.norm(wrist_delta)/np.linalg.norm(head_delta)),
   'profile_sample_count':len(samples),'profile_loop_exact':exact_profile_loop,'max_profile_trajectory_displacement_m':max_profile_drift,
   'maximum_profile_marker_vs_float64_GLB_discrepancy_m':marker_profile_errors,
   'maximum_profile_dual_marker_displacement_difference_m':max(float(np.linalg.norm((np.asarray(row['blade_base'])-p0['blade_base'])-(np.asarray(row['blade_tip'])-p0['blade_tip']))) for row in samples),
   'maximum_profile_blade_length_change_m':max(abs(float(np.linalg.norm(np.asarray(row['blade_tip'])-row['blade_base']))-float(np.linalg.norm(np.asarray(p0['blade_tip'])-p0['blade_base']))) for row in samples),
   'micromotion_budget_passed':max(max_profile_drift['blade_base'],max_profile_drift['blade_tip'])<=.002,
   'budget_fraction_of_blade_length':.002/lengths[0],'budget_fraction_of_profile_head_breathing':.002/max_profile_drift['head'],
   'all_times_pair_invariants_passed':not normal_errors,'negative_cases':{'hand_local_mount_translation_plus0p005':{'space':'HandGrip_R local GLB coordinates; not prepared-world metres','detected':mount_errors},'forearm_offset_times1p01':{'detected':bone_errors}},
   'wrist_drift_fraction_of_blade_length':float(np.linalg.norm(wrist_delta)/lengths[0]),
   'rest_vector_mismatch_prediction':vector_row(predicted),'prediction_residual_m':float(np.linalg.norm(predicted-wrist_delta)),
   'source_FK_prediction_residual_m':float(np.linalg.norm(ps-delta(sw[0],sw[.75]))),
   'prediction_across_loop':predictions,'maximum_prediction_residual_m':max(r['prediction_residual_m'] for r in predictions),
   'largest_rest_vector_contributions':sorted(chain,key=lambda r:r['rest_vector_difference_contribution_mm'],reverse=True)}
  print(cid,'wrist_mm',np.linalg.norm(wrist_delta)*1000,'pred_mm',np.linalg.norm(predicted)*1000,'prediction_error_mm',np.linalg.norm(predicted-wrist_delta)*1000,'length_changes',bones,flush=True)
 report['production_budget']={'target_blade_micromotion_metres':.002,'decision':'Root accepted morphology-aware natural FK on2026-11-16; source-only near-fixed grip is not a universal target end-effector lock.',
 'basis':'2mm is under0.3percent of the measured0.720676m blade and below the approximately4.5-5mm head-breathing motion. It is an authoring budget, not floating-point or collision tolerance.',
 'unchanged_gates':'No change to root/foot1e-6 or exact closed-loop checks. Mount and bone fixtures are evaluated independently of the2mm budget.'}
 report['conclusion']={
  'classification':'Expected FK consequence of rotation-only world-rest retarget with preserved target lengths/rest vectors; source fixed wrist is not a target end-effector constraint.',
  'drift_cause_scope':'Temporal hand-to-blade marker matrices are constant and lengths are preserved; varying mount/scale does not cause the measured drift. Static ergonomic grip/mesh clearance is not assessed by these matrix checks.',
  'original_commitment_scope':'The source RHand/dao was held near fixed. A universal10micrometre target lock was not established by the rotation-transfer contract.',
  'recommendation':'Root selected existing morphology-aware FK with2mm target micromotion authoring budget; retain source-only near-fixed grip, exact loop and original root/foot checks. No production/test file is changed by this diagnosis.',
  'options':[
   {'name':'Preserve morphology-aware natural FK',
    'implementation':'Keep current retarget. Root may define verification around unchanged bone/knife lengths, constant mount, closed loop, temporal world-rest rotation transfer, and an independently predicted target FK trajectory. Keep source near-fixed grip as a source assertion only.',
    'tradeoff':'No new deformation or helper/IK changes. Indigo/veteran retain measured0.397/1.051mm natural wrist translation, about0.055/0.146percent of blade length. A10micrometre target-position assertion would need an explicitly different contract, not a larger unexplained epsilon.'},
   {'name':'Add explicit target end-effector constraint',
    'implementation':'At existing idle keys solve a two-bone right-arm IK using the target actual lengths, guard-time wrist anchor plus scaled source wrist displacement, source-transferred hand orientation, and a continuous source-derived elbow pole. Keep shoulder/chest breathing, all original key times, rest/IBM/Grip/fingers, and deterministic closed endpoints. Reconcile elbow/twist helper support using real weights; regenerate/review all three targets.',
    'tradeoff':'Produces designed steady hands across morphologies without stretch or copied endpoint frames, but changes target arm curves and needs reachability, pole continuity, helper deformation, clearance and canonical-boundary review. It is a new constraint absent from the present rotation-only transfer, not a numerical bug patch.'}
  ]}
 (OUT/'measurement.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
 print('Saved',OUT/'measurement.json')

if __name__=='__main__':main()
