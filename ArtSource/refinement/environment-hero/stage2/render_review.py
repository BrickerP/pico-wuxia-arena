"""One Blender process, same cameras/lighting/opponent for both actual GLBs."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import traceback

import bpy
from mathutils import Vector

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ROOT=BASE.parents[2]
SOURCE=BASE/'courtyard_hero.glb'
CANDIDATE=HERE/'courtyard_materials_stage2.glb'
CHARACTER=ROOT/'app/src/main/assets/models/opponents/base.glb'
VIEWS={
 'player':((0,1.6,0),(0,1.7,-5.4),18),
 'explore':((1.5,1.6,-.4),(4.1,1.55,-3.1),18),
 'paper_3m':((-2.47,1.6,-2.42),(-2.47,1.65,-5.42),25),
 'paper_1p5m':((-2.47,1.6,-3.92),(-2.47,1.65,-5.42),25),
 'paper_0p8m':((-2.47,1.6,-4.62),(-2.47,1.65,-5.42),25),
 'lantern_joinery':((-2.15,1.6,-2.9),(-2.15,2.5,-4.9),22),
}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def point(p):return Vector((p[0],-p[2],p[1]))

def import_opponent():
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.import_scene.gltf(filepath=str(CHARACTER))
    imported=list(bpy.context.selected_objects)
    parent=bpy.data.objects.new('Review same frozen opponent',None);bpy.context.scene.collection.objects.link(parent)
    for o in imported:
        if o.parent is None:o.parent=parent
        data=o.animation_data
        if not data:continue
        data.action=None
        for track in data.nla_tracks:
            selected='attack_overhead' in track.name
            track.mute=not selected
            if selected:
                for strip in track.strips:
                    strip.frame_start=strip.action_frame_start
    parent.location=point((0,.028,-2.4))
    bpy.context.scene.frame_set(0)

def light(name,typ,p,color,energy,size,target=None):
    data=bpy.data.lights.new(name,typ);data.energy=energy;data.color=color
    if typ=='AREA':data.size=size
    else:data.shadow_soft_size=size
    o=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(o);o.location=point(p)
    if target:o.rotation_euler=(point(target)-o.location).to_track_quat('-Z','Y').to_euler()

def setup(recipe):
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.render.resolution_x=1200;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.world=bpy.data.worlds.new('Controlled '+recipe);scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.065,.09,.12,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.28 if recipe=='neutral' else .085
    light('fixed cool soft key','AREA',(-2,7,-1.5),(.63,.78,1),950 if recipe=='neutral' else 210,7,(0,1,-4))
    light('fixed opponent fill','AREA',(-.4,2.4,.5),(1,.91,.82),550 if recipe=='neutral' else 320,3,(0,1.2,-2.4))
    light('fixed neutral court fill','AREA',(3.5,4,-3),(.80,.88,1),400 if recipe=='neutral' else 80,4,(0,1.5,-5))
    for i,p in enumerate([(-2.15,2.7,-4.7),(2.15,2.7,-4.7),(-4.03,2.25,.56),(4.03,2.25,-1.32)]):
        light(f'fixed lamp {i}','POINT',p,(1,.49,.20),24 if i<2 else 18,.16)
    data=bpy.data.cameras.new('Same normal eye');data.clip_start=.03;data.sensor_width=36
    cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam);scene.camera=cam
    return scene,cam

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--recipe',choices=['neutral','night'],default='neutral')
    parser.add_argument('--views',nargs='*',default=list(VIEWS));args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    manifest=json.loads((HERE/'candidate_manifest.json').read_text())
    assert sha(SOURCE)==manifest['source_sha256'];assert sha(CANDIDATE)==manifest['sha256']
    outputs={}
    for phase,path in [('before',SOURCE),('after',CANDIDATE)]:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(path))
        import_opponent();scene,cam=setup(args.recipe)
        for name in args.views:
            position,target,lens=VIEWS[name]
            cam.location=point(position);cam.rotation_euler=(point(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
            output=HERE/'review'/f'{args.recipe}_{phase}_{name}.png'
            scene.render.filepath=str(output);bpy.ops.render.render(write_still=True);outputs[output.name]=sha(output)
    evidence={'kind':'actual GLB import, controlled offline comparison; not PICO screenshot',
       'recipe':args.recipe,'source_sha256':sha(SOURCE),'candidate_sha256':sha(CANDIDATE),
       'character_path':str(CHARACTER.relative_to(ROOT)),'character_sha256':sha(CHARACTER),
       'character_pose':'attack_overhead at source 0.0s; stage (0,.028,-2.4)',
       'camera_stage_m':{k:VIEWS[k] for k in args.views},'eye_height_m':1.6,
       'lighting_equal':True,'native_point_color_reference':[1,.49,.20],
       'lighting_caveat':'Blender watts are an offline comparison recipe, not a conversion claim for PICO lumens',
       'images':outputs}
    (HERE/'review'/f'{args.recipe}_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('STAGE2_REVIEW_COMPLETE',args.recipe,manifest['sha256'])

if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.exit(1)
