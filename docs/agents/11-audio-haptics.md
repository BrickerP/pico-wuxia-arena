# 11 · 打击声音、场景声与触觉数值

## 当前状态

2026-11-11已接手并完成真实刀声、衣料、雨声混音与消费源码；音频/触觉35项与资产6项通过，扩展共享战斗回归有8项失败，整包与Space Pro验收仍由Root负责。

## 目标

用可信金属、布料、风切、脚步和雨夜声景建立近身重量感。参考目标游戏的起手／接触／余响分层，让普通斩、硬甲、格挡、弹反、要害和致命有可辨节奏。

## 所有权

负责 runtime/CombatAudio.kt、CombatFeedbackProfile.kt中的音调／触觉accent数值、ArtSource/audio/与ArtSource/refinement/audio/、相应app/res/raw音频及专项测试。本文件为交接。保留既有hitStop／死亡时钟函数与数值，Main触觉SDK调用由Root接线。08负责视觉，勿改CombatEffects与ArenaSession。

## 制作队列

1. 读取当前11种WAV和同批事件音频路径，识别合成感与缺少起手／材质层次的问题。正常速度和致命慢动作均给对照短片／音频。
2. 优先使用已有素材和授权明确的真实CC0／自制foley，再做合成、EQ、短瞬态和余响。来源、许可和派生处理可追溯。不得用目标游戏原声作为交付素材。
3. 接触材质kind、真实appliedDamage／zone／fatal共同决定层次，队列保持新鲜度与有界并发，场景不可用／暂停／重开／释放停止并清理。
4. 补玩家挥刀风切、湿石脚步与雨夜远近声景。若做空间定位先核官方SDK与现有依赖能力，无法证明HRTF时明确实际实现范围。不可猜API或新增SDK／Gradle依赖。
5. 触觉沿已有公有接口调短脉冲、尖锐弹反和较厚致命重音，保留VR动作即时性。音量、peak、频率、duration及重叠优先级给可读数据，Root真机验证。

## 首轮交付

普通命中、金属格挡、弹反三种明显改善的实际WAV／前后试听与对应消费代码。随后补致命、挥刀和环境声。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

### 2026-11-11 · 首轮实物已交，继续专项回归

来源代码节点 `562449af40ee984ddd8ef61be5c339ac9bea2de5`。本路未运行共享Gradle、设备、Git提交，没有改Main/HomeStage、hitStop与死亡时钟。独立读取了当前11种WAV，均为正弦与噪声合成，已把原始11种声音完整冻结到 `ArtSource/refinement/audio/before/` 并写逐文件SHA256。

**实际可试听产物**：

- `ArtSource/refinement/audio/contact_before_after.wav`：19.48秒；普通命中、格挡、弹反、硬质、护甲、挥刀、处决依次旧/新，时间表同名JSON。
- `ArtSource/refinement/audio/fatal_normal_vs_slow.wav`：原致命0.90×、新普通1×、新材质与致命重音0.90×、处决1×/0.90×。敌人动画仍走既有死亡时钟，音效不跟0.35×动画作全局降速。
- `ArtSource/refinement/audio/combat_rain_sequence.wav`：9秒混音演示，含雨、挥刀、接触、弹反、步声、致命叠层；这是离线音频，不能证明端内接触同步或VR手感。
- `app/src/main/res/raw/arena_*.wav`：沿既有11种命名，新增 `arena_step`、`arena_rain`，共13种、48kHz/mono/16-bit；声音资源属于本路明确所有权，不触碰角色/场景正式资源。

**实录来源**：StarNinjas两把刀录制的20种攻击/碰刀声（OpenGameArt CC0）用于刀刃与挥刀主体；Ylmir麦克风录制的Rain(loopable)（OpenGameArt CC0）用于8秒雨循环和步声水层；Kenney官方Impact Sounds（CC0）用于身体/衣物冲击与混合重量。Kenney作者未逐项声明实录，故不把它描述成已确认实录。来源、许可页面快照、原zip与每文件SHA在 `ArtSource/audio/sources/sources.json`、`licenses/`。

