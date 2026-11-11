"""Single bounded visibility candidate. Geometry and trajectories come from immutable v1."""
import copy
import hashlib
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / 'ArtSource/tripo-warrior'))
from prepare_rigged_warrior import read_glb, write_glb

V1 = Path(__file__).resolve().parent.parent
SOURCE_SHAS = {'dodge': 'ebbdaad332022ea017f7207956f3963a675adf3770dd287553076714a352ddf2',
               'landing': 'b29a5d67fee5343e12a318ed7dab8afb4eb55c6d0b98a9e785a0afb3723d55ae'}
COLOR = [0.35, 0.32, 0.28, 1.0]
ALPHA_MULTIPLIER = 1.8
ALPHA_CAP = 0.65
PEAK = 0.85


def color_rows(document, binary, index):
    accessor = document['accessors'][index]
    assert accessor['componentType'] == 5126 and accessor['type'] == 'VEC4'
    view = document['bufferViews'][accessor['bufferView']]
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', 16)
    return [struct.unpack_from('<4f', binary, offset + row*stride) for row in range(accessor['count'])]


def make_variant(output_dir, kind):
    name = kind + '_ground_polish.glb'
    source = V1 / name
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_sha == SOURCE_SHAS[kind]
    original, binary = read_glb(source)
    candidate = copy.deepcopy(original)
    packed = bytearray(binary)
    changes = []
    for index, material in enumerate(candidate['materials']):
        pbr = material['pbrMetallicRoughness']
        changes.append({'material': index, 'field': 'baseColorFactor',
                        'before': list(pbr['baseColorFactor']), 'after': COLOR})
        pbr['baseColorFactor'] = list(COLOR)
    alpha_stats = {'total_vertices': 0, 'changed_vertices': 0, 'edge_zero_vertices': 0,
                   'source_max_alpha': 0.0, 'candidate_max_alpha': 0.0}
    for mesh in candidate['meshes']:
        for primitive in mesh['primitives']:
            old_accessor = primitive['attributes']['COLOR_0']
            rows = color_rows(original, binary, old_accessor)
            transformed = []
            for r, g, b, alpha in rows:
                new_alpha = 0.0 if alpha == 0 else min(ALPHA_CAP, alpha * ALPHA_MULTIPLIER)
                transformed.append((r, g, b, new_alpha))
                alpha_stats['total_vertices'] += 1
                alpha_stats['changed_vertices'] += int(new_alpha != alpha)
                alpha_stats['edge_zero_vertices'] += int(alpha == 0)
                alpha_stats['source_max_alpha'] = max(alpha_stats['source_max_alpha'], alpha)
                alpha_stats['candidate_max_alpha'] = max(alpha_stats['candidate_max_alpha'], new_alpha)
            packed.extend(b'\0' * (-len(packed) % 4))
            offset = len(packed)
            packed.extend(struct.pack('<' + 'f' * (len(transformed)*4), *(v for row in transformed for v in row)))
            view_index = len(candidate['bufferViews'])
            candidate['bufferViews'].append({'buffer': 0, 'byteOffset': offset,
                                            'byteLength': len(transformed)*16, 'target': 34962})
            accessor_index = len(candidate['accessors'])
            candidate['accessors'].append({'bufferView': view_index, 'componentType': 5126,
                                          'count': len(transformed), 'type': 'VEC4'})
            primitive['attributes']['COLOR_0'] = accessor_index
    candidate['buffers'][0]['byteLength'] = len(packed)
    information = write_glb(output_dir / name, candidate, bytes(packed))
    original_motion = json.loads((V1 / (kind + '_motion.json')).read_text())
    motion = copy.deepcopy(original_motion)
    motion_changes = []
    for particle in motion['particles']:
        before = copy.deepcopy(particle['opacity_keys'])
        old_peak = max(alpha for _, alpha in before)
        particle['opacity_keys'] = [[age, min(PEAK, alpha * PEAK / old_peak)] for age, alpha in before]
        motion_changes.append({'node': particle['node'], 'before': before, 'after': particle['opacity_keys']})
    motion_path = output_dir / (kind + '_motion.json')
    motion_path.write_text(json.dumps(motion, ensure_ascii=False, indent=2) + '\n')
    patch = {'source': str(source.relative_to(ROOT)), 'source_sha256': source_sha,
             'source_motion_sha256': hashlib.sha256((V1 / (kind + '_motion.json')).read_bytes()).hexdigest(),
             'candidate_motion_sha256': hashlib.sha256(motion_path.read_bytes()).hexdigest(),
             'candidate': information, 'material_changes': changes, 'vertex_alpha': {
                 'multiplier': ALPHA_MULTIPLIER, 'cap': ALPHA_CAP, 'zero_edges_preserved': True, **alpha_stats},
             'motion_opacity_changes': motion_changes,
             'unchanged': ['POSITION', 'NORMAL', 'indices', 'node transforms', 'geometry size',
                           'initial positions / velocities', 'gravity', 'lifetime / opacity key times',
                           'TBN orientation', 'base clamp / anchor offset']}
    return patch


def build(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    patches = {kind: make_variant(output_dir, kind) for kind in ('dodge', 'landing')}
    (output_dir / 'visibility_patch.json').write_text(json.dumps({'assets': patches}, ensure_ascii=False, indent=2) + '\n')
    metrics = {'status': 'single material/alpha visibility candidate', 'assets': {
        kind: patch['candidate'] for kind, patch in patches.items()}, 'base_color_factor': COLOR,
        'vertex_alpha_multiplier': ALPHA_MULTIPLIER, 'vertex_alpha_cap': ALPHA_CAP,
        'motion_peak': PEAK, 'geometry_and_trajectory_changes': False}
    (output_dir / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    return metrics
