# 03 · 人物设计母版与Tripo输入质量

## 最新用户目标与执行队列

完整制作规格见[动作与打击反馈规格](../combat-polish-spec.md)。本队列承接2026-11-10用户最新的动作、特效、UI、环境与数值要求，领襟、扣具与现有场景为本会话后续责任。当前已产出的有效阶段先收口，再按队列继续，不因等Root回复而停住。

Root对阶段3小片领襟的review已经写在本文件，立即按阶段4整段前襟合同继续，不等待再次批准。随后制作古铜环扣／暗钩候选。人物阶段交付后转ArtSource/refinement/environment，精修当前酒馆／庭院的石路、排水、积水、木柱脚、门槛、瓦檐与灯笼。先选玩家面向对手时最常见的一段路面和门楼，给同机位真实3D前后图。湿润有空间原因，建筑层次与材质尺度可读。原有场景沿用同一来源，候选不覆盖app，Root统一接地与配光。

四会话共享仓库，请保留他人编辑。Root维护真实命中事件、最终UI与SDK接线、公共角色producer、正式发布、共享构建、设备和Git。先开发与专项制作检查，整局自玩后置。每阶段交GLB／代码、前后图或短片、来源与明确限制，30分钟先交第一项可见进展。

Root已取得本轮启动实图artifacts/combat-polish/first-build-ready.png。环境阶段以此实际机位评审石板尺寸／黑缝深度、门口木构与墙面材质尺度、阴雨远景层次。主体人物仍需先完成当前领襟与扣具。UI面板遮挡和文字大小由Root处理，美术源保持真实场景内容。

## 当前状态

**阶段3结束，等待Root review。** 已交真实领襟局部GLB、顶点位移和52张素模／PBR及专项姿态对照。

## 上一轮成果与Root review

主角源为Tripo-v3.1详细几何、v3.5 extreme PBR、60k convert、78骨与原生slash，上一轮实耗175credits。最终已发布body为60,006三角、3张4K图。面数与贴图提供了基础，人物身份、衣物结构、面部与手部细节的美术目标仍需明确。

用户指定[Kensei参考文章](https://x.com/0xKense1/status/2118717647357395170)。原帖的三视图、分件、定向蒙皮和逐姿态检查值得转化为当前制作工序。其风格化服饰与本项目中式写实目标分别评审，源权重规则按VR手指需求重写。

## 文件所有权

负责ArtSource/refinement/character/design/与本文件。其他character源目录、原始rig／slash、公共producer、manifest、library和app成品交Root维护。02做分区蒙皮，01做按clip手姿，04做端内配光。

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
