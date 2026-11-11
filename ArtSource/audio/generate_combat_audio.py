"""Rebuild CC0 foley composites and their frozen-baseline A/B reels (no synth oscillators).

Run in the sole arena repository. ffmpeg only decodes licensed source audio; all
mixing, filters, envelopes and measurements use Python's standard library.
"""
import hashlib
import json
import math
import struct
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

SAMPLE_RATE = 48000
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'app/src/main/res/raw'
REVIEW = ROOT / 'ArtSource/refinement/audio'
SOURCES = ROOT / 'ArtSource/audio/sources'
KENNEY = SOURCES / 'kenney-impact-sounds/Audio'
BEFORE = REVIEW / 'before'
# These ten recordings are the complete build input, not the downloaded packs.
SOURCE_FILES = (
    'kenney-impact-sounds/Audio/impactPunch_heavy_001.ogg',
    'kenney-impact-sounds/Audio/impactPlate_medium_001.ogg',
    'kenney-impact-sounds/Audio/impactPlate_heavy_000.ogg',
    'kenney-impact-sounds/Audio/footstep_concrete_003.ogg',
    'starninjas-sword/clashes/sword_clash.2.ogg',
    'starninjas-sword/clashes/sword_clash.5.ogg',
    'starninjas-sword/attacks/sword - StarNinjas/sword.4.ogg',
    'haeldb-cloth/footsteps/step_cloth1.ogg',
    'haeldb-cloth/footsteps/step_cloth2.ogg',
    'ylmir-rain/1.ogg',
)
OUTCOME_CUES = ('arena_victory', 'arena_defeat')
COMPARISON_CUES = ('hit', 'block', 'parry', 'hard_hit', 'guarded_hit', 'whoosh', 'execution')


def blank(seconds):
    return [0.0] * round(seconds * SAMPLE_RATE)


@lru_cache(maxsize=None)
def decode(path):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path),
                                   '-ac', '1', '-ar', str(SAMPLE_RATE), '-f', 's16le', '-'])
    return [x / 32768 for x in struct.unpack(f'<{len(raw) // 2}h', raw)]


def rate_shift(samples, rate):
    if rate == 1: return list(samples)
    size = max(1, int(len(samples) / rate))
    result = []
    for i in range(size):
        pos = i * rate
        lower = min(int(pos), len(samples) - 1)
        upper = min(lower + 1, len(samples) - 1)
        result.append(samples[lower] * (1 - (pos - lower)) + samples[upper] * (pos - lower))
    return result


def filtered(samples, low=55, high=12000):
    """One-pole low/high cut keeps mic rumble and brittle highs below the contact."""
    a = 1 - math.exp(-math.tau * low / SAMPLE_RATE)
    b = 1 - math.exp(-math.tau * high / SAMPLE_RATE)
    lo = hi = 0.0
    out = []
    for x in samples:
        lo += a * (x - lo)
        hi += b * (x - hi)
        out.append(hi - lo)
    return out


def trim_onset(samples):
    peak = max(map(abs, samples), default=0)
    threshold = max(0.002, peak * 0.025)
    start = next((i for i, x in enumerate(samples) if abs(x) >= threshold), 0)
    return samples[max(0, start - 24):]


def recorded(path, rate=1, low=55, high=12000):
    samples = filtered(rate_shift(trim_onset(decode(path)), rate), low, high)
    peak = max(map(abs, samples), default=0)
    if peak < 0.001: raise ValueError(f'Empty/silent foley source: {path}')
    return [x * 0.7 / peak for x in samples]


def source(name, rate=1, low=55, high=12000):
    return recorded(KENNEY / name, rate, low, high)


def add(destination, samples, gain=1, delay=0):
    offset = round(delay * SAMPLE_RATE)
    for i, x in enumerate(samples[:max(0, len(destination) - offset)]):
        destination[i + offset] += x * gain


def master(samples, peak=0.48, rms_limit=0.16, loop=False):
    mean = sum(samples) / len(samples)
    samples = [x - mean for x in samples]
    if not loop:
        for i in range(len(samples)):
            samples[i] *= min(1, i / 24, (len(samples) - 1 - i) / 720)
    top = max(map(abs, samples), default=0)
    rms = math.sqrt(sum(x * x for x in samples) / len(samples))
    gain = min(peak / max(top, 1e-9), rms_limit / max(rms, 1e-9))
    return [x * gain for x in samples]


def write_pcm(path, samples):
    pcm = struct.pack(f'<{len(samples)}h', *(round(max(-1, min(1, x)) * 32767) for x in samples))
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE); f.writeframes(pcm)


def compose(duration, *layers):
    result = blank(duration)
    for samples, gain, delay in layers: add(result, samples, gain, delay)
    return result


