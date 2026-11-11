# 并行制作与Root审核入口

## 当前方向

中式写实短PVE竞技场由12个用户会话并行制作，实际工程统一为 `/Users/yupeng/projects/personal/pico-wuxia-arena`。Root负责审核、组合、正式发布、共享构建与设备操作。各路按已授权队列交付实物，阶段完成不等于全部会话应持续空转。

人物、服装、环境、原生光色、动作、特效与UI均按0.8m／1.5m／3m正常游戏视距评审。每路交真实模型、代码或可见画面，同机位前后图与连续片段说明收益。参照与门槛见[动作／打击反馈规格](../combat-polish-spec.md)和[视觉bench](../visual-quality-bench.md)。

## 分工、已收件与当前队列

| 会话 | 责任 | 当前收件／下一项 | 交接 |
| --- | --- | --- | --- |
| 01 | 动作源、站姿、三方向、防御／弹反／行动 | canonical guarded idle／六步walk已组合；反应源待按状态衔接，继续真实动作与鞋底审核 | [01](01-combat.md) |
| 02 | dao几何、握持、武器PBR与装配 | 新dao及玩家刀已正式发布；按真实手面修握持穿插与刃口可读性 | [02](02-input.md) |
| 03 | 服装结构、领襟、袖口、扣具 | v3领襟材质／UV方向获开发集成认可；袖口动态与扣具装配继续，尚未合入人物 | [03](03-art.md) |
| 04 | 独立颗粒、湿布、近地／落地效果源 | 源资源已交08；依据真实表面／落地事件接入，不伪造触发 | [04](04-benchmark-qa.md) |
| 05 | 成年写实头脸、眼与发束 | 连续头颈raw34ce已入正式base并在Full Stage显示；只交微表面／材质delta，补近距与动态审核 | [05](05-hero-face.md) |
| 06 | 雨后酒馆庭院、路面、建筑与构图 | stage2材质8b1098已入新包；定位重置观察视角的纸面显示差异，再决定实际返修 | [06](06-environment.md) |
| 07 | PICO原生光影、IBL、雨雾 | v4补光与释放修正已接入；以新人物实际图复核脸／手／刀与背景层次 | [07](07-lookdev.md) |
| 08 | 打击VFX、刀光与独立粒子运行 | 软／金属接触已有事件入口；湿布／闪避近地／落地只有预载，继续真实事件闭环 | [08](08-impact-vfx.md) |
| 09 | 动作bank、循环、动画／代理一致 | schema3 b03f正式KTX组与typed数据身份已统一；六步共用clock已冻结，Root验实际过渡与代理 | [09](09-combat-direction.md) |
| 10 | 中式UI美术、空间引导与可读性 | 四页教学、配置引导已冻结；Root已应用安全区pose，实际图确认完整且不挡脸刀，继续状态／交互验收 | [10](10-ui-art.md) |
| 11 | Foley、音频消费、场景声与触觉 | 六步同源脚声、10个必要OGG最小源交付，61项JVM＋7项资产专项通过；实际音画与触觉待验 | [11](11-audio-haptics.md) |
| 12 | 目标游戏视觉bench、正常视距审核 | 用新组合原生图给明确返修；分清离线、模拟器和Space Pro证据 | [12](12-visual-bench.md) |

## 当前组合与公开版本

