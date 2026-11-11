# 07 · PICO原生光影与氛围

## 当前状态

2026-11-11当前冻结为v4：SceneLighting SHA `8243467b...d8d0e`，含awaitRelease及下一组原生聚光。真实SDK独立编译与累计34项专项检查通过，其中11项验证实际SceneLighting协程／释放路径。新值为前向Spot20,000lm、刀补12,000lm、IBL指数4（16倍）；其它环境灯、天气、全部资产不变。依据dac9f5e5失败实图和已核官方单位制作，v4仍须Root重编译取图判断，未宣称已达到视觉目标。准确身份见`ArtSource/refinement/lookdev/native_handoff.json`。

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

### 第一阶段 · 原生模块先交（2026-11-11）

来源：`562449af40ee984ddd8ef61be5c339ac9bea2de5`。实际端内输入图已查看：`artifacts/ui-input/current-scene.png`、`ArtSource/refinement/presentation/combat-feedback-outcome.png`。当前人物／墙面／石路亮度接近、灯笼未形成局部暖池、背景纯黑；本轮以正常视距下冷暖和前后分层解决，未改角色或环境几何。

已制作的真实源码：

- `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/SceneLighting.kt`：固定原生月光＋灯笼＋克制面部反弹光＋侧后冷光；`attach(root)`创建一次，`close()`销毁；`loadEnvironment(assetsRelativePath)`显式加载LINEAR KTX并保留到销毁后释放，异常上抛，没有互操作成功声明。
- `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/SceneWeather.kt`：9个模型实例的有界天气owner（6个雨tile、2个低位侧雾、1个30m天空）；真实米制位置，中央视线留空；按绝对时钟计算下落，暂停隐藏不积压。异步加载后检查旧parent失效，失败／取消清理部分树；Root在返回后仍需做`owner.root !== root`检查并关闭迟到结果。
- `ArtSource/refinement/lookdev/lighting_profile.json`：各层光色关系、真实Stage灯位、IBL候选身份和SDK限制。
- `ArtSource/refinement/lookdev/tests/SceneWeatherMotionTest.kt`、`verify_modules.py`：独立编译与雨tile循环／长运行／低雾侧向界限的测试入口，不调用Gradle。

已完成官方6.1文档与实际6.1.9公开类型核对，证据目录为 `/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/`。`spatial-sdk_rendering_dynamic-lighting.md`确认lux／lumen／米、发射轴为本地−Z、点光不投影；API `GroundShadowComponent`确认必须逐mesh设置、不继承；`StageEnvironmentLightingComponent`确认Full Stage和2^exponent；`spatial-sdk_rendering_particles.md`及`ParticleComponent`公开类型确认runtime不能创建粒子，须Editor预制Bundle。未找到全局Fog／曝光／SSR公共setter，本轮没有猜测接口。天空只提供背景、透明mesh侧雾只提供层次，不冒充IBL或体积雾。

当前接入边界：上述模块尚未由HomeStage调用，属于Root待接入候选。现有GroundShadow和contactLight继续由Root保留。原先HomeStage的KEY_LIGHT与两个fill应由SceneLighting替换，避免叠加导致全场过亮。IBL规范头KTX SHA `c2f8f6997f800340cd47bb33e75dd0111c0fc8c670ab2dffe5aae113f01629bd`沿用04只读候选，PICO实际load及反射仍未验证。

源检查：`placement-source-check.json`通过（2个文件，0 violation，0 advisory）。这是源码检查，不是运行证明。正常视距同机位离线对照正在本路唯一Blender中生成；SDK单模块独立编译进行中。后续在本节补真实图、资产SHA和最终测试结果，并继续可独立的雨／低雾／天空资产，不等待重复批准。

### 第二阶段 · 天气资产与接入合同

三个真实候选均在`ArtSource/refinement/lookdev/weather/`，原创CC0，未发布到app：

| 文件 | 节点 | SHA-256 |
| --- | --- | --- |
| rain_tile.glb | RainTile | 6c89ce09b8202c7ff640bb1113f7b64eb5fe3c9e1d007b611fb7a55a0074a695 |
| side_haze.glb | SideHaze | 7a15675be61dfe56cbd1962d90a514a78ce52639939809910d7b09d1b8a452f9 |
| rain_night_sky.glb | NightSky | 11b80a1337b4d0574fd524a08619a43edab1f30ff6f86284c82d49cf35e12017 |

