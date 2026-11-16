"""Compile and replay the actor-only escape with the canonical isolated Kotlin/JUnit runner."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
FIXTURE=HERE.parent/'enemy-arm-prototype/fixture/recovery.csv'
WITNESS=HERE.parent/'failed-projection/contact-witness.json'
FIXTURE_SHA='67146106cfec0b0db55ad6ab51c0a32c735c0bc72f6eb507e98cf76151854976'
WITNESS_SHA='5ae7324c17f7c4303b7c621ec5ffd138a528b0b07479e4bc951a8134218f8524'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'result')
    args=parser.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if sha(FIXTURE)!=FIXTURE_SHA or sha(WITNESS)!=WITNESS_SHA:
        raise RuntimeError('Fixture or fixed player witness identity changed; do not silently replay another geometry')
    sources=[ROOT/'app/src/main/java/com/example/wuxiaarena/core/math/PoseMath.kt',
        ROOT/'app/src/main/java/com/example/wuxiaarena/core/math/SegmentGeometry.kt',
        ROOT/'app/src/main/java/com/example/wuxiaarena/core/combat/BladeContact.kt',
        HERE/'ActorWithdrawal.kt',HERE/'ActorWithdrawalFixtureTest.kt']
    identities={str(p.relative_to(ROOT)):sha(p) for p in sources}
    env=os.environ.copy();env['PICO_ACTOR_FIXTURE']=str(FIXTURE);env['PICO_ACTOR_RESULT']=str(out/'withdrawal.json')
    cmd=[sys.executable,str(ROOT/'ArtSource/refinement/effects/runtime-polish/testing/run_jvm_tests.py'),
        '--java',str(Path.home()/'.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java'),'--output',str(out)]
    for source in sources:cmd+=['--source',str(source)]
    cmd+=['--test','com.example.wuxiaarena.prototype.withdrawal.ActorWithdrawalFixtureTest']
    run=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
    (out/'run.txt').write_text(run.stdout+run.stderr)
    stable=all(sha(ROOT/p)==value for p,value in identities.items())
    (out/'run_result.json').write_text(json.dumps({'exit_code':run.returncode,'input_stable_during_run':stable,
        'sources':identities,'fixture_sha256':sha(FIXTURE),'witness_sha256':sha(WITNESS),'command':cmd,
        'pure_math_no_sdk':True},indent=2)+'\n')
    print(run.stdout+run.stderr,end='')
    if not stable:raise RuntimeError('Source identity changed while compiling/replaying; result is stale')
    return run.returncode
if __name__=='__main__':raise SystemExit(main())
