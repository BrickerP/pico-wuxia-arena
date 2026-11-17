# 03 · 角色模型、蒙皮和材质交付合同

更新：2026-11-17。目标是中式写实刀客及自然动作；Tripo/Blender是制作工具，glTF警告数量或面数不等于视觉质量。

## 正式版本与Root评审

开发提交 `37d0ebf4`，见[草稿PR #13](https://github.com/BrickerP/pico-wuxia-arena/pull/13)。正式binding `7af35f02`，veteran `42e89a29`。raw源 `ec67ae3c` 已保留，源朝向经既有转换，身高仍1.78m；禁止用新头重新缩放整个角色。

新头/发、Tripo护肩、连续袖身、834左臂及紧凑受击已进入同包ddac原生实战；第三轮Boss实际显示过。头部3图2048，其余1024，4K源保留。含刀47091三角、78骨及rest/IBM沿既有产线保全。

Root退回旧仰天/翻刀HEAD；现recipe3身体gain0.35、颈头0.11，胸约13.64°、颈相对胸约10.25°，300ms刀速峰值约5.78–5.92m/s。BODY/SIDE和非reaction保全。当前护肩固定原2100面单Upperarm挂接，继承的12组局部交叉如实披露，不称全模型零穿插。不得擅自扩大删面域或换肩形让动作线程失去固定目标。

皮肤仍偏平滑年轻、颈部衔接和整体写实度未通过。原生比赛卡刀由01继续修，不用静态模型图冒充战斗体验已好。

## 切线精修候选：已收件，尚未正式发布

交接：`ArtSource/refinement/character/veteran-head-refinement/tangent-finish/current-production/handoff.json`。

- 基于当前prepared PNG `f4342127` 输出 `bea4844a`，保留最新recipe3；绝不能用旧926整包覆盖导致受击动作回退。
- 五个body primitive采用MikkTSpace，并对一个实际零UV角执行已批准的明确退化策略。134个必要顶点split，原corner P/N/UV/JOINTS/WEIGHTS、刀及78骨/IBM保全。
- 24 Node、10编排和1次真实源/recipe3集成检查通过；独立116项检查、10动作各.75s的corner蒙皮差为0。
- glTF零错误，身体缺切线警告5→0。DAO两处及原零权joint警告保留，不以清警告擅改权重。
- Mikk与许可证收敛到本仓；禁止把个人网站仓库作为生产依赖，更不能修改它。
- 身体几何身份按真实indexed corner的P/J/W/三角语义核对；纯切线split不改变实际表面，但模型文件和审批身份必须显式重绑。

## Root下一任务

已退回并修正固定诊断目录阻断复建的问题；`current-production/review-revision/handoff.json`保留两次真实raw→recipe3同路径重建、产物/规范化报告一致及失败保全证据。Root下一步审核该revision的`production.patch`与原vendor闭包，只接入唯一 `prepare_character_library.py`：wrist/recipe3之后、KTX之前。公共工具、配置及依赖进入production binding，再生成私有候选、核10clip/轮廓/刀与身体校准、审批并正式发布。不得另建导出器、自动沿用旧授权或直接替换正式GLB。

发布后以同视角、同头/手Pose及同配光做原生材质对照。切线修复只证明法线贴图解释更明确，只有实际画面能判断皮肤、布料和金属质感是否改善。若仍不足，下一件围绕现有脸部/衣料PBR细节制作，不扩大角色数量或新玩法。

Root维护正式资源、typed生成、Gradle、设备和Git；制作路只交所属候选、可复建源码、真实输入输出身份、可看的图与已知限制。所有Blender走现有 `run_blender.py` 共享锁；先确认实际进程，禁止因观察超时重复启动。
