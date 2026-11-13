"""Independent scalar-only weapon material and private-actor verification.

Run with host python3; only verification.json in this directory is written.
"""
import argparse
import copy
import hashlib
import json
import math
import struct
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SOURCE = REPO / "ArtSource/dao/dao_study.glb"
SOURCE_HASH = "0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616"
PLAYER_SOURCE_HASH = "a2a5eae94ef6f577697d6c91a5cd4d7fe22e09e2f8b8e4411cd53768751739fc"
BASE_GUARD_SOURCE_HASH = "34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896"
EXPECTED = {
    "Steel | forged body": {"roughnessFactor": .30},
    "Steel | sharpened edge": {"roughnessFactor": .19, "metallicFactor": 1.0},
    "Steel | dark spine": {"roughnessFactor": .45},
    "Brass | aged": {"roughnessFactor": .55},
    "Steel | uneven wear": {},
    "Brass | polished ridges": {"roughnessFactor": .35},
    "Grip | worn cord": {"roughnessFactor": .80},
    "Grip | dark oxblood leather": {"roughnessFactor": .72},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    data = path.read_bytes()
    magic, version, size = struct.unpack_from("<4sII", data)
    require(magic == b"glTF" and version == 2 and size == len(data), "invalid GLB header")
    offset, document, binary = 12, None, None
    while offset < len(data):
        length, kind = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        require(len(chunk) == length, "truncated GLB chunk")
        if kind == 0x4E4F534A:
            document = json.loads(chunk)
        elif kind == 0x004E4942:
            binary = chunk
        offset += 8 + length
    require(document is not None and binary is not None and offset == len(data), "missing GLB chunks")
    return document, binary


def values(document, binary, index):
    spec = document["accessors"][index]
    view = document["bufferViews"][spec["bufferView"]]
    dtype = np.dtype({5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[spec["componentType"]])
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}[spec["type"]]
    return np.ndarray((spec["count"], width), dtype=dtype, buffer=binary,
        offset=view.get("byteOffset", 0) + spec.get("byteOffset", 0),
        strides=(view.get("byteStride", width * dtype.itemsize), dtype.itemsize)).copy()


def local(node):
    if "matrix" in node:
        return np.array(node["matrix"]).reshape(4, 4).T
    x, y, z, w = node.get("rotation", (0, 0, 0, 1))
    rotation = np.array(((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)),
                         (2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)),
                         (2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y))))
    result = np.eye(4)
    result[:3, :3] = rotation @ np.diag(node.get("scale", (1, 1, 1)))
    result[:3, 3] = node.get("translation", (0, 0, 0))
    return result


