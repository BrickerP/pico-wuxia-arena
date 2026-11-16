"""Exact modified-control ledger and visible anatomical ring topology from GLBs."""
import importlib.util,json,hashlib
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('joint',HERE/'build_joint.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def read(path):
 d,b=g.h.read(path);pr=d['meshes'][0]['primitives'][0];a={k:g.h.values(d,b,v) for k,v in pr['attributes'].items()};f=g.h.values(d,b,pr['indices']).reshape(-1,3).astype(int);return d,b,pr,a,f

def main():
 delta=json.loads((HERE/'joint_delta.json').read_text());source,sb,sp,sa,sf=read(g.SOURCE);candidate,cb,cp,ca,cf=read(HERE/'right_hand_joint.glb');names=[source['nodes'][i]['name'] for i in source['skins'][0]['joints']];poses={}
 for label,time in [('default',None),('open',0.),('mid',.5),('closed',1.)]:
  world=g.h.sampled_worlds(source,sb,None if time is None else 'grip',time or 0.);poses[label]=(g.h.skin(source,sb,sp,world),g.h.skin(candidate,cb,cp,world))
 rows={}
 for idx in delta['modified_source_vertices']:
  angle=float(np.degrees(np.arccos(np.clip((sa['NORMAL'][idx]@ca['NORMAL'][idx])/(np.linalg.norm(sa['NORMAL'][idx])*np.linalg.norm(ca['NORMAL'][idx])),-1,1))))
  rows[str(idx)]={'source_vertex_id':idx,'raw_position_shift_mm':float(np.linalg.norm(ca['POSITION'][idx]-sa['POSITION'][idx])*1000),'source_position_m':sa['POSITION'][idx].tolist(),'candidate_position_m':ca['POSITION'][idx].tolist(),'normal_angle_degrees':angle,'source_normal':sa['NORMAL'][idx].tolist(),'candidate_normal':ca['NORMAL'][idx].tolist(),'source_skin':[[names[j],float(w)] for j,w in zip(sa['JOINTS_0'][idx],sa['WEIGHTS_0'][idx])],'candidate_skin':[[names[j],float(w)] for j,w in zip(ca['JOINTS_0'][idx],ca['WEIGHTS_0'][idx])],'actual_pose_position_delta_mm':{label:((q[idx]-p[idx])*1000).tolist() for label,(p,q) in poses.items()}}
 report={'source_sha256':delta['source_sha256'],'candidate_sha256':delta['candidate_sha256'],'originals_position_changed':len(delta['moved_source_vertices']),'originals_normal_changed':len(delta['original_normal_changed_vertex_ids']),'originals_skin_changed':len(delta['original_weight_changed_vertex_ids']),'all_original_UV_exact':bool(np.array_equal(sa['TEXCOORD_0'],ca['TEXCOORD_0'][:len(sa['POSITION'])])),'modified_originals':rows,'pose_original_position_max_delta_mm':{label:float(np.linalg.norm(q[:len(p)]-p,axis=1).max()*1000) for label,(p,q) in poses.items()}}
 (HERE/'original_change_ledger.json').write_text(json.dumps(report,indent=2)+'\n')
 image=Image.new('RGB',(1600,1300),(25,30,37));dr=ImageDraw.Draw(image);origin=np.asarray(delta['anatomy']['hand_origin']);axes=np.asarray(delta['anatomy']['axes']);opened=poses['open'][1];local=(opened-origin)@axes.T
 def point(v):return (800+v[0]*10500,1240-(v[1]-.088)*10500)
 roi=set(np.flatnonzero(np.isin(np.asarray(delta['candidate_face_to_source']),delta['ROI_faces'])).tolist())
 for fi,face in enumerate(cf):
  if local[face,1].min()<.092 or fi not in roi:continue
  dr.line([point(local[i]) for i in [*face,face[0]]],fill=(75,85,96),width=1)
 for cut in delta['joint_planes']:
  di=cut['digit'];fr=delta['anatomy']['bones'][di];st,th,r,c=g.coordinates(opened,fr);signed=(opened-np.asarray(cut['center']))@np.asarray(cut['normal']);mask=(abs(signed)<.000025)&(r<.017)
  color={'MCP':(247,202,80),'PIP':(247,145,65),'DIP':(235,104,136)}[cut['joint']]
  for face in cf:
   for x,y in [(face[0],face[1]),(face[1],face[2]),(face[2],face[0])]:
    if mask[x] and mask[y]:dr.line([point(local[x]),point(local[y])],fill=color,width=3)
 for fr in delta['anatomy']['bones']:
  chain=np.asarray([fr['MCP'],fr['PIP'],fr['DIP']]);ll=(chain-origin)@axes.T;dr.line([point(v) for v in ll],fill=(65,180,245),width=3)
  for v,label in zip(ll,['MCP','PIP','DIP']):
   xy=point(v);dr.ellipse((xy[0]-5,xy[1]-5,xy[0]+5,xy[1]+5),fill=(65,180,245));dr.text((xy[0]+7,xy[1]-12),fr['digit']+' '+label,fill='white')
 dr.text((20,15),'Actual open-pose joint-strip topology | gold MCP / orange PIP / red DIP / blue actual bones',fill='white');dr.text((20,40),'Anatomical plane clipping + constrained ear triangulation; no PN subdivision or free centroid fan.',fill=(210,215,220));image.save(HERE/'joint_loops_topology.png');print('EXACT_CHANGE_LEDGER_AND_TOPOLOGY')
if __name__=='__main__':main()