雨层位于Stage x=±2.7、z=−2.8，三段2m竖向循环，速度2.4m/s；216条交叉渐隐雨条保守留出中央半宽至少1.6m。两块低侧雾中心x=±3、z=−4.4，高度0.7m、峰值alpha0.12，±0.12m水平漂移后的中央最小半宽1.38m。天空为Stage原点的30m闭合内向球、深蓝顶点渐变，不参与环境照明。共9个静态GLB实例，运行时只更新6个雨tile与2个雾条的位置，没有每帧重建资源。详细结构、材质、边界和最终SHA见`weather_contract.json`。

本地检查：真实SDK6.1.9＋Kotlin2.1.20的两个模块独立编译已通过；4项JUnit运动测试通过，覆盖循环边界、Long.MAX_VALUE时钟、雾的侧向界限、非法输入。7项真实GLB测试通过，覆盖确定性、雨条端部alpha0、雾边缘alpha0、float32 accessor精确边界、内向闭合天空、序列化／截断／非法数据拒绝。测试结果在`lookdev/verification/`和`weather/validation.json`。未运行Gradle、共享构建或设备。

自审修复：释放时只有在native rig确实销毁后才标记closed并关闭IBL纹理；若destroy失败，owner保留为可重试，避免有效环境组件引用已关闭纹理。四项复核（正确性、复杂度、可读性、依赖／配置漂移）未引入新依赖或配置，未改根场景或正式资产。

#### Root最小接入顺序

1. 在SceneOwner增加`var lighting: SceneLighting? = null`、`var weather: SceneWeather? = null`，释放时分别调用close，成功后清空引用；若close抛错须保留对象以便重试，错误记录后继续销毁整棵旧root。保留现有逐mesh GroundShadow绑定。
2. 用`owner.lighting = SceneLighting.attach(root)`替换HomeStage旧Directional与warm/cool两个fill，保留原contactLight。最终月光650lux，灯笼1500lm，面部bounce900lm，侧后冷光900lm；不要把新旧灯相加。色温意图为冷月／冷侧缘对暖灯笼与较中性的暖反弹，具体交付以linear RGB为准，不把RGB标成物理黑体温度。
3. Root将三个候选发布到选定的assets目录后，使用真实`asset://...`路径调用`val weather = SceneWeather.load(root, rainAsset, hazeAsset, skyAsset)`；返回后沿当前HomeStage模式检查`owner.root !== root`，迟到就close并return，否则赋给owner。不要在Compose重组中重复加载。
4. 在场景的持续update中调用`owner.weather?.update(System.nanoTime(), visible = true)`；这是环境，不绑定单次命中或对局时钟。追踪／场景真正不可见时可传false；普通暂停仍应保留天空背景。离开scene则close。
5. IBL单独进行真实候选加载：Root发布规范头KTX后，在当前SpatialView的suspend初始化中用`val lighting = checkNotNull(owner.lighting)`，再调用`lighting.loadEnvironment("实际assets相对路径.ktx") { owner.root === root && owner.lighting === lighting }`，不带`asset://`。最终方法已改为suspend：官方允许的纹理加载在IO，组件只在原场景线程挂载。指数0，linear纹理。先保留texture加载结果、日志和同机位反射画面，再决定正式保留；结构PASS不等同加载或生效PASS。

给06的对齐点：左灯实际光心Stage(-1.43,2.86,-3.58)，右后冷缘(1.9,2.5,-3.4)，暖反弹(-1.8,1.55,-1.1)；若新的几何灯笼移动，先更新同一灯位，避免模型与光源脱离。湿地以PBR roughness和真实IBL响应为准；本路没有伪造镜面反射或修改06材质。给08的对齐点：contactLight仍保留原110+180×strength lm、0.60m半径的短pulse，不叠加持续发白的命中灯；新环境的基础灯光不跟打击事件抖动。

### 第三阶段 · 正常视距可见对照

已实际打开并review本路5张原始渲染和两张对照排版。使用正式app当前真实GLB、同一个base对手、同一idle@1.0s、同一机位／曝光，环境以当前HomeStage的实际Stage变换装配。玩家机位距对手2.4m，另给1.5m战斗视距；不是极端近景。

