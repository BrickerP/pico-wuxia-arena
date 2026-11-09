"""Author the arena's small, original glTF combat effects.

Run with Blender's Python to reuse the project's GLB encoder. Geometry is
authored directly in glTF metre coordinates, +Y up, without a scene conversion.
"""

import json
import math
import random
import struct
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNTIME = ROOT / "app/src/main/assets/models/effects"
sys.path.insert(0, str(HERE.parent / "tripo-warrior"))
from prepare_rigged_warrior import write_glb


class Effect:
    def __init__(self, name, clip, duration, plane):
        self.name = name
        self.clip = clip
        self.duration = duration
        self.plane = plane
        self.binary = bytearray()
        self.triangles = 0
        self.positions = []
        self.document = {
            "asset": {"version": "2.0", "generator": "PICO Wuxia Arena original effects"},
            "scene": 0,
            "scenes": [{"name": name, "nodes": [0]}],
            "nodes": [{"name": name, "children": [], "extras": {
                "units": "metres", "up": "+Y", "effectPlane": plane,
                "durationSeconds": duration, "clip": clip,
            }}],
            "materials": [], "meshes": [], "accessors": [], "bufferViews": [],
            "buffers": [{"byteLength": 0}],
            "animations": [{"name": clip, "samplers": [], "channels": []}],
        }

    def accessor(self, rows, kind, component=5126, target=None):
        while len(self.binary) % 4:
            self.binary.append(0)
        offset = len(self.binary)
        values = [value for row in rows for value in row]
        code = "f" if component == 5126 else "H"
        self.binary.extend(struct.pack("<" + code * len(values), *values))
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(self.binary) - offset}
        if target is not None:
            view["target"] = target
        view_index = len(self.document["bufferViews"])
        self.document["bufferViews"].append(view)
        accessor = {
            "bufferView": view_index, "componentType": component,
            "count": len(rows), "type": kind,
        }
        if kind in ("SCALAR", "VEC3"):
            accessor["min"] = [min(row[axis] for row in rows) for axis in range(len(rows[0]))]
            accessor["max"] = [max(row[axis] for row in rows) for axis in range(len(rows[0]))]
        self.document["accessors"].append(accessor)
        return len(self.document["accessors"]) - 1

    def material(self, name, color, emission=(0, 0, 0), roughness=0.5):
        self.document["materials"].append({
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorFactor": list(color), "metallicFactor": 0,
                "roughnessFactor": roughness,
            },
            "emissiveFactor": list(emission), "alphaMode": "BLEND", "doubleSided": True,
        })
        return len(self.document["materials"]) - 1

    def node(self, name, vertices, indices, colors, material, translation=(0, 0, 0)):
        normals = [(0.0, 0.0, 0.0)] * len(vertices)
        for start in range(0, len(indices), 3):
            a, b, c = (vertices[index] for index in indices[start:start + 3])
            ab = tuple(b[axis] - a[axis] for axis in range(3))
            ac = tuple(c[axis] - a[axis] for axis in range(3))
            normal = (
                ab[1] * ac[2] - ab[2] * ac[1],
                ab[2] * ac[0] - ab[0] * ac[2],
                ab[0] * ac[1] - ab[1] * ac[0],
            )
            length = math.sqrt(sum(value * value for value in normal))
            normal = tuple(value / length for value in normal) if length else (0, 0, 1)
            for index in indices[start:start + 3]:
                normals[index] = normal
        mesh_index = len(self.document["meshes"])
        self.document["meshes"].append({"name": name, "primitives": [{
            "attributes": {
                "POSITION": self.accessor(vertices, "VEC3", target=34962),
                "NORMAL": self.accessor(normals, "VEC3", target=34962),
                "COLOR_0": self.accessor(colors, "VEC4", target=34962),
            },
            "indices": self.accessor([(index,) for index in indices], "SCALAR", 5123, 34963),
            "material": material, "mode": 4,
        }]})
        node_index = len(self.document["nodes"])
        self.document["nodes"].append({"name": name, "mesh": mesh_index, "translation": list(translation)})
        self.document["nodes"][0]["children"].append(node_index)
        self.triangles += len(indices) // 3
        self.positions.extend(tuple(vertex[axis] + translation[axis] for axis in range(3)) for vertex in vertices)
        return node_index

    def track(self, node, path, times, values):
        animation = self.document["animations"][0]
        sampler = len(animation["samplers"])
        animation["samplers"].append({
            "input": self.accessor([(time,) for time in times], "SCALAR"),
            "output": self.accessor(values, "VEC3"), "interpolation": "LINEAR",
        })
        animation["channels"].append({"sampler": sampler, "target": {"node": node, "path": path}})

    def pulse(self, node, start=0.0, peak=0.025, tail=0.1, finish=None):
        finish = self.duration if finish is None else finish
        times = [0.0]
        values = [(0, 0, 0)]
        if start > 0:
            times.append(start)
            values.append((0, 0, 0))
        times.extend((peak, tail, finish))
        values.extend(((1, 1, 1), (0.6, 0.6, 0.6), (0, 0, 0)))
        self.track(node, "scale", times, values)

    def publish(self):
        self.document["buffers"][0]["byteLength"] = len(self.binary)
        output = HERE / (self.name + ".glb")
        information = write_glb(output, self.document, bytes(self.binary))
        runtime_output = RUNTIME / output.name
        write_glb(runtime_output, self.document, bytes(self.binary))
        return {
            **information, "runtime": "asset://models/effects/" + output.name,
            "clip": self.clip, "durationSeconds": self.duration, "plane": self.plane,
            "triangles": self.triangles, "nodes": len(self.document["nodes"]),
            "defaultPoseBoundsMeters": {
                "min": [min(point[axis] for point in self.positions) for axis in range(3)],
                "max": [max(point[axis] for point in self.positions) for axis in range(3)],
            },
        }


