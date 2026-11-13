# 并行制作与 Root 审核入口

## 当前交付合同

唯一仓库 `/Users/yupeng/projects/personal/pico-wuxia-arena`，Kotlin＋PICO Spatial SDK6.1.9、Space Pro／OS6、Full Stage。唯一产品路径为原生源码→APK→PICO Emulator→Space Pro。整体人物、动作、打击品质仍未通过，成品Demo未完成；不扩地点、模式或底层规则。

已发布 [native-visual-v9-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-visual-v9-2026-11-13)，固定源码bfaf53b、APK1c41cfc3…；8附件大小与SHA核对，最终349单测全过。真实SDK头手／鼠标完成Start→三角色→VICTORY895／60HP→实际Retry回READY。[52秒主片](../../ArtSource/refinement/presentation/native-visual-v9-three-rounds-2026-11-13.mp4)、[重试片](../../ArtSource/refinement/presentation/native-visual-v9-retry-2026-11-13.mp4)、[验收边界](../../ArtSource/refinement/presentation/native-visual-v9-2026-11-13.json)。旧ca26／a22／967分节点保持独立，不混用证明。

正式资源已包含211键v9上劈、右手v2闭握、64da整面庭院、近场光、薄刀轨、终局UI。Root已实际看源审图、原生准备／交战／胜利／重试画面；不以测试或三轮通关代替整体品质。引擎附件视觉AABB仍UNOBSERVED，未伪报数值PASS；主机录像fps不代表设备性能。

## 本轮审核与续派

| 方向 | Root审核与正式状态 | 下一明确任务 |
| --- | --- | --- |
| [01 动作](01-combat.md) | v9三角色/binding365578/typed/profile齐套正式发布，OVERHEAD211键、左右各106；输入真实且已通关 | 仅据实际原片复核.50–.65快抬头、肩肘与手刀，最多3条可见意见；未确证问题不做v10或再渲染 |
| [02 手刀](02-input.md) | 3a1be1dd右手v2已源审、装包与原生显示，闭握新增指间交叉清除；旧掌背/腕口仍保留 | 冻结v2，不再闭握参数扫描。后续据明确原生问题继续掌腕表面，不能称全部抓松曲线零穿模 |
| [03 服装](03-art.md) | 既有Cloth／松弛／guard静态候选均未形成可发布整衣 | Root已续派一次REST衣片结构收敛：真实缝共享拓扑、开放领腕下摆、保脸手腰裤78骨；先可绑定完整GLB，不模拟、不UV/bake、不重启旧参数循环 |
| [05 头发](05-hero-face.md) | 旧发髻partial未发布，新发型未通过 | 保脸眼和现正式源；等待Root一次受控Tripo新源，不继续曲线/参数盘髻 |
| [06 场景](06-environment.md) | 正式64da已原生显示／通关。2f9a8774合批只作冻结A/B备选：提交估算109→80，唯一VB+5.55MB，未证明硬件收益 | 本阶段结束，不继续新几何或渲染；实际Space Pro瓶颈且Root指定后才重启A/B |
| [07 光影](07-lookdev.md) | 三行近场光已进入正式包；原生仍见黑刀面及部分近脸偏白 | 按实际GLB/KTX通道与灯-刀-视线几何找根因，交现有材质/灯的单变量最小候选；不加新灯、全局曝光/IBL、HTML或扫描 |
| [08 刀轨/接触](08-impact-vfx.md) | 75d1薄刀轨已合入，30cm门已移除；真实SOFT/METAL消费有证据，像素可读性未批准 | 据52秒原片追enable→几何提交→材质/vertexColor alpha；只交真实根因与一件私有修正，不凭公开API或数值宣称已渲染 |
| [10 UI](10-ui-art.md) | 终局文本/摆位已合入并实际可点Retry；不再以“未开局”为阻塞 | 冻结当前结构。保留ECS visual bounds不可观测事实，不能用期望尺寸冒充实测 |

[04独立效果审阅](04-benchmark-qa.md)、[09 bank接线](09-combat-direction.md)、[11声音触觉](11-audio-haptics.md)、[12视觉bench](12-visual-bench.md)保持各自职责，现有源码/来源保留，不因idle另造研究、页面、素材或新系统。声音触觉仍需真实设备同步验收，离线WAV与消费日志不能代替听感。

## 验收边界

仍待玩家PARRY、HMD动作闪避、技能/处决、暂停/恢复/超时/追踪中断，以及Space Pro性能、持续运行、舒适度和声音触觉。保已有机制和真实SDK来源，不造事件、不扩大判定或增加玩法来通过检查。整体目标继续active。

Tripo仅用已安装tripo-cli、ov官方区域、tripo-v3.1；Root统一doctor/余额/dry-run/付费。当前官方API的TLS仍未打通、余额未知、无新收费任务。不能将网络错误推成余额0或足够；不重登或空转重试。API Key与授权材料不得进入仓库或聊天。

## 制作与合入边界

Root独占公共角色producer/manifest、library/app正式资源、Main/HomeStage最终接线、共享构建、设备、画面、Git与发布。各路只改责任目录或明确授权文件，保留他人编辑；不复制仓库、不建worktree，不改pico或个人网站仓库。停止HTML/Web/Three.js游戏、浏览器试玩、网页光照和新mock；已有文件仅保留历史。

交接文件是工程合同与验收产物：写清源/实物、可见变化、验证边界、review和下一项。长期决定/偏好/教训只能进agentmemory。有限检查一次取证，不无限轮询logcat或等会话；可用产物由Root直接取件、审核、合入或补齐。源审、单测、原生像素和真机验收分别取证，不混称通过。
