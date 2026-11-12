# 03 · 服装结构与装配精修

## 当前有效执行：原生APK资源限定（2026-11-13）

按用户最新纠偏：唯一产品是 **Kotlin＋PICO Spatial SDK 6.1.9 APK**，由Root在PICO Emulator验证，终端Space Pro／OS6。停止HTML／Web／Three.js游戏、浏览器试玩、网页材质光照与新HTML mock；现有文件保留，不维护、不删除他人工作。浏览器仅用于必要官方资料／账号服务，不能作为游戏验收。Root继续独占正式资源接入、共享构建、设备、Git及发布。

本路只交可进入现有APK的GLB／贴图／动作等原生资源及明确接入点。**当前pattern-first产物尚不能接入原生角色，本轮已停止求解、松弛及诊断渲染，没有导出guard态测试GLB冒充资产。**

- 已有真实2D源保留：`ArtSource/refinement/character/design/garment-pattern-first/pattern/pattern_v2.json`、同名SVG／NPZ／PNG，含前后身、交襟、前后袖片与腋片；机械源图在`render/images/pattern_2d_source.png`，不是3D结果。
- 衣形仍未完成：真实Cloth源到guard在F369未过，缝未闭合；另存静态构造及一次约束松弛也未收敛，且是guard态、未绑定。它们不是REST＋78骨的可用衣物GLB，未生成整体新衣clay／current-before图，不记为45分钟首件通过。
- 所有现有源／失败记录保留，模型和renderer均确认无运行进程。无实质可接入原生资源时停止，不因回报再造报告、页面、重复图或假资产；之后仅按明确原生任务接力。既有图像条件Tripo计划仍由Root保留待TLS网络，本路不接管CLI／付费。

以下旧衣片／物理／研究正文仅为既有证据，不覆盖当前原生限定；未过灰模和动态，不进入UV／bake。正式源／producer／library／app、Kotlin、设备、共享构建、Git、本机pico／网站仓库均未修改。

## 当前执行：二维衣片构型与原生角色候选

只推进已授权的`ArtSource/refinement/character/design/garment-pattern-first/`：从前后身、交襟和袖片构造肩袖垂落、渐收薄腕口，保当前脸手、腰裤与78骨。`pattern_v2.npz`是实际构造输入，必须随源码保留；bphys、逐帧求解和备份不是正式角色。

先交一件完整guard灰模及同机位当前人物对照；形体未被接受不进入UV/bake或覆盖正式库。当前尚无通过的整衣handoff，不宣称可装包。原Cloth首件失败且已结束，不继续R1/R2参数循环。停止HTML/Web、额外案例报告和重复渲染；Root统一原生接入、Emulator、Git及发布。

## 已结束的真实Cloth物理首件（2026-11-12）

Root已完成有界网络排查，现有出口与三个节点均未通过Tripo TLS，短期新源暂不可得。**图像条件Tripo方案保留待网络，不宣布取消；CLI／余额／付费仍由Root独占。** 为不让服装主目标空等，本轮另授权一种本机真实Cloth方法首件，不是R3参数袖筒。

范围：以现有`source-prep/upperbody_source_editable.blend`为高模目标，必要时用R2 REST衣片作物理求解笼。先核Blender4.5官方文档和本机4.5.15 RNA；一次固定Cloth物理方案，最多一个Blender、2线程。保UB-01交襟／薄腕口、当前脸手／腰裤和78骨。只交guard三分之四／侧面同机位图，不用规整环位移或正弦噪声冒称雕修，不下载／购买工具，不进入UV／bake。失败须给真实物理／输入结构原因，不换名做参数循环；正式源／producer／app／输入／Git／设备／构建不碰。

### 本轮实际结果：阶段结束，等待Root review

入口：`ArtSource/refinement/character/design/cloth-physical-first-2026-11-12/delivery_handoff.json`。已查官方4.5文档并实测RNA，实际运行一个Cloth modifier：R2作为求解笼，少量颈肩／腰pin、有限力loose sewing、重力及碰撞。10帧健康探针在F06停止，无参数重试；只为持久化缓存同参数重放，六帧点hash全部一致。live Cloth `.blend`、原生`.bphys`、逐帧NPZ和全部参数已留。

实际目视同一求解笼F01／F06的两角前后：腕边发生挤压，肩肘仍是大平筒，**未证明目标大形改善**。未向原高模传递失败笼，未完成高模雕修；不能把R2失败帧与原高模拼成成功前后。只有四张诊断图，均标guard-state／physics failed／no high-mesh transfer，不是最终绑定或动态通过。

失败归因限定为三点：①碰撞体来自骨域argmax＋incident面的保守手部保护域，含未确认／旧衣候选面，不是已逐面确认的裸体，848／860只是与该域的几何交叉，过宽碰撞体可能贡献失败；②R2输入有7–45mm袖根缝缺口及极短薄折返边，guard初态最短边约0.0357mm，相对1mm碰撞间距不相容，最差边由0.0451拉至3.406mm；③F06整体未爆飞，但局部严重应变和腕口挤压已触发固定健康门。此单次run未隔离各因素，**不能推论原高模或Cloth不可用**。

本轮不换方法／参数重试，不扩图、不做UV／bake或新下载。下一次若Root继续该路线，应先确认真实人体碰撞域、单层模拟材质与缝合／初态空间，再评价肩肘物理造型；这不是让继续加刚度／质量参数代替结构修复。Tripo新源实验仍待Root网络恢复后交源。

## 当前接力：图像条件新源的服装接收准备（2026-11-12）

Root本次已正式确认R2 **NOT_PASSED／STOPLOSS**，选择一次图像条件Tripo源实验，替代下方旧路线选择。本路已实际看 `ArtSource/bench/tripo-image-input-2026-11-12/front-tpose-v1.png` 与R2侧面／三分之四两组配套图。**本阶段准备结束，等待Root交付新源；不是3D造型通过。** 余额、CLI、dry-run、收费调用均由Root独占，本路没有调用Tripo。

原路线失败原因：v1在融合高模上改位移未建立衣片关系；R2换了拓扑却仍由规整参数面板主导，抹掉肩肘自然布量，交襟压盖弱，颈腕接口与旧衣移除未完成。更多面数、渲染或烘焙无法补足这些形体／层次错误。R1／R2及noR3停损保持冻结。

该图只作为衣服条件输入，三项造型收件标准固定为：

