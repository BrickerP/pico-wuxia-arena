# Common Grip 静态左手重建

**本阶段实物与检查完成，等待对应 Root review。** 沿用已冻结的 `d8e9…` 候选，11 月 15 日补齐真实 dao、自交、开／中／闭、手性、法线／绕序和实际三视图，没有再次重建或改变契约。

- [完整 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/left_hand_rebuilt.glb)：SHA `d8e9c3cb034f465e4527c13aad84e7ba283c3efcc537ab254c6295717cd1bbfd`，2,627,980 B。
- [复建脚本](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/build_left.py)／[变换及节点名映射](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/mapping.json)／[原制作自检](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/rebuild_manifest.json)。
- [独立实际核验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/verification.json)／[主线程四遍复核](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/result.json)／[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/handoff.json)。
- 实际 KTX＋原 dao：[正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/previews/left_closed_front.png)／[背面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/previews/left_closed_back.png)／[斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/previews/left_closed_oblique.png)。

## 必须原子切换的接口

新资产采用和 Right／dao 相同的 common Grip，最外 `LeftGripRoot` 为 identity，运行时 **handRootL＝G**。没有 B/C 内层抵消、旧腕偏移或 `DerivedHandGrip_L`。Root 应将完整候选换入 `app/src/main/assets/models/player_hands/left_hand.glb`，并在**同一次整合中**删除 `PlayerHandsPose.kt` 的旧左腕／派生 marker 转换，使左右手都直接消费 G。禁止只换其中一件；旧 C 配此资产会放错。

本路未改 Kotlin、正式 app 资源、右手、dao、公共 producer、设备、Gradle 或 Git。同级 `left-rebuild-math-review.py`／测试由 Root 独立维护，本路未改。

## 静态烘焙与真实皮肤

以正式 Right `3a1be1dd…` 为可信完整源，S＝diag(-1,1,1,1)。POSITION／NORMAL 反射 X，三角后两索引交换；节点和 78 IBM 共轭 S*M*S，translation 反射、quaternion 共轭、正 scale 保留。原 node ID、palette 顺序、skin 权重／索引、UV／材质／三张 1536² KTX 保持。全双侧骨名 R_↔L_ 交换且唯一，原 R 渲染／动画目标成为 L，未使用同名查找掩盖。

默认姿态继承源 Right 的 closed；唯一 `grip` 仍为 0=open、1=closed。旧 cf3203 的 open 字节／腕 ABI 已按 Root 新合同废止，不留兼容选项。新左手共 4,936 三角面，包含源 Right 的前臂收口；袖型与材质也复用 Right，而非旧左红色绑带。

独立实际求值 default 和 0／0.5／1：全部 primitive 顶点满足 **Lskin＝S*Rskin**，78 joint world、inverse-transpose NORMAL、翻绕序后的真实面积向量均误差 0；所有 local determinant 为正、无负 scale。实际手性 Right +0.959660、Left -0.959660。不是只验 Grip 原点。

源两 primitive 没有 TANGENT，实际数据不会冒称有切线。实现的 T.xyz 反射／w 反号经合成手性测试；UV/KTX 不变，运行时仍需正确 MikkTSpace。三图使用实际 KTX level 0 解码像素和 fresh 镜像后的 geometry／skin／animation，没有复用旧 cf 左网格。

## 原刀的实际检查

刀为未镜像的正式 `db28d426…`。13 个部件分别核拓扑，只有实际闭合有向 solid 作 signed 检查；没有假设护手／整刀对称。

| closed@1 | Right 源 | 新 Left |
| --- | ---: | ---: |
| core 入内样本 | 2 个 Index 浅点 | 2 个 Index 浅点 |
| core 最大采样深度 | 0.092522 mm | 0.093440 mm |
| Thumb／Mid／Ring／Pinky 核内 | 0 | 0 |
| 闭合护手／collar／ferrule／pommel 等入内或表面交叉 | 0 | 0 |
| 开放 cord 表面交叉 | 38 | 33 |

cord 有 1,442 条开放边，只报告 surface gap／crossing，不编造体积穿入。接触的微小非对称差异来自真正的原刀计算，不以 Right 镜像值代替。0.1 mm 是本次离散检查工作线，不是测量精度或零穿透声明。

开／中／闭全手 finite-triangle self 检查实际执行：open／mid 双方为 0；closed 双方同为继承的 **109 对**（Thumb–Index 47、Mid–Ring 62），新 Left 新增集合为空。已排除固定位置 weld 的合法邻接／UV seam；不把 109 对表面交叉夸称为体积穿透，也不称全手绝对无自交。

固定刀的旧 Thumb 侵入仍在：open R11.0776／L11.0676 mm，mid R4.88092／L4.87569 mm。closed 改善不代表整条曲线绝对清核。源掌背硬脊、腕口硬边、低多边形折面和近端收口质感也继承，仍需后续质量验收。

## 三视图与范围

主线程已看正／背／斜三张实际 3D 图：四指自然包柄，拇指／虎口不再出现旧左手横切进柄的薄片；拇指侧与左手手性一致，指缝可读，没有新增明显融合／折钩。材质、手刀比例、根坐标未用于掩盖接触。

单 Blender 进程、两线程，三图固定四灯；相机 X 对源 Right 机位作对应侧选择以看同一掌面／背面／拇指侧，**只选相机，未额外旋转手或镜像刀**。输入和实际相机矩阵见 `previews/render_manifest.json`。

28 项实际资产、损坏、tangent／winding 及实际 DAO 控制全部通过；companion／render 工具 5 测通过。只读资料和图像判定由主线程完成，代码生产任务并行，没有在 DeepSeek 不可用时偷换只读子任务模型。

本轮只批准供 Root 原子整合复核的资产实物，不代表 SDK 原始 ControllerPose 生理约定、PICO skinning、真实站姿／亮度或最终手部质量通过。Root 还会独立数学复审并决定是否同时换代码和资产。

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/verify_left_rebuild.py
```

复建入口 `build_left.py` 保持原样；本次续做未重跑重建或改变 `d8e9…`。候选、旧 Right 和原 dao 的起止身份均核对不变。
