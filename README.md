# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

**[下载「身位判定」APK](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-head-motion-2026-11-23/arena.apk)** · [80 秒三场通关与重开](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-head-motion-2026-11-23/three-duels-victory.mp4) · [713 分结算画面](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-head-motion-2026-11-23/victory.png)

安装后点「开始试炼」。首敌上举时横刀护额，握刀手收近额侧，等来刀落下；接住后撤手，将刀降到肩线，从空出的一侧还击。第二场青衫侧斩走肋部，按提示降低握刀手，不要只护头。面对第三名玄甲刀客，看他何时举刀露隙。原地左右摆腕而不送手或稳架，只会轻擦。

三名对手已分别调整右手握柄。落败时对手收刀后退，结果面板保留系统射线用于再挑战。模拟器虚拟手初始位置见下方操作说明。PICO Emulator 已通过同一 APK 的三场通关和胜后重开。Space Pro 头显上的手感、触觉和持续帧时待实机验证。[按版本查看证据](docs/acceptance.md)。

## 两条独立工作线

**参赛原生Demo：源码 → APK → PICO Emulator → Space Pro。** 本次Demo采用同一SDK头手观察与战斗判定，原生任务不能用HTML、Three.js或浏览器试玩替代开发和设备验收。

**独立探索原型：[prototype/web-v0.18](prototype/web-v0.18/README.md)。** 允许`web/**`独立PR继续探索、美术和敌群试验；现有v0.34–v0.37成果及未来Web版本有明确归属。它们不计为原生完成度，也不自动扩进当前短PVE Demo。选中的资产/动作/玩法须经过原生移植和验证。

两线保留各自产物，不互相覆盖；Root统一审核。详见[协作边界](docs/collaboration-boundaries.md)。

## 当前交付

| 内容 | 当前事实 |
| --- | --- |
| 前台交战帧时 | 同机首敌上劈、稳架与还击的前台五秒，应用空间帧间隔 P95 从 83.98 ms 降到 56.72 ms。整局仍有可见长帧。 [数据](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-head-motion-2026-11-23/opening-frame-intervals.csv) |
| 玩家手部 | 在准备界面切换惯用手。[左手持刀](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-duel-result-2026-11-23/left-grip-ready.png) · [右手持刀、左掌张开](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-duel-result-2026-11-23/ready-natural-hands.png)。当前包沿用同一双手资产与握点。斜向收刀时个别角度仍可看见袖管的平截面。 |
| 模拟器实战 | 713 分、余血 20、击败 3/3。青衫战确认三次闪避，玄甲战确认一次弹反，胜后同进程重新开局。[本包完整实录](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-head-motion-2026-11-23/three-duels-victory.mp4) |
| 版本对照 | [流程复现版](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-2026-11-18)保留了左右扫通关的反例；[握姿与守势](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-grip-2026-11-18)改了双手；[玄甲反击窗口](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-counter-window-2026-11-18)扩大上举时的命中机会。 |
| 动作 | 三角色共享自然守势/呼吸；修正 RIGHT 空手回收及 veteran LEFT 末端约束；726 个声明范围内有限姿态未检出被测非邻接核心/Steel交叉。这不覆盖全衣料、连续时间或最终GPU蒙皮 |
| 拼刀 | 解析卸力优先。证不出来、再次接触或连续不可证查询改为一次最长 220ms 的强制回守，然后把刀交还跟踪。同一次重叠不连打出伤。玩家手不吃敌人的强制位移 |
| 玩家刀与当前验收 | 正式刀面已派生七个半径 6 mm 的接触体，5533 个 Steel 顶点的最大外侧距离为 0.416 mm。当前验证真实交手后的收势、胜负与重开，见[验收清单](docs/acceptance.md)。 |
| 敌人动作 | [持刀右臂左斩](ArtSource/refinement/presentation/duel-rightcut-wrist-2026-11-18.jpg)与[守势前后对照](ArtSource/refinement/presentation/mounted-guard-wrist-2026-11-18.jpg)。刀的接触轨迹从同版模型重新导出。 |
| 上一版公开下载 | [试炼战绩](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-result-2026-11-23)，源码 `ce2d7c2`，APK SHA256 `1298c636…`。 |

