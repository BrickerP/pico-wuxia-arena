# Weighted overhead v3：逐方向 phase 开发候选

本目录是 Root 已审核设计的候选输入，不是正式模型发布或原生验收。唯一生产路径仍为 `prepare_character_library.py`；Root 独占实际 target 模型生成、正式 manifest／library、typed 数据、组合构建、设备与 Git。本路没有运行 target 模型生成。

源阶段继续使用 RAW `85d633ec61534c62f59269c1d9f02854e829d1b84db33a91e3a3afac2e779076`、authoring `6056fddca9407c882fba1a12e2d67b4a0ce4983c7d5511bc00ecca9a0fc07380`。仅 OVERHEAD 的完整 RAW 换新；LEFT／RIGHT 原始 GLB、idle／walk、reaction／turn／fall、三个 target 的模型／grip／指校正／纹理、武器与 coverage 配置保持原样。私有 preview 不能当 RAW，也不把新源作为旧 prepared 模型的局部差分。

## 唯一逐方向契约

`attack_source` 不再有顶层共享 `phase_markers`。每个 `clips[]` 独立持有原六键 `phase_markers` 及四整数 `runtime_phase_nanos`，后者顺序为 PREPARING／STARTUP／ACTIVE／RECOVERING。三方向 authoring 清单保留完整 RAW 与时间网格证据，并与本方向两组字段逐值绑定；旧 `ACTIVE_phase_elapsed_ms=100` 元数据已删除。

| direction | source start／preparation_end／startup_end／active_end／recovery_end | contact 制作 cue | runtime 纳秒，按四阶段顺序 |
| --- | --- | --- | --- |
| OVERHEAD | `0, .65, 5/6, 31/30, 1.75` | `1.0` | `650000000, 183333333, 200000000, 716666667` |
| LEFT | `0, .65, .9, 1.1, 1.75` | `1.0` | `550000000, 180000000, 200000000, 600000000` |
| RIGHT | `0, .65, .9, 1.1, 1.75` | `1.0` | `550000000, 180000000, 200000000, 600000000` |

OVERHEAD 的游戏总时长仍为 1.75s，source 到游戏时间接近 1:1，整数纳秒舍入界由专项验证；左右游戏时长与原值不变。所有 phase 内只按起止线性映射，contact 是制作 cue，不能把 ACTIVE 播放时钟折成前后两半。

producer 与 profile 导出的旧 Python `ATTACK_PHASES` 已删除；typed generator 按审核 binding 中对应 direction 的源身份、phase 和 runtime 核验，且直接读取实际 Kotlin `AttackDirection` enum 交叉核四个时长，不用另一张抄写表替代真实 enum。typed `AttackProfile` 仅保留运行实际需要的 source phase／cue／samples，不额外存一套不用的 runtime 副本。旧顶层共同 phase 不再兼容。

旧 `recoveryFromContact`／`enemyRecoveryFromContact` 贯穿参数、状态与 HUD 路径删除。实际 TOI 的 `ContactRecovery` 独占接触恢复；cue 改变不能改变 ACTIVE 映射或实际接触恢复，更不能在 geometry 重建后跳到固定 cue。持续钢非穿透、TOI 统一姿态、全局规则时间与敌物理运动时间分离的既有严格契约仍保留。

## 文件与实际校验

- `motion_library.json`：可直接交唯一 producer 的新候选 manifest；旧 `production_review` 已删除。
- `attack_bank_inputs.json`：完整三方向 authoring；OVERHEAD 仍为 78 joints／234 tracks／211 keys／120Hz／0..1.75s，LEFT／RIGHT 各 106 keys／60Hz。
- `input_contract.json`：冻结 baseline、源与 producer 身份，限定本轮字段差异；上游变化必须重新核事实，不能自动沿用旧批准。
- `validate_candidate.py`／`validation_report.json`：实际导入唯一现行 producer，执行 manifest／authoring／真实 RAW／canonical family／实际 enum 等校验。最终数量与结果以 report 为准。

本轮触及清单（路径均相对仓库根目录；不含正式资产或生成 typed）：

