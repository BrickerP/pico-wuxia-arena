"""Independent, host-only preservation and surface audit for the two Right ROIs.

No asset writes, renderer, app, device, or producer invocation. Collision results
are complete triangle-pair sets at the three requested poses, not net counts or
continuous clearance claims. Only main() writes the requested verification JSON.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
import numpy as np

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
REPO = HERE.parents[5]
sys.path.insert(0, str(NATIVE))
import verify_hands as h

SOURCE_SHA = "3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0"
DAO_SHA = "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0"
POSES = (0., .5, 1.)
DIGITS = ("Thumb", "Index", "Mid", "Ring", "Pinky")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def primitive(document, primitive_index=0):
    require(len(document["meshes"]) == 1, "Expected one native hand mesh")
    return document["meshes"][0]["primitives"][primitive_index]


def attributes(document, binary, primitive_index=0):
    return {name: h.values(document, binary, index)
            for name, index in primitive(document, primitive_index)["attributes"].items()}


def faces(document, binary, primitive_index=0):
    return h.values(document, binary, primitive(document, primitive_index)["indices"]).reshape(-1, 3).astype(int)


def actual_skin(document, binary, time=None, primitive_index=0):
    """Actual source LBS in its Dao/player frame; None means node defaults."""
    world = h.sampled_worlds(document, binary, "grip" if time is not None else None,
                             0. if time is None else time)
    return h.skin(document, binary, primitive(document, primitive_index), world)


def skinned_normal_vectors(document, binary, time=None):
    """Mathematical inverse-transpose blended-LBS normals; no SDK/TBN claim."""
    a = attributes(document, binary)
    world = h.sampled_worlds(document, binary, "grip" if time is not None else None,
                             0. if time is None else time)
    skin = document["skins"][0]
    binds = h.values(document, binary, skin["inverseBindMatrices"]).reshape(-1, 4, 4).transpose(0, 2, 1)
    transforms = np.asarray([world[index] for index in skin["joints"]]) @ binds
    weights = a["WEIGHTS_0"].astype(float)
    spec = document["accessors"][primitive(document)["attributes"]["WEIGHTS_0"]]
    if spec.get("normalized"):
        weights /= np.iinfo(a["WEIGHTS_0"].dtype).max
    blend = np.sum(transforms[a["JOINTS_0"].astype(int)]*weights[:, :, None, None], axis=1)
    require((abs(np.linalg.det(blend[:, :3, :3])) > 1e-12).all(), "Singular skinned normal transform")
    normal = np.einsum("vij,vj->vi", np.linalg.inv(blend[:, :3, :3]).transpose(0, 2, 1), a["NORMAL"])
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    require(np.isfinite(normal).all(), "Nonfinite skinned normals")
    return normal


def actual_geometry(document, binary, time=None):
    pp, ff, offset = [], [], 0
    for primitive_index in range(len(document["meshes"][0]["primitives"])):
        p = actual_skin(document, binary, time, primitive_index)
        pp.append(p)
        ff.append(faces(document, binary, primitive_index)+offset)
        offset += len(p)
    return np.concatenate(pp), np.concatenate(ff)


def bind_geometry(document, binary):
    pp, ff, offset = [], [], 0
    for primitive_index in range(len(document["meshes"][0]["primitives"])):
        p = attributes(document, binary, primitive_index)["POSITION"]
        pp.append(p)
        ff.append(faces(document, binary, primitive_index)+offset)
        offset += len(p)
    return np.concatenate(pp), np.concatenate(ff)


def topology_health(document, binary):
    points, triangles = bind_geometry(document, binary)
    weld = position_weld(points)
    edges = np.sort(np.concatenate((weld[triangles[:, [0, 1]]], weld[triangles[:, [1, 2]]],
                                     weld[triangles[:, [2, 0]]])), axis=1)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    result = {"position_welded_open_edges": int(np.count_nonzero(counts == 1)),
              "position_welded_nonmanifold_edges": int(np.count_nonzero(counts > 2)),
              "collapsed_welded_triangles": int(np.count_nonzero(np.any(
                  np.sort(weld[triangles], axis=1)[:, 1:] == np.sort(weld[triangles], axis=1)[:, :-1], axis=1)))}
    require(all(value == 0 for value in result.values()), "Open seam, nonmanifold edge, or collapsed welded triangle")
    return result


def skin_regions(document, binary):
    """Weight-derived hand/palm/forearm/digit masks without image assumptions."""
    a = attributes(document, binary)
    joints, weights = a["JOINTS_0"].astype(int), a["WEIGHTS_0"].astype(float)
    spec = document["accessors"][primitive(document)["attributes"]["WEIGHTS_0"]]
    if spec.get("normalized"):
        weights /= np.iinfo(a["WEIGHTS_0"].dtype).max
    names = [document["nodes"][i]["name"] for i in document["skins"][0]["joints"]]
    dense = np.zeros((len(joints), len(names)))
    for slot in range(joints.shape[1]):
        np.add.at(dense, (np.arange(len(joints)), joints[:, slot]), weights[:, slot])
    def influence(test):
        ids = [i for i, name in enumerate(names) if test(name)]
        return dense[:, ids].sum(axis=1) if ids else np.zeros(len(joints))
    digits = {d: influence(lambda n, d=d: n.startswith("R_" + d)) for d in DIGITS}
    palm = influence(lambda n: n == "R_Hand")
    forearm = influence(lambda n: n.startswith("R_Forearm"))
    hand = palm + sum(digits.values())
    return {"names": names, "dense_weights": dense, "palm_weight": palm,
            "forearm_weight": forearm, "hand_weight": hand,
            "digit_weights": digits, "dominant_joint": np.argmax(dense, axis=1),
            "hand_vertices": np.flatnonzero(hand > .5),
            "finger_vertices": np.flatnonzero(sum(digits.values()) > .01)}


def position_weld(points, tolerance=1e-7):
    """Equivalent bind-space points include UV seams, never animation contacts."""
    points = np.asarray(points, float)
    require(np.isfinite(points).all(), "Nonfinite position weld input")
    cells = np.floor(points / tolerance).astype(np.int64)
    buckets, ids, representatives = {}, np.empty(len(points), int), []
    offsets = [(x, y, z) for x in (-1, 0, 1) for y in (-1, 0, 1) for z in (-1, 0, 1)]
    for i, (point, cell) in enumerate(zip(points, cells)):
        found = None
        for offset in offsets:
            for candidate in buckets.get(tuple(cell + offset), ()):
                if np.linalg.norm(point - points[candidate]) <= tolerance:
                    found = ids[candidate]
                    break
            if found is not None:
                break
        if found is None:
            found = len(representatives)
            representatives.append(i)
        ids[i] = found
        buckets.setdefault(tuple(cell), []).append(i)
    return ids


def _point_in_triangle(point, triangle, tolerance):
    first, second = triangle[1] - triangle[0], triangle[2] - triangle[0]
    offset = point - triangle[0]
    aa, ab, bb = first @ first, first @ second, second @ second
    denominator = aa * bb - ab * ab
    if abs(denominator) < 1e-24:
        return False
    u = (bb * (offset @ first) - ab * (offset @ second)) / denominator
    v = (aa * (offset @ second) - ab * (offset @ first)) / denominator
    return u >= -tolerance and v >= -tolerance and u + v <= 1 + tolerance


def triangles_cross(first, second, tolerance=1e-7):
    """Match the repository's noncoplanar edge/face crossing convention."""
    for triangle, target in ((first, second), (second, first)):
        normal = np.cross(target[1] - target[0], target[2] - target[0])
        length = np.linalg.norm(normal)
        if length < 1e-14:
            continue
        normal /= length
        distances = (triangle - target[0]) @ normal
        for index in range(3):
            after = (index + 1) % 3
            start, end = distances[index], distances[after]
            if ((start > tolerance and end > tolerance)
                    or (start < -tolerance and end < -tolerance)):
                continue
            difference = start - end
            if abs(difference) < tolerance:
                continue
            fraction = start / difference
            if -tolerance <= fraction <= 1 + tolerance:
                point = triangle[index] + fraction * (triangle[after] - triangle[index])
                if _point_in_triangle(point, target, tolerance):
                    return True
    return False


