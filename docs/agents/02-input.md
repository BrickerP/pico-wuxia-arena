# 02 · 刀具造型材质与握持

## 最新用户目标与执行队列

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你主责现有dao的明显几何与材质升级及三角色握持。03收服装结构，05收头脸，08接实际攻击特效。

最新一轮不能只改roughness和金属factor。制作有实际倒角与截面的刀脊／刃口、刀尖过渡、护手铸造边、柄绳编织、端帽与有因果磨损。保持公共刀长和握点语义，握持接触区优先保护，确需变化给明确映射和可见对照，由Root重签。正常游戏视距的刀身反射和轮廓必须有可辨改进。现袖口微小候选与限制交03，继续武器队列，不等待其回复。

Root已开发接收 stage2 实体刀槽／刃脊方向，公共 producer 候选与新刀身份 pin 由 Root 统一处理。当前续项为右手握持 147／55／85 个既有相交手面的实际可见程度与柄核穿透深度，允许只交局部原指骨增量或手部接触几何修正。正常距离、近景、原始 IDs 与真实深度共同验收，保护当前三方向左手与 05 头脸／03 服装组合。

## 当前状态

**右手柄核接触修复进行中。** 最新十段动作三角色与新刀为冻结输入。实际闭合柄核量测已定位 base／veteran 约 11.5 mm 拇指穿入、indigo 约 2.9 mm 小指穿入，已开始有限静态指骨增量与局部接触几何候选。上一阶段刀形和十段库适配的实物、18 张对照与左手无新增交叉结果保留。

袖口结构后续交 03。[袖口现有实物及限制](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/README.md)和[机读 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/vertex_delta.json)可作为局部组件，当前只完成左侧灰棱约 1.5 mm 径向收细。12 mm 退腕、真实开口和布／皮边界仍待服装结构制作，保护集合也需要按实际手部语义细化。

## 上一轮成果与Root review

三角色握持和非持刀侧局部包络已进入统一producer。主角指面覆盖改善，仍有8.333mm峰值径向代理、深样本增加及源段外交叉。只调挂点和指骨不足以解决衣物／关节变形，本轮补部位级语义和权重审查。

## 文件所有权

负责 ArtSource/refinement/weapon/、现有ArtSource/dao内你明确新增的候选制作源与本文件。正式dao资源、角色producer与挂点校准由Root统一维护。衣物、头脸和其它会话目录保持。

## 本轮任务

1. 冻结 `current-bank` 新刀三角色、alignment、profiles 与原始 SHA。核验当前右指校准已单次烘焙，后续只使用明确增量。
2. 对真实闭合 `Handle core` 做内外分类与最近三角面深度，包含顶点、边中点和面心，报告最坏姿态、原 face／vertex IDs、骨支持与实际截面。开放缠绳单独记录表面交叉。
3. 优先每角色独立静态右指骨旋转，统一作用十段动作。若小范围残留来自接触表面，可试同拓扑局部 POSITION／NORMAL 修正，并保留完整 seam 组及机读 delta。
4. 复核真实柄核深度、各指残留、外绳或相邻指的自然贴靠、非邻接指面自交和可见闭合，保护左手／刀路／腕／挂点及非手部数据。
5. 交正常距离与手部正侧近景前后、柄轴截面、局部修正候选和独立验证。原 producer、正式资源及最终合成由 Root 维护。

## 审核产物

真实几何与纹理候选、正常视距和持刀近景、来源 SHA、部件和材质映射、玩家 Grip 入口、三角色装配及接触检查。量测区分结构合法、表面接触与实际可见收益，运行时观感由 Root 统一验收。

## 下游

Root 审核后统一更新刀具输入、装配身份和挂点校准，再组合 01 动作、03 服装、05 头脸与 07 光照。候选保留各自来源，按部件和数据映射交付。

## 共同执行约束

唯一工作仓库为 /Users/yupeng/projects/personal/pico-wuxia-arena。当前模型基线为main的cc12bf1，base.glb SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641。运行栈为Kotlin + PICO Spatial SDK6.1.9，终端Space Pro／OS6。

其他会话正在同一仓库并行。各自只修改责任范围，保留其他人的编辑。Git提交、分支、合入、共享构建、设备操作、实际截图与正式模型发布由Root统一负责。候选输出留在各自目录，library、app角色与公共manifest由Root发布。

