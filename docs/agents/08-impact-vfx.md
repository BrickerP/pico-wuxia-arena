# 08 · 运行时攻击／弹反／防御／闪避特效

## 当前Root审核与执行合同

Root已把`native-impact-polish/01-local-native-impact.patch`和`surface-preload/02-remove-unused-surface-route.patch`接入正式app。APK`ca26f4a9…`已构建/安装，336项当前单测通过；真实PICO Emulator完成失败→重开→三轮胜利967分/余40HP。源码已无EnemyHitFlash/BodyFlashMaterial与废时长字段，SOFT/METAL保6槽，头手/输入/伤害/时钟保持。旧候选“未改app/待合入”仅为制作时快照，不再表示当前状态。

Root实际看了交战和胜利画面，整身平色替换路径已退出；细粒子效果和Space Pro触觉仍不能由代码通过推定。主机约57fps窗口录制不等于终端性能。

下一件只在`ArtSource/refinement/effects/native-blade-trail-polish/`精修现有刀轨：当前`artifacts/native-ui-impact-2026-11-13/contact-detail.png`中的宽灰硬多边形需要变为有渐隐边缘的细亮刃线/短弧。保真实Blade_Base/Tip、65ms寿命、失追踪/换代断史、当前头手与判定，不做新特效系统或相机抖动。优先现有资源和公开SDK材质，交能接入当前APK的最小patch/必需小资产和实际源轨迹检查；不靠离线画弧宣称原生改善。

唯一交付仍为Kotlin + PICO Spatial SDK6.1.9原生APK，PICO Emulator验证、Space Pro/OS6终端。禁止HTML/Web/mock，不能接入的研究/重复渲染停止。Root统一正式源码/构建/设备/Git；本路不碰app。每次最多1Blender2线程，交可见首件再等对应review。

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

## 阶段2当前任务与入口复核（2026-11-12）

本轮首件：普通身体命中、弹反各18帧／30fps／0.6秒的完整离线接触包络，固定1.5m参考面与80°水平视角，显示核心／12独立颗粒／寿命回收；另交既有真实采样刀光的0.6秒连续回放。仅复用当前正式GLB，无新资源预载，无玩法变化。源码来源以本轮source_start.json与最终文件SHA记录，不执行Git命令。

### 当前真实消费入口

Main.kt把ArenaSession的ArenaPresenter回调转给enemyPresenter；HomeStage在加载后注册owner::presentArena。ArenaSession.publish把当批事件events.toList送入回调；SceneOwner.presentArena先effects.present，再bladeTrail.present。CombatEffects.present按事件ID消费一次，检查场景／暂停／输入／终局例外，按致命／弹反优先，再选择SOFT／METAL池；ContactParticleEmitter.emit设置真实接触锚点、TBN、age，随后每帧update推进到回收。PlayerBladeTrail仍直接消费ArenaViewState里的真实刀根／刀尖、tipSpeed、atRest和motionGeneration，不由命中事件画固定弧线。

已核对：5份app正式GLB均与resource_handoff.json SHA一致，motion要求节点均存在；ArenaSession已保留contact.tangent。普通移动SOFT_HIT会走core／scar／12chips消费分支，PARRY会走metal/core／12sparks分支。现有结构与资源核对能证明入口接通，尚无本轮原生触发到像素的运行证据。

本轮最小代码改动为CombatEffects中的逐新事件日志：`ArenaEffects: Contact consumed id=… kind=… family=… accepted=… mode=core_particles|core_only ageNs=… round=… origin=…`。accepted表示消费器接受该事件；不是可见像素、命中判定或原生输入证明。事件ID去重后只记录一次，无逐帧刷屏。Root可将它与实际生产事件和原生输入日志按时间／ID配对。本轮未运行共享构建或设备，所以这条新回执尚无实际输出。

### 新发现：合法弹反可能缺来刃切向