def crossing_pairs(points, triangles, other_points=None, other_faces=None,
                   weld_ids=None, first_face_ids=None, second_face_ids=None):
    """Full canonical face pairs, AABB accelerated; weld adjacency is excluded."""
    same = other_points is None
    a = np.asarray(points)[triangles]
    b = a if same else np.asarray(other_points)[other_faces]
    low, high = b.min(axis=1), b.max(axis=1)
    selected_a = np.arange(len(a)) if first_face_ids is None else np.asarray(first_face_ids, int)
    selected_b = np.arange(len(b)) if second_face_ids is None else np.asarray(second_face_ids, int)
    result = []
    welded = weld_ids[triangles] if same and weld_ids is not None else triangles
    for i in selected_a:
        ids = selected_b[((high[selected_b] >= a[i].min(axis=0)-1e-7)
                          & (low[selected_b] <= a[i].max(axis=0)+1e-7)).all(axis=1)]
        if same:
            ids = ids[ids > i]
            ids = ids[~np.any(welded[ids, :, None] == welded[i][None, None, :], axis=(1, 2))]
        for j in ids:
            if triangles_cross(a[i], b[j]):
                result.append((int(i), int(j)))
    return set(result)


def closest_surface(points, triangles, batch_size=64):
    """Closest triangle, point and distance, bounded-memory vector arithmetic."""
    triangles = np.asarray(triangles, float)
    require(len(triangles) > 0, "Empty target surface")
    best_d, best_f, best_p = [], [], []
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    ab, ac = b-a, c-a
    aa, bb, cc = (ab*ab).sum(axis=1), (ab*ac).sum(axis=1), (ac*ac).sum(axis=1)
    denominator = aa*cc-bb*bb
    for start in range(0, len(points), batch_size):
        p = np.asarray(points[start:start+batch_size], float)
        ap = p[:, None, :]-a
        d, e = (ap*ab).sum(axis=2), (ap*ac).sum(axis=2)
        u = np.divide(d*cc-e*bb, denominator, out=np.zeros_like(d), where=abs(denominator)>1e-30)
        v = np.divide(e*aa-d*bb, denominator, out=np.zeros_like(d), where=abs(denominator)>1e-30)
        projected = a+u[..., None]*ab+v[..., None]*ac
        valid = (u >= 0) & (v >= 0) & (u+v <= 1) & (abs(denominator)>1e-30)
        distances = np.where(valid, ((p[:, None]-projected)**2).sum(axis=2), np.inf)
        locations = projected.copy()
        for first, second in ((a, b), (b, c), (c, a)):
            edge = second-first
            ratio = np.divide(((p[:, None]-first)*edge).sum(axis=2),
                              (edge*edge).sum(axis=1), out=np.zeros_like(d),
                              where=(edge*edge).sum(axis=1)>1e-30)
            location = first+np.clip(ratio, 0, 1)[..., None]*edge
            distance = ((p[:, None]-location)**2).sum(axis=2)
            better = distance < distances
            distances[better], locations[better] = distance[better], location[better]
        face_ids = np.argmin(distances, axis=1)
        row = np.arange(len(p))
        best_d.extend(np.sqrt(distances[row, face_ids]))
        best_f.extend(face_ids)
        best_p.extend(locations[row, face_ids])
    return np.asarray(best_d), np.asarray(best_f), np.asarray(best_p)


