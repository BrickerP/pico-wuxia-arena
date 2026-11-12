# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

## 唯一开发与验收路径

**原生源码 → APK → PICO Emulator → Space Pro。** 模拟器的真实头手观察和终端设备共用战斗判定。HTML、Three.js、浏览器试玩和网页光照实验已停止，不作为前置步骤或验收入口；已有 prototype 文件仅保留历史，不继续维护。

## 当前交付

| 内容 | 状态与边界 |
| --- | --- |
| 本轮原生组合 | UI精简、取消整身Unlit白闪、局部接触灯、清理无caller特效预载；APK `ca26f4a9837437b05f1d8a3a3b0c0dbb770624656af2eaba148c60dafc605c5c`，242,709,621字节 |
| 实际主流程 | PICO Emulator真实输入完成失败→重新挑战→三轮角色换入/交战→胜利，结算967分、剩余40生命；SOFT/HARD/GUARDED/PLAYER_HIT与三次fall均有对应日志 |
| 实际画面 | [52秒连续交战片](ArtSource/refinement/presentation/native-ui-impact-three-rounds-2026-11-13.mp4)、[交战状态](ArtSource/refinement/presentation/native-ui-impact-contact-2026-11-13.png)、[胜利结算](ArtSource/refinement/presentation/native-ui-impact-victory-2026-11-13.png)、[版本与边界](ArtSource/refinement/presentation/native-ui-impact-2026-11-13.json) |
| 检查 | 构建、安装启动、336项单元测试通过；UI样式0错误/0警告。通用模板架构检查仍报现有game包布局/ViewModel差异，未宣称整个workflow clean |
| 最新下载 | [native-ui-impact-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-ui-impact-2026-11-13)，固定源码a22a216，含APK/52秒实录/两张原生图/manifest，五附件大小与SHA已核对 |
| 当前品质 | **成品Demo未完成。** 握柄长指、近景肤色/刀面、衣服/发型、宽灰刀轨、近身NPC遮挡终局牌仍有问题；玩家PARRY/HMD闪避/技能处决、暂停恢复与Space Pro实测未完成 |

336项是当前机制测试集：新增局部灯测试，删除随旧白闪/死入口一并退役的测试。完整三轮通过是模拟器流程证据，不等于视觉、手感或终端性能已达标。原生镜像窗口约57fps录制也不代表PICO渲染帧率。

[验收清单](docs/acceptance.md)区分代码、原生运行、视觉品质与终端实测。[分工与审核](docs/agents/README.md)列候选状态；整立面、上劈v9、近场光仍未进入本包。HTML/Web路线保持停止。

## 构建与模拟器

先读[PICO CLI开发手册](docs/agent-start.md)，沿当前安装工具完成环境检查。使用JDK 21、PICO SDK 6.1和Android SDK；本机路径留在未提交的local.properties。

```bash
./gradlew :app:assembleDebug :app:testDebugUnitTest
pico-cli app install app/build/outputs/apk/debug/app-debug.apk --device <device-id> --replace
pico-cli app launch com.example.wuxiaarena.p0d2f0182 --activity .platform.LaunchActivity --device <device-id>
```

APK为`app/build/outputs/apk/debug/app-debug.apk`。选定PICO Emulator后所有设备命令使用同一个device-id。Root统一共享构建、正式资产、安装、截图、录制与发布。

模拟器使用 **Right Controller Mode**，启用 **Controller Button Mode**，关闭 **Keyboard Mode** 文本模式。Shift+W/A/S/D/Q/E移动虚拟手柄，鼠标改变朝向与空间射线；攻击、格挡、弹反、闪避和技能经动作判定，按钮用于实际UI。没有Activity按键动作宏或HMD派生假手路径。

## 既有体验与制作范围

准备→三秒倒计时→三轮攻防与补给→胜利/失败→重新挑战。已接入生命、体力、气势、连击、得分与最佳成绩；挥刀/前刺、架刀/弹反、身法、蓄力破势与低血处决仍须按验收清单逐项完成真实运行证明。

参考Blade & Sorcery、荣耀战魂的空间攻防，影之刃零、鬼武者、只狼的蓄势/接触/收势，黑神话悟空的成年写实骨相、交领束带、刀具、木作与湿石材。骑马与砍杀、天国拯救仅提供可信尺度和空间感参考，本Demo不扩开放世界。

正式三角色、刀、双手与唯一courtyard位于`app/src/main/assets/models/`。每名敌人78骨、10clip，KTX2/mips；待机、六步步法、三攻击与HIT渲染/接触共享采样。当前binding为`1b3e031d6f0510ba9d955cd0eee7b34fbc03dcf256cd23958d252873e9221fe2`，base为`ac7dfbc…`，正式庭院为`9b2598…`。新立面、精细上劈与近场光仍为待合入候选；本轮原生UI与局部接触反馈已合入。

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
