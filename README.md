# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

## 两条独立工作线

**参赛原生Demo：源码 → APK → PICO Emulator → Space Pro。** 本次Demo采用同一SDK头手观察与战斗判定，原生任务不能用HTML、Three.js或浏览器试玩替代开发和设备验收。

**独立探索原型：[prototype/web-v0.18](prototype/web-v0.18/README.md)。** 允许`web/**`独立PR继续探索、美术和敌群试验；现有v0.34–v0.37成果及未来Web版本有明确归属。它们不计为原生完成度，也不自动扩进当前短PVE Demo。选中的资产/动作/玩法须经过原生移植和验证。

两线保留各自产物，不互相覆盖；Root统一审核。详见[协作边界](docs/collaboration-boundaries.md)。

**成品 Demo 未完成。** 当前只有一道门，写在 [docs/agents/README.md](docs/agents/README.md)：先让钢交叠在 220ms 内回守，再让刀的显示和判定共用一个网格形状，然后用同一个 APK 打完三轮并重开。旧包录像不能代替这一包。

## 当前交付

| 内容 | 当前事实 |
| --- | --- |
| 最新main画面 | [新手部原生右持](ArtSource/refinement/presentation/native-hand-joints-right-2026-11-17.png)、[精确版本与未验收项](ArtSource/refinement/presentation/native-hand-joints-2026-11-17.json)。当前Left尚未端内验收 |
| 已公开组合画面 | [7abefa5准备态](ArtSource/refinement/presentation/native-contact-polish-ready-2026-11-17.png)、[45秒交战](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.mp4)、[57f7版本与边界](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.json) |
| 最新main APK | SHA256 `c5c28446ea443d14a3ce7d96fd4abb5f48aa5a81666f5f9f3c60a881a33cb9b6`，221191753 B；设备安装包SHA及19个GLB核对，467测试，0失败/错误/跳过 |
| 动作 | 三角色共享自然守势/呼吸；修正 RIGHT 空手回收及 veteran LEFT 末端约束；726 个声明范围内有限姿态未检出被测非邻接核心/Steel交叉。这不覆盖全衣料、连续时间或最终GPU蒙皮 |
| 拼刀 | 解析卸力优先。证不出来、再次接触或连续不可证查询改为一次最长 220ms 的强制回守，然后把刀交还跟踪。同一次重叠不连打出伤。玩家手不吃敌人的强制位移 |
| 当前阻断 | **刀的形状仍是 12mm 单胶囊**，静态刀面局部漏覆盖约 45mm。下一提交只做网格分段，并让显示、CCD、恢复读它。手部、衣片、Tripo、IBL 暂停 |
| 手与场景 | Right `199c228c…` / Left `0295c147…`，各6222三角；闭握局部关节弧面改善，整体手品质未过。庭院 `c7f2e2b2…`；Tripo厚甲和场景IBL仍未装入本APK |
| 当前公开下载 | [有限拼刀卸力开发预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-contact-polish-2026-11-17)固定源码 `7abefa5` / APK `57f7cb12…`，5附件SHA/大小/状态已核；不含最新199c/0295手与技能误触修复 |

录像保持原始时间流和帧数。主机窗口帧率不是 PICO 渲染性能，无声录像不能判断卡肉。弹反、头闪、技能、处决和 Space Pro 排在三轮通关之后。[当前门](docs/acceptance.md)只认正在构建的这一包。[目标](docs/agents/README.md)是 Codex 的唯一派工单。

## 构建与模拟器

先读[PICO CLI开发手册](docs/agent-start.md)，沿当前安装工具完成环境检查。使用JDK 21、PICO SDK 6.1和Android SDK；本机路径留在未提交的local.properties。

```bash
./gradlew :app:assembleDebug :app:testDebugUnitTest
pico-cli app install app/build/outputs/apk/debug/app-debug.apk --device <device-id>
pico-cli app launch com.example.wuxiaarena.p0d2f0182 --activity .platform.LaunchActivity --device <device-id>
```

APK为`app/build/outputs/apk/debug/app-debug.apk`。选定PICO Emulator后所有设备命令使用同一个device-id。Root统一共享构建、正式资产、安装、截图、录制与发布。

模拟器使用 **Right Controller Mode**，启用 **Controller Button Mode**，关闭 **Keyboard Mode** 文本模式。Shift+W/A/S/D/Q/E移动虚拟手柄，鼠标改变朝向与空间射线；攻击、格挡、弹反、闪避和技能经动作判定，按钮用于实际UI。没有Activity按键动作宏或HMD派生假手路径。

## 既有体验与制作范围

准备→三秒倒计时→三轮攻防与补给→胜利/失败→重新挑战。已接入生命、体力、气势、连击、得分与最佳成绩；挥刀/前刺、架刀/弹反、身法、蓄力破势与低血处决仍须按验收清单逐项完成真实运行证明。

参考Blade & Sorcery、荣耀战魂的空间攻防，影之刃零、鬼武者、只狼的蓄势/接触/收势，黑神话悟空的成年写实骨相、交领束带、刀具、木作与湿石材。骑马与砍杀、天国拯救仅提供可信尺度和空间感参考，本Demo不扩开放世界。

正式三角色、刀、双手与唯一courtyard位于`app/src/main/assets/models/`。每名敌人78骨、10clip，KTX2/mips；待机、六步步法、三攻击与HIT渲染/接触共享采样。当前binding为`51807084b2d6abd2cc322e2225d6afa42f25db0eae48c57c4d85dbf6193abd33`，base为`871b5521…`、indigo为`0c148e95…`、veteran为`9a392e2e…`。OVERHEAD为211键/120Hz；veteran LEFT准备曲线130键，其余左右各106键，时序不变。正式producer验证逐clip精确时间网格与末端约束；生成数据来自同一份模型。

## 工程入口

| 入口 | 职责 |
| --- | --- |
| LaunchActivity → Main.kt → HomeStage.kt | 原生Full Stage、空间UI、资产与场景生命周期 |
| runtime/ArenaSession.kt | 三轮流程、时钟、资源、胜负与呈现事件 |
| core/combat/PlayerCombatResolver.kt | 同一套头手/刀轨攻防判定 |
| input/PicoTrackingAdapter.kt、runtime/TrackingSession.kt | SDK原生观察、就绪安全门与生命周期 |
| content/EnemyAnimator.kt、runtime/AttackBankProfiles.kt | 同源骨骼/刀段/步态/HIT采样 |
| content/PlayerHands.kt | 原生第一人称手部模型、抓握与追踪呈现 |
| content/CombatEffects.kt、ContactParticleEmitter.kt、PlayerBladeTrail.kt | 原生接触反馈、粒子、刀光 |
| ArtSource/tripo-warrior/、ArtSource/refinement/ | 已发布资产来源与明确标记的制作候选 |

唯一仓库为本项目；不复制仓库，不修改pico或个人网站仓库。API凭据仅留CLI本机配置，禁止进入源码、交接或发布附件。
