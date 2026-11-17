"""Whole-scene preservation, genuine solid module and PBR-frame checks."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compose_entry as build
from verify_environment import active_nodes, world_primitives


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EntryChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pairs = []
        for label, (path, expected) in build.SOURCES.items():
            out = HERE / f'courtyard_entry_finish_{label}.glb'
            cls.pairs.append((path, expected, *build.read(path), out, *build.read(out)))

    def test_inputs_are_exact_fixed_sources(self):
        for path, expected, *_ in self.pairs:
            self.assertEqual(sha(path), expected)

    def test_bad_input_identity_rejected_without_writing(self):
        md, mb = build.read(HERE / 'entry_module.glb')
        for path, expected, *_ in self.pairs:
            with self.assertRaisesRegex(ValueError, 'identity'):
                build.compose(path, '0' * 64, md, mb)

    def test_source_binary_prefix_and_all_texture_bytes_preserved(self):
        for _, _, original, blob, _, candidate, out in self.pairs:
            count = original['buffers'][0]['byteLength']
            self.assertEqual(out[:count], blob[:count])
            for key in ['materials', 'images', 'textures', 'samplers', 'extensionsUsed', 'extensionsRequired']:
                self.assertEqual(candidate.get(key), original.get(key), key)

    def test_all_non_target_meshes_and_vertex_streams_unchanged(self):
        for _, _, original, blob, _, candidate, out in self.pairs:
            masks = build.select_removed(original, blob)
            self.assertEqual({k: int(v.sum()) for k, v in masks.items()}, {(22, 0): 76, (36, 0): 550, (36, 1): 20})
            for mi, mesh in enumerate(original['meshes']):
                for pi, prim in enumerate(mesh['primitives']):
                    target = candidate['meshes'][mi]['primitives'][pi]
                    if (mi, pi) not in masks:
                        self.assertEqual(target, prim, (mi, pi))
                    else:
                        self.assertEqual({k: v for k, v in target.items() if k != 'indices'},
                                         {k: v for k, v in prim.items() if k != 'indices'})
                        indices = build.rows(original, blob, prim['indices']).reshape(-1, 3)
                        np.testing.assert_array_equal(build.rows(candidate, out, target['indices']).reshape(-1, 3),
                                                      indices[~masks[(mi, pi)]])

    def test_nodes_windows_lanterns_floor_and_anchors_preserved(self):
        for _, _, original, _, _, candidate, _ in self.pairs:
            root = original['scenes'][original.get('scene', 0)]['nodes'][0]
            for ni, node in enumerate(original['nodes']):
                if ni == root:
                    expected = copy.deepcopy(node)
                    expected['children'].append(len(candidate['nodes']) - 1)
                    self.assertEqual(candidate['nodes'][ni], expected)
                else:
                    self.assertEqual(candidate['nodes'][ni], node)
            self.assertEqual(len(active_nodes(candidate)), len(candidate['nodes']))

    def test_new_solid_construction_and_socket_clearance(self):
        record = json.loads((HERE / 'construction.json').read_text())
        self.assertEqual(len(record['topology']), 10)
        for part in record['topology'].values():
            self.assertEqual(part['non_manifold_edges'], 0)
            self.assertGreater(part['volume_m3'], 0)
        self.assertEqual(record['textures_added'], 0)
        posts = [p for p in record['parts'] if 'Post_' in p['part']]
        self.assertEqual(len(posts), 2)
        self.assertTrue(all(p['foot_m'] == [.23, .29] for p in posts))

    def test_new_primitives_have_valid_explicit_TBN_no_degenerate_triangles(self):
        for _, _, original, _, _, candidate, out in self.pairs:
            for mesh in candidate['meshes'][len(original['meshes']):]:
                for prim in mesh['primitives']:
                    a = prim['attributes']
                    for key in ['POSITION', 'NORMAL', 'TEXCOORD_0', 'TANGENT']:
                        self.assertIn(key, a)
                    positions = build.rows(candidate, out, a['POSITION']).astype(float)
                    normals = build.rows(candidate, out, a['NORMAL']).astype(float)
                    tangent = build.rows(candidate, out, a['TANGENT']).astype(float)
                    indices = build.rows(candidate, out, prim['indices']).reshape(-1, 3)
                    self.assertTrue(np.isfinite(positions).all() and np.isfinite(tangent).all())
                    np.testing.assert_allclose(np.linalg.norm(tangent[:, :3], axis=1), 1, atol=2e-6)
                    self.assertLess(float(np.max(np.abs((normals * tangent[:, :3]).sum(1)))), 2e-6)
                    self.assertTrue(np.isin(tangent[:, 3], [-1, 1]).all())
                    tri = positions[indices]
                    self.assertTrue(np.all(np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) > 1e-10))

    def test_new_timber_stays_outside_combat_clearance_and_no_runtime_layers_added(self):
        for _, _, original, _, _, candidate, out in self.pairs:
            for mesh in candidate['meshes'][len(original['meshes']):]:
                for prim in mesh['primitives']:
                    positions = build.rows(candidate, out, prim['attributes']['POSITION'])
                    self.assertLess(float(positions[:, 2].max()), -4.6)
            self.assertFalse(candidate.get('animations'))
            self.assertFalse(candidate.get('cameras'))
            self.assertNotIn('KHR_lights_punctual', candidate.get('extensions', {}))

    def test_png_ktx_same_geometry_budget_and_material_mapping(self):
        _, _, source, _, _, p, pb = self.pairs[0]
        _, _, _, _, _, k, kb = self.pairs[1]
        self.assertEqual(build.budget(p, pb), build.budget(k, kb))
        self.assertLessEqual(build.budget(p, pb)['node_expanded_triangles'], 270000)
        self.assertEqual(len(p['materials']), 32)
        self.assertEqual(len(p['images']), 50)
        for mi in range(len(source['meshes']), len(p['meshes'])):
            for a, b in zip(p['meshes'][mi]['primitives'], k['meshes'][mi]['primitives']):
                self.assertEqual(a['material'], b['material'])
                for attr in a['attributes']:
                    np.testing.assert_array_equal(build.rows(p, pb, a['attributes'][attr]), build.rows(k, kb, b['attributes'][attr]))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EntryChecks))
    report = {'status': 'passed' if result.wasSuccessful() else 'failed', 'tests': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'scope': 'Full private scene/non-target/solid construction/PBR stream checks; not native appearance or terminal performance.'}
    (HERE / 'review/verification.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
