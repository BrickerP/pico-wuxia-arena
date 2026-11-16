"""Independent finite audit of a Right-v2 palm/wrist production patch.

Normal/UV corner splits are allowed; geometric seams, new winding defects and
new collision pairs are not. No model, app, device or Blender writes occur.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("patch_surface_tools", HERE.parent / "verify_surface.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
REPO = v.REPO
SOURCE = HERE.parents[1] / "right_hand_refined_v2.glb"
DAO = REPO / "app/src/main/assets/models/dao_grip.glb"
POSES = (None, 0.0, 0.5, 1.0)
require = v.require
BASELINE_DELTA_SHA = "ee0ab21e08063057d60a10017a7f0cc516c820c6e7dd56f18086e54ea7f9db99"


def anatomical_metacarpal_domain(source, sb):
    """Root's source-ray ROI, reconstructed from source skin and actual MCP bones."""
    worlds = v.h.sampled_worlds(source, sb, "grip", 0.)
    names = {node.get("name"): index for index, node in enumerate(source["nodes"])}
    bones = ("R_Index1", "R_Mid1", "R_Pinky1")
    origin = worlds[names["R_Hand"]][:3, 3]
    joints = np.asarray([worlds[names[name]][:3, 3] for name in bones])
    forward = joints.mean(axis=0) - origin
    forward /= np.linalg.norm(forward)
    radial = joints[0] - joints[2]
    radial -= forward * (forward @ radial)
    radial /= np.linalg.norm(radial)
    dorsal = np.cross(radial, forward)
    dorsal /= np.linalg.norm(dorsal)
    axes = np.asarray([radial, forward, dorsal])
    local = (v.actual_skin(source, sb, 0.) - origin) @ axes.T
    mcp = (joints - origin) @ axes.T
    line = sorted((float(row[0]), float(row[1])) for row in mcp)
    sf = v.faces(source, sb)
    weld = v.position_weld(v.attributes(source, sb)["POSITION"])
    seeds = np.unique(weld[sf[[1101, 1075]]])
    ring_faces = np.flatnonzero(np.isin(weld[sf], seeds).any(axis=1))
    ring_groups = np.unique(weld[sf[ring_faces]])
    ring = set(np.flatnonzero(np.isin(weld, ring_groups)).tolist())
    def evidence(point, in_ring):
        u, y, depth = map(float, point)
        # MCP positions are joint centres, not the lateral skin silhouette.
        # Outside that centre span hold the nearest endpoint, within the same
        # source one-ring; never extrapolate the sloping line toward fingers.
        boundary = line[0][1] if u <= line[0][0] else line[-1][1]
        for a, b in zip(line, line[1:]):
            if a[0] <= u <= b[0]:
                boundary = a[1] + (b[1] - a[1]) * (u - a[0]) / (b[0] - a[0])
                break
        margin = boundary - y
        return {"source_open_anatomical_m": [u, y, depth], "inside_vertex_one_ring": in_ring,
                "radially_interpolated_MCP_forward_m": boundary, "MCP_proximal_margin_m": margin,
                "eligible": bool(in_ring and depth < -.01 and margin is not None and margin >= .003)}
    rows = {vertex: evidence(point, vertex in ring) for vertex, point in enumerate(local)}
    return {"local": local, "evidence": rows, "point_evidence": evidence,
            "frame": {"origin_m": origin.tolist(), "axes": axes.tolist(),
                      "MCP_bones": {name: row.tolist() for name, row in zip(bones, mcp)},
                      "source_seed_faces": [1101, 1075], "vertex_one_ring_faces": ring_faces.tolist(),
                      "radial_MCP_boundary": "linear between joint centres, nearest endpoint held laterally"},
            "ring_faces": set(ring_faces.tolist())}