1. **交领：** 左外襟压右内襟，斜向穿戴者右腰连续收束，浅色内领窄露，边是薄布翻折。新源clay若仍融合浅浮雕、厚V条、镜像压盖或腰上横台阶即退回。
2. **肩肘：** 肩—肘—前臂连续但布量不均匀，保当前人体比例，可见斜向牵拉与肘区余量。拒绝R2式光滑大筒／硬壳与等距环褶；仅T姿不证明弯肘，后续实际guard／walk／overhead另验。
3. **腕口：** 袖布渐收、一次薄折返，深色腕围／皮约束克制，裸手清楚。拒绝厚白圈、双硬筒、袖口封死、手口空洞或旧硬圈可见叠层；不能把Hand原点当解剖腕界。

仅正面图不能证明侧背厚度、背领、腋后和举臂空间；图上阴影／织纹不等于几何。源到手先看关贴图／法线的clay，03只分离衣料，不采纳生成脸手；发型／头部由05提案、Root组合，双方不覆盖整人。

接收准备入口：`ArtSource/refinement/character/design/image-source-intake-2026-11-12/handoff.json`；完整但有界的分离／保护顺序见同目录`intake_plan.md`。当前接收体已实际核为材质整合raw `a4280be1…`、prepared `b3fbfe66…`、library／app `ac7dfbc6…`、binding `1b3e031d…`；旧b732／b03f不是当前基线。保当前p1…8头眼颈及p0实际裸手、52点颈界／83同位别名和78骨rest／IBM，并保07材质／切线整合。不能只保头部primitive就称保手。

新源到手后才读实际mesh／frame／skin并分衣料及争议面，只调整新衣，不改原头手骨架；重新确认原衣移除范围，旧9c33高模IDs、17157行及bary缓存均不得直接套新源。只交私有衣料部件及明确移除／保护证据，不返喂prepared context。**未收到实际新源，本轮不写抽象转换器、不造衣筒、不启Blender／UV／bake，也不接管Root的CLI或下载任务。**

## Root本轮灰模审核与R2续派（2026-11-12）

已实际看shape-v1/front_1p5m_before_after及当前对照。结论REQUEST_CHANGES，灰模关未过。三项：下外襟新增水平台阶；肩/肘/袖筒在整人1.5m差别太弱；袖缘仍是厚而方的翘片。不是缺更多渲染和烘焙，而是原拓扑位移不足以形成UB-01连续衣片。

现在授权R2，不再等待Root/12回执。保v1冻结，允许替换完整交领/上衣必要拓扑，不强保旧顶点ID，不沿原面继续毫米级位移。做真正连续衣片、独立内外襟与自然收束袖口；旧可见衣服需移除，不叠两层。可用现高模作贴合/解剖导向，但结构必须能从clay读到。头脸、裸手、腰带裤装、78骨rest保持。先给完整guard三分之四和侧面两张灰模；若大形仍弱，不批量出余图，不做UV/烘焙。两轮上限到后必须执行已有停损，不能开R3参数循环。正式资源仍由Root发布。

Root另派07在原基线几何上做材质隔离A/B，仅为分清石斑纹理的贡献，不是放行你的新几何或让你跳过灰模/动态关。你不改07责任目录。主控持续目标已恢复active，本次review已消除先前“无审核”的阻塞。

### R2已执行：阶段结束，按两轮上限停损

**阶段结束，等待协调Root review／停损后路线选择。**

当前入口：`ArtSource/refinement/character/design/upperbody-2026-11-12/handoff.json`；精简结论与具体后续来源在同目录 `review_r2_stoploss.md`。v1保持冻结，R2已实际新建内外襟、肩背、双袖和薄腕折返拓扑，交新REST部件及可编辑`.blend`，没有沿v1做毫米点位迭代。

本路已实际看完整guard 1.5m两对：`preview/r2/comparisons/three_quarter_1p5m_clay_before_after.png`、`side_1p5m_clay_before_after.png`。左current原衣、右R2，同机位；只交4张配套图及2张拼图，不扩其余视图。

本路自审NOT_PASSED，协调Root／12尚待收件。只交三条：①抬臂袖仍是光滑大筒，缺少肩肘受力褶；②交襟压盖层次弱，腰带上方仍有横向堆叠；③颈肩／腕口接口未完成，右腕旧硬圈也未证全清。定向／保护检查通过不构成灰模通过，借形变预览不构成正式绑定或动态通过。

已执行`STOPLOSS / noR3`，不再程序调参、扩图、UV、烘焙或发布。交Root选择的具体路线：优先用既有`source-prep/upperbody_source_editable.blend`做实际Mask／Face Sets／Cloth Sculpt与衣片切分；备选为britdawgmasterfunk的`Clothing And Character Kit 1.0`衣片源，真实URL、许可冲突、未下载／费用未核边界已列报告，不作为已验证可直接接入底模。本轮未下载／购买新资产，无新增Tripo收费调用。正式资源、07目录、Kotlin、构建、设备、Git未改。等待协调Root对停损后路线作review，不把此状态说成仍缺v1审核。

## Root review and next production contract (2026-11-12)

用户本次要求继续。Root已实际看图收件：12研究完成；05发髻变光滑蛋形，拒绝；03袖口像深色短筒加浅色粗壳且极限姿态穿插，拒绝；06木窗同光clay有真实进深收益，只接受结构方向，尚未原生放行。本轮正式游戏没有获得有效的人物升级。

下一节点是一个完整刀客上半身。比较三路：旧小补丁收益已不足；反复整人重生成会重置身份/绑定且无质量保证；选择现有Tripo高模、固定身份和明确参考下的完整部件造型。最大风险是缺少造型输入时再把发髻做成球、袖子做成管，所以先形体、再动态、再材质、最后原生。

唯一仓库 /Users/yupeng/projects/personal/pico-wuxia-arena，Kotlin+PICO Spatial SDK6.1.9，Space Pro/OS6。正式b03f人物与8b1098场景仍为基线。你不独占仓库，不回滚他人，不复制仓库，不改pico/BrickerP.github.io。Root独占正式producer/manifest/library/app、Kotlin、共享构建、设备和Git。本轮具体制作继续，不等同恢复24小时自动监控。只改本路范围，研究已交部分不反复写长报告。

Root审核：拒绝method-review-2026-11-12袖口v2。已看1.5m前后及极限clay：新硬筒/浅色壳破坏服装连续性，腕口台阶、受力褶和穿插仍未解决。

