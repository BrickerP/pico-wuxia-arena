"""Compile only the two candidate modules against installed SDK; never run Gradle."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = Path.home() / ".gradle/caches/modules-2/files-2.1"
OUT = HERE / "verification"


def jar(group, artifact, version):
    matches = list((CACHE / group / artifact / version).glob("*/*.jar"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one cached {artifact}:{version}, found {matches}")
    return matches[0]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    compiler = [jar("org.jetbrains.kotlin", "kotlin-compiler-embeddable", "2.1.20"),
                jar("org.jetbrains.kotlin", "kotlin-stdlib", "2.1.20"),
                jar("org.jetbrains.kotlin", "kotlin-script-runtime", "2.1.20"),
                jar("org.jetbrains.kotlin", "kotlin-reflect", "1.6.10"),
                jar("org.jetbrains.intellij.deps", "trove4j", "1.0.20200330"),
                jar("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.8.0"),
                jar("org.jetbrains", "annotations", "13.0")]
    core = Path.home() / ".gradle/caches/8.13/transforms/559e06748c84ca24f6935b142ea849f3/transformed/core-6.1.9-runtime.jar"
    foundation = Path.home() / ".gradle/caches/8.13/transforms/3e205561cd5a5d68fd8b18809ef69bc3/transformed/foundation-6.1.9-runtime.jar"
    classpath = [core, foundation, compiler[1],
                 jar("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.9.0"),
                 jar("androidx.annotation", "annotation-jvm", "1.9.1"),
                 jar("junit", "junit", "4.13.2"),
                 jar("org.hamcrest", "hamcrest-core", "1.3"),
                 Path.home() / "Library/Android/sdk/platforms/android-35/android.jar"]
    java = Path.home() / ".pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java"
    source = ROOT / "app/src/main/java/com/example/wuxiaarena/p0d2f0182/content"
    files = [source / "SceneLighting.kt", source / "SceneWeather.kt", HERE / "tests/SceneWeatherMotionTest.kt"]
    classes = OUT / "classes"
    command = [str(java), "-cp", ":".join(map(str, compiler)), "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler",
               "-no-stdlib", "-no-reflect", "-jvm-target", "11", "-classpath", ":".join(map(str, classpath)),
               "-d", str(classes), *map(str, files)]
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (OUT / "sdk-compile.txt").write_text(result.stdout)
    print(result.stdout)
    report = {"scope": "isolated candidate compile and pure motion tests; no app build or device proof",
              "sdk": "6.1.9", "compiler": "2.1.20", "compile_exit_code": result.returncode,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    if result.returncode == 0:
        tests = subprocess.run([str(java), "-cp", ":".join(map(str, [classes, *classpath])),
                                "org.junit.runner.JUnitCore", "com.example.wuxiaarena.p0d2f0182.content.SceneWeatherMotionTest"],
                               cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (OUT / "motion-tests.txt").write_text(tests.stdout)
        print(tests.stdout)
        report["test_exit_code"] = tests.returncode
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    if classes.exists():
        shutil.rmtree(classes)
    raise SystemExit(result.returncode or report.get("test_exit_code", 1))


if __name__ == "__main__":
    main()
