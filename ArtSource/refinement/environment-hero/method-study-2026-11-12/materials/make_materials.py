"""Produce six private wood-window material maps from a fixed source contract.

Long grain: existing Poly Haven CC0 scan, same UV orientation, no added grooves.
End grain: original nonuniform growth arcs; not claimed to be a scanned surface.
Only this script's directory is writable. No Blender or runtime publication.
"""

from pathlib import Path
import hashlib
import json
import math
import sys
import traceback

import numpy as np
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCE = REPO / "ArtSource/tavern/textures"
SEED = 2026111206
LONG_SIZE = 1024
END_SIZE = 512
SOURCE_SHA = {
    "fine_grained_wood_col_1k.jpg": "d171f45ef01bc6e239b00dfaa4961bcd27f7d8e93e3962da3bd3d0ce703d802c",
    "fine_grained_wood_nor_gl_1k.jpg": "ba95eadc009818e161d0f753191f1bacc3fc861e593be0bc6d82b437f9ec8044",
    "fine_grained_wood_rough_1k.jpg": "f281f682e62fe322303dfeaa13dac18b5cb9e113617fe0aca43605b49161d82b",
}
LUMA = np.asarray([.2126, .7152, .0722], dtype=np.float64)
MAPS = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def srgb_to_linear(value):
    return np.where(value <= .04045, value / 12.92,
                    ((value + .055) / 1.055) ** 2.4)


def linear_to_srgb(value):
    value = np.clip(value, 0, 1)
    return np.where(value <= .0031308, 12.92 * value,
                    1.055 * value ** (1 / 2.4) - .055)


def write_png(name, values, role, physical_tile_m, source_kind):
    if values.dtype != np.uint8:
        if not np.isfinite(values).all():
            raise ValueError(f"Non-finite map: {name}")
        values = np.round(np.clip(values, 0, 1) * 255).astype(np.uint8)
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError(f"Expected RGB map: {name}")
    path = HERE / (name + ".png")
    temporary = HERE / (name + ".tmp")
    Image.fromarray(values).save(temporary, format="PNG", compress_level=6)
    temporary.replace(path)
    height, width = values.shape[:2]
    MAPS[path.name] = {
        "role": role,
        "source_kind": source_kind,
        "channels": "RGB",
        "color_space": "sRGB" if role == "baseColor" else "linear",
        "size_px": [width, height],
        "physical_tile_m": list(physical_tile_m),
        "density_px_per_m": [width / physical_tile_m[0], height / physical_tile_m[1]],
        "sha256": sha(path),
    }
    return values


def pack_mr(roughness):
    result = np.empty((*roughness.shape, 3), dtype=np.uint8)
    result[:, :, 0] = 255
    result[:, :, 1] = roughness
    result[:, :, 2] = 0
    return result


def smooth_noise(size, x_knots, y_knots, rng):
    """Nonperiodic interpolated random field; no fixed sinusoidal stripe layer."""
    grid = rng.random((y_knots, x_knots))
    xs = np.linspace(0, x_knots - 1, size)
    ys = np.linspace(0, y_knots - 1, size)
    horizontal = np.asarray([np.interp(xs, np.arange(x_knots), row) for row in grid])
    result = np.asarray([np.interp(ys, np.arange(y_knots), horizontal[:, col])
                         for col in range(size)]).T
    return result


