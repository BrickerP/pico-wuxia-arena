"""Offline source checks for the wet-cloth contact asset and motion contract."""
import hashlib
import json
import math
import struct
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sample_opacity(keys, age):
    if age < keys[0][0] or age >= keys[-1][0]:
        return 0.0
    for (start, left), (end, right) in zip(keys, keys[1:]):
        if start <= age < end:
            fraction = (age - start) / (end - start)
            return left + (right - left) * fraction
    return 0.0


def stream(document, binary, index):
    accessor = document['accessors'][index]
    view = document['bufferViews'][accessor['bufferView']]
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}[accessor['type']]
    code = {5123: 'H', 5126: 'f'}[accessor['componentType']]
    size = struct.calcsize('<' + code * width)
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return [struct.unpack_from('<' + code * width, binary, start + row * view.get('byteStride', size))
            for row in range(accessor['count'])]


def verify():
    data = (HERE / 'wet_cloth_contact.glb').read_bytes()
    assert struct.unpack_from('<4sII', data) == (b'glTF', 2, len(data))
    size, kind = struct.unpack_from('<II', data, 12)
    assert kind == 0x4e4f534a
    document = json.loads(data[20:20 + size])
    binary_size, binary_kind = struct.unpack_from('<II', data, 20 + size)
    assert binary_kind == 0x004e4942
    binary = data[28 + size:28 + size + binary_size]
    motion = json.loads((HERE / 'motion.json').read_text())
    assert not document.get('animations') and not document.get('extensionsUsed')
    assert motion['gravity_stage_mps2'] == [0.0, -9.81, 0.0]
    particles = motion['particles']
    assert len(particles) == 10
    assert sum(p['type'] == 'droplet' for p in particles) == 8
    assert len(document['meshes']) == 10
    assert len({p['node'] for p in particles}) == 10
    triangles = 0
    diameters = []
    for particle in particles:
        nodes = [node for node in document['nodes'] if node['name'] == particle['node']]
        assert len(nodes) == 1
        node = nodes[0]
        assert node.get('translation') == particle['initial_position_local_m']
        primitives = document['meshes'][node['mesh']]['primitives']
        assert len(primitives) == 1
        primitive = primitives[0]
        positions = stream(document, binary, primitive['attributes']['POSITION'])
        normals = stream(document, binary, primitive['attributes']['NORMAL'])
        indices = [row[0] for row in stream(document, binary, primitive['indices'])]
        assert all(math.isfinite(v) for position in positions for v in position)
        assert all(abs(math.sqrt(sum(v*v for v in normal)) - 1) < 1e-5 for normal in normals)
        assert all(0 <= index < len(positions) for index in indices)
        assert len(indices) % 3 == 0
        triangles += len(indices) // 3
        if particle['type'] == 'droplet':
            extent = max(max(p[axis] for p in positions) - min(p[axis] for p in positions) for axis in range(3))
            assert abs(extent - particle['diameter_m']) < 1e-9
            assert 0.002 - 1e-9 <= extent <= 0.004 + 1e-9
            diameters.append(extent)
            for a, b, c in zip(indices[0::3], indices[1::3], indices[2::3]):
                u = tuple(positions[b][axis] - positions[a][axis] for axis in range(3))
                v = tuple(positions[c][axis] - positions[a][axis] for axis in range(3))
                normal = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
                centroid = tuple((positions[a][axis]+positions[b][axis]+positions[c][axis])/3 for axis in range(3))
                assert sum(normal[axis]*centroid[axis] for axis in range(3)) > 0
        life = particle['lifetime_s']
        assert 0.18 <= life <= 0.32
        keys = particle['opacity_keys']
        assert keys[0][0] == 0 and keys[-1] == [life, 0.0]
        assert all(a[0] < b[0] for a, b in zip(keys, keys[1:]))
        assert all(0 <= opacity <= 1 for _, opacity in keys)
        assert sample_opacity(keys, -0.01) == sample_opacity(keys, life) == 0
        assert sample_opacity(keys, 0.008) > 0
        assert particle['initial_velocity_local_mps'][0] > 0
        assert particle['initial_velocity_local_mps'][2] > 0
    assert triangles == 196
    assert all(m['alphaMode'] == 'BLEND' for m in document['materials'])
    assert all(m['pbrMetallicRoughness']['metallicFactor'] == 0 for m in document['materials'])
    report = {'status': 'OFFLINE_SOURCE_CHECKS_PASS', 'runtime': 'Root SDK and headset validation pending',
              'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'particles': 10, 'droplets': 8,
              'fibers': 2, 'independent_meshes': 10, 'triangles': triangles,
              'measured_droplet_diameter_m': [min(diameters), max(diameters)],
              'lifetime_range_s': [min(p['lifetime_s'] for p in particles), max(p['lifetime_s'] for p in particles)],
              'normal_and_winding_checks': 'PASS', 'opacity_before_birth_and_at_death': 'PASS',
              'gravity_coordinate_space': 'Stage', 'paid_asset_tasks': 0}
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


class OpacityChecks(unittest.TestCase):
    def test_fresh_particle_interpolates(self):
        self.assertAlmostEqual(.5, sample_opacity([[0, 0], [.01, 1], [.2, 0]], .005))

    def test_unborn_and_expired_particle_are_hidden(self):
        keys = [[0, 0], [.01, 1], [.2, 0]]
        for age in (-.001, .2, .4):
            self.assertEqual(0, sample_opacity(keys, age))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(OpacityChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    verify()