def anatomical_authorization(source, sb, delta):
    declared = integer_rows(delta.get("anatomical_metacarpal_vertices", []),
                            len(delta.get("anatomical_metacarpal_vertices", [])),
                            "anatomical MCP", 0, len(v.attributes(source, sb)["POSITION"]))
    baseline_path = HERE / "patch_delta.json"
    require(v.digest(baseline_path) == BASELINE_DELTA_SHA, "Root wrist baseline domain changed")
    baseline = set(json.loads(baseline_path.read_text())["modified_source_vertices"])
    domain = anatomical_metacarpal_domain(source, sb)
    for vertex in declared:
        require(domain["evidence"][int(vertex)]["eligible"],
                "Declared MCP exception is outside the actual source dorsal/MCP domain: " + str(vertex))
    editable = set(delta["modified_source_vertices"])
    require(editable - baseline <= set(declared.tolist()),
            "New editable vertex lacks independently proven anatomical authorization")
    return set(declared.tolist()), domain, {"Root_wrist_delta_sha256": BASELINE_DELTA_SHA,
            "frame": domain["frame"], "declared_vertex_evidence": {str(i): domain["evidence"][int(i)] for i in declared}}


def require_metacarpal_palette(source, palettes, weights):
    names = [source["nodes"][i]["name"] for i in source["skins"][0]["joints"]]
    allowed = {i for i, name in enumerate(names) if name in
               {"R_Hand", "R_Thumb1", "R_Index1", "R_Mid1", "R_Ring1", "R_Pinky1"}}
    require(set(np.asarray(palettes)[np.asarray(weights) > 1e-8].tolist()) <= allowed,
            "Anatomical patch weight uses a non-palm/MCP bone")


def integer_rows(values, count, label, minimum=0, maximum=None):
    require(isinstance(values, list) and len(values) == count and
            all(type(value) is int for value in values), "Invalid " + label + " mapping size/type")
    result = np.asarray(values, dtype=int)
    require((result >= minimum).all() and (maximum is None or (result < maximum).all()),
            "Invalid " + label + " mapping bounds")
    return result


def mapping(source, sb, candidate, cb, delta):
    sa, ca = v.attributes(source, sb), v.attributes(candidate, cb)
    sf, cf = v.faces(source, sb), v.faces(candidate, cb)
    n, m = len(sa["POSITION"]), len(sf)
    require(delta["source_vertex_count"] == n and delta["source_face_count"] == m,
            "Declared source counts differ")
    vm = integer_rows(delta["candidate_vertex_to_source"], len(ca["POSITION"]), "vertex", -1, n)
    fm = integer_rows(delta["candidate_face_to_source"], len(cf), "face", 0, m)
    protected = set(integer_rows(delta["protected_source_vertices"], len(delta["protected_source_vertices"]),
                                 "protected", 0, n).tolist())
    editable = set(integer_rows(delta["modified_source_vertices"], len(delta["modified_source_vertices"]),
                                "editable", 0, n).tolist())
    roi = set(integer_rows(delta["ROI_faces"], len(delta["ROI_faces"]), "ROI", 0, m).tolist())
    require(not protected & editable and protected | editable == set(range(n)),
            "Protected/editable domains must partition the complete source")
    regions = v.skin_regions(source, sb)
    digit_core = np.flatnonzero(sum(regions["digit_weights"].values()) > .5)
    exceptions, anatomical, proof = anatomical_authorization(source, sb, delta)
    require(set(digit_core) - exceptions <= protected,
            "Every digit-dominated source vertex must remain protected")
    require(editable <= set(sf[list(roi)].ravel().tolist()) if roi else not editable,
            "Editable source vertex lies outside declared ROI faces")
    require(set(sa) == set(ca), "Attribute set changed")
    for old in range(n):
        require(np.count_nonzero(vm == old) >= 1, "Source vertex missing from correspondence")
    changed = {}
    retained = np.flatnonzero(vm >= 0)
    for name in sa:
        bad = retained[np.any(ca[name][retained] != sa[name][vm[retained]], axis=1)]
        altered = set(vm[bad].tolist())
        require(altered <= editable, "Protected attribute changed: " + name)
        if name in ("JOINTS_0", "WEIGHTS_0"):
            require(altered <= exceptions, "Weight/JOINTS change outside proven MCP skin")
            for vertex in bad:
                require_metacarpal_palette(source, ca["JOINTS_0"][vertex], ca["WEIGHTS_0"][vertex])
        changed[name] = sorted(altered)
    true_digits = set(digit_core) - exceptions
    digit_faces = set(np.flatnonzero(np.isin(sf, list(true_digits)).all(axis=1)).tolist())
    for old in (set(range(m)) - roi) | digit_faces:
        children = np.flatnonzero(fm == old)
        require(len(children) == 1 and np.array_equal(vm[cf[children[0]]], sf[old]),
                "Protected face topology or oriented winding changed")
    rows = delta.get("candidate_added_vertices", [])
    require(isinstance(rows, list), "Inserted correspondence must be a list")
    added = {row["candidate_vertex_id"]: row for row in rows}
    require(len(added) == len(rows) and set(added) == set(np.flatnonzero(vm == -1)),
            "Inserted vertex correspondence incomplete or duplicated")
    dense_source, dense_candidate = v.skin_regions(source, sb)["dense_weights"], v.skin_regions(candidate, cb)["dense_weights"]
    for vertex, row in added.items():
        parent = row["source_face_id"]
        require(type(parent) is int and parent in roi, "Inserted source face lies outside ROI")
        bary = np.asarray(row["barycentric"], float)
        require(bary.shape == (3,) and np.isfinite(bary).all() and (bary >= -1e-7).all()
                and abs(bary.sum() - 1) < 1e-7, "Invalid barycentric correspondence")
        require(np.array_equal(row["source_vertex_ids"], sf[parent]), "Inserted source face vertices differ")
        require(np.max(abs(ca["TEXCOORD_0"][vertex] - bary @ sa["TEXCOORD_0"][sf[parent]])) < 2e-6,
                "Inserted UV does not match its source projection")
        weight = bary @ dense_source[sf[parent]]
        top = np.argsort(weight)[-4:]
        expected = np.zeros_like(weight)
        expected[top] = weight[top]
        expected /= expected.sum()
        if np.max(abs(dense_candidate[vertex] - expected)) >= 2e-6:
            point = bary @ anatomical["local"][sf[parent]]
            allowed_point = anatomical["point_evidence"](point, parent in anatomical["ring_faces"])
            require(allowed_point["eligible"], "Reweighted inserted point is outside the source MCP domain")
            require_metacarpal_palette(source, ca["JOINTS_0"][vertex], ca["WEIGHTS_0"][vertex])
    splits = integer_rows(delta.get("normal_split_vertices", []), len(delta.get("normal_split_vertices", [])),
                          "normal split", 0, len(vm))
    for vertex in splits:
        peers = next((group for group in seam_groups(vm, added) if vertex in group), [])
        require(len(peers) > 1, "Normal split must map to a duplicated source point")
        for name in ("POSITION", "JOINTS_0", "WEIGHTS_0"):
            require(all(np.array_equal(ca[name][vertex], ca[name][peer]) for peer in peers),
                    "Normal split changed its geometric/skin seam: " + name)
    return vm, fm, added, protected, changed


