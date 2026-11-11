"""Original CC0 code-owned mesh weather; no native particles or volumetric fog.

All coordinates are metres in PICO Stage axes (+Y up, forward -Z).
Only this candidate directory is written. No input or formal app asset is modified.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random
import struct

HERE = Path(__file__).resolve().parent


def encode_glb(document, binary):
    raw = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    raw += b" " * (-len(raw) % 4)
    binary += b"\0" * (-len(binary) % 4)
    length = 12 + 8 + len(raw) + 8 + len(binary)
    return (struct.pack("<4sII", b"glTF", 2, length) +
            struct.pack("<I4s", len(raw), b"JSON") + raw +
            struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def decode_glb(payload):
    if len(payload) < 28:
        raise ValueError("Truncated GLB")
    magic, version, length = struct.unpack_from("<4sII", payload)
    if magic != b"glTF" or version != 2 or length != len(payload):
        raise ValueError("Invalid GLB header or length")
    json_length, kind = struct.unpack_from("<I4s", payload, 12)
    end = 20 + json_length
    if kind != b"JSON" or end + 8 > len(payload):
        raise ValueError("Missing JSON chunk")
    document = json.loads(payload[20:end])
    bin_length, kind = struct.unpack_from("<I4s", payload, end)
    if kind != b"BIN\0" or end + 8 + bin_length != len(payload):
        raise ValueError("Truncated BIN chunk")
    return document, payload[end + 8:]


def mesh_glb(name, positions, colors, triangles, *, blend):
    if not positions or len(colors) != len(positions):
        raise ValueError("Position/color counts differ or empty mesh")
    if any(len(point) != 3 or not all(math.isfinite(v) for v in point) for point in positions):
        raise ValueError("Invalid mesh positions")
    if any(len(color) != 4 or not all(math.isfinite(v) and 0 <= v <= 1 for v in color) for color in colors):
        raise ValueError("Invalid linear vertex colors")
    if not triangles or any(len(face) != 3 or any(i < 0 or i >= len(positions) for i in face) for face in triangles):
        raise ValueError("Invalid triangle index")
    if len(positions) > 65535:
        raise ValueError("Candidate uses uint16 indices")
    # Accessor min/max must describe the actual float32 buffer, not pre-pack doubles.
    positions = [struct.unpack("<3f", struct.pack("<3f", *point)) for point in positions]
    positions_bytes = struct.pack("<" + "f" * (3 * len(positions)), *(v for p in positions for v in p))
    color_bytes = struct.pack("<" + "f" * (4 * len(colors)), *(v for c in colors for v in c))
    index_bytes = struct.pack("<" + "H" * (3 * len(triangles)), *(i for tri in triangles for i in tri))
    parts = (positions_bytes, color_bytes, index_bytes)
    offsets = (0, len(positions_bytes), len(positions_bytes) + len(color_bytes))
    bounds = {key: [fn(p[axis] for p in positions) for axis in range(3)]
              for key, fn in (("min", min), ("max", max))}
    document = {
        "asset": {"version": "2.0", "generator": "PICO 07 original mesh weather generator", "copyright": "CC0-1.0"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name + "Root", "children": [1]}, {"name": name, "mesh": 0}],
        "meshes": [{"name": name, "primitives": [{"attributes": {"POSITION": 0, "COLOR_0": 1}, "indices": 2, "material": 0}]}],
        "materials": [{"name": name + "Unlit", "doubleSided": True, "alphaMode": "BLEND" if blend else "OPAQUE",
                       "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "metallicFactor": 0, "roughnessFactor": 1},
                       "extensions": {"KHR_materials_unlit": {}}}],
        "extensionsUsed": ["KHR_materials_unlit"], "extensionsRequired": ["KHR_materials_unlit"],
        "buffers": [{"byteLength": sum(map(len, parts))}],
        "bufferViews": [{"buffer": 0, "byteOffset": offset, "byteLength": len(part), "target": 34963 if n == 2 else 34962}
                        for n, (offset, part) in enumerate(zip(offsets, parts))],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": len(positions), "type": "VEC3", **bounds},
                      {"bufferView": 1, "componentType": 5126, "count": len(colors), "type": "VEC4"},
                      {"bufferView": 2, "componentType": 5123, "count": 3 * len(triangles), "type": "SCALAR"}],
    }
    return encode_glb(document, b"".join(parts))


def rain_tile(seed=701, count=36):
    rng = random.Random(seed)
    positions, colors, triangles = [], [], []
    drops = []
    for _ in range(count):
        length, width = rng.uniform(.08, .15), rng.uniform(.004, .008)
        center = (rng.uniform(-.97, .97), rng.uniform(length / 2, 2 - length / 2), rng.uniform(-1.97, 1.97))
        alpha = rng.uniform(.25, .45)
        drops.append({"center": list(center), "length_m": length, "width_m": width, "peak_alpha": alpha})
        # Two crossed tapered diamonds stay visible from normal front and oblique views.
        for plane in (0, 2):
            first = len(positions)
            for row, (height, lateral, opacity) in enumerate(((.5, 0, 0), (0, -.5, alpha), (0, .5, alpha), (-.5, 0, 0))):
                point = list(center)
                point[1] += height * length
                point[0] += height * length * .12
                point[plane] += lateral * width
                positions.append(tuple(point))
                colors.append((.50, .66, .78, opacity))
            triangles.extend(((first, first + 1, first + 2), (first + 1, first + 3, first + 2)))
    return positions, colors, triangles, drops


def side_haze(columns=16, rows=6):
    positions, colors, triangles = [], [], []
    for row in range(rows + 1):
        v = row / rows
        for column in range(columns + 1):
            u = column / columns
            x, y = -1.5 + 3 * u, .7 * v
            z = .05 * math.sin(math.pi * u) * math.sin(math.pi * v)
            # All four borders fade exactly to zero, including the ground edge.
            alpha = .12 * math.sin(math.pi * u) ** 2 * math.sin(math.pi * v) ** 2
            positions.append((x, y, z))
            colors.append((.08, .13, .18, alpha))
    for row in range(rows):
        for column in range(columns):
            first = row * (columns + 1) + column
            below = first + columns + 1
            triangles.extend(((first, first + 1, below), (first + 1, below + 1, below)))
    return positions, colors, triangles


def night_sky(segments=48, latitudes=20, radius=30):
    positions = [(0, radius, 0)]
    top, horizon, ground = (.004, .009, .018), (.025, .040, .070), (.008, .012, .016)
    colors = [(*top, 1)]
    for ring in range(1, latitudes):
        theta = math.pi * ring / latitudes
        vertical = math.cos(theta)
        blend = abs(vertical) ** .65
        endpoint = top if vertical >= 0 else ground
        color = tuple(h * (1 - blend) + e * blend for h, e in zip(horizon, endpoint))
        for segment in range(segments):
            phi = math.tau * segment / segments
            positions.append((radius * math.sin(theta) * math.cos(phi), radius * vertical, radius * math.sin(theta) * math.sin(phi)))
            colors.append((*color, 1))
    bottom = len(positions)
    positions.append((0, -radius, 0))
    colors.append((*ground, 1))
    triangles = []
    for segment in range(segments):
        next_segment = (segment + 1) % segments
        # Inward winding, in addition to explicit double-sided material.
        triangles.append((0, 1 + segment, 1 + next_segment))
        for ring in range(latitudes - 2):
            a = 1 + ring * segments + segment
            b = 1 + ring * segments + next_segment
            c = a + segments
            d = b + segments
            triangles.extend(((a, c, b), (b, c, d)))
        last = 1 + (latitudes - 2) * segments
        triangles.append((last + segment, bottom, last + next_segment))
    # Normalize winding directly from geometric orientation (no axis convention ambiguity).
    oriented = []
    for a, b, c in triangles:
        pa, pb, pc = positions[a], positions[b], positions[c]
        ab, ac = [pb[i] - pa[i] for i in range(3)], [pc[i] - pa[i] for i in range(3)]
        cross = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
        oriented.append((a, c, b) if sum(cross[i] * pa[i] for i in range(3)) > 0 else (a, b, c))
    return positions, colors, oriented


def inspect(payload):
    document, binary = decode_glb(payload)
    if document["buffers"][0]["byteLength"] > len(binary):
        raise ValueError("BIN data is shorter than declared")
    decoded = []
    for accessor in document["accessors"]:
        view = document["bufferViews"][accessor["bufferView"]]
        components = {"VEC3": 3, "VEC4": 4, "SCALAR": 1}[accessor["type"]]
        fmt, stride = {5126: ("f", 4), 5123: ("H", 2)}[accessor["componentType"]]
        expected = components * stride * accessor["count"]
        start = view.get("byteOffset", 0)
        if expected != view["byteLength"] or start + expected > len(binary):
            raise ValueError("Accessor exceeds its BIN bufferView")
        values = struct.unpack_from("<" + fmt * (components * accessor["count"]), binary, start)
        if fmt == "f" and not all(math.isfinite(v) for v in values):
            raise ValueError("Nonfinite accessor")
        decoded.append([values[i:i + components] for i in range(0, len(values), components)])
    positions, colors, indices = decoded
    if len(positions) != len(colors) or any(row[0] >= len(positions) for row in indices):
        raise ValueError("Invalid mesh attribute/index counts")
    return document, decoded


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    rain = rain_tile()
    assets = (("rain_tile.glb", "RainTile", rain[:3], True),
              ("side_haze.glb", "SideHaze", side_haze(), True),
              ("rain_night_sky.glb", "NightSky", night_sky(), False))
    manifest = {
        "schema": "pico07-mesh-weather-v1", "source_commit": "562449af40ee984ddd8ef61be5c339ac9bea2de5",
        "license": "CC0-1.0; original analytic geometry and vertex colors in generate_weather.py",
        "coordinate_space": "PICO Stage metres, +Y up, forward -Z",
        "representation": "Mesh weather. Not native ParticleComponent, volumetric fog, IBL, or HDR sky lighting.",
        "runtime_status": "UNTESTED on PICO 6.1.9. Vertex-alpha BLEND and unlit rendering require Root runtime verification.",
        "assets": {},
        "rain_contract": {"tile_height_m": 2, "tile_local_x_range_m": [-1, 1], "tile_local_z_range_m": [-2, 2],
                          "lane_centers_stage": [[-2.7, 0, -2.8], [2.7, 0, -2.8]],
                          "tile_indices_per_lane": [0, 1, 2], "tile_y_m": "-2 + ((tileIndex * 2 + fallPhase) mod 6)",
                          "fall_phase_m": "positive modulo of -2.4 * elapsedSeconds by 6", "central_clear_half_width_m": 1.6,
                          "drops_per_tile": len(rain[3]), "total_tile_instances": 6, "drop_shapes": "two crossed alpha-tapered diamonds"},
        "haze_contract": {"instance_centers_stage": [[-3, 0, -4.4], [3, 0, -4.4]],
                          "peak_vertex_alpha": .12, "all_border_vertex_alpha": 0,
                          "central_clear_half_width_m": 1.5, "type": "thin translucent side strip, no volume integration"},
        "sky_contract": {"center_stage_m": [0, 0, 0], "radius_m": 30, "node": "NightSky", "unlit": True,
                         "alpha_mode": "OPAQUE", "double_sided": True, "winding": "inward", "lighting_contribution": "none"},
        "rain_drops": rain[3],
    }
    for filename, name, geometry, blend in assets:
        payload = mesh_glb(name, *geometry, blend=blend)
        document, decoded = inspect(payload)
        path = HERE / filename
        path.write_bytes(payload)
        manifest["assets"][filename] = {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
                                        "mesh_node": name, "root_node": name + "Root", "vertices": len(decoded[0]),
                                        "triangles": len(decoded[2]) // 3, "bounds": {key: document["accessors"][0][key] for key in ("min", "max")},
                                        "material": document["materials"][0]}
    manifest["generator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (HERE / "weather_contract.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({name: value for name, value in manifest["assets"].items()}, indent=2))


if __name__ == "__main__":
    main()
