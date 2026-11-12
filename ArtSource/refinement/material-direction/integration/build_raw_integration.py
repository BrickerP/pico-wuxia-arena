"""Compose the accepted RGB atlas and exact local tangent delta on frozen raw34ce.

No prepared actor is used as the output document; no producer or formal asset is written.
"""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RAW = REPO / 'ArtSource/refinement/hero-face/neck-continuous/candidate-raw.glb'
RAW_SHA = '34ce3a601f842fcb512b643d2ea62317e87485d646ca453e4a46d5116681d4f9'
REFERENCE_SHA = 'b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09'
BODY_SHA = '2f3c385efcd08004dc851549af60088711c5b289ec964a2874116d4270ccc79b'
ALBEDO = HERE.parent / 'textures/coat_basecolor.png'
MASK = HERE.parent / 'textures/albedo_write_mask.png'
DELTA = REPO / 'ArtSource/refinement/hero-face/tangent-audit/tangent-delta.json'
TANGENT_SCRIPT = DELTA.with_name('build_tangent_delta.py')
PINS = {
    ALBEDO: 'd1037bb7875a75520a83358d0b150ed8e7945f74c3f7b9a717a5369db1f33d20',
    MASK: '1dd1913a6249ee9238baef7b9f41cd901e1fb62f4f5aa41ed0e87d1f480420ad',
    DELTA: '6044878a8056e8839ba2a8190d54e0b13b0461147cb8fbb7ca56da19a6b9bc2c',
    TANGENT_SCRIPT: 'e0024d59da41cf787de9bb961f38340356f314e4a7fa2a171fe61f9ec4ed6c35',
    HERE.parent / 'handoff.json': '61e0d9baca7411c5db33d867fd9e365db8536fccf452b31694662234b166e3b8',
    HERE / 'baseline_manifest.json': '52912cd6753c89fdf22ef263e4fcc59b7111160f72cd8d84cbea8342301f52da',
    HERE / 'baseline_request.json': '12a4f2bc81a929c05c1750160cdff46dc71a3fbd2af5b8de5bc42f275f2a696c',
    HERE / 'baseline_profiles.json': 'cf33d354801c21a688a241f6daead2611c7594cbd0d709107c49d0ac80dd6d1b',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


codec = load('integration_codec', REPO / 'ArtSource/refinement/pbr-compression/compress_pbr.py')
tangents = load('integration_tangents', TANGENT_SCRIPT)


def pinned(path, expected):
    data = path.read_bytes()
    require(sha(data) == expected, 'input identity changed: ' + str(path))
    return data


def raw_document(data):
    require(sha(data) == RAW_SHA, 'composition requires frozen raw34ce, never a prepared actor')
    document, binary = codec.load_glb(data)
    require(not document.get('animations'), 'raw input must not contain prepared clips')
    require(len(document['skins']) == 1 and len(document['skins'][0]['joints']) == 78, 'raw skin identity differs')
    codec.image_contracts(document)  # Reject image/view/accessor aliasing and unsupported layouts.
    return document, binary


def payload(document, binary, index):
    return codec.view_bytes(document, binary, document['images'][index]['bufferView'])


def check_pixels(original, replacement, mask_payload):
    with Image.open(io.BytesIO(original)) as image:
        image.load()
        source = np.array(image)
        mode = image.mode
    with Image.open(io.BytesIO(replacement)) as image:
        image.load()
        target = np.array(image)
        require(image.mode == mode and mode in ('RGB', 'RGBA'), 'albedo channel mode changed')
    with Image.open(io.BytesIO(mask_payload)) as image:
        require(image.mode == 'L', 'write mask must be a binary L image')
        mask = np.array(image)
    require(source.shape == target.shape and mask.shape == source.shape[:2], 'albedo/mask dimensions changed')
    require(set(np.unique(mask)).issubset({0, 255}), 'write mask is not binary')
    require(source.shape[2] == 3 or np.array_equal(source[:, :, 3], target[:, :, 3]), 'albedo alpha changed')
    changed = np.any(source[:, :, :3] != target[:, :, :3], axis=2)
    require(not np.any(changed & (mask == 0)), 'RGB changed outside accepted write mask')
    require(changed.any(), 'accepted albedo contains no RGB change')
    return {'size': [source.shape[1], source.shape[0]], 'mode': mode,
            'changed_rgb_pixels': int(changed.sum()), 'mask_pixels': int((mask > 0).sum()),
            'outside_mask_rgb_exact': True, 'alpha_exact': True}


def checked_tangents(document, binary, delta):
    streams, allowed = [], set()
    for stream in delta['streams']:
        accessor = tangents.tangent_matches(document, binary, stream)
        streams.append((accessor, stream))
        for change in stream['changes']:
            offset = tangents.byte_offset(document, accessor, change['vertex'])
            allowed.update(range(offset, offset + 12))
    patched = tangents.apply_delta(document, binary, delta, RAW_SHA)
    changes = np.flatnonzero(np.frombuffer(binary, dtype=np.uint8) != np.frombuffer(patched, dtype=np.uint8))
    require(all(int(offset) in allowed for offset in changes), 'tangent delta changed bytes outside listed XYZ')
    for accessor, stream in streams:
        require(tangents.stream_hash(document, patched, accessor) == stream['new_stream_sha256'], 'new tangent stream hash differs')
        require(np.array_equal(tangents.rows(document, binary, accessor)[:, 3],
                               tangents.rows(document, patched, accessor)[:, 3]), 'tangent W changed')
    require(len(changes) == delta['verification']['changed_byte_count'] == 380, 'unexpected tangent changed-byte count')
    return patched, {'changed_rows': sum(len(s['changes']) for _, s in streams), 'actual_changed_bytes': len(changes),
                     'only_listed_xyz_changed': True, 'w_exact': True,
                     'streams': [{'accessor': a, 'old_sha256': s['old_stream_sha256'],
                                  'new_sha256': s['new_stream_sha256']} for a, s in streams],
                     'native_zero_tangent_warning_resolved': False,
                     'remaining_risks_from_delta_prepared_reference': delta['untouched_native_tangent_generation_risks']}


def repack_image(document, binary, replacement):
    result = copy.deepcopy(document)
    selected = document['images'][1]['bufferView']
    result['images'][1]['mimeType'] = 'image/png'
    packed = bytearray()
    for index, view in enumerate(result['bufferViews']):
        packed.extend(b'\0' * (-len(packed) % 4))
        data = replacement if index == selected else codec.view_bytes(document, binary, index)
        view['byteOffset'], view['byteLength'] = len(packed), len(data)
        packed.extend(data)
    result['buffers'][0]['byteLength'] = len(packed)
    return result, bytes(packed)


def verify_repack(source, expected_binary, result, packed, replacement):
    selected = source['images'][1]['bufferView']
    require(set(source) == set(result), 'top-level GLB keys changed')
    for field in source:
        if field not in ('buffers', 'bufferViews', 'images'):
            require(source[field] == result[field], 'immutable JSON changed: ' + field)
    expected_images = copy.deepcopy(source['images'])
    expected_images[1]['mimeType'] = 'image/png'
    require(result['images'] == expected_images, 'unexpected image metadata or reference change')
    require(len(source['bufferViews']) == len(result['bufferViews']), 'image replacement appended orphan views')
    require({k: v for k, v in source['buffers'][0].items() if k != 'byteLength'} ==
            {k: v for k, v in result['buffers'][0].items() if k != 'byteLength'}, 'buffer metadata changed')
    for index, (before, after) in enumerate(zip(source['bufferViews'], result['bufferViews'])):
        allowed = {'byteOffset', 'byteLength'} if index == selected else {'byteOffset'}
        require({k: v for k, v in before.items() if k not in allowed} ==
                {k: v for k, v in after.items() if k not in allowed}, 'bufferView metadata changed')
        expected = replacement if index == selected else codec.view_bytes(source, expected_binary, index)
        require(codec.view_bytes(result, packed, index) == expected, 'protected view bytes changed: ' + str(index))
    require(payload(result, packed, 1) == replacement, 'selected albedo payload differs')
    return {'buffer_view_count_unchanged': len(source['bufferViews']), 'selected_view': selected,
            'replaced_in_original_image_view': True, 'appended_orphan_views': 0,
            'other_view_payloads_exact_after_only_listed_tangent_patch': True,
            'geometry_indices_uv_weights_rest_animations_json_exact': True,
            'other_images_exact': [i for i in range(len(source['images'])) if i != 1]}


def build():
    raw_bytes = pinned(RAW, RAW_SHA)
    for path, digest in PINS.items():
        pinned(path, digest)
    handoff = json.loads((HERE.parent / 'handoff.json').read_text())
    require(handoff['recommended_candidate'] == 'albedo_only', 'material selection is not albedo_only')
    document, binary = raw_document(raw_bytes)
    source_image = payload(document, binary, 1)
    require(sha(source_image) == BODY_SHA,
            'raw body albedo payload does not match the accepted material source')
    replacement, mask = ALBEDO.read_bytes(), MASK.read_bytes()
    pixel_report = check_pixels(source_image, replacement, mask)
    patched, tangent_report = checked_tangents(document, binary, json.loads(DELTA.read_text()))
    result, packed = repack_image(document, patched, replacement)
    protection = verify_repack(document, patched, result, packed, replacement)
    output = codec.write_glb(result, packed)
    decoded, encoded_binary = codec.load_glb(output)
    verify_repack(document, patched, decoded, encoded_binary, replacement)
    output_path = HERE / 'base_albedo_tangent_raw.glb'
    output_path.write_bytes(output)
    # Supplied immutable snapshots keep this recipe reproducible after Root publishes.
    baseline_bytes = (HERE / 'baseline_manifest.json').read_bytes()
    candidate = json.loads(baseline_bytes)
    base = next(row for row in candidate['characters'] if row['id'] == 'base')
    require(base['source_sha256'] == RAW_SHA, 'baseline base source differs from the frozen raw')
    base['source'] = str(Path('..') / output_path.relative_to(REPO / 'ArtSource'))
    base['source_sha256'] = sha(output)
    (HERE / 'candidate_manifest.json').write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + '\n')
    baseline_request = (HERE / 'baseline_request.json').read_bytes()
    report = {'status': 'raw_candidate_verified', 'author_script_sha256': sha(Path(__file__).read_bytes()),
              'raw_source': {'path': str(RAW.relative_to(REPO)), 'sha256': RAW_SHA, 'animations': 0},
              'historical_prepared_reference': {'sha256': REFERENCE_SHA,
                  'body_albedo_payload_sha256': BODY_SHA, 'required_for_raw_rebuild': False,
                  'read_during_this_build': False,
                  'role': 'historical b03f source whose image1 payload was independently verified equal to raw34ce'},
              'accepted_handoff_sha256': PINS[HERE.parent / 'handoff.json'],
              'body_albedo_source_payload_sha256': BODY_SHA,
              'replacement_albedo': {'path': str(ALBEDO.relative_to(REPO)), 'sha256': sha(replacement),
                                     'mime_type': 'image/png', 'roughness_replacement_applied': False},
              'pixels': pixel_report, 'tangents': tangent_report, 'protection': protection,
              'output': {'file': output_path.name, 'bytes': len(output), 'sha256': sha(output)},
              'baseline_manifest_sha256': sha(baseline_bytes),
              'candidate_manifest_sha256': sha((HERE / 'candidate_manifest.json').read_bytes()),
              'baseline_profiles_sha256': sha((HERE / 'baseline_profiles.json').read_bytes()),
              'baseline_request_sha256': sha(baseline_request),
              'new_geometry_acceptance': False, 'native_material_and_tangent_warning_status': 'OPEN; Root validates native'}
    (HERE / 'raw_integration_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for path, digest in PINS.items():
        pinned(path, digest)
    pinned(RAW, RAW_SHA)
    print(json.dumps({'raw': report['output'], 'candidate_manifest_sha256': report['candidate_manifest_sha256'],
                      'pixels': pixel_report, 'tangent_rows': tangent_report['changed_rows']}, ensure_ascii=False))


if __name__ == '__main__':
    build()
