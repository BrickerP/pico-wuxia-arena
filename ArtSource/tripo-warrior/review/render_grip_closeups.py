"""Render actual posed skin and dao grip close-ups as production evidence."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_character_library as display


def main():
    suffix = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'current'
    display.scene.cycles.samples = 16
    display.scene.render.resolution_x = 1024
    display.scene.render.resolution_y = 1024
    display.camera_data.ortho_scale = .28
    for _, armatures in display.actors:
        display.pose(armatures, 'slash', 2.117)
    display.scene.frame_set(63)
    for key, armatures in display.actors:
        armature = armatures[0]
        joint = armature.pose.bones
        centre = sum((armature.matrix_world @ joint[name].matrix.translation
                      for name in ('R_Mid1', 'R_Mid3')), Vector()) / 2
        display.camera.location = centre + Vector((.30, -.42, .24))
        display.camera.rotation_euler = (centre - display.camera.location).to_track_quat('-Z', 'Y').to_euler()
        display.scene.render.filepath = str(display.HERE / f'{key}_grip_{suffix}.png')
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
