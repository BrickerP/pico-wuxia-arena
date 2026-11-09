"""Prepare the approved CLI rig in a common scene frame, preserving skin data.

Run with Blender 4.5 Python. Source mesh, weights, inverse binds and texture
bytes stay in place. The added parent frame transforms mesh and joints
uniformly, as specified by glTF scene/skin transform rules.
"""

import copy
import hashlib
import json
import math
import os
import struct
import tempfile
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector


HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'tripo-out/f2a5c5b3-rig-bb23cd4c/model.glb'
DAO_SOURCE = HERE.parent / 'dao/dao_study.glb'
SOURCE_SHA = '6e2ddd38982a5dc3baee45f7db8f545988e493ba994c29c40fb4ee1cff7cb3c9'
HEIGHT = 1.78
# Conservative curled-hand calibration, stored at the glTF R_Hand joint origin.
GRIP_LOCAL_FRAME = (
    -.18316746145743912, -.5286014485954089, -.037618815684032504, 0,
    -.2715799926541686, .12781040670100427, -.4735967545530686, 0,
    .4550594249261904, -.1364917456044495, -.2977851575238925, 0,
    .019713686436414718, .02435691554099322, -.02339721978455782, 1,
)
CLIP_SOURCES = (
    ('idle', 'bb23cd4c-retarget-2-43bfb8da', 'b4d92356d0c74e066d9301b7bf2bf6ef58f0ce209c821765b96610e5e2985645'),
    ('slash', 'bb23cd4c-retarget-a65f688a', '21fe0e6fd26e744308227b7e7d0d55cbef22346128753c44174a12320fe209b0'),
    ('hurt', 'bb23cd4c-retarget-3-221c8495', '4a664278fcbd244956898172606baefd19e216c146f47cdbac377594300dce08'),
    ('fall', 'bb23cd4c-retarget-4-44c8eae0', '542852badb502f3706b6b3e1932094522aee00db9991bea021c021cd0cf720c9'),
)


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or length != len(data):
        raise ValueError('invalid GLB: ' + str(path))
    json_size, json_kind = struct.unpack_from('<II', data, 12)
    if json_kind != 0x4E4F534A:
        raise ValueError('missing GLB JSON chunk')
    doc = json.loads(data[20:20+json_size])
    binary_size, binary_kind = struct.unpack_from('<II', data, 20+json_size)
    binary = data[28+json_size:28+json_size+binary_size]
    if binary_kind != 0x004E4942 or len(doc['buffers']) != 1:
        raise ValueError('expected one embedded GLB buffer')
    return doc, binary


def encode_glb(doc, binary):
    encoded = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    encoded += b' ' * (-len(encoded) % 4)
    binary += b'\0' * (-len(binary) % 4)
    header = struct.pack('<4sII', b'glTF', 2, 28+len(encoded)+len(binary))
    output = header + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded
    output += struct.pack('<II', len(binary), 0x004E4942) + binary
    return output


def output_info(path, output):
    return {'file': path.name, 'bytes': len(output), 'sha256': hashlib.sha256(output).hexdigest()}


