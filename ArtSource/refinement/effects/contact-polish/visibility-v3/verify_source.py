"""Offline v3 source checks; normal-distance look and runtime remain separate evidence."""
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('contact_reader', HERE.parent / 'verify_contact_polish.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def verify_layer_coverage(mesh_names, motion):
    if len(mesh_names) != len(set(mesh_names)):
        raise ValueError('Mesh node names must be unique')
    definitions = motion['particles'] + motion['cores'] + motion['accents']
    names = [item['node'] for item in definitions]
    if len(names) != len(set(names)) or set(mesh_names) != set(names):
        raise ValueError('Every visible mesh must be defined exactly once')


def verify_envelope(layer, lifetime):
    keys = layer['opacity_keys']
    assert len(keys) >= 2
    assert all(len(key) == 2 and all(math.isfinite(v) for v in key) for key in keys)
    assert keys[0][0] == 0 and math.isclose(keys[-1][0], lifetime, abs_tol=1e-9)
    assert keys[-1][1] == 0 and all(0 <= alpha <= 1 for _, alpha in keys)
    assert all(a[0] < b[0] for a, b in zip(keys, keys[1:]))


def main():
    reports = []
    for family in ('metal', 'wet'):
        motion = json.loads((HERE / family / 'motion.json').read_text())
        assert motion['schema'] == 'contact-particle-motion/v2'
        path = HERE / family / motion['asset']
        document, binary = reader.read_glb(path)
        assert not document.get('animations') and not document.get('skins')
        assert not document.get('extensionsUsed') and not document.get('extensionsRequired')
        assert not document.get('images')
        mesh_nodes = [node for node in document['nodes'] if 'mesh' in node]
        verify_layer_coverage([node['name'] for node in mesh_nodes], motion)
        nodes = {node['name']: node for node in mesh_nodes}
        assert motion['gravity_stage_mps2'] == [0, -9.81, 0]
        counts = {}
        for particle in motion['particles']:
            kind = particle['type']; counts[kind] = counts.get(kind, 0) + 1
            assert 0 < particle['lifetime_s'] <= .5
            for key in ('initial_position_local_m', 'initial_velocity_local_mps'):
                assert len(particle[key]) == 3 and all(math.isfinite(v) for v in particle[key])
            verify_envelope(particle, particle['lifetime_s'])
            axis = particle['orientation_axis_local']
            assert len(axis) == 3 and all(math.isfinite(v) for v in axis)
            assert math.isclose(math.hypot(*axis), 1, abs_tol=1e-9)
            points = reader.positions(document, binary, nodes[particle['node']])
            assert all(math.isfinite(v) for point in points for v in point)
            if kind == 'droplet' and particle.get('shape') == 'round':
                diameter = max(math.dist(a, b) for a in points for b in points)
                assert .002 <= diameter <= .010
        for core in motion['cores']:
            for profile, lifetime in (('normal', .065), ('parry', .09), ('fatal', .15)):
                assert core[profile]['lifetime_s'] == lifetime
                verify_envelope(core[profile], lifetime)
        for accent in motion['accents']:
            assert accent['requires_real_tangent'] is True
            assert 0 < accent['lifetime_s'] <= .15
            verify_envelope(accent, accent['lifetime_s'])
        for material in document['materials']:
            assert material['alphaMode'] == 'BLEND'
            assert all(0 <= value <= 1 for value in material['pbrMetallicRoughness']['baseColorFactor'])
            assert all(0 <= value <= 1 for value in material.get('emissiveFactor', [0, 0, 0]))
        reports.append({'family': family, 'asset': str(path.relative_to(HERE)),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'motion_sha256': hashlib.sha256((HERE / family / 'motion.json').read_bytes()).hexdigest(),
                        'mesh_nodes': len(nodes), 'moving_particles': len(motion['particles']),
                        'cores': len(motion['cores']), 'accents': len(motion['accents']),
                        'types': counts, 'all_visible_meshes_covered': True})
    (HERE / 'verification.json').write_text(json.dumps({'status': 'SOURCE_CONTRACT_PASS',
        'runtime_integration_status': '08 must regenerate v2 definitions and Root publishes assets together',
        'normal_distance_review': 'See review images; offline is not SDK evidence', 'sources': reports}, indent=2) + '\n')
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    verify_envelope({'opacity_keys': [[0, 1], [.065, 0]]}, .065)
    try:
        verify_envelope({'opacity_keys': [[0, 1], [.09, 0]]}, .065)
    except AssertionError:
        pass
    else:
        raise AssertionError('A mismatched core curve must be rejected')
    try:
        verify_layer_coverage(['spark', 'spark'], {'particles': [{'node': 'spark'}], 'cores': [], 'accents': []})
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate GLB node names must be rejected')
    try:
        verify_layer_coverage(['core', 'arc'], {'particles': [], 'cores': [{'node': 'core'}], 'accents': []})
    except ValueError:
        pass
    else:
        raise AssertionError('An unmanaged arc must be rejected')
    try:
        verify_layer_coverage(['core'], {'particles': [{'node': 'core'}], 'cores': [{'node': 'core'}], 'accents': []})
    except ValueError:
        pass
    else:
        raise AssertionError('A multiply-driven node must be rejected')
    main()
