"""Original-material veteran LEFT arm/chest close views of the actual new bank."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('combined_render_tools',HERE/'review_combined.py')
c=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
r=c.r


def main():
    import bpy
    from mathutils import Vector
    out=HERE/'local-review'
    out.mkdir(exist_ok=True)
    path=c.BANK/'veteran_prepared_png.glb'
    paths=[Path(__file__),HERE/'review_combined.py',Path(r.STUDIO.__file__),Path(r.DIRECT.__file__),path,c.BANK/'production_review_request.json']
    pins={str(p.relative_to(c.REPO)):r.sha(p) for p in paths}
    eye,aim=Vector((-.78,1.47,1.4)),Vector((-.20,1.31,.14))
    cv=lambda v:Vector((v[0],-v[2],v[1]))
    scene,camera=r.STUDIO.setup_scene(640,8)
    scene.render.resolution_y=640
    scene.render.threads_mode,scene.render.threads='FIXED',2
    scene.cycles.device='CPU'
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()),disable_bone_shape=True)
    camera.data.type,camera.data.lens,camera.data.sensor_width,camera.data.clip_start='PERSP',65,36,.005
    camera.location=cv(eye)
    camera.rotation_euler=(cv(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
    report={'binding_sha256':json.loads((c.BANK/'production_review_request.json').read_bytes())['binding_sha256'],
        'source_pins':pins,'frames':[],'original_material':True,'geometry_or_pose_override':False,
        'scope':'Offline original-material constrained actual veteran; no native SDK playback or aesthetics approval'}
    for clip,time,label in [('idle',0.,'guard'),('attack_left',1.1,'LEFT_1p1'),('attack_left',1.2,'LEFT_1p2'),('attack_left',1.75,'LEFT_return')]:
        action=r.DIRECT.select_action(scene,clip,time)
        bpy.context.view_layer.update()
        output=out/f'veteran_{label}.png'
        scene.render.filepath=str(output)
        bpy.ops.render.render(write_still=True)
        report['frames'].append({'path':str(output.relative_to(c.REPO)),'sha256':r.sha(output),
            'actual_model_sha256':pins[str(path.relative_to(c.REPO))],'clip':clip,'source_seconds':time,
            'actual_action':action,'camera_eye_actor_m':list(eye),'camera_aim_actor_m':list(aim),
            'camera_matrix_blender':[list(row) for row in camera.matrix_world]})
        r.save(out/'render_manifest.json',report)
        print('COMBINED_LOCAL_RENDER',clip,time,flush=True)
    for p,pin in pins.items():r.require(r.sha(c.REPO/p)==pin,'render input drift: '+p)


if __name__=='__main__':main()
