# 原生竞技场验收清单

当前为可运行的开发预览，**整体人物、动作与打击品质未通过，成品 Demo 未完成**。唯一工程使用 Kotlin + PICO Spatial SDK 6.1.9，目标 Space Pro / OS 6、Full Stage。只打磨既有雨夜庭院、持刀攻防与三轮短 PVE。

## 当前开发整合：真实刀刀接触＋入口构造

2026-11-13，用户确认本轮反手、挥刀卡顿和拼刀无交互发生在PICO Emulator原生版。当前源码已移除按ACTIVE中点自动裁决的防御，双方刀与身体比较最早连续接触；钢先接触才可招架，玩家手与刀消费同一约束后Grip，敌人使用同一实际clip/source卸力。持续顶刀只停止物理运动，规则时钟与攻击就绪继续推进。胶囊代理与离散动作数据仍有误差，不宣称真实三角面接触或完整物理模拟。

最终Gradle构建及417项单元测试通过，0失败/错误/跳过。独立整合复核发现并修正了HUD随纯手刀姿态重绘的问题；回归先在旧实现失败，再在修复后通过。接线与验收契约见[09交接](agents/09-combat-direction.md)。新增日志读取实际实体根变换，并明确没有读出骨骼/蒙皮刀面，不能将推导值冒充实测。

庭院中央门组、门框止口、门槛、柱础已以96c554候选替换正式开发资源，保留32材质/50图和原场地坐标；展开三角面243358，较原场景增加7612。最终开发APK `d1b61cb3b9e9643b921cf3262b95a94ce17766f0d19743d239c5559f7e090898`（218586373 B）已安装启动，首名对手和新庭院已在[实际Full Stage画面](../ArtSource/refinement/presentation/native-blade-contact-stage-2026-11-13.png)显示；[版本与边界](../ArtSource/refinement/presentation/native-blade-contact-stage-2026-11-13.json)固定源码、7个主要GLB及其余模型、截图身份。普通capture是本机空间截图flag失败后的替代路径。进程9861运行，但本次启动的虚拟手柄callback仍为0。**本轮真实顶刀、回撤、弹反、反手修正和挥刀流畅度均未通过画面验收。** 旧v9的三轮录像不能用于证明新接触实现。

Boss外贴平甲候选因观感变平、guard/举臂存在339/443三角交叉对而退回，没有进入正式角色。03仅继续原Tripo曲面肩甲/护臂局部；02核真实左右手蒙皮与腕指轴，禁止猜测旋转或镜像。01全身上劈v3仅通过源阶段review，正式动作仍为v9，待Root重新生成匹配代理后接入。

## 上一公开完整三轮节点：v9动作＋右手v2

2026-11-13已公开为[native-visual-v9-2026-11-13](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-visual-v9-2026-11-13)，固定源码`bfaf53bf0166999ae33ca7b94597aa69f2fae064`。APK `1c41cfc30fa79dd391e9c6af329cdfcf8b8d6ad7401465b9f16b90d0016d7b46`，242,706,266 B；8附件大小、SHA及uploaded状态均已核对。最终构建与349单测全过，源码在构建/测试/原生录制期间一致，7个装包GLB与正式资源匹配。

本包进入精细上劈v9／211键120Hz、三角色binding365578…、64da庭院、近场光、薄刀轨和终局UI／世界锚，以及右手闭握v2。PICO Emulator6.1.0的真实鼠标／Shift组合键经SDK_NATIVE头手观察进入共用判定，实际完成Start→三名敌人→VICTORY，895分／余60生命，再点击再挑战返回READY。HMD为(0,1.65,0)、左手约(-.20,1.35,-.35)、右手约(.27,1.40,-.45)，均来自实际SDK观察，没有注入应用状态。

[约52秒连续原生片](../ArtSource/refinement/presentation/native-visual-v9-three-rounds-2026-11-13.mp4)、[独立重试短片](../ArtSource/refinement/presentation/native-visual-v9-retry-2026-11-13.mp4)、[胜利](../ArtSource/refinement/presentation/native-visual-v9-victory-2026-11-13.png)、[版本与边界](../ArtSource/refinement/presentation/native-visual-v9-2026-11-13.json)。两段均为系统录制真实Emulator窗口，不改速、不插帧，完整解码通过；主片来自67.963333s原始录制的前约52s，主机约56.5fps不是设备渲染性能。本次未录声音。最终日志含8次SOFT_HIT、6次敌方GUARDED_HIT、4次PLAYER_HIT和generation0/1/2三次fall；GUARDED_HIT不等于玩家防御验收。

