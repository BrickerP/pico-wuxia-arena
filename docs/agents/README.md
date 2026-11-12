# 并行制作与 Root 审核入口

## 当前交付合同

整体仍是开发预览，人物、动作与打击的整体观感未通过，尚未达到完整参赛 Demo。技术栈为 **Kotlin + PICO Spatial SDK 6.1.9**，目标 **Space Pro / OS 6、Full Stage**；只打磨既有单院落、短 PVE 三轮战斗。

| 状态 | 已有实物与证据 | 验收边界 |
| --- | --- | --- |
| 最新已公开 | [原生双手/HIT开发预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-hands-hit-2026-11-13)，源码`27bd559d9d204aeb9fbb7e53ffd92e1dd38f9a4e`、APK`a8907a84…`，四附件已核对SHA与上传状态；[版本收据](../../ArtSource/refinement/presentation/native-hands-hit-2026-11-13.json) | 整体品质未通过。后续场景、上劈、UI、FX候选仅备份制作源，尚未装入此APK。 |
| 已合入 main | [PR #11](https://github.com/BrickerP/pico-wuxia-arena/pull/11)，合入提交 `93f3ded393d4c417f6fb883447cc1e6fe4602199` | main 源码节点与公开 APK 的固定源码标签分别标识，不能把后续工作树改动算进已发布包。 |
| 原生链路局部通过 | [15.8 秒交战片](../../ArtSource/refinement/presentation/native-input-contact-2026-11-12.mp4)、[扣血画面](../../ArtSource/refinement/presentation/native-input-contact-2026-11-12.png)、[身份与事件收据](../../ArtSource/refinement/presentation/native-input-contact-2026-11-12.json)：真实 Start → COUNTDOWN，实际模拟器鼠标动作 → SDK 虚拟手柄轨迹 → 共享 resolver → MotionStrike / SOFT_HIT，HUD 敌血 100→12 | 原始捕获只有 74 帧，导出 30fps 未补造中间状态；不能据此判定 38ms 特效细节、完整手感或三轮通过。 |
| 玩家格挡、重开局部通过 | [格挡画面](../../artifacts/native-controller-burst/held-guard-4s.png)、[实际输入录像](../../artifacts/native-controller-burst/held-guard-attempt.mp4)、[对应日志](../../artifacts/native-controller-burst/held-guard-attempt.log)：终局后重开并再次 Start，generation=1；实际 BLOCK 消费 id=9，画面玩家 HP100 / 耐力75；随后异向来刀 PLAYER_HIT | 玩家 BLOCK 与敌人 GUARDED_HIT 已区分；玩家 PARRY、HMD 闪避、技能 / 处决、三轮胜利及 Space Pro 实机仍未验证。 |
| 已发布包构建通过 | [9e 构建身份](../../artifacts/native-controller-burst/build-identity.json)：328 测试、0 失败 / 错误 / 跳过，构建前后 Kotlin 源码摘要一致 | 该结果只属于 9e 包，不覆盖当前双手 / HIT 工作树。 |
| 最新原生运行 | 双手/HIT组合包 `a8907a84…` 已构建、安装、进入实际交战；[准备态实图](../../ArtSource/refinement/presentation/native-hands-ready-2026-11-13.png)、[交战实图](../../ArtSource/refinement/presentation/native-hands-contact-2026-11-13.png)、[实际输入日志](../../artifacts/native-hands-hit-2026-11-13/real-input.log)。初始化禁用模型后播放动画的黑屏已修；真实Start/挥刀/敌血100→12/受击hit_body再次成立 | 整体workflow的自定义验收仍未自动证明；右手一指过直、近景肤色、左手/换手/切口与HIT过渡像素仍待验。数据/构建通过不算视觉通过。当前公开包为a8907a84，原9e视频仍只作为旧节点证据。 |
| 美术未通过 | 当前正式角色 base `ac7dfbc…` / binding `1b3e031…`、单窗庭院 `9b2598…` 已原生显示；新上劈、整立面与近场配光候选已交 | 新衣物物理首件失败，发型仅局部方向收益；人物质感、握刀贴合、动作衔接、遮挡与效果仍需改善。面数、导入与尺寸不是整体品质验收。 |

唯一产品路径为原生源码→APK→PICO Emulator→Space Pro。HTML/Three.js游戏、浏览器试玩、Web光照和新HTML mock全部停止。prototype及已有Web候选只保留历史，不继续接入或维护；浏览器只用于必要资料与账号服务。

## Root 审核重点与下一交付

1. **先把双手与 HIT 合成可运行节点。** 保留真实 SDK 输入、同一 resolver 和现有动作规则；核实左右持刀、默认闭握 / 空手放松、追踪丢失恢复、UI 射线与退出回收。受击模型与代理共享真实 clip / source clock，保留短停和过渡，不用 standing 代理或关闭淡入掩盖问题。交新的固定源码、APK 与实际近景画面。
2. **把同一记近身战斗磨清楚。** 01 上劈 v7 先由 Root 审完整短片、侧向刀路与接触 / 回守，再决定重导；04 的整身白闪遮细节、黑色刀面遮脸问题交 07 / 08 / 02 协同，先改明确可见的两点。缺少像素证据的效果不作通过，未被真实动作触发的资源不算可用机制。
3. **把人物与原场景的整体现有内容做精。** 03 的失败物理笼不传入正式高模，不继续参数试错；05 保脸眼与已签名源，不重做失败发型。06 整立面候选进入 Root 目视与原生预算审查，旧“单窗冻结”已被本轮成套精修合同替代；不扩场景或地点。
4. **再收既有完整流程。** 沿真实输入补玩家弹反、HMD 闪避、技能 / 处决，随后三轮角色切换与回收、胜利 / 死亡 / 超时、暂停 / 恢复 / 重开。Space Pro 性能、画面与触觉实测单独列为待验，未完成前不宣称 100%。

## 各方向收件与下一项

下表为工程交付状态；“待 Root”代表收件 / 合入关卡，不是质量已通过。具体来源、SHA、限制与制作文件以各路交接为准。

| 方向 | 当前实物 / 审核结论 | 最重要下一交付 | Root 接力 |
| --- | --- | --- | --- |
| [01 动作](01-combat.md) | fine-overhead v7：1.75 秒完整源、五姿态与同机位前后片已交；正式仍是既有 10clip / 六步 walk | 同一招经 Root 审阅后的刀路、接触与收招修正，不新增招式 | 待完整动作审核与重导决策 |
| [02 手刀](02-input.md) | 原生双手版本 `71c39091…`，共 10,578 面 / 5.47MB；离线开发集成接受，资源与接线已入工作树 | 原生实际闭握、左右映射与前臂截口画面，修具体贴合问题 | Root 正在整包与原生接力 |
| [03 服装](03-art.md) | 一次真实 Cloth 求解在 F06 健康门停止；腕口挤压、肩肘大形未改善；未传高模、未烘焙 | Root 选定结构修复或新源后，先交结构正确的完整 guard 灰模；不得沿失败笼继续参数循环 | Root已续派真实二维衣片结构；无可发布新衣 |
| [04 独立效果审阅](04-benchmark-qa.md) | 原生片已审：10.296611s 整身白闪，12.080411 / 12.455311s 黑刀面遮脸；未把单目重叠判成确定穿模 | 对修后实际交战片核这两处可见问题及独立粒子细节 | 现有问题已可派修，待修后画面 |
| [05 头发](05-hero-face.md) | direct-high 侧面仅小幅收益，背面仍扇形刻槽；冻结为 partial，未正式发布 | 一次受控新源到达后只适配发区，保既有脸眼，交连续汇根与盘结灰模 | 待 Root 新源；不追加曲线 / 参数盘髻 |
| [06 场景](06-environment.md) | 整庭院 `64da2798…` 已交：四地层 / 五上层共享窗、近檐瓦口 / 滴水；零新增图片 / 材质，有整立面与 1.5m 对照 | Root 审同机位整体收益、原生材质及实际绘制 / 内存预算 | Root已目视接受开发整合，待原生替换；正式仍9b |
| [07 光影](07-lookdev.md) | 已签名 albedo 已发布；Web IBL 候选冻结；原生 `native-nearfield.patch/json` 为未应用数值提案 | Root 受控应用近场提案，交同场景近脸 / 刀刃前后画面 | 候选待 Root 审 / 接；不改已签名 albedo |
| [08 运行效果](08-impact-vfx.md) | 薄 core / 切向 scar / 分层碎屑已进9e，SOFT / METAL 实际消费已证；5资源存在不等于5类触发全通 | 修明确遮挡并取得实际接触细节画面；核真实闪避等入口再消费已有资源 | 已收源码，细节像素与其它触发待验 |
| [09 bank / 接线](09-combat-direction.md) | 正式 locomotion / typed 基础已收；网页消费者工作保留独立外观标签；新增 hurt 数据已由 Root 正式重发 | 收口受击 source clock、typed 与 runtime 一致性，交原生动作 / 判定对齐 | Root 正在整合；不混入网页扩世界 |
| [10 UI](10-ui-art.md) | 既有四页教学、HUD、伤害字已接 | 在真实交战中修影响来刀阅读与操作的具体 UI 问题 | 不扩页面；整体观感待 Root 审 |
| [11 声音触觉](11-audio-haptics.md) | 13种 Foley / 雨声与消费已收；离线试听不等于端内同步 | 对真实命中 / 格挡 / 弹反画面核音画与触觉时机 | 待 Root 设备侧同步与实机触觉 |
| [12 视觉 bench](12-visual-bench.md) | UB-01v2 与单张 T-pose 条件图已交，输入图已接受；不是3D成果 | 只审03 / 05下一件灰模，给最多3条可直接制作的造型意见 | 输入冻结；不扩研究 / 概念图轮次 |

Tripo 图像条件实验保留：只用已配置 `tripo-cli`、`ov` 区域、`tripo-v3.1`，Root 统一 doctor / 余额 / dry-run / 付费。当前可用出口未通过官方 TLS，余额**未知**，没有新收费任务；网络失败不能推成余额为0或足够，不反复空转重试。不得把 API Key 或授权链接写进仓库 / 聊天。

## 制作与合入边界

唯一仓库为 `/Users/yupeng/projects/personal/pico-wuxia-arena`。Root 负责公共角色 producer / manifest 正式发布、library / app 资源、Main / HomeStage 最终接线、共享构建、设备、画面与 Git。各路只改责任目录或明确授权文件，保留同仓库他人的编辑；不复制仓库、不建 worktree、不改 `/Users/yupeng/projects/personal/pico` 或 `BrickerP.github.io`。

每路交接只保留可执行工程合同、来源 / 实物、可见变化、验证边界和下一项。Root 将具体 review 与续派写回对应交接；长期决定与教训进入 agentmemory。有限观察一次取证，不无限轮询 logcat、不无限等会话；收到可用产物就审核合入或自行补齐。离线图、单元测试、加载日志与实际游戏画面分开验收。
