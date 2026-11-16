"""Original-material close views of this actual canonical three-target bank."""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('clearance_review_tools',HERE / 'review_candidate.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
r = c.r


def main():
    import bpy
    from mathutils import Vector
    out = HERE / 'local-review'
    out.mkdir(exist_ok=True)
    pins = {str(p.relative_to(c.REPO)):r.sha(p) for p in [Path(__file__),HERE / 'review_candidate.py',
        Path(r.STUDIO.__file__),Path(r.DIRECT.__file__)]}
    eye,aim = Vector((.78,1.47,1.40)),Vector((.20,1.31,.14))
    cv = lambda v:Vector((v[0],-v[2],v[1]))
    result = {'binding_sha256':json.loads((c.BANK / 'production_review_request.json').read_bytes())['binding_sha256'],
        'source_pins':pins,'original_material':True,'geometry_override':False,'frames':[],
        'scope':'Offline original-material actual canonical target; no PICO or continuous-time claim'}
    for target in c.family.TARGETS:
        path = c.BANK / (target+'_prepared_png.glb')
        pin = r.sha(path)
        scene,camera = r.STUDIO.setup_scene(640,8)
        scene.render.resolution_y = 640
        scene.render.threads_mode,scene.render.threads = 'FIXED',2
        scene.cycles.device = 'CPU'
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()),disable_bone_shape=True)
        camera.data.type,camera.data.lens,camera.data.sensor_width,camera.data.clip_start = 'PERSP',65,36,.005
        camera.location = cv(eye)
        camera.rotation_euler = (cv(aim)-camera.location).to_track_quat('-Z','Y').to_euler()
        for t in [1.,1.15,1.25]:
            action = r.DIRECT.select_action(scene,'attack_right',t)
            bpy.context.view_layer.update()
            output = out / f'{target}_RIGHT_{round(t*1000):04d}.png'
            scene.render.filepath = str(output.resolve())
            bpy.ops.render.render(write_still=True)
            result['frames'].append({'path':str(output.relative_to(c.REPO)),'sha256':r.sha(output),
                'target':target,'source_seconds':t,'actual_model_sha256':pin,'actual_action':action,
                'camera_eye_actor_m':list(eye),'camera_aim_actor_m':list(aim),
                'camera_matrix_blender':[list(row) for row in camera.matrix_world]})
            r.save(out / 'render_manifest.json',result)
            print('LOCAL_RENDER',target,t,flush=True)
        r.require(r.sha(path)==pin,'model changed during render')
    for path,pin in pins.items():
        r.require(r.sha(c.REPO/path)==pin,'render helper changed')


if __name__ == '__main__':
    main()
