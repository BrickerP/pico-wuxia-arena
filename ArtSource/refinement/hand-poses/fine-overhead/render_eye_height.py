"""Frozen-source overhead diagnosis from two horizontal eye-height cameras.

Use only hand-poses/run_blender.py -b --factory-startup --threads 2.
The saved camera_set.json can be passed unchanged to a later candidate.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DEFAULT_OUTPUT = HERE / 'review/eye-height-v7'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


BASE = load('eye_height_existing_renderer', HERE / 'render_fine_overhead.py')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def camera_set(path):
    data = json.loads(path.read_text())
    if data['projection'] != 'perspective' or data['vertical_fov_degrees'] <= 0:
        raise ValueError('Expected a perspective camera contract')
    if data['actor_transform_policy'] != 'unchanged imported source; no recenter, carrier, or lift':
        raise ValueError('Actor transform must remain the imported source')
    for view in data['views'].values():
        if view['location_gltf'][1] != 1.62 or view['aim_gltf'][1] != 1.62:
            raise ValueError('Both eye and aim must be at1.62m: horizontal optical axis')
    return data


def inputs(args):
    proof = BASE.verify_png_view()
    pins = {name: BASE.identity(path) for name, path in (
        ('formal', BASE.FORMAL), ('profile', BASE.PROFILE), ('characters', BASE.CHARACTERS),
        ('png_encoding_view', BASE.PNG_VIEW), ('candidate', args.candidate),
        ('candidate_metadata', args.metadata), ('camera_set', args.camera_set),
        ('renderer', Path(__file__)), ('base_renderer', HERE / 'render_fine_overhead.py'))}
    contract = BASE.clip_time_contract(args.candidate)
    contract['metadata_match'] = BASE.candidate_metadata_contract(args.candidate, args.metadata)
    attack = json.loads(BASE.PROFILE.read_text())['attacks']['OVERHEAD']
    phase = dict(zip(('start', 'preparation_end', 'startup_end', 'active_end', 'recovery_end'), attack['source_phase_seconds']))
    phase['contact'] = attack['contact_source_seconds']
    record = {'created_local': datetime.datetime.now().astimezone().isoformat(), 'inputs': pins,
              'candidate_actual_time_contract': contract, 'current_phase_markers_seconds': phase,
              'formal_png_equivalence': proof, 'scope': 'new source diagnosis phase; historical review pins are unchanged'}
    phase_path = args.output / 'phase_inputs.json'
    if phase_path.exists():
        previous = json.loads(phase_path.read_text())
        if previous['inputs'] != pins:
            raise ValueError('This output phase already pins different input identities')
    else:
        save(phase_path, record)
    return record


def source_times(mode):
    if mode == 'poses':
        return [time for time, label in BASE.POSES]
    return [index / 30 for index in range(52)] + [1.75]


def geometry_points(imported):
    import bpy
    import numpy as np
    dependency = bpy.context.evaluated_depsgraph_get()
    blocks, names = [], []
    for obj in imported:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(dependency)
        mesh = evaluated.to_mesh()
        try:
            if mesh.vertices:
                local = np.array([tuple(vertex.co) for vertex in mesh.vertices], dtype=np.float64)
                matrix = np.array(evaluated.matrix_world, dtype=np.float64)
                blocks.append(local @ matrix[:3, :3].T + matrix[:3, 3])
                names.append(obj.name)
        finally:
            evaluated.to_mesh_clear()
    if not blocks:
        raise ValueError('No actual skin and weapon vertices')
    return np.concatenate(blocks), names


def projection(points, camera, vfov):
    import numpy as np
    inverse = np.array(camera.matrix_world.inverted(), dtype=np.float64)
    local = points @ inverse[:3, :3].T + inverse[:3, 3]
    depth = -local[:, 2]
    half_span = 2 * math.tan(math.radians(vfov) / 2)
    ndc = .5 + local[:, :2] / (depth[:, None] * half_span)
    outside = (depth <= 0) | (ndc[:, 0] < 0) | (ndc[:, 0] > 1) | (ndc[:, 1] < 0) | (ndc[:, 1] > 1)
    return {'vertex_count': len(points), 'outside_vertex_count': int(np.count_nonzero(outside)),
            'minimum_ndc_xy': ndc.min(axis=0).tolist(), 'maximum_ndc_xy': ndc.max(axis=0).tolist(),
            'minimum_camera_depth_metres': float(depth.min())}


def source_diagnosis(armature, neutral_head_rotation):
    from mathutils import Vector
    head = armature.matrix_world @ armature.pose.bones['Head'].matrix
    current_rotation = head.to_quaternion()
    forward = (current_rotation @ neutral_head_rotation.inverted()) @ Vector((0, -1, 0))
    forward_gltf = [forward.x, forward.z, -forward.y]
    hip = armature.matrix_world @ armature.pose.bones['Hip'].matrix.translation
    spine = armature.matrix_world @ armature.pose.bones['Spine02'].matrix.translation
    torso = spine - hip
    return {'head_forward_gltf_guard_calibrated': forward_gltf,
            'head_forward_pitch_from_guard_degrees': math.degrees(math.atan2(forward_gltf[1], math.hypot(forward_gltf[0], forward_gltf[2]))),
            'head_forward_calibration': 'world glTF+Z at canonical guard, transported by Head world rotation delta; not an anatomical surface-normal claim',
            'head_world_matrix_blender': [list(row) for row in head],
            'hip_to_spine02_forward_lean_degrees': math.degrees(math.atan2(-torso.y, torso.z))}


def render(args):
    import bpy
    import numpy as np
    from mathutils import Vector

    args.output.mkdir(parents=True, exist_ok=True)
    data = camera_set(args.camera_set)
    phase = inputs(args)
    studio = load('eye_height_studio', HERE.parents[1] / 'grip/render_grip_candidates.py')
    common = load('eye_height_geometry', HERE.parent / 'attack-keyposes/render_attack_keyposes.py')
    direct = load('eye_height_direct', HERE.parent / 'attack-keyposes/stage8/render_hit_reactions.py')
    scene, original_camera = studio.setup_scene(args.size, args.samples)
    bpy.ops.import_scene.gltf(filepath=str(args.candidate.resolve()))
    imported = list(bpy.context.selected_objects)
    armatures = [obj for obj in imported if obj.type == 'ARMATURE']
    if len(armatures) != 1:
        raise ValueError('Expected one imported source armature')
    armature = armatures[0]
    direct.select_action(scene, BASE.CLIP, 0.)
    neutral_rotation = (armature.matrix_world @ armature.pose.bones['Head'].matrix).to_quaternion()
    cameras = {}
    for name, value in data['views'].items():
        camera_data = original_camera.data.copy()
        camera_data.type, camera_data.sensor_fit = 'PERSP', 'VERTICAL'
        camera_data.angle_y = math.radians(data['vertical_fov_degrees'])
        camera = bpy.data.objects.new(name + ' eye-height camera', camera_data)
        scene.collection.objects.link(camera)
        camera.location = common.to_blender(value['location_gltf'])
        target = Vector(common.to_blender(value['aim_gltf']))
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        cameras[name] = camera
    floor_z = data['floor_blender_z']
    floor = common.material('Eye-height source floor', (.075, .09, .11))
    grid = common.material('Eye-height source grid', (.20, .25, .28))
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, floor_z - .006))
    bpy.context.object.data.materials.append(floor)
    for index in range(-7, 8):
        distance = index * .25
        common.line('Grid X', [(-1.75, floor_z + .002, distance), (1.75, floor_z + .002, distance)], grid, .001)
        common.line('Grid Z', [(distance, floor_z + .002, -1.75), (distance, floor_z + .002, 1.75)], grid, .001)
    bpy.context.view_layer.update()
    mode = 'measurements' if args.mode == 'measure' else args.mode
    record = {'completion': 'measuring' if args.mode == 'measure' else 'rendering', 'inputs': phase['inputs'],
              'current_phase_markers_seconds': phase['current_phase_markers_seconds'], 'camera_set': data,
              'mode': args.mode, 'size': args.size, 'samples': args.samples, 'source_times_seconds': source_times(args.mode),
              'source_evaluation': 'direct imported Action + action_slot; NLA disabled; no epsilon or actor transform',
              'camera_optical_axis_vertical_pitch_degrees': 0., 'frames': [], 'cameras': {}}
    for name, camera in cameras.items():
        record['cameras'][name] = {**data['views'][name], 'matrix_world_blender': [list(row) for row in camera.matrix_world],
                                  'actual_vertical_fov_degrees': math.degrees(camera.data.angle_y)}
        (args.output / name / mode).mkdir(parents=True, exist_ok=True)
    manifest = args.output / mode / 'render_manifest.json'
    save(manifest, record)
    for index, seconds in enumerate(record['source_times_seconds']):
        evaluation = direct.select_action(scene, BASE.CLIP, seconds)
        points, meshes = geometry_points(imported)
        row = {'index': index, 'source_seconds': seconds, 'action_evaluation': evaluation,
               'anchors_gltf_metres': BASE.bone_points(armature, imported),
               'source_diagnosis': source_diagnosis(armature, neutral_rotation),
               'actual_geometry_bounds_blender': {'min': points.min(axis=0).tolist(), 'max': points.max(axis=0).tolist(),
                                                'vertex_count': len(points), 'meshes': meshes}, 'views': {}}
        for name, camera in cameras.items():
            row['views'][name] = projection(points, camera, data['vertical_fov_degrees'])
            if row['views'][name]['outside_vertex_count']:
                raise ValueError(f'{name} source{seconds:.6f} has actual geometry outside the frame: {row["views"][name]}')
            if args.mode != 'measure':
                scene.camera = camera
                scene.render.filepath = str(args.output / name / mode / f'frame_{index:03d}.png')
                bpy.ops.render.render(write_still=True)
        record['frames'].append(row)
        save(manifest, record)
        print('EYE_HEIGHT_SOURCE', args.mode, index, seconds, flush=True)
    for pin in phase['inputs'].values():
        if BASE.identity(pin['path']) != pin:
            raise ValueError('Pinned phase input changed: ' + pin['path'])
    record['completion'] = 'complete'
    save(manifest, record)


def movie_artifacts(directory, panels):
    from PIL import Image
    import subprocess

    lines = ['ffconcat version 1.0']
    for index, panel in enumerate(panels):
        lines += [f"file 'panel_{index:03d}.png'", 'option framerate 60',
                  f'duration {(1 / 30 if index < len(panels) - 1 else 1 / 60):.9f}']
    concat = directory / 'frames.ffconcat'
    concat.write_text('\n'.join(lines) + '\n')
    video = directory / 'full_source_1p75s_30fps.mp4'
    subprocess.run(['/opt/homebrew/bin/ffmpeg', '-y', '-loglevel', 'error', '-safe', '0', '-f', 'concat', '-i', str(concat),
                    '-t', '1.75', '-fps_mode', 'vfr', '-enc_time_base', '1:60', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-video_track_timescale', '60000', str(video)], check=True)
    probe = json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe', '-v', 'error', '-show_streams', '-show_format',
                                       '-of', 'json', str(video)], check=True, capture_output=True, text=True).stdout)
    if abs(float(probe['format']['duration']) - 1.75) > .001 or int(probe['streams'][0]['nb_frames']) != 53:
        raise ValueError('Source movie timing contract failed')
    save(directory / 'video_timing.json', {'source_sample_rate_hz': 30, 'duration_seconds': 1.75,
         'endpoint_source_seconds': 1.75, 'final_display_frame_duration_seconds': 1 / 60,
         'timing_note': 'nominal30fps VFR; source1.75 occupies the final half-frame', 'ffprobe': probe, 'video': BASE.identity(video)})
    tile_width = max(240, panels[0].width // 2)
    tile_height = round(panels[0].height * tile_width / panels[0].width)
    columns = 7
    mosaic = Image.new('RGB', (tile_width * columns, tile_height * math.ceil(len(panels) / columns)), (24, 29, 35))
    for index, panel in enumerate(panels):
        mosaic.paste(panel.resize((tile_width, tile_height), Image.Resampling.LANCZOS),
                     ((index % columns) * tile_width, (index // columns) * tile_height))
    mosaic.save(directory / 'all_53_source_frames_mosaic.png')


def assemble(args):
    from PIL import Image, ImageDraw, ImageFont
    import subprocess

    record = json.loads((args.output / args.mode / 'render_manifest.json').read_text())
    if record['completion'] != 'complete':
        raise ValueError('The source pass is incomplete')
    font_path = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    font = ImageFont.truetype(font_path, 18)
    small = ImageFont.truetype(font_path, 14)
    size, header, footer = record['size'], 58, 46
    sha = record['inputs']['candidate']['sha256'][:12]
    for view in record['cameras']:
        directory = args.output / view / args.mode
        panels = []
        for row in record['frames']:
            panel = Image.new('RGB', (size, size + header + footer), (24, 29, 35))
            panel.paste(Image.open(directory / f'frame_{row["index"]:03d}.png').convert('RGB'), (0, header))
            draw = ImageDraw.Draw(panel)
            draw.text((9, 4), f'{view} / frozen source {sha}', font=font, fill='white')
            draw.text((9, 30), f'source {row["source_seconds"]:.6f}s / Head pitch from guard {row["source_diagnosis"]["head_forward_pitch_from_guard_degrees"]:+.1f}deg', font=small, fill=(190, 205, 220))
            camera = record['camera_set']
            draw.text((9, size + header + 3), f'eye=aim1.62m / horizontal axis / {camera["horizontal_standoff_metres"]:.2f}m / VFOV{camera["vertical_fov_degrees"]:.0f}', font=small, fill=(190, 205, 220))
            draw.text((9, size + header + 24), 'Unchanged actor / Direct Action+slot / source0-1.75s', font=small, fill=(190, 205, 220))
            panel.save(directory / f'panel_{row["index"]:03d}.png')
            panels.append(panel)
        if args.mode == 'poses':
            width = 320
            height = round(panels[0].height * width / panels[0].width)
            board = Image.new('RGB', (width * len(panels), height), (24, 29, 35))
            for index, panel in enumerate(panels):
                board.paste(panel.resize((width, height), Image.Resampling.LANCZOS), (index * width, 0))
            board.save(directory / 'five_source_poses.png')
        else:
            movie_artifacts(directory, panels)
        print('EYE_HEIGHT_ASSEMBLED', view, args.mode, flush=True)
    if args.reference_output is not None:
        assemble_pairs(args, record)
    save(args.output / 'review_state.json', {'state': 'waiting_review', 'completed_mode': args.mode,
         'candidate': record['inputs']['candidate'], 'camera_set': record['inputs']['camera_set'],
         'scope': 'frozen source diagnosis only; no posture change or next-phase implementation authorized here'})


def assemble_pairs(args, record):
    from PIL import Image, ImageDraw, ImageFont

    reference_path = args.reference_output / args.mode / 'render_manifest.json'
    current_path = args.output / args.mode / 'render_manifest.json'
    reference = json.loads(reference_path.read_text())
    if reference['completion'] != 'complete':
        raise ValueError('Reference source pass is incomplete')
    for key in ('source_times_seconds', 'size', 'samples', 'camera_set', 'cameras'):
        if reference[key] != record[key]:
            raise ValueError('Reference comparison contract differs: ' + key)
    for name in ('formal', 'profile', 'characters', 'png_encoding_view', 'camera_set'):
        if reference['inputs'][name] != record['inputs'][name]:
            raise ValueError('Reference phase pin differs: ' + name)
    if len(reference['frames']) != len(record['frames']):
        raise ValueError('Reference frame count differs')
    size = record['size']
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 18)
    before_sha = reference['inputs']['candidate']['sha256'][:12]
    after_sha = record['inputs']['candidate']['sha256'][:12]
    comparison = {'completion': 'complete', 'reference_manifest': BASE.identity(reference_path),
                  'current_manifest': BASE.identity(current_path), 'reference_candidate': reference['inputs']['candidate'],
                  'candidate': record['inputs']['candidate'], 'camera_set': record['inputs']['camera_set'],
                  'source_times_seconds': record['source_times_seconds'], 'reference_images_reused': True,
                  'same_camera_actor_and_source_time': True, 'frame_count': len(record['frames']), 'views': {}}
    for view in record['cameras']:
        directory = args.output / view / 'paired' / args.mode
        directory.mkdir(parents=True, exist_ok=True)
        pairs = []
        for before, after in zip(reference['frames'], record['frames']):
            if before['index'] != after['index'] or before['source_seconds'] != after['source_seconds']:
                raise ValueError('Paired source frame index or time differs')
            index = after['index']
            before_path = args.reference_output / view / args.mode / f'panel_{index:03d}.png'
            after_path = args.output / view / args.mode / f'panel_{index:03d}.png'
            old = Image.open(before_path).convert('RGB')
            new = Image.open(after_path).convert('RGB')
            if old.size != new.size or old.width != size:
                raise ValueError('Paired panel dimensions differ')
            panel = Image.new('RGB', (size * 2, old.height), (24, 29, 35))
            panel.paste(old, (0, 0))
            panel.paste(new, (size, 0))
            draw = ImageDraw.Draw(panel)
            draw.rectangle((0, 0, panel.width, 27), fill=(24, 29, 35))
            draw.text((9, 4), f'v7 before / {view} / {before_sha}', font=font, fill='white')
            draw.text((size + 9, 4), f'neck-only after / {view} / {after_sha}', font=font, fill='white')
            panel.save(directory / f'panel_{index:03d}.png')
            pairs.append(panel)
        if args.mode == 'poses':
            tile_width = 320
            tile_height = round(pairs[0].height * tile_width / size)
            board = Image.new('RGB', (tile_width * len(pairs), tile_height * 2), (24, 29, 35))
            for index, panel in enumerate(pairs):
                for stage in range(2):
                    crop = panel.crop((stage * size, 0, (stage + 1) * size, panel.height))
                    board.paste(crop.resize((tile_width, tile_height), Image.Resampling.LANCZOS),
                                (index * tile_width, stage * tile_height))
            board.save(directory / 'five_source_poses.png')
        else:
            movie_artifacts(directory, pairs)
        comparison['views'][view] = {'directory': str(directory.resolve()), 'panel_count': len(pairs)}
        print('EYE_HEIGHT_PAIRED', view, args.mode, flush=True)
    save(args.output / 'paired' / args.mode / 'comparison_manifest.json', comparison)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('measure', 'poses', 'movie'), default='measure')
    parser.add_argument('--candidate', type=Path, default=HERE / 'candidate/v7/fine_overhead_preview.glb')
    parser.add_argument('--metadata', type=Path, default=HERE / 'candidate/v7/fine_overhead_metadata.json')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--camera-set', type=Path, default=DEFAULT_OUTPUT / 'camera_set.json')
    parser.add_argument('--size', type=int, default=480)
    parser.add_argument('--samples', type=int, default=4)
    parser.add_argument('--assemble-only', action='store_true')
    parser.add_argument('--reference-output', type=Path)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.reference_output is not None and args.output.resolve().is_relative_to(args.reference_output.resolve()):
        parser.error('Output must be outside the frozen reference tree')
    if args.size < 128 or args.size % 2 or args.samples < 1:
        parser.error('Expected even size>=128 and positive samples')
    if args.assemble_only:
        if args.mode == 'measure':
            parser.error('Measurements have no image assembly')
        assemble(args)
    else:
        render(args)


if __name__ == '__main__':
    main()
