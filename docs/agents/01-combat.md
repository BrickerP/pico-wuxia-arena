# 01 · 动作源与战斗姿态

## 最新用户目标与执行队列

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你继续负责动作源与正常视距可见的站姿、引刀、随势、防御支撑、弹反卸力、受击与行走转身。09接正式bank／正常循环／动画与代理，05接头脸，Root统一producer和发布。

三攻击stage5 raw保持冻结，继续既有后续队列。把动作力度和人体重心作为重点，避免只用细微角度与误差小数作为完成证明。每项交原生曲线、真实刀尖轨迹、源时间、足底与双手可见图／短片。与09交换来刀侧和接触标记，与03交换服装动作穿插。公共prepare_character_library和prepare_rigged_warrior由Root内部生产线维护，你不再编辑它们。

## 当前状态

**fine-overhead下一轮修复进行中。** v7已获实际动态review，髋肩随势改善有效，尚未获准正式发布。源.65／1.00／1.10秒头胸偏低、前视近似鞠躬，先输出正常眼高三分之四和侧面完整连续片，区分源姿态与投影，再决定最小修正。v7及原有证据保持冻结。

## 当前精细上劈合同（2026-11-13）

唯一新增责任为 `ArtSource/refinement/hand-poses/fine-overhead/` 私有候选与本交接。 唯一产品交付为Kotlin + PICO Spatial SDK6.1.9的原生APK，终端Space Pro／OS6，由Root统一构建、PICO Emulator验收与发布。本路只交可由现有producer接入APK的动作GLB与明确重导输入；离线两机位短片仅作Root已要求的动作源审阅证据。停止HTML／Web／Three.js、网页材质与新mock页面工作，已有网页不改不删。基于当前正式源及现有native骨曲线，完成guard→引刀→落刀→随势→收招，改善髋肩、肘腕、重心、支撑与回守。骨长、rest、敌人规则、伤害与整体1.75秒时标保持既定合同；本招手轨、骨轨与真实刀路可独立改进，给Root明确重导输入。

正式对照GLB SHA-256为 `ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20`，当前profile为 `04b225ac95aafc13b5d38dec5bbb55cf278b235514b4e7ca864fdebb20af3e90`。正式守势用于03衣片对照。原生动作源为refined-base60k/slash.glb的连续骨曲线，SHA `98e785d73a5d6cb767cebd5b79ec2bb9af9a2b717ae2d2576f3a0b7e07ea370a`。派生制作记录实际采样与约束修正来源，采用单调时间映射及连续肘平面，入口／出口回当前canonical guard。

本轮先交眼高1.62m、水平视线的三分之四与侧面1.75秒全片及实际采样帧板，保留固定相机身份和真实刀尖轨迹，不移动演员补画面。若源姿态仍低俯，只修颈胸与必要的准备段肘外展。髋肩随势、刀路、骨长、rest、足底、整体1.75秒及source1.00接触保持；不重做刀路，不扩另一招。45分钟内首项可见实物或明确失败。

全路最多一个Blender、2线程并通过既有宿主锁。当前producer、正式GLB、Kotlin、Git、设备、构建均由其既定负责人维护。阶段结束后在此写明“阶段结束，等待review”，随后等待对应回复，再继续下一轮。
Root已交原生真实输入实录 [native-input-contact-2026-11-12.mp4](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/presentation/native-input-contact-2026-11-12.mp4)及同名PNG／JSON，记录SDK鼠标进入同一resolver、SOFT_HIT／敌人护刀和敌血100降12。此为已接入基础，本轮源审阅以该正式身体／刀为对照。

v7历史交付及审计见下方。新一轮相机证据独立写入review/eye-height-v7，后续若需修姿态另建候选版本，不覆盖v7。

本轮首批正常眼高图已出现，45分钟首交目标内完成。实际侧面contact及三分之四引刀均可见低头，确认不只是投影。两机位为水平眼高1.62m、水平距离2.75m、VFOV70°，全53源时点的72,926个实际身体／刀具顶点均入框。源0.65／1.00／1.10秒的Head前向相对guard向下约41.38／37.37／30.50°，与固定解剖轴度量的26–37°基准不同。最小修正拟只给NeckTwist01／02的rotation分摊45／55%，将俯仰偏离保留20%；其余轨道逐原字节保持，胸、肩、髋、刀与足底不改。两段完整诊断片已交并逐格查看，[三分之四](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v7/three_quarter/movie/full_source_1p75s_30fps.mp4)及[侧面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v7/side/movie/full_source_1p75s_30fps.mp4)，各53真实源帧、实测1.750000秒。

v8仅两颈rotation的字节与世界轨隔离通过，但新60Hz实际全身体／Steel面检查在source.4667／.4833／.5000秒检出3个Head交叉时点，因此明确失败并冻结留证，不作发布输入。刀面位置逐bit保持v7，问题是抬头进入原准备刀弧。继续同轮最小v9修正，准备段抬头混入延后到.50至.65秒，其余合同保持；需重验混入速度、完整面检查与两机位连续表现。
## fine-overhead v7历史阶段交付

**v7阶段已结束，Root已review，尚未批准正式发布。** 本段保留candidate/v7冻结交付事实。首轮可见对照于22:54出现，完整候选经过刀向、准备空间及收刀阶段修正后收口；美术与实际游戏动态由Root最终验收。

- [1.5m同机位完整前后片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/comparison/movie/overhead_full_source_1p75s_30fps.mp4)，960×592、53个真实源采样，名义30Hz，末半帧VFR，ffprobe实际时长1.750000秒。
- [五关键姿态前后板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/comparison/poses/overhead_five_keyposes_compact.png)及[完整运动选帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/comparison/movie/full_motion_contact_sheet.png)，同source秒与镜头，包含guard／引刀／接触／随势／收招。
- [Root重导输入清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/candidate/v7/fine_overhead_inputs.json)，SHA-256 `b674501f88e5ed76fdeb12cb41ba2465f48b40d50b2b08999fc6da4fe94d63d4`。

| 文件 | SHA-256 |
| --- | --- |
| fine_overhead_raw.glb | `87c5fd566a63bba551cbbdfaa5841f519a7ed865cbbffc7da929c65219c9ef26` |
| fine_overhead_preview.glb | `285d3e34e94e335d2e5f3705d77483fabbe3a297ccfbdec08153bcab1b13a21c` |

均位于fine-overhead/candidate/v7，211帧／120Hz、234条TRS、源0至1.75秒。原骨长、rest与skin保持，预览使用当前正式身体、材质与真实dao。raw原右15指握姿恒定、右指校正UNBAKED；preview应用一次原8项右指修正及一次正式常量root shift约-.027999145m。首尾保留canonical原始float32轨值，guard首图与正式图像均差约.003／255。

### 动作来源及改动

每个输出帧采现有Tripo native slash骨曲线，单调cubic Hermite时间映射为输出0／.65／.9／1／1.1／1.55／1.75对应native1.55／1.90／2.03／2.117／2.15／3.40／3.40。保留连续髋肩运动细节，收束过大前倾并加入约35mm受力下沉、足底IK；准备段重新给刀头上举空间，末段闭回guard。来源为现有native曲线派生与约束重作。

右上臂、前臂与手腕均已重作新轨。旧native腕朝向直接套当前刀绑定会刀背领先，单纯前臂旋前无法自然吸收约157°翻刀。本轮放开腕路径，前臂／手共同重定向，肘在真实肩球上重求，保留自然局部腕关系并使锐刃向运动方向。原native2.17后的收刀移至RECOVERING，ACTIVE末1.1只映native2.15。接触仍为源1.00秒、ACTIVE elapsed100ms，整体阶段边界0／.65／.9／1.1／1.75保持。

### 实际接触与足底

[独立真实刃向审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/candidate/v7/blade_direction_audit.json)回读最终GLB，ACTIVE25个时点最低锐刃／切向cos为刀尖.891107、中刃.883858，接触时.999689／.999868；ACTIVE末无早期收刀面拍。接触瞬间刀尖／中刃源速度约8.37／5.38m/s。

source1.00的实际Steel | sharpened edge与z=.90面交点代表值为(-.199805,1.260666,.90)m、几何面法线(-.998950,-.022356,.039993)，来自当前preview primitive10／triangle408（zero-based）。清单保留全部真实交点与normal含义。双足整段采用鞋面支撑约束，鞋面最小高度／中心误差约.0018mm；它不表示整鞋所有曲面都同时接地。

