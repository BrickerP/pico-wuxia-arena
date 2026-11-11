"""Bake original paper PBR maps for the private 06 stage2 courtyard candidate.

No source image, frozen GLB, production resource, or stage1 producer is changed.
The emissive maps are art-directed radiance variation, not physical transmission.
Run from the canonical repository with system Python, Pillow and NumPy.
"""

from pathlib import Path
import hashlib
import json
import math
import sys
import traceback

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


HERE = Path(__file__).resolve().parent
OUT = HERE / "textures"
SEED = 2026111106
ATLAS_SIZE = 2048
TILE_SIZE = 1024
GUTTER = 8
PAPER_SIZE = TILE_SIZE - 2 * GUTTER
LANTERN_SIZE = (1024, 512)
MAPS = {}


def noise(width, height, grid_x, grid_y, seed):
    rng = np.random.default_rng(seed)
    grid = Image.fromarray(np.uint8(rng.random((grid_y, grid_x)) * 255))
    result = grid.resize((width, height), Image.Resampling.BICUBIC)
    return np.asarray(result, dtype=np.float32) / 255


def periodic_noise(width, height, grid_x, grid_y, seed):
    """Smooth noise whose U endpoints and first derivative agree."""
    rng = np.random.default_rng(seed)
    grid = rng.random((grid_y, grid_x)).astype(np.float32)
    yy, xx = np.meshgrid(np.linspace(0, grid_y - 1, height),
                         np.linspace(0, grid_x, width), indexing="ij")
    ix = np.floor(xx).astype(int) % grid_x
    iy = np.minimum(np.floor(yy).astype(int), grid_y - 2)
    fx, fy = xx - np.floor(xx), yy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = grid[iy, ix] * (1 - fx) + grid[iy, (ix + 1) % grid_x] * fx
    b = grid[iy + 1, ix] * (1 - fx) + grid[iy + 1, (ix + 1) % grid_x] * fx
    return (a * (1 - fy) + b * fy).astype(np.float32)


def fibres(width, height, seed, wrap_u=False):
    """Short randomly oriented cellulose bundles, without a wood-grain axis."""
    rng = np.random.default_rng(seed)
    field = Image.new("L", (width, height), 128)
    draw = ImageDraw.Draw(field)
    for _ in range(int(width * height / 260)):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        angle = rng.uniform(0, 2 * math.pi)
        length = rng.uniform(2, 10)
        dx, dy = math.cos(angle) * length, math.sin(angle) * length
        color = int(rng.choice([85, 105, 151, 174]))
        for offset in ((-width, 0, width) if wrap_u else (0,)):
            draw.line([(x + offset, y), (x + dx + offset, y + dy)], fill=color, width=1)
    field = field.filter(ImageFilter.GaussianBlur(.55))
    return (np.asarray(field, dtype=np.float32) / 255 - .5) * 3


def normal_map(height_m, physical_width, physical_height, wrap_u=False):
    dy, dx = np.gradient(height_m,
                         physical_height / (height_m.shape[0] - 1),
                         physical_width / (height_m.shape[1] - 1))
    vectors = np.dstack((-dx, -dy, np.ones_like(height_m)))
    vectors /= np.linalg.norm(vectors, axis=2, keepdims=True)
    result = vectors * .5 + .5
    if wrap_u:
        ends = (result[:, 0] + result[:, -1]) / 2
        result[:, 0] = result[:, -1] = ends
    return result


def soft_rectangle(u, v, x0, y0, x1, y1, feather=.003):
    def smooth(value):
        value = np.clip(value, 0, 1)
        return value * value * (3 - 2 * value)
    return (smooth((u - x0) / feather) * smooth((x1 - u) / feather) *
            smooth((v - y0) / feather) * smooth((y1 - v) / feather))


