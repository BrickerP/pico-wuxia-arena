# Benchmark 与 QA

## 当前交接

| 项目 | 当前状态 |
| --- | --- |
| 状态 | 预演与呈现回归review通过，f70e6aa统一构建与81项测试通过 |
| 当前主分支 | `f70e6aa` |
| 已合入成果 | 真实 W 技术链、Full Stage 角色画面、77 项现有测试通过 |
| 当前任务 | 等待主控新的玩家刀与角色运行画面，核对构建身份和实际可见结果 |
| 主控审核 | 当前软件链路通过到出招资格层，完整攻防与真机仍待验 |

## 共同执行约束

用户已预先批准本项目后续操作。主控按职责分工自主review与执行，并报告阶段成果和实际费用。共享设备、提交及Tripo任务由主控统一调度，Agent继续遵守文件职责范围。

- 唯一工作目录为 `/Users/yupeng/projects/personal/pico-wuxia-arena`。直接在该仓库按职责协作，主控审核与提交。已有副本先保全未提交差异，再由主控迁回并清理。每次提交只包含自己负责的文件。
- 技术栈为 Kotlin + PICO Spatial SDK 6.1.9，使用 pico-cli、Gradle 8.13、JDK 21。目标设备为 PICO Space Pro / OS 6。桌面预演通过 PICO 模拟器运行。
- `/Users/yupeng/projects/personal/pico` 是只读技术参考。`BrickerP.github.io` 不属于本任务。
- `7645c5d` 已实测用户真实 W → 模拟器 HMD 观察 → 虚拟双手 → 共用 `canStartAttack` 出招资格查询，日志包含同一头手序号及 false→true 的结果。完整攻防、独立手位控制与真机表现继续待验。
- 下一轮只推进独立手部输入、可见玩家刀和一个实际刀刃接触。必要回归限定已打通的链路，保持单敌人和单刀范围。真实 VR 战斗由头部及手部动作驱动。
- 敌人由已配置账号的 Tripo 生成写实中式刀客，导出 GLB，优先绑定与动作能力。Blender 只处理米制、轴向、原点、握点和现有 dao 对齐。
- 模型必须进入 Full Stage，交付用户可直接查看的运行时画面。空间截图失败时，由主控改用模拟器窗口截图、录屏或其他可观察的实际渲染捕获。
- 四份固定文档用于当前任务、评审和交付。Agent 更新本文件进度，主控填写审核和下一步。构建、安装、共享设备输入与捕获由主控统一协调。Agent 完成源码与静态检查后交主控运行统一验证。



## 本轮主控 review

- 主控已对新增两项回归的当前工作区运行 `:app:testDebugUnitTest :app:assembleDebug --offline`，构建成功。XML 结果共79项，失败0、错误0、跳过0，新增的两个完整方法名均已实际执行并通过。该验证对应工作区源码，当前尚未提交。
- `7645c5d` 的 `:app:testDebugUnitTest :app:assembleDebug --offline` 成功，77 项现有测试通过。已安装 APK 与构建 SHA-256 均为 `41d3fc524ab88ef37d18bf0453a2fb928c3d5b13e8d9beacacc74e385261790b`。
- 18:10 用户真实 W 产生约 1.4 m 头部前移，虚拟双手同步移动。`headSequence=26852`、`handSequence=26853` 与同序号共用战斗查询对应，目标距离约0.997m、`targetInRange=true`、`canStartAttack=true`。原始 DOWN/UP 由模拟器宿主消费，人工操作确认与位姿日志关联。
- [验证日志](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/7645c5d-key-chain-verified.log)和[验证范围与身份](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/7645c5d-key-chain-verified.json)完整保留。虚拟双手是 HMD 派生预演数据，独立手控和实际命中未完成。
- [Full Stage 实际画面](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/f5ab507-full-stage-mission-control.png)来自 `f5ab507` 在 macOS 系统窗口概览中的模拟器窗口裁剪。[捕获身份](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/f5ab507-full-stage-capture.json)与后续键盘构建分别记录。人物、dao、酒馆可见，角色为静态 T-pose。

## 已完成的输入回归范围

只修改既有 `app/src/test/java/com/example/wuxiaarena/p0d2f0182/input/PicoTrackingAdapterTest.kt` 与本文件，复用其 Fake Provider 增加两项必要回归。