| 目录 | 文件 |
| --- | --- |
| `ArtSource/tripo-warrior/` | `prepare_character_library.py`、`production_contract.py`、`attack_grounding.py`（仅政策常量提取）、`attack_profiles.py`、`test_attack_bank_pipeline.py`、`test_attack_profiles.py` |
| `ArtSource/refinement/combat-direction/` | `generate_attack_bank_profiles.py`、`test_generate_attack_bank_profiles.py` |
| `app/src/main/java/com/example/wuxiaarena/core/combat/` | `EnemyCombatStateMachine.kt` |
| `app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/` | `AttackBankProfiles.kt`、`ArenaOpponents.kt`、`ArenaSession.kt`、`HudStateProjection.kt` |
| `app/src/test/java/com/example/wuxiaarena/core/combat/` | `EnemyCombatStateMachineTest.kt` |
| `app/src/test/java/com/example/wuxiaarena/p0d2f0182/runtime/` | `AttackBankProfilesTest.kt`、`EnemyPoseSelectionTest.kt`、`ArenaAttackDirectionTest.kt`、`NativeBladeInteractionTest.kt`、`HudStateProjectionTest.kt`、`ContactTimeWitnessTest.kt`、新增 `AttackPhaseClockTest.kt` |
| 本 `integration/` | `motion_library.json`、`attack_bank_inputs.json`、`input_contract.json`、`validate_candidate.py`、`validation_report.json`、`README.md` |

校验覆盖完整时间网格、左右未授权资产字段不变、真实 RAW 字节与 SHA 篡改、descriptor 与 rehashed authoring 已烘焙指校正、真实临时 RAW 烘入一次右拇指校正、private preview 冒充 RAW、错 key grid、旧 shared phase、方向 phase／runtime 与 authoring 漂移，以及无 Root review 的正式发布拒绝。暂存负例 GLB／JSON 在本目录下建立并清理；没有 mock、放松校验、target retargeting、KTX 编码或正式写入。

逐方向时标首轮回归为 producer／profile 32 项、typed generator 24 项、本目录真实源契约 16 项，结果仅属于对应旧代码／输入。本次当前 manifest 绑定闸门修复已执行 producer／profile **35 项**及 typed generator **41 项**，共 **76 项全通过**；覆盖只改 RAW 路径或 SHA、target、texture 而保留旧 bank／receipt 的拒绝，以及真正无 Blender 包的独立 Python 导入。旧 `5d44…` 候选全部 23 文件及绑定 SHA 实际复核未变。Root 正切换新的动作源，本目录16项须在同步新 raw／source_authoring／baseline pins 后重新执行；pending 报告保留上次完成收据，不能据更新代码 pin 直接声称新源通过。

既有 Kotlin 197 项隔离执行中195项通过，仅两项阻止旧 typed 数据混入新时标：`AttackBankProfilesTest.allActorsUsePlayerViewDirectionClipsAndCompleteSourceSamples` 与 `everyActorDirectionMapsItsLinearPhaseBoundariesWithoutBendingAtTheCue` 仍读到旧 OVERHEAD `.9／1.1`，要求的新值为 `5/6／31/30`。它们没有改成自比或加旧数据回退。

其余严格回归覆盖 OVERHEAD 全程近 1:1 的 ≤1ns 误差、左右原值、cue 不改变任一 phase／实际 ContactRecovery、geometry 重建无旧 cue 跳转、持续压力 1 秒不穿且世界 readiness 继续、真实 TOI／guard 证据与同刻手刀头、卸力后同 clip 连续恢复、batch 时钟及原死亡／暂停反馈。恢复测试先沿真实接触法向回撤让出空间，再保留 `source < actualTOI` 断言；持续压住应停的独立非穿透测试完整保留。完整新资产组合仍由 Root 在正式重生后验证。

从仓库根运行有限校验，经现有锁串行使用 Blender，仅取得 `mathutils`：

```sh
python3 ArtSource/refinement/hand-poses/run_blender.py --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/combat-direction/native-weighted-overhead/integration/validate_candidate.py
```

`source` 按 producer 自身 `HERE=ArtSource/tripo-warrior` 解析，不按此 manifest 父目录解析。Root 如开始生成私有候选，使用现有入口；本路不执行下列命令：

