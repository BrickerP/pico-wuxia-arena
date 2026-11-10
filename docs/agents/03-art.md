# 精修Tripo人物与PBR

## 本轮目标

先把第一轮主展示刀客做成有明显质量提升的候选，重点是完整人体、面部与手部形体、交领束带、袖口与衣摆的关节余量，以及布／皮／金属的PBR层次。

## 责任与文件

本会话负责 ArtSource/refinement/character/ 的源任务、候选GLB、生产脚本、质量对比和本文件。现有library、app运行模型、人物生产公共脚本、Main与HomeStage由主控统一发布。其它方向正在并行，不回退其改动。

## Tripo路线

1. 查当前高模与低模差异，优先建立一个高精主角色打样。几何生成显式tripo-v3.1，geometry_quality=detailed，smart_low_poly=false，先检查完整头手与服装结构，再做PBR、烘焙低模和rig。
2. 可用v3.5 texture、extreme与delight精修表面层次，原始高精贴图与移动端运行候选分别保留。
3. 已安装CLI具备实验mesh edit，处理器固定P2且接受已有H3模型。它属于独立局部处理试验，先核框选模型空间、费用与输出保持条件，再提交主控决定。每次只评估一个明显缺陷区域。

## 费用与账号

账号区域固定ov，TRIPO_CLIENT_APP=codex。主控先跑doctor并下达可用余额与预算，余额为0停止收费并告知主控。使用已安装tripo-cli，凭据只在本机标准配置，始终先dry-run核实计划。既有授权允许预算内执行，遇到无法估价的实验处理先把真实限制交主控处理。

首轮只打磨一个主展示角色，主控doctor已通过，余额4465、冻结0。首轮人物生产预算上限200credits，先完成一个主展示角色高精与移动端候选。预算内已核实的标准链先dry-run后可直接执行，无需再等用户批准。实验mesh_edit费用未估，先提交计划和模型空间bbox，待主控另行决定。普通rig使用v3.0／tripo以保持78骨与手指细节，再对本角色生成原生slash和握指依据。

质量review追加100credits用于同一PBR源的一次60k convert对比，总上限300credits。complex convert费率未公开，先dry-run核路由，单次按真实账单回填，超过追加额度后停止额外绑定。该授权保留20k候选作对照。

## 质量与交付

- 输出高精源、移动端候选、PBR、绑定与动作适配身份，保持原始源可追溯。
- 近景至少能看清面部、完整手指、交领厚度、袖口和布料／皮革／金属差异。
- 在候选上摆出准备、接触、收势、步法和受击姿态，检查关节与衣摆穿插。高模源直接用于制作。当前已采用60k运行候选，后续按局部轮廓、变形质量和端内开销共同评审密度。
- 给同机位before／after与可看的短片，明确仍待处理项。旧Studio与旧占位角色不作为本轮正式来源。

30分钟内交一个可review阶段，远端任务未结束则保留同一task_id交主控继续watch，禁止重复提交已收费任务。只在主仓库工作，不创建副本、不提交推送、不占用模拟器或桌面前台。

## 当前CLI通路

使用已安装 `/Users/yupeng/.npm/_npx/f5a4b36c43527c00/node_modules/tripo-cli/dist/cli.js`，Node22路径为 `/Users/yupeng/.nvm/versions/node/v22.22.1/bin/node`。每次设置TRIPO_CLIENT_APP=codex、TRIPO_REGION=ov、HTTPS_PROXY=http://127.0.0.1:7897、HTTP_PROXY=http://127.0.0.1:7897。主控维持本轮临时网络通路到任务结束，你不改全局网络或账号profile。

## 阶段交付与验收（2026-11-10）

### 阶段结论

**第一阶段结束，等待review。主控已复核高精头部、交领与双手五指，review通过。**

**第二阶段结束，等待review。20k烘焙、绑定与原生slash已完成，主控要求提高近景几何密度，20k保留对照。**

**第三阶段结束，等待review。60k转换、78骨绑定与原生slash已完成，源GLB已冻结，主控已接管正式集成。**

主控逐张复核60k同机位真实PBR与clay近景，确认唇线、鼻翼和指尖轮廓改善，选择60k作为主展示候选方向。本会话交付范围为 `ArtSource/refinement/character/`，正式发布与设备验收由主控继续。

### 来源与费用

全部远端任务成功，实际合计 **175credits**，总授权上限300，余125。逐项账单、源文件字节数和完整SHA256在 `review_handoff.json`，各目录的 `task.json` 与 `download_receipt.json` 保留成功身份与下载校验。