def original_end_grain(palette_linear):
    """A sawn section whose pith lies outside the tile, with irregular growth."""
    rng = np.random.default_rng(SEED)
    size, tile_m = END_SIZE, .25
    texel_centers = (np.arange(size) + .5) / size
    uu, vv = np.meshgrid(texel_centers, texel_centers)
    x, y = uu * tile_m, vv * tile_m
    center = (-.046, .137)
    dx, dy = x - center[0], y - center[1]
    radius = np.sqrt((dx * 1.025) ** 2 + (dy * .975) ** 2)
    theta = np.arctan2(dy, dx)
    large = smooth_noise(size, 7, 8, rng)
    small = smooth_noise(size, 29, 31, rng)
    fine = smooth_noise(size, 157, 163, rng)
    warp_m = (large - .5) * .0065 + (small - .5) * .0012

    latewood = np.zeros((size, size), dtype=np.float64)
    growth_centers = []
    boundary = .0
    while boundary < float(radius.max()) + .015:
        boundary += float(rng.uniform(.0021, .0047))
        growth_centers.append(boundary)

    angular_knots = np.linspace(-math.pi, math.pi, 14)
    widths_m = []
    for boundary in growth_centers:
        # Each year's growth changes gradually around the circumference.
        wobble = rng.uniform(-.00040, .00040, len(angular_knots))
        wobble[-1] = wobble[0]
        angular_shift = np.interp(theta, angular_knots, wobble)
        intensity_knots = rng.uniform(.08, 1.0, len(angular_knots))
        intensity_knots[-1] = intensity_knots[0]
        intensity = np.interp(theta, angular_knots, intensity_knots)
        width = float(rng.uniform(.00028, .00065))
        widths_m.append(width)
        distance = radius + warp_m - boundary - angular_shift
        band = np.exp(-.5 * (distance / (width * (.85 + .3 * small))) ** 2)
        latewood += band * intensity
    latewood = np.minimum(latewood, 1.15)

    # Low-contrast anatomical color variation, not a high-contrast black barcode.
    brightness = .969 + (large - .5) * .095 + (small - .5) * .032 - latewood * .077
    brightness += (fine - .5) * .027
    color = palette_linear[None, None, :] * brightness[:, :, None]
    # Slight early/latewood chroma change; mean palette remains aged scan-derived.
    color[:, :, 0] *= 1 + (small - .5) * .020
    color[:, :, 2] *= 1 - (small - .5) * .025
    color = np.clip(color, 0, 1)

    # Micrometre relief only. No cracks, sculpted grooves, edge dirt or AO.
    height_m = -.000018 * latewood + (fine - .5) * .000009
    dy_h, dx_h = np.gradient(height_m, tile_m / size, tile_m / size)
    normal = np.dstack((-dx_h, -dy_h, np.ones_like(dx_h)))
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    normal = normal * .5 + .5
    roughness = np.clip(.875 + (small - .5) * .040 + latewood * .018 +
                        (fine - .5) * .015, .80, .95)

    recipe = {
        "kind": "original procedural end grain; palette derived from aged scan mean only",
        "seed": SEED,
        "pith_m_relative_to_tile_top_left": list(center),
        "radius_m": "sqrt((1.025*(x+0.046))^2 + (0.975*(y-0.137))^2)",
        "growth_spacing_m": [.0021, .0047],
        "latewood_gaussian_width_m": [min(widths_m), max(widths_m)],
        "angular_boundary_wobble_m": [-.00040, .00040],
        "spatial_warp_m": "0.0065*(noise7x8-.5)+0.0012*(noise29x31-.5)",
        "angular_ring_intensity_range": [.08, 1.0],
        "color_multiplier": "0.969+.095*(large-.5)+.032*(small-.5)-.077*latewood+.027*(fine-.5)",
        "height_m": "-0.000018*latewood+0.000009*(fine-.5)",
        "normal_formula": "normalize(-dHeight/dU_m, -dHeight/dV_m, 1), mapped to RGB [0,1]",
        "roughness_formula": "clamp(.875+.040*(small-.5)+.018*latewood+.015*(fine-.5),.80,.95)",
        "added_ao": False,
        "added_position_dependent_dirt_wear_or_wetness": False,
        "fixed_sinusoidal_layers": False,
    }
    return linear_to_srgb(color), normal, roughness, recipe


