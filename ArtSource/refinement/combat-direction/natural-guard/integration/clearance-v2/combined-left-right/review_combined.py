"""Actual combined bank checks against the immutable c300 target references."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base=load('clearance_actual_tools',HERE.parent/'review_candidate.py')
r,family=base.r,base.family
import numpy as np
from attack_grounding import foot_surface,surface_heights
import target_wrist_constraint as solver

BANK=HERE/'candidate-library'
FORMAL=REPO/'ArtSource/tripo-warrior/library'
OUT=HERE/'target-review'
ALLOWED={('R_Upperarm','rotation'),('R_Forearm','rotation'),('R_Hand','rotation')}


def difference(a,b):
    return float(np.max(np.abs(np.asarray(a)-np.asarray(b))))


def review_motion(target,asset,previous,clip_name):
    doc,binary=asset
    _,tracks,keys=r.clip(*asset,clip_name)
    _,old_tracks,old_keys=r.clip(*previous,clip_name)
    names={n['name']:i for i,n in enumerate(doc['nodes'])}
    parents,order=r.library.node_order(doc)
    r.require(len(tracks)==len(old_tracks)==234 and tracks.keys()==old_tracks.keys(),'234 TRS mismatch')
    changed=[]
    for key,track in tracks.items():
        if track!=old_tracks[key]:
            role=(doc['nodes'][key[0]]['name'],key[1])
            changed.append('/'.join(role))
            r.require(target=='veteran' and clip_name=='attack_left' and role in ALLOWED,'unexpected prepared TRS change')
            r.require(len(track[0])==130 and len(old_tracks[key][0])==106 and track[2]=='LINEAR','three rotation density must be130')
    if target=='veteran' and clip_name=='attack_left':
        r.require(set(changed)=={'/'.join(v) for v in ALLOWED},'exactly three prepared rotations must change')
    else:
        r.require(not changed and keys==old_keys,'protected animation changed')
    key_times=sorted(keys)
    times=sorted(set(key_times)|{(a+b)/2 for a,b in zip(key_times,key_times[1:])})
    hand_points=solver.combined_steel_hand_points(doc,binary)
    r.require(hand_points.shape==(5533,4),'actual Steel reference is incomplete')
    steel=r.UTILITY.surface(doc,binary)
    r.require(sum(len(p[2]) for p in steel[2])==5533,'actual Steel LBS count differs')
    _,idle,_=r.clip(*asset,'idle')
    endpoint=0.
    for t in (0.,1.75):
        for key,track in tracks.items():
            rotation=key[1]=='rotation'
            a=np.array(r.profiles.sample_track(track,t,rotation))
            b=np.array(r.profiles.sample_track(idle[key],0.,rotation))
            endpoint=max(endpoint,min(float(np.max(np.abs(a-b))),float(np.max(np.abs(a+b)))) if rotation else float(np.max(np.abs(a-b))))
    r.require(endpoint<=1e-6,'234 guard endpoint differs')
    feet=foot_surface(doc,binary,parents,names['BoneRoot'])
    joints=doc['skins'][0]['joints']
    edges=[(parents[i],i) for i in joints if parents.get(i) in joints]
    report={'track_count':234,'key_union_count':len(keys),'old_key_union_count':len(old_keys),
        'key_and_midpoint_count':len(times),'changed_tracks':changed,'steel_vertex_count':5533,
        'all_234_guard_endpoint_max_component_delta':endpoint,
        'key_steel_max_m':0.,'subkey_steel_max_m':0.,'key_wrist_max_m':0.,'subkey_wrist_max_m':0.,
        'key_wrist_orientation_radians':0.,'subkey_wrist_orientation_radians':0.,
        'key_wrist_orientation_at_steel_radius_m':0.,'subkey_wrist_orientation_at_steel_radius_m':0.,
        'head_root_hip_foot_world_max_component_delta':0.,'foot_surface_max_delta_m':0.,
        'all77_bone_length_max_same_time_delta_m':0.,'all77_bone_length_max_temporal_delta_m':0.,'frames':[]}
    initial_lengths=None
    for t in times:
        world=r.profiles.pose_world(doc,tracks,t,parents,order)
        old=r.profiles.pose_world(previous[0],old_tracks,t,parents,order)
        key=t in keys
        prefix='key_' if key else 'subkey_'
        points=r.UTILITY.steel_points(steel,world)
        old_points=r.UTILITY.steel_points(steel,old)
        error=max(float(np.max(np.linalg.norm(a[2]-b[2],axis=1))) for a,b in zip(points,old_points))
        wrist=(world[names['R_Hand']].translation-old[names['R_Hand']].translation).length
        # Complete rigid orientation, measured independently of acos rounding.
        qa=np.asarray(world[names['R_Hand']].to_quaternion(),dtype=float)
        qb=np.asarray(old[names['R_Hand']].to_quaternion(),dtype=float)
        qa/=np.linalg.norm(qa);qb/=np.linalg.norm(qb)
        if np.dot(qa,qb)<0:qa=-qa
        angle=4*math.atan2(float(np.linalg.norm(qa-qb)),float(np.linalg.norm(qa+qb)))
        radius=max(float(np.max(np.linalg.norm(p[2]-np.asarray(old[names['R_Hand']].translation),axis=1))) for p in old_points)
        for field,value in [('steel_max_m',error),('wrist_max_m',wrist),('wrist_orientation_radians',angle),('wrist_orientation_at_steel_radius_m',2*radius*math.sin(angle/2))]:
            report[prefix+field]=max(report[prefix+field],value)
        protected=max(difference(world[names[n]],old[names[n]]) for n in ['Head','BoneRoot','Hip','L_Foot','R_Foot'])
        report['head_root_hip_foot_world_max_component_delta']=max(report['head_root_hip_foot_world_max_component_delta'],protected)
        lengths=[(world[b].translation-world[a].translation).length for a,b in edges]
        if initial_lengths is None:initial_lengths=lengths
        same=max(abs(v-(old[b].translation-old[a].translation).length) for v,(a,b) in zip(lengths,edges))
        temporal=max(abs(v-u) for v,u in zip(lengths,initial_lengths))
        report['all77_bone_length_max_same_time_delta_m']=max(report['all77_bone_length_max_same_time_delta_m'],same)
        report['all77_bone_length_max_temporal_delta_m']=max(report['all77_bone_length_max_temporal_delta_m'],temporal)
        new_feet,old_feet=surface_heights(doc,world,feet),surface_heights(doc,old,feet)
        foot_error=max(abs(new_feet[s]-old_feet[s]) for s in new_feet)
        report['foot_surface_max_delta_m']=max(report['foot_surface_max_delta_m'],foot_error)
        report['frames'].append({'source_seconds':t,'stored_key':key,'full_steel_max_m':error,
            'full_wrist_orientation_radians':angle,'foot_plane_residual_metres':{s:y+.028 for s,y in new_feet.items()}})
    r.require(report['head_root_hip_foot_world_max_component_delta']==report['foot_surface_max_delta_m']==0.,'protected world/feet changed')
    r.require(report['all77_bone_length_max_same_time_delta_m']<=1e-6 and report['all77_bone_length_max_temporal_delta_m']<=1e-6,'bone length changed')
    for role,budget in [('key_',5e-6),('subkey_',.001)]:
        for field in ['steel_max_m','wrist_max_m','wrist_orientation_at_steel_radius_m']:
            r.require(report[role+field]<=budget,'strict dynamic '+role+field+' budget exceeded')
    if not changed:
        r.require(report['key_steel_max_m']==report['subkey_steel_max_m']==0.,'unchanged clip Steel must remain exactly zero difference')
    return report


def main():
    OUT.mkdir(exist_ok=True)
    r.OUT=OUT
    inputs=json.loads((HERE/'input_receipt.json').read_bytes())
    request=json.loads((BANK/'production_review_request.json').read_bytes())
    reference=json.loads((HERE/'reference_request_c300.json').read_bytes())
    r.require(request['status']=='pending_root_review' and request['binding_sha256']==inputs['expected_binding_sha256']==r.library.canonical_hash(request['binding']),'candidate binding differs')
    r.require(reference['binding_sha256']=='c3009af39766bf9dce50181db351b356999aaafc3761ca8eea7f8f4012162f31','reference is not c300')
    paths=[Path(__file__),Path(base.__file__),Path(family.__file__),Path(r.__file__),Path(r.library.__file__),
        Path(r.profiles.__file__),Path(r.UTILITY.__file__),Path(solver.__file__),Path(r.DIRECT.__file__),
        Path(r.STUDIO.__file__),Path(r.EYE.__file__),Path(r.COMMON.__file__),r.CAMERA,
        HERE/'motion_library_candidate.json',BANK/'production_review_request.json',HERE/'reference_request_c300.json']
    pins={str(p.relative_to(REPO)):r.sha(p) for p in paths}
    for item in inputs['pins']:
        r.require(r.sha(REPO/item['file'])==item['sha256'],'pinned producer/reference changed: '+item['file'])
        pins[item['file']]=item['sha256']
    report={'status':'actual_combined_review_in_progress','binding_sha256':request['binding_sha256'],
        'reference_binding_sha256':reference['binding_sha256'],'source_pins':pins,'targets':[],
        'limits':['Finite actual exported target samples, not continuous-time proof or native SDK skinned playback.',
            'Eight regions are dominant-weight-only nonadjacent forearm/hand vs head/chest; adjacent upperarm/chest, mixed-weight seams and cloth-layer self intersections excluded.',
            'Existing foot-plane residuals retained; grounding preservation does not establish dual-foot contact.',
            'Original target hand shapes, sleeve/cuff roughness and armor geometry remain unchanged.',
            'RIGHT .9s local second-difference source limitation remains; no aesthetics or native acceptance.']}
    save=lambda:r.save(OUT/'review_report.json',report)
    for target in family.TARGETS:
        row={'target':target,'static_preservation':{},'changed_clips':{},'motion':{},'clips':{}}
        report['targets'].append(row)
        receipt=next(t for t in request['characters'] if t['id']==target)
        expected=['attack_left'] if target=='veteran' else []
        for item in receipt['outputs']:
            path,oldpath=BANK/item['file'],FORMAL/item['file']
            r.require(r.sha(path)==item['sha256'] and path.stat().st_size==item['bytes'],'output receipt mismatch')
            pins[str(path.relative_to(REPO))]=r.sha(path)
            current,old=r.library.read_glb(path),r.library.read_glb(oldpath)
            a,b=r.static_signature(*current),r.static_signature(*old)
            checks={k:a[k]==b[k] for k in a}
            r.require(all(checks.values()),'geometry/rest/skin/material changed '+item['file'])
            old_sig={c['name']:r.library.animation_signature(*old,c) for c in old[0]['animations']}
            new_sig={c['name']:r.library.animation_signature(*current,c) for c in current[0]['animations']}
            r.require(old_sig.keys()==new_sig.keys() and len(new_sig)==10,'ten clip bank changed')
            changed=sorted(k for k,v in new_sig.items() if old_sig[k]!=v)
            r.require(changed==expected,'unexpected changed clip set '+item['file']+str(changed))
            if not expected:r.require(path.read_bytes()==oldpath.read_bytes(),'base/indigo GLB must remain exact bytes')
            row['changed_clips'][item['file']]=changed
            row['static_preservation'][item['file']]=checks
        asset=r.library.read_glb(BANK/(target+'_prepared_png.glb'))
        previous=r.library.read_glb(FORMAL/(target+'_prepared_png.glb'))
        row['png_ktx_preservation']=r.png_encoding_proof(asset,r.library.read_glb(BANK/(target+'.glb')))
        profile_path=BANK/(target+'_attack_profiles.json')
        profile=json.loads(profile_path.read_bytes())
        pins[str(profile_path.relative_to(REPO))]=r.sha(profile_path)
        for clip in ['attack_left','attack_right']:
            row['motion'][clip]=review_motion(target,asset,previous,clip)
        for clip in ['attack_left','attack_right']:
            body=r.library.read_glb(BANK/(target+'_body.glb'))
            r.require(r.library.animation_signature(*body,next(a for a in body[0]['animations'] if a['name']==clip))==r.library.animation_signature(*asset,next(a for a in asset[0]['animations'] if a['name']==clip)),'body/combined curve mismatch')
        alignment=json.loads((BANK/(target+'_alignment.json')).read_bytes())
        row['canonical_producer_wrist_report']=alignment['prepared_wrist_constraint']
        r.require(alignment['prepared_wrist_constraint']['combined_rigid_steel_vertex_count']==5533,'canonical producer did not validate Steel')
        poses=copy.deepcopy(family.POSES)
        old_review=json.loads((HERE.parent/'target-review/review_report.json').read_bytes())
        poses['attack_right']=[f['source_seconds'] for f in next(t for t in old_review['targets'] if t['target']==target)['clips']['attack_right']]
        left_times=[i/120 for i in range(108,157)]
        left_times += [f['source_seconds'] for f in row['motion']['attack_left']['frames'] if .9<=f['source_seconds']<=1.3]
        poses['attack_left']=sorted(set(poses['attack_left'])|set(left_times)|{.9,.95,1.,1.05,1.06,1.1,1.15,1.2,1.235,1.25,1.3})
        for clip,times in poses.items():
            surface=r.ActualTargetSurface(asset,profile['proxy_calibration']['measurement']['body_primitive_indices'],clip)
            frames=row['clips'][clip]=[]
            for t in times:
                f=surface.evaluate(t)
                frames.append(f)
                if f['steel_fullbody_intersections'] or any(f['nonadjacent_region_triangle_pairs'].values()):
                    print('CONTACT',target,clip,t,f['nonadjacent_region_triangle_pairs'],flush=True)
            print('COMBINED_CLIP',target,clip,'poses',len(frames),'contacts',sum(bool(f['steel_fullbody_intersections']) or any(f['nonadjacent_region_triangle_pairs'].values()) for f in frames),flush=True)
            save()
        if target=='veteran':
            r.render_target(target,BANK/(target+'_prepared_png.glb'),row,(('idle',0.,'guard'),('attack_left',1.1,'LEFT_1p1'),('attack_left',1.2,'LEFT_1p2'),('attack_left',1.75,'LEFT_return')))
        save()
    # Exercise the three permanent public integration admission tests on the actual tree.
    test_module=load('actual_public_pipeline_tests',REPO/'ArtSource/tripo-warrior/test_attack_bank_pipeline.py')
    names=['test_prepared_wrist_requires_actual_combined_steel_before_writing',
        'test_prepared_wrist_rejects_normalized_steel_weight_outside_hand',
        'test_prepared_wrist_recipe_and_implementation_are_binding_inputs']
    suite=unittest.TestSuite(test_module.AttackBankContracts(name) for name in names)
    with (OUT/'public_contract_tests.txt').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    report['public_contract_tests']={'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}
    r.require(result.wasSuccessful(),'public admission tests failed')
    for path,pin in pins.items():r.require(r.sha(REPO/path)==pin,'input drift during actual review: '+path)
    report['intersection_pose_counts']={t['target']:{clip:sum(bool(f['steel_fullbody_intersections']) or any(f['nonadjacent_region_triangle_pairs'].values()) for f in frames) for clip,frames in t['clips'].items()} for t in report['targets']}
    passed=not any(v for clips in report['intersection_pose_counts'].values() for v in clips.values())
    report['status']='finite_combined_checks_passed_pending_Root_visual_native_review' if passed else 'finite_combined_checks_failed_not_approved'
    save()
    print('COMBINED_REVIEW_COMPLETE',report['intersection_pose_counts'],flush=True)
    r.require(passed,'actual combined target intersections remain')


if __name__=='__main__':main()
