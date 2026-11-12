"""Actual flat, independently cut pattern panels; no prior garment coordinates."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; BASE=HERE.parent;ROOT=HERE.parents[5]
sys.path.insert(0,str(ROOT/'ArtSource/refinement/character/design/cuff-structure/motion-stage3'))
import audit_motion as a
P=[];L=[];Q=[];PID=[];PANELS=[];IDS={};SEAMS=[]
def patch(name,u,v,place):
 uv=np.stack(np.broadcast_arrays(u,v),axis=-1); n,m=uv.shape[:2]; start=len(P)
 ids=np.arange(start,start+n*m).reshape(n,m);local=uv.reshape(-1,2)
 offset=np.array([len(PANELS)%4*.65,len(PANELS)//4*.65])
 P.extend(np.column_stack((local+offset,np.zeros(len(local)))))
 L.extend(place(local)); q=[]
 for i in range(n-1):
  for j in range(m-1):q.append([ids[i,j],ids[i,j+1],ids[i+1,j+1],ids[i+1,j]])
 Q.extend(q);PID.extend([len(PANELS)+1]*len(q));IDS[name]=ids
 PANELS.append(dict(name=name,id=len(PANELS)+1,vertex_start=start,vertex_count=n*m,grid=[n,m],pattern_uv_m=local.tolist(),layout_flat_offset_m=offset.tolist(),source_material_domain='PLANAR',placement='RIGID_ROTATION_TRANSLATION_ONLY',boundary_ids={}))
 return ids

def seam(name,aa,bb):
 aa=np.asarray(aa).ravel();bb=np.asarray(bb).ravel();assert len(aa)==len(bb),(name,len(aa),len(bb))
 pp=np.asarray(P);la=np.linalg.norm(np.diff(pp[aa],axis=0),axis=1);lb=np.linalg.norm(np.diff(pp[bb],axis=0),axis=1)
 assert np.max(abs(la-lb))<1e-6,(name,la.sum(),lb.sum())
 SEAMS.append(dict(id=name,edge_a=aa.tolist(),edge_b=bb.tolist(),pair_order='EXPLICIT_CORRESPONDING_SAMPLES',samples=len(aa),length_a_m=float(la.sum()),length_b_m=float(lb.sum()),max_segment_mismatch_m=float(np.max(abs(la-lb))),intent='EQUAL_LENGTH_SEW_NO_GATHER'))

# All material dimensions metres. Full sleeve root 320mm and wrist 200mm.
length=.42;rootw=.32;cuffw=.20;ns=42;nv=32
gus=np.hypot(length/ns,(rootw-cuffw)/2/ns)*6
zb=1.02;zt=1.46;za=zt-.16-gus
z=np.r_[np.linspace(zb,za,23),np.linspace(za,za+gus,7)[1:],np.linspace(za+gus,zt,17)[1:]]
iz_side=22;iz_gus=28
# Back top has a shallow real neck cut, while both shoulder segments are 155mm.
xx=np.r_[np.linspace(-.21,-.055,17),np.linspace(-.055,.055,13)[1:],np.linspace(.055,.21,17)[1:]]
u=xx[None,:];vv=z[:,None]+np.zeros((len(z),len(xx)))
dip=np.where(abs(xx)<.055,.015*(1-abs(xx)/.055),0)
vv=vv-dip[None,:]*np.clip((vv-1.42)/.04,0,1)
back=patch('back',u+np.zeros_like(vv),vv,lambda uv:np.c_[uv[:,0],np.full(len(uv),.115),uv[:,1]])
for side,name,dep in [(1,'front_L_outer',-.125),(-1,'front_R_inner',-.105)]:
 edge=np.interp(z,[zb,1.20,zt],[-.17 if side==1 else .11,-.065 if side==1 else .045,.055*side])
 t=np.linspace(0,1,17)[None,:];x=edge[:,None]*(1-t)+(.21*side)*t
 ids=patch(name,x,z[:,None]+np.zeros_like(x),lambda uv,dep=dep:np.c_[uv[:,0],np.full(len(uv),dep),uv[:,1]])
 seam(side>0 and 'shoulder_L' or 'shoulder_R',ids[-1],back[-1,28:] if side>0 else back[-1,:17][::-1])
 seam(side>0 and 'side_L' or 'side_R',ids[:iz_side+1,-1],back[:iz_side+1,-1 if side>0 else 0])

for side,label in [(1,'L'),(-1,'R')]:
 s=np.linspace(0,length,ns+1)[:,None];width=rootw+(cuffw-rootw)*s/length
 vf=np.linspace(-.5,0,17)[None,:]*width;vb=np.linspace(0,.5,17)[None,:]*width
 fs=patch('sleeve_front_'+label,s+np.zeros_like(vf),vf,lambda uv,side=side:np.c_[side*(.23+uv[:,0]),np.full(len(uv),-.085),1.46+uv[:,1]])
 bs=patch('sleeve_back_'+label,s+np.zeros_like(vb),vb,lambda uv,side=side:np.c_[side*(.23+uv[:,0]),np.full(len(uv),.115),1.46-uv[:,1]])
 front=IDS['front_L_outer' if side>0 else 'front_R_inner']
 seam('armhole_front_'+label,front[iz_gus:,-1],fs[0])
 seam('armhole_back_'+label,back[iz_gus:,-1 if side>0 else 0],bs[0,::-1])
 seam('sleeve_upper_'+label,fs[:,-1],bs[:,0])
 seam('sleeve_under_'+label,fs[6:,0],bs[6:,-1])
 gu=np.linspace(0,gus,7)[None,:];gv=np.linspace(0,gus,7)[:,None]
 gi=patch('gusset_'+label,gu+np.zeros_like(gv),gv+np.zeros_like(gu),lambda uv,side=side:np.c_[np.full(len(uv),side*.24),uv[:,0]-.5*gus+.025,uv[:,1]+za])
 seam('gusset_body_front_'+label,front[iz_side:iz_gus+1,-1],gi[:,0])
 seam('gusset_body_back_'+label,back[iz_side:iz_gus+1,-1 if side>0 else 0],gi[0,:])
 seam('gusset_sleeve_front_'+label,fs[:7,0],gi[-1,:])
 seam('gusset_sleeve_back_'+label,bs[:7,-1],gi[:,-1])
# Independent flat inner neckline facing, display 12mm; no thick rim geometry.
# Back collar cut length = back neck edge. V edge is retained separate trim.
cu=np.linspace(-.055,.055,13)[None,:];cv=np.linspace(0,.012,3)[:,None]
collar=patch('narrow_inner_collar',cu+np.zeros_like(cv),cv+np.zeros_like(cu),lambda uv:np.c_[uv[:,0],np.full(len(uv),.105),1.46+uv[:,1]])
# Collar intentionally construction-only in this first physical cut: no fake equal-length sew.
pp=np.asarray(P);ll=np.asarray(L);qq=np.asarray(Q,np.int32);pid=np.asarray(PID,np.int16)
edges=np.unique(np.sort(np.concatenate([qq[:,[0,1]],qq[:,[1,2]],qq[:,[2,3]],qq[:,[3,0]]]),axis=1),axis=0)
sew=np.unique(np.sort(np.concatenate([np.c_[s['edge_a'],s['edge_b']] for s in SEAMS]),axis=1),axis=0)
restlen=np.linalg.norm(pp[edges[:,0]]-pp[edges[:,1]],axis=1)
layoutlen=np.linalg.norm(ll[edges[:,0]]-ll[edges[:,1]],axis=1)
print('EDGE_MIN',restlen.min(), 'id', edges[restlen.argmin()], flush=True)
assert restlen.min()>=.0059
assert np.max(abs(restlen-layoutlen))<1e-10
# Actual current 78-rest is read only, used solely for proxy and pin-target motion.
path=ROOT/'ArtSource/tripo-warrior/library/base_prepared_png.glb';doc,bin=a.load_glb(path);skin=doc['skins'][0];sam=a.Sampler(doc,bin,'idle');guard=sam.sample(0)[skin['joints']];sam.tracks={};rest=sam.sample(0)[skin['joints']]
C=np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]])
rest=np.einsum('ij,njk->nik',C,rest);guard=np.einsum('ij,njk->nik',C,guard)
names=[doc['nodes'][i]['name'] for i in skin['joints']];bn={n:i for i,n in enumerate(names)}
# Pose targets are explicitly separate from flat material rest.
tt=ll.copy();target=ll.copy();pin=np.zeros(len(ll),np.float32)
for panel in PANELS:
 name=panel['name'];ii=np.arange(panel['vertex_start'],panel['vertex_start']+panel['vertex_count']);coords=ll[ii]
 if name.startswith('sleeve'):
  side=name[-1];uv=np.asarray(panel['pattern_uv_m']);w=np.clip((uv[:,0]-.16)/.16,0,1); mats=[]
  for bone in [side+'_Upperarm',side+'_Forearm']:
   bi=bn[bone];m=guard[bi]@np.linalg.inv(rest[bi]);mats.append(coords@m[:3,:3].T+m[:3,3])
  target[ii]=mats[0]*(1-w[:,None])+mats[1]*w[:,None]
  ids=IDS[name];cuff_top=ids[-1,-1] if 'front' in name else ids[-1,0];pin[cuff_top]=1
  # Only three top-of-cuff targets; underseam endpoints remain free.
  hi=bn[side+'_Hand']; T=np.eye(4);T[:3,3]=rest[hi,:3,3]-np.array([(1 if side=='L' else -1)*.012,0,-.04])
  delta=T[:3,3]-ll[cuff_top];tt[ii]=ll[ii]+delta*np.clip(uv[:,0]/length,0,1)[:,None]
  hmat=guard[hi]@np.linalg.inv(rest[hi]);target[ii]=tt[ii]@hmat[:3,:3].T+hmat[:3,3]
 else:
  bi=bn['Spine02'];m=guard[bi]@np.linalg.inv(rest[bi]);target[ii]=coords@m[:3,:3].T+m[:3,3]
for name in ['front_L_outer','front_R_inner']:
 ids=IDS[name];pin[ids[0,:3]]=1
pin[back[-1,18:27:4]]=1;pin[back[0,18:27:4]]=1
# Three paired shoulder sewing fixtures per side stop a flat back panel
# falling behind the mannequin before the seam closes. This moves pin targets,
# never pattern REST. 12 extra supports, under half a percent total pinned.
mi=guard[bn['Spine02']]@np.linalg.inv(rest[bn['Spine02']])
for label,side in [('L',1),('R',-1)]:
 fi=IDS['front_L_outer' if side>0 else 'front_R_inner'][-1,[0,8,16]]
 bi=back[-1,[28,36,44]] if side>0 else back[-1,[16,8,0]]
 for ff,bb in zip(fi,bi):
  x=ll[ff,0];zfix=1.465-.045*(abs(x)-.055)/.155
  for idx,off in [(ff,-.0007),(bb,.0007)]:
   tt[idx]=[x,.04+off,zfix];target[idx]=tt[idx]@mi[:3,:3].T+mi[:3,3];pin[idx]=1
# Collar constructed outside cloth; excluded from sim so it cannot free-fall.
active=pid!=len(PANELS)
np.savez_compressed(HERE/'pattern_v2.npz',flat_rest_positions=pp.astype(np.float32),layout_positions=ll.astype(np.float32),t_target_positions=tt.astype(np.float32),guard_target_positions=target.astype(np.float32),quad_faces=qq,quad_part_ids=pid,sewing_edges=sew.astype(np.int32),pin_weights=pin,guard_bone_world=guard,rest_bone_world=rest,bone_names=np.array(names))
report=dict(status='TRUE_FLAT_PATTERN_SOURCE_FIRST_CUT_NOT_FINAL_BINDING',pattern_version=2,units='metres',coordinates='Blender +X wearer left, -Y front, +Z up',panels=PANELS,seams=SEAMS,material=dict(single_layer=True,display_thickness_m=.0012,cloth_rest='flat_rest_positions / Rest_Flat shape key',shape_key_dynamic_mesh=False),mesh=dict(vertices=len(pp),quads=len(qq),physical_panels=9,construction_only_panels=['narrow_inner_collar'],minimum_structural_edge_m=float(restlen.min()),max_rigid_layout_edge_error_m=float(abs(restlen-layoutlen).max()),loose_sewing_edges=len(sew)),pose=dict(source=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),joints=78,guard='idle@0',rest_modified=False,pin_targets_are_not_material_rest=True),construction_limits=['Narrow collar remains separately constructed trim in this first cut; no fraudulent unequal seam pairing.','Human collision consists only of labelled torso/capsule approximations; no original hand-protection domain collider.','No final binding, production replacement, device or dynamic coverage claim.'])
(HERE/'pattern_v2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
colors=['#729db2','#c8a56c','#d08478','#88b57c','#8f8cbd','#ba9480','#a2b6a4','#879db2','#a5af74','#999999']
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="-260 -60 2900 2200"><rect x="-260" y="-60" width="2900" height="2200" fill="#faf9f5"/><text x="0" y="0" font-family="sans-serif" font-size="26">UB-01 v2 — true flat pattern / metres / 9 cloth pieces + inner facing</text>']
for panel,color in zip(PANELS,colors):
 start=panel['vertex_start'];n,m=panel['grid'];ids=np.arange(start,start+n*m).reshape(n,m);boundary=np.r_[ids[0,:],ids[1:,-1],ids[-1,-2::-1],ids[-2:0:-1,0]];pts=pp[boundary,:2]*1000;pts[:,1]=1450-pts[:,1]
 svg.append('<polygon points="'+ ' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="{color}" fill-opacity=".3" stroke="{color}" stroke-width="3"/>')
 center=pts.mean(0);svg.append(f'<text x="{center[0]:.1f}" y="{center[1]:.1f}" font-family="sans-serif" font-size="22">{panel["name"]}</text>')
for k,s in enumerate(SEAMS):
 for side in ['edge_a','edge_b']:
  pts=pp[s[side],:2]*1000;pts[:,1]=1450-pts[:,1];c=pts[len(pts)//2]
  svg.append('<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="none" stroke="#333" stroke-width="2"/><text x="{c[0]:.1f}" y="{c[1]:.1f}" font-family="sans-serif" font-size="13">S{k+1:02d}</text>')
svg.append('</svg>');(HERE/'pattern_v2.svg').write_text('\n'.join(svg));print(json.dumps(report['mesh']),flush=True)
