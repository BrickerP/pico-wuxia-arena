"""Editable dao geometry candidate from the pinned source, with stable anchors/parts.

Blender 4.5, run from the repository with the complete surface manifest:
  Blender -b --python this_file.py -- --surface-manifest PATH/surface_manifest.json

The final producer requires the manifest. Public sources are read-only.
"""

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO / "ArtSource/dao/dao_study.glb"
SOURCE_SHA = "0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616"
sys.path.insert(0, str(REPO / "ArtSource/refinement/weapon"))
from build_weapon import read_glb, encode_glb
import bpy
from mathutils.bvhtree import BVHTree

SECTIONS = [
    (0.015, -0.020, 0.022, 0.0032),
    (0.055, -0.022, 0.025, 0.0032),
    (0.160, -0.023, 0.027, 0.0030),
    (0.330, -0.021, 0.030, 0.0028),
    (0.500, -0.014, 0.039, 0.0026),
    (0.610, -0.003, 0.051, 0.0023),
    (0.680, 0.014, 0.058, 0.0018),
    (0.720, 0.036, 0.058, 0.0010),
    (0.735, 0.0528, 0.0532, 0.0001),
]
ACROSS = [0, 0.035, 0.11, 0.18, 0.23, 0.29, 0.34, 0.52, 0.69, 0.88, 1]
PROTECTED = {
    "Handle core",
    "Grip | cord wrap",
    "Grip ferrule",
    "Pommel ring",
    "Blade collar",
    "Guard pin 1",
    "Guard pin 2",
}
CHANGED = {
    "Blade",
    "Blade | shallow fuller",
    "Blade | asymmetric wear",
    "Guard | flared oval",
    "Guard | outer rim",
    "Pommel | brass",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lerp(a, b, t):
    return a + (b - a) * t


def profile(height):
    """Preserve the outer outline and interpolate a monotone half-thickness."""
    for section_index, (start, end) in enumerate(zip(SECTIONS, SECTIONS[1:])):
        if start[0] - 1e-8 <= height <= end[0] + 1e-8:
            fraction = max(0, min(1, (height - start[0]) / (end[0] - start[0])))
            slopes = []
            for index in (section_index, section_index + 1):
                previous = SECTIONS[max(0, index - 1)]
                current = SECTIONS[index]
                following = SECTIONS[min(len(SECTIONS) - 1, index + 1)]
                incoming = (
                    (current[3] - previous[3]) / (current[0] - previous[0])
                    if index
                    else 0
                )
                outgoing = (
                    (following[3] - current[3]) / (following[0] - current[0])
                    if index < len(SECTIONS) - 1
                    else incoming
                )
                slopes.append(
                    2 * incoming * outgoing / (incoming + outgoing)
                    if incoming * outgoing > 0
                    else 0
                )
            interval = end[0] - start[0]
            half_thickness = (
                (2 * fraction**3 - 3 * fraction * fraction + 1) * start[3]
                + (fraction**3 - 2 * fraction * fraction + fraction)
                * interval
                * slopes[0]
                + (-2 * fraction**3 + 3 * fraction * fraction) * end[3]
                + (fraction**3 - fraction * fraction) * interval * slopes[1]
            )
            return (
                lerp(start[1], end[1], fraction),
                lerp(start[2], end[2], fraction),
                half_thickness,
            )
    raise ValueError("blade profile outside source range")


def groove(z):
    up = max(0, min(1, (z - 0.035) / 0.035))
    down = max(0, min(1, (0.705 - z) / 0.055))
    return (up * up * (3 - 2 * up)) * (down * down * (3 - 2 * down))


def section(z):
    """Return the symmetric spine, fuller, ridge and cutting-edge section."""
    spine_x, edge_x, half_thickness = profile(z)
    source_factors = [
        0.72 + 0.28 * min(u / 0.69, 1) if u <= 0.69 else (1 - u) / 0.31 for u in ACROSS
    ]
    refined_factors = [0.72, 0.84, 0.87, 0.70, 0.62, 0.72, 0.93, 0.98, 1, 0.40, 0]
    groove_strength = groove(z)
    half_thicknesses = [
        half_thickness * lerp(a, b, groove_strength)
        for a, b in zip(source_factors, refined_factors)
    ]
    front_points = [
        (lerp(spine_x, edge_x, u), -thickness, z)
        for u, thickness in zip(ACROSS, half_thicknesses)
    ]
    return front_points + [(x, -y, z) for x, y, z in reversed(front_points[:-1])]


def front_surface(x, z):
    back, edge, _ = profile(z)
    u = max(0, min(1, (x - back) / (edge - back)))
    side = section(z)[: len(ACROSS)]
    for a, b, pa, pb in zip(ACROSS, ACROSS[1:], side, side[1:]):
        if a <= u <= b:
            return lerp(pa[1], pb[1], (u - a) / (b - a))
    return 0


def new_mesh(
    obj, vertices, faces, materials, indices=None, smooth=False, blade_uv=False
):
    mesh = bpy.data.meshes.new(obj.name + " | refined geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj.data = mesh
    for mat in materials:
        mesh.materials.append(mat)
    for i, face in enumerate(mesh.polygons):
        face.material_index = indices[i] if indices is not None else 0
        face.use_smooth = smooth
    uv = mesh.uv_layers.new(name="SurfaceUV")
    z0 = min(v[2] for v in vertices)
    z1 = max(v[2] for v in vertices)
    for face in mesh.polygons:
        for loop in face.loop_indices:
            p = mesh.vertices[mesh.loops[loop].vertex_index].co
            if blade_uv:
                uv.data[loop].uv = ((p.x + 0.025) / 0.085, (p.z - 0.015) / 0.72)
            else:
                uv.data[loop].uv = (
                    (math.atan2(p.y, p.x) / (2 * math.pi)) % 1,
                    (p.z - z0) / max(z1 - z0, 1e-6),
                )


def build_blade(objects, materials):
    stations = set(s[0] for s in SECTIONS)
    for a, b in zip(SECTIONS, SECTIONS[1:]):
        count = max(2, math.ceil((b[0] - a[0]) / 0.012))
        stations.update(lerp(a[0], b[0], i / count) for i in range(count + 1))
    stations = sorted({round(z, 8) for z in stations})
    vertices = [p for z in stations for p in section(z)]
    n = len(section(stations[0]))
    body, body_mat, floor = [], [], []
    for i in range(len(stations) - 1):
        for j in range(n):
            face = (
                i * n + j,
                i * n + (j + 1) % n,
                (i + 1) * n + (j + 1) % n,
                (i + 1) * n + j,
            )
            if j in (3, 4, 15, 16):
                floor.append(face)
            else:
                body.append(face)
                body_mat.append(2 if j == n - 1 else 1 if j in (8, 9, 10, 11) else 0)
    # Fan caps around an interior point retain boundary edges without collinear-ngon slivers.
    for ring, reverse, material in ((0, True, 2), (len(stations) - 1, False, 1)):
        points = vertices[ring * n : (ring + 1) * n]
        centre = tuple(sum(p[a] for p in points) / n for a in range(3))
        index = len(vertices)
        vertices.append(centre)
        for j in range(n):
            a, b = ring * n + j, ring * n + (j + 1) % n
            body.append((index, b, a) if reverse else (index, a, b))
            body_mat.append(material)
    new_mesh(
        objects["Blade"],
        vertices,
        body,
        [
            materials["Steel | forged body"],
            materials["Steel | sharpened edge"],
            materials["Steel | dark spine"],
        ],
        body_mat,
        blade_uv=True,
    )
    used = sorted({i for f in floor for i in f})
    remap = {old: i for i, old in enumerate(used)}
    new_mesh(
        objects["Blade | shallow fuller"],
        [vertices[i] for i in used],
        [tuple(remap[i] for i in f) for f in floor],
        [materials["Steel | dark spine"]],
        blade_uv=True,
    )
    wear = objects["Blade | asymmetric wear"]
    wear_vertices = [
        (p.co.x, front_surface(p.co.x, p.co.z) - 0.000025, p.co.z)
        for p in wear.data.vertices
    ]
    new_mesh(
        wear,
        wear_vertices,
        [tuple(p.vertices) for p in wear.data.polygons],
        list(wear.data.materials),
        [p.material_index for p in wear.data.polygons],
        blade_uv=True,
    )
    return stations


def lathe(obj, rings, material, inset_bottom=False):
    count = 64
    vertices = []
    faces = []
    for z, rx, ry in rings:
        vertices.extend(
            (
                rx * math.cos(i * 2 * math.pi / count),
                ry * math.sin(i * 2 * math.pi / count),
                z,
            )
            for i in range(count)
        )
    for ring in range(len(rings) - 1):
        for i in range(count):
            faces.append(
                (
                    ring * count + i,
                    ring * count + (i + 1) % count,
                    (ring + 1) * count + (i + 1) % count,
                    (ring + 1) * count + i,
                )
            )
    if inset_bottom:
        base = len(vertices)
        vertices.extend(
            (
                0.0065 * math.cos(i * 2 * math.pi / count),
                0.0055 * math.sin(i * 2 * math.pi / count),
                -0.2306,
            )
            for i in range(count)
        )
        for i in range(count):
            faces.append((i, base + i, base + (i + 1) % count, (i + 1) % count))
        faces.append(tuple(reversed(range(base, base + count))))
    else:
        faces.append(tuple(reversed(range(count))))
    faces.append(tuple((len(rings) - 1) * count + i for i in range(count)))
    new_mesh(obj, vertices, faces, [material], smooth=True)


def snapshot(obj):
    vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
    faces = [tuple(p.vertices) for p in obj.data.polygons]
    return vertices, faces


def bounds(vertices):
    # Blender Z-up -> exported glTF Y-up.
    points = [(v.x, v.z, -v.y) for v in vertices]
    return {
        "min_metres": [min(p[a] for p in points) for a in range(3)],
        "max_metres": [max(p[a] for p in points) for a in range(3)],
    }


def player_frame(document, binary):
    result = copy.deepcopy(document)
    nodes = result["nodes"]
    root = next(i for i, n in enumerate(nodes) if n.get("name") == "DAO_Root")
    grip = next(i for i, n in enumerate(nodes) if n.get("name") == "Grip")
    position = nodes[grip]["translation"]
    q = [-math.sqrt(0.5), 0, 0, math.sqrt(0.5)]
    for i in nodes[root]["children"]:
        if i == grip:
            continue
        node = nodes[i]
        if node.get("rotation", [0, 0, 0, 1]) != [0, 0, 0, 1] or "matrix" in node:
            raise ValueError("unexpected geometry export child rotation")
        p = node.get("translation", [0, 0, 0])
        x, y, z = [p[a] - position[a] for a in range(3)]
        node["translation"] = [x, z, -y]
        node["rotation"] = q.copy()
    nodes[root]["name"] = "Grip"
    nodes[root]["extras"] = {
        "units": "metres",
        "origin": "grip centre",
        "frame": "glTF +Y up, blade forward -Z",
    }
    nodes[root]["children"].remove(grip)
    mapping = {
        old: new for new, old in enumerate(i for i in range(len(nodes)) if i != grip)
    }
    result["nodes"] = [n for i, n in enumerate(nodes) if i != grip]
    for n in result["nodes"]:
        if "children" in n:
            n["children"] = [mapping[i] for i in n["children"]]
    for scene in result["scenes"]:
        scene["nodes"] = [mapping[i] for i in scene["nodes"]]
    return encode_glb(result, binary)


def apply_surfaces(path):
    report = []
    manifest = json.loads(path.read_text())
    for name, entry in manifest["materials"].items():
        mat = bpy.data.materials.get(name)
        if mat is None:
            raise ValueError("surface material missing " + name)
        shader = mat.node_tree.nodes.get("Principled BSDF")
        for role, spec in entry.get("textures", {}).items():
            if role == "roughness":
                report.append(
                    {
                        "material": name,
                        "role": role,
                        "path": spec["path"],
                        "sha256": digest(REPO / spec["path"]),
                        "binding": "audit-only; combined MR green channel is bound",
                    }
                )
                continue
            target = REPO / spec["path"]
            image = bpy.data.images.load(str(target), check_existing=True)
            image.colorspace_settings.name = (
                "sRGB" if spec["color_space"] == "sRGB" else "Non-Color"
            )
            image.pack()
            tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tex.image = image
            tex.extension = "REPEAT"
            if role == "base_color":
                shader.inputs["Base Color"].default_value = (1, 1, 1, 1)
                mat.node_tree.links.new(
                    tex.outputs["Color"], shader.inputs["Base Color"]
                )
            elif role == "metallic_roughness":
                shader.inputs["Roughness"].default_value = 1
                shader.inputs["Metallic"].default_value = 1
                split = mat.node_tree.nodes.new("ShaderNodeSeparateColor")
                mat.node_tree.links.new(tex.outputs["Color"], split.inputs["Color"])
                mat.node_tree.links.new(
                    split.outputs["Green"], shader.inputs["Roughness"]
                )
                mat.node_tree.links.new(
                    split.outputs["Blue"], shader.inputs["Metallic"]
                )
            elif role == "normal":
                normal = mat.node_tree.nodes.new("ShaderNodeNormalMap")
                normal.inputs["Strength"].default_value = spec.get("scale", 1)
                mat.node_tree.links.new(tex.outputs["Color"], normal.inputs["Color"])
                mat.node_tree.links.new(
                    normal.outputs["Normal"], shader.inputs["Normal"]
                )
            else:
                raise ValueError("unsupported texture role " + role)
            report.append(
                {
                    "material": name,
                    "role": role,
                    "path": str(target.relative_to(REPO)),
                    "sha256": digest(target),
                }
            )
    return report


def build(surface_manifest):
    if not surface_manifest.is_file():
        raise FileNotFoundError(
            f"required surface manifest does not exist: {surface_manifest}"
        )
    if digest(SOURCE) != SOURCE_SHA:
        raise ValueError("source dao changed")
    source_doc, _ = read_glb(SOURCE)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    objects = {o.name: o for o in bpy.context.scene.objects if o.type == "MESH"}
    if len(objects) != 13:
        raise ValueError("source component count changed")
    source = {name: snapshot(obj) for name, obj in objects.items()}
    mats = {m.name: m for m in bpy.data.materials}
    stations = build_blade(objects, mats)
    lathe(
        objects["Guard | flared oval"],
        [
            (-0.014, 0.032, 0.014),
            (-0.0135, 0.035, 0.015),
            (-0.011, 0.0405, 0.0175),
            (-0.010, 0.0425, 0.0185),
            (-0.006, 0.0445, 0.019),
            (-0.005, 0.045, 0.019),
            (-0.0035, 0.044, 0.0185),
            (-0.001, 0.041, 0.0175),
            (0, 0.039, 0.017),
            (0.002, 0.034, 0.0145),
            (0.004, 0.026, 0.011),
        ],
        mats["Brass | aged"],
    )
    lathe(
        objects["Guard | outer rim"],
        [
            (-0.008, 0.042, 0.018),
            (-0.0072, 0.0455, 0.0193),
            (-0.0064, 0.046, 0.0195),
            (-0.0048, 0.046, 0.0195),
            (-0.004, 0.0455, 0.0193),
            (-0.0032, 0.0425, 0.0183),
        ],
        mats["Brass | polished ridges"],
    )
    lathe(
        objects["Pommel | brass"],
        [
            (-0.232, 0.009, 0.008),
            (-0.2315, 0.010, 0.0085),
            (-0.229, 0.015, 0.012),
            (-0.2275, 0.0165, 0.013),
            (-0.223, 0.018, 0.014),
            (-0.217, 0.016, 0.012),
            (-0.214, 0.014, 0.011),
        ],
        mats["Brass | aged"],
        True,
    )
    textures = apply_surfaces(surface_manifest)
    HERE.mkdir(parents=True, exist_ok=True)
    blend = HERE / "dao_refined.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    target = HERE / "dao_refined.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(target),
        export_format="GLB",
        export_animations=False,
        export_yup=True,
        export_extras=True,
        export_tangents=False,
    )
    doc, binary = read_glb(target)
    # Preserve the original eight slot order by name, regardless of exporter encounter order.
    names = [m["name"] for m in source_doc["materials"]]
    if sorted(m["name"] for m in doc["materials"]) != sorted(names):
        raise ValueError("material name contract changed")
    old = doc["materials"]
    doc["materials"] = [next(m for m in old if m["name"] == name) for name in names]
    remap = {i: names.index(m["name"]) for i, m in enumerate(old)}
    for mesh in doc["meshes"]:
        for p in mesh["primitives"]:
            p["material"] = remap[p["material"]]
    target.write_bytes(encode_glb(doc, binary))
    player = HERE / "dao_grip_refined.glb"
    player.write_bytes(player_frame(doc, binary))
    components = []
    for name, obj in objects.items():
        before, faces = source[name]
        after, new_faces = snapshot(obj)
        tree = BVHTree.FromPolygons(before, faces, all_triangles=False)
        distance = max(tree.find_nearest(p)[3] for p in after)
        if name in PROTECTED:
            assert len(before) == len(after) and all(
                (a - b).length < 1e-8 for a, b in zip(before, after)
            )
        components.append(
            {
                "source_node": name,
                "candidate_node": name,
                "protected_contact_surface": name in PROTECTED,
                "geometry_changed": name in CHANGED,
                "source_vertices": len(before),
                "candidate_vertices": len(after),
                "source_triangles": sum(len(f) - 2 for f in faces),
                "candidate_triangles": sum(len(f) - 2 for f in new_faces),
                "maximum_candidate_vertex_to_source_surface_mm": distance * 1000,
                "before_bounds_gltf": bounds(before),
                "after_bounds_gltf": bounds(after),
                "materials": [m.name for m in obj.data.materials],
            }
        )
    manifest = {
        "source": str(SOURCE.relative_to(REPO)),
        "source_sha256": SOURCE_SHA,
        "coordinate": "NPC native glTF metres, +Y blade axis; editable Blender Z-up; player identity Grip and blade -Z",
        "anchors_gltf": {
            n["name"]: n.get("translation", [0, 0, 0])
            for n in doc["nodes"]
            if n.get("name") in ("Grip", "Blade_Base", "Blade_Tip")
        },
        "section_stations_metres": stations,
        "section_across_fractions": ACROSS,
        "fuller_width_fraction": 0.11,
        "fuller_depth_fraction_of_half_thickness": 0.38,
        "outer_edge_scope": "apex follows exact original nine-station linear outer profile",
        "components": components,
        "material_slots": names,
        "surface_manifest": str(surface_manifest.relative_to(REPO)),
        "integrated_textures": textures,
        "tangent_exported": any(
            "TANGENT" in p["attributes"] for m in doc["meshes"] for p in m["primitives"]
        ),
        "tangent_contract": "NORMAL and UV0 exported; no TANGENT, client MikkTSpace generation requires SDK visual validation",
        "outputs": {
            p.name: {"sha256": digest(p), "bytes": p.stat().st_size}
            for p in (target, player, blend)
        },
        "limitations": [
            "surface distances are candidate-vertex samples, not continuous Hausdorff bounds",
            "source grip contact pieces remain exact in editable scene; exported float checks separate",
            "offline geometry candidate, runtime visuals/contact remain Root-owned",
        ],
    }
    (HERE / "geometry_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    assert digest(SOURCE) == SOURCE_SHA
    print(
        json.dumps(
            {
                "outputs": manifest["outputs"],
                "triangles": sum(c["candidate_triangles"] for c in components),
                "surface_manifest": manifest["surface_manifest"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface-manifest", type=Path, required=True)
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    build(args.surface_manifest.resolve())
