# 动作输入与 PICO 追踪

## 当前交接

| 项目 | 当前状态 |
| --- | --- |
| 状态 | 本回合已结束，产物已交主控 root 统一收尾 |
| 当前主分支 | `f70e6aa` |
| 已合入成果 | 同一队列的头手预演、实际共享出招资格查询及日志 |
| 当前任务 | 保留当前源码与验证边界，主控统一补齐、构建、验收和合入 |
| 主控审核 | 身体移动链通过，虚拟双手当前由 HMD 派生，独立挥刀尚待实现 |

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

数字1日志白名单与玩家刀呈现已随 `f70e6aa` 合入。独立 review 发现并修复模型晚加载可能错过当前手位的问题，注册时立即同步最新有效快照，失效时发送null，恢复中头部最后到达也能更新显示。两项针对回归和两项预演输入回归均实际执行，完整81项测试通过、0失败／错误／跳过，APK构建成功。APK SHA-256 为 `f2e63201e9a2e0ee46a7745d0df02b9a72c41d0860e8959d584a5316cff7a88b`。实际数字1原始事件与玩家刀画面继续待主控验证。

主控对 `7645c5d` 运行 `:app:testDebugUnitTest :app:assembleDebug --offline` 成功，77 项现有测试通过。构建与已安装 APK SHA-256 均为 `41d3fc524ab88ef37d18bf0453a2fb928c3d5b13e8d9beacacc74e385261790b`。

18:10 用户确认关闭 Keyboard Mode、返回眼手模式并按 W。应用记录头部 Z 移至约 `-1.403 m`，虚拟右手 Z 同步至约 `-1.753 m`。`headSequence=26852`、`handSequence=26853` 与 `ArenaCombat` 中的同序号记录关联，目标距离约 `0.997 m`，出招资格由 false 变为 true。根入口为 `Main → ObserveTracking → PicoTrackingAdapter → TrackingEventBuffer → TrackingProcessor/TrackingState → ArenaSession → EnemyCombatStateMachine.canStartAttack(Boolean)`。

[原始验证日志](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/7645c5d-key-chain-verified.log) · [构建与验证范围](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/runtime/7645c5d-key-chain-verified.json)

### 当前有效的模拟器操作

- 当前预演使用模拟器原生相机键控，保持眼手／相机交互，手柄设置的 Keyboard Mode 关闭。推荐 ABC／英文输入法，按键前让 3D 视口获得焦点。官方说明 W/S/A/D 移动相机、Q/E 调整高度，右键拖动旋转视角。
- 手柄 Keyboard Mode 用于把键盘映射为控制器按钮，与本轮相机位姿入口分开。主控此前要求开启它的说明与当前实现不一致，已纠正。
- W 由模拟器宿主消费，应用从 HMD Provider 的位姿观察开始记录。真实按键来源由用户操作与确认关联，当前没有 Android W 原始 DOWN/UP 证据。

[官方键鼠说明](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_quickstart_create-your-first-spatial-app.md:61)

### 源模式和边界

仅在 debug 且 `Build.HARDWARE == ranchu`、显式启用预演时，头部观察标为 DESKTOP，并派生固定 Stage 偏移的左右手。手位相对头部为 X ±0.25 m、Y -0.4 m、Z -0.35 m，旋转沿用 HMD，日志标记 `HMD_DERIVED`、`synthetic=true`、质量 UNKNOWN。这些值是预演手位校准。该模式忽略真实控制器位姿及其不可用事件，头部失效、暂停和缺口仍中断全套预演观察。

默认硬件路径继续使用真实头部与控制器观察，两种来源进入同一个追踪消费者和战斗资格函数。当前双手不能独立操纵，当前结果尚未覆盖挥刀、格挡、弹反、技能或真机追踪质量。

本机当前进程还出现 `ControllerActionResult` 的 `sizeof p:32 / e:96` 报错，控制器 Provider 为 PENDING / DEVICE_NOT_SUPPORTED。它与动作回调缺失的因果尚未隔离，当前相机预演不依赖该动作回调。

## 当前交付方向与下一轮任务

