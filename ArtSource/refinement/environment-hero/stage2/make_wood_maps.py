"""Read frozen stage1 scans and bake directional stage2 wood maps locally."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'textures'
OUT=HERE/'textures'
OUT.mkdir(exist_ok=True)
size=1024
v,u=np.mgrid[0:1:complex(size),0:1:complex(size)]
rng=np.random.default_rng(202611112)

def load(name):
    return np.asarray(Image.open(SOURCE/name).convert('RGB').resize((size,size),Image.Resampling.LANCZOS),dtype=float)/255
def save(name,values):
    Image.fromarray(np.uint8(np.clip(values,0,1)*255)).save(OUT/name)

# V is the long axis already authored on the frozen beam/column UVs.
broad=np.sin(2*np.pi*(u*9+.12*np.sin(v*2*np.pi)))
grain=np.sin(2*np.pi*(u*67+.15*np.sin(v*4*np.pi)))
fine=np.sin(2*np.pi*(u*139+.21*np.sin(v*2*np.pi)))
variation=1.18+.075*broad+.045*grain+.018*fine
color=load('wood_color.png')*variation[:,:,None]
color+=np.dstack((np.maximum(broad,0)*.025,np.maximum(broad,0)*.018,np.maximum(broad,0)*.011))
save('wood_basecolor.png',color)
save('wood_roughness.png',np.clip(.64-.045*broad-.035*grain+rng.normal(0,.008,(size,size)),.48,.79))
old=load('wood_normal.png')*2-1
# Height is 0.04mm/0.35m transverse tile; no giant grooves in the timber.
height=(grain*.000035+fine*.000009)
dy,dx=np.gradient(height,1.25/size,.35/size)
n=old.copy();n[:,:,0]-=dx;n[:,:,1]+=dy
n/=np.maximum(1e-8,np.linalg.norm(n,axis=2,keepdims=True))
save('wood_normal.png',n*.5+.5)

# Separate endgrain avoids painting every timber/window/lantern recess alike.
radius=np.sqrt(((u-.42)*1.1)**2+((v-.57)*.9)**2)
rings=np.sin(radius*115+.9*np.sin(u*14)+.7*np.sin(v*11))
end_color=np.dstack((.31+.028*rings,.205+.020*rings,.12+.013*rings))
split=(np.abs(np.sin(np.arctan2(v-.57,u-.42)*3+.2))<.025)&(radius>.25)
end_color[split]*=.55
save('endgrain_basecolor.png',end_color)
save('endgrain_roughness.png',.72-.04*rings)
dy,dx=np.gradient(rings*.00010,.11/size,.33/size)
n=np.dstack((-dx,dy,np.ones_like(dx)));n/=np.linalg.norm(n,axis=2,keepdims=True)
save('endgrain_normal.png',n*.5+.5)
files=['wood_basecolor.png','wood_normal.png','wood_roughness.png','endgrain_basecolor.png','endgrain_normal.png','endgrain_roughness.png']
(OUT/'wood_maps_manifest.json').write_text(json.dumps({
    'status':'complete','source':'Frozen stage1 wood maps derived from Poly Haven CC0 Fine Grained Wood',
    'source_color_sha256':hashlib.sha256((SOURCE/'wood_color.png').read_bytes()).hexdigest(),
    'wood_uv_m_per_tile':{'U':.35,'V':1.25},'endgrain_face_m':[.33,.11],
    'color_space':{'basecolor':'sRGB','normal':'linear OpenGL +Y','roughness':'linear'},
    'maps':{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in files}},indent=2)+'\n')
print('Wrote six stage2 wood maps')
