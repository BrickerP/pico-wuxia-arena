"""Validate imported PBR wiring and Blender TBN, then render normal-map A/B.

The normal-off images are display-only debugging variants. Source GLB bytes
and metallic/roughness connections remain intact throughout the comparison.
"""

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_review import VIEWS, import_character, set_camera, studio

sys.path.insert(0, str(HERE.parents[1] / "tripo-warrior"))
from prepare_rigged_warrior import read_glb


def linked(socket, node_type):
    if len(socket.links) != 1:
        raise ValueError(f"Expected one connection into {socket.node.name}/{socket.name}")
    link = socket.links[0]
    if link.from_node.bl_idname != node_type:
        raise ValueError(f"Unexpected node feeding {socket.node.name}/{socket.name}")
    return link


def embedded_dimensions(payload, mime_type):
    if mime_type == "image/png":
        if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
            raise ValueError("Invalid embedded PNG header")
        return list(struct.unpack_from(">II", payload, 16))
    if mime_type != "image/jpeg" or payload[:2] != b"\xff\xd8":
        raise ValueError("Expected an embedded PNG or JPEG image")
    offset = 2
    frame_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                     0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset < len(payload):
        if payload[offset] != 0xFF:
            raise ValueError("Invalid embedded JPEG marker")
        while offset < len(payload) and payload[offset] == 0xFF:
            offset += 1
        marker = payload[offset]
        offset += 1
        if marker in {0xD9, 0xDA}:
            break
        length = struct.unpack_from(">H", payload, offset)[0]
        if length < 2 or offset + length > len(payload):
            raise ValueError("Invalid embedded JPEG segment length")
        if marker in frame_markers:
            height, width = struct.unpack_from(">HH", payload, offset + 3)
            return [width, height]
        offset += length
    raise ValueError("Embedded JPEG contains no frame dimensions")


def image_record(image, source_hashes, source_dimensions):
    if image.packed_file is None:
        raise ValueError(f"Imported image is not packed: {image.name}")
    digest = hashlib.sha256(image.packed_file.data).hexdigest()
    if digest not in source_hashes:
        raise ValueError(f"Imported image bytes do not match source GLB: {image.name}")
    return {
        "blender_name": image.name, "source_image_index": source_hashes[digest],
        "sha256": digest, "dimensions": list(image.size),
        "embedded_header_dimensions": source_dimensions[source_hashes[digest]],
        "color_space": image.colorspace_settings.name,
    }


