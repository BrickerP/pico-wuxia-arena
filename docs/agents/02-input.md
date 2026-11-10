# 精修手部握持与角色穿插

## 本轮目标

解决真实角色手指、非持刀手与刀柄／护手之间的明显穿插，进一步改善原生Tripo姿态的握持自然度。

## 责任与文件

本会话负责 ArtSource/refinement/grip/ 候选生产脚本、校准数据和制作近景，以及本文件。现有 prepare_character_library.py、motion_library.json、library 与app运行模型由主控统一发布，避免与人物精修会话同时覆盖。

## 已有基线

三名角色各有78骨、8动作资源。青衫与玄甲已完成握点平移，仍有约9.79mm／7.47mm的残余峰值径向代理，平均深度与深样本增多的取舍已有报告。只移动刀柄不足以完成手指适配。

## 本轮工作

- 以最终实际蒙皮模型做指面、刀柄、护手和非持刀手检查，覆盖native slash1.55–3.4秒、2.117秒接触以及步法／受击姿态。
- 利用各角色自己的Tripo骨架与原生姿态，在握持对齐范围内产生可复建的局部指姿校正候选，保持手腕与刀路时标可追踪。
- 保留原始Tripo输出。人物网格、骨长与蒙皮权重继续沿原源，必要的绑定质量缺陷先量化并提交主控选择Tripo重绑方案。
- 同时评估接触覆盖、悬空间隙、径向交叠和视觉自然度。提供同机位before／after近景及动作小片段。
- 使用当前三角色做候选，新的高精角色就绪后由主控安排适配。当前不提交收费任务。

## 交付与审核

输出候选目录与清楚的发布步骤，原始与派生姿态可复建。只在主仓库工作，不动其他会话文件，不提交或推送，不创建副本。制作可用Blender离线处理，设备与实际视口由主控统一操作。

30分钟内交付一个阶段，遇到骨架或原生姿态的真实限制写清证据，不用持续等待维持状态。

## 本阶段交付

**阶段结束，等待主控 review。本回合完成后直接结束。** 已在 `ArtSource/refinement/grip/` 交付三角色可复建候选、校准数据、实际蒙皮审计和同机位制作近景。发布仍由主控统一执行。本轮费用 0，原始 Tripo、公共 prepare 脚本、library 和 app 资源保持本会话接入时的内容。

候选采用本轮批准的局部指骨旋转方案，每节校正向量上限 18 度。最终保留每角色 78 骨、8 动作，原节点/rest transforms、骨长、蒙皮权重、逆绑定、网格、材质、原 buffer 和关键帧时间输入均受验证。65 个源姿态中，非指骨世界矩阵分量最大差为 0，手腕与刚性刀具原有时标保持。修正数据仅追加至指骨旋转输出。

### 审核实物与复建

- [候选、方法与发布步骤](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/README.md)
- [三角色校准与固定哈希](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/calibration.json)
- [65 姿态右手测量](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/report.json)与[实际刀身／左手审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/left_weapon_audit.json)
- [近景相机、原生时间与最终 GLB 哈希清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/render_manifest.json)

| 角色 | 候选 | slash 原生 2.117 秒的峰值径向代理前→后 | 同机位右手近景 |
| --- | --- | --- | --- |
| 试刀客 | [base.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/candidates/base.glb) | 2.407→0.162 mm | [对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/base_right_before_after.png) |
| 青衫护院 | [indigo.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/candidates/indigo.glb) | 9.793→1.569 mm | [对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_right_before_after.png) |
| 玄甲守擂 | [veteran.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/candidates/veteran.glb) | 7.467→6.475 mm | [对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_right_before_after.png) |

三角色平均径向深度均下降，大于 2 mm 的顶点数量分别为 1→0、44→0、37→37。表面 3 mm 内样本分别为 10→16、77→74、64→81。青衫近距覆盖代理保留约 96.1%，需要结合图中握持自然度审核。以上是椭圆柄核与表面顶点的采样代理，样本数并非接触面积。

### 非持刀手与明确残余

实际刀身检查发现，柄核之外存在后段小指穿过刀身的情况。青衫新增 `L_Ring2` 局部 X -9 度，玄甲新增 `L_Pinky1` 局部 Z -18 度，两项均已写入最终 GLB 的全部 8 条对应动作轨道。65 个离散采样姿态均未增加左手确认交叉或 3 mm 近距样本。

| 角色 | 跨 65 姿态累计确认三角形交叉对前→后 | 单姿态峰值前→后 | 仍需审核的画面 |
| --- | --- | --- | --- |
| 试刀客 | 0→0 | 0→0 | 本次采样范围内左手未见确认交叉 |
| 青衫 | 299→275 | 43→33 | [3.133 秒残余小指](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_left_slash_3133_before_after.png)、[3.167 秒局部改善](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_left_slash_3167_before_after.png) |
| 玄甲 | 72→23 | 23→23 | [1.833 秒小指解除](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_left_slash_1833_before_after.png)、[1.55 秒掌部残余](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_left_slash_1550_before_after.png) |

