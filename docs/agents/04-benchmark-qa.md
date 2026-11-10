# 精修命中特效、声音与触觉呈现

## 本轮目标

让软目标命中、硬目标／护甲接触、格挡、弹反、破势与处决都有清晰可见、可听、可感知的局部反馈。

## 责任与文件

本轮职责切换为呈现生产。负责 CombatEffects.kt、CombatAudio.kt、ArtSource/refinement/effects/、现有effects与audio生产资产及本文件。Main.kt和HomeStage.kt由主控集成，ArenaSession与接触事件生产由01会话负责。其它会话正在并行，不回退其改动。

## 共享接触合同

主控已建立 core/combat/CombatImpact.kt，继承EnemyCombatEvent。按id、kind、point、normal、strength、hand、atNanos驱动呈现。point为Stage米制，strength为0到1。同一批中的多个事件须被完整消费，UI低气势／距离提示继续作为界面信息。

## 本轮工作

- 移除以最后一条state.feedback代替真实接触的路径，按CombatImpact消费。声音、特效各自去重，主控再把同一事件接到触觉与局部光反馈。
- 调查目前导入动画为空即禁用的实际可见性问题。依据6.1.9公开API选择单一可靠的最终表现路径，清理过时导入依赖。
- 肉体／衣物击中需要接触点冲击核心、少量布尘或碎屑与短暂刀痕，金属／格挡／弹反需要明确火星及材质差别。刃光只辅助表达挥动方向。
- 提高近身效果的可见保持时间、材质与层次，保留中式写实尺度。表现与接触点、法线、强度和角色动作同步。
- 精修现有短音效的瞬态、低频主体和材质差异。触觉参数与API依据交主控统一接入Main，保持实际追踪连续。
- 可制作离线效果小片段。实际PICO视口与单次命中的专项观感由主控独占操作，完整游戏验收另列。

## 交付与审核

给可编译源码、效果资产、各事件映射和前后可视对比，不能只交文件数量或日志尺寸。查对应版本官方文档再用新增SDK API，不猜私有接口。30分钟内交付一个阶段并结束，主控取产物审核构建。

只在主仓库工作，不创建副本、不提交推送、不抢设备、不进行无限logcat或wait_threads零等待轮询。

## 本阶段生产接口

已采用静态GLB分层网格加Entity变换与透明度的单一运行路径。`CombatEffects` 保留 `load(root)`、`present(state, events)` 与 `close()`，移除导入动画资源、播放控制器及 `state.feedback` 接触推断。四份生产GLB均无animations，接触核心、碎屑／火星、短刀痕由命名层 `core/debris/scar` 驱动。

音效新入口为 `CombatAudio.present(state: ArenaViewState, events: List<EnemyCombatEvent>)`。声音和特效各持本轮事件ID集合，按每个 `CombatImpact` 消费，首批和切轮首批继续处理。主控现已在Main传入同一批 `events`，并接入逐事件触觉及HomeStage接触点局部光。实际视口、头显声音与触觉由主控专项验收。

| 接触kind | 视觉资源与层次 | 独立接触声音 |
| --- | --- | --- |
| SOFT_HIT | soft_contact，暖色冲击核、布尘、短暗亮刀痕 | arena_hit |
| PLAYER_HIT | soft_contact，实际接触点局部冲击 | arena_hurt |
| HARD_HIT | metal_contact，白热核心、细长金属火星、擦痕 | arena_hard_hit |
| GUARDED_HIT | metal_contact，护甲接触火星 | arena_guarded_hit |
| BLOCK | metal_contact，刀刃碰撞火星 | arena_block |
| PARRY | metal_contact，核心放大1.3倍，闪核0.22秒、整体0.54秒 | arena_parry |
| SKILL | force_contact，断续冲击环、碎屑与短痕 | arena_skill |
| EXECUTION | force_contact，终结接触的局部冲击 | arena_execution |

当前合同没有单列GUARD_BREAK，破势暂按主控的SKILL接触事件呈现。保留脚步和倒地尘作为动作附属效果，使用ground_dust；命中反馈由真实接触事件产生。

普通软接触保持0.62秒、金属0.44秒、破势／处决0.72秒。强度映射到0.72至1.18倍局部尺寸，法线定位沿表面外偏8毫米，手别给短刀痕轻微方向差异。事件atNanos与当前模拟时间计算初始视觉年龄，上限80毫秒。每类预载6槽，忙槽接触排队，不覆盖同批的前一接触。场景失效时清空活动层与待播接触。普通非终局暂停或观察失效也清空；VICTORY／DEFEAT在场景仍有效时继续呈现本批新接触，事件ID去重与轮次门槛继续生效。关闭时递归销毁池。

