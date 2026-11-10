# 01 · 按动作与手别精修手姿

## 当前状态

**阶段3收尾，阶段4已续派。** 按clip空手姿态及原生slash左手避刀方向通过Root可见审阅，五关键姿态仍需战斗站姿与完整动力链。当前制作同一记正劈的连续动作候选，正式接入由Root统一完成。

## 上一轮成果与Root review

已发布60k主角、8份动作资源、接触姿态短停／反冲与角色代理。上一轮数学转移和数据校验充分，但七段重定向资源统一锁定双手30根指骨为slash@2.117秒，待机／行走／受击时空手也保持抓握。这是本轮首先移除的旧机制。

## 文件所有权

负责ArtSource/tripo-warrior/prepare_character_library.py中手姿采样／重定向逻辑、ArtSource/refinement/hand-poses/和本文件。prepare_rigged_warrior.py、motion_library.json、正式library/app模型与全部Kotlin运行代码由Root维护。02会话只做分区蒙皮候选，04只做场景配光。

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

本轮允许离线资产生成、渲染及专项制作检查。游戏整局自测继续后置。30分钟内交付首阶段实物，写明“阶段结束”、输入SHA、文件、效果、剩余问题与下一步建议后结束当前回合。遇到阻塞先交已做出的部分并写明具体阻塞，继续能独立完成的工作。用当前模型和已安装依赖推进，不为等审批或等待其他线程维持空转。

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
