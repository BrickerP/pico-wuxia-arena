"""Compose one private RIGHT replacement for the existing canonical producer."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
REPO = OUT.parents[5]
PRODUCER = REPO / 'ArtSource/tripo-warrior'
HANDOFF = REPO / 'ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/handoff.json'
HANDOFF_SHA = 'd82b4d08da5d55bfbe4bcfe58712bba1c966d3b8dab1b31081b8cc730d032547'
RAW_SHA = 'a726b0f65680b7ac8ed2f4dac15e23d9525054786f398d0068712e7c42705aa4'
spec = importlib.util.spec_from_file_location('existing_natural_inputs', OUT.parent / 'prepare_integration_inputs.py')
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def build():
    # Validate the existing five-RAW family using its original reconstruction;
    # retain the current formal target/encoder configuration for the new export.
    existing = prepare.build_inputs()
    formal_path = PRODUCER / 'motion_library.json'
    formal = json.loads(formal_path.read_bytes())
    baseline_candidate = json.loads(existing['motion_library_candidate.json'])
    for family in ('locomotion_source', 'attack_source'):
        prepare.fail_unless(formal[family] == baseline_candidate[family],
                           'Current formal family differs from verified natural family v1')
    handoff_identity = prepare.identity(REPO, HANDOFF)
    prepare.fail_unless(handoff_identity['sha256'] == HANDOFF_SHA, 'RIGHT handoff identity differs')
    handoff = json.loads(HANDOFF.read_bytes())
    prepare.fail_unless(handoff['status'] == 'numeric_stage_complete_pending_root_dynamic_three_target_native_review',
                       'RIGHT source has not been sealed at the expected numeric stage')
    for record in handoff['artifact_identities']:
        prepare.check_record(REPO, record)
    raw = prepare.check_record(REPO, handoff['raw'])
    prepare.fail_unless(raw['sha256'] == RAW_SHA, 'RIGHT RAW identity differs')
    manifest = copy.deepcopy(formal)
    manifest.pop('production_review', None)
    attacks = json.loads((PRODUCER / formal['attack_source']['authoring_manifest']['source']).read_bytes())
    previous = copy.deepcopy(next(row for row in attacks['clips'] if row['clip'] == 'slash_to_right'))
    row = next(row for row in attacks['clips'] if row['clip'] == 'slash_to_right')
    row['raw'] = {'path': raw['file'], 'sha256': raw['sha256'], 'bytes': raw['bytes'],
                  'right_finger_calibration_baked': False}
    row['source_handoff'] = {'path': handoff_identity['file'], 'sha256': HANDOFF_SHA,
                             'bytes': handoff_identity['bytes']}
    row['source_scope'] = handoff['scope'] + '; three-target canonical export required; not production approval'
    row['inherited_interior_provenance'] = {'previous_raw': previous['raw'],
        'scope': 'Only RIGHT empty left-arm rotations change; original full-interior identity no longer applies',
        'sealed_source_evidence': handoff_identity}
    attacks['inherited_unchanged_family_source_verification'] = attacks.pop('source_verification')
    attacks['source_verification'] = {'right_handoff': handoff_identity, 'right_raw': raw,
        'scope': 'Sealed numeric RIGHT source only; old family evidence applies only to unchanged sources. Actual canonical target review required.',
        'production_approved': False, 'left_integrated': False}
    attacks['freeze_status'] = 'Private RIGHT clearance replacement; Root review pending; LEFT unresolved'
    attack_bytes = prepare.encoded(attacks)
    name = 'attack_bank_inputs.json'
    entry = next(row for row in manifest['attack_source']['clips'] if row['name'] == 'attack_right')
    entry.update(prepare.producer_entry(REPO, raw['file'], raw['sha256']))
    manifest['attack_source']['authoring_manifest'] = prepare.producer_entry(
        REPO, OUT / name, prepare.digest(attack_bytes))
    documents = {name: attack_bytes, 'motion_library_candidate.json': prepare.encoded(manifest)}
    receipt = {'status': 'private_RIGHT_only_inputs_not_approval', 'handoff': handoff_identity,
        'raw': raw, 'formal_manifest_before': prepare.identity(REPO, formal_path),
        'existing_input_builder': prepare.identity(REPO, OUT.parent / 'prepare_integration_inputs.py'),
        'left_integrated': False, 'left_status': 'unsealed; original LEFT preserved',
        'preserved_formal_fields': [key for key in formal if key not in ('attack_source', 'production_review')],
        'files': {name: {'sha256': prepare.digest(data), 'bytes': len(data)} for name, data in documents.items()}}
    return documents, receipt


def main():
    documents, receipt = build()
    for name, data in documents.items():
        (OUT / name).write_bytes(data)
    (OUT / 'input_receipt.json').write_bytes(prepare.encoded(receipt))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
