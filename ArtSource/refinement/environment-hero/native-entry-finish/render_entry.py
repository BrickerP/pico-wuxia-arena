"""Same actual full scenes, 1.65m player view and two oblique solid-volume views."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ENV = HERE.parent
ROOT = ENV.parents[2]
SOURCE = ENV / 'native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_png.glb'
AFTER = HERE / 'courtyard_entry_finish_png.glb'
LIGHTING = ENV / 'stage2/render_review.py'
VIEWS = {
    'player_1p65': {'position_stage': [0, 1.65, 0], 'target_stage': [0, 1.65, -5.35], 'lens_mm': 18},
    'joint_oblique': {'position_stage': [-.55, 2.40, -3.8], 'target_stage': [-1.4, 2.80, -5.13], 'lens_mm': 34},
    'foot_oblique': {'position_stage': [-.70, .72, -3.8], 'target_stage': [-1.4, .45, -5.24], 'lens_mm': 38},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def point(v):
    return Vector((v[0], -v[2], v[1]))


def main(phases=('before', 'after')):
    output = HERE / 'review'
    output.mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('same_entry_review_light', LIGHTING)
    light = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(light)
    previous = output / 'render_manifest.json'
    records = json.loads(previous.read_text())['phases'] if previous.exists() and phases == ('after',) else {}
    for phase, path in [('before', SOURCE), ('after', AFTER)]:
        if phase not in phases:
            continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.import_scene.gltf(filepath=str(path))
        scene, camera = light.setup('night')
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 12
        scene.cycles.use_denoising = True
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = 2
        scene.render.resolution_x = 960
        scene.render.resolution_y = 960
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'
        camera.data.sensor_width = 36
        camera.data.dof.use_dof = False
        paths = {}
        for name, view in VIEWS.items():
            camera.location = point(view['position_stage'])
            camera.rotation_euler = (point(view['target_stage']) - camera.location).to_track_quat('-Z', 'Y').to_euler()
            camera.data.lens = view['lens_mm']
            result = output / f'{name}_{phase}.png'
            scene.render.filepath = str(result)
            bpy.ops.render.render(write_still=True)
            paths[result.name] = sha(result)
        if phase == 'after':
            bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'entry_finish_full_scene.blend'))
        records[phase] = {'scene': str(path.relative_to(ROOT)), 'scene_sha256': sha(path), 'images': paths}
    manifest = {'kind': 'Actual full PNG GLB offline before/after; not native screenshots',
                'phases': records, 'views': VIEWS, 'lighting_source': str(LIGHTING.relative_to(ROOT)),
                'lighting_sha256': sha(LIGHTING), 'same_camera_lighting': True,
                'renderer': 'Cycles CPU', 'threads': 2, 'samples': 12, 'resolution': [960, 960],
                'actors_UI_hand': 'Excluded in both phases; no old actor substitution',
                'runtime_boundary': 'No device or 7f light calibration claim; original scene textures/lights unchanged by composition.'}
    (output / 'render_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('ENTRY_REVIEW_COMPLETE', sha(AFTER), flush=True)