1. 改做连贯的交领-双肩-双袖-腕口衣片系统；保脸、手、腰带、裤装与78骨rest。先按12造型板固定衣片关系。美术定向：黛青/炭灰布面短打、窄内领、棕皮与古铜分工；左襟压右襟并在穿戴者右侧收束。整体灰白随机花斑不作为风化目标。
2. 从已有高模复用可用轮廓与受力褶，必要处按衣片重建肩肘空间/翻折，不再径向管圈收缩、套白筒，不为保旧顶点ID保坏结构。新旧衣服不能叠为可见两层。
3. 第一关只做完整上半身大形：1.5m正/侧/三分之四/剪影，0.8m补构造；可借现权重做guard预览，但不冒充动态通过。灰模未过，不进入整衣低模/UV/烘焙，不先做36张PBR。
4. 灰模通过后才做受控低模和权重；先看实际idle/walk/overhead极限的肩肘/领口/腕口。动态未过返回造型与层间空间，不能进烘焙。最后整衣一次重烘/材质，移除无原因白斑，保有原因磨损。
5. 交Root可组合部件、原上衣移除区域和骨架映射，不返喂带头/DAO/动画的prepared context。正式整人源与producer由Root更新。

停损：参考明确后两轮仍像硬壳/硬筒或整人1.5m无收益，停止程序参数修形，提出具体可授权衣片底模或原高模直接雕修路线。保Tripo身份，不以Quaternius替敌人。

### 03首件回填：可编辑源场景（非新造型）

- 已交 `ArtSource/refinement/character/design/upperbody-2026-11-12/source-prep/handoff.json`，包含 `upperbody_source_editable.blend`、源面映射／衣片工作选择集和 `original_high_source_fact_front_clay.png`。这是原高模事实图，仍为原高模旧头，**不是当前新头组合／新造型候选**。
- 16个衣片／保护工作组与真实Sculpt Mask已写入；脸、手、腰带裤装及争议面保持保护，未造型、未减面、未UV、未烘焙。所有high IDs仅对应high_pbr `9c336b4a…`，顺序不同的high_geometry不能共用这些IDs；这些组不是已确认的物理衣缝。
- 当前头手组合的未雕修guard基线已交 `upperbody-2026-11-12/preview/handoff.json`，DAO仅在衣物审核中隐藏。该初始基线后来扩展衣料工作选面，因此第一轮实际比较只用下述配套before，不混用旧图。采用借用surface deformation，未建立最终绑定；旧碎裂预览及116°刀尖定框已标失效。

### 03第一轮整衣灰模：阶段结束，等待Root／12 review

唯一当前入口为 `ArtSource/refinement/character/design/upperbody-2026-11-12/handoff.json`，精简review在同目录`review_v1.md`。用户已明确恢复03目标active，当前按灰模关等待对应review后继续；不进入动态、低模、UV或烘焙，不以active越过Root发布边界。

实际雕修源与可编辑三Shape Keys见 `shape-v1/handoff.json`。当前头手guard七视图前后已齐：1.5m正／侧／背／三分之四／剪影与0.8m两图。首对拼图在 `preview/comparisons/shape-v1/front_1p5m_before_after.png`，配套before为 `guard_ed7176ff_garment/`、after为`guard_adde1d4a_garment/`。机位和衣料选面一致，DAO只为衣物审核隐藏；这是借形变灰模预览，不是最终绑定／动态通过。

本路自审不放行，只交三条判断：①下外襟新增横向台阶；②肩肘在整人视距改善不足；③袖缘仍呈方形厚翘片，未达UB-01的软收束。

仅上衣REST部件、原上衣移除映射、78骨palette／IBM来源和借形变face／bary已交 `preview/components/handoff.json`；没有返喂带头／DAO／动画的prepared context。当前原手4193个incident三角删0、头手颈p1..8实际完整，source同位alias无位移差。1403个未确认衣料的受改动邻接面前后均排除，具体IDs随包；接口闭合、正式权重与最终低模尚未完成，不能发布。本轮未收费、未改正式资源／Kotlin／构建／设备／Git。

---

> Prior delivery evidence below; execute only the current contract above.

## 最新用户目标与执行队列

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你集中做整段领襟、交领层次、真实袖口／护腕、布／皮分工、腰带铜扣、衣摆开衩和服装局部重拓，要求正常胸部／全身视距有可见变化。

06主导整套雨后庭院与建筑，07主导照明，05主导头脸与发束。你已经产出的environment候选和测量直接写清路径交06，环境后续从你的执行队列移交。继续完整领边折返带与铜扣，并接02尚未完成的12mm袖口结构。保持原78骨rest、手部和动作来源可追溯，新拓扑给原面／顶点／UV／权重映射。与05约定颈部边界，不整只覆盖对方成果。

## 上轮袖口动态阶段（2026-11-11，冻结）

**阶段结束，等待Root review。袖口本阶段NOT_PASSED，未发布正式资产。** Root已接受领襟v3材质方向，袖口完成真实动态核查、修复试验和正常视距对照，仍有新增／恶化穿插。唯一交接入口为 `ArtSource/refinement/character/design/clothing_handoff.json`；本轮完整结论见本文末“袖口动态返修阶段交付”。本轮Tripo费用0，保留免费静态GLB，不升级Web订阅。收到对应review后继续下一轮。

### 本轮动态核查与结构返修

正式动作参照为 `ArtSource/tripo-warrior/library/base_prepared_png.glb`，SHA `b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09`。已从实际EnemyAnimator消费入口核实guard取idle首帧，移动取walk；本轮完整采样idle、walk、attack_overhead／left／right，包含全部祖先。原35308属性、78骨rest／IBM与候选前缀逐值核对。

`cuff-structure/motion-stage3/renders/first_guard/`及`renders/critical_diagnosis_v2/`共六张0.8m同机位PBR图为真实正式曲线的离线证据。关键攻击帧的全部78骨形变矩阵及旧手ROI／新增袖口实际蒙皮点已与独立CPU核对，最大表面误差约0.000841mm；渲染未改材质slot。该证据不代替设备验收。

v2动态审核未通过。source face1130的原样裁片在left@0.4s与face2728产生原源没有的18.953mm交线；原因是POSITION／WEIGHTS分别插值后再蒙皮不等于原面动态表面的重心插值。完整原面候选消除了该机制，但全594帧仍发现径向拟合造成的新增／恶化交叉；该候选也未通过。停止继续全局收径／权重参数循环，冻结失败试验，等待Root review确定下一轮腕筒与外袖口的重建范围。

