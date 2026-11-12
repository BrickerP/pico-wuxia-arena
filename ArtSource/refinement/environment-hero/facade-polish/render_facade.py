"""Two controlled views of the actual full-scene resources, one Blender process."""
from pathlib import Path
import hashlib
import json
import sys
import traceback

import bpy
from mathutils import Vector

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE/'stage2'));import render_review as lighting
SOURCE=BASE/'single-window-integration-2026-11-12/courtyard_one_window.glb'
ACTOR=ROOT/'ArtSource/tripo-warrior/library/base_prepared_png.glb'
FORMAL=ROOT/'app/src/main/assets/models/opponents/base.glb'
ACTOR_SHA='b3fbfe66727d0dd90bd741420937a6c57dbb9e083d76ecd983cd9383ab5bbf96'
FORMAL_SHA='ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20'
VIEWS={'facade':((0,1.6,0),(0,1.65,-5.4),18),
       'near_1p5m':((2.47,1.6,-3.92),(2.47,1.65,-5.42),25)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pt(p):return Vector((p[0],-p[2],p[1]))
def actor():
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.import_scene.gltf(filepath=str(ACTOR))
    root=bpy.data.objects.new('Current clean-coat guard',None);bpy.context.scene.collection.objects.link(root);count=0
    for o in list(bpy.context.selected_objects):
        if o.parent is None:o.parent=root
        data=o.animation_data
        if data:
            data.action=None
            for track in data.nla_tracks:
                chosen=track.name.split('.')[0]=='idle';track.mute=not chosen
                if chosen:
                    count+=1
                    for strip in track.strips:strip.frame_start=strip.action_frame_start
    if not count:raise ValueError('Current idle guard track missing')
    root.location=pt((0,.028,-2.4));bpy.context.scene.frame_set(0)
def main():
    m=json.loads((HERE/'candidate_manifest.json').read_text());candidate=HERE/m['candidate']
    assert sha(candidate)==m['sha256'];assert sha(SOURCE)==m['source_sha256']
    assert sha(ACTOR)==ACTOR_SHA and sha(FORMAL)==FORMAL_SHA
    outputs={}
    for phase,path in [('before',SOURCE),('after',candidate)]:
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));actor()
        scene,cam=lighting.setup('night')
        for view,(position,target,lens) in VIEWS.items():
            cam.location=pt(position);cam.rotation_euler=(pt(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.dof.use_dof=False
            output=HERE/'review'/f'{phase}_{view}.png';scene.render.filepath=str(output);bpy.ops.render.render(write_still=True);outputs[output.name]=sha(output)
    assert sha(ACTOR)==ACTOR_SHA and sha(FORMAL)==FORMAL_SHA
    report={'kind':'actual full-scene GLB offline same-light comparison, not native PICO',
      'source_sha256':sha(SOURCE),'candidate_sha256':sha(candidate),'actor_png_sha256':ACTOR_SHA,'formal_actor_ktx_sha256':FORMAL_SHA,
      'guard':'idle@0 locked STEP, Stage(0,.028,-2.4)','views_stage_m':VIEWS,'same_lighting':True,'dof':False,
      'eye_note':'1.6m standard standing-eye review; not measured HMD pose','images':outputs}
    (HERE/'review/render_evidence.json').write_text(json.dumps(report,indent=2)+'\n');print('FACADE_REVIEW_COMPLETE',m['sha256'])
if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.exit(1)
