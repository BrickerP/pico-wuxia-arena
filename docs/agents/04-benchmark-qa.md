# 04 · PICO端内人物配光与接地影

## 当前状态

**阶段3执行中。** 首版配光已由Root构建安装并取得Full Stage画面，原六primitive材质候选因分片高光拒绝。当前制作单primitive连续材质贴图补丁与IBL KTX候选。

## 上一轮成果与Root review

CombatImpact、分层FX、11段音效、触觉与离线预演已交付。正式PICO准备态已显示新刀客。离线棚灯和端内条件差异明显，当前方向光接近正视顺光，侧灯接近人物3m衰减边界。代码没有显式接入IBL，SDK默认贡献仍需通过实际画面对照。

## 文件所有权

阶段2当前仅写 `ArtSource/refinement/lighting/stage2/` 与本文件，HomeStage及正式资源均冻结。阶段2任务为HDR→IBL KTX生成链核对与raw rig部位PBR审校，以下HomeStage修改范围为上一阶段合同。

负责app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt中照明、阴影接线及对应资源生命周期，ArtSource/refinement/lighting/、必要的app照明资源和本文件。保留现有角色／手部presenter、战斗位置、面板布局与CombatImpact接口。Main、战斗内核、角色GLB、producer和manifest由Root维护。

## 本轮任务

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

唯一工作仓库为 /Users/yupeng/projects/personal/pico-wuxia-arena。当前模型基线为main的cc12bf1，base.glb SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641。运行栈为Kotlin + PICO Spatial SDK6.1.9，终端Space Pro／OS6。

其他会话正在同一仓库并行。各自只修改责任范围，保留其他人的编辑。Git提交、分支、合入、共享构建、设备操作、实际截图与正式模型发布由Root统一负责。候选输出留在各自目录，library、app角色与公共manifest由Root发布。

本轮允许离线资产生成、渲染及专项制作检查。游戏整局自测继续后置。30分钟内交付首阶段实物，写明“阶段结束”、输入SHA、文件、效果、剩余问题与下一步建议后结束当前回合。遇到阻塞先交已做出的部分并写明具体阻塞，继续能独立完成的工作。用当前模型和已安装依赖推进，不为等审批或等待其他线程维持空转。

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

## 当前阶段2执行项

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
