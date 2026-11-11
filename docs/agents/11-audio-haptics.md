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
