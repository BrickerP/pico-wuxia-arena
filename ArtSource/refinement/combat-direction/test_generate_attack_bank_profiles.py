import copy
import json
import unittest
from unittest.mock import patch

import generate_attack_bank_profiles as generator


BOUND_BINDING = '1b3e031d6f0510ba9d955cd0eee7b34fbc03dcf256cd23958d252873e9221fe2'
BOUND_MODELS = {'base': 'ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20', 'indigo': '94773349741af7cdd2616bb3f5970c5c9fa16f16199c1d0ce5bf6fde6ee0c54e', 'veteran': 'cabf24597a83d46495ad67b451867aaf5e1dad1bbb5df21cae286513af9a17a5'}


class GenerateAttackBankProfilesTest(unittest.TestCase):
    def test_published_schema3_library_exactly_regenerates_runtime_data(self):
        self.assertEqual(generator.REPO / 'ArtSource/tripo-warrior/library', generator.DEFAULT_BANK)
        self.assertIn('// Prepared source: ArtSource/tripo-warrior/library\n', generator.DEFAULT_OUTPUT.read_text())
        bank = generator.DEFAULT_BANK
        review = json.loads((bank / 'production_review_request.json').read_text())
        self.assertEqual(BOUND_BINDING, review['binding_sha256'])
        self.assertEqual(generator.generate(bank), generator.DEFAULT_OUTPUT.read_text())
        data = generator.load_bank(bank)
        self.assertEqual(len(data), 3)
        self.assertEqual(BOUND_MODELS, {c['id']: profile['model_sha256'] for c, profile, _ in data})
        self.assertEqual(sum(len(p['attacks'][d]['samples']) for _, p, _ in data for d in generator.DIRECTIONS), 954)
        self.assertEqual(sum(len(p['locomotion'][name]['samples']) for _, p, _ in data for name in ['idle', 'walk']), 1662)

    def test_profile_identity_drift_is_rejected_before_export(self):
        with patch.object(generator, 'sha256', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'Profile SHA differs'):
                generator.load_bank(generator.DEFAULT_BANK)

    def test_model_identity_drift_is_rejected_before_export(self):
        actual_sha256 = generator.sha256
        with patch.object(generator, 'sha256', side_effect=lambda path: '0' * 64 if path.suffix == '.glb' else actual_sha256(path)):
            with self.assertRaisesRegex(ValueError, 'Prepared model identity differs'):
                generator.load_bank(generator.DEFAULT_BANK)

    def test_old_two_step_or_misaligned_contact_contract_is_rejected(self):
        bank = generator.DEFAULT_BANK
        character = json.loads((bank / 'characters.json').read_text())['characters'][0]
        profile = json.loads((bank / character['attack_profiles']['file']).read_text())
        self.assertEqual(6, len(generator.gait_step_events(profile)))
        two_steps = copy.deepcopy(profile)
        two_steps['source_contract']['steps_per_loop'] = 2
        with self.assertRaisesRegex(ValueError, 'six-step'):
            generator.gait_step_events(two_steps)
        shifted = copy.deepcopy(profile)
        shifted['source_contract']['contact_phases']['R_'][0][0] += 0.01
        with self.assertRaisesRegex(ValueError, 'support entry'):
            generator.gait_step_events(shifted)

    def test_cross_clip_canonical_drift_is_rejected(self):
        bank = generator.DEFAULT_BANK
        character = json.loads((bank / 'characters.json').read_text())['characters'][0]
        profile = json.loads((bank / character['attack_profiles']['file']).read_text())
        generator.validate_canonical_boundaries(profile)
        bad_walk = copy.deepcopy(profile)
        for sample in bad_walk['locomotion']['walk']['samples']:
            sample['head'][0] += 0.001
        with self.assertRaisesRegex(ValueError, 'idle and walk canonical boundary'):
            generator.validate_canonical_boundaries(bad_walk)
        for direction in generator.DIRECTIONS:
            for endpoint in [0, -1]:
                drifted = copy.deepcopy(profile)
                drifted['attacks'][direction]['samples'][endpoint]['blade_tip'][0] += 0.001
                with self.assertRaisesRegex(ValueError, 'attack canonical boundary'):
                    generator.validate_canonical_boundaries(drifted)


if __name__ == '__main__':
    unittest.main()
