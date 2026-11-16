# 原生竞技场验收清单

当前为可运行的开发预览，**整体人物、动作与打击品质未通过，成品 Demo 未完成**。唯一工程使用 Kotlin + PICO Spatial SDK 6.1.9，目标 Space Pro / OS 6、Full Stage。只打磨既有雨夜庭院、持刀攻防与三轮短 PVE。

## 最新手部与输入原生检查（2026-11-17，运行包尚未公开）

主掌背V沟定位为MCP前皮面被错误按指部权重保护；只修14个授权掌背混权点，Right为a9809a45、Left为ecc07136，同源一次镜像，common Grip与手写SDK/frame代码不变。原材质和neutral前后图显示长沟消失，Right15项验证与Left28独立正负例通过；实际Source/T/S/UV/3KTX与保护指体/内掌均保持，继承109指间交面继续披露。

当前诊断APK `62b2ece822b7749413ff076b31cbb07575808b5034c41ebd9209bb1c77cef2bd`，220966944 B，已核设备安装包SHA与19个装包GLB。源码基点519f2c6仅新增有界诊断里的实际SDK头姿记录，战斗代码仍沿用446测试通过组合；本次没有为资产或日志变动重复宣称新测试数。此前2f22包的取景没有清楚展示手部，不作为精修观感通过。

已定位模拟器前台进程与实际Qt焦点的差异：Controller Setting窗口吞掉移动键，导致手柄仍在头部原点；主视口恢复焦点后，一次Shift+D的实际SDK右手x从.28到.29m，设置窗负例被helper拒绝。真实头眼高为1.65m，右手(.28,1.4,-.45)，原始SDK、实际手Root与刀Root一致。[当前实际画面](../ArtSource/refinement/presentation/native-hand-input-ready-2026-11-17.png)可查看新握刀手；肤色偏亮、指节棱角仍在，整体手部品质未通过，SDK TBN与左持仍待验。

[24秒原生交战片](../ArtSource/refinement/presentation/native-hand-input-contact-2026-11-17.mp4)与[精确身份及事件](../ArtSource/refinement/presentation/native-hand-input-2026-11-17.json)来自同一有界录制/输入调度：真实UI Start accepted，2次SOFT_HIT、6次BLOCK金属反馈、2次PLAYER_HIT有同时间窗消费收据。主机窗口录制1229帧、24秒，压缩后帧数/时长保持且完整解码通过，无插帧/改速/声音；这不是PICO渲染帧率。片中持续架刀存在数秒同姿态，Root已续派接触卸力诊断；不能据BLOCK日志认定玩家弹反或整体拼刀手感通过。本包仍未完成三轮胜利/身法/技能处决/Space Pro验收，公开APK没有更新。

## 当前开发预览：自然守势、呼吸与湿石（2026-11-16）

已公开为[自然守势与呼吸开发预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-natural-guard-2026-11-16)，固定源码`add9f3f3b070081b52fd0fdbd3d0a3375aa0f023`。APK/校验文件/原生PNG/版本JSON四附件均核对服务端SHA、字节数及uploaded状态；这是pre-release，不是成品验收。

本节点使用binding `dc0df17be4b24504f7a21e3b2192e3c1ed5264b58be3f62a752f0ce83aaf8872`，APK SHA256 `e13f370c875aba54e119a4aeb60daa66cdfdff8cd212484da6d7f27f5875f9d9`，220019997 B。构建与446项单元测试通过，0失败/错误/跳过；19个打包GLB与工作树逐字节匹配，生成数据精确检查通过。

- 新自然守势统一idle/walk/三攻击首尾；idle为181键120Hz/1.5秒LINEAR，代理保361个真实采样，准备态/倒计时/交战的显示与判定共用动作时钟，暂停/击中停顿/持续拼刀同冻。
- 修正旋转精确键与插值的归一化语义；三个实际target的234TRS、世界矩阵与五锚闭环通过。生成样本按角色分入三个私有类，保持所有Double位模式，解决JVM常量池容量限制。
- 异体型保骨长FK会产生自然刀端微动：base不到1µm、青衫约.397mm、玄甲约1.051mm；2mm制作预算有181/361样本、独立预测及六负例支持，不改变脚/root精度或闭环exact门。
- 湿石bd5仅替两张1024材质图，场景布局/几何/光源不变。已真实加载和显示，但湿反射/金属配光及整体画质仍未通过。