SoundPool加载完成前的接触先排队，记录System.nanoTime入队时间，后续present排空已就绪样本。超过120毫秒的待播项直接移除，已失败的样本记录后移除待播项。非终局暂停、切轮和close清空待播及流句柄。保留现有SoundPool与12路并发上限，关闭时解除监听并release。音量受事件强度和接触距离影响，左右手使用轻微声像差异。

## 已交付效果实物

- [同米制峰值对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact_materials_comparison.png)与[0.833秒离线短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact_materials_preview.mp4)直接导入实际GLB，按运行包络驱动。左列展示旧刃光资源的理论峰值，右三列为软接触、金属和破势／处决。旧图像列的范围为离线资源对比。
- [267毫秒尾段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact_materials_267ms.png)中刀痕、布尘及余火星可辨；[467毫秒尾段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact_materials_467ms.png)中软目标刀痕和破势环继续保持，普通金属按0.44秒结束。已逐张目视核对。
- [12.06秒音色前后试听](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/audio/material_contact_comparison.wav)配有[时间顺序](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/audio/comparison_cues.json)和[波形总览](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/audio/waveform_overview.svg)。软目标突出低频主体与布料瞬态，硬接触突出高频金属瞬态，弹反增加较长清亮尾音，破势和处决各有独立声层。

四份静态运行GLB总计73,588字节，三角数分别为软228、金属132、破势636、地尘182。每份3个mesh层，24个预载实例合计7,068三角。旧运行目录的blade_arc、metal_sparks、break_ring和foot_dust动画GLB已移除，原制作源保留作离线对比。实际资源与制作源字节一致，尺寸和哈希见 [contact_effects_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact_effects_manifest.json)。

声音为11份48kHz／16-bit／单声道WAV，8种接触加刀风和胜负提示。逐份解码检查通过，零削波、首尾零采样、峰值约−4.437dBFS，最长单段解码91,200字节。Cue时长与实际帧数逐项吻合。软命中低于300Hz能量约81.7%，硬接触高于3kHz约48.6%，弹反约48.3%，差异来源为实际PCM测量。旧arena_clash和arena_dry已清理。[测量结果](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/audio/audio_measurements.json)

## 官方依据与触觉建议

项目BOM为6.1.9。本会话无可调用的Context7或PICO知识查询工具，按主控约定读取本机SDK6.1官方文档，并与已安装6.1.9公开类型交叉核对。`Entity.loadSuspend`返回模型层级，`findEntity`定位命名层；`TransformComponent`在主线程改变位置、旋转和缩放，`OpacityControllerComponent`逐层控制透明度，关闭时递归销毁。三个透明层各自淡出，父根不重复乘淡出系数。[模型加载](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_ecs_create-entities.md)、[命名查找](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/api-reference/com.pico.spatial.core.ecs.md:1729)、[透明度控制](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_rendering_opacity-control.md)

以下为strength等于1时的首轮触觉调音候选，由主控统一采用或调整。level按事件strength线性缩放并约束至0至255，按事件hand选择左右控制器。

| kind | level | frequency Hz | duration ms |
| --- | ---: | ---: | ---: |
| SOFT_HIT | 145 | 90 | 30 |
| HARD_HIT | 195 | 220 | 16 |
| GUARDED_HIT | 170 | 170 | 24 |
| BLOCK | 190 | 150 | 28 |
| PARRY | 235 | 280 | 18 |
| PLAYER_HIT | 180 | 80 | 42 |
| SKILL | 195 | 125 | 46 |
| EXECUTION | 235 | 75 | 64 |

官方参数范围为level 0至255、frequency 40至500Hz、duration 0至1000ms，Press预设为240／127／15。主控使用既有LocalHandControllerHaptic与公开 `HandControllerHapticType.custom`，保持当前追踪生命周期。触觉只在控制器交互模式生效，表中材质分层参数尚待真机调音。[官方触觉说明](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_interaction_controller-haptic-feedback.md:19)

## 阶段检查与交付边界

已完成源码差异检查、制作脚本语法检查、GLB头／索引／有限值／三层命名／无动画／源与运行一致性验证，以及11份WAV格式／时长／削波／边界采样验证。独立只读复核确认首批、切轮、多事件去重与排队、加载中途释放及close幂等路径。法线旋转以轴向及100个方向离线验算，最大误差约1.03e−15。

