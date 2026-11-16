"""Validate this private bank and preserve the existing JVM assertion contract."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
GENERATOR = REPO / 'ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py'
ACTORS = ('base', 'indigo', 'veteran')
DIRECTIONS = ('OVERHEAD', 'LEFT', 'RIGHT')
ORIGINAL_COUNT_ASSERTION = 'assertEquals(if (direction == AttackDirection.OVERHEAD) 211 else 106, profile.samples.size)'
PRIVATE_COUNT_ASSERTION = '''assertEquals(when {
                    asset == "asset://models/opponents/veteran.glb" && direction == AttackDirection.LEFT -> 130
                    direction == AttackDirection.OVERHEAD -> 211
                    else -> 106
                }, profile.samples.size)'''


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_generator():
    spec = importlib.util.spec_from_file_location('combined_bank_generator', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_counts(loaded):
    require(tuple(character['id'] for character, _, _ in loaded) == ACTORS,
            'Expected exactly base, indigo and veteran in the original order')
    result = {}
    for character, profile, _ in loaded:
        actor = character['id']
        require(set(profile['attacks']) == set(DIRECTIONS), 'Attack directions changed: ' + actor)
        result[actor] = {}
        for direction in DIRECTIONS:
            expected = 130 if (actor, direction) == ('veteran', 'LEFT') else 211 if direction == 'OVERHEAD' else 106
            actual = len(profile['attacks'][direction]['samples'])
            require(actual == expected, f'{actor}/{direction} requires {expected} samples, got {actual}')
            result[actor][direction] = actual
    return result


def identities(review):
    require(tuple(row['id'] for row in review['characters']) == ACTORS,
            'Review actor order differs from the original three-actor contract')
    result = [('binding', review['binding_sha256'])]
    for row in review['characters']:
        actor = row['id']
        models = [output['sha256'] for output in row['outputs'] if output['file'] == actor + '.glb']
        require(len(models) == 1, 'Expected one reviewed model identity: ' + actor)
        result += [(actor + '/model', models[0]), (actor + '/profile', row['attack_profiles_sha256'])]
    require(len(result) == 7 and all(re.fullmatch(r'[0-9a-f]{64}', value) for _, value in result),
            'Expected seven exact SHA-256 identities')
    return result


def build_private_fixture(original, formal, candidate):
    before, after = identities(formal), identities(candidate)
    require(len({value for _, value in before}) == 7, 'Original identity literals are not unique')
    content = original
    replacements = []
    for (label, old), (new_label, new) in zip(before, after):
        require(label == new_label, 'Identity order changed')
        require(content.count('"' + old + '"') == 1, 'Published identity fixture differs: ' + label)
        content = content.replace('"' + old + '"', '"' + new + '"')
        replacements.append({'identity': label, 'before': old, 'after': new})
    require(content.count(ORIGINAL_COUNT_ASSERTION) == 1, 'Original exact sample-count assertion changed')
    content = content.replace(ORIGINAL_COUNT_ASSERTION, PRIVATE_COUNT_ASSERTION)
    tests = lambda value: re.findall(r'@Test\s+fun\s+(\w+)\s*\(', value)
    require(tests(content) == tests(original), 'Existing test methods were changed or removed')
    require(content.count('@Test') == original.count('@Test') and '@Ignore' not in content,
            'Existing tests must not be ignored or omitted')
    return content, replacements


def validate_bank(bank, output):
    generator = load_generator()
    review = json.loads((bank / 'production_review_request.json').read_text())
    manifest = json.loads((REPO / 'ArtSource/tripo-warrior/motion_library.json').read_text())
    current_binding = json.loads(json.dumps(generator.production_binding(manifest)))
    require(review['binding'] == current_binding, 'Candidate does not use the current manifest binding')
    require(review['binding_sha256'] == generator.canonical_hash(current_binding),
            'Candidate binding SHA does not match the current manifest')
    counts = sample_counts(generator.load_bank(bank, review))
    require(output.read_text() == generator.generate(bank, review), 'Typed data differs from the complete candidate bank')
    return {
        'binding_sha256': review['binding_sha256'],
        'typed_sha256': sha256(output),
        'typed_source': str(output.relative_to(REPO)),
        'candidate_bank': str(bank.relative_to(REPO)),
        'sample_counts': counts,
        'identities': dict(identities(review)),
        'manifest_binding_matches': True,
        'exact_generated_data_matches': True,
    }


class ValidationTests(unittest.TestCase):
    def review(self, suffix):
        digest = lambda key: hashlib.sha256((key + suffix).encode()).hexdigest()
        return {'binding_sha256': digest('binding'), 'characters': [
            {'id': actor, 'attack_profiles_sha256': digest(actor + '/profile'),
             'outputs': [{'file': actor + '.glb', 'sha256': digest(actor + '/model')}]}
            for actor in ACTORS]}

    def fixture(self, review):
        return '\n'.join(['@Test\nfun originalIdentityAndBehavior() {',
                          *['assertEquals("' + value + '", actual)' for _, value in identities(review)],
                          ORIGINAL_COUNT_ASSERTION, '}'])

    def loaded(self):
        return [({'id': actor}, {'attacks': {
            direction: {'samples': [None] * (130 if (actor, direction) == ('veteran', 'LEFT') else 211 if direction == 'OVERHEAD' else 106)}
            for direction in DIRECTIONS}}, '') for actor in ACTORS]

    def test_exact_identity_and_only_veteran_left_sample_adjustment(self):
        formal, candidate = self.review('formal'), self.review('candidate')
        fixture, changes = build_private_fixture(self.fixture(formal), formal, candidate)
        self.assertEqual(7, len(changes))
        for _, value in identities(candidate):
            self.assertEqual(1, fixture.count(value))
        self.assertIn(PRIVATE_COUNT_ASSERTION, fixture)
        self.assertEqual(130, sample_counts(self.loaded())['veteran']['LEFT'])

    def test_missing_published_identity_is_rejected(self):
        formal = self.review('formal')
        with self.assertRaisesRegex(ValueError, 'Published identity fixture differs'):
            build_private_fixture(self.fixture(formal).replace(formal['binding_sha256'], 'missing'), formal, self.review('candidate'))

    def test_missing_original_count_assertion_is_rejected(self):
        formal = self.review('formal')
        with self.assertRaisesRegex(ValueError, 'exact sample-count assertion changed'):
            build_private_fixture(self.fixture(formal).replace(ORIGINAL_COUNT_ASSERTION, 'assertTrue(profile.samples.isNotEmpty())'), formal, self.review('candidate'))

    def test_other_lateral_sample_growth_is_rejected(self):
        loaded = self.loaded()
        loaded[0][1]['attacks']['LEFT']['samples'].append(None)
        with self.assertRaisesRegex(ValueError, 'base/LEFT requires 106 samples, got 107'):
            sample_counts(loaded)

    def test_overhead_sample_loss_is_rejected(self):
        loaded = self.loaded()
        loaded[2][1]['attacks']['OVERHEAD']['samples'].pop()
        with self.assertRaisesRegex(ValueError, 'veteran/OVERHEAD requires 211 samples, got 210'):
            sample_counts(loaded)

    def test_veteran_left_requires_all_130_samples(self):
        loaded = self.loaded()
        loaded[2][1]['attacks']['LEFT']['samples'].pop()
        with self.assertRaisesRegex(ValueError, 'veteran/LEFT requires 130 samples, got 129'):
            sample_counts(loaded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', type=Path, default=HERE / 'candidate-library')
    parser.add_argument('--output', type=Path, default=HERE / 'typed-validation/AttackBankProfileData.kt')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ValidationTests))
        return 0 if result.wasSuccessful() else 1
    result = validate_bank(args.bank.resolve(), args.output.resolve())
    destination = HERE / 'typed-validation/python-validation.json'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
