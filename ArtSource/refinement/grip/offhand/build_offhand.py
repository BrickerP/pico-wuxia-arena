"""Smooth slash-only offhand rotations from the reviewed finger candidates."""
import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GRIP = HERE.parent
REPO = GRIP.parents[2]
sys.path.insert(0, str(REPO / 'ArtSource/tripo-warrior'))
from mathutils import Quaternion
from prepare_character_library import decode_animation, sample_track
from prepare_rigged_warrior import encode_glb, read_glb

SOURCE_HASHES = {
    'indigo': '4516458ab2d44d986046d36c8349a5901ef20452e60e6570f56c6540d172ee43',
    'veteran': '010e80a08573d0b165692b30a06fcc93f6f0394181fa138b198aa09049b934a3',
}
CONFIG = {
    'indigo': {'window_seconds': [1.8, 2.0, 3.4, 3.6],
               'rotations': {'L_Hand': {'axis': [1, 0, 0], 'degrees': 8.0}}},
    'veteran': {'window_seconds': [1.5, 1.55, 1.72, 1.95],
                'rotations': {'L_Forearm': {'axis': [0, 0, 1], 'degrees': 4.0}}},
}


def envelope(time, window):
    start, rise, fall, end = window
    if not start < rise <= fall < end:
        raise ValueError('invalid envelope window')
    if time <= start or time >= end:
        return 0.0
    if time < rise:
        return .5 - .5 * math.cos(math.pi * (time - start) / (rise - start))
    if time <= fall:
        return 1.0
    return .5 + .5 * math.cos(math.pi * (time - fall) / (end - fall))


def correction(time, config, bone):
    data = config['rotations'][bone]
    delta = Quaternion(data['axis'], math.radians(data['degrees']))
    return Quaternion((1, 0, 0, 0)).slerp(delta, envelope(time, config['window_seconds']))


def append_accessor(document, packed, rows, kind):
    width = len(rows[0])
    packed.extend(b'\0' * (-len(packed) % 4))
    offset = len(packed)
    for row in rows:
        packed.extend(struct.pack('<' + 'f' * width, *row))
    view = len(document['bufferViews'])
    document['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(rows) * width * 4})
    accessor = len(document['accessors'])
    data = {'bufferView': view, 'componentType': 5126, 'count': len(rows), 'type': kind}
    if kind == 'SCALAR':
        data.update(min=[rows[0][0]], max=[rows[-1][0]])
    document['accessors'].append(data)
    return accessor


def patch(document, binary, config):
    result, packed = copy.deepcopy(document), bytearray(binary)
    slash = next(a for a in document['animations'] if a['name'] == 'slash')
    output = next(a for a in result['animations'] if a['name'] == 'slash')
    tracks, _ = decode_animation({**document, 'animations': [slash]}, binary)
    changed = []
    for channel in slash['channels']:
        target = channel['target']
        name = document['nodes'][target['node']].get('name')
        if target['path'] != 'rotation' or name not in config['rotations']:
            continue
        if name not in ('L_Hand', 'L_Forearm'):
            raise ValueError('correction outside reviewed wrist/forearm scope')
        track = tracks[(target['node'], 'rotation')]
        if track[2] != 'LINEAR':
            raise ValueError('offhand patch requires LINEAR quaternion source')
        start, _, _, end = config['window_seconds']
        if start < track[0][0] or end > track[0][-1]:
            raise ValueError('envelope extends beyond the original slash track')
        extra = [start, end, *config['window_seconds'], 1.55, 2.117, 94 / 30, 95 / 30]
        extra += [frame / 60 for frame in range(math.floor(start * 60), math.ceil(end * 60) + 1)]
        extra += [start + (config['window_seconds'][1] - start) * t for t in (.25, .5, .75)]
        # Collapse float32-equivalent timestamps before encoding strictly increasing inputs.
        sampled = [*track[0], *[t for t in extra if start <= t <= end]]
        times = sorted({struct.unpack('<f', struct.pack('<f', t))[0] for t in sampled
                        if track[0][0] <= t <= track[0][-1]})
        values = []
        for time in times:
            x, y, z, w = sample_track(track, time, True)
            q = (Quaternion((w, x, y, z)) @ correction(time, config, name)).normalized()
            row = (q.x, q.y, q.z, q.w)
            if values and sum(a*b for a, b in zip(values[-1], row)) < 0:
                row = tuple(-v for v in row)
            values.append(row)
        sampler = output['samplers'][channel['sampler']]
        sampler['input'] = append_accessor(result, packed, [(t,) for t in times], 'SCALAR')
        sampler['output'] = append_accessor(result, packed, values, 'VEC4')
        changed.append({'bone': name, 'source_key_count': len(track[0]), 'candidate_key_count': len(times),
                        'source_range_seconds': [track[0][0], track[0][-1]]})
    if {r['bone'] for r in changed} != set(config['rotations']):
        raise ValueError('a requested rotation track is absent')
    result['buffers'][0]['byteLength'] = len(packed)
    assert result['nodes'] == document['nodes'] and result['skins'] == document['skins']
    assert result['meshes'] == document['meshes'] and packed[:len(binary)] == binary
    return result, bytes(packed), changed


def build(keys=('indigo', 'veteran')):
    (HERE / 'candidates').mkdir(parents=True, exist_ok=True)
    report = {'scope': 'slash-only smoothly enveloped local offhand rotation',
              'envelope': 'raised-cosine sampled values; zero endpoint correction; exported LINEAR track is C0 with sampled seam slopes',
              'sample_rate_hz': 60, 'characters': []}
    if set(keys) != set(CONFIG):
        report['characters'] = [r for r in json.loads((HERE / 'calibration.json').read_text())['characters'] if r['id'] not in keys]
    for key in keys:
        config = CONFIG[key]
        source = GRIP / 'candidates' / (key + '.glb')
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        if source_hash != SOURCE_HASHES[key]:
            raise ValueError('reviewed source changed: ' + key)
        document, binary = read_glb(source)
        result, packed, tracks = patch(document, binary, config)
        output = encode_glb(result, packed)
        candidate = HERE / 'candidates' / (key + '.glb')
        candidate.write_bytes(output)
        report['characters'].append({'id': key, 'source': str(source.relative_to(REPO)),
            'source_sha256': source_hash, 'candidate': str(candidate.relative_to(REPO)),
            'candidate_sha256': hashlib.sha256(output).hexdigest(), **config, 'changed_tracks': tracks})
    report['characters'].sort(key=lambda c: c['id'])
    (HERE / 'calibration.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    build()
