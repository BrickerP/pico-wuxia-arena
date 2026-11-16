"""Validate private input construction against real frozen files; no producer or asset writes."""

import contextlib
import io
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import prepare_integration_inputs as prepare


class IntegrationInputsTest(unittest.TestCase):
    def test_happy_path_preserves_targets_and_builds_only_the_new_source_contracts(self):
        first = prepare.build_inputs()
        self.assertEqual(first, prepare.build_inputs())
        self.assertEqual(len(first), 4)
        self.assertEqual(prepare.digest(first['baseline_motion_library_6d35519.json']), prepare.BASE_SHA256)
        baseline = json.loads(first['baseline_motion_library_6d35519.json'])
        candidate = json.loads(first['motion_library_candidate.json'])
        for field in ('characters', 'motion_source', 'body_coverage_calibration', 'runtime_texture_encoding',
                      'weapon_source', 'player_weapon_source'):
            self.assertEqual(candidate[field], baseline[field])
        self.assertNotIn('production_review', candidate)
        locomotion = json.loads(first['locomotion_inputs.json'])
        idle, walk = locomotion['profiles']
        self.assertEqual(idle['source_loop_seconds'], [0, 1.5])
        self.assertEqual(idle['sample_count'], 181)
        self.assertEqual(idle['interpolation'], 'LINEAR')
        self.assertEqual(idle['stance_intervals_seconds'], {'L_': [[0, 1.5]], 'R_': [[0, 1.5]]})
        self.assertEqual(walk['source_loop_seconds'], [1 / 3, 1.5])
        self.assertEqual(walk['sample_count'], 185)
        for row in locomotion['profiles']:
            for stale in ('preview', 'locked_head_ancestor_chain', 'maximum_world_proxy_relative_canonical_difference_metres',
                          'independent_audit_status', 'right_finger_calibration'):
                self.assertNotIn(stale, row)
        attacks = json.loads(first['attack_bank_inputs.json'])
        for row, source in zip(attacks['clips'], baseline['attack_source']['clips']):
            self.assertEqual(row['phase_markers'], source['phase_markers'])
            self.assertEqual(row['runtime_phase_nanos'], source['runtime_phase_nanos'])
            self.assertEqual(row['raw']['sha256'], prepare.RAW_SHA256[source['name']])
            self.assertNotIn('preview', row)
            self.assertNotIn('real_surface_contact', row)
            self.assertNotIn('blade_kinematics', row)
        for family, filename in [('locomotion_source', 'locomotion_inputs.json'), ('attack_source', 'attack_bank_inputs.json')]:
            self.assertEqual(candidate[family]['authoring_manifest']['source_sha256'], prepare.digest(first[filename]))
            for row in candidate[family]['clips']:
                self.assertEqual(row['source_sha256'], prepare.RAW_SHA256[row['name']])
                self.assertFalse(row['right_calibration_baked'])

    def test_raw_byte_tampering_is_rejected_without_changing_original_sources(self):
        original = Path.read_bytes
        raw = (prepare.REPO / prepare.FAMILY / 'walk_raw.glb').resolve()

        def tampered(path):
            data = original(path)
            return data + b'tampered RAW' if path.resolve() == raw else data

        with patch.object(Path, 'read_bytes', tampered):
            with self.assertRaisesRegex(ValueError, 'SHA/byte identity drift'):
                prepare.build_inputs()

    def test_failed_or_wrong_verification_status_is_rejected(self):
        original = prepare.read_json
        for filename in ('verification_endpoints.json', 'verification_surfaces.json'):
            def changed(repo, relative):
                data = original(repo, relative)
                if relative.name == filename:
                    data['status'] = 'failed'
                return data
            with self.subTest(filename=filename), patch.object(prepare, 'read_json', side_effect=changed):
                with self.assertRaisesRegex(ValueError, 'has not passed'):
                    prepare.build_inputs()

    def test_green_status_cannot_authorize_a_different_authoring_identity(self):
        original = prepare.read_json

        def stale(repo, relative):
            data = original(repo, relative)
            if relative.name == 'verification_endpoints.json':
                data['authoring']['sha256'] = '0' * 64
            return data

        with patch.object(prepare, 'read_json', side_effect=stale):
            with self.assertRaisesRegex(ValueError, 'SHA/byte identity drift'):
                prepare.build_inputs()

    def test_wrong_baseline_commit_bytes_are_rejected(self):
        with patch.object(prepare.subprocess, 'run', return_value=SimpleNamespace(stdout=b'wrong baseline')):
            with self.assertRaisesRegex(ValueError, 'fixed 6d35519 blob'):
                prepare.build_inputs()

    def test_dry_run_reports_deterministic_hashes_without_writing_outputs(self):
        output = prepare.REPO / prepare.OUT
        names = ('baseline_motion_library_6d35519.json', 'locomotion_inputs.json',
                 'attack_bank_inputs.json', 'motion_library_candidate.json')
        before = {name: (output / name).read_bytes() if (output / name).exists() else None for name in names}
        stdout = io.StringIO()
        with patch('sys.argv', ['prepare_integration_inputs.py', '--dry-run']), contextlib.redirect_stdout(stdout):
            prepare.main()
        result = json.loads(stdout.getvalue())
        self.assertTrue(result['dry_run'])
        self.assertEqual(result['status'], 'validated_private_inputs_not_production_approval')
        for name in names:
            self.assertEqual(before[name], (output / name).read_bytes() if (output / name).exists() else None)


if __name__ == '__main__':
    unittest.main()
