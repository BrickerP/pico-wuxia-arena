"""Prepare immutable high-source correspondence and provisional garment selections.

CPU only. Uses NumPy and SciPy; no source geometry is modified. The semantic
sets are working regions, not a claim that this fused mesh contains sewn panels.
"""
import hashlib
import json
import struct
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
HIGH = ROOT / "ArtSource/refinement/character/high_pbr/model.glb"
LOW = ROOT / "ArtSource/tripo-warrior/refined-base60k/rig.glb"
PREPARED = ROOT / "ArtSource/tripo-warrior/library/base_prepared_png.glb"
SHA_HIGH = "9c336b4ab7469532b28a5550ee8ac53839aba0b53f00ca3beb89288a23108103"
SHA_LOW = "43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6"
GROUPS = {
    0: "DISPUTED_do_not_treat_as_confirmed_cloth",
    1: "WORK_front_wearer_left",
    2: "WORK_front_wearer_right",
    3: "WORK_back_body",
    4: "WORK_left_shoulder_upper_sleeve",
    5: "WORK_right_shoulder_upper_sleeve",
    6: "WORK_left_forearm_sleeve",
    7: "WORK_right_forearm_sleeve",
    8: "WORK_left_wrist_opening",
    9: "WORK_right_wrist_opening",
    10: "WORK_inner_collar_review",
    20: "LOCK_head_face_neck_hair",
    21: "LOCK_left_hand_fingers",
    22: "LOCK_right_hand_fingers",
    23: "LOCK_waist_belt",
    24: "LOCK_lower_garment_trousers_boots",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data = path.read_bytes()
    size, kind = struct.unpack_from("<II", data, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(data[20:20+size])
    binary = data[28+size:]
    pr = doc["meshes"][0]["primitives"][0]
    def stream(index):
        a = doc["accessors"][index]
        v = doc["bufferViews"][a["bufferView"]]
        dtype = np.dtype({5121:"u1", 5123:"<u2", 5125:"<u4", 5126:"<f4"}[a["componentType"]])
        width = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}[a["type"]]
        return np.ndarray((a["count"],width),dtype=dtype,buffer=binary,
            offset=v.get("byteOffset",0)+a.get("byteOffset",0),
            strides=(v.get("byteStride",width*dtype.itemsize),dtype.itemsize)).copy()
    arrays = {k:stream(v) for k,v in pr["attributes"].items()}
    arrays["faces"] = stream(pr["indices"]).reshape(-1,3).astype(np.int32)
    return doc,binary,arrays


def node_world(document,index):
    parents={child:i for i,node in enumerate(document["nodes"]) for child in node.get("children",[])}
    node=document["nodes"][index]
    if "matrix" in node:
        matrix=np.asarray(node["matrix"],float).reshape(4,4,order="F")
    else:
        x,y,z,w=node.get("rotation",[0,0,0,1])
        rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
            [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
            [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
        matrix=np.eye(4)
        matrix[:3,:3]=rotation@np.diag(node.get("scale",[1,1,1]))
        matrix[:3,3]=node.get("translation",[0,0,0])
    return node_world(document,parents[index])@matrix if index in parents else matrix


def point_triangle_candidates(points, triangles):
    """Closest point among plane interior and the three closed edges."""
    a,b,c = triangles[:,:,0],triangles[:,:,1],triangles[:,:,2]
    ab,ac = b-a,c-a
    q = points[:,None,:]-a
    d00,d01,d11 = (ab*ab).sum(2),(ab*ac).sum(2),(ac*ac).sum(2)
    d20,d21 = (q*ab).sum(2),(q*ac).sum(2)
    den = d00*d11-d01*d01
    safe = np.where(abs(den)>1e-18,den,1)
    v,w = (d11*d20-d01*d21)/safe,(d00*d21-d01*d20)/safe
    projected = a+v[:,:,None]*ab+w[:,:,None]*ac
    distances = ((projected-points[:,None,:])**2).sum(2)
    distances[(v<0)|(w<0)|(v+w>1)|(abs(den)<1e-18)] = np.inf
    bary = np.stack((1-v-w,v,w),axis=2)
    for first,second in ((0,1),(1,2),(2,0)):
        start,end=triangles[:,:,first],triangles[:,:,second]
        edge=end-start
        t=np.clip(((points[:,None,:]-start)*edge).sum(2)/np.maximum((edge*edge).sum(2),1e-18),0,1)
        p=start+t[:,:,None]*edge
        d=((p-points[:,None,:])**2).sum(2)
        use=d<distances
        distances[use]=d[use]
        edge_bary=np.zeros_like(bary)
        edge_bary[:,:,first]=1-t
        edge_bary[:,:,second]=t
        bary[use]=edge_bary[use]
    best=distances.argmin(1)
    rows=np.arange(len(points))
    return best,np.sqrt(distances[rows,best]),bary[rows,best]


def classify_low(points,faces,regions,material,coat):
    centers=points[faces].mean(1)
    x,y,z=centers.T
    anatomy=regions["face_anatomy_ids"]
    group=np.zeros(len(faces),np.int16)
    # Geographic protection is deliberately conservative. It has precedence
    # over colour/material candidates and never authorizes skin modification.
    group[y<.975]=24
    group[(y>=.975)&(y<=1.075)&(abs(x)<.32)]=23
    group[(y>1.48)|((anatomy==1)&(y>1.42))]=20
    group[np.isin(regions["anatomy_ids"][faces],[4]).any(1)]=21
    group[np.isin(regions["anatomy_ids"][faces],[7]).any(1)]=22
    eligible=(group==0)&(y>1.075)&(y<=1.48)
    # Existing face-material labels are candidates, not a physical seam truth.
    cloth=eligible&((material==3)|coat)
    group[cloth&(z<=0)]=3
    group[cloth&(z>0)&(x>=0)]=1
    group[cloth&(z>0)&(x<0)]=2
    group[cloth&(anatomy==2)]=4
    group[cloth&(anatomy==5)]=5
    group[cloth&(anatomy==3)]=6
    group[cloth&(anatomy==6)]=7
    for side,region_id,target in (("left",3,8),("right",6,9)):
        wrist=regions[side+"_cuff_mask"][faces].any(1)
        group[cloth&wrist&(anatomy==region_id)]=target
    # Keep narrow white/inner collar as a separate working review region.
    group[cloth&(abs(x)<.105)&(y>1.30)&(z>0)&(~coat)]=10
    reasons=np.zeros(len(faces),np.uint16)
    reasons[eligible&(material==0)]|=1
    reasons[eligible&np.isin(material,[1,2,4,5])]|=2
    reasons[eligible&regions["face_anatomy_mixed"]]|=4
    reasons[eligible&regions["face_garment_mixed"]]|=8
    reasons[eligible&((abs(y-1.075)<.010)|(abs(y-1.48)<.010))]|=16
    # The front/back divide and left/right divide are NOT established seams.
    reasons[eligible&((abs(z)<.008)|((abs(x)<.008)&(z>0)))]|=32
    return group,reasons


def ranges(ids):
    if len(ids)==0:return []
    splits=np.flatnonzero(np.diff(ids)!=1)+1
    chunks=np.split(ids,splits)
    return [[int(c[0]),int(c[-1])] for c in chunks]


def main():
    assert sha(HIGH)==SHA_HIGH and sha(LOW)==SHA_LOW
    hd,hb,high=load(HIGH)
    ld,lb,low=load(LOW)
    regions=np.load(ROOT/"ArtSource/refinement/deformation/regions.npz")
    assert np.array_equal(regions["raw_positions"],low["POSITION"])
    assert np.array_equal(regions["faces"],low["faces"])
    hp,lp=high["POSITION"].astype(float),low["POSITION"].astype(float)
    tree=cKDTree(hp)
    translation=(lp.min(0)+lp.max(0)-hp.min(0)-hp.max(0))*.5
    trace=[]
    for i in range(8):
        distance,near=tree.query(lp-translation,workers=3)
        residual=lp-hp[near]-translation
        delta=np.median(residual[distance<np.quantile(distance,.85)],axis=0)
        translation+=delta
        trace.append({"iteration":i,"delta_raw":delta.tolist(),"nearest_vertex_median_raw":float(np.median(distance))})
        if np.linalg.norm(delta)<1e-7:break
    # Use current pinned canonical scale, but explicit mesh world translation.
    alignment=json.loads((ROOT/"ArtSource/tripo-warrior/library/base_alignment.json").read_text())
    frame=np.asarray(alignment["normalization_matrix_gltf"]).reshape(4,4,order="F")
    low_node=next(i for i,n in enumerate(ld["nodes"]) if n.get("mesh")==0)
    high_node=next(i for i,n in enumerate(hd["nodes"]) if n.get("mesh")==0)
    low_world=node_world(ld,low_node)
    high_world=node_world(hd,high_node)
    assert np.allclose(high_world,np.eye(4),atol=1e-12)
    assert np.allclose(low_world[:3,:3],np.eye(3),atol=1e-12)
    raw_to_canonical=frame@low_world
    high_to_raw=np.eye(4);high_to_raw[:3,3]=translation
    high_to_canonical=raw_to_canonical@high_to_raw
    canonical=lp@raw_to_canonical[:3,:3].T+raw_to_canonical[:3,3]
    material_doc=json.loads((ROOT/"ArtSource/refinement/lighting/stage2/pbr/face_material_map.json").read_text())
    material=np.zeros(len(low["faces"]),np.int16)
    for m in material_doc["source_face_ids_by_material"]:material[m["source_face_ids"]]=m["material_index"]
    coat=np.zeros(len(low["faces"]),bool)
    coat[np.load(ROOT/"ArtSource/refinement/character/design/cloth-surface/v2/source_uv_masks.npz")["coat_face_ids"]]=True
    low_group,low_reasons=classify_low(canonical,low["faces"],regions,material,coat)
    # Search several source triangles, then use real closest points rather
    # than copying the nearest centroid/vertex label blindly.
    source_tri=lp[low["faces"]]
    face_tree=cKDTree(source_tri.mean(1))
    count=len(high["faces"])
    source_faces=np.empty(count,np.int32)
    bary=np.empty((count,3),np.float32)
    distances=np.empty(count,np.float32)
    for begin in range(0,count,50000):
        end=min(begin+50000,count)
        p=hp[high["faces"][begin:end]].mean(1)+translation
        _,candidates=face_tree.query(p,k=12,workers=3)
        best,d,b=point_triangle_candidates(p,source_tri[candidates])
        source_faces[begin:end]=candidates[np.arange(len(p)),best]
        distances[begin:end]=d*alignment["uniform_scale"]
        bary[begin:end]=b
        if begin%250000==0:print("mapped",end,"/",count,flush=True)
    high_group=low_group[source_faces]
    reasons=low_reasons[source_faces].copy()
    reasons[distances>.005]|=64
    # Source correspondence is geometric; discrepancies are not editing grants.
    reasons[(distances>.002)&(high_group<20)]|=128
    arrays_path=HERE/"source_group_mapping.npz"
    np.savez_compressed(arrays_path,high_raw_positions=high["POSITION"],high_faces=high["faces"],
        high_uv=high["TEXCOORD_0"],high_normals=high["NORMAL"],
        high_face_source_face=source_faces,high_face_source_barycentric=bary,
        high_face_source_distance_m=distances,high_face_group=high_group,
        high_face_dispute_bits=reasons,low_face_group=low_group,low_face_dispute_bits=low_reasons,
        low_face_material_candidate=material,high_to_canonical=high_to_canonical,
        raw_to_canonical=raw_to_canonical,high_to_raw=high_to_raw)
    report={"schema_version":1,"status":"editable_source_preparation_not_sculpted_not_approved",
        "sources":{"high_pbr":{"path":str(HIGH.relative_to(ROOT)),"sha256":SHA_HIGH},
            "high_geometry":{"path":"ArtSource/refinement/character/high_geometry/model.glb","sha256":sha(ROOT/"ArtSource/refinement/character/high_geometry/model.glb")},
            "low_mapping_source":{"path":str(LOW.relative_to(ROOT)),"sha256":SHA_LOW},
            "current_prepared_context":{"path":str(PREPARED.relative_to(ROOT)),"sha256":sha(PREPARED)},
            "current_raw_context":{"path":"ArtSource/refinement/hero-face/neck-continuous/candidate-raw.glb","sha256":alignment["source_sha256"]}},
        "counts":{"high_vertices":len(hp),"high_triangles":count,"low_vertices":len(lp),"low_triangles":len(low["faces"]),"source_bones":78},
        "frame":{"source_axes":"+Y up, +X forward, centred high source; no mesh-node transform on high GLB",
            "canonical_axes":"+Y up, +Z forward, wearer left +X; metres",
            "blender_axes":"+Z up, -Y forward, wearer left +X; metres",
            "high_to_raw_translation":translation.tolist(),"registration_method":"translation-only robust ICP to high vertices; no source rescale/deformation; fixed current canonical normalization afterwards",
            "registration_trace":trace,"high_to_canonical_row_major":high_to_canonical.tolist(),
            "high_mesh_node_index":high_node,"high_mesh_node_world_row_major":high_world.tolist(),
            "raw_mesh_node_index":low_node,"raw_mesh_node_world_row_major":low_world.tolist(),
            "raw_to_canonical_row_major":raw_to_canonical.tolist(),
            "high_raw_bounds":[hp.min(0).tolist(),hp.max(0).tolist()],
            "low_raw_bounds":[lp.min(0).tolist(),lp.max(0).tolist()],
            "high_canonical_bounds":[(hp@high_to_canonical[:3,:3].T+high_to_canonical[:3,3]).min(0).tolist(),(hp@high_to_canonical[:3,:3].T+high_to_canonical[:3,3]).max(0).tolist()]},
        "mapping":{"arrays_file":arrays_path.name,"sha256":sha(arrays_path),"index_base":0,
            "high_id_source":"Only high_pbr/model.glb SHA9c336b4a; high_geometry vertex/face order differs and is not interchangeable",
            "method":"high original triangle centroid -> nearest point on 12 low source face-centroid candidates; retain face ID + barycentric + distance",
            "distance_quantiles_mm":{str(q):float(np.quantile(distances,q)*1000) for q in [0,.5,.9,.95,.99,1]},
            "not_exhaustive_nearest_surface_search":True},
        "disputed":{"bits":{"1":"source material unassigned","2":"skin/hair/leather/metal candidate in upperbody","4":"mixed source anatomy","8":"mixed source garment hypothesis","16":"protection border","32":"front/back or midline working divide is not a confirmed seam","64":"source surface mismatch over 5mm","128":"editable source mismatch over 2mm"},
            "high_face_count":int((reasons!=0).sum()),"safe_to_edit_automatically":False},
        "groups":[],"limits":[
            "One fused high mesh: groups are source face selections and provisional panel work regions, not physical sewn panels or verified overlap layers.",
            "No modelling, UV, baking, decimation, rig transfer, original-face deletion or dynamic validation performed.",
            "High source has its original head/hands. Current raw34ce/preparedb732 revised head/hands/DAO/78 bones are context only and must not be replaced by this high source.",
            "high_geometry a72eb8ee has a different vertex/face order; these IDs and selections apply only to high_pbr9c336b4a.",
            "Existing semantic/material maps are candidate evidence; colour thresholds never override protected anatomy.",
            "True left-over-right lapel seam and shoulder/elbow/wrist construction require artistic review against the 12 design board."
        ]}
    for gid,name in GROUPS.items():
        ids=np.flatnonzero(high_group==gid)
        report["groups"].append({"id":gid,"name":name,"high_face_count":len(ids),
            "high_face_inclusive_ranges":ranges(ids),"low_face_inclusive_ranges":ranges(np.flatnonzero(low_group==gid)),
            "high_disputed_face_count":int((reasons[ids]!=0).sum()),"confirmed_physical_panel":False})
    # Images are original immutable payload copies; no raster edits.
    textures=HERE/"original_source_textures";textures.mkdir(exist_ok=True)
    for i,img in enumerate(hd.get("images",[])):
        view=hd["bufferViews"][img["bufferView"]]
        ext={"image/png":"png","image/jpeg":"jpg"}.get(img["mimeType"],"bin")
        offset=view.get("byteOffset",0)
        (textures/f"image_{i}.{ext}").write_bytes(hb[offset:offset+view["byteLength"]])
    (HERE/"source_group_mapping.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"frame":report["frame"],"mapping":report["mapping"],"groups":[{k:v for k,v in g.items() if "ranges" not in k} for g in report["groups"]]},indent=2),flush=True)


if __name__=="__main__":main()