def seam_groups(vertex_map, inserted):
    groups = {}
    for vertex, source in enumerate(vertex_map):
        if source >= 0:
            key = ("vertex", int(source))
        else:
            row = inserted[vertex]
            key = ("bary", row["source_face_id"], tuple(row["source_vertex_ids"]), tuple(row["barycentric"]))
        groups.setdefault(key, []).append(vertex)
    return [np.asarray(group, int) for group in groups.values() if len(group) > 1]


def reference_points(source_points, source_faces, vertex_map, inserted):
    result = np.empty((len(vertex_map), 3), float)
    keep = vertex_map >= 0
    result[keep] = source_points[vertex_map[keep]]
    for vertex, row in inserted.items():
        result[vertex] = np.asarray(row["barycentric"]) @ source_points[source_faces[row["source_face_id"]]]
    return result


def posed_health(source, sb, candidate, cb, vm, fm, added, protected, time):
    old_p, new_p = v.actual_skin(source, sb, time), v.actual_skin(candidate, cb, time)
    old_f, new_f = v.faces(source, sb), v.faces(candidate, cb)
    old_cross = np.cross(old_p[old_f[:, 1]] - old_p[old_f[:, 0]], old_p[old_f[:, 2]] - old_p[old_f[:, 0]])
    new_cross = np.cross(new_p[new_f[:, 1]] - new_p[new_f[:, 0]], new_p[new_f[:, 2]] - new_p[new_f[:, 0]])
    lengths = np.linalg.norm(new_cross, axis=1)
    require((lengths > 1e-14).all(), "Posed degenerate face at " + str(time))
    inverted = np.flatnonzero((old_cross[fm] * new_cross).sum(axis=1) <= 0)
    require(not len(inverted), "Posed geometry inverted relative to source at " + str(time) + ": " + str(inverted[:12].tolist()))
    old_normals, new_normals = v.skinned_normal_vectors(source, sb, time), v.skinned_normal_vectors(candidate, cb, time)
    old_dot = (old_cross[:, None] * old_normals[old_f]).sum(axis=2) / np.linalg.norm(old_cross, axis=1)[:, None]
    new_dot = (new_cross[:, None] * new_normals[new_f]).sum(axis=2) / lengths[:, None]
    new_bad = []
    for face, corner in np.argwhere(new_dot < -1e-5):
        parent, old_vertex = fm[face], vm[new_f[face, corner]]
        original_corner = np.flatnonzero(old_f[parent] == old_vertex) if old_vertex >= 0 else []
        if not any(old_dot[parent, index] < -1e-5 for index in original_corner):
            new_bad.append([int(face), int(corner), int(parent)])
    require(not new_bad, "New posed normal opposes winding at " + str(time) + ": " + str(new_bad[:12]))
    keep = np.flatnonzero(np.isin(vm, list(protected)))
    error = float(np.max(abs(new_p[keep] - old_p[vm[keep]]))) if len(keep) else 0.0
    require(error < 1e-10, "Protected posed skin changed")
    # Per-corner splits must remain one geometric point after actual LBS too.
    split_drift = 0.0
    for ids in seam_groups(vm, added):
        split_drift = max(split_drift, float(np.max(abs(new_p[ids] - new_p[ids[0]]))))
    require(split_drift < 1e-10, "Posed seam split opened")
    source_weld = v.position_weld(v.attributes(source, sb)["POSITION"])
    new_opening = 0.0
    for group in np.unique(source_weld):
        source_ids = np.flatnonzero(source_weld == group)
        if len(source_ids) < 2:
            continue
        ids = np.flatnonzero(np.isin(vm, source_ids))
        reference = old_p[vm[ids]]
        before = float(np.max(abs(reference - reference[0])))
        after = float(np.max(abs(new_p[ids] - new_p[ids[0]])))
        new_opening = max(new_opening, after - before)
    require(new_opening < 1e-10, "Original UV/normal position seam opens under skinning")
    return {"protected_skin_max_component_error_m": error, "split_position_max_error_m": split_drift,
            "source_weld_new_pose_opening_m": new_opening,
            "source_bad_normal_corners": int(np.count_nonzero(old_dot < -1e-5)),
            "candidate_bad_normal_corners": int(np.count_nonzero(new_dot < -1e-5)),
            "new_bad_normal_corners": new_bad, "geometry_inverted_faces": inverted.tolist()}