| 范围 | 已取得的证据 | 边界 |
| --- | --- | --- |
| 最新本地新包 | `app/build/outputs/apk/debug/app-debug.apk`，SHA `7e1368fed7423fa5b3d9ea2f567cc1e786fa0bbfa85ebd6409a714369fbfc17e`，242,709,448字节；pose调整前共享构建及311项单元测试通过；两行pose调整后重建与原生视觉检查通过，未重跑311项 | 尚未作为新GitHub release发布，测试不替代实际手感 |
| 新包Full Stage | [已收件实图](../../ArtSource/refinement/presentation/canonical-2026-11-11.png)与[身份清单](../../ArtSource/refinement/presentation/canonical-2026-11-11.json)；约27秒完成场景／新人物附着，完整面板不挡脸刀，未报NO_MEMORY | 仅首轮准备态；新skinned切轮、近距法线与完整交战未验 |
| 真实原生输入 | 旧233584包的主机Shift+E → SDK右手 → 同一`PlayerCombatResolver.observe`，见`artifacts/input-native/real-key-to-resolver-final.*` | 返回motion frame与刀段，没有敌人扣血证据 |
| 真实流程画面 | 旧233584包的`artifacts/input-native/start-stationary-left.png`显示敌人接近、玩家受击后的DEFEAT | Start receipt未捕获；不代表新包或三轮胜利通过 |
| 已公开交付 | main节点fd58c04；[现有预发行](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/visual-polish-2026-11-11)仍为8d1e456e、99,113,182字节旧组合包 | 不得与本地7e1368fe版本混用证据；新checkpoint仍待Root commit／push |

前一组合包767bc0af保留原身份；当前7e1368fe与它只有上述两行HomeStage控制面板pose差异。约27秒为本次模拟器加载观察，不能推断Space Pro性能。

正式人物、profile、typed数据和玩家刀以schema3 binding `b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f`成组发布。当前场景只加载一个stage2 `courtyard_hero.glb`；旧三份运行场景已移除。设备和模拟器都消费SDK原生头手，HMD派生假手、右A脚本斩击与Activity按键宏已移除。

## Root审核与下一门槛

1. **准备页交互。** Root已将控制面板从`(-0.85,1.15,-1.45)`／yaw34°移至`(-0.6,1.2,-1.75)`／yaw20°，实际图确认完整且不挡脸刀。下一项验证开始、翻页与状态切换的真实确认；就绪与能力安全门保持原样。
2. **新组真实攻防。** 已有真实键到共享motion.observe的证据；接下来取得新包开局、真实挥刀命中／掉血、格挡、弹反、闪避、处决的连续画面与事件对应，不以队列注入或资格查询代替。
3. **动作与人物。** canonical源、统一根校准和同源profile已接入。实际过渡、青衫／玄甲鞋底残余、攻击身体拟合、手指／袖口／领口仍按正常距离返修。
4. **场景与反馈。** 06分清观察视角／帧时序与真实纸面问题，按证据修；08的湿布／闪避近地／落地需接真正事件生产者；11验证六步音画与真实SoundPool。
5. **完整交付。** 三轮资源换入／回收与胜利、死亡／超时、暂停恢复和重开形成新版本证据后，再统一发布源码、APK和实图。Space Pro性能、持续运行、热稳定与舒适度保留独立验收。

## 制作与合入合同

技术栈仅Kotlin + PICO Spatial SDK 6.1.9，目标Space Pro／OS 6，Full Stage。围绕单院落短竞技场精修人物、武器、动作、打击、UI与场景，不增加新的探索模式或并行院落。

Root独占公共正式角色producer／manifest最终发布、library／app资源发布、Main／HomeStage最终接线、共享构建、设备、画面采集和Git。各路只改责任目录或明确授权文件，保留同仓库他人的编辑；禁止复制仓库、建worktree或另开同链路。Root可委派公共producer的具体修改，正式发布仍由Root执行。

各路交接文档承载当前工程交付、来源SHA、可见变化、接入合同、限制和下一项。Root将review与续派写回对应文档。长期决定、偏好与教训进入agentmemory，交接不写成记忆日志。不无限轮询日志或等待会话；不以离线图、单元测试或导入成功替代实际操作验收。

付费Tripo任务由Root统一调度，使用已配置CLI、ov区域、显式 `tripo-v3.1`，先doctor与dry-run；沿现有角色精修，优先已授权制作。API Key与授权URL不得进入仓库或聊天。
