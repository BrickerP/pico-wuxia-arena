# Spatial App Design Doc — 酒馆试炼 HUD

## 1 · Frame

**Routing** — `product_doc + existing_module`。输入是既有游戏上的完整 HUD 功能规格，明确了两个新区域、真实字段、状态与交互约束，但没有用户提供的视觉资产。它不是一句话意图，因此不走 managed `intent_only`，也不需要 `intent-brief.md`；Designer gate 仍然必需并由本包完成。

**Subject** — 写实中式 PvE 刀术试炼的场边 HUD。它不增加新的战斗规则，只把当前 `EnemyCombatStateMachine` 已有的生命、阶段、护身、攻击方向、暂停和输入状态变成可读、可操作的空间反馈。

**Viewer & context** — 站立玩家位于 Full Space 酒馆场景，主要视线落在约 1.2–2.4 m 前方的刀客。桌面预演来自 HMD 派生头手位姿，真机来自 PICO 头手追踪。HUD 以余光阅读，不能遮挡敌人躯干、武器和玩家刀路。

**The single job** — 在不离开对手的前提下，看懂当前试炼状态并完成开始、暂停／恢复与重新开局。

**Spatial justification**

| Core task | Affordance | Why spatial beats flat | 2D counterfactual |
| --- | --- | --- | --- |
| 观察攻击方向与敌人状态 | Direction + position | 信息固定在敌人两侧的场边，余光可读且不覆盖身体与刀路 | 平面 HUD 会叠在中心视野或需要把视线移到屏幕边缘 |
| 控制试炼 | Body + position | 控制匾保持在左侧固定位置，玩家形成空间记忆，操作后立即回到对手 | 传统暂停菜单会取代整个画面，打断空间连续性 |
| 区分桌面预演与真机输入 | Position | 输入来源贴着控制匾长期可见，避免把合成手位误当成真机证据 | 日志或调试面板需要离开体验才能确认来源 |

**Form & scale** — 继承现有 Full Stage。HUD 是挂在 Stage ECS 实体上的两个小型 Planar `AttachmentPanel`，不创建新的根容器，也不使用裸 Compose 覆盖。

**Assumptions**

| Assumption | Confidence | What changes if wrong |
| --- | --- | --- |
| 玩家以站姿正对敌人，中心视线需要完全留空 | High | 若转为坐姿，需要降低两匾高度并缩短横向间距 |
| 状态更新频率低于头手位姿，不需要高频动画 | High | 若加入连续连击计量，再评估独立的短时反馈层 |
| `tryStartAttack`、暂停／恢复、重开和事件出口会接到现有状态机 | High | 未接线前 UI 对应控件保持不可声称运行完成 |
| 输入来源能由既有 DESKTOP／PICO origin 映射为诚实标签 | High | 若 origin 不稳定，退化为“预演输入／设备输入待确认” |

## 2 · Explore — alternatives

**Direction generation** — 当前是 leaf 设计任务，不能再创建独立子代理，因此三条方向按隔离约束分别推演后再比较。

### Direction A — 场边双匾

左侧控制匾、右侧态势匾，中间无 UI。签名元素是右匾的三段“招向印”，只在已有攻击方向出现时抬升对应方向。风险是左右视线切换，需把信息密度保持在一眼范围。

### Direction B — 持刀腕侧小窗

把状态和暂停控制固定在非持刀手附近，随手移动。签名元素是腕侧方向罗盘。风险是桌面预演双手由 HMD 派生且无法独立控制，真机挥刀时小窗运动会干扰可读性，也会占用玩家身体动作空间。

### Direction C — 门楣式横幅

在敌人上方放一条横向试炼牌匾，生命、阶段和方向从中轴向外展开。风险是需要频繁抬头，状态与敌人的刀路分离，且容易遮挡酒馆构图和敌人上肢动作。

**Decision matrix**

