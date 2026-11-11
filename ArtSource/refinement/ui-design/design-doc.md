# 酒馆试炼 · 试刀印

范围：`web_design_validation_only`。这是现有 Full Stage / Attachment 的 UI 设计与布局验证产物，不是端内截图、VR 舒适性结论或新的游戏逻辑。源码基线为 `562449af40ee984ddd8ef61be5c339ac9bea2de5`。本目录只负责设计产物；实际 Compose 在 `ArenaHud.kt`、`DamagePopupText.kt` 与 `ui/ArenaUiPalette.kt`，由 UI 执行负责人实现。

## Frame

站立玩家的主要视觉任务是读对手与刀路，HUD 的任务是扫视后回到攻防。准备、暂停、结算时允许有仪式感的标题；交战时控制区缩成两行文字和按钮。敌人姓名、主要血条、当前起势优先于玩家三项资源与持久操作说明。

空间价值来自位置与方向：敌人状态留在对手上方，操作入口留在左侧场边。二维反事实是在屏幕四角贴 HUD；若直接照搬到 VR，会把同样内容硬塞到中央视野，夺走对手轮廓与手部动作。既有两个 Attachment 的位置和朝向保持，不增加浮窗、腕部跟随、深度动画或需玩家转头寻找的新入口。

假设：既有 Attachment 距离与 500×260/400×160/400 协议继续有效（高置信；Root 才能改接线）。实体 PICO 字体会回退到系统中文 Serif/Sans（中置信，需端内验字形）。16sp 提示、14sp 资源在当前位置可读（待验证，不能以本 Web 图证明）。

## Explore 与选择

| 方案 | 信息结构与空间形式 | 效率与题材表达 | 主要风险 | 结论 |
| --- | --- | --- | --- | --- |
| 单一悬挂榜匾 | 将控制、资源、技法合并成对手上方的大匾 | 一处读完、器物感明显 | 抬眼阅读多、遮建筑和对手上沿，战斗时持续面积过大 | 拒绝 |
| 腕部护符＋对手姓名牌 | 玩家资源附手腕，目标仅姓名和来势 | 中央视野最空，身体空间关系强 | 需要新 Attachment、稳定追踪与抬腕动作；偏离现有输入和接线 | 拒绝 |
| 场边纸墨双态 | 准备纸页，交战轻墨窄条；敌人上方独立状态牌 | 用已有两个位置完成操作和扫视，状态变化肉眼明显 | 浅纸与雨后亮背景的对比、远距小字需实际验收 | 采用 |

签名是朱砂方印正文字“试”，不是图标，也不代替按钮。它只出现在纸页状态。无新增字体、纹理或第三方图片，无素材许可依赖。

## Plan

所有实现事实以 `design-spec.json` revision 9 为准。原生 16 个 `PicoTheme.colorScheme` 角色保持同名 Vibrant 引用。自有颜料在 `theme.brandColors` 与 `ArenaUiPalette` 中独立声明：纸白、墨黑、轻墨 veil、朱砂、暗金、淡灰、玉青、余烬红。没有覆盖系统主题角色。

Stage Attachment 外根透明；只有 `control-surface` 与 `status-surface` 拥有有界内容 fill。纸态只有一个纸色内容面；交战态用轻墨内容面。没有额外 WindowContainer、Augment 或系统根玻璃改动。预览的浅灰背景仅是 Web 环境背景，不是应用表面。默认面板大小沿用现有协议，Web 的 dp→px 只用于布局预览。

文字规则：场边标题 Serif 28sp，状态24sp；交战控制标题20sp，回合/说明14sp；敌名24sp、阶段22sp、提示/反馈16sp、资源14sp；结算分数 Serif44sp。阿拉伯数字保留实际值/最大值。方向朱砂牌只在交战真实威胁的样本中出现；追踪等待与错误样本隐藏方向牌并禁用控制。

```text
准备 / 暂停 / 结算                   交战 / 换轮
┌ 内容区域，无装饰边线 ┐             状态标题           轮次
  [试] 酒馆试炼     轮次              简短状态说明
  状态标题                           暂停   重新开局
  简短状态说明
  主操作 / 次操作                     对手名             轮次·时间
  技法 或 结算                        敌方生命 + 主资源条
                                      起势               来势
                                      提示
                                      生命     体力     气势
                                      反馈
```

