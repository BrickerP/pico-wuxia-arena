"""Seal the combined actual export for Root publication and native verification."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[6]


def identity(path):
    data=path.read_bytes()
    return {'file':str(path.relative_to(REPO)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def read(path):return json.loads(path.read_bytes())


def main():
    inputs=read(HERE/'input_receipt.json')
    request=read(HERE/'candidate-library/production_review_request.json')
    reference=read(HERE/'reference_request_c300.json')
    review=read(HERE/'target-review/review_report.json')
    render=read(HERE/'local-review/render_manifest.json')
    typed=read(HERE/'typed-validation/candidate_fixture.json')
    jvm=read(HERE/'typed-validation/result-all-core.json')
    snapshots=HERE/'typed-validation/compiled-inputs/input-manifest.json'
    assert snapshots.is_file()
    binding=request['binding_sha256']
    assert binding==inputs['expected_binding_sha256']==review['binding_sha256']==render['binding_sha256']==typed['binding_sha256']
    assert binding=='51807084b2d6abd2cc322e2225d6afa42f25db0eae48c57c4d85dbf6193abd33'
    assert request['status']=='pending_root_review'
    assert review['status']=='finite_combined_checks_passed_pending_Root_visual_native_review'
    projection=dict(request['binding'])
    descriptor=projection.pop('prepared_wrist_constraint')
    assert projection==reference['binding'],'Only constraint descriptor may change relative to c300 inputs'
    assert typed['jvm_test_count']==179 and jvm['exit_code']==0
    assert typed['compiled_sources_unchanged'] and not typed['existing_test_filters_applied']
    for name,pin in review['source_pins'].items():
        assert identity(REPO/name)['sha256']==pin,'Actual review source/input drift: '+name
    for name,pin in render['source_pins'].items():
        assert identity(REPO/name)['sha256']==pin,'Local render source/input drift: '+name
    for item in inputs['pins']:
        assert identity(REPO/item['file'])==item,'Frozen producer/c300 input drift: '+item['file']
    frames=[f for t in review['targets'] for f in t.get('renders',{}).get('frames',[])]+render['frames']
    assert len(frames)==8
    for frame in frames:
        assert identity(REPO/frame['path'])['sha256']==frame['sha256']
    artifacts=[identity(path) for path in sorted(HERE.rglob('*')) if path.is_file() and path.name!='handoff.json'
        and '__pycache__' not in path.parts and 'classes' not in path.parts and path.suffix!='.jar']
    motion={t['target']:{clip:{key:value for key,value in proof.items() if key!='frames'} for clip,proof in t['motion'].items()} for t in review['targets']}
    foot_residuals={t['target']:{clip:{side:{'minimum_signed_mm':1000*min(f['foot_plane_residual_metres'][side] for f in proof['frames']),
        'maximum_signed_mm':1000*max(f['foot_plane_residual_metres'][side] for f in proof['frames'])}
        for side in ('L','R')} for clip,proof in t['motion'].items()} for t in review['targets']}
    handoff={'schema':'pico-wuxia-engineering-handoff-v1',
        'status':'combined_LEFT_RIGHT_actual_checks_passed_pending_Root_approval_and_native',
        'binding_sha256':binding,'reference_binding_sha256':reference['binding_sha256'],
        'scope':'Only private combined-left-right candidate, tests, snapshots and render outputs; no formal/library/app/public producer/Git state/device writes',
        'candidate_manifest':identity(HERE/'motion_library_candidate.json'),
        'production_review_request':identity(HERE/'candidate-library/production_review_request.json'),
        'typed_data':identity(HERE/'typed-validation/AttackBankProfileData.kt'),
        'public_solver_descriptor':descriptor,
        'actual_character_outputs':request['characters'],
        'executed_before_export_source_pins':inputs['pins'],
        'producer_execution':'Current public prepare_character_library.py through shared run_blender.py -b --factory-startup --threads 2; snapshot manifest, private --candidate-dir; original fixed encoder/settings',
        'passed':{
            'binding_change':'Only prepared_wrist_constraint descriptor added to c300 binding; original RAW identities, durations, phase contracts and target body/weapon configuration retained.',
            'base_indigo':'All three GLBs per actor are byte-identical to c300; all ten animation signatures unchanged.',
            'veteran':'Only LEFT R_Upperarm/R_Forearm/R_Hand rotations change; three tracks130 keys, other231 tracks exact106; other9 clips including RIGHT exact.',
            'static':'All target geometry/rest/skin/inverse binds/material/image semantics unchanged; prepared PNG to KTX non-image semantics and payloads exact.',
            'actual_motion':motion,
            'finite_clearance_poses':sum(len(v) for t in review['targets'] for v in t['clips'].values()),
            'finite_pose_counts':{t['target']:{clip:len(v) for clip,v in t['clips'].items()} for t in review['targets']},
            'intersection_pose_counts':review['intersection_pose_counts'],
            'full_steel_gate':'All5533 actual same-target LBS vertices; key budget5µm and subkey1mm unchanged; complete wrist orientation checked at actual Steel radius. Body/combined curves exact and canonical receipt verifies shared full Steel reference.',
            'new_public_contract_tests':review['public_contract_tests'],
            'typed':'Existing generator and --check exact; six Python fixture/count boundary tests pass; complete179-test old-runtime JVM suite passes with only seven identity fixture literals plus explicit veteran/LEFT130 sampling expectation updated.',
            'compiled_inputs':identity(snapshots),
            'compiled_inputs_scope':'37 exact per-file inputs retained;35 public sources equal stable HEAD5c9843ed0440528fe6a8d2b514dc8d3371d3481e,2 private candidate typed/test fixtures. These179 tests do not validate ongoing contact-unload changes.',
            'images':'4 normal and4 local original-material actual veteran LEFT guard/1.10/1.20/return images; RIGHT images preserved in prior c300 handoff.'},
        'inherited_foot_plane_residuals_mm':foot_residuals,
        'limits':review['limits']+[
            'No idle2mm micromotion allowance was used for either dynamic blade check.',
            'No new contact-unload feature tests or app build; Root owns complete combined-app suite.',
            'No PICO Emulator SDK skinned playback, APK or Space Pro evidence was produced by this integration lane.'],
        'remaining_for_Root':['Review finite original-material LEFT views and motion aesthetics.',
            'Approve the exact new production request before formal canonical re-export and typed/assets publication.',
            'Run full current app tests/build and verify SDK playback/native input on PICO Emulator and Space Pro.'],
        'artifact_identities':artifacts}
    (HERE/'handoff.json').write_text(json.dumps(handoff,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'handoff':identity(HERE/'handoff.json'),'binding_sha256':binding,'artifacts':len(artifacts),
        'finite_poses':handoff['passed']['finite_clearance_poses'],'status':handoff['status']},indent=2))


if __name__=='__main__':main()
