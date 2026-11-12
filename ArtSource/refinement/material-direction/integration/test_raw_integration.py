"""Selected raw source, atlas mask and byte-conservation boundary checks only."""
import copy
import io
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

import build_raw_integration as author


def png(values, mode):
    buffer = io.BytesIO()
    image = Image.fromarray(np.asarray(values, dtype=np.uint8))
    assert image.mode == mode
    image.save(buffer, format='PNG')
    return buffer.getvalue()


class RawIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = author.pinned(author.RAW, author.RAW_SHA)
        cls.document, cls.binary = author.raw_document(cls.raw)
        cls.delta = __import__('json').loads(author.pinned(author.DELTA, author.PINS[author.DELTA]))

    def test_prepared_actor_cannot_be_used_as_raw_source(self):
        prepared_document = copy.deepcopy(self.document)
        prepared_document['animations'] = [{'name': 'prepared_idle', 'channels': [], 'samplers': []}]
        prepared = author.codec.write_glb(prepared_document, self.binary)
        with self.assertRaisesRegex(ValueError, 'never a prepared'):
            author.raw_document(prepared)

    def test_actual_rebuild_needs_no_prepared_or_formal_library_files(self):
        read_bytes = Path.read_bytes

        def source_only(path):
            if path.name.endswith('_prepared_png.glb') or 'library' in path.parts:
                raise AssertionError('raw rebuild tried to read a generated/formal file: ' + str(path))
            return read_bytes(path)

        with patch.object(Path, 'read_bytes', source_only):
            author.build()
        self.assertEqual(author.sha((author.HERE / 'base_albedo_tangent_raw.glb').read_bytes()),
                         'a4280be15191970a6271a127bf862adee0ea7b7a93174d1b82c83304e49d52ec')
        self.assertEqual(author.sha((author.HERE / 'candidate_manifest.json').read_bytes()),
                         'a35f40fe7227b45d0376ff9f5b2e52560700aeecf7cd12f01fbe100146cdff0c')

    def test_exact_local_tangent_delta_and_clean_image_view_replacement(self):
        patched, report = author.checked_tangents(self.document, self.binary, self.delta)
        self.assertEqual(report['changed_rows'], 48)
        self.assertEqual(report['actual_changed_bytes'], 380)
        replacement = author.pinned(author.ALBEDO, author.PINS[author.ALBEDO])
        result, packed = author.repack_image(self.document, patched, replacement)
        proof = author.verify_repack(self.document, patched, result, packed, replacement)
        self.assertEqual(proof['appended_orphan_views'], 0)
        self.assertEqual(len(result['bufferViews']), 71)
        self.assertEqual(result.get('animations', []), [])
        self.assertEqual(author.sha(author.payload(self.document, self.binary, 1)), author.BODY_SHA)
        self.assertEqual(author.sha(author.payload(result, packed, 1)), author.PINS[author.ALBEDO])

    def test_tangent_old_row_and_full_stream_mismatch_stop_patch(self):
        broken = copy.deepcopy(self.delta)
        broken['streams'][0]['changes'][0]['old'][0] += .125
        with self.assertRaisesRegex(ValueError, 'old value'):
            author.checked_tangents(self.document, self.binary, broken)
        broken = copy.deepcopy(self.delta)
        broken['streams'][0]['old_stream_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'matching old SHA'):
            author.checked_tangents(self.document, self.binary, broken)

    def test_non_image_view_corruption_is_detected(self):
        replacement = author.pinned(author.ALBEDO, author.PINS[author.ALBEDO])
        result, packed = author.repack_image(self.document, self.binary, replacement)
        view_index = next(i for i in range(len(result['bufferViews'])) if i != result['images'][1]['bufferView'])
        altered = bytearray(packed)
        altered[result['bufferViews'][view_index]['byteOffset']] ^= 1
        with self.assertRaisesRegex(ValueError, 'protected view'):
            author.verify_repack(self.document, self.binary, result, bytes(altered), replacement)

    def test_rgb_mask_boundary_and_alpha_are_enforced(self):
        original = np.zeros((2, 2, 4), dtype=np.uint8)
        original[:, :, 3] = 255
        target = original.copy()
        target[0, 0, 0] = 20
        mask = np.zeros((2, 2), dtype=np.uint8)
        mask[0, 0] = 255
        self.assertEqual(author.check_pixels(png(original, 'RGBA'), png(target, 'RGBA'), png(mask, 'L'))['changed_rgb_pixels'], 1)
        target[1, 1, 1] = 2
        with self.assertRaisesRegex(ValueError, 'outside accepted'):
            author.check_pixels(png(original, 'RGBA'), png(target, 'RGBA'), png(mask, 'L'))
        target = original.copy()
        target[0, 0, 3] = 254
        with self.assertRaisesRegex(ValueError, 'alpha changed'):
            author.check_pixels(png(original, 'RGBA'), png(target, 'RGBA'), png(mask, 'L'))


if __name__ == '__main__':
    unittest.main()
