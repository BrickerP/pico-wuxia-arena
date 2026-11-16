"""Review actual pending three-target outputs; no approval or formal writes.
Run only via hand-poses/run_blender.py -b --factory-startup --threads 2 --python this_file.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
import traceback
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
OUT = None
CANDIDATE = None
FORMAL = REPO / 'ArtSource/tripo-warrior/library'
EXPECTED_BINDING = None
TIMES = [0., .2, .68, 5/6, .9, .9667, 1., 31/30, 1.15, 1.27, 1.34, 1.4, 1.42, 1.5, 1.55, 1.75]
TARGETS = ('base', 'indigo', 'veteran')
CLIP = 'attack_overhead'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


sys.path.insert(0, str(REPO / 'ArtSource/tripo-warrior'))
import prepare_character_library as library
import attack_profiles as profiles
import numpy as np
from mathutils.bvhtree import BVHTree
EYE = load('target_eye_renderer', REPO / 'ArtSource/refinement/hand-poses/fine-overhead/render_eye_height.py')
UTILITY = load('target_surface_utility', REPO / 'ArtSource/refinement/hand-poses/fine-overhead/verify_fine_overhead.py')
DIRECT = load('target_direct_action', REPO / 'ArtSource/refinement/hand-poses/attack-keyposes/stage8/render_hit_reactions.py')
COMMON = load('target_render_geometry', REPO / 'ArtSource/refinement/hand-poses/attack-keyposes/render_attack_keyposes.py')
STUDIO = load('target_studio', REPO / 'ArtSource/refinement/grip/render_grip_candidates.py')
CAMERA = REPO / 'ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v7/camera_set.json'


def view_bytes(doc, binary, index):
    view = doc['bufferViews'][index]
    start = view.get('byteOffset', 0)
    return binary[start:start + view['byteLength']]


def accessor_signature(doc, binary, index):
    accessor = dict(doc['accessors'][index])
    accessor.pop('bufferView', None)
    accessor.pop('byteOffset', None)
    accessor['payload_sha256'] = hashlib.sha256(UTILITY.accessor(doc, binary, index).tobytes(order='C')).hexdigest()
    return accessor


def static_signature(doc, binary):
    meshes = copy.deepcopy(doc['meshes'])
    for mesh in meshes:
        for primitive in mesh['primitives']:
            primitive['attributes'] = {key: accessor_signature(doc, binary, index) for key, index in primitive['attributes'].items()}
            if 'indices' in primitive:
                primitive['indices'] = accessor_signature(doc, binary, primitive['indices'])
            if primitive.get('targets'):
                primitive['targets'] = [{key: accessor_signature(doc, binary, index) for key, index in row.items()} for row in primitive['targets']]
    skins = copy.deepcopy(doc['skins'])
    for skin in skins:
        skin['inverseBindMatrices'] = accessor_signature(doc, binary, skin['inverseBindMatrices'])
    images = [{**{k: v for k, v in image.items() if k != 'bufferView'},
               'payload_sha256': hashlib.sha256(view_bytes(doc, binary, image['bufferView'])).hexdigest()} for image in doc['images']]
    return dict(nodes=doc['nodes'], scenes=doc['scenes'], meshes=meshes, skins=skins,
                materials=doc['materials'], textures=doc['textures'], samplers=doc.get('samplers', []), images=images)


def png_encoding_proof(png, encoded):
    # Same exact non-image preservation contract as compress_pbr.verify_preserved;
    # no Pillow dependency and no image transcoding in this read-only review.
    a, ab = png
    b, bb = encoded
    def semantics(doc, compressed):
        doc = copy.deepcopy(doc)
        doc['buffers'][0].pop('byteLength', None)
        for view in doc['bufferViews']:
            view.pop('byteOffset', None)
        for image in doc['images']:
            doc['bufferViews'][image['bufferView']].pop('byteLength', None)
            image.pop('mimeType', None)
        if compressed:
            for texture in doc['textures']:
                require('source' not in texture and set(texture.get('extensions', {})) == {'KHR_texture_basisu'}, 'invalid encoded texture route')
                texture['source'] = texture.pop('extensions')['KHR_texture_basisu']['source']
            for field in ('extensionsRequired', 'extensionsUsed'):
                require(doc.pop(field) == ['KHR_texture_basisu'], 'unexpected encoded extension')
        return doc
    require(semantics(a, False) == semantics(b, True), 'prepared PNG/encoded non-image semantics drift')
    images = {image['bufferView'] for image in a['images']}
    checked = 0
    for index in range(len(a['bufferViews'])):
        if index not in images:
            require(view_bytes(a, ab, index) == view_bytes(b, bb, index), 'prepared PNG/encoded non-image payload drift: ' + str(index))
            checked += 1
    return {'non_image_json_semantics_identical': True, 'non_image_bufferViews_byte_identical': checked,
            'scope': 'PNG versus KTX image payloads intentionally differ; PNG payload unchanged versus same-target old PNG is checked separately'}


def clip(doc, binary, name):
    animation = next(row for row in doc['animations'] if row['name'] == name)
    tracks, times = library.decode_animation({**doc, 'animations': [animation]}, binary)
    return animation, tracks, times


def compare_assets(target, request):
    files = {row['file']: row for row in request['outputs']}
    report = {'target': target, 'variants': {}, 'clips': {}}
    loaded = {}
    for suffix in ('_body.glb', '_prepared_png.glb', '.glb'):
        name = target + suffix
        candidate, old = CANDIDATE / name, FORMAL / name
        require(sha(candidate) == files[name]['sha256'], 'request output SHA drift: ' + name)
        new_doc, new_bin = library.read_glb(candidate)
        old_doc, old_bin = library.read_glb(old)
        new_static, old_static = static_signature(new_doc, new_bin), static_signature(old_doc, old_bin)
        checks = {key: new_static[key] == old_static[key] for key in new_static}
        require(all(checks.values()), 'static mesh/skin/rest/material/image drift: ' + name + ' ' + str(checks))
        new_clips = {row['name']: library.animation_signature(new_doc, new_bin, row) for row in new_doc['animations']}
        old_clips = {row['name']: library.animation_signature(old_doc, old_bin, row) for row in old_doc['animations']}
        require(len(new_clips) == len(old_clips) == 10 and new_clips.keys() == old_clips.keys(), 'ten clips changed')
        changed = [name for name in new_clips if new_clips[name] != old_clips[name]]
        require(changed == [CLIP], 'non-overhead clip changed: ' + str(changed))
        _, tracks, keys = clip(new_doc, new_bin, CLIP)
        require(len(tracks) == 234 and len(keys) == 211 and keys[0] == 0 and keys[-1] == 1.75, 'OH234tracks/211keys grid changed')
        require(all(row[0] == keys and row[2] == 'LINEAR' for row in tracks.values()), 'OH per-track grid/interpolation differs')
        report['variants'][name] = {'candidate_sha256': sha(candidate), 'old_sha256': sha(old), 'static_checks': checks,
                                   'changed_clips': changed, 'track_count': len(tracks), 'key_count': len(keys)}
        loaded[suffix] = (new_doc, new_bin)
        report['clips'][name] = {'candidate': new_clips, 'old': old_clips}
    report['prepared_png_encoded'] = png_encoding_proof(loaded['_prepared_png.glb'], loaded['.glb'])
    profile_path = CANDIDATE / (target + '_attack_profiles.json')
    require(sha(profile_path) == request['attack_profiles_sha256'], 'profile request SHA drift')
    profile = json.loads(profile_path.read_text())
    attack = profile['attacks']['OVERHEAD']
    require(profile['model_sha256'] == files[target + '.glb']['sha256'], 'profile/model SHA drift')
    require(attack['source_phase_seconds'] == [0, .65, 5/6, 31/30, 1.75], 'OH stage source mapping drift')
    require(attack['runtime_phase_nanos'] == [650000000, 183333333, 200000000, 716666667], 'OH runtime phase drift')
    require(len(attack['samples']) == 211 and attack['contact_source_seconds'] == 1., 'OH profile sampling drift')
    require(attack['animation_semantics_sha256'] == report['clips'][target + '.glb']['candidate'][CLIP], 'profile clip signature drift')
    report['overhead_phase_contract'] = {key: attack[key] for key in ('source_phase_seconds', 'runtime_phase_nanos', 'contact_source_seconds', 'source_range_seconds')}
    return report, loaded['_prepared_png.glb'], profile


class ActualTargetSurface:
    def __init__(self, asset, body_primitives, clip_name):
        self.doc, binary = asset
        _, self.tracks, _ = clip(self.doc, binary, clip_name)
        self.parents, self.order = library.node_order(self.doc)
        self.steel = UTILITY.surface(self.doc, binary)
        self.joints = self.doc['skins'][0]['joints']
        self.bind = UTILITY.accessor(self.doc, binary, self.doc['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        mesh = self.doc['meshes'][next(node['mesh'] for node in self.doc['nodes'] if 'mesh' in node)]
        points, palettes, weights, faces, face_materials, pools = [], [], [], [], [], {}
        offset = 0
        for primitive_index in body_primitives:
            primitive = mesh['primitives'][primitive_index]
            attributes = primitive['attributes']
            key = tuple(attributes[name] for name in ('POSITION', 'JOINTS_0', 'WEIGHTS_0'))
            if key not in pools:
                p = UTILITY.accessor(self.doc, binary, attributes['POSITION']).astype(float)
                pools[key] = offset
                points.append(p)
                palettes.append(UTILITY.accessor(self.doc, binary, attributes['JOINTS_0']).astype(int))
                weights.append(UTILITY.accessor(self.doc, binary, attributes['WEIGHTS_0']).astype(float))
                offset += len(p)
            f = UTILITY.accessor(self.doc, binary, primitive['indices']).reshape(-1, 3).astype(int) + pools[key]
            faces.append(f)
            face_materials.extend([self.doc['materials'][primitive['material']].get('name', '')] * len(f))
        self.position = np.column_stack((np.concatenate(points), np.ones(offset)))
        self.palette, self.weights, self.faces = np.concatenate(palettes), np.concatenate(weights), np.concatenate(faces)
        self.weights /= self.weights.sum(axis=1)[:, None]
        self.materials = np.array(face_materials)
        joint_names = [self.doc['nodes'][index]['name'] for index in self.joints]
        self.dominant = np.array([joint_names[int(i)] for i in self.palette[np.arange(offset), np.argmax(self.weights, axis=1)]])
        groups = {'head': {'Head', 'L_Eye', 'R_Eye', 'FacialBone'}, 'chest': {'Waist', 'Spine01', 'Spine02'}}
        for side in ('R_', 'L_'):
            groups[side + 'forearm'] = {side + name for name in ('Forearm', 'ForearmTwist01', 'ForearmTwist02', 'ElbowShareBone')}
            groups[side + 'hand'] = {name for name in joint_names if name == side + 'Hand' or name.startswith(tuple(side + finger for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')))}
        self.regions = {}
        for name, joints in groups.items():
            subset = self.faces[np.isin(self.dominant, list(joints))[self.faces].all(axis=1)]
            indices, remap = np.unique(subset, return_inverse=True)
            require(len(subset) > 0, 'empty target anatomical region: ' + name)
            self.regions[name] = indices, remap.reshape(-1, 3)

    def evaluate(self, seconds):
        world = profiles.pose_world(self.doc, self.tracks, seconds, self.parents, self.order)
        transforms = np.array([list(world[index]) for index in self.joints]) @ self.bind
        blend = np.sum(transforms[self.palette] * self.weights[:, :, None, None], axis=1)
        body = np.einsum('vij,vj->vi', blend, self.position)[:, :3]
        parts = UTILITY.steel_points(self.steel, world)
        steel = np.concatenate([part[2] for part in parts])
        triangles = body[self.faces]
        low, high = steel.min(axis=0) - .00001, steel.max(axis=0) + .00001
        selected_indices = np.flatnonzero(((triangles.min(axis=1) <= high) & (triangles.max(axis=1) >= low)).all(axis=1))
        selected = self.faces[selected_indices]
        collisions = []
        if len(selected):
            tree = BVHTree.FromPolygons(body.tolist(), selected.tolist(), all_triangles=True, epsilon=0.)
            for primitive, material, points, faces in parts:
                hits = BVHTree.FromPolygons(points.tolist(), faces.tolist(), all_triangles=True, epsilon=0.).overlap(tree)
                if hits:
                    actual_body_faces = selected_indices[[pair[1] for pair in hits]]
                    vertices = self.faces[actual_body_faces].ravel()
                    collisions.append({'steel_primitive': primitive, 'steel_material': material, 'triangle_pair_count': len(hits),
                                       'body_materials': dict(Counter(self.materials[actual_body_faces])),
                                       'dominant_body_joint_vertices': dict(Counter(self.dominant[vertices])),
                                       'body_intersected_triangle_bounds_metres': {'min': body[vertices].min(axis=0).tolist(), 'max': body[vertices].max(axis=0).tolist()}})
        trees = {name: BVHTree.FromPolygons(body[indices].tolist(), faces.tolist(), all_triangles=True, epsilon=0.)
                 for name, (indices, faces) in self.regions.items()}
        region_hits, examples = {}, []
        for limb in ('R_forearm', 'R_hand', 'L_forearm', 'L_hand'):
            for core in ('head', 'chest'):
                hits = trees[limb].overlap(trees[core])
                region_hits[limb + '__' + core] = len(hits)
                if hits:
                    limb_indices, limb_faces = self.regions[limb]
                    core_indices, core_faces = self.regions[core]
                    examples.append({'first_region': limb, 'second_region': core, 'triangle_pair_count': len(hits),
                        'actual_intersecting_triangles': [
                            {'first_region_triangle': int(a), 'second_region_triangle': int(b),
                             'first_triangle_metres': body[limb_indices[limb_faces[a]]].tolist(),
                             'second_triangle_metres': body[core_indices[core_faces[b]]].tolist()}
                            for a, b in hits[:8]], 'example_limit': 8})
        return {'source_seconds': seconds, 'steel_fullbody_intersections': collisions,
                'nonadjacent_region_triangle_pairs': region_hits, 'nonadjacent_intersection_details': examples}


def render_target(target, prepared, report, frames):
    import bpy
    from mathutils import Vector
    scene, camera = STUDIO.setup_scene(480, 2)
    scene.render.threads_mode, scene.render.threads = 'FIXED', 2
    require('--threads' in sys.argv and sys.argv[sys.argv.index('--threads') + 1] == '2', 'host two-thread argument required')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(prepared.resolve()), disable_bone_shape=True)
    imported = list(set(bpy.data.objects) - before)
    require(len([obj for obj in imported if obj.type == 'ARMATURE']) == 1, 'actual target armature count')
    camera_contract = EYE.camera_set(CAMERA)
    view = camera_contract['views']['three_quarter']
    camera.data.type, camera.data.sensor_fit = 'PERSP', 'VERTICAL'
    camera.data.angle_y = math.radians(camera_contract['vertical_fov_degrees'])
    camera.location = COMMON.to_blender(view['location_gltf'])
    camera.rotation_euler = (Vector(COMMON.to_blender(view['aim_gltf'])) - camera.location).to_track_quat('-Z', 'Y').to_euler()
    floor = COMMON.material('Target review floor', (.075, .09, .11))
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, camera_contract['floor_blender_z'] - .006))
    bpy.context.object.data.materials.append(floor)
    rows = []
    for clip_name, seconds, label in frames:
        evaluation = DIRECT.select_action(scene, clip_name, seconds)
        points, meshes = EYE.geometry_points(imported)
        framing = EYE.projection(points, camera, camera_contract['vertical_fov_degrees'])
        require(framing['outside_vertex_count'] == 0, 'actual target outside unchanged fixed camera: ' + target + ' ' + str(framing))
        name = target + '_' + label + '.png'
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
        rows.append({'path': str((OUT / name).relative_to(REPO)), 'sha256': sha(OUT / name), 'clip': clip_name, 'source_seconds': seconds,
                     'actual_import_action': evaluation, 'actual_geometry_bounds_blender': {'min': points.min(axis=0).tolist(), 'max': points.max(axis=0).tolist(), 'mesh_names': meshes},
                     'projection': framing})
        print('TARGET_RENDER', target, seconds, flush=True)
    report['renders'] = {'prepared_png_path': str(prepared.relative_to(REPO)), 'prepared_png_sha256': sha(prepared),
                         'size': 480, 'samples': 2, 'render_threads': scene.render.threads, 'threads_mode': scene.render.threads_mode, 'camera_contract': camera_contract,
                         'actual_camera_matrix_blender': [list(row) for row in camera.matrix_world], 'frames': rows,
                         'scope': 'actual target prepared PNG import and original pixels; offline Blender, not PICO; no actor recenter/scale/pose correction'}


def main():
    global OUT, CANDIDATE, EXPECTED_BINDING
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--binding', required=True)
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    args = parser.parse_args(argv)
    CANDIDATE, OUT, EXPECTED_BINDING = args.bank.resolve(), args.output.resolve(), args.binding
    if len(EXPECTED_BINDING) != 64 or any(ch not in '0123456789abcdef' for ch in EXPECTED_BINDING):
        parser.error('binding must be a SHA256')
    OUT.mkdir(parents=True, exist_ok=True)
    request_path = CANDIDATE / 'production_review_request.json'
    request = json.loads(request_path.read_text())
    require(request['binding_sha256'] == EXPECTED_BINDING, 'unexpected pending request binding')
    require(library.canonical_hash(request['binding']) == EXPECTED_BINDING, 'request canonical binding drift')
    require(request['status'] == 'pending_root_review', 'request approval status changed')
    pins = {str(path.relative_to(REPO)): sha(path) for path in [request_path, Path(__file__), CAMERA, Path(library.__file__), Path(profiles.__file__), Path(UTILITY.__file__), Path(EYE.__file__), Path(STUDIO.__file__), Path(DIRECT.__file__), Path(COMMON.__file__)]}
    for target in TARGETS:
        for directory in (CANDIDATE, FORMAL):
            for suffix in ('_body.glb', '_prepared_png.glb', '.glb', '_attack_profiles.json'):
                path = directory / (target + suffix)
                pins[str(path.relative_to(REPO))] = sha(path)
    result = {'status': 'review_in_progress_not_approval', 'binding_sha256': EXPECTED_BINDING,
              'discrete_times_seconds': TIMES, 'source_pins': pins, 'targets': [],
              'limits': ['Only 16 named discrete poses per target; no continuous-time guarantee.',
                         'LBS evaluated from actual assembled target GLB; no runtime/skinned PICO readback.',
                         'Nonadjacent regions require all triangle vertices to have dominant joint within region; skin blend seams, adjacent upperarm/chest and cloth-layer self intersections are excluded.',
                         'Triangle intersections are geometric evidence, not a claim of perceptual visibility or release approval.']}
    save(OUT / 'review_report.json', result)
    for target in TARGETS:
        row = next(item for item in request['characters'] if item['id'] == target)
        report, candidate, profile = compare_assets(target, row)
        result['targets'].append(report)
        save(OUT / 'review_report.json', result)
        body_primitives = profile['proxy_calibration']['measurement']['body_primitive_indices']
        new = ActualTargetSurface(candidate, body_primitives, CLIP)
        old = ActualTargetSurface(library.read_glb(FORMAL / (target + '_prepared_png.glb')), body_primitives, CLIP)
        frames = []
        for seconds in TIMES:
            frame = new.evaluate(seconds)
            if frame['steel_fullbody_intersections'] or any(frame['nonadjacent_region_triangle_pairs'].values()):
                frame['same_target_old_v9_same_time'] = old.evaluate(seconds)
            frames.append(frame)
            print('TARGET_CHECK', target, seconds, 'steel', sum(item['triangle_pair_count'] for item in frame['steel_fullbody_intersections']), 'regions', frame['nonadjacent_region_triangle_pairs'], flush=True)
        report['actual_assembled_target_checks'] = {'frames': frames,
            'body_primitive_indices': body_primitives, 'body_triangle_count': len(new.faces),
            'region_triangle_counts': {name: len(value[1]) for name, value in new.regions.items()}}
        save(OUT / 'review_report.json', result)
        render_target(target, CANDIDATE / (target + '_prepared_png.glb'), report,
                      ((CLIP, .68, 'load_0p68'), (CLIP, 1.15, 'unload_1p15')))
        save(OUT / 'review_report.json', result)
    for path, digest in pins.items():
        require(sha(REPO / path) == digest, 'input/source hash drift during review: ' + path)
    result['status'] = 'bounded_target_review_complete_pending_Root_visual_review'
    result['intersection_pose_counts'] = {row['target']: sum(bool(frame['steel_fullbody_intersections']) or any(frame['nonadjacent_region_triangle_pairs'].values()) for frame in row['actual_assembled_target_checks']['frames']) for row in result['targets']}
    save(OUT / 'review_report.json', result)
    print('REVIEW_COMPLETE', result['intersection_pose_counts'], flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save(OUT / 'execution_failure.json', {'status': 'review_failed_not_approval', 'error': str(error), 'traceback': traceback.format_exc()})
        raise
