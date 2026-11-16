"""Seal the matched199c/0295 pair after complete independent finite audits."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[7]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def item(p):return {'path':str(p.relative_to(REPO)),'sha256':sha(p),'bytes':p.stat().st_size}
def main():
 construction=json.loads((HERE/'construction.json').read_text());review=json.loads((HERE/'verification.json').read_text());contract=json.loads((HERE/'verification_contract.json').read_text());tests=json.loads((HERE/'verification_tests.json').read_text());mirror=json.loads((HERE/'verification_mirror_dao.json').read_text());baseline=json.loads((HERE/'verification_actual_baseline.json').read_text());actual=json.loads((HERE/'verification_actual_contacts.json').read_text());render=json.loads((HERE/'renders/render_manifest.json').read_text())
 assert all(x['passed'] for x in [review,contract,tests,mirror,baseline,actual]);assert render['status']=='six_actual_paired_closed_renders_complete'
 right=HERE.parent/'right_hand_joint.glb';left=HERE/'left_hand_joint.glb';rsha='199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64';lsha='0295c147673a5cf15b4265cbfcb83391d2fa399b8be778c54ecc789fc61c46f7';assert sha(right)==rsha==construction['source']['sha256'] and sha(left)==lsha==construction['candidate']['sha256']
 for report in [review,contract,tests,mirror,baseline,actual]:assert report['source_sha256']==rsha and report['candidate_sha256']==lsha
 actual_rows={str(st['time']):{side:{'self_raw':st['hands'][side]['position_weld_self']['count'],'total_DAO_surface_crossings':sum(c['surface_crossing_count'] for c in st['hands'][side]['components'].values()),'core_max_sampled_depth_mm':st['hands'][side]['components']['Handle core']['maximum_sampled_penetration_mm']} for side in ['R','L']} for st in actual['actual_unreflected_DAO_and_self']['states']}
 files=['left_hand_joint.glb','derive_left.py','construction.json','mapping.json','left_hand_joint_decoded.glb','make_companion.py','decode_manifest.json','verify_left.py','test_left.py','verification.json','verification_contract.json','verification_tests.json','verification_mirror_dao.json','verification_actual_contacts.json','verification_actual_baseline.json','render_pair.py','render_plan.json','renders/render_manifest.json','renders/comparison_manifest.json','assemble_pairs.py','finalize.py']
 packet={'status':'complete_matched_Left_ready_for_Root_pair_integration','pair':{'Right':item(right),'Left':item(left)},'candidate_triangles':construction['triangles_total'],'producer':'Frozen left-rebuild/build_left.py rebuild()/verify()/control_tests(), bound to199c by thin adapter; no second mirror algorithm.','independent_checks_passed':True,'tests_run':tests['tests_run'],'four_pose_mirror_LBS_normal_winding_joint_error':0,'protected_original_vertices':contract['protected_domain'][0]['protected_source_controls'],'protected_mirror_error_m':0,'full78_palette_same_order':True,'UV_weights_palette_and_three_KTX_exact':True,'common_Grip_identity_no_runtime_negative_scale':True,'source_BIN_prefix_exact':True,'self_and_mirrored_DAO':{pose:{'raw_self':row['raw_self_pair_count'],'mapped_inherited_self':row['source_parent_mapped_self_pair_count'],'new_source_pairs':row['source_parent_self_pair_delta']['new_source_face_pairs'],'removed_source_pairs':row['source_parent_self_pair_delta']['removed_source_face_pairs'],'mirrored_DAO_components':len(row['components'])} for pose,row in mirror['states'].items()},'actual_unreflected_DAO':actual_rows,'actual_Left_vs_correct_a980_Left':{'reference_sha256':baseline['reference_sha256'],'all_four_poses_passed':True,'source_correspondence':'Source vertex IDs remain; Left parent triangle vertices1/2 and their bary coefficients swap together.','new_or_deeper_inside':False,'new_or_removed_self_or_DAO_parent_pairs':False},'paired_closed_views':['renders/paired_closed_front.png','renders/paired_closed_back.png','renders/paired_closed_oblique.png'],'files':{name:item(HERE/name) for name in files},'source_review':item(HERE.parent/'verification.json'),'source_delta':item(HERE.parent/'joint_delta.json'),'frozen_reused_code':construction['frozen_reused_code'],'integration':'Root replaces Right199c and this Left0295 together, with the existing commonGrip wiring. No formal assets, app, coordinates, device or Git writes were made by this lane.','limits':review['limits']+['The actual unreflected DAO is not mirror symmetric; open/mid inherited penetrations and109 mapped self crossings remain disclosed.','No SDK TBN, continuous-time clearance, native device physiology, performance or whole-hand quality acceptance.']}
 (HERE/'handoff.json').write_text(json.dumps(packet,indent=2)+'\n')
 readme=f'''# 199c Right 配套静态 Left

匹配 Left 已完成，独立四态与接触审计全部通过；Root 已看左右共同握点的斜视图，作为局部关节开发候选。整体手部品质与原生验收不在本次通过含义内。正式资源与 APK 由 Root 成对整合。

| 资产 | SHA256 | 三角 |
| --- | --- | --- |
| Right 输入 | `{rsha}` | 6,222 |
| Left 输出 `left_hand_joint.glb` | `{lsha}` | 6,222 |

唯一生产输入是冻结的当前 199c Right。旧 d8／ecc Left 都被当前合同拒绝为替换品；ecc 只用于“正确 a980 Left”接触参考，另经过 a980 的独立镜像合同证明。

## 复用的产线

先读了 `anatomical-crease/left-derivation/derive_left.py` 的实际入口：只有 `--verify-only`，来源和“14点”检查绑定旧 a980，不能给它冒填新源。因此本目录薄适配器只绑定新输入、输出和源技术证据，直接调用冻结 `left-rebuild/build_left.py` 的 `rebuild`、`verify`、`control_tests`，不调用其旧硬编码 build 入口、不复制镜像实现、不改旧文件。三个冻结 producer／verifier／tests 的 SHA 在 `construction.json` 与 `handoff.json`。

`S=diag(-1,1,1,1)` 静态烘焙：P／N 反射X、三角绕序反转，node／IBM 采用 `S*M*S`，动画 translation／rotation 相应变换，R_／L_ 全双向重命名。全78 palette 索引顺序、UV、J/W、3张 KTX 保持，完整当前 Right BIN 是 Left BIN 的 exact prefix。`LeftGripRoot` 是 common Grip identity，无 runtime 负 scale、旧 C/B frame、额外腕 Offset 或派生补偿。

## 实际核验

- {tests['tests_run']} 项测试全过：复用冻结28项，再加5项当前源／旧Left拒绝／镜像bary来源控制。
- default／open／mid／closed 的全部 primitive 实际 LBS、逆转置 N、绕序面积向量、78骨 world transform 镜像误差全部为0。
- {contract['protected_domain'][0]['protected_source_controls']} 个保护原点逐态镜像误差0；全UV／权重／palette／3KTX逐值或逐字节保持。
- Right 与 Left 均实际证明 default 与 grip1 的 LBS、normal、拓扑完全相同；旧实际DAO审计的默认接触因此明确等同闭握，另一路基线与镜像DAO仍逐四态实算。
- Left＋同源镜像DAO 的13组件完整 face-pair 集合逐四态与 Right＋真实DAO 一致；self raw136／0／0／136，父面映射仍完整109／0／0／109，无新增、无移除。
- 对真实**未镜像DAO**另外独立测左右手，不假设刀具对称。Left 当前与正确旧 ecc/a980 Left 的四态完整父面对、inside 与深度比较，无新增／移除 crossing，无新增 inside 或加深。

旧源问题保持披露：真实未镜像DAO closed 总surface crossings Right48／Left43；Left闭握仍有2个继承 Index 核内样本，最大0.093440 mm，沿用已验0.1 mm浅点上限，其余闭合solid组件无cross／inside。Left open／mid 核内有限采样深度约11.067647／4.875685 mm，Right约11.077612／4.880923 mm；这是固定刀具下的继承状态，不能称“零穿模”。全部face-pair和样本证据见 `verification*.json`。

源父面对应在左侧必须同时交换 face 的1／2角和其 bary 系数，不能拿 Right 的原系数直接套反绕序 Left face。该规则有真实 GLB 非对称 bary 测试覆盖。

## Root 可看图

- [左右闭握正面](renders/paired_closed_front.png)
- [左右闭握背面](renders/paired_closed_back.png)
- [左右闭握斜面](renders/paired_closed_oblique.png)

共六张实际3D原材质图，Left 是新GLB，没有镜像像素。两手和同一未镜像DAO均处于 common Grip identity，只有相机依既有三机位作解剖对称观察；材质、配光、模型尺度没有改动。

## 复建与复核

从仓库根目录运行；只写本目录。输入 199c 不改，Blender 走既有序列锁。

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/derive_left.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/derive_left.py --verify-only
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/verify_left.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/make_companion.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/render_pair.py --preflight
python3 ArtSource/refinement/hand-poses/run_blender.py -b --factory-startup --python ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/render_pair.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/assemble_pairs.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/joint-loops/left-derivation/finalize.py
```

带SHA的固定收件入口是 `handoff.json`。本路没有修改199c／48e、正式左右手、02、app、SDK坐标、公共producer、设备或Git。
'''
 (HERE/'README.md').write_text(readme);print('SEALED_MATCHED_LEFT',lsha)
if __name__=='__main__':main()
