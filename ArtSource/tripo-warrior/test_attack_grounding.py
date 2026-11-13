"""Small LBS invariants for the one canonical guard grounding frame."""

import copy
import math
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from attack_grounding import CANONICAL_CLIPS, GROUNDING_POLICY, ground_canonical_guard_feet
from attack_profiles import animation_tracks, hierarchy, pose_world
from prepare_rigged_warrior import accessor_bytes, animation_signature


def source_timelines(overhead_rate=60):
    timelines = {}
    for name in CANONICAL_CLIPS:
        if name == 'idle':
            times = [frame / 60 for frame in range(91)]
        elif name == 'walk':
            times = sorted({*[frame / 120 for frame in range(181)], 19 / 36, 26 / 36, 40 / 36, 47 / 36})
        else:
            rate = overhead_rate if name == 'attack_overhead' else 60
            times = [frame / rate for frame in range(int(1.75 * rate) + 1)]
        timelines[name] = [struct.unpack('<f', struct.pack('<f', time))[0] for time in times]
    return timelines


def fixture(animate_parent=False, overhead_rate=60):
    """Two real weighted sole surfaces, different key grids and a nonunit parent."""
    document = {
        'nodes': [{'name': 'Actor', 'children': [1, 5]},
                  {'name': 'Armature', 'scale': [.5, .5, .5], 'children': [2]},
                  {'name': 'BoneRoot', 'children': [3, 4]},
                  {'name': 'L_Foot'}, {'name': 'R_Foot'}, {'name': 'Body', 'mesh': 0, 'skin': 0}],
        'scenes': [{'nodes': [0]}], 'scene': 0,
        'skins': [{'joints': [2, 3, 4]}], 'meshes': [{'primitives': []}],
        'accessors': [], 'bufferViews': [], 'buffers': [{'byteLength': 0}], 'animations': [],
    }
    binary = bytearray()

    def accessor(rows, kind):
        binary.extend(b'\0' * (-len(binary) % 4))
        start = len(binary)
        for row in rows:
            binary.extend(struct.pack('<' + 'f' * len(row), *row))
        view = len(document['bufferViews'])
        document['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(binary) - start})
        index = len(document['accessors'])
        document['accessors'].append({'bufferView': view, 'componentType': 5126, 'type': kind, 'count': len(rows)})
        return index

    positions = accessor([[-.1, 0, 0], [-.1, .02, .1], [.1, 0, 0], [.1, .02, .1]], 'VEC3')
    palettes = accessor([[1, 0, 0, 0], [1, 0, 0, 0], [2, 0, 0, 0], [2, 0, 0, 0]], 'VEC4')
    weights = accessor([[1, 0, 0, 0]] * 4, 'VEC4')
    identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    document['skins'][0]['inverseBindMatrices'] = accessor([identity] * 3, 'MAT4')
    document['meshes'][0]['primitives'].append({'attributes': {
        'POSITION': positions, 'JOINTS_0': palettes, 'WEIGHTS_0': weights}})
    for name in CANONICAL_CLIPS:
        times = source_timelines(overhead_rate)[name]
        values = [(0, .1 if name in {'idle', 'walk'} else .1 + .04 * math.sin(math.pi * time / 1.75), 0)
                  for time in times]
        document['animations'].append({'name': name,
            'samplers': [{'input': accessor([(time,) for time in times], 'SCALAR'),
                          'output': accessor(values, 'VEC3'),
                          'interpolation': 'STEP' if name in {'idle', 'walk'} else 'LINEAR'}],
            'channels': [{'sampler': 0, 'target': {'node': 2, 'path': 'translation'}}]})
        animation = document['animations'][-1]
        animation['samplers'].append({'input': animation['samplers'][0]['input'],
            'output': accessor([(0, 0, 0, 1)] * len(times), 'VEC4'), 'interpolation': 'STEP'})
        animation['channels'].append({'sampler': 1, 'target': {'node': 3, 'path': 'rotation'}})
        if animate_parent and name == 'idle':
            animation['samplers'].append({'input': animation['samplers'][0]['input'],
                'output': accessor([(1 + time * .01, 1, 1) for time in times], 'VEC3'), 'interpolation': 'LINEAR'})
            animation['channels'].append({'sampler': 2, 'target': {'node': 1, 'path': 'scale'}})
    untouched_clip = copy.deepcopy(document['animations'][-1])
    untouched_clip['name'] = 'turn'
    document['animations'].append(untouched_clip)
    document['buffers'][0]['byteLength'] = len(binary)
    return document, bytes(binary)


class CanonicalGroundingTests(unittest.TestCase):
    def test_one_shift_preserves_clocks_curves_and_authored_residuals(self):
        document, binary = fixture()
        original = copy.deepcopy(document)
        result, report = ground_canonical_guard_feet(document, binary, source_timelines())
        self.assertEqual(report['policy'], GROUNDING_POLICY)
        self.assertEqual(result[:len(binary)], binary)
        for field in ('nodes', 'meshes', 'skins', 'scenes'):
            self.assertEqual(document[field], original[field])
        self.assertAlmostEqual(report['constant_world_root_shift_metres'], -.078, places=6)
        self.assertAlmostEqual(report['constant_local_root_shift'][1], -.156, places=6)
        _, parents, order = hierarchy(document)
        self.assertEqual(animation_signature(original, binary, original['animations'][-1]),
                         animation_signature(document, result, document['animations'][-1]))
        for before, after, clip_report in zip(original['animations'], document['animations'], report['clips']):
            self.assertEqual(before['channels'], after['channels'])
            self.assertEqual(before['samplers'][0]['interpolation'], after['samplers'][0]['interpolation'])
            self.assertEqual(accessor_bytes(original, binary, before['samplers'][1]['output']),
                             accessor_bytes(document, result, after['samplers'][1]['output']))
            self.assertEqual(before['samplers'][1], after['samplers'][1])
            self.assertEqual(accessor_bytes(original, binary, before['samplers'][0]['input']),
                             accessor_bytes(document, result, after['samplers'][0]['input']))
            old_tracks, _ = animation_tracks(original, binary, before, require_attack_range=False)
            tracks, _ = animation_tracks(document, result, after, require_attack_range=False)
            for sample in clip_report['samples']:
                time = sample['source_seconds']
                old_world = pose_world(original, old_tracks, time, parents, order)
                world = pose_world(document, tracks, time, parents, order)
                for index in (2, 3, 4):
                    difference = world[index].translation - old_world[index].translation
                    self.assertAlmostEqual(difference.x, 0, places=6)
                    self.assertAlmostEqual(difference.y, report['constant_world_root_shift_metres'], places=6)
                    self.assertAlmostEqual(difference.z, 0, places=6)
                self.assertAlmostEqual(sample['root_shift_metres'], report['constant_world_root_shift_metres'], places=6)
            expected_count = {'idle': 91, 'walk': 185}.get(after['name'], 106)
            self.assertEqual(clip_report['key_count'], expected_count)
            self.assertEqual(len(clip_report['samples']), 2 * expected_count - 1)
            # Authored attack lift survives; no per-frame plane clamp is permitted.
            if after['name'].startswith('attack'):
                self.assertGreater(clip_report['maximum_plane_error_metres'], .019)
            else:
                self.assertLess(clip_report['maximum_plane_error_metres'], 1e-6)
            self.assertEqual(clip_report['before_semantics_sha256'], animation_signature(original, binary, before))
            self.assertEqual(clip_report['after_semantics_sha256'], animation_signature(document, result, after))

    def test_v9_overhead_preserves_all211_keys_with_the_same_one_guard_shift(self):
        document, binary = fixture(overhead_rate=120)
        original = copy.deepcopy(document)
        timelines = source_timelines(overhead_rate=120)
        result, report = ground_canonical_guard_feet(document, binary, timelines)
        self.assertAlmostEqual(report['constant_world_root_shift_metres'], -.078, places=6)
        expected = {'idle': 91, 'walk': 185, 'attack_overhead': 211, 'attack_left': 106, 'attack_right': 106}
        for before, after, row in zip(original['animations'], document['animations'], report['clips']):
            self.assertEqual(row['key_count'], expected[row['clip']])
            self.assertEqual(len(row['samples']), expected[row['clip']] * 2 - 1)
            self.assertEqual(accessor_bytes(original, binary, before['samplers'][0]['input']),
                             accessor_bytes(document, result, after['samplers'][0]['input']))
        self.assertEqual(report['policy'], GROUNDING_POLICY)

    def test_grounding_rejects_per_clip_count_and_boundary_mismatch_instead_of_resampling(self):
        for changed_clip, changed_index in [('attack_overhead', -1), ('attack_left', 1)]:
            document, binary = fixture(overhead_rate=120)
            timelines = source_timelines(overhead_rate=120)
            timelines[changed_clip][changed_index] += .00001
            with self.assertRaisesRegex(ValueError, 'frozen source timeline'):
                ground_canonical_guard_feet(document, binary, timelines)
        document, binary = fixture(overhead_rate=120)
        timelines = source_timelines(overhead_rate=120)
        timelines['attack_overhead'] = source_timelines()['attack_overhead']
        with self.assertRaisesRegex(ValueError, 'frozen source timeline'):
            ground_canonical_guard_feet(document, binary, timelines)

    def test_requires_five_distinct_clips_and_measured_both_feet(self):
        document, binary = fixture()
        for bad_names in (CANONICAL_CLIPS[2:], ['idle'] * 5):
            with self.assertRaisesRegex(ValueError, 'five distinct'):
                ground_canonical_guard_feet(copy.deepcopy(document), binary, bad_names)
        document['nodes'][4]['name'] = 'MissingFoot'
        with self.assertRaisesRegex(ValueError, 'both feet'):
            ground_canonical_guard_feet(document, binary, source_timelines())

    def test_refuses_animated_root_parent_frame(self):
        document, binary = fixture(animate_parent=True)
        with self.assertRaisesRegex(ValueError, 'fixed root parent frame'):
            ground_canonical_guard_feet(document, binary, source_timelines())

    def test_refuses_old_timeline_or_changed_root_interpolation(self):
        for clip_name in ('idle', 'walk', 'attack_overhead'):
            document, binary = fixture()
            clip = next(row for row in document['animations'] if row['name'] == clip_name)
            clip['samplers'][0]['interpolation'] = 'LINEAR' if clip_name in {'idle', 'walk'} else 'STEP'
            with self.assertRaisesRegex(ValueError, 'unchanged .* root keys'):
                ground_canonical_guard_feet(document, binary, source_timelines())
        document, binary = fixture()
        clip = document['animations'][0]
        document['accessors'][clip['samplers'][0]['input']]['count'] -= 1
        for sampler in clip['samplers']:
            document['accessors'][sampler['output']]['count'] -= 1
        with self.assertRaisesRegex(ValueError, 'frozen source timeline'):
            ground_canonical_guard_feet(document, binary, source_timelines())


if __name__ == '__main__':
    unittest.main(argv=[__file__])
