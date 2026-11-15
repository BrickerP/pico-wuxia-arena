"""Seal final second-solution v5 RAW and bounded validation evidence."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import hashlib,json,struct,math
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1];REPO=LANE.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'file':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size}
def load(name):return json.loads((OUT/name).read_text())
def timestamp(p):return {'utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat(),'cst':datetime.fromtimestamp(p.stat().st_mtime,ZoneInfo('Asia/Shanghai')).isoformat()}
def main():
    a=load('weighted_overhead_authoring.json');v=load('weighted_overhead_verification.json');src=load('weighted_overhead_source_finite_verification.json');motion=load('weighted_overhead_motion_steps.json');metrics=load('weighted_overhead_clearance_metrics.json');repro=load('veteran_v4_defect_reproduction.json');alignment=load('veteran_alignment.json')
    assert a['raw']['sha256']==v['raw']['sha256']==src['RAW']['sha256']==metrics['RAW']['sha256']==motion['RAW']['sha256']==sha(OUT/'weighted_overhead_raw.glb')
    assert v['status']=='v5_raw_and_actual_veteran_bounded_checks_passed' and v['overlap_sample_count']==0 and v['sample_count']==70
    assert src['status']=='original_source_base_context63_finite_checks_passed' and src['sample_count']==63
    assert v['added_swivel_direction_stable_in_each_window']
    assert sha(LANE/'candidate/v4/weighted_overhead_raw.glb')=='050c55a2b64726f38ca7d36eec52f5832c370b92be3f80551f7c8249e5a3694f'
    assert sha(LANE/'candidate/v4/veteran_prepared_png.glb')=='cead1124ab1c3453f6fae2f98e0be275a39792be3de98e6888edaf83a4aabb86'
    source_path_drift=[]
    for path,expected in a['source_pins'].items():
        actual=sha(REPO/path)
        if actual!=expected:source_path_drift.append({'file':path,'recorded_build_time_sha256':expected,'current_live_sha256':actual,'current_live_mtime':timestamp(REPO/path),'interpretation':'Live shared source changed after frozen artifact creation; current source is not claimed to be the executed source. Original authoring pin is preserved; no producer write or scan rerun.'})
    # Derive true LINEAR influence from the actual stored float32 time array.
    raw=(OUT/'weighted_overhead_raw.glb').read_bytes();size=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+size]);binary=raw[28+size:]
    ac=doc['accessors'][doc['animations'][0]['samplers'][0]['input']];bv=doc['bufferViews'][ac['bufferView']];offset=bv.get('byteOffset',0)+ac.get('byteOffset',0);times=[r[0] for r in struct.iter_unpack('<f',binary[offset:offset+ac['count']*4])]
    ids=[r['key_index'] for r in a['v5_delta']['changed_keys']];groups=[]
    for i in ids:
        if not groups or i!=groups[-1][-1]+1:groups.append([i])
        else:groups[-1].append(i)
    assert len(ids)==43
    precision={'nominal_windows':a['v5_delta']['nominal_windows_seconds'],'stored_key_groups':[{'indices':[g[0],g[-1]],'changed_key_times_seconds':[times[g[0]],times[g[-1]]],'actual_LINEAR_influence_interval_seconds':[times[g[0]-1],times[g[-1]+1]],'influence_endpoints':'unchanged v4 predecessor/successor key values'} for g in groups],'scope':'Stored key payload comparisons are distinct from continuously evaluated t. C2 applies only to analytic scalar authoring envelopes, not the sampled glTF LINEAR clip.'}
    delta=load('weighted_overhead_delta.json');delta['delta']['sampling_and_support_precision']=precision;delta['geometric_attempts']=2;delta['rejected_attempt1']='attempt1/failure.json';delta['final_direction_policy']='Fixed signs[-1,+1] chosen at each actual fault peak; no per-frame normal-driven sign selection.';(OUT/'weighted_overhead_delta.json').write_text(json.dumps(delta,indent=2)+'\n')
    (OUT/'weighted_overhead_verification_executed.json').write_bytes((OUT/'weighted_overhead_verification.json').read_bytes())
    source=OUT/'source';source.mkdir(exist_ok=True)
    executed=[LANE/'build_weighted_overhead.py',OUT/'verify_reproduce_veteran.py',OUT/'verify_weighted_overhead.py',OUT/'verify_source_finite.py',OUT/'verify_clearance_metrics.py',OUT/'verify_motion_steps.py',Path(__file__)]
    for p in executed:(source/p.name).write_bytes(p.read_bytes())
    # Renderer owns review and must bind its final two after images to this target.
    comparison=load('review/comparison_manifest.json')
    manifests=[load('review/'+name) for name in ('after_1100_manifest.json','after_1467_manifest.json')]
    for manifest in manifests:assert manifest['inputs']['asset']['sha256']==sha(OUT/'veteran_prepared_png.glb'),'after image is not the final target'
    baseline_diagnosis=[]
    for row in repro['frames']:
        geom=row['geometry_diagnosis'];baseline_diagnosis.append({'source_seconds':row['source_seconds'],'actual_triangle_pairs':geom['intersection_triangle_pair_count'],'unique_near_elbow_forearm_triangles':geom['unique_forearm_triangles'],'unique_Waist_triangles':geom['unique_chest_triangles'],'forearm_region_joint_counts':geom['forearm_dominant_joint_vertices'],'chest_classification_actual_joint_counts':geom['chest_dominant_joint_vertices'],'elbow_to_wrist_projection_fraction_bounds':geom['forearm_vertex_projection_along_elbow_to_wrist_fraction_bounds'],'local_nearest_normal_distance_metres_bounds':geom['forearm_vertex_nearest_chest_signed_distance_metres_bounds'],'paired_face_plane_vertex_distance_metres_bounds':geom['paired_face_plane_signed_vertex_bounds_metres'],'visibility':'Actual before closeups show tucked near-elbow armor/sleeve against the waist/belt inner edge, with no obvious exposed cutout or gross outer-contour rupture at that camera. Counts are not a severity score.','depth_limit':geom['depth_limit']})
    compact_motion=[]
    for context in motion['contexts']:
        compact_motion.append({'context':context['context'],'stored_Q_hemisphere_checks':context['stored_quaternion_half_sphere_checks'],'complete211_key_step_summary':context['summary']})
    private=alignment['private_v5_validation']
    result={
      'status':'v5_final_second_solution_RAW_ready_bounded_checks_passed_pending_Root_review',
      'clock':{'Root_declared_start_cst':'2026-11-15T13:28:00+08:00','Root_deadline_cst':'2026-11-15T14:13:00+08:00','sealed_utc':datetime.now(timezone.utc).isoformat(),'sealed_cst':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'artifact_mtimes':{name:timestamp(OUT/name) for name in ('weighted_overhead_raw.glb','weighted_overhead_authoring.json','veteran_prepared_png.glb','weighted_overhead_verification.json')}},
      'shared_live_source_path_drift_after_build':source_path_drift,
      'raw':identity(OUT/'weighted_overhead_raw.glb'),'authoring':identity(OUT/'weighted_overhead_authoring.json'),'delta':identity(OUT/'weighted_overhead_delta.json'),
      'frozen_v4':{'raw':identity(LANE/'candidate/v4/weighted_overhead_raw.glb'),'target':identity(LANE/'candidate/v4/veteran_prepared_png.glb'),'authoring':identity(LANE/'candidate/v4/weighted_overhead_authoring.json'),'unchanged':True},
      'requested_fault_results':[{'source_seconds':f['source_seconds'],'regions':'near-elbow L_forearm core versus Waist part of the chest semantic group','before_actual_pairs':f['before']['nonadjacent_region_triangle_pairs']['L_forearm__chest'],'reproduced_before_pairs':f['reproduced_before']['nonadjacent_region_triangle_pairs']['L_forearm__chest'],'final_actual_pairs':f['after']['nonadjacent_region_triangle_pairs']['L_forearm__chest']} for f in v['requested_faults_before_after']],
      'before_local_diagnosis_and_visibility':baseline_diagnosis,
      'final_local_clearance_metrics':{'report':identity(OUT/'weighted_overhead_clearance_metrics.json'),'frames':metrics['frames'],'important_limit':'At1.1 the old affected vertices still have local nearest-normal signed minimum about-2.50mm despite zero sampled triangle intersections. Open-core normals do not establish closed-volume inside/outside; no complete volumetric clearance is claimed. At44/30 those same previously affected vertices are all locally outward, minimum about+9.4mm.'},
      'finite_validation':{'actual_veteran':{'report':identity(OUT/'weighted_overhead_verification.json'),'sample_count':70,'steel_fullbody_overlap_sample_count':0,'nonadjacent_arm_hand_vs_head_chest_overlap_sample_count':0,'right_hand_head_at_0p9_still_clear':True},'source_base_context':{'report':identity(OUT/'weighted_overhead_source_finite_verification.json'),'sample_count':63,'unmodified_executed_report':identity(OUT/'weighted_overhead_source_finite_verification_executed.json'),'steel_fullbody_overlap_sample_count':0,'nonadjacent_arm_hand_vs_head_chest_overlap_sample_count':0,'method':'In-memory final RAW six-arm rotations applied to frozen v3 base mesh/grip context, including unchanged v4 threeR correction; no generated base target or new retarget.'}},
      'authoring_scope':{'only_geometrically_changed_RAW_streams':a['v5_delta']['only_changed_tracks'],'stored_changed_keys_per_stream':43,'sampling_and_support_precision':precision,'fixed_swivel_direction_by_window':[-1,1],'peak_swivel_degrees':8,'final_added_swivel_maximum_step_degrees_at120Hz_by_window':v['maximum_added_swivel_step_degrees_at120Hz_by_window'],'R_Upperarm_R_Forearm_R_Hand_rotation_payloads':'all original v4 bytes retained across all211 keys','guard_R15_unbaked_static_rest_actor_grip_weights':'retained original v4 bytes/geometry','left_RAW_wrist_target_and_world_palm_orientation':'held at original v4; sampled RAW wrist reconstruction error less than0.4micrometre','actual_veteran_left_hand_origin':'small target-dependent shifts1.813mm and2.579mm at the two fault times; not claimed bit-identical position','actual_veteran_non_L3_max_float32_component_difference_from_actual_v4':v['actual_target_invariants']['non_left_arm_max_float32_component_error_from_actual_v4']},
      'full211_key_motion_and_Q_signs':{'report':identity(OUT/'weighted_overhead_motion_steps.json'),'summaries':compact_motion,'existing_motion_limit':'Parent v4 already has about25.615degree forearm-world/wrist-local neighbor rotation at1.45→1.45833; final about25.927degree. Largest added geometric neighbor rotation increase is about1.393degree. This local collision repair does not certify overall source motion naturalness or C2.','inherited_RAW_sign_exception':'Both v4 and final v5 RAW L_Forearm retain negative stored adjacent dot at[0,1] and[209,210], inherited from exact guard packing. No new negative pair is introduced; actual veteran target threeL streams are all same-hemisphere. Root explicitly keeps the original guard/out-of-window payload; SDK/producer packing is a future Root item, not expanded here.'},
      'attempts':{'geometric_localization_solutions':2,'attempt1':{'status':'rejected_due_added_sign_selection_jumps_despite_surface_clearance','record':identity(OUT/'attempt1/failure.json'),'source_and_artifacts':'attempt1/ retained; not final'},'attempt2':{'status':'final_fixed_per_window_direction','no_third_solution':True}},
      'RAW_contract':{'stage':'authored_raw','right_calibration_baked':False,'joints':78,'channels':234,'keys':211,'sample_rate_hz':120,'duration_seconds':1.75,'guard_endpoints':'exact v4 float32 values','R15':'exact v4 unbaked original values'},
      'actual_target_generation':{'target':'veteran_only','before_pipeline_reproduction_max_component_error':v['actual_target_invariants']['before_reproduction_max_float32_component_error'],'native_target_grip':private['target_native_right_grip'],'RAW_retarget_count':1,'finger_calibration_applications':1,'canonical_target_idle_root_shift_applications':1,'canonical_source_timelines':'five original native canonical helper clips through prepare_character canonical_grounding_clips','already_retargeted_veteran_used_as_RAW':False,'static_checks':v['actual_target_invariants']['static_checks'],'alignment':identity(OUT/'veteran_alignment.json'),'preview':identity(OUT/'veteran_prepared_png.glb'),'private_preview_is_not_RAW':True},
      'phase_and_damage_authority':{'Root_source_phase_seconds':[0,.65,5/6,31/30,1.75],'source1p0':'metadata cue, never automatic damage time','actual_damage_window':'Root owns actual final sharpened-mesh/target contact evaluation and runtime timing'},
      'images':{'comparison_manifest':identity(OUT/'review/comparison_manifest.json'),'before_after_board':identity(OUT/'review/veteran_two_fault_times_before_after.png'),'review_root':'candidate/v5/review/'},
      'executed_source_snapshots':[identity(source/p.name) for p in executed],
      'boundaries':{'integration_formal_producer_library_app_device_Git_written':False,'shared_tree_others_preserved':True,'generated_targets':['veteran']},
      'limits':['70 actual-veteran and63 source/base discrete triangle checks do not prove continuous-time or all-cloth-volume clearance.','Semantic cores exclude blend seams, adjacent shoulder junctions and within-region clothing layers.','Two static local before/after pictures do not replace full playback or native device acceptance.','No base/indigo production retarget, final library/binding/profile publication, SDK acceptance or overall naturalness approval is claimed.']}
    (OUT/'weighted_overhead_handoff.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'raw':result['raw'],'authoring':result['authoring'],'handoff':identity(OUT/'weighted_overhead_handoff.json')},indent=2))
if __name__=='__main__':main()
