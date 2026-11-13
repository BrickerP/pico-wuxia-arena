import copy
import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import generate_attack_bank_profiles as generator


BOUND_BINDING = '365578d497f3a592e08cbe158f90777fe326211f8d9593bab85ff807c0ac07ac'
BOUND_MODELS = {'base': '6ca12659ef6705b2fba43ace092fb8eb567df090c55849b87869e79a9031df24', 'indigo': '27782bbe11bfff327d4635a1c5276053dda012c12bf2911047fbe880653121df', 'veteran': '6d4211c8ed07dffb3f683748688120c581e2ee82b12559941b68a6d7170fcee2'}


def reaction_fixture():
    def sample(time):
        return {'source_seconds': time, 'head': [0.0, 1.6, time],
                'body_bottom': [0.0, .55, time], 'body_top': [0.0, 1.4, time],
                'blade_base': [.2, 1.0, time], 'blade_tip': [.2, 1.0, time + .72]}
    return {name: {'clip': name, 'source_range_seconds': [.03, 1.3],
                   'playback_range_seconds': [.05, end],
                   'animation_semantics_sha256': hashlib.sha256(name.encode()).hexdigest(),
                   'samples': [sample(.03), sample(1.3)]}
            for name, (_, end) in generator.REACTIONS.items()}


