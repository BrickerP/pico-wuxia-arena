"""Generate the arena's original short PCM feedback assets with the standard library."""

import math
import random
import struct
import wave
from pathlib import Path


SAMPLE_RATE = 22050
OUTPUT = Path(__file__).resolve().parents[2] / "app/src/main/res/raw"


def render(name, duration, sound):
    samples = []
    for index in range(round(duration * SAMPLE_RATE)):
        time = index / SAMPLE_RATE
        value = sound(time)
        fade_in = min(1.0, time / 0.003)
        fade_out = min(1.0, (duration - time) / 0.014)
        samples.append(value * fade_in * fade_out)
    peak = max(abs(value) for value in samples)
    gain = 0.82 / peak if peak else 1.0
    pcm = b"".join(struct.pack("<h", round(max(-1.0, min(1.0, value * gain)) * 32767))
                   for value in samples)
    with wave.open(str(OUTPUT / name), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(SAMPLE_RATE)
        file.writeframes(pcm)


def metal(seed, low, decay):
    rng = random.Random(seed)
    modes = ((low, 1.0), (low * 1.63, 0.52), (low * 2.71, 0.31), (low * 4.13, 0.18))

    def sample(time):
        ring = sum(weight * math.sin(math.tau * frequency * time) * math.exp(-time * decay * (1 + frequency / 5500))
                   for frequency, weight in modes)
        strike = rng.uniform(-1, 1) * math.exp(-time * 95)
        return ring * 0.48 + strike * 0.62

    return sample


def impact(seed, frequency):
    rng = random.Random(seed)

    def sample(time):
        low = math.sin(math.tau * (frequency * time - 52 * time * time)) * math.exp(-time * 28)
        noise = rng.uniform(-1, 1) * math.exp(-time * 48)
        return low * 0.75 + noise * 0.40

    return sample


def wind(seed):
    rng = random.Random(seed)
    previous = 0.0

    def sample(time):
        nonlocal previous
        raw = rng.uniform(-1, 1)
        filtered = raw - previous * 0.65
        previous = raw
        envelope = math.sin(math.pi * min(1.0, time / 0.26)) ** 1.5
        return filtered * envelope * math.exp(-time * 3)

    return sample


def energy(seed, finisher=False):
    rng = random.Random(seed)
    base = metal(seed + 1, 460 if finisher else 720, 6.5)

    def sample(time):
        sweep = math.sin(math.tau * (190 * time + 520 * time * time)) * math.exp(-time * 8)
        burst = rng.uniform(-1, 1) * math.exp(-time * 22)
        body = math.sin(math.tau * 76 * time) * math.exp(-time * 11)
        return base(time) * 0.35 + sweep * 0.25 + burst * 0.25 + body * (0.6 if finisher else 0.3)

    return sample


def ending(notes):
    def sample(time):
        result = 0.0
        for start, frequency in notes:
            elapsed = time - start
            if elapsed < 0:
                continue
            result += (math.sin(math.tau * frequency * elapsed) +
                       0.25 * math.sin(math.tau * frequency * 2.01 * elapsed)) * math.exp(-elapsed * 5)
        return result

    return sample


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    render("arena_hit.wav", 0.20, impact(71, 146))
    render("arena_clash.wav", 0.44, metal(72, 1460, 10))
    render("arena_whoosh.wav", 0.28, wind(73))
    render("arena_hurt.wav", 0.29, impact(74, 83))
    render("arena_skill.wav", 0.58, energy(75))
    render("arena_execution.wav", 0.72, energy(76, finisher=True))
    render("arena_victory.wav", 0.95, ending(((0.0, 523.25), (0.13, 659.25), (0.27, 783.99))))
    render("arena_defeat.wav", 0.78, ending(((0.0, 311.13), (0.17, 233.08), (0.31, 155.56))))
    render("arena_dry.wav", 0.09, impact(77, 260))
    print("Generated 9 arena feedback sounds")


if __name__ == "__main__":
    main()
