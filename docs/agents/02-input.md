# 动作输入与 PICO 追踪

## 当前交接

| 项目 | 当前状态 |
| --- | --- |
| 状态 | 停止旧挥击任务，重启真实键盘入口诊断 |
| 当前主分支 | `70ea9f9` |
| 已合入成果 | `1463ee3`、`3ea626f` 输入队列与适配，`70ea9f9` 生命周期接线 |
| 待处理成果 | `20174ae` 挥击候选，发现并发时间推进问题，尚未合入 |
| 当前任务 | 保全修复差异，只读排查真实 W 输入与虚拟手柄通路 |
| 主控审核 | 用户真实 W 尚无应用日志，当前仅头显姿态回调已观察到 |

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

1. 立即停止挥击阈值、姿态旋转候选和新动作实验。列出已有修复差异供主控迁回唯一仓库。
2. 通过本机官方文档与已安装 SDK 公开类型核实模拟器 Keyboard Mode、虚拟手柄输入和应用入口。主控独占设备操作，Agent 交付具体诊断步骤和可观察回调。
3. 主控验证真实按键后，负责最小连续虚拟头手轨迹接入。轨迹通过既有 `TrackingEventBuffer` 和共用输入/战斗处理，日志需关联按键边沿、轨迹序号和判定消费。
4. 只在主控确认真实链路后，按新 review 恢复必要修复和动作识别。键盘预演模式与真实头手模式使用同一战斗规则。

## 当前证据与待处理问题

- 用户在模拟器前台按 W，临时诊断 APK 的 Android `dispatchKeyEvent` 没有新增日志。设备侧注入 W 曾进入该监听。真实按键的焦点、模式和虚拟摇杆映射仍待核实。
- `70ea9f9` 在模拟器观察到头显姿态，控制器显示 `PROVIDER_UNAVAILABLE`，尚未观察到手柄姿态。
- `20174ae` 中 drain 后、时间推进前的正常回调可在下一批被误判 `INVALID_TIME`。保留已有修复，先迁回仓库，当前不扩动作范围。
- 头显与控制器来自独立 Provider，应用接收时间用于观察排序。硬件时间和逐分量质量仍需真实设备测量。

## Agent 当前回应

### 停止确认与迁回清单

已停止挥击识别、姿态旋转候选、阈值和新增测试开发。后续工作采用唯一仓库 `/Users/yupeng/projects/personal/pico-wuxia-arena`。旧副本保留原状，等待主控迁回安排。

- 已提交的候选原型为旧分支 `codex/input-swing` 上的 `20174aec717490398184aed8965deb4a14411eea`，其并发时间推进问题仍待修复。
- 停止时仅有一个未提交文件 `/Users/yupeng/projects/personal/pico-wuxia-arena-swing/app/src/main/java/com/example/wuxiaarena/core/input/SwingRecognizer.kt`，差异为 `43` 行新增、`6` 行删除，包含刀根/刀尖参数和旋转位移草稿。构造参数已改而测试调用尚未更新，草稿未编译或测试，迁回时须保留为未完成差异。
- 队列与计时水位方案仅完成分析，尚无修复代码。本轮无队列、主场景或构建配置的未提交修改。
- 安全迁回需主控先决定历史提交如何保留，再处理上述单文件草稿。旧副本当前保持停止状态。

### 真实键盘入口的只读诊断

已核对主仓库 `70ea9f9` 调用链 `mainApp → ObserveTracking → TrackingSession → PicoTrackingAdapter`。适配器为控制器注册了位姿 `DataListener`，当前应用源码尚无 `addControllerActionListener` 调用。`start()` 的返回值也尚未记录，Provider 多种支持状态会统一显示为 `PROVIDER_UNAVAILABLE`。这些入口和诊断信息需补齐，才能定位真实 W 的去向。

本机 Spatial SDK 6.1.9 缓存 `tracking-6.1.9/jars/classes.jar` 的 `javap` 核对确认公开方法存在，包含 `ControllerTrackingProvider.addControllerActionListener`、`removeControllerActionListener`、`ControllerActionListener.onControllerAction`，以及动作对象的左右手、`thumbstickValue.x/y`、`aButtonPressed`。官方文档说明回调在数据源线程执行，可以连续返回相同快照。SDK 接口存在，模拟器真实回调仍待主控取证。[手柄追踪官方说明](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_tracking_controller-tracking.md)

建议主控在现有模拟器与同一应用内按以下顺序执行。

1. 在现有 `TrackingSession` 持有具体 `ControllerTrackingProvider` 实例，通过已有构造参数传给 `PicoTrackingAdapter(controllers = provider)`。启动前注册一个稳定的 `ControllerTrackingProvider.ControllerActionListener`，生命周期结束时配对移除。回调只缓存最新动作和计数，消费线程按变化记录。该实例沿用现有启动与停止所有权。
2. 在现有启动位置记录 `DataProvider.StartResult`，并记录变化的 `provider.state`、`provider.supportState`。`PENDING` 需区分 Full Space、设备和权限条件。以 `STARTED/SUPPORTED`、动作回调计数和位姿回调计数分别定位通路。[DataProvider 官方说明](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_tracking_use-dataprovider.md)
3. 由主控确认模拟器处于控制器模式、Keyboard Mode 开启、前台场景取得焦点。真实按住再松开 W，观察 `action.left.thumbstickValue.x/y` 的变化及回零。再用 Space 核对 `action.right.aButtonPressed`。轴符号需实测，日志附动作计数与应用单调接收时间。Android `dispatchKeyEvent` 与控制器动作分别取证，设备侧注入仅作独立对照。若动作无变化，再结合支持状态、焦点和映射查原因。
4. 真实按压出现动作变化后，由主控指定入口，将按住/释放状态转成连续虚拟头手观察，经既有 `TrackingEventBuffer → TrackingProcessor` 进入共用输入和战斗处理。日志关联按键边沿、轨迹序号和判定消费，并记录释放回零及失焦清除状态。

官方资料确认模拟器支持键盘映射到控制器按钮，同时仍将键盘模拟手部姿态列为计划能力。因此控制器动作变化后仍需应用生成虚拟位姿，实际按键、轨迹和战斗消费需分别取证。[模拟器功能](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-toolkit_pico-emulator_what-is-pico-emulator.md) [模拟器与设备差异](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-toolkit_pico-emulator_understand-the-differences-between-the-pico-emulator-and-the-actual-device.md)

**本阶段结束，等待主控 review。** 只读核查已完成，具体运行诊断交由主控执行。真实键盘到虚拟轨迹与战斗的闭环尚无日志证明。本阶段未操作共享模拟器，未新增运行代码、测试或阈值。

主控已将暂停草稿保存在本仓库 Git stash `77237158a7c12c7651b1fc14d3785fd6df95acc3`，原型提交仍保留在 Git 分支，旧工作副本已移除。当前已派发唯一主仓库内的最小输入诊断，限定修改 `TrackingSession.kt`、`PicoTrackingAdapter.kt` 和 `LaunchActivity.kt`，由主控构建、安装并验证。
