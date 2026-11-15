"""Inspect individual evaluated neck faces using Root's actual prepared poses.

Run in Blender background mode; this tool NEVER renders or edits an asset.
`python3 probe_neck_faces.py --list-only` validates provenance and lists jobs
without importing Blender. Root owns executing the real evaluated probe.
"""

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFAULT_SOURCE = HERE / 'prepared/base.glb'
DEFAULT_MANIFEST = HERE / 'posed-review/render_manifest.json'
COLLAPSE_RATIO = .01


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def area_metrics(points):
    a, b, c = points
    u = tuple(b[i]-a[i] for i in range(3))
    v = tuple(c[i]-a[i] for i in range(3))
    cross = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    size = math.sqrt(sum(x*x for x in cross))
    area = size/2
    edges = [math.dist(a,b), math.dist(b,c), math.dist(c,a)]
    quality = 4*math.sqrt(3)*area/sum(x*x for x in edges) if any(edges) else 0
    return {'area_m2': area, 'area_mm2': area*1e6,
            'edge_lengths_metres': edges, 'edge_lengths_mm': [x*1000 for x in edges],
            'normalized_triangle_quality': quality,
            'maximum_edge_to_minimum_edge': max(edges)/min(edges) if min(edges)>0 else None,
            'normal': [x/size for x in cross] if size>0 else None}


def jobs_from_manifest(manifest, clips=None, seconds=None):
    flagged = [row for row in manifest.get('probe', []) if row.get('seam') and
               (row['seam'].get('collapsed_faces', 0)>0 or row['seam'].get('minimum_area_ratio',1)<COLLAPSE_RATIO)]
    if clips and seconds:
        return [(clip, second) for clip in clips for second in sorted(set(seconds))], flagged
    selected = set(clips or [row['clip'] for row in flagged])
    if not selected:
        raise ValueError('No flagged probe: provide --clips and --seconds explicitly')
    jobs = set()
    for row in manifest.get('probe', []):
        if row['clip'] in selected:
            jobs.add((row['clip'], float(row['seconds'])))
    for row in flagged:
        if row['clip'] not in selected:
            continue
        for offset in (-1/30,-1/60,-.01,0,.01,1/60,1/30):
            jobs.add((row['clip'], round(max(0,float(row['seconds'])+offset),9)))
    return sorted(jobs), flagged


def prepared_bridge(path):
    """Read actual GLB primitive order for reproducible loft triangle IDs."""
    sys.path.insert(0, str(HERE.parent))
    import graft_head as glb
    document,binary = glb.read_glb(path)
    matches=[]
    for mesh_index,mesh in enumerate(document['meshes']):
        for primitive_index,primitive in enumerate(mesh['primitives']):
            material=document['materials'][primitive['material']]
            if not material.get('name','').startswith('tripo_neck_continuous'):
                continue
            positions,faces=glb.triangles(document,binary,primitive)
            uv=glb.accessor_rows(document,binary,primitive['attributes']['TEXCOORD_0'])
            matches.append({'mesh':mesh_index,'primitive':primitive_index,'positions':positions,
                            'faces':faces,'uv':uv,'material':material['name']})
    if len(matches)!=1:
        raise ValueError('Expected exactly one prepared continuous-neck primitive')
    return matches[0]


def primitive_region(raw, face_id):
    face=raw['faces'][face_id]
    points=[raw['positions'][i] for i in face]
    coords=[raw['uv'][i] for i in face]
    centroid=[sum(p[i]for p in points)/3 for i in range(3)]
    v=sum(p[1]for p in coords)/3
    return {'prepared_gltf_mesh':raw['mesh'],'prepared_gltf_primitive':raw['primitive'],
            'loft_triangle_index':face_id,'prepared_gltf_vertex_ids':face,
            'raw_positions_gltf':points,'raw_centroid_gltf':centroid,'atlas_uv':coords,
            'loft_band_index':min(3,int(v*4)),
            'loft_band_v_range':[min(p[1]for p in coords),max(p[1]for p in coords)],
            'anatomical_region':('front' if centroid[0]>0 else 'posterior')+
                                 (' / raw -Z side' if centroid[2]<0 else ' / raw +Z side')}


