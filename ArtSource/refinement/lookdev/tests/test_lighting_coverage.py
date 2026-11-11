"""Geometry/anchor checks, not an emulation of PICO photometry."""
from pathlib import Path
import itertools
import json
import math
import re
import unittest

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[2]
PROFILE = json.loads((BASE / "lighting_profile.json").read_text())


class LightingCoverageTests(unittest.TestCase):
    def test_all_practicals_match_the_actual_courtyard_anchors(self):
        manifest = json.loads((ROOT / "ArtSource/refinement/environment-hero/candidate_manifest.json").read_text())
        self.assertEqual(PROFILE["environment"]["sha256"], manifest["sha256"])
        for point in PROFILE["points"][:4]:
            actual = manifest["anchors"][point["name"]]["stage_m"]
            for expected, value in zip(actual, point["position"]):
                self.assertAlmostEqual(expected, value, places=6)

    def test_face_corridor_stays_inside_bounce_and_edge_cutoffs(self):
        # 1.1-2.4 m approach, with lateral allowance and both face and hand heights.
        corridor = itertools.product([-.65, 0, .65], [1.0, 1.55, 1.85], [-2.4, -1.75, -1.1])
        points = {p["name"]: p for p in PROFILE["points"]}
        points["face_key"] = PROFILE["spot"]
        for position in corridor:
            for name, maximum_fraction in [("face_key", .75), ("cool_edge", .85), ("blade_fill", .80)]:
                light = points[name]
                distance = math.sqrt(sum((a-b)**2 for a, b in zip(position, light["position"])))
                self.assertLess(distance / light["attenuation_radius_m"], maximum_fraction)

    def test_native_source_and_profile_have_identical_point_values(self):
        source = (ROOT / "app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/SceneLighting.kt").read_text()
        matches = re.findall(r"point\(rig, Vector3\(([^)]+)\), Color4\(([^)]+)\), ([\d.]+)f, ([\d.]+)f\)", source)
        self.assertEqual(len(matches), 6)
        for (position, color, intensity, radius), light in zip(matches, PROFILE["points"]):
            self.assertEqual([float(x.strip().rstrip('f')) for x in position.split(',')], light["position"])
            self.assertEqual([float(x.strip().rstrip('f')) for x in color.split(',')][:3], light["color_linear_rgb"])
            self.assertEqual(float(intensity), light["lumens"])
            self.assertEqual(float(radius), light["attenuation_radius_m"])

    def test_forward_key_stops_before_rear_facade_and_ibl_gain_matches(self):
        key = PROFILE["spot"]
        self.assertGreater(key["position"][2], 0)
        self.assertGreater(key["position"][2] - (-4.7), key["attenuation_radius_m"])
        source = (ROOT / "app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/SceneLighting.kt").read_text()
        exponent = re.search(r"StageEnvironmentLightingComponent\(ImageBasedLightSource.Single\(texture\), ([\d.]+)f\)", source)
        self.assertIsNotNone(exponent)
        self.assertEqual(float(exponent.group(1)), PROFILE["ibl_candidate"]["intensity_exponent"])

    def test_spot_source_axis_and_cone_cover_face_and_hands(self):
        spot = PROFILE["spot"]
        source = (ROOT / "app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/SceneLighting.kt").read_text()
        native = re.search(r"SpotLightComponent\(Color4\(([^)]+)\), ([\d.]+)f, ([\d.]+)f, ([\d.]+)f, ([\d.]+)f, false\)", source)
        self.assertIsNotNone(native)
        rgb = [float(x.strip().rstrip('f')) for x in native.group(1).split(',')][:3]
        self.assertEqual(rgb, spot["color_linear_rgb"])
        self.assertEqual([float(x) for x in native.groups()[1:]],
                         [spot["lumens"], spot["attenuation_radius_m"], spot["inner_angle_degrees"], spot["outer_angle_degrees"]])
        ray = spot["ray_direction"]
        qx, qy, qz, qw = spot["rotation_xyzw"]
        self.assertAlmostEqual(qx*qx+qy*qy+qz*qz+qw*qw, 1, places=6)
        rotated_minus_z = [-2*(qx*qz+qy*qw), -2*(qy*qz-qx*qw), -(1-2*(qx*qx+qy*qy))]
        for expected, actual in zip(ray, rotated_minus_z):
            self.assertAlmostEqual(expected, actual, places=6)
        for position in itertools.product([-.65, 0, .65], [1.0, 1.55, 1.85], [-2.4, -1.75, -1.1]):
            delta = [a-b for a, b in zip(position, spot["position"])]
            distance = math.sqrt(sum(x*x for x in delta))
            angle = math.degrees(math.acos(sum(a*b for a, b in zip(delta, ray))/distance))
            # Public docs do not specify full/half cone angles; use the narrower interpretation.
            self.assertLess(angle, spot["outer_angle_degrees"]/2)


if __name__ == "__main__":
    unittest.main()
