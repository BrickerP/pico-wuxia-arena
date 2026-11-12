# 04 · 独立接触与地面特效资产

## 当前接力 · 原生接触视觉review（2026-11-12）

**本轮阶段结束，等待review。** Root已收并发布软／金属／湿布／闪避／落地5份粒子资源，08运行消费已接通；本录制原日志明确确认SOFT／METAL两family共6条accepted消费。Root已修模拟器输入，APK `9e5fc90…b24b2b` 的实际SDK鼠标→共享resolver→扣血局部通过，交付记录328测试全过。本轮引用该交付，不重跑测试或继续等待真实输入前置。

本轮所有权仅为 `ArtSource/refinement/effects/native-contact-review/` 及04交接，已检查15.8秒H264片、同名JSON／PNG、原VFR采样和contact-attempt.log。提交两项明确画面派修：**10.296611秒整身白闪填平脸／衣褶细节（08／07）**；**12.080411、12.455311秒来刀呈大块黑面，遮住头脸且刃线不清（02／07，必要时01核轨迹）**。没有仅凭单目重叠给03报确定穿模。

原捕获只有74帧，71／73个相邻间隔超过38ms。独立SOFT／METAL粒子像素仍待补证，不能由画面未见推成未触发，也不能把整身白闪当成38ms新SOFT效果通过。日志与视频没有精确对时锚，GUARDED_HIT是敌人挡住玩家攻击，玩家格挡／弹反、完整三轮和Space Pro仍开放。详见 [本轮视觉review](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/native-contact-review/README.md) 与 [逐项证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/native-contact-review/review.json)。

## 历史源制作目标与队列（2026-11-11）

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你集中做独立火星、湿布、纤维、闪避近地尘、落地、技能与致命特效源资产。08接运行时发射／真实切向／轨迹与可复用池，07接全局lookdev，11接声音触觉。

当前微小星火和水滴在正常视距仍偏弱，按可见性明确调整热芯、数量、宽度、明暗层次与短寿命包络，交实际比例前后短片并与08对齐，维持材质差异和不遮来刀。既有motion.json／TBN／Stage重力接口作为共同数据。旧lighting候选、HDR/KTX来源与限制交07，global配光后续移出本会话。不要用固定DEAD秒数或HUD提示冒充真实落地。

## 历史visibility-v3源交付状态

**visibility-v3阶段结束，等待review。** 已交更强的金属与湿布源资产、1.5／2.5m同条件前后图和短片，统一复建、节点／曲线检查及渲染输入SHA核对通过。金属在两种距离有清楚提升，2.5m湿布仍细；08／Root的运行接入与端内观感尚待验证。交付与下一项见文末，旧lighting阶段记录属于历史，后续全局lookdev归07。

### Root阶段3收件与反馈呈现接线

Root已查看连续MR脸／领口前后图。三角硬切高光问题已消除，连续mask与单primitive组合方法接受。当前可见提升仍较轻，材质候选继续保留审校用途，先按顶部队列推进接触特效实物。实际生成的HDR KTX与标准头候选已收件，PICO加载和环境光互操作交Root专项接入。

Root在HomeStage增加角色独占白闪与实际刀尖动态ribbon的所有权／生命周期接线，并统一接触灯的要害／致命层次。旧HomeStage整文件409400aa哈希属于首版配光输入，当前Root已修改该文件；原主光／补光／接地影配置保持其已审核参数。04候选不需回写Root的共享源码，原输入快照继续保留各自阶段身份。

反馈事件现在携带appliedDamage、zone和fatal，音频／触觉／接触灯／FX共同消费CombatFeedbackProfile.accent。FX已删除长期等待队列，120ms内的当前接触按fatal／parry优先占槽，核心普通金属65ms、弹反90ms，scar缩到100ms。新效果实物以此时序制作，避免再把旧整组长闪光烘入模型。独立飞溅子层与真实切向接口随候选交Root统一接入。

## 上一轮成果与Root review

CombatImpact、分层FX、11段音效、触觉与离线预演已交付。正式PICO准备态已显示新刀客。离线棚灯和端内条件差异明显，当前方向光接近正视顺光，侧灯接近人物3m衰减边界。代码没有显式接入IBL，SDK默认贡献仍需通过实际画面对照。

## 文件所有权

当前续派仅负责 ArtSource/refinement/effects/native-contact-review/ 与本文件的视觉review交接。以下contact-polish制作属于已交历史源工作；HomeStage、照明、音频、共享CombatEffects运行文件仍由Root／07／08／11分工维护。

## 历史配光阶段任务（已完成）

1. 读既有场景和已安装6.1官方文档，交叉核对6.1.9公开类型，按代码所属场景使用适用的Spatial场景技能。当前固定主角SHA见共同约束。
2. 在原场景建立有体积感的主光方向和有效补光，确保初始人物确实位于有效照明区域，保留酒馆冷暖气氛。
3. 用已公开的GroundShadowComponent配置实际渲染mesh和接收地面，核对不向children传播的边界；方向／聚光阴影使用确切公开能力。
4. 核对StageEnvironmentLightingComponent、ImageBasedLightSource与.ktx资源路径。已有可复用且来源清楚的资源时纳入同一最终场景；资产工具受阻时先交已完成配光和接地影，不为等待HDR转换拖住阶段。
5. 资源与场景一起释放，加载中断、初始化失败和重入保持一致。新增SDK调用先查文档与类型，不凭记忆猜接口。全局曝光能力与Editor预览设置分开。

## 审核产物

HomeStage可编译修改、资源和来源、主光／补光位置与有效范围、阴影caster／receiver绑定说明、若有IBL则给资源与强度说明、静态生命周期自审。Root统一构建、安装并以相同机位／角色／姿态取实际Full Stage前后图。

## 下游

01／02／03本阶段不覆盖正式app模型，本会话按固定模型独立完成。保留已交付FX／音频语义，光照改进以脸、衣褶、材质反射与脚底关系可读为门槛。