玄甲 1.55 秒残余涉及 `L_Hand` 主导的蒙皮表面，当前限定指姿候选仍留交叉。进一步改变手掌与刀身关系或选择原生重绑方案需主控审核。当前结果不证明整段连续时间均无穿插，共面交叉也不在确认计数范围。握持自然度、掌指过渡和新的高精角色适配继续待审。

### 动作与验证

已交付 44 张 before、44 张 after、11 张近景对比、3 张六姿态板和 3 个九帧 slash 对比 GIF，帧源时间覆盖 1.55–3.4 秒，另包含 walk 与受击。可直接查看[试刀客片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/base_slash_before_after.gif)、[青衫片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_slash_before_after.gif)、[玄甲片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_slash_before_after.gif)。最终图片清单与最终候选哈希一致，已离线目检关键左右手画面。

实际执行 `verify_grip_candidates.py`，3 个正常路径和 21 个负向拒绝通过。独立验证每条修改输出等于 `normalize(source_q @ Qx @ Qz)`，以及输出类型、有限值、归一化、关键帧数量、追加引用和精确左手关节范围。青衫与玄甲完成最终哈希锁定回放。独立代码复审发现的回放哈希锁与旋转输出验证问题已修复，复审通过。Blender 渲染、脚本语法及差异检查通过。

所有产物均为离线候选，实际应用发布与设备观感由主控统一验收。本会话按阶段交付结束，主控可依据上述实物选择接受局部改善，或另派剩余掌部／小指与绑定关系的后续修正。

## 主控review与下一阶段

主控已查看持刀手同机位图和玄甲1.833秒、青衫3.133秒残余图，接受本阶段指姿的局部改善接入正式producer。指标代表离散代理与交叉采样，掌指自然度和残余刀面穿插继续待修。

下一阶段仅在offhand子目录制作slash的非持刀侧局部腕／必要前臂与手指修正，优先青衫3.133／3.167秒与玄甲1.55秒，采用平滑起止和完整关键姿态检查。右手与刀具轨迹继续固定，原rest、骨长与skin保持。新候选独立评审后由主控统一接入现有制作入口。

## 非持刀侧局部腕／前臂阶段交付

**阶段结束，交主控 review，本回合直接结束。** 新产物全部位于 [offhand 候选目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/README.md)。输入固定为上阶段已审核的 `grip/candidates` 哈希，保留上阶段 candidate/calibration。当前正式 library 已由主控发布时，仍使用固定候选基线。

### 最终实物和参数

| 角色 | 新候选 | slash 唯一修改 | 包络起点／全幅起点／全幅终点／终点 |
| --- | --- | --- | --- |
| 青衫 | [indigo.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/candidates/indigo.glb) | L_Hand 局部 X +8° | 1.80／2.00／3.40／3.60 秒 |
| 玄甲 V2 | [veteran.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/candidates/veteran.glb) | L_Forearm 局部 Z +4° | 1.50／1.55／1.72／1.95 秒 |

原生运动继续播放，校正右乘到原生局部四元数。全部原关键帧保留，局部窗口加入 60 Hz 与四分之一抬升点采样，窗外校正为零，源动作范围仍为约 0.033333–6.6 秒。原 rest、骨长、skin、权重、逆绑定、网格和其他七动作均保持，右手与刀具轨道保持原语义。玄甲允许的左腕位置变化峰值为 15.833 mm。

玄甲初版 +12° 腕姿在提前抬手 1.3–1.5 秒增加交叉，已退回并保留 [拒绝证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/rejected_wrist_audit.json)。最终 V2 将修改缩为上述 4° 前臂局部窗，完整审计未见新增交叉回归。导出 LINEAR 轨道为 C0 连续采样近似，接缝斜率已记录，解析余弦包络的零导数不作为导出轨道的严格 C1 保证。

### 密集审计与剩余边界

[独立审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/audit.json)检查 1–4 秒的 120 Hz、四分之一抬升点和接缝 ±1 ms，青衫 370 个姿态、玄甲 373 个姿态均未增加确认交叉。

| 指定 1.55–3.4 秒范围 | 青衫 | 玄甲 V2 |
| --- | --- | --- |
| 密集采样数 | 229 | 230 |
| 累计确认非共面三角形交叉对 | 1100→0 | 44→0 |
| 采样左手顶点到刀面最小无符号距离 | 2.428 mm | 4.589 mm |
| 3 mm 内顶点累计数 | 748→19 | 38→0 |