## 状态与真实运行边界

| 状态 | 主要任务与焦点 | 样本入口与出口 |
| --- | --- | --- |
| ready | 看懂试炼目的，开始 | 开始试炼 → fighting |
| fighting | 看敌血、来势、资源，保留刀路 | 暂停 → paused；展示样本事件 → round-clear |
| paused | 停稳并决定继续或重开 | 继续 → fighting；重开确认 → ready |
| round-clear | 明确此轮已破、收刀等待 | 展示样本事件 → victory；重开确认 → ready |
| victory | 读取分数和余血，再战 | 再挑战 → ready |

Web 不是战斗模拟器。`dataCases.*.stateSamples` 是独立布局样本：准备用第一场，交战/结算用最终场；开始时切换的是样本，不证明从第一场打到了第三场。默认 Web 展示在交战7秒后显示换轮、再3.5秒后显示最终结算，全部计时事实写在 actions payload。真实应用仍由 `ArenaSession`、伤害 timeline、既有输入回调和轮次判定驱动，不采用这些 Web 展示计时。

`normal`、`fallback`、`error` 走同一树。后两者用于缺少观察与追踪中断布局，控件禁用，不显示来势。没有加产品中不存在的数据模式开关；QA 通过 `window.__arenaPreview` 注入样本。

## 组件映射

| 内容/操作 | SpatialUI Web | API 来源 | 事件/状态 |
| --- | --- | --- | --- |
| 开始、暂停、继续、重开、再挑战 | `sui-button` | vendored `js/button.js` | `click-action`；`disabled` |
| 重开确认 | `sui-alert-dialog`＋`sui-button` | vendored `js/dialogs.js` | `dismiss-request`；确定/取消 |
| 敌血与生命/体力/气势 | `sui-linear-progress` | vendored `js/progress.js` | `value`，独立颜料 props |
| 试炼方印与来势牌 | `sui-badge` | vendored `js/badge.js` | 非交互正文字，组件颜色 props |
| 标题、技法、反馈、数字 | 通用文本节点 | JSON typography | 无交互，不伪装控件 |

Web 进度组件内置240px轨道，renderer 对整个原生组件横向适配，不改其 shadow CSS；Badge 同样对原生组件尺寸适配。此适配仅供 Web 预览，真实 Compose 使用原生 size/height API，字形与细小圆角允许存在平台差异。浏览器截图不当作像素级 Compose 一致性证据。

## Critique 1

拒绝“普通黑色控制板换成金色边框”的惯性方案。去掉装饰边线与多层卡片，以纸态/墨态面积变化区分准备和交战；朱砂只服务印章、操作与威胁。四步教学逐页呈现完整原技法说明，避免把整张说明页长期搬进战斗视野。没有以大量仿古字体和纹理牺牲阅读。

## Critique 2 / 受限修订

第一次浏览器检查发现资源条在较窄列中被裁切，已按组件固有轨道宽度做适配；第二次 surface 检查发现方印被计为嵌套 app surface，已回到原生 Badge 的组件所属背景；第三次校对按实际 Compose 完成 160/400 高度协议、22sp阶段、资源值/最大值、44sp结算层级与最终palette。JSON、HTML内嵌快照已重新一致性校验。

真实 VR 尚未验证：0.8m/1.5m/3m 可读性、头动抖动、低照度可读、遮脸/刀路、hover/触觉、Space Pro 字体与实体背景混合。Root 负责实际构建、接线和端内截图。本目录五张 `*-preview.png` 均是 Chrome Web 布局图。

## 可复现检查

渲染：`python3 ArtSource/refinement/ui-design/build_preview.py`。HTML 内联完整 vendored SpatialUI 与精确 JSON，无 CDN、fetch 或外部图像。Schema 使用 PICO skill `assets/design-spec.schema.json`；surface 门使用同 skill 的 `scripts/check_design_surface_discipline.py`。

浏览器已观察：开始、暂停、继续、再挑战真实触发可见状态变化；样本事件分别进入换轮与结算。normal/fallback/error 同树可渲染，fallback/error 控制禁用。默认与最小宽度相同（控制400、状态500），动态高度仍按纸400、墨160协议；小窗口自然换行，仅是预览外部排布。`body` computed background 为 `rgb(218,214,211)`，background-image 为 `none`。