旧“emitImpact漏转发”已修。本轮发现的是另一问题：判定允许fastGuardAt后180ms内弹反，但defenseContact在当前护刀已静止时tangent=null，消费器于是按安全策略仅显示核心，所有方向火星隐藏。当前ArenaSession把点吸到enemy blade，但未同时改normal/tangent，它们仍可能来自玩家护刀代理。

已向Root发送最小数据修复要求：从实际enemy AttackProfile相邻pose，按同一刀段接触见证点计算incoming位移／切向，吸附点时一并转发；不可用继续null/core-only，不用刀轴、固定左右roll或预设方向猜。Root补“快速架刀后静止、仍在PARRY_WINDOW”的事件回归，并检查三方向。08不越界修改Core／ArenaSession。预演将使用明确示例TBN，不隐藏此运行时缺口。

暂停、重开、场景释放和预算复核未见新缺陷：暂停前先消费事件ID再clear，恢复不重播；roundGeneration变化清空池与去重；close销毁；SOFT／METAL各3槽，其余预存3类各1槽，2个force槽，本轮未增加；同批reserved防止重复覆盖，120ms以上与未来事件不排队。

### 已交连续刀光回放

`ArtSource/refinement/effects/runtime-polish/sequence-trail-review/trail_sequence_0.6s.mp4`与`trail_sequence_timeline.png`已出。仅回放2026-11-11的49帧90Hz DESKTOP导出网格；本轮两份刀光源码SHA与该导出清单完全相同。18帧固定相机，空网格清屏，最后一帧显式清屏，0.600000秒与全片解码检查通过。最后的显式清屏只证明回放边界，不能称为新的生产静止事件；没有假定此刀光fixture有真实命中。

普通／弹反两条0.6秒预演已完成，实际交付与限制如下。

### 阶段2实交：普通命中与弹反各0.6秒

- `ArtSource/refinement/effects/runtime-polish/sequence-review/ordinary_contact_0.6s.mp4`：普通身体首击25实际伤害的示例，strength=0.625，slot size=1.0075；视频SHA256 `4c1ba1a8bc226c6660084e5266ebfac8f2ffe9e970e2d2de336f4cb757b91138`。
- 同目录 `parry_contact_0.6s.mp4`：PARRY示例，strength=1.0，slot size=1.18；视频SHA256 `8c813b3cabab685845f4ba73baacb457e8598706e4b12973fa2fc9a90f10edf3`。
- `ordinary_timeline.png`／`parry_timeline.png`均含0／33／67／167／300／567ms六幅。普通67ms核心已灭而85ms scar可仍存在；弹反67ms热芯仍亮；167ms颗粒独立飞散；300ms和567ms所有核心与粒子均隐藏。
- 两视频各18帧／30fps，ffprobe确认0.600000秒，ffmpeg全片解码exit0。`manifest.json`含完整参数／相机／接触点／来源与逐帧状态；`delivery_check.json`复核视频SHA／时长／回收及五资源未变。渲染与编码入口为同目录`render_preview.py`，命令及日志在render.log／finalize.log。当前只运行离线制图、数据／帧／结构检查，未运行Kotlin或共享构建。

机位为固定1.5m身体参考点、80°水平视角，两例共用相机；实际突出刀面接触点距相机约1.236m，在manifest中单列，没有把所有接触距离都写成1.5m。角色静态参考姿势只提供尺度与材质语境，不模拟NPC停顿、反冲、控制器或音画同步。接触TBN为明确标注的示例，不是原生事件。

当前正式actor为10clip GLB，SHA256 `ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20`。Blender首次导入因KHR_texture_basisu失败，错误日志保留。实际用本机已有官方KTX工具，把该源26张KTX2的顶mip解码为RGBA8 PNG，并仅在sequence-review内追加到原BIN后生成`actor_published_decoded_for_blender.glb`。原几何、节点、骨架、动画、材质参数与sampler保持，来源／PNG SHA及色彩元数据见`actor_decode_manifest.json`；图头显式标`OFFLINE decoded texture copy`。它不是正式asset，未加入任何运行加载或handoff资源路径，没有改app正式GLB。

