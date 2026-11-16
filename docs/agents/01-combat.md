# 01 · 动作源与战斗姿态

## Root续派：真实刀形链与完整Grip（2026-11-17）

静态18薄条已交（41tests），不再以漏45mm的单轴代理作最终视觉证明。新完整Grip制作60tests通过：4281原rows保留，按实际FK曲率新增370行，总4651；key刚性误差≤0.462µm、mid插值≤0.846mm、连续离线工程界≤1mm。旧60Hz多层FK即使端点准也可在中点差14.56mm，不能从base/tip猜roll或放大门掩盖。

`blade-chain-runtime/` 正制作完整consumer候选：6组broadphase/18caps CCD、身体与Steel排序、全链constraint/release、有限yaw+后退和未来恢复认证；需守真实OH主动反例、静持不刷impact、玩家0强迫位移与全部生命周期。528×4同批host查询已计数，空挥0窄相，误差/性能均不能称PICO已过。私有完整候选34项已过，含真实OH、45秒walking与Tracking边缘入招；主产线schema4/正式fixture迁移及APK仍待Root。host plan OH中位15.11ms/最大32.33ms、walking最大63.71ms，性能是明确未解决风险，未装入app，不以安全hold或host数字称终端通过。

Boss cap与动作共同冻结single Upperarm的2100面cap（prepared6dcc9650/raw62c51a96），native_clearance_integration另在 `natural-guard/boss-armor-arm-clearance/` 修空手左臂：OH/LEFT/RIGHT实际回收撞肩冠/裙，旧源也有。不得删前臂/手或加入豁免；保右手钢刀、phase、根头脚、guard，交真实曲线与甲网格审图。Root统一canonical producer/数据/场景合入，不让候选覆盖已发布5180。

## Root 当前评审与下一任务（2026-11-17）

本地组合开发包 binding `51807084…` / APK `57f7cb12…` 已完成460项单测（0失败、0跳过）与模拟器实际输入检查。原生录像证明前两敌倒下、第三敌加载；未证明三轮胜利。有限actor卸力已出现实际后退／转身／恢复，不能据此称所有穿刀已修好。

新增阻断：正式玩家dao默认scene中的5533个Steel顶点，4469个超出当前12mm胶囊；最远离轴56.994mm，即形状局部漏覆盖约44.994mm。证据 `artifacts/native-combined-2026-11-17/player-blade-proxy-audit.json` 仅静态玩家握点空间，不代表敌人／动态蒙皮已审计。Root已启动 `native-steel-release/blade-shape-fit/` 私有制作：先复核模型到query的同空间变换，再交资产派生分段胶囊、全三角覆盖证明、过度覆盖量和叠加图。保持stroke资格轴与碰撞形状语义分开；链形状未接入CCD和恢复认证前，不替换正式判定。不得靠扩大单胶囊或降低HP使验收通过。

## Root review修正：真实未来恢复域（2026-11-17）

**新源码48专项全过、无Ignore；正式构建／原生审图由Root接手。** beginSteelWithdrawal现只认证 `[max(first, contactSource−.06), last]`，精确插入retreat／end／当前TOI及域内keys，保首18%反向0.06；idle保持全loop。当前见证在相同时点优先。没有放宽半空间／CCD／速度或改几何参数。

四项新回归覆盖：真正未访问windup（不改插值必需的左支撑key）扰动不影响selected samples／计划；精确非key retreat、current、end与所有域内keys保全；真实retreat／end几何改变必须重认证；idle完整loop保持。原主动反例、pause／失追／击杀／过期／同ID／真新Swing／新enemy attack及parry停顿等旧专项继续过。

**配对实测没有降角收益。** 同一当前runtime profile由212样本缩到120；原／新均−61.93100461°、1.227053786s、49.5mm，主导约束仍在真实未来域。Source1310ms恢复／1990ms回guard／玩家0位移保持。旧private90点的−62.765°不能拿来冒作修正前runtime数值。

旧44证据及源码已冻结`actor-withdrawal/archive/full-clip-44/`；新版[receipt](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-steel-release/actor-withdrawal/future-domain-result/receipt.json)与[编译测试原文](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-steel-release/actor-withdrawal/future-domain-result/run.txt)绑定当前48项源码。更新[handoff](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-steel-release/actor-withdrawal/handoff.json) SHA `cff0f204c76f97f2c2f25758ae707411b5890f076998130ad95a79cb79150f8e`。下面44项正文是历史收件，不能把其旧SHA称新验证。约62°转身与约2秒节奏仍待原生观感评审；本路未做SDK／设备／构建／Git操作。


## 有限actor卸力收件（2026-11-17）

**本阶段已实现并过专项，待Root原生审图／构建／合入，不宣称成品手感或设备通过。** 旧推手方案保持拒绝归档；骨骼Entity写入不驱动最终蒙皮的Root结论已接受，本轮只复用现有actor根位姿。[交接](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-steel-release/actor-withdrawal/handoff.json) SHA `87fcc932e13d264ad572bc5d1973eb9e7021533ae52084b04d438bcdd23e7fd9`；[说明与入口](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-steel-release/actor-withdrawal/README.md)。

真实有限刀段解析选择一侧退出，不用旧无限平面推玩家手。原90姿态／213 CCD全无接触；49.5mm回撤、−62.765°转身。0.65m/s和1rad/s直接来自旧moveEnemy，改同一路径时间参数为35ms起止速度斜坡＋原满速，actor1.241613s。源姿只在该有限actor阶段暂持，之后既有contactRecovery接回；同一position／yaw／clip／source同时用于query和Scene／EnemyAnimator。玩家raw／held没有敌方强制位移。

private3tests与当前协调器44tests全部通过、无Ignore。实际OH .833333反例source1310ms恢复、1990ms回guard，10ms刀间gap／actor速度、原命中stop和玩家位移0均守门；IDLE顶刀150ms恢复、静止续持不再循环退步／刷impact。真新挥击／新enemy attack重装，同ID补伤／过期receipt拒绝，暂停继续／失追／击杀、parry95ms停顿和新命中打断旧恢复均验。输入基线失效解锁物理，但不清已接受战斗ID以免暂停刷事件。

实际代码仅ActorWithdrawal.kt／ArenaSession.kt及专属tests；未碰HomeStage／EnemyAnimator／数据／SDK／其它候选／Git／设备。新旧失败阶段正文保留历史，不作为本轮状态。Root下一步：看63°转身和约2秒节奏是否自然，确认同APK原生真实输入到最终画面，再决定合入；设备性能与Space Pro另验。无可证路径或CCD不确定仍安全保持，不硬解锁／把不确定当MISS，不承诺任意极端手位都自动退出。


## Root当前合入与接触修复边界（2026-11-17）

RIGHT a726已由Root核对65项身份、审三target实际图，并经同一canonical producer正式重导为binding c3009af3；typed与7项身份fixture已同步，446单测0失败/跳过，正执行新包原生检查。LEFT的target末端约束补丁已经收件，尚待Root审核/合入，不把私有首件计入当前APK。

持续拼刀projection候选因主动OVERHEAD恢复会要求过大的玩家虚拟手位移而拒绝。四个旧app/test文件及新增SustainedSteelDamageTest已从正式树移回冻结归档 `native-steel-release/failed-projection/`，可自含重放失败；不留下Ignore，也不把行走顶刀通过当主动接触通过。当前APK保留已知持续顶刀局限，没有装失败候选。

下一实现由Root专项在 `native-steel-release/enemy-arm-prototype/` 制作：保持玩家实际手位，通过敌方刀方向分离半空间约束与本target两骨IK求腕目标，再让判定和原生骨骼消费同一最终姿态。先交真实OVERHEAD反例的Kotlin求解器/骨长/可达性/刀面gap/玩家位移0数据与坏例，不新造通用物理框架。Root已实际读到6.1.9骨骼Entity，但首读可能是bind pose；正在验证后续时点与写入能否驱动最终蒙皮，尚不能宣称SDK骨骼控制已打通。

## 持续拼刀卸力修复 · 本阶段未完成（2026-11-17）

**30分钟阶段交接：不要将本工作区候选当正式通过。** 实际专项编译通过；首次完整41项中40过／1失败，最终普通suite为40过／1项明确Ignore诊断；未解决的是主动攻击被架住后的恢复仍无法在保持合理虚拟手偏移时完成，未放宽断言。Root已收到禁止按“41项曾全绿”部署的说明。a726／全部资产、正式producer、HomeStage、输入脚本、Git与设备均未碰。

**入口到出口已查实。** `Main`正常TrackingControls把accepted TrackingEvent送`ArenaSession.onTrackingEvent`；只接受当前epoch／continuity／sequence基线，经`PlayerCombatResolver.observe`入pendingMotion；`advanceFight→advanceEnemy`做steel-before-body TOI。首次钢接触锁虚拟Grip并发原BLOCK／PARRY和命中停顿。后续旧`steelContactLatched`分支却只`combat.advanceWhileWeaponStopped`，不增`enemyMotionNanos`、不推进`contactRecovery`，可把实际actor／source无限停在原架刀姿。`viewState.playerWeaponGrip`由HomeStage同时驱动玩家手／刀；`enemyPoseSourceSeconds`由EnemyAnimator主动setTime，Main向Scene转发完整state，不受HUD限流。因此这是可达时钟／约束逻辑缺陷，不能先归模型；旧Native测试还明确断言1秒source／actor／gait完全冻结。Root提供的24秒原生片及9／12／15秒同姿态与该缺陷相容，本路未把新代码当已在设备复现／修好。

