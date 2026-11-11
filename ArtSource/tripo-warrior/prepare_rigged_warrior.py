"""Prepare the approved CLI rig in a common scene frame, preserving skin data.

Run with Blender 4.5 Python. Source mesh, weights, inverse binds and texture
bytes stay in place. The added parent frame transforms mesh and joints
uniformly, as specified by glTF scene/skin transform rules.
"""

import bisect
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


def append_animations(doc, binary, reference, clip_sources=None):
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

    if clip_sources is None:
        clip_sources = [(name, HERE / 'tripo-out' / folder / 'model.glb', digest)
                        for name, folder, digest in CLIP_SOURCES]
    names = [name for name, path, digest in clip_sources]
    if not names or len(names) != len(set(names)):
        raise ValueError('animation names must be nonempty and unique')
    for name,path,expected_sha in clip_sources:
        path = Path(path)
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


def sample_track(track, time, rotation):
    times, values, interpolation = track
    after = bisect.bisect_right(times, time)
    if after == 0:
        return values[0]
    if after == len(times) or interpolation == 'STEP':
        return values[after - 1]
    before = after - 1
    amount = (time - times[before]) / (times[after] - times[before])
    start, end = values[before], values[after]
    if rotation:
        a = Quaternion((start[3], *start[:3]))
        b = Quaternion((end[3], *end[:3]))
        a.normalize()
        b.normalize()
        result = a.slerp(b, amount)
        return (result.x, result.y, result.z, result.w)
    return tuple(a + (b - a) * amount for a, b in zip(start, end))


def apply_finger_rotation_offsets(doc, binary, offsets):
    """Apply reviewed local X/Z offsets once to freshly merged finger tracks."""
    if not offsets:
        return binary, None
    joint_nodes = {doc['nodes'][index]['name']: index for index in doc['skins'][0]['joints']}
    finger_names = {side + finger + str(segment)
                    for side in ('L_', 'R_')
                    for finger in ('Thumb', 'Index', 'Mid', 'Ring', 'Pinky')
                    for segment in (1, 2, 3)}
    rotations = {}
    for name, angles in offsets.items():
        if name not in finger_names or name not in joint_nodes:
            raise ValueError('finger calibration targets an unavailable finger joint: ' + name)
        if set(angles) != {'x_degrees', 'z_degrees'}:
            raise ValueError('finger calibration requires local X/Z angles: ' + name)
        x, z = angles['x_degrees'], angles['z_degrees']
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool)
                   and math.isfinite(value) for value in (x, z)):
            raise ValueError('finger calibration angles must be finite numbers: ' + name)
        rotations[joint_nodes[name]] = (
            name, Quaternion((1, 0, 0), math.radians(x)) @ Quaternion((0, 0, 1), math.radians(z)))

    packed = bytearray(binary)
    clips = []
    for animation in doc['animations']:
        references = {}
        for channel in animation['channels']:
            index = channel['sampler']
            references[index] = references.get(index, 0) + 1
        modified = set()
        for channel in animation['channels']:
            target = channel['target']
            if target['path'] != 'rotation' or target['node'] not in rotations:
                continue
            name, delta = rotations[target['node']]
            if name in modified:
                raise ValueError('duplicate finger rotation channel: ' + name)
            sampler_index = channel['sampler']
            sampler = animation['samplers'][sampler_index]
            if sampler.get('interpolation', 'LINEAR') not in {'LINEAR', 'STEP'}:
                raise ValueError('finger calibration requires LINEAR/STEP quaternion interpolation')
            accessor = doc['accessors'][sampler['output']]
            if accessor['componentType'] != 5126 or accessor['type'] != 'VEC4':
                raise ValueError('finger rotation output must be FLOAT VEC4')
            values = accessor_bytes(doc, binary, sampler['output'])
            output = bytearray()
            for x, y, z, w in struct.iter_unpack('<4f', values):
                if not all(math.isfinite(value) for value in (x, y, z, w)) or x*x + y*y + z*z + w*w <= 1e-12:
                    raise ValueError('finger rotation contains an invalid quaternion: ' + name)
                q = (Quaternion((w, x, y, z)) @ delta).normalized()
                output.extend(struct.pack('<4f', q.x, q.y, q.z, q.w))
            packed.extend(b'\0' * (-len(packed) % 4))
            view = len(doc['bufferViews'])
            doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(packed), 'byteLength': len(output)})
            packed.extend(output)
            output_index = len(doc['accessors'])
            doc['accessors'].append({'bufferView': view, 'componentType': 5126,
                                     'count': accessor['count'], 'type': 'VEC4'})
            # A shared sampler may also serve a different finger or an uncalibrated joint.
            if references[sampler_index] > 1:
                sampler = copy.deepcopy(sampler)
                channel['sampler'] = len(animation['samplers'])
                animation['samplers'].append(sampler)
            sampler['output'] = output_index
            modified.add(name)
        if modified != set(offsets):
            raise ValueError('clip lacks calibrated finger rotation tracks: ' + animation['name'])
        clips.append({'clip': animation['name'], 'modified_rotation_tracks': len(modified)})
    doc['buffers'][0]['byteLength'] = len(packed)
    return bytes(packed), {
        'application': 'normalize(q @ (Qx(x_degrees) @ Qz(z_degrees))) in local joint space',
        'offsets': copy.deepcopy(offsets), 'clips': clips,
        'modified_rotation_tracks': sum(row['modified_rotation_tracks'] for row in clips),
    }