def publish_outputs(outputs):
    """Stage the complete generation, restoring old files on publication error."""
    folder = outputs[0][0].parent
    if any(path.parent != folder for path, data in outputs):
        raise ValueError('grouped outputs must share one directory')
    with tempfile.TemporaryDirectory(prefix='.rigged-stage-', dir=folder) as temporary:
        stage = Path(temporary)
        pending, previous = {}, {}
        for path, data in outputs:
            staged = stage / path.name
            staged.write_bytes(data)
            pending[path] = staged
            previous[path] = None
            if path.exists():
                backup = stage / (path.name + '.previous')
                os.link(path, backup)
                previous[path] = backup
        published = []
        try:
            for path, staged in pending.items():
                published.append(path)
                staged.replace(path)
        except BaseException:
            # A manual interruption must also restore a consistent generation.
            for path in reversed(published):
                if previous[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    previous[path].replace(path)
            raise


def write_glb(path, doc, binary):
    """Single-file helper used by temporary observation scripts."""
    output = encode_glb(doc, binary)
    publish_outputs(((path, output),))
    return output_info(path, output)


def matrix_values(matrix):
    return [float(matrix[row][column]) for column in range(4) for row in range(4)]


def local_matrix(node):
    if 'matrix' in node:
        values = node['matrix']
        return Matrix(tuple(tuple(values[row+column*4] for column in range(4)) for row in range(4)))
    x,y,z,w = node.get('rotation', (0,0,0,1))
    return Matrix.LocRotScale(Vector(node.get('translation', (0,0,0))),
                              Quaternion((w,x,y,z)), Vector(node.get('scale', (1,1,1))))


def world_matrix(nodes, target):
    parents = {child: index for index,node in enumerate(nodes) for child in node.get('children', [])}
    chain = []
    current = target
    while True:
        chain.append(current)
        if current not in parents:
            break
        current = parents[current]
    result = Matrix.Identity(4)
    for index in reversed(chain):
        result = result @ local_matrix(nodes[index])
    return result


def accessor_bytes(doc, binary, index):
    """Read supplied FLOAT scalar/vector values without resampling."""
    accessor = doc['accessors'][index]
    components = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4}
    if accessor['componentType'] != 5126 or accessor['type'] not in components:
        raise ValueError('expected FLOAT scalar/vector data')
    if 'sparse' in accessor or accessor.get('normalized'):
        raise ValueError('unexpected animation accessor encoding')
    view = doc['bufferViews'][accessor['bufferView']]
    width = components[accessor['type']] * 4
    stride = view.get('byteStride', width)
    count = accessor['count']
    start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    end = start + (count-1)*stride + width
    if view['buffer'] != 0 or count < 1 or stride < width:
        raise ValueError('invalid animation accessor layout')
    if end > view.get('byteOffset', 0)+view['byteLength'] or end > len(binary):
        raise ValueError('animation accessor exceeds its buffer view')
    return b''.join(binary[start+i*stride:start+i*stride+width] for i in range(count))


def animation_signature(doc, binary, animation):
    rows = []
    for channel in animation['channels']:
        sampler = animation['samplers'][channel['sampler']]
        row = [doc['nodes'][channel['target']['node']]['name'],
               channel['target']['path'], sampler.get('interpolation', 'LINEAR')]
        for key in ('input', 'output'):
            accessor = doc['accessors'][sampler[key]]
            row.append([accessor['type'], accessor['count'],
                        hashlib.sha256(accessor_bytes(doc, binary, sampler[key])).hexdigest()])
        rows.append(row)
    return hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest()