- `ArtSource/refinement/lookdev/review/lighting_compare_player.png`：左为当前配光值，右为本轮目标。左灯笼上方和门柱出现明确暖池，右墙冷光、深蓝背景与暗衣服形成分层。已确认整体收益肉眼可辨。
- `ArtSource/refinement/lookdev/review/lighting_compare_fighter_1_5m.png`：相同人物在1.5m，脸两侧冷暖可见、双眼可读，衣服比面部暗；本轮把最初过暗的面部bounce从420调到最终900lm，源码／JSON／render参数已逐项一致性检查。
- `ArtSource/refinement/lookdev/review/offline_target_with_mesh_weather_player.png`：单独的真实天气组合预演，六个雨tile／两块侧雾／30m天空全部使用已交GLB的实际bytes，在0.6s采样。雨条在两侧可见，人物中央不被遮挡；此正面视角的低侧雾很克制。

渲染provenance：`review/provenance.json` SHA `a00753fba016df63bbbf74367feb55304cd1d230476e8a69eab39b2c097aa22d`，记录全部源模型和天气SHA、摄像机、灯光、原始RGBA参数、曝光、CPU4线程／samples、软件版本与精确变换。最后单个Blender进程完成5图，exit0；原始模型与天气输入bytes均未修改。排版图仅拼接与标注，没有绘制假效果。

严格限制：这些是离线方向证明，非PICO端内画面。点光按共享的lumen/W25、美术转换，sun按lux/W683；PICO cutoff radius未在Blender模拟，所有Blender灯影关闭以接近本轮native路径；没有伪称复现GroundShadow。纯灯光对照的世界颜色是环境近似；真实天空mesh在额外组合图中只对camera可见，不参与Cycles间接光，避免把它误作IBL。

**未通过项：现有dao宽刀身仍主要为暗色轮廓，不能把这轮声明为冷钢反射已完成。** Root需结合02武器候选、真实IBL和实际端内曝光，复核刀刃反射与湿地高光。PICO透明排序／顶点alpha、天空内向显示、IBL互操作、Space Pro曝光／性能均未观测。0.8m／3m的真实设备视图也仍由Root补齐。

本阶段不重复渲染已清楚的机位，继续交雨夜专用HDR与真实cmgen候选，保持正式资源、接线、构建与设备由Root统一。

### 最终冻结 · 新庭院适配与Root三个收口

**Root可立即整合当前模块与三项weather GLB；本路不再抢写这两个Kotlin文件。** 新目标环境为06 `courtyard_hero.glb`，SHA `56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`，世界原点装配。最终`lighting_profile.json`为`rain-night-courtyard-hero-v2-FROZEN`，之前v1小酒馆离线图不代表新庭院端内效果。

原生灯位已删除旧Lantern_L并改为新四anchor：前(-2.15,2.7,-4.7)／(2.15,2.7,-4.7)，各1500lm、半径3.8m；侧(-4.03,2.25,.56)／(4.03,2.25,-1.32)，各1100lm、半径3.4m。月光仍650lux。面部warm_bounce仍900lm，半径从2.6增至4.2m；cool_edge仍900lm，半径从3增至4.5m。共1方向光＋6点光，另保留Root原接触pulse。

面部覆盖已核：对手中心x=0、脸高1.55m、z从−2.4走到−1.1时，warm距离/radius从0.529降至0.429；原2.6m半径在初始处为0.854，确实太靠衰减边界。加入x±.65m、脸高1.35–1.75m的整个走近包络，warm最坏0.662、cool最坏0.805。`verification/coverage.json`有完整采样；3项专项测试同时确认原生源码／JSON数值一致、四灯位对应06真实anchor、整个走近包络位于有效半径内部。这里只证明几何余量，未伪造PICO衰减或端内脸亮度。

Root三个收口均已实改并重新编译：

- `loadEnvironment`已改suspend，IO只运行TextureResource.load；官方直接依据是`spatial-sdk_spatial-container_sample-welcome-to-pico-os-6!.md`的RoomLighting.kt示例315–329行，不是把MainThread组件扔到IO。pending句柄在IO块内部赋值，返回Unit，覆盖返回调度取消导致丢失资源的窗口；回原线程ensureActive、检查closed/rig/stillOwned后挂StageEnvironmentLightingComponent；未接管的资源在原线程关闭，关闭失败则owner保留句柄供重试。
- `close()`仅在texture.close成功之后清空environment并标记closed；若rig已销毁但texture释放抛错，下一次close仍可重试纹理，不重复销毁rig。
- Weather不再要求System.nanoTime非负；周期均用Math.floorMod，已加入Long.MIN_VALUE、−1、Long.MAX_VALUE测试，雨tile连续／雾位移均有界。4项JUnit通过。

