"""Build the runtime character library from local, hash-pinned Tripo sources.

Run with Blender Python after the CLI downloads have completed. The motion
source may use a different biped rest frame. Body rotations are transferred
through world-space rest deltas, while each target keeps its own geometry,
bone lengths, weights, inverse binds and sampled native grip pose.
"""

import argparse
import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prepare_rigged_warrior import (
    HERE,
    accessor_bytes,
    encode_glb,
    local_matrix,
    normalization_frame,
    prepare_character,
    publish_outputs,
    read_glb,
    sample_track,
    world_matrix,
)


def pinned_source(entry):
    path = HERE / entry['source']
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != entry['source_sha256']:
        raise ValueError('source hash differs from manifest: ' + str(path))
    return path, *read_glb(path)


def joint_nodes(document):
    if len(document.get('skins', [])) != 1:
        raise ValueError('expected exactly one character skin')
    joints = document['skins'][0]['joints']
    names = {document['nodes'][index].get('name'): index for index in joints}
    if None in names or len(names) != len(joints):
        raise ValueError('character joints require unique names')
    return names


def node_order(document):
    parents = {child: parent for parent, node in enumerate(document['nodes'])
               for child in node.get('children', [])}
    order = []
    visiting = set()
    visited = set()

    def visit(index):
        if index in visiting:
            raise ValueError('cyclic character hierarchy')
        if index in visited:
            return
        visiting.add(index)
        if index in parents:
            visit(parents[index])
        visiting.remove(index)
        visited.add(index)
        order.append(index)

    for index in range(len(document['nodes'])):
        visit(index)
    return parents, order


def decode_animation(document, binary):
    if len(document.get('animations', [])) != 1:
        raise ValueError('expected exactly one source animation')
    animation = document['animations'][0]
    tracks = {}
    timeline = set()
    for channel in animation['channels']:
        target = channel['target']
        path = target['path']
        if path not in {'translation', 'rotation', 'scale'}:
            raise ValueError('unsupported biped animation channel: ' + path)
        sampler = animation['samplers'][channel['sampler']]
        interpolation = sampler.get('interpolation', 'LINEAR')
        if interpolation not in {'LINEAR', 'STEP'}:
            raise ValueError('source interpolation requires a dedicated retarget path: ' + interpolation)
        times = [value[0] for value in struct.iter_unpack(
            '<f', accessor_bytes(document, binary, sampler['input']))]
        width = 4 if path == 'rotation' else 3
        values = list(struct.iter_unpack('<' + 'f' * width,
                                       accessor_bytes(document, binary, sampler['output'])))
        if len(values) != len(times) or any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError('source animation key times must be strictly increasing')
        if not all(math.isfinite(value) for row in values for value in row):
            raise ValueError('source animation contains non-finite values')
        tracks[(target['node'], path)] = (times, values, interpolation)
        timeline.update(times)
    if not timeline or not all(math.isfinite(time) and time >= 0 for time in timeline):
        raise ValueError('source animation has no finite nonnegative timeline')
    return tracks, sorted(timeline)


def sampled_local(node, index, tracks, time):
    location, rotation, scale = local_matrix(node).decompose()
    translation_track = tracks.get((index, 'translation'))
    rotation_track = tracks.get((index, 'rotation'))
    scale_track = tracks.get((index, 'scale'))
    if translation_track is not None:
        location = Vector(sample_track(translation_track, time, False))
    if rotation_track is not None:
        x, y, z, w = sample_track(rotation_track, time, True)
        rotation = Quaternion((w, x, y, z))
    if scale_track is not None:
        scale = Vector(sample_track(scale_track, time, False))
    return Matrix.LocRotScale(location, rotation, scale)


def require_same_rest(source, reference):
    source_joints = joint_nodes(source)
    reference_joints = joint_nodes(reference)
    if source_joints.keys() != reference_joints.keys():
        raise ValueError('motion or grip source differs from its declared rig')
    source_parents, _ = node_order(source)
    reference_parents, _ = node_order(reference)
    for name, index in source_joints.items():
        other = reference_joints[name]
        a = local_matrix(source['nodes'][index])
        b = local_matrix(reference['nodes'][other])
        difference = max(abs(a[row][column] - b[row][column])
                         for row in range(4) for column in range(4))
        parent = source_parents.get(index)
        other_parent = reference_parents.get(other)
        parent_name = source['nodes'][parent].get('name') if parent is not None else None
        other_parent_name = reference['nodes'][other_parent].get('name') if other_parent is not None else None
        if difference > 0.0001 or parent_name != other_parent_name:
            raise ValueError('motion or grip rest frame differs at ' + name)


