# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

## 两条独立工作线

**参赛原生Demo：源码 → APK → PICO Emulator → Space Pro。** 本次Demo采用同一SDK头手观察与战斗判定，原生任务不能用HTML、Three.js或浏览器试玩替代开发和设备验收。

**独立探索原型：[prototype/web-v0.18](prototype/web-v0.18/README.md)。** 允许`web/**`独立PR继续探索、美术和敌群试验；现有v0.34–v0.37成果及未来Web版本有明确归属。它们不计为原生完成度，也不自动扩进当前短PVE Demo。选中的资产/动作/玩法须经过原生移植和验证。

两线保留各自产物，不互相覆盖；Root统一审核。详见[协作边界](docs/collaboration-boundaries.md)。

**当前版本未通过可玩性评审。** 11 月 18 日的原生包能通关和重开，但连续来回横扫就可击败三名对手，手腕与手指形变不自然，交战明显卡顿。[流程复现包与录像](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-duel-2026-11-18)仅保留作修复前对照。参赛质量和 Space Pro 体验均未验收，见[验收清单](docs/acceptance.md)。

## 当前交付

| 内容 | 当前事实 |
| --- | --- |
| 手部历史对照 | [11 月 17 日右持刀](ArtSource/refinement/presentation/native-hand-joints-right-2026-11-17.png)、[对应版本与未验收项](ArtSource/refinement/presentation/native-hand-joints-2026-11-17.json)。本轮也只验证右持。 |
| 已公开组合画面 | [7abefa5准备态](ArtSource/refinement/presentation/native-contact-polish-ready-2026-11-17.png)、[45秒交战](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.mp4)、[57f7版本与边界](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.json) |
| 本轮 APK | 原生代码 `1244f83`；234289759 B，设备安装包 SHA256 `dcafb901aa8e8f61fdfe25fd0cc4e5bfc6644ec2ab58aebefce605c2c44a1527`。473 项单测、6 项刀面几何检查通过。 |
| 动作 | 三角色共享自然守势/呼吸；修正 RIGHT 空手回收及 veteran LEFT 末端约束；726 个声明范围内有限姿态未检出被测非邻接核心/Steel交叉。这不覆盖全衣料、连续时间或最终GPU蒙皮 |
| 拼刀 | 解析卸力优先。证不出来、再次接触或连续不可证查询改为一次最长 220ms 的强制回守，然后把刀交还跟踪。同一次重叠不连打出伤。玩家手不吃敌人的强制位移 |
| 玩家刀与当前验收 | 正式刀面已派生七个半径 6 mm 的接触体，5533 个 Steel 顶点的最大外侧距离为 0.416 mm。当前验证真实交手后的收势、胜负与重开，见[验收清单](docs/acceptance.md)。 |
| 手与场景 | Right `199c228c…` / Left `0295c147…`，各6222三角；闭握局部关节弧面改善，整体手品质未过。庭院 `c7f2e2b2…`；Tripo厚甲和场景IBL仍未装入本APK |
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
