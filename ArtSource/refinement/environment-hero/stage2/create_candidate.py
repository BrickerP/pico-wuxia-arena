"""Patch frozen GLB into an independent candidate; never run the stage1 producer.

Original geometry, ground, receivers, anchors and source buffer remain intact.
Paper gets per-sheet atlas UVs with recomputed tangents; structural joint caps
and inner door trim are a separate named mesh outside combat clearance.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import struct
import sys

import numpy as np
from PIL import Image

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[2]
SOURCE=BASE/'courtyard_hero.glb'
EXPECTED='56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8'
sys.path.insert(0,str(BASE))
from verify_environment import read,rows,active_nodes

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def assert_frozen(path=SOURCE):
    if sha(path)!=EXPECTED:raise ValueError('Frozen source identity changed')

def encode(doc,blob):
    doc['buffers'][0]['byteLength']=len(blob)
    js=json.dumps(doc,separators=(',',':'),ensure_ascii=True).encode()
    js+=b' '*((-len(js))%4)
    binary=bytes(blob)+b'\0'*((-len(blob))%4)
    total=12+8+len(js)+8+len(binary)
    return struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(binary),b'BIN\0')+binary

class Writer:
    def __init__(self,doc,blob):
        self.doc=doc;self.blob=bytearray(blob[:doc['buffers'][0]['byteLength']])
        self.texture_cache={}
        self.repeat=len(doc['samplers']);doc['samplers'].append({'magFilter':9729,'minFilter':9987,'wrapS':10497,'wrapT':10497})
        self.clamp=len(doc['samplers']);doc['samplers'].append({'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071})
    def view(self,data,target=None):
        self.blob.extend(b'\0'*((-len(self.blob))%4));offset=len(self.blob);self.blob.extend(data)
        view={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
        if target:view['target']=target
        self.doc['bufferViews'].append(view)
        return len(self.doc['bufferViews'])-1
    def accessor(self,array,kind,indices=False):
        array=np.asarray(array,dtype='<u4' if indices else '<f4')
        view=self.view(array.tobytes(),34963 if indices else 34962)
        a={'bufferView':view,'componentType':5125 if indices else 5126,'count':len(array),'type':kind}
        if kind=='VEC3':a.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
        self.doc['accessors'].append(a)
        return len(self.doc['accessors'])-1
    def texture(self,name,clamp=False):
        key=(name,clamp)
        if key in self.texture_cache:return self.texture_cache[key]
        path=HERE/'textures'/name
        image={'name':'S2 '+name,'mimeType':'image/png','bufferView':self.view(path.read_bytes())}
        self.doc['images'].append(image)
        self.doc['textures'].append({'name':'S2 '+name,'source':len(self.doc['images'])-1,'sampler':self.clamp if clamp else self.repeat})
        index=len(self.doc['textures'])-1;self.texture_cache[key]=index
        return index
    def mr(self,name):
        name=Path(name)
        target=name.with_name(name.stem+'_mr.png')
        rough=np.asarray(Image.open(HERE/'textures'/name).convert('L'))
        packed=np.stack((np.full_like(rough,255),rough,np.zeros_like(rough)),axis=2)
        Image.fromarray(packed).save(HERE/'textures'/target)
        return self.texture(str(target),clamp='atlas' in str(name))
    def bind(self,m,prefix,emission=None,clamp=False):
        m['pbrMetallicRoughness']={'baseColorTexture':{'index':self.texture(prefix+'_basecolor.png',clamp)},
          'baseColorFactor':[1,1,1,1],'metallicRoughnessTexture':{'index':self.mr(prefix+'_roughness.png')},
          'metallicFactor':0,'roughnessFactor':1}
        m['normalTexture']={'index':self.texture(prefix+'_normal.png',clamp),'scale':.6 if prefix=='paper_atlas' else .75}
        if emission:
            m['emissiveFactor']=emission
            m['emissiveTexture']={'index':self.texture(prefix+'_emissive.png',clamp)}

def components(vertices,indices):
    parent=list(range(len(vertices)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    positions={}
    for i,p in enumerate(vertices):
        key=tuple(np.rint(p*1000000).astype(int))
        if key in positions:union(i,positions[key])
        else:positions[key]=i
    for tri in indices:
        union(int(tri[0]),int(tri[1]));union(int(tri[1]),int(tri[2]))
    result={}
    for i in range(len(vertices)):result.setdefault(find(i),[]).append(i)
    return [np.array(group) for group in result.values()]

def tangents(vertices,normals,uv,indices,old):
    t=np.zeros_like(vertices);b=np.zeros_like(vertices)
    for tri in indices:
        pos=vertices[tri];tex=uv[tri]
        e1,e2=pos[1]-pos[0],pos[2]-pos[0];d1,d2=tex[1]-tex[0],tex[2]-tex[0]
        det=d1[0]*d2[1]-d1[1]*d2[0]
        if abs(det)<1e-12:continue
        tangent=(e1*d2[1]-e2*d1[1])/det;bitangent=(e2*d1[0]-e1*d2[0])/det
        for i in tri:t[i]+=tangent;b[i]+=bitangent
    result=old.copy()
    for i in range(len(vertices)):
        tangent=t[i]-normals[i]*np.dot(normals[i],t[i]);length=np.linalg.norm(tangent)
        if length<1e-8:
            normal=normals[i]/np.linalg.norm(normals[i])
            fallback=result[i,:3]-normal*np.dot(normal,result[i,:3])
            if np.linalg.norm(fallback)<1e-8:
                basis=np.eye(3)[int(np.argmin(np.abs(normal)))]
                fallback=basis-normal*np.dot(normal,basis)
            result[i,:3]=fallback/np.linalg.norm(fallback)
            result[i,3]=1 if result[i,3]>=0 else -1
            continue
        tangent/=length;result[i,:3]=tangent
        result[i,3]=-1 if np.dot(np.cross(normals[i],tangent),b[i])<0 else 1
    return result

def paper_uvs(writer,source_doc,source_blob):
    report=[]
    for mesh_index,mesh in enumerate(writer.doc['meshes']):
        for pi,p in enumerate(mesh['primitives']):
            if p.get('material')!=4:continue
            pos=rows(source_doc,source_blob,p['attributes']['POSITION'])
            normals=rows(source_doc,source_blob,p['attributes']['NORMAL'])
            indices=rows(source_doc,source_blob,p['indices']).reshape(-1,3)
            uv=np.zeros((len(pos),2),dtype=np.float32)
            groups=components(pos,indices)
            for number,group in enumerate(sorted(groups,key=lambda a:tuple(pos[a].mean(axis=0)))):
                points=pos[group];lo=points.min(axis=0);hi=points.max(axis=0)
                # Face width is X on front facades and -Z on the side gallery.
                front=(hi[0]-lo[0])>(hi[2]-lo[2]);haxis=0 if front else 2
                width=max(hi[haxis]-lo[haxis],1e-6);height=max(hi[1]-lo[1],1e-6)
                u=(points[:,haxis]-lo[haxis])/width
                if not front:u=1-u
                v=1-(points[:,1]-lo[1])/height
                tile=(number+mesh_index)%4;col,row=tile%2,tile//2
                # PNG and glTF UV both use the image's upper-left origin.
                uv[group,0]=(col*1024+8.5+u*1007)/2048
                uv[group,1]=(row*1024+8.5+v*1007)/2048
                report.append({'mesh':mesh_index,'primitive':pi,'sheet':number,'atlas_tile':tile,
                  'local_bounds_m':[lo.tolist(),hi.tolist()],'paper_width_height_m':[float(width),float(height)],
                  'uv_bounds':[[float(uv[group,0].min()),float(uv[group,1].min())],
                               [float(uv[group,0].max()),float(uv[group,1].max())]]})
            if 'TANGENT' in p['attributes']:
                old_tangent=rows(source_doc,source_blob,p['attributes']['TANGENT'])
            else:
                # Untextured stage1 paper has no tangent accessor. Supply a valid
                # perpendicular fallback for tiny bevel faces with degenerate UV.
                old_tangent=np.tile([1.,0.,0.,1.],(len(pos),1))
                old_tangent[np.abs(normals[:,0])>.95,:3]=[0,0,1]
            p['attributes']['TEXCOORD_0']=writer.accessor(uv,'VEC2')
            p['attributes']['TANGENT']=writer.accessor(tangents(pos,normals,uv,indices,old_tangent),'VEC4')
    return report

class JointGeometry:
    def __init__(self):self.points=[];self.normals=[];self.uv=[];self.faces=[[],[]];self.boxes=[]
    def face(self,points,center,material):
        points=np.array(points,dtype=float)
        normal=np.cross(points[1]-points[0],points[2]-points[0])
        if np.dot(normal,points.mean(axis=0)-center)<0:points=points[::-1];normal=-normal
        normal/=np.linalg.norm(normal)
        start=len(self.points);self.points.extend(points.tolist());self.normals.extend([normal.tolist()]*len(points))
        axis=int(np.argmax(np.abs(normal)));axes=[k for k in range(3) if k!=axis]
        if material==1:
            self.uv.extend([[(p[0]-center[0])/.33+.5,.5-(p[1]-center[1])/.11] for p in points])
        else:
            self.uv.extend([[(p[axes[0]]-center[axes[0]])/.35,(p[axes[1]]-center[axes[1]])/1.25] for p in points])
        for i in range(1,len(points)-1):self.faces[material].append([start,start+i,start+i+1])
    def box(self,name,center,size,bevel=.004,endgrain=False):
        c=np.array(center);h=np.array(size)/2;r=min(bevel,float(h.min())*.6)
        for axis in range(3):
            a,b=[k for k in range(3) if k!=axis]
            outline=[(-h[a]+r,-h[b]),(h[a]-r,-h[b]),(h[a],-h[b]+r),(h[a],h[b]-r),
                     (h[a]-r,h[b]),(-h[a]+r,h[b]),(-h[a],h[b]-r),(-h[a],-h[b]+r)]
            for sign in (-1,1):
                points=[]
                for u,v in outline:
                    p=c.copy();p[axis]+=sign*h[axis];p[a]+=u;p[b]+=v;points.append(p)
                self.face(points,c,int(endgrain and axis==2 and sign==1))
        for a,b in [(0,1),(0,2),(1,2)]:
            k=next(i for i in range(3) if i not in (a,b))
            for sa in (-1,1):
                for sb in (-1,1):
                    points=[]
                    for aa,bb,kk in [(h[a],h[b]-r,-h[k]+r),(h[a],h[b]-r,h[k]-r),
                                     (h[a]-r,h[b],h[k]-r),(h[a]-r,h[b],-h[k]+r)]:
                        p=c.copy();p[a]+=sa*aa;p[b]+=sb*bb;p[k]+=kk;points.append(p)
                    self.face(points,c,0)
        for sx in (-1,1):
            for sy in (-1,1):
                for sz in (-1,1):
                    points=[c+np.array([sx*h[0],sy*(h[1]-r),sz*(h[2]-r)]),
                            c+np.array([sx*(h[0]-r),sy*h[1],sz*(h[2]-r)]),
                            c+np.array([sx*(h[0]-r),sy*(h[1]-r),sz*h[2]])]
                    self.face(points,c,0)
        self.boxes.append({'name':name,'center_stage_m':center,'size_m':size})

def add_joints(w,end_material):
    g=JointGeometry()
    for x in (-5.65,-3.6,-1.4,1.4,3.6,5.65):
        for k in range(3):
            # End faces of the existing cantilever corbels, not arbitrary decoration.
            g.box(f'corbel_end_{x}_{k}',(x,2.98+k*.09,-4.855+k*.15),(.30+k*.04,.085,.022),.003,True)
        for dx in (-.09,.09):g.box(f'locking_key_{x}_{dx}',(x+dx,2.85,-5.085),(.022,.12,.028),.002)
    for side in (-1,1):
        x=side*1.29
        g.box(f'inner_jamb_{side}',(x,1.43,-5.17),(.055,2.70,.085),.006)
    g.box('inner_lintel',(0,2.80,-5.17),(2.63,.085,.085),.006)
    attributes={'POSITION':w.accessor(g.points,'VEC3'),'NORMAL':w.accessor(g.normals,'VEC3'),
                'TEXCOORD_0':w.accessor(g.uv,'VEC2')}
    points=np.array(g.points);normals=np.array(g.normals);uv=np.array(g.uv)
    fallback=np.tile([1.,0.,0.,1.],(len(points),1));fallback[np.abs(normals[:,0])>.95,:3]=[0,0,1]
    attributes['TANGENT']=w.accessor(tangents(points,normals,uv,np.array(g.faces[0]+g.faces[1]),fallback),'VEC4')
    primitives=[]
    for slot,material in [(0,0),(1,end_material)]:
        if g.faces[slot]:primitives.append({'attributes':attributes.copy(),'indices':w.accessor(np.array(g.faces[slot]).reshape(-1,1),'SCALAR',True),'material':material,'mode':4})
    w.doc['meshes'].append({'name':'EH_S2_TimberJointFaces_Mesh','primitives':primitives})
    w.doc['nodes'].append({'name':'EH_S2_TimberJointFaces','mesh':len(w.doc['meshes'])-1,
                          'extras':{'role':'existing corbel endgrain, locking keys and inner door trim'}})
    root=w.doc['scenes'][w.doc.get('scene',0)]['nodes'][0]
    w.doc['nodes'][root].setdefault('children',[]).append(len(w.doc['nodes'])-1)
    return g.boxes

def main():
    assert_frozen()
    (HERE/'textures'/'paper_maps_manifest.json').read_text()
    original,blob=read(SOURCE);doc=copy.deepcopy(original);w=Writer(doc,blob)
    for index,name in [(0,'EH Timber | aged grain'),(4,'EH Windows | warm paper'),(10,'EH Lantern | vermilion paper')]:
        if doc['materials'][index]['name']!=name:raise ValueError('Frozen material binding mismatch')
    w.bind(doc['materials'][0],'wood')
    w.bind(doc['materials'][4],'paper_atlas',[.42,.27,.10],True)
    # Keep reflected fill subdued so the causal interior warm patch remains
    # visible; a bright diffuse sheet would wash out the emission variation.
    doc['materials'][4]['pbrMetallicRoughness']['baseColorFactor']=[.38,.30,.21,1]
    doc['materials'][4]['name']='EH S2 Windows | layered paper emission'
    w.bind(doc['materials'][10],'lantern',[.75,.65,.50],True)
    doc['materials'][10]['name']='EH S2 Lantern | graded paper emission'
    paper_report=paper_uvs(w,original,blob)
    # Distant storeys keep a subdued value and do not compete with the opponent.
    far=copy.deepcopy(doc['materials'][4]);far['name']='EH S2 Windows | distant dim paper'
    far['emissiveFactor']=[.055,.040,.022];far['pbrMetallicRoughness']['baseColorFactor']=[.65,.65,.65,1]
    doc['materials'].append(far);far_index=len(doc['materials'])-1
    for p in doc['meshes'][1]['primitives']:
        if p.get('material')==4:p['material']=far_index
    joint=copy.deepcopy(doc['materials'][3]);joint['name']='EH S2 Timber | joint recess'
    joint['pbrMetallicRoughness']['baseColorFactor']=[.065,.045,.029,1]
    joint['pbrMetallicRoughness']['roughnessFactor']=.68
    doc['materials'].append(joint);joint_index=len(doc['materials'])-1
    for mesh_index in (14,22):
        for p in doc['meshes'][mesh_index]['primitives']:
            if p.get('material')==3:p['material']=joint_index
    end={'name':'EH S2 Timber | corbel endgrain','doubleSided':False}
    w.bind(end,'endgrain');doc['materials'].append(end)
    boxes=add_joints(w,len(doc['materials'])-1)
    # The old lantern had no normal map and therefore no exported tangent.
    # New normal-mapped primitives all get an explicit orthonormal basis.
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            if 'normalTexture' not in doc['materials'][p['material']] or 'TANGENT' in p['attributes']:continue
            pos=rows(doc,w.blob,p['attributes']['POSITION']);n=rows(doc,w.blob,p['attributes']['NORMAL'])
            uv=rows(doc,w.blob,p['attributes']['TEXCOORD_0']);indices=rows(doc,w.blob,p['indices']).reshape(-1,3)
            fallback=np.tile([1.,0.,0.,1.],(len(pos),1));fallback[np.abs(n[:,0])>.95,:3]=[0,0,1]
            p['attributes']['TANGENT']=w.accessor(tangents(pos,n,uv,indices,fallback),'VEC4')
    doc['asset']['extras']={'stage2_source_sha256':EXPECTED,
      'emission_contract':'art-directed emission maps; no physical transmission; native point lights are separate'}
    output=HERE/'courtyard_materials_stage2.glb';output.write_bytes(encode(doc,w.blob))
    manifest={'status':'complete','candidate':output.name,'sha256':sha(output),
      'source_commit_observed':'193d0f6dcc859168b8f7c00669c185a3863e1a8d',
      'root_stable_commit':'6b407acc4507812b99d1315e58c8a2c588719fd0',
      'source_glb':str(SOURCE.relative_to(ROOT)),'source_sha256':EXPECTED,
      'frozen_producer_sha256':sha(BASE/'build_environment.py'),'producer_sha256':sha(Path(__file__)),
      'load_position_stage_m':[0,0,0],'load_rotation':'identity','load_scale':[1,1,1],
      'ground_receivers':['EH_GroundReceiver','EH_MortarAndDrain'],
      'paper_sheets':paper_report,'added_joinery':boxes,
      'unchanged':['all original POSITION/NORMAL/index accessors','all original node transforms',
                   'ground geometry and PBR','walls and roofs','window lattice geometry',
                   'all named light anchors','stage1 source/producer/input maps and formal app asset'],
      'materials_changed':[0,4,10],'emission_model':'Core glTF emissiveTexture/factor only; no transmission extension',
      'paper_basecolor_factor':[.38,.30,.21,1],'paper_emissive_factor':[.42,.27,.10],
      'lantern_emissive_factor':[.75,.65,.50],
      'limitations':['No PICO installation/runtime proof','native lights remain owned by07/Root',
                     'emission and point light units are independent','headset brightness hierarchy requires native recheck']}
    (HERE/'candidate_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if sha(SOURCE)!=EXPECTED:raise AssertionError('Frozen source was altered')
    print('STAGE2_CANDIDATE_COMPLETE',manifest['sha256'],'paper sheets',len(paper_report),'joint boxes',len(boxes))

if __name__=='__main__':main()
