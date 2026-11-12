"""Compile only the candidate pure policies and existing core tests; never invokes Gradle/Git/device."""
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MAIN = ROOT / 'app/src/main/java/com/example/wuxiaarena'
TEST = ROOT / 'app/src/test/java/com/example/wuxiaarena'
CANDIDATE = HERE / 'candidate'

def main():
    sources = sorted((MAIN / 'core').rglob('*.kt'))
    sources += [MAIN / 'p0d2f0182/runtime/CombatFeedbackProfile.kt']
    sources += [MAIN / ('p0d2f0182/content/' + n + '.kt') for n in ['ContactParticleMotion', 'ContactParticlePresets', 'SoftContactEnvelope']]
    sources += [CANDIDATE / 'src/main/java/com/example/wuxiaarena/p0d2f0182/content/NativeImpactLight.kt',
                CANDIDATE / 'src/test/java/com/example/wuxiaarena/p0d2f0182/content/NativeImpactLightTest.kt',
                TEST / 'p0d2f0182/content/SoftContactEnvelopeTest.kt']
    command = [sys.executable, str(ROOT / 'ArtSource/refinement/effects/runtime-polish/testing/run_jvm_tests.py'),
               '--java', str(Path.home() / '.pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java'),
               '--output', str(HERE / 'isolated-tests')]
    for source in sources: command += ['--source', str(source)]
    for name in ['NativeImpactLightTest', 'SoftContactEnvelopeTest']:
        command += ['--test', 'com.example.wuxiaarena.p0d2f0182.content.' + name]
    return subprocess.run(command, cwd=ROOT, timeout=120).returncode

if __name__ == '__main__': sys.exit(main())