本阶段生产修改为CombatEffects.kt、CombatAudio.kt及对应效果／音频资产和可复现制作源。图与短片是离线素材观感，PICO实际透明混合、近身遮挡、保持时间、密集接触排队时延、混音与触觉感受待主控专项视口验收。统一编译及运行结果由主控回填。

**本阶段呈现生产结束，交主控review。** 已交付真实源码、静态分层GLB、分材质WAV、前后对比实物与触觉建议，当前回合结束。

## 主控review最小返修交付

- CombatEffects已与Audio对齐终局例外。场景有效时，VICTORY／DEFEAT同批的新CombatImpact可继续入队和呈现，避免最后一击被结算的USER暂停清空。sceneReady门槛、本轮ID去重及旧轮拒绝仍生效；普通非终局暂停与追踪失效仍清空。
- CombatAudio的PendingImpact已记录System.nanoTime入队时间，playReadyImpacts每次统一取当前时间，先移除超过120毫秒的接触，再检查样本ready并播放。恰好120毫秒仍可播放，加载在时效外完成时该接触已过期。

静态差异检查通过。已核对终局／非终局、场景有效／失效、暂停与输入门槛组合，以及120毫秒前1纳秒、正好120毫秒和后1纳秒的ready／未ready边界。本轮仅修改CombatEffects.kt、CombatAudio.kt与本文件，素材保持上一阶段交付。

**本轮最小返修阶段结束，交主控review。** 编译与设备验证按主控要求交统一增量构建及专项验收，本会话已结束当前回合。

## 补充正式角色近身接触对比

已交付 [同机位before／after躯干接触图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/torso_contact_before_after.png)，1440×960，使用实际soft_contact与metal_contact生产GLB。正式角色取自 `HomeStage → arenaOpponents.first()` 的 `app/src/main/assets/models/opponents/base.glb`，SHA-256为 `a0122103a6bc11b6612d87cb839202b2d19fdcb12260f14fb8e6416442070b22`。

姿态为该资源真实slash动作的2.117秒，效果为55毫秒，strength为0.65，整体尺寸比例1.019。软核心约10.2厘米，金属核心约7.9厘米。软接触落在衣料躯干，金属接触落在正式钢刀的 `Steel | forged body` 材质表面。两处接触点与法线均由实际变形网格三角面取得，锚点沿面法线外移8毫米。

| 离线接触 | actor-local glTF米制点 | actor-local法线 |
| --- | --- | --- |
| 衣料躯干 | (0.169846, 0.765666, 0.172864) | (−0.563872, 0.413012, 0.715171) |
| 正式钢刀 | (0.056216, 0.868370, 0.742738) | (−0.913685, −0.200563, 0.353489) |

表中为离线角色局部坐标，运行接口继续使用CombatImpact的Stage米制点和法线。已目视确认同机位下衣料冲击与金属火星可辨，保留角色及刀刃的真实遮挡。图明确标为离线制作预览，PICO运行观感待主控专项验收。可复现脚本为 [render_torso_contact.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/render_torso_contact.py)，角色与生产素材均只读，本次补图仅新增该图与脚本。

**本轮最小返修与补图阶段结束，交主控review。** 两项源码返修、静态边界检查和正式角色离线对比均已交付，统一增量编译及设备验收由主控完成。

## 主控整合review与下一轮

两项返修的独立复审结论为接受。Main、HomeStage、CombatEffects与CombatAudio共同保留终局当前批次接触，声音等待边界为120ms。已采用本文件材质触觉候选并按strength缩放，加入140ms接触点灯光。主控整合增量构建通过，仍未运行游戏流程、测试套件或Space Pro验收。

主控已查看torso_contact_before_after.png，软衣料冲击与钢刀火星的近身比例通过离线制作初审。下一轮在通过角色review的新主刀客上重看接触遮挡、短停后反冲与音画时序，保留实际视口验证边界。

## 命中材质语义复审

主控将普通身体命中按现役衣料／护甲映射。试刀客和青衫身体走软接触，玄甲护甲身体走金属硬接触；裸露头部命中走软接触，伤害强度继续控制包络，头部80ms短停保留。格挡、弹反和护身仍走已接受的防御接触。该修正避免把所有头部强命中解释为金属火星。

## 冻结60k主刀客最终展示一阶段

已交付 [近身接触图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/hero60k/hero60k_contact.png)与[2.75秒离线资产动效预演](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/hero60k/hero60k_preview.mp4)。画面固定机位，包含头部、双手和刀尖，全片标注“离线资产动效预演”及制作切段。角色、FX与声音均来自正式生产资产。