雨夜专用IBL：`ArtSource/refinement/lookdev/ibl/candidate_standard_header.ktx` SHA `da33c8cde84d6e2da04125760190d50c6b26521eedd0457c7b726c73d8ff0980`。原创HDR SHA `4d55e3d8b0160952ea131c440a6feac89009ca7bbc0f747d43808d9dfa8175e0`，真实cmgen原始KTX SHA `1ec5ca44d0243da9252de5bfc0d34c0374a28d2d9c6c5118c53c3b0c9d9b3e1f`。Capture参考Stage(0,1.5,−2.4)，两暖瓣指向06真实前灯，月光／侧冷瓣及深蓝环境均为原创正值HDR解析源。固定已安装Filament1.80.0真实cmgen生成128六面、4级预滤、27有限SH；7项测试通过，峰值4.0625。规范候选只改三个KTX头字段，64字节后所有metadata／payload逐字节不变。无下载、付费或Blender重渲。完整命令、工具身份、原始文件、验证在`ibl/`。**镜像方向、PICO格式互操作和实际反射仍待Root实测，不能只凭KTX结构称已生效。**

层次闭环：资产源与GLB/HDR/KTX已交；SDK模块已按6.1.9编译；专项测试21项通过（4运动＋3灯位覆盖＋7weather＋7IBL）；正式资源发布／HomeStage入口／整包构建／端内截图仍由Root执行。本轮没有触碰数据库、UI字符串、Gradle、Manifest、正式资产、设备或Git。下一项有意义证据是Root组合图，再针对实际反射、透明排序、雨是否穿新廊檐和脸部可读性调校，当前冻结不以旧离线图冒充该结果。

### Root共享构建前复核 · 运行文件保持冻结

2026-11-11收到Root已接HomeStage的通知后重新执行独立检查，**SDK6.1.9／Kotlin2.1.20编译通过，4运动＋3灯位覆盖＋7weather＋7IBL共21项全部通过**。未修改任何运行源码、光照常量或资产。冻结源码身份保持：SceneLighting SHA `ab305df4672a22196a61015c28122a1d02705634c012ed28c34344a8d75677bc`；SceneWeather SHA `d180d23d7d64c80024a436f03f84057326173050dc9ab993ad3a09a9fdbba253`。共享Gradle与实际启动期间，本路不再写这两个文件。

发布／接线核对的真实差异，留给Root在其所有权内收口：

1. 三份`app/src/main/assets/models/weather/` GLB与冻结候选SHA完全一致。**`app/src/main/assets/textures/rain_night_ibl.ktx`核对时却仍为旧stage3 SHA `c2f8f6997f800340cd47bb33e75dd0111c0fc8c670ab2dffe5aae113f01629bd`**。若本轮目标是新庭院雨夜IBL，应发布`ArtSource/refinement/lookdev/ibl/candidate_standard_header.ktx`，最终SHA必须为`da33c8cde84d6e2da04125760190d50c6b26521eedd0457c7b726c73d8ff0980`；不能把旧文件的加载结果记作新IBL已验证。本路未代改正式资源。
2. HomeStage第484行的suspend调用与模块签名一致，但回调目前只有`{ owner.root === root }`。完整交接检查是`{ owner.root === root && owner.lighting === lighting }`，防止同一root下owner已换成其它lighting时迟到资源重新挂载。本路未代改HomeStage。
3. HomeStage release在lighting.close或weather.close抛错后仍无条件将对应owner字段置null（核对时约第299–309行）。模块已保留可重试句柄，但调用方无条件清空字段会丢掉重试入口；应只在close成功后置null，失败保留owner并在整棵root销毁后重试释放。此项为异常清理分支，不是编译故障。

本轮仅补交接与独立检查结果。端内材质、透明排序、雨穿新廊檐、PICO KTX互操作和最终曝光继续以Root实际组合画面／日志为准。

### Inflight loader收口 · 最小方案，尚未改运行文件

Root已实际启动组合APK `8ebe75ac...`，告知新庭院、10clip、5FX、新da33 IBL加载且无启动异常；本路未把该通知当成已亲自review图。Root要求先给最小方案，当前运行文件仍保持上节冻结SHA。

