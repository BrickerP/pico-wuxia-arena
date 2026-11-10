# 精修手部握持与角色穿插

## 本轮目标

解决真实角色手指、非持刀手与刀柄／护手之间的明显穿插，进一步改善原生Tripo姿态的握持自然度。

## 责任与文件

本会话负责 ArtSource/refinement/grip/ 候选生产脚本、校准数据和制作近景，以及本文件。现有 prepare_character_library.py、motion_library.json、library 与app运行模型由主控统一发布，避免与人物精修会话同时覆盖。

## 已有基线

三名角色各有78骨、8动作资源。青衫与玄甲已完成握点平移，仍有约9.79mm／7.47mm的残余峰值径向代理，平均深度与深样本增多的取舍已有报告。只移动刀柄不足以完成手指适配。

## 本轮工作

- 以最终实际蒙皮模型做指面、刀柄、护手和非持刀手检查，覆盖native slash1.55–3.4秒、2.117秒接触以及步法／受击姿态。
- 利用各角色自己的Tripo骨架与原生姿态，在握持对齐范围内产生可复建的局部指姿校正候选，保持手腕与刀路时标可追踪。
- 保留原始Tripo输出。人物网格、骨长与蒙皮权重继续沿原源，必要的绑定质量缺陷先量化并提交主控选择Tripo重绑方案。
- 同时评估接触覆盖、悬空间隙、径向交叠和视觉自然度。提供同机位before／after近景及动作小片段。
- 使用当前三角色做候选，新的高精角色就绪后由主控安排适配。当前不提交收费任务。

## 交付与审核

输出候选目录与清楚的发布步骤，原始与派生姿态可复建。只在主仓库工作，不动其他会话文件，不提交或推送，不创建副本。制作可用Blender离线处理，设备与实际视口由主控统一操作。

30分钟内交付一个阶段，遇到骨架或原生姿态的真实限制写清证据，不用持续等待维持状态。

## 本阶段交付

**阶段结束，等待主控 review。本回合完成后直接结束。** 已在 `ArtSource/refinement/grip/` 交付三角色可复建候选、校准数据、实际蒙皮审计和同机位制作近景。发布仍由主控统一执行。本轮费用 0，原始 Tripo、公共 prepare 脚本、library 和 app 资源保持本会话接入时的内容。

候选采用本轮批准的局部指骨旋转方案，每节校正向量上限 18 度。最终保留每角色 78 骨、8 动作，原节点/rest transforms、骨长、蒙皮权重、逆绑定、网格、材质、原 buffer 和关键帧时间输入均受验证。65 个源姿态中，非指骨世界矩阵分量最大差为 0，手腕与刚性刀具原有时标保持。修正数据仅追加至指骨旋转输出。

### 审核实物与复建

- [候选、方法与发布步骤](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/README.md)
- [三角色校准与固定哈希](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/calibration.json)
- [65 姿态右手测量](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/report.json)与[实际刀身／左手审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/left_weapon_audit.json)
- [近景相机、原生时间与最终 GLB 哈希清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/render_manifest.json)

| 角色 | 候选 | slash 原生 2.117 秒的峰值径向代理前→后 | 同机位右手近景 |
| --- | --- | --- | --- |
| 试刀客 | [base.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/candidates/base.glb) | 2.407→0.162 mm | [对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/base_right_before_after.png) |
| 青衫护院 | [indigo.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/candidates/indigo.glb) | 9.793→1.569 mm | [对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_right_before_after.png) |
| 玄甲守擂 | [veteran.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/candidates/veteran.glb) | 7.467→6.475 mm | [对比图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_right_before_after.png) |

三角色平均径向深度均下降，大于 2 mm 的顶点数量分别为 1→0、44→0、37→37。表面 3 mm 内样本分别为 10→16、77→74、64→81。青衫近距覆盖代理保留约 96.1%，需要结合图中握持自然度审核。以上是椭圆柄核与表面顶点的采样代理，样本数并非接触面积。

### 非持刀手与明确残余

实际刀身检查发现，柄核之外存在后段小指穿过刀身的情况。青衫新增 `L_Ring2` 局部 X -9 度，玄甲新增 `L_Pinky1` 局部 Z -18 度，两项均已写入最终 GLB 的全部 8 条对应动作轨道。65 个离散采样姿态均未增加左手确认交叉或 3 mm 近距样本。

| 角色 | 跨 65 姿态累计确认三角形交叉对前→后 | 单姿态峰值前→后 | 仍需审核的画面 |
| --- | --- | --- | --- |
| 试刀客 | 0→0 | 0→0 | 本次采样范围内左手未见确认交叉 |
| 青衫 | 299→275 | 43→33 | [3.133 秒残余小指](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_left_slash_3133_before_after.png)、[3.167 秒局部改善](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_left_slash_3167_before_after.png) |
| 玄甲 | 72→23 | 23→23 | [1.833 秒小指解除](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_left_slash_1833_before_after.png)、[1.55 秒掌部残余](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_left_slash_1550_before_after.png) |

玄甲 1.55 秒残余涉及 `L_Hand` 主导的蒙皮表面，当前限定指姿候选仍留交叉。进一步改变手掌与刀身关系或选择原生重绑方案需主控审核。当前结果不证明整段连续时间均无穿插，共面交叉也不在确认计数范围。握持自然度、掌指过渡和新的高精角色适配继续待审。

### 动作与验证

已交付 44 张 before、44 张 after、11 张近景对比、3 张六姿态板和 3 个九帧 slash 对比 GIF，帧源时间覆盖 1.55–3.4 秒，另包含 walk 与受击。可直接查看[试刀客片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/base_slash_before_after.gif)、[青衫片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/indigo_slash_before_after.gif)、[玄甲片段](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/grip/previews/veteran_slash_before_after.gif)。最终图片清单与最终候选哈希一致，已离线目检关键左右手画面。

实际执行 `verify_grip_candidates.py`，3 个正常路径和 21 个负向拒绝通过。独立验证每条修改输出等于 `normalize(source_q @ Qx @ Qz)`，以及输出类型、有限值、归一化、关键帧数量、追加引用和精确左手关节范围。青衫与玄甲完成最终哈希锁定回放。独立代码复审发现的回放哈希锁与旋转输出验证问题已修复，复审通过。Blender 渲染、脚本语法及差异检查通过。

所有产物均为离线候选，实际应用发布与设备观感由主控统一验收。本会话按阶段交付结束，主控可依据上述实物选择接受局部改善，或另派剩余掌部／小指与绑定关系的后续修正。

## 主控review与下一阶段

主控已查看持刀手同机位图和玄甲1.833秒、青衫3.133秒残余图，接受本阶段指姿的局部改善接入正式producer。指标代表离散代理与交叉采样，掌指自然度和残余刀面穿插继续待修。

下一阶段仅在offhand子目录制作slash的非持刀侧局部腕／必要前臂与手指修正，优先青衫3.133／3.167秒与玄甲1.55秒，采用平滑起止和完整关键姿态检查。右手与刀具轨迹继续固定，原rest、骨长与skin保持。新候选独立评审后由主控统一接入现有制作入口。
