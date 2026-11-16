"""Independent four-pose audit of the a980 finger-surface candidate.

Original positions, UVs and skin are immutable. Explicitly declared original
normals may follow the changed surface only in the independently reconstructed
finger dorsal/side domain; protected normals stay exact. New surface samples
need an oriented parent-face correspondence. Complete collision
sets are compared in source-parent space; extra subdivision pairs are reported
separately from newly intersecting source parents. No producer/DCC/device writes.
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
PARENT = HERE.parent / "palm-wrist-surface" / "production-patch"
spec = importlib.util.spec_from_file_location("finger_patch_audit", PARENT / "verify_patch.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
v, require = p.v, p.require
VERIFIER_SHA = v.digest(Path(__file__))
REPO = v.REPO
SOURCE = PARENT / "anatomical-crease" / "right_hand_patch.glb"
SOURCE_SHA = "a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862"
DAO = REPO / "app/src/main/assets/models/dao_grip.glb"
POSES = (None, 0., .5, 1.)


def mapping(source, sb, candidate, cb, delta):
    sa, ca = v.attributes(source, sb), v.attributes(candidate, cb)
    sf, cf = v.faces(source, sb), v.faces(candidate, cb)
    n, m = len(sa["POSITION"]), len(sf)
    require(delta["source_vertex_count"] == n and delta["source_face_count"] == m,
            "Declared source counts differ")
    vm = p.integer_rows(delta["candidate_vertex_to_source"], len(ca["POSITION"]), "vertex", -1, n)
    fm = p.integer_rows(delta["candidate_face_to_source"], len(cf), "face", 0, m)
    declared = delta.get("original_normal_changed_vertex_ids", [])
    normal_changes = set(p.integer_rows(declared, len(declared), "original normal change", 0, n).tolist())
    require(len(normal_changes) == len(declared), "Original normal change declaration contains duplicates")
    protected = set(p.integer_rows(delta["protected_source_vertices"], n-len(normal_changes), "protected", 0, n))
    require(protected == set(range(n))-normal_changes, "Protected vertices must exclude only declared normal controls")
    require(set(delta.get("modified_source_vertices", [])) == normal_changes,
            "Modified source controls must be the exact declared normal-change set")
    roi = set(p.integer_rows(delta["ROI_faces"], len(delta["ROI_faces"]), "ROI", 0, m))
    require(set(sa) == set(ca), "Attribute set changed")
    retained = np.flatnonzero(vm >= 0)
    require(set(vm[retained]) == set(range(n)), "A source vertex is missing from correspondence")
    require(len(retained) == n, "An original vertex was duplicated without an authorized normal split")
    for name in sa:
        if name == "NORMAL":
            altered = set(vm[retained[np.any(ca[name][retained] != sa[name][vm[retained]], axis=1)]])
            require(altered == normal_changes, "Original NORMAL changes differ from the exact declared set")
        else:
            require(np.array_equal(ca[name][retained], sa[name][vm[retained]]),
                    "Protected attribute changed: " + name)
    for old in set(range(m)) - roi:
        children = np.flatnonzero(fm == old)
        require(len(children) == 1 and np.array_equal(vm[cf[children[0]]], sf[old]),
                "Protected face topology or oriented winding changed")
    rows = delta.get("candidate_added_vertices", [])
    require(isinstance(rows, list), "Inserted correspondence must be a list")
    added = {row["candidate_vertex_id"]: row for row in rows}
    require(len(added) == len(rows) and set(added) == set(np.flatnonzero(vm == -1)),
            "Inserted vertex correspondence incomplete or duplicated")
    ds = v.skin_regions(source, sb)["dense_weights"]
    dc = v.skin_regions(candidate, cb)["dense_weights"]
    max_uv = max_weight = 0.
    for vertex, row in added.items():
        parent = row["source_face_id"]
        require(type(parent) is int and parent in roi, "Inserted source face lies outside ROI")
        bary = np.asarray(row["barycentric"], float)
        require(bary.shape == (3,) and np.isfinite(bary).all() and (bary >= -1e-7).all()
                and abs(bary.sum() - 1) < 1e-7, "Invalid barycentric correspondence")
        require(np.array_equal(row["source_vertex_ids"], sf[parent]), "Inserted source face vertices differ")
        uv_error = float(np.max(abs(ca["TEXCOORD_0"][vertex] - bary @ sa["TEXCOORD_0"][sf[parent]])))
        require(uv_error < 2e-6, "Inserted UV does not match its source projection")
        expected = bary @ ds[sf[parent]]
        top = np.argsort(expected)[-4:]
        weight = np.zeros_like(expected)
        weight[top] = expected[top]
        weight /= weight.sum()
        weight_error = float(np.max(abs(dc[vertex] - weight)))
        require(weight_error < 2e-6, "Inserted skin does not match its source interpolation")
        max_uv, max_weight = max(max_uv, uv_error), max(max_weight, weight_error)
    require(not delta.get("normal_split_vertices", []), "Original normal splitting is not authorized")
    require(set(fm.tolist()) == set(range(m)), "A source parent face is missing")
    normal_scope = {}
    if normal_changes:
        normal_scope = anatomical_audit(source, sb, added, normal_changes)["original_normal_change_evidence"]
        op, cp = v.actual_skin(source, sb, 0.), v.actual_skin(candidate, cb, 0.)
        oc = np.cross(op[sf[:, 1]]-op[sf[:, 0]], op[sf[:, 2]]-op[sf[:, 0]])
        nc = np.cross(cp[cf[:, 1]]-cp[cf[:, 0]], cp[cf[:, 2]]-cp[cf[:, 0]])
        oc /= np.maximum(np.linalg.norm(oc, axis=1)[:, None], 1e-30)
        nc /= np.maximum(np.linalg.norm(nc, axis=1)[:, None], 1e-30)
        for old in normal_changes:
            vertex = int(np.flatnonzero(vm == old)[0])
            incident = np.flatnonzero((cf == vertex).any(axis=1))
            curved = incident[(np.linalg.norm(nc[incident]-oc[fm[incident]], axis=1) > 1e-5)
                              & np.isin(fm[incident], list(roi))]
            require(len(curved) > 0, "Original normal change lacks a changed incident surface")
            normal_scope[str(old)]["changed_incident_child_faces"] = curved.tolist()
            normal_scope[str(old)]["changed_incident_source_parents"] = np.unique(fm[curved]).tolist()
    # Each candidate corner must be a point of the mapped original triangle.
    # This validates incidence, rather than accepting arbitrary face-parent labels.
    for face, parent in zip(cf, fm):
        old_ids = set(sf[parent].tolist())
        for corner in face:
            old = vm[corner]
            if old >= 0:
                require(old in old_ids, "Retained corner does not belong to its face parent")
            else:
                row = added[int(corner)]
                support = {i for i, b in zip(row["source_vertex_ids"], row["barycentric"]) if b > 1e-7}
                require(support <= old_ids, "Inserted corner does not belong to its face parent")
    return vm, fm, added, set(range(n)), {"all_original_attributes_exact": not bool(normal_changes),
        "all_original_positions_UV_skin_exact": True, "all_protected_original_normals_exact": True,
        "declared_original_normal_changes": sorted(normal_changes), "normal_change_scope": normal_scope,
        "source_vertices": n, "source_faces": m, "inserted_vertices": len(added),
        "subdivided_source_parents": int(np.count_nonzero(np.bincount(fm, minlength=m) > 1)),
        "inserted_UV_max_component_error": max_uv, "inserted_weight_max_component_error": max_weight}


def mesh_health(document, binary):
    a, f = v.attributes(document, binary), v.faces(document, binary)
    total = sum(len(v.faces(document, binary, i)) for i in range(len(document["meshes"][0]["primitives"])))
    require(total <= 9000, "Triangle budget exceeded")
    require(v.primitive(document).get("mode", 4) == 4, "Expected triangle-list mode")
    require(len(f) and f.min() >= 0 and f.max() < len(a["POSITION"]), "Face index out of bounds")
    for name, values in a.items():
        require(len(values) == len(a["POSITION"]) and np.isfinite(values).all(), "Nonfinite or wrong-length " + name)
    require(np.max(abs(np.linalg.norm(a["NORMAL"], axis=1)-1)) < 2e-4, "Nonunit NORMAL")
    v.actual_skin(document, binary)
    cross = np.cross(a["POSITION"][f[:, 1]]-a["POSITION"][f[:, 0]],
                     a["POSITION"][f[:, 2]]-a["POSITION"][f[:, 0]])
    require((np.linalg.norm(cross, axis=1) > 1e-14).all(), "Degenerate bind triangle")
    return {"vertices": len(a["POSITION"]), "triangles": len(f), "total_triangles": total,
            "triangle_budget": 9000, "finite_skin_and_attributes": True, "unit_normals": True}


def anatomical_audit(source, sb, added, normal_changed=()):
    """Locate reference samples against actual open-pose bones, without skin labels."""
    world = v.h.sampled_worlds(source, sb, "grip", 0.)
    names = {n.get("name"): i for i, n in enumerate(source["nodes"])}
    origin = world[names["R_Hand"]][:3, 3]
    mcp = np.array([world[names["R_"+d+"1"]][:3, 3] for d in ("Index", "Mid", "Pinky")])
    forward = mcp.mean(0)-origin
    forward /= np.linalg.norm(forward)
    radial = mcp[0]-mcp[2]
    radial -= forward*(forward@radial)
    radial /= np.linalg.norm(radial)
    palm = np.cross(radial, forward)
    bones, segments = {}, []
    for digit in ("Index", "Mid", "Ring", "Pinky"):
        chain = np.array([world[names["R_"+digit+str(i)]][:3, 3] for i in (1, 2, 3)])
        # The source has no fingertip bone. This frozen 20mm extension only
        # delimits the source skin support, it does not pretend to be a bone.
        distal = chain[-1]-chain[-2]
        tip = chain[-1] + .020*distal/np.linalg.norm(distal)
        points = np.vstack((chain, tip))
        bones[digit] = {"MCP_PIP_DIP_m": chain.tolist(), "estimated_tip_m": tip.tolist()}
        for segment, (a, b) in enumerate(zip(points, points[1:])):
            segments.append((digit, segment, a, b))
    points = v.actual_skin(source, sb, 0.)
    faces = v.faces(source, sb)
    normals = v.skinned_normal_vectors(source, sb, 0.)
    owner = np.full(len(points), -1, int)
    nearest = np.full(len(points), np.inf)
    for digit_index, digit in enumerate(("Index", "Mid", "Ring", "Pinky")):
        chain = np.vstack((bones[digit]["MCP_PIP_DIP_m"], bones[digit]["estimated_tip_m"]))
        cumulative = np.r_[0., np.cumsum(np.linalg.norm(np.diff(chain, axis=0), axis=1))]
        for segment, (a, b) in enumerate(zip(chain, chain[1:])):
            axis = b-a
            length = np.linalg.norm(axis)
            unit_axis = axis/length
            dorsal = -palm-unit_axis*((-palm)@unit_axis)
            dorsal /= np.linalg.norm(dorsal)
            t = (points-a)@axis/(length*length)
            clipped = np.clip(t, 0., 1.)
            diff = points-(a+clipped[:, None]*axis)
            radius = np.linalg.norm(diff, axis=1)
            station = cumulative[segment]+clipped*length
            eligible = ((t >= -.04) & (t <= 1.04) & (radius > .002) & (radius < .0165)
                & (station > .0035) & (station < cumulative[-1]-.002)
                & (normals@dorsal > -.12) & (diff@dorsal > -.0008))
            choose = eligible & (radius < nearest)
            owner[choose], nearest[choose] = digit_index, radius[choose]
    rows = {}
    normal_proof = {}
    for vertex in normal_changed:
        require(owner[vertex] >= 0,
                "Declared original normal is outside independently reconstructed dorsal/side finger domain")
        normal_proof[str(vertex)] = {"source_vertex": int(vertex), "reference_open_m": points[vertex].tolist(),
            "source_open_normal": normals[vertex].tolist(), "capsule_owner": ("Index", "Mid", "Ring", "Pinky")[owner[vertex]],
            "nearest_eligible_axis_distance_mm": float(nearest[vertex]*1000)}
    for vertex, row in added.items():
        support = np.array([i for i, coefficient in zip(row["source_vertex_ids"], row["barycentric"]) if coefficient > 1e-7], int)
        require(len(support) == 2 and owner[support[0]] >= 0 and (owner[support] == owner[support[0]]).all(),
                "Inserted reference edge is outside independently reconstructed dorsal/side finger domain")
        q = np.asarray(row["barycentric"]) @ points[faces[row["source_face_id"]]]
        matches = []
        for digit, segment, a, b in segments:
            axis = b-a
            t = float((q-a)@axis/(axis@axis))
            closest = a+np.clip(t, 0., 1.)*axis
            diff = q-closest
            matches.append((float(np.linalg.norm(diff)), digit, segment, t, float(diff@palm)))
        distance, digit, segment, axial, palmar = min(matches)
        rows[str(vertex)] = {"reference_open_m": q.tolist(), "nearest_digit": digit,
            "nearest_segment": ("MCP-PIP", "PIP-DIP", "DIP-estimated-tip")[segment],
            "nearest_segment_axial": axial, "axis_distance_mm": distance*1000,
            "palmar_offset_mm": palmar*1000, "endpoint_capsule_owner": ("Index", "Mid", "Ring", "Pinky")[owner[support[0]]]}
    return {"basis": {"origin_m": origin.tolist(), "radial": radial.tolist(),
                       "finger_forward": forward.tolist(), "palmar": palm.tolist()},
            "actual_bones": bones, "inserted_reference_evidence": rows,
            "original_normal_change_evidence": normal_proof,
            "endpoint_domain_rule": "Actual bones, t[-.04,1.04], capsule radius(2,16.5)mm, station(3.5,total-2)mm, projected dorsal normal dot>-.12 and projected dorsal height>-.8mm; both endpoints same capsule; no skin-weight labels.",
            "qualification": "Independent actual source skin and actual open MCP/PIP/DIP audit. The 20mm estimated tip is a declared support limit; topology/sections and visual quality still need review."}


def posed_audit(source, sb, candidate, cb, vm, fm, added, protected, time):
    errors = []
    old_p, new_p = v.actual_skin(source, sb, time), v.actual_skin(candidate, cb, time)
    sf, cf = v.faces(source, sb), v.faces(candidate, cb)
    oc = np.cross(old_p[sf[:, 1]]-old_p[sf[:, 0]], old_p[sf[:, 2]]-old_p[sf[:, 0]])
    nc = np.cross(new_p[cf[:, 1]]-new_p[cf[:, 0]], new_p[cf[:, 2]]-new_p[cf[:, 0]])
    lengths = np.linalg.norm(nc, axis=1)
    degenerate = np.flatnonzero(lengths <= 1e-14).tolist()
    inverted = np.flatnonzero((oc[fm]*nc).sum(1) <= 0).tolist()
    on, nn = v.skinned_normal_vectors(source, sb, time), v.skinned_normal_vectors(candidate, cb, time)
    od = (oc[:, None]*on[sf]).sum(2)/np.linalg.norm(oc, axis=1)[:, None]
    nd = (nc[:, None]*nn[cf]).sum(2)/np.maximum(lengths[:, None], 1e-30)
    new_bad = []
    for face, corner in np.argwhere(nd < -1e-5):
        parent, old = fm[face], vm[cf[face, corner]]
        prior = np.flatnonzero(sf[parent] == old) if old >= 0 else []
        if not any(od[parent, index] < -1e-5 for index in prior):
            new_bad.append([int(face), int(corner), int(parent)])
    keep = np.flatnonzero(np.isin(vm, list(protected)))
    error = float(np.max(abs(new_p[keep]-old_p[vm[keep]]))) if len(keep) else 0.
    split_error = max((float(np.max(abs(new_p[ids]-new_p[ids[0]]))) for ids in p.seam_groups(vm, added)), default=0.)
    sw = v.position_weld(v.attributes(source, sb)["POSITION"])
    opening = 0.
    for group in np.unique(sw):
        source_ids = np.flatnonzero(sw == group)
        if len(source_ids) < 2:
            continue
        ids = np.flatnonzero(np.isin(vm, source_ids))
        before = float(np.max(abs(old_p[vm[ids]]-old_p[vm[ids[0]]])))
        after = float(np.max(abs(new_p[ids]-new_p[ids[0]])))
        opening = max(opening, after-before)
    # A new midpoint may be duplicated across two source UV charts and have
    # different parent IDs. Parent/bary keys alone do not identify that seam.
    # Weld reference bind positions too, then preserve any inherited source
    # pose separation rather than silently accepting a new skinned crack.
    bind_reference = p.reference_points(v.attributes(source, sb)["POSITION"], sf, vm, added)
    reference = p.reference_points(old_p, sf, vm, added)
    reference_groups = v.position_weld(bind_reference)
    inserted_seam_opening = 0.
    for group in np.unique(reference_groups):
        ids = np.flatnonzero(reference_groups == group)
        if len(ids) < 2 or not (vm[ids] < 0).any():
            continue
        before = float(np.max(abs(reference[ids]-reference[ids[0]])))
        after = float(np.max(abs(new_p[ids]-new_p[ids[0]])))
        inserted_seam_opening = max(inserted_seam_opening, after-before)
    for condition, message in [(not degenerate, "Posed degenerate face"), (not inverted, "Posed geometry inverted relative to source parent"),
        (not new_bad, "New posed normal opposes winding"), (error < 1e-10, "Protected posed skin changed"),
        (split_error < 1e-10, "Posed seam split opened"), (opening < 1e-10, "Original position seam opens under skinning"),
        (inserted_seam_opening < 1e-10, "Inserted source seam opens under skinning")]:
        if not condition:
            errors.append(message)
    added_ids = np.array(sorted(added), int)
    displacement = np.linalg.norm(new_p[added_ids]-reference[added_ids], axis=1) if len(added_ids) else np.array([])
    return {"passed": not errors, "errors": errors, "protected_skin_max_component_error_m": error,
        "split_position_max_error_m": split_error, "source_weld_new_pose_opening_m": opening,
        "inserted_reference_weld_new_pose_opening_m": inserted_seam_opening,
        "source_bad_normal_corners": int(np.count_nonzero(od < -1e-5)),
        "candidate_bad_normal_corners": int(np.count_nonzero(nd < -1e-5)),
        "new_bad_normal_corners": new_bad, "geometry_inverted_faces": inverted,
        "degenerate_faces": degenerate, "added_point_max_source_bary_displacement_mm": float(displacement.max()*1000) if len(displacement) else 0.}


def collision_audit(source, sb, candidate, cb, vm, fm, added, roi, time, dao):
    errors = []
    op, of = v.actual_geometry(source, sb, time)
    np_, nf = v.actual_geometry(candidate, cb, time)
    old_bind, _ = v.bind_geometry(source, sb)
    new_bind, _ = v.bind_geometry(candidate, cb)
    ow, nw = v.position_weld(old_bind), v.position_weld(new_bind)
    old_pairs = v.crossing_pairs(op, of, weld_ids=ow)
    new_pairs = v.crossing_pairs(np_, nf, weld_ids=nw)
    complete = np.r_[fm, np.arange(len(v.faces(source, sb)), len(of))]
    diff = v.mapped_pair_delta(old_pairs, new_pairs, complete, True, of, ow)
    if diff["new_source_face_pairs"]:
        errors.append("New self intersection")
    changed_faces = np.flatnonzero(np.isin(fm, list(roi)))
    vertices = np.unique(nf[changed_faces])
    primary = p.reference_points(v.actual_skin(source, sb, time), v.faces(source, sb), vm, added)
    reference = np.concatenate((primary, op[len(v.attributes(source, sb)["POSITION"]):]))
    samples, labels = v.contact_samples(np_, nf, vertices, changed_faces)
    expected, _ = v.contact_samples(reference, nf, vertices, changed_faces)
    contacts = {}
    for name, shape in dao.items():
        old_cross = v.crossing_pairs(op, of, shape["points"], shape["faces"])
        new_cross = v.crossing_pairs(np_, nf, shape["points"], shape["faces"])
        change = v.mapped_pair_delta(old_cross, new_cross, complete)
        change.update(source_surface_pair_count=len(old_cross), candidate_surface_pair_count=len(new_cross),
                      source_surface_pairs=sorted(old_cross), candidate_surface_pairs=sorted(new_cross))
        if change["new_source_face_pairs"]:
            errors.append("New Dao crossing: " + name)
        if shape["closed"] and len(changed_faces):
            tri = shape["points"][shape["faces"]]
            distance, old_distance = v.closest_surface(samples, tri)[0], v.closest_surface(expected, tri)[0]
            inside = v.contains(samples, tri) & (distance > 1e-7)
            was_inside = v.contains(expected, tri) & (old_distance > 1e-7)
            introduced = np.flatnonzero(inside & ~was_inside)
            deeper = np.flatnonzero(inside & was_inside & (distance > old_distance+1e-5))
            if len(introduced):
                errors.append("New Dao interior sample: " + name)
            if len(deeper):
                errors.append("Deeper inherited Dao sample: " + name)
            change.update(ROI_source_reference_interior_samples=int(was_inside.sum()), ROI_candidate_interior_samples=int(inside.sum()),
                ROI_source_max_depth_mm=float(old_distance[was_inside].max()*1000) if was_inside.any() else 0.,
                ROI_candidate_max_depth_mm=float(distance[inside].max()*1000) if inside.any() else 0.,
                new_interior_sample_labels=[labels[i] for i in introduced], deeper_inherited_sample_labels=[labels[i] for i in deeper])
        contacts[name] = change
    return {"passed": not errors, "errors": errors, "source_self_pair_count": len(old_pairs),
        "candidate_self_pair_count": len(new_pairs), "source_self_pairs": sorted(old_pairs),
        "candidate_self_pairs": sorted(new_pairs), "self_pair_delta": diff, "actual_dao_pair_deltas": contacts}


def verify(source, sb, candidate, cb, delta, dao=None):
    report = {"passed": False, "errors": [], "poses": {}}
    report["rig_resources"] = v.exact_rig_and_resources(source, sb, candidate, cb)
    require(len(source["skins"][0]["joints"]) == 78, "Expected original 78-joint rig")
    report["health"] = mesh_health(candidate, cb)
    report["topology"] = v.topology_health(candidate, cb)
    vm, fm, added, protected, correspondence = mapping(source, sb, candidate, cb, delta)
    report["correspondence"] = correspondence
    report["anatomical_audit"] = anatomical_audit(source, sb, added, delta.get("original_normal_changed_vertex_ids", []))
    for time in POSES:
        row = posed_audit(source, sb, candidate, cb, vm, fm, added, protected, time)
        if dao is not None:
            print("COLLISION_POSE", time, flush=True)
            row["contacts"] = collision_audit(source, sb, candidate, cb, vm, fm, added, set(delta["ROI_faces"]), time, dao)
            report["errors"].extend(str(time)+": "+error for error in row["contacts"]["errors"])
        report["errors"].extend(str(time)+": "+error for error in row["errors"])
        report["poses"][str(time)] = row
    report["passed"] = not report["errors"]
    report["limits"] = ["Finite default/open/mid/closed checks; not continuous-time or native acceptance.",
        "Mathematical inverse-transpose blended-LBS normals; not SDK TBN readback.",
        "Triangle crossings follow the repository noncoplanar edge/face convention. Parent mappings distinguish subdivision multiplicity from newly crossing parents; they do not redefine the baseline.",
        "Grip anchors and all original contact points remain exact. Added surface samples are compared against the corresponding barycentric source surface, including inherited open/mid Dao penetration."]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--candidate", type=Path, default=HERE / "right_hand_finger.glb")
    parser.add_argument("--delta", type=Path, default=HERE / "finger_delta.json")
    parser.add_argument("--output", type=Path, default=HERE / "verification.json")
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args()
    report = {"passed": False}
    try:
        require(v.digest(args.source) == SOURCE_SHA, "Pinned a980 source identity mismatch")
        delta = json.loads(args.delta.read_text())
        require(delta["source_sha256"] == SOURCE_SHA and delta["candidate_sha256"] == v.digest(args.candidate),
                "Candidate/delta input identity differs")
        report = verify(*v.h.read(args.source), *v.h.read(args.candidate), delta,
                        None if args.geometry_only else v.dao_geometry(DAO))
        require(v.digest(args.source) == SOURCE_SHA and v.digest(args.candidate) == delta["candidate_sha256"],
                "Input asset changed during verification")
        require(v.digest(Path(__file__)) == VERIFIER_SHA, "Verifier source changed during execution")
    except (ValueError, KeyError, IndexError, TypeError) as error:
        report["passed"] = False
        report["error"] = str(error)
    report.update(source_sha256=v.digest(args.source), candidate_sha256=v.digest(args.candidate),
        delta_sha256=v.digest(args.delta), actual_dao_sha256=v.digest(DAO),
        verifier_sha256=VERIFIER_SHA, tests_sha256=v.digest(HERE/"test_verify_finger.py"),
        collision_checks_run=not args.geometry_only)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"passed": report["passed"], "error": report.get("error"),
        "errors": report.get("errors"), "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
