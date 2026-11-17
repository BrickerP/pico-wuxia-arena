# 01 · 动作与战斗交互交付合同

更新：2026-11-17。本文只保留当前生效任务、Root评审和验收要求。正式源码、资产身份、补丁和测量收据以所链接实物为准。

## 正式检查点

- 唯一仓库：`/Users/yupeng/projects/personal/pico-wuxia-arena`。Kotlin + Spatial SDK6.1.9，Space Pro / OS6，Full Stage。
- 开发提交 `37d0ebf4` 已推送，见[草稿PR #13](https://github.com/BrickerP/pico-wuxia-arena/pull/13)。草稿尚未合入main，不能称已完成。
- 正式角色binding `7af35f02`。实战基线ddacc7a6已发布；本地源交接修复4dacc6a0与8c木构的APK65ac2091过558正式测试；实际65秒/49输入/13接触仅打到第二场，indigo45/125时缺回守势而锁住，未通过。当前产线又发布纯T修复c8cd395d/veteran af74e574，基于同10clip，待新包配对；65ac实物仍属旧7af bank。71 Blender产线与42贴图编码结果仍属同一未改角色bank。
- 同包原生输入已实际开始比赛，15次接触，前两敌倒下并进入第三轮Boss。Boss150HP、玩家100HP时出现约16.267秒锁刀；完整胜利和重开未通过。
- 原生画面与55秒实战录像：`ArtSource/refinement/presentation/native-compact-reaction-2026-11-17.*`。该录像无音轨，不证明GPU帧率或音效震动。

## Root评审与P0任务

当前返修目录是`native-steel-release/blade-chain-runtime/native-escape-repair-65ac/`，ddac封件保留。以下相对路径均位于`ArtSource/refinement/combat-direction/`。

Root真实65秒录制已收（app PID9084，Start20:50:17.471 accepted）。最后BLOCK13在20:50:41.137；随后attack_right@1.0481423844624762→idle@1.227366357被准入拒绝，钢端点变化1.120825860m。Root退回“已修好”结论：旧ContactRecovery局部退刀结束后未真正回guard，逻辑却IDLE。当前01须收敛到已有authored SourceReturn，1×走完真实守势才允许恢复/下一招，不能放宽容差或恢复跳刀绕过。原始失败图/片/日志在artifacts/native-source-authority-2026-11-17/real-trial-02/。

Boss冻结源为已持有walk切换idle：同actor/held下idle钢刀间隙约−0.160mm，walk约+0.184mm，而原查询数值包络约0.0023mm。安全释放后直接换动画源会重新穿入；必须修正实际显示与物理所用源的交接，不能放宽碰撞容差或推开玩家手。

- accepted source是当前显示、查询、接触提交的唯一权威；override释放、actor完成/中断、clearMotion、暂停恢复及同clip跳时均须经过同一准入。
- ahead查询沿实际owned source推进，包含真实source key、actor及头部路径。未来恢复域不得按相同秒数合并不同clip。
- USER暂停恢复候选曾在缺motion基线时推进desired source，审核已退回。只可用已确认、完整、有效的真实TrackingSnapshot建立零挥击基线，并验证完整钢刀静态分离；无安全基线时world clock与动作推进分开。
- 原冻结JDI数据、攻击ID/伤害去重、a88/414回收边界必须保留；整数时钟与冻结浮点source的量化差应明确说明，不以放宽runtime身份比较处理。
- 2mm仅是已批准的Steel/Grip微接缝制作预算；身体按真实守势呼吸包络核查。该预算不是碰撞误差容忍，也不代表完整骨架数学相同。
- Root统一审核生产补丁、运行正式测试、构建并用同包原生输入验证。未通过Boss及暂停恢复，不标完成。

## 身体判定：实测结论与下一件

原HEAD/躯干caps漏掉部分肩臂和小腿；粗胶囊及低模候选出现假碰，未获准代替正式判定。SDK专项探针已结束，临时接线全部撤回，不继续扩大诊断。

完整indexed蒙皮候选位于 `native-steel-release/body-contact-fit/skinned-proxy/full-mesh/`：绑定veteran `42e89a29`、38389实际body三角、19183点、8个living clip，shape外扩为0。它目前仍不参与正式伤害。

Root在同一模拟器分别装入baseline `6f57ac4d` 与optimized `804c26f0`，取得独立PID12721/13456的32case×3受控CPU测量。Root重跑 `android-review/compare_android.py`：96条请求及日志记录的status/fraction/zone/triangle等一致；未记录的normal/bary/player Grip不能据此声称已实测相同。

| 热身后64条 | baseline | optimized |
| --- | ---: | ---: |
| 中位耗时 | 104.299ms | 14.508ms |
| P95 / 最慢 | 387.374 / 732.075ms | 42.640 / 109.387ms |
| 分配中位 / 最大 | 1925120 / 12865536B | 98304 / 884736B |
| 过程GC计数 / 时间 | 2 / 498ms | 1 / 163ms |

这些是模拟器进程的CPU测量，分配/GC计数可能含其他线程；保留冷启动和全部不利样本，不算Space Pro预算通过。高层日志曾回放旧运行，已按真实PID、LOAD和装包SHA辨别，失败流保留。原始收据在 `artifacts/native-body-shadow-2026-11-17/`；测后2个源码逐字恢复、5个诊断源码及bin撤回，正式伤害入口没有更换。

`full-mesh/lazy-bone-bvh/`已交保守骨影响bounds和按需精确蒙皮，393个host完整witness逐bit一致。Root另测PID17483/APK4a990246，96条记录结果一致，但warm中位16.948/P95 57.102/最慢76.164ms，并未比pooled版本整体更快；加载约2.038s，heap delta27.75MB，GC0不等于预算通过。初始120秒只观察67条后结束采集，未重启同一benchmark；之后按同PID取完整单次快照。所有临时接线已撤回。

当前身体路续做`lazy-bone-bvh/android-profile-revision/`：按逐case线程CPU及FK/refit/剩余成本定位一个热点再改，保留完整indexed surface和现CCD/sourceE。权重sum不一定等于1，必须显式包住实际sum区间、actor origin及外向舍入；不可加大物理形体或误差预算。缓存精确绑定clip/source bits、actor、geometry/motion，并覆盖异常未完成写入。先交host完整witness逐bit对照与坏例，再由Root测Android同一数据集。冻结baseline/optimized不覆盖。

## 出口验收

先修P0并保持前两轮，再证明三轮胜利、重开、暂停/失追恢复及实际输入不重复伤害；随后专项验证头部闪避、双手技能、处决和音效震动同步。Space Pro性能与舒适度需真机证据，当前未取得。