[完整数值及面检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/candidate/v7/fine_overhead_verification.json)已实际执行，0至1.75秒每60Hz共106时点，真实钢刀与当前完整body skin三角面0重叠。非法时间／非单调映射等9项拒绝检查、骨长、原mesh／skin、首尾、恒定握指、一次校正与formal shift均通过。腕部114°分支跳变已修复；仍只证明所采时刻，未作C1或无限连续无穿插声明。

### Root重导与审阅边界

Root应读取唯一输入清单，把新R_Upperarm／R_Forearm／R_Hand、body与左护手轨一起重导；当前正式旧手轨不适合本招。每target按其原grip／once校正、真实武器、grounding重新生成动作、hand-track signatures、contact／head-body-Blade profiles及binding。不得直接把base预览点当三角色通用最终判定点。原敌人规则、伤害与整体时标未调整。

当前1.5m离线眼高1.62m、看胸1.10m、vFOV100°保持前后相同。正式before在源.867／.900／.933秒有三帧刀尖越上框，已在片内披露；候选53帧全部8个真实锚均在画内。Blender审阅使用与正式KTX2源逐非图像语义／2587个bufferView一致的当前PNG视图。图片证明动作候选可见变化，Root仍需审准备肘外展、重心节奏和收招自然度，并做最终SDK／三target／03衣片组合验收。

.90附近腕保留约19°举刀IK修正，.9833之后才恢复至native局部腕约3e-5°误差，不将整段标成未经改动的native。当前所有正式模型、公共producer、Kotlin、构建、设备及Git均由既定负责人维护。动态审阅期间未扩其他方向。

## 上一轮成果与Root review

已发布60k主角、8份动作资源、接触姿态短停／反冲与角色代理。上一轮数学转移和数据校验充分，但七段重定向资源统一锁定双手30根指骨为slash@2.117秒，待机／行走／受击时空手也保持抓握。这是本轮首先移除的旧机制。

## 文件所有权

负责 ArtSource/refinement/hand-poses/、ArtSource/refinement/slash-refinement/ 的动作制作源、候选与本文件。公共producer、manifest、正式库、Kotlin runtime与Git归Root及指定运行会话。

## 本轮任务

1. 冻结并记录当前base输入，输出现有idle、walk、hit、slash的双手基线近景与明确缺陷。
2. 将手姿按手别及实际clip组织。右手围绕DAO保留稳定抓握；空手左手制作放松、护身或受击对应姿态，动作意图先在关键姿态图中表达。
3. 优先完成idle、walk和受击的空手改善，保持现有body轨迹、rest、骨长和出招时标。必要的新数据直接服务这些clip，移除统一双手锁姿路径，不叠加旧／新兼容机制。
4. 在独立候选目录生成8clip角色，禁止调用会覆盖全局library/app的build_library入口。可以复用retarget_clip和底层prepare_character，输出路径全部指向hand-poses。
5. 原生slash有需要时另列局部修正及前后姿态，源接触标记变化交Root同步运行映射。先把已确认的空手问题做完整。

## 审核产物

一个候选GLB、按clip／手别的姿态数据、前后同机位双手图和短片、源时标／骨架／非目标轨迹检查。新的手姿逻辑补正常路径和无效输入边界的离线专项验证。明确仍有的穿插和手形问题，实际图片参与验收。

## 下游

02的首阶段只修肩腋、袖口、腰胯和衣摆相关区域，手部权重先诊断。Root整合新蒙皮后，由本会话再复核手柄接触；本阶段使用当前固定基线独立完成。

## 共同执行约束

唯一工作仓库为 /Users/yupeng/projects/personal/pico-wuxia-arena。当前模型基线为main的cc12bf1，base.glb SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641。运行栈为Kotlin + PICO Spatial SDK6.1.9，终端Space Pro／OS6。

其他会话正在同一仓库并行。各自只修改责任范围，保留其他人的编辑。Git提交、分支、合入、共享构建、设备操作、实际截图与正式模型发布由Root统一负责。候选输出留在各自目录，library、app角色与公共manifest由Root发布。

本轮允许离线资产生成、渲染及专项制作检查，运行／设备由Root统筹。新版12路合同为45分钟先交首项可见实物，阶段回报写明“阶段结束”、输入SHA、文件、效果、限制与下一项，按已授权队列继续。旧阶段的30分钟目标与实际延误保留历史记录。每路最多1个Blender进程，本路统一经 `ArtSource/refinement/hand-poses/run_blender.py` 宿主锁串行，构建、审计、渲染可入队；无Blender工作并行。Root已实测运行中持锁、退出释放及后台模式拒绝边界。遇到阻塞先交已完成部分并继续能独立完成的工作。

## 阶段回报

**阶段结束，等待Root review，本回合结束。** 本轮已交实际8clip候选及同机位双手前后图、真实walk短片，未覆盖正式library/app角色。

### 固定输入与候选

