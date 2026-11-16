"""One fixed eye-height natural-guard pose and 1.5s idle review; no producer writes."""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OLD = HERE.parent / 'native-weighted-overhead'
BEFORE = REPO / 'ArtSource/tripo-warrior/library/base_prepared_png.glb'
BEFORE_SHA = '6649302a095e341670c4305901b0c4864d9b10e4b4196da3e69b6dd78449bd2a'
CAMERA = {'projection': 'perspective', 'eye_height_metres': 1.62,
          'aim_gltf': [0., 1.1, .1], 'horizontal_standoff_metres': 1.8,
          'azimuth_degrees': 25., 'vertical_fov_degrees': 68.,
          'scope': 'One near-medium normal eye-height view; original actor, head and grip transforms retained'}
CAMERA['location_gltf'] = [1.8 * math.sin(math.radians(25)), 1.62,
                           .1 + 1.8 * math.cos(math.radians(25))]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RENDERER = load('natural_guard_render_helpers', OLD / 'render_weighted_overhead.py')
BASE, EYE = RENDERER.BASE, RENDERER.EYE


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def render(args):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    if BASE.identity(BEFORE)['sha256'] != BEFORE_SHA:
        raise ValueError('Root-pinned current real before changed')
    if BASE.identity(args.asset)['sha256'] != args.expected_sha:
        raise ValueError('Explicit actual preview SHA mismatch')
    if args.stage == 'before' and args.expected_sha != BEFORE_SHA:
        raise ValueError('Before must be the pinned current body idle@0')
    pins = {name: BASE.identity(path) for name, path in (
        ('asset', args.asset), ('actual_before', BEFORE), ('renderer', Path(__file__)),
        ('helpers', OLD / 'render_weighted_overhead.py'), ('surface_helpers', OLD / 'integration/review_candidate.py'))}
    if args.metadata:
        pins['authoring'] = BASE.identity(args.metadata)
    reviewer = load('natural_guard_static_semantics', OLD / 'integration/review_candidate.py')
    before = reviewer.static_signature(*reviewer.library.read_glb(BEFORE))
    actual = reviewer.static_signature(*reviewer.library.read_glb(args.asset))
    static_checks = {key: before[key] == actual[key] for key in before}
    studio = load('natural_guard_studio', REPO / 'ArtSource/refinement/grip/render_grip_candidates.py')
    common = load('natural_guard_geometry', REPO / 'ArtSource/refinement/hand-poses/attack-keyposes/render_attack_keyposes.py')
    direct = load('natural_guard_direct', REPO / 'ArtSource/refinement/hand-poses/attack-keyposes/stage8/render_hit_reactions.py')
    scene, camera = studio.setup_scene(args.size, args.samples)
    bpy.ops.import_scene.gltf(filepath=str(args.asset.resolve()))
    imported = list(bpy.context.selected_objects)
    arms = [obj for obj in imported if obj.type == 'ARMATURE']
    if len(arms) != 1:
        raise ValueError('Expected one actual source armature')
    armature = arms[0]
    direct.select_action(scene, args.clip, 0.)
    actor_matrix = [list(row) for row in armature.matrix_world]
    camera.data.type, camera.data.sensor_fit = 'PERSP', 'VERTICAL'
    camera.data.angle_y = math.radians(CAMERA['vertical_fov_degrees'])
    camera.location = common.to_blender(CAMERA['location_gltf'])
    aim = Vector(common.to_blender(CAMERA['aim_gltf']))
    camera.rotation_euler = (aim - camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    floor_path = args.output / 'floor_reference.json'
    if args.stage == 'before':
        points, _ = EYE.geometry_points(imported)
        floor_record = {'actual_before': BASE.identity(BEFORE), 'clip': args.clip, 'source_seconds': 0.,
                        'floor_blender_z': float(points[:, 2].min())}
        save(floor_path, floor_record)
    else:
        floor_record = json.loads(floor_path.read_text())
        if floor_record['actual_before'] != BASE.identity(BEFORE):
            raise ValueError('Floor must derive from the same actual before')
    floor_z = floor_record['floor_blender_z']
    floor = common.material('Natural guard source floor', (.075, .09, .11))
    grid = common.material('Natural guard source grid', (.20, .25, .28))
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, floor_z - .006))
    bpy.context.object.data.materials.append(floor)
    for index in range(-6, 7):
        value = index * .25
        common.line('Grid X', [(-1.5, floor_z + .002, value), (1.5, floor_z + .002, value)], grid, .001)
        common.line('Grid Z', [(value, floor_z + .002, -1.5), (value, floor_z + .002, 1.5)], grid, .001)
    directory = args.output / args.stage / args.mode
    directory.mkdir(parents=True, exist_ok=True)
    source_times = [0.] if args.mode == 'pose' else [index / 30 for index in range(46)]
    record = {'completion': 'rendering', 'stage': args.stage, 'mode': args.mode, 'clip': args.clip,
              'size': args.size, 'samples': args.samples, 'inputs': pins,
              'static_same_actual_before_checks': static_checks,
              'source_times_seconds': source_times, 'source_duration_seconds': 1.5,
              'camera': {**CAMERA, 'matrix_world_blender': [list(row) for row in camera.matrix_world],
                         'actual_vertical_fov_degrees': math.degrees(camera.data.angle_y)},
              'actor_world_matrix_blender': actor_matrix, 'floor_reference': floor_record,
              'scope': 'Direct Action+action_slot; source clock starts0, NLA disabled, no actor carrier/recenter, no head/grip edits by renderer',
              'review_status': 'visual preview; candidate verification and Root visual acceptance separate', 'frames': []}
    destination = directory / 'render_manifest.json'
    save(destination, record)
    for index, seconds in enumerate(source_times):
        evaluation = direct.select_action(scene, args.clip, seconds)
        anchors = BASE.bone_points(armature, imported)
        projections = {}
        for name, point in anchors.items():
            p = world_to_camera_view(scene, camera, Vector(common.to_blender(point)))
            projections[name] = {'ndc': list(p), 'in_frame': 0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0}
        for name in ('Head', 'L_Hand', 'R_Hand', 'R_Foot', 'L_Foot', 'Blade_Base'):
            if not projections[name]['in_frame']:
                raise ValueError(f'Critical {name} outside fixed camera at source{seconds}')
        hand = armature.matrix_world @ armature.pose.bones['R_Hand'].matrix
        inverse = hand.inverted()
        blade_in_hand = {name: list(inverse @ Vector(common.to_blender(anchors[name]))) for name in ('Blade_Base', 'Blade_Tip')}
        points, mesh_names = EYE.geometry_points(imported)
        row = {'index': index, 'source_seconds': seconds, 'action_evaluation': evaluation,
               'anchors_gltf_metres': anchors, 'anchor_projections': projections,
               'actual_blade_landmarks_in_R_hand_frame': blade_in_hand,
               'actual_geometry_projection': EYE.projection(points, camera, CAMERA['vertical_fov_degrees']),
               'actual_geometry_mesh_names': mesh_names}
        scene.render.filepath = str(directory / f'frame_{index:03d}.png')
        bpy.ops.render.render(write_still=True)
        row['image'] = BASE.identity(directory / f'frame_{index:03d}.png')
        record['frames'].append(row)
        save(destination, record)
        print('NATURAL_GUARD', args.stage, args.mode, index, seconds, flush=True)
    for pin in pins.values():
        if BASE.identity(pin['path']) != pin:
            raise ValueError('Input changed during rendering: ' + pin['path'])
    record['completion'] = 'complete'
    save(destination, record)


