# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

## 两条独立工作线

**参赛原生Demo：源码 → APK → PICO Emulator → Space Pro。** 本次Demo采用同一SDK头手观察与战斗判定，原生任务不能用HTML、Three.js或浏览器试玩替代开发和设备验收。

**独立探索原型：[prototype/web-v0.18](prototype/web-v0.18/README.md)。** 允许`web/**`独立PR继续探索、美术和敌群试验；现有v0.34–v0.37成果及未来Web版本有明确归属。它们不计为原生完成度，也不自动扩进当前短PVE Demo。选中的资产/动作/玩法须经过原生移植和验证。

两线保留各自产物，不互相覆盖；Root统一审核。详见[协作边界](docs/collaboration-boundaries.md)。

## 当前交付

| 内容 | 状态与边界 |
| --- | --- |
| 当前开发源码 | 真实刀刀连续接触、手刀共用最终Grip、持续非穿透及同源卸力，中央入口木作换为96c554；构建与417项单测通过，已安装启动；本次虚拟手柄callback仍为0，交互与反手问题未验收 |
| 当前开发画面 | [PICO Full Stage实图](ArtSource/refinement/presentation/native-blade-contact-stage-2026-11-13.png)与[版本/边界](ArtSource/refinement/presentation/native-blade-contact-stage-2026-11-13.json)：新庭院及首名对手显示，停在等待手柄；不是拼刀成功证据 |
| 上一公开组合 | 精细上劈v9、右手闭握v2、九窗庭院、近场光、薄刀轨及结算面板；APK `1c41cfc30fa79dd391e9c6af329cdfcf8b8d6ad7401465b9f16b90d0016d7b46`，242,706,266字节 |
| 公开v9主流程 | PICO Emulator真实SDK输入完成开局、三轮角色轮换、胜利895分／余60生命，再实际点击再挑战回到准备态；8次SOFT_HIT、6次敌方GUARDED_HIT、4次PLAYER_HIT及三次fall有对应日志；不证明新刀刀接触实现 |
| 公开v9画面 | [52秒连续交战片](ArtSource/refinement/presentation/native-visual-v9-three-rounds-2026-11-13.mp4)、[重试短片](ArtSource/refinement/presentation/native-visual-v9-retry-2026-11-13.mp4)、[交战状态](ArtSource/refinement/presentation/native-visual-v9-combat-2026-11-13.png)、[胜利](ArtSource/refinement/presentation/native-visual-v9-victory-2026-11-13.png)、[版本与边界](ArtSource/refinement/presentation/native-visual-v9-2026-11-13.json) |
| 公开v9检查 | 构建、安装启动、349项单元测试通过；7个打包模型SHA匹配。空ECS附件AABB标记UNOBSERVED，不伪报数值PASS；实际纸牌与点击已验证 |
| 最新下载 | [native-visual-v9-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-visual-v9-2026-11-13)，固定源码bfaf53b，8附件大小与SHA均核对 |
| 当前品质 | **成品Demo未完成。** 衣料／发型、近景肤色／刀面反光、腕口／掌背、刀轨与接触反馈可读性仍需打磨；玩家PARRY/HMD闪避/技能处决、部分生命周期和Space Pro实测未完成 |

模拟器主流程证据不等于视觉、手感或终端性能达标。录像保持原始时间流，未插帧，主机约56.5fps也不代表PICO渲染帧率；本次录像未录声音。[验收清单](docs/acceptance.md)与[分工审核](docs/agents/README.md)列当前实物、审核边界和续派。上一已发布UI节点为ca26f4a9／a22a216，保留独立证据。

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

正式三角色、刀、双手与唯一courtyard位于`app/src/main/assets/models/`。每名敌人78骨、10clip，KTX2/mips；待机、六步步法、三攻击与HIT渲染/接触共享采样。当前binding为`365578d497f3a592e08cbe158f90777fe326211f8d9593bab85ff807c0ac07ac`，base为`6ca12659…`，开发庭院为`96c554cc…`（公开v9为64da），右手为`3a1be1dd…`。OVERHEAD为211键／120Hz，左右攻击各106键；正式producer按每clip声明的精确时间网格验证。场景静态合批2f9a8774仅保留为未采用A/B备选，不凭提交估算宣称硬件收益。

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
