"""One fixed REST construction. No simulation, relaxation, or pose inversion.

The unchanged v2 material pattern is the provenance domain. Garment surfaces
are developed around the LIVE native-default joint points, then equal semantic
seams become shared vertex identities. The output is prepared-world glTF REST.
"""
from pathlib import Path
from collections import defaultdict, deque
import hashlib
import json
import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
ROOT = HERE.parents[7]
SOURCE = BASE / 'pattern/pattern_v2.npz'
PATTERN = BASE / 'pattern/pattern_v2.json'
SNAPSHOT = HERE.parent / 'export/current_rest_snapshot.npz'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def edge_table(faces):
    table = defaultdict(list)
    for fi, face in enumerate(faces):
        for a, b in zip(face, np.roll(face, -1)):
            table[tuple(sorted((int(a), int(b))))].append((fi, int(a), int(b)))
    return table


def orient(faces):
    """Propagate opposite edge directions, rejecting nonorientable joins."""
    table = edge_table(faces)
    assert all(len(hits) <= 2 for hits in table.values())
    signs = np.zeros(len(faces), np.int8)
    neighbors = defaultdict(list)
    for hits in table.values():
        if len(hits) == 2:
            (i, a, b), (j, c, d) = hits
            relation = -1 if (a, b) == (c, d) else 1
            neighbors[i].append((j, relation))
            neighbors[j].append((i, relation))
    components = 0
    for seed in range(len(faces)):
        if signs[seed]:
            continue
        components += 1
        signs[seed] = 1
        queue = deque([seed])
        while queue:
            i = queue.popleft()
            for j, relation in neighbors[i]:
                required = signs[i] * relation
                if signs[j]:
                    assert signs[j] == required, ('nonorientable', i, j)
                else:
                    signs[j] = required
                    queue.append(j)
    out = faces.copy()
    out[signs < 0] = out[signs < 0, ::-1]
    return out, signs, components


def loops_and_links(faces, nvertices):
    table = edge_table(faces)
    boundary = [edge for edge, hits in table.items() if len(hits) == 1]
    adjacency = defaultdict(list)
    for a, b in boundary:
        adjacency[a].append(b)
        adjacency[b].append(a)
    assert all(len(n) == 2 for n in adjacency.values()), 'boundary branches'
    pending = set(boundary)
    loops = []
    while pending:
        a, b = min(pending)
        loop = [a]
        prev, cur = a, b
        pending.remove(tuple(sorted((a, b))))
        while cur != a:
            loop.append(cur)
            nxt = next(v for v in adjacency[cur] if v != prev)
            pending.remove(tuple(sorted((cur, nxt))))
            prev, cur = cur, nxt
        loops.append(loop)
    # A manifold vertex has a connected cyclic or interval link.
    links = [defaultdict(set) for _ in range(nvertices)]
    for face in faces:
        for k, vertex in enumerate(face):
            a, b = int(face[k-1]), int(face[(k+1) % len(face)])
            links[vertex][a].add(b)
            links[vertex][b].add(a)
    failures = []
    for vertex, link in enumerate(links):
        if not link:
            failures.append(vertex)
            continue
        seen, queue = set(), [next(iter(link))]
        while queue:
            a = queue.pop()
            if a not in seen:
                seen.add(a)
                queue.extend(link[a] - seen)
        degree_one = sum(len(n) == 1 for n in link.values())
        if len(seen) != len(link) or any(len(n) > 2 for n in link.values()) or degree_one not in (0, 2):
            failures.append(vertex)
    assert not failures, ('bad_vertex_links', failures)
    return table, loops


