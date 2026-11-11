"""Independent offline dao geometry, player-frame and actor-preservation checks.

python3 -B ArtSource/refinement/weapon/stage2/verify_geometry.py
Only verification.json is written; no source or candidate is modified.
"""
import argparse
import copy
import hashlib
import io
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from verify_weapon import read, values, local, digest, require

SOURCE_HASH = "0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616"
PLAYER_SOURCE_HASH = "a2a5eae94ef6f577697d6c91a5cd4d7fe22e09e2f8b8e4411cd53768751739fc"
CHANGED = {"Blade", "Blade | shallow fuller", "Blade | asymmetric wear",
           "Guard | flared oval", "Guard | outer rim", "Pommel | brass"}
GRIP = {"Handle core", "Grip | cord wrap", "Grip ferrule", "Pommel ring"}


def path(value):
    result = Path(value)
    return result if result.is_absolute() else REPO / result


def worlds(document):
    parents = {child: i for i, node in enumerate(document["nodes"]) for child in node.get("children", [])}
    result = {}
    def visit(i, seen=()):
        require(i not in seen, "node cycle")
        if i not in result:
            result[i] = visit(parents[i], (*seen, i)) @ local(document["nodes"][i]) if i in parents else local(document["nodes"][i])
        return result[i]
    for i in range(len(document["nodes"])):
        visit(i)
    return result


def components(document, binary):
    transforms, result = worlds(document), {}
    for i, node in enumerate(document["nodes"]):
        if "mesh" not in node:
            continue
        name = node.get("name", str(i))
        require(name not in result, "duplicate mesh node name")
        points, faces, offset = [], [], 0
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            p = values(document, binary, primitive["attributes"]["POSITION"]).astype(float)
            p = (np.column_stack((p, np.ones(len(p)))) @ transforms[i].T)[:, :3]
            f = values(document, binary, primitive["indices"]).reshape(-1, 3).astype(int)
            points.append(p); faces.append(f + offset); offset += len(p)
        result[name] = (np.concatenate(points), np.concatenate(faces))
    return result


def protected_attributes(source, old_binary, candidate, binary, name):
    def primitives(document):
        node = next(n for n in document["nodes"] if n.get("name") == name)
        return document["meshes"][node["mesh"]]["primitives"]
    old, new = primitives(source), primitives(candidate)
    require(len(old) == len(new), "protected primitive count changed: " + name)
    a_world = worlds(source); b_world = worlds(candidate)
    a_index = next(i for i,n in enumerate(source["nodes"]) if n.get("name") == name)
    b_index = next(i for i,n in enumerate(candidate["nodes"]) if n.get("name") == name)
    maximum_normal_error = 0.0
    ordered = True
    for first, second in zip(old, new):
        require(set(first["attributes"]) == set(second["attributes"]), "protected attribute set changed: " + name)
        require(source["materials"][first["material"]]["name"] == candidate["materials"][second["material"]]["name"], "protected material slot changed")
        def triangle_rows(document, payload, primitive, matrix):
            attributes = {key: values(document,payload,index).astype(float) for key,index in primitive["attributes"].items()}
            points = (np.column_stack((attributes["POSITION"],np.ones(len(attributes["POSITION"])))) @ matrix.T)[:,:3]
            normals = attributes["NORMAL"] @ np.linalg.inv(matrix[:3,:3])
            normals /= np.linalg.norm(normals,axis=1)[:,None]
            uv = attributes.get("TEXCOORD_0",np.zeros((len(points),0)))
            faces = values(document,payload,primitive["indices"]).reshape(-1,3)
            rows = {}
            for face in faces:
                corners = np.round(np.column_stack((points[face],uv[face])),8)
                keys = [tuple(np.roll(corners,-shift,axis=0).reshape(-1)) for shift in range(3)]
                shift = min(range(3),key=lambda i:keys[i]); key = keys[shift]
                rows.setdefault(key,[]).append(np.roll(normals[face],-shift,axis=0))
            return attributes, faces, rows
        aa, fa, ar = triangle_rows(source,old_binary,first,a_world[a_index])
        ba, fb, br = triangle_rows(candidate,binary,second,b_world[b_index])
        require(ar.keys() == br.keys() and all(len(ar[k]) == len(br[k]) for k in ar), "protected oriented POSITION/UV triangle multiset changed: " + name)
        for key in ar:
            available = list(br[key])
            for normal in ar[key]:
                pick = min(range(len(available)),key=lambda i:np.max(np.abs(available[i]-normal)))
                maximum_normal_error = max(maximum_normal_error,float(np.max(np.abs(available.pop(pick)-normal))))
        ordered = ordered and fa.shape == fb.shape and np.array_equal(fa,fb) and all(aa[k].shape == ba[k].shape and np.array_equal(aa[k],ba[k]) for k in aa if k != "NORMAL")
    require(maximum_normal_error <= .001, "protected exported normal drift exceeds 0.001: " + name)
    return {"position_uv_oriented_triangle_multiset_preserved": True, "ordered_position_uv_indices_exact": bool(ordered), "normal_max_component_error": maximum_normal_error,
            "normal_tolerance": .001, "mapping": "one-to-one oriented triangle-corner POSITION/UV signatures at 1e-8 units; export vertex splitting allowed, winding retained"}


