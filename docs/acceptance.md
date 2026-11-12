# 原生竞技场验收清单

当前为可运行的开发预览，**整体人物、动作与打击品质未通过，成品 Demo 未完成**。唯一工程使用 Kotlin + PICO Spatial SDK 6.1.9，目标 Space Pro / OS 6、Full Stage。只打磨既有雨夜庭院、持刀攻防与三轮短 PVE。

## 当前可交付节点

| 节点 | 产物 | 实际边界 |
| --- | --- | --- |
| 已公开原生包 | [native-input-feedback-2026-11-12](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/native-input-feedback-2026-11-12)，源码 `0ed05ce761bd6f53ef54b1aeef7cf62b9e124b26`，APK `9e5fc90a3d341b6b21a36585594ce25d9b16a10d498b424244a67dcc11b24b2b` | 328项测试通过；真实 SDK 挥刀、命中、敌血100→12、玩家 BLOCK 与终局重开已有证据。不是完整三轮与真机验收。 |
| main整合点 | [PR #11](https://github.com/BrickerP/pico-wuxia-arena/pull/11)，`93f3ded393d4c417f6fb883447cc1e6fe4602199` | 合入原生输入与已审核资产；网页扩世界原型不计原生交付。 |
| 本机双手/HIT包 | [APK身份](../artifacts/native-hands-hit-2026-11-13/init-fix-identity.json)，APK `a8907a84b867e9383f6d2f5a50d02f43fc75ecae7fbdf1d0cce886d742eb498b` | managed assembleDebug成功、已安装启动。修复了disabled skeleton创建动画导致场景中止；[准备态实图](../ArtSource/refinement/presentation/native-hands-ready-2026-11-13.png)已显示手部、场景、敌人。[实际交战图](../ArtSource/refinement/presentation/native-hands-contact-2026-11-13.png)敌血12/100、玩家80/100。尚未公开。 |

当前包的真实输入记录为 [real-input.log](../artifacts/native-hands-hit-2026-11-13/real-input.log) 与 [桌面操作收据](../artifacts/native-hands-hit-2026-11-13/real-input-ui.json)：实际鼠标 Start accepted → COUNTDOWN → SDK手柄轨迹 → SOFT_HIT / GUARDED_HIT / PLAYER_HIT，受击播放 `hit_body`。没有状态注入或按键宏代替共享判定。

本机环境的 managed Run `run-2e7eba15-3d6a-4b59-aeff-87f152533fd8` 构建步骤通过，整体delivery因自定义验收没有自动证据而BLOCKED；不能宣称整个workflow通过。源码/构建、实际画面与整体品质分开记录。

## 已证实与待验

- [x] 原生准备态加载庭院、首名角色、玩家刀和真实第一人称手部。
- [x] 同一 SDK 头手来源进入共享判定；实际鼠标开局、挥刀、扣血与既有软/金属反馈有同时间窗证据。
- [x] 已公开9e包真实玩家 BLOCK、异向受伤、失败后重开并再次开局。
- [x] 普通 HIT 从正式GLB导出真实受击采样；渲染与接触查询共享 clip/source clock，保留接触短停与过渡。新typed数据与三份正式profile完全一致。
- [x] 341项单元测试在双手/HIT组合源码上通过；初始化顺序修复后的运行已重新构建并进入实际交战，最终复验收据见 [fixed-test-counts.json](../artifacts/native-hands-hit-2026-11-13/fixed-test-counts.json)。
- [ ] 玩家弹反、HMD动作闪避、技能与处决的真实设备输入到反馈闭环。
- [ ] 三轮角色切换、清场补给、胜利、超时、暂停恢复与追踪中断的完整实际流程。
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

三角色的78骨、10clip、KTX2/mips、同源守势/六步行走/三攻击仍保留。此次HIT数据发布没有改变运行GLB。离线青衫约18mm、玄甲约14mm足底残余、身体拟合约49mm仍未关闭；不扩大判定体掩盖。`turn`资源尚无实际运行编排，湿布/闪避近地/落地资源亦没有完整真实事件入口，不能按文件存在认定可用。

下一批仅围绕同一战斗画面交付：

1. **人物与手刀：** 修自然握柄、袖肩薄厚、皮肤/衣料分区、近距过亮与黑刀面；服装Cloth首件失败，转真实二维衣片构型，保当前脸手/骨架。
2. **一招动作：** fine-overhead v7的整体随势比旧版明显，但准备/接触时低头弯腰需要三分之四/侧面复核；未正式重导，暂不扩新招。
3. **场景：** 整立面64da候选已由Root看图接受开发整合，尚待替换唯一courtyard并检查原生法线、接缝与成本；不是新场景。
4. **反馈/UI：** 处理普通命中的整身白块、刀面遮脸和重复大面板；只消费真实事件，头手保持实时，不用相机抖动补力度。

各方向实物、Root修改意见和当前责任见 [并行制作入口](agents/README.md)。每次收件要求同机位正常视距前后图/短片和可追溯源；尺寸、面数、离线图或测试PASS均不能代替实际品质验收。