浏览器限制：chrome-use 对 Shadow DOM 按钮报告误遮挡，本轮使用工具明确提供的 `--allow-dom` 完成组件事件检查，事件为 `isTrusted=false`。此证据只证明 Web 事件与状态可达，不证明真实手柄输入、hover 或触觉。重开确认已实际触发并分别验证取消保留 fighting、接受返回 ready。

最终同步：状态牌 vertical gap 为4dp；准备标题行固定40dp，试印绘制边界与下方状态行间距实测8dp。增加128×80透明跳字静态样本：数字44sp/48sp、标签18sp/22sp、墨色阴影；普通无标签，要害暗金，护身淡灰，致命暗金；优先级 fatal > guarded > headHit，护身样本同时带 headHit、致命样本同时带三个标志，以显式核对优先级。静态图不证明600ms时间线、8cm漂移、四槽并发或稳定深度，真实timeline保持原代码。


## 出招与击中文字强调（revision 9）

设计事实写在 `nodes[id=direction-label].props.simulationScale` 与 `nodes[id=feedback].props.simulationScale`，沿现有 `phaseElapsedNanos` 驱动，不引入新的动画时钟，也不改变 Combat 时间。方向牌在 PREPARING 按 `clamp(phaseElapsedNanos / preparationNanos, 0, 1)` 从0.94到1.0；STARTUP/ACTIVE保持1.0，暂停隐藏。击中反馈在 HIT 开头160ms由1.04到1.0，其余阶段与暂停保持1.0。

Web renderer 只呈现静态最终尺度1.0，未模拟或验收这两段动态、VR轨迹或端内观感。本轮不重截图片：已有五状态与跳字截图为revision 5的静态布局证据，palette、surface与最终静态外观保持。

最终边界：feedback文字强调还须 result=FIGHTING、pauseReason=null、inputReady=true、phase=HIT，且feedback为HIT/HEADSHOT/GUARDED_HIT/PARRY之一；OUT_OF_RANGE、LOW_STAMINA等错误反馈以及任何门槛不满足时保持scale1。该事实写在feedback.props.simulationScale.allowedFeedback/when/otherwiseScale；本次只同步静态快照，未增加浏览器验证。


## DEFEAT 结算样本（revision 9）

保持五类状态结构。第五类是结算版式，历史内部 state id `victory` 沿用；新样本的 `result` 明确为 `DEFEAT`，不能据这个内部布局 id 声称获胜。通过 `window.__arenaPreview.setSettlementSample('defeat')` 注入普通落败，或 `setSettlementSample('defeat-timeout')` 注入超时落败。默认产品上没有新增调试开关。

全部文案、分数与资源在 `dataCases.*.settlementSamples` 中，HTML从同一JSON再生。普通落败与超时分别使用实际 `ArenaHud.feedbackLabel` 分支：`arena_defeat_detail`（“调整架势与节奏，再战一局。”）与 `arena_feedback_timeout`（“试炼时间已尽”）；标题使用 `arena_state_defeat`（“本次落败”）、说明使用 `arena_trial_finished`（“本局已结 · 可再挑战”），结算保留本局得分、最佳、连战/余血及落败结语。所有字符串已对照本次工程 `strings.xml`，没有另造战斗逻辑。

结算下半部按实际 `MatchSummary` 所在的可滚动内容区组织，表面尺寸/配色/动作motion字段保持原值。新 `defeat-preview.png`、`defeat-timeout-preview.png` 均为Chrome容量图；默认样本结算正文实测clientHeight=scrollHeight=194px，未发生裁切。最小浏览器检查观察到两种DEFEAT样本文案与资源切换、再挑战返回ready。既有端内输入、动态、设备舒适性结论均没有新增；Root端内验收仍独立进行。


## READY / PAUSED 四步教学（revision 9）

本次先读真实 `artifacts/integrated-polish/ready-scene.png`：桌面 READY 中，预演说明、两排禁用动作和三行键位挤占了教学空间，实际画面底部只剩被裁切的“刀术要诀”。该图是 Root 的端内基线；本目录新图全部是 Web 布局容量证据，不能充当修复后的 VR 截图。

