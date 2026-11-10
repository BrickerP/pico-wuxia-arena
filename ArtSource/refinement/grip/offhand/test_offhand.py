"""Small Blender-side regressions for the scoped offhand producer."""
import copy
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_offhand as producer


def rejected(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('invalid offhand operation was accepted')


def main():
    manifest = json.loads((producer.HERE / 'calibration.json').read_text())
    results = {'deterministic_replays': [], 'boundary_rejections': [], 'envelope_checks': []}
    for entry in manifest['characters']:
        key = entry['id']
        source, binary = producer.read_glb(producer.REPO / entry['source'])
        config = producer.CONFIG[key]
        output, packed, _ = producer.patch(source, binary, config)
        digest = hashlib.sha256(producer.encode_glb(output, packed)).hexdigest()
        assert digest == entry['candidate_sha256'], 'producer does not reproduce reviewed output'
        results['deterministic_replays'].append(key)
        start, rise, fall, end = config['window_seconds']
        for t in (start - .01, start, end, end + .01):
            assert producer.envelope(t, config['window_seconds']) == 0
        for t in (rise, (rise + fall) / 2, fall):
            assert producer.envelope(t, config['window_seconds']) == 1
        epsilon = 1e-6
        assert producer.envelope(start + epsilon, config['window_seconds']) / epsilon < .001
        assert producer.envelope(end - epsilon, config['window_seconds']) / epsilon < .001
        results['envelope_checks'].append(key)
        bad = copy.deepcopy(config)
        bad['rotations'] = {'R_Hand': {'axis': [1, 0, 0], 'degrees': 8}}
        rejected(lambda: producer.patch(source, binary, bad))
        results['boundary_rejections'].append(key + ':right-hand-scope')
        bad = copy.deepcopy(config)
        bad['window_seconds'] = [0, .1, 7, 8]
        rejected(lambda: producer.patch(source, binary, bad))
        results['boundary_rejections'].append(key + ':outside-native-time-range')
    rejected(lambda: producer.envelope(2, [1, 1, 2, 3]))
    results['boundary_rejections'].append('empty-rise-window')
    old = producer.SOURCE_HASHES['indigo']
    before = {e['id']: hashlib.sha256((producer.REPO / e['candidate']).read_bytes()).hexdigest()
              for e in manifest['characters']}
    try:
        producer.SOURCE_HASHES['indigo'] = '0' * 64
        rejected(producer.build)
        results['boundary_rejections'].append('source-hash-drift')
    finally:
        producer.SOURCE_HASHES['indigo'] = old
    for e in manifest['characters']:
        assert hashlib.sha256((producer.REPO / e['candidate']).read_bytes()).hexdigest() == before[e['id']]
    (producer.HERE / 'tests.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps(results), flush=True)


if __name__ == '__main__':
    main()
