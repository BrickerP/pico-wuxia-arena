"""Three-way a980/48e/joint-loop review from untouched camera-matched frames."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
OUT=HERE/('initial/renders' if '--initial' in sys.argv else 'renders')
def main():
 report=json.loads((OUT/'render_manifest.json').read_text());assert report['status']=='six_matched_actual_joint_renders_complete'
 old=json.loads((HERE.parent/'renders/render_manifest.json').read_text());result=[]
 for pose in ['open','mid','closed']:
  panel=Image.new('RGB',(3600,1900),(25,30,37));draw=ImageDraw.Draw(panel)
  for ri,material in enumerate(['original','neutral']):
   paths=[HERE.parent/f'renders/{pose}_{material}_before_0.3m.png',HERE.parent/f'renders/{pose}_{material}_after_0.3m.png',OUT/f'{pose}_{material}_joint_0.3m.png']
   labels=['a980 source','48e technical baseline',report['candidate_sha256'][:8]+' joint loops']
   for ci,(p,label) in enumerate(zip(paths,labels)):
    im=Image.open(p).convert('RGB');assert im.size==(1200,900);panel.paste(im,(ci*1200,ri*950+50));draw.text((ci*1200+20,ri*950+20),pose+' / '+material+' / '+label+' / 0.3m',fill='white')
  path=OUT/f'{pose}_three_way.png';panel.save(path);result.append({'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 (OUT/'comparison_manifest.json').write_text(json.dumps({'candidate_sha256':report['candidate_sha256'],'panels':result,'frames_unretouched':True},indent=2)+'\n');print('THREE_WAY_PANELS',report['candidate_sha256'])
if __name__=='__main__':main()
