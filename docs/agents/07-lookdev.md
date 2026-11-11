# 07 · PICO原生光影与氛围

## 当前状态

首轮执行待会话接手。2026-11-11用户要求扩大并行，整体品质需明显提升。

## 目标

建立雨夜中式的冷暖光色、脸部体积、刀刃反射与场景纵深。正常玩法画面具有明确主次和空气感，避免整个空间同亮或黑成背景。与06几何共同对齐《黑神话》的环境层次，维持VR出招可读性。

## 所有权

负责 ArtSource/refinement/lookdev/、新的 content/SceneLighting.kt 或明确命名的新照明模块，以及本文件。HomeStage／Main由Root最终接线，你给最小接入补丁说明。04旧lighting/stage3候选只读，可复用其HDR和KTX链。

## 制作队列

1. 读取当前HomeStage配光与实际端内图，提出一个强主方向并交可复现光照剖面，明确脸／刀／门楼／路面／远景各层的亮度和色温关系。
2. 基于已安装SDK官方6.1文档和6.1.9公有类型实现code-owned照明模块，资源和Entity由场景owner持有，失败／取消／销毁完整释放。
3. 接入可验证的IBL候选。已有 ArtSource/refinement/lighting/stage3/ibl/ 的原创HDR、Filament工具与KTX规范头候选可复用，PICO格式互操作仍待Root实测。不要把生成KTX等同已生效。
4. 优先原生PBR、有效环境光、接地影与合适光源半径。雨雾／远景层按SDK实际能力实现，任何曝光、tone-map、反射或雾API先核官方。Shader无法证明时报告具体边界并继续可实现的照明。
5. 与06交换灯位、湿地材质和背景方向，与08交换接触灯强度。交同一实际模型和机位的neutral／目标光照对照、模块代码和资源身份。

## 首轮交付

可由Root接入的原生光照模块与一组可见lookdev对照。端内构建／设备／取图统一由Root进行，你完成全部接入准备并继续雨雾、灯笼与地面反射层次。

## 共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

## 阶段交付

由负责会话填写真实产物与review问题。

