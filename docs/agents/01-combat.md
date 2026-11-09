# 战斗状态与动作呈现

## 当前交接

| 项目 | 当前要求 |
| --- | --- |
| 当前主分支 | `f70e6aa` |
| 本轮方向 | 复用既有战斗能力，补状态、事件和控制接线，支持HUD与动作 |
| 冻结范围 | 新碰撞算法、严格几何证明、新追踪阈值与底层规则扩展 |
| Agent 负责 | `runtime/ArenaSession.kt` 的呈现出口与既有状态机调用接线 |
| 主控负责 | `Main.kt`、`HomeStage.kt`、HUD设计与实现、Tripo任务、合入与运行验收 |
| 输入负责 | `TrackingSession.kt` 的既有暂停／重开控制出口 |
| 美术负责 | 低模、骨架、握点、动作资源的整理 |
| QA负责 | 当前阶段必要验证及实际画面／操作证据 |

## 当前交付方向

用户要求在既有能力上改善游戏机制呈现、UI、建模和动作，底层游戏机制先暂停继续完善。主控以场景／角色／玩家刀可见、现有试炼阶段可展示、开始／暂停恢复／重开可用作为基础展示门槛，随后在BrickerP个人账号创建独立私有GitHub仓库，再继续UI、美术和动作迭代。基线门槛由主控审核实际构建与画面。

## 共同执行约束

用户已预先批准本项目后续操作。主控按职责分工自主review与执行，并报告阶段成果和实际费用。共享设备、提交及Tripo任务由主控统一调度，Agent继续遵守文件职责范围。

- 唯一仓库为 `/Users/yupeng/projects/personal/pico-wuxia-arena`，各方保留其他人的修改。
- Kotlin + PICO Spatial SDK6.1.9、pico-cli、Gradle8.13、JDK21，PICO Space Pro／OS6，桌面通过PICO模拟器预演。
- `/Users/yupeng/projects/personal/pico` 为只读参考，`BrickerP.github.io` 不属于当前仓库。
- 四份固定任务文档承担当前分工、review及交付。正式提交、设备与CLI任务由主控统一协调。
- 原生VR输入继续基于真实头手。桌面当前为HMD派生双手预演，来源和质量如实展示。

## 已完成进展与主控 review

`f70e6aa` 已合入玩家dao呈现、数字1日志入口和四项必要回归，完整81项测试／APK构建通过。异步模型晚注册会错过手位的问题已修复，注册时立即同步最新有效追踪快照，失效时隐藏，恢复中Head最后到达也能更新显示。新APK已安装，进程13610，实际画面及数字1入口继续待验证。

真实W已于18:10进入 `PicoTrackingAdapter → TrackingEventBuffer → TrackingState → ArenaSession → canStartAttack`，验证到出招资格，完整攻击结果继续待接线。已有旧Tripo角色／酒馆Full Stage图像身份为f5ab507，不能当作新低模的运行图像。

此前A/B/C连续接触方案均未进入生产。C的刀外包最大样本约25mm、身体粗候选最大样本约111mm，当前候选未获批准。按用户新方向，该研究阶段收束，当前工作转向既有状态机的应用接线与表层呈现。

## 正常入口发现的未接能力

当前 `ArenaSession` 只调用 `advanceBy` 并查询 `canStartAttack`，没有生产调用 `tryStartAttack`，因此敌人实际保持IDLE。`advanceBy`、`interruptTracking`、`resetRound`返回的呈现事件也被丢弃。追踪恢复后没有 `tryResume`，暂停状态可能持续保留。

已有 `receivePlayerHit`、`resolveActiveAttack`、`pauseByPlayer`、`tryResume` 和ROUND_RESET消费分支，分别覆盖受击／格挡弹反／玩家暂停／恢复／重开。当前新任务先补明确的应用调用和事件出口，实际伤害输入继续按已有真实输入能力接线。

## 本轮任务

1. 先在本文件回复一个最小接口约定，供主控与输入线对齐。HUD读取现有状态机快照、输入就绪、范围资格及试炼是否开始，避免复制底层规则和数值。
2. 提出既有出招、暂停、恢复、重开在ArenaSession中的最小调用时序。恢复必须复用真实pauseId和新观察就绪门槛，重开仍经过已有ROUND_RESET路径。
3. 提出状态／事件呈现出口。消费现有 `EnemyCombatEvent`，支持动作和HUD，注册晚于资源加载时同步当前状态，释放时解除绑定。
4. 主控review接口后，在本文件规定源码范围落地最小接线。核心 `core/combat/EnemyCombatStateMachine.kt` 规则保持在当前范围，当前优先让既有能力进入真实入口。
5. 主控负责UI和场景实体，勿并行修改Main／HomeStage。输入线在TrackingSession暴露生命周期受控的暂停／重开入口，先通过文档对齐控制语义。