class ReactionBankFixture:
    """Small schema fixture; model bytes test identity checking, not GLB rendering."""
    def __enter__(self):
        folder = generator.REPO / 'build'
        folder.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix='reaction-bank-test-', dir=folder)
        self.path = Path(self.temporary.name)
        self.review = {'binding': {'schema_version': 3}, 'characters': []}
        self.review['binding_sha256'] = hashlib.sha256(json.dumps(
            self.review['binding'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        self.characters, self.profiles = [], {}
        source = json.loads((generator.DEFAULT_BANK / 'base_attack_profiles.json').read_text())
        # Keep real contract metadata; reduce only sample density to exact required keys.
        for cid in ('base', 'indigo', 'veteran'):
            model = self.path / (cid + '.glb')
            model.write_bytes(('fixture-model-' + cid).encode())
            profile = copy.deepcopy(source)
            profile['model_sha256'] = generator.sha256(model)
            for name, clip in profile['locomotion'].items():
                start = copy.deepcopy(source['locomotion']['idle']['samples'][0])
                end = copy.deepcopy(start)
                end['source_seconds'] = 1.5
                clip['samples'] = [start, end]
            for clip in profile['attacks'].values():
                clip['samples'] = [copy.deepcopy(source['locomotion']['idle']['samples'][0]) for _ in range(3)]
                for row, time in zip(clip['samples'], (0.0, 1.0, 1.75)):
                    row['source_seconds'] = time
            profile['reactions'] = reaction_fixture()
            self.profiles[cid] = profile
            signatures = {clip['clip']: clip['animation_semantics_sha256']
                          for group in ('locomotion', 'attacks', 'reactions') for clip in profile[group].values()}
            output = {'file': model.name, 'sha256': profile['model_sha256']}
            self.characters.append({'id': cid, 'output': model.name, 'outputs': [output],
                                    'attack_profiles': {'file': cid + '_attack_profiles.json'}})
            self.review['characters'].append({'id': cid, 'outputs': [output], 'clip_semantic_signatures': signatures})
        self.write()
        return self

    def write(self):
        for character, reviewed in zip(self.characters, self.review['characters']):
            profile = self.path / character['attack_profiles']['file']
            profile.write_text(json.dumps(self.profiles[character['id']]))
            digest = generator.sha256(profile)
            character['attack_profiles']['sha256'] = digest
            reviewed['attack_profiles_sha256'] = digest
        (self.path / 'characters.json').write_text(json.dumps({'characters': self.characters}))
        (self.path / 'production_review_request.json').write_text(json.dumps(self.review))

    def __exit__(self, *args):
        self.temporary.cleanup()


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
        self.assertEqual(sum(len(p['attacks'][d]['samples']) for _, p, _ in data for d in generator.DIRECTIONS), 1269)
        self.assertEqual(sum(len(p['locomotion'][name]['samples']) for _, p, _ in data for name in ['idle', 'walk']), 1662)
        self.assertTrue(all(set(profile['reactions']) == set(generator.REACTIONS) for _, profile, _ in data))

    def test_reactions_validate_and_generate_for_each_actor_without_replacing_the_existing_clips(self):
        with ReactionBankFixture() as bank:
            loaded = generator.load_bank(bank.path)
            self.assertEqual(['base', 'indigo', 'veteran'], [character['id'] for character, _, _ in loaded])
            output = generator.generate(bank.path)
            self.assertEqual(output.count('reactions = ReactionProfiles('), 3)
            self.assertEqual(output.count('AttackDirection.'), 9)
            self.assertEqual(output.count('locomotion = LocomotionProfile('), 3)
            for cid in bank.profiles:
                for name, (field, _) in generator.REACTIONS.items():
                    title = name.title().replace('_', '')
                    self.assertIn(f'{field} = PoseClipProfile("{name}", {cid}{title}()),', output)
                    self.assertIn(f'private fun {cid}{title}(): List<AttackPoseSample> = decodeAttackSamples(', output)

    def test_cli_relative_output_writes_successfully_and_passes_check(self):
        with ReactionBankFixture() as bank:
            output = Path(os.path.relpath(bank.path / 'AttackBankProfileData.kt', Path.cwd()))
            arguments = ['generate_attack_bank_profiles.py', '--bank', str(bank.path), '--output', str(output)]
            stdout = io.StringIO()
            with patch('sys.argv', arguments), redirect_stdout(stdout):
                generator.main()
            self.assertTrue(output.is_file())
            self.assertEqual(generator.generate(bank.path), output.read_text())
            self.assertIn(f'Generated {output} (', stdout.getvalue())
            stdout = io.StringIO()
            with patch('sys.argv', arguments + ['--check']), redirect_stdout(stdout):
                generator.main()
            self.assertIn('Verified exact generated attack data:', stdout.getvalue())

    def test_missing_reaction_group_or_clip_is_rejected_instead_of_falling_back(self):
        with ReactionBankFixture() as bank:
            bank.profiles['base'].pop('reactions')
            bank.write()
            with self.assertRaisesRegex(ValueError, 'requires actual hit_body, hit_head and hit_side'):
                generator.load_bank(bank.path)
        with ReactionBankFixture() as bank:
            bank.profiles['base']['reactions'].pop('hit_head')
            bank.write()
            with self.assertRaisesRegex(ValueError, 'requires actual hit_body, hit_head and hit_side'):
                generator.load_bank(bank.path)

    def test_reaction_signature_must_match_the_reviewed_prepared_animation(self):
        with ReactionBankFixture() as bank:
            bank.profiles['base']['reactions']['hit_body']['animation_semantics_sha256'] = '0' * 64
            bank.write()
            with self.assertRaisesRegex(ValueError, 'Reaction curve identity differs'):
                generator.load_bank(bank.path)

    def test_reaction_source_must_cover_the_unchanged_hit_playback_window(self):
        with ReactionBankFixture() as bank:
            clip = bank.profiles['base']['reactions']['hit_side']
            clip['source_range_seconds'][1] = 1.0
            clip['samples'][-1]['source_seconds'] = 1.0
            bank.write()
            with self.assertRaisesRegex(ValueError, 'does not cover the complete HIT playback'):
                generator.load_bank(bank.path)
        with ReactionBankFixture() as bank:
            bank.profiles['base']['reactions']['hit_body']['playback_range_seconds'][1] = .73
            bank.write()
            with self.assertRaisesRegex(ValueError, 'differs from the existing HIT clock'):
                generator.load_bank(bank.path)

    def test_reaction_samples_require_exact_endpoints_and_finite_anchors(self):
        with ReactionBankFixture() as bank:
            bank.profiles['base']['reactions']['hit_head']['samples'][-1]['source_seconds'] = 1.2
            bank.write()
            with self.assertRaisesRegex(ValueError, 'exact source endpoints'):
                generator.load_bank(bank.path)
        with ReactionBankFixture() as bank:
            bank.profiles['base']['reactions']['hit_head']['samples'][0]['head'][0] = float('nan')
            bank.write()
            with self.assertRaisesRegex(ValueError, 'Invalid anchor: head'):
                generator.load_bank(bank.path)

    def test_invalid_reaction_source_ranges_are_rejected(self):
        for invalid in (None, [], [.03], [-.1, 1.3], [1.3, .03], [.03, float('inf')], [.03, '1.3']):
            with self.subTest(source=invalid):
                profile = {'reactions': reaction_fixture()}
                reviewed = {'clip_semantic_signatures': {name: clip['animation_semantics_sha256']
                                                        for name, clip in profile['reactions'].items()}}
                profile['reactions']['hit_body']['source_range_seconds'] = invalid
                with self.assertRaisesRegex(ValueError, 'Reaction source range'):
                    generator.validate_reactions(profile, reviewed)

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
