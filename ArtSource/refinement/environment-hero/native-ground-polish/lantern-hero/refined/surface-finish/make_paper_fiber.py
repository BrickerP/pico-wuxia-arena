"""Derive one neutral 1024x512 paper-fiber map from the existing lantern base map."""
from pathlib import Path
from io import BytesIO
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageFilter
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[6]
SOURCE=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';EXPECTED='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392'
sys.path.insert(0,str(ROOT/'ArtSource/refinement/environment-hero'));from verify_environment import read
def sha(v):return hashlib.sha256(v.read_bytes() if isinstance(v,Path) else v).hexdigest()
def image_bytes(d,b,i):
 v=d['bufferViews'][d['images'][i]['bufferView']];return bytes(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
def main():
 if sha(SOURCE)!=EXPECTED:raise ValueError('PNG-equivalent source changed')
 d,b=read(SOURCE);base=Image.open(BytesIO(image_bytes(d,b,38))).convert('RGB');base=base.resize((1024,512),Image.Resampling.LANCZOS);a=np.asarray(base,dtype=np.float32)/255.
 rng=np.random.default_rng(20261116);strands=rng.normal(0,1,1024);strands=np.asarray(Image.fromarray(np.uint8(np.clip((strands-strands.min())/(strands.max()-strands.min()),0,1)*255)).resize((1024,512),Image.Resampling.BICUBIC),dtype=np.float32)/255.;strands=(strands-.5)
 cloud=rng.normal(0,1,(32,64));cloud=np.asarray(Image.fromarray(np.uint8(np.clip((cloud-cloud.min())/(cloud.max()-cloud.min()),0,1)*255)).resize((1024,512),Image.Resampling.BICUBIC),dtype=np.float32)/255.-.5
 # Fibers follow V; the modulation is neutral and has no scene-space highlight direction.
 factor=1+.035*strands+.026*cloud;out=np.clip(a*factor[:,:,None],0,1);path=HERE/'textures/paper_fiber_1024x512.png';path.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(np.uint8(np.floor(out*255+.5)),'RGB').save(path,optimize=True)
 report={'status':'generated','source_png_equivalent_sha256':EXPECTED,'source_image_index':38,'source_image_sha256':sha(image_bytes(d,b,38)),'output':{'path':str(path.relative_to(HERE)),'sha256':sha(path),'size':[1024,512]},'algorithm':'seeded neutral vertical fiber plus low-frequency transmission variation; no fixed light, reflection, hue or AI generation','seed':20261116,'factor_min':float(factor.min()),'factor_max':float(factor.max()),'factor_mean':float(factor.mean()),'license':'derived procedural modification of existing project lantern paper base map; no external download'}
 (HERE/'fiber_provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
