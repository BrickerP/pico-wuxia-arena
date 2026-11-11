"""Run production audio policy and feedback tests on the JVM, without Gradle/APK/device.

Uses the existing local Kotlin/JUnit caches and Android SDK API definitions.
Only android.util.Log and generated resource IDs are test substitutes; the audio
output itself is injected by CombatAudioTest. ArenaSession and combat code remain
the real production sources. Generated files live under the ignored build/ tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CACHE = Path.home() / ".gradle/caches/modules-2/files-2.1"
BUILD = ROOT / "build/audio-jvm-tests"
PACKAGE = "com.example.wuxiaarena.p0d2f0182"
MAIN = ROOT / "app/src/main/java"
TEST = ROOT / "app/src/test/java" / Path(PACKAGE.replace(".", "/")) / "runtime"
RUNTIME = MAIN / Path(PACKAGE.replace(".", "/")) / "runtime"


def cached(group: str, artifact: str, version: str | None = None) -> Path:
    base = CACHE / group / artifact
    found = sorted(base.glob(f"{version or '*'}/*/{artifact}-*.jar"))
    if not found:
        raise RuntimeError(f"Existing local dependency missing: {group}:{artifact}:{version or '*'}")
    return found[-1]


def java_executable() -> Path:
    candidates = []
    if os.environ.get("JAVA_HOME"):
        candidates.append(Path(os.environ["JAVA_HOME"]) / "bin/java")
    candidates.extend(sorted((Path.home() / ".pico/primer-cli/jdk").glob("*/Contents/Home/bin/java")))
    candidates.extend(sorted((Path.home() / ".pico/primer-cli/jdk").glob("*/bin/java")))
    if shutil.which("java"):
        candidates.append(Path(shutil.which("java")))
    for candidate in candidates:
        if candidate.is_file() and subprocess.run(
            [str(candidate), "-version"], capture_output=True, timeout=10,
        ).returncode == 0:
            return candidate
    raise RuntimeError("No installed JDK found; set JAVA_HOME to an existing JDK. Nothing was installed.")


def android_jar() -> Path:
    sdk_paths = [Path.home() / "Library/Android/sdk"]
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(key):
            sdk_paths.insert(0, Path(os.environ[key]))
    properties = ROOT / "local.properties"
    if properties.exists():
        for line in properties.read_text().splitlines():
            if line.startswith("sdk.dir="):
                sdk_paths.insert(0, Path(line.split("=", 1)[1].replace("\\:", ":").replace("\\ ", " ")))
    for sdk in sdk_paths:
        candidate = sdk / "platforms/android-35/android.jar"
        if candidate.is_file():
            return candidate
    raise RuntimeError("Existing Android 35 API definitions were not found; nothing was installed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audio-only', action='store_true', help='Run the audio/accent lane without the shared combat timing fixtures')
    args = parser.parse_args()
    evidence = BUILD / 'audio-only' if args.audio_only else BUILD
    if subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip() != str(ROOT):
        raise RuntimeError("Run only against the original pico-wuxia-arena working tree")
    java = java_executable()
    api = android_jar()
    compiler = cached("org.jetbrains.kotlin", "kotlin-compiler-embeddable", "2.1.20")
    stdlib = cached("org.jetbrains.kotlin", "kotlin-stdlib", "2.1.20")
    junit = cached("junit", "junit", "4.13.2")
    hamcrest = cached("org.hamcrest", "hamcrest-core", "1.3")
    annotations = cached("org.jetbrains", "annotations", "13.0")
    compiler_cp = [compiler, stdlib, annotations,
                   cached("org.jetbrains.kotlin", "kotlin-script-runtime", "2.1.20"),
                   cached("org.jetbrains.kotlin", "kotlin-reflect"),
                   cached("org.jetbrains.intellij.deps", "trove4j"),
                   cached("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm")]
    classpath = os.pathsep.join(map(str, [stdlib, junit, hamcrest, annotations, api]))
    evidence.mkdir(parents=True, exist_ok=True)
    classes = evidence / "classes"
    if classes.exists():
        shutil.rmtree(classes)
    classes.mkdir()
    log_stub = evidence / "Log.kt"
    log_stub.write_text("""package android.util
object Log {
    @JvmStatic fun i(tag: String, message: String): Int = 0
    @JvmStatic fun w(tag: String, message: String, error: Throwable? = null): Int = 0
    @JvmStatic fun e(tag: String, message: String, error: Throwable? = null): Int = 0
}
""")
    # Test-only integer identities. Asset validity is checked by the audio asset tests.
    resources = sorted(set(re.findall(r"R\.raw\.(\w+)", (RUNTIME / "CombatAudio.kt").read_text())))
    r_stub = evidence / "R.kt"
    r_stub.write_text(f"package {PACKAGE}\nobject R {{ object raw {{\n" +
                      "".join(f"    const val {name}: Int = {index}\n" for index, name in enumerate(resources, 1)) +
                      "} }\n")
    sources = sorted((MAIN / "com/example/wuxiaarena/core").rglob("*.kt"))
    sources += [RUNTIME / name for name in (
        "ArenaSession.kt", "ArenaOpponents.kt", "AttackBankProfiles.kt", "AttackBankProfileData.kt",
        "CombatFeedbackProfile.kt", "CombatAudio.kt",
    )]
    sources += [MAIN / Path(PACKAGE.replace(".", "/")) / "input/DesktopCombatInput.kt"]
    test_names = ["CombatAudioTest", "ImpactAccentTest"]
    if not args.audio_only: test_names.append("CombatFeedbackTimingTest")
    sources += [TEST / f"{name}.kt" for name in test_names]
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    command = [str(java), "-cp", os.pathsep.join(map(str, compiler_cp)),
               "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler", "-no-stdlib", "-no-reflect",
               "-jvm-target", "11", "-classpath", classpath, "-d", str(classes)]
    print(f"Compiling {len(sources)} production/test sources with local Kotlin 2.1.20 and JDK: {java}", flush=True)
    compile_result = subprocess.run(command + list(map(str, sources + [log_stub, r_stub])), cwd=ROOT, capture_output=True, text=True)
    (evidence / "compile.txt").write_text(compile_result.stdout + compile_result.stderr)
    if compile_result.returncode:
        print(compile_result.stdout + compile_result.stderr)
        return compile_result.returncode
    run = subprocess.run(
        [str(java), "-cp", str(classes) + os.pathsep + classpath, "org.junit.runner.JUnitCore"] +
        [f"{PACKAGE}.runtime.{name}" for name in test_names], cwd=ROOT, capture_output=True, text=True,
    )
    output = run.stdout + run.stderr
    (evidence / "result.txt").write_text(output)
    count = re.search(r"OK \((\d+) tests?\)", output)
    (evidence / "report.json").write_text(json.dumps({
        "passed": run.returncode == 0, "test_count": int(count[1]) if count else None,
        "java": str(java), "source_sha256": hashes,
        "scope": "Production event/audio and haptic policy only; no Android output, SDK haptics or device verification.",
    }, indent=2) + "\n")
    print(output, end="")
    print(f"Evidence: {evidence / 'report.json'}")
    return run.returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Audio JVM checks unavailable: {error}", file=sys.stderr)
        sys.exit(2)