**当前候选实物。** 仅改WeaponContactConstraint.kt／ArenaSession.kt及专属测试：固定真实接触支持平面，保持玩家刀旋转，按敌人下一线性刀段对虚拟Grip作单向外推，证明两端支持平面不穿后才推进原恢复钟；首次TOI／命中停顿保留。敌actor只按原0.65m/s走一次49.5mm水平回撤，保持地面高度。钢碰触消费原swing ID；静止物理分开不重装同episode，新合格玩家Swing或正常state machine新enemy attack ID才开始新接触。追踪不改；自动无碰撞catchup重建原motion baseline／清pending，防止虚拟位移变成假挥击；击杀清锁，暂停／失追／过期receipt仍守原门。

**已实际通过。** 真实Tracking Fixture行走顶刀：40ms内source开始推进、49.5mm一次回撤、虚拟Grip与raw最大偏差0；每10ms检查1秒steel gap≥−0.0006m／原接触平面不越过，双方HP100；再静持2秒不刷impact／不再退。慢撤回后不重装，安静后真快速新挥击才有第2次钢接触。暂停／失追冻结与旧事件不重播、过期qualified receipt拒绝、碰钢同swing ID补身体伤害拒绝、带锁击杀释放均通过。core固定平面运动的happy与非法起始平面坏例通过；原接触排序、真实TOI判定、ArenaSession已有恢复／暂停专项也已跑。

**未通过的关键反例，不能掩盖。** 新主动OH真实profile夹具：原forward recovery虽结束，却把静止raw的虚拟手推远1168mm；唯一定位修改改为持续受压时沿原source反向回canonical guard，仍会推远481.6mm。这两版虽“41 tests全绿”，视觉／VR自然性不合格。当前保守门拒绝把玩家手推过既有一接触净空49.5mm，实测最大32.01mm，source90ms开始动，但1.2秒后仍RECOVERING，`aBlockedActiveAttackCompletesRecoveryInsteadOfFreezingItsSourceClock`真实失败（预期IDLE，实际RECOVERING）。这是尚未解决的敌方几何卸力路径，不是需再调大手偏移上限；不能用丢steel／超时硬解锁／更长动作掩盖。初始平面不可证分离或超手位预算时保安全hold并有限警告，故不能宣称全部接触均有限退出。

**测试与复核。** 用现有isolated Kotlin2.1.20/JUnit runner，仅编译必要production依赖，运行7个专项类，最终40tests通过、1个已知限制诊断显式Ignore；主动恢复断言没有删除或放宽，独立诊断包装器实际调用它并确认IDLE-vs-RECOVERING失败。没有全局Gradle／设备／全测试扫描。最终日志：[run.txt](/tmp/pico-steel-release-tests/run.txt)，含完整源码SHA与编译／JUnit原文的[report.json](/tmp/pico-steel-release-tests/report.json)；复跑入口[/tmp/pico-steel-release-runner.py](/tmp/pico-steel-release-runner.py)。最终源码身份与report记录逐一重算一致。测试壁钟不是设备帧率，BLOCK也未称玩家弹反验收。

**Root要求的固定反例已交。** [结构化见证](/tmp/pico-steel-release-diagnostic/contact-witness.json)、[完整诊断输出](/tmp/pico-steel-release-diagnostic/run.txt)和[源码身份／断言报告](/tmp/pico-steel-release-diagnostic/report.json)。profile为`asset://models/opponents/base.glb`／`attack_overhead`，首次contact source=`0.8333333333333334`；首个超预算proposal发生于反向恢复`0.273284624560741→0.27098614534426113`。raw／held／proposed Grip、初始及当前normal、enemy blade previous／current完整米制数值和当前profile源码SHA均入JSON。这里raw是用真实当前profile构造的几何夹具，并非伪称从原生片读取了用户控制器。

普通suite不挂永远失败项：`aBlockedActiveAttackCompletesRecoveryInsteadOfFreezingItsSourceClock`保留原断言并显式Ignore；`python3 /tmp/pico-steel-release-runner.py --diagnostic`以独立[/tmp/PicoSteelDiagnosticTest.kt](/tmp/PicoSteelDiagnosticTest.kt)实际调用，捕获并报告该特定未解决失败。诊断包装器自身绿仅证明失败可重复，不是主动接触通过。候选添加安全预算而非继续推手，未进行第三轮路径／参数试验；后续由Root选择敌腕肘或真实回撤承受接触。

**下一阶段须补。** 在保持raw玩家手及真实steel支持面的前提下，让敌方刀路／root回撤／现有恢复source真正绕开该主动接触；先用上述反例求空间出路，再作原生实物评审。禁止放宽49.5mm预算、删除该失败或只验IDLE夹具。Root应先审这份未完成候选，不能将active路径merge／安装为最终交付；人物动作a726和LEFT专项由各自既定产线继续，不能拿来抵消这个机制失败。当前未跑新APK／新原生片／Space Pro。

源码SHA：

- `app/src/main/java/com/example/wuxiaarena/core/combat/WeaponContactConstraint.kt`：`22cf280a339fc418b83f360526e959d2f35e8513febfbd0b25ecc573edd21e39`
- `app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSession.kt`：`fef60311ac063d07e566c9ef9c1e34bcc2c429e5290000a9cc14a2f017df6c72`
- `app/src/test/java/com/example/wuxiaarena/core/combat/WeaponContactConstraintTest.kt`：`90ac19710cb66c93a6c8c8b3eb180e6056fa94373fa01ebf90c2e2e1faa432c3`
- `app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/NativeEnemyMotionContactTest.kt`：`ce74e75859b80ac3616421590ac4ce87456a81bf02c379e0d65f694cf875473e`
- `app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/SustainedSteelDamageTest.kt`：`998b3e8e69c7d51ba103be321bdf6c37b61b6119ad4fe077aeee4d1678eb65fb`


## 当前专项收件：RIGHT 空手连续回收（2026-11-17）

**本阶段结束，21项独立数值门通过，等待 Root 动态审图／三角色重导／原生验收。** [完整RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/candidate/attack_right_raw.glb) SHA `a726b0f65680b7ac8ed2f4dac15e23d9525054786f398d0068712e7c42705aa4`，[authoring](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/candidate/authoring.json)与[唯一handoff](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/handoff.json)已交；handoff SHA `d82b4d08da5d55bfbe4bcfe58712bba1c966d3b8dab1b31081b8cc730d032547`。Root已拒绝e7df作为最终动作，该版仅作冻结净空起点，下面旧收件不代表本轮状态。

`.9–1.5`只重做L_Upperarm／L_Forearm／L_Hand三rotation：normalized actor-world腕／肘Hermite曲线经逆normalization作两骨IK，空手world方向连续过渡，指local／右刀时标／root／头／脚／rest／IBM／guard／窗口外保持。仍106键／234TRS／78骨、1.75秒、R15 UNBAKED；没有局部q低通代替空间净空，也没有延长整招。仅一次首件，未用定位返修额度／未扫参。

[完整独立复核](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/verification.json)已在共享wrapper实际完成并退出，不是仅28姿态初检：两actual target各45姿态Steel／fullbody＋8区域全0，各39个60Hz完整邻接采样；21门全true，篡改右腕1.1／上臂guard0／左腕窗尾1.5三坏例真实拒绝。实际全部刀点／Head／R_Hand差0；全骨段最大差source5.65e−8m、indigo1.33e−7m、veteran2.20e−7m。private prepared只作验证，不能覆盖Root并行LEFT或其它正式clip。

源三关节最大角步Upper／Fore／Hand由19.63／22.86／36.90°降至15.03／18.75／10.06°；旧1.033→1.05腕36.90°降至7.61°。真实全hand整窗最大跨步indigo87.42→27.30mm、veteran102.76→31.26mm，最大二阶差分97.05→16.81mm／118.07→19.18mm。这里旧全窗峰高于此前特定时点75.73／91.61mm，不能混用。具体point IDs／weights／时域及finger-only另列report，图绑定正式验证JSON。

能看：[Indigo原速对照](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/review/indigo_before_after_realtime.mp4)／[四时点板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/review/indigo_four_times_before_after.png)，[Veteran原速对照](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/review/veteran_before_after_realtime.mp4)／[四时点板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/review/veteran_four_times_before_after.png)。共148张真实原材质PNG，同机位.9–1.5／60Hz；视频左e7df右首件，原速三次重复、111帧／1.85秒，不是延长游戏动作或PICO录像。[源角步曲线](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/review/source_joint_steps.png)／[同target手部曲线](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/continuity/review/actual_hand_motion.png)已出，无第二轮Blender渲染。

**未放宽的边界。** 新二阶差分局部峰在`.8833/.9/.9167`接合，虽全局峰显著下降，不能写成C1／连续时间无尖峰或最终动态审美通过；原角色指形、腕袖源缺口仍粗糙。Root第三角色base、最新全family／并行LEFT组合、profile／typed／binding及PICO原生蒙皮／Space Pro仍待验收。e7df及全部旧证据冻结，本路未动LEFT专项／正式producer／integration／app／设备／Gradle／Git。详见continuity/README。

## 当前专项收件：RIGHT 左空手／胸净空（2026-11-17）

**本阶段结束，等待 Root 独立 review；不自动扩到 LEFT／新动作。** 完整 [RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/candidate-final/attack_right_raw.glb) SHA `e7dfc4ddb5ab85c39be4b23edf8a06f9edca07f0660301eae24785b4d130d8c7`；[authoring](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/candidate-final/authoring.json)、[唯一交接](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/handoff.json)和[制作说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/README.md)已封存。handoff SHA `4bf645d49f83ab1a5d27d12729c0e93659cacf69a9145c101b7a932788a53c4e`。下方 attempt1 的18→6是历史失败，不是当前结果。