## 共同执行约束

唯一工作仓库为 /Users/yupeng/projects/personal/pico-wuxia-arena。历史配光输入为main的cc12bf1、base.glb SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641；该快照不代表后续Root发布的正式模型，本阶段实际参考输入以文末及render_manifest为准。运行栈为Kotlin + PICO Spatial SDK6.1.9，终端Space Pro／OS6。

其他会话正在同一仓库并行。各自只修改责任范围，保留其他人的编辑。Git提交、分支、合入、共享构建、设备操作、实际截图与正式模型发布由Root统一负责。候选输出留在各自目录，library、app角色与公共manifest由Root发布。

本轮允许离线资产生成、渲染及专项制作检查。游戏整局自测继续后置。12路升级首轮45分钟内交付实物，写明“阶段结束，等待review”、输入SHA、文件、效果、剩余问题与下一项。对应review返回后再进入下一轮；已明确授权的独立检查继续完成。遇阻塞先交已有实物与具体阻塞，Root负责共享接入和设备验收。

## 阶段回报

**本阶段结束，交Root统一review、构建和端内取图。** 已完成HomeStage配光、实际mesh接地影和相关生命周期修改。输入base.glb制作前后SHA保持 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`。本阶段在30分钟内交付，正式角色和生产资产均按共同约束保持只读。

### 生产源码与配光

修改位于 [HomeStage.kt](/Users/yupeng/projects/personal/pico-wuxia-arena/app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt:54)。原主光沿默认−Z正面照射；原两侧点光到初始脸／躯干约3.010／3.135米，超过3米衰减半径。现采用斜向方向主光，加两盏进入初始人物有效范围的点补光，沿用原有光源数量与接触脉冲。

| 光源 | Stage位置或发射方向 | 强度及范围 | 颜色RGB |
| --- | --- | --- | --- |
| 主光 | 方向(0.5014, −0.6217, −0.6017)，由前左上方照入 | 1100 lux，动态投影关闭 | (0.92, 0.95, 1.00) |
| 暖补光 | (−1.30, 1.80, −1.10)米 | 2300 lumen，半径4.2米 | (1.00, 0.72, 0.46) |
| 冷补光 | (1.25, 1.65, −1.55)米 | 1300 lumen，半径4.0米 | (0.58, 0.74, 1.00) |

方向光四元数为 `Quat(−0.347382f, −0.280147f, 0f, 0.894899f)`，按官方光源局部−Z发射轴验算，并保留Stage到场景根局部的公有转换。暖补光距初始脸／躯干1.849／1.967米，冷补光1.512／1.609米，均小于各自半径的一半。lux与lumen按各自单位使用。点补光提供冷暖照明，方向主光承担斜向塑形。接触点140ms脉冲、角色／手部presenter、战斗位置和面板布局继续沿用现有入口。

### 实际mesh与地面接地影

GroundShadowComponent逐个绑定实际ModelComponent实体，遍历子树；公开合同明确该组件不向children传播。三份正式角色GLB各包含一个 `TripoBody_Mesh`，角色及同mesh的DAO材质部分设 `castsShadowEnabled=true, receivesShadowEnabled=false`。地面接收目标为以下已从活动GLB场景核对的实体，逐mesh设 `false, true`。

| 场景资产 | 接收子树 | 源mesh数 |
| --- | --- | ---: |
| tavern_slice.glb | Paving | 1 |
| forecourt.glb | Paving | 1 |
| courtyard_details.glb | SidePaving_Geometry | 1 |

初始化日志会输出 `GroundShadow bound label=… meshes=… casts=… receives=…`。源层级已核对，实际SDK加载数量由Root结合日志确认。本阶段采用GroundShadow顶投接地影作为单一阴影基准，主方向光设 `castsShadowEnabled=false`。骨骼动作后的阴影形状、深浅与帧开销仍待端内验收。[官方接地影说明](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_rendering_dynamic-shadowing.md)、[不传播与公有构造](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/api-reference/com.pico.spatial.core.ecs.md:2696)、[光源方向与动态阴影](/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_rendering_dynamic-lighting.md)

### IBL与曝光核对

本阶段没有合格、来源许可明确的IBL-ready KTX可直接纳入运行。库存仅发现官方模板的museum_day_ibl.exr源图，缺少可确认的官方转换工具，模板内也未找到独立资源许可。已交付 [IBL资源与接口核对](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/ibl/README.md)，其中记录源路径、SHA、Cube／ENV_LIGHTING配置要求及6.1.9公开接口。

因此本阶段交付已完成的配光和接地影，保留既有环境贡献。SDK默认IBL贡献需要Root同机位画面对照。StageEnvironmentLightingComponent强度为2的intensityExponent次方，示例8f对应乘256。Editor的Environment Preview Exposure仅用于Editor预览；已查官方6.1公有资料中未找到现有Full Stage的全局曝光／tone-mapper曲线setter。Unlit材质参与tone mapping的开关维持其材质含义。

后续IBL接入需要先取得可复用许可与经过官方处理、格式验证的HDR cubemap KTX，再由Root统一加入最终场景。本阶段未添加新app纹理、曝光配置或额外依赖。

### 生命周期与专项检查

灯实体由当前场景根拥有，root销毁时一起释放。addPointLight挂载或初始化失败会销毁自身；外层初始化失败分别尝试清理未挂实体，cleanup异常保留在原异常的suppressed中，然后独立尝试owner.release。取消继续抛出原CancellationException。SceneOwner释放时分别隔离presenter撤销错误，几何回调与root销毁由finally保证顺序。异步加载后的root身份检查继续保护加载中断与重入。

已完成正确性、可维护性、界面／文案与变更范围自审，并经独立只读复核通过。新增SDK调用先读取官方6.1文档，再与安装的6.1.9公有构造与setter交叉核对。静态差异检查通过，未改Main、战斗内核、正式GLB、producer、manifest或构建配置。

新增 [verify_lighting.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/verify_lighting.py) 读取实际Kotlin常量及活动GLB场景，验证主光方向、补光覆盖、源mesh目标与模型SHA，输出 [lighting_profile.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/lighting_profile.json)。四项离线校验器用例实际通过，覆盖有效子mesh、缺失／空receiver、有效补光、半径边界和非有限参数。该结果为源码／几何检查，运行亮度与SDK阴影仍待Root统一构建和实际截图。

### Root下一步取图出口

统一构建后，以同一机位、53b80e…00641角色及相同准备态取Full Stage前后图。先核对六条caster／receiver绑定日志，再观察脸部明暗分区、衣褶、DAO反射与脚底接地；确认移动及换轮后仍使用当前角色实际mesh。IBL阻塞和曝光核对边界按上节保留，实际性能与Space Pro表现分别记录。

**本轮首阶段配光与接地影生产结束。** 交付HomeStage源码、离线校验器／参数剖面与IBL证据说明，Root负责统一编译、安装、实际画面对照与后续续派，本会话结束当前回合。

### Root收口选择回应

按Root只读review，本阶段以GroundShadow稳定接地基准为最终阴影路径。已关闭主方向光动态投影，保留斜向key与冷暖补光塑形。双影／脚底过暗属于尚待现场验证的叠加风险，本次收口用于取得单一基准；后续真实方向影由Root另行对照后决定替换。

已同步离线校验器和lighting_profile.json，明确记录 `shadowMode=GroundShadow`、`directionalShadowEnabled=false`，并校验实际源码开关。四项离线用例、场景参数与mesh绑定检查及静态差异检查通过。角色输入SHA仍为53b80e…00641，真实画面与编译由Root统一验证。

**本轮GroundShadow收口阶段结束。** 源码与阶段回报已交Root立即构建／截图，本会话结束当前回合。

## Root初版review决定

实际mesh绑定、Stage坐标转换与生命周期初审通过。GroundShadow与方向动态影叠加存在双影／过暗风险，当前还未经现场对照。本阶段选择单套GroundShadow接地基准，斜向主光负责塑形并关闭该主光的动态投影。下一步由Root构建取图，按可见结果审校。

## 历史阶段2执行项

HomeStage冻结在409400aad752611ffbd948aa62426c6ea14504bde3d35bacbaf0056d49538df4，由Root合入。责任目录为lighting/stage2。核对可复现HDR到IBL KTX工具链，给有效资源／接线或确切缺件；工具受阻时继续现raw rig部位PBR候选，皮肤／眼／发／布／皮／铜的分色区域、材质参数和面分组作为可组合补丁。POSITION／UV／骨架／权重／动作保持，使用现有贴图及已支持的普通PBR。

## Root首版运行review

12秒编译成功，APK SHA3c008c61801a9b053905f463d7f3e29712da1da1d483456f5254e4312d599821，已安装启动。观察到三处receiver与三角色caster绑定，场景最终加载完成。实际图能看见脸、衣褶和脚底投影，接受为可见基准。首次45秒启动观察未到场景完成，后续单次快照确认就绪。

前后实际取景位置和idle时刻不完全一致，当前不能作严格定量A/B；IBL、动作和换轮后的阴影以及Space Pro性能继续待验收。正式角色输入仍为53b80e71…00641。

## 阶段2回报 · IBL工具链与raw部位PBR候选

**阶段结束，交Root审核。** 本阶段仅写 `ArtSource/refinement/lighting/stage2/` 与本文件。HomeStage SHA保持 `409400aad752611ffbd948aa62426c6ea14504bde3d35bacbaf0056d49538df4`，正式base仍为53b80e…00641。raw输入为 `ArtSource/tripo-warrior/refined-base60k/rig.glb`，SHA为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`，35,308顶点、60,006面、78骨、0动画。[输入清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/inputs.json)

