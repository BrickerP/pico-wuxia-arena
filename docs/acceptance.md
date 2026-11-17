# 原生竞技场验收清单

当前为可运行开发预览，**成品Demo未完成，整体人物、动作和打击品质未通过**。唯一工程是Kotlin + PICO Spatial SDK6.1.9，Space Pro / OS6、Full Stage；打磨现有雨夜庭院和三轮短PVE。

## 当前可追溯检查点

开发提交 `37d0ebf4b9997d64de90bbe4c0a331981e375f5f` 已推送至[草稿PR #13](https://github.com/BrickerP/pico-wuxia-arena/pull/13)，尚未合入main。正式binding `7af35f02b8092c0b541d75b263f333f41d8a43689b8a931bb5fc33e48e0569c6`。

APK SHA256 `ddacc7a60d23f96a1f85338bf85a33bc80bd0dc0ec213777111e9d15aa532b02`，124839117B；19个装包GLB与3份profile同正式文件一致。544 JVM、71 Blender产线和42真实贴图编码检查通过，不代表终端体验通过。

[55秒原生实战](../ArtSource/refinement/presentation/native-compact-reaction-2026-11-17.mp4)、[第三轮画面](../ArtSource/refinement/presentation/native-compact-reaction-boss-2026-11-17.png)和[版本及限制](../ArtSource/refinement/presentation/native-compact-reaction-2026-11-17.json)来自同包。真实Start accepted、15次接触、前两敌倒下并进入Boss；随后约16.267秒锁刀，完整胜利未通过。无accepted Start的首条输入录像不算交战。宿主录像无声音，3102帧不是PICO GPU帧率；原日志一处时间回退保留。

main素材提交9cf3f35及旧release各有独立身份，旧包通关不代表当前组合通关。历史证据留在原release和presentation版本收据，不与当前勾选混用。

## 当前验收矩阵

- [x] 当前原生准备态实际显示完整庭院、角色、第一人称手和刀。
- [x] 同一SDK头手来源进入共享判定；真实Start、挥刀、扣血及接触反馈有同时间窗证据。
- [x] 新头/发/甲袖、紧凑受击、纸墨HUD和7f配光进入上述同包。
- [x] 正式profile、typed生成与装包资产身份一致。
- [x] 原生开发未改独立Web原型，同仓保留两线。
- [ ] Boss拼刀后无长锁死；显示、查询、actor卸力与动作源交接连续，不靠推手或扩大容差。
- [ ] 当前组合三轮胜利、换轮补给、生命归零、超时、失败/胜利重开及确认框。
- [ ] USER暂停、失追/过期/epoch变化、确认恢复及隐藏/退出重建；不补演失去的时间、不重放攻击ID。
- [ ] 玩家精确弹反、防御、HMD动作闪避、双手技能与处决的真实输入到反馈闭环。
- [ ] Left装备/显示、左右切换、自然闭握/放松及腕口/指间/握柄精度；镜像或打包不算全姿态通过。
- [ ] 全身实际表面命中范围及可接受成本；当前正式伤害仍用HEAD/torso方案。
- [ ] 受击/攻击/切换关键段的全身、衣料、护甲和两刀交互；有限采样或同源数据不能证明所有时刻及SDK混合精度。
- [ ] 真实接触短停、轨迹、火花/水滴、数字、近场光、声音与触觉同步；头手实时，不靠相机震动补力度。
- [ ] HUD四页帮助、最长反馈/蓄势、暂停与结算、较大字号、字体回退、遮挡/裁切及可读性。
- [ ] 人脸皮肤、衣料/护甲、自然动作、刀具、木石场景及夜间光影达到一致的中式写实品质。
- [ ] Space Pro帧耗时、纹理/模型内存、切轮峰值、持续运行、发热、声音触觉与舒适度。
- [ ] 最终比赛包、复建说明、素材来源/许可及参赛所需材料齐全。

## 当前修复与候选准入

**P0源交接。** Boss held walk→idle使钢刀从分离变为约0.160mm穿入。accepted source必须同时支配显示与查询，override终止及暂停恢复都要准入。缺motion时推进desired源的候选已退回；修复在 `ArtSource/refinement/combat-direction/native-steel-release/blade-chain-runtime/native-escape-repair-ddac/`，尚未合入，不以私有测试代替原生Boss验证。

**身体精度。** 完整38389三角候选不消费正式伤害。两次独立模拟器进程各96条同请求，日志记录结果一致；优化版热身中位14.508ms、P95 42.640ms、最慢109.387ms，仍未准入。冷/暖/GC和不利样本均保留。临时2源码逐字恢复、5诊断源码和bin删除，设备恢复ddac。下一件保留完整surface做保守BVH/按需蒙皮，不以低模假碰换速度，详见[01](agents/01-combat.md)。

**角色材质。** 当前Mikk切线候选保10clip，只补五个body primitive，DAO及零权joint警告保留。Root要求修正同输出目录复建被旧诊断目录阻断的问题，再走唯一产线审批发布和原生A/B；尚无视觉品质通过，详见[03](agents/03-art.md)。

**场景体积。** 新柱和190mm曲木承托 `8c44106f` 过9项保护，尺寸、64原节点和12锚点保留；Root接受局部实体改善，尚未装入当前ddac包。原生KTX/TBN和整场效果仍待审，详见[06](agents/06-environment.md)。

## 当前正式资产身份

下表按当前实际文件计算，对应ddac检查点；不含尚未采用的切线/木构候选。

| Asset | SHA256 |
| --- | --- |
| base | `5e312d830715575e2d6b74b57320d05c226336082049f6981ba81f78b2704b38` |
| indigo | `09d516f2086df8020121152322f3468c87e3461ed276b0994001a87bdcaf73b6` |
| veteran | `42e89a297ba523ce0bf8943bcdfe0ebc6699ea9e52526c34d3638980f69e6c5d` |
| dao_grip | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |
| courtyard | `c7f2e2b2833cdd84fbc73918fdcd2f9036dee582a46c29d8db67df806e77fc78` |
| right_hand | `199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64` |
| left_hand | `0295c147673a5cf15b4265cbfcb83391d2fa399b8be778c54ecc789fc61c46f7` |

每次采用候选须重新核审批、装包SHA、同包流程和画面，不能只改表格或沿用旧测试数。当前任务与Root修改意见见[01战斗](agents/01-combat.md)、[02输入/手部/UI](agents/02-input.md)、[03角色](agents/03-art.md)、[06场景](agents/06-environment.md)。
