# 08 · 运行时攻击／弹反／防御／闪避特效

## 当前状态

阶段1运行源码和候选已交：普通命中独立碎屑、金属普通／弹反逐粒运动、真实65ms尾迹＋12ms亮芯。Root发布前需应用root-tangent.patch并按resource_handoff.json发布5资源；未做共享构建或端内验收。2026-11-11用户要求扩大并行，整体品质需明显提升。

## 目标

把现有偏小、偏弱的核心火花提升为清楚且有材质差异的打击反馈。参考《只狼》《鬼武者》《影之刃零》的接触节奏与招架辨识，使用当前VR实际头手和接触数据，维持视点实时跟踪。

## 所有权

负责 content/CombatEffects.kt、PlayerBladeTrail.kt、BladeTrailGeometry.kt、新的ContactParticleEmitter／轨迹模块、ArtSource/refinement/effects/runtime-polish/及专项测试。本文件为交接。04继续独立颗粒／近地资产制作，你负责SDK接线。CombatAudio和Profile由11维护，HomeStage／Main最终接线归Root。

允许你最小扩展 core/combat/CombatImpact.kt 和 PlayerCombatResolver.kt 的每次接触切向元数据，保持既有阈值、碰撞规则与伤害公式。ArenaSession由09维护，给Root emitImpact所需的最小元数据转发补丁，不直接修改该文件。

## 制作队列

1. 阅读04的 contact-polish GLB、motion.json、driver_contract和参考采样器。将独立火星按各自初速／重力／寿命驱动，基于真实接触点／法线／同次挥刀切向，事件过期不排队重播。
2. 为金属、布／身体、要害、弹反、格挡、技能与致命建立辨识层次。先做一记普通斩和一次弹反的完整接触包络，正常视距下能清楚看到核心、碎屑与回收节奏。
3. 适当增强真实刀光的热芯／半透明尾迹，沿已有65ms真实采样改进，静止、异常和重建基线仍清理。强化来自当前动作的弧线与接触停顿。
4. 水滴只用于已确认湿衣物，裸头与普通SOFT标签不能自动当水面。缺切向时核心与粒子选择需明确，不用固定左右手roll冒充实际刀路。
5. 粒子数量、尺寸、曝光与不透明度按实际视距调校，单个接触有界预算与可复用池。Root会统一运行实际触发取图，交源码、资源接口与短时序预演。

## 首轮交付

普通命中与弹反两个完整运行时效果，包含可见实物和最小专项验证。随后接湿布、闪避近地尘、落地与技能。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

由负责会话填写真实产物与review问题。


## 阶段1实交 · 独立接触颗粒与真实热芯轨迹（2026-11-11）

**已交运行源码和候选实物；正式资源发布、ArenaSession最后一处转发、共享构建与端内图归Root。** 来源HEAD为 `562449af40ee984ddd8ef61be5c339ac9bea2de5`。本轮保留其它并行改动，没有切分支、worktree、提交、推送或设备操作。

### 本轮肉眼可审的内容

- 普通柔性命中：由正式soft_contact的原材质／RGBA派生，拆为12个独立干性碎屑，接触core扩大、65ms结束，方向切痕85ms结束；碎屑各自180–290ms后回收。无水、无血，SOFT不推断湿衣物。候选为 `ArtSource/refinement/effects/runtime-polish/soft/soft_contact_polish.glb`，SHA256 `19384ff327d9080048ad485422c64b679242281b2b8d7eb77f9f7d6319fce534`。
- 金属普通／弹反：消费04的metal_contact_polish，逐个spark初速和Stage重力驱动。普通65ms核心／弹反90ms核心，弹反飞散速度×1.8、颗粒截面×1.65；金属核心普通×1.9／弹反×2.6（按33ms实物复核后提高），轮廓与回收时长可辨；不整体缩放一团debris冒充粒子。
- 刀光：同一个动态mesh里，65ms冷白尾迹增加12ms暖白亮芯；亮芯来自同一真实相邻采样的时间裁切。保留静止／异常／运动代次清空和首点基线，最多8个真实采样点；不增加固定弧线。
- 0.8／1.5／3m刀光同机位对照：`ArtSource/refinement/effects/runtime-polish/trail-review/trail_compare_0.8m.png`、`trail_compare_1.5m.png`、`trail_compare_3.0m.png`。生产DesktopCombatInput→TrackingState→PlayerCombatResolver实跑49帧，再由两版Kotlin几何输出mesh。图明确为离线软件投影；暖白短芯可辨，3m仍小，未宣称VR观感通过。
- 普通命中三时刻／三视距：`ArtSource/refinement/effects/runtime-polish/review/soft_normal_distance_033ms.png`、100ms、233ms。采用实际GLB、当前正式actor、同机位同灯；是离线预演，非端内触发证据。最终图与来源见同目录soft_render_manifest.json。该普通命中图使用原motion与固定1.019 scale，未模拟consumer额外core growth／accent，作为源资产前后对照。近身接触轮廓变宽，1.5／3m收益仍需Root按Stage画面判定。

### 代码入口与实际路径

