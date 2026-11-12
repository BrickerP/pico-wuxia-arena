"""Validate the 08 source subset against installed public 6.1.9 SDK classes, without Gradle."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import hashlib

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
MAIN = ROOT / 'app/src/main/java/com/example/wuxiaarena'
TEST = ROOT / 'app/src/test/java/com/example/wuxiaarena'
CACHE = Path.home() / '.gradle/caches/modules-2/files-2.1'
JAVA = Path.home() / '.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java'
CONTENT = ['SoftContactEnvelope', 'ContactEventTiming', 'ContactParticleMotion', 'ContactParticlePresets', 'ContactParticleEmitter', 'CombatEffects', 'BladeTrailGeometry', 'PlayerBladeTrail']
RUNTIME = ['ArenaSession', 'ArenaOpponents', 'AttackBankProfiles', 'AttackBankProfileData', 'CombatFeedbackProfile', 'TrackingProcessor']
TESTS = ['p0d2f0182/content/SoftContactEnvelopeTest', 'p0d2f0182/content/ContactEventTimingTest', 'p0d2f0182/content/ContactParticleMotionTest', 'p0d2f0182/content/CombatEffectsTimingTest',
         'p0d2f0182/content/BladeTrailGeometryTest', 'core/combat/PlayerContactTangentTest',
         'core/combat/PlayerCombatImpactTest', 'core/combat/PlayerMotionContinuityTest']

def main():
    with_root_patch = '--with-root-patch' in sys.argv
    with tempfile.TemporaryDirectory(prefix='sdk-subset-', dir=HERE) as folder:
        classpath = [Path.home() / 'Library/Android/sdk/platforms/android-35/android.jar']
        provenance = []
        for aar in sorted(CACHE.glob('com.pico.spatial.*/*/6.1.9/*/*.aar')):
            data = aar.read_bytes()
            jar = Path(folder) / (aar.parent.parent.parent.parent.name + '-' + aar.parent.parent.parent.name + '.jar')
            with zipfile.ZipFile(aar) as archive:
                jar.write_bytes(archive.read('classes.jar'))
                for index, name in enumerate(n for n in archive.namelist() if n.endswith('.jar') and n != 'classes.jar'):
                    extra = Path(folder) / (aar.parent.parent.parent.parent.name + '-' + aar.parent.parent.parent.name + '-embedded-' + str(index) + '.jar')
                    extra.write_bytes(archive.read(name))
                    classpath.append(extra)
            classpath.append(jar)
            provenance.append({'aar': str(aar), 'sha256': hashlib.sha256(data).hexdigest()})
        classpath.extend(CACHE.glob('org.jetbrains.kotlinx/kotlinx-coroutines-core-jvm/1.8.0/*/*.jar'))
        sources = sorted((MAIN / 'core').rglob('*.kt'))
        sources += [MAIN / ('p0d2f0182/content/' + name + '.kt') for name in CONTENT]
        sources += [MAIN / ('p0d2f0182/runtime/' + name + '.kt') for name in RUNTIME]
        sources += [MAIN / 'p0d2f0182/input/DesktopCombatInput.kt']
        sources += [TEST / (name + '.kt') for name in TESTS]
        test_names = list(TESTS)
        if with_root_patch:
            session = MAIN / 'p0d2f0182/runtime/ArenaSession.kt'
            text = session.read_text()
            old = 'combat.simulationNanos, appliedDamage, zone, fatal)'
            new = 'combat.simulationNanos, appliedDamage, zone, fatal, tangent = contact.tangent)'
            if old in text:
                assert text.count(old) == 1
                text = text.replace(old, new)
            else:
                assert new in text
            staged = Path(folder) / 'ArenaSession.kt'
            staged.write_text(text)
            sources = [staged if source == session else source for source in sources]
            test = TEST / 'p0d2f0182/runtime/CombatImpactEventTest.kt'
            text = test.read_text()
            old = '        assertEquals(strike.contact.normal, impact.normal)'
            new = old + '\n        assertTrue(strike.contact.tangent != null)\n        assertEquals(strike.contact.tangent, impact.tangent)'
            if 'assertEquals(strike.contact.tangent, impact.tangent)' not in text:
                assert text.count(old) == 1
                text = text.replace(old, new)
            staged_test = Path(folder) / 'CombatImpactEventTest.kt'
            staged_test.write_text(text)
            sources.append(staged_test)
            test_names.append('p0d2f0182/runtime/CombatImpactEventTest')
        command = [sys.executable, str(HERE / 'run_jvm_tests.py'), '--java', str(JAVA), '--output', str(HERE / ('root-integration' if with_root_patch else 'runtime-subset'))]
        for path in classpath: command += ['--classpath', str(path)]
        for path in sources: command += ['--source', str(path)]
        for name in test_names: command += ['--test', 'com.example.wuxiaarena.' + name.replace('/', '.')]
        (HERE / 'sdk_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
        return subprocess.run(command, cwd=ROOT, timeout=150).returncode

if __name__ == '__main__': sys.exit(main())
