"""Geometry/serialization contract tests; these do not prove PICO appearance."""
import collections
import json
import math
from pathlib import Path
import struct
import unittest

import generate_weather as weather


class WeatherTests(unittest.TestCase):
    def test_rain_is_reproducible_and_alpha_tapered_with_clear_combat_lane(self):
        first = weather.rain_tile()
        self.assertEqual(first, weather.rain_tile())
        positions, colors, triangles, drops = first
        self.assertEqual(len(drops), 36)
        self.assertTrue(all(0 <= point[1] <= 2 for point in positions))
        self.assertTrue(all(-1 <= point[0] <= 1 and -2 <= point[2] <= 2 for point in positions))
        for start in range(0, len(colors), 4):
            self.assertEqual(colors[start][3], 0)
            self.assertEqual(colors[start + 3][3], 0)
            self.assertTrue(.25 <= colors[start + 1][3] <= .45)
        for center_x in (-2.7, 2.7):
            self.assertTrue(all(abs(center_x + point[0]) >= 1.6 for point in positions))
        self.assertTrue(all(.08 <= drop["length_m"] <= .15 and .004 <= drop["width_m"] <= .008 for drop in drops))

    def test_haze_has_soft_borders_and_clear_center(self):
        positions, colors, triangles = weather.side_haze()
        self.assertAlmostEqual(max(color[3] for color in colors), .12)
        for point, color in zip(positions, colors):
            if abs(point[0]) == 1.5 or point[1] == 0 or point[1] == .7:
                self.assertAlmostEqual(color[3], 0, places=12)
        self.assertTrue(all(abs(center + point[0]) >= 1.5 for center in (-3, 3) for point in positions))

    def test_sky_is_closed_inward_and_at_thirty_metres(self):
        positions, colors, triangles = weather.night_sky()
        edges = collections.Counter()
        for point in positions:
            self.assertAlmostEqual(math.sqrt(sum(v * v for v in point)), 30, places=9)
        for a, b, c in triangles:
            pa, pb, pc = positions[a], positions[b], positions[c]
            u, v = [pb[i] - pa[i] for i in range(3)], [pc[i] - pa[i] for i in range(3)]
            normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            self.assertLess(sum(normal[i] * pa[i] for i in range(3)), 0)
            for edge in ((a, b), (b, c), (c, a)):
                edges[tuple(sorted(edge))] += 1
        self.assertTrue(all(count == 2 for count in edges.values()))
        self.assertTrue(all(color[3] == 1 for color in colors))

    def test_assets_round_trip_with_required_unlit_and_finite_vertex_colors(self):
        for name, geometry, blend in (("RainTile", weather.rain_tile()[:3], True), ("SideHaze", weather.side_haze(), True), ("NightSky", weather.night_sky(), False)):
            with self.subTest(mesh=name):
                payload = weather.mesh_glb(name, *geometry, blend=blend)
                document, decoded = weather.inspect(payload)
                self.assertEqual(document["nodes"][1]["name"], name)
                self.assertTrue(document["materials"][0]["doubleSided"])
                self.assertEqual(document["materials"][0]["alphaMode"], "BLEND" if blend else "OPAQUE")
                self.assertEqual(document["extensionsRequired"], ["KHR_materials_unlit"])
                self.assertEqual(len(decoded[0]), len(geometry[0]))
                for key, operation in (("min", min), ("max", max)):
                    self.assertEqual(document["accessors"][0][key], [operation(point[axis] for point in decoded[0]) for axis in range(3)])

    def test_truncated_glb_is_rejected(self):
        payload = weather.mesh_glb("RainTile", *weather.rain_tile()[:3], blend=True)
        for missing in (1, 8, 100, len(payload) - 10):
            with self.assertRaises(ValueError):
                weather.inspect(payload[:-missing])

    def test_invalid_geometry_is_rejected(self):
        for positions, colors, triangles in (([], [], []), ([(float("nan"), 0, 0)], [(1, 1, 1, 1)], [(0, 0, 0)]),
                                              ([(0, 0, 0)], [(1, 1, 1, 1)], [(0, 1, 0)]),
                                              ([(0, 0, 0)], [(1, 1, 1, 2)], [(0, 0, 0)])):
            with self.assertRaises(ValueError):
                weather.mesh_glb("Invalid", positions, colors, triangles, blend=True)

    def test_serialized_accessor_overrun_is_rejected(self):
        payload = weather.mesh_glb("SideHaze", *weather.side_haze(), blend=True)
        document, binary = weather.decode_glb(payload)
        document["accessors"][0]["count"] += 1
        with self.assertRaises(ValueError):
            weather.inspect(weather.encode_glb(document, binary))


if __name__ == "__main__":
    unittest.main(verbosity=2)
