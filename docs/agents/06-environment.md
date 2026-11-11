# 06 · 雨夜酒馆庭院整体场景

## 当前状态

2026-11-11 Root已将庭院发布至正式app资源，并以原点identity单加载接入HomeStage；两地面receiver已绑定，07正在对齐原生灯光。06交付的模型SHA已冻结，正常视距图与文档齐备；设备验收继续由Root执行。

## 目标

把当前黑背景、平直墙面和大黑缝石块的院落提升为有构图、空间层次和生活痕迹的中式雨后酒馆。参考《黑神话》的建筑与材质，《天国拯救》《骑马与砍杀》的可信空间尺度。以现短场景形成探索片段与战斗区域，玩家站立区和对砍视线清楚。

## 所有权

负责 ArtSource/refinement/environment-hero/ 与本文件。原场景和03已有environment候选只读作输入，整个环境新方向由你主导。07负责照明／天气运行，10负责UI，你交几何与材质可组合场景，不改HomeStage或正式app资产。

## 制作队列

1. 读取真实端内图 ArtSource/refinement/presentation/combat-feedback-outcome.png 和 artifacts/ui-input/current-scene.png，确定主视角构图。建立酒馆门楼、瓦檐、木柱基座、石路、墙根、排水与积水的连续结构。
2. 用Blender和现制作逻辑完成真实GLB升级。石板厚度／倒角／缝宽、木构榫接／门槛／瓦片层次要在正常视距可见。纹理采用原有资产或可核对授权来源，给物理尺度、baseColor／normal／roughness。
3. 构建前景灯笼与屋檐、中景对手与门楼、远景雨雾／小镇轮廓。可在侧面加入池水或小桥一角形成记忆点，景观服务同一庭院风格。
4. 湿润、苔痕、污渍和破损有位置原因，低处积水、檐下干区和脚步路径不同。战斗地面以Y=0作为公共基准。
5. 场景按少量有名mesh／material分组，地面receiver与重要灯位给明确节点名。交本地包围盒、米制坐标、实体装配点和可用Root接入说明，远近层分清。

## 首轮交付

一个明显改善构图和材质层次的真实场景GLB，以及主战斗视角／侧向探索视角各一张前后图。首轮集中做好一段石路和门楼，随后扩相邻屋檐、墙角和水面。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

### 2026-11-11 · 首张PICO集成图只读评审

输入为Root实际取得的 `artifacts/integrated-polish/ready-scene.png`，2160×2158，SHA256 `c5a7a7d23c9f99b66fc418bffe01d8fcdc00a8e87a674d723905bbd0cb40186c`。候选与正式app模型只读复核仍为 `56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`。Root反馈原点装配、receiver、天气、IBL及角色10clip已加载；本图能直接证明新建筑与石路已进入PICO画面，不能仅凭单图证明所有角色/动作或运行性能。

**本图结论：** 石板相对鞋长、人物和门洞的物理尺度可信，横向错缝与窄缝可辨，没有证据要求整体缩放铺地。廊檐暗带较厚，但没有遮住对手头部、躯干或门洞；举刀上缘进入暗檐背景，需要后续举刀/侧向图继续确认视线。灯笼骨架已可见。实际瓦片上表面、完整屋脊、远景整体、侧廊进深、池沿和踏步未在本图中充分显示，不能据此宣布它们已完成端内视觉验收。

**只保留两个待选改进，均未实施：**

1. **檐口瓦当／滴水轮廓。** 主视角的连续平直蓝灰边目前比瓦片端头更醒目，建筑细节容易读成一条整齐横带。侧向图确认这是当前檐口几何的表现后，可在保留承重梁、现有檐深和中央净空的前提下，为筒瓦端部和滴水瓦增加可读端面、轻微不齐和局部磨损。只处理檐边可见轮廓，不凭这张图重做未入镜的整片屋顶。
2. **地面湿度过渡与亮缝一致性。** 当前地面仍有较连续、均匀的蓝亮边，远处读成规则网格。先让07完成曝光/IBL/高光收口；若同机位仍如此，再考虑在独立材质候选中为步行中带、边沟低处和檐下干区设置连续roughness过渡及少量逐石变化，减少所有边线同亮的感受。保留现有石板尺度、浅床和窄缝，不通过重新加大接缝或整体改尺寸解决受光问题。

当前没有本图足以证实、必须立即修改几何的阻断项。06本轮仅做图片与源码只读审核、回填本交接，没有修改模型、manifest、贴图、producer、运行代码或正常视距图，没有启动Blender、构建或设备操作。等待Root提供侧向探索图及07完成后的同机位图，再由Root选择是否制作独立新候选；若制作，明确新文件路径和新SHA，冻结56bb签名继续保留。

