"""Bind the wet-stone review packet to exact source, maps, KTX and render evidence."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}
def main():
    source=ROOT/'ArtSource/refinement/environment-hero/native-fight-entrance/courtyard_native_entrance.glb';png=HERE/'courtyard_wet_stone_png.glb';ktx=HERE/'courtyard_wet_stone_ktx.glb'
    original=json.loads((HERE/'delivery_manifest.json').read_text())['original_authoring_execution']
    checks=json.loads((HERE/'review/verification.json').read_text());gate=json.loads((HERE/'review/visual_gate.json').read_text());render=json.loads((HERE/'review/render_manifest.json').read_text());prov=json.loads((HERE/'texture_provenance.json').read_text())
    assert checks['status']=='passed' and checks['source_sha256']==sha(source)
    assert checks['png_candidate_sha256']==sha(png) and checks['ktx_candidate_sha256']==sha(ktx)
    assert render['same_actor_camera_lighting'] and render['phases']['before']['environment_sha256']==sha(source) and render['phases']['after']['environment_sha256']==sha(png)
    for phase in render['phases'].values():
        for name,digest in phase['images'].items():assert sha(HERE/'review'/name)==digest
    files=['build_wet_stone.py','verify_wet_stone.py','render_wet_stone.py','finalize_delivery.py','courtyard_wet_stone_png.glb','courtyard_wet_stone_ktx.glb','texture_provenance.json','REBUILD.md','textures/wet_stone_basecolor_1024.png','textures/wet_stone_metallic_roughness_1024.png','review/verification.json','review/png_gltf_validator.json','review/ktx_gltf_validator.json','review/render_manifest.json','review/visual_gate.json','review/eye_before.png','review/eye_after.png','review/close_before.png','review/close_after.png']
    deps=[ROOT/'ArtSource/refinement/environment-hero/verify_environment.py',ROOT/'ArtSource/refinement/environment-hero/facade-polish/build_facade.py',ROOT/'ArtSource/refinement/pbr-compression/compress_pbr.py',ROOT/'ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs',ROOT/'ArtSource/tavern/README.md']
    result={'status':gate['status'],'adoption_recommendation':gate['adoption_recommendation'],'input':item(source),'png_review_scene':item(png),'ktx_private_candidate':item(ktx),'budget':checks['budget'],'generated_image_count':2,'generated_maps':prov['generated_images'],'license':prov['license'],'compression':{'settings':prov['compression']['settings'],'encoder':prov['compression']['encoder']},'visual_gate':gate,'files':[item(HERE/f) for f in files],'existing_dependencies':[item(p) for p in deps],'runtime_changes':[],'limitations':['PNG review is not PICO KTX loading proof.','No native light or IBL change was made; reflection remains an explicit native dependency.','No collision, path, performance, Space Pro, device or APK claim. Root owns formal integration, build, device and Git.']}
    assert original['delivery_manifest']['png_review_scene']['sha256']==sha(png)
    assert original['delivery_manifest']['ktx_private_candidate']['sha256']==sha(ktx)
    for entry in original['delivery_manifest']['files']:
        if entry['path'].lower().endswith('.png'):assert sha(ROOT/entry['path'])==entry['sha256']
    result['original_authoring_execution']=original
    result['maintenance']={'purpose':'Repair authoring-input reachability after downstream runtime promotion; not new material art.',
      'authoring_input':item(source),'build_execution':prov['build_execution'],'verification_execution':checks['execution'],
      'private_rebuild':prov['maintenance_rebuild'],
      'sealer_code':item(Path(__file__)),'render_rerun':False,'original_images_and_assets_byte_identical':True,
      'historical_actor_authoring_source':'ArtSource/refinement/combat-direction/native-weighted-overhead/integration/candidate-library-v5; exact original6649/f6 pair, no runtime input or exclusion fallback',
      'visual_gate_scope':'Original offline images and original review decision retained. Current code file hashes are maintenance identities, not a claim that images were rerendered.'}
    actor=ROOT/'ArtSource/refinement/combat-direction/native-weighted-overhead/integration/candidate-library-v5'
    result['maintenance']['render_reproduction_inputs']=[item(actor/name) for name in
      ['base_prepared_png.glb','base.glb','base_texture_encoding.json','base_alignment.json']]+[
      item(HERE.parent/'render_ground.py'),item(ROOT/'ArtSource/refinement/environment-hero/stage2/render_review.py'),
      item(ROOT/'ArtSource/refinement/presentation/native-grip-motion-2026-11-15.json')]
    (HERE/'delivery_manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'status':result['status'],'ktx':result['ktx_private_candidate'],'budget':result['budget']},indent=2))
if __name__=='__main__':main()
