"""Deterministic native PBR textures for the authored dao's actual UV0 layout.

Run with host Python/Pillow/numpy. No geometry, material GLB or source is written.
PNG row zero is glTF V=0. Base colour is sRGB; MR/normal data are linear.
"""

import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
SOURCE = REPO / "ArtSource/dao/dao_study.glb"
SOURCE_SHA = "0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616"
SEED = 20261111
SIZE = 1024


def read_source():
    data = SOURCE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SOURCE_SHA
    length = struct.unpack_from("<I", data, 12)[0]
    return json.loads(data[20:20 + length]), data[28 + length:]


def accessor(document, binary, index):
    row = document["accessors"][index]
    view = document["bufferViews"][row["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[row["type"]]
    dtype = np.dtype({5121: "u1", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[row["componentType"]])
    return np.ndarray((row["count"], width), dtype=dtype, buffer=binary,
        offset=view.get("byteOffset", 0) + row.get("byteOffset", 0),
        strides=(view.get("byteStride", width * dtype.itemsize), dtype.itemsize)).copy()


def node_matrices(document):
    parents = {child: index for index, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    world = {}
    def get(index):
        if index in world:
            return world[index]
        node = document["nodes"][index]
        if "matrix" in node:
            local = np.array(node["matrix"], dtype=float).reshape(4, 4).T
        else:
            x, y, z, w = node.get("rotation", [0, 0, 0, 1])
            local = np.eye(4)
            local[:3, :3] = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]) @ np.diag(node.get("scale", [1, 1, 1]))
            local[:3, 3] = node.get("translation", [0, 0, 0])
        world[index] = get(parents[index]) @ local if index in parents else local
        return world[index]
    return {index: get(index) for index in range(len(document["nodes"]))}


def uv_analysis(document, binary):
    matrices = node_matrices(document)
    result = {material["name"]: [] for material in document["materials"]}
    for index, node in enumerate(document["nodes"]):
        if "mesh" not in node:
            continue
        mesh = document["meshes"][node["mesh"]]
        for primitive in mesh["primitives"]:
            name = document["materials"][primitive["material"]]["name"]
            attributes = primitive["attributes"]
            p = accessor(document, binary, attributes["POSITION"]).astype(float)
            p = (np.column_stack((p, np.ones(len(p)))) @ matrices[index].T)[:, :3]
            record = {"node": node.get("name"), "mesh": mesh.get("name"),
                      "world_bounds_metres": [p.min(axis=0).tolist(), p.max(axis=0).tolist()]}
            if "TEXCOORD_0" not in attributes:
                record["UV0"] = "missing; assign UV0 before binding these images"
                result[name].append(record)
                continue
            uv = accessor(document, binary, attributes["TEXCOORD_0"]).astype(float)
            record["UV0"] = [uv.min(axis=0).tolist(), uv.max(axis=0).tolist()]
            if "indices" in primitive:
                triangles = accessor(document, binary, primitive["indices"]).ravel().astype(int).reshape(-1, 3)
                a, b = uv[triangles[:, 1]] - uv[triangles[:, 0]], uv[triangles[:, 2]] - uv[triangles[:, 0]]
                x, y = p[triangles[:, 1]] - p[triangles[:, 0]], p[triangles[:, 2]] - p[triangles[:, 0]]
                determinant = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
                good = np.abs(determinant) > 1e-12
                if good.any():
                    du = (b[good, 1, None] * x[good] - a[good, 1, None] * y[good]) / determinant[good, None]
                    dv = (-b[good, 0, None] * x[good] + a[good, 0, None] * y[good]) / determinant[good, None]
                    record["median_metres_per_uv_tile"] = [float(np.median(np.linalg.norm(du, axis=1))),
                                                          float(np.median(np.linalg.norm(dv, axis=1)))]
                else:
                    record["uv_metric_status"] = "UV triangles degenerate; no finite texel density inferred"
            result[name].append(record)
    return result


def smooth_noise(rng, size=SIZE, grid=32):
    image = Image.fromarray(np.uint8(rng.uniform(0, 255, (grid, grid))))
    return np.array(image.resize((size, size), Image.Resampling.BICUBIC), dtype=float) / 255


def normal_from_height(height, metres_u, metres_v):
    du = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) / (2 * metres_u / height.shape[1])
    dv_down = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) / (2 * metres_v / height.shape[0])
    normal = np.stack((-du, dv_down, np.ones_like(height)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return normal * .5 + .5


def main():
    document, binary = read_source()
    analysis = uv_analysis(document, binary)
    rng = np.random.default_rng(SEED)
    u, v = np.meshgrid((np.arange(SIZE) + .5) / SIZE, (np.arange(SIZE) + .5) / SIZE)
    broad, medium = smooth_noise(rng, grid=12), smooth_noise(rng, grid=48)
    files, materials = [], {}

    def save(name, data, role, colour_space):
        path = HERE / (name + ".png")
        pixels = np.uint8(np.round(np.clip(data, 0, 1) * 255))
        Image.fromarray(pixels).save(path)
        info = {"path": str(path.relative_to(REPO)), "color_space": colour_space, "texCoord": 0}
        files.append({**info, "role": role, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "resolution": list(Image.open(path).size)})
        return info

    def material(name, stem, colour, roughness, metallic, causes, normal=None, normal_scale=None):
        textures = {"base_color": save(stem + "_basecolor", colour, "base_color", "sRGB"),
                    "roughness": save(stem + "_roughness", roughness, "roughness", "linear"),
                    "metallic_roughness": save(stem + "_metallicRoughness",
                        np.stack((np.ones_like(roughness), roughness, np.broadcast_to(metallic, roughness.shape)), axis=-1),
                        "metallic_roughness", "linear")}
        if normal is not None:
            textures["normal"] = {**save(stem + "_normal", normal, "normal", "linear"), "scale": normal_scale}
        materials[name] = {"textures": textures, "uv_observed": analysis[name], "cause_regions": causes,
                           "pbr_factors_when_binding_absolute_maps": {"baseColorFactor": [1, 1, 1, 1],
                               "metallicFactor": 1, "roughnessFactor": 1},
                           "sampler": {"wrapS": "REPEAT", "wrapT": "REPEAT"}}

    # Blade UV0 V=0 is tip, V=1 is guard. Grinding lives primarily in roughness.
    grain_u = np.array(Image.fromarray(np.uint8(rng.uniform(0, 255, (1, 128)))).resize((SIZE, 1), Image.Resampling.BICUBIC))[0] / 255
    grinding = np.broadcast_to(grain_u[None, :], (SIZE, SIZE))
    scratch = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(scratch)
    for _ in range(22):
        x, y = rng.uniform(.06, .94), rng.uniform(.08, .93)
        length = rng.uniform(.007, .019)
        angle = rng.uniform(-.7, .7)
        dx, dy = length * math.cos(angle) / .085, length * math.sin(angle) / .720
        draw.line((round(x*SIZE), round(y*SIZE), round((x+dx)*SIZE), round((y+dy)*SIZE)),
                  fill=int(rng.uniform(100, 220)), width=2)
    scuff = np.array(scratch.filter(ImageFilter.GaussianBlur(.65)), dtype=float) / 255
    oxide = np.clip((v - .935) / .065, 0, 1) ** 1.7
    oxide *= .65 + .35 * broad
    steel = np.array((.46, .49, .51))[None, None, :] * (1 + .025 * (medium[..., None] - .5))
    steel = steel * (1 - .5 * oxide[..., None]) + np.array((.075, .065, .05)) * oxide[..., None] * .25
    steel += scuff[..., None] * .025
    rough = np.clip(.33 + .075*(grinding-.5) + .025*(medium-.5) + .12*scuff + .18*oxide, .25, .68)
    material("Steel | forged body", "steel_forged", steel, rough, 1-.45*oxide,
             ["V>.935 corresponds last46.8mm near guard; dark oxidized transition", "longitudinal grinding roughness along V", "22 sparse cross-scuff strokes7–19mm", "no painted bright fuller band"])
    material("Steel | sharpened edge", "steel_edge", np.broadcast_to((.63,.66,.68),(SIZE,SIZE,3))*(1-.20*oxide[...,None]),
             np.clip(.21+.035*(grinding-.5)+.06*scuff+.10*oxide,.17,.42), 1-.25*oxide,
             ["existing sharpened-edge material geometry; clean finer polishing, guard-end oxide"])
    material("Steel | dark spine", "steel_spine", np.broadcast_to((.22,.25,.27),(SIZE,SIZE,3))*(.92+.12*broad[...,None]),
             .48+.08*broad, .87, ["dark spine and actual fuller geometry floor; source fuller mesh lacks UV0 and requires geometry-agent UV assignment"])
    material("Steel | uneven wear", "steel_wear", steel*.82, np.clip(rough+.12,.25,.8), .84,
             ["existing physical scar meshes only; source scar mesh lacks UV0"])

    # One cord V tile is repeated12times in the original helical UVs.
    warp, weft = np.cos(2*np.pi*6*u), np.cos(2*np.pi*24*v)
    over = np.cos(np.pi*6*u)*np.cos(np.pi*24*v)
    weave = (warp*(.5+.4*over)+weft*(.5-.4*over))
    crown = np.maximum(np.cos(2*np.pi*(u-.5)),0)**3
    wear = crown*(.25+.45*broad)
    cord = np.array((.25,.17,.10))[None,None,:]*(.94+.10*weave[...,None]+.07*medium[...,None])
    cord += np.array((.16,.13,.08))[None,None,:]*wear[...,None]
    metric = next(row["median_metres_per_uv_tile"] for row in analysis["Grip | worn cord"] if "median_metres_per_uv_tile" in row)
    cord_normal = normal_from_height(weave*.000035, metric[0], metric[1])
    material("Grip | worn cord", "cord_weave", cord, np.clip(.84-.18*wear+.035*weave,.60,.94), 0,
             ["6by24 periodic interlaced yarn cells per original UV tile", "raised cord crown wear hypothesis u≈.5; actual hand contact not baked", "source helical UV V−11..1 repeats12tiles; low-contrast fibers, no high-frequency pixel noise"], cord_normal, .65)

    aged_mask = np.clip(.25+.65*broad+.10*np.sin(2*np.pi*v)**2,0,1)
    aged = np.array((.34,.25,.12))[None,None,:]*(1-.6*aged_mask[...,None])
    aged += np.array((.02,.035,.02))*aged_mask[...,None]*.5
    material("Brass | aged", "brass_aged", aged, .55+.22*aged_mask, .85-.55*aged_mask,
             ["cast base/recess material assignment distinguishes oxidized areas; mottling is not a curvature/AO bake", "large soft oxidation patches retain restrained brass colour"])
    material("Brass | polished ridges", "brass_contact", np.array((.46,.32,.14))[None,None,:]*(.92+.12*medium[...,None]),
             .30+.12*broad, .96, ["existing convex ridge/ring material assignment supplies actual raised-contact causal region"])
    ends = np.maximum(np.clip((.055-v)/.055,0,1),np.clip((v-.945)/.055,0,1))
    crease = (.5+.5*np.sin(2*np.pi*(8*u+.16*np.sin(2*np.pi*v))))**12
    leather = np.array((.19,.075,.058))[None,None,:]*(.9+.16*broad[...,None])
    leather += ends[...,None]*np.array((.18,.12,.075)) + crease[...,None]*.025
    leather_height = -.000045*crease*(.4+.6*np.sin(np.pi*v)**2)
    material("Grip | dark oxblood leather", "leather_pressed", leather, np.clip(.74-.10*crease+.10*ends+.025*(medium-.5),.5,.9),0,
             ["Vends each~11.1mm of202mm handle core receive dry end wear", "8 broad compressed longitudinal leather crease bands; no baked lighting"],
             normal_from_height(leather_height,.095,.202),.45)

    manifest = {"schema":"weapon_surfaces_v1", "source":{"path":str(SOURCE.relative_to(REPO)),"sha256":SOURCE_SHA},
        "seed":SEED,"resolution":SIZE,"uv_convention":{"origin":"upper-left; row0 is glTF V0", "coord":"TEXCOORD_0", "blade_y_metres":"0.735−0.720*V", "blade_tip_V":0,"blade_guard_V":1},
        "normal_convention":{"encoding":"OpenGL/glTF tangent +X red, +Y green(up), +Z blue; linearRGB", "height_to_normal":"R=−dH/dU; G=+dH/dimageV(down); B=+1, normalized", "green_flip":False,"height_units":"metres", "cord_height_amplitude_m":.000035,"leather_indent_amplitude_m":.000045},
        "metallic_roughness_channels":{"R":"1; neutral occlusion if used","G":"absolute roughness","B":"absolute metallic"},
        "materials":materials,"files":files,
        "scope":"procedurally authored PNG assets only; actual groove remains geometry; oxidation/contact masks partly material-level hypotheses requiring integrated visual review"}
    (HERE/"surface_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    for name in ("steel_forged_basecolor","steel_forged_roughness","cord_weave_basecolor","cord_weave_normal"):
        assert (HERE/(name+'.png')).is_file()
    print(json.dumps({"materials":len(materials),"PNG_files":len(files),"manifest":str(HERE/"surface_manifest.json"),"cord_metres_per_uv_tile":metric}))


if __name__ == "__main__":
    main()