def contact_sheet():
    sample = 384
    header = 60
    row_height = sample + header
    sheet = Image.new("RGB", (sample * 3, row_height * 2), (27, 29, 31))
    draw = ImageDraw.Draw(sheet)
    font_path = Path("/System/Library/Fonts/Supplemental/Songti.ttc")
    font = ImageFont.truetype(str(font_path), 20) if font_path.exists() else ImageFont.load_default()
    for row, (prefix, label) in enumerate([
        ("wood_long", "实扫顺纹 · 0.8m/tile · 1280px/m"),
        ("wood_end", "原创端纹 · 0.25m/tile · 2048px/m"),
    ]):
        for col, (suffix, role) in enumerate([("basecolor", "sRGB baseColor"),
                                               ("normal", "linear OpenGL normal"),
                                               ("mr", "linear MR: R1 Grough B0")]):
            image = Image.open(HERE / f"{prefix}_{suffix}.png").convert("RGB")
            image = image.resize((sample, sample), Image.Resampling.LANCZOS)
            y = row * row_height
            draw.text((col * sample + 10, y + 5), label, font=font, fill=(235, 232, 220))
            draw.text((col * sample + 10, y + 31), role, font=font, fill=(190, 198, 202))
            sheet.paste(image, (col * sample, y + header))
    path = HERE / "materials_contact.png"
    sheet.save(path)
    return {"path": path.name, "sha256": sha(path),
            "color_exposure_change_for_preview": False,
            "note": "Displayed at equal pixel panel sizes; labels state different physical tile sizes"}


