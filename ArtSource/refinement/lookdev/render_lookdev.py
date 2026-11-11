"""Controlled offline lighting compare of the exact current app GLBs.

This is a Blender look-development transfer, never PICO render proof. Assets,
pose, camera and view transform are identical between the two images. PICO lux /
lumens are transferred to Blender with explicitly recorded approximate factors.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "ArtSource/refinement/environment"))
from render_environment_review import import_asset, stage_to_blender

SOURCE_SHA = "562449af40ee984ddd8ef61be5c339ac9bea2de5"
ENVIRONMENT = {"tavern_slice": (0, 0, -4), "forecourt": (0, 0, -4), "courtyard_details": (0, 0, 0)}
CAMERAS = {
    "player": {"position_stage": [0, 1.60, 0], "target_stage": [0, 1.32, -2.4], "lens_mm": 24},
    "fighter_1_5m": {"position_stage": [0, 1.60, -.90], "target_stage": [0, 1.46, -2.4], "lens_mm": 24},
}
# A single transfer is applied to all fixtures in both profiles. It is an artistic
# approximation because PICO and Blender do not publish equivalent exposure paths.
LUMENS_PER_BLENDER_WATT = 25.0
LUX_PER_BLENDER_SUN_ENERGY = 683.0
PROFILES = {
    "current": {
        "world_color_linear": [.025, .025, .025], "world_strength": .35,
        "sun": {"name": "Current broad white key", "lux": 1100.0, "color": [.92, .95, 1], "ray_stage": [.501406, -.621743, -.601687]},
        "points": [
            {"name": "Current warm front fill", "stage_position": [-1.30, 1.80, -1.10], "color": [1, .72, .46], "lumens": 2300, "radius_m": 4.2},
            {"name": "Current cool front fill", "stage_position": [1.25, 1.65, -1.55], "color": [.58, .74, 1], "lumens": 1300, "radius_m": 4.0},
        ],
    },
    "target": {
        "world_color_linear": [.025, .040, .070], "world_strength": .50,
        "sun": {"name": "Moon cool diagonal key", "lux": 650.0, "color": [.57, .73, 1], "ray_stage": [.501406, -.621743, -.601687]},
        "points": [
            {"name": "Lantern practical", "stage_position": [-1.43, 2.86, -3.58], "color": [1, .49, .20], "lumens": 1500, "radius_m": 3.2},
            {"name": "Warm bounce for face", "stage_position": [-1.80, 1.55, -1.10], "color": [1, .69, .40], "lumens": 900, "radius_m": 2.6},
            {"name": "Cool rear edge", "stage_position": [1.90, 2.50, -3.40], "color": [.38, .65, 1], "lumens": 900, "radius_m": 3.0},
        ],
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_fighter(path):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    imported = list(bpy.context.selected_objects)
    placement = bpy.data.objects.new("Same actual app fighter placement", None)
    bpy.context.scene.collection.objects.link(placement)
    for obj in imported:
        if obj.parent is None:
            obj.parent = placement
    placement.location = stage_to_blender((0, .028, -2.4))
    tracks = []
    for obj in imported:
        if obj.type == "ARMATURE":
            data = obj.animation_data
            if data is None:
                raise RuntimeError("Actual app fighter has no imported animation data")
            data.action = None
            data.use_nla = True
            found = False
            for track in data.nla_tracks:
                selected = track.name == "idle"
                track.mute = not selected
                if selected:
                    found = True
                    tracks.append(track.name)
                    track.strips[0].frame_start = 1
                    track.strips[0].influence = 1.0
            if not found:
                raise RuntimeError("Actual app fighter is missing idle NLA")
    bpy.context.scene.frame_set(31)
    bpy.context.view_layer.update()
    return {"source": str(path.resolve()), "source_sha256": sha(path),
            "stage_position_metres": [0, .028, -2.4], "rotation": "unchanged source", "uniform_scale": 1.0,
            "clip": "idle", "source_seconds": 1.0, "nla_tracks": tracks,
            "mesh_names": [o.name for o in imported if o.type == "MESH"]}


def lighting(profile):
    for obj in list(bpy.context.scene.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    world = bpy.data.worlds.new("Offline " + profile["sun"]["name"])
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (*profile["world_color_linear"], 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = profile["world_strength"]
    bpy.context.scene.world = world
    sun = profile["sun"]
    data = bpy.data.lights.new(sun["name"], "SUN")
    data.energy = sun["lux"] / LUX_PER_BLENDER_SUN_ENERGY
    # Matches HomeStage castsShadowEnabled=false in both profiles.
    data.use_shadow = False
    data.color = sun["color"]
    obj = bpy.data.objects.new(data.name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.rotation_euler = stage_to_blender(sun["ray_stage"]).to_track_quat("-Z", "Y").to_euler()
    for spec in profile["points"]:
        data = bpy.data.lights.new(spec["name"], "POINT")
        data.energy = spec["lumens"] / LUMENS_PER_BLENDER_WATT
        # Native PointLightComponent has no real-time cast-shadow flag.
        data.use_shadow = False
        data.color = spec["color"]
        data.shadow_soft_size = .18
        obj = bpy.data.objects.new(data.name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = stage_to_blender(spec["stage_position"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "review")
    parser.add_argument("--size", type=int, default=960)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--views", nargs="+", choices=tuple(CAMERAS), default=list(CAMERAS))
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.render.fps = 30
    scene.render.engine = "CYCLES"
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = args.size
    scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    assets = []
    for name, position in ENVIRONMENT.items():
        path = ROOT / "app/src/main/assets/models" / (name + ".glb")
        assets.append(import_asset(name, path, position, [], [], args.output))
    fighter = import_fighter(ROOT / "app/src/main/assets/models/opponents/base.glb")
    data = bpy.data.cameras.new("Identical player-view camera")
    data.type = "PERSP"
    data.sensor_width = 36
    data.clip_start, data.clip_end = .01, 100
    camera = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    manifest = {"scope": "OFFLINE Blender actual app models, controlled lighting comparison; not PICO validation",
                "source_git_sha": SOURCE_SHA, "source_bytes_preserved": True,
                "assets": assets, "fighter": fighter, "cameras": CAMERAS,
                "profiles": PROFILES, "blender_version": bpy.app.version_string,
                "engine": scene.render.engine, "samples": args.samples, "threads": 4,
                "resolution": [args.size, args.size], "view_transform": scene.view_settings.view_transform,
                "exposure": scene.view_settings.exposure,
                "coordinate_contract": "PICO Stage(x,y,z) -> Blender(x,-z,y)",
                "transfer": {"type": "explicit artistic approximation, no equivalent SDK exposure is claimed",
                             "point_lumens_per_blender_watt": LUMENS_PER_BLENDER_WATT,
                             "lux_per_blender_sun_energy": LUX_PER_BLENDER_SUN_ENERGY,
                             "point_source_radius_m": .18,
                             "physical_light_shadows": "All light shadows disabled in both profiles to match native directional cast flag and non-shadowing point lights; SDK GroundShadow is not reproduced",
                             "ibl": "world-color approximation; no KTX/PICO proof",
                             "radius": "PICO cutoff radii recorded but not emulated in Blender inverse-square falloff"},
                "renders": {}}
    (args.output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for name, profile in PROFILES.items():
        lighting(profile)
        manifest["renders"][name] = {}
        for view in args.views:
            spec = CAMERAS[view]
            camera.location = stage_to_blender(spec["position_stage"])
            camera.rotation_euler = (stage_to_blender(spec["target_stage"]) - camera.location).to_track_quat("-Z", "Y").to_euler()
            camera.data.lens = spec["lens_mm"]
            path = args.output / f"offline_{name}_{view}.png"
            scene.render.filepath = str(path.resolve())
            bpy.ops.render.render(write_still=True)
            manifest["renders"][name][view] = {"path": str(path.resolve()), "sha256": sha(path)}
            (args.output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for source in [*(Path(x["source"]) for x in assets), Path(fighter["source"])]:
        expected = next(x["source_sha256"] for x in [*assets, fighter] if x["source"] == str(source))
        if sha(source) != expected:
            raise RuntimeError(f"Source changed during render: {source}")
    # Separate integrated view: delivered mesh weather, not part of the controlled
    # light-only pair. One frozen 0.6 s state uses the same SDK placement formula.
    weather_dir = HERE / "weather"
    contract = json.loads((weather_dir / "weather_contract.json").read_text())
    weather = []
    for side, x in enumerate((-2.7, 2.7)):
        for tile in range(3):
            fall = (600_000_000 % 2_500_000_000) * (6.0 / 2_500_000_000)
            y = -2.0 + (tile * 2.0 + 6.0 - fall) % 6.0
            weather.append(import_asset(f"weather_rain_{side}_{tile}", weather_dir / "rain_tile.glb", (x, y, -2.8), [], [], args.output))
    for side, x in enumerate((-3, 3)):
        drift = .12 * math.sin(.6 * math.pi / 20 + side * math.pi)
        weather.append(import_asset(f"weather_haze_{side}", weather_dir / "side_haze.glb", (x + drift, 0, -4.4), [], [], args.output))
    weather.append(import_asset("weather_sky", weather_dir / "rain_night_sky.glb", (0, 0, 0), [], [], args.output))
    # The native sky mesh does not illuminate PBR materials. Hide weather from
    # indirect light paths in Cycles so its unlit shader is camera-only as well.
    for obj in scene.objects:
        parent = obj
        is_weather = False
        while parent is not None:
            if parent.name.startswith("Offline placement weather_"):
                is_weather = True
                break
            parent = parent.parent
        if is_weather and obj.type == "MESH":
            obj.visible_diffuse = False
            obj.visible_glossy = False
            obj.visible_shadow = False
            obj.visible_transmission = False
            obj.visible_volume_scatter = False
    spec = CAMERAS["player"]
    camera.location = stage_to_blender(spec["position_stage"])
    camera.rotation_euler = (stage_to_blender(spec["target_stage"]) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = spec["lens_mm"]
    path = args.output / "offline_target_with_mesh_weather_player.png"
    scene.render.filepath = str(path.resolve())
    bpy.ops.render.render(write_still=True)
    manifest["integrated_weather"] = {"scope": "Separate offline integration of delivered analytic GLB mesh rain, side strips and sky; not volumetric fog or native particles", "time_nanos": 600_000_000,
        "assets": weather, "weather_contract_sha256": sha(weather_dir / "weather_contract.json"),
        "sky_gi": "All weather is hidden from diffuse/glossy/transmission/shadow/volume paths to avoid accidental Blender emission lighting", "render": {"path": str(path.resolve()), "sha256": sha(path)}}
    (args.output / "provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("LOOKDEV_COMPARE_READY", args.output)


if __name__ == "__main__":
    main()
