"""Numerical evidence for the private overhead; does not approve visual quality."""
import copy
import json
import math
import struct
import sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_fine_overhead as build
from mathutils import Matrix,Vector
from prepare_rigged_warrior import apply_finger_rotation_offsets
import numpy as np

def angle(a,b):
    theta = math.degrees(a.rotation_difference(b).angle)
    return min(theta,360.-theta)

def maximum_row_delta(a,b,path):
    normal=max(abs(x-y) for x,y in zip(a,b))
    return min(normal,max(abs(x+y) for x,y in zip(a,b))) if path=='rotation' else normal

def accessor(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()

def mesh_signature(doc,binary):
    result=[]
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            attrs={key:accessor(doc,binary,index) for key,index in primitive['attributes'].items()}
            attrs['indices']=build.author.accessor(doc,binary,primitive['indices'])
            attrs['material']=doc['materials'][primitive['material']]
            result.append(attrs)
    return result

def surface(doc,binary):
    skin=doc['skins'][0]
    joints=skin['joints']
    inverse=build.author.accessor(doc,binary,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    parts=[]
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        for number,p in enumerate(doc['meshes'][node['mesh']]['primitives']):
            material=doc['materials'][p['material']].get('name','')
            if 'Steel' not in material:
                continue
            attrs=p['attributes']
            positions=build.author.accessor(doc,binary,attrs['POSITION']).astype(float)
            palettes=build.author.accessor(doc,binary,attrs['JOINTS_0']).astype(int)
            weights=build.author.accessor(doc,binary,attrs['WEIGHTS_0']).astype(float)
            weights/=weights.sum(axis=1)[:,None]
            faces=build.author.accessor(doc,binary,p['indices']).reshape(-1,3).astype(int)
            parts.append((number,material,np.column_stack((positions,np.ones(len(positions)))),palettes,weights,faces))
    if not parts:
        raise ValueError('actual steel mesh absent')
    return joints,inverse,parts

def steel_points(surface,world):
    joints,inverse,parts=surface
    transforms=np.array([list(world[i]) for i in joints])@inverse
    rows=[]
    for index,name,positions,palettes,weights,faces in parts:
        blended=np.sum(transforms[palettes]*weights[:,:,None,None],axis=1)
        points=np.einsum('vij,vj->vi',blended,positions)[:,:3]
        rows.append((index,name,points,faces))
    return rows

def true_contact(parts,plane):
    found=[]
    for primitive,name,points,faces in parts:
        for triangle,indices in enumerate(faces):
            polygon=points[indices]
            edge=[]
            for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
                if (a[2]-plane)*(b[2]-plane)<=0 and abs(b[2]-a[2])>1e-9:
                    edge.append(a+(b-a)*((plane-a[2])/(b[2]-a[2])))
            if len(edge)<2:
                continue
            point=np.mean(edge,axis=0)
            normal=np.cross(polygon[1]-polygon[0],polygon[2]-polygon[0]);normal/=np.linalg.norm(normal)
            found.append({'primitive':primitive,'triangle':triangle,'material':name,'point_metres':point.tolist(),'normal':normal.tolist()})
    return found

def main():
    metadata=json.loads(build.output('fine_overhead_metadata.json').read_text())
    for path,sha in metadata['source_pins'].items():
        assert build.digest(build.REPO/path)==sha,('source drift',path)
    for row in metadata['preview_outputs']:
        assert build.digest(build.output(row['file']))==row['sha256'],row['file']
    assert build.digest(build.output(metadata['raw_output']['file']))==metadata['raw_output']['sha256']
    rig_path,native_path,guard_path,_=build.FIXED_PINS
    rig,rb=build.library.read_glb(rig_path)
    raw,rawb=build.library.read_glb(build.output('fine_overhead_raw.glb'))
    preview,pb=build.library.read_glb(build.output('fine_overhead_preview.glb'))
    guard,gb=build.library.read_glb(guard_path)
    native,nb=build.library.read_glb(native_path)
    assert rawb[:len(rb)]==rb
    for field in ('nodes','skins','meshes','materials','textures','images'):
        assert raw[field]==rig[field],field
    tracks,times=build.library.decode_animation(raw,rawb)
    final,final_times=build.library.decode_animation(preview,pb)
    gt,_=build.library.decode_animation(guard,gb)
    nt,_=build.library.decode_animation(native,nb)
    assert len(tracks)==len(final)==metadata['native_channel_count']==234
    assert len(times)==211 and times==final_times and times[0]==0 and times[-1]==1.75
    assert all(row[2]=='LINEAR' and row[0]==times for row in tracks.values())
    names={n.get('name'):i for i,n in enumerate(raw['nodes'])}
    pn={n.get('name'):i for i,n in enumerate(preview['nodes'])}
    parent,order=build.library.node_order(raw)
    pp,po=build.library.node_order(preview)
    norm=build.library.local_matrix({'matrix':json.loads(build.output('fine_overhead_alignment.json').read_text())['normalization_matrix_gltf']})
    canonical=build.sample(rig,gt,0)
    canonical_world=build.author.worlds(rig,canonical,parent,order)
    close_error=0
    endpoint_raw_component_error=0
    for time in (0,1.75):
        local=build.sample(raw,tracks,time)
        for (i,path),track in tracks.items():
            source=gt[i,path]
            expected=build.library.sample_track(source,0.,path=='rotation')
            actual=build.library.sample_track(track,time,path=='rotation')
            endpoint_raw_component_error=max(endpoint_raw_component_error,maximum_row_delta(actual,expected,path))
        for i in canonical:
            close_error=max(close_error,max(abs(a-b) for a,b in zip(local[i][0],canonical[i][0])),
                            max(abs(a-b) for a,b in zip(local[i][2],canonical[i][2])),
                            maximum_row_delta(tuple(local[i][1]),tuple(canonical[i][1]),'rotation'))
    assert close_error<1e-6,close_error
    for key,track in tracks.items():
        assert track[1][0]==track[1][-1]==gt[key][1][0],('canonical endpoint float32 bytes',key)
    hands=build.library.sample_native_hands(rig,native,nb,2.117)
    right_error=0
    right_constant_component_error=0
    for name in build.RIGHT_FINGERS:
        components=list(hands[name].decompose())
        for path,slot in [('translation',0),('rotation',1),('scale',2)]:
            component=components[slot]
            expected=(component.x,component.y,component.z,component.w) if slot==1 else tuple(component)
            for value in tracks[names[name],path][1]:
                right_error=max(right_error,maximum_row_delta(value,expected,path))
                right_constant_component_error=max(right_constant_component_error,maximum_row_delta(value,tracks[names[name],path][1][0],path))
    assert right_error<3e-7,right_error
    assert right_constant_component_error==0.,right_constant_component_error
    calibrated=copy.deepcopy(raw)
    calibratedb,_=apply_finger_rotation_offsets(calibrated,rawb,metadata['calibration_stages']['preview']['offsets'])
    expected,_=build.library.decode_animation(calibrated,calibratedb)
    shift=metadata['preview_grounding']['constant_local_root_shift']
    bake_error=0
    for (index,path),row in expected.items():
        target=final[pn[raw['nodes'][index]['name']],path]
        for a,b in zip(row[1],target[1]):
            if raw['nodes'][index].get('name')=='BoneRoot' and path=='translation':
                a=struct.unpack('<3f',struct.pack('<3f',*[x+y for x,y in zip(a,shift)]))
            bake_error=max(bake_error,maximum_row_delta(a,b,path))
    assert bake_error<1e-7,bake_error
    # Current formal PNG is the exact semantic view checked by the renderer.
    formal,fb=build.library.read_glb(build.PRODUCER/'library/base_prepared_png.glb')
    a,b=mesh_signature(preview,pb),mesh_signature(formal,fb)
    assert len(a)==len(b)
    for i,(left,right) in enumerate(zip(a,b)):
        assert left.keys()==right.keys(),i
        for key in left:
            assert left[key]==right[key] if key=='material' else np.array_equal(left[key],right[key]),(i,key)
    foot_geometry=build.stance.foot_geometry(preview,pb)
    blade=surface(preview,pb)
    reference_feet=None
    sole_error,foot_slip,bone_error=0.,0.,0.
    world_steps={name:0. for name in ('Hip','Spine02','R_Upperarm','R_Forearm','R_Hand','L_Forearm')}
    local_steps={name:0. for name in world_steps}
    previous_world=previous_local=None
    measurements=[]
    native_world_error=0.
    native_wrist_local_error=0.
    from mathutils.bvhtree import BVHTree
    mesh=next(preview['meshes'][n['mesh']] for n in preview['nodes'] if n.get('name')=='TripoBody_Mesh')
    source=metadata['body_source']
    target,tb=build.library.read_glb(build.PRODUCER/source['source'])
    body_mesh=target['meshes'][next(n['mesh'] for n in target['nodes'] if 'mesh' in n)]
    # Each official material primitive can own a different vertex pool.
    # Concatenate unique pools and remap every primitive's local indices.
    positions_list=[];palettes_list=[];weights_list=[];faces_list=[];pools={};offset=0
    for primitive in body_mesh['primitives']:
        attrs=primitive['attributes']
        identity=tuple(attrs[key] for key in ('POSITION','JOINTS_0','WEIGHTS_0'))
        if identity not in pools:
            positions=accessor(target,tb,attrs['POSITION']).astype(float)
            pools[identity]=offset
            positions_list.append(positions)
            palettes_list.append(accessor(target,tb,attrs['JOINTS_0']).astype(int))
            weights_list.append(accessor(target,tb,attrs['WEIGHTS_0']).astype(float))
            offset+=len(positions)
        faces_list.append(accessor(target,tb,primitive['indices']).reshape(-1,3).astype(int)+pools[identity])
    body_positions=np.concatenate(positions_list)
    body_palettes=np.concatenate(palettes_list)
    body_weights=np.concatenate(weights_list)
    body_weights/=body_weights.sum(axis=1)[:,None]
    body_faces=np.concatenate(faces_list)
    body_bind=accessor(target,tb,target['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    body_joints=preview['skins'][0]['joints']
    body_positions=np.column_stack((body_positions,np.ones(len(body_positions))))
    collision_rows=[]
    for time in times:
        raw_local=build.sample(raw,tracks,time)
        raw_world=build.author.worlds(raw,raw_local,parent,order)
        local=build.sample(preview,final,time)
        world=build.author.worlds(preview,local,pp,po)
        feet=build.stance.foot_measurements(foot_geometry,world,Matrix.Identity(4))
        if reference_feet is None:
            reference_feet=feet
        for side,value in feet.items():
            sole_error=max(sole_error,abs(value['sole_height_metres']+.028))
            foot_slip=max(foot_slip,float(np.linalg.norm(np.array(value['centre_metres'])-np.array(reference_feet[side]['centre_metres']))))
        for index in raw['skins'][0]['joints']:
            if index not in parent or parent[index] not in raw['skins'][0]['joints'] or raw['nodes'][index].get('name') in {'BoneRoot','Hip'}:
                continue
            p=parent[index]
            reference=(canonical_world[index].translation-canonical_world[p].translation).length
            actual=(raw_world[index].translation-raw_world[p].translation).length
            bone_error=max(bone_error,abs(actual-reference)*norm.to_scale()[0])
        if previous_world:
            for name in world_steps:
                world_steps[name]=max(world_steps[name],angle(previous_world[pn[name]].to_quaternion(),world[pn[name]].to_quaternion()))
                local_steps[name]=max(local_steps[name],angle(previous_local[pn[name]][1],local[pn[name]][1]))
        if .98<=time<=1.3:
            native_local=build.sample(rig,nt,build.native_time(time))
            native_world=build.author.worlds(rig,native_local,parent,order)
            native_wrist_local_error=max(native_wrist_local_error,maximum_row_delta(tuple(raw_local[names['R_Hand']][1]),tuple(native_local[names['R_Hand']][1]),'rotation'))
            for name in ('R_Upperarm','R_Forearm','R_Hand'):
                native_world_error=max(native_world_error,maximum_row_delta(tuple(raw_world[names[name]].to_quaternion()),tuple(native_world[names[name]].to_quaternion()),'rotation'))
        parts=steel_points(blade,world)
        positions=np.concatenate([r[2] for r in parts])
        row={'source_seconds':time,'blade_bounds_metres':{'min':positions.min(axis=0).tolist(),'max':positions.max(axis=0).tolist()}}
        if abs(time-1)<1e-6:
            row['contact_plane_z_0p9_intersections']=true_contact(parts,.9)
            row['actual_steel_surface_midpoint']=(positions.min(axis=0)+(positions.max(axis=0)-positions.min(axis=0))*.5).tolist()
        # Broadphase real triangles against the true posed blade bounds, then
        # exact BVH triangle overlap. This scans the skinned current body,
        # including head, sleeve, hand and torso; no capsule stand-ins.
        if round(time*120)%2==0:
            transforms=np.array([list(world[i]) for i in body_joints])@body_bind
            blended=np.sum(transforms[body_palettes]*body_weights[:,:,None,None],axis=1)
            body_points=np.einsum('vij,vj->vi',blended,body_positions)[:,:3]
            triangles=body_points[body_faces]
            low,high=positions.min(axis=0)-.00001,positions.max(axis=0)+.00001
            mask=((triangles.min(axis=1)<=high)&(triangles.max(axis=1)>=low)).all(axis=1)
            selected=body_faces[mask]
            overlaps=[]
            if len(selected):
                body_bvh=BVHTree.FromPolygons(body_points.tolist(),selected.tolist(),all_triangles=True,epsilon=0.)
                for primitive,name,points,faces in parts:
                    blade_bvh=BVHTree.FromPolygons(points.tolist(),faces.tolist(),all_triangles=True,epsilon=0.)
                    hit=blade_bvh.overlap(body_bvh)
                    if hit:
                        from collections import Counter
                        region_indices=selected[[pair[1] for pair in hit]].ravel()
                        dominant=body_palettes[region_indices,np.argmax(body_weights[region_indices],axis=1)]
                        regions=Counter(preview['nodes'][body_joints[int(palette)]]['name'] for palette in dominant)
                        overlaps.append({'primitive':primitive,'material':name,'triangle_pair_count':len(hit),'body_joint_regions':dict(regions)})
            collision_rows.append({'source_seconds':time,'body_broadphase_triangles':int(mask.sum()),'actual_steel_body_triangle_overlaps':overlaps})
        measurements.append(row)
        previous_world,previous_local=world,local
    build.write('fine_overhead_surface_probe.json',{'steel_body_surface_scan':collision_rows,'blade_motion':measurements})
    assert sole_error<2e-5,sole_error
    assert foot_slip<2e-5,foot_slip
    assert bone_error<2e-6,bone_error
    assert world_steps['R_Hand']<15.,world_steps['R_Hand']
    assert native_wrist_local_error<2e-6,native_wrist_local_error
    failures=[]
    for invalid in (float('nan'),float('inf'),-.001,1.751,True,'1'):
        try:build.native_time(invalid)
        except ValueError:failures.append(repr(invalid))
        else:raise AssertionError(('accepted invalid native time',invalid))
    for x,y in [([0,0],[1,2]),([0,1],[2,1]),([0,float('nan')],[0,1])]:
        try:build.warp_slopes(x,y)
        except ValueError:failures.append('nonmonotonic/nonfinite knots')
        else:raise AssertionError('accepted invalid knots')
    warp=[build.native_time(i/1200) for i in range(2101)]
    assert all(b>=a-1e-12 for a,b in zip(warp,warp[1:]))
    assert all(abs(build.native_time(t)-n)<1e-12 for t,n in zip(build.WARP_X,build.WARP_Y))
    contact=next(r for r in measurements if abs(r['source_seconds']-1)<1e-6)
    result={'completion':'numerical_checks_passed','raw_sha256':build.digest(build.output('fine_overhead_raw.glb')),
            'preview_sha256':build.digest(build.output('fine_overhead_preview.glb')),'static_raw_rig_mesh_skin_unchanged':True,
            'formal_current_png_mesh_materials_weapon_identical':True,'raw_guard_entry_exit_max_component_error':close_error,'raw_guard_entry_exit_source_float32_values_identical':True,
            'native_right_fingers_max_component_error':right_error,'raw_right_finger_constant_max_float32_component_variation':right_constant_component_error,
            'raw_guard_endpoint_track_max_float32_component_error':endpoint_raw_component_error,'preview_once_baked_plus_formal_constant_root_shift_max_error':bake_error,
            'actual_shoe_sole_plane_error_metres':sole_error,'actual_shoe_surface_centre_max_motion_metres':foot_slip,
            'maximum_bone_length_change_metres':bone_error,'carrier_links_excluded_from_bone_length_test':['Armature→BoneRoot','BoneRoot→Hip'],'maximum_world_rotation_step_degrees_at_120hz':world_steps,
            'maximum_local_rotation_step_degrees_at_120hz':local_steps,'invalid_input_cases_rejected':failures,
            'true_contact_sample':contact,'blade_motion':measurements,
            'intentional_world_arm_reorientation_max_component_delta_from_native':native_world_error,'active_native_wrist_local_max_component_error':native_wrist_local_error,
            'steel_body_surface_scan':collision_rows,
            'steel_body_surface_overlap_sample_count':sum(bool(r['actual_steel_body_triangle_overlaps']) for r in collision_rows),
            'additional_source_pins':{str(p.relative_to(build.REPO)):build.digest(p) for p in [build.PRODUCER/'refine_character_grips.py',build.HERE.parent/'run_blender.py',Path(__file__)]},
            'collision_scan_scope':'0–1.75s full clip at60Hz',
            'limits':'Triangle overlap is sampled at60Hz in declared collision_scan_scope, may miss intersample collision and does not measure cloth volume. Aesthetics require independent rendered review. Contact at output1.0 uses native2.117; actual z=.90 intersections reported, not assumed.'}
    build.write('fine_overhead_verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('blade_motion','steel_body_surface_scan')},indent=2))

if __name__=='__main__':main()