def rain_loop():
    rain = filtered(decode(SOURCES / 'ylmir-rain/1.ogg'), 180, 8200)
    # Split one continuous 16s take into two 8s halves. Equal-power crossfade
    # makes both boundaries the same point in the field recording.
    length = 8 * SAMPLE_RATE
    first = rain[5 * SAMPLE_RATE:13 * SAMPLE_RATE]
    second = rain[13 * SAMPLE_RATE:21 * SAMPLE_RATE]
    return [a * math.sin(math.pi * i / (2 * (length - 1))) +
            b * math.cos(math.pi * i / (2 * (length - 1)))
            for i, (a, b) in enumerate(zip(first, second))]


def build_material():
    punch = source('impactPunch_heavy_001.ogg', 0.87, 55, 4500)
    cloth = recorded(SOURCES / 'haeldb-cloth/footsteps/step_cloth2.ogg', 1.08, 300, 7500)
    metal = recorded(SOURCES / 'starninjas-sword/clashes/sword_clash.2.ogg', 0.93, 180, 11000)
    plate = source('impactPlate_medium_001.ogg', 1.08, 550, 12000)
    bright = recorded(SOURCES / 'starninjas-sword/clashes/sword_clash.5.ogg', 1.08, 1200, 14000)
    soft = compose(0.38, (punch, 0.85, 0), (cloth, 0.50, 0.012))
    hard = compose(0.56, (metal, 0.85, 0), (plate, 0.26, 0.008))
    block = compose(0.62, (metal, 0.80, 0), (source('impactPlate_heavy_000.ogg', 0.92), 0.36, 0.021))
    parry = compose(0.80, (bright, 1.0, 0), (plate, 0.42, 0.007), (punch, 0.13, 0))
    guarded = compose(0.42, (recorded(SOURCES / 'haeldb-cloth/footsteps/step_cloth1.ogg', 0.9, 90, 3300), 0.8, 0),
                      (metal, 0.22, 0.006))
    hurt = compose(0.36, (punch, 0.95, 0), (cloth, 0.37, 0.021))
    skill = compose(0.70, (block, 0.8, 0), (bright, 0.38, 0.038), (cloth, 0.40, 0.08))
    execution = compose(0.88, (rate_shift(punch, 0.74), 0.82, 0), (cloth, 0.65, 0.055),
                        (rate_shift(cloth, 0.80), 0.32, 0.14))
    swish = recorded(SOURCES / 'starninjas-sword/attacks/sword - StarNinjas/sword.4.ogg', 1.25, 650, 10500)
    whoosh = compose(0.28, (swish, 0.85, 0))
    rain = rain_loop()
    water = decode(SOURCES / 'ylmir-rain/1.ogg')[6 * SAMPLE_RATE:6 * SAMPLE_RATE + round(0.20 * SAMPLE_RATE)]
    water = filtered(water, 1700, 8500)
    for i in range(len(water)): water[i] *= math.exp(-i / (0.035 * SAMPLE_RATE))
    step = compose(0.32, (source('footstep_concrete_003.ogg', 0.95, 70, 9000), 0.8, 0), (water, 0.9, 0.015))
    return {'arena_hit': soft, 'arena_hard_hit': hard, 'arena_guarded_hit': guarded,
            'arena_block': block, 'arena_parry': parry, 'arena_hurt': hurt,
            'arena_skill': skill, 'arena_execution': execution, 'arena_whoosh': whoosh,
            'arena_step': step, 'arena_rain': rain}


