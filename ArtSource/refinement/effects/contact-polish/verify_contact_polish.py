"""Offline mesh, lifetime and trajectory checks for contact-polish candidates."""
import hashlib
import json
import math
import struct
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from contact_motion import contact_basis, sample_particle, sample_ground_particle


class TrajectoryChecks(unittest.TestCase):
    def setUp(self):
        self.particle = {'initial_position_local_m': [0, 0, 0],
                         'initial_velocity_local_mps': [1, 0, .2],
                         'lifetime_s': .2, 'opacity_keys': [[0, 1], [.2, 0]]}

    def test_actual_tangent_and_stage_gravity(self):
        result = sample_particle(self.particle, .1, (1, 2, 3), (0, 0, 1), (1, 0, 0))
        for actual, expected in zip(result['position_stage_m'], (1.1, 1.95095, 3.02)):
            self.assertAlmostEqual(expected, actual)
        self.assertAlmostEqual(.5, result['opacity'])

    def test_rotated_surface_does_not_rotate_gravity(self):
        result = sample_particle(self.particle, .1, (0, 0, 0), (0, 1, 0), (1, 0, 0))
        self.assertAlmostEqual(-.02905, result['position_stage_m'][1])
        self.assertAlmostEqual(0, result['position_stage_m'][2])

    def test_unavailable_tangent_is_rejected(self):
        for tangent in [(0, 0, 1), (0, 0, 0), (math.nan, 0, 0), (1, 0)]:
            with self.assertRaises(ValueError):
                contact_basis((0, 0, 1), tangent)

    def test_expired_or_unborn_particles_do_not_restart(self):
        for age in (-.01, .2, 10, math.nan):
            self.assertIsNone(sample_particle(self.particle, age, (0, 0, 0), (0, 0, 1), (1, 0, 0)))

    def test_ground_base_stays_above_actual_surface(self):
        particle = dict(self.particle, initial_velocity_local_mps=[.3, 0, .1])
        anchor = (0, .028, -2)
        result = sample_ground_particle(particle, .15, anchor, (0, 1, 0), (1, 0, 0))
        self.assertAlmostEqual(anchor[1], result['position_stage_m'][1])
        self.assertGreater(result['position_stage_m'][0], anchor[0])

    def test_ground_constraint_uses_surface_normal(self):
        particle = dict(self.particle, initial_velocity_local_mps=[.3, 0, -.5])
        result = sample_ground_particle(particle, .1, (0, 0, 0), (0, 0, 1), (1, 0, 0))
        self.assertAlmostEqual(0, result['position_stage_m'][2])
        self.assertLess(result['position_stage_m'][1], 0)


def read_glb(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20 + size])
    bin_size, kind = struct.unpack_from('<II', raw, 20 + size)
    assert kind == 0x004e4942
    return document, raw[28 + size:28 + size + bin_size]


def positions(document, binary, node):
    primitive = document['meshes'][node['mesh']]['primitives'][0]
    accessor = document['accessors'][primitive['attributes']['POSITION']]
    view = document['bufferViews'][accessor['bufferView']]
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', 12)
    return [struct.unpack_from('<fff', binary, start + i*stride) for i in range(accessor['count'])]


def main():
    report = []
    candidates = [
        ('metal', 'metal_contact_polish', 'motion.json'),
        ('wet', 'wet_cloth_contact', 'motion.json'),
        ('ground', 'dodge_ground_polish', 'dodge_motion.json'),
        ('ground', 'landing_ground_polish', 'landing_motion.json'),
    ]
    for family, name, motion_name in candidates:
        path = HERE / family / (name + '.glb')
        document, binary = read_glb(path)
        assert not document.get('animations') and not document.get('skins')
        motion = json.loads((path.parent / motion_name).read_text())
        assert motion['gravity_stage_mps2'] == [0, -9.81, 0]
        particles = motion['particles']
        nodes = {node.get('name'): node for node in document['nodes'] if 'mesh' in node}
        assert len(nodes) == len([node for node in document['nodes'] if 'mesh' in node])
        if family == 'metal':
            assert 8 <= len(particles) <= 14
            assert 'core_star' in nodes
            assert motion['cores'][0]['normal']['lifetime_s'] == .065
            assert motion['cores'][0]['parry']['lifetime_s'] == .09
        elif family == 'wet':
            drops = [p for p in particles if p['type'] == 'droplet']
            assert 6 <= len(drops) <= 10
        else:
            assert 6 <= len(particles) <= 10
            assert motion['anchor_normal_offset_m'] == .002
        for particle in particles:
            assert particle['node'] in nodes
            maximum_life = .45 if family == 'ground' else .32
            assert .18 <= particle['lifetime_s'] <= maximum_life
            assert all(math.isfinite(v) for v in particle['initial_position_local_m'] + particle['initial_velocity_local_mps'])
            keys = particle['opacity_keys']
            assert all(0 <= value <= 1 for _, value in keys)
            assert all(a[0] < b[0] for a, b in zip(keys, keys[1:]))
            points = positions(document, binary, nodes[particle['node']])
            assert all(math.isfinite(v) for point in points for v in point)
            if family == 'ground':
                assert min(point[2] for point in points) >= -1e-6
            if family == 'wet' and particle['type'] == 'droplet':
                diameter = max(math.dist(a, b) for a in points for b in points)
                assert .0019 <= diameter <= .0041, (particle['node'], diameter)
            assert sample_particle(particle, particle['lifetime_s'], (0, 0, 0), (0, 0, 1), (1, 0, 0)) is None
        report.append({'asset': path.relative_to(HERE).as_posix(),
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'mesh_nodes': len(nodes), 'particles': len(particles), 'animations': 0})
    (HERE / 'verification.json').write_text(json.dumps({'status': 'OFFLINE_ASSET_AND_TRAJECTORY_PASS',
        'runtime_status': 'Root integration and PICO verification required', 'assets': report}, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TrajectoryChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    main()