def shard(length, width, depth, angle):
    local = [(0, -length / 2, 0), (width, -length * 0.12, depth),
             (0, length / 2, 0), (-width, -length * 0.12, -depth)]
    return [(x * math.cos(angle) - y * math.sin(angle),
             x * math.sin(angle) + y * math.cos(angle), z) for x, y, z in local]


def metal_sparks():
    effect = Effect("metal_sparks", "metal_sparks_burst", 0.24, "XY facing +Z")
    gold = effect.material("Tempered_gold", (1.0, 0.70, 0.30, 1), (0.62, 0.26, 0.05))
    hot = effect.material("White_hot_core", (1.0, 0.96, 0.79, 1), (0.95, 0.75, 0.40))
    rng = random.Random(513)
    for index in range(18):
        angle = rng.uniform(0, math.tau)
        radius = rng.uniform(0.035, 0.16)
        drift = (math.sin(angle) * radius, math.cos(angle) * radius, rng.uniform(-0.018, 0.018))
        length = rng.uniform(0.018, 0.070)
        vertices = shard(length, rng.uniform(0.0015, 0.0038), 0.0008, -angle)
        colors = [(1, 0.85, 0.55, 0), (1, 1, 1, 0.9), (1, 0.9, 0.65, 0.15), (1, 1, 1, 0.9)]
        node = effect.node("Spark_%02d" % index, vertices, [0, 1, 2, 0, 2, 3], colors,
                           hot if index % 5 == 0 else gold, drift)
        finish = 0.15 + rng.random() * 0.09
        effect.pulse(node, peak=0.012, tail=finish * 0.55, finish=finish)
        effect.track(node, "translation", [0, 0.04, finish], [
            tuple(value * 0.08 for value in drift), drift,
            (drift[0] * 1.8, drift[1] * 1.8 - 0.038, drift[2] * 1.8),
        ])
    return effect


def arc_vertices(radius, width, start, end, segments, plane="XY", lift=0.0):
    vertices, colors, indices = [], [], []
    for index in range(segments + 1):
        fraction = index / segments
        angle = start + (end - start) * fraction
        taper = math.sin(math.pi * fraction) ** 0.7
        for offset, alpha in ((-width * taper, 0), (0, 0.85 * taper), (width * taper, 0)):
            radial = radius + offset
            if plane == "XY":
                vertices.append((math.cos(angle) * radial, math.sin(angle) * radial, lift))
            else:
                vertices.append((math.cos(angle) * radial, lift, math.sin(angle) * radial))
            colors.append((1, 1, 1, alpha))
        if index > 0:
            previous, current = (index - 1) * 3, index * 3
            for side in range(2):
                indices.extend((previous + side, current + side, current + side + 1,
                                previous + side, current + side + 1, previous + side + 1))
    return vertices, indices, colors


