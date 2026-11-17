"""One bounded real timber-entry specimen, then full-scene composition/review.

All paths written are private native-entry-finish outputs. Existing scene,
materials, images, anchors, doorway leaves and collision floor are read-only.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import traceback

import bpy
import bmesh
from mathutils import Vector

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ENV = HERE.parent
ROOT = ENV.parents[2]
SOURCE = ENV / 'native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_png.glb'
SOURCE_SHA = 'd935d8185dff6750838bc1d5d98c0b1f07bdce4b0a25249e42957bc501fbe06d'
sys.path.insert(0, str(ENV / 'method-study-2026-11-12'))
import build_window_sample as wood
PARTS = []
DESIGN = []


def p(v):
    return (v[0], -v[2], v[1])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box(name, center, size):
    return wood.cube(name, p(center), (size[0], size[2], size[1]), WOOD)


def cut(obj, name, center, size):
    tool = box(name, center, size)
    wood.boolean(obj, tool, 'DIFFERENCE')
    bpy.data.objects.remove(tool, do_unlink=True)


def finish(obj, grain=(0, 0, 1), radius=.006):
    wood.finish(obj, grain, radius)
    PARTS.append(obj)
    return obj


def mesh(name, vertices, faces):
    data = bpy.data.meshes.new(name + '_Mesh')
    data.from_pydata([p(v) for v in vertices], [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    data.materials.append(WOOD)
    return obj


def post(side):
    x, z = side * 1.4, -5.24
    # Original stone socket remains. Its .242 x .302 opening receives this
    # .230 x .290 foot; front depth grows above the shoe, never into the ground.
    levels = [(.285, .115, .145), (.36, .115, .145), (.52, .115, .172),
              (1.10, .115, .180), (2.38, .115, .175), (2.70, .115, .175),
              (3.30, .115, .170), (4.70, .115, .157), (4.9, .115, .145)]
    shape = [(-1, -.80), (-.80, -1), (.80, -1), (1, -.80),
             (1, .80), (.80, 1), (-.80, 1), (-1, .80)]
    vertices = [(x + a * hx, y, z + b * hz) for y, hx, hz in levels for a, b in shape]
    faces = [tuple(reversed(range(8))), tuple(range((len(levels) - 1) * 8, len(levels) * 8))]
    for j in range(len(levels) - 1):
        for i in range(8):
            k = (i + 1) % 8
            faces.append((j * 8 + i, j * 8 + k, (j + 1) * 8 + k, (j + 1) * 8 + i))
    obj = mesh(f'HeroEntry_Post_{side}', vertices, faces)
    # Genuine through-rail seats, matching the retained facade rail volumes.
    # Shallow front/back shoulders remain; the beam is not merely drawn on top.
    for y, height in [(2.85, .17), (3.15, .17), (4.80, .17)]:
        cut(obj, 'RailMortise', (x, y, -5.23), (.27, height + .001, .251))
    cut(obj, 'CorbelTenonSocket', (x, 2.69, -5.125), (.112, .196, .222))
    # Bounded real edge losses; no painted highlight or additional texture.
    for y, dz, depth in [(.77, .176, .005), (1.42, .174, .004)]:
        cut(obj, 'ShallowWear', (x + side * .106, y, z + dz), (.018, .035, depth * 2))
    finish(obj, radius=.004)
    DESIGN.append({'part': obj.name, 'center_xz': [x, z], 'foot_m': [.23, .29],
                   'height_m': 4.615, 'max_depth_m': .36, 'width_m': .23,
                   'rail_seats': [2.85, 3.15, 4.8], 'corbel_mortise': True,
                   'grain_stage': [0, 1, 0], 'edge_radius_m': .004})


def corbel(side):
    x = side * 1.4
    # Closed 190 mm thick carved ox-leg support; curved underside is a real
    # sequence of profiled faces. Back tenon seats into the post mortise.
    profile = [(-5.067, 2.80), (-5.067, 2.98), (-4.715, 2.98),
               (-4.715, 2.905), (-4.745, 2.858), (-4.79, 2.825),
               (-4.85, 2.795), (-4.90, 2.752), (-4.943, 2.695),
               (-4.98, 2.62), (-5.015, 2.56), (-5.052, 2.536),
               (-5.067, 2.548)]
    vertices = [(xx, y, z) for xx in [x - .095, x + .095] for z, y in profile]
    n = len(profile)
    faces = [tuple(reversed(range(n))), tuple(range(n, n * 2))]
    faces += [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
    body = mesh(f'HeroEntry_OxLeg_{side}', vertices, faces)
    # Carved side recess stops inside the body rather than making a flat decal.
    for sign in [-1, 1]:
        cut(body, 'SideCarvedRecess', (x + sign * .095, 2.845, -4.89), (.015, .065, .135))
    finish(body, (0, -1, 0), .005)
    tenon = box(f'HeroEntry_HiddenShoulderedTenon_{side}', (x, 2.69, -5.125), (.110, .194, .220))
    finish(tenon, (0, -1, 0), .001)
    # Bearing directly meets the retained porch beam bottom at Y=3.02.
    saddle = box(f'HeroEntry_BearingSaddle_{side}', (x, 3.0, -4.86), (.29, .04, .38))
    finish(saddle, (1, 0, 0), .004)
    # Locking key and driven peg have visible endgrain from the existing atlas.
    key = box(f'HeroEntry_WedgeKey_{side}', (x, 2.75, -5.005), (.15, .034, .055))
    finish(key, (1, 0, 0), .002)
    DESIGN.append({'part': body.name, 'profile_stage_zy': profile, 'thickness_m': .19,
                   'real_side_recess_depth_m': .0075, 'bearing_top_y_m': 3.02,
                   'tenon_m': [.110, .194, .220], 'socket_clearance_m': .001,
                   'grain_stage': [0, 0, 1], 'edge_radius_m': .005})


def main():
    global WOOD
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError('Frozen d935 scene changed')
    HERE.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    WOOD = bpy.data.materials['Method | CC0 directional wood .8m']
    wood.WOOD = WOOD
    wood.END = bpy.data.materials['Method | original endgrain .25m']
    wood.PARTS = []
    wood.AFTER = []
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for side in [-1, 1]:
        post(side)
        corbel(side)
    bpy.context.view_layer.update()
    topology = {}
    for obj in PARTS:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        before_vertices = len(bm.verts)
        # Boolean/bevel junctions may contain sub-micron edges that collapse at
        # glTF float32 precision. Clean only these new authored pieces, then
        # triangulate before computing/exporting their normal-map frame.
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-6)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        topology[obj.name] = {'non_manifold_edges': sum(not e.is_manifold for e in bm.edges),
                              'volume_m3': bm.calc_volume(signed=True),
                              'cleaned_vertices': before_vertices - len(bm.verts),
                              'float_safety_merge_m': 1e-5,
                              'min_triangle_twice_area_m2': min(face.calc_area() * 2 for face in bm.faces)}
        bm.to_mesh(obj.data)
        bm.free()
    if any(v['non_manifold_edges'] or v['volume_m3'] <= 0 for v in topology.values()):
        raise ValueError('Non-solid generated timber part: ' + str(topology))
    (HERE / 'construction.json').write_text(json.dumps({'parts': DESIGN, 'topology': topology,
        'materials': ['Method | CC0 directional wood .8m', 'Method | original endgrain .25m'],
        'textures_added': 0, 'coordinate_stage_to_blender': 'X,-Z,Y'}, indent=2) + '\n')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in PARTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'NativeEntryFinish_SolidTimber'
    bpy.ops.export_scene.gltf(filepath=str(HERE / 'entry_module.glb'), export_format='GLB',
                             use_selection=True, export_apply=True, export_yup=True,
                             export_cameras=False, export_lights=False, export_tangents=False)
    # Only this composition helper runs outside Blender; it never invokes another
    # Blender or touches public paths. The shared lock remains with this process.
    subprocess.run(['/usr/bin/python3', str(HERE / 'compose_entry.py')], cwd=ROOT, check=True)
    spec = importlib.util.spec_from_file_location('entry_private_review', HERE / 'render_entry.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(phases=('after',) if '--after-only' in sys.argv else ('before', 'after'))


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        sys.exit(1)
