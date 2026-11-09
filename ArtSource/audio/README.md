# 战斗音效来源与接线

本目录的 `generate_combat_audio.py` 仅使用Python标准库，以固定随机种子生成本项目原始短音效。当前生成9个单声道、16-bit PCM、22050Hz的WAV，位于 `app/src/main/res/raw/arena_*.wav`。

| 资源 | 用途 |
| --- | --- |
| arena_hit | 命中、头部命中 |
| arena_clash | 架刀、护身命中、弹反 |
| arena_whoosh | 闪避与敌人起手刀风 |
| arena_hurt | 玩家受伤、破防 |
| arena_skill | 破势 |
| arena_execution | 处决分支 |
| arena_victory、arena_defeat | 结算提示 |
| arena_dry | 体力、气势或距离条件提示 |

从仓库根目录重新生成生产资源。

```bash
python3 ArtSource/audio/generate_combat_audio.py
```

`runtime/CombatAudio.kt` 使用Android SoundPool，以roundGeneration与feedbackSequence消费事件。晚注册、资源尚未完成加载和暂停时的旧反馈不会在恢复后补播，关闭时释放资源。`Main.kt`在同一呈现出口连接声音和PICO手柄触觉调用，最佳分数也在该入口持久化。

本轮只生成资源和实现接线，按用户要求没有试听、自测或设备反馈验收。实际音量、音色、时序与触觉强度在后续Space Pro验收中校准。