1. 正常路径验证预演 HMD 观察产生 DESKTOP 头手配对，真实控制器数据在该模式被隔离，质量保持 UNKNOWN。确认经实际 `TrackingEventBuffer → TrackingState` 消费后只在所需头手到齐时观察就绪。
2. 失效路径验证 HMD 不可用清空所需观察，失效期间旧样本不能恢复就绪；恢复可用后仍需新观察。覆盖配对源的连续性，不声称传感器有效性或真实设备通过。

不加依赖，不扩碰撞夹具和大型用例清单，不修改产品源码。构建由主控统一协调，写完先执行静态差异检查，并在下方标明可审核的测试改动和预期。

输入线当前只改 Activity 的数字1白名单，主控正在 `Main`、`HomeStage`、`ArenaSession` 接入玩家刀呈现。各方共享唯一仓库，保留他人修改。

## 捕获与后续 benchmark

空间截图接口在当前模拟器缺少 `--spatial` 支持，普通 console display0 曾得到黑图。原生窗口单独截图也失败。已验证的替代路径是宿主屏幕截图，在系统窗口概览中取得实际渲染帧并裁出模拟器窗口，保留构建身份与捕获时间。

手感后续从玩家刀的可见响应、真实接触与反馈、方向和动画衔接验证。真机输入、舒适度、画质与性能需要 PICO Space Pro / OS 6 实测。当前静态显示与合成回归不能支持这些结论。

## Agent 当前回应

已在现有 [PicoTrackingAdapterTest.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/test/java/com/example/wuxiaarena/p0d2f0182/input/PicoTrackingAdapterTest.kt:123) 复用 Fake Provider 新增两项回归，测试方法数由 20 项增至 22 项。

- `emulatorPreviewPairsDesktopHeadAndHandsAndIgnoresRealControllers` 验证 HMD 回调产出顺序相邻、同坐标 epoch 的 DESKTOP 头手事件，头部与双手质量均为 UNKNOWN。事件经真实缓冲队列取出后，消费 Head 仍未观察就绪，消费 Controllers 后才就绪。配对前后的控制器回调均未进入队列。
- `emulatorPreviewLossClearsThePairAndRecoveryRequiresNewObservations` 验证 HMD 不可用时仅发出一次 DESKTOP／ALL 中断，清空头部与双手观察并推进各自 continuity。失效期间重复 SDK 样本不能重新入队，恢复可用性也不生成观察。显式在消费者边界重放旧事件仍被拒绝，后续新回调的配对按 Head、Controllers 顺序恢复观察就绪，保持新的连续性基线。

静态差异检查 `git diff --check -- app/src/test/java/com/example/wuxiaarena/p0d2f0182/input/PicoTrackingAdapterTest.kt docs/agents/04-benchmark-qa.md` 通过。已核对字段类型、事件顺序与失效边界，并完成独立只读复核。新增内容为两个测试方法和一个既有 JUnit 断言导入，沿用现有命名及夹具，依赖与配置差异为空。

主控已完成统一构建，并读取 XML 确认两个新增方法实际执行，完整结果为79项通过、0失败／错误／跳过。产物为上述测试源码与本交接说明，覆盖范围为预演输入的软件观察链路。

**本轮必要回归 review 通过。** 下一轮先等主控交付对应构建的玩家刀、CLI 新角色实际运行画面与输入结果，再按同一构建身份核对可见性、握姿、绑定与实际键盘入口。主控正在修复 review 发现的呈现回调迟注册竞态，该修复将独立重新验证。当前79项结果仅覆盖本段列明的已运行工作区。

## 新方向与当前主控补充 review

用户要求优先既有能力的UI、模型与动作呈现，底层算法先暂停深入完善。主控以场景／角色／玩家刀可见、既有试炼阶段可展示、开始／暂停恢复／重开可用作为基础展示门槛，达到后创建BrickerP账号下的独立私有GitHub仓库，再继续表层迭代。

`f70e6aa`已修复呈现回调迟注册竞态，两项针对回归均实际通过，完整81项测试0失败／错误／跳过，APK构建成功并安装，进程13610。当前APK SHA-256为 `f2e63201e9a2e0ee46a7745d0df02b9a72c41d0860e8959d584a5316cff7a88b`。79项为上一轮已运行结果，81项是当前已合入版本结果。

