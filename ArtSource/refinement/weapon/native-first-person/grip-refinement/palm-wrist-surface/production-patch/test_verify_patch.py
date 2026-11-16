"""Actual-source positive controls plus targeted contract failure injections."""
import copy
import unittest

import numpy as np
import verify_patch as p


class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc, cls.binary = p.v.h.read(p.SOURCE)
        cls.attributes = p.v.attributes(cls.doc, cls.binary)
        cls.faces = p.v.faces(cls.doc, cls.binary)
        cls.n = len(cls.attributes["POSITION"])
        cls.delta = {"source_vertex_count": cls.n, "source_face_count": len(cls.faces),
                     "candidate_vertex_to_source": list(range(cls.n)),
                     "candidate_face_to_source": list(range(len(cls.faces))),
                     "candidate_added_vertices": [], "modified_source_vertices": [],
                     "protected_source_vertices": list(range(cls.n)), "ROI_faces": [], "normal_split_vertices": []}

    def candidate(self, attributes=None, faces=None):
        doc, binary = copy.deepcopy(self.doc), bytearray(self.binary)
        primitive = p.v.primitive(doc)
        for name, values in (self.attributes if attributes is None else attributes).items():
            old = self.doc["accessors"][primitive["attributes"][name]]
            binary.extend(b"\0" * (-len(binary) % 4))
            offset = len(binary)
            binary.extend(np.asarray(values).tobytes())
            view = len(doc["bufferViews"])
            doc["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(binary) - offset})
            accessor = len(doc["accessors"])
            row = {"bufferView": view, "componentType": old["componentType"], "type": old["type"], "count": len(values)}
            if "normalized" in old:
                row["normalized"] = old["normalized"]
            doc["accessors"].append(row)
            primitive["attributes"][name] = accessor
        triangles = self.faces if faces is None else faces
        indices = triangles.astype(np.uint16).ravel()
        binary.extend(b"\0" * (-len(binary) % 4))
        offset = len(binary)
        binary.extend(indices.tobytes())
        view = len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer": 0, "byteOffset": offset, "byteLength": len(binary) - offset})
        primitive["indices"] = len(doc["accessors"])
        doc["accessors"].append({"bufferView": view, "componentType": 5123, "type": "SCALAR", "count": len(indices)})
        doc["buffers"][0]["byteLength"] = len(binary)
        return doc, bytes(binary)

    def test_actual_identity_passes_all_four_posed_geometric_checks(self):
        result = p.verify(self.doc, self.binary, self.doc, self.binary, self.delta)
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["poses"]), 4)
        self.assertEqual(result["poses"]["1.0"]["new_bad_normal_corners"], [])

    def test_a_legal_per_corner_duplicate_does_not_create_a_welded_crack(self):
        attrs = {name: np.vstack((rows, rows[self.faces[0, 0]])) for name, rows in self.attributes.items()}
        face = self.faces.copy()
        source_vertex = int(face[0, 0])
        face[0, 0] = self.n
        doc, binary = self.candidate(attrs, face)
        delta = copy.deepcopy(self.delta)
        delta["candidate_vertex_to_source"].append(source_vertex)
        delta["normal_split_vertices"] = [self.n]
        result = p.verify(self.doc, self.binary, doc, binary, delta)
        self.assertTrue(result["passed"])
        self.assertEqual(result["poses"]["0.5"]["split_position_max_error_m"], 0.0)

    def test_missing_protected_finger_is_rejected(self):
        regions = p.v.skin_regions(self.doc, self.binary)
        finger = int(np.flatnonzero(sum(regions["digit_weights"].values()) > .5)[0])
        delta = copy.deepcopy(self.delta)
        delta["protected_source_vertices"].remove(finger)
        delta["modified_source_vertices"] = [finger]
        with self.assertRaisesRegex(ValueError, "anatomical authorization"):
            p.mapping(self.doc, self.binary, self.doc, self.binary, delta)

    def test_low_digit_spill_does_not_reclassify_the_palm_as_a_finger(self):
        delta = copy.deepcopy(self.delta)
        vertex = 33  # actual source: 93.6% R_Hand, 6.4% Thumb spill
        delta["protected_source_vertices"].remove(vertex)
        delta["modified_source_vertices"] = [vertex]
        delta["ROI_faces"] = np.flatnonzero((self.faces == vertex).any(axis=1)).tolist()
        p.mapping(self.doc, self.binary, self.doc, self.binary, delta)

    def test_inserted_source_barycentric_point_can_have_legal_normal_splits(self):
        original = 33  # palm-dominated vertex with a real multi-face fan
        incident = np.flatnonzero((self.faces == original).any(axis=1))
        first, adjacent = map(int, incident[:2])
        attrs = {name: np.vstack((rows, rows[original], rows[original])) for name, rows in self.attributes.items()}
        face = self.faces.copy()
        first_corner = int(np.flatnonzero(face[first] == original)[0])
        face[first, first_corner] = self.n
        face[adjacent, np.flatnonzero(face[adjacent] == original)[0]] = self.n + 1
        doc, binary = self.candidate(attrs, face)
        delta = copy.deepcopy(self.delta)
        delta["candidate_vertex_to_source"] += [-1, -1]
        delta["ROI_faces"] = [first, adjacent]
        delta["normal_split_vertices"] = [self.n, self.n + 1]
        delta["candidate_added_vertices"] = [
            {"candidate_vertex_id": vertex, "source_face_id": first,
             "source_vertex_ids": self.faces[first].tolist(),
             "barycentric": [float(i == first_corner) for i in range(3)]}
            for vertex in [self.n, self.n + 1]]
        self.assertTrue(p.verify(self.doc, self.binary, doc, binary, delta)["passed"])

    def test_a_bone_default_or_texture_payload_cannot_change(self):
        doc = copy.deepcopy(self.doc)
        doc["nodes"][0]["name"] += "changed"
        with self.assertRaisesRegex(ValueError, "Protected JSON changed"):
            p.verify(self.doc, self.binary, doc, self.binary, self.delta)
        binary = bytearray(self.binary)
        view = self.doc["bufferViews"][self.doc["images"][0]["bufferView"]]
        binary[view.get("byteOffset", 0) + 100] ^= 1
        with self.assertRaisesRegex(ValueError, "KTX payload changed"):
            p.verify(self.doc, self.binary, self.doc, binary, self.delta)

    def test_invalid_source_mapping_does_not_use_numpy_negative_wraparound(self):
        delta = copy.deepcopy(self.delta)
        delta["candidate_face_to_source"][0] = -1
        with self.assertRaisesRegex(ValueError, "face mapping bounds"):
            p.mapping(self.doc, self.binary, self.doc, self.binary, delta)

    def test_out_of_bounds_actual_indices_are_rejected(self):
        face = self.faces.copy()
        face[0, 0] = self.n + 5
        doc, binary = self.candidate(faces=face)
        with self.assertRaisesRegex(ValueError, "Face index out of bounds"):
            p.verify(self.doc, self.binary, doc, binary, self.delta)

    def test_negative_weights_are_rejected_before_posed_sampling(self):
        attrs = {name: rows.copy() for name, rows in self.attributes.items()}
        attrs["WEIGHTS_0"][0, 0] = -.2
        doc, binary = self.candidate(attrs)
        with self.assertRaisesRegex(ValueError, "negative skin"):
            p.verify(self.doc, self.binary, doc, binary, self.delta)

    def test_new_normal_reversal_is_not_inherited_from_another_bad_corner(self):
        attrs = {name: rows.copy() for name, rows in self.attributes.items()}
        vertex = 33
        attrs["NORMAL"][vertex] *= -1
        doc, binary = self.candidate(attrs)
        delta = copy.deepcopy(self.delta)
        delta["protected_source_vertices"].remove(vertex)
        delta["modified_source_vertices"] = [vertex]
        delta["ROI_faces"] = np.flatnonzero((self.faces == vertex).any(axis=1)).tolist()
        with self.assertRaisesRegex(ValueError, "New posed normal opposes"):
            p.verify(self.doc, self.binary, doc, binary, delta)

    def test_mixed_MCP_proximal_dorsal_skin_can_receive_palm_weights(self):
        vertex = 546
        attrs = {name: rows.copy() for name, rows in self.attributes.items()}
        names = [self.doc["nodes"][i]["name"] for i in self.doc["skins"][0]["joints"]]
        attrs["JOINTS_0"][vertex] = [names.index("R_Hand"), 0, 0, 0]
        attrs["WEIGHTS_0"][vertex] = [1., 0., 0., 0.]
        doc, binary = self.candidate(attrs)
        delta = copy.deepcopy(self.delta)
        delta["protected_source_vertices"].remove(vertex)
        delta["modified_source_vertices"] = [vertex]
        delta["ROI_faces"] = np.flatnonzero((self.faces == vertex).any(axis=1)).tolist()
        delta["anatomical_metacarpal_vertices"] = [vertex]
        p.mapping(self.doc, self.binary, doc, binary, delta)
        proof = p.anatomical_authorization(self.doc, self.binary, delta)[2]
        self.assertGreater(proof["declared_vertex_evidence"]["546"]["MCP_proximal_margin_m"], .003)

    def test_false_distal_finger_declaration_cannot_override_source_anatomy(self):
        delta = copy.deepcopy(self.delta)
        delta["protected_source_vertices"].remove(11)
        delta["modified_source_vertices"] = [11]
        delta["ROI_faces"] = np.flatnonzero((self.faces == 11).any(axis=1)).tolist()
        delta["anatomical_metacarpal_vertices"] = [11]
        delta["source_open_anatomical_m"] = [0., .07, -.02]  # untrusted builder claim
        with self.assertRaisesRegex(ValueError, "actual source dorsal/MCP domain"):
            p.mapping(self.doc, self.binary, self.doc, self.binary, delta)

    def test_inner_palm_and_source_one_ring_are_independent_requirements(self):
        domain = p.anatomical_metacarpal_domain(self.doc, self.binary)
        core = p.v.skin_regions(self.doc, self.binary)
        digit = np.flatnonzero(sum(core["digit_weights"].values()) > .5)
        vertex = next(int(i) for i in digit if domain["local"][i, 2] >= -.01)
        delta = copy.deepcopy(self.delta)
        delta["anatomical_metacarpal_vertices"] = [vertex]
        with self.assertRaisesRegex(ValueError, "actual source dorsal/MCP domain"):
            p.anatomical_authorization(self.doc, self.binary, delta)
        lateral = domain["evidence"][836]
        self.assertTrue(lateral["eligible"])
        self.assertGreater(lateral["MCP_proximal_margin_m"], .003)
        valid = domain["local"][546].copy()
        self.assertTrue(domain["point_evidence"](valid, True)["eligible"])
        self.assertFalse(domain["point_evidence"](valid, False)["eligible"])
        inner = valid.copy()
        inner[2] = 0.0
        self.assertFalse(domain["point_evidence"](inner, True)["eligible"])

    def test_reversed_geometry_cannot_be_hidden_by_flipping_normals(self):
        face = self.faces.copy()
        selected = int(np.flatnonzero((self.faces == 33).any(axis=1))[0])
        face[selected, [0, 1]] = face[selected, [1, 0]]
        doc, binary = self.candidate(faces=face)
        delta = copy.deepcopy(self.delta)
        delta["ROI_faces"] = [selected]
        with self.assertRaisesRegex(ValueError, "geometry inverted"):
            p.verify(self.doc, self.binary, doc, binary, delta)

    def test_missing_inserted_correspondence_is_rejected(self):
        delta = copy.deepcopy(self.delta)
        delta["candidate_vertex_to_source"][0] = -1
        with self.assertRaisesRegex(ValueError, "Source vertex missing"):
            p.mapping(self.doc, self.binary, self.doc, self.binary, delta)


if __name__ == "__main__":
    unittest.main()