## 已冻结首批服装交付索引（2026-11-11）

首个闭合领襟GLB于13:29、首对0.8m图于13:41交付，处于本轮45分钟首实物目标内。该首交阶段结束，可供Root review；已授权的袖口、扣具和衣料返修继续。

| 部件 | 当前可组合产物 | 真实结果与限制 |
| --- | --- | --- |
| 连续领襟 | `collar-shell/body_with_collar_v2.glb`，SHA `003f96c6975455101aa8e18be9dd5822f68e6425fd0a36c67889dc613275c1ff`；独立件 `collar_component_v2.glb`，SHA `4faf34befed5a5547b8f19b4007943ac2c7fca6481b1d27316820e2c83cc743f` | 43mm宽、实体前后配对约4mm、2mm圆折返，旧面删除228个，新增4544面；5mm覆盖接缝未焊接。连续灰布与边缘在0.8m／1.5m可读，带端及较素净材质仍需Root艺术取舍 |
| 外衣PBR | `cloth-surface/material_patch.json`；首版context SHA `dcf1134ccb05aa83fd2e11fa3bc19c301bd1e550332a8cd76ab7538946c0a79f` | 实改4K颜色与MR像素，普通视距大白斑减少，候选偏浅灰／平滑，边界有白残留。旧normal保留；强UV采样保护的独立v2正在补齐，当前首版不签全非衣料采样不变 |
| 裸腕结构 | `cuff-structure/v2/cuff_opening_v2.glb`，SHA `f46ed9686f0d67cba34b89be1b654669dc7de68ec26d684e8706864c6ba41a3e` | 实删412原面并补肤／重剖／封袖边，60684面。相对原可见肤布界的间隔左11.30–12.64mm、右10.61–12.59mm；解剖腕纹未确认，接缝硬脊与动态尚待收口，literal_12mm仍为false |
| 古铜扣装配 | `buckle-assembly/body_buckle_assembly_v2.glb`，SHA `32a3f3c4667be139b6b5efa27ca9711ebf9c4d0add80695874f769dfc1161fee` | 旧面删除473个，7个闭合零件，硬件用Waist21而非腿部Hip／Pelvis。正常PBR显示浅棕背衬补片感、环被埋平及残金面27834／26896，视觉未通过；独立v3返修中 |

### 有效评审图

- 领襟有效图为 `collar-shell/renders/valid_v2/`，0.8m正视／1.5m斜视PBR。`structure_v1/`保留同几何clay与抬臂／转头证据。`invalid_material_slot/`为失效验图，不用于源材质判断。
- 外衣真实图为 `cloth-surface/renders/` 的1.5m衣物及3m全身四图；前后同灯、同机位，材质slot保持。
- 裸腕实际PBR在 `cuff-structure/v2/renders_pbr/`，左右0.8m前后四图。CPU图明确仅作几何诊断。
- 铜扣实图及射线定位在 `buckle-assembly/renders/`，`visual_review.json`保留未通过结论。

验图工具曾使用materials.clear()导致新增襟面slot归零，误采身体atlas。现已改为逐slot替换／恢复，导入到渲染后逐face索引全量核对，实际body／cloth为59778／4544面，错色已消失。此修复没有改变源v2法线参数。

### 来源、保护与接入

共同raw SHA为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。原35308顶点ID前缀、旧UV／权重、78骨rest／IBM及手部作为组合基准。各context GLB用于本部件审图，Root按source face／vertex映射和材质补丁合成。

具体唯一producer与SDK路径见 `coordination/sdk_integration_03.md`。当前producer尚无服装补丁hook；候选逻辑在append_animations之前接入，保持原BIN前缀，角色和attack profiles由Root同次发布。领襟13632与铜扣17964新增角点合并原35308点已达66904，合成必须采用各primitive局部索引或升级UINT，避免16位截断。正式producer、manifest、library／app与Git由Root维护。

环境来源／候选／地面26mm差异已交 `coordination/environment_to_06.md`，后续环境归06。`neck_boundary_05.json`是待05／Root确认的颈界提案；已给暗衣料争议面和保护集合，不能只按Head／Neck正权重认定皮肤。当前领襟最大Y约1.4652m，未进入Y>1.48m保护域。本轮Tripo扣费0。


## 已冻结的领襟与袖口v2首批交付

