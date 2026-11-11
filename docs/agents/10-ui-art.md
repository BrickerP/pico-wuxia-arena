# 10 · 中式UI美术与空间信息设计

## 当前状态

Root实图准备页裁切已回修：开始主动作固定，教学改四步，只有当前说明正文内滚动；160/240/400协议不变。候选编译及24项回归、带设计JSON样式门通过。最新回修范围、SHA和验证边界见文末；Root需重建后取同机位ready图验证。

## 目标

把当前大黑面板、小字与普通资源条提升为克制、有质感的中式游戏UI。参考目标游戏的信息层次、纸墨／朱砂／暗金与器物气质，保持VR清晰阅读和操作反馈。

## 所有权

负责 content/ArenaHud.kt、DamagePopupText.kt、新ui目录与app/res内自有UI资源、设计包和本文件。Main／HomeStage最终容器与Attachment接线由Root负责，交最小集成点。伤害timeline正确性、CombatImpact与输入规则保持原逻辑。

## 当前基线

最新主线有真实伤害、600ms／8cm四槽跳字，已修同batch覆盖与fatal保护，状态牌按玩家yaw转向。代码109项所选回归通过，实际图 artifacts/ui-input/current-scene.png。交战控制面板已有160dp／桌面240dp紧凑版，准备／暂停400dp说明版，保留暂停与重开。

## 制作队列

1. 先按PICO空间设计流程制作可审设计包／预览，给准备、交战、暂停、换轮、结算五状态。使用当前Full Stage和Attachment，优先可读层次和战斗视野。
2. 明确中文字体、数字样式、敌人身份、生命／精力／气、来刀提示、弹反／要害与结算。可加入原创印章、刀痕、细笔触等可辨元素，保留标准控件语义与hover／haptics。
3. 写Compose前读取spatial-ui-design-style和所需能力／组件官方指南。PicoTheme原生语义角色保持，项目自有装饰色单独命名。新字体／图纹必须可核对授权，沿既有资源组织。
4. 文本按真实物理阅读距离设计，避免把桌面像素图当VR验收。伤害数字透明背景、稳定深度与不遮脸／刀路仍参与评审。
5. 设计自审后直接实现责任代码，保留现有回调和可用入口。交Root真实Compose与资源、状态对照、接线差异与样式检查结果。

## 首轮交付

一套清楚显示目标方向的可运行UI预览与至少准备／交战两个状态的实际代码。随后完善暂停、结算、出招与击中UI动效。

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

实际Compose宿主隔离图取证正在`ArtSource/refinement/ui-native-preview/`进行：本机缺layoutlib实现及原生图形引擎，正在独立目录有界补齐Robolectric Native Graphics，不触碰项目根Gradle/生产依赖/设备。此阶段没有以Web或仿绘图片声称Compose图已生成。

## Root本轮组合审核与续派（2026-11-11）

审核：dac9f5e5实际图首式教学、键位与上下式完整，准备页裁切回修开发接收。

下一步：交战/结算沿现控制语义做视觉节奏，先交现Compose实际隔离图；Root已修HUD phase时钟过滤导致印记/反馈冻结的缺陷。
