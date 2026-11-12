"""Render the current formal overhead and its fine candidate at one fixed 1.5m camera.

Only Blender entry point: hand-poses/run_blender.py -b --factory-startup --threads 2
Baseline identity is the current formal KTX2 GLB; the byte-verified current PNG
encoding is imported because Blender cannot read KHR_texture_basisu. No motion,
skin, mesh, weapon, node, or material semantics are substituted.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REVIEW = HERE / 'review'
FORMAL = REPO / 'app/src/main/assets/models/opponents/base.glb'
PROFILE = FORMAL.with_name('base_attack_profiles.json')
CHARACTERS = REPO / 'ArtSource/tripo-warrior/library/characters.json'
PNG_VIEW = REPO / 'ArtSource/tripo-warrior/library/base_prepared_png.glb'
POSES = [(0., 'guard'), (.65, 'lift'), (1., 'contact'), (1.1, 'follow'), (1.75, 'recover')]
CLIP = 'attack_overhead'
DURATION = 1.75


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def glb(path):
    data = path.read_bytes()
    if struct.unpack_from('<III', data) != (0x46546c67, 2, len(data)):
        raise ValueError('Invalid GLB ' + str(path))
    size, kind = struct.unpack_from('<II', data, 12)
    if kind != 0x4e4f534a:
        raise ValueError('Expected GLB JSON')
    doc = json.loads(data[20:20 + size])
    bin_size, bin_kind = struct.unpack_from('<II', data, 20 + size)
    if bin_kind != 0x004e4942:
        raise ValueError('Expected GLB BIN')
    binary = data[28 + size:28 + size + bin_size]
    return doc, binary


def verify_png_view():
    formal, fb = glb(FORMAL)
    png, pb = glb(PNG_VIEW)
    def semantics(doc, encoded):
        doc = copy.deepcopy(doc)
        doc['buffers'][0].pop('byteLength', None)
        for view in doc['bufferViews']:
            view.pop('byteOffset', None)
        for image in doc['images']:
            doc['bufferViews'][image['bufferView']].pop('byteLength', None)
            image.pop('mimeType', None)
        if encoded:
            for texture in doc['textures']:
                texture['source'] = texture.pop('extensions')['KHR_texture_basisu']['source']
            for field in ('extensionsRequired', 'extensionsUsed'):
                if doc.pop(field) != ['KHR_texture_basisu']:
                    raise ValueError('Unexpected formal extensions')
        return doc
    if semantics(formal, True) != semantics(png, False):
        raise ValueError('Current PNG view differs from formal non-image JSON semantics')
    images = {image['bufferView'] for image in formal['images']}
    count = 0
    for i, view in enumerate(formal['bufferViews']):
        if i in images:
            continue
        other = png['bufferViews'][i]
        a, b = view.get('byteOffset', 0), other.get('byteOffset', 0)
        if fb[a:a + view['byteLength']] != pb[b:b + other['byteLength']]:
            raise ValueError('Current PNG view differs from formal non-image bytes ' + str(i))
        count += 1
    profile = json.loads(PROFILE.read_text())
    characters = json.loads(CHARACTERS.read_text())
    actor = next(row for row in characters['characters'] if row['id'] == 'base')
    formal_sha, profile_sha = identity(FORMAL)['sha256'], identity(PROFILE)['sha256']
    if profile['model_sha256'] != formal_sha:
        raise ValueError('Current formal profile/model SHA mismatch')
    if next(row for row in actor['outputs'] if row['file'] == 'base.glb')['sha256'] != formal_sha:
        raise ValueError('Current character metadata/formal SHA mismatch')
    if actor['attack_profiles']['sha256'] != profile_sha:
        raise ValueError('Current character metadata/profile SHA mismatch')
    if profile['attacks']['OVERHEAD']['source_range_seconds'] != [0., DURATION]:
        raise ValueError('Formal overhead duration changed')
    return {'non_image_json_semantics_identical': True, 'non_image_bufferViews_byte_identical': count,
            'image_encoding_scope': 'current PNG source of formal KTX2 encoding; mesh, skin, weapon and every animation byte verified unchanged',
            'formal_overhead_animation_semantics_sha256': profile['attacks']['OVERHEAD']['animation_semantics_sha256']}


def clip_time_contract(path):
    doc, binary = glb(path)
    clips = [row for row in doc.get('animations', []) if row.get('name') == CLIP]
    if len(clips) != 1:
        raise ValueError('Expected one candidate attack_overhead animation')
    result = []
    for index in sorted({row['input'] for row in clips[0]['samplers']}):
        accessor = doc['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != 'SCALAR' or accessor.get('sparse'):
            raise ValueError('Expected dense float32 source seconds')
        view = doc['bufferViews'][accessor['bufferView']]
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        stride = view.get('byteStride', 4)
        values = [struct.unpack_from('<f', binary, start + i * stride)[0] for i in range(accessor['count'])]
        if not values or not all(math.isfinite(value) for value in values) or any(a >= b for a, b in zip(values, values[1:])):
            raise ValueError('Source seconds must be strictly increasing and finite')
        result.append({'input_accessor': index, 'source_range_seconds': [values[0], values[-1]], 'key_count': len(values)})
    if not result or abs(min(row['source_range_seconds'][0] for row in result)) > .0000001 or \
            abs(max(row['source_range_seconds'][1] for row in result) - DURATION) > .0000001:
        raise ValueError('Candidate actual GLB source range must be0–1.75s')
    return {'clip': CLIP, 'source_range_seconds': [0., DURATION], 'channel_count': len(clips[0]['channels']), 'sampler_inputs': result}


def candidate_metadata_contract(candidate, metadata_path):
    metadata = json.loads(metadata_path.read_text())
    if metadata.get('clip') != CLIP or metadata.get('source_range_seconds') != [0., DURATION]:
        raise ValueError('Candidate metadata must identify attack_overhead and source0–1.75s')
    outputs = [row for row in metadata.get('preview_outputs', []) if row.get('file') == candidate.name]
    if len(outputs) != 1 or outputs[0].get('sha256') != identity(candidate)['sha256']:
        raise ValueError('Candidate metadata preview SHA does not match the actual GLB')
    return {'clip': metadata['clip'], 'source_range_seconds': metadata['source_range_seconds'],
            'preview_output': outputs[0]}


def bone_points(armature, imported):
    result = {}
    for name in ('Head', 'Hip', 'R_Hand', 'L_Hand', 'R_Foot', 'L_Foot', 'Blade_Base', 'Blade_Tip'):
        bone = armature.pose.bones.get(name)
        if bone is not None:
            point = armature.matrix_world @ bone.matrix.translation
        else:
            landmarks = [obj for obj in imported if obj.name == name]
            if len(landmarks) != 1:
                raise ValueError('Missing actual source landmark ' + name)
            point = landmarks[0].matrix_world.translation
        result[name] = [point.x, point.z, -point.y]
    return result


def actual_skin_bounds(objects):
    import bpy
    dependency = bpy.context.evaluated_depsgraph_get()
    low, high, total, names = [float('inf')] * 3, [-float('inf')] * 3, 0, []
    for obj in objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        # Imported rendered geometry only. Floor, lights and helpers are absent.
        evaluated = obj.evaluated_get(dependency)
        mesh = evaluated.to_mesh()
        try:
            if not mesh.vertices:
                continue
            names.append(obj.name)
            for vertex in mesh.vertices:
                point = evaluated.matrix_world @ vertex.co
                for axis in range(3):
                    low[axis] = min(low[axis], point[axis])
                    high[axis] = max(high[axis], point[axis])
                total += 1
        finally:
            evaluated.to_mesh_clear()
    if not total:
        raise ValueError('No actual imported skin/weapon vertices')
    return {'min_blender': low, 'max_blender': high, 'vertices': total, 'meshes': names}


def write_manifest(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def render(args):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    proof = verify_png_view()
    profile = json.loads(PROFILE.read_text())
    hit = module('fine_direct_actions', HERE.parent / 'attack-keyposes/stage8/render_hit_reactions.py')
    common = module('fine_geometry', HERE.parent / 'attack-keyposes/render_attack_keyposes.py')
    studio = module('fine_studio', HERE.parents[1] / 'grip/render_grip_candidates.py')
    pins = {name: identity(path) for name, path in [('formal', FORMAL), ('profile', PROFILE), ('characters', CHARACTERS), ('png_encoding_view', PNG_VIEW)]}
    source = PNG_VIEW
    candidate_contract = None
    if args.stage == 'after':
        if args.candidate is None or args.metadata is None:
            raise ValueError('Candidate and metadata are required for after render')
        pins['candidate'] = identity(args.candidate)
        pins['candidate_metadata'] = identity(args.metadata)
        source = args.candidate
        candidate_contract = clip_time_contract(source)
        candidate_contract['metadata_match'] = candidate_metadata_contract(source, args.metadata)
    output = REVIEW / 'measurements' / args.stage / args.mode if args.measure_only else REVIEW / args.stage / args.mode
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / 'render_manifest.json'
    source_times = [seconds for seconds, label in POSES]
    if args.mode == 'movie':
        count = math.floor(DURATION * args.fps)
        # Retain the exact authored endpoint in the final partial display frame.
        source_times = [i / args.fps for i in range(count)] + [DURATION]
    manifest = {'completion': 'rendering', 'inputs': pins, 'stage': args.stage, 'mode': args.mode,
                'clip': CLIP, 'duration_seconds': DURATION, 'source_times_seconds': source_times,
                'images_rendered': not args.measure_only,
                'fps': args.fps, 'size': args.size, 'samples': args.samples, 'formal_png_equivalence': proof,
                'candidate_actual_time_contract': candidate_contract,
                'pose_evaluation': 'direct native imported Action and action_slot; NLA disabled; no sample epsilon',
                'camera': {'projection': 'perspective', 'horizontal_standoff_metres': 1.5,
                           'eye_height_metres': 1.62, 'aim_height_metres': 1.1, 'vertical_fov_degrees': 100.,
                           'location_gltf': [0, 1.62, 1.5], 'aim_gltf': [0, 1.1, 0],
                           'scope': 'offline single fixed camera; identical before/after; no actor or time rebase'},
                'keyposes': [{'source_seconds': s, 'label': label} for s, label in POSES], 'frames': []}
    reusable = set()
    if args.resume:
        previous = json.loads(manifest_path.read_text())
        for key in ('inputs', 'stage', 'mode', 'source_times_seconds', 'fps', 'size', 'samples'):
            if previous.get(key) != manifest[key]:
                raise ValueError('Resume render contract differs: ' + key)
        if any(previous['camera'].get(key) != value for key, value in manifest['camera'].items()):
            raise ValueError('Resume camera differs')
        previously_verified = set(previous.get('resumed_image_indices', []))
        previously_verified.update(row['index'] for row in previous['frames']
                                   if 0 <= row['index'] < len(source_times) and row['source_seconds'] == source_times[row['index']])
        for index in sorted(previously_verified):
            if not 0 <= index < len(source_times):
                raise ValueError('Resume image index is outside the verified time table')
            png = output / f'frame_{index:03d}.png'
            if png.is_file():
                data = png.read_bytes()
                if data[:8] == b'\x89PNG\r\n\x1a\n' and data[-12:] == b'\x00\x00\x00\x00IEND\xaeB`\x82':
                    reusable.add(index)
    manifest['resumed_image_indices'] = sorted(reusable)
    write_manifest(manifest_path, manifest)
    scene, camera = studio.setup_scene(args.size, args.samples)
    bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
    imported = list(bpy.context.selected_objects)
    armatures = [obj for obj in imported if obj.type == 'ARMATURE']
    if len(armatures) != 1:
        raise ValueError('Expected one actual source armature')
    armature = armatures[0]
    camera.data.type, camera.data.sensor_fit = 'PERSP', 'VERTICAL'
    camera.data.angle_y = math.radians(100.)
    camera.location = common.to_blender((0, 1.62, 1.5))
    target = Vector(common.to_blender((0, 1.1, 0)))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    # Keep the floor at the actual formal entry sole surface, same for both stages.
    floor_record = REVIEW / 'floor_reference.json'
    if args.stage == 'before':
        hit.select_action(scene, CLIP, 0.)
        floor_z = actual_skin_bounds(imported)['min_blender'][2]
        write_manifest(floor_record, {'formal_sha256': pins['formal']['sha256'], 'floor_blender_z': floor_z,
                                      'source': 'minimum actual rendered skin/weapon entry bounds, no helper bounds'})
    else:
        floor = json.loads(floor_record.read_text())
        if floor['formal_sha256'] != pins['formal']['sha256']:
            raise ValueError('Floor baseline changed')
        floor_z = floor['floor_blender_z']
    floor_mat = common.material('Fine overhead floor', (.075, .09, .11))
    grid_mat = common.material('Fine overhead quarter metre grid', (.20, .25, .28))
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, floor_z - .006))
    bpy.context.object.data.materials.append(floor_mat)
    for index in range(-6, 7):
        value = index * .25
        common.line('Grid X', [(-1.5, floor_z + .002, value), (1.5, floor_z + .002, value)], grid_mat, .001)
        common.line('Grid Z', [(value, floor_z + .002, -1.5), (value, floor_z + .002, 1.5)], grid_mat, .001)
    manifest['floor_blender_z'] = floor_z
    manifest['camera'].update(actual_vertical_fov_degrees=math.degrees(camera.data.angle_y),
                              location_blender=list(camera.location), rotation_euler=list(camera.rotation_euler))
    for index, seconds in enumerate(source_times):
        evaluation = hit.select_action(scene, CLIP, seconds)
        anchors = bone_points(armature, imported)
        if args.stage == 'before':
            reference = min(profile['attacks']['OVERHEAD']['samples'], key=lambda row: abs(row['source_seconds'] - seconds))
            if abs(reference['source_seconds'] - seconds) < .0001:
                expected = {'Head': reference['head_origin'], 'Hip': reference['hip']}
                errors = {bone: math.dist(anchors[bone], point) for bone, point in expected.items()}
                if max(errors.values()) > .0002:
                    raise ValueError('Formal action endpoint/profile anchor mismatch ' + str(errors))
                evaluation['formal_profile_anchor_errors_metres'] = errors
        projected = {}
        for name, point in anchors.items():
            ndc = world_to_camera_view(scene, camera, Vector(common.to_blender(point)))
            projected[name] = {'ndc': list(ndc), 'in_frame': 0 <= ndc.x <= 1 and 0 <= ndc.y <= 1 and ndc.z > 0}
        row = {'index': index, 'source_seconds': seconds, 'action_evaluation': evaluation,
               'anchors_gltf_metres': anchors, 'anchor_projections': projected,
               'actual_rendered_bounds': actual_skin_bounds(imported)}
        manifest['frames'].append(row)
        write_manifest(manifest_path, manifest)
        scene.render.filepath = str(output / f'frame_{index:03d}.png')
        if not args.measure_only and index not in reusable:
            bpy.ops.render.render(write_still=True)
        print('FINE_OVERHEAD_FRAME', args.stage, args.mode, index, seconds, flush=True)
    for pin in pins.values():
        if identity(pin['path']) != pin:
            raise ValueError('Input changed during render ' + pin['path'])
    manifest['completion'] = 'complete'
    write_manifest(manifest_path, manifest)


def assemble(args):
    from PIL import Image, ImageDraw, ImageFont
    import subprocess

    stages = ['before', 'after'] if args.compare else [args.stage]
    records = [json.loads((REVIEW / stage / args.mode / 'render_manifest.json').read_text()) for stage in stages]
    if any(record['completion'] != 'complete' for record in records):
        raise ValueError('All renders must be complete')
    record = records[0]
    if any(row['camera'] != record['camera'] or row['source_times_seconds'] != record['source_times_seconds'] or
           row['size'] != record['size'] or row['samples'] != record['samples'] or
           any(row['inputs'][name] != record['inputs'][name] for name in ('formal', 'profile', 'characters', 'png_encoding_view')) for row in records):
        raise ValueError('Before/after camera, source times, or size differs')
    output = REVIEW / ('comparison' if args.compare else args.stage) / args.mode
    output.mkdir(parents=True, exist_ok=True)
    size, header, footer = record['size'], 62, 50
    font_path = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    font = ImageFont.truetype(font_path, 21)
    small = ImageFont.truetype(font_path, 16)
    panels = []
    for index, seconds in enumerate(record['source_times_seconds']):
        panel = Image.new('RGB', (size * len(stages), size + header + footer), (24, 29, 35))
        draw = ImageDraw.Draw(panel)
        for column, (stage, source) in enumerate(zip(stages, records)):
            panel.paste(Image.open(REVIEW / stage / args.mode / f'frame_{index:03d}.png').convert('RGB'), (column * size, header))
            label = 'Current formal overhead' if stage == 'before' else 'Fine overhead candidate'
            sha = source['inputs']['formal' if stage == 'before' else 'candidate']['sha256'][:12]
            draw.text((column * size + 10, 5), label, font=font, fill='white')
            draw.text((column * size + 10, 32), f'source {seconds:.6f}s / {sha}', font=small, fill=(190, 205, 220))
        draw.text((10, size + header + 5), '1.50m / eye1.62m / aim1.10m / vertical FOV100 / fixed offline perspective', font=small, fill=(190, 205, 220))
        detail = 'Direct Action + slot / full source0–1.75s / no motion or actor rebase'
        if args.compare and args.mode == 'movie':
            detail = 'Before blade tip clips 3 frames at source .867–.933s / identical camera / full 1.75s source'
        draw.text((10, size + header + 27), detail, font=small, fill=(190, 205, 220))
        panel.save(output / f'panel_{index:03d}.png')
        panels.append(panel)
    if args.mode == 'poses':
        sheet = Image.new('RGB', (panels[0].width, panels[0].height * len(panels)), (24, 29, 35))
        for i, panel in enumerate(panels):
            sheet.paste(panel, (0, i * panel.height))
        sheet.save(output / 'overhead_five_keyposes.png')
        compact_size = 320
        compact_tile_height = compact_size + header
        compact = Image.new('RGB', (compact_size * len(POSES), compact_tile_height * len(stages)), (24, 29, 35))
        compact_draw = ImageDraw.Draw(compact)
        for row, (stage, source) in enumerate(zip(stages, records)):
            label = 'Current formal' if stage == 'before' else 'Fine candidate'
            sha = source['inputs']['formal' if stage == 'before' else 'candidate']['sha256'][:10]
            label += ' / ' + sha
            for column, (seconds, pose) in enumerate(POSES):
                x, y = column * compact_size, row * compact_tile_height
                image = Image.open(REVIEW / stage / args.mode / f'frame_{column:03d}.png').convert('RGB')
                compact.paste(image.resize((compact_size, compact_size), Image.Resampling.LANCZOS), (x, y + header))
                compact_draw.text((x + 8, y + 5), label, font=font, fill='white')
                compact_draw.text((x + 8, y + 32), f'{pose} / source {seconds:.2f}s', font=small, fill=(190, 205, 220))
        compact.save(output / 'overhead_five_keyposes_compact.png')
        # Full resolution single keyposes remain easy to inspect individually.
        for (seconds, label), panel in zip(POSES, panels):
            panel.save(output / f'overhead_{label}_{round(seconds * 1000):04d}.png')
    else:
        # 1.75s is52.5 frames at30fps. A VFR final half-frame preserves
        # exact duration; the final image explicitly samples authored source1.75.
        fps = record['fps']
        concat = output / 'frames.ffconcat'
        times = record['source_times_seconds']
        lines = ['ffconcat version 1.0']
        for i, seconds in enumerate(times):
            lines += [f"file 'panel_{i:03d}.png'", 'option framerate 60']
            duration = 1 / fps if i + 1 < len(times) else DURATION - i / fps
            lines += [f'duration {duration:.9f}']
        concat.write_text('\n'.join(lines) + '\n')
        video = output / f'overhead_full_source_1p75s_{fps}fps.mp4'
        subprocess.run(['/opt/homebrew/bin/ffmpeg', '-y', '-loglevel', 'error', '-safe', '0', '-f', 'concat', '-i', str(concat),
                        '-t', '1.75', '-fps_mode', 'vfr', '-enc_time_base', '1:60',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-video_track_timescale', '60000', str(video)], check=True)
        probe = subprocess.run(['/opt/homebrew/bin/ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(video)],
                               check=True, capture_output=True, text=True)
        inspection = json.loads(probe.stdout)
        if abs(float(inspection['format']['duration']) - DURATION) > .001:
            raise ValueError('Movie duration differs from1.75s')
        write_manifest(output / 'video_timing.json', {'source_sample_rate_hz': fps, 'nominal_video_fps': fps,
                       'duration_seconds': DURATION, 'last_authored_source_seconds': DURATION,
                       'final_display_frame_duration_seconds': DURATION - (len(times) - 1) / fps,
                       'timing_note': f'{fps}fps nominal/VFR; exact source1.75 endpoint replaces the last regular sample and occupies the final partial frame; no slow motion',
                       'ffprobe': inspection, 'video': identity(video)})
    print('FINE_OVERHEAD_ASSEMBLED', output, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('before', 'after'), default='before')
    parser.add_argument('--mode', choices=('poses', 'movie'), default='poses')
    parser.add_argument('--size', type=int, default=640)
    parser.add_argument('--samples', type=int, default=4)
    parser.add_argument('--fps', type=int, choices=(15, 30), default=30)
    parser.add_argument('--candidate', type=Path)
    parser.add_argument('--metadata', type=Path)
    parser.add_argument('--compare', action='store_true')
    parser.add_argument('--measure-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--assemble-only', action='store_true')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.size < 128 or args.size % 2 or args.samples < 1:
        parser.error('Use even size>=128 and positive sample count')
    REVIEW.mkdir(parents=True, exist_ok=True)
    if args.assemble_only:
        assemble(args)
    else:
        render(args)


if __name__ == '__main__':
    main()