**阶段结束，交Root review。** 唯一可组合入口为 `ArtSource/refinement/character/design/clothing_handoff.json`，固定source为raw SHA `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。已冻结v2首批身份，同时明确列出Root返修后的独立v3材质候选。本轮Tripo费用0。

### 源面与新增结构

- 领襟删除228个原面，独立component的mesh0／primitive0为新增4544面、13632属性角点。43mm宽、前后约4mm实厚、2mm圆折返，邻面表面凸高另为3.42–7.92mm。5mm覆盖接缝未焊接；原35308顶点、UV、skin、78骨rest与IBM保持。几何／skin来源在 `mapping_v1.json`，v2／v3新渲染UV与材质分别独立记录。
- 袖口删除412个原面，新增使用candidate的mesh1全部三primitive，依次为345个保留原材质的裁片、517个linear COLOR_0肤面、228个袖边壁。所有新点有原face、bary、UV及最多4骨插值映射。旧body保留的59594面不作为新增geometry重复追加。皮肤／袖边材质发布时重命名为tripo_前缀，具体overrides在入口中。
- 两组删除面交集为0。已只读对05的52点颈桥快照核对，collar／cuff删除面与52点incident faces及head clipped faces的交集均为0；旧52点原属性前缀保持。快照来源和SHA已写入口，05重启后的最新版本仍由05／Root最终确认。

### 新v3实际材质回报

Root指出v2大段均匀灰带后，几何底稿和旧审核图保持冻结。独立v3采用512×2048唯一strip、约5.305 texel/mm，从662个原衣料face密集重投影，保留连续衣料细纹／结构明暗及细边缝；旧body图、UV和所有geometry／skin保持。

v3 body SHA为 `1db4dd5d0856487f53a0f88af00acb1db095dff70bad5f1b802b29ad50ab0150`，component SHA为 `22dc6ad12459ced779fb4e4d648bfce4fab77ceb7c3f204ba80c7ec78ae50b02`。可组合补丁是 `collar-shell/v3/composable_uv_material_patch_v3.json`，仅改接收体的新增collar UV／材质，保留Root外部头、手和颈桥。

同v2机位的0.8m正视／1.5m斜视实际PNG在 `collar-shell/v3/renders/first_pair/`。原均匀灰带已恢复衣料变化，下段不再整片常值；上颈仍较平整，针脚主要读作细缝，43mm宽带和两端封盖衔接继续作为Root造型review项，不宣称整体美术已通过。

### 其他部件限制与后续

袖口相对原可见肤布边代理的间隔为左11.30–12.64mm、右10.61–12.59mm。实际0.8mPBR四图已交，解剖腕纹未定、接缝硬脊与guard／walk动态仍未签，literal_12mm保持false。Root可按当前可见变化单独选择返修范围。

外衣去白斑的实际PBR1.5m／3m对照已交，强采样保护v2在 `cloth-surface/v2/`，所有非coat真实采样保护及重建验证通过，后续按材质补丁组合。铜扣装配v2因浅色大背衬及旧金弧未过，独立v3已修侧皮曲面、正面环深度与两面烘焙金残影，仍待同机位首对，不能以闭合／删除面数代替视觉通过。

正式组合接点见 `coordination/sdk_integration_03.md`。public producer／manifest／library／app／Git继续由Root维护。06的环境交接及05的颈界资料已放coordination目录，本会话后续按已授权扣具与衣料队列继续，冻结本批身份不覆盖。


## 上一轮成果与Root review

主角源为Tripo-v3.1详细几何、v3.5 extreme PBR、60k convert、78骨与原生slash，上一轮实耗175credits。最终已发布body为60,006三角、3张4K图。面数与贴图提供了基础，人物身份、衣物结构、面部与手部细节的美术目标仍需明确。

用户指定[Kensei参考文章](https://x.com/0xKense1/status/2118717647357395170)。原帖的三视图、分件、定向蒙皮和逐姿态检查值得转化为当前制作工序。其风格化服饰与本项目中式写实目标分别评审，源权重规则按VR手指需求重写。

## 文件所有权

负责 ArtSource/refinement/character/design/ 的服装设计／领襟／扣具候选，以及接收02袖口数据后的独立服装补丁与本文件。environment旧产物只交接，之后由06负责环境新方向。

## 本轮任务

1. 用现有raw rig或body-only源生成正、右、背三个正交事实基线，统一身高、尺度、脚底、空手、灰背景和中性光，附原模型SHA。
2. 给出一版明确的设计修订板，保持成年真实人体比例、交领束带、中式刀客主题。具体到脸部形体、领口／袖口厚度、衣摆开衩、护腕、布／皮／金属分工及磨损位置。
3. 设计目标图与现有模型基线清楚标记。可按imagegen技能制作原创设计母版，先查看本地参考并保持三视图一致；禁止把更漂亮的设计图当作已完成3D资产。
4. 输出能在现有模型上局部修复的项目与确需Tripo换源的项目，每项给可见问题、目标和建议处理方式。
5. 确需换源时准备已安装tripo-cli的multiview或局部处理dry-run，明确ov、tripo-v3.1与真实参数。本阶段不正式提交收费生成，Root看设计板后直接下达制作步骤，不向用户索要重复批准。

## 审核产物

同尺度正侧背基线、一版设计修订板、3至5个最高优先级部位及目标近景、输入一致性检查、必要的CLI dry-run计划。避免同阶段扩成多角色或新场景。

## 下游

本轮01／02／04均可在当前固定模型上独立推进，不因设计母版等待。Root以设计板衡量现有模型修复效果，再决定换源范围。账号密钥留在本机标准配置，正式生成沿既有CLI和同一task_id恢复。

## 共同执行约束

唯一工作仓库为 /Users/yupeng/projects/personal/pico-wuxia-arena。当前模型基线为main的cc12bf1，base.glb SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641。运行栈为Kotlin + PICO Spatial SDK6.1.9，终端Space Pro／OS6。

其他会话正在同一仓库并行。各自只修改责任范围，保留其他人的编辑。Git提交、分支、合入、共享构建、设备操作、实际截图与正式模型发布由Root统一负责。候选输出留在各自目录，library、app角色与公共manifest由Root发布。

本轮允许离线资产生成、渲染及专项制作检查。游戏整局自测继续后置。30分钟内交付首阶段实物，写明“阶段结束”、输入SHA、文件、效果、剩余问题与下一步建议后结束当前回合。遇到阻塞先交已做出的部分并写明具体阻塞，继续能独立完成的工作。用当前模型和已安装依赖推进，不为等审批或等待其他线程维持空转。

## 阶段回报

**阶段结束，等待review。本轮源模型身份保持不变，Tripo实际扣费0、上传0、任务提交0。**

### 输入与真实基线

指定base SHA为 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`。实际空手body SHA为 `65c0702e348627c539b1e33d7f95e044a037e22caf851d0a93a085860525ae55`，60,006三角、35,308顶点、78骨。身体primitive的全部属性、indices、材质图像和skin身份与指定base一致，DAO分件未加入事实图。

- `ArtSource/refinement/character/design/baseline/front_right_back.png` 是正／角色右／背的3D事实基线，单图分别为 `front.png`、`right.png`、`back.png`。
- 三图统一1.78米、脚底0、正交相机、空手REST、灰背景与中性白光。角色右侧按R_Hand核对。脸、领、袖口、衣摆、手的实际近景在同目录。
- `baseline/provenance.json` 记录源SHA、相机、展示变换及身体身份比较，`render_baseline.py` 可复建。

### 二维设计产物与局部目标

- `design/concept/turnaround_v1.png` 为原创正／右／背设计母版，`design/concept/detail_board_v1.png` 为五部位修订板。二者使用内置imagegen生成并标注2D DESIGN TARGET，提示原文保留在 `design/prompts/`。
- 五项优先目标为成年刀客面部、交领／袖口、手／护腕、衣摆／挂带、材质／接触磨损。具体问题、目标与局部修复路径在 `design/design_targets.md`。
- 目前五项均有现模型局部修复基础。整人换源的启用条件为完整解剖缺失、身份需整体换头，或衣物体积无法局部分离。动作穿插继续由01／02独立检查。
- 尺寸是设计提案。当前统一侧开衩160mm、袖口退腕12mm、折边总厚4mm；全身母版的实际长度比例与护腕表达仍需同步。扣具现图保留针扣，与暗铜板／环扣的文字目标尚未一致。

