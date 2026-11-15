"""Verify final v4 raw delta and the actual once-retargeted veteran target."""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1]
sys.path.insert(0,str(LANE))
import build_weighted_overhead as b
import numpy as np
review=b.load_module('v4_actual_target_review',LANE/'integration/review_candidate.py')

def require(condition,message):
    if not condition:raise ValueError(message)
def clip(doc,binary):return review.clip(doc,binary,'attack_overhead')[1:]
def max_delta(a,c,path):
    d=max(abs(x-y) for x,y in zip(a,c))
    return min(d,max(abs(x+y) for x,y in zip(a,c))) if path=='rotation' else d

def main():
    meta=json.loads((OUT/'weighted_overhead_authoring.json').read_text())
    raw,rb=b.library.read_glb(OUT/'weighted_overhead_raw.glb');parent,pb=b.library.read_glb(b.SOURCE)
    rt,keys=b.library.decode_animation(raw,rb);pt,pkeys=b.library.decode_animation(parent,pb)
    require(len(rt)==234 and len(keys)==211 and len(raw['skins'][0]['joints'])==78 and keys==pkeys,'RAW complete234/78/211120Hz grid drift')
    require(keys[0]==0 and keys[-1]==1.75 and all(r[0]==keys and r[2]=='LINEAR' for r in rt.values()),'RAW timeline/interpolation drift')
    for field in ('nodes','skins','meshes','materials','images','textures','bufferViews','accessors'):require(raw[field]==parent[field],'RAW nonanimation JSON drift:'+field)
    require(len(rb)==len(pb),'RAW binary layout changed')
    names={n.get('name'):i for i,n in enumerate(raw['nodes'])};changed=[];diff_bytes=set(np.flatnonzero(np.frombuffer(rb,dtype=np.uint8)!=np.frombuffer(pb,dtype=np.uint8)).tolist());allowed=set()
    animation=raw['animations'][0]
    for key,row in rt.items():
        n,path=key
        require(np.isfinite(np.array(row[1])).all(),'nonfinite RAW curve')
        require(row[1][0]==row[1][-1]==pt[key][1][0],'RAW guard closure changed')
        if row[1]!=pt[key][1]:
            changed.append(raw['nodes'][n]['name']+'.'+path)
            require(raw['nodes'][n]['name'] in b.BONES and path=='rotation','non-target RAW stream changed')
            c=next(c for c in animation['channels'] if c['target']=={'node':n,'path':path});a=raw['accessors'][animation['samplers'][c['sampler']]['output']];v=raw['bufferViews'][a['bufferView']];start=v.get('byteOffset',0)+a.get('byteOffset',0)
            for k,t in enumerate(keys):
                if row[1][k]!=pt[key][1][k]:
                    require(b.weight(float(t))>0,'RAW key outside open bounded window changed')
                    allowed.update(range(start+k*16,start+(k+1)*16))
    require(set(changed)=={n+'.rotation' for n in b.BONES},'unexpected changed RAW channels')
    require(diff_bytes<=allowed,'RAW non-target payload bytes changed')
    # The actual production-before OH must match our native retarget+finger+
    # target-idle-grounding reproduction before the after-target can be trusted.
    before=b.library.read_glb(b.TARGET_BEFORE)
    reproduced=b.library.read_glb(OUT/'veteran_v3_reproduction_prepared_png.glb')
    after=b.library.read_glb(OUT/'veteran_prepared_png.glb')
    oldtracks,_=clip(*before);reprotracks,_=clip(*reproduced);newtracks,newtimes=clip(*after)
    nmap={n.get('name'):i for i,n in enumerate(before[0]['nodes'])};rmap={n.get('name'):i for i,n in enumerate(reproduced[0]['nodes'])};amap={n.get('name'):i for i,n in enumerate(after[0]['nodes'])}
    reproduction_error=0.;unchanged_error=0.
    for (i,path),track in oldtracks.items():
        name=before[0]['nodes'][i]['name'];repro=reprotracks[rmap[name],path]
        for a,c in zip(track[1],repro[1]):reproduction_error=max(reproduction_error,max_delta(a,c,path))
        require(track[0]==repro[0] and len(track[1])==len(repro[1]),'reproduction grid drift')
        if name not in b.BONES:
            for a,c in zip(track[1],newtracks[amap[name],path][1]):unchanged_error=max(unchanged_error,max_delta(a,c,path))
    require(reproduction_error<2e-6,'actual veteran v3 OH reproduction drift:'+str(reproduction_error))
    require(unchanged_error<2e-6,'actual veteran non-right-arm track drift:'+str(unchanged_error))
    static_before=review.static_signature(*before);static_after=review.static_signature(*after)
    static_checks={key:static_before[key]==static_after[key] for key in static_before}
    require(all(static_checks.values()),'actual veteran rest/mesh/skin/weights/grip/material drift:'+str(static_checks))
    old=review.ActualTargetSurface(before,[0]);repro=review.ActualTargetSurface(reproduced,[0]);new=review.ActualTargetSurface(after,[0])
    r0=old.evaluate(.9);rr=repro.evaluate(.9);r1=new.evaluate(.9)
    require(r0['nonadjacent_region_triangle_pairs']['R_hand__head']==rr['nonadjacent_region_triangle_pairs']['R_hand__head']==4,'actual4pair reproduction did not hold')
    require(not any(r1['nonadjacent_region_triangle_pairs'].values()) and not r1['steel_fullbody_intersections'],'first v4 correction failed at true veteran.9')
    print('V4_TRUE_VETERAN_0p9_CLEAR',flush=True)
    times=sorted(set([i/30 for i in range(53)]+[.68,.82,.86,.9,.94,.9667,1.,31/30,1.15,1.27,1.34,1.4,1.42,1.5,1.55,1.75]))
    rows=[]
    for t in times:
        r=r1 if t==.9 else new.evaluate(t)
        rows.append(r)
        print('V4_TARGET_CHECK',t,'steel',len(r['steel_fullbody_intersections']),'body',sum(r['nonadjacent_region_triangle_pairs'].values()),flush=True)
    bad=[r for r in rows if r['steel_fullbody_intersections'] or any(r['nonadjacent_region_triangle_pairs'].values())]
    def joint_metrics(asset,surface):
        doc=asset[0];names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
        world=review.profiles.pose_world(doc,surface.tracks,.9,surface.parents,surface.order)
        return {name:list(world[names[name]].translation) for name in ('R_Hand','R_Forearm','R_Upperarm','Head','L_Hand')},world,names
    before_pos,before_world,before_names=joint_metrics(before,old)
    after_pos,after_world,after_names=joint_metrics(after,new)
    target_delta={name:[y-x for x,y in zip(before_pos[name],after_pos[name])] for name in before_pos}
    hand_angle=math.degrees(before_world[before_names['R_Hand']].to_quaternion().rotation_difference(after_world[after_names['R_Hand']].to_quaternion()).angle)
    rejects=[]
    for t in [float('nan'),float('inf'),-.001,1.751,True]:
        try:b.weight(t)
        except ValueError:rejects.append(repr(t))
        else:raise AssertionError('bad source time accepted')
    require(b.weight(.82)==b.weight(1.)==0.,'bounded support endpoints must be exactly zero')
    result={'status':'v4_raw_and_actual_veteran_bounded_checks_passed' if not bad else 'v4_target_bounded_checks_failed','raw':b.identity(OUT/'weighted_overhead_raw.glb'),'authoring':b.identity(OUT/'weighted_overhead_authoring.json'),'actual_target_after':b.identity(OUT/'veteran_prepared_png.glb'),'actual_target_before':b.identity(b.TARGET_BEFORE),'v3_actual4pairs':r0,'v3_native_pipeline_reproduced4pairs':rr,'v4_same_time_clear':r1,'source_invariants':{'RAW234channels_78joints_211keys_same120Hz_grid':True,'exact_guard_endpoint_float32_values':True,'right15_unbaked_all_bytes_preserved':True,'all_static_and_other_TRS_payload_bytes_preserved':True,'only_changed_tracks':changed,'changed_binary_byte_count':len(diff_bytes),'allowed_patch_byte_count':len(allowed),'outside_source_0p82_1p0_unchanged':True},'actual_veteran_0p9_joint_delta_metres':target_delta,'actual_veteran_0p9_hand_world_orientation_change_degrees':hand_angle,'actual_target_invariants':{'before_reproduction_max_float32_component_error':reproduction_error,'non_right_arm_max_float32_component_error_from_actual_v3':unchanged_error,'static_checks':static_checks,'native_target_grip_finger_once_and_target_idle_root_once':'actual prepare_character canonical_grounding_clips timelines from five target canonical clips, see alignment private_v4_validation; old/new before reproduction validates assembly identity'},'sample_count':len(times),'overlap_sample_count':len(bad),'invalid_time_cases_rejected':rejects,'scope':'actual assembled veteran only, full30Hz plus bounded critical/boundary times; true steel/full-body and nonadjacent R/L forearm/hand versus head/chest triangles','limits':['No continuous-time or all-cloth-volume clearance guarantee.','Base/indigo actual retargeting not regenerated in this source lane.','Root must regenerate final target library/binding/profiles and actual damage window; cue1.0 is metadata.'],'frames':rows,'source_pins':{str(p.relative_to(b.REPO)):b.digest(p) for p in [Path(__file__),Path(b.__file__),LANE/'integration/review_candidate.py',b.PRODUCER/'prepare_rigged_warrior.py',b.PRODUCER/'prepare_character_library.py',b.PRODUCER/'attack_grounding.py']}}
    b.write('weighted_overhead_verification.json',result)
    print('V4_RESULT',result['status'],'samples',len(times),'overlap',len(bad),'reproduction_error',reproduction_error,flush=True)
    if bad:raise SystemExit(2)

if __name__=='__main__':main()
