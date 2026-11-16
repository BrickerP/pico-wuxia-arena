"""Thin 199c common-Grip Left adapter; the frozen mirror producer is reused."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[7]
SOURCE=HERE.parent/'right_hand_joint.glb';SOURCE_SHA='199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64'
OUTPUT=HERE/'left_hand_joint.glb'
LEGACY=HERE.parents[2]/'left-rebuild'
DEPS={'build_left.py':'f23797a0af98f26b83f032aff1540fc7d81b070351d33ab89ddb074de058c29f','verify_left_rebuild.py':'4cd634d3c854825cd4761e2e78df75c169ad80b1ca673eb7dfacacaf80340447','test_verify_left_rebuild.py':'425c7f9b50571810181ca61353e4d5b5b812e347760de8c1251f340d392317f7'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):return {'path':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size}
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
 assert sha(SOURCE)==SOURCE_SHA,'Pinned199c Right identity changed'
 for name,pin in DEPS.items():assert sha(LEGACY/name)==pin,'Frozen mirror dependency changed: '+name
 review=json.loads((HERE.parent/'verification.json').read_text());delta=json.loads((HERE.parent/'joint_delta.json').read_text())
 assert review['passed'] and review['collision_checks_run'] and review['candidate_sha256']==SOURCE_SHA==delta['candidate_sha256']
 assert sha(HERE.parent/'joint_delta.json')==review['delta_sha256']
 builder=load('joint_left_frozen_producer',LEGACY/'build_left.py');source,sb=builder.h.read(SOURCE);result,packed,edits=builder.rebuild(source,sb);raw=builder.common.encode_glb(result,packed);pin=hashlib.sha256(raw).hexdigest()
 if args.verify_only:assert OUTPUT.exists() and OUTPUT.read_bytes()==raw,'Existing Left differs from deterministic199c derivation'
 else:OUTPUT.write_bytes(raw)
 left,lb=builder.h.read(OUTPUT);checks=builder.verify(source,sb,left,lb);controls=builder.control_tests()
 assert lb[:len(sb)]==sb
 report={'status':'actual_static_left_constructed_independent_audit_pending','source':item(SOURCE),'candidate':item(OUTPUT),'source_technical_evidence':item(HERE.parent/'verification.json'),'source_delta':item(HERE.parent/'joint_delta.json'),'frozen_reused_code':[item(LEGACY/name) for name in DEPS],'implementation':item(Path(__file__)),'producer_checks':checks,'producer_synthetic_controls':controls,'source_BIN_prefix_exact':True,'triangles_total':sum(left['accessors'][p['indices']]['count']//3 for mesh in left['meshes'] for p in mesh['primitives']),'scope':'S*M*S is baked by the existing producer; all geometry/N/winding/IBM/TRS/animation reflect, UV and skin palette/weights exact. Identity LeftGripRoot, no runtime negative scale or legacy correction.'}
 (HERE/'construction.json').write_text(json.dumps(report,indent=2)+'\n');(HERE/'mapping.json').write_text(json.dumps({'source':item(SOURCE),'candidate':item(OUTPUT),'reflection_S_rowmajor':builder.S.tolist(),'common_Grip_root':'LeftGripRoot identity','legacy_C_B_negative_scale':False,'node_name_map':[{'node':i,'right':a.get('name'),'left':b.get('name')} for i,(a,b) in enumerate(zip(source['nodes'],left['nodes']))],'accessor_transforms':edits},indent=2)+'\n')
 assert sha(SOURCE)==SOURCE_SHA
 print(json.dumps({'source_sha256':SOURCE_SHA,'left_sha256':pin,'triangles':report['triangles_total'],'bytes':len(raw),'producer_checks_passed':True}))
if __name__=='__main__':main()
