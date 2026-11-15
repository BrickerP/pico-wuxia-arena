"""Bounded source validation: full30Hz + named critical poses; no release claim."""
import copy,json,math,sys
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_weighted_overhead as build
sys.path.insert(0,str(build.FINE))
import verify_fine_overhead as utility
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
import numpy as np

def u_error(a,c,path):
    d=max(abs(x-y) for x,y in zip(a,c))
    return min(d,max(abs(x+y) for x,y in zip(a,c))) if path=='rotation' else d

def main():
    b=build;out=b.OUT
    meta=json.loads((out/'weighted_overhead_authoring.json').read_text())
    raw,rb=b.library.read_glb(out/'weighted_overhead_raw.glb')
    preview,pb=b.library.read_glb(out/'weighted_overhead_preview.glb')
    parent,sourceb=b.library.read_glb(b.SOURCE);rig,rigb=b.library.read_glb(b.RIG)
    rt,keys=b.library.decode_animation(raw,rb);pt,pkeys=b.library.decode_animation(preview,pb);st,_=b.library.decode_animation(parent,sourceb)
    assert b.digest(out/'weighted_overhead_raw.glb')==meta['raw']['sha256']
    for row in meta['preview_outputs']:assert b.digest(out/row['file'])==row['sha256']
    assert len(rt)==len(pt)==234 and len(keys)==len(pkeys)==211 and keys[0]==0 and keys[-1]==1.75
    assert len(raw['skins'][0]['joints'])==78
    for field in ('nodes','skins','meshes','materials','textures','images'):assert raw[field]==rig[field],field
    assert rb[:len(rigb)]==rigb
    assert all(row[2]=='LINEAR' and row[0]==keys for row in rt.values())
    for key,row in rt.items():
        assert row[1][0]==row[1][-1]==st[key][1][0],('endpoint',key)
        assert np.isfinite(np.array(row[1])).all()
    names={n.get('name'):i for i,n in enumerate(raw['nodes'])};pn={n.get('name'):i for i,n in enumerate(preview['nodes'])}
    for name in b.base.RIGHT_FINGERS:
        for path in ('translation','rotation','scale'):
            assert all(row==st[names[name],path][1][0] for row in rt[names[name],path][1]),('unbaked_R15',name,path)
    rp,ro=b.library.node_order(raw);pp,po=b.library.node_order(preview)
    norm=b.library.local_matrix({'matrix':meta['normalization_matrix_gltf']})
    guard=b.base.sample(raw,rt,0);gw=b.author.worlds(raw,guard,rp,ro)
    from prepare_rigged_warrior import apply_finger_rotation_offsets
    calibrated=copy.deepcopy(raw)
    calibrated_binary,_=apply_finger_rotation_offsets(calibrated,rb,meta['body_source'].get('finger_rotation_offsets'))
    expected_tracks,_=b.library.decode_animation(calibrated,calibrated_binary)
    bake_error=0.;root_shift=meta['preview_grounding']['constant_local_root_shift']
    import struct
    for (i,path),track in expected_tracks.items():
        other=pt[pn[raw['nodes'][i]['name']],path]
        for a,c in zip(track[1],other[1]):
            if raw['nodes'][i].get('name')=='BoneRoot' and path=='translation':a=struct.unpack('<3f',struct.pack('<3f',*[x+y for x,y in zip(a,root_shift)]))
            bake_error=max(bake_error,u_error(a,c,path))
    assert bake_error<1e-7,('once calibration/rootshift',bake_error)
    reference={i:(gw[i].translation-gw[rp[i]].translation).length for i in raw['skins'][0]['joints'] if i in rp and rp[i] in raw['skins'][0]['joints'] and raw['nodes'][i].get('name') not in ('BoneRoot','Hip')}
    geometry=b.stance.foot_geometry(preview,pb);blade=utility.surface(preview,pb)
    # Reuse the established exact body mesh pool assembly, not proxies.
    target,tb=b.library.read_glb(b.base.PRODUCER/meta['body_source']['source'])
    mesh=target['meshes'][next(n['mesh'] for n in target['nodes'] if 'mesh' in n)]
    positions=[];palettes=[];weights=[];faces=[];pools={};offset=0
    for primitive in mesh['primitives']:
        attrs=primitive['attributes'];identity=tuple(attrs[k] for k in ('POSITION','JOINTS_0','WEIGHTS_0'))
        if identity not in pools:
            points=utility.accessor(target,tb,attrs['POSITION']).astype(float);pools[identity]=offset;positions.append(points)
            palettes.append(utility.accessor(target,tb,attrs['JOINTS_0']).astype(int));weights.append(utility.accessor(target,tb,attrs['WEIGHTS_0']).astype(float));offset+=len(points)
        faces.append(utility.accessor(target,tb,primitive['indices']).reshape(-1,3).astype(int)+pools[identity])
    bp=np.column_stack((np.concatenate(positions),np.ones(offset)));bj=np.concatenate(palettes);bw=np.concatenate(weights);bw/=bw.sum(axis=1)[:,None];bf=np.concatenate(faces)
    bind=utility.accessor(target,tb,target['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    bodyj=preview['skins'][0]['joints']
    times=sorted(set([i/30 for i in range(53) if i/30<=1.75]+[.68,.75,.82,.90,.93,1.,1.15,1.16,1.34,1.42,1.50,1.55,1.75]))
    rows=[];sole=slip=bone=0.;feet0=None
    for number,t in enumerate(times):
        local=b.base.sample(raw,rt,t);world=b.author.worlds(raw,local,rp,ro)
        pl=b.base.sample(preview,pt,t);pw=b.author.worlds(preview,pl,pp,po)
        fs=b.stance.foot_measurements(geometry,pw,Matrix.Identity(4))
        if feet0 is None:feet0=fs
        for side,f in fs.items():
            sole=max(sole,abs(f['sole_height_metres']+.028));slip=max(slip,float(np.linalg.norm(np.array(f['centre_metres'])-np.array(feet0[side]['centre_metres']))))
        for i,ref in reference.items():bone=max(bone,abs((world[i].translation-world[rp[i]].translation).length-ref)*norm.to_scale()[0])
        parts=utility.steel_points(blade,pw);steel=np.concatenate([part[2] for part in parts])
        transforms=np.array([list(pw[i]) for i in bodyj])@bind
        blended=np.sum(transforms[bj]*bw[:,:,None,None],axis=1);body=np.einsum('vij,vj->vi',blended,bp)[:,:3]
        triangles=body[bf];low,high=steel.min(axis=0)-.00001,steel.max(axis=0)+.00001
        mask=((triangles.min(axis=1)<=high)&(triangles.max(axis=1)>=low)).all(axis=1);selected=bf[mask]
        overlaps=[]
        if len(selected):
            body_bvh=BVHTree.FromPolygons(body.tolist(),selected.tolist(),all_triangles=True,epsilon=0.)
            for primitive,material,points,indices in parts:
                weapon=BVHTree.FromPolygons(points.tolist(),indices.tolist(),all_triangles=True,epsilon=0.);hit=weapon.overlap(body_bvh)
                if hit:
                    vertices=selected[[pair[1] for pair in hit]].ravel();dominant=bj[vertices,np.argmax(bw[vertices],axis=1)]
                    regions=Counter(preview['nodes'][bodyj[int(j)]]['name'] for j in dominant)
                    overlaps.append({'primitive':primitive,'material':material,'triangle_pair_count':len(hit),'body_joint_regions':dict(regions)})
        hip=(norm@world[names['Hip']]).translation;chest=(norm@world[names['Spine02']]).translation
        torso=chest-hip
        # Reference frame from guard's actual chest (rotation delta, not head-to-hip).
        delta=(norm@world[names['Spine02']]).to_quaternion()@(norm@gw[names['Spine02']]).to_quaternion().inverted()
        euler=delta.to_euler('XYZ')
        head=(norm@world[names['Head']]).translation
        steel_head_distance=float(np.linalg.norm(steel-np.array(head),axis=1).min())
        contact=utility.true_contact(parts,.9)
        row={'source_seconds':t,'hip_metres':list(hip),'chest_metres':list(chest),'hip_to_Spine02_sagittal_degrees':math.degrees(math.atan2(torso.z,torso.y)),'chest_world_guard_delta_XYZ_degrees':[math.degrees(v) for v in euler],'R_hand_metres':list((norm@world[names['R_Hand']]).translation),'L_hand_metres':list((norm@world[names['L_Hand']]).translation),'R_elbow_metres':list((norm@world[names['R_Forearm']]).translation),'L_elbow_metres':list((norm@world[names['L_Forearm']]).translation),'L_shoulder_metres':list((norm@world[names['L_Upperarm']]).translation),'steel_bounds_metres':{'min':steel.min(axis=0).tolist(),'max':steel.max(axis=0).tolist()},'steel_vertex_to_head_origin_minimum_metres':steel_head_distance,'actual_steel_body_triangle_overlaps':overlaps,'z_0p9_surface_intersections':len(contact),'foot_surfaces':fs}
        if abs(t-1.)<1e-8:row['actual_steel_contact_plane_intersections']=contact
        rows.append(row)
        print('WEIGHTED_CHECK',number+1,len(times),t,'overlaps',sum(x['triangle_pair_count'] for x in overlaps),flush=True)
    overlap=[r for r in rows if r['actual_steel_body_triangle_overlaps']]
    result={'status':'bounded_source_checks_passed' if not overlap and sole<2e-5 and slip<1e-4 and bone<2e-6 else 'bounded_source_checks_failed','raw':b.identity(out/'weighted_overhead_raw.glb'),'preview':b.identity(out/'weighted_overhead_preview.glb'),'source_authoring':b.identity(out/'weighted_overhead_authoring.json'),'all234_channels_78joints_211keys_complete':True,'native_rest_mesh_skin_and_payload_unchanged':True,'unbaked_right15_exact_parent':True,'guard_endpoint_float32_values_exact':True,'preview_once_finger_calibration_and_once_root_shift_max_component_error':bake_error,'maximum_bone_length_change_metres':bone,'maximum_actual_shoe_sole_error_metres':sole,'maximum_actual_shoe_centre_motion_metres':slip,'steel_body_overlap_sample_count':len(overlap),'sample_count':len(times),'scan_scope':'full0–1.75s at30Hz plus explicit load/drive/contact/follow poses','collision_scope':'true posed sharpened steel triangles against all actual posed body material primitives including head/hands/feet/torso; no capsules','limits':['No continuous-time proof between samples.','Body-body cloth volume penetration is not certified by this blade/body surface scan.','Contact plane z=.9 is a source reference, not the runtime target; Root owns actual damage cue.','No native runtime or target retarget acceptance.'],'frames':rows,'source_pins':{str(p.relative_to(b.REPO)):b.digest(p) for p in [Path(__file__),Path(utility.__file__),b.base.PRODUCER/'prepare_rigged_warrior.py']}}
    b.write('weighted_overhead_verification.json',result)
    print('WEIGHTED_VERIFICATION',json.dumps({k:v for k,v in result.items() if k not in ('frames','source_pins')},indent=2),flush=True)
    if result['status'].endswith('failed'):raise SystemExit(2)

if __name__=='__main__':main()
