# 10 · 中式UI美术与空间信息设计

## 当前状态与Root审核

`next-polish/ui-polish.patch`已由Root精确应用到ArenaHud，当前源SHA`097e46fc…`。APK`ca26f4a9…`已构建并在PICO Emulator实际完成失败→重开→三轮→胜利967/40HP；336项当前单测通过，UI样式0错误/0警告。正式app现已修改，旧“候选/未改app/待共享构建”都是制作时快照。Full Stage、400×160/400与500×260、原生actions/确认链、ready/quality/来源门槛保持。

Root实际审图接受战斗信息区精简的运行集成，整体视觉未通过。DEFEAT时近身NPC/刀遮部分左侧纸牌，VICTORY/DEFEAT顶栏与结算内容仍重复；Space Pro手势、hover/haptics、放大字体和暂停恢复实际操作未验。

当前仅在`ArtSource/refinement/ui-native-preview/terminal-occlusion/`交下一原生修复。基于`artifacts/native-ui-impact-2026-11-13/current-terminal.png`与`three-round-final.png`，用最小源码patch改善终局可读与操作，不加页面/新窗口/HTML或mock，不用缩小字体/纸牌掩盖遮挡。保现有state/actions与确认链；若需改HomeStage空间关系，先核真实owner/坐标与公开SDK，交Root最小接入建议，不以未测bbox宣称安全。Root持有正式源码、构建、Emulator、Git。

当前控制牌仍Position=(-0.6,1.2,-1.75)、yaw20°，不擅自套旧A/B值。只推进已授权原生任务，不能接入的研究/重复渲染停止。

## 目标

把当前大黑面板、小字与普通资源条提升为克制、有质感的中式游戏UI。参考目标游戏的信息层次、纸墨／朱砂／暗金与器物气质，保持VR清晰阅读和操作反馈。

## 所有权

当前唯一可写责任为ArtSource/refinement/ui-native-preview/next-polish/与本文件，交可映射现有state/action的原生Kotlin最小源码patch。正式ArenaHud/其他app源码由Root合入；Main/HomeStage最终接线、Gradle、设备、Git提交与发布也由Root统一。保留他人编辑，不扩玩法、入口或宏，伤害timeline/CombatImpact/输入规则不改。

## 当前基线

最新主线有真实伤害、600ms／8cm四槽跳字，已修同batch覆盖与fatal保护，状态牌按玩家yaw转向。代码109项所选回归通过，实际图 artifacts/ui-input/current-scene.png。交战控制面板已有160dp／桌面240dp紧凑版，准备／暂停400dp说明版，保留暂停与重开。

## 制作队列

1. 以现有真实APK画面与state/action链为基线，只交可接入Kotlin/PICO Spatial SDK6.1.9 APK的源码或原生资源；准备、交战、暂停、换轮、结算仍使用当前Full Stage与Attachment。不新增或维护HTML/Web/Three.js，不以浏览器或mock充当游戏验收。
2. 明确中文字体、数字样式、敌人身份、生命／精力／气、来刀提示、弹反／要害与结算。可加入原创印章、刀痕、细笔触等可辨元素，保留标准控件语义与hover／haptics。
3. 写Compose前读取spatial-ui-design-style和所需能力／组件官方指南。PicoTheme原生语义角色保持，项目自有装饰色单独命名。新字体／图纹必须可核对授权，沿既有资源组织。
4. 文本按真实物理阅读距离设计，避免把桌面像素图当VR验收。伤害数字透明背景、稳定深度与不遮脸／刀路仍参与评审。
5. 自审后在候选目录制作最小原生源码patch，保留现有回调、机制反馈和可点击入口。交Root明确目标文件、基线SHA、公有API检查与接入差异；正式实现由Root合入，不能接入的研究/报告或重复渲染立即停止。

## 首轮交付

一份可进入现有原生APK的最小Compose补丁与准确state/action映射。Root在PICO Emulator验证、终端Space Pro/OS6验收；历史Web/mock保留作过程资料，不是产品交付或原生验收。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

由负责会话填写真实产物与review问题。


### 2026-11-11 · 第一阶段：真实UI代码已制作，候选检查进行中

来源：`562449af40ee984ddd8ef61be5c339ac9bea2de5`。本会话未创建分支、worktree或提交，未运行共享Gradle或操作设备。读过实际端内基线图，已通过agentmemory本地REST中文检索取回中式氛围、动作优先、实机画面评审偏好（当前会话未暴露memory MCP工具）。

已制作：
- `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt`：纸色准备/暂停/结算，朱砂“试”印，交战紧凑墨色内容区；敌名24sp与敌血主条，阶段22sp、方向42×34，三项自身资源次层。结算得分44sp。原400×160/240/400与500×260 Attachment协议不变，所有回调、ready/pending/resume gates与重开确认保留。
- 同目录 `DamagePopupText.kt`：透明44sp有阴影数字；要害/护身/致命18sp短标签。未修改Timeline、四槽、600ms、8cm、致命保护。
- 新 `ui/ArenaUiPalette.kt`、`ui/ArenaPresentation.kt` 与 `res/values/arena_ui_art.xml`：自有颜料token，原生PicoTheme语义角色不改；威胁方向只在正常交战、输入就绪的PREPARING/STARTUP/ACTIVE出现，收势和暂停不残留。
- `app/src/test/java/com/example/wuxiaarena/p0d2f0182/ui/ArenaPresentationTest.kt`：威胁窗口正例与收势、暂停、追踪丢失、非交战边界。
- `ArtSource/refinement/ui-design/` 正在制作五状态可触发设计预览；`ArtSource/refinement/ui-validation/`负责隔离候选检查，避免共享构建争用。

当前验证：实际SDK6.1.9 AAR类型已检查；首遍 `verify-design-style.sh` 对责任源码与9个自有颜色通过，0 errors、0 warnings；该遍未带尚在制作的design-spec，因此不宣称surface追踪已通过。`git diff --check`通过。完整候选编译、JUnit、设计JSON追踪待下一阶段回填。

最小接入：当前Main/HomeStage已调用两个同名Composable，无新容器或接线需求；Root只需正常共享构建合入这些源码与res。未编辑Main、HomeStage、manifest、producer、library或正式模型。

限制：目前未取得本轮新UI的端内图，Web预览只证明布局和状态，不证明0.8m/1.5m/3m实机可读。Root需用同机位截图及Space Pro验证字号、刀路遮挡和hover。下一项继续候选编译、五状态预览视觉检查及带spec样式门，完成后更新SHA与结果。

### 2026-11-11 · 第二阶段交付：五状态与战斗文字动效候选可审

