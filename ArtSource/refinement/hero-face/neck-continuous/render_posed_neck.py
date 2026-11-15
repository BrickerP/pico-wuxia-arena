"""Compare actual prepared clips with Root's frozen camera and studio.

No rig, source, producer or formal library is changed. The pose helper is the
same one used by Root's integrated review. This also checks evaluated seams.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FROZEN=ROOT/'ArtSource/tripo-warrior/review/hero-face-integrated'
TIMES={'idle':1.,'walk':.8,'turn':.8,'attack_overhead':1.,'attack_left':1.,'attack_right':1.}


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seam_reference(scene):
    for obj in scene.objects:
        if obj.type!='MESH':continue
        bridge={i for i,m in enumerate(obj.data.materials) if m and m.name.startswith('tripo_neck_continuous')}
        if not bridge:continue
        used={};bridge_faces=[]
        for polygon in obj.data.polygons:
            for i in polygon.vertices:used.setdefault(i,set()).add(polygon.material_index)
            if polygon.material_index in bridge:bridge_faces.append(tuple(polygon.vertices))
        groups={}
        for i,mats in used.items():
            groups.setdefault(struct.pack('<3f',*obj.data.vertices[i].co),[]).append((i,mats))
        seams=[]
        for members in groups.values():
            mats=set().union(*(m for _,m in members))
            if mats&bridge and mats-bridge:seams.append([i for i,_ in members])
        rest=[obj.matrix_world@v.co for v in obj.data.vertices]
        areas=[(rest[b]-rest[a]).cross(rest[c]-rest[a]).length/2 for a,b,c in bridge_faces]
        if len(seams)<100 or min(areas)<=1e-14:raise ValueError('Missing or degenerate actual continuous-neck seam')
        return obj,seams,bridge_faces,areas
    return None


def measure(reference):
    if reference is None:return None
    obj,seams,faces,rest_areas=reference
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    try:
        if len(mesh.vertices)!=len(obj.data.vertices):raise ValueError('Unexpected modifier topology change')
        needed={i for group in seams for i in group}|{i for face in faces for i in face}
        points={i:evaluated.matrix_world@mesh.vertices[i].co for i in needed}
        gap=max((points[i]-points[group[0]]).length for group in seams for i in group)
        ratios=[((points[b]-points[a]).cross(points[c]-points[a]).length/2)/area
                for (a,b,c),area in zip(faces,rest_areas)]
        if gap>2e-6:raise ValueError(f'Actual posed seam opened: {gap} metres')
        return {'seam_groups':len(seams),'maximum_seam_gap_metres':gap,
                'bridge_triangles':len(faces),'minimum_area_ratio':min(ratios),
                'maximum_area_ratio':max(ratios),'collapsed_faces':sum(r<.01 for r in ratios)}
    finally:evaluated.to_mesh_clear()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clips',nargs='+',choices=list(TIMES),default=list(TIMES))
    parser.add_argument('--views',nargs='+',choices=['oblique','oblique_other','normal','normal_1.5','normal_3','rear_1.5','whole'],default=['oblique','normal'])
    parser.add_argument('--stage',choices=['before','after','both'],default='both')
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--at-start',action='store_true',help='Actual stationary guard holds each attack at its first source key')
    parser.add_argument('--output',type=Path,default=HERE/'posed-review')
    parser.add_argument('--seconds',type=float,help='One explicit source time for a finite stress-pose review')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    studio=load('continuous_studio',ROOT/'ArtSource/refinement/grip/render_grip_candidates.py')
    poses=load('continuous_poses',ROOT/'ArtSource/refinement/hand-poses/render_hand_poses.py')
    frozen_manifest=json.loads((FROZEN/'review/render_manifest.json').read_text())
    original=next(row for row in frozen_manifest['images'] if row['label']=='after' and row['clip']=='idle' and row['view']=='oblique')
    frozen_sha=original['sha256']
    before=FROZEN/'base.glb'
    if hashlib.sha256(before.read_bytes()).hexdigest()!=frozen_sha:raise ValueError('Frozen prepared actor drifted')
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    sources={'before':before,'after':HERE/'prepared/base.glb'}
    stages=list(sources) if args.stage=='both' else [args.stage]
    reference_cameras={};record={'scope':'actual prepared clips; Root same-pose studio/camera',
        'original_defect_image':'ArtSource/tripo-warrior/review/hero-face-integrated/review/after_idle_oblique.png',
        'fps':30,'size':768,'cycles_samples':8,'images':[],'probe':[]}
    # Derive all non-idle cameras from the frozen actor, never the new surface.
    for stage in (['before'] if args.stage=='after' else [])+stages:
        source=sources[stage];digest=hashlib.sha256(source.read_bytes()).hexdigest()
        scene,camera=studio.setup_scene(768,8);scene.render.threads_mode='FIXED';scene.render.threads=2
        for light in bpy.data.lights:light.color=(1,1,1)
        bpy.ops.mesh.primitive_plane_add(size=10,location=(0,0,-.029))
        bpy.ops.import_scene.gltf(filepath=str(source.resolve()))
        armature=next(obj for obj in scene.objects if obj.type=='ARMATURE')
        seam=seam_reference(scene)
        for clip in args.clips:
            seconds=0. if args.at_start and clip.startswith('attack_') else args.seconds if args.seconds is not None else TIMES[clip]
            poses.select_pose(scene,clip,seconds)
            target=armature.matrix_world@armature.pose.bones['Head'].matrix.translation+Vector((0,0,.035))
            for view in args.views:
                key=(clip,view)
                if stage=='before':
                    if clip=='idle' and view=='oblique':
                        position=Vector(original['camera_location']);aim=Vector(original['camera_target']);scale=original['camera_ortho_scale']
                    elif view=='whole':position,aim,scale=Vector((2.8,-6,2.7)),Vector((0,0,1.13)),3.5
                    elif view.startswith(('normal','rear')):
                        distance=.8 if view=='normal' else float(view.split('_')[1])
                        position,aim,scale=target+Vector((0,distance if view.startswith('rear') else -distance,0)),target,60.
                    else:position,aim,scale=target+Vector((-.85 if view=='oblique_other' else .85,-1.6,.05)),target,.58
                    reference_cameras[key]=(position,aim,scale)
                position,aim,scale=reference_cameras[key]
                camera.location=position;camera.rotation_euler=(aim-position).to_track_quat('-Z','Y').to_euler()
                camera.data.type='PERSP' if view.startswith(('normal','rear')) else 'ORTHO'
                if view.startswith(('normal','rear')):
                    import math
                    camera.data.sensor_fit='HORIZONTAL';camera.data.angle=math.radians(60)
                else:camera.data.ortho_scale=scale
                if args.stage=='after' and stage=='before':continue
                intent='guard_'+clip if args.at_start and clip.startswith('attack_') else clip
                name=f'{stage}_{intent}_{view}.png';scene.render.filepath=str(output/name)
                bpy.ops.render.render(write_still=True)
                record['images'].append({'source':str(source.relative_to(ROOT)),'source_sha256':digest,
                    'stage':stage,'intent':intent,'clip':clip,'seconds':seconds,'view':view,'file':name,
                    'camera':list(position),'target':list(aim),'scale_or_fov':scale,'seam':measure(seam)})
                (output/'render_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
        if args.probe and stage=='after':
            for clip in TIMES:
                samples=[0,.3,.65,.8,.9,1.,1.1,1.35,1.75] if clip.startswith('attack') else [0,.4,.8,1.,1.2]
                for seconds in samples:
                    poses.select_pose(scene,clip,seconds)
                    record['probe'].append({'clip':clip,'seconds':seconds,'seam':measure(seam)})
        if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:raise ValueError('Source changed while rendering')
    record['status']='complete_pending_visual_review'
    (output/'render_manifest.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__=='__main__':main()