正式角色为 `app/src/main/assets/models/opponents/base.glb`，制作前后SHA-256均为 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`。四份正式FX与11份WAV的输入路径、SHA和字节数记录在 [inputs.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/hero60k/inputs.json)，实际使用的接触素材及逐帧源秒记录在 [timeline.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/hero60k/timeline.json)。

| 制作段输出采样秒 | 正式clip | 实际源采样秒 |
| --- | --- | --- |
| 0.000至0.792 | slash | 1.350至2.100，含头部接触停顿 |
| 0.833至1.458 | hit_head | 0.053至0.678 |
| 1.500至1.833 | slash | 1.850至2.100，制作切段及刀刃接触停顿 |
| 1.875至2.708 | hit_side | 0.093至1.128 |

按本轮主控复审，当前无甲主刀客采用“裸头SOFT / 刀刃PARRY”。0.75秒裸头接触使用soft_contact与arena_hit，保持80毫秒短停；1.75秒接触取自真实DAO钢刀表面，使用metal_contact与arena_parry，保持90毫秒短停后转入hit_side。两次接触strength为0.7、整体尺寸倍率1.042，停顿后均有220毫秒反冲，峰值0.0635米、包络4p(1−p)。PARRY使用0.54秒总包络、0.22秒核心及1.3倍核心尺寸，水平反冲沿接触法线。FX按独立输出时钟继续，声音对齐第18和42帧。24fps以相邻采样帧表达80／90毫秒停顿。

修正版短片为960×640、24fps、66帧，H.264与48kHz单声道AAC。原先身体HARD段已撤回，当前静帧为第43帧、1.791667秒的刀刃PARRY峰值。为同步全片字幕，同机位重渲了66帧；首36帧源秒摘要、首触点参数、机位及灯光均与已通过版本一致，真实遮挡保留。

可复现制作脚本为 [render_hero60k.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/hero60k/render_hero60k.py)。片中clip以制作切段衔接，未做跨clip混合，来源秒和NLA映射均留在timeline。该交付用于正式资产、接触遮挡及短停反冲音画时序的离线review，PICO运行表现继续待主控专项验收。

**本阶段最终展示制作结束，交主控review。** 本次仅新增hero60k目录产物与更新本文件，runtime、正式角色及生产FX／WAV均保持只读，当前回合结束。

### 本轮材质语义返修定版

第二触点取自当前正式DAO的 `Steel | forged body` 变形网格面。actor-local glTF米制点为 (0.149048, 1.302999, 0.845157)，法线为 (−0.962155, −0.065006, 0.264636)，锚点沿该法线外移8毫米。PARRY水平反冲方向为 (−0.964194, 0, 0.265197)，90毫秒短停后执行220毫秒、峰值0.0635米的反冲。

图、片、字幕与timeline已统一为“裸头SOFT / 刀刃PARRY”。PARRY使用正式arena_parry.wav，0.54秒总包络、0.22秒核心及1.3倍核心尺寸。保留首段80毫秒头部短停和原接触源秒。相机边界仍沿用首次采样以固定机位，其中hit_body仅为边界测量项；成片逐帧动作由slash、hit_head与hit_side构成。

已目视最终PARRY峰值图，核对片长、视频／音轨、两次接触帧、材质名及实际FX／WAV哈希。正式actor与全部输入哈希保持一致，首36帧源秒摘要一致，脚本语法及静态差异检查通过。PARRY核心紧邻头部与刀身，保留实际几何遮挡，仍属于离线资产动效预演，PICO运行观感由主控验收。

**本轮材质语义返修阶段结束，交主控review与统一提交。** 当前hero60k图、片、脚本和timeline为修正版，runtime、正式actor、生产FX／WAV及inputs.json均保持只读，当前回合结束。

## 主控最终review与本轮收口

主控已核对960×640／24fps／2.75秒H264＋AAC成片，并抽看1.833秒弹反峰值。第二触点已从布衣躯干修正为实际钢刀PARRY，正式素材、声效、90ms短停与hit_side语义对齐，接受本轮离线制作产物。

主控另已完成当前APK构建、安装启动和实际Full Stage准备态截图，场景／人物／HUD可见。真实输入触发的战斗特效、混音／触觉、整局与Space Pro体验仍在后续验收。下一轮先收紧主角残余拇指交叠与源段外交叉，再做动作收势／步法和UI细化，维持现有三轮短竞技场。
