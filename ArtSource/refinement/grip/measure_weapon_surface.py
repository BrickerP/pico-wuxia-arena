"""Offline left-hand surface audit against the actual rigid skinned dao mesh.

Run inside Blender Python. Distances are unsigned vertex-to-triangle surface
distances, not penetration depth. BVH overlaps are candidate surface crossings
and are reported separately. Discrete samples do not prove continuous clearance.
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
CHARACTER_ROOT = Path(__file__).resolve().parents[2] / "tripo-warrior"
sys.path.insert(0, str(CHARACTER_ROOT))

import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Matrix, Quaternion
from prepare_character_library import decode_animation, node_order, sampled_local
from prepare_rigged_warrior import read_glb
from refine_character_grips import accessor


def _geometry(document, binary, primitive_indices):
    mesh = next(document["meshes"][node["mesh"]] for node in document["nodes"]
                if node.get("name") == "TripoBody_Mesh")
    positions, palettes, weights, triangles = [], [], [], []
    offset = 0
    for index in primitive_indices:
        primitive = mesh["primitives"][index]
        attributes = primitive["attributes"]
        position = accessor(document, binary, attributes["POSITION"]).astype(float)
        palette = accessor(document, binary, attributes["JOINTS_0"]).astype(int)
        weight = accessor(document, binary, attributes["WEIGHTS_0"]).astype(float)
        weight /= weight.sum(axis=1)[:, None]
        faces = accessor(document, binary, primitive["indices"]).reshape(-1, 3).astype(int)
        positions.append(position)
        palettes.append(palette)
        weights.append(weight)
        triangles.append(faces + offset)
        offset += len(position)
    return tuple(np.concatenate(rows) for rows in (positions, palettes, weights, triangles))


def _skin(geometry, transforms):
    positions, palettes, weights, _ = geometry
    homogeneous = np.column_stack((positions, np.ones(len(positions))))
    blended = np.sum(transforms[palettes] * weights[:, :, None, None], axis=1)
    posed = np.einsum("vij,vj->vi", blended, homogeneous)
    return posed[:, :3]


def _tree(vertices, faces):
    return BVHTree.FromPolygons(vertices.tolist(), faces.tolist(), all_triangles=True)


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


def _triangles_cross(first, second, tolerance=1e-7):
    """Confirm noncoplanar edge/triangle crossings at 0.0001 mm tolerance.

    Coplanar BVH pairs remain explicitly unconfirmed, avoiding a volume/depth
    claim for touching or overlapping coplanar display surfaces.
    """
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
            if (start > tolerance and end > tolerance) or (start < -tolerance and end < -tolerance):
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


def measure_left_weapon(document, binary, alignment, poses=None, corrections=None):
    """Return per-pose actual-dao surface gaps and BVH crossing candidates.

    Inputs are the loaded final/candidate GLB plus its unchanged alignment JSON.
    No document, binary, armature, mesh or source file is modified.
    """
    if poses is None:
        times = sorted({1.55, 2.117, 3.4, *[frame / 30 for frame in range(47, 103)]})
        poses = [("slash", time) for time in times]
        poses += [("idle", 1.0), ("walk", .60), ("turn", .35),
                  ("hit_body", .35), ("hit_head", .35), ("hit_side", .35), ("fall", .35)]
    joints = document["skins"][0]["joints"]
    names = [document["nodes"][index]["name"] for index in joints]
    left_palette = [index for index, name in enumerate(names)
                    if name == "L_Hand" or name.startswith(
                        ("L_Thumb", "L_Index", "L_Mid", "L_Ring", "L_Pinky"))]
    body = _geometry(document, binary, alignment["body_primitive_indices"])
    mask = sum(np.sum(body[2] * (body[1] == index), axis=1) for index in left_palette) > .5
    faces = body[3][mask[body[3]].any(axis=1)]
    used = np.unique(faces)
    remap = np.full(len(body[0]), -1, dtype=int)
    remap[used] = np.arange(len(used))
    left = (body[0][used], body[1][used], body[2][used], remap[faces])
    sample_mask = mask[used]
    finger_palette = [index for index in left_palette if names[index] != "L_Hand"]
    finger_weight = sum(np.sum(left[2] * (left[1] == index), axis=1) for index in finger_palette)
    if not sample_mask.any():
        raise ValueError("left-hand weighted surface is absent")
    sources = alignment["weapon_binding"]["primitive_sources"]
    groups = {
        "whole_dao": alignment["weapon_binding"]["weapon_primitive_indices"],
        "guard_and_fittings": [row["target_primitive"] for row in sources
                               if "Guard" in row["source_node"] or
                               row["source_node"] in ("Blade collar", "Grip ferrule")],
        "blade": [row["target_primitive"] for row in sources
                  if row["source_node"].startswith("Blade") and row["source_node"] != "Blade collar"],
    }
    geometry = {name: _geometry(document, binary, indices) for name, indices in groups.items()}
    binds = accessor(document, binary, document["skins"][0]["inverseBindMatrices"])
    binds = binds.reshape(-1, 4, 4).transpose(0, 2, 1)
    parents, order = node_order(document)
    clips = {clip["name"]: decode_animation({**document, "animations": [clip]}, binary)[0]
             for clip in document["animations"]}
    rows = []
    deltas = {}
    for index, (x_degrees, z_degrees) in (corrections or {}).items():
        x, z = math.radians(x_degrees) / 2, math.radians(z_degrees) / 2
        deltas[index] = Quaternion((math.cos(x), math.sin(x), 0, 0)) @ Quaternion(
            (math.cos(z), 0, 0, math.sin(z)))
    for clip, time in poses:
        world = {}
        for index in order:
            local = sampled_local(document["nodes"][index], index, clips[clip], time)
            if index in deltas:
                location, rotation, scale = local.decompose()
                local = Matrix.LocRotScale(location, rotation @ deltas[index], scale)
            world[index] = world[parents[index]] @ local if index in parents else local
        transforms = np.array([list(world[index]) for index in joints]) @ binds
        points = _skin(left, transforms)
        hand_tree = _tree(points, left[3])
        row = {"clip": clip, "time_seconds": time, "groups": {}}
        for name, weapon in geometry.items():
            vertices = _skin(weapon, transforms)
            weapon_tree = _tree(vertices, weapon[3])
            distances = np.array([weapon_tree.find_nearest(tuple(point))[3]
                                  for point in points[sample_mask]], dtype=float)
            pairs = hand_tree.overlap(weapon_tree)
            confirmed = [pair for pair in pairs if _triangles_cross(
                points[left[3][pair[0]]], vertices[weapon[3][pair[1]]])]
            record = {
                "minimum_vertex_surface_gap_mm": float(distances.min() * 1000),
                "samples_within_3mm": int(np.count_nonzero(distances <= .003)),
                "bvh_surface_crossing_candidate_pairs": len(pairs),
                "confirmed_noncoplanar_triangle_crossing_pairs": len(confirmed),
            }
            if pairs:
                crossing_faces = np.unique([pair[0] for pair in pairs])
                crossing_vertices = np.unique(left[3][crossing_faces])
                dominant = left[1][crossing_vertices, left[2][crossing_vertices].argmax(axis=1)]
                record["crossing_vertex_dominant_joints"] = dict(Counter(names[index] for index in dominant))
                record["candidate_faces_without_any_finger_weight"] = int(np.count_nonzero(
                    (finger_weight[left[3][crossing_faces]] <= 1e-8).all(axis=1)))
            row["groups"][name] = record
        rows.append(row)
    minimum = min(rows, key=lambda row: row["groups"]["whole_dao"]["minimum_vertex_surface_gap_mm"])
    return {
        "metric": "unsigned weighted-left-hand vertex to actual skinned dao triangle distance",
        "scope": "discrete poses; BVH pairs are crossing candidates, not certified penetration depth",
        "left_surface_sample_count": int(sample_mask.sum()),
        "sampled_pose_count": len(rows),
        "minimum_gap_pose": minimum,
        "maximum_crossing_candidate_pairs": max(
            row["groups"]["whole_dao"]["bvh_surface_crossing_candidate_pairs"] for row in rows),
        "maximum_confirmed_triangle_crossing_pairs": max(
            row["groups"]["whole_dao"]["confirmed_noncoplanar_triangle_crossing_pairs"] for row in rows),
        "pose_measurements": rows,
    }


def audit_left_hand(model_path, alignment_path, poses=None):
    document, binary = read_glb(Path(model_path))
    alignment = json.loads(Path(alignment_path).read_text())
    return measure_left_weapon(document, binary, alignment, poses)


def _whole(row):
    return row["groups"]["whole_dao"]


def _admissible(candidate, baseline):
    if len(candidate["pose_measurements"]) != len(baseline["pose_measurements"]):
        return False
    return all(
        (new["clip"], new["time_seconds"]) == (old["clip"], old["time_seconds"]) and
        _whole(new)["bvh_surface_crossing_candidate_pairs"] <=
        _whole(old)["bvh_surface_crossing_candidate_pairs"] and
        _whole(new)["confirmed_noncoplanar_triangle_crossing_pairs"] <=
        _whole(old)["confirmed_noncoplanar_triangle_crossing_pairs"] and
        _whole(new)["samples_within_3mm"] <= _whole(old)["samples_within_3mm"]
        for new, old in zip(candidate["pose_measurements"], baseline["pose_measurements"])
    )


def _score(report, corrections):
    rows = [_whole(row) for row in report["pose_measurements"]]
    return (
        sum(row["confirmed_noncoplanar_triangle_crossing_pairs"] for row in rows),
        sum(row["samples_within_3mm"] for row in rows),
        -round(min(row["minimum_vertex_surface_gap_mm"] for row in rows), 5),
        sum(x * x + z * z for x, z in corrections.values()),
    )


def propose_left_offsets(document, binary, alignment):
    """Propose bounded local X/Z deltas while retaining wrist/blade transforms.

    Returns node-index -> [X degrees, Z degrees], composed as q @ Qx @ Qz.
    Only five left pinky/ring joints are eligible, each at most 18 degrees.
    Every accepted step is checked against all 65 baseline sample poses for no
    extra triangle crossings and no increase in samples within 3 mm of the dao.
    """
    baseline = measure_left_weapon(document, binary, alignment)
    if not any(_whole(row)["confirmed_noncoplanar_triangle_crossing_pairs"]
               for row in baseline["pose_measurements"]):
        return {}
    eligible_names = {"L_Pinky1", "L_Pinky2", "L_Pinky3", "L_Ring2", "L_Ring3"}
    eligible = [index for index, node in enumerate(document["nodes"])
                if node.get("name") in eligible_names]
    critical_poses = [(row["clip"], row["time_seconds"]) for row in baseline["pose_measurements"]
                      if _whole(row)["minimum_vertex_surface_gap_mm"] < 8 or
                      _whole(row)["bvh_surface_crossing_candidate_pairs"] > 0]
    critical_baseline = measure_left_weapon(document, binary, alignment, critical_poses)
    chosen = {}
    current = baseline
    current_critical = critical_baseline
    for step in (12.0, 6.0, 3.0):
        options = []
        for index in eligible:
            for axis in (0, 1):
                for direction in (-1, 1):
                    proposal = {key: list(value) for key, value in chosen.items()}
                    angles = proposal.setdefault(index, [0.0, 0.0])
                    angles[axis] += step * direction
                    if math.hypot(*angles) > 18.000001:
                        continue
                    report = measure_left_weapon(document, binary, alignment, critical_poses, proposal)
                    if _admissible(report, critical_baseline) and _score(report, proposal) < _score(current_critical, chosen):
                        options.append((_score(report, proposal), proposal, report))
        for _, proposal, critical_report in sorted(options, key=lambda row: row[0]):
            full = measure_left_weapon(document, binary, alignment, corrections=proposal)
            if _admissible(full, baseline) and _score(full, proposal) < _score(current, chosen):
                chosen, current, current_critical = proposal, full, critical_report
                break
    if _score(current, chosen)[0] >= _score(baseline, {})[0]:
        return {}
    return {index: angles for index, angles in chosen.items() if any(angles)}
