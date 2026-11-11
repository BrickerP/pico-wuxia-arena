# 09 · 正式动作bank与战斗表现接线

## 当前状态

首轮执行待会话接手。2026-11-11用户要求扩大并行，整体品质需明显提升。

## 目标

把新站姿、正劈、左右斩接到真实正常循环，攻击方向、动画、代理、刀路、接触时刻与受击反应一致。参考《荣耀战魂》《只狼》《影之刃零》的来刀辨识、支撑、卸力与收势，沿已有能力完善。

## 所有权

负责 content/EnemyAnimator.kt、runtime/ArenaOpponents.kt、新AttackBankProfiles数据与加载／生成接口、ArenaSession.kt中既有方向调度与接触pose选择、EnemyCombatStateMachine.kt中反击方向参数转发及专项测试。本文件为交接。Root保留其它战斗数值／核心判定，08可能需要emitImpact转发补丁，交Root统一应用。

01是动作作者，Root内部character_grip_polish负责Python producer、manifest及正式发布。你不改这些制作源或GLB，不写Main/HomeStage。

## 当前输入

stage5/candidate/attack_bank_inputs.json三raw已冻结，正劈377bcfc1197d1ae84d2c1784dc1de4004b68d09189528025786578c0b95987b9。三方向最终候选位于 ArtSource/tripo-warrior/review/attack-bank-candidate，已有各角色10clip与attack_profiles.json。Root刚增加实际足底的攻击整体根平移校准，正式approval尚未完成，读取最新候选SHA。

来刀侧为玩家视角，LEFT对应attack_left／slash_to_left，RIGHT对应attack_right／slash_to_right。prepared +X为演员左。三源phase标记0／.65／.90／1.10／1.75，接触1.00秒=ACTIVE中点100ms。横斩游戏阶段550／180／200／600ms，正劈650／250／200／650ms。

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

### 2026-11-11 · 首轮三方向接线候选（专项验证进行中）

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

