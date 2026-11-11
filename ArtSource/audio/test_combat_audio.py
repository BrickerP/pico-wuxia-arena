"""Asset acceptance checks: actual PCM, load budget, timing and provenance."""
import hashlib
import json
import struct
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'app/src/main/res/raw'
REVIEW = ROOT / 'ArtSource/refinement/audio'


def read_pcm(path):
    with wave.open(str(path), 'rb') as f:
        metadata = (f.getnchannels(), f.getsampwidth(), f.getframerate())
        samples = struct.unpack(f'<{f.getnframes()}h', f.readframes(f.getnframes()))
    return metadata, samples


class CombatAudioAssetsTest(unittest.TestCase):
    def test_every_runtime_cue_is_short_unclipped_pcm(self):
        files = sorted(RAW.glob('arena_*.wav'))
        self.assertEqual(13, len(files))
        for path in files:
            with self.subTest(cue=path.name):
                fmt, pcm = read_pcm(path)
                self.assertEqual((1, 2, 48000), fmt)
                self.assertLess(len(pcm) * 2, 1_000_000, 'SoundPool truncates decoded sounds above 1 MB')
                self.assertGreater(len(pcm), 0)
                self.assertLess(max(map(abs, pcm)), 32767)
                self.assertGreater(max(map(abs, pcm)), 100)

    def test_contact_transients_arrive_within_25ms_and_fade_without_edge_clicks(self):
        for name in ['hit', 'hard_hit', 'guarded_hit', 'block', 'parry', 'hurt', 'skill', 'execution']:
            with self.subTest(cue=name):
                _, pcm = read_pcm(RAW / f'arena_{name}.wav')
                self.assertGreater(max(map(abs, pcm[:1200])), 327, 'No audible contact in first 25ms')
                self.assertEqual(0, pcm[0])
                self.assertEqual(0, pcm[-1])
                self.assertLess(max(map(abs, pcm[-24:])), 250)

    def test_rain_seam_is_quieter_than_a_normal_waveform_step(self):
        _, pcm = read_pcm(RAW / 'arena_rain.wav')
        self.assertEqual(8 * 48000, len(pcm))
        seam = abs(pcm[-1] - pcm[0])
        largest_step = max(abs(a - b) for a, b in zip(pcm, pcm[1:]))
        self.assertLess(seam, largest_step * 0.5)
        self.assertLess(seam / 32768, 0.02)

    def test_frozen_before_files_and_published_after_files_match_their_hashes(self):
        baseline = json.loads((REVIEW / 'before/baseline.json').read_text())
        for item in baseline['files']:
            self.assertEqual(item['sha256'], hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest())
        manifest = json.loads((REVIEW / 'production_manifest.json').read_text())
        for item in manifest['outputs']:
            self.assertEqual(item['sha256'], hashlib.sha256((RAW / (item['name'] + '.wav')).read_bytes()).hexdigest())
        self.assertEqual(manifest['generator_sha256'], hashlib.sha256((ROOT / 'ArtSource/audio/generate_combat_audio.py').read_bytes()).hexdigest())
        for name, checksum in manifest['source_sha256'].items():
            self.assertEqual(checksum, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_three_first_delivery_cues_are_replaced_with_different_waveforms(self):
        for name in ['hit', 'block', 'parry']:
            before = (REVIEW / f'before/arena_{name}.wav').read_bytes()
            after = (RAW / f'arena_{name}.wav').read_bytes()
            self.assertNotEqual(before, after)

    def test_legal_source_manifest_and_all_four_evidence_pages_exist(self):
        manifest = ROOT / 'ArtSource/audio/sources/sources.json'
        self.assertTrue(manifest.is_file())
        data = manifest.read_text()
        for item in json.loads(data)['sources']:
            self.assertEqual('CC0-1.0', item['license'])
            packages = item.get('packages', [item] if 'package' in item else [])
            for package_item in packages:
                package = manifest.parent / package_item['package']
                self.assertEqual(package_item['package_sha256'], hashlib.sha256(package.read_bytes()).hexdigest())
            for archive in item.get('archives', []):
                self.assertEqual(archive['sha256'], hashlib.sha256((manifest.parent / archive['path']).read_bytes()).hexdigest())
            for media in item['files']:
                self.assertEqual(media['sha256'], hashlib.sha256((manifest.parent / media['path']).read_bytes()).hexdigest())
        for creator in ['Kenney', 'Ylmir', 'StarNinjas', 'HaelDB']:
            self.assertIn(creator.lower(), data.lower())
        for page in ['kenney-impact-sounds-page.txt', 'ylmir-rain-page.txt', 'starninjas-sword-page.txt', 'haeldb-cloth-page.txt']:
            self.assertTrue((manifest.parent / 'licenses' / page).is_file(), page)


if __name__ == '__main__': unittest.main()
