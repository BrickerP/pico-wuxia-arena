"""Seal actual full scenes and side-by-side evidence after Root-readable checks."""
from pathlib import Path
import hashlib
import json

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    composition = json.loads((HERE / 'composition.json').read_text())
    render = json.loads((HERE / 'review/render_manifest.json').read_text())
    verification = json.loads((HERE / 'review/verification.json').read_text())
    gltf = json.loads((HERE / 'review/gltf_summary.json').read_text())
    if verification['status'] != 'passed' or not gltf['baseline_warning_fingerprints_exact'] or any(
            m['errors'] or m['new_timber_missing_TBN'] for m in gltf['models']):
        raise ValueError('Structural/glTF gate failed')
    candidate = HERE / composition['outputs']['png']['file']
    if sha(candidate) != render['phases']['after']['scene_sha256']:
        raise ValueError('Images belong to an obsolete geometry/normal-map-frame version')
    for name in ['player_1p65', 'joint_oblique', 'foot_oblique']:
        output = Image.new('RGB', (1920, 986), '#e5e5e5')
        draw = ImageDraw.Draw(output)
        for index, phase in enumerate(['before', 'after']):
            image_path = HERE / 'review' / f'{name}_{phase}.png'
            if sha(image_path) != render['phases'][phase]['images'][image_path.name]:
                raise ValueError('Render image identity changed')
            with Image.open(image_path) as image:
                output.paste(image.convert('RGB'), (960 * index, 26))
            draw.text((960 * index + 10, 6), name + ' ' + phase + ' | full GLB / same camera + light', fill='black')
        output.save(HERE / 'review' / f'{name}_comparison.png')
    files = ['build_entry.py', 'compose_entry.py', 'render_entry.py', 'verify_entry.py',
             'validate_entry.mjs', 'finalize_entry.py', 'entry_module.glb', 'construction.json',
             'courtyard_entry_finish_png.glb', 'courtyard_entry_finish_ktx.glb', 'entry_finish_full_scene.blend',
             'composition.json', 'REBUILD.md', 'review/verification.json', 'review/gltf_summary.json',
             'review/png_gltf_validator.json', 'review/ktx_gltf_validator.json', 'review/render_manifest.json']
    files += ['review/' + name + '_' + phase + '.png'
              for name in ['player_1p65', 'joint_oblique', 'foot_oblique']
              for phase in ['before', 'after', 'comparison']]
    outputs = composition['outputs']
    manifest = {'schema': 'pico-full-scene-native-entry-finish-v1',
        'status': 'private_full_scene_specimen_for_Root_visual_review_not_native_acceptance',
        'outputs': outputs, 'verification': verification, 'gltf_validation': gltf,
        'images': {name: 'review/' + name + '_comparison.png' for name in ['player_1p65', 'joint_oblique', 'foot_oblique']},
        'replacement_scope': 'Only two existing main entry posts and two old three-part brackets; existing door leaves/frames/paper/bronze/stone seats/windows/lanterns/ground unchanged.',
        'visible_work': ['chamfered solid directional-grain posts seated in original stone sockets',
                         'true through-rail seats and shouldered corbel tenons',
                         '190mm closed profiled ox-leg braces, real side recesses and bearing saddles',
                         'two bounded real wear cuts per post; original PBR materials reused'],
        'correction': 'Localized boolean/bevel float32 cleanup: remove the smallest wear notch, weld only new parts within10um, dissolve sub-micron degenerate edges and triangulate before export. Closed-solid and strict final triangle checks retained; explicit TBN uses existing canonical helper. Final after views rerendered.',
        'public_scene_modified': False, 'device_or_shared_gradle_run': False, 'git_history_or_index_modified': False,
        'limits': ['Normal player-distance change is restrained; local timber shape/connection is visibly improved, not overall art approval.',
                   'No terminal load, native TBN/lighting or Space Pro performance evidence.',
                   'Offline fixed lighting is the inherited stage2 recipe; not a calibration of the runtime7f IBL.',
                   'Existing source material grain/normal maps remain; no new scanned wood or texture detail claimed.'],
        'files': {name: {'sha256': sha(HERE / name), 'bytes': (HERE / name).stat().st_size} for name in files}}
    (HERE / 'handoff.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'handoff_sha256': sha(HERE / 'handoff.json'), 'png': outputs['png']['sha256'],
                      'ktx': outputs['ktx']['sha256'], 'budget': outputs['ktx']['budget']}))


if __name__ == '__main__':
    main()
