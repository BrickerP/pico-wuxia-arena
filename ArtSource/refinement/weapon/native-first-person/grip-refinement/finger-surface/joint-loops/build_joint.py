"""True joint-plane loops and anatomy-parameterized dorsal surface reconstruction."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('finger_common',HERE.parent/'build_finger.py');old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
b=old.b;h=b.h;unit=old.unit;SOURCE=old.SOURCE;SOURCE_SHA=old.SOURCE_SHA

def features(s,theta,lp,ld,total):
 u=s/total;cols=[]
 harmonics=[np.ones_like(theta),np.cos(theta),np.sin(theta),np.cos(2*theta),np.sin(2*theta)]
 for power in range(4):
  for angle in harmonics:cols.append(u**power*angle)
 for joint,width in [(lp,.009),(ld,.006)]:
  bump=np.exp(-.5*((s-joint)/width)**2)
  for angle in harmonics:cols.append(bump*angle)
 return np.column_stack(cols)

def coordinates(points,frame):
 origin=np.asarray(frame['MCP']);axis=np.asarray(frame['axis']);D=np.asarray(frame['dorsal']);R=np.asarray(frame['radial']);chain=np.asarray(frame['chain']);stations=np.asarray(frame['stations'])
 s=(points-origin)@axis;center=np.column_stack([np.interp(s,stations,chain[:,k]) for k in range(3)])
 radial=points-center;z=radial@D;x=radial@R;theta=np.arctan2(x,z);radius=np.sqrt(x*x+z*z)
 return s,theta,radius,center

def surface_points(st,theta,frame,coef):
 stations=np.asarray(frame['stations']);chain=np.asarray(frame['chain']);center=np.column_stack([np.interp(st,stations,chain[:,k]) for k in range(3)])
 radius=np.clip(features(st,theta,stations[1],stations[2],stations[-1])@coef,.004,.0155)
 radial=np.cos(theta)[:,None]*np.asarray(frame['dorsal'])+np.sin(theta)[:,None]*np.asarray(frame['radial'])
 return center+radius[:,None]*radial

def main():
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_SHA
 doc,binary=h.read(SOURCE);pr=doc['meshes'][0]['primitives'][0];a={k:h.values(doc,binary,v) for k,v in pr['attributes'].items()};of=h.values(doc,binary,pr['indices']).reshape(-1,3).astype(int)
 op,on,uv,oj,ow=[a[k] for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']]
 origin,axes,world=b.basis(doc,binary);opened=h.skin(doc,binary,pr,world);blend=b.blended_transforms(doc,binary,oj.astype(int),ow.astype(float),world);normal=unit(np.einsum('vij,vj->vi',np.linalg.inv(blend[:,:3,:3]).transpose(0,2,1),on))
 owner,station,height,bones=old.anatomy(doc,binary,opened,normal,origin,axes,world)
 frames=[];nearest=np.full(len(op),1e9);all_owner=np.full(len(op),-1,int)
 for di,row in enumerate(bones):
  chain=np.asarray([row['MCP'],row['PIP'],row['DIP'],row['inferred_tip']]);axis=unit(chain[2]-chain[0]);D=unit(-axes[2]-axis*((-axes[2])@axis));R=unit(np.cross(axis,D));ss=(chain-chain[0])@axis
  frame={**row,'axis':axis.tolist(),'dorsal':D.tolist(),'radial':R.tolist(),'chain':chain.tolist(),'stations':ss.tolist()};frames.append(frame)
  s,t,r,c=coordinates(opened,frame);eligible=(s>=0)&(s<=ss[-1])&(r>.002)&(r<.017)
  better=eligible&(r<nearest);nearest[better]=r[better];all_owner[better]=di
 fits=[]
 for di,frame in enumerate(frames):
  ids=np.flatnonzero(all_owner==di);s,t,r,c=coordinates(opened[ids],frame);ss=frame['stations'];X=features(s,t,ss[1],ss[2],ss[-1]);penalty=np.eye(X.shape[1])*.002;penalty[:5,:5]=0
  coef=np.linalg.lstsq(np.vstack([X,penalty]),np.r_[r,np.zeros(len(penalty))],rcond=None)[0]
  for _ in range(2):
   residual=r-X@coef;scale=max(float(np.median(abs(residual-np.median(residual))))*1.4826,.0005);ww=np.minimum(1,1.5*scale/np.maximum(abs(residual),1e-12));coef=np.linalg.lstsq(np.vstack([X*ww[:,None],penalty]),np.r_[r*ww,np.zeros(len(penalty))],rcond=None)[0]
  fits.append(coef);frame['fit_source_vertices']=ids.tolist();frame['fit_rms_mm']=float(np.sqrt(np.mean((r-X@coef)**2))*1000)
 # Measured source-parent failures retain their full controls and geometric boundary.
 repair_parents=[255,299,361,362,379,410,473,487,519,520,539,540,564,573,606,649,666,671,674,710,718,740,745,800]
 source_weld=b.weld(op);repair_groups=np.unique(source_weld[of[repair_parents]])
 repair_vertices=np.flatnonzero(np.isin(source_weld,repair_groups));blocked_edges=set()
 for face in of[repair_parents]:
  for x,y in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:blocked_edges.add(tuple(sorted((int(source_weld[x]),int(source_weld[y])))))
 # Do not subdivide zero-edit source sectors: mixed-bone LBS and source-face subdivision do not commute.
 preview=np.zeros(len(op))
 for di,fr in enumerate(frames):
  ids=np.flatnonzero(owner==di);ss=fr['stations'];st,th,rr,cc=coordinates(opened[ids],fr)
  near=np.maximum.reduce([np.exp(-.5*((st-.012)/.010)**2),np.exp(-.5*((st-ss[1])/.014)**2),np.exp(-.5*((st-ss[2])/.009)**2)])
  dd=np.linalg.norm(opened[ids,None,:]-opened[repair_vertices][None,:,:],axis=2).min(1)
  preview[ids]=b.smoothstep(.0035,.010,st)*(1-b.smoothstep(ss[2]+.008,ss[2]+.016,st))*b.smoothstep(-.0008,.0035,height[ids])*near*b.smoothstep(.002,.010,dd)
 for group in np.unique(source_weld):
  ids=np.flatnonzero(source_weld==group)
  if (owner[ids]<0).any() or len(set(owner[ids]))!=1:preview[ids]=0
  else:preview[ids]=preview[ids].min()
 for face in of:
  for x,y in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:
   if max(preview[x],preview[y])<=.001:blocked_edges.add(tuple(sorted((int(source_weld[x]),int(source_weld[y])))))
 # Source-pinned anatomical cross-section planes: real joint centers and support rings.
 cuts=[]
 for di,fr in enumerate(frames):
  ss=fr['stations'];axis=np.asarray(fr['axis']);mcp=np.asarray(fr['MCP'])
  for joint,center,offsets in [('MCP',0.,[.005,.009,.014]),('PIP',ss[1],[-.008,-.004,0,.004,.008]),('DIP',ss[2],[-.005,-.0025,0,.0025,.005])]:
   for off in offsets:cuts.append({'digit':di,'joint':joint,'offset_m':off,'station_m':float(center+off),'normal':axis,'center':mcp+axis*(center+off)})
 # A parent triangle is cut only where its reference is inside a single actual dorsal finger domain.
 # Boundary neighbors sharing selected source edges receive identical linear support samples.
 edge_cuts={};face_cuts={}
 for fi,face in enumerate(of):
  if fi in repair_parents or preview[face].max()<=.001:continue
  valid=owner[face];known=valid[valid>=0]
  if len(known)<2 or len(np.unique(known))!=1:continue
  di=int(known[0])
  for ci,cut in enumerate(cuts):
   if cut['digit']!=di:continue
   signed=(opened[face]-cut['center'])@cut['normal']
   if signed.min()>=-1e-7 or signed.max()<=1e-7:continue
   crossings=[]
   for x,y in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:
    sx=float((opened[x]-cut['center'])@cut['normal']);sy=float((opened[y]-cut['center'])@cut['normal'])
    if sx*sy>=0:continue
    t=sx/(sx-sy);q=opened[x]*(1-t)+opened[y]*t;n=unit(normal[x]*(1-t)+normal[y]*t)
    # The point itself is proven against real bone capsules; endpoints need not both be eligible.
    qowner,_,_,_=old.anatomy(doc,binary,q[None,:],n[None,:],origin,axes,world)
    if qowner[0]!=di:crossings=[];break
    key=tuple(sorted((int(source_weld[x]),int(source_weld[y]))));tt=t if source_weld[x]<source_weld[y] else 1-t
    if key in blocked_edges:crossings=[];break
    crossings.append((key,float(tt),ci))
   if len(crossings)==2:
    face_cuts.setdefault(fi,[]).append(ci)
    for key,t,ci in crossings:edge_cuts.setdefault(key,[]).append((t,ci))
 # Each source triangle is partitioned by its actual joint planes. Per-corner UV seams remain separate.
 vertex_cache={};output=[{i:1.} for i in range(len(op))];poly_faces=[];fm=[];loop_records=[]
 def vertex(prov,fi):
  nz={int(k):float(v) for k,v in prov.items() if v>1e-9};total=sum(nz.values());nz={k:v/total for k,v in nz.items()}
  if len(nz)==1:return next(iter(nz))
  key=tuple((k,round(v,9)) for k,v in sorted(nz.items()))
  if key not in vertex_cache:vertex_cache[key]=len(output);output.append(nz)
  return vertex_cache[key]
 def blendprov(a,b,t):
  out={k:(1-t)*v for k,v in a.items()}
  for k,v in b.items():out[k]=out.get(k,0)+t*v
  return out
 def point(prov):return sum(opened[k]*v for k,v in prov.items())
 for fi,face in enumerate(of):
  polygons=[[{int(v):1.} for v in face]]
  for ci in face_cuts.get(fi,[]):
   cut=cuts[ci];next_polys=[]
   for poly in polygons:
    side=np.asarray([(point(p)-cut['center'])@cut['normal'] for p in poly])
    if side.min()>-1e-8 or side.max()<1e-8:next_polys.append(poly);continue
    for sign in [1,-1]:
     out=[]
     for i,A in enumerate(poly):
      j=(i+1)%len(poly);B=poly[j];da,db=side[i]*sign,side[j]*sign
      if da>=-1e-9:out.append(A)
      if da*db<0:out.append(blendprov(A,B,float(da/(da-db))))
     if len(out)>=3:next_polys.append(out)
   polygons=next_polys
  # Inject all source-edge samples selected by neighboring parents into every boundary edge.
  injected=[]
  for poly in polygons:
   seq=[]
   for i,A in enumerate(poly):
    B=poly[(i+1)%len(poly)];seq.append(A);support=set(A)|set(B)
    if len(support)!=2:continue
    x,y=sorted(support);ta=A.get(y,0);tb=B.get(y,0)
    gkey=tuple(sorted((int(source_weld[x]),int(source_weld[y]))))
    chart_samples=[t if source_weld[x]<source_weld[y] else 1-t for t,_ in edge_cuts.get(gkey,[])]
    samples=sorted({round(t,9):t for t in chart_samples if min(ta,tb)+1e-8<t<max(ta,tb)-1e-8}.values(),reverse=tb<ta)
    seq.extend({x:1-t,y:t} for t in samples)
   injected.append(seq)
  for poly in injected:
   ids=[vertex(p,fi) for p in poly]
   # Constrained convex-polygon ear clipping preserves every anatomical ring/UV edge,
   # and eliminates the independent centroid skin samples which caused actual LBS bubbles.
   children=[];remaining=list(range(len(ids)));xyz=np.asarray([point(p) for p in poly])
   face_normal=unit(np.cross(opened[face[1]]-opened[face[0]],opened[face[2]]-opened[face[0]]))
   while len(remaining)>3:
    ears=[]
    for ri,index in enumerate(remaining):
     prev=remaining[ri-1];nxt=remaining[(ri+1)%len(remaining)];tri=xyz[[prev,index,nxt]]
     area=float(np.cross(tri[1]-tri[0],tri[2]-tri[0])@face_normal)
     if area<=1e-14:continue
     occupied=False
     for other in remaining:
      if other in (prev,index,nxt):continue
      signs=[float(np.cross(tri[(k+1)%3]-tri[k],xyz[other]-tri[k])@face_normal) for k in range(3)]
      if min(signs)>=-1e-14:occupied=True;break
     if not occupied:
      quality=area/max(float(np.sum((tri-np.roll(tri,1,axis=0))**2)),1e-20);ears.append((quality,ri,prev,index,nxt))
    if not ears:raise ValueError('No positive constrained ear for source parent '+str(fi))
    _,ri,prev,index,nxt=max(ears);children.append([ids[prev],ids[index],ids[nxt]]);remaining.pop(ri)
   children.append([ids[i] for i in remaining])
   for child in children:poly_faces.append(child);fm.append(fi)
 f=np.asarray(poly_faces,int);fm=np.asarray(fm,int)
 # Build actual reference points, exact source UVs and source-face-local skin interpolation.
 p=[];n=[];u=[];j=[];w=[];added=[]
 incident=[set() for _ in op]
 for fi,face in enumerate(of):
  for v in face:incident[v].add(fi)
 for idx,prov in enumerate(output):
  ids=list(prov);coef=np.asarray(list(prov.values()));p.append(coef@op[ids]);n.append(unit(coef@on[ids]));u.append(coef@uv[ids]);jj,ww=b.interpolate_weights(ids,coef,oj,ow);j.append(jj);w.append(ww)
  if idx>=len(op):
   parent=min(set.intersection(*(incident[t] for t in ids)));vertices=of[parent].tolist();added.append({'candidate_vertex_id':idx,'source_face_id':parent,'source_vertex_ids':vertices,'barycentric':[prov.get(v,0.) for v in vertices]})
 p,n,u,j,w=np.asarray(p),np.asarray(n),np.asarray(u),np.asarray(j),np.asarray(w)
 # Original palette order/float payload is kept until a measured skinning cause warrants a local weight edit.
 j[:len(op)]=oj;w[:len(op)]=ow;n[:len(op)]=on
 newblend=b.blended_transforms(doc,binary,j.astype(int),w,world);reference=np.asarray([sum(opened[k]*v for k,v in row.items()) for row in output]);open_normals=unit(np.asarray([sum(normal[k]*v for k,v in row.items()) for row in output]))
 own,sta,hei,_=old.anatomy(doc,binary,reference,open_normals,origin,axes,world);strength=np.zeros(len(p));target=reference.copy();fit_proof=[]
 for di,fr in enumerate(frames):
  ids=np.flatnonzero(own==di);ss=fr['stations'];s,theta,r,center=coordinates(reference[ids],fr);pred=features(s,theta,ss[1],ss[2],ss[-1])@fits[di]
  pred=np.clip(pred,.004,.0155)
  # Measured varying Fourier sections preserve noncircular sides and real joint bulges.
  near=np.maximum.reduce([np.exp(-.5*((s-.012)/.010)**2),np.exp(-.5*((s-ss[1])/.014)**2),np.exp(-.5*((s-ss[2])/.009)**2)])
  fade=b.smoothstep(.0035,.010,s)*(1-b.smoothstep(ss[2]+.008,ss[2]+.016,s))*b.smoothstep(-.0008,.0035,hei[ids])*near
  shift=np.clip(pred-r,-.0025,.0025)*fade
  radial=unit(reference[ids]-center);target[ids]=reference[ids]+radial*shift[:,None];strength[ids]=fade
  fit_proof.append({'digit':fr['digit'],'originals_moved_candidates':ids[ids<len(op)].tolist(),'radius_delta_max_mm':float(abs(shift).max()*1000),'fit_rms_mm':fr['fit_rms_mm']})
 # A single geometric-distance feather around actual failed parents avoids abrupt repaired borders.
 distance=np.linalg.norm(reference[:,None,:]-opened[repair_vertices][None,:,:],axis=2).min(1)
 repair_fade=b.smoothstep(.002,.010,distance)
 target=reference+(target-reference)*repair_fade[:,None];strength*=repair_fade
 # A new interior ring sample may not bypass a protected/feathered original parent field.
 source_strength=strength[:len(op)].copy()
 for idx in range(len(op),len(output)):
  limit=sum(source_strength[k]*v for k,v in output[idx].items());capped=min(float(strength[idx]),float(limit))
  if strength[idx]>1e-12:target[idx]=reference[idx]+(target[idx]-reference[idx])*(capped/strength[idx])
  strength[idx]=capped
 # Exact source bind-position seams share geometric/skin edits, while UV and normal corners remain separate.
 refbind=np.asarray([sum(op[k]*v for k,v in row.items()) for row in output]);weld=b.weld(refbind)
 for group in np.unique(weld):
  ids=np.flatnonzero(weld==group)
  if len(ids)<2:continue
  if (own[ids]<0).any() or len(set(own[ids]))!=1:
   strength[ids]=0;target[ids]=reference[ids]
  else:
   strength[ids]=strength[ids].min();target[ids]=target[ids].mean(0)
 # Joint-local interpolation removes measured cross-finger spill and inconsistent axial ramps.
 names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']];dense=np.zeros((len(op),len(names)))
 for slot in range(4):np.add.at(dense,(np.arange(len(op)),oj[:,slot]),ow[:,slot])
 weight_proof=[]
 for di,fr in enumerate(frames):
  sources=np.flatnonzero(owner==di);ss,tt,_,_=coordinates(opened[sources],fr);ids=np.flatnonzero((own==di)&(strength>.001));ts,th,_,_=coordinates(reference[ids],fr)
  keep=['R_Hand',*['R_'+fr['digit']+str(i) for i in [1,2,3]]];palette=[names.index(name) for name in keep]
  for idx,st,theta in zip(ids,ts,th):
   angular=np.abs((tt-theta+np.pi)%(2*np.pi)-np.pi);valid=(abs(ss-st)<=.020)&(angular<=1.2)
   choices=np.flatnonzero(valid)
   if not len(choices):continue
   metric=((ss[choices]-st)/.010)**2+(angular[choices]/.7)**2;selected=choices[np.argsort(metric)[:6]];metric=((ss[selected]-st)/.010)**2+(angular[selected]/.7)**2;coef=np.exp(-.5*metric);coef/=coef.sum();anchors=sources[selected]
   profile=coef@dense[anchors];filtered=np.zeros(len(names));filtered[palette]=profile[palette]
   if filtered.sum()<1e-8:continue
   filtered/=filtered.sum();base_ids=list(output[idx]);base_coef=np.asarray(list(output[idx].values()));base=base_coef@dense[base_ids];factor=.75*float(strength[idx]);result=(1-factor)*base+factor*filtered;order=np.argsort(result)[::-1][:4];result=result[order];result/=result.sum();j[idx]=order;w[idx]=result
   weight_proof.append({'candidate_vertex_id':int(idx),'source_vertex_ids':anchors.tolist(),'coefficients':coef.tolist(),'digit':fr['digit'],'keep_joint_names':keep,'target_station_m':float(st),'anchor_stations_m':ss[selected].tolist(),'axial_halfwidth_m':.020,'angular_halfwidth_rad':1.2,'blend_factor':factor,'base_source_vertex_ids':base_ids,'base_coefficients':base_coef.tolist()})
 # Weight-equivalent geometric source seams must remain identical under all poses.
 byvertex={r['candidate_vertex_id']:r for r in weight_proof}
 for group in np.unique(weld):
  ids=np.flatnonzero(weld==group)
  if len(ids)<2 or not (own[ids]>=0).all():continue
  chosen=next((int(i) for i in ids if i in byvertex),None)
  if chosen is None:continue
  for idx in ids:
   j[idx]=j[chosen];w[idx]=w[chosen]
   if idx not in byvertex:
    row=copy.deepcopy(byvertex[chosen]);row['candidate_vertex_id']=int(idx);weight_proof.append(row);byvertex[int(idx)]=row
 # New loop samples interpolate the finalized original-control field, never a second independent field.
 control_dense=np.zeros((len(op),len(names)))
 for slot in range(4):np.add.at(control_dense,(np.arange(len(op)),j[:len(op),slot].astype(int)),w[:len(op),slot])
 weight_proof=[row for row in weight_proof if row['candidate_vertex_id']<len(op)]
 for idx in range(len(op),len(output)):
  controls=list(output[idx]);coef=np.asarray(list(output[idx].values()));profile=coef@control_dense[controls];order=np.argsort(profile)[::-1][:4];values=profile[order];values/=values.sum();j[idx]=order;w[idx]=values
  weight_proof.append({'kind':'updated_control_barycentric','candidate_vertex_id':idx,'control_source_vertex_ids':controls,'control_coefficients':coef.tolist()})
 byvertex={r['candidate_vertex_id']:r for r in weight_proof}
 newblend=b.blended_transforms(doc,binary,j.astype(int),w,world)
 # Open positions are inverse-LBS projections; no source bone, joint length or anchor edit.
 active=np.flatnonzero(strength>.001);p[active]=np.einsum('vij,vj->vi',np.linalg.inv(newblend[active]),np.column_stack((target[active],np.ones(len(active)))))[:,:3]
 # Compute finite four-pose geometry and constrain normals to the actual new incident faces.
 poses=[];inverse=[]
 for time in old.POSES:
  wr=h.sampled_worlds(doc,binary,None if time is None else 'grip',time or 0.);bb=b.blended_transforms(doc,binary,j.astype(int),w,wr);poses.append(np.einsum('vij,vj->vi',bb,np.column_stack((p,np.ones(len(p)))))[:,:3]);inverse.append(np.linalg.inv(bb[:,:3,:3]))
 cross=[unit(np.cross(q[f[:,1]]-q[f[:,0]],q[f[:,2]]-q[f[:,0]])) for q in poses]
 # Smooth normals come from the actual fitted anatomical surface derivatives, not triangle area averages.
 smooth_open=open_normals.copy()
 for di,fr in enumerate(frames):
  ids=np.flatnonzero(own==di);st,theta,rr,cc=coordinates(reference[ids],fr)
  ds=(surface_points(st+.0001,theta,fr,fits[di])-surface_points(st-.0001,theta,fr,fits[di]))/.0002
  dt=(surface_points(st,theta+.002,fr,fits[di])-surface_points(st,theta-.002,fr,fits[di]))/.004
  analytic=unit(np.cross(dt,ds));radial=unit(reference[ids]-cc);analytic=np.where((analytic*radial).sum(1)[:,None]<0,-analytic,analytic)
  fac=strength[ids,None];smooth_open[ids]=unit((1-fac)*open_normals[ids]+fac*analytic)
 preferred=unit(np.einsum('vji,vj->vi',newblend[:,:3,:3],smooth_open))
 vm=list(range(len(op)))+[-1]*len(added);data=[list(p),list(n),list(u),list(j),list(w)];splits=[]
 # A legal original normal can need a minimal update even where its position/skin feather is zero.
 changed_norm_geometry=np.zeros(len(f),bool)
 for ti,time in enumerate(old.POSES):
  wr=h.sampled_worlds(doc,binary,None if time is None else 'grip',time or 0.);sp=h.skin(doc,binary,doc['meshes'][0]['primitives'][0],wr);sc=unit(np.cross(sp[of[:,1]]-sp[of[:,0]],sp[of[:,2]]-sp[of[:,0]]))
  changed_norm_geometry|=np.linalg.norm(cross[ti]-sc[fm],axis=1)>1e-5
 normal_support=set(np.unique(f[changed_norm_geometry]).tolist())
 for idx in normal_support:
  if idx<len(op) and strength[idx]<=.001:preferred[idx]=on[idx]
 mutable=set(active.tolist())|set(range(len(op),len(p)))|{idx for idx in normal_support if idx<len(op) and own[idx]>=0}
 for idx in sorted(mutable):
  if idx<len(op) and own[idx]<0:continue
  faces=np.flatnonzero((f==idx).any(1));constraints=[inverse[t][idx]@cross[t][fi] for t in range(4) for fi in faces]
  norm,ok=old.nt.feasible_normal(constraints,preferred[idx])
  if ok:data[1][idx]=norm;continue
  for fi in faces:
   constraints=[inverse[t][idx]@cross[t][fi] for t in range(4)];norm,ok=old.nt.feasible_normal(constraints,preferred[idx])
   if not ok:continue
   new=len(data[0])
   for arr,oldarr in zip(data,[p,n,u,j,w]):arr.append(oldarr[idx].copy())
   data[1][-1]=norm;vm.append(vm[idx]);splits.append(new);f[fi,f[fi]==idx]=new
   if idx in byvertex:
    proof=copy.deepcopy(byvertex[idx]);proof['candidate_vertex_id']=new;weight_proof.append(proof)
   if idx>=len(op):
    row=copy.deepcopy(next(r for r in added if r['candidate_vertex_id']==idx));row['candidate_vertex_id']=new;added.append(row)
 p,n,u,j,w=[np.asarray(x,dtype=t) for x,t in zip(data,['<f4','<f4','<f4','<u2','<f4'])]
 # Dense differences exclude harmless float32 palette/rounding differences from the changed-ID claim.
 actual_dense=np.zeros((len(p),len(names)))
 for slot in range(4):np.add.at(actual_dense,(np.arange(len(p)),j[:,slot].astype(int)),w[:,slot])
 real_weight_changes=[]
 added_lookup={row['candidate_vertex_id']:row for row in added}
 for row in weight_proof:
  idx=row['candidate_vertex_id'];source_id=vm[idx]
  if source_id>=0:baseline=dense[source_id]
  else:
   origin_row=added_lookup[idx];baseline=np.asarray(origin_row['barycentric'])@dense[origin_row['source_vertex_ids']]
  if np.max(abs(actual_dense[idx]-baseline))>=2e-6:real_weight_changes.append(idx)
 actual=copy.deepcopy(doc);packed=bytearray(binary);pr=actual['meshes'][0]['primitives'][0]
 for semantic,arr,kind,component in [('POSITION',p,'VEC3',5126),('NORMAL',n,'VEC3',5126),('TEXCOORD_0',u,'VEC2',5126),('JOINTS_0',j,'VEC4',5123),('WEIGHTS_0',w,'VEC4',5126)]:pr['attributes'][semantic]=b.append_stream(actual,packed,arr,kind,component)
 pr['indices']=b.append_stream(actual,packed,f.astype('<u4').reshape(-1),'SCALAR',5125);packed.extend(b'\0'*(-len(packed)%4));actual['buffers'][0]['byteLength']=len(packed)
 path=HERE/'right_hand_joint.glb';path.write_bytes(b.encode_glb(actual,bytes(packed)))
 moved=np.flatnonzero(np.any(p[:len(op)]!=op,axis=1));norms=np.unique([src for idx,src in enumerate(vm) if src>=0 and np.any(n[idx]!=on[src])]);weights_changed=np.flatnonzero(np.any(j[:len(op)]!=oj,axis=1)|np.any(w[:len(op)]!=ow,axis=1));modified=sorted(set(moved.tolist())|set(norms.tolist())|set(weights_changed.tolist()));roi=np.unique(np.r_[fm[np.bincount(fm,minlength=len(of))[fm]>1],np.flatnonzero(np.isin(of,modified).any(1))]);total=len(f)+255
 assert total<=12000,(total,len(p),len(cuts))
 delta={'schema':'anatomical-joint-loop-v1','source':str(SOURCE.relative_to(b.REPO)),'source_sha256':SOURCE_SHA,'candidate':str(path.relative_to(b.REPO)),'candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_vertex_count':len(op),'source_face_count':len(of),'candidate_vertex_count':len(p),'candidate_face_count':len(f),'candidate_total_triangles':total,'candidate_vertex_to_source':vm,'candidate_face_to_source':fm.tolist(),'candidate_added_vertices':added,'moved_source_vertices':moved.tolist(),'original_normal_changed_vertex_ids':norms.tolist(),'original_weight_changed_vertex_ids':weights_changed.tolist(),'candidate_weight_changed_vertex_ids':real_weight_changes,'weight_change_projections':weight_proof,'modified_source_vertices':modified,'protected_source_vertices':sorted(set(range(len(op)))-set(modified)),'ROI_faces':roi.tolist(),'normal_split_vertices':splits,'anatomy':{'hand_origin':origin.tolist(),'axes':axes.tolist(),'bones':frames,'source_vertex_ids_in_anatomical_domain':np.flatnonzero(owner>=0).tolist()},'joint_planes':[{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in c.items()} for c in cuts],'source_cut_parents':sorted(face_cuts),'edit_strength_source':source_strength.tolist(),'edit_strength_candidate':strength.tolist(),'edit_field_constraint':'New point edit strength <= source-parent original-control barycentric strength. This bounds both radial shape and local weight profile, preventing long-parent interior bubbles around protected source controls.','section_fit':fit_proof,'measured_failure_repair':{'source_parents':repair_parents,'contact_buffer_parents':[255,299,379,410,520,540],'source_vertices_frozen':repair_vertices.tolist(),'feather_distance_m':[.002,.010],'initial_candidate_sha256':'f432356e9743c11bbb752bb45cd3777df9891e55cbd5c115ccdf10eb3b6110d9','new_weight_field_rule':'Every inserted joint-loop point barycentrically interpolates final modified original-control dense weights, then top4 normalizes; no independent interior profile.', 'reason':'Actual final-child geometry and normal failures; preserve full parents and their welded edges, with source-distance local skin/shape feather. UV chart cuts now propagate by welded geometric edge rather than indexed chart edge.'},'source_positions_max_shift_mm':float(np.linalg.norm(p[:len(op)]-op,axis=1).max()*1000),'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Constrained ear-clipped joint strips, no independent centroid fan. Anatomical joint-plane polygon clipping creates MCP/PIP/DIP transverse loops; full-finger varying 4 axial x 5 angular Fourier sections plus separate PIP/DIP Gaussian volume terms fit original actual radial sections. Only true dorsal/side skin moves radially with protected angular/axial feathers. Original UV remains exact; anatomy-local axial/angular source-anchor skin interpolation cleans measured cross-digit spill, open target preserved through inverse new-LBS; all new UV/weights source-parent barycentric. Fitted anatomical surface derivative normals blend with authored source open normals by exact edit field, then four-pose feasible constraints follow actual new geometry; per-corner split only when needed. No PN-edge subdivision or cylinder fitting.'}
 (HERE/'joint_delta.json').write_text(json.dumps(delta,indent=2)+'\n');print(json.dumps({'sha256':delta['candidate_sha256'],'triangles':total,'vertices':len(p),'originals_moved':len(moved),'original_weights_changed':len(weights_changed),'original_normals_changed':len(norms),'normal_splits':len(splits),'new_corners':len(added),'max_shift_mm':delta['source_positions_max_shift_mm']}))
if __name__=='__main__':main()