**实际修正。** 先在当前 dc0 真实indigo／veteran取得完整18／53对triangle／材质／权重／可见性见证，确定是腕远端的掌／小指侧，不靠权重名称把它当护腕。兼容胸面分离方向主要向前；首件30.56mm使indigo清零，veteran剩28对。对实际原来完全埋入、未落在旧53对边界的点作正向出口测量，唯一定位返修再加10.27mm，总规范actor腕偏移 `[+16.2447,−.27825,+37.4638]mm`，经normalization逆矩阵回RAW。Root明确授权包络 `.95→1.05→1.35→1.5`，覆盖原veteran1.25／1.3仍有59／62对的时域；不是旧1.2截断。

**实际通过。** 只改 `L_Upperarm.rotation`／`L_Forearm.rotation`，`L_Hand` local轨、原234TRS结构及其余轨payload、78骨／IBM、模型权重、新guard首尾及窗外key保持；R15仍UNBAKED。两真实target各106姿态完整0–1.75秒（总212）Steel／fullbody及8组手前臂—头胸区域均0；原9个残留出口见证最终nearest均为正约8.23–18.85mm、外向无胸面再交。独立保持检查实际全部刀顶点／Head／R_Hand差均0；目标左臂段长最大差1.55e−7m，source6.54e−8m。happy和篡改右腕／guard两坏例均运行。证据分别为 `candidate-final/full_clip_and_motion.json`、`contract_verification.json`、`exit_verification.json`，没有用base替代。

**能看的原材质图。** 同机位source1.1，无透明／覆盖：[indigo修前](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/review-final/indigo_before_right1p1_close.png)／[修后](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/review-final/indigo_after_right1p1_close.png)，[veteran修前](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/review-final/veteran_before_right1p1_close.png)／[修后](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/review-final/veteran_after_right1p1_close.png)。manifest固定相机、actual action／source time与target SHA。原indigo正常前视交线中点多被遮挡，不凭18对夸大可见收益；veteran三分之四诊断角有可见穿胸，图呈现手离胸变化。

**明确未通过。** 本次是净空修复，不是整招流畅度／手部建模验收：原 `L_Hand` local轨在1.03333→1.05秒仍有36.895°最短弧步进，源手指形体、腕袖口缺口仍粗糙。[具体连续性见证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/deep-contact/candidate-final/wrist_continuity_witness.json)含第62／63键原XYZW四元数和dot=.94861289，确非符号等价。相同16.67ms实际指顶点最大位移indigo70.09→75.73mm、veteran76.42→91.61mm；本轮指标增加，包含整臂／腕／指运动，不只腕q贡献。下一阶段如修空手腕连续性，须固定本轮已净空左臂轨与右刀轨，另复核净空；本轮未提前修改。LEFT105对未改；base第三角色、Root整family／当前producer重导、profile／typed／binding正式发布、PICO原生蒙皮画面和Space Pro仍待Root。有限离散0交叉和局部开放胸面出口不等于连续时间／全衣料体积证明。本路未动integration／public producer／formal／app／设备／Gradle／Git；family-v1保持冻结。


## Root 当前审核与执行合同（2026-11-16）

family-v1 已源审接收并完成三target重导，当前自然守势/共享idle时钟正构建原生预览。最终binding为dc0df17b，已修共享旋转采样的exact-key归一化，完整234TRS和361样本五锚首尾闭合；旧91/STEP门已移除，不再等待迁移。旧family-v1和Root integration保持冻结。

现在正式执行 family-clearance-v2，不能只重复封存v1：indigo RIGHT@1.1左手/胸18对，veteran LEFT@1.1右前臂/胸105对，veteran RIGHT@1.1左手/胸53对。Root实际旧6d35519同target同刻比对完全相同，属于既有左右攻击缺陷，不是新守势回归。证据在integration/target-review及target-review-final。

Ownership仅natural-guard/candidate/family-clearance-v2/与01。本轮允许必要约1.0..1.2中段修改：RIGHT局部左腕/前臂外侧净空；LEFT优先肩肘pole调整，保右腕与真实刀轨。不动头/actor/78骨IBM/Grip/权重/碰撞体，不改idle/walk/OH及新guard首尾。用当前formal dc0库真实indigo/veteran准备PNG作为参考并pin SHA，复现实际交叉位置与可见性，不能用base替代。

**attempt1失败已收件，专项子任务接手RIGHT修复。** 在真实indigo target中，source1.10的 `L_hand__chest` 从18对仅降至6对，1.15为15→9、1.20为8→6，未清零。旧RAW与失败证据保持冻结。Root已安排专项实现子任务在 `family-clearance-v2/deep-contact/` 处理真实交叉三角和近景定位；01当前不并行写该目录、不生成新RAW，等待Root将专项结论写回本通路。

## family-clearance-v2失败收件（2026-11-16）

**阶段结束，等待专项结论与Root review。** [失败证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/attempt1_failure.json)记录唯一尝试：只改attack_right的左上臂／前臂／手旋转，在[.98,1.10,1.22]窗口峰值将左腕移动约(+26,0,+8)mm、肘pole约(+18,0,+14)mm；头、actor、Grip、权重、右臂、78骨与IBM未改。

实际indigo before的18对来自当前candidate-library prepared PNG，after为同一target私有重导，保指校正和root流程。 [before](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/review/indigo_before_right_1100_before.png)与[失败after](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-clearance-v2/review/indigo_after_attempt1_right_1100_after.png)仅作上下文，完整视角无法证明局部净空；有限真实表面测量才给出未清零结论。

family-v1、idle、walk、OH、attack_left和正式产线未覆盖。没有修改integration／producer／formal／app／设备／Git；不把“18→6”写成通过，也不凭全局图像宣称可见性已修复。

## 当前执行合同：自然canonical family私有RAW（2026-11-16）

**阶段结束，等待 review。** family-v1已冻结，guard `c9a96738…`／idle `0cac7c29…` 仍为候选身份，未替换正式资源。五条私有RAW已把现walk、LEFT／RIGHT及v5 OVERHEAD的首尾守势迁移到新guard，同时保留每clip中段时标、主攻击轨迹、78骨／IBM、脚支撑和实际持刀Grip。不做新招、公用接口、正式producer／app／构建／设备／Git改动。

采用局部首尾过渡并统一family，而不是仅挂新idle。只替换idle会使idle→攻击跳回旧守势；整段重做又会破坏步法和攻击中段。本轮walk只迁移守势上身、原腿部和脚步曲线保留；不把旧source1／3锁点迁移到呼吸idle。右指保持UNBAKED，私有preview最多一次校正规则检验。

natural idle的181键LINEAR／1.5秒保持，不能削回旧91键STEP。现producer的idle／walk与三攻canonical门仍不接受它，Root接受family候选后统一迁移contract、typed、profile、binding、代理和shared idle clock。当前运行IDLE／guarded HIT仍取idle首样本并手动setTime，候选呼吸不应宣称已在APK播放。完整family RAW、authoring、端点逐分量闭合、有限净空与关键过渡板均已交；本阶段结束，等待Root私有bank与实物review。

## 自然canonical family v1收件（2026-11-16）

**阶段结束，等待 review。** [最终交接](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-v1/family_handoff.json) SHA `8903cacaad715fde2d1ec96421df81dfa3ae53b47bb3d66a2a9168cfc5508f45`，authoring SHA `3c579d6bd9d910c6779603dc5894733405afa6509489f43d6e992be5add3e585`。其中production输入路径已明确以 `ArtSource/tripo-warrior` 为基准，Root可从family_authoring及outputs构造正式私有bank。

| clip | RAW SHA-256 | 采样与约束 |
| --- | --- | --- |
| idle | `0cac7c29e9fd9445e3b1e1825c60e885323b870181df33c5242fc0b6b40d95a6` | 181键、120Hz、LINEAR、loop `[0,1.5]` |
| walk | `5c60c6588442beb4f7d287c7621efce8c9621113bf4ded01980815e56bf2f462` | 185键、原六腿轨／时间、loop `[1/3,1.5]`、7/6 |
| attack_overhead | `9ce928b478360d23db60e16d613658853a7856994dcbfa03e7a505777d359696` | 211键、120Hz |
| attack_left | `ca9c1192def0284f84b2b7c418165c93480b68af0146cb8921b4488b2a0ebecc` | 106键、原中段保持 |
| attack_right | `e53f0d7e9fa4c0f9a5ea93e1f2cccb5e25b0d4527a66d94f97dc41f6434f35b9` | 106键、原中段保持 |

五条RAW均为78骨、234TRS，首尾逐分量精确闭合到新自然guard，R15仍UNBAKED。walk六腿轨和185键时间保持，三攻仅在0至.20、1.50至1.75的局部端点过渡叠加新guard差，中段主攻击轨迹仍是原曲线。idle沿已审1.5秒呼吸候选，未因旧生产门降采样。

[关键过渡板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/review/family-v1/overhead_four_times_formal_vs_family.png)对照source0／.20／1.50／1.75。端点左手随新guard变化约70.7mm，右刀握为微米级差；中段实际锚点差约1.5至3.1微米。板中8个真实采样几何均入框、静态body／材质等8项一致；它不替代全部动态审美与接触验收。

[最终渲染manifest](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/review/family-v1/review_manifest.json) SHA `2a4e555bfdce424b1a7a3310a3995dd65859dffa2e8d2a8ef0899b237d2ef6b9`绑定最终handoff与检查。过渡图完成后，共享 `integration/review_candidate.py` 的live字节在18:42:29发生变化；manifest分列渲染执行pin `cf01c72b…` 与事后live `91b8541d…`，执行原字节快照缺失，不把新live源码冒充为执行身份，也不为这项事后漂移重渲。

[端点检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-v1/verification_endpoints.json)通过234轨、78骨、采样网格、R15、walk六腿原轨与三攻核心原值保全，并实际拒绝7项错误输入。[有限净空检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/family-v1/verification_finite.json)覆盖五clip共272姿态，Steel／fullbody和8组手前臂对头胸声明区域均为0。有限检查不证明连续时间、全部衣料体积、三target或运行组合通过。