def collision_health(source, sb, candidate, cb, vm, fm, added, roi, time, dao):
    old_p, old_f = v.actual_geometry(source, sb, time)
    new_p, new_f = v.actual_geometry(candidate, cb, time)
    old_bind, _ = v.bind_geometry(source, sb)
    new_bind, _ = v.bind_geometry(candidate, cb)
    old_weld, new_weld = v.position_weld(old_bind), v.position_weld(new_bind)
    old_pairs = v.crossing_pairs(old_p, old_f, weld_ids=old_weld)
    new_pairs = v.crossing_pairs(new_p, new_f, weld_ids=new_weld)
    complete_map = np.r_[fm, np.arange(len(v.faces(source, sb)), len(old_f))]
    delta = v.mapped_pair_delta(old_pairs, new_pairs, complete_map, True, old_f, old_weld)
    require(not delta["new_source_face_pairs"], "New self intersection at " + str(time))
    contacts = {}
    changed_faces = np.flatnonzero(np.isin(fm, list(roi)))
    changed_vertices = np.unique(new_f[changed_faces]) if len(changed_faces) else np.array([], int)
    primary_reference = reference_points(v.actual_skin(source, sb, time), v.faces(source, sb), vm, added)
    reference = np.concatenate((primary_reference, old_p[len(v.attributes(source, sb)["POSITION"]):]))
    if len(changed_faces):
        sample, _ = v.contact_samples(new_p, new_f, changed_vertices, changed_faces)
        expected, _ = v.contact_samples(reference, new_f, changed_vertices, changed_faces)
    # This is a whole-surface pair test, including closure; the unchanged fingers
    # must retain the same inherited pairs, not merely the same total count.
    for name, shape in dao.items():
        old_cross = v.crossing_pairs(old_p, old_f, shape["points"], shape["faces"])
        new_cross = v.crossing_pairs(new_p, new_f, shape["points"], shape["faces"])
        change = v.mapped_pair_delta(old_cross, new_cross, complete_map)
        require(not change["new_source_face_pairs"], "New Dao crossing at " + str(time) + ": " + name)
        if shape["closed"] and len(changed_faces):
            triangles = shape["points"][shape["faces"]]
            distance = v.closest_surface(sample, triangles)[0]
            old_distance = v.closest_surface(expected, triangles)[0]
            inside = v.contains(sample, triangles) & (distance > 1e-7)
            old_inside = v.contains(expected, triangles) & (old_distance > 1e-7)
            require(not np.any(inside & ~old_inside), "New Dao interior sample at " + str(time) + ": " + name)
            require(not np.any(inside & old_inside & (distance > old_distance + 1e-5)),
                    "Deeper inherited Dao sample at " + str(time) + ": " + name)
            change["ROI_interior_samples"] = int(np.count_nonzero(inside))
            change["ROI_max_sample_depth_mm"] = float(distance[inside].max() * 1000) if inside.any() else 0.0
        contacts[name] = change
    return {"source_self_pair_count": len(old_pairs), "candidate_self_pair_count": len(new_pairs),
            "self_pair_delta": delta, "actual_dao_pair_deltas": contacts}