Root已回填首阶段安装后脸／衣褶／脚底投影及六条绑定日志可见。该结果仅接受为可见基准；前后机位与idle时刻有差异，严格A/B继续归Root执行。

### IBL实物、可复现链与阻塞

已交原创CC0的 [512×256 HDR源](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/ibl/original_studio_latlong.hdr)、[生成器](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/ibl/generate_source_hdr.py)与[显示映射预览](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/ibl/source_preview.png)。RGBE源经Blender解码，最大通道8.0625，保留HDR范围，源与许可记录于同目录source_manifest.json。

[工具链说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/ibl/README.md)给出Filament官方v1.80.0 mac包、43.3MB、完整归档SHA和校验／生成命令。候选链使用cmgen的HDR输入、SH及roughness预滤与KTX1输出，参数为 `--format=ktx --size=128 --ibl-samples=1024 --ibl-ld=<输出目录>`。

当前本机缺少该工具或PICO官方转换器，安装交Root安排，阶段内没有下载安装。PICO公有资料尚未确认cmgen SH／roughness mip布局与ENV_LIGHTING等价，mac包实际可执行架构也待安装核对。因此当前交付是合法HDR源和可复现候选链，尚无经PICO验证的IBL KTX或正式app接线。后续先核对六面HDR／预滤mip与工具输出，再经官方互操作或实际加载验证后接入。

### raw材质候选与实际审校图

已交 [分色区域板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/pbr/material_regions_board.png)、[同相机／同灯脸与腰带PBR前后图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/pbr/pbr_before_after.png)，以及 [材质／面分组raw候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/pbr/pbr_candidate_raw.glb)、[参数补丁](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/pbr/pbr_patch.json)与[原face ID映射](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/pbr/face_material_map.json)。候选SHA为 `efff09a702d84798c86b36edbf79a25ac4fc4e8638cf1d1b660b5821c37b4507`。

