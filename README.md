# PICO Wuxia Arena

面向 **PICO Space Pro / OS 6** 的中式写实短 PVE 刀术竞技场。采用 **Kotlin + PICO Spatial SDK 6.1.9**，在 **Full Stage** 运行。范围是一座雨夜酒馆院落、一把刀、三名顺序对手；手感优先，其次是人物与场景观感。

## 两条独立工作线

**参赛原生Demo：源码 → APK → PICO Emulator → Space Pro。** 本次Demo采用同一SDK头手观察与战斗判定，原生任务不能用HTML、Three.js或浏览器试玩替代开发和设备验收。

**独立探索原型：[prototype/web-v0.18](prototype/web-v0.18/README.md)。** 允许`web/**`独立PR继续探索、美术和敌群试验；现有v0.34–v0.37成果及未来Web版本有明确归属。它们不计为原生完成度，也不自动扩进当前短PVE Demo。选中的资产/动作/玩法须经过原生移植和验证。

两线保留各自产物，不互相覆盖；Root统一审核。详见[协作边界](docs/collaboration-boundaries.md)。

当前开发组合已接入左右攻击净空修正、有限拼刀卸力与新灯笼庭院，binding `51807084…`。**成品 Demo 未完成。** 460 项单测与 APK 构建通过；真实模拟器输入已打倒前两敌并进入第三轮，未完成本版本三轮胜利验收。

## 当前交付

| 内容 | 当前事实 |
| --- | --- |
| 原生画面与录像 | [Full Stage准备态](ArtSource/refinement/presentation/native-contact-polish-ready-2026-11-17.png)、[45秒实际交战](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.mp4)、[版本、源文件身份与边界](ArtSource/refinement/presentation/native-contact-polish-2026-11-17.json) |
| 开发 APK | SHA256 `57f7cb12286aa9b466bb75c8e53d87b8c31ee6adc887186f6b1adc2e26e9d8e2`，220863361 B；19 个 GLB 装包身份一致；460 测试，0失败/错误/跳过 |
| 动作 | 三角色共享自然守势/呼吸；修正 RIGHT 空手回收及 veteran LEFT 末端约束；726 个声明范围内有限姿态未检出被测非邻接核心/Steel交叉。这不覆盖全衣料、连续时间或最终GPU蒙皮 |
| 拼刀 | 首次接触停顿后由敌人有限后退/转身/恢复，玩家手不承担敌方强制位移；同一最终actor/source用于显示和判定。极端不可证路径仍安全保持 |
| 当前阻断 | **真实刀刃与单胶囊不贴合**：静态玩家刀局部漏覆盖约45mm，正在制作资产派生形状；胶囊测试通过不等于画面无穿刀 |
| 手与场景 | Right `a9809a45…` / Left `ecc07136…`；庭院 `c7f2e2b2…`。新指关节、Tripo厚甲和场景IBL仍是私有制作候选，未装入本APK |
| 已有公开下载 | [自然守势预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-natural-guard-2026-11-16)固定旧源码 `add9f3f`，不含本轮组合。新 APK 发布后另列独立 release |

录像保持原始时间流和帧数，无插帧/改速，本次未录声音；主机窗口录制帧率不是PICO渲染性能。完整本版本胜利、玩家弹反/头部闪避/技能处决、音画触觉同步，以及 Space Pro 性能/热量/舒适度均未通过。[验收清单](docs/acceptance.md)列证据与未完成项，[四路交接](docs/agents/README.md)承接制作与评审。

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