def nearest_vertices(first, second):
    # Bounded memory; this verifies protected vertices, not general surface depth.
    maximum = 0.0
    for start in range(0, len(first), 128):
        distances = ((first[start:start+128, None] - second[None]) ** 2).sum(axis=2)
        maximum = max(maximum, float(np.sqrt(distances.min(axis=1)).max()))
    return maximum


def protected_delta(first, second):
    a, fa = first; b, fb = second
    return {"source_vertices": len(a), "candidate_vertices": len(b),
            "source_triangles": len(fa), "candidate_triangles": len(fb),
            "symmetric_vertex_gap_mm": 1000 * max(nearest_vertices(a, b), nearest_vertices(b, a)),
            "symmetric_triangle_centroid_gap_mm": 1000 * max(nearest_vertices(a[fa].mean(axis=1), b[fb].mean(axis=1)), nearest_vertices(b[fb].mean(axis=1), a[fa].mean(axis=1)))}


def health(document, binary):
    require(document.get("asset", {}).get("version") == "2.0", "not glTF2")
    for i, accessor in enumerate(document.get("accessors", [])):
        require("sparse" not in accessor, "unsupported sparse accessor")
        data = values(document, binary, i)
        require(np.isfinite(data).all(), "nonfinite accessor " + str(i))
    primitive_rows = []
    for mi, mesh in enumerate(document["meshes"]):
        for pi, primitive in enumerate(mesh["primitives"]):
            require(primitive.get("mode", 4) == 4, "nontriangle primitive")
            attributes = primitive["attributes"]
            p = values(document, binary, attributes["POSITION"]).astype(float)
            require(len(p) > 0 and p.shape[1] == 3, "invalid position shape")
            raw_indices = values(document, binary, primitive["indices"]).reshape(-1)
            require(len(raw_indices) % 3 == 0, "incomplete triangle")
            require(raw_indices.dtype.kind in "ui", "noninteger indices")
            require(raw_indices.min() >= 0 and raw_indices.max() < len(p), "index out of bounds")
            triangles = p[raw_indices.astype(int).reshape(-1, 3)]
            area = .5 * np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]), axis=1)
            for name, index in attributes.items():
                require(len(values(document, binary, index)) == len(p), "attribute count mismatch " + name)
            require(np.all(area > 1e-14), "zero/near-zero area triangle")
            require("NORMAL" in attributes, "lit primitive NORMAL absent")
            if "NORMAL" in attributes:
                lengths = np.linalg.norm(values(document, binary, attributes["NORMAL"]), axis=1)
                require(np.all((lengths > .9) & (lengths < 1.1)), "invalid normal length")
            material_index = primitive.get("material")
            require(isinstance(material_index, int) and 0 <= material_index < len(document["materials"]), "bad material index")
            material = document["materials"][material_index]
            def texture_uvs(value, key=""):
                if isinstance(value, dict):
                    if key.endswith("Texture"):
                        uv = "TEXCOORD_" + str(value.get("texCoord", 0))
                        require(uv in attributes, "textured primitive missing " + uv)
                        require(values(document, binary, attributes[uv]).shape == (len(p), 2), "invalid texture coordinate shape")
                    for k, child in value.items(): texture_uvs(child, k)
                elif isinstance(value, list):
                    for child in value: texture_uvs(child, key)
            texture_uvs(material)
            primitive_rows.append({"mesh": mi, "primitive": pi, "vertices": len(p), "triangles": len(area), "minimum_triangle_area_mesh_local_units_squared": float(area.min())})
    images = []
    from PIL import Image
    for i, image in enumerate(document.get("images", [])):
        require("uri" not in image and "bufferView" in image, "image is not embedded")
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0); payload = binary[start:start+view["byteLength"]]
        require(len(payload) == view["byteLength"], "truncated image")
        with Image.open(io.BytesIO(payload)) as opened:
            width, height = opened.size; opened.verify()
        require(0 < width <= 8192 and 0 < height <= 8192, "image dimensions outside bounded offline scope")
        images.append({"index": i, "name": image.get("name"), "size": [width, height], "sha256": hashlib.sha256(payload).hexdigest()})
    for texture in document.get("textures", []):
        require(0 <= texture.get("source", -1) < len(images), "invalid texture image reference")
    def check_material(value, key=""):
        if isinstance(value, dict):
            if key.endswith("Texture"):
                require(isinstance(value.get("index"), int) and 0 <= value["index"] < len(document.get("textures", [])), "invalid material texture reference")
            for k, child in value.items():
                check_material(child, k)
        elif isinstance(value, list):
            for child in value: check_material(child, key)
        elif isinstance(value, (float, int)):
            if key in ("roughnessFactor", "metallicFactor", "alphaCutoff", "baseColorFactor", "emissiveFactor", "scale", "strength"):
                require(type(value) in (int,float), "boolean used as material number")
            require(math.isfinite(value), "nonfinite material field")
            if key in ("roughnessFactor", "metallicFactor", "alphaCutoff"):
                require(0 <= value <= 1, "out-of-range material scalar")
    for material in document["materials"]: check_material(material)
    return {"accessors_finite": True, "indices_valid": True, "nondegenerate_triangles": True, "primitives": primitive_rows, "embedded_images": images}


