"""Source and real-cmgen KTX checks; no PICO runtime compatibility claim."""
import json
import math
import struct
import unittest

import generate_ibl as source


class RainNightIblTests(unittest.TestCase):
    def test_all_source_texels_positive_finite_and_hdr(self):
        minimum, maximum = math.inf, 0
        for y in range(source.HEIGHT):
            for x in range(source.WIDTH):
                rgb = source.sample(x, y)
                self.assertTrue(all(math.isfinite(value) and value > 0 for value in rgb))
                minimum, maximum = min(minimum, *rgb), max(maximum, *rgb)
        self.assertGreater(minimum, 0)
        self.assertGreater(maximum, 4)

    def test_light_patches_face_authored_lantern_and_moon(self):
        for light in source.LIGHTS:
            self.assertAlmostEqual(sum(value * value for value in light["direction"]), 1, places=12)
            forward = source.sample_direction(light["direction"])
            opposite = source.sample_direction(tuple(-v for v in light["direction"]))
            self.assertGreater(sum(forward), sum(opposite) * 2)
        self.assertEqual(source.sample_direction((0, -1, 0)), list(source.LOWER))

    def test_rgbe_source_decodes_as_512x256_positive_hdr(self):
        payload = (source.HERE / "rain_night_latlong.hdr").read_bytes()
        marker = b"-Y 256 +X 512\n"
        position = payload.index(marker) + len(marker)
        maximum, minimum = 0, math.inf
        for row in range(256):
            self.assertEqual(payload[position:position + 4], bytes((2, 2, 2, 0)))
            position += 4
            channels = []
            for channel in range(4):
                values = bytearray()
                while len(values) < 512:
                    count = payload[position]
                    position += 1
                    self.assertGreater(count, 0)
                    self.assertLessEqual(count, 128)
                    values.extend(payload[position:position + count])
                    position += count
                self.assertEqual(len(values), 512)
                channels.append(values)
            for x in range(512):
                exponent = channels[3][x]
                self.assertGreater(exponent, 0)
                rgb = [math.ldexp(channels[c][x], exponent - 128 - 8) for c in range(3)]
                self.assertTrue(all(math.isfinite(value) and value > 0 for value in rgb))
                maximum, minimum = max(maximum, *rgb), min(minimum, *rgb)
        self.assertEqual(position, len(payload))
        # Allow the specified four-unit warm peaks to quantize into RGBE.
        self.assertGreater(maximum, 3.9)
        self.assertGreater(minimum, 0)

    def test_real_prefilter_has_six_faces_four_mips_and_27_sh_values(self):
        validator = source.load_module("ktx_test_validator", source.VALIDATOR)
        report = validator.validate_bytes((source.HERE / "candidate_standard_header.ktx").read_bytes())
        self.assertTrue(report["valid"])
        self.assertEqual(report["cubemap_faces"], 6)
        self.assertEqual([level["width"] for level in report["levels"]], [128, 64, 32, 16])
        self.assertTrue(report["all_stored_texels_finite"])
        self.assertEqual(len(report["spherical_harmonics_metadata"][0]["numeric_values"]), 27)

    def test_raw_is_preserved_and_candidate_changes_only_three_header_fields(self):
        raw = (source.HERE / "generated/generated_ibl.ktx").read_bytes()
        candidate = (source.HERE / "candidate_standard_header.ktx").read_bytes()
        actual, report = source.canonicalize(raw)
        self.assertEqual(actual, candidate)
        self.assertEqual(raw[64:], candidate[64:])
        self.assertEqual(set(report["changed_byte_offsets"]), {16, 20, 32, 33})
        validator = source.load_module("raw_test_validator", source.VALIDATOR)
        with self.assertRaises(ValueError):
            validator.validate_bytes(raw)
        self.assertFalse(validator.validate_bytes(raw, inspect=True)["valid"])

    def test_truncated_and_nonfinite_ktx_are_rejected(self):
        validator = source.load_module("bad_test_validator", source.VALIDATOR)
        candidate = (source.HERE / "candidate_standard_header.ktx").read_bytes()
        for cut in (1, 100, len(candidate) - 10):
            with self.assertRaises(ValueError):
                validator.validate_bytes(candidate[:-cut])
        bad = bytearray(candidate)
        metadata_bytes = struct.unpack_from("<I", bad, 60)[0]
        first_face = 64 + metadata_bytes + 4
        struct.pack_into("<I", bad, first_face, 0xFFFFFFFF)
        with self.assertRaises(ValueError):
            validator.validate_bytes(bad)

    def test_manifest_tool_and_payload_hashes_match_existing_files(self):
        generation = json.loads((source.HERE / "generation_manifest.json").read_text())
        self.assertEqual(generation["exit_code"], 0)
        self.assertEqual(generation["tool_binary_sha256_checked"], source.digest(source.CMGEN.read_bytes()))
        for entry in generation["output_files"]:
            self.assertEqual(entry["sha256"], source.digest((source.HERE / entry["path"]).read_bytes()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