```sh
python3 ArtSource/refinement/hand-poses/run_blender.py --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/tripo-warrior/prepare_character_library.py -- --manifest ArtSource/refinement/combat-direction/native-weighted-overhead/integration/motion_library.json --candidate-dir ArtSource/refinement/combat-direction/native-weighted-overhead/integration/candidate-library
```

Root 用新 candidate 生成 profiles 和 typed 正式数据后，须再跑完整组合；当前正式 manifest／GLB／旧 typed 未由本路改写，不能以旧正式数据验证本轮最终 source phase。现有正式入口应拒绝没有新 `production_review` 的发布；Root 检查真实 prepared 输出后，按新 request／binding／hand tracks／profiles 重新给出批准，不复制旧 v9 approved 文件。

typed generator 对最终 resolve 后落入 `app/` 的任何写入（默认或显式路径）都执行正式批准校验：bank request 必须为 `approved_for_development_integration`，当前 manifest 的完整 `production_binding` 必须逐值及 canonical SHA 与该 bank 一致，manifest 引用的 Root review 文件 SHA、approved decision、binding、角色输出和 player weapon 也须全部匹配。只改当前 RAW、target 或 texture 而沿用旧 receipt／bank 会在生成前拒绝；默认 formal manifest 可通过 `--manifest` 明确指定，receipt 仍按 producer 目录解析。私有显式 `--output` 可以分析 pending bank，`--check` 只读但照常校验 bank 数据。路径规则仍以实际 resolved 写入目标判断，不加入旧路径回退。

`production_contract.py` 是无 `bpy`／`mathutils` 的共享纯模块，集中现有生产绑定投影、canonical hash、HAND_POLICY／LEFT_HAND_POSES 与 GROUNDING_POLICY；producer、grounding 与 typed generator 引用同一份政策，避免独立抄写字段表。提取保留已生成 `5d44…` 候选的完整绑定值和 SHA；该候选仍未自动获得批准。`input_contract.json` 的共享模块代码 pin 也进入实际输入校验及报告。当前源选择由 Root 管理，切换 RAW 后应同步 raw／source_authoring pins 并重新执行本目录校验，不能把上一次16项收据换新 SHA 后冒充本次通过。

Root 审核并经唯一 producer 正式发布之后，再执行：

```sh
python3 ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py --bank ArtSource/tripo-warrior/library
python3 ArtSource/refinement/combat-direction/generate_attack_bank_profiles.py --bank ArtSource/tripo-warrior/library --check
```

生成后，按 Root 真正批准的新 binding／model／profile 身份更新 `AttackBankProfilesTest.generatedDataMatchesThePublishedCanonicalBankIdentity` 的旧硬 pin，再执行完整组合构建。不得把硬 pin 改成自比，也不得为让旧数据通过而补旧 shared-phase 回退。当前旧 typed 的 OVERHEAD `.9／1.1` 与新 `5/6／31/30` 不符，专门的 generated-data phase 回归应保持失败直到真实重生。

## 仍属开发候选的窗口与验收边界

本轮 Root 确定了上述逐方向开发窗口，并未把五个离散近刃参考点升级成连续锐刃证明。v3历史 handoff 在 source `.8333／.9／.9667／1.0／1.0333` 的有限参考诊断支持主斩刃侧领先；source `1.1s` 的 edge cosine `-.187187`、absolute face cosine `.979395`、速度约 `1.37m/s` 表明已进入面领先的减速随势。参考点与构造平面不是实际刃口三角面／接触法线。

连续钢／头身 CCD 决定实际接触与最早 TOI；敌刀对玩家的身体候选仍由 ACTIVE 许可。制作 cue 不定时扣血，也不扭曲播放时钟。开发 ACTIVE 已止于 `31/30`，不能再拿旧 `.9–1.1` 整段作为新动作切割许可。

源契约及单元验证不证明三 target prepared 结果、握持一次校正、grounding、最终纹理／profile／typed 身份或真实刀面贴合已经完成。Root 仍须以新 APK 的 PICO Emulator 真实 SDK 输入检查双刀持续接触、卸力、真实身体命中、HMD 避开与 raw／final 姿态；Space Pro 声音／触觉、延迟、性能和舒适度需对应设备证据。
