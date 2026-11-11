"""The single production entry for contact-polish candidate assets.

Run in Blender Python. Writes candidates only; app assets remain Root-owned.
"""
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def main():
    assets = []
    with tempfile.TemporaryDirectory(prefix='.contact-build-', dir=HERE) as temporary:
        jobs = [('metal', 'build_metal.py'), ('wet', 'build_wet.py'), ('ground', 'build_ground.py'),
                ('ground/visibility-v2', 'build_visibility.py'),
                ('visibility-v3/metal', 'build_metal_v3.py'), ('visibility-v3/wet', 'build_wet_v3.py')]
        for family, filename in jobs:
            path = HERE / family / filename
            module_name = 'contact_polish_' + family.replace('/', '_').replace('-', '_')
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            staged = Path(temporary) / family
            module.build(staged)
            files = sorted(staged.iterdir())
            for output in files:
                output.replace(HERE / family / output.name)
            assets.append({'family': family, 'builder': family + '/' + filename,
                           'files': [output.name for output in files]})
    outputs = []
    for path in sorted(HERE.rglob('*.glb')):
        data = path.read_bytes()
        outputs.append({'path': path.relative_to(HERE).as_posix(), 'bytes': len(data),
                        'sha256': hashlib.sha256(data).hexdigest()})
    (HERE / 'catalog.json').write_text(json.dumps({'production_entry': 'build_contact_polish.py',
        'assets': assets, 'outputs': outputs, 'runtime_integration': 'Root-owned Entity/Opacity driver',
        'contact_review': {'baseline': ['metal/', 'wet/'], 'visibility_candidate': 'visibility-v3/',
                           'motion_schema': 'contact-particle-motion/v2'},
        'ground_review': {'baseline': 'ground/', 'visibility_candidate': 'ground/visibility-v2/'},
        'publication': 'Review candidates only; Root selects the final runtime assets'},
        ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(outputs, ensure_ascii=False))


if __name__ == '__main__':
    main()
