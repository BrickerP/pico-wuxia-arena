# 03 · 角色模型、蒙皮和材质交付合同

更新：2026-11-17。目标是中式写实刀客及自然动作；Tripo/Blender是制作工具，glTF警告数量或面数不等于视觉质量。

## 正式版本与Root评审

开发提交 `37d0ebf4`，见[草稿PR #13](https://github.com/BrickerP/pico-wuxia-arena/pull/13)。正式binding `7af35f02`，veteran `42e89a29`。raw源 `ec67ae3c` 已保留，源朝向经既有转换，身高仍1.78m；禁止用新头重新缩放整个角色。

新头/发、Tripo护肩、连续袖身、834左臂及紧凑受击已进入同包ddac原生实战；第三轮Boss实际显示过。头部3图2048，其余1024，4K源保留。含刀47091三角、78骨及rest/IBM沿既有产线保全。

Root退回旧仰天/翻刀HEAD；现recipe3身体gain0.35、颈头0.11，胸约13.64°、颈相对胸约10.25°，300ms刀速峰值约5.78–5.92m/s。BODY/SIDE和非reaction保全。当前护肩固定原2100面单Upperarm挂接，继承的12组局部交叉如实披露，不称全模型零穿插。不得擅自扩大删面域或换肩形让动作线程失去固定目标。

皮肤仍偏平滑年轻、颈部衔接和整体写实度未通过。原生比赛卡刀由01继续修，不用静态模型图冒充战斗体验已好。

## 切线精修：Root唯一产线已发布，原生品质待验

交接：`ArtSource/refinement/character/veteran-head-refinement/tangent-finish/current-production/handoff.json`。

- Root实际从当前prepared PNG f434重建bea4844a，再KTX成af74e574；正式binding c8cd395d已发布/typed生成check通过。base/indigo模型和profile逐字不变，三角色10clip与手轨签名exact，veteran profile仅modelSHA及两个vertex_count变化，全部姿态/误差/锚点exact。保留最新recipe3；绝不能用旧926整包覆盖导致受击动作回退。
- 五个body primitive采用MikkTSpace，并对一个实际零UV角执行已批准的明确退化策略。134个必要顶点split，原corner P/N/UV/JOINTS/WEIGHTS、刀及78骨/IBM保全。
- 24 Node、10编排和1次真实源/recipe3集成检查通过；独立116项检查、10动作各.75s的corner蒙皮差为0。
- glTF零错误，身体缺切线警告5→0。DAO两处及原零权joint警告保留，不以清警告擅改权重。
- Mikk与许可证收敛到本仓；禁止把个人网站仓库作为生产依赖，更不能修改它。
- 身体几何身份按真实indexed corner的P/J/W/三角语义核对；纯切线split不改变实际表面，但模型文件和审批身份必须显式重绑。

## 当前下一任务与Root授权

Root已审核并接入review-revision与vendor，唯一产线正式发布c8cd；80项完整Blender产线、24项Node和17项正式profile测试通过。原生A/B待与01新回守势修复包一起审；旧65ac录像不是新材质证明。

下一制作由`skin-surface-refinement/`承担：当前真实头局部高模微雕/解剖分区PBR→烘焙，修过亮塑料感、面部层次与脸颈衔接。眼/唇/发保护，不以全脸噪声或统一降亮冒称精修；先同机位正常距离/近距实图，再Root审批编码。

源审已发现480tri颈延伸UV几乎挤在4K图0.20×0.20像素，单点涂色不能解决。Root已纠正‘所有UV冻结’的过严约束：仅允许这个真实颈桥重展到现head三图独占空白island、必要UV缝复制及该域/必要邻接T重算。三角/材质序、P/N/J/W、骨/IBM/10clip/DAO及非颈脸眼唇发UV保全；出逐角ledger、真实atlas占用图和新受审合同，不能修改旧c8/9bc封件或验收器白名单。若空间不足，先交实际打包证据，Root选最小布局变化。保4K源和runtime头三图≤2048预算。

Root维护正式资源、typed生成、Gradle、设备和Git；制作路只交所属候选、可复建源码、真实输入输出身份、可看的图与已知限制。所有Blender走现有`run_blender.py`共享锁；先确认实际进程，禁止因观察超时重复启动。