def source_weights(obj, indices):
    return [{obj.vertex_groups[group.group].name:group.weight
             for group in obj.data.vertices[index].groups if group.weight>0} for index in indices]


def transported_normal(obj, armature, indices, rest_normal):
    """Reference normal transported by the mean local LBS affine transform.

    This removes ordinary whole-head rotation from the flip diagnostic. Bone
    weight gradients are deliberately NOT included: a mismatch can expose a
    local fold caused by varying weights, but requires adjacent-face evidence.
    """
    from mathutils import Matrix, Vector
    weights={}
    for row in source_weights(obj,indices):
        for name,weight in row.items():weights[name]=weights.get(name,0)+weight/3
    result=Matrix(((0.,0.,0.),(0.,0.,0.),(0.,0.,0.)))
    for name,weight in weights.items():
        pose=armature.pose.bones.get(name)
        if pose is None:
            raise ValueError('Missing actual pose bone '+name)
        world=armature.matrix_world @ pose.matrix @ pose.bone.matrix_local.inverted() @ armature.matrix_world.inverted()
        linear=world.to_3x3()
        for row in range(3):
            for column in range(3):result[row][column]+=weight*linear[row][column]
    determinant=result.determinant()
    if abs(determinant)<1e-10:
        return None,determinant,weights
    normal=result.inverted().transposed()@Vector(rest_normal)
    return list(normal.normalized()),determinant,weights


def configure_camera(camera,row):
    from mathutils import Vector
    camera.location=row['camera']
    target=Vector(row['target'])
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='PERSP' if row['view'].startswith('normal') else 'ORTHO'
    if camera.data.type=='PERSP':
        camera.data.sensor_fit='HORIZONTAL'
        camera.data.angle=math.radians(row['scale_or_fov'])
    else:camera.data.ortho_scale=row['scale_or_fov']


