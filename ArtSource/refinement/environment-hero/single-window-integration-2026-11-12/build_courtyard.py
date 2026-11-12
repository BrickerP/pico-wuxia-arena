"""Replace exactly one window and its shared-wall infill in frozen 8b.

No Blender roundtrip of the courtyard: preserve the original binary prefix,
all unrelated primitives and every source node transform. Append only used
module resources; deduplicate images by decoded pixels, textures by sampler,
and equivalent materials after remapping their texture references.
"""
from pathlib import Path
from io import BytesIO
import copy
import hashlib
import json
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
SOURCE=BASE/'stage2/courtyard_materials_stage2.glb'
MODULE=BASE/'method-study-2026-11-12/window_infill_candidate.glb'
SOURCE_SHA='8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b'
MODULE_SHA='2fb34ef40f8dffe34c2f6d4f058bf673979df8e5ba27560f51c5c4e61752f6d5'
sys.path.insert(0,str(BASE));from verify_environment import read,rows,world_primitives,active_nodes
sys.path.insert(0,str(BASE/'stage2'));from create_candidate import components,encode

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(value):
    if isinstance(value,dict):return {k:canonical(v) for k,v in sorted(value.items()) if k not in ['name','extras']}
    if isinstance(value,list):return [canonical(v) for v in value]
    return round(value,5) if isinstance(value,float) else value
def material_key(value):
    m=copy.deepcopy(value);m.setdefault('alphaMode','OPAQUE');m.setdefault('doubleSided',False);m.setdefault('emissiveFactor',[0,0,0])
    p=m.setdefault('pbrMetallicRoughness',{});p.setdefault('baseColorFactor',[1,1,1,1]);p.setdefault('metallicFactor',1);p.setdefault('roughnessFactor',1)
    if 'normalTexture' in m:m['normalTexture'].setdefault('scale',1)
    for key in ['normalTexture','emissiveTexture']:
        if key in m:m[key].setdefault('texCoord',0)
    for key in ['baseColorTexture','metallicRoughnessTexture']:
        if key in p:p[key].setdefault('texCoord',0)
    return json.dumps(canonical(m),sort_keys=True)

