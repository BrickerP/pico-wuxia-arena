# Demo实现与验收清单

## 当前版本与证据

目标为Space Pro／OS 6、Kotlin + PICO Spatial SDK 6.1.9、Full Stage。范围为单雨后酒馆院落、单刀、三名顺序对手和180秒三轮试炼。品质与数值目标见[动作／打击反馈规格](combat-polish-spec.md)，正常视距门槛见[视觉bench](visual-quality-bench.md)。

| 项目 | 当前事实与证据边界 |
| --- | --- |
| 最新本地APK | `app/build/outputs/apk/debug/app-debug.apk`，242,709,448字节 |
| APK SHA-256 | `7e1368fed7423fa5b3d9ea2f567cc1e786fa0bbfa85ebd6409a714369fbfc17e` |
| 组合检查 | 面板pose两行修改前，Root运行`:app:assembleDebug :app:testDebugUnitTest --offline`通过；32个suite、311项，0失败／错误／跳过。修改后仅重新assemble与原生视觉验，未重跑311项 |
| 安装与启动 | 新APK已安装到emulator-5554，运行`com.example.wuxiaarena.p0d2f0182/.platform.LaunchActivity` |
| 新组实际画面 | [canonical-2026-11-11.png](../ArtSource/refinement/presentation/canonical-2026-11-11.png)及[身份清单](../ArtSource/refinement/presentation/canonical-2026-11-11.json)；新头／眼／颈、canonical idle、玩家刀、场景与完整准备面板已显示 |
| 启动检查 | 约27秒完成场景与新人物附着，当次未见NO_MEMORY；不证明三轮换入、GPU预算或Space Pro性能 |
| 前一组合包／唯一区别 | 767bc0af、同为242,709,448字节；当前包只将HomeStage控制面板从`(-0.85,1.15,-1.45)`／yaw34°移至`(-0.6,1.2,-1.75)`／yaw20°，其余源码与APK资产相同 |
| 新人物binding | `b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f`，schema3正式KTX整组 |
| 场景身份 | `8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b`，唯一`courtyard_hero.glb` |
| 旧原生输入证据 | 233584包：`artifacts/input-native/real-key-to-resolver-final.*`，真实Shift+E经SDK进入共享motion.observe，无命中／扣血证据 |
| 旧流程证据 | 同233584包：`artifacts/input-native/start-stationary-left.png`显示敌人接近、玩家受击后的DEFEAT；Start receipt未捕获 |
| GitHub交付 | main已公开节点fd58c04；[现有开发预发行](https://github.com/BrickerP/pico-wuxia-arena/releases/tag/visual-polish-2026-11-11)仍为8d1e456e…、99,113,182字节的旧包，运行源码6b407ac。7e1368fe新包尚未新发布，新checkpoint仍待Root commit／push |

`artifacts/`为本机证据目录，未纳入版本控制。以下勾选仅表示所注明的代码／资源／检查已完成；准备态、旧版本交互和单元测试不能替代新包完整流程或Space Pro体验。

## 流程与原生输入

- [x] 准备、三秒倒计时、三轮交战、清场补给、胜利／死亡／超时与重新挑战代码已接入。
- [x] 玩家生命、体力、气势、连击、分数与本机最佳成绩代码已接入。
- [x] 同一姿态判定器处理挥刀、前刺、架刀、弹反、身法和双手蓄推；破势与低血处决共享入口。
- [x] 暂停、显式恢复、追踪失效和重开撤销旧输入／反馈上下文。
- [x] 设备与模拟器均消费SDK原生HMD／controller pose；模拟器标记DESKTOP，追踪质量UNKNOWN，硬件触觉隔离。
- [x] HMD派生假手、Activity按键宏与右A脚本斩击路径已删除，provider state／support安全门保留。
- [x] 旧233584原生输入包已证明一次真实主机Shift+E → SDK原生右手 → 共享`PlayerCombatResolver.observe`，返回motion frame与刀段。
- [ ] 新7e1368fe包真实挥刀 → 接触判定 → 敌人掉血／反馈的同时间窗证据。
- [ ] 新包三轮胜利、超时、追踪中断、暂停恢复和失败后重新挑战的完整实际流程。

模拟器使用Right Controller Mode、实际启用Controller Button Mode、关闭Keyboard文本模式，Shift+W/A/S/D/Q/E移动虚拟手柄。旧包已有失败结算画面；该画面没有补齐Start receipt，也不能替代新包完整交互。`STARTED/SUPPORTED`、队列注入和资格查询均不算真实命中。

## 正式角色、动作与纹理

- [x] 三轮按base、indigo、veteran请求单一active对手，关闭旧动画／材质并销毁旧角色，再加载新角色；取消与过期返回回收。
- [x] 三名角色各78骨、十段动作，身体与R_Hand刀共用骨架。
- [x] canonical idle／walk与三攻击共用一次根Y校准，typed采样与最终GLB／profile／binding成组发布。
- [x] 正劈、左斩、右斩共享守势端点，source 1.00秒映射ACTIVE接触中点；成功接触继续收势，未命中从ACTIVE末端继续。
- [x] 动画、身体代理与敌刀读取同一profile／源时钟；最终encoded GLB实际蒙皮采样，头／身体XZ校准与body Y coverage合同明确。
- [x] 六步walk源循环1/3–1.5秒，每1.45m六步；动画、代理和脚声消费同组locomotion profile。
- [x] 试刀客采用raw34ce新头、独立眼球／角膜和连续颈桥，已在新包Full Stage首轮准备态显示。
- [x] 三角色和玩家刀使用必需KHR_texture_basisu／KTX2，全分辨率UASTC3、Zstd18、完整mips；保留normal XYZ与sampler分轴语义。
- [x] 受击部位、弹反反应与倒地／处决代码衔接已接入；新增六组反应源尚未进入正式bank。

| 正式运行资产 | SHA-256 |
| --- | --- |
| 试刀客base | `722ffe6e9d3d498629b257e88aaeaf3b0ad368e5c5a37be87ccb85d63a6cf83e` |
| 青衫护院indigo | `94773349741af7cdd2616bb3f5970c5c9fa16f16199c1d0ce5bf6fde6ee0c54e` |
| 玄甲守擂veteran | `cabf24597a83d46495ad67b451867aaf5e1dad1bbb5df21cae286513af9a17a5` |
| 玩家dao_grip | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |

每名角色包含idle、walk、fall、turn、hit_body、hit_head、hit_side及三攻击。turn在bank中，运行编排仍待补齐。

离线检查已证明同组输入／输出身份、非图片GLB数据守恒与profile数值守恒。**动态质量仍OPEN：** 青衫约18.36mm、玄甲约13.68mm的离线足底残余；攻击身体表面拟合残余约48.86mm；实际过渡、握柄、手指、袖口、领口、近距眼／皮肤法线与切轮资源峰值。数据和导入通过不能关闭这些项。

## 场景、UI、特效与声音

- [x] 唯一courtyard_hero替换旧三块运行场景，stage2窗纸暖斑、方向木纹和灯笼纸腹材质已在新包显示。
- [x] 原生月光、四灯笼、v4人物／刀手补光、雨夜IBL和每帧雨雾已接入。
- [x] 纸墨／朱砂UI、三项玩家资源、敌人状态、来势提示、伤害跳字和结算已接入。
- [x] 四页教学与未知来源ranchu配置引导已接入；交战统一160dp，准备／暂停／结算400dp；输入来源和就绪规则不由帮助显示覆盖。
- [x] 同批CombatImpact传递实际伤害、部位、致命标记、接触点、法线和同一扫掠见证切向。
- [x] 身体70ms、要害90ms、甲片85ms、弹反95ms、致命150ms短停；玩家头手保持实时。
- [x] 致命动作0.35倍220ms、180ms恢复；身体白闪28ms／致命40ms；刀具材质独立并恢复原PBR。
- [x] 刀根／刀尖驱动65ms轨迹与短亮核心；异常样本、静止和代次变化断开旧历史。
- [x] 软／金属接触粒子已有真实事件入口，湿布／闪避近地／落地资源已预载。
- [x] 13份WAV、同源六步脚声与事件去重已接入；61项音频JVM和7项最小源专项通过，正式WAV未改。
- [x] 音频重建仅依赖实际10份OGG及许可；整包URL／hash为来源记录，不要求下载ZIP存在。
- [x] 触觉按手别、优先级和代次去重，模拟器不冒充硬件触觉。
- [ ] 湿布／闪避近地／落地的真实事件生产与呈现闭环；目前存在无调用入口，不能称五类效果全部可触发。
- [x] 控制面板pose两行修正后，Root实际查看新PICO设备截图，确认完整面板在视场内且不遮敌人脸和刀。
- [ ] 新位置的真实开始／翻页确认，以及暂停／结算等状态下的完整可操作区域。
- [ ] 重置模拟器观察视角时纸面显示差异定位；普通设备图有暖纸面，尚未证明背面／alpha根因。
- [ ] 命中、格挡、弹反、闪避和致命击的真实短片，以及声音／粒子／跳字同步。
- [ ] 实际SoundPool、六个落脚音画、Space Pro扬声器与触觉体感。

## 当前制作收件与返修

| 方向 | 已审核收件 | 下一门槛 |
| --- | --- | --- |
| 05头脸 | raw34ce连续头颈已正式组合并显示，几何冻结 | 仅微表面／材质delta；近距眼／皮肤、实际攻击／转头压力 |
| 02刀具 | NPC与玩家刀正式发布，装配身份闭合 | 真实握持穿插、刀刃高光和正常视距材质 |
| 03服装 | v3领襟材质／UV方向获开发集成认可，尚未入正式人物 | 袖口真实蒙皮穿插／腕纹参照、扣具装配与组合 |
| 01／09动作 | canonical idle／六步walk与typed profile正式发布 | 实际过渡／足底／代理与反应动作接入 |
| 06／07环境 | stage2场景与v4配光已在新包显示 | 纸面视角差异、人物／背景层次与设备预算 |
| 10／11呈现 | 新配置教学、六步脚声与最小音源已冻结 | UI真实确认／状态切换、真实音画、扬声器与触觉 |

完整交付、来源与Root续派在[12路交接](agents/README.md)。

## 成品Demo仍需通过

- [ ] 新包实际完成开局、三轮胜利、生命归零、超时、暂停恢复和重开，资源正确换入／回收。
- [ ] 真实键盘模拟头手与Space Pro动作走同一判定出口，暂停／换代不残留旧动作。
- [ ] 三方向蓄势、触刀、受击、破势、步法与处决衔接可信，判定与可见身体／刀一致。
- [ ] 三角色0.8m／1.5m／3m正常视距可读，握持、领袖、脚底与场景保持可信接触。
- [ ] 特效、数字、声音、触觉和局部灯光在同次接触同步，密集接触不补播过期事件。
- [ ] UI完整覆盖准备、追踪中断、交战、蓄力、局间与终局，不裁字、不挡脸或刀路。
- [ ] Space Pro实测帧耗时、模型／纹理内存、持续运行、热稳定、舒适度与真实触觉。
- [ ] 同版本可追溯源码／资产、APK、实际操作片段和参赛材料统一发布。

Root负责运行证据与最终合入。每次观察有明确目标和有限时长；不无限轮询logcat、等待会话，也不把离线或测试PASS写成品质达标。
