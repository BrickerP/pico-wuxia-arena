# PICO Wuxia Arena

面向 PICO Space Pro／OS 6 的中式 PvE 刀术竞技场 Demo，采用 Kotlin + PICO Spatial SDK 6.1.9。体验围绕酒馆院落、单一刀客与一把刀展开，单次试炼连续三轮，共用180秒战斗时限。

本轮已补齐游戏链路的代码实现。主控已完成 `:app:assembleDebug --offline` 编译打包，按用户要求，本轮未运行自测、测试套件、模拟器操作或真机验收。运行完成度与手感仍需后续验收，详见[验收清单](docs/acceptance.md)。

## 游戏流程

准备就绪 → 开始 → 三秒倒计时 → 第一轮交战 → 清场与补给 → 下一轮倒计时 → 三轮胜利结算，或玩家生命归零／战斗时限耗尽后失败结算。结束后可重新挑战。

- 敌人逐轮为100、125、150生命，待机出招间隔逐轮缩短。AI会在待机阶段接近玩家，并保持近身距离。
- 玩家挥刀与前刺由真实刀段、移动速度和扫掠轨迹产生命中，区分头部与躯干，同一挥击去重。
- 举刀形成格挡，近期快速迎刀可产生弹反，侧移、后撤和下蹲用于避开攻击。持续守势消耗体力，体力不足会破防。
- 连击窗口影响伤害与得分。命中、防御和闪避积累气势，双手收刀蓄力后前推可释放破势。
- 同一“破势 / 处决”入口在敌人低血时自动进入处决分支。它沿已有倒地动作表现，当前没有单独制作新的配对处决动画。
- 玩家生命、体力、气势、轮次、倒计时、得分和结算进入HUD，最佳分数保存在本机。

## 输入与桌面预演

设备模式使用PICO头部及控制器观察。格挡、弹反、闪避、攻击和双手技能均由姿态产生结果。

桌面预演仅在debug模拟器条件下启用。键盘和五个预演动作按钮生成连续的虚拟头手轨迹，经过与设备模式相同的输入队列和战斗判定。按键与按钮不会直接扣血。

| 键位 | 预演动作 |
| --- | --- |
| 1 / J | 斩击 |
| 2、3 | 左斩、右斩 |
| 4 / K | 前刺 |
| 5 / V | 头上架刀 |
| 6 / B、7 / N | 左、右架刀 |
| 8 / Z、9 / X | 左、右闪避 |
| C | 下蹲 |
| G | 破势 / 处决，敌人低血时自动处决 |

WASD、Q/E及右键保留模拟器的移动、升降和转向控制。应用内暂停、显式恢复与重新开局走既有生命周期控制和输入队列。

## 角色与场景

角色由ov区域Tripo CLI通过 `tripo-v3.1` 生成，完成PBR贴图、低模烘焙及双足绑定。身体18,833三角面、78关节，Base Color为2K，Normal与Metallic-Roughness为1K。DAO为3,722三角面，刚性蒙皮到角色的R_Hand，与身体共用GPU骨架。

一个GLB打包idle、slash、hurt、fall四个原始动作。站立短受击使用fall开头片段，原hurt为坐姿负伤资源；出招和处决的播放段由现有状态驱动。角色米制、身高约1.78m、+Y向上、朝+Z。

场景复用已有酒馆、灯笼和石铺地，额外前院铺地由同一Paving模块派生。命中停顿、场景光脉冲、九个原始短音效和手柄触觉调用用于战斗反馈。效果与时序尚未实测。

## 本地构建

配置JDK 21、PICO SDK 6.1与Android SDK，并设置 `JAVA_HOME`、`PICO_HOME`、`ANDROID_HOME`。本机SDK路径留在未纳入版本控制的 `local.properties`。

```bash
./gradlew :app:assembleDebug
```

APK输出为 `app/build/outputs/apk/debug/app-debug.apk`。后续运行验收可使用已准备好的PICO模拟器或Space Pro，应用包名为 `com.example.wuxiaarena.p0d2f0182`，启动Activity为 `.platform.LaunchActivity`。

## 代码与资产入口

| 位置 | 职责 |
| --- | --- |
| `Main.kt` | Full Stage注册、HUD、音效／震动接线、最佳分数存储 |
| `runtime/ArenaSession.kt` | 三轮流程、资源、时序切段、伤害、胜负和呈现出口 |
| `core/combat/PlayerCombatResolver.kt` | 同源姿态的挥击接触、架刀、弹反、闪避和双手蓄推识别 |
| `core/combat/EnemyCombatStateMachine.kt` | 敌招阶段、护身、受击、暂停与重开 |
| `input/DesktopCombatInput.kt` | 桌面动作轨迹，供同一战斗入口消费 |
| `content/HomeStage.kt`、`EnemyAnimator.kt` | 角色位置、四动作、HUD锚点、光脉冲及场景生命周期 |
| `ArtSource/tripo-warrior/` | 角色、动作来源、整理脚本和绑定信息 |
| `ArtSource/audio/` | 原始音效的可复建生成脚本与说明 |
| `ArtSource/tavern/` | 酒馆与复用前院铺地来源 |

API凭据由CLI的标准本机配置管理。仓库排除本地凭据上下文、宿主诊断截图和高分辨率源文件。

## 交付与验收

- [当前验收清单](docs/acceptance.md)
- [战斗交接](docs/agents/01-combat.md)
- [输入交接](docs/agents/02-input.md)
- [美术交接](docs/agents/03-art.md)
- [验证交接](docs/agents/04-benchmark-qa.md)

`docs/media/arena-preview.png` 是上一轮静态展示基线图。本轮功能以当前代码和主控编译结果交付，新的运行画面、设备手感和性能尚待后续验收。
