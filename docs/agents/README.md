# 并行制作与Root审核入口

## 当前可交付状态

整体仍是工程原型，没有达到最终参赛美术或完整可验收Demo。当前真实进展是：原生开局、SDK鼠标动作到共享战斗判定、有效命中/扣血与接触消费已取得实际画面；完整攻防、三轮和Space Pro硬件仍开放。

| 范围 | 权威证据 | 边界 |
| --- | --- | --- |
| 最新本地原生包 | `artifacts/native-controller-burst/native-controller-burst-debug.apk`，SHA `9e5fc90a3d341b6b21a36585594ce25d9b16a10d498b424244a67dcc11b24b2b`；构建和328测试0失败，构建前后Kotlin源码SHA一致，已安装 | 这是输入/反馈整合包，尚未公开上传 |
| 实际交战 | [15.8秒录像](../../ArtSource/refinement/presentation/native-input-contact-2026-11-12.mp4)、[扣血实图](../../ArtSource/refinement/presentation/native-input-contact-2026-11-12.png)、[身份/事件收据](../../ArtSource/refinement/presentation/native-input-contact-2026-11-12.json)；真实Start进入COUNTDOWN，真实鼠标旋转产生MotionStrike及SOFT_HIT，HUD敌人100→12、玩家40；敌人护刀接触也实际消费 | 敌人GUARDED_HIT不等于玩家格挡/弹反；三轮胜利和完整手感未通过 |
| 原生人物/场景 | base ac7 / binding1b3e、单窗庭院9b已显示；最新启动首敌成功附着，无NO_MEMORY/FATAL | 新衣/发型未通过；局部颜色和单窗不代表整体美术通过 |
| 已公开节点 | [唯一仓库](https://github.com/BrickerP/pico-wuxia-arena)；[开发预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-visual-preview-2026-11-12)已公开，源码标签精确f4540f0，APK为1b905，3份附件摘要核对一致 | 公开1b905是前一美术节点，不含本轮输入/反馈修复；不能混用9e测试或交战证据 |
| 浏览器 | 旧三方候选1fb已独立APPROVE并在实际Chrome加载三正式资产/44个KTX纹理、78骨10clip、真实双手/dao；无加载/FP错误 | 该次是明确的本地资源接收测试，不能称公网请求或PICO通过；最新44fd候选已保留上游v0.32/8人和地形，待Root实际合入 |
| Tripo | 单人条件图已审；ov代理/直连失败，3个现有节点未通过官方TLS；没有新收费任务 | 余额未知，不等于0或足够；新源实验未执行 |

## 上轮Root审核与本轮修正

- 输入：拒绝Core“保留旧可信基线直到速度变合理”的方案，它会把tracking teleport累积成假扫掠。改为上游队尾相邻Controllers去重，使用最新pose/真实receipt、保连续sequence；Head/control/origin/epoch/有效性变化均为边界。Core原35m/s、250ms、旋转保护不变。328测试及实际MotionStrike/扣血已证明当前模拟器路径。
- 03服装：两轮大形仍是光滑袖筒、压襟弱、颈腕接口未完，STOPLOSS。Tripo不可用期间改为原高模真实Cloth Sculpt/布料约束的单件实验，先完整guard灰模，不再参数衣筒/R3。
- 05发型：直接高模首件只小幅侧面收益，背面仍扇形刻槽，partial_direction，不发布；保脸眼，新条件源待网络。
- 02手刀：旧3项MEDIUM已独立关闭，真实左右持刀、故障锁、旧占位清理通过。续派PICO可用双手/前臂骨架资产，控制移动端纹理预算。
- 08效果：旧普通身体命中浅色硬片拒绝；薄短core/真实切向scar/大小有层次碎屑的新envelope已进9e。实际SOFT/METAL消费已证，38ms细节像素仍要更合适的捕获，不能只凭日志放行。
- 07光影：现有HDR网页IBL有可见金属收益，候选待集成；同时诊断原生近距皮肤泛白。已签名albedo输入冻结，不改动其handoff。
- 06场景：一个结构窗已进入唯一原生courtyard；不扩第二窗，硬件预算仍开放。浏览器双翼是保留其上游构图，不改变原生单场景合同。

## 下一轮交付与验收

1. Root沿同一真实输入完成玩家格挡/弹反、HMD闪避、既有技能/处决，再验三轮切换/回收、胜利/死亡/超时、暂停/恢复/重开。先拍一段完整交战，不再以启动成功替代。Space Pro真机缺口仍明确保留。
2. 01精修一招上劈的引刀—落刀—随势—收招，先1.5m前后短片与5关键姿态；03做完整上衣新方法首件；02做原生双手资产；05保脸眼等待条件源。灰模→动态→材质→原生四关不跳过。
3. Root合入保留最新上游的实际消费者/手刀，再接现有HDR IBL。所有人物/替身复用一次解码并保独立骨架，不恢复旧模型/白盒/静默失败。
4. 04只审实际15.8秒片段，给最多3个带时间点的可见问题；08根据真实画面修接触效果，11随后做音画/触觉对应。不要批量新增QA夹具或更多预载未触发资源。
5. Git使用固定节点发布、核退出码和远端SHA；当前公开f454已完成。后续把新源码、包和实录成组发布，并保留远端网页更新，禁止force或覆盖其内容。

## 当前分工

| 会话 | 当前责任 | 交接 |
| --- | --- | --- |
| Root | 唯一正式产线、共享构建、设备、真实交战与Git发布 | 本文 |
| 01 | 已续派一招精细上劈；原10clip/六步walk已收 | [01](01-combat.md) |
| 02 | 已续派PICO双手/前臂GLB、骨架/抓松与贴图预算 | [02](02-input.md) |
| 03 | 原高模/Cloth方法完整上衣首件；Tripo实验未取消 | [03](03-art.md) |
| 04 | 已续派实际交战视频的3条视觉review | [04](04-benchmark-qa.md) |
| 05 | 发型partial冻结，条件源到手后适配，保脸眼 | [05](05-hero-face.md) |
| 06 | 单窗原生已收，冻结 | [06](06-environment.md) |
| 07 | 网页IBL候选收尾、原生近场皮肤诊断 | [07](07-lookdev.md) |
| 08 | 身体斩envelope已进9e；等实际细节图再校准 | [08](08-impact-vfx.md) |
| 09 | loader/typed组已收，整合由Root处理 | [09](09-combat-direction.md) |
| 10 | 现有四页教学/UI已接；不扩页 | [10](10-ui-art.md) |
| 11 | Foley已收；完整音画/真机触觉未验 | [11](11-audio-haptics.md) |
| 12 | 条件图与造型输入已交冻结 | [12](12-visual-bench.md) |

## 制作与合入合同

技术栈仅Kotlin + PICO Spatial SDK 6.1.9，目标Space Pro／OS 6，Full Stage。围绕单院落短竞技场精修人物、武器、动作、打击、UI与场景，不增加新的探索模式或并行院落。

Root独占公共正式角色producer／manifest最终发布、library／app资源发布、Main／HomeStage最终接线、共享构建、设备、画面采集和Git。各路只改责任目录或明确授权文件，保留同仓库他人的编辑；禁止复制仓库、建worktree或另开同链路。Root可委派公共producer的具体修改，正式发布仍由Root执行。

各路交接文档承载当前工程交付、来源SHA、可见变化、接入合同、限制和下一项。Root将review与续派写回对应文档。长期决定、偏好与教训进入agentmemory，交接不写成记忆日志。不无限轮询日志或等待会话；不以离线图、单元测试或导入成功替代实际操作验收。

付费Tripo任务由Root统一调度，使用已配置CLI、ov区域、显式 `tripo-v3.1`，先doctor与dry-run；沿现有角色精修，优先已授权制作。API Key与授权URL不得进入仓库或聊天。
