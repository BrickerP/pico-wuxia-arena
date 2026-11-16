"""Anatomical finger dorsal/side PN-edge reconstruction; source geometry/skin immutable.
Host Python only. Existing repository GLB and LBS tools are used verbatim.
"""
import copy, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
SURFACE=HERE.parent/'palm-wrist-surface'
spec=importlib.util.spec_from_file_location('surface_builder',SURFACE/'build_surface.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
spec=importlib.util.spec_from_file_location('normal_tools',SURFACE/'production-patch/build_patch.py')
nt=importlib.util.module_from_spec(spec);spec.loader.exec_module(nt)
SOURCE=SURFACE/'production-patch/anatomical-crease/right_hand_patch.glb'
SOURCE_SHA='a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862'
POSES=[None,0.,.5,1.]

def unit(x):
 x=np.asarray(x);return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-20)

def anatomy(doc,binary,opened,normals,origin,axes,world):
 names={n.get('name'):i for i,n in enumerate(doc['nodes'])};D=-axes[2]
 dist=np.full(len(opened),1e6);owner=np.full(len(opened),-1,int);stations=np.zeros(len(opened));height=np.zeros(len(opened));frames=[]
 for di,digit in enumerate(['Index','Mid','Ring','Pinky']):
  joints=np.asarray([world[names['R_'+digit+str(i)]][:3,3] for i in [1,2,3]])
  tip=joints[2]+unit(joints[2]-joints[1])*.020
  chain=np.vstack([joints,tip]);lengths=np.linalg.norm(np.diff(chain,axis=0),axis=1);cumulative=np.r_[0,np.cumsum(lengths)]
  frames.append({'digit':digit,'MCP':joints[0].tolist(),'PIP':joints[1].tolist(),'DIP':joints[2].tolist(),'inferred_tip':tip.tolist(),'tip_policy':'20mm along PIP-DIP axis, used solely to delimit distal surface support','segment_lengths_m':lengths.tolist()})
  for si,(a,z) in enumerate(zip(chain[:-1],chain[1:])):
   e=z-a;length=np.linalg.norm(e);t=((opened-a)@e)/(length*length);clipped=np.clip(t,0,1);center=a+clipped[:,None]*e
   q=opened-center;rad=np.linalg.norm(q,axis=1);dorsal=unit(D-unit(e)*(D@unit(e)))
   eligible=(t>=-.04)&(t<=1.04)&(rad<.0165)&(rad>.002)&((normals@dorsal)>-.12)
   s=cumulative[si]+clipped*length
   eligible&=(s>.0035)&(s<cumulative[-1]-.002)&((q@dorsal)>-.0008)
   update=eligible&(rad<dist)
   dist[update]=rad[update];owner[update]=di;stations[update]=s[update];height[update]=(q@dorsal)[update]
 return owner,stations,height,frames

