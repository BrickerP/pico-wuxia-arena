# 有限actor卸力：真实未来恢复域修正

**当前48项专项通过，等待Root正式构建与原生审图。** 认证输入仅覆盖实际会播放的恢复段，不再纳入已结束的预备动作；安全半空间、有限端点、CCD、回撤和转向速度均保持。

```bash
python3 ArtSource/refinement/combat-direction/native-steel-release/actor-withdrawal/run_session.py --output-dir future-domain-result
```

## 本次修正

`ArenaSession.steelRecoverySamples(current)`从 `max(profile.first, recovery.sourceSeconds−0.06)` 到 `profile.last`选取未来keys，并显式插入精确插值的retreat、end及当前TOI见证。相同时点以当前见证为先。这样首18%反向0.06和随后的回guard都受认证；无contactRecovery时仍保留完整idle loop与当前见证。

精确retreat有时需要读取边界左侧key作插值，因此测试保留这一个数学支撑点，只扰动它以前真正未访问的windup。改变这些旧windup不影响selected samples或计划。真正retreat/end变化则必须改变认证或返回无可证解；测试把两边界分别放到旧计划末位姿的玩家刀上，确认旧计划确实负gap，且不能复用旧证书。另覆盖合法非key end与当前非key／相同时点见证。

## 实际结果

同一当前base runtime profile的配对结果：

| 项目 | 原全clip输入 | 本次真实未来域 |
| --- | ---: | ---: |
| 认证样本 | 212 | 120 |
| 反例source域 | 0..1.75 | .7733333333..1.75，含当前.8333333333 |
| 计划转角 | −61.93100461° | −61.93100461° |
| actor时长 | 1.227053786s | 1.227053786s |
| 回撤 | 49.5mm | 49.5mm |

**该固定反例没有可测的降角或缩时收益。** 约束主导仍在真实未来段；未调角度／回撤参数去追求变小。旧90点实际FK私有benchmark的−62.765°／1.2416s是不同数据集，不能拿两者差异冒充本次修复收益。

当前实际协调器反例source约1310ms恢复、1990ms回guard，玩家raw／held位移0。原命中停顿、全部10ms刀面gap／body速度、同ID不补伤、真新Swing／新enemy attack、暂停／失追／过期／击杀、原parry停顿与新命中中断旧恢复等回归继续通过。48项无Ignore，原文、编译输入SHA和命令见`future-domain-result/run.txt`及`report.json`。

## 证据与边界

旧44项结果、旧handoff／README和五份实际app／test源码已经冻结在 `archive/full-clip-44/`，`archive_identity.json`记录其身份；该批SHA只证明旧版。当前receipt为 `future-domain-result/receipt.json`，当前唯一交接为 `handoff.json`。

本次只改ArenaSession的认证域与专属测试／runner，不改actor solver的安全域、速度曲线、HomeStage、EnemyAnimator、数据、SDK或设备。仍沿现有actor根位姿共享query与render：玩家手不承担敌方整条恢复弧，没有骨骼写入或视觉单独位移。

48项是隔离JVM协调器证据，不是PICO画面、帧率、最终蒙皮或动态审美通过。约62°转身／约2秒总节奏仍待Root实看；BLOCK不自动等于玩家弹反。无可证路径／CCD不确定时保持最后安全姿，不强行解锁。正式构建、安装、原生取图与合入由Root负责。