[实际Full Stage画面](../ArtSource/refinement/presentation/native-natural-guard-ready-2026-11-16.png)及[版本/输入/边界](../ArtSource/refinement/presentation/native-natural-guard-2026-11-16.json)。本包在emulator-5554安装启动，SDK实际seek回执0/1.080945/.8265794与共用source时钟对应；这不是蒙皮顶点读回。进程21610只描述本次记录窗口。后台操作器将原生键盘/指针事件限制到指定模拟器进程/窗口，SDK已收到实际轨迹；不注入应用pose或胜负状态。

当前只完成新包准备态/共享待机的端内验证。8秒录制只有8帧，明确不能证明动作流畅性。新包完整三轮、弹反/头部闪避/技能处决、追踪/暂停全流程、音画触觉同步和Space Pro性能/舒适度均未完成。有限网格检查保留三处原左右攻击穿胸（青衫RIGHT1.1左手18对、玄甲LEFT1.1右前臂105对、玄甲RIGHT1.1左手53对），已比对旧6d同刻数目相同，不能标成已解决。

新手部、护甲和灯笼首件仍在Root专项review中，不在本APK。衣料/脸发/刀面反光和实际接触表现仍低于目标，**这是开发节点，不是成品验收通过**。

## 上一公开节点：全身上劈v5、共同握点与真实换手（2026-11-15）

本轮正式source bank为`713532c0f047573a77632a55a0178d79a9833a04a9bdb25ef986cc161caa598a`，APK SHA256 `498c9fc325cd50e52f7da14147f4961210c60382c367cf5d8441092929b3a2a7`，220424428 B。全Gradle构建与**436项单元测试通过，0失败／错误／跳过**；当前manifest完整binding及Root receipt校验、typed精确检查通过。该结果覆盖本次完整代码／资产组合，旧v9证据继续只属旧包。

2026-11-16已公开为[原生握持与动作开发预览](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-grip-motion-2026-11-15)，固定源码`6d3551903440039afbef75a322dd66a6842c1e65`；8附件均为uploaded，服务端SHA256和字节数与本地逐一相等。新自然守势、掌背／腕口、干净肩甲与湿石材仍为独立制作候选，未进入本包。

- 新overhead v5保78骨／234轨／211键120Hz，修右手碰头及两处左臂碰胸；三个实际target共48指定姿态未检出声明范围钢／身体或非邻接核心交叉，Root已看六图。它是有限源检查，不证明连续时刻或所有衣料。
- 旧cue中点折速与cue恢复路径删除；逐方向source／runtime同契约，OH总1.75s，cue只为制作元数据。LEFT／RIGHT原始动作不变。
- 新左手`d8e9c3cb…`与删除旧腕部C补偿同次整合，闭握拇指11mm穿柄／薄片已去除；实际DAO只余两个约.093mm食指浅点，无新增自交。继承109对指间表面交叉、腕口／掌背粗糙及开中态旧侵入不隐去，整体手部品质仍未通过。
- 原生准备页左／右入口经真实buffer→reducer→Arena；Root实际点LEFT后先撤旧观察，再收新侧并显示左持，随后RIGHT及Start通过。换手失败不锁存／不延期，战斗／倒计时禁切。

[准备态](../ArtSource/refinement/presentation/native-grip-motion-ready-2026-11-15.png)、[实际左持](../ArtSource/refinement/presentation/native-grip-motion-left-2026-11-15.png)、[26秒原生连续接触片](../ArtSource/refinement/presentation/native-grip-motion-contact-2026-11-15.mp4)、[第二轮](../ArtSource/refinement/presentation/native-grip-motion-round2-2026-11-15.png)、[真实Retry返回准备态](../ArtSource/refinement/presentation/native-grip-motion-retry-2026-11-15.png)和[身份／边界](../ArtSource/refinement/presentation/native-grip-motion-2026-11-15.json)。均来自本次实际PICO Emulator，使用系统原生鼠标／键盘事件进入模拟器、SDK_NATIVE provider与共用判定，未注入应用状态。观察到BLOCK／SOFT_HIT／PLAYER_HIT及对应反馈消费。Controller模式移动为每次按键约1cm，已记录真实双手摆位；不能用日志“发送成功”代替SDK轨迹。