def contains(points, triangles, batch_size=32):
    """Absolute solid-angle winding for closed surfaces, independent of winding."""
    result = []
    for start in range(0, len(points), batch_size):
        p = np.asarray(points[start:start+batch_size], float)
        rays = triangles[None]-p[:, None, None]
        lengths = np.linalg.norm(rays, axis=3)
        a, b, c = rays[:, :, 0], rays[:, :, 1], rays[:, :, 2]
        la, lb, lc = lengths[:, :, 0], lengths[:, :, 1], lengths[:, :, 2]
        numerator = np.einsum("bfi,bfi->bf", a, np.cross(b, c))
        denominator = la*lb*lc+(a*b).sum(axis=2)*lc+(b*c).sum(axis=2)*la+(c*a).sum(axis=2)*lb
        result.extend(abs((2*np.arctan2(numerator, denominator)).sum(axis=1)) > 2*math.pi)
    return np.asarray(result, bool)


def dao_geometry(path):
    require(digest(path) == DAO_SHA, "Actual Dao identity mismatch")
    d, binary = h.read(path)
    worlds = h.sampled_worlds(d, binary)
    result = {}
    for node_id, node in enumerate(d["nodes"]):
        if "mesh" not in node:
            continue
        pp, ff, offset = [], [], 0
        for prim in d["meshes"][node["mesh"]]["primitives"]:
            p = h.values(d, binary, prim["attributes"]["POSITION"]).astype(float)
            if "skin" in node:
                p = h.skin(d, binary, prim, worlds, node["skin"])
            else:
                p = (np.column_stack((p, np.ones(len(p)))) @ worlds[node_id].T)[:, :3]
            f = h.values(d, binary, prim["indices"]).reshape(-1, 3).astype(int)
            pp.append(p); ff.append(f+offset); offset += len(p)
        p, f = np.concatenate(pp), np.concatenate(ff)
        welded = position_weld(p)
        edges = np.sort(np.concatenate((welded[f[:, [0, 1]]], welded[f[:, [1, 2]]],
                                        welded[f[:, [2, 0]]])), axis=1)
        _, counts = np.unique(edges, axis=0, return_counts=True)
        result[node["name"]] = {"points": p, "faces": f, "closed": bool(np.all(counts == 2))}
    require("Handle core" in result, "Actual Dao lacks Handle core")
    return result


def contact_samples(points, triangles, vertex_ids=None, face_ids=None):
    vids = np.arange(len(points)) if vertex_ids is None else np.asarray(vertex_ids, int)
    fids = np.arange(len(triangles)) if face_ids is None else np.asarray(face_ids, int)
    chosen = triangles[fids]
    edges = np.unique(np.sort(np.concatenate((chosen[:, [0, 1]], chosen[:, [1, 2]],
                                              chosen[:, [2, 0]])), axis=1), axis=0)
    sample_points = np.concatenate((points[vids], points[chosen].mean(axis=1), points[edges].mean(axis=1)))
    labels = (["v:"+str(i) for i in vids]+["f:"+str(i) for i in fids]
              +["e:"+str(i)+","+str(j) for i, j in edges])
    return sample_points, labels


def contact_audit(points, triangles, dao, vertex_ids=None, face_ids=None):
    samples, labels = contact_samples(points, triangles, vertex_ids, face_ids)
    result = {}
    for name, geometry in dao.items():
        p, f = geometry["points"], geometry["faces"]
        pairs = crossing_pairs(points, triangles, p, f)
        row = {"closed": geometry["closed"], "face_pairs": sorted(pairs),
               "surface_crossing_pairs": len(pairs)}
        if geometry["closed"]:
            distance, near_faces, _ = closest_surface(samples, p[f])
            inside = contains(samples, p[f]) & (distance > 1e-7)
            row["inside_samples"] = {labels[i]: float(distance[i]*1000) for i in np.flatnonzero(inside)}
            row["maximum_sample_penetration_mm"] = float(distance[inside].max()*1000) if inside.any() else 0.
            row["deepest_nearest_face"] = int(near_faces[np.argmax(np.where(inside, distance, -1))]) if inside.any() else None
        result[name] = row
    return result