本轮允许离线资产生成、渲染及专项制作检查。游戏整局自测继续后置。30分钟内交付首阶段实物，写明“阶段结束”、输入SHA、文件、效果、剩余问题与下一步建议后结束当前回合。遇到阻塞先交已做出的部分并写明具体阻塞，继续能独立完成的工作。用当前模型和已安装依赖推进，不为等审批或等待其他线程维持空转。

## 阶段回报

待执行会话填写。

### 部位分区与左腋首阶段交付

**阶段结束，交 Root review，本回合直接结束。** 已在 [deformation 产物目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/README.md)交付分区、缺陷清单、raw body-only 派生 rig、动画展示副本及可复建脚本。当前权重试验明确标为 **`blocked_cross_pose_strain_regression`**，结构合法但动态质量未过门槛，暂不接入正式 producer。

输入完整 SHA 为当前动画 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`、raw rig `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。raw／prepared 的 35,308 顶点、60,006 面同 ID，对应 POSITION、NORMAL、UV、索引、JOINTS、WEIGHTS 完全一致，重排为 identity。归一化矩阵、逐顶点／face 语义和来源身份见 [regions.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/regions.json)与[regions.npz](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/regions.npz)。

### 分区与实际诊断

已建立 14 个解剖区域和 5 类衣物假设，提供 [衣物覆盖正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_base_native_front.png)、[背面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_base_native_back.png)及[解剖中立正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_anatomy_neutral_front.png)、[背面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_anatomy_neutral_back.png)。解剖标签参考已有权重，衣物标签是空间假设，置信度与歧义另记，需结合实际画面复核，不能当作独立真值。

[缺陷清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/defects.json)包含原生 slash、左右迈步、受击、turn 及单独合成转头检查。4740 组重合点均涉及 UV 拆分，16 组有法线拆分，权重不一致为 0，位姿接缝间距为 0；远端手指与 Hand 影响在本次阈值下均为 0。手部保持诊断范围。

首个局部目标选左侧躯干腋下过渡，种子边 `[32080,32220]` 的 rest 长为 23.801 mm，`hit_side 0.35s` 达 63.865 mm。原因实验显示 `L_Upperarm` 的局部影响与该边伸长有关，但孤立转移也会影响周边应变，因此只保留有限拓扑邻域并锁定外圈作试验。

### 派生 rig 与前后实物

- [candidate_rig.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/candidate_rig.glb) 为原 raw body-only 派生，单一 skinned body mesh、原 PBR／UV、78 骨 rest／骨长与逆绑定保持，无 DAO、归一化包装或动作；SHA `66ebbb7513ec70672af6d48f3efb5bd0a81da55bfd42f61dc5b1ed40aaa3eeac`。
- [candidate_base.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/candidate_base.glb) 仅用于原动画同姿态比较，SHA `b1d8c11a2e0cae1406bc2bbbdad1e29c0545bd18da6155f056a9d5832e49fa01`。
- [candidate.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/candidate.json) 记录 5 个被改顶点 `29361、30818、32220、33044、33493` 的部位、原／新 palette、骨名与权重；仅把局部原 L_Upperarm 质量按最轻 25% 衰减转移到原有 Spine01，包含完整重合组，手部改动 0。
- 受击 [PBR 背侧对比](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/hit_side_0350_left_armpit_back_before_after.png)、[线框背侧对比](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/hit_side_0350_left_armpit_back_wire_before_after.png)，以及 [slash 2.117 秒 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/slash_2117_left_armpit_front_before_after.png)、[线框](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/slash_2117_left_armpit_front_wire_before_after.png)均为同姿态／同机位。

### 数值收益、回归与验证边界

| 度量 | 基线 | 最轻候选 |
| --- | --- | --- |
| hit_side 0.35s 种子边长度 | 63.865 mm | 56.283 mm |
| hit_side 区域最大伸长 | 40.064 mm | 35.078 mm |
| hit_side 区域 P95 伸长 | 33.292 mm | 31.152 mm |
| slash 2.117s 区域最大伸长 | 22.523 mm | 25.009 mm |
| slash 2.117s 区域 P95 伸长 | 22.175 mm | 24.263 mm |

四个试算强度均未通过跨姿态门槛，只保留最轻实物供审查。独立 [verification.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/verification.json)覆盖 179 个姿态，最大新增伸长为 **4.402 mm**。数据可证明局部受击拉伸减轻，也证明应变转移导致 slash 邻边恶化。PBR 正视存在前臂遮挡，观感改善细微，线框用于核对几何差异，当前不宣称衣物整体修复或可见品质已达到发布要求。