idle的source1／3仍保真实呼吸而非旧guard锁点，相关报告只识别9条实际旋转曲线，未将旧归一化统计冒充动作。当前producer的91键／STEP、locked head ancestor和旧marker门必须由Root随family一并替换；不要加旧新fallback。实际运行仍需既有enemyMotionNanos以同一clock驱动idle profile／proxy／SDK，在准备、倒计时、暂停、命中停顿和持续钢接触时共冻，walk继续signed gait。guard_pose仅是canonical参考，不能注册新运行时模式或让SDK独立repeat。

## Root实物评审与下一步（2026-11-16）

已实际看natural_guard_before_after图：左手由垂腕改为自然护手，正常距离有可见收益。接受设计首件继续整合准备，尚未批准正式资源替换；guard c9a96738、idle 0cac7c29保持身份。49离散源姿态报告不能代替三target或端内验证。实际旧入口会将alive idle停在首帧，单有GLB不算呼吸已接入。

下一步统一迁移idle／walk／三攻击canonical端点，保攻击中段、脚支撑与持刀Grip，再由Root原子迁移producer／typed／共享idle时钟并重导三target；不新增招或独立SDK自播。上一轮因账号不支持所选模型退出，现已使用账号可用开发模型续现有文件，不重做已有渲染。

## 自然守势首件历史合同（Root已接受设计，现续派family候选）

**阶段结束，等待 review。** 自然guard与轻呼吸idle v1已在17:15 CST封存，首姿态板17:00、1.5秒片17:12，均早于17:25首件截止。Root已接受v5源审，正式三target重导binding713532c0…，48targetpose无交叉、436组合通过，并取得新APK首人击败到第二轮、实际BLOCK／命中／换手／Retry回执；这些是Root收件，不推作最终动作审美或真机通过。v5 RAW与全部已交身份冻结。

本轮只在既有 `ArtSource/refinement/combat-direction/natural-guard/` 制作同一43a原78骨frame的新自然左护手、双肩放松guard RAW及0..1.5秒轻呼吸idle，不是新招、模式或新family正式发布。首件截止17:25 CST，一姿态前后图与一段1.5秒短片；最多一次有定位修正，不多镜头／参数扫，不构建／设备／Git。保脚支撑不滑、持刀腕与实际刀不脱，右15指仍UNBAKED；preview只为私有目视，不能当RAW。

初选胸肩小幅起伏而非整根上下搬动，保既有脚位与持刀腕世界位姿，左腕按前臂中立关系重建，15指自然轻弯。完整family、producer、app均不提前改；Root接受首件后才统一迁移idle／walk／三攻canonical端点、typed／profile／binding与同源时钟。

实际HAND_POLICY在production_contract.py。motion41只对turn／hit_body／hit_head／hit_side／fall生成其空手curl；attack78／locomotion78仅覆盖目标native右15，左手曲线取authored source。locomotion retarget保留source interpolation，但现validate_source_clip仍要求idle91／walk185的frozen STEP／锁头祖先／canonical marker合同，新呼吸不能直接套现family宣称可正式发布，也不能把motion41的空手生成当本idle的最终规则。

运行入口已查实：ArenaSession.effectiveEnemyPose→ArenaOpponents.selectEnemyPose(IDLE或guarded HIT)→LocomotionProfile.sourceSeconds(moving=false)返回idle首样本；EnemyAnimator对alive clip一直pause并setTime(state.enemyPoseSourceSeconds)。因此只把GLB设repeat(-1)不会播放呼吸；Root后续必须用同一模拟／idle clock同时驱动实际profile与SDK显示，并迁移Locked idle anchor恒定门与相关代理，不能交无人调用动画或独立让SDK自跑。

本轮只交新guard／idle RAW、明确producer规则与后续接线声明、有限源验证和首件图／片。现已收口，Root对应实物review后再续；下方上劈各阶段仅作既有交接。

## 自然guard／idle v1收件（2026-11-15）

**阶段结束，等待 review。** 推荐先看[自然guard前后板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/review/v1/natural_guard_before_after.png)和[1.5秒呼吸片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/review/v1/after/movie/natural_idle_1p5s_30fps.mp4)。左腕由折垂改为中立护胸，掌指自然轻弯，双肩小幅放松；右刀握、头和脚保持。46个真实源样本覆盖0至1.5秒，视频为45帧、精确1.500000秒；当前片仅证明候选的可见变化，正常视距的呼吸自然度仍由Root播放审定。

- [Guard RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/v1/guard_raw.glb) SHA `c9a9673852343f922c7c5cfc026dc63a5c21b89b037f2729c5ea42cdf9a23ee4`。
- [Idle RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/v1/idle_raw.glb) SHA `0cac7c29e9fd9445e3b1e1825c60e885323b870181df33c5242fc0b6b40d95a6`。
- [Authoring与接入清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/natural-guard/candidate/v1/natural_guard_handoff.json) SHA `ef4a5aff2bf11a1acbf6c5dd659b7135212c04f44579120f6851f04db0c2b01a`。

Guard为2键canonical参考姿态，idle为181键、120Hz、1.5秒闭合LINEAR候选，首尾234条TRS float32精确等于新guard。呼吸峰值为Spine约0.699°、胸部约1.886mm，右手／真实钢刀及脚面为微米级漂移。49个有限源姿态的Steel／fullbody与声明自体区域均为0，R15保持UNBAKED，私有preview的一次指校正和一次root shift误差为0。有限采样不证明连续时间、全部衣料或三target组合通过。

现有producer已实际拒绝该idle，因为locomotion78要求冻结的91键idle与非腿STEP恒定轨。它不能通过重采样或伪装为旧锁定idle接入。当前运行链在IDLE／guarded HIT固定取idle首样本，EnemyAnimator手动采时，因此repeat动画自身不会呼吸。Root接受后需一次性迁移自然guard家族、idle／walk／三攻端点、profile／typed／binding、旧locked marker与祖先门，并把同一模拟idle时钟接到profile／proxy与SDK；guard_pose不新增运行时模式。正式family、producer、app、构建、设备和Git均未由本路修改。

## Root下一阶段规划（2026-11-15）

下一首件为自然左护手与微呼吸idle，Root接受guard后才统一更新canonical family与运行idle时钟；v5正式不变。 45分钟单一首件，最多一次定位返修；仅各自制作目录／本交接，Root统一正式资源、构建、设备与Git。

## Root本轮整合review（2026-11-15）

Root已源审v5 RAW85d633ec…并通过唯一producer将三target正式重导，binding713532c0…。全套436单测、typed精确检查通过；Root看过六正常视图，三target48指定pose钢／非邻接核心相交0。实际SDK输入已开局、击败首人并进入第二轮；新三轮胜利仍未验，不扩大源净空结论为连续／所有衣物通过。保v5身份冻结，下一轮据本次原生接触片打磨动作可读性，勿再扫参数。

## v5历史合同：左肘／腰侧净空（Root已源审接收）

**本阶段结束，等待 review。** v5已完成两处局部净空整理，最终真实veteran相交21→0、23→0；不等同整体动作自然度、闭体积或原生验收通过。 用户11月15日恢复总目标，Root已收v4右手／头4→0，冻结RAW `050c55a2b64726f38ca7d36eec52f5832c370b92be3f80551f7c8249e5a3694f`；本轮只继续同一上劈剩余source1.10、1.4666667的L_forearm／chest区域相交，覆盖此前左手不在权限内的限制。

输出仅在既有 `native-weighted-overhead/candidate/v5/`及01交接，不覆盖v4、不改integration／producer／formal／app，不操作设备或Git，保留共享工作树他人修改。首件／修正交付截止14:13 CST，最多两次有定位修正，不加招、不另开美术session或仓库。

先在实际v4 veteran `cead1124ab1c3453f6fae2f98e0be275a39792be3de98e6888edaf83a4aabb86` 复现21／23对三角并出两时点真实局部before。初步解剖定位为近肘袖／护甲根部与Waist腰侧，非左手穿胸：1.10秒交叠bounds约x[.100,.154]／y[.881,.931]／z[.205,.253]m，1.4667秒约x[.143,.170]／y[.944,.996]／z[.026,.085]m。局部最近面法向负距离估计约2.8／9.3mm，不等同封闭体积深度；实际可见性、是否被衣甲遮挡需与原材质before图一起判断，不能只凭21／23总数称严重穿模。

只修必要左肘／腕路径，优先保持左腕目标和world掌姿、由肘外侧净空解决根部交叠；不移动头／actor、不改握点或权重。保78骨、234轨、211键120Hz、首尾guard、R15 UNBAKED及v4三右臂轨和.9已清净空。用真正target私有重导复查两故障及有限邻近／全段，不以base预览代替；Root并行整合手部和phase接口，不作为本路等待理由。

最终RAW／authoring、两时点前后图和有限检查已交；本轮使用两次定位修正，未追加第三版。**阶段结束，等待 review**，Root依据本轮实际target与新产线再决定正式接入。


## v5交付：近肘袖／护甲与腰侧净空整理

**阶段结束，等待 review。** [两时点真实veteran前后板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/review/veteran_two_fault_times_before_after.png)保留原材质和相同相机。修前没有明显开洞或外轮廓破裂，相交主要藏在护肘／腰带相贴内侧；修后仅可见护肘略向前／外退开，不能凭21／23对把它描述为严重可见穿模或巨大视觉收益。

