"""Build static, metre-scale contact layers with the project's existing GLB writer.

Run with Blender Python. Runtime owns timing, opacity and transforms. No glTF
animation resources are required, and every model has three mesh-bearing layers.
"""

import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ArtSource/effects"))
from build_effects import Effect

RUNTIME = ROOT / "app/src/main/assets/models/effects"


class Layer:
    def __init__(self):
        self.vertices, self.indices, self.colors = [], [], []

    def polygon(self, points, color):
        offset = len(self.vertices)
        self.vertices.extend(points)
        self.colors.extend([color] * len(points))
        for index in range(1, len(points) - 1):
            self.indices.extend((offset, offset + index, offset + index + 1))

    def puff(self, center, radius, color, squash=1.0, sides=12):
        offset = len(self.vertices)
        self.vertices.append(center)
        self.colors.append(color)
        for side in range(sides):
            angle = side / sides * math.tau
            self.vertices.append((center[0] + math.cos(angle) * radius,
                                  center[1] + math.sin(angle) * radius * squash,
                                  center[2]))
            self.colors.append((*color[:3], 0.0))
        for side in range(sides):
            self.indices.extend((offset, offset + 1 + side, offset + 1 + (side + 1) % sides))

    def streak(self, center, length, width, angle, color):
        direction = (math.cos(angle), math.sin(angle))
        side = (-direction[1], direction[0])
        offset = len(self.vertices)
        for along, across, alpha in ((-.5, 0, 0), (0, -1, .75), (.5, 0, 0), (0, 1, 1)):
            self.vertices.append((center[0] + direction[0] * length * along + side[0] * width * across,
                                  center[1] + direction[1] * length * along + side[1] * width * across,
                                  center[2]))
            self.colors.append((*color[:3], color[3] * alpha))
        self.indices.extend((offset, offset + 1, offset + 3, offset + 1, offset + 2, offset + 3))

    def arc(self, radius, width, start, end, color, depth=.004, sides=20):
        offset = len(self.vertices)
        for side in range(sides + 1):
            fraction = side / sides
            angle = start + (end - start) * fraction
            taper = math.sin(math.pi * fraction) ** .6
            for displacement, alpha in ((-width, 0), (0, color[3] * taper), (width, 0)):
                radial = radius + displacement * taper
                self.vertices.append((math.cos(angle) * radial, math.sin(angle) * radial, depth))
                self.colors.append((*color[:3], alpha))
            if side:
                previous = offset + (side - 1) * 3
                current = offset + side * 3
                for strip in range(2):
                    self.indices.extend((previous + strip, current + strip, current + strip + 1,
                                         previous + strip, current + strip + 1, previous + strip + 1))


