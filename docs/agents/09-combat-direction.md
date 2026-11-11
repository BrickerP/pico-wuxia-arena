# 09 · 正式动作bank与战斗表现接线

## 当前状态

Root已用唯一publisher原子发布KTX整组至正式library/app（含dao_grip），当前schema3 binding为b03f55e6。09已从DEFAULT_BANK正式library重新生成typed身份并对齐精确pin；本轮仅身份更新，运行逻辑、时钟、判定、输入、样本数组及生成器不动。64／64 focus、5／5生成器及默认来源精确重现均通过，现已重新冻结给Root共享新APK；最高画面／交互HIGH继续由Root实际验收。

## 目标

把新站姿、正劈、左右斩接到真实正常循环，攻击方向、动画、代理、刀路、接触时刻与受击反应一致。参考《荣耀战魂》《只狼》《影之刃零》的来刀辨识、支撑、卸力与收势，沿已有能力完善。

## 所有权

负责 content/EnemyAnimator.kt、runtime/ArenaOpponents.kt、新AttackBankProfiles数据与加载／生成接口、ArenaSession.kt中既有方向调度与接触pose选择、EnemyCombatStateMachine.kt中反击方向参数转发及专项测试。本文件为交接。Root保留其它战斗数值／核心判定，08可能需要emitImpact转发补丁，交Root统一应用。

01是动作作者，Root内部character_grip_polish负责Python producer、manifest及正式发布。你不改这些制作源或GLB，不写Main/HomeStage。

## 当前输入

唯一生产真源为`ArtSource/tripo-warrior/library`，正式KTX schema3 binding `b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f`，状态`approved_for_development_integration`。三角色library GLB、app GLB、profile内部model SHA、characters/review及Kotlin exact pin已一致；typed数据仍从DEFAULT_BANK正式library生成，私有candidate不作默认。

本轮Root严格audit已报告：除`model_sha256`外，三份profile与ff3完整JSON精确相同，全部非image GLB数据守恒；09另外验证2616个typed样本数组与本轮开始前相同。locomotion／三攻击／gait及代理规则保持。当前完整身份见文末KTX发布表与`ArtSource/refinement/combat-direction/ktx_published_locomotion_runtime_identity.json`。此前ff3与私有基准／身份快照作为历史冻结保留。

## 制作队列

1. 复用同一profile数据选择三方向clip、source阶段及各角色head/body/刀根尖代理，替换旧统一slash和手写旧曲线数组。普通guarded HIT明确取新守势与对应代理。
2. 正常出招／反击目前硬编码OVERHEAD。给已有入口可读且可重复的三方向序列，按真实AttackStarted推进，不在每tick消耗随机选择。保持既有伤害、资源和识别阈值。
3. hitstop仍保留实际接触前姿态，致命仍读统一死亡时钟。转身、起步、停步、回守与受击切换减少突跳，保留最新白闪／真实刀光接线。
4. 与01接防御支撑、弹反卸力、受击与行动资源，逐阶段写明确输入文件与使用状态。现bank未正式发布前交完整接入代码给Root统一合入，Root组合后构建。
5. 以实际最终target profile验证phase端点、玩家视角方向、actor yaw和Root反冲一致，正常入口一招对应一次接触。

## 首轮交付

三方向正常循环与动画／代理使用同一数据的完整代码与必要专项。随后收口防御、转身和受击。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

### 2026-11-11 · 首轮三方向接线候选（专项通过，最终发布存在 locomotion 闸门）

真实代码已写入唯一共享工程，未更改正式资产、producer、manifest、Main/HomeStage，未运行共享Gradle或设备。当前改动必须与下述10clip候选由Root一并发布，旧8clip资产尚无attack_overhead/left/right，不能把源码单独作为设备可用完成态。

- `content/EnemyAnimator.kt`：按真实attackDirection选择对应clip，并直接使用统一profile阶段时钟；攻击clip手动采样后暂停自由播放，避免两帧之间自主前进而代理不跟随。短停仍提前返回保留已见接触前姿态，致命保留统一死亡时钟；普通守势HIT采对应新attack首帧。
- `runtime/ArenaOpponents.kt`：删除旧slash手写数组与旧source区间，三角色头/躯干代理从同一bank采样；守势HIT显式取新守势代理。
- `runtime/ArenaSession.kt`：正常入口与守势反击统一读取OVERHEAD→LEFT→RIGHT序列，仅消费实际AttackStarted，逐轮重置；已保留伤害、资源、阈值和ACTIVE中点裁决。
- `EnemyCombatStateMachine.kt`：receivePlayerHit新增末尾counterDirection参数，仅新启动反击时使用；在途攻击保持方向，advanceBy的既有反击方向入口保留。
- `runtime/AttackBankProfiles.kt`与`AttackBankProfileData.kt`：统一clip、phase、头身/刀根尖数据。每角色3方向106样本，共954个；全样本保留最终prepared actor-local坐标。stage yaw和Root反冲平移仅一次。
- `ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py`：读取冻结候选，校验characters/profile/model SHA与轴、单位、方向语义、源阶段和精确contact key；只生成Kotlin代码，不写正式模型资源。

来源为`ArtSource/tripo-warrior/review/attack-bank-candidate`。当前匹配GLB SHA：base `0c2a4801aaa6b89866303a9c783b524a88b6440633f0c9348041a6239af7d48a`；indigo `c980b18ef19190bf682604a43b730c3a0188829db8ea1c7c9e5d819d1959fed2`；veteran `63b92ac8edda1ab7ad56e2d3196522788fec8a43a04c0d665deef08028d82e83`。profile SHA依次为`ee2335d51cd3bd948476b840b9f1ac7583e6419c05e1bada7604e9142a790f5f`、`66aaaf374b23e3766f26f26fc0df71fe5259931301c2200c26d80cb3e02a6851`、`6b6cef951e7446245243fc7ebfef589a35fef8dd8d37a76cc3c02ef999a83e36`；生成数据亦内嵌这些身份和逐clip animation semantics SHA。

可见收益由真实新clip实现：正常游戏将从单一旧前倾slash变为正劈、玩家左侧来刀、玩家右侧来刀的轮换；本路目前交实际接入代码，未制作或宣称新的设备画面。实际端内视觉、输入及手感由Root统一组合后验证。现存动画短片/三视板是01的源审阅，不当作本路设备验收。

已完成2项生成专项与--check精确重现。下一步：隔离Kotlin/JUnit专项，补齐phase端点/方向/guard/yaw/根平移、循环与不消费失败尝试、一次出招一次接触；再对01防御/破势/受击候选建立明确使用状态。



### 本轮收口与真实验证

三方向的普通循环、守势反击、静止新守势、对应头身/刀根尖代理均已接入源码。新站姿不再每招结束返回旧idle：静止IDLE取attack首帧，guarded HIT亦取该新guard，旧walk保留。一次攻击只消费一次AttackStarted，序列是正劈→玩家左来刀→玩家右来刀，失败尝试/重复呈现不推进，换轮和ROUND_RESET复位。