- [完整RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_raw.glb) SHA `85d633ec61534c62f59269c1d9f02854e829d1b84db33a91e3a3afac2e779076`。
- [Authoring声明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_authoring.json) SHA `6056fddca9407c882fba1a12e2d67b4a0ce4983c7d5511bc00ecca9a0fc07380`。
- [Delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_delta.json)与[唯一交接清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_handoff.json)，handoff SHA `3589a3164e68cb0e001243a003793fc1093582858297bb24ea493cd771e36112`。

### 实际修正和检查

从冻结v4出发，只改L_Upperarm／L_Forearm／L_Hand三条rotation，每轨43个stored key，两个局部窗口绕合法肩—腕两骨圆小幅调肘，峰值8°；RAW左腕目标和world掌姿保持，未改头／actor／握点／权重。78骨、234轨、211键120Hz、首尾guard、R15 UNBAKED、三条右臂轨的全部原字节保留，右手.9净空未退步。

真实v4 veteran before私有重导的完整OH轨与冻结cead1124…逐分量差为0，确认本target原生握指／一次指校正／一次idle-root与timeline匹配。最终私有target为 `f2b5f82cd275ab08df5df894193f46db64356d551493af8bed807d0b08d5496a`，不能作为RAW二次重导。原材质、几何、skin／weights及静态装配保持。

[实际target检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_verification.json)最终70个离散姿态的Steel／fullbody与指定非邻接core自体区域均0；两请求时点21→0、23→0，右手／头.9仍0。[原source/base检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_source_finite_verification.json)在冻结v3实际上下文内存应用六条臂旋转（含继承v4右侧及本v5左侧），63姿态均0；未另生成base target。原执行报告封存，six-arm方法文本勘误另列，不冒称重扫。

名义窗口为(1.02,1.10,1.20)、(1.38,44/30,1.56)。修改key分别123–143和166–187，LINEAR实际插值影响范围约[1.01666665,1.20000005]、[1.375,1.56666672]；窗外位同指stored key，C2仅描述标量包络。

### 可见性、深度与动作边界

[局部距离记录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_clearance_metrics.json)将语义L_forearm／chest落实为近肘袖／护甲根部与Waist。修前局部nearest-normal负距离约2.82mm／9.3mm；1.4667修后旧受影响顶点最小转为约+9.4mm，1.10修后三角交叉为0但同类开放面距离仍最小约−2.50mm。该法向距离不是封闭体积inside判据，不能把三角清零写成全体积净空。真实target左手原点因重定向骨长有1.813／2.579mm小位移；Head／右手／真实刀基与刀尖点差均0，不声称target左腕逐分量不动。

第一版逐帧按法向选旋转正负，虽有限表面样本0却产生窗内约14°附加翻向，已拒绝。第二版固定每窗方向，保8°峰值，附加swivel每120Hz步最大约1.539°／1.424°；只用了授权两次修正。[211键完整步进与Q检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v5/weighted_overhead_motion_steps.json)仍列出v4既有1.45→1.4583约25.615°大步，v5约25.927°，不作整招自然或C2声明。RAW L_Forearm的两处旧guard符号边界原样保留，无新增窗内符号翻向；actual target三左臂轨同半球。未为包装旧问题扩大改guard或窗外payload。

最终图14:04:06 CST完成，同一诊断相机eye1.62m／aim腰侧.94m、水平距离1m、VFOV52°；修前原图13:39:08／13保留，修后按最终f2b5…真实重渲，无新movie或扩大机位。RAW生成于13:53:37，最终target／70+63检查与图在14:13窗口内已交；汇总handoff于14:16:42封存，未把封存时间写成窗口内。

### 执行来源与Root接入边界

封存期间两份共享live源码已变化，handoff分别记录执行时pin与当前pin：prepare_character_library.py `3b4d29…→71c303…`（live mtime14:15:53），attack_grounding.py `eb18de…→7f08c0…`（14:14:10）。这些变更晚于本RAW生成，本路未写公共源码，也未把新live代码冒充旧执行身份；本次冻结RAW／target／数值报告与图像身份独立保持。Root应以当前统一产线重导复验，不把本私有结果当新产线／三target已通过。

v4 RAW、authoring和真实target哈希复核未改。没有移动头／actor、改握点、权重、右臂路径，没有改integration／producer／formal／app／设备／Git。70／63有限采样不证明连续时间、全部衣物体积、三target或原生组合通过；Root统一现有phase、接触、手部和最终发布。**阶段结束，等待 review。**

## v4历史返修合同：右手／头净空（现已续派v5左侧）

**本轮局部修复阶段结束，等待 review。** 实际veteran source.9的右手／头相交已由4对降为0；整体target仍有两处v3继承的左前臂／胸相交，不宣称全target净空通过。 Root已用v3真实重导三target，veteran source.90检出新增右手／头4对真实三角相交，旧同target／v9同刻0；base／indigo的16关键时点0，三target的Steel／body共48pose为0。此明确续派覆盖上轮不自行v4的冻结，其余v3全身意图保持。

只写本目录既有制作源、`native-weighted-overhead/candidate/v4/`及01交接；integration全部只读，禁止改唯一producer、正式库、app、设备或Git，保留他人共享修改。输入为[integration实际veteran](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/integration/candidate-library/veteran_prepared_png.glb)，SHA `e44ac2c334169825e95b99213b0c53d6957cb7ff3b5c10df905f7567d3ebc973`，四对三角坐标见[Root报告](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/integration/review/review_report.json)。已在该实际target复现，掌缘／小指根区域875／906与头区域624／625相交，世界bounds x[−.16671,−.15368]、y[1.41280,1.46047]、z[.18583,.21026]m。

仅修source约.82–1.0右手刀路必要外侧净空，优先腕肘自然联动；不缩头、不改握点或权重、不整体抬头／搬actor，左手不动。保持78骨／234轨／211键120Hz、首尾guard及R15 UNBAKED，封存v3。最多两次有定位修正，不扫参数、不扩新招；45分钟截止18:59前交修正RAW／authoring／delta及最少source.9前后图。

必须用实际veteran重导结果检验.9附近，不能以base preview零碰撞替代。允许复用现有retarget_clip／prepare_character在v4目录生成一个target私有校验件，正确应用该target原生握指、一次指校正及一次root；因grounding合同需要idle／walk／三攻共同canonical，私有单target校验透传其真实source timeline，不调用全库build或3target正式生成。若必须调用真正producer，先告Root。Root独占正式三target发布与逐方向phase契约更新，OH边界将为(.65,5/6,31/30,1.75)，cue1.0只元数据；本路不改判定接口，也不等待另一路SDK整体反手验证。

本轮仅一次几何定位修正，采用局部C2外侧16mm腕弧／8mm肘pole联动；真实veteran请求点及附近10个离散姿态已通过，遗留两处失败另列。source1.0端点权重显式归零，保证该原key位同。**阶段结束，等待 review**，不扩大改左手或收招。

## Root三target实物返修：veteran右手／头部净空（2026-11-13）

v3已由唯一producer实际导出三target，48个指定姿态的钢刃／身体交叉均0，base／indigo非邻接核心均0；veteran在source.9右手／头部新增4对三角交叉，旧同target/v9同刻0。真实位置／面坐标见`native-weighted-overhead/integration/review/review_report.json`，不是从base私有preview推断。Root已看new veteran .68与1.15，保整体蓄重卸力收益，当前5d44候选尚未正式批准。

这一新实物问题授权01做**唯一一轮v4局部修正**，覆盖下方禁止自行v4的冻结：仅在.82–1.0附近给右手刀路必要外侧净空与自然肘腕联动，不缩头、抬头、改握点或搬actor；左手暂不改。保全78骨/234轨/211键120Hz、首尾guard和R15unbaked，保v3证据。45分钟、最多两次有定位的修改，交RAW/authoring/delta、故障前后图和真正veteran retarget私有校验；明确一次指校正／一次root，不把base零交叉当veteran通过。Root独占正式producer/库/app/Git，01不得修改integration同伴目录；仅在自身candidate/v4做私有结果。

方向时点已在当前源码收敛：OH source0/.65/5/6/31/30/1.75，运行总1.75秒，ACTIVE线性，cue1.0不控制时钟或伤害；这不是完整锐刃或实际SDK通过。新RAW接受后Root统一更新配置/正式导出与typed，暂不批准v3头部相交为最终成品。


## v4交付：请求点修复，整体target仍含继承相交

**阶段结束，等待 review。** [真实veteran source.9故障前后图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/review/veteran_source_0900_before_after.png)于18:26首交，最终after已按最终target身份实际重渲，未仅替换旧图字幕；18:41完成封存，在18:59截止前交付。

- [RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_raw.glb) SHA `050c55a2b64726f38ca7d36eec52f5832c370b92be3f80551f7c8249e5a3694f`。
- [Authoring](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_authoring.json) SHA `a28f6b2980b220793476ecb5bf59b57c77172e71cff4a2e9504745cbaeaa35c9`。
- [Delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_delta.json)逐key声明改动；[唯一交接清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_handoff.json) SHA `3139ddd4c3d37cb684f40c9d3615199348ec74f31d16a0f3f86180ec917ceeb4`，将请求点、附近窗口与整体target状态分开。

### 修正范围与真实target闭环

先在Root实际e44ac2… veteran复现source.9原4对，再从同v3 RAW用现有retarget_clip／prepare_character私有重导。复现件的完整overhead轨对Root实际target逐float32分量最大差为0，证明使用了实际target原生握指、一次指校正和一次target idle-root grounding，而非base预览替代。私有生成只包含该veteran所需五canonical及真实timeline，未调用全库producer／三target正式生成。