首轮已完成真实源码、可运行的五状态设计包与定向验证，来源基线仍为 `562449af40ee984ddd8ef61be5c339ac9bea2de5`。本轮没有正式APK、没有端内新图；下列Web图只证明布局和状态可达。

可见变化与实物：
- [准备图](../../ArtSource/refinement/ui-design/ready-preview.png)、[交战图](../../ArtSource/refinement/ui-design/fighting-preview.png)、[暂停图](../../ArtSource/refinement/ui-design/paused-preview.png)、[换轮图](../../ArtSource/refinement/ui-design/round-clear-preview.png)、[结算图](../../ArtSource/refinement/ui-design/victory-preview.png)。旧端内图仍为 `artifacts/ui-input/current-scene.png`，不能把不同渲染来源拼成端内前后对照。
- [可运行预览](../../ArtSource/refinement/ui-design/preview.html)、[设计说明](../../ArtSource/refinement/ui-design/design-doc.md)、[唯一设计JSON](../../ArtSource/refinement/ui-design/design-spec.json)；revision 7，五状态可切、重开取消/确认可达，含普通/要害/护身/致命四张透明跳字样本。九张PNG来自revision 5静态布局；revision 6/7只补实际动效契约与静态最终尺度，未声称新增动态浏览器证据。
- 实际出招印章随真实PREPARING `phaseElapsedNanos / preparationNanos` 从0.94变为1；STARTUP/ACTIVE维持1。命中/要害/护身/弹反文字仅在FIGHTING、输入就绪且HIT phase的160ms内从1.04回落到1，暂停或无关反馈为1。只改graphicsLayer绘制，不引入UI时钟、不变布局或战斗判定。
- 默认字体尺度下原生交战约138/160dp，桌面约234/240dp；状态区最重样本缩小gap后约243/260dp。是静态容量检查，字体放大和实体字形仍待端内观察。

验证结果：
- `python3 ArtSource/refinement/ui-validation/validate_candidate.py`：真实strings用aapt2/javac生成候选R，Kotlin 2.1.20 + Compose compiler 2.1.20隔离编译通过。四个责任Kotlin文件与新测试被快照并记SHA，`current_sources_match=true`。只读已有编译产物作为依赖；没有调用共享Gradle、写app/build、安装APK或操作设备。
- JUnit `ArenaPresentationTest`（4项新用例）＋`DamagePopupTimelineTest`＋`ArenaSessionTest`，**24项全部通过**。新用例含真实威胁窗口、收势/暂停/追踪丢失、除零、负elapsed、Long.MAX_VALUE、动效终点与非命中反馈。已有两类回归使用Root上轮编译的baseline类；其他会话正在改运行时，因此Root最终共享构建仍须重跑完整所选回归。
- [候选验证JSON](../../ArtSource/refinement/ui-validation/validation.json)、[编译日志](../../ArtSource/refinement/ui-validation/kotlin-compile.log)、[JUnit日志](../../ArtSource/refinement/ui-validation/junit.log)。
- `verify-design-style.sh`：责任源码＋9个design-color＋最终design-spec，**0 error / 0 warning**，两处有界surface追踪通过；日志见 `ArtSource/refinement/ui-validation/design-style.log`。设计JSON schema、HTML嵌入一致性、引用与surface检查通过，证据见 `ui-design/validation.json`。
- 自审与独立四项review完成：correctness保留全部gates/回调与尺寸；maintainability只抽取颜料与纯展示计算；UX/i18n修正数字locale、伤害单次朗读及fatal→guarded→head优先级；drift无依赖/Gradle/manifest/schema改变。`git diff --check`责任文件通过。

接入合同与PICO样式核对：
- Main→HomeStage既有两个Attachment→两个同名Composable链保持；不需要Root增加容器、Attachment或回调。Root正常合入责任源码与res即可，正式模型及其发布路径不涉及本轮。
- 标准组件：`com.pico.spatial.ui.design` 的Text、Button、Badge、LinearProgressIndicator，`design.windows.AlertDialog`。每个公开面板与跳字入口仍包PicoTheme；按钮slot继承组件foreground，hover/音效/触觉沿标准组件，没有自制hover或新增haptic事件。
- 9个app-owned颜色集中在 `ui/ArenaUiPalette.kt` 并与JSON对应；原生16个ColorScheme角色保持。control/status外结构透明，只有一个有界内容面；无装饰边线或嵌套app surface，未创建WindowContainer/Augment，未触碰系统根玻璃、Stage背景或manifest开关。
- 中文字体走系统Serif/Sans，未分发新字体、图片或纹理；“试”为原生Badge中的正文字，避免未知授权素材。Space Pro实际中文Serif回退待验。

仍需Root验证：最终当前工作树共享构建与完整回归、新端内同机位前后图、Space Pro的0.8m/1.5m/3m整体读字与刀路遮挡、字体放大、原生按钮hover/触觉及动态强调。本轮沿用status最低阅读距离1.8m，0.8m/1.5m目标不能据Web声称通过；若要改变空间锚点由Root决定。本UI已完成制作与本责任范围验证，下一项为Root统一构建/端内review后的具体回修。

最终文件指纹（SHA-256）：

| 文件 | SHA-256 |
| --- | --- |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt` | `91e38500fbff3d21ced188eb5ec0ed0cb3d86c8231e532783b7458115273f0cc` |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/DamagePopupText.kt` | `e336d5cbf45d40eff4d9bfa741a355472caf8c56e51313a26a4ebb054f4dfdc0` |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/ui/ArenaUiPalette.kt` | `95517b55f9933baf78648e3c5bdc3f379fbd91b0848f84963cad01c4cb750c41` |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/ui/ArenaPresentation.kt` | `c8fe297eb889a0b3f1613aeab0a7a84a0be5e16441f73bc2272f0c52ef0ad9a9` |
| `app/src/test/java/com/example/wuxiaarena/p0d2f0182/ui/ArenaPresentationTest.kt` | `52d12c341deddb293c38aa001561594a7902c3eb343f0a6995d91eec54511713` |
| `app/src/main/res/values/arena_ui_art.xml` | `deb9349cca4e1a0b833507083242ada9f9daee04d9a32aba93a544e5d3949755` |
| `ArtSource/refinement/ui-design/design-spec.json` | `d14681a508e0f4a36aa9057503290135eb16f01aa6ec1caf717669112d7a9938` |
| `ArtSource/refinement/ui-design/preview.html` | `02bb5ec06d1132150c0b5e20d5086d2892bc2615577eb06513c0efc8ff28c222` |

### 2026-11-11 · Root集成冻结与端内审核支持