def material_record(material, source_hashes, source_dimensions):
    nodes = material.node_tree.nodes
    shaders = [node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"]
    if len(shaders) != 1:
        raise ValueError("Expected one Principled BSDF in each character material")
    shader = shaders[0]
    base = linked(shader.inputs["Base Color"], "ShaderNodeTexImage").from_node
    normal_link = linked(shader.inputs["Normal"], "ShaderNodeNormalMap")
    normal = normal_link.from_node
    normal_image = linked(normal.inputs["Color"], "ShaderNodeTexImage").from_node
    metallic = linked(shader.inputs["Metallic"], "ShaderNodeSeparateColor")
    roughness = linked(shader.inputs["Roughness"], "ShaderNodeSeparateColor")
    if metallic.from_node != roughness.from_node:
        raise ValueError("Metallic and roughness must share the source MR image")
    separator = metallic.from_node
    mr_image = linked(separator.inputs["Color"], "ShaderNodeTexImage").from_node
    record = {
        "name": material.name,
        "base_color": image_record(base.image, source_hashes, source_dimensions),
        "normal": image_record(normal_image.image, source_hashes, source_dimensions),
        "metallic_roughness": image_record(mr_image.image, source_hashes, source_dimensions),
        "normal_space": normal.space,
        "normal_strength": normal.inputs["Strength"].default_value,
        "normal_connected_to_principled": normal_link.from_socket.name == "Normal",
        "metallic_channel": metallic.from_socket.name,
        "roughness_channel": roughness.from_socket.name,
        "separator_mode": separator.mode,
        "links": [[link.from_node.name, link.from_socket.name,
                   link.to_node.name, link.to_socket.name] for link in material.node_tree.links],
    }
    image = normal_image.image
    width, height = image.size
    samples = []
    for y in range(8):
        for x in range(8):
            px = min(width - 1, int((x + .5) * width / 8))
            py = min(height - 1, int((y + .5) * height / 8))
            offset = (py * width + px) * image.channels
            samples.append(list(image.pixels[offset:offset + 3]))
    deviation = max(max(abs(rgb[0] - .5), abs(rgb[1] - .5)) for rgb in samples)
    record["normal_pixel_samples"] = {
        "grid": [8, 8], "sample_count": len(samples),
        "max_xy_deviation_from_flat": deviation,
        "rgb_min": [min(rgb[axis] for rgb in samples) for axis in range(3)],
        "rgb_max": [max(rgb[axis] for rgb in samples) for axis in range(3)],
        "non_flat_sample_found": deviation > .02,
        "python_pixel_count_read": len(samples) * 3,
    }
    checks = {
        "normal_image_mapping": record["normal"]["source_image_index"] == 0,
        "base_color_image_mapping": record["base_color"]["source_image_index"] == 1,
        "mr_image_mapping": record["metallic_roughness"]["source_image_index"] == 2,
        "normal_dimensions": record["normal"]["dimensions"] == record["normal"]["embedded_header_dimensions"],
        "base_color_dimensions": record["base_color"]["dimensions"] == record["base_color"]["embedded_header_dimensions"],
        "mr_dimensions": record["metallic_roughness"]["dimensions"] == record["metallic_roughness"]["embedded_header_dimensions"],
        "normal_tangent_space": normal.space == "TANGENT",
        "normal_strength_positive": normal.inputs["Strength"].default_value > 0,
        "normal_non_color": record["normal"]["color_space"] == "Non-Color",
        "mr_non_color": record["metallic_roughness"]["color_space"] == "Non-Color",
        "base_color_srgb": record["base_color"]["color_space"] == "sRGB",
        "metallic_blue": metallic.from_socket.name == "Blue",
        "roughness_green": roughness.from_socket.name == "Green",
        "normal_not_all_flat": record["normal_pixel_samples"]["non_flat_sample_found"],
    }
    record["checks"] = checks
    return record, (material.node_tree, normal_link.from_socket, normal_link.to_socket)


def tangent_record(mesh):
    uv = mesh.uv_layers.active
    if uv is None:
        raise ValueError(f"No active UV map on {mesh.name}")
    mesh.calc_tangents(uvmap=uv.name)
    maximum_error = 0
    minimum_length = math.inf
    maximum_length = 0
    finite = True
    valid_signs = True
    for loop in mesh.loops:
        tangent, normal = loop.tangent, loop.normal
        finite &= all(math.isfinite(value) for value in (*tangent, *normal, loop.bitangent_sign))
        maximum_error = max(maximum_error, abs(tangent.dot(normal)))
        minimum_length = min(minimum_length, tangent.length)
        maximum_length = max(maximum_length, tangent.length)
        valid_signs &= abs(abs(loop.bitangent_sign) - 1) < 1e-6
    checks = {
        "finite_tangents_and_normals": finite,
        "orthogonal": maximum_error < 1e-4,
        "unit_tangents": minimum_length > .999 and maximum_length < 1.001,
        "valid_bitangent_signs": valid_signs,
    }
    return {"mesh": mesh.name, "uv_map": uv.name, "loop_count": len(mesh.loops),
            "max_orthogonality_error": maximum_error,
            "tangent_length_range": [minimum_length, maximum_length], "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE / "mobile/model.glb")
    parser.add_argument("--output", type=Path, default=HERE / "material_review")
    parser.add_argument("--report", type=Path, default=HERE / "material_validation.json")
    parser.add_argument("--yaw", type=float, default=-90)
    parser.add_argument("--size", type=int, default=768)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    document, binary = read_glb(args.source)
    source_hashes = {}
    source_dimensions = {}
    for index, image in enumerate(document["images"]):
        view = document["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        payload = binary[start:start + view["byteLength"]]
        digest = hashlib.sha256(payload).hexdigest()
        source_hashes[digest] = index
        source_dimensions[index] = embedded_dimensions(payload, image["mimeType"])
    source_materials = []
    for material in document["materials"]:
        pbr = material["pbrMetallicRoughness"]
        roles = {"normal": material["normalTexture"]["index"],
                 "base_color": pbr["baseColorTexture"]["index"],
                 "metallic_roughness": pbr["metallicRoughnessTexture"]["index"]}
        source_materials.append({
            "name": material.get("name"),
            "roles": {role: {"texture_index": texture,
                              "image_index": document["textures"][texture]["source"],
                              "mime_type": document["images"][document["textures"][texture]["source"]]["mimeType"]}
                      for role, texture in roles.items()},
            "occlusion_texture_present": "occlusionTexture" in material,
        })
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = import_character(args.source, args.yaw)
    meshes = [obj for obj in bpy.context.scene.objects if obj.name in source["mesh_names"]]
    materials = {material.name: material for obj in meshes for material in obj.data.materials}
    records, normal_connections = [], []
    for material in materials.values():
        record, connection = material_record(material, source_hashes, source_dimensions)
        records.append(record)
        normal_connections.append(connection)
    tangents = [tangent_record(obj.data) for obj in meshes]
    scene, camera = studio(args.size)
    args.output.mkdir(parents=True, exist_ok=True)
    renders = {}
    for variant in ("normal_on", "normal_off"):
        if variant == "normal_off":
            for tree, output, input_socket in normal_connections:
                tree.links.remove(input_socket.links[0])
        renders[variant] = {}
        for name in ("head", "right_hand_top", "left_hand_top"):
            set_camera(camera, *VIEWS[name])
            image = args.output / f"{variant}_{name}.png"
            scene.render.filepath = str(image.resolve())
            bpy.ops.render.render(write_still=True)
            renders[variant][name] = str(image.resolve())
    for tree, output, input_socket in normal_connections:
        tree.links.new(output, input_socket)
    material_checks = [value for record in records for value in record["checks"].values()]
    tangent_checks = [value for record in tangents for value in record["checks"].values()]
    report = {
        "scope": "Blender offline PBR and generated tangent-basis validation",
        "source": source, "source_material_mapping": source_materials,
        "source_primitive_attributes": [list(primitive["attributes"]) for mesh in document["meshes"]
                                        for primitive in mesh["primitives"]],
        "materials": records, "tangent_bases": tangents,
        "all_material_and_tangent_checks_passed": all(material_checks + tangent_checks),
        "debug_variant": "normal_off disconnects only the Principled Normal input; MR links remain connected",
        "source_sha256_after_render": hashlib.sha256(args.source.read_bytes()).hexdigest(),
        "source_bytes_preserved": hashlib.sha256(args.source.read_bytes()).hexdigest() == source["source_sha256"],
        "renders": renders,
        "sdk_tangent_basis_and_material_playback": "pending main validation",
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    if not report["all_material_and_tangent_checks_passed"]:
        raise RuntimeError("A material or tangent-basis validation check failed; see the report")


if __name__ == "__main__":
    main()