已确认缺口：inflight IO尚未结束时environment为null，现close可能返回成功；迟到load若关闭纹理失败，调用方此前清掉owner就丢失重试入口。最小修复只需SceneLighting现有状态收口，不改灯值、天气、HomeStage帧入口或加载架构：

1. `closed`改为`closing`，close入口立即置true；新load和迟到资源adoption均检查closing并拒绝。
2. 暴露仅场景线程读的`val isReleased: Boolean get() = closing && !loadingEnvironment && environment == null && !rig.valid`。loadingEnvironment包含IO、返回调度与pending清理全过程，直到现有finally结束才置false。
3. close只在isReleased时提前返回；仍先销毁rig，纹理close成功才清空environment。销毁或纹理释放失败时字段保留。inflight时close可返回，但isReleased必须为false。
4. 保留现有pending在IO块内赋值、ensureActive／owner guard、迟到资源关闭、关闭失败回存environment和finally清loading的路径。无需新Job、新作用域、NonCancellable或额外资源注册表。
5. Root pending teardown保留owner，close后只有isReleased才移除；false或异常均保留，后续重试。Root自行保留destroy失败的整棵root句柄。

应覆盖的关键窗口：IO期间close后isReleased=false；成功迟到结果不得attach且关闭后变true；迟到结果close失败则仍false且可重试；rig.destroy失败仍false；重复close在真实释放后幂等。本轮仅交方案，没有声称这些新状态测试已实现。

天气持续入口已确认在HomeStage122的`weather?.update(System.nanoTime(), state.sceneReady)`，不再重复添加。当前等待Root安排这个最小源码改动的构建窗口，既有已启动APK不受本路改动影响。

### v3已实改并冻结 · 依据真实组合图的主体可读性与释放状态

Root随后明确解冻本路，要求直接修光照和最小资源状态。已实际打开`artifacts/integrated-polish/ready-scene.png`（APK `8ebe75ac...`，Root报告da33 IBL load无抛错），观察确认：白墙与纸墨UI比主体亮，脸／手明显偏黑，竖起刀身几乎纯黑；v2没有达到主体阅读目标。本轮先改原生模块，不重跑离线图、不修改Root接线。

**最终SceneLighting SHA：`f1687376d8fd969792728c005fc3ad874c02b0e2f79822c1e3e7123eaa0b1cfe`。本路从此再次冻结运行文件，供Root统一重编译。** SceneWeather仍为`d180d23d7d64c80024a436f03f84057326173050dc9ab993ad3a09a9fdbba253`；天气三GLB与da33 KTX bytes均未修改，正式assets的IBL当前也已核对为da33。

| 原生光项 | v2 | v3最终值 |
| --- | --- | --- |
| 人物主补光 | 左侧900lm、偏橙；Stage(-1.8,1.55,-1.1)、半径4.2m | 前向暖白`face_key`，5200lm；Stage(-.75,1.9,+.6)、linear RGB(1,.86,.70)、半径4.8m |
| 刀／手前向补光 | 无 | `blade_fill`，1800lm；Stage(+1.15,1.65,+.25)、linear RGB(.72,.85,1)、半径4.2m |
| 原生IBL指数 | 0，即1倍 | 2，即4倍，继续使用已发布da33 KTX |
| 月光／四灯笼／侧后冷缘 | 650lux／1500,1500,1100,1100lm／900lm | 保持v2的位置、光色与强度 |

这次把主要补光移到玩家前上方，避免对手走近后光源落成纯侧光；暖白比旧橙色更能保住皮肤和手部颜色。face_key到后方z=-4.7m墙面的Z距离就有5.3m，大于其4.8m cutoff半径，因此其主要直射贡献集中于对手与前景，不继续直接抬亮后白墙。IBL提升提供更有效的间接光／刀刃反射输入；是否产生足够反射仍由端内图判断。

几何余量：x±.65m、手到脸y=1.0–1.85m、z=-2.4到-1.1m包络内，face_key最坏距离/半径0.715、blade_fill0.778、原cool_edge0.833，均在范围内部。4项coverage测试通过，检查实际四anchor、全部7个点光源码／JSON一致、脸手走近包络、前向key与后墙cutoff关系、IBL指数与源码一致。这不等于原生亮度验收。

资源状态已按最小方案实改：`closed`换成`closing`，close入口立即置true；`isReleased = closing && !loadingEnvironment && environment == null && !rig.valid`。inflight IO期间即使close无异常返回，isReleased也保持false；迟到结果在原场景线程看到closing后拒绝attach并关闭。pending关闭失败仍回存environment，loading最后才清零，保留Root重试入口。没有新增Job、非取消作用域、资源注册表或运行配置。

