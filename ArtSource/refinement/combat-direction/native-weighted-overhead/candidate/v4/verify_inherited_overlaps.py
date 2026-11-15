"""Classify only the two newly discovered off-delta veteran overlap samples."""
import importlib.util,json,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1]
sys.path.insert(0,str(LANE));import build_weighted_overhead as b
review=b.load_module('v4_inherited_target_review',LANE/'integration/review_candidate.py')
report=json.loads((OUT/'weighted_overhead_verification.json').read_text())
before=b.library.read_glb(b.TARGET_BEFORE);surface=review.ActualTargetSurface(before,[0])
from mathutils.bvhtree import BVHTree
import numpy as np

def full_pairs(asset,surface,time):
    world=review.profiles.pose_world(asset[0],surface.tracks,time,surface.parents,surface.order)
    transforms=np.array([list(world[i]) for i in surface.joints])@surface.bind
    blended=np.sum(transforms[surface.palette]*surface.weights[:,:,None,None],axis=1)
    body=np.einsum('vij,vj->vi',blended,surface.position)[:,:3]
    li,lf=surface.regions['L_forearm'];ci,cf=surface.regions['chest']
    hits=BVHTree.FromPolygons(body[li].tolist(),lf.tolist(),all_triangles=True,epsilon=0.).overlap(BVHTree.FromPolygons(body[ci].tolist(),cf.tolist(),all_triangles=True,epsilon=0.))
    return [{'first_region_triangle':int(a),'second_region_triangle':int(c),'first_triangle_metres':body[li[lf[a]]].tolist(),'second_triangle_metres':body[ci[cf[c]]].tolist()} for a,c in hits]

rows=[]
for new in report['frames']:
    if not new['steel_fullbody_intersections'] and not any(new['nonadjacent_region_triangle_pairs'].values()):continue
    old=surface.evaluate(new['source_seconds'])
    equal=old['nonadjacent_region_triangle_pairs']==new['nonadjacent_region_triangle_pairs'] and old['steel_fullbody_intersections']==new['steel_fullbody_intersections']
    assert equal,('new unexpected target overlap',new['source_seconds'])
    assert b.weight(float(new['source_seconds']))==0
    rows.append({'all_actual_v3_left_forearm_chest_triangle_pairs':full_pairs(before,surface,new['source_seconds']),'source_seconds':new['source_seconds'],'same_actual_v3_target':old,'v4_target':new,'identical_triangle_pair_counts_outside_delta':equal})
result={'status':'targeted0p9_defect_repaired_two_off_delta_v3_inherited_overlaps_confirmed','before':b.identity(b.TARGET_BEFORE),'after':b.identity(OUT/'veteran_prepared_png.glb'),'verification':b.identity(OUT/'weighted_overhead_verification.json'),'sample_count':len(rows),'new_overlap_sample_count':0,'unchanged_inherited_overlap_sample_count':len(rows),'frames':rows,'decision_boundary':'No second geometric correction and no expansion beyond .82–1.0. Root must decide the inherited veteran defects; this source lane does not claim whole-target clearance.','source_pin':b.identity(Path(__file__))}
(OUT/'weighted_overhead_inherited_overlaps.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'samples':[{'source_seconds':r['source_seconds'],'v3':r['same_actual_v3_target']['nonadjacent_region_triangle_pairs'],'v4':r['v4_target']['nonadjacent_region_triangle_pairs']} for r in rows]},indent=2),flush=True)
