import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

import fit_grip_pose as producer
import verify_hands as hand

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "grip-refinement/left-rebuild"))
import verify_left_rebuild as surface

PACKAGED = HERE.parents[3] / "app/src/main/assets/models/player_hands"
ASSETS = (
    ("right", "R", producer.SOURCES / "right_hand_joint.glb"),
    ("left", "L", producer.SOURCES / "left-derivation/left_hand_joint.glb"),
)


def crossings(doc, binary, time):
    actual = surface.hand_geometry(doc, binary, time)
    faces = actual["faces"]
    triangles = actual["points"][faces]
    weld = hand.weld_positions(actual["bind"])[1]
    return surface.crossing_pairs(triangles, triangles, True, faces, weld)


class HandPoseTest(unittest.TestCase):
    def test_equipped_and_relaxed_skin_do_not_cross(self):
        for name, _, src in ASSETS:
            previous = hand.read(src)
            self.assertTrue(crossings(*previous, 1))
            doc, binary = hand.read(PACKAGED / (name + "_hand.glb"))
            default = hand.sampled_worlds(doc, binary)
            closed = hand.sampled_worlds(doc, binary, "grip", 1.)
            for mesh in doc["meshes"]:
                for primitive in mesh["primitives"]:
                    np.testing.assert_allclose(hand.skin(doc, binary, primitive, default),
                                               hand.skin(doc, binary, primitive, closed), atol=1e-6, rtol=0)
            for time in (0., 1.):
                with self.subTest(name=name, time=time):
                    self.assertEqual([], crossings(doc, binary, time))

    def test_both_grips_clear_the_actual_handle_core(self):
        core = surface.actual_dao_components()["Handle core"]
        triangles = core["points"][core["faces"]]
        for name, _, _ in ASSETS:
            geometry = surface.hand_geometry(*hand.read(PACKAGED / (name + "_hand.glb")), 1.)
            self.assertEqual([], surface.crossing_pairs(geometry["points"][geometry["faces"]], triangles))
            self.assertEqual(0, surface.solid_distances(geometry["points"], triangles, True)["inside_samples"])

    def test_relaxation_and_opposition_are_mirrored(self):
        mirror = np.array([-1., 1., 1.])
        right = {}
        for name, side, src in ASSETS:
            doc, binary = hand.read(PACKAGED / (name + "_hand.glb"))
            original = hand.read(src)
            digit_names = ["Thumb", "Index", "Mid", "Ring", "Pinky"]
            tips = [producer.tip_vertices(*original, side + "_" + digit) for digit in digit_names]
            for time in (0., .5, 1.):
                geometry = surface.hand_geometry(doc, binary, time)
                posed = geometry["points"]
                if side == "R":
                    right[time] = posed
                else:
                    np.testing.assert_allclose(posed, right[time] * mirror, atol=1e-6, rtol=0)
                if time == 1.:
                    tip_centres = [posed[indices].mean(axis=0) for indices in tips]
                    self.assertLess(np.linalg.norm(tip_centres[0] - tip_centres[1]), .035)
                if time == 0.:
                    worlds = hand.sampled_worlds(doc, binary, "grip", time)
                    nodes = {item["name"]: i for i, item in enumerate(doc["nodes"])}
                    for digit, limit in zip(digit_names[1:], (18, 21, 25, 25)):
                        positions = [worlds[nodes[f"{side}_{digit}{j}"]][:3, 3] for j in (1, 2, 3)]
                        first, second = (producer.unit(x) for x in np.diff(positions, axis=0))
                        self.assertGreater(np.degrees(np.arccos(np.clip(first @ second, -1, 1))), limit)

    def test_packaged_assets_are_reproducible_and_preserve_the_original_skin(self):
        with tempfile.TemporaryDirectory() as scratch:
            for name, side, src in ASSETS:
                out = Path(scratch) / "hand.glb"
                producer.build(src, out, side)
                self.assertEqual(hand.digest(out), hand.digest(PACKAGED / (name + "_hand.glb")))
                before, old_bytes = hand.read(src)
                after, new_bytes = hand.read(out)
                for field in ("scenes", "meshes", "skins", "materials", "images", "animations"):
                    self.assertEqual(before[field], after[field])
                outputs = {s["output"] for s in before["animations"][0]["samplers"]}
                for i in range(len(before["accessors"])):
                    if i not in outputs:
                        np.testing.assert_array_equal(hand.values(before, old_bytes, i), hand.values(after, new_bytes, i))
                for i in range(len(before["images"])):
                    self.assertEqual(hand.image_bytes(before, old_bytes, i), hand.image_bytes(after, new_bytes, i))


if __name__ == "__main__":
    unittest.main()
