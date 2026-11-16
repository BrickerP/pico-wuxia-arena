"""Rebuild the natural-guard private producer inputs; never publishes models or approval."""

import argparse
import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
HERE = Path('ArtSource/tripo-warrior')
OUT = Path('ArtSource/refinement/combat-direction/natural-guard/integration')
FAMILY = Path('ArtSource/refinement/combat-direction/natural-guard/candidate/family-v1')
BASE_COMMIT = '6d3551903440039afbef75a322dd66a6842c1e65'
BASE_SOURCE = 'ArtSource/tripo-warrior/motion_library.json'
BASE_SHA256 = '1d2dd4fdc03b66ebdda954319dc93fbd0adc6fbdede8d5d875ba5ede6cd09ba0'
RAW_SHA256 = {
    'idle': '0cac7c29e9fd9445e3b1e1825c60e885323b870181df33c5242fc0b6b40d95a6',
    'walk': '5c60c6588442beb4f7d287c7621efce8c9621113bf4ded01980815e56bf2f462',
    'attack_overhead': '9ce928b478360d23db60e16d613658853a7856994dcbfa03e7a505777d359696',
    'attack_left': 'ca9c1192def0284f84b2b7c418165c93480b68af0146cb8921b4488b2a0ebecc',
    'attack_right': 'e53f0d7e9fa4c0f9a5ea93e1f2cccb5e25b0d4527a66d94f97dc41f6434f35b9',
}
ALIASES = {'OVERHEAD': 'overhead', 'LEFT': 'slash_to_left', 'RIGHT': 'slash_to_right'}


