# 原生右手指缝与末端支撑返修 v2

**本轮阶段结束，等待对应 Root review。** v2 完整实物、同机位三图及独立验证已完成，四遍终审为 `APPROVE_FOR_ROOT_NATIVE_REVIEW`，无阻塞项。可接现有 PlayerHands 进行原生运行评审，正式 app 资产未替换；Root 仍负责运行、设备与发布验收。

[固定收件索引](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/handoff_v2.json)。

- [完整 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined_v2.glb)：SHA `3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0`，2,517,124 B。
- [相对 0c44 的骨姿 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/pose_delta_v2.json)／[制作输入与自检](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/manifest_v2.json)。
- [独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/verification_v2.json)／[三视图 review](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/review_v2.json)。
- 实际 KTX 0.3 m：[正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews_v2/grip_0.3m_front.png)／[反面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews_v2/grip_0.3m_back.png)／[斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews_v2/grip_0.3m_oblique.png)。

## 可直接接入的原生入口

Root 选择替换 `app/src/main/assets/models/player_hands/right_hand.glb`，消费者仍为 `PlayerHands.kt` 的 `asset://models/player_hands/right_hand.glb`。保留 identity `RightGripRoot`、单蒙皮实体／骨架、唯一 `grip` 动画 0→1 秒；默认 Rclosed＝新 `grip@1`，`grip@0` 原样，不需要修改 Kotlin 或识别。Root 负责正式源、构建、Emulator 与 Git，本路未实施这些操作。

本轮基线为已审 `0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef`，正式 dao 仍为 `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0`。v1 的所有实物、图像及审计保持冻结。

## 改了什么

只改 Pinky1／2／3 的闭握 rotation。先用确定的 Pinky1 约 2° 外展分开中节，再用一次受约束的三节联动收指腹，主要补 PIP 弯曲，不是只将 Pinky3 折钩。实际骨链方向中 PIP 约 21.15°→42.69°，末端方向代理约 27.16°→29.07°；这些是骨链代理，不是生理解剖测量。

Root 已允许必要最小局部几何／权重调整；本轮纯骨姿已达到指缝与支撑目标，故**实际没有修改网格或权重**。POSITION／NORMAL／UV／JOINTS／WEIGHTS、拓扑、78 骨／IBM、骨长与节点 T/S、腕／Grip／Base／Tip、尺度／父级、材质与三张 1536² KTX 字节均保持。原无 TANGENT 的契约未改变；开／中／闭没有新增面退化或法线方向负变。

Thumb1／2／3 及其余非 Pinky 共 12 指骨的 default／curve 保留，213 个 Thumb 和 160 个 Index 主导皮面点实际位移为 0，Thumb→Index 原 24 个近 1 mm 支撑样本 ID 全保留。原混合 Pinky 权重使 Ring／Mid 主导皮面局部随动最多约 1.5602／0.004541 mm，已列明，不声称所有其它皮面完全静止。左手未动。

## 接触与开／中／闭结果

| 项目 | v1 | v2 |
| --- | ---: | ---: |
| Ring／Pinky 新增真实非邻接交面 | 10 对 | 0 对 |
| 固定 24 个 P3 掌侧点到绳面中位距 | 7.196 mm | 2.216 mm |
| 同掌侧区域近 3 mm 样本 | 0／24 | 17／24 |
| 掌侧最近／P95 距离 | — | 1.392／3.663 mm |
| 全 P3 的 200 样本到绳面中位距 | 18.843 mm | 11.454 mm |

固定掌侧区域用同一原 source face／重心样本，未按新权重重分类。指背等全 P3 数据也保留；不把整个指表面都称为接触面，不将 3 mm 工作参考冒称真实接触压力。实际三图用于判断顺柄弧线、指缝和支撑观感。

独立审计逐姿态比较完整 face-pair 集合，排除了真实 position-weld 的合法相邻面：open／mid 的 digit 和静态掌面交叉均 0；closed 原 10 对归零，Thumb／Index 47 对和 Mid／Ring 62 对等既有集合保持，**所有新增 pair 集合为空**。受 Pinky 影响的全部面（含混合 Ring／RHand）与静态掌面没有新增穿掌，不只是比较净数量。

固定 DAO 的对照中，open 原有 core 最大 11.0776 mm／187 样本，mid 原有 4.88092 mm／45 样本，closed 保留 Index 的 0.092522 mm／2 极浅样本。v2 三态都没有新增或加深这些侵入，Pinky 三态 core 均为 0。不能由 closed 改善声称整条 clip 绝对清核；默认装备侧仍取 closed@1，Root 验真实装备／松开语义。

## 图像与验证范围

仅一个 Blender 进程、两线程，单次三图；相机、镜头、光照、材质设置与 v1 完全相同，手刀根 identity、比例不变。像素来自 v2 实际未变 KTX level 0 和正式 dao 的实际 KTX 解码，fresh companion 保 v2 全部非 image 语义／41 个视图，未复用旧姿态网格。新图记录在 `previews_v2/render_manifest.json`。

三视图独立终审确认：小指沿柄圆周自然收回，Ring–Pinky 指缝连续可读，无折钩、融合、黑三角或新增穿插，拇指夹持与腕口未回归。剩余数毫米采样间隙不冒称压力接触，有限三帧也不证明完整连续曲线无碰撞。

这些是可接现有 APK 的制作候选，不是已安装运行证据。肤色／原腕口不规则边／源手部折面及近端 cap 裁边限制保留，Root 在 PICO Emulator 实际手姿与光照下复核；未改 SDK、手势、左手、正式资产或网页。

独立验证 PASS，腕平移／open 行／KTX 字节三个禁改负例均拒绝，另以“数量相同但换入新交面”的控制验证集合检查。复建和终验：

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/build_grip_v2.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/verify_grip_v2.py --candidate ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined_v2.glb --sha256 3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0
```
