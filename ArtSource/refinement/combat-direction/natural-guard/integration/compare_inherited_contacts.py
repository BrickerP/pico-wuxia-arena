"""Compare newly sampled failing poses against the unchanged previous target bank."""
import importlib.util
import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[5]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bank', type=Path, required=True)
parser.add_argument('--review', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else None)
bank = args.bank.resolve()
helper_path = REPO / 'ArtSource/refinement/combat-direction/native-weighted-overhead/integration/review_candidate.py'
spec = importlib.util.spec_from_file_location('actual_surface_comparison', helper_path)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)
source = args.review.resolve()
report = json.loads(source.read_text())
request_path = bank / 'production_review_request.json'
if json.loads(request_path.read_text())['binding_sha256'] != report['binding_sha256']:
    raise ValueError('bank identity differs from the target review')
rows = []
pins = {str(path.relative_to(REPO)): review.sha(path) for path in (source, request_path, Path(__file__), helper_path)}
for target in report['targets']:
    name = target['target']
    new_path = bank / (name + '_prepared_png.glb')
    old_path = review.FORMAL / (name + '_prepared_png.glb')
    profile_path = bank / (name + '_attack_profiles.json')
    body = json.loads(profile_path.read_text())['proxy_calibration']['measurement']['body_primitive_indices']
    old, new = review.library.read_glb(old_path), review.library.read_glb(new_path)
    for path in (old_path, new_path, profile_path):
        pins[str(path.relative_to(REPO))] = review.sha(path)
    for clip, frames in target['clips'].items():
        failures = [f for f in frames if f['steel_fullbody_intersections'] or any(f['nonadjacent_region_triangle_pairs'].values())]
        if not failures:
            continue
        surface = review.ActualTargetSurface(old, body, clip)
        _, old_tracks, _ = review.clip(*old, clip)
        _, new_tracks, _ = review.clip(*new, clip)
        parents, order = review.library.node_order(old[0])
        for failure in failures:
            seconds = failure['source_seconds']
            baseline = surface.evaluate(seconds)
            before = review.profiles.pose_world(old[0], old_tracks, seconds, parents, order)
            after = review.profiles.pose_world(new[0], new_tracks, seconds, parents, order)
            error = max(abs(before[index][r][c] - after[index][r][c]) for index in before for r in range(4) for c in range(4))
            rows.append({'target': name, 'clip': clip, 'source_seconds': seconds,
                         'new_core_pairs': failure['nonadjacent_region_triangle_pairs'],
                         'previous_core_pairs': baseline['nonadjacent_region_triangle_pairs'],
                         'new_steel': failure['steel_fullbody_intersections'],
                         'previous_steel': baseline['steel_fullbody_intersections'],
                         'joint_world_matrix_max_component_difference': error,
                         'identical_sampled_contacts': baseline['nonadjacent_region_triangle_pairs'] == failure['nonadjacent_region_triangle_pairs']
                             and baseline['steel_fullbody_intersections'] == failure['steel_fullbody_intersections']})
for path, digest in pins.items():
    if review.sha(REPO / path) != digest:
        raise ValueError('comparison input changed: ' + path)
result = {'scope': 'Only the finite poses that failed the new target review; not a clearance approval.',
          'baseline_binding_sha256': json.loads((review.FORMAL / 'production_review_request.json').read_text())['binding_sha256'],
          'binding_sha256': report['binding_sha256'], 'pins': pins, 'poses': rows,
          'all_failed_poses_have_identical_previous_contacts': all(row['identical_sampled_contacts'] for row in rows)}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