修复了有效裁决的后续断段：状态机会在ACTIVE中点立即进入RECOVERING，以前按phase起点会从source1.00直接跳1.10。现成功裁决用统一`enemyRecoveryFromContact`从1.00继续映到1.75，MISS仍完整走到1.10再恢复。该标志仅真实AttackResolved非MISSED设定，AttackStarted、取消和回IDLE/HIT/DEAD清理，USER pause保留当前招状态。规则时长、伤害、资源、识别阈值没有改变。

刀端点现已实际消费：`ArenaViewState.enemyBladeBase/Tip`为同source clock、同actor yaw、同origin+Root recoil后的Stage坐标，供Root/08最终呈现接线；`resolveEnemyContact`在phase变更前保存接触sample，把既有防御结果的反馈点投到该真实敌刀段，未改变防御判定。BLOCK/PARRY短停保留刀与身体sample，下一招清掉旧hold。PLAYER_HIT既有hitstop=0，同批tick可能在裁决后继续消费余量，因此impact仍取source1.00，而发布的view/body/blade按当前RECOVERING时钟；测试已分别证明这两个时刻，未为测试改变批处理规则。

生成数据匹配最新已grounded schema2 candidate，binding SHA `6f23259d67f504ce58630b2dc7ba61fa290b50beaa7109de772f4f46dd7b2c72`。`AttackBankProfileData.kt`内嵌binding、逐角色model/profile和逐clip animation semantics身份。生成器校验review binding hash、profile/GLB hash及clip semantics；现为typed DoubleArray常量，首次使用不再拆分CSV或parse 15,264个Double。加载分配/真机帧时仍待Root端测。

Root整体根校准在profile/hash之前，仅改三攻击BoneRoot.translation，prepared最低足面Y=-.028配HomeStage实体originY=+.028。base两足余量小于.04mm；indigo/veteran另一脚仍约16–20mm。本路不把整体根校准描述为双脚零滑，未更改这些资源。

验证：`python3 ArtSource/refinement/combat-direction/run_isolated_tests.py --focus`使用缓存Kotlin2.1.20、Android35和PICO6.1.9实际类型进行隔离编译，39项focused全部通过；覆盖正常三方向一次出招一次裁决、出范围/重复帧不耗方向、换轮复位、3角色×3方向阶段端点和100ms接触、真实玩家视角刀切向、守势代理、yaw+根反冲、成功/MISS收势起点、实际发布body/blade及接触反馈刀段。`python3 -m unittest discover -s ArtSource/refinement/combat-direction -p 'test_*.py'`两项通过，`generate_attack_bank_profiles.py --check`精确重现，`git diff --check`通过。未用共享Gradle、APK/设备或Blender。

`CombatFeedbackTimingTest`仅将真实tracked strike fixture的手x从0改为-.25m，使其仍瞄准新canonical guard身体；原来的伤害、短停、死亡时钟、恢复和失败断言全部保留，39项包含这些回归。更广core测试首轮发现的`deathIsTerminalUntilRoundReset`断言与当前原有interruptTracking行为不符，以及08并行`PlayerContactTangentTest`切向失败，不在本路擅改。

证据在`artifacts/combat-direction/isolated-jvm/`；focused编译/运行不会写共享app/build。当前为真实接入代码交付，无新设备图，未声称VR手感或全流程已经验收。

### 最终发布闸门与后续动作来源

独立四轮review剩余HIGH：旧walk与新canonical guard头身代理中心相差约.246–.262m，原生walk↔guard/attack crossfade为180ms，而代理入口直接切换；正常范围内可能边走边开招。因此当前静止守势/三攻击路径成立，完整起步、停步、转身与locomotion回守尚未完成。不能用把crossfade归零制造可见突跳来掩盖，亦不能把未观测的线性proxy插值当实际骨骼blend。Root/01应提供canonical-guard出入的locomotion与对应prepared profile，再作为最终发布闸门核对；Root若先组合端测，须保留这一已知限制。

已继续完成01防御/弹反/受击来源对接，交付`ArtSource/refinement/combat-direction/reaction_sources.json`：六份enemy continuous raw、preview、metadata均记录当前真实SHA、一次右指校正边界、事件语义与消费时段。guard_brace(.8s，支撑key.26)、正劈parried_recoil及左右parried_recoil_left/right(.85s，分别从对应attack@1.00进入)、hit_body/hit_head(.72s，普通HIT .05→.72映实际HIT duration；hit_head另有execution前缀.1→.595)均存在。当前10clip bank尚未含这些新reaction，Root producer尚需按三角色适配、prepared grounding及proxy生成后统一发布；运行代码继续消费当前bank原hit_body/head/side，未用空壳或fallback冒充接入。方向破势需在resolveActiveAttack清空attack前保留已裁决方向，不能在HIT时读已为null的currentAttackDirection。


### 末次复核

typed数组版本实际隔离编译后，focused 39/39通过；复用同一批已编译class扩展运行core+上述runtime共111项，110通过，唯一失败为旧`EnemyCombatStateMachineTest.deathIsTerminalUntilRoundReset:422`（现有interruptTracking会发暂停事件，旧断言期待空）。08并行刀路切向专项在这次已通过，不再列为当前失败。独立review确认刀端点消费、接触后收势断段和文本解析风险均已关闭；仅保留locomotion HIGH，最终发布结论为候选可组合／完整动作连续性未验收。

本路当前源码与专项身份见`ArtSource/refinement/combat-direction/source_identity.json`，该文件只记录本次交付文件SHA，不是正式角色发布manifest。当前git基线 380dd46b1cfa6aaf54ef54bc44535b5af330b62d，本路无提交。Root无需改HomeStage现有`EnemyAnimator(enemy)`构造调用；该类用当前roundNumber选择同角色profile。Main/HomeStage正式资源发布、08敌刀FX最终消费、共享构建与设备由Root继续负责。


检查范围说明：末次全树`git diff --check`出现03路交接`docs/agents/03-art.md:162`的EOF空行提示，本路未修改该文件；限定本路已跟踪源码/测试的diff检查通过。未回退、清理或覆盖其他路线文件。


## Root组合期间的冻结与01来源核对（2026-11-11）

Root已收三方向代码，接手08 tangent转发、10clip正式发布、组合构建与设备验证。09已冻结`EnemyAnimator`、`ArenaOpponents`、`ArenaSession`、`EnemyCombatStateMachine`、`AttackBankProfiles`、生成数据、生成器及所交专项；收到Root下一项源码任务前，本路只读这些文件，仅写本交接。正式资源／Main／HomeStage／共享构建继续由Root负责。09本次读入时核对原`source_identity.json`的14份交付文件，均仍匹配首轮SHA；Root此后集成产生的新SHA属于Root工作，本路不覆盖或重新生成。

