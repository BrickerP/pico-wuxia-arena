# PICO Wuxia Arena

面向 PICO Space Pro／OS 6 的中式写实 PVE 刀术竞技场 Demo，采用 Kotlin + PICO Spatial SDK 6.1.9，以 Full Stage 运行。体验围绕一座雨后酒馆院落、一把刀与三名依次上场的刀客展开，单次试炼连续三轮，共用180秒战斗时限。

## 当前开发节点

2026-11-11的本地集成版已换入三角色十段动作、新刀具、两层酒馆庭院、雨雾与原生光照、独立接触粒子、纸墨UI和录制素材音效。组合构建与261项单元测试通过，当前APK已在模拟器实际加载场景、玩家刀和首轮敌人。三敌同时预载的原生内存故障已改为按轮单active加载；完整三轮切换与真实输入仍待验收。

最新本地安装包为 `artifacts/integrated-polish/wuxia-arena-integrated-debug.apk`，99,113,182字节，SHA-256：

```text
8d1e456e027c9ac14243e65db9171f5998909dd80400189f0451f0e1d99a6ede
```

[下载本轮开发包、实图与身份清单](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/visual-polish-2026-11-11) · [本轮源码节点](https://github.com/BrickerP/pico-wuxia-arena/commit/6b407acc4507812b99d1315e58c8a2c588719fd0) · [最新源码](https://github.com/BrickerP/pico-wuxia-arena/tree/main)。此前2026-11-10预发行保留为历史节点。当前事实与待验项目见[验收清单](docs/acceptance.md)。

| 范围 | 已接入本地集成版 | 当前缺口 |
| --- | --- | --- |
| 游戏流程 | 准备、倒计时、三轮攻防、补给、胜负、暂停与重开 | 当前版本的真人完整流程尚未验收 |
| 人物动作 | 三名78骨刀客，每名十段动作；正劈、左右斩使用同源时钟与刀段／身体采样 | 旧步法与新守势切换有约0.25m祖先高度差；青衫、玄甲部分足底离地16–20mm |
| 场景光影 | `courtyard_hero.glb` 两层酒馆、连续石路、侧巷；雨雾、月光、灯笼光与雨夜IBL | 人物脸／手／刀刃可读性正在用端内图复核 |
| 打击呈现 | 接触短停、身体白闪、反冲、刀光、伤害跳字、五份新粒子资源、声音与触觉事件消费 | 受控真实命中的完整画面与触觉未验收，湿布／近地效果还缺真实表面事件接线 |
| 人物／刀具精修 | 新dao几何／PBR已在正式本地资源；成年头脸、独立眼球与发束候选 | 新头动态颈部退回修复；服装结构继续制作 |

## 产品立场与主题

核心体验是近身挥刀命中的确定感、迎刀弹反、身法避招与顺畅的反击收势。手感优先，视觉其次，制作范围围绕个人4–8周可打磨的单院落、单刀、三名顺序对手收敛。

| 参照 | 本 Demo 的交付要求 |
| --- | --- |
| Blade & Sorcery、荣耀战魂 | 头、手与刀的动作参与攻防，读招、格挡、弹反、闪避、反击和处决衔接清楚 |
| 影之刃零、鬼武者、只狼 | 蓄势、接触、卸力与收势可读，命中、格挡和弹反具有不同反馈 |
| 黑神话悟空 | 成熟写实骨相、交领束带、可信刀具，以及木作、灯笼、湿石材和冷暖光层次 |
| 骑马与砍杀、天国拯救 | 借鉴人物、兵器和环境的可信尺度与空间感；本次仍交付单院落短竞技场 |

三轮与180秒是当前节奏参数。最终品质按正常游戏视距下的人物、动作、材质、光影和攻防反馈评审，具体门槛见[视觉bench](docs/visual-quality-bench.md)与[动作／打击反馈规格](docs/combat-polish-spec.md)。

## 游戏流程

准备就绪 → 开始 → 三秒倒计时 → 第一轮交战 → 清场与补给 → 下一轮倒计时 → 三轮胜利结算，或生命归零／时限耗尽后失败结算。结束后可重新挑战。

- 三名敌人依次为100、125、150生命，待机出招间隔逐轮缩短，按距离接近玩家。
- 挥刀和前刺由刀段、移动与扫掠轨迹判定，区分头部、躯干，同一挥击去重。
- 举刀形成格挡，近期迎刀可产生弹反，侧移、后撤和下蹲用于避招；守势消耗体力，体力不足会破防。
- 连击影响伤害与得分，攻防积累气势，双手收刀蓄力后前推释放破势；敌人低血时，同一入口进入处决。
- 玩家生命、体力、气势、轮次与阶段提示进入HUD，得分和本机最佳成绩集中于结算。

以上是当前代码路径，实际运行验收另见清单。整局自玩按当前安排后置，构建、专项制作、输入诊断和启动检查继续进行。

## 输入与桌面预演

设备模式消费PICO头部与控制器观察，攻击、架刀、弹反、闪避与双手技能由动作判定。桌面预演仅在debug模拟器条件下启用；已实现的动作入口生成虚拟头手轨迹，再进入相同输入队列与战斗判定，入口本身不直接扣血。

**真实主机按键进入模拟器、产生虚拟轨迹并造成共享判定结果的完整链路尚未证明。** SDK启动成功、模拟注入测试与出招资格查询均不算这条链路通过。以下是应用已实现的映射，不能据此推断模拟器已把这些键送入应用。

| 应用键位 | 预演动作 |
| --- | --- |
| 1 / J | 正向斩击 |
| 2、3 | 左斩、右斩 |
| 4 / K | 前刺 |
| 5 / V | 头上架刀 |
| 6 / B、7 / N | 左、右架刀 |
| 8 / Z、9 / X | 左、右闪避 |
| C | 下蹲 |
| G | 破势／低血处决 |

应用还接入官方虚拟手柄右A的边沿事件。模拟器原生设置当前显示Space对应右A，但实际主机Space至该事件仍缺证据。W属于模拟器移动控制，其效果依赖当前模拟器输入模式。切换模式和按键测试统一由Root操作同一实例。

## 人物、动作与场景

三轮分别加载 `app/src/main/assets/models/opponents/` 下的 `base.glb`、`indigo.glb`、`veteran.glb`，对应试刀客、青衫护院和玄甲守擂。角色由ov区域Tripo CLI生成，约1.78m、78骨，与R_Hand绑定的dao共用骨架。

| 当前十段资源 | 用途 |
| --- | --- |
| `idle`、`walk` | 备用待机与距离驱动步法；静止战斗守势取三攻击的共同起点 |
| `attack_overhead`、`attack_left`、`attack_right` | 三方向蓄势、攻击与收势，共享source 1.00秒接触标记 |
| `hit_body`、`hit_head`、`hit_side` | 分部位受击与弹反反应 |
| `fall`、`turn` | 倒地，以及已打包待编排的转身 |

三方向姿态来自78骨制作源，保留目标rest、骨长与原握持校正；攻击profile由最终GLB蒙皮采样生成，与动画共享时钟。步法仍沿用旧源0.333333–1.5秒循环、每1.45m一周期，01与09正在统一其守势与代理，当前过渡缺口保留在验收清单。

场景只加载一份 `courtyard_hero.glb`，替换旧酒馆／前庭／细节三块运行资源；制作源仍保留供复建。`SceneLighting` 和 `SceneWeather` 负责原生直射光、雨夜IBL与雨雾。准备页采用纸墨与朱砂，四步教学可翻页，交战时缩为紧凑资源／动作提示。

接触呈现消费同批 `CombatImpact` 的伤害、部位、致命标记、接触点、法线与实际扫掠切向。新资源包含软接触、金属、湿布、闪避近地和落地五类，按独立粒子运动；湿布／近地真实触发与受控端内效果仍待接通和验收。13份WAV覆盖攻防、脚步、雨声与结算，来源和许可在 `ArtSource/audio/`。

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
| `input/DesktopCombatInput.kt` | 桌面动作轨迹与共用队列入口 |
| `content/EnemyAnimator.kt`、`runtime/AttackBankProfiles.kt` | 角色播放及同源骨骼／刀段采样 |
| `content/CombatEffects.kt`、`ContactParticleEmitter.kt`、`PlayerBladeTrail.kt` | 接触特效、独立粒子与刀光 |
| `ArtSource/tripo-warrior/`、`ArtSource/refinement/` | 可复建角色管线、分工候选与审核资产 |
| `ArtSource/audio/` | 音频制作、原始来源、许可与校验 |

唯一仓库为本项目，API凭据由CLI本机配置管理。当前12路分工、Root审核与下一步在[制作入口](docs/agents/README.md)，运行完成条件在[验收清单](docs/acceptance.md)。

[本轮实际Full Stage画面](ArtSource/refinement/presentation/integrated-2026-11-11.png)与[构建／资源身份及证据边界](ArtSource/refinement/presentation/integrated-2026-11-11.json)。当前图为首轮准备态，不包含受控命中。
