"""Pure offline synthetic checks for attack anchor export, run with Blender Python."""

import copy
import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attack_profiles import export_attack_profiles


BANK = {'OVERHEAD': 'attack_overhead', 'LEFT': 'attack_left', 'RIGHT': 'attack_right'}


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
                       for name in [*BANK.values(), 'idle']],
    }
    binary = struct.pack('<8f', 0, 1.75, .2, 0, 0, .4, 0, 0)
    return document, binary


class AttackProfileTests(unittest.TestCase):
    def test_final_hierarchy_drives_mounted_blade_and_normalized_body(self):
        document, binary = actor()
        original = copy.deepcopy(document)
        result = export_attack_profiles(document, binary, BANK)
        self.assertEqual(document, original)
        self.assertEqual(result['axes'], {'up': '+Y', 'forward': '+Z', 'actor_left': '+X'})
        self.assertEqual(set(result['attacks']), set(BANK))
        for profile in result['attacks'].values():
            self.assertEqual(len(profile['samples']), 106)
            self.assertTrue(all(a['time_seconds'] < b['time_seconds']
                                for a, b in zip(profile['samples'], profile['samples'][1:])))
            contact = next(sample for sample in profile['samples'] if sample['time_seconds'] == 1.0)
            self.assertAlmostEqual(contact['head'][1], 1.62, places=6)
            self.assertAlmostEqual(contact['body_bottom'][1], .55, places=6)
            self.assertAlmostEqual(contact['body_top'][1], 1.4, places=6)
            self.assertAlmostEqual(contact['blade_base'][0], .4 + .4 / 1.75, places=6)
            self.assertAlmostEqual(contact['blade_base'][1], 1.32, places=6)
            self.assertAlmostEqual(contact['blade_tip'][1], 2.02, places=6)
            self.assertEqual(contact['torso_lower'], contact['hip'])
            self.assertEqual(contact['torso_upper'], contact['spine02'])
            for marker in result['phase_sample_times_seconds'].values():
                self.assertIn(marker, [sample['time_seconds'] for sample in profile['samples']])
        json.dumps(result, allow_nan=False)

    def test_blade_marker_outside_hand_is_rejected(self):
        document, binary = actor()
        document['nodes'][7]['children'].remove(9)
        document['nodes'][0]['children'].append(9)
        with self.assertRaisesRegex(ValueError, 'mounted R_Hand'):
            export_attack_profiles(document, binary, BANK)

    def test_head_proxy_uses_idle_calibrated_local_offset_during_rotation(self):
        document, binary = actor()
        offset = len(binary)
        binary += struct.pack('<8f', 0, 0, 0, 1, 1, 0, 0, 0)
        document['buffers'][0]['byteLength'] = len(binary)
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': 32})
        document['accessors'].append({'bufferView': 2, 'componentType': 5126, 'type': 'VEC4', 'count': 2})
        animation = document['animations'][0]
        animation['samplers'].append({'input': 0, 'output': 2})
        animation['channels'].append({'sampler': 1, 'target': {'node': 4, 'path': 'rotation'}})
        result = export_attack_profiles(document, binary, BANK)
        end = result['attacks']['OVERHEAD']['samples'][-1]
        self.assertAlmostEqual(end['head_origin'][1], 1.6, places=6)
        self.assertAlmostEqual(end['head'][1], 1.58, places=6)

    def test_weapon_markers_follow_actual_parent_rotation(self):
        document, binary = actor()
        offset = len(binary)
        binary += struct.pack('<8f', 0, 0, 0, 1, 1, 0, 0, 0)
        document['buffers'][0]['byteLength'] = len(binary)
        document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': 32})
        document['accessors'].append({'bufferView': 2, 'componentType': 5126, 'type': 'VEC4', 'count': 2})
        animation = document['animations'][0]
        animation['samplers'].append({'input': 0, 'output': 2})
        animation['channels'].append({'sampler': 1, 'target': {'node': 5, 'path': 'rotation'}})
        result = export_attack_profiles(document, binary, BANK)
        end = result['attacks']['OVERHEAD']['samples'][-1]
        self.assertAlmostEqual(end['blade_base'][1], 1.08, places=6)
        self.assertAlmostEqual(end['blade_tip'][1], .38, places=6)
        self.assertAlmostEqual(end['blade_base'][2], -.10, places=6)

    def test_source_range_is_rejected_before_profile_export(self):
        document, binary = actor()
        binary = struct.pack('<2f', 0, 2.0) + binary[8:]
        with self.assertRaisesRegex(ValueError, '0 to 1.75'):
            export_attack_profiles(document, binary, BANK)

    def test_nonfinite_source_and_duplicate_times_are_rejected(self):
        for first, last in [(0, float('nan')), (0, 0)]:
            document, binary = actor()
            binary = struct.pack('<2f', first, last) + binary[8:]
            with self.assertRaises(ValueError):
                export_attack_profiles(document, binary, BANK)

    def test_incomplete_bank_and_missing_clip_are_rejected(self):
        document, binary = actor()
        with self.assertRaisesRegex(ValueError, 'OVERHEAD'):
            export_attack_profiles(document, binary, {'OVERHEAD': 'attack_overhead'})
        broken = dict(BANK, LEFT='absent')
        with self.assertRaisesRegex(ValueError, 'absent'):
            export_attack_profiles(document, binary, broken)

    def test_scene_root_transform_and_hierarchy_cycle_are_rejected(self):
        document, binary = actor()
        document['nodes'][0]['translation'] = [10, 0, 0]
        with self.assertRaisesRegex(ValueError, 'identity'):
            export_attack_profiles(document, binary, BANK)
        document, binary = actor()
        document['nodes'][9]['children'] = [7]
        with self.assertRaises(ValueError):
            export_attack_profiles(document, binary, BANK)


if __name__ == '__main__':
    unittest.main(argv=[__file__])
