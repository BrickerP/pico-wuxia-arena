"""Review this actual canonical export using the existing family/surface tools."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / 'ArtSource/tripo-warrior'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


family = load('existing_family_review', HERE.parent / 'review_family.py')
r = load('existing_actual_target_review', family.HELPER)
import numpy as np
from attack_grounding import foot_surface, surface_heights

BANK = HERE / 'candidate-library'
OUT = HERE / 'target-review'
FORMAL = REPO / 'ArtSource/tripo-warrior/library'


def mmatrix(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(4) for j in range(4))


def main():
    OUT.mkdir(exist_ok=True)
    r.OUT = OUT
    request_path = BANK / 'production_review_request.json'
    request = json.loads(request_path.read_bytes())
    manifest = json.loads((HERE / 'motion_library_candidate.json').read_bytes())
    r.require(request['status'] == 'pending_root_review', 'not a private pending bank')
    r.require(r.library.canonical_hash(r.library.production_binding(manifest)) == request['binding_sha256']
              == r.library.canonical_hash(request['binding']), 'candidate binding mismatch')
    paths = [Path(__file__), HERE / 'prepare_candidate.py', HERE.parent / 'review_family.py', family.HELPER,
             Path(r.library.__file__), Path(r.profiles.__file__), Path(r.UTILITY.__file__),
             HERE / 'motion_library_candidate.json', HERE / 'attack_bank_inputs.json', request_path,
             REPO / 'ArtSource/tripo-warrior/production_contract.py',
             REPO / 'ArtSource/tripo-warrior/attack_grounding.py']
    pins = {str(p.relative_to(REPO)): r.sha(p) for p in paths}
    report = {'status': 'actual_canonical_RIGHT_only_review_in_progress',
        'binding_sha256': request['binding_sha256'], 'left_integrated': False,
        'source_pins': pins, 'targets': [], 'limits': [
            'Finite actual exported target poses; not continuous-time or SDK skinned-mesh proof.',
            'Steel against full body plus eight nonadjacent forearm/hand versus head/chest region pairs.',
            'Region test excludes adjacent upperarm/chest, mixed dominant-weight seam triangles and clothing-layer self intersections.',
            'Original LEFT is retained and known unresolved; any full-family collision is reported as a failure.',
            'RIGHT joining .9s second-difference spike remains disclosed by the sealed source handoff.',
            'Original material renders are offline Blender evidence, not PICO or Space Pro acceptance.']}
    save = lambda: r.save(OUT / 'review_report.json', report)
    for target in family.TARGETS:
        receipt = next(row for row in request['characters'] if row['id'] == target)
        row = {'target': target, 'static_preservation': {}, 'changed_clips': {}, 'clips': {}}
        report['targets'].append(row)
        for item in receipt['outputs']:
            current_path, previous_path = BANK / item['file'], FORMAL / item['file']
            r.require(current_path.stat().st_size == item['bytes'] and r.sha(current_path) == item['sha256'],
                      'receipt differs: ' + item['file'])
            pins[str(current_path.relative_to(REPO))] = r.sha(current_path)
            pins[str(previous_path.relative_to(REPO))] = r.sha(previous_path)
            current, previous = r.library.read_glb(current_path), r.library.read_glb(previous_path)
            a, b = r.static_signature(*current), r.static_signature(*previous)
            checks = {k: a[k] == b[k] for k in a}
            r.require(all(checks.values()), 'static target geometry/rest/skin/material drift: ' + item['file'])
            old_clips = {c['name']: r.library.animation_signature(*previous, c) for c in previous[0]['animations']}
            new_clips = {c['name']: r.library.animation_signature(*current, c) for c in current[0]['animations']}
            r.require(len(old_clips) == len(new_clips) == 10 and old_clips.keys() == new_clips.keys(), 'ten clips required')
            changed = sorted(k for k in new_clips if old_clips[k] != new_clips[k])
            r.require(changed == ['attack_right'], 'only RIGHT may change: ' + str(changed))
            row['static_preservation'][item['file']] = checks
            row['changed_clips'][item['file']] = changed
        prepared = BANK / (target + '_prepared_png.glb')
        asset, old_asset = r.library.read_glb(prepared), r.library.read_glb(FORMAL / prepared.name)
        r.png_encoding_proof(asset, r.library.read_glb(BANK / (target + '.glb')))
        profile_path = BANK / (target + '_attack_profiles.json')
        profile = json.loads(profile_path.read_bytes())
        pins[str(profile_path.relative_to(REPO))] = r.sha(profile_path)
        d, binary = asset
        _, old_tracks, old_keys = r.clip(*old_asset, 'attack_right')
        _, tracks, keys = r.clip(*asset, 'attack_right')
        r.require(len(tracks) == 234 and keys == old_keys and old_tracks.keys() == tracks.keys(), '234 TRS/time grid differs')
        times = sorted(set(keys) | {(a+b)/2 for a,b in zip(sorted(keys), sorted(keys)[1:])})
        parents, order = r.library.node_order(d)
        names = {n.get('name'): i for i,n in enumerate(d['nodes'])}
        _, idle_tracks, _ = r.clip(*asset, 'idle')
        endpoint_delta = 0.
        for t in [min(keys), max(keys)]:
            for key, (_, values, _) in tracks.items():
                path = key[1]
                a = np.array(r.profiles.sample_track(tracks[key],t,path=='rotation'))
                b = np.array(r.profiles.sample_track(idle_tracks[key],0,path=='rotation'))
                error = min(float(np.max(np.abs(a-b))),float(np.max(np.abs(a+b)))) if path=='rotation' else float(np.max(np.abs(a-b)))
                endpoint_delta = max(endpoint_delta,error)
        r.require(endpoint_delta <= 1e-6, 'new guard endpoint mismatch')
        surface = foot_surface(d,binary,parents,names['BoneRoot'])
        steel = r.UTILITY.surface(*asset)
        joint_ids = d['skins'][0]['joints']
        edges = [(parents[i],i) for i in joint_ids if parents.get(i) in joint_ids]
        old_lengths = None
        preservation = {'steel_vertex_max_component_delta_m': 0., 'head_world_max_component_delta': 0.,
            'right_wrist_world_max_component_delta': 0., 'same_time_bone_length_max_delta_m': 0.,
            'temporal_bone_length_max_delta_m': 0., 'foot_height_max_delta_m': 0.}
        foot_rows = []
        for t in times:
            w = r.profiles.pose_world(d,tracks,t,parents,order)
            old = r.profiles.pose_world(d,old_tracks,t,parents,order)
            for a,b in zip(r.UTILITY.steel_points(steel,w),r.UTILITY.steel_points(steel,old)):
                preservation['steel_vertex_max_component_delta_m'] = max(preservation['steel_vertex_max_component_delta_m'],float(np.max(np.abs(a[2]-b[2]))))
            for name,field in [('Head','head_world_max_component_delta'),('R_Hand','right_wrist_world_max_component_delta')]:
                preservation[field] = max(preservation[field],mmatrix(w[names[name]],old[names[name]]))
            lengths = [(w[b].translation-w[a].translation).length for a,b in edges]
            old_lengths = old_lengths or lengths
            preservation['temporal_bone_length_max_delta_m'] = max(preservation['temporal_bone_length_max_delta_m'],max(abs(a-b) for a,b in zip(lengths,old_lengths)))
            preservation['same_time_bone_length_max_delta_m'] = max(preservation['same_time_bone_length_max_delta_m'],max(abs(length-(old[b].translation-old[a].translation).length) for length,(a,b) in zip(lengths,edges)))
            feet, old_feet = surface_heights(d,w,surface),surface_heights(d,old,surface)
            preservation['foot_height_max_delta_m'] = max(preservation['foot_height_max_delta_m'],max(abs(feet[s]-old_feet[s]) for s in feet))
            foot_rows.append({'source_seconds':t,'foot_min_metres':feet,'plane_residual_metres':{s:h+.028 for s,h in feet.items()}})
        r.require(preservation['steel_vertex_max_component_delta_m'] == 0., 'dynamic Steel curve changed')
        r.require(preservation['head_world_max_component_delta'] == preservation['right_wrist_world_max_component_delta'] == 0., 'protected head/right wrist changed')
        r.require(preservation['foot_height_max_delta_m'] == 0. and preservation['same_time_bone_length_max_delta_m'] < 1e-5 and preservation['temporal_bone_length_max_delta_m'] < 1e-5, 'bone/grounding changed')
        align = json.loads((BANK / (target+'_alignment.json')).read_bytes())
        old_align = json.loads((FORMAL / (target+'_alignment.json')).read_bytes())
        def grounding_measurements(alignment):
            value = copy.deepcopy(alignment['canonical_root_grounding'])
            for clip in value['clips']:
                clip.pop('before_semantics_sha256', None)
                clip.pop('after_semantics_sha256', None)
            return value
        r.require(grounding_measurements(align) == grounding_measurements(old_align), 'grounding policy or measured shift changed')
        row['motion_preservation'] = {'key_and_midpoint_count':len(times),'track_count':len(tracks),
            'bone_edges':len(edges),'all_234_TRS_guard_endpoint_max_component_delta':endpoint_delta,
            **preservation,'grounding_measurements_identical_to_formal_excluding_clip_hashes':True,'right_foot_measurements':foot_rows}
        poses = copy.deepcopy(family.POSES)
        source_report = json.loads((REPO / 'ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/verification.json').read_bytes())
        sealed_window = [f['source_seconds'] for f in source_report['targets'][0]['collisions']]
        poses['attack_right'] = sorted(set(poses['attack_right']) | {t for t in times if .85<=t<=1.55} | set(sealed_window))
        # Include the known LEFT late-contact/return failure locations explicitly.
        poses['attack_left'] = sorted(set(poses['attack_left']) | {.85,.95,1.,1.05,1.15,1.2,1.25,1.3})
        for clip_name, sample_times in poses.items():
            actual = r.ActualTargetSurface(asset,profile['proxy_calibration']['measurement']['body_primitive_indices'],clip_name)
            frames = row['clips'][clip_name] = []
            for t in sample_times:
                frame = actual.evaluate(t)
                frames.append(frame)
                if frame['steel_fullbody_intersections'] or any(frame['nonadjacent_region_triangle_pairs'].values()):
                    print('CONTACT',target,clip_name,t,frame['nonadjacent_region_triangle_pairs'],flush=True)
            print('REVIEW_CLIP',target,clip_name,'poses',len(frames),'contacts',sum(bool(f['steel_fullbody_intersections']) or any(f['nonadjacent_region_triangle_pairs'].values()) for f in frames),flush=True)
            save()
        r.render_target(target,prepared,row,(('idle',0.,'natural_guard'),('attack_right',1.,'RIGHT_contact'),('attack_right',1.15,'RIGHT_return')))
        save()
    for path,digest in pins.items():
        r.require(r.sha(REPO/path)==digest,'input changed during review: '+path)
    report['intersection_pose_counts'] = {row['target']:{name:sum(bool(f['steel_fullbody_intersections']) or any(f['nonadjacent_region_triangle_pairs'].values()) for f in frames) for name,frames in row['clips'].items()} for row in report['targets']}
    right_pass = all(row['attack_right']==0 for row in report['intersection_pose_counts'].values())
    report['RIGHT_finite_gate_passed'] = right_pass
    report['status'] = 'RIGHT_finite_passed_full_family_LEFT_failed_not_approved' if right_pass else 'RIGHT_finite_failed_not_approved'
    save()
    print('REVIEW_COMPLETE',json.dumps(report['intersection_pose_counts']),flush=True)
    r.require(right_pass,'RIGHT actual target intersections remain')


if __name__ == '__main__':
    main()
