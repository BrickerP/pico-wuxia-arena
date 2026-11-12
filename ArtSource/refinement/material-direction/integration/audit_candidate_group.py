#!/usr/bin/env python3
"""Audit the material/tangent raw and the complete rebuilt candidate group.

This full audit requires NEW same-group *_body.glb, *_prepared_png.glb, KTX2
models, profiles and reports from the unique prepare_character_library producer.
The new prepared PNG files are encoding inputs, not the historical b732 copy.
No historical prepared file or mutable formal-library fallback is read.

Prerequisites, from /Users/yupeng/projects/personal/pico-wuxia-arena:
  1. Deliver tracked raw34ce, coat PNG/mask, T delta/helpers and frozen baseline
     JSON snapshots; install the manifest-pinned host Python/Pillow/NumPy and KTX tools.
  2. Rebuild raw a428 and candidate manifest a35f with the host author:
     /Library/Developer/CommandLineTools/usr/bin/python3 ArtSource/refinement/material-direction/integration/build_raw_integration.py
  3. Rebuild the COMPLETE private group with the unique producer:
     /Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --python ArtSource/tripo-warrior/prepare_character_library.py -- --manifest ArtSource/refinement/material-direction/integration/candidate_manifest.json --candidate-dir ArtSource/refinement/material-direction/integration
  4. Run this host audit against the resulting pinned request:
     /Library/Developer/CommandLineTools/usr/bin/python3 ArtSource/refinement/material-direction/integration/audit_candidate_group.py --request-sha256 eb8c0c0cd58488f1db4aa3c6361572513f47b07496b76013cfa55f7c9233e175

Only candidate_group_audit.json is written. This script never executes an author,
producer, Blender build or publication, and never substitutes missing candidates.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
ART_HERE = REPO / 'ArtSource/tripo-warrior'
PINS = {
    'raw_integration_audit.json': '64c8dfc23c91bbfc30ef1f6f2192d58db81b6da14b55c9ad801ace30b309e7dd',
    'build_raw_integration.py': 'be767413c6766825d401a51dfb9c272d8bbf74c904a061f1bc57121f57ac6e6d',
    'candidate_manifest.json': 'a35f40fe7227b45d0376ff9f5b2e52560700aeecf7cd12f01fbe100146cdff0c',
    'baseline_manifest.json': '52912cd6753c89fdf22ef263e4fcc59b7111160f72cd8d84cbea8342301f52da',
    'baseline_profiles.json': 'cf33d354801c21a688a241f6daead2611c7594cbd0d709107c49d0ac80dd6d1b',
    'baseline_request.json': '12a4f2bc81a929c05c1750160cdff46dc71a3fbd2af5b8de5bc42f275f2a696c',
}
RAW_SOURCE = REPO / 'ArtSource/refinement/hero-face/neck-continuous/candidate-raw.glb'
RAW_SHA256 = '34ce3a601f842fcb512b643d2ea62317e87485d646ca453e4a46d5116681d4f9'
RAW_CANDIDATE_SHA256 = 'a4280be15191970a6271a127bf862adee0ea7b7a93174d1b82c83304e49d52ec'
BASELINE_BINDING_SHA256 = 'b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f'
ALBEDO_SHA256 = 'd1037bb7875a75520a83358d0b150ed8e7945f74c3f7b9a717a5369db1f33d20'
MASK_SHA256 = '1dd1913a6249ee9238baef7b9f41cd901e1fb62f4f5aa41ed0e87d1f480420ad'
DELTA_SHA256 = '6044878a8056e8839ba2a8190d54e0b13b0461147cb8fbb7ca56da19a6b9bc2c'
HANDOFF_SHA256 = '61e0d9baca7411c5db33d867fd9e365db8536fccf452b31694662234b166e3b8'
PLAYER_SHA256 = 'db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode())


def identity(path):
    data = path.read_bytes()
    resolved = path.resolve()
    name = str(resolved.relative_to(REPO)) if REPO in resolved.parents else str(resolved)
    return {'path': name, 'sha256': sha(data), 'bytes': len(data)}


def pinned_json(path, expected):
    actual = identity(path)
    require(actual['sha256'] == expected, 'pinned JSON identity changed: ' + actual['path'])
    return json.loads(path.read_text()), actual


def local_path(folder, filename):
    require(isinstance(filename, str) and Path(filename).name == filename,
            'artifact filename must be local: ' + str(filename))
    return folder / filename


def check_output(row, folder):
    path = local_path(folder, row['file'])
    actual = identity(path)
    require(actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes'],
            'output file differs from its SHA/byte count: ' + actual['path'])
    return actual


def by_id(rows):
    result = {row['id']: row for row in rows}
    require(len(result) == len(rows), 'duplicate character identifiers')
    return result


def load_helper(config):
    for field in ('helper', 'encoder', 'release_identity', 'host_python'):
        entry = config[field]
        require(sha((ART_HERE / entry['source']).read_bytes()) == entry['source_sha256'],
                'runtime encoding input identity changed: ' + field)
    import PIL
    import numpy as np
    require(sys.version.split()[0] == config['host_python']['version'] and
            PIL.__version__ == config['host_python']['pillow_version'] and
            np.__version__ == config['host_python']['numpy_version'],
            'audit must run in the manifest-pinned host Python/Pillow/NumPy environment')
    path = (ART_HERE / config['helper']['source']).resolve()
    spec = importlib.util.spec_from_file_location('encoded_group_pbr_helper', path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(helper.SETTINGS == config['settings'], 'helper settings differ from manifest')
    encoder = helper.encoder_identity(ART_HERE / config['encoder']['source'])
    require(encoder['sha256'] == config['encoder']['source_sha256'] and
            encoder['version'] == config['encoder']['version'] and
            encoder['libktx_sha256'] == config['encoder']['libktx_sha256'],
            'encoder/libktx identity differs from manifest')
    return helper, encoder, {'executable': str(Path(sys.executable).resolve()),
                             'python_version': sys.version.split()[0],
                             'pillow_version': PIL.__version__, 'numpy_version': np.__version__}


def check_encoding_report(report, source, output, config, helper):
    source_id, output_id = identity(source), identity(output)
    require(report['input']['sha256'] == source_id['sha256'] and
            report['input']['bytes'] == source_id['bytes'], 'encoding report input identity differs')
    require(report['output']['sha256'] == output_id['sha256'] and
            report['output']['bytes'] == output_id['bytes'] and
            report['output']['path'] == output.name, 'encoding report output identity differs')
    require(report['settings'] == config['settings'] and
            report['encoder']['sha256'] == config['encoder']['source_sha256'] and
            report['encoder']['libktx_sha256'] == config['encoder']['libktx_sha256'] and
            report['encoder']['version'] == config['encoder']['version'],
            'encoding report settings/tool identity differs')
    for field in ('helper', 'host_python', 'release_identity'):
        require(report[field] == config[field], 'encoding report tool binding differs: ' + field)
    require(report['decoder']['version'] == config['host_python']['pillow_version'],
            'encoding report decoder identity differs')
    proof = helper.verify_preserved(source.read_bytes(), output.read_bytes())
    require(proof['non_image_json_semantics_identical'] is True,
            'encoding changed non-image JSON semantics')
    require(report['preservation'] == proof, 'recorded preservation proof differs from recomputed proof')
    document, _ = helper.load_glb(output.read_bytes())
    require(document['extensionsUsed'] == ['KHR_texture_basisu'] and
            document['extensionsRequired'] == ['KHR_texture_basisu'] and
            all(image['mimeType'] == 'image/ktx2' for image in document['images']) and
            all('source' not in texture and set(texture['extensions']) == {'KHR_texture_basisu'}
                for texture in document['textures']), 'runtime contains a PNG/JPEG texture fallback')
    return proof


def snapshot_inputs(report):
    documents = {}
    report['frozen_inputs'] = {}
    for name, digest in PINS.items():
        path = HERE / name
        actual = identity(path)
        require(actual['sha256'] == digest, 'frozen integration input changed: ' + name)
        report['frozen_inputs'][name] = actual
        if path.suffix == '.json':
            documents[name] = json.loads(path.read_text())
    audit = documents['raw_integration_audit.json']
    historical = audit['historical_prepared_reference']
    require(historical['sha256'] == 'b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09' and
            historical['body_albedo_payload_sha256'] == '2f3c385efcd08004dc851549af60088711c5b289ec964a2874116d4270ccc79b' and
            historical['required_for_raw_rebuild'] is False and historical['read_during_this_build'] is False and
            'prepared_reference' not in audit, 'historical b732 provenance must declare no required/read prepared file')
    report['historical_prepared_reference'] = copy.deepcopy(historical)
    report['historical_prepared_reference_file_read'] = False
    require(audit['status'] == 'raw_candidate_verified' and audit['author_script_sha256'] == PINS['build_raw_integration.py'],
            'raw author/audit identity differs')
    for field, name in [('baseline_manifest_sha256', 'baseline_manifest.json'),
                        ('candidate_manifest_sha256', 'candidate_manifest.json'),
                        ('baseline_profiles_sha256', 'baseline_profiles.json'),
                        ('baseline_request_sha256', 'baseline_request.json')]:
        require(audit[field] == PINS[name], 'raw audit snapshot identity differs: ' + name)
    before, after = copy.deepcopy(documents['baseline_manifest.json']), copy.deepcopy(documents['candidate_manifest.json'])
    before.pop('production_review', None); after.pop('production_review', None)
    prior_base = next(row for row in before['characters'] if row['id'] == 'base')
    new_base = next(row for row in after['characters'] if row['id'] == 'base')
    require(prior_base['source_sha256'] == RAW_SHA256 and new_base['source_sha256'] == RAW_CANDIDATE_SHA256,
            'manifest base raw identities differ from the reviewed pair')
    require((ART_HERE / new_base['source']).resolve() == (HERE / 'base_albedo_tangent_raw.glb').resolve(),
            'base manifest must use the integrated raw, never a prepared GLB')
    prior_base['source'], prior_base['source_sha256'] = new_base['source'], new_base['source_sha256']
    require(canonical_sha(before) == canonical_sha(after),
            'manifest changed beyond base.source/source_sha256 and optional production_review')
    report['manifest_change_policy'] = 'exactly base.source and base.source_sha256; production_review ignored as approval metadata'
    return documents


def tangent_stream(document, views, index):
    accessor = document['accessors'][index]
    require(accessor['componentType'] == 5126 and accessor['type'] == 'VEC4' and
            not accessor.get('normalized') and 'sparse' not in accessor, 'T delta requires nonsparse FLOAT VEC4')
    view = document['bufferViews'][accessor['bufferView']]
    stride, offset = view.get('byteStride', 16), accessor.get('byteOffset', 0)
    require(accessor['count'] > 0 and stride >= 16 and offset >= 0 and
            offset + (accessor['count'] - 1) * stride + 16 <= len(views[accessor['bufferView']]),
            'T accessor exceeds its bufferView')
    payload = b''.join(views[accessor['bufferView']][offset + vertex * stride:offset + vertex * stride + 16]
                       for vertex in range(accessor['count']))
    return payload, stride, offset


def audit_raw(helper, source_report):
    import numpy as np
    from PIL import Image
    raw_bytes = RAW_SOURCE.read_bytes()
    output_path = HERE / source_report['output']['file']
    output_bytes = output_path.read_bytes()
    require(sha(raw_bytes) == RAW_SHA256 and sha(output_bytes) == RAW_CANDIDATE_SHA256 == source_report['output']['sha256'],
            'raw source/integration output SHA differs')
    require(len(output_bytes) == source_report['output']['bytes'], 'raw output byte count differs')
    original, binary = helper.load_glb(raw_bytes)
    integrated, packed = helper.load_glb(output_bytes)
    require(not original.get('animations') and not integrated.get('animations') and
            len(original['images']) == len(integrated['images']) == 8 and
            len(original['skins']) == len(integrated['skins']) == 1 and
            len(original['skins'][0]['joints']) == len(integrated['skins'][0]['joints']) == 78,
            'raw shape must remain zero animations, eight images and one 78-joint skin')
    helper.image_contracts(original)
    require(set(original) == set(integrated), 'raw top-level JSON keys changed')
    for field in set(original) - {'buffers', 'bufferViews', 'images'}:
        require(original[field] == integrated[field], 'raw protected JSON changed: ' + field)
    expected_images = copy.deepcopy(original['images']); expected_images[1]['mimeType'] = 'image/png'
    require(integrated['images'] == expected_images, 'only image1 MIME metadata may change')
    require(len(original['bufferViews']) == len(integrated['bufferViews']), 'raw bufferView count changed')
    require(len(original['buffers']) == len(integrated['buffers']) == 1 and
            {key: value for key, value in original['buffers'][0].items() if key != 'byteLength'} ==
            {key: value for key, value in integrated['buffers'][0].items() if key != 'byteLength'},
            'raw buffer metadata changed')
    selected = original['images'][1]['bufferView']
    before_views = {index: helper.view_bytes(original, binary, index) for index in range(len(original['bufferViews']))}
    expected_views = {index: bytearray(payload) for index, payload in before_views.items()}
    delta_path = REPO / 'ArtSource/refinement/hero-face/tangent-audit/tangent-delta.json'
    delta, delta_identity = pinned_json(delta_path, DELTA_SHA256)
    require(RAW_SHA256 in delta['verified_source_sha256'], 'T delta does not admit the frozen raw source')
    tangent_accessors = {primitive['attributes']['TANGENT'] for mesh in original['meshes']
                        for primitive in mesh['primitives'] if 'TANGENT' in primitive['attributes']}
    changed_rows, allowed, stream_reports = set(), {}, []
    for stream in delta['streams']:
        matches = [index for index in tangent_accessors if original['accessors'][index]['count'] == stream['vertex_count']
                   and sha(tangent_stream(original, before_views, index)[0]) == stream['old_stream_sha256']]
        require(len(matches) == 1, 'T delta source stream must match exactly one raw accessor')
        index = matches[0]; accessor = original['accessors'][index]; view_index = accessor['bufferView']
        require(view_index != selected, 'image1 and T accessor share a view')
        old_stream, stride, offset = tangent_stream(original, before_views, index)
        for change in stream['changes']:
            vertex = change['vertex']
            require(type(vertex) is int and 0 <= vertex < accessor['count'] and (index, vertex) not in changed_rows,
                    'invalid or duplicate listed T row')
            previous = old_stream[vertex * 16:(vertex + 1) * 16]
            old, new = change['old'], change['new']
            require(len(old) == len(new) == 4 and np.isfinite(np.array([old, new], dtype=float)).all() and
                    struct.pack('<4f', *old) == previous and new[3] == old[3],
                    'T delta old value/W identity differs')
            begin = offset + vertex * stride
            expected_views[view_index][begin:begin + 12] = struct.pack('<3f', *new[:3])
            allowed.setdefault(view_index, set()).update(range(begin, begin + 12))
            changed_rows.add((index, vertex))
        actual_stream = tangent_stream(original, expected_views, index)[0]
        require(sha(actual_stream) == stream['new_stream_sha256'], 'T delta new stream SHA differs')
        require(all(old_stream[row * 16 + 12:(row + 1) * 16] == actual_stream[row * 16 + 12:(row + 1) * 16]
                    for row in range(accessor['count'])), 'T W bytes changed')
        stream_reports.append({'accessor': index, 'rows': len(stream['changes']),
                               'old_sha256': sha(old_stream), 'new_sha256': sha(actual_stream)})
    difference_count = 0
    for index, before in before_views.items():
        changes = np.flatnonzero(np.frombuffer(before, dtype=np.uint8) != np.frombuffer(expected_views[index], dtype=np.uint8))
        require(all(int(byte) in allowed.get(index, set()) for byte in changes), 'T patch exceeds listed XYZ bytes')
        difference_count += len(changes)
    require(len(changed_rows) == 48 and difference_count == 380 and
            source_report['tangents']['changed_rows'] == 48 and source_report['tangents']['actual_changed_bytes'] == 380,
            'T delta must contain exactly 48 rows and 380 changed bytes')
    albedo_path = HERE.parent / 'textures/coat_basecolor.png'
    mask_path = HERE.parent / 'textures/albedo_write_mask.png'
    albedo, mask_bytes = albedo_path.read_bytes(), mask_path.read_bytes()
    require(sha(albedo) == ALBEDO_SHA256 == source_report['replacement_albedo']['sha256'] and sha(mask_bytes) == MASK_SHA256,
            'accepted albedo/mask SHA differs')
    handoff, handoff_identity = pinned_json(HERE.parent / 'handoff.json', HANDOFF_SHA256)
    require(handoff['recommended_candidate'] == 'albedo_only', 'accepted material route differs')
    source_image = before_views[selected]
    require(sha(source_image) == source_report['body_albedo_source_payload_sha256'], 'source image1 payload differs')
    with Image.open(io.BytesIO(source_image)) as image:
        mode = image.mode; image.load(); old_pixels = np.array(image)
    with Image.open(io.BytesIO(albedo)) as image:
        require(image.mode == mode and mode in ('RGB', 'RGBA'), 'albedo pixel mode changed')
        image.load(); new_pixels = np.array(image)
    with Image.open(io.BytesIO(mask_bytes)) as image:
        require(image.mode == 'L', 'write mask must be binary L'); image.load(); mask = np.array(image)
    require(old_pixels.shape == new_pixels.shape and mask.shape == old_pixels.shape[:2] and
            set(np.unique(mask)).issubset({0, 255}), 'albedo or binary mask dimensions changed')
    require(mode == 'RGB' or np.array_equal(old_pixels[:, :, 3], new_pixels[:, :, 3]), 'albedo alpha changed')
    changed = np.any(old_pixels[:, :, :3] != new_pixels[:, :, :3], axis=2)
    require(changed.any() and not np.any(changed & (mask == 0)), 'albedo RGB changed outside accepted mask or not at all')
    pixels = {'size': [old_pixels.shape[1], old_pixels.shape[0]], 'mode': mode,
              'changed_rgb_pixels': int(changed.sum()), 'mask_pixels': int((mask > 0).sum()),
              'outside_mask_rgb_exact': True, 'alpha_exact': True}
    require(pixels == source_report['pixels'], 'recomputed pixel proof differs from author report')
    expected_views[selected] = bytearray(albedo)
    for index, (before, after) in enumerate(zip(original['bufferViews'], integrated['bufferViews'])):
        ignored = {'byteOffset', 'byteLength'} if index == selected else {'byteOffset'}
        require({key: value for key, value in before.items() if key not in ignored} ==
                {key: value for key, value in after.items() if key not in ignored}, 'protected raw view metadata changed')
        require(helper.view_bytes(integrated, packed, index) == bytes(expected_views[index]),
                'raw candidate changed protected bufferView payload: ' + str(index))
    return {'source': identity(RAW_SOURCE), 'integrated_raw': identity(output_path), 'delta': delta_identity,
            'handoff': handoff_identity, 'accepted_albedo': identity(albedo_path), 'write_mask': identity(mask_path),
            'animations': 0, 'images': 8, 'skin_joints': 78, 'image1_view': selected,
            'all_other_json_exact': True, 'all_71_view_payloads_match_selected_image_plus_listed_tangent_xyz': True,
            'tangent_rows_changed': 48, 'tangent_bytes_changed': 380, 'tangent_w_bits_unchanged': True,
            'tangent_streams': stream_reports, 'pixels': pixels,
            'normal_roughness_geometry_indices_uv_weights_rest_animations_unchanged': True,
            'native_tangent_warning_status': 'OPEN; listed tangent correction is not a native warning-resolution claim'}


def require_complete_candidate(manifest):
    expected = {'base_albedo_tangent_raw.glb', 'production_review_request.json', 'characters.json',
                'dao_grip.glb', 'dao_grip_texture_encoding.json', 'player_weapon_manifest.json'}
    for actor in manifest['characters']:
        output = actor['output']
        local_path(HERE, output)
        stem = Path(output).stem
        expected.update({output, stem + '_body.glb', stem + '_prepared_png.glb', stem + '_alignment.json',
                         stem + '_attack_profiles.json', stem + '_texture_encoding.json'})
    missing = sorted(name for name in expected if not (HERE / name).is_file())
    require(not missing,
            'Incomplete rebuilt private candidate group; missing: ' + ', '.join(missing) +
            '. These are NEW same-group producer outputs, not historical b732 inputs. '
            'Run the host author and unique producer commands in --help, then rerun this audit. '
            'No formal-library fallback is permitted.')


def audit(request_sha, report):
    snapshots = snapshot_inputs(report)
    manifest = snapshots['candidate_manifest.json']; prior_manifest = snapshots['baseline_manifest.json']
    require_complete_candidate(manifest)
    prior_request = snapshots['baseline_request.json']; prior_profiles = snapshots['baseline_profiles.json']
    request, report['candidate_request'] = pinned_json(HERE / 'production_review_request.json', request_sha)
    require(canonical_sha(prior_request['binding']) == prior_request['binding_sha256'] == BASELINE_BINDING_SHA256,
            'frozen baseline request is not the published b03f group')
    require(canonical_sha(request['binding']) == request['binding_sha256'], 'candidate binding hash differs')
    prior_binding = copy.deepcopy(prior_request['binding'])
    new_base = next(row for row in manifest['characters'] if row['id'] == 'base')
    expected_base = next(row for row in prior_binding['characters'] if row['id'] == 'base')
    expected_base['source'], expected_base['source_sha256'] = new_base['source'], new_base['source_sha256']
    require(canonical_sha(prior_binding) == canonical_sha(request['binding']),
            'candidate binding changed beyond base raw source identity')
    for field in ('schema_version', 'motion_source', 'locomotion_source', 'body_coverage_calibration',
                  'attack_source', 'runtime_texture_encoding', 'player_weapon_source', 'weapon_source'):
        require(request['binding'][field] == manifest[field], 'candidate manifest/binding differs: ' + field)
    selected = ('id', 'name', 'source', 'source_sha256', 'grip_source', 'height_metres', 'output',
                'grip_frame', 'finger_rotation_offsets')
    require(request['binding']['characters'] == [{key: row.get(key) for key in selected} for row in manifest['characters']],
            'candidate character binding differs from manifest')
    config = manifest['runtime_texture_encoding']
    helper, report['encoder_identity'], report['host_runtime_identity'] = load_helper(config)
    report['raw_source_verification'] = audit_raw(helper, snapshots['raw_integration_audit.json'])
    report['binding_sha256'] = request['binding_sha256']
    index = json.loads((HERE / 'characters.json').read_text()); report['index'] = identity(HERE / 'characters.json')
    current, prior, indexed = by_id(request['characters']), by_id(prior_request['characters']), by_id(index['characters'])
    require(set(current) == set(prior) == set(indexed) == set(prior_profiles) == {'base', 'indigo', 'veteran'},
            'candidate/index/baseline profile groups differ')
    report['characters'] = []
    for actor in manifest['characters']:
        name, output_name = actor['id'], actor['output']; stem = Path(output_name).stem
        new, old, item = current[name], prior[name], indexed[name]
        alignment_path = HERE / (stem + '_alignment.json'); alignment = json.loads(alignment_path.read_text())
        require(new['outputs'] == item['outputs'] == alignment['outputs'], 'output lists differ: ' + name)
        output_identities = [check_output(row, HERE) for row in new['outputs']]
        model_path = local_path(HERE, output_name); model_identity = identity(model_path)
        old_model = next(row for row in old['outputs'] if row['file'] == output_name)
        if name != 'base':
            require(model_identity['sha256'] == old_model['sha256'] and model_identity['bytes'] == old_model['bytes'],
                    'unchanged target encoded bytes differ from b03f: ' + name)
        require(item['output'] == output_name and item['animations'] == list(new['clip_semantic_signatures']),
                'index model/animations differ: ' + name)
        require(alignment['source_sha256'] == actor['source_sha256'], 'alignment raw source differs: ' + name)
        profile_path = HERE / (stem + '_attack_profiles.json'); profile = json.loads(profile_path.read_text())
        profile_identity = identity(profile_path); previous_profile = prior_profiles[name]
        previous_profile_bytes = (json.dumps(previous_profile, ensure_ascii=False, indent=2) + '\n').encode()
        require(sha(previous_profile_bytes) == old['attack_profiles_sha256'] and
                previous_profile['model_sha256'] == old_model['sha256'], 'baseline profile snapshot/request chain differs: ' + name)
        require(profile['model_sha256'] == model_identity['sha256'] and
                profile_identity['sha256'] == new['attack_profiles_sha256'] == item['attack_profiles']['sha256'] ==
                alignment['attack_profiles']['sha256'] and item['attack_profiles']['file'] == profile_path.name ==
                alignment['attack_profiles']['file'], 'profile/model/ref SHA chain differs: ' + name)
        current_values, previous_values = copy.deepcopy(profile), copy.deepcopy(previous_profile)
        current_values.pop('model_sha256'); previous_values.pop('model_sha256')
        require(canonical_sha(current_values) == canonical_sha(previous_values), 'profile numerical/contract values changed: ' + name)
        require(new['clip_semantic_signatures'] == old['clip_semantic_signatures'] and
                new['hand_track_signatures'] == old['hand_track_signatures'], 'animation/hand semantics changed: ' + name)
        encoding_ref = alignment['runtime_texture_encoding']
        require(new['texture_encoding_manifest_sha256'] == encoding_ref['sha256'] and
                item['runtime_texture_encoding'] == encoding_ref, 'encoding-report SHA chain differs: ' + name)
        encoding_path = local_path(HERE, encoding_ref['file'])
        encoding, encoding_identity = pinned_json(encoding_path, encoding_ref['sha256'])
        prepared = HERE / (stem + '_prepared_png.glb')
        proof = check_encoding_report(encoding, prepared, model_path, config, helper)
        require(encoding_ref['prepared_png_sha256'] == identity(prepared)['sha256'] and
                encoding_ref['encoded_sha256'] == model_identity['sha256'] and encoding_ref['preservation'] == proof and
                encoding['animation_semantic_signatures'] == new['clip_semantic_signatures'],
                'encoded GLB/source/animation evidence differs: ' + name)
        report['characters'].append({'id': name, 'encoded_model': model_identity,
            'unchanged_b03f_model_sha256': old_model['sha256'] if name != 'base' else None,
            'outputs': output_identities, 'alignment': identity(alignment_path), 'profile': profile_identity,
            'profile_excluding_model_sha256_exactly_equal': True, 'profile_values_sha256': canonical_sha(current_values),
            'encoding_report': encoding_identity, 'encoding_and_all_metadata_sha_chain_consistent': True,
            'prepared_png_to_encoded_non_image_preservation': proof,
            'all_clip_and_hand_semantic_signatures_unchanged': True,
            'locomotion_sample_counts': {key: len(row['samples']) for key, row in profile['locomotion'].items()},
            'attack_sample_counts': {key: len(row['samples']) for key, row in profile['attacks'].items()}})
        print('AUDITED_ACTOR', name, model_identity['sha256'], flush=True)
    player = request['player_weapon']; player_manifest_path = HERE / 'player_weapon_manifest.json'
    player_manifest = json.loads(player_manifest_path.read_text())
    require(player == prior_request['player_weapon'] == index['player_weapon'] and
            {key: value for key, value in player.items() if key != 'manifest_sha256'} == player_manifest and
            identity(player_manifest_path)['sha256'] == player['manifest_sha256'], 'player group differs from b03f or metadata chain')
    require(player_manifest['source'] == manifest['player_weapon_source'] and player_manifest['runtime_texture_encoding'] == config,
            'player source/tool binding differs')
    player_output = check_output(player_manifest['output'], HERE)
    require(player_output['sha256'] == PLAYER_SHA256 and player_manifest['output']['file'] == 'dao_grip.glb',
            'player runtime bytes differ from the published db28 baseline')
    source_path = (ART_HERE / manifest['player_weapon_source']['source']).resolve()
    require(identity(source_path)['sha256'] == manifest['player_weapon_source']['source_sha256'], 'player source pin changed')
    encoding_ref = player_manifest['texture_encoding_manifest']; encoding_path = local_path(HERE, encoding_ref['file'])
    encoding, encoding_identity = pinned_json(encoding_path, encoding_ref['sha256'])
    proof = check_encoding_report(encoding, source_path, HERE / 'dao_grip.glb', config, helper)
    report['player_weapon'] = {'encoded_model': player_output, 'manifest': identity(player_manifest_path),
        'encoding_report': encoding_identity, 'exact_b03f_bytes_and_metadata': True, 'non_image_preservation': proof}
    report['status'] = 'passed_offline_material_raw_and_candidate_group_audit'
    report['native_material_tangent_sdk_contact_status'] = 'OPEN; no native appearance, tangent-warning, SDK collision or GPU-memory claim'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--request-sha256', required=True)
    args = parser.parse_args()
    report = {'schema_version': 1, 'status': 'failed', 'audit_script': identity(Path(__file__)),
              'expected_request_sha256': args.request_sha256}
    try:
        audit(args.request_sha256, report)
    except FileNotFoundError as error:
        report['error'] = ('Missing required delivered source/snapshot or rebuilt candidate: ' + str(error.filename) +
                           '. Restore the pinned repository inputs and follow the author/unique-producer prerequisites in --help. '
                           'Historical b732 and mutable-library fallback are never used.')
    except (ValueError, KeyError, IndexError, StopIteration, TypeError, OSError, ImportError, struct.error) as error:
        report['error'] = str(error)
    output = HERE / 'candidate_group_audit.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(report['status'], 'REPORT', output, 'SHA256', sha(output.read_bytes()), flush=True)
    if report['status'] != 'passed_offline_material_raw_and_candidate_group_audit':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