400×400 协议、上方40dp标题行、状态、summary与主操作固定；READY/PAUSED 删除独立预演说明和非战斗动作块，已就绪 summary 统一现有 objective。教学区共194dp：顶行24dp，caption14sp、当前页标题20sp/24sp、右侧x/4为14sp/18sp；底部两个标准Small40dp按钮固定；上下间隔各8dp，正文区域114dp。正文只一段16sp/22sp说明，不另设键位小字块；不设maxLines，正文可内滚动。页面切换重建正文节点，scrollTop回0。首步上一式disabled，末步下一式disabled。

技法四步完整detail逐字取 `strings.xml`：进刀、架刀、避锋、破势。桌面操作提示已在revision 10改为官方虚拟手柄的模式设置、Shift右手平移、鼠标转腕/瞄准和左键确认；不提供单键战斗宏。原4行精简说明与废弃节点已从JSON移除；所有页面数据在 `dataCases.normal.techniqueGuide`，本地翻页action只改变index，不调用战斗动作。native隐藏桌面操作提示块，没有可见模式调试开关；QA使用 `__arenaPreview.setInputMode('desktop'|'native')`。

浏览器以真实400×400 CSS面板测量：教学区194、正文clientHeight=scrollHeight=114；默认首屏完整，破势最长正文在当前字体下为两行，desktop与native均无滚动需求；导航底边距外面板底边20px，完全位于面板内。已通过标准sui-button实际翻页1→2→3→4、末步disabled、上一式4→3以及正文scrollTop=0；PAUSED共用教学版式同样不裁切。截图 `teaching-desktop-1.png` 至 `teaching-desktop-4.png`、`teaching-native-4.png`、`teaching-paused-desktop-4.png`；图片按浏览器device pixel ratio输出，CSS面板固定400×400，不能据图像像素推算VR物理尺寸。

约束与未验：Web系统字体换到PICO字体时可能增加行数，内滚动只保护极端容量，不代替默认首屏检查；真实VR的翻页射线点击、hover/触觉、距离、头动、教学导航是否被武器遮住仍由Root复测。FIGHTING、结算数据、所有surface尺寸、palette与两处simulationScale字段均保持。本次只编辑设计目录，未触碰runtime/res/test/Main/HomeStage/build/device。


## 官方虚拟手柄输入约定（revision 10）

本轮仅修改设计数据与HTML快照，接口冻结，不为图片延迟。战斗控制对native/desktop统一400×160；准备、暂停、结算400×400。paper/ink、原有四步导航及尺寸层次保持，不新增控件或窗口。JSON没有DesktopActions、onDesktopAction、DesktopCombatInput或预制战斗动作入口。

桌面提示沿官方虚拟手柄：右下RightControllerMode，ControllerButtonMode开，Keyboard文本模式关；Shift+W/A/S/D/Q/E仅平移虚拟右手，鼠标转腕/瞄准，左键确认。头部移动与手柄移动明确区分，VR仍以实体动作识别。native保留四招完整技法detail；desktop采用独立的四页模拟器操作，caption为“模拟器操作”。desktop仅由注入样本的inputOrigin==DESKTOP判定，原setInputMode仅为无可见调试控件的QA样本注入器。终局VICTORY/DEFEAT的comboVisible固定false，score/best/history不清零，显示门槛另记在status-surface.props.comboVisibility。

本轮只跑schema、精确JSON快照与surface门，未跑浏览器/Native图。旧teaching-desktop截图记录revision 9的旧按键文案，不能作为当前输入说明或验收图；本轮不刷新这些历史图。Web进度组件的240px固有轨道适配仍保留，它不代表战斗面板高度。


### revision 11 · 与已收敛XML精确同步

直接读取当前 `strings.xml` 与 `arena_ui_art.xml`：desktop四页为控制模式、移动虚拟手、动作识别、头手分开，caption“模拟器操作”；native仍为进刀、架刀、避锋、破势，caption“刀术要诀”。每页只有title/detail，detail16sp、22sp行高；删除第三块desktopHint/键位小字。说明中的Android字符串换行已转为JSON真实换行。两种模式数据分别位于 `dataCases.normal.techniqueGuide.inputModes`，来源XML SHA随JSON记录。其余冻结约定保持，本轮仍未运行浏览器或Native截图。
