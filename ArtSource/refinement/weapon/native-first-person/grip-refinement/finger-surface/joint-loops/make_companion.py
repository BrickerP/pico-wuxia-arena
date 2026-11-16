"""Fresh joint GLB, unchanged actual KTX decode, no source mesh substitution."""
import hashlib,importlib.util,json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('decode',HERE.parent.parent/'palm-wrist-surface/make_companion.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.CANDIDATE=HERE/'right_hand_joint.glb';m.OUTPUT=HERE/'right_hand_joint_decoded.glb';driver=m.load_driver();p=driver.helper();pin=hashlib.sha256(m.CANDIDATE.read_bytes()).hexdigest();out,report=m.derive(driver,p,m.CANDIDATE.read_bytes(),pin);m.OUTPUT.write_bytes(out);report['adapter_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(HERE/'decode_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('JOINT_DECODED',pin)
