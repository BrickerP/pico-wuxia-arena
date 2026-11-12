"""Dry-run/apply the private diff only in a temporary fixture of its five touched input files."""
from pathlib import Path
import hashlib,json,subprocess,tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
lock=json.loads((HERE/'source_lock.json').read_text())
patch=HERE/'01-local-native-impact.patch'
inputs=lock['input_source_sha256']
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==s for p,s in inputs.items()), 'Locked source drift; rebase candidate explicitly.'
with tempfile.TemporaryDirectory(prefix='patch-fixture-',dir=HERE)as d:
 stage=Path(d)
 for p in lock['candidate_sha256']:
  src=ROOT/p
  if src.exists():
   out=stage/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(src.read_bytes())
 dry=subprocess.run(['patch','-E','--dry-run','-p1','-i',str(patch.resolve())],cwd=stage,text=True,capture_output=True)
 assert dry.returncode==0,dry.stdout+dry.stderr
 applied=subprocess.run(['patch','-E','-p1','-i',str(patch.resolve())],cwd=stage,text=True,capture_output=True)
 assert applied.returncode==0,applied.stdout+applied.stderr
 for p,s in lock['candidate_sha256'].items():
  f=stage/p
  if s is None:assert not f.exists(),p
  else:assert f.exists()and hashlib.sha256(f.read_bytes()).hexdigest()==s,p
 home=(stage/'app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt').read_text()
 assert 'EnemyHitFlash' not in home and 'seenImpactLights.add(it.id)' in home
 assert 'remainingNativeImpactLightNanos' in home and 'pulseUntil = now + remaining' in home
 preserved=['CombatEffects.kt','ContactParticleEmitter.kt','SoftContactEnvelope.kt','ContactParticleMotion.kt','ContactParticlePresets.kt']
 for name in preserved:
  path='app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/'+name
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==inputs[path]
 result={'dry_run_exit_code':dry.returncode,'isolated_apply_exit_code':applied.returncode,'candidate_hashes_match':True,
         'app_sources_unchanged':all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==s for p,s in inputs.items()),
         'shared_gradle_run':False,'device_run':False,'git_run':False,
         'limits':'Only isolated patch consistency and source preservation; HomeStage SDK compilation and actual pixels remain Root checks.',
         'dry_run_output':dry.stdout,'apply_output':applied.stdout}
 assert result['app_sources_unchanged']
 (HERE/'patch_check.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items()if not k.endswith('_output')},indent=2))
