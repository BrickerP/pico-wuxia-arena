"""Actual skeleton/topology and 8 transverse sections for frozen finger candidate."""
import importlib.util,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('finger_builder',HERE/'build_finger.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
def unit(x):return x/max(np.linalg.norm(x),1e-20)
def geometry(path):
 d,bb=b.b.h.read(path);p=d['meshes'][0]['primitives'][0];return b.b.h.skin(d,bb,p,b.b.h.sampled_worlds(d,bb,'grip',0.)),b.b.h.values(d,bb,p['indices']).reshape(-1,3).astype(int)
def sections(points,faces,center,axis,radial,dorsal):
 out=[]
 for tri in points[faces]:
  signed=(tri-center)@axis
  if signed.min()>0 or signed.max()<0:continue
  intersections=[]
  for i,j in [(0,1),(1,2),(2,0)]:
   if signed[i]*signed[j]<0:
    q=tri[i]+(tri[j]-tri[i])*signed[i]/(signed[i]-signed[j]);diff=q-center
    if np.linalg.norm(diff)<.017:intersections.append([float(diff@radial),float(diff@dorsal)])
  if len(intersections)==2:out.append(intersections)
 return out

def main():
 delta=json.loads((HERE/'finger_delta.json').read_text());p,f=geometry(b.SOURCE);q,g=geometry(HERE/'right_hand_finger.glb')
 axes=np.asarray(delta['anatomy']['axes']);D=-axes[2]
 image=Image.new('RGB',(1600,1130),(25,30,37));draw=ImageDraw.Draw(image)
 draw.text((24,15),'Actual open-pose skeleton and transverse finger sections | blue: source / orange: candidate',fill='white')
 evidence={}
 for di,row in enumerate(delta['anatomy']['bones']):
  chain=np.asarray([row['MCP'],row['PIP'],row['DIP'],row['inferred_tip']]);evidence[row['digit']]={}
  for ji in [1,2]:
   axis=unit(chain[ji+1]-chain[ji-1]);dorsal=unit(D-axis*(D@axis));radial=unit(np.cross(axis,dorsal));center=chain[ji]
   old=sections(p,f,center,axis,radial,dorsal);new=sections(q,g,center,axis,radial,dorsal)
   left=di*400+20;top=(ji-1)*450+70;cx=left+180;cy=top+220;scale=10000
   draw.rectangle((left,top,left+360,top+400),outline=(75,84,95));draw.text((left+12,top+12),row['digit']+' '+('PIP' if ji==1 else 'DIP')+' | 10px/mm',fill='white')
   draw.line((cx-150,cy,cx+150,cy),fill=(58,67,77));draw.line((cx,cy-160,cx,cy+160),fill=(58,67,77));draw.text((cx+6,cy-155),'dorsal',fill=(200,210,220))
   for rows,col in [(old,(67,162,242)),(new,(255,176,66))]:
    for seg in rows:draw.line([(cx+x*scale,cy-y*scale) for x,y in seg],fill=col,width=2)
   evidence[row['digit']][('PIP' if ji==1 else 'DIP')]={'center_m':center.tolist(),'normal_axis':axis.tolist(),'source_intersection_segments':old,'candidate_intersection_segments':new,'section_dorsal_unit':dorsal.tolist(),'section_radial_unit':radial.tolist()}
 draw.text((24,1010),'Each plane is centered on the actual MCP/PIP/DIP chain; thumb, palm, cuff and every original control are immutable.',fill=(210,215,220))
 draw.text((24,1040),'Section shape follows the source joint relief. No radial cylinder fitting, surface-wide smoothing, or material edits.',fill=(210,215,220))
 draw.text((24,1070),'Geometry overlays are diagnostics; the 0.3m matched original/neutral renders determine visible benefit.',fill=(210,215,220))
 image.save(HERE/'anatomical_sections.png')
 # Dorsal coordinate projection of the actual mesh, limited to the finger domain.
 origin=np.asarray(delta['anatomy']['hand_origin']);local=(p-origin)@axes.T;lq=(q-origin)@axes.T
 im=Image.new('RGB',(1500,1200),(25,30,37));dr=ImageDraw.Draw(im);scale=9000
 def point(v):return (750+scale*v[0],1150-scale*(v[1]-.085))
 for face in f:
  if local[face,1].min()<.09:continue
  dr.line([point(local[i]) for i in [*face,face[0]]],fill=(65,73,84),width=1)
 for row in delta['candidate_added_vertices']:
  v=lq[row['candidate_vertex_id']];xy=point(v);dr.ellipse((xy[0]-2,xy[1]-2,xy[0]+2,xy[1]+2),fill=(255,176,66))
 for row in delta['anatomy']['bones']:
  chain=np.asarray([row['MCP'],row['PIP'],row['DIP'],row['inferred_tip']]);loc=(chain-origin)@axes.T
  dr.line([point(v) for v in loc],fill=(73,190,245),width=3)
  for v,label in zip(loc,['MCP','PIP','DIP','tip*']):
   xy=point(v);dr.ellipse((xy[0]-5,xy[1]-5,xy[0]+5,xy[1]+5),fill=(73,190,245));dr.text((xy[0]+7,xy[1]-10),row['digit']+' '+label,fill='white')
 dr.text((20,15),'Actual open-pose anatomical ROI | gray source topology | orange curved added points | blue actual bone chain',fill='white')
 dr.text((20,40),'*20mm inferred distal endpoint delimits support only; it is not an authored bone.',fill=(210,215,220));im.save(HERE/'anatomical_roi.png')
 report={'source_sha256':delta['source_sha256'],'candidate_sha256':delta['candidate_sha256'],'sections':evidence,'source_positions_UV_and_skin_unchanged':True,'only_original_normal_changed_vertex_ids':delta.get('original_normal_changed_vertex_ids',[]),'images':['anatomical_sections.png','anatomical_roi.png']}
 (HERE/'section_diagnostics.json').write_text(json.dumps(report,indent=2)+'\n');print('ANATOMY_DIAGNOSTICS',len(evidence)*2,'sections')
if __name__=='__main__':main()
