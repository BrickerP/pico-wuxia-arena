# 原生竞技场验收清单

当前为可运行的开发预览，**整体人物、动作与打击品质未通过，成品 Demo 未完成**。唯一工程使用 Kotlin + PICO Spatial SDK 6.1.9，目标 Space Pro / OS 6、Full Stage。只打磨既有雨夜庭院、持刀攻防与三轮短 PVE。

## 本轮开发整合：v9动作＋右手v2（原生流程待验）

2026-11-13 新组合APK `d0c76247ce0e6957e721e4840a0ea7a5311fe8ba931cb9b45214d0d09088be95`，242,706,266 B，已构建并安装到同一PICO Emulator 6.1.0。Kotlin源码与349项全过版本逐文件相同；相对已完成managed scene build只换入已源审的右手v2，7个装包GLB均匹配正式资源。上劈v9/120Hz211键、64da庭院、近场光、薄刀轨与终局摆位已进入本包。APK/构建身份见本地 `artifacts/native-visual-v9-grip-v2-2026-11-13/`。

同包原生准备态已显示庭院、首敌和v2左右手；SDK Head/Controller为STARTED/SUPPORTED，真实Shift组合键和鼠标进入SDK_NATIVE共享判定，Start gate随有效头手恢复。完整三轮、v9动作/刀轨、终局面板数值及点击仍待本包实际试玩，不能借下方旧版三轮录像判新包通过。当前还在校准模拟器切左右模式后变化的虚拟手基点。新增Tripo doctor在30秒有界检查内未返回，余额未知，没有新的收费任务。

右手v2已获Root和独立三视图复审；只改Pinky闭握并保留v1拇指收益，新增Ring/Pinky交叉10→0。旧掌背硬脊、腕口硬边及closed极浅样本仍保留，未作最终手部质量通过。运行时仅消费grip0/1，不消费mid；离线固定右手DAO的open/mid旧穿入仍如实保留在源审核。

## 上一已公开、完成三轮的节点

本轮原生UI/命中组合APK：`ca26f4a9837437b05f1d8a3a3b0c0dbb770624656af2eaba148c60dafc605c5c`，242,709,621字节，已公开为[native-ui-impact-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-ui-impact-2026-11-13)，固定源码a22a216。构建与336项单测通过，源在构建/测试/录制期间一致；运行包已无EnemyHitFlash。UI样式0error/0warning，保Full Stage、既有面板尺寸/位置、输入与规则。

[52秒原生连续片](../ArtSource/refinement/presentation/native-ui-impact-three-rounds-2026-11-13.mp4)来自一次65秒PICO Emulator窗口原始录制，未插帧或改速，完整解码通过；[交战状态](../ArtSource/refinement/presentation/native-ui-impact-contact-2026-11-13.png)、[胜利](../ArtSource/refinement/presentation/native-ui-impact-victory-2026-11-13.png)、[版本/验收边界](../ArtSource/refinement/presentation/native-ui-impact-2026-11-13.json)已固定。

当前同包已证明：失败结算→实际UI重新挑战→Start accepted→三轮base/indigo/veteran依次换入→胜利967分、余40HP。日志中的Contact.round表示generation；本次重开后三轮generation=3/4/5，角色加载日志round=1/2/3。SOFT/HARD/GUARDED/PLAYER_HIT与三次fall已消费/播放。原始日志与物理鼠标收据在`artifacts/native-ui-impact-2026-11-13/`，没有注入游戏状态。

通用workflow的源码扫描、Gradle发现、构建、安装启动已通过；旧项目缺其要求的domain/model与ViewModel导致架构阶段失败。当前继续使用既有core/combat与ArenaSession状态拥有者，不伪造clean receipt或为小范围呈现改动重构游戏。样式与完整测试独立完成。PICO renderer性能/Space Pro刷新率不能从主机录制fps推导。

前一公开节点 [native-hands-hit-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-hands-hit-2026-11-13)仍为APK a8907a84、源码27bd559，不能混用本轮新流程证据。更早9e的真实玩家BLOCK仍只属其原节点。

