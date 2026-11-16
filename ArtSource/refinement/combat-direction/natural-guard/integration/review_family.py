"""Review the actual three-target natural-guard bank before Root publication.

Run in the existing Blender host wrapper. This checks finite target surfaces and
renders the exported actors; it never publishes models or approves the bank.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[5]
HELPER = REPO / 'ArtSource/refinement/combat-direction/native-weighted-overhead/integration/review_candidate.py'
TARGETS = ('base', 'indigo', 'veteran')
POSES = {
    'idle': [0.0, .375, .75, 1.125, 1.5],
    'walk': [0.0, 1 / 3, 19 / 36, 11 / 12, 1.5],
    'attack_overhead': [0.0, .1, .2, .68, 5 / 6, .9, 1.0, 31 / 30, 1.1, 1.15, 1.4, 44 / 30, 1.5, 1.6, 1.75],
    'attack_left': [0.0, .1, .2, .65, .9, 1.1, 1.5, 1.6, 1.75],
    'attack_right': [0.0, .1, .2, .65, .9, 1.1, 1.5, 1.6, 1.75],
}


def require(value, message):
    if not value:
        raise ValueError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bank', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--binding', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
    if len(args.binding) != 64 or any(ch not in '0123456789abcdef' for ch in args.binding):
        parser.error('binding must be a SHA256')
    spec = importlib.util.spec_from_file_location('target_surface_review', HELPER)
    review = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review)
    bank, output = args.bank.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    review.OUT = output
    request_path = bank / 'production_review_request.json'
    request = json.loads(request_path.read_text())
    require(request['status'] == 'pending_root_review', 'review requires an unpublished candidate bank')
    require(request['binding_sha256'] == args.binding == review.library.canonical_hash(request['binding']),
            'candidate binding differs from the requested identity')
    pins = {str(path.relative_to(REPO)): review.sha(path) for path in
            (request_path, Path(__file__), HELPER, Path(review.library.__file__),
             Path(review.profiles.__file__), Path(review.UTILITY.__file__), review.CAMERA)}
    report = {
        'status': 'actual_target_review_in_progress_not_approval',
        'binding_sha256': args.binding,
        'source_pins': pins,
        'declared_finite_poses': POSES,
        'targets': [],
        'limits': [
            'Finite actual target samples, not a continuous-time or native skinned-mesh proof.',
            'Steel against full body and nonadjacent core semantic regions only; adjacent cloth/armor layers are excluded.',
            'Original material PNG renders are offline evidence, not PICO KTX or hardware acceptance.',
        ],
    }
    report_path = output / 'review_report.json'
    save(report_path, report)
    for target in TARGETS:
        receipt = next(row for row in request['characters'] if row['id'] == target)
        row = {'target': target, 'static_preservation': {}, 'changed_clips': {}, 'clips': {}}
        report['targets'].append(row)
        for item in receipt['outputs']:
            candidate = bank / item['file']
            require(candidate.stat().st_size == item['bytes'] and review.sha(candidate) == item['sha256'],
                    'exported asset differs from receipt: ' + item['file'])
            pins[str(candidate.relative_to(REPO))] = item['sha256']
            old_path = review.FORMAL / item['file']
            pins[str(old_path.relative_to(REPO))] = review.sha(old_path)
            current, previous = review.library.read_glb(candidate), review.library.read_glb(old_path)
            before = review.static_signature(*previous)
            after = review.static_signature(*current)
            checks = {key: before[key] == after[key] for key in before}
            require(all(checks.values()), 'unexpected geometry/rest/skin/material change: ' + item['file'])
            row['static_preservation'][item['file']] = checks
            old_clips = {clip['name']: review.library.animation_signature(*previous, clip)
                         for clip in previous[0]['animations']}
            new_clips = {clip['name']: review.library.animation_signature(*current, clip)
                         for clip in current[0]['animations']}
            require(old_clips.keys() == new_clips.keys() and len(new_clips) == 10, 'ten-clip identity changed')
            changed = sorted(name for name in new_clips if new_clips[name] != old_clips[name])
            require(set(POSES).issubset(changed), 'the five canonical family clips must change')
            extra = set(changed) - set(POSES)
            require(extra.issubset({'fall', 'turn', 'hit_body', 'hit_head', 'hit_side'}),
                    'unexpected extra animation clip changed')
            numeric = {}
            for clip_name in sorted(extra):
                _, before_tracks, before_keys = review.clip(*previous, clip_name)
                _, after_tracks, after_keys = review.clip(*current, clip_name)
                require(before_tracks.keys() == after_tracks.keys() and before_keys == after_keys,
                        'sampling repair changed a reaction track or source grid')
                delta = 0.0
                for key, (times, values, interpolation) in before_tracks.items():
                    new_times, new_values, new_interpolation = after_tracks[key]
                    require(times == new_times and interpolation == new_interpolation,
                            'sampling repair changed a reaction interpolation or key time')
                    delta = max(delta, max(abs(a-b) for old, new in zip(values, new_values)
                                           for a, b in zip(old, new)))
                require(delta <= 1e-6, 'reaction differs beyond the measured float32 sampling repair')
                parents, order = review.library.node_order(current[0])
                world_delta = 0.0
                keys = sorted(before_keys)
                for seconds in [*keys, *((a+b)/2 for a, b in zip(keys, keys[1:]))]:
                    old_world = review.profiles.pose_world(previous[0], before_tracks, seconds, parents, order)
                    new_world = review.profiles.pose_world(current[0], after_tracks, seconds, parents, order)
                    world_delta = max(world_delta, max(abs(old_world[index][r][c] - new_world[index][r][c])
                                      for index in old_world for r in range(4) for c in range(4)))
                require(world_delta <= 1e-5, 'reaction world pose changed beyond numerical sampling repair')
                numeric[clip_name] = {'raw_TRS_max_component_delta': delta,
                                      'joint_world_matrix_max_component_delta': world_delta,
                                      'actual_keys_and_midpoints': len(keys) * 2 - 1,
                                      'source_grid_and_interpolation_unchanged': True}
            row['changed_clips'][item['file']] = changed
            row.setdefault('exact_key_sampling_numeric_repair', {})[item['file']] = numeric
        prepared = bank / (target + '_prepared_png.glb')
        profile_path = bank / (target + '_attack_profiles.json')
        pins[str(profile_path.relative_to(REPO))] = review.sha(profile_path)
        profile = json.loads(profile_path.read_text())
        asset = review.library.read_glb(prepared)
        body = profile['proxy_calibration']['measurement']['body_primitive_indices']
        for clip_name, times in POSES.items():
            surface = review.ActualTargetSurface(asset, body, clip_name)
            frames = []
            row['clips'][clip_name] = frames
            for seconds in times:
                frame = surface.evaluate(seconds)
                frames.append(frame)
                print('FAMILY_TARGET', target, clip_name, seconds, 'steel',
                      sum(item['triangle_pair_count'] for item in frame['steel_fullbody_intersections']),
                      'core', frame['nonadjacent_region_triangle_pairs'], flush=True)
            save(report_path, report)
        review.render_target(target, prepared, row,
                             (('idle', 0.0, 'natural_guard'), ('attack_overhead', .68, 'overhead_load')))
        save(report_path, report)
    for path, digest in pins.items():
        require(review.sha(REPO / path) == digest, 'review input changed during execution: ' + path)
    report['intersection_pose_counts'] = {
        row['target']: sum(bool(frame['steel_fullbody_intersections']) or
                           any(frame['nonadjacent_region_triangle_pairs'].values())
                           for frames in row['clips'].values() for frame in frames)
        for row in report['targets']
    }
    report['status'] = ('finite_actual_target_checks_passed_pending_Root_visual_review'
                        if not any(report['intersection_pose_counts'].values())
                        else 'finite_actual_target_checks_failed_not_approved')
    save(report_path, report)
    require(not any(report['intersection_pose_counts'].values()), 'actual target intersections need Root review')
    print('FAMILY_REVIEW_COMPLETE', report['intersection_pose_counts'], flush=True)


if __name__ == '__main__':
    main()
