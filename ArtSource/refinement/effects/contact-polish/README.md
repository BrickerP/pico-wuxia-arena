# 独立接触粒子候选

本目录为离线源资产与motion候选，08接运行消费，Root统一发布。唯一制作入口为 `build_contact_polish.py`；旧素材保留作可重复的前后基准，不是运行回退路径。

## 当前visibility-v3候选

- `visibility-v3/metal/metal_hero_v3.glb`：32火星、1核心、2短接触辅弧，35mesh、258三角；三层热近／暖主／冷余烬。核心普通65ms、弹反90ms、致命150ms。
- `visibility-v3/wet/wet_cloth_contact.glb`：18滴水和5条纤维，23mesh、596三角；圆滴3–9mm，拉伸滴长10–18mm。
- `visibility-v3/source_contract.json`：`contact-particle-motion/v2`，所有mesh必须由particles／cores／accents恰好覆盖一次；重名、漏驱动、过期曲线均拒绝。
- `visibility-v3/review/`：水平FOV60、1.5／2.5m、0.5m尺的正常视距前后图／片。旧、新湿布都固定源TBN；离线每个对象独占Opacity，全部层过期后补真实空帧。

08需切换新motion路径，吸收accents、fatal、axis、tier／priority，重新生成完整节点定义并在发布前隐藏全部层。当前源不替换app资产。完整SHA、观感限制和阶段review状态见 `docs/agents/04-benchmark-qa.md`。下文为原基准阶段说明。

## 金属模块接口

`metal/build_metal.py` 只公开 `build(output_dir:Path)->dict`，没有独立main入口。Root统一builder传入metal输出目录，返回asset／motion路径及metrics。模块只import现有Layer／Effect／GLB writer，不运行旧main；关闭Python bytecode写入。

`metal/metal_contact_polish.glb` 包含根节点、一个 `core_star` 与 `spark_00` 至 `spark_11`，13个独立mesh，32三角，0动画、0纹理、0扩展。静态原点为局部接触点，local X为切向T、Y为binormal B、Z为外法线N，单位米。材料沿用PBR emissive、顶点alpha、BLEND和双面。

核心最长跨度70mm，由三条细星芒与7mm中心菱形构成。普通核心65ms，弹反核心90ms，没有添加大光盘。12条火星各自长约12–28mm、全宽约2.0–2.8mm，生命周期180–290ms。每条为独立mesh与独立opacity_keys。

motion统一字段为 `node/type/initial_position_local_m/initial_velocity_local_mps/lifetime_s/opacity_keys`，金属额外记录length_m、width_m和cross_section_m。core_star另有normal／parry两套透明时序。初始位置明确包含局部2mm出面偏移，Root anchor共享8mm法线偏移单独负责。

## 真实切向与Stage重力

原基准制作时CombatImpact尚无真实tangent；活动接口以08／Root当前事件定义为准。08／Root须从相邻真实blade-tip采样delta取得方向，投影到接触切平面并归一化为T，再由N与T建立B。无效／近法线delta应按Root规则拒绝或跳过，不能将离线示例T当作游戏轨迹。

粒子位置使用接触点及T/B/N展开初始位置与速度，之后加 `0.5 * gravity_stage * t²`。gravity_stage固定为Stage `[0,-9.81,0]`，不能随接触旋转到local Y。每条短火星的长轴沿瞬时Stage速度调整，截面保留实际毫米尺寸。独立粒子不依赖资源动画导入。

## 实物预览

- `review/contact_timeline.png` 为0／33／67／167／267ms五行三栏分时图。
- `review/contact_polish_preview.mp4` 为0.5秒、30fps、15帧、1280×720的固定机位短片。
- `review/contact_00/01/02/05/08.png` 为原始单帧。
- `review/render_manifest.json` 记录示例基底、重力、帧数与标尺。

三栏依次为普通金属65ms核心、弹反90ms核心、湿布8滴及2纤维。实际加载候选GLB与motion逐节点驱动，保留真实尺寸。10cm标尺在同一空间。67ms一帧中普通核心已结束，弹反核心仍可见。水滴2–3.9mm在此分辨率下呈细小点，分时合板缩小时会更弱，未人工放大。湿布的材质及motion由wet模块负责，保持实际PBR alpha近似，不添加自发光或未支持的折射扩展。

示例基底明确为T=Stage+X、B=+Y、N=+Z，所有栏目使用相同物理比例。该图／片标注离线素材预演，没有bloom、摄影后期或角色／场景替代物。它用于检查形状、数量、时间和重力，不能作为PICO观感或真实输入轨迹证明。

## 收尾与验证

金属生成函数实际调用成功；根统一builder已重建同hash。节点、逐粒子尺寸、寿命、透明边界与静态GLB结构已核对。Root报告统一轨迹／expiry／无效tangent用例与独立尺寸验证通过。实际SDK单粒子Entity接线、槽位预算、端内可读性及真机性能交Root后续验证。

本阶段没有修改runtime、app、旧效果、正式角色、付费任务或设备。后续ground候选由Root统一续派。

## 离线Opacity审校纠正

旧金属／湿滴和ground预览存在共享材质透明度串乘，相关错图／片已归档review/invalid_shared_alpha，旧弱可见性判断撤回。有效render_contact_polish.py、ground/render_ground.py及visibility-v2/render_visibility.py现共用offline_opacity.py，使用对象级MaterialSlot和独占材质，一对象仅一个alpha控制，匹配独立Entity语义。

金属／湿滴三栏36对象／36独占材质的正确0.5秒片、分时板及67ms帧已重出。ground公平100／300ms对照在visibility-v2/review。共享mesh两对象回归与重复配置拒绝测试已实际通过。源GLB与motion保持，端内可见性继续由Root审校。
