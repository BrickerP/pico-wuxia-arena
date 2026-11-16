"""Thin independent audit adapter for the Left derived from frozen Right199c.

Reuse the frozen common-Grip contract, negative controls and actual-DAO contact
auditor. A separate covariance check reflects DAO too and compares complete pair
sets with the certified Right. No mirror producer or replacement auditor here.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
sys.modules.setdefault("verify_left", sys.modules[__name__])
HERE = Path(__file__).resolve().parent
JOINT = HERE.parent
GRIP = JOINT.parents[1]
REPO = GRIP.parents[4]
LEGACY = GRIP / "left-rebuild"
SOURCE = JOINT / "right_hand_joint.glb"
CANDIDATE = HERE / "left_hand_joint.glb"
DAO = REPO / "ArtSource/tripo-warrior/library/dao_grip.glb"
RIGHT_SHA = "199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64"
LEFT_SHA = "0295c147673a5cf15b4265cbfcb83391d2fa399b8be778c54ecc789fc61c46f7"
DAO_SHA = "db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0"
REFERENCE = GRIP/"palm-wrist-surface/production-patch/anatomical-crease/left-derivation/left_hand_anatomical.glb"
REFERENCE_SHA = "ecc071364b89d6ec64fad5a8924f2c65d2e787822a28e3088a2aa7c35a0a02ab"
DEPS = {"build_left.py": "f23797a0af98f26b83f032aff1540fc7d81b070351d33ab89ddb074de058c29f",
        "verify_left_rebuild.py": "4cd634d3c854825cd4761e2e78df75c169ad80b1ca673eb7dfacacaf80340447",
        "test_verify_left_rebuild.py": "425c7f9b50571810181ca61353e4d5b5b812e347760de8c1251f340d392317f7"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


joint = load("left_joint_frozen_audit", JOINT / "verify_joint.py")
v, require = joint.v, joint.require
VERIFIER_SHA = v.digest(Path(__file__))
_legacy = None


def legacy():
    global _legacy
    if _legacy is None:
        for name, pin in DEPS.items():
            require(v.digest(LEGACY/name) == pin, "Frozen common-Grip dependency changed: " + name)
        _legacy = load("verify_left_rebuild", LEGACY / "verify_left_rebuild.py")
        _legacy.SOURCE, _legacy.CANDIDATE, _legacy.DAO = SOURCE, CANDIDATE, DAO
        _legacy.PINS = {"source": RIGHT_SHA, "candidate": LEFT_SHA, "dao": DAO_SHA}
    return _legacy


def certify_source(source_path=SOURCE, review=None, delta=None):
    require(v.digest(source_path) == RIGHT_SHA, "Only the current199c Right may supply this Left")
    review = json.loads((JOINT/"verification.json").read_text()) if review is None else review
    delta = json.loads((JOINT/"joint_delta.json").read_text()) if delta is None else delta
    require(review.get("passed") is True and review.get("collision_checks_run") is True
            and review.get("candidate_sha256") == RIGHT_SHA and not review.get("errors"),
            "Current199c Right full certification is missing or mismatched")
    require(delta["candidate_sha256"] == RIGHT_SHA and v.digest(JOINT/"joint_delta.json") == review["delta_sha256"],
            "Current199c Right delta/certification differs")
    require(v.digest(JOINT/"verify_joint.py") == review["verifier_sha256"]
            and v.digest(JOINT/"test_verify_joint.py") == review["tests_sha256"],
            "Certified Right audit implementation changed")
    require(set(review["poses"]) == {"None", "0.0", "0.5", "1.0"}, "Right four-pose certification incomplete")
    return review, delta


def inputs():
    review, delta = certify_source()
    require(v.digest(CANDIDATE) == LEFT_SHA, "Pinned derived Left identity differs")
    require(v.digest(DAO) == DAO_SHA, "Pinned actual unreflected DAO differs")
    check = legacy()
    return check, *v.h.read(SOURCE), *v.h.read(CANDIDATE), review, delta


def frozen():
    require(v.digest(SOURCE) == RIGHT_SHA and v.digest(CANDIDATE) == LEFT_SHA
            and v.digest(DAO) == DAO_SHA and v.digest(Path(__file__)) == VERIFIER_SHA,
            "Audit input/adapter changed during execution")
    for name, pin in DEPS.items():
        require(v.digest(LEGACY/name) == pin, "Frozen dependency changed during audit: " + name)


def stamp(report):
    report.update(source_sha256=RIGHT_SHA, candidate_sha256=LEFT_SHA, actual_dao_sha256=DAO_SHA,
        verifier_sha256=VERIFIER_SHA, tests_sha256=v.digest(HERE/"test_left.py"),
        source_certification_sha256=v.digest(JOINT/"verification.json"), source_delta_sha256=v.digest(JOINT/"joint_delta.json"),
        frozen_dependencies=DEPS)
    return report


def write(name, report):
    frozen()
    path = HERE/name
    path.write_text(json.dumps(stamp(report), indent=2)+"\n")
    print(json.dumps({"passed": report.get("passed"), "output": str(path)}), flush=True)
    return report


def contract():
    check, right, rb, left, lb, review, delta = inputs()
    require(lb[:len(rb)] == rb, "Complete current Right BIN prefix was not preserved")
    result = check.verify_contract(right, rb, left, lb)
    for state in result["states"]:
        require(state["joint_world_max_error"] == 0, "Nonzero joint S M S reflection error")
        for primitive in state["primitives"]:
            require(all(primitive[k] == 0 for k in ("LBS_max_error_m", "inverse_transpose_normal_max_error", "winding_area_vector_max_error_m2")),
                    "Nonzero actual skin/normal/winding reflection error")
    protected = set(delta["protected_source_vertices"])
    vm = np.asarray(delta["candidate_vertex_to_source"])
    ids = np.flatnonzero(np.isin(vm, list(protected)))
    protection, closure = [], {}
    for time in joint.POSES:
        rp, lp = v.actual_skin(right, rb, time), v.actual_skin(left, lb, time)
        error = float(np.max(abs(lp[ids]-rp[ids]*[-1., 1., 1.])))
        require(error == 0, "Protected original-source domain did not reflect exactly")
        protection.append({"time": "default" if time is None else time, "protected_source_controls": len(protected),
                           "protected_current_Right_vertices": len(ids), "LBS_mirror_error_m": error})
    for side, document, binary in (("R", right, rb), ("L", left, lb)):
        p0, faces0 = v.actual_geometry(document, binary, None)
        p1, faces1 = v.actual_geometry(document, binary, 1.)
        position = float(np.max(abs(p0-p1)))
        normal = float(np.max(abs(v.skinned_normal_vectors(document, binary, None)-v.skinned_normal_vectors(document, binary, 1.))))
        require(position == normal == 0 and np.array_equal(faces0, faces1), "Default is not exactly closed: " + side)
        closure[side] = {"default_vs_closed_LBS_error_m": position, "default_vs_closed_normal_error": normal,
                         "all_primitive_topology_equal": True}
    return {"passed": True, "independent_contract": result, "protected_domain": protection,
        "source_original_BIN_prefix_exact": True, "default_closed_equivalence": closure,
        "source_inherited_self_baseline": {time: {"raw": row["contacts"]["candidate_self_pair_count"],
            "source_parent_mapped": len(row["contacts"]["self_pair_delta"]["mapped_candidate_source_face_pairs"])}
            for time, row in review["poses"].items()},
        "limits": ["Actual mathematical default/open/mid/closed mirror equivalence, not SDK TBN or native visual acceptance."]}


def run_tests():
    legacy()
    tests = load("joint_left_adapter_tests", HERE/"test_left.py")
    suite = tests.make_suite()
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {"passed": result.wasSuccessful() and not result.skipped,
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "output": stream.getvalue(),
        "legacy_negative_controls_reused": 28, "additional_adapter_controls": result.testsRun-28}
    write("verification_tests.json", report)
    require(report["passed"] and result.testsRun >= 28, "Independent Left controls failed: " + stream.getvalue())
    return report


def actual_contacts():
    check, right, rb, left, lb, _, _ = inputs()
    report = check.audit_contacts(right, rb, left, lb)
    proof = contract()["default_closed_equivalence"]
    return {"passed": True, "actual_unreflected_DAO_and_self": report,
        "default_contact_state": {"identical_to_grip_time": 1., "actual_LBS_normal_and_topology_proof": proof},
        "limits": ["Actual DAO is measured independently for each hand and is not assumed symmetric.",
            "The legacy auditor includes coplanar positive-area overlap; its raw counts must not be mixed with the Right joint auditor's noncoplanar convention.",
            "Open/mid source penetrations are retained. Default contact data are exactly the closed state by the independently checked equivalence above."]}


def mirrored_dao():
    _, right, rb, left, lb, review, delta = inputs()
    components = v.dao_geometry(DAO)
    old, oldb = v.h.read(joint.SOURCE)
    require(v.digest(joint.SOURCE) == review["source_sha256"], "Frozen a980 parent identity differs")
    old_bind, old_faces = v.bind_geometry(old, oldb)
    old_weld = v.position_weld(old_bind)
    fm = np.asarray(delta["candidate_face_to_source"])
    closure_count = len(v.faces(right, rb, 1))
    face_map = np.r_[fm, np.arange(delta["source_face_count"], delta["source_face_count"]+closure_count)]
    left_bind, _ = v.bind_geometry(left, lb)
    left_weld = v.position_weld(left_bind)
    report = {"passed": True, "states": {}, "method": "Reflect DAO positions X and reverse its triangle winding, preserving component and triangle IDs. Compare Left+S*DAO with certified Right+DAO full pair sets at all four actual poses."}
    for time in joint.POSES:
        print("MIRRORED_DAO_POSE", time, flush=True)
        points, faces = v.actual_geometry(left, lb, time)
        cached = review["poses"][str(time)]["contacts"]
        self_pairs = v.crossing_pairs(points, faces, weld_ids=left_weld)
        require(self_pairs == {tuple(pair) for pair in cached["candidate_self_pairs"]},
                "Mirrored Left self pair set differs from current Right at " + str(time))
        mapped = json.loads(json.dumps(v.mapped_pair_delta(cached["source_self_pairs"], self_pairs, face_map, True, old_faces, old_weld)))
        require(mapped == cached["self_pair_delta"], "Left source-parent self mapping differs at " + str(time))
        results = {}
        for name, shape in components.items():
            mirrored_points = shape["points"]*[-1., 1., 1.]
            mirrored_faces = shape["faces"][:, [0, 2, 1]]
            pairs = v.crossing_pairs(points, faces, mirrored_points, mirrored_faces)
            expected = {tuple(pair) for pair in cached["actual_dao_pair_deltas"][name]["candidate_surface_pairs"]}
            require(pairs == expected, "Left+mirrored DAO pair set differs: " + name + " at " + str(time))
            results[name] = {"pair_count": len(pairs), "left_mirrored_DAO_pairs": sorted(pairs),
                             "same_as_certified_Right_actual_DAO_pairs": True}
        report["states"][str(time)] = {"raw_self_pair_count": len(self_pairs),
            "self_pairs": sorted(self_pairs), "source_parent_mapped_self_pair_count": len(mapped["mapped_candidate_source_face_pairs"]),
            "source_parent_self_pair_delta": mapped, "components": results}
    return report


def reflected_reference_rows(delta, reference, binary):
    """Mirror correspondence orientation, without changing source vertex IDs."""
    source_faces = v.faces(reference, binary)
    require(len(source_faces) == delta["source_face_count"]
            and len(v.attributes(reference, binary)["POSITION"]) == delta["source_vertex_count"],
            "Historical anatomical Left is not the a980 correspondence source")
    rows = {}
    for original in delta["candidate_added_vertices"]:
        row = copy.deepcopy(original)
        face = source_faces[row["source_face_id"]]
        require(np.array_equal(face, np.asarray(row["source_vertex_ids"])[[0, 2, 1]]),
                "Historical Left source face does not reverse the a980 Right winding")
        row["source_vertex_ids"] = face.tolist()
        row["barycentric"] = np.asarray(row["barycentric"])[[0, 2, 1]].tolist()
        rows[row["candidate_vertex_id"]] = row
    return rows


def actual_baseline():
    check, _, _, left, lb, review, delta = inputs()
    reference_sha = v.digest(REFERENCE)
    require(reference_sha == REFERENCE_SHA, "Reference is not the frozen a980-derived anatomical Left")
    reference, refb = v.h.read(REFERENCE)
    old_right, oldb = v.h.read(joint.SOURCE)
    require(v.digest(joint.SOURCE) == review["source_sha256"], "Historical a980 Right identity differs")
    reference_contract = check.verify_contract(old_right, oldb, reference, refb)
    require(reference_contract["passed"], "Historical Left is not independently equivalent to a980 Right")
    vm = np.asarray(delta["candidate_vertex_to_source"])
    fm = np.asarray(delta["candidate_face_to_source"])
    added = reflected_reference_rows(delta, reference, refb)
    dao = v.dao_geometry(DAO)
    report = {"passed": True, "reference_sha256": reference_sha,
        "reference_role": "Only the correctly a980-derived Left baseline; never a replacement production input for current199c.",
        "reference_mirror_contract": reference_contract,
        "correspondence": "Keep vm/fm/source vertex IDs. Source Left faces reverse corners1/2, so source_vertex_ids and barycentric coefficients reverse corners1/2 together.",
        "states": {}, "errors": []}
    for time in joint.POSES:
        print("ACTUAL_LEFT_BASELINE_POSE", time, flush=True)
        row = joint.f.collision_audit(reference, refb, left, lb, vm, fm, added, set(delta["ROI_faces"]), time, dao)
        report["states"][str(time)] = row
        report["errors"].extend(str(time)+": "+error for error in row["errors"])
    report["passed"] = not report["errors"]
    require(v.digest(REFERENCE) == reference_sha, "Historical Left reference changed during contact audit")
    return report


def assemble():
    names = ("verification_contract.json", "verification_tests.json", "verification_actual_contacts.json", "verification_mirror_dao.json", "verification_actual_baseline.json")
    reports = {name: json.loads((HERE/name).read_text()) for name in names}
    for name, report in reports.items():
        require(report.get("passed") is True and report["source_sha256"] == RIGHT_SHA
                and report["candidate_sha256"] == LEFT_SHA and report["verifier_sha256"] == VERIFIER_SHA
                and report["tests_sha256"] == v.digest(HERE/"test_left.py"), "Stale/failed Left audit packet: " + name)
    return {"passed": True, "reports": reports,
        "limits": ["Finite asset mirror and contact audit; not a claim of zero inherited self intersections, safe continuous motion, SDK TBN, device physiology, performance or final hand quality."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("all", "contract", "actual", "mirror", "baseline", "assemble"), default="all")
    args = parser.parse_args()
    if args.mode in ("all", "contract"):
        write("verification_contract.json", contract())
        run_tests()
    if args.mode in ("all", "actual"):
        write("verification_actual_contacts.json", actual_contacts())
    if args.mode in ("all", "mirror"):
        write("verification_mirror_dao.json", mirrored_dao())
    if args.mode in ("all", "baseline"):
        write("verification_actual_baseline.json", actual_baseline())
    if args.mode in ("all", "assemble"):
        write("verification.json", assemble())


if __name__ == "__main__":
    main()