def paper_panel(index):
    n = PAPER_SIZE
    rng = np.random.default_rng(SEED + index)
    v, u = np.mgrid[0:1:complex(n), 0:1:complex(n)]
    cloud = noise(n, n, 9, 12, SEED + index * 7)
    fine = noise(n, n, 69, 83, SEED + index * 7 + 1)
    cellulose = fibres(n, n, SEED + index * 7 + 2)
    pixel_noise = rng.normal(0, .12, (n, n)).astype(np.float32)

    edge_distance = np.minimum.reduce([u, 1 - u, v, 1 - v])
    frame_edge = np.exp(-edge_distance / .017) * (.76 + .24 * cloud)
    bottom_line = .94 - .025 * noise(n, n, 13, 4, SEED + index + 90)
    lower_damp = np.clip((v - bottom_line) / .060, 0, 1) * (.45 + .55 * cloud)
    left_age = np.exp(-u / .065) * np.exp(-((v - .77) / .30) ** 2) * cloud

    # Sheet overlap is a seam in the paper, not another painted window lattice.
    seam = np.zeros((n, n), dtype=np.float32)
    if index in (0, 2):
        seam_y = .58 if index == 0 else .69
        seam = np.exp(-((v - seam_y) / .0017) ** 2).astype(np.float32)
    if index == 3:
        seam = np.exp(-((u - .34) / .0018) ** 2).astype(np.float32)

    patch = np.zeros((n, n), dtype=np.float32)
    patch_edge = patch.copy()
    if index in (1, 3):
        rectangle = (.62, .69, .84, .84) if index == 1 else (.13, .16, .31, .29)
        patch = soft_rectangle(u, v, *rectangle, feather=.003).astype(np.float32)
        patch_inner = soft_rectangle(u, v, rectangle[0] + .004, rectangle[1] + .004,
                                     rectangle[2] - .004, rectangle[3] - .004,
                                     feather=.002)
        patch_edge = np.clip(patch - patch_inner, 0, 1).astype(np.float32)

    value = (.765 + (cloud - .5) * .060 + (fine - .5) * .025 +
             cellulose * .020 + pixel_noise * .015 - frame_edge * .115 -
             lower_damp * .073 - left_age * .035 - seam * .032 +
             patch * .024 - patch_edge * .047)
    basecolor = np.dstack((value, value * .945 - lower_damp * .008,
                          value * .827 - lower_damp * .015)).astype(np.float32)

    # Warm regions are blurred by the paper; denser repairs are less luminous.
    centers = [( .36, .61, .19, .24), (.69, .45, .17, .25),
               ( .46, .34, .21, .19), (.66, .70, .19, .23)]
    cx, cy, rx, ry = centers[index]
    halo = np.exp(-(((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2) * .5)
    core = np.exp(-(((u - cx) / (rx * .46)) ** 2 +
                    ((v - cy) / (ry * .46)) ** 2) * .5)
    glow = (.500 + (cloud - .5) * .055 + halo * .165 + core * .225 -
            frame_edge * .080 - lower_damp * .038 - patch * .105 -
            seam * .022 + cellulose * .006)
    emissive = np.dstack((glow, glow * .980, glow * .895)).astype(np.float32)
    roughness = (.875 + (fine - .5) * .055 + frame_edge * .032 + patch * .020 -
                 lower_damp * .060 + cellulose * .014).astype(np.float32)
    height_m = (cellulose * .000035 + (fine - .5) * .000020 +
                pixel_noise * .000012 + seam * .000045 + patch * .00017)
    normals = normal_map(height_m, 1.25, 1.50)
    return {"basecolor": basecolor, "normal": normals,
            "roughness": roughness, "emissive": emissive}


def lantern_maps():
    width, height = LANTERN_SIZE
    v, u = np.mgrid[0:1:complex(height), 0:1:complex(width)]
    cloud = periodic_noise(width, height, 17, 13, SEED + 301)
    fine = periodic_noise(width, height, 93, 57, SEED + 302)
    cellulose = fibres(width, height, SEED + 303, wrap_u=True)
    belt = np.sin(math.pi * v) ** .70
    rib = ((1 + np.cos(2 * math.pi * 12 * u)) * .5) ** 24
    seams = np.zeros_like(u)
    for x in (1 / 12, 5 / 12, 9 / 12):
        d = (u - x + .5) % 1 - .5
        seams += np.exp(-(d / .0017) ** 2)
    # The collar shadow and lap seams stay on the paper, with no painted halo.
    collar = np.exp(-v / .055) + np.exp(-(1 - v) / .055)
    value = (.655 + (cloud - .5) * .085 + (fine - .5) * .028 +
             cellulose * .028 - collar * .055 - seams * .027 - rib * .009)
    basecolor = np.dstack((value, value * (.258 + belt * .023),
                          value * (.090 + belt * .012))).astype(np.float32)

    glow = (.205 + belt * .625 + (cloud - .5) * .065 +
            np.cos(2 * math.pi * u + .5) * belt * .035 - collar * .032 -
            seams * .025 - rib * .017 + cellulose * .008)
    emissive = np.dstack((glow, glow * (.535 + belt * .065),
                         glow * (.180 + belt * .055))).astype(np.float32)
    roughness = (.815 - belt * .070 + (fine - .5) * .075 +
                 cellulose * .020 + seams * .016).astype(np.float32)
    height_m = cellulose * .000035 + (fine - .5) * .000025 + seams * .000075
    normals = normal_map(height_m, 1.40, .64, wrap_u=True)
    maps = {"basecolor": basecolor, "normal": normals,
            "roughness": roughness, "emissive": emissive}
    for field in maps.values():
        ends = (field[:, 0] + field[:, -1]) * .5
        field[:, 0] = field[:, -1] = ends
    return maps


def save_map(name, values, role):
    if not np.isfinite(values).all():
        raise ValueError(f"Non-finite values in {name}")
    data = np.round(np.clip(values, 0, 1) * 255).astype(np.uint8)
    image = Image.fromarray(data)
    temporary = OUT / (name + ".tmp")
    path = OUT / (name + ".png")
    image.save(temporary, format="PNG", compress_level=6)
    temporary.replace(path)
    MAPS[path.name] = {
        "role": role, "color_space": "sRGB" if role in ("basecolor", "emissive") else "linear",
        "size_px": list(image.size), "channels": image.mode,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "range_normalized": [float(data.min() / 255), float(data.max() / 255)],
        "mean_normalized": float(data.mean() / 255),
    }
    return data


def contact_sheet():
    size = 512
    canvas = Image.new("RGB", (size * 4, size * 2 + 64), (26, 28, 30))
    draw = ImageDraw.Draw(canvas)
    for row, prefix in enumerate(("paper_atlas", "lantern")):
        for col, role in enumerate(("basecolor", "normal", "roughness", "emissive")):
            image = Image.open(OUT / f"{prefix}_{role}.png").convert("RGB")
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            canvas.paste(image, (col * size, row * (size + 32) + 32))
            draw.text((col * size + 12, row * (size + 32) + 9), f"{prefix} / {role}",
                      fill=(235, 230, 216))
    canvas.save(OUT / "paper_maps_contact.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    output = {}
    tiles = []
    for index in range(4):
        panel = paper_panel(index)
        col, row = index % 2, index // 2
        for role, field in panel.items():
            if role not in output:
                shape = (ATLAS_SIZE, ATLAS_SIZE) + field.shape[2:]
                output[role] = np.empty(shape, dtype=np.float32)
            padding = ((GUTTER, GUTTER), (GUTTER, GUTTER))
            if field.ndim == 3: padding += ((0, 0),)
            padded = np.pad(field, padding, mode="edge")
            output[role][row * TILE_SIZE:(row + 1) * TILE_SIZE,
                         col * TILE_SIZE:(col + 1) * TILE_SIZE] = padded
        x0, y0 = col * TILE_SIZE + GUTTER, row * TILE_SIZE + GUTTER
        x1, y1 = (col + 1) * TILE_SIZE - GUTTER - 1, (row + 1) * TILE_SIZE - GUTTER - 1
        tiles.append({"index": index, "name": ["lower lamp and horizontal overlap",
                      "right warm spot and lower repair", "upper warm spot and lower overlap",
                      "left paper join and upper repair"][index],
                      "pixel_rect_inclusive_top_left": [x0, y0, x1, y1],
                      "gltf_uv_rect_texel_centers_top_left": [(x0 + .5) / ATLAS_SIZE,
                           (y0 + .5) / ATLAS_SIZE, (x1 + .5) / ATLAS_SIZE, (y1 + .5) / ATLAS_SIZE]})

    for role, field in output.items(): save_map("paper_atlas_" + role, field, role)
    for role, field in lantern_maps().items():
        data = save_map("lantern_" + role, field, role)
        if not np.array_equal(data[:, 0], data[:, -1]):
            raise ValueError(f"Lantern U seam is not periodic: {role}")

    contact_sheet()
    manifest = {
        "status": "complete", "source": "Original deterministic procedural paper and cellulose maps; no external images",
        "seed": SEED, "producer": "ArtSource/refinement/environment-hero/stage2/make_paper_maps.py",
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "maps": MAPS,
        "paper_atlas": {"size_px": ATLAS_SIZE, "tiles_per_axis": 2,
             "tile_size_px": TILE_SIZE, "gutter_px": GUTTER, "content_size_px": PAPER_SIZE,
             "tiles": tiles, "reference_paper_size_m": [1.25, 1.50],
             "recommended_emissive_factor": [.32, .24, .13], "recommended_normal_scale": .65,
             "v_direction": "PNG/glTF v=0 is the top; sheet lower damp edge is v=1",
             "sampler": "Use content texel-center rectangles; edge-dilated gutters protect bilinear/mip sampling"},
        "lantern": {"size_px": list(LANTERN_SIZE), "uv": "full 0..1; U seam endpoints identical",
             "v_direction": "v=0 top collar; v=.5 belly; v=1 bottom collar; symmetric collar darkening",
             "reference_surface_size_m": [1.40, .64], "recommended_emissive_factor": [.75, .65, .50],
             "recommended_normal_scale": .55, "rib_count": 12,
             "native_light_reference": "07 RGB (1,.49,.20), existing unchanged lantern anchors"},
        "causal_features": ["adhesive/frame compression and damp aging at paper edges",
             "sheet overlaps and a small number of denser paper repairs",
             "blurred warm regions behind paper; layered repairs reduce emitted pattern intensity",
             "short random cellulose bundles without a wood-grain direction",
             "lantern belly brightens; metal collar proximity and lap seams darken the paper"],
        "limits": ["Emissive textures are art-directed visible radiance; no physical transmission is claimed",
             "Texture emission creates no native light pool; 07 must keep real point lights at the anchors",
             "Final contrast and protagonist/background hierarchy require the PICO runtime review"],
    }
    path = OUT / "paper_maps_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("PAPER_MAPS_COMPLETE", len(MAPS), "maps", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