def surface_metrics(points, triangles, face_ids):
    """Area/edge/dihedral metrics describe roughness; visual acceptance is separate."""
    face_ids = np.asarray(face_ids, int)
    selected = triangles[face_ids]
    tri = points[selected]
    cross = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
    area = np.linalg.norm(cross, axis=1)/2
    normal = np.divide(cross, 2*area[:, None], out=np.zeros_like(cross), where=area[:, None]>1e-18)
    edge = np.concatenate((selected[:, [0, 1]], selected[:, [1, 2]], selected[:, [2, 0]]))
    edge = np.unique(np.sort(edge, axis=1), axis=0)
    length = np.linalg.norm(points[edge[:, 0]]-points[edge[:, 1]], axis=1)
    incidence = {}
    weld = position_weld(points)
    for local_id, face in enumerate(weld[selected]):
        for i, j in ((0, 1), (1, 2), (2, 0)):
            incidence.setdefault(tuple(sorted((int(face[i]), int(face[j])))), []).append(local_id)
    angles = [math.degrees(math.acos(float(np.clip(normal[a] @ normal[b], -1, 1))))
              for ids in incidence.values() if len(ids) == 2 for a, b in [ids]]
    def summary(rows):
        return {"min": float(np.min(rows)), "p50": float(np.median(rows)),
                "p95": float(np.percentile(rows, 95)), "max": float(np.max(rows))} if len(rows) else None
    return {"faces": len(face_ids), "surface_area_mm2": float(area.sum()*1e6),
            "triangle_area_mm2": summary(area*1e6), "edge_length_mm": summary(length*1000),
            "adjacent_dihedral_degrees": summary(angles),
            "degenerate_faces": int(np.count_nonzero(area < 1e-14))}


def exact_rig_and_resources(source, sb, candidate, cb):
    """Node/default q, all animation keys/times and IBM bytes are immutable."""
    for key in ("nodes", "skins", "animations", "scenes", "scene", "materials", "textures", "images",
                "samplers", "extensionsUsed", "extensionsRequired"):
        require(source.get(key) == candidate.get(key), "Protected JSON changed: "+key)
    protected = []
    for skin in source["skins"]:
        protected.append(skin["inverseBindMatrices"])
    for animation in source["animations"]:
        for sampler in animation["samplers"]:
            protected.extend((sampler["input"], sampler["output"]))
    for index in sorted(set(protected)):
        require(np.array_equal(h.values(source, sb, index), h.values(candidate, cb, index)),
                "Protected animation or IBM payload changed: "+str(index))
    for index, image in enumerate(source["images"]):
        require(h.image_bytes(source, sb, index) == h.image_bytes(candidate, cb, index), "KTX payload changed")
        payload = h.image_bytes(candidate, cb, index)
        require(payload[:12] == b"\xabKTX 20\xbb\r\n\x1a\n", "Expected reused KTX2")
        import struct
        width, height = struct.unpack_from("<II", payload, 20)
        require((width, height) == (1536, 1536), "Expected 1536 KTX atlas")
    require(len(source["images"]) == 3, "Expected three reused KTX atlas images")
    require({k: val for k, val in source["meshes"][0].items() if k != "primitives"}
            == {k: val for k, val in candidate["meshes"][0].items() if k != "primitives"},
            "Mesh metadata changed")
    require({k: val for k, val in primitive(source).items() if k not in ("attributes", "indices")}
            == {k: val for k, val in primitive(candidate).items() if k not in ("attributes", "indices")},
            "Primitive material, mode, or metadata changed")
    require(len(source["meshes"][0]["primitives"]) == len(candidate["meshes"][0]["primitives"]),
            "Primitive count changed")
    for index in range(1, len(source["meshes"][0]["primitives"])):
        require(primitive(source, index) == primitive(candidate, index), "Closure descriptor changed")
        for name, old in attributes(source, sb, index).items():
            require(np.array_equal(old, attributes(candidate, cb, index)[name]), "Closure attribute changed: "+name)
        require(np.array_equal(faces(source, sb, index), faces(candidate, cb, index)), "Closure topology changed")
    return {"nodes_default_quaternions_and_frames_exact": True,
            "all_animation_keys_times_interpolation_exact": True, "inverse_bind_matrices_exact": True,
            "bone_lengths_and_grip_anchors_exact": True, "three_1536_KTX_payloads_exact": True}


