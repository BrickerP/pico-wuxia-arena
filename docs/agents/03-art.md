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

## 质量与交付

- 输出高精源、移动端候选、PBR、绑定与动作适配身份，保持原始源可追溯。
- 近景至少能看清面部、完整手指、交领厚度、袖口和布料／皮革／金属差异。
- 在候选上摆出准备、接触、收势、步法和受击姿态，检查关节与衣摆穿插。高模源直接用于制作，运行候选约2–3万三角并回填实际统计。
- 给同机位before／after与可看的短片，明确仍待处理项。旧Studio与旧占位角色不作为本轮正式来源。

30分钟内交一个可review阶段，远端任务未结束则保留同一task_id交主控继续watch，禁止重复提交已收费任务。只在主仓库工作，不创建副本、不提交推送、不占用模拟器或桌面前台。

## 当前CLI通路

使用已安装 `/Users/yupeng/.npm/_npx/f5a4b36c43527c00/node_modules/tripo-cli/dist/cli.js`，Node22路径为 `/Users/yupeng/.nvm/versions/node/v22.22.1/bin/node`。每次设置TRIPO_CLIENT_APP=codex、TRIPO_REGION=ov、HTTPS_PROXY=http://127.0.0.1:7897、HTTP_PROXY=http://127.0.0.1:7897。主控维持本轮临时网络通路到任务结束，你不改全局网络或账号profile。

## 本阶段实施与review材料（2026-11-10）

本阶段执行高精几何打样，候选与生产依据均在 `ArtSource/refinement/character/`。canonical来源为本节唯一TripoCLI源任务，制作使用本文件批准的200credits预算。

- 几何dry-run通过，归一化模型 `v3.1-20260211`，显式 `geometry_quality=detailed`、`smart_low_poly=false`、`texture=false`。唯一任务 `89f78fc8-53b0-4e6b-ada3-7277e8606007` 已成功，实际30credits。原始预览为 `geometry_preview.webp`，生成参考为 `generation_reference.jpeg`。
- 原现役身体为18,833三角、10,734顶点、78骨，高精源为1,489,123三角、762,070顶点、78骨。来源与统计在 `asset_comparison.json`，当前低模面部、指节和领口层次损失较大。
- 新候选已具备完整头顶、面部、交领厚度和束带轮廓。手指间隙需完成原始高模近景检查，PBR与烘焙的收费步骤依赖这一质量检查。
- `texture_plan.json` 离线通过，显式 `v3.5-20260815`、`extreme`、`pbr=true`、`delight=true`。CLI将此后处理费用标记为未估价，官方价表核实为30credits。完整标准链预计130credits，见 `production_plan.json`。
- `render_review.py` 统一1.78米、脚底归零、相机与灯光，支持真实源材质和同材质几何对比。全部展示变换独立于GLB源文件。

新高模已完整下载并通过GLB长度校验，53,996,800字节，1,900,024三角、974,844顶点，SHA256为 `a72eb8ee5fbf172d59f32351f6b86d293dd7afa90af29c1b858f72dd4cfa1132`。旧watch已停止，当前只进行离线同机位近景与转台渲染。下载恢复始终沿用同一成功任务，没有重复生成。阶段结论将在此节补齐。

### 第一阶段结束与review结果

**第一阶段结束，等待review。主控随后已逐张复核面部与双手俯视近景，几何门槛通过，授权沿标准链继续第二阶段。**

- 本地完整源为 `high_geometry/model.glb`。双手俯视在 `review_top/after_right_hand_top.png`、`review_top/after_left_hand_top.png`，可见五指分离。头部与交领在 `review/after_head.png`、`review/after_collar.png`。
- `review/` 为现役身体与新高模的同材质、同相机、同灯光对比。`review/comparison_turntable.mp4` 为左右对照转台，1536×768、12fps、2秒，用于静态几何检查。
- 验证已完成GLB长度、来源哈希、统计、Blender实际渲染、视频时长与分辨率、JSON解析、脚本语法及文档差异检查。
- 第二阶段PBR唯一任务 `d2ca3080-2179-47b4-8b61-4da73b37e4de`，输入为几何任务 `89f78fc8-53b0-4e6b-ada3-7277e8606007`。已完成实际扣费30credits，PBR预计30credits，提交记录为 `texture_submission.json`。
- 第二阶段待完成PBR材料核验、2万三角烘焙及指间/袖口复检、78骨实测、原生slash与握指来源。候选当前仍处于源制作阶段。

### 第二阶段进行中

PBR任务 `d2ca3080-2179-47b4-8b61-4da73b37e4de` 已成功，实际30credits。`high_pbr/preview.webp` 可见黑灰布衣、棕色皮带、黄铜扣与靛蓝裤的分区。高精PBR源76,726,496字节，正在使用同任务断点恢复下载。

2万三角烘焙任务 `f2fd1fd6-b436-4312-9ba2-172602653810` 已成功，实际35credits。参数为 `model=v3.0`、`face_limit=20000`、`bake=true`、`quad=false`。正在下载到 `mobile/`。基于已成功的远端输出并行启动原生绑定，交付前完成低模指间与袖口复检。当前累计实际95credits。

`download_task.py` 只读取既有成功任务，按准确字节区间恢复下载，核对206、Content-Range、ETag、完整GLB长度和SHA256。签名下载URL仅在内存，落盘记录脱敏。输出目录使用单写锁，下载失败沿同一task_id恢复。