用户要求在既有能力上完善UI、模型与动作呈现，底层追踪和战斗算法先暂停深入完善。主控负责HUD和场景，战斗线负责ArenaSession的既有状态／事件接线。

1. 当前源码职责切换为现有 `runtime/TrackingSession.kt` 与本文件。先提出最小控制接口，复用已有 `markUserPause` 和ROUND_RESET的生产路径，供主控HUD调用。控制对象在ObserveTracking生命周期中交给主控，释放时清理，避免UI持有失效session。
2. 与01-combat.md对齐暂停／恢复／重开顺序，保留既有队列、stamp、coordinateEpoch和观察失效语义。主控review接口后再写源码，避免各自新增一套命令机制。
3. 提供HUD的简短输入说明和状态文案。区分桌面预演、等待头手观察、暂停和实际设备来源，继续如实显示UNKNOWN质量含义。桌面已验证WASD相机移动、Q/E升降、右键转向的正常路径。
4. 主控继续处理实际数字1验证，当前不增挥击阈值、新传感器机制或碰撞夹具。
5. 源码完成交主控统一构建、合入与设备验证。各方共享唯一仓库，保留其他人的修改。

## Agent 当前回应

### 已批准控制接口的源码交付

**本阶段结束，等待主控 review。** 已按文末冻结接口在现有 `runtime/TrackingSession.kt` 完成源码，变更保留在唯一主仓库供主控审核与提交。新增 `TrackingControls` 和 `InputControlResult` 名称与批准稿一致，`ObserveTracking` 的 `onControlsChanged`、`onResumeRequested`、`onTick` 均带默认值，原调用可以继续编译。

**本次生命周期复审修复已结束，等待主控 review。** 主控确认前版统一构建与 `83` 项测试通过后，指出屏障失败会阻断 Provider 释放。本次已移除待处理控制失败或交付异常时的两个提前返回，继续执行原有 `adapter.stop()` 与停止恢复重试。停止期间的 `drain` 交付异常单独记录，后续 SDK 清理仍继续。`stop()` 的 finally 在 APP_PAUSED 结束边界记录残留意图，并清除 `pendingControl`、`pendingControlEnqueued`、`pendingControlRecovery`，旧 HUD 意图不会留到新 generation。

本次修复的静态路径已逐项核对。控制中重入停止先撤销句柄并延后释放，退出控制栈后执行 Provider 终止。四次屏障仍未完成及观察回调抛错两条路径均会到达 Provider 停止。SDK 停止本身若仍失败，保留 `attempted/stopRequested` 供后续启动前重试，期间不发布新句柄，本地旧 UI 意图已取消。独立只读复审与 `git diff --check` 通过。

故障注入边界尚未运行验证。当前 TrackingSession 为私有类并直接构造真实 SDK Provider，既有 FakeProvider 位于适配器测试的私有作用域，直接复用需要扩大构造接缝与运行环境。本轮按主控 review 先交最小修复和静态证据，保持统一测试／构建和生命周期设备验收由主控执行。前版 `83` 项通过不作为本次故障分支已经通过的证据。

- 会话成功启动后发布本次生命周期专属句柄。暂停或释放先撤销可用状态并回传 null，旧引用通过代次校验返回不可用，后续启动发布新句柄。新增回调均通过 `rememberUpdatedState` 读取当前接线。
- `pause()` 复用 `markUserPause`，`resetRound()` 复用同一个缓冲的 `ROUND_RESET`。现有队列继续生成来源、stamp 和 coordinateEpoch。每次只保留一个意图，并区分尚未入队与已入队等待恢复两个阶段，避免恢复重试重复生成暂停／重开。只有消费与恢复完成后才返回 APPLIED，有限次数仍受阻时保留同一意图并返回 PENDING，同请求继续报告 PENDING，另一命令返回 UNAVAILABLE。
- `resume(confirmedPauseId)` 先排空并处理已有恢复屏障，再一次性调用主控绑定的 `onResumeRequested`。确认 ID 和返回失败的点击均不缓存，回调后还会核对当前句柄代次。主控应绑定 `ArenaSession.confirmResume`，恢复门槛和实际战斗状态继续由战斗线负责。
- 若外部逐事件回调同步触发停止，先撤销句柄，Provider 停止延后到当前控制栈退出。停止时控制屏障无法完成会记录准确意图及入队阶段，随后继续释放 Provider，并在 APP_PAUSED 边界取消旧 UI 意图。SDK 停止本身失败时保留停止状态供后续启动前重试。该异常停止分支仍需统一验证。
- 现有正常排空与控制恢复处理结束后，且会话仍活动时，每帧调用一次 `onTick(System.nanoTime())`。控制方法本身不额外推进帧时钟，主控可绑定 `ArenaSession.onTick`。