def mesh_health(document, binary, primitive_index=0):
    a, f = attributes(document, binary, primitive_index), faces(document, binary, primitive_index)
    require(primitive(document, primitive_index).get("mode", 4) == 4, "Expected triangle-list mode")
    require(document["accessors"][primitive(document, primitive_index)["indices"]]["componentType"]
            in (5121, 5123, 5125), "Invalid triangle index type")
    n = len(a["POSITION"])
    require(sum(len(faces(document, binary, i)) for i in range(len(document["meshes"][0]["primitives"]))) <= 8000,
            "Triangle budget exceeded")
    require(f.min() >= 0 and f.max() < n, "Face index out of bounds")
    for name, values in a.items():
        require(len(values) == n and np.isfinite(values).all(), "Nonfinite or wrong-length "+name)
    for name in ("NORMAL",):
        require(name in a, "Missing "+name)
        require(np.max(abs(np.linalg.norm(a[name], axis=1)-1)) < 2e-4, "Nonunit "+name)
    if "TANGENT" in a:
        require(np.max(abs(np.linalg.norm(a["TANGENT"][:, :3], axis=1)-1)) < 2e-4, "Nonunit tangent")
        require(np.max(abs((a["TANGENT"][:, :3]*a["NORMAL"]).sum(axis=1))) < 2e-4,
                "Tangent is not normal-orthogonal")
        require(np.isin(a["TANGENT"][:, 3], (-1., 1.)).all(), "Invalid tangent handedness")
    actual_skin(document, binary, primitive_index=primitive_index)
    cross = np.cross(a["POSITION"][f[:, 1]]-a["POSITION"][f[:, 0]],
                     a["POSITION"][f[:, 2]]-a["POSITION"][f[:, 0]])
    area = np.linalg.norm(cross, axis=1)
    require(np.all(area > 1e-14), "Degenerate triangle")
    dot = (cross[:, None]*a["NORMAL"][f]).sum(axis=2)/area[:, None]
    return {"vertices": n, "triangles": len(f), "finite_skin_and_attributes": True,
            "nonunit_normals": 0, "tangent_present": "TANGENT" in a,
            "normal_opposes_winding_corners": np.argwhere(dot < -1e-5).tolist(),
            "normal_opposes_winding_corner_count": int(np.count_nonzero(dot < -1e-5))}