def offhand_envelope_weight(time, window):
    start, rise, fall, end = window
    if time <= start or time >= end:
        return 0.0
    if time < rise:
        return .5 - .5 * math.cos(math.pi * (time - start) / (rise - start))
    if time <= fall:
        return 1.0
    return .5 + .5 * math.cos(math.pi * (time - fall) / (end - fall))


def apply_offhand_rotation_envelope(doc, binary, config):
    """Apply the reviewed sampled slash envelope after whole-clip finger offsets."""
    if not config:
        return binary, None
    window = config['window_seconds']
    if len(window) != 4 or not all(math.isfinite(value) for value in window):
        raise ValueError('offhand envelope requires four finite boundary times')
    start, rise, fall, end = window
    if not start < rise <= fall < end:
        raise ValueError('invalid offhand envelope window')
    rotations = config['rotations']
    if not rotations or not set(rotations).issubset({'L_Hand', 'L_Forearm'}):
        raise ValueError('offhand envelope is outside reviewed wrist/forearm scope')
    deltas = {}
    for name, values in rotations.items():
        axis, degrees = values['axis'], values['degrees']
        if (len(axis) != 3 or not all(math.isfinite(value) for value in [*axis, degrees]) or
                sum(value * value for value in axis) <= 1e-12):
            raise ValueError('offhand rotation requires a finite nonzero axis and angle')
        deltas[name] = Quaternion(axis, math.radians(degrees))
    animation = next((clip for clip in doc['animations'] if clip['name'] == 'slash'), None)
    if animation is None:
        raise ValueError('offhand envelope requires the native slash clip')
    packed = bytearray(binary)
    references = {}
    for channel in animation['channels']:
        index = channel['sampler']
        references[index] = references.get(index, 0) + 1

    def append_accessor(rows, kind):
        width = len(rows[0])
        packed.extend(b'\0' * (-len(packed) % 4))
        offset = len(packed)
        for row in rows:
            packed.extend(struct.pack('<' + 'f' * width, *row))
        view = len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(rows) * width * 4})
        index = len(doc['accessors'])
        value = {'bufferView': view, 'componentType': 5126, 'count': len(rows), 'type': kind}
        if kind == 'SCALAR':
            value.update(min=[rows[0][0]], max=[rows[-1][0]])
        doc['accessors'].append(value)
        return index

    changed = []
    for channel in animation['channels']:
        target = channel['target']
        name = doc['nodes'][target['node']].get('name')
        if target['path'] != 'rotation' or name not in rotations:
            continue
        if any(row['bone'] == name for row in changed):
            raise ValueError('duplicate offhand rotation channel: ' + name)
        sampler_index = channel['sampler']
        sampler = animation['samplers'][sampler_index]
        if sampler.get('interpolation', 'LINEAR') != 'LINEAR':
            raise ValueError('offhand envelope requires a LINEAR quaternion source')
        if doc['accessors'][sampler['input']]['type'] != 'SCALAR' or doc['accessors'][sampler['output']]['type'] != 'VEC4':
            raise ValueError('offhand envelope requires SCALAR times and VEC4 rotations')
        times = [row[0] for row in struct.iter_unpack('<f', accessor_bytes(doc, binary, sampler['input']))]
        rows = list(struct.iter_unpack('<4f', accessor_bytes(doc, binary, sampler['output'])))
        if (not times or len(times) != len(rows) or not all(math.isfinite(value) for value in times) or
                any(b <= a for a, b in zip(times, times[1:]))):
            raise ValueError('offhand source times must be finite and strictly increasing')
        if any(not all(math.isfinite(value) for value in row) or sum(value * value for value in row) <= 1e-12
               for row in rows):
            raise ValueError('offhand source contains an invalid quaternion')
        if start < times[0] or end > times[-1]:
            raise ValueError('offhand envelope extends beyond the source slash track')
        track = (times, rows, 'LINEAR')
        extra = [start, end, *window, 1.55, 2.117, 94 / 30, 95 / 30]
        extra += [frame / 60 for frame in range(math.floor(start * 60), math.ceil(end * 60) + 1)]
        extra += [start + (rise - start) * value for value in (.25, .5, .75)]
        sampled = [*times, *[time for time in extra if start <= time <= end]]
        output_times = sorted({struct.unpack('<f', struct.pack('<f', time))[0] for time in sampled
                               if times[0] <= time <= times[-1]})
        output_rows = []
        for time in output_times:
            x, y, z, w = sample_track(track, time, True)
            correction = Quaternion((1, 0, 0, 0)).slerp(deltas[name], offhand_envelope_weight(time, window))
            q = (Quaternion((w, x, y, z)) @ correction).normalized()
            row = (q.x, q.y, q.z, q.w)
            if output_rows and sum(a * b for a, b in zip(output_rows[-1], row)) < 0:
                row = tuple(-value for value in row)
            output_rows.append(row)
        if references[sampler_index] > 1:
            sampler = copy.deepcopy(sampler)
            channel['sampler'] = len(animation['samplers'])
            animation['samplers'].append(sampler)
        sampler['input'] = append_accessor([(time,) for time in output_times], 'SCALAR')
        sampler['output'] = append_accessor(output_rows, 'VEC4')
        changed.append({'bone': name, 'source_key_count': len(times), 'candidate_key_count': len(output_times),
                        'source_range_seconds': [times[0], times[-1]]})
    if {row['bone'] for row in changed} != set(rotations):
        raise ValueError('a reviewed offhand rotation track is absent')
    doc['buffers'][0]['byteLength'] = len(packed)
    return bytes(packed), {
        'clip': 'slash', 'application': 'normalize(q(t) @ slerp(identity, local_axis_angle, raised_cosine(t)))',
        'window_seconds': list(window), 'rotations': copy.deepcopy(rotations), 'sample_rate_hz': 60,
        'interpolation': 'LINEAR', 'changed_tracks': changed,
    }


