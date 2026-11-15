"""Final v5 source: bounded left-elbow clearance patch of frozen v4 RAW.

Only three left-arm rotation streams are patched at two declared windows. The
veteran target is retargeted from native RAW once, calibrated once and grounded
once for private validation. No producer/library/app/integration writes.
"""
import copy,hashlib,importlib.util,json,math,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
FINE=REPO/'ArtSource/refinement/hand-poses/fine-overhead'
PRODUCER=REPO/'ArtSource/tripo-warrior'
OUT=HERE/'candidate/v5'
PARENT=HERE/'candidate/v4'
SOURCE=PARENT/'weighted_overhead_raw.glb'
SOURCE_SHA='050c55a2b64726f38ca7d36eec52f5832c370b92be3f80551f7c8249e5a3694f'
RIG=PRODUCER/'refined-base60k/rig.glb'
RIG_SHA='43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6'
TARGET_BEFORE=PARENT/'veteran_prepared_png.glb'
TARGET_BEFORE_SHA='cead1124ab1c3453f6fae2f98e0be275a39792be3de98e6888edaf83a4aabb86'
sys.path.insert(0,str(FINE))
import build_fine_overhead as base
library,author=base.library,base.author
from mathutils import Vector,Quaternion
import numpy as np
DURATION=1.75
RATE=120
BONES=('L_Upperarm','L_Forearm','L_Hand')
WINDOWS=((1.02,1.10,1.20),(1.38,44/30,1.56))
ELBOW_SWIVEL_DEGREES=8.


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def identity(path):
    path=Path(path);return {'file':str(path.relative_to(REPO)),'sha256':digest(path),'bytes':path.stat().st_size}