通关录像保留设备原始视频流。受击触感和音画同步需在头显中体验。各发布包的画面与帧时见[验收清单](docs/acceptance.md)，协作范围见[当前目标](docs/agents/README.md)。

## 构建与模拟器

先读[PICO CLI开发手册](docs/agent-start.md)，沿当前安装工具完成环境检查。使用JDK 21、PICO SDK 6.1和Android SDK；本机路径留在未提交的local.properties。

```bash
./gradlew :app:assembleDebug :app:testDebugUnitTest
pico-cli app install app/build/outputs/apk/debug/app-debug.apk --device <device-id>
pico-cli app launch com.example.wuxiaarena.p0d2f0182 --activity .platform.LaunchActivity --device <device-id>
```

APK为`app/build/outputs/apk/debug/app-debug.apk`。选定PICO Emulator后所有设备命令使用同一个device-id。Root统一共享构建、正式资产、安装、截图、录制与发布。

模拟器使用 **Right Controller Mode**，启用 **Controller Button Mode**，关闭 **Keyboard Mode** 文本模式。Shift+W/A/S/D/Q/E移动虚拟手柄，鼠标改变朝向与空间射线；攻击、格挡、弹反、闪避和技能经动作判定，按钮用于实际UI。没有Activity按键动作宏或HMD派生假手路径。

要在模拟器里侧身，保持手柄模式，在场景视口按住 Shift 并用鼠标左键横拖，松开后再用鼠标转动握刀手。在视口滚动鼠标滚轮可前后移动视点。在本机当前窗口，向右拖 70 像素时，SDK 记录头部向左移动约 21 厘米，握刀手仍在原位置。闪避是否成功由实际头部轨迹与来招相交情况决定。

要在模拟器里侧身躲刀，开局后关闭 **Controller Button Mode**，用不带 Shift 的 A/D 移动头部；带 Shift 的 A/D 移动的是虚拟手。需要点结算按钮时重新启用 Controller Button Mode。头显上直接移动身体。

刚开启手柄时，如果手背和刀挡住视野，先不要开始试炼。点主视口的空白处，朝正前方，用 **Shift+D** 把右手移到右侧，**Shift+Q** 下移，**Shift+W** 前移，直到握柄在右下方、能完整看清对手。本轮模拟器实测右手相对头部向右 28 cm、向下 31 cm、向前 45 cm，头到握点约 61 cm；虚拟右手和刀柄的位置均与 SDK 握点一致。这只用于复现同一视角，不是游戏或真机的持刀限制。

## 既有体验与制作范围

从准备界面进入三秒倒计时，依次挑战三名对手，结算后可重新挑战。生命、体力、气势、连击和得分随战斗更新。本包录到了格挡、还击、闪避、弹反与通关。双手蓄力破势和低血处决未在这局演示。

参考Blade & Sorcery、荣耀战魂的空间攻防，影之刃零、鬼武者、只狼的蓄势/接触/收势，黑神话悟空的成年写实骨相、交领束带、刀具、木作与湿石材。骑马与砍杀、天国拯救仅提供可信尺度和空间感参考，本Demo不扩开放世界。

正式三角色、刀、双手与唯一courtyard位于`app/src/main/assets/models/`。每名敌人78骨、10clip，KTX2/mips；待机、六步步法、三攻击与HIT渲染/接触共享采样。当前 binding 为 `3ed4cb55900c606877c29204ffb347cece9ac929c17bbe8b7519dfbc8eb48a7c`，base 为 `58741ce7…`、indigo 为 `fe3c330b…`、veteran 为 `d5898b17…`。OVERHEAD为211键/120Hz；veteran LEFT准备曲线130键，其余左右各106键，时序不变。正式producer验证逐clip精确时间网格与末端约束；生成数据来自同一份模型。

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
