"""Offline mesh-base and reference-sampler checks for courtyard ground effects."""
import hashlib
import importlib.util
import json
import math
import struct
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('contact_motion', HERE.parent / 'contact_motion.py')
motion_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motion_helper)


def stream(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    code = {5123: 'H', 5126: 'f'}[accessor['componentType']]
    size = struct.calcsize('<' + code * width)
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return [struct.unpack_from('<' + code * width, binary, offset + row * view.get('byteStride', size))
            for row in range(accessor['count'])]


def read_asset(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    size = struct.unpack_from('<I', raw, 12)[0]
    document = json.loads(raw[20:20 + size])
    binary_size = struct.unpack_from('<I', raw, 20 + size)[0]
    return document, raw[28 + size:28 + size + binary_size]


def check_asset(kind):
    recipe = json.loads((HERE / (kind + '_motion.json')).read_text())
    path = HERE / recipe['asset']
    document, binary = read_asset(path)
    assert not document.get('animations') and not document.get('extensionsUsed')
    assert len(recipe['particles']) == len(document['meshes']) == 8
    assert recipe['anchor_normal_offset_m'] == .002
    assert recipe['ground_constraint'] == 'particle base >= anchor plane'
    assert recipe['gravity_stage_mps2'] == [0.0, -9.81, 0.0]
    assert recipe['waves'] == []
    geometry = {}
    triangles = 0
    for particle in recipe['particles']:
        assert particle['initial_position_local_m'][2] == 0
        assert .25 <= particle['lifetime_s'] <= .45
        assert particle['opacity_keys'][-1] == [particle['lifetime_s'], 0.0]
        assert 'fixed TBN' in particle['orientation_policy']
        node = next(node for node in document['nodes'] if node['name'] == particle['node'])
        assert node['translation'] == particle['initial_position_local_m']
        primitive = document['meshes'][node['mesh']]['primitives'][0]
        positions = stream(document, binary, primitive['attributes']['POSITION'])
        normals = stream(document, binary, primitive['attributes']['NORMAL'])
        indices = [v[0] for v in stream(document, binary, primitive['indices'])]
        assert all(math.isfinite(v) for position in positions for v in position)
        assert min(p[2] for p in positions) >= 0
        assert abs(min(p[2] for p in positions)) < 1e-10
        assert .019999 <= max(p[2] for p in positions) <= .030001
        assert abs(max(p[2] for p in positions) - particle['height_m']) < 1e-8
        assert all(abs(math.sqrt(sum(v*v for v in n)) - 1) < 1e-5 for n in normals)
        assert all(0 <= index < len(positions) for index in indices)
        triangles += len(indices) // 3
        geometry[particle['node']] = positions
    assert triangles == 192
    minimum_clearance = float('inf')
    for n in ((0, 1, 0), (0, .8, .6), (.2, .95, .24)):
        normal = motion_helper.unit(n)
        surface = (.4, 1.7, -2.1)
        anchor = tuple(surface[i] + normal[i] * .002 for i in range(3))
        for particle in recipe['particles']:
            for index in range(64):
                age = particle['lifetime_s'] * index / 64
                sample = motion_helper.sample_ground_particle(particle, age, anchor, normal, (1, 0, 0))
                assert sample is not None
                height = motion_helper.dot(tuple(sample['position_stage_m'][i] - anchor[i] for i in range(3)), normal)
                minimum_clearance = min(minimum_clearance, height)
                assert height >= -1e-12
                assert height + min(v[2] for v in geometry[particle['node']]) >= -1e-12
            assert motion_helper.sample_ground_particle(particle, -0.001, anchor, normal, (1, 0, 0)) is None
            assert motion_helper.sample_ground_particle(particle, particle['lifetime_s'], anchor, normal, (1, 0, 0)) is None
    maximum_diameter = 0.0
    for step in range(101):
        age = step / 100 * max(p['lifetime_s'] for p in recipe['particles'])
        points = []
        for particle in recipe['particles']:
            sample = motion_helper.sample_ground_particle(particle, age, (0, .002, 0), (0, 1, 0), (1, 0, 0))
            if sample is None:
                continue
            x, _, z = sample['position_stage_m']
            points.extend((x + p[0], z - p[1]) for p in geometry[particle['node']])
        if points:
            extent_x = max(p[0] for p in points) - min(p[0] for p in points)
            extent_z = max(p[1] for p in points) - min(p[1] for p in points)
            maximum_diameter = max(maximum_diameter, math.hypot(extent_x, extent_z))
    assert maximum_diameter <= .40
    return {'asset': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'particles': 8, 'triangles': triangles, 'geometry_local_z_nonnegative': True,
            'tested_ground_normals': 3, 'minimum_base_clearance_m': minimum_clearance,
            'maximum_live_horizontal_bbox_diagonal_m': maximum_diameter}


class GroundBoundaryChecks(unittest.TestCase):
    def test_ground_particle_stays_above_tilted_plane(self):
        particle = {'initial_position_local_m': [0, 0, 0], 'initial_velocity_local_mps': [0, 0, .1],
                    'lifetime_s': .4, 'opacity_keys': [[0, 0], [.02, .6], [.4, 0]]}
        normal = motion_helper.unit((0, .8, .6)); anchor = (.4, 1.7, -2.1)
        sample = motion_helper.sample_ground_particle(particle, .35, anchor, normal, (1, 0, 0))
        distance = motion_helper.dot(tuple(sample['position_stage_m'][i] - anchor[i] for i in range(3)), normal)
        self.assertGreaterEqual(distance, -1e-12)

    def test_missing_tangent_and_expired_particle_are_rejected(self):
        particle = {'initial_position_local_m': [0, 0, 0], 'initial_velocity_local_mps': [0, 0, .1],
                    'lifetime_s': .4, 'opacity_keys': [[0, 0], [.02, .6], [.4, 0]]}
        with self.assertRaises(ValueError):
            motion_helper.sample_ground_particle(particle, .1, (0, 0, 0), (0, 1, 0), (0, 1, 0))
        self.assertIsNone(motion_helper.sample_ground_particle(particle, .4, (0, 0, 0), (0, 1, 0), (1, 0, 0)))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GroundBoundaryChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    report = {'status': 'OFFLINE_SOURCE_AND_REFERENCE_MOTION_PASS',
              'runtime': 'Root actual ground event / SDK integration and device validation pending',
              'assets': [check_asset(kind) for kind in ('dodge', 'landing')]}
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
