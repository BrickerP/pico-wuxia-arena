"""Generate and run the existing complete JVM suite against this private bank."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
from validate_typed import HERE, REPO, GENERATOR, build_private_fixture, sha256, validate_bank, require

SOURCE = REPO / 'ArtSource/refinement/combat-direction/run_isolated_tests.py'
OUT = HERE / 'typed-validation'
BANK = HERE / 'candidate-library'
RUNTIME = REPO / 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime'
TEST_SOURCE = REPO / 'app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/AttackBankProfilesTest.kt'


def main():
    require(len(sys.argv) == 1, 'Run the complete existing suite without focus or test filters')
    OUT.mkdir(exist_ok=True)
    typed = OUT / 'AttackBankProfileData.kt'
    for arguments, log_name in [([], 'generate.txt'), (['--check'], 'generate-check.txt')]:
        result = subprocess.run([sys.executable, str(GENERATOR), '--bank', str(BANK), '--output', str(typed), *arguments],
                                cwd=REPO, text=True, capture_output=True)
        (OUT / log_name).write_text(result.stdout + result.stderr)
        print(result.stdout + result.stderr, end='')
        if result.returncode:
            return result.returncode
    checks = validate_bank(BANK, typed)
    (OUT / 'python-validation.json').write_text(json.dumps(checks, indent=2) + '\n')

    formal = json.loads((REPO / 'ArtSource/tripo-warrior/library/production_review_request.json').read_text())
    candidate = json.loads((BANK / 'production_review_request.json').read_text())
    original = TEST_SOURCE.read_text()
    fixture_content, replacements = build_private_fixture(original, formal, candidate)
    fixture = OUT / TEST_SOURCE.name
    fixture.write_text(fixture_content)
    spec = importlib.util.spec_from_file_location('combined_existing_isolated_jvm', SOURCE)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.OUT = OUT
    original_run = subprocess.run
    compile_inputs = {}
    executed_test_classes = []
    # Delete only this run's generated classes, preventing stale compilation output.
    if (OUT / 'classes').exists():
        shutil.rmtree(OUT / 'classes')

    def private_run(command, *args, **kwargs):
        nonlocal compile_inputs, executed_test_classes
        if 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler' in command:
            require(command.count(str(RUNTIME / 'AttackBankProfileData.kt')) == 1,
                    'Existing runner must compile exactly one published typed source')
            require(command.count(str(TEST_SOURCE)) == 1, 'Existing runner must compile the original attack-bank tests')
            command = [str(typed) if str(arg) == str(RUNTIME / 'AttackBankProfileData.kt')
                       else str(fixture) if str(arg) == str(TEST_SOURCE) else arg for arg in command]
            reaction_source = str(RUNTIME / 'ReactionProfiles.kt')
            if reaction_source not in command:
                command.append(reaction_source)
            compile_inputs = {str(Path(arg).relative_to(REPO)): sha256(Path(arg))
                              for arg in command if str(arg).endswith('.kt')}
            (OUT / 'compiled-sources.json').write_text(json.dumps(compile_inputs, indent=2) + '\n')
        if 'org.junit.runner.JUnitCore' in command:
            executed_test_classes = command[command.index('org.junit.runner.JUnitCore') + 1:]
            require(executed_test_classes and any('.core.' in name for name in executed_test_classes),
                    'Complete existing core and runtime suites must run')
        return original_run(command, *args, **kwargs)

    runner.subprocess.run = private_run
    try:
        result = runner.main()
    finally:
        runner.subprocess.run = original_run
    changed_inputs = [path for path, identity in compile_inputs.items() if sha256(REPO / path) != identity]
    require(not changed_inputs, 'Compiled sources changed during validation: ' + ', '.join(changed_inputs))
    junit_path = OUT / 'junit-all-core.txt'
    junit = junit_path.read_text() if junit_path.exists() else ''
    match = re.search(r'^OK \((\d+) tests\)$', junit, re.MULTILINE)
    if result == 0:
        require(match is not None, 'JVM runner succeeded without a complete JUnit result')
        require(int(match.group(1)) >= 179, 'Existing 179-test suite must not be reduced')
    receipt = {
        **checks, 'source_runner': str(SOURCE.relative_to(REPO)),
        'source_runner_sha256': sha256(SOURCE),
        'source_test_sha256': hashlib_sha(original), 'private_test_sha256': sha256(fixture),
        'identity_replacements': replacements,
        'sample_assertion_change': 'Only veteran/LEFT=130; all OVERHEAD=211; all other lateral=106',
        'original_test_methods_preserved': True, 'existing_test_filters_applied': False,
        'additional_existing_source': 'ReactionProfiles.kt if absent from the current runner',
        'compiled_source_count': len(compile_inputs), 'compiled_sources_unchanged': True,
        'test_class_count': len(executed_test_classes),
        'jvm_test_count': int(match.group(1)) if match else None,
        'app_sources_modified': False, 'formal_bank_modified': False,
        'gradle_used': False, 'exit_code': result,
    }
    (OUT / 'candidate_fixture.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return result


def hashlib_sha(content):
    import hashlib
    return hashlib.sha256(content.encode()).hexdigest()


if __name__ == '__main__':
    sys.exit(main())