def geometry(document, binary, section_levels=(.03, .15, .35, .55, .70)):
    parents = {child: index for index, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    worlds = {}
    def world(index):
        if index not in worlds:
            worlds[index] = world(parents[index]) @ local(document["nodes"][index]) if index in parents else local(document["nodes"][index])
        return worlds[index]
    meshes = []
    for index, node in enumerate(document["nodes"]):
        if "mesh" not in node:
            continue
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            points = values(document, binary, primitive["attributes"]["POSITION"])
            points = (np.column_stack((points, np.ones(len(points)))) @ world(index).T)[:, :3]
            triangles = values(document, binary, primitive["indices"]).reshape(-1, 3).astype(int)
            meshes.append((node["name"], document["materials"][primitive["material"]]["name"], points, triangles))
    def bounds(points):
        low, high = points.min(axis=0), points.max(axis=0)
        return {"minimum_metres": low.tolist(), "maximum_metres": high.tolist(), "size_mm": ((high-low)*1000).tolist()}
    sections = []
    for y in section_levels:
        samples = []
        for name, material, points, faces in meshes:
            if name != "Blade":
                continue
            intersections = []
            for triangle in points[faces]:
                for a, b in ((0, 1), (1, 2), (2, 0)):
                    first, second = triangle[a], triangle[b]
                    if abs(first[1] - y) < 1e-9:
                        intersections.append(first)
                    if (first[1] - y) * (second[1] - y) < 0:
                        intersections.append(first + (second-first) * ((y-first[1])/(second[1]-first[1])))
            if intersections:
                samples.append((material, np.array(intersections)))
        sections.append({"axis_y_metres": y, "whole_blade": bounds(np.concatenate([p for _, p in samples])),
                         "material_surface_sections": {name: bounds(points) for name, points in samples}})
    anchors = {node["name"]: world(index)[:3, 3].tolist() for index, node in enumerate(document["nodes"])
               if node.get("name") in ("Grip", "Blade_Base", "Blade_Tip")}
    delta = np.array(anchors["Blade_Tip"]) - anchors["Blade_Base"]
    principal = int(np.argmax(abs(delta)))
    return {"coordinate_frame": "native glTF metres; dominant blade axis " + ("+" if delta[principal] >= 0 else "-") + "XYZ"[principal],
        "mesh_count": len(document["meshes"]), "triangle_count": sum(len(faces) for _, _, _, faces in meshes),
        "bounds": bounds(np.concatenate([points for _, _, points, _ in meshes])), "anchors": anchors,
        "blade_marker_length_mm": float(np.linalg.norm(np.array(anchors["Blade_Tip"])-anchors["Blade_Base"])*1000),
        "blade_sections": sections,
        "guard": {name: bounds(np.concatenate([points for n, _, points, _ in meshes if n == name]))
                  for name in ("Guard | flared oval", "Guard | outer rim")},
        "cord": {"bounds": bounds(np.concatenate([points for n, _, points, _ in meshes if n == "Grip | cord wrap"])),
                 "vertices": sum(len(points) for n, _, points, _ in meshes if n == "Grip | cord wrap"),
                 "triangles": sum(len(faces) for n, _, _, faces in meshes if n == "Grip | cord wrap")},
        "measurement_scope": "actual unchanged mesh bounds/sections, not a new edge bevel or physical material-thickness refinement"}


def verify(source, old_binary, candidate, binary, actor=False):
    a, b = copy.deepcopy(source), copy.deepcopy(candidate)
    old_materials, new_materials = a.pop("materials"), b.pop("materials")
    require(a == b, "nonmaterial JSON changed (nodes/anchors/meshes/skin/animation/textures)")
    require(old_binary == binary, "geometry/skin/curve/image binary changed")
    require(len(old_materials) == len(new_materials), "material count changed")
    require(len({m["name"] for m in old_materials}) == len(old_materials), "ambiguous duplicate material names")
    matched, changes = set(), []
    for index, (old, new) in enumerate(zip(old_materials, new_materials)):
        name = old["name"]
        if name not in EXPECTED:
            require(actor and old == new, "body/unmatched material changed")
            continue
        matched.add(name)
        expected = copy.deepcopy(old)
        pbr = expected.setdefault("pbrMetallicRoughness", {})
        delta = {}
        for key, value in EXPECTED[name].items():
            require(math.isfinite(value) and 0 <= value <= 1, "invalid bounded PBR scalar")
            actual = new.get("pbrMetallicRoughness", {}).get(key)
            require(type(actual) in (int, float) and math.isfinite(actual) and 0 <= actual <= 1,
                    "candidate PBR field is not a finite numeric scalar")
            before = pbr.get(key, 1.0)
            require(abs(value-before) <= (.100001 if key == "roughnessFactor" else .020001), "PBR delta exceeds reviewed bound")
            pbr[key] = value
            delta[key] = {"before": before, "after": value}
        require(expected == new, "material update exceeds reviewed scalar fields: " + name)
        changes.append({"index": index, "name": name, "scalars": delta})
    require(matched == set(EXPECTED), "missing weapon material match")
    return {"binary_exact": True, "all_nonmaterial_json_exact": True,
            "body_and_unmatched_materials_exact": True, "weapon_material_changes": changes}


def rejection_tests(source, old_binary, candidate, binary):
    verify(source, old_binary, candidate, binary)
    tests = []
    for label in ("anchor", "mesh", "source_binary"):
        changed, payload, source_payload = copy.deepcopy(candidate), binary, old_binary
        if label == "anchor":
            next(node for node in changed["nodes"] if node.get("name") == "Blade_Tip")["translation"][0] += .001
        elif label == "mesh":
            changed["meshes"][0]["primitives"][0]["attributes"]["POSITION"] += 1
        else:
            source_payload = bytes([old_binary[0] ^ 1]) + old_binary[1:]
        try:
            verify(source, source_payload, changed, payload)
        except ValueError:
            tests.append(label)
            continue
        raise ValueError("negative test failed to reject " + label)
    return {"valid_candidate_passed": True, "mutations_rejected": tests}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actors", type=Path)
    args = parser.parse_args()
    candidate_path = HERE / "dao_response.glb"
    require(digest(SOURCE) == SOURCE_HASH, "formal dao identity changed")
    source, old_binary = read(SOURCE)
    candidate, binary = read(candidate_path)
    candidate_hash = digest(candidate_path)
    result = {"scope": "independent material-only weapon validation; offline appearance/runtime still separately reviewed",
        "source_sha256": SOURCE_HASH, "candidate_sha256": candidate_hash,
        "source_binary_sha256": hashlib.sha256(old_binary).hexdigest(),
        "weapon": verify(source, old_binary, candidate, binary), "source_geometry": geometry(source, old_binary),
        "failure_tests": rejection_tests(source, old_binary, candidate, binary), "actors": []}
    player_source_path = REPO / "ArtSource/dao/dao_grip.glb"
    player_candidate_path = HERE / "dao_grip_response.glb"
    if player_candidate_path.exists():
        player_source_hash, player_candidate_hash = digest(player_source_path), digest(player_candidate_path)
        require(player_source_hash == PLAYER_SOURCE_HASH, "formal player Grip source changed")
        player_source, player_old_binary = read(player_source_path)
        player_candidate, player_binary = read(player_candidate_path)
        player_check = verify(player_source, player_old_binary, player_candidate, player_binary)
        player_geometry = geometry(player_source, player_old_binary, section_levels=())
        require(np.linalg.norm(player_geometry["anchors"]["Grip"]) < 1e-9, "player Grip is not identity origin")
        require(player_geometry["coordinate_frame"].endswith("-Z"), "player blade frame changed")
        require(digest(player_source_path) == player_source_hash and digest(player_candidate_path) == player_candidate_hash,
                "player format changed during audit")
        result["player_format"] = {"source_sha256": player_source_hash, "candidate_sha256": player_candidate_hash,
            "frame_and_anchors_retained": True, "geometry": player_geometry, **player_check}
    if args.actors:
        result["actors_manifest"] = str(args.actors)
        manifest = json.loads(args.actors.read_text())
        require({row["id"] for row in manifest["actors"]} == {"base", "indigo", "veteran"}
                and len(manifest["actors"]) == 3, "expected three distinct actor identities")
        for row in manifest["actors"]:
            before_path, after_path = REPO / row["source"], REPO / row["candidate"]
            before_hash, after_hash = digest(before_path), digest(after_path)
            require(before_hash == row["source_sha256"] and after_hash == row["candidate_sha256"], "private actor identity mismatch")
            if row["id"] == "base":
                require(before_hash == BASE_GUARD_SOURCE_HASH, "base actor is not the approved guard preview")
            before, before_binary = read(before_path)
            after, after_binary = read(after_path)
            record = verify(before, before_binary, after, after_binary, actor=True)
            require(digest(before_path) == before_hash and digest(after_path) == after_hash, "actor changed during audit")
            result["actors"].append({"id": row["id"], "source_sha256": before_hash,
                "candidate_sha256": after_hash, "skin_joints": len(before.get("skins", [{}])[0].get("joints", [])),
                "animation_names": [clip["name"] for clip in before.get("animations", [])], **record})
    result["actor_verification_complete"] = len(result["actors"]) == 3
    require(digest(SOURCE) == SOURCE_HASH and digest(candidate_path) == candidate_hash, "dao changed during audit")
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"weapon_verified": True, "actors_verified": len(result["actors"]),
        "anchors": result["source_geometry"]["anchors"], "blade_marker_mm": result["source_geometry"]["blade_marker_length_mm"],
        "bounds_mm": result["source_geometry"]["bounds"]["size_mm"], "negative_tests": result["failure_tests"]}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        (HERE / "verification.json").write_text(json.dumps({"status": "FAILED", "error": str(error)}, indent=2) + "\n")
        raise
