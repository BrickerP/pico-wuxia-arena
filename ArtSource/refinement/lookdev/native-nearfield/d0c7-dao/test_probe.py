"""Independent stdlib-only tests of the one-pointer native dao diagnostic.

No texture decoding or codec calls. Only test_probe.py and tests.json are owned
by this test worker; the explicitly authorized private builder writes its output.
"""
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BUILDER = HERE / 'build_probe.py'
RUNTIME = ROOT / 'app/src/main/assets/models/dao_grip.glb'
SOURCE = ROOT / 'ArtSource/refinement/weapon/stage2/dao_grip_refined.glb'
RUNTIME_SHA = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'
SOURCE_SHA = 'a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637'
CANDIDATE_SHA = '634e7b8aff412e53edff7a6cc73932c3c99a7dd607b3436bcc2ef17edd8a8fa5'
POINTER = '/materials/0/pbrMetallicRoughness/metallicFactor'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def differing_paths(first, second, path=''):
    if type(first) is not type(second):
        return [path]
    if isinstance(first, dict):
        result = []
        for key in sorted(first.keys() | second.keys()):
            child = path + '/' + str(key)
            result.extend([child] if key not in first or key not in second else differing_paths(first[key], second[key], child))
        return result
    if isinstance(first, list):
        if len(first) != len(second):
            return [path]
        return [item for index, (left, right) in enumerate(zip(first, second))
                for item in differing_paths(left, right, path + '/' + str(index))]
    return [] if first == second else [path]


def image_payload(document, binary, index):
    view = document['bufferViews'][document['images'][index]['bufferView']]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


class FactorProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('private_factor_probe_under_test', BUILDER)
        cls.probe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.probe)
        cls.original_bytes = RUNTIME.read_bytes()
        if digest(cls.original_bytes) != RUNTIME_SHA or digest(SOURCE.read_bytes()) != SOURCE_SHA:
            raise ValueError('Actual formal source pin changed')
        cls.original, cls.original_bin = cls.probe.read_glb_bytes(cls.original_bytes)
        cls.candidate_bytes = cls.probe.make_candidate(cls.original_bytes)
        cls.candidate, cls.candidate_bin = cls.probe.read_glb_bytes(cls.candidate_bytes)

    def test_exact_requested_factor_from_actual_absent_default_one(self):
        pbr = self.original['materials'][0]['pbrMetallicRoughness']
        self.assertNotIn('metallicFactor', pbr)
        self.assertEqual(pbr.get('metallicFactor', 1), 1)
        self.assertEqual(self.probe.FACTOR, 217 / 255)
        self.assertEqual(self.candidate['materials'][0]['pbrMetallicRoughness']['metallicFactor'], 217 / 255)
        self.assertNotEqual(217 / 255, .85)
        report = self.probe.verify_runtime_delta(self.original_bytes, self.candidate_bytes)
        self.assertEqual(report['only_JSON_pointer_changed'], POINTER)

    def test_independent_recursive_json_diff_contains_exactly_one_pointer(self):
        self.assertEqual(differing_paths(self.original, self.candidate), [POINTER])

    def test_complete_bin_views_all_eighteen_ktx_and_accessor_records_exact(self):
        self.assertEqual(self.candidate_bin, self.original_bin)
        self.assertEqual(len(self.original_bin), 4312988)
        self.assertEqual(len(self.original['bufferViews']), 77)
        self.assertEqual(self.candidate['bufferViews'], self.original['bufferViews'])
        self.assertEqual(self.candidate['accessors'], self.original['accessors'])
        self.assertEqual(self.candidate['images'], self.original['images'])
        self.assertEqual(len(self.original['images']), 18)
        for index in range(18):
            old = image_payload(self.original, self.original_bin, index)
            self.assertTrue(old.startswith(b'\xabKTX 20\xbb\r\n\x1a\n'))
            self.assertEqual(image_payload(self.candidate, self.candidate_bin, index), old)
        for accessor in self.original['accessors']:
            view = self.original['bufferViews'][accessor['bufferView']]
            start = view.get('byteOffset', 0)
            self.assertEqual(self.candidate_bin[start:start + view['byteLength']], self.original_bin[start:start + view['byteLength']])

    def test_wrong_full_source_sha_rejected_before_candidate_or_verification(self):
        corrupted = bytearray(self.original_bytes)
        corrupted[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            self.probe.make_candidate(bytes(corrupted))
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            self.probe.verify_runtime_delta(bytes(corrupted), self.candidate_bytes)

    def test_wrong_source_material_role_rejected(self):
        document = copy.deepcopy(self.original)
        document['materials'][0]['name'] = 'Grip | worn cord'
        with self.assertRaisesRegex(ValueError, 'material0 role'):
            self.probe.validate_material(document)

    def test_wrong_source_factor_rejected_but_explicit_one_is_effectively_one(self):
        for value in (.85, 217 / 255, 0, float('nan')):
            document = copy.deepcopy(self.original)
            document['materials'][0]['pbrMetallicRoughness']['metallicFactor'] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'effective default1'):
                    self.probe.validate_material(document)
        document = copy.deepcopy(self.original)
        document['materials'][0]['pbrMetallicRoughness']['metallicFactor'] = 1
        self.probe.validate_material(document)

    def test_wrong_source_primitive_or_texture_binding_rejected(self):
        for binding in ('primitive', 'texture'):
            document = copy.deepcopy(self.original)
            if binding == 'primitive':
                document['meshes'][0]['primitives'][0]['material'] = 1
            else:
                document['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']['index'] = 0
            with self.assertRaisesRegex(ValueError, 'binding'):
                self.probe.validate_material(document)

    def test_wrong_candidate_factor_or_missing_delta_rejected(self):
        for value in (.85, 0.7, 1, None):
            document = copy.deepcopy(self.candidate)
            if value is None:
                del document['materials'][0]['pbrMetallicRoughness']['metallicFactor']
            else:
                document['materials'][0]['pbrMetallicRoughness']['metallicFactor'] = value
            with self.assertRaisesRegex(ValueError, 'Unexpected JSON delta'):
                self.probe.verify_runtime_delta(self.original_bytes, self.probe.write_glb(document, self.candidate_bin))

    def test_roughness_albedo_other_material_and_geometry_json_tampering_rejected(self):
        for mutation in ('roughness', 'albedo', 'other_material', 'geometry', 'sampler', 'anchor'):
            document = copy.deepcopy(self.candidate)
            if mutation == 'roughness':
                document['materials'][0]['pbrMetallicRoughness']['roughnessFactor'] = .42
            elif mutation == 'albedo':
                document['materials'][0]['pbrMetallicRoughness']['baseColorFactor'] = [.9, .8, .7, 1]
            elif mutation == 'other_material':
                document['materials'][1]['pbrMetallicRoughness']['metallicFactor'] = .7
            elif mutation == 'geometry':
                document['meshes'][0]['primitives'][0]['attributes']['POSITION'] = 99999
            elif mutation == 'sampler':
                document['samplers'][0]['wrapS'] = 33071
            else:
                document['nodes'][0]['translation'] = [.01, 0, 0]
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(ValueError, 'Unexpected JSON delta'):
                    self.probe.verify_runtime_delta(self.original_bytes, self.probe.write_glb(document, self.candidate_bin))

    def test_bin_payload_corruption_rejected(self):
        changed = bytearray(self.candidate_bin)
        changed[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'BIN changed'):
            self.probe.verify_runtime_delta(self.original_bytes, self.probe.write_glb(self.candidate, bytes(changed)))

    def test_view_or_image_metadata_changes_rejected(self):
        for mutation in ('view', 'image'):
            document = copy.deepcopy(self.candidate)
            if mutation == 'view':
                document['bufferViews'][0]['byteLength'] -= 1
            else:
                document['images'][0]['bufferView'] = document['images'][1]['bufferView']
            with self.assertRaisesRegex(ValueError, 'Unexpected JSON delta'):
                self.probe.verify_runtime_delta(self.original_bytes, self.probe.write_glb(document, self.candidate_bin))

    def test_glb_truncation_bad_magic_and_chunk_length_rejected(self):
        for cut in (1, 8, 100, len(self.original_bytes) - 10):
            with self.assertRaises(ValueError):
                self.probe.read_glb_bytes(self.original_bytes[:-cut])
        for offset, value in ((0, 0), (12, len(self.original_bytes))):
            changed = bytearray(self.original_bytes)
            struct.pack_into('<I', changed, offset, value)
            with self.assertRaises(ValueError):
                self.probe.read_glb_bytes(changed)

    def test_actual_private_artifact_is_the_pinned_verified_candidate(self):
        delivered = (HERE / 'dao_grip_forged_factor217_runtime.glb').read_bytes()
        self.assertEqual(digest(delivered), CANDIDATE_SHA)
        self.assertEqual(delivered, self.candidate_bytes)
        self.assertEqual(len(delivered), 4332248)
        self.probe.verify_runtime_delta(self.original_bytes, delivered)

    def test_two_private_builds_deterministic_without_any_codec_subprocess(self):
        hashes = []
        with mock.patch('subprocess.run', side_effect=AssertionError('Codec/process call forbidden')), mock.patch('subprocess.Popen', side_effect=AssertionError('Codec/process call forbidden')):
            for _ in range(2):
                with contextlib.redirect_stdout(io.StringIO()):
                    report = self.probe.build()
                self.assertEqual(report['status'], 'PRIVATE_DIAGNOSTIC_JSON_FACTOR_ONLY')
                self.assertEqual(report['codec_invocations'], 0)
                hashes.append(digest((HERE / 'dao_grip_forged_factor217_runtime.glb').read_bytes()))
        self.assertEqual(hashes, [CANDIDATE_SHA, CANDIDATE_SHA])
        self.assertEqual(digest(RUNTIME.read_bytes()), RUNTIME_SHA)
        self.assertEqual(digest(SOURCE.read_bytes()), SOURCE_SHA)
        self.__class__.deterministic_hashes = hashes


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FactorProbeTests))
    report = {'status': 'PASS' if result.wasSuccessful() else 'FAIL', 'schema': 'one-JSON-factor-only-tests',
              'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped),
              'test_source_sha256': digest(Path(__file__).read_bytes()), 'builder_sha256': digest(BUILDER.read_bytes()),
              'two_rebuild_hashes': getattr(FactorProbeTests, 'deterministic_hashes', None), 'codec_invocations': 0,
              'candidate_quantization_status': 'NO_REENCODING_ALL18_KTX_BIT_IDENTICAL',
              'limits': 'PASS proves the exact one-pointer JSON diagnostic, immutable encoded data and deterministic no-codec builds. Native appearance remains untested.'}
    (HERE / 'tests.json').write_text(json.dumps(report, indent=2) + '\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