def proper_crossings(vertices, triangles):
    """CPU segment/triangle proper-interior intersections, no shared vertices."""
    p = vertices[triangles]
    centers = p.mean(1)
    radii = np.linalg.norm(p - centers[:, None], axis=2).max(1)
    pairs = cKDTree(centers).query_pairs(float(2 * radii.max()), output_type='ndarray')
    if not len(pairs):
        return np.empty((0, 2), np.int32)
    a, b = pairs.T
    keep = np.linalg.norm(centers[a] - centers[b], axis=1) <= radii[a] + radii[b]
    keep &= np.all(p[a].min(1) <= p[b].max(1) + 1e-10, axis=1)
    keep &= np.all(p[b].min(1) <= p[a].max(1) + 1e-10, axis=1)
    keep &= ~np.any(triangles[a, :, None] == triangles[b, None, :], axis=(1, 2))
    pairs = pairs[keep]
    hits = np.zeros(len(pairs), bool)
    for reverse in (False, True):
        aa = p[pairs[:, int(reverse)]]
        bb = p[pairs[:, int(not reverse)]]
        e1, e2 = bb[:, 1] - bb[:, 0], bb[:, 2] - bb[:, 0]
        for k in range(3):
            origin = aa[:, k]
            direction = aa[:, (k+1) % 3] - origin
            h = np.cross(direction, e2)
            det = np.einsum('ij,ij->i', e1, h)
            safe = abs(det) > 1e-14
            inv = np.zeros_like(det)
            inv[safe] = 1 / det[safe]
            s = origin - bb[:, 0]
            u = inv * np.einsum('ij,ij->i', s, h)
            q = np.cross(s, e1)
            v = inv * np.einsum('ij,ij->i', direction, q)
            t = inv * np.einsum('ij,ij->i', e2, q)
            hits |= safe & (u > 1e-7) & (v > 1e-7) & (u + v < 1 - 1e-7) & (t > 1e-7) & (t < 1 - 1e-7)
    return pairs[hits].astype(np.int32)


