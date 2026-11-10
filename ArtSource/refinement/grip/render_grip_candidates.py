"""Render actual grip candidates without changing published character assets.

Blender 4.5 examples, from the repository root:
  Blender -b --factory-startup --python this_file.py -- --stage before
  Blender -b --factory-startup --python this_file.py -- --stage after
  python3 this_file.py --assemble-only

Before renders store their camera transforms. After renders use those exact
transforms, so each pair has the same view and original source animation time.
The GIF follows the source grip with a baseline-derived camera, and includes
only sampled native slash poses. It is an offline asset review.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LIBRARY = REPO / "ArtSource/tripo-warrior/library"
PREVIEWS = HERE / "previews"
CHARACTERS = ("base", "indigo", "veteran")
MOTION_TIMES = (1.55, 1.78, 2.0, 2.117, 2.35, 2.6, 2.85, 3.1, 3.4)
CONTACT_POSES = (("slash", 1.55), ("slash", 2.117), ("slash", 2.6),
                 ("slash", 3.4), ("walk", .60), ("hit_body", .35))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose_id(clip, seconds):
    return f"{clip}_{round(seconds * 1000):04d}"


def render_jobs(character):
    jobs = [dict(id="right_contact", clip="slash", seconds=2.117, view="right", scale=.32),
            dict(id="left_contact", clip="slash", seconds=2.117, view="left", scale=.32)]
    poses = set(CONTACT_POSES) | {("slash", seconds) for seconds in MOTION_TIMES}
    for clip, seconds in sorted(poses):
        jobs.append(dict(id=pose_id(clip, seconds), clip=clip, seconds=seconds,
                         view="both", scale=.62))
    crossing_time = {"indigo": 94 / 30, "veteran": 55 / 30}.get(character)
    if crossing_time is not None:
        jobs.append(dict(id="left_" + pose_id("slash", crossing_time), clip="slash",
                         seconds=crossing_time, view="left", scale=.32))
    if character == "indigo":
        jobs.append(dict(id="left_side_" + pose_id("slash", 94 / 30), clip="slash",
                         seconds=94 / 30, view="left_side", scale=.32))
        jobs.append(dict(id="left_" + pose_id("slash", 95 / 30), clip="slash",
                         seconds=95 / 30, view="left_side", scale=.32))
    if character == "veteran":
        jobs.append(dict(id="left_" + pose_id("slash", 1.55), clip="slash",
                         seconds=1.55, view="left", scale=.32))
    return jobs


def setup_scene(size, samples):
    import bpy
    from mathutils import Vector

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.unit_settings.system = "METRIC"
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("Grip candidate offline studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (.07, .09, .12, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = .42
    scene.world = world
    for name, position, power, size_metres, colour in (
        ("Warm key", (-3, -4.5, 5.5), 900, 5, (1, .84, .69)),
        ("Cool fill", (4.2, -2, 3.5), 650, 4, (.62, .76, 1)),
        ("Edge", (1.2, 3, 4), 1100, 3, (.88, .94, 1)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = power, "DISK", size_metres, colour
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (Vector((0, 0, 1.2)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    camera_data = bpy.data.cameras.new("Grip review camera")
    camera_data.type = "ORTHO"
    camera = bpy.data.objects.new("Grip review camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, camera


def select_pose(armatures, scene, clip, seconds):
    for armature in armatures:
        animation = armature.animation_data
        if animation is None:
            raise ValueError(f"Missing animation data in {armature.name}")
        animation.action = None
        found = False
        for track in animation.nla_tracks:
            selected = track.name == clip
            track.mute = not selected
            if selected:
                found = True
                strip = track.strips[0]
                strip.frame_start = 64 - seconds * scene.render.fps
                strip.influence = 1.0
        if not found:
            raise ValueError(f"Missing original clip {clip}")
    scene.frame_set(63)


def derive_camera(armature, job, camera):
    from mathutils import Vector

    bone = armature.pose.bones
    if job["view"] == "right":
        names, offset = ("R_Mid1", "R_Mid3"), (.30, -.42, .24)
    elif job["view"] in ("left", "left_side"):
        names = ("L_Mid1", "L_Mid3")
        offset = (-.30, .42, .24) if job["view"] == "left" else (.30, -.42, .15)
    else:
        names, offset = ("R_Hand", "L_Hand"), (.30, -.42, .24)
    centre = sum((armature.matrix_world @ bone[name].matrix.translation for name in names), Vector()) / len(names)
    camera.location = centre + Vector(offset)
    camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = job["scale"]
    return {"location": list(camera.location), "rotation_euler": list(camera.rotation_euler),
            "ortho_scale_metres": camera.data.ortho_scale, "target": list(centre)}


def render_stage(stage, characters, size, samples, only_jobs):
    import bpy

    manifest_path = PREVIEWS / "render_manifest.json"
    if stage == "before" and not only_jobs:
        manifest = {"blender_version": bpy.app.version_string, "render_size": size,
                    "cycles_samples": samples, "scope": "offline posed source GLB skin and weapon",
                    "same_camera_pairs": True, "source_times_seconds": list(MOTION_TIMES),
                    "motion_camera": "tracks baseline wrists at each sampled original source time",
                    "characters": {}}
    else:
        manifest = json.loads(manifest_path.read_text())
        if manifest["render_size"] != size or manifest["cycles_samples"] != samples:
            raise ValueError("Use the same render size and samples as the before pass")
    for key in characters:
        path = LIBRARY / f"{key}.glb" if stage == "before" else HERE / "candidates" / f"{key}.glb"
        if not path.is_file():
            raise FileNotFoundError(path)
        baseline_path = LIBRARY / f"{key}.glb"
        if stage == "before" and key not in manifest["characters"]:
            record = {"source": str(baseline_path.relative_to(REPO)), "source_sha256": digest(baseline_path),
                      "cameras": {}}
            manifest["characters"][key] = record
        elif stage == "after":
            record = manifest["characters"][key]
            if digest(baseline_path) != record["source_sha256"]:
                raise ValueError("Published baseline changed during review: " + key)
            record["candidate"] = str(path.relative_to(REPO))
            record["candidate_sha256"] = digest(path)
        else:
            record = manifest["characters"][key]
            if digest(baseline_path) != record["source_sha256"]:
                raise ValueError("Published baseline changed during review: " + key)
        scene, camera = setup_scene(size, samples)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.import_scene.gltf(filepath=str(path))
        armatures = [obj for obj in bpy.context.selected_objects if obj.type == "ARMATURE"]
        if not armatures:
            raise ValueError("No actual rig imported from " + str(path))
        output = PREVIEWS / key / stage
        output.mkdir(parents=True, exist_ok=True)
        jobs = render_jobs(key)
        if only_jobs:
            jobs = [job for job in jobs if job["id"] in only_jobs]
        for job in jobs:
            select_pose(armatures, scene, job["clip"], job["seconds"])
            if stage == "before":
                record["cameras"][job["id"]] = {**job, **derive_camera(armatures[0], job, camera)}
            else:
                saved = record["cameras"][job["id"]]
                camera.location = saved["location"]
                camera.rotation_euler = saved["rotation_euler"]
                camera.data.ortho_scale = saved["ortho_scale_metres"]
            scene.render.filepath = str(output / (job["id"] + ".png"))
            bpy.ops.render.render(write_still=True)
            print(f"GRIP_REVIEW {stage} {key} {job['id']}", flush=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest_path


def assemble(characters, only_jobs=None):
    from PIL import Image, ImageDraw, ImageFont

    font_path = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    font = ImageFont.truetype(font_path, 22)
    small = ImageFont.truetype(font_path, 17)

    def paired(key, job_id, label, tile_size=512):
        images = [Image.open(PREVIEWS / key / stage / f"{job_id}.png").convert("RGB")
                  .resize((tile_size, tile_size), Image.Resampling.LANCZOS) for stage in ("before", "after")]
        result = Image.new("RGB", (tile_size * 2, tile_size + 72), (24, 29, 35))
        draw = ImageDraw.Draw(result)
        draw.text((12, 7), f"{key}  {label}  |  native source time", font=small, fill=(236, 237, 239))
        draw.text((12, 34), "Before", font=font, fill=(236, 237, 239))
        draw.text((tile_size + 12, 34), "After candidate", font=font, fill=(236, 237, 239))
        for index, image in enumerate(images):
            result.paste(image, (index * tile_size, 72))
        return result

    for key in characters:
        for side in ("right", "left"):
            if only_jobs and side + "_contact" not in only_jobs:
                continue
            paired(key, side + "_contact", f"slash 2.117 s / {side} hand", 768).save(
                PREVIEWS / f"{key}_{side}_before_after.png")
        for job in render_jobs(key):
            if job["view"] in ("left", "left_side") and job["id"] != "left_contact":
                if only_jobs and job["id"] not in only_jobs:
                    continue
                paired(key, job["id"], f"slash {job['seconds']:.6f} s / left hand", 768).save(
                    PREVIEWS / f"{key}_{job['id']}_before_after.png")
        if only_jobs:
            continue
        cells = [paired(key, pose_id(clip, seconds), f"{clip} {seconds:.3f} s", 320)
                 for clip, seconds in CONTACT_POSES]
        width, height = cells[0].size
        sheet = Image.new("RGB", (width * 3, height * 2 + 40), (24, 29, 35))
        ImageDraw.Draw(sheet).text((12, 7), "Offline grip samples / before and after / same baseline cameras",
                                  font=font, fill=(236, 237, 239))
        for index, cell in enumerate(cells):
            sheet.paste(cell, ((index % 3) * width, 40 + (index // 3) * height))
        sheet.save(PREVIEWS / f"{key}_contact_sheet.png")
        frames = [paired(key, pose_id("slash", seconds), f"slash {seconds:.3f} s", 448)
                  for seconds in MOTION_TIMES]
        durations = [round((following - time) * 1000) for time, following in zip(MOTION_TIMES, MOTION_TIMES[1:])]
        durations.append(durations[-1])
        frames[0].save(PREVIEWS / f"{key}_slash_before_after.gif", save_all=True, append_images=frames[1:],
                       duration=durations, loop=0, optimize=False)
        print("GRIP_REVIEW_ASSEMBLED", key, flush=True)


def main():
    arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("before", "after", "both"), default="both")
    parser.add_argument("--characters", nargs="+", choices=CHARACTERS, default=list(CHARACTERS))
    parser.add_argument("--size", type=int, default=640)
    parser.add_argument("--samples", type=int, default=8)
    parser.add_argument("--assemble-only", action="store_true")
    parser.add_argument("--only-jobs", nargs="+")
    options = parser.parse_args(arguments)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    if options.assemble_only:
        assemble(options.characters, options.only_jobs)
        return
    for stage in (("before", "after") if options.stage == "both" else (options.stage,)):
        render_stage(stage, options.characters, options.size, options.samples, options.only_jobs)


if __name__ == "__main__":
    main()
