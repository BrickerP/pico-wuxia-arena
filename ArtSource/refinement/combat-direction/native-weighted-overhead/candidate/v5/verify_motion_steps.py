"""Compare all211 keys: old/new local and world elbow/wrist steps, and Q signs."""
from pathlib import Path
import json,math,sys,numpy as np
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1]
sys.path.insert(0,str(LANE));import build_weighted_overhead as b
review=b.load_module('v5_all_key_step_review',LANE/'integration/review_candidate.py')

def qangle(a,c):
    a=np.array(a,dtype=float);c=np.array(c,dtype=float);a/=np.linalg.norm(a);c/=np.linalg.norm(c)
    return math.degrees(2*math.acos(min(1.,max(-1.,abs(float(a@c))))))

def evaluate(path,norm):
    doc,binary=b.library.read_glb(path);_,tracks,times=review.clip(doc,binary,'attack_overhead');names={n.get('name'):i for i,n in enumerate(doc['nodes'])};parents,order=b.library.node_order(doc)
    hemispheres={}
    for name in ('L_Upperarm','L_Forearm','L_Hand'):
        stored=np.array(tracks[names[name],'rotation'][1]);dots=np.sum(stored[:-1]*stored[1:],axis=1);k=int(np.argmin(dots))
        # Record inherited stored-sign boundaries explicitly; do not hide
        # them behind the hemisphere-equivalent geometric angle below.
        hemispheres[name]={'minimum_actual_stored_adjacent_dot':float(dots[k]),'key_pair':[k,k+1],'source_seconds_pair':[times[k],times[k+1]],'negative_pair_count':int(np.count_nonzero(dots<0)),'negative_key_pairs':[[int(i),int(i+1)] for i in np.flatnonzero(dots<0)]}
    poses=[]
    for t in times:
        world=review.profiles.pose_world(doc,tracks,t,parents,order);row={}
        for name in ('L_Forearm','L_Hand'):
            local=b.library.sampled_local(doc['nodes'][names[name]],names[name],tracks,t)
            matrix=norm@world[names[name]]
            row[name]={'local_q':list(local.to_quaternion()),'world_q':list(matrix.to_quaternion()),'world_metres':list(matrix.translation)}
        poses.append(row)
    return times,poses,hemispheres

meta=json.loads((OUT/'weighted_overhead_authoring.json').read_text());norm=b.library.local_matrix({'matrix':meta['normalization_matrix_gltf']})
from mathutils import Matrix
contexts=[]
for label,before_path,after_path,frame in [
 ('source_RAW',b.SOURCE,OUT/'weighted_overhead_raw.glb',norm),
 ('actual_veteran',b.TARGET_BEFORE,OUT/'veteran_prepared_png.glb',Matrix.Identity(4))]:
    times,old,old_dot=evaluate(before_path,frame);newtimes,new,new_dot=evaluate(after_path,frame);assert len(times)==211 and times==newtimes
    rows=[]
    for k in range(1,211):
        r={'key_pair':[k-1,k],'source_seconds_pair':[times[k-1],times[k]],'bones':{}}
        for name in ('L_Forearm','L_Hand'):
            z={}
            for mode in ('local','world'):
                q=mode+'_q';x=qangle(old[k-1][name][q],old[k][name][q]);y=qangle(new[k-1][name][q],new[k][name][q]);z[mode+'_rotation_step_degrees']={'v4':x,'v5':y,'increase':y-x}
            x=float(np.linalg.norm(np.array(old[k][name]['world_metres'])-old[k-1][name]['world_metres']));y=float(np.linalg.norm(np.array(new[k][name]['world_metres'])-new[k-1][name]['world_metres']));z['world_position_step_metres']={'v4':x,'v5':y,'increase':y-x}
            r['bones'][name]=z
        rows.append(r)
    summary={}
    for name in ('L_Forearm','L_Hand'):
        summary[name]={}
        for metric in ('local_rotation_step_degrees','world_rotation_step_degrees','world_position_step_metres'):
            top={}
            for field in ('v4','v5','increase'):
                r=max(rows,key=lambda r:r['bones'][name][metric][field]);top[field]={'source_seconds_pair':r['source_seconds_pair'],**r['bones'][name][metric]}
            top['largest_existing_v4_steps']=[{'source_seconds_pair':r['source_seconds_pair'],**r['bones'][name][metric]} for r in sorted(rows,key=lambda r:r['bones'][name][metric]['v4'],reverse=True)[:3]]
            summary[name][metric]=top
    contexts.append({'context':label,'before':b.identity(before_path),'after':b.identity(after_path),'keys':211,'steps':210,'stored_quaternion_half_sphere_checks':{'v4':old_dot,'v5':new_dot},'summary':summary,'all_neighbor_steps':rows})
    print('V5_STEPS',label,json.dumps(summary),flush=True)
result={'status':'complete211_key_step_comparison_and_stored_Q_hemisphere_checks','RAW':b.identity(OUT/'weighted_overhead_raw.glb'),'actual_target':b.identity(OUT/'veteran_prepared_png.glb'),'contexts':contexts,'limits':'Stored adjacent quaternion dots are checked without abs; geometric angular steps use hemisphere-equivalent angle. These key-neighbor metrics do not assert that the existing or modified glTF LINEAR animation is globally C2. Existing v4 peaks are listed independently.','source':b.identity(Path(__file__))}
(OUT/'weighted_overhead_motion_steps.json').write_text(json.dumps(result,indent=2)+'\n')