候选使用原baseColor／normal／metallicRoughness三张贴图和标准glTF PBR。每组共享原属性accessor，只建立原面ID对应的indices和材质索引。分区依据为源atlas取样与位置假设，诊断色仅用于审校图；PBR候选保留原atlas颜色。

| 候选区域 | 原面数 | roughnessFactor | metallicFactor |
| --- | ---: | ---: | ---: |
| 未分配／边界及眼眶 | 15766 | 原值 | 原值 |
| 皮肤 | 4505 | 0.66 | 0 |
| 头发 | 5045 | 0.82 | 0 |
| 布料 | 27872 | 1.00 | 0 |
| 皮革 | 6798 | 0.76 | 0 |
| 暖金属扣具／铜候选 | 20 | 0.70 | 1 |

独立眼球／角膜当前为0面，眼眶保持源材质。铜仅有20面暖金属扣具seed，材质种类尚未证实。既有权重分区没有可信的皮肤／眼／发／皮革／铜材质mask，R_Eye与L_Eye也没有正权重支持，不能据此自动给眼睛赋材质。

已目视图板。腰带下和靴面有碎片化皮革／布料边界，眼眶未分配区域较宽，脸部after额头及面颊出现分片亮斑；这些结果尚不能证明材质观感通过。当前交付为可追溯审校候选，暂不建议直接合入正式角色。[独立视觉审校记录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/visual_review.json)

### 结构验证与组合接口

新增 [独立校验器](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/verify_material_candidate.py)已实际验证全部6个primitive，按face ID还原60,006个有向三角，每面恰好一次。POSITION／NORMAL／UV／JOINTS／WEIGHTS字节、nodes、skin／rest／逆绑定、原0动画、图像、纹理与采样器保持一致，原BIN完整前缀不变。四项校验器测试通过，包含属性变更拒绝、交错属性、三角朝向及重复面拒绝。[独立验证结果](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage2/verification.json)

Root组合时先选择已通过的02权重／03领口delta，再按原vertex ID、拓扑、UV和稳定skin身份应用face材质补丁，保留目标的POSITION／WEIGHTS等上游修改。新增或重排的领口面需要额外映射。当前02权重候选仍为BLOCKED，03尚无机读领口边界，本阶段没有擅自组合或发布。

原 `deformation/diagnose_weights.py` 的primitive()只取首primitive，分面后需要聚合全部body primitive；本阶段独立验证器已覆盖全部6组。raw候选本身没有动画，正式8clip与DAO的组合由Root现有producer执行并验证。

### 下一步与结束

IBL由Root安排工具安装与PICO格式兼容核对。PBR先确认实际可见面与atlas的对应、修正皮肤／衣物分区边界及眼部归属，再小幅调参；铜扣具需逐面确认。当前同灯REST图用于离线审校，端内响应与组合后表现由Root专项验证。

**本轮阶段2结束。** 已交HDR源与工具链证据、raw材质候选／面映射／参数补丁、分色及近景图、独立结构与视觉检查。HomeStage、runtime、library和正式app角色保持冻结，本会话结束当前回合。

## Root阶段2 review与阶段3续派

Root已查看同机位PBR前后图。脸颊与额头的分片高光、腰部碎片化边界未达到正式使用标准，当前六primitive候选保留审校用途。原创HDR与来源、生成器可以保留，KTX互操作仍需实物证据。

阶段3立即执行，目录为lighting/stage3，首项实物在30分钟内交付。

1. 优先修正材质连续性。以原始单primitive模型和原atlas为输入，只对已确认皮肤、布、皮革、扣具区域制作可组合的metallicRoughness贴图补丁，保留原baseColor与normal。逐三角硬切材质造成的新分片需消除，保持一个body primitive。边界、眼眶和不确定区域保留源值，UV chart边缘需有明确处理依据。交面／像素mask、参数、原图到候选图的变化，以及同机位脸、领口、腰带、靴面前后图。若贴图方案仍恶化，明确拒绝并给最小原因，勿为完成而发布。
2. 本轮已授权在用户缓存目录下载并解包固定版本Filament工具，无需等待Root安排。下载前核对官方发布与校验和，确认本机架构并实际生成KTX候选。不要提交二进制工具归档，不改app、HomeStage、依赖或设备。验证六面、HDR格式和预滤mip，PICO加载兼容与端内表现交Root验证。工具失败时提交具体错误后继续第一项。
3. 保留原POSITION、NORMAL、UV、JOINTS、WEIGHTS、骨架、动画及原源文件。补丁供Root组合02／03产物。公共制作脚本、正式库、Git与设备仍由Root独占。

交阶段结束报告后，若Root正在集成，可继续独立准备当前场景灯笼／湿石／木构的材质问题近景与最小修复候选，限定原有场景和图层，不增加新场景或模式。

## 阶段3回报 · 连续MR补丁与实际IBL KTX候选

**阶段结束，交Root review。** 首项实物在30分钟内落盘，后续独立验证与交接已收束。本阶段只写 `ArtSource/refinement/lighting/stage3/` 和本文件；固定版工具仅下载解包到用户缓存。HomeStage仍为409400aa…38df4、raw仍为43a34e3a…2b81e6、正式base仍为53b80e71…00641，身份见 [阶段3输入清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/inputs.json)。

### 原单primitive连续MR候选

已交 [raw候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/pbr_candidate_raw.glb)，SHA为 `93c668050575225d455bd22f8fbf4753983044d4d78d5d408aba8e8a587264d3`。原meshes、单primitive、indices、attributes、materials／factor、nodes、skin、动画、baseColor／normal均保持。仅在原BIN后追加PNG，将image2指向新MR，原BIN完整前缀保持。

- [脸／领口同机位同灯图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/face_collar_before_after.png)、[腰带／靴面同机位同灯图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/belt_boots_before_after.png)。
- [原MR／候选／差图／连续mask板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/mr_mask_review.png)，以及mr_source.png、mr_candidate.png、mask_editable／feather／protected和各部位mask。
- [参数补丁](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/pbr_patch.json)、[面／像素覆盖](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/face_pixel_masks.json)、[生成与组合说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/pbr/README.md)。

