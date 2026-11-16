"""Derive a fresh decoded companion while preserving the candidate's non-image data."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    source=HERE.parent/'make_companion.py'
    spec=importlib.util.spec_from_file_location('verified_companion_builder',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.CANDIDATE=HERE/'right_hand_patch.glb'
    module.OUTPUT=HERE/'right_hand_patch_decoded.glb'
    module.MANIFEST=HERE/'decode_manifest.json'
    driver=module.load_driver();helper=driver.helper()
    pin=hashlib.sha256(module.CANDIDATE.read_bytes()).hexdigest()
    output,report=module.derive(driver,helper,module.CANDIDATE.read_bytes(),pin)
    report['production_patch_adapter']={'path':driver.relative(Path(__file__)),
        'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    module.OUTPUT.write_bytes(output)
    module.MANIFEST.write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh actual-KTX companion',pin)


if __name__=='__main__':main()