def append_dao(doc, binary, hand, mount, source_path=None, source_sha=None):
    """Bake the dao into body bind space and rigidly skin it to R_Hand."""
    source_path = Path(source_path) if source_path is not None else DAO_SOURCE
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_sha is not None and digest != source_sha:
        raise ValueError('approved dao source hash changed')
    dao, original_binary = read_glb(source_path)
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
            normal_texture = dao['materials'][primitive['material']].get('normalTexture')
            if normal_texture is not None:
                uv = 'TEXCOORD_' + str(normal_texture.get('texCoord', 0))
                if 'NORMAL' not in attributes or uv not in attributes:
                    raise ValueError('normal-mapped dao primitive lacks its normal/UV basis')
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
                                 'source_glb':os.path.relpath(source_path, HERE),'source_sha256':digest,
                                 'joint_name':doc['nodes'][hand]['name'],'joint_palette_index':palette,
                                 'body_primitive_indices':body_indices,
                                 'weapon_primitive_indices':weapon_indices,
                                 'primitive_sources':primitive_sources}


def normalization_frame(source, height):
    """Fit the complete skinned body to a metre-scale, feet-at-zero scene frame."""
    mesh_nodes = [index for index, node in enumerate(source['nodes']) if 'mesh' in node]
    if len(mesh_nodes) != 1:
        raise ValueError('expected one skinned body mesh node')
    mesh_node = mesh_nodes[0]
    if source['nodes'][mesh_node].get('skin') != 0:
        raise ValueError('body mesh must use the supplied skin')
    mesh = source['meshes'][source['nodes'][mesh_node]['mesh']]
    transform = world_matrix(source['nodes'], mesh_node)
    corners = []
    for primitive in mesh['primitives']:
        accessor = source['accessors'][primitive['attributes']['POSITION']]
        for x in (accessor['min'][0], accessor['max'][0]):
            for y in (accessor['min'][1], accessor['max'][1]):
                for z in (accessor['min'][2], accessor['max'][2]):
                    corners.append(transform @ Vector((x, y, z)))
    low = Vector(tuple(min(point[axis] for point in corners) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in corners) for axis in range(3)))
    if not math.isfinite(height) or height <= 0 or high.y <= low.y:
        raise ValueError('body height must be finite and positive')
    scale = height / (high.y - low.y)
    centre = Vector(((low.x + high.x) / 2, low.y, (low.z + high.z) / 2))
    normalization = (Matrix.Scale(scale, 4) @ Matrix.Rotation(-math.pi / 2, 4, 'Y')
                     @ Matrix.Translation(-centre))
    return normalization, scale, low, high, mesh_node


