"""Fail-closed admission of the canonical prepared tangent producer."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import prepared_tangents as tangents

SOURCE_ROOT = Path(__file__).resolve().parent


class PreparedTangentProduction(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((SOURCE_ROOT / 'motion_library.json').read_text())
        self.config = self.manifest['prepared_tangents']
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_current_manifest_admits_one_pinned_self_contained_tool_closure(self):
        self.assertEqual(tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT), self.config)

    def test_absent_stage_has_no_old_untangented_publication_path(self):
        del self.manifest['prepared_tangents']
        with self.assertRaisesRegex(ValueError, 'requires the reviewed'):
            tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT)

    def test_changed_tool_fails_before_process_execution(self):
        self.config['tools']['mikktspace.mjs']['source_sha256'] = '0' * 64
        with mock.patch.object(tangents.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'tool identity changed'):
                tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT)
            run.assert_not_called()

    def test_orchestration_implementation_is_pinned(self):
        self.config['implementation']['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'orchestration identity changed'):
            tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT)

    def test_truncated_tool_or_license_closure_is_rejected(self):
        del self.config['tools']['licenses/three-MIT.txt']
        with self.assertRaisesRegex(ValueError, 'closure is incomplete'):
            tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT)

    def test_other_repository_cannot_supply_runtime_module(self):
        self.config['tools']['mikktspace.mjs']['source'] = '/Users/yupeng/projects/personal/brickerp/BrickerP.github.io/node_modules/three/examples/jsm/libs/mikktspace.module.js'
        with self.assertRaisesRegex(ValueError, 'escapes the repository'):
            tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT)

    def test_target_cannot_be_silently_omitted_from_bank(self):
        self.manifest['characters'] = [row for row in self.manifest['characters'] if row['id'] != 'veteran']
        with self.assertRaisesRegex(ValueError, 'absent'):
            tangents.validate_prepared_tangents(self.manifest, SOURCE_ROOT)

    def test_non_target_characters_keep_their_existing_data(self):
        for character in ('base', 'indigo'):
            self.assertEqual(tangents.apply_prepared_tangents(character, self.folder / 'unused.glb', self.config, SOURCE_ROOT), {'applied': False})


if __name__ == '__main__':
    unittest.main(verbosity=2)