Root已接手共享Gradle与实际取图，paper/ink方向已由12路离线接受。此后本路不并发修改已交 `ArenaHud.kt`、`DamagePopupText.kt`、`ui/ArenaUiPalette.kt`、`ui/ArenaPresentation.kt`、`arena_ui_art.xml` 或其测试；不重建APK、不碰设备。收到具体端内缺陷后才恢复对应代码回修。冻结时六项责任文件SHA与第二阶段交付完全一致。

只读核对：默认字号静态容量无阻塞，FIGHTING原生控制约138/160dp、状态最重组合约243/260dp；DEFEAT纸页400dp可容纳结算。尚不能由此宣布端内阅读通过。Root取图时可直接看：
1. FIGHTING的“试炼进行中”、暂停与重新开局完整，底边不裁按钮。
2. 顶部24sp敌名、22sp阶段、方向印章层级分明；印章只在蓄势/起势/出招出现，收势后消失。
3. 自身气血/体力/气势三列及当前/最大数字不挤压截尾；低血量颜色清楚。
4. 蓄势条、长弹反反馈、连击同时存在时仍落在墨色内容区，缩放强调不碰底边或连击。
5. DEFEAT切换纸色400dp页：本次落败、本局已结、44sp得分、最佳分、再挑战齐全；无方向牌，超时顶部反馈显示“试炼时间已尽”。

只读复审未发现新的运行代码问题。为支持Root将补独立DEFEAT/超时结算Web样本，沿用五类状态版式，不改变运行代码、配色、尺寸或真实战斗逻辑；其截图仍仅作Web布局验证。

### 2026-11-11 · 冻结期预览补充：DEFEAT与超时

- 新增 [普通落败图](../../ArtSource/refinement/ui-design/defeat-preview.png) 与 [超时落败图](../../ArtSource/refinement/ui-design/defeat-timeout-preview.png)。第五类仍为结算版式，内部布局id沿用victory，样本明确为`result=DEFEAT`；未增加真实游戏状态或产品调试入口。
- QA可用 `__arenaPreview.setSettlementSample('defeat' | 'defeat-timeout')` 注入样本。普通落败反馈为“调整架势与节奏，再战一局。”；超时反馈为“试炼时间已尽”。“再挑战”实际回到ready样本。
- revision 8只更新`ArtSource/refinement/ui-design/`和本交接。浏览器正文clientHeight/scrollHeight均194px，落败两种样本无裁切；schema、内嵌JSON一致性、surface与最小浏览器检查通过（0 error / 0 warning）。已目视核对两图，但它们依然仅证明Web布局容量。
- 冻结后再次逐文件比较：运行源码、颜色、资源与测试六项SHA与已交候选全部一致，未重跑共享/候选构建或操作设备。Root取图与最终回归继续由Root负责。

当前预览文件SHA-256（替代第二阶段表中的设计产物指纹，运行文件指纹不变）：

| 文件 | SHA-256 |
| --- | --- |
| `ArtSource/refinement/ui-design/design-spec.json` | `2fb1c7d6beabf7ef935345bbd7f65b6f38f0b4f749b578121452358aced7fdc0` |
| `ArtSource/refinement/ui-design/preview.html` | `7c51d0a3312a1baac1fdd158b2e23ade0bfa8f7f5a10651a41932ffbb40d99c9` |
| `ArtSource/refinement/ui-design/validation.json` | `416c9e673bff8232954f1d8e1e52cc8cad7f710dc793dac5d2075fb1d983171e` |
| `ArtSource/refinement/ui-design/defeat-preview.png` | `33291d6a7baa6f55b38081c7082f18f2679383087643ff7111378df1b2024876` |
| `ArtSource/refinement/ui-design/defeat-timeout-preview.png` | `1053140a84cae96f299dac709804e4d70e8a9605e8c7ffe10d57624e5be7cf26` |

## Root组合审核与下一步

纸墨五状态方向离线接受，现有开始/暂停/恢复/重开及透明数字入口已直接使用新Compose，原生构建和250项组合回归通过。实际1.5m阅读、上方状态牌边缘和对手脸/刀路遮挡待本轮取图。角色模型与新场景一并变化时，实际Root图不作为严格旧版A/B，只验本版使用效果。运行源码先冻结，待Root回图后作一轮有依据的视觉收口。

### 2026-11-11 · READY实图裁切回修（已交候选，等待Root端内复核）

来源：当前Git节点`380dd46b1cfa6aaf54ef54bc44535b5af330b62d`，Root提供 `artifacts/integrated-polish/ready-scene.png`（Root报告APK前缀`8ebe75ac`）。已目视确认旧图桌面准备页只露刀术标题，正文在400dp首屏之外。

根因：顶部固定区扣除后body约194dp，旧桌面分支先放重复预演说明、两排始终disabled的DesktopActions和三行键盘help，随后才排完整TechniqueGuide。此前静态估算与简化Web样本没有覆盖这条实际分支，不能据此判定首屏教学可读。相关教训已更正保存至agentmemory。

实际修改只有运行文件`ArenaHud.kt`与`res/values/arena_ui_art.xml`，另更新设计包、隔离验证实物与本文：
- 开始/继续/重开主动作仍固定在上方，回调与所有ready/pending/resume条件保持；正常输入就绪时显示试炼目标，追踪等待仍显示必要的输入状态。
- 删除非交战模式中始终不可用的五个招式按钮与重复技术说明；桌面FIGHTING的真实可用五动作入口完整保留。
- 关键教学改四步：进刀、架刀、避锋、破势。顶部单排“刀术要诀＋当前招名＋1/4”，正文采用原完整中文说明16sp/22行高；桌面附对应键位14sp/18行高，原生不显示键位。没有缩小教学字号或截断正文。
- 教学占剩余高度，Small40dp上一式/下一式固定底部；仅当前说明体可内滚动，`key(page)`翻页重置滚动。索引限制0–3、首尾禁用，等待追踪时仍可翻页；没有新增读完教学才能开始的门槛。
- FIGHTING原生160／桌面240、准备/暂停/结算400、顶部状态牌和结算MatchSummary路径保持。Main/HomeStage、manifest、palette、伤害字和战斗运行时均未修改。