未沿用阶段2碎片face材质标签。此次以真实REST内侧ROI构造连续空间场，按原UV三角像素中心重心插值，分217个保守UV chart。chart边界在内侧12像素smoothstep退回源值，跨chart覆盖冲突为0。眼眶、额头、未确认扣具、边界及其余不确定区保持源值，未将20面金属seed扩大成铜区。

源MR为4096² RGB，R恒255、原无A。仅G／B变化469,197像素，允许区域471,394像素，约为整图2.81%。皮肤G目标为原值×0.90，布×1.05，皮革×0.94，各区域B目标为0，通过连续alpha与原值混合。对应原face覆盖为皮肤222、布2172、皮革326面。

[独立结构／像素验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/verification.json)通过。已实际解码原／候选和三类mask，确认R／A、mask外和保护区不变，原属性／骨架／权重／贴图0与1、单primitive与indices均一致。三项验证器用例通过，覆盖合法内侧变化、保护／mask外拒绝、R／A变更拒绝。[独立校验器](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/verify_stage3.py)

已目视四部位同灯图，未再见阶段2明显三角硬切亮斑；但相对原MR的总体可见收益仍较轻，当前不确认正式观感通过。最小原因是可编辑区域和参数保守，非零alpha均为连续中间值，较多原响应仍被保护。当前候选继续保留审校用途，暂不建议直接发布。[视觉审校结论](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/visual_review.json)

Root组合02／03已批准目标时，只替换MR图片数据，保留目标已有POSITION／NORMAL／JOINTS／WEIGHTS等delta；核对UV和拓扑身份，新增面或chart变化需要重新映射。raw候选仍无动画，正式8clip合成继续由Root的producer验证。

### 实际工具安装、预滤与KTX候选

已在 `/Users/yupeng/Library/Caches/pico-wuxia-arena/filament/v1.80.0/` 下载解包固定官方工具。归档SHA与官方 `b514ec6dc8d6026e70f6e0dc9673b1c5748060a4be5137aea8502a46d740fb6b` 一致，host和cmgen均为arm64。实际help／license与生成命令执行成功，使用阶段2原创CC0 HDR，输出SH与roughness预滤四级128／64／32／16。工具归档和二进制留在用户缓存。

[工具来源、完整命令与候选接线](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/ibl/README.md)与同目录tool_provenance、generation_manifest／output保留完整证据。原始 [generated_ibl.ktx](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/ibl/generated/generated_ibl.ktx)、generated_skybox.ktx和sh.txt已生成。

实际发现原始KTX头存在规范差异，glType／glTypeSize／glBaseInternalFormat为0x8c3a／1／0x8c3a，原始严格校验失败。保留原件及失败证据后，依据Khronos规范另交 [标准头容器候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/ibl/candidate_standard_header.ktx)。仅修正三个头字段为0x8c3b／4／RGB，glInternalFormat仍为0x8c3a。64字节后SH元数据与预滤payload完全相同，实际差异字节为16、20、32、33。[重封装记录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/ibl/header_repack_manifest.json)

标准头候选为522,604字节，SHA `c2f8f6997f800340cd47bb33e75dd0111c0fc8c670ab2dffe5aae113f01629bd`。严格校验和独立读取通过，六面128²、四mip、全部HDR通道有限、峰值8.125，SH含27系数。[独立KTX验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/lighting/stage3/verification_ibl.json)

当前结果证明容器与实际HDR预滤payload，PICO的SH／粗糙度布局互操作、纹理加载与Stage IBL生效仍待Root专项验证。没有改app资产、HomeStage、公共依赖或设备，候选接线仅作为Root集成说明。

**本轮阶段3结束。** 已交原单primitive连续MR实物和像素保护证据、四部位同灯对照、真实生成KTX及规范容器候选。MR可见收益尚待认可，PICO IBL互操作尚待验证；失败与限制均保留，交Root统一决定后续组合与发布。

## 接触精修阶段回报 · 独立火星与湿衣物颗粒

**本阶段实物已交Root review，按顶部队列继续地面效果。** 首批GLB在14:44前落盘，三栏预览在14:50生成。本阶段只写 `ArtSource/refinement/effects/contact-polish/` 与本文件，SDK消费、事件、白闪、刀光和UI由Root维护。409400aa仅保留为旧配光输入快照，当前HomeStage由Root维护。

### 唯一制作入口与候选

[build_contact_polish.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/build_contact_polish.py)为本批唯一制作入口，复用已有Layer／Effect／GLB编码，仅import旧制作模块，候选输出限定新目录。入口在同目录临时构建后逐文件原子发布，已实际复建并核对哈希一致，候选没有覆盖app。

- [金属候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/metal/metal_contact_polish.glb)，14,624字节，SHA `dfa1ab15ceb141fc132c8633871722c4dbc36c902ca8c1b940d1578054c514ce`。core_star与spark_00至11共13个独立mesh，32三角，无动画。核心直径70mm，普通65ms、弹反90ms；12条火星长约12至28mm、宽2.0至2.8mm，寿命180至290ms。
- [湿衣物候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/wet/wet_cloth_contact.glb)，19,448字节，SHA `9d8990c4d66c612182763107c757b42bfee0668dbf555b007d1d1c34a11c27af`。8滴水与2条纤维共10个独立mesh，196三角，无动画。水滴真实外包直径2至3.9mm，寿命180至320ms，材质为普通PBR透明高光近似。

水滴、火星逐节点运动，包含各自初速、寿命与opacity_keys。湿衣物需Root确认真实湿衣料目标，裸头或普通SOFT标签本身不触发水滴。金属素材用于真实金属接触，当前代码接入由Root按实际材质选择。

### 轨迹与Root接口

