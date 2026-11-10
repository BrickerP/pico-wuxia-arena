"""Measure actual posed character hands and conservatively refine their dao grip.

The report uses a radial clearance proxy for the authored tapered elliptical
handle core. Its values describe radial clearance at posed hand-surface samples.
Only a translation of the existing grip frame may be published.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_character_library import decode_animation, node_order, sampled_local
from prepare_rigged_warrior import (
    HERE, calibrated_mount, local_matrix, matrix_values, normalization_frame, read_glb,
)


FINGERS = ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
POSES = [('slash', time) for time in sorted({1.55, 2.117, *[frame / 30 for frame in range(47, 103)]})]
POSES += [('idle', 1.0), ('walk', .60), ('hit_body', .35), ('hit_head', .35), ('hit_side', .35)]
# Ring centres and radii come from the authored Handle core, relative to Grip.
RINGS = np.array(((-.104, .012, .010), (-.096, .016, .012), (-.051, .017, .013),
                  (.044, .016, .012), (.092, .014, .011), (.098, .012, .009)))


def accessor(document, binary, index):
    value = document['accessors'][index]
    if 'sparse' in value:
        raise ValueError('sparse attribute requires a separate production reader')
    view = document['bufferViews'][value['bufferView']]
    types = {5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    width = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}[value['type']]
    dtype = np.dtype(types[value['componentType']])
    stride = view.get('byteStride', width * dtype.itemsize)
    offset = view.get('byteOffset', 0) + value.get('byteOffset', 0)
    rows = np.ndarray((value['count'], width), dtype=dtype, buffer=binary,
                      offset=offset, strides=(stride, dtype.itemsize)).copy()
    if value.get('normalized'):
        rows = rows.astype(float) / np.iinfo(dtype).max
    return rows


def handle_clearance(points):
    y = points[:, 1]
    rx = np.interp(y, RINGS[:, 0], RINGS[:, 1])
    rz = np.interp(y, RINGS[:, 0], RINGS[:, 2])
    radial = np.sqrt(points[:, 0] ** 2 + points[:, 2] ** 2)
    ellipse_scale = np.sqrt((points[:, 0] / rx) ** 2 + (points[:, 2] / rz) ** 2)
    surface_radius = np.divide(radial, ellipse_scale, out=np.minimum(rx, rz).copy(),
                               where=ellipse_scale > 1e-12)
    side = radial - surface_radius
    cap = np.maximum(RINGS[0, 0] - y, y - RINGS[-1, 0])
    return np.sqrt(np.maximum(side, 0) ** 2 + np.maximum(cap, 0) ** 2) + np.minimum(np.maximum(side, cap), 0)


def measurements(points, finger_masks):
    signed = handle_clearance(points)
    depth = np.maximum(-signed, 0) * 1000
    gaps = {finger: float(np.min(np.abs(signed[mask])) * 1000)
            for finger, mask in finger_masks.items()}
    return {
        'max_radial_penetration_mm': float(depth.max()),
        'mean_radial_penetration_mm': float(depth.mean()),
        'vertices_deeper_than_2mm': int(np.count_nonzero(depth > 2)),
        'surface_samples_within_3mm': int(np.count_nonzero(np.abs(signed) <= .003)),
        'finger_nearest_core_surface_mm': gaps,
    }


def pose_clouds(document, binary, alignment, baseline_mount):
    joints = document['skins'][0]['joints']
    names = [document['nodes'][index]['name'] for index in joints]
    hand_index = next(index for index in joints if document['nodes'][index]['name'] == 'R_Hand')
    finger_palettes = {finger: [i for i, name in enumerate(names) if name.startswith('R_' + finger)]
                       for finger in FINGERS}
    right_palettes = [names.index('R_Hand')] + [i for values in finger_palettes.values() for i in values]
    mesh_node = next(node for node in document['nodes'] if node.get('name') == 'TripoBody_Mesh')
    mesh = document['meshes'][mesh_node['mesh']]
    streams, seen = [], set()
    for primitive_index in alignment['body_primitive_indices']:
        attributes = mesh['primitives'][primitive_index]['attributes']
        key = tuple(attributes[field] for field in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
        if key in seen:
            continue
        seen.add(key)
        position = accessor(document, binary, attributes['POSITION']).astype(float)
        palette = accessor(document, binary, attributes['JOINTS_0']).astype(int)
        weights = accessor(document, binary, attributes['WEIGHTS_0']).astype(float)
        weights /= weights.sum(axis=1)[:, None]
        region = sum(np.sum(weights * (palette == i), axis=1) for i in right_palettes) > .5
        position, palette, weights = position[region], palette[region], weights[region]
        masks = {finger: sum(np.sum(weights * (palette == i), axis=1) for i in values) > .25
                 for finger, values in finger_palettes.items()}
        streams.append((position, palette, weights, masks))
    positions = np.concatenate([stream[0] for stream in streams])
    palettes = np.concatenate([stream[1] for stream in streams])
    weights = np.concatenate([stream[2] for stream in streams])
    masks = {finger: np.concatenate([stream[3][finger] for stream in streams]) for finger in FINGERS}
    if any(not mask.any() for mask in masks.values()):
        raise ValueError('finger surface samples are incomplete')
    positions = np.column_stack((positions, np.ones(len(positions))))
    binds = accessor(document, binary, document['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    parents, order = node_order(document)
    clips = {clip['name']: clip for clip in document['animations']}
    decoded = {name: decode_animation({**document, 'animations': [clip]}, binary)[0]
               for name, clip in clips.items()}
    published_mount = local_matrix({'matrix': alignment['grip_local_matrix_gltf']})
    clouds = []
    for name, time in POSES:
        world = {}
        for index in order:
            local = sampled_local(document['nodes'][index], index, decoded[name], time)
            parent = parents.get(index)
            world[index] = world[parent] @ local if parent is not None else local
        joint_world = np.array([list(world[index]) for index in joints])
        transforms = joint_world @ binds
        blended = np.sum(transforms[palettes] * weights[:, :, None, None], axis=1)
        posed = np.einsum('vij,vj->vi', blended, positions)
        grip_world = world[hand_index] @ baseline_mount
        points = (posed @ np.array(list(grip_world.inverted())).T)[:, :3]
        actual_world = world[hand_index] @ published_mount
        actual = (posed @ np.array(list(actual_world.inverted())).T)[:, :3]
        clouds.append({'clip': name, 'time_seconds': time, 'points': points,
                       'grip_world': grip_world, 'published': measurements(actual, masks)})
    return clouds, masks, len(positions)


def summarize(clouds, masks, offset):
    rows = [measurements(cloud['points'] - offset, masks) for cloud in clouds]
    gap = max(max(row['finger_nearest_core_surface_mm'].values()) for row in rows)
    maximum = max(row['max_radial_penetration_mm'] for row in rows)
    mean = sum(row['mean_radial_penetration_mm'] for row in rows) / len(rows)
    contact = sum(row['surface_samples_within_3mm'] for row in rows) / len(rows)
    deep = sum(row['vertices_deeper_than_2mm'] for row in rows) / len(rows)
    return {'worst_penetration_mm': maximum, 'worst_finger_gap_mm': gap,
            'mean_penetration_mm': mean, 'mean_contact_samples': contact,
            'mean_deep_samples': deep, 'poses': rows}


def admissible(candidate, baseline):
    return all(
        new['surface_samples_within_3mm'] >= old['surface_samples_within_3mm'] * .90 and
        new['max_radial_penetration_mm'] <= old['max_radial_penetration_mm'] + .05 and
        all(new['finger_nearest_core_surface_mm'][finger] <= old['finger_nearest_core_surface_mm'][finger] + 1.5
            for finger in FINGERS)
        for new, old in zip(candidate['poses'], baseline['poses'])
    )


def objective(summary, offset):
    return (summary['worst_penetration_mm'] ** 2 + summary['mean_penetration_mm'] ** 2 * 4 +
            summary['worst_finger_gap_mm'] ** 2 * 2 + float(offset @ offset) * 1e6 * .03)


def main():
    path = HERE / 'motion_library.json'
    manifest = json.loads(path.read_text())
    report = {'method': 'final posed skin surface versus authored tapered elliptical core radial proxy',
              'depth_scope': 'surface-sample radial clearance approximation',
              'max_grip_translation_mm': 80, 'source_time_seconds': 2.117, 'characters': []}
    changed = False
    for character in manifest['characters']:
        key = character['id']
        model_path = HERE / 'library' / character['output']
        runtime_path = HERE.parents[1] / 'app/src/main/assets/models/opponents' / character['output']
        digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
        if hashlib.sha256(runtime_path.read_bytes()).hexdigest() != digest:
            raise ValueError('published and runtime character assets differ: ' + key)
        document, binary = read_glb(model_path)
        alignment = json.loads((HERE / 'library' / (key + '_alignment.json')).read_text())
        source, _ = read_glb(HERE / character['source'])
        normalization, _, _, _, _ = normalization_frame(source, character['height_metres'])
        hand = next(index for index, node in enumerate(source['nodes']) if node.get('name') == 'R_Hand')
        mount = calibrated_mount(source, normalization, hand)
        clouds, masks, count = pose_clouds(document, binary, alignment, mount)
        baseline = summarize(clouds, masks, np.zeros(3))
        best, best_offset = baseline, np.zeros(3)
        native = next(cloud for cloud in clouds if cloud['clip'] == 'slash' and cloud['time_seconds'] == 2.117)
        native_cloud = [native]
        native_baseline = summarize(native_cloud, masks, np.zeros(3))
        native_best = native_baseline
        for x in range(-16, 4):
            for y in range(-4, 5):
                for z in range(-6, 3):
                    offset = np.array((x, y, z), dtype=float) * .005
                    if float(offset @ offset) > .080 ** 2:
                        continue
                    candidate_native = summarize(native_cloud, masks, offset)
                    if not admissible(candidate_native, native_baseline):
                        continue
                    if objective(candidate_native, offset) >= objective(native_best, best_offset):
                        continue
                    candidate = summarize(clouds, masks, offset)
                    if admissible(candidate, baseline):
                        best, best_offset, native_best = candidate, offset, candidate_native
        accepted = (baseline['worst_penetration_mm'] - best['worst_penetration_mm'] >= 1.5 or
                    best['worst_finger_gap_mm'] <= baseline['worst_finger_gap_mm'] * .5)
        if accepted:
            chosen = mount @ Matrix.Translation(Vector(best_offset))
            chosen_frame = matrix_values(chosen)
            if character.get('grip_frame') != chosen_frame:
                character['grip_frame'] = chosen_frame
                changed = True
        elif 'grip_frame' in character:
            del character['grip_frame']
            changed = True
        rows, blade_path = [], []
        for index, cloud in enumerate(clouds):
            rows.append({'clip': cloud['clip'], 'time_seconds': cloud['time_seconds'],
                         'current_published': cloud['published'], 'baseline': baseline['poses'][index],
                         'candidate': best['poses'][index]})
            if cloud['clip'] == 'slash':
                tip = Vector((.0532, .849, 0))
                before = cloud['grip_world'] @ tip
                after = cloud['grip_world'] @ (tip + Vector(best_offset))
                blade_path.append({'time_seconds': cloud['time_seconds'], 'before_tip_metres': list(before),
                                   'after_tip_metres': list(after), 'translation_mm': (after - before).length * 1000})
        record = {'id': key, 'input_glb_sha256': digest, 'hand_surface_samples': count,
                  'accepted': accepted, 'grip_translation_metres': best_offset.tolist(),
                  'maximum_blade_path_translation_mm': float(np.linalg.norm(best_offset) * 1000),
                  'baseline': {k: v for k, v in baseline.items() if k != 'poses'},
                  'candidate': {k: v for k, v in best.items() if k != 'poses'}, 'pose_measurements': rows,
                  'native_slash_blade_path': blade_path}
        report['characters'].append(record)
        print(json.dumps({k: v for k, v in record.items() if k != 'pose_measurements'}), flush=True)
    output = HERE / 'review/grip_refinement.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if changed:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print('Grip calibration report published', output, 'manifest_changed', changed)


if __name__ == '__main__':
    main()