检查与实物：
- `python3 ArtSource/refinement/ui-validation/validate_candidate.py`真实资源aapt2/javac与Kotlin/Compose隔离编译通过；定向JUnit **24项通过**；`current_sources_match=true`。本轮是布局缺陷回修，没有新增战斗逻辑或调用共享Gradle。
- 最终revision9设计JSON的 `verify-design-style.sh` **0 error / 0 warning**；独立四项review未发现新的callback/gate、weight/scroll、i18n或漂移问题；责任文件`git diff --check`通过。
- [桌面第1式](../../ArtSource/refinement/ui-design/teaching-desktop-1.png)、[第2式](../../ArtSource/refinement/ui-design/teaching-desktop-2.png)、[第3式](../../ArtSource/refinement/ui-design/teaching-desktop-3.png)、[第4式](../../ArtSource/refinement/ui-design/teaching-desktop-4.png)、[原生第4式](../../ArtSource/refinement/ui-design/teaching-native-4.png)、[暂停桌面第4式](../../ArtSource/refinement/ui-design/teaching-paused-desktop-4.png)。
- Web在固定400×400下实测guide194dp、正文视口114dp，完整四页正文与键位均不超出，导航底内缩20dp；真实触发翻页1→4及4→3、首尾禁用和滚动复位。Schema、JSON嵌入一致性、surface门通过。以上是Web容量证据，不能充当Android/VR截图或真实手柄输入证据。

Root复核：重建同一工程后取同机位READY图，确认首式完整说明、键位与翻页全部在纸面中；实际点到第4式，确认气满破势/虚弱处决完整；另看原生/暂停分支。当前上方状态牌整体在画面内，但竖直实物刀刃穿过状态牌右侧和脸部，后续FIGHTING/结算图应分辨字体可读与刀路遮挡；本路未通过缩字或改Main/HomeStage回避它。

此回修可直接由Root共享构建接入，未重建APK或操作设备。代码到此收口，在Root下一张端内图/缺陷前不再并发变动已交候选。

本轮最终SHA-256（替代旧UI源码/资源及设计产物指纹，其余已交运行文件不变）：