def assemble(args):
    from PIL import Image, ImageDraw, ImageFont
    import subprocess

    directory = args.output / args.stage / args.mode
    record = json.loads((directory / 'render_manifest.json').read_text())
    if record['completion'] != 'complete':
        raise ValueError('Render incomplete')
    fontfile = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
    font, small = ImageFont.truetype(fontfile, 22), ImageFont.truetype(fontfile, 17)
    panels = []
    for row in record['frames']:
        size = record['size']; header, footer = 70, 54
        panel = Image.new('RGB', (size, size + header + footer), (24, 29, 35))
        panel.paste(Image.open(row['image']['path']).convert('RGB'), (0, header));draw = ImageDraw.Draw(panel)
        draw.text((10, 7), f'Natural guard / {args.stage} / {record["clip"]}', font=font, fill='white')
        draw.text((10, 37), f'source {row["source_seconds"]:.6f}s / SHA {record["inputs"]["asset"]["sha256"][:16]}', font=small, fill=(205,218,230))
        draw.text((10,size+header+5),'eye1.62m / standoff1.80m / VFOV68 / original actor + materials',font=small,fill=(205,218,230))
        draw.text((10,size+header+29),'Direct Action + slot / no actor, head or grip edit by renderer',font=small,fill=(205,218,230))
        panel.save(directory / f'panel_{row["index"]:03d}.png');panels.append(panel)
    if args.mode == 'pose':
        panels[0].save(directory / 'natural_guard_pose.png')
        if args.stage == 'after':
            previous = args.output / 'before/pose'
            before = json.loads((previous / 'render_manifest.json').read_text())
            for key in ('camera','actor_world_matrix_blender','size','samples'):
                if before[key] != record[key]:raise ValueError('Paired pose contract differs: ' + key)
            old = Image.open(previous/'panel_000.png').convert('RGB')
            board = Image.new('RGB',(old.width*2,old.height),(24,29,35));board.paste(old,(0,0));board.paste(panels[0],(old.width,0));board.save(args.output/'natural_guard_before_after.png')
    else:
        # 46 actual30Hz source samples include the exact endpoint. The45 regular
        # frames make an exact1.5s30Hz clip; source1.5 remains an endpoint still.
        video = directory / 'natural_idle_1p5s_30fps.mp4'
        subprocess.run(['/opt/homebrew/bin/ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(directory/'panel_%03d.png'),'-frames:v','45','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
        probe=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],check=True,capture_output=True,text=True).stdout)
        if abs(float(probe['format']['duration'])-1.5)>.001 or int(probe['streams'][0]['nb_frames'])!=45:raise ValueError('Exact1.5s30Hz video contract failed')
        save(directory/'video_timing.json',{'source_sample_count':46,'source_times_seconds':record['source_times_seconds'],'encoded_frame_count':45,'encoded_duration_seconds':1.5,'endpoint_still':record['frames'][-1]['image'],'endpoint_policy':'True source0..1.5 sampled30Hz inclusive; exact endpoint retained as still,45 regular frames encode1.5s at30Hz without time warp.','video':BASE.identity(video),'ffprobe':probe})
        width=240;height=round(panels[0].height*width/panels[0].width)
        mosaic=Image.new('RGB',(width*7,height*7),(24,29,35))
        for index,panel in enumerate(panels):mosaic.paste(panel.resize((width,height),Image.Resampling.LANCZOS),((index%7)*width,(index//7)*height))
        mosaic.save(directory/'all_46_source_samples.png')
    print('NATURAL_GUARD_ASSEMBLED',args.stage,args.mode,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset',type=Path,required=True)
    parser.add_argument('--expected-sha',required=True)
    parser.add_argument('--clip',required=True)
    parser.add_argument('--stage',choices=('before','after'),required=True)
    parser.add_argument('--mode',choices=('pose','movie'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--metadata',type=Path)
    parser.add_argument('--size',type=int,default=640)
    parser.add_argument('--samples',type=int,default=2)
    parser.add_argument('--assemble-only',action='store_true')
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    args=parser.parse_args(argv)
    if args.stage=='after' and args.metadata is None:parser.error('After requires explicit --metadata')
    if args.size<128 or args.size%2 or args.samples<1:parser.error('Expected even size>=128 and positive samples')
    if args.stage=='before' and (args.clip!='idle' or args.mode!='pose'):parser.error('Before review is one actual current idle@0 pose only')
    if args.assemble_only:assemble(args)
    else:render(args)


if __name__=='__main__':main()