### 一致性与预检

三张设计输入在 `design/concept/views/`，均为768²、同头脚线；从单一母版原像素拆分，无独立缩放，去除了标题和边框。`manifest.json` 记录裁窗及源SHA。手部近景给出五指目标，正交侧视的自然叠遮仍需后续3D逐指复核。

`design/cli/multiview_dry_run.json` 已通过，归一化模型为 `v3.1-20260211`，路由 `/v3/generation/multiview-to-model`，真实view键为front／back／right。参数显式detailed、smart_low_poly=false，client为codex、region为ov。CLI估价50credits，仅为生成步骤，本轮没有实际扣费。

`design/design_review.json` 明确 `generation_ready=false`。CLI仅验证文件与参数，视觉母版还需Root确认护腕、扣具、衣摆比例及面部身份。后续由Root优先下达局部修复，确需换源时再选输入与处理范围。

### 验证与时限

事实图源身份、错误SHA拒绝、设计裁图像素一致性、CLI视图映射、脚本语法与JSON均已检查。两套图分别标明事实基线和二维目标。制图及一致性收尾超过30分钟交付目标，未把设计图标为已完成3D改造。

## Root首阶段review与续派

已查看三视图和局部板，接受成年面部、真实布纹及有因果磨损方向。阶段2统一古铜环扣／带钩、窄布缠腕加薄皮固定带、袖口退腕12mm，并以现有事实基线锁定正侧背衣摆长度。侧开衩160mm与4mm折边的文字、图示一致后再次审读。

## 阶段2回报

**阶段结束，等待review。Tripo实际扣费0、任务0，raw模型保持输入身份。**

- 统一板为 `ArtSource/refinement/character/design/concept/unified_board_v2_final.png`。全身正／右／背与局部RING／WRIST／HEM同板，已采用开口古铜圆环和背面暗钩、窄布缠腕加单条薄旧皮固定带。错误悬空12mm箭头已移除，退腕12mm标注仅在腕部局部图保留。
- 原面部身份按窄长成年脸、眉眼、直鼻、耳位及顶髻关系目检保持。imagegen对局部织纹有重绘，材质制作继续沿Root已接受的真实布纹方向。
- 事实前中心腰带下缘到主布下缘为362.6±4.6mm，源顶点确认主布Z0.645595m。本轮选择此前中心为共同锚点，板上取约363mm。原背上折边高32.1mm、背下层低89.5mm，已明确列出差异。
- `design/measurements/hem_measurements.json`、锚图和 `measure_hem.py` 留存测量定义与误差。`design/stage2_alignment.md` 给出扣具、腕层、衣摆、材质的局部3D修复优先顺序，160mm侧衩与4mm折边由实作时按坐标验收。
- `design/stage2_review.json` 记录最终图SHA、基准、视觉检查及限制。当前generation_ready=false，v1 views／dry-run仅属上阶段，后续若需v2输入应重新准备。
- 本轮图像局部编辑与标注收尾超过10–15分钟目标。产物已收束，本会话结束当前阶段，供Root直接review并安排局部建模。

## 当前阶段3执行项

责任目录为character/design/collar-refinement。从raw body-only事实基线量领口／前襟现有厚度，针对4mm目标做一个真实局部GLB改进，优先保原拓扑／顶点ID／UV／权重，仅局部位置和法线变化，避开02左腋及手部。交可复建脚本、vertex deltas、同机位素模／PBR正侧图及转头／抬臂检查。设计图与实际GLB分别标识；若Root在集成，可准备古铜环扣的独立可尺量几何候选。

## Root阶段3可见review与阶段4续派

Root已查看rest_overlap_detail的前后PBR近景及geometry_measurement。18个位置顶点的小片凸脊改动可作为制作方法样例，4mm当前指邻面基准的凸起高度，尚未证明布料实体厚度。整条前襟的锯齿状轮廓、表面小尖角与内外襟交叠仍明显，当前不作为整条领口精修完成验收。

先收口阶段3真实产物与专项检查，随后在collar-refinement/stage4针对实际可见的整段前襟折边做连续轮廓修整。沿可见折边建立有原face／vertex ID的连续路径，消除锯齿和尖角，让领边有一致的布料折返形体。范围以实际图像问题为准，允许扩到完整相关前襟，避免继续只抬高一个小凸点。优先同拓扑位置／法线修整。若源融合网格无法形成折返，可明确局部重拓扑并提供原面和顶点映射、原UV／weights插值与接缝处理。原78骨、rest／IBM、手部及02袖口区域保持。

交真正raw body-only候选、可组合delta或拓扑补丁，以及同灯正／斜侧PBR与素模前后图。必须让整体领边改善在胸部正常取景中可见，细节放大另附。转头和抬臂专项制作检查继续，实际厚度与表面凸起分别量测。Root负责与02袖口、04材质组合，源文件不覆盖。30分钟先交路径与第一版轮廓实物。

其后可独立制作已确定的古铜环扣／暗钩独立几何并按腰带装配尺寸留候选，无需等Root答复。公共producer、manifest、library/app、Git、共享构建与设备由Root独占，保持其他会话编辑。

## 阶段3回报

**阶段结束，等待review。真实GLB已冻结，Tripo扣费0。**