| 文件 | SHA-256 |
| --- | --- |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt` | `c045f183c103276b27ee2667848507882afcf3b96b437676bab2a81af3057bcf` |
| `app/src/main/res/values/arena_ui_art.xml` | `e7e818550b88afc2dcf3e9abdc1eed125e22342b6551407f2db27caf9afc6330` |
| `ArtSource/refinement/ui-design/design-spec.json` | `207d5b7dd34d21a84e2eecb9038643c7eaeb66c261f8964240b9cdac87a31020` |
| `ArtSource/refinement/ui-design/preview.html` | `ed41ab06ae9c1a1efd2d4cef71867d246a8c04ab0843b9a358bdf0c179b05daf` |
| `ArtSource/refinement/ui-validation/validation.json` | `d7ea8fa8de3a0e4dd943c21b33fad4e99b19736f54d928b7824b2911b8d12393` |

### 2026-11-11 · 新阶段：冻结源码，交战/结算独立渲染取证

Root已接收`relight-ready-scene.png`（报告APK dac9f5e5、250项回归通过）的准备页首屏：完整说明、键位、上下式均在纸面内；真实翻页点击尚由Root同一输入probe验证。本路继续冻结已交运行代码/配色/res，当前只做独立资源与阅读审核。

新增`ArtSource/refinement/ui-review/combat-settlement/`：源绑定8个实际Compose布局样本、`palette-readability.json`和`review.md`。发现超时终局可残留combo>=2的暗金连击，已保留到timeout样本；本轮未改代码，待Root看图续派。

实际Compose宿主隔离图取证已在`ArtSource/refinement/ui-native-preview/`完成：独立补齐Robolectric Native Graphics后，直接调用冻结正式Compose出图，不触碰项目根Gradle/生产依赖/设备。图片没有使用Web或仿绘替代。

### 2026-11-11 · 交战/结算实际Compose隔离图交付

运行源码、配色、资源保持冻结，六项当前SHA与源绑定样本完全一致。8例×两个现有面板，共16张PNG，均直接调用冻结正式ArenaHud的ArenaControlPanel/ArenaStatusPanel，经Robolectric4.17 Native Graphics、Android35、mdpi在ComposeView中绘制。没有重写UI、修改正式app、启动设备或运行项目根Gradle。

优先review/Root触发对应端内状态：
- [原生交战状态牌](../../ArtSource/refinement/ui-native-preview/images/fighting-native-ArenaStatusPanel.png)
- [桌面交战控制](../../ArtSource/refinement/ui-native-preview/images/fighting-desktop-ArenaControlPanel.png)
- [蓄势与处决就绪](../../ArtSource/refinement/ui-native-preview/images/fighting-charge-execution-ready-ArenaStatusPanel.png)
- [弹反首帧](../../ArtSource/refinement/ui-native-preview/images/fighting-parry-ArenaStatusPanel.png)
- [通关结算](../../ArtSource/refinement/ui-native-preview/images/victory-ArenaControlPanel.png)
- [超时落败状态牌](../../ArtSource/refinement/ui-native-preview/images/defeat-timeout-ArenaStatusPanel.png)

真实执行：Native Bitmap像素断言PASS，实际Compose八例绘制PASS；两个fixture方法均按JUnit真实wasSuccessful结果通过，driver退出码0，无下载或renderer JVM遗留。最初运行包下载受限，最终只补缺段并通过完整ZIP CRC及官方Maven checksum校验；当前报告已替代早期未出图的调查结果，不把旧Stub错误归因PICO。

主agent目视8张、独立ui_review目视5张；16张全部核验尺寸、alpha、多色内容与SHA。原生160/桌面240按钮、长中文提示、三资源当前/最大值、结算44sp得分/最佳/余血均未见裁切或重叠。弹反1.04强调略偏统一左线，仍在墨色区域内。纸墨层级与留白可用于当前Root实图对照，本轮未追加装饰或功能。

一处已证实问题：超时状态牌同时显示“试炼时间已尽”与暗金“连击5”。finishDefeat(TIMEOUT)保留combo，状态牌仅以combo>=2显示；本轮保留现行为出图、没有修改运行源码，建议Root下一次定向隐藏终局连击。

证据与复现：
- `ArtSource/refinement/ui-native-preview/renderer-report.json`：完整执行、16图、输入二进制与各SHA，最终SHA `fd6341de73b56a3f7d812127895ebb0446f67b63e7b5ad7bc1f231d5473983c8`。
- `ui-native-preview/README.md`、`ActualComposeFixture.kt`、`run_actual_fixture.py`：实际调用入口、复现与限制。冻结输入app-classes SHA `97d1a12c3a320d033ab529208a2ecd41c439130eb4257bc6e44826e7b9e03af2`，真实R.jar SHA `86116f4a6966aece45cf3b43a3f7de52a9b8fc40874f37e57d33b3ca2746e2f1`，资源APK SHA `dcb753e4aa1189e37848b1baa2262b58288aeb6e7d605d19bb736d4e776b0cb7`。
- `ArtSource/refinement/ui-review/combat-settlement/render-review.json`：最终图像指纹、主agent/独立目视范围与结论；`review.md`提供阅读审核、颜色边界与官方工具资料；`snapshot-cases.json`提供8个源码绑定样本。

范围限制：这是非空间Android宿主的实际Compose输出，使用宿主Android字体、人工ViewState与no-op回调，背景不含FullStage。它证明组件边界与中文排版，不能证明PICO合成、正常0.8m/1.5m/3m视距、挥刀/脸部遮挡、真实翻页点击或hover/haptics。Root可以据这些隔离图触发对应FIGHTING/VICTORY/DEFEAT状态，继续场景帧与输入probe。下载依赖/冻结APK/缓存已由候选目录局部gitignore排除，Root正式发布只需挑选实际所需产物，不引入生产依赖。

### 2026-11-11 · 终局连击徽记修复候选（Root直接授权）

基线为公开节点`193d0f6dcc859168b8f7c00669c185a3863e1a8d`及原生APK `8d1e456e027c9ac14243e65db9171f5998909dd80400189f0451f0e1d99a6ede`。本轮是下一轮候选，不重写已发布身份，不把候选图/测试结果标作已部署验收。

实际改动仅三个责任文件：
- `ui/ArenaPresentation.kt`：新增纯展示函数`arenaShowsCombo(result, combo)`，条件为combo>=2且结果不是VICTORY/DEFEAT。
- `content/ArenaHud.kt`：状态牌唯一连击显示条件调用上述函数；整段终局连击Text节点移除，反馈可使用释放的宽度。
- `ui/ArenaPresentationTest.kt`：新增3项回归，正常FIGHTING连击2/5与ROUND_CLEAR5保留，两终局的0/1/2/5/Int.MAX_VALUE全部隐藏，各结果的combo<2均隐藏。

运行时combo、计分、最佳分、暂停、反馈、输入、资源与所有尺寸协议保持。Main/HomeStage、正式资产、manifest、Gradle和Git均未操作。

验证：
- Kotlin/Compose隔离候选编译通过，定向JUnit **27项通过**，源码SHA与当前文件匹配；样式门仍0 error/0 warning。证据单独复制至`ArtSource/refinement/ui-review/terminal-combo-fix/`，含`candidate.patch`、`unit-validation.json`、编译/JUnit/样式日志与`candidate.json`。
- 在独立`ui-native-preview/terminal-combo-candidate/`用公开8d1e456e的真实R/APK和冻结classes为底，Kotlin/Compose编译本轮两源overlay，优先加载候选UI。NativeBitmap与ActualCompose测试均通过，driver退出0；3例共5张实际候选PNG，无残留进程。
- [交战combo5仍显示](../../ArtSource/refinement/ui-native-preview/terminal-combo-candidate/images/fighting-combo5-ArenaStatusPanel.png)、[超时落败不显示连击](../../ArtSource/refinement/ui-native-preview/terminal-combo-candidate/images/defeat-timeout-combo5-ArenaStatusPanel.png)、[胜利不显示连击](../../ArtSource/refinement/ui-native-preview/terminal-combo-candidate/images/victory-combo5-ArenaStatusPanel.png)。两张纸色结算控制图得分310/860、最佳1200保持，渲染日志中的输入combo始终仍为5。
- 修后timeout与旧实际图仅416像素变化，差异框`[435,195,480,212]`正是原暗金连击区域；两张纸色结算控制图与旧图逐像素一致。主agent目视5图，独立复审3张状态牌，未见裁切或版式回归。
- 原16张宿主图、原renderer-report和原输入身份SHA逐项未变；候选另存，没有覆盖历史证据。独立四项review确认只读展示判断，无状态写入、依赖或配置漂移。

候选渲染报告：`ArtSource/refinement/ui-native-preview/terminal-combo-candidate/candidate-report.json`，SHA `ebf38ef525244d65440d16065fbb3099453132b01e17aa1e95a2b2a920a94eba`。修后超时PNG SHA `621967fdfbe0959e1ad32aa9212a09306b03350477348d6eab8f6a4144076db6`。

本轮源文件SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `ArenaHud.kt` | `7339febc548ee20249e5953d110df96e857f9fffe78d9e22959c1b48a70340fb` |
| `ui/ArenaPresentation.kt` | `5af112df8201a27a7297419f33b247bab39d8c687b3bff5bff58da5d8f938bb2` |
| `ui/ArenaPresentationTest.kt` | `86cd4a89a09ddc5390a4552dcecd404cb7ea7209f3a4a50ca2d90d47ddeb193d` |

尚未验证：Root下一轮共享Gradle/整体回归、安装后的真实TIMEOUT/VICTORY帧与FullStage阅读。本轮没有运行根Gradle、安装或操作设备；由Root按此三文件候选进入下一轮集成。

## Root本轮组合审核与续派（2026-11-11）

审核：dac9f5e5实际图首式教学、键位与上下式完整，准备页裁切回修开发接收。

下一步：交战/结算沿现控制语义做视觉节奏，先交现Compose实际隔离图；Root已修HUD phase时钟过滤导致印记/反馈冻结的缺陷。

### 2026-11-11 · 原生输入UI收敛完成与接口冻结

来源节点：`fd58c04f9b8bc8a0999f633d149fb2897164e53f`。Root已经通过真实Shift+E观测SDK右手Y独立变化0.01m（`artifacts/input-native/right-shift-e.*`），输入侧统一模拟器/硬件原生头手通路。UI按这条已授权路径收敛，不添加替代动作或输入判定。

冻结接口：
- `ArenaControlPanel(state, controlsAvailable, controlPending, onStart, onPause, onResume, onRestart)`：只有四个试炼控制回调，已删除onDesktopAction公开/私有参数及转发。
- `arenaControlPanelHeightDp(result, pauseReason)`：两个参数，无暂停的COUNTDOWN/FIGHTING/ROUND_CLEAR统一160；READY/VICTORY/DEFEAT或暂停400。
- ArenaHud已删除DesktopActions五按钮、DesktopCombatAction/DesktopCombatInput依赖；desktop仅为`state.inputOrigin == InputOrigin.DESKTOP`。它只选择教学文案，不生成动作，不按Build硬件或全局预演开关推断。
- Main已由输入侧移除onDesktopAction。本路确认时高度调用尚留第三个Build.HARDWARE/desktop参数，Root明确接手删除。只需把该调用改为两参数；本路未编辑Main/HomeStage或其他输入worker文件。

教学保持原有四页和分页控件，无新窗口/控件：来源未就绪或原生VR仍显示四条通用实体动作说明；DESKTOP改为四页“模拟器操作”：控制模式、移动虚拟手、动作识别、头手分开。模式指引按Root实证要求：右下RightControllerMode、ControllerButtonMode开启、Keyboard文本模式关闭；Shift+W/A/S/D/Q/E平移右手、鼠标转腕或瞄准、左键确认。头部用于视角与身体闪避，虚拟手柄位姿用于出刀与架刀；单按W不执行预制挥刀。每页只有完整16sp/22行高正文，不再叠第三个旧keys提示块；`key(desktop,page)`在来源或页码改变时重置正文滚动。关键主操作与翻页footer固定。

资源清理：移除四个arena_ui_keys_*与旧arena_keyboard_help、五个arena_preview_*动作label、arena_preview_instruction；arena_input_desktop改“模拟器虚拟手柄”。终局combo纯展示修复、分数/最佳/历史combo、全部ready/pending/resume gate与开始/暂停/恢复/重开动作保留，战斗规则未改。

检查结果：
- 真实资源aapt2/javac与Kotlin/Compose隔离编译通过；27项定向JUnit通过。更新后的DamagePopupTimelineTest源码已纳入候选编译，覆盖三类compact160、三类非compact400以及两种暂停400，不再用旧二进制的240预期。
- 独立四项review无控制/资源/漂移问题；来源切换滚动复位边界已收口；责任源码`git diff --check`通过。样式门0 error/0 warning，两个有界surface及原配色保持。
- 最小设计包revision11已同步实际XML、独立四页desktop、native四招、160/400和终局combo隐藏；schema、内嵌JSON一致性、surface门0 error/0 warning。没有浏览器/Native新截图，原16图和终局5图保留为旧接口历史容量证据，不能标作本轮新布局验收。
- 独立证据在 `ArtSource/refinement/ui-review/native-input-convergence/`：handoff.json、unit-validation.json、编译/JUnit/样式日志；源快照和当前SHA匹配。

Root下一步：按冻结两参数高度调用接线并共享构建/整体回归；本路不运行根Gradle、不操作设备、不改正式asset或Git。真实头手输入与Attachment点击沿Root输入probe验收；新接口原生隔离图后置，不为图延迟构建。

最终文件SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt` | `8899445473ce1f2cb73dc262e64b85418e36a04528333f1e017dbb64429464ca` |
| `app/src/main/res/values/strings.xml` | `b1cdab95aa2fe0ac0e24cdaebf1a1872de237872508bf5f8d15f6016ab2e10eb` |
| `app/src/main/res/values/arena_ui_art.xml` | `4e3023dcd6a2ae28a77fc982efeee9001980d125b3b30f20e8c1e5323f08a583` |
| `app/src/test/java/com/example/wuxiaarena/p0d2f0182/content/DamagePopupTimelineTest.kt` | `2d7d774b9d175322d1cd2ce4cb4e2ada63580eab9aa2565c989b078a1b35936a` |
| `ArtSource/refinement/ui-design/design-spec.json` | `41a271ac60071255ca7143b7112fedb413282e501495370ec0a433a8e27201f3` |
| `ArtSource/refinement/ui-design/preview.html` | `4e4f46dd6b02e06669b2e8f2a07cdcc08eee39009df713ad349630161392da51` |