## 已证实与待验

- [x] 原生准备态加载庭院、首名角色、玩家刀和真实第一人称手部。
- [x] 同一 SDK 头手来源进入共享判定；实际鼠标开局、挥刀、扣血与既有软/金属反馈有同时间窗证据。
- [x] 已公开9e包真实玩家 BLOCK、异向受伤、失败后重开并再次开局。
- [x] 普通 HIT 从正式GLB导出真实受击采样；渲染与接触查询共享 clip/source clock，保留接触短停与过渡。新typed数据与三份正式profile完全一致。
- [x] 当前组合336项单元测试通过，0失败/错误/跳过；旧白闪/死入口测试随其机制删除，局部灯happy/boundary已覆盖。
- [ ] 玩家弹反、HMD动作闪避、技能与处决的真实设备输入到反馈闭环。
- [x] 当前包真实三轮角色切换、清场补给、胜利、生命归零与失败后重开。
- [ ] 超时、暂停恢复、追踪中断与原生UI重开确认的实际流程。
- [ ] 原生左右手完整握柄贴合、换手、隐藏恢复、前臂切口与退出重建；当前右手有一指过直且肤色偏亮，未作视觉通过。
- [ ] 原生短时交叉淡入中的模型与判定精度；数据同源不等于每个blend瞬间已测量。
- [ ] 真正接触时的短停、粒子、轨迹、数字、声音与触觉同步；38ms效果不能用稀疏录制认定通过。
- [ ] Space Pro 的帧耗时、纹理/模型内存、切轮峰值、持续运行、发热、舒适度、声音与触觉。

## 正式资产与视觉关卡

| 当前正式运行资产 | SHA-256 |
| --- | --- |
| base | `6ca12659ef6705b2fba43ace092fb8eb567df090c55849b87869e79a9031df24` |
| indigo | `27782bbe11bfff327d4635a1c5276053dda012c12bf2911047fbe880653121df` |
| veteran | `6d4211c8ed07dffb3f683748688120c581e2ee82b12559941b68a6d7170fcee2` |
| dao_grip | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |
| courtyard | `64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605` |
| right_hand | `3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0` |
| left_hand | `cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541` |

三角色的78骨、10clip、KTX2/mips、同源守势/六步行走/三攻击仍保留。本轮v9已通过唯一producer重导，typed/profile/三角色binding为365578…；此前HIT阶段未改运行GLB的事实仅属于旧公开包。离线青衫约18mm、玄甲约14mm足底残余、身体拟合约49mm仍未关闭；不扩大判定体掩盖。`turn`资源尚无实际运行编排，湿布/闪避近地/落地无真实witness，当前已移除无caller入口与无用预载；源资产保留，不按文件存在认定可用。

下一批仅围绕同一战斗画面交付：

1. **人物与手刀：** 修自然握柄、袖肩薄厚、皮肤/衣料分区、近距过亮与黑刀面；服装Cloth首件失败，转真实二维衣片构型，保当前脸手/骨架。
2. **一招动作：** fine-overhead v9已完成三角色正式重导，低头姿态经源审改善；0.50–0.65s快抬头及连续交战仍待本包原生观察，不扩新招。
3. **场景：** 整立面64da已换入唯一courtyard并显示于本包原生准备态；进一步检查动态法线/接缝和Space Pro成本。静态合批候选另由06制作，未合入，不凭静态计数归因LMK。
4. **反馈/UI：** 旧整身白闪已在上一公开包删除；本轮薄刀轨、近场光、终局文本和面板世界锚进入开发包，实际接触/遮挡/点击待验。只消费真实事件，头手保持实时，不用相机抖动补力度。

各方向实物、Root修改意见和当前责任见 [并行制作入口](agents/README.md)。每次收件要求同机位正常视距前后图/短片和可追溯源；尺寸、面数、离线图或测试PASS均不能代替实际品质验收。
