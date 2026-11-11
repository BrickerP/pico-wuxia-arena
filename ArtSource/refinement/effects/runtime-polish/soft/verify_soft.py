"""Independent dry-soft asset checks, including source preservation and lifetime bounds."""
import importlib.util
import json
import math
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('soft_builder', HERE / 'build_soft.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
spec = importlib.util.spec_from_file_location('contact_motion', HERE.parents[1] / 'contact-polish/contact_motion.py')
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


class SoftChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.source_binary = builder.read_glb(builder.SOURCE)
        cls.doc, cls.binary = builder.read_glb(HERE / 'soft_contact_polish.glb')
        cls.motion = json.loads((HERE / 'motion.json').read_text())
        cls.nodes = {n['name']: n for n in cls.doc['nodes']}
        cls.source_nodes = {n['name']: n for n in cls.source['nodes']}

    def test_named_meshes_materials_and_no_animation(self):
        expected = {'core', 'scar'} | {f'chip_{i:02d}' for i in range(12)}
        self.assertEqual(expected, {n['name'] for n in self.doc['nodes'] if 'mesh' in n})
        self.assertEqual(self.source['materials'], self.doc['materials'])
        self.assertFalse(self.doc.get('animations'))
        self.assertFalse(self.doc.get('extensionsUsed'))

    def test_source_shapes_and_rgba_are_preserved(self):
        for name, scale in [('core', 1.85), ('scar', 1.25)]:
            old, old_indices, old_material = builder.mesh_data(self.source, self.source_binary, self.source_nodes[name])
            new, indices, material = builder.mesh_data(self.doc, self.binary, self.nodes[name])
            self.assertEqual(old_indices, indices)
            self.assertEqual(old_material, material)
            self.assertEqual(old['COLOR_0'], new['COLOR_0'])
            for a, b in zip(old['POSITION'], new['POSITION']):
                for axis in range(3):
                    self.assertAlmostEqual(a[axis] * (scale if axis < 2 else 1), b[axis], places=7)

    def test_each_particle_uses_source_component_and_local_origin(self):
        old, old_indices, old_material = builder.mesh_data(self.source, self.source_binary, self.source_nodes['debris'])
        groups = builder.components(old_indices)
        for number, source_pair in enumerate(builder.SELECTED):
            selected = sorted(groups[source_pair * 2] + groups[source_pair * 2 + 1])
            origin = old['POSITION'][groups[source_pair * 2][0]]
            new, indices, material = builder.mesh_data(self.doc, self.binary, self.nodes[f'chip_{number:02d}'])
            self.assertEqual(old_material, material)
            self.assertEqual([old['COLOR_0'][i] for i in selected], new['COLOR_0'])
            for index, actual in zip(selected, new['POSITION']):
                for axis in range(3):
                    self.assertAlmostEqual(old['POSITION'][index][axis] - origin[axis], actual[axis], places=7)
            self.assertEqual(14, len(indices) // 3)
            self.assertLess(max(math.hypot(*p) for p in new['POSITION']), .08)

    def test_finite_mesh_attributes_and_valid_indices(self):
        for node in self.doc['nodes']:
            if 'mesh' not in node:
                continue
            attributes, indices, material = builder.mesh_data(self.doc, self.binary, node)
            count = len(attributes['POSITION'])
            self.assertTrue(all(0 <= i < count for i in indices))
            self.assertTrue(all(math.isfinite(v) for rows in attributes.values() for row in rows for v in row))
            self.assertTrue(all(0 <= color[3] <= 1 for color in attributes['COLOR_0']))

    def test_lifetimes_expiry_and_independent_stage_gravity(self):
        self.assertEqual(12, len(self.motion['particles']))
        self.assertEqual([0, -9.81, 0], self.motion['gravity_stage_mps2'])
        for particle in self.motion['particles']:
            lifetime = particle['lifetime_s']
            self.assertTrue(.18 <= lifetime <= .32)
            for age in (-.01, lifetime, lifetime + 10, math.nan):
                self.assertIsNone(reference.sample_particle(particle, age, (0, 1.2, 0), (0, 0, 1), (1, 0, 0)))
            age = .10
            sample = reference.sample_particle(particle, age, (0, 1.2, 0), (0, 1, 0), (1, 0, 0))
            expected_y = 1.2 + particle['initial_position_local_m'][2] + particle['initial_velocity_local_mps'][2] * age - .5 * 9.81 * age * age
            self.assertAlmostEqual(expected_y, sample['position_stage_m'][1])
            self.assertTrue(0 <= sample['opacity'] <= 1)
        velocities = {tuple(p['initial_velocity_local_mps']) for p in self.motion['particles']}
        self.assertEqual(12, len(velocities))

    def test_unavailable_tangent_rejected_and_core_bounded(self):
        for tangent in ((0, 0, 1), (0, 0, 0), (math.nan, 1, 0)):
            with self.assertRaises(ValueError):
                reference.sample_particle(self.motion['particles'][0], .05, (0, 0, 0), (0, 0, 1), tangent)
        durations = {core['node']: core['normal']['lifetime_s'] for core in self.motion['cores']}
        self.assertEqual({'core': .065, 'scar': .085}, durations)
        self.assertIn('no water', self.motion['contact_semantics'])


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SoftChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    (HERE / 'verification.json').write_text(json.dumps({'suite': 'SoftChecks', 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(),
        'scope': 'Offline source/material/mesh contract and stateless trajectory only; PICO runtime unverified'}, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
