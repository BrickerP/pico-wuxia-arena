"""Pure offline synthetic checks for attack anchor export, run with Blender Python."""

import copy
import importlib.util
import json
import math
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attack_profiles import export_attack_profiles, float32, locomotion_source_contract, sample_track, hierarchy, pose_world


BANK = {'OVERHEAD': 'attack_overhead', 'LEFT': 'attack_left', 'RIGHT': 'attack_right'}


def typed_generator():
    path = Path(__file__).resolve().parents[1] / 'refinement/combat-direction/generate_attack_bank_profiles.py'
    spec = importlib.util.spec_from_file_location('attack_runtime_contract_fixture', path)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    return generator


def attack_contracts():
    generator = typed_generator()
    runtime = generator.runtime_phase_nanos_from_enum()
    return {clip: {
        'phase_markers': {'start': 0.0, 'preparation_end': .65,
                          'startup_end': 5 / 6 if direction == 'OVERHEAD' else .9,
                          'active_end': 31 / 30 if direction == 'OVERHEAD' else 1.1,
                          'recovery_end': 1.75, 'contact': 1.0},
        'runtime_phase_nanos': runtime[direction],
    } for direction, clip in BANK.items()}


def actor():
    document = {
        'scene': 0, 'scenes': [{'nodes': [0]}],
        'nodes': [
            {'name': 'TripoWarrior_Root', 'children': [1]},
            {'name': 'TripoBody_Root', 'scale': [2, 2, 2], 'children': [2]},
            {'name': 'Hip', 'translation': [0, .45, 0], 'children': [3]},
            {'name': 'Spine02', 'translation': [0, .15, 0], 'children': [4, 5]},
            {'name': 'Head', 'translation': [0, .20, 0]},
            {'name': 'R_Hand', 'translation': [.2, 0, 0], 'children': [6]},
            {'name': 'HandGrip_R', 'translation': [0, .01, .05], 'children': [7]},
            {'name': 'Weapon_Root', 'translation': [0, -.05, 0], 'children': [8, 9]},
            {'name': 'Blade_Base', 'translation': [0, .10, 0]},
            {'name': 'Blade_Tip', 'translation': [0, .45, 0]},
        ],
        'skins': [{'joints': [2, 3, 4, 5]}], 'buffers': [{'byteLength': 32}],
        'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 8},
                        {'buffer': 0, 'byteOffset': 8, 'byteLength': 24}],
        'accessors': [{'bufferView': 0, 'componentType': 5126, 'type': 'SCALAR', 'count': 2},
                      {'bufferView': 1, 'componentType': 5126, 'type': 'VEC3', 'count': 2}],
        'animations': [{'name': name, 'samplers': [{'input': 0, 'output': 1}],
                        'channels': [{'sampler': 0, 'target': {'node': 5, 'path': 'translation'}}]}
                       for name in [*BANK.values(), 'hit_body', 'hit_head', 'hit_side', 'idle', 'walk']],
    }
    binary = struct.pack('<8f', 0, 1.75, .2, 0, 0, .4, 0, 0)
    def append(rows, kind, component=5126):
        nonlocal binary
        formats = {5121: 'B', 5126: 'f'}
        width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[kind]
        view = len(document['bufferViews'])
        raw = b''.join(struct.pack('<' + formats[component] * width, *row) for row in rows)
        document['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(raw)})
        binary += raw
        result = len(document['accessors'])
        document['accessors'].append({'bufferView': view, 'componentType': component,
                                      'type': kind, 'count': len(rows)})
        document['buffers'][0]['byteLength'] = len(binary)
        return result

    idle_times = append([(0,), (1.5,)], 'SCALAR')
    for animation in document['animations'][-2:]:
        animation['samplers'][0]['input'] = idle_times
    positions = [(.15, 0, -.05), (.25, 0, .05), (.2, .1, 0),
                 (-.1, -.1, -.1), (.1, -.1, .1), (0, 0, 0),
                 (-.1, 0, -.1), (.1, 0, .1), (0, .1, 0)]
    position = append(positions, 'VEC3')
    palettes = append([(index, 0, 0, 0) for index in [2] * 3 + [0] * 3 + [1] * 3], 'VEC4', 5121)
    weights = append([(1, 0, 0, 0)] * 9, 'VEC4')
    inverse_bind = append([tuple(1 if row == column else 0 for column in range(4) for row in range(4))] * 4, 'MAT4')
    document['skins'][0]['inverseBindMatrices'] = inverse_bind
    document['meshes'] = [{'primitives': [{'attributes': {'POSITION': position, 'JOINTS_0': palettes,
                                                         'WEIGHTS_0': weights}}],
                           'extras': {'body_primitive_indices': [0], 'weapon_primitive_indices': []}}]
    document['nodes'][0]['children'].append(len(document['nodes']))
    document['nodes'].append({'name': 'TripoBody_Mesh', 'mesh': 0, 'skin': 0})
    return document, binary


def frozen_contract():
    result = json.loads((Path(__file__).resolve().parents[1] /
                         'refinement/hand-poses/attack-keyposes/stage10/candidate/locked_locomotion_inputs.json').read_text())
    idle = next(row for row in result['profiles'] if row['clip_alias'] == 'idle')
    idle['source_loop_seconds'] = [0, 1.5]
    idle['source_loop_duration_seconds'] = 1.5
    return result


def coverage_contract():
    return {'space': 'prepared actor root',
            'source_profile': {'path': 'test/prior_profile.json', 'sha256': '1' * 64, 'model_sha256': '2' * 64},
            'idle_centres_metres': {'body_bottom': [0, .55, 0], 'body_top': [0, 1.4, 0]},
            'idle_reference': {'hip': [0, .9, 0], 'spine02': [0, 1.2, 0]}}


class AttackProfileTests(unittest.TestCase):
    def test_constant_nearly_unit_linear_Q_has_identical_first_middle_last_world_without_raw_edits(self):
        document, _ = actor()
        q = tuple(value * 1.000001 for value in (.2, .3, .4, math.sqrt(.71)))
        tracks = {(3, 'rotation'): ([0.0, .75, 1.5], [q, q, q], 'LINEAR')}
        original = copy.deepcopy(tracks)
        _, parents, order = hierarchy(document)
        worlds = [pose_world(document, tracks, time, parents, order) for time in (0, .375, .75, 1.125, 1.5)]
        for world in worlds[1:]:
            for index in world:
                self.assertEqual(world[index], worlds[0][index])
        self.assertEqual(tracks, original)

    def test_dynamic_unit_Q_keeps_its_short_arc_interpolation(self):
        track = ([0.0, 1.0], [(0, 0, 0, 1), (0, 0, math.sqrt(.5), math.sqrt(.5))], 'LINEAR')
        halfway = sample_track(track, .5, True)
        self.assertAlmostEqual(halfway[2], math.sin(math.pi / 8), places=6)
        self.assertAlmostEqual(halfway[3], math.cos(math.pi / 8), places=6)
        self.assertNotEqual(halfway, sample_track(track, 0, True))
        self.assertNotEqual(halfway, sample_track(track, 1, True))

    def test_dynamic_nearly_unit_closed_Q_uses_exact_stored_keys_and_closes_all_world_matrices(self):
        document, _ = actor()
        start = tuple(float32(value * 1.000001) for value in (.2, .3, .4, math.sqrt(.71)))
        middle = tuple(float32(value * 1.000002) for value in (.201, .299, .401, math.sqrt(1 - .201**2 - .299**2 - .401**2)))
        curve = ([0.0, .75, 1.5], [start, middle, start], 'LINEAR')
        original = copy.deepcopy(curve)
        self.assertEqual(sample_track(curve, 0, True), sample_track(curve, 1.5, True))
        for time, value in zip(curve[0], curve[1]):
            constant = ([0.0, 1.5], [value, value], 'LINEAR')
            self.assertEqual(sample_track(curve, time, True), sample_track(constant, 0, True))
        tracks = {(3, 'rotation'): curve}
        _, parents, order = hierarchy(document)
        first = pose_world(document, tracks, 0, parents, order)
        last = pose_world(document, tracks, 1.5, parents, order)
        for index in first:
            self.assertEqual(first[index], last[index])
        self.assertNotEqual(pose_world(document, tracks, .75, parents, order)[4], first[4])
        self.assertEqual(curve, original)

    def test_contact_cue_is_metadata_without_resampling_geometry_or_the_phase_clock(self):
        document, binary = actor()
        original_contracts = attack_contracts()
        original = export_attack_profiles(document, binary, BANK, original_contracts, frozen_contract(), coverage_contract())
        generator = typed_generator()
        for cue in (.95, .955):
            contracts = copy.deepcopy(original_contracts)
            for row in contracts.values():
                row['phase_markers']['contact'] = cue
            result = export_attack_profiles(document, binary, BANK, contracts, frozen_contract(), coverage_contract())
            binding_rows = []
            for direction, clip in BANK.items():
                binding_rows.append({'name': clip, 'direction': direction, 'incoming_guard_side': direction,
                    'actor_travel_side': 'DOWN' if direction == 'OVERHEAD' else direction,
                    'source_sha256': '1' * 64, **contracts[clip]})
            bound = generator.validate_attack_contracts({'attack_source': {'clips': binding_rows}})
            for direction, clip in BANK.items():
                profile = result['attacks'][direction]
                baseline = original['attacks'][direction]
                self.assertEqual(profile['samples'], baseline['samples'])
                self.assertEqual(profile['source_phase_seconds'], baseline['source_phase_seconds'])
                self.assertEqual(profile['runtime_phase_nanos'], baseline['runtime_phase_nanos'])
                self.assertEqual(profile['contact_source_seconds'], cue)
                metadata = {key: bound[direction][key] for key in
                            ('incoming_guard_side', 'actor_travel_side', 'source_sha256')}
                generator.validate_attack_profile(profile, metadata, bound[direction])
                if cue == .955:
                    self.assertNotIn(float32(cue), [sample['source_seconds'] for sample in profile['samples']])

    def test_each_exported_direction_uses_only_its_bound_phase_and_runtime_contract(self):
        document, binary = actor()
        contracts = attack_contracts()
        original = copy.deepcopy(contracts)
        result = export_attack_profiles(document, binary, BANK, contracts, frozen_contract(), coverage_contract())
        self.assertEqual(contracts, original)
        self.assertNotIn('phase_markers_seconds', result)
        self.assertNotIn('phase_sample_times_seconds', result)
        names = ('start', 'preparation_end', 'startup_end', 'active_end', 'recovery_end')
        for direction, clip in BANK.items():
            profile = result['attacks'][direction]
            markers = contracts[clip]['phase_markers']
            self.assertEqual(profile['source_phase_seconds'], [markers[name] for name in names])
            self.assertEqual(profile['contact_source_seconds'], markers['contact'])
            self.assertEqual(profile['runtime_phase_nanos'], contracts[clip]['runtime_phase_nanos'])
            for name, marker in markers.items():
                if name == 'contact':
                    continue
                self.assertIn(float32(marker), [sample['source_seconds'] for sample in profile['samples']])
        self.assertNotEqual(result['attacks']['OVERHEAD']['source_phase_seconds'],
                            result['attacks']['LEFT']['source_phase_seconds'])

    def test_missing_direction_clock_and_invalid_phase_and_runtime_contracts_are_rejected(self):
        document, binary = actor()
        invalid = []
        missing = attack_contracts()
        del missing['attack_left']
        invalid.append(missing)
        for field, value in [('phase_markers', {}), ('runtime_phase_nanos', [1, 2, 3]),
                             ('runtime_phase_nanos', [False, 1, 1, 1]),
                             ('runtime_phase_nanos', [1.5, 1, 1, 1]),
                             ('runtime_phase_nanos', [1, -1, 1, 1]),
                             ('runtime_phase_nanos', [1 << 63, 1, 1, 1])]:
            contracts = attack_contracts()
            contracts['attack_overhead'][field] = value
            invalid.append(contracts)
        for field, value in [('startup_end', float('nan')), ('startup_end', .65),
                             ('contact', 31 / 30), ('start', False), ('recovery_end', 2.0)]:
            contracts = attack_contracts()
            contracts['attack_overhead']['phase_markers'][field] = value
            invalid.append(contracts)
        for contracts in invalid:
            with self.assertRaises(ValueError):
                export_attack_profiles(document, binary, BANK, contracts, frozen_contract(), coverage_contract())

    def test_final_hierarchy_drives_mounted_blade_and_normalized_body(self):
        document, binary = actor()
        original = copy.deepcopy(document)
        result = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        self.assertEqual(document, original)
        self.assertEqual(result['axes'], {'up': '+Y', 'forward': '+Z', 'actor_left': '+X'})
        self.assertEqual(set(result['attacks']), set(BANK))
        for profile in result['attacks'].values():
            self.assertEqual(len(profile['samples']), 106)
            self.assertTrue(all(a['time_seconds'] < b['time_seconds']
                                for a, b in zip(profile['samples'], profile['samples'][1:])))
            contact = next(sample for sample in profile['samples'] if sample['time_seconds'] == 1.0)
            self.assertAlmostEqual(contact['head'][0], .4, places=6)
            self.assertAlmostEqual(contact['head'][1], 1.7, places=6)
            self.assertAlmostEqual(contact['body_bottom'][1], .55, places=6)
            self.assertAlmostEqual(contact['body_top'][1], 1.4, places=6)
            self.assertAlmostEqual(contact['blade_base'][0], .4 + .4 / 1.75, places=6)
            self.assertAlmostEqual(contact['blade_base'][1], 1.32, places=6)
            self.assertAlmostEqual(contact['blade_tip'][1], 2.02, places=6)
            self.assertEqual(contact['torso_lower'], contact['hip'])
            self.assertEqual(contact['torso_upper'], contact['spine02'])
            markers = attack_contracts()[profile['clip']]['phase_markers']
            for name, marker in markers.items():
                if name == 'contact':
                    continue
                self.assertIn(float32(marker), [sample['time_seconds'] for sample in profile['samples']])
        json.dumps(result, allow_nan=False)

    def test_schema3_locomotion_uses_one_actual_mesh_calibration_and_exact_phase_samples(self):
        document, binary = actor()
        result = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        self.assertEqual(result['schema_version'], 3)
        self.assertEqual(set(result['locomotion']), {'idle', 'walk'})
        contract = result['source_contract']
        self.assertEqual(contract['steps_per_loop'], 6)
        self.assertEqual(contract['loop_duration_seconds'], 7 / 6)
        self.assertEqual(contract['idle_loop_start_seconds'], 0)
        self.assertEqual(contract['idle_loop_duration_seconds'], 1.5)
        self.assertEqual(result['locomotion']['idle']['source_loop_seconds'], [0, 1.5])
        self.assertEqual(contract['distance_per_step_metres'], 1.45 / 6)
        bounds = result['proxy_calibration']['measurement']['anatomical_bounds_metres']
        self.assertEqual(bounds['head']['vertex_count'], 3)
        reference = result['locomotion']['idle']['samples'][0]
        for profile in [*result['locomotion'].values(), *result['attacks'].values()]:
            for field in ('head', 'body_bottom', 'body_top'):
                self.assertEqual(profile['samples'][0][field], reference[field])
        for name, profile in result['locomotion'].items():
            times = [row['source_seconds'] for row in profile['samples']]
            if name == 'walk':
                for phase in contract['contact_source_seconds']:
                    self.assertIn(float32(phase), times)
            self.assertEqual(times[0], 0)
            self.assertEqual(times[-1], 1.5)

    def test_dynamic_idle_exports_actual_body_and_blade_on_the_same_source_time(self):
        document, binary = actor()
        packed = bytearray(binary)

        def append(rows, kind):
            packed.extend(b'\0' * (-len(packed) % 4))
            start = len(packed)
            for row in rows:
                packed.extend(struct.pack('<' + 'f' * len(row), *row))
            view = len(document['bufferViews'])
            document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(packed) - start})
            index = len(document['accessors'])
            document['accessors'].append({'bufferView': view, 'componentType': 5126,
                                          'type': kind, 'count': len(rows)})
            return index

        idle = next(row for row in document['animations'] if row['name'] == 'idle')
        idle['channels'][0]['target']['node'] = 3
        idle['samplers'][0] = {'input': append([(0,), (.75,), (1.5,)], 'SCALAR'),
                               'output': append([(0, .15, 0), (0, .152, 0), (0, .15, 0)], 'VEC3'),
                               'interpolation': 'LINEAR'}
        document['buffers'][0]['byteLength'] = len(packed)
        result = export_attack_profiles(document, bytes(packed), BANK, attack_contracts(), frozen_contract(), coverage_contract())
        samples = result['locomotion']['idle']['samples']
        start, end = samples[0], samples[-1]
        middle = next(row for row in samples if row['source_seconds'] == .75)
        for field in ('head', 'body_bottom', 'body_top', 'blade_base', 'blade_tip'):
            self.assertEqual(start[field], end[field])
        for field in ('head', 'body_top', 'blade_base', 'blade_tip'):
            self.assertAlmostEqual(middle[field][1] - start[field][1], .004, places=6)
        self.assertEqual(middle['body_bottom'], start['body_bottom'])
        self.assertEqual(result['locomotion']['idle']['source_loop_seconds'], [0, 1.5])

    def test_reaction_samples_follow_actual_hurt_bones_with_the_same_calibration(self):
        document, binary = actor()
        animation = next(row for row in document['animations'] if row['name'] == 'hit_body')
        animation['channels'][0]['target']['node'] = 3
        result = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        self.assertEqual(set(result['reactions']), {'hit_body', 'hit_head', 'hit_side'})
        for name, clip in result['reactions'].items():
            self.assertEqual(clip['clip'], name)
            self.assertEqual(clip['playback_range_seconds'], [.05, 1.18 if name == 'hit_side' else .72])
            self.assertEqual(clip['source_range_seconds'], [0.0, 1.75])
            times = [row['source_seconds'] for row in clip['samples']]
            self.assertEqual(times[0], 0.0)
            self.assertEqual(times[-1], 1.75)
            self.assertIn(float32(.05), times)
            self.assertIn(float32(clip['playback_range_seconds'][1]), times)
        hurt = result['reactions']['hit_body']['samples']
        first, last = hurt[0], hurt[-1]
        self.assertGreater(last['head'][0] - first['head'][0], .39)
        self.assertGreater(last['body_top'][0] - first['body_top'][0], .39)
        self.assertEqual(first['body_bottom'], last['body_bottom'])
        self.assertNotEqual(first['head'], result['locomotion']['idle']['samples'][0]['head'])

    def test_missing_or_too_short_reaction_source_fails_instead_of_exporting_standing(self):
        document, binary = actor()
        document['animations'] = [row for row in document['animations'] if row['name'] != 'hit_head']
        with self.assertRaisesRegex(ValueError, 'reaction clip is absent.*hit_head'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        document, binary = actor()
        animation = next(row for row in document['animations'] if row['name'] == 'hit_side')
        # Reuse an existing accessor but make its second source time unable to cover 1.18s.
        original_view = document['bufferViews'][document['accessors'][0]['bufferView']]
        changed = bytearray(binary)
        struct.pack_into('<f', changed, original_view['byteOffset'] + 4, .7)
        # Keep the three attacks valid by removing their use of the shortened time accessor.
        for row in document['animations']:
            if row['name'] != 'hit_side' and row['samplers'][0]['input'] == 0:
                row['samplers'][0]['input'] = document['animations'][-1]['samplers'][0]['input']
        # The isolated reaction exporter reaches the missing-window guard without the attack-range guard.
        from attack_profiles import hierarchy, landmark_indices, export_reaction_profiles
        from mathutils import Vector
        root, parents, order = hierarchy(document)
        landmarks = landmark_indices(document, root, parents)
        with self.assertRaisesRegex(ValueError, 'reaction source does not cover.*hit_side'):
            export_reaction_profiles(document, bytes(changed), root, parents, order, landmarks,
                {'head': Vector((0, 0, 0)), 'body_bottom': Vector((0, 0, 0)), 'body_top': Vector((0, 0, 0))})

    def test_final_mesh_change_moves_proxy_without_editing_constants(self):
        document, binary = actor()
        original = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        accessor = document['meshes'][0]['primitives'][0]['attributes']['POSITION']
        view = document['bufferViews'][document['accessors'][accessor]['bufferView']]
        changed = bytearray(binary)
        for vertex in range(3):
            offset = view['byteOffset'] + vertex * 12
            x = struct.unpack_from('<f', changed, offset)[0]
            struct.pack_into('<f', changed, offset, x + .15)
        updated = export_attack_profiles(document, bytes(changed), BANK, attack_contracts(), frozen_contract(), coverage_contract())
        self.assertAlmostEqual(updated['proxy_calibration']['idle_centres_metres']['head'][0] -
                               original['proxy_calibration']['idle_centres_metres']['head'][0], .3, places=6)
        self.assertNotEqual(updated['proxy_calibration']['bone_local_offsets']['head'],
                            original['proxy_calibration']['bone_local_offsets']['head'])
        self.assertEqual(updated['proxy_calibration']['bone_local_offsets']['body_top'],
                         original['proxy_calibration']['bone_local_offsets']['body_top'])

    def test_legacy_loop_and_missing_surface_are_rejected(self):
        frozen = frozen_contract()
        frozen['runtime_contract']['physical_steps_per_loop'] = 2
        with self.assertRaisesRegex(ValueError, 'six-step'):
            locomotion_source_contract(frozen)
        frozen = frozen_contract()
        next(row for row in frozen['profiles'] if row['clip_alias'] == 'idle')['source_loop_seconds'] = [1 / 3, 1.5]
        with self.assertRaisesRegex(ValueError, 'idle/walk source domain'):
            locomotion_source_contract(frozen)
        document, binary = actor()
        document['meshes'][0]['extras'].pop('body_primitive_indices')
        with self.assertRaisesRegex(ValueError, 'explicit body primitive'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        document, binary = actor()
        document['animations'][-1]['samplers'][0]['input'] = 0
        with self.assertRaisesRegex(ValueError, '0 to 1.5'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())

    def test_body_coverage_preserves_prior_anchor_relative_y_and_measures_xz(self):
        document, binary = actor()
        prior = coverage_contract()
        prior['idle_reference']['hip'][1] -= .2
        prior['idle_reference']['spine02'][1] -= .1
        original = copy.deepcopy(prior)
        result = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), prior)
        centres = result['proxy_calibration']['idle_centres_metres']
        self.assertAlmostEqual(centres['body_bottom'][1], .75, places=6)
        self.assertAlmostEqual(centres['body_top'][1], 1.5, places=6)
        surface = result['proxy_calibration']['measurement']['surface_axis_centres_metres']
        self.assertAlmostEqual(surface['body_bottom'][1], .7, places=6)
        for field in ('body_bottom', 'body_top'):
            self.assertEqual(centres[field][0], surface[field][0])
            self.assertEqual(centres[field][2], surface[field][2])
        self.assertEqual(prior, original)
        self.assertEqual(result['proxy_calibration']['body_coverage']['source_contract'], prior)

    def test_missing_and_nonfinite_body_coverage_contract_is_rejected(self):
        for prior, message in [(None, 'explicit'), ({}, 'explicit')]:
            document, binary = actor()
            with self.assertRaisesRegex(ValueError, message):
                export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), prior)
        for field, value in [('body_bottom', float('nan')), ('body_bottom', 1.5)]:
            document, binary = actor()
            prior = coverage_contract()
            prior['idle_centres_metres'][field][1] = value
            with self.assertRaises(ValueError):
                export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), prior)
        document, binary = actor()
        prior = coverage_contract()
        prior['source_profile']['sha256'] = 'unbound'
        with self.assertRaisesRegex(ValueError, 'pinned'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), prior)

    def test_invalid_skin_and_nonfinite_surface_are_rejected(self):
        for attribute, value, message in [('WEIGHTS_0', .2, 'normalized'), ('POSITION', float('nan'), 'finite')]:
            document, binary = actor()
            accessor = document['accessors'][document['meshes'][0]['primitives'][0]['attributes'][attribute]]
            offset = document['bufferViews'][accessor['bufferView']]['byteOffset']
            binary = bytearray(binary)
            struct.pack_into('<f', binary, offset, value)
            with self.assertRaisesRegex(ValueError, message):
                export_attack_profiles(document, bytes(binary), BANK, attack_contracts(), frozen_contract(), coverage_contract())

    def test_blade_marker_outside_hand_is_rejected(self):
        document, binary = actor()
        document['nodes'][7]['children'].remove(9)
        document['nodes'][0]['children'].append(9)
        with self.assertRaisesRegex(ValueError, 'mounted R_Hand'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())

    def test_head_proxy_uses_idle_calibrated_local_offset_during_rotation(self):
        document, binary = actor()
        offset = len(binary)
        binary += struct.pack('<8f', 0, 0, 0, 1, 1, 0, 0, 0)
        document['buffers'][0]['byteLength'] = len(binary)
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': 32})
        document['accessors'].append({'bufferView': len(document['bufferViews']) - 1, 'componentType': 5126, 'type': 'VEC4', 'count': 2})
        animation = document['animations'][0]
        animation['samplers'].append({'input': 0, 'output': len(document['accessors']) - 1})
        animation['channels'].append({'sampler': 1, 'target': {'node': 4, 'path': 'rotation'}})
        result = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        end = result['attacks']['OVERHEAD']['samples'][-1]
        self.assertAlmostEqual(end['head_origin'][1], 1.6, places=6)
        self.assertAlmostEqual(end['head'][1], 1.5, places=6)

    def test_weapon_markers_follow_actual_parent_rotation(self):
        document, binary = actor()
        offset = len(binary)
        binary += struct.pack('<8f', 0, 0, 0, 1, 1, 0, 0, 0)
        document['buffers'][0]['byteLength'] = len(binary)
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': 32})
        document['accessors'].append({'bufferView': len(document['bufferViews']) - 1, 'componentType': 5126, 'type': 'VEC4', 'count': 2})
        animation = document['animations'][0]
        animation['samplers'].append({'input': 0, 'output': len(document['accessors']) - 1})
        animation['channels'].append({'sampler': 1, 'target': {'node': 5, 'path': 'rotation'}})
        result = export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        end = result['attacks']['OVERHEAD']['samples'][-1]
        self.assertAlmostEqual(end['blade_base'][1], 1.08, places=6)
        self.assertAlmostEqual(end['blade_tip'][1], .38, places=6)
        self.assertAlmostEqual(end['blade_base'][2], -.10, places=6)

    def test_source_range_is_rejected_before_profile_export(self):
        document, binary = actor()
        binary = struct.pack('<2f', 0, 2.0) + binary[8:]
        with self.assertRaisesRegex(ValueError, '0 to 1.75'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())

    def test_nonfinite_source_and_duplicate_times_are_rejected(self):
        for first, last in [(0, float('nan')), (0, 0)]:
            document, binary = actor()
            binary = struct.pack('<2f', first, last) + binary[8:]
            with self.assertRaises(ValueError):
                export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())

    def test_incomplete_bank_and_missing_clip_are_rejected(self):
        document, binary = actor()
        with self.assertRaisesRegex(ValueError, 'OVERHEAD'):
            export_attack_profiles(document, binary, {'OVERHEAD': 'attack_overhead'}, {}, frozen_contract(), coverage_contract())
        broken = dict(BANK, LEFT='absent')
        with self.assertRaisesRegex(ValueError, 'absent'):
            export_attack_profiles(document, binary, broken, attack_contracts(), frozen_contract(), coverage_contract())

    def test_scene_root_transform_and_hierarchy_cycle_are_rejected(self):
        document, binary = actor()
        document['nodes'][0]['translation'] = [10, 0, 0]
        with self.assertRaisesRegex(ValueError, 'identity'):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())
        document, binary = actor()
        document['nodes'][9]['children'] = [7]
        with self.assertRaises(ValueError):
            export_attack_profiles(document, binary, BANK, attack_contracts(), frozen_contract(), coverage_contract())


if __name__ == '__main__':
    unittest.main(argv=[__file__])