最终RAW仅改 `R_Upperarm／R_Forearm／R_Hand.rotation` 三轨、key99–119共21个局部key；其余TRS payload、78骨／234轨／211键120Hz、首尾guard、R15 UNBAKED及静态rig／mesh／skin保持。头、左手、握点、权重与actor未改，全身蓄重与卸力意图不变。名义腕弧峰值16mm向外，肘pole联动8mm；实际veteran .9手心delta约(−16.404,+1.600,+.491)mm，手世界朝向变化测值0°，Head／L_Hand／右肩原点位移0。非右臂重导分量最大浮点差约2.98e−7，未把它声称逐bit全同。

C2仅描述解析权重包络(.82,1.0)。.82不在120Hz网格，glTF LINEAR实际受影响的插值区间为[.8166666626930237,1.0]，两端原key值保持；“窗外不变”仅指存储key payload比较，不是每个连续t≤.82求值完全不变，也不声称整招LINEAR曲线C2。此为证据精度说明，没有追加几何尝试或参数扫描。

### 两层检查与Root待决项

[原source/base有限检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_source_finite_verification.json)沿冻结v3实际mesh／skin／grip／一次校正／root上下文，内存只替换新RAW三条旋转，原63姿态的Steel／fullbody及指定自体core区域均0；未重导或导出另一base模型。

[实际veteran检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_verification.json)对最终私有target `cead1124ab1c3453f6fae2f98e0be275a39792be3de98e6888edaf83a4aabb86` 实际重跑64姿态。请求source.9右手／头4→0，附近10个离散姿态Steel及指定自体区域均0，全64的Steel／body均0。**整体target检查仍失败**，新增采样范围揭示以下两处同actual v3已有的core区域交叠，v4与v3同刻计数相同，均在本轮delta之外：

| clip/source | 区域 | 实际v3 | v4 |
| --- | --- | --- | --- |
| attack_overhead／1.100000s | L_forearm／chest | 21对 | 21对 |
| attack_overhead／1.4666667s | L_forearm／chest | 23对 | 23对 |

[继承相交报告](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v4/weighted_overhead_inherited_overlaps.json)及handoff含全部44对实际三角／坐标，交Root决定是否及如何续派；本轮没有越权修左手或扩大收招。63／64检查仅证明有限姿态和声明core区域，不证明连续时间、全部衣物体积或三target最终组合通过。base／indigo最终重导仍归Root，未在本路重新生成。

最终故障图为同相机／同actor／同Action source.900000的真实veteran before／after，静态nodes／mesh／skin／weights／grip／材质贴图一致。仅一机位两张图，水平眼高1.62m、局部距离.90m、方位−55°、VFOV70；头、手和刀柄在框，刀尖裁切在局部画面外，不能将近景当完整刀路图。没有新movie或扩大姿态集。旧64执行JSON另原样保存，primary仅补LINEAR窗口解释，未伪称为文字说明重扫；图manifest核对最终primary与执行报告身份。

v3 RAW／authoring与Root integration输入e44ac2…哈希复核未改。本轮只做一次定位几何修正；source1.0零权重边界的数值收口不改原16mm方案。源码快照与交接引用均已核对。Root统一更新逐方向phase、三target正式发布与新proxy／实际接触判定，source1.0仅元数据；本路未改integration／producer／library／app／设备／Git。**本轮局部阶段结束，等待Root review，整体target未宣称通过。**

## v3历史review：RAW阶段接受（现已据目标缺陷续派v4）

Root已实际审看完整53帧板与两侧面姿态，确认全身蓄重、主斩、卸力收守较旧姿态有改进，接受RAW几何阶段供下一轮正式接入；这不等同原生或最终审美过关。

冻结RAW `410d5b445bfd59f615a639a1eb2fb8d5bc8f4cf31e5aa541f9b4cfd84140b1c2` 与authoring `315cd0f0e9a1f0c570d10188a3a0f2bd3b977eda800a616806a2c8d8b8419ce9`。侧面蓄势source.68的左腕下垂仍显刻意，后续仅在Root原生组合画面后精调；01不自行增加v4、不重复报告或渲染，不修改正式producer／library／app／Git。

Root本轮先合真实双刀CCD／约束，正式仍使用v9，避免新动作与旧proxy错配。v3在Root正式切换、同组重导与原生取样前，保持为已接受的RAW制作源，不称已装入当前APK或拼刀交互已完成。**本阶段结束，等待实际接入反馈。**

## 本轮制作合同：原生有分量上劈（已完成，等待实际接入）

**制作阶段结束，RAW阶段已获Root接受，等待实际接入反馈。** 冻结native-weighted-overhead/candidate/v3，首侧面姿态14:26、完整片14:38交付，均在15:03首件截止前。 用户最新否定原生攻击动作质量，Root已明确续派全身重作，覆盖旧v9冻结／仅颈部修正限制。此前三轮通关只证明流程，不代表动作品质或拼刀交互完成；真实刀刀接触判定由Root负责，本路不以缺原生输入阻塞。

唯一写入范围为 `ArtSource/refinement/combat-direction/native-weighted-overhead/` 与本交接。从v9完整234轨、正式78骨制作同一招overhead，原v9 raw SHA `66a56edc4a2bfd4e83c29866a9ce93a854d2d64f1a215e433dc1ac54dc16d750` 保持可回退；原rig SHA `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`，rest／骨长不变。新派生只走一条新制作路径，不添加运行兼容分支。

实际动作要从脚支撑、髋重心传到胸肩肘腕与刀，接触后有卸力和收势，避免机械匀速或只抬脖子。允许修改髋、躯干、肩肘手和真实刀轨；0与结束guard可接，整体约1.75秒、接触cue约1.00秒沿用为制作标记，真正伤害取Root的实际接触时刻。沿v9连续曲线重作力点、支撑与分段速度，不扩另一招或模式。

45分钟首件截止15:03 CST。先交一段完整水平正常眼高短片与侧面2关键姿态，再交有限的实际刀面／头手脚、自穿插与足底检查。最多一个Blender、2线程，经既有01宿主锁串行；不做大规模多镜头渲染或参数／采样扫描。最终交raw与authoring声明，私有preview仅供目视，不当raw交付；不改正式producer、library、app、Root新判定接口、设备或Git。03的veteran甲胄独立部件最终由Root组合动态复核。

本轮源码与有限检查已收口，Root已审看并接受RAW阶段，**阶段结束，等待实际接入反馈**。左腕姿态仅在Root原生组合取样后定向续派。下方v9回执、冻结与三帧复核仅为历史阶段，不作为本轮动作质量通过证明。


## 本阶段交付：native-weighted-overhead v3

**RAW阶段已获Root接受，等待实际接入反馈。** 已交[完整水平眼高短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/review/v3/three_quarter/movie/full_source_1p75s_30fps.mp4)及[侧面蓄势／卸力两姿态](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/review/v3/side/poses/weighted_overhead_two_side_poses.png)。已目视既有53帧板、source1.00接触cue帧与两侧面姿态；不把有限源检查等同Root审美或原生交互通过。

### 交付与实际变化

- [RAW](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v3/weighted_overhead_raw.glb) SHA `410d5b445bfd59f615a639a1eb2fb8d5bc8f4cf31e5aa541f9b4cfd84140b1c2`。
- [Authoring声明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v3/weighted_overhead_authoring.json) SHA `315cd0f0e9a1f0c570d10188a3a0f2bd3b977eda800a616806a2c8d8b8419ce9`。
- [唯一交接清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v3/weighted_overhead_handoff.json) SHA `e20f17870bed638b4ce1d23f8f009a93633bc67070470bd9c185e31f7d2737df`，包含实际执行源码快照、检查身份和RAW接入规则。

由v9完整曲线派生，重作了髋中心位置、髋旋转、胸部独立时钟和双肩肘腕路径。蓄势髋心由约.870m降至.795m、向后至z−.040m，出刀推至z+.105m，接触后再次降至约.782m卸力；此为髋中心／重心代理，不是动力学质心或受力平衡证明。左右鞋面保持原支撑，膝髋配合下沉。持刀手从太阳穴侧提起，刀尖先直立清头再上后蓄刀；左肘下置护胸，胸肩与髋分开推进，落刀后双手从身体外侧回守。移除了“必须先低头让原刀弧通过”的旧制作限制，没有仅抬颈。

Hip→Spine02中心线前倾在source.68／1.00／1.15约2.36／15.96／18.70°，与Head−Hip指标分开记录。动作时间控制明确区分较慢蓄重、加速主斩、减速随势及回守；主斩和随势的既有刀尖样本速度明显不同。是否达到用户期望的力度与拼刀观感，仍请Root以完整片及原生组合审定。

原始78骨、234轨、211键／120Hz、0至1.75秒及首尾guard原始float32值保留。raw右15指为原UNBAKED恒定握姿；私有preview一次目标指校正加一次formal root shift与raw逐轨比对误差为0，绝不把preview当raw交付。

### 有限验证及故障修正

[主检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v3/weighted_overhead_verification.json)与[自体区域检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/combat-direction/native-weighted-overhead/candidate/v3/weighted_overhead_regions_verification.json)均实际执行，各63时点，覆盖完整30Hz及必要关键点。真实Steel／全body相交样本0，非邻接左右前臂及手／头胸core区域相交样本0；原rest／mesh／skin、端点、R15与一次校正通过。鞋底高度最大离散误差约.01984mm，鞋心移动最大.09282mm，骨长数值差约.000376mm。5项非法时间、实际输入SHA改变与导出guard被篡改共7项拒绝实际通过。

v1在source.20提刀碰头，改为太阳穴侧直立抬刀后修复；v2在1.27–1.40回收新增左前臂／胸、右手／头交叠，已通过右手外侧／前方回收及左肘pole前移修复，v3包含这些旧失败时点及1.42／1.55关键点。失败证据保留，不把仅刀／身体零交叠冒充自体零交叠。

