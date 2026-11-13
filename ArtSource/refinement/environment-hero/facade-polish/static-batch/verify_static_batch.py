"""World-space, attribute-contract and full resource-GC equivalence checks."""
from pathlib import Path
import copy
import hashlib
import json
import sys

import numpy as np

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent.parent
sys.path.insert(0,str(BASE));from verify_environment import read,rows,active_nodes
sys.path.insert(0,str(HERE));from build_static_batch import layout,image_bytes,WINDOW_NODES
sys.path.insert(0,str(BASE/'facade-polish'));from build_facade import budget
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def corner_data(doc,blob,frame,p):
    ix=rows(doc,blob,p['indices']).reshape(-1,3);attrs={k:rows(doc,blob,a)[ix] for k,a in p['attributes'].items()}
    x=attrs['POSITION'].astype(float);attrs['POSITION']=(np.concatenate((x,np.ones((*x.shape[:2],1))),axis=2)@frame.T)[:,:,:3]
    return attrs
def main():
    m=json.loads((HERE/'candidate_manifest.json').read_text());source=HERE.parent/'courtyard_facade_polish.glb';target=HERE/m['candidate']
    assert sha(source)==m['source_sha256'] and sha(target)==m['sha256']
    old,ob=read(source);new,nb=read(target);of,nf=active_nodes(old),active_nodes(new)
    assert new['materials']==old['materials'] and new['textures']==old['textures'] and new['samplers']==old['samplers']
    assert len(new['materials'])==32 and len(new['images'])==50
    image_proof=[]
    for i,(a,b) in enumerate(zip(old['images'],new['images'])):
        a=copy.deepcopy(a);b=copy.deepcopy(b);a.pop('bufferView');b.pop('bufferView');assert a==b
        raw=image_bytes(old,ob,i);assert raw==image_bytes(new,nb,i)
        image_proof.append({'index':i,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    assert new['scenes']==old['scenes'] and len(new['nodes'])==len(old['nodes'])+1
    root=old['scenes'][old.get('scene',0)]['nodes'][0]
    max_error=0.;attributes_checked=0;triangles_checked=0
    expected_windows={}
    for ni,node in enumerate(old['nodes']):
        candidate=copy.deepcopy(new['nodes'][ni]);original=copy.deepcopy(node)
        np.testing.assert_array_equal(nf[ni],of[ni])
        if ni==root:assert candidate.pop('children')[:-1]==original.pop('children')
        if ni in WINDOW_NODES:
            assert 'mesh' not in candidate;original.pop('mesh');assert candidate==original
            for p in old['meshes'][node['mesh']]['primitives']:
                key=(p['material'],layout(old,p));expected_windows.setdefault(key,[]).append(corner_data(old,ob,of[ni],p))
        else:
            if 'mesh' in original:
                oldmesh=old['meshes'][original.pop('mesh')];newmesh=new['meshes'][candidate.pop('mesh')]
                assert len(oldmesh['primitives'])==len(newmesh['primitives'])
                for a,b in zip(oldmesh['primitives'],newmesh['primitives']):
                    assert a['material']==b['material'] and layout(old,a)==layout(new,b)
                    x,y=corner_data(old,ob,of[ni],a),corner_data(new,nb,nf[ni],b)
                    assert x.keys()==y.keys();assert x['POSITION'].shape==y['POSITION'].shape
                    for key in x:
                        if key=='POSITION':
                            delta=float(np.abs(x[key]-y[key]).max());assert delta<=1e-6;max_error=max(max_error,delta)
                        else:np.testing.assert_array_equal(x[key].view('u1'),y[key].view('u1'));attributes_checked+=x[key].size
                    triangles_checked+=len(x['POSITION'])
            assert candidate==original,node['name']
    batch_node=next(i for i,n in enumerate(new['nodes']) if n['name']=='Facade_StaticWindows')
    batch_mesh=new['meshes'][new['nodes'][batch_node]['mesh']];assert len(batch_mesh['primitives'])==7
    actual_keys=set()
    for p in batch_mesh['primitives']:
        key=(p['material'],layout(new,p));actual_keys.add(key)
        source_groups=expected_windows[key];expected={k:np.concatenate([g[k] for g in source_groups]) for k in source_groups[0]}
        actual=corner_data(new,nb,nf[batch_node],p)
        assert expected.keys()==actual.keys()
        delta=float(np.abs(expected['POSITION']-actual['POSITION']).max());assert delta<=1e-6;max_error=max(max_error,delta)
        for semantic in expected:
            if semantic!='POSITION':
                np.testing.assert_array_equal(expected[semantic].view('u1'),actual[semantic].view('u1'));attributes_checked+=expected[semantic].size
        triangles_checked+=len(expected['POSITION'])
    assert actual_keys==set(expected_windows) and len(actual_keys)==7
    # No replaced or unreferenced geometry resource is retained in the document.
    used_meshes={new['nodes'][i]['mesh'] for i in nf if 'mesh' in new['nodes'][i]};assert used_meshes==set(range(len(new['meshes'])))
    used_accessors=set()
    for mesh in new['meshes']:
        for p in mesh['primitives']:used_accessors.add(p['indices']);used_accessors.update(p['attributes'].values())
    assert used_accessors==set(range(len(new['accessors'])))
    used_views={a['bufferView'] for a in new['accessors']}|{i['bufferView'] for i in new['images']}
    assert used_views==set(range(len(new['bufferViews'])))
    spans=sorted((v.get('byteOffset',0),v.get('byteOffset',0)+v['byteLength']) for v in new['bufferViews'])
    cursor=0
    for a,b in spans:assert 0<=a-cursor<=3;cursor=b
    assert cursor==new['buffers'][0]['byteLength'] and len(new['buffers'])==1
    assert budget(old,ob)==m['source_budget'] and budget(new,nb)==m['candidate_budget']
    assert triangles_checked==m['source_budget']['node_expanded_triangles']==235746
    # All unchanged mesh vertices remain in their original local coordinates;
    # windows differ only by their required world-space float32 bake.
    report={'status':'passed world-space/attribute/image/resource equivalence checks','source_sha256':m['source_sha256'],'candidate_sha256':m['sha256'],
      'triangles_compared_including_winding_and_order':triangles_checked,'max_world_position_error_m':max_error,
      'nonposition_corner_values_compared_bit_exact':attributes_checked,'normal_uv_existing_tangent_bits_preserved':True,
      'missing_tangent_contract_preserved':True,'all50_image_payloads_bit_exact':image_proof,
      'no_unused_mesh_accessor_or_view':True,'old_bin_not_appended':True,
      'intentional_retained_legacy_image_slots':[0,1,2,15],
      'image_contract_note':'all50 slots explicitly retained as required, including legacy images; this is not a texture-preload reduction claim',
      'budget':{'source':m['source_budget'],'candidate':m['candidate_budget'],'source_bytes':m['source_bytes'],'candidate_bytes':m['candidate_bytes']},
      'lmk_conclusion':'none; no native memory/frame-time measurement performed'}
    (HERE/'review/equivalence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['all50_image_payloads_bit_exact']},indent=2))
if __name__=='__main__':main()