def fixed_grip_pose(target, grip, binary, time):
    require_same_rest(grip, target)
    tracks, _ = decode_animation(grip, binary)
    pose = {}
    for name, index in joint_nodes(grip).items():
        if name.startswith(('L_Thumb', 'L_Index', 'L_Mid', 'L_Ring', 'L_Pinky',
                            'R_Thumb', 'R_Index', 'R_Mid', 'R_Ring', 'R_Pinky')):
            pose[name] = sampled_local(grip['nodes'][index], index, tracks, time)
    if len(pose) != 30:
        raise ValueError('native grip requires all 30 target finger joints')
    return pose


def retarget_clip(source, source_binary, motion_rig, target, target_binary, grip_pose, name):
    require_same_rest(source, motion_rig)
    source_joints = joint_nodes(source)
    target_joints = joint_nodes(target)
    if len(target_joints) != 78 or 'BoneRoot' not in target_joints:
        raise ValueError('runtime retarget requires the target 78-joint Tripo rig')
    mapping = {node: source_joints[joint_name] for joint_name, node in target_joints.items()
               if joint_name in source_joints}
    mapping[target_joints['BoneRoot']] = source_joints['Root']
    if len(mapping) != 41:
        raise ValueError('expected the complete 41-joint source body mapping')
    source_parents, source_order = node_order(source)
    target_parents, target_order = node_order(target)
    source_bind = {index: world_matrix(source['nodes'], index) for index in source_joints.values()}
    target_bind = {index: world_matrix(target['nodes'], index) for index in target_joints.values()}
    source_bind_rotations = {index: value.to_quaternion().normalized() for index, value in source_bind.items()}
    target_bind_rotations = {index: value.to_quaternion().normalized() for index, value in target_bind.items()}
    target_locals = {index: local_matrix(node).decompose() for index, node in enumerate(target['nodes'])}
    _, source_scale, _, _, _ = normalization_frame(motion_rig, 1.78)
    _, target_scale, _, _, _ = normalization_frame(target, 1.78)
    translation_scale = source_scale / target_scale
    tracks, timeline = decode_animation(source, source_binary)
    curves = {index: {'translation': [], 'rotation': [], 'scale': []} for index in target_joints.values()}
    shared_joints = {
        'L_ElbowShareBone': ('L_Upperarm', 'L_Forearm'),
        'R_ElbowShareBone': ('R_Upperarm', 'R_Forearm'),
        'L_KneeShareBone': ('L_Thigh', 'L_Calf'),
        'R_KneeShareBone': ('R_Thigh', 'R_Calf'),
    }
    maximum_rotation_step = 0.0
    for time in timeline:
        source_world = {}
        for index in source_order:
            local = sampled_local(source['nodes'][index], index, tracks, time)
            parent = source_parents.get(index)
            source_world[index] = source_world[parent] @ local if parent is not None else local
        target_world = {}
        for index in target_order:
            node = target['nodes'][index]
            parent = target_parents.get(index)
            parent_world = target_world[parent] if parent is not None else Matrix.Identity(4)
            location, rotation, scale = target_locals[index]
            location, rotation, scale = location.copy(), rotation.copy(), scale.copy()
            source_index = mapping.get(index)
            if source_index is not None:
                animated_rotation = source_world[source_index].to_quaternion().normalized()
                delta = animated_rotation @ source_bind_rotations[source_index].inverted()
                wanted_world_rotation = delta @ target_bind_rotations[index]
                rotation = parent_world.to_quaternion().inverted() @ wanted_world_rotation
                rotation.normalize()
                if node.get('name') in {'BoneRoot', 'Hip'}:
                    offset = (source_world[source_index].translation - source_bind[source_index].translation) * translation_scale
                    wanted_world_position = target_bind[index].translation + offset
                    location = parent_world.inverted() @ wanted_world_position
            elif node.get('name') in shared_joints:
                before, after = shared_joints[node['name']]
                a, b = source_joints[before], source_joints[after]
                delta_a = source_world[a].to_quaternion() @ source_bind_rotations[a].inverted()
                delta_b = source_world[b].to_quaternion() @ source_bind_rotations[b].inverted()
                delta_a.normalize()
                delta_b.normalize()
                wanted_world_rotation = delta_a.slerp(delta_b, 0.5) @ target_bind_rotations[index]
                rotation = parent_world.to_quaternion().inverted() @ wanted_world_rotation
                rotation.normalize()
            elif node.get('name') in grip_pose:
                location, rotation, scale = grip_pose[node['name']].decompose()
            local = Matrix.LocRotScale(location, rotation, scale)
            target_world[index] = parent_world @ local
            if index not in curves:
                continue
            rows = curves[index]
            if rows['rotation']:
                previous = Quaternion((rows['rotation'][-1][3], *rows['rotation'][-1][:3]))
                if previous.dot(rotation) < 0:
                    rotation.negate()
                maximum_rotation_step = max(maximum_rotation_step, previous.rotation_difference(rotation).angle)
            rows['translation'].append(tuple(location))
            rows['rotation'].append((rotation.x, rotation.y, rotation.z, rotation.w))
            rows['scale'].append(tuple(scale))
    result = copy.deepcopy(target)
    packed = bytearray(target_binary)

    def append_accessor(rows, kind):
        width = len(rows[0])
        packed.extend(b'\0' * (-len(packed) % 4))
        byte_offset = len(packed)
        for row in rows:
            packed.extend(struct.pack('<' + 'f' * width, *row))
        view = len(result['bufferViews'])
        result['bufferViews'].append({'buffer': 0, 'byteOffset': byte_offset,
                                     'byteLength': len(rows) * width * 4})
        accessor = len(result['accessors'])
        result['accessors'].append({'bufferView': view, 'componentType': 5126,
                                    'count': len(rows), 'type': kind,
                                    'min': [min(row[axis] for row in rows) for axis in range(width)],
                                    'max': [max(row[axis] for row in rows) for axis in range(width)]})
        return accessor

    time_accessor = append_accessor([(value,) for value in timeline], 'SCALAR')
    animation = {'name': name, 'samplers': [], 'channels': []}
    for index, channels in curves.items():
        for path, rows in channels.items():
            accessor = append_accessor(rows, 'VEC4' if path == 'rotation' else 'VEC3')
            sampler = len(animation['samplers'])
            animation['samplers'].append({'input': time_accessor, 'output': accessor, 'interpolation': 'LINEAR'})
            animation['channels'].append({'sampler': sampler, 'target': {'node': index, 'path': path}})
    result['animations'] = [animation]
    result['buffers'][0]['byteLength'] = len(packed)
    record = {'method': 'world-space bind-rotation delta, target local bone lengths preserved',
              'source_joints': len(source_joints), 'target_joints': len(target_joints),
              'mapped_body_joints': len(mapping), 'fixed_native_finger_joints': len(grip_pose),
              'sample_count': len(timeline), 'time_range_seconds': [timeline[0], timeline[-1]],
              'translation_scale': translation_scale,
              'maximum_quaternion_step_radians': maximum_rotation_step}
    return encode_glb(result, bytes(packed)), record