def compare_weapon(source, old_binary, candidate, binary, player=False):
    source_components, candidate_components = components(source, old_binary), components(candidate, binary)
    for node in candidate["nodes"]:
        if "mesh" not in node: continue
        primitives = candidate["meshes"][node["mesh"]]["primitives"]
        source_node = next(n for n in source["nodes"] if n.get("name") == node["name"])
        old_primitives = source["meshes"][source_node["mesh"]]["primitives"]
        old_uv_materials = {source["materials"][p["material"]]["name"] for p in old_primitives if "TEXCOORD_0" in p["attributes"]}
        for primitive in primitives:
            require("TANGENT" not in primitive["attributes"], "weapon TANGENT unsupported by actor binding path")
            if candidate["materials"][primitive["material"]]["name"] in old_uv_materials:
                require("TEXCOORD_0" in primitive["attributes"], "source UV surface silently lost UVs")
    require(set(source_components) == set(candidate_components), "mesh object set changed")
    source_names = [m["name"] for m in source["materials"]]
    require(len(set(source_names)) == 8 and set(source_names) == {m["name"] for m in candidate["materials"]}, "eight named material identities changed")
    require(len(source["nodes"]) == len(candidate["nodes"]), "node count changed")
    require(len({n.get("name") for n in candidate["nodes"]}) == len(candidate["nodes"]), "duplicate/missing node names")
    require(len(candidate["materials"]) == 8 and len({m.get("name") for m in candidate["materials"]}) == 8, "material count/uniqueness changed")
    require(all("tripo_" not in m["name"].lower() for m in candidate["materials"]), "body material leaked into dao")
    def hierarchy(document):
        return {document["nodes"][child]["name"]: node["name"] for node in document["nodes"] for child in node.get("children",[])}
    require(hierarchy(source) == hierarchy(candidate), "node parent-child hierarchy changed")
    wa, wb = worlds(source), worlds(candidate)
    named_a = {n["name"]: i for i, n in enumerate(source["nodes"])}
    named_b = {n["name"]: i for i, n in enumerate(candidate["nodes"])}
    require(set(named_a) == set(named_b), "node identities changed")
    for name in named_a:
        require(np.allclose(wa[named_a[name]], wb[named_b[name]], atol=1e-6, rtol=0), "node world transform changed: " + name)
    anchors = {}
    for name in ("Grip", "Blade_Base", "Blade_Tip"):
        require(np.allclose(wa[named_a[name]], wb[named_b[name]], atol=1e-7, rtol=0), "anchor changed: " + name)
        anchors[name] = wb[named_b[name]][:3, 3].tolist()
    delta = np.array(anchors["Blade_Tip"]) - anchors["Blade_Base"]
    require(abs(np.linalg.norm(delta) - .7206756975) < 1e-6, "metre blade marker length changed")
    if player:
        require(np.allclose(wb[named_b["Grip"]], np.eye(4), atol=1e-9), "player Grip not identity")
        require(delta[2] < 0 and abs(delta[1]) < 1e-6, "player blade no longer -Z")
    all_points = np.concatenate([v[0] for v in candidate_components.values()])
    bounds = np.stack((all_points.min(axis=0), all_points.max(axis=0)))
    require(np.abs(all_points).max() < 2, "nonmetre/unbounded knife geometry")
    axial = 2 if player else 1
    old_points = np.concatenate([v[0] for v in source_components.values()])
    require(abs(np.ptp(all_points[:, axial]) - np.ptp(old_points[:, axial])) < 1e-5, "overall axial length changed")
    protected = {}
    for name in sorted(set(source_components) - CHANGED):
        measurement = protected_delta(source_components[name], candidate_components[name])
        require(measurement["symmetric_vertex_gap_mm"] < .0011, "protected grip/contact vertices moved: " + name)
        require(measurement["symmetric_triangle_centroid_gap_mm"] < .0011 and measurement["source_triangles"] == measurement["candidate_triangles"], "protected contact triangle surface changed: " + name)
        measurement.update(protected_attributes(source, old_binary, candidate, binary, name))
        protected[name] = measurement
    return {"health": health(candidate, binary), "anchors_retained": anchors, "all_node_world_transforms_retained": True,
            "blade_marker_length_mm": float(np.linalg.norm(delta)*1000), "bounds_metres": bounds.tolist(),
            "original_grip_contact_components": {n: protected[n] for n in sorted(GRIP)},
            "all_protected_components": protected, "protected_tolerance_mm": .0011,
            "normal_texture_runtime_status": "offline NORMAL/UV/image checks only; SDK tangent generation, MikkTSpace handedness and actual shading unverified"}


