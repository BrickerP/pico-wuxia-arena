"""Reuse the frozen common-Grip Left decode derivation for the actual199c pair."""
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;LEGACY=HERE.parents[2]/'left-rebuild'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 spec=importlib.util.spec_from_file_location('frozen_left_decode',LEGACY/'make_companion.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.CANDIDATE=HERE/'left_hand_joint.glb';m.CANDIDATE_SHA=json.loads((HERE/'construction.json').read_text())['candidate']['sha256'];m.RIGHT=HERE.parent/'right_hand_joint.glb';m.RIGHT_SHA='199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64';m.RIGHT_DECODED=HERE.parent/'right_hand_joint_decoded.glb';m.RIGHT_DECODED_SHA=sha(m.RIGHT_DECODED);m.OUTPUT=HERE/'left_hand_joint_decoded.glb'
 driver=m.load_driver();p=driver.helper();raw=m.CANDIDATE.read_bytes();result,report=m.derive(driver,p,raw,m.CANDIDATE_SHA);m.OUTPUT.write_bytes(result)
 assert m.CANDIDATE.read_bytes()==raw
 report['adapter']={'path':driver.relative(Path(__file__).resolve()),'sha256':sha(Path(__file__))}
 report['frozen_left_decode_implementation']={'path':str((LEGACY/'make_companion.py').relative_to(HERE.parents[7])),'sha256':sha(LEGACY/'make_companion.py')}
 (HERE/'decode_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('FRESH_LEFT_DECODE',m.CANDIDATE_SHA,sha(m.OUTPUT))
if __name__=='__main__':main()