[driver_contract.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/driver_contract.json)与两目录motion.json给出局部T／B／N基、每个子节点及单位。N为真实法线，T为实际刀路切向在接触面的归一化投影，B=N×T。共享表面偏移8mm由Root锚点只加一次，粒子local初始偏移另列。

参考 [contact_motion.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/contact_motion.py)直接在Stage积分初速和重力(0,−9.81,0)，重力不随接触法线旋转。按真实呈现年龄无状态采样，出生前／寿命结束后为空，不能把过期粒子重启为新接触；没有待播接触队列。Root负责事件新鲜度、致命／弹反优先级和预算。

当前CombatImpact具有point／normal／伤害／fatal，但尚无切向字段。Root需在真实接触生产或消费时保留对应刀尖相邻采样的切向，不能把一批事件都套最终state方向。切向不可用或平行法线时参考函数拒绝，Root控制核心与粒子的发射策略。本阶段没有声称已接真实SDK轨迹。

### 可见实物与验证范围

已交 [三栏分时板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/contact_timeline.png)、[0.5秒预演](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/contact_polish_preview.mp4)与[67ms帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/contact_02.png)。1280×720、30fps、15帧，含10cm标尺，明确标为示例T=Stage+X／B=+Y／N=+Z的离线素材预演。67ms时普通65ms核心已灭，弹反90ms核心仍亮。湿滴按真实毫米尺度呈细小点，缩图下较弱，近身可见性待端内取图。

唯一入口复建、GLB节点／尺寸／寿命及脚本语法检查通过。四项参考轨迹测试实际通过，覆盖TBN与Stage重力、法线旋转后重力保持、无效切向拒绝以及过期／未出生采样。[独立检查结果](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/verification.json)

**独立金属／湿布素材阶段结束。** 真实粒子接入、透明排序、场景光下可见性和帧预算由Root统一验证；本会话继续授权队列的闪避近地尘与落地素材。

## 地面效果阶段回报 · 闪避近地尘与落地候选

**本轮结构与制作实物结束，观感未通过，继续一次材质修正。** 首批两份GLB在15:21落盘，实际Paving对照图／片已交；最终说明和复核收尾超过30分钟。当前候选没有覆盖app。

- [闪避近地尘](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/dodge_ground_polish.glb)，17,980字节，SHA `ebbdaad332022ea017f7207956f3963a675adf3770dd287553076714a352ddf2`。
- [落地低尘](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/landing_ground_polish.glb)，18,072字节，SHA `b29a5d67fee5343e12a318ed7dab8afb4eb55c6d0b98a9e785a0afb3723d55ae`。

每种8个独立cross-card mesh、192三角，无动画。几何原点在体积底面，localZ从0到约2至2.8cm，水平动态包络对角约22.2／32.9cm。闪避寿命260至380ms，落地300至420ms。姿态固定TBN，Stage重力保持−Y，锚点沿真实地面法线外移2mm，底部投影约束在锚点平面以上。

统一制作入口已扩至ground并实际复建，前阶段金属／湿布hash保持。参考采样器新增sample_ground_particle，6项正常／边界测试与独立GLB检查通过；ground自身验证覆盖3种地面法线、非零高度、底部、法线、索引和寿命，最小平面偏差仅浮点−1.87e−16m。[地面说明与检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/README.md)

### 真实承载材质对照与失败

原 [100ms错误渲染证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/review/invalid_shared_alpha/ground_compare_100ms.png)、[300ms错误渲染证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/review/invalid_shared_alpha/ground_compare_300ms.png)与[0.7秒错误渲染短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/review/invalid_shared_alpha/ground_preview.mp4)，1920×544、30fps、21帧。来源为正式forecourt.glb的实际Paving原材质，输入SHA为 `fde7def5888232f0b20fd5959fac4a5edbae1ee51261a88b97e6216ce741477e`。最高水平石面作示例锚点，30cm尺、固定机位／灯光，旧栏注明资源理论包络。

此前目视两图标记FAIL_READABILITY。现已查明离线renderer给8个共用material的mesh各串接一次Alpha multiplier，最终得到8个opacity的乘积；该结论混入制图故障，已撤回对素材本身可见强度的判断。原图仅保留为错误渲染证据。SDK独立Entity／Opacity的实际语义需要每个离线对象独占材质后重新模拟。visibility-v2材质试验已生成，但当前停止调参，先修正制图器并重做v1／v2同条件比较。

### 触发与剩余接口

闪避T应来自实际玩家地面位移，落地应由当前pose与地面真实接触解析，Root提供点／法线／材质。UI闪避提示和固定DEAD秒数不能作为接地事件。参考base-clamp保证传入局部平面的底部关系，实际不平石面、触发同步、致命慢时钟和SDK消费由Root接入。

**地面候选v1结构阶段结束，原视觉判断待修正复核。** 当前优先处理独立颗粒的离线材质所有权，保留错误图与v2试验，不再以错误基准调高素材浓度。

### 独立粒子离线Alpha所有权故障

2026-11-11已用Blender实际导入复现，8个dust对象有8个material slot，但共用同一material。旧alpha_controls循环修改共享Principled Alpha链，造成所有对象读取opacity乘积，例如0.6的8次方约0.0168；原100ms样本约0.0264。共享GLB材质本身合法，本次修复限定离线对象材质副本与单一Alpha控制，原GLB、几何和运动轨迹保持。

将同步检查金属／湿布独立粒子renderer，修正后重出同机位图。此前普通65ms／弹反90ms核心的时长语义仍按数值核对，独立火星、水滴与地尘的亮度判断以修正制图器后的结果为准。当前没有将该离线故障称为SDK实际呈现故障。

## 地尘材质试验与离线Alpha根因修正回报

**本批阶段结束，交Root统一review与接入。** 本轮诊断和制图器统一修复收尾超过30分钟目标，未把错误图当成源素材观感通过或失败的证据。保留原始候选、材质v2试验及无效图归档。

### v2实际素材变化

