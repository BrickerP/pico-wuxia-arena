# PICO Wuxia Arena

面向 PICO Space Pro／OS 6 的中式写实 PVE 刀术竞技场 Demo，采用 Kotlin + PICO Spatial SDK 6.1.9，以 Full Stage 运行。体验围绕一座雨后酒馆院落、一把刀与三名依次上场的刀客展开，单次试炼连续三轮，共用180秒战斗时限。

## 当前开发节点

当前本地组合已接入新头脸与连续颈部、三角色十段动作、共用守势的六步行走、KTX2材质、新刀具、第二轮酒馆材质、原生光照雨雾、纸墨UI和13份录制素材音效。面板pose调整前的组合构建与311项单元测试通过；两行pose调整后重新assemble，并完成原生视觉检查。最新包已在模拟器 Full Stage 实际显示首轮人物、眼睛、领口、玩家刀和场景，完整准备面板处于视场内且不遮敌人脸和刀；完整交战与三轮胜利仍待该版本验收。

| 版本 | 身份与可用范围 |
| --- | --- |
| 最新本地安装包 | `app/build/outputs/apk/debug/app-debug.apk`，242,709,448字节；SHA-256 `7e1368fed7423fa5b3d9ea2f567cc1e786fa0bbfa85ebd6409a714369fbfc17e` |
| 本地检查 | 面板pose调整前`:app:assembleDebug :app:testDebugUnitTest --offline`通过；32个suite、311项，0失败／错误／跳过。两行调整后仅重建与原生视觉检查，未重跑311项 |
| 最新实际画面 | [Full Stage准备态](ArtSource/refinement/presentation/canonical-2026-11-11.png)及[身份与验收边界](ArtSource/refinement/presentation/canonical-2026-11-11.json)，已收件；新包尚未作为新release发布 |
| 前一组合包 | `artifacts/canonical-native/canonical-head-scene-debug.apk`，767bc0af…，242,709,448字节；与当前包的唯一区别是控制面板pose |
| 已公开节点 | GitHub main节点 `fd58c04`；[已发布开发预发行](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/visual-polish-2026-11-11)仍是99,113,182字节的 `8d1e456e…` APK，运行源码节点为 `6b407ac` |

本地新包与已公开预发行的资源、输入和测试身份不同。新包的构建成功与准备态画面尚不表示完整可玩性通过。逐项事实、证据位置和剩余门槛见[验收清单](docs/acceptance.md)。

| 范围 | 当前接入 | 待验或返修 |
| --- | --- | --- |
| 游戏流程 | 准备、倒计时、三轮攻防、补给、胜负、暂停与重开 | 新包完整三轮、超时、恢复与重开 |
| 人物动作 | 三名78骨刀客各十段；canonical idle／六步walk与三攻击读取同组profile | 实际过渡、鞋底残余、握持穿插及攻击身体拟合 |
| 人物与刀具 | 试刀客新头脸、眼球和连续颈桥已入包；两种dao正式发布 | 近距皮肤／眼睛／刀刃，服装领襟、袖口与扣具组合 |
| 场景光影 | 唯一两层酒馆院落、窗纸暖斑、方向木纹、灯笼纸腹层次、雨雾和原生灯光 | 视角变化时纸面显示差异仍在定位，Space Pro预算未测 |
| 打击呈现 | 短停、白闪、反冲、刀光、跳字、接触粒子、声音与触觉消费 | 真实命中／弹反完整片段；湿布、闪避近地和落地仍缺实际事件生产入口 |
| UI与声音 | 四页教学、160dp交战面板、六步同源脚声与13份WAV | 准备面板安全区已实际确认；状态切换、SoundPool、落脚同步和真实触觉仍待验收 |

## 产品立场与主题

核心体验是近身挥刀命中的确定感、迎刀弹反、身法避招与顺畅的反击收势。手感优先，视觉其次，范围围绕个人4–8周可打磨的单院落、单刀、三名顺序对手收敛。

| 参照 | 本 Demo 的交付要求 |
| --- | --- |
| Blade & Sorcery、荣耀战魂 | 头、手与刀参与攻防；读招、格挡、弹反、闪避、反击和处决衔接清楚 |
| 影之刃零、鬼武者、只狼 | 蓄势、接触、卸力与收势可读，命中、格挡和弹反具有不同反馈 |
| 黑神话悟空 | 成年写实骨相、交领束带、可信刀具，以及木作、灯笼、湿石材和冷暖光层次 |
| 骑马与砍杀、天国拯救 | 借鉴人物、兵器与环境的可信尺度和空间感，交付范围仍为单院落短竞技场 |

三轮与180秒是当前节奏参数。品质按0.8m／1.5m／3m正常游戏视距下的人物、动作、材质、光影和攻防反馈评审，门槛见[视觉bench](docs/visual-quality-bench.md)与[动作／打击反馈规格](docs/combat-polish-spec.md)。

## 游戏流程

准备就绪 → 开始 → 三秒倒计时 → 第一轮交战 → 清场与补给 → 下一轮倒计时 → 三轮胜利结算，或生命归零／时限耗尽后失败结算。结束后可重新挑战。

- 三名敌人依次为100、125、150生命，待机出招间隔逐轮缩短，按距离接近玩家。
- 挥刀和前刺由刀段、移动与扫掠轨迹判定，区分头部、躯干，同一挥击去重。
- 举刀形成格挡，近期迎刀可产生弹反；侧移、后撤和下蹲用于避招。守势消耗体力，体力不足会破防。
- 连击影响伤害与得分，攻防积累气势；双手收刀蓄力后前推释放破势，敌人低血时同一入口进入处决。
- 玩家生命、体力、气势、轮次与阶段提示进入HUD，得分和本机最佳成绩集中于结算。