独立验证的结构部分通过，raw／prepared 权重数组一致、3483 个手部影响顶点保持、未选顶点保持、权重合法，接缝最大间距仍为 0，rest 蒙皮偏差约 0.00000696 mm，未新增源姿态相对翻面或零面积面。正常源检查及变更 rest／POSITION 的拒绝测试通过，分区源哈希漂移拒绝也已执行。动态部分明确失败并阻止发布，完整脚本、映射和拒绝证据均保留。

制作图的限制已核对，当前语义正背图有部分鞋端裁切，可用[带图例板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_base_neutral_legend.png)复核颜色和部位，足部视觉覆盖仍需补齐。前伸／抬臂／迈步及合成转头的基线检查已保留，完整候选 stress 短片本阶段尚未制作。`stage_rest_positions` 字段实际为归一化 GLB 场景根的模型静止坐标，米制，未包含运行时 Entity 的场景放置变换。

下一阶段建议以多姿态整片应变为约束求解衣物过渡权重，在确认连续衣物结构后再评估更宽邻域，而不是仅追求单边缩短。本会话费用 0，公共脚本、源模型、library、app 和其他会话文件保持各自所有权，正式整合由 Root 选择后执行。

## Root合入前审查补充

派生正式输入保持raw body-only格式，单一带蒙皮body mesh、原PBR／UV、78骨rest／骨长／inverse binds。文件不带DAO、全局归一化包装或动作。分色模型仅用于诊断，顶点变化提供新旧映射。

首阶段手部语义区域的权重改动为0，缺陷只诊断。每个实际修改顶点记录部位、源／目标权重与位置，交Root组合后复核。

Root以派生rig加01手姿统一重建。新target SHA触发旧校准时由Root复审重签，01随后复核实际手柄接触。

## Root首阶段review与续派

分区和缺陷定位接受，首权重候选因跨姿态回归及可见改善不足退回。阶段2补齐脚端分区图，以多姿态区域应变和语义影响为依据，最多三个定向候选，实际可见的尖刺／裂缝／拉花直接拦截。数值变化与可见性共同评审。当前状态为阶段2执行中，失败候选保留为研究证据。

## 阶段2回报

**阶段结束，交 Root review，本回合直接结束。** 实物、参数及剩余根因见 [stage2 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/README.md)。当前三个权重候选均为 **BLOCKED**，未进入公共模型或 app。

### 鞋端裁切已修复

已补齐 [衣物正背分区板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/semantic_base_full_neutral_legend.png)和[解剖正背分区板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/semantic_anatomy_full_neutral_legend.png)。实际 body 包围盒驱动相机，排除 DAO 并加 14% 留白，头、双手和靴端均完整。投影纵向约 0.0614–0.9386，[相机证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/full_body_camera_manifest.json)已记录。

### 有依据的部位选择与候选

[纹理／空间复核](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/source_defects.json)确认，旧腰胯和侧腿种子实际属于蓝色裤子，连续裤裆跨腿影响不能直接认定错误。本次只对实际灰色前衣摆 659 个顶点／504 个重合组做定向试验，没有删除对侧腿影响。

使用真实表面拓扑、锁定两圈边界、保留原关节支持集的区域图平均，仅生成 0.2／0.4／0.6 三种强度。每个候选改 251 个顶点，手部权重改动为 0，无新增关节影响或最终 top4 质量裁剪。源 raw／final 哈希分别仍为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6` 与 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`，同 ID 映射、raw body-only 格式与原 PBR／UV、78 骨 rest 合同继续满足。

- [候选清单与固定哈希](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/candidates.json)。三个子目录均有 `candidate_rig.glb`、`candidate_base.glb` 与逐顶点 `weight_changes.json`。
- [0.2 侧面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_020/slash_2117_side_before_after.png)、[0.4 正面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_040/slash_2117_front_before_after.png)，其余前／侧／后及 walk 对照位于 [制作图目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews)。

### 数据与真实可见性分开评审

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/verification.json)覆盖每个候选 579 个姿态。区域平均正伸长 RMS 为 1.5337→1.4879／1.4605／1.4518 mm，平均 P95 为 3.2823→3.1926／3.1526／3.1059 mm，最大 P95 增长仅 0.060／0.066／0.083 mm。这里没有以每条边完全不增作唯一门槛。