def verify_delta(source, sb, candidate, cb, delta, constraints):
    """Verify geometry against an independently pinned old-source ROI contract."""
    sa, ca = attributes(source, sb), attributes(candidate, cb)
    sf, cf = faces(source, sb), faces(candidate, cb)
    require(set(sa) == set(ca), "Attribute set changed")
    require(constraints["source_sha256"] == SOURCE_SHA, "ROI constraints source mismatch")
    require(set(delta["rois"]) == set(constraints["rois"]) and len(delta["rois"]) == 2,
            "Exactly the two pinned ROIs are required")
    allowed_v, allowed_f = set(), set()
    for name, roi in constraints["rois"].items():
        require(set(delta["rois"][name]["source_vertex_ids"]) == set(roi["source_vertex_ids"]),
                "Source vertex ROI differs: "+name)
        require(set(delta["rois"][name]["source_face_ids"]) == set(roi["source_face_ids"]),
                "Source face ROI differs: "+name)
        allowed_v.update(roi["source_vertex_ids"])
        allowed_f.update(roi["source_face_ids"])
    support_f = set(constraints.get("source_support_face_ids", allowed_f))
    require(set(delta.get("source_support_face_ids", allowed_f)) == support_f,
            "Conforming subdivision support differs from pinned source faces")
    require(allowed_f <= support_f, "ROI missing from topology support")
    vm = np.asarray(delta["candidate_vertex_to_source"], int)
    fm = np.asarray(delta["candidate_face_to_source_face"], int)
    require(vm.shape == (len(ca["POSITION"]),) and fm.shape == (len(cf),), "Invalid topology mapping size")
    require((vm >= -1).all() and (vm < len(sa["POSITION"])).all(), "Invalid source vertex mapping")
    require((fm >= 0).all() and (fm < len(sf)).all(), "Invalid source face mapping")
    for old in set(range(len(sa["POSITION"])))-allowed_v:
        require(np.count_nonzero(vm == old) == 1, "Protected source vertex missing or duplicated")
    retained = np.flatnonzero(vm >= 0)
    changed = {}
    for name in sa:
        differs = np.flatnonzero(np.any(ca[name][retained] != sa[name][vm[retained]], axis=1))
        old_changed = set(vm[retained[differs]].tolist())
        if name in ("JOINTS_0", "WEIGHTS_0", "TEXCOORD_0"):
            require(not old_changed, "Existing UV or skin influences changed: "+name)
        else:
            require(old_changed <= allowed_v, "Attribute changed outside pinned ROI: "+name)
        changed[name] = sorted(old_changed)
    for old in set(range(len(sf)))-support_f:
        ids = np.flatnonzero(fm == old)
        require(len(ids) == 1, "Protected face missing or subdivided")
        require(np.array_equal(vm[cf[ids[0]]], sf[old]), "Protected face topology or winding changed")
    documented = {int(row["candidate_vertex_id"]): row for row in delta.get("candidate_added_vertices", [])}
    require(set(documented) == set(np.flatnonzero(vm == -1).tolist()), "Inserted vertex mapping incomplete")
    sdense, cdense = skin_regions(source, sb)["dense_weights"], skin_regions(candidate, cb)["dense_weights"]
    for vertex, row in documented.items():
        old_face, bary = int(row["source_face_id"]), np.asarray(row["barycentric"], float)
        require(old_face in support_f, "Inserted vertex source is outside ROI support")
        require(np.array_equal(np.asarray(row["source_vertex_ids"], int), sf[old_face]),
                "Inserted source triangle vertex IDs differ")
        require(bary.shape == (3,) and np.isfinite(bary).all() and (bary >= -1e-7).all()
                and abs(bary.sum()-1) < 1e-7, "Invalid inserted vertex barycentric mapping")
        expected_uv = bary @ sa["TEXCOORD_0"][sf[old_face]]
        require(np.max(abs(ca["TEXCOORD_0"][vertex]-expected_uv)) < 2e-6, "Inserted UV is not source-barycentric")
        expected_weight = bary @ sdense[sf[old_face]]
        top = np.argsort(expected_weight)[-4:]
        truncated = np.zeros_like(expected_weight)
        truncated[top] = expected_weight[top]
        truncated /= truncated.sum()
        require(np.max(abs(cdense[vertex]-truncated)) < 2e-6, "Inserted weights are not source-barycentric top4")
    # Inserting a source-face child must stay inside that ROI's geometric skin.
    for name, roi in constraints["rois"].items():
        expected_faces = set(np.flatnonzero(np.isin(fm, roi["source_face_ids"])).tolist())
        require(set(delta["rois"][name]["candidate_face_ids"]) == expected_faces,
                "Candidate face ROI does not match provenance: "+name)
        require(set(delta["rois"][name]["candidate_vertex_ids"]) <= set(np.unique(cf[list(expected_faces)]).tolist()),
                "Candidate vertex ROI lies outside mapped faces: "+name)
    # Reversed child winding is forbidden, even if normals were also flipped.
    old_normal = np.cross(sa["POSITION"][sf[:, 1]]-sa["POSITION"][sf[:, 0]],
                          sa["POSITION"][sf[:, 2]]-sa["POSITION"][sf[:, 0]])
    new_normal = np.cross(ca["POSITION"][cf[:, 1]]-ca["POSITION"][cf[:, 0]],
                          ca["POSITION"][cf[:, 2]]-ca["POSITION"][cf[:, 0]])
    require(((old_normal[fm]*new_normal).sum(axis=1) > 0).all(), "Triangle winding reversed")
    def uv_determinants(uv, ff):
        tri = uv[ff]
        a, b = tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]
        return a[:, 0]*b[:, 1]-a[:, 1]*b[:, 0]
    old_uv, new_uv = uv_determinants(sa["TEXCOORD_0"], sf), uv_determinants(ca["TEXCOORD_0"], cf)
    nondegenerate_uv = abs(old_uv[fm]) > 1e-14
    require((old_uv[fm][nondegenerate_uv]*new_uv[nondegenerate_uv] > 0).all(),
            "UV triangle winding or derived tangent handedness changed")
    old_weld = position_weld(sa["POSITION"])
    new_weld = position_weld(ca["POSITION"])
    for group in np.unique(old_weld):
        old_ids = np.flatnonzero(old_weld == group)
        ids = np.flatnonzero(np.isin(vm, old_ids))
        require(len(np.unique(new_weld[ids])) <= 1, "Position-weld UV seam split")
    candidate_health = mesh_health(candidate, cb)
    source_health = mesh_health(source, sb)
    source_bad = set(tuple(x) for x in source_health["normal_opposes_winding_corners"])
    for face, corner in candidate_health["normal_opposes_winding_corners"]:
        old_face, old_vertex = int(fm[face]), int(vm[cf[face, corner]])
        source_corners = np.flatnonzero(sf[old_face] == old_vertex)
        require(any((old_face, int(c)) in source_bad for c in source_corners),
                "New normal opposes triangle winding")
    # All protected skin points remain exact at defaults and requested grip poses.
    protected = np.flatnonzero((vm >= 0) & ~np.isin(vm, list(allowed_v)))
    max_motion = {}
    inserted_motion = {}
    posed_normals = {}
    for time in (None, *POSES):
        old_p, new_p = actual_skin(source, sb, time), actual_skin(candidate, cb, time)
        error = float(np.max(abs(new_p[protected]-old_p[vm[protected]]))) if len(protected) else 0.
        require(error < 1e-10, "Protected skin/ventral contact moved")
        max_motion[str(time)] = error
        old_cross = np.cross(old_p[sf[:, 1]]-old_p[sf[:, 0]], old_p[sf[:, 2]]-old_p[sf[:, 0]])
        new_cross = np.cross(new_p[cf[:, 1]]-new_p[cf[:, 0]], new_p[cf[:, 2]]-new_p[cf[:, 0]])
        require(((old_cross[fm]*new_cross).sum(axis=1) > 0).all(),
                "Animated candidate triangle inverted relative to source parent")
        old_n, new_n = skinned_normal_vectors(source, sb, time), skinned_normal_vectors(candidate, cb, time)
        old_dot = (old_cross[:, None]*old_n[sf]).sum(axis=2)/np.linalg.norm(old_cross, axis=1)[:, None]
        new_dot = (new_cross[:, None]*new_n[cf]).sum(axis=2)/np.linalg.norm(new_cross, axis=1)[:, None]
        old_bad = set(np.flatnonzero((old_dot < -1e-5).any(axis=1)).tolist())
        new_bad = set(np.flatnonzero((new_dot < -1e-5).any(axis=1)).tolist())
        new_parents = set(fm[list(new_bad)].tolist())-old_bad
        require(not new_parents, "New skinned normal opposes posed triangle winding")
        posed_normals[str(time)] = {"source_bad_face_ids": sorted(old_bad),
                                   "candidate_bad_face_ids": sorted(new_bad),
                                   "new_bad_source_face_ids": sorted(new_parents),
                                   "method": "inverse transpose of actual blended LBS affine, normalized"}
        rows = []
        for vertex, row in documented.items():
            old_face = int(row["source_face_id"])
            expected = np.asarray(row["barycentric"]) @ old_p[sf[old_face]]
            distance = closest_surface(new_p[[vertex]], old_p[sf[[old_face]]])[0][0]*1000
            rows.append((vertex, old_face, float(distance), float(np.linalg.norm(new_p[vertex]-expected)*1000)))
        inside = [row for row in rows if row[1] in allowed_f]
        outside = [row for row in rows if row[1] not in allowed_f]
        def motion_summary(values):
            return {"count": len(values), "max_mm": max((r[2] for r in values), default=0.),
                    "p95_mm": float(np.percentile([r[2] for r in values], 95)) if values else 0.,
                    "max_corresponding_bary_point_drift_mm": max((r[3] for r in values), default=0.),
                    "largest_witnesses": [{"candidate_vertex": v, "source_face": f, "nearest_parent_surface_mm": d,
                                            "corresponding_bary_point_drift_mm": b}
                                           for v, f, d, b in sorted(values, key=lambda r: -r[2])[:12]]}
        inserted_motion[str(time)] = {"ROI": motion_summary(inside), "split_support_outside_ROI": motion_summary(outside)}
        require(max((r[2] for r in outside), default=0.) < constraints.get("support_skin_max_drift_mm", .01),
                "Inserted non-ROI split-border skin drift exceeds pinned tolerance")
    return {"passed": True, "source_ROI_vertices": len(allowed_v), "source_ROI_faces": len(allowed_f),
            "inserted_vertices": len(documented), "changed_source_vertices_by_attribute": changed,
            "protected_skin_max_error_metres_by_pose": max_motion,
            "inserted_vertex_actual_LBS_to_source_face_barycentric_skin_drift": inserted_motion,
            "posed_normal_winding": posed_normals,
            "winding_and_position_weld_seams_preserved": True,
            "source_nondegenerate_UV_triangle_handedness_preserved": True,
            "source_degenerate_UV_faces": np.flatnonzero(abs(old_uv) <= 1e-14).tolist(),
            "tangent_scope": "No authored source TANGENT; no runtime tangent-generation or normal-map decoder claim",
            "candidate_face_to_source_face": fm.tolist(), "candidate_vertex_to_source": vm.tolist()}


