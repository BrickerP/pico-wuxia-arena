"""Executable positive controls and asset-contract failure injections.

All GLB mutations are in memory. The published source and candidate are never
modified by these tests. Run python3 -B -m unittest discover -s <this directory>.
"""
import copy
import json
import unittest

import numpy as np
import verify_surface as v


class SurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document, cls.binary = v.h.read(v.REPO/"app/src/main/assets/models/player_hands/right_hand.glb")
        cls.source_attributes = v.attributes(cls.document, cls.binary)
        cls.source_faces = v.faces(cls.document, cls.binary)
        cls.constraints = json.loads((v.HERE/"roi_constraints.json").read_text())
        cls.delta = {"rois": {}, "source_support_face_ids": cls.constraints["source_support_face_ids"],
                     "candidate_vertex_to_source": list(range(len(cls.source_attributes["POSITION"]))),
                     "candidate_face_to_source_face": list(range(len(cls.source_faces))),
                     "candidate_added_vertices": []}
        for name, roi in cls.constraints["rois"].items():
            cls.delta["rois"][name] = {**roi, "candidate_vertex_ids": roi["source_vertex_ids"],
                                       "candidate_face_ids": roi["source_face_ids"]}

    def mutate_accessor(self, index, change):
        document, binary = copy.deepcopy(self.document), bytearray(self.binary)
        spec = document["accessors"][index]
        view = document["bufferViews"][spec["bufferView"]]
        values = v.h.values(document, binary, index)
        change(values)
        width = values.shape[1]*values.dtype.itemsize
        start = view.get("byteOffset", 0)+spec.get("byteOffset", 0)
        stride = view.get("byteStride", width)
        for row, value in enumerate(values):
            binary[start+row*stride:start+row*stride+width] = value.tobytes()
        return document, bytes(binary)

    def mutate_attribute(self, name, change):
        return self.mutate_accessor(v.primitive(self.document)["attributes"][name], change)

    def reject_health(self, name, change, message):
        document, binary = self.mutate_attribute(name, change)
        with self.assertRaisesRegex(ValueError, message):
            v.mesh_health(document, binary)

    def reject_delta(self, document, binary, message, delta=None):
        with self.assertRaisesRegex(ValueError, message):
            v.verify_delta(self.document, self.binary, document, binary,
                           self.delta if delta is None else delta, self.constraints)

    def test_exact_rig_resource_positive_control(self):
        self.assertTrue(v.exact_rig_and_resources(self.document, self.binary,
                                                  self.document, self.binary)["inverse_bind_matrices_exact"])

    def test_identity_topology_positive_control(self):
        report = v.verify_delta(self.document, self.binary, self.document, self.binary,
                                self.delta, self.constraints)
        self.assertTrue(report["passed"])
        self.assertEqual(report["inserted_vertices"], 0)

    def test_actual_default_equals_closed(self):
        np.testing.assert_allclose(v.actual_skin(self.document, self.binary),
                                   v.actual_skin(self.document, self.binary, 1.), atol=1e-12)

    def test_actual_mid_is_a_real_animation_sample(self):
        opened = v.actual_skin(self.document, self.binary, 0.)
        middle = v.actual_skin(self.document, self.binary, .5)
        closed = v.actual_skin(self.document, self.binary, 1.)
        self.assertGreater(np.max(abs(opened-closed)), .01)
        self.assertGreater(np.max(abs(middle-(opened+closed)/2)), 1e-4)

    def test_full_geometry_includes_unchanged_closure(self):
        points, faces = v.actual_geometry(self.document, self.binary, 1.)
        self.assertEqual(len(faces), 4936)
        self.assertGreater(len(points), 2741)

    def test_full_source_has_no_welded_boundary_or_nonmanifold_edges(self):
        self.assertTrue(all(value == 0 for value in v.topology_health(self.document, self.binary).values()))

    def test_open_seam_negative_control(self):
        document = copy.deepcopy(self.document)
        document["accessors"][v.primitive(document)["indices"]]["count"] -= 3
        with self.assertRaisesRegex(ValueError, "Open seam"):
            v.topology_health(document, self.binary)

    def test_source_healthy_with_disclosed_inherited_normal_corners(self):
        result = v.mesh_health(self.document, self.binary)
        self.assertEqual(result["normal_opposes_winding_corner_count"], 13)
        self.assertFalse(result["tangent_present"])

    def test_triangle_distance_interior_and_edge(self):
        tri = np.array([[[0., 0, 0], [1, 0, 0], [0, 1, 0]]])
        distance, _, location = v.closest_surface(np.array([[.2, .2, .1], [2., 0, 0]]), tri)
        np.testing.assert_allclose(distance, [.1, 1.], atol=1e-12)
        np.testing.assert_allclose(location, [[.2, .2, 0], [1, 0, 0]], atol=1e-12)

    def test_closed_winding_control(self):
        p = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
        f = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])
        self.assertEqual(v.contains(np.array([[.1, .1, .1], [-1., 0, 0]]), p[f]).tolist(), [True, False])

    def test_noncoplanar_crossing_positive_and_negative(self):
        a = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0]])
        b = np.array([[.2, .2, -1], [.2, .2, 1], [.5, .2, 0]])
        self.assertTrue(v.triangles_cross(a, b))
        self.assertFalse(v.triangles_cross(a, b+[2., 0, 0]))
        self.assertFalse(v.triangles_cross(a, a))

    def test_uv_seam_duplicate_is_true_adjacency(self):
        points = np.array([[0., 0, 0], [1, 0, 0], [0, 1, 0],
                           [0, 0, 0], [.2, .2, -1], [.2, .2, 1]])
        f = np.array([[0, 1, 2], [3, 4, 5]])
        self.assertTrue(v.crossing_pairs(points, f))
        self.assertFalse(v.crossing_pairs(points, f, weld_ids=v.position_weld(points)))

    def test_weld_checks_neighbor_cells(self):
        points = np.array([[.999e-7, 0, 0], [1.001e-7, 0, 0]])
        self.assertEqual(v.position_weld(points).tolist(), [0, 0])

    def test_new_pair_cannot_be_canceled_by_removed_pair(self):
        result = v.mapped_pair_delta([(0, 1)], [(2, 3)], np.arange(4), True)
        self.assertEqual(result["new_source_face_pairs"], [(2, 3)])
        self.assertEqual(result["removed_source_face_pairs"], [(0, 1)])

    def test_self_crossing_subdivision_siblings_are_new(self):
        result = v.mapped_pair_delta([], [(0, 1)], [10, 10], True)
        self.assertEqual(result["new_source_face_pairs"], [(10, 10)])

    def test_nonfinite_position_rejected(self):
        self.reject_health("POSITION", lambda x: x.__setitem__((0, 0), np.nan), "Nonfinite")

    def test_nonunit_normal_rejected(self):
        self.reject_health("NORMAL", lambda x: x.__setitem__(0, [0, 0, 0]), "Nonunit")

    def test_nonfinite_normal_rejected(self):
        self.reject_health("NORMAL", lambda x: x.__setitem__((0, 0), np.inf), "Nonfinite")

    def test_negative_weight_rejected(self):
        self.reject_health("WEIGHTS_0", lambda x: x.__setitem__((0, 0), -.1), "negative skin")

    def test_unnormalized_weight_rejected(self):
        self.reject_health("WEIGHTS_0", lambda x: x.__setitem__(0, [0, 0, 0, 0]), "Unnormalized")

    def test_joint_palette_oob_rejected(self):
        self.reject_health("JOINTS_0", lambda x: x.__setitem__((0, 0), 255), "palette out of bounds")

    def test_nonfinite_IBM_rejected(self):
        document, binary = self.mutate_accessor(self.document["skins"][0]["inverseBindMatrices"],
                                                lambda x: x.__setitem__((0, 0), np.nan))
        with self.assertRaisesRegex(ValueError, "Invalid inverse bind"):
            v.mesh_health(document, binary)

    def test_default_finger_quaternion_immutable(self):
        document = copy.deepcopy(self.document)
        node = next(n for n in document["nodes"] if n.get("name") == "R_Index1")
        node["rotation"][0] += .001
        with self.assertRaisesRegex(ValueError, "Protected JSON changed: nodes"):
            v.exact_rig_and_resources(self.document, self.binary, document, self.binary)

    def test_wrist_translation_immutable(self):
        document = copy.deepcopy(self.document)
        node = next(n for n in document["nodes"] if n.get("name") == "R_Hand")
        node["translation"][0] += .001
        with self.assertRaisesRegex(ValueError, "Protected JSON changed: nodes"):
            v.exact_rig_and_resources(self.document, self.binary, document, self.binary)

    def test_grip_animation_key_payload_immutable(self):
        index = self.document["animations"][0]["samplers"][0]["output"]
        document, binary = self.mutate_accessor(index, lambda x: x.__setitem__((0, 0), x[0, 0]+.001))
        with self.assertRaisesRegex(ValueError, "animation or IBM payload"):
            v.exact_rig_and_resources(self.document, self.binary, document, binary)

    def test_grip_time_payload_immutable(self):
        index = self.document["animations"][0]["samplers"][0]["input"]
        document, binary = self.mutate_accessor(index, lambda x: x.__setitem__((0, 0), .01))
        with self.assertRaisesRegex(ValueError, "animation or IBM payload"):
            v.exact_rig_and_resources(self.document, self.binary, document, binary)

    def test_IBM_payload_immutable(self):
        document, binary = self.mutate_accessor(self.document["skins"][0]["inverseBindMatrices"],
                                                lambda x: x.__setitem__((0, 0), x[0, 0]+.001))
        with self.assertRaisesRegex(ValueError, "animation or IBM payload"):
            v.exact_rig_and_resources(self.document, self.binary, document, binary)

    def test_KTX_payload_immutable(self):
        binary = bytearray(self.binary)
        view = self.document["bufferViews"][self.document["images"][0]["bufferView"]]
        binary[view.get("byteOffset", 0)+100] ^= 1
        with self.assertRaisesRegex(ValueError, "KTX payload changed"):
            v.exact_rig_and_resources(self.document, self.binary, self.document, binary)

    def test_primitive_material_binding_immutable(self):
        document = copy.deepcopy(self.document)
        v.primitive(document)["material"] = 1
        with self.assertRaisesRegex(ValueError, "Primitive material"):
            v.exact_rig_and_resources(self.document, self.binary, document, self.binary)

    def test_existing_UV_cannot_drift_even_inside_ROI(self):
        vertex = next(iter(self.constraints["rois"].values()))["source_vertex_ids"][0]
        document, binary = self.mutate_attribute("TEXCOORD_0", lambda x: x.__setitem__((vertex, 0), x[vertex, 0]+.001))
        self.reject_delta(document, binary, "Existing UV or skin influences changed")

    def test_nonROI_position_cannot_move(self):
        selected = set(sum([r["source_vertex_ids"] for r in self.constraints["rois"].values()], []))
        vertex = next(i for i in range(2741) if i not in selected)
        document, binary = self.mutate_attribute("POSITION", lambda x: x.__setitem__((vertex, 0), x[vertex, 0]+.001))
        self.reject_delta(document, binary, "outside pinned ROI")

    def test_ROI_face_reversed_winding_rejected(self):
        face = next(iter(self.constraints["rois"].values()))["source_face_ids"][0]
        def change(values):
            values[[3*face, 3*face+1]] = values[[3*face+1, 3*face]]
        document, binary = self.mutate_accessor(v.primitive(self.document)["indices"], change)
        self.reject_delta(document, binary, "winding reversed")

    def test_ROI_authored_normal_reversal_rejected(self):
        vertex = next(iter(self.constraints["rois"].values()))["source_vertex_ids"][0]
        document, binary = self.mutate_attribute("NORMAL", lambda x: x.__setitem__(vertex, -x[vertex]))
        self.reject_delta(document, binary, "New normal opposes")

    def test_unapproved_ROI_expansion_rejected(self):
        delta = copy.deepcopy(self.delta)
        next(iter(delta["rois"].values()))["source_vertex_ids"] = [999999]
        self.reject_delta(self.document, self.binary, "Source vertex ROI differs", delta)

    def test_incomplete_topology_mapping_rejected(self):
        delta = copy.deepcopy(self.delta)
        delta["candidate_vertex_to_source"].pop()
        self.reject_delta(self.document, self.binary, "topology mapping size", delta)


if __name__ == "__main__":
    unittest.main()