本次一次性遍历`ArtSource/refinement/hand-poses`：尚未发现`guard_idle`、`guard_walk`、locomotion候选或stage9；`attack-keyposes`现有stage4至stage8。01文档仍以stage6回报为末节，但stage7／8实物已存在，以下以实物metadata和SHA为准。新loco是Root已派01的最高优先任务，源尚未交付时不以旧walk冒充新源，也不连续轮询等待。

### locomotion接入所需事实和接口

| 现有真实入口 | 现有行为 | 新源交付及Root后续接线所需 |
| --- | --- | --- |
| `ArenaSession.moveEnemy` | 仅IDLE移动，0.65m/s，desired距1.30m；`enemyGaitMeters`按实走距离加正／负号 | guard_walk须交实际一循环步距、源循环起止、正走与倒放语义；外部实体平移仍由Session独占，避免源水平根位移再叠一次 |
| `EnemyAnimator` IDLE moving | 旧walk按`enemyGaitMeters / 1.45m`模周期，source起点1/3s、周期7/6s，手动seek并暂停自由播放 | 现1.45m和源循环常量只属旧walk，不能直接套guard_walk；后续从新源冻结的同一profile读步距／区间，Root收到后再授权改代码 |
| 静止IDLE／guarded HIT／attack首尾 | 现统一取三攻击canonical guard首帧 | guard_idle以及guard_walk循环/起停入口应与该同一守势关联，并逐角色输出实际prepared head/body/刀根尖样本；单纯换新clip名不关闭HIGH |
| `ArenaOpponent.attackPose/contactPose` | moving IDLE仍返回旧站立proxy，攻击和静止guard用新bank样本 | final目标须让moving IDLE与画面按同一gait phase取新walk代理，覆盖起步、停步及walk→PREPARING，而非继续站立fallback |
| `EnemyAnimator` walk切换 | 原生180ms crossfade；当前代理入口硬切，约.246–.262m差 | final prepared locomotion入口、出口和有效支撑阶段核对后再决定过渡；未取得真实blend姿态前不把线性proxy混合当逐帧一致证明 |
| `ArenaSession.moveEnemy` yaw | IDLE时直接`atan2(toward.x,toward.z)`设置根yaw | guard_idle/walk交付本身不证明转身收口；转身资源／根yaw连续策略仍需Root后续指定，不在本轮并发改Session |

上述是后续接口需要的数据，不是本轮新增或已实现的schema。来源归01，三角色适配、grip一次校正、grounding、正式clip命名与profile发布归Root producer；09生成器当前只覆盖三攻击，冻结期间不加loader兼容分支。新数据应直接纳入最终干净路径，旧walk时标和standing代理在替换时一起移出。

验收需分别证明：canonical守势入口/出口、任意gait相位切攻击的实际画面与代理、正/负累计步距、暂停/追踪丢失/换轮的gait复位、相同actor yaw和根反冲仅一次、prepared足面与originY=.028配合。仅有首尾相等或全局最低鞋点贴地，不足以证明任意步态起停连续、双足无滑或完整VR手感。


### 已存在reaction源与后续消费接口

以下是首轮来源清单当前列出的六份raw。preview只作审阅，Root producer输入使用右指校正UNBAKED的raw；三角色prepared输出及其profile仍须由Root生成并冻结新身份。

| 源clip | raw路径 | 首轮登记raw SHA-256 |
| --- | --- | --- |
| guard_brace | `ArtSource/refinement/hand-poses/attack-keyposes/stage6/candidate/guard_brace_raw.glb` | `c2b80547b2c2e3199caf9713ba9e39c641d595b0f1f5b9ac0377786ca4f263cc` |
| parried_recoil | `ArtSource/refinement/hand-poses/attack-keyposes/stage6/candidate/parried_recoil_raw.glb` | `f3eb395277dd8df673fa74836e6e1c568552bbe4d30710f19d1162a3490e3691` |
| parried_recoil_left | `ArtSource/refinement/hand-poses/attack-keyposes/stage7/candidate/parried_recoil_left_raw.glb` | `3619bd24c4d25ac6d183e0b9cc2ab1a950a52a437aa37005a9a3cfbed122609b` |
| parried_recoil_right | `ArtSource/refinement/hand-poses/attack-keyposes/stage7/candidate/parried_recoil_right_raw.glb` | `22f0879fecbbebc2b2313229551e17838a1efcd76900c5cfaa09ecb7f92f4802` |
| hit_body | `ArtSource/refinement/hand-poses/attack-keyposes/stage8/candidate/hit_body_raw.glb` | `8213e52e9dacb9885db17c72326444dbb4db2545d57f15e264552e0cfbdaab0b` |
| hit_head | `ArtSource/refinement/hand-poses/attack-keyposes/stage8/candidate/hit_head_raw.glb` | `16e4f5a8e4d0fd186addee366798494eb89d6e8b9429c51af9595967b72e9a42` |

消费接口逐项保持明确：

- 三方向被弹反：在`resolveEnemyContact`调用`resolveActiveAttack`之前保留此次已裁决的玩家来刀方向；当前state machine在PARRIED时清掉attack，HIT中读取`currentAttackDirection`会变成null。后续用保留方向选择`parried_recoil`／`parried_recoil_left`／`parried_recoil_right`，从对应attack@1.00的入口映source0→.85，实际HIT时长为550ms；起点不能继承旧`hit_side`的.05，终点也不能继承1.18。
- 普通头／身受击：新`hit_head`／`hit_body`的普通HIT消费范围.05→.72，与现有source区间一致。保留当前真实总HIT时长映射，不能假定永远300ms，因为剩余parry硬直可延长该时长；短停期间仍冻结实际接触前姿态。换成新源后，必须同时换prepared头身／刀代理，而非仅复用旧站立fallback。
- execution前缀：新`hit_head`额外声明source.10→.595，对应既有统一death visual clock的前.45秒、source rate1.1。继续读当前`deathElapsedSeconds`，不得叠加第二套减速时钟；source是正常时标，致命hitstop和slowdown由既有runtime持有。
- 守势支撑：`guard_brace`事件key是.26秒，总源.8秒。它对应敌方承载的guarded HIT，不是玩家BLOCK动作。若guarding=true同时已在PREPARING/STARTUP/ACTIVE，不能直接用支撑clip覆盖正在进行的三方向攻击；需Root明确事件窗口及prepared pose/profile消费后再接。
- raw→prepared：反应raw的base78骨入口相等不代表indigo/veteran最终目标已相等；Root应在目标grip一次校正、角色适配、BoneRoot grounding之后重新生成anchor和身份。当前三攻击binding不包含新reaction，不能把该binding SHA当作反应资源已经发布的证明。

本阶段只核来源和接口，09未执行模型制作、生成器、测试编译、共享Gradle、设备或Git写操作。


### 本次只读复核结论

独立只读复核已完成：`reaction_sources.json`六条的raw／preview／metadata共18个文件SHA全部匹配，六个metadata的`parameters_sha256`也与实际parameters文件匹配；当前attack bank binding仍与`AttackBankProfileData`的`6f23259d67f504ce58630b2dc7ba61fa290b50beaa7109de772f4f46dd7b2c72`一致。没有改动该来源清单、运行代码或生成数据。

