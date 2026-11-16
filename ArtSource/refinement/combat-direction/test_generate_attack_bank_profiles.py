import copy
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import generate_attack_bank_profiles as generator


def generated_sample_factories(source):
    """Read numeric payloads independently of the generator's formatting helpers."""
    owners = {}
    for owner, body in re.findall(r'^private object (\w+) \{\n(.*?)^\}', source, flags=re.MULTILINE | re.DOTALL):
        methods = {}
        for name, numbers in re.findall(r'\bfun\s+(\w+)\(\)\s*:\s*List<AttackPoseSample>\s*=\s*'
                r'decodeAttackSamples\(doubleArrayOf\((.*?)\)\)', body, flags=re.DOTALL):
            methods[name] = [float(value.strip()) for value in numbers.split(',') if value.strip()]
        owners[owner] = methods
    return owners


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
        self.review = {'status': 'pending_root_review', 'binding': {'schema_version': 3}, 'characters': []}
        self.characters, self.profiles = [], {}
        source = json.loads((generator.DEFAULT_BANK / 'base_attack_profiles.json').read_text())
        runtime = generator.runtime_phase_nanos_from_enum()
        contracts = []
        for direction in generator.DIRECTIONS:
            markers = dict(zip(generator.PHASE_MARKERS, (0.0, .65, .90, 1.10, 1.75, 1.0)))
            if direction == 'OVERHEAD':
                markers.update(startup_end=5 / 6, active_end=31 / 30)
            contracts.append({'name': 'attack_' + direction.lower(), 'direction': direction,
                              **source['directions'][direction], 'phase_markers': markers,
                              'runtime_phase_nanos': runtime[direction]})
        self.review['binding']['attack_source'] = {'clips': contracts}
        # Keep real contract metadata; reduce only sample density to exact required keys.
        for cid in ('base', 'indigo', 'veteran'):
            model = self.path / (cid + '.glb')
            model.write_bytes(('fixture-model-' + cid).encode())
            profile = copy.deepcopy(source)
            profile.pop('phase_markers_seconds', None)
            profile.pop('phase_sample_times_seconds', None)
            profile['model_sha256'] = generator.sha256(model)
            profile['source_contract'].update(idle_loop_start_seconds=0.0, idle_loop_end_seconds=1.5,
                                              idle_loop_duration_seconds=1.5)
            for name, clip in profile['locomotion'].items():
                start = copy.deepcopy(source['locomotion']['idle']['samples'][0])
                end = copy.deepcopy(start)
                end['source_seconds'] = 1.5
                clip['samples'] = [start, end]
                clip['source_loop_seconds'] = [0.0, 1.5] if name == 'idle' else [1 / 3, 1.5]
                clip['source_loop_duration_seconds'] = 1.5 if name == 'idle' else 7 / 6
            for direction, clip in profile['attacks'].items():
                contract = next(row for row in contracts if row['direction'] == direction)
                clip['source_phase_seconds'] = [contract['phase_markers'][key] for key in generator.PHASE_MARKERS[:5]]
                clip['contact_source_seconds'] = contract['phase_markers']['contact']
                clip['runtime_phase_nanos'] = contract['runtime_phase_nanos'][:]
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
        self.review['binding_sha256'] = hashlib.sha256(json.dumps(
            self.review['binding'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
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


@contextmanager
def app_publication_fixture():
    with tempfile.TemporaryDirectory(prefix='typed-app-publication-test-') as temporary:
        repo = Path(temporary).resolve() / 'repo'
        repo.mkdir()
        output = repo / 'app/AttackBankProfileData.kt'
        output.parent.mkdir()
        output.write_text('unchanged app data')
        manifest = repo / 'ArtSource/tripo-warrior/motion_library.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{}')
        with patch.object(generator, 'REPO', repo), patch.object(generator, 'DEFAULT_OUTPUT', output):
            with ReactionBankFixture() as bank:
                yield bank, manifest, output


def approve_app_fixture(bank, manifest):
    bank.review['status'] = 'approved_for_development_integration'
    bank.review['player_weapon'] = {'file': 'fixture-dao.glb', 'sha256': '1' * 64}
    # Keep a complete real producer projection; fake model bytes below only
    # exercise publication identity, not asset generation or visual quality.
    inputs = json.loads((generator.DEFAULT_BANK.parent / 'motion_library.json').read_text())
    fixture_rows = {row['direction']: row for row in bank.review['binding']['attack_source']['clips']}
    inputs['attack_source'].pop('phase_markers', None)
    for row in inputs['attack_source']['clips']:
        row.update(copy.deepcopy(fixture_rows[row['direction']]))
    bank.review['binding'] = generator.production_binding(inputs)
    bank.write()
    approval = generator.REPO / 'ArtSource/tripo-warrior/root_approval.json'
    approval.write_text(json.dumps({'decision': 'approved', 'binding_sha256': bank.review['binding_sha256'],
                                   'characters': copy.deepcopy(bank.review['characters']),
                                   'player_weapon': copy.deepcopy(bank.review['player_weapon'])}))
    manifest.parent.mkdir(parents=True, exist_ok=True)
    inputs['production_review'] = {'source': approval.name, 'source_sha256': generator.sha256(approval)}
    manifest.write_text(json.dumps(inputs))
    return approval


def run_cli(bank, output=None, manifest=None, check=False):
    arguments = ['generate_attack_bank_profiles.py', '--bank', str(bank.path)]
    if output is not None:
        arguments += ['--output', str(output)]
    if manifest is not None:
        arguments += ['--manifest', str(manifest)]
    if check:
        arguments.append('--check')
    stdout = io.StringIO()
    with patch('sys.argv', arguments), redirect_stdout(stdout):
        generator.main()
    return stdout.getvalue()


class GenerateAttackBankProfilesTest(unittest.TestCase):
    def test_real_bank_factories_have_three_class_owners_and_preserve_every_double_bit(self):
        output = generator.generate(generator.DEFAULT_BANK)
        factories = generated_sample_factories(output)
        self.assertEqual(set(factories), {'BaseAttackSamples', 'IndigoAttackSamples', 'VeteranAttackSamples'})
        self.assertEqual(re.findall(r'^private fun (\w+)\(', output, flags=re.MULTILINE), ['decodeAttackSamples'])
        for character, profile, _ in generator.load_bank(generator.DEFAULT_BANK):
            owner = character['id'].title() + 'AttackSamples'
            clips = {direction.lower(): profile['attacks'][direction] for direction in generator.DIRECTIONS}
            clips.update(profile['locomotion'])
            clips.update({name.split('_')[0] + name.split('_')[1].title(): clip
                          for name, clip in profile['reactions'].items()})
            self.assertEqual(set(factories[owner]), set(clips))
            for method, clip in clips.items():
                expected = [value for sample in clip['samples'] for value in
                            [sample['source_seconds'], *[v for field in generator.FIELDS for v in sample[field]]]]
                actual = factories[owner][method]
                self.assertEqual(len(actual), len(clip['samples']) * 16)
                self.assertEqual(b''.join(struct.pack('>d', value) for value in actual),
                                 b''.join(struct.pack('>d', value) for value in expected), (owner, method))
            for direction in generator.DIRECTIONS:
                self.assertIn(f'samples = {owner}.{direction.lower()}(),', output)

    def test_grouping_keeps_signed_zero_adjacent_double_and_tiny_finite_values(self):
        with ReactionBankFixture() as bank:
            clip = bank.profiles['base']['reactions']['hit_body']
            clip['samples'][0]['head'][0] = -0.0
            clip['samples'][0]['body_top'][0] = 1.0000000000000002
            clip['samples'][-1]['blade_tip'][2] = 1e-300
            bank.write()
            actual = generated_sample_factories(generator.generate(bank.path))['BaseAttackSamples']['hitBody']
            self.assertEqual(struct.pack('>d', actual[1]), struct.pack('>d', -0.0))
            self.assertEqual(struct.pack('>d', actual[7]), struct.pack('>d', 1.0000000000000002))
            self.assertEqual(struct.pack('>d', actual[-1]), struct.pack('>d', 1e-300))

    def test_dynamic_idle_body_samples_survive_typed_generation_with_one_closed_loop(self):
        with ReactionBankFixture() as bank:
            for profile in bank.profiles.values():
                idle = profile['locomotion']['idle']['samples']
                middle = copy.deepcopy(idle[0])
                middle['source_seconds'] = .75
                middle['head'][2] += .002
                middle['body_top'][1] += .001
                idle.insert(1, middle)
            bank.write()
            rows = generator.load_bank(bank.path)
            output = generator.generate(bank.path)
            for _, profile, _ in rows:
                idle = profile['locomotion']['idle']['samples']
                self.assertNotEqual(idle[0]['head'], idle[1]['head'])
                self.assertEqual(idle[0]['head'], idle[-1]['head'])
                self.assertEqual(idle[0]['blade_base'], idle[1]['blade_base'])
            factories = generated_sample_factories(output)
            for methods in factories.values():
                self.assertEqual(methods['idle'][::16], [0.0, .75, 1.5])

    def test_idle_loop_must_close_and_cannot_keep_the_retired_walk_phase_domain(self):
        for change in ('endpoint', 'old_loop', 'duration', 'missing_clock', 'boolean_clock', 'boolean_loop'):
            with self.subTest(change=change), ReactionBankFixture() as bank:
                profile = bank.profiles['base']
                idle = profile['locomotion']['idle']
                if change == 'endpoint':
                    idle['samples'][-1]['head'][0] += .0001
                elif change == 'old_loop':
                    idle['source_loop_seconds'] = [1 / 3, 1.5]
                elif change == 'duration':
                    idle['source_loop_duration_seconds'] = 7 / 6
                elif change == 'boolean_clock':
                    profile['source_contract']['idle_loop_start_seconds'] = False
                elif change == 'boolean_loop':
                    idle['source_loop_seconds'][0] = False
                else:
                    profile['source_contract'].pop('idle_loop_duration_seconds')
                bank.write()
                with self.assertRaises(ValueError):
                    generator.load_bank(bank.path)

    def test_reviewed_per_direction_bank_generates_typed_source_phases_without_runtime_duplication(self):
        self.assertEqual(generator.REPO / 'ArtSource/tripo-warrior/library', generator.DEFAULT_BANK)
        with ReactionBankFixture() as bank:
            data = generator.load_bank(bank.path)
            self.assertEqual(len(data), 3)
            self.assertTrue(all(set(profile['reactions']) == set(generator.REACTIONS) for _, profile, _ in data))
            output = generator.generate(bank.path)
            self.assertEqual(output.count('sourcePhaseSeconds = listOf(0.0, 0.65, 0.8333333333333334, 1.0333333333333334, 1.75)'), 3)
            self.assertEqual(output.count('sourcePhaseSeconds = listOf(0.0, 0.65, 0.9, 1.1, 1.75)'), 6)
            self.assertNotIn('runtime_phase_nanos', output)
            self.assertNotIn('runtimePhaseNanos', output)

    def test_cue_changes_do_not_require_sample_keys_or_change_generated_geometry(self):
        with ReactionBankFixture() as bank:
            original = copy.deepcopy(bank.profiles)
            generated = []
            for cue in (.95, .955):
                bank.review['binding']['attack_source']['clips'][0]['phase_markers']['contact'] = cue
                for profile in bank.profiles.values():
                    attack = profile['attacks']['OVERHEAD']
                    attack['contact_source_seconds'] = cue
                    self.assertNotIn(cue, [sample['source_seconds'] for sample in attack['samples']])
                bank.write()
                generator.load_bank(bank.path)
                generated.append(generator.generate(bank.path))
            for cid, profile in bank.profiles.items():
                for direction, attack in profile['attacks'].items():
                    for field in ('samples', 'source_phase_seconds', 'runtime_phase_nanos'):
                        self.assertEqual(original[cid]['attacks'][direction][field], attack[field])
            # New cue metadata correctly changes its binding/profile identity digests.
            # Apart from those provenance fields, only the cue literal may differ.
            def payload(text):
                return '\n'.join(line for line in text.splitlines() if not any(
                    field in line for field in ('bindingSha256', 'profileSha256')))
            self.assertEqual(payload(generated[0]).replace('contactSourceSeconds = 0.95,', 'contactSourceSeconds = 0.955,'),
                             payload(generated[1]))

    def test_shared_binding_phase_contract_is_rejected_even_with_an_updated_review_hash(self):
        with ReactionBankFixture() as bank:
            bank.review['binding']['attack_source']['phase_markers'] = copy.deepcopy(
                bank.review['binding']['attack_source']['clips'][0]['phase_markers'])
            bank.write()
            with self.assertRaisesRegex(ValueError, 'shared phase_markers are retired'):
                generator.load_bank(bank.path)

    def test_shared_profile_phase_metadata_is_rejected_instead_of_used_as_fallback(self):
        for field in ('phase_markers_seconds', 'phase_sample_times_seconds'):
            with self.subTest(field=field), ReactionBankFixture() as bank:
                bank.profiles['base'][field] = {}
                bank.write()
                with self.assertRaisesRegex(ValueError, 'Shared profile phase metadata is retired'):
                    generator.load_bank(bank.path)

    def test_source_identity_must_match_the_reviewed_direction_row(self):
        with ReactionBankFixture() as bank:
            bank.profiles['base']['directions']['OVERHEAD']['source_sha256'] = '0' * 64
            bank.write()
            with self.assertRaisesRegex(ValueError, 'source/clip/direction differs'):
                generator.load_bank(bank.path)

    def test_each_profile_uses_its_direction_specific_phase_contract(self):
        with ReactionBankFixture() as bank:
            overhead = bank.profiles['base']['attacks']['OVERHEAD']
            overhead['source_phase_seconds'] = bank.profiles['base']['attacks']['LEFT']['source_phase_seconds'][:]
            bank.write()
            with self.assertRaisesRegex(ValueError, 'phase/contact markers differ from its reviewed direction'):
                generator.load_bank(bank.path)

    def test_profile_runtime_cannot_drift_from_the_reviewed_runtime(self):
        with ReactionBankFixture() as bank:
            bank.profiles['base']['attacks']['OVERHEAD']['runtime_phase_nanos'][1] += 1
            bank.write()
            with self.assertRaisesRegex(ValueError, 'runtime phases differ from its reviewed direction'):
                generator.load_bank(bank.path)

    def test_reviewed_runtime_cannot_drift_from_the_actual_kotlin_enum(self):
        with ReactionBankFixture() as bank:
            bank.review['binding']['attack_source']['clips'][0]['runtime_phase_nanos'][1] += 1
            bank.write()
            with self.assertRaisesRegex(ValueError, 'runtime phases differ from the actual AttackDirection enum'):
                generator.load_bank(bank.path)

    def test_runtime_validation_reads_enum_changes_instead_of_a_second_python_duration_table(self):
        with ReactionBankFixture() as bank:
            original = generator.ENEMY_COMBAT_SOURCE.read_text()
            modified, count = re.subn(r'(\bOVERHEAD\s*\(\s*)([0-9][0-9_]*L)',
                lambda match: match[1] + str(int(match[2][:-1].replace('_', '')) + 1) + 'L', original, count=1)
            self.assertEqual(1, count)
            enum = bank.path / 'EnemyCombatStateMachine.kt'
            enum.write_text(modified)
            with patch.object(generator, 'ENEMY_COMBAT_SOURCE', enum):
                with self.assertRaisesRegex(ValueError, 'runtime phases differ from the actual AttackDirection enum'):
                    generator.load_bank(bank.path)

    def test_runtime_requires_four_positive_long_integers(self):
        valid = generator.runtime_phase_nanos_from_enum()['OVERHEAD']
        for invalid in (None, valid[:3], valid + [1], [True, *valid[1:]], [0, *valid[1:]],
                        [-1, *valid[1:]], [float(valid[0]), *valid[1:]], [2**63, *valid[1:]]):
            with self.subTest(values=invalid):
                with self.assertRaisesRegex(ValueError, 'four positive integer Long'):
                    generator.validate_runtime_phase_nanos(invalid)

    def test_enum_durations_require_explicit_four_long_literals_without_expression_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            enum = Path(temporary) / 'EnemyCombatStateMachine.kt'
            original = generator.ENEMY_COMBAT_SOURCE.read_text()
            modified, count = re.subn(r'(\bOVERHEAD\s*\(\s*)([0-9][0-9_]*L)', r'\g<1>1L * NANOS_PER_MILLISECOND', original, count=1)
            self.assertEqual(1, count)
            enum.write_text(modified)
            with patch.object(generator, 'ENEMY_COMBAT_SOURCE', enum):
                with self.assertRaisesRegex(ValueError, 'four explicit Long literals'):
                    generator.runtime_phase_nanos_from_enum()

    def test_reviewed_phase_markers_require_exact_keys_finite_values_and_order(self):
        for change in ('missing', 'extra', 'boolean', 'infinite', 'reversed', 'contact_boundary'):
            with self.subTest(change=change), ReactionBankFixture() as bank:
                phases = bank.review['binding']['attack_source']['clips'][0]['phase_markers']
                if change == 'missing':
                    phases.pop('contact')
                elif change == 'extra':
                    phases['damage_end'] = phases['active_end']
                elif change == 'boolean':
                    phases['start'] = False
                elif change == 'infinite':
                    phases['active_end'] = float('inf')
                elif change == 'reversed':
                    phases['startup_end'] = phases['preparation_end']
                else:
                    phases['contact'] = phases['active_end']
                bank.write()
                with self.assertRaisesRegex(ValueError, 'phase markers|phase/contact order'):
                    generator.load_bank(bank.path)

    def test_missing_or_duplicate_reviewed_direction_is_rejected(self):
        with ReactionBankFixture() as bank:
            clips = bank.review['binding']['attack_source']['clips']
            clips[-1] = copy.deepcopy(clips[0])
            bank.write()
            with self.assertRaisesRegex(ValueError, 'exactly three direction-specific rows'):
                generator.load_bank(bank.path)

    def test_binding_identity_gate_precedes_per_direction_export(self):
        with ReactionBankFixture() as bank:
            bank.review['binding']['attack_source']['clips'][0]['source_sha256'] = '0' * 64
            (bank.path / 'production_review_request.json').write_text(json.dumps(bank.review))
            with self.assertRaisesRegex(ValueError, 'binding identity differs'):
                generator.load_bank(bank.path)

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
                    method = title[0].lower() + title[1:]
                    self.assertIn(f'{field} = PoseClipProfile("{name}", {cid.title()}AttackSamples.{method}()),', output)
                    self.assertIn(f'    fun {method}(): List<AttackPoseSample> = decodeAttackSamples(', output)

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
        with ReactionBankFixture() as bank:
            with patch.object(generator, 'sha256', return_value='0' * 64):
                with self.assertRaisesRegex(ValueError, 'Profile SHA differs'):
                    generator.load_bank(bank.path)

    def test_model_identity_drift_is_rejected_before_export(self):
        actual_sha256 = generator.sha256
        with ReactionBankFixture() as bank:
            with patch.object(generator, 'sha256', side_effect=lambda path: '0' * 64 if path.suffix == '.glb' else actual_sha256(path)):
                with self.assertRaisesRegex(ValueError, 'Prepared model identity differs'):
                    generator.load_bank(bank.path)

    def test_old_two_step_or_misaligned_contact_contract_is_rejected(self):
        with ReactionBankFixture() as bank:
            profile = copy.deepcopy(bank.profiles['base'])
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


class AppPublicationTest(unittest.TestCase):
    def test_pending_default_and_explicit_app_outputs_reject_before_generation(self):
        for explicit in (False, True):
            with self.subTest(explicit=explicit), app_publication_fixture() as (bank, _, output):
                with patch.object(generator, 'generate', side_effect=AssertionError('must reject before model/profile reads')):
                    with self.assertRaisesRegex(ValueError, 'approved_for_development_integration bank status'):
                        run_cli(bank, output if explicit else None)
                self.assertEqual('unchanged app data', output.read_text())

    def test_explicit_private_output_accepts_pending_without_a_manifest(self):
        with app_publication_fixture() as (bank, manifest, app_output):
            manifest.unlink()
            output = generator.REPO / 'analysis.kt'
            run_cli(bank, output)
            self.assertEqual(generator.generate(bank.path), output.read_text())
            self.assertEqual('unchanged app data', app_output.read_text())

    def test_matching_existing_root_receipt_allows_the_default_app_destination(self):
        with app_publication_fixture() as (bank, manifest, output):
            approve_app_fixture(bank, manifest)
            run_cli(bank)
            self.assertEqual(generator.generate(bank.path), output.read_text())

    def test_only_current_manifest_source_target_or_texture_drift_rejects_stale_receipt(self):
        for drift in ('overhead_raw_path', 'overhead_raw_sha', 'target', 'texture'):
            with self.subTest(drift=drift), app_publication_fixture() as (bank, manifest, output):
                approve_app_fixture(bank, manifest)
                current = json.loads(manifest.read_text())
                if drift.startswith('overhead_raw_'):
                    row = next(row for row in current['attack_source']['clips'] if row['direction'] == 'OVERHEAD')
                    row['source' if drift.endswith('_path') else 'source_sha256'] = 'unapproved-b.glb' if drift.endswith('_path') else 'b' * 64
                elif drift == 'target':
                    current['characters'][0]['source_sha256'] = 'b' * 64
                else:
                    current['runtime_texture_encoding']['settings']['uastc_quality'] = 1
                manifest.write_text(json.dumps(current))
                with patch.object(generator, 'generate', side_effect=AssertionError('reject before generation')):
                    with self.assertRaisesRegex(ValueError, 'Current manifest production binding differs'):
                        run_cli(bank)
                self.assertEqual('unchanged app data', output.read_text())

    def test_incomplete_manifest_with_unchanged_approval_cannot_publish(self):
        with app_publication_fixture() as (bank, manifest, output):
            approve_app_fixture(bank, manifest)
            data = json.loads(manifest.read_text())
            del data['motion_source']
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'lacks complete production binding'):
                run_cli(bank)
            self.assertEqual('unchanged app data', output.read_text())

    def test_current_projection_preserves_the_reviewed_formal_binding_without_blender_import(self):
        # Use the repository's formal receipt, not a developer's private candidate.
        # The frozen request checks that policies and all projected fields survive
        # this extraction even when Root selects a newer current RAW in parallel.
        request = json.loads((generator.DEFAULT_BANK / 'production_review_request.json').read_text())
        manifest = {key: copy.deepcopy(value) for key, value in request['binding'].items()
                    if key not in ('schema_version', 'hand_policy', 'canonical_root_grounding')}
        projected = json.loads(json.dumps(generator.production_binding(manifest)))
        self.assertEqual(request['binding'], projected)
        self.assertEqual(request['binding_sha256'], generator.canonical_hash(projected))

    def test_generator_imports_in_a_python_process_without_blender_packages(self):
        script = Path(generator.__file__).resolve()
        code = """import importlib.util, runpy, sys
assert importlib.util.find_spec('bpy') is None
assert importlib.util.find_spec('mathutils') is None
runpy.run_path(sys.argv[1], run_name='pure_generator_import')
assert 'bpy' not in sys.modules and 'mathutils' not in sys.modules
print('PURE_GENERATOR_IMPORT_OK')
"""
        process = subprocess.run([sys.executable, '-I', '-c', code, str(script)], capture_output=True, text=True, timeout=15)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertIn('PURE_GENERATOR_IMPORT_OK', process.stdout)

    def test_explicit_manifest_resolves_review_source_from_the_producer_directory(self):
        with app_publication_fixture() as (bank, _, output):
            manifest = generator.REPO / 'configuration/custom-manifest.json'
            approval = approve_app_fixture(bank, manifest)
            (manifest.parent / approval.name).write_text('{"decision":"rejected"}')
            run_cli(bank, output, manifest)
            self.assertEqual(generator.generate(bank.path), output.read_text())

    def test_an_approved_status_without_the_root_manifest_receipt_cannot_publish(self):
        for missing in ('manifest', 'receipt'):
            with self.subTest(missing=missing), app_publication_fixture() as (bank, manifest, output):
                bank.review['status'] = 'approved_for_development_integration'
                bank.write()
                if missing == 'manifest':
                    manifest.unlink()
                    expected = FileNotFoundError
                else:
                    expected = ValueError
                with self.assertRaises(expected):
                    run_cli(bank)
                self.assertEqual('unchanged app data', output.read_text())

    def test_stale_or_mismatching_root_receipts_cannot_publish(self):
        for drift in ('file_hash', 'decision', 'binding', 'characters', 'player_weapon'):
            with self.subTest(drift=drift), app_publication_fixture() as (bank, manifest, output):
                approval = approve_app_fixture(bank, manifest)
                review = json.loads(approval.read_text())
                if drift == 'file_hash':
                    approval.write_text(approval.read_text() + '\n')
                    expected = 'file hash changed'
                else:
                    if drift == 'decision':
                        review['decision'] = 'rejected'
                        expected = 'does not approve the current sources'
                    elif drift == 'binding':
                        review['binding_sha256'] = '0' * 64
                        expected = 'does not approve the current sources'
                    elif drift == 'characters':
                        review['characters'] = []
                        expected = 'differs from final outputs'
                    else:
                        review['player_weapon'] = {}
                        expected = 'differs from the encoded player weapon'
                    approval.write_text(json.dumps(review))
                    data = json.loads(manifest.read_text())
                    data['production_review']['source_sha256'] = generator.sha256(approval)
                    manifest.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, expected):
                    run_cli(bank)
                self.assertEqual('unchanged app data', output.read_text())

    def test_old_approval_does_not_authorize_a_new_valid_binding(self):
        with app_publication_fixture() as (bank, manifest, output):
            approve_app_fixture(bank, manifest)
            bank.review['binding']['attack_source']['clips'][0]['phase_markers']['contact'] = .955
            for profile in bank.profiles.values():
                profile['attacks']['OVERHEAD']['contact_source_seconds'] = .955
            bank.write()
            inputs = json.loads(manifest.read_text())
            inputs['attack_source']['clips'][0]['phase_markers']['contact'] = .955
            manifest.write_text(json.dumps(inputs))
            with self.assertRaisesRegex(ValueError, 'does not approve the current sources'):
                run_cli(bank)
            self.assertEqual('unchanged app data', output.read_text())

    def test_resolved_app_paths_traversal_and_symlink_routes_all_require_approval(self):
        for route in ('directory', 'traversal', 'symlink_to_app', 'symlink_file'):
            with self.subTest(route=route), app_publication_fixture() as (bank, _, output):
                if route == 'directory':
                    destination = generator.REPO / 'app'
                elif route == 'traversal':
                    private = generator.REPO / 'private'
                    private.mkdir()
                    destination = private / '../app' / output.name
                elif route == 'symlink_to_app':
                    alias = generator.REPO / 'app-alias'
                    alias.symlink_to(output.parent, target_is_directory=True)
                    destination = alias / output.name
                else:
                    destination = generator.REPO / 'private.kt'
                    destination.symlink_to(output)
                with patch.object(generator, 'generate', side_effect=AssertionError('must reject before generation')):
                    with self.assertRaisesRegex(ValueError, 'approved_for_development_integration bank status'):
                        run_cli(bank, destination)
                self.assertEqual('unchanged app data', output.read_text())

    def test_paths_resolving_outside_app_allow_private_pending_analysis(self):
        for route in ('traversal_out', 'symlink_out'):
            with self.subTest(route=route), app_publication_fixture() as (bank, manifest, output):
                manifest.unlink()
                private_output = generator.REPO / 'analysis.kt'
                if route == 'traversal_out':
                    destination = output.parent / '../analysis.kt'
                else:
                    destination = output.parent / 'analysis-link.kt'
                    destination.symlink_to(private_output)
                run_cli(bank, destination)
                self.assertEqual(generator.generate(bank.path), private_output.read_text())
                self.assertEqual('unchanged app data', output.read_text())

    def test_relative_app_output_is_protected_after_resolution(self):
        with app_publication_fixture() as (bank, _, output):
            previous = Path.cwd()
            try:
                os.chdir(generator.REPO)
                with self.assertRaisesRegex(ValueError, 'approved_for_development_integration bank status'):
                    run_cli(bank, Path('app') / output.name)
            finally:
                os.chdir(previous)
            self.assertEqual('unchanged app data', output.read_text())

    def test_check_is_read_only_and_needs_no_approval_but_still_validates_the_bank(self):
        with app_publication_fixture() as (bank, manifest, output):
            manifest.unlink()
            content = generator.generate(bank.path)
            output.write_text(content)
            before = output.stat().st_mtime_ns
            with patch.object(generator, 'validate_app_publication', side_effect=AssertionError('check must not require publication approval')):
                run_cli(bank, check=True)
            self.assertEqual(before, output.stat().st_mtime_ns)
            self.assertEqual(content, output.read_text())
            profile = bank.path / bank.characters[0]['attack_profiles']['file']
            profile.write_text(profile.read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'Profile SHA differs'):
                run_cli(bank, check=True)
            self.assertEqual(content, output.read_text())

    def test_matching_approval_does_not_bypass_bank_identity_validation(self):
        with app_publication_fixture() as (bank, manifest, output):
            approve_app_fixture(bank, manifest)
            profile = bank.path / bank.characters[0]['attack_profiles']['file']
            profile.write_text(profile.read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'Profile SHA differs'):
                run_cli(bank)
            self.assertEqual('unchanged app data', output.read_text())


if __name__ == '__main__':
    unittest.main()
