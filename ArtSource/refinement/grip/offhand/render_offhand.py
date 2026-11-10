"""Offline offhand review using the reviewed grip candidates as the baseline.

Run with Blender 4.5 from the repository root:
  Blender -b --factory-startup --python this_file.py -- --stage before
  Blender -b --factory-startup --python this_file.py -- --stage after
Then assemble with the host Python/Pillow:
  python3 this_file.py --assemble-only

Only this driver's directory receives output. Camera transforms are pinned by
the before pass. The previous renderer is imported with bytecode writing off.
"""

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GRIP = HERE.parent
BASELINE_HASHES = {
    "indigo": "4516458ab2d44d986046d36c8349a5901ef20452e60e6570f56c6540d172ee43",
    "veteran": "010e80a08573d0b165692b30a06fcc93f6f0394181fa138b198aa09049b934a3",
}
MOTION_TIMES = (1.25, 1.35, 1.55, 55 / 30, 2.117, 2.65, 94 / 30, 95 / 30, 3.4, 3.55)
CONTACT_POSES = tuple(("slash", time) for time in (1.25, 1.55, 55 / 30, 94 / 30, 95 / 30, 3.55))


def pose_id(seconds):
    return f"slash_{round(seconds * 1000):04d}"


def render_jobs(character):
    jobs = [dict(id="right_contact", clip="slash", seconds=2.117, view="right", scale=.32),
            dict(id="left_contact", clip="slash", seconds=2.117, view="left", scale=.32)]
    for seconds in MOTION_TIMES:
        jobs.append(dict(id=pose_id(seconds), clip="slash", seconds=seconds, view="body", scale=2.4))
    critical = (94 / 30, 95 / 30) if character == "indigo" else (1.55, 55 / 30)
    for seconds in critical:
        jobs.append(dict(id="arm_" + pose_id(seconds), clip="slash", seconds=seconds,
                         view="arm", scale=.95))
        for view in ("left", "left_side"):
            jobs.append(dict(id=view + "_" + pose_id(seconds), clip="slash", seconds=seconds,
                             view=view, scale=.36))
    if character == "indigo":
        jobs.append(dict(id="left_side_" + pose_id(62 / 30), clip="slash", seconds=62 / 30,
                         view="left_side", scale=.36))
    if character == "veteran":
        for seconds in (91 / 60, 46 / 30):
            jobs.append(dict(id="arm_" + pose_id(seconds), clip="slash", seconds=seconds,
                             view="arm", scale=.95))
    return jobs


def derive_camera(armature, job, camera):
    from mathutils import Vector

    bones = armature.pose.bones
    if job["view"] == "body":
        centre = sum((armature.matrix_world @ bones[name].matrix.translation
                      for name in ("Hip", "Head")), Vector()) / 2
        centre.z += .08
        offset = Vector((1.6, -3.2, .7))
    elif job["view"] == "arm":
        centre = sum((armature.matrix_world @ bones[name].matrix.translation
                      for name in ("L_Upperarm", "L_Hand")), Vector()) / 2
        offset = Vector((1.6, -3.2, .7))
    else:
        names = ("R_Mid1", "R_Mid3") if job["view"] == "right" else ("L_Mid1", "L_Mid3")
        centre = sum((armature.matrix_world @ bones[name].matrix.translation for name in names), Vector()) / 2
        offset = Vector((-.30, .42, .24) if job["view"] == "left" else (.30, -.42, .15))
    camera.location = centre + offset
    camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = job["scale"]
    return {"location": list(camera.location), "rotation_euler": list(camera.rotation_euler),
            "ortho_scale_metres": camera.data.ortho_scale, "target": list(centre)}


def assemble_arm_pairs(characters):
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 20)
    for character in characters:
        for job in render_jobs(character):
            if job["view"] != "arm":
                continue
            images = [Image.open(HERE / "previews" / character / stage / (job["id"] + ".png")).convert("RGB")
                      for stage in ("before", "after")]
            width, height = images[0].size
            result = Image.new("RGB", (width * 2, height + 60), (24, 29, 35))
            label = ImageDraw.Draw(result)
            label.text((12, 8), f"{character} / left arm guard / slash {job['seconds']:.6f} s", font=font, fill="white")
            label.text((12, 33), "Before", font=font, fill="white")
            label.text((width + 12, 33), "After candidate", font=font, fill="white")
            for index, image in enumerate(images):
                result.paste(image, (index * width, 60))
            result.save(HERE / "previews" / f"{character}_{job['id']}_before_after.png")


def main():
    for character, expected in BASELINE_HASHES.items():
        path = GRIP / "candidates" / f"{character}.glb"
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Reviewed before baseline changed: " + character)
    spec = importlib.util.spec_from_file_location("reviewed_grip_renderer", GRIP / "render_grip_candidates.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    renderer.HERE = HERE
    renderer.LIBRARY = GRIP / "candidates"
    renderer.PREVIEWS = HERE / "previews"
    renderer.CHARACTERS = tuple(BASELINE_HASHES)
    renderer.MOTION_TIMES = MOTION_TIMES
    renderer.CONTACT_POSES = CONTACT_POSES
    renderer.render_jobs = render_jobs
    renderer.derive_camera = derive_camera
    renderer.main()
    if "--assemble-only" in sys.argv:
        arguments = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--characters", nargs="+", choices=tuple(BASELINE_HASHES), default=list(BASELINE_HASHES))
        options, _ = parser.parse_known_args(arguments)
        assemble_arm_pairs(options.characters)
    manifest_path = renderer.PREVIEWS / "render_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        manifest["motion_camera"] = "baseline torso framing at each native source time; exact same after camera"
        manifest["scope"] = "offline offhand local-pose candidate versus previously reviewed grip candidate"
        manifest["baseline_hashes"] = BASELINE_HASHES
        manifest["envelope_review_times_seconds"] = list(MOTION_TIMES)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