| Direction | Task efficiency | Spatial value | PICO comfort | Domain fit | Risk | Distinctiveness |
| --- | --- | --- | --- | --- | --- | --- |
| A | High | High | High | High | Low | High |
| B | Medium | Medium | Low | Medium | High | High |
| C | Medium | Medium | Medium | High | Medium | Medium |

**Chosen: A** — 它把场景中心、玩家刀路和敌人动作完整留空，同时用固定空间位置建立最快的余光读取习惯。

**Rejected** — B 与当前桌面预演能力冲突，真机运动可读性也较差。C 会增加颈部抬头和中心上方遮挡，方向提示离攻击动作太远。

## 3 · Plan

**Executable spec** — `design-spec.json`，schema version `1.0`，revision `10`。

### Visual tokens

全部 16 个 SpatialUI `ColorScheme` 角色保持同名 Vibrant 引用。没有品牌色覆盖。实际 AttachmentPanel 样例不提供系统玻璃背景，因此两个面板各有且仅有一个 bounded content surface，使用原生 `fillPrimary`；面板内按钮通过组件 `colors` API 使用 `fillSecondary`／`labelPrimary`，没有修改 Theme。攻击方向同时用文字、位置和抬升表示。

**Type** — 运行时继续使用 `PicoTheme.typography`。标题映射 `title`，正文映射 `body`，辅助标签映射 `label`。不引入字体资产，中式气质由“场边试炼、对手态势、招向印、气血、护身”等词汇与场景模型承担。

**Depth** — 两个 AttachmentPanel 位于场景中心两侧并略向玩家内收。招向印活动段抬升 12 dp，周围不再叠加内容表面。

**AttachmentPanel background premise** — SDK 6.1.9 的正式 AttachmentPanel 样例只挂载调用方提供的 Compose 内容，没有 WindowContainer 的系统玻璃。两匾各自使用一个 32 dp 圆角、`fillPrimary` 的 bounded content surface；不调用 `backgroundMaterial`，不与系统玻璃叠加，也不添加边框。

### Signature element

“招向印”由“左、上、右”三个固定方位组成。当前攻击方向出现时，对应方位使用 `interaction`、文字和 12 dp 抬升共同强调。没有攻击时显示“观势”。周围信息保持克制。

### Surface sizing and Stage placement

| Surface | Type | Content | Default | Min | Max | Stage placement |
| --- | --- | --- | --- | --- | --- | --- |
| arena-stage | Existing Full Stage context | 已有酒馆、刀客、玩家刀场景，仅作 Web 设计对照 | 4.345×3.428 m | 同默认 | 同默认 | 继承当前 `DefaultStage` 与 arena-root |
| trial-control | Planar AttachmentPanel | 开始、暂停／恢复、重新开局、输入来源 | 360×176 dp | 340×160 dp | 400×184 dp | arena-root 左侧 `(-0.8, 1.08, -1.9)m`，朝两观察位姿中点偏转约 34° |
| combat-status | Planar AttachmentPanel | 生命、阶段、护身、攻击方向、范围／输入提示 | 440×156 dp | 400×148 dp | 480×176 dp | 刀客上方 `(0, 2.10, -2.4)m`，正对玩家；运行时保持底边不低于 1.95 m |

状态匾按两种已验证观察位姿审查。头部约 `(0,1.6,0)m` 时，匾中心距离约 2.45 m、上仰约 11.8°；W 前移至 `(0,1.6,-1.4)m` 时，距离约 1.12 m、上仰约 26.6°。当前敌人可视顶部约 1.808 m，状态匾实现时必须用 `LocalPhysicalLengthConverter` 把 156 dp 高度换成米，并保持底边不低于 1.95 m，至少留出约 0.14 m 的头顶间隙。控制匾在两观察位姿分别约左转 22.8°／58.0°、下视 14.1°／29.0°，定位为需要主动转头的低频控制区，不承担战中持续读取。

### Layout