**代码与接入**：`CombatAudio.kt`继续从已存在的Main `audio.present(state, events)`入口消费真实CombatImpact整批。材质决定底声，appliedDamage调有限音量，zone/head调音调，fatal保留材质并叠执行重音。加载待播上限24且120ms过期；短音最多10路主动按优先级回收，给雨声保留一路，避免SoundPool无通知偷声后雨声永不恢复。弹反5/致命6高于普通3，场景雨0。玩家真实刀尖速度跨1.45m/s阈值触发，回落0.70m/s才重新预备，最短180ms间隔，motionGeneration/暂停/切轮清理。敌人脚步随既有enemyGaitMeters累积步距，不用时间猜移动，不补播跳变积压。

`CombatFeedbackProfile.kt`只改soundRate和haptic accent数字；保留visualScale、lightDuration、hitStop、deathElapsed代码与数值。普通/硬质/弹反分别26/12/14ms，弹反频率300、fatal72ms；具体声压与触觉必须由Root真机确认。Main内同帧触觉消费仍由Root负责。

**限制与Root review**：这一路没有画面变更；正常游戏视距的端内画面/同步、Space Pro扬声器与触觉未验证。Main现有触觉按最大ID去重（会漏掉同批较小乱序ID），且同手多接触逐个发；建议Root统一改为本轮集合去重并按同手同帧选择最高强调，勿以音频单元测试代替此接线验收。终局DEFEAT先设USER暂停再发PLAYER_HIT，仍保留现有终局末击例外，但雨/步/挥刀只在FIGHTING播放。

### 2026-11-11 · 队列制作完成，Root审阅包

已补HaelDB确认实录布料（CC0），普通命中/护甲/玩家受击/处决衣料层沿此源；原Kenney只保留punch/plate/concrete重量。雨循环延长到8秒，最大解码768,000字节，无SoundPool截断。敌人步距对齐现有EnemyAnimator 1.45m完整步态的两脚，单步0.725m，替换首版0.43m以免每个动作周期发3.4个脚声；同一present最多发1步，瞬移不积压。

**已通过**：

- `python3 ArtSource/audio/run_audio_tests.py --audio-only` → **35/35**（真实CombatAudio/Feedback/Core/ArenaState编译，Android输出用注入记录器，实际声卡与SDK未调用）。30项音频：首批/乱序/切轮去重、120ms边界、24条有界与优先级、保留材质的fatal叠层、暂停/场景/终局清理、真实玩家挥刀、0.725m步距、10短音留雨和close。
- `python3 -m unittest discover -s ArtSource/audio -p test_combat_audio.py -v` → **6/6**（实际最终13种PCM、25ms内接触、首尾fade、8秒雨接缝、1MB预算、削波、冻结前版SHA、生成器/产物/166个源媒体及4套原包SHA、四套CC0证据）。
- 独立四面review：正确性、可维护性、UX/验收边界与依赖漂移；无本路待修严重项。hitStop/deathElapsed/visualScale/lightDuration的diff保持为空；未新增依赖或配置。

**不可扩大通过结论**：首轮共享51项曾通过，但后续共享ArenaSession三方向与接触代理/core变更后，最新默认 `python3 ArtSource/audio/run_audio_tests.py` 为51项中8项原CombatFeedbackTimingTest失败。原fixture没有产生预期strike/impact，因此死亡与恢复链后续断言失败。本路未改此fixture或其它路生产代码，不能声称最新共享51项通过。失败原文和源码SHA已冻结在 `ArtSource/refinement/audio/shared_timing_regression.txt/.json`；通过的本路35项证据在 `audio_policy_checks.json`。请Root结合09/08的真实接触与方向变更对齐fixture后统一回归。

**Root可直接审阅/构建**：本路任务队列（首轮三音、致命、挥刀、环境、触觉accent与专项检查）已制作完成。无需Main新音频入口，资源名沿用且新增step/rain已落盘。请在共享构建空闲时运行所选回归并验证真机；尤其review末击音画同步、刀刃实录的实际听感、近身雨/步声比例和300频率/72ms重音。当前没有任何端内新画面或已通过Space Pro手感的结论。