- 固定输入为 `app/src/main/assets/models/opponents/base.glb`，SHA-256 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`，阶段末再次核对相同。
- 主候选为 `ArtSource/refinement/hand-poses/candidate/base_hand_poses.glb`，23,000,772字节，SHA-256 `df08f96a25b34d0f499489f8c40767c9a626ce466786fa8b178339e5fe0ced12`。中间retarget片段与身体版本均留在同一候选目录，Root以该主候选及metadata取产物。
- 修改了 `prepare_character_library.py` 的手姿路径，移除 `fixed_grip_pose` 的统一双手锁姿入口。新路径先取native参考，再逐clip给右15指保留抓握、左15指独立旋转包络。其它身体重定向分支保持原逻辑。

### 按clip与手别的制作结果

| clip | 左手 | 右手 |
| --- | --- | --- |
| idle | 轻松微屈，curl权重0.18→0.22→0.18 | 保留已审native抓握 |
| walk | 自然随臂，0.22→0.30→0.22 | 保留已审native抓握 |
| turn | 稍屈护身，0.20→0.28→0.20 | 保留已审native抓握 |
| hit_body | 展开护胸并回落，0.18→0.52→0.32→0.18 | 保留已审native抓握 |
| hit_head | 更开放的护头掌，0.18→0.10→0.16→0.18 | 保留已审native抓握 |
| hit_side | 柔和护身，0.18→0.38→0.26→0.18 | 保留已审native抓握 |
| fall | 空手逐步松开，0.18→0.12→0.04 | 本阶段继续保留抓握 |
| slash | 保留原生曲线与时标，另列剩余局部问题 | 保留原生及已审修正 |

左指从本角色rest旋转向本角色native curl插值，拇指混合系数为表中权重的0.55。参数、各关键比例及源SHA见 `candidate/hand_pose_policies.json`。idle/walk近景显示左手从虚握拳改为放松下垂，hit_body左手由拳形改为展开护胸，右手与DAO接触保持原基线。

### 正常与边界验证

已在Blender Python中实际执行 `build_candidate.py` 与 `verify_candidate.py`，只调用现有retarget与底层prepare_character，全部输出指向hand-poses，未调用全局build_library。

- 8clip名称、输入时标、采样数量与基线相同。七段动作各15条左指rotation改变，其它动画轨迹逐通道最大差为0，含身体/手腕、右指和左指translation/scale。原生slash全部轨迹最大差为0。
- rest节点、骨长、skin/IBM、原mesh属性、weights及indices均与基线相同。
- 11项无效输入检查实际拒绝，覆盖unknown clip、NaN/越界progress、缺指、奇异矩阵、target缺必要指骨、无效native采样时刻及输入SHA改变。变更SHA的失败路径没有写入候选。
- 初版出现左指scale重分解的约1e-7舍入差，已改为直接沿用原native translation/scale并重新构建。最终版本的非目标轨迹严格同值。

完整结果见 `candidate/verification.json`。这是离线数据验证，皮肤穿插及游戏内表现仍由视觉和后续设备验收确认。

### 图像与短片验收

已目视核对idle、walk、hit_body和slash的双手近景，总图按每行同clip/源秒、前左/后左/前右/后右排列。每对冻结同一相机、光照、材质和尺寸，图及render_manifest均携带当前输入/候选身份。曾被衣摆/左手遮挡的idle与slash右手，已成对调整机位重渲以看清DAO柄。

- [双手前后总图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/review/hands_before_after_contact_sheet.png)
- [idle近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/review/idle_hands_before_after.png)
- [hit_body近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/review/hit_body_hands_before_after.png)
- [walk连续短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/review/walk_left_before_after.mp4)，源0.3至1.4秒，12帧、10fps、1.2秒、640×380，实际clip采样。另有GIF及明确标注为关键姿态翻页的reel。

### raw／baked与合入边界

制作从manifest指定的raw rig和raw native slash重建。`candidate/retargeted` 七片段尚未应用旧finger/offhand校正。最终主候选已在八clip各执行一次原base的8项右指修正，共64条rotation轨，base没有offhand envelope。原生slash也只包含这一次原有右指修正。完整offset、clip与次数由alignment及hand_pose_policies交叉核对，Root不能再向最终候选叠同一校正。

Root正式迁移应仍从raw源制作，按clip分配已有校正，原生slash的必要校正保留一次。本轮只评审pinned base，另外两角色的旧左指offset与新姿态组合尚未评审。

### 剩余问题与下一步

原生slash约2.117秒仍有左手环握/贴近右腕的局部姿态，当前原生曲线与接触时标未改。右手已有的掌柄交叠沿基线保留，本轮未作全表面穿插证明。Root合并02分区蒙皮候选后，需要重看袖口、掌指与DAO接触及片段切换。本轮无新模型、收费、正式发布、游戏构建或设备操作，新增制作脚本及负责文件静态检查通过。

## Root合入前审查补充

新姿态的数据必须声明是否已经包含旧指姿／包络校正。正式重建以原始rig与原生slash采样为起点，每项校正只应用一次。主角本阶段可保留现有已审右手抓握，通过raw姿态加一次已审右手修正达成。

Root负责同步迁移manifest与底层校正配置。新的按clip空手姿态取代对应旧的统一左手锁定／校正。原生slash当前仍需的修正保留一次，其数据与重定向片段分别组织。01先交候选和所需接口，正式输入以raw源重建。

## Root首阶段review与续派

已查看idle和hit_body双手前后图，接受本阶段空手改善，正式发布交Root迁移校准。阶段2执行原生slash左手护身意图与必要腕／前臂局部修整，raw曲线为源，保留右手／刀路和出招时标。交raw单clip与带刀预览，覆盖当前播放段及完整源中已知交叉，不以裁段替代修复。阶段2交付结果见下方回报。

## 阶段2范围与输入冻结

本阶段责任增加 `ArtSource/refinement/slash-refinement/`，首阶段producer代码冻结在SHA-256 `76c0c9f5bb3cbdf1bea41d31b1291804e38b3d32f975778f4fdec80625160ec9`。原始slash仍取 `refined-base60k/slash.glb`，SHA-256 `98e785d73a5d6cb767cebd5b79ec2bb9af9a2b717ae2d2576f3a0b7e07ea370a`。带刀对照基线为首阶段候选 `df08f96a25b34d0f499489f8c40767c9a626ce466786fa8b178339e5fe0ced12`，其中slash与正式基线同值。

完整源0.033至6.6秒按30Hz检查实际刀面，在1.258至1.45秒及3.833至4秒加密到60Hz。固定基线出现26个离散刀面交叉姿态，最多61对三角面交叉。早段以左拇指并包含掌部为主，晚段以左小指为主。原数据见 `slash-refinement/surface_before.json`。

## 阶段2回报

**阶段结束，等待Root review，本回合结束。** 本轮完成原生slash的左手意图修整，完整源0.033333335至6.599999905秒保留。出招时标及接触映射沿用原值。

### 交付与身份

| 产物 | 字节数 | SHA-256 |
| --- | --- | --- |
| `slash-refinement/candidate/slash_guard_raw.glb` | 18,714,904 | `43e0ca0b0501f4be4dc066e045d1b60092e3bd65aea228bc3a2a32405f826391` |
| `slash-refinement/candidate/slash_guard_preview.glb` | 19,537,320 | `34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896` |

派生源已写入15条左指旋转和左前臂局部曲线，右指校正为UNBAKED。带刀预览从固定raw rig与该单clip派生源制作，原base的8项右指校正执行一次。左前臂修整已经包含在派生源内，合入时直接消费该曲线。完整记录见 [制作元数据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/candidate/slash_guard_metadata.json)，其中区分raw与preview、校正次数、输入快照和完成状态。

### 姿态与局部修整

左指沿原生每帧curl与本角色rest旋转制作，权重在0.18至0.26间平滑变化，拇指乘0.55。准备、挥击和回收时空手保持开放护身掌，原2.117秒环状虚握已舒展。全部198个原始指轨采样时刻保留。

最初只改左指时，刀面交叉由26个姿态降至10个，晚段3.833至4秒已消除，早段掌部仍穿过刀面。随后只给 `L_Forearm` 加局部+Z6°，窗口为1.12／1.27／1.46／1.62秒，复用现有raised-cosine包络。方向试验中+4°已有零交叉，但最小采样间距约2.36mm；本轮选择+6°，最小约9.05mm。未增加L_Hand修整。配置见 `candidate/slash_wrist_policy.json`。

### 数据与失败回归

实际执行 `refine_slash.py`、`verify_slash.py` 与 `audit_slash.py`，并独立复核最终文件的逐轨字节及SHA。

- raw与原始slash、preview与首阶段slash对比均只有15条左指rotation及1条左前臂rotation变化。其余218条轨逐字节相同，其中102条右侧轨相同。身体主轨迹、右手和同skin DAO轨迹保持原值。
- 原始所有采样时刻及首尾范围保留。仅左前臂rotation从198增至220个采样，额外点服务短时平滑包络。指曲线与前臂公式最大分量误差均为0。
- 节点rest、mesh、skin、weights、IBM、材质、纹理及刀绑定同值。正式base和首阶段producer SHA已再次核对。
- 13项失败回归通过，覆盖错误源SHA、重复派生raw／baked、重复左指／前臂处理、重复曲线时刻、非有限时间／强度、越界强度、错误端点及空腕部配置。正常局部包络的内存回归通过。构建开始即清除旧验证结果，以in_progress／complete与产物SHA标识完整交付。
- 固定源没有共享sampler，该隔离分支已做源码review。报告不将它计为实测回归。

结果见 [专项验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/candidate/verification.json)。

### 实际刀面与全源可见检查

实际左手蒙皮对实际DAO三角面扫描覆盖完整源30Hz、两段已知交叉区间60Hz及指定关键时刻，共217个离散姿态。最终刀面和护手均为0个BVH交叉候选、0对已确认非共面三角面交叉，全部采样中左手顶点至刀表面最近间距约9.04967mm，出现在1.366667秒。各采样时刻没有交叉对数回归。见 [刀面对照数据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/surface_comparison.json)。

已目视8个关键时刻的双视角同机位对照，以及全源54时刻的三张双视角mosaic。左手由虚握改为开放掌，早段拇指与晚段小指离开刀面。右手握柄与刀路视觉一致，采样中未见新增明显手形跳变。

- [关键时刻双视角前后图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/review/slash_contact_before_after.png)
- [完整源双视角前后短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/review/slash_full_source_before_after.mp4)，8fps、54帧、6.75秒，源0.033333335至6.599999905秒，保留最终端点。
- [全源mosaic 1](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/review/slash_full_source_before_after_mosaic_01.png)、[mosaic 2](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/review/slash_full_source_before_after_mosaic_02.png)、[mosaic 3](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/review/slash_full_source_before_after_mosaic_03.png)，覆盖全54个时刻。
- [渲染方法与限制](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/slash-refinement/review/slash_visual_review.json)，记录相机、输入SHA、采样及近景刀尖出画等限制。旧partial与临时progress已清理。

### 交Root的最小接口提案

角色的 `grip_source` 继续绑定原raw native slash及2.117秒手姿参考。另设明确的 `slash_source` 绑定攻击播放源，base指向本轮派生raw与对应SHA，其它角色显式绑定各自原生源。库制作的slash打包改从 `slash_source` 取片段，七段重定向仍从 `grip_source` 采手姿。这样精修攻击左手不会改变其它clip的curl参考。manifest与底层迁移由Root执行。

### 待review与验证边界

本轮选择+6°前臂幅度及0.18至0.26的左指curl权重，动作意图与掌形交Root视觉review。刀面扫描和8fps图像均为离散源资产证据，连续时刻的全表面穿插及PICO运行时尚未验证。02新蒙皮合入后，需用同一动作重新核对袖口、手掌和刀面。正式发布、manifest迁移及运行构建交Root整合。

## 当前阶段3执行项

责任目录增加hand-poses/attack-keyposes，已交公共源码冻结。以现有78骨制作守势、引刀、接触、随势、回守五关键姿态，标实际DAO刀尖、目标守位高度／距离、脚接触和头部朝向。先评审可见姿态，再细化完整clip。Root负责接入动作映射与代理。若Root在集成，可独立测现有idle／walk／turn的脚滑与收势基线。

## 阶段3回报

**阶段结束，等待Root review，本回合结束。** 五关键姿态GLB、三视角图与专项验证已完成并目视核对。图像地面已由错误的-1m校正到真实LBS足底约0m，完整三视角重新渲染。本阶段超过30分钟，追加修正覆盖引刀护手近头、近似接触点、STEP求值及图像地面偏低。

### 身份与制作参数

输入为原78骨raw rig、首阶段78骨idle@1.0、阶段2slash与固定native slash@2.117抓握参考。完整源SHA见 `hand-poses/attack-keyposes/candidate/metadata.json`。骨架rest、骨长、skin、weights、IBM、材质及DAO原尺寸保持。actor标定1.78m，prepared glTF为+Y向上、+Z向前、+X角色左，骨盆水平移到原点。

- raw为 `candidate/overhead_keyposes_raw.glb`，SHA-256 `d6e3da9550aa1c5a8c5ca197736e92ea04104f061464c2a60b0f30d496e3ce61`。右15指保持native抓握，右校正UNBAKED。
- preview为 `candidate/overhead_keyposes_preview.glb`，19,423,568字节，SHA-256 `e77307bfb139e8df291194ebf10e48e741d7c86164797beca6ce6bf9024b9eb0`。原8项右指修正执行一次。
- 全部234条轨为STEP，只有五个独立关键姿态hold。刀尖虚线连接表达五点间弦线。

| 姿态 | 建议秒 | 腰颈前倾 | 右腕目标(x,y,z)m | 实际刀尖(x,y,z)m |
| --- | --- | --- | --- | --- |
| 守势 | 0.00 | 5° | (-.13,1.27,.27) | (-.160,1.968,.786) |
| 引刀 | 0.65 | 8° | (-.13,1.60,.14) | (-.160,2.060,-.596) |
| 触目标守位 | 0.90 | 12° | (-.06,1.43,.33) | (-.090,1.285,1.186) |
| 随势 | 1.10 | 14° | (-.10,1.08,.28) | (-.130,.574,.985) |
| 回守 | 1.75 | 5° | (-.13,1.27,.27) | (-.160,1.968,.786) |

建议沿用OVERHEAD预650／起250／有200／收650ms。头朝对手眼位(0,1.58,1.05)，空手位于角色左胸前外侧。肩肘腕用两骨解析IK求解，刀轴及实际DAO source+X刃向分别约束。原native有效段前倾约59至69°，本轮五姿态为5至14°。

实际守位接触是 `Steel | sharpened edge` 表面点 `(-.09006450,1.36361861,.90)`，高度约1.364m、前向距离0.90m、水平距离约0.9045m。原刀根至刀尖弦线交点偏离表面约4.505mm，已独立标为approx。红标记采用真实刀面点。守位框是空间参考，尚未绑定对手实体。

### 验证与修正

`build_keyposes.py`、`verify_keyposes.py` 已实际运行通过，12项无效输入回归通过，覆盖源身份、无效／重复时刻、不可达IK、退化方向及非法参数。右指T/S直接取原native采样，preview从raw重建一次右校正后全部234轨匹配。源和校正配置未改共享文件。

腰颈角、Head相对rest的真实注视向、刀轴与刃向均实测核对，双腕误差小于1微米。下肢轨跨五姿态同值，脚关节位移0。真实LBS左足底约0m、右足底约4.564mm。非指T/S相对idle最大浮点差约3.576e-7，本轮保留该数值边界。

原引刀护手距头部仅1.266mm，右腕向角色右侧外移3cm后，最终间距约30.318mm。五姿态左手及头颈对实际整刀均为0个BVH候选、0对已确认三角面交叉，左手最小采样间距约197.717mm。见 [表面检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/candidate/surface_review.json)和[专项验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/candidate/verification.json)。

STEP使用实际float32关键时刻。名义1.1秒存储为1.10000002384秒，渲染在实际key之后微移1e-5秒，避免误取接触姿态。

### 待review边界

本轮自行选择表中腕位、刃向、前倾和建议时点。连续过渡、速度、完整动力链、重心转移、脚底滑移及设备表现待完整clip验证。下肢当前沿用idle窄站距，右足底约4.56mm离地，均需参与下一轮姿态review。Root审过五姿态后再细化动作与同步映射／代理。

## Root阶段3 review与阶段4续派

Root已查看五姿态三视角最终板。接受收敛腰颈前倾、明确上方引刀、开放护身掌和真实刀面接触标记。当前只能作为姿态草案，下肢窄站距且全程固定，重心与肩腰几乎没有出刀过程，动作仍显僵硬。STEP资源保留制作审阅用途。

阶段4在attack-keyposes/stage4制作同一记正劈的连续动作候选。先把五姿态修成可用的战斗站姿，合理前后脚及横向间距、屈膝、骨盆与肩部先后带动，双脚实际足底落地。保持身高、刀长、握点和原rest／IBM，落脚依据真实蒙皮足底。上身已有刀面方向与护手离头距离继续维持。站距和转体幅度先以自然可见性决定并记录，不用微小IK误差替代动作表达。

交v2三视角板并做离线自审后可独立继续完整clip，无需等待Root回复。连续片段保留约650／250／200／650ms的四阶段建议，明确刀尖轨迹和接触点，做引刀减速、挥出加速、随势减速与回守过渡。使用标准可加载TRS曲线和采样，移除五姿态STEP播放的正式用途。交raw单clip、一次右指校正的带刀预览及正／侧短片，标明身体动力链、脚底接触、源时间到游戏阶段的映射。相邻关键姿态之间必须检查实际左手／头颈与DAO关系，补间不能只凭端点通过。

先收口当前阶段报告与文件，随后执行阶段4。公共producer当前交付保持冻结，正式动作接线与战斗代理由Root统一整合。其他会话并行，保留其编辑。新动作只服务既有OVERHEAD能力。30分钟交第一项可见进展，阶段完成后可独立量测idle／walk／turn脚滑，不空等Root。

### 视觉交付

- [五关键姿态三视角总板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/review/overhead_keyposes_three_view_board.png)，已目视五姿态全部15个视图，统一世界相机与比例，地面0.25m网格。
- [真实刀尖五点弦线图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/review/actual_blade_tip_keypose_chords.png)，侧面／正面／顶面投影，标真实刀刃接触点。
- [姿态参数](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/candidate/keypose_parameters.json)与[渲染身份及采样](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/review/render_manifest.json)，每姿态另有独立三视角图。

最终图地面高度为约8.1e-9m，框景限定实际TripoBody_Mesh，脚圈投影在地面上方8mm用于可读标注。随势已按真实1.10000002384秒之后求值，图中刀尖向下，右腕高1.08m。

## 阶段4回报

**阶段结束，等待Root review。** 已交v2五姿态板与同一记OVERHEAD完整连续候选。首张可见v2板约22:25完成，超出30分钟目标约4分钟，阶段中追加了真实鞋跟／前掌放平。按最新队列授权继续左右斩制作。

### 候选与raw／baked

- v2审阅板为 `hand-poses/attack-keyposes/stage4/candidate/overhead_v2_keyposes_preview.glb`，SHA-256 `94dfd60fadf62101df18a5a6886f2219fce1252f3c5578b5ba59daf80fa32d11`，5键STEP，仅作姿态审阅。
- 正式待审动作源为 `stage4/candidate/overhead_raw.glb`，SHA-256 `7ea4a924bc3e730d597a6d7261056746890167e09e18252bda57272260e1b991`，已写身体／脚／腕曲线，右指校正UNBAKED。
- 带刀预览为 `stage4/candidate/overhead_preview.glb`，19,753,452字节，SHA-256 `1cb7a1ab744968af4d72fb8ff4c77b047626e0c1cfa894ac81350f13d2213789`。clip为 `overhead`，106个60Hz采样，标准LINEAR TRS，源0至1.75秒。原8项右指修正一次，末姿态严格回到守势。
- 原rest、骨长、mesh、skin、weights、IBM与材质保持。公共producer SHA仍冻结，全部候选只在stage4目录。

### 站姿与身体带动

足底中心为L(.16,0,.12)、R(-.16,0,-.12)m，横向32cm、前后24cm。骨盆五键高度为.870／.865／.860／.855／.870m，Hip绝对yaw为-8／-12／4／8／-8°，肩部Spine02绝对yaw为-16／-26／12／20／-16°。腰背前倾维持5／8／12／14／5°。双膝屈曲最小约19.97°，头持续看对手，空手护身。引刀采用减速、挥出加速、随势减速与回守过渡，身体与腕刀分相采样。

原idle只有前掌低点近地，鞋跟曾悬空36／72mm。本阶段按真实鞋面ROI放平后再解腿和逐帧落地，heel/front近等高。全鞋最低点接地，曲面鞋底使左heel/front仍高约4.84／4.86mm、右约7.42／7.42mm。实际几何PCA鞋轴约左+5.37°／右-1.23°，骨轴±8°只作制作初值。

### 源时间与游戏阶段

| 游戏阶段 | 现有OVERHEAD时长 | 新源区间 |
| --- | --- | --- |
| PREPARING | 650ms | 0至.65秒 |
| STARTUP | 250ms | .65至.90秒 |
| ACTIVE | 200ms | .90至1.10秒 |
| RECOVERING | 650ms | 1.10至1.75秒 |

**Root合入前需校正接触时点。** 阶段5审查确认当前裁决contactDue位于ACTIVE中点100ms，阶段4正劈接触key在源.90秒，会在线性阶段映射下提前100ms。阶段4资产保持冻结，Root须在正式接入前统一正劈源接触与裁决时点。阶段5已将左右斩接触key移到源1.00秒，ACTIVE仍为.90至1.10秒，已加100ms断言。

接触仍取真实Steel刃面点(-.09006450,1.36361861,.90)m。新骨锚见 [joint_anchors.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage4/audit/joint_anchors.json)，含106实际key的Head／Spine02／Hip／双Foot／ToeBase原点与世界旋转及真实刀根／尖，坐标在游戏实体变换之前。Root使用该源重新绑定代理局部锚与现半径／阈值，旧native前倾曲线保留各自来源。stage4 metadata的 `feet_world_gltf_m` 实际是足底中心，真实踝骨位置以此导出的 `bone_anchors` 为准。

### 验证、短片与限制

16项失败回归实际通过。raw→preview重建一次右校正的全部234轨、原native右15指、骨架及蒙皮保持、首尾守势闭合均已核对。独立审查通过。非根T/S存在约1.49e-8／5.96e-8浮点差，当前仅作标准采样曲线交付。

实际表面检查覆盖106个源key及105个相邻key中点，共211时刻。左手／头颈对DAO均为0 BVH候选、0对已确认非共面三角面交叉，最小间距分别197.717／24.502mm。固定足底低带最大水平位移为左1.054／右0.706mm，全鞋鞋帮混合权重点可约8／7mm；不能以足迹中心稳定声明整鞋零滑。补间最大鞋面下探约0.021mm。见[可复跑审计与完整数据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage4/audit/overhead_surface_review.json)。

- [v2五姿态三视角板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage4/review/overhead_v2_three_view_board.png)，已目视15视图，宽站距、屈膝及转体可见。
- [连续正侧短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage4/review/overhead_v2_front_side_continuous.mp4)，真实源0至1.75秒，22帧／12fps／960×572，显示1.833秒。
- [全段mosaic 1](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage4/review/overhead_v2_motion_mosaic_01.png)、[mosaic 2](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage4/review/overhead_v2_motion_mosaic_02.png)，已覆盖全部22个正侧采样，未见出画或明显姿态跳变。

当前提供C0采样曲线及有限补间检查。C1连续性、未采样时刻穿插、实际卡肉手感及PICO运行性能待后续验证。Root负责动作选择、代理与最终发布接线。

## 当前阶段5执行项

### Root动作bank合入review

Root已查看阶段4的v2三视角板，接受更宽战斗站姿、屈膝、上方引刀、肩腰带动及开放护身手方向。原生旧slash的前倾曲线将从正式攻击播放路径移出，native grip_source保留每角色抓握参考。

接触时序作为合入闸门。当前规则在ACTIVE中点裁决，OVERHEAD对应游戏有效段开始后100ms。新源三招统一使用1.00秒的真实Steel接触key，阶段区间仍为0／.65／.90／1.10／1.75。已冻结阶段4原件保留，在stage5候选目录输出overhead_aligned_raw及对应预览、metadata与骨锚，避免覆盖既有来源身份。左右斩按同一规则收口。Root接入后由同一数据导出播放相位与接触代理。

请先冻结这三招的raw／右指一次校正预览、实际接触点与每帧骨锚，逐文件写完整SHA和校正次数。方向名是角色视角，另给源.90／1.00／1.10秒刀尖X坐标和切向，Root按玩家视角的来刀侧映射LEFT／RIGHT。三个最终文件冻结后，可继续已授权防御／弹反／受击，公共源码与正式库仍由Root维护。

责任增加 `hand-poses/attack-keyposes/stage5/`，冻结已交阶段4与公共代码。沿用战斗站姿和原右手抓握，分别制作角色视角向左／向右的横斩。prepared+X为角色左，接口名为slash_to_left／slash_to_right，左右转体、引刀、空手护身和刃向分别制作。切向由±Y转轴与实际刀轴叉乘确定。接触点从各动作真实Steel刀面重取，代理骨锚随各源输出。

源阶段边界保持0／.65／.90／1.10／1.75秒，真实接触key为1.00秒。现有LEFT／RIGHT游戏时长为550／180／200／600ms，Root按阶段区间映射，角色与玩家视角的方向语义在接线时明确核对。正常循环尚未调用这些方向动作，Root与各自clip、代理一起接通。

## 阶段5回报与三攻击bank冻结

**阶段结束，等待Root review。** 左右斩与校时正劈的三份完整raw现已冻结，供Root动作bank合入。统一输入为 [attack_bank_inputs.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/candidate/attack_bank_inputs.json)，SHA-256 `70882dead0ea0e006e113a23f90098aea6ec777cd2c1d9cb3084a1285808ae24`。完整路径、预览SHA、实际接触面、校正次数、时序和切向均在清单内。

### 三份冻结源

| clip | raw文件 | raw SHA-256 |
| --- | --- | --- |
| overhead | overhead_aligned_raw.glb | `377bcfc1197d1ae84d2c1784dc1de4004b68d09189528025786578c0b95987b9` |
| slash_to_left | slash_to_left_raw.glb | `d0c850d4cb3fba0bff744a2714cc3310f98df4cc6e694d5b34dfc60cb815de65` |
| slash_to_right | slash_to_right_raw.glb | `a4ae7f07c11f96c5a2d9b81c571a5eaedd01cd628983146708926e516768263a` |

文件均在stage5/candidate。raw包含已制作身体／脚／腕／左指曲线，右指校正UNBAKED。每个preview原base的8项右指校正执行一次。独立逐轨重算确认每招8条旋转匹配一次校正，其余226轨数值相等，最大校正重算分量差8.55e-8。当前制作基准为base78骨，其他角色握持与曲线适配由Root统一处理。

三preview完整SHA分别为 `4bf8057da353c4f1ee5037de7c5fe87910887910a9589b44d39105a5a55c7bd9`、`4c0d898a4078b3c3b9651f3fcba91b5acfd6a519b7757003a28715aa22b3fb21`、`149340854a45e8191c277819d304a64ed202c45a4ab7794da894ef9c84e47ae2`。早期左右.90秒接触版已被本次1.00秒版取代。旧stage4保持冻结，仅用于来源追溯。

### 接触与方向

三招106个60Hz LINEAR采样、源0至1.75秒，接触统一在1.00秒，对应ACTIVE中点100ms。正劈以冻结stage4完整TRS分段重时标，新0／.65／1／1.1／1.75映旧0／.65／.9／1.1／1.75，重采后腕位最大差约.046mm、鞋面中心约.058mm。

| clip | 刀尖X@.90s(m) | X@1.00s(m) | X@1.10s(m) | 实际主切向 |
| --- | --- | --- | --- | --- |
| overhead | -.125650 | -.090107 | -.130107 | 向下−Y |
| slash_to_left | -.682599 | -.067192 | +.752867 | 角色左+X |
| slash_to_right | +.498293 | -.063109 | -.961526 | 角色右−X |

清单逐时刻另给真实刀尖XYZ、source+X刃切向及h=1/120源秒中心差分速度，单位为m/source-second。上述.90至1.10大窗口差分仅用于方向核对，不与小窗口瞬时速度混用。contact处重时标两侧速度可不同。

现enum定义为玩家来刀侧。实际左斩从玩家左侧进入并向玩家右扫，对应LEFT；右斩从玩家右侧进入并向左扫，对应RIGHT。依据是实际入射轨迹与防守side规则。prepared+X是角色左侧，也是正面玩家画面右侧，源名描述角色切向。左右游戏时长550／180／200／600ms需逐阶段映源区间，正劈650／250／200／650ms各阶段速率为1。

左右真实Steel接触点分别为(-.104616,1.293127,.90)、(-.025353,1.343339,.90)m，来自各自刀面；正劈为(-.090065,1.363619,.90)m。源1.00秒实际三角面到记录点误差均低于.001mm。每招106帧骨锚见stage5/audit的各自joint_anchors文件，Root据同源生成新代理与播放相位。

### 制作、验证与限制

右斩初版出现15个离散时刻空手穿刀，调整引刀护手至(.34,1.48,-.05)、触刀护手至(.24,1.38,.05)后消除。右持刀目标保持，原抓握未镜像。首尾234轨均与冻结overhead守势相同。

三完整候选各16项拒绝回归及100ms时序断言通过，左右pose板各16项通过。实际刀面审计每招覆盖106个key与105个补间中点，共211时刻，左手／头颈均0个BVH候选、0对已确认交叉。正劈最小手／头间距197.717／24.502mm，左斩112.526／168.027mm，右斩97.428／94.012mm。可复跑脚本与报告在stage5/audit，明确各最终SHA。

鞋底曲面余量沿用原制作基准。新时标下最大足底低带水平滑移约1.404mm，补间最深下探约.128mm，保持实测披露。有限采样不证明无限连续无穿插或C1。PICO运行、三角色适配、正常循环入口、实际判定同步及FX接线由Root整合验证。

### 可见产物

- [左斩三视角板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/review/slash_to_left/slash_to_left_three_view_board.png)、[右斩三视角板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/review/slash_to_right/slash_to_right_three_view_board.png)，已目视全部30视图，接触图为源1.00秒。
- [最终左斩短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/review/video_bank/slash_to_left/slash_to_left_front_side_continuous.mp4)、[最终右斩短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/review/video_bank/slash_to_right/slash_to_right_front_side_continuous.mp4)、[校时正劈短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/review/video_bank/overhead/overhead_front_side_continuous.mp4)，各22个12fps真实源采样。最终三视频统一3.3m正交比例与世界相机，覆盖正劈补间最高刀尖，旧尺度短片已清理。
- [最终渲染方法与限制](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage5/review/directional_visual_review.json)，记录三招全66个连续时刻与统一机位身份。

本阶段超出30分钟，追加了实际补间穿插修正、ACTIVE中点校时及三攻击输入收口。按已授权队列，三raw冻结后接续防御支撑／被弹反卸力／受击制作。

## 阶段6回报

**阶段结束，等待Root／09 review。** 两类敌人状态候选、最终短片及审计均已完成。首版两姿态板约00:45可见，超过30分钟首图目标约3分钟；后续补齐依赖闭包后重建，12个GLB的字节与SHA均保持相同。

### 语义、产物与事件源

| clip | 角色语义 | 连续源 | raw SHA-256 | preview SHA-256 |
| --- | --- | --- | --- | --- |
| guard_brace | 敌方举刀承载、稳住支撑 | .80秒／52键 | `c2b80547b2c2e3199caf9713ba9e39c641d595b0f1f5b9ac0377786ca4f263cc` | `8937250292c06364b08f5fb29d1f7df25daf31c80a4a642b1b4cbd1032399248` |
| parried_recoil | 敌刀被玩家弹开后的卸力破势 | .85秒／55键 | `f3eb395277dd8df673fa74836e6e1c568552bbe4d30710f19d1162a3490e3691` | `eb3dd3946352aedb32aeeeb9335e1ee0fd420c63e1a31433ae72034e38c746c2` |

文件在 `hand-poses/attack-keyposes/stage6/candidate`，连续源均标准LINEAR TRS，另有五姿态STEP审阅板。raw右指校正UNBAKED，preview原8项右指校正一次。原rest、骨长、mesh、skin、weights、IBM及刀长保留。

支撑事件／建议持姿时刻为源.26秒，Steel面点(-.128084,1.829010,.45)m。破势事件为源0秒，入口raw与preview全部234轨分别精确匹配冻结overhead_aligned源1.00秒接触帧，末帧回到canonical guard。其钢面点为(-.090065,1.363618,.90)m。该入口当前只证明OVERHEAD被弹反，左右斩入口尚未覆盖。

本轮选择支撑抬刀、躯干约2.5cm后移与小幅下沉；破势右腕侧后撤、肩腰向角色右侧卸力后回守。具体中间姿态、刃向和时点由本轮制作补齐，均在各parameters与metadata。现有550ms敌破势时长如何映.85秒源由Root接线决定，本轮保留正常源时标。

### 实测与依赖修正

支撑每份15项、破势每份17项拒绝回归fresh通过，覆盖来源、入口、重复／无效参数及依赖漂移。左右原握持、一次校正和入口／出口逐值核对通过。两类曲线按实际蒙皮检查52+51／55+54个key及中点，左手／头颈均0个BVH候选和0对已确认交叉。最小间距分别为支撑276.191／181.461mm、破势268.318／83.460mm。足底低带最大水平位移约支撑.132mm、破势.768mm，最深补间鞋面下探约.076mm。

共享producer由Root并行更新。原loader先后因整文件身份和decoder实际变化拒绝复跑，已检查当前API，补齐stage3脚本的stance.SOURCE_PINS、几何accessor及实际静态依赖。Root helper去除未使用offhand分支、decoder增加重复目标拒绝，合法曲线语义保持。用当前依赖重新构建，12个raw／body／preview逐字节相等。证明见 [dependency_rebuild_report.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/candidate/dependency_rebuild_report.json)。公共及旧阶段源文件保持各自所有者维护。

### 已见姿态与限制

- [支撑五姿态三视角板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/review/guard_brace/guard_brace_three_view_board.png)
- [正劈被弹反卸力三视角板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/review/parried_recoil/parried_recoil_three_view_board.png)

已目视全部30视图，支撑抬刀与卸力侧摆可区分，刀尖和脚底均入画。有限过渡采样不证明C1或无限连续无穿插，实际游戏触发、各状态映射、三角色适配与设备画面仍待Root整合。左右入口补齐及受击动作接续队列执行。

- [支撑连续正侧短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/review/guard_brace/guard_brace_front_side_continuous.mp4)、[破势卸力连续正侧短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/review/parried_recoil/parried_recoil_front_side_continuous.mp4)，11／12个实际时刻均已目视。
- [渲染方法与末帧修正](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/review/defense_visual_review.json)，LINEAR末帧在duration之前10微秒取样，避免Blender NLA端点回到入口；模型自身末key已逐值证明为guard。
- [支撑表面审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/audit/guard_brace_surface_review.json)、[破势表面审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage6/audit/parried_recoil_surface_review.json)，已按最终metadata与29项实际依赖闭包fresh复跑，骨锚在同audit目录。

## 阶段7回报

**阶段结束，等待Root／09 review。** 左右攻击被弹反的入口源已补齐。三攻击raw未修改，新角色语义是敌人的左／右攻击被玩家弹开后卸力。

| clip | raw SHA-256 | preview SHA-256 |
| --- | --- | --- |
| parried_recoil_left | `3619bd24c4d25ac6d183e0b9cc2ab1a950a52a437aa37005a9a3cfbed122609b` | `8fde4d6ba500e029d3b2baca807458599169c232a6dca54f66d3dc0d26818257` |
| parried_recoil_right | `22f0879fecbbebc2b2313229551e17838a1efcd76900c5cfaa09ecb7f92f4802` | `ca482d661da4cab6a3868ad636a4d311b7015abed99c32bab17409cc176c4970` |

文件位于 `hand-poses/attack-keyposes/stage7/candidate`，每源.85秒／55键LINEAR，另有五姿态STEP板。raw原右手抓握未校正，preview原8项右指校正一次。源0的234条raw／preview TRS分别精确匹配最终slash_to_left／right源1.00秒接触帧，末canonical guard。左入口顺角色+X卸刀，源0／.18／.26刀尖X约-.067／+.356／+.708m；右入口顺-X，约-.063／-.413／-.726m。中段护手、腕位与肩腰参数由本轮制作记录。

### 验证与可见交付

四份候选各19项拒绝回归通过。两完整源各55key与54中点共109时刻，左手／头颈对实际DAO均0个BVH候选、0对已确认交叉。左入口最小间距158.221／151.687mm，右入口123.608／58.597mm。足底低带最大水平位移约.721mm、最深下探约.071mm。36项依赖及六项错误源／入口／数学依赖拒绝回归通过，各55行7骨与刀端点由audit统一导出。

- 三视角板 [左入口](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage7/review/parried_recoil_left/parried_recoil_left_three_view_board.png)、[右入口](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage7/review/parried_recoil_right/parried_recoil_right_three_view_board.png)。
- 连续正侧片 [左入口](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage7/review/parried_recoil_left/parried_recoil_left_front_side_continuous.mp4)、[右入口](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage7/review/parried_recoil_right/parried_recoil_right_front_side_continuous.mp4)。
- [可复跑审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage7/audit_parry_entries.py)与同audit目录两表面报告／骨锚，[渲染方法与骨锚校验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage7/review/parry_entries_visual_review.json)。

本轮交图延后，原01:45首图目标未达到，最终图在11日中午收口。渲染改为单一直接Action＋action_slot求值，取消NLA路线与STEP端点补丁，源0至.85秒精确覆盖。入口、出口及内部抽样6骨数值校验最大约6.338e-7m，全部30静图及24视频采样已目视。动作源、有限采样与渲染证据未证明设备手感、C1或无限连续无穿插。550ms破势如何映.85秒源及状态选择由09接入。

## 当前阶段8与新版分工

已读12路制作入口与新版文件所有权。当前制作hit_body／hit_head源，保持现消费者.05至.72秒映普通HIT300ms或实际扩展时长；hit_head同时覆盖执行前段.10至.595秒。源正常时钟不烘焙短停或死亡慢动作。0／.05／.72严格canonical guard，实际front mesh标记与骨锚已产，正常1.5m视距前后图及300ms播放还在制作。

本路后续重点为可见重心、蓄势、支撑、卸力和转身，三攻击stage5源保持冻结。与09共享源时点和入口语义，应用接线由09与Root维护；服装跨动作穿插由01／03交换源姿态处理。遵循新版每路最多1个Blender进程，避免并行制作争用。

## 阶段8收件回报

**技术首版阶段结束，等待review；表现仍需加强。** Root已收件并要求先冻结，当前优先级让位于canonical locomotion HIGH。

| clip | raw SHA-256 | preview SHA-256 |
| --- | --- | --- |
| hit_body | `8213e52e9dacb9885db17c72326444dbb4db2545d57f15e264552e0cfbdaab0b` | `74d0ad940352944f86e192dc711aad372086d6081af2f7250ba959fe00c2f139` |
| hit_head | `16e4f5a8e4d0fd186addee366798494eb89d6e8b9429c51af9595967b72e9a42` | `910732b624578ab77ac503d8a7cda5205365f5e3212f56c1b3bdf629ddde304f` |

源在stage8/candidate，每段0至.72秒／48键LINEAR。raw右握UNBAKED，preview原8项修正一次；源0／.05／.72的234轨分别精确canonical guard。正常HIT继续使用.05至.72源映300ms或实际扩展HIT时长，入场跨姿态仍由既有25至55ms crossfade处理。hit_head保留处决读取.10至.595源，450ms×1.1源速闭合；头峰值后仰12°、.595仍约8°。正常源时标未烘焙短停或死亡慢时钟。

四份源／审阅板各16项失败回归通过。两源各95个key及中点无左手／头颈穿DAO，执行前段额外65时刻通过。源.05真实身体前表面点为(0,1.25,.130143)、头部为(-.001364,1.542499,.128832)m，均来自实际body primitive0、tripo_mat；骨原点和Steel标记均被负例检查拒绝。每源48行7骨与刀端点在stage8/audit。足底最大低带位移约.166mm、下探约.048mm。

[1.5m身体受击首张对照](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage8/review/hit_body_1p5m_pain_before_after.png)已出，eye1.62／aim1.05／vFOV75°，源.23对应正常HIT约80.6ms。脚底与守势衔接改善，但新躯干、视线和手臂仍接近招架轮廓，正常视距痛感偏弱。初图旧基线取idle锚还有约6至8cm水平recenter局限，不能作为最终严格对齐画面通过证据。正常300ms与450ms执行片尚未完成。限制见[首项方法记录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage8/review/hit_reactions_visual_review.json)。后续应明确压身、头部回避、刀臂失去完整防线与收拢护腹，按正常视距再审；当前源冻结。

## 阶段9收件回报

**阶段结束，等待Root／09 review。** 原同源步态版已交完整数据与正常视距对照，保留来源；Root随后要求全周期核心锁定，正式优先候选改在stage10制作，本版不冒称符合最新锁链合同。

输入为 [canonical_locomotion_inputs.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/candidate/canonical_locomotion_inputs.json)，SHA-256 `812142fcfa1a14c1841fd084619ac8e0d6eb73c5d791f5c80861cb07291a53fb`。

| 源 | raw SHA-256 | preview SHA-256 |
| --- | --- | --- |
| guard_idle（idle） | `77a132d6b956933118a829b8f421e37c04ee75d5e7c7d7ecf12dbb64180ba292` | `3d3ee7fdf5ed6eaef45152cd4650a14f787882e18c6bc763b13ec40e0587da1f` |
| guard_walk（walk） | `6fcc10d4e5743bb0d57d37d92e8b7bee0c51d6b7f24b495a460811c8f37b14f5` | `a5622eb12d06d2893be4595771ccf7e041a6f18d984b583584d21f259e2aa66c` |

97键待机1.6秒、49键行走.8秒，均新78骨源，右指未烘焙／预览一次8项修正。首尾raw／preview234轨精确同stage5 canonical。行走是新造的两骨IK与真实鞋面轨迹，周期.52m、载体.65m/s；摆脚前移.26m加载体.26m，单脚一步世界距离.52m。source后摆与世界支撑分列，加入载体后L／R支撑低带位移.149／.076mm，实际离地峰50.0002mm。

193／97个key及中点检查无左手／头颈穿刀。97／49行锚包含完整列主序W矩阵、scale、骨原点、同帧校准centre、Blade与足相。对canonical旧offset的相对中心变化，idle约1.4mm、walk约8.5mm；原输入显式记录这类bob。该相对闭合不等于Runtime绝对贴合。

- [正常守势图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/review/guard_idle_normal_before_after.png)、[载体步态五时刻图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/review/guard_walk_source_carrier_keyframes.png)。
- [步态前后连续片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/review/guard_walk_carrier_normal_before_after.mp4)，24帧／30fps／精确.8秒，固定相机距初始2.02m至结束1.50m，世界载体+.65t。
- [待机连续片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/review/guard_idle_carrier_normal_before_after.mp4)、[方法与消费者边界](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/review/guard_locomotion_visual_review.json)。已看五时刻图和守势图，团队覆盖72编码时刻。旧idle是资产基线，旧walk保留历史consumer映射，.8s窗口只走旧周期35.86%，两者并非同旧循环边界。

### 独立HIGH与09接入点

[runtime_alignment_findings.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage9/audit/runtime_alignment_findings.json)已用正式app同SHA的base GLB `0c2a4801…9af7d48a` 和profile `ee2335d5…90f5f` 实测。attack_overhead源0真实Head网格bbox中心x=-.005025，旧idle局部offset算出的head proxy x=-.247932，横差.242907m，总距.243101m；body主要横差约.232m。body Y覆盖语义与ROI不同，仅列数据。

当前moving IDLE仍取standing常量、stationary取attack首帧，两分支原中心跳差约25.4cm。统一Stage O与Ry均只一次，profile已烘-.028m、entity另+.028m，未发现专属X补偿。新raw闭合只能解决源姿态一致性，**HIGH仍需09／Root重标新canonical实际网格对应的bone_local_offsets并统一moving分支**，不能以骨原点或源循环闭合宣称Runtime已关。实际W×offset需保留scale。

本版.8／.52协议不能直接复用旧start1/3、duration7/6、stride1.45；stage10将保留旧窗口与总距，作为最新优先输入。Rootproducer还需同组处理idle／walk／三攻击的target grounding，entity+.028一次。三角色target、实际180ms淡入与SDK效果由09／Root验证。

## 当前阶段10优先执行项

依Root最新要求，所有Head至scene root的真实祖先（含Armature／BoneRoot／Hip／Waist／Spine／Neck／Head）全周期local T/R/S逐值同canonical，实际只重作六条腿旋转，非在旧walk上遮上身。常量轨STEP、腿LINEAR是标准混合采样，原骨／mesh／rest／IBM保持。

为同时保旧loop[1/3,1.5]、stride1.45及真实腿可达性，采用一个loop三对／六步，每对.483333m、每半步载体推进.241667m。实际游戏.65m/s时whole loop2.230769秒，旧source rate约.5229885保持。原双步1.45尝试需腿根至踝.999038m而真腿长.741414m，已拒绝，无伸骨／降Hip。六步范围接近原canonical足位，可达实证后才输出。

15:50首个合法6步模型已产；腿120Hz为本轮唯一加密，锁链和旧消费窗口不变。最终raw／metadata／完整SHA、同帧W骨锚与足底样本已冻结，正常1.5m可见片与三帧图已完成。三攻击stage5以及已收件支撑／卸力／受击保持冻结，不编辑public producer、正式库或09源码。

## 阶段10源交付

**首张新源实图已落盘。** [锁链步态中步图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage10/review/locked_guard_walk_midstep_before_after.png)，目前文件虽含before_after命名，内容仅新源after，不能当作前后通过证据。源.916667秒／游戏1.115秒／载体前进.725m，头、刀、脚全入画。1.5m连续walk→停步guard与三关键帧正在优先输出，raw保持冻结。

**阶段结束，等待Root／09 review。** 源、独立审计与正常视距可见交付已完成。唯一优先输入为 [locked_locomotion_inputs.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage10/candidate/locked_locomotion_inputs.json)，最终SHA-256 `3a3090ba4181f84169df9e8d7374505ddab5ff4cf3948d183800b116143feab6`，已回填最终骨锚与审计身份。本清单替代阶段9对运行常量的修改建议，旧来源保留。

| alias | raw SHA-256 | preview SHA-256 |
| --- | --- | --- |
| idle | `f1aa9efbb2060c36df2047021fcdc1d1b1127a25bae876513c755aa73da486b1` | `79a93fc6bf2185e1367ceac1e1dc3374f129971cf07267d5d33879f00ddb8c4b` |
| walk | `0e3a6c60c557cfbdfa979ffd9c98098c4d0306474f8e18dc7ae46f327ceb534e` | `f9bebc74195b577e1e875edc80be4602bb08f96f6332f085c13b84fcf6ad7b82` |

对应文件在stage10/candidate，为locked_guard_idle／walk_raw.glb及preview.glb。91／185个实际源key，原78骨rig／mesh／rest／IBM保持。raw右指UNBAKED，preview原8项右指校正一次。所有上身及根链常量STEP、六条腿旋转LINEAR，属于标准混合采样；没有以五pose STEP替代连续腿运动。

### 完整锁链与旧节奏兼容

从Head沿实际parent至scene root枚举，raw9个祖先、preview加两层外Root共11个祖先。全部key及中点local T/R/S逐值与canonical存储值相同，Head／Hip／Spine02／RHand世界矩阵及旧offset相对守势proxy差为0。源0、loopstart1/3、末1.5的raw／preview全部234轨同canonical；prefix所有234采样也已实测相同。

保留旧WALK_LOOP_START=1/3、DURATION=7/6、STRIDE=1.45。一个loop为三对／六步，每对世界.483333m、每半步载体.241667m，实际carrier.65m/s下完整游戏周期2.230769秒、旧source速率约.5229885。1.45m是六步总前进距离，未伪称双步幅度。原两步设计末支撑需.999038m，超真腿长.741414m，已拒绝；正式六步全部可达，没有降Hip或伸骨。

### 足底与同帧数据

[独立审计脚本](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage10/audit_locked_locomotion.py)已实际复跑，idle181／walk369个key和中点均无左手／头颈穿DAO。六段支撑分别应用carrier并重置参考，左最大低带位移.164mm、右.065mm；六次摆脚世界步距约.483333m，离地49.899至50mm。source carrier1.242857m/source-second乘旧rate得到游戏.65m/s，禁止把两种时钟混用。最深离散鞋底下探.146mm，仅为制作数据，不是运行标准或C1证明。

同audit目录包含91／185帧8骨锚，给Head／Spine02／Hip／RHand／双Foot／ToeBase完整列主序W、scale、原点及旋转，另列Blade、载体与足相。清单已写骨锚完整SHA和鞋样本路径。七项源／依赖／采样模式／外Root误移／旧stride／carrier单位错误拒绝回归通过。

### 09／Root集成边界

本源关闭的是核心姿态变化这一层。源相对锁定不能消除旧profile的绝对偏差，阶段9已实测头.243m与body主要X.232m错位。Root／09仍需基于新canonical真实mesh重标局部offset，统一moving／stationary代理分支，完成同组target grounding与entity+.028一次应用，随后在实际发布模型与SDK180ms交叉淡入中验收。三角色target适配、任意步相起停、转向、SDK混合采样加载及PICO观感尚未验。当前不宣称Runtime HIGH已关闭。

## Root本轮组合审核与续派（2026-11-11）

审核：stage10 idle／walk源和369个key／中点的锁链与足底报告已收件；原始rig、一次右指校正、guard共同端点保留。stride1.45为六步总距离，不能再以旧两步音步消费。Root已看1.5m tracking三关键帧，步态／停步守势进入开发组合；最终三target绝对代理与native连续性仍待验。

下一步：当前raw与图冻结。Root唯一producer按schema3接locomotion78，并消费05冻结34ce；09复用同源时钟/actual profile、11同步六步音频。未完成三target绝对body代理与native画面前，absolute HIGH保留。

### 阶段10最终可见交付

- [1.5m行走→停步守势连续片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage10/review/locked_walk_tracking_stop_1p5m.mp4)，79帧／30fps／2.633333秒，离线actor-relative跟拍，eye1.62m、vFOV90°。
- [起步／中步／停稳三关键帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/attack-keyposes/stage10/review/locked_walk_tracking_triptych.png)，已目视全部三帧。最终f9bebc74源及现有原rig／刀／握持未改。

六步按.65m/s载体前进1.45m，约2.230769秒完成。随后停止载体，源准确钳在1.50秒／Action frame45，实际再渲染12帧canonical guard保持.4秒；相机水平距始终1.50m，停步后cameraZ=2.95。末帧没有复用较早的source1.484步态帧。实际静守与核心链稳定可见，脚下世界网格保持固定。

本轮按Root最新优先交新源after-only，原先旧资产完整前后对照尚未作为最终证据交付。FOV90°看胸构图里刀尖部分贴近／超出上边，头、双手、脚与完整停稳动作可见，限制需随片保留。此片示范整循环结束后保持同canonical pose，并未运行SDK两controller的180ms过渡或任意步相停步。15:50首模型在45分钟窗口内出现，完整可见交付明显延后，已保留实际时间与限制，未用数值代替画面结论。
