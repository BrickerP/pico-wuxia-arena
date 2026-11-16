"""Compose c2ae lantern surface module into private PNG/KTX full-scene candidates only."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;SURFACE=HERE.parent;ROOT=HERE.parents[7]
FORMAL=ROOT/'app/src/main/assets/models/courtyard_hero.glb';FORMAL_SHA='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667';PNG=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';PNG_SHA='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392';MODULE=SURFACE/'lantern_surface_module.glb';MODULE_SHA='c2ae86e490ef4fb56a6111ff1bbc6ee693262c1e44ab2a4e890d472062d89c4a';FIBER=SURFACE/'textures/paper_fiber_1024x512.png'
sys.path[:0]=[str(ROOT/'ArtSource/refinement/environment-hero'),str(ROOT/'ArtSource/refinement/environment-hero/stage2'),str(ROOT/'ArtSource/refinement/environment-hero/single-window-integration-2026-11-12'),str(ROOT/'ArtSource/refinement/pbr-compression')]
from verify_environment import read
from create_candidate import encode
from build_courtyard import Output
import compress_pbr as ktx
ENCODER=ROOT/'ArtSource/refinement/pbr-compression/tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx'
def sha(v):return hashlib.sha256(v.read_bytes() if isinstance(v,Path) else v).hexdigest()
def triangles(d,b,p):
 from verify_environment import rows
 return rows(d,b,p['indices']).reshape(-1,3)
def rows(d,b,a):
 from verify_environment import rows as r
 return r(d,b,a)
def view(d,b,i):
 q=d['bufferViews'][i];o=q.get('byteOffset',0);return bytes(b[o:o+q['byteLength']])
def old_remove(d,b,out):
 report={};total=0
 for mi,pi,name in [(6,0,'wood'),(6,1,'bronze'),(7,0,'paper')]:
  source=d['meshes'][mi]['primitives'][pi];pos=rows(d,b,source['attributes']['POSITION']);ix=triangles(d,b,source);mask=np.zeros(len(ix),bool)
  for x in [-2.15,2.15]:
   q=pos[ix];mask|=np.all(abs(q[:,:,0]-x)<.29,1)&np.all((q[:,:,1]>2.06)&(q[:,:,1]<3.46),1)&np.all((q[:,:,2]>-5.05)&(q[:,:,2]<-4.51),1)
  out.doc['meshes'][mi]['primitives'][pi]['indices']=out.accessor(ix[~mask].reshape(-1,1),'SCALAR',True);report[name]=int(mask.sum());total+=int(mask.sum())
 return report,total
class ModuleCopy:
 def __init__(self,out,d,b):self.o=out;self.d=d;self.b=b;self.views={};self.acc={};self.mesh={}
 def v(self,i):
  if i not in self.views:
   src=self.d['bufferViews'][i];self.views[i]=self.o.view(view(self.d,self.b,i),src.get('target'))
   if 'byteStride' in src:self.o.doc['bufferViews'][-1]['byteStride']=src['byteStride']
  return self.views[i]
 def a(self,i):
  if i not in self.acc:
   q=copy.deepcopy(self.d['accessors'][i]);q['bufferView']=self.v(q['bufferView']);self.o.doc['accessors'].append(q);self.acc[i]=len(self.o.doc['accessors'])-1
  return self.acc[i]
 def m(self,i):
  if i not in self.mesh:
   q=copy.deepcopy(self.d['meshes'][i]);
   for p in q['primitives']:
    p['attributes']={k:self.a(v) for k,v in p['attributes'].items()};p['indices']=self.a(p['indices']);name=self.d['materials'][p['material']]['name'];p['material']=10 if 'surface finish preview' in name else {'EH Timber | aged grain':0,'EH Fittings | aged bronze':7,'Rope | twisted hemp':24}[name]
   self.o.doc['meshes'].append(q);self.mesh[i]=len(self.o.doc['meshes'])-1
  return self.mesh[i]
 def n(self,i):
  src=self.d['nodes'][i];q={k:copy.deepcopy(v) for k,v in src.items() if k!='children'}
  if 'mesh'in q:q['mesh']=self.m(q['mesh'])
  self.o.doc['nodes'].append(q);idx=len(self.o.doc['nodes'])-1
  if 'children'in src:q['children']=[self.n(c) for c in src['children']]
  return idx
def replace_image_payloads(d,b,replacements):
 packed=bytearray()
 for i,v in enumerate(d['bufferViews']):
  packed.extend(b'\0'*(-len(packed)%4));data=replacements.get(i,view(d,b,i));v['byteOffset']=len(packed);v['byteLength']=len(data);packed.extend(data)
 return bytes(packed)
def compose(source,source_sha,mode,ktx_payload=None):
 if sha(source)!=source_sha or sha(MODULE)!=MODULE_SHA or sha(FIBER)!=json.loads((SURFACE/'fiber_provenance.json').read_text())['output']['sha256']:raise ValueError('pinned input changed')
 d,b=read(source);md,mb=read(MODULE);out=Output(copy.deepcopy(d),b);removed,total=old_remove(d,b,out);copy_module=ModuleCopy(out,md,mb);root=out.doc['scenes'][out.doc.get('scene',0)]['nodes'][0];module_root=md['scenes'][md.get('scene',0)]['nodes'][0];children=md['nodes'][module_root].get('children',[])
 for name,t in [('front_left',[-2.15,2.70,-4.78]),('front_right',[2.15,2.70,-4.78])]:
  copied=[copy_module.n(c) for c in children];out.doc['nodes'].append({'name':'LanternSurface_'+name,'translation':t,'children':copied});out.doc['nodes'][root].setdefault('children',[]).append(len(out.doc['nodes'])-1)
 # One existing texture/image slot serves both base and emission; MR/normal stay formal.
 m=out.doc['materials'][10];m['pbrMetallicRoughness']['baseColorTexture']['index']=41;m['emissiveTexture']['index']=41
 if mode=='png':replacement=(FIBER.read_bytes());out.doc['images'][41]['mimeType']='image/png'
 else:
  replacement=ktx_payload;out.doc['images'][41]['mimeType']='image/ktx2'
  texture=out.doc['textures'][41]
  if 'source' in texture:texture['extensions']={'KHR_texture_basisu':{'source':texture.pop('source')}}
 newbin=replace_image_payloads(out.doc,out.blob,{out.doc['images'][41]['bufferView']:replacement})
 return out.doc,newbin,{'removed':removed,'removed_total':total,'copied_meshes':copy_module.mesh,'mode':mode}
def main():
 if sha(FORMAL)!=FORMAL_SHA or sha(PNG)!=PNG_SHA:raise ValueError('formal/PNG source changed')
 cache=HERE/'ktx-cache';cache.mkdir(exist_ok=True);identity=ktx.encoder_identity(ENCODER);contract={'roles':['baseColor','emissive'],'domain':'srgb','wrap_s':'wrap','wrap_t':'wrap'};payload,record=ktx.encode_image(FIBER.read_bytes(),contract,ENCODER,identity,cache)
 results={}
 for label,source,source_sha,encoded in [('png',PNG,PNG_SHA,None),('ktx',FORMAL,FORMAL_SHA,payload)]:
  d,b,report=compose(source,source_sha,label,encoded);path=HERE/f'courtyard_lantern_surface_{label}.glb';path.write_bytes(encode(d,b));results[label]={'path':path.name,'sha256':sha(path),'bytes':path.stat().st_size,'report':report}
 manifest={'status':'private_full_composition_for_root_review','formal_input_sha256':FORMAL_SHA,'png_preview_input_sha256':PNG_SHA,'module_sha256':MODULE_SHA,'fiber_sha256':sha(FIBER),'ktx_record':record,'outputs':results,'material10_update':{'baseColorTexture_index':41,'emissiveTexture_index':41,'replaced_image_index':41,'unchanged_mr_index':39,'unchanged_normal_index':40},'instances':[[-2.15,2.70,-4.78],[2.15,2.70,-4.78]],'removed':results['ktx']['report']['removed']}
 (HERE/'composition_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