- 实物为 `ArtSource/refinement/character/design/collar-refinement/candidate_body.glb`，SHA为 `7d7a8d5c3bd813351cadf8cf79780b7b2a100df336819266ab9e96587df312bc`。来源raw rig SHA为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。
- 大V领跨越内外襟，本轮保拓扑最小方案只改善一段约48mm长、14mm宽的外襟表面起伏。固定邻面拟合基准下，crest由0.9648mm到3.9967mm，拟合RMS为0.2587mm。该指标为单表面relief，独立双层shell厚度尚未建立。
- 18个POSITION及36个邻接NORMAL改变，最大规范位移3.5961mm。原60,006三角、35,308顶点、78骨、vertex ID、UV、权重、索引、rest、逆绑定及贴图保持，其他BIN字节一致；UV拆点同位移动。43个相关三角无塌陷或翻面，最小面积比0.6804、最大面法线转角19.05度。区域位于中央前襟，避开左腋与手部。
- `prepare_collar.py` 可复建，`vertex_delta.json` 给逐顶点raw／规范位移，`geometry_measurement.json` 保存截面与平面数据。重建SHA一致，错误source SHA拒绝测试及独立二进制复核通过。
- `renders/` 交48张PBR／clay正、严格侧及斜侧前后对照，包含REST、前伸60度、转头正负45度；`renders/detail/` 另交4张8cm局部近景。每组同相机、尺度与姿态，源骨架和skin先行核对。`comparison_detail_clay.png`／`comparison_detail_pbr.png` 左源右候选，保持实际渲染像素。
- 总览变化较细，局部可辨起伏改变。原source前伸姿态的肩胸折陷前后均存在，继续交01／02复验。当前只交单处最小候选，整圈领襟及实体壳厚未完成。
- 首个GLB约21:18落盘，处于30分钟首实物目标内，完整对照与独立复核随后完成。`stage3_review.json` 记录冻结身份与限制，下一步由Root审图并将vertex delta接入唯一producer，正式source／library／app发布归Root。

## 阶段4领襟分支收口

**阶段结束，结果为blocked_visual_target。**

实际领边已追踪71个源face截面点、19组原顶点连接，覆盖约363mm。同拓扑v1／v2保持原数据，但正常胸部PBR改善不足。局部自适应细分v3／v3b保留35,308旧ID前缀，新增3,969个原face重心映射点，39,277顶点／67,686三角，替换773个原面。共享边与UV同位拆点同步、新UV和最多4骨权重插值、78骨／IBM／贴图及4项重复测试均通过。

最终技术分支为 `design/collar-refinement/stage4/retopo/candidate_v3b.glb`，SHA `6dae6360a1ecf7463ad439dd16189da4cf8e285315aa59de1b6be9d5093caa5d`。旧领边实际位移最高约0.282mm，正常胸部8图仍无明确整体PBR改善，因此不作为整段领襟精修通过。各版冻结，停止小参数试错。实图和判定在 `retopo/renders_v3b/visual_review.json`，技术证据在 `retopo/validation_v3b.json` 与 `test_retopo.py`。Root可据此另定折返带结构重建与材质组合方案。

## 古铜环扣独立实物

**阶段结束，尺寸与几何专项通过，待Root装配review。** `design/buckle-candidate/buckle.glb` SHA为 `cc3aa1264736c273e59e30ee5e298fc793f2ad7bf82bb72acabf3690a6d85360`。外径30mm／内径22mm／圆截面4mm，后置J形暗钩含0.30mm真倒角和1mm轴向间隙，共3468三角、2个闭合solid，深古铜metallic1／roughness0.45。中心253条射线检查通孔，重新导入尺寸和拓扑通过。

真实前侧背及暗钩图在 `buckle-candidate/renders/`。源腰带高86.48±2.81mm，旧方扣仍需先移除，建议装配中心规范坐标[0,1.052539,0.168722]m来自曲面拟合外推，需装配复核。皮耳、细微锈色、绑骨和角色接入留待后续，不能直接把环扣叠在旧方扣上。

## 环境首套实物（2026-11-11）

**阶段结束，等待review。实际离线PBR可见改善通过内部专项，等待Root审图与端内验证。** 本轮Tripo费用0。

来源为当前 `ArtSource/tavern/tavern_slice.glb`，SHA `af3adf8b15bb5aa6f34a9a5240e18bc2534bc977db4a05089a0c3a1ee1bbdc69`；前庭为同Paving平移复用。已查看Root真实端内 `artifacts/combat-polish/first-build-ready.png`，围绕大黑缝石板、木纹尺度和门口层次制作。原producer／source／app资产保持各自发布权，由Root统一接入。

- 铺地为 `ArtSource/refinement/environment/paving/paving_candidate.glb`，SHA `bc9a7d0e4a5dc463ca2a73f4936f253e56efc6a87363c74c14b0a95f9e75d3fb`。137块约350×280mm错缝石板，10mm浅缝，填缝低5.35–7.94mm，2.4–3.6mm几何倒角，共6092三角。原Paving_Root／Paving名称、坐标、整体bounds保持；中央Y0.02535–0.02794m，两侧排水坡2%最大12mm，低侧与窄缝湿润／积水有明确分区。
- 石材三通道沿同一CC0源166px净石面裁窗对齐，去除照片自带5×5假缝；UV按米制投影，侧面UV已修。独立重新导入核925条接地射线，导出高度误差0。`paving_measurements.json`、`groundheight_mapping.json` 与 `validation.json` 给出来源、尺寸和高度。
- 门口最终为 `environment/entry/structure_entry_v2.glb`，SHA `4f0b4ce49034ba938a574cddd377c3454e26c449d5eaefe404116641c8dfcfa7`，4392三角，只含Structure_Root与Structure，整体bounds同源。门套分6层石块／6mm真缝，门槛三块及6–9mm倒角／2mm鼻口磨耗，柱脚分层，木构顺长轴米制UV，湿润限底缘。14处退入砂浆床封住贯穿空缝，4项测试通过，见 `entry_changes_v2.json`。
- 实际对照在 `environment/review/before/` 与 `environment/review/after_v2/`，玩家、近地斜视、门槛柱脚机位固定；离线同灯PBR不标成SDK截图。两段铺地继承原前庭+3.02m平移，BBox拼接间隙0，活动前庭仅一个Paving，无重复门楼。
- 当前明确改善是细缝路面与门口层次。雨后湿润的端内反射、接地、瓦檐与阴雨远景层次仍需后续制作／Root配光验证。原有大UI与战斗反馈由Root维护。本套首候选超过最初30分钟目标，源图和最终专项检查已如实交付。

### 环境最终冻结补充

最终唯一入口为 `ArtSource/refinement/environment/environment_handoff.json`。铺地bc9a与门口v2的4f0b来源已统一，`review/render_evidence.json`／`assembly_validation.json` 均指向此入口。before与after_v2各三图，玩家／近地／门槛柱脚的相机和光照逐组相同。旧v1只作历史，遮挡的旧局部图已剔除。

独立快审确认所有铺地UV三角非退化、水片向上；门套14个砂浆床未侵入±0.925m净门洞、过梁净空及0.16m门槛。来源图像复用，门口4项测试通过。当前候选已冻结，Root继续正式producer／app摆放、接地、配光与设备验收；瓦檐、灯笼和阴雨远景属于后续环境模块。

