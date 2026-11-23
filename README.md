# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

**[下载「握刀与退场」APK](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-after-duel-2026-11-23/arena.apk)** · [青衫握姿](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-after-duel-2026-11-23/indigo-grip.jpg) · [玄甲握姿](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-after-duel-2026-11-23/veteran-grip.jpg) · [上版三场实战](https://github.com/BrickerP/pico-wuxia-arena/releases/download/native-ready-trail-2026-11-23/three-duels-boss-9hp.mp4)

安装后点「开始试炼」。首敌上举时横刀护额，握刀手收近额侧，等来刀落下；接住后撤手，将刀降到肩线，从空出的一侧还击。第二场青衫侧斩走肋部，按提示降低握刀手，不要只护头。面对第三名玄甲刀客，看他何时举刀露隙。原地左右摆腕而不送手或稳架，只会轻擦。

三名对手已分别调整右手握柄。落败时对手收刀后退，结果面板保留系统射线用于再挑战。模拟器虚拟手初始位置见下方操作说明。三场胜局与 Space Pro 实机手感仍待验证。[按版本查看证据](docs/acceptance.md)。

## 两条独立工作线

**参赛原生Demo：源码 → APK → PICO Emulator → Space Pro。** 本次Demo采用同一SDK头手观察与战斗判定，原生任务不能用HTML、Three.js或浏览器试玩替代开发和设备验收。

**独立探索原型：[prototype/web-v0.18](prototype/web-v0.18/README.md)。** 允许`web/**`独立PR继续探索、美术和敌群试验；现有v0.34–v0.37成果及未来Web版本有明确归属。它们不计为原生完成度，也不自动扩进当前短PVE Demo。选中的资产/动作/玩法须经过原生移植和验证。

两线保留各自产物，不互相覆盖；Root统一审核。详见[协作边界](docs/collaboration-boundaries.md)。

## 当前交付

| 内容 | 当前事实 |
| --- | --- |
| 玩家手部 | [上排右手、下排左手的握姿对照](ArtSource/refinement/presentation/native-player-grip-pose-comparison-2026-11-18.jpg)。左右手均做过原生持刀检查；手感另验。 |
| 已公开组合画面 | [7abefa5准备态](ArtSource/refinement/presentation/native-contact-polish-ready-2026-11-17.png)、[45秒交战](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.mp4)、[57f7版本与边界](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.json) |
| 版本对照 | [流程复现版](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-2026-11-18)保留了左右扫通关的反例；[握姿与守势](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-grip-2026-11-18)改了双手；[玄甲反击窗口](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-counter-window-2026-11-18)扩大上举时的命中机会。 |
| 动作 | 三角色共享自然守势/呼吸；修正 RIGHT 空手回收及 veteran LEFT 末端约束；726 个声明范围内有限姿态未检出被测非邻接核心/Steel交叉。这不覆盖全衣料、连续时间或最终GPU蒙皮 |
| 拼刀 | 解析卸力优先。证不出来、再次接触或连续不可证查询改为一次最长 220ms 的强制回守，然后把刀交还跟踪。同一次重叠不连打出伤。玩家手不吃敌人的强制位移 |
| 玩家刀与当前验收 | 正式刀面已派生七个半径 6 mm 的接触体，5533 个 Steel 顶点的最大外侧距离为 0.416 mm。当前验证真实交手后的收势、胜负与重开，见[验收清单](docs/acceptance.md)。 |
| 敌人动作 | [持刀右臂左斩](ArtSource/refinement/presentation/duel-rightcut-wrist-2026-11-18.jpg)与[守势前后对照](ArtSource/refinement/presentation/mounted-guard-wrist-2026-11-18.jpg)。刀的接触轨迹从同版模型重新导出。 |
| 上一版公开下载 | [11 月 17 日开发预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-contact-polish-2026-11-17)，固定源码 `7abefa5` / APK `57f7cb12…`。 |

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

要在模拟器里侧身躲刀，开局后关闭 **Controller Button Mode**，用不带 Shift 的 A/D 移动头部；带 Shift 的 A/D 移动的是虚拟手。需要点结算按钮时重新启用 Controller Button Mode。头显上直接移动身体。

刚开启手柄时，如果手背和刀挡住视野，先不要开始试炼。点主视口的空白处，朝正前方，用 **Shift+D** 把右手移到右侧，**Shift+Q** 下移，**Shift+W** 前移，直到握柄在右下方、能完整看清对手。本轮模拟器实测右手相对头部向右 28 cm、向下 31 cm、向前 45 cm，头到握点约 61 cm；虚拟右手和刀柄的位置均与 SDK 握点一致。这只用于复现同一视角，不是游戏或真机的持刀限制。

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