当前QA工作聚焦主控交付的同构建实际画面、控件操作、真实状态与动作反馈。先阅读01／02的新接口稿，列出最小验收点，避免扩大碰撞、几何证明或底层基准。主控在HUD接线后统一验证必要正常路径和失效边界。GitHub交付仅纳入项目所需源码与运行资产，宿主全屏截图含其他会话内容，留作本地诊断并排除出发布资料。

## 主控接口 review 后的QA任务

01／02的最小控制与呈现接口已获主控批准，战斗线修改ArenaSession.kt，输入线修改TrackingSession.kt。QA先跟进其实际源码出口，复用现有ArenaSessionTest的真实TrackingState入口，补最小的正常试炼开始／阶段呈现与暂停恢复或重开边界回归，保持两项针对方法范围，待接口落地后写。主控统一运行构建与必要测试。

已有f70e6aa实际玩家刀图 `artifacts/runtime/f70e6aa-player-dao.png`，截图由模拟器native window捕获，旧Tripo／酒馆与玩家刀可见。新低模、4动作和HUD画面需分别核对后续构建身份。宿主数字1自动化尚无应用事件证据，UI说明继续按已验证W相机／合成手位预演范围表述。

## 本轮 UI 与呈现验收稿

已读取01／02正文，并从应用入口只读核对 `f70e6aa` 的原有调用链。主控现已批准 `ArenaViewState`／`ArenaPresenter`、生命周期 `TrackingControls` 与排空后恢复委托，采用READY停钟、重开回READY。首轮方向按最新动作review调整为OVERHEAD下劈。以下验收点按这些已批准语义对齐，实际UI结果待主控接线后验证。

当前真实入口为 `SpatialApplication → mainApp → ObserveTracking + HomeStage`，已加载场景、静态角色和主手驱动的玩家刀。当前开始／暂停恢复／重开与HUD入口仍待接线。`tryStartAttack`、`pauseByPlayer`、`tryResume`、`receivePlayerHit`、`resolveActiveAttack` 当前没有生产调用方，`ROUND_RESET` 只有消费分支。Android生命周期启停与玩家控制需要分别验收。所需观察失效后，当前刀可随新观察重新显示，但战斗缺少 `tryResume` 调用，仍可能保留追踪中断暂停。上述入口缺口交既定负责人接线。依据为 [Main.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/Main.kt:13)、[HomeStage.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt:36)、[ArenaSession.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSession.kt:54) 与 [TrackingSession.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/TrackingSession.kt:358)。

以下五项在主控HUD与动作接线后，使用同一构建实测。试炼阶段沿用现有 `EnemyPhase` 与开始标志，状态文字由实际快照驱动。

| 验收入口 | 最小通过条件 | 所需实际证据 |
| --- | --- | --- |
| 进入与可见呈现 | 场景、当前运行角色和玩家刀可见。模型尺寸、朝向、刀柄握点与手位关系可观察。输入说明如实显示桌面预演、HMD派生双手和质量未知；实际设备来源按运行模式显示。 | 同构建的场景与HUD截图，以及短段位姿变化画面，能辨认角色版本、玩家刀和显示文案。 |
| 开始与阶段反馈 | 从实际开始控件进入试炼，开始标志与当前 `EnemyPhase` 可见。输入就绪和范围资格来自现有查询。满足条件时，既有出招调用产生阶段变化，HUD与已接入动作／提示对应同一事件。尚未接入的动作单独列为待验。 | 一次真实控件操作到状态与事件输出的日志关联，加对应阶段画面。仅有资格查询日志时，出招与阶段变化继续待验。 |
| 玩家暂停与恢复 | 暂停后显示实际暂停状态，出招推进停止。恢复使用当前真实 `pauseId`，在新观察就绪后恢复，HUD与动作反馈同步。观察未到齐时保持等待提示，重复操作不会制造第二套推进。 | 暂停前、暂停中、恢复后的状态与画面，关联同一次暂停标识及新观察。 |
| 重开 | 实际重开控件经已有 `ROUND_RESET` 路径清除当前轮状态和旧动作，HUD回到定义的初始状态。旧观察不能让玩家刀或战斗沿用上一轮进度，新观察到齐后再恢复对应呈现。 | 一次重开操作、重置事件和新观察的日志顺序，加重开后的实际界面。 |
| 追踪失效与生命周期 | 所需头手观察失效时，刀隐藏、战斗中断且HUD提示等待。仅恢复Provider可用性时继续等待，新观察到齐并经过既定恢复调用后，刀、战斗状态与HUD一致。离开再进入场景后，控件绑定当前session，呈现回调能同步最新快照。 | 主控协调一次可控失效／恢复及一次场景退出／返回，核对失效画面、恢复画面和当前session的事件关联。 |

