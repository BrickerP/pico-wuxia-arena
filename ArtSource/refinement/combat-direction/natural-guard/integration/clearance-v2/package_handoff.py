"""Seal identities and evidence for Root; never approves or publishes the bank."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]


def identity(path):
    data = path.read_bytes()
    return {'file':str(path.relative_to(REPO)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}


def main():
    request = json.loads((HERE / 'candidate-library/production_review_request.json').read_bytes())
    review = json.loads((HERE / 'target-review/review_report.json').read_bytes())
    local = json.loads((HERE / 'local-review/render_manifest.json').read_bytes())
    source = json.loads((HERE / 'source_verification.json').read_bytes())
    jvm = json.loads((HERE / 'typed-validation/result-all-core.json').read_bytes())
    fixture = json.loads((HERE / 'typed-validation/candidate_fixture.json').read_bytes())
    assert request['status']=='pending_root_review'
    assert review['binding_sha256']==local['binding_sha256']==fixture['binding_sha256']==request['binding_sha256']
    assert review['RIGHT_finite_gate_passed'] and source['passed'] and jvm['exit_code']==fixture['exit_code']==0
    for name,pin in review['source_pins'].items():
        assert identity(REPO / name)['sha256']==pin,'review pin drift: '+name
    for name,pin in local['source_pins'].items():
        assert identity(REPO / name)['sha256']==pin,'local render pin drift: '+name
    for frame in local['frames']:
        assert identity(REPO / frame['path'])['sha256']==frame['sha256']
        assert identity(HERE / 'candidate-library' / (frame['target']+'_prepared_png.glb'))['sha256']==frame['actual_model_sha256']
    assert len(local['frames'])==9 and sum(len(t['renders']['frames']) for t in review['targets'])==9
    artifacts = [identity(p) for p in sorted(HERE.rglob('*')) if p.is_file()
        and p.name!='handoff.json' and '__pycache__' not in p.parts and 'classes' not in p.parts and p.suffix!='.jar']
    producer_sources = [REPO / 'ArtSource/tripo-warrior' / name for name in [
        'prepare_character_library.py','prepare_rigged_warrior.py','production_contract.py','attack_profiles.py','attack_grounding.py']]
    inputs = json.loads((HERE / 'input_receipt.json').read_bytes())
    assert identity(REPO / inputs['formal_manifest_before']['file'])==inputs['formal_manifest_before']
    handoff = {'schema':'pico-wuxia-engineering-handoff-v1',
        'status':'RIGHT_stage_ready_for_Root_review_LEFT_unresolved_not_approved',
        'scope':'Private current canonical producer full-bank export; only RIGHT RAW source replaced; no formal/runtime/device/Git writes',
        'binding_sha256':request['binding_sha256'], 'candidate_bank':str((HERE / 'candidate-library').relative_to(REPO)),
        'candidate_manifest':identity(HERE / 'motion_library_candidate.json'),
        'typed_data':identity(HERE / 'AttackBankProfileData.kt'),
        'source_handoff':inputs['handoff'],'raw':inputs['raw'], 'left_integrated':False,
        'formal_manifest_unchanged':inputs['formal_manifest_before'],
        'canonical_producer_sources_observed_after_export':[identity(p) for p in producer_sources],
        'producer_source_identity_limit':'Source hashes observed after execution; executed dependency byte snapshots were not captured. Actual output identities are pinned by the canonical request and target review.',
        'passed':{
            'canonical_export':'Current prepare_character_library.py via shared run_blender.py --candidate-dir; 3 actors, 78 joints, 10 clips each; original full-resolution UASTC3 encoder',
            'source':source,
            'target_static_and_clips':'All source geometry/rest/skin/material/image semantics exact to same-target formal; only attack_right animation changes; nine other clip signatures exact',
            'RIGHT_motion':[{k:v for k,v in t['motion_preservation'].items() if k!='right_foot_measurements'} | {'target':t['target']} for t in review['targets']],
            'RIGHT_net_clearance':'98 finite actual poses per target (294 total); full-body Steel and eight nonadjacent region-pair counts all zero',
            'family_finite_poses':420,
            'typed_generator':'Existing generator normal output and --check exact; actual profile/model/source/phase/binding contracts passed',
            'python_tests':'4 tests pass including sealed identity/RAW tamper rejection, wrong binding rejection and pending-app-publication rejection',
            'jvm':'179 existing JVM tests pass on actual candidate Kotlin data; only seven private identity fixture SHA literals replaced; existing ReactionProfiles.kt added to outdated runner source list',
            'renders':'9 actual-target full-body normal original-material PNGs + 9 local original-material PNGs'},
        'not_passed':{
            'LEFT':'Original LEFT retained; veteran R_forearm/chest triangle pairs:1.10s=105,1.15s=93,1.20s=50. Full family not approved.',
            'aesthetics':'Root dynamic visual review pending; hand/wrist cuff and sleeve geometry roughness remains visible in unchanged target geometry',
            'native':'No APK/Gradle/PICO SDK playback/PICO Emulator/Space Pro validation performed'},
        'inherited_grounding_residuals_mm':{t['target']:{side:{
            'minimum_signed_mm':1000*min(f['plane_residual_metres'][side] for f in t['motion_preservation']['right_foot_measurements']),
            'maximum_signed_mm':1000*max(f['plane_residual_metres'][side] for f in t['motion_preservation']['right_foot_measurements'])}
            for side in ('L','R')} for t in review['targets']},
        'intersection_pose_counts':review['intersection_pose_counts'],
        'limits':review['limits']+['No idle 2mm micromotion budget used for dynamic blade preservation: actual same-target Steel delta was exactly zero.',
            'Grounding passes preservation only: existing target foot-plane residuals are retained, not corrected; this is not a dual-foot contact acceptance.',
            'Source .9s joining local second-difference remains16.81mm/19.18mm in sealed indigo/veteran source review; finite tests do not prove C1 continuity.',
            'First private JVM attempt failed because old isolated runner omitted ReactionProfiles.kt; initial compiler error log retained, fixed private harness passes.'],
        'root_next':['Review actual normal/local images and sealed real-time source clips.',
            'Resolve LEFT independently before full-family approval, or explicitly choose a RIGHT-only stage.',
            'If accepted, Root alone updates production_review, formal manifest/library, app typed/assets and runs native SDK/device acceptance.'],
        'artifact_identities':artifacts}
    (HERE / 'handoff.json').write_text(json.dumps(handoff,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'handoff':identity(HERE / 'handoff.json'),'binding_sha256':request['binding_sha256'],
        'artifacts':len(artifacts),'status':handoff['status']},indent=2))


if __name__ == '__main__':
    main()