额外直接读取GLB的raw动画数据，五组关键入口各核234条TRS通道，均无缺失、最大分量差为0：

| 反应源入口 | 对照源 |
| --- | --- |
| stage6 `parried_recoil@0` | stage5 `overhead_aligned@1.00` |
| stage7 `parried_recoil_left@0` | stage5 `slash_to_left@1.00` |
| stage7 `parried_recoil_right@0` | stage5 `slash_to_right@1.00` |
| stage8 `hit_body@.05` | stage6 `guard_brace@0` |
| stage8 `hit_head@.05` | stage6 `guard_brace@0` |

这仅证明上述raw关键帧入口相等，不证明全段C1、最终三角色retarget、prepared profile或实际VR过渡。未运行作者验证脚本、producer、Blender、构建或设备。当前locomotion尚无新落盘源，约.25m入口差的HIGH原样保留；本路可继续接收Root指定的下一项，运行源码冻结维持。

## Root组合审核与下一步

Root已按binding6f23259d批准development_integration，正式producer发布3份10clip GLB和profile，同组数据与Kotlin pins匹配。Main已归一enemyBladeBase/Tip高频字段，接触tangent转发也已合入。构建与250项共享回归通过。旧死亡terminal用例修为允许跟踪暂停但保持DEAD/0血量/不推进时钟，未改死亡规则。开发包仍带locomotion约0.25m HIGH和另两角色16–20mm单足余量，最终Demo需由01 canonical locomotion及同一profile关闭。新reaction源已收，后续Root扩bank并与你继续接线。

## Root本轮组合审核与续派（2026-11-11）

审核：三攻接触/恢复时钟已入包；新刀weapon-only binding7373已正式发布，profile坐标未变。

下一步：把模型/profile/Kotlin身份更新到新正式library，默认generator源也收敛到library；随后接01 canonical walk及真实profile，保留HIGH至关闭。


## 正式weapon-only库身份更新（2026-11-11）

Root明确授权本轮身份更新，暂时解除生成器、生成数据及身份专项的冻结；更新完成后重新冻结，等待Root共享Gradle。Root producer完成后，本路先核到实际正式request为`7373f5937cd19d1306b861ca0e1654e040977eafb3af6685618742e3e0716cff`，并核三模型、profile、characters与request一致，随后实际执行：

`python3 ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py --bank ArtSource/tripo-warrior/library`

生成器 `DEFAULT_BANK`现唯一默认正式library，删除旧候选默认路径；输出注释标明正式来源，错误文案改为library，额外校验model实际SHA与profile／characters／review三方相等。没有新增fallback或双生产路径。

| 角色 | 正式GLB SHA-256 | 正式profile SHA-256 |
| --- | --- | --- |
| base | `e7f3de3d8c7e202999b2d456ae85257b89a01e7c21792f332c4b273c77b60cbc` | `f4b2d918bdb63cfd9436708822dc262df9c5e94ec357f1dc6b5a0ee01a114450` |
| indigo | `448d46394743018aff3165e0e49e5c07480b617664c072c14ab6ae186cc87ef3` | `4633e2a7e3d8173f09e2c1e7ff98e713b11cacb6b01979055dbe4ba469d44a3a` |
| veteran | `0c0b57a4f3684a25603a6875b2fd9188096755dc4b3688d921a7de8776f1e9c2` | `c6822e9f07ca94af850ded93c7a2d175bd10df4a4cb73be4f08d024cc9dd2c88` |

`reaction_sources.json`当前消费binding已更新至7373；六组reaction自身raw／preview／metadata、entry_source身份与尚未进入10clip bank的状态全部保留。`source_identity.json`继续作为首轮6f232交付快照保存原身份，不追改历史；本次正式库快照另见`formal_library_identity.json`。本文首轮候选段落的6f232及旧模型SHA均是历史证据，当前生产身份以本节和“当前输入”为准。

范围校验已证明：三份body与上轮候选逐字节相等；三个profile除`model_sha256`外全部JSON字段相等（包含九clip语义签名、方向、phase、954个样本与所有坐标）；重新生成的typed样本数组SHA仍为`1ba346a14d6a5d7b83eadee65f51263945823a373792857feaaf0d9d4d072f07`。因此本轮变化只涉及新dao的binding／model／profile文件身份，未改变动画或刀端点坐标。本路接收Root正式weapon-only产物，不重做制作源或改动作逻辑；刀具视觉验收由Root组合画面负责。

身份专项补齐：Python明确断言默认目录为正式library、新binding及三个新model SHA，并保留profile身份漂移拒绝、补上model身份漂移拒绝；Kotlin新增精确binding+三model+三profile pin，原三方向／时序／proxy专项保持原样。walk HIGH约.25m及locomotion后续合同原样保留，未把本次新刀发布描述为该问题已修复。


### 本次正式库更新完成，重新冻结

实跑结果：正式来源`--check`精确重现通过；生成器Python 3/3通过；`run_isolated_tests.py --focus`在实际PICO6.1.9类型上隔离编译并运行40/40通过（原39项加正式库身份pin）。未运行共享Gradle或设备。额外指纹核对五份动作逻辑文件在本次身份更新前后SHA完全相等，样本数组完全相等；Root已接的tangent改动未覆盖。

本次仅改生成器默认来源及身份校验、`AttackBankProfileData.kt`生成身份、Python／Kotlin身份专项、`reaction_sources.json`当前binding、本交接与本次`formal_library_identity.json`。`source_identity.json`首轮快照保留。旧walk／新guard入口差的HIGH保持开放，没有动作层面的修复声明。09源码／生成器／数据／专项现重新冻结，Root可开始共享Gradle。


### Root单active隐藏实体初始化契约（2026-11-11）

Root报告单active实机首轮未再出现NO_MEMORY，但隐藏初始化暴露SDK查询问题：加载器先将`entity.enabled=false`，`EnemyAnimator`构造中的默认`findSkeletonRootEntity()`／`findSkinnedMeshEntity()`过滤禁用节点，line33的single因空集合失败。Root将显式传`includeDisabled=true`，让实体保持hidden完成初始化；这属于查询修复，不改动画逻辑。01／09后续集成遵守该契约，不通过提前启用角色来规避。

本路仅记录Root实机发现，未自行复测或修改`EnemyAnimator`；运行源码、生成器与专项继续冻结，Root独占该修复及组合验证。


## stage10最小接入方案（2026-11-11，仅方案）

**结论：保留10clip正式别名与现有步态时钟，用stage10替换idle／walk来源；复用attack78重定向及实际蒙皮grounding基础，在三个最终目标上将idle／walk／三攻击一起校准、导出新profile与新binding。本轮不实施producer或runtime更改，Root输入probe构建不受本路影响。**

### 实物、来源及已证明范围