v2从原独立地尘派生，几何、POSITION／NORMAL／indices、节点变换、尺寸、初始位置／速度、Stage重力、生命周期及opacity关键帧时间完全相同。改变限定为候选实际GLB材质／颜色Alpha和motion的透明度取值。

- [v2闪避GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/visibility-v2/dodge_ground_polish.glb)，22,332字节，SHA `cfca84cc04b880031f6ba0e0e8279bd9ba1a10d54d92060e4405e0f1b12f184c`。
- [v2落地GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/visibility-v2/landing_ground_polish.glb)，22,424字节，SHA `f802ca73ff953432e6afb9a3951247fc236292198414e4f1aeda37d7d600218b`。

baseColorFactor采用暗湿泥色(0.35,0.32,0.28,1)，材质Alpha由0.28改为1；顶点Alpha×1.8并限制到0.65，原中心0.7会被上限下调，透明边缘0保持。motion峰值由原约0.55／0.64改为0.85。没有新增自发光，参数见visibility_patch.json。[独立几何／轨迹／透明边缘核验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/visibility-v2/independent_verification.json)通过。

### 已修正的唯一离线透明控制

[offline_opacity.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/offline_opacity.py)使用公有MaterialSlot的OBJECT链接与material.copy，为每个对象材质槽建立独占材质，每slot只增加一个Alpha因子。contact-polish、ground、visibility-v2三个有效renderer均已使用该helper，重复配置会显式拒绝。

Blender真实回归覆盖两个对象共用同一mesh／源材质，确认0.5和0.8透明度独立、原mesh／shader不变；实际渲染所有权为金属／湿滴36对象对应36材质，ground入口19／19，v2比较24／24。[helper回归证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/opacity_helper_verification.json)

旧金属／湿滴和ground错误图片、短片已归档到各自review/invalid_shared_alpha，明确作废。GLB合法共享材质保持，无需为了离线故障把源素材拆成更多材质。SDK的逐Entity Opacity由Root接入，本阶段仅修正离线模拟它的实例所有权。

### 修正后的实物与判断

已目视 [正确100ms地面比较](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/visibility-v2/review/visibility_v2_100ms.png)与[正确300ms比较](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/ground/visibility-v2/review/visibility_v2_300ms.png)。同一正式Paving、相机、灯光和尺度下，v1原材质呈弱浅尘，v2的低矮尘团更清楚，随后依实际寿命衰减。当前可作为Root专项接入／浓度审校候选，尚不代表PICO观感或写实程度通过。

金属／湿布 [67ms帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/contact_02.png)、[时序板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/contact_timeline.png)及[0.5秒片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/review/contact_polish_preview.mp4)均已用独立Opacity重出。普通65ms核心已结束，弹反90ms核心仍在，火星与毫米水滴各自透明变化。原ground 0.7秒错误片已作废，本轮交正确100／300ms图，避免混用旧片。

### 一键复建与剩余项

唯一build_contact_polish.py已纳入金属、湿布、ground基准及v2材质试验，实际复建的6份GLB哈希与交付一致，catalog明确均为审校候选。6项轨迹／边界用例、GLB尺寸／寿命及v2同几何核验通过，脚本语法与静态差异检查通过。

Root需按真实接触点／法线／切向、真实成功闪避及骨骼落地触发驱动；湿布需真实材质语义，过期事件不重启。SDK透明排序、实际场景浓度与性能由Root验证，白闪／刀光／逐击UI和运行源码继续归Root。原HomeStage409400aa是历史输入快照，本轮未回写任何共享运行文件。

**独立接触与地面候选本批制作结束。** 已交实际GLB、运动代码／合同、修正后的同条件图与重渲片、错误证据归档。授权队列本批候选齐备，Root统一决定正式选择、接入、构建、设备和Git，本会话结束当前回合。

## 12路升级首轮 · visibility-v3制作与08接口

当前按最新队列集中独立源资产，候选目录为 `ArtSource/refinement/effects/contact-polish/visibility-v3/`。07接管旧lighting/stage3的原创HDR、工具记录及标准头KTX候选，PICO互操作仍由07／Root验证；11维护声音／触觉。本轮不改HomeStage、共享FX运行代码、音频或正式app资产。

已制作金属32独立火星、core_star和arc_00／01，共35个mesh；湿布18滴加5纤维，共23个mesh。前者以热近／暖主层／冷余烬分层，后者以hero／main／stretched／fine／fiber分层。正常1.5／2.5m视距、固定FOV60的前后图／片正在制作，范围与强度通过实际资产变化表达。

### 给08的v2数据契约

新源明确使用 [source_contract.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/source_contract.json) 中的 `contact-particle-motion/v2`。新arc仅为真实接触切向定向的短辅弧，Root实际刀尖历史ribbon保持其运行职责。每个可见mesh必须恰好被particles、cores或accents覆盖一次，缺失／重复层应在生成阶段报错，不能默认为常亮。

本轮起始核对时，08的generate_presets.py仍取旧metal／wet motion路径，只解析particles／cores，忽略accents、fatal、tier／priority及方向轴；directional还按scar名称判定。若直接换入新GLB，arc层会未受控可见。08需切到v3 source_jobs、完整吸收上述字段并重新生成handoff／Kotlin，在发布前核对全部mesh覆盖与初始隐藏；后续完成状态以08实际生成结果为准。当前源不自动替换运行资产。

现池无每次12粒子的硬限制。按METAL三槽，新源35mesh对应105个常驻受控mesh，WET一槽对应23mesh，另有锚点／模型根。先按这一实际预算由08选择热近／暖主／余烬层级，预算拒绝必须隐藏对应节点，事件过期仍不排队重播。

普通／弹反核心提案为65／90ms；fatal核心提案按规格对齐150ms，具体事件及呈现时钟由Root／08选择。水滴形状和orientation_axis_local明确区分圆滴、拉伸滴与纤维，避免把所有长轴硬编码为X。接触选择继续依真实材质，裸头SOFT不自动触发湿布飞溅。

