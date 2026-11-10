"""Replay reviewed hero parameters and reject a changed source identity."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_hero as producer


def main():
    calibration = json.loads((producer.HERE / 'calibration.json').read_text())
    source, binary = producer.read_glb(producer.SOURCE)
    alignment = json.loads((producer.REPO / 'ArtSource/tripo-warrior/library/base_alignment.json').read_text())
    offsets = calibration['right_finger_local_offsets']
    deltas = {i: [offsets[n['name']]['x_degrees'], offsets[n['name']]['z_degrees']]
              for i, n in enumerate(source['nodes']) if n.get('name') in offsets}
    patched, packed, _ = producer.fingers.patch_rotations(source, binary, deltas)
    old_mount = producer.Matrix(producer.np.array(calibration['grip_before_gltf']).reshape(4, 4).T.tolist())
    document, data, _ = producer.translate_weapon(patched, packed, alignment, old_mount, calibration['grip_offset_metres'])
    digest = hashlib.sha256(producer.encode_glb(document, data)).hexdigest()
    assert digest == calibration['candidate_sha256'], 'reviewed parameter replay changed output'
    old = producer.SOURCE_SHA
    try:
        producer.SOURCE_SHA = '0' * 64
        try:
            producer.build()
        except ValueError:
            pass
        else:
            raise AssertionError('accepted changed hero baseline')
    finally:
        producer.SOURCE_SHA = old
    candidate = producer.HERE / 'candidates/base.glb'
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == digest
    result = {'reviewed_parameter_replay': True, 'source_hash_drift_rejected_without_writing': True,
              'candidate_sha256': digest}
    (producer.HERE / 'tests.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