# 新12路服装制作阶段

**新分工执行中。** 03集中连续领襟折返带、12mm袖口结构与古铜扣具，环境旧产物交06、头脸由05制作。本轮45分钟先交服装可组合实物与正常视距对照。

06接收既有 `ArtSource/refinement/environment/environment_handoff.json`，三组同机位图为 `review/before/` 与 `review/after_v2/`。铺地bc9a与门口v2的4f0b均已冻结，来源、尺寸和限制详见 `design/coordination/environment_to_06.md`。后续环境方向归06。

05负责头脸、皮肤与发束；03负责衣料前襟。共同raw SHA为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。03先避开规范Y>1.48m及头脸皮肤，领边实际路径至Y1.46m。源面与顶点保护范围见 `design/coordination/neck_boundary_05.json`，此为供05／Root确认的边界提案。

本轮结构方案在 `design/collar-shell/`，制作可尺量闭合扁折返带，实体厚度与邻面凸高分别记录。原面删除、覆盖接缝、新顶点UV／权重插值均提供映射。旧单表面relief和细分分支保留未过视觉门槛的结论。

02旧袖口数据只读接收，新的12mm结构候选在 `design/cuff-structure/`。退腕距离按可见皮肤／布边界核对，Hand骨原点不足以证明腕纹位置。每路仅运行一个Blender进程，构建与渲染串行排程。公共producer、正式模型与发布继续由Root维护。

## Root本轮组合审核与续派（2026-11-11）

审核：Root已实际对比collar-shell valid_v2的0.8m前后及1.5m斜视。连续带形体可见，但呈均匀灰带、织物细节与折返层次不足，整体美术暂不通过。cuff v2有实际退移，但报告仍注明guard_walk_pose_validation=not run，不能凭静态12mm放行动态袖口。

下一步：保留领襟几何底稿，修有效UV／纹素密度、纤维方向、带缘缝线及两端过渡；袖口补guard与walk的真实蒙皮检查后再给组合入口。05颈桥边界保持，正式资源仍未替换。


## Root领襟v3目视审核（2026-11-11）

Root实际查看first_pair/after_v3_pbr_rest_near_front_0p8m.png，领带已从均匀灰带改善为与衣料匹配的细纹折边，接受v3材质/UV方向进入后续组合。尚未发布正式角色；袖口动态穿插、腕纹参照和扣具装配仍须本路修正。下一轮不得用v2灰带或纯静态12mm报告代替本项动态验收。

## 袖口动态返修阶段交付（2026-11-11）

**阶段结束，等待Root review。结果NOT_PASSED；当前没有可放行的袖口候选。** 本阶段只改03服装责任目录、专项验证和交接文档，未改正式producer、library、app、Kotlin、构建或设备。领襟v3已接受的方向保持，扣具／waist-v4仍在后续队列。本轮Tripo费用0，继续免费静态GLB，不升级Web订阅。

### 实际产物与接入边界

当前检查候选为 `cuff-structure/motion-stage3/cuff_wholeface.glb`，SHA `62d881b1e770a3d59ca6507b27a311fed2a88e6e9f5008b05f8174900e915b87`，19,220,856字节。来源raw SHA为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`；正式曲线参照PNG SHA为 `b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09`。

`opening_mapping_wholeface.json`给出177个完整原面删除ID、原顶点一对一映射及新primitive实际attributes／indices。仅新增mesh1／primitive0的177个肤面、primitive1的124个袖边壁；旧mesh0的59829面作为context保留，不重复追加。无partialclip或新重心边点，新增skin／wall直接复制原顶点skin；任何实际atlas皮肤采样命中的完整原手面均保护。原35308属性、78骨rest／IBM保持，位置焊接检查开放边／非流形均为0。与领襟删除面、05颈桥52点incident faces均无交集，见 `composition_boundary_check.json`。这些保护检查不构成动态通过。

### 动作、实图与失败证据

- `motion_audit_wholeface_summary.json`：idle／walk各91／185帧，三攻各106帧，共594帧，采样间隔不超过约1/60秒，包含所有祖先。区分真正几何新增、既有几何恶化和材质语义暴露变化；交线长度不是穿透深度，共面／近平面接触未由该proper-cross检查放行。
- 真正新增布／肤交叉最坏为left@0.15s右侧，交线14.7049mm；既有pair最坏增加11.6680mm（1.9446→13.6126mm）。高置信atlas交点筛选的新增肤／原手为0，但保守skin-bearing混合面在overhead@1s左侧仍有4条proper交叉，不能称手部绝对清零。全量交叉存档已校验压缩SHA，摘要列出来源。
- `renders/wholeface_review/`为0.8m guard／left／overhead三图，沿用原before机位与hash；`guard_1p5m/`为1.5m实际前后两图。全部78骨形变与旧ROI／新增两primitive实际蒙皮点逐姿态核对，Blender与CPU最大表面误差约0.000889mm，材质slot与源hash保持。0.8m左腕可见完整原面边界的尖折，1.5m较弱；均为离线图，未作设备验收。
- `wholeface_retreat_measurement.json`：48方向实际袖边，采用多交点中的保守最小退距。左6.517–16.078mm、右7.718–17.124mm；左4／右1个方向存在多交点歧义，最大差分别6.711／8.248mm。解剖腕纹未定，精确12mm仍为false。
- `safe_reset_analysis.json`：最后一次全ROI、任何颜色及新组件相互交叉的收口检查，需要撤回95个非零收径组中的86个（90.53%），仅余9组。该方案会失去大多数真实形变，因此停止，未生成以材质替代结构的候选。

5项proper-cross正常／边界测试通过，相关脚本AST检查通过，独立review为REQUEST CHANGES。594帧审计启动时未保存运行源码快照，之后仅补CLI及mapping元数据断言；GLB、role和几何映射未变，当前元数据另行核验，不宣称当前源码hash完整跑过594帧。旧权重拟合／local试验均退出主交付路径，保持未通过身份。

### 等待的review与下一轮建议

建议重建相连的腕筒与外袖口，扩大到命中的source2357／2278等布层及其邻面，先确定真实皮肤／布层关系，再做局部几何与蒙皮，保留原手面与78骨。该范围比收径更大，但可直接解决层间空间。较小的替代范围是缩小退腕并保留原腕周包裹，几何改动少，但需接受偏离12mm目标。请Root在对应review明确范围后续派；本会话现等待对应回复。