def append_animations(doc, binary, reference):
    """Copy only referenced curves into the existing body and joint nodes."""
    target_nodes = {node.get('name'): index for index,node in enumerate(doc['nodes'])}
    reference_nodes = {node.get('name'): index for index,node in enumerate(reference['nodes'])}
    reference_parents = {child: index for index,node in enumerate(reference['nodes'])
                         for child in node.get('children', [])}
    joint_names = {reference['nodes'][index]['name'] for index in reference['skins'][0]['joints']}
    packed = bytearray(binary)
    records = []
    doc['animations'] = []

    def parent_chain(document, parents, index):
        names = []
        while True:
            names.append(document['nodes'][index].get('name'))
            if index not in parents:
                return names
            index = parents[index]

    for name,folder,expected_sha in CLIP_SOURCES:
        path = HERE / 'tripo-out' / folder / 'model.glb'
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise ValueError('approved animation source hash changed: ' + name)
        source, source_binary = read_glb(path)
        if len(source.get('animations', [])) != 1:
            raise ValueError('expected one source clip: ' + name)
        source_nodes = {node.get('name'): index for index,node in enumerate(source['nodes'])}
        source_parents = {child: index for index,node in enumerate(source['nodes'])
                          for child in node.get('children', [])}
        source_joints = {source['nodes'][index]['name'] for index in source['skins'][0]['joints']}
        if source_joints != joint_names:
            raise ValueError('animation skeleton names differ: ' + name)
        maximum_rest_difference = 0.0
        for joint_name in joint_names:
            source_index, reference_index = source_nodes[joint_name], reference_nodes[joint_name]
            if parent_chain(source,source_parents,source_index) != parent_chain(reference,reference_parents,reference_index):
                raise ValueError('animation joint parent chain differs: ' + joint_name)
            a = local_matrix(source['nodes'][source_index])
            b = local_matrix(reference['nodes'][reference_index])
            maximum_rest_difference = max(maximum_rest_difference,
                                          max(abs(a[row][column]-b[row][column])
                                              for row in range(4) for column in range(4)))
        if maximum_rest_difference > .0001:
            raise ValueError('animation rest frame differs: ' + name)

        copied = {}

        def copy_accessor(index):
            if index not in copied:
                values = accessor_bytes(source, source_binary, index)
                packed.extend(b'\0' * (-len(packed) % 4))
                view_index = len(doc['bufferViews'])
                doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(packed), 'byteLength': len(values)})
                packed.extend(values)
                accessor = copy.deepcopy(source['accessors'][index])
                accessor['bufferView'], accessor['byteOffset'] = view_index, 0
                copied[index] = len(doc['accessors'])
                doc['accessors'].append(accessor)
            return copied[index]

        original = source['animations'][0]
        animation = copy.deepcopy(original)
        animation['name'] = name
        times = []
        for sampler in animation['samplers']:
            times.extend(value[0] for value in struct.iter_unpack('<f', accessor_bytes(source,source_binary,sampler['input'])))
            sampler['input'] = copy_accessor(sampler['input'])
            sampler['output'] = copy_accessor(sampler['output'])
        for channel in animation['channels']:
            target = channel['target']
            joint_name = source['nodes'][target['node']]['name']
            if joint_name not in joint_names or target['path'] not in {'translation','rotation','scale'}:
                raise ValueError('unexpected animation target: ' + joint_name)
            target['node'] = target_nodes[joint_name]
        signature = animation_signature(source,source_binary,original)
        if animation_signature(doc,packed,animation) != signature:
            raise AssertionError('animation semantics changed: ' + name)
        doc['animations'].append(animation)
        records.append({'name':name,'source_glb':str(path.relative_to(HERE)),
                        'source_sha256':expected_sha,'channels':len(animation['channels']),
                        'keyframe_time_range_seconds':[min(times),max(times)],
                        'interpolation_modes':sorted({s.get('interpolation','LINEAR') for s in animation['samplers']}),
                        'keyframe_semantics_sha256':signature,
                        'max_default_local_matrix_difference':maximum_rest_difference})
    doc['buffers'][0]['byteLength'] = len(packed)
    return bytes(packed), records