自体检查使用三顶点均主导于指定解剖区域的core三角形，排除邻接、混合接缝和同区域衣物叠层，不能证明全部衣料体积、任意连续时间或03新veteran甲胄无穿插。少量独立FK刃侧参考点诊断支持source.833–1.033主斩刃领先；1.10秒减速随势已翻刃（约1.37m/s，方向诊断详见handoff），不把整段都声称锐刃领先。该诊断点是选定刃侧近似点，非真实接触三角面；真实几何碰撞检查与它分开。

### 可见证据与Root接入

完整片480×584、53个真实源采样、名义30Hz、末半帧VFR，ffprobe时长1.750000秒，SHA `67862539689c76ceb6edc960126ddc677dee8270fe2a1224a51bda5eb52b8702`。相机固定水平eye＝aim1.62m、距离2.75m、VFOV70°，actor未移动；侧面只出.68蓄势和1.15卸力两pose。所有实际几何均在框内，预览mesh／material／texture／image与正式PNG等价视图核对一致。渲染器旧v1默认已移除，四个路径参数必填；缺参拒绝、语法与help通过，实际执行源码另存snapshot且manifest引用一致，未为此重渲。

Root取完整RAW与authoring，按每target既有grip／一次校正／grounding重导并重生实际刀路与接触数据。source1.00仅作制作cue，**不能作为定时伤害或复用旧v9整段ACTIVE杀伤窗口**；实际击中／拼刀时刻和刀面意义由Root新接触系统决定。当前没有改变正式producer、library、app、Kotlin、判定接口、设备或Git，也没有增加运行兼容路径。03甲胄的最终组合及原生动态验收归Root。

本路本阶段仅交上述RAW、authoring与必要目视／有限检查，Root已收件并接受RAW阶段，Blender已释放，**阶段结束，等待实际接入反馈**。

## 历史收件：v9有限复核收口（已被本轮全身重作任务续派）

Root已收3张真实原生帧及有界复核：未确证颈部跳断、肩肘脱节或刀具脱手；部分手部遮挡和source时间对齐限制保留，不推成整段动态品质通过。v9已由唯一producer正式重导，bfaf53b／1c41包实际三轮通关并可重试。接受本轮动作收口，冻结v9，不开v10、不重复离线渲染或扩大招式。Root下一优先为服装、刀面与刀轨；无明确新动作缺陷时01不空转，也不把流程证据当所有攻防动作验收完成。

## 最新用户目标与执行队列

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你继续负责动作源与正常视距可见的站姿、引刀、随势、防御支撑、弹反卸力、受击与行走转身。09接正式bank／正常循环／动画与代理，05接头脸，Root统一producer和发布。

Root已接受fine-overhead v9进入开发整合，上劈保留211键／120Hz，左右攻击保留原106键；v7／v8和历史stage5源继续冻结。Root已回执v9原生三轮通关，本次限3张实际原生帧完成一次动作目视复核，等待Root review／续派后再调整。把动作力度和人体重心作为重点，避免只用细微角度与误差小数作为完成证明。每项交原生曲线、真实刀尖轨迹、源时间、足底与双手可见图／短片。与09交换来刀侧和接触标记，与03交换服装动作穿插。公共prepare_character_library和prepare_rigged_warrior由Root内部生产线维护，你不再编辑它们。

## v9历史状态

**v9原生三轮已获Root回执，单次动作抽帧复核已结束。** 正式binding `365578…`、三角色及typed／profiles／pins齐套；Root回执源码 `bfaf53b`／APK `1c41cfc3…` 实际三轮895分／60HP、349测试通过。[发布录像](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/presentation/native-visual-v9-three-rounds-2026-11-13.mp4)已存在，不再将缺APK或原生输入作为阻塞。该回执属于PICO Emulator，Space Pro真机未由本路验收。

**阶段结束，等待Root review／续派。** 本次仅从既有trial2原生录像抽取并目视3张原尺寸帧，结论见当前合同。未确证需要返修的问题，保持v9的211键／120Hz；不开v10、不降采样、不重渲，不改动作源、正式库／producer／Kotlin／设备／Git。

## v9历史制作合同（已由上方全身任务续派）

唯一新增责任为 `ArtSource/refinement/hand-poses/fine-overhead/` 私有候选与本交接。唯一产品交付为Kotlin + PICO Spatial SDK6.1.9的原生APK，终端Space Pro／OS6，由Root统一构建、PICO Emulator验收与发布。本路只交可由现有producer接入APK的动作GLB与明确重导输入；离线两机位短片仅作Root已要求的动作源审阅证据。停止HTML／Web／Three.js、网页材质与新mock页面工作，已有网页不改不删。v9制作阶段基于已审v7，限定颈胸低俯与必要的准备肘修正，保留已改善的髋肩随势；该制作合同已结束，本次只做一次实际v9目视复核，最多3张原生帧、最多3条结论，未确证问题不改源。骨长、rest、敌人规则、伤害、原刀路与整体1.75秒时标保持既定合同。实际v9仅调整两颈rotation，未动胸肩或准备肘。

本轮冻结正式对照GLB SHA-256为 `ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20`，profile为 `04b225ac95aafc13b5d38dec5bbb55cf278b235514b4e7ca864fdebb20af3e90`。正式守势用于03衣片对照。原生动作源为refined-base60k/slash.glb的连续骨曲线，SHA `98e785d73a5d6cb767cebd5b79ec2bb9af9a2b717ae2d2576f3a0b7e07ea370a`。派生制作记录实际采样与约束修正来源，采用单调时间映射及连续肘平面，入口／出口回当前canonical guard。

本轮先交眼高1.62m、水平视线的三分之四与侧面1.75秒全片及实际采样帧板，保留固定相机身份和真实刀尖轨迹，不移动演员补画面。若源姿态仍低俯，只修颈胸与必要的准备段肘外展。髋肩随势、刀路、骨长、rest、足底、整体1.75秒及source1.00接触保持；不重做刀路，不扩另一招。45分钟内首项可见实物或明确失败。

全路最多一个Blender、2线程并通过既有宿主锁。当前producer、正式GLB、Kotlin、Git、设备、构建均由其既定负责人维护。阶段结束后在此写明“阶段结束，等待review”，随后等待对应回复，再继续下一轮。

Root已交原生真实输入实录 [native-input-contact-2026-11-12.mp4](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/presentation/native-input-contact-2026-11-12.mp4)及同名PNG／JSON，记录SDK鼠标进入同一resolver、SOFT_HIT／敌人护刀和敌血100降12。此为已接入基础，本轮源审阅以该正式身体／刀为对照。


### 本次原生动作目视复核（2026-11-13）

1. **快抬眼未见确证返修点。** 实际[帧1](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/native-v9-2026-11-13/native_01.png)／[帧2](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/native-v9-2026-11-13/native_02.png)／[帧3](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/native-v9-2026-11-13/native_03.png)来自[trial2-window.mov](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/native-visual-v9-grip-v2-2026-11-13/trial2-window.mov)的PTS29.150000／29.291667／29.433333秒，HUD依次为蓄势／蓄势／起势。trial2为Root说明的同v9动作源、仅后续终局日志诊断代码不同版本，不冒充发布APK逐字节相同的录像。正常游戏视距下，头从前俯经可见中间姿态转向前方，未见颈部跳断或位置突移；三帧不充当150ms连续节奏全面通过证明。定位依据是[trial2.log](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/native-visual-v9-grip-v2-2026-11-13/trial2.log:462)中OVERHEAD attackId1的08:30:22.643 STARTUP／source.6511296。按录像文件birthtime00:29:53.279056Z估算source约.44／.58／.72，文件birth不是已校准首帧时钟，故不把估值冒充精确source.50／.575／.65。
2. **肩肘、手刀未见明确脱节。** 同三帧中持刀肩肘随引刀换位，右手／刀柄仍相连，头颈与衣领未见明显裂开或悬浮；左护手保持在胸前侧。持刀手部分被头肩遮住，不据此宣称所有握持面无穿插。前景横贯胸前的是玩家刀，未作为敌人刀路或脱手证据。
3. **保持v9，等待Root决定下一项。** [同场日志](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/native-visual-v9-grip-v2-2026-11-13/trial2.log)记录该OVERHEAD完整PREPARING→STARTUP→ACTIVE→RECOVERING→IDLE及PLAYER_HIT，另有完整LEFT／RIGHT，未为侧击增加抽帧。本次未确证动作源需返修，不创建v10或改正式资源；以Root已完成的原生三轮与本次有限目视为现有证据，后续仅按Root新派发的具体问题调整。**阶段结束，等待 review。**


## fine-overhead v9本阶段交付（2026-11-13）

**源码制作阶段已结束，Root源审与原生三轮回执已收件，本次单次目视复核见当前合同。** 先交水平眼高v7完整诊断片，确认低俯来自源颈部折叠与旧相机俯视叠加，再修两颈曲线。v7与原证据未覆盖，v8失败留证，未扩另一招或改刀路。

### 审阅入口

| 机位 | v7／v9完整配对片 | 五关键姿态 | 全53帧对照 |
| --- | --- | --- | --- |
| 三分之四 | [连续片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v9/three_quarter/paired/movie/full_source_1p75s_30fps.mp4) | [姿态板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v9/three_quarter/paired/poses/five_source_poses.png) | [全帧板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v9/three_quarter/paired/movie/all_53_source_frames_mosaic.png) |
| 侧面 | [连续片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v9/side/paired/movie/full_source_1p75s_30fps.mp4) | [姿态板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v9/side/paired/poses/five_source_poses.png) | [全帧板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/review/eye-height-v9/side/paired/movie/all_53_source_frames_mosaic.png) |