def validate_finger_calibration(character):
    offsets = character.get('finger_rotation_offsets')
    review = character.get('finger_rotation_review')
    if not offsets and not review:
        return
    if not offsets or not review:
        raise ValueError('finger offsets require their reviewed source binding: ' + character['id'])
    if (review['target_rig_sha256'] != character['source_sha256'] or
            review['target_grip_sha256'] != character['grip_source']['source_sha256'] or
            review['grip_time_seconds'] != character['grip_source'].get('time_seconds', 2.117)):
        raise ValueError('finger calibration requires review for the selected rig/grip source: ' + character['id'])
    grip_digest = hashlib.sha256(json.dumps(character.get('grip_frame'),
                                           sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if review['grip_frame_sha256'] != grip_digest:
        raise ValueError('finger calibration requires review for the selected weapon mount: ' + character['id'])
    path = HERE / review['calibration_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != review['calibration_sha256']:
        raise ValueError('reviewed finger calibration file changed')
    approved = json.loads(path.read_text())['characters']
    row = next((entry for entry in approved if entry['id'] == character['id']), None)
    if (row is None or row['local_finger_offsets'] != offsets or
            row['source_sha256'] != review['reviewed_source_asset_sha256'] or
            row['candidate_sha256'] != review['reviewed_candidate_asset_sha256']):
        raise ValueError('finger offsets differ from the reviewed candidate: ' + character['id'])


def validate_offhand_calibration(character):
    config = character.get('offhand_rotation_envelope')
    review = character.get('offhand_rotation_review')
    if not config and not review:
        return
    if not config or not review:
        raise ValueError('offhand envelope requires its reviewed source binding: ' + character['id'])
    finger_review = character.get('finger_rotation_review')
    finger_digest = hashlib.sha256(json.dumps(character.get('finger_rotation_offsets'),
                                               sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if (review['target_rig_sha256'] != character['source_sha256'] or
            review['target_grip_sha256'] != character['grip_source']['source_sha256'] or
            review['grip_time_seconds'] != character['grip_source'].get('time_seconds', 2.117) or
            not finger_review or
            review['finger_reviewed_candidate_sha256'] != finger_review['reviewed_candidate_asset_sha256'] or
            review['finger_rotation_offsets_sha256'] != finger_digest or
            review['reviewed_source_asset_sha256'] != finger_review['reviewed_candidate_asset_sha256']):
        raise ValueError('offhand envelope requires review for the selected rig/grip/finger correction: ' + character['id'])
    path = HERE / review['calibration_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != review['calibration_sha256']:
        raise ValueError('reviewed offhand calibration file changed')
    approved = json.loads(path.read_text())
    row = next((entry for entry in approved['characters'] if entry['id'] == character['id']), None)
    if (approved['sample_rate_hz'] != 60 or row is None or row['window_seconds'] != config['window_seconds'] or
            row['rotations'] != config['rotations'] or row['source_sha256'] != review['reviewed_source_asset_sha256'] or
            row['candidate_sha256'] != review['reviewed_candidate_asset_sha256']):
        raise ValueError('offhand envelope differs from the reviewed candidate: ' + character['id'])


def build_library(manifest_path):
    manifest = json.loads(manifest_path.read_text())
    characters = manifest['characters']
    if not characters or len({character['id'] for character in characters}) != len(characters):
        raise ValueError('manifest requires uniquely identified characters')
    if len({character['output'] for character in characters}) != len(characters):
        raise ValueError('characters must have distinct output files')
    for character in characters:
        validate_finger_calibration(character)
        validate_offhand_calibration(character)
    _, motion_rig, _ = pinned_source(manifest['motion_source'])
    clips = manifest['motion_source']['clips']
    clip_names = [clip['name'] for clip in clips]
    required_clips = {'idle', 'walk', 'turn', 'fall', 'hit_body', 'hit_head', 'hit_side'}
    if len(set(clip_names)) != len(clip_names) or not required_clips.issubset(clip_names):
        raise ValueError('motion library requires unique names and all locomotion/reaction clips')
    library = HERE / 'library'
    library.mkdir(exist_ok=True)
    summaries = []
    for character in characters:
        source_path, target, target_binary = pinned_source(character)
        grip_path, grip, grip_binary = pinned_source(character['grip_source'])
        grip_pose = fixed_grip_pose(target, grip, grip_binary,
                                    character['grip_source'].get('time_seconds', 2.117))
        output_name = character['output']
        if Path(output_name).name != output_name or not output_name.endswith('.glb'):
            raise ValueError('character output must be a local GLB filename')
        stem = Path(output_name).stem
        retargeted = library / (stem + '_retargeted')
        retargeted.mkdir(exist_ok=True)
        pending = []
        records = []
        packed_clips = []
        for clip in clips:
            name = clip['name']
            if name == 'slash':
                continue
            if not name or Path(name).name != name:
                raise ValueError('clip name must be a local filename stem')
            clip_path, motion, binary = pinned_source(clip)
            output, record = retarget_clip(motion, binary, motion_rig, target, target_binary, grip_pose, name)
            path = retargeted / (name + '.glb')
            digest = hashlib.sha256(output).hexdigest()
            pending.append((path, output))
            packed_clips.append((name, path, digest))
            records.append({'name': name, 'source': str(clip_path.relative_to(HERE)),
                            'source_sha256': clip['source_sha256'], 'output_sha256': digest, **record})
        # The native slash retains the authored contact and curled finger curves.
        packed_clips.append(('slash', grip_path, character['grip_source']['source_sha256']))
        publish_outputs(pending)
        record = prepare_character(source_path, character['source_sha256'], packed_clips,
                                   library / (stem + '_body.glb'), library / output_name,
                                   library / (stem + '_alignment.json'),
                                   height=character.get('height_metres', 1.78),
                                   grip_frame=character.get('grip_frame'),
                                   finger_rotation_offsets=character.get('finger_rotation_offsets'),
                                   offhand_rotation_envelope=character.get('offhand_rotation_envelope'))
        record['id'] = character['id']
        record['name'] = character['name']
        record['retargeting'] = records
        record['grip_source'] = character['grip_source']
        if character.get('finger_rotation_review'):
            record['finger_rotation_review'] = copy.deepcopy(character['finger_rotation_review'])
        if character.get('offhand_rotation_review'):
            record['offhand_rotation_review'] = copy.deepcopy(character['offhand_rotation_review'])
        metadata = (json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode()
        publish_outputs(((library / (stem + '_alignment.json'), metadata),))
        summaries.append({'id': character['id'], 'name': character['name'],
                          'output': output_name, 'animations': [row['name'] for row in record['animations']],
                          'joint_count': record['joint_count'], 'outputs': record['outputs']})
    index = (json.dumps({'characters': summaries}, ensure_ascii=False, indent=2) + '\n').encode()
    publish_outputs(((library / 'characters.json', index),))
    runtime = HERE.parent.parent / 'app/src/main/assets/models/opponents'
    runtime.mkdir(parents=True, exist_ok=True)
    publish_outputs(tuple((runtime / row['output'], (library / row['output']).read_bytes())
                          for row in summaries))
    print(json.dumps({'characters': summaries}, ensure_ascii=False))


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    options = parser.parse_args(arguments)
    build_library(options.manifest.resolve())


if __name__ == '__main__':
    main()
