"""Original CC0 rain-night HDR, real cmgen prefilter and separate KTX1 header candidate.

Existing stage2 RGBE/PNG writers and stage3 KTX inspector are reused read-only.
This script writes only its own directory, never the app's published resources.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE_WRITER = ROOT / "ArtSource/refinement/lighting/stage2/ibl/generate_source_hdr.py"
VALIDATOR = ROOT / "ArtSource/refinement/lighting/stage3/ibl/validate_ktx.py"
TOOL_PROVENANCE = ROOT / "ArtSource/refinement/lighting/stage3/ibl/tool_provenance.json"
CMGEN = Path("/Users/yupeng/Library/Caches/pico-wuxia-arena/filament/v1.80.0/filament/bin/cmgen")
WIDTH, HEIGHT = 512, 256
TOP, HORIZON, LOWER = (.015, .027, .055), (.025, .040, .070), (.012, .016, .020)
CAPTURE_ORIGIN = (0, 1.5, -2.4)
ENVIRONMENT_SHA256 = "56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8"
FRONT_LANTERNS = ((-2.15, 2.7, -4.7), (2.15, 2.7, -4.7))


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def unit(vector):
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        raise ValueError("Light patch needs a nonzero direction")
    return tuple(value / length for value in vector)


LIGHTS = [
    *[{"name": "front_lantern_" + side,
       "direction": unit(tuple(anchor[i] - CAPTURE_ORIGIN[i] for i in range(3))),
       "color": (1, .49, .20), "peak": 4, "exponent": 64}
      for side, anchor in zip(("left", "right"), FRONT_LANTERNS)],
    {"name": "moon", "direction": unit((-.5014, .6217, .6017)), "color": (.57, .73, 1), "peak": 3, "exponent": 32},
    {"name": "rear", "direction": unit((1.9, 1, -1)), "color": (.38, .65, 1), "peak": 1.2, "exponent": 48},
]


def sample_direction(direction):
    vertical = direction[1]
    end = TOP if vertical >= 0 else LOWER
    blend = abs(vertical)
    rgb = [h * (1 - blend) + e * blend for h, e in zip(HORIZON, end)]
    for light in LIGHTS:
        weight = light["peak"] * max(0, sum(a * b for a, b in zip(direction, light["direction"]))) ** light["exponent"]
        rgb = [value + color * weight for value, color in zip(rgb, light["color"])]
    return rgb


def sample(x, y):
    theta = math.pi * (y + .5) / HEIGHT
    phi = math.tau * ((x + .5) / WIDTH - .5)
    return sample_direction((math.sin(theta) * math.sin(phi), math.cos(theta), math.sin(theta) * math.cos(phi)))


def source_files():
    writer = load_module("readonly_rgbe_writer", SOURCE_WRITER)
    header = b"#?RADIANCE\n# Original rain-night analytic source, CC0-1.0\nFORMAT=32-bit_rle_rgbe\n\n-Y 256 +X 512\n"
    binary, display = bytearray(header), bytearray()
    minimum, maximum = math.inf, 0
    for y in range(HEIGHT):
        colors = [sample(x, y) for x in range(WIDTH)]
        for rgb in colors:
            if not all(math.isfinite(value) and value > 0 for value in rgb):
                raise ValueError("Nonfinite or nonpositive analytic radiance")
            minimum = min(minimum, *rgb)
            maximum = max(maximum, *rgb)
        pixels = [writer.rgbe(color) for color in colors]
        binary.extend(bytes((2, 2, WIDTH >> 8, WIDTH & 255)))
        for channel in range(4):
            row = bytes(pixel[channel] for pixel in pixels)
            for offset in range(0, WIDTH, 128):
                block = row[offset:offset + 128]
                binary.append(len(block))
                binary.extend(block)
        display.append(0)
        for rgb in colors:
            for value in rgb:
                display.append(round((value / (1 + value)) ** (1 / 2.2) * 255))
    hdr = HERE / "rain_night_latlong.hdr"
    hdr.write_bytes(binary)
    preview = (b"\x89PNG\r\n\x1a\n" + writer.chunk(b"IHDR", struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)) +
               writer.chunk(b"IDAT", zlib.compress(display, 9)) + writer.chunk(b"IEND", b""))
    (HERE / "source_preview.png").write_bytes(preview)
    manifest = {
        "source_commit": "562449af40ee984ddd8ef61be5c339ac9bea2de5", "date": "2026-11-11",
        "license": "CC0-1.0; original analytic rain-night lighting functions in generate_ibl.py",
        "source": hdr.name, "sha256": digest(binary), "bytes": len(binary), "width": WIDTH, "height": HEIGHT,
        "format": "Radiance RGBE per-channel scanline RLE", "projection": "2:1 latlong, PICO +Y up; phi=0 at +Z; positive phi toward +X",
        "linear_color": "Positive scene-linear RGB; arbitrary radiance units, not calibrated lux or lumens",
        "ambient_top": TOP, "ambient_horizon": HORIZON, "ambient_lower": LOWER, "light_patches": LIGHTS,
        "environment_source": {"candidate": "courtyard_hero", "sha256": ENVIRONMENT_SHA256,
                               "capture_origin_stage_m": CAPTURE_ORIGIN, "front_lantern_anchors_stage_m": FRONT_LANTERNS,
                               "side_lantern_anchors_stage_m": [[-4.03, 2.25, .56], [4.03, 2.25, -1.32]],
                               "side_lobes": "not included; front pair supplies the authored warm lobes"},
        "all_analytic_texels_finite_and_positive": True, "minimum_linear_channel": minimum, "maximum_linear_channel": maximum,
        "generator_sha256": digest(Path(__file__).read_bytes()), "reused_writer": str(SOURCE_WRITER.relative_to(ROOT)),
        "reused_writer_sha256": digest(SOURCE_WRITER.read_bytes()),
        "preview": {"path": "source_preview.png", "sha256": digest(preview), "mapping": "Reinhard value/(1+value), gamma1/2.2; source inspection only"},
        "orientation_boundary": "cmgen default mirroring is enabled (no --no-mirror). Source/Filament/PICO reflected azimuth equivalence remains untested.",
        "status": "HDR source generated; downstream conversion tracked separately",
    }
    (HERE / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return hdr, manifest


def canonicalize(raw):
    if raw[:12] != b"\xabKTX 11\xbb\r\n\x1a\n" or raw[12:16] != b"\x01\x02\x03\x04":
        raise ValueError("Expected existing cmgen little-endian KTX1 profile")
    changed = bytearray(raw)
    fields = (("glType", 16, 0x8C3A, 0x8C3B), ("glTypeSize", 20, 1, 4), ("glBaseInternalFormat", 32, 0x8C3A, 0x1907))
    for name, offset, old, new in fields:
        if struct.unpack_from("<I", raw, offset)[0] != old:
            raise ValueError("Unexpected cmgen field " + name)
        struct.pack_into("<I", changed, offset, new)
    if raw[64:] != changed[64:]:
        raise ValueError("Header candidate changed metadata/prefilter payload")
    return bytes(changed), {"fields": [{"name": n, "offset": o, "from": a, "to": b} for n, o, a, b in fields],
                            "changed_byte_offsets": [i for i, (a, b) in enumerate(zip(raw, changed)) if a != b],
                            "all_bytes_after_64_identical": True, "metadata_and_prefilter_payload_sha256": digest(raw[64:])}


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    hdr, source = source_files()
    if not CMGEN.is_file():
        (HERE / "generation_manifest.json").write_text(json.dumps({"status": "SOURCE_ONLY", "reason": "Existing cmgen binary unavailable; no download attempted"}, indent=2) + "\n")
        return
    previous_tool = json.loads(TOOL_PROVENANCE.read_text())
    tool_hash = digest(CMGEN.read_bytes())
    if tool_hash != previous_tool["binary_sha256"]:
        raise ValueError("Existing cmgen differs from the already verified tool identity")
    output = HERE / "generated"
    output.mkdir(exist_ok=True)
    command = [str(CMGEN), "--format=ktx", "--size=128", "--ibl-samples=1024", "--ibl-ld=" + str(output), "--deploy=" + str(output), str(hdr)]
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    (HERE / "generation_output.txt").write_text(completed.stdout)
    report = {"status": "GENERATED" if completed.returncode == 0 else "FAILED", "command": command, "cwd": str(ROOT), "started_utc": started,
              "ended_utc": datetime.now(timezone.utc).isoformat(), "exit_code": completed.returncode,
              "source_sha256": source["sha256"], "tool": previous_tool, "tool_binary_sha256_checked": tool_hash,
              "output_files": [{"path": str(path.relative_to(HERE)), "bytes": path.stat().st_size, "sha256": digest(path.read_bytes())} for path in sorted(output.glob("*")) if path.is_file()],
              "orientation_boundary": source["orientation_boundary"], "pico_interoperability": "UNTESTED; structure and generation do not prove runtime compatibility"}
    (HERE / "generation_manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    if completed.returncode:
        raise RuntimeError("cmgen failed; exact output preserved")
    raw_path = output / "generated_ibl.ktx"
    raw = raw_path.read_bytes()
    candidate, repack = canonicalize(raw)
    candidate_path = HERE / "candidate_standard_header.ktx"
    candidate_path.write_bytes(candidate)
    repack.update({"source": str(raw_path.relative_to(HERE)), "source_sha256": digest(raw), "output": candidate_path.name, "output_sha256": digest(candidate),
                   "bytes": len(candidate), "status": "THREE_HEADER_FIELDS_ONLY; source unchanged", "pico_interoperability": "UNTESTED"})
    (HERE / "header_repack_manifest.json").write_text(json.dumps(repack, indent=2) + "\n")
    validator = load_module("readonly_ktx_validator", VALIDATOR)
    validation = validator.validate_bytes(candidate)
    raw_inspection = validator.validate_bytes(raw, inspect=True)
    if validation["cubemap_faces"] != 6 or validation["mip_levels"] != 4:
        raise ValueError("Expected 6 faces and 4 real roughness-prefilter levels")
    if len(validation["spherical_harmonics_metadata"]) != 1 or len(validation["spherical_harmonics_metadata"][0]["numeric_values"]) != 27:
        raise ValueError("Expected 9 RGB spherical-harmonic coefficients")
    validation["validator_sha256"] = digest(VALIDATOR.read_bytes())
    (HERE / "canonical_validation.json").write_text(json.dumps(validation, indent=2, allow_nan=False) + "\n")
    (HERE / "raw_inspection.json").write_text(json.dumps(raw_inspection, indent=2, allow_nan=False) + "\n")
    shutil.copyfile(ROOT / "ArtSource/refinement/lighting/stage3/ibl/cmgen-license.txt", HERE / "cmgen-license.txt")
    print(json.dumps({"source_sha256": source["sha256"], "raw_sha256": digest(raw), "candidate_sha256": digest(candidate), "faces": 6,
                      "mips": 4, "peak_radiance": validation["maximum_radiance"], "pico_interoperability": "UNTESTED"}, indent=2))


if __name__ == "__main__":
    main()