## visibility-v3阶段交付 · 正常视距接触源

**阶段结束，等待review。** 2026-11-11 05:04:42 UTC开始，湿布首实物05:12:58落盘，首批正常视距图约05:30交出；最终公平性与来源复核于05:56收尾。首实物在45分钟内完成，最终复核收尾超过该时间窗。本阶段只写04源目录与本文件，08／Root接运行和发布。

### 实际资产与变化

| 候选 | 变化 | 成本与时序 |
| --- | --- | --- |
| [metal_hero_v3.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/metal/metal_hero_v3.glb) | 火星12→32，12热近／12暖主／8冷余烬，另加2条短接触辅弧；细星芒跨度70→140mm，实心中心对角仅14mm | 45,396字节，35mesh，258三角，3材质；普通／弹反／致命核心65／90／150ms |
| [wet_cloth_contact.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/wet/wet_cloth_contact.glb) | 8滴＋2纤维→18滴＋5纤维，含2颗8.5／9mm主滴、4颗主滴、4颗拉伸滴、8颗细滴和5条拖尾纤维 | 48,128字节，23mesh，596三角，3材质；分层寿命180–400ms |

金属热近层长60–100mm、宽5–8mm，暖主与余烬依次缩短、变冷。湿布圆滴3–9mm，拉伸滴长10–18mm、截面3.6–4.5mm；纤维长8–15mm。两份均为项目原创程序几何，无纹理、动画或材质扩展。金属沿用普通PBR emissiveFactor范围0–1；湿布没有自发光、折射或bloom。短辅弧不是实际刀尖历史ribbon。

最终统一入口输出SHA如下，GLB和motion须成对取用。

- 金属GLB：`71502f591b19c3e067772fa1648cc78d10c2c37aac3b4e36102e3027964f6525`；motion：`4c0226c325efbe967255579c0c6ce53da4366f2c8bdd383d9c2335fb1ce7ca14`。
- 湿布GLB：`a96623710d43a5e952a559153ce7cf1d0e75ca68636d5e9e98ff492040f15077`；motion：`910d9f355dfa39895ff40b61a96f0aabaa322f75961048d48561ec61c0c1acf4`。

### 正常视距前后证据

已交 [1.5m普通图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/normal_distance_150cm.png)、[2.5m普通图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/normal_distance_250cm.png)、[1.5m弹反图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/parry_distance_150cm.png)、[2.5m弹反图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/parry_distance_250cm.png)，以及 [1.5m短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/distance_150cm.mp4)、[2.5m短片](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/distance_250cm.mp4)。

每栏原图640×480、水平FOV60、相机到接触点1.5／2.5m，0.5m标尺，不放大特效；同一idle源1.0s姿态和固定灯光。四栏依次旧金属／新金属／旧湿布／新湿布，旧新湿布都固定源TBN。普通取40ms、弹反取50ms；短片2560×610、24fps、21帧、0.875秒，示例两次发射，最后采样第二次年龄433ms，全部层过期，可核 [消失末帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/expiry_clear.png)。致命150ms本轮只验源曲线，未演示实际致命事件。

参考角色为渲染时Root当前 `app/src/main/assets/models/opponents/base.glb`，SHA `0c2a4801aaa6b89866303a9c783b524a88b6440633f0c9348041a6239af7d48a`，仅作比例背景。本轮未写该模型。基准金属／湿布仍为dfa1ab15…514ce／9d8990c4…c27af，完整八项源输入SHA见 [render_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/review/render_manifest.json)。

目视两种距离的新金属热芯与火星更清楚；湿布1.5m亮滴与纤维更易辨认，2.5m仍呈少量细点，不能据此判定端内可读性通过。所有图仅是固定T=Stage+X、N=+Z示例预演；实际切向、场景光、透明排序、头显表现和手感继续由08／Root验收。

### 检查、修复与接入出口

唯一 [build_contact_polish.py](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/build_contact_polish.py) 已实际串行复建六项制作job、八份GLB；原基准／地尘v2与新GLB哈希保持。新源恰好覆盖35／23个可见节点，明确方向轴、tier／priority、核心及accents。6项轨迹回归、3项湿布正常／边界测试通过；漏节点、GLB重名、重复驱动和错误核心末时四种负例均被拒绝。[源检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/verification.json)及[湿布几何检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/effects/contact-polish/visibility-v3/wet/verification.json)通过。

离线81对象对应81独占材质／单Alpha控制，无共享串乘。独立复核发现并修正了旧湿布朝向不公平、重复名称被字典吞掉及核心曲线未检查三处问题。复建曾因wet JSON键插入顺序不同触发SHA拒绝；重排可精确复现旧cda0e66b…，字段值及轨迹完全一致。最终仍从统一入口的910d9f35…重新渲染，渲染起止锁定所有源哈希，最终八项输入与参考角色均实际复核一致，没有替换旧渲染的SHA充数。

08接入继续按上节v2合同完成：切换source_jobs、完整生成particles／cores／accents、初始及过期隐藏、真实切向与Stage重力、湿布真实材质判定。完整金属三槽为105受控mesh、湿布一槽23，实际Entity／透明性能由08／Root检查。全局光照／IBL交07、声音触觉交11，正式选择与设备验证由Root收口。

**本轮visibility-v3制作与离线专项验证结束，等待对应review。** 收到本轮review后继续04范围内的修正与下一阶段地尘／落地或技能／致命源制作；实际VR观感、运行接入及性能尚未验证。

## Root本轮组合审核与续派（2026-11-11）

审核：软／金属／湿布／闪避／落地5资源已由Root发布，08负责运行独立粒子。

下一步：保持接触材质差异与真实地面事件约束；湿布与近地事件没有真实生产者时不能按固定时间伪造，后续据实际受控命中图再修粒子。