唯一优先输入是`ArtSource/refinement/hand-poses/attack-keyposes/stage10/candidate/locked_locomotion_inputs.json`。本次实读SHA为`3a3090ba4181f84169df9e8d7374505ddab5ff4cf3948d183800b116143feab6`；01文档旧登记的`c05ec72b...`不是本次实读身份，Root最终收件按实际清单及依赖闭包冻结。两个raw／preview以及各自metadata、verification、骨锚、独立surface audit的登记SHA已逐文件核对，全部匹配。

rig为`refined-base60k/rig.glb`，SHA `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`，真实78骨。raw右指UNBAKED，preview校正一次；producer只消费raw。

| 正式alias | stage10 raw | raw SHA-256 | 实际采样 |
| --- | --- | --- | --- |
| idle | `locked_guard_idle_raw.glb` | `f1aa9efbb2060c36df2047021fcdc1d1b1127a25bae876513c755aa73da486b1` | 91键，全常量STEP；181个key／midpoint审计 |
| walk | `locked_guard_walk_raw.glb` | `0e3a6c60c557cfbdfa979ffd9c98098c4d0306474f8e18dc7ae46f327ceb534e` | 185键，228条常量STEP＋6条腿rotation LINEAR；369个key／midpoint审计 |

两源0→1.5s，prefix 0→1/3s全守势；循环[1/3,1.5]、时长7/6s。Head的真实9层祖先链全key／midpoint local TRS锁到canonical；raw／preview在0、loopstart与1.5的234条TRS同守势。relative canonical proxy difference=0证明相对守势稳定，清单的`absolute_proxy_high.status`仍为OPEN。

绝对错位证据为stage9 `audit/runtime_alignment_findings.json`，SHA `078e616b4b6fcb2a0679516290020a23713965ba5fe9da64c4da86040b8945d0`。例如旧base实际头面bbox中心X约-.0050m，旧offset proxy X约-.2479m，差约-.2429m；这是相对锁定不能自行解决的绝对校准问题。此旧报告的模型身份是历史6f232候选，不能直接当未来三个新target的最终验收。

### Root已选定的schema v3最小路径

Root已审架构并选定唯一正式manifest schema v3：

| 来源合同 | 唯一负责clip | rig与处理 |
| --- | --- | --- |
| motion41 | fall／turn／hit_body／hit_head／hit_side，共5项 | 现有真实41骨来源及原消费保持 |
| locomotion78 | idle／walk，共2项 | stage10真实78骨来源；复用现78世界rest delta／目标骨长／握持处理 |
| attack78 | attack_overhead／attack_left／attack_right，共3项 | 既有三攻击真实78骨来源及严格106键合同保持 |

正式仍10clip、一个producer。只替换idle／walk的来源，不把其余五项同步换成新反应源；不复制retarget核心，不让新78走41校验，不设v2 fallback、旧idle／walk兜底或第二运行库。`locomotion78`与`attack78`区分来源时序合同，底层共用78骨重定向实现，不能仅把三攻击106-key校验改松后笼统接受所有78骨源。

**切换时机明确：05仍在旧v2私有manifest复建颈桥；当前共享producer／manifest保持冻结。等Root收齐最终raw和连续图／audit后，再统一升schema v3并迁正式输入，既不提前破坏05复建，也不为保留v2另加兼容／fallback路径。** 本节为已定架构与数据合同，当前没有实施代码。

### Root producer最小改动顺序

1. **显式schema v3来源分组。** 旧motion41组移出idle／walk，仅保留五项；新`locomotion78`组绑定stage10及同一真实78骨rig／SHA，attack78仍三攻击。`validate_manifest`从v2七旧动作＋三攻击收口到v3的5＋2＋3唯一合同，`production_binding`同时纳入locomotion组、locked input SHA、grounding与proxy合同身份。移出旧idle／walk的41手姿消费，不将新源送进41-joint／Root校验；正式切换不保留v2 fallback。
2. **分开rig与时间线约束。** `retarget_clip`接受显式`locomotion78`，复用其现有attack78的同名78骨映射、target本地骨长、native右手和作者左手核心；不复制实现。decoder已支持STEP／LINEAR，无需新播放器。`validate_source_clip`为attack78保留106键0→1.75s，为locomotion78严格核真实91／185键、0→1.5s、完整234轨、locked祖先链及六条moving腿；不能pad为106键、拉伸至1.75s、误送41或放松全部78校验。
3. **逐角色重定向并保插值语义。** base／indigo／veteran共用78世界rest delta处理及一次右指校正，保持mesh／rest／IBM／骨长。按Root合同保留常量STEP、六条腿rotation LINEAR；现retarget统一输出LINEAR的序列化点需一并改到该明确合同，不以所有轨重采成LINEAR替代源锁定证明。最终每key／midpoint复核祖先链和世界锚，raw零差不能抄成target零差。
4. **五段guard同基准grounding并保护锁链。** 同一target的idle／walk／三攻击五段guard根平移使用同一canonical基准，复用`attack_grounding.py`的Foot/Toe真实权重表面、LBS、parent空间换算和prepared plane Y=-.028；entity originY=+.028仍Root只加一次。现helper写死三攻击／106键／LINEAR BoneRoot，不能只把名单扩成5个就跑。推荐对同一target canonical guard求idle／walk共同竖直根校准，三攻击首尾用相同canonical根结果，攻击中段沿既有实际鞋面grounding。locked walk若每帧随最低鞋点动态补根，就不能继续声称祖先链全周期锁定；若共同静态校准在某target步态超现有plane容差，应修目标步态／制作源并重验，不增动态root fallback。保留真实source key，不叠水平carrier，不改变实体移动归属。
5. **重绑绝对proxy并统一导出。** 复用`export_attack_profiles`的final idle参考求local offsets；新idle全程canonical，现idle@1.00可继续作参考。用新prepared idle重新算offset，再重生三攻击profile，不能继承旧idle的约.243m错位offset。导出同组idle／walk的prepared head、bodyBottom／Top、bladeBase／Tip，以及loop／stride／六个支撑边界；最终上身若经全key／midpoint验证为常量，可用profile绑定的共同canonical sample，不再手写standing曲线。绝对mesh覆盖和Y／轮廓仍须实物核对，固定旧目标中心本身不能算验收通过。
6. **新身份闭包。** idle／walk动画和proxy校准均变了，三角色body／刀版GLB、profile、clip semantics、来源依赖、review request和binding全部重生，不能沿用weapon-only的7373身份。Root审核后一起发布正式library／app，09再从正式library重生Kotlin数据和精确pin；不从候选独立发布。

### 同组最终profile的必要数据合同（仅文档）

下列数据进入最终角色profile并绑定新模型SHA／新binding；是本轮最低消费需求，不是新增独立配置层。manifest升级为v3不等于profile已自动具备这些字段，Root实现时应一次对齐exporter、09生成器与消费者。

