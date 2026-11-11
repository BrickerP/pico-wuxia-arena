# 08 · 运行时攻击／弹反／防御／闪避特效

## 当前状态

首轮执行待会话接手。2026-11-11用户要求扩大并行，整体品质需明显提升。

## 目标

把现有偏小、偏弱的核心火花提升为清楚且有材质差异的打击反馈。参考《只狼》《鬼武者》《影之刃零》的接触节奏与招架辨识，使用当前VR实际头手和接触数据，维持视点实时跟踪。

## 所有权

负责 content/CombatEffects.kt、PlayerBladeTrail.kt、BladeTrailGeometry.kt、新的ContactParticleEmitter／轨迹模块、ArtSource/refinement/effects/runtime-polish/及专项测试。本文件为交接。04继续独立颗粒／近地资产制作，你负责SDK接线。CombatAudio和Profile由11维护，HomeStage／Main最终接线归Root。

允许你最小扩展 core/combat/CombatImpact.kt 和 PlayerCombatResolver.kt 的每次接触切向元数据，保持既有阈值、碰撞规则与伤害公式。ArenaSession由09维护，给Root emitImpact所需的最小元数据转发补丁，不直接修改该文件。

## 制作队列

1. 阅读04的 contact-polish GLB、motion.json、driver_contract和参考采样器。将独立火星按各自初速／重力／寿命驱动，基于真实接触点／法线／同次挥刀切向，事件过期不排队重播。
2. 为金属、布／身体、要害、弹反、格挡、技能与致命建立辨识层次。先做一记普通斩和一次弹反的完整接触包络，正常视距下能清楚看到核心、碎屑与回收节奏。
3. 适当增强真实刀光的热芯／半透明尾迹，沿已有65ms真实采样改进，静止、异常和重建基线仍清理。强化来自当前动作的弧线与接触停顿。
4. 水滴只用于已确认湿衣物，裸头与普通SOFT标签不能自动当水面。缺切向时核心与粒子选择需明确，不用固定左右手roll冒充实际刀路。
5. 粒子数量、尺寸、曝光与不透明度按实际视距调校，单个接触有界预算与可复用池。Root会统一运行实际触发取图，交源码、资源接口与短时序预演。

## 首轮交付

普通命中与弹反两个完整运行时效果，包含可见实物和最小专项验证。随后接湿布、闪避近地尘、落地与技能。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

由负责会话填写真实产物与review问题。

