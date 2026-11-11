# Tripo 角色与动作库

角色库由 `prepare_character_library.py --manifest` 唯一生产。当前生产合同是 schema 3：三名角色各有十段动作，角色、代理 profile 和玩家刀具按同一输入身份生成，由 Root 审阅后整组发布。

角色 ID 为 `base`（试刀客）、`indigo`（青衫护院）和 `veteran`（玄甲守擂）。正式身份以经批准的 manifest、`library/characters.json`、各角色 alignment 和 `production_review_request.json` 为准；私有候选与离线展示不代表设备验收完成。

## 当前正式组

当前正式binding为 `b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f`。`motion_library.json`是唯一正式输入，Root已将三角色、profile、玩家刀及对应typed运行身份成组发布。base选用连续头颈raw `34ce3a60…`，indigo／veteran沿各自既有目标rig。

本地 `7e1368fe…` APK已在模拟器Full Stage显示新base头／眼／颈、canonical idle、玩家刀和场景；约27秒完成场景与人物附着，未报NO_MEMORY。相比前一767bc0af包，仅控制面板pose两行调整，实际图确认完整且不挡脸刀；311项组合测试为该调整前结果，调整后仅重建与原生视觉验。三轮切换、近距材质、实际过渡与Space Pro内存／性能仍未验收。构建和版本证据见[验收清单](../../docs/acceptance.md)，公开GitHub预发行仍是旧包。

## 十段动作合同

| 来源合同 | 输出 clip | 源合同 |
| --- | --- | --- |
| `motion41` | `fall`、`turn`、`hit_body`、`hit_head`、`hit_side` | 原 41 关节动作源 |
| `locomotion78` | `idle`、`walk` | stage10 冻结的未烘焙右指校准源；0–1.5 秒，分别 91／185 keys |
| `attack78` | `attack_overhead`、`attack_left`、`attack_right` | 冻结的三路未烘焙右指校准源；0–1.75 秒，106 keys |

重定向复用世界 rest rotation／position delta，将姿态映射到各自 78 关节目标。每个目标保留自身 rest frame、骨长、几何、skin 权重和 inverse bind matrices；米制归一、身体与骨架使用共同变换，+Y 向上、朝 +Z，目标身高由 manifest 指定。

右手指从各目标 `grip_source` 的原生握姿取样，再对全部十段统一应用一次已审阅的右指偏移。历史原生 slash 仅作握姿来源；运行十段使用上表的显式 clip。步法保留常量通道的 STEP，以及六条腿旋转通道的 LINEAR 语义。

`idle`、`walk` 和三路 attack 共享本目标 canonical idle 源时刻 0 的一次根 Y 平移，将该守势真实 LBS 最低足底定位到 −0.028m。运行实体再加 +0.028m 一次。五段共用这一个基准，足底审计记录 key 与 midpoint 的真实残余；锁链相对差为零不能证明绝对足底或代理已经对齐。

walk 循环源区间为 1/3–1.5 秒，时长 7/6 秒；每 1.45m 推进一周期，共六步／三对，每步距离 1.45/6m。接触相位取冻结 source contract，消费者共用距离驱动的 gait clock。

## 重建与发布

完整字段与输出合同见 [character_library.md](character_library.md)。可执行的 schema 3 输入为 [正式manifest](motion_library.json)，其中冻结角色、动作、握姿、body coverage、两种刀具来源及纹理编码工具身份。正式重建与专项以此为默认来源。所有相对输入路径均从本目录解析。

从仓库根目录使用 Blender 4.5，先生成私有候选：

```bash
"$BLENDER" --background --factory-startup --python-exit-code 1 \
  --python ArtSource/tripo-warrior/prepare_character_library.py -- \
  --manifest ArtSource/tripo-warrior/motion_library.json \
  --candidate-dir ArtSource/tripo-warrior/review/character-library-candidate
```

Root 检查同组模型、profile、纹理保真和 review request 后，批准当前完整 binding，再通过同一入口发布到 `library/` 和应用 assets。只接受完整schema 3；缺少必需字段、来源／工具SHA漂移及旧standalone入口会被拒绝；`prepare_rigged_warrior.py` 仅供唯一 producer 内部复用。

## 运行纹理与代理

`runtime_texture_encoding` 和 `player_weapon_source` 是必需输入。最终 `base.glb`、`indigo.glb`、`veteran.glb` 及玩家 `dao_grip.glb` 全部使用必需的 `KHR_texture_basisu`／KTX2，无 PNG fallback。固定编码为全分辨率 UASTC quality 3、Zstd 18、完整 mip 链；编码器、helper、宿主 Python 3.9.6／Pillow 11.3.0／NumPy 2.0.2 和发行包身份均被锁定。编码保留几何、skin、IBM 和动画语义，不缩小原贴图。

纹理按真实 sampler 分别记录 `wrap_s`／`wrap_t`，仅支持 REPEAT 与 CLAMP_TO_EDGE，明确拒绝 MIRRORED_REPEAT。`SETTINGS.mip_source` 固定 S/T 模式相同时由 KTX CLI 生成 Lanczos4 mip，模式不同时按 `axis_mips` 合同逐级显式生成：float64、先 S 后 T、在线性域递归过滤，保留原始解码 top mip；完整算法参数与版本进入来源身份。

原始来源、`*_body.glb` 和 `*_prepared_png.glb` 中的 PNG 仅用于离线制作与来源审计。运行 profile 在最终 encoded GLB 上求值生成，包含 idle／walk／三路 attack 的真实曲线样本，绑定最终 model SHA 和 profile SHA。头部中心与躯干 XZ 从最终 idle 的真实 LBS 网格测量；body coverage Y 按冻结校准保留原骨锚相对高度，伤害半径与规则保持原合同。

Root已用最终组取得首轮准备态加载与显示证据。动画过渡、足底接触、握持、三轮资源切换和内存预算仍需实际验收。KTX文件大小不能替代GPU字节测量，离线保真与相对锁链证据不替代运行结果。

## 历史来源

`expanded/`、`refined-base60k/` 和 refinement 目录保存 Tripo 原始模型、动作、生成任务及制作来源。旧生成命令、四段／八段整理资产、历史预览和任务回执只作 source provenance，不是当前生产入口或完成声明。当前输入选择由 schema 3 manifest 固定。

`expanded/production_receipt.json`仅作为生成来源回执，不是当前余额或完成声明。账号凭据使用CLI本机配置管理。

刀具来源见 [刀具说明](../dao/README.md)；许可与计费来源见 [ov API 条款](https://developers.tripo3d.ai/en/terms)和 [API 账单](https://developers.tripo3d.ai/en/docs/billing)。
