# 11 · 打击声音、场景声与触觉数值

## 当前状态

首轮执行待会话接手。2026-11-11用户要求扩大并行，整体品质需明显提升。

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

由负责会话填写真实产物与review问题。