最终文件/SHA索引：`ArtSource/refinement/audio/review_manifest.json`。详细参数与来源：[ArtSource/audio/README.md](../../ArtSource/audio/README.md)。


**共享树并行变动提醒**：第一轮独立51项通过后，最新重跑中音频/触觉35项仍过，但原CombatFeedbackTimingTest出现8项失败（真实strike未形成impact，死亡/恢复流程随之失败）。当前不是音频消费测试失败，正在保留最新源码SHA核查并按实际结果分开报告；不修改其它路ArenaSession/core来迁就本路测试。详见 `build/audio-jvm-tests/result.txt` 与 `report.json`。

## Root组合审核与下一步

Root已补CombatAudio warning注入，标准Android单元环境可记录故障告警并验证失败样本不阻塞已就绪材质。已加入CombatHapticContacts，按回合集合去重并每手每帧选择最高强调，保留处决/技能双手与终局末击。原Main最大ID过滤已移除，6项正常/乱序/暂停/回合/双手/末击回归覆盖。当前完整250项组合回归通过，早前8项timing失败不再沿用。实际声压、音画同步和Space Pro触觉仍未验证，运行WAV/代码保持本轮冻结。

## Root本轮组合审核与续派（2026-11-11）

审核：13WAV、现场雨声/步态消费和逐手最高优先触觉已集成，单次事件去重/暂停消费回归通过。

下一步：冻结运行文件，后续据实际试听与Space Pro触觉再校准；当前没有原生试听或设备舒适度证据。

## stage10六步Audio消费合同与测试计划（2026-11-11，仅文档）

**当前状态：Root已选stage10六步canonical walk进入私有组合；本路只更新本交接，等待09确认共同runtime clock/type字段后再改CombatAudio与专项。** 旧交付的`.725m/step`与“两脚/1.45m”仅是旧源假设，不能用于stage10验收。此处不把`.725`替换为另一Audio常量，也不新建Audio gait时钟。真实foley、13份WAV、现有播放gain/rate/并发策略与所有accent继续冻结，不新调haptic。Root统一Gradle/native/Git。

### 本次已核对的来源与冻结边界

- 当前工程HEAD：`fd58c04f9b8bc8a0999f633d149fb2897164e53f`。当前CombatAudio SHA-256：`e52309478152f2e470f6840a1eb1649354e46d79d80d035b37cab4953455c47d`；其相对最初review manifest的变化来自Root已登记的warning注入，不能为“恢复冻结”回退。旧review manifest SHA-256：`ea9e7c9c11a6324d7e804188fd7224bd41eab41dca77ad3413ded5608855dc05`，本轮保持原件不重写。
- stage10输入：`ArtSource/refinement/hand-poses/attack-keyposes/stage10/candidate/locked_locomotion_inputs.json`，SHA-256 `3a3090ba4181f84169df9e8d7374505ddab5ff4cf3948d183800b116143feab6`。
- walk metadata：同目录`locked_guard_walk_metadata.json`，SHA-256 `55b2796fd0fd3880f075012a0eb844989a7981d330ff03b53731de5881f0a28d`；真实字段明确6步/3pairs、L_/R_ stance与swing六段。此源没有独立touchdown/step_events数组；支撑边界是从区间推导的候选事件，需进入Root最终profile并经落脚审核后冻结，不能从measurements flags跳变猜事件。
- 只读review确认当前尚无已落盘可共用的locomotion/footfall type；权威输入仍是ArenaViewState.enemyGaitMeters，旧映射在EnemyAnimator私有常量。当前源码仍是`abs(gait-previous)`累计`.725`并`stepIndex++`猜脚。本次未改这段代码，也未运行旧测试来声称六步已通过。早期timing 8失败属于历史证据；Root后续已登记完整250项通过，不把那8项继续当当前阻塞，也不把旧250或旧35+6复用为新六步通过证据。