**Root调用合同：** close后只有`lighting.isReleased`为true才清掉该owner；为false或抛错都留在pending teardown中，后续在场景线程重试。Root仍独占整棵root销毁失败句柄、HomeStage接线与共享构建。Weather持续update入口保持现有位置，没有重复添加。

验证：v3实际源码针对真实SDK6.1.9／Kotlin2.1.20独立编译通过，原4项运动测试通过（含所有正负Long时钟边界）；4项新coverage检查通过；新增`SceneLightingLifecycleTest.kt`＋`verify_lifecycle.py`用实际SceneLighting源码、SDK操作替身、真实coroutines1.9／Dispatchers.IO和有时限CountDownLatch验证6项场景：加载中关闭不提前Released、迟到纹理close失败重试、rig.destroy失败拒绝adoption并可重试、已绑定纹理close失败重试、调用方取消时回收IO结果、重复close幂等；并断言解码在IO、组件操作与纹理关闭在调用场景线程。6项全部PASS，报告在`tests/lifecycle-stubs/results/`。这组替身测试证明状态和异常路径，不冒充原生SDK运行。

当前累计28项检查通过（4运动＋4coverage＋7weather＋7IBL＋6生命周期），新source gate仍为0 violation／0 advisory。四轮自审确认无新增依赖或配置、无Root接线／天气／正式资产漂移。唯一待验收的新增效果是Root以v3重建后的同机位真实图：脸应比身后暗门亮一层，双手和刃口清楚，白墙不过曝，保留冷暖纵深；本路没有先行声称已达到该视觉结果。

### 新builder等待旧loader · 短方案，未改冻结源码

Root已将closeAtmosphere改成仅isReleased才清owner，并保留destroy失败的teardownRoot。新builder若只看到teardownPending就return，旧IO后来结束不会自动重跑该builder，确有持续空场风险。此轮Root要求先评估，v3运行文件和灯值保持冻结。

最小方案为SceneLighting增加一个不挂在旧load Job下的`CompletableDeferred<Unit>`完成信号和`suspend fun awaitRelease()`，不引入新scope或轮询：

1. 每次真正开始load时创建独立完成信号，保存到owner并捕获局部引用；保持现有loadingEnvironment=true。
2. load的finally先完成pending资源清理／失败回存，再令loadingEnvironment=false，最后对该次信号`complete(Unit)`。旧load失败或取消也正常complete，不能completeExceptionally继承旧取消，亦不能让旧Job先取消信号。
3. awaitRelease在场景线程立即置closing=true，快照本次信号并await一次，随后close一次并check(isReleased)。无inflight时立即走close；释放仍失败就抛错且Root保留owner，不能伪称完成。await中取消新builder只取消该等待者，不取消独立完成信号，下一builder仍可接着等。
4. Root新builder顺序为release旧scene → 有旧lighting则awaitRelease → 再release旧scene一次处理teardownRoot／字段清理 → 确认无teardownPending后继续本次builder。不要await循环、不要再次静默return等待不存在的自动callback。
5. Root可在等待外围加有限withTimeout，并走已有可见scene-load错误／重试入口；超时只结束新builder的等待，保留旧owner与句柄，允许IO之后继续回收。这样原生同步load若异常不返回也不会永久静默空场，不尝试强杀native线程。

信号只保证旧loader的资源交接／清理完成，不代替整个旧builder的root／owner身份检查。仍需保留当前旧回调guard。实施后的专项测试应补：旧load正常／取消均能唤醒等待；新等待者取消不破坏后续等待；无load直接释放；释放异常保留句柄且向Root报告。此节只交最小方案，尚未宣称这些新增测试或API已落盘。

### awaitRelease已完成并冻结 · 精确调用合同

Root明确授权后已完成最小实现；**SceneLighting最终SHA `ce4e4d05042b4b3a50c0c9cfd6c3c3a3d88886dee0548e719e4a82c4b73e9cbc`**。新增仅一个独立`CompletableDeferred<Unit>?`字段、每次load的完成信号，以及`suspend fun awaitRelease()`；未改灯值、天气、资产或HomeStage。Root随后告知已接入releasePreviousScene与15秒withTimeout，正在共享构建，本路保持此源码冻结。

