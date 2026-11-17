# 原生竞技场验收清单

当前为可运行开发预览，**成品Demo未完成，整体人物、动作和打击品质未通过**。唯一工程是Kotlin + PICO Spatial SDK6.1.9，Space Pro / OS6、Full Stage；打磨现有雨夜庭院和三轮短PVE。

## 当前可追溯检查点

当前源码与实物汇入[草稿PR #13](https://github.com/BrickerP/pico-wuxia-arena/pull/13)，尚未作为成品合入main。当前正式角色bank是c8cd395d、veteran af74e574；仅补正确Tangent，三角色10clip/手轨及全部姿态/误差/锚点保全。80项Blender产线、24项Node与17项profile检查过，新材质原生A/B仍待验。

最近实测APK为`65ac20915a2c1f9186c54801327a65f4c3d273f797411ebffdd286e81a3df359`，125076273B，Runtime源4dacc6a0、旧角色bank7af35f02、8c木构。正式558 JVM全过，19GLB/3profile装包身份匹配，已无身体诊断接线。

[65秒原生实战](../ArtSource/refinement/presentation/native-source-authority-2026-11-17.mp4)、[第二轮失败画面](../ArtSource/refinement/presentation/native-source-authority-held-2026-11-17.png)及[版本/限制](../ArtSource/refinement/presentation/native-source-authority-2026-11-17.json)来自该包：新PID9084真实Start accepted、49实际输入、13接触；第二场indigo45/125、玩家100/100时attack_right源未回守势而锁住。完整胜利未通过。3645原视频帧与归一化PTS完全保留，所有输入在录像内；无音轨，宿主帧数不是PICO GPU帧率。

第一条新trial在录制前已经有accepted Start，不能按“新增Start计数没增加”说应用没开局；其短失败记录保留，不计完整交战。第二条改成新进程、在瞄准前记录开始基线并录制，才取得本次有效实战。鼠标已统一有owner校验的真实HID，进程投递成功不当SDK输入证明。

此前ddacc7a6/7af包曾打过前两敌并显示第三轮Boss，再锁住约16.267秒；那份[旧实物](../ArtSource/refinement/presentation/native-compact-reaction-2026-11-17.json)不当65ac通关证明。c8纯材质资产未用于65ac，不以旧录像冒称新材质通过。历史节点各有独立源码/APK/媒体身份。

## 当前验收矩阵

- [x] 当前原生准备态实际显示完整庭院、角色、第一人称手和刀。
- [x] 同一SDK头手来源进入共享判定；真实Start、挥刀、扣血及接触反馈有同时间窗证据。
- [x] 新头/发/甲袖已在ddac第三轮实际显示，紧凑受击、纸墨HUD和7f同链路已用；c8新材质原生对照仍待验。
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

**P0源交接。** Boss held walk→idle使钢刀从分离变为约0.160mm穿入。accepted source必须同时支配显示与查询，override终止及暂停恢复都要准入。缺motion时推进desired源的候选已退回并返修；最新4dacc6a0已由Root接入，正式558项全过、APK65ac2091构建完成并实际65秒/49输入/13接触，第二场45/125时attack_right@1.048→idle有1.1208m跳接而锁住，未通过。修复在 `ArtSource/refinement/combat-direction/native-steel-release/blade-chain-runtime/native-escape-repair-ddac/`，已在当前工作树接入，尚未发布该修复提交；不以测试代替原生Boss验证。

**身体精度。** 完整38389三角候选不消费正式伤害。两次独立模拟器进程各96条同请求，日志记录结果一致；优化版热身中位14.508ms、P95 42.640ms、最慢109.387ms，仍未准入。冷/暖/GC和不利样本均保留。临时2源码逐字恢复、5诊断源码和bin删除，设备恢复ddac。保守BVH/按需蒙皮又取得独立96条一致结果，但warm16.948/P95 57.102/最慢76.164ms仍未准入；正在按实际线程CPU定位热点，不以低模假碰换速度，详见[01](agents/01-combat.md)。

**角色材质。** Root已通过唯一产线发布c8cd395d/veteran af74e574并生成typed，保全部10clip/手轨，只补五个body primitive，DAO及零权joint警告保留。同输出目录复建被旧诊断目录阻断的问题已按Root意见返修，两次真实raw→recipe3重建同bytes/报告；仍须走唯一产线审批发布和原生A/B，尚无视觉品质通过，详见[03](agents/03-art.md)。

**场景体积。** 新柱和190mm曲木承托 `8c44106f` 过9项保护，尺寸、64原节点和12锚点保留；Root接受局部实体改善，已装入7897b9c4并实际看到原生准备态，图见`presentation/native-entry-2026-11-17.png`；该包Kotlin与ddac相同，只变场景，完整新组合交战/TBN细节及整场品质仍待审，详见[06](agents/06-environment.md)。

## 当前正式资产身份

下表是已发布c8cd正式资源：base/indigo/手刀不变，veteran只补Tangent；场景为已原生显示的8c44106f。旧65ac实战仍用7af/42e，不能算新材质验收；完整新组合待P0修后重验。

| Asset | SHA256 |
| --- | --- |
| base | `5e312d830715575e2d6b74b57320d05c226336082049f6981ba81f78b2704b38` |
| indigo | `09d516f2086df8020121152322f3468c87e3461ed276b0994001a87bdcaf73b6` |
| veteran | `af74e57427aa23bfc2bbd80ee33593799c8f280da0e65232f74db17c6d5dcc7b` |
| dao_grip | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |
| courtyard | `8c44106f40bf1225e82c46b32c439abeeb0e88c67ab5d232f202b26e291ce151` |
| right_hand | `199c228cb4e0bdca0f8236cd225773ecc4560b60b8d2950ca8156e44ec5f0b64` |
| left_hand | `0295c147673a5cf15b4265cbfcb83391d2fa399b8be778c54ecc789fc61c46f7` |

每次采用候选须重新核审批、装包SHA、同包流程和画面，不能只改表格或沿用旧测试数。当前任务与Root修改意见见[01战斗](agents/01-combat.md)、[02输入/手部/UI](agents/02-input.md)、[03角色](agents/03-art.md)、[06场景](agents/06-environment.md)。
