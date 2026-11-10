"""Build original, deterministic material-contact PCM and an offline A/B reel."""

import json
import math
import random
import struct
import wave
from pathlib import Path


SAMPLE_RATE = 48000
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "app/src/main/res/raw"
REVIEW = ROOT / "ArtSource/refinement/effects/audio"


def blank(duration):
    return [0.0] * round(duration * SAMPLE_RATE)


def add(destination, source, gain=1.0, delay=0.0):
    offset = round(delay * SAMPLE_RATE)
    for index, value in enumerate(source[:max(0, len(destination) - offset)]):
        destination[index + offset] += value * gain


def thump(duration, start_hz, end_hz, decay):
    result = blank(duration)
    phase = 0.0
    for index in range(len(result)):
        time = index / SAMPLE_RATE
        frequency = end_hz + (start_hz - end_hz) * math.exp(-time * 38)
        phase += math.tau * frequency / SAMPLE_RATE
        result[index] = math.sin(phase) * math.exp(-time * decay)
    return result


def grain(duration, seed, low_hz, high_hz, decay, attack=0.0008):
    result = blank(duration)
    rng = random.Random(seed)
    lower = 0.0
    upper = 0.0
    low_alpha = 1.0 - math.exp(-math.tau * low_hz / SAMPLE_RATE)
    high_alpha = 1.0 - math.exp(-math.tau * high_hz / SAMPLE_RATE)
    for index in range(len(result)):
        time = index / SAMPLE_RATE
        raw = rng.uniform(-1.0, 1.0)
        lower += low_alpha * (raw - lower)
        upper += high_alpha * (raw - upper)
        envelope = min(1.0, time / attack) * math.exp(-time * decay)
        result[index] = (upper - lower) * envelope
    return result


def ring(duration, fundamental, decay, gain=1.0):
    result = blank(duration)
    modes = ((1.0, 0.45), (1.47, 0.32), (2.09, 0.22), (3.13, 0.16), (4.71, 0.10))
    for index in range(len(result)):
        time = index / SAMPLE_RATE
        envelope = min(1.0, time / 0.0015)
        result[index] = gain * envelope * sum(
            weight * math.sin(math.tau * fundamental * ratio * time) *
            math.exp(-time * decay * (1.0 + ratio * 0.18))
            for ratio, weight in modes
        )
    return result


def soft_hit(seed=210):
    result = blank(0.32)
    add(result, thump(0.26, 142, 68, 21), 0.85)
    add(result, grain(0.13, seed, 180, 1600, 35), 1.4)
    add(result, grain(0.16, seed + 1, 1400, 7000, 37), 1.1)
    add(result, grain(0.15, seed + 2, 700, 3200, 28), 0.35, 0.024)
    return result


def hard_hit():
    result = blank(0.48)
    add(result, thump(0.22, 260, 105, 28), 0.32)
    add(result, grain(0.10, 220, 1900, 12500, 57), 2.0)
    add(result, ring(0.48, 870, 12), 0.68)
    return result


def guarded_hit():
    result = blank(0.41)
    add(result, thump(0.30, 118, 59, 18), 0.85)
    add(result, grain(0.18, 230, 160, 2100, 25), 1.7)
    add(result, ring(0.35, 590, 19), 0.34)
    add(result, grain(0.15, 231, 900, 4300, 37), 0.38, 0.017)
    return result


def block():
    result = blank(0.55)
    add(result, thump(0.25, 180, 74, 23), 0.72)
    add(result, grain(0.12, 240, 1400, 10500, 46), 1.7)
    add(result, ring(0.52, 660, 8.5), 0.72)
    add(result, ring(0.26, 930, 20), 0.19, 0.036)
    return result


def parry():
    result = blank(0.72)
    add(result, grain(0.11, 250, 3500, 17000, 65), 2.5)
    add(result, ring(0.70, 1390, 6), 0.65)
    add(result, ring(0.48, 2030, 12), 0.20, 0.018)
    add(result, thump(0.14, 170, 90, 35), 0.25)
    return result


def player_hit():
    result = blank(0.36)
    add(result, thump(0.33, 103, 48, 15), 1.0)
    add(result, grain(0.20, 260, 120, 1900, 25), 1.8)
    add(result, grain(0.24, 261, 600, 3600, 21), 0.42, 0.025)
    return result


def skill():
    result = blank(0.70)
    add(result, thump(0.42, 138, 47, 13), 0.88)
    add(result, grain(0.15, 270, 1000, 12000, 39), 1.9)
    add(result, ring(0.50, 720, 12), 0.37)
    add(result, grain(0.22, 271, 2000, 14500, 23), 0.9, 0.045)
    add(result, ring(0.43, 470, 14), 0.30, 0.063)
    return result


def execution():
    result = blank(0.88)
    add(result, soft_hit(280), 0.70)
    add(result, thump(0.64, 110, 39, 9), 0.74)
    add(result, grain(0.26, 283, 350, 3600, 18), 0.70, 0.07)
    add(result, grain(0.15, 284, 1800, 9000, 27), 0.55, 0.125)
    add(result, ring(0.45, 510, 15), 0.18, 0.13)
    return result


