"""Build the left hand in the shared Grip frame from accepted right geometry.

Reflection is baked into geometry, proper local transforms and inverse binds.
The scene root is identity. No legacy left offset, corrective frame, negative
scale, palette pruning or rebind is part of this asset contract.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
GRIP = HERE.parent
NATIVE = GRIP.parent
REPO = HERE.parents[5]
sys.path.insert(0, str(GRIP))
import build_grip as common
import numpy as np

h = common.helpers
SOURCE = GRIP / 'right_hand_refined_v2.glb'
SOURCE_SHA = '3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0'
DAO = REPO / 'ArtSource/tripo-warrior/library/dao_grip.glb'
DAO_SHA = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'
S = np.diag([-1., 1., 1., 1.])
COMPONENT_TYPES = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2',
                   5125: '<u4', 5126: '<f4'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def swap_name(name):
    if name.startswith('R_'):
        return 'L_' + name[2:]
    if name.startswith('L_'):
        return 'R_' + name[2:]
    if name.endswith('_R'):
        return name[:-2] + '_L'
    if name.endswith('_L'):
        return name[:-2] + '_R'
    if name == 'RightGripRoot':
        return 'LeftGripRoot'
    return name


def reflect_quaternions(values):
    result = np.array(values, copy=True)
    result[..., 1:3] *= -1
    return result


def conjugate_flat_matrices(values):
    matrices = np.asarray(values).reshape(-1, 4, 4).transpose(0, 2, 1)
    reflected = S @ matrices @ S
    return reflected.transpose(0, 2, 1).reshape(np.asarray(values).shape)


def reflect_node(node):
    result = copy.deepcopy(node)
    if 'matrix' in node:
        result['matrix'] = conjugate_flat_matrices(np.array(node['matrix'])).tolist()
    else:
        if 'translation' in node:
            result['translation'][0] *= -1
        if 'rotation' in node:
            result['rotation'] = reflect_quaternions(np.array(node['rotation'])).tolist()
        # Diagonal scale commutes with S; the source positive scale is kept.
    if 'name' in node:
        result['name'] = swap_name(node['name'])
    return result


def rebuild(source, binary):
    result = copy.deepcopy(source)
    result['nodes'] = [reflect_node(node) for node in source['nodes']]
    if any(node.get('name') == 'DerivedHandGrip_L' for node in result['nodes']):
        raise ValueError('source unexpectedly contains the rejected legacy marker')
    names = [node.get('name') for node in result['nodes'] if node.get('name')]
    if len(names) != len(set(names)):
        raise ValueError('full bilateral name swap created duplicate node names')
    packed = bytearray(binary)
    cache = {}
    edits = []

    def append(accessor_index, values, operation):
        key = (accessor_index, operation)
        if key in cache:
            return cache[key]
        descriptor = copy.deepcopy(source['accessors'][accessor_index])
        if descriptor.get('sparse'):
            raise ValueError('pinned source must use explicit dense accessors')
        dtype = np.dtype(COMPONENT_TYPES[descriptor['componentType']])
        values = np.asarray(values, dtype=dtype)
        if len(values) != descriptor['count']:
            raise ValueError('reflected accessor count changed')
        packed.extend(b'\0' * (-len(packed) % 4))
        view = {'buffer': 0, 'byteOffset': len(packed), 'byteLength': values.nbytes}
        old_view = source['bufferViews'][descriptor['bufferView']]
        if 'target' in old_view:
            view['target'] = old_view['target']
        view_index = len(result['bufferViews'])
        result['bufferViews'].append(view)
        packed.extend(values.tobytes())
        descriptor['bufferView'] = view_index
        descriptor.pop('byteOffset', None)
        if 'min' in descriptor or 'max' in descriptor:
            rows = values.reshape(descriptor['count'], -1)
            descriptor['min'] = rows.min(axis=0).tolist()
            descriptor['max'] = rows.max(axis=0).tolist()
        new_index = len(result['accessors'])
        result['accessors'].append(descriptor)
        cache[key] = new_index
        edits.append({'source_accessor': accessor_index, 'candidate_accessor': new_index,
                      'operation': operation, 'count': descriptor['count'],
                      'componentType': descriptor['componentType'], 'byte_length': values.nbytes})
        return new_index

    for mesh in result['meshes']:
        if 'name' in mesh:
            mesh['name'] = swap_name(mesh['name'])
        for primitive in mesh['primitives']:
            if primitive.get('mode', 4) != 4 or 'indices' not in primitive:
                raise ValueError('pinned hand must use indexed triangle primitives')
            for semantic in ('POSITION', 'NORMAL', 'TANGENT'):
                if semantic not in primitive['attributes']:
                    continue
                accessor = primitive['attributes'][semantic]
                values = h.values(source, binary, accessor).copy()
                values[:, 0] *= -1
                if semantic == 'TANGENT':
                    if values.shape[1] != 4:
                        raise ValueError('base TANGENT requires VEC4 handedness')
                    values[:, 3] *= -1
                primitive['attributes'][semantic] = append(accessor, values, semantic + '_reflect_X')
            for target in primitive.get('targets', []):
                for semantic in ('POSITION', 'NORMAL', 'TANGENT'):
                    if semantic in target:
                        accessor = target[semantic]
                        values = h.values(source, binary, accessor).copy()
                        values[:, 0] *= -1
                        target[semantic] = append(accessor, values, 'morph_' + semantic + '_reflect_X')
            accessor = primitive['indices']
            values = h.values(source, binary, accessor).copy()
            triangles = values.reshape(-1, 3)
            triangles[:, [1, 2]] = triangles[:, [2, 1]]
            primitive['indices'] = append(accessor, values, 'triangle_reverse_winding')

    for skin in result['skins']:
        accessor = skin['inverseBindMatrices']
        skin['inverseBindMatrices'] = append(
            accessor, conjugate_flat_matrices(h.values(source, binary, accessor)), 'IBM_S_M_S',
        )
    for animation in result.get('animations', []):
        roles = {}
        for channel in animation['channels']:
            sampler = channel['sampler']
            path = channel['target']['path']
            if sampler in roles and roles[sampler] != path:
                raise ValueError('source sampler is shared by incompatible animation paths')
            roles[sampler] = path
        for sampler, path in roles.items():
            if path not in ('rotation', 'translation'):
                continue
            accessor = animation['samplers'][sampler]['output']
            values = h.values(source, binary, accessor).copy()
            if path == 'rotation':
                values = reflect_quaternions(values)
            else:
                values[:, 0] *= -1
            animation['samplers'][sampler]['output'] = append(accessor, values, 'animation_' + path + '_reflect_X')
    for scene in result['scenes']:
        scene['name'] = 'NativeFirstPersonLRebuilt'
        for root in scene['nodes']:
            if not np.allclose(h.local(result['nodes'][root]), np.eye(4), atol=1e-12, rtol=0):
                raise ValueError('outer scene root is not identity')
            if result['nodes'][root].get('name') != 'LeftGripRoot':
                raise ValueError('outer root must expose only the new common-Grip ABI')
    result['buffers'][0]['byteLength'] = len(packed)
    return result, bytes(packed), edits


def skin_normals(document, binary, primitive, worlds):
    skin = document['skins'][0]
    inverse = h.values(document, binary, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
    transforms = np.array([worlds[i] for i in skin['joints']]) @ inverse
    attrs = primitive['attributes']
    palettes = h.values(document, binary, attrs['JOINTS_0']).astype(int)
    weights = h.values(document, binary, attrs['WEIGHTS_0'])
    blended = np.sum(transforms[palettes] * weights[:, :, None, None], axis=1)
    normals = h.values(document, binary, attrs['NORMAL'])
    normals = np.einsum('vij,vj->vi', np.linalg.inv(blended[:, :3, :3]).transpose(0, 2, 1), normals)
    return normals / np.linalg.norm(normals, axis=1)[:, None]


def verify(source, binary, candidate, candidate_binary):
    h.accessor_storage(candidate, candidate_binary)
    if candidate_binary[:len(binary)] != binary:
        raise AssertionError('original data/image BIN prefix changed')
    for key in ('materials', 'images', 'textures', 'samplers', 'extensionsUsed', 'extensionsRequired'):
        if source.get(key) != candidate.get(key):
            raise AssertionError('source material/image contract changed: ' + key)
    if len(source['nodes']) != len(candidate['nodes']):
        raise AssertionError('unexpected legacy frame or marker added')
    if len(source['skins']) != len(candidate['skins']) or len(candidate['skins'][0]['joints']) != 78:
        raise AssertionError('source full palette was pruned/rebound')
    if source['skins'][0]['joints'] != candidate['skins'][0]['joints']:
        raise AssertionError('joint palette index ordering changed')
    local_errors = []
    local_determinants = []
    for old, new in zip(source['nodes'], candidate['nodes']):
        local_errors.append(float(abs(h.local(new) - S @ h.local(old) @ S).max()))
        local_determinants.append(float(np.linalg.det(h.local(new)[:3, :3])))
        if 'scale' in new and np.any(np.array(new['scale']) <= 0):
            raise AssertionError('negative or zero node scale')
    if max(local_errors) > 1e-12 or min(local_determinants) <= 0:
        raise AssertionError('local conjugation/proper-transform contract failed')
    results = []
    total_triangles = 0
    for time in (0, .5, 1):
        old_world = h.sampled_worlds(source, binary, 'grip', time)
        new_world = h.sampled_worlds(candidate, candidate_binary, 'grip', time)
        joint_error = max(float(abs(new_world[i] - S @ old_world[i] @ S).max())
                          for i in source['skins'][0]['joints'])
        primitives = []
        for mesh_index, (old_mesh, new_mesh) in enumerate(zip(source['meshes'], candidate['meshes'])):
            for pi, (old, new) in enumerate(zip(old_mesh['primitives'], new_mesh['primitives'])):
                for semantic in ('TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0'):
                    a = h.values(source, binary, old['attributes'][semantic])
                    b = h.values(candidate, candidate_binary, new['attributes'][semantic])
                    if a.dtype != b.dtype or a.tobytes() != b.tobytes():
                        raise AssertionError('unchanged skin/UV bytes differ')
                before = h.skin(source, binary, old, old_world)
                actual = h.skin(candidate, candidate_binary, new, new_world)
                expected = before @ S[:3, :3].T
                error = float(abs(actual - expected).max())
                source_normal = skin_normals(source, binary, old, old_world)
                actual_normal = skin_normals(candidate, candidate_binary, new, new_world)
                normal_error = float(abs(actual_normal - source_normal @ S[:3, :3].T).max())
                old_faces = h.values(source, binary, old['indices']).reshape(-1, 3).astype(int)
                new_faces = h.values(candidate, candidate_binary, new['indices']).reshape(-1, 3).astype(int)
                if not np.array_equal(new_faces, old_faces[:, [0, 2, 1]]):
                    raise AssertionError('actual exported winding differs')
                a = before[old_faces]
                b = actual[new_faces]
                old_cross = np.cross(a[:, 1] - a[:, 0], a[:, 2] - a[:, 0])
                new_cross = np.cross(b[:, 1] - b[:, 0], b[:, 2] - b[:, 0])
                face_error = float(abs(new_cross - old_cross @ S[:3, :3].T).max())
                if max(error, normal_error, face_error, joint_error) > 2e-6:
                    raise AssertionError('actual reflected skin/normal/geometry mismatch')
                primitives.append({
                    'mesh': mesh_index, 'primitive': pi, 'vertices': len(actual),
                    'triangles': len(new_faces), 'actual_LBS_max_coordinate_error_m': error,
                    'actual_inverse_transpose_skin_NORMAL_max_error': normal_error,
                    'actual_winding_geometric_area_vector_max_error_m2': face_error,
                })
                if time == 0:
                    total_triangles += len(new_faces)
        results.append({'grip_time': time, 'joint_world_S_M_S_max_error': joint_error,
                        'primitives': primitives})
    return {
        'passed': True, 'real_skin_comparison': 'Lskin = S * Rskin in common Grip; no C/B factor',
        'default_pose': 'complete mirrored accepted Right source default closed; grip@0 remains open',
        'grip_times': results, 'triangles_total': total_triangles,
        'full_joint_palette': 78, 'palette_and_weight_bytes_preserved': True,
        'local_S_M_S_max_error': max(local_errors),
        'proper_local_determinant_range': [min(local_determinants), max(local_determinants)],
        'UV_material_and_three_KTX_payloads_byte_exact': True,
        'source_original_BIN_prefix_exact': True,
        'all_outer_scene_roots_identity': True, 'legacy_DerivedHandGrip_L_present': False,
    }


def control_tests():
    # Nontrivial quaternion and tangent fixture verifies the reflection rules,
    # including the handedness sign that a position-only mirror would miss.
    quaternion = np.array([.2, -.3, .4, .8])
    quaternion /= np.linalg.norm(quaternion)
    if not np.allclose(h.quat_matrix(reflect_quaternions(quaternion)),
                       S @ h.quat_matrix(quaternion) @ S, atol=1e-12):
        raise AssertionError('quaternion conjugation fixture failed')
    tangent = np.array([.6, .8, 0., -1.])
    reflected = tangent * np.array([-1, 1, 1, -1])
    normal = np.array([0., 0., 1.])
    old_bitangent = np.cross(normal, tangent[:3]) * tangent[3]
    new_bitangent = np.cross(S[:3, :3] @ normal, reflected[:3]) * reflected[3]
    if not np.allclose(new_bitangent, S[:3, :3] @ old_bitangent):
        raise AssertionError('tangent handedness fixture failed')
    return {'passed': True, 'cases': ['proper quaternion S conjugation', 'tangent xyz reflection and w sign']}


def build():
    if digest(SOURCE.read_bytes()) != SOURCE_SHA or digest(DAO.read_bytes()) != DAO_SHA:
        raise ValueError('accepted Right/dao source identity changed')
    source, binary = h.read(SOURCE)
    control = control_tests()
    result, packed, edits = rebuild(source, binary)
    target = HERE / 'left_hand_rebuilt.glb'
    target.write_bytes(common.encode_glb(result, packed))
    actual, actual_binary = h.read(target)
    checks = verify(source, binary, actual, actual_binary)
    mapping = {
        'contract': 'Both hand roots receive finalGrip G directly; Left asset and Right/dao share Grip origin and axes.',
        'source_right_sha256': SOURCE_SHA,
        'reflection_S_rowmajor': S.tolist(),
        'outer_root': {'name': 'LeftGripRoot', 'matrix_rowmajor': np.eye(4).tolist()},
        'asset_geometry': 'P/N reflect X, tangent.xyz reflect X and tangent.w changes sign, triangle winding swaps last two indices',
        'rig_and_IBM': 'S * M * S; translations reflect X, proper quaternions map (x,y,z,w) to (x,-y,-z,w), positive scales unchanged',
        'runtime_equation': 'pL_world = G * S * pR_Grip; handRootL = G',
        'runtime_migration': 'Root must atomically remove previous LEFT_WRIST_FROM_GRIP and derived-marker placement. This builder does not modify Kotlin.',
        'legacy_C_or_B_frame_in_asset': False,
        'legacy_DerivedHandGrip_L_in_asset': False,
        'names': [{'node': i, 'source': a.get('name'), 'candidate': b.get('name')}
                  for i, (a, b) in enumerate(zip(source['nodes'], actual['nodes']))],
    }
    (HERE / 'mapping.json').write_text(json.dumps(mapping, indent=2) + '\n')
    manifest = {
        'source': str(SOURCE.relative_to(REPO)), 'source_sha256': SOURCE_SHA,
        'candidate': str(target.relative_to(REPO)), 'candidate_sha256': digest(target.read_bytes()),
        'dao_sha256': DAO_SHA, 'mapping_sha256': digest((HERE / 'mapping.json').read_bytes()),
        'producer_sha256': digest(Path(__file__).read_bytes()),
        'accessor_transform_mapping': edits, 'checks': checks, 'control_tests': control,
        'source_KTX_payload_sha256': [digest(h.image_bytes(source, binary, i)) for i in range(len(source['images']))],
        'candidate_KTX_payload_sha256': [digest(h.image_bytes(actual, actual_binary, i)) for i in range(len(actual['images']))],
        'source_missing_TANGENT': [pi for pi, p in enumerate(source['meshes'][0]['primitives']) if 'TANGENT' not in p['attributes']],
        'normal_mapping': 'Original UV/KTX and NORMAL retained under reflection; missing TANGENT remains the existing runtime MikkTSpace generation contract.',
        'rebuild_command': 'python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/build_left.py',
        'limits': ['Natural-grip quality and actual rendering require Root review.',
                   'The rebuilt hand inherits accepted Right source contacts/intersections; reflection is not an automatic anatomical approval.',
                   'Current Kotlin still uses its old offset until Root atomically switches app and asset.'],
        'status': '实现阶段结束，等待 Root review；common-Grip asset only, no public/runtime publication',
    }
    (HERE / 'rebuild_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'candidate_sha256': manifest['candidate_sha256'], 'checks': checks}, indent=2), flush=True)


if __name__ == '__main__':
    build()
