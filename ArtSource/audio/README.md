# 战斗材质音效

`generate_combat_audio.py` 使用Python标准库与固定随机种子制作本项目原创PCM短音效。生产资源统一为48 kHz、单声道、16-bit WAV。11个资源的时长为0.28到0.95秒，最长解码体积91,200字节。

| CombatImpactKind | 生产资源 | 材质层次 |
| --- | --- | --- |
| SOFT_HIT | arena_hit | 布料撕擦瞬态、软组织低频冲击、延迟布尘尾声 |
| HARD_HIT | arena_hard_hit | 硬质短敲击、非整数倍金属共振、明亮短噪声 |
| GUARDED_HIT | arena_guarded_hit | 被衣物包裹的护甲闷击、低频主体、短促低调金属颤音 |
| BLOCK | arena_block | 重格挡低频碰撞、宽频钢铁瞬态、短二次金属振动 |
| PARRY | arena_parry | 高频清脆瞬态、较高音域钢铁余鸣、少量低频重量 |
| PLAYER_HIT | arena_hurt | 较低身体闷击、短促空气与衣物震动 |
| SKILL | arena_skill | 破势双段脆响、金属断裂颗粒、低频冲击 |
| EXECUTION | arena_execution | 较重软目标冲击、延迟刀切与布料摩擦、克制低频尾声 |

现有合同没有GUARD_BREAK枚举，本轮SKILL按破势音色制作。`arena_whoosh`仅配合真实敌人STARTUP阶段切换。`arena_victory`与`arena_defeat`用于实际结算切换。旧`arena_clash`与`arena_dry`已从生产目录移除，低体力／低气势／距离提示由界面承担。

## 生成与试听

从唯一主仓库运行以下命令。

```sh
python3 ArtSource/audio/generate_combat_audio.py
```

[12.06秒前后试听合辑](../refinement/effects/audio/material_contact_comparison.wav)按软目标旧／新、金属旧／新、护甲、格挡、弹反、玩家受击、破势、处决排序，各段之间留有静音。[试听时间表](../refinement/effects/audio/comparison_cues.json)记录每一段的起始时间。[PCM测量结果](../refinement/effects/audio/audio_measurements.json)由写出的16-bit PCM重新读取计算。

`before_soft_hit.wav`和`before_metal.wav`是本轮修改前冻结的两个参考声音，仅供离线对比。

## 呈现接线

主控在同一呈现回调使用 `audio.present(state, events)`，释放时调用 `audio.close()`。`CombatAudio`完整遍历CombatImpact批次，以当前roundGeneration内的ID集合去重，支持首批、切轮首批与同批非顺序ID。切轮清空去重集合并停止旧声音。暂停／追踪失效期间的接触会被消费，恢复后保持当前时刻语义。

强度决定音量，Stage接触点与头部距离提供轻度衰减，hand提供轻微左右声道偏置。SoundPool输出为双声道音量控制，当前未使用SDK空间音频。全批事件均进入消费流程，池上限12路同时发声，超出后由SoundPool按优先级与年龄回收。资源尚在加载的接触先进入小型pending队列，后续present逐项播放已经ready的样本。已报告加载失败或load返回0的样本不会留在队列中等待；暂停、切轮和close清空待播接触，恢复后保持当前时刻语义。

Android35本地官方SoundPool源码说明其短声音预解码上限为每段1MB，并公开load、play、setOnLoadCompleteListener和release。实际声压、头显扬声器音色及命中时序交主控PICO专项验收。本轮完成生产素材、PCM检查和离线试听产物，未启动设备或游戏。
