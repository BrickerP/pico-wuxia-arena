"""Small offline contract checks. No bank publication or app writes."""
import copy
import hashlib
import json
import math
import struct
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from mathutils import Quaternion
import prepare_character_library as library
from test_attack_profiles import attack_contracts, float32


class AttackBankContracts(unittest.TestCase):
    def test_published_empty_wrist_does_not_fold_into_the_forearm(self):
        from attack_profiles import animation_tracks, hierarchy, pose_world
        for actor in ('base', 'indigo', 'veteran'):
            doc, binary = library.read_glb(library.HERE / 'library' / (actor + '.glb'))
            _, parents, order = hierarchy(doc)
            names = {node.get('name'): index for index, node in enumerate(doc['nodes'])}
            for clip, time in (('attack_right', .65), ('attack_left', .75), ('attack_overhead', 1.25)):
                with self.subTest(actor=actor, clip=clip, time=time):
                    action = next(a for a in doc['animations'] if a['name'] == clip)
                    tracks, _ = animation_tracks(doc, binary, action)
                    world = pose_world(doc, tracks, time, parents, order)
                    elbow, wrist, knuckle = [world[names[n]].translation for n in
                                              ('L_Forearm', 'L_Hand', 'L_Mid1')]
                    self.assertLessEqual(math.degrees((wrist-elbow).angle(knuckle-wrist)), 38.1)

    def setUp(self):
        self.manifest = json.loads((library.HERE / 'motion_library.json').read_text())
        self.original_manifest = copy.deepcopy(self.manifest)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.bind_phase_rows(self.manifest)

    def bind_phase_rows(self, manifest):
        """Use existing source GLBs with an explicitly new, isolated reviewed-row fixture."""
        bank = manifest['attack_source']
        bank.pop('phase_markers', None)
        authoring = json.loads((library.HERE / bank['authoring_manifest']['source']).read_text())
        aliases = {'OVERHEAD': 'overhead', 'LEFT': 'slash_to_left', 'RIGHT': 'slash_to_right'}
        for entry in bank['clips']:
            contract = attack_contracts()[entry['name']]
            entry.update(copy.deepcopy(contract))
            row = next(row for row in authoring['clips'] if row['clip'] == aliases[entry['direction']])
            row.update(copy.deepcopy(contract))
        path = Path(self.temporary.name) / (str(len(list(Path(self.temporary.name).iterdir()))) + '_attack_inputs.json')
        path.write_text(json.dumps(authoring))
        bank['authoring_manifest'] = {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def breathing_idle(self):
        """Real rig/REST/IBM plus a synthetic closed chest curve; never writes a model."""
        bank = self.manifest['locomotion_source']
        row = next(row for row in bank['clips'] if row['name'] == 'idle')
        _, document, binary = library.pinned_source(row)
        tracks, _ = library.decode_animation(document, binary)
        result, packed = copy.deepcopy(document), bytearray(binary)
        times = [float32(index / 120) for index in range(181)]

        def accessor(rows, kind):
            width = len(rows[0])
            packed.extend(b'\0' * (-len(packed) % 4))
            start = len(packed)
            for value in rows:
                packed.extend(struct.pack('<' + 'f' * width, *value))
            view = len(result['bufferViews'])
            result['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(packed) - start})
            index = len(result['accessors'])
            result['accessors'].append({'bufferView': view, 'componentType': 5126,
                                        'type': kind, 'count': len(rows)})
            return index

        time_index = accessor([(time,) for time in times], 'SCALAR')
        animation = {'name': 'idle', 'samplers': [], 'channels': []}
        for (index, path), (_, original, _) in tracks.items():
            values = [original[0]] * len(times)
            if result['nodes'][index]['name'] == 'Spine02' and path == 'rotation':
                q = Quaternion((original[0][3], *original[0][:3]))
                for key in range(1, len(times) - 1):
                    value = q @ Quaternion((1, 0, 0), math.radians(.7) * math.sin(math.pi * times[key] / 1.5) ** 2)
                    values[key] = (value.x, value.y, value.z, value.w)
            sampler = len(animation['samplers'])
            animation['samplers'].append({'input': time_index, 'output': accessor(values, 'VEC4' if path == 'rotation' else 'VEC3'),
                                           'interpolation': 'LINEAR'})
            animation['channels'].append({'sampler': sampler, 'target': {'node': index, 'path': path}})
        result['animations'] = [animation]
        result['buffers'][0]['byteLength'] = len(packed)
        return result, bytes(packed)

    def test_prepared_wrist_requires_actual_combined_steel_before_writing(self):
        solver, recipe = library.prepared_wrist_contract(self.manifest)
        original, binary = library.read_glb(library.HERE / 'library/veteran_prepared_png.glb')
        points = solver.combined_steel_hand_points(original, binary)
        self.assertEqual(points.shape, (5533, 4))
        missing = copy.deepcopy(original)
        for material in missing['materials']:
            material['name'] = material.get('name', '').replace('Steel', 'Rubber')
        folder = Path(self.temporary.name)
        body = folder / 'body.glb'
        combined = folder / 'combined.glb'
        body.write_bytes((library.HERE / 'library/veteran_body.glb').read_bytes())
        combined.write_bytes(solver.encode_glb(missing, binary))
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in (body, combined)]
        with self.assertRaisesRegex(ValueError, 'no Steel weapon surface'):
            solver.apply_prepared_character('veteran', body, combined, recipe)
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in (body, combined)])

    def test_prepared_wrist_rejects_normalized_steel_weight_outside_hand(self):
        solver, recipe = library.prepared_wrist_contract(self.manifest)
        document, binary = library.read_glb(library.HERE / 'library/veteran_prepared_png.glb')
        names = {node['name']: index for index, node in enumerate(document['nodes'])}
        hand = document['skins'][0]['joints'].index(names['R_Hand'])
        primitive = next(primitive for mesh in document['meshes']
                         for primitive in mesh['primitives']
                         if 'Steel' in document['materials'][primitive['material']].get('name', ''))
        attributes = primitive['attributes']
        weights = solver.skin_attribute(document, binary, attributes['WEIGHTS_0']).copy()
        joints = solver.skin_attribute(document, binary, attributes['JOINTS_0'])
        hand_slot = next(slot for slot, joint in enumerate(joints[0]) if joint == hand)
        other_slot = next(slot for slot, joint in enumerate(joints[0]) if joint != hand)
        weights[0] = 0
        weights[0, hand_slot] = .75
        weights[0, other_slot] = .25
        binary, attributes['WEIGHTS_0'] = solver.append_accessor(
            document, binary, weights.tolist(), 'VEC4')
        folder = Path(self.temporary.name)
        body = folder / 'body.glb'
        combined = folder / 'combined.glb'
        body.write_bytes((library.HERE / 'library/veteran_body.glb').read_bytes())
        combined.write_bytes(solver.encode_glb(document, binary))
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in (body, combined)]
        with self.assertRaisesRegex(ValueError, 'not rigid to R_Hand'):
            solver.apply_prepared_character('veteran', body, combined, recipe)
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in (body, combined)])

    def test_prepared_wrist_recipe_and_implementation_are_binding_inputs(self):
        original = library.canonical_hash(library.production_binding(self.manifest))
        for role in ('implementation', 'recipe'):
            broken = copy.deepcopy(self.manifest)
            broken['prepared_wrist_constraint'][role]['source_sha256'] = '0' * 64
            self.assertNotEqual(original, library.canonical_hash(library.production_binding(broken)))
            with self.assertRaisesRegex(ValueError, 'constraint identity changed'):
                library.prepared_wrist_contract(broken)
        broken = copy.deepcopy(self.manifest)
        broken.pop('prepared_wrist_constraint')
        with self.assertRaisesRegex(ValueError, 'requires its pinned prepared wrist constraint'):
            library.prepared_wrist_contract(broken)

    def test_frozen_manifest_and_retired_fields(self):
        library.validate_manifest(self.manifest)
        broken = copy.deepcopy(self.manifest)
        broken['characters'][0]['offhand_rotation_envelope'] = {'legacy': True}
        with self.assertRaises(ValueError):
            library.validate_manifest(broken)

    def test_shared_phase_manifest_is_rejected_and_bound_direction_rows_are_distinct(self):
        shared = copy.deepcopy(self.original_manifest)
        shared['attack_source']['phase_markers'] = copy.deepcopy(self.manifest['attack_source']['clips'][0]['phase_markers'])
        with self.assertRaisesRegex(ValueError, 'shared.*phase_markers'):
            library.validate_manifest(shared)
        contracts = library.attack_source_contracts(self.manifest['attack_source'])
        expected = attack_contracts()
        for name, row in contracts.items():
            self.assertEqual(row['phase_markers'], expected[name]['phase_markers'])
            self.assertEqual(row['runtime_phase_nanos'], expected[name]['runtime_phase_nanos'])
        self.assertNotEqual(contracts['attack_overhead']['phase_markers'], contracts['attack_left']['phase_markers'])

    def test_phase_or_runtime_drift_from_the_same_authoring_direction_is_rejected(self):
        for field in ('phase_markers', 'runtime_phase_nanos'):
            bank = copy.deepcopy(self.manifest['attack_source'])
            overhead = next(row for row in bank['clips'] if row['direction'] == 'OVERHEAD')
            if field == 'phase_markers':
                overhead[field]['startup_end'] += .001
            else:
                overhead[field][0] += 1
            with self.assertRaisesRegex(ValueError, 'phase/runtime contract differs'):
                library.attack_source_contracts(bank)
        for field in ('phase_markers', 'runtime_phase_nanos'):
            changed = copy.deepcopy(self.manifest)
            changed['attack_source']['clips'][0][field] = copy.deepcopy(changed['attack_source']['clips'][1][field])
            self.assertNotEqual(library.canonical_hash(library.production_binding(self.manifest)),
                                library.canonical_hash(library.production_binding(changed)))

    def test_each_direction_requires_its_own_complete_valid_clock(self):
        for field, value in [('phase_markers', None), ('runtime_phase_nanos', None),
                             ('runtime_phase_nanos', [True, 1, 1, 1]),
                             ('runtime_phase_nanos', [1.0, 1, 1, 1]),
                             ('runtime_phase_nanos', [0, 1, 1, 1]),
                             ('runtime_phase_nanos', [1 << 63, 1, 1, 1])]:
            bank = copy.deepcopy(self.manifest['attack_source'])
            bank['clips'][0][field] = value
            with self.assertRaises(ValueError, msg=str(value)):
                library.attack_source_contracts(bank)

    def test_nonkey_contact_cue_remains_bound_metadata_without_changing_the_raw_grid(self):
        original_binding = library.canonical_hash(library.production_binding(self.manifest))
        for cue in (.95, .955):
            changed = copy.deepcopy(self.manifest)
            bank = changed['attack_source']
            authoring = json.loads((library.HERE / bank['authoring_manifest']['source']).read_text())
            for entry in bank['clips']:
                entry['phase_markers']['contact'] = cue
            for row in authoring['clips']:
                row['phase_markers']['contact'] = cue
                row['contact_source_seconds'] = cue
            path = Path(self.temporary.name) / ('cue_' + str(cue) + '.json')
            path.write_text(json.dumps(authoring))
            bank['authoring_manifest'] = {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            declared = library.attack_source_contracts(bank)
            self.assertNotEqual(original_binding, library.canonical_hash(library.production_binding(changed)))
            _, rig, rig_binary = library.pinned_source(bank)
            for entry in bank['clips']:
                _, document, binary = library.pinned_source(entry)
                tracks = library.validate_source_clip(document, binary, rig, rig_binary, 'attack78', entry['name'],
                                                      declared[entry['name']])
                self.assertEqual(declared[entry['name']]['contact_source_seconds'], cue)
                if cue == .955:
                    self.assertNotIn(float32(cue), next(iter(tracks.values()))[0])

    def test_v2_and_motion41_idle_and_baked_locomotion_are_rejected(self):
        for change in ('schema', 'old_idle', 'baked', 'missing', 'missing_coverage', 'coverage_drift'):
            broken = copy.deepcopy(self.manifest)
            if change == 'schema':
                broken['schema_version'] = 2
            elif change == 'old_idle':
                broken['motion_source']['clips'].append({'name': 'idle'})
            elif change == 'baked':
                broken['locomotion_source']['clips'][0]['right_calibration_baked'] = True
            elif change == 'missing':
                del broken['locomotion_source']
            elif change == 'missing_coverage':
                del broken['body_coverage_calibration']
            else:
                broken['body_coverage_calibration']['source_sha256'] = '0' * 64
            with self.assertRaises(ValueError, msg=change):
                library.validate_manifest(broken)
        broken = copy.deepcopy(self.manifest)
        broken['attack_source']['clips'][0]['right_calibration_baked'] = True
        with self.assertRaises(ValueError):
            library.validate_manifest(broken)

    def test_producer_projection_and_calculation_use_one_shared_pure_policy(self):
        import attack_grounding
        import production_contract
        self.assertIs(library.production_binding, production_contract.production_binding)
        self.assertIs(library.HAND_POLICY, production_contract.HAND_POLICY)
        self.assertIs(library.LEFT_HAND_POSES, production_contract.LEFT_HAND_POSES)
        self.assertIs(attack_grounding.GROUNDING_POLICY, production_contract.GROUNDING_POLICY)
        self.assertEqual(library.HAND_POLICY, library.production_binding(self.manifest)['hand_policy'])
        self.assertEqual(attack_grounding.GROUNDING_POLICY,
                         library.production_binding(self.manifest)['canonical_root_grounding'])

    def test_manual_review_matches_data_and_rejects_drift(self):
        request = {'binding_sha256': 'frozen-inputs', 'characters': [{'id': 'actor', 'output_sha256': 'sample'}],
                   'player_weapon': {'output': {'sha256': 'encoded-player'}}}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.json'
            path.write_text(json.dumps({'decision': 'approved', **request}))
            manifest = {'production_review': {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
            library.validate_production_review(manifest, request)
            changed = copy.deepcopy(request)
            changed['characters'][0]['output_sha256'] = 'changed'
            with self.assertRaises(ValueError):
                library.validate_production_review(manifest, changed)
            changed = copy.deepcopy(request)
            changed['player_weapon']['output']['sha256'] = 'changed-player'
            with self.assertRaisesRegex(ValueError, 'player weapon'):
                library.validate_production_review(manifest, changed)
            with self.assertRaises(ValueError):
                library.validate_production_review({}, request)

    def test_texture_encoding_contract_is_fixed_and_rejects_png_and_tool_drift(self):
        config = self.manifest['runtime_texture_encoding']
        library.validate_texture_encoding(config)
        for field, value in [('format', 'PNG'), ('settings', {**config['settings'], 'pixel_resize': True}),
                             ('helper', {**config['helper'], 'source_sha256': '0' * 64}),
                             ('host_python', {**config['host_python'], 'pillow_version': 'incorrect'})]:
            broken = copy.deepcopy(config)
            broken[field] = value
            with self.assertRaises(ValueError, msg=field):
                library.validate_texture_encoding(broken)
        with self.assertRaises(ValueError):
            library.validate_texture_encoding(None)

    def test_runtime_encoding_and_player_source_are_mandatory_binding_inputs(self):
        for field in ('runtime_texture_encoding', 'player_weapon_source'):
            broken = copy.deepcopy(self.manifest)
            del broken[field]
            with self.assertRaises(ValueError, msg=field):
                library.validate_manifest(broken)
        original = library.canonical_hash(library.production_binding(self.manifest))
        changed = copy.deepcopy(self.manifest)
        changed['player_weapon_source']['source_sha256'] = '0' * 64
        self.assertNotEqual(original, library.canonical_hash(library.production_binding(changed)))
        with self.assertRaisesRegex(ValueError, 'player_weapon_source'):
            library.validate_manifest(changed)

    def test_attack78_world_transfer_and_native_weapon_fingers(self):
        bank = self.manifest['attack_source']
        _, rig, rig_binary = library.pinned_source(bank)
        row = next(row for row in bank['clips'] if row['direction'] == 'LEFT')
        _, motion, motion_binary = library.pinned_source(row)
        library.validate_source_clip(motion, motion_binary, rig, rig_binary, 'attack78', row['name'],
                                     library.attack_source_contracts(bank)[row['name']])
        target_row = next(row for row in self.manifest['characters'] if row['id'] == 'indigo')
        _, target, target_binary = library.pinned_source(target_row)
        _, grip, grip_binary = library.pinned_source(target_row['grip_source'])
        native = library.sample_native_hands(target, grip, grip_binary, 2.117)
        output, record = library.retarget_clip(motion, motion_binary, rig, target, target_binary,
                                               native, 'attack_left', source_contract='attack78')
        import struct
        size = struct.unpack_from('<I', output, 12)[0]
        result = json.loads(output[20:20 + size])
        binary = output[28 + size:]
        self.assertEqual(result['nodes'], target['nodes'])
        self.assertEqual(result['skins'], target['skins'])
        self.assertEqual(result['meshes'], target['meshes'])
        self.assertEqual(record['source_joints'], 78)
        tracks, _ = library.decode_animation(result, binary)
        names = library.joint_nodes(result)
        for name, pose in native.items():
            if name.startswith('R_'):
                actual = library.sampled_local(result['nodes'][names[name]], names[name], tracks, 1.0)
                self.assertLess(actual.to_quaternion().rotation_difference(pose.to_quaternion()).angle, 1e-4)
        with self.assertRaises(ValueError):
            library.retarget_clip(motion, motion_binary, rig, target, target_binary,
                                  native, 'idle', source_contract='motion41')

    def test_each_attack_uses_its_bound_authoring_grid_without_downsampling_v9(self):
        bank = self.manifest['attack_source']
        _, rig, rig_binary = library.pinned_source(bank)
        original_contracts = library.attack_source_contracts(bank)
        left = next(row for row in bank['clips'] if row['direction'] == 'LEFT')
        _, source, binary = library.pinned_source(left)
        actual = library.validate_source_clip(source, binary, rig, rig_binary, 'attack78', left['name'],
                                             original_contracts[left['name']])
        self.assertEqual(len(actual), 234)
        self.assertEqual(len(next(iter(actual.values()))[0]), 106)
        candidate = json.loads((library.HERE.parent / 'refinement/combat-direction/overhead-v9-candidate/motion_library.json').read_text())
        # Keep the historical source grid while satisfying today's prepared-space admission contract.
        candidate['prepared_wrist_constraint'] = copy.deepcopy(self.manifest['prepared_wrist_constraint'])
        self.bind_phase_rows(candidate)
        library.validate_manifest(candidate)
        attack = candidate['attack_source']
        contracts = library.attack_source_contracts(attack)
        row = next(row for row in attack['clips'] if row['direction'] == 'OVERHEAD')
        _, source, binary = library.pinned_source(row)
        actual = library.validate_source_clip(source, binary, rig, rig_binary, 'attack78', row['name'], contracts[row['name']])
        self.assertEqual(len(actual), 234)
        self.assertEqual(len(next(iter(actual.values()))[0]), 211)
        self.assertEqual([contracts[name]['sample_count'] for name in library.ATTACK_CLIPS.values()], [211, 106, 106])

    def test_v9_wrong_declared_count_or_wrong_clip_contract_is_rejected(self):
        candidate = json.loads((library.HERE.parent / 'refinement/combat-direction/overhead-v9-candidate/motion_library.json').read_text())
        self.bind_phase_rows(candidate)
        bank = candidate['attack_source']
        contracts = library.attack_source_contracts(bank)
        _, rig, rig_binary = library.pinned_source(bank)
        row = next(row for row in bank['clips'] if row['direction'] == 'OVERHEAD')
        _, source, binary = library.pinned_source(row)
        bad_count = copy.deepcopy(contracts[row['name']])
        bad_count['sample_count'] = 210
        for declared in (bad_count, contracts['attack_left']):
            with self.assertRaisesRegex(ValueError, 'authoring time contract'):
                library.validate_source_clip(source, binary, rig, rig_binary, 'attack78', row['name'], declared)
        swapped = copy.deepcopy(bank)
        swapped['clips'][0]['source_sha256'] = swapped['clips'][1]['source_sha256']
        with self.assertRaisesRegex(ValueError, 'frozen unbaked authoring source'):
            library.attack_source_contracts(swapped)

    def test_v9_off_grid_or_shortened_boundary_source_times_are_rejected(self):
        candidate = json.loads((library.HERE.parent / 'refinement/combat-direction/overhead-v9-candidate/motion_library.json').read_text())
        self.bind_phase_rows(candidate)
        bank = candidate['attack_source']
        row = next(row for row in bank['clips'] if row['direction'] == 'OVERHEAD')
        declared = library.attack_source_contracts(bank)[row['name']]
        _, rig, rig_binary = library.pinned_source(bank)
        _, source, binary = library.pinned_source(row)
        tracks, times = library.decode_animation(source, binary)
        for index, delta in ((1, .00001), (-1, -.00001)):
            changed = list(times)
            changed[index] += delta
            altered_tracks = {key: (changed, values, interpolation)
                              for key, (_, values, interpolation) in tracks.items()}
            with mock.patch.object(library, 'decode_animation', return_value=(altered_tracks, changed)):
                with self.assertRaisesRegex(ValueError, 'source key count/time grid'):
                    library.validate_source_clip(source, binary, rig, rig_binary, 'attack78', row['name'], declared)

    def test_locked_locomotion_reuses_world_transfer_and_keeps_step_semantics(self):
        bank = self.manifest['locomotion_source']
        _, rig, rig_binary = library.pinned_source(bank)
        target_row = self.manifest['characters'][0]
        _, target, target_binary = library.pinned_source(target_row)
        _, grip, grip_binary = library.pinned_source(target_row['grip_source'])
        native = library.sample_native_hands(target, grip, grip_binary, 2.117)
        row = next(row for row in bank['clips'] if row['name'] == 'walk')
        _, motion, motion_binary = library.pinned_source(row)
        tracks = library.validate_source_clip(motion, motion_binary, rig, rig_binary, 'locomotion78', 'walk')
        with self.assertRaisesRegex(ValueError, 'pinned authoring time contract'):
            library.validate_source_clip(motion, motion_binary, rig, rig_binary, 'attack78')
        broken = copy.deepcopy(motion)
        channel = next(c for c in broken['animations'][0]['channels']
                       if broken['nodes'][c['target']['node']]['name'] == 'Head' and c['target']['path'] == 'rotation')
        broken['animations'][0]['samplers'][channel['sampler']]['interpolation'] = 'LINEAR'
        with self.assertRaisesRegex(ValueError, 'interpolation'):
            library.validate_source_clip(broken, motion_binary, rig, rig_binary, 'locomotion78', 'walk')
        original_times = list(next(iter(tracks.values()))[0])
        shifted_times = list(original_times)
        shifted_times[50] += .00001
        shifted_tracks = {key: (shifted_times, values, interpolation)
                          for key, (_, values, interpolation) in tracks.items()}
        with mock.patch.object(library, 'decode_animation', return_value=(shifted_tracks, shifted_times)):
            with self.assertRaisesRegex(ValueError, 'unchanged 185-key six-step source time grid'):
                library.validate_source_clip(motion, motion_binary, rig, rig_binary, 'locomotion78', 'walk')
        output, record = library.retarget_clip(motion, motion_binary, rig, target, target_binary,
                                              native, 'walk', source_contract='locomotion78')
        import struct
        size = struct.unpack_from('<I', output, 12)[0]
        result, binary = json.loads(output[20:20+size]), output[28+size:]
        self.assertEqual(result['nodes'], target['nodes'])
        self.assertEqual(result['skins'], target['skins'])
        self.assertEqual(result['meshes'], target['meshes'])
        actual, times = library.decode_animation(result, binary)
        self.assertEqual(len(times), 185)
        source_names, names = library.joint_nodes(motion), library.joint_nodes(result)
        for name, index in names.items():
            for path in ('translation', 'rotation', 'scale'):
                expected = tracks[source_names[name], path][2]
                self.assertEqual(actual[index, path][2], expected, name + '/' + path)
                if expected == 'STEP':
                    self.assertEqual(len(set(actual[index, path][1])), 1)
        self.assertEqual(record['sample_count'], 185)

    def test_breathing_idle_keeps_all181_linear_keys_and_real_body_motion_after_retarget(self):
        bank = self.manifest['locomotion_source']
        _, rig, rig_binary = library.pinned_source(bank)
        motion, binary = self.breathing_idle()
        tracks = library.validate_source_clip(motion, binary, rig, rig_binary, 'locomotion78', 'idle')
        self.assertEqual(len(tracks), 234)
        self.assertEqual(len(next(iter(tracks.values()))[0]), 181)
        spine = library.joint_nodes(motion)['Spine02']
        self.assertNotEqual(tracks[spine, 'rotation'][1][0], tracks[spine, 'rotation'][1][90])
        target_row = self.manifest['characters'][0]
        _, target, target_binary = library.pinned_source(target_row)
        _, grip, grip_binary = library.pinned_source(target_row['grip_source'])
        native = library.sample_native_hands(target, grip, grip_binary, 2.117)
        output, record = library.retarget_clip(motion, binary, rig, target, target_binary,
                                              native, 'idle', source_contract='locomotion78')
        size = struct.unpack_from('<I', output, 12)[0]
        result, result_binary = json.loads(output[20:20+size]), output[28+size:]
        actual, times = library.decode_animation(result, result_binary)
        self.assertEqual(len(times), 181)
        self.assertTrue(all(track[2] == 'LINEAR' for track in actual.values()))
        actual_spine = library.joint_nodes(result)['Spine02']
        self.assertNotEqual(actual[actual_spine, 'rotation'][1][0], actual[actual_spine, 'rotation'][1][90])
        self.assertEqual(result['skins'], target['skins'])
        self.assertEqual(result['nodes'], target['nodes'])
        self.assertEqual(record['sample_count'], 181)

    def test_idle_rejects_old_step_grid_bad_loop_root_motion_and_weapon_finger_motion(self):
        bank = self.manifest['locomotion_source']
        _, rig, rig_binary = library.pinned_source(bank)
        motion, binary = self.breathing_idle()
        names = library.joint_nodes(motion)
        tracks, times = library.decode_animation(motion, binary)
        for issue in ('old_count', 'step', 'endpoint', 'root', 'weapon_finger'):
            altered = copy.deepcopy(tracks)
            altered_times = list(times)
            if issue == 'old_count':
                altered_times = altered_times[::2]
                altered = {key: (altered_times, values[::2], interpolation)
                           for key, (_, values, interpolation) in altered.items()}
            else:
                joint, path = ('Spine02', 'rotation') if issue in ('step', 'endpoint') else (
                    ('BoneRoot', 'translation') if issue == 'root' else ('R_Index1', 'rotation'))
                key = names[joint], path
                grid, values, interpolation = altered[key]
                if issue == 'step':
                    interpolation = 'STEP'
                else:
                    at = -1 if issue == 'endpoint' else 90
                    values[at] = tuple(value + (.001 if axis == 0 else 0) for axis, value in enumerate(values[at]))
                altered[key] = grid, values, interpolation
            with self.subTest(issue=issue), mock.patch.object(library, 'decode_animation', return_value=(altered, altered_times)):
                with self.assertRaises(ValueError):
                    library.validate_source_clip(motion, binary, rig, rig_binary, 'locomotion78', 'idle')

    def test_raw_canonical_234_markers_and_ancestor_midpoints(self):
        frozen, _ = library.validate_manifest(self.manifest)
        sources = []
        for family in ('locomotion_source', 'attack_source'):
            for entry in self.manifest[family]['clips']:
                _, document, binary = library.pinned_source(entry)
                sources.append((entry, document, binary, None, self.manifest[family]['contract']))
        idle, binary = self.breathing_idle()
        entry = next(row for row in self.manifest['locomotion_source']['clips'] if row['name'] == 'idle')
        sources[0] = (entry, idle, binary, None, 'locomotion78')
        evidence = library.canonical_source_evidence(sources, frozen)
        self.assertEqual(evidence['idle']['key_and_midpoint_count'], 361)
        self.assertEqual(evidence['idle']['marker_source_seconds'], [0, 1.5])
        self.assertEqual(evidence['walk']['key_and_midpoint_count'], 369)
        broken = copy.deepcopy(sources)
        idle = broken[0][1]
        armature = next(node for node in idle['nodes'] if node['name'] == 'Armature')
        armature.pop('matrix', None)
        armature['translation'] = [.1, 0, 0]
        with self.assertRaisesRegex(ValueError, 'static ancestor'):
            library.canonical_source_evidence(broken, frozen)


if __name__ == '__main__':
    unittest.main(argv=[__file__])
