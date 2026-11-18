"""Verify material, corner streams, winding, anchors, and sample local culling tradeoffs."""
import hashlib
import json
import math
import sys
from collections import defaultdict
from itertools import product
from pathlib import Path

import numpy as np

from batch_courtyard import REGIONS, data, read, view


def worlds(doc):
    out = {}
    def visit(idx, parent):
        node = doc["nodes"][idx]
        if "matrix" in node:
            local = np.array(node["matrix"]).reshape((4,4)).T
        else:
            x,y,z,w = node.get("rotation",(0,0,0,1))
            rot = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                            [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                            [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            local = np.eye(4)
            local[:3,:3] = rot @ np.diag(node.get("scale",(1,1,1)))
            local[:3,3] = node.get("translation",(0,0,0))
        world = parent @ local
        assert idx not in out
        out[idx] = world
        for child in node.get("children",[]):
            visit(child,world)
    for root in doc["scenes"][doc["scene"]]["nodes"]:
        visit(root, np.eye(4))
    return out


def primitives(bank):
    doc = bank[0]
    streams = defaultdict(list)
    proxies = []
    for idx,world in worlds(doc).items():
        node = doc["nodes"][idx]
        if "mesh" not in node:
            continue
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            names = tuple(sorted(prim["attributes"]))
            arrays = []
            for attr in names:
                values = data(bank,prim["attributes"][attr])
                if attr == "POSITION":
                    points = (values @ world[:3,:3].T + world[:3,3]).astype("<f4")
                    values = points
                elif attr in ("NORMAL","TANGENT"):
                    basis = world[:3,:3]
                    assert np.allclose(basis.T @ basis, np.eye(3), atol=2e-6) and np.linalg.det(basis)>0
                    xyz = (values[:,:3] @ basis.T).astype("<f4")
                    values = np.column_stack([xyz,values[:,3:]])
                arrays.append(values)
            indices = data(bank,prim["indices"]).reshape(-1,3)
            assert indices.min()>=0 and indices.max()<len(points)
            triplets = np.ascontiguousarray(np.concatenate(arrays,axis=1)[indices]).reshape(len(indices), -1)
            assert np.isfinite(triplets).all()
            key = str((prim["material"],names,prim.get("mode",4)))
            streams[key].append(triplets.view(np.dtype((np.void,triplets.shape[1]*4))).ravel())
            box = np.asarray(list(product(*zip(points.min(axis=0),points.max(axis=0)))))
            proxies.append((node["name"],box,len(indices)))
    return {key:np.sort(np.concatenate(parts)).tobytes() for key,parts in streams.items()},proxies


def frustum(proxies, eye, yaw):
    radians = math.radians(yaw)
    forward = np.array([math.sin(radians),0,-math.cos(radians)])
    right = np.array([math.cos(radians),0,math.sin(radians)])
    draws = triangles = 0
    for _,box,count in proxies:
        rel = box-eye
        depth = rel@forward
        side = rel@right
        height = rel[:,1]
        if any(np.all(dist<0) for dist in (depth-.05, depth+side, depth-side,depth+height,depth-height)):
            continue
        draws += 1
        triangles += count
    return [draws,triangles]


def main(before,after):
    old,new = read(before),read(after)
    a,b=old[0],new[0]
    for field in ("asset","scene","scenes","materials","samplers","textures","extensionsRequired","extensionsUsed"):
        assert a[field]==b[field],field
    assert len(a["images"])==len(b["images"])
    for source,candidate in zip(a["images"],b["images"]):
        assert dict(source,bufferView=0)==dict(candidate,bufferView=0)
        assert view(old,source["bufferView"])==view(new,candidate["bufferView"])
    allowed=set(name for group in REGIONS.values() for name in group)
    a_world,b_world=worlds(a),worlds(b)
    root,=a["scenes"][a["scene"]]["nodes"]
    for idx,node in enumerate(a["nodes"]):
        rewrite=dict(b["nodes"][idx])
        if idx==root:
            rewrite["children"]=rewrite["children"][:len(node["children"])]
        expected=dict(node)
        if "mesh" in expected:
            if node["name"] not in allowed:
                assert "mesh" in rewrite
            expected.pop("mesh")
            rewrite.pop("mesh",None)
        assert expected==rewrite and np.array_equal(a_world[idx],b_world[idx]),node["name"]
    old_streams,old_proxies=primitives(old)
    new_streams,new_proxies=primitives(new)
    assert old_streams.keys()==new_streams.keys()
    for key in old_streams:
        assert old_streams[key]==new_streams[key],key
    for name in ("EH_GroundReceiver","EH_MortarAndDrain"):
        def signature(proxies):
            return [(p[1].tobytes(),p[2]) for p in proxies if p[0]==name]
        assert signature(old_proxies)==signature(new_proxies) and signature(old_proxies)
    return {
        "sha256":[hashlib.sha256(p.read_bytes()).hexdigest() for p in (before,after)],
        "glb_bytes":[p.stat().st_size for p in (before,after)],
        "draw_primitives":[len(p) for p in (old_proxies,new_proxies)],
        "instanced_triangles":[sum(i[2] for i in p) for p in (old_proxies,new_proxies)],
        "original_nodes_identical_worlds":len(a_world),
        "texture_payloads_identical":len(a["images"]),
        "verified":"Per material/layout: every ordered triangle corner world position, normal, tangent XYZW and UV0, as float32.",
        "frustum_90x90_degrees_primitive_aabbs_not_renderer_profile":{
            str(yaw): [frustum(p,np.array([0,1.65,0]),yaw) for p in (old_proxies,new_proxies)]
            for yaw in (0,20,-20,45,-45,90,-90,180)
        },
    }


if __name__=="__main__":
    print(json.dumps(main(*(Path(x) for x in sys.argv[1:])),indent=2))
