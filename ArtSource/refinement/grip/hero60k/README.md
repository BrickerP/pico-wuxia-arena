# 新主展示角色握持候选

阶段产物为单一待审候选，审核状态为 `requires_review_new_left_crossings_and_penetration_tradeoff`。本阶段结束，正式发布由主控选择。

## 固定基线与变化

输入为新主展示 base，22,881,080 bytes，SHA-256 `5ff55210dfbe9e10fbad1bf0d182424ae298bf009f9b845e9d307543302e0f3f`。原始 rig/slash 来自 `ArtSource/tripo-warrior/refined-base60k/`，各自哈希记录在 `calibration.json`。

候选 `candidates/base.glb` SHA-256 `52f5ab67f8761dbb2b442367f245cf6ec669a497566295886072aaf3e6bba545`。握持局部偏移为 `(-40,-10,-10)` mm，8 个右手指节作 1.5–4.5 度的小幅局部修正，映射到 8 个动作的 64 条旋转轨道。

原 body、78 骨 rest、skin、权重、逆绑定及全部动作时间保持。武器仅平移 POSITION，法线、索引和方向保持。非骨定位点 `HandGrip_R` 同步平移，其子定位点继续跟随。实际刀尖路径最大平移 42.42648 mm，before/after 路径在校准文件内。2.117 秒时间标记保留，平移后的实际接触位置由主控重新验收，旧世界接触点不可直接复用。

## 指面收益与取舍

以下是 native slash 2.117 秒的表面顶点／柄核径向代理。

| 指标 | 基线 | 候选 |
| --- | --- | --- |
| 峰值径向交叠 | 10.715 mm | 8.333 mm |
| 最大指面近距间隙 | 30.768 mm | 0.164 mm |
| 3 mm 内样本数 | 10 | 71 |
| 平均径向交叠 | 0.03110 mm | 0.13383 mm |
| 深于 2 mm 的样本 | 6 | 34 |

同机位侧面图可见刀柄进入握持指面，但平均深度和深样本增加。当前候选只体现覆盖改善与穿插之间的取舍，仍有残余嵌入。

## 新增左手交叉

独立实际蒙皮审计在 slash 1–4 秒以 120 Hz 检查。基线没有确认左手交叉，候选新增 45 个交叉姿态，峰值 61 对，集中于 1.258–1.45 秒和 3.833–4 秒，主要涉及左拇指。指定 1.55–3.4 秒与 2.117 秒仍保持无确认交叉，2.117 秒左手顶点至刀面最近距离为 52.844 mm。

上述新增回归与握持取舍均需要主控审核，不能按全动作改善直接发布。其他七动作尚未做完整连续时间刀面审计，离散无交叉也不构成连续时间证明。详细证据见 `audit.json` 和新增残余近景。

新增回归实图为 `previews/base_left_side_slash_1367_before_after.png` 与 `base_left_side_slash_3900_before_after.png`。1.366667 秒的侧面图明确可见候选刀刃新增穿过左拇指，条件状态另存于 `previews/conditional_review.json`。

## 复建与校验

从唯一主仓库运行。

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/hero60k/build_hero.py
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/hero60k/test_hero.py
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/hero60k/verify_hero.py
```

已实际执行审核参数确定性回放及源哈希漂移拒绝，失败时原候选保持；独立骨架／body／权重／时间检查、刚性刀具平移与定位点一致性通过。实际渲染和相机哈希见 `previews/render_manifest.json`。候选挂点参数在 `grip_after_gltf`，仅待主控在唯一 producer 中按当前源身份评估接入。本会话未修改公共 producer、manifest、library 或 app，费用为 0。
