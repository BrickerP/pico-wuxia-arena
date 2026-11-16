"""Fresh actual-KTX decode for the anatomically corrected hand, no mesh substitution."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    spec=importlib.util.spec_from_file_location('actual_decode',HERE.parents[1]/'make_companion.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.CANDIDATE=HERE/'right_hand_patch.glb';module.OUTPUT=HERE/'right_hand_patch_decoded.glb'
    driver=module.load_driver();helper=driver.helper()
    pin=hashlib.sha256(module.CANDIDATE.read_bytes()).hexdigest()
    decoded,report=module.derive(driver,helper,module.CANDIDATE.read_bytes(),pin)
    report['anatomical_adapter']={'path':driver.relative(Path(__file__)),
        'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    module.OUTPUT.write_bytes(decoded)
    (HERE/'decode_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Fresh actual-KTX anatomical companion',pin)


if __name__=='__main__':main()
