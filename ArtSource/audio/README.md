# 刀战foley与触觉候选

2026-11-11本路把接触素材从纯正弦/噪声合成改为许可可追溯的foley混音。运行入口仍是Main现有 `audio.present(state, events)`；Main、容器与SDK版本无需新接线。正式声音资源由本路明确负责，角色与场景发布仍归Root。

## 试听与重建

- [19.48秒旧/新接触试听](../refinement/audio/contact_before_after.wav)：普通命中、格挡、弹反、硬材质、护甲、挥刀、处决依次A/B，起始时间见同名JSON。
- [普通/致命/处决速度对照](../refinement/audio/fatal_normal_vs_slow.wav)：致命播放0.90×，保留材质并叠低重音。敌人动画0.35×期间，声音仍走真实时间。
- [9秒雨夜交战混音](../refinement/audio/combat_rain_sequence.wav)：离线编排，供音色与层次review，不作为端内同步证明。

```sh
python3 ArtSource/audio/generate_combat_audio.py
python3 -m unittest discover -s ArtSource/audio -p test_combat_audio.py -v
python3 ArtSource/audio/run_audio_tests.py --audio-only
```

生成器只用标准库混音与现有ffmpeg解码，不新增Gradle或Python依赖。旧版11种PCM冻结在 `ArtSource/refinement/audio/before/`，来源节点 `562449af40ee984ddd8ef61be5c339ac9bea2de5`。当前生产资源、生成器和原始媒体SHA在 `production_manifest.json`。原胜负旋律保留，没有用目标游戏声音。

## 来源与派生

完整来源、作者、逐文件SHA256、原包SHA和许可证据页在 [sources.json](sources/sources.json)。四套均选择CC0，允许派生处理。

生成器以 `SOURCE_FILES` 明确列出下列10个OGG；清单只记录实际读取的源文件，不扫描或依赖下载包里的其它素材。`upstream_archives` 的官方包URL与SHA仅保留来源证据，不要求本地ZIP存在。

| 目录（相对 `sources/`） | 必需文件 |
| --- | --- |
| `kenney-impact-sounds/Audio/` | `impactPunch_heavy_001.ogg`、`impactPlate_medium_001.ogg`、`impactPlate_heavy_000.ogg`、`footstep_concrete_003.ogg` |
| `starninjas-sword/clashes/` | `sword_clash.2.ogg`、`sword_clash.5.ogg` |
| `starninjas-sword/attacks/sword - StarNinjas/` | `sword.4.ogg` |
| `haeldb-cloth/footsteps/` | `step_cloth1.ogg`、`step_cloth2.ogg` |
| `ylmir-rain/` | `1.ogg` |

同时保留 `sources.json`、`licenses/` 的四份许可来源文本及 `kenney-impact-sounds/License.txt`。生产13条WAV依赖这10个OGG与冻结的 `before/arena_victory.wav`、`before/arena_defeat.wav`。运行完整生成器还要 `before/baseline.json` 和7条A/B旧声：`arena_hit`、`arena_block`、`arena_parry`、`arena_hard_hit`、`arena_guarded_hit`、`arena_whoosh`、`arena_execution`。验收另核对冻结基线清单中的全部11条旧WAV，包括不参与重建的 `arena_hurt`、`arena_skill`。

资产专项会在 `build/audio-minimal-sources/` 下仅放10个OGG与完整生成器必需的9条旧WAV，缺省不放ZIP或其它源媒体；清空解码缓存后执行真实 `main()`，核对实际解码源集合、脚本SHA与全部13个WAV的逐字节SHA。测试不改正式音频输出。

