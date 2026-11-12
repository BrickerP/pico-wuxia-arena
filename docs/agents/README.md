# 并行制作与 Root 审核入口

## 当前交付合同

整体仍为开发预览，人物/动作/打击品质未通过。Kotlin + PICO Spatial SDK6.1.9，Space Pro/OS6、Full Stage；唯一产品路径是原生源码→APK→PICO Emulator→Space Pro，HTML/Web与新mock保持停止。

本轮UI/局部命中组合已构建并在Emulator完整通关：APK`ca26f4a9…`，336单测通过，样式0error/0warning；实际失败→重开→三轮→VICTORY 967/40HP。[完整交战片](../../ArtSource/refinement/presentation/native-ui-impact-three-rounds-2026-11-13.mp4)、[胜利图](../../ArtSource/refinement/presentation/native-ui-impact-victory-2026-11-13.png)、[证据边界](../../ArtSource/refinement/presentation/native-ui-impact-2026-11-13.json)。已公开为[native-ui-impact-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-ui-impact-2026-11-13)，固定源码a22a216、五附件SHA均核对；旧a890和9e节点保持独立。

整身Unlit白闪已移除，默认BODY不加点光，保真实短停/切向/碎屑和头手实时；无caller的表面入口与3个预载实例已移除，只保6个实际SOFT/METAL槽。现有游戏架构未改，通用模板架构gate仍不clean；不得把构建/三轮通关写成整体品质达标。

Root已实看新图并续派两处真实问题：02修source闭握长指/拇指；08修宽灰刀轨；10修终局纸牌被近身NPC/刀遮挡及重复信息。三路只做原生候选，正式app/构建/设备/Git由Root统一。已交64da整立面、上劈v9、近场配光仍待Root下一轮原生接入；03衣片与05发型没有可发布新角色。

## Root审核重点与下一交付

1. 当前UI/局部命中包已通过真实失败→重开→三轮胜利；不重复把这条主链写成待开局。Root下一轮接已交64da立面与近场光，按同一实际视点比较人物/刀面/窗檐。
2. 01的v9低头改善接受进入候选重导。唯一producer目前硬要求106键，v9为211键/120Hz；须同步OVERHEAD合同、authoring_manifest与三target重导/typed，LEFT/RIGHT仍106。不能降采样绕过或直接把preview装包，重点看.50–.65s快抬头。
3. 02修默认R闭握长指/拇指的真实绕柄；08修细刃光与alpha渐隐，拒绝新增30cm空间门把合法快挥轨迹丢掉；10修终局遮挡与重复信息。三路只交原生候选，Root接实际APK。
4. 03先交可接受的完整guard衣形，失败物理笼不传入正式高模；05保脸眼，缺新源不再绕曲线/参数盘髻。所有新形体仍需正常视距与动态组合，不能靠数值或导入通过。
5. 剩余真实分支是玩家PARRY、HMD闪避、技能/处决、暂停/恢复/超时/追踪中断，以及Space Pro声音/触觉/性能/舒适度。保已有规则和真实SDK来源，不为通过测试造事件或扩模式。整体品质未达标，目标继续active。

## 各方向收件与下一项

下表为工程交付状态；“待 Root”代表收件 / 合入关卡，不是质量已通过。具体来源、SHA、限制与制作文件以各路交接为准。