## 当前资产与后续出口

运行源GLB为 `ArtSource/tripo-warrior/tripo-out/f2a5c5b3-rig-bb23cd4c/model.glb`，18,833三角面、2.39MB、78关节、真实蒙皮，当前0动画。主控将先制作slash并核验，再补idle／hurt／fall等确实存在的预设。最终整理后的运行资源与动作路径由03-art.md交付。

完成接口稿后写明阶段结束及待主控review事项。下一轮以实际状态切换、动作衔接和HUD反馈为验收出口。

## Agent 最小接口稿

**阶段结束，等待 review。** 本轮核对 `f70e6aa` 的实际入口，仅修改本文件，先交主控与输入线对齐。源码落地范围为现有 `runtime/ArenaSession.kt`，Main、HomeStage、HUD及TrackingSession由各自负责人接线。

### 呈现出口

建议沿用现有 HandPosePresenter 的同步回调模式。另一种方式是 StateFlow 快照加独立事件流，但当前只有主控一个呈现接线点，后者增加订阅、事件缓存和释放策略。采用一个回调可直接复用当前晚注册同步方式，主控在回调中更新HUD状态并分发动作事件。

拟定接口如下，名称供本轮冻结。

```kotlin
typealias ArenaPresenter = (ArenaViewState, List<EnemyCombatEvent>) -> Unit

fun setArenaPresenter(presenter: ArenaPresenter?)
fun startTrial(): Boolean
fun confirmResume(pauseId: Long): Boolean
fun onTick(nowNanos: Long)
```

`ArenaViewState` 为不可变快照，包含下表。状态机字段直接读取，协调字段只表示应用会话与当前观察。

| 字段组 | 最小内容 |
| --- | --- |
| 会话 | roundGeneration、trialStarted、sceneReady |
| 状态机 | simulationNanos、phase、phaseElapsedNanos、phaseRemainingNanos、attackId、attackDirection |
| 敌人表现 | health、initialHealth、guarding、hitReaction |
| 暂停 | pauseReason、pauseId、resumeReady |
| 输入与范围 | inputReady、inputOrigin、headQuality、dominantHandQuality、targetInRange、canStartAttack |

`initialHealth` 从本实例创建后的 `combat.health` 取得，HUD血条不复制100等规则值。输入就绪沿用 `hasRequiredObservations`，来源与UNKNOWN质量照实提供。缺少几何或必要观察时，范围/出招资格字段为未知，已知时才调用既有 `canStartAttack`。开始试炼是独立会话门槛，出招资格继续读取同一状态机。

注册后立即发送“当前完整快照 + 空事件列表”，资源晚加载也能定位当前阶段和进度。每次状态机操作后消费其返回事件，按原顺序发送本次事件与操作后的快照。解除绑定只清呈现回调，后续重新注册再同步当前状态，一次性音效/受击事件不补放。动作使用roundGeneration与attackId识别身份，以phaseElapsed/remaining定位播放进度。

### 控制与唯一时钟时序

| HUD意图 | 入口与消费顺序 |
| --- | --- |
| 开始 | `ArenaSession.startTrial()` 检查场景、必要观察和当前暂停状态，成功后设置trialStarted并清时钟基线。重复开始不重置状态机 |
| 暂停 | 输入生命周期handle调用既有 `adapter.markUserPause()`，同一队列产生USER_PAUSED。ArenaSession在通用观察缺失分支之前消费它并调用 `pauseByPlayer()`，发布真实pauseId |
| 恢复 | 建议输入handle的 `resume(pauseId)` 先排空待处理观察/控制，再回调 `ArenaSession.confirmResume(pauseId)`，当场核对新观察门槛与当前pauseId后调用既有tryResume |
| 重开 | 输入handle投递既有ROUND_RESET，ArenaSession在该事件推进时间之前仅调用一次resetRound，递增roundGeneration，清时钟和旧确认，再发布RoundReset及完整快照 |

建议READY阶段不推进模拟时钟，开始后才推进既有800ms待机等待。重开回到READY，由用户再次开始。这两项是本轮需主控确认的会话呈现语义，核心规则数值保持原值。