| 来源 | 已证明范围 | 使用 |
| --- | --- | --- |
| [StarNinjas – 20 Sword Sound Effects](https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes) | 作者说明两把刀实物录制后用Audacity编辑 | clashes 2/5作刀刃接触，attack 4作挥刀 |
| [HaelDB – Footsteps Leather, Cloth, Armor](https://opengameart.org/content/footsteps-leather-cloth-armor) | 作者评论确认布料/皮革录音，提供CC0选项 | step_cloth1/2作衣料层 |
| [Ylmir – Rain (loopable)](https://opengameart.org/content/rain-loopable) | 窗边麦克风录制再加工 | 8秒雨循环、步声水层 |
| [Kenney – Impact Sounds](https://kenney.nl/assets/impact-sounds) | 官方impact/foley，未说明逐项录制方法 | punch/plate与concrete脚步 |

处理顺序：48kHz单声道解码→去无声前导→轻微速率调整→低切/高切→多个实物声瞬态与延迟余响→0.5ms起始/15ms尾部淡化→去DC→峰值与RMS上限控制→16bit PCM。雨用连续录音的两段8秒等功率拼接，循环边界回到同一录音时刻。普通接触最大峰值−6.38dBFS，雨−12.40dBFS；所有PCM与试听均无削波，最长声音解码768,000字节。

湿石脚步是concrete与实录雨水的合成候选，未取得独立实录湿石素材，不声称它是湿石实录。场景声是单声道雨床和声音层次；左右声道仅作轻微hand偏置，没有HRTF或真实三维声源定位。

## 事件与生命周期

材质kind选择主声；真实appliedDamage仅作有限音量强调；有伤害的HEAD把音调提到1.08×；fatal用0.90×并在原材质上叠0.52相对音量的处决重音，EXECUTION不双叠。各事件ID只在当前roundGeneration内消费一次，首批与乱序ID均能消费。全部暂存最多24个，超过120ms不补播。

短音最多10路，另保留一路雨。声音按优先级主动回收：雨0、脚步/挥刀1、胜负2、材质3、格挡/受伤4、弹反/SKILL5、处决6。这样低优先级声音不会偷掉弹反或致命；雨声也不会被SoundPool无通知回收后永远停播。

玩家挥刀使用真实刀尖速度：先观察低于0.70m/s或rest，再跨1.45m/s触发，最短180ms间隔；暂停、切轮或motionGeneration改变后须重新观察低速。敌人起手沿既有STARTUP入口。敌人步声使用现有累计步距，瞬移不补播步声。雨只在FIGHTING、场景/输入可用时播放，接触后180ms从0.10降至0.045，恢复后回到0.10。

暂停、场景丢失、重开与close停止并清空；终局DEFEAT与USER暂停同批时保留末击，但不继续雨/脚步/挥刀。SKILL是实际SKILL事件，不能等同于没有CombatImpact枚举的GUARD_BREAK。

## 触觉交接

仅调整 `CombatFeedbackProfile.accent` 数值，hitStop、死亡时钟、视觉和局部光完全保持。下表level为strength=1时的基准，HEAD在有真实伤害时强调，fatal固定level245/72ms。实际SDK调用与同帧触觉优先级由Root接线。

| 接触 | level | frequency | duration ms |
| --- | ---: | ---: | ---: |
| SOFT_HIT | 160 | 100 | 26 |
| HARD_HIT | 205 | 240 | 12 |
| GUARDED_HIT | 165 | 165 | 20 |
| BLOCK | 190 | 150 | 28 |
| PARRY | 245 | 300 | 14 |
| PLAYER_HIT | 185 | 85 | 40 |
| SKILL | 210 | 140 | 42 |
| EXECUTION | 240 | 75 | 58 |

## 验证边界

专项使用注入的输出记录器运行真实CombatAudio与CombatFeedbackProfile，不调用Android声卡或PICO触觉。资源检查读取最终PCM、许可清单与SHA。`run_audio_tests.py`默认还运行共享CombatFeedbackTimingTest，并保留独立结果；`--audio-only`将本路证据另存到 `build/audio-jvm-tests/audio-only/`，不会覆盖共享回归失败记录。

完整最新结果与Root待办见 [11-audio-haptics.md](../../docs/agents/11-audio-haptics.md)。整包构建、设备播放同步、实际声压、Space Pro频率/力度与长时间舒适度均未由本路验证。
