#!/usr/bin/env python3
"""Compile an explicit, isolated Kotlin/JUnit subset without invoking shared Gradle."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def cached_jar(group, artifact, version):
    base = Path.home() / '.gradle/caches/modules-2/files-2.1' / group / artifact / version
    matches = sorted(base.glob(f'*/{artifact}-{version}.jar'))
    if len(matches) != 1:
        raise RuntimeError(f'Expected one cached {artifact} {version}, found {len(matches)}')
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--source', type=Path, action='append', required=True)
    parser.add_argument('--test', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--classpath', type=Path, action='append', default=[])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # A unique classes directory prevents an old test class from satisfying a later subset run.
    temporary_classes = tempfile.TemporaryDirectory(prefix='classes-', dir=output)
    classes = Path(temporary_classes.name)
    compiler = [cached_jar('org.jetbrains.kotlin', name, version) for name, version in [
        ('kotlin-compiler-embeddable', '2.1.20'),
        ('kotlin-stdlib', '2.1.20'),
        ('kotlin-script-runtime', '2.1.20'),
        ('kotlin-reflect', '1.6.10'),
        ('kotlin-daemon-embeddable', '2.1.20'),
    ]]
    compiler.extend([
        cached_jar('org.jetbrains.intellij.deps', 'trove4j', '1.0.20200330'),
        cached_jar('org.jetbrains', 'annotations', '23.0.0'),
        cached_jar('org.jetbrains.kotlinx', 'kotlinx-coroutines-core-jvm', '1.8.0'),
    ])
    runtime = [
        cached_jar('org.jetbrains.kotlin', 'kotlin-stdlib', '2.1.20'),
        cached_jar('junit', 'junit', '4.13.2'),
        cached_jar('org.hamcrest', 'hamcrest-core', '1.3'),
        cached_jar('org.jetbrains', 'annotations', '23.0.0'),
    ]
    runtime.extend(path.resolve(strict=True) for path in args.classpath)
    sources = [source.resolve(strict=True) for source in args.source]
    compile_cmd = [str(args.java), '-cp', ':'.join(map(str, compiler)),
                   'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect',
                   '-jvm-target', '11', '-classpath', ':'.join(map(str, runtime)),
                   '-d', str(classes), *map(str, sources)]
    test_cmd = [str(args.java), '-cp', ':'.join(map(str, [classes, *runtime])),
                'org.junit.runner.JUnitCore', *args.test]
    report = {'sources': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
              'compile': {'command': compile_cmd}, 'tests': {'command': test_cmd}}
    try:
        for name, command in [('compile', compile_cmd), ('tests', test_cmd)]:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=120)
            report[name].update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
            print(completed.stdout, end='')
            print(completed.stderr, file=sys.stderr, end='')
            (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            if completed.returncode:
                return completed.returncode
        return 0
    finally:
        temporary_classes.cleanup()


if __name__ == '__main__':
    sys.exit(main())