**新APK完整三轮胜利仍未通过。** 当前真实流程已击败首人、进入第二轮，并经历超时／玩家失败及UI Retry。第二次固定鼠标轨迹只产生格挡和受伤，不能把未通关录像说成成品。PARRY、HMD闪避、蓄力／处决、音画／触觉同步、持续拼刀的自然卸力以及Space Pro性能／热量／舒适度仍待验证。Metallic刀面偏黑、人物／肩甲整体细度未达目标品质；solid-shoulder V2因266 REST自交及外表见证退回，未进入正式Boss。

## 上一开发节点：真实刀刀接触＋入口构造（8ac1a78）

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
- [x] 当前公开6d35519组合的436项单元测试通过，0失败/错误/跳过；公开v9包的349项结果仍只属于旧包。
- [ ] 新刀刀接触的完整画面验收：6d35519已取得真实SDK手柄输入、BLOCK／命中／受伤和26秒交战片；连续非穿透、主动回撤卸力、精确弹反与完整同步反馈仍待验，不沿用旧包通过记录。
- [ ] 玩家弹反、HMD动作闪避、技能与处决的真实设备输入到反馈闭环。
- [x] 旧公开v9包真实三轮角色切换、清场补给、胜利、生命归零与失败后重开；此项只属旧包。
- [ ] 当前6d35519完整三轮胜利：已证明首人击败进入第二轮、失败后实际UI重试；未取得该包三轮胜利。
- [ ] 超时、暂停恢复、追踪中断与原生UI重开确认的实际流程。
- [ ] 原生左右手完整握柄贴合、隐藏恢复、前臂切口与退出重建；6d35519准备页左右换手及新左手真实显示已证实，掌背／腕口、指间交面与整体肤色仍未作最终质量通过。
- [ ] 原生短时交叉淡入中的模型与判定精度；数据同源不等于每个blend瞬间已测量。
- [ ] 真正接触时的短停、粒子、轨迹、数字、声音与触觉同步；38ms效果不能用稀疏录制认定通过。
- [ ] Space Pro 的帧耗时、纹理/模型内存、切轮峰值、持续运行、发热、舒适度、声音与触觉。

## 正式资产与视觉关卡

| 当前正式运行资产 | SHA-256 |
| --- | --- |
| base | `f6bc15d6c46c0a3e61d27ed21f76a9c120942d9cee5eece2309cf25073ad6ffd` |
| indigo | `cce030fc4dc37f33c7300fb953d98b7d9a641b5deec8b60f384928d5c116e593` |
| veteran | `803d88201a47da9c73a9a95845a5749915dc29b6eb733f4b5212da13b04f9bed` |
| dao_grip | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |
| courtyard（当前开发资源） | `96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d` |
| right_hand | `3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0` |
| left_hand | `d8e9c3cb034f465e4527c13aad84e7ba283c3efcc537ab254c6295717cd1bbfd` |

三角色的78骨、10clip、KTX2/mips、同源守势/六步行走/三攻击仍保留。当前v5已通过唯一producer重导，typed/profile/三角色binding为713532c0…；365578…及此前HIT未改运行GLB的事实仅属于旧公开包。离线青衫约18mm、玄甲约14mm足底残余、身体拟合约49mm仍未关闭；不扩大判定体掩盖。`turn`资源尚无实际运行编排，湿布/闪避近地/落地无真实witness，当前已移除无caller入口与无用预载；源资产保留，不按文件存在认定可用。

下一批仅围绕同一战斗画面交付：

1. **人物与手刀：** 修自然握柄、袖肩薄厚、皮肤/衣料分区、近距过亮与黑刀面；服装Cloth首件失败，转真实二维衣片构型，保当前脸手/骨架。
2. **一招动作：** fine-overhead v9已完成正式重导与本包三轮流程；01正在据实际原片复核0.50–0.65s快抬头和肩肘手刀，不凭流程通关批准动作品质，不扩新招。
3. **场景：** 整立面64da已换入唯一courtyard并显示于本包原生准备态；进一步检查动态法线/接缝和Space Pro成本。静态合批候选另由06制作，未合入，不凭静态计数归因LMK。
4. **反馈/UI：** 旧整身白闪已在上一公开包删除；本轮薄刀轨、近场光、终局文本和面板世界锚已进入公开开发包；实际结算点击已通过，08据原生片继续检查刀轨/接触像素可读性，07处理黑刀和近场肤色。只消费真实事件，头手保持实时，不用相机抖动补力度。

各方向实物、Root修改意见和当前责任见 [并行制作入口](agents/README.md)。每次收件要求同机位正常视距前后图/短片和可追溯源；尺寸、面数、离线图或测试PASS均不能代替实际品质验收。
