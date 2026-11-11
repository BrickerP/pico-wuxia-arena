import copy
import io
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
import json

from PIL import Image
import compress_pbr as p
import measure_quality

ROOT = Path(__file__).resolve().parent
ENCODER = ROOT / "tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx"


def fixture(mode="RGB", image=None, wraps=None):
    image = image if image is not None else Image.new(mode, (4, 4), (130, 170, 220, 70) if mode == "RGBA" else (130, 170, 220))
    png = io.BytesIO()
    image.save(png, format="PNG")
    geometry = struct.pack("<3f", 0.0, 1.0, 2.0)
    pixels = png.getvalue()
    binary = geometry + pixels
    doc = {
        "asset": {"version": "2.0", "generator": "private-test"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [{"buffer": 0, "byteLength": len(geometry)},
                        {"buffer": 0, "byteOffset": len(geometry), "byteLength": len(pixels)}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 1, "type": "VEC3"}],
        "images": [{"name": "test", "mimeType": "image/png", "bufferView": 1}],
        "textures": [{"source": 0}],
        "materials": [{"pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        "nodes": [{"mesh": 0, "skin": 0, "translation": [1, 2, 3],
                   "extras": {"anchor": "hand", "matrix_pin": [1, 2, 3, 4]}}],
        "skins": [{"joints": [0], "inverseBindMatrices": 0}],
        "animations": [{"name": "contract", "samplers": [{"input": 0, "output": 0, "interpolation": "STEP"}],
                        "channels": [{"sampler": 0, "target": {"node": 0, "path": "translation"}}]}],
        "scene": 0, "scenes": [{"nodes": [0]}],
    }
    if wraps is not None:
        doc["samplers"] = [{"wrapS": wraps[0], "wrapT": wraps[1]}]
        doc["textures"][0]["sampler"] = 0
    return p.write_glb(doc, binary)


class Contracts(unittest.TestCase):
    def setUp(self):
        self.doc, self.binary = p.load_glb(fixture())

    def test_source_dimensions_mode_and_default_wrap(self):
        self.assertEqual(p.image_contracts(self.doc), [{"roles": ["baseColor"], "domain": "srgb", "wrap_s": "wrap", "wrap_t": "wrap"}])

    def test_wrong_sha_fails_before_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, output = Path(tmp) / "in.glb", Path(tmp) / "out.glb"
            source.write_bytes(fixture())
            with self.assertRaisesRegex(ValueError, "SHA256"):
                p.build(source, "0" * 64, output, Path("missing-encoder"), Path(tmp) / "cache")
            self.assertFalse(output.exists())

    def test_mixed_srgb_linear_image_rejected(self):
        self.doc["materials"][0]["normalTexture"] = {"index": 0}
        with self.assertRaisesRegex(ValueError, "mixed color"):
            p.image_contracts(self.doc)

    def test_unclassified_image_rejected(self):
        self.doc["images"].append(copy.deepcopy(self.doc["images"][0]))
        with self.assertRaisesRegex(ValueError, "no classified role"):
            p.image_contracts(self.doc)

    def test_unknown_material_extension_rejected(self):
        self.doc["materials"][0]["extensions"] = {"new_feature": {"map": {"index": 0}}}
        with self.assertRaisesRegex(ValueError, "material extension"):
            p.image_contracts(self.doc)

    def test_conflicting_sampler_wraps_rejected(self):
        self.doc["textures"].append({"source": 0, "sampler": 0})
        self.doc["samplers"] = [{"wrapS": 33071, "wrapT": 33071}]
        self.doc["materials"][0]["emissiveTexture"] = {"index": 1}
        with self.assertRaisesRegex(ValueError, "mixed sampler wraps"):
            p.image_contracts(self.doc)

    def test_different_axis_wrap_classified_without_changing_sampler(self):
        self.doc["textures"][0]["sampler"] = 0
        self.doc["samplers"] = [{"wrapS": 33071}]
        self.assertEqual(p.image_contracts(self.doc)[0]["wrap_s"], "clamp")
        self.assertEqual(p.image_contracts(self.doc)[0]["wrap_t"], "wrap")
        self.assertEqual(self.doc["samplers"], [{"wrapS": 33071}])

    def test_unknown_axis_wrap_rejected(self):
        self.doc["textures"][0]["sampler"] = 0
        self.doc["samplers"] = [{"wrapS": 12345}]
        with self.assertRaisesRegex(ValueError, "unsupported sampler wrap"):
            p.image_contracts(self.doc)

    def test_mirrored_repeat_explicitly_rejected_on_either_axis(self):
        self.doc["textures"][0]["sampler"] = 0
        for sw, tw in ((33648, 10497), (10497, 33648), (33648, 33648)):
            self.doc["samplers"] = [{"wrapS": sw, "wrapT": tw}]
            with self.subTest(sw=sw, tw=tw), self.assertRaisesRegex(ValueError, "only REPEAT and CLAMP_TO_EDGE"):
                p.image_contracts(self.doc)

    def test_image_accessor_overlap_rejected(self):
        self.doc["accessors"][0]["bufferView"] = 1
        with self.assertRaisesRegex(ValueError, "also used by accessor"):
            p.image_contracts(self.doc)

    def test_truncated_glb_rejected(self):
        with self.assertRaisesRegex(ValueError, "header"):
            p.load_glb(fixture()[:-1])

    def test_out_of_bounds_view_rejected(self):
        self.doc["bufferViews"][0]["byteLength"] = len(self.binary) + 1
        with self.assertRaisesRegex(ValueError, "bufferView"):
            p.load_glb(p.write_glb(self.doc, self.binary))


