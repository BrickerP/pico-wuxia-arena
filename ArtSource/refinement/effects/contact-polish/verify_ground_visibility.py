"""Verify the ground visibility material trial keeps geometry and motion fixed."""
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('contact_asset_reader', HERE / 'verify_contact_polish.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def colors(document, binary, index):
    a = document['accessors'][index]
    assert a['componentType'] == 5126 and a['type'] == 'VEC4'
    v = document['bufferViews'][a['bufferView']]
    start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride', 16)
    return [struct.unpack_from('<ffff', binary, start + i*stride) for i in range(a['count'])]


def main():
    reports = []
    for name, motion_file in [('dodge_ground_polish', 'dodge_motion.json'),
                              ('landing_ground_polish', 'landing_motion.json')]:
        source_path = HERE / 'ground' / (name + '.glb')
        output = HERE / 'ground/visibility-v2'
        candidate_path = output / source_path.name
        old, old_bin = reader.read_glb(source_path)
        new, new_bin = reader.read_glb(candidate_path)
        assert new_bin[:old['buffers'][0]['byteLength']] == old_bin[:old['buffers'][0]['byteLength']]
        assert old['nodes'] == new['nodes']
        assert old['accessors'] == new['accessors'][:len(old['accessors'])]
        assert old['bufferViews'] == new['bufferViews'][:len(old['bufferViews'])]
        assert len(old['meshes']) == len(new['meshes'])
        for before, after in zip(old['meshes'], new['meshes']):
            assert len(before['primitives']) == len(after['primitives'])
            for a, b in zip(before['primitives'], after['primitives']):
                assert a['indices'] == b['indices']
                assert a.get('mode', 4) == b.get('mode', 4)
                assert set(a['attributes']) == set(b['attributes'])
                for key in a['attributes']:
                    if key != 'COLOR_0':
                        assert a['attributes'][key] == b['attributes'][key]
                first = colors(old, old_bin, a['attributes']['COLOR_0'])
                second = colors(new, new_bin, b['attributes']['COLOR_0'])
                assert len(first) == len(second)
                for original, current in zip(first, second):
                    assert all(0 <= value <= 1 for value in current)
                    if original[3] == 0:
                        assert current[3] == 0
        for a, b in zip(old['materials'], new['materials']):
            assert a.get('emissiveFactor', [0, 0, 0]) == b.get('emissiveFactor', [0, 0, 0])
            assert a.get('alphaMode') == b.get('alphaMode') == 'BLEND'
        old_motion = json.loads((source_path.parent / motion_file).read_text())
        new_motion = json.loads((output / motion_file).read_text())
        assert old_motion['gravity_stage_mps2'] == new_motion['gravity_stage_mps2']
        assert old_motion['anchor_normal_offset_m'] == new_motion['anchor_normal_offset_m']
        assert len(old_motion['particles']) == len(new_motion['particles'])
        for a, b in zip(old_motion['particles'], new_motion['particles']):
            for field in ('node', 'type', 'initial_position_local_m', 'initial_velocity_local_mps', 'lifetime_s'):
                assert a[field] == b[field], field
            assert [x[0] for x in a['opacity_keys']] == [x[0] for x in b['opacity_keys']]
        reports.append({'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
                        'candidate_sha256': hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
                        'geometry_and_kinematics_identical': True, 'transparent_edges_preserved': True,
                        'emission_unchanged': True, 'runtime_status': 'Root review and integration required'})
    (HERE / 'ground/visibility-v2/independent_verification.json').write_text(json.dumps(reports, indent=2) + '\n')
    print(json.dumps(reports, indent=2))


if __name__ == '__main__':
    main()