每组证据记录提交或工作区身份、APK SHA-256、运行目标、时间、运行资产路径和对应状态／事件日志。新HUD或新角色构建分别核验其运行身份。展示资料使用只含目标应用内容的截图或录屏，宿主全屏诊断图按主控约定留在本地。

本轮产物为上述五项验收点与真实入口缺口说明。已完成正确性、可维护性、界面文案／状态表达及变更范围的只读复核，`git diff --check -- docs/agents/04-benchmark-qa.md` 通过。当前已运行基线沿用主控回填的 `f70e6aa`、81项测试与APK构建结果。上述UI操作、当前角色动作和新构建画面均待主控实测回填。

**本轮验收稿阶段结束，主控已批准进入最小接线回归。** 主控HUD接线后的同构建画面、控件操作及日志仍按这五项核对实际结果。

## 本轮最小接线回归交付

已跟进实际落地的 `ArenaSession` 接口，在既有 [ArenaSessionTest.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSessionTest.kt:107) 复用现有头手夹具和 `TrackingState.accept → ArenaSession.onTrackingEvent` 入口，新增两项针对方法，文件内测试方法由2项增至4项。

- `trialStartPublishesPhasesAndLatePresenterReceivesOnlyCurrentState` 验证READY期间不推进模拟时间，开始后的首tick只建立基线，既有待机时间到达后产生OVERHEAD出招与PREPARING事件。快照与事件批次对应，重复开始保留当前进度，晚注册立即取得当前快照和空事件，后续STARTUP变化继续从当前事件出口呈现。
- `userPauseRequiresFreshObservationsAndCurrentConfirmationWithoutClockCatchUp` 通过真实追踪状态消费USER_PAUSED，核对用户暂停身份和实际 `pauseId`。头手未齐时确认失败，先到新手位仍不足，新头部补齐后继续等待显式确认。错误ID及已消费ID均被拒绝，正确确认保留当前敌招与进度。暂停tick和恢复后的首tick不推进模拟时间，后续只累计恢复后的实际tick间隔。

上述断言覆盖应用状态与呈现事件出口。当前HUD控件点击、输入handle的生命周期交付、重开和实际动画画面仍按上表由主控统一实测。

已目视核对主控交付的 [f70e6aa玩家刀图](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/f70e6aa-player-dao.png)，原图1590×1646，SHA-256为 `94c67db8ac5f0ae2fda48aa4f3004645a4c35d46a1b6fd2ab200b7dac4e8b8ab`。图中酒馆、静态T-pose旧角色及右下玩家刀身可见，构建归属依据主控本轮交接。手部和握柄区域尚未充分展示，握姿、连续随动、新低模、四动作和HUD继续等待后续同构建画面。

源码静态差异检查 `git diff --check -- app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSessionTest.kt docs/agents/04-benchmark-qa.md` 通过，独立只读复核也已通过。新增内容仅为两个方法和既有领域类型导入，生产源码由分配负责人实现。编译及测试结果待主控统一运行，并核对两个新增完整方法名实际执行。此前81项结果对应 `f70e6aa`。

**本轮源码阶段结束，等待 review。** 交付为上述测试源码、静态检查结果和玩家刀单帧核对结论，等待主控统一构建结果与实际UI运行证据。

### 主控本轮代码 review

两项针对回归范围通过review。新资源观察确认slash为下劈，战斗线已按主控调整为既有 `AttackDirection.OVERHEAD`。请同步本轮试炼开始方法中原LEFT的方向／事件／preparationNanos断言为OVERHEAD，保留同一方法数与真实事件入口。时间断言读取现有方向字段，避免复制动作规则值。完成后写入静态复核结果，主控统一构建运行。

新低模静态Full Stage已通过，图 `artifacts/runtime/rigged-first-stage.png` 和 `rigged-first-stage-capture.json` 记录APK与资源身份。四动作与HUD在下一构建单独验收。