def blade_arc():
    effect = Effect("blade_arc", "blade_arc_cut", 0.18, "XY facing +Z, radius around origin")
    ivory = effect.material("Ivory_edge_glint", (0.91, 0.91, 0.80, 0.62), (0.34, 0.35, 0.26))
    for index, (radius, width, start, end) in enumerate((
        (0.43, 0.018, -0.40, 1.75),
        (0.40, 0.007, -0.30, 1.38),
    )):
        vertices, indices, colors = arc_vertices(radius, width, start, end, 28, lift=index * 0.002)
        node = effect.node("Blade_sweep_%d" % index, vertices, indices, colors, ivory)
        effect.pulse(node, peak=0.024, tail=0.07, finish=0.18)
    return effect


def break_ring():
    effect = Effect("break_ring", "break_ring_release", 0.44, "XZ ground, +Y normal")
    air = effect.material("Desaturated_gold_air", (0.76, 0.66, 0.43, 0.30), (0.17, 0.12, 0.04))
    for index, (radius, width, start, end) in enumerate((
        (0.38, 0.028, 0.05, 1.16), (0.38, 0.024, 1.50, 2.64),
        (0.38, 0.030, 2.98, 4.04), (0.38, 0.025, 4.42, 5.88),
        (0.26, 0.012, 0.25, 2.40), (0.26, 0.012, 3.0, 5.5),
    )):
        vertices, indices, colors = arc_vertices(radius, width, start, end, 18, "XZ", 0.016 + index * 0.001)
        node = effect.node("Broken_air_arc_%d" % index, vertices, indices, colors, air)
        effect.track(node, "scale", [0, 0.04, 0.20, 0.36, 0.44],
                     [(0, 0, 0), (0.45, 1, 0.45), (1.20, 1, 1.20), (1.45, 1, 1.45), (0, 0, 0)])
    return effect


def foot_dust():
    effect = Effect("foot_dust", "foot_dust_settle", 0.52, "XZ ground, +Y normal")
    dust = effect.material("Wet_stone_dust", (0.30, 0.27, 0.20, 0.26), roughness=1)
    grit = effect.material("Stone_grit", (0.28, 0.28, 0.25, 0.70), roughness=1)
    rng = random.Random(715)
    for index in range(10):
        angle = rng.uniform(0, math.tau)
        distance = rng.uniform(0.04, 0.18)
        center = (math.cos(angle) * distance, rng.uniform(0.007, 0.028), math.sin(angle) * distance)
        size = rng.uniform(0.035, 0.075)
        vertices = [(0, 0, 0)]
        colors = [(1, 1, 1, 0.42)]
        indices = []
        for side in range(9):
            angle = side / 8 * math.tau
            vertices.append((math.cos(angle) * size, 0, math.sin(angle) * size * 0.62))
            colors.append((1, 1, 1, 0))
            if side < 8:
                indices.extend((0, side + 2, side + 1))
        node = effect.node("Dust_wisp_%02d" % index, vertices, indices, colors, dust, center)
        effect.track(node, "scale", [0, 0.06, 0.26, 0.52],
                     [(0, 0, 0), (0.75, 1, 0.75), (1.4, 1, 1.4), (0, 0, 0)])
        effect.track(node, "translation", [0, 0.26, 0.52], [
            tuple(value * 0.35 for value in center), center,
            (center[0] * 1.6, center[1] + 0.035, center[2] * 1.6),
        ])
    for index in range(6):
        angle = rng.uniform(0, math.tau)
        center = (math.sin(angle) * 0.15, 0.018, math.cos(angle) * 0.15)
        vertices = [(0, 0.003, 0), (0.003, 0, 0), (-0.002, 0, 0.003), (-0.002, 0, -0.002)]
        node = effect.node("Grit_%02d" % index, vertices,
                           [0, 1, 2, 0, 2, 3, 0, 3, 1, 1, 3, 2], [(1, 1, 1, 1)] * 4, grit, center)
        effect.pulse(node, peak=0.035, tail=0.16, finish=0.30)
    return effect


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    entries = [make().publish() for make in (metal_sparks, blade_arc, break_ring, foot_dust)]
    manifest = {
        "units": "metres", "coordinates": "glTF +Y up",
        "source": "Original geometry and vertex-color effects authored for this project",
        "textures": 0, "skins": 0, "effects": entries,
    }
    (HERE / "effects_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for entry in entries:
        print(entry["file"], entry["triangles"], "triangles", entry["bytes"], "bytes")


if __name__ == "__main__":
    main()