终局纸牌已在真实画面显示于来敌眼下，并实际可点重试。Root修正了原“空AABB等于摆位失败”的错误证据语义：直接实体两种bounds均空且未读到AttachmentPanelComponent，记录`ecsVisualBounds=UNOBSERVED numeric=UNOBSERVED`；没有用配置400dp或计算期望值冒充引擎视觉bounds。原点转换证据为ownerOrigin.z≈+.256、rawHead.z=0→headInOwner.z≈-.256，同一基准用于摆位，不能据此认定HMD漂移。

右手v2已获Root和独立三视图复审并进入本包；只改Pinky闭握，保留v1拇指收益，新Ring/Pinky交叉10→0。旧掌背／腕口及closed极浅样本仍保留，完整手部品质未通过。运行时仅消费grip0/1；离线固定右手DAO的open/mid旧侵入不隐去，也不直接等同当前右持刀故障。

同一模拟器干净启动后，最终流程后进程仍运行，单次系统MemAvailable3,396,728kB、应用PSS379,840kB／RSS637,848kB；这不是Space Pro预算或峰值验收。原先LMK发生在全局内存低水位，不能由资产数或当前RSS单独归因；目前没有降画质。Tripo ov doctor本次未完成，已知代理对官方API的TLS失败，余额未知、无新收费任务。

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
- [x] 当前源码417项单元测试通过，0失败/错误/跳过；公开v9包的349项结果仍只属于旧包。
- [ ] 新连续刀刀接触的本次APK真实输入、非穿透、卸力恢复及同步反馈；不沿用旧方向/计时防御的设备通过记录。
- [ ] 玩家弹反、HMD动作闪避、技能与处决的真实设备输入到反馈闭环。
- [x] 当前包真实三轮角色切换、清场补给、胜利、生命归零与失败后重开。
- [ ] 超时、暂停恢复、追踪中断与原生UI重开确认的实际流程。
- [ ] 原生左右手完整握柄贴合、换手、隐藏恢复、前臂切口与退出重建；闭握v2已有原生显示与源审，掌背／腕口、换手及整体肤色仍未作最终质量通过。
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
| courtyard（当前开发资源） | `96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d` |
| right_hand | `3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0` |
| left_hand | `cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541` |

三角色的78骨、10clip、KTX2/mips、同源守势/六步行走/三攻击仍保留。本轮v9已通过唯一producer重导，typed/profile/三角色binding为365578…；此前HIT阶段未改运行GLB的事实仅属于旧公开包。离线青衫约18mm、玄甲约14mm足底残余、身体拟合约49mm仍未关闭；不扩大判定体掩盖。`turn`资源尚无实际运行编排，湿布/闪避近地/落地无真实witness，当前已移除无caller入口与无用预载；源资产保留，不按文件存在认定可用。

下一批仅围绕同一战斗画面交付：

1. **人物与手刀：** 修自然握柄、袖肩薄厚、皮肤/衣料分区、近距过亮与黑刀面；服装Cloth首件失败，转真实二维衣片构型，保当前脸手/骨架。
2. **一招动作：** fine-overhead v9已完成正式重导与本包三轮流程；01正在据实际原片复核0.50–0.65s快抬头和肩肘手刀，不凭流程通关批准动作品质，不扩新招。
3. **场景：** 整立面64da已换入唯一courtyard并显示于本包原生准备态；进一步检查动态法线/接缝和Space Pro成本。静态合批候选另由06制作，未合入，不凭静态计数归因LMK。
4. **反馈/UI：** 旧整身白闪已在上一公开包删除；本轮薄刀轨、近场光、终局文本和面板世界锚已进入公开开发包；实际结算点击已通过，08据原生片继续检查刀轨/接触像素可读性，07处理黑刀和近场肤色。只消费真实事件，头手保持实时，不用相机抖动补力度。

各方向实物、Root修改意见和当前责任见 [并行制作入口](agents/README.md)。每次收件要求同机位正常视距前后图/短片和可追溯源；尺寸、面数、离线图或测试PASS均不能代替实际品质验收。