def verify(source, sb, candidate, cb, delta, dao=None):
    report = {"rig_resources": v.exact_rig_and_resources(source, sb, candidate, cb),
              "health": v.mesh_health(candidate, cb), "topology": v.topology_health(candidate, cb), "poses": {}}
    require(len(source["skins"][0]["joints"]) == 78, "Expected the original 78-joint rig")
    vm, fm, added, protected, changed = mapping(source, sb, candidate, cb, delta)
    report["changed_source_attributes"] = changed
    report["anatomical_authorization"] = anatomical_authorization(source, sb, delta)[2]
    for time in POSES:
        row = posed_health(source, sb, candidate, cb, vm, fm, added, protected, time)
        if dao is not None:
            row["contacts"] = collision_health(source, sb, candidate, cb, vm, fm, added,
                                                set(delta["ROI_faces"]), time, dao)
        report["poses"][str(time)] = row
    report["passed"] = True
    report["limits"] = ["Finite default/open/mid/closed checks, not continuous-time or native acceptance.",
                         "Normals use the mathematical inverse-transpose blended-LBS transform, not SDK TBN readback.",
                         "The accepted wrist domain is fixed to the immutable 3000 packet. Any extension needs independently reconstructed source MCP/dorsal/one-ring evidence. Digit-dominated vertices remain protected except those proven metacarpal exceptions; joint weights alone are not anatomy."]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--candidate", type=Path, default=HERE / "right_hand_patch.glb")
    parser.add_argument("--delta", type=Path, default=HERE / "patch_delta.json")
    parser.add_argument("--output", type=Path, default=HERE / "verification.json")
    args = parser.parse_args()
    require(v.digest(args.source) == v.SOURCE_SHA, "Pinned Right v2 source identity mismatch")
    delta = json.loads(args.delta.read_text())
    delta_sha = v.digest(args.delta)
    require(delta["source_sha256"] == v.SOURCE_SHA and delta["candidate_sha256"] == v.digest(args.candidate),
            "Patch input identity differs")
    try:
        report = verify(*v.h.read(args.source), *v.h.read(args.candidate), delta, v.dao_geometry(DAO))
        require(v.digest(args.source) == v.SOURCE_SHA and v.digest(args.candidate) == delta["candidate_sha256"]
                and v.digest(DAO) == v.DAO_SHA and v.digest(args.delta) == delta_sha,
                "Input asset or correspondence changed during verification")
    except (ValueError, KeyError, IndexError) as error:
        report = {"passed": False, "error": str(error)}
    report.update(source_sha256=v.SOURCE_SHA, candidate_sha256=v.digest(args.candidate),
                  delta_sha256=delta_sha, actual_dao_sha256=v.DAO_SHA,
                  verifier_sha256=v.digest(Path(__file__)), tests_sha256=v.digest(HERE / "test_verify_patch.py"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "error": report.get("error"), "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
