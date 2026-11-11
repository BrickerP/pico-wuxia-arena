#!/usr/bin/env python3
"""Run production Kotlin blade sampling and compare its exact triangle meshes with Pillow/NumPy.
Offline inspection only: no SDK renderer, scene occlusion, tone mapping or headset validation.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/'
JAVA = Path('/Users/yupeng/.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java')
SHA = '562449af40ee984ddd8ef61be5c339ac9bea2de5'
CAPTURE_INDEX = 24
WIDTH, HEIGHT, SS = 900, 660, 2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, name):
    result = subprocess.run(list(map(str, command)), cwd=ROOT, text=True, capture_output=True, timeout=90)
    (HERE / f'{name}.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def export():
    spec = importlib.util.spec_from_file_location('jvm_subset', HERE.parent / 'testing/run_jvm_tests.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    jar = helper.cached_jar
    compiler = [jar('org.jetbrains.kotlin', n, v) for n, v in [
        ('kotlin-compiler-embeddable', '2.1.20'), ('kotlin-stdlib', '2.1.20'),
        ('kotlin-script-runtime', '2.1.20'), ('kotlin-reflect', '1.6.10'), ('kotlin-daemon-embeddable', '2.1.20')]]
    compiler += [jar('org.jetbrains.intellij.deps', 'trove4j', '1.0.20200330'),
                 jar('org.jetbrains', 'annotations', '23.0.0'),
                 jar('org.jetbrains.kotlinx', 'kotlinx-coroutines-core-jvm', '1.8.0')]
    stdlib = jar('org.jetbrains.kotlin', 'kotlin-stdlib', '2.1.20')
    annotations = jar('org.jetbrains', 'annotations', '23.0.0')
    android = Path('/Users/yupeng/Library/Android/sdk/platforms/android-35/android.jar')
    baseline = run(['git', 'show', f'{SHA}:{BASE}BladeTrailGeometry.kt'], 'baseline-source')
    baseline_path = HERE / 'BaselineBladeTrailGeometry.kt'
    baseline_path.write_text(baseline.replace('internal class BladeTrailGeometry', 'internal class BaselineBladeTrailGeometry'))
    sources = sorted((ROOT / 'app/src/main/java/com/example/wuxiaarena/core').glob('**/*.kt'))
    sources += [ROOT / BASE / 'BladeTrailGeometry.kt',
                ROOT / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/input/DesktopCombatInput.kt',
                baseline_path, HERE / 'ExportTrail.kt']
    with tempfile.TemporaryDirectory(prefix='classes-', dir=HERE) as directory:
        cp = ':'.join(map(str, [stdlib, annotations, android]))
        run([JAVA, '-cp', ':'.join(map(str, compiler)), 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler',
             '-no-stdlib', '-no-reflect', '-jvm-target', '11', '-classpath', cp, '-d', directory, *sources], 'compile')
        run([JAVA, '-cp', f'{directory}:{cp}',
             'com.example.wuxiaarena.p0d2f0182.content.ExportTrailKt', HERE / 'meshes.json'], 'export')
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    source_hashes[BASE + 'PlayerBladeTrail.kt'] = sha(ROOT / BASE / 'PlayerBladeTrail.kt')
    return source_hashes


def camera_for(frame, distance):
    positions = np.array(frame['after']['positions'])
    # Same direction through the real head and the complete tail's fixed bounding-box centre.
    tail = positions[:frame['after']['core_vertex_offset']]
    target = (tail.min(axis=0) + tail.max(axis=0)) * .5
    toward_head = np.array([0., 1.6, 0.]) - target
    toward_head /= np.linalg.norm(toward_head)
    camera = target + toward_head * distance
    forward = -toward_head
    right = np.cross(forward, [0., 1., 0.])
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    return camera, forward, right, up, target


def project(positions, camera):
    eye, forward, right, up, _ = camera
    relative = np.array(positions) - eye
    depth = relative @ forward
    # Horizontal FOV is fixed at 90 degrees for all distances; no per-panel scaling/cropping.
    focal = WIDTH * SS * .5
    points = np.column_stack([WIDTH * SS * .5 + relative @ right * focal / depth,
                              HEIGHT * SS * .5 - relative @ up * focal / depth])
    return points, depth


def raster(mesh, candidate, camera):
    background = np.array([.073, .090, .105])
    canvas = np.broadcast_to(background, (HEIGHT * SS, WIDTH * SS, 3)).copy()
    points, depths = project(mesh['positions'], camera)
    alphas = np.array(mesh['alphas'])
    core_offset = mesh['core_vertex_offset']
    triangles = np.array(mesh['indices']).reshape(-1, 3)
    for tri in triangles:
        p = points[tri]
        if np.any(depths[tri] <= .02):
            raise ValueError('Fixture crosses the software near plane')
        x0, y0 = np.maximum(np.floor(p.min(axis=0)).astype(int), [0, 0])
        x1, y1 = np.minimum(np.ceil(p.max(axis=0)).astype(int), [WIDTH*SS-1, HEIGHT*SS-1])
        if x1 < x0 or y1 < y0:
            continue
        x, y = np.meshgrid(np.arange(x0, x1+1) + .5, np.arange(y0, y1+1) + .5)
        denom = (p[1, 1]-p[2, 1])*(p[0, 0]-p[2, 0]) + (p[2, 0]-p[1, 0])*(p[0, 1]-p[2, 1])
        if abs(denom) < 1e-12:
            continue
        a = ((p[1, 1]-p[2, 1])*(x-p[2, 0]) + (p[2, 0]-p[1, 0])*(y-p[2, 1]))/denom
        b = ((p[2, 1]-p[0, 1])*(x-p[2, 0]) + (p[0, 0]-p[2, 0])*(y-p[2, 1]))/denom
        c = 1-a-b
        mask = (a >= 0) & (b >= 0) & (c >= 0)
        inv_z = 1 / depths[tri]
        opacity = (a*alphas[tri[0]]*inv_z[0] + b*alphas[tri[1]]*inv_z[1] + c*alphas[tri[2]]*inv_z[2]) / (a*inv_z[0]+b*inv_z[1]+c*inv_z[2])
        if not candidate:
            color, factor = [.78, .82, .75], .28
        elif tri[0] < core_offset:
            color, factor = [.70, .79, .83], .38
        else:
            color, factor = [1., .94, .76], .82
        opacity = np.where(mask, opacity * factor, 0)[..., None]
        area = canvas[y0:y1+1, x0:x1+1]
        area[:] = area*(1-opacity) + np.array(color)*opacity
    result = Image.fromarray(np.uint8(np.clip(canvas, 0, 1)*255)).resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    return result


def font(size):
    return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', size)


def panel(frame, candidate, distance):
    camera = camera_for(frame, distance)
    mesh = frame['after' if candidate else 'before']
    image = raster(mesh, candidate, camera)
    draw = ImageDraw.Draw(image)
    draw.text((24, 20), 'CANDIDATE / 65ms wake + 12ms hot edge' if candidate else 'BEFORE / 562449a / 65ms wake', font=font(24), fill='#e3e5e6')
    draw.text((24, 55), f'{distance:.1f} m to target | HFOV 90 deg | same camera', font=font(19), fill='#acb4bd')
    # Ten-centimetre ruler is in the target plane, and keeps the physical camera scale.
    _, _, right, up, target = camera
    ruler = [target - right*.05 - up*.25, target + right*.05 - up*.25]
    coords, _ = project(ruler, camera)
    coords /= SS
    draw.line([tuple(coords[0]), tuple(coords[1])], fill='#949ca6', width=2)
    for xy in coords:
        draw.line([(xy[0],xy[1]-4),(xy[0],xy[1]+4)],fill='#949ca6',width=1)
    draw.text((coords[:,0].mean()-21, coords[0,1]+10), '10 cm', font=font(16), fill='#949ca6')
    draw.text((24, HEIGHT-73), f'LEFT_SLASH | t={frame["age_ns"]/1e6:.1f}ms | tip {frame["tip_speed"]:.2f}m/s', font=font(18), fill='#b7bec4')
    draw.text((24, HEIGHT-42), 'OFFLINE mesh projection / DESKTOP fixture / NOT SDK CAPTURE', font=font(17), fill='#d6af78')
    return image


def main():
    source_hashes = export()
    data = json.loads((HERE / 'meshes.json').read_text())
    frame = data['frames'][CAPTURE_INDEX]
    assert frame['before'] and frame['after'] and not frame['at_rest']
    old, new = frame['before'], frame['after']
    assert old['positions'] == new['positions'][:new['core_vertex_offset']]
    assert old['indices'] == new['indices'][:len(old['indices'])]
    assert old['alphas'] == new['alphas'][:new['core_vertex_offset']]
    for mesh in [old, new]:
        assert all(0 <= alpha <= 1 for alpha in mesh['alphas'])
        points = np.array(mesh['positions'])
        assert np.isfinite(points).all()
        for tri in np.array(mesh['indices']).reshape(-1, 3):
            assert np.all((tri >= 0) & (tri < len(points)))
            assert np.linalg.norm(np.cross(points[tri[1]]-points[tri[0]], points[tri[2]]-points[tri[0]])) > 0
    source_hashes[str(Path(__file__).resolve().relative_to(ROOT))] = sha(Path(__file__).resolve())
    images = []
    for distance in [.8, 1.5, 3.]:
        before, after = panel(frame, False, distance), panel(frame, True, distance)
        board = Image.new('RGB', (WIDTH*2, HEIGHT), '#17202a')
        board.paste(before, (0, 0)); board.paste(after, (WIDTH, 0))
        file = HERE / f'trail_compare_{distance:.1f}m.png'
        board.save(file)
        images.append({'file': file.name, 'sha256': sha(file), 'distance_m': distance,
                       'camera': [a.tolist() for a in camera_for(frame, distance)]})
    report = {'baseline_commit': SHA, 'source_hashes': source_hashes,
              'fixture': data['source'], 'fixture_file': 'meshes.json', 'fixture_sha256': sha(HERE/'meshes.json'),
              'sample_hz': 90, 'capture_index': CAPTURE_INDEX, 'capture_age_ms': frame['age_ns']/1e6,
              'tail_vertices': frame['after']['core_vertex_offset'],
              'candidate_vertices': len(frame['after']['positions']),
              'before_triangles': len(frame['before']['indices'])//3,
              'candidate_triangles': len(frame['after']['indices'])//3,
              'verification': {'baseline_equals_candidate_tail_geometry_and_alpha': True,
                  'finite_nondegenerate_triangles_and_valid_indices': True, 'same_camera_for_before_after': True},
              'images': images, 'limitations': ['Offline software alpha projection, not SDK or device capture.',
                'Production desktop synthetic poses, not real controller recording.',
                'No scene occlusion, bloom, exposure or SDK tone mapping; color values mapped directly to display RGB.',
                'Distance is camera-to-tail-bounds-centre; camera direction is head-to-target, fixed per comparison.',
                'No normal-distance VR readability or timing acceptance claim.']}
    (HERE/'review.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'capture_ms':report['capture_age_ms'],'images':[i['file'] for i in images]}))


if __name__ == '__main__':
    main()
