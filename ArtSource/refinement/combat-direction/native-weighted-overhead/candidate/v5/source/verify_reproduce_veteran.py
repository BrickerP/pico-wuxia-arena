"""Reproduce frozen v4 target, inspect actual affected region, no pose edits."""
from pathlib import Path
import json,sys,hashlib
from collections import Counter
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1]
sys.path.insert(0,str(LANE));import build_weighted_overhead as b
review=b.load_module('v5_before_actual_target',LANE/'integration/review_candidate.py')
import numpy as np
from mathutils.bvhtree import BVHTree
path=LANE/'candidate/v4/veteran_prepared_png.glb'
assert b.digest(path)=='cead1124ab1c3453f6fae2f98e0be275a39792be3de98e6888edaf83a4aabb86'
asset=b.library.read_glb(path);surface=review.ActualTargetSurface(asset,[0]);doc=asset[0]
names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
rows=[]
for time,expected in [(1.1,21),(44/30,23)]:
    r=surface.evaluate(time);assert r['nonadjacent_region_triangle_pairs']['L_forearm__chest']==expected
    world=review.profiles.pose_world(doc,surface.tracks,time,surface.parents,surface.order)
    trans=np.array([list(world[i]) for i in surface.joints])@surface.bind
    blend=np.sum(trans[surface.palette]*surface.weights[:,:,None,None],axis=1)
    points=np.einsum('vij,vj->vi',blend,surface.position)[:,:3]
    li,lf=surface.regions['L_forearm'];ci,cf=surface.regions['chest']
    lt=BVHTree.FromPolygons(points[li].tolist(),lf.tolist(),all_triangles=True,epsilon=0.)
    ct=BVHTree.FromPolygons(points[ci].tolist(),cf.tolist(),all_triangles=True,epsilon=0.)
    hits=lt.overlap(ct);assert len(hits)==expected
    lv=np.unique(li[lf[[a for a,c in hits]]]);cv=np.unique(ci[cf[[c for a,c in hits]]])
    allv=np.concatenate([lv,cv]);details=[];plane_values=[];nearest=[]
    elbow=np.array(world[names['L_Forearm']].translation);wrist=np.array(world[names['L_Hand']].translation);axis=wrist-elbow
    for index in lv:
        nearest_point,normal,face,distance=ct.find_nearest(points[index])
        nearest.append(float(np.dot(points[index]-np.array(nearest_point),np.array(normal))))
    for a,c in hits:
        arm=points[li[lf[a]]];chest=points[ci[cf[c]]]
        normal=np.cross(chest[1]-chest[0],chest[2]-chest[0]);normal/=np.linalg.norm(normal)
        signed=(arm-chest[0])@normal;plane_values.extend(signed.tolist())
        details.append({'L_forearm_region_triangle':int(a),'chest_region_triangle':int(c),'arm_triangle_metres':arm.tolist(),'chest_triangle_metres':chest.tolist(),'chest_face_normal':normal.tolist(),'arm_vertices_signed_to_paired_chest_face_plane_metres':signed.tolist()})
    palette_names=[doc['nodes'][i]['name'] for i in surface.joints]
    def vertex_summary(indices):
        result=[]
        for i in indices:
            weights={palette_names[int(j)]:float(w) for j,w in zip(surface.palette[i],surface.weights[i]) if w>.02}
            result.append({'index':int(i),'world_metres':points[i].tolist(),'dominant_joint':str(surface.dominant[i]),'skin_weights_gt2percent':weights})
        return result
    r['joint_origins_metres']={name:list(world[names[name]].translation) for name in ('L_Upperarm','L_Forearm','L_Hand','Spine02','Spine01','Waist')}
    r['geometry_diagnosis']={'intersection_triangle_pair_count':len(hits),'unique_forearm_triangles':len(set(a for a,c in hits)),'unique_chest_triangles':len(set(c for a,c in hits)),'intersection_bounds_metres':{'min':points[allv].min(axis=0).tolist(),'max':points[allv].max(axis=0).tolist()},'forearm_dominant_joint_vertices':dict(Counter(surface.dominant[lv])),'chest_dominant_joint_vertices':dict(Counter(surface.dominant[cv])),'forearm_vertex_projection_along_elbow_to_wrist_fraction_bounds':[float(np.min((points[lv]-elbow)@axis/(axis@axis))),float(np.max((points[lv]-elbow)@axis/(axis@axis)))],'forearm_vertex_nearest_chest_signed_distance_metres_bounds':[min(nearest),max(nearest)],'paired_face_plane_signed_vertex_bounds_metres':[min(plane_values),max(plane_values)],'forearm_vertices':vertex_summary(lv),'chest_vertices':vertex_summary(cv),'all_triangle_pairs':details,'depth_limit':'Signed distances use local triangle/nearest surface normals on open semantic core regions. They bound a local surface excursion, not closed-volume penetration. Visibility requires actual material pixels/camera.'}
    rows.append(r)
    print('V5_BASELINE',time,json.dumps({k:v for k,v in r['geometry_diagnosis'].items() if k not in ('all_triangle_pairs','forearm_vertices','chest_vertices')},ensure_ascii=False),flush=True)
result={'status':'v4_actual_veteran21_and23_pairs_reproduced_before_v5_edit','input':b.identity(path),'RAW_v4':b.identity(LANE/'candidate/v4/weighted_overhead_raw.glb'),'frames':rows,'source':b.identity(Path(__file__))}
(OUT/'veteran_v4_defect_reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
