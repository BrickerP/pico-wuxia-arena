"""Bind reviewed outputs to exact source, candidate and construction identities."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(BASE));from verify_environment import read
sys.path.insert(0,str(BASE/'facade-polish'));from build_facade import budget

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size}

def main():
    target=HERE/'courtyard_native_entrance.glb';source=BASE/'facade-polish/courtyard_facade_polish.glb'
    v=json.loads((HERE/'review/verification.json').read_text())
    g=json.loads((HERE/'review/gltf-validator.json').read_text())
    r=json.loads((HERE/'review/render_manifest.json').read_text())
    module=json.loads((HERE/'review/module_audit.json').read_text())
    assert v['status']=='passed' and v['sha256']==sha(target)
    assert g['issues']['numErrors']==0 and g['candidateValidation']['inputSha256']==sha(target)
    assert r['same_actor_camera_lighting'] and r['phases']['before']['environment_sha256']==sha(source)
    assert r['phases']['after']['environment_sha256']==sha(target)
    assert module['input']['sha256']==sha(HERE/'entrance_module.glb')
    for phase in r['phases'].values():
        for name,digest in phase['images'].items():assert sha(HERE/'review'/name)==digest
    files=['build_entrance_module.py','build_candidate.py','verify_entrance.py','render_entrance.py','finalize_delivery.py','entrance_editable.blend','entrance_module.glb','courtyard_native_entrance.glb','optional_blocker_bounds.json','REBUILD.md','audit.json','review/verification.json','review/module_audit.json','review/gltf-validator.json','review/render_manifest.json','review/eye_before.png','review/eye_after.png','review/close_after.png']
    deps=[BASE/'method-study-2026-11-12/build_window_sample.py',BASE/'single-window-integration-2026-11-12/build_courtyard.py',BASE/'stage2/create_candidate.py',BASE/'verify_environment.py',BASE/'facade-polish/build_facade.py',BASE/'stage2/render_review.py']
    a,ab=read(source);b,bb=read(target)
    result={'status':'offline_candidate_for_root_native_review','input':item(source),'candidate':item(target),'budget_before':budget(a,ab),'budget_after':budget(b,bb),'files':[item(HERE/p) for p in files],'existing_readonly_dependencies':[item(p) for p in deps],'runtime_changes':[],'preserved':['nine facade windows','all existing node transforms','Stage origin and ground Y=0','ground receivers and anchors','combat clearance','32 materials and 50 exact image payloads'],'replaced':['closed double doors and handles','rebated doorway case','narrow sloped threshold','two stone post bases with sockets','two solid under-eave supports','local obstructing low beam and buried approach steps'],'limitations':['Offline Blender images are not native PICO Emulator evidence.','No runtime collider, navigation or door interaction is installed.','Closed visual doors remain closed; passability is unverified.','Space Pro performance, runtime tangent appearance and APK integration are Root-owned and unverified by this delivery.']}
    (HERE/'delivery_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'candidate':result['candidate'],'budget':result['budget_after']},indent=2))

if __name__=='__main__':main()
