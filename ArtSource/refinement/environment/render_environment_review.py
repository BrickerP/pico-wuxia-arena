"""Render controlled offline environment views using active glTF scene nodes.

Source GLBs remain read-only. Forecourt orphan nodes are explicitly excluded.
Camera coordinates and placement are recorded in the SDK stage coordinate frame.
"""

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ArtSource/tripo-warrior"))
from prepare_rigged_warrior import encode_glb, read_glb, world_matrix


SOURCE_DIR = ROOT / "ArtSource/tavern"
EXPECTED = {
    "tavern_slice": "af3adf8b15bb5aa6f34a9a5240e18bc2534bc977db4a05089a0c3a1ee1bbdc69",
    "forecourt": "fde7def5888232f0b20fd5959fac4a5edbae1ee51261a88b97e6216ce741477e",
    "courtyard_details": "d2bdf0806ef972fe8fc533066aa96830d23c97e7f617ebca26b808c548f53d3e",
}
CANDIDATE_HASHES = {
    "Paving_Root": "bc9a7d0e4a5dc463ca2a73f4936f253e56efc6a87363c74c14b0a95f9e75d3fb",
    "Structure_Root": "4f0b4ce49034ba938a574cddd377c3454e26c449d5eaefe404116641c8dfcfa7",
}
PLACEMENTS = {"tavern_slice": (0, 0, -4), "forecourt": (0, 0, -4), "courtyard_details": (0, 0, 0)}
CAMERAS = {
    "player": {"position_stage": [0, 1.6, 0], "target_stage": [0, 1.45, -4], "lens_mm": 24},
    "ground_oblique": {"position_stage": [1.15, .38, -.65], "target_stage": [0, .02, -2.5], "lens_mm": 30},
    "threshold_column": {"position_stage": [-.30, .58, -2.6], "target_stage": [-1.10, .18, -3.9], "lens_mm": 28},
}
LIGHTS = [
    {"name": "Overcast cool white", "type": "AREA", "position_stage": [-2, 4.5, -1.5],
     "target_stage": [0, .5, -3], "watts": 1000, "size_metres": 5, "color": [.90, .95, 1]},
    {"name": "Warm white fill", "type": "AREA", "position_stage": [3, 3.2, -2],
     "target_stage": [0, 1, -3.5], "watts": 500, "size_metres": 4, "color": [1, .94, .86]},
    {"name": "Lantern warm white", "type": "POINT", "position_stage": [-1.43, 2.86, -3.58],
     "watts": 28, "size_metres": .25, "color": [1, .85, .68]},
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_to_blender(value):
    x, y, z = value
    return Vector((x, -z, y))


def reachable(document, roots):
    result = set()
    stack = list(roots)
    while stack:
        index = stack.pop()
        if index not in result:
            result.add(index)
            stack.extend(document["nodes"][index].get("children", []))
    return result


def active_subset(document, select, exclude):
    if document.get("skins") or document.get("animations"):
        raise ValueError("The environment review accepts static source scene hierarchies")
    scene_index = document.get("scene", 0)
    roots = document["scenes"][scene_index].get("nodes", [])
    active = reachable(document, roots)
    parents = {child: index for index in active for child in document["nodes"][index].get("children", [])}
    keep = set(active)
    if select:
        keep = set()
        for name in select:
            matches = [index for index in active if document["nodes"][index].get("name") == name]
            if len(matches) != 1:
                raise ValueError(f"Expected one active candidate root named {name}")
            keep.update(reachable(document, matches))
            index = matches[0]
            while index in parents:
                index = parents[index]
                keep.add(index)
    for name in exclude:
        matches = [index for index in active if document["nodes"][index].get("name") == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one active original replacement root named {name}")
        keep.difference_update(reachable(document, matches))
    order = sorted(keep)
    remap = {old: new for new, old in enumerate(order)}
    result = copy.deepcopy(document)
    result["nodes"] = []
    for index in order:
        node = copy.deepcopy(document["nodes"][index])
        if "children" in node:
            node["children"] = [remap[child] for child in node["children"] if child in keep]
        result["nodes"].append(node)
    result["scenes"] = [{"name": "Offline active scene selection", "nodes": [remap[index] for index in roots if index in keep]}]
    result["scene"] = 0
    return result, {"original_active_scene": scene_index, "active_source_nodes": sorted(active),
                    "retained_source_nodes": order,
                    "orphan_source_nodes_excluded": sorted(set(range(len(document["nodes"]))) - active),
                    "selected_roots": list(select), "excluded_roots": list(exclude)}


def scene_bounds(document, instance_matrix):
    points = []
    for index, node in enumerate(document["nodes"]):
        if "mesh" not in node:
            continue
        transform = instance_matrix @ world_matrix(document["nodes"], index)
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            accessor = document["accessors"][primitive["attributes"]["POSITION"]]
            if "min" not in accessor or "max" not in accessor:
                raise ValueError("Environment POSITION accessor needs explicit source bounds")
            for corner in itertools.product(*zip(accessor["min"], accessor["max"])):
                points.append(transform @ Vector(corner))
    if not points:
        return None
    return {"min_stage": [min(point[axis] for point in points) for axis in range(3)],
            "max_stage": [max(point[axis] for point in points) for axis in range(3)]}


def import_asset(label, path, placement, select, exclude, output, instance_matrix=None):
    source_hash = sha(path)
    document, binary = read_glb(path)
    filtered, selection = active_subset(document, select, exclude)
    prepared = output / "inputs" / f"{label}_active.glb"
    prepared.parent.mkdir(parents=True, exist_ok=True)
    prepared.write_bytes(encode_glb(filtered, binary))
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(prepared.resolve()))
    imported = list(bpy.context.selected_objects)
    frame = bpy.data.objects.new(f"Offline placement {label}", None)
    bpy.context.scene.collection.objects.link(frame)
    for obj in imported:
        if obj.parent is None:
            obj.parent = frame
    instance_matrix = instance_matrix if instance_matrix is not None else Matrix.Translation(Vector(placement))
    axes = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    frame.matrix_world = axes @ instance_matrix @ axes.inverted()
    bpy.context.view_layer.update()
    return {"label": label, "source": str(path.resolve()), "source_sha256": source_hash,
            "derived_active_scene_file": str(prepared.resolve()), "derived_sha256": sha(prepared),
            "stage_position_metres": list(placement), "selection": selection,
            "instance_matrix_stage": [list(row) for row in instance_matrix],
            "active_scene_bounds": scene_bounds(filtered, instance_matrix),
            "mesh_object_count": sum(obj.type == "MESH" for obj in imported)}


def replacement_frame(source, candidate, root_name, placement):
    if sha(candidate) != CANDIDATE_HASHES[root_name]:
        raise ValueError(f"Candidate does not match the frozen review identity: {candidate}")
    source_document, _ = read_glb(source)
    candidate_document, _ = read_glb(candidate)
    root_matrices = []
    for document in (source_document, candidate_document):
        active = reachable(document, document["scenes"][document.get("scene", 0)].get("nodes", []))
        matches = [index for index in active if document["nodes"][index].get("name") == root_name]
        if len(matches) != 1:
            raise ValueError(f"Expected one active binding root {root_name}")
        root_matrices.append(world_matrix(document["nodes"], matches[0]))
    return Matrix.Translation(Vector(placement)) @ root_matrices[0] @ root_matrices[1].inverted()


def studio():
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x, scene.render.resolution_y = 1280, 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("Controlled overcast neutral environment")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (.10, .12, .15, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = .45
    scene.world = world
    for spec in LIGHTS:
        data = bpy.data.lights.new(spec["name"], spec["type"])
        data.energy, data.color = spec["watts"], spec["color"]
        if spec["type"] == "AREA":
            data.size = spec["size_metres"]
        else:
            data.shadow_soft_size = spec["size_metres"]
        light = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(light)
        light.location = stage_to_blender(spec["position_stage"])
        if "target_stage" in spec:
            light.rotation_euler = (stage_to_blender(spec["target_stage"]) - light.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("Offline controlled player camera")
    data.type = "PERSP"
    data.sensor_width = 36
    data.clip_start, data.clip_end = .01, 100
    camera = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("before", "after"), default="before")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--paving-tavern", type=Path)
    parser.add_argument("--paving-forecourt", type=Path)
    parser.add_argument("--entry", type=Path)
    parser.add_argument("--entry-sha256", default=CANDIDATE_HASHES["Structure_Root"])
    parser.add_argument("--views", nargs="+", choices=tuple(CAMERAS), default=list(CAMERAS))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    args.output = args.output or HERE / "review" / args.phase
    CANDIDATE_HASHES["Structure_Root"] = args.entry_sha256
    replacements = {"tavern_slice": [], "forecourt": [], "courtyard_details": []}
    if args.phase == "after":
        if not any((args.paving_tavern, args.paving_forecourt, args.entry)):
            raise ValueError("After review requires an explicit candidate root")
        if args.paving_tavern:
            replacements["tavern_slice"].append(("Paving_Root", args.paving_tavern))
        if args.paving_forecourt:
            replacements["forecourt"].append(("Paving_Root", args.paving_forecourt))
        if args.entry:
            replacements["tavern_slice"].append(("Structure_Root", args.entry))
    for key, expected in EXPECTED.items():
        for path in (SOURCE_DIR / f"{key}.glb", ROOT / f"app/src/main/assets/models/{key}.glb"):
            if sha(path) != expected:
                raise ValueError(f"Source/app identity mismatch: {path}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    args.output.mkdir(parents=True, exist_ok=True)
    instances = []
    for key in EXPECTED:
        substitutions = replacements[key]
        instances.append(import_asset(key, SOURCE_DIR / f"{key}.glb", PLACEMENTS[key], [],
                                      [name for name, path in substitutions], args.output))
        for name, path in substitutions:
            instance_matrix = replacement_frame(SOURCE_DIR / f"{key}.glb", path, name, PLACEMENTS[key])
            instances.append(import_asset(f"{key}_{name}_candidate", path, PLACEMENTS[key], [name], [], args.output,
                                          instance_matrix=instance_matrix))
    scene, camera = studio()
    manifest = {"scope": "offline controlled Blender view of real source/candidate GLBs",
                "phase": args.phase, "coordinate_contract": "SDK +Y up, +Z behind player; Blender (x,-z,y)",
                "runtime_placement_source": "app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt",
                "active_scene_only": True, "assets": instances, "cameras": CAMERAS, "lights": LIGHTS,
                "world": {"color": [.10, .12, .15], "strength": .45}, "resolution": [1280, 960],
                "engine": scene.render.engine, "blender_version": bpy.app.version_string,
                "color_management": scene.view_settings.view_transform, "renders": {}}
    previous_path = args.output / f"{args.phase}_manifest.json"
    if previous_path.exists():
        previous = json.loads(previous_path.read_text())
        old_inputs = [(item["label"], item["source_sha256"]) for item in previous["assets"]]
        new_inputs = [(item["label"], item["source_sha256"]) for item in instances]
        if old_inputs != new_inputs:
            raise ValueError("An output directory cannot mix source/candidate variants")
        for name, image in previous["renders"].items():
            if name not in args.views:
                if previous["cameras"][name] != CAMERAS[name]:
                    raise ValueError("A retained view has a different camera")
                manifest["renders"][name] = image
    if args.phase == "after":
        before_path = HERE / "review/before/before_manifest.json"
        before = json.loads(before_path.read_text())
        if any(before[key] != manifest[key] for key in ("cameras", "lights", "world", "resolution", "engine", "color_management")):
            raise ValueError("Before/after controlled camera or lighting contract differs")
        manifest["same_camera_lighting_as_before_verified"] = True
        manifest["before_manifest_sha256"] = sha(before_path)
    for name in args.views:
        spec = CAMERAS[name]
        camera.location = stage_to_blender(spec["position_stage"])
        camera.rotation_euler = (stage_to_blender(spec["target_stage"]) - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.lens = spec["lens_mm"]
        image = args.output / f"offline_{args.phase}_{name}.png"
        scene.render.filepath = str(image.resolve())
        bpy.ops.render.render(write_still=True)
        manifest["renders"][name] = str(image.resolve())
    for instance in instances:
        if sha(Path(instance["source"])) != instance["source_sha256"]:
            raise ValueError("Source changed during controlled scene rendering")
    manifest["all_input_bytes_preserved"] = True
    (args.output / f"{args.phase}_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