已目视两张最终时序板：弹反的短热芯／向外飞散清楚，普通0／33ms的出生叠层仍像偏实浅色团，不能据此宣称普通命中写实观感已通过。此问题连同实际图交Root审；本轮没有为离线图私调已发布素材或新加强度公式。连续刀光回放仍作为单独真实采样几何证据，未与示例接触拼成一次假“原生成功”。

运行代码变化只有`CombatEffects.kt`逐事件INFO回执；`scope_check.json`通过移除日志可逐字恢复开工SHA，证明池、采样、时钟、公式、预设均未改。未增预载资源；未改Core、ArenaSession、HomeStage或Main，未操作设备或注入命中。开工只读核对过一次仓库根目录，其后未运行Git，未提交或推送。

下一步为Root用真实输入取得普通斩／弹反的事件和Stage短片，将`ArenaEffects / Contact consumed`回执与实际触发配对；Root处理静止架刀弹反的incoming tangent后，再按实际1.5m观感决定普通浅色叠层／金属爆发的下一次有界修正。当前两条离线包络首件及入口核对已交，不把原生触发或SDK透明排序当已验证。


阶段2最后复核：离线KTX2解码副本已独立核验，原74,172,904字节BIN完整前缀及所有几何／骨架／动画／材质结构保持；26图色彩域分别为11张sRGB带PNG sRGB块、15张linear无sRGB块，未手工gamma。两张时序板未见明显解码错色或结构破损。这只认可离线来源与呈现合同，不复现原生KTX2的GPU mip采样。当前源码与五资源不再因预演继续调参，交Root按真实触发画面续派。

## 阶段3当前任务：只修普通身体SOFT包络

按Root顶部续派处理浅色硬片／等大软斑。Root已接incoming tangent并回报5新例／28相关例通过，本轮不重复该功能；弹反参数冻结，Core输入由其它会话维护。

已新增纯SoftContactEnvelope.kt，只由CombatEffects对`SOFT_HIT && zone == BODY`选择。Emitter每次emit重写softBodyCut标志，复用槽不会把该包络带进金属／玩家受伤／头部命中。原GLB、motion、ContactParticlePresets与池数量不变。

新普通核心以真实T/B非均匀压薄，38ms结束；scar按原mesh内在34.384°斜率，在非均匀缩放后校正到真实T，60ms结束。缺切向只给32ms小型对称核心，scar／颗粒仍隐藏。原12节点中只点亮8片（0、1、2、4、5、6、10、11），按固定index三档，局部X缩放0.18／0.32／0.50，B缩放0.065／0.11／0.16，初速gain1.55／1.05／0.65，有效寿命不超源寿命且分别封顶135／190／250ms；淡入错开约4–26ms，仅作用透明度，不从delay重新积分。Stage重力、真实age和过期事件门不变。

7项纯Kotlin专项用例已写入SoftContactEnvelopeTest.kt，留Root共享构建执行；本轮不编译。独立数值参考检查已执行，8片opacity总和峰值约3.152（低于3.5），250ms后全部清空，缩放后scar主轴B分量接近0。证据位于runtime-polish/soft-envelope-review/numeric_check.json，明确它不是Kotlin执行或SDK结果。

制图复用阶段2解码副本、实际已发布SOFT资源、完全相同1.5m相机／接触点／灯光，先出0／33／67／167／300ms前后一对时序，不重渲弹反。

### 阶段3最终实交与冻结点

同一1.5m相机、灯光、角色、接触点与已发布资源的5对图已交：runtime-polish/soft-envelope-review/compare_000ms.png、compare_033ms.png、compare_067ms.png、compare_167ms.png、compare_300ms.png。before为阶段2原PNG按字节保持，不重渲；after仅改普通身体包络。第一轮过弱薄屑图归档calibration-thin-1，当前图头为body-cut candidate，不冒称Root已批准。

