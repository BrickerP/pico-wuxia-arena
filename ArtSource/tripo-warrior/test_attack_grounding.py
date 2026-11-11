"""Offline LBS checks on the private bank candidates. No asset publication."""

import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from attack_grounding import GROUNDING_POLICY, ground_attack_feet
from attack_profiles import animation_tracks, hierarchy, pose_world
from prepare_rigged_warrior import animation_signature, accessor_bytes, read_glb


HERE = Path(__file__).resolve().parent
BANK = ['attack_overhead', 'attack_left', 'attack_right']


class AttackGroundingTests(unittest.TestCase):
    def test_three_targets_keep_other_curves_and_ground_keys_and_midpoints(self):
        for actor in ('base', 'indigo', 'veteran'):
            path = HERE / 'review/attack-bank-candidate' / (actor + '.glb')
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            document, binary = read_glb(path)
            original = copy.deepcopy(document)
            before = {clip['name']: animation_signature(document, binary, clip)
                      for clip in document['animations']}
            result, report = ground_attack_feet(document, binary, BANK)
            self.assertEqual(report['policy'], GROUNDING_POLICY)
            self.assertEqual(result[:len(binary)], binary)
            self.assertEqual(document['nodes'], original['nodes'])
            self.assertEqual(document['meshes'], original['meshes'])
            self.assertEqual(document['skins'], original['skins'])
            root = next(index for index, node in enumerate(document['nodes']) if node['name'] == 'BoneRoot')
            for old_clip, clip in zip(original['animations'], document['animations']):
                if clip['name'] not in BANK:
                    self.assertEqual(animation_signature(document, result, clip), before[clip['name']])
                    continue
                for old_channel, channel in zip(old_clip['channels'], clip['channels']):
                    self.assertEqual(channel, old_channel)
                    old_sampler = old_clip['samplers'][old_channel['sampler']]
                    sampler = clip['samplers'][channel['sampler']]
                    self.assertEqual(accessor_bytes(document, result, sampler['input']),
                                     accessor_bytes(original, binary, old_sampler['input']))
                    if channel['target'] != {'node': root, 'path': 'translation'}:
                        self.assertEqual(accessor_bytes(document, result, sampler['output']),
                                         accessor_bytes(original, binary, old_sampler['output']))
                old_tracks, _ = animation_tracks(original, binary, old_clip)
                tracks, _ = animation_tracks(document, result, clip)
                _, parents, order = hierarchy(document)
                for time in (0, .65, 1, 1.1, 1.75):
                    old_world = pose_world(original, old_tracks, time, parents, order)
                    world = pose_world(document, tracks, time, parents, order)
                    hand = next(index for index, node in enumerate(document['nodes']) if node['name'] == 'R_Hand')
                    self.assertAlmostEqual(world[hand].translation.x, old_world[hand].translation.x, places=5)
                    self.assertAlmostEqual(world[hand].translation.z, old_world[hand].translation.z, places=5)
                    self.assertLess(world[hand].to_quaternion().rotation_difference(old_world[hand].to_quaternion()).angle, 1e-4)
            for clip in report['clips']:
                self.assertEqual(clip['key_count'], 106)
                self.assertEqual(clip['midpoint_count'], 105)
                self.assertEqual(len(clip['samples']), 211)
                self.assertLess(clip['maximum_plane_error_metres'], .001)
                for sample in clip['samples']:
                    if sample['source_key']:
                        self.assertAlmostEqual(min(sample['after_foot_min_metres'].values()), -.028, places=6)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), file_hash)

    def test_missing_foot_surface_and_duplicate_clips_fail(self):
        document, binary = read_glb(HERE / 'review/attack-bank-candidate/base.glb')
        with self.assertRaisesRegex(ValueError, 'three distinct'):
            ground_attack_feet(copy.deepcopy(document), binary, [BANK[0]] * 3)
        for node in document['nodes']:
            if node.get('name', '').startswith(('R_Foot', 'R_Toe')):
                node['name'] = 'Renamed_' + node['name']
        with self.assertRaisesRegex(ValueError, 'both feet'):
            ground_attack_feet(document, binary, BANK)


if __name__ == '__main__':
    unittest.main(argv=[__file__])
