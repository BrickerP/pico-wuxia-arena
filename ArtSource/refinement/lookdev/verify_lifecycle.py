"""Test actual SceneLighting with deterministic native doubles and real coroutines; no Gradle."""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CACHE = Path.home() / ".gradle/caches/modules-2/files-2.1"
STUBS = HERE / "tests/lifecycle-stubs"
OUT = STUBS / "results"


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
    classpath = [compiler[1], jar("org.jetbrains.kotlinx", "kotlinx-coroutines-core-jvm", "1.9.0"),
                 jar("androidx.annotation", "annotation-jvm", "1.9.1"),
                 jar("junit", "junit", "4.13.2"), jar("org.hamcrest", "hamcrest-core", "1.3")]
    java = Path.home() / ".pico/primer-cli/jdk/jdk-21.0.13+9/Contents/Home/bin/java"
    production = ROOT / "app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/SceneLighting.kt"
    sources = [production, HERE / "tests/SceneLightingLifecycleTest.kt", *sorted(STUBS.glob("*.kt"))]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    report = {"scope": "Actual SceneLighting lifecycle with native doubles; no SDK compatibility/rendering/device proof",
              "compiler": "2.1.20", "coroutines": "1.9.0", "source_sha256": hashes}
    with tempfile.TemporaryDirectory(prefix="classes-", dir=OUT) as classes:
        command = [str(java), "-cp", ":".join(map(str, compiler)), "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler",
                   "-no-stdlib", "-no-reflect", "-jvm-target", "11", "-classpath", ":".join(map(str, classpath)),
                   "-d", classes, *map(str, sources)]
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=60)
        (OUT / "compile.txt").write_text(result.stdout)
        print(result.stdout)
        report["compile_exit_code"] = result.returncode
        if result.returncode == 0:
            tests = subprocess.run([str(java), "-cp", ":".join(map(str, [classes, *classpath])),
                                    "org.junit.runner.JUnitCore",
                                    "com.example.wuxiaarena.p0d2f0182.content.SceneLightingLifecycleTest"],
                                   cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, timeout=60)
            (OUT / "tests.txt").write_text(tests.stdout)
            print(tests.stdout)
            report["test_exit_code"] = tests.returncode
    if hashes != {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}:
        raise RuntimeError("Production or test source changed during verification; rerun")
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(report["compile_exit_code"] or report.get("test_exit_code", 1))


if __name__ == "__main__":
    main()
