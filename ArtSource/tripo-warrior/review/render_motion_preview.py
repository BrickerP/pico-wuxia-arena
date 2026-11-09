"""Render an offline gait display from the three actual runtime GLBs."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_character_library as display


def main():
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg is None:
        raise RuntimeError('ffmpeg is required to encode the asset display')
    scene = display.scene
    scene.cycles.samples = 8
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    display.camera_data.ortho_scale = 7.2
    display.title.body = '酒馆试炼 · 三角色步法资源'
    for curve, name in zip(display.labels, ('试刀客', '青衫护院', '玄甲守擂')):
        curve.body = name
    # This phase range and stride also drive the gameplay animation presenter.
    frames = 54
    with tempfile.TemporaryDirectory(prefix='pico-gait-display-') as temporary:
        folder = Path(temporary)
        for frame in range(frames):
            source_time = 1 / 3 + frame / frames * 7 / 6
            for _, armatures in display.actors:
                display.pose(armatures, 'walk', source_time)
            scene.frame_set(63)
            scene.render.filepath = str(folder / f'{frame:03d}.png')
            bpy.ops.render.render(write_still=True)
        cycle = folder / 'cycle.mp4'
        subprocess.run([
            ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-framerate', '24',
            '-i', str(folder / '%03d.png'), '-c:v', 'libx264', '-crf', '20',
            '-pix_fmt', 'yuv420p', str(cycle),
        ], check=True)
        output = display.HERE / 'character_motion_preview.mp4'
        subprocess.run([
            ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-stream_loop', '2',
            '-i', str(cycle), '-c', 'copy', '-movflags', '+faststart', str(output),
        ], check=True)
        print('Produced offline asset motion display', output)


if __name__ == '__main__':
    main()