def append_dao(doc, binary, hand, mount):
    """Bake the dao into body bind space and rigidly skin it to R_Hand."""
    dao, original_binary = read_glb(DAO_SOURCE)
    if dao.get('skins') or dao.get('animations') or dao.get('extensionsRequired'):
        raise ValueError('dao source contract changed')
    skin = doc['skins'][0]
    palette = skin['joints'].index(hand)
    if palette > 255:
        raise ValueError('joint palette no longer fits the supplied byte format')
    bind_accessor = doc['accessors'][skin['inverseBindMatrices']]
    bind_view = doc['bufferViews'][bind_accessor['bufferView']]
    if bind_accessor['componentType'] != 5126 or bind_accessor['type'] != 'MAT4':
        raise ValueError('expected FLOAT inverse bind matrices')
    offset = bind_view.get('byteOffset',0) + bind_accessor.get('byteOffset',0)
    offset += palette * bind_view.get('byteStride',64)
    inverse_bind = local_matrix({'matrix':struct.unpack_from('<16f',binary,offset)})
    hand_bind = inverse_bind.inverted()
    source_grip = next(node['translation'] for node in dao['nodes'] if node.get('name') == 'Grip')
    grip_shift = Matrix.Translation(-Vector(source_grip))
    packed_dao = bytearray(original_binary)
    baked = set()
    owners = {}
    weight_streams = {}
    primitives = []
    primitive_sources = []

    def bake_attribute(index, matrix, normal):
        if index in baked:
            return
        accessor = dao['accessors'][index]
        if accessor['componentType'] != 5126 or accessor['type'] != 'VEC3':
            raise ValueError('expected FLOAT dao position/normal')
        view = dao['bufferViews'][accessor['bufferView']]
        begin = view.get('byteOffset',0) + accessor.get('byteOffset',0)
        stride = view.get('byteStride',12)
        transformed = []
        for number,values in enumerate(struct.iter_unpack('<3f',accessor_bytes(dao,original_binary,index))):
            point = matrix @ Vector(values)
            if normal:
                point.normalize()
            transformed.append(point)
            struct.pack_into('<3f',packed_dao,begin+number*stride,*point)
        accessor['min'] = [min(v[axis] for v in transformed) for axis in range(3)]
        accessor['max'] = [max(v[axis] for v in transformed) for axis in range(3)]
        baked.add(index)

    def add_attribute(values, component, kind, count):
        packed_dao.extend(b'\0' * (-len(packed_dao) % 4))
        view_index = len(dao['bufferViews'])
        dao['bufferViews'].append({'buffer':0,'byteOffset':len(packed_dao),
                                   'byteLength':len(values),'target':34962})
        packed_dao.extend(values)
        index = len(dao['accessors'])
        dao['accessors'].append({'bufferView':view_index,'componentType':component,
                                 'count':count,'type':kind})
        return index

    for node_index,node in enumerate(dao['nodes']):
        if 'mesh' not in node:
            continue
        transform = hand_bind @ mount @ grip_shift @ world_matrix(dao['nodes'],node_index)
        normal_transform = transform.to_3x3().inverted().transposed()
        source_mesh = dao['meshes'][node['mesh']]
        for primitive_index,primitive in enumerate(source_mesh['primitives']):
            attributes = primitive['attributes']
            if 'TANGENT' in attributes or 'JOINTS_0' in attributes or 'WEIGHTS_0' in attributes:
                raise ValueError('dao attribute contract changed')
            for attribute in ('POSITION','NORMAL'):
                index = attributes[attribute]
                if index in owners and owners[index] != node_index:
                    raise ValueError('dao accessor is instanced under distinct transforms')
                owners[index] = node_index
            position_index = attributes['POSITION']
            bake_attribute(position_index,transform,False)
            bake_attribute(attributes['NORMAL'],normal_transform,True)
            if position_index not in weight_streams:
                count = dao['accessors'][position_index]['count']
                joints = add_attribute(bytes((palette,0,0,0))*count,5121,'VEC4',count)
                weights = add_attribute(struct.pack('<4f',1,0,0,0)*count,5126,'VEC4',count)
                weight_streams[position_index] = (joints,weights)
            primitive = copy.deepcopy(primitive)
            primitive['attributes']['JOINTS_0'],primitive['attributes']['WEIGHTS_0'] = weight_streams[position_index]
            primitives.append(primitive)
            primitive_sources.append({'source_node':node['name'],'source_mesh':node['mesh'],
                                      'source_primitive':primitive_index})

    keys = ('bufferViews','accessors','samplers','images','textures','materials')
    offsets = {key:len(doc.get(key,[])) for key in keys}
    for view in dao['bufferViews']:
        view['byteOffset'] = view.get('byteOffset',0) + len(binary)
    for accessor in dao['accessors']:
        accessor['bufferView'] += offsets['bufferViews']
    for image in dao['images']:
        image['bufferView'] += offsets['bufferViews']
    for texture in dao['textures']:
        texture['source'] += offsets['images']
        if 'sampler' in texture:
            texture['sampler'] += offsets['samplers']
    for material in dao['materials']:
        fields = [material.get(key) for key in ('normalTexture','occlusionTexture','emissiveTexture')]
        pbr = material.get('pbrMetallicRoughness',{})
        fields += [pbr.get(key) for key in ('baseColorTexture','metallicRoughnessTexture')]
        for field in fields:
            if field is not None:
                field['index'] += offsets['textures']
    mesh_node = next(node for node in doc['nodes'] if 'mesh' in node)
    body_mesh = doc['meshes'][mesh_node['mesh']]
    body_indices = list(range(len(body_mesh['primitives'])))
    for primitive,record in zip(primitives,primitive_sources):
        primitive['indices'] += offsets['accessors']
        primitive['material'] += offsets['materials']
        primitive['attributes'] = {key:value+offsets['accessors'] for key,value in primitive['attributes'].items()}
        record['target_primitive'] = len(body_mesh['primitives'])
        body_mesh['primitives'].append(primitive)
    weapon_indices = [item['target_primitive'] for item in primitive_sources]
    body_mesh.setdefault('extras',{}).update({'body_primitive_indices':body_indices,
                                            'weapon_primitive_indices':weapon_indices})
    for key in keys:
        doc.setdefault(key,[]).extend(dao.get(key,[]))
    used = sorted(set(doc.get('extensionsUsed',[])) | set(dao.get('extensionsUsed',[])))
    if used:
        doc['extensionsUsed'] = used

    # These empty nodes are authoring anchors. Rendered dao geometry lives
    # exclusively in the shared skinned mesh, not under this entity subtree.
    anchor_index = len(doc['nodes'])
    doc['nodes'].append({'name':'Weapon_Root','translation':[-v for v in source_grip],'children':[]})
    for name in ('Grip','Blade_Base','Blade_Tip'):
        marker = copy.deepcopy(next(node for node in dao['nodes'] if node.get('name') == name))
        doc['nodes'][anchor_index]['children'].append(len(doc['nodes']))
        doc['nodes'].append(marker)
    combined = binary + bytes(packed_dao)
    doc['buffers'][0]['byteLength'] = len(combined)
    return combined,anchor_index,{'method':'same-skin rigid vertices','skin':0,
                                 'joint_name':'R_Hand','joint_palette_index':palette,
                                 'body_primitive_indices':body_indices,
                                 'weapon_primitive_indices':weapon_indices,
                                 'primitive_sources':primitive_sources}


