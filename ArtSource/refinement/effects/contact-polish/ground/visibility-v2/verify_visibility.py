"""Verify the one material/alpha visibility revision against immutable v1."""
import copy
import hashlib
import importlib.util
import json
import math
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
V1 = HERE.parent
spec = importlib.util.spec_from_file_location('readonly_ground_checks', V1 / 'verify_ground.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


def verify_variant(kind):
    name = kind + '_ground_polish.glb'
    source, source_bin = helper.read_asset(V1 / name)
    candidate, candidate_bin = helper.read_asset(HERE / name)
    assert candidate_bin[:len(source_bin)] == source_bin
    for key in ('nodes', 'scenes', 'scene', 'skins', 'animations', 'images', 'textures',
                'samplers', 'extensionsUsed', 'extensionsRequired'):
        assert source.get(key) == candidate.get(key), key
    assert candidate['accessors'][:len(source['accessors'])] == source['accessors']
    assert candidate['bufferViews'][:len(source['bufferViews'])] == source['bufferViews']
    geometry_streams = 0
    zero_edges = 0
    changed_alpha_vertices = 0
    old_max, new_max = 0.0, 0.0
    for old_mesh, new_mesh in zip(source['meshes'], candidate['meshes']):
        assert old_mesh['name'] == new_mesh['name']
        for old, new in zip(old_mesh['primitives'], new_mesh['primitives']):
            original, current = copy.deepcopy(old), copy.deepcopy(new)
            original['attributes'].pop('COLOR_0'); current['attributes'].pop('COLOR_0')
            assert original == current
            for attr in ('POSITION', 'NORMAL'):
                a = helper.stream(source, source_bin, old['attributes'][attr])
                b = helper.stream(candidate, candidate_bin, new['attributes'][attr])
                assert a == b
                geometry_streams += 1
            assert helper.stream(source, source_bin, old['indices']) == helper.stream(candidate, candidate_bin, new['indices'])
            colors_before = helper.stream(source, source_bin, old['attributes']['COLOR_0'])
            colors_after = helper.stream(candidate, candidate_bin, new['attributes']['COLOR_0'])
            assert len(colors_before) == len(colors_after)
            for a, b in zip(colors_before, colors_after):
                assert a[:3] == b[:3]
                expected = 0.0 if a[3] == 0 else min(.65, a[3] * 1.8)
                assert abs(b[3] - expected) < 1e-7
                if a[3] == 0:
                    assert b[3] == 0
                    zero_edges += 1
                changed_alpha_vertices += int(a[3] != b[3])
                old_max, new_max = max(old_max, a[3]), max(new_max, b[3])
    assert len(source['meshes']) == len(candidate['meshes']) == 8
    assert len(source['materials']) == len(candidate['materials'])
    for old, new in zip(source['materials'], candidate['materials']):
        a, b = copy.deepcopy(old), copy.deepcopy(new)
        a['pbrMetallicRoughness'].pop('baseColorFactor')
        b['pbrMetallicRoughness'].pop('baseColorFactor')
        assert a == b
        assert new['pbrMetallicRoughness']['baseColorFactor'] == [.35, .32, .28, 1.0]
        assert new['emissiveFactor'] == [0, 0, 0]
    old_motion = json.loads((V1 / (kind + '_motion.json')).read_text())
    new_motion = json.loads((HERE / (kind + '_motion.json')).read_text())
    old_copy, new_copy = copy.deepcopy(old_motion), copy.deepcopy(new_motion)
    for old, new, a, b in zip(old_motion['particles'], new_motion['particles'], old_copy['particles'], new_copy['particles']):
        old_peak = max(alpha for _, alpha in old['opacity_keys'])
        assert [t for t, _ in old['opacity_keys']] == [t for t, _ in new['opacity_keys']]
        for (_, alpha), (_, changed) in zip(old['opacity_keys'], new['opacity_keys']):
            assert abs(changed - min(.85, alpha * .85 / old_peak)) < 1e-12
        a.pop('opacity_keys'); b.pop('opacity_keys')
    assert old_copy == new_copy
    source_peak = max(a for _, a in old_motion['particles'][0]['opacity_keys'])
    old_effective = source['materials'][0]['pbrMetallicRoughness']['baseColorFactor'][3] * old_max * source_peak
    new_effective = new_max * .85
    return {'asset': name, 'source_sha256': hashlib.sha256((V1 / name).read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256((HERE / name).read_bytes()).hexdigest(),
            'original_binary_prefix_unchanged': True, 'geometry_streams_compared': geometry_streams,
            'zero_alpha_edge_vertices_preserved': zero_edges, 'changed_alpha_vertices': changed_alpha_vertices,
            'all_rgb_unchanged': True, 'only_color_alpha_and_base_color_changed': True,
            'all_nonopacity_motion_fields_unchanged': True,
            'source_max_vertex_alpha': old_max, 'candidate_max_vertex_alpha': new_max,
            'source_center_effective_peak_alpha': old_effective,
            'candidate_center_effective_peak_alpha': new_effective,
            'center_effective_alpha_ratio': new_effective / old_effective}


class VisibilityBounds(unittest.TestCase):
    def test_alpha_edges_and_cap(self):
        self.assertEqual(0, min(.65, 0 * 1.8))
        self.assertEqual(.65, min(.65, .7 * 1.8))
        self.assertAlmostEqual(.36, min(.65, .2 * 1.8))

    def test_motion_scaling_preserves_zero_and_bound(self):
        peak = .55
        for alpha in (0, .385, .55):
            changed = min(.85, alpha * .85 / peak)
            self.assertGreaterEqual(changed, 0)
            self.assertLessEqual(changed, .85)
        self.assertEqual(0, min(.85, 0 * .85 / peak))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(VisibilityBounds))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {'status': 'MATERIAL_ALPHA_ONLY_SOURCE_CHECKS_PASS',
              'visual_status': 'Root actual GLB frame review pending',
              'assets': [verify_variant(kind) for kind in ('dodge', 'landing')]}
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