### 2026-11-11 · 未就绪时模拟器配置帮助方案（仅文档，代码继续冻结）

Root实测边界：冷启233原生输入包场景正常，Controller provider返回PENDING/DEVICE_NOT_SUPPORTED、尚无hand数据；head已观测到DESKTOP。当前GUI“输入来源待确认”后只显示VR通用教学，用户难以知道如何启用虚拟控制器。本轮不改代码、资源、设计包、测试或安全门，只给待Root数据定位后选择的方案。

源码原因已核对：ArenaSession.viewState的inputOrigin取dominantHand.stamp.origin；head存在而hand缺失时该值为null。ArenaHud只以state.inputOrigin==DESKTOP选择模拟器教学。因此这次需要分开“帮助的宿主/来源上下文”和“已收到可用于动作的完整观察”，不能等inputReady才提供配置帮助。

推荐A：Root把已接受的head DESKTOP来源提前传到现有state.inputOrigin。
- 仍优先当前snapshot中真实dominant-hand origin；hand缺失时，才使用同一快照、当前epoch/generation内已接受head的DESKTOP来源。不要从未接受的原始日志、旧generation缓存或场景已加载推断。
- 先限定DESKTOP补全，解决当前“模拟器head已到、hand未到”情形；不能将head存在解释为手柄已连接或有效。
- UI可以沿现有单一state.inputOrigin分支显示配置页，避免新增一条动作输入路径或全局预演开关。inputReady仍由snapshot.hasRequiredObservations，actionReady仍由原baseline与scene条件产生，resumeReady和SDK能力门保持。
- 若全部观察清空，来源回到未知；不能为保留帮助复用旧观察。明确hand来源不能被head/宿主覆盖，混合来源的诊断和原有安全判定保留。
- 该字段也被CombatHapticContacts与PlayerBladeTrail消费，并非纯UI专用。Root落地前应复核：DESKTOP不会触发硬件haptic；来源变化可清trail但不能在inputReady=false时采样或绘制新刀轨。不能笼统称“只改展示字段就没有其他影响”。

方案B：状态接口暂时冻结时，已明确ranchu的宿主上下文只选择配置帮助。
- 仅在缺少明确观察来源、且Root已确认宿主为ranchu时，允许显示“模拟器配置 · 等待手柄数据”。它是帮助上下文，不写state.inputOrigin，不赋值inputReady/actionReady/resumeReady，也不宣称硬件已就绪。
- 复用Root已有的宿主判定，不恢复DesktopCombatInput或HMD-derived宏，不用虚拟手几何可见性替代SDK观察。未知宿主仍保留通用实体动作说明；明确PICO/hand来源优先，不靠宿主判断抹平冲突。
- 优点是全部追踪丢失时仍有配置入口；代价是教学选择多一项宿主上下文，需与数据来源标签分清。Root若采用A即已解决当前head先到的情况，可先不引入B；是否补足“零观察但明确ranchu”的帮助入口另由Root选定。

共同UI表现与边界：
- PENDING或DEVICE_NOT_SUPPORTED且已知模拟器时，配置帮助仍可见；标题可为“模拟器配置”，状态文案用“等待虚拟手柄数据”。不要写“手柄已连接”“已启用”或承诺打开选项即可解除能力不支持。
- 首配置页包含右下RightControllerMode、ControllerButtonMode开、Keyboard文本模式关；后续页为Shift+W/A/S/D/Q/E平移虚拟右手、鼠标转腕/瞄准/左键确认与头手分工。来源确认DESKTOP后应从配置页开始并重置正文滚动，避免沿用通用教学的末页。
- 下一式/上一式等本地帮助操作不应依赖输入就绪；开始/恢复继续沿原gate，不能通过“已读教程”或宿主提示放行。
- 保留PENDING与DEVICE_NOT_SUPPORTED各自真实诊断。显示帮助不等于SDK能力已恢复；不新增手数据、不调整Unsupported处理、不绕过baseline或原生动作识别。

