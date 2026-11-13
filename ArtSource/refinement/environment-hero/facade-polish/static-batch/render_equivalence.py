"""At most one existing camera pair; static environment only, not game QA."""
from pathlib import Path
import hashlib
import json
import sys
import traceback

import bpy
from mathutils import Vector

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent.parent
sys.path.insert(0,str(BASE/'stage2'));import render_review as lighting
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    m=json.loads((HERE/'candidate_manifest.json').read_text());source=HERE.parent/'courtyard_facade_polish.glb';candidate=HERE/m['candidate']
    assert sha(source)==m['source_sha256'] and sha(candidate)==m['sha256']
    outputs={};eye=Vector((0,0,1.6));target=Vector((0,5.4,1.65))
    for phase,path in [('before',source),('after',candidate)]:
        bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
        scene,camera=lighting.setup('night');camera.location=eye;camera.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler()
        camera.data.lens=18;camera.data.dof.use_dof=False
        output=HERE/'review'/f'{phase}_static_environment.png';scene.render.filepath=str(output);bpy.ops.render.render(write_still=True);outputs[output.name]=sha(output)
    e={'kind':'one actual GLB equivalence camera pair, offline, not native APK proof','source_sha256':sha(source),'candidate_sha256':sha(candidate),
       'camera_stage_m':[0,1.6,0],'target_stage_m':[0,1.65,-5.4],'lens_mm':18,'same_lighting':True,'dof':False,
       'scope':'environment only; NPC/player hands/blade are separate APK resources and were not inserted into either review frame',
       'images':outputs}
    (HERE/'review/render_evidence.json').write_text(json.dumps(e,indent=2)+'\n');print('STATIC_EQUIVALENCE_PAIR_COMPLETE',m['sha256'])
if __name__=='__main__':
    try:main()
    except BaseException:traceback.print_exc();sys.exit(1)
