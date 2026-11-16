"""Preview the refined module against the PNG-equivalent wet-stone scene only."""
from pathlib import Path
import hashlib,importlib.util,json,sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
FORMAL=ROOT/'app/src/main/assets/models/courtyard_hero.glb';FORMAL_SHA='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667'
PNG=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';PNG_SHA='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('old_lantern_renderer',HERE.parent/'render_lantern.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.HERE=HERE;module.OUT=HERE/'review';module.SOURCE=PNG;module.MODULE=HERE/'lantern_refined_module.glb';module.EXPECTED=PNG_SHA
if __name__=='__main__':
    if sha(FORMAL)!=FORMAL_SHA or sha(PNG)!=PNG_SHA:raise SystemExit('formal or PNG-equivalent identity changed')
    module.main()
    phase=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else ''
    path=HERE/'review'/f'render_manifest_{phase}.json';data=json.loads(path.read_text());data['formal_source_sha256']=FORMAL_SHA;data['preview_source_png_equivalent_sha256']=PNG_SHA;data['preview_source_note']='Blender cannot import formal KHR_texture_basisu; this preview uses its verified PNG-equivalent scene and does not test KTX loading.';path.write_text(json.dumps(data,indent=2)+'\n')
    combined=HERE/'review'/'render_manifest.json';payload=json.loads(combined.read_text());payload['formal_source_sha256']=FORMAL_SHA;payload['preview_source_png_equivalent_sha256']=PNG_SHA;payload['preview_source_note']=data['preview_source_note'];combined.write_text(json.dumps(payload,indent=2)+'\n')
