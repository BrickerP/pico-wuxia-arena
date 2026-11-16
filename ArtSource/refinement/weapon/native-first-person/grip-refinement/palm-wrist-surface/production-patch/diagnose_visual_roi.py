"""Trace the visible remaining dorsal crease to source geometry, anatomy and skin weights."""
import importlib.util
import json
import hashlib
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('source_hand_tools',HERE.parent/'build_surface.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
doc,binary=b.h.read(b.SOURCE);primitive=doc['meshes'][0]['primitives'][0]
a={k:b.h.values(doc,binary,v) for k,v in primitive['attributes'].items()}
faces=b.h.values(doc,binary,primitive['indices']).reshape(-1,3).astype(int)
origin,axes,opened_world=b.basis(doc,binary)
opened=b.h.skin(doc,binary,primitive,opened_world)
local=(opened-origin)@axes.T
closed=b.h.skin(doc,binary,primitive,b.h.sampled_worlds(doc,binary,'grip',1.))
triangles=closed[faces]
render=json.loads((HERE/'renders/render_manifest.json').read_text())
matrix=np.asarray(render['source_fixed_cameras']['dorsal']['matrix_world'])
ray_origin=np.asarray([matrix[0,3],matrix[2,3],-matrix[1,3]])
names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
results=[]
for x,y in [(450,480),(445,530),(430,570),(428,570),(422,570),(415,610)]:
    direction=matrix[:3,:3]@np.asarray([(x/1000-.5)*36/45,(.5-y/750)*27/45,-1.])
    direction=np.asarray([direction[0],direction[2],-direction[1]]);direction/=np.linalg.norm(direction)
    e1,e2=triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]
    h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=(e1*h).sum(1)
    good=abs(det)>1e-12;inv=np.divide(1.,det,out=np.zeros_like(det),where=good)
    start=ray_origin-triangles[:,0];u=(start*h).sum(1)*inv;q=np.cross(start,e1)
    v=(q*direction).sum(1)*inv;t=(q*e2).sum(1)*inv
    ids=np.flatnonzero(good&(u>=0)&(v>=0)&(u+v<=1)&(t>0))
    ids=ids[np.argsort(t[ids])]
    if not len(ids):continue
    face=int(ids[0]);vertices=faces[face];weights={}
    for vertex in vertices:
        for joint,weight in zip(a['JOINTS_0'][vertex],a['WEIGHTS_0'][vertex]):
            weights[names[joint]]=weights.get(names[joint],0.)+float(weight)/3
    results.append({'pixel_xy':[x,y],'source_face':face,'source_vertices':vertices.tolist(),
                    'source_open_anatomical_coordinates_m':local[vertices].tolist(),
                    'average_weights':dict(sorted(weights.items(),key=lambda x:-x[1]))})
knuckles={}
for name in ['R_Index1','R_Mid1','R_Pinky1']:
    index=next(i for i,node in enumerate(doc['nodes']) if node.get('name')==name)
    knuckles[name]=((opened_world[index][:3,3]-origin)@axes.T).tolist()
report={'source_sha256':b.SOURCE_SHA,'source_view':'renders/dorsal_original_before.png',
        'source_view_sha256':hashlib.sha256((HERE/'renders/dorsal_original_before.png').read_bytes()).hexdigest(),
        'render_manifest_sha256':hashlib.sha256((HERE/'renders/render_manifest.json').read_bytes()).hexdigest(),
        'diagnostic_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'camera':render['source_fixed_cameras']['dorsal'],'image_size':[1000,750],
        'pose_seconds':1.,'knuckle_bone_positions_in_anatomical_frame_m':knuckles,'pixel_surface_hits':results,
        'conclusion':'The remaining visible long crease is not a normal-texture-only problem: it also appears in the neutral-material images. Pixel rays hit native source faces1101/1075 near anatomical forward0.088..0.090m, before MCP joints at0.101..0.116m. These are mixed metacarpal skin, not an all-digit region; the production brush digit-spill cutoff0.18 was too conservative and left most of this defect unchanged.',
        'next_requirement':'Derive the dorsal ROI from visible pixels plus actual MCP positions, then examine mixed finger skinning/normal continuity there. Weight percentages alone do not define anatomy. No extra correction was performed after the one localized thin-fan repair.',
        'limits':'Ray hits and weights locate the defect; they do not alone prove whether local geometry, authored normals or mixed skinning is the dominant cause.'}
(HERE/'visual_roi_diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print('VISUAL_ROI_DIAGNOSED',[(r['pixel_xy'],r['source_face']) for r in results])