def calibrated_mount(source, normalization, hand):
    """Transfer the reviewed metre-scale wrist-to-grip frame to this rig's rest axes."""
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('reviewed grip reference source hash changed')
    reference, _ = read_glb(SOURCE)
    reference_frame, _, _, _, _ = normalization_frame(reference, HEIGHT)
    reference_hand = next(index for index, node in enumerate(reference['nodes'])
                          if node.get('name') == 'R_Hand')
    wrist_frame = reference_frame @ world_matrix(reference['nodes'], reference_hand)
    location, rotation, _ = local_matrix({'matrix': GRIP_LOCAL_FRAME}).decompose()
    rotation.normalize()
    oriented = wrist_frame @ Matrix.LocRotScale(None, rotation, None)
    compensation = Vector(tuple(1 / value for value in oriented.to_scale()))
    reference_grip = wrist_frame @ Matrix.LocRotScale(location, rotation, compensation)
    wrist_offset = reference_grip.translation - wrist_frame.translation
    target_wrist = normalization @ world_matrix(source['nodes'], hand)
    target_grip = Matrix.LocRotScale(target_wrist.translation + wrist_offset,
                                    reference_grip.to_quaternion(), Vector((1, 1, 1)))
    return target_wrist.inverted() @ target_grip


def prepare_character(source_path, source_sha, clip_sources, body_path, weapon_path,
                      alignment_path, height=HEIGHT, grip_frame=None, finger_rotation_offsets=None,
                      attack_grounding_clips=None, weapon_source=None):
    """Publish a body, its same-skin dao variant and their shared asset metadata."""
    source_path = Path(source_path)
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_sha:
        raise ValueError('approved source hash changed')
    source, binary = read_glb(source_path)
    if len(source.get('skins', [])) != 1 or not source['skins'][0]['joints']:
        raise ValueError('expected one nonempty character skin')
    joint_names = [source['nodes'][index].get('name') for index in source['skins'][0]['joints']]
    if None in joint_names or len(set(joint_names)) != len(joint_names):
        raise ValueError('skin joint names must be present and unique')
    if 'R_Hand' not in joint_names:
        raise ValueError('character has no R_Hand weapon joint')
    if source.get('animations'):
        raise ValueError('source animation contract changed')
    doc = copy.deepcopy(source)
    normalization, scale, low, high, mesh_node = normalization_frame(source, height)
    source_mesh = source['meshes'][source['nodes'][mesh_node]['mesh']]
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
    binary, animation_records = append_animations(doc,binary,source,clip_sources)
    binary, finger_calibration = apply_finger_rotation_offsets(doc, binary, finger_rotation_offsets)
    grounding = None
    if attack_grounding_clips is not None:
        from attack_grounding import ground_attack_feet
        binary, grounding = ground_attack_feet(doc, binary, attack_grounding_clips)
    if finger_calibration is not None or grounding is not None:
        for animation, record in zip(doc['animations'], animation_records):
            record['source_keyframe_semantics_sha256'] = record['keyframe_semantics_sha256']
            record['keyframe_semantics_sha256'] = animation_signature(doc, binary, animation)
    assert binary[:len(source_binary)] == source_binary
    body_path, weapon_path, alignment_path = Path(body_path), Path(weapon_path), Path(alignment_path)
    body_bytes = encode_glb(doc,binary)
    body_output = output_info(body_path,body_bytes)
    hand = next(index for index,node in enumerate(source['nodes']) if node.get('name') == 'R_Hand')
    hand_world = normalization @ world_matrix(source['nodes'],hand)
    if grip_frame is None:
        mount = calibrated_mount(source, normalization, hand)
    else:
        location,quaternion,_ = local_matrix({'matrix':grip_frame}).decompose()
        quaternion.normalize()
        oriented_world = hand_world @ Matrix.LocRotScale(None,quaternion,None)
        compensation = Vector(tuple(1/value for value in oriented_world.to_scale()))
        mount = Matrix.LocRotScale(location,quaternion,compensation)
    location = mount.translation
    target = (hand_world @ mount).translation
    source_target = world_matrix(source['nodes'],hand) @ location
    dao_arguments = {} if weapon_source is None else {
        'source_path': HERE / weapon_source['source'], 'source_sha': weapon_source['source_sha256']}
    combined,weapon_index,weapon_binding = append_dao(doc,binary,hand,mount,**dao_arguments)
    grip_index = len(doc['nodes'])
    doc['nodes'].append({'name':'HandGrip_R','matrix':matrix_values(mount),'children':[weapon_index]})
    doc['nodes'][hand].setdefault('children',[]).append(grip_index)
    assert doc['skins'] == source['skins']
    assert combined[:len(binary)] == binary
    for joint in source['skins'][0]['joints']:
        for key in ('translation','rotation','scale','matrix'):
            assert doc['nodes'][joint].get(key) == source['nodes'][joint].get(key), (joint,key)
    weapon_bytes = encode_glb(doc,combined)
    weapon_output = output_info(weapon_path,weapon_bytes)
    record = {'source_glb':str(source_path.relative_to(HERE)),'source_sha256':source_sha,
              'body_height_metres':height,'source_forward':'+X','prepared_forward':'+Z',
              'rotation_y_degrees':-90,'uniform_scale':scale,'normalization_matrix_gltf':matrix_values(normalization),
              'source_triangles':sum(source['accessors'][p['indices']]['count']//3 for p in source_mesh['primitives']),
              'source_vertices':sum(source['accessors'][index]['count'] for index in
                                    {primitive['attributes']['POSITION'] for primitive in source_mesh['primitives']}),
              'joint_count':len(source['skins'][0]['joints']),
              'animation_count':len(doc['animations']),'animations':animation_records,
              'body_bounds_node':'TripoBody_Mesh','body_subtree':'TripoBody_Root',
              'body_bounds_scope':'all body primitives before same-skin dao',
              'body_primitive_indices':weapon_binding['body_primitive_indices'],
              'body_bind_bounds_gltf_metres':{'min':[min((normalization@Vector((x,y,z)))[i] for x in (low.x,high.x) for y in (low.y,high.y) for z in (low.z,high.z)) for i in range(3)],
                                            'max':[max((normalization@Vector((x,y,z)))[i] for x in (low.x,high.x) for y in (low.y,high.y) for z in (low.z,high.z)) for i in range(3)]},
              'weapon_subtree':'Weapon_Root','grip_node':'HandGrip_R','grip_parent':'R_Hand',
              'grip_local_matrix_gltf':matrix_values(mount),'grip_world_metres':list(target),
              'grip_pose':'reviewed curled-hand frame transferred through normalized wrist rest frame' if grip_frame is None else 'per-character reviewed grip-frame calibration',
              'grip_source_metres':list(source_target),'weapon_binding':weapon_binding,
              'anchor_nodes_role':'bind/source anchors; SDK dynamic markers require joint-pose support',
              'weapon_bind_forward_vector_gltf':list(((hand_world@mount).to_3x3()@Vector((0,1,0))).normalized()),
              'weapon_world_scale':1.0,
              'source_binary_sha256':hashlib.sha256(source_binary).hexdigest(),
              'outputs':[body_output,weapon_output]}
    if finger_calibration is not None:
        record['finger_rotation_calibration'] = finger_calibration
    if grounding is not None:
        record['attack_root_grounding'] = grounding
    alignment_bytes = (json.dumps(record,indent=2)+'\n').encode('utf-8')
    publish_outputs(((body_path,body_bytes), (weapon_path,weapon_bytes),
                     (alignment_path,alignment_bytes)))
    return record


def main():
    record = prepare_character(SOURCE, SOURCE_SHA, None,
                               HERE / 'tripo_warrior_rigged.glb',
                               HERE / 'tripo_warrior_rigged_with_dao.glb',
                               HERE / 'rigged_alignment.json', grip_frame=GRIP_LOCAL_FRAME)
    print('PREPARED', json.dumps(record))


if __name__ == '__main__':
    main()
