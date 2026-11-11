# 09 · 正式动作bank与战斗表现接线

## 当前状态

Root已收三方向代码。本轮已按Root新授权完成weapon-only正式库身份接入：生成器默认正式library，Kotlin数据和当前身份pin已更新至7373 binding，40项隔离专项与3项生成器测试通过；动作逻辑未动，locomotion HIGH原样保留。09已重新冻结源码、生成器、数据与专项，交Root共享Gradle／设备组合验证。

## 目标

把新站姿、正劈、左右斩接到真实正常循环，攻击方向、动画、代理、刀路、接触时刻与受击反应一致。参考《荣耀战魂》《只狼》《影之刃零》的来刀辨识、支撑、卸力与收势，沿已有能力完善。

## 所有权

负责 content/EnemyAnimator.kt、runtime/ArenaOpponents.kt、新AttackBankProfiles数据与加载／生成接口、ArenaSession.kt中既有方向调度与接触pose选择、EnemyCombatStateMachine.kt中反击方向参数转发及专项测试。本文件为交接。Root保留其它战斗数值／核心判定，08可能需要emitImpact转发补丁，交Root统一应用。

01是动作作者，Root内部character_grip_polish负责Python producer、manifest及正式发布。你不改这些制作源或GLB，不写Main/HomeStage。

## 当前输入

当前生产真源为 `ArtSource/tripo-warrior/library`，weapon-only正式binding `7373f5937cd19d1306b861ca0e1654e040977eafb3af6685618742e3e0716cff`，已实际落盘并完成三个GLB/profile/characters/review的身份一致核对。09生成器默认来源已收敛到正式library，Kotlin数据从该目录重新生成；旧review/attack-bank-candidate仅作历史来源比较，不作生产默认。新头未通过动态黑颈验收，本次未并入。

三攻击动作仍来自冻结的stage5 `attack_bank_inputs.json`；正劈raw SHA `377bcfc1197d1ae84d2c1784dc1de4004b68d09189528025786578c0b95987b9`。来刀侧为玩家视角，LEFT对应attack_left／slash_to_left，RIGHT对应attack_right／slash_to_right。prepared +X为演员左。源phase0／.65／.90／1.10／1.75，接触1.00秒=ACTIVE中点100ms。横斩游戏550／180／200／600ms，正劈650／250／200／650ms。

本次仅换新dao资产身份：三角色body、10clip清单和profile除model_sha256之外全部字段逐值相等；生成后954样本的typed数组文本SHA亦与换刀前完全相同，动作逻辑未改。当前准确模型与profile身份见文末本次正式库更新表及 `ArtSource/refinement/combat-direction/formal_library_identity.json`。locomotion HIGH未关闭。

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
