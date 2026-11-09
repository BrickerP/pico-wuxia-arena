# PICO Wuxia Arena

开发基线，完整PVE验收仍有阻塞。完成与未完成项见[验收清单](docs/acceptance.md)。

面向 PICO Space Pro／OS 6 的中式 PvE 刀术竞技场 Demo。场景采用酒馆、灯笼与石面院落，围绕一名刀客、一把刀和短试炼迭代。

## 技术与入口

- Kotlin、PICO Spatial SDK 6.1.9、Gradle 8.13、JDK 21。
- `Main.kt` 注册 Full Stage，`HomeStage.kt` 管理场景、模型与玩家刀。
- `TrackingSession.kt` 维护追踪生命周期和同一输入队列，`ArenaSession.kt` 协调既有战斗状态及呈现。
- `core/combat/EnemyCombatStateMachine.kt` 管理出招阶段、生命、护身、暂停和重开规则。

## 本地构建与模拟器

配置 JDK 21、PICO SDK 6.1 与 Android SDK，并设置对应的 `JAVA_HOME`、`PICO_HOME`、`ANDROID_HOME`。SDK 的本机路径配置放在未纳入版本控制的 `local.properties`。

```bash
./gradlew :app:testDebugUnitTest :app:assembleDebug
pico-cli device list --format json
pico-cli app install app/build/outputs/apk/debug/app-debug.apk --replace --device emulator-5554
pico-cli app launch com.example.wuxiaarena.p0d2f0182 --activity .platform.LaunchActivity --device emulator-5554
```

使用实际设备编号替换 `emulator-5554`。APK 位于 `app/build/outputs/apk/debug/app-debug.apk`。

桌面预演使用模拟器的相机控制，保持眼手／相机模式并关闭手柄 Keyboard Mode。WASD 移动，Q/E 升降，右键转向。当前桌面双手由 HMD 派生并标记为合成预演数据。设备输入入口使用实际头部与控制器观察。

## 角色与动作

角色通过 ov 区域的 Tripo CLI 生成，文生模型为 `tripo-v3.1`，经 PBR 贴图、低模烘焙及双足绑定。运行身体为18,833三角面，78关节，Base Color为2K，Normal及Metallic-Roughness为1K。刀具为3,722三角面。

原始低模与动作源、整理脚本及来源信息位于 `ArtSource/tripo-warrior/`。Blender 整理限于米制、轴向、原点、握点及 dao 对齐。角色运行方向为+Z，+Y向上，身高约1.78m，刀具通过实际右手骨骼挂接。

本机凭据由 Tripo CLI 的标准用户配置管理。仓库保存任务来源和可重建资产，宿主诊断截图与高分辨率源文件留在本地。

## 当前开发范围

当前优先接通既有试炼能力的 UI、状态反馈、模型与动作。位姿到实际命中／防御结果的产生者属于后续范围，当前状态机已经提供结果消费入口。实际 Space Pro 手感、舒适度与性能验收需要真机。

四份任务文档维护当前分工、review与交付。

- [战斗与动作呈现](docs/agents/01-combat.md)
- [输入与控制](docs/agents/02-input.md)
- [角色与美术](docs/agents/03-art.md)
- [验收范围](docs/agents/04-benchmark-qa.md)