def whoosh():
    result = grain(0.28, 290, 600, 8000, 5, attack=0.07)
    for index in range(len(result)):
        time = index / SAMPLE_RATE
        result[index] *= math.sin(math.pi * min(1.0, time / 0.28)) ** 1.2
    return result


def ending(notes, duration):
    result = blank(duration)
    for index in range(len(result)):
        time = index / SAMPLE_RATE
        for start, frequency in notes:
            elapsed = time - start
            if elapsed >= 0:
                result[index] += (math.sin(math.tau * frequency * elapsed) +
                                  0.25 * math.sin(math.tau * frequency * 2.01 * elapsed)) * math.exp(-elapsed * 5)
    return result


def write_pcm(path, samples, sample_rate=SAMPLE_RATE):
    pcm = b"".join(struct.pack("<h", round(value * 32767)) for value in samples)
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(pcm)


def master(samples):
    mean = sum(samples) / len(samples)
    samples = [value - mean for value in samples]
    for index in range(len(samples)):
        time = index / SAMPLE_RATE
        remaining = (len(samples) - 1 - index) / SAMPLE_RATE
        samples[index] *= min(1.0, time / 0.0006, remaining / 0.012)
    peak = max(abs(value) for value in samples)
    return [value * 0.60 / peak for value in samples]


def read_mono(path):
    with wave.open(str(path), "rb") as file:
        rate = file.getframerate()
        count = file.getnframes()
        raw = struct.unpack(f"<{count}h", file.readframes(count))
    values = [value / 32768.0 for value in raw]
    if rate == SAMPLE_RATE:
        return values
    # Linear interpolation is sufficient for the frozen low-rate comparison clips.
    resampled = blank(len(values) / rate)
    for index in range(len(resampled)):
        position = index * rate / SAMPLE_RATE
        lower = min(int(position), len(values) - 1)
        upper = min(lower + 1, len(values) - 1)
        fraction = position - lower
        resampled[index] = values[lower] * (1.0 - fraction) + values[upper] * fraction
    return resampled


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REVIEW.mkdir(parents=True, exist_ok=True)
    material = {
        "arena_hit": soft_hit(), "arena_hard_hit": hard_hit(),
        "arena_guarded_hit": guarded_hit(), "arena_block": block(), "arena_parry": parry(),
        "arena_hurt": player_hit(), "arena_skill": skill(), "arena_execution": execution(),
        "arena_whoosh": whoosh(),
        "arena_victory": ending(((0.0, 523.25), (0.13, 659.25), (0.27, 783.99)), 0.95),
        "arena_defeat": ending(((0.0, 311.13), (0.17, 233.08), (0.31, 155.56)), 0.78),
    }
    metrics = []
    for name, samples in material.items():
        samples = master(samples)
        write_pcm(OUTPUT / f"{name}.wav", samples)
        with wave.open(str(OUTPUT / f"{name}.wav"), "rb") as file:
            pcm = struct.unpack(f"<{file.getnframes()}h", file.readframes(file.getnframes()))
        measured = [value / 32768.0 for value in pcm]
        rms = math.sqrt(sum(value * value for value in measured) / len(measured))
        metrics.append({"name": name, "seconds": len(measured) / SAMPLE_RATE,
                        "sample_rate": SAMPLE_RATE, "channels": 1, "bits": 16,
                        "peak_dbfs": 20 * math.log10(max(abs(value) for value in measured)),
                        "rms_dbfs": 20 * math.log10(rms),
                        "clipped_samples": sum(abs(value) >= 32767 for value in pcm),
                        "decoded_bytes": len(pcm) * 2})
    (REVIEW / "audio_measurements.json").write_text(json.dumps(metrics, indent=2) + "\n")
    clips = [
        ("before_soft_hit", REVIEW / "before_soft_hit.wav"),
        ("after_soft_hit", OUTPUT / "arena_hit.wav"),
        ("before_metal", REVIEW / "before_metal.wav"),
        ("after_hard_hit", OUTPUT / "arena_hard_hit.wav"),
        ("guarded_hit", OUTPUT / "arena_guarded_hit.wav"),
        ("block", OUTPUT / "arena_block.wav"),
        ("parry", OUTPUT / "arena_parry.wav"),
        ("player_hit", OUTPUT / "arena_hurt.wav"),
        ("skill_guard_break", OUTPUT / "arena_skill.wav"),
        ("execution", OUTPUT / "arena_execution.wav"),
    ]
    reel = []
    cue_sheet = []
    for label, path in clips:
        reel.extend(blank(0.35))
        start = len(reel) / SAMPLE_RATE
        samples = read_mono(path)
        reel.extend(samples)
        reel.extend(blank(0.35))
        cue_sheet.append({"label": label, "start_seconds": start, "duration_seconds": len(samples) / SAMPLE_RATE})
    write_pcm(REVIEW / "material_contact_comparison.wav", reel)
    (REVIEW / "comparison_cues.json").write_text(json.dumps(cue_sheet, indent=2) + "\n")
    print(json.dumps({"production_cues": len(material), "reel_seconds": len(reel) / SAMPLE_RATE,
                      "max_decoded_bytes": max(item["decoded_bytes"] for item in metrics)}, indent=2))


if __name__ == "__main__":
    main()
