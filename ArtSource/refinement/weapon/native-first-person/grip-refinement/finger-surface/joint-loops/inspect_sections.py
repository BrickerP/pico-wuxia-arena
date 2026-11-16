"""Actual-pose transverse PIP/DIP geometry, source/48e/joint; not rendered shading."""
import importlib.util,json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('joint',HERE/'build_joint.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
s=importlib.util.spec_from_file_location('sections',HERE.parent/'inspect_roi.py');helper=importlib.util.module_from_spec(s);s.loader.exec_module(helper)
def read(path,time):
 d,b=g.h.read(path);pr=d['meshes'][0]['primitives'][0];return d,b,g.h.skin(d,b,pr,g.h.sampled_worlds(d,b,'grip',time)),g.h.values(d,b,pr['indices']).reshape(-1,3).astype(int)
def main():
 delta=json.loads((HERE/'joint_delta.json').read_text());source,sb=g.h.read(g.SOURCE);names={n.get('name'):i for i,n in enumerate(source['nodes'])};openw=g.h.sampled_worlds(source,sb,'grip',0.);axes=np.asarray(delta['anatomy']['axes']);D=-axes[2];srcopen=read(g.SOURCE,0.)[2]
 all_owner=np.full(len(srcopen),-1,int);nearest=np.full(len(srcopen),1e6)
 for di,fr in enumerate(delta['anatomy']['bones']):
  st,th,r,c=g.coordinates(srcopen,fr);ss=fr['stations'];eligible=(st>=-.002)&(st<=ss[-1]+.003)&(r<.017)
  take=eligible&(r<nearest);all_owner[take]=di;nearest[take]=r[take]
 mappings=[np.arange(delta['source_face_count']),np.asarray(json.loads((HERE.parent/'finger_delta.json').read_text())['candidate_face_to_source']),np.asarray(delta['candidate_face_to_source'])]
 report={'candidate_sha256':delta['candidate_sha256'],'poses':{}}
 for pose,time in [('open',0.),('mid',.5),('closed',1.)]:
  datasets=[read(g.SOURCE,time),read(HERE.parent/'right_hand_finger.glb',time),read(HERE/'right_hand_joint.glb',time)];world=g.h.sampled_worlds(source,sb,'grip',time);srcfaces=datasets[0][3]
  image=Image.new('RGB',(1600,1060),(25,30,37));draw=ImageDraw.Draw(image);draw.text((20,15),pose+' actual PIP/DIP bone sections | blue a980 / gray48e / orange joint | 9px/mm',fill='white');rows={}
  for di,digit in enumerate(['Index','Mid','Ring','Pinky']):
   chain=np.asarray([world[names['R_'+digit+str(i)]][:3,3] for i in [1,2,3]]);tip=chain[2]+g.unit(chain[2]-chain[1])*.02;chain=np.vstack([chain,tip]);field=np.flatnonzero(np.isin(all_owner[srcfaces],di).any(1))
   for ji in [1,2]:
    center=chain[ji];axis=g.unit(chain[ji+1]-chain[ji-1]);relative=world[names['R_'+digit+str(ji+1)]][:3,:3]@np.linalg.inv(openw[names['R_'+digit+str(ji+1)]][:3,:3]);dorsal=g.unit(relative@D-axis*((relative@D)@axis));radial=g.unit(np.cross(axis,dorsal));left=di*400+20;top=(ji-1)*470+60;cx=left+180;cy=top+225
    draw.rectangle((left,top,left+360,top+420),outline=(70,80,92));draw.text((left+12,top+12),digit+' '+('PIP' if ji==1 else 'DIP'),fill='white');draw.line((cx-150,cy,cx+150,cy),fill=(50,60,70));draw.line((cx,cy-160,cx,cy+160),fill=(50,60,70))
    rec=[]
    for data,mapping,color,label in zip(datasets,mappings,[(65,160,245),(135,143,153),(255,176,65)],['a980','48e','joint']):
     points,faces=data[2],data[3];selected=faces[np.isin(mapping,field)];segments=helper.sections(points,selected,center,axis,radial,dorsal)
     for seg in segments:draw.line([(cx+v[0]*9000,cy-v[1]*9000) for v in seg],fill=color,width=2)
     rec.append({'asset':label,'segments':segments})
    rows[digit+'_'+str(ji)]={'center_m':center.tolist(),'axis':axis.tolist(),'section_dorsal':dorsal.tolist(),'curves':rec}
  draw.text((20,1020),'Planes share the actual source bones; reference triangles retain source-finger ownership. Skinning and geometric section changes are explicit.',fill=(210,215,220));image.save(HERE/(pose+'_joint_sections.png'));report['poses'][pose]=rows
 (HERE/'section_diagnostics.json').write_text(json.dumps(report,indent=2)+'\n');print('ACTUAL_JOINT_SECTIONS')
if __name__=='__main__':main()