| 步骤 | 唯一task_id | 实际credits | 源文件 |
| --- | --- | --- | --- |
| H3.1详细几何 | 89f78fc8-53b0-4e6b-ada3-7277e8606007 | 30 | high_geometry/model.glb |
| v3.5 extreme PBR | d2ca3080-2179-47b4-8b61-4da73b37e4de | 30 | high_pbr/model.glb |
| v3.0 baked 20k | f2fd1fd6-b436-4312-9ba2-172602653810 | 35 | mobile/model.glb |
| 20k v3／tripo rig | b465d763-a04a-45a9-906a-96bb85b4aa9c | 25 | rig/model.glb |
| 20k native slash | 1e5d9538-e3e5-435a-a05c-c7ba8df05752 | 10 | slash/model.glb |
| 独立60k convert | 78aef961-efe3-4f9f-a9e2-d501bb808dac | 10 | mobile60k/model.glb |
| 60k v3／tripo rig | 584470a3-9b9a-4636-a9dc-0b1ffb4171eb | 25 | rig60k/model.glb |
| 60k native slash | 5c6edff0-2cf7-4c6b-8885-749b33ec8a62 | 10 | slash60k/model.glb |

生成显式使用 `tripo-v3.1`、`geometry_quality=detailed`、`smart_low_poly=false`。PBR使用 `v3.5`、`extreme`、`pbr=true`、`delight=true`。60k转换沿同一PBR源执行 `format=GLTF`、`face_limit=60000`、`bake=false`、`with_animation=true`。转换实际为60,006三角。原始高精、20k与60k分别保留。

### 最终60k来源

- `rig60k/model.glb` 为18,480,880字节、60,006三角、35,308顶点、78关节，SHA256为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。
- `slash60k/model.glb` 为18,660,564字节、60,006三角、35,325顶点、78关节，SHA256为 `98e785d73a5d6cb767cebd5b79ec2bb9af9a2b717ae2d2576f3a0b7e07ea370a`。含原生 `slash` 的234个通道，源时间0.033333至6.6秒。
- 全部绑定顶点权重合法，最大归一化误差约1.08e-7，逆绑定矩阵全有限。三个PBR图片与转换源逐张SHA一致，见 `rig60k_validation.json`。
- Retarget重导出增加17个顶点，按关节名核对的逆绑定矩阵最大变化约1.94e-6。三张PBR图按材质角色与rig源逐张一致，见 `slash60k_validation.json`。后续动画包装应核对实际skin／rest。

### 评审入口

- `density60k_review/` 对照20k与60k的真实PBR，包含全身、面部、双手俯视和交领。`density60k_clay_review/` 为同相机、同灯光、同中性材质的形体对比，两个目录均有源哈希与展示变换manifest。
- `motion60k_review/native_slash60k.mp4` 为640²、30fps、6.6秒的连续原生动作。该目录保留五个真实时间点的全身、头部与右手近景，`motion_manifest.json` 记录精确时间、NLA、源哈希与骨骼位置。
- `material60k_review/` 有法线开关对照和后腰、后靴、左手的局部PBR／红边定位图，`material60k_validation.json` 与 `tangent_anomalies.json` 记录实际材质及局部边界。

### 已核实与保留项

