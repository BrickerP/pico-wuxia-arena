# 三角色局部指姿候选

本目录是离线握持候选和制作验收产物。已审核局部指姿已由主控接入公共制作流程，设备画面验收与剩余offhand精修继续跟踪。

## 复建与发布

审核后的指骨校正记录在 `calibration.json`，来源为当前最终三角色 `ArtSource/tripo-warrior/library/{base,indigo,veteran}.glb`，每个输入都固定 SHA-256。指骨局部姿态采用原四元数右乘 `Qx @ Qz`，每节修正向量长度上限 18 度。原始 Tripo 输出和公共模型保持原路径。

正式重建使用 `ArtSource/tripo-warrior/prepare_character_library.py --manifest ArtSource/tripo-warrior/motion_library.json`，在原始源合并后应用一次校正，并生成一致的body、带刀版本和索引。生产语义与审核candidate的24份动作完全一致，见production_receipt.json。

下列回放和验证针对git节点4b07c7a中的原成品基线。当前library已应用校正，源哈希防护会阻止再次叠加。

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/build_grip_candidates.py -- --replay ArtSource/refinement/grip/calibration.json
python3 ArtSource/refinement/grip/verify_grip_candidates.py
```

`build_grip_candidates.py` 无参数运行会重新搜索右手指姿，并合入 `left_offsets.json` 中已核验的左手参数。参数回放适合主控审核后复建。输入哈希变化时停止，需重新评审校准。公共 prepare 脚本现在从原始Tripo和动作源重建，并在合并阶段单次应用本候选校正，回填library、索引和app副本的身份。三个候选只放在本目录，原始文件和公共脚本由各自负责人维护。

`verify_grip_candidates.py` 检查 78 骨、8 动作，原 buffer 前缀、节点、骨长所依赖的 rest transforms、蒙皮、逆绑定、网格、材质、时间输入和非指骨轨道保持。另以独立四元数计算逐键核对 `normalize(source_q @ Qx @ Qz)`，检查输出类型、有限值、归一化、关键帧数量及追加数据的引用。已执行 3 个正常验证和 21 个拒绝测试，覆盖 rest 节点、时间、原 buffer、错误四元数、非有限值、关键帧数量及未审核左关节。65 个姿态的非指骨世界矩阵分量最大差为 0。

回放在写候选前同时核对已审核的输出 SHA-256，漂移时失败，保持原校准记录。青衫和玄甲最终候选已执行哈希锁定回放并得到相同 SHA，试刀客保留首轮已验证产物。

## 右手结果

下表为 slash 原生 2.117 秒接触姿态的实际蒙皮表面顶点相对作者刀柄椭圆核的径向代理，单位毫米。它描述采样近距关系，接触样本数并非接触面积。完整 65 姿态覆盖 slash 1.55–3.4 秒以及 idle、walk、turn、三类受击和 fall，见 `report.json`。

| 角色 | 峰值交叠前→后 | 平均深度前→后 | 大于 2mm 顶点前→后 | 距表面 3mm 内顶点前→后 |
| --- | --- | --- | --- | --- |
| 试刀客 | 2.407→0.162 | 0.00558→0.00086 | 1→0 | 10→16 |
| 青衫护院 | 9.793→1.569 | 0.14655→0.01286 | 44→0 | 77→74 |
| 玄甲守擂 | 7.467→6.475 | 0.13675→0.11976 | 37→37 | 64→81 |

青衫近距样本略降至原来的 96.1%，需结合握持画面审核。玄甲仍保留明显核内样本，当前是局部改善候选。

## 非持刀手与残余问题

`measure_weapon_surface.py` 对最终实际蒙皮刀身、护手及非持刀手作离散三角形检查，并以边/三角形相交另行确认非共面交叉，见 `left_weapon_audit.json`。它覆盖 65 个姿态，尚未证明连续时间段和共面接触均无交叠。

| 角色 | 跨采样累计确认三角形交叉对前→后 | 单姿态峰值前→后 | 3mm 内左手顶点累计前→后 |
| --- | --- | --- | --- |
| 试刀客 | 0→0 | 0→0 | 0→0 |
| 青衫护院 | 299→275 | 43→33 | 224→213 |
| 玄甲守擂 | 72→23 | 23→23 | 53→13 |

青衫 `L_Ring2` 局部 X 修正 -9 度。3.133／3.167 秒附近的小指仍有刀身交叉。玄甲 `L_Pinky1` 局部 Z 修正 -18 度，1.833 秒原交叉解除，1.55 秒仍有手掌主导表面交叉。每个采样姿态的交叉数与近距样本数均未增加。进一步处理玄甲手掌需主控评估握持关系或绑定方案，当前保持手腕与刀路原值。

## 实物复核

`previews/render_manifest.json` 绑定候选哈希、相机与原生时间。三角色各有左右手同机位对比、六姿态板和九帧 slash 对比 GIF。优先查看 `indigo_left_slash_3133_before_after.png`、`indigo_left_slash_3167_before_after.png`、`veteran_left_slash_1833_before_after.png`，以及玄甲 1.55 秒残余视图。GIF 只显示所列离散姿态。

新模型分辨率、指面光顺、掌指过渡和真实游戏观感继续交主控审核。当前费用为 0，无远端生成任务。