def main():
    pattern = json.loads(PATTERN.read_text())
    data = np.load(SOURCE)
    live = np.load(SNAPSHOT)
    live_json = json.loads(SNAPSHOT.with_suffix('.json').read_text())
    assert sha(SNAPSHOT) == live_json['snapshot']['sha256']
    names = live['bone_names'].tolist()
    assert len(names) == 78 and names == data['bone_names'].tolist()
    # C is only a coordinate rotation; NO animation or skin matrix is sampled.
    C = np.array([[1., 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    rest = C @ live['prepared_joint_world_rest']
    bones = {name: rest[i, :3, 3] for i, name in enumerate(names)}
    flat = data['flat_rest_positions'].astype(float)
    source_q = data['quad_faces'].copy()
    source_part = data['quad_part_ids'].copy()
    grids = {p['name']: np.arange(p['vertex_start'], p['vertex_start'] + p['vertex_count']).reshape(p['grid']) for p in pattern['panels']}
    positions = np.zeros_like(flat)
    cn = bones['Spine02'][1] + .03638688975563518
    cx = (bones['L_Upperarm'][0] + bones['R_Upperarm'][0]) / 2
    zshift = bones['NeckTwist01'][2] + .024 - 1.46
    za = 1.30 - np.hypot(.42 / 42, .12 / 2 / 42) * 6
    alpha = .4
    root_radius = .32 / (2 * np.pi)
    sleeve_frames = {}
    anchors = {}
    for label, sign in [('L', 1), ('R', -1)]:
        shoulder, elbow, hand = [bones[label + '_' + n] for n in ('Upperarm', 'Forearm', 'Hand')]
        cuff = hand - .012 * unit(hand - elbow)
        first = np.linalg.norm(elbow - shoulder)
        second = np.linalg.norm(cuff - elbow)
        split = .42 * first / (first + second)
        axis = unit(elbow - shoulder)
        up = unit(np.array([0., 0, 1]) - axis * axis[2])
        back = unit(-sign * np.cross(axis, up))
        B = shoulder - root_radius * np.sin(alpha) * back - root_radius * np.cos(alpha) * up
        D = shoulder + root_radius * np.sin(alpha) * back - root_radius * np.cos(alpha) * up
        A = np.array([shoulder[0], cn, za + .026 + zshift])
        anchors[label] = dict(A=A, B=B, D=D, shoulder=shoulder)
        sleeve_frames[label] = dict(shoulder=shoulder, elbow=elbow, cuff=cuff, split=split, sign=sign)

    def sidecurve(z, label, front):
        anchor = anchors[label]
        sign = 1 if label == 'L' else -1
        out = np.zeros((len(z), 3))
        lo, mid, high = z < za, (z >= za) & (z <= 1.30), z > 1.30
        t = (z[lo] - 1.02) / (za - 1.02)
        low = np.array([cx + sign * .155, cn, 1.02 + zshift])
        out[lo] = low * (1 - t[:, None]) + anchor['A'] * t[:, None]
        t = (z[mid] - za) / (1.30 - za)
        end = anchor['B' if front else 'D']
        out[mid] = anchor['A'] * (1 - t[:, None]) + end * t[:, None]
        sf = sleeve_frames[label]
        axis = unit(sf['elbow'] - sf['shoulder'])
        up = unit(np.array([0., 0, 1]) - axis * axis[2])
        back = unit(-sign * np.cross(axis, up))
        angle = -np.pi / 2 + alpha + (np.pi - alpha) * (z[high] - 1.30) / .16
        out[high] = anchor['shoulder'] + (-1 if front else 1) * root_radius * np.cos(angle)[:, None] * back + root_radius * np.sin(angle)[:, None] * up
        return out

    for panel in pattern['panels']:
        name = panel['name']
        indices = grids[name].ravel()
        uv = np.asarray(panel['pattern_uv_m'])
        x, z = uv.T
        if name == 'back' or name.startswith('front_'):
            front = name != 'back'
            rx = np.interp(z, [1.02, 1.24, 1.46], [.155, .18, .18])
            ry = np.interp(z, [1.02, 1.24, 1.46], [.078, .09, .075])
            phi = np.pi * x / .42
            pp = np.c_[cx + rx * np.sin(phi), cn + (-1 if front else 1) * ry * np.cos(phi), z + zshift]
            top = np.clip((z - 1.40) / .06, 0, 1)
            shoulder = np.clip((abs(x) - .055) / .155, 0, 1)
            pp[:, 1] = pp[:, 1] * (1 - top) + cn * top
            pp[:, 2] -= .04 * shoulder * top
            if front:
                label = 'L' if name == 'front_L_outer' else 'R'
                sign = 1 if label == 'L' else -1
                edge = np.interp(z, [1.02, 1.20, 1.46], [-.17 if sign > 0 else .11, -.065 if sign > 0 else .045, .055 * sign])
                weight = np.clip((x - edge) / (.21 * sign - edge), 0, 1) ** 4
                dest = sidecurve(z, label, True)
                # Disclosed left-over-right layer separation, smoothly vanishing
                # at the shared shoulder and side. No coincident front sheets.
                pp[:, 1] += (-.0025 if sign > 0 else .0025) * (1 - top)
            else:
                weight = (abs(x) / .21) ** 4
                dest = np.zeros_like(pp)
                for label, sign in [('L', 1), ('R', -1)]:
                    mask = x >= 0 if sign > 0 else x < 0
                    dest[mask] = sidecurve(z[mask], label, False)
            developed = pp * (1 - weight[:, None]) + dest * weight[:, None]
            # Both body pieces use ONE shoulder boundary, independent of their
            # different front/back interior parameterizations.
            for label, sign in [('L', 1), ('R', -1)]:
                mask = (abs(z-1.46) < 1e-10) & (x * sign >= .055-1e-10)
                if not np.any(mask):
                    continue
                frame = sleeve_frames[label]
                axis = unit(frame['elbow'] - frame['shoulder'])
                up = unit(np.array([0., 0, 1]) - axis * axis[2])
                cap = frame['shoulder'] + root_radius * up
                neck = np.array([cx + sign*.18*np.sin(np.pi*.055/.42), cn, 1.46+zshift])
                t = np.clip((abs(x[mask])-.055)/.155, 0, 1)
                developed[mask] = neck*(1-t[:, None]) + cap*t[:, None]
            positions[indices] = developed
        elif name.startswith('sleeve'):
            label = name[-1]
            frame = sleeve_frames[label]
            u, v = uv.T
            fraction = np.clip(u / frame['split'], 0, 1)
            centers = frame['shoulder'] * (1 - fraction[:, None]) + frame['elbow'] * fraction[:, None]
            upper = u <= frame['split']
            fraction = np.clip((u - frame['split']) / (.42 - frame['split']), 0, 1)
            centers[~upper] = (frame['elbow'] * (1 - fraction[:, None]) + frame['cuff'] * fraction[:, None])[~upper]
            axis = np.broadcast_to(unit(frame['elbow'] - frame['shoulder']), centers.shape).copy()
            axis[~upper] = unit(frame['cuff'] - frame['elbow'])
            up = unit(np.array([0., 0, 1]) - axis * axis[:, 2, None])
            back = unit(-frame['sign'] * np.cross(axis, up))
            width = .32 - .12 * u / .42
            radius = width / (2 * np.pi)
            opening_angle = alpha * np.clip(1 - u / .06, 0, 1)
            if 'front' in name:
                angle = -np.pi / 2 + opening_angle + (np.pi - opening_angle) * (v + width / 2) / (width / 2)
            else:
                angle = np.pi / 2 + (np.pi - opening_angle) * v / (width / 2)
            positions[indices] = centers - radius[:, None] * np.cos(angle)[:, None] * back + radius[:, None] * np.sin(angle)[:, None] * up

    # Coons gussets use the ACTUAL four adjoining curves, no loose-sewing pull.
    for label, sign in [('L', 1), ('R', -1)]:
        f = grids['front_L_outer' if sign > 0 else 'front_R_inner']
        b, sf, sb, g = [grids[n] for n in ('back', 'sleeve_front_' + label, 'sleeve_back_' + label, 'gusset_' + label)]
        ab = positions[f[22:29, -1]]
        ad = positions[b[22:29, -1 if sign > 0 else 0]]
        bc, dc = positions[sf[:7, 0]], positions[sb[:7, -1]]
        u = np.linspace(0, 1, 7)[None, :, None]
        v = np.linspace(0, 1, 7)[:, None, None]
        A, B, D, E = ab[0], ab[-1], ad[-1], bc[-1]
        patch = (1-u)*ab[:, None] + u*dc[:, None] + (1-v)*ad[None] + v*bc[None] - ((1-u)*(1-v)*A + (1-u)*v*B + u*(1-v)*D + u*v*E)
        positions[g.ravel()] = patch.reshape(-1, 3)

    parent = np.arange(len(flat))
    def find(a):
        a = int(a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    seams = []
    source_edges = edge_table(source_q)
    for seam in pattern['seams']:
        a, b = np.array(seam['edge_a']), np.array(seam['edge_b'])
        la, lb = [np.linalg.norm(np.diff(flat[e], axis=0), axis=1) for e in (a, b)]
        assert max(abs(la-lb)) < 5e-7
        assert all(len(source_edges[tuple(sorted((int(i), int(j))))]) == 1 for edge in (a, b) for i, j in zip(edge[:-1], edge[1:]))
        gap = np.linalg.norm(positions[a] - positions[b], axis=1)
        assert gap.max() < 1e-8, (seam['id'], 'bad initial geometry', gap.max())
        for aa, bb in zip(a, b):
            parent[find(aa)] = find(bb)
        seams.append(dict(id=seam['id'], edge_a=a.tolist(), edge_b=b.tolist(), source_length_a_m=float(la.sum()), source_length_b_m=float(lb.sum()), source_max_segment_mismatch_m=float(max(abs(la-lb))), preunion_max_gap_m=float(gap.max()), closure='SHARED_VERTEX_UNION', samples=len(a)))
    roots = np.array([find(i) for i in range(len(flat))])
    keep = source_part != 10
    used = np.unique(source_q[keep])
    unique = np.unique(roots[used])
    root_index = {int(root): i for i, root in enumerate(unique)}
    remap = np.full(len(flat), -1, np.int32)
    remap[used] = [root_index[int(roots[i])] for i in used]
    vertices = positions[unique].tolist()
    quads = remap[source_q[keep]].tolist()
    parts = source_part[keep].tolist()
    provenance = np.flatnonzero(keep).tolist()
    source_vertex_lists = [[int(i) for i in used[roots[used] == root]] for root in unique]

    # Continuous attached inner facing: front V -> back neck -> opposite V.
    # Original collar rows supply the back's 0/6/12mm source width domain;
    # the two V extensions have explicit generated-face provenance (-1).
    fL, fR, back = grids['front_L_outer'], grids['front_R_inner'], grids['back']
    zrows = np.asarray(pattern['panels'][1]['pattern_uv_m']).reshape(*fL.shape, 2)[:, 0, 1]
    first = int(np.flatnonzero(zrows >= 1.32)[0])
    chain = np.r_[fL[first:, 0], back[-1, 27:15:-1], fR[-2:first-1:-1, 0]]
    near = np.r_[fL[first:, 1], back[-2, 27:15:-1], fR[-2:first-1:-1, 1]]
    band = np.zeros((len(chain), 3), np.int32)
    band[:, 0] = remap[chain]
    outer = np.array(vertices)[band[:, 0]]
    inward = unit(positions[chain] - positions[near])
    # Smooth only the offset directions at the two shoulder-to-neck corners.
    for k in range(1, len(inward)-1):
        if chain[k] in (int(fL[-1, 0]), int(back[-1, 16])):
            inward[k] = unit(inward[k-1] + inward[k] + inward[k+1])
    for row in range(len(chain)):
        for col in (1, 2):
            band[row, col] = len(vertices)
            vertices.append((outer[row] + inward[row] * col * .006).tolist())
            source_vertex_lists.append([])
    for row in range(len(chain)-1):
        for col in range(2):
            quads.append([int(band[row, col]), int(band[row+1, col]), int(band[row+1, col+1]), int(band[row, col+1])])
            parts.append(10)
            provenance.append(-1)
    collar = grids['narrow_inner_collar']
    for column, back_vertex in enumerate(back[-1, 16:29]):
        at = int(np.flatnonzero(remap[chain] == remap[back_vertex])[0])
        for row in range(3):
            remap[collar[row, column]] = band[at, row]
            source_vertex_lists[band[at, row]].append(int(collar[row, column]))

    vertices = np.asarray(vertices, np.float64)
    quads, flips, components = orient(np.asarray(quads, np.int32))
    parts = np.asarray(parts, np.int16)
    # The back reference winding must face +depth in Z-up, away from torso.
    center_face = np.flatnonzero(parts == 1)[len(np.flatnonzero(parts == 1)) // 2]
    a, b, c = vertices[quads[center_face, :3]]
    if np.cross(b-a, c-a)[1] < 0:
        quads = quads[:, ::-1]
        flips *= -1
    table, loops = loops_and_links(quads, len(vertices))
    assert components == 1 and len(loops) == 3
    # Export same points in canonical live prepared-world frame.
    vertices = vertices @ C[:3, :3]
    tri = np.stack([quads[:, [0, 1, 2]], quads[:, [0, 2, 3]]], axis=1).reshape(-1, 3)
    tri_quad = np.repeat(np.arange(len(quads)), 2)
    lengths = np.array([np.linalg.norm(vertices[a] - vertices[b]) for a, b in table])
    areas = np.linalg.norm(np.cross(vertices[tri[:, 1]]-vertices[tri[:, 0]], vertices[tri[:, 2]]-vertices[tri[:, 0]]), axis=1) / 2
    assert lengths.min() > 1e-4 and areas.min() > 1e-9, ('tiny edge/triangle', lengths.min(), areas.min())
    cross = proper_crossings(vertices, tri)
    loop_report = []
    for loop in loops:
        pp = vertices[loop]
        semantic = 'neck_lapels_and_hem_open_wrap_boundary' if len(loop) > 100 else ('left_wrist' if pp[:, 0].mean() > cx else 'right_wrist')
        loop_report.append(dict(semantic=semantic, vertices=loop, edge_count=len(loop), length_m=float(np.linalg.norm(pp-np.roll(pp, -1, axis=0), axis=1).sum()), bounds_m=[pp.min(0).tolist(), pp.max(0).tolist()]))
    offsets = np.r_[0, np.cumsum([len(x) for x in source_vertex_lists])]
    inverse_map = np.array([i for group in source_vertex_lists for i in group], np.int32)
    out = HERE / 'constructed_rest.npz'
    np.savez_compressed(out, positions_rest=vertices.astype(np.float32), triangles=tri, quad_faces=quads, quad_part_ids=parts, triangle_part_ids=np.repeat(parts, 2), triangle_quad_ids=tri_quad, quad_source_ids=np.array(provenance, np.int32), source_vertex_to_rest=remap, rest_vertex_source_offsets=offsets, rest_vertex_source_ids=inverse_map, source_flat_positions=flat.astype(np.float32), source_quad_faces=source_q, source_quad_part_ids=source_part, bone_names=live['bone_names'], current_rest_bone_world=live['prepared_joint_world_rest'], prepared_to_construction=C, construction_to_prepared=np.linalg.inv(C), proper_crossing_triangle_pairs=cross)
    report = dict(status='REST_STRUCTURE_READY_FOR_BINDING' if not len(cross) else 'REST_STRUCTURE_FAILED_SELF_INTERSECTION_STOP', source_pattern=dict(path=str(SOURCE), sha256=sha(SOURCE)), current_snapshot=dict(path=str(SNAPSHOT), sha256=sha(SNAPSHOT), raw=live_json['raw'], prepared=live_json['outputs']['base_prepared_png.glb']), output=dict(path=str(out), sha256=sha(out)), frame='LIVE prepared glTF world; metres +Y up +Z forward; native node defaults REST, never idle/guard', construction='Analytic live-joint developed panels; exact shared seam union; Coons armpit patches; continuous attached 12mm collar. No physical solver, relaxation, or old constructed/guard geometry read.', vertices=len(vertices), quads=len(quads), triangles=len(tri), single_connected_component=True, nonmanifold_edges=0, bad_vertex_links=0, degenerate_faces=0, minimum_edge_m=float(lengths.min()), minimum_triangle_area_m2=float(areas.min()), winding='globally consistent and back points outward', source_quads_flipped=np.flatnonzero(flips[:sum(keep)] < 0).tolist(), seam_count=len(seams), seams=seams, allowed_open_boundary_loops=loop_report, proper_crossing_count=len(cross), proper_crossing_triangle_pairs=cross.tolist(), proper_crossing_source_quad_pairs=np.array(provenance)[tri_quad[cross]].tolist(), coordinates=dict(prepared_to_construction=C.tolist(), construction_to_prepared=np.linalg.inv(C).tolist()), bone_anchor_points_construction={k:v.tolist() for k,v in bones.items() if k in ['Spine02', 'NeckTwist01', 'L_Upperarm', 'L_Forearm', 'L_Hand', 'R_Upperarm', 'R_Forearm', 'R_Hand']}, collar=dict(width_m=.012, single_layer=True, attached=True, source_collar_vertices_remapped=39, generated_v_extensions=True), left_outer_over_right_inner_nominal_gap_m=.005, source_input_arrays_read=['flat_rest_positions', 'quad_faces', 'quad_part_ids', 'bone_names'], source_input_arrays_not_geometry=['layout_positions','t_target_positions','guard_target_positions','rest_bone_world','guard_bone_world'], limitations=['No source body anatomical collision or cloth simulation certified.', 'No sculpted folds, thickness, UV, bake, final skin, animation, or device pass is claimed.', 'Hand bone minus 12mm is an explicit sleeve-end construction datum, not an anatomical wrist boundary.'])
    (HERE / 'structure_handoff.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:report[k] for k in ['status','vertices','quads','triangles','minimum_edge_m','minimum_triangle_area_m2','proper_crossing_count']}))
    if len(cross):
        print('CROSSING PAIRS', report['proper_crossing_source_quad_pairs'][:30])
        raise SystemExit(2)


if __name__ == '__main__':
    main()