def main():
    expected_suffix = Path("ArtSource/refinement/environment-hero/method-study-2026-11-12/materials")
    if HERE != REPO / expected_suffix:
        raise RuntimeError("Output directory differs from the explicit materials ownership contract")
    sources = {}
    for name, expected in SOURCE_SHA.items():
        path = SOURCE / name
        if sha(path) != expected:
            raise ValueError(f"Frozen scan SHA mismatch: {name}")
        sources[name] = {"path": str(path.relative_to(REPO)), "sha256": expected}
    source_color = np.asarray(Image.open(SOURCE / "fine_grained_wood_col_1k.jpg").convert("RGB"))
    source_normal = np.asarray(Image.open(SOURCE / "fine_grained_wood_nor_gl_1k.jpg").convert("RGB"))
    source_roughness = np.asarray(Image.open(SOURCE / "fine_grained_wood_rough_1k.jpg").convert("L"))
    if source_color.shape != (LONG_SIZE, LONG_SIZE, 3) or source_normal.shape != source_color.shape:
        raise ValueError("Unexpected long-grain source dimensions")
    if source_roughness.shape != (LONG_SIZE, LONG_SIZE):
        raise ValueError("Unexpected roughness source dimensions")

    color_linear = srgb_to_linear(source_color.astype(np.float64) / 255)
    luminance = color_linear @ LUMA
    aged_linear = (.88 * color_linear + .12 * luminance[:, :, None]) * .98
    long_color = write_png("wood_long_basecolor", linear_to_srgb(aged_linear),
                            "baseColor", (.8, .8), "existing CC0 scanned long grain, modest color adjustment")
    write_png("wood_long_normal", source_normal, "normal", (.8, .8),
              "decoded source pixels copied exactly; no channel flip, rotation, sharpening or amplitude change")
    write_png("wood_long_mr", pack_mr(source_roughness), "metallicRoughness", (.8, .8),
              "G is decoded source roughness copied exactly; R=255, B=0")

    end_color, end_normal, end_roughness, end_recipe = original_end_grain(aged_linear.mean(axis=(0, 1)))
    write_png("wood_end_basecolor", end_color, "baseColor", (.25, .25), "original procedural end grain")
    write_png("wood_end_normal", end_normal, "normal", (.25, .25), "original physical-height end-grain normal")
    write_png("wood_end_mr", pack_mr(np.round(end_roughness * 255).astype(np.uint8)),
              "metallicRoughness", (.25, .25), "original dry end-grain roughness; R=255, B=0")

    # Validate actual encoded deliverables, not just the arrays before PNG export.
    actual_long_normal = np.asarray(Image.open(HERE / "wood_long_normal.png"))
    actual_long_mr = np.asarray(Image.open(HERE / "wood_long_mr.png"))
    actual_end_mr = np.asarray(Image.open(HERE / "wood_end_mr.png"))
    assert np.array_equal(actual_long_normal, source_normal)
    assert np.array_equal(actual_long_mr[:, :, 1], source_roughness)
    for array in [actual_long_mr, actual_end_mr]:
        assert np.all(array[:, :, 0] == 255)
        assert np.all(array[:, :, 2] == 0)
    encoded_luma = srgb_to_linear(long_color.astype(np.float64) / 255) @ LUMA
    assert encoded_luma.mean() < luminance.mean(), "Mean color luminance was raised"
    actual_end_normal = np.asarray(Image.open(HERE / "wood_end_normal.png")).astype(float) / 255 * 2 - 1
    end_normal_error = float(np.max(np.abs(np.linalg.norm(actual_end_normal, axis=2) - 1)))
    assert end_normal_error < .01

    manifest = {
        "status": "complete",
        "scope": "Directed 2026-11-12 wood-window material study only; no scene or runtime modification",
        "producer": str(Path(__file__).relative_to(REPO)),
        "producer_sha256": sha(Path(__file__)),
        "seed": SEED,
        "source": {"asset": "Fine Grained Wood", "author": "Rob Tuytel", "license": "CC0",
                   "asset_url": "https://polyhaven.com/a/fine_grained_wood",
                   "license_url": "https://polyhaven.com/license",
                   "license_record_source": "ArtSource/tavern/README.md", "files": sources},
        "long_grain": {
            "physical_tile_m": [.8, .8], "size_px": [1024, 1024], "density_px_per_m": [1280, 1280],
            "uv_direction": "U across grain, V along source grain; source image orientation retained",
            "basecolor_formula": "decode sRGB C; Y=.2126R+.7152G+.0722B; C_out=.98*(.88*C+.12*Y); encode sRGB; round to 8-bit",
            "normal_formula": "copy decoded fine_grained_wood_nor_gl_1k.jpg RGB pixels exactly into PNG",
            "roughness_formula": "MR.R=255; MR.G=decoded fine_grained_wood_rough_1k.jpg; MR.B=0",
            "resampling": "none", "added_ao": False, "added_grooves": False,
            "added_position_dependent_dirt_wear_or_wetness": False,
        },
        "end_grain": {"physical_tile_m": [.25, .25], "size_px": [512, 512],
                      "density_px_per_m": [2048, 2048], "recipe": end_recipe},
        "binding": {"baseColorFactor": [1, 1, 1, 1], "roughnessFactor": 1,
                    "metallicFactor": 1, "normalTexture.scale": 1,
                    "normal_convention": "OpenGL/glTF tangent-space +Y; linear RGB",
                    "MR": "RGB: R=1 unused for AO, G=absolute roughness, B=0 absolute metallic",
                    "occlusionTexture": "Do not bind the MR red channel as added AO; it is constant one",
                    "note": "Wetness, dust, wear and positional layering belong to Root's geometry/material zoning"},
        "checks": {"long_normal_matches_decoded_source_exactly": True,
                   "long_roughness_matches_decoded_source_exactly": True,
                   "MR_red_constant_255_and_blue_constant_0": True,
                   "long_basecolor_linear_luminance_mean_before": float(luminance.mean()),
                   "long_basecolor_linear_luminance_mean_after": float(encoded_luma.mean()),
                   "long_basecolor_mean_luminance_ratio_after_over_before": float(encoded_luma.mean() / luminance.mean()),
                   "end_normal_max_decoded_unit_length_error": end_normal_error,
                   "six_maps_encoded_and_verified": True},
        "maps": MAPS,
        "contact_sheet": contact_sheet(),
        "limits": ["This is a reusable material tile set, not an installed or rendered PICO result",
                   "Original end grain is not advertised as scanned data or as an identified wood species",
                   "No AO, edge wear, local wetness, or position-dependent dirt is baked into these new tiles"],
    }
    path = HERE / "materials_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("WOOD_MATERIALS_COMPLETE", len(MAPS), "maps", sha(path))


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