### 与09共用的唯一合同

生产数据由Root的同组locomotion profile/新binding提供，09负责runtime typed数据和共同phase/clock。Audio只保留“上一份已消费快照”的游标，不积累绝对步距、不按时间估计脚步、不复制loop/stride/carrier/foot序列常量。以下是**语义需求，非本路先行定义的字段名或新接口**；最终名称与类型以09确认文件为准。

| 共同合同必须表达 | Audio用途 |
| --- | --- |
| 同组profile/model/binding与locomotion身份 | 绑定改变时只重建游标；拒绝旧两步或错组数据，不能静默回退旧步距 |
| loop起止、整loop位移、六个支撑边界、每界正反进入脚侧 | 完全读取同一typed contract；不在Audio复制`.2416667`或L/R表 |
| 当前signed gait的未取模周期及其同一phase/source映射 | 正向、负向、跨零与跨loop使用同一权威坐标；不把负gait变abs累计 |
| 当前walk是否实际生效/移动、暂停与连续性边界 | 停步/转攻击/场景或输入失效不发脚声；恢复、teleport、重绑定只重新定基 |
| round/角色/locomotion连续性generation或等价的权威重置标记 | 区分连续反向与新段；不把玩家blade motionGeneration当敌人步态重置依据 |
| 共同边界归属与浮点精度规则（或已解析的脚步crossing结果） | Audio不另设epsilon/hysteresis或第二个取模规则；避免源float32接缝与runtime Double判断分叉 |

准确数量：整loop为1.45m、6步、3pairs；相邻步载体距离`1.45/6=.2416666666667m`，同脚相邻`1.45/3=.4833333333333m`。source loop仍`[1/3,1.5]`、时长`7/6s`；game carrier仍`.65m/s`，整圈`2.230769230769s`，相邻步名义`29/78=.3717948717949s`。这些数字是本节核对依据，**不授权在CombatAudio中复制为clock常量**；source rate约`.5229885057471`由共同映射持有，Audio不乘第二遍source carrier。

### 源支撑脚、首步与反向

下表直接由上述metadata的stance/swing区间推导。L_/R_是源角色脚侧，不是玩家持刀手，也不把立体声pan称作空间定位。

| 边界phase k/6 | source秒 | 正播跨界后进入支撑 | 反播跨界后进入支撑 |
| --- | --- | --- | --- |
| 0 | 1/3 | L_ | R_ |
| 1/6 | 19/36 ≈ .5277778 | R_ | L_ |
| 2/6 | 13/18 ≈ .7222222 | L_ | R_ |
| 3/6 | 11/12 ≈ .9166667 | R_ | L_ |
| 4/6 | 10/9 ≈ 1.1111111 | L_ | R_ |
| 5/6 | 47/36 ≈ 1.3055556 | R_ | L_ |

source1.5和下一圈1/3是同一接缝。**若09初始映射确认为gait0→phase0，则初次绑定不发声；首次前进跨到1/6进入R_，不是为了轮流而先发L_。** 从0连续反向，第一次到-1/6等价phase5/6，反播进入L_。在每帧只跨一个边界的完整前进圈中，应消费`R,L,R,L,R,L`；完整后退圈为`L,R,L,R,L,R`。任意非零phase启动时直接读实际下一个边界的脚侧，不能重置左右计数。

这是基于源区间的推导，不冒称Root已验收“鞋底落地音”时刻。09需确认起始phase/prefix和边界脚侧沿用该来源；若最终target/01可见落脚审核与区间标注不同，先由01/Root修正并冻结共同profile，不由11偏移事件或猜另一只脚。当前表已能回答源phase0之后的首个前进支撑脚，故无需以没有证据的假设代替01数据。

### 消费、起停、反向与丢帧规则

