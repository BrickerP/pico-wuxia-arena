"""Compile the 09 combat integration tests without invoking the shared Gradle build."""
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

REPO = Path(__file__).resolve().parents[3]
CACHE = Path.home() / '.gradle/caches/modules-2/files-2.1'
OUT = REPO / 'artifacts/combat-direction/isolated-jvm'


def jar(package, version):
    return next((CACHE / package / version).glob('*/*.jar'))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    stdlib = jar('org.jetbrains.kotlin/kotlin-stdlib', '2.1.20')
    compiler_jars = [jar(p, v) for p, v in [
        ('org.jetbrains.kotlin/kotlin-compiler-embeddable', '2.1.20'),
        ('org.jetbrains.kotlin/kotlin-script-runtime', '2.1.20'),
        ('org.jetbrains.kotlin/kotlin-reflect', '1.6.10'),
        ('org.jetbrains.intellij.deps/trove4j', '1.0.20200330'),
        ('org.jetbrains.kotlinx/kotlinx-coroutines-core-jvm', '1.8.0'),
        ('org.jetbrains/annotations', '23.0.0'),
    ]] + [stdlib]
    junit = jar('junit/junit', '4.13.2')
    hamcrest = jar('org.hamcrest/hamcrest-core', '1.3')
    android_home = Path(os.environ.get('ANDROID_HOME', Path.home() / 'Library/Android/sdk'))
    android = android_home / 'platforms/android-35/android.jar'
    if not android.exists():
        raise SystemExit('Android 35 SDK jar is required for existing Android imports')
    source = REPO / 'app/src/main/java/com/example/wuxiaarena'
    sources = sorted((source / 'core').rglob('*.kt'))
    sources += [source / 'p0d2f0182/runtime' / name for name in [
        'ArenaSession.kt', 'ArenaOpponents.kt', 'CombatFeedbackProfile.kt',
        'AttackBankProfiles.kt', 'AttackBankProfileData.kt',
    ]]
    sources += [source / 'p0d2f0182/input/DesktopCombatInput.kt', source / 'p0d2f0182/content/EnemyAnimator.kt']
    tests = REPO / 'app/src/test/java/com/example/wuxiaarena'
    test_sources = sorted((tests / 'core').rglob('*.kt'))
    test_sources += [tests / 'p0d2f0182/runtime' / name for name in [
        'ArenaSessionTest.kt', 'ArenaAttackDirectionTest.kt', 'AttackBankProfilesTest.kt',
        'CombatFeedbackTimingTest.kt', 'CombatImpactEventTest.kt',
    ]]
    classes = OUT / 'classes'
    classes.mkdir(exist_ok=True)
    pico_jars = []
    for group in ['com.pico.spatial.core/core', 'com.pico.spatial.foundation/foundation']:
        aar = next((CACHE / group / '6.1.9').glob('*/*.aar'))
        target = OUT / (group.split('/')[-1] + '-6.1.9.jar')
        with zipfile.ZipFile(aar) as archive:
            target.write_bytes(archive.read('classes.jar'))
        pico_jars.append(target)
    compile_cp = os.pathsep.join(map(str, [stdlib, junit, android, compiler_jars[-2], *pico_jars]))
    java_home = os.environ.get('JAVA_HOME')
    java = str(Path(java_home) / 'bin/java') if java_home else str(next((Path.home() / '.pico/primer-cli/jdk').glob('*/Contents/Home/bin/java')))
    command = [java, '-Xmx768m', '-cp', os.pathsep.join(map(str, compiler_jars)),
               'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect',
               '-jvm-target', '11', '-classpath', compile_cp, '-d', str(classes),
               *map(str, sources + test_sources)]
    compiled = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    (OUT / 'compile.txt').write_text(compiled.stdout + compiled.stderr)
    print(compiled.stdout + compiled.stderr, end='')
    if compiled.returncode:
        return compiled.returncode
    # Paths above are package-relative to app/src/test/java, not source file names inferred from output.
    test_classes = ['com.example.wuxiaarena.' + '.'.join(p.relative_to(tests).with_suffix('').parts) for p in test_sources]
    if '--focus' in sys.argv:
        test_classes = [name for name in test_classes if '.p0d2f0182.runtime.' in name]
    run = subprocess.run([java, '-cp', os.pathsep.join(map(str, [classes, stdlib, junit, hamcrest, android])),
                          'org.junit.runner.JUnitCore', *test_classes], cwd=REPO, text=True, capture_output=True)
    output = run.stdout + run.stderr
    suffix = 'focused' if '--focus' in sys.argv else 'all-core'
    (OUT / ('junit-' + suffix + '.txt')).write_text(output)
    (OUT / ('result-' + suffix + '.json')).write_text(json.dumps({'exit_code': run.returncode, 'test_classes': test_classes,
                                                'compiler': 'Kotlin 2.1.20', 'shared_gradle_used': False}, indent=2) + '\n')
    print(output)
    return run.returncode


if __name__ == '__main__':
    sys.exit(main())
