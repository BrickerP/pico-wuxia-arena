"""Intrinsic 2D pattern, equal seam and semantic corner graph proof."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
j=json.loads((HERE/'pattern_v2.json').read_text());d=np.load(HERE/'pattern_v2.npz');p=d['flat_rest_positions'].astype(float);l=d['layout_positions'].astype(float);q=d['quad_faces'];part=d['quad_part_ids']
parent={}
def find(x):
 x=int(x);parent.setdefault(x,x)
 if parent[x]!=x:parent[x]=find(parent[x])
 return parent[x]
def union(x,y):parent[find(x)]=find(y)
seams=[]
for s in j['seams']:
 a=np.array(s['edge_a']);b=np.array(s['edge_b']);la=np.linalg.norm(np.diff(p[a],axis=0),axis=1);lb=np.linalg.norm(np.diff(p[b],axis=0),axis=1)
 assert len(a)==len(b) and abs(la-lb).max()<1e-6
 for x,y in zip(a,b):union(x,y)
 seams.append(dict(id=s['id'],samples=len(a),length_a_m=float(la.sum()),length_b_m=float(lb.sum()),maximum_segment_mismatch_m=float(abs(la-lb).max())))
ii={x['name']:np.arange(x['vertex_start'],x['vertex_start']+x['vertex_count']).reshape(x['grid']) for x in j['panels']};corner=[]
for side,backcol in [('L',-1),('R',0)]:
 f=ii['front_L_outer' if side=='L' else 'front_R_inner'];b=ii['back'];sl=ii['sleeve_front_'+side];sb=ii['sleeve_back_'+side];g=ii['gusset_'+side]
 tests={'shoulder_cap':[f[-1,-1],b[-1,backcol],sl[0,-1],sb[0,0]],'gusset_bottom':[f[22,-1],b[22,backcol],g[0,0]],'gusset_front':[f[28,-1],sl[0,0],g[-1,0]],'gusset_back':[b[28,backcol],sb[0,-1],g[0,-1]],'gusset_sleeve_under':[sl[6,0],sb[6,-1],g[-1,-1]]}
 for name,ids in tests.items():
  assert len({find(i) for i in ids})==1
  corner.append(dict(side=side,name=name,vertex_ids=[int(x) for x in ids],seam_equivalence_pass=True))
e=np.unique(np.sort(np.concatenate([q[:,[0,1]],q[:,[1,2]],q[:,[2,3]],q[:,[3,0]]]),axis=1),axis=0);rp=np.linalg.norm(p[e[:,0]]-p[e[:,1]],axis=1);lp=np.linalg.norm(l[e[:,0]]-l[e[:,1]],axis=1)
assert rp.min()>.0059 and abs(rp-lp).max()<5e-7
planar=[]
for panel in j['panels']:
 ids=np.arange(panel['vertex_start'],panel['vertex_start']+panel['vertex_count']);sv=np.linalg.svd(l[ids]-l[ids].mean(0),compute_uv=False)
 assert sv[-1]<1e-5
 planar.append(dict(panel=panel['name'],flat_rest_z_range_m=float(np.ptp(p[ids,2])),layout_smallest_singular_value_m=float(sv[-1]),not_a_preformed_tube=True))
report=dict(status='PATTERN_INTRINSIC_AND_SEAM_GRAPH_PASS',pattern_npz_sha256=hashlib.sha256((HERE/'pattern_v2.npz').read_bytes()).hexdigest(),all_material_panels_flat=True,all_initial_3d_islands_flat=True,minimum_structural_edge_m=float(rp.min()),max_float32_rigid_layout_edge_error_m=float(abs(rp-lp).max()),pin_vertices=int((d['pin_weights']>0).sum()),pin_fraction=float((d['pin_weights']>0).mean()),seams=seams,semantic_corner_graph=corner,panels=planar,limits=['Topology proves equal pairings and coherent corners, not successful physical seam closure.','Tenth panel inner collar remains construction-only; nine physical panels in solver.','No source-human anatomical surface exists in this pattern file; hidden mannequin is approximate.'])
(HERE/'pattern_v2_audit.json').write_text(json.dumps(report,indent=2)+'\n')
# Readable 2D pattern chart, all panels share the same 700 px/metre scale.
im=Image.new('RGB',(1640,1560),'#faf9f5');dr=ImageDraw.Draw(im)
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,19);title=ImageFont.truetype(fontpath,32);small=ImageFont.truetype(fontpath,14)
dr.text((30,20),'UB-01 v2 | TRUE FLAT CUTTING PATTERN',font=title,fill='#222222');dr.text((30,63),'9 physical cloth pieces + 1 construction-only inner facing | 700 px/m | no source garment mesh used',font=font,fill='#555555')
colors=['#4f8198','#b5924e','#b9645d','#5e9358','#7774a0','#a2765c','#6d937c','#8f967c','#738aa4','#777777']
scale=700;positions={}
for idx,panel in enumerate(j['panels']):
 ids=ii[panel['name']];uv=np.asarray(panel['pattern_uv_m']);uv=(uv-uv.min(0))*scale;uv[:,1]=uv[:,1].max()-uv[:,1];off=np.array([30+(idx%4)*405,145+(idx//4)*470]);uv+=off;positions.update({int(i):tuple(xy) for i,xy in zip(ids.ravel(),uv)})
 boundary=np.r_[ids[0,:],ids[1:,-1],ids[-1,-2::-1],ids[-2:0:-1,0]];poly=[positions[int(i)] for i in boundary];dr.polygon(poly,fill=colors[idx]+'22' if False else '#e8e6dc',outline=colors[idx],width=3)
 dr.text(tuple(off-np.array([0,30])),f'{idx+1:02d} {panel["name"]}',font=font,fill=colors[idx])
 wh=np.ptp(np.asarray(panel['pattern_uv_m']),axis=0)*1000;dr.text((off[0],off[1]+max(uv[:,1]-off[1])+12),f'{wh[0]:.0f} x {wh[1]:.0f} mm',font=small,fill='#555555')
 for row in ids[::max(1,len(ids)//8)]:dr.line([positions[int(x)] for x in row],fill='#d1d0c7',width=1)
 for col in ids[:,::max(1,len(ids[0])//8)].T:dr.line([positions[int(x)] for x in col],fill='#d1d0c7',width=1)
for idx,s in enumerate(j['seams']):
 for side in ['edge_a','edge_b']:
  pts=[positions[int(i)] for i in s[side]];dr.line(pts,fill='#343434',width=2);mid=pts[len(pts)//2];dr.text((mid[0]+3,mid[1]+2),f'S{idx+1:02d}',font=small,fill='#111111')
dr.text((30,1504),'All 20 seam pairs have equal sampled lengths. 10 semantic corner checks pass. Minimum edge: 6 mm.',font=font,fill='#333333');dr.text((30,1535),'Flat source + rigid initial placement are separate from moving pin targets, mannequin and evaluated solver output.',font=small,fill='#666666')
im.save(HERE/'pattern_v2.png');print(json.dumps({k:v for k,v in report.items() if k not in ['seams','semantic_corner_graph','panels','limits']}))