- Normal、BaseColor、MR均为4096²。Normal与MR为Non-Color，BaseColor为sRGB。MR正确连接B到Metallic、G到Roughness。当前材质未声明occlusionTexture。转换将原8k BaseColor降为4k，实际数据已回填。
- NormalMap使用TANGENT空间、强度1，已连入Principled Normal。源含NORMAL／UV0，未写TANGENT。Blender生成的切线已实测，SDK材质与TBN实现由主控验收。glTF建议缺失切线时按MikkTSpace生成。[Khronos glTF规范](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#meshes)
- 7个极小非零面积补片的UV面积为0，Mikk返回默认切线。对应21个异常loop，占0.0116655%，分布为右后腰2面、左后靴2面、左手3面。严格全TBN检查保留失败状态。主控确认这些局部微小问题不阻塞候选制作，定位图已交付，设备观感继续核对。
- 高精PBR的顶点／索引顺序存在重排，坐标及保留绕序的三角面多重集完全相同，表面几何等价。全文件multipart ETag与服务端一致，证据在 `high_pbr/geometry_integrity.json`。
- 下载曾发生截断及旧下载器实例重叠，已停止旧writer并恢复安全前缀，最终源通过完整校验。下载器仅读取既有成功任务，使用准确Range、单写锁、ETag及GLB长度／SHA校验，签名URL不落盘。
- P2局部编辑保留 `mesh_edit_plan.json` 草案，费用 `not_estimated`，bbox解剖位置仍需叠图复核，未执行实验任务。

### 验证

4项下载回归测试通过，覆盖完整拼接、无preview成功任务、重复跳过、短响应补尾、非法任务及区间边界。全部Python脚本语法、JSON解析及文档差异检查通过。GLB、预览、材质开关与动作均经实际离线渲染，最终源保持冻结。

## 主控60k候选接入与下一轮

主控已接受60k静态几何与真实PBR近景，并取得对应78骨与原生slash。正式原始源复制至ArtSource/tripo-warrior/refined-base60k，source.json记录输入身份与文件SHA。旧base校准已从当前manifest清理，现由唯一producer生成8动作、同皮肤DAO、索引和app副本。

首次装配基线为22,881,080字节、SHA5ff55210dfbe9e10fbad1bf0d182424ae298bf009f9b845e9d307543302e0f3f。本轮握持发布后最终为23,000,580字节、SHA53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641，01／02已完成本轮代理与握持适配。7个微小UV退化三角继续保留局部材质边界，设备观感后续核对。

## Kensei参考流程review与人物精修方案

研究来源为用户指定的[Kensei原帖](https://x.com/0xKense1/status/2118717647357395170)，发表于2026-11-06。已读全文并核对三视图、权重对照与角色转身演示画面。原帖采用风格化角色，帽檐、围巾、披肩和腰带形成清楚层次；本项目继续按中式写实人物评审造型。

### 原帖可移植的工序

作者先审核正侧背设计图，经多视图生成网格，再做部位标记、定向权重修正和姿态检查，动作围绕同一rest pose制作。文中保留头颈与髋部变形问题，战斗动作列为方法模板。具体规则需要按本项目服装、手指和动作范围重写。

### 本项目可核实的差距

1. 当前主角源为text-to-model，缺少先经过美术评审的人物三视图母版。人物身份、五官、服装结构和磨损分布仍较依赖生成器解释。
2. 正式生产入口保留源网格、材质和蒙皮，后续工作集中在动作包装、挂点与指姿，缺少身体／衣物部位的权重清理和关节变形修复。
3. 人体60,006三角共用一套全身4K图集和普通opaque PBR。贴图能够逐像素区分材质，但现有部位近景审查之外，皮肤、眼睛、头发和衣料还缺少定向造型、纹理密度分配及表面参数调校。
4. 七段重定向资源使用同一帧的30根双手指骨姿态，空手左手也被锁为握持形。动作转换的数学正确性与动作本身的自然度需要分别评审。
5. 离线近景使用环境光与三盏面光，实际HomeStage的方向光接近初始相机顺光，侧灯接近人物的3m衰减边界。端内呈现需要单独建立稳定基准。

最终已发布主角为23,000,580字节、SHA53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641。正文早期5ff55210基线对应握持修正前的装配，后续review以最终身份为准。

### 路线比较与推荐

- 现有角色定向修复。保留现骨架与已接通的运行入口，补语义分区、局部蒙皮、按手／片段制作姿态及端内材质灯光。返工范围集中，适合作为首选试点。
- 三视图驱动换源。先锁定设计母版，再用已安装CLI的multiview-to-model制作候选。适用于现有脸型、服装结构和剪影达不到设计目标的部位，会增加重绑、动作与握点适配。
- 重做整套骨架和动作。控制能力更强，涉及全部动作、衣料骨、导出与运行约定，制作和回归范围最大。

下一轮方案以现有主角定向修复为先，三视图同时作为对照基准。Blender职责建议扩展到分区、局部权重、关节几何和动作曲线修整，纳入方案review后执行。每一组部位以固定机位素模、材质近景、制作姿态与实际PICO画面对照审核。

### 四方向下一轮交接

- 03负责人物设计母版与Tripo输入质量，输出可对照的正侧背、材质／配色分区及几何缺陷清单。
- 02负责语义部位与局部蒙皮，分区数据绑定输入模型SHA，优先袖口、肩腋、腰胯、手掌与衣物接触。
- 01负责关键姿态、手部意图与动作变形。按持刀手／空手、按clip分别制作，先评审引刀、击中、随势与收式。
- 04负责实际PICO材质／照明基准，使用同一正式GLB比较主光、IBL与地面接触阴影，再做部位材质审校。

本节为本轮研究交付与下一轮review输入。实现范围、验收门槛和源身份在方案review时统一收敛。