最终只启用原12节点中的8片；三档opacity peak为0.60／0.45／0.32，B缩放0.065／0.11／0.16，其余速度／寿命／绝对age公式与本节说明一致。0ms只有core/scar两层，33ms最多8片加短核心，67ms核心与痕全灭，167ms6片，300ms全清。没有新GLB、motion变动、额外预载或弹反重渲。

已目视0／33／167ms：掌前硬片和等大软斑已去掉，呈短切向闪口与几片薄屑；167ms仍偏克制，当前只认可去遮挡与层次方向，不认定强打击或原生效果通过。Root可据当前图选择进入真实触发验证，再调实际曝光与可见度，本轮不继续漂移参数。

独立静态审查通过，确认只由SOFT_HIT+BODY选择、slot复用每次重写路由、PLAYER_HIT／头部／METAL/PARRY原公式保持；Stage重力不缩放、delay不重开轨迹、缺切向只对称core。制图18行采样独立复算position/scale/opacity/quaternion误差0，5图输出与原before图SHA核对通过。5份正式资源SHA均保持。

新增7项SoftContactEnvelopeTest已写，覆盖薄口／scar轴校正／缺切向／出生与8片预算／确定性寿命／迟到不重播／重力独立；本轮按禁令未执行Kotlin或共享构建。Root在下一轮共享构建运行该类并复核实际Stage。源码及图SHA冻结清单见同目录delivery.json；参数数值检查在numeric_check.json，制图输入／采样表与独立复核见manifest.json及after_samples.json。本轮未改Core、ArenaSession、HomeStage／Main，未运行Git、构建或设备。

## 阶段4：原生白块归因与私有局部反馈补丁（2026-11-13）

当前唯一写入范围为ArtSource/refinement/effects/native-impact-polish/和08交接。主补丁`01-local-native-impact.patch`、事件数值表`event_values.json`、选择／API／验证说明README.md均已落盘；没有直接修改app或其它会话源码。

### 实录证据与选择

04的原VFR frame47 PTS=926695/90000=10.296611s，三张相邻PNG逐像素匹配原视频解码。该帧主色RGB196/194/179，面部SD约0.0117、两处衣料ROI为常数，脸部种子连通平色色域545,490像素、占画面11.70%；这不是身体表面积，也不是RGB255曝光裁切。前后间隔69.544／238.789ms不能用于推断28ms白闪或38ms粒子的实际寿命，没有共同时间锚也不强配event id。唯一对照板和JSON在frame-evidence/。

SDK／源码归因是EnemyHitFlash把除cornea外9个tripo_* body/head/eyes/neck PBR槽改成同色OPAQUE Unlit；不受点光照明的Unlit直接抹掉材质层次。点光另作用于PBR／其它物体，不是把Unlit人形照白的主因。候选选择删除全身替换机制，而非继续增加材质白闪例外；致命与弹反的更强反馈留给现有局部core／颗粒／单点光。完整退出也移除toGlobal／restore／close的旧资源恢复风险。

主补丁只改HomeStage现有接线并新增纯NativeImpactLight数值策略，删除EnemyHitFlash／BodyFlashMaterial及两旧测试。普通非致命SOFT BODY从222.5/.60/60ms额外点光改为关闭，原局部38ms core／60ms scar／8干碎屑<=250ms保持；PARRY为120/.35/70ms，fatal为160/.45/90ms，HEAD例35/.18/45ms，HARD例54/.22/45ms，GUARD/BLOCK例49.5/.22/45ms。所有事件原PBR始终保持。强度只标SDK参数，不把公有签名未证明的单位写成流明；半径不是表面mask。其它例值见README表与JSON，均是策略样例而非伪造原生事件。

