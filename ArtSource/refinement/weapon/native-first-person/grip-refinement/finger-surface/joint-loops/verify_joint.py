"""Independent a980 joint-loop mapping, anatomy and four-pose surface audit.

The declared non-protected dorsal/side controls may move and change normal or
local interpolated skin weights. Protected source controls and original UVs are
exact. New cutting samples use parent barycentric UV semantics, without assuming
midpoints or treating skin-weight labels as anatomical ownership.
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
spec = importlib.util.spec_from_file_location("frozen_finger_audit", HERE.parent / "verify_finger.py")
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
v, p, require = f.v, f.p, f.require
SOURCE, SOURCE_SHA, DAO, POSES = f.SOURCE, f.SOURCE_SHA, f.DAO, f.POSES
VERIFIER_SHA = v.digest(Path(__file__))


def unit(array):
    value = np.asarray(array, float)
    return value/np.maximum(np.linalg.norm(value, axis=-1, keepdims=True), 1e-30)


def integer_set(delta, key, maximum):
    rows = delta.get(key, [])
    values = p.integer_rows(rows, len(rows), key, 0, maximum).tolist()
    require(len(values) == len(set(values)), "Duplicate " + key)
    return set(values)


def anatomy(source, sb):
    """Actual open-pose MCP/PIP/DIP and skin normals; no palette classification."""
    world = v.h.sampled_worlds(source, sb, "grip", 0.)
    names = {node.get("name"): i for i, node in enumerate(source["nodes"])}
    origin = world[names["R_Hand"]][:3, 3]
    mcp = np.array([world[names["R_"+digit+"1"]][:3, 3] for digit in ("Index", "Mid", "Pinky")])
    forward = unit(mcp.mean(0)-origin)
    radial = mcp[0]-mcp[2]
    radial = unit(radial-forward*(forward@radial))
    palm = unit(np.cross(radial, forward))
    frames, segments, profile_frames = {}, [], {}
    for digit in ("Index", "Mid", "Ring", "Pinky"):
        bones = np.array([world[names["R_"+digit+str(i)]][:3, 3] for i in (1, 2, 3)])
        chain = np.vstack((bones, bones[2]+.020*unit(bones[2]-bones[1])))
        lengths = np.linalg.norm(np.diff(chain, axis=0), axis=1)
        cumulative = np.r_[0., np.cumsum(lengths)]
        frames[digit] = {"MCP_PIP_DIP_m": bones.tolist(), "estimated_tip_m": chain[-1].tolist(),
                         "joint_stations_m": cumulative.tolist()}
        profile_axis = unit(bones[2]-bones[0])
        profile_dorsal = unit(-palm-profile_axis*((-palm)@profile_axis))
        profile_frames[digit] = {"origin": bones[0], "chain": chain,
            "axis": profile_axis, "dorsal": profile_dorsal,
            "radial": unit(np.cross(profile_axis, profile_dorsal)),
            "stations": (chain-bones[0])@profile_axis}
        for index, (a, b) in enumerate(zip(chain, chain[1:])):
            axis = unit(b-a)
            segments.append({"digit": digit, "segment": index, "start": a, "end": b,
                "axis": axis, "length": lengths[index], "station": cumulative[index],
                "total_length": cumulative[-1], "dorsal": unit(-palm-axis*((-palm)@axis))})

    def classify(points, normals):
        points, normals = np.asarray(points), unit(normals)
        nearest = np.full(len(points), np.inf)
        rows = [None]*len(points)
        for segment in segments:
            length, axis = segment["length"], segment["axis"]
            t = (points-segment["start"])@axis/length
            clipped = np.clip(t, 0., 1.)
            center = segment["start"]+clipped[:, None]*length*axis
            offset = points-center
            radius = np.linalg.norm(offset, axis=1)
            height = offset@segment["dorsal"]
            facing = normals@segment["dorsal"]
            station = segment["station"]+clipped*length
            eligible = ((t >= -.04) & (t <= 1.04) & (radius > .002) & (radius < .0165)
                & (station > .0035) & (station < segment["total_length"]-.002)
                & (height > -.0008) & (facing > -.12))
            for i in np.flatnonzero(eligible & (radius < nearest)):
                nearest[i] = radius[i]
                rows[i] = {"digit": segment["digit"], "segment": int(segment["segment"]),
                    "open_m": points[i].tolist(), "radius_mm": float(radius[i]*1000),
                    "station_mm": float(station[i]*1000), "dorsal_height_mm": float(height[i]*1000),
                    "dorsal_normal_dot": float(facing[i])}
        return rows

    opened = v.actual_skin(source, sb, 0.)
    normals = v.skinned_normal_vectors(source, sb, 0.)
    def profile_coordinates(digit, points):
        frame = profile_frames[digit]
        s = (np.asarray(points)-frame["origin"])@frame["axis"]
        center = np.column_stack([np.interp(s, frame["stations"], frame["chain"][:, k]) for k in range(3)])
        radial = np.asarray(points)-center
        return s, np.arctan2(radial@frame["radial"], radial@frame["dorsal"])

    return {"classify": classify, "profile_coordinates": profile_coordinates,
        "source_points": opened, "source_normals": normals,
        "source_evidence": classify(opened, normals), "actual_bones": frames,
        "basis": {"origin_m": origin.tolist(), "radial": radial.tolist(),
                  "finger_forward": forward.tolist(), "palmar": palm.tolist()},
        "domain_rule": "Actual MCP/PIP/DIP, declared20mm distal extension; t[-.04,1.04], radius(2,16.5)mm, station(3.5,total-2)mm, dorsal height>-.8mm, dorsal normal dot>-.12. Classification uses source anatomy, never dominant bone weights."}


def edit_strength_audit(added, vm, delta, domain):
    source = np.asarray(delta["edit_strength_source"], float)
    candidate = np.asarray(delta["edit_strength_candidate"], float)
    require(source.shape == (len(domain["source_points"]),) and candidate.shape == (len(vm),)
            and np.isfinite(source).all() and np.isfinite(candidate).all()
            and (source >= 0).all() and (source <= 1).all()
            and (candidate >= 0).all() and (candidate <= 1).all(), "Invalid source/candidate edit-strength fields")
    outside = np.array([row is None for row in domain["source_evidence"]])
    require((source[outside] == 0).all(), "Edit strength authorizes an original protected anatomical control")
    retained = np.flatnonzero(vm >= 0)
    require(np.max(abs(candidate[retained]-source[vm[retained]])) < 2e-7,
            "Original/split edit strength differs from its source control")
    caps = []
    for vertex, row in added.items():
        cap = float(np.asarray(row["barycentric"])@source[row["source_vertex_ids"]])
        require(candidate[vertex] <= cap+2e-7,
                "Inserted edit strength exceeds its parent barycentric source-control cap")
        caps.append((int(vertex), cap, float(candidate[vertex])))
    return candidate, {"rule": "Candidate edit strength cannot exceed parent-face barycentric interpolation of the original source-control strength; original/split controls preserve the source strength. Original-control Gaussian weight blend=.75*capped strength; new cutting samples interpolate the updated parent controls.",
        "source_nonzero_controls": int(np.count_nonzero(source)),
        "candidate_nonzero_controls": int(np.count_nonzero(candidate)),
        "maximum_inserted_cap_excess": max((actual-cap for _, cap, actual in caps), default=0.),
        "inserted_cap_evidence": [{"candidate_vertex": i, "source_bary_cap": cap, "actual_strength": actual} for i, cap, actual in caps]}


def weighted_skin(source, sb, candidate, cb, added, vm, weight_changes, delta, domain, edit_strength):
    """Exact bary interpolation by default; explicitly projected local edits allowed."""
    sf = v.faces(source, sb)
    ds = v.skin_regions(source, sb)["dense_weights"]
    dc = v.skin_regions(candidate, cb)["dense_weights"]
    candidate_changes = integer_set(delta, "candidate_weight_changed_vertex_ids", len(vm))
    changed_original_corners = set(np.flatnonzero(np.isin(vm, list(weight_changes))).tolist())
    require((candidate_changes-set(added)) <= changed_original_corners,
            "Candidate weight declaration names an undeclared original skin control")
    inserted_changes = candidate_changes & set(added)
    projections = delta.get("weight_change_projections", [])
    require(isinstance(projections, list), "Weight projection evidence must be a list")
    proof = {row["candidate_vertex_id"]: row for row in projections}
    expected_ids = inserted_changes | changed_original_corners
    extra = set(proof)-expected_ids
    require(expected_ids <= set(proof) and len(proof) == len(projections)
            and extra <= set(added) and all(proof[i].get("kind") == "updated_control_barycentric" for i in extra),
            "Changed local skin requires exact per-candidate weight projection evidence")
    actual_inserted, maximum = set(), 0.
    for vertex, row in added.items():
        parent, bary = row["source_face_id"], np.asarray(row["barycentric"])
        expected = bary@ds[sf[parent]]
        top = np.argsort(expected)[-4:]
        normalized = np.zeros_like(expected)
        normalized[top] = expected[top]
        normalized /= normalized.sum()
        error = float(np.max(abs(dc[vertex]-normalized)))
        maximum = max(maximum, error)
        if error >= 2e-6:
            actual_inserted.add(vertex)
    require(actual_inserted == inserted_changes, "Inserted skin change differs from declared local-weight set")
    palette_names = [source["nodes"][i]["name"] for i in source["skins"][0]["joints"]]
    anchor_report, updated_control_report = {}, {}
    for vertex, row in proof.items():
        require(type(vertex) is int and 0 <= vertex < len(vm), "Invalid weight projection vertex")
        if row.get("kind") == "updated_control_barycentric":
            require(vertex in added, "Updated-control barycentric skin is only for a new cutting sample")
            ref = added[vertex]
            ids = np.asarray(row["control_source_vertex_ids"], int)
            coefficients = np.asarray(row["control_coefficients"], float)
            require(ids.ndim == 1 and len(ids) > 0 and len(set(ids.tolist())) == len(ids)
                    and coefficients.shape == (len(ids),) and np.isfinite(coefficients).all()
                    and (coefficients >= 0).all() and abs(coefficients.sum()-1) < 1e-7,
                    "Invalid updated-control barycentric weight projection")
            weights = dict(zip(ids.tolist(), coefficients.tolist()))
            require(set(weights) <= set(ref["source_vertex_ids"])
                    and all(abs(weights.get(old, 0.)-bary) < 2e-7
                            for old, bary in zip(ref["source_vertex_ids"], ref["barycentric"])),
                    "Updated-control weight projection differs from its original parent barycentric correspondence")
            controls = np.array([np.flatnonzero(vm == old)[0] for old in ids], int)
            expected = coefficients@dc[controls]
            top = np.argsort(expected)[-4:]
            normalized = np.zeros_like(expected)
            normalized[top] = expected[top]
            normalized /= normalized.sum()
            require(np.max(abs(dc[vertex]-normalized)) < 2e-6,
                    "Inserted skin differs from barycentric interpolation of the updated original controls")
            updated_control_report[str(vertex)] = {"source_control_ids": ids.tolist(),
                "candidate_control_ids": controls.tolist(), "coefficients": coefficients.tolist()}
            continue
        if "source_vertex_ids" in row:
            anchors = p.integer_rows(row["source_vertex_ids"], len(row["source_vertex_ids"]), "weight anchors", 0, len(ds))
            coefficients = np.asarray(row["coefficients"], float)
            require(len(anchors) > 0 and len(set(anchors.tolist())) == len(anchors) and coefficients.shape == (len(anchors),)
                    and np.isfinite(coefficients).all() and (coefficients >= 0).all()
                    and abs(coefficients.sum()-1) < 1e-7, "Invalid local anchor interpolation coefficients")
            if vm[vertex] >= 0:
                base = {int(vm[vertex]): 1.}
                evidence = domain["source_evidence"][vm[vertex]]
                target = domain["source_points"][vm[vertex]]
            else:
                ref = added[vertex]
                base = {int(i): float(c) for i, c in zip(ref["source_vertex_ids"], ref["barycentric"]) if c > 1e-7}
                target = np.asarray(ref["barycentric"])@domain["source_points"][sf[ref["source_face_id"]]]
                ref_n = np.asarray(ref["barycentric"])@domain["source_normals"][sf[ref["source_face_id"]]]
                evidence = domain["classify"](target[None, :], ref_n[None, :])[0]
            require(evidence is not None, "Weight target is outside true dorsal/side finger anatomy")
            digit = evidence["digit"]
            require(row["digit"] == digit, "Weight target digit differs from actual bone-capsule anatomy")
            for anchor in anchors:
                require(domain["source_evidence"][anchor] is not None and domain["source_evidence"][anchor]["digit"] == digit,
                        "Weight source anchor is outside the same true finger domain")
            s, theta = domain["profile_coordinates"](digit, domain["source_points"])
            target_s, target_theta = domain["profile_coordinates"](digit, target[None, :])
            ds_axis = s-target_s[0]
            angle = (theta-target_theta[0]+np.pi)%(2*np.pi)-np.pi
            same = np.array([r is not None and r["digit"] == digit for r in domain["source_evidence"]])
            pool = np.flatnonzero(same & (abs(ds_axis) <= .020+1e-10) & (abs(angle) <= 1.2+1e-10))
            metric = (ds_axis/.010)**2+(angle/.7)**2
            expected_ids = pool[np.argsort(metric[pool])[:6]]
            require(set(anchors.tolist()) == set(expected_ids.tolist()),
                    "Weight source anchors are not the nearest six in the fixed20mm/1.2rad neighborhood")
            expected_coefficients = np.exp(-.5*metric[anchors])
            expected_coefficients /= expected_coefficients.sum()
            require(np.max(abs(coefficients-expected_coefficients)) < 2e-6,
                    "Weight anchor coefficients differ from fixed local Gaussian metric")
            require(abs(float(row["axial_halfwidth_m"])-.020) < 1e-10, "Weight axial halfwidth differs from fixed20mm policy")
            if "target_station_m" in row:
                require(abs(row["target_station_m"]-target_s[0]) < 2e-7, "Weight target station evidence differs")
            if "anchor_stations_m" in row:
                require(np.max(abs(np.asarray(row["anchor_stations_m"])-s[anchors])) < 2e-7, "Weight anchor station evidence differs")
            recorded_base = {int(i): float(c) for i, c in zip(row["base_source_vertex_ids"], row["base_coefficients"]) if c > 1e-7}
            require(set(recorded_base) == set(base) and all(abs(recorded_base[i]-base[i]) < 2e-7 for i in base),
                    "Weight blend base differs from the immutable original source correspondence")
            keep = {"R_Hand", *["R_"+digit+str(i) for i in (1, 2, 3)]}
            require(set(row["keep_joint_names"]) == keep, "Foreign-palette filtering differs from the actual target finger")
            target_weight = coefficients@ds[anchors]
            target_weight[[name not in keep for name in palette_names]] = 0.
            require(target_weight.sum() > 1e-12, "Local anchor interpolation has no same-finger mass")
            target_weight /= target_weight.sum()
            blend = float(row["blend_factor"])
            require(np.isfinite(blend) and 0 <= blend <= .75+1e-10, "Local weight feather is outside authorized0-.75 range")
            require(abs(blend-.75*edit_strength[vertex]) < 2e-7,
                    "Local weight blend does not match capped anatomical edit strength")
            base_weight = sum(ds[i]*c for i, c in base.items())
            expected = (1-blend)*base_weight+blend*target_weight
            top = np.argsort(expected)[-4:]
            normalized = np.zeros_like(expected)
            normalized[top] = expected[top]
            normalized /= normalized.sum()
            require(np.max(abs(dc[vertex]-normalized)) < 2e-6, "Local anchor/filter/blend projection differs from actual skin")
            anchor_report[str(vertex)] = {"digit": digit, "target_station_m": float(target_s[0]),
                "source_anchor_ids": anchors.tolist(), "source_anchor_stations_m": s[anchors].tolist(),
                "source_anchor_angle_delta_rad": angle[anchors].tolist(), "coefficients": coefficients.tolist(),
                "blend_factor": blend, "fixed_axial_halfwidth_m": .020, "fixed_angular_halfwidth_rad": 1.2,
                "keep_joint_names": sorted(keep)}
            continue
        face = row["source_face_id"]
        bary = np.asarray(row["barycentric"], float)
        require(type(face) is int and 0 <= face < len(sf) and bary.shape == (3,)
                and np.isfinite(bary).all() and (bary >= 0).all() and abs(bary.sum()-1) < 1e-7,
                "Invalid local weight projection")
        support = {int(vm[vertex])} if vm[vertex] >= 0 else set(sf[added[vertex]["source_face_id"]])
        require(bool(support & set(sf[face])), "Weight projection is outside the original local one-ring")
        expected = bary@ds[sf[face]]
        top = np.argsort(expected)[-4:]
        normalized = np.zeros_like(expected)
        normalized[top] = expected[top]
        normalized /= normalized.sum()
        require(np.max(abs(dc[vertex]-normalized)) < 2e-6, "Local weight projection differs from actual skin")
    return inserted_changes, {"original_weight_changed_source_ids": sorted(weight_changes),
        "inserted_weight_changed_candidate_ids": sorted(inserted_changes),
        "local_weight_projection_count": len(proof), "local_anatomical_anchor_projection": anchor_report,
        "updated_original_control_barycentric_projection": updated_control_report,
        "maximum_inserted_source_bary_weight_difference": maximum}


def mapping(source, sb, candidate, cb, delta):
    sa, ca = v.attributes(source, sb), v.attributes(candidate, cb)
    sf, cf = v.faces(source, sb), v.faces(candidate, cb)
    n, m = len(sa["POSITION"]), len(sf)
    require(delta["source_vertex_count"] == n and delta["source_face_count"] == m, "Source counts differ")
    vm = p.integer_rows(delta["candidate_vertex_to_source"], len(ca["POSITION"]), "vertex", -1, n)
    fm = p.integer_rows(delta["candidate_face_to_source"], len(cf), "face", 0, m)
    moved = integer_set(delta, "moved_source_vertices", n)
    normal = integer_set(delta, "original_normal_changed_vertex_ids", n)
    weight = integer_set(delta, "original_weight_changed_vertex_ids", n)
    modified = moved | normal | weight
    require(integer_set(delta, "modified_source_vertices", n) == modified, "Modified set differs from P/N/W declaration union")
    protected = integer_set(delta, "protected_source_vertices", n)
    require(protected == set(range(n))-modified, "Protected set is not the exact modified-set complement")
    roi = integer_set(delta, "ROI_faces", m)
    splits = integer_set(delta, "normal_split_vertices", len(vm))
    require(set(sa) == set(ca), "Attribute set changed")
    retained = np.flatnonzero(vm >= 0)
    require(set(vm[retained]) == set(range(n)), "A source vertex is missing")
    for old in range(n):
        ids = np.flatnonzero(vm == old)
        require(len(ids) >= 1 and set(ids[1:]) <= splits, "Undeclared original normal-corner duplicate")
        for semantic in ("POSITION", "TEXCOORD_0", "JOINTS_0", "WEIGHTS_0"):
            require(np.array_equal(ca[semantic][ids], np.repeat(ca[semantic][ids[:1]], len(ids), axis=0)),
                    "Normal split changed a source control's geometry/UV/skin: " + semantic)
    changed = {}
    for semantic in sa:
        changed[semantic] = set(vm[retained[np.any(ca[semantic][retained] != sa[semantic][vm[retained]], axis=1)]].tolist())
    require(changed["POSITION"] == moved, "POSITION changes differ from moved-source declaration")
    require(changed["NORMAL"] == normal, "NORMAL changes differ from original-normal declaration")
    require(changed["JOINTS_0"] | changed["WEIGHTS_0"] == weight,
            "Skin changes differ from original-weight declaration")
    require(not changed["TEXCOORD_0"], "Original UV changed")
    for semantic in set(sa)-{"POSITION", "NORMAL", "JOINTS_0", "WEIGHTS_0", "TEXCOORD_0"}:
        require(not changed[semantic], "Protected extra source attribute changed: " + semantic)

    rows = delta.get("candidate_added_vertices", [])
    require(isinstance(rows, list), "Inserted correspondence must be a list")
    added = {row["candidate_vertex_id"]: row for row in rows}
    require(len(added) == len(rows) and set(added) == set(np.flatnonzero(vm == -1)),
            "Inserted correspondence incomplete or duplicated")
    ref_open, ref_normal = [], []
    for vertex, row in added.items():
        parent = row["source_face_id"]
        bary = np.asarray(row["barycentric"], float)
        require(type(parent) is int and parent in roi and bary.shape == (3,) and np.isfinite(bary).all()
                and (bary >= -1e-7).all() and abs(bary.sum()-1) < 1e-7, "Invalid inserted parent/barycentric")
        require(np.array_equal(row["source_vertex_ids"], sf[parent]), "Inserted source parent vertices differ")
        require(np.max(abs(ca["TEXCOORD_0"][vertex]-bary@sa["TEXCOORD_0"][sf[parent]])) < 2e-6,
                "Inserted UV differs from original parent barycentric projection")
    domain = anatomy(source, sb)
    edit_strength, strength_report = edit_strength_audit(added, vm, delta, domain)
    inserted_weights, weight_report = weighted_skin(source, sb, candidate, cb, added, vm, weight, delta, domain, edit_strength)
    original_proof = {}
    candidate_open = v.actual_skin(candidate, cb, 0.)
    for old in sorted(modified):
        require(domain["source_evidence"][old] is not None,
                "Modified original control is outside actual dorsal/side finger anatomy: " + str(old))
        ids = np.flatnonzero(vm == old)
        original_proof[str(old)] = dict(domain["source_evidence"][old],
            candidate_corner_ids=ids.tolist(), source_bind_position_m=sa["POSITION"][old].tolist(),
            candidate_bind_position_m=ca["POSITION"][ids[0]].tolist(),
            bind_delta_mm=((ca["POSITION"][ids[0]]-sa["POSITION"][old])*1000).tolist(),
            actual_open_delta_mm=((candidate_open[ids[0]]-domain["source_points"][old])*1000).tolist(),
            normal_corner_rotation_degrees=np.degrees(np.arccos(np.clip(ca["NORMAL"][ids]@sa["NORMAL"][old], -1., 1.))).tolist(),
            source_JOINTS_0=sa["JOINTS_0"][old].tolist(), source_WEIGHTS_0=sa["WEIGHTS_0"][old].tolist(),
            candidate_JOINTS_0=ca["JOINTS_0"][ids[0]].tolist(), candidate_WEIGHTS_0=ca["WEIGHTS_0"][ids[0]].tolist())
    # Protect the accepted MCP redistribution controls explicitly in addition
    # to the geometric domain: these source IDs come from the frozen a980 map.
    source_delta = json.loads((SOURCE.parent/"patch_delta.json").read_text())
    old_metacarpal = set(source_delta.get("anatomical_metacarpal_vertices", []))
    accepted_map = np.asarray(source_delta["candidate_vertex_to_source"])
    accepted_palm = set(np.flatnonzero(np.isin(accepted_map, list(old_metacarpal))).tolist())
    require(not (modified & accepted_palm), "Accepted14-point MCP palm repair was modified")
    ordered = sorted(added)
    for vertex in ordered:
        row = added[vertex]
        face, bary = sf[row["source_face_id"]], np.asarray(row["barycentric"])
        ref_open.append(bary@domain["source_points"][face])
        ref_normal.append(unit(bary@domain["source_normals"][face]))
    classification = domain["classify"](np.asarray(ref_open).reshape(-1, 3), np.asarray(ref_normal).reshape(-1, 3))
    inserted_proof, linear_support, inherited_weight_support, inside = {}, [], [], set()
    for vertex, evidence in zip(ordered, classification):
        row = added[vertex]
        reference = np.asarray(row["barycentric"])@sa["POSITION"][sf[row["source_face_id"]]]
        if evidence is None:
            if vertex in inserted_weights:
                expected_open = np.asarray(row["barycentric"])@domain["source_points"][sf[row["source_face_id"]]]
                require(str(vertex) in weight_report["updated_original_control_barycentric_projection"]
                        and np.max(abs(candidate_open[vertex]-expected_open)) < 2e-7,
                        "Independent weight/shape edit is outside actual dorsal/side finger anatomy: " + str(vertex))
                inherited_weight_support.append(vertex)
            else:
                require(np.max(abs(ca["POSITION"][vertex]-reference)) < 2e-7,
                        "Deformed inserted control is outside actual dorsal/side finger anatomy: " + str(vertex))
            require(edit_strength[vertex] == 0, "Inserted edit strength authorizes a protected anatomical sample")
            linear_support.append(vertex)
        else:
            inside.add(vertex)
            inserted_proof[str(vertex)] = evidence

    # Actual support is reconstructed from topology and attributes. A declared
    # extra untouched boundary face must share a geometric edge with that
    # support; declaring an arbitrary palm ROI cannot authorize deformation.
    counts = np.bincount(fm, minlength=m)
    actual_support = set(np.flatnonzero(counts != 1).tolist())
    for old in range(m):
        children = np.flatnonzero(fm == old)
        require(len(children) > 0, "A source parent face is missing")
        if len(children) == 1 and not np.array_equal(vm[cf[children[0]]], sf[old]):
            actual_support.add(old)
    actual_support |= set(np.flatnonzero(np.isin(sf, list(modified)).any(axis=1)).tolist())
    weld = v.position_weld(sa["POSITION"])
    support_edges = set()
    for face in weld[sf[list(actual_support)]] if actual_support else []:
        support_edges.update(tuple(sorted((int(face[i]), int(face[j])))) for i, j in ((0, 1), (1, 2), (2, 0)))
    justified_boundary = set()
    for old in roi-actual_support:
        face = weld[sf[old]]
        if any(tuple(sorted((int(face[i]), int(face[j])))) in support_edges for i, j in ((0, 1), (1, 2), (2, 0))):
            justified_boundary.add(old)
    require(actual_support <= roi, "Actual modified parent is missing from ROI")
    require(roi <= actual_support | justified_boundary, "Declared ROI contains unjustified untouched source faces")
    for old in set(range(m))-roi:
        child = np.flatnonzero(fm == old)
        require(len(child) == 1 and np.array_equal(vm[cf[child[0]]], sf[old]), "Protected face topology/winding changed")
    # All truly rebuilt parents need anatomical skin support. Linear off-domain
    # cutting points may complete the shared boundary of an adjacent patch.
    anatomical_parents = set(np.flatnonzero(np.array([row is not None for row in domain["source_evidence"]])[sf].any(1)).tolist())
    anatomical_parents |= {added[i]["source_face_id"] for i in inside}
    for old in actual_support:
        if old in anatomical_parents:
            continue
        require(not np.isin(sf[old], list(modified)).any(), "Non-anatomical modified parent")
        face = set(weld[sf[old]])
        require(any(len(face & set(weld[sf[parent]])) >= 2 for parent in anatomical_parents & actual_support),
                "Non-anatomical cutting support is not adjacent to the real finger patch")
    for face, parent in zip(cf, fm):
        ids = set(sf[parent])
        for vertex in face:
            if vm[vertex] >= 0:
                require(vm[vertex] in ids, "Retained corner does not belong to mapped parent")
            else:
                row = added[int(vertex)]
                support = {i for i, coefficient in zip(row["source_vertex_ids"], row["barycentric"]) if coefficient > 1e-7}
                require(support <= ids, "Inserted corner does not belong to mapped parent")
    for vertex in splits:
        if vm[vertex] >= 0:
            require(np.count_nonzero(vm == vm[vertex]) > 1, "Declared normal split has no original peer")
        else:
            require(any(vertex in group for group in p.seam_groups(vm, added)), "Declared inserted normal split has no barycentric peer")
    report = {"moved_source_vertices": sorted(moved), "normal_changed_source_vertices": sorted(normal),
        "weight_changed_source_vertices": sorted(weight), "protected_original_attributes_exact": True,
        "original_UV_exact": True, "original_changes_anatomical_proof": original_proof,
        "accepted_MCP_palm_controls_protected": sorted(accepted_palm),
        "inserted_anatomical_evidence": inserted_proof, "zero_shape_change_linear_support_vertices": linear_support,
        "zero_open_shape_change_updated_control_weight_support_vertices": inherited_weight_support,
        "weight_projection": weight_report, "edit_strength_field": strength_report,
        "actual_support_source_faces": sorted(actual_support),
        "necessary_untouched_boundary_faces": sorted(justified_boundary), "normal_split_vertices": sorted(splits),
        "source_vertices": n, "source_faces": m, "candidate_vertices": len(vm), "candidate_faces": len(fm),
        "actual_bones": domain["actual_bones"], "basis": domain["basis"], "anatomical_domain": domain["domain_rule"]}
    return vm, fm, added, protected, report


def mesh_health(candidate, cb):
    a, faces = v.attributes(candidate, cb), v.faces(candidate, cb)
    total = sum(len(v.faces(candidate, cb, i)) for i in range(len(candidate["meshes"][0]["primitives"])))
    require(total <= 12000, "Triangle budget exceeded")
    require(v.primitive(candidate).get("mode", 4) == 4, "Expected triangle-list mode")
    require(len(faces) and faces.min() >= 0 and faces.max() < len(a["POSITION"]), "Face index out of bounds")
    for semantic, array in a.items():
        require(len(array) == len(a["POSITION"]) and np.isfinite(array).all(), "Nonfinite/wrong-length " + semantic)
    require(np.max(abs(np.linalg.norm(a["NORMAL"], axis=1)-1)) < 2e-4, "Nonunit normals")
    v.actual_skin(candidate, cb)
    points = a["POSITION"][faces]
    require((np.linalg.norm(np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0]), axis=1) > 1e-14).all(),
            "Degenerate bind triangle")
    return {"vertices": len(a["POSITION"]), "main_triangles": len(faces), "total_triangles": total, "budget": 12000}


def verify(source, sb, candidate, cb, delta, dao=None):
    report = {"passed": False, "errors": [], "poses": {}}
    report["rig_resources"] = v.exact_rig_and_resources(source, sb, candidate, cb)
    require(len(source["skins"][0]["joints"]) == 78, "Expected original78-joint rig")
    report["health"] = mesh_health(candidate, cb)
    report["topology"] = v.topology_health(candidate, cb)
    vm, fm, added, protected, report["correspondence"] = mapping(source, sb, candidate, cb, delta)
    for time in POSES:
        row = f.posed_audit(source, sb, candidate, cb, vm, fm, added, protected, time)
        if dao is not None:
            print("COLLISION_POSE", time, flush=True)
            row["contacts"] = f.collision_audit(source, sb, candidate, cb, vm, fm, added, set(delta["ROI_faces"]), time, dao)
            report["errors"].extend(str(time)+": "+error for error in row["contacts"]["errors"])
        report["errors"].extend(str(time)+": "+error for error in row["errors"])
        report["poses"][str(time)] = row
    report["passed"] = not report["errors"]
    report["limits"] = ["Finite default/open/mid/closed mathematical LBS and normal checks; not continuous time, SDK TBN, native visual acceptance or performance clearance.",
        "Complete triangle-pair sets use the frozen repository crossing convention. Source-parent mapping distinguishes subdivision multiplicity from new anatomical crossings. Inherited source109 self pairs and open/mid Dao issues remain explicit."]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=HERE/"right_hand_joint.glb")
    parser.add_argument("--delta", type=Path, default=HERE/"joint_delta.json")
    parser.add_argument("--output", type=Path, default=HERE/"verification.json")
    parser.add_argument("--geometry-only", action="store_true")
    args = parser.parse_args()
    report = {"passed": False}
    try:
        delta = json.loads(args.delta.read_text())
        delta_sha = v.digest(args.delta)
        require(v.digest(SOURCE) == SOURCE_SHA and delta["source_sha256"] == SOURCE_SHA, "Pinned a980 source identity differs")
        require(delta["candidate_sha256"] == v.digest(args.candidate), "Candidate/delta identity differs")
        report = verify(*v.h.read(SOURCE), *v.h.read(args.candidate), delta,
                        None if args.geometry_only else v.dao_geometry(DAO))
        require(v.digest(SOURCE) == SOURCE_SHA and v.digest(args.candidate) == delta["candidate_sha256"]
                and v.digest(args.delta) == delta_sha, "Inputs changed during audit")
        require(v.digest(Path(__file__)) == VERIFIER_SHA, "Verifier changed during execution")
    except (ValueError, KeyError, IndexError, TypeError) as error:
        report["passed"], report["error"] = False, str(error)
    report.update(source_sha256=v.digest(SOURCE), candidate_sha256=v.digest(args.candidate),
        delta_sha256=v.digest(args.delta), verifier_sha256=VERIFIER_SHA, tests_sha256=v.digest(HERE/"test_verify_joint.py"),
        frozen_audit_dependency_sha256=v.digest(HERE.parent/"verify_finger.py"), collision_checks_run=not args.geometry_only)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"passed": report["passed"], "error": report.get("error"), "errors": report.get("errors"), "output": str(args.output)}))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