1. Main现有`audio.present(state, events)`仍为入口。Audio从09同一locomotion快照/合同获取上一点到当前点；只替换`presentSteps`与其敌人脚步游标，不碰CombatImpact、终局末击、雨、玩家挥刀或触觉策略。
2. 连续正向采用`(previous,current]`，连续反向采用`[current,previous)`；端点归属交09共同规则实现。同一快照/同一gait不发声，到接缝只消费一次，直接在精确边界反向不因“初始化反向”重播脚声。
3. 普通停步保留权威signed phase，不强制回到phase0。停步→继续、非零相位反向均沿共同clock，只有真正跨过下一支撑边界才消费；不使用`abs(delta)`消掉行进方向。转入attack/非walk不播脚声，重入walk先确认共同clock是连续还是权威新段。
4. 暂停、追踪/输入或场景丢失、换轮/对手/绑定改变、teleport或权威continuity重置：本帧不播、游标定基到当前。恢复首份快照只建游标，不追补暂停期间或旧绑定跨过的脚声。非法/缺失合同与非有限gait也不发声，不兜底旧常量。
5. 同一present跨多个合法边界时，先把游标推进当前点，再只取**按本次行进方向最后跨过的一个**；其它已过边界当帧丢弃，不能排到下一帧补播。teleport/不连续样本则整段丢弃、零声；保留每present最多一声的约束。现`.75m`大跳保护是旧消费保护，不能当作六步合同或本路新调参；09应确认权威continuity如何覆盖它。
6. 新STEP仍用已冻结WAV、priority1、既有音量与速率范围；脚侧从共同边界结果选，移除`stepIndex++`的人造左右推断。是否沿既有±.07轻微声道偏置也按Root当前实现保留，不能宣称物理HRTF。一次loop既不新增foley也不叠haptic。

### 09字段确认后的专项测试计划

所有场景运行真实消费器＋注入输出记录器，输入通过09真实typed contract与共同resolver构造；不能在测试里复制另一套clock使实现/测试一起错。现有接触/终局/雨/挥刀/优先级测试继续回归；旧`.725`脚步断言明确替换为下面的新源语义。

| 测试 | 必须观察到的结果 |
| --- | --- |
| phase0绑定、prefix→loop、首个前进边界 | 初始化/已有支撑无声；首次合法前进跨1/6为R_，边界前零声、到边界一声 |
| 完整一圈按正常小步采样 | 6声，脚侧R/L/R/L/R/L；source与game nominal时序来自同一resolver，1.45m不再只出2声 |
| 零点向负gait、连续后退一圈 | 正模phase与source一致，首次反向跨-1/6为L_，六声L/R/L/R/L/R |
| 正负跨零、接缝、精确边界、重复同帧 | 每个真实跨界一次；source1.5/下一圈1/3无双播，相同快照/相同gait不重播 |
| 非零phase停止/再走、任意phase反向 | 不从0重起，不猜首脚，直接消费共同clock的实际下一边界；精确边界原地换向不追加初始化声 |
| 方向抖动与float32源边界/Double runtime | 使用09共同端点精度规则，不靠Audio独立epsilon；无仅因表示差异出现的重复声 |
| pause/scene/input loss/resume、换轮/对手/新binding | 恢复只定基；旧批次/旧步声不会补播，后续首次真正跨界脚侧正确 |
| teleport、非有限/缺失合同、权威重置 | 当帧零声且无后续积压，不回退旧`.725`或固定source rate |
| 一帧跨2/多边界、反向多边界 | 合法连续样本最多最新1声；反向选遍历末界，不错取数值最大界；下一静止帧零声 |
| moving IDLE→attack/HIT→guard→walk | 只有共同clock确认walk且移动时才播；不以持续gait或旧游标误发attack脚声 |
| 玩家blade motionGeneration单独改变 | 只重置玩家挥刀，敌人signed gait/下一落脚继续，不能一起清空敌人游标 |
| SoundPool样本未ready/播放失败 | 游标照常前进，后续ready不追补旧落脚；既有短音有界/雨声保留成立 |
| 旧行为回归与身份一致 | 普通接触、fatal、末击、玩家挥刀、雨声、accent行为不变；同合同binding变动重新定基 |

