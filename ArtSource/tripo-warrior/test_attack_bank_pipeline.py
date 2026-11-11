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
        self.manifest['weapon_source'] = {'source': '../dao/dao_study.glb',
                                         'source_sha256': '0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616'}

    def test_frozen_manifest_and_retired_fields(self):
        library.validate_manifest(self.manifest)
        broken = copy.deepcopy(self.manifest)
        broken['characters'][0]['offhand_rotation_envelope'] = {'legacy': True}
        with self.assertRaises(ValueError):
            library.validate_manifest(broken)
        broken = copy.deepcopy(self.manifest)
        broken['attack_source']['clips'][0]['right_calibration_baked'] = True
        with self.assertRaises(ValueError):
            library.validate_manifest(broken)

    def test_manual_review_matches_data_and_rejects_drift(self):
        request = {'binding_sha256': 'frozen-inputs', 'characters': [{'id': 'actor', 'output_sha256': 'sample'}]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'review.json'
            path.write_text(json.dumps({'decision': 'approved', **request}))
            manifest = {'production_review': {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}}
            library.validate_production_review(manifest, request)
            changed = copy.deepcopy(request)
            changed['characters'][0]['output_sha256'] = 'changed'
            with self.assertRaises(ValueError):
                library.validate_production_review(manifest, changed)
            with self.assertRaises(ValueError):
                library.validate_production_review({}, request)

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


if __name__ == '__main__':
    unittest.main(argv=[__file__])
