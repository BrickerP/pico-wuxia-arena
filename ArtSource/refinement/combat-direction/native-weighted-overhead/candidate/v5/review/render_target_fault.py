"""Two inherited left-elbow/waist diagnostic stills per real veteran target, through the shared Blender lock."""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT.parents[3]
BEFORE = ROOT / 'candidate/v4/veteran_prepared_png.glb'
BEFORE_SHA = 'cead1124ab1c3453f6fae2f98e0be275a39792be3de98e6888edaf83a4aabb86'
SOURCE_SECONDS = 1.1
CAMERA = {'projection': 'perspective', 'eye_height_metres': 1.62,
          'aim_height_metres': .94, 'horizontal_standoff_metres': 1.0,
          'azimuth_degrees': 55., 'vertical_fov_degrees': 52.,
          'aim_gltf': [.14, .94, .16],
          'scope': 'local left-elbow/waist diagnosis; actor-left camera; original materials, actor and grip unchanged'}
CAMERA['location_gltf'] = [CAMERA['aim_gltf'][0] + math.sin(math.radians(55)),
                           1.62, CAMERA['aim_gltf'][2] + math.cos(math.radians(55))]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RENDERER = load('v5_reuse_weighted_renderer', ROOT / 'render_weighted_overhead.py')
BASE, EYE = RENDERER.BASE, RENDERER.EYE


def render(args):
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    if BASE.identity(BEFORE)['sha256'] != BEFORE_SHA:
        raise ValueError('Root-pinned actual veteran before changed')
    if BASE.identity(args.asset)['sha256'] != args.expected_sha:
        raise ValueError('Actual target asset differs from explicit expected SHA')
    if args.stage == 'before' and args.expected_sha != BEFORE_SHA:
        raise ValueError('Before must be the root-pinned real veteran target')
    if args.stage == 'after' and args.expected_sha == BEFORE_SHA:
        raise ValueError('After must be a separately verified veteran v5 target')
    pins = {name: BASE.identity(path) for name, path in (
        ('asset', args.asset), ('actual_veteran_before', BEFORE),
        ('renderer', Path(__file__)), ('reused_renderer', ROOT / 'render_weighted_overhead.py'),
        ('review_geometry', ROOT / 'integration/review_candidate.py'))}
    reviewer = load('v5_actual_target_surface_semantics', ROOT / 'integration/review_candidate.py')
    source = reviewer.library.read_glb(args.asset)
    reference = reviewer.library.read_glb(BEFORE)
    left, right = reviewer.static_signature(*reference), reviewer.static_signature(*source)
    static_checks = {key: left[key] == right[key] for key in left}
    if not all(static_checks.values()):
        raise ValueError('Actual veteran static render semantics changed: ' + str(static_checks))
    studio = load('v5_fault_studio', REPO / 'ArtSource/refinement/grip/render_grip_candidates.py')
    common = load('v5_fault_geometry', REPO / 'ArtSource/refinement/hand-poses/attack-keyposes/render_attack_keyposes.py')
    direct = load('v5_fault_direct', REPO / 'ArtSource/refinement/hand-poses/attack-keyposes/stage8/render_hit_reactions.py')
    scene, camera = studio.setup_scene(args.size, args.samples)
    bpy.ops.import_scene.gltf(filepath=str(args.asset.resolve()))
    imported = list(bpy.context.selected_objects)
    arms = [obj for obj in imported if obj.type == 'ARMATURE']
    if len(arms) != 1:
        raise ValueError('Expected one actual veteran target armature')
    actor = arms[0]
    actor_matrix = [list(row) for row in actor.matrix_world]
    evaluation = direct.select_action(scene, 'attack_overhead', SOURCE_SECONDS)
    camera.data.type, camera.data.sensor_fit = 'PERSP', 'VERTICAL'
    camera.data.angle_y = math.radians(CAMERA['vertical_fov_degrees'])
    camera.location = common.to_blender(CAMERA['location_gltf'])
    aim = Vector(common.to_blender(CAMERA['aim_gltf']))
    camera.rotation_euler = (aim - camera.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    anchors = BASE.bone_points(actor, imported)
    projections = {}
    for name, point in anchors.items():
        p = world_to_camera_view(scene, camera, Vector(common.to_blender(point)))
        projections[name] = {'ndc': list(p), 'in_frame': 0 <= p.x <= 1 and 0 <= p.y <= 1 and p.z > 0}
    for name in ('L_Hand',):
        if not projections[name]['in_frame']:
            raise ValueError('Critical left-hand anchor outside diagnostic camera: ' + name)
    points, mesh_names = EYE.geometry_points(imported)
    record = {'status': 'measured' if args.measure_only else 'rendering', 'target': 'veteran', 'stage': args.stage,
              'clip': 'attack_overhead', 'source_seconds': SOURCE_SECONDS, 'inputs': pins,
              'static_same_veteran_checks': static_checks,
              'camera': {**CAMERA, 'matrix_world_blender': [list(row) for row in camera.matrix_world],
                         'actual_vertical_fov_degrees': math.degrees(camera.data.angle_y), 'optical_axis_pitch_degrees': -math.degrees(math.atan2(.68, 1.0))},
              'actor_world_matrix_blender': actor_matrix,
              'source_evaluation': evaluation, 'anchors_gltf_metres': anchors, 'anchor_projections': projections,
              'actual_geometry_projection': EYE.projection(points, camera, CAMERA['vertical_fov_degrees']),
              'actual_geometry_mesh_names': mesh_names,
              'scope': 'One fixed local diagnostic camera; all actual target geometry, no actor, grip, or time modification; full body, head and blade may lie outside this elbow/waist crop.'}
    args.output.mkdir(parents=True, exist_ok=True)
    stamp = f'{round(SOURCE_SECONDS * 1000):04d}'
    if not args.measure_only:
        image = args.output / f'veteran_{args.stage}_source_{stamp}.png'
        scene.render.filepath = str(image)
        bpy.ops.render.render(write_still=True)
        record['image'] = BASE.identity(image)
        record['status'] = 'complete'
    for pin in pins.values():
        if BASE.identity(pin['path']) != pin:
            raise ValueError('Input changed during diagnostic: ' + pin['path'])
    suffix = 'measure' if args.measure_only else 'manifest'
    RENDERER.save(args.output / f'{args.stage}_{stamp}_{suffix}.json', record)
    print('VETERAN_FAULT_DIAGNOSTIC', args.stage, record['status'], SOURCE_SECONDS, flush=True)


def main():
    global SOURCE_SECONDS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset', type=Path, required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--stage', choices=('before', 'after'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--size', type=int, default=960)
    parser.add_argument('--samples', type=int, default=4)
    parser.add_argument('--measure-only', action='store_true')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    if args.size < 128 or args.size % 2 or args.samples < 1:
        parser.error('Expected even size>=128 and positive samples')
    for SOURCE_SECONDS in (1.1, 22 / 15):
        render(args)


if __name__ == '__main__':
    main()