实际主要缺陷边 `[34287,34481]` 的两端都在锁定边界，三个候选均未编辑目标本身；slash 2.117 秒仍为 60.349 mm 长、19.248 mm 伸长。内部平滑的数字小幅改善不足以支持主要轮廓已修复，目检仍未证明足够可见收益。该边界／目标不一致是当前试验的明确剩余原因，不能以平均小数字宣布通过。

三个候选还分别有 1／2／5 个最大单姿态法线反向信号，0.2 相关面并非无穷小，0.6 最大源面约 47.5 mm²，并有新增拉普拉斯尖刺候选。它们需要具体 pose 图确认，当前不宣布已看见裂缝，也不据此放行。结构与动态分别记录，raw／prepared 权重一致、手部及未选区域不变、原支持集保持、rest／skin／逆绑定／动画保持，重合组接缝为 0，未新增零面积面；正常与变更输入拒绝检查通过。

最终实图已完成每候选六张同机位 PBR 对照，共 18 张；[0.6 正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_060/slash_2117_front_before_after.png)与[0.6 侧面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_060/slash_2117_side_before_after.png)也基本不变，较大侧腰鼓包仍在。0.6 的最低相对三角面积比仅 3.54%，需保留挤压风险。纹理与空间选区尚未证明它对应实际相机可见折痕，`gray_front_hem` 仅作为本次数据标识；后续应先从实际问题视图拾取 face ID 与可见性，再重定编辑内部和锁边。新增最坏风险姿态未扩展渲染，当前不提供发布通过结论。

本阶段保留三个有限试验并结束。下一步应先把实际可见目标纳入经确认的连续衣物内部、重新定义锁定边界，再做区域多姿态求解，并区分源网格／纹理折痕与蒙皮变形。本会话费用 0，公共代码、library、app 和其他会话产物由各自负责人维护。

## 阶段3回报

**阶段结束，交 Root review，本回合直接结束。** 完整产物与边界见 [stage3 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/README.md)。实际图像光线拾取、目标内圈证明、最多三个新支持集候选和 bind 几何证据已交付，三个候选均保持 **BLOCKED**。

### 实际图像拾取与目标修改

