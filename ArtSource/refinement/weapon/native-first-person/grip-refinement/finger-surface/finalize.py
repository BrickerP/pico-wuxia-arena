"""Seal a reviewable actual candidate packet from its executed checks and renders."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads((HERE/'finger_delta.json').read_text());v=json.loads((HERE/'verification.json').read_text());t=json.loads((HERE/'verification_tests.json').read_text());r=json.loads((HERE/'renders/render_manifest.json').read_text())
 assert v['passed'] and t['passed'] and r['status']=='twelve_matched_actual_renders_complete'
 assert d['candidate_sha256']==v['candidate_sha256']==t['candidate_sha256']==r['candidate_sha256']==sha(HERE/'right_hand_finger.glb')
 poses={}
 for label,row in v['poses'].items():
  c=row['contacts'];poses[label]={'source_self_pairs':c['source_self_pair_count'],'candidate_raw_self_pairs':c['candidate_self_pair_count'],'mapped_candidate_self_pairs':len(c['self_pair_delta']['mapped_candidate_source_face_pairs']),'new_self_parent_pairs':c['self_pair_delta']['new_source_face_pairs'],'removed_self_parent_pairs':c['self_pair_delta']['removed_source_face_pairs'],'source_bad_normal_corners':row['source_bad_normal_corners'],'candidate_bad_normal_corners':row['candidate_bad_normal_corners'],'new_bad_normal_corners':row['new_bad_normal_corners'],'inverted_faces':row['geometry_inverted_faces'],'original_position_LBS_max_component_error_m':row['protected_skin_max_component_error_m'],'new_inserted_seam_gap_m':row['inserted_reference_weld_new_pose_opening_m'],'dao_shape_count':len(c['actual_dao_pair_deltas']),'dao':{name:{k:val for k,val in detail.items() if k in ['source_surface_pair_count','candidate_surface_pair_count','new_source_face_pairs','removed_source_face_pairs','ROI_source_reference_interior_samples','ROI_candidate_interior_samples','ROI_source_max_depth_mm','ROI_candidate_max_depth_mm','new_interior_sample_labels','deeper_inherited_sample_labels']} for name,detail in c['actual_dao_pair_deltas'].items()}}
 files=['right_hand_finger.glb','finger_delta.json','build_finger.py','make_companion.py','decode_manifest.json','right_hand_finger_decoded.glb','verify_finger.py','test_verify_finger.py','verification.json','verification_geometry.json','verification_tests.json','inspect_roi.py','section_diagnostics.json','anatomical_sections.png','anatomical_roi.png','render_finger.py','render_guides.json','assemble_review.py','finalize.py','renders/render_manifest.json','renders/comparison_manifest.json']
 packet={'status':'technical_pass_visual_review_required','source_sha256':d['source_sha256'],'candidate_sha256':d['candidate_sha256'],'candidate_total_triangles':d['candidate_total_triangles'],'candidate_added_vertices':len(d['candidate_added_vertices']),'selected_curved_geometric_edges':d['selected_geometric_edges'],'source_positions_UV_weights_joints_exact':True,'all_original_normals_exact':False,'only_original_normal_changed_vertex_ids':d['original_normal_changed_vertex_ids'],'normal_repair':d['normal_repair_proof'],'tests':{'passed':t['passed'],'tests_run':t['tests_run'],'protection_violation_negative_case':t['protection_violation_negative_case']},'poses':poses,'visual_review':{'assessment':'Local side contours are slightly rounder; the overall PIP/DIP faceting remains visible. The original and neutral0.3m comparisons are provided without claiming native or overall hand-quality acceptance. Root visual review is required before any Left/formal integration.','original_materials_or_textures_changed':False,'distance_m':.3,'matched_camera_per_pose':True,'source_before_images_reused_only_after_camera_asset_pixel_hash_checks':True,'panels':['renders/open_comparison.png','renders/mid_comparison.png','renders/closed_comparison.png']},'frozen_previous_candidates':['attempt1/right_hand_finger.glb','before-normal-repair/right_hand_finger.glb'],'files':{name:{'path':str((HERE/name).relative_to(REPO)),'sha256':sha(HERE/name),'bytes':(HERE/name).stat().st_size} for name in files},'limits':v['limits']+['No formal assets, Left derivation, app, SDK coordinates, device operation, Git, producer or lighting changes. Offline render uses the inherited source comparison lighting.']}
 (HERE/'handoff.json').write_text(json.dumps(packet,indent=2)+'\n')
 readme=f'''# Right 指背／指侧曲面首件

实际候选已制作并通过数值检查，等待 Root 实物 review；未替换正式资源。局部指侧轮廓略圆顺，但 PIP／DIP 大折面仍可见，不将新增面数、像素变化或技术检查通过作为整体观感通过。

- 唯一源：a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862。
- 完整 GLB：`right_hand_finger.glb`，SHA `{d['candidate_sha256']}`，{d['candidate_total_triangles']:,} 三角（源 5,018，预算 9,000）；新增 {len(d['candidate_added_vertices'])} indexed corners／{d['selected_geometric_edges']} 条几何曲边。
- 原 2,867 个位置、UV、JOINTS 与 WEIGHTS 逐值不变，内掌／握柄指腹、拇指支撑、已通过的 14 点掌背混权、腕口、原点米制、78 骨／IBM／Grip／动画及 3 张原 KTX 保持。
- **原法线并非全部不变**：仅原 Pinky 指侧 1475 在真实 MCP 远端 15.325 mm、背侧高度 5.755 mm 的合法域内旋转 4.00164°。其新方向同时服从四姿态全部相邻子面的几何；其余原法线逐值不变。完整证明在 `finger_delta.json` 与独立 `verification.json`。

## 解剖与制作

先用实际 grip0 的四指 MCP／PIP／DIP 骨中心及三角拓扑定位最近骨段 capsule，排除 Thumb、MCP 近端、指腹与掌内区域；末节没有 tip 骨，20 mm 延长仅界定采样范围，不伪称真实骨位。`anatomical_roi.png` 展示实际骨与源拓扑；`anatomical_sections.png`／`section_diagnostics.json` 给出八个实际 PIP／DIP 横切面。

在合法源边上按两端实际 open 法线与局部几何法线构造 PN cubic 中点，曲率偏移最大 {d['open_added_displacement_mm']['max']:.3f} mm、平均 {d['open_added_displacement_mm']['mean']:.3f} mm，改变平面边的轮廓。原控制点不平滑、不移动；关节起伏沿源面保留，没有拟合成圆管。新增 UV／四骨权重按原父面 barycentric 插值，所有相邻面共形分裂，UV split 几何缝保持闭合。唯一原 normal 1475 的必要修复按四姿态全部 incident 子面求一致方向，未翻面或隐藏背剔除。

首件 013f 发现父面 494 子面反向、71／673 原角 normal 冲突及 [120,310] 新交叉；保留这些父面和 [204,299] 旧交叉父面的所有源边，逐对恢复原交叉集合。修后 060a 的 692／1475 存在真实共享角 normal 冲突，几何健康；Root 追加授权后对合法非保护 normal 1475 做必要修复。失败实物及原报告分别完整封存在 `attempt1/`、`before-normal-repair/`，不冒充当前通过图。

## 已执行验证

{t['tests_run']} 项 happy／bad-case tests 全通过，四姿态 default／open／mid／closed 全部独立重算。无新增几何反向、坏 normal、缝口、self parent-pair、Dao parent-pair、内部样本或穿入加深；全原位置实际 LBS 最大误差 0。保护区坏例实际改内掌原点 521 的 X 1 mm 被拒绝；伪造该点 normal 改动授权也被拒绝。UV、权重、Grip 改动与伪造解剖 ROI 的负例均包含。

闭握／default 旧 self **109 对全部保留**；细分后的 raw pair 计数为 {poses['1.0']['candidate_raw_self_pairs']}，映射后仍 109，新增与移除父面对均为空。open／mid self 为 0。13 个真实 Dao shape 的所有父面对集合保持，旧 open／mid 的 core 132／64、cordwrap 114／67 及 open ferrule 19 等继承问题明确保留；不能当作握持整体无穿入。逐对集合和各区域 inside 数据在 `verification.json`。

## 0.3 m 同机位图

- [open 对照](renders/open_comparison.png)
- [mid 对照](renders/mid_comparison.png)
- [closed 对照](renders/closed_comparison.png)

每组上排为原材质、下排为 neutral；左为 a980 源、右为当前候选。共 12 张原始图在 `renders/`。原材质来自当前真实 GLB 的原 3 KTX 解码，未改色、roughness、贴图或灯光；6 张 before 只在源资产、像素 SHA 与相机矩阵全等后复用，6 张 after 由当前候选重新渲染。相机为透视、距 source 固定 finger ROI 0.3 m；同姿态两阶段完全同机位。

以上为离线 GLB／数学 LBS 与 Blender 图，不证明连续时间、Spatial SDK TBN、原生设备观感或性能。Root 看图接受前不派生 Left、不装包。

## 复建与验证

从仓库根目录运行，所有输出仅写本目录。Blender 必须走现有序列锁。

```sh
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/build_finger.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/make_companion.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/inspect_roi.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/test_verify_finger.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/verify_finger.py
python3 ArtSource/refinement/hand-poses/run_blender.py -b --factory-startup --python ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/render_finger.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/assemble_review.py
python3 ArtSource/refinement/weapon/native-first-person/grip-refinement/finger-surface/finalize.py
```

完整带 SHA 收件入口：`handoff.json`。未修改正式左右手、app、SDK 坐标、刀、公共 producer、设备或 Git。
'''
 (HERE/'README.md').write_text(readme);print('SEALED_PACKET',d['candidate_sha256'])
if __name__=='__main__':main()