def main():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('approved source hash changed')
    source, binary = read_glb(SOURCE)
    if len(source.get('skins', [])) != 1 or len(source['skins'][0]['joints']) != 78:
        raise ValueError('source skeleton differs from the reviewed 78-joint rig')
    if source.get('animations'):
        raise ValueError('source animation contract changed')
    doc = copy.deepcopy(source)
    mesh_node = next(index for index,node in enumerate(doc['nodes']) if 'mesh' in node)
    mesh = doc['meshes'][doc['nodes'][mesh_node]['mesh']]
    position = doc['accessors'][mesh['primitives'][0]['attributes']['POSITION']]
    low,high = Vector(position['min']),Vector(position['max'])
    if local_matrix(doc['nodes'][mesh_node]) != Matrix.Identity(4):
        raise ValueError('mesh transform requires a fresh source inspection')
    scale = HEIGHT/(high.y-low.y)
    centre = Vector(((low.x+high.x)/2, low.y, (low.z+high.z)/2))
    rotation = Matrix.Rotation(-math.pi/2, 4, 'Y')
    normalization = Matrix.Scale(scale, 4) @ rotation @ Matrix.Translation(-centre)
    original_roots = doc['scenes'][doc.get('scene',0)]['nodes']
    doc['nodes'][mesh_node]['name'] = 'TripoBody_Mesh'
    body_index = len(doc['nodes'])
    doc['nodes'].append({'name':'TripoBody_Root','matrix':matrix_values(normalization),
                         'children':original_roots})
    root_index = len(doc['nodes'])
    doc['nodes'].append({'name':'TripoWarrior_Root','children':[body_index]})
    doc['scenes'] = [{'name':'TripoWarrior','nodes':[root_index]}]
    doc['scene'] = 0
    for key in ('meshes','accessors','bufferViews','materials','images','textures','skins'):
        assert doc.get(key) == source.get(key), key
    source_binary = binary
    binary, animation_records = append_animations(doc,binary,source)
    assert binary[:len(source_binary)] == source_binary
    body_path = HERE/'tripo_warrior_rigged.glb'
    body_bytes = encode_glb(doc,binary)
    body_output = output_info(body_path,body_bytes)
    hand = next(index for index,node in enumerate(source['nodes']) if node.get('name') == 'R_Hand')
    hand_world = normalization @ world_matrix(source['nodes'],hand)
    location,quaternion,_ = local_matrix({'matrix':GRIP_LOCAL_FRAME}).decompose()
    quaternion.normalize()
    oriented_world = hand_world @ Matrix.LocRotScale(None,quaternion,None)
    compensation = Vector(tuple(1/value for value in oriented_world.to_scale()))
    mount = Matrix.LocRotScale(location,quaternion,compensation)
    target = (hand_world @ mount).translation
    source_target = world_matrix(source['nodes'],hand) @ location
    combined,weapon_index,weapon_binding = append_dao(doc,binary,hand,mount)
    grip_index = len(doc['nodes'])
    doc['nodes'].append({'name':'HandGrip_R','matrix':matrix_values(mount),'children':[weapon_index]})
    doc['nodes'][hand].setdefault('children',[]).append(grip_index)
    assert doc['skins'] == source['skins']
    assert combined[:len(binary)] == binary
    for joint in source['skins'][0]['joints']:
        for key in ('translation','rotation','scale','matrix'):
            assert doc['nodes'][joint].get(key) == source['nodes'][joint].get(key), (joint,key)
    weapon_path = HERE/'tripo_warrior_rigged_with_dao.glb'
    weapon_bytes = encode_glb(doc,combined)
    weapon_output = output_info(weapon_path,weapon_bytes)
    record = {'source_glb':str(SOURCE.relative_to(HERE)),'source_sha256':SOURCE_SHA,
              'body_height_metres':HEIGHT,'source_forward':'+X','prepared_forward':'+Z',
              'rotation_y_degrees':-90,'uniform_scale':scale,'normalization_matrix_gltf':matrix_values(normalization),
              'source_triangles':sum(source['accessors'][p['indices']]['count']//3 for p in source['meshes'][0]['primitives']),
              'source_vertices':position['count'],'joint_count':len(source['skins'][0]['joints']),
              'animation_count':len(doc['animations']),'animations':animation_records,
              'body_bounds_node':'TripoBody_Mesh','body_subtree':'TripoBody_Root',
              'body_bounds_scope':'primitive0 only, full rendered mesh also contains dao',
              'body_primitive_indices':weapon_binding['body_primitive_indices'],
              'body_bind_bounds_gltf_metres':{'min':[min((normalization@Vector((x,y,z)))[i] for x in (low.x,high.x) for y in (low.y,high.y) for z in (low.z,high.z)) for i in range(3)],
                                            'max':[max((normalization@Vector((x,y,z)))[i] for x in (low.x,high.x) for y in (low.y,high.y) for z in (low.z,high.z)) for i in range(3)]},
              'weapon_subtree':'Weapon_Root','grip_node':'HandGrip_R','grip_parent':'R_Hand',
              'grip_local_matrix_gltf':matrix_values(mount),'grip_world_metres':list(target),
              'grip_pose':'fixed conservative curled-hand calibration B',
              'grip_source_metres':list(source_target),'weapon_binding':weapon_binding,
              'anchor_nodes_role':'bind/source anchors; SDK dynamic markers require joint-pose support',
              'weapon_bind_forward_vector_gltf':list(((hand_world@mount).to_3x3()@Vector((0,1,0))).normalized()),
              'weapon_world_scale':1.0,
              'source_binary_sha256':hashlib.sha256(source_binary).hexdigest(),
              'outputs':[body_output,weapon_output]}
    alignment_bytes = (json.dumps(record,indent=2)+'\n').encode('utf-8')
    publish_outputs(((body_path,body_bytes), (weapon_path,weapon_bytes),
                     (HERE/'rigged_alignment.json',alignment_bytes)))
    print('PREPARED',json.dumps(record))


if __name__ == '__main__':
    main()