时钟入口建议由 `ObserveTracking` 增加一个 `onTick` 回调。在 `TrackingSession.onFrame` 完成正常drain及溢出恢复后的第二次drain之后，调用一次 `onTick(System.nanoTime())`。队列当前也使用System.nanoTime，Compose frameNanos只提供帧节拍。ArenaSession移除Controllers分支原有的时间差推进，统一由tick读取最新快照并推进，Head最后恢复或静止无新Controllers时也能更新状态。[现有帧入口](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/TrackingSession.kt:121)

每tick在trialStarted、输入与场景就绪且未暂停时，先 `advanceBy`，保留全部事件，再至多调用一次现有 `tryStartAttack`。本轮建议用既有LEFT方向展示，方向策略可由主控确认。护刀结束时状态机可能已自动反击，重复请求会由现有状态条件拒绝。开始、暂停、成功恢复、重开、失效和场景不可用时均清tick基线，下一次有效tick只建基线，避免补入停顿时间。

### 暂停与恢复门槛

USER_PAUSED产生的预期观察清空归主动暂停，其后新头/手逐项到达期间保持该暂停。另有真实追踪失效、APP_PAUSED、重定位、缺口、换手或必要来源连续性变化时，调用既有interruptTracking，保留新的暂停身份。非持刀手失效继续沿现有单刀必要来源语义处理。

暂停时记录控制序号与必要来源的连续性基线。恢复就绪需头和当前持刀手均在暂停序号之后产生新有效观察，并满足TrackingState的requiredSinceSequence和当前坐标/连续性代次。当前无挥击识别会话，本轮actionReady仅表示旧动作引用已清且新头手基线已建立，该含义写入调用约定。确认在门槛未满足时立即失败，不能提前保存。过期pauseId同样失败。

纯USER恢复保留敌招和剩余时长，TRACKING_INTERRUPTION恢复由现有状态机取消旧招、清护刀并回IDLE。成功恢复后清tick基线，继续前必须再次经过最新排空后的状态。输入handle在ObserveTracking生命周期注册时交给主控，释放时交null，HUD据此禁用已失效入口。恢复不会重复产生新的tracking控制事件。

### 事件消费与本轮待审核点

`advanceBy`、`pauseByPlayer`、`interruptTracking`、`tryResume`、`resetRound`和`tryStartAttack`的返回事件均进入上述出口。RoundReset只有重开事件，HUD通过完整快照同步生命、护刀和阶段。HIT→HIT仍需消费真实受击事件，护刀下EnemyDamaged不会每次重播整段硬直。大步长跨阶段时保留事件顺序，最终动作进度读取最终快照。动作资源只按03已核验的真实资源名称映射。

现阶段已有受击、格挡/弹反结果入口仍无真实接触来源，本轮将它们作为既有领域事件呈现能力保留。敌招到生效期末的既有MISSED事件用于展示窗口结束，UI与实际伤害结果的接线由后续真实输入能力确认。

请主控冻结同步回调字段/名称、READY停钟与重开返回READY、初轮LEFT出招，以及输入handle的排空后恢复回调和每帧tick接线。通过review后再在ArenaSession落地，随后交主控统一构建和运行验证。本轮已完成调用链与控制顺序静态核对，源码尚未修改。

## 主控接口 review 与实现批准

接口稿通过，采用现有呈现回调模式。冻结 `ArenaPresenter`、`ArenaViewState`、`setArenaPresenter`、`startTrial`、`confirmResume(pauseId)`、`onTick(nowNanos)`，另提供只读 `viewState` 给主控初始化HUD。完整状态字段按上表，规则值直接读现有实例。

READY停钟、开始后推进既有待机时间、重开回READY通过本轮范围review。新slash的实际观察确认主要动作是下劈，首轮展示方向据此改为既有TOP，保持HUD方向与模型一致。每帧由输入会话排空后仅调用一次onTick，移除Controllers分支的旧推进，保持唯一时钟。恢复使用输入生命周期handle排空后的onResumeRequested委托，pauseId与新头手基线在ArenaSession当场校验。

`actionReady`本轮的应用含义为旧动作引用已撤销、当前场景可用且新的持刀动作基线已建立。与原始追踪观察是否齐备分别记录。当前尚无挥击识别会话，该值的验收范围为本段列明的应用状态。

现在可在分配的ArenaSession.kt中实现。保留既有构造和手位呈现功能，消费事件保持顺序，晚注册发送当前快照和空事件，离场清回调。源码完成交主控统一构建。QA负责后续最小接线回归，避免并行修改测试文件。

## Agent 源码交付

**阶段结束，等待 review。** 已在唯一主仓库修改 `app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/ArenaSession.kt`，本交接文件同步更新。源码保留为未提交差异，主控负责统一构建、合入和设备验收。