```text
                                      ┌ 对手态势 · 阶段 ───────────┐
                                      │ 气血 72/100  护身  招向印   │
                                      │ 范围／输入提示              │
                                      └─────────────────────────────┘
                                                 ↑ 头顶留空
┌ 场边试炼 ───────────┐                 [ 玩家刀 ↔ 刀客 ]
│ 当前状态／输入来源  │
│ [开始/暂停/恢复] [重开]│
└─────────────────────┘
```

Primary focus 是刀客。两匾都没有滚动、二级导航或展开层。密度上限为每匾三个纵向信息带。

### States and transitions

| State | Primary task | Focus | Entry / exit |
| --- | --- | --- | --- |
| ready | 开始试炼并确认输入来源 | 开始按钮 | 开始 → fighting |
| fighting | 观察敌人状态与攻击方向 | 招向印／气血 | 暂停 → paused；追踪失效 → tracking-lost；敌人生命归零 → defeated |
| paused | 选择恢复或重新开局 | 恢复按钮 | 恢复 → fighting；重开确认 → ready |
| tracking-lost | 等待新的有效头手观察 | 输入提示 | 新头手基线建立 → tracking-resume-ready；重开确认 → ready |
| tracking-resume-ready | 明确确认当前暂停标识后继续 | 继续试炼按钮 | 玩家点击且 `resumeReady=true` → fighting；重开确认 → ready |
| defeated | 确认试炼结束并重新开局 | 结果与重开 | 重开确认 → ready |

重新开局会丢弃当前轮次，必须通过 `sui-alert-dialog` 确认。追踪失效后，新头手基线只把状态推进到 `tracking-resume-ready`；只有玩家明确点击“继续试炼”且冻结的 `resumeReady=true`，才以当前 `pauseId` 调用恢复。UI 不会自动伪造确认。

### Components and real data sources

| Component | SpatialUI mapping | Data / action source | Purpose |
| --- | --- | --- | --- |
| 开始、暂停、恢复、重新开局 | `sui-button` | `ArenaSession` 控制接线 | 操作当前轮次 |
| 阶段标签 | `sui-chip` | `EnemyCombatStateMachine.phase` | 一眼识别 IDLE/WINDUP/ACTIVE/RECOVERY/HIT/DEAD 的中文状态 |
| 气血 | `sui-circular-progress` + text | `health` / initial health | 用紧凑圆形进度显示对手生命，不虚构玩家生命 |
| 护身 | text | `guarding` | 显示已有护身状态 |
| 招向印 | `domain_visual: attack-direction-seal`；生产端使用三个 SpatialUI `Badge` | `activeAttack.direction` | 显示左／上／右攻击方向，活动方向前移 12 dp |
| 暂停与追踪说明 | text | `pauseReason`, `hasRequiredObservations`, `origin` | 区分用户暂停、追踪中断和输入来源 |
| 重开确认 | `sui-alert-dialog` | `resetRound` | 防止误触重置 |

不显示技能、经济、关卡、连招、玩家生命或未实现的挥击判定。桌面标签为“桌面预演 · HMD 派生手位”，真机标签为“设备追踪 · 头手动作”。

### Responsive behavior

控制匾宽度低于 350 dp 时使用 8 dp 内边距。态势匾宽度低于 420 dp 时使用 8 dp 内边距。两匾都保持单行按钮和三行以内信息，控件语义、状态和文本不变。

## 4 · Critique — before build

通用输出很容易变成深色半透明仪表盘、许多小卡片和高饱和强调色。初稿曾考虑给两匾加仿木边框和金色品牌色，但这会复制场景材质、削弱系统玻璃并引入装饰性表面。修订后移除自有边框和品牌色，把中式识别集中到空间构图、词汇、刀客和招向印。

硬检查通过。三条方向在空间结构与交互上实质不同；2D counterfactual 完整；尺寸与最小控件高度匹配；AttachmentPanel 来自现有 Stage 需求；16 个原生色角色保持不变；所有标准控件映射到 `sui-*`；无显式图标需求；结构节点透明；没有嵌套应用表面、内容边框或材质字段。

