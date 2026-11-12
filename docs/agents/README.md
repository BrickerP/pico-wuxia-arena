# 并行制作与Root审核入口

## 当前可交付状态

整体仍是工程原型，没有达到参赛成品或用户要求的精细程度。只有真正进入目标消费者并有画面/操作证据的产物算已接入；阶段交件、自审通过、测试数量均不等于Root视觉或实战验收。

| 范围 | 最新证据 | 尚未通过 |
| --- | --- | --- |
| 原生可运行包 | `artifacts/clean-coat-native/clean-coat-one-window-debug.apk`，SHA `1b905852d2c6286eaab23f6cc172fa02fcc0c4483cd3861641c88154cb6ec6a1`；共享构建及311项单元测试0失败，已安装并显示Full Stage | 完整攻防、三轮与Space Pro硬件验收 |
| 原生人物/场景 | [实际准备态](../../ArtSource/refinement/presentation/clean-coat-one-window-2026-11-12.png)及[包与画面身份](../../ArtSource/refinement/presentation/clean-coat-one-window-2026-11-12.json)；base albedo/tangent组1b3e、单窗整景9b已接入；首敌附着阶段无NO_MEMORY和已知零切线警告 | 服装轮廓、发型、动态穿插与全部切轮仍未验收；材质清理不代表新造型完成 |
| 真实原生开局 | 新包18:59:24.908 Start receipt为accepted=true、nextResult=COUNTDOWN | 此后4次真实拖动未得到玩家有效strike/敌人扣血；这是当前P0，不能宣称战斗闭环 |
| 浏览器消费者 | 09已修旧967资产锁定、KTX2/UASTC解码、正式角色/单庭院/dao、启动失败显式显示与新墙体坐标；02真实手臂和dao已有实际截图 | 当前仍锁ce90旧albedo/旧窗；02左手物理轨迹、运行失败停机、旧占位分配三项MEDIUM在修；浏览器不代替PICO |
| 公开仓库 | [唯一仓库](https://github.com/BrickerP/pico-wuxia-arena)，公开main69f3866已含原生ce90源码与既有浏览器玩法 | 最新1b3e/9b和手刀工作尚在本地待合入；[旧预发行](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/visual-polish-2026-11-11)不是最新包；新预发行仍为草稿 |

主机里名为swing-reason-probe的旧副本SHA仍为1b905；临时probe编译失败后复制到了旧APK，且reason日志为0，不能当诊断包成功或有效reason证据。临时Core源码已撤回。后续严格以构建成功、实际APK身份和reason标记三项共同确认，不重复安装旧包。

## 上轮Root审核结论

- 03：R2新衣拓扑仍为光滑大袖筒，交襟层次弱，颈腕接口未完成。NOT_PASSED，确认STOPLOSS，不开参数R3、不扩图、不做UV/bake。
- 05：两轮完整发型未过；新的原高模直接修形只在侧面略收紧，背面仍扇形刻槽，partial_direction，尚不发布。
- 06：一个结构窗已进入唯一courtyard并有原生画面；保留此项，不扩第二窗，硬件预算仍开放。
- 07：albedo-only清掉部分整衣石斑，已正式接入原生，旧“尚未合入”不再适用；不据此放行衣袖几何。
- 09：真实消费者修复已交且两项独立review问题修正；typed数据已同步1b3e，动作数值未变，源码冻结待Root合入。
- 02：真实手刀替代白盒有明显收益，但三项MEDIUM未收件前不批准整体。
- 12：研究和UB-01 v2造型输入已交；单人全身T-pose图已由Root看过，仅接受为一次受控Tripo实验输入，不算游戏模型。

## 下一轮三条交付线

1. **真实战斗闭环，Root负责。** 先取得一次可信的reset reason，修实际采样/时序根因，保留35m/s等安全门；随后用真实操作证明挥刀→同一判定→敌人扣血→受击反应/特效/声音。再验格挡/弹反和现有三轮，不用注入命中交卷。
2. **完整刀客造型，03/05制作，12参考，Root生成与合成。** 停止继续拼参数衣筒/曲线髻。对[单人条件输入](../../ArtSource/bench/tripo-image-input-2026-11-12/front-tpose-v1.png)做一次图像条件Tripo源实验；先OV余额和dry-run，余额为0停止，未知不收费。当前代理及直连各一次有界余额查询均为NetworkError，余额未知；未提交收费生成。保原脸/眼与既有78骨动作基础；03收衣片结构，05收发根/主束/盘结。先整人1.5m灰模/实际guard，再动态、材质、原生，不凭生成图放行。
3. **连续呈现，02/07/08负责，Root收件。** 02先闭合左持刀与故障/资源清理；07沿现有HDR做刀面IBL候选，不直接抢改02文件；08先把普通身体斩和弹反做成两个清楚、有限时、可清理的接触时序，不再增加预载未触发资源。所有效果的原生验收依赖第一条真实事件。

下一份整合交付必须同时给：正常游戏视距同机位前后、真实操作短片、对应可下载包/源码节点、明确未通过项。不能用更多研究、测试数或离线特写代替这些结果。

## 当前分工

| 会话 | 当前任务/状态 | 交接 |
| --- | --- | --- |
| Root | 原生输入P0、正式整组发布、整合/构建/设备/画面/Git；不无限轮询 | 本文 |
| 01 | canonical guarded idle/六步walk/三攻击源已收，冻结；新造型后复核动作 | [01](01-combat.md) |
| 02 | 活跃：真实第一人称手刀三项MEDIUM修正 | [02](02-input.md) |
| 03 | 已续派：停止R2路线；条件新源衣服结构审核/适配 | [03](03-art.md) |
| 04 | 已有独立颗粒交08；冻结，不另开资源链 | [04](04-benchmark-qa.md) |
| 05 | 已续派：直接高模首件冻结；条件新源发型审核/适配，保脸眼 | [05](05-hero-face.md) |
| 06 | 单窗已原生，冻结，暂不复制第二窗 | [06](06-environment.md) |
| 07 | 已续派：现有HDR的独立网页IBL候选；保留原生v4 | [07](07-lookdev.md) |
| 08 | 已续派：普通身体斩/弹反两个完整接触时序与真实消费接点 | [08](08-impact-vfx.md) |
| 09 | loader/墙体修复及1b3e typed数据已交冻结，Root收件 | [09](09-combat-direction.md) |
| 10 | 四页教学/准备与战斗UI已接入；冻结，不先扩页 | [10](10-ui-art.md) |
| 11 | 六步同源脚声和必要真实OGG已交；随真实事件做音画验收 | [11](11-audio-haptics.md) |
| 12 | 条件图已交，冻结；新3D源到达后与Root审整体 | [12](12-visual-bench.md) |

## 制作与合入合同

技术栈仅Kotlin + PICO Spatial SDK 6.1.9，目标Space Pro／OS 6，Full Stage。围绕单院落短竞技场精修人物、武器、动作、打击、UI与场景，不增加新的探索模式或并行院落。

Root独占公共正式角色producer／manifest最终发布、library／app资源发布、Main／HomeStage最终接线、共享构建、设备、画面采集和Git。各路只改责任目录或明确授权文件，保留同仓库他人的编辑；禁止复制仓库、建worktree或另开同链路。Root可委派公共producer的具体修改，正式发布仍由Root执行。

各路交接文档承载当前工程交付、来源SHA、可见变化、接入合同、限制和下一项。Root将review与续派写回对应文档。长期决定、偏好与教训进入agentmemory，交接不写成记忆日志。不无限轮询日志或等待会话；不以离线图、单元测试或导入成功替代实际操作验收。

付费Tripo任务由Root统一调度，使用已配置CLI、ov区域、显式 `tripo-v3.1`，先doctor与dry-run；沿现有角色精修，优先已授权制作。API Key与授权URL不得进入仓库或聊天。