**实施前待09确认（写入其交接或提供实际type文件后再动源码）**：共享type/函数实际路径和字段名；未取模signed cycle与moving/source前缀语义；六界的正反脚侧、起始phase和接缝精度；连续起停/反向与teleport/新段的权威标志；Audio取得同组contract的实际入口。若shared clock已直接产出crossing事件，Audio只消费该结果，不再实现平行边界计算。

### 本次交付与下一步

本次仅变更`docs/agents/11-audio-haptics.md`。未改CombatAudio、tests、WAV、源素材、生成器、review/production manifest、profile、共同clock、Main或任何haptic数值；未运行Gradle、native或旧专项。已做源码/metadata只读核对及文档空白检查，不宣称新六步测试已运行。等待09具体type确认后，在本路授权范围实现最小消费改动并补上述边界回归，再交Root同组构建与真实落脚音画验收。

## stage10六步实施与最小音源交付（2026-11-11，代码完成）

**最新结论：已按Root续派完成实际六步消费与最小源闭环，隔离JVM 61项、资产7项通过，独立四面review通过；本轮没有运行共享Gradle/native/设备/Git。** 前节“仅文档/等type”状态由本节替代，旧`.725m`消费已移除。真实foley、13份正式WAV及全部accent保持逐字节/源码SHA不变。

### 共同clock与实际消费

实际09类型名为`LocomotionProfile`，位于冻结的`runtime/LocomotionProfiles.kt`（SHA-256 `03fe18536ccd66bfa8cb35190616b4a3bada006e47a58693f0590e1b19e6c4a1`），并非另一个需补建的`LocomotionContract`类。Audio通过当前`arenaOpponents[roundNumber-1].locomotionProfile()`读取同组profile，复用其`sourceSeconds(true, signedGait)`、loop/stride及六个`GaitStepEvent`，没有修改09文件、复制clock常量或添加Audio epsilon。

`CombatAudio.presentSteps`只保留上一权威gait与profile身份，移除了`stepDistance`、`stepIndex`和`.725`。只有实际moving IDLE且方向有限非零时播脚声，停止/attack期间也推进游标，不回放被跳过的步界。玩家blade generation仅清理玩家挥刀，不再清掉敌人步态。初绑、暂停/追踪或场景恢复、换轮/角色/profile只重新定基；非有限gait和既有`.75m`大跳保护丢弃当帧全部脚声。这里`.75m`是保留的声音不连续保护，未改游戏移动或碰撞阈值。

同文件的`latestAudioFootfall`是无状态**声音消费计算**，不产生另一个时钟：相位只读09函数，恢复整数周回后，在原signed gait域用`stride*(cycle+step.phase)`精确执行正向`(previous,current]`、反向`[current,previous)`。固定检查当前和相邻周回，处理浮点接缝落在前一圈的情况；只选按本次行进方向最后跨过的一界，最多每present一声，未ready/播放失败也不排队补响。正常stage10 `1.45m`合同全部使用此精确路径；只有极小正stride导致绝对cycle不可表达小数时，才从同一09 wrapped phase选择最新marker，避免除法溢出，未新增调参或epsilon。

已用实际六个prepared marker证明：phase0初绑无声，向前首次进入R_，向后首次进入L_；完整前进圈`R,L,R,L,R,L`，后退圈`L,R,L,R,L,R`。脚侧用于原有pan/rate变体：LEFT仍-.07/.96，RIGHT仍+.07/1.03，音量.16与priority1不变；不宣称HRTF。普通接触、fatal、末击、雨、玩家挥刀与haptic策略没有修改。

### 专项与实修证据