def mapped_pair_delta(source_pairs, candidate_pairs, face_map, self_collision=False,
                      source_faces=None, source_weld=None):
    """A removed old pair never cancels an unrelated new pair."""
    mapped = set()
    for first, second in candidate_pairs:
        a = int(face_map[first])
        b = int(face_map[second]) if self_collision else int(second)
        if self_collision:
            if a == b:
                # Intersecting siblings from one subdivided old triangle are new.
                mapped.add((a, a))
                continue
            a, b = sorted((a, b))
            if source_faces is not None and source_weld is not None:
                if np.intersect1d(source_weld[source_faces[a]], source_weld[source_faces[b]]).size:
                    continue
        mapped.add((a, b))
    baseline = set(tuple(pair) for pair in source_pairs)
    return {"new_source_face_pairs": sorted(mapped-baseline),
            "removed_source_face_pairs": sorted(baseline-mapped),
            "mapped_candidate_source_face_pairs": sorted(mapped)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--dao", type=Path, required=True)
    parser.add_argument("--delta", type=Path, default=HERE/"roi_delta.json")
    parser.add_argument("--constraints", type=Path, default=HERE/"roi_constraints.json")
    parser.add_argument("--refresh-baseline", action="store_true")
    parser.add_argument("--run-tests", action="store_true")
    parser.add_argument("--output", type=Path, default=HERE/"verification.json")
    args = parser.parse_args()
    require(digest(args.source) == SOURCE_SHA, "Pinned Right source identity mismatch")
    source, sb = h.read(args.source)
    dao = dao_geometry(args.dao)
    regions, primary_faces = skin_regions(source, sb), faces(source, sb)
    bind_p, f = bind_geometry(source, sb)
    hand_faces = np.flatnonzero((regions["hand_weight"][primary_faces] > .5).any(axis=1))
    weld = position_weld(bind_p)
    report = {"source": str(args.source), "source_sha256": SOURCE_SHA, "actual_dao_sha256": DAO_SHA,
              "scope": "Discrete default/grip@0/.5/1 checks; not continuous clearance or visual/native acceptance",
              "source_health": mesh_health(source, sb), "source_poses": {},
              "known_inherited_limitations": ["Source open/mid against fixed actual Dao already invade",
                 "Source closed has shallow core points and inherited self intersections",
                 "No claim of zero collisions across grip curve", "Visual acceptance belongs to Root"]}
    if args.output.exists() and not args.refresh_baseline:
        cached = json.loads(args.output.read_text())
        if cached.get("source_sha256") == SOURCE_SHA and cached.get("actual_dao_sha256") == DAO_SHA:
            report["source_poses"] = cached["source_poses"]
            report["source_collision_baseline_reused"] = True
    if not report["source_poses"]:
        for time in POSES:
            p, f = actual_geometry(source, sb, time)
            self_pairs = crossing_pairs(p, f, weld_ids=weld)
            report["source_poses"][str(time)] = {"self_face_pairs": sorted(self_pairs),
                 "self_pair_count": len(self_pairs),
                 "actual_dao": contact_audit(p, f, dao, regions["hand_vertices"], hand_faces)}
    if args.candidate:
        candidate, cb = h.read(args.candidate)
        failures = []
        report["candidate_sha256"] = digest(args.candidate)
        delta = json.loads(args.delta.read_text())
        require(delta["source_sha256"] == SOURCE_SHA and delta["candidate_sha256"] == report["candidate_sha256"],
                "ROI delta asset identity mismatch")
        constraints = json.loads(args.constraints.read_text())
        for name, call in [("rig_resources", lambda: exact_rig_and_resources(source, sb, candidate, cb)),
                           ("candidate_health", lambda: mesh_health(candidate, cb)),
                           ("candidate_topology", lambda: topology_health(candidate, cb)),
                           ("ROI_preservation", lambda: verify_delta(source, sb, candidate, cb, delta, constraints))]:
            try:
                report[name] = call()
            except (ValueError, KeyError, IndexError) as error:
                failures.append(name+": "+str(error))
                report[name] = {"passed": False, "error": str(error)}
        c_regions = skin_regions(candidate, cb)
        cp_bind, cf = bind_geometry(candidate, cb)
        c_primary_faces = faces(candidate, cb)
        c_hand_faces = np.flatnonzero((c_regions["hand_weight"][c_primary_faces] > .5).any(axis=1))
        c_weld = position_weld(cp_bind)
        fm = np.r_[delta["candidate_face_to_source_face"],
                   np.arange(len(primary_faces), len(f))]
        report["candidate_poses"] = {}
        report["surface_ROI_metrics"] = {}
        for time in POSES:
            p, _ = actual_geometry(candidate, cb, time)
            old_p, _ = actual_geometry(source, sb, time)
            self_pairs = crossing_pairs(p, cf, weld_ids=c_weld)
            self_delta = mapped_pair_delta(report["source_poses"][str(time)]["self_face_pairs"],
                                            self_pairs, fm, True, f, weld)
            dao_contact = contact_audit(p, cf, dao, c_regions["hand_vertices"], c_hand_faces)
            row = {"self_face_pairs": sorted(self_pairs), "self_pair_count": len(self_pairs),
                   "self_pair_delta": self_delta, "actual_dao": dao_contact}
            if self_delta["new_source_face_pairs"]:
                failures.append("New self intersection pairs at "+str(time))
            for name, contact in dao_contact.items():
                source_contact = report["source_poses"][str(time)]["actual_dao"][name]
                contact["face_pair_delta"] = mapped_pair_delta(source_contact["face_pairs"], contact["face_pairs"], fm)
                if contact["face_pair_delta"]["new_source_face_pairs"]:
                    failures.append("New actual Dao crossing pairs: "+name+" at "+str(time))
                if contact["closed"] and contact["maximum_sample_penetration_mm"] > source_contact["maximum_sample_penetration_mm"]+.01:
                    failures.append("Deeper actual Dao samples: "+name+" at "+str(time))
            report["candidate_poses"][str(time)] = row
            report["surface_ROI_metrics"][str(time)] = {name: {
                "before": surface_metrics(old_p, f, roi["source_face_ids"]),
                "after": surface_metrics(p, cf, delta["rois"][name]["candidate_face_ids"])}
                for name, roi in constraints["rois"].items()}
        report["failures"] = failures
        report["numeric_preservation_passed"] = not failures
        report["visual_acceptance"] = "Pending independent Root before/after inspection"
        report["freeze"] = {"verifier_sha256": digest(Path(__file__)), "delta_sha256": digest(args.delta),
                            "constraints_sha256": digest(args.constraints),
                            "tests_sha256": digest(HERE/"test_verify_surface.py")}
        require(digest(args.candidate) == report["candidate_sha256"], "Candidate changed during audit")
    require(digest(args.source) == SOURCE_SHA and digest(args.dao) == DAO_SHA, "Pinned source changed during audit")
    if args.run_tests:
        command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(HERE), "-p", "test_verify_surface.py"]
        result = subprocess.run(command, capture_output=True, text=True)
        report["test_execution"] = {"command": command, "exit_code": result.returncode,
                                    "output": result.stdout+result.stderr}
        if result.returncode:
            report.setdefault("failures", []).append("Executable verification tests failed")
            report["numeric_preservation_passed"] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"output": str(args.output), "source_self_pairs": {
        pose: row["self_pair_count"] for pose, row in report["source_poses"].items()},
        "numeric_preservation_passed": report.get("numeric_preservation_passed"),
        "failures": report.get("failures", [])}, indent=2))
    if report.get("numeric_preservation_passed") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
