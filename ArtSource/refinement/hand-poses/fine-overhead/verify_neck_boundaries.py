"""Supplemental host-only rejection checks and completed-scan provenance.

Does not build a candidate, run Blender, or repeat the BVH scan.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.dont_write_bytecode = True
import build_neck_refinement as build


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    frozen = {p: digest(p) for p in build.PARENT.iterdir() if p.is_file()}
    rejected = []
    def refuses(label, function):
        try:
            function()
        except ValueError as error:
            rejected.append({'case': label, 'exception': 'ValueError', 'message': str(error)})
        else:
            raise AssertionError('invalid input accepted: '+label)
    for value in (float('nan'), float('inf'), -float('inf'), -.001, 1.751, True, False):
        refuses('correction_weight_'+repr(value), lambda value=value: build.correction_weight(value))
    raw = build.PARENT/'fine_overhead_raw.glb'
    for value in (float('nan'), float('inf'), -.1, 0., 1.01):
        refuses('gain_'+repr(value), lambda value=value: build.patched_bytes(raw, gain=value))
    original = build.read_glb(raw)
    doc, binary, start, encoded = original
    names = {node.get('name'): index for index, node in enumerate(doc['nodes'])}
    missing = copy.deepcopy(doc)
    missing['nodes'][names['NeckTwist02']]['name'] = 'missing_neck_test'
    with patch.object(build, 'read_glb', return_value=(missing, binary, start, encoded)):
        refuses('missing_NeckTwist02', lambda: build.patched_bytes(raw))
    hierarchy = copy.deepcopy(doc)
    hierarchy['nodes'][names['NeckTwist01']]['children'].remove(names['NeckTwist02'])
    hierarchy['nodes'][names['Spine02']]['children'].append(names['NeckTwist02'])
    with patch.object(build, 'read_glb', return_value=(hierarchy, binary, start, encoded)):
        refuses('NeckTwist02_wrong_parent', lambda: build.patched_bytes(raw))
    head_parent = copy.deepcopy(doc)
    head_parent['nodes'][names['NeckTwist02']]['children'].remove(names['Head'])
    head_parent['nodes'][names['NeckTwist01']]['children'].append(names['Head'])
    with patch.object(build, 'read_glb', return_value=(head_parent, binary, start, encoded)):
        refuses('Head_wrong_parent', lambda: build.patched_bytes(raw))
    assert all(digest(path) == sha for path, sha in frozen.items()), 'frozen v7 input mutated'
    primary_path = build.OUTPUT/'fine_overhead_neck_verification.json'
    primary = json.loads(primary_path.read_text())
    assert primary['surface_scan']['status'] == 'scanned', 'primary completed scan is required before supplement'
    source_relatives = [
        'ArtSource/refinement/hand-poses/fine-overhead/build_neck_refinement.py',
        'ArtSource/refinement/hand-poses/fine-overhead/verify_neck_refinement.py',
        'ArtSource/refinement/hand-poses/fine-overhead/verify_fine_overhead.py',
        'ArtSource/refinement/hand-poses/fine-overhead/build_fine_overhead.py',
        'ArtSource/refinement/hand-poses/attack-keyposes/build_keyposes.py',
        'ArtSource/refinement/hand-poses/attack-keyposes/stage4/build_overhead.py',
        'ArtSource/tripo-warrior/refine_character_grips.py',
        'ArtSource/tripo-warrior/prepare_character_library.py',
        'ArtSource/tripo-warrior/prepare_rigged_warrior.py',
        'ArtSource/refinement/hand-poses/run_blender.py',
    ]
    closure = {relative: digest(build.REPO/relative) for relative in source_relatives}
    for relative, sha in primary['source_pins'].items():
        assert digest(build.REPO/relative) == sha, 'primary executed code/evidence changed before provenance capture'
    result = {'completion': 'supplemental_host_checks_passed',
      'primary_report_sha256_before_supplement': digest(primary_path),
      'rejected_inputs': rejected,
      'frozen_v7_files_unchanged': {str(path.relative_to(build.REPO)): sha for path, sha in frozen.items()},
      'host_check_source_sha256': digest(Path(__file__)),
      'executed_scan_helper_import_closure_sha256': closure,
      'dependency_roles': {
        'main_patch': 'build_neck_refinement.py directly patches frozen GLB bytes using host NumPy; does not import or invoke public producer',
        'host_FK_verify': 'verify_neck_refinement.py uses build_neck_refinement.py NumPy math',
        'surface_scan': 'verify_neck_refinement.py imports surface/steel_points from verify_fine_overhead.py; that imports build_fine_overhead.py, its dynamic stage4 stance module, build_keyposes and listed public producer/math modules',
        'producer_usage_in_surface_scan': 'Imported helper/module closure only; no producer rebuild, retarget, calibration application or publishing is invoked',
        'capture_timing': 'File identities captured after the completed primary scan; original primary verifier source identity is preserved and asserted unchanged',
      },
      'no_BVH_rerun': True, 'no_candidate_or_v7_rewrite': True}
    output = build.OUTPUT/'fine_overhead_neck_boundary_verification.json'
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    primary['post_scan_dependency_provenance'] = {
      'supplement': {'file': str(output.relative_to(build.REPO)), 'sha256': digest(output)},
      'source_capture_timing': result['dependency_roles']['capture_timing'],
      'primary_verifier_source_unchanged': True,
      'patch_and_surface_dependency_roles': result['dependency_roles']}
    primary['source_pins'].update(closure)
    primary_path.write_text(json.dumps(primary, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'completion': result['completion'], 'rejected_case_count': len(rejected),
                      'supplement': str(output), 'primary_scan_result_retained': primary['completion']}, indent=2))


if __name__ == '__main__':
    main()