最小待验矩阵：

| 当前观察/宿主 | 帮助/来源预期 | 必须保持 |
| --- | --- | --- |
| accepted head DESKTOP、无hand、PENDING | A显示模拟器配置；B仅明确ranchu时显示 | inputReady/actionReady不变，开始禁用 |
| 同上、DEVICE_NOT_SUPPORTED | 帮助仍可见，保留能力失败诊断 | Unsupported不放宽 |
| 无head/hand、明确ranchu | A来源未知；B可显示配置帮助且不冒充来源 | 所有ready不恢复 |
| 无观察、宿主未知 | 通用动作说明，不断言是模拟器或硬件 | 开始禁用 |
| 完整DESKTOP head/hand | 模拟器教材、实际DESKTOP来源 | 仅原判定决定就绪 |
| 完整PICO head/hand | 实体VR四招、PICO来源 | 硬件流程不变 |
| hand明确来源与head/宿主不一致 | hand优先，保留冲突诊断 | 不用展示选择改数据判定 |
| 中断先清hand后清全部观察 | A按当前快照退回未知；B可保留已知宿主帮助 | 不复用旧epoch，不恢复ready |

每例一起记录head/hand的origin与epoch/generation、界面教材、provider状态、inputReady/actionReady/resumeReady以及开始按钮；单看教程出现不能算输入接通。

本轮执行范围：只更新10文档并做只读源码核对/独立方案审查。ArenaHud冻结SHA仍为8899445473ce1f2cb73dc262e64b85418e36a04528333f1e017dbb64429464ca，其余UI源/资源/测试指纹同上一阶段；未运行编译、测试、设备或新渲染。等Root完成本轮数据/输入gate定位再指定实现路径。

### 2026-11-11 · ranchu等待态配置帮助最小实现（SOURCE FROZEN）

Root已选方案B。本轮Main只加Build import和isRanchuHost展示参数；ArenaControlPanel透传后仅用于arenaShowsEmulatorGuide(inputOrigin,isRanchuHost)选择教材。规则：明确DESKTOP始终显示；仅来源null可由ranchu补足；PICO/SYNTHETIC不被宿主覆盖；null且非ranchu仍用通用说明。帮助切换重置页码/正文滚动。控制模式首屏明确Right Controller、Controller Button Mode启用、Keyboard文本关闭和Shift组合键移动虚拟手。

数据来源标签仍可显示“输入来源待确认”，输入未就绪时开始/恢复继续禁用。没有修改ArenaViewState、ArenaSession、inputReady、actionReady、quality、Unsupported、触觉或刀轨来源，Main Start receipt及其余接线保留；黑点瞄准无receipt或Start浅粉问题不通过放宽UI gate处理。

4项新用例覆盖null+ranchu正常路径、DESKTOP两种宿主、PICO/SYNTHETIC不可覆盖边界、null+未知宿主边界。既有隔离专项现一并编译Main和UI：Kotlin/Compose通过，33项JUnit通过，样式0 error/0 warning，源快照匹配，独立四项review无新增问题。本地专项补全了已缓存的同名Spatial DSL/UI foundation classpath，没有改项目依赖或运行共享Gradle。

证据：ArtSource/refinement/ui-review/ranchu-help/ 下handoff.json、unit-validation.json和编译/JUnit/样式日志。冻结Main SHA e689c605837775e27fd2a008f3d1cb4ba7fc16c1c32a8e5fdc5f8399e66bb727；ArenaHud SHA e9711f73a6578fbfe9c3cf413dfe43257dcdadb7814b3db475eae6fc30ba6a12。Root可立即在下一APK纳入此展示修复；未跑设备、共享Gradle或Git，未更新截图集，实际waiting界面与Attachment点击由Root新包观察。

### 2026-11-11 · 767bc0af控制牌安全区：只读pose建议

已目视 `artifacts/canonical-native/full-stage-settled.png`（2160×2158）与 `reset-controller-view.png`（模拟器窗口）。前者纸面左边缘及文字出界，后者完整且位置相对更右；两图的视点/取景范围未对齐，不能据此默认是SDK故障。

实际HomeStage：controlPosition=(-0.85,1.15,-1.45)，controlRotation=(0,0.2923717,0,0.9563048)，即yaw约+34°；HUD_WORLD_SCALE=1.4。Attachment为CENTER，准备/暂停/结算400×400、交战400×160，中心与朝向不随高度改变，宽度始终400。因此160紧凑态只收上下边，不会消除横向出界；本轮不改UI尺寸或字体。

A 推荐，优先边缘余量：
Position=(-0.55,1.05,-1.85)；Quat=(0,0.1391731,0,0.9902681)，yaw +16°。
scale=1.4保持；右收30cm、后移40cm、降低10cm，留中央脸部净空，文字角尺寸会略小。

B 偏可读，降低纸面：
Position=(-0.48,0.95,-1.60)；Quat=(0,0.1478094,0,0.9890159)，yaw +17°。
scale=1.4保持；字更大、纸面更低，但需要更多低头，内侧边缘更接近手部活动区。

这两组把名义正视横向中心角从约左30.4°收至左16.6°/16.7°，是位置方案，不是已通过的可见性证明。实际米制宽高取决于LocalPhysicalLengthConverter，当前未读取设备值，不由400dp直接假定物理尺寸。

Root只需择一改既有controlPosition/controlRotation；update与首次attach已共用这两个值，不另加位置路径。建议先A，用同一正视复位机位取400dp准备页，目标左右至少留约5%画幅（2160图约108px，仅本轮观察目标），完整看见四边、首屏说明和分页；再看160dp战斗牌，内缘不要越入敌人脸/持刀的实际包围区。小幅左右转头和一段挥刀另验，不能承诺固定世界牌在所有头位/刀帧都始终无遮挡。若A字过小再比较B，不因窗口截图完整就省略FullStage复拍。

本轮只读源码与看两图，未修改HomeStage、Main、教程、安全门、控件或宏，未运行构建/设备；冻结UI五项指纹与上一阶段一致。Root拥有HomeStage应用和native复验。

### 2026-11-11 · Root已应用pose的只读核对（不改源码）

Root当前值：Position=(-0.6,1.2,-1.75)，Quat=(0,0.17364818,0,0.98480775)，yaw +20°，HUD_WORLD_SCALE仍1.4。它优先于上一节未采用A/B；本路不再提出替换或扩大研究。

