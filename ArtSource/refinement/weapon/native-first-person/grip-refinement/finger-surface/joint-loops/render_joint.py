"""Source/48e camera-identical joint-loop review; only new candidate is rendered."""
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;NATIVE=HERE.parents[2];REPO=HERE.parents[6];OUT=HERE/'renders';PREVIOUS=HERE.parent/'renders/render_manifest.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,name):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 import bpy
 from mathutils import Matrix,Vector
 previous=json.loads(PREVIOUS.read_text());delta=json.loads((HERE/'joint_delta.json').read_text());decode=json.loads((HERE/'decode_manifest.json').read_text());assert delta['candidate_sha256']==decode['candidate_sha256']==sha(HERE/'right_hand_joint.glb')
 common=load(NATIVE/'render_hands.py','hand_renderer');scene,camera=common.STUDIO.setup_scene(1200,24);scene.render.resolution_y=900;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
 camera.data.type='PERSP';camera.data.lens=60;camera.data.sensor_width=36;camera.data.clip_start=.005
 light=bpy.data.lights.new('Source fixed dorsal fill','AREA');light.shape='DISK';light.energy=45;light.size=.65;obj=bpy.data.objects.new('Source fixed dorsal fill',light);scene.collection.objects.link(obj);obj.location=(0.,-.25,-.60);obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
 root,rigs=common.import_at(HERE/'right_hand_joint_decoded.glb','Joint_candidate',(0,0,0));root.matrix_world=Matrix.Identity(4);original={item:list(item.data.materials) for item in root.children_recursive if item.type=='MESH'}
 gray=bpy.data.materials.new('Neutral geometry review');gray.use_nodes=True;node=gray.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(.36,.39,.42,1.);node.inputs['Roughness'].default_value=.72
 report={'status':'rendering','candidate_sha256':delta['candidate_sha256'],'source_sha256':delta['source_sha256'],'comparison_48e_sha256':previous['candidate_sha256'],'source_comparison_manifest_sha256':sha(PREVIOUS),'source_fixed_cameras':previous['source_fixed_cameras'],'images':[],'distance_m':.3,'limits':'Offline actual GLB and decoded unchanged KTX; not native/continuous/performance acceptance.'};OUT.mkdir(exist_ok=True)
 for pose,time in [('open',0.),('mid',.5),('closed',1.)]:
  common.pose(rigs,scene,time);row=previous['source_fixed_cameras'][pose];mat=Matrix(row['matrix_world']);camera.location=mat.to_translation();camera.rotation_euler=mat.to_euler();bpy.context.view_layer.update()
  for material in ['original','neutral']:
   for item,mats in original.items():
    item.data.materials.clear()
    for m in mats:item.data.materials.append(gray if material=='neutral' else m)
   path=OUT/f'{pose}_{material}_joint_0.3m.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   report['images'].append({'path':str(path.relative_to(REPO)),'pose':pose,'pose_seconds':time,'material':material,'sha256':sha(path),'camera_matrix':[list(row) for row in camera.matrix_world],'source_camera_matrix':row['matrix_world'],'asset_sha256':sha(HERE/'right_hand_joint_decoded.glb')});(OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('JOINT_RENDER',path.name,flush=True)
 report['status']='six_matched_actual_joint_renders_complete';(OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
