"""Render one frozen entrance comparison phase: Blender --python this.py -- before|after.

Root runs phases serially. These are offline images, not native PICO screenshots.
The same current PNG actor, idle pose, cameras and stage2 lighting serve both phases.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import traceback

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ENV = HERE.parent
ROOT = ENV.parents[2]
SOURCE = ENV / 'facade-polish/courtyard_facade_polish.glb'
CANDIDATE = HERE / 'courtyard_native_entrance.glb'
ACTOR = ROOT / 'ArtSource/tripo-warrior/library/base_prepared_png.glb'
LIGHT_SCRIPT = ENV / 'stage2/render_review.py'
OUT = HERE / 'review'
SOURCE_SHA = '64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605'
RUNTIME_ACTOR_SHA = '6ca12659ef6705b2fba43ace092fb8eb567df090c55849b87869e79a9031df24'
VIEWS = {
    'eye': {'position_stage': [0, 1.65, 0], 'target_stage': [0, 1.55, -5.3], 'lens_mm': 18},
    'close': {'position_stage': [.8, 1.4, -3.85], 'target_stage': [.3, .95, -5.2], 'lens_mm': 18},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage(point):
    return Vector((point[0], -point[2], point[1]))


def current_actor():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(ACTOR))
    objects = list(bpy.context.selected_objects)
    frame = bpy.data.objects.new('Review_CurrentBaseActor', None)
    bpy.context.scene.collection.objects.link(frame)
    selected_idle = 0
    for obj in objects:
        if obj.parent is None:
            obj.parent = frame
        animation = obj.animation_data
        if animation is None:
            continue
        animation.action = None
        for track in animation.nla_tracks:
            chosen = track.name == 'idle' or any(
                strip.action and strip.action.name == 'idle' for strip in track.strips
            )
            track.mute = not chosen
            if chosen:
                selected_idle += 1
                for strip in track.strips:
                    strip.frame_start = strip.action_frame_start
    if selected_idle == 0:
        raise ValueError('Current PNG actor has no idle NLA track; do not substitute another actor')
    frame.location = stage((0, .028, -2.4))
    frame.rotation_euler = (0, 0, 0)
    frame.scale = (1, 1, 1)
    bpy.context.scene.frame_set(0)
    return selected_idle


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if len(args) != 1 or args[0] not in ('before', 'after'):
        raise ValueError('Usage: Blender --background --python render_entrance.py -- before|after')
    phase = args[0]
    asset = SOURCE if phase == 'before' else CANDIDATE
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Frozen 64da source identity changed')
    actor_sha = sha(ACTOR)
    if actor_sha != '1cc9aaba1b7ee18c9c9b4be85c82f6ef93be72f9ffd3d9f18b96da920ab594bb':
        raise ValueError('Expected current 1cc9 PNG actor; no old ac7/b3 substitution')
    asset_sha = sha(asset)
    light_sha = sha(LIGHT_SCRIPT)
    OUT.mkdir(exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(asset))
    idle_tracks = current_actor()
    spec = importlib.util.spec_from_file_location('entrance_shared_stage2_lighting', LIGHT_SCRIPT)
    lighting = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lighting)
    scene, camera = lighting.setup('night')
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x = 960
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    camera.data.sensor_width = 36
    camera.data.dof.use_dof = False
    images = {}
    for name, view in VIEWS.items():
        camera.location = stage(view['position_stage'])
        camera.rotation_euler = (stage(view['target_stage']) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.lens = view['lens_mm']
        path = OUT / f'{name}_{phase}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        images[path.name] = sha(path)
    if sha(asset) != asset_sha or sha(ACTOR) != actor_sha or sha(LIGHT_SCRIPT) != light_sha:
        raise ValueError('Input changed during render; output pair is not stable')
    record = {
        'phase': phase, 'kind': 'offline actual GLB comparison; not native PICO screenshot',
        'environment_path': str(asset.relative_to(ROOT)), 'environment_sha256': asset_sha,
        'baseline_sha256': SOURCE_SHA, 'actor_png_path': str(ACTOR.relative_to(ROOT)),
        'actor_png_sha256': actor_sha, 'runtime_actor_sha256': RUNTIME_ACTOR_SHA,
        'actor_pose': 'idle@0.0s', 'actor_idle_tracks_selected': idle_tracks,
        'actor_stage_position': [0, .028, -2.4], 'actor_scale': [1, 1, 1], 'actor_yaw': 0,
        'excluded_runtime_layers': ['native UI', 'player hand/dao', 'separately mounted runtime weapon'],
        'cameras': VIEWS, 'sensor_width_mm': 36, 'dof': False,
        'lighting_source': str(LIGHT_SCRIPT.relative_to(ROOT)), 'lighting_sha256': light_sha,
        'lighting_recipe': 'stage2 setup night, unchanged between before and after',
        'renderer': 'Cycles CPU', 'threads': 2, 'samples': 8, 'resolution': [960, 960],
        'images': images,
    }
    (OUT / f'render_manifest_{phase}.json').write_text(json.dumps(record, indent=2) + '\n')
    combined = {'kind': 'offline entrance review, not native runtime proof', 'phases': {}}
    for part in ('before', 'after'):
        path = OUT / f'render_manifest_{part}.json'
        if path.exists():
            combined['phases'][part] = json.loads(path.read_text())
    if set(combined['phases']) == {'before', 'after'}:
        before, after = combined['phases']['before'], combined['phases']['after']
        combined['same_actor_camera_lighting'] = all(before[k] == after[k] for k in (
            'actor_png_sha256', 'runtime_actor_sha256', 'actor_pose', 'cameras',
            'lighting_sha256', 'lighting_recipe', 'resolution', 'samples',
        ))
        if not combined['same_actor_camera_lighting']:
            raise ValueError('Before/after identity, camera or lighting differs; rerender the pair')
    (OUT / 'render_manifest.json').write_text(json.dumps(combined, indent=2) + '\n')
    print('ENTRANCE_RENDER_COMPLETE', phase, asset_sha)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
