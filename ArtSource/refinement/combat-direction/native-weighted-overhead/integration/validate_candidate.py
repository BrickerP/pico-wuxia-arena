"""Validate candidate inputs with the unmodified producer; never generate model outputs.

Run through the existing combat-source Blender lock (mathutils is required).
All temporary rejection fixtures and the validation report stay in this directory.
"""
import sys
sys.dont_write_bytecode = True

import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

INTEGRATION = Path(__file__).resolve().parent
REPO = INTEGRATION.parents[4]
PRODUCER_DIR = REPO / 'ArtSource/tripo-warrior'
sys.path.insert(0, str(PRODUCER_DIR))
import prepare_character_library as producer
from mathutils import Quaternion
sys.path.insert(0, str(REPO / 'ArtSource/refinement/combat-direction'))
from generate_attack_bank_profiles import runtime_phase_nanos_from_enum


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


class CandidateContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load(INTEGRATION / 'input_contract.json')
        for name in ('baseline_manifest', 'baseline_attack_authoring', 'source_authoring', 'raw', 'producer', 'production_contract'):
            pin = cls.contract[name]
            if digest(REPO / pin['path']) != pin['sha256']:
                raise ValueError('candidate prerequisite changed; Root must review before rebasing: ' + name)
        cls.baseline = load(REPO / cls.contract['baseline_manifest']['path'])
        cls.authoring_baseline = load(REPO / cls.contract['baseline_attack_authoring']['path'])
        cls.manifest = load(INTEGRATION / 'motion_library.json')
        cls.bank = cls.manifest['attack_source']
        cls.rows = producer.attack_source_contracts(cls.bank)
        _, cls.rig, cls.rig_binary = producer.pinned_source(cls.bank)
        cls.sources = {}
        for family_name in ('attack_source', 'locomotion_source'):
            family = cls.manifest[family_name]
            for entry in family['clips']:
                _, document, binary = producer.pinned_source(entry)
                cls.sources[entry['name']] = (entry, document, binary, cls.rig, family['contract'])

    def changed_authoring(self, change):
        temporary = tempfile.TemporaryDirectory(prefix='.negative-', dir=INTEGRATION)
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / 'attack_bank_inputs.json'
        authoring = load(INTEGRATION / 'attack_bank_inputs.json')
        change(authoring)
        path.write_text(json.dumps(authoring, ensure_ascii=False, indent=2) + '\n')
        changed = copy.deepcopy(self.manifest)
        changed['attack_source']['authoring_manifest'] = {'source': str(path), 'source_sha256': digest(path)}
        return changed

    def test_manifest_uses_the_existing_validator_and_only_allowed_changes(self):
        frozen, coverage = producer.validate_manifest(self.manifest)
        self.assertEqual({'base', 'indigo', 'veteran'}, set(coverage))
        self.assertTrue(frozen['source_assets_frozen'])
        expected = copy.deepcopy(self.baseline)
        expected.pop('production_review')
        expected['attack_source']['clips'][0]['source'] = self.bank['clips'][0]['source']
        expected['attack_source']['clips'][0]['source_sha256'] = self.contract['raw']['sha256']
        expected['attack_source']['authoring_manifest'] = self.bank['authoring_manifest']
        expected['attack_source'].pop('phase_markers')
        for row in expected['attack_source']['clips']:
            declared = self.contract['per_direction_development_contracts'][row['direction']]
            row['phase_markers'] = declared['phase_markers']
            row['runtime_phase_nanos'] = declared['runtime_phase_nanos']
        self.assertEqual(expected, self.manifest)
        for before, after in zip(self.authoring_baseline['clips'][1:], load(INTEGRATION / 'attack_bank_inputs.json')['clips'][1:]):
            expected_row = copy.deepcopy(before)
            expected_row.pop('ACTIVE_phase_elapsed_ms')
            actual_row = copy.deepcopy(after)
            for name in ('phase_markers', 'runtime_phase_nanos', 'phase_contract_status'):
                actual_row.pop(name)
            self.assertEqual(expected_row, actual_row)
        self.assertNotIn('production_review', self.manifest)

    def test_three_complete_raw_sources_keep_their_exact_authoring_grids(self):
        for entry in self.bank['clips']:
            with self.subTest(direction=entry['direction']):
                _, document, binary, _, _ = self.sources[entry['name']]
                tracks = producer.validate_source_clip(document, binary, self.rig, self.rig_binary,
                    'attack78', entry['name'], self.rows[entry['name']])
                self.assertEqual(234, len(tracks))
                self.assertEqual(211 if entry['direction'] == 'OVERHEAD' else 106,
                    len(next(iter(tracks.values()))[0]))

    def test_direction_runtime_contracts_match_the_actual_kotlin_enum(self):
        actual = runtime_phase_nanos_from_enum()
        self.assertEqual({'OVERHEAD', 'LEFT', 'RIGHT'}, set(actual))
        for entry in self.bank['clips']:
            self.assertEqual(actual[entry['direction']], entry['runtime_phase_nanos'])

    def test_existing_canonical_guard_and_locomotion_contract_still_closes(self):
        frozen, _ = producer.validate_manifest(self.manifest)
        for name in ('idle', 'walk'):
            entry, document, binary, _, _ = self.sources[name]
            producer.validate_source_clip(document, binary, self.rig, self.rig_binary,
                'locomotion78', entry['name'])
        evidence = producer.canonical_source_evidence(list(self.sources.values()), frozen)
        self.assertEqual({'idle', 'walk'}, set(evidence))
        self.assertTrue(all(row['canonical_234_trs_markers_exact'] for row in evidence.values()))

    def test_manifest_raw_hash_tampering_is_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['attack_source']['clips'][0]['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'frozen unbaked authoring source'):
            producer.validate_manifest(changed)

    def test_actual_raw_byte_tampering_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory(prefix='.negative-', dir=INTEGRATION) as temporary:
            path = Path(temporary) / 'tampered.glb'
            path.write_bytes((REPO / self.contract['raw']['path']).read_bytes() + b'\0')
            entry = copy.deepcopy(self.bank['clips'][0])
            entry['source'] = str(path)
            with self.assertRaisesRegex(ValueError, 'source hash differs from manifest'):
                producer.pinned_source(entry)

    def test_baked_finger_flag_in_source_descriptor_is_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['attack_source']['clips'][0]['right_calibration_baked'] = True
        with self.assertRaisesRegex(ValueError, 'unbaked authored raw'):
            producer.validate_manifest(changed)

    def test_baked_finger_flag_in_rehashed_authoring_is_rejected(self):
        changed = self.changed_authoring(lambda authoring:
            authoring['clips'][0]['raw'].update(right_finger_calibration_baked=True))
        with self.assertRaisesRegex(ValueError, 'frozen unbaked authoring source'):
            producer.validate_manifest(changed)

    def test_frozen_authoring_hash_tampering_is_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['attack_source']['authoring_manifest']['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'frozen attack input manifest hash changed'):
            producer.validate_manifest(changed)

    def test_actual_private_preview_cannot_masquerade_as_raw(self):
        path = INTEGRATION.parent / 'candidate/v3/weighted_overhead_preview.glb'
        # A correct preview hash cannot authorize its baked/normalized data as RAW.
        _, document, binary = producer.pinned_source({'source': str(path), 'source_sha256': digest(path)})
        with self.assertRaises(ValueError):
            producer.validate_source_clip(document, binary, self.rig, self.rig_binary,
                'attack78', 'attack_overhead', self.rows['attack_overhead'])

    def test_actual_baked_finger_correction_breaks_the_existing_canonical_raw_family(self):
        entry, document, binary, rig, contract = self.sources['attack_overhead']
        names = producer.joint_nodes(document)
        animation = document['animations'][0]
        channel = next(row for row in animation['channels'] if row['target'] ==
            {'node': names['R_Thumb1'], 'path': 'rotation'})
        accessor = document['accessors'][animation['samplers'][channel['sampler']]['output']]
        view = document['bufferViews'][accessor['bufferView']]
        self.assertNotIn('byteStride', view)
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        altered = bytearray(binary)
        correction = Quaternion((1.0, 0.0, 0.0), math.radians(4.5))
        for index in range(accessor['count']):
            offset = start + index * 16
            x, y, z, w = struct.unpack_from('<4f', binary, offset)
            baked = (Quaternion((w, x, y, z)) @ correction).normalized()
            struct.pack_into('<4f', altered, offset, baked.x, baked.y, baked.z, baked.w)
        with tempfile.TemporaryDirectory(prefix='.negative-', dir=INTEGRATION) as temporary:
            path = Path(temporary) / 'baked_finger_raw.glb'
            path.write_bytes(producer.encode_glb(document, bytes(altered)))
            _, changed, changed_binary = producer.pinned_source({'source': str(path), 'source_sha256': digest(path)})
            # Even with a truthful file hash and a syntactically valid 234-track grid,
            # once-baked calibration cannot be passed off as the frozen RAW family.
            producer.validate_source_clip(changed, changed_binary, self.rig, self.rig_binary,
                'attack78', 'attack_overhead', self.rows['attack_overhead'])
            family = dict(self.sources)
            family['attack_overhead'] = (entry, changed, changed_binary, rig, contract)
            frozen, _ = producer.validate_manifest(self.manifest)
            with self.assertRaisesRegex(ValueError, 'locomotion raw guard marker differs'):
                producer.canonical_source_evidence(list(family.values()), frozen)

    def test_wrong_grid_is_rejected_by_existing_source_validation(self):
        _, document, binary, _, _ = self.sources['attack_overhead']
        row = copy.deepcopy(self.rows['attack_overhead'])
        row['sample_count'] = 210
        with self.assertRaisesRegex(ValueError, 'authoring time contract'):
            producer.validate_source_clip(document, binary, self.rig, self.rig_binary,
                'attack78', 'attack_overhead', row)

    def test_legacy_shared_phase_contract_is_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed['attack_source']['phase_markers'] = copy.deepcopy(changed['attack_source']['clips'][0]['phase_markers'])
        with self.assertRaises(ValueError):
            producer.validate_manifest(changed)

    def test_direction_phase_and_runtime_cannot_drift_from_bound_authoring(self):
        for field in ('phase_markers', 'runtime_phase_nanos'):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.manifest)
                if field == 'phase_markers':
                    changed['attack_source']['clips'][0][field]['startup_end'] = 0.9
                else:
                    changed['attack_source']['clips'][0][field][1] += 1
                with self.assertRaises(ValueError):
                    producer.validate_manifest(changed)

    def test_consistent_non_midpoint_cue_is_metadata_rather_than_a_fixed_one_second_gate(self):
        changed = self.changed_authoring(lambda authoring: authoring['clips'][0].update(
            phase_markers={**authoring['clips'][0]['phase_markers'], 'contact': 0.95},
            contact_source_seconds=0.95))
        changed['attack_source']['clips'][0]['phase_markers']['contact'] = 0.95
        producer.validate_manifest(changed)

    def test_no_formal_publication_or_review_can_be_inherited(self):
        with self.assertRaisesRegex(ValueError, 'requires Root production_review'):
            producer.validate_production_review(self.manifest, {})
        # This real entry point rejects before source conversion, encoding or publication.
        with self.assertRaisesRegex(ValueError, 'private --candidate-dir'):
            producer.build_library(INTEGRATION / 'motion_library.json')


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CandidateContracts)
    test_cases = [test.id() for test in suite]
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        'status': 'source_contract_validation_passed' if result.wasSuccessful() else 'failed',
        'tests_run': result.testsRun, 'test_cases': test_cases,
        'failures': len(result.failures), 'errors': len(result.errors),
        'producer_functions_executed': ['validate_manifest', 'attack_source_contracts', 'pinned_source',
            'validate_source_clip', 'canonical_source_evidence', 'validate_production_review',
            'build_library without approval: rejected before model generation'],
        'candidate_target_models_generated': False, 'formal_publication_executed': False,
        'negative_fixture_policy': 'Temporary GLB/JSON mutations under integration only; removed after tests.',
        'production_review': 'absent; Root target-output inspection and approval still required',
        'inputs': {name: {'path': str(path.relative_to(REPO)), 'sha256': digest(path)} for name, path in (
            ('manifest', INTEGRATION / 'motion_library.json'),
            ('three_direction_authoring', INTEGRATION / 'attack_bank_inputs.json'),
            ('input_contract', INTEGRATION / 'input_contract.json'),
            ('validation_script', Path(__file__).resolve()),
            ('producer', PRODUCER_DIR / 'prepare_character_library.py'),
            ('production_contract', PRODUCER_DIR / 'production_contract.py'),
            ('typed_generator', REPO / 'ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py'),
            ('actual_runtime_enum', REPO / 'app/src/main/java/com/example/wuxiaarena/core/combat/EnemyCombatStateMachine.kt'))},
        'limits': ['Root-reviewed per-direction development window; bounded reference samples do not prove full sharpened-mesh cutting direction.',
            'No target retargeting, KTX encoding, output profiles, formal/app writes, runtime or device validation.'],
    }
    (INTEGRATION / 'validation_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
