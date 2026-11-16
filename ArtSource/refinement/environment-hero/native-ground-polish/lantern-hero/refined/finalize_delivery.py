from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def main():
 formal=ROOT/'app/src/main/assets/models/courtyard_hero.glb';png=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';module=HERE/'lantern_refined_module.glb';check=json.loads((HERE/'review/verification.json').read_text());manifest=json.loads((HERE/'module_manifest.json').read_text());render=json.loads((HERE/'review/render_manifest.json').read_text());gate=json.loads((HERE/'review/visual_gate.json').read_text());gltf=json.loads((HERE/'review/module_gltf_validator.json').read_text())
 assert check['status']=='passed' and check['formal_source_sha256']==sha(formal) and check['module_sha256']==sha(module) and manifest['formal_source_sha256']==sha(formal) and manifest['blender_png_equivalent_sha256']==sha(png) and gltf['issues']['numErrors']==0 and render['same_actor_camera_lighting']
 for phase in render['phases'].values():
  for name,digest in phase['images'].items():assert sha(HERE/'review'/name)==digest
 files=['build_refined_lantern.py','verify_refined_lantern.py','render_refined_lantern.py','finalize_delivery.py','lantern_refined_module.glb','lantern_refined_editable.blend','module_manifest.json','REBUILD.md','review/verification.json','review/module_gltf_validator.json','review/render_manifest.json','review/visual_gate.json','review/eye_before.png','review/eye_after.png','review/close_before.png','review/close_after.png']
 deps=[ROOT/'ArtSource/refinement/environment-hero/verify_environment.py',ROOT/'ArtSource/refinement/environment-hero/facade-polish/build_facade.py',ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/render_lantern.py',png]
 out={'status':gate['status'],'adoption_recommendation':gate['adoption_recommendation'],'formal_input':item(formal),'blender_png_equivalent':item(png),'module':item(module),'instances':manifest['instances'],'budget':check,'visual_gate':gate,'files':[item(HERE/f) for f in files],'existing_dependencies':[item(p) for p in deps],'runtime_changes':[],'limitations':['Root has not composed this module into formal bd5d.','Offline PNG preview cannot prove KTX load or native lighting.','No device, performance, collision, navmesh, memory or Space Pro claim.']}
 (HERE/'delivery_manifest.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':out['status'],'module':out['module'],'preview_budget':check['preview_expanded_triangle_budget']},indent=2))
if __name__=='__main__':main()
