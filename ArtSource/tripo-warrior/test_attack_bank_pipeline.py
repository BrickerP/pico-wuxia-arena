"""Small offline contract checks. No bank publication or app writes."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mathutils import Quaternion
import prepare_character_library as library


class AttackBankContracts(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((library.HERE / 'motion_library.json').read_text())

    def test_frozen_manifest_and_retired_fields(self):
        library.validate_manifest(self.manifest)
        broken = copy.deepcopy(self.manifest)
        broken['characters'][0]['offhand_rotation_envelope'] = {'legacy': True}
        with self.assertRaises(ValueError):
            library.validate_manifest(broken)

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
        library.validate_source_clip(motion, motion_binary, rig, rig_binary, 'attack78')
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
        with self.assertRaisesRegex(ValueError, '106-key'):
            library.validate_source_clip(motion, motion_binary, rig, rig_binary, 'attack78')
        broken = copy.deepcopy(motion)
        channel = next(c for c in broken['animations'][0]['channels']
                       if broken['nodes'][c['target']['node']]['name'] == 'Head' and c['target']['path'] == 'rotation')
        broken['animations'][0]['samplers'][channel['sampler']]['interpolation'] = 'LINEAR'
        with self.assertRaisesRegex(ValueError, 'interpolation'):
            library.validate_source_clip(broken, motion_binary, rig, rig_binary, 'locomotion78', 'walk')
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

    def test_raw_canonical_234_markers_and_ancestor_midpoints(self):
        frozen, _ = library.validate_manifest(self.manifest)
        sources = []
        for family in ('locomotion_source', 'attack_source'):
            for entry in self.manifest[family]['clips']:
                _, document, binary = library.pinned_source(entry)
                sources.append((entry, document, binary, None, self.manifest[family]['contract']))
        evidence = library.canonical_source_evidence(sources, frozen)
        self.assertEqual(evidence['idle']['key_and_midpoint_count'], 181)
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
