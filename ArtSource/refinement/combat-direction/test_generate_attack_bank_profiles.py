import json
import unittest
from unittest.mock import patch

import generate_attack_bank_profiles as generator


PUBLISHED_BINDING = '7373f5937cd19d1306b861ca0e1654e040977eafb3af6685618742e3e0716cff'
PUBLISHED_MODELS = {
    'base': 'e7f3de3d8c7e202999b2d456ae85257b89a01e7c21792f332c4b273c77b60cbc',
    'indigo': '448d46394743018aff3165e0e49e5c07480b617664c072c14ab6ae186cc87ef3',
    'veteran': '0c0b57a4f3684a25603a6875b2fd9188096755dc4b3688d921a7de8776f1e9c2',
}


class GenerateAttackBankProfilesTest(unittest.TestCase):
    def test_formal_library_identity_exactly_regenerates_runtime_data(self):
        self.assertEqual(generator.REPO / 'ArtSource/tripo-warrior/library', generator.DEFAULT_BANK)
        review = json.loads((generator.DEFAULT_BANK / 'production_review_request.json').read_text())
        self.assertEqual(PUBLISHED_BINDING, review['binding_sha256'])
        self.assertEqual(generator.generate(generator.DEFAULT_BANK), generator.DEFAULT_OUTPUT.read_text())
        data = generator.load_bank(generator.DEFAULT_BANK)
        self.assertEqual(len(data), 3)
        self.assertEqual(PUBLISHED_MODELS, {c['id']: profile['model_sha256'] for c, profile, _ in data})
        self.assertEqual(sum(len(p['attacks'][d]['samples']) for _, p, _ in data for d in generator.DIRECTIONS), 954)

    def test_profile_identity_drift_is_rejected_before_export(self):
        with patch.object(generator, 'sha256', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'Profile SHA differs'):
                generator.load_bank(generator.DEFAULT_BANK)

    def test_model_identity_drift_is_rejected_before_export(self):
        actual_sha256 = generator.sha256
        with patch.object(generator, 'sha256', side_effect=lambda path: '0' * 64 if path.suffix == '.glb' else actual_sha256(path)):
            with self.assertRaisesRegex(ValueError, 'Prepared model identity differs'):
                generator.load_bank(generator.DEFAULT_BANK)


if __name__ == '__main__':
    unittest.main()
