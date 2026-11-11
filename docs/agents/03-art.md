# 03 · 服装结构与装配精修

## 最新用户目标与执行队列

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你集中做整段领襟、交领层次、真实袖口／护腕、布／皮分工、腰带铜扣、衣摆开衩和服装局部重拓，要求正常胸部／全身视距有可见变化。

06主导整套雨后庭院与建筑，07主导照明，05主导头脸与发束。你已经产出的environment候选和测量直接写清路径交06，环境后续从你的执行队列移交。继续完整领边折返带与铜扣，并接02尚未完成的12mm袖口结构。保持原78骨rest、手部和动作来源可追溯，新拓扑给原面／顶点／UV／权重映射。与05约定颈部边界，不整只覆盖对方成果。

## 当前状态

**本轮有效阶段已收口，等待Root review。** 领襟分支未通过正常胸部PBR可见性门槛并冻结；古铜环扣和石路／门口真实GLB候选已完成专项及同机位检查。

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
