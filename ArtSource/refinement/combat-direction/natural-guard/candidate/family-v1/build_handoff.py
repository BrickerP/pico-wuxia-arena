"""Seal five family RAW identities for Root's private production input."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import json,hashlib
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1];REPO=LANE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'file':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size}
def load(p):return json.loads(p.read_text())
def main():
 a=load(OUT/'family_authoring.json');e=load(OUT/'verification_endpoints.json');s=load(OUT/'verification_surfaces.json')
 assert a['preview']['sha256']==s['preview']['sha256']==sha(OUT/'base_family_preview.glb')
 assert e['status']=='all_five_raw_endpoints_passed' and s['status']=='finite_base_scan_passed'
 assert e['all_234_TRS_marker_values_float32_exact'] and e['constant_R15_master_UNBAKED_exact']
 assert e['three_attack_interiors_0p20_to1p50_exact_source']
 assert e['authoring']==s['authoring']==identity(OUT/'family_authoring.json')
 assert len(a['outputs'])==5
 for name,row in a['outputs'].items():assert row['raw']==identity(REPO/row['raw']['file']) and s['clips'][name]['overlap_sample_count']==0
 # This immutable earlier result reads actual stored key40. The family idle
 # is a byte-for-byte copy, so normalized-Q component noise must not inflate
 # the number of actually changed stored rotation channels.
 legacy_path=LANE/'candidate/v1/verification_legacy_marker.json';legacy=load(legacy_path)
 assert sha(OUT/'idle_raw.glb')=='0cac7c29e9fd9445e3b1e1825c60e885323b870181df33c5242fc0b6b40d95a6'
 marker={'actual_source_seconds':1/3,'actual_nearest_raw_key':40,'actual_stored_changed_rotation_channels':legacy['raw_changed_channels_from_guard_at_key40'],'actual_changed_count':len(legacy['raw_changed_channels_from_guard_at_key40']),'proof':identity(legacy_path),'proof_applicability':'Family idle is byte-identical to the immutable natural-guard v1 idle. Actual stored float32key40 comparison has9 rotation streams; do not count normalization-only changes when sampling other constant quaternions.','new_surface_scan_performed':False}
 assert marker['actual_changed_count']==9
 (OUT/'verification_idle_marker_addendum.json').write_text(json.dumps(marker,indent=2)+'\n')
 source=OUT/'source';source.mkdir(exist_ok=True)
 py_candidates=[p for p in OUT.rglob('*.py') if p.is_file()]
 snapshots=[];drift=[]
 for stage,pins in [('build',a['source_pins']),('endpoints',e['verification_source_pins']),('surfaces',s['verification_source_pins'])]:
  for relative,expected in pins.items():
   original=REPO/relative;matched=original if original.is_file() and sha(original)==expected else next((p for p in py_candidates if sha(p)==expected),None)
   if matched is None:
    drift.append({'stage':stage,'file':relative,'execution_sha256':expected,'current_live_sha256':sha(original) if original.is_file() else None,'note':'Live source is not substituted for the execution pin.'});continue
   if matched.suffix=='.py':
    dest=source/'executed-dependencies'/expected[:12]/original.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(matched.read_bytes());snapshots.append({'stage':stage,'original_file':relative,'execution_sha256':expected,'snapshot':identity(dest)})
 for p in [LANE/'build_natural_guard_family.py',LANE/'verify_family.py',Path(__file__)]:
  (source/p.name).write_bytes(p.read_bytes())
 outputs={}
 for name,row in a['outputs'].items():
  outputs[name]={**row,'source_sample_rate_hz':120 if name in ('idle','attack_overhead') else 60 if name.startswith('attack_') else 'original185-key grid preserved, includes authored special-time samples'}
 # Explicit producer input descriptors, no new runtime alias or legacy head
 # constraint. Root consumes this one accepted family as the final path.
 production_inputs={name:{'name':name,'source':'../'+str((REPO/row['raw']['file']).relative_to(REPO/'ArtSource')),'source_resolution_base':'ArtSource/tripo-warrior','repository_relative_file':row['raw']['file'],'source_sha256':row['raw']['sha256'],'stage':'authored_raw','right_calibration_baked':False,**({k:row[k] for k in ('source_loop_seconds','source_loop_duration_seconds')} if name in ('idle','walk') else {})} for name,row in outputs.items()}
 join_summary={}
 for name,row in e['clips'].items():
  measures=row['join_neighbor_key_measurements']
  join_summary[name]={'maximum_old_world_neighbor_step_degrees':max((v['old']['maximum_world_shortest_angle_degrees'] for v in measures),default=0),'maximum_new_world_neighbor_step_degrees':max((v['new']['maximum_world_shortest_angle_degrees'] for v in measures),default=0),'stored_negative_Q_event_counts':{k:len(v) for k,v in row['stored_Q_negative_dot_events_all_adjacent_keys'].items()},'inherited_source_norm_deviations':row['inherited_quaternion_norm_deviations_at_or_above_2e_minus5']}
 result={
  'status':'five_RAW_family_and_authoring_frozen_ready_for_Root_private_bank_input',
  'sealed_utc':datetime.now(timezone.utc).isoformat(),'sealed_cst':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
  'family_authoring':identity(OUT/'family_authoring.json'),'raw_identity_creation_record':identity(OUT/'family_raw_identity.json'),
  'master_natural_guard':a['guard'],'outputs':outputs,'production_input_descriptors':production_inputs,
  'frozen_inputs':a['inputs'],'frozen_natural_idle_copied_byte_for_byte':True,
  'canonical_endpoint_proof':{'report':identity(OUT/'verification_endpoints.json'),'all_five_234_TRS_float32_markers_exact':True,'idle_markers_seconds':[0,1.5],'walk_markers_seconds':[0,1/3,1.5],'attack_markers_seconds':[0,1.75],'idle_absolute_one_third':'intentionally breathing, not a guard marker','idle_marker_addendum':identity(OUT/'verification_idle_marker_addendum.json'),'R15_master_native2p117_UNBAKED_exact':True,'old_rest_mesh_skin_static_payload_retained':True,'walk_original_six_leg_TRS_and185_time_grid_and_interpolation_retained':True,'attack_interior_key_values_0p20_through1p50_retained':True,'actual_bad_input_rejections':e['rejection_cases_actually_run']},
  'source_loops':{'idle':{'source_loop_seconds':[0,1.5],'source_loop_duration_seconds':1.5,'keys':181,'interpolation':'LINEAR'},'walk':{'source_loop_seconds':[1/3,1.5],'source_loop_duration_seconds':7/6,'keys':185,'original_gait_curves_and_clock':'preserved signed-gait family'}},
  'attack_migration':{'method':'Bounded local minimum-angle guard difference applied on top of original motion, not full-pose blending that would flatten the original windup.','nominal_correction_windows_seconds':[[0,.20],[1.50,1.75]],'stored_key_preservation':'All original per-channel key values at source.20..1.50 retained; exact new guard endpoint payloads override0/1.75.','continuity_limit':'C2 describes scalar correction envelopes; complete original and modified LINEAR animations are not globally C2. Actual interpolation influence can extend into the neighboring segments at the first/last modified key.'},
  'join_measurements':{'summary':join_summary,'full_evidence':identity(OUT/'verification_endpoints.json'),'interpretation':'Original and new source-key local/world shortest-angle steps are listed independently from stored quaternion signs. Old large motion and source sign/norm exceptions are not silently repackaged or claimed newly fixed.'},
  'finite_private_base':{'report':identity(OUT/'verification_surfaces.json'),'preview':a['preview'],'alignment':a['alignment'],'sample_counts':{name:r['sample_count'] for name,r in s['clips'].items()},'total_sample_count':sum(r['sample_count'] for r in s['clips'].values()),'all_actual_Steel_full_body_and_declared8_self_regions_overlap_counts':0,'once_finger_and_once_root_shift_max_component_error_by_clip':{name:r['once_finger_calibration_and_root_shift_max_component_error'] for name,r in s['clips'].items()},'same_base_static_rest_mesh_skin_materials_verified_against':s['same_base_rest_mesh_skin_materials_verified_against'],'preview_is_not_RAW':True},
  'Root_clock_contract':{'idle_driver':'existing enemyMotionNanos, shared source time for idle profile/proxy/SDK','idle_loop_seconds':[0,1.5],'idle_loop_duration_seconds':1.5,'preparation_and_countdown':'same enemyMotionNanos clock','pause_hit_stop_sustained_steel_contact':'freeze that shared clock together','walk_driver':'existing signed gait distance','walk_loop_seconds':[1/3,1.5],'walk_loop_duration_seconds':7/6,'SDK':'manual shared-source time consumption, no independently running repeat'},
  'Root_production_contract_boundary':{'guard_pose':'canonical reference only; never register a new runtime guard mode/clip','idle_constraints':'No locked-head ancestor constraint is emitted or migrated for idle. Keep181LINEAR and genuine closed breathing cycle; no91/STEP downgrade.','single_path_migration':'Root consumes these five sources through the accepted updated locomotion/attack family contracts and regenerates profiles/typed/binding together, without old/new fallback.','three_target_and_runtime_acceptance':'Root-owned private production bank, real target contact, SDK and native validation; this lane has not performed them.'},
  'execution_dependency_pins':{'build':a['source_pins'],'endpoints':e['verification_source_pins'],'surfaces':s['verification_source_pins']},'matched_executed_dependency_snapshots':snapshots,'live_source_drift_not_substituted':drift,
  'local_source_snapshots':[identity(source/name) for name in ('build_natural_guard_family.py','verify_family.py','build_handoff.py')],
  'boundaries':{'old_natural_v1_and_overhead_v5_and_old_family_sources_overwritten':False,'producer_formal_app_device_Git_written':False,'generated_target_preview':'private base only','visual_deliverable_not_a_dependency_of_this_handoff':True},
  'limits':s['limits']+['Exact source endpoints and finite surfaces do not prove runtime blends, transition aesthetics or continuous collision freedom. Existing source Q-sign and norm deviations are listed, not hidden by global normalization.']}
 (OUT/'family_handoff.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'authoring':result['family_authoring'],'handoff':identity(OUT/'family_handoff.json'),'outputs':{k:v['raw']['sha256'] for k,v in outputs.items()},'live_drift_count':len(drift)},indent=2))
if __name__=='__main__':main()