def contact_asset(name, style):
    effect = Effect(name, "", (.62, .44, .72, .65)[style], "XY contact plane; +Z outward normal")
    effect.document.pop("animations")
    effect.document["nodes"][0]["extras"].pop("clip")
    effect.document["nodes"][0]["extras"]["driver"] = "Entity transform and hierarchical opacity"
    core, debris, scar = Layer(), Layer(), Layer()
    rng = random.Random(240 + style)

    if style == 0:
        core.puff((0, 0, .012), .058, (1, .83, .58, .9), .72)
        core.streak((0, 0, .016), .13, .009, .6, (1, .94, .76, 1))
        for index in range(15):
            angle = rng.uniform(0, math.tau)
            radius = rng.uniform(.045, .17)
            center = (math.cos(angle) * radius, math.sin(angle) * radius, rng.uniform(.012, .065))
            debris.puff(center, rng.uniform(.018, .044), (.70, .57, .39, rng.uniform(.32, .58)), .60)
            debris.streak(center, rng.uniform(.014, .040), .0024, angle + .4, (.58, .47, .31, .9))
        scar.streak((0, 0, .003), .28, .013, .6, (.21, .11, .055, .92))
        scar.streak((0, .003, .004), .25, .0022, .6, (1, .79, .45, .94))
        emissions = ((.70, .43, .20), (.065, .043, .022), (.17, .09, .025))
    elif style == 1:
        core.puff((0, 0, .014), .045, (1, .97, .81, .9))
        for angle in (0, .7, 1.8, 2.7):
            core.streak((0, 0, .018), .115, .0045, angle, (1, .96, .83, 1))
        for index in range(27):
            angle = rng.uniform(0, math.tau)
            radius = rng.uniform(.07, .20)
            center = (math.cos(angle) * radius, math.sin(angle) * radius, rng.uniform(.01, .075))
            debris.streak(center, rng.uniform(.035, .095), rng.uniform(.0018, .0038), angle,
                          (1, rng.uniform(.67, .94), .35, 1))
            if index % 3 == 0:
                debris.puff(center, .007, (1, .82, .44, .9), sides=6)
        scar.streak((0, 0, .003), .24, .005, .6, (.94, .80, .54, 1))
        scar.streak((0, -.003, .002), .26, .010, .6, (.19, .15, .10, .75))
        emissions = ((1, .89, .59), (1, .49, .09), (.48, .29, .10))
    elif style == 2:
        core.puff((0, 0, .012), .065, (1, .89, .64, .95), .8)
        for start in (.1, 1.9, 3.7):
            core.arc(.078, .014, start, start + 1.25, (1, .86, .53, .9), sides=14)
        for start in (.05, 1.6, 3.1, 4.65):
            debris.arc(.21, .014, start, start + 1.1, (.92, .76, .42, .82), sides=16)
        for index in range(14):
            angle = rng.uniform(0, math.tau)
            center = (math.cos(angle) * .17, math.sin(angle) * .17, rng.uniform(.016, .06))
            debris.streak(center, .065, .003, angle, (.98, .84, .55, .85))
            debris.puff(center, .028, (.65, .57, .43, .36), .65)
        scar.streak((0, 0, .004), .31, .014, .6, (.25, .16, .08, .95))
        scar.streak((0, .004, .006), .29, .004, .6, (1, .87, .58, 1))
        emissions = ((.85, .63, .29), (.38, .25, .09), (.31, .17, .04))
    else:
        core.puff((0, 0, .006), .055, (.50, .44, .34, .36), .6)
        for index in range(12):
            angle = rng.uniform(0, math.tau)
            center = (math.cos(angle) * rng.uniform(.035, .15), math.sin(angle) * .08, rng.uniform(.006, .035))
            debris.puff(center, rng.uniform(.025, .055), (.47, .42, .33, .32), .6)
            debris.streak(center, .012, .002, angle, (.55, .48, .34, .75))
        scar.streak((0, 0, .002), .18, .035, 0, (.22, .19, .15, .22))
        emissions = ((.035, .027, .018), (.035, .028, .020), (.015, .011, .007))

    layer_stats = {}
    for layer_name, layer, emission in zip(("core", "debris", "scar"), (core, debris, scar), emissions):
        material = effect.material(layer_name + "_material", (1, 1, 1, 1), emission, roughness=.85)
        effect.node(layer_name, layer.vertices, layer.indices, layer.colors, material)
        layer_stats[layer_name] = {"triangles": len(layer.indices) // 3,
                                  "boundsMin": [min(p[a] for p in layer.vertices) for a in range(3)],
                                  "boundsMax": [max(p[a] for p in layer.vertices) for a in range(3)]}
    return effect, layer_stats


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    entries = []
    from prepare_rigged_warrior import write_glb
    for style, name in enumerate(("soft_contact", "metal_contact", "force_contact", "ground_dust")):
        effect, layers = contact_asset(name, style)
        effect.document["buffers"][0]["byteLength"] = len(effect.binary)
        source = HERE / (name + ".glb")
        info = write_glb(source, effect.document, bytes(effect.binary))
        write_glb(RUNTIME / source.name, effect.document, bytes(effect.binary))
        entries.append({**info, "triangles": effect.triangles, "layers": layers,
                        "runtime": "asset://models/effects/" + source.name,
                        "boundsMin": [min(p[a] for p in effect.positions) for a in range(3)],
                        "boundsMax": [max(p[a] for p in effect.positions) for a in range(3)]})
        print(name, effect.triangles, info["bytes"])
    (HERE / "contact_effects_manifest.json").write_text(json.dumps({
        "units": "metres", "plane": "XY", "outwardNormal": "+Z", "animations": 0,
        "meshLayers": ["core", "debris", "scar"], "effects": entries,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
