"""Bounded nonadjacent arm/head/chest true triangle check, with v9 comparison."""
import copy,json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_weighted_overhead as b
sys.path.insert(0,str(b.FINE))
import verify_fine_overhead as u
from mathutils.bvhtree import BVHTree
import numpy as np

def require(condition,message):
    if not condition:raise ValueError(message)

def validate_time(t):
    require(not isinstance(t,bool) and isinstance(t,(int,float,np.floating)) and math.isfinite(t) and 0<=t<=1.75,'invalid finite source0–1.75 time')

def validate_contract(doc,binary,source_tracks):
    tracks,times=b.library.decode_animation(doc,binary)
    require(len(tracks)==234 and len(times)==211,'complete234/211 contract required')
    for t in times:validate_time(t)
    require(times[0]==0 and times[-1]==1.75 and all(y>x for x,y in zip(times,times[1:])),'invalid timeline')
    for key,row in tracks.items():
        require(np.isfinite(np.array(row[1])).all(),'nonfinite track')
        require(row[1][0]==row[1][-1]==source_tracks[key][1][0],'guard closure not exact')
    return tracks

def validate_pin(path,sha):require(b.digest(path)==sha,'candidate sourceSHA mismatch')

def main():
    out=b.OUT;meta=json.loads((out/'weighted_overhead_authoring.json').read_text())
    raw,rb=b.library.read_glb(out/'weighted_overhead_raw.glb');source,sb=b.library.read_glb(b.SOURCE);st,_=b.library.decode_animation(source,sb)
    validate_pin(out/'weighted_overhead_raw.glb',meta['raw']['sha256']);validate_contract(raw,rb,st)
    rejected=[]
    for t in [float('nan'),float('inf'),-.001,1.751,True]:
        try:validate_time(t)
        except ValueError:rejected.append('time:'+repr(t))
        else:raise AssertionError('bad time accepted')
    try:validate_pin(out/'weighted_overhead_raw.glb','0'*64)
    except ValueError:rejected.append('actual candidate sourceSHA mismatch')
    else:raise AssertionError('wrong sourceSHA accepted')
    # Perturb an actual exported float32 last guard translation in memory.
    bad=bytearray(rb);animation=raw['animations'][0]
    channel=next(c for c in animation['channels'] if c['target']['path']=='translation')
    sampler=animation['samplers'][channel['sampler']];a=raw['accessors'][sampler['output']];v=raw['bufferViews'][a['bufferView']]
    import struct
    pos=v.get('byteOffset',0)+a.get('byteOffset',0)+(a['count']-1)*12
    old=struct.unpack_from('<f',bad,pos)[0];struct.pack_into('<f',bad,pos,old+.01)
    try:validate_contract(raw,bad,st)
    except ValueError:rejected.append('mutated actual exported guard closure')
    else:raise AssertionError('broken guard accepted')
    preview,pb=b.library.read_glb(out/'weighted_overhead_preview.glb');pt,_=b.library.decode_animation(preview,pb);pp,po=b.library.node_order(preview)
    v9,v9b=b.library.read_glb(b.FINE/'candidate/v9/fine_overhead_preview.glb');v9t,_=b.library.decode_animation(v9,v9b);vp,vo=b.library.node_order(v9)
    target,tb=b.library.read_glb(b.base.PRODUCER/meta['body_source']['source']);mesh=target['meshes'][next(n['mesh'] for n in target['nodes'] if 'mesh' in n)]
    positions=[];palettes=[];weights=[];faces=[];pools={};offset=0
    for primitive in mesh['primitives']:
        attrs=primitive['attributes'];identity=tuple(attrs[k] for k in ('POSITION','JOINTS_0','WEIGHTS_0'))
        if identity not in pools:
            p=u.accessor(target,tb,attrs['POSITION']).astype(float);pools[identity]=offset;positions.append(p)
            palettes.append(u.accessor(target,tb,attrs['JOINTS_0']).astype(int));weights.append(u.accessor(target,tb,attrs['WEIGHTS_0']).astype(float));offset+=len(p)
        faces.append(u.accessor(target,tb,primitive['indices']).reshape(-1,3).astype(int)+pools[identity])
    pos=np.column_stack((np.concatenate(positions),np.ones(offset)));pal=np.concatenate(palettes);wgt=np.concatenate(weights);wgt/=wgt.sum(axis=1)[:,None];faces=np.concatenate(faces)
    bind=u.accessor(target,tb,target['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    joints=preview['skins'][0]['joints'];joint_names=[preview['nodes'][i]['name'] for i in joints];dominant=np.array([joint_names[int(i)] for i in pal[np.arange(len(pal)),np.argmax(wgt,axis=1)]])
    groups={
        'head':{'Head','L_Eye','R_Eye','FacialBone'},
        'chest':{'Waist','Spine01','Spine02'},
    }
    for side in ('L_','R_'):
        groups[side+'forearm']={side+n for n in ('Forearm','ForearmTwist01','ForearmTwist02','ElbowShareBone')}
        groups[side+'hand']={n for n in joint_names if n==side+'Hand' or n.startswith(tuple(side+f for f in ('Thumb','Index','Mid','Ring','Pinky')))}
    regions={}
    for label,names in groups.items():
        mask=np.isin(dominant,list(names));subset=faces[mask[faces].all(axis=1)]
        indices,remap=np.unique(subset,return_inverse=True);regions[label]=(indices,remap.reshape(-1,3))
        require(len(subset)>0,'empty actual semantic region:'+label)
    pairs=[(limb,core) for limb in ('R_forearm','R_hand','L_forearm','L_hand') for core in ('head','chest')]
    v9names={n.get('name'):i for i,n in enumerate(v9['nodes'])};vj=[v9names[n] for n in joint_names]
    def skin(world,indices):
        trans=np.array([list(world[i]) for i in indices])@bind
        blend=np.sum(trans[pal]*wgt[:,:,None,None],axis=1)
        return np.einsum('vij,vj->vi',blend,pos)[:,:3]
    def overlaps(points):
        trees={label:BVHTree.FromPolygons(points[index].tolist(),mapped.tolist(),all_triangles=True,epsilon=0.) for label,(index,mapped) in regions.items()}
        return {limb+'__'+core:len(trees[limb].overlap(trees[core])) for limb,core in pairs}
    times=sorted(set([i/30 for i in range(53)]+[.68,.75,.82,.90,.93,1.,1.15,1.16,1.34,1.42,1.50,1.55,1.75]))
    rows=[]
    for t in times:
        world=b.author.worlds(preview,b.base.sample(preview,pt,t),pp,po);candidate=overlaps(skin(world,joints))
        baseline=None
        if any(candidate.values()):
            oldworld=b.author.worlds(v9,b.base.sample(v9,v9t,t),vp,vo);baseline=overlaps(skin(oldworld,vj))
        rows.append({'source_seconds':t,'candidate_true_triangle_pair_counts':candidate,'same_time_parent_v9_counts_when_candidate_overlap':baseline})
        print('SELF_REGIONS',t,candidate,flush=True)
    failures=[r for r in rows if any(r['candidate_true_triangle_pair_counts'].values())]
    result={'status':'sampled_nonadjacent_regions_clear' if not failures else 'sampled_nonadjacent_region_overlaps_found','raw':b.identity(out/'weighted_overhead_raw.glb'),'preview':b.identity(out/'weighted_overhead_preview.glb'),'source_authoring':b.identity(out/'weighted_overhead_authoring.json'),'parent_v9_preview':b.identity(b.FINE/'candidate/v9/fine_overhead_preview.glb'),'sample_count':len(times),'overlap_sample_count':len(failures),'scope':'63 discrete poses: full30Hz plus named critical times. Actual skinned body material triangles for R/L forearm and hand versus head/chest.','semantic_region_rule':'All3 triangle vertices must have dominant skin joint in same explicit anatomical region. Shared boundary and adjacent upperarm/neck triangles are excluded; within-region cloth layers never tested against each other.','region_triangle_counts':{label:len(row[1]) for label,row in regions.items()},'rejection_cases_actually_run':rejected,'limits':['Not continuous-time/volumetric proof.','Dominant-weight core regions exclude skinning blend seams and upperarm-to-chest adjacent junction.','Zero region overlap does not certify every cloth layer or every body-body pair.'],'frames':rows,'source_pins':{str(p.relative_to(b.REPO)):b.digest(p) for p in [Path(__file__),Path(u.__file__)]}}
    b.write('weighted_overhead_regions_verification.json',result)
    print('REGION_RESULT',result['status'],'overlap_samples',len(failures),flush=True)
    if failures:raise SystemExit(2)

if __name__=='__main__':main()