### 2026-11-11 · Root已接入，签名冻结

Root通知已将 `courtyard_hero.glb` 发布到 `app/src/main/assets/models/`，HomeStage改为原点identity单加载，旧三场景的运行加载路径和包内资源已移除，原ArtSource源保留；07按本模型灯位继续对齐。本会话只读核对了候选与正式app GLB，两者SHA256均为 `56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`。HomeStage源码已包含 `EH_GroundReceiver`、`EH_MortarAndDrain` 接收节点绑定。

**冻结边界：** 保持上述模型字节、现有manifest及图像身份不变。06不再运行会覆盖 `courtyard_hero.glb` 的producer，不改Root正式资源或接线。后续新几何必须写入独立候选文件／目录，并同时列出显式新SHA及相对已冻结版本的可见变化，再交Root选择；禁止在旧文件名下悄然覆盖已接入签名。当前没有新几何候选。

主视角、侧向探索前后图及0.8m／1.5m／3m常规眼高图均已完成。`candidate_manifest.json`、`after_evidence.json`、`board_receipt.json`、`validation.json` 的模型身份一致；这些图仍是冻结GLB的离线对照，不是本次Root接线后的端内验收图。当前06只完成文档和既有图像完整性核对，没有重生成资产、启动Blender、共享构建或操作设备。

下一步由Root取得实际集成画面，确认原生材质、灯光、阴影、脚底高度及Space Pro性能。06收到定向视觉问题后可继续只读分析；需要新几何时遵守上述独立候选与新SHA边界。

### 2026-11-11 · 首轮完整候选与专项自检

本轮没有修改正式producer、app资源、HomeStage、Main、Gradle、Manifest或其它会话目录；没有共享构建、设备操作、Git提交或推送。所有实物在 `ArtSource/refinement/environment-hero/`。来源代码节点 `562449af40ee984ddd8ef61be5c339ac9bea2de5`，旧酒馆来源SHA `af3adf8b15bb5aa6f34a9a5240e18bc2534bc977db4a05089a0c3a1ee1bbdc69`。

**可见结果：** 单片门墙已形成双层酒馆与两翼围廊，真实柱脚、木托、木椽和层叠瓦片构成进深；连续薄缝石路覆盖站立与战斗范围，灰缝有浅床，侧边有排水槽、苔痕及低处湿石。门前保留对砍净空，池角以湿石砌边、三块踏石和水面形成侧向记忆点。四只纸灯笼有暗色竹肋和独立灯位；茶桌、酒坛、青瓷与石盆复用旧场景已制作的精细道具。较高的相邻镇屋檐在主视角与侧视角可见，不再完全藏在主楼后。

| 产物 | 路径（相对本工程） |
| --- | --- |
| 真实GLB | `ArtSource/refinement/environment-hero/courtyard_hero.glb` |
| 可编辑源 | `ArtSource/refinement/environment-hero/courtyard_hero.blend` |
| 私有producer／PBR图生成 | `ArtSource/refinement/environment-hero/build_environment.py`、`make_textures.py` |
| 坐标、模块、灯位、SHA | `ArtSource/refinement/environment-hero/candidate_manifest.json` |
| 纹理来源、物理UV尺度、SHA | `ArtSource/refinement/environment-hero/texture_manifest.json` |
| 主视角同机位前后图 | `ArtSource/refinement/environment-hero/review/comparison_player.png` |
| 侧向探索同机位前后图 | `ArtSource/refinement/environment-hero/review/comparison_explore.png` |
| 0.8m／1.5m／3m常规眼高检查 | `ArtSource/refinement/environment-hero/review/distance_review.png` |
| 实际GLB检查 | `ArtSource/refinement/environment-hero/review/validation.json`、`validation.log` |
| 原道具选择与装配证据 | `ArtSource/refinement/environment-hero/review/props_provenance.json` |
| 前后相机／输入身份 | `ArtSource/refinement/environment-hero/review/before_evidence.json`、`after_evidence.json`、`board_receipt.json` |

候选SHA256：`56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`。最终GLB含38个活跃节点、30个mesh、151594三角、26个材质与31张内嵌图；这些是装配成本信息，不能代替可见画面或设备性能。

**Root接入：** 本候选是三份旧环境资产的整体替代方案，不是叠加补丁。加载 `EnvironmentHero_Root` 于 SDK `(0,0,0)`，identity旋转、scale=1；移除旧 `tavern_slice.glb`、`forecourt.glb`、`courtyard_details.glb` 的对应场景实例。不能继续给候选平移Z=-4，也不要再同时叠03的旧门套/铺地候选。旧道具已选择性合进新GLB，不会再需要旧details全体。