实现顺序：load真正开始时创建无parent的完成信号；现有pending关闭／失败回存逻辑先执行，finally再清loading，最后正常complete(Unit)。awaitRelease立即closing，await一次该信号，检查当前等待者取消，再close一次并检查isReleased。没有await循环、新scope、NonCancellable或native线程中断。旧load取消不会把信号取消；新builder等待者取消也不影响后续等待者。

Root调用合同是：在新SpatialView builder自己的协程中，release旧owner → 旧lighting?.awaitRelease() → 再release一次清旧root／字段 → check无teardownPending → 在同一次builder继续创建新scene。Root保留外围15秒超时、原有可见错误路径及root／owner旧回调guard；取消继续向上传递。等待或native close失败时旧owner保留，不强行清空；没有inflight时awaitRelease直接释放返回。此信号只覆盖loader清理结束，不保证整个旧builder已结束，不能删掉身份guard。

真实SDK6.1.9／Kotlin2.1.20独立编译通过。实际SceneLighting＋真实coroutines1.9的生命周期测试现为**11/11 PASS**，新增5项覆盖旧IO清理唤醒等待、旧load取消仍完成信号、首个等待者取消后后续仍可等、无load立即释放、awaitRelease释放失败上抛且可重试；原6项全部保留。测试使用门闩和有界超时，无sleep；源码完整性检查确认编译／运行前后SHA一致。4项运动、4项coverage及既有资产检查均不变，累计33项。

