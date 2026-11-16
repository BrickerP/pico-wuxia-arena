"""Derive the current anatomical Right as a common-Grip Left; no runtime asset writes."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[8]
SOURCE=HERE.parent/'right_hand_patch.glb'
SOURCE_SHA='a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862'
SOURCE_VERIFICATION=HERE.parent/'verification.json'
SOURCE_DELTA=HERE.parent/'patch_delta.json'
LEGACY=REPO/'ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild'
DEPS={'build_left.py':'f23797a0af98f26b83f032aff1540fc7d81b070351d33ab89ddb074de058c29f',
      'verify_left_rebuild.py':'4cd634d3c854825cd4761e2e78df75c169ad80b1ca673eb7dfacacaf80340447',
      'test_verify_left_rebuild.py':'425c7f9b50571810181ca61353e4d5b5b812e347760de8c1251f340d392317f7'}
OUTPUT=HERE/'left_hand_anatomical.glb'
DAO=REPO/'ArtSource/tripo-warrior/library/dao_grip.glb'
DAO_SHA='db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def item(path):return {'path':path.relative_to(REPO).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size}
def require(value,message):
 if not value:raise ValueError(message)
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--verify-only',action='store_true',help='Keep existing GLB and independently re-audit the pinned current source')
 args=parser.parse_args()
 require(sha(SOURCE)==SOURCE_SHA,'Current anatomical Right identity changed; never substitute old3a geometry')
 require(sha(DAO)==DAO_SHA,'Actual unreflected dao changed')
 for name,digest in DEPS.items():require(sha(LEGACY/name)==digest,'Frozen producer/verifier changed: '+name)
 source_review=json.loads(SOURCE_VERIFICATION.read_text())
 require(source_review.get('passed') is True and source_review['candidate_sha256']==SOURCE_SHA,'Current anatomical source verification missing')
 delta=json.loads(SOURCE_DELTA.read_text())
 require(delta['candidate_sha256']==SOURCE_SHA and sha(SOURCE_DELTA)==source_review['delta_sha256'],'Current anatomical delta identity differs')
 authorized=source_review['changed_source_attributes']['WEIGHTS_0']
 require(len(authorized)==14,'Expected the actual14 authorized metacarpal weight edits')
 builder=load('anatomical_left_frozen_builder',LEGACY/'build_left.py')
 source,binary=builder.h.read(SOURCE)
 result,packed,edits=builder.rebuild(source,binary)
 value=builder.common.encode_glb(result,packed)
 expected_sha=hashlib.sha256(value).hexdigest()
 if args.verify_only:
  require(OUTPUT.exists() and sha(OUTPUT)==expected_sha,'Existing derived Left differs from deterministic current-source result')
 else:
  OUTPUT.write_bytes(value)
 left,lb=builder.h.read(OUTPUT)
 production_check=builder.verify(source,binary,left,lb)
 controls=builder.control_tests()
 # This independent verifier does not call the producer. Only explicit input
 # bindings change in RAM; its frozen code and original d8 package remain intact.
 verifier=load('verify_left_rebuild',LEGACY/'verify_left_rebuild.py')
 verifier.SOURCE=SOURCE;verifier.CANDIDATE=OUTPUT;verifier.DAO=DAO
 verifier.PINS={'source':SOURCE_SHA,'candidate':expected_sha,'dao':DAO_SHA}
 contract=verifier.verify_contract(source,binary,left,lb)
 for state in contract['states']:
  require(state['joint_world_max_error']==0,'Nonzero actual joint reflection error')
  for primitive in state['primitives']:
   require(all(primitive[k]==0 for k in ['LBS_max_error_m','inverse_transpose_normal_max_error','winding_area_vector_max_error_m2']),'Nonzero actual LBS/normal/winding reflection error')
 # Explicitly expose the inherited source protection domain and authorized14
 # rows, in addition to the complete-array checks in the independent verifier.
 import numpy as np
 protected=np.asarray(delta['protected_source_vertices'],dtype=int)
 require(delta['candidate_vertex_to_source'][:delta['source_vertex_count']]==list(range(delta['source_vertex_count'])),'Original source vertex ordering changed')
 rp=source['meshes'][0]['primitives'][0];lp=left['meshes'][0]['primitives'][0]
 protection=[]
 for time in (None,0.,.5,1.):
  rw=builder.h.sampled_worlds(source,binary,None if time is None else 'grip',time or 0)
  lw=builder.h.sampled_worlds(left,lb,None if time is None else 'grip',time or 0)
  r=builder.h.skin(source,binary,rp,rw);l=builder.h.skin(left,lb,lp,lw)
  error=float(np.max(np.abs(l[protected]-r[protected]@builder.S[:3,:3])))
  require(error==0,'Protected-domain LBS reflection changed')
  protection.append({'time':'default' if time is None else time,'protected_original_vertices':len(protected),'LBS_reflection_error_m':error})
 weight_rows={}
 for name in ('WEIGHTS_0','JOINTS_0'):
  a=builder.h.values(source,binary,rp['attributes'][name])[authorized]
  b=builder.h.values(left,lb,lp['attributes'][name])[authorized]
  require(a.tobytes()==b.tobytes(),'Authorized14 source rows changed')
  weight_rows[name]={'source_and_left_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'rows':len(a),'byte_exact':True}
 old_left,old_binary=builder.h.read(LEGACY/'left_hand_rebuilt.glb')
 try:verifier.verify_contract(source,binary,old_left,old_binary)
 except ValueError:old_left_rejected=True
 else:raise ValueError('Old d8 Left unexpectedly substituted for current anatomical source')
 test_module=load('anatomical_left_legacy_controls',LEGACY/'test_verify_left_rebuild.py')
 stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream).run(unittest.defaultTestLoader.loadTestsFromModule(test_module))
 require(tests.wasSuccessful() and tests.testsRun>=27 and not tests.skipped,'Independent negative controls failed: '+stream.getvalue())
 print('INDEPENDENT_CONTRACT_CONTROLS',tests.testsRun,'passed',flush=True)
 contact=verifier.audit_contacts(source,binary,left,lb)
 for state in contact['states']:
  right=state['hands']['R']['position_weld_self']['count'];mirrored=state['hands']['L']['position_weld_self']['count']
  require(right==mirrored,'New self crossings in derived Left')
  require(not state['Left_self_added_vs_Right'],'New Left-only self crossings')
 require(contact['states'][-1]['hands']['R']['position_weld_self']['count']==109,'Source finger-pair inheritance changed')
 require(binary==lb[:len(binary)],'Original complete source BIN prefix was not preserved')
 # Actual WEIGHTS/JOINTS byte identity includes all14 authorized edits; UV and
 # texture preservation above are checked against a980, not the old3a baseline.
 attributes=[]
 for mi,(rm,lm) in enumerate(zip(source['meshes'],left['meshes'])):
  for pi,(rp,lp) in enumerate(zip(rm['primitives'],lm['primitives'])):
   entry={'mesh':mi,'primitive':pi,'attributes':{}}
   for name in ('WEIGHTS_0','JOINTS_0','TEXCOORD_0'):
    a=builder.h.values(source,binary,rp['attributes'][name]);b=builder.h.values(left,lb,lp['attributes'][name])
    require(a.dtype==b.dtype and a.shape==b.shape and a.tobytes()==b.tobytes(),'Current source attribute changed: '+name)
    entry['attributes'][name]={'sha256':hashlib.sha256(a.tobytes()).hexdigest(),'byte_exact':True,'count':len(a)}
   attributes.append(entry)
 verification={'status':'private_anatomical_Left_numeric_review_passed_not_native_acceptance',
  'source':item(SOURCE),'candidate':item(OUTPUT),'dao':item(DAO),'source_verification':item(SOURCE_VERIFICATION),'source_delta':item(SOURCE_DELTA),
  'producer_crosscheck':production_check,'independent_contract':contract,'synthetic_producer_controls':controls,
  'independent_negative_controls':{'tests':tests.testsRun,'failures':len(tests.failures),'errors':len(tests.errors),'skipped':len(tests.skipped),'output':stream.getvalue()},
  'current_source_attributes':attributes,'authorized_source_weight_vertex_ids':authorized,
  'authorized14_weight_and_palette_rows':weight_rows,'protected_domain':protection,'obsolete_d8_Left_rejected':old_left_rejected,
  'actual_contacts_and_self':contact,'source_BIN_prefix_exact':True,'new_self_pairs':0,'inherited_closed_finger_pairs':109,
  'implementation':item(Path(__file__).resolve()),'frozen_reused_code':[item(LEGACY/name) for name in DEPS],
  'scope':'Actual default/grip0/.5/1 LBS, inverse-transpose normals, winding, full palette/IBM and animations. Real source has no TANGENT; tangent xyz/w covered by synthetic controls. No image or SDK acceptance.'}
 (HERE/'verification.json').write_text(json.dumps(verification,indent=2,ensure_ascii=False)+'\n')
 mapping={'reflection_S_rowmajor':builder.S.tolist(),'common_Grip_root':'LeftGripRoot identity; receives G directly',
  'legacy_C_B_or_negative_scale':False,'palette_order_unchanged':source['skins'][0]['joints']==left['skins'][0]['joints'],
  'node_names':[{'node':i,'right':a.get('name'),'left':b.get('name')} for i,(a,b) in enumerate(zip(source['nodes'],left['nodes']))],
  'accessor_transforms':edits,'independent_geometry_reflection_max_error_m':0,'source':item(SOURCE),'candidate':item(OUTPUT)}
 (HERE/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
 handoff={'status':'stage_ended_private_Left_derivation_ready_for_Root_integration_review','source':item(SOURCE),'candidate':item(OUTPUT),
  'source_technical_evidence':item(SOURCE_VERIFICATION),'source_delta':item(SOURCE_DELTA),'verification':item(HERE/'verification.json'),'mapping':item(HERE/'mapping.json'),
  'implementation':item(Path(__file__).resolve()),'reused_frozen_code':[item(LEGACY/name) for name in DEPS],
  'normal_and_winding_LBS_reflection_error':0,'authorized14_weights_preserved':True,'inherited_closed_finger_self_pairs':109,'new_self_pairs':0,
  'rebuild_command':'python3 -B '+str(Path(__file__).resolve().relative_to(REPO)),
  'integration':'Root replaces current Right and derived Left together; commonGrip/SDK frame unchanged. This task never writes app/formal assets.',
  'limits':['Mirror equivalence does not repair inherited finger intersections or old fixed-DAO open/mid contacts.','The actual dao is not mirrored and is independently measured by component topology.','No render, Blender, native SDK tracking physiology, tangent generator or final hand-quality pass is claimed.']}
 (HERE/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
 require(sha(SOURCE)==SOURCE_SHA and sha(DAO)==DAO_SHA,'Input changed during audit')
 for name,digest in DEPS.items():require(sha(LEGACY/name)==digest,'Frozen dependency changed during audit')
 print(json.dumps({'left_sha256':expected_sha,'bytes':OUTPUT.stat().st_size,'independent_controls':tests.testsRun,'geometry_reflection_error':0,'inherited109_new0':True,'verification':str(HERE/'verification.json')},indent=2),flush=True)

if __name__=='__main__':main()
