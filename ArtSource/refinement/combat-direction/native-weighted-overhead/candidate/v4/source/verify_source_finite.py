"""Apply final RAW in-memory to the frozen v3 base context for original63 checks.

No retarget, no generated second-target GLB and no producer/renderer writes.
"""
from pathlib import Path
import copy,json,struct,sys
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;LANE=OUT.parents[1]
sys.path.insert(0,str(LANE));import build_weighted_overhead as b
review=b.load_module('v4_source_finite_actual_mesh',LANE/'integration/review_candidate.py')
parent=b.PARENT
metadata=json.loads((parent/'weighted_overhead_authoring.json').read_text())
frozen=parent/'weighted_overhead_preview.glb'
expected=next(r['sha256'] for r in metadata['preview_outputs'] if r['file']==frozen.name)
assert b.digest(frozen)==expected=='dd0a0d4caa82f832350bac97dc5f2a6a6ec04308de7f5637a882efea9be07eaa'
doc,binary=b.library.read_glb(frozen);binary=bytearray(binary)
raw,rb=b.library.read_glb(OUT/'weighted_overhead_raw.glb');rt,keys=b.library.decode_animation(raw,rb)
oldraw,oldb=b.library.read_glb(b.SOURCE);oldtracks,_=b.library.decode_animation(oldraw,oldb)
base_tracks,base_keys=b.library.decode_animation(doc,binary)
rnames={n.get('name'):i for i,n in enumerate(raw['nodes'])};names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
assert base_keys==keys
before=bytes(binary);allowed=set();maximum_existing_base_source_rotation_delta=0.
for name in b.BONES:
    i=rnames[name];n=names[name];animation=doc['animations'][0]
    for a,c in zip(base_tracks[n,'rotation'][1],oldtracks[i,'rotation'][1]):
        maximum_existing_base_source_rotation_delta=max(maximum_existing_base_source_rotation_delta,min(max(abs(x-y) for x,y in zip(a,c)),max(abs(x+y) for x,y in zip(a,c))))
    channel=next(c for c in animation['channels'] if c['target']=={'node':n,'path':'rotation'})
    a=doc['accessors'][animation['samplers'][channel['sampler']]['output']];v=doc['bufferViews'][a['bufferView']]
    assert a['type']=='VEC4' and a['count']==211 and v.get('byteStride',16)==16
    start=v.get('byteOffset',0)+a.get('byteOffset',0)
    for k,row in enumerate(rt[i,'rotation'][1]):struct.pack_into('<4f',binary,start+k*16,*row)
    allowed.update(range(start,start+211*16))
assert maximum_existing_base_source_rotation_delta<1e-7
import numpy as np
changed=set(np.flatnonzero(np.frombuffer(before,dtype=np.uint8)!=np.frombuffer(binary,dtype=np.uint8)).tolist());assert changed<=allowed
alignment=json.loads((parent/'weighted_overhead_alignment.json').read_text())
body_primitives=alignment['body_primitive_indices']
surface=review.ActualTargetSurface((doc,binary),body_primitives)
times=[r['source_seconds'] for r in json.loads((parent/'weighted_overhead_verification.json').read_text())['frames']]
assert len(times)==63 and times[0]==0 and times[-1]==1.75
rows=[]
for t in times:
    row=surface.evaluate(t);rows.append(row)
    print('V4_SOURCE63',t,'steel',len(row['steel_fullbody_intersections']),'self',sum(row['nonadjacent_region_triangle_pairs'].values()),flush=True)
bad=[r for r in rows if r['steel_fullbody_intersections'] or any(r['nonadjacent_region_triangle_pairs'].values())]
result={'status':'original_source_base_context63_finite_checks_passed' if not bad else 'original_source_base_context63_finite_checks_failed','RAW':b.identity(OUT/'weighted_overhead_raw.glb'),'source_authoring':b.identity(OUT/'weighted_overhead_authoring.json'),'frozen_v3_base_context':b.identity(frozen),'frozen_v3_alignment':b.identity(parent/'weighted_overhead_alignment.json'),'source_times_from_original_v3_verification':b.identity(parent/'weighted_overhead_verification.json'),'method':'In memory only: original immutable v3 base prepared mesh/skin/normalization/actual mounted weapon; replace only named R_Upperarm/R_Forearm/R_Hand local rotation payloads from final RAW. Preserve all base target finger calibration and canonical root shift bytes. No retarget or emitted base model.','body_primitive_indices':body_primitives,'original_base_three_rotation_tracks_vs_v3_RAW_max_component_error':maximum_existing_base_source_rotation_delta,'modified_binary_bytes':len(changed),'static_JSON_and_other_binary_bytes_unchanged':True,'sample_count':63,'overlap_sample_count':len(bad),'actual_steel_fullbody_overlap_sample_count':sum(bool(r['steel_fullbody_intersections']) for r in rows),'nonadjacent_arm_hand_head_chest_overlap_sample_count':sum(any(r['nonadjacent_region_triangle_pairs'].values()) for r in rows),'frames':rows,'limits':['Original source/base context only; distinct from the actual veteran retarget check.','63 discrete poses are not continuous-time or all-cloth-volume proof.'],'source_pins':{str(p.relative_to(b.REPO)):b.digest(p) for p in [Path(__file__),Path(b.__file__),LANE/'integration/review_candidate.py']}}
(OUT/'weighted_overhead_source_finite_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('V4_SOURCE63_RESULT',result['status'],'bad',len(bad),flush=True)
if bad:raise SystemExit(2)