API依据：[coroutines1.9.0公开CompletableDeferred定义](https://github.com/Kotlin/kotlinx.coroutines/blob/1.9.0/kotlinx-coroutines-core/common/src/CompletableDeferred.kt)确认parent默认为null；[官方await契约](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-deferred/await.html)确认挂起等待不阻塞线程、等待方可取消。本机SDK6.1的SpatialView指南／公开API／生命周期示例未找到新旧initial执行cancelAndJoin的明确保证，因此不能依赖隐含串行顺序。

### dac9f5e5实图复核与下一组受控光照（只读研究，尚未改值）

已查看`artifacts/integrated-polish/relight-ready-scene.png`：人物更居中且UI完整，但脸／手仍偏暗、衣服近黑，刀仍是暗边，窗纸比主体更抢。v3未达到视觉目标，不能以加载或构建通过记为完成。

官方单位核对：DirectionalLight强度为lux；PointLight、SpotLight强度为lumen、范围米；SpotLight沿本地−Z发射，innerAngle内满强度、到outerAngle平滑降为0。证据为本机`com.pico.spatial.core.ecs.md`的DirectionalLight／PointLight／SpotLight公开文档（1217／3927／4540段）。PBR材质能受光，Unlit不受光；三个角色及dao正式GLB均为PBR，没有unlit扩展，刀的metallic=.85–.98、底图均值约RGB112/118/119，并不是黑色底图。当前没有EnvironmentLightingSettings禁用覆盖，也不缺direct-light receiver。Stage IBL作用于整个Full Stage，local receiver只服务局部IBL。

关键尺度区别：把5200lm当成比650lux大很多是错误比较。全向理想点灯在3.112m处正对面仅约`5200/(4πr²)=42.7lux`，还没算角度和范围衰减；这是物理近似上限，不冒充PICO的精确衰减函数。旧离线lumen/W25属于明确记录的美术转换，不能用其亮度预测原生结果。

下一组候选是**用一个前向SpotLight替换人物主补点光**，不再扩大无方向的点光：Stage(-.35,2.10,+.45)朝(0,1.30,-1.75)，20,000lm，半径4.8m，inner45°／outer75°、无shadow，暖白(1,.91,.82)。对应本地−Z的单位ray(.147869,-.337986,-.929462)，Quat(-.172054,-.075274,0,.982207)。脸手包络最大离轴角26.0°；公开文档未明确角度是半角还是全角，因此只保守确认它在outer75°的半角37.5°内，不假称重建PICO角衰减曲线。聚光集中通量而非向4π发散，预计能给人物更有分量的前光；后墙仍在4.8m范围外。冷白刀补光可提高到12,000lm，IBL可控提高为指数4（16倍），其它环境灯保持不变。以上仅为下一窗口的候选，不是已经改动或已经生效；Root共享构建结束并解冻后再落源码／专项检查，以同机位实图判定。

### v4原生聚光已落盘并再次冻结

Root随后通知253 tests通过、`dcb753e4...`构建安装结束，明确解冻SceneLighting。本路已直接完成上述下一组值，**最终源码SHA `8243467b7b4e04fa82ff66eff208c212fb9b19d471e01060c4fe58f8c14d8d0e`**；独立SDK6.1.9编译通过、11项实际源码生命周期测试通过、5项灯位／数值／光锥检查通过。冻结后不再与Root共享构建同时写运行文件。SceneWeather、GLB、KTX、HomeStage均未改动。

| 原生项 | 精确最终参数 |
| --- | --- |
| face_key（替换原5200lm点灯） | `SpotLightComponent`；linear RGB(1,.91,.82)；**20,000 lumen**；attenuationRadius **4.8米**；innerAngle **45度**；outerAngle **75度**；castsShadowEnabled=false |
| face_key变换 | Stage(-.35,2.10,+.45)，目标(0,1.30,-1.75)，Quat(-.17205445,-.07527382,0,.98220727)；沿原生本地−Z发射 |
| blade_fill | 原点光位置(+1.15,1.65,+.25)、linear RGB(.72,.85,1)、半径4.2米不变，**12,000 lumen** |
| Stage IBL | 同一da33 KTX，intensityExponent **4，即2^4=16倍**；无新IBL资源或隐式替换 |
| 环境层 | 650lux月光、四灯笼位置／1500,1500,1100,1100lm、900lm侧后冷缘不变 |

原生灯数量保持有界：1方向光＋6点光＋1聚光，另加Root现有短暂contact point。新face_key替换旧face point，没有保留两条主补光路径；它随现有rig一并销毁，创建失败也清理新Entity。关闭／awaitRelease的状态机保持上一阶段已测合同。

强度依据是官方**lumen与lux不是同一量**：PointLight和SpotLight的intensity是总光通量lumen，DirectionalLight是照度lux，不能按参数数值比较亮度。理想全向点灯在3.112m正对面，5200lm只有约42.7lux（还未计角度、范围衰减）；聚光将通量集中到交战区。官方SpotLight示例给10,000lm、10m、15/30度；本轮使用更宽角度的20,000lm照脸手，未假设精确PICO锥角公式。证据：`/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/api-reference/com.pico.spatial.core.ecs.md` 的SpotLightComponent4540段及其lumen／米／度／本地−Z说明，已通过6.1.9真实公有类型编译。IBL指数2^x依据同文件StageEnvironmentLightingComponent4673段，Full Stage作用范围依据官方IBL指南。本轮没有把加载成功当作反射布局或可读性成功。

5项参数检查包含：原四灯位仍匹配06；六个点光＋一个spot与JSON逐项一致；spot四元数归一化且将本地−Z转到真实目标ray；脸手x±.65、y1.0–1.85、z−2.4到−1.1范围最大离轴26.0度，按更窄的outer半角37.5度仍在范围内；后墙Z间隔5.15m已超过主光4.8m cutoff；IBL指数4与源码一致。只证明参数／轴向／范围，没有假装完成端内亮度验收。

当前累计34项专项检查（4运动＋5参数＋7weather＋7IBL＋11生命周期）；source gate仍0 violation／0 advisory。Root可复用已有`attach`、`loadEnvironment`、`awaitRelease`和`isReleased`接线，无需添加新的调用点。下一张同机位真实图须看脸／手是否比暗门高一层、刃边是否清楚、近处皮肤是否过曝、白墙是否仍抢主体；v4未在设备上由本路观察，不能据数值宣布完成。

## Root组合审核与下一步

异步IBL、纹理失败可重试与任意nanoTime相位收口已接，旧HomeStage key/fill已替换为SceneLighting，GroundShadow和contactLight保留。Root已发布新雨夜IBL SHAda33c8cde84d6e2da04125760190d50c6b26521eedd0457c7b726c73d8ff0980及3天气GLB，owner统一加载/更新/关闭，构建与250项组合回归通过。实际KTX加载、脸部亮度、透明排序与雨雾遮挡仍待本轮PICO取图，不能把此处检查当原生lookdev已通过。运行源码继续冻结至Root给图。

## Root本轮组合审核与续派（2026-11-11）

审核：v3实际图教学完整，但脸、手、衣物与刃口仍偏暗，主体可读性未通过；awaitRelease已由Root接同builder继续创建。

下一步：在已查证原生灯单位/方向/影响范围后做下一组明显可见补光，避免只报coverage。根、旧IO、纹理释放须可重试。
