"""Real joint-loop candidate acceptance and deliberate contract violations."""
import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_joint as q


def changed_attribute(document, binary, semantic, vertex, amount):
    accessor = document["accessors"][q.v.primitive(document)["attributes"][semantic]]
    view = document["bufferViews"][accessor["bufferView"]]
    array = q.v.attributes(document, binary)[semantic].copy()
    array[vertex, 0] += amount
    stride = array.shape[1]*array.dtype.itemsize
    if view.get("byteStride", stride) != stride:
        raise ValueError("Negative-case helper needs an unstrided candidate stream")
    offset = view.get("byteOffset", 0)+accessor.get("byteOffset", 0)
    result = bytearray(binary)
    result[offset:offset+array.nbytes] = array.tobytes()
    return bytes(result)


def declare_original_change(delta, key, old):
    delta[key] = sorted(set(delta.get(key, [])) | {old})
    modified = set(delta.get("moved_source_vertices", [])) | set(delta.get("original_normal_changed_vertex_ids", [])) | set(delta.get("original_weight_changed_vertex_ids", []))
    delta["modified_source_vertices"] = sorted(modified)
    delta["protected_source_vertices"] = sorted(set(range(delta["source_vertex_count"]))-modified)


class JointLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.sb = q.v.h.read(q.SOURCE)
        cls.candidate, cls.cb = q.v.h.read(HERE/"right_hand_joint.glb")
        cls.delta = json.loads((HERE/"joint_delta.json").read_text())
        cls.mapping = q.mapping(cls.source, cls.sb, cls.candidate, cls.cb, cls.delta)
        cls.domain = q.anatomy(cls.source, cls.sb)
        basis = cls.domain["basis"]
        local = (cls.domain["source_points"]-np.array(basis["origin_m"]))@np.array([basis["radial"], basis["finger_forward"], basis["palmar"]]).T
        facing = cls.domain["source_normals"]@np.array(basis["palmar"])
        inner = np.flatnonzero((facing > .6) & (local[:, 1] > .04) & (local[:, 1] < .09) & (abs(local[:, 0]) < .025))
        if not len(inner):
            raise ValueError("No independent inner-palm negative-case control")
        cls.palm = int(inner[np.argmin(abs(local[inner, 1]-.065))])
        cls.palm_proof = {"source_vertex": cls.palm, "open_hand_local_m": local[cls.palm].tolist(),
                          "palmar_normal_dot": float(facing[cls.palm])}

    def test_actual_feature_mapping_and_resources(self):
        self.assertTrue(self.mapping[4]["protected_original_attributes_exact"])
        self.assertTrue(self.mapping[4]["original_UV_exact"])
        self.assertGreater(len(self.mapping[2]), 0)
        q.v.exact_rig_and_resources(self.source, self.sb, self.candidate, self.cb)
        q.mesh_health(self.candidate, self.cb)
        q.v.topology_health(self.candidate, self.cb)

    def test_actual_four_poses(self):
        vm, fm, added, protected, _ = self.mapping
        for time in q.POSES:
            with self.subTest(pose=time):
                row = q.f.posed_audit(self.source, self.sb, self.candidate, self.cb, vm, fm, added, protected, time)
                self.assertTrue(row["passed"], row["errors"])

    def test_inner_palm_move_rejected_even_if_declared(self):
        cb = changed_attribute(self.candidate, self.cb, "POSITION", self.palm, .001)
        delta = copy.deepcopy(self.delta)
        declare_original_change(delta, "moved_source_vertices", self.palm)
        with self.assertRaisesRegex(ValueError, "Modified original control is outside actual dorsal/side finger anatomy"):
            q.mapping(self.source, self.sb, self.candidate, cb, delta)

    def test_inner_palm_normal_rejected_even_if_declared(self):
        cb = changed_attribute(self.candidate, self.cb, "NORMAL", self.palm, .01)
        delta = copy.deepcopy(self.delta)
        declare_original_change(delta, "original_normal_changed_vertex_ids", self.palm)
        with self.assertRaisesRegex(ValueError, "Modified original control is outside actual dorsal/side finger anatomy"):
            q.mapping(self.source, self.sb, self.candidate, cb, delta)

    def test_forged_untouched_palm_ROI_rejected(self):
        delta = copy.deepcopy(self.delta)
        faces = q.v.faces(self.source, self.sb)
        parent = int(np.flatnonzero((faces == self.palm).any(1))[0])
        self.assertNotIn(parent, delta["ROI_faces"])
        delta["ROI_faces"] = sorted(set(delta["ROI_faces"]) | {parent})
        with self.assertRaisesRegex(ValueError, "Declared ROI contains unjustified untouched source faces"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_original_UV_edit_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "TEXCOORD_0", self.palm, .01)
        with self.assertRaisesRegex(ValueError, "Original UV changed"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_inserted_UV_edit_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "TEXCOORD_0", min(self.mapping[2]), .01)
        with self.assertRaisesRegex(ValueError, "Inserted UV differs"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_undeclared_local_weight_edit_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "WEIGHTS_0", self.palm, .01)
        with self.assertRaisesRegex(ValueError, "Skin changes differ from original-weight declaration"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_foreign_anatomical_weight_anchor_rejected(self):
        delta = copy.deepcopy(self.delta)
        rows = [row for row in delta.get("weight_change_projections", []) if "source_vertex_ids" in row]
        if not rows:
            self.skipTest("This candidate has no local anatomical-anchor weight edits")
        rows[0]["source_vertex_ids"][0] = self.palm
        with self.assertRaisesRegex(ValueError, "Weight source anchor is outside the same true finger domain"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_wrong_local_weight_kernel_rejected(self):
        delta = copy.deepcopy(self.delta)
        rows = [row for row in delta.get("weight_change_projections", []) if len(row.get("source_vertex_ids", [])) >= 2]
        if not rows:
            self.skipTest("This candidate has no multi-anchor weight interpolation")
        coefficients = np.asarray(rows[0]["coefficients"])
        coefficients[:] = 0.
        coefficients[0] = 1.
        rows[0]["coefficients"] = coefficients.tolist()
        with self.assertRaisesRegex(ValueError, "Weight anchor coefficients differ"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_inserted_strength_cannot_bypass_source_control_cap(self):
        delta = copy.deepcopy(self.delta)
        source = np.asarray(delta["edit_strength_source"])
        row = next(row for row in delta["candidate_added_vertices"]
                   if np.asarray(row["barycentric"])@source[row["source_vertex_ids"]] < .95)
        cap = float(np.asarray(row["barycentric"])@source[row["source_vertex_ids"]])
        delta["edit_strength_candidate"][row["candidate_vertex_id"]] = cap+.01
        with self.assertRaisesRegex(ValueError, "Inserted edit strength exceeds its parent barycentric source-control cap"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_weight_blend_must_follow_capped_edit_strength(self):
        delta = copy.deepcopy(self.delta)
        row = next(row for row in delta["weight_change_projections"] if row.get("blend_factor", 0) > .01)
        row["blend_factor"] = 0.
        with self.assertRaisesRegex(ValueError, "Local weight blend does not match capped anatomical edit strength"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_new_weight_sample_must_use_updated_parent_control_barycentric(self):
        delta = copy.deepcopy(self.delta)
        row = next(row for row in delta["weight_change_projections"]
                   if row.get("kind") == "updated_control_barycentric" and len(row["control_coefficients"]) >= 2)
        donor = int(np.argmax(row["control_coefficients"]))
        recipient = (donor+1)%len(row["control_coefficients"])
        row["control_coefficients"][donor] -= .01
        row["control_coefficients"][recipient] += .01
        with self.assertRaisesRegex(ValueError, "Updated-control weight projection differs from its original parent barycentric correspondence"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_missing_correspondence_rejected(self):
        delta = copy.deepcopy(self.delta)
        delta["candidate_face_to_source"].pop()
        with self.assertRaisesRegex(ValueError, "Invalid face mapping size/type"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_Grip_edit_rejected(self):
        candidate = copy.deepcopy(self.candidate)
        node = next(n for n in candidate["nodes"] if "Grip" in n.get("name", ""))
        node["translation"] = [.001, 0., 0.]
        with self.assertRaisesRegex(ValueError, "Protected JSON changed: nodes"):
            q.v.exact_rig_and_resources(self.source, self.sb, candidate, self.cb)

    def test_source_parent_pair_multiplicity(self):
        parent_map = np.array([0, 0, 1, 2, 2])
        same = q.v.mapped_pair_delta({(0, 2)}, {(0, 3), (1, 4)}, parent_map, True)
        self.assertEqual(same["new_source_face_pairs"], [])
        bad = q.v.mapped_pair_delta({(0, 2)}, {(0, 2)}, parent_map, True)
        self.assertEqual(bad["new_source_face_pairs"], [(0, 1)])
        self.assertEqual(bad["removed_source_face_pairs"], [(0, 2)])


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(JointLoopTests))
    report = {"passed": result.wasSuccessful(), "tests_run": result.testsRun,
        "errors": [(str(test), message) for test, message in result.errors],
        "failures": [(str(test), message) for test, message in result.failures],
        "source_sha256": q.v.digest(q.SOURCE), "candidate_sha256": q.v.digest(HERE/"right_hand_joint.glb"),
        "verifier_sha256": q.v.digest(HERE/"verify_joint.py"), "tests_sha256": q.v.digest(Path(__file__)),
        "inner_palm_negative_case": getattr(JointLoopTests, "palm_proof", None)}
    (HERE/"verification_tests.json").write_text(json.dumps(report, indent=2)+"\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)
