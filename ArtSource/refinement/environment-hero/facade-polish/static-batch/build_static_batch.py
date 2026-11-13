"""Native GLB derivative: world-batch nine windows, then repack all live data.

Material/image/texture/sampler tables remain semantically and bytewise frozen.
Lower missing tangents and upper explicit tangents are separate layout groups.
All source nodes remain; old window nodes become transform/reference empties.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;FACADE=HERE.parent;BASE=FACADE.parent;ROOT=BASE.parents[2]
SOURCE=FACADE/'courtyard_facade_polish.glb'
EXPECTED='64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605'
sys.path.insert(0,str(BASE));from verify_environment import read,rows,active_nodes
sys.path.insert(0,str(BASE/'stage2'));from create_candidate import encode
sys.path.insert(0,str(FACADE));from build_facade import budget
WINDOW_NODES=tuple(range(41,50))
DTYPE={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def layout(doc,primitive):
    return tuple((k,doc['accessors'][i]['componentType'],doc['accessors'][i]['type'],doc['accessors'][i].get('normalized',False))
                 for k,i in sorted(primitive['attributes'].items()))
def image_bytes(doc,blob,index):
    image=doc['images'][index];view=doc['bufferViews'][image['bufferView']];a=view.get('byteOffset',0)
    return bytes(blob[a:a+view['byteLength']])

class Pack:
    def __init__(self):self.blob=bytearray();self.views=[];self.accessors=[]
    def view(self,data,target=None):
        self.blob.extend(b'\0'*((-len(self.blob))%4));offset=len(self.blob);self.blob.extend(data)
        v={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
        if target:v['target']=target
        self.views.append(v);return len(self.views)-1
    def accessor(self,array,blueprint,indices=False):
        a=copy.deepcopy(blueprint)
        for key in ['bufferView','byteOffset','count','min','max','sparse']:a.pop(key,None)
        array=np.asarray(array,dtype=DTYPE[a['componentType']]);a['count']=len(array)
        a['bufferView']=self.view(array.tobytes(),34963 if indices else 34962)
        if blueprint['type']=='VEC3' and not indices and ('min' in blueprint or blueprint.get('_position')):
            a['min']=array.min(axis=0).tolist();a['max']=array.max(axis=0).tolist()
        elif 'min' in blueprint:
            a['min']=array.min(axis=0).tolist();a['max']=array.max(axis=0).tolist()
        a.pop('_position',None);self.accessors.append(a);return len(self.accessors)-1
    def index(self,values,vertex_count):
        values=np.asarray(values).reshape(-1,1);kind=5123 if vertex_count<=65535 else 5125
        return self.accessor(values,{'componentType':kind,'type':'SCALAR'},True)

def make_window_groups(doc,blob,frames):
    groups={}
    for ni in WINDOW_NODES:
        node=doc['nodes'][ni];frame=frames[ni]
        assert node['mesh'] in [32,33]
        np.testing.assert_array_equal(frame[:3,:3],np.eye(3))
        for pi,p in enumerate(doc['meshes'][node['mesh']]['primitives']):
            key=(p['material'],layout(doc,p));g=groups.setdefault(key,{'arrays':{k:[] for k in p['attributes']},
              'blueprints':{k:doc['accessors'][i] for k,i in p['attributes'].items()},'indices':[],
              'vertex_count':0,'triangle_count':0,'members':[]})
            indices=rows(doc,blob,p['indices']).reshape(-1,3);used=np.unique(indices);mapped=np.searchsorted(used,indices)
            count=len(used)
            for attr,ai in p['attributes'].items():
                values=rows(doc,blob,ai)[used]
                if attr=='POSITION':
                    # Source windows are translation-only. Baking to float32 is
                    # the sole numerical change, checked in world coordinates.
                    values=(np.column_stack((values,np.ones(len(values))))@frame.T)[:,:3].astype('<f4')
                g['arrays'][attr].append(values)
            g['indices'].append(mapped+g['vertex_count'])
            g['members'].append({'node':ni,'primitive':pi,'first_triangle':g['triangle_count'],'triangles':len(indices)})
            g['vertex_count']+=count;g['triangle_count']+=len(indices)
    assert len(groups)==7
    return groups

def compact_scene(doc,blob,groups):
    result=copy.deepcopy(doc);pack=Pack();frames=active_nodes(doc)
    assert not doc.get('skins') and not doc.get('animations')
    for i in WINDOW_NODES:result['nodes'][i].pop('mesh')
    keep_meshes=sorted({node['mesh'] for i,node in enumerate(result['nodes']) if i in frames and 'mesh' in node})
    assert 32 not in keep_meshes and 33 not in keep_meshes
    # All fifty images are explicit contract roots, including four legacy
    # unreferenced slots. Their payloads are copied, never decoded/reencoded.
    result['images']=copy.deepcopy(doc['images'])
    image_view_map={}
    for i,image in enumerate(result['images']):
        old_view=image['bufferView']
        if old_view not in image_view_map:image_view_map[old_view]=pack.view(image_bytes(doc,blob,i))
        image['bufferView']=image_view_map[old_view]
    # Compact unions of actually indexed vertices per original attribute set;
    # this preserves sharing across unaffected material primitives.
    streams={}
    for mi in keep_meshes:
        for p in doc['meshes'][mi]['primitives']:
            signature=tuple(sorted(p['attributes'].items()))
            streams.setdefault(signature,[]).append(rows(doc,blob,p['indices']).reshape(-1))
    stream_outputs={}
    for signature,index_arrays in streams.items():
        used=np.unique(np.concatenate(index_arrays));attrs={}
        for semantic,ai in signature:
            blueprint=copy.deepcopy(doc['accessors'][ai]);blueprint['_position']=semantic=='POSITION'
            attrs[semantic]=pack.accessor(rows(doc,blob,ai)[used],blueprint)
        stream_outputs[signature]=(used,attrs)
    mesh_map={};meshes=[]
    for mi in keep_meshes:
        mesh=copy.deepcopy(doc['meshes'][mi])
        for primitive in mesh['primitives']:
            signature=tuple(sorted(primitive['attributes'].items()));used,attrs=stream_outputs[signature]
            old_indices=rows(doc,blob,primitive['indices']).reshape(-1)
            primitive['attributes']=attrs.copy();primitive['indices']=pack.index(np.searchsorted(used,old_indices),len(used))
        mesh_map[mi]=len(meshes);meshes.append(mesh)
    for node in result['nodes']:
        if 'mesh' in node:node['mesh']=mesh_map[node['mesh']]
    batch_primitives=[];batch_report=[]
    for (material,schema),g in sorted(groups.items()):
        attrs={}
        for semantic,arrays in g['arrays'].items():
            blueprint=copy.deepcopy(g['blueprints'][semantic]);blueprint['_position']=semantic=='POSITION'
            attrs[semantic]=pack.accessor(np.concatenate(arrays),blueprint)
        index=pack.index(np.concatenate(g['indices']),g['vertex_count'])
        batch_primitives.append({'attributes':attrs,'indices':index,'material':material,'mode':4})
        batch_report.append({'material':material,'material_name':doc['materials'][material]['name'],
          'layout':schema,'vertices':g['vertex_count'],'triangles':g['triangle_count'],
          'index_component_type':pack.accessors[index]['componentType'],'members':g['members']})
    batch_mesh=len(meshes);meshes.append({'name':'Facade_StaticWindows_ByMaterialAndLayout','primitives':batch_primitives})
    root=doc['scenes'][doc.get('scene',0)]['nodes'][0];np.testing.assert_array_equal(frames[root],np.eye(4))
    batch_node=len(result['nodes']);result['nodes'].append({'name':'Facade_StaticWindows','mesh':batch_mesh})
    result['nodes'][root]['children'].append(batch_node)
    result['meshes']=meshes;result['accessors']=pack.accessors;result['bufferViews']=pack.views;result['buffers']=[{'byteLength':len(pack.blob)}]
    return result,pack.blob,{'source_mesh_map':mesh_map,'new_batch_mesh':batch_mesh,'new_batch_node':batch_node,
      'groups':batch_report,'preserved_empty_window_nodes':list(WINDOW_NODES),
      'removed_source_meshes':[32,33],'all_image_slots_retained':True}

def main():
    if sha(SOURCE)!=EXPECTED:raise ValueError('Frozen64da source identity differs')
    doc,blob=read(SOURCE);groups=make_window_groups(doc,blob,active_nodes(doc));candidate,data,mapping=compact_scene(doc,blob,groups)
    output=HERE/'courtyard_static_batch.glb';output.write_bytes(encode(candidate,data))
    before,after=budget(doc,blob),budget(candidate,data)
    assert before['node_expanded_triangles']==after['node_expanded_triangles']
    assert after['primitive_node_submission_upper_estimate']==80
    assert candidate['materials']==doc['materials'] and candidate['textures']==doc['textures'] and candidate['samplers']==doc['samplers']
    info={'status':'candidate_built_for_equivalence_and_budget_review','candidate':output.name,'sha256':sha(output),
      'source':str(SOURCE.relative_to(ROOT)),'source_sha256':EXPECTED,'producer_sha256':sha(Path(__file__)),
      'source_budget':before,'candidate_budget':after,'source_bytes':SOURCE.stat().st_size,'candidate_bytes':output.stat().st_size,
      'batch_mapping':mapping,'group_policy':'same material and original attribute schema; do not add missing T or delete explicit T',
      'geometry_policy':'bake source node world translation; preserve normals/UV/explicit tangents and primitive winding',
      'numeric_policy':'world POSITION rounded once to float32; max world error must stay <=1e-6m; all other attribute bytes identical',
      'resource_policy':'full active geometry/accessor/view repack, not prefix append; all32 materials/all50 raw image payloads frozen',
      'risk':'unique VB grows from instance expansion; lower submission estimate is not measured draw count or LMK improvement',
      'entry':'same single courtyard at Stage origin identity; Root owns app publishing/build/device/Git'}
    (HERE/'candidate_manifest.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps({'sha256':info['sha256'],'bytes':[info['source_bytes'],info['candidate_bytes']],
      'source_budget':before,'candidate_budget':after,'groups':[(x['material'],x['vertices'],x['index_component_type']) for x in mapping['groups']]},indent=2))
if __name__=='__main__':main()
