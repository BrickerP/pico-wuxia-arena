"""Reuse all frozen28 controls, plus current-source substitution rejection."""
import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_left as a


class CurrentSourceControls(unittest.TestCase):
    def test_old_a980_Right_cannot_supply_new_Left(self):
        with self.assertRaisesRegex(ValueError, "Only the current199c Right"):
            a.certify_source(a.joint.SOURCE)

    def test_old_d8_Left_rejected(self):
        verifier, right, rb, _, _, _, _ = a.inputs()
        old, oldb = a.v.h.read(a.LEGACY/"left_hand_rebuilt.glb")
        with self.assertRaises(ValueError):
            verifier.verify_contract(right, rb, old, oldb)

    def test_old_anatomical_ecc_Left_rejected(self):
        verifier, right, rb, _, _, _, _ = a.inputs()
        old_path = a.GRIP/"palm-wrist-surface/production-patch/anatomical-crease/left-derivation/left_hand_anatomical.glb"
        old, oldb = a.v.h.read(old_path)
        with self.assertRaises(ValueError):
            verifier.verify_contract(right, rb, old, oldb)

    def test_old_Right_certification_cannot_authorize_199c(self):
        review = copy.deepcopy(json.loads((a.JOINT/"verification.json").read_text()))
        review["candidate_sha256"] = a.joint.SOURCE_SHA
        with self.assertRaisesRegex(ValueError, "Current199c Right full certification"):
            a.certify_source(review=review)

    def test_reference_barycentric_orientation_matches_actual_mirror(self):
        delta = json.loads((a.JOINT/"joint_delta.json").read_text())
        right, rb = a.v.h.read(a.joint.SOURCE)
        reference, refb = a.v.h.read(a.REFERENCE)
        rows = a.reflected_reference_rows(delta, reference, refb)
        original = next(row for row in delta["candidate_added_vertices"]
                        if abs(row["barycentric"][1]-row["barycentric"][2]) > .1)
        reflected = rows[original["candidate_vertex_id"]]
        rp = a.v.attributes(right, rb)["POSITION"]
        lp = a.v.attributes(reference, refb)["POSITION"]
        expected = np.asarray(original["barycentric"])@rp[original["source_vertex_ids"]]*[-1., 1., 1.]
        actual = np.asarray(reflected["barycentric"])@lp[reflected["source_vertex_ids"]]
        np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)


def make_suite():
    a.legacy()
    frozen = a.load("left_joint_frozen_tests", a.LEGACY/"test_verify_left_rebuild.py")
    suite = unittest.defaultTestLoader.loadTestsFromModule(frozen)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(CurrentSourceControls))
    return suite


if __name__ == "__main__":
    a.run_tests()
