"""Source-fixed0.3m actual finger GLBs, open/mid/closed original and neutral pairs."""
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
NATIVE=HERE.parents[1];REPO=HERE.parents[5];OUT=HERE/'renders'
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import bpy,numpy as np
 from mathutils import Vector,Matrix
 common=load(NATIVE/'render_hands.py','actual_hand_renderer')
 delta=json.loads((HERE/'finger_delta.json').read_text());decode=json.loads((HERE/'decode_manifest.json').read_text())
 source_ktx=HERE.parent/'palm-wrist-surface/production-patch/anatomical-crease/right_hand_patch.glb'
 source=source_ktx.with_name('right_hand_patch_decoded.glb');candidate=HERE/'right_hand_finger_decoded.glb'
 assert sha(HERE/'right_hand_finger.glb')==delta['candidate_sha256']==decode['candidate_sha256']
 guides=json.loads((HERE/'render_guides.json').read_text())
 paths=[source_ktx,HERE/'render_guides.json',source,candidate,HERE/'right_hand_finger.glb',HERE/'finger_delta.json',HERE/'decode_manifest.json',HERE/'build_finger.py',HERE/'make_companion.py',Path(__file__),NATIVE/'render_hands.py']
 pins={str(p.relative_to(REPO)):sha(p) for p in paths}
 scene,camera=common.STUDIO.setup_scene(1200,24);scene.render.resolution_y=900
 scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU'
 scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0
 camera.data.type='PERSP';camera.data.lens=60;camera.data.sensor_width=36;camera.data.clip_start=.005
 # Existing neutral source review fill, applied identically to source/candidate.
 light=bpy.data.lights.new('Source fixed dorsal fill','AREA');light.shape='DISK';light.energy=45;light.size=.65
 obj=bpy.data.objects.new('Source fixed dorsal fill',light);scene.collection.objects.link(obj)
 obj.location=(0.,-.25,-.60);obj.rotation_euler=(Vector((0,0,0))-obj.location).to_track_quat('-Z','Y').to_euler()
 roots={};rigs={};originals={}
 for label,path in [('before',source),('after',candidate)]:
  root,rig=common.import_at(path,'Finger_'+label,(0,0,0));root.matrix_world=Matrix.Identity(4);roots[label]=root;rigs[label]=rig
  for item in root.children_recursive:
   if item.type=='MESH':originals[item]=list(item.data.materials)
 gray=bpy.data.materials.new('Neutral geometry review');gray.use_nodes=True
 node=gray.node_tree.nodes.get('Principled BSDF');node.inputs['Base Color'].default_value=(.36,.39,.42,1.);node.inputs['Roughness'].default_value=.72
 def blender(v):return Vector((v[0],-v[2],v[1]))
 report={'status':'rendering','source_sha256':delta['source_sha256'],'candidate_sha256':delta['candidate_sha256'],'source_pins':pins,'images':[],'source_fixed_cameras':{},'distance_m':.3,'lighting':'repository source studio and unchanged45W source dorsal fill, same exposure/materials for both stages','limits':'Offline actualGLB and actualKTX decoded pixels, not native device/SDK evidence.'}
 OUT.mkdir(exist_ok=True)
 previous_path=HERE/'before-normal-repair/renders/render_manifest.json'
 previous=json.loads(previous_path.read_text()) if previous_path.exists() else None
 report['reused_before_source_manifest_sha256']=sha(previous_path) if previous else None
 for pose,time in [('open',0.),('mid',.5),('closed',1.)]:
  for label in roots:common.pose(rigs[label],scene,time)
  guide=guides[pose]
  center=blender(guide['center_canonical_m']);direction=blender(guide['direction_canonical']).normalized()
  camera.location=center+.3*direction;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
  bpy.context.view_layer.update();matrix=[list(row) for row in camera.matrix_world]
  report['source_fixed_cameras'][pose]={'center_blender':list(center),'matrix_world':matrix,'distance_m':.3,'lens_mm':60,'type':'PERSP','source_vertex_ids':guide['source_vertex_ids']}
  for material in ['original','neutral']:
   for label in ['before','after']:
    for stage,root in roots.items():
     for item in [root,*root.children_recursive]:item.hide_render=stage!=label
    for item,materials in originals.items():
     item.data.materials.clear()
     for mat in materials:item.data.materials.append(gray if material=='neutral' else mat)
    path=OUT/f'{pose}_{material}_{label}_0.3m.png'
    reused=label=='before' and previous is not None
    if reused:
     prior=next(row for row in previous['images'] if row['pose']==pose and row['material']==material and row['stage']=='before')
     assert prior['camera_matrix']==matrix and prior['asset_sha256']==sha(source) and prior['sha256']==sha(path),'Before source/camera/image differs'
    else:
     scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    report['images'].append({'path':str(path.relative_to(REPO)),'sha256':sha(path),'stage':label,'material':material,'pose_seconds':time,'pose':pose,'camera_matrix':matrix,'asset_sha256':sha(source if label=='before' else candidate),'reused_verified_before_image':reused})
    (OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('FINGER_RENDER',path.name,flush=True)
 for p,pin in pins.items():assert sha(REPO/p)==pin,p
 report['status']='twelve_matched_actual_renders_complete';(OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