## 5 · Build

`preview.html` 只从嵌入的 `design-spec.json` 渲染。产品标记仅保留挂载点，内联 vendored SpatialUI Web bundle。普通、缺失和错误数据走同一节点树。重新开局通过 `sui-alert-dialog`，状态变化通过声明的 transition/action 驱动。

## 6 · Critique again

**Verdict: pass after six JSON-first patches and one control-contract sync**

第一轮视觉检查发现控制匾在最小高度下重复说明行会挤压按钮。revision 2 删除重复的 `control-state-hint` 节点，把控制匾收敛为标题、状态、输入来源和动作三个信息带，没有扩大表面。revision 3 清理重复说明字段。revision 4 合并输入来源和就绪状态，并把右匾末行固定为真实范围／战斗状态。第二轮发现固定浅色审查环境无法代表黑色酒馆 Stage 的实际对比度，revision 5 嵌入已有运行截图，UI palette 仍保持原生 Vibrant。revision 6 外移双匾。主控复审指出 W 前移后原面板会落到观察者身后，revision 7 改为刀客上方的紧凑状态匾与左侧低频控制匾，并按 z=0／-1.4 m 两个观察位姿记录角度与头顶间隙约束。revision 8 把控制匾默认高度从 168 dp 调整为 176 dp，消除默认宽度下 6 dp 的内容溢出；340 dp 最小宽度仍用 8 dp 紧凑内边距保持 160 dp 高度。revision 9 与冻结控制契约同步，将追踪恢复拆成“基线已建立”和“玩家确认继续”两步。revision 10 根据实际运行图和 SDK 样例移除“AttachmentPanel 自带系统玻璃”的错误前提，为两个面板各增加一个 `fillPrimary` bounded surface，并以原生 `fillSecondary` 提升按钮与底色区分。

- 外部 JSON 与嵌入 JSON 语义一致，revision 一致。
- schema 和 surface discipline 检查通过。
- 两个 Planar 表面、五个状态、全部转换、组件、绑定和响应规则均由 JSON 驱动。
- 预览保留 SpatialUI Vibrant 原生角色与系统玻璃，没有 HTML-only 产品文案、颜色、尺寸或状态。
- 默认尺寸与最小宽度检查通过，中间视觉区保持空白，按钮和气血信息无截断。
- normal／fallback／error 可通过非产品测试钩子切换，交付页面没有调试控件。
- 设备舒适度、实际遮挡、射线命中和真机性能未执行，留给下游 PICO 运行验证。
- Designer gate receipt 为 `design_escalation_receipt.json`，状态 `designer_passed`；其中记录 schema、表面纪律和浏览器视觉检查的真实路径与结果。
- revision 10 的对比度修订来自实际运行图 `artifacts/runtime/hud-animation-first.png`；root 完成 world scale=2 后仍需重新捕获设备画面，Web 预览不能替代该验收。

**Implementation interface needs**

1. `ArenaSession` 暴露只读 UI 状态，内容限定 health、phase、guarding、active direction、pause reason、input ready/origin、target in range。
2. 接通现有 `tryStartAttack`、`pauseByPlayer`、`tryResume` 和 `resetRound`。`TRACKING_INTERRUPTION` 恢复必须由用户点击并携当前 `pauseId` 确认，状态机规则本身冻结。
3. 消费现有 `EnemyCombatEvent`，驱动 UI 与后续 idle/slash/hurt/fall 动作。当前设计不承诺未接入的挥击命中。
4. `HomeStage` 在 arena root 下创建两个 AttachmentPanel，并在场景销毁时一并释放。面板不进入玩家刀或敌人骨骼子树。

## Runtime contrast revision 11

The actual Stage attachment does not provide a window glass background. Panel-owned ink surfaces and parchment foreground tokens provide stable contrast while preserving the native PicoTheme ColorScheme. The attachment ECS parents use absolute scale 2, with status height converted to metres after that scale.
