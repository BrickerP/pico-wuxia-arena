"""Seal the natural guard/idle source candidate without changing the family."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import json,hashlib
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1];REPO=LANE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'file':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size}
def read(name):return json.loads((OUT/name).read_text())
def main():
 a=read('natural_guard_authoring.json');v=read('verification_natural_guard.json');marker=read('verification_legacy_marker.json')
 assert v['status']=='bounded_base_source_checks_passed' and v['sample_count']==49 and v['overlap_sample_count']==0
 assert v['authoring']==identity(OUT/'natural_guard_authoring.json')
 for name,row in v['assets'].items():assert identity(OUT/name)==row
 assert sha(REPO/a['parent_v5_frozen']['file'])=='85d633ec61534c62f59269c1d9f02854e829d1b84db33a91e3a3afac2e779076'
 assert marker['exact_endpoint_payload_comparisons']['source0_and1p5_equal_new_guard_float32_values']
 drift=[];dependency_snapshots=[]
 for stage,pins in [('build',a['source_pins']),('verification',v['verification_source_pins'])]:
  for relative,expected in pins.items():
   original=REPO/relative;actual=sha(original)
   if actual!=expected:drift.append({'stage':stage,'file':relative,'execution_pin':expected,'current_live_pin':actual,'note':'Current shared source is not substituted for the recorded execution pin; frozen artifact identities remain authoritative.'})
   elif original.suffix=='.py':
    snapshot=OUT/'source/executed-dependencies'/relative;snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes(original.read_bytes());dependency_snapshots.append({'stage':stage,'original_file':relative,'execution_sha256':expected,'snapshot':identity(snapshot)})
 source=OUT/'source';source.mkdir(exist_ok=True)
 for p in [LANE/'build_natural_guard.py',LANE/'verify_natural_guard.py',Path(__file__)]:
  (source/p.name).write_bytes(p.read_bytes())
 review=LANE/'review/v1';movie=review/'after/movie/natural_idle_1p5s_30fps.mp4';board=review/'natural_guard_before_after.png';anchors=review/'before_after_actual_anchor_deltas.json'
 assert movie.is_file() and board.is_file() and anchors.is_file()
 manifests=sorted(review.rglob('*manifest.json'))
 assert manifests,'render identity manifests missing'
 result={
  'status':'source_guard_and_breathing_idle_ready_for_Root_review_no_family_or_native_acceptance',
  'clock':{'Root_start_cst':'2026-11-15T16:40:00+08:00','Root_deadline_cst':'2026-11-15T17:25:00+08:00','sealed_utc':datetime.now(timezone.utc).isoformat(),'sealed_cst':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'RAW_mtimes_cst':{name:datetime.fromtimestamp((OUT/name).stat().st_mtime,ZoneInfo('Asia/Shanghai')).isoformat() for name in ('guard_raw.glb','idle_raw.glb')}},
  'RAW':{'guard':identity(OUT/'guard_raw.glb'),'idle':identity(OUT/'idle_raw.glb')},
  'authoring':identity(OUT/'natural_guard_authoring.json'),
  'canonical_guard_role':'guard_pose is an offline canonical reference pose only, not a new runtime guard clip or mode.',
  'idle_role':'Real breathing source remains named idle and is intended for the existing idle entry after Root accepts and coherently updates the family and its clock.',
  'source_contract':v['contract'],
  'source_interpolation':'All234TRS tracks complete; guard2keys and idle181keys0..1.5s@120Hz, LINEAR. Analytic cosine breath is periodic, exported LINEAR data is not claimed globally C2.',
  'guard_pose_intent':a['guard_authoring'],
  'breath_intent':a['idle'],
  'bounded_verification':{'report':identity(OUT/'verification_natural_guard.json'),'sample_count':49,'actual_steel_fullbody_overlap_sample_count':0,'nonadjacent_forearm_hand_vs_head_chest_overlap_sample_count':0,'all_checks':v['checks'],'guard_and_idle_endpoint_234_TRS_float32_exact':True,'RAW_R15_exact_constant_v5_UNBAKED':True,'preview_once_finger_and_once_root_shift_max_component_errors':v['once_finger_calibration_and_once_root_shift_max_component_error'],'maximum_guard_relative_joint_displacement_metres':v['maximum_guard_relative_joint_displacement_metres'],'maximum_guard_relative_joint_rotation_degrees':v['maximum_guard_relative_joint_rotation_degrees'],'maximum_actual_steel_vertex_motion_metres':v['maximum_actual_steel_vertex_motion_metres'],'maximum_actual_shoe_sole_plane_error_metres':v['maximum_actual_shoe_sole_plane_error_metres'],'maximum_actual_shoe_centre_motion_metres':v['maximum_actual_shoe_centre_motion_metres'],'maximum_bone_length_change_metres':v['maximum_bone_length_change_metres'],'actual_rejections':v['rejection_cases_actually_run']},
  'absolute_legacy_marker':{'report':identity(OUT/'verification_legacy_marker.json'),'source_seconds':1/3,'actual_nearest_key_seconds':marker['actual_float32_raw_key_seconds'],'changed_rotation_track_count':len(marker['raw_changed_channels_from_guard_at_key40']),'joint_displacement_metres':marker['joint_displacement_lengths_from_guard_metres'],'result':'Absolute source1/3 is intentionally not frozen to guard. Only0/1.5 endpoints are exact guard. Reuses the same executed49-pose scan, no extra surface pass.'},
  'before_after_grip_evidence':{'report':identity(anchors),'scope':'Actual current formal base idle0 versus new private base guard0, full existing Grip binding and shift included. Existing before/after node measurements give RHand/BladeBase/BladeTip differences about1.5–1.7micrometres; does not independently assert a full RHand rotation matrix identity.'},
  'private_previews':{'guard':identity(OUT/'guard_preview.glb'),'idle':identity(OUT/'idle_preview.glb'),'not_RAW':True,'base_only':True,'right_finger_offset_applications':1,'target_canonical_root_shift_applications':1,'no_family_or_three_target_generation':True},
  'existing_producer_gate_probe':v['existing_production_locomotion78_gate'],
  'Root_integration_gates_to_replace':['frozen idle91/walk185 source count convention','non-leg STEP and constant idle body tracks','locked_head_ancestor_chain','canonical source markers[0,1/3,1.5] all equal attack0','LocomotionProfile locked-idle contact/blade anchor constructor requirements while preserving intended held-knife constraint','idle first-sample source time selection and EnemyAnimator manual setTime must share the simulation idle clock','unified natural guard in idle/walk/three attacks, profiles, typed data and binding'],
  'Root_acceptance_then_single_path_migration':{'family':'Unify the accepted natural canonical guard in idle/walk and all three attack endpoints, then regenerate typed/proxy/binding together. Do not add an old/new fallback or force this idle to91/STEP to satisfy the retired locked assumption.','source_contract':'Replace the current frozen91-key idle gate, non-leg STEP/constant gate and canonical_source_evidence idle0/1/3/1.5+locked_head_ancestor_chain assumptions coherently. guard_pose remains a source reference.','runtime_actual_chain':a['production_boundary']['actual_runtime_chain'],'runtime_clock':'Current moving=false returns idle.samples.first and EnemyAnimator alive pauses+setTime(state.enemyPoseSourceSeconds). A shared simulation/idle source clock must drive both profile/proxy and SDK; SDK repeat(-1) alone is insufficient.','anchor_contract':'This source holds actual knife/RHand fixed while chest/head breathe. Root must replace incompatible locked-body expectations in the profile/generator with the same source clock, preserving the actual contact/knife constraints.','public_paths_modified_here':False},
  'visual_evidence':{'before_after_board':identity(board),'idle_movie':identity(movie),'movie_contract':'1.500s/30fps45 video frames from46 actual source samples0..1.5; endpoint closure still is separate. No slow-down/time stretch.','render_manifests':[identity(p) for p in manifests],'aesthetic_authority':'Independent same-camera source review only; Root judges naturalness and whether the light breath is perceptible. Numeric nonstatic checks do not replace aesthetic or PICO acceptance.'},
  'frozen_v5_parent':a['parent_v5_frozen'],
  'source_live_path_drift_after_build':drift,'execution_dependency_pins':{'build':a['source_pins'],'verification':v['verification_source_pins']},'matched_executed_dependency_snapshots':dependency_snapshots,
  'executed_source_snapshots':[identity(source/name) for name in ('build_natural_guard.py','verify_natural_guard.py','build_handoff.py')],
  'boundaries':{'geometry_localization_corrections_used':0,'v5_old_family_producer_formal_app_device_Git_written':False,'generated_targets':['private_base_preview']},
  'limits':v['limits']+['The two RAW sources are authoring candidates; current producer rejection is intentional evidence of the required coherent migration, not bypassed acceptance.']}
 (OUT/'natural_guard_handoff.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'RAW':result['RAW'],'authoring':result['authoring'],'handoff':identity(OUT/'natural_guard_handoff.json'),'live_drift_count':len(drift)},indent=2))
if __name__=='__main__':main()
