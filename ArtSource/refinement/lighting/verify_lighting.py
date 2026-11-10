"""Check actual HomeStage light constants and named shadow receivers offline.

This validates Stage geometry and resource bindings, not PICO rendered brightness.
"""
import hashlib
import json
import math
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt'
EXPECTED_ACTOR = '53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641'


def glb(path):
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or length != len(raw):
        raise ValueError('Invalid GLB container')
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + size])


def reachable(document, roots):
    pending = list(roots)
    result = []
    while pending:
        index = pending.pop()
        result.append(index)
        pending.extend(document['nodes'][index].get('children', []))
    return result


def mesh_targets(document, name=None):
    active = reachable(document, document['scenes'][document.get('scene', 0)]['nodes'])
    if name is not None:
        selected = [i for i in active if document['nodes'][i].get('name') == name]
        if len(selected) != 1:
            raise ValueError('Shadow target must be unique: ' + name)
        active = reachable(document, selected)
    meshes = [document['nodes'][i].get('name', str(i)) for i in active if 'mesh' in document['nodes'][i]]
    if not meshes:
        raise ValueError('Shadow target contains no render mesh')
    return meshes


def vector_constant(source, name, kind='Vector3'):
    match = re.search(r'private val ' + name + r' = ' + kind + r'\(([^)]+)\)', source)
    if not match:
        raise ValueError('Missing light constant: ' + name)
    return tuple(float(x.strip().removesuffix('f')) for x in match.group(1).split(','))


def scalar_constant(source, name):
    match = re.search(r'private const val ' + name + r' = ([0-9.]+)f', source)
    if not match:
        raise ValueError('Missing light constant: ' + name)
    return float(match.group(1))


def check_fill(position, lumens, radius, probes):
    if not all(math.isfinite(x) for x in (*position, lumens, radius)) or lumens <= 0 or radius <= 0:
        raise ValueError('Invalid point light parameters')
    distances = {name: math.dist(position, point) for name, point in probes.items()}
    if any(distance >= radius for distance in distances.values()):
        raise ValueError('Initial actor is outside the fill radius')
    return distances


class BindingChecks(unittest.TestCase):
    def test_wrapper_resolves_actual_child_mesh(self):
        document = {'nodes': [{'name': 'Floor', 'children': [1]}, {'name': 'Tile', 'mesh': 0}],
                    'scenes': [{'nodes': [0]}]}
        self.assertEqual(['Tile'], mesh_targets(document, 'Floor'))

    def test_empty_or_missing_receiver_is_rejected(self):
        document = {'nodes': [{'name': 'Floor'}], 'scenes': [{'nodes': [0]}]}
        with self.assertRaises(ValueError):
            mesh_targets(document, 'Floor')
        with self.assertRaises(ValueError):
            mesh_targets(document, 'Absent')

    def test_valid_fill_covers_actor(self):
        self.assertEqual({'face': 1.0}, check_fill((0, 1, 0), 500, 2, {'face': (0, 1, -1)}))

    def test_edge_and_nonfinite_fill_are_rejected(self):
        with self.assertRaises(ValueError):
            check_fill((0, 1, 0), 500, 1, {'face': (0, 1, -1)})
        with self.assertRaises(ValueError):
            check_fill((math.nan, 1, 0), 500, 2, {'face': (0, 1, -1)})


def validate_scene():
    source = SOURCE.read_text()
    key_shadow = re.search(
        r'DirectionalLightComponent\(KEY_LIGHT_COLOR,\s*KEY_LIGHT_LUX,\s*castsShadowEnabled\s*=\s*(true|false)\)',
        source,
    )
    assert key_shadow is not None and key_shadow.group(1) == 'false'
    probes = {'face': (0.0, 1.6, -2.4), 'torso': (0.0, 1.1, -2.4)}
    fills = []
    for prefix in ('WARM', 'COOL'):
        position = vector_constant(source, prefix + '_FILL_POSITION')
        lumens = scalar_constant(source, prefix + '_FILL_LUMENS')
        radius = scalar_constant(source, prefix + '_FILL_RADIUS_METERS')
        distances = check_fill(position, lumens, radius, probes)
        assert max(distances.values()) / radius < .5
        fills.append({'name': prefix, 'stagePositionMeters': position, 'lumens': lumens,
                      'radiusMeters': radius, 'initialProbeDistanceMeters': distances})
    x, y, z, w = vector_constant(source, 'KEY_LIGHT_ROTATION', 'Quat')
    norm = math.sqrt(x*x + y*y + z*z + w*w)
    assert abs(norm - 1) < 2e-6
    x, y, z, w = (value / norm for value in (x, y, z, w))
    ray = (-2*(x*z + w*y), -2*(y*z - w*x), -(1 - 2*(x*x + y*y)))
    expected = (.5, -.62, -.6)
    length = math.sqrt(sum(v*v for v in expected))
    assert math.dist(ray, [v/length for v in expected]) < 2e-6
    receivers = []
    for asset, name in [('tavern_slice', 'Paving'), ('forecourt', 'Paving'),
                        ('courtyard_details', 'SidePaving_Geometry')]:
        path = ROOT / 'app/src/main/assets/models' / (asset + '.glb')
        receivers.append({'asset': str(path.relative_to(ROOT)), 'target': name,
                          'meshes': mesh_targets(glb(path), name)})
    casters = []
    for name in ('base', 'indigo', 'veteran'):
        path = ROOT / 'app/src/main/assets/models/opponents' / (name + '.glb')
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        if name == 'base':
            assert sha == EXPECTED_ACTOR
        casters.append({'asset': str(path.relative_to(ROOT)), 'sha256': sha,
                        'meshes': mesh_targets(glb(path))})
    profile = {'evidence': 'Offline source/geometry check; PICO rendering remains unverified',
               'homeStageSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
               'keyLux': scalar_constant(source, 'KEY_LIGHT_LUX'), 'keyStageRay': ray,
               'shadowMode': 'GroundShadow', 'directionalShadowEnabled': False,
               'fills': fills, 'groundShadowCasters': casters, 'groundShadowReceivers': receivers,
               'ibl': 'No explicit IBL texture bound; no verified licensed IBL KTX available'}
    (HERE / 'lighting_profile.json').write_text(json.dumps(profile, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(profile, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BindingChecks))
    if not result.wasSuccessful():
        raise SystemExit(1)
    validate_scene()
