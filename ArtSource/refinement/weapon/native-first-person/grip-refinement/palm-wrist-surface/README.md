# 右掌背／腕口表面候选

**本阶段结束，等待对应 Root review。** 候选完成了局部真实表面光顺和四张同机位对照，但视觉变化有限，不把它写成整体手部质量通过或正式资源发布批准。

- [完整候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/right_hand_surface.glb)，SHA `687aea63eabfd4c08401a0a207f23e3740b9dad6348e9ebd6b7cce61f1c31e9e`，5,598 面。
- [ROI 变更与来源映射](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/roi_delta.json)／[制作清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/manifest.json)／[实际三姿态核验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/verification.json)。
- 固定机位对照：[掌背改前](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/previews/before_dorsal_back_closed1_0.3m.png)／[改后](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/previews/after_dorsal_back_closed1_0.3m.png)，[腕口改前](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/previews/before_wrist_cuff_closed1_0.3m.png)／[改后](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/previews/after_wrist_cuff_closed1_0.3m.png)。

## 范围

源为已接受 Right v2 `3a1be1dd…`，4,936 面；候选为 5,598 面，低于 8,000 面限制。只改两个 ROI：掌背硬脊 16 个原顶点／54 个源面，以及手邻第一袖口带 51 个原顶点／125 个源面。新增 352 点全在这两个范围。掌腹、指腹、指骨曲线、default、`grip@0/0.5/1`、腕、Grip、骨长、78 IBM、收口、材质和三张 1536² KTX 都保留。

这是实际形体修改：64 个原顶点做受限曲率圆化，其余新点来自局部共形细分与 UV／权重插值。UV 和既有权重数据对原顶点保持；新增点的插值来源、父面和边界均在 `roi_delta.json`。源没有 TANGENT，因此本轮不伪称端侧切线通过；UV chart 和贴图不变，MikkTSpace 仍待运行端确认。

## 动态与碰撞守门

35 项核验通过。default 与 `grip@0/0.5/1` 的非 ROI 原皮肤误差为 0；ROI 的离旧 parent 面最大约 1.954／1.965／1.973 mm，属于声明的造型位移。对新增点先在三姿态拒绝高混合权重边：未变形插入残差最多约 0.146／0.137 mm。完整映射后的 self／dao face-pair 集合无新增，core 最大深度仍为 open 11.077612、mid 4.880923、closed 0.092522 mm；open／mid 的旧穿入、closed 的 109 对继承表面交叉（Thumb–Index 47、Mid–Ring 62）仍在。

源有既存缺 TANGENT、bind 反法线角点和三姿态的坏面，候选没有新增。细分会改变边长和 dihedral 分布，统计下降只能说明几何分布变平，不能替代视觉判断。

## 四图判读和限制

所有图使用实际 KTX level 0 解码像素、同一 closed@1、同一 50 mm 相机／四灯；相机离**源 ROI 焦点** 0.3 m，并非 Grip 距离。中性 45 W 补光只是让掌背可读，前后一致。掌背长脊仍可见，只是折角减弱；腕口第一带更圆顺，但轮廓改善也有限。源腕口硬边、掌背低多边形折面、远端收口与整体材质限制仍保留。

这是一份供 Root 评审的 Right 候选，未改正式 app 或公共资源。Root 若接受这份形体，再以它统一静态重建 Left；本轮不派生 Left，也不把离线图或数值守门当作 PICO 运行验收。

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/verify_surface.py
```

旧源、dao、Right v2 与所有当前正式资源保持不动。正式 app／构建／Emulator／Git 仍由 Root 负责。