### Agent 本轮 review 修正回应

已在原试炼开始方法内同步四处方向相关断言，当前快照、AttackStarted事件、准备阶段剩余时间与推进至STARTUP的时长均使用 `AttackDirection.OVERHEAD`。准备时长读取该枚举的 `preparationNanos`。已只读核对生产方向与事件顺序，暂停恢复方法中的累计推进仍在该准备阶段内，两项针对方法范围保持一致。

### 主控统一验证与新增回归要求

主控当前工作区83项测试全部通过，0失败／错误／跳过，APK构建成功。两个新增接线方法均已进入完整集。当前还在修复review发现的停止屏障与呈现异常证据问题。

请在原ArenaSessionTest追加一项针对回归，使用战斗线新增的可注入失败日志函数，令呈现回调抛出具有cause的异常，验证异常被记录且状态操作只执行一次、正常推进保持。继续复用现有事件和状态入口，不扩故障框架。输入停止故障按02文档范围由输入线给静态／可复用测试证据，主控做生命周期实测。

上轮OVERHEAD断言同步仅修改测试与本文件，静态检查通过。主控现已回填83项测试与APK构建成功，两个接线方法均实际进入完整集。

**上轮OVERHEAD修正阶段结束，主控统一验证通过。** 该83项结果对应新增呈现异常回归之前的工作区。

### Agent 呈现异常回归交付

已按本次复审要求，在现有 [ArenaSessionTest.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSessionTest.kt:235) 追加一个方法 `presenterFailuresPreserveCausesWithoutReplayingResetOrBlockingProgress`，文件内测试方法由4项增至5项。

用例复用现有追踪事件和 `TrackingState`，注入实际落地的 `logFailure(context, Throwable)`。同一次ROUND_RESET处理中，手部呈现回调发生一次故障，场景呈现回调在接收RoundReset事件后发生故障，两者均抛出带不同cause的 `IllegalStateException`。断言核对两条上下文及原Throwable／cause的对象身份，确保失败记录保留完整异常链。

该用例同时断言roundGeneration只递增一次、RoundReset只投递一次、会话回到READY且清空旧观察。补齐新坐标代次的头手观察后，再次开始并经正常tick进入PREPARING，AttackStarted只出现一次，失败记录保持两条。断言沿用现有控制与状态入口。

已完成静态差异检查和独立只读复核，`git diff --check -- app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSessionTest.kt docs/agents/04-benchmark-qa.md` 通过。本轮产物为上述一个针对方法与交接说明，源码范围为该测试文件和本文件。新增方法编译与实际执行结果待主控统一回填，输入停止屏障与生命周期运行结果由输入线和主控交付。

**本轮呈现异常回归源码阶段结束，等待 review。** 等待主控确认新增完整方法名实际执行、全量测试及APK构建结果，再继续实际HUD与动作验收。

## QA 结束交接

按用户最新“主控唯一负责30分钟收尾”的调度，QA当前执行阶段结束。主仓库中已写入的产物全部保留，后续由主控统一补齐、构建、验收和合入。

- 已合入的两项预演输入回归位于 `PicoTrackingAdapterTest.kt`。当前未提交的 `ArenaSessionTest.kt` 保留三项新增方法，覆盖试炼开始与阶段呈现、暂停恢复门槛及呈现异常隔离。方向与事件断言已同步OVERHEAD。
- 主控已确认前两项接线方法进入83项完整测试集，0失败／错误／跳过，APK构建通过。第三项呈现异常方法已完成源码、静态检查与独立只读复核，实际编译和执行结果仍待主控回填。
- 五项UI与呈现验收点、构建身份要求及玩家刀单帧核对结论已保留在本文件。新HUD控件操作、四动作、握姿与连续随动、输入停止屏障及生命周期运行结果继续交主控验收。

**QA本阶段结束，已交主控统一收尾。** 当前回合结束，后续审核结果及最终交付由主控处理。

## Root final integration handoff

The user has assigned sole final ownership to root. All waiting loops and further worker edits are stopped. Existing production changes are integrated in the single main repository. The authoritative completed/incomplete result is docs/acceptance.md. The current build passes 84 unit tests. Static actor/HUD/idle and start-to-attack phases were observed. The emulator movement blue viewport, full live pause/reset checks, real hit/defense production and hardware validation remain open.
