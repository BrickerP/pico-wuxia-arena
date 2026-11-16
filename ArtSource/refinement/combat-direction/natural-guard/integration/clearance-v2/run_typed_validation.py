"""Reuse the isolated JVM runner with candidate typed data and identity fixture."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
SOURCE = REPO / 'ArtSource/refinement/combat-direction/run_isolated_tests.py'
spec = importlib.util.spec_from_file_location('existing_isolated_jvm',SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def main():
    out = HERE / 'typed-validation'
    out.mkdir(exist_ok=True)
    formal = json.loads((REPO / 'ArtSource/tripo-warrior/library/production_review_request.json').read_bytes())
    candidate = json.loads((HERE / 'candidate-library/production_review_request.json').read_bytes())
    test_source = REPO / 'app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/AttackBankProfilesTest.kt'
    content = test_source.read_text()
    replacements = {formal['binding_sha256']:candidate['binding_sha256']}
    for before,after in zip(formal['characters'],candidate['characters']):
        assert before['id']==after['id']
        replacements[before['attack_profiles_sha256']]=after['attack_profiles_sha256']
        replacements[next(o['sha256'] for o in before['outputs'] if o['file']==before['id']+'.glb')]=next(o['sha256'] for o in after['outputs'] if o['file']==after['id']+'.glb')
    for old,new in replacements.items():
        assert content.count(old)==1,'published identity fixture differs: '+old
        content=content.replace(old,new)
    fixture = out / test_source.name
    fixture.write_text(content)
    runner.OUT = out
    original_run = subprocess.run
    typed_source = REPO / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/AttackBankProfileData.kt'
    def private_compile(command,*args,**kwargs):
        if 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler' in command:
            command=[str(HERE / 'AttackBankProfileData.kt') if str(arg)==str(typed_source)
                     else str(fixture) if str(arg)==str(test_source) else arg for arg in command]
            # The older isolated runner predates this existing source split.
            command.append(str(REPO / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/ReactionProfiles.kt'))
        return original_run(command,*args,**kwargs)
    runner.subprocess.run = private_compile
    result = runner.main()
    (out / 'candidate_fixture.json').write_text(json.dumps({'binding_sha256':candidate['binding_sha256'],
        'source_runner':str(SOURCE.relative_to(REPO)), 'fixture_changes':'Only seven exact binding/model/profile SHA literals replaced; all original behavioral assertions preserved',
        'additional_existing_source':'ReactionProfiles.kt (omitted by old isolated runner)',
        'app_sources_modified':False,'gradle_used':False,'exit_code':result},indent=2)+'\n')
    return result


if __name__ == '__main__':
    sys.exit(main())
