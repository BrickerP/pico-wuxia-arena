# 02 · 部位分区与衣物蒙皮修复

## 最新用户目标与执行队列

完整制作规格见[动作与打击反馈规格](../combat-polish-spec.md)。本队列承接2026-11-10用户最新的动作、特效、UI、环境与数值要求，袖口、刀具与握持为本会话后续责任。当前已产出的有效阶段先收口，再按队列继续，不因等Root回复而停住。

当前袖口候选按原合同继续，交付后转ArtSource/refinement/weapon做现有dao局部精修。重点是刃／脊几何分工、护手厚度、握柄缠绕、磨损与金属反射。米制长度、握点、现有手指接触为共同约束，逐角色给三视角与持刀近景。复用ArtSource/dao现有制作逻辑，首轮候选写独立目录，禁止覆盖正式dao／角色源。新刀形影响挂点或表面时交Root统一重签校准及重新组合，不以外观精修破坏实际刀路。

四会话共享仓库，请保留他人编辑。Root维护真实命中事件、最终UI与SDK接线、公共角色producer、正式发布、共享构建、设备和Git。先开发与专项制作检查，整局自玩后置。每阶段交GLB／代码、前后图或短片、来源与明确限制，30分钟先交第一项可见进展。

Root已接角色实例身体白闪，按实际tripo_身体材质名识别，保留Steel／Brass／Grip刀具槽。刀具候选继续保留明确部件材质名和米制握持身份，原身体材质改名或拆分需在交付中给映射。身体与DAO仍共用蒙皮ModelComponent，正式合成由Root处理。

## 当前状态

**阶段4执行中。** 三轮权重候选均未通过，正式源保持。Root接受当前衣摆有自然凸面与折层这一事实，停止围绕该凸面追逐应变数字，转到袖口与腕部可见细节制作。

## 上一轮成果与Root review

三角色握持和非持刀侧局部包络已进入统一producer。主角指面覆盖改善，仍有8.333mm峰值径向代理、深样本增加及源段外交叉。只调挂点和指骨不足以解决衣物／关节变形，本轮补部位级语义和权重审查。

## 文件所有权

负责ArtSource/refinement/deformation/与本文件。原始Tripo、prepare_character_library.py、prepare_rigged_warrior.py、motion_library.json、library和app模型由Root或01维护，不直接覆盖。01同期制作手姿，04同期修光照。

## 本轮任务

1. 输入采用refined-base60k/rig.glb和当前最终base动画作为姿态依据，记录完整SHA与坐标变换。
2. 建立头、躯干、左右臂／手、左右腿、衣领、袖口、腰带、衣摆等语义区域。输出前后分色图，face／vertex映射绑定模型SHA，颜色和空间共同复核。
3. 查抬臂、前伸、转头、左右迈步及当前slash关键姿态的拉伸、接缝和错误骨骼影响，定位最差顶点。
4. 首阶段优先肩腋／袖口或腰胯／衣摆中一个最明显问题，保留现有78骨rest和骨长，做局部权重修复候选。手部权重本阶段只诊断，避免与01的手姿同时改基线。
5. 连续皮肤与衣物结构分别判断。合并、拆边和权重平滑依据结构执行；UV／法线缝的重复顶点保持合理一致的变形。禁止把整手刚性到Hand的示例直接套入本模型。

## 审核产物

语义分区数据与正背图、pose缺陷清单、一个派生rig GLB、可复建修复脚本、前后相同pose／相机渲染、最大拉伸边与接缝量化。验证body／骨架／权重合法性及正常和边界输入。数据改善与可见改善分别陈述。

## 下游

派生rig保留原始源，Root评审后作为唯一producer的新target输入。01当前使用固定旧权重完成独立手姿，本阶段交付后再做整合复核，不等待01才能开工。

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