主控 HUD 使用 `onControlsChanged` 绑定和撤销按钮入口，实际状态和待处理结果结合原有逐事件出口、Arena 呈现快照及控制结果展示。PENDING 表示恢复屏障仍存在，不能仅因对应控制事件已经出现就宣告全部处理完毕。生命周期撤销后应清除 HUD 的等待显示。

已完成正确性、维护性、提示/来源语义和配置漂移四项自查，以及独立只读复审。复查发现的回调重入停止和提前结束恢复屏障问题均已修复，最终静态复审通过，`git diff --check` 通过。本轮构建、测试与设备操作按分工交主控统一执行，待验证暂停／恢复／重开、饱和重试不重复控制、回调重入停止、旧句柄拒绝、每帧单次 tick 及现有头手预演回归。源码范围仅为批准的 TrackingSession，Main、ArenaSession、HUD 与测试由对应负责人接线。

### 暂停恢复重开接口稿

**本阶段结束，等待主控 review。** 本轮只交付接口与顺序约定，源码保持当前基线。已沿入口核对 `Main → ObserveTracking → TrackingSession → TrackingEventBuffer → ArenaSession`，以及适配器 `markUserPause` 和状态机现有 `pauseByPlayer/tryResume/resetRound`。

| 方案 | 控制出口 | 影响 |
| --- | --- | --- |
| 推荐由输入生命周期托管同一个 HUD 控制对象 | 暂停与重开进入既有队列，恢复先排空已接收输入，再委托 ArenaSession 的恢复入口 | HUD 使用一个对象，输入层管理生命周期和排队边界，战斗层保有 pauseId 与恢复门槛 |
| 分别暴露输入暂停重开与 ArenaSession 恢复 | HUD 直接调用两方对象，额外协调恢复前的输入排空 | 接口类型较少，主控需在 UI 调用处保证顺序和双方对象的有效期 |

建议在现有 `TrackingSession.kt` 内定义以下最小控制契约，所有方法由主线程调用。`APPLIED` 表示对应输入控制已交付处理，实际战斗状态以 ArenaSession 的呈现快照为准。`PENDING` 表示同一意图仍在可靠重试，HUD 暂停其他控制操作。`UNAVAILABLE` 表示当前生命周期无法接收。

```kotlin
interface TrackingControls {
    fun pause(): InputControlResult
    fun resume(confirmedPauseId: Long): Boolean
    fun resetRound(): InputControlResult
}

enum class InputControlResult { APPLIED, PENDING, UNAVAILABLE }
```

`ObserveTracking` 增加 `onControlsChanged: (TrackingControls?) -> Unit` 与 `onResumeRequested: (Long) -> Boolean`。前者在会话启动成功后交付控制对象，在应用暂停或 Compose 释放时先撤销可用状态并回传 null，保留旧引用的调用也返回不可用。后者由主控绑定战斗线的恢复方法，继续使用当前回调。现有 `onEvent` 仍负责逐事件交付与输入观察状态，避免复制追踪判定。

执行顺序建议如下，交战斗线对齐后由主控确认。

