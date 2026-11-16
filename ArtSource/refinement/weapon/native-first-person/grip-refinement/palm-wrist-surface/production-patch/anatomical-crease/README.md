# 掌背长折沟：解剖混权修复首件

**阶段结束，待 Root 实物 review、左右同步派生与原生验收。未写正式资源。**

候选 `right_hand_patch.glb` SHA256：`a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862`。仍为 5,018 三角，沿用健康 `3000b6be…` 面流和腕口；没有堆叠 687／9f。完整源对照继续是 Right v2 `3a1be1dd…`。

## 可见结果

- 原材质：[before](renders/dorsal_original_before.png) · [after](renders/dorsal_original_after.png)
- 中性材质：[before](renders/dorsal_neutral_before.png) · [after](renders/dorsal_neutral_after.png)

主长 V 形沟在两套图中均明显消除，掌背保留正常隆起，不靠贴图遮盖。四图同一实际源相机、PERSP、0.3m、closed grip@1、相同四灯／原点／动画和 KTX 解码像素；中性材质只作离线诊断。指节和远端袖口仍有源低面数特征，整体肤色／纹理与原生观感不在本阶段通过范围。

## 真正原因与修法

像素射线把折沟定位到 source faces1101 `[631,106,546]`／1075 `[106,37,364]` 及必要一环。这些点在源 open 解剖 frame 位于 MCP 关节之前，源546虽然主权重是 `R_Mid1`，其实际 forward 仍在 Mid MCP 之前约8mm；把所有 digit-dominated 顶点都当真手指保护，遗漏了真正掌背。

原631／546／37／364随卷指被拉10–14.8mm，造成掌背皮面长折痕。此次只改14个经独立解剖证明的源点及其法线拆点副本：种子点平滑移除94% finger spill 到 `R_Hand`，一环羽化，MCP前3–8mm渐隐；重新求 bind POSITION 保持实际 open 表面。主四点的 open→closed 变动降至约0.61／0.89／0.78／0.80mm，保留柔和皮面变化。旧3000的 open 表面最大分量误差约 `1.03e-7m`。

授权点是 `[37,87,106,350,364,438,546,631,728,729,836,837,1236,1349]`。独立验证从源实际 MCP 骨位、背侧深度 `<-0.01m`、forward 在径向插值 MCP 线前至少3mm及指定一环重新计算；836／837在 Index 中心外仅0.373mm，采用骨中心线向侧缘最近端点延伸的夹持语义，仍满足4.547mm前向余量。真正 MCP 远端指体／指腹和内掌没有放开保护。

## 检查

15项正／坏例测试通过。default／open／mid／closed：无新增相对源几何反转、normal/winding反向、位置焊接缝口、self或实际Dao问题，保护域实际LBS误差为0。self保持 `109/0/0/109`；继承坏法线角 `34/13/19/34 → 33/13/19/33`，并未新增豁免。UV、78骨／节点／REST／IBM／骨长／动画键／Grip及3张KTX保留。

本阶段首件已过源检查，无需定位返修。检查是有限姿态和现有非共面求交判据，不证明连续时间、SDK TBN或原生质量；Root须先审图再派生Left及装包。

## 复建

使用现有不可变缓存 `grip-refinement/right_hand_refined_v2.glb`，不依赖未来会被发布覆盖的 app Right；SHA必须等于3a。保持父3000 GLB不动。

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/build_anatomical.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/verify_patch.py --source ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined_v2.glb --candidate ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/right_hand_patch.glb --delta ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/patch_delta.json --output ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/verification.json
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/make_companion.py
python3 ArtSource/refinement/hand-poses/run_blender.py --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/render_anatomical.py
```

未改 app、正式模型、左手、刀、公共producer、Gradle、设备或Git。
