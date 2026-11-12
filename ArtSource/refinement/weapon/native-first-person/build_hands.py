"""Extract pinned native first-person hand geometry and author real grip clips.

Run with Blender Python. No public asset, publisher or application is written.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FORMAL = REPO / 'ArtSource/tripo-warrior/library/base.glb'
PNG = FORMAL.with_name('base_prepared_png.glb')
FORMAL_SHA = 'ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20'
PNG_SHA = 'b3fbfe66727d0dd90bd741420937a6c57dbb9e083d76ecd983cd9383ab5bbf96'
sys.path.insert(0, str(HERE.parent))
from build_weapon import read_glb, encode_glb
import numpy as np


def sha(data):
    return hashlib.sha256(data).hexdigest()


def view_bytes(document, binary, index):
    view = document['bufferViews'][index]
    offset = view.get('byteOffset', 0)
    if view['buffer'] != 0 or offset + view['byteLength'] > len(binary):
        raise ValueError('invalid embedded buffer view')
    return binary[offset:offset + view['byteLength']]


def attribute(document, binary, index, normalized=False):
    descriptor = document['accessors'][index]
    if 'sparse' in descriptor:
        raise ValueError('sparse source attribute requires explicit support')
    view = document['bufferViews'][descriptor['bufferView']]
    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
    types = {5120: '<i1', 5121: '<u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
    dtype = np.dtype(types[descriptor['componentType']])
    width = widths[descriptor['type']]
    stride = view.get('byteStride', width * dtype.itemsize)
    offset = view.get('byteOffset', 0) + descriptor.get('byteOffset', 0)
    rows = np.ndarray((descriptor['count'], width), dtype=dtype, buffer=binary,
                      offset=offset, strides=(stride, dtype.itemsize)).copy()
    if normalized and descriptor.get('normalized'):
        rows = rows.astype(float) / np.iinfo(dtype).max
    return rows


def verify_inputs():
    if sha(FORMAL.read_bytes()) != FORMAL_SHA or sha(PNG.read_bytes()) != PNG_SHA:
        raise ValueError('Root-approved formal/PNG identity changed')
    formal, formal_binary = read_glb(FORMAL)
    png, png_binary = read_glb(PNG)
    image_views = {image['bufferView'] for image in formal['images']}
    if image_views != {image['bufferView'] for image in png['images']}:
        raise ValueError('formal and PNG image-view identities differ')
    ignored = {'buffers', 'bufferViews', 'images', 'textures', 'extensionsUsed', 'extensionsRequired'}
    if {k: v for k, v in formal.items() if k not in ignored} != {k: v for k, v in png.items() if k not in ignored}:
        raise ValueError('formal/PNG non-image JSON differs')
    for field in ('extensionsUsed', 'extensionsRequired'):
        if [v for v in formal.get(field, []) if v != 'KHR_texture_basisu'] != png.get(field, []):
            raise ValueError('unexpected non-image extension difference')
    textures = copy.deepcopy(formal['textures'])
    for texture in textures:
        basis = texture.get('extensions', {}).pop('KHR_texture_basisu', None)
        if basis:
            texture['source'] = basis['source']
        if not texture.get('extensions'):
            texture.pop('extensions', None)
    if textures != png['textures']:
        raise ValueError('formal/PNG texture semantics differ')
    if len(formal['bufferViews']) != len(png['bufferViews']):
        raise ValueError('formal/PNG buffer-view count differs')
    compared = 0
    for i, (first, second) in enumerate(zip(formal['bufferViews'], png['bufferViews'])):
        if i in image_views:
            continue
        if {k: v for k, v in first.items() if k != 'byteOffset'} != {k: v for k, v in second.items() if k != 'byteOffset'}:
            raise ValueError('non-image buffer-view descriptor changed')
        if view_bytes(formal, formal_binary, i) != view_bytes(png, png_binary, i):
            raise ValueError('non-image buffer-view bytes changed')
        compared += 1
    return png, png_binary, {'passed': True, 'non_image_json_exact': True,
                             'non_image_buffer_views_exact': compared,
                             'normalized_texture_semantics_exact': True}


def select_hands(document, binary, equivalence):
    names = [document['nodes'][i]['name'] for i in document['skins'][0]['joints']]
    mesh_index = next(node['mesh'] for node in document['nodes'] if node.get('name') == 'TripoBody_Mesh')
    mesh = document['meshes'][mesh_index]
    arrays = {}
    manifest = {
        'formal_source': str(FORMAL.relative_to(REPO)), 'formal_sha256': FORMAL_SHA,
        'png_source': str(PNG.relative_to(REPO)), 'png_sha256': PNG_SHA,
        'equivalence': equivalence,
        'selection_rule': 'visible body primitives; all three vertices have a dominant bone of the selected Forearm/ForearmTwist/Hand/15-finger side',
        'id_space': 'source mesh/primitive-local vertex ID and source primitive triangle ID; compact indices map through source_vertex_ids',
        'npz': str((HERE / 'selection.npz').relative_to(REPO)), 'sides': {},
    }
    for side in ('R', 'L'):
        region = re.compile(r'^' + side + r'_(Forearm(?:Twist\d+)?|Hand|(?:Thumb|Index|Mid|Ring|Pinky)[123])$')
        records = []
        for primitive_id in mesh['extras']['body_primitive_indices']:
            primitive = mesh['primitives'][primitive_id]
            if primitive.get('mode', 4) != 4:
                raise ValueError('source body must contain triangle primitives')
            attrs = primitive['attributes']
            joints = attribute(document, binary, attrs['JOINTS_0']).astype(int)
            weights = attribute(document, binary, attrs['WEIGHTS_0'], True)
            dominant = joints[np.arange(len(joints)), weights.argmax(axis=1)]
            selected = np.array([bool(region.fullmatch(names[i])) for i in dominant]) & (weights.max(axis=1) > 0)
            faces = attribute(document, binary, primitive['indices']).reshape(-1, 3).astype(int)
            face_ids = np.flatnonzero(selected[faces].all(axis=1))
            if not len(face_ids):
                continue
            chosen = faces[face_ids]
            vertices = np.unique(chosen)
            compact = np.full(len(selected), -1, dtype=np.int32)
            compact[vertices] = np.arange(len(vertices), dtype=np.int32)
            prefix = side + '_p' + str(primitive_id)
            arrays[prefix + '_source_vertex_ids'] = vertices.astype(np.int32)
            arrays[prefix + '_source_face_ids'] = face_ids.astype(np.int32)
            arrays[prefix + '_source_triangles'] = chosen.astype(np.int32)
            arrays[prefix + '_indices'] = compact[chosen].astype(np.uint32)
            descriptors = {}
            for semantic, accessor_id in attrs.items():
                key = prefix + '_' + semantic
                arrays[key] = attribute(document, binary, accessor_id)[vertices]
                descriptors[semantic] = {'npz_key': key, 'source_accessor': accessor_id,
                                         'componentType': document['accessors'][accessor_id]['componentType'],
                                         'normalized': document['accessors'][accessor_id].get('normalized', False),
                                         'type': document['accessors'][accessor_id]['type']}
            records.append({'source_mesh': mesh_index, 'source_primitive': primitive_id,
                            'source_material': primitive['material'],
                            'material_name': document['materials'][primitive['material']].get('name'),
                            'triangles': len(face_ids), 'vertices': len(vertices),
                            'npz_prefix': prefix, 'attributes': descriptors})
        if not records:
            raise ValueError('no actual source geometry selected for ' + side)
        manifest['sides'][side] = {'triangles': sum(p['triangles'] for p in records),
                                   'vertices': sum(p['vertices'] for p in records), 'primitives': records}
    total = sum(side['triangles'] for side in manifest['sides'].values())
    if total > 20_000:
        raise ValueError('selected two-hand geometry exceeds Root 20k triangle budget')
    manifest['total_triangles'] = total
    manifest['decimation_applied'] = False
    HERE.mkdir(parents=True, exist_ok=True)
    if (HERE / 'selection.json').exists() and (HERE / 'selection.npz').exists():
        previous = json.loads((HERE / 'selection.json').read_text())
        if {**manifest, 'npz_sha256': previous['npz_sha256']} != previous:
            raise ValueError('existing frozen selection metadata differs')
        with np.load(HERE / 'selection.npz', allow_pickle=False) as existing:
            if set(existing.files) != set(arrays) or any(not np.array_equal(existing[key], value) for key, value in arrays.items()):
                raise ValueError('existing frozen selection arrays differ')
        print('HAND_SELECTION_REUSED_EXACT', flush=True)
        return previous, arrays
    np.savez_compressed(HERE / 'selection.npz', **arrays)
    manifest['npz_sha256'] = sha((HERE / 'selection.npz').read_bytes())
    (HERE / 'selection.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('HAND_SELECTION_READY ' + json.dumps({side: value['triangles'] for side, value in manifest['sides'].items()}), flush=True)
    return manifest, arrays


def add_sleeve_closure(document, packed, side, selection_record, append_accessor, atlas_side):
    """Add a generated cloth transition, rolled edge and cap; never edit source streams."""
    from mathutils import Vector
    from prepare_rigged_warrior import world_matrix
    sys.path.insert(0, str(HERE.parent.parent / 'grip'))
    from measure_weapon_surface import _tree, _triangles_cross

    source_primitive = document['meshes'][0]['primitives'][0]
    attrs = source_primitive['attributes']
    positions = attribute(document, packed, attrs['POSITION'])
    normals = attribute(document, packed, attrs['NORMAL'])
    uv = attribute(document, packed, attrs['TEXCOORD_0'])
    joints = attribute(document, packed, attrs['JOINTS_0']).astype(int)
    weights = attribute(document, packed, attrs['WEIGHTS_0'], True)
    faces = attribute(document, packed, source_primitive['indices']).reshape(-1, 3).astype(int)
    _, welded = np.unique(np.round(positions, 7), axis=0, return_inverse=True)
    welded_faces = welded[faces]
    directed = np.concatenate((welded_faces[:, [0, 1]], welded_faces[:, [1, 2]], welded_faces[:, [2, 0]]))
    _, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    if np.any(counts > 2):
        raise ValueError('source closure boundary is nonmanifold')
    boundary = directed[counts[inverse] == 1]
    outgoing = {}
    incoming = {}
    for a, b in boundary:
        if int(a) in outgoing or int(b) in incoming:
            raise ValueError('source boundary is not a simple consistently oriented loop')
        outgoing[int(a)] = int(b)
        incoming[int(b)] = int(a)
    start = min(outgoing)
    loop = [start]
    while outgoing[loop[-1]] != start:
        loop.append(outgoing[loop[-1]])
        if len(loop) > len(boundary):
            raise ValueError('source boundary did not close')
    if len(loop) != len(boundary):
        raise ValueError('multiple source openings require a separate closure design')
    representatives = {int(w): i for i, w in enumerate(welded)}
    boundary_ids = np.array([representatives[i] for i in loop], dtype=int)
    n = len(boundary_ids)
    nodes = {node.get('name'): i for i, node in enumerate(document['nodes'])}
    skin = document['skins'][0]
    bind = attribute(document, packed, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    transforms = np.array([list(world_matrix(document['nodes'], i)) for i in skin['joints']]) @ bind
    blended = np.sum(transforms[joints] * weights[:, :, None, None], axis=1)
    homogeneous = np.column_stack((positions, np.ones(len(positions))))
    world_positions = np.einsum('vij,vj->vi', blended, homogeneous)[:, :3]
    wrist = np.array(list(world_matrix(document['nodes'], nodes[side + '_Hand']).translation))
    elbow = np.array(list(world_matrix(document['nodes'], nodes[side + '_Forearm']).translation))
    axis = elbow - wrist
    axis /= np.linalg.norm(axis)
    seed = np.array([float(i == int(np.argmin(abs(axis)))) for i in range(3)])
    u = np.cross(axis, seed)
    u /= np.linalg.norm(u)
    v = np.cross(axis, u)
    source_world = world_positions[boundary_ids]
    offset = source_world - wrist
    along = offset @ axis
    projected = np.column_stack((offset @ u, offset @ v))
    center_2d = projected.mean(axis=0)
    relative = projected - center_2d
    radii = np.max(abs(relative), axis=0)
    if np.any(radii < .003):
        raise ValueError('source opening is too narrow for a cloth closure')
    envelope = float(np.sqrt(((relative / radii) ** 2).sum(axis=1)).max())
    radii = radii * envelope + .0015
    signed_area = np.sum(projected[:, 0] * np.roll(projected[:, 1], -1) - projected[:, 1] * np.roll(projected[:, 0], -1))
    if abs(signed_area) < 1e-8:
        raise ValueError('source loop has a degenerate projected winding')
    orientation = 1 if signed_area > 0 else -1
    edge_lengths = np.linalg.norm(np.roll(source_world, -1, axis=0) - source_world, axis=1)
    parameters = np.concatenate(([0.0], np.cumsum(edge_lengths[:-1]))) / edge_lengths.sum()
    source_angles = np.arctan2(relative[:, 1], relative[:, 0])
    phase = np.angle(np.exp(1j * (source_angles - orientation * 2 * np.pi * parameters)).sum())
    angles = phase + orientation * 2 * np.pi * parameters
    end = float(along.max()) + .004
    center = wrist + axis * end + u * center_2d[0] + v * center_2d[1]
    outer = center + np.cos(angles)[:, None] * radii[0] * u + np.sin(angles)[:, None] * radii[1] * v
    inner = center + axis * .0015 + np.cos(angles)[:, None] * (radii[0] - .0015) * u + np.sin(angles)[:, None] * (radii[1] - .0015) * v
    target_positions = np.concatenate((source_world, outer, outer, inner, inner, [center + axis * .0015]))
    new_joints = np.concatenate([joints[boundary_ids]] * 5 + [np.zeros((1, 4), dtype=int)])
    new_weights = np.concatenate([weights[boundary_ids]] * 5 + [np.zeros((1, 4))])
    masses = np.zeros(len(skin['joints']))
    for vertex in boundary_ids:
        for palette, weight in zip(joints[vertex], weights[vertex]):
            masses[palette] += weight
    selected = np.argsort(masses)[-4:][::-1]
    new_joints[-1] = selected
    new_weights[-1] = masses[selected] / masses[selected].sum()
    new_matrices = np.sum(transforms[new_joints] * new_weights[:, :, None, None], axis=1)
    raw = np.array([np.linalg.inv(matrix[:3, :3]) @ (point - matrix[:3, 3]) for point, matrix in zip(target_positions, new_matrices)])
    raw[:n] = positions[boundary_ids]
    actual_world = np.einsum('vij,vj->vi', new_matrices, np.column_stack((raw, np.ones(len(raw)))))[:, :3]
    generated_faces = []
    for i in range(n):
        j = (i + 1) % n
        generated_faces.extend(((j, i, n + i), (j, n + i, n + j),
                                (2*n + j, 2*n + i, 3*n + i), (2*n + j, 3*n + i, 3*n + j),
                                (4*n + j, 4*n + i, 5*n)))
    generated_faces = np.array(generated_faces, dtype=int)
    triangles = actual_world[generated_faces]
    face_normals = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    if np.min(np.linalg.norm(face_normals, axis=1)) < 1e-11:
        raise ValueError('generated closure contains a degenerate triangle')
    cap_normal = face_normals[4::5].mean(axis=0)
    if cap_normal @ axis <= 0:
        raise ValueError('generated cap winding does not face the proximal exterior')
    # Source normals are not valid normals for the newly generated transition.
    # Split only generated corners at real folds. Every smooth group contains
    # pairwise normals within 45 degrees, so its average faces every member.
    unit_face_normals = face_normals / np.linalg.norm(face_normals, axis=1)[:, None]
    adjacency = [[] for _ in raw]
    for face_id, face in enumerate(generated_faces):
        for vertex in face:
            adjacency[int(vertex)].append(face_id)
    origin_ids = []
    corner_normals = []
    split_faces = np.empty_like(generated_faces)
    crease_cosine = math.cos(math.radians(45))
    for vertex, adjacent in enumerate(adjacency):
        groups = []
        for face_id in adjacent:
            group = next((group for group in groups if all(unit_face_normals[face_id] @ unit_face_normals[other] >= crease_cosine for other in group)), None)
            if group is None:
                group = []
                groups.append(group)
            group.append(face_id)
        for group in groups:
            normal = face_normals[group].sum(axis=0)
            normal /= np.linalg.norm(normal)
            new_id = len(origin_ids)
            origin_ids.append(vertex)
            corner_normals.append(normal)
            for face_id in group:
                split_faces[face_id, np.flatnonzero(generated_faces[face_id] == vertex)] = new_id
    origin_ids = np.array(origin_ids, dtype=int)
    center_joints = new_joints[-1].tolist()
    center_weights = new_weights[-1].tolist()
    raw = raw[origin_ids]
    new_joints = new_joints[origin_ids]
    new_weights = new_weights[origin_ids]
    new_matrices = new_matrices[origin_ids]
    actual_world = actual_world[origin_ids]
    generated_faces = split_faces
    raw_normals = np.array([matrix[:3, :3].T @ normal for matrix, normal in zip(new_matrices, corner_normals)])
    raw_normals /= np.linalg.norm(raw_normals, axis=1)[:, None]
    boundary_copies = [np.flatnonzero(origin_ids == i).tolist() for i in range(n)]
    # Geometric adjacency uses welded positions, including hard-normal seam copies.
    all_world = np.concatenate((world_positions, actual_world))
    _, weld_all = np.unique(np.round(all_world, 6), axis=0, return_inverse=True)
    generated_weld = weld_all[len(world_positions):][generated_faces]
    source_weld = weld_all[:len(world_positions)][faces]
    cap_tree = _tree(actual_world, generated_faces)
    crossings = []
    for a, b in cap_tree.overlap(cap_tree):
        if a >= b or set(generated_weld[a]) & set(generated_weld[b]):
            continue
        if _triangles_cross(actual_world[generated_faces[a]], actual_world[generated_faces[b]]):
            crossings.append((int(a), int(b)))
    source_crossings = []
    for a, b in cap_tree.overlap(_tree(world_positions, faces)):
        if set(generated_weld[a]) & set(source_weld[b]):
            continue
        if _triangles_cross(actual_world[generated_faces[a]], world_positions[faces[b]]):
            source_crossings.append((int(a), int(b)))
    if crossings or source_crossings:
        raise ValueError('closure intersects itself/source: ' + str((len(crossings), len(source_crossings))))
    sample_request = {'uv': uv[boundary_ids].tolist(),
                      'base': str(REPO / atlas_side['textures']['base_color']['path']),
                      'mr': str(REPO / atlas_side['textures']['metallic_roughness']['path'])}
    sampler_code = '''import json,sys,numpy as np
from PIL import Image
d=json.load(sys.stdin)
def sample(path):
 a=np.asarray(Image.open(path).convert('RGB'),dtype=float);h,w=a.shape[:2];rows=[]
 for u,v in d['uv']:
  x=np.clip(u*w-.5,0,w-1);y=np.clip(v*h-.5,0,h-1);ix=int(x);iy=int(y);jx=min(ix+1,w-1);jy=min(iy+1,h-1);fx=x-ix;fy=y-iy
  rows.append(a[iy,ix]*(1-fx)*(1-fy)+a[iy,jx]*fx*(1-fy)+a[jy,ix]*(1-fx)*fy+a[jy,jx]*fx*fy)
 return np.array(rows)
b=sample(d['base']);mr=sample(d['mr']);s=b/255;l=np.where(s<=.04045,s/12.92,((s+.055)/1.055)**2.4)
print(json.dumps({'base_mean_srgb8':b.mean(axis=0).tolist(),'base_mean_linear':l.mean(axis=0).tolist(),'roughness_mean':float(mr[:,1].mean()/255),'roughness_min_max':[float(mr[:,1].min()/255),float(mr[:,1].max()/255)],'source_metallic_mean':float(mr[:,2].mean()/255)}))'''
    sampled = subprocess.run(['python3', '-B', '-c', sampler_code], input=json.dumps(sample_request),
                             capture_output=True, text=True, check=True)
    color = json.loads(sampled.stdout)
    material_index = len(document['materials'])
    document['materials'].append({'name': side + '_GeneratedGreyClothClosure', 'doubleSided': False,
                                  'pbrMetallicRoughness': {'baseColorFactor': [*color['base_mean_linear'], 1],
                                                         'metallicFactor': 0,
                                                         'roughnessFactor': max(.04, min(1, color['roughness_mean']))},
                                  'extras': {'generated_closure': True, 'normal_map': False}})
    generated_uv = np.zeros((5*n + 1, 2), dtype='<f4')
    for ring in range(5):
        generated_uv[ring*n:(ring+1)*n, 0] = parameters
        generated_uv[ring*n:(ring+1)*n, 1] = ring / 4
    generated_uv[-1] = (.5, .5)
    generated_uv = generated_uv[origin_ids]
    descriptors = {semantic: document['accessors'][attrs[semantic]] for semantic in attrs}
    generated_attributes = {
        'POSITION': append_accessor(raw.astype('<f4'), descriptors['POSITION'], 34962),
        'NORMAL': append_accessor(raw_normals.astype('<f4'), descriptors['NORMAL'], 34962),
        'TEXCOORD_0': append_accessor(generated_uv, descriptors['TEXCOORD_0'], 34962),
        'JOINTS_0': append_accessor(new_joints.astype(np.dtype({5121: '<u1', 5123: '<u2'}[descriptors['JOINTS_0']['componentType']])), descriptors['JOINTS_0'], 34962),
        'WEIGHTS_0': append_accessor(new_weights.astype('<f4'), descriptors['WEIGHTS_0'], 34962),
    }
    index_accessor = append_accessor(generated_faces.astype('<u2').reshape(-1, 1), {'componentType': 5123, 'type': 'SCALAR'}, 34963)
    primitive_id = len(document['meshes'][0]['primitives'])
    document['meshes'][0]['primitives'].append({'attributes': generated_attributes, 'indices': index_accessor,
                                              'material': material_index, 'mode': 4,
                                              'extras': {'generated_closure': True, 'source_original_triangles': False}})
    source_ids = np.load(HERE / 'selection.npz', allow_pickle=False)[selection_record['npz_prefix'] + '_source_vertex_ids']
    return {
        'generated_not_source': True, 'primitive': primitive_id, 'material': material_index,
        'vertices': len(raw), 'triangles': len(generated_faces),
        'boundary_loop_source_compact_ids': boundary_ids.tolist(),
        'boundary_loop_source_original_vertex_ids': source_ids[boundary_ids].tolist(),
        'boundary_copy_generated_vertex_ids': [copies[0] for copies in boundary_copies],
        'boundary_all_generated_vertex_copies': boundary_copies,
        'normal_crease_degrees': 45,
        'normal_split_origin_vertex_ids': origin_ids.tolist(),
        'geometry_and_winding_unchanged_by_normal_split': True,
        'source_boundary_span_mm': float(np.ptp(along) * 1000),
        'source_boundary_axis_range_metres': [float(along.min()), float(along.max())],
        'new_transition_axial_range_mm': [float((end-along).min()*1000), float((end-along).max()*1000)],
        'new_transition_actual_edge_range_mm': [float(np.linalg.norm(outer-source_world, axis=1).min()*1000), float(np.linalg.norm(outer-source_world, axis=1).max()*1000)],
        'rim_radial_thickness_mm': 1.5, 'rim_axial_thickness_mm': 1.5,
        'ellipse_radii_metres': radii.tolist(), 'ellipse_vertex_order': 'original directed loop order; monotone arc-length parameter, no angular sorting',
        'boundary_weights_copied_exact': True, 'center_joints': center_joints, 'center_weights': center_weights,
        'sampled_boundary_compact_ids': boundary_ids.tolist(), 'sampled_material': color,
        'base_color_sampling': 'actual adjacent atlas texels, bilinear sRGB values converted by sRGB EOTF before linear averaging',
        'roughness_sampling': 'actual metallic_roughness atlas green channel, linear',
        'material_texture_paths': sample_request, 'generated_attributes': generated_attributes,
        'generated_indices_accessor': index_accessor, 'self_crossings': crossings, 'source_crossings': source_crossings,
        'source_streams_and_triangles_unchanged': True,
    }


def verify_serialized_hand(document, binary, closure, side):
    from prepare_rigged_warrior import local_matrix
    from prepare_character_library import decode_animation, node_order, sampled_local

    widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
    sizes = {5121: 1, 5123: 2, 5125: 4, 5126: 4}
    for accessor in document['accessors']:
        view = document['bufferViews'][accessor['bufferView']]
        expected = accessor['count'] * widths[accessor['type']] * sizes[accessor['componentType']]
        if view['byteLength'] != expected:
            raise ValueError('serialized accessor payload width/count mismatch')
    skin = document['skins'][0]
    bind = attribute(document, binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    primitives = document['meshes'][0]['primitives']
    decoded = []
    for primitive in primitives:
        attrs = primitive['attributes']
        position = attribute(document, binary, attrs['POSITION'])
        joints = attribute(document, binary, attrs['JOINTS_0']).astype(int)
        weights = attribute(document, binary, attrs['WEIGHTS_0'], True)
        faces = attribute(document, binary, primitive['indices']).reshape(-1, 3).astype(int)
        if joints.min() < 0 or joints.max() >= len(skin['joints']):
            raise ValueError('serialized joint palette index is invalid')
        if not np.isfinite(weights).all() or np.max(abs(weights.sum(axis=1) - 1)) > 1e-5:
            raise ValueError('serialized weights are not finite normalized influences')
        decoded.append((position, joints, weights, faces))
    parents, order = node_order(document)
    tracks, _ = decode_animation(document, binary)

    def posed(time, include_normals=False):
        world = {}
        for index in order:
            node = document['nodes'][index]
            matrix = sampled_local(node, index, tracks, time) if time is not None and (index, 'rotation') in tracks else local_matrix(node)
            world[index] = world[parents[index]] @ matrix if index in parents else matrix
        transforms = np.array([list(world[index]) for index in skin['joints']]) @ bind
        result = []
        normal_dots = []
        for primitive_id, (positions, joints, weights, face_indices) in enumerate(decoded):
            blended = np.sum(transforms[joints] * weights[:, :, None, None], axis=1)
            points = np.einsum('vij,vj->vi', blended, np.column_stack((positions, np.ones(len(positions)))))[:, :3]
            if not np.isfinite(points).all():
                raise ValueError('serialized open/closed LBS is non-finite')
            result.append(points)
            if include_normals and primitive_id == 1:
                normals = attribute(document, binary, primitives[primitive_id]['attributes']['NORMAL'])
                world_normals = np.array([np.linalg.inv(matrix[:3, :3]).T @ normal for matrix, normal in zip(blended, normals)])
                world_normals /= np.linalg.norm(world_normals, axis=1)[:, None]
                triangle = points[face_indices]
                geometric = np.cross(triangle[:, 1] - triangle[:, 0], triangle[:, 2] - triangle[:, 0])
                geometric /= np.linalg.norm(geometric, axis=1)[:, None]
                average = world_normals[face_indices].mean(axis=1)
                average /= np.linalg.norm(average, axis=1)[:, None]
                normal_dots = np.einsum('ij,ij->i', average, geometric)
                if not np.isfinite(normal_dots).all() or normal_dots.min() <= 0:
                    raise ValueError('serialized generated normal opposes actual LBS face winding')
        return (result, normal_dots) if include_normals else result

    opened, open_dots = posed(0, True)
    closed, closed_dots = posed(1, True)
    default = posed(None)
    expected_default = closed if side == 'R' else opened
    default_error = max(float(np.linalg.norm(a - b, axis=1).max()) for a, b in zip(default, expected_default))
    if default_error > 1e-5:
        raise ValueError('serialized default Rclosed/Lopen contract failed')
    boundary = closure['boundary_loop_source_compact_ids']
    generated = closure['boundary_copy_generated_vertex_ids']
    seam = max(float(np.linalg.norm(pose[0][source_id] - pose[1][copies], axis=1).max())
               for pose in (opened, closed) for source_id, copies in zip(boundary, closure['boundary_all_generated_vertex_copies']))
    if seam > 1e-6:
        raise ValueError('serialized closure/source open-closed seam split')
    positions = np.concatenate([rows[0] for rows in decoded])
    faces = np.concatenate((decoded[0][3], decoded[1][3] + len(decoded[0][0])))
    _, weld = np.unique(np.round(positions, 6), axis=0, return_inverse=True)
    welded_faces = weld[faces]
    edges = np.concatenate((welded_faces[:, [0, 1]], welded_faces[:, [1, 2]], welded_faces[:, [2, 0]]))
    _, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    boundary_count = int((counts == 1).sum())
    if boundary_count or np.any(counts != 2):
        raise ValueError('combined welded-position closure has open/nonmanifold edges')
    return {
        'serialized_payload_bytecounts_exact': True,
        'generated_joints_componentType': document['accessors'][primitives[1]['attributes']['JOINTS_0']]['componentType'],
        'generated_joints_decoded_min_max': [int(decoded[1][1].min()), int(decoded[1][1].max())],
        'open_closed_serialized_lbs_finite': True,
        'open_closed_boundary_seam_max_metres': seam,
        'generated_closure_open_closed_max_motion_metres': float(np.linalg.norm(closed[1] - opened[1], axis=1).max()),
        'source_hand_open_closed_max_motion_metres': float(np.linalg.norm(closed[0] - opened[0], axis=1).max()),
        'combined_welded_position_boundary_edges': boundary_count,
        'combined_welded_position_edge_incidence_two': True,
        'source_primitive0_open_boundary_edges_preserved': len(boundary),
        'generated_normal_world_dot_min_open': float(open_dots.min()),
        'generated_normal_world_dot_min_closed': float(closed_dots.min()),
        'generated_normal_world_nonpositive_faces_open_closed': 0,
        'default_pose_contract': 'Rclosed' if side == 'R' else 'Lopen',
        'default_to_expected_grip_pose_max_error_metres': default_error,
    }


def build_rigs(source, source_binary, selection, arrays, atlas, remapped_uv):
    from mathutils import Matrix, Quaternion, Vector
    sys.path.insert(0, str(REPO / 'ArtSource/tripo-warrior'))
    from prepare_rigged_warrior import local_matrix, world_matrix, matrix_values, sample_track
    from prepare_character_library import decode_animation

    names = {node.get('name'): i for i, node in enumerate(source['nodes'])}
    rest = {name: world_matrix(source['nodes'], index) for name, index in names.items()}
    idle = next(clip for clip in source['animations'] if clip['name'] == 'idle')
    tracks, _ = decode_animation({**source, 'animations': [idle]}, source_binary)
    fingers = ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
    reflection = Matrix.Diagonal(Vector((-1, 1, 1, 1)))

    def rigid(matrix):
        position, rotation, _ = matrix.decompose()
        return Matrix.LocRotScale(position, rotation.normalized(), Vector((1, 1, 1)))

    def quaternion_values(value):
        return [float(value.x), float(value.y), float(value.z), float(value.w)]

    right_grip = rigid(rest['HandGrip_R'])
    right_conversion = Matrix.Rotation(-math.pi / 2, 4, 'X') @ right_grip.inverted()
    wrist = rest['L_Hand'].translation
    forward = sum((rest['L_' + digit + '3'].translation for digit in ('Index', 'Mid', 'Ring', 'Pinky')), Vector()) / 4 - wrist
    forward.normalize()
    radial = rest['L_Index1'].translation - rest['L_Pinky1'].translation
    radial -= forward * radial.dot(forward)
    radial.normalize()
    dorsal = radial.cross(forward).normalized()
    back = -forward
    lateral = dorsal.cross(back).normalized()
    left_frame = Matrix(((lateral.x, dorsal.x, back.x, wrist.x),
                         (lateral.y, dorsal.y, back.y, wrist.y),
                         (lateral.z, dorsal.z, back.z, wrist.z),
                         (0, 0, 0, 1)))
    left_conversion = left_frame.inverted()
    rig_manifest = {
        'formal_source': str(FORMAL.relative_to(REPO)), 'formal_sha256': FORMAL_SHA,
        'png_source': str(PNG.relative_to(REPO)), 'png_sha256': PNG_SHA,
        'selection_sha256': sha((HERE / 'selection.json').read_bytes()),
        'atlas_manifest_sha256': sha((HERE / 'atlas_manifest.json').read_bytes()),
        'uv_remap_npz_sha256': atlas['uv_remap_npz_sha256'],
        'default_pose': 'R defaults to actual idle@0 closed finger rotations; L defaults to source/rest open; every nonfinger node stays source default/rest',
        'grip_clip': 'time0=open source finger rest; time1=closed; only the selected 15 finger rotations animate',
        'tangent_contract': {'source_tangent': False, 'exported_tangent': False,
                             'required_runtime_generation': 'MikkTSpace from actual NORMAL and UV; PICO runtime behavior requires Root validation'},
        'sides': {},
    }
    for side in ('R', 'L'):
        document = {key: copy.deepcopy(source[key]) for key in ('asset', 'nodes', 'skins')}
        document.update(scene=0, scenes=[{'name': 'NativeFirstPerson' + side, 'nodes': []}],
                        meshes=[], accessors=[], bufferViews=[], buffers=[{'byteLength': 0}],
                        materials=[], images=[], textures=[], samplers=[])
        packed = bytearray()

        def append_bytes(payload, target=None):
            packed.extend(b'\0' * (-len(packed) % 4))
            index = len(document['bufferViews'])
            view = {'buffer': 0, 'byteOffset': len(packed), 'byteLength': len(payload)}
            if target is not None:
                view['target'] = target
            document['bufferViews'].append(view)
            packed.extend(payload)
            return index

        def append_accessor(rows, descriptor, target=None):
            rows = np.ascontiguousarray(rows)
            expected_dtype = np.dtype({5121: '<u1', 5123: '<u2', 5125: '<u4', 5126: '<f4'}[descriptor['componentType']])
            widths = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}
            if rows.dtype != expected_dtype or rows.shape != (len(rows), widths[descriptor['type']]):
                raise ValueError('accessor rows dtype/width disagrees with its componentType/type')
            index = len(document['accessors'])
            output = {key: copy.deepcopy(descriptor[key]) for key in ('componentType', 'type', 'normalized') if key in descriptor}
            output.update(bufferView=append_bytes(rows.tobytes(), target), count=len(rows))
            if output['type'] in ('VEC3', 'SCALAR') and len(rows):
                output['min'] = rows.min(axis=0).tolist()
                output['max'] = rows.max(axis=0).tolist()
            document['accessors'].append(output)
            return index

        texture_map, material_map = {}, {}
        atlas_side = atlas['sides'][side]
        role_by_texture = {source['materials'][0]['normalTexture']['index']: 'normal',
                           source['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']: 'base_color',
                           source['materials'][0]['pbrMetallicRoughness']['metallicRoughnessTexture']['index']: 'metallic_roughness'}
        document['samplers'] = [copy.deepcopy(atlas_side['sampler'])]

        def copy_texture(index):
            if index in texture_map:
                return texture_map[index]
            role = role_by_texture[index]
            texture = atlas_side['textures'][role]
            payload = (REPO / texture['path']).read_bytes()
            if sha(payload) != texture['sha256']:
                raise ValueError('frozen atlas texture identity changed')
            image_index = len(document['images'])
            document['images'].append({'name': side + '_' + role + '_atlas', 'mimeType': 'image/png',
                                        'bufferView': append_bytes(payload)})
            value = {'sampler': 0, 'source': image_index}
            texture_map[index] = len(document['textures'])
            document['textures'].append(value)
            return texture_map[index]

        def copy_material(index):
            if index in material_map:
                return material_map[index]
            value = copy.deepcopy(source['materials'][index])
            containers = [value, value.get('pbrMetallicRoughness', {})]
            for container in containers:
                for name, field in container.items():
                    if name.endswith('Texture') and isinstance(field, dict):
                        field['index'] = copy_texture(field['index'])
            material_map[index] = len(document['materials'])
            document['materials'].append(value)
            return material_map[index]

        primitives = []
        primitive_mapping = []
        for record in selection['sides'][side]['primitives']:
            prefix = record['npz_prefix']
            attributes = {}
            for semantic, info in record['attributes'].items():
                rows = arrays[info['npz_key']]
                if semantic == 'TEXCOORD_0':
                    if not np.array_equal(remapped_uv[prefix + '_source_vertex_ids'], arrays[prefix + '_source_vertex_ids']):
                        raise ValueError('atlas compact vertex order changed')
                    if not np.array_equal(remapped_uv[prefix + '_source_uv'], rows):
                        raise ValueError('atlas source UV differs from frozen selection')
                    rows = remapped_uv[atlas_side['uv_npz_key']]
                    if rows.shape != arrays[info['npz_key']].shape or not np.isfinite(rows).all():
                        raise ValueError('invalid atlas UV output')
                descriptor = source['accessors'][info['source_accessor']]
                attributes[semantic] = append_accessor(rows, descriptor, 34962)
            faces = arrays[prefix + '_indices'].astype('<u2')
            indices = append_accessor(faces.reshape(-1, 1), {'componentType': 5123, 'type': 'SCALAR'}, 34963)
            primitives.append({'attributes': attributes, 'indices': indices,
                               'material': copy_material(record['source_material']), 'mode': 4})
            primitive_mapping.append({**record, 'output_primitive': len(primitives) - 1,
                                       'output_attributes': copy.deepcopy(attributes), 'output_indices_accessor': indices})
        document['meshes'] = [{'name': side + '_ActualSourceHand', 'primitives': primitives}]
        mesh_node = next(node for node in document['nodes'] if 'mesh' in node)
        mesh_node['mesh'] = 0
        bind_index = source['skins'][0]['inverseBindMatrices']
        bind = attribute(source, source_binary, bind_index)
        document['skins'][0]['inverseBindMatrices'] = append_accessor(bind, source['accessors'][bind_index])
        conversion = right_conversion if side == 'R' else left_conversion
        conversion_index = len(document['nodes'])
        document['nodes'].append({'name': 'SourceHandRigidConversion', 'matrix': matrix_values(conversion),
                                  'children': copy.deepcopy(source['scenes'][source.get('scene', 0)]['nodes'])})
        root_index = len(document['nodes'])
        document['nodes'].append({'name': 'RightGripRoot' if side == 'R' else 'LeftAnatomicalWristRoot',
                                  'children': [conversion_index]})
        document['scenes'][0]['nodes'] = [root_index]
        if side == 'L' and 'HandGrip_L' not in names:
            mirrored_grip = reflection @ rest['HandGrip_R'] @ reflection
            local_grip = rest['L_Hand'].inverted() @ mirrored_grip
            index = len(document['nodes'])
            document['nodes'].append({'name': 'DerivedHandGrip_L', 'matrix': matrix_values(local_grip),
                                      'extras': {'derived': True, 'basis': 'mirrored calibrated R grip in actual L rest basis'}})
            document['nodes'][names['L_Hand']].setdefault('children', []).append(index)
        time_accessor = append_accessor(np.array([[0], [1]], dtype='<f4'), {'componentType': 5126, 'type': 'SCALAR'})
        animation = {'name': 'grip', 'channels': [], 'samplers': []}
        angles = {}
        for digit in fingers:
            for segment in (1, 2, 3):
                name = side + '_' + digit + str(segment)
                index = names[name]
                open_q = local_matrix(source['nodes'][index]).to_quaternion().normalized()
                right_name = 'R_' + digit + str(segment)
                right_index = names[right_name]
                x, y, z, w = sample_track(tracks[(right_index, 'rotation')], 0, True)
                right_closed = Quaternion((w, x, y, z)).normalized()
                if side == 'R':
                    closed_q = right_closed
                else:
                    right_open = local_matrix(source['nodes'][right_index]).to_quaternion().normalized()
                    delta = right_open.inverted() @ right_closed
                    right_basis = rest[right_name].to_quaternion().normalized().to_matrix().to_4x4()
                    left_basis = rest[name].to_quaternion().normalized().to_matrix().to_4x4()
                    mirrored = reflection @ right_basis @ delta.to_matrix().to_4x4() @ right_basis.inverted() @ reflection
                    local_delta = left_basis.inverted() @ mirrored @ left_basis
                    closed_q = (open_q @ local_delta.to_quaternion().normalized()).normalized()
                if open_q.dot(closed_q) < 0:
                    closed_q.negate()
                rows = np.array([quaternion_values(open_q), quaternion_values(closed_q)], dtype='<f4')
                output = append_accessor(rows, {'componentType': 5126, 'type': 'VEC4'})
                animation['channels'].append({'sampler': len(animation['samplers']), 'target': {'node': index, 'path': 'rotation'}})
                animation['samplers'].append({'input': time_accessor, 'output': output, 'interpolation': 'LINEAR'})
                angles[name] = math.degrees(open_q.rotation_difference(closed_q).angle)
                if side == 'R':
                    document['nodes'][index]['rotation'] = quaternion_values(closed_q)
        document['animations'] = [animation]
        original_prefix = bytes(packed)
        original_primitive = copy.deepcopy(document['meshes'][0]['primitives'][0])
        closure = add_sleeve_closure(document, packed, side, selection['sides'][side]['primitives'][0], append_accessor, atlas_side)
        if bytes(packed[:len(original_prefix)]) != original_prefix or document['meshes'][0]['primitives'][0] != original_primitive:
            raise AssertionError('generated closure modified original source streams/triangles')
        packed.extend(b'\0' * (-len(packed) % 4))
        document['buffers'][0]['byteLength'] = len(packed)
        output_path = HERE / ('right_hand_png.glb' if side == 'R' else 'left_hand_png.glb')
        output_path.write_bytes(encode_glb(document, bytes(packed)))
        serialized_document, serialized_binary = read_glb(output_path)
        serialized_verification = verify_serialized_hand(serialized_document, serialized_binary, closure, side)
        rig_manifest['sides'][side] = {
            'path': str(output_path.relative_to(REPO)), 'sha256': sha(output_path.read_bytes()),
            'bytes': output_path.stat().st_size, 'triangles': selection['sides'][side]['triangles'] + closure['triangles'],
            'source_triangles': selection['sides'][side]['triangles'], 'generated_closure': closure,
            'serialized_verification': serialized_verification,
            'root_node_identity': True, 'root_node': root_index,
            'source_asset_to_output_matrix_gltf': matrix_values(conversion),
            'source_normalization_preserved': True, 'source_inverse_bind_matrices_exact': True,
            'joint_palette_count': len(source['skins'][0]['joints']), 'palette_pruned': False,
            'primitive_mapping': primitive_mapping, 'finger_open_closed_angle_degrees': angles,
            'closed_source': 'actual source idle@0 R finger rotations' if side == 'R' else 'R curl mirrored in actual L/R default-rest bone bases; derived, not authored L closed',
            'root_frame': 'actual authored R grip, +Y up / -Z blade forward' if side == 'R' else 'L_Hand anatomical wrist; +Y dorsal / -Z fingers',
            'left_basis_definition': None if side == 'R' else {
                'forward': 'mean(Index3,Mid3,Ring3,Pinky3) minus L_Hand',
                'radial': 'L_Index1 minus L_Pinky1 orthogonalized to forward',
                'dorsal': 'cross(radial,forward)', 'matrix_asset_frame': matrix_values(left_frame)},
            'atlas_applied': True,
            'atlas_textures': atlas_side['textures'],
            'source_uv_degenerate_face_ids': atlas_side['zero_area_source_face_ids'],
            'output_uv_sha256': sha(remapped_uv[atlas_side['uv_npz_key']].tobytes()),
        }
        print('HAND_RIG_READY ' + side + ' ' + str(output_path) + ' ' + rig_manifest['sides'][side]['sha256'], flush=True)
    (HERE / 'rig_manifest.json').write_text(json.dumps(rig_manifest, indent=2) + '\n')
    return rig_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection-only', action='store_true')
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ([] if '--python' in sys.argv else sys.argv[1:])
    args = parser.parse_args(argv)
    document, binary, equivalence = verify_inputs()
    selection, arrays = select_hands(document, binary, equivalence)
    if not args.selection_only:
        atlas_path = HERE / 'atlas_manifest.json'
        if sha(atlas_path.read_bytes()) != 'b8d66b744131484cf17a2ce0158ddf14f0b681a8cfea7facfef244f57254425d':
            raise ValueError('Root-approved atlas identity changed')
        atlas = json.loads(atlas_path.read_text())
        if atlas['selection_sha256'] != sha((HERE / 'selection.json').read_bytes()):
            raise ValueError('atlas does not identify frozen hand selection')
        if atlas['source_material_json'] != document['materials'][0]:
            raise ValueError('atlas material factors differ from source')
        uv_path = REPO / atlas['uv_remap_npz']
        if sha(uv_path.read_bytes()) != atlas['uv_remap_npz_sha256']:
            raise ValueError('atlas remapped UV identity changed')
        with np.load(uv_path, allow_pickle=False) as data:
            remapped_uv = {key: data[key] for key in data.files}
        build_rigs(document, binary, selection, arrays, atlas, remapped_uv)


if __name__ == '__main__':
    main()