| 数据 | 必须表达的语义 |
| --- | --- |
| 角色与来源身份 | final model SHA、profile SHA、manifest v3 binding、locomotion输入清单SHA、idle／walk clip semantics；canonical参考与最终proxy offsets的来源 |
| idle／walk实际姿态 | 最终prepared actor-local下的head、bodyBottom／Top、bladeBase／Tip及真实source times；由新target取值，不能复制raw锚或旧站立常量 |
| source时钟 | source范围0→1.5、prefix0→1/3、loop [1/3,1.5]、duration7/6、stride1.45m；新mode与骨架合同为locomotion78 |
| 唯一gait时钟 | 实际signed `enemyGaitMeters`为权威，Animation／Proxy／Audio共享它的同一phase映射；无第二套累计步距或反向假时钟 |
| 六步支撑边界 | 归一化phase k/6，k=0…5；对应source1/3+k×7/36；正播支撑脚L/R/L/R/L/R，反播相反。显式标为由stance/swing区间推导并经Root最终落脚审核后冻结，不能伪称源已自带touchdown事件 |
| 采样／插值 | 新idle 91键、walk185键；常量STEP／六腿LINEAR的真实合同、canonical全链key／midpoint锁定证据；若最终变更采样，连同正式身份重新审核 |
| grounding／绝对proxy | 五段guard同一target根基准、entityY=.028只一次；每target实际蒙皮绝对位置和moving分支的校准证据。relative0只作相对证据，absolute HIGH状态单独保留 |

上身最终若验证为全周期同一姿态，可以让profile明确共用canonical sample；这必须是final retarget＋同组grounding＋握持之后的事实，不能预先删掉新idle／walk实际姿态证据。音频只消费共享步态合同，不从render frame的measurement flags反推脚步。

### 09后续runtime接口，收到Root下一项后再改

- `EnemyAnimator`静止IDLE选正式新idle，moving IDLE选新walk。现`WALK_STRIDE_METERS=1.45`、`WALK_LOOP_START=1/3`、`WALK_LOOP_DURATION=7/6`可保留，signed gait仍用现正模公式；最终profile合同必须与三常量对应。source carrier不再叠实体平移。
- `ArenaOpponents.attackPose/contactPose`移除moving IDLE→旧`EnemyContactPose.standing`分支，idle／walk／attack guard统一取新校准profile头身刀锚；verified locked上身可共享canonical sample，但须由profile绑定，不按骨数猜测或回退旧数据。
- `ArenaSession`维持现0.65m/s、signed `enemyGaitMeters`、生命周期边界与Root recoil单次Stage变换。本轮不加移动门控／settle timer或改攻击节奏。任意gait相位停止／转攻击的腿连续性仍需最终视频、target和SDK crossfade核对；上身锁定不等于双脚任意相位闭合。
- hidden初始化契约继续保留：骨架／skinned查询显式includeDisabled，构造期不启用隐藏角色；Root输入probe与tangent改动不动。

### 给11的脚步消费变更通知

**整loop仍前进1.45m，现在六步；当前`CombatAudio.kt:255–269`仍按.725m一声，只播2声／loop，真实应6声，频率少三倍。11文档两步结论及`CombatAudioTest`旧.725专项仅属旧源，需随同组profile更新。**

| 合同量 | stage10准确值 |
| --- | --- |
| steps／pairs per loop | 6／3 |
| 相邻落脚载体距离 | 1.45/6 = .2416666666667m |
| 同脚相邻落脚距离 | 1.45/3 = .4833333333333m |
| 相邻支撑边界source间隔 | 7/36 = .1944444444444 source-second |
| 名义.65m/s下相邻game间隔 | 29/78 = .3717948717949s |
| whole game loop | 2.230769230769s |
| 名义步频 | 161.3793103448次/分钟；旧.725仅53.7931034483 |
| nominal source rate | .5229885057471；source carrier1.242857142857 × rate = game.65m/s |

11应读共享locomotion profile的loop／stride／支撑边界，沿同一个有符号`enemyGaitMeters/1.45`未取模周期消费；不能只把.725换成.241667后继续另起绝对距离累计器。由stance区间推导的周期边界为`1/3+k×7/36`（k=0…5）：.3333333、.5277778、.7222222、.9166667、1.1111111、1.3055556s；正播进入支撑脚L/R/L/R/L/R，反播在同边界进入相反脚。初次绑定只建游标，起点不额外响；source1.5与下一圈1/3是同一接缝，不能双播。

建议冻结去重规则：正向(previous,current]、负向[current,previous)，用整数周期＋边界索引处理跨圈与负gait，重复快照不发声，不用独立stepIndex++猜脚。沿11已有换轮／mute／resume／motionGeneration边界重新定基，不追播暂停时间。跨大位移或多边界时先推进游标到当前，仅消费本帧允许的最新事件、不把旧声排到后续帧；现每present最多一声／大跳保护可以保留，其阈值不是stage10新合同，本轮不擅改。

当前stage10只有stance/swing区间，**没有独立step_events／touchdown数组**；上述六边界和脚侧属于据区间推导的消费方案。measurement float32边界flags可能both-stance／prefix_guard，不能直接以flags变化发声。Root最终profile应显式冻结六个边界及正反脚侧，再交11随新binding验收音画一致；本轮未改11代码／文档，通知合同在09交接由Root并行入口接收。

### 验收闸门和本轮边界

- 01最终同机位连续图／视频及最终input SHA由Root收件；当前hash核对不代替视觉审核。
- producer专项至少拒绝78误进41、错误91／185时标、锁链漂移、重复右指校正、重复entity／carrier位移、旧两步节奏、旧offset混新clip。最终足面、祖先链、蒙皮头／躯干绝对proxy及blade markers覆盖key／midpoint，不能只列relative0。
- runtime专项覆盖signed gait双向、跨圈、任意步态停止、IDLE→attack、命中／反击回守、暂停／追踪丢失／换轮及真实180ms crossfade；头身刀yaw／origin／recoil只一次，11六步声与可见落脚对齐。
- **absolute proxy HIGH仍OPEN。** 最终三角色mesh／新校准proxy绝对位置、moving分支替换及SDK过渡一起通过后才关闭；raw relative0不是关闭依据。
- 本轮仅本文件方案，未改producer、manifest、library/app、生成器、runtime、Core、测试或11代码，未运行制作／构建／设备。Root独占正式集成，09等待下一项明确源码任务。


### 本轮架构补充后的冻结边界

Root指定schema v3合同已写入方案；05的v2私有颈桥复建与共享producer当前均未被本路修改，待最终raw收件再由Root统一升级。Root报告已读到非零真实左右SDK姿态，正在修模拟器InteractionMode入口；实际按键→判定仍未通过，本路不将姿态可读等同输入验收完成。当前所有producer／app／运行源码／生成器／专项继续冻结，仅本09方案与数据合同有文档更新。


## 09 runtime接入执行与给canonical_locomotion_pipeline的数据合同（2026-11-11）

