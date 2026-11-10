"""Offline same-camera review of the final 60k hero's actual skinned grip.

Blender 4.5: Blender -b --factory-startup --python this_file.py -- --stage before
Then repeat with --stage after after the candidate is finalized, followed by:
  python3 this_file.py --assemble-only
All output belongs to hero60k/previews; the prior renderer is read-only.
"""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GRIP = HERE.parent
REPO = HERE.parents[3]
LIBRARY = REPO / "ArtSource/tripo-warrior/library"
SOURCE_SHA256 = "5ff55210dfbe9e10fbad1bf0d182424ae298bf009f9b845e9d307543302e0f3f"


def assemble_right_side():
    from PIL import Image, ImageDraw, ImageFont

    images = [Image.open(HERE / "previews/base" / stage / "right_side.png").convert("RGB")
              for stage in ("before", "after")]
    width, height = images[0].size
    result = Image.new("RGB", (width * 2, height + 60), (24, 29, 35))
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 20)
    label = ImageDraw.Draw(result)
    label.text((12, 8), "60k hero / right grip side / native slash 2.117 s", font=font, fill="white")
    label.text((12, 33), "Before", font=font, fill="white")
    label.text((width + 12, 33), "After candidate", font=font, fill="white")
    for index, image in enumerate(images):
        result.paste(image, (index * width, 60))
    result.save(HERE / "previews/base_right_side_before_after.png")


def main():
    source = LIBRARY / "base.glb"
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("The reviewed public 60k hero baseline changed")
    spec = importlib.util.spec_from_file_location("reviewed_grip_renderer", GRIP / "render_grip_candidates.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    original_jobs, original_camera = renderer.render_jobs, renderer.derive_camera

    def jobs(character):
        result = original_jobs(character)
        result.append(dict(id="right_side", clip="slash", seconds=2.117, view="right_side", scale=.32))
        for seconds in (41 / 30, 1.55, 2.117, 3.4, 3.9):
            result.append(dict(id=f"left_side_slash_{round(seconds * 1000):04d}", clip="slash",
                               seconds=seconds, view="left_side", scale=.36))
        return result

    def camera(armature, job, camera_object):
        if job["view"] != "right_side":
            return original_camera(armature, job, camera_object)
        from mathutils import Vector
        bones = armature.pose.bones
        centre = sum((armature.matrix_world @ bones[name].matrix.translation
                      for name in ("R_Mid1", "R_Mid3")), Vector()) / 2
        camera_object.location = centre + Vector((.30, -.28, -.26))
        camera_object.rotation_euler = (centre - camera_object.location).to_track_quat("-Z", "Y").to_euler()
        camera_object.data.ortho_scale = job["scale"]
        return {"location": list(camera_object.location), "rotation_euler": list(camera_object.rotation_euler),
                "ortho_scale_metres": camera_object.data.ortho_scale, "target": list(centre)}

    renderer.HERE = HERE
    renderer.LIBRARY = LIBRARY
    renderer.PREVIEWS = HERE / "previews"
    renderer.CHARACTERS = ("base",)
    renderer.render_jobs = jobs
    renderer.derive_camera = camera
    renderer.main()
    if "--assemble-only" in sys.argv and "--only-jobs" not in sys.argv:
        assemble_right_side()
    path = renderer.PREVIEWS / "render_manifest.json"
    if path.is_file():
        manifest = json.loads(path.read_text())
        manifest["scope"] = "offline final 60k hero versus one local grip correction candidate"
        manifest["baseline_public_sha256"] = SOURCE_SHA256
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
