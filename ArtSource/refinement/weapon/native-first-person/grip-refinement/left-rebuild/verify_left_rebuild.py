"""Independent pinned common-Grip Left audit; never builds or edits an asset.

Host NumPy only. Reports actual DAO component topology, finite sampled solid
penetration, surface crossings and full-hand self intersections at 0/.5/1.
"""
import argparse
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
import numpy as np
HERE = Path(__file__).resolve().parent
GRIP = HERE.parent
REPO = HERE.parents[5]
sys.path.insert(0, str(GRIP))
sys.path.insert(0, str(GRIP / 'transform-diagnostic-2026-11-13'))
import verify_grip as surface
import verify_hand_models as anatomy
h = surface.h
S = np.diag([-1., 1., 1., 1.])
SOURCE = REPO / 'app/src/main/assets/models/player_hands/right_hand.glb'
CANDIDATE = HERE / 'left_hand_rebuilt.glb'
DAO = REPO / 'app/src/main/assets/models/dao_grip.glb'
PINS = {'source': '3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0',
        'candidate': 'd8e9c3cb034f465e4527c13aad84e7ba283c3efcc537ab254c6295717cd1bbfd',
        'dao': 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'}
TIMES = (0., .5, 1.)
DIGITS = ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')


def swap_name(name):
    if name == 'RightGripRoot':
        return 'LeftGripRoot'
    if name.startswith(('R_', 'L_')):
        return ('L_' if name.startswith('R_') else 'R_') + name[2:]
    if name.endswith(('_R', '_L')):
        return name[:-2] + ('_L' if name.endswith('_R') else '_R')
    return name


def require_close(actual, expected, label, tolerance=1e-7):
    actual, expected = np.asarray(actual), np.asarray(expected)
    h.require(actual.shape == expected.shape and np.isfinite(actual).all(), label + ': invalid shape/nonfinite')
    error = float(np.max(abs(actual-expected))) if actual.size else 0.
    h.require(error <= tolerance, label + ': mismatch ' + str(error))
    return error


def reflected_vectors(values, tangent=False):
    result = np.array(values, copy=True)
    result[:, 0] *= -1
    if tangent:
        h.require(result.shape[1] == 4, 'base tangent must be VEC4')
        result[:, 3] *= -1
    return result


def matrix_values(document, binary, accessor):
    return h.values(document, binary, accessor).reshape(-1, 4, 4).transpose(0, 2, 1)


def primitives(document):
    return [(mi, pi, p) for mi, m in enumerate(document['meshes']) for pi, p in enumerate(m['primitives'])]


def skin_normals(document, binary, primitive, worlds):
    a = primitive['attributes']
    skin = document['skins'][0]
    transforms = np.array([worlds[i] for i in skin['joints']]) @ matrix_values(document, binary, skin['inverseBindMatrices'])
    palettes = h.values(document, binary, a['JOINTS_0']).astype(int)
    weights = h.values(document, binary, a['WEIGHTS_0'])
    blend = np.sum(transforms[palettes] * weights[:, :, None, None], axis=1)
    determinant = np.linalg.det(blend[:, :3, :3])
    h.require(np.isfinite(determinant).all() and determinant.min() > 0, 'actual blended skin not proper')
    normal = h.values(document, binary, a['NORMAL'])
    normal = np.einsum('vij,vj->vi', np.linalg.inv(blend[:, :3, :3]).transpose(0, 2, 1), normal)
    return normal / np.linalg.norm(normal, axis=1)[:, None]


def verify_contract(source, sb, candidate, cb):
    """Verify decoded geometry/rig and real LBS independently of the producer."""
    h.accessor_storage(candidate, cb)
    h.require(len(source['nodes']) == len(candidate['nodes']), 'node/frame/marker count changed')
    h.require(len(source['meshes']) == len(candidate['meshes']), 'mesh count changed')
    h.require(len(source['skins']) == len(candidate['skins']) == 1, 'skin count changed')
    names = [n.get('name') for n in candidate['nodes'] if n.get('name')]
    h.require(len(names) == len(set(names)), 'duplicate bilateral names')
    h.require(not any('DerivedHandGrip' in n for n in names), 'legacy derived marker present')
    h.require(source.get('scene') == candidate.get('scene'), 'active scene changed')
    h.require(len(source['scenes']) == len(candidate['scenes']), 'scene count changed')
    for a, b in zip(source['scenes'], candidate['scenes']):
        h.require(a['nodes'] == b['nodes'] and len(b['nodes']) == 1, 'outer root membership changed')
        root = candidate['nodes'][b['nodes'][0]]
        h.require(root.get('name') == 'LeftGripRoot', 'common-Grip root name missing')
        require_close(h.local(root), np.eye(4), 'outer identity root', 1e-12)
    for old, new in zip(source['nodes'], candidate['nodes']):
        h.require(new.get('name') == swap_name(old.get('name', '')), 'bilateral name mapping incorrect')
        for key in ('children', 'mesh', 'skin'):
            h.require(old.get(key) == new.get(key), 'hierarchy/mesh/skin index changed')
        h.require(not ('matrix' in new and any(k in new for k in ('translation', 'rotation', 'scale'))), 'mixed matrix/TRS')
        if 'scale' in new:
            h.require(np.all(np.asarray(new['scale']) > 0), 'negative/zero scale')
        if 'rotation' in new:
            h.require(abs(np.linalg.norm(new['rotation'])-1) < 1e-4, 'nonunit node quaternion')
        require_close(h.local(new), S @ h.local(old) @ S, 'local S M S', 1e-12)
        h.require(np.linalg.det(h.local(new)[:3, :3]) > 0, 'improper local transform')
    oldskin, newskin = source['skins'][0], candidate['skins'][0]
    h.require(len(newskin['joints']) == 78 and len(set(newskin['joints'])) == 78, 'full 78 palette missing')
    h.require(oldskin['joints'] == newskin['joints'], 'palette order changed')
    h.require(oldskin.get('skeleton') == newskin.get('skeleton'), 'skin skeleton changed')
    require_close(matrix_values(candidate, cb, newskin['inverseBindMatrices']),
                  S @ matrix_values(source, sb, oldskin['inverseBindMatrices']) @ S, 'IBM S M S')
    for key in ('materials', 'images', 'textures', 'samplers', 'extensionsUsed', 'extensionsRequired'):
        h.require(source.get(key) == candidate.get(key), 'appearance contract changed: ' + key)
    image_hashes = []
    for i in range(len(source.get('images', []))):
        a, b = h.image_bytes(source, sb, i), h.image_bytes(candidate, cb, i)
        h.require(a == b, 'embedded image bytes changed')
        image_hashes.append(hashlib.sha256(a).hexdigest())
    pairs = list(zip(primitives(source), primitives(candidate)))
    h.require(len(pairs) == len(primitives(source)) == len(primitives(candidate)), 'primitive count changed')
    for old, new in zip(source['meshes'], candidate['meshes']):
        h.require(new.get('name') == swap_name(old.get('name', '')), 'mesh bilateral name mapping incorrect')
    tangent_count = 0
    for (mi, pi, old), (mj, pj, new) in pairs:
        h.require((mi, pi) == (mj, pj), 'primitive identity changed')
        h.require(old.get('mode', 4) == new.get('mode', 4) == 4, 'not triangle primitive')
        h.require(old.get('material') == new.get('material'), 'material assignment changed')
        h.require(set(old['attributes']) == set(new['attributes']), 'attribute set changed')
        for semantic, accessor in old['attributes'].items():
            a = h.values(source, sb, accessor)
            b = h.values(candidate, cb, new['attributes'][semantic])
            if semantic in ('POSITION', 'NORMAL', 'TANGENT'):
                require_close(b, reflected_vectors(a, semantic == 'TANGENT'), semantic + ' X reflection', 0)
                tangent_count += semantic == 'TANGENT'
            else:
                h.require(a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes(), 'unchanged attribute bytes differ: ' + semantic)
        a = h.values(source, sb, old['indices']).reshape(-1, 3)
        b = h.values(candidate, cb, new['indices']).reshape(-1, 3)
        h.require(np.array_equal(b, a[:, [0, 2, 1]]), 'triangle winding not reversed')
        h.require(len(old.get('targets', [])) == len(new.get('targets', [])), 'morph target count changed')
        for ot, nt in zip(old.get('targets', []), new.get('targets', [])):
            h.require(set(ot) == set(nt), 'morph semantics changed')
            for semantic in ot:
                a, b = h.values(source, sb, ot[semantic]), h.values(candidate, cb, nt[semantic])
                require_close(b, reflected_vectors(a) if semantic in ('POSITION', 'NORMAL', 'TANGENT') else a, 'morph reflection', 0)
    h.require(len(source.get('animations', [])) == len(candidate.get('animations', [])), 'animation count changed')
    for old, new in zip(source.get('animations', []), candidate.get('animations', [])):
        h.require(old['channels'] == new['channels'] and old.get('name') == new.get('name'), 'animation target/channel changed')
        h.require(len(old['samplers']) == len(new['samplers']), 'sampler count changed')
        for channel in old['channels']:
            index, path = channel['sampler'], channel['target']['path']
            a, b = old['samplers'][index], new['samplers'][index]
            h.require(a.get('interpolation', 'LINEAR') == b.get('interpolation', 'LINEAR'), 'interpolation changed')
            require_close(h.values(candidate, cb, b['input']), h.values(source, sb, a['input']), 'animation times', 0)
            values = h.values(source, sb, a['output'])
            expected = values.copy()
            if path == 'rotation': expected[:, 1:3] *= -1
            elif path == 'translation': expected[:, 0] *= -1
            require_close(h.values(candidate, cb, b['output']), expected, 'animation output ' + path, 0)
    states = []
    for time in (None, *TIMES):
        sw = h.sampled_worlds(source, sb, None if time is None else 'grip', time or 0)
        cw = h.sampled_worlds(candidate, cb, None if time is None else 'grip', time or 0)
        joint_error = max(require_close(cw[i], S @ sw[i] @ S, 'joint world conjugation') for i in oldskin['joints'])
        entries = []
        for (mi, pi, old), (_, _, new) in pairs:
            a, b = h.skin(source, sb, old, sw), h.skin(candidate, cb, new, cw)
            error = require_close(b, a @ S[:3, :3], 'actual LBS mirror')
            na, nb = skin_normals(source, sb, old, sw), skin_normals(candidate, cb, new, cw)
            normal_error = require_close(nb, na @ S[:3, :3], 'actual skin normal mirror')
            af, bf = [h.values(d, data, p['indices']).reshape(-1, 3) for d, data, p in ((source, sb, old), (candidate, cb, new))]
            ta, tb = a[af], b[bf]
            area_a, area_b = [np.cross(t[:, 1]-t[:, 0], t[:, 2]-t[:, 0]) for t in (ta, tb)]
            winding_error = require_close(area_b, area_a @ S[:3, :3], 'actual geometric winding mirror')
            entries.append({'mesh': mi, 'primitive': pi, 'vertices': len(b), 'triangles': len(bf), 'LBS_max_error_m': error,
                            'inverse_transpose_normal_max_error': normal_error, 'winding_area_vector_max_error_m2': winding_error})
        states.append({'time': 'default' if time is None else time, 'joint_world_max_error': joint_error, 'primitives': entries})
    default_world, closed_world = h.sampled_worlds(candidate, cb), h.sampled_worlds(candidate, cb, 'grip', 1)
    default_closed_error = max(require_close(h.skin(candidate, cb, p, default_world), h.skin(candidate, cb, p, closed_world),
                                           'default pose must equal closed grip@1') for _, _, p in primitives(candidate))
    return {'passed': True, 'contract': 'Lskin = S * Rskin in common Grip; identity outer root; no B/C frame',
            'full_palette_joints': 78, 'TANGENT_primitives_in_actual_source': tangent_count,
            'default_vs_closed_actual_LBS_max_error_m': default_closed_error,
            'missing_TANGENT_scope': 'Source has no tangent; synthetic controls cover tangent.xyz and tangent.w. Runtime tangent generation remains unverified.',
            'KTX_payload_sha256': image_hashes, 'states': states}


def hand_geometry(document, binary, time):
    world = h.sampled_worlds(document, binary, 'grip', time)
    points, bind, faces, weights, palettes = [], [], [], [], []
    offset = 0
    for _, _, p in primitives(document):
        a = p['attributes']
        x = h.skin(document, binary, p, world)
        points.append(x)
        bind.append(h.values(document, binary, a['POSITION']))
        faces.append(h.values(document, binary, p['indices']).reshape(-1, 3).astype(int)+offset)
        weights.append(h.values(document, binary, a['WEIGHTS_0']))
        palettes.append(h.values(document, binary, a['JOINTS_0']).astype(int))
        offset += len(x)
    return dict(points=np.concatenate(points), bind=np.concatenate(bind), faces=np.concatenate(faces),
                weights=np.concatenate(weights), palettes=np.concatenate(palettes),
                names=[document['nodes'][i]['name'] for i in document['skins'][0]['joints']])


def sample_layout(geometry, side):
    """Fixed hand region vertices, incident centroids and unique edge midpoints."""
    faces, palettes, weights, names = [geometry[k] for k in ('faces', 'palettes', 'weights', 'names')]
    ids = [i for i, name in enumerate(names) if name == side+'_Hand' or name.startswith(tuple(side+'_'+d for d in DIGITS))]
    influence = sum(np.sum(weights*(palettes == i), axis=1) for i in ids)
    fi = np.flatnonzero((influence[faces] > .5).any(axis=1))
    chosen = faces[fi]
    vertices = np.flatnonzero(influence > .5)
    edges = np.unique(np.sort(np.concatenate((chosen[:, [0, 1]], chosen[:, [1, 2]], chosen[:, [2, 0]])), axis=1), axis=0)
    table = [(np.array([i]), np.array([1.])) for i in vertices]
    table += [(f, np.ones(3)/3) for f in chosen]
    table += [(e, np.ones(2)/2) for e in edges]
    dense = np.zeros((len(weights), len(names)))
    for slot in range(weights.shape[1]):
        np.add.at(dense, (np.arange(len(weights)), palettes[:, slot]), weights[:, slot])
    labels = [names[int((b @ dense[a]).argmax())] for a, b in table]
    return table, labels


def actual_dao_components():
    document, binary = h.read(DAO)
    worlds = h.sampled_worlds(document, binary)
    result = {}
    for i, node in enumerate(document['nodes']):
        if 'mesh' not in node: continue
        points, faces, offset = [], [], 0
        for p in document['meshes'][node['mesh']]['primitives']:
            x = h.values(document, binary, p['attributes']['POSITION'])
            points.append((np.c_[x, np.ones(len(x))] @ worlds[i].T)[:, :3])
            f = h.values(document, binary, p['indices']).reshape(-1, 3).astype(int)
            faces.append(f+offset)
            offset += len(x)
        points, faces = np.concatenate(points), np.concatenate(faces)
        topology, _, _ = h.edge_topology(points, faces)
        closed = all(topology[key] == 0 for key in ('open_edges', 'nonmanifold_edges', 'inconsistent_two_face_edge_orientation'))
        result[node['name']] = {'points': points, 'faces': faces, 'topology': topology, 'closed': closed}
    h.require('Handle core' in result and result['Handle core']['closed'], 'actual core is not closed')
    h.require('Grip | cord wrap' in result and not result['Grip | cord wrap']['closed'], 'actual cord topology unexpectedly changed')
    return result


def crossing_pairs(first, second, same=False, faces=None, weld=None):
    """All surface triangles, AABB broad phase, robust finite intersection.

    Self adjacency uses fixed source bind-position weld, including UV seams;
    coincident posed vertices can never erase a newly created intersection.
    """
    low, high = second.min(axis=1), second.max(axis=1)
    result = []
    for a, triangle in enumerate(first):
        candidates = np.flatnonzero(((high >= triangle.min(axis=0)-1e-7) & (low <= triangle.max(axis=0)+1e-7)).all(axis=1))
        if same: candidates = candidates[candidates > a]
        for b in candidates:
            if same and set(weld[faces[a]]) & set(weld[faces[b]]): continue
            if h.triangle_pair_intersection(triangle, second[b], 0): result.append([int(a), int(b)])
    return result


def dominant_face_labels(geometry):
    weights, palettes = geometry['weights'], geometry['palettes']
    dense = np.zeros((len(weights), len(geometry['names'])))
    for slot in range(weights.shape[1]):
        np.add.at(dense, (np.arange(len(weights)), palettes[:, slot]), weights[:, slot])
    return [geometry['names'][i] for i in dense[geometry['faces']].mean(axis=1).argmax(axis=1)]


def grouped_pair_counts(pairs, labels, side):
    result = {}
    for a, b in pairs:
        # Remove only the side prefix for comparison, retaining digit/segment.
        key = ' / '.join(sorted((labels[a].removeprefix(side+'_'), labels[b].removeprefix(side+'_'))))
        result[key] = result.get(key, 0)+1
    return result


def solid_distances(samples, triangles, closed):
    low, high = triangles.min(axis=(0, 1)), triangles.max(axis=(0, 1))
    bounded = np.flatnonzero(((samples >= low-1e-7) & (samples <= high+1e-7)).all(axis=1))
    inside = []
    depths = []
    if closed:
        inside = [int(i) for i in bounded if surface.contains(samples[i], triangles)]
        if inside:
            distance, _, _ = surface.nearest(samples[inside], triangles)
            keep = distance > 1e-7
            inside = np.asarray(inside)[keep].tolist()
            depths = (distance[keep]*1000).tolist()
    return {'signed_volume_test': bool(closed), 'inside_sample_ids': inside, 'inside_samples': len(inside),
            'maximum_sampled_penetration_mm': max(depths, default=0.),
            'inside_depth_p95_mm': float(np.percentile(depths, 95)) if depths else 0.,
            'inside_depth_mm': depths}


def minimum_sample_gap(samples, triangles):
    # A triangle AABB bounds distance from below. Start with an exact surface
    # query near the component centroid, then reject only points beyond that
    # upper bound. This preserves the global finite-sample minimum exactly.
    center = triangles.mean(axis=(0, 1))
    seed = int(np.argmin(np.linalg.norm(samples-center, axis=1)))
    initial = float(surface.nearest(samples[seed:seed+1], triangles)[0][0])
    low, high = triangles.min(axis=(0, 1)), triangles.max(axis=(0, 1))
    delta = np.maximum(np.maximum(low-samples, samples-high), 0)
    chosen = np.flatnonzero(np.linalg.norm(delta, axis=1) <= initial+1e-12)
    gap, _, _ = surface.nearest(samples[chosen], triangles)
    return float(gap.min()*1000)


def audit_contacts(source, sb, candidate, cb):
    dao = actual_dao_components()
    topology = {name: {'topology': item['topology'], 'closed_oriented_solid': item['closed'],
                      'triangles': len(item['faces']), 'bounds_Grip_m': [item['points'].min(axis=0).tolist(), item['points'].max(axis=0).tolist()]}
                for name, item in dao.items()}
    report = {'dao_sha256': PINS['dao'], 'component_topology': topology, 'states': [],
              'scope': 'Actual unreflected DAO in common Grip. Whole hand+forearm triangle crossings and self tested; solid inside/gap uses fixed weighted hand-region vertices, incident triangle centroids and unique edge midpoints. Finite samples do not prove continuous penetration maximum. Open components only surface intersection/unsigned gap; no inside claim.'}
    geometries = {'R': hand_geometry(source, sb, 0), 'L': hand_geometry(candidate, cb, 0)}
    layouts = {side: sample_layout(g, side) for side, g in geometries.items()}
    # Fixed bind-pose adjacency, not a candidate-pose coincidence test.
    adjacency = {side: h.weld_positions(g['bind'], epsilon=1e-7)[1] for side, g in geometries.items()}
    for time in TIMES:
        state = {'time': time, 'hands': {}}
        for side, d, b in (('R', source, sb), ('L', candidate, cb)):
            g = hand_geometry(d, b, time)
            points, faces = g['points'], g['faces']
            table, labels = layouts[side]
            samples = np.array([weights @ points[ids] for ids, weights in table])
            triangles = points[faces]
            self_pairs = crossing_pairs(triangles, triangles, True, faces, adjacency[side])
            face_labels = dominant_face_labels(g)
            records = {}
            for name, component in dao.items():
                ct = component['points'][component['faces']]
                pairs = crossing_pairs(triangles, ct)
                record = solid_distances(samples, ct, component['closed'])
                record['minimum_sample_surface_gap_mm'] = minimum_sample_gap(samples, ct)
                record['surface_crossing_pairs'] = pairs
                record['surface_crossing_count'] = len(pairs)
                record['deepest_sample_witnesses'] = [
                    {'sample_id': index, 'dominant_joint': labels[index],
                     'global_hand_vertex_ids': table[index][0].tolist(), 'barycentric': table[index][1].tolist(),
                     'point_Grip_m': samples[index].tolist(), 'penetration_mm': depth}
                    for index, depth in sorted(zip(record['inside_sample_ids'], record['inside_depth_mm']), key=lambda row: -row[1])[:8]]
                if name == 'Handle core':
                    record['by_digit'] = {}
                    ids, depths = record['inside_sample_ids'], record['inside_depth_mm']
                    for digit in DIGITS:
                        values = [depth for i, depth in zip(ids, depths) if labels[i].startswith(side+'_'+digit)]
                        record['by_digit'][digit] = {'inside_samples': len(values), 'maximum_sampled_penetration_mm': max(values, default=0.)}
                if name == 'Grip | cord wrap':
                    gap = surface.nearest(samples, ct)[0]*1000
                    record['surface_gap_by_digit'] = {}
                    for digit in DIGITS:
                        mask = np.array([label.startswith(side+'_'+digit) for label in labels])
                        values = gap[mask]
                        h.require(len(values) > 0, 'missing weighted contact samples: '+digit)
                        record['surface_gap_by_digit'][digit] = {
                            'samples': len(values), 'minimum_mm': float(values.min()),
                            'median_mm': float(np.median(values)), 'p95_mm': float(np.percentile(values, 95)),
                            'within_1mm': int((values <= 1).sum()), 'within_3mm': int((values <= 3).sum()),
                            'farther_than_10mm': int((values > 10).sum())}
                records[name] = record
            state['hands'][side] = {'sample_count': len(samples), 'components': records,
                                   'sample_layout_counts': {'vertices': sum(len(ids) == 1 for ids, _ in table),
                                                            'face_centroids': sum(len(ids) == 3 for ids, _ in table),
                                                            'edge_midpoints': sum(len(ids) == 2 for ids, _ in table)},
                                   'position_weld_self': {'count': len(self_pairs), 'face_pairs': self_pairs,
                                                         'dominant_face_joint_pair_counts': grouped_pair_counts(self_pairs, face_labels, side),
                                                         'adjacency': 'source bind-position epsilon 1e-7m; shared welded vertex/edge and UV seam neighbors excluded'}}
        right = {tuple(x) for x in state['hands']['R']['position_weld_self']['face_pairs']}
        left = {tuple(x) for x in state['hands']['L']['position_weld_self']['face_pairs']}
        state['Left_self_added_vs_Right'] = sorted([list(x) for x in left-right])
        state['Left_self_removed_vs_Right'] = sorted([list(x) for x in right-left])
        h.require(left == right, 'Left gained/lost full-hand self intersection vs Right')
        report['states'].append(state)
        print(json.dumps({'time': time, 'self_R_L': [len(right), len(left)], 'core_R_L': [state['hands'][s]['components']['Handle core']['maximum_sampled_penetration_mm'] for s in ('R', 'L')], 'dao_crossings_R_L': [sum(c['surface_crossing_count'] for c in state['hands'][s]['components'].values()) for s in ('R', 'L')]}), flush=True)
    report['no_new_self_intersections'] = True
    report['actual_dao_not_assumed_mirror_symmetric'] = True
    closed = report['states'][-1]['hands']['L']['components']
    core = closed['Handle core']
    h.require(core['maximum_sampled_penetration_mm'] < .1, 'closed Left actual core exceeds accepted shallow source margin')
    h.require(all(group['inside_samples'] == 0 for digit, group in core['by_digit'].items() if digit != 'Index'),
              'closed Left has non-Index core penetration')
    for name, record in closed.items():
        if name != 'Handle core' and record['signed_volume_test']:
            h.require(record['inside_samples'] == record['surface_crossing_count'] == 0,
                      'closed Left intersects actual solid fitting: '+name)
    report['closed_Left_finite_numeric_contact_checks'] = {
        'passed': True, 'maximum_core_sampled_depth_limit_mm': .1,
        'actual_core_sampled_depth_mm': core['maximum_sampled_penetration_mm'],
        'non_Index_digits_inside_actual_core': 0, 'other_closed_solid_component_crossings_or_inside_samples': 0,
        'open_cord_surface_crossings_reported_separately': closed['Grip | cord wrap']['surface_crossing_count'],
        'natural_grip_or_visual_acceptance_claimed': False}
    return report


def run_audit():
    paths = {'source': SOURCE, 'candidate': CANDIDATE, 'dao': DAO}
    for role, path in paths.items(): h.require(h.digest(path) == PINS[role], 'pinned ' + role + ' changed')
    source, sb = h.read(SOURCE)
    candidate, cb = h.read(CANDIDATE)
    h.require(cb[:len(sb)] == sb, 'actual source original BIN prefix changed')
    test_output = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_verify_left_rebuild.py')
    tests = unittest.TextTestRunner(stream=test_output).run(suite)
    h.require(tests.wasSuccessful() and tests.testsRun >= 27 and not tests.skipped,
              'verification controls failed: '+test_output.getvalue())
    report = {'inputs': {role: {'path': str(path.relative_to(REPO)), 'sha256': PINS[role]} for role, path in paths.items()},
              'contract': verify_contract(source, sb, candidate, cb),
              'source_original_BIN_prefix_exact': True,
              'verification_controls': {'passed': True, 'tests_run': tests.testsRun, 'failures': len(tests.failures),
                                        'errors': len(tests.errors), 'skipped': len(tests.skipped),
                                        'command': 'python3 -B -m unittest discover -s '+str(HERE.relative_to(REPO))+' -p test_verify_left_rebuild.py -v'}}
    assets = {'R': anatomy.inspect_asset(source, sb, 'R'), 'L': anatomy.inspect_asset(candidate, cb, 'L')}
    report['actual_anatomical_chirality'] = {side: {'open_signed_chirality': a['surface'][0]['signed_chirality'],
                                                 'open_thumb_radial_offset_m': a['summary']['actual_open_thumb_radial_offset_metres'],
                                                 'proper_actual_skin_and_weighted_side': a['summary']} for side, a in assets.items()}
    report['actual_dao_and_self'] = audit_contacts(source, sb, candidate, cb)
    report['limitations'] = [
        'Right inherited fixed-DAO open/mid penetrations are explicitly measured at 0/.5; the mirrored Left does not repair source animation or imply a safe transition.',
        'Source dorsal palm ridge and hard wrist opening are inherited geometry; numerical mirror/chirality/contact pass is not final hand quality approval.',
        'All DAO components use their actual topology; blade/wear/fuller/cord are open and have no signed-volume claim.',
        'No Blender, render, device, SDK pose physiology, tangent generator, runtime transform or visual-quality verification is claimed. Root reviews these independently.',
        'Self intersections are finite triangle tests with epsilon 1e-7m, excluding shared source-weld adjacency; coplanar positive-area overlap is included, isolated tangency is not penetration.'
    ]
    report['numeric_common_Grip_contract_passed'] = True
    report['final_visual_or_native_acceptance_claimed'] = False
    report['freeze'] = {'verifier_sha256': h.digest(Path(__file__)), 'tests_sha256': h.digest(HERE/'test_verify_left_rebuild.py')}
    for role, path in paths.items(): h.require(h.digest(path) == PINS[role], 'input changed during audit: ' + role)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE/'verification.json')
    args = parser.parse_args()
    h.require(args.output.resolve() == (HERE/'verification.json').resolve(), 'only owned verification.json may be written')
    report = run_audit()
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps({'passed': True, 'output': str(args.output), 'sha256': h.digest(args.output)}))


if __name__ == '__main__': main()