def main():
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
 doc,binary=b.h.read(SOURCE);pr=doc['meshes'][0]['primitives'][0]
 a={k:b.h.values(doc,binary,v) for k,v in pr['attributes'].items()}
 op,on,uv,j,w=[a[k] for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']]
 of=b.h.values(doc,binary,pr['indices']).reshape(-1,3).astype(int)
 origin,axes,world=b.basis(doc,binary);blends=[];poses=[];transforms=[]
 bind=b.h.values(doc,binary,doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 for time in POSES:
  worlds=b.h.sampled_worlds(doc,binary,None if time is None else 'grip',time or 0.)
  matrices=np.asarray([worlds[i] for i in doc['skins'][0]['joints']])@bind
  blend=np.sum(matrices[j.astype(int)]*w[:,:,None,None],axis=1)
  transforms.append(matrices);blends.append(blend);poses.append(b.h.skin(doc,binary,pr,worlds))
 opened=poses[1];normals=unit(np.einsum('vij,vj->vi',np.linalg.inv(blends[1][:,:3,:3]).transpose(0,2,1),on))
 owner,station,height,anatomical=anatomy(doc,binary,opened,normals,origin,axes,world)
 groups,reps,neighbors,opposites=b.adjacency(op,of)
 # Averaged geometric normals derive curvature from actual open surface, never from palette labels.
 gnormal=b.geometric_normals(opened,of)
 curve_normals=unit(.72*normals+.28*gnormal)
 indexed_edges={};geometric_edges={}
 for fi,face in enumerate(of):
  for x,y in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:
   key=tuple(sorted((int(groups[x]),int(groups[y]))));geometric_edges.setdefault(key,[]).append((int(x),int(y),fi))
 # One measured correction only: retain the seven failed/altered source parent triangles exactly.
 repair_faces=[71,120,204,299,310,494,673]
 blocked_edges=set()
 for face in of[repair_faces]:
  for x,y in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:blocked_edges.add(tuple(sorted((int(groups[x]),int(groups[y])))))
 selected={};rejected={'outside_anatomy':0,'low_curvature':0,'pose_geometry_or_normal':0,'skin_interpolation':0,'measured_local_repair':0}
 for key,rows in geometric_edges.items():
  if key in blocked_edges:
   rejected['measured_local_repair']+=1;continue
  x,y,_=rows[0]
  # Both endpoint controls must be on the same real-bone finger capsule and dorsal/side half.
  if owner[x]<0 or owner[x]!=owner[y] or any(owner[t]!=owner[x] for r in rows for t in r[:2]):
   rejected['outside_anatomy']+=1;continue
  e=opened[y]-opened[x];length=np.linalg.norm(e)
  if length<.002 or length>.022:
   rejected['low_curvature']+=1;continue
  nx,ny=curve_normals[x],curve_normals[y]
  delta=(ny*(e@ny)-nx*(e@nx))/8.
  delta-=unit(e)*(delta@unit(e))
  amount=np.linalg.norm(delta)
  if amount<.000045:
   rejected['low_curvature']+=1;continue
  # Preserve source joint ridges; bounded PN cubic midpoint softens only between controls.
  if amount>.0011:delta*=.0011/amount
  pj,pw=b.interpolate_weights([x,y],[.5,.5],j,w)
  candidate_blend=[np.sum(m[pj]*pw[:,None,None],axis=0) for m in transforms]
  reference=np.asarray([.5*(q[x]+q[y]) for q in poses]);raw=(op[x]+op[y])*.5
  linear=np.asarray([(mat@np.r_[raw,1])[:3] for mat in candidate_blend])
  if np.linalg.norm(linear-reference,axis=1).max()>.0005:
   rejected['skin_interpolation']+=1;continue
  target=.5*(opened[x]+opened[y])+delta
  pos=(np.linalg.inv(candidate_blend[1])@np.r_[target,1])[:3]
  actual=np.asarray([(mat@np.r_[pos,1])[:3] for mat in candidate_blend])
  # Reject any PN edge which folds either incident child against its source face in any pose.
  constraints=[];healthy=True
  for ti,q in enumerate(poses):
   for xx,yy,fi in rows:
    face=of[fi];source_cross=np.cross(q[face[1]]-q[face[0]],q[face[2]]-q[face[0]])
    third=next(int(v) for v in face if v not in (xx,yy))
    for child in [(xx,-1,third),(-1,yy,third)]:
     # rows edge order follows face winding.
     pts=np.asarray([actual[ti] if t<0 else q[t] for t in child]);cross=np.cross(pts[1]-pts[0],pts[2]-pts[0])
     if cross@source_cross<=1e-18:healthy=False;break
     constraints.append(np.linalg.inv(candidate_blend[ti][:3,:3])@unit(cross))
    if not healthy:break
   if not healthy:break
  preferred=unit(on[x]+on[y]);normal,ok=nt.feasible_normal(constraints,preferred)
  if not healthy or not ok:
   rejected['pose_geometry_or_normal']+=1;continue
  selected[key]={'position':pos,'delta_open':delta,'normal':normal,'joints':pj,'weights':pw,'owner':int(owner[x]),'edge':(x,y)}
 # Every geometric split is shared across all source UV/normal corners, preserving seam closure.
 out={k:list(v.copy()) for k,v in a.items()};edge_cache={};added=[]
 def mid(x,y,fi):
  key=tuple(sorted((int(groups[x]),int(groups[y]))))
  if key not in selected:return None
  indexed=tuple(sorted((int(x),int(y))))
  if indexed in edge_cache:return edge_cache[indexed]
  row=selected[key];idx=len(out['POSITION']);edge_cache[indexed]=idx
  values={'POSITION':row['position'],'NORMAL':row['normal'],'TEXCOORD_0':.5*(uv[x]+uv[y]),'JOINTS_0':row['joints'],'WEIGHTS_0':row['weights']}
  for semantic in out:out[semantic].append(values[semantic])
  ids=of[fi].tolist();bary=[.5 if t in (x,y) else 0. for t in ids]
  added.append({'candidate_vertex_id':idx,'source_face_id':int(fi),'source_vertex_ids':ids,'barycentric':bary,'source_edge':[int(x),int(y)],'bone_capsule_owner':['Index','Mid','Ring','Pinky'][row['owner']],'open_PN_displacement_m':row['delta_open'].tolist()})
  return idx
 faces=[];face_map=[]
 for fi,(x,y,z) in enumerate(of):
  x,y,z=map(int,(x,y,z));xy,yz,zx=mid(x,y,fi),mid(y,z,fi),mid(z,x,fi);count=sum(t is not None for t in [xy,yz,zx])
  if count==0:sub=[(x,y,z)]
  elif count==3:sub=[(x,xy,zx),(xy,y,yz),(zx,yz,z),(xy,yz,zx)]
  elif count==1:
   if xy is not None:sub=[(x,xy,z),(xy,y,z)]
   elif yz is not None:sub=[(y,yz,x),(yz,z,x)]
   else:sub=[(z,zx,y),(zx,x,y)]
  elif xy is None:sub=[(z,zx,yz),(zx,x,y),(zx,y,yz)]
  elif yz is None:sub=[(x,xy,zx),(xy,y,z),(xy,z,zx)]
  else:sub=[(y,yz,xy),(yz,z,x),(yz,x,xy)]
  faces.extend(sub);face_map.extend([fi]*len(sub))
 out={k:np.asarray(v,dtype=a[k].dtype) for k,v in out.items()};faces=np.asarray(faces,dtype='<u4');face_map=np.asarray(face_map,int)
 # Re-evaluate added normals against actual multi-edge child geometry, across all four poses.
 for row in added:
  idx=row['candidate_vertex_id'];incident=np.flatnonzero((faces==idx).any(1));constraints=[]
  for ti in range(4):
   matrices=transforms[ti];blend=np.sum(matrices[out['JOINTS_0'].astype(int)]*out['WEIGHTS_0'][:,:,None,None],axis=1)
   pts=np.einsum('vij,vj->vi',blend,np.column_stack((out['POSITION'],np.ones(len(out['POSITION'])))))[:,:3]
   crosses=np.cross(pts[faces[incident,1]]-pts[faces[incident,0]],pts[faces[incident,2]]-pts[faces[incident,0]])
   constraints.extend(np.einsum('ij,vj->vi',np.linalg.inv(blend[idx,:3,:3]),unit(crosses)))
  normal,ok=nt.feasible_normal(constraints,out['NORMAL'][idx])
  if not ok:raise ValueError('Added corner cannot satisfy four-pose geometry: '+str(idx))
  out['NORMAL'][idx]=normal
 # Root authorizes the one anatomically proven non-protected source normal corner.
 normal_repairs=[1475];normal_proof=[]
 for idx in normal_repairs:
  assert owner[idx]>=0 and height[idx]>-.0008, 'Normal repair must be in true dorsal/side capsule'
  incident=np.flatnonzero((faces==idx).any(1));constraints=[]
  for ti in range(4):
   blend=np.sum(transforms[ti][out['JOINTS_0'].astype(int)]*out['WEIGHTS_0'][:,:,None,None],axis=1)
   pts=np.einsum('vij,vj->vi',blend,np.column_stack((out['POSITION'],np.ones(len(out['POSITION'])))))[:,:3]
   crosses=np.cross(pts[faces[incident,1]]-pts[faces[incident,0]],pts[faces[incident,2]]-pts[faces[incident,0]])
   constraints.extend(np.einsum('ij,vj->vi',np.linalg.inv(blend[idx,:3,:3]),unit(crosses)))
  normal,ok=nt.feasible_normal(constraints,on[idx]);assert ok,'Shared original corner lacks a four-pose feasible normal'
  out['NORMAL'][idx]=normal
  normal_proof.append({'source_vertex_id':idx,'capsule_owner':['Index','Mid','Ring','Pinky'][owner[idx]],'station_distal_MCP_m':float(station[idx]),'dorsal_height_m':float(height[idx]),'source_normal':on[idx].tolist(),'candidate_normal':out['NORMAL'][idx].tolist(),'angle_degrees':float(np.degrees(np.arccos(np.clip(on[idx]@out['NORMAL'][idx],-1,1)))),'candidate_incident_faces':incident.tolist(),'source_parent_faces':np.unique(face_map[incident]).tolist(),'four_pose_min_face_normal_dot':float((unit(np.asarray(constraints))@out['NORMAL'][idx]).min()),'root_authorization':'2026-11-17 necessary anatomy-bounded normal repair; original POSITION/UV/JOINTS/WEIGHTS immutable'})
 actual=copy.deepcopy(doc);packed=bytearray(binary);pr=actual['meshes'][0]['primitives'][0]
 for semantic,kind,component in [('POSITION','VEC3',5126),('NORMAL','VEC3',5126),('TEXCOORD_0','VEC2',5126),('JOINTS_0','VEC4',5123),('WEIGHTS_0','VEC4',5126)]:pr['attributes'][semantic]=b.append_stream(actual,packed,out[semantic],kind,component)
 pr['indices']=b.append_stream(actual,packed,faces.reshape(-1),'SCALAR',5125);packed.extend(b'\0'*(-len(packed)%4));actual['buffers'][0]['byteLength']=len(packed)
 output=HERE/'right_hand_finger.glb';output.write_bytes(b.encode_glb(actual,bytes(packed)))
 total=len(faces)+sum(doc['accessors'][p['indices']]['count']//3 for p in doc['meshes'][0]['primitives'][1:]);assert total<=9000
 roi=np.flatnonzero(np.bincount(face_map,minlength=len(of))>1)
 delta={'schema':'anatomical-finger-PN-edge-v1','source':str(SOURCE.relative_to(b.REPO)),'source_sha256':SOURCE_SHA,'candidate':str(output.relative_to(b.REPO)),'candidate_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'source_vertex_count':len(op),'source_face_count':len(of),'candidate_vertex_count':len(out['POSITION']),'candidate_face_count':len(faces),'candidate_total_triangles':int(total),'candidate_vertex_to_source':list(range(len(op)))+[-1]*len(added),'candidate_face_to_source':face_map.tolist(),'candidate_added_vertices':added,'protected_source_vertices':[i for i in range(len(op)) if i not in normal_repairs],'modified_source_vertices':normal_repairs,'original_normal_changed_vertex_ids':normal_repairs,'normal_repair_proof':normal_proof,'ROI_faces':roi.tolist(),'normal_split_vertices':[],'anatomy':{'space':'actual grip0 LBS canonical meters','hand_origin':origin.tolist(),'axes':axes.tolist(),'bones':anatomical,'rule':'closest actual MCP-PIP-DIP bone segment capsule; radius2-16.5mm, >=3.5mm distal MCP; dorsal/side signed height>-.8mm and outward normal dot local dorsal>-.12; no palette-based anatomical classification','source_vertex_ids_in_anatomical_domain':np.flatnonzero(owner>=0).tolist()},'method':'Single conforming PN cubic edge midpoint using72% authored open normal plus28% geometric normal; source positions/UV/skin and all protected attributes bitwise immutable; only anatomically proven nonprotected original normal1475 is minimally reprojected against all four-pose incident child faces; no circular cylinder fit, smoothing or material edit; midpoint UV/weights source-face barycentric; max1.1mm curved offset and max.5mm undeformed LBS residual; four-pose geometric and normal precheck','single_measured_correction':{'frozen_source_parents':repair_faces,'reason':'First actual candidate parent494 geometry reversed;71/673 original-corner normal conflict;120/310 added crossing;204/299 removed inherited crossing. All seven parents and shared geometric edges retained exactly, no threshold relaxation.','initial_candidate_sha256':'013ffb9a44ac3f72490e56f0e1ca12ec3de80a9905f2f32112374910b4df0341'},'selected_geometric_edges':len(selected),'rejected_edges':rejected,'open_added_displacement_mm':{'max':float(max((np.linalg.norm(r['delta_open']) for r in selected.values()),default=0)*1000),'mean':float(np.mean([np.linalg.norm(r['delta_open']) for r in selected.values()])*1000)},'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
 (HERE/'finger_delta.json').write_text(json.dumps(delta,indent=2)+'\n')
 print(json.dumps({'candidate':str(output),'sha256':delta['candidate_sha256'],'triangles':int(total),'selected_edges':len(selected),'added_vertices':len(added),'PN_displacement_mm':delta['open_added_displacement_mm'],'rejected':rejected}))
if __name__=='__main__':main()