| 方向 | 当前实物 / 审核结论 | 最重要下一交付 | Root 接力 |
| --- | --- | --- | --- |
| [01 动作](01-combat.md) | fine-overhead v7：1.75 秒完整源、五姿态与同机位前后片已交；正式仍是既有 10clip / 六步 walk | 同一招经 Root 审阅后的刀路、接触与收招修正，不新增招式 | 待完整动作审核与重导决策 |
| [02 手刀](02-input.md) | 原生双手版本 `71c39091…`，共 10,578 面 / 5.47MB；离线开发集成接受，资源与接线已入工作树 | 原生实际闭握、左右映射与前臂截口画面，修具体贴合问题 | 原生已显示；source闭握精修续派 |
| [03 服装](03-art.md) | 一次真实 Cloth 求解在 F06 健康门停止；腕口挤压、肩肘大形未改善；未传高模、未烘焙 | Root 选定结构修复或新源后，先交结构正确的完整 guard 灰模；不得沿失败笼继续参数循环 | Root已续派真实二维衣片结构；无可发布新衣 |
| [04 独立效果审阅](04-benchmark-qa.md) | 原生片已审：10.296611s 整身白闪，12.080411 / 12.455311s 黑刀面遮脸；未把单目重叠判成确定穿模 | 对修后实际交战片核这两处可见问题及独立粒子细节 | 现有问题已可派修，待修后画面 |
| [05 头发](05-hero-face.md) | direct-high 侧面仅小幅收益，背面仍扇形刻槽；冻结为 partial，未正式发布 | 一次受控新源到达后只适配发区，保既有脸眼，交连续汇根与盘结灰模 | 待 Root 新源；不追加曲线 / 参数盘髻 |
| [06 场景](06-environment.md) | 整庭院 `64da2798…` 已交：四地层 / 五上层共享窗、近檐瓦口 / 滴水；零新增图片 / 材质，有整立面与 1.5m 对照 | Root 审同机位整体收益、原生材质及实际绘制 / 内存预算 | Root已目视接受开发整合，待原生替换；正式仍9b |
| [07 光影](07-lookdev.md) | 已签名 albedo 已发布；Web IBL 候选冻结；原生 `native-nearfield.patch/json` 为未应用数值提案 | Root 受控应用近场提案，交同场景近脸 / 刀刃前后画面 | 候选待 Root 审 / 接；不改已签名 albedo |
| [08 运行效果](08-impact-vfx.md) | 薄 core / 切向 scar / 分层碎屑已进9e，SOFT / METAL 实际消费已证；5资源存在不等于5类触发全通 | 修明确遮挡并取得实际接触细节画面；核真实闪避等入口再消费已有资源 | 本轮已合入；宽灰刀轨精修续派 |
| [09 bank / 接线](09-combat-direction.md) | 正式 locomotion / typed 基础已收；网页消费者工作保留独立外观标签；新增 hurt 数据已由 Root 正式重发 | 收口受击 source clock、typed 与 runtime 一致性，交原生动作 / 判定对齐 | HIT源钟接线已合入；不混入网页扩世界 |
| [10 UI](10-ui-art.md) | 既有四页教学、HUD、伤害字已接 | 在真实交战中修影响来刀阅读与操作的具体 UI 问题 | 已合入并通关；下一项终局遮挡修复 |
| [11 声音触觉](11-audio-haptics.md) | 13种 Foley / 雨声与消费已收；离线试听不等于端内同步 | 对真实命中 / 格挡 / 弹反画面核音画与触觉时机 | 待 Root 设备侧同步与实机触觉 |
| [12 视觉 bench](12-visual-bench.md) | UB-01v2 与单张 T-pose 条件图已交，输入图已接受；不是3D成果 | 只审03 / 05下一件灰模，给最多3条可直接制作的造型意见 | 输入冻结；不扩研究 / 概念图轮次 |

Tripo 图像条件实验保留：只用已配置 `tripo-cli`、`ov` 区域、`tripo-v3.1`，Root 统一 doctor / 余额 / dry-run / 付费。当前可用出口未通过官方 TLS，余额**未知**，没有新收费任务；网络失败不能推成余额为0或足够，不反复空转重试。不得把 API Key 或授权链接写进仓库 / 聊天。

## 制作与合入边界

唯一仓库为 `/Users/yupeng/projects/personal/pico-wuxia-arena`。Root 负责公共角色 producer / manifest 正式发布、library / app 资源、Main / HomeStage 最终接线、共享构建、设备、画面与 Git。各路只改责任目录或明确授权文件，保留同仓库他人的编辑；不复制仓库、不建 worktree、不改 `/Users/yupeng/projects/personal/pico` 或 `BrickerP.github.io`。

每路交接只保留可执行工程合同、来源 / 实物、可见变化、验证边界和下一项。Root 将具体 review 与续派写回对应交接；长期决定与教训进入 agentmemory。有限观察一次取证，不无限轮询 logcat、不无限等会话；收到可用产物就审核合入或自行补齐。离线图、单元测试、加载日志与实际游戏画面分开验收。