class Output:
    def __init__(self,doc,blob):self.doc=doc;self.blob=bytearray(blob[:doc['buffers'][0]['byteLength']])
    def view(self,data,target=None):
        self.blob.extend(b'\0'*((-len(self.blob))%4));offset=len(self.blob);self.blob.extend(data)
        v={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
        if target:v['target']=target
        self.doc['bufferViews'].append(v);return len(self.doc['bufferViews'])-1
    def accessor(self,array,kind,indices=False):
        a=np.asarray(array,dtype='<u4' if indices else '<f4')
        v={'bufferView':self.view(a.tobytes(),34963 if indices else 34962),'componentType':5125 if indices else 5126,'count':len(a),'type':kind}
        if kind=='VEC3':v.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
        self.doc['accessors'].append(v);return len(self.doc['accessors'])-1

def remove_window(doc,blob,out,bounds):
    result=[];mesh=out.doc['meshes'][4]
    lo=np.array(bounds['min']);hi=np.array(bounds['max'])
    for pi,p in enumerate(mesh['primitives']):
        original=doc['meshes'][4]['primitives'][pi]
        pos=rows(doc,blob,original['attributes']['POSITION']);ix=rows(doc,blob,original['indices']).reshape(-1,3)
        chosen=set();count=0
        for group in components(pos,ix):
            a,b=pos[group].min(axis=0),pos[group].max(axis=0)
            if np.all(a>=lo-2e-5) and np.all(b<=hi+2e-5):chosen.update(group.tolist());count+=1
        keep=np.array([not any(int(i) in chosen for i in tri) for tri in ix])
        if count:
            p['indices']=out.accessor(ix[keep].reshape(-1,1),'SCALAR',True)
        result.append({'primitive':pi,'material':p['material'],'removed_parts':count,'removed_triangles':int((~keep).sum())})
    counts=[r['removed_parts'] for r in result]
    if counts[:3]!=[4,9,1] or any(counts[3:]):raise ValueError('Single-window selection does not match 14 frozen parts: '+str(counts))
    return result

def clip_wall(doc,blob,out,bounds):
    p=doc['meshes'][23]['primitives'][0];attrs={k:rows(doc,blob,a) for k,a in p['attributes'].items()}
    if set(attrs)-{'POSITION','NORMAL','TEXCOORD_0','TANGENT'}:raise ValueError('Unexpected static wall attribute')
    ix=rows(doc,blob,p['indices']).reshape(-1,3);lo=np.array(bounds['min']);hi=np.array(bounds['max']);eps=2e-6
    planes=[(axis,float(bound),sign) for axis in range(3) for bound,sign in [(lo[axis],1),(hi[axis],-1)]]
    result={k:[] for k in attrs};indices=[];touched=0
    def clip(poly,axis,bound,sign,positive):
        if not poly:return []
        output=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da=(a['POSITION'][axis]-bound)*sign;db=(b['POSITION'][axis]-bound)*sign
            ina=da>=-eps if positive else da< -eps;inb=db>=-eps if positive else db< -eps
            if ina:output.append(a)
            if ina!=inb:
                t=da/(da-db)
                output.append({k:a[k]+t*(b[k]-a[k]) for k in attrs})
        return output
    def emit(poly):
        if len(poly)<3:return
        for j in range(1,len(poly)-1):
            tri=[poly[0],poly[j],poly[j+1]]
            if np.linalg.norm(np.cross(tri[1]['POSITION']-tri[0]['POSITION'],tri[2]['POSITION']-tri[0]['POSITION']))<1e-11:continue
            start=len(result['POSITION']);indices.append([start,start+1,start+2])
            for v in tri:
                v={k:val.copy() for k,val in v.items()}
                n=v['NORMAL'];n/=np.linalg.norm(n)
                if 'TANGENT' in v:
                    t=v['TANGENT'][:3];t-=n*np.dot(n,t)
                    if np.linalg.norm(t)<1e-8:
                        t=np.eye(3)[int(np.argmin(np.abs(n)))];t-=n*np.dot(n,t)
                    v['TANGENT'][:3]=t/np.linalg.norm(t);v['TANGENT'][3]=1 if v['TANGENT'][3]>=0 else -1
                for k in attrs:result[k].append(v[k])
    for tri in ix:
        poly=[{k:values[i].astype(float) for k,values in attrs.items()} for i in tri]
        box=attrs['POSITION'][tri]
        if np.any(box.max(axis=0)<lo-eps) or np.any(box.min(axis=0)>hi+eps):emit(poly);continue
        touched+=1
        for axis,bound,sign in planes:
            emit(clip(poly,axis,bound,sign,False))
            poly=clip(poly,axis,bound,sign,True)
            if not poly:break
    target=out.doc['meshes'][23]['primitives'][0]
    for k,values in result.items():target['attributes'][k]=out.accessor(values,'VEC'+str(len(values[0])))
    target['indices']=out.accessor(np.array(indices).reshape(-1,1),'SCALAR',True)
    return {'source_triangles':len(ix),'result_triangles':len(indices),'intersecting_source_triangles':touched,
            'plane_tolerance_m':eps,'coplanar_policy':'boundary belongs to removed volume; do not emit coplanar interior front/back skins'}

class ModuleMerger:
    def __init__(self,out,module,blob):
        self.out=out;self.d=module;self.b=blob;self.maps={k:{} for k in ['view','accessor','image','sampler','texture','material','mesh','node']}
        self.image_keys={self.image_key(out.doc,out.blob,i):i for i in range(len(out.doc['images']))}
        self.material_keys={material_key(m):i for i,m in enumerate(out.doc['materials'])}
    def image_key(self,doc,blob,index):
        im=doc['images'][index];v=doc['bufferViews'][im['bufferView']];a=v.get('byteOffset',0)
        image=Image.open(BytesIO(bytes(blob[a:a+v['byteLength']]))).convert('RGBA')
        return (image.size,hashlib.sha256(image.tobytes()).hexdigest())
    def view(self,i):
        if i not in self.maps['view']:
            v=self.d['bufferViews'][i];a=v.get('byteOffset',0)
            self.maps['view'][i]=self.out.view(self.b[a:a+v['byteLength']],v.get('target'))
            if 'byteStride' in v:self.out.doc['bufferViews'][-1]['byteStride']=v['byteStride']
        return self.maps['view'][i]
    def accessor(self,i):
        if i not in self.maps['accessor']:
            a=copy.deepcopy(self.d['accessors'][i]);assert 'sparse' not in a;a['bufferView']=self.view(a['bufferView'])
            self.out.doc['accessors'].append(a);self.maps['accessor'][i]=len(self.out.doc['accessors'])-1
        return self.maps['accessor'][i]
    def image(self,i):
        if i not in self.maps['image']:
            key=self.image_key(self.d,self.b,i)
            if key in self.image_keys:index=self.image_keys[key]
            else:
                im=copy.deepcopy(self.d['images'][i]);im['bufferView']=self.view(im['bufferView']);self.out.doc['images'].append(im)
                index=len(self.out.doc['images'])-1;self.image_keys[key]=index
            self.maps['image'][i]=index
        return self.maps['image'][i]
    def sampler(self,i):
        if i not in self.maps['sampler']:
            value=self.d['samplers'][i];key=canonical(value)
            matches=[j for j,s in enumerate(self.out.doc['samplers']) if canonical(s)==key]
            if matches:index=matches[0]
            else:self.out.doc['samplers'].append(copy.deepcopy(value));index=len(self.out.doc['samplers'])-1
            self.maps['sampler'][i]=index
        return self.maps['sampler'][i]
    def texture(self,i):
        if i not in self.maps['texture']:
            t=copy.deepcopy(self.d['textures'][i]);t['source']=self.image(t['source'])
            if 'sampler' in t:t['sampler']=self.sampler(t['sampler'])
            matches=[j for j,x in enumerate(self.out.doc['textures']) if canonical(x)==canonical(t)]
            if matches:index=matches[0]
            else:self.out.doc['textures'].append(t);index=len(self.out.doc['textures'])-1
            self.maps['texture'][i]=index
        return self.maps['texture'][i]
    def material(self,i):
        if i not in self.maps['material']:
            m=copy.deepcopy(self.d['materials'][i])
            for key in ['normalTexture','occlusionTexture','emissiveTexture']:
                if key in m:m[key]['index']=self.texture(m[key]['index'])
            for key in ['baseColorTexture','metallicRoughnessTexture']:
                if key in m.get('pbrMetallicRoughness',{}):
                    t=m['pbrMetallicRoughness'][key];t['index']=self.texture(t['index'])
            key=material_key(m)
            if key in self.material_keys:index=self.material_keys[key]
            else:self.out.doc['materials'].append(m);index=len(self.out.doc['materials'])-1;self.material_keys[key]=index
            self.maps['material'][i]=index
        return self.maps['material'][i]
    def mesh(self,i):
        if i not in self.maps['mesh']:
            m=copy.deepcopy(self.d['meshes'][i]);m['name']='EH_OneWindow_Infill'
            for p in m['primitives']:
                p['attributes']={k:self.accessor(a) for k,a in p['attributes'].items()};p['indices']=self.accessor(p['indices']);p['material']=self.material(p['material'])
            self.out.doc['meshes'].append(m);self.maps['mesh'][i]=len(self.out.doc['meshes'])-1
        return self.maps['mesh'][i]
    def node(self,i):
        if i not in self.maps['node']:
            n=copy.deepcopy(self.d['nodes'][i]);n['name']='EH_OneWindow_'+n.get('name',str(i))
            if 'mesh' in n:n['mesh']=self.mesh(n['mesh'])
            if 'children' in n:n['children']=[self.node(c) for c in n['children']]
            self.out.doc['nodes'].append(n);self.maps['node'][i]=len(self.out.doc['nodes'])-1
        return self.maps['node'][i]

def main():
    if sha(SOURCE)!=SOURCE_SHA or sha(MODULE)!=MODULE_SHA:raise ValueError('Frozen source identity mismatch')
    original,blob=read(SOURCE);module,mb=read(MODULE);doc=copy.deepcopy(original);out=Output(doc,blob)
    frames=active_nodes(original)
    for i in [5,30]:np.testing.assert_allclose(frames[i],np.eye(4),atol=1e-8)
    recipe=json.loads((MODULE.parent/'replacement_recipe.json').read_text())
    removed=remove_window(original,blob,out,recipe['remove_window_parts']['bounds_stage_m'])
    wall=clip_wall(original,blob,out,recipe['replace_wall_volume']['bounds_stage_m'])
    merger=ModuleMerger(out,module,mb)
    children=[merger.node(i) for i in module['scenes'][module.get('scene',0)]['nodes']]
    doc['nodes'].append({'name':'EH_OneWindowReplacement_Root','translation':recipe['module_origin_stage_m'],'children':children})
    root=doc['scenes'][doc.get('scene',0)]['nodes'][0];doc['nodes'][root]['children'].append(len(doc['nodes'])-1)
    output=HERE/'courtyard_one_window.glb';output.write_bytes(encode(doc,out.blob))
    before=sum(len(i) for n,p,v,i in world_primitives(original,blob));after=sum(len(i) for n,p,v,i in world_primitives(doc,out.blob))
    info={'status':'full_candidate_for_root_native_intake','candidate':output.name,'sha256':sha(output),
      'source_sha256':SOURCE_SHA,'module_sha256':MODULE_SHA,'producer_sha256':sha(Path(__file__)),
      'placement_stage_m':[0,0,0],'rotation':'identity','scale':[1,1,1],
      'replacement':'one closed window at Stage X=-2.47 and its wall infill only',
      'window_removed':removed,'wall_clip':wall,'module_resource_maps':merger.maps,
      'budget':{'source_bytes':SOURCE.stat().st_size,'candidate_bytes':output.stat().st_size,'delta_bytes':output.stat().st_size-SOURCE.stat().st_size,
        'source_triangles':before,'candidate_triangles':after,'delta_triangles':after-before,
        'source_materials':len(original['materials']),'candidate_materials':len(doc['materials']),
        'source_images':len(original['images']),'candidate_images':len(doc['images']),
        'source_meshes':len(original['meshes']),'candidate_meshes':len(doc['meshes'])},
      'root_contract':'replace the single courtyard asset after explicit Root review; no additive runtime scene',
      'unchanged':['all original nodes/transforms except adding the replacement child','all primitives except mesh4 indices and mesh23/p0 clipped geometry',
        'source binary prefix','ground receivers','light anchors','other windows/posts/beams/props','combat volume','formal source/app files']}
    (HERE/'candidate_manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps({'sha256':info['sha256'],'budget':info['budget'],'material_reuse':merger.maps['material'],'image_reuse':merger.maps['image']},indent=2))

if __name__=='__main__':main()
