"""Render source PBR and fine triangle-edge overlays for localized UV defects."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from render_review import import_character, set_camera, studio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE / "mobile60k/model.glb")
    parser.add_argument("--evidence", type=Path, default=HERE / "material60k_review/tangent_anomalies.json")
    parser.add_argument("--output", type=Path, default=HERE / "material60k_review")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    evidence = json.loads(args.evidence.read_text())
    digest = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if digest != evidence["source_sha256"]:
        raise ValueError("Source GLB does not match the localized anomaly evidence")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = import_character(args.source, -90)
    objects = [obj for obj in bpy.context.scene.objects if obj.name in source["mesh_names"]]
    if len(objects) != 1:
        raise ValueError("Expected the single localized character mesh")
    obj = objects[0]
    mesh = obj.data
    mesh.calc_tangents(uvmap=mesh.uv_layers.active.name)
    scene, camera = studio(768)
    args.output.mkdir(parents=True, exist_ok=True)
    red = bpy.data.materials.new("Debug-only triangle boundary")
    red.use_nodes = True
    shader = red.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (1, .005, .005, 1)
    shader.inputs["Emission Color"].default_value = (1, .005, .005, 1)
    shader.inputs["Emission Strength"].default_value = 2
    regions = {}
    normal_matrix = obj.matrix_world.to_3x3().inverted().transposed()
    for row in evidence["rows"]:
        region = regions.setdefault(row["region"], {"polygons": [], "points": [], "normals": []})
        polygon = mesh.polygons[row["polygon"]]
        region["polygons"].append(polygon.index)
        region["points"].extend(obj.matrix_world @ mesh.vertices[index].co for index in polygon.vertices)
        region["normals"].extend(normal_matrix @ mesh.corner_normals[index].vector for index in polygon.loop_indices)
    manifest = {
        "source": source, "scope": "actual PBR and display-only localized triangle-edge overlay",
        "triangle_count": len(evidence["rows"]), "orthographic_scale_metres": .04,
        "line_radius_metres": .00002, "line_camera_offset_metres": .00002, "regions": {},
    }
    for region_name, region in regions.items():
        centre = sum(region["points"], Vector()) / len(region["points"])
        outward = sum(region["normals"], Vector()).normalized()
        set_camera(camera, centre, centre + outward * .30, .04)
        key = region_name.replace(" ", "_")
        original = args.output / f"anomaly_{key}_pbr.png"
        scene.render.filepath = str(original.resolve())
        bpy.ops.render.render(write_still=True)
        lines = []
        for polygon_index in region["polygons"]:
            polygon = mesh.polygons[polygon_index]
            curve = bpy.data.curves.new(f"Anomaly edge {polygon_index}", "CURVE")
            curve.dimensions = "3D"
            curve.bevel_depth = .00002
            curve.bevel_resolution = 1
            curve.materials.append(red)
            spline = curve.splines.new("POLY")
            spline.points.add(len(polygon.vertices) - 1)
            for point, vertex_index in zip(spline.points, polygon.vertices):
                position = obj.matrix_world @ mesh.vertices[vertex_index].co + outward * .00002
                point.co = (*position, 1)
            spline.use_cyclic_u = True
            line = bpy.data.objects.new(curve.name, curve)
            scene.collection.objects.link(line)
            lines.append(line)
        overlay = args.output / f"anomaly_{key}_overlay.png"
        scene.render.filepath = str(overlay.resolve())
        bpy.ops.render.render(write_still=True)
        for line in lines:
            bpy.data.objects.remove(line, do_unlink=True)
        manifest["regions"][region_name] = {
            "polygon_indices": region["polygons"], "centre_metres": list(centre),
            "camera_metres": list(camera.location),
            "pbr_image": str(original.resolve()), "overlay_image": str(overlay.resolve()),
        }
    manifest["source_bytes_preserved"] = hashlib.sha256(args.source.read_bytes()).hexdigest() == digest
    (args.output / "anomaly_render_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