1. **暂停。** 控制对象调用已有 `adapter.markUserPause()`，排空同一输入队列。ArenaSession 应优先消费 `USER_PAUSED`，调用 `pauseByPlayer()`、清除 `hadReadyInput` 和 `lastInputTime`，并完成该控制分支。当前生产代码还会直接进入 `interruptTracking`，需由战斗线调整这个已存在的入口。Provider 持续供数，暂停后到达的新观察仍用于建立当前基线。
2. **恢复。** 按钮携带 HUD 点击时实际显示的 `pauseId`。输入会话先处理已有控制屏障并排空已接收观察，再将该 ID 一次性传给 `onResumeRequested`。ArenaSession 使用当前真实 ID、追踪与动作就绪门槛调用 `tryResume`。就绪不足或 ID 已变化时返回 false，早于就绪的确认不缓存，后续新观察也不自动重用该点击。恢复成功时由战斗线重建输入计时基线，避免把暂停时长推进为战斗时间。
3. **重开。** 会话通过已有 `buffer.discontinuity(当前来源, ALL, ROUND_RESET)` 入队并排空，保留队列生成的 stamp 和递增 coordinateEpoch。ArenaSession 只在接收到该事件后执行现有 `resetRound` 并重置试炼展示状态。后续真实观察重新建立基线，HUD 从战斗事件更新画面。
4. **控制饱和。** 暂停按“消费旧批次 → 重试同一 markUserPause → recoverControlOverflow → 再消费”处理，重开按“消费旧批次 → 重试同一 ROUND_RESET → 再消费”处理。有限次数内仍受阻时，会话仅保留一个待处理意图并返回 PENDING，保持原请求身份和顺序，拒绝另一命令。应用停止或释放也须先处理该屏障或明确报告未能清理的状态，撤销 HUD 对象本身不丢弃待处理意图。沿用已有缓冲与可靠控制机制。

需要主控及战斗线确认的边界有两项。其一，同意恢复由该控制对象排空输入后委托 ArenaSession，还是由主控显式协调两个对象。其二，当前展示阶段的 `actionReady` 应由战斗线给出有依据的定义，`TrackingSnapshot.hasRequiredObservations` 只代表当前头手观察齐备，不能用同一个值代替两个独立门槛。输入层继续保持质量 UNKNOWN 的既有语义。

HUD 可采用以下短文案，由主控统一组合展示。

| 条件 | 建议文案 |
| --- | --- |
| 显式模拟器预演 | 桌面预演 · 合成双手 |
| 真实头手来源 | PICO 设备输入 · 追踪质量未知 |
| 必需观察未齐 | 等待头部与持刀手 |
| 当前观察齐备 | 头手观察已接收 · 追踪质量未知 |
| 用户暂停 | 已暂停 |
| 恢复门槛未满足 | 准备就绪后再继续 |
| 可靠控制仍在处理 | 正在处理，请稍候 |
| 会话暂不可用 | 输入暂不可用 |
| 桌面操作说明 | WASD 移动 · Q/E 升降 · 按住右键转向 |

暂停文案由战斗状态优先决定，避免被暂停控制引起的暂时缺少观察覆盖。固定手位来源显示合成性质，独立挥刀入口继续等待主控验证。源码实现与运行验证在接口获 review 后推进。

### 上轮数字 1 监听交付

**本阶段已结束，主控代码 review 及统一构建通过。当前等待真实数字 1 入口结果与下一轮 review。** 已在唯一主仓库的 `platform/LaunchActivity.kt` 将现有诊断白名单由 W 扩展为 W 和 `KEYCODE_1`，源码差异为一行条件调整，主控已随 `f70e6aa` 合入。按下与释放、重复次数、输入设备/来源、扫描码、flags、Android 事件时间及应用单调接收时间继续由现有 `ArenaKeyboard` 日志记录，运行条件保持 debug 且 `ranchu`，事件继续交给父类分发。

已核对本机 Android 35 官方源码中 `KEYCODE_1 = 8`，并完成条件边界、分发行为、日志字段与变更范围的自查及 `git diff --check`。构建、提交、安装与模拟器操作由主控执行。数字 1 的真实按下/释放是否到达当前 Activity 尚待日志证明，独立手位的连续轨迹在该入口确认后进入下一轮设计。

## 主控接口 review 与实现批准

采用推荐的单一生命周期 `TrackingControls`，冻结 `pause():InputControlResult`、`resume(confirmedPauseId:Long):Boolean`、`resetRound():InputControlResult` 及APPLIED／PENDING／UNAVAILABLE。ObserveTracking新增 `onControlsChanged`、`onResumeRequested` 和 `onTick(nowNanos)` 回调，使用默认参数保持已有调用可用。

