"""Seal v4 bounded repair evidence; does not generate animation or render."""
from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent
LANE=OUT.parents[1]
REPO=LANE.parents[3]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def identity(p):return {'file':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size}

def main():
    # Documentation-only annotation is a seal step, separate from executing
    # any geometric scan. Preserve the exact numeric scan JSON as evidence.
    delta_record=json.loads((OUT/'weighted_overhead_delta.json').read_text())
    precision=delta_record['delta']['sampling_and_support_precision']
    primary_path=OUT/'weighted_overhead_verification.json'
    primary=json.loads(primary_path.read_text())
    if 'stored_key_payload_and_LINEAR_influence_interpretation' not in primary['source_invariants']:
        executed_path=OUT/'weighted_overhead_verification_executed.json'
        if executed_path.exists():assert json.loads(executed_path.read_text())==primary,'numeric report changed; cannot replace sealed execution'
        else:executed_path.write_bytes(primary_path.read_bytes())
        primary['source_invariants']['stored_key_payload_and_LINEAR_influence_interpretation']=precision
        primary['documentation_only_addendum']={'executed_numerical_report_file':str(executed_path),'executed_numerical_report_sha256':sha(executed_path),'RAW_target_and_numerical_results_unchanged':True,'scan_rerun_for_wording':False}
        primary_path.write_text(json.dumps(primary,indent=2)+'\n')
    assert primary['source_invariants']['stored_key_payload_and_LINEAR_influence_interpretation']==precision
    a=json.loads((OUT/'weighted_overhead_authoring.json').read_text())
    v=json.loads((OUT/'weighted_overhead_verification.json').read_text())
    inherited=json.loads((OUT/'weighted_overhead_inherited_overlaps.json').read_text())
    source_finite=json.loads((OUT/'weighted_overhead_source_finite_verification.json').read_text())
    assert source_finite['RAW']==identity(OUT/'weighted_overhead_raw.glb') and source_finite['status']=='original_source_base_context63_finite_checks_passed'
    alignment=json.loads((OUT/'veteran_alignment.json').read_text())
    for path,expected in a['source_pins'].items():assert sha(REPO/path)==expected,path
    delta=json.loads((OUT/'weighted_overhead_delta.json').read_text())
    assert delta['delta']['sampling_and_support_precision']['actual_gltf_LINEAR_influence_interval_seconds']==[0.8166666626930237,1.0]
    assert v['raw']==identity(OUT/'weighted_overhead_raw.glb')
    assert v['authoring']==identity(OUT/'weighted_overhead_authoring.json')
    after_manifest=json.loads((OUT/'review/after_manifest.json').read_text())
    assert after_manifest['inputs']['asset']['sha256']==sha(OUT/'veteran_prepared_png.glb'),'after render does not use final target'
    assert inherited['verification']==identity(OUT/'weighted_overhead_verification.json')
    assert inherited['new_overlap_sample_count']==0 and inherited['unchanged_inherited_overlap_sample_count']==2
    assert sha(LANE/'candidate/v3/weighted_overhead_raw.glb')=='410d5b445bfd59f615a639a1eb2fb8d5bc8f4cf31e5aa541f9b4cfd84140b1c2'
    assert sha(LANE/'candidate/v3/weighted_overhead_authoring.json')=='315cd0f0e9a1f0c570d10188a3a0f2bd3b977eda800a616806a2c8d8b8419ce9'
    changes=a['v4_delta']['changed_keys'];assert len(changes)==21
    near=[r for r in v['frames'] if .82<=r['source_seconds']<=1.]
    assert len(near)==10 and all(not r['steel_fullbody_intersections'] and not any(r['nonadjacent_region_triangle_pairs'].values()) for r in near)
    src=OUT/'source';src.mkdir(exist_ok=True)
    executed=[LANE/'build_weighted_overhead.py',OUT/'verify_reproduce_veteran.py',OUT/'verify_weighted_overhead.py',OUT/'verify_inherited_overlaps.py',OUT/'verify_source_finite.py',Path(__file__)]
    for p in executed:(src/p.name).write_bytes(p.read_bytes())
    faults=[]
    for row in inherited['frames']:
        count=row['same_actual_v3_target']['nonadjacent_region_triangle_pairs']['L_forearm__chest']
        pairs=row['all_actual_v3_left_forearm_chest_triangle_pairs'];assert len(pairs)==count
        faults.append({'source_seconds':row['source_seconds'],'regions':['L_forearm','chest'],'actual_v3_count':count,'v4_count':row['v4_target']['nonadjacent_region_triangle_pairs']['L_forearm__chest'],'before_input':identity(LANE/'integration/candidate-library/veteran_prepared_png.glb'),'all_actual_v3_region_triangle_pairs_and_coordinates_metres':pairs,'v4_same_counts':row['identical_triangle_pair_counts_outside_delta']})
    result={
      'status':{
        'requested_R_hand_head_at_0p9':'passed_actual_veteran_triangle_pairs4_to0',
        'requested_window_near_0p9':'passed_all_10_discrete_steel_and_nonadjacent_region_samples',
        'whole_target_all_regions':'failed_due_inherited_left_forearm_chest_at_1p1_and_1p4667'},
      'raw':identity(OUT/'weighted_overhead_raw.glb'),
      'authoring':identity(OUT/'weighted_overhead_authoring.json'),
      'delta':identity(OUT/'weighted_overhead_delta.json'),
      'v3_frozen':{'raw':identity(LANE/'candidate/v3/weighted_overhead_raw.glb'),'authoring':identity(LANE/'candidate/v3/weighted_overhead_authoring.json'),'both_unchanged':True},
      'requested_fault':{'target':'veteran','source_seconds':.9,'actual_before_triangle_pairs':4,'actual_after_triangle_pairs':0,'before_region_triangle_pairs':'R_hand875/906 versus head624/625','reproduced_before_source_edit':identity(OUT/'veteran_v3_defect_reproduction.json'),'actual_before':identity(LANE/'integration/candidate-library/veteran_prepared_png.glb'),'actual_after':identity(OUT/'veteran_prepared_png.glb')},
      'requested_window_near_0p9':{'source_window_seconds':[.82,1.0],'tested_source_times_seconds':[r['source_seconds'] for r in near],'sample_count':len(near),'steel_fullbody_overlap_sample_count':0,'nonadjacent_arm_hand_head_chest_overlap_sample_count':0,'scope':'actual veteran at declared discrete poses, not continuous-time proof'},
      'original_source_base_finite_validation':{'status':source_finite['status'],'report':identity(OUT/'weighted_overhead_source_finite_verification.json'),'method':'in-memory final RAW on frozen v3 source/base actual mesh/grip context; no retarget or emitted base target','sample_count':63,'steel_fullbody_overlap_sample_count':source_finite['actual_steel_fullbody_overlap_sample_count'],'nonadjacent_arm_hand_head_chest_overlap_sample_count':source_finite['nonadjacent_arm_hand_head_chest_overlap_sample_count'],'distinct_from_actual_veteran_target_validation':True},
      'whole_target_validation':{'primary_status':v['status'],'primary_report':identity(OUT/'weighted_overhead_verification.json'),'unmodified_executed_64_sample_report':identity(OUT/'weighted_overhead_verification_executed.json'),'inherited_confirmation':identity(OUT/'weighted_overhead_inherited_overlaps.json'),'sample_count':v['sample_count'],'steel_fullbody_overlap_sample_count':0,'nonadjacent_overlap_sample_count':2,'new_overlap_sample_count_vs_actual_v3':0,'unchanged_inherited_faults':faults},
      'bounded_authoring_delta':{'geometric_localization_corrections':1,'second_geometric_correction_used':False,'numerical_support_boundary':'t<=.82 and t>=1.0 explicitly return exact0; avoids quintic float tail invoking IK and changing the1.0 original key by roundoff. This clamps the intended window, without changing the16mm pose solution.','only_changed_tracks':a['v4_delta']['only_changed_tracks'],'changed_keys_per_track':21,'first_last_changed_key_source_seconds':[changes[0]['source_seconds'],changes[-1]['source_seconds']],'peak_wrist_shift_metres':a['v4_delta']['peak_wrist_shift_prepared_metres'],'peak_elbow_pole_shift_metres':a['v4_delta']['peak_elbow_pole_shift_prepared_metres'],'all_other_RAW_TRS_payload_bytes_identical_to_v3':True,'all_RAW_stored_key_payloads_outside_open_0p82_1p0_bit_identical_to_v3':True,'sampling_and_support_precision':v['source_invariants']['stored_key_payload_and_LINEAR_influence_interpretation'],'body_load_drive_unload_intent':'frozen v3 unchanged','left_hand_head_clavicles_hip_chest_feet_grip_skin_weights_actor_transform':'unchanged','actual_veteran_0p9_joint_delta_metres':v['actual_veteran_0p9_joint_delta_metres'],'actual_veteran_0p9_hand_world_orientation_change_degrees':v['actual_veteran_0p9_hand_world_orientation_change_degrees']},
      'RAW_contract':{'stage':'authored_raw','right_calibration_baked':False,'joints':78,'channels':234,'keys':211,'sample_rate_hz':120,'duration_seconds':1.75,'guard_endpoints':'exact v3 original float32 values','R15':'exact v3 unbaked original payload bytes','rest_mesh_skin_weights':'unchanged'},
      'private_target_generation':{'target':'veteran_only','native_retarget_count':1,'native_target_grip':alignment['private_v4_validation']['target_native_right_grip'],'target_right_finger_offset_applications':1,'target_canonical_idle_grounding_applications':1,'grounding_method':'prepare_character canonical_grounding_clips over five actual canonical source timelines; target idle measured once','actual_Root_v3_pipeline_reproduction_max_float32_component_error':v['actual_target_invariants']['before_reproduction_max_float32_component_error'],'non_right_arm_max_float32_component_error_from_actual_Root_v3':v['actual_target_invariants']['non_right_arm_max_float32_component_error_from_actual_v3'],'static_checks':v['actual_target_invariants']['static_checks'],'target_already_retargeted_animation_used_as_RAW':False,'alignment':identity(OUT/'veteran_alignment.json'),'preview_is_not_RAW':True},
      'phase_contract':{'Root_owned_source_phase_seconds':[0,.65,5/6,31/30,1.75],'old_0p9_1p1_contract_reused':False,'source1p0':'metadata cue only, not a damage timestamp','damage_window':'Root determines from final actual assembled sharpened-mesh/target contact'},
      'requested_before_after_image':identity(OUT/'review/veteran_source_0900_before_after.png'),'image_manifest':identity(OUT/'review/comparison_manifest.json'),
      'source_snapshots':[identity(src/p.name) for p in executed],
      'write_boundary':{'integration_written':False,'formal_producer_library_app_written':False,'device_Git_operations':False,'generated_targets':['veteran'],'unchanged_canonical_helpers':['idle','walk','attack_left','attack_right']},
      'limits':['Whole veteran target remains not clear due to the two unchanged inherited left forearm/chest defects above.','64 discrete actual target poses are not continuous-time or all-cloth-volume clearance proof.','No base/indigo regeneration, native/PICO acceptance, final production binding/profile, actual damage-window, or publication approval is claimed.']}
    (OUT/'weighted_overhead_handoff.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'raw':result['raw'],'authoring':result['authoring'],'handoff':identity(OUT/'weighted_overhead_handoff.json')},indent=2))

if __name__=='__main__':main()