HomeStage复用原contactLight，不新增灯；事件用round-local ID集合去重，普通无灯事件不会延长之前的强脉冲。迟到时取duration-age的剩余时间，future／负时刻拒绝；仍用wall deadline推进，不冻结HMD／双手、不做camera shake，不碰Core输入或战斗判定。

### public API与未使用入口

BOM6.1.9、host知识线6.1；MCP不可用，已读取本机6.1参考与exact core AAR公有javap签名。PointLightComponent(Color4,float,float)、setColor/setIntensity/setAttenuationRadius公开存在。未采用未经证明的局部material mask／surface emit。api-review/保留参考／AAR SHA和签名输出。

presentResolvedSurface湿／闪避／落地真实生产caller为0，未发现湿材质／成功近地位移／实际骨骼落地witness，不造触发。完整入口链和缺失witness在surface-preload/route_evidence.json。推荐其02-remove-unused-surface-route.patch清理无caller API／gate／三类运行预设，预载9→6实例；真实SOFT BODY与8碎屑cleanup保持。01只是被否决的仅过滤loader对照，不建议留成正式死接口。该建议不删除04源资产或已发布资源；与主补丁文件不重叠，可独立审入。

### 已跑验证与未证明范围

候选Native7例＋原Soft7例已在本目录隔离JDK/Kotlin运行，14/14通过，覆盖普通BODY无灯、0伤弹反有灯、fatal强调、HEAD值、PLAYER近脸无灯、迟到／future／精确截止、strength边界与原SOFT生命周期／重力。没有启动Gradle或设备。patch在本目录临时5文件fixture里dry-run/apply，逐路径SHA／删除项匹配，app输入锁未变；表面清理另有独立15/15与17源文件锁。独立只读审查通过。

源码、patch、API和测试证据分别在source_lock.json、patch_check.json、api-review/、isolated-tests/report.json。HomeStage完整SDK/UI编译、Root组合验收包、实际PBR细节／曝光和短颗粒像素仍待Root应用后验证；本轮没有新“修复后原生图”，不把原白块或消费日志当粒子像素证明。


## 阶段5：原生刀轨细化私有补丁（2026-11-13）

Root已接受顶端6cm尾／1cm芯与两边alpha0的接入方向，明确否决前版>30cm单段清baseline。本版已完整移除该距离门与常量，不添加25ms时间门或其它替代阈值；只保留原有rest、失追／motionGeneration、时间回退和65ms历史过期断史。

同一`native-blade-trail-polish/01-native-blade-trail.patch`已更新：patch SHA `75d1af3a124d74cfc147986f76d9e7c709bfae3d472b9b72fd0da52a46d9a779`，Geometry SHA `424e5eecccce9233c90bd3c39d4fa880e42f95edcdee839655ff87cd16c91a2b`。仍只有Geometry、Player两行颜色和对应测试三路径，正式app未动。

保留真实tip末端6cm尾带／1cm芯，共心tip后3cm，尾／芯各3点，边缘alpha0，中心随原age和tipSpeed变化；65ms／12ms、8点、单mesh／material／entity、透明／深度与释放顺序不变。窄带和渐隐直接解决原约45cm宽灰面，不通过丢掉合法快速反馈规避问题。无新资源、HTML、相机抖动，输入／判定／伤害／HMD／双手保持。

19项必要几何测试重新执行通过；原距离拒绝例已改为同代快速挥刀保反馈，0.30m、nextUp及0.60m在33ms内均继续输出窄带，同时既有65ms／12ms、rest／generation等边界通过。补丁仅在本目录临时三文件fixture里dry-run/apply和SHA核对，正式app源锁原样。

按Root要求不扩或重跑unknown-rest假设组合，不追加研究／渲染。native-replay/的194条原源及6项结果只保留为前版证据，不冒作本版连续原生像素证明。当前结果以isolated-tests/report.json、patch_check.json和delivery.json为准。Root下一轮直接进APK看实际像素；本轮没有发现或暗混其它原断史／真实caller修复。