def fail_unless(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def project_path(repo, relative):
    path = (repo / relative).resolve()
    fail_unless(path.is_relative_to(repo.resolve()), 'Input path escapes the canonical repository')
    return path


def identity(repo, relative):
    path = project_path(repo, relative)
    data = path.read_bytes()
    return {'file': path.relative_to(repo.resolve()).as_posix(), 'sha256': digest(data), 'bytes': len(data)}


def read_json(repo, relative):
    return json.loads(project_path(repo, relative).read_bytes())


def check_record(repo, record, expected_path=None):
    fail_unless(isinstance(record, dict) and {'file', 'sha256', 'bytes'}.issubset(record), 'Incomplete file identity')
    actual = identity(repo, record['file'])
    fail_unless(type(record['bytes']) is int and record['bytes'] > 0 and
                record['bytes'] == actual['bytes'] and record['sha256'] == actual['sha256'],
                'File SHA/byte identity drift: ' + record['file'])
    if expected_path is not None:
        fail_unless(project_path(repo, record['file']) == project_path(repo, expected_path),
                    'File role/path mismatch: ' + record['file'])
    return actual


def producer_entry(repo, relative, sha256):
    return {'source': os.path.relpath(project_path(repo, relative), repo / HERE), 'source_sha256': sha256}


def source_json(repo, entry):
    relative = HERE / entry['source']
    record = identity(repo, relative)
    fail_unless(record['sha256'] == entry['source_sha256'], 'Pinned baseline authoring identity drift')
    return read_json(repo, relative), record


def frozen_baseline(repo):
    result = subprocess.run(['git', 'show', BASE_COMMIT + ':' + BASE_SOURCE], cwd=repo,
                            capture_output=True, check=True, timeout=15)
    fail_unless(digest(result.stdout) == BASE_SHA256, 'Baseline bytes differ from the fixed 6d35519 blob')
    return result.stdout, json.loads(result.stdout)


def verified_family(repo, baseline):
    author_path = FAMILY / 'family_authoring.json'
    author = read_json(repo, author_path)
    author_identity = identity(repo, author_path)
    endpoints = read_json(repo, FAMILY / 'verification_endpoints.json')
    surfaces = read_json(repo, FAMILY / 'verification_surfaces.json')
    fail_unless(author.get('stage') == 'authored_raw' and author.get('right_calibration_baked') is False,
                'Family must remain explicitly unbaked authored RAW')
    fail_unless(endpoints.get('status') == 'all_five_raw_endpoints_passed', 'Five-RAW endpoint review has not passed')
    fail_unless(surfaces.get('status') == 'finite_base_scan_passed', 'Finite base surface review has not passed')
    for report in (endpoints, surfaces):
        fail_unless(check_record(repo, report['authoring'], author_path) == author_identity,
                    'Verification refers to a different family authoring file')
    for key in ('all_raw_original_rest_and_payload_exact', 'all_234_TRS_marker_values_float32_exact',
                'constant_R15_master_UNBAKED_exact', 'three_attack_interiors_0p20_to1p50_exact_source'):
        fail_unless(endpoints.get(key) is True, 'Endpoint guarantee missing: ' + key)
    fail_unless(endpoints.get('walk', {}).get('six_original_leg_TRS_curves_and_time_grid_exact') is True and
                endpoints['walk'].get('original_mixed_interpolation_preserved') is True,
                'Original walk leg curves/time grid/interpolation have not been preserved')
    fail_unless(set(author.get('outputs', {})) == set(RAW_SHA256) and
                set(endpoints.get('clips', {})) == set(RAW_SHA256) and
                set(surfaces.get('clips', {})) == set(RAW_SHA256), 'Expected exactly the five canonical RAW clips')
    guard = check_record(repo, author['guard'])
    fail_unless(check_record(repo, endpoints['master_guard']) == guard, 'Endpoint master guard differs')
    records = {}
    for name, sha in RAW_SHA256.items():
        row = author['outputs'][name]
        raw = check_record(repo, row['raw'], FAMILY / (name + '_raw.glb'))
        fail_unless(raw['sha256'] == sha, 'RAW differs from the selected Root candidate: ' + name)
        fail_unless(check_record(repo, endpoints['clips'][name]['raw']) == raw, 'Endpoint RAW differs: ' + name)
        count = {'idle': 181, 'walk': 185, 'attack_overhead': 211, 'attack_left': 106, 'attack_right': 106}[name]
        end = 1.5 if name in ('idle', 'walk') else 1.75
        markers = [0, 1 / 3, end] if name == 'walk' else [0, end]
        fail_unless(row['clip'] == name and row['track_count'] == 234 and row['joint_count'] == 78 and
                    row['sample_count'] == count and endpoints['clips'][name]['key_count'] == count and
                    row['source_range_seconds'] == [0, end] and
                    endpoints['clips'][name]['exact_master_guard_markers_seconds'] == markers,
                    'RAW channel/joint/key contract differs: ' + name)
        report = surfaces['clips'][name]
        fail_unless(type(report['sample_count']) is int and report['sample_count'] > 0 and
                    len(report['frames']) == report['sample_count'] and type(report['overlap_sample_count']) is int and
                    report['overlap_sample_count'] == 0 and
                    report['once_finger_calibration_and_root_shift_max_component_error'] == 0.0,
                    'Finite surface/once-calibration review differs: ' + name)
        records[name] = raw
    fail_unless(check_record(repo, author['preview']) == check_record(repo, surfaces['preview']),
                'Finite scan preview differs from authored family preview')
    fail_unless(author['body_source'] == baseline['characters'][0] and
                author['body_source']['source_sha256'] == 'a4280be15191970a6271a127bf862adee0ea7b7a93174d1b82c83304e49d52ec',
                'Private base review must use the unchanged a428 material body source')
    fail_unless(author['weapon_source'] == baseline['weapon_source'], 'Private family weapon source differs')
    evidence = {'authoring': author_identity,
                'endpoints': identity(repo, FAMILY / 'verification_endpoints.json'),
                'finite_base_surfaces': identity(repo, FAMILY / 'verification_surfaces.json'),
                'scope': 'Five RAW endpoints and finite private base only; no three-target or native acceptance.'}
    return author, records, guard, evidence


def encoded(document):
    return (json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def build_inputs(repo=REPO):
    repo = repo.resolve()
    baseline_bytes, baseline = frozen_baseline(repo)
    old_locomotion, old_loco_identity = source_json(repo, baseline['locomotion_source']['authoring_manifest'])
    old_attacks, old_attack_identity = source_json(repo, baseline['attack_source']['authoring_manifest'])
    author, raws, guard, evidence = verified_family(repo, baseline)
    provenance = {'commit': BASE_COMMIT, 'source': BASE_SOURCE, 'sha256': BASE_SHA256,
                  'frozen_copy': (OUT / 'baseline_motion_library_6d35519.json').as_posix()}
    walk_source = next(row for row in old_locomotion['profiles'] if row['clip_alias'] == 'walk')
    walk_fields = ('stance_intervals_seconds', 'swing_intervals_seconds', 'steps_per_loop', 'step_pairs_per_loop',
                   'whole_loop_carrier_distance_metres', 'distance_per_pair_metres', 'carrier_distance_per_half_step_metres',
                   'carrier_curve', 'source_root_forward_accumulation_metres', 'swing_sole_clearance_metres',
                   'pair_guard_source_seconds', 'moving_bone_rotations')
    profiles = []
    for name in ('idle', 'walk'):
        raw = {'path': raws[name]['file'], 'sha256': raws[name]['sha256'], 'bytes': raws[name]['bytes'],
               'right_finger_calibration_baked': False}
        row = {'profile': 'natural_guard_' + name, 'clip_alias': name, 'raw': raw,
               'source_range_seconds': [0, 1.5], 'source_loop_seconds': [0, 1.5] if name == 'idle' else [1 / 3, 1.5],
               'source_loop_duration_seconds': 1.5 if name == 'idle' else 7 / 6,
               'sample_count': author['outputs'][name]['sample_count'], 'base_sample_rate_hz': 120,
               'canonical_234_marker_source_seconds': [0, 1.5] if name == 'idle' else [0, 1 / 3, 1.5],
               'right_finger_policy': 'R15_UNBAKED; target grip and right-only calibration applied once by producer',
               'source_verification': copy.deepcopy(evidence)}
        if name == 'idle':
            row.update(interpolation='LINEAR', stance_intervals_seconds={'L_': [[0, 1.5]], 'R_': [[0, 1.5]]},
                       swing_intervals_seconds={}, steps_per_loop=0)
        else:
            row.update({key: copy.deepcopy(walk_source[key]) for key in walk_fields})
            row.update(constant_track_interpolation='STEP', moving_leg_rotation_interpolation='LINEAR',
                       upper_body='same new guard; original six leg TRS curves and time grid preserved')
        profiles.append(row)
    runtime_fields = ('WALK_STRIDE_METERS', 'WALK_LOOP_START', 'WALK_LOOP_DURATION',
                      'physical_steps_per_loop', 'source_time_formula')
    locomotion = {'scope': 'Natural guard breathing idle and original six-step walk; private producer candidate',
                  'source_assets_frozen': True, 'baseline': provenance,
                  'source_rig': copy.deepcopy(old_locomotion['source_rig']),
                  'coordinate_frame': old_locomotion['coordinate_frame'],
                  'canonical_ref': {'clip': 'guard_pose', 'source_seconds': 0, 'raw': guard,
                                    'role': 'source reference only; never a new runtime mode'},
                  'profiles': profiles,
                  'runtime_contract': {key: copy.deepcopy(old_locomotion['runtime_contract'][key]) for key in runtime_fields},
                  'inherited_walk_metadata': {'source': old_loco_identity,
                    'scope': 'Six unchanged leg curves, original gait/foot support timing only; old proxy/lock audits are not acceptance.'},
                  'source_verification': evidence, 'validation_scope': 'Finite base source checks only; Root must retarget and review all three targets.'}
    locomotion['runtime_contract'].update(IDLE_LOOP_START=0, IDLE_LOOP_DURATION=1.5,
        idle_source_time_formula='(enemyMotionNanos % 1500000000) / 1000000000.0; same profile/proxy/SDK sample')
    attacks = {key: copy.deepcopy(old_attacks[key]) for key in
               ('coordinate_frame', 'direction_semantics', 'rig_sha256', 'native_grip_reference')}
    attacks.update(freeze_status='Hash-frozen private natural-guard family; Root production review remains pending',
                   baseline=provenance, source_verification=evidence, clips=[])
    for entry in baseline['attack_source']['clips']:
        name, alias = entry['name'], ALIASES[entry['direction']]
        old = next(row for row in old_attacks['clips'] if row['clip'] == alias)
        fail_unless(old['phase_markers'] == entry['phase_markers'] and
                    old['runtime_phase_nanos'] == entry['runtime_phase_nanos'], 'Baseline per-direction authoring differs')
        row = {key: copy.deepcopy(old[key]) for key in
               ('clip', 'actor_direction', 'source_range_seconds', 'sample_rate_hz', 'interpolation')}
        row.update(raw={'path': raws[name]['file'], 'sha256': raws[name]['sha256'], 'bytes': raws[name]['bytes'],
                        'right_finger_calibration_baked': False}, sample_count=author['outputs'][name]['sample_count'],
                   animation_channel_count=234, source_handoff={'path': evidence['authoring']['file'],
                       'sha256': evidence['authoring']['sha256'], 'bytes': evidence['authoring']['bytes']},
                   phase_markers=copy.deepcopy(entry['phase_markers']), runtime_phase_nanos=copy.deepcopy(entry['runtime_phase_nanos']),
                   contact_source_seconds=entry['phase_markers']['contact'],
                   source_scope='New canonical entry/return; original0.20..1.50s key payloads identical. No old preview or full-clip metrics reused.',
                   inherited_interior_provenance={'old_authoring': old_attack_identity, 'old_raw': copy.deepcopy(old['raw']),
                       'source_range_seconds': [.20, 1.50], 'payload_identity_evidence': evidence['endpoints']})
        attacks['clips'].append(row)
    manifest = copy.deepcopy(baseline)
    manifest.pop('production_review', None)
    for family in ('locomotion_source', 'attack_source'):
        for entry in manifest[family]['clips']:
            entry.update(producer_entry(repo, raws[entry['name']]['file'], raws[entry['name']]['sha256']))
            entry.update(stage='authored_raw', right_calibration_baked=False)
    documents = {'baseline_motion_library_6d35519.json': baseline_bytes,
                 'locomotion_inputs.json': encoded(locomotion), 'attack_bank_inputs.json': encoded(attacks)}
    for family, filename in [('locomotion_source', 'locomotion_inputs.json'), ('attack_source', 'attack_bank_inputs.json')]:
        manifest[family]['authoring_manifest'] = producer_entry(repo, OUT / filename, digest(documents[filename]))
    documents['motion_library_candidate.json'] = encoded(manifest)
    return documents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Validate and print input identities without writing files')
    arguments = parser.parse_args()
    documents = build_inputs()
    if not arguments.dry_run:
        output = REPO / OUT
        output.mkdir(parents=True, exist_ok=True)
        baseline = output / 'baseline_motion_library_6d35519.json'
        fail_unless(not baseline.exists() or baseline.read_bytes() == documents[baseline.name], 'Frozen baseline copy was modified')
        for name, data in documents.items():
            (output / name).write_bytes(data)
    print(json.dumps({'dry_run': arguments.dry_run, 'status': 'validated_private_inputs_not_production_approval',
        'files': {name: {'sha256': digest(data), 'bytes': len(data)} for name, data in documents.items()}}, indent=2))


if __name__ == '__main__':
    main()
