# 战斗与敌人 AI

## 当前交接

| 项目 | 当前状态 |
| --- | --- |
| 状态 | 停止旧碰撞任务，等待真实键盘链路证据 |
| 当前主分支 | `70ea9f9` |
| 已合入成果 | `bbbd196` 确定性敌人状态机 |
| 待处理成果 | `d6294bf` 隔离碰撞实验，模拟器运行出现失败，尚未合入 |
| 当前任务 | 保全与入口只读核对完成，等待真实键盘链路证据和主控派发 |
| 主控审核 | 首轮实验不能支撑正式接触判定，先完成真实键盘入口 |

## 共同执行约束

- 唯一工作目录为 `/Users/yupeng/projects/personal/pico-wuxia-arena`。直接在该仓库按职责协作，主控审核与提交。已有副本先保全未提交差异，再由主控迁回并清理。每次提交只包含自己负责的文件。
- 技术栈为 Kotlin + PICO Spatial SDK 6.1.9，使用 pico-cli、Gradle 8.13、JDK 21。目标设备为 PICO Space Pro / OS 6。桌面预演通过 PICO 模拟器运行。
- `/Users/yupeng/projects/personal/pico` 是只读技术参考。`BrickerP.github.io` 不属于本任务。
- 当前最高优先级是一次真实键盘按键进入模拟器应用，生成连续虚拟头手轨迹，并进入与真实头手输入共用的战斗判定。主控保存按键、轨迹和判定三段关联日志，完成后在四份文档解除后续玩法门槛。
- 该证据完成前，停止新增挥击阈值、碰撞夹具和 QA 用例。真实 VR 战斗由头部及手部动作驱动。
- 敌人由已配置账号的 Tripo 生成写实中式刀客，导出 GLB，优先绑定与动作能力。Blender 只处理米制、轴向、原点、握点和现有 dao 对齐。
- 模型必须进入 Full Stage，交付用户可直接查看的运行时画面。空间截图失败时，由主控改用模拟器窗口截图、录屏或其他可观察的实际渲染捕获。
- 四份固定文档用于当前任务、评审和交付。Agent 更新本文件进度，主控填写审核和下一步。共享设备安装、停止、输入与捕获由主控协调。

## 本轮职责和出口

1. 立即停止此前原生碰撞实验迭代。在当前文件报告已停止、未提交文件和已有提交，供主控保全与迁回。
2. 只读确认已有 `EnemyCombatMachine` 的真实调用入口及它要求的领域事件。键盘链路接通前等待主控，不扩充玩法、夹具或参数。
3. 真实键盘链路完成后，按主控复审恢复一对一攻防、生命、胜负与重开。轨迹与实际几何形成接触后再提交领域结果，保持唯一判定路径。
4. Tripo 敌人进入 Full Stage 后，使用实际骨架、刀具握点和动作时间与主控对齐。用户体验目标包含格挡、弹反、闪避、技能组合和流畅处决。

## 当前证据与待处理问题

主控首轮模拟器实验观察到静止球投射和初始重叠结果符合参考。高速位姿跳变、双体运动及旋转案例未通过，冻结起点投射还出现 null。原因仍待区分夹具同步、状态污染和 SDK 运动语义。既有差异保全后暂停此项，等待键盘门槛解除。

## Agent 当前回应

**本轮保全与入口核对阶段结束，等待 review。** 碰撞实验迭代已停止。本轮只读核对以主仓库 `70ea9f96da71df86b8a764a0e6120c44a2c80a73` 为准，当前战斗侧修改的文件为本交接文档。

### 已有成果保全与迁回清单

已有战斗工作副本 `/Users/yupeng/projects/personal/pico-wuxia-arena-combat` 和 `/Users/yupeng/projects/personal/pico-wuxia-arena-combat-probe` 均已核对，Git 状态干净。敌人状态机原提交 `756e18f` 已以 `bbbd196` 合入唯一主仓库。实验提交 `d6294bf03c6d533f8df391940dc5f87d8f5ff1a3` 含以下三个文件，由主控按新时序决定迁回和清理。

| 文件 | 当前处置 |
| --- | --- |
| `app/src/androidTest/collision-probe.init.gradle` | 专用实验 runner 配置，随已有提交保全 |
| `app/src/androidTest/java/com/example/wuxiaarena/core/combat/NativeCollisionProbe.kt` | 含首轮模拟器未通过条件，随已有提交保全 |
| `app/src/androidTest/java/com/example/wuxiaarena/core/combat/NativeCollisionOracleTest.kt` | 3 项解析基准的既有本地验证已完成，随已有提交保全 |

上述副本与主仓库共享 Git 对象，主控可在唯一仓库直接审查已有提交。此前实验的失败与同步疑点仍需后续授权任务处理。

### 实际入口与领域事件

实际类名为 `EnemyCombatStateMachine`。主仓库生产源码中目前只有该类和公开方法定义，实例化与调用位于单元测试。它仍是尚待生产接线的已合入模块。[状态机定义](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/core/combat/EnemyCombatStateMachine.kt:100)

实际应用入口从清单中的 `SpatialApplication`、`LaunchActivity` 进入 `mainApp`，由 `DefaultStage` 承载 `ObserveTracking` 和 `HomeStage`。追踪生命周期与帧处理经过 `TrackingSession`、`TrackingProcessor` 到 `TrackingState.accept`，当前出口为追踪日志和观察就绪状态。`HomeStage` 加载酒馆模型与灯光。当前 `LaunchActivity` 继承 SDK 的启动 Activity，应用键盘处理及轨迹到战斗状态机的调用仍待主控接通。[Stage 入口](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/Main.kt:11)

| 状态机入口 | 调用方需提供的领域信息 |
| --- | --- |
| `advanceBy`、`tryStartAttack` | 模拟时间步、有效目标距离和招式方向，外部接触与中断发生前拆分推进区间 |
| `receivePlayerHit` | 已确认接触且按对局、挥击和目标完成去重的有效命中 |
| `resolveActiveAttack` | 当前招式 ID，以及已裁定的格挡、弹反或玩家受击结果，未命中由生效窗口结束产生 |
| `pauseByPlayer`、`interruptTracking`、`tryResume` | 有序暂停或中断，以及追踪就绪、动作就绪和匹配当前暂停 ID 的确认 |
| `resetRound` | 可靠的重开控制，上层维护对局身份并过滤旧输入和旧结果 |

状态机输出阶段变化、招式开始/裁决/取消、敌人生命变化、护刀变化、受击反应、暂停变化和重开事件。当前入口核对仅为静态证据，真实键盘、连续轨迹与共享战斗判定的关联日志等待主控提供。
