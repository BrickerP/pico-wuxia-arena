#!/usr/bin/env python3
"""Offline base-mip code-value errors; no native visual or GPU-memory claim."""
import argparse
import io
import json
import math
from pathlib import Path
import tempfile

from PIL import Image, ImageChops
import compress_pbr as p


def measure(source, source_sha, candidate, candidate_sha, encoder, output):
    p.require(output.resolve() not in (source.resolve(), candidate.resolve()) and not output.exists(),
              "quality report output must be a new file")
    raw, converted = source.read_bytes(), candidate.read_bytes()
    p.require(p.sha(raw) == source_sha and p.sha(converted) == candidate_sha, "source/candidate SHA mismatch")
    p.verify_preserved(raw, converted)
    p.encoder_identity(encoder)
    sd, sb = p.load_glb(raw)
    cd, cb = p.load_glb(converted)
    contracts = p.image_contracts(sd)
    records = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, contract in enumerate(contracts):
            ktx, png = Path(tmp) / "image.ktx2", Path(tmp) / "decoded.png"
            ktx.write_bytes(p.view_bytes(cd, cb, cd["images"][i]["bufferView"]))
            if png.exists():
                png.unlink()
            p.run([encoder, "extract", "--transcode", "rgba8", "--level", "0", ktx, png])
            with Image.open(io.BytesIO(p.view_bytes(sd, sb, sd["images"][i]["bufferView"]))) as original:
                with Image.open(png) as decoded:
                    mode = original.mode
                    difference = ImageChops.difference(original, decoded.convert(mode))
                    stats = []
                    for channel, band in zip(mode, difference.split()):
                        histogram = band.histogram()
                        n = original.width * original.height
                        mse = sum(v * v * count for v, count in enumerate(histogram)) / n
                        stats.append({"channel": channel,
                                      "psnr_db": 10 * math.log10(255 * 255 / mse) if mse else None,
                                      "mean_absolute_error_0_255": sum(v * count for v, count in enumerate(histogram)) / n,
                                      "max_absolute_error_0_255": max(v for v, count in enumerate(histogram) if count)})
            records.append({"image": i, "name": sd["images"][i].get("name"), **contract, "channels": stats})
            print(f"measured {i + 1}/{len(contracts)}", flush=True)
    report = {"input_sha256": source_sha, "candidate_sha256": candidate_sha,
              "measurement": "full-resolution top-mip decoded UASTC vs original decoded PNG/JPEG, per-channel code-value error",
              "psnr_null_means_exact_channel": True,
              "native_visual_acceptance": "pending; these metrics have no automatic visual pass threshold",
              "images": records}
    output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("input", "candidate", "encoder", "output"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--candidate-sha256", required=True)
    args = parser.parse_args()
    measure(args.input, args.source_sha256, args.candidate, args.candidate_sha256, args.encoder, args.output)