目标关键区间的离散交叉已清开，连续时间及共面交叠仍未获得全量证明。青衫约 1.325–1.408 秒、玄甲约 1.142–1.533 秒与 3.65–4 秒仍有原生交叉，位于本次目标范围之外并已保留审计。护手自然度、掌指观感和正式设备画面继续由主控审查。

### 同机位图与动作

- 青衫 [3.133 秒近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/indigo_left_slash_3133_before_after.png)、[3.167 秒侧面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/indigo_left_side_slash_3167_before_after.png)及[左臂护手全貌](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/indigo_arm_slash_3167_before_after.png)。
- 玄甲 [1.55 秒掌部](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/veteran_left_slash_1550_before_after.png)、[1.516667 秒过渡](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/veteran_arm_slash_1517_before_after.png)与[1.533333 秒过渡](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/veteran_arm_slash_1533_before_after.png)。
- [青衫十帧片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/indigo_slash_before_after.gif)、[玄甲十帧片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/veteran_slash_before_after.gif)与[相机／最终哈希清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/previews/render_manifest.json)。

已完成离线实际蒙皮渲染与目检，全部最终图对应青衫 `398e3aa9…`、玄甲 V2 `6379628c…`，完整 SHA 见 [calibration.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/offhand/calibration.json)。2 个固定哈希确定性回放、2 组包络检查与 6 个边界拒绝实际通过，独立核对旋转公式、窗外零修正、源时间保留、结构和右手／刀具一致性通过。源指姿候选仍为 `4516458a…` 和 `010e80a0…`。

主控可按 README 将本包络接入唯一 producer 的已审核指姿阶段之后，正式发布预期保留 22 个完整动作，另外两个 slash 各只更改上述一个左侧旋转轨道。本会话费用 0，阶段交付结束，后续正式发布与设备验收由主控统一执行。

## 主控正式发布指姿

已把已审核指姿接入prepare_character_library→prepare_character唯一生产链，绑定raw rig／grip源SHA与采样时刻，防换源误套旧校正。主控实际生成三角色body／带刀版本和索引，24份动作的语义签名及rest节点与审核candidate完全一致，再以分组发布同步app副本。生产身份见production_receipt.json，原Tripo源保留。剩余offhand第二阶段继续独立评审。

## 主控第二阶段review

主控查看青衫3.167秒左臂全貌与玄甲1.533秒过渡，接受V2的局部包络改进接入。当前游戏使用的slash源段为1.55–3.4秒，本段的离散交叉检查通过，完整6.6秒原生动作窗外仍有残余。正式producer接在指姿之后应用，输出与候选对照后再统一发布。下一轮待新主角色定型后重新适配其握持。

## 主控第二阶段正式发布

唯一producer已生成并发布非持刀手V2。三角色24份动作语义签名与对应审核candidate逐项相等，rest节点一致，indigo／veteran的slash仅增加已批准局部包络。分组同步app副本完成，生产身份见offhand/production_receipt.json。代理源身份重新量取，头／躯干曲线数值保持一致。当前游戏映射的1.55–3.4秒片段按离散蒙皮检查清开左手确认刀面交叉，完整原生动作与连续时间边界继续如上记录。

正式制作入口现会在全部角色与索引生成后，分组同步app/models/opponents，避免重建library后应用副本滞后。主控已实际重建并核对副本身份一致，源码、原始源与运行成品继续在同一仓库维护。

## 新主展示 60k 角色握持阶段交付

**本阶段结束，交主控 review，本回合直接结束。** 本次只在 [hero60k 候选目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/README.md) 制作一个新 base 候选。输入与主控指定一致，22,881,080 bytes、SHA `5ff55210dfbe9e10fbad1bf0d182424ae298bf009f9b845e9d307543302e0f3f`。原始 `refined-base60k/rig.glb`、`slash.glb` 的身份另记入校准，旧 indigo/veteran 候选与校准保持冻结。

### 实物与校准

- [单一审核 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/candidates/base.glb)，SHA `52f5ab67f8761dbb2b442367f245cf6ec669a497566295886072aaf3e6bba545`。
- [固定参数与刀路前后记录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/calibration.json)及[独立实际蒙皮审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/audit.json)。
- [右手侧面同机位图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/previews/base_right_side_before_after.png)、[左手 2.117 秒对照](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/previews/base_left_side_slash_2117_before_after.png)、[1.55–3.4 秒九帧片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/previews/base_slash_before_after.gif)。

先目检当前蒙皮近景，发现四指浮离刀柄，测量间隙约 22–31 mm。候选将现有 grip_frame 作局部 `(-40,-10,-10)` mm 平移，再校正 8 个右手指节的局部旋转，幅度为 1.5–4.5 度。保留原 body、78 骨 rest、骨长、skin、权重、逆绑定和 8 个动作时标，64 条右手指旋转输出发生变化。

