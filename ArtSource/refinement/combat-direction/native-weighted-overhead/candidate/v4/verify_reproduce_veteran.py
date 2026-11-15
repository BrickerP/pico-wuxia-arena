"""Reproduce the real assembled veteran v3 target defect before any edit."""
import importlib.util,json,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
LANE=HERE.parents[1];REPO=LANE.parents[3]
p=LANE/'integration/review_candidate.py'
s=importlib.util.spec_from_file_location('actual_target_review',p);review=importlib.util.module_from_spec(s);s.loader.exec_module(review)
asset=LANE/'integration/candidate-library/veteran_prepared_png.glb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(asset)=='e44ac2c334169825e95b99213b0c53d6957cb7ff3b5c10df905f7567d3ebc973'
model=review.library.read_glb(asset);surface=review.ActualTargetSurface(model,[0]);r=surface.evaluate(.9)
assert r['nonadjacent_region_triangle_pairs']['R_hand__head']==4,r
names={n.get('name'):i for i,n in enumerate(model[0]['nodes'])}
w=review.profiles.pose_world(model[0],surface.tracks,.9,surface.parents,surface.order)
r['joint_origins_metres']={name:list(w[names[name]].translation) for name in ('R_Hand','R_Forearm','R_Upperarm','Head')}
r['actual_target']={'file':str(asset.relative_to(REPO)),'sha256':sha(asset)}
r['review_source_sha256']=sha(p);r['status']='real_veteran_v3_four_pairs_reproduced_before_source_edit'
(HERE/'veteran_v3_defect_reproduction.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'status':r['status'],'counts':r['nonadjacent_region_triangle_pairs'],'joints':r['joint_origins_metres']},indent=2),flush=True)
