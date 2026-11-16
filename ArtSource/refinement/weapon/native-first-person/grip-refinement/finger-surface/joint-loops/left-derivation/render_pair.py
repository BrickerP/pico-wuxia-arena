"""Actual paired closed-grip Right/Left views using the established camera plan."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[7];NATIVE=HERE.parents[3];LEGACY=HERE.parents[2]/'left-rebuild';OUT=HERE/'renders';PLAN=HERE/'render_plan.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def preflight():
 old=load('frozen_pair_camera_plan',LEGACY/'render_left_rebuild.py');old.OUT=OUT;left=old.camera_plans();source=json.loads(old.CAMERAS.read_text());plans=[]
 for raw,l in zip(source['images'],left):
  plans.append({'side':'R','view':raw['view'],'file':str((OUT/('right_closed_'+raw['view']+'.png')).relative_to(REPO)),'camera_blender_metres':raw['camera_blender_metres'],'camera_target_blender_metres':raw['camera_target_blender_metres'],'lens_mm':raw['lens_mm'],'grip_seconds':1.})
  plans.append({**l,'side':'L'})
 inputs=[HERE.parent/'right_hand_joint.glb',HERE.parent/'right_hand_joint_decoded.glb',HERE/'left_hand_joint.glb',HERE/'left_hand_joint_decoded.glb',HERE/'decode_manifest.json',old.DAO,old.DAO_DECODED,old.DAO_MANIFEST,old.CAMERAS,old.COMMON,old.STUDIO,LEGACY/'render_left_rebuild.py',Path(__file__)]
 assert sha(old.DAO)==old.DAO_SHA and sha(old.DAO_DECODED)==old.DAO_DECODED_SHA and sha(old.DAO_MANIFEST)==old.DAO_MANIFEST_SHA
 construction=json.loads((HERE/'construction.json').read_text());assert sha(HERE.parent/'right_hand_joint.glb')==construction['source']['sha256']=='199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64';assert sha(HERE/'left_hand_joint.glb')==construction['candidate']['sha256']
 report={'status':'preflight_passed','source_right_sha256':construction['source']['sha256'],'left_sha256':construction['candidate']['sha256'],'plans':plans,'source_camera_manifest':str(old.CAMERAS.relative_to(REPO)),'camera_rule':'Existing source3-camera plans; Left camera/target X reflect only, actual Left GLB and actual unreflected DAO both at identity commonGrip','FILL':old.FILL,'input_pins':{str(p.relative_to(REPO)):sha(p) for p in inputs},'dao_decoded':str(old.DAO_DECODED.relative_to(REPO)),'images':[],'hand_and_dao_runtime_negative_scale':False,'lighting_changed_from_frozen_review':False};PLAN.write_text(json.dumps(report,indent=2)+'\n');print('PAIRED_RENDER_PREFLIGHT')

def render():
 import bpy
 from mathutils import Matrix,Vector
 report=json.loads(PLAN.read_text())
 def pins():
  for path,pin in report['input_pins'].items():assert sha(REPO/path)==pin,path
 pins();common=load('actual_pair_renderer',NATIVE/'render_hands.py');scene,camera=common.STUDIO.setup_scene(1200,24);scene.render.resolution_y=900;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.view_settings.view_transform='AgX';scene.view_settings.exposure=0;camera.data.type='PERSP';camera.data.clip_start=.005;camera.data.sensor_width=36
 fill=report['FILL'];data=bpy.data.lights.new(fill['name'],fill['type']);data.shape=fill['shape'];data.energy=fill['power_watts'];data.size=fill['size_metres'];data.color=fill['color_linear_rgb'];obj=bpy.data.objects.new(fill['name'],data);scene.collection.objects.link(obj);obj.location=fill['position_blender_metres'];obj.rotation_euler=(Vector(fill['target_blender_metres'])-obj.location).to_track_quat('-Z','Y').to_euler()
 roots={}
 for side,path in [('R',HERE.parent/'right_hand_joint_decoded.glb'),('L',HERE/'left_hand_joint_decoded.glb')]:
  root,rigs=common.import_at(path,'Actual_'+side+'_commonGrip',(0,0,0));root.matrix_world=Matrix.Identity(4);common.pose(rigs,scene,1.);roots[side]=root
 dao,_=common.import_at(REPO/report['dao_decoded'],'Actual_unreflected_dao_commonGrip',(0,0,0));dao.matrix_world=Matrix.Identity(4)
 report['status']='rendering';report['blender_version']=bpy.app.version_string;report['images']=[];OUT.mkdir(exist_ok=True)
 for plan in report['plans']:
  for side,root in roots.items():
   for item in [root,*root.children_recursive]:item.hide_render=side!=plan['side']
  camera.location=Vector(plan['camera_blender_metres']);camera.rotation_euler=(Vector(plan['camera_target_blender_metres'])-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=plan['lens_mm'];bpy.context.view_layer.update()
  assert roots[plan['side']].matrix_world==Matrix.Identity(4) and dao.matrix_world==Matrix.Identity(4)
  scene.render.filepath=str(REPO/plan['file']);bpy.ops.render.render(write_still=True);pins();report['images'].append({**plan,'sha256':sha(REPO/plan['file']),'camera_matrix_world':[list(row) for row in camera.matrix_world],'hand_root_matrix_world':[list(row) for row in roots[plan['side']].matrix_world],'dao_root_matrix_world':[list(row) for row in dao.matrix_world],'evaluated_hand_geometry':common.evaluated_geometry(roots[plan['side']])});(OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('PAIR_RENDER',plan['side'],plan['view'],flush=True)
 report['status']='six_actual_paired_closed_renders_complete';(OUT/'render_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
 if '--preflight' in args:preflight()
 else:render()