`content/CombatEffects.kt` 已接新消费器；`ContactParticleEmitter.kt` 为有界可复用Entity池，`ContactParticleMotion.kt`实现T/B/N、Stage重力、真实年龄、逐粒位置／方向／opacity，`ContactParticlePresets.kt`由motion.json确定性生成，`ContactEventTiming.kt`为真实表面事件一次消费门。软／金属各3槽，湿布／闪避地尘／落地各1槽，另2个技能force槽。新接触优先使用空槽或回收同类最老槽，同批按致命／弹反优先，没有待播队列。

`CombatImpact.tangent`与`MotionContact.tangent`为可空单位Stage向量。真实命中在命中刀段见证点上取相邻扫刀子步的方向，targetContact／defenseContact按真实base/tip位移插值。静止、基线、重建与PLAYER_HIT未知敌刀方向不造切向。消费器投影T到接触平面；无效／平行／缺失切向时只呈现无定向核心，隐藏scar和方向颗粒；已删除左右手固定roll。

Root必须先原子发布5份候选到 `app/src/main/assets/models/effects/contact-polish/`。**完整来源路径、目标路径、SHA与粒子数见 `ArtSource/refinement/effects/runtime-polish/resource_handoff.json`。** 本会话没有覆盖正式app资源。生成入口为 `python3 ArtSource/refinement/effects/runtime-polish/generate_presets.py`；它只生成Kotlin数据及交接清单。

### Root发布前必接：ArenaSession一行

`emitImpact()`当前仍丢弃tangent。必须将CombatImpact构造末尾改为 `fatal, tangent = contact.tangent`，否则新素材只能出核心，所有方向颗粒都按保护策略隐藏。最小补丁：`ArtSource/refinement/effects/runtime-polish/root-tangent.patch`；对应已识别帧→事件边界断言：`root-tangent-test.patch`。两者均未擅自应用到Root／09拥有的文件。

现有 `HomeStage → CombatEffects.load/present/close`入口不变。Stage root为identity，消费器沿已存在的官方Entity加载／Transform／Opacity／convertPositionFrom／convertRotationFrom用法；未新增SDK、依赖、容器或配置。

### 后续授权队列已推进的接口与真实缺口

- 04湿布、v2闪避地尘、v2落地GLB的motion已经编译进统一数据，逐粒运行代码已实现。地尘将Stage重力转成接触局部坐标，底面约束在真实平面以上，锚点只沿真实法线+2mm；接触类统一+8mm一次。
- `CombatEffects.presentResolvedSurface(eventId, roundGeneration, family, point, normal, tangent, atNanos, simulationNanos)`是Root接真实证据的入口，必须在当帧present之后调用。稳定ID／轮次去重，暂停事件消费丢弃，未来／>120ms事件拒绝，hitstop只推进呈现钟而不重启start。
- **当前没有可靠湿衣物材质、玩家近地闪避见证或骨骼实际落地producer，以上接口尚未接游戏触发。** 已移除按敌人累计travel每0.5m冒充脚步接地、DEAD固定1.6／2.35秒冒充落地的旧路径。后续由Root／09提供真实接触事件，再接本入口；不根据SOFT、裸头、UI闪避提示或死亡秒数发水与地尘。
- 技能／处决继续使用原force几何包络，方向scar已改真实切向；本阶段没有重新生产技能特效外形。

### 已运行验证与限制

`python3 ArtSource/refinement/effects/runtime-polish/testing/verify_runtime_subset.py`实际使用本机JDK21、Kotlin2.1.20、SDK6.1.9公开AAR类型与Android35 jar编译这条源码及实际依赖，**47项JUnit通过**。覆盖新粒子8项、表面事件时效4项、既有接触时效3项、刀光15项、切向／既有动作17项。此为隔离子集验证，不运行共享Gradle，也不替代Root的APK构建。

普通候选 `python3 ArtSource/refinement/effects/runtime-polish/soft/verify_soft.py` **6项通过**，含源材质与RGBA保持、独立节点/速度、Stage重力、寿命和缺切向。完整输出与源码SHA在runtime-polish/testing/runtime-subset/report.json；公开SDK来源在testing/sdk_provenance.json。自审发现并修复表面入口无ID造成hitstop冻结／暂停重播的问题，新增4项回归。`git diff --check`通过。

尚未验证：新资源在PICO上的透明排序／Opacity实际语义、首次加载耗时、全部槽并发帧预算、正常视距下的实际命中／弹反画面和手感。离线图、GLB与单元不能替代这些结论。Root必须先发布资源并转发切向，再统一构建和触发取图；不得将当前缺切向时的核心保护表现误判为粒子系统已生效。

## Root组合审核与下一步

Root已原子发布handoff的5份GLB并核APK内SHA，emitImpact已named转发contact.tangent，普通物理事件回归补了切向保留断言。当前强粒子链已接到正常CombatEffects入口，构建与250项组合回归通过。缺少物理证据的湿衣物、闪避近地和实际落地触发仍未冒充完成。下一步Root取实际斩击/弹反短片，按1.5m和3m可见性续派，当前预设和源身份保持。

## Root本轮组合审核与续派（2026-11-11）

审核：5资源与tangent真实扫掠转发均已接入；250→253组合回归已过，但真实命中画面尚缺，不能声称打击观感通过。

下一步：当前运行文件先冻结，待真实攻击/弹反图后按材质、近地与1.5/3m可读性修；不能用假DEAD计时触发落地。
