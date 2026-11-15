"""Measure local surface clearance and actual target limb movement at two faults."""
from pathlib import Path
import json,sys,numpy as np
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1]
sys.path.insert(0,str(LANE));import build_weighted_overhead as b
review=b.load_module('v5_local_surface_metrics',LANE/'integration/review_candidate.py')
from mathutils.bvhtree import BVHTree
before_asset=b.library.read_glb(b.TARGET_BEFORE);after_asset=b.library.read_glb(OUT/'veteran_prepared_png.glb')
before=review.ActualTargetSurface(before_asset,[0]);after=review.ActualTargetSurface(after_asset,[0])
base=json.loads((OUT/'veteran_v4_defect_reproduction.json').read_text());rows=[]
def posed(surface,t):
    world=review.profiles.pose_world(surface.doc,surface.tracks,t,surface.parents,surface.order)
    transforms=np.array([list(world[i]) for i in surface.joints])@surface.bind
    blend=np.sum(transforms[surface.palette]*surface.weights[:,:,None,None],axis=1)
    points=np.einsum('vij,vj->vi',blend,surface.position)[:,:3]
    return points,world
for row in base['frames']:
    t=row['source_seconds'];old,ow=posed(before,t);new,nw=posed(after,t)
    affected=[v['index'] for v in row['geometry_diagnosis']['forearm_vertices']]
    ci,cf=after.regions['chest'];tree=BVHTree.FromPolygons(new[ci].tolist(),cf.tolist(),all_triangles=True,epsilon=0.)
    signed=[]
    for i in affected:
        point,normal,face,distance=tree.find_nearest(new[i]);signed.append(float(np.dot(new[i]-np.array(point),np.array(normal))))
    on={n.get('name'):i for i,n in enumerate(before.doc['nodes'])};nn={n.get('name'):i for i,n in enumerate(after.doc['nodes'])}
    delta={name:list(nw[nn[name]].translation-ow[on[name]].translation) for name in ('L_Upperarm','L_Forearm','L_Hand','Head','R_Hand')}
    rows.append({'source_seconds':t,'previously_intersecting_forearm_vertex_indices':affected,'before_local_nearest_chest_signed_distance_metres_bounds':row['geometry_diagnosis']['forearm_vertex_nearest_chest_signed_distance_metres_bounds'],'after_same_vertices_local_nearest_chest_signed_distance_metres_bounds':[min(signed),max(signed)],'actual_veteran_joint_origin_delta_metres':delta,'world_L_hand_rotation_delta_degrees':float(np.degrees(ow[on['L_Hand']].to_quaternion().rotation_difference(nw[nn['L_Hand']].to_quaternion()).angle)),'depth_interpretation':'Local nearest triangle normal signed distances on open semantic core surface, not closed body volume. Positive means outward along that local surface normal; actual pixels and intersections are independent evidence.'})
    print('V5_CLEARANCE',json.dumps(rows[-1]),flush=True)
result={'before':b.identity(b.TARGET_BEFORE),'after':b.identity(OUT/'veteran_prepared_png.glb'),'RAW':b.identity(OUT/'weighted_overhead_raw.glb'),'frames':rows,'source':b.identity(Path(__file__))}
(OUT/'weighted_overhead_clearance_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