def measure(path):
    with wave.open(str(path), 'rb') as f:
        assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (1, 2, SAMPLE_RATE)
        pcm = struct.unpack(f'<{f.getnframes()}h', f.readframes(f.getnframes()))
    samples = [x / 32768 for x in pcm]
    peak = max(map(abs, samples)); rms = math.sqrt(sum(x*x for x in samples)/len(samples))
    return {'name': path.stem, 'seconds': len(samples) / SAMPLE_RATE, 'sample_rate': SAMPLE_RATE,
            'channels': 1, 'bits': 16, 'peak_dbfs': 20*math.log10(peak),
            'rms_dbfs': 20*math.log10(rms), 'clipped_samples': sum(abs(x) >= 32767 for x in pcm),
            'decoded_bytes': len(pcm)*2, 'max_sample_step': max(abs(a-b) for a,b in zip(samples,samples[1:])),
            'edge_step': abs(samples[-1]-samples[0]), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def comparison_reel(name, labels):
    result = []; cue_sheet = []
    for label, path, rate, gain in labels:
        result.extend(blank(0.4))
        samples = rate_shift(decode(path), rate)
        cue_sheet.append({'label': label, 'start_seconds': len(result)/SAMPLE_RATE,
                          'duration_seconds': len(samples)/SAMPLE_RATE, 'rate': rate, 'gain': gain})
        result.extend(x * gain for x in samples)
        result.extend(blank(0.45))
    write_pcm(REVIEW / f'{name}.wav', result)
    (REVIEW / f'{name}.json').write_text(json.dumps(cue_sheet, indent=2)+'\n')
    return len(result)/SAMPLE_RATE


def production_manifest(metrics):
    """Describe the current generator and exact inputs without rewriting audio."""
    source_files = {str((SOURCES / name).relative_to(ROOT)):
                    hashlib.sha256((SOURCES / name).read_bytes()).hexdigest()
                    for name in sorted(SOURCE_FILES)}
    return {
        'baseline_git_head': json.loads((BEFORE/'baseline.json').read_text())['git_head'],
        'generator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_sha256': source_files, 'outputs': metrics,
        'runtime': {'pending_limit':24,'short_voices':10,'ambience_voices':1,'freshness_ms':120,
                    'contact_gain_range':[0.34,0.72],'rain_gain':0.10,'ducked_rain_gain':0.045,
                    'priority':{'rain':0,'step_and_swing':1,'result':2,'material':3,'block_and_hurt':4,
                                'parry_and_skill':5,'execution':6}},
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True); REVIEW.mkdir(parents=True, exist_ok=True)
    cues = build_material()
    for name, samples in cues.items():
        samples = master(samples, 0.24 if name == 'arena_rain' else 0.48,
                         0.065 if name == 'arena_rain' else 0.16, loop=name == 'arena_rain')
        write_pcm(OUTPUT / f'{name}.wav', samples)
    # Outcome cues remain the frozen original composition, independent of combat foley.
    for name in OUTCOME_CUES:
        (OUTPUT / f'{name}.wav').write_bytes((BEFORE / f'{name}.wav').read_bytes())
    metrics = [measure(OUTPUT / f'{name}.wav') for name in sorted((*cues, *OUTCOME_CUES))]
    (REVIEW/'audio_measurements.json').write_text(json.dumps(metrics,indent=2)+'\n')
    comparisons = []
    for name in COMPARISON_CUES:
        comparisons += [(f'before_{name}', BEFORE / f'arena_{name}.wav', 1, 0.72),
                        (f'after_{name}', OUTPUT / f'arena_{name}.wav', 1, 0.72)]
    reel = comparison_reel('contact_before_after', comparisons)
    lethal = compose(1.1, (rate_shift(decode(OUTPUT/'arena_hit.wav'),0.90),0.72,0),
                     (rate_shift(decode(OUTPUT/'arena_execution.wav'),0.90),0.37,0))
    write_pcm(REVIEW/'fatal_composite.wav',lethal)
    comparison_reel('fatal_normal_vs_slow', [
        ('before_fatal_at_0.90', BEFORE/'arena_hit.wav',0.90,0.72),
        ('after_ordinary_at_1x',OUTPUT/'arena_hit.wav',1,0.72),
        ('after_fatal_material_and_accent_at_0.90',REVIEW/'fatal_composite.wav',1,1),
        ('execution_at_1x',OUTPUT/'arena_execution.wav',1,0.72),
        ('execution_at_0.90',OUTPUT/'arena_execution.wav',0.90,0.72)])
    # Real-world playback is not globally slowed with the enemy animation. The reel models that policy.
    demo = blank(9)
    rain = decode(OUTPUT/'arena_rain.wav')
    for i in range(len(demo)): demo[i] = rain[i % len(rain)] * 0.10
    for at,name,gain,rate in [(0.8,'whoosh',0.28,1),(1.02,'hit',0.65,1),(2.5,'block',0.70,1),
                              (3.9,'parry',0.72,1),(5.6,'step',0.16,1),(6.2,'whoosh',0.28,1),
                              (6.4,'hard_hit',0.72,0.90),(6.4,'execution',0.37,0.90)]:
        add(demo,rate_shift(decode(OUTPUT/f'arena_{name}.wav'),rate),gain,at)
    write_pcm(REVIEW/'combat_rain_sequence.wav',demo)
    (REVIEW/'production_manifest.json').write_text(json.dumps(production_manifest(metrics),indent=2)+'\n')
    assert all(x['clipped_samples'] == 0 and x['decoded_bytes'] < 1_000_000 for x in metrics)
    print(json.dumps({'production_cues':len(metrics),'ab_reel_seconds':reel,
                      'max_decoded_bytes':max(x['decoded_bytes'] for x in metrics)},indent=2))


if __name__ == '__main__': main()
