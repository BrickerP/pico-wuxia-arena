"""Assemble unchanged render frames into labeled source/candidate review panels."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
HERE=Path(__file__).resolve().parent;OUT=HERE/'renders'
def main():
 manifest=json.loads((OUT/'render_manifest.json').read_text());assert len(manifest['images'])==12 and manifest['status']=='twelve_matched_actual_renders_complete'
 report={'candidate_sha256':manifest['candidate_sha256'],'panels':[],'per_pose_raw_render_difference':{},'limits':'Pixel differences document changed images only, not visible-quality acceptance. Frames are not retouched, recolored or cropped.'}
 for pose in ['open','mid','closed']:
  panel=Image.new('RGB',(2400,1900),(25,30,37));draw=ImageDraw.Draw(panel)
  for ri,material in enumerate(['original','neutral']):
   for ci,stage in enumerate(['before','after']):
    p=OUT/f'{pose}_{material}_{stage}_0.3m.png';im=Image.open(p).convert('RGB');assert im.size==(1200,900)
    panel.paste(im,(1200*ci,50+950*ri));draw.text((1200*ci+20,950*ri+20),f'{pose} / {material} / '+('a980 source' if stage=='before' else '48e9 candidate')+' / distance0.3m',fill='white')
   before=np.asarray(Image.open(OUT/f'{pose}_{material}_before_0.3m.png').convert('RGB'),int);after=np.asarray(Image.open(OUT/f'{pose}_{material}_after_0.3m.png').convert('RGB'),int)
   diff=abs(after-before);report['per_pose_raw_render_difference'][pose+'_'+material]={'mean_abs_channel_8bit':float(diff.mean()),'pixels_any_channel_over8':int((diff.max(2)>8).sum()),'pixels_total':int(diff.shape[0]*diff.shape[1])}
  path=OUT/f'{pose}_comparison.png';panel.save(path);report['panels'].append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 (OUT/'comparison_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('THREE_REVIEW_PANELS')
if __name__=='__main__':main()