以上说明当前代码路径。旧原生输入包已取得敌人接近、玩家受击和失败结算画面；新包完整流程的验收状态见清单。

## 输入与桌面预演

设备与模拟器都消费 SDK 原生 HMD／controller pose，经同一观察队列进入 `PlayerCombatResolver`。攻击、架刀、弹反、闪避和双手技能由动作判定。模拟器来源保持 `InputOrigin.DESKTOP`、追踪质量UNKNOWN，不生成硬件触觉；设备支持状态与输入就绪安全门保持有效。

模拟器预演使用实际虚拟手柄设置：

1. 选择 **Right Controller Mode**，实际启用 **Controller Button Mode**。
2. 关闭 **Keyboard Mode** 文本模式，使用 **Shift + W/A/S/D/Q/E** 移动虚拟手柄。
3. 鼠标调整射线，按射线落点选择空间UI；具体按钮键以当前模拟器设置为准。

真实主机 Shift+E → SDK原生右手pose → 共享 `PlayerCombatResolver.observe` 已在旧 `233584…` 原生输入包取证，返回了真实motion frame与刀段。该证据没有造成敌人扣血。新 `7e1368fe…` 包沿用这条输入实现，仍需实际攻防、暂停与重开的组合证明。应用不再保留按键动作宏、右A脚本斩击或HMD派生假手路径。

浏览器代理原型的桌面试玩入口见[`prototype/web-v0.13/index.html`](prototype/web-v0.13/index.html)。它是单文件Three.js页面，用鼠标左右键代理双手持握，用来提前验证兵器架、连招衔接与跑跳语义；不是PICO安装包，也不消费上面的模拟器键位。该目录的实测结论只适用于自身，回真机必须重新接线。

## 人物、动作与场景

正式角色为 `app/src/main/assets/models/opponents/` 下的 `base.glb`、`indigo.glb`、`veteran.glb`，对应试刀客、青衫护院和玄甲守擂。角色由ov区域Tripo CLI生成，约1.78m、78骨，与R_Hand绑定的dao共用骨架。当前正式组binding为 `b03f55e6…`，运行角色与玩家刀均为必需KTX2／BasisU材质；源贴图分辨率保留。

| 十段资源 | 当前用途 |
| --- | --- |
| `idle`、`walk` | 共用canonical守势的待机和距离驱动六步步法 |
| `attack_overhead`、`attack_left`、`attack_right` | 三方向蓄势、攻击与收势，共享source 1.00秒接触标记 |
| `hit_body`、`hit_head`、`hit_side` | 分部位受击与弹反反应 |
| `fall`、`turn` | 倒地，以及已打包待编排的转身 |

idle／walk／三攻击共用每个角色的一次根Y校准。walk源循环为1/3–1.5秒，每1.45m六步；动画、代理与脚声读取同一locomotion profile。青衫／玄甲足底残余及攻击身体拟合仍需动态复核。生产入口、来源与纹理合同见[角色库说明](ArtSource/tripo-warrior/README.md)。

场景只加载一份 `courtyard_hero.glb`，当前采用材质stage2 `8b109801…`；原制作源保留供复建。`SceneLighting` 和 `SceneWeather` 提供原生直射光、雨夜IBL和雨雾。准备、暂停与结算使用400dp纸墨面板，交战缩为160dp。控制面板位置由`(-0.85,1.15,-1.45)`／yaw34°改为`(-0.6,1.2,-1.75)`／yaw20°，实际设备图确认完整且不遮敌人脸刀。

接触呈现消费同批 `CombatImpact` 的伤害、部位、致命标记、接触点、法线和实际扫掠切向。软接触与金属已有真实接触入口；湿布、闪避近地和落地资源虽已预载，实际事件生产仍待接通。13份WAV的最小重建源为10份录制OGG，许可与SHA在 `ArtSource/audio/`。

## 构建与工程入口

先读[PICO CLI开发手册](docs/agent-start.md)，配置JDK 21、PICO SDK 6.1和Android SDK。本机路径留在未纳入版本控制的 `local.properties`。

```bash
./gradlew :app:assembleDebug :app:testDebugUnitTest --offline
```

APK输出为 `app/build/outputs/apk/debug/app-debug.apk`，包名 `com.example.wuxiaarena.p0d2f0182`，启动Activity `.platform.LaunchActivity`。Root统一正式发布、共享构建、模拟器与Space Pro操作。

| 入口 | 职责 |
| --- | --- |
| `Main.kt`、`content/HomeStage.kt` | Full Stage、UI／音触接线、场景生命周期 |
| `runtime/ArenaSession.kt` | 三轮流程、资源、攻击时钟、伤害、胜负与呈现事件 |
| `core/combat/PlayerCombatResolver.kt` | 轨迹接触、架刀、弹反、闪避与双手技能判定 |
| `input/PicoTrackingAdapter.kt`、`runtime/TrackingSession.kt` | SDK原生头手观察、来源、安全门与生命周期 |
| `content/EnemyAnimator.kt`、`runtime/AttackBankProfiles.kt`、`LocomotionProfiles.kt` | 播放与同源骨骼／刀段／步态采样 |
| `content/CombatEffects.kt`、`ContactParticleEmitter.kt`、`PlayerBladeTrail.kt` | 接触特效、独立粒子与刀光 |
| `ArtSource/tripo-warrior/`、`ArtSource/refinement/` | 可复建角色管线、分工候选与审核资产 |
| `ArtSource/audio/` | 音频制作、实际重建源、许可与校验 |

唯一仓库为本项目，API凭据由CLI本机配置管理。[12路制作入口](docs/agents/README.md)维护当前分工、审核结论和下一门槛；[验收清单](docs/acceptance.md)维护对应版本的完成条件。