刀具仅平移其刚性蒙皮 POSITION，`HandGrip_R` 非骨定位点同步更新，blade 朝向与尺度保持。实际刀尖路径最大平移 **42.42648 mm**，2.117 秒源标记保留。主控接入前须重新量取刀路／接触位置，旧 2.117 秒世界接触点不能继续沿用。

### 指面改善与明确取舍

| native slash 2.117 秒代理指标 | 基线 | 候选 |
| --- | --- | --- |
| 峰值径向交叠 | 10.715 mm | 8.333 mm |
| 最大指面近距间隙 | 30.768 mm | 0.164 mm |
| 3 mm 内顶点数 | 10 | 71 |
| 平均径向交叠 | 0.03110 mm | 0.13383 mm |
| 大于 2 mm 顶点数 | 6 | 34 |

侧面实图可见刀柄进入手指／拇指区域，但平均交叠和深样本增加。此候选改善了握持覆盖，仍有嵌入取舍，不能描述为各项全面改善。

### 新增回归与发布边界

独立 120 Hz 的 slash 1–4 秒实际刀身检查发现，基线左手无确认交叉，而候选新增 **45 个交叉姿态**，峰值 61 对，集中在 **1.258–1.45 秒和 3.833–4 秒**，主要涉及左拇指。当前战斗源段 **1.55–3.4 秒**与 **2.117 秒**仍无确认交叉，2.117 秒左手顶点到刀面的最近距离为 52.844 mm。

已明确标为 `requires_review_new_left_crossings_and_penetration_tradeoff`，当前不作为全动作改善直接发布。新增回归应由主控结合游戏实际源段、握持自然度和剩余动作选择后续处理。其他七动作未作全时域刀面审计，连续时间与共面交叉仍有验证边界。

新增回归已补实际同机位图，[1.366667 秒左拇指穿刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/previews/base_left_side_slash_1367_before_after.png)与[3.9 秒左手](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/previews/base_left_side_slash_3900_before_after.png)均对应同一候选哈希。前者可见基线左拇指清开，而候选刀刃穿过拇指，应作为条件审核或退回的直接证据。[条件审核标记](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/hero60k/previews/conditional_review.json)记录时刻与实物身份。

### 验证与出口

审核参数的确定性回放与源哈希漂移拒绝实际通过，原候选在失败用例中保持。独立骨架／body／skin／权重／逆绑定／动作时间、武器统一平移与定位点对齐检查通过，静态数学与职责范围复审通过。离线实际渲染、同机位相机及最终哈希已核对。制作范围与原始源保留符合本轮合同，公共 producer、manifest、library 和 app 均由主控统一发布，本阶段费用 0。

本阶段保留单一待审实物并结束，交主控决定是否接受该源段内的覆盖改善，或在后续阶段收紧平移与左手约束重新校准。

## 主控新主角review与正式接入

主控已查看右手侧面、左手2.117秒与3.4秒近景，接受当前游戏播放源段内的握持覆盖改善。已将grip_after_gltf与8节右手指姿接入正式manifest，绑定raw rig／slash、校准SHA与刀挂点摘要，其他角色同样封存挂点身份。源段外新增交叉与8.333mm峰值代理残余继续保留为下一轮动作精修项。

正式producer已生成并分组发布三角色，24份动作语义与各自审核candidate完全一致。所有骨骼rest节点精确一致；唯一非骨HandGrip_R因世界尺度补偿重组有约8.94e-8的矩阵分量差，几何最大分量误差约8.94e-8米。最终base SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641，身份见../final_production_receipt.json。01已对新主角源重新量取头／躯干代理。

## 参考流程review后的蒙皮修复提案

研究依据与整体路线见03的Kensei参考流程review。下一轮的部位修复建议从握点扩展到实际蒙皮，作为制作范围review输入。

先给头、躯干、左右臂／手、左右腿及衣物建立语义区域和分色正背视图。部位数据绑定模型SHA，模型重拓扑或索引重排后重新映射。核对权重是否把袖口、衣摆或腰带带向错误骨骼，并在当前78骨目标上做局部定向修正。

连续皮肤、关节过渡和衣物结构分别处理。相同位置的UV／法线缝顶点需要一致的变形关系；分件和焊接都先检查结构及贴图边界。原帖整手刚性绑定的示例需要为本项目的指骨活动重写，保留手指分节与合理关节过渡。

制作验收包含抬臂、前伸、转头、左右迈步和持刀关键姿态的前侧视图，并列出最大拉伸边、接缝间隙与最差顶点的骨骼影响。归一化、有限值和索引合法性继续作为数据检查，部位跟随与可见形变单列评审。