两机位固定eye＝aim1.62m、水平距离2.75m、VFOV70°，actor不移动。每机位另有v9独立片，四片均实际53源帧、名义30Hz、末半帧VFR，ffprobe均为1.750000秒。配对片960×584，独立片480×584；v7参考直接复用，未重渲。五pose为source0／.65／1／1.1／1.75，已看全部v9源采样板与关键姿态。侧面与三分之四的接触／随势脸朝前，当前640图未见明显颈裂口、悬浮或肤色断带，首尾回guard。

### 源与实际改动

唯一接入清单为[fine_overhead_inputs.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/candidate/v9/fine_overhead_inputs.json)，SHA-256 `96f994be8a0ef9e4770b0f1256137a061379dca8824d47830af5d893f78d09af`。

| candidate/v9文件 | SHA-256 |
| --- | --- |
| fine_overhead_raw.glb | `66a56edc4a2bfd4e83c29866a9ce93a854d2d64f1a215e433dc1ac54dc16d750` |
| fine_overhead_preview.glb | `84786acc2956da2fb6d7382a70bfaba906f3b93b1ea925eaf857d88c68a2d253` |

新builder直接从冻结v7 patch `NeckTwist01／02.rotation`，增量45／55%分摊，充分混入时保留原俯仰偏离20%。Head局部TRS与native微动保留。source .65／1／1.1相对guard的Head前向由向下41.38／37.37／30.50°收敛至8.28／7.47／6.10°。该指标以guard为零，与旧rest固定解剖轴的26–37°不同；胸世界姿态和Hip→Spine02中心线保持v7，不将Head−Hip指标变化称为胸部修正。

整体1.75秒、211个120Hz采样、234轨及原phase／contact1.00秒保持。raw右15指仍UNBAKED，preview原8项指校正与一次formal root shift原字节保留，未烘焙runtime entity抬升。

### 验证与失败处理

[主验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/candidate/v9/fine_overhead_neck_verification.json) SHA `046eeff2585da6a1fcadfbd7ecb7a68e7228c4b6df8a90a2e307fe5b12a1f9d2`已实际执行。三份raw／body／preview的JSON、rest、mesh、skin、首尾canonical float32和非颈轨字节保持；每份211key加210midpoint共421时点，整个Neck01子树以外的全部世界矩阵逐bit与v7一致，含髋、胸肩、双手、刀与脚。最大骨长数值差约1.54e−8m。

新实际body／Steel扫描覆盖全招60Hz106时点，加.45–.72秒局部240Hz格点与精确边界，去重共155时点，0个相交样本。所有采样的实际钢刀顶点逐bit与v7一致；鞋面位置变化0，当前鞋底最小高度相对formal源平面误差约.00166mm。[边界与执行依赖补充](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/hand-poses/fine-overhead/candidate/v9/fine_overhead_neck_boundary_verification.json)记录15项非法时间／gain／层级拒绝、v7未改及实际scan helper导入闭包，未为补充文字重复BVH。

v8从起手即抬眼，在source.4667／.4833／.5000的原准备刀弧出现3个Head／Steel交叉时点，已明确标failed并保留执行源／SHA。v9仍直接从v7派生，将进入混合延后为.50–.65秒，未叠v8修正，重新完成上述155点检查。

### Root接收与原生验证回执（2026-11-13）

Root回执明确接受v9进入开发整合，三视图低头改善有效，未见新的刀路／足底／握持倒退。唯一producer已采用authoring逐clip精确timegrid合同，OVERHEAD保留211键／120Hz，LEFT／RIGHT各106键；grounding透传同一条已验证timeline，相关17项测试通过。正式publish已exit0并匹配三角色候选binding `365578…`，typed与identity pins由Root重生。Root现已回执源码bfaf53b／APK1c41cfc3…真实三轮895分／60HP、349测试通过；本路未重新构建或操作设备。

接入入口仍为清单production_entry指定的 `motion_library.json`／`attack_source.clips[name=attack_overhead]` 与完整v9 raw。v9包含v7已重作的身体／右臂／手和刀轨，不是向旧bank叠两条颈补丁。三向authoring_manifest、三target profiles、hand signatures、binding及每target原grip、一次校正与grounding由Root唯一生产线维护；本路未修改这些正式文件。以上发布／17测试为Root回执，不记作本路另行构建或设备验收。

source.50前保留v7原头姿以让准备刀弧通过，全招最深俯视仍约37.94°，不能声称整段只剩9.65°。150ms混入是较快抬眼，Head最大离散步进3.193°／120Hz、速度约383.2°／s；已看真实.500／.533／.567／.600／.633／.667连续样本呈逐步抬起，最终节奏、原准备肘外展及身体俯身仍由Root审。C2仅描述混合包络，未证明LINEAR节点瞬时导数或连续时间无穿插。640全景也不覆盖瞳孔和1–2px normal seam。Root已完成正式生产线发布与PICO Emulator三轮实战；本次已用3张原生帧完成有限动作目视，未见确证返修点。未扩展三角色全表面或Space Pro验收，精确连续节奏不由三帧证明。

本轮源码与离线源验证已收口，原生回执及本次单次目视结论已更新，**阶段结束，等待Root review／续派**。当前waiting，不新开v10、不降采样、不重渲，不修改正式producer／资源／设备／Git。

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

## LEFT肘部专项（2026-11-17 · 首件封口，未合入）

本节只属 `family-clearance-v2/left-elbow/`，不修改 RIGHT／deep-contact 或01顶部合同。Root明确允许必要的 `R_Hand` 局部Q反补偿，以保源腕世界朝向；不是锁死局部腕Q。只改 LEFT 的 `R_Upperarm/R_Forearm/R_Hand.rotation`，其它源JSON、TRS、手指、root/head/脚、78骨/IBM/权重几何与其它四RAW保持。

实际 veteran `attack_left@1.1` 的105对均严格跨越两三角面平面：40个参与臂顶点全dominant `R_Forearm`，130个胸顶点全 `Waist`，范围x[-.109,.0014]/y[.964,1.090]/z[.182,.255]m，约在肘→腕前3%–49%。原材质局部图可辨近肘袖／腰前接触，不以helper或整肩排除清零。

本轮只做一首件和一次定位修正，均**不合入**。−8°负swivel（.98/1.10/1.22）峰值105→0，但同target5533个全钢刃顶点最大偏移base1.162／indigo3.101／veteran4.915mm，且1.15／1.20／1.22仍10／48／17对。唯一修正减至−1.5°并把尾窗延到1.28，刀轨最大偏移0.213／0.582／0.923mm，均满足Root为本攻击明确制定的1mm保护（约刀长0.14%，非碰撞精度；未使用idle2mm预算），但veteran峰仍78对，四处窗口未清。

RAW首件 `3f51c41d…`；修正 `f95ad3a9…`。源关键钢刃误差分别0.867／0.706µm，子键钢刃差分别1.162／0.213mm，说明逐键IK不保证60Hz分段SLERP的任意时刻末端恒等。源/三target head/root/脚、首末全节点world及骨长证据见独立收件，不作连续净空或完整视觉通过声明。

已交原材质正常／局部 before/after四图；正常视距收益几乎不可辨，局部仍见袖／腰接触。`left-elbow/handoff.json` 状态为 `stage_ended_failed_do_not_integrate`；禁止以105→78当修复成功。阶段超出30分钟窗口，包含5分钟实际排锁及本路runpy路径封存错误；已停止源角度尝试。

随后按Root新授权仅进入 `left-elbow/target-wrist-constraint/`：使用各自冻结原LEFT世界腕TR与刀轨，按该target真实骨长作两骨IK／腕Q反补偿，可对三旋转局部加密120Hz；保时长/时序与其它9clip/root/head/脚/fingers/骨架/几何。它是唯一canonical producer目标末端约束的私有原型，Root接受后再收进正式产线，不能永久并存两条生产线或扩1mm保护。


目标末端约束首件现已封口，状态 `private_finite_target_constraint_first_piece_complete_pending_Root`。每个target使用冻结原LEFT自身FK，不跨体型借臂长。仅veteran使用−12°肘pole及必要腕Q反补偿；base／indigo字节不变。三旋转仅在.9–1.3s局部120Hz加密，union106→130键，其它231轨与9clip、静态骨架/IBM/权重几何、root/head/脚/fingers、首末world保持。三target的.9–1.3s 120Hz有限窗口中，八类非相邻身体分区与全钢刃/身体检查均0对；另有六个实际腕向/骨长坏例被抓住。四张原材质前后正常／局部图已实际查看，不等同原生设备通过。

同target全5533钢刃顶点：veteran关键点最大0.669µm，子键最大0.624mm，低于本攻击5µm/1mm保护；world骨长数值差最大0.126µm。首件冻结原LEFT语义`032a552e…`，修后`3d17f011…`。Root随后整合RIGHT导致整文件SHA变化不影响此LEFT参考；新算法运行时从当次未改的同target prepared资产在内存取目标，不读取旧formal。

生产接入候选已交 `left-elbow/target-wrist-constraint/canonical-integration/handoff.json`。私有`target_wrist_constraint.py`＋固定`constraint_recipe.json`和四文件最小`canonical-integration.patch`，接在唯一producer的prepared归一化/指校正/grounding之后、KTX/profile输出之前；body与PNG同处理，最终输出语义/bytes/SHA同步。源代码和recipe均进新binding，不兼容缺失旧manifest，不复用旧批准。

真实module检查重现首件LEFT语义；3个非法recipe及3个缺失/错身份被拒。补丁loader/binding在内存实跑，真实profile生成130 samples包含全部130 prepared时点，source phase／runtime nanos／1.75s时长保持。完整RIGHT＋LEFT候选统一导出、全套typed/构建与模拟器验收仍由Root执行；本路未写公共producer、正式库、manifest或app。详细可复建命令、边界与所有身份见该目录README及handoff，不以私有prepared拷贝代替产线。
