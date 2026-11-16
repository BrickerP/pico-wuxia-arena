from pathlib import Path
import hashlib,importlib.util,json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[6]
FORMAL=ROOT/'app/src/main/assets/models/courtyard_hero.glb';FORMAL_SHA='bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667';PNG=ROOT/'ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb';PNG_SHA='5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('lantern_renderer',HERE.parents[1]/'render_lantern.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=HERE;m.OUT=HERE/'review';m.SOURCE=PNG;m.MODULE=HERE/'lantern_surface_module.glb';m.EXPECTED=PNG_SHA
if __name__=='__main__':
 if sha(FORMAL)!=FORMAL_SHA or sha(PNG)!=PNG_SHA:raise SystemExit('formal/PNG source identity changed')
 m.main();phase=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else '';path=HERE/'review'/f'render_manifest_{phase}.json';d=json.loads(path.read_text());d['formal_source_sha256']=FORMAL_SHA;d['preview_source_png_equivalent_sha256']=PNG_SHA;d['preview_source_note']='PNG equivalent required because Blender does not import formal KHR_texture_basisu.';path.write_text(json.dumps(d,indent=2)+'\n');combined=HERE/'review'/'render_manifest.json';d=json.loads(combined.read_text());d['formal_source_sha256']=FORMAL_SHA;d['preview_source_png_equivalent_sha256']=PNG_SHA;d['preview_source_note']='PNG equivalent required because Blender does not import formal KHR_texture_basisu.';combined.write_text(json.dumps(d,indent=2)+'\n')