核对未见明确HIGH。相对旧值，右收25cm、后移30cm、抬高5cm；名义正视中心角从左30.4°收至左18.9°，20°朝向与中心方位接近。水平距离约1.68m增至1.85m，同一实体尺寸的字角尺寸会稍小。

物理尺寸本身未变：准备/暂停/结算400×400、战斗400×160、scale1.4，CENTER锚点保持；160只缩上下边，宽度仍400。绝对米宽高依赖当前PhysicalLengthConverter，本轮没有设备实值，不能把估算写成已测尺寸。

剩余是待native复拍的可见性风险：400页抬高后的上缘与脸部/持刀区、当前取景左边余量、近身挥刀经过时的内侧边缘。固定世界pose不能保证所有头位和刀帧无遮挡；当前没有已证实的高风险，因此不给另一组数值打断Root构建。按同一正视复位机位先验400页完整，再验160战斗和短挥刀帧；两种截图相机不同不直接归因SDK。

本路本轮只修改10交接；HomeStage由Root应用，Main/教程/安全门均未触碰，无新控件/面板/宏，无构建或设备操作。

### 2026-11-13 · 9e画面UI精修首轮实物（候选制作中）

唯一写入工作范围为ArtSource/refinement/ui-native-preview/next-polish/与本文；正式app、浏览器主试玩、Gradle、设备与Git均不操作。基线取ArtSource/refinement/presentation/native-input-contact-2026-11-12.png，源码与图像SHA已固定于next-polish/source-baseline.json。

首项实物：next-polish/mock/fighting-same-view-mock.png，图内明确MOCK/设计示意/非原生验收；HTML对照页已停止维护且不作为交付；仅保留标明MOCK的PNG和原生Kotlin候选。使用内置ImageGen编辑参考图，完整prompt在mock/prompt.txt；生成图参照原机位/人物/刀路，但不是场景像素一致性或代码字体证明。

方案：正常交战控制区去掉重复试炼标题、目标和轮次，保留印章、暂停/重开原生按钮及确认链；敌人状态区以透明结构和必要的小范围承载替代大墨块，敌名/轮次/敌血主层，架势/方向独立，玩家三资源与短时反馈完整。待机与近期受到攻击不是重复项；敌人蓄势与玩家收刀蓄势也不能合并。没有架势HP字段，不虚构新数值。

已交ui-polish.patch仅修改ArenaHud.kt，映射现有state/action；Root负责正式合入、构建和PICO Emulator状态验收。候选未写入app。

### 2026-11-13 · 原生UI精修单文件候选交付（收口，Root合入）

按用户最新纠偏，本轮只以可进入原生APK的源码patch为交付。HTML/Web/Three.js、浏览器游戏、新HTML mock和不能接入的研究/重复渲染已停止；此前已创建的HTML与生成mock保留历史、不维护、不删除他人文件、不作为原生验收。当前没有扩展任务，不再为回报制造新工作。

唯一目标为正式`app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt`。候选在`ArtSource/refinement/ui-native-preview/next-polish/candidate/src/app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt`，统一diff为`next-polish/ui-polish.patch`，由Python difflib生成，没有运行Git。正式app源码未改，Root独占合入、构建、设备和发布。

最小变化：
- 正常FIGHTING控制区改透明，仅保留原生Small40暂停/重开和28dp试印；不缩点击目标。暂停为朱砂，重开为低优先墨色，确认链与全部控制gates不变。去掉此处重复试炼标题、目标和轮次；COUNTDOWN/ROUND_CLEAR真实秒数、controlPending、场景/输入等待文本仍保留。
- 状态牌去掉整块墨底，结构透明；现有敌名/轮次/时间、敌血分母、阶段/方向、三项玩家资源、短时攻防事件、蓄势/收刀复位/处决条件完整。4个数字用原生Badge作局部承托，其余文字使用与现跳字同类的轻量Shadow，未加app装饰边框或覆盖PicoTheme角色。
- feedbackLabel只把最后默认“目标在范围内”兜底改为不显示；全部14种事件、低资源、距离不足、敌人护身、执行、追踪中断、倒计时、换轮和终局优先级仍在。敌人阶段与近期反馈各自保留，不把“待机＋受到攻击”错误去重。没有新增架势HP、技能或UI计时器。
- 准备/暂停/结算纸页、教程、开始/恢复条件、pending禁用、重开确认、终局combo隐藏、400×160/400和500×260槽位及公开接口保留。Palette、ArenaPresentation、Main/HomeStage、输入/战斗规则都没有候选改动。

核对依据为当前PICO SpatialUI6.1.9公有Button/Badge/LinearProgressIndicator/Text/AlertDialog与PicoTheme契约；没有使用私有token。候选单文件Kotlin2.1.20+Compose隔离编译PASS，未运行Gradle；样式门0 error/0 warning，扫描包含未改palette快照。未提供新完整设计IR，R10 IR追踪没有冒充通过；源码层无嵌套app填充/装饰边框，原生Badge背景属组件处理。

独立四项审查未发现HIGH/阻塞：所有动作callback与gates保留，阶段/反馈映射完整。默认资源列约142.7dp，标签与76dp数值Badge约132dp；理论最重状态约251/260dp，Root仍须原生核字和底边，不能用数字估算充当通过。Badge实际内容宽约68dp，100/100、放大字体、亮窗/灯笼后的透明标签、长提示+combo+charge和点击/hover/haptics均待APK中复验。

先前生成mock仅说明方向，与候选存在差异：mock敌血单排而源码上下两排；源码有4个暗底数字Badge；mock的斜角/描边/印章肌理和字形不是候选承诺。它不证明空间尺寸、原生文字、点击或刀线无遮挡。正式实现一律以源码patch为准。

Root接入：先核对当前ArenaHud基线SHA，再仅应用这一文件的patch；没有Main/HomeStage或资源接线要求。保持既有原生头手通路与所有安全门，统一由Root共享构建，并在PICO Emulator/Space Pro复验实际9e同机位及正常视距。

交付指纹：
- 基线ArenaHud：`e9711f73a6578fbfe9c3cf413dfe43257dcdadb7814b3db475eae6fc30ba6a12`。
- 候选ArenaHud：`097e46fc72552fe3d2df1109284a0eaef4d0f9de408eea416f2c0842d6737f51`。
- `next-polish/ui-polish.patch`：`8dab16ec3dc852ca3470b65d26ae5c580c75348848d8dad5b7631ff8264fd7fc`。
- `next-polish/candidate/candidate-report.json`含编译、样式、不变量、基线/候选及输入SHA；`next-polish/delivery.json`为本轮最终接入摘要，README明确原生唯一产品合同。

本轮至此停止，等待Root对原生候选的真实集成结果再派具体工作。
