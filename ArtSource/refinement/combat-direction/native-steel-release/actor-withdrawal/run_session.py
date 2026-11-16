"""Run the affected coordinator/contact subset against live owned implementation."""
from pathlib import Path
import subprocess,zipfile,json,hashlib,argparse
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];CACHE=Path.home()/'.gradle/caches/modules-2/files-2.1'
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',default='session-result');args=parser.parse_args()
 out=HERE/args.output_dir;out.mkdir(exist_ok=True);src=ROOT/'app/src/main/java/com/example/wuxiaarena';tests=ROOT/'app/src/test/java/com/example/wuxiaarena'
 sources=sorted((src/'core').rglob('*.kt'))+[src/'p0d2f0182/runtime'/n for n in ['ArenaSession.kt','ArenaOpponents.kt','CombatFeedbackProfile.kt','AttackBankProfiles.kt','AttackBankProfileData.kt','LocomotionProfiles.kt','ReactionProfiles.kt']]+[src/'p0d2f0182/content/EnemyAnimator.kt']
 names=['core/combat/WeaponContactConstraintTest.kt','p0d2f0182/runtime/NativeEnemyMotionContactTest.kt','p0d2f0182/runtime/ActorSteelWithdrawalSessionTest.kt','p0d2f0182/runtime/ContactTimeWitnessTest.kt','p0d2f0182/runtime/WeaponContactOrderingTest.kt','p0d2f0182/runtime/CombatImpactEventTest.kt','p0d2f0182/runtime/ArenaSessionTest.kt','p0d2f0182/runtime/HurtPoseContinuityTest.kt']
 for name in ['p0d2f0182/runtime/SteelEpisodeLifecycleTest.kt','p0d2f0182/runtime/SteelRecoveryDomainTest.kt']:
  if (tests/name).exists():names.append(name)
 sources += [tests/name for name in names]
 cmd=['python3',str(ROOT/'ArtSource/refinement/effects/runtime-polish/testing/run_jvm_tests.py'),'--java',str(Path.home()/'.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java'),'--output',str(out)]
 for s in sources:cmd+=['--source',str(s)]
 for name in names:cmd+=['--test','com.example.wuxiaarena.'+name[:-3].replace('/','.')]
 cmd+=['--classpath',str(Path.home()/'Library/Android/sdk/platforms/android-35/android.jar')]
 for group,name in [('com.pico.spatial.core','core'),('com.pico.spatial.foundation','foundation')]:
  aar=next((CACHE/group/name/'6.1.9').glob('*/*.aar'));jar=out/(name+'.jar')
  with zipfile.ZipFile(aar) as z:jar.write_bytes(z.read('classes.jar'))
  cmd+=['--classpath',str(jar)]
 run=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=180);(out/'run.txt').write_text(run.stdout+run.stderr);print(run.stdout+run.stderr,end='');return run.returncode
if __name__=='__main__':raise SystemExit(main())
