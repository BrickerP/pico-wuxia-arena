"""Real-file composition and rejection checks; never changes formal inputs."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('clearance_inputs', HERE / 'prepare_candidate.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class CandidateInputsTest(unittest.TestCase):
    def test_one_RIGHT_replacement_and_protected_formal_fields(self):
        docs, receipt = p.build()
        manifest = json.loads(docs['motion_library_candidate.json'])
        formal = json.loads((p.PRODUCER / 'motion_library.json').read_bytes())
        expected = copy.deepcopy(formal)
        expected.pop('production_review')
        source = next(c for c in expected['attack_source']['clips'] if c['direction'] == 'RIGHT')
        source.update(p.prepare.producer_entry(p.REPO, receipt['raw']['file'],p.RAW_SHA))
        expected['attack_source']['authoring_manifest'] = manifest['attack_source']['authoring_manifest']
        self.assertEqual(manifest,expected)
        self.assertEqual(manifest['attack_source']['authoring_manifest']['source_sha256'],p.prepare.digest(docs['attack_bank_inputs.json']))
        self.assertFalse(receipt['left_integrated'])

    def test_sealed_handoff_tampering_is_rejected(self):
        original = p.prepare.identity
        def changed(repo,relative):
            record = original(repo,relative)
            if Path(relative).resolve() == p.HANDOFF.resolve():
                record['sha256'] = '0'*64
            return record
        with patch.object(p.prepare,'identity',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'handoff identity differs'):
                p.build()

    def test_candidate_RAW_tampering_is_rejected(self):
        original = p.prepare.check_record
        def changed(repo,record,expected_path=None):
            result = original(repo,record,expected_path)
            if record['sha256'] == p.RAW_SHA:
                result['sha256'] = '0'*64
            return result
        with patch.object(p.prepare,'check_record',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'RAW identity differs'):
                p.build()

    def test_current_contract_accepts_private_bank_and_rejects_forged_binding(self):
        spec = importlib.util.spec_from_file_location('existing_typed_generator',p.REPO / 'ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py')
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        bank = HERE / 'candidate-library'
        request = json.loads((bank / 'production_review_request.json').read_bytes())
        self.assertEqual(len(generator.load_bank(bank,request)),3)
        forged = copy.deepcopy(request)
        forged['binding_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'binding identity differs'):
            generator.load_bank(bank,forged)
        with self.assertRaisesRegex(ValueError,'approved_for_development_integration'):
            generator.validate_app_publication(HERE / 'motion_library_candidate.json',request)


if __name__ == '__main__':
    unittest.main()