Root已授权09开始独立type／消费者与专项。ownership为`EnemyAnimator`、`AttackBankProfiles`、`ArenaOpponents`及相关测试；`ArenaSession`只允许在现两个代理调用传入`enemyGaitMeters`。Root includeDisabled、single-active、原生SDK输入、伤害／阈值／半径不动。Python producer／manifest／候选由`canonical_locomotion_pipeline`独占；09不手写最终generated arrays／pin，等候选实落盘再生成。

### Python→09消费者所需的最终profile合同

下列是先前消费者需求；字段布局现以文末“实际schema3字段与runtime交付”为准。实际候选已统一为`source_contract`与`locomotion.idle/walk`，未同时支持此处早期建议的clips包装，也无v2／standing兼容回退：

- 顶层仍含`character_id`、最终`model_sha256`、共同canonical idle求得的`proxy_calibration`与三方向`attacks`；同组binding覆盖新idle/walk及offset。profile明确升级后的schema，不能让旧schema2 profile混入新consumer。
- `locomotion.source_loop_seconds=[1/3,1.5]`、`stride_metres=1.45`；这是一整圈六步总距，不是单步距。
- `locomotion.clips.idle`与`.walk`各含`clip`（正式别名idle／walk）、`animation_semantics_sha256`及实际prepared `samples`。sample字段沿用三攻击：`source_seconds`、`head`、`body_bottom`、`body_top`、`blade_base`、`blade_tip`；所有值为最终同target offsets、同grounding后的actor-local米坐标，非raw值或旧offset值。真实91／185时间线及canonical markers不可手工重造。
- `locomotion.step_events`冻结六个`phase`（k/6，[0,1)）、`forward_foot`与`reverse_foot`（LEFT／RIGHT）。phase0正播L、反播R，此后交替；这仍须Root按最终stance审阅确认。source1.5与loopstart是一条边界，首次定基不发声，不能给0和1双事件。

09类型将为`PoseClipProfile(clip,samples)`和`LocomotionProfile(idle,walk,loopStartSeconds,loopEndSeconds,strideMeters,stepEvents)`；动画／body／blade统一调用其`sourceSeconds(moving,gaitMeters)`与`sample(...)`。signed gait正模处理负距离和跨圈，不假设上身绝对恒定；即使源已锁链，也插值最终实际sample。`CharacterAttackProfiles`最终应持有mandatory locomotion数据，不以null／旧standing／old attack@0作为兼容fallback。正式数据未交前先完成可独立验证的type与选择函数，不凭空填入最终角色锚或身份。

最高HIGH继续OPEN，最终实际profile、绝对mesh对齐与组合画面通过后再由Root关闭。


## 实际schema3字段与runtime交付（2026-11-11）

Root `canonical_locomotion_pipeline`私有产物实际落盘后，09读取其schema3 request／characters／三GLB／profile，按实际模型与profile SHA检查一致，才执行本路生成器。当前快照binding为`ff3ca3920261a6f5574497395f88e69284f2a66dd3166674b97fcf84c43af70c`，候选目录`ArtSource/tripo-warrior/review/locomotion-v3-candidate`；不是手填最终坐标或身份。准确完整身份见`ArtSource/refinement/combat-direction/locomotion_runtime_identity.json`。

| 角色 | 候选模型SHA-256 | 候选profile SHA-256 | 实际idle／walk样本数 |
| --- | --- | --- | --- |
| base | `b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09` | `372d3eb4feff89f5cbbfe6695e9a34f4281cffdf9fb03a71cc84e140a099e229` | 185／369 |
| indigo | `21fae35e61d07d1eff41eb4ca5906261ec88d70e7699e2d37c0ce750b5efaf0f` | `bdd168343cf026354aed50b05f5d0768ed68a538dc1bcb238e063c80ad9e6689` | 185／369 |
| veteran | `3ecb6d13390b3c09df9eddaa450c29f75fd9e179ae96b49d9a87e203d9ad16e1` | `869e4db939c03297957b2bc9c59aef075940d865e6c4570a375f6671ba864eb2` | 185／369 |

实际唯一JSON合同为：顶层`schema_version=3`；`source_contract`含locomotion78、loop_start/end_seconds、stride_metres=1.45、steps_per_loop=6、contact_phases；`locomotion.idle`与`.walk`各自含clip、source_range／source_loop_seconds、animation_semantics_sha256、真实prepared samples。样本head／body_bottom／body_top／blade_base／blade_tip与三攻击采用同一final-target校准。six-step event由已校验的contact_phases各stance起点推导，省略循环末尾重复接缝；不是measurement flags触发，也没有虚构源自带touchdown数组。

### 已完成代码

- 新`LocomotionProfiles.kt`：`PoseClipProfile`保存真实samples，`LocomotionProfile`保存mandatory idle/walk、loop、stride与六步合同。signed gait先取remainder再归一，处理正／负／跨圈并避exclusive end；新idle五锚全period恒定、walk五锚seam exact闭合、六个均匀phase与正反脚侧均强制校验。**当前idle是Root指定locked STEP常量，Animator明确seek真实首样本并pause，未虚构第二套idle时钟。** walk仍插值真实profile，不简化为手写guard。
- `AttackBankProfiles`提取共享`samplePose`，Character必须包含LocomotionProfile，不提供null或v2默认。新的三攻击数据及idle185／walk369样本从实际schema3候选生成，共954攻击＋1662 locomotion样本；未手写arrays／pins。
- `ArenaOpponents`用同一`EnemyPoseFrame/selectEnemyPose`选clip与source sample：静止idle、移动walk、guarded HIT canonical idle，三攻击仍逐phase。moving IDLE→旧standing分支已删除，body／刀根尖来自该同一frame；standing只保留在现native非guard HIT／DEAD尚无新reaction profile的既有范围，不作为locomotion fallback。
- `EnemyAnimator`直接读取同一poseFrame的clip及sourceSeconds，idle／walk均manual seek+pause；删除重复旧walk时钟常量和自由速度计算。保留Root两处includeDisabled查询、hitstop接触前持姿、反应clip／死亡时钟和crossfade。Rootsingle-active加载、原生输入入口均未改。
- `ArenaSession`本路只在两处代理调用各加`gaitMeters=enemyGaitMeters`。文件现有native输入观测、移除Desktop路径等diff属于Root工作，未回退或重写。伤害／识别阈值／半径未动。
- 生成器只接受schema3及当前唯一字段布局，核binding／model／profile／clip semantics和六步合同；增加idle→walk exact、idle→三攻击首尾距离≤1e-6m的canonical边界拒绝验证，此容差只用于浮点重定向数据检查，不是战斗阈值。新类型不改变原三攻击phase映射、ACTIVE中点或成功恢复语义。

### 验证及发布边界

`run_isolated_tests.py --focus`以本机真实PICO6.1.9类型编译，**64／64通过**；包含新13项clock／data拒绝、7项中央消费者、实际三角色idle/walk/三攻击同校准、gait正反及Stage变换。新fixture是明确虚构样本，不冒充角色数据。生成器专项**5／5通过**，覆盖精确重现、身份漂移、旧两步／错phase、跨clip canonical漂移拒绝。`--bank ArtSource/tripo-warrior/review/locomotion-v3-candidate --check`精确重现，限定文件`git diff --check`通过。未跑共享Gradle、producer、Blender或设备。

