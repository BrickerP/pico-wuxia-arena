"""Matched original/neutral actual GLB renders at source-fixed 0.3m cameras."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[7]
NATIVE=HERE.parents[3]
OUT=HERE/'renders'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import bpy
    from mathutils import Matrix,Vector
    s=importlib.util.spec_from_file_location('actual_hand_renderer',NATIVE/'render_hands.py')
    common=importlib.util.module_from_spec(s);s.loader.exec_module(common)
    delta=json.loads((HERE/'patch_delta.json').read_text())
    source=HERE.parents[2]/'right_hand_refined_v2_decoded.glb'
    candidate=HERE/'right_hand_patch_decoded.glb'
    decode=json.loads((HERE/'decode_manifest.json').read_text())
    assert sha(HERE/'right_hand_patch.glb')==delta['candidate_sha256']==decode['candidate_sha256']
    paths=[source,candidate,HERE/'right_hand_patch.glb',HERE/'patch_delta.json',HERE/'decode_manifest.json',
           HERE/'build_anatomical.py',HERE/'make_companion.py',Path(__file__),NATIVE/'render_hands.py']
    pins={str(p.relative_to(REPO)):sha(p) for p in paths}
    OUT.mkdir(exist_ok=True)
    scene,camera=common.STUDIO.setup_scene(1000,16)
    scene.render.resolution_y=750
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU'
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
    camera.data.type='PERSP';camera.data.lens=45;camera.data.sensor_width=36;camera.data.clip_start=.005
    # Same neutral fill used by the accepted source dorsal review; no after-only lighting.
    light=bpy.data.lights.new('Source fixed dorsal fill','AREA');light.shape='DISK';light.energy=45;light.size=.65
    obj=bpy.data.objects.new('Source fixed dorsal fill',light);scene.collection.objects.link(obj)
    obj.location=(0.,-.25,-.60);obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
    roots={};original_materials={}
    for label,path in [('before',source),('after',candidate)]:
        root,rigs=common.import_at(path,'Production_patch_'+label,(0,0,0));root.matrix_world=Matrix.Identity(4)
        common.pose(rigs,scene,1.);roots[label]=root
        for item in root.children_recursive:
            if item.type=='MESH':original_materials[item]=list(item.data.materials)
    gray=bpy.data.materials.new('Neutral geometry review');gray.use_nodes=True
    node=gray.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(.36,.39,.42,1.)
    node.inputs['Roughness'].default_value=.72
    def blender(v):return Vector((v[0],-v[2],v[1]))
    report={'status':'rendering','candidate_sha256':delta['candidate_sha256'],'source_sha256':delta['source_sha256'],
            'source_pins':pins,'source_fixed_cameras':{},'images':[],
            'lighting':[{'name':o.name,'matrix_world':[list(row) for row in o.matrix_world],
                         'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size}
                        for o in scene.objects if o.type=='LIGHT'],
            'limits':'Offline Blender GLBs, actual decoded KTX pixels and actual skeleton; not PICO or continuous clearance.'}
    for view in ['dorsal']:
        guide=delta['render_guides'][view]
        center=blender(guide['center_canonical_m']);normal=blender(guide['outward_canonical_unit']).normalized()
        camera.location=center+.3*normal
        camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update()
        matrix=[list(row) for row in camera.matrix_world]
        assert camera.data.type=='PERSP' and abs((camera.location-center).length-.3)<1e-6
        report['source_fixed_cameras'][view]={'center_blender':list(center),'distance_m':.3,'matrix_world':matrix,'lens_mm':45,'type':camera.data.type}
        for material in ['original','neutral']:
            for label in ['before','after']:
                for stage,root in roots.items():
                    for item in [root,*root.children_recursive]:item.hide_render=stage!=label
                for item,materials in original_materials.items():
                    item.data.materials.clear()
                    for mat in materials:item.data.materials.append(gray if material=='neutral' else mat)
                bpy.context.view_layer.update()
                path=OUT/(view+'_'+material+'_'+label+'.png');scene.render.filepath=str(path)
                bpy.ops.render.render(write_still=True)
                report['images'].append({'path':str(path.relative_to(REPO)),'sha256':sha(path),'stage':label,
                    'material':material,'view':view,'pose_seconds':1.,'camera_matrix':matrix,
                    'asset_sha256':sha(source if label=='before' else candidate)})
                (OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
                print('PATCH_RENDER',path.name,flush=True)
    for path,pin in pins.items():assert sha(REPO/path)==pin,path
    report['status']='four_matched_actual_renders_complete'
    (OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
