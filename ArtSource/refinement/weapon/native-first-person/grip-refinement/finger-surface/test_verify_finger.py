"""Real-candidate happy path and deliberate corruption rejection checks."""
import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_finger as q


def changed_attribute(document, binary, semantic, vertex, amount):
    """Mutate one actual stream element, leaving the candidate JSON untouched."""
    accessor = document["accessors"][q.v.primitive(document)["attributes"][semantic]]
    view = document["bufferViews"][accessor["bufferView"]]
    array = q.v.attributes(document, binary)[semantic].copy()
    array[vertex, 0] += amount
    require_stride = array.shape[1]*array.dtype.itemsize
    if view.get("byteStride", require_stride) != require_stride:
        raise ValueError("Negative-case helper requires an unstrided candidate stream")
    offset = view.get("byteOffset", 0)+accessor.get("byteOffset", 0)
    result = bytearray(binary)
    result[offset:offset+array.nbytes] = array.tobytes()
    return bytes(result)


class FingerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.sb = q.v.h.read(q.SOURCE)
        cls.candidate, cls.cb = q.v.h.read(HERE/"right_hand_finger.glb")
        cls.delta = json.loads((HERE/"finger_delta.json").read_text())
        cls.map = q.mapping(cls.source, cls.sb, cls.candidate, cls.cb, cls.delta)
        evidence = q.anatomical_audit(cls.source, cls.sb, cls.map[2])
        frame = evidence["basis"]
        points = q.v.actual_skin(cls.source, cls.sb, 0.)
        palm = np.array(frame["palmar"])
        normal = q.v.skinned_normal_vectors(cls.source, cls.sb, 0.)
        local = (points-np.array(frame["origin_m"]))@np.array([frame["radial"], frame["finger_forward"], frame["palmar"]]).T
        eligible = np.flatnonzero((normal@palm > .6) & (local[:, 1] > .04) & (local[:, 1] < .09) & (abs(local[:, 0]) < .025))
        if not len(eligible):
            raise ValueError("Cannot independently locate an inner-palm negative-case point")
        cls.palm_vertex = int(eligible[np.argmin(abs(local[eligible, 1]-.065))])
        cls.palm_proof = {"source_vertex": cls.palm_vertex, "open_hand_local_m": local[cls.palm_vertex].tolist(),
                          "palmar_normal_dot": float(normal[cls.palm_vertex]@palm),
                          "intentional_position_component_change_m": .001}

    def test_actual_candidate_correspondence(self):
        self.assertTrue(self.map[4]["all_original_positions_UV_skin_exact"])
        self.assertTrue(self.map[4]["all_protected_original_normals_exact"])
        self.assertGreater(len(self.map[2]), 0)
        q.v.exact_rig_and_resources(self.source, self.sb, self.candidate, self.cb)
        q.mesh_health(self.candidate, self.cb)
        q.v.topology_health(self.candidate, self.cb)

    def test_independent_actual_bone_surface_domain(self):
        proof = q.anatomical_audit(self.source, self.sb, self.map[2])
        self.assertEqual(len(proof["inserted_reference_evidence"]), len(self.map[2]))

    def test_all_four_actual_poses(self):
        vm, fm, added, protected, _ = self.map
        for time in q.POSES:
            with self.subTest(pose=time):
                result = q.posed_audit(self.source, self.sb, self.candidate, self.cb, vm, fm, added, protected, time)
                self.assertTrue(result["passed"], result["errors"])

    def test_forged_palmar_surface_domain_rejected(self):
        added = copy.deepcopy(self.map[2])
        row = added[min(added)]
        faces = q.v.faces(self.source, self.sb)
        parent = int(np.flatnonzero((faces == self.palm_vertex).any(axis=1))[0])
        face = faces[parent]
        bary = np.zeros(3)
        palm_corner = int(np.flatnonzero(face == self.palm_vertex)[0])
        bary[palm_corner], bary[(palm_corner+1)%3] = .5, .5
        row.update(source_face_id=parent, source_vertex_ids=face.tolist(), barycentric=bary.tolist())
        with self.assertRaisesRegex(ValueError, "outside independently reconstructed dorsal/side finger domain"):
            q.anatomical_audit(self.source, self.sb, added)

    def test_Grip_frame_change_rejected(self):
        candidate = copy.deepcopy(self.candidate)
        node = next(n for n in candidate["nodes"] if "Grip" in n.get("name", ""))
        node["translation"] = [.001, 0., 0.]
        with self.assertRaisesRegex(ValueError, "Protected JSON changed: nodes"):
            q.v.exact_rig_and_resources(self.source, self.sb, candidate, self.cb)

    def test_inner_palm_protection_violation_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "POSITION", self.palm_vertex, .001)
        with self.assertRaisesRegex(ValueError, "Protected attribute changed: POSITION"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_inner_palm_NORMAL_change_rejected_even_if_declared(self):
        cb = changed_attribute(self.candidate, self.cb, "NORMAL", self.palm_vertex, .01)
        delta = copy.deepcopy(self.delta)
        declared = set(delta.get("original_normal_changed_vertex_ids", [])) | {self.palm_vertex}
        delta["original_normal_changed_vertex_ids"] = sorted(declared)
        delta["modified_source_vertices"] = sorted(declared)
        delta["protected_source_vertices"] = sorted(set(range(delta["source_vertex_count"]))-declared)
        with self.assertRaisesRegex(ValueError, "Declared original normal is outside independently reconstructed dorsal/side finger domain"):
            q.mapping(self.source, self.sb, self.candidate, cb, delta)

    def test_original_weight_change_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "WEIGHTS_0", self.palm_vertex, .001)
        with self.assertRaisesRegex(ValueError, "Protected attribute changed: WEIGHTS_0"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_inserted_UV_change_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "TEXCOORD_0", min(self.map[2]), .01)
        with self.assertRaisesRegex(ValueError, "Inserted UV does not match"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_inserted_weight_change_rejected(self):
        cb = changed_attribute(self.candidate, self.cb, "WEIGHTS_0", min(self.map[2]), .01)
        with self.assertRaisesRegex(ValueError, "Inserted skin does not match"):
            q.mapping(self.source, self.sb, self.candidate, cb, self.delta)

    def test_missing_parent_mapping_rejected(self):
        delta = copy.deepcopy(self.delta)
        delta["candidate_face_to_source"].pop()
        with self.assertRaisesRegex(ValueError, "Invalid face mapping size/type"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_unprotected_original_rejected(self):
        delta = copy.deepcopy(self.delta)
        delta["protected_source_vertices"].pop()
        with self.assertRaisesRegex(ValueError, "Invalid protected mapping size/type"):
            q.mapping(self.source, self.sb, self.candidate, self.cb, delta)

    def test_parent_pair_mapping_distinguishes_subdivision(self):
        # Two subdivided crossings of the same old source pair do not add an
        # anatomical collision; an unrelated new pair cannot cancel an old one.
        old = {(0, 2)}
        child_to_parent = np.array([0, 0, 1, 2, 2])
        same = q.v.mapped_pair_delta(old, {(0, 3), (1, 4)}, child_to_parent, True)
        self.assertEqual(same["new_source_face_pairs"], [])
        new = q.v.mapped_pair_delta(old, {(0, 2)}, child_to_parent, True)
        self.assertEqual(new["new_source_face_pairs"], [(0, 1)])
        self.assertEqual(new["removed_source_face_pairs"], [(0, 2)])
        sibling = q.v.mapped_pair_delta(set(), {(0, 1)}, child_to_parent, True)
        self.assertEqual(sibling["new_source_face_pairs"], [(0, 0)])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FingerAuditTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"passed": result.wasSuccessful(), "tests_run": result.testsRun,
        "errors": [(str(t), message) for t, message in result.errors],
        "failures": [(str(t), message) for t, message in result.failures],
        "source_sha256": q.v.digest(q.SOURCE), "candidate_sha256": q.v.digest(HERE/"right_hand_finger.glb"),
        "verifier_sha256": q.v.digest(HERE/"verify_finger.py"), "tests_sha256": q.v.digest(Path(__file__)),
        "protection_violation_negative_case": getattr(FingerAuditTests, "palm_proof", None)}
    (HERE/"verification_tests.json").write_text(json.dumps(report, indent=2)+"\n")
    raise SystemExit(0 if result.wasSuccessful() else 1)