当前实物中idle→walk五锚exact相等，idle→三攻击首尾最大偏差小于1e-6m；只是数据与代码阶段证据，最高HIGH仍OPEN，Root实际模型／proxy／组合画面验收后才可关闭。11的consumer本路未改，需用新profile的stride、stepEvents与同signed gait；旧.725消费问题仍须11／Root接线。

**发布闸门：当前generated data已用新候选，app三GLB仍旧weapon-only。不能直接把此源码打进旧GLB包称完成；Root须批准并原子发布本组模型／profile至正式library/app，再用默认正式library重新生成Kotlin数据与身份验证，最后共享构建／安装。** `DEFAULT_BANK`仍唯一正式library，不改为候选默认；本轮仅用显式--bank真实私有候选为Root组合，正式默认在旧v2库上会拒绝，不做兼容回退。

独立review撤回了动态idle finding（与locked idle合同不符），确认shared clock、seam、六步、guarded HIT、hitstop/death与Root初始化保留。其提出的跨clip数据合同缺口已补生成拒绝专项；原子发布与最终画面闸门继续保留。本轮09代码／data／生成器／专项完成后重新冻结，Root接管共享构建、发布及剩余小修。


## schema3正式发布后的最终来源收口（2026-11-11）

Root已正式publisher成功，本路一次性核对正式library/app及profile/manifest一致后，实际运行默认来源：

`python3 ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py`

`Prepared source`已收敛到正式library。binding／三model／三profile数值与已收私有候选完全相同，因此runtime精确pin无需变造；Kotlin身份专项命名改为published canonical bank。Python专项取消按generated header动态选择私有目录，明确验证并仅消费`DEFAULT_BANK=ArtSource/tripo-warrior/library`，防止旧candidate和旧数据一起假绿。reaction清单当前binding也已更新ff3；六组reaction raw／preview／metadata本体和未进入bank的状态保持。

| 角色 | 正式model SHA-256 | 正式profile SHA-256 |
| --- | --- | --- |
| base | `b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09` | `372d3eb4feff89f5cbbfe6695e9a34f4281cffdf9fb03a71cc84e140a099e229` |
| indigo | `21fae35e61d07d1eff41eb4ca5906261ec88d70e7699e2d37c0ce750b5efaf0f` | `bdd168343cf026354aed50b05f5d0768ed68a538dc1bcb238e063c80ad9e6689` |
| veteran | `3ecb6d13390b3c09df9eddaa450c29f75fd9e179ae96b49d9a87e203d9ad16e1` | `869e4db939c03297957b2bc9c59aef075940d865e6c4570a375f6671ba864eb2` |

本轮五份运行逻辑文件SHA与开始时逐项相同：EnemyAnimator、ArenaOpponents、AttackBankProfiles、LocomotionProfiles、ArenaSession。全部2616个typed sample数组文本SHA仍为`781a861dfd3c30384678fbdd3685028d4cd1f56e0aee847ea78a9ce9a774f3a4`，没有动作／坐标修改。Root原生输入共享链、NativeMotion日志、onTick规则、includeDisabled／single-active保留；ArenaSession本路累计仍只有两处gait参数。

本节关闭前节“candidate data对旧app资产”的身份发布gate；前节候选snapshot原样保留，不追改历史。最高画面／交互HIGH仍OPEN。Root反馈原生输入共享链257项已通过，本路未重复运行；冷启动控制器PENDING／DEVICE_NOT_SUPPORTED属于Root系统状态排查，本轮未据此更改数据或输入。

本次改动清单：默认正式来源重生的`AttackBankProfileData.kt`、仅正式library的Python生成专项、Kotlin身份专项命名、reaction当前binding、此交接及`published_locomotion_runtime_identity.json`。其余runtime源码／私有基准／旧身份快照冻结。Root继续统合共享构建、设备及剩余小修。


最终实跑：默认正式library `--check`通过；生成器5／5、PICO6.1.9实际类型隔离编译／JUnit64／64通过。Root可开始共享构建。本路数据／生成器／专项／runtime现全部重新冻结；交付不包含共享Gradle或设备操作，最高画面／交互HIGH保留给Root最终判定。


## KTX正式整组身份收口（2026-11-11，identity-only）

Root已用唯一publisher发布`b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f`整组library/app，包含dao_grip。本路实际核到正式request、三个model/profile与app副本一致后，仅执行一次DEFAULT_BANK生成：

`python3 ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py`

| 角色 | KTX正式model SHA-256 | KTX正式profile SHA-256 |
| --- | --- | --- |
| base | `722ffe6e9d3d498629b257e88aaeaf3b0ad368e5c5a37be87ccb85d63a6cf83e` | `df8a8531a4e94ef3651f8b9d889688e418a8b5e07a7685587300fa6899da657e` |
| indigo | `94773349741af7cdd2616bb3f5970c5c9fa16f16199c1d0ce5bf6fde6ee0c54e` | `ef1a853a1801ddd4a2f8a28292a7ad6358385c2cb6f1bea0ca1b8c2e524ad73a` |
| veteran | `cabf24597a83d46495ad67b451867aaf5e1dad1bbb5df21cae286513af9a17a5` | `2a0c8ae7a824dcf952fcf3b80e8b4431017b0f16ad30ff0e2947b470f7de0ee6` |

精确Kotlin binding／三model／三profile pin与Python binding／model pin全部取实际正式metadata更新；reaction当前消费binding改为b03f55e6，六组reaction来源SHA和状态保持。`DEFAULT_BANK`仍仅正式library，未改生成器逻辑、未取私有candidate作默认。

本轮前后EnemyAnimator、ArenaOpponents、AttackBankProfiles、LocomotionProfiles、ArenaSession、EnemyCombatStateMachine、生成器及隔离runner SHA逐项完全相同。typed样本数组文本SHA仍是`781a861dfd3c30384678fbdd3685028d4cd1f56e0aee847ea78a9ce9a774f3a4`。Root关于profile剥model SHA的整JSON与全部非image GLB守恒结论记录为Root audit，本路未重复审计资产。没有改动作时钟／判定／阈值／半径／输入／资产／Gradle／设备／Git。

本轮身份产物为`ktx_published_locomotion_runtime_identity.json`；先前`published_locomotion_runtime_identity.json`及各私有快照保留原ff3历史身份，不追改。Root接管共享新APK与实际画面／输入验收，09只交限定身份更新与focus验证。


KTX身份更新最终实跑：默认正式library `--check`通过，Python生成器5／5、PICO6.1.9类型隔离编译／focus JUnit64／64通过。独立只读复核确认app/library/profile内部/characters/review/Kotlin/Python/reaction全部一致，四个身份文件无旧ff3及旧model/profile pin或candidate locator残留。本路现全部重新冻结，Root可开始共享新APK。