def same_accessor(a, ab, ai, b, bb, bi, label):
    sa, sb = a["accessors"][ai], b["accessors"][bi]
    require({k: v for k, v in sa.items() if k not in ("bufferView", "byteOffset")} == {k: v for k, v in sb.items() if k not in ("bufferView", "byteOffset")}, label + " accessor semantic changed")
    va, vb = values(a, ab, ai), values(b, bb, bi)
    require(va.dtype == vb.dtype and va.shape == vb.shape and va.tobytes() == vb.tobytes(), label + " binary changed")


def material_semantics(document, binary, material):
    result = copy.deepcopy(material)
    def visit(value, key=""):
        if isinstance(value,dict):
            if key.endswith("Texture"):
                texture = document["textures"][value.pop("index")]
                image = document["images"][texture["source"]]
                view = document["bufferViews"][image["bufferView"]]
                start = view.get("byteOffset",0)
                value["embedded_image_sha256"] = hashlib.sha256(binary[start:start+view["byteLength"]]).hexdigest()
                value["sampler_semantics"] = document.get("samplers",[])[texture["sampler"]] if "sampler" in texture else None
            for k,child in list(value.items()): visit(child,k)
        elif isinstance(value,list):
            for child in value: visit(child,key)
    visit(result)
    return result


def actor_weapon_bakes(source, old_binary, candidate, binary, entry, weapon_indices, mesh_index):
    canonical_path = path(entry["weapon_source"])
    require(digest(canonical_path) == entry["weapon_source_sha256"], "canonical weapon pin mismatch")
    canonical, payload = read(canonical_path)
    transforms = worlds(canonical)
    mapping = entry["weapon_binding"]["primitive_sources"]
    require(sorted(row["target_primitive"] for row in mapping) == sorted(weapon_indices), "actor weapon primitive mapping is not complete one-to-one")
    names = [source["nodes"][i]["name"] for i in source["skins"][0]["joints"]]
    hand = names.index("R_Hand")
    inverse_bind = values(source,old_binary,source["skins"][0]["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)[hand]
    mount = local(next(node for node in source["nodes"] if node.get("name") == "HandGrip_R"))
    grip = next(i for i,node in enumerate(canonical["nodes"]) if node.get("name") == "Grip")
    shift = np.eye(4); shift[:3,3] = -transforms[grip][:3,3]
    maximum_position = maximum_normal = 0.0
    for row in mapping:
        ni = next(i for i,node in enumerate(canonical["nodes"]) if node.get("name") == row["source_node"])
        source_mesh = canonical["nodes"][ni]["mesh"]
        require(row["source_mesh"] == source_mesh, "bake source mesh mismatch")
        a = canonical["meshes"][source_mesh]["primitives"][row["source_primitive"]]
        b = candidate["meshes"][mesh_index]["primitives"][row["target_primitive"]]
        expected = np.linalg.inv(inverse_bind) @ mount @ shift @ transforms[ni]
        declared = np.array(row["bake_matrix_gltf"]).reshape(4,4).T
        require(np.allclose(expected,declared,atol=2e-6,rtol=0), "declared bake matrix differs from actual rig/Grip frame")
        p = values(canonical,payload,a["attributes"]["POSITION"])
        actual = values(candidate,binary,b["attributes"]["POSITION"])
        predicted = (np.column_stack((p,np.ones(len(p)))) @ expected.T)[:,:3]
        require(predicted.shape == actual.shape, "baked weapon vertex count changed")
        position_error = float(np.max(np.abs(actual-predicted)))
        maximum_position = max(maximum_position,position_error)
        require(position_error <= 2e-6, "actor baked POSITION differs from canonical geometry")
        normal = values(canonical,payload,a["attributes"]["NORMAL"]) @ np.linalg.inv(expected[:3,:3])
        normal /= np.linalg.norm(normal,axis=1)[:,None]
        actual_normal = values(candidate,binary,b["attributes"]["NORMAL"])
        normal_error = float(np.max(np.abs(actual_normal-normal)))
        maximum_normal = max(maximum_normal,normal_error)
        require(normal_error <= 2e-6, "actor baked NORMAL differs from canonical geometry")
        for attribute,index in a["attributes"].items():
            if attribute in ("POSITION","NORMAL"): continue
            same_accessor(canonical,payload,index,candidate,binary,b["attributes"][attribute],"baked weapon "+attribute)
        same_accessor(canonical,payload,a["indices"],candidate,binary,b["indices"],"baked weapon topology")
        require(material_semantics(canonical,payload,canonical["materials"][a["material"]]) == material_semantics(candidate,binary,candidate["materials"][b["material"]]), "baked weapon material/image semantics changed")
    return {"canonical_weapon_sha256": digest(canonical_path), "primitive_count": len(mapping),
        "all_primitive_geometry_indices_uv_materials_matched": True, "bake_independently_derived_from_actual_inverse_bind_mount_and_Grip": True,
        "maximum_position_component_error_mm": maximum_position*1000,"maximum_normal_component_error": maximum_normal}


def compare_actor(a, ab, b, bb, entry):
    require(len(a["meshes"]) == len(b["meshes"]) == 1, "actor mesh count changed")
    require(len(a["materials"]) == len(b["materials"]), "actor material slot count changed")
    require(a["nodes"] == b["nodes"], "actor nodes/rest/anchors changed")
    require(a.get("scenes") == b.get("scenes") and a.get("scene") == b.get("scene"), "actor scene changed")
    require(len(a["skins"]) == len(b["skins"]), "skin count changed")
    for sa, sb in zip(a["skins"], b["skins"]):
        require({k: v for k, v in sa.items() if k != "inverseBindMatrices"} == {k: v for k, v in sb.items() if k != "inverseBindMatrices"}, "skin joints changed")
        same_accessor(a, ab, sa["inverseBindMatrices"], b, bb, sb["inverseBindMatrices"], "inverse binds")
    require(len(a["animations"]) == len(b["animations"]), "animation count changed")
    for ca, cb in zip(a["animations"], b["animations"]):
        require({k: v for k, v in ca.items() if k != "samplers"} == {k: v for k, v in cb.items() if k != "samplers"}, "animation channels changed")
        require(len(ca["samplers"]) == len(cb["samplers"]), "animation sampler count changed")
        for si, (ta, tb) in enumerate(zip(ca["samplers"], cb["samplers"])):
            require(ta.get("interpolation", "LINEAR") == tb.get("interpolation", "LINEAR"), "animation interpolation changed")
            for key in ("input", "output"):
                same_accessor(a, ab, ta[key], b, bb, tb[key], ca["name"] + ":" + str(si) + ":" + key)
    alignment = json.loads(path(entry.get("alignment_source", entry.get("source_alignment", entry.get("alignment", "ArtSource/tripo-warrior/library/"+entry["id"]+"_alignment.json")))).read_text())
    body_indices = alignment["body_primitive_indices"]
    mesh_node = next(n for n in a["nodes"] if n.get("name") == "TripoBody_Mesh")
    mesh_index = mesh_node["mesh"]
    protected_materials = set()
    for index in body_indices:
        pa, pb = a["meshes"][mesh_index]["primitives"][index], b["meshes"][mesh_index]["primitives"][index]
        require({k: v for k, v in pa.items() if k not in ("attributes", "indices")} == {k: v for k, v in pb.items() if k not in ("attributes", "indices")}, "body primitive semantic changed")
        require(set(pa["attributes"]) == set(pb["attributes"]), "body attributes changed")
        for name in pa["attributes"]:
            same_accessor(a, ab, pa["attributes"][name], b, bb, pb["attributes"][name], "body " + name)
        same_accessor(a, ab, pa["indices"], b, bb, pb["indices"], "body topology")
        protected_materials.add(pa["material"])
    for index in protected_materials:
        require(a["materials"][index] == b["materials"][index], "body material changed")
    # Only body texture/image resources are immutable; weapon images may change.
    texture_indices = set()
    def body_textures(value, key=""):
        if isinstance(value, dict):
            if key.endswith("Texture"): texture_indices.add(value["index"])
            for k, child in value.items(): body_textures(child, k)
        elif isinstance(value, list):
            for child in value: body_textures(child, key)
    for index in protected_materials: body_textures(a["materials"][index])
    for ti in texture_indices:
        require(a["textures"][ti] == b["textures"][ti], "body texture reference changed")
        ia = a["textures"][ti]["source"]
        image, ib = a["images"][ia], b["images"][ia]
        require({k:v for k,v in image.items() if k != "bufferView"} == {k:v for k,v in ib.items() if k != "bufferView"}, "body image metadata changed")
        va, vb = a["bufferViews"][image["bufferView"]], b["bufferViews"][ib["bufferView"]]
        require(ab[va.get("byteOffset", 0):va.get("byteOffset", 0)+va["byteLength"]] == bb[vb.get("byteOffset", 0):vb.get("byteOffset", 0)+vb["byteLength"]], "body image bytes changed")
    joint_names = [b["nodes"][index]["name"] for index in b["skins"][0]["joints"]]
    right = joint_names.index("R_Hand")
    weapon_indices = [i for i in range(len(b["meshes"][mesh_index]["primitives"])) if i not in body_indices]
    require(bool(weapon_indices), "actor weapon absent")
    for index in weapon_indices:
        attributes = b["meshes"][mesh_index]["primitives"][index]["attributes"]
        require("TANGENT" not in attributes, "actor weapon TANGENT unsupported")
        palettes = values(b, bb, attributes["JOINTS_0"])
        weights = values(b, bb, attributes["WEIGHTS_0"])
        require(np.all((palettes == right) | (weights == 0)), "weapon influence is not rigid R_Hand")
        require(np.allclose(weights.sum(axis=1), 1, atol=1e-7), "weapon weights not normalized")
    bakes = actor_weapon_bakes(a, ab, b, bb, entry, weapon_indices, mesh_index)
    return {"weapon_canonical_bake_validation": bakes, "body_attributes_and_indices_byte_exact": True, "all_weights_byte_exact": True,
            "nodes_rest_anchors_exact": True, "skin_and_inverse_bind_exact": True,
            "all_animation_times_values_and_interpolation_exact": True, "body_material_exact": True,
            "body_embedded_images_exact": True, "weapon_rigid_R_Hand_palette": right, "weapon_primitive_indices": weapon_indices, "body_primitive_indices": body_indices,
            "offline_candidate_health": health(b, bb)}


def integrated_surfaces(document, binary, manifest_path):
    from PIL import Image
    manifest = json.loads(manifest_path.read_text())
    require(manifest["source"]["sha256"] == SOURCE_HASH, "surface source pin mismatch")
    checked = []
    for material in document["materials"]:
        name = material["name"]
        require(name in manifest["materials"], "material missing from surface manifest")
        declaration = manifest["materials"][name]
        pbr = material.get("pbrMetallicRoughness",{})
        require(pbr.get("baseColorFactor",[1,1,1,1]) == [1,1,1,1], "absolute base color multiplied by tint")
        require(pbr.get("roughnessFactor",1) == 1 and pbr.get("metallicFactor",1) == 1, "absolute MR map multiplied twice")
        roles = {}
        for role, field in (("base_color","baseColorTexture"),("metallic_roughness","metallicRoughnessTexture"),("normal","normalTexture")):
            if role not in declaration["textures"]: continue
            binding = material.get(field) if role == "normal" else pbr.get(field)
            require(isinstance(binding,dict), "surface role not bound: "+name+":"+role)
            require(binding.get("texCoord",0) == declaration["textures"][role].get("texCoord",0), "texture UV set mismatch")
            if role == "normal": require(abs(binding.get("scale",1)-declaration["textures"][role].get("scale",1)) < 1e-7, "normal scale mismatch")
            texture = document["textures"][binding["index"]]
            image = document["images"][texture["source"]]
            view = document["bufferViews"][image["bufferView"]]; start = view.get("byteOffset",0)
            raw = binary[start:start+view["byteLength"]]
            with Image.open(io.BytesIO(raw)) as im: embedded = np.array(im.convert("RGBA"))
            with Image.open(path(declaration["textures"][role]["path"])) as im: expected = np.array(im.convert("RGBA"))
            require(embedded.shape == expected.shape and np.array_equal(embedded,expected), "embedded texture pixels differ from declared role: "+name+":"+role)
            if role == "metallic_roughness":
                with Image.open(path(declaration["textures"]["roughness"]["path"])) as im: roughness = np.array(im.convert("RGB"))[:,:,0]
                require(np.all(embedded[:,:,0] == 255) and np.array_equal(embedded[:,:,1],roughness), "MR channel convention violated (R neutral/G roughness)")
            roles[role] = {"texture_index":binding["index"],"image_index":texture["source"],"pixel_exact_to_declared_map":True,"size":[embedded.shape[1],embedded.shape[0]]}
        checked.append({"material":name,"absolute_factors_all_one":True,"roles":roles})
    return {"source_manifest":str(manifest_path.relative_to(REPO)),"material_roles":checked,
            "channel_contract":"baseColor sRGB; MR G=roughness B=metallic and normal RGB linear by glTF slot semantics; encoded pixels match manifest maps",
            "runtime_unverified":"SDK-generated tangents/MikkTSpace compatibility, normal handedness and PICO appearance not executed"}


def negative_tests(source, old_binary, candidate, binary):
    mutations = []
    anchor = copy.deepcopy(candidate)
    node = next(n for n in anchor["nodes"] if n.get("name") == "Blade_Tip")
    if "matrix" in node: node["matrix"][12] += .001
    else: node.setdefault("translation", [0,0,0])[0] += .001
    try: compare_weapon(source, old_binary, anchor, binary)
    except (ValueError, IndexError): mutations.append("anchor_translation_1mm")
    else: raise ValueError("negative anchor test accepted")
    index = candidate["meshes"][0]["primitives"][0]["attributes"]["POSITION"]
    spec = candidate["accessors"][index]; view = candidate["bufferViews"][spec["bufferView"]]
    offset = spec.get("byteOffset", 0) + view.get("byteOffset", 0)
    bad = bytearray(binary); bad[offset:offset+4] = np.array([float("nan")], dtype="<f4").tobytes()
    try: health(candidate, bytes(bad))
    except ValueError: mutations.append("nonfinite_position")
    else: raise ValueError("negative NaN test accepted")
    bad_index = copy.deepcopy(candidate)
    accessor = bad_index["accessors"][bad_index["meshes"][0]["primitives"][0]["indices"]]
    view = bad_index["bufferViews"][accessor["bufferView"]]
    width = {5121: 1, 5123: 2, 5125: 4}[accessor["componentType"]]
    offset = accessor.get("byteOffset", 0) + view.get("byteOffset", 0)
    bad = bytearray(binary); bad[offset:offset+width] = ((1 << (8*width))-1).to_bytes(width, "little")
    try: health(bad_index, bytes(bad))
    except ValueError: mutations.append("out_of_range_triangle_index")
    else: raise ValueError("negative index test accepted")
    return {"normal_candidate_passed": True, "mutations_rejected": mutations}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actors", type=Path, default=HERE/"actor_manifest.json")
    parser.add_argument("--out", type=Path, default=HERE/"verification.json")
    args = parser.parse_args()
    report = {"scope": "Independent finite offline structural geometry and actor preservation audit; contact in contact_audit.json", "weapons": {}, "actors": [], "errors": []}
    report["triangle_area_units_note"] = "Primitive health areas are measured before node transforms, in mesh-local coordinate units squared; nonuniform/scaled nodes mean these values must not be read as world square metres. Contact distances and affected hand-face areas are separately measured after actual LBS world transforms."
    snapshots = {}
    weapon_documents = {}
    geometry_manifest = HERE/"geometry_manifest.json"
    if geometry_manifest.exists():
        gm = json.loads(geometry_manifest.read_text())
        report["geometry_manifest_source_pin"] = gm.get("source_sha256") == SOURCE_HASH
        for filename, info in gm.get("outputs",{}).items():
            if filename.endswith(".glb") and (HERE/filename).exists():
                require(digest(HERE/filename) == info["sha256"], "geometry manifest output pin mismatch")
        report["integrated_surface_manifest"] = gm.get("surface_manifest")
        if not gm.get("surface_manifest"): report["errors"].append("final integrated texture surface manifest not ready")
    else: report["errors"].append("geometry manifest not ready")
    for name, source_path, candidate_path, pin, player in (
        ("npc", REPO/"ArtSource/dao/dao_study.glb", HERE/"dao_refined.glb", SOURCE_HASH, False),
        ("player", REPO/"ArtSource/dao/dao_grip.glb", HERE/"dao_grip_refined.glb", PLAYER_SOURCE_HASH, True)):
        if not candidate_path.exists():
            report["errors"].append(name+" candidate not ready"); continue
        try:
            snapshots[source_path] = digest(source_path); snapshots[candidate_path] = digest(candidate_path)
            require(snapshots[source_path] == pin, name+" source pin mismatch")
            a, ab = read(source_path); b, bb = read(candidate_path)
            weapon_documents[name] = (b,bb)
            check = compare_weapon(a, ab, b, bb, player)
            if report.get("integrated_surface_manifest"):
                check["integrated_surfaces"] = integrated_surfaces(b,bb,path(report["integrated_surface_manifest"]))
            if not player: report["failure_tests"] = negative_tests(a, ab, b, bb)
            report["weapons"][name] = {"source_sha256": pin, "candidate_sha256": snapshots[candidate_path], **check}
        except Exception as error:
            report["errors"].append(name+": "+str(error))
    if set(report["weapons"]) == {"npc","player"}:
        npc, npc_binary = weapon_documents["npc"]
        player, player_binary = weapon_documents["player"]
        try:
            require(npc_binary == player_binary, "player frame geometry/image binary differs from NPC")
            require({k:v for k,v in npc.items() if k not in ("nodes","scenes","scene")} == {k:v for k,v in player.items() if k not in ("nodes","scenes","scene")}, "player frame non-frame resources differ from NPC")
            report["weapons"]["player"]["same_canonical_geometry_and_embedded_material_resources_as_npc"] = True
        except ValueError as error: report["errors"].append(str(error))
    if args.actors.exists():
        manifest = json.loads(args.actors.read_text())
        for entry in manifest["actors"]:
            record = {"id": entry["id"]}
            try:
                source, candidate = path(entry["source"]), path(entry["candidate"])
                snapshots[source], snapshots[candidate] = digest(source), digest(candidate)
                require(snapshots[source] == entry["source_sha256"] and snapshots[candidate] == entry["candidate_sha256"], "actor manifest pin mismatch")
                require(digest(path(entry["alignment_source"])) == entry["alignment_sha256"], "actor alignment pin mismatch")
                a, ab = read(source); b, bb = read(candidate)
                record.update(compare_actor(a, ab, b, bb, entry))
                record.update(source_sha256=snapshots[source], candidate_sha256=snapshots[candidate], passed=True)
            except Exception as error:
                record.update(passed=False, error=str(error)); report["errors"].append(entry["id"]+": "+str(error))
            report["actors"].append(record)
    else: report["errors"].append("actor manifest not ready")
    report["stable_input_snapshot"] = all(digest(p) == h for p,h in snapshots.items())
    if not report["stable_input_snapshot"]: report["errors"].append("input changed during verification")
    report["passed"] = not report["errors"] and len(report["weapons"]) == 2 and len(report["actors"]) == 3
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({"passed": report["passed"], "weapons": list(report["weapons"]), "actors": [{"id": r["id"], "passed": r["passed"], "error": r.get("error")} for r in report["actors"]], "errors": report["errors"]}))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
