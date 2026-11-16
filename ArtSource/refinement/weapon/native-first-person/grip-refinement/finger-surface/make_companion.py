"""Retain this candidate's complete GLB and decode its unchanged actual KTX pixels."""
import hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('actual_decode',HERE.parent/'palm-wrist-surface/make_companion.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.CANDIDATE=HERE/'right_hand_finger.glb';m.OUTPUT=HERE/'right_hand_finger_decoded.glb'
driver=m.load_driver();helper=driver.helper();pin=hashlib.sha256(m.CANDIDATE.read_bytes()).hexdigest()
result,report=m.derive(driver,helper,m.CANDIDATE.read_bytes(),pin)
m.OUTPUT.write_bytes(result)
report['adapter_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(HERE/'decode_manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print('DECODED',pin,len(result))

spec=importlib.util.spec_from_file_location('finger_geometry',HERE/'build_finger.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
delta=json.loads((HERE/'finger_delta.json').read_text());doc,binary=g.b.h.read(g.SOURCE)
ids=g.np.asarray(delta['anatomy']['source_vertex_ids_in_anatomical_domain']);axes=g.np.asarray(delta['anatomy']['axes'])
guides={}
for label,time in [('open',0.),('mid',.5),('closed',1.)]:
 world=g.b.h.sampled_worlds(doc,binary,'grip',time);points=g.b.h.skin(doc,binary,doc['meshes'][0]['primitives'][0],world)
 guides[label]={'center_canonical_m':points[ids].mean(0).tolist(),'direction_canonical':g.unit(-axes[2]+.9*axes[1]+.28*axes[0]).tolist(),'source_vertex_ids':ids.tolist()}
(HERE/'render_guides.json').write_text(json.dumps(guides,indent=2)+'\n')