def screen_region(scene,camera,world_points,obj,polygon_index):
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    import bpy
    coords=[world_to_camera_view(scene,camera,point)for point in world_points]
    width=scene.render.resolution_x*scene.render.resolution_percentage/100
    height=scene.render.resolution_y*scene.render.resolution_percentage/100
    pixels=[(value.x*width,(1-value.y)*height)for value in coords]
    area=abs((pixels[1][0]-pixels[0][0])*(pixels[2][1]-pixels[0][1])-
             (pixels[2][0]-pixels[0][0])*(pixels[1][1]-pixels[0][1]))/2
    centroid=sum(world_points,Vector())/3
    normal=(world_points[1]-world_points[0]).cross(world_points[2]-world_points[0])
    facing=normal.dot(camera.location-centroid)
    if camera.data.type=='ORTHO':
        local=camera.matrix_world.inverted()@centroid
        origin=camera.matrix_world@Vector((local.x,local.y,0))
        direction=camera.matrix_world.to_quaternion()@Vector((0,0,-1))
        distance=(centroid-origin).dot(direction)
        facing=normal.dot(-direction)
    else:
        origin=camera.location.copy();delta=centroid-origin;distance=delta.length;direction=delta.normalized()
    occlusion={'tested':False}
    if distance>0:
        hit,location,hit_normal,face,hit_obj,matrix=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),origin,direction,distance=max(0,distance-1e-5))
        occlusion={'tested':True,'centroid_occluded_before_target':bool(hit),
                   'first_hit_object':hit_obj.name if hit else None,
                   'first_hit_polygon':face if hit else None,
                   'first_hit_distance_metres':(location-origin).length if hit else None}
    return {'pixel_origin':'top-left','projected_vertices_px':[list(p)for p in pixels],
            'bbox_px':[[min(p[i]for p in pixels)for i in range(2)],
                       [max(p[i]for p in pixels)for i in range(2)]],
            'projected_area_px2':area,'equivalent_disc_diameter_px':math.sqrt(4*area/math.pi),
            'all_vertices_in_front':all(c.z>0 for c in coords),
            'inside_viewport_vertices':sum(c.z>0 and 0<=c.x<=1 and 0<=c.y<=1for c in coords),
            'front_facing_geometric_normal':facing>0,'front_facing_dot_unnormalized':facing,
            'occlusion':occlusion}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    parser.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST)
    parser.add_argument('--output',type=Path,default=HERE/'probe_neck_faces.json')
    parser.add_argument('--clips',nargs='+')
    parser.add_argument('--seconds',type=float,nargs='+')
    parser.add_argument('--top',type=int,default=5,help='Include this many worst faces per sampled pose')
    parser.add_argument('--list-only',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--'in sys.argv else sys.argv[1:])
    if args.top<1 or args.top>30:parser.error('--top must be1..30')
    if args.seconds and not args.clips:parser.error('--seconds requires explicit --clips')
    if args.source.resolve()==args.output.resolve() or args.manifest.resolve()==args.output.resolve():parser.error('Keep probe inputs immutable')
    manifest=json.loads(args.manifest.read_text());jobs,flagged=jobs_from_manifest(manifest,args.clips,args.seconds)
    source=args.source.resolve();sha=digest(source)
    matching=[row for row in manifest['images']if row['stage']=='after'and(ROOT/row['source']).resolve()==source]
    if not matching or any(row['source_sha256']!=sha for row in matching):raise ValueError('Prepared actor does not match actual pose manifest')
    raw=prepared_bridge(source)
    metadata={'source':str(source),'source_sha256':sha,'manifest':str(args.manifest.resolve()),
              'manifest_sha256':digest(args.manifest),'flagged_manifest_probes':flagged,
              'jobs':[{'clip':clip,'seconds':seconds}for clip,seconds in jobs],
              'bridge_primitive':{key:raw[key]for key in('mesh','primitive','material')},
              'bridge_triangle_count':len(raw['faces']),'collapse_area_ratio_threshold':COLLAPSE_RATIO}
    if args.list_only:
        print(json.dumps({'probe_not_executed':True,**metadata},indent=2));return
    import bpy
    from mathutils import Vector
    renderer=load('actual_neck_probe_renderer',HERE/'render_posed_neck.py')
    studio=load('actual_neck_probe_studio',ROOT/'ArtSource/refinement/grip/render_grip_candidates.py')
    poses=load('actual_neck_probe_poses',ROOT/'ArtSource/refinement/hand-poses/render_hand_poses.py')
    scene,camera=studio.setup_scene(manifest['size'],manifest['cycles_samples'])
    scene.render.fps=manifest['fps']
    bpy.ops.import_scene.gltf(filepath=str(source))
    armatures=[obj for obj in scene.objects if obj.type=='ARMATURE']
    if len(armatures)!=1:raise ValueError('Expected actual prepared actor armature')
    armature=armatures[0];reference=renderer.seam_reference(scene)
    if reference is None:raise ValueError('Actual prepared bridge missing')
    obj,seams,faces,rest_areas=reference
    if len(faces)!=len(raw['faces']):raise ValueError('Imported bridge face count differs from prepared glTF')
    material_indices={i for i,m in enumerate(obj.data.materials)if m and m.name.startswith('tripo_neck_continuous')}
    polygon_ids=[polygon.index for polygon in obj.data.polygons if polygon.material_index in material_indices]
    needed={i for face in faces for i in face}|{i for group in seams for i in group}
    rest={i:obj.matrix_world@obj.data.vertices[i].co for i in needed}
    rest_details=[area_metrics([tuple(rest[i])for i in face])for face in faces]
    raw_details=[area_metrics([raw['positions'][i]for i in face])for face in raw['faces']]
    edge_pairs=[(posed['edge_lengths_metres'][j],raw['edge_lengths_metres'][j])
                for posed,raw in zip(rest_details,raw_details)for j in range(3)]
    ratios_order=[world/local for world,local in edge_pairs if local>2e-4]
    rest_scale=sorted(ratios_order)[len(ratios_order)//2]
    order_error=max(abs(world/local-rest_scale)/rest_scale for world,local in edge_pairs if local>1e-12)
    order_absolute_error=max(abs(world-local*rest_scale)for world,local in edge_pairs)
    if order_absolute_error>2e-6:raise ValueError('Imported bridge triangle order/rest edge identity differs from prepared glTF')
    profiles_path=source.parent/'base_attack_profiles.json'
    markers = {}
    if profiles_path.exists():
        for attack in json.loads(profiles_path.read_text())['attacks'].values():
            phases = dict(zip(('start','preparation_end','startup_end','active_end','recovery_end'), attack['source_phase_seconds']))
            phases['contact'] = attack['contact_source_seconds']
            markers[attack['clip']] = phases
    neighbors={};edge_faces={}
    for face_id,face in enumerate(faces):
        for a,b in zip(face,face[1:]+face[:1]):
            ka=struct.pack('<3f',*obj.data.vertices[a].co);kb=struct.pack('<3f',*obj.data.vertices[b].co)
            edge_faces.setdefault(tuple(sorted((ka,kb))),[]).append(face_id)
    for rows in edge_faces.values():
        for face_id in rows:neighbors.setdefault(face_id,set()).update(i for i in rows if i!=face_id)
    # First locate all actual degenerate faces, then track those SAME IDs at
    # guard/start, contact and recovery even when not worst-ranked there.
    tracked=set();first_pass=[]
    for clip,seconds in jobs:
        poses.select_pose(scene,clip,seconds)
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        try:
            current={i:evaluated.matrix_world@mesh.vertices[i].co for face in faces for i in face}
            areas=[(current[b]-current[a]).cross(current[c]-current[a]).length/2 for a,b,c in faces]
            ratios=[area/rest for area,rest in zip(areas,rest_areas)]
            collapsed=[i for i,ratio in enumerate(ratios)if ratio<COLLAPSE_RATIO]
            tracked.update(collapsed);first_pass.append({'clip':clip,'seconds':seconds,'minimum_area_ratio':min(ratios),'collapsed_face_ids':collapsed})
        finally:evaluated.to_mesh_clear()
    samples=[];problem_faces=set()
    for clip,seconds in jobs:
        owners=poses.select_pose(scene,clip,seconds)
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
        try:
            if len(mesh.vertices)!=len(obj.data.vertices):raise ValueError('Actual modifier changed bridge vertex mapping')
            points={i:evaluated.matrix_world@mesh.vertices[i].co for i in rest}
            metrics=[area_metrics([tuple(points[i])for i in face])for face in faces]
            ratios=[metric['area_m2']/rest_areas[i]for i,metric in enumerate(metrics)]
            collapsed=[i for i,ratio in enumerate(ratios)if ratio<COLLAPSE_RATIO]
            worst=sorted(range(len(faces)),key=lambda i:ratios[i])[:args.top]
            include=sorted(set(collapsed+worst+list(tracked)));problem_faces.update(collapsed)
            camera_rows=[]
            for view in ('oblique','normal','normal_1.5','normal_3'):
                row=next((row for row in matching if row['clip']==clip and row['view']==view),None)
                if row:camera_rows.append(row)
            records=[]
            for face_id in include:
                face=faces[face_id];metric=metrics[face_id];normal=metric['normal']
                transported,determinant,bone_weights=transported_normal(obj,armature,face,rest_details[face_id]['normal'])
                neighbor_normals=[metrics[i]['normal']for i in neighbors.get(face_id,[])if metrics[i]['normal']and ratios[i]>=COLLAPSE_RATIO]
                nearby=unit_vector([sum(row[a]for row in neighbor_normals)for a in range(3)])if neighbor_normals else None
                record={**primitive_region(raw,face_id),'blender_object':obj.name,'blender_vertex_ids':list(face),
                    'blender_polygon_index':polygon_ids[face_id],'rest':rest_details[face_id],
                    'posed':metric,'area_ratio':ratios[face_id],'collapsed_by_manifest_rule':face_id in collapsed,
                    'rest_world_positions':[list(rest[i])for i in face],
                    'posed_world_positions':[list(points[i])for i in face],
                    'source_vertex_bone_weights':source_weights(obj,face),
                    'centroid_bone_weights':bone_weights,'mean_skin_affine_determinant':determinant,
                    'transported_reference_normal':transported,
                    'posed_normal_dot_transported_reference':dot(normal,transported),
                    'posed_normal_dot_noncollapsed_neighbor_mean':dot(normal,nearby),
                    'neighbor_triangle_indices':sorted(neighbors.get(face_id,[])),
                    'screen_regions':[]}
                for row in camera_rows:
                    configure_camera(camera,row);bpy.context.view_layer.update()
                    record['screen_regions'].append({'view':row['view'],'camera_reference_source_seconds':row['seconds'],
                        'camera_reference_image':row['file'],**screen_region(scene,camera,[points[i]for i in face],obj,polygon_ids[face_id])})
                records.append(record)
            gap=max((points[i]-points[group[0]]).length for group in seams for i in group)
            samples.append({'clip':clip,'seconds':seconds,'source_phase':phase_label(seconds,markers[clip])if clip.startswith('attack_')else None,'actual_nla_owners':owners,
                'minimum_area_ratio':min(ratios),'collapsed_face_ids':collapsed,'maximum_seam_gap_metres':gap,
                'faces':records})
            print('NECK_FACE_PROBE',clip,seconds,'minimum',min(ratios),'collapsed',collapsed,flush=True)
        finally:evaluated.to_mesh_clear()
    if digest(source)!=sha:raise ValueError('Prepared actor changed during probe')
    output={**metadata,'blender_version':bpy.app.version_string,'probe_executed':True,
        'status':'evaluated_problem_faces_pending_Root_review','source_assets_modified':False,'renders_produced':0,
        'normal_reference_note':'Dot to mean-affine transported rest normal removes ordinary bone rotation; neighbor mean provides a separate local fold cue. Neither alone proves visibility.',
        'screen_note':'Frozen per-clip cameras from actual image manifest; reference image may be1.0s while probe samples another actual source time. Centroid ray test is approximate visibility evidence, not a rendered proof.',
        'gltf_imported_face_order_rest_edge_relative_error':order_error,'gltf_imported_face_order_rest_edge_absolute_error_metres':order_absolute_error,'rest_world_uniform_scale_from_raw_gltf':rest_scale,
        'phase_markers_seconds':markers,'profiles_source':str(profiles_path)if profiles_path.exists()else None,
        'tracked_problem_face_ids_at_every_pose':sorted(tracked),'first_pass':first_pass,
        'unique_collapsed_loft_triangle_ids':sorted(problem_faces),'samples':samples}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(args.output),'samples':len(samples),'problem_face_ids':sorted(problem_faces),'source_sha256':sha}))



def phase_label(seconds,markers):
    if not markers:return 'not declared'
    contact=markers.get('contact')
    if contact is not None and abs(seconds-contact)<1e-7:return 'contact'
    if seconds<markers.get('preparation_end',float('-inf')):return 'preparation'
    if seconds<markers.get('startup_end',float('-inf')):return 'startup'
    if seconds<=markers.get('active_end',float('-inf')):return 'active'
    if seconds<=markers.get('recovery_end',float('-inf')):return 'recovery'
    return 'outside declared source phases'


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))if a is not None and b is not None else None


def unit_vector(value):
    norm=math.sqrt(sum(v*v for v in value))
    return [v/norm for v in value]if norm>1e-15 else None


if __name__=='__main__':main()