class AxisMips(unittest.TestCase):
    def test_legal_rectangle_and_non_power_of_two_mip_sizes(self):
        self.assertEqual(p.mip_sizes((12, 4)), [(12, 4), (6, 2), (3, 1), (1, 1)])
        sizes = p.mip_sizes((1024, 256))
        self.assertEqual(len(sizes), 11)
        self.assertEqual(sizes[-4:], [(8, 2), (4, 1), (2, 1), (1, 1)])
        image = Image.new("RGB", (12, 4), (10, 40, 90))
        self.assertEqual([i.size for i in p.axis_mips(image, "linear", "wrap", "clamp")], p.mip_sizes(image.size))

    def test_top_level_pixels_and_dimensions_are_exact(self):
        image = Image.new("RGBA", (12, 8))
        image.putdata([(x * 19 % 256, x * 43 % 256, x * 7 % 256, x * 71 % 256) for x in range(96)])
        levels = p.axis_mips(image, "srgb", "wrap", "clamp")
        self.assertEqual(levels[0].size, image.size)
        self.assertEqual(levels[0].mode, image.mode)
        self.assertEqual(levels[0].tobytes(), image.tobytes())

    def test_srgb_linear_light_average_and_linear_alpha(self):
        image = Image.new("RGBA", (8, 4))
        image.putdata([(255 if x % 2 else 0,) * 3 + (200 if x % 2 else 100,) for y in range(4) for x in range(8)])
        color = p.axis_mips(image, "srgb", "wrap", "clamp")
        data = p.axis_mips(image, "linear", "wrap", "clamp")
        # IEC sRGB encoding of linear .5 is 187.516...; raw byte .5 is 127.5.
        for level in color[1:]:
            self.assertEqual(set(level.getdata()), {(188, 188, 188, 150)})
        for level in data[1:]:
            self.assertEqual(set(level.getdata()), {(128, 128, 128, 150)})

    def test_wrong_mip_inputs_rejected(self):
        for size in ((0, 4), (-4, 4), (4.0, 4)):
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "dimensions"):
                p.mip_sizes(size)
        with self.assertRaisesRegex(ValueError, "mode/domain"):
            p.axis_mips(Image.new("RGB", (4, 4)), "unknown", "wrap", "clamp")
        with self.assertRaisesRegex(ValueError, "wrap"):
            p.axis_mips(Image.new("RGB", (4, 4)), "linear", "unknown", "clamp")

    def test_each_axis_matches_independent_official_cli_boundary_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def official(image, wrap, label):
                source, ktx, decoded = root / (label + ".png"), root / (label + ".ktx2"), root / (label + "-mip.png")
                image.save(source)
                p.run([ENCODER, "create", "--format", "R8G8B8_UNORM", "--assign-tf", "linear",
                       "--assign-primaries", "none", "--generate-mipmap", "--mipmap-filter", "lanczos4",
                       "--mipmap-wrap", wrap, source, ktx])
                p.run([ENCODER, "extract", "--level", "1", ktx, decoded])
                with Image.open(decoded) as result:
                    return result.convert("RGB")

            column = Image.new("RGB", (16, 16))
            column.putdata([(255 if x == 0 else 0, 0, 0) for y in range(16) for x in range(16)])
            row = Image.new("RGB", (16, 16))
            row.putdata([(0, 255 if y == 0 else 0, 0) for y in range(16) for x in range(16)])
            combined = Image.merge("RGB", (column.getchannel("R"), row.getchannel("G"), Image.new("L", (16, 16), 80)))
            for sw, tw in (("wrap", "clamp"), ("clamp", "wrap")):
                with self.subTest(sw=sw, tw=tw):
                    s_reference = official(column, sw, "s-" + sw).getchannel("R")
                    t_reference = official(row, tw, "t-" + tw).getchannel("G")
                    actual = p.axis_mips(combined, "linear", sw, tw)[1]
                    for band, reference in ((actual.getchannel("R"), s_reference), (actual.getchannel("G"), t_reference)):
                        self.assertLessEqual(max(abs(a - b) for a, b in zip(band.getdata(), reference.getdata())), 1)
            periodic = official(column, "wrap", "periodic")
            clamped = official(column, "clamp", "clamped")
            self.assertGreater(max(abs(a[0] - b[0]) for a, b in zip(periodic.getdata(), clamped.getdata())), 10)

    def test_explicit_mips_reach_real_uastc_with_preserved_glb_and_gamma(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = Image.new("RGBA", (8, 4))
            image.putdata([(255 if x % 2 else 0,) * 3 + (200 if x % 2 else 100,) for y in range(4) for x in range(8)])
            raw = fixture(image=image, wraps=(10497, 33071))
            source, output = root / "in.glb", root / "out.glb"
            source.write_bytes(raw)
            report = p.build(source, p.sha(raw), output, ENCODER, root / "cache")
            proof = p.verify_preserved(raw, output.read_bytes())
            self.assertTrue(proof["non_image_json_semantics_identical"])
            record = report["images"][0]
            self.assertEqual(record["mip_provenance"]["source"], "explicit-axis-lanczos4-v1")
            self.assertEqual(record["mip_provenance"]["generator_sha256"], p.sha(Path(p.__file__).read_bytes()))
            self.assertEqual([r["size"] for r in record["mip_inputs"]], [[8, 4], [4, 2], [2, 1], [1, 1]])
            self.assertEqual(record["mip_inputs"][0]["pixels_sha256"], p.sha(image.tobytes()))
            self.assertIn("--levels", record["command_template"])
            self.assertNotIn("--generate-mipmap", record["command_template"])
            self.assertNotIn("--normal-mode", record["command_template"])
            doc, binary = p.load_glb(output.read_bytes())
            ktx = root / "out.ktx2"
            ktx.write_bytes(p.view_bytes(doc, binary, doc["images"][0]["bufferView"]))
            for level, size in enumerate(p.mip_sizes(image.size)):
                decoded = root / f"read-{level}.png"
                p.run([ENCODER, "extract", "--transcode", "rgba8", "--level", str(level), ktx, decoded])
                with Image.open(decoded) as actual:
                    self.assertEqual(actual.size, size)
                    expected = image if level == 0 else Image.new("RGBA", size, (188, 188, 188, 150))
                    self.assertLessEqual(max(abs(a - b) for actual_pixel, expected_pixel in zip(actual.convert("RGBA").getdata(), expected.getdata()) for a, b in zip(actual_pixel, expected_pixel)), 5)


class RealEncoder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / "source.glb"
        cls.raw = fixture()
        cls.source.write_bytes(cls.raw)
        cls.output = cls.root / "candidate.glb"
        cls.report = p.build(cls.source, p.sha(cls.raw), cls.output, ENCODER, cls.root / "cache")
        cls.candidate = cls.output.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def mutate(self, change):
        doc, binary = p.load_glb(self.candidate)
        change(doc)
        return p.write_glb(doc, binary)

    def test_happy_path_all_nonimage_semantics_and_bin(self):
        proof = p.verify_preserved(self.raw, self.candidate)
        self.assertTrue(proof["non_image_json_semantics_identical"])
        self.assertEqual(proof["non_image_bufferViews_byte_identical"], 1)
        self.assertEqual(proof["images"][0]["levels"], 3)
        self.assertEqual(proof["images"][0]["dfd_transfer"], 2)

    def test_cache_is_byte_reproducible(self):
        other = self.root / "other.glb"
        p.build(self.source, p.sha(self.raw), other, ENCODER, self.root / "cache")
        self.assertEqual(other.read_bytes(), self.candidate)

    def test_corrupted_cache_rejected(self):
        damaged_cache = self.root / "damaged-cache"
        shutil.copytree(self.root / "cache", damaged_cache)
        cached = next(damaged_cache.glob("*.ktx2"))
        data = bytearray(cached.read_bytes())
        data[-1] ^= 1
        cached.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "cache integrity"):
            p.build(self.source, p.sha(self.raw), self.root / "damaged-out.glb", ENCODER, damaged_cache)

    def test_geometry_buffer_mutation_detected(self):
        doc, binary = p.load_glb(self.candidate)
        damaged = bytearray(binary)
        damaged[0] ^= 1
        with self.assertRaisesRegex(ValueError, "BIN bufferView"):
            p.verify_preserved(self.raw, p.write_glb(doc, bytes(damaged)))

    def test_measurement_happy_path(self):
        import json
        output = self.root / "quality.json"
        measure_quality.measure(self.source, p.sha(self.raw), self.output, p.sha(self.candidate), ENCODER, output)
        report = json.loads(output.read_text())
        self.assertEqual(report["candidate_sha256"], p.sha(self.candidate))
        self.assertEqual([c["channel"] for c in report["images"][0]["channels"]], list("RGB"))

    def test_measurement_wrong_identity_and_overwrite_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            measure_quality.measure(self.source, "0" * 64, self.output, p.sha(self.candidate), ENCODER, self.root / "bad-quality.json")
        with self.assertRaisesRegex(ValueError, "new file"):
            measure_quality.measure(self.source, p.sha(self.raw), self.output, p.sha(self.candidate), ENCODER, self.source)

    def test_rest_skin_animation_anchor_mutations_detected(self):
        edits = [lambda d: d["nodes"][0]["translation"].__setitem__(0, 4),
                 lambda d: d["skins"][0]["joints"].append(1),
                 lambda d: d["animations"][0]["samplers"][0].__setitem__("interpolation", "LINEAR"),
                 lambda d: d["nodes"][0]["extras"].__setitem__("anchor", "broken"),
                 lambda d: d["accessors"][0].__setitem__("count", 2)]
        for change in edits:
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "semantics"):
                p.verify_preserved(self.raw, self.mutate(change))

    def test_fallback_source_detected(self):
        with self.assertRaisesRegex(ValueError, "fallback"):
            p.verify_preserved(self.raw, self.mutate(lambda d: d["textures"][0].__setitem__("source", 0)))

    def test_missing_required_extension_detected(self):
        with self.assertRaisesRegex(ValueError, "extensionsRequired"):
            p.verify_preserved(self.raw, self.mutate(lambda d: d.pop("extensionsRequired")))

    def test_normal_linear_xyz_and_alpha_channels(self):
        for mode, domain in (("RGB", "linear"), ("RGBA", "srgb")):
            with self.subTest(mode=mode):
                raw = fixture(mode)
                doc, binary = p.load_glb(raw)
                if domain == "linear":
                    doc["materials"] = [{"normalTexture": {"index": 0}}]
                    raw = p.write_glb(doc, binary)
                source, output = self.root / (mode + ".glb"), self.root / (mode + "-out.glb")
                source.write_bytes(raw)
                report = p.build(source, p.sha(raw), output, ENCODER, self.root / "cache")
                self.assertEqual(report["images"][0]["source_mode"], mode)
                self.assertEqual(report["images"][0]["domain"], domain)
                self.assertNotIn("--normal-mode", report["images"][0]["command_template"])
                self.assertNotIn("--input-swizzle", report["images"][0]["command_template"])
                self.assertEqual(report["images"][0]["ktx2"]["dfd_primaries"], 0 if domain == "linear" else 1)
                candidate_doc, candidate_bin = p.load_glb(output.read_bytes())
                encoded = self.root / (mode + ".ktx2")
                encoded.write_bytes(p.view_bytes(candidate_doc, candidate_bin, candidate_doc["images"][0]["bufferView"]))
                decoded = self.root / (mode + "-decoded.png")
                p.run([ENCODER, "extract", "--transcode", "rgba8", "--level", "0", encoded, decoded])
                with Image.open(decoded) as decoded_image:
                    actual = decoded_image.convert("RGBA").getpixel((0, 0))
                expected = (130, 170, 220, 70 if mode == "RGBA" else 255)
                self.assertTrue(all(abs(a - b) <= 5 for a, b in zip(actual, expected)), (actual, expected))

    def test_wrong_dfd_and_missing_mips_rejected(self):
        doc, binary = p.load_glb(self.candidate)
        ktx = p.view_bytes(doc, binary, doc["images"][0]["bufferView"])
        bad = bytearray(ktx)
        dfd = struct.unpack_from("<I", bad, 48)[0]
        bad[dfd + 13] = 0
        with self.assertRaisesRegex(ValueError, "color metadata"):
            p.check_ktx(bytes(bad), "srgb", (4, 4))
        bad = bytearray(ktx)
        struct.pack_into("<I", bad, 40, 1)
        with self.assertRaisesRegex(ValueError, "full mip"):
            p.check_ktx(bytes(bad), "srgb", (4, 4))


if __name__ == "__main__":
    unittest.main()