def write(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def window_weight(t,window):
    start,peak,end=window
    if t<=start or t>=end:return 0.
    return base.smooth((t-start)/(peak-start))*(1-base.smooth((t-peak)/(end-peak)))
def weight(t):
    if isinstance(t,bool) or not isinstance(t,(int,float)) or not math.isfinite(t) or not 0<=t<=DURATION:raise ValueError('finite source0–1.75 time required')
    return sum(window_weight(t,w) for w in WINDOWS)
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def patch_rotation(doc,binary,node,key,rotation):
    animation=doc['animations'][0]
    c=next(c for c in animation['channels'] if c['target']=={'node':node,'path':'rotation'})
    a=doc['accessors'][animation['samplers'][c['sampler']]['output']];v=doc['bufferViews'][a['bufferView']]
    assert a['componentType']==5126 and a['type']=='VEC4' and v.get('byteStride',16)==16
    offset=v.get('byteOffset',0)+a.get('byteOffset',0)+key*16
    old=struct.unpack_from('<4f',binary,offset);q=(rotation.x,rotation.y,rotation.z,rotation.w)
    if sum(x*y for x,y in zip(old,q))<0:q=tuple(-x for x in q)
    struct.pack_into('<4f',binary,offset,*q)


def prepare_veteran(raw_path,prefix,manifest,rig):
    character=next(c for c in manifest['characters'] if c['id']=='veteran')
    source_path,target,tb=library.pinned_source(character)
    grip_path,grip,gb=library.pinned_source(character['grip_source'])
    native_hands=library.sample_native_hands(target,grip,gb,character['grip_source'].get('time_seconds',2.117))
    source,sb=library.read_glb(raw_path)
    encoded,retarget=library.retarget_clip(source,sb,rig,target,tb,native_hands,'attack_overhead',source_contract='attack78')
    clip_path=OUT/(prefix+'_retargeted_overhead.glb');clip_path.write_bytes(encoded)
    lexical=lambda p:PRODUCER/('../refinement/combat-direction/native-weighted-overhead/'+str(p.relative_to(HERE)))
    clips=[('attack_overhead',lexical(clip_path),digest(clip_path))]
    timelines={'attack_overhead':library.decode_animation(source,sb)[1]}
    # The grounding implementation requires all five canonical clips. Build
    # those four unchanged helpers for this target only, once; reuse them for
    # before/after without retargeting the already-retargeted OH.
    for family_name in ('locomotion_source','attack_source'):
        family=manifest[family_name];_,family_rig,_=library.pinned_source(family)
        for entry in family['clips']:
            if entry['name'] not in ('idle','walk','attack_left','attack_right'):continue
            _,motion,mb=library.pinned_source(entry)
            timelines[entry['name']]=library.decode_animation(motion,mb)[1]
            path=OUT/('veteran_canonical_'+entry['name']+'_retargeted.glb')
            data,_=library.retarget_clip(motion,mb,family_rig,target,tb,native_hands,entry['name'],source_contract=family['contract'])
            if path.exists() and path.read_bytes()!=data:raise ValueError('canonical helper differs from current pinned native inputs:'+str(path))
            path.write_bytes(data)
            clips.append((entry['name'],lexical(path),digest(path)))
    body=OUT/(prefix+'_body.glb');preview=OUT/(prefix+'_prepared_png.glb');align_path=OUT/(prefix+'_alignment.json')
    alignment=library.prepare_character(source_path,character['source_sha256'],clips,body,preview,align_path,height=character['height_metres'],grip_frame=character['grip_frame'],finger_rotation_offsets=character.get('finger_rotation_offsets'),canonical_grounding_clips=timelines,weapon_source=manifest['weapon_source'])
    canonical_path=PARENT/'veteran_alignment.json'
    actual=json.loads(canonical_path.read_text())['canonical_root_grounding']
    canonical=alignment['canonical_root_grounding']
    assert np.max(np.abs(np.array(canonical['constant_local_root_shift'])-np.array(actual['constant_local_root_shift'])))<1e-8,'target canonical grounding reproduction drift'
    alignment['private_v5_validation']={'target':'veteran','RAW':identity(raw_path),'retarget_count':1,'target_native_right_grip':identity(grip_path),'target_finger_offset_applications':1,'target_root_shift_applications':1,'root_shift_method':'native canonical_grounding_clips actual timelines, target idle-derived once','root_shift_identity':identity(canonical_path),'retargeted_clip':identity(clip_path),'retarget_record':retarget,'canonical_source_timelines':timelines}
    alignment['outputs']=[identity(p) for p in (body,preview)];align_path.write_text(json.dumps(alignment,indent=2)+'\n')
    return preview,align_path


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    for path,sha in [(SOURCE,SOURCE_SHA),(RIG,RIG_SHA),(TARGET_BEFORE,TARGET_BEFORE_SHA)]:
        if digest(path)!=sha:raise ValueError('frozen source identity drift: '+str(path))
    reproduction=json.loads((OUT/'veteran_v4_defect_reproduction.json').read_text())
    assert [r['nonadjacent_region_triangle_pairs']['L_forearm__chest'] for r in reproduction['frames']]==[21,23]
    normals=[]
    for row in reproduction['frames']:
        normal=np.mean([p['chest_face_normal'] for p in row['geometry_diagnosis']['all_triangle_pairs']],axis=0)
        normal/=np.linalg.norm(normal);normals.append(Vector(normal))
    doc,binary=library.read_glb(SOURCE);rig,rigb=library.read_glb(RIG);library.require_same_rest(doc,rig)
    tracks,times=library.decode_animation(doc,binary);assert len(tracks)==234 and len(times)==211
    parents,order=library.node_order(doc);names={n.get('name'):i for i,n in enumerate(doc['nodes'])}
    parent_meta=json.loads((PARENT/'weighted_overhead_authoring.json').read_text());norm=library.local_matrix({'matrix':parent_meta['normalization_matrix_gltf']});inv=norm.inverted()
    packed=bytearray(binary);delta=[]
    for k,t in enumerate(times):
        w=weight(float(t))
        if not w:continue
        local=base.sample(doc,tracks,t);world=author.worlds(doc,local,parents,order)
        shoulder=(norm@world[names['L_Upperarm']]).translation
        wrist=(norm@world[names['L_Hand']]).translation
        elbow=(norm@world[names['L_Forearm']]).translation
        hand_rotation=world[names['L_Hand']].to_quaternion()
        axis=(wrist-shoulder).normalized()
        bend=elbow-shoulder-axis*(elbow-shoulder).dot(axis)
        tangent=axis.cross(bend).normalized()
        region=0 if window_weight(t,WINDOWS[0])>0 else 1
        # Fixed directions are chosen from the actual fault peak. Per-frame
        # sign selection would flip inside a nonzero envelope.
        direction=(-1.,1.)[region]
        angle=math.radians(ELBOW_SWIVEL_DEGREES)*w*direction
        pole=shoulder+Quaternion(axis,angle)@(elbow-shoulder)
        author.solve_arm(doc,local,'L_',inv@wrist,inv@pole,names,parents,order)
        world=author.worlds(doc,local,parents,order)
        author.set_world_rotation(local,names['L_Hand'],hand_rotation,world,parents)
        final=author.worlds(doc,local,parents,order)
        for name in BONES:patch_rotation(doc,packed,names[name],k,local[names[name]][1])
        delta.append({'source_seconds':t,'key_index':k,'weight':w,'window_index':region,'elbow_swivel_degrees':math.degrees(angle),'wrist_before_metres':list(wrist),'wrist_after_metres':list((norm@final[names['L_Hand']]).translation),'elbow_before_metres':list(elbow),'elbow_after_metres':list((norm@final[names['L_Forearm']]).translation),'world_hand_rotation_error_degrees':math.degrees(hand_rotation.rotation_difference(final[names['L_Hand']].to_quaternion()).angle)})
    doc=copy.deepcopy(doc)
    doc['extras']['weighted_overhead'].update(parent_sha256=SOURCE_SHA,revision='v5_left_elbow_waist_clearance',raw_right_calibration_applications=0)
    raw_path=OUT/'weighted_overhead_raw.glb';raw_path.write_bytes(library.encode_glb(doc,packed))
    print('V5_RAW_READY',str(raw_path),digest(raw_path),flush=True)
    manifest_path=PRODUCER/'motion_library.json';manifest=json.loads(manifest_path.read_text())
    # First recreate v3 through the identical target-native pipeline. Its OH
    # tracks must match Root's real assembled before-target before v4 is judged.
    before,before_align=prepare_veteran(SOURCE,'veteran_v4_reproduction',manifest,rig)
    preview,alignment_path=prepare_veteran(raw_path,'veteran',manifest,rig)
    meta={k:copy.deepcopy(v) for k,v in parent_meta.items() if k not in ('raw','raw_output','preview_outputs','frames','source_pins','parent','status')}
    meta.update(status='v5_RAW_ready_target_verification_pending',parent=identity(SOURCE),raw=identity(raw_path),raw_output={'file':raw_path.name,'sha256':digest(raw_path)},preview_outputs=[{'file':p.name,'sha256':digest(p)} for p in (preview,alignment_path)],preview_target='veteran',internal_preview_policy='PRIVATE veteran only, RAW retargeted once to actual veteran rest/native-grip; target finger offsets once and target constant idle-root shift once. Never use this target animation as RAW or retarget it a second time.',phase_contract={'source_phase_seconds':[0,.65,5/6,31/30,1.75],'contact_source_seconds':1.0,'contact_role':'metadata cue only; actual target mesh contact determines damage'},v5_delta={'reason':'Actual frozen veteran v4 near-elbow sleeve/armor versus Waist intersections: source1.1=21pairs and44/30=23pairs; before pixels show tucked inner armor contact without a visible gross cutout.','only_changed_tracks':[n+'.rotation' for n in BONES],'nominal_windows_seconds':WINDOWS,'envelope':'C2 analytic scalar window only; final sampled glTF remains LINEAR, with influence between unchanged neighboring keys','peak_elbow_swivel_degrees':ELBOW_SWIVEL_DEGREES,'fixed_swivel_direction_by_window':[-1,1],'clearance_normals_prepared_frame':[list(n) for n in normals],'left_wrist_and_world_palm_orientation':'fixed to parent v4 at each patched key; elbow swivels on the legal shoulder-wrist circle','right_hand_blade_and_all_other_animation_TRS_payloads':'byte-identical to frozen v4','changed_keys':delta},private_target_before=identity(TARGET_BEFORE),private_reproduction=identity(before),private_target_after=identity(preview),source_pins={str(p.relative_to(REPO)):digest(p) for p in [Path(__file__),SOURCE,RIG,TARGET_BEFORE,manifest_path,Path(base.__file__),Path(author.__file__),Path(library.__file__),PRODUCER/'prepare_rigged_warrior.py',PRODUCER/'refine_character_grips.py',FINE.parent/'run_blender.py']})
    target_alignment=json.loads(alignment_path.read_text())
    meta['raw_body_source']=copy.deepcopy(parent_meta['raw_body_source'])
    meta['body_source']=next(c for c in manifest['characters'] if c['id']=='veteran')
    meta['preview_grounding']=target_alignment['canonical_root_grounding']
    meta['preview_normalization_matrix_gltf']=target_alignment['normalization_matrix_gltf']
    meta['raw_normalization_policy']='normalization_matrix_gltf is the original v3 base RAW authoring frame; preview uses its own explicit veteran normalization and grounding above.'
    dependencies=[PRODUCER/'attack_grounding.py',PARENT/'veteran_alignment.json']
    for entry in [meta['body_source'],meta['body_source']['grip_source'],manifest['weapon_source']]:dependencies.append(PRODUCER/entry['source'])
    for family_name in ('locomotion_source','attack_source'):
        family=manifest[family_name];dependencies.append(PRODUCER/family['source'])
        dependencies.extend(PRODUCER/e['source'] for e in family['clips'] if e['name'] in ('idle','walk','attack_left','attack_right'))
    dependencies.extend(OUT.glob('veteran_canonical_*_retargeted.glb'))
    for path in dependencies:meta['source_pins'][str(path.relative_to(REPO))]=digest(path)
    meta['preserved_v4_right_arm_delta']=meta.pop('v4_delta')
    write('weighted_overhead_authoring.json',meta)
    write('weighted_overhead_delta.json',{'raw':identity(raw_path),'parent':identity(SOURCE),'delta':meta['v5_delta'],'reproduction_before_fix':identity(OUT/'veteran_v4_defect_reproduction.json')})
    print('V5_VETERAN_READY',str(preview),digest(preview),flush=True)

if __name__=='__main__':build()