与战斗线已对齐，恢复先排空再委托 `ArenaSession.confirmResume`，确认不预存。READY停钟、重开回READY由战斗线负责，输入只生产既有控制并管理可用性。onTick在正常排空及既有溢出恢复的第二次排空结束后，每帧仅调用一次System.nanoTime。控制饱和沿已有队列／恢复路径处理，当前仅需一个待处理意图与现有屏障。

现在可在分配的TrackingSession.kt内实现并更新本文件。生命周期停止／释放先撤销HUD入口，旧handle拒绝新调用，后续启动重新交付handle。QA和主控统一测试，勿并行修改Main／ArenaSession。

主控已捕获f70e6aa实际玩家刀画面 `artifacts/runtime/f70e6aa-player-dao.png`，旧Tripo／酒馆与右下玩家刀可见，该图仅验玩家刀呈现。宿主正常OS按键自动化已尝试数字1，包含定向与前台两条发送路径，当前应用日志未出现DOWN／UP。按用户最新方向，该深层诊断暂收束，当前优先HUD控制接线。原已验证W相机派生头手链仍按原范围验收。

## 主控代码复审修改要求

统一工作区已通过编译及83项测试，review发现需先修的生命周期问题。`stopProviders`处理pendingControl时，若四次屏障仍无法完成或drain回调抛异常，当前提前return会跳过adapter.stop及清理。ON_PAUSE可能没有后续帧，onDispose会取消frame loop，旧Provider可能持续运行。

请保留控制投递失败证据，但让生命周期终止继续执行既有adapter.stop／Provider释放路径。释放后清除pendingControl、pendingControlEnqueued、pendingControlRecovery，旧UI意图不得在新generation中重放，旧handle保持失效。停止边界沿用APP_PAUSED。只修本次控制接线引入的阻断，保持既有队列与停止恢复规则。

优先用已有可复用依赖接缝验证pending未完成时仍释放、旧handle拒绝、重启不重放。如现有私有类与真实SDK构造要求新增大套测试框架，先交最小修复和静态路径证据，主控统一做生命周期运行验收并如实记录未覆盖的故障注入边界。

## 本回合结束交接

按用户终极调度要求，本输入回合已结束，文件监视、等待和轮询已停止，产物保留在唯一主仓库，后续由主控 root 统一收尾。

当前生产源码差异位于 `app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/TrackingSession.kt`，相对 `f70e6aa` 为 `208` 行新增、`13` 行删除，尚未由主控提交。内容包含批准的暂停／恢复／重开控制对象、生命周期代次、单个意图的入队与恢复阶段、最新 Compose 回调及排空后的帧时钟出口。最新修复确保控制屏障失败或观察回调异常仍执行 Provider 释放，在 APP_PAUSED 结束边界记录并取消残留 UI 意图。

已完成源码静态自查、独立静态复审和差异检查。主控前版 `83` 项测试与构建通过，最新生命周期修复尚待统一重跑和故障验证。停止屏障受阻、观察回调异常、旧句柄失效、重启不重放，以及实际页面暂停／销毁后的 SDK 释放属于需要明确取证的边界。主控统一确认 HUD 与 Arena 回调接线、最终 APK 身份和实际控制效果。

数字 1 的 Android 原始按下／释放尚未观察到，独立手位与挥刀尚未实现，PICO Space Pro 真机仍待验。已验证的 W 相机 → HMD → 合成双手 → 共享出招资格链继续按原证据范围保留。当前阶段的底层诊断与算法研究按最新方向收束。

**本阶段结束，交主控 root 审核与收尾，本回合不再等待后续派发。**

## Root final integration handoff

The user has assigned sole final ownership to root. All waiting loops and further worker edits are stopped. Existing production changes are integrated in the single main repository. The authoritative completed/incomplete result is docs/acceptance.md. The current build passes 84 unit tests. Static actor/HUD/idle and start-to-attack phases were observed. The emulator movement blue viewport, full live pause/reset checks, real hit/defense production and hardware validation remain open.