- SDK为米制、+Y向上、初始视线朝-Z；完整局部/装配包围盒 `min(-10.867,-0.120,-13.2175)`、`max(11.185,11.1773,2.917)`。高处与远处两座屋体属于远景层，中央实际铺地约10.8×9m。
- 战斗石路顶面Y=0，几何专项确认中央 `X[-1.35,1.35]、Z[-3.0,.8]、Y[.05,2.4]` 无装饰三角侵入。现角色脚底Y=.028由Root决定同步归零或保留并注明间隙；06没有改角色落脚量。
- 主地面receiver节点是 `EH_GroundReceiver`，浅床/排水是 `EH_MortarAndDrain`。它们替换旧 `Paving`、`SidePaving_Geometry` 的receiver选择。raised侧廊可按需另选 `EH_SideGalleryWalls`。
- `EH_Light_Lantern_01..04` 为07/Root原生暖点光装配点；精确位置见manifest。主门两灯 Stage `(-2.15,2.7,-4.7)`、`(2.15,2.7,-4.7)`；侧廊两灯 `(-4.03,2.25,.56)`、`(4.03,2.25,-1.32)`。`EH_Light_CourtMoon` 是冷色高位光参考，`EH_CombatClearCenter` 是地面判定参考。GLB不携带运行灯光和相机。
- baseColor／normal／roughness可直接随GLB使用。花岗岩和木材来自项目现有Poly Haven CC0扫描图；屋瓦、灰墙、苔痕为本项目原始烘图，旧酒坛/茶具/灯笼纸图来源继承 `ArtSource/tavern/README.md`，没有新外部素材或付费生成。木纹沿梁柱长轴，墙根潮痕使用有高度含义的UV，法线为OpenGL切线空间。

**验证与自我review：** `python3 ArtSource/refinement/environment-hero/verify_environment.py`，7项全部通过：身份与无孤儿节点、Y=0覆盖、战斗净空、筒瓦外法线、可移植PBR及有限坐标、无运行灯光/相机/动画、截断GLB拒绝路径。前后均使用同一1.6m眼高、18mm/36mm镜头、1200方图、同一受控灯光；after由交付GLB重新导入后渲染，未使用仅存在于.blend的材质。两张并列图只加文字边框，没有修图。旧forecourt的孤儿节点通过既有active-scene过滤排除。

四轮review已覆盖：正确性（修复筒瓦反面并加GLB检查、地面基准、净空）；可维护性（候选只一条producer路径、重用已有道具与过滤器）；体验/i18n（正常站立图、中文“酒”牌、近侧廊光线视线）；漂移（无新依赖、SDK/配置/schema/正式资源变更）。审查指出的远景遮挡、石池误用木材、灯笼椭球、木纹方向已在最终候选中实际修正。

**当前限制：** 图是离线资产对照，不是PICO端内图。原生IBL、水面反射、阴影receiver、生效材质、帧率/发热、Space Pro双眼舒适度尚未验证。水面采用不透明低roughness薄面，未加入折射或依赖特殊透明排序。场景无碰撞或新导航系统；当前固定近身交战入口保持Root现有链路。部分瓦面为薄壳双面材质，筒瓦受光法线已经专项核对。

**已继续的队列与下一步：** 首轮石路/门楼后已继续完成两翼屋檐、墙根排水、池角水面、远景屋檐及三档距离图；当前06制作队列的可独立部分已产出。Root可按上面的互斥替换说明实际装配；07使用命名灯位做原生夜雨光色。下一项有意义的证据是Root接线后的同眼位端内图，06随后据实际光照修材质与遮挡，不以离线图宣称VR体验已完成。

## Root组合审核与下一步

已核对完整courtyard_hero SHA56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8，离线主视角显示建筑体量、连续细缝铺地和庭院层次有可见升级，接受开发集成。Root已发布单一courtyard_hero入口并删除旧三份运行场景，原ArtSource保持。两个实际receiver已绑定，灯位由07按新anchors适配。原生构建与250项组合回归通过，实际画面尚待本轮取图。随后优先按原生图修正材质尺度、瓦檐薄弱处和探索侧景，不再增加同类随机道具。

## Root本轮组合审核与续派（2026-11-11）

审核：courtyard_hero已作为唯一主场景实际启动，旧三运行资源已移除；两层酒馆与连续石路可见。

下一步：根据relight-ready-scene实际图集中建筑材质尺度、窗纸与人物亮度层次的最多3个可见改进；不增开放世界或再造并行院落。