- `python3 ArtSource/audio/run_audio_tests.py --audio-only` → **61/61通过**（56 Audio + 5 Accent）。真实编译Audio、09共享clock、当前profile/状态/Core；Android声卡仍为注入记录器。runner只补真实`LocomotionProfiles.kt`并移除Root已经删除的Desktop旧源列表，没有桩掉clock。
- 新六步边界覆盖正反、负gait、跨零/跨圈、初绑首脚、精确接缝、非零phase起停/反向/attack、玩家generation独立、暂停/scene/input/round/角色切换、瞬移/非有限、多界latest与未ready丢弃。
- 独立review找出的两个真实负周期ULP问题已先红后绿：反向到达`stride*(1/6-1)`不能漏声、正向离开`stride*(1/3-1)`不能重播。用signed marker原域半开比较修复，未加入本地容差。另覆盖正负第7圈接缝、`.1m`完整圈精确端点、`1e-200`与`Double.MIN_VALUE` typed数值域；当前全部通过。
- 红测冻结在 `build/audio-jvm-tests/audio-only/negative-marker-red/`；最终61项报告与全部编译源SHA在 `build/audio-jvm-tests/audio-only/report.json`。本轮交付SHA和冻结项核对在 `build/audio-six-step/delivery.json`。不复用旧35/51/250/257项报告为本轮通过证据。

### 最小源读取与干净交付

Root补充发现原生成器扫描166条OGG并把整包ZIP当本地测试必需；本轮已收口为**实际使用的10个OGG**，共644,879字节。`generate_combat_audio.py`只声明/哈希这些真实输入，`sources/sources.json`只记录相同10个源与4套CC0/许可，`production_manifest.json`恰为10个源SHA＋13个输出SHA。官方包URL/原包SHA仍保留为`upstream_archives`来源记录，不要求ZIP在checkout存在。没有删除工作树中任何旧包或未用文件。

`python3 -m unittest discover -s ArtSource/audio -p test_combat_audio.py -v` → **7/7通过**。新增最小fixture真的调用生产生成器main：仅复制10个OGG、生成比较所需9个旧WAV与必要清单，不带ZIP/其余156媒体，重建13种声音，逐条SHA和正式WAV完全一致。正式WAV没有被重写；最初before冻结清单仍保留11种旧WAV，因此完整交付应带11个before WAV＋baseline.json。

精确最小文件集合在 `build/audio-minimal-sources/stage_paths.txt`（45条：代码/metadata5、源10、许可文本5、before 12、正式WAV13），逐文件SHA和正式WAV before/after一致证据在 `stage_inputs.json`。Root按该集合选择文件，不能把仍在本地的整包缓存作为必需输入。**本路没有执行暂存、删除、提交或推送。**

### 本轮实际改动与身份

- `runtime/CombatAudio.kt`：SHA-256 `247b692eab1d013c78ef3c31816674b6c70f495ecc5654938c86b8607dfa6859`。
- `runtime/CombatAudioTest.kt`：SHA-256 `18ed6bd38e437d80e80725db88f6dad366bb634aa3c8154ff9b1765a430ac710`。
- `ArtSource/audio/run_audio_tests.py`：SHA-256 `7d1a2e72c58edaf639b96a20415f626f4b87241ecc63fc81bc795685f66d7b99`。
- 最小源生成器SHA-256 `2cebee813c4ef02292f1398966eafd70afd040853aa982cfb08f9b3031a32b5d`；最小production manifest SHA-256 `f99ead626117557af260520d8321fe07ae5a9c962ffd11b36aa5f7ab1a3b7191`。其余实际改动为 `test_combat_audio.py`、`sources/sources.json`、音频README与本交接；全SHA索引见delivery.json。

只读冻结核对16项全部相同：09 LocomotionProfiles、CombatFeedbackProfile、原review manifest和正式13WAV。production manifest因Root明确要求最小来源而更新；原review manifest作为首轮冻结证据未追改。未修改ArenaSession、Main、09数据/clock、角色或场景正式资产、SDK/Gradle配置与haptic参数。

**未验证**：真实SoundPool播放时序、normal视距下六个实际鞋底落地与声音同步、PICO SDK渲染/crossfade、Space Pro扬声器和触觉体感。Root统一构建和native/设备取证后才能关闭这些项。本轮不以离线生成或单元通过宣称VR音画已验收。当前代码与最小源已交Root review，后续保持冻结，按实际证据续派。
