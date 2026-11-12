# 原生竞技场验收清单

当前为可运行的开发预览，**整体人物、动作与打击品质未通过，成品 Demo 未完成**。唯一工程使用 Kotlin + PICO Spatial SDK 6.1.9，目标 Space Pro / OS 6、Full Stage。只打磨既有雨夜庭院、持刀攻防与三轮短 PVE。

## 当前可交付节点

本轮原生UI/命中组合APK：`ca26f4a9837437b05f1d8a3a3b0c0dbb770624656af2eaba148c60dafc605c5c`，242,709,621字节，当前本地待新发布。构建与336项单测通过，源在构建/测试/录制期间一致；运行包已无EnemyHitFlash。UI样式0error/0warning，保Full Stage、既有面板尺寸/位置、输入与规则。

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
| base | `ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20` |
| indigo | `94773349741af7cdd2616bb3f5970c5c9fa16f16199c1d0ce5bf6fde6ee0c54e` |
| veteran | `cabf24597a83d46495ad67b451867aaf5e1dad1bbb5df21cae286513af9a17a5` |
| dao_grip | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |
| courtyard | `9b259812a46f07e95dab6b4e4c414521c05118366ed09fca9632bebc51c27dd5` |
| right_hand | `5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d` |
| left_hand | `cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541` |

三角色的78骨、10clip、KTX2/mips、同源守势/六步行走/三攻击仍保留。此次HIT数据发布没有改变运行GLB。离线青衫约18mm、玄甲约14mm足底残余、身体拟合约49mm仍未关闭；不扩大判定体掩盖。`turn`资源尚无实际运行编排，湿布/闪避近地/落地无真实witness，当前已移除无caller入口与无用预载；源资产保留，不按文件存在认定可用。

下一批仅围绕同一战斗画面交付：

1. **人物与手刀：** 修自然握柄、袖肩薄厚、皮肤/衣料分区、近距过亮与黑刀面；服装Cloth首件失败，转真实二维衣片构型，保当前脸手/骨架。
2. **一招动作：** fine-overhead v7的整体随势比旧版明显，但准备/接触时低头弯腰需要三分之四/侧面复核；未正式重导，暂不扩新招。
3. **场景：** 整立面64da候选已由Root看图接受开发整合，尚待替换唯一courtyard并检查原生法线、接缝与成本；不是新场景。
4. **反馈/UI：** 处理普通命中的整身白块、刀面遮脸和重复大面板；只消费真实事件，头手保持实时，不用相机抖动补力度。

各方向实物、Root修改意见和当前责任见 [并行制作入口](agents/README.md)。每次收件要求同机位正常视距前后图/短片和可追溯源；尺寸、面数、离线图或测试PASS均不能代替实际品质验收。
