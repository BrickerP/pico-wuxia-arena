"""Single pinned hero grip candidate; only weapon translation and right fingers."""
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
sys.path.insert(0, str(GRIP))
import build_grip_candidates as fingers
import numpy as np
from mathutils import Matrix, Vector
from prepare_rigged_warrior import encode_glb, matrix_values, read_glb
from refine_character_grips import accessor

SOURCE = REPO / 'ArtSource/tripo-warrior/library/base.glb'
SOURCE_SHA = '5ff55210dfbe9e10fbad1bf0d182424ae298bf009f9b845e9d307543302e0f3f'


def mount_score(row, offset):
    gaps = list(row['finger_nearest_core_surface_mm'].values())
    return (row['max_radial_penetration_mm'] ** 2 + 2 * max(gaps) ** 2 + .3 * sum(v*v for v in gaps)
            + .03 * float(offset @ offset) * 1e6)


def choose_mount(samples):
    original = samples.mount.copy()
    baseline, _ = samples.evaluate(('slash', 2.117), {})
    best, chosen = baseline, np.zeros(3)
    def consider(offset):
        nonlocal best, chosen
        if np.linalg.norm(offset) > .065:
            return
        samples.mount = original @ Matrix.Translation(Vector(offset))
        row, _ = samples.evaluate(('slash', 2.117), {})
        if (row['max_radial_penetration_mm'] <= baseline['max_radial_penetration_mm'] + .05 and
                row['surface_samples_within_3mm'] >= baseline['surface_samples_within_3mm'] and
                mount_score(row, offset) < mount_score(best, chosen)):
            best, chosen = row, offset.copy()
    for x in range(-50, 11, 10):
        for y in range(-10, 41, 10):
            for z in range(-40, 11, 10):
                consider(np.array((x, y, z), dtype=float) / 1000)
    centre = chosen.copy()
    for x in (-5, 0, 5):
        for y in (-5, 0, 5):
            for z in (-5, 0, 5):
                consider(centre + np.array((x, y, z), dtype=float) / 1000)
    samples.mount = original @ Matrix.Translation(Vector(chosen))
    return chosen, original, baseline


def translate_weapon(document, binary, alignment, mount, offset):
    result, packed = copy.deepcopy(document), bytearray(binary)
    joints = document['skins'][0]['joints']
    hand = next(i for i in joints if document['nodes'][i].get('name') == 'R_Hand')
    palette_index = joints.index(hand)
    inverse = accessor(document, binary, document['skins'][0]['inverseBindMatrices'])[palette_index].reshape(4, 4).T
    shift = Matrix(inverse.tolist()).inverted() @ mount @ Vector((*offset, 0))
    mesh_node = next(n for n in result['nodes'] if n.get('name') == 'TripoBody_Mesh')
    primitives = result['meshes'][mesh_node['mesh']]['primitives']
    changed = {}
    for index in alignment['weapon_binding']['weapon_primitive_indices']:
        attributes = primitives[index]['attributes']
        old = attributes['POSITION']
        if old not in changed:
            positions = accessor(document, binary, old).astype(float) + np.array(shift[:3])
            packed.extend(b'\0' * (-len(packed) % 4))
            start = len(packed)
            packed.extend(positions.astype('<f4').tobytes())
            view = len(result['bufferViews'])
            result['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(positions) * 12})
            new = len(result['accessors'])
            result['accessors'].append({'bufferView': view, 'componentType': 5126, 'count': len(positions),
                'type': 'VEC3', 'min': positions.min(axis=0).tolist(), 'max': positions.max(axis=0).tolist()})
            changed[old] = new
        attributes['POSITION'] = changed[old]
    for n in result['nodes']:
        if n.get('name') == 'HandGrip_R':
            n['matrix'] = matrix_values(mount @ Matrix.Translation(Vector(offset)))
    result['buffers'][0]['byteLength'] = len(packed)
    return result, bytes(packed), list(shift[:3])


def build():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('hero baseline identity changed')
    (HERE / 'candidates').mkdir(parents=True, exist_ok=True)
    document, binary = read_glb(SOURCE)
    alignment = json.loads((REPO / 'ArtSource/tripo-warrior/library/base_alignment.json').read_text())
    original_samples = fingers.Samples(document, binary, alignment)
    samples = fingers.Samples(document, binary, alignment)
    offset, before_mount, before = choose_mount(samples)
    deltas, moved_before, after = fingers.optimize(samples)
    patched, packed, changed = fingers.patch_rotations(document, binary, deltas)
    output_doc, output_bin, bind_shift = translate_weapon(patched, packed, alignment, before_mount, offset)
    output = encode_glb(output_doc, output_bin)
    candidate = HERE / 'candidates/base.glb'
    candidate.write_bytes(output)
    adjusted = copy.deepcopy(alignment)
    adjusted['grip_local_matrix_gltf'] = matrix_values(samples.mount)
    (HERE / 'alignment.json').write_text(json.dumps(adjusted, indent=2) + '\n')
    actual = fingers.Samples(output_doc, output_bin, adjusted)
    rows, paths = [], []
    for pose in fingers.POSES:
        old, world = original_samples.evaluate(pose, {})
        new, _ = actual.evaluate(pose, {})
        rows.append({'clip': pose[0], 'time_seconds': pose[1], 'before': old, 'after': new})
        if pose[0] == 'slash':
            point = Vector((.0532, .849, 0))
            a = world[original_samples.hand] @ before_mount @ point
            b = world[original_samples.hand] @ samples.mount @ point
            paths.append({'time_seconds': pose[1], 'before_tip_metres': list(a), 'after_tip_metres': list(b),
                          'translation_mm': (b-a).length*1000})
    calibration = {'source': str(SOURCE.relative_to(REPO)), 'source_sha256': SOURCE_SHA,
        'review_status': 'requires_review_new_left_crossings_and_penetration_tradeoff',
        'raw_sources': {key: {'path': str(Path('ArtSource/tripo-warrior/refined-base60k') / (key + '.glb')),
                             'sha256': hashlib.sha256((REPO / 'ArtSource/tripo-warrior/refined-base60k' / (key + '.glb')).read_bytes()).hexdigest()}
                        for key in ('rig', 'slash')},
        'candidate': str(candidate.relative_to(REPO)), 'candidate_sha256': hashlib.sha256(output).hexdigest(),
        'grip_offset_metres': offset.tolist(), 'grip_before_gltf': matrix_values(before_mount),
        'grip_after_gltf': matrix_values(samples.mount), 'weapon_bind_shift': bind_shift,
        'right_finger_local_offsets': {document['nodes'][i]['name']: {'x_degrees': a[0], 'z_degrees': a[1]} for i, a in deltas.items()},
        'changed_rotation_tracks': changed, 'contact_marker_seconds': 2.117,
        'contact_pose_before': before, 'contact_pose_moved_before_fingers': moved_before,
        'contact_pose_after': next(r['after'] for r in rows if r['clip']=='slash' and r['time_seconds']==2.117),
        'blade_path': paths, 'pose_measurements': rows}
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
    (HERE / 'calibration.json').write_text(json.dumps(calibration, indent=2) + '\n')
    print(json.dumps({k:v for k,v in calibration.items() if k not in ('pose_measurements','blade_path')}), flush=True)


if __name__ == '__main__':
    build()