- 已提供不可变 `ArenaViewState`、`ArenaPresenter`、只读 `viewState`，以及冻结的 `setArenaPresenter`、`startTrial`、`confirmResume(pauseId)`、`onTick(nowNanos)`。快照按已审字段实现，并独立提供actionReady。
- READY停钟，开始建立新时钟基线。按最新动作review，后续tick请求现有 `AttackDirection.OVERHEAD` 下劈出招，对应主控文档中的TOP。Controllers旧推进已移除。Start按钮应依据场景、输入和暂停状态开放，READY中的canStartAttack仍受状态机待机时间约束。
- 所有实际状态机返回事件进入同一呈现批次，注册时立即交当前快照与空事件，解绑后停止回调。玩家刀晚注册同步及失效隐藏入口保持现有行为。呈现回调异常会记录并隔离，状态机操作不会被重放。
- accepted USER_PAUSED先进入主动暂停，预期清空后新的有效头手分包可重建基线。独立控制中断、必要来源连续性/coordinateEpoch/requiredSinceSequence变化会撤销动作基线并分配真实中断身份。重复被忽略且仍有效的快照保留原有观察语义。
- 恢复当场核对当前pauseId、必要观察与暂停序号后的新基线。重开仅消费既有ROUND_RESET，递增roundGeneration并回READY，清空时间与旧日志身份。场景不可用、暂停与失效时清tick基线，恢复后首tick只建基线。

静态检查已完成 `git diff --check`，并复审条件、空值/迟到注册、事件顺序、暂停代次与时钟边界。构造参数 `logMessage` 及玩家刀呈现签名保持可供现有测试使用。本轮依主控统一调度要求，构建、测试及设备运行尚未执行。QA可围绕开始后推进、晚注册同步、纯暂停/真实失效区分、旧pauseId拒绝与重开回READY核对现有入口。

### 下劈方向复审回应

**阶段结束，等待 review。** 已将首轮普通出招调用改为 `tryStartAttack(AttackDirection.OVERHEAD, targetInRange)`。当前代码的下劈枚举名为OVERHEAD，复用其既有预备/出招/生效/恢复参数。源码静态差异已检查，主控统一运行构建和动作验收。

## 主控代码复审修改要求

统一工作区编译及83项测试已通过，呈现异常隔离还有一项证据缺口。presentHand与publish当前仅把error.message交给info字符串日志，异常类型、完整堆栈及cause丢失。

请保持隔离和状态机不回放语义，以最小可注入的失败日志函数保留Throwable，默认调用现有Android Log.e(TAG, context, error)，不添加日志框架或依赖。保留已有构造调用可用。QA将在现有ArenaSessionTest补一项针对回归，验证抛异常presenter仍只执行一次领域操作并记录实际异常。源码修复后交主控统一验证。

### Throwable 日志修复交付

**阶段结束，等待 review。** 已为ArenaSession增加带默认值的构造参数 `logFailure: (String, Throwable) -> Unit`，默认执行 `Log.e("ArenaCombat", context, error)`。玩家刀和Arena呈现回调的catch均传入实际异常对象，保留类型、堆栈与cause。现有无参及 `logMessage = {}` 构造调用已逐处核对。

回调仍在原操作之后执行，失败路径只记录异常，状态机操作与事件批次维持一次交付语义。修改范围为ArenaSession.kt及本文件，`git diff --check`通过。本次日志修复等待QA针对回归和主控统一构建，主控记录的83项通过结果属于修复前统一工作区。

## 终止调度交接

按用户最新调度，本 Agent 已停止开发、等待和轮询，文档监看进程已终止。阶段结束，交 root review 并统一收尾，本回合结束。

当前战斗交付保留于唯一主仓库的ArenaSession.kt及本文件，包含完整呈现快照/事件出口、开始与唯一tick、主动暂停和追踪中断区分、真实pauseId恢复、重开回READY、OVERHEAD下劈展示及Throwable失败日志。生产文件不再由本 Agent 继续修改。

本轮静态检查通过。最终Throwable针对回归、统一构建、实际HUD控制/动作同步和设备验收由root接管，提交与合入也由root统一完成。旧碰撞方案及未批准的几何参数继续保持冻结。

## Root final integration handoff

The user has assigned sole final ownership to root. All waiting loops and further worker edits are stopped. Existing production changes are integrated in the single main repository. The authoritative completed/incomplete result is docs/acceptance.md. The current build passes 84 unit tests. Static actor/HUD/idle and start-to-attack phases were observed. The emulator movement blue viewport, full live pause/reset checks, real hit/defense production and hardware validation remain open.