[target.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/target.json)固定当前 final `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641` 与 raw `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。侧视像素 `(400,320)` 实际命中灰衣面 **43900**、顶点 **31463／32012／30406**，重投影误差低于 1 像素；旧边 **34287／34481** 也已纳入核心。新 ROI 为 513 组／667 顶点，五个目标均在可编辑核心且 fade=1，锁边移到外圈，冲突为 0。

本轮只生成 [contra_half、pelvis_025、pelvis_045 三个候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/candidates.json)，分别减弱对侧腿跟随、转移 25%／45% 双腿质量到 Pelvis／Waist。它们是衣物支持集实验，未把跨腿影响自动定性为错误。新增 Waist 仍在原 78 骨内，每顶点最多四影响、归一化，手部语义权重改动 0。每个目录提供 raw body-only rig、同权重的原动画预览及新增／移除影响、部位和 pose 依据的 `weight_changes.json`。

三个候选实际改 316／466／466 顶点，全部五个要求目标都已变。主面三个顶点分别移动约 **2–4／34–38／62–68 mm**，已排除上轮“目标本身没改”的情况。

### 动态失败与轮廓覆盖仍不足

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/verification.json)覆盖每个候选 179 姿态，结构、原 rest／IBM／UV／拓扑、合法新支持集、手部与接缝检查通过。区域平均 RMS 为 **1.966→2.021／2.550／4.168 mm**，平均 P95 为 **4.223→4.573／5.411／8.299 mm**，最大新增伸长为 **5.345／7.421／38.546 mm**。法线相对反向峰值为 11／24／45，存在显著面积缩小，不能因命中面已经移动就宣布改善。

补充轮廓拾取发现，实际外沿像素 455／456 对应灰衣面 **26875／25779**，控制点 **35019／34731／35089／34795** 在三个候选均未改，原因是位于主面 0.18 m 图距离外或锁边。第 320 行右侧轮廓均为 **457→457**。因此当前尝试尚未覆盖完整的轮廓控制面，不能把它解释成权重方法原则上无法改变该轮廓。

### 已定位的 bind 几何与最小后续范围

已交付真正 bind 与原生姿态的 [clay 同面板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/bind_vs_native_clay_targets.png)、[PBR 板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/bind_vs_native_pbr_targets.png)、[wire 板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/bind_vs_native_wire_targets.png)及[跟踪主面近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/side_bulge_tracked_bind_vs_native.png)。Bind 已关闭 NLA 并将骨骼 basis 归零，非 idle 帧；同面邻域凸起在 bind 已有 **9.521 mm**，slash 为 **6.787 mm**。静止几何本身确有凸面，不能简单当作错误权重，艺术形状是否需改仍由 Root 判断。

若要改变 bind 凸面，最小新增范围是：按实际轮廓面 26875／25779 与主面 43900 重新选连续衣片，先测衣物／腿的间隙，再以同拓扑局部 POSITION 修形或姿态形状修正处理，保留 seam 组一致并重核 NORMAL／TANGENT、多姿态碰撞。此几何修改本轮未实施，需另派明确范围。若继续权重实验，则必须先完整覆盖轮廓控制面，再评审边界和骨影响，避免重复只移动内部点。

纹理／空间独立核查已排除蓝裤控制点，bind 的 pinch 面还存在约 14.95 mm 叠层遮挡，均记录于 target。其他 14 区未追加全面重扫。当前三个候选只保留研究证据，费用 0，公共代码、library、app 及其他会话产物未由本会话改动。

## 当前阶段3执行项

责任目录为deformation/stage3。由实际缺陷视图拾取face／vertex，主要目标应在编辑内圈，锁边不能把目标本身冻结。允许衣物ROI在现有78骨中改变合理vertex支持集合，新增／移除影响给部位与pose依据，max4归一化，骨架rest／IBM／UV／拓扑保持，手部语义权重改动0。最多三个定向候选，以真实可见改善和跨姿态风险共同判断，必要时明确几何／动作根因。

## Root阶段3 review与阶段4续派

Root已查看同面跟踪与bind／native PBR图。该处存在源衣物折层及自然凸面，三轮权重修改均没有足够可见收益，全部BLOCKED保持。当前不将此处普通布料体积作为必须抹平的缺陷，结束该目标的权重实验。

阶段4责任目录为deformation/cuff-refinement，独立于03的前领几何。围绕已接受的设计板落实袖口退腕与布／皮护腕边界，先交真实模型近景与量测，再做最小同拓扑几何修整。

1. 读取原raw rig与01已审slash_guard_raw曲线，在REST、slash 1.367／2.117秒及walk姿态查看左右袖口、裸露腕部与护腕。交同机位近景、原face／vertex ID和实际缝隙、厚度与腕褶位置。明确区分有意贴合与可见穿插，不用单纯边伸长替代画面问题。
2. 以窄布缠腕、薄旧皮固定带和袖口退腕12mm设计为方向，选择一个证据明确且能局部修复的袖口轮廓。允许局部POSITION／NORMAL修改，优先保原拓扑、UV与所有权重，手部语义顶点和权重保持。不得改骨架rest、IBM或01曲线。若源融合几何不支持该目标，交出具体面范围与最小拓扑修改提案，先完成可独立修正的一处。
3. 输出机读delta、来源SHA、raw body-only GLB和成对素模／PBR图，保留原材质。30分钟内交第一项可见实物，后续离线专项检查覆盖原slash和walk的袖口／手腕关系。Root负责与03领口、04材质组合及正式发布。

其他会话共享仓库，保持其编辑。公共producer、manifest、正式library/app、Git、共享构建和设备不在本会话范围。阶段交付后若Root正在集成，可独立测量另一侧袖口并给同规格候选，避免等待。

## 阶段4袖口首项交付

**本袖口阶段结束，交 Root review；按最新队列继续现有 dao，不等待重复批准。** 本次实物与完整限制见 [cuff-refinement 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/README.md)。当前只交左侧近端灰色外棱局部径向收细，**未完成 12 mm 袖口退腕、新开口及布／皮完整重制**。

输入为原 raw rig `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`，01 已审 raw 曲线 `43e0ca0b0501f4be4dc066e045d1b60092e3bd65aea228bc3a2a32405f826391`，同 ID 预览 `34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896`。01 raw 有 35,325 顶点，原 body 为 35,308，已避免误用 ID，实际袖口姿态使用 approved preview。

### 首项候选和实际图

- [raw body-only 候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/candidate_rig.glb)，SHA `9ccd0717ca850196accd8351dd4f8bf6f139957a9b86f4fbcbd4505c1910f5d4`。
- [机读局部 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/vertex_delta.json)，184 个 POSITION、277 个 NORMAL；最大模型空间径向收细 1.499966 mm，轴向位移近零。只按 delta 与其他会话合成，不整文件覆盖领口／材质。
- [REST A 面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/previews/rest_left_A_pbr_before_after.png)、[REST B 面素模](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/previews/rest_left_B_clay_before_after.png)、[guard 1.367 秒 B 面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/previews/guard_1367_left_B_pbr_before_after.png)均同机位，共八张左侧对照。径向变化细微，B 角度较清楚，尚待 Root 判断是否接受为局部组件。

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/verification.json)通过，所有权重／UV／拓扑／rig/rest/IBM／原材质与已存在的 01 曲线保持；严格手／皮肤保护集合的 POSITION／NORMAL 未改。REST、guard 1.367／2.117 秒与 walk 四姿态无新增三角反向、零面积或衣物—保护面确认交叉。最近保护集合表面间距约 12.343 mm，这不是袖壁厚度或裸腕长度。完整补间及设备观感尚待后续。

### 退腕结构限制与后续最小范围

[measurement.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/measurement.json)定位到左侧布／皮肤过渡面 58422、58454、58485、58487、58488、58489、58522、58573、58615、58676。Hand 参考后 12 mm 截面穿 66 面、66 段，周长约 241.622 mm，是身体参考截面而非独立袖口。焊接开边为 0，但这个数字本身不能证明没有封闭衣壳或必需重拓扑。

当前保护集合包含所有 Hand/finger 影响，强于实际手语义，677 个左侧灰缠腕点因保守策略未动。后续应先通过实际材质、颜色和结构确认手与衣物；若有独立衣物环，验证同拓扑退移；若确认融合，则给袖侧环复制／重索引及最小内腕、布壁和局部 UV 方案，原手顶点保持。当前没有冒充实现真实 12 mm 开口，右侧候选与窄布／薄皮材料分工仍待后续。

本轮费用 0，实际发布由 Root 统一处理。当前有效阶段已收口，继续 `ArtSource/refinement/weapon/` 的独立 dao 候选。

## 刀具首轮材质响应交付

**本阶段结束，等待 Root review，当前回合结束。** 完整产物、固定 SHA、参数和限制见 [weapon 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/README.md)。本轮完成材质响应候选及几何量测基线，整体刀具精修仍有后续工作。后续按本文件顶部最新队列继续，避免因等待重复批准而空转。

### 双入口实物与三角色制作副本

- [NPC 刀具候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/dao_response.glb)，源 SHA `0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616`，候选 SHA `ed06ec82a709ce2e21d867e6d8d3cfd95557b92e58b9d8dc553e8fad9463496a`。
- [玩家 Grip 候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/dao_grip_response.glb)，源 SHA `a2a5eae94ef6f577697d6c91a5cd4d7fe22e09e2f8b8e4411cd53768751739fc`，候选 SHA `a579748a3edd4b378b896cd6c387c222f11bd107c2a740e1630600437f7cb48f`。玩家入口为 Grip identity、+Y 向上、−Z 刀轴。
- [机读材质 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/material_delta.json)记录七个粗糙度字段及刃口金属度。刃口粗糙度约 0.27→0.19、刀脊 0.40→0.45、旧黄铜 0.48→0.55，其他值见完整表。八个部件槽具明确原名，可供 Root 继续区分身体白闪与刀具。
- [三角色私有清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/actor_manifest.json)提供 base／indigo／veteran 前后 GLB。base 采用 01 已审 guard 预览 `34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896`，尚待 Root 与领襟、袖口和其他材质组合。

### 实际图与效果边界

独立刀具两套固定灯光各有正／斜／背及护手柄近景，三角色各有正／侧／背及持刀近景，共 20 张前后板。

- [常规灯光正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/standalone/front_before_after.png)、[反射灯斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/reflection_test/oblique_before_after.png)、[反射灯护手柄近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/reflection_test/guard_grip_before_after.png)。常规灯下刀面偏暗，反射灯下亮面趋白，前后差异均较轻微，视觉收益待 Root 判断。
- [base 持刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/actors/base_before_after.png)、[indigo 持刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/actors/indigo_before_after.png)、[veteran 持刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/actors/veteran_before_after.png)，全身三视图见 weapon 说明。头、靴与刀尖完整入画，部分刀面呈侧缘或被身体遮挡，前景空手也遮住部分刀柄。完整接触面与既有穿插仍需专项处理。

### 量测、验证与下一步

[实际量测](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/source_measurements.json)记录 13 mesh、3,722 面、8 材质，全刀约 104×967×39 mm、标记刀段 720.676 mm、护手轴向厚 18 mm、缠柄约 18 圈及五处刃／脊截面。本轮几何 delta 为零，新增倒角、护手减薄、缠绕造型及局部接触磨损继续作为后续制作项。

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/verification.json)已实际运行，NPC／玩家／三角色五个入口的完整 BIN 与非材质 JSON 一致性通过，涵盖几何、UV、节点、锚点、skin、rest 与动作。正常候选及锚点／网格／源 BIN 变更拒绝通过，生成器四类非法材质更新拒绝通过。当前验证支持有限材质补丁交付，现有手部接触问题仍需解决。

后续刀形与握持联合精修继续使用米制长度、Grip 和真实手表面约束。Root负责新文件身份复审、校准重签、正式组合与发布。玩家帧当前已验证结构与材质，独立玩家帧渲染仍待制作。现有低采样离线图适合首轮方向审查，PICO 实时加载、游戏 IBL、实际持刀输入、连续补间、完整三轮与 Space Pro 性能尚待验证。本阶段费用 0。

## 刀具第二轮真实几何与表面交付

**阶段结束，等待 Root review。结构 PASS，接触审核待修。** 完整实物、来源、装配、验证与限制见 [stage2 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/README.md)。本轮已交可见实体刀槽和截面分光，新增左手相交范围须继续处理。

### 实物和可见变化

- [NPC 候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/dao_refined.glb)，SHA `4834a555d70f80151bbe19358c0a94c11e1c3f76ab2e501bf6e70c2860bcf452`，源为 `0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616`。
- [玩家候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/dao_grip_refined.glb)，SHA `a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637`。另交 [可编辑 Blender 源](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/dao_refined.blend)及几何、表面生成脚本。
- 刀身细化为 66 轴向站位、21 点截面，原窄条改为约 5–7 mm 实体槽并向刀尖收束。护手铸造压边和端帽凹面已重建，总三角 3,722→8,702，13 部件、8 材质，NPC 约 2.889 MB。26 张实际 PBR 制作图中 18 张嵌入 GLB，涵盖打磨／磨痕、氧化、柄绳织纹和皮革压痕，部分磨损仍属部件／UV 假设。
- [刀槽近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_blade_oblique_before_after.png)、[2.2 m 刀具](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_normal_distance_before_after.png)、[玩家帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/player_grip_held_frame_before_after.png)、[base 斜角](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_normal_oblique_before_after.png)、[veteran 右侧握柄](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/veteran_grip_back_before_after.png)。共 25 张成对板，900²／24 samples，正常视距透视约 2.2 m，所有机位与来源 SHA 已固定。独立刀具的槽与反光可辨，角色当前正面刀面偏暗，正式场景可读性仍待与 07 光照共同评审。

### 三角色与真实接触门槛

[三角色清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/actor_manifest.json)使用当前正式 base／indigo／veteran 冻结输入，各含原八段动作。候选保留三人各自 `HandGrip_R` 与刚性蒙皮装配，身体／权重／skin/rest/IBM／动作保真通过，15 个刀 primitive 与 canonical 装配吻合，独立最大 POSITION 差约 0.000101 mm。原握柄保护表面位置差 0，重导 cord NORMAL 最大差约 0.000615，映射已记录。

[结构验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/verification.json)双入口及三角色通过，三类几何与六类装配边界拒绝通过，实际 GLB 导入通过。原材质名和身体 `tripo_` 白闪命名合同满足。GLB 具有有效 NORMAL／UV，无 TANGENT，客户端 MikkTSpace 生成和 PICO 法线显示待 Root 端内验收。

[接触审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/contact_audit.json)覆盖每角色 13 离散姿态、前后和左右手。右手握柄指标沿原结果，既有指柄相交仍存在。2.117 秒左手三人均无交叉，但早段原生左手穿刀仍在，候选增加部分受影响面，因此 `contact_clearance_accepted=false`。

- base 1.3167 秒相交手面 17→19，完整受影响手面面积 1019.314→1113.313 mm²，新增 58792／58823。
- veteran 1.367 秒 30→32，3303.844→3489.241 mm²，新增 19607／19789。1.5 秒 43→45，3460.628→3582.143 mm²，新增 15568／15569。
- [base 风险实图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_risk_1317_left_front_before_after.png)、[veteran 风险实图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/veteran_risk_1500_left_front_before_after.png)及反面均已补齐。源与候选均可见穿刀，新增面证据仍保留。面积是完整手三角面之和，穿透深度及真实重叠面积尚未量化。

下一项先修左手接触扩张，结合 01 最新动作核对早段空手与刀面，再交正常场景高光与连续补间。Root负责正式 producer、挂点身份重签、模型组合和发布。袖口结构已交 03 的现有实物与限制入口。实际输入、PICO 实时加载、Space Pro 观感与性能仍待验证，本轮费用 0。


## 当前十段动作库适配

**阶段结束，等待 Root review。** Root 在几何阶段收口时发布 `attack_overhead/attack_left/attack_right` 三方向，正式角色由八段变为十段。本会话继续完成新库装配、检查和实图，完整说明见 [current-bank 交付](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/README.md)。旧阶段接触限制和来源保留，新库结果独立记录。

### 最新输入、输出与接入

[actor_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/actor_manifest.json)记录当前十段动作输入、私有 profiles、各自 `HandGrip_R`、新刀部件和完整 SHA。

- base 源 `0c2a4801aaa6b89866303a9c783b524a88b6440633f0c9348041a6239af7d48a`，候选 `e7f3de3d8c7e202999b2d456ae85257b89a01e7c21792f332c4b273c77b60cbc`。
- indigo 源 `c980b18ef19190bf682604a43b730c3a0188829db8ea1c7c9e5d819d1959fed2`，候选 `448d46394743018aff3165e0e49e5c07480b617664c072c14ab6ae186cc87ef3`。
- veteran 源 `63b92ac8edda1ab7ad56e2d3196522788fec8a43a04c0d665deef08028d82e83`，候选 `0c0b57a4f3684a25603a6875b2fd9188096755dc4b3688d921a7de8776f1e9c2`。

独立新刀仍为 NPC `4834a555…`／玩家 `a09ba1f7…`。复用同一装配入口的 `--output` 参数，十段动作、身体、skin/rest/IBM、权重、各人挂点和原身体白闪材质保真通过。实际 GLB 导入通过。profiles 冻结并核验原模型签名，候选发布身份需 Root 重新生成／重签。

### 三方向接触与实图

[结构验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/verification.json)通过。[接触审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/contact_audit.json)按实际 0–1.75 秒键域采样，每方向 9 个等距离时刻及关键 .65／.9／1／1.1 秒，共 13 姿态，再加 walk 中点，每角色每版本 40 姿态。

三角色左手全部无确认交叉、无新增受影响手面，最近间距约 106.455／90.375／54.947 mm。右手握柄相关指标前后相同，既存受影响面峰值 147／55／85。整体握持仍保留人工验收状态，连续补间与实际穿透深度尚待验证。

最终交 18 张三方向成对板、36 张单图，包括约 2.2 m／20 mm 正常视距与握柄近景。[base 正劈](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/previews/base_attack_overhead_normal_oblique_before_after.png)可见刀槽和截面分光，[indigo 左斩](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/previews/indigo_attack_left_normal_oblique_before_after.png)的侧缘材质变化较小，[veteran 右斩握柄](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/previews/veteran_attack_right_grip_back_before_after.png)可复核原指面与新柄、护手、端帽关系。全部同机位与输入／图像 SHA 已核对。

离线预览器已修正新短动作的 NLA 完整区间平移及 0 秒起键采样，三角色×三方向 1 秒 R_Hand 对纯 GLTF 最大差约 0.000897 mm，首批偏差图已重出。旧长 slash 三组另外核对，最大差约 0.01604 mm，旧 25 图的标注时刻继续有效。[姿态验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/pose_validation.json)与[旧库校验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/legacy_pose_validation.json)均留实际数值。

[相机投影验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/camera_validation.json)覆盖实际蒙皮后全身和刀具顶点，18 张正常距离单图均有至少 1.5% 留白，头、靴及刀尖完整。PICO MikkTSpace、法线显示、正式 IBL、动态高光、真机画质与性能仍待验收。下一项为 Root 复审部件与新库装配后重签模型／profile 身份，再结合 07 光照核正常交锋可读性。本轮费用 0。

## Root本轮组合审核与续派（2026-11-11）

审核：实体刀槽／刃脊与护手方向通过开发集成审核；weapon-only正式发布已执行，三角色动作和proxy坐标保持，玩家Grip一并替换。

下一步：量测右手真实可见穿透深度并交局部修正；现有面交叉计数不能代表实际深度，保护新三攻左手。
