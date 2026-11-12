# 05 · 写实头脸、头发与连续颈部

## 当前收件合同：一次图像条件Tripo新源（2026-11-12）

Root已收direct-high首件，`partial_direction`不等于整头通过。现转入**一次图像条件源实验**：Root负责OV余额、能力／dry-run审核及付费任务；05只接新源后的头发适配，03负责衣服。已交直修首件冻结供Root审图，不再改型／扩图，不做新曲线／参数盘髻，不购买hair cards或继续商品搜索。以下旧路线与商品记录仅为历史证据，本节优先。

**已实际看输入图**：`ArtSource/bench/tripo-image-input-2026-11-12/front-tpose-v1.png`，1254×1254，SHA `d07299e90d89077add6e09a59f62138a1035536fb7728dcadbab8b3c0894c453`。正面可读前额主束隆起、两侧后梳及髻顶分瓣；束根大半被前部头发遮挡，不能据此确认耳后／后颈汇聚、侧后体积、交叉叠压或藏尾。它是二维条件输入，尚非新3D来源或质量通过。

**身份锁定**：现已接入的成年脸／眼以`neck-continuous/candidate-raw.glb`（34ce）与同源b732 PNG角色为真源，保脸型、发际与耳的关系、眼距、眼球／角膜和当前78骨rest。生成图及新Tripo脸／眼不构成替换许可；发型适配不得通过缩放／移动现脸眼迁就新发区。新源若头发与脸皮融合，先标清发区和保护边界，再做接口适配。

### 新源只按三项收件

| 项目 | 收件标准 |
| --- | --- |
| 发根真实汇聚 | 同一模型的侧背clay能连续追踪前额、额侧／耳后、后颈主束到束根；起束贴头，连接有实际几何，去掉颜色／normal后仍成立。悬边、浮贴发片、断开的套圈不收。 |
| 主束与盘结大形 | 完整头部／上半身1.5m同灯多角度能读出主束分组、空间转向、实心折束叠压与藏尾；单球外包络、放射刻槽扇形或几条交叉带子不能算作盘结。先灰模／剪影，再材料。 |
| guard／转头贴合 | 适配到现有角色后，以Root实际guard入口及转向两侧／回正的同源流程观察，根部、头皮和髻保持贴合，无浮束、开口、穿插或侧背散架；脸眼身份保持。T-pose单帧不能替代此项，任意未接入运行入口的动画也不能冒充通过。 |

### 已冻direct sculpt侧背：仅三条结论

1. 侧面降低后收的小幅收益可见，但只改变原髻体积的朝向与高度，未新增盘结结构。
2. 背面仍是压矮的放射刻槽扇形，主束转向、折返叠压和藏尾尚未读出。
3. 原双圈束根在髻缩短后相对更突出；这两个已审guard角度未见明确新增开缝，不能外推为转头贴合通过。

冻结点：`direct-high-sculpt-2026-11-12/delivery-freeze.json`中16个实物／证据文件本轮只读核验一致。新源尚未到，本路不轮询或自行触发生成；Root交付原始源与任务／输入标识后，05按上述标准接发区、03接衣服。正式资源、公共producer、构建、设备和Git均由Root处理。

## Root本轮R2审核与路线切换（2026-11-12）

已实际看R2四向clay/剪影：侧后仍像分离带子、架空弧片和细尾，整头没有优于现基线。结论拒绝，不再做第三轮参数曲面/漂浮发带。UB-01v2仅作为造型输入接受，不能当3D通过。

现在执行你已交出的“原高模直接修形”路线：先读取本轮handoff具体源/保护区，在既有真实高模发区上整理主束与盘绕，保连续发根/贴头表面；不要用外加曲线遮住原壳后当修形。先只改一项能在完整头部侧后1.5m读到的大结构，给保原脸/眼的完整guard两张灰模。无需再等用户批准，不收费重生全人，不改正式34ce。若直接高模路线也无可见增益，交具体成熟可授权发束部件的来源、适配工作与代价，停止无效算法循环，Root选择替代，不擅用无来源资产。

主控持续目标已恢复active，阶段完成写本文件供Root接力；不无限等待，不做新的PBR/微孔实验遮形。

## 本轮直接高模首件：一项H5后扫压低，侧／背两图已交（2026-11-12）

实物目录：`ArtSource/refinement/hero-face/direct-high-sculpt-2026-11-12/`。完整guard、实际1.5m同灯同机位对照：`review/side_guard_1.5m_before_after.png`、`review/rear_guard_1.5m_before_after.png`；原图`after_side_guard_1.5m_clay.png`与`after_rear_guard_1.5m_clay.png`。**NON-NATIVE OFFLINE；只交这一项大结构，不声称新建叠压盘结或整头通过。**

1. 在真实`fc447`高模原髻上直接压低并向后收，原束根和盘绕表面连续保留；没有新壳／曲线／发带／封盖。`head-high-sculpt.glb` SHA `f051f274222717af96e647c5c14a1cf35ae20ccf60f70f21993c35a649a5d684`是真实修改后的完整高模，仍为原Tripo源坐标；`direct-high-editable.blend`含原高模Basis／H5编辑shape key与脸／耳／头冠／根部sculpt mask，并含实际guard预览Scene。
2. guard图片为**现有低模接受同一高模体积编辑**的公平宏观预览，脸／眼／其余头发与衣物、78骨rest动画保持；不是把完整旧高模脸替换进当前角色。`guard-private.glb` SHA `cd649293cb7bcbb2c202718a19594022448990e44a3a899544c3375896b4e343`。10项测试通过，高低模实测无新增退化／负向三角形；源拓扑、UV、全部保护区保持。首个未发布过渡草案的一处低模细长面问题已通过上段仿射化解决，当前不保留旧处理路径。
3. 独立目视判定为**partial_direction：小幅方向收益，未通过完整发髻／发型**。侧面更低、更后伏且紧凑；背面仍是偏扁的刻槽扇形，未形成新的盘结，原双圈束根相对更明显。未见明确新增开口，但这里只审侧背两个guard样本，不能据此放行转头、举刀或PBR。结论见`visual-review.json`。

源／选择区／法线传递／面积与保护检查在`direct-sculpt-report.json`；实际shape key／mask与两图指纹在`review/render_manifest.json`。保存的高模shape key与sculpt mask已实测确认；高模原有UV保留，未新做UV或贴图。所有源文件与34ce正式raw未覆盖，Root公共producer／app／构建／设备／Git未触及。当前这一项已交供Root接力，不空等轮询，也不自行扩大到整头或下一关。

成熟备选已核到具体商品：[Sleek Man Bun with Trimmed Beard – Game-Ready Asset](https://www.artstation.com/marketplace/p/nzW27/sleek-man-bun-with-trimmed-beard-game-ready-asset-low-poly)，当前挂牌USD19，为hair cards；髻位较低，需保脸后重新贴合发际、上移髻、绑定Head26，并验证GLB透明排序／移动端开销，不能即插即用。确切商品许可与适用额度需按实际选项核定；**本路未购买／下载／引入**。另一低髻＋散侧束商品不匹配收紧剪影，已剔除。来源、格式、当前价格、许可链接、适配工作和未核项在`licensed-hair-options.json`，只供Root选择替代。

## Root review and next production contract (2026-11-12)

用户本次要求继续。Root已实际看图收件：12研究完成；05发髻变光滑蛋形，拒绝；03袖口像深色短筒加浅色粗壳且极限姿态穿插，拒绝；06木窗同光clay有真实进深收益，只接受结构方向，尚未原生放行。本轮正式游戏没有获得有效的人物升级。

下一节点是一个完整刀客上半身。比较三路：旧小补丁收益已不足；反复整人重生成会重置身份/绑定且无质量保证；选择现有Tripo高模、固定身份和明确参考下的完整部件造型。最大风险是缺少造型输入时再把发髻做成球、袖子做成管，所以先形体、再动态、再材质、最后原生。

唯一仓库 /Users/yupeng/projects/personal/pico-wuxia-arena，Kotlin+PICO Spatial SDK6.1.9，Space Pro/OS6。正式b03f人物与8b1098场景仍为基线。你不独占仓库，不回滚他人，不复制仓库，不改pico/BrickerP.github.io。Root独占正式producer/manifest/library/app、Kotlin、共享构建、设备和Git。本轮具体制作继续，不等同恢复24小时自动监控。只改本路范围，研究已交部分不反复写长报告。

Root审核：拒绝method-study-2026-11-12参数发髻。已看0.8m对照，原盘绕被圆蛋替代；既有skin/tangent delta另列，不算新造型成果。

1. 保当前成年脸/眼/身材，范围为发际、后梳主束至盘绕髻的完整发型，不再只替髻顶。与12统一造型板对齐；用已有高模和真实束发参考，表现主束分组、叠压、收束方向、发根及不规则轮廓。单球/环和连续正弦槽不是可接受造型。
2. 首交可编辑造型、可组合部件及完整上半身guard的1.5m正/侧/背/三分之四clay与剪影，0.8m只补关键问题。保03衣物不变，标明改动。可借现骨架预览，不重建10clip、不先做细纹/整头UV/PBR。
3. 与03按现raw坐标、1.78m和78骨rest交接。灰模通过后才接实际转头/举刀形变，随后做一次整发束材质。Root负责完整角色组合与正式发布。
4. 参考明确后最多两轮大形。若仍未明显优于正式整头发型，停止参数曲面，交具体可授权发束部件或原高模直接修形替代方案，不能加细纹后又宣称改善；不得以Quaternius替敌人。

本轮先交一组有效整人灰模，不批量渲染几十张图。阶段写本文件供Root即时接力，不空等重复许可，不碰共享构建/设备。

---

## 当前首件：完整发型两轮灰模已交，R2返修／停止参数路线（2026-11-12）

完整对照已交：`ArtSource/refinement/hero-face/full-hair-clay-2026-11-12/r2/review/full-upper-body-clay-silhouette.png`；首件图为同目录`after_3q_1.5m_clay.png`。正／侧／背／三分之四，共4张before clay、4张after clay和4张after剪影，均为实际guard `attack_overhead@0`、实际1.5m、同一46.5°镜头与灯光。**NON-NATIVE OFFLINE；两轮均未明显优于正式整头发型，灰模关不通过，不进入UV／PBR、动态或原生。**

1. **主束仍不成立：** 正面收益很小，侧背宽束像覆在旧发纹上的叶片，悬边、暗缝和尖尾割裂“发际／耳后→束根”的连续收束。修掉R1黑片并不等于完成整头升级。
2. **盘髻／剪影仍不成立：** 像在旧髻上加盖片，交叉可见但紧实盘绕、叠压和藏尾未成立；侧后轮廓增加了高度和杂点。独立复核已看四个方向及侧背剪影，结论为返工。
3. **保护通过不等于组件通过：** R2原24图元、全部属性／索引和78骨rest动画逐字节保持，6项追加组装测试通过；但新束端盖有同向公共边，另有局部法线／面朝向不一致，新增几何也未完全通过。**两个大形轮次已用完，停止第三轮参数尝试，保留基线，由Root接力下述原高模直接雕修方向。**

实物均位于`ArtSource/refinement/hero-face/full-hair-clay-2026-11-12/`：`r2/full-hair-authoring.blend`为真实原生Bezier＋扁截面驱动，`r2/hair-locks-clay.glb`为部件，`r2/full-hair-private-clay.glb` SHA `6cde4741f4798fb2e44d991379022a6d1b7bd4c083666d98e7b4030587ccd115`为拒绝发布的私有组合；`r2/review/posed-editable-review.blend`保留实际guard场景。原生控制点移动驱动几何的探针已验证；没有新UV／贴图／bake。`r2/source-guides.json`锁12 UB-01板指纹，`guide-controls.json`保存实际控制点，`composition-report.json`、`independent-geometry-review.json`、`visual-review.json`分别为组合保护、几何失败与目视证据。

**具体替代入口：原高模直接雕修，未伪称已完成。** 使用已有`source/head-high-source.glb` SHA `fc44714e8f12a739570a110c881133d057344d8f9fad45a46b0703f1ecc196ab`，无需另购／生成；到raw的变换为`P*.18+(-.009,.8899,0)`。H1–H4直接在原雕塑体积上建立连续后梳大束、减弱重复深槽，手工核发际／耳／脸保护；H5以原髻体积雕出三个不等实心折束和藏尾，固定束根。H5可用已核单闭环场`raw Y−.35X>.966`定位（未对齐source为`y−.35x>.4052777778`）。先1.5m四向clay，再考虑边界重拓扑。完整输入、选区、锁定范围和验收在`r2/direct-sculpt-alternative.json`；现有`high-hair-reference.glb`仅含y≥.939上冠／髻，不能冒充完整高模发型。当前完整高低UV对应仍未证实，禁止把整张low atlas当已核高模材质映射。

复现R2：在仓库根目录用Blender4.5.15运行`author_hair.py -- --controls …/r2/source-guides.json --output …/r2`，Python运行`assemble_clay.py`（仅追加，默认r2），再顺序运行Blender `render_clay.py -- --first`、`--complete`，最后Python `render_clay.py --assemble`；上述脚本位于本次完整发型目录。`render_manifest.json`锁模型／原图指纹、姿态、四向相机和灯，R1/R2相机完全一致。当前不继续改型或运行下一关；正式34ce／b732未写入，Root公共producer／app／构建／设备／Git均未触及。

### R1首件与拒绝证据（保留）

首张完整上半身guard、实际1.5m三分之四灰模：`ArtSource/refinement/hero-face/full-hair-clay-2026-11-12/review/after_3q_1.5m_clay.png`。**NON-NATIVE OFFLINE，首轮形体未通过。** 正／侧／背clay和剪影已补齐；R1冻结作拒绝证据。

- 实物：同目录`full-hair-authoring.blend`为真实原生Bezier路径＋可编辑扁截面，控制点变动确实驱动几何；`hair-locks-clay.glb`为组合部件；`full-hair-private-clay.glb` SHA `04afedc2f1c351252dfddf2325610b0232083de1da4045d47c5ed36ef6eda613`为仅私有合成。现脸／眼／03衣服、原78骨/rest/动画保持，原发面转为内层；没有新贴图或bake。映射与6项保护／边界测试在`composition-report.json`、`test_assemble_clay.py`。
- 首图最大问题：主束间黑缝和薄片感明显，盘髻形成过空的提手状轮廓；虽已不再是单圆蛋，**不能记为写实提升**。实物审计进一步定位：R1向法线内缩原发面，使微小发槽三角形发生大量翻转，重算法线朝旧N对齐掩盖了几何问题。R2已撤除整条内缩／缩髻路径，原头所有属性和索引保持不变，只组合真正贴合的新发束。
- 12的`ArtSource/bench/upper-body-design-2026-11-12/UB-01-upper-body-v1.png`及README已交并实际查看，R2据此完成第二轮；旧v2不再作当前造型依据。检索到的教程横幅不是已核真人参考，IG正文可读但媒体受弹窗限制，均未冒充已核真人造型照片。

---

> Prior delivery evidence below; execute only the current contract above.

## 2026-11-12 方法重审交付：样件拒绝发布，停在Root回执

本轮研究和**一个发髻局部实物样件**已完成。结论是：制作链确有缺口；本次“高模包络→参数曲面重建→受控UV/bake”虽然完成技术闭环，**审美退步，不作为production候选**。不得因文件齐全、拓扑或贴图检查通过而合入。本节覆盖下方历史交付状态；全局自动开发仍暂停。

### 根因与来源

1. **身份输入未闭环。** `cli/head_dry_run.json`是`text_to_model`且`pending_uploads=[]`；未见统一v2母版真正传入头部任务的证据，v2仍`generation_ready=false`。成年骨相、发际与耳鼻比例没有受控多视图约束。
2. **整壳降模替代了按语义雕修／拓扑。** `prepare_head.py`是焊接后全头DECIMATE，未建立眼睑、嘴角、头皮、发束的受控边流。去材质后仍有宽大的雕刻发槽，说明形体问题实际存在。眼球与角膜已另拆，不能误说全角色都融合。
3. **碎片UV与材质／bake缺口。** 按POSITION+UV合并后的low仍461片UV，正式P1为459片；前中央脸窗口跨101片。正式PNG三张头图与241482低头逐像素一致，未有接受过的新高低模normal bake。皮肤和头冠／发髻共用PBR表面；旧微表面与切线候选不能补回这些形体工序。

指定[X文章](https://x.com/0xKense1/status/2118717647357395170)实际标题是“Create 3D Game Models for Free: Opus 5.5 + Blender + Tripo (15 Steps)”。它强调一致多视图、部件拆分及真实姿态检查；**尚未核实“Fable 5.2”所指的其他原帖，也未见该文公开可复用代码仓库**。不能把作者效果帖当作已验证开源实现。公开可核的替代实现为[Hunyuan3D-2官方仓库](https://github.com/Tencent-Hunyuan/Hunyuan3D-2)，含2mv多视图模型与Blender addon；本轮未安装或运行，未验证本机／许可证适用性。

### 两条路径与本轮选择

| 路径 | 收益 | 代价／边界 |
| --- | --- | --- |
| A：现有高模雕修、语义分件、受控重拓扑、新UV／烘焙 | 固定身份和尺寸，可直接验证工序；无需收费生成 | 仍需真正的发束叠压、眼睑嘴部边流和美术判断 |
| B：完成一致reference后重新生成再精修 | 源骨相／轮廓经正侧面证明失败时，可改善输入约束 | v2尚未生成就绪；新模型仍需A中的后处理，不能保证更好 |

**选A，本次只检验局部发髻。** B的具体前置门是同尺度、平光、闭口的正面／真实右侧／背面正交图，耳眼鼻底下颌高度与发际顶髻一致；先由Root审reference和预期收益，再决定生成参数。没有提交新任务，追加credits=0。

### 实物、映射与复现

目录：`ArtSource/refinement/hero-face/method-study-2026-11-12/`。

- `topknot-authoring.blend`：真实低模quad源、高模流向雕修壳、原高模局部参考与12条示意曲线；曲线是派生参考，**不是可编辑groom驱动**。真实造型源是高模测量轮廓、平滑拟合和参数曲面。
- `topknot-low.glb`：新UV／独立材质组件，SHA `88e07feacb84860726f7f208e1d8908f4f473bb6107e85e0fbbb7cacbc66eb39`。
- `candidate-private.glb`：只在b732私有PNG副本替换顶髻，SHA `446f3faa672d68c289caca3fa571caa92e3972cc56c0eb9f7bf82bfed4f91a4e`。**仅失败方法证据，不发布。**
- `hair-basecolor.png`、`hair-mr.png`、`hair-normal.png`：2048²，normal由真实高到低Cycles tangent bake生成；纵向UV重建，不继承旧头normal到新UV。固定烘焙／导出三角划分；参数在`authoring-report.json`。
- `assembly-report.json`：旧头每面保留／裁切／移除及交点映射。删除区域按raw空间场`Y−.35X>.966`定义；新source不以旧顶点ID永久不变为约束。新组件按骨名映射Head，保留原skin/rest/IBM和动画。原头切面有意开放，依靠闭合发髻／发带重叠，**不声称整头水密**。
- `method-evidence.json`：完整链路、官方来源、两路径、审美与四遍自查；`verify-report.json`记录独立检查及失败；`delivery-freeze.json`给文件指纹。

复现按顺序执行，**同时最多一个Blender进程**，终端workdir必须为`/Users/yupeng/projects/personal/pico-wuxia-arena`：

```sh
study_dir=ArtSource/refinement/hero-face/method-study-2026-11-12
study_blender=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$study_blender" --background --factory-startup --threads 2 --python "$study_dir/author_topknot.py"
python3 "$study_dir/assemble_specimen.py" --before ArtSource/refinement/hero-face/skin-bake/native-v3-source.glb --component "$study_dir/topknot-low.glb" --output "$study_dir/candidate-private.glb"
"$study_blender" --background --factory-startup --threads 2 --python "$study_dir/render_specimen.py" -- --stage before
"$study_blender" --background --factory-startup --threads 2 --python "$study_dir/render_specimen.py" -- --stage after
python3 "$study_dir/render_specimen.py" --assemble
python3 "$study_dir/verify_specimen.py"
python3 -m unittest discover -s "$study_dir" -p 'test_*.py' -v
```

`verify_specimen.py`固定输入SHA，重建GLB若因工具版本／导出元数据改变指纹，必须先核对内容再显式更新预期SHA；当前冻结输入应以exit1报告真实接缝缺口。最后一条命令复核9个裁切、属性、资源映射和源保护边界用例。

### 真实对照与判定

- `review/comparison_0.8m.png`与`comparison_1.5m.png`：上before／下after，wire、clay、PBR；同一真实`attack_overhead@0`、同灯同矩阵、60°透视、实际0.8m／1.5m。原始1024²图片未改，拼图只加标签。**均为NON-NATIVE OFFLINE，非端内图。**
- `review/after_diagnostics.png`：侧面、后面、normal开／关，以及实际`attack_overhead@.8`单采样。`render_manifest.json`含相机、灯、姿态和图像指纹。
- **0.8m明显退步：** 新发髻是完整蛋形，原有转向／交叠发束轮廓被抹掉，平行亮纹像硬壳或缎面；独立复核同意拒绝。clay已经显示形体缺失，PBR条纹不能补回叠压。
- **1.5m无真实感提升：** 细纹消失只剩偏亮圆球，与原头冠风格不一致。normal开关收益很小。发根圆环又强化了独立零件插在头顶的感觉。
- 技术方面：9项组装单测通过；新部件闭合、UV无退化、N/T有效、Head权重及贴图嵌入正确；原binary/accessor前缀、其余图元、nodes/skin/animation保持。但**Root containment失败**：151边环604采样中13点在新发髻／发带体积外，最大约0.097mm raw，即约0.177mm场景实尺寸。图中未见透光洞不等于连续遮盖通过。

本轮的正向收益是验证了独立材质、新UV、固定拓扑和可复现bake；它们没有自动带来写实发束。**拒绝参数曲面加细纹作为头发造型捷径。** 后续A必须先用真正可编辑、扁截面、宽窄变化和不均匀叠压的发束通过clay剪影，再进入UV／bake；本路不自行继续第二件样品。

冻结34ce raw、b732公开PNG与canonical图片SHA本轮末复核均保持。无公共producer／manifest／library写入、无app／Kotlin／构建／设备／Git写操作；旧skin-bake和tangent delta继续冻结。未验证完整转头、三攻、其他灯光和SpacePro端内表现；完整头冠groom、面部拓扑／皮肤仍未完成。**研究与样件交付完成，已停在Root回执点，不自动恢复全局目标。**

---

## 当前交付与冻结边界（以下为2026-11-11历史）

2026-11-11：Root已接收 **34ce头颈几何**，并将schema3 canonical gait／KTX组b03f正式组合、原生模拟器启动（Root报告APK767bc0af无NO_MEMORY）。FullStage图已可见新头脸、眼和领口；**近距、转头、三攻压力与Space Pro实机质量仍未完成**。

本路本轮收束为两份独立delta：

1. 局部肤色与粗糙度PNG候选：`ArtSource/refinement/hero-face/skin-bake/skin-material-delta.json`。
2. 头皮零切线／接缝正交修复候选：`ArtSource/refinement/hero-face/tangent-audit/tangent-delta.json`。

几何raw **34ce保持冻结**，原normal保留。没有新Tripo任务／新rig／公共producer或app修改／Git写操作／设备操作。Root独占schema3 Python与发布窗口；旧v2 producer调用入口已移除，**不得恢复v2 fallback**。新prepared需要Root给v3私有manifest或Root执行，本路只在Root提供的PNG文件副本替换图像。

## 唯一工程、分工与输入

工程：`/Users/yupeng/projects/personal/pico-wuxia-arena`。每次终端调用显式workdir；禁止复制仓库/worktree、切分支或提交推送，保留其他并行修改。只负责`ArtSource/refinement/hero-face/`与本文件。Root维护正式producer、manifest、library/app、Main/HomeStage、构建、设备和Git；03负责领襟，02武器，07光色。

技术栈：Kotlin + PICO Spatial SDK6.1.9、Space Pro/OS6、FullStage。本路没有更改容器、Gradle或SDK版本。

固定原raw rig SHA：`43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。头部来源为既有高精头`fc44714e8f12a739570a110c881133d057344d8f9fad45a46b0703f1ecc196ab`与彩色源`ba0086a8cf7a94c050f65fdd705138ae2238886004557e361b6a86743a5d8f88`。历史Tripo实耗60+30=90credits，本轮追加0，Root已明确停止收费生成。

## 已接收的连续头颈几何

- 当前raw：`neck-continuous/candidate-raw.glb`。
- SHA：`34ce3a601f842fcb512b643d2ea62317e87485d646ca453e4a46d5116681d4f9`。
- 几何交接：`neck-continuous/neck-handoff.json`。
- 冻结记录：`neck-continuous/freeze-34ce.json`，含raw、旧私有prepared与82个验收图文件；`verify_frozen_candidate.py`只读校验。
- 旧拒绝候选`hero-face-candidate.glb`的595455 SHA仍原样保留，**不作为发布source**。

原方案把新颈部全权重Head叠在原Head/Spine02/Clavicle混合权重的颈领上，静态图无法证明动态接缝。现已采用原身体真实52点边环到新头129点斜切环的连续桥，逐点共位／同权重，原78骨/rest/IBM和原身体流保留；原身体50,350面保留。03的13个领襟保护面全部保留，与52环的83个UV同位源ID无共享顶点；`coordination-03.json`给确认与未来delta同步规则。

斜切场`Y+.6X=.8223`保下颌并把新头和桥面分离。源52环有真实凹口，不强套不成立的共极点参数化。双向半边52/129闭合、共位权重差0、桥面未检出自交。桥接取色已改为真实边/点取样后在线性RGB插值，不再跨UV岛插值UV。

可见证据（未重采样的真实GLB离线图）：

- `neck-continuous/same-idle-neck-comparison.png`：Root同idle／机位，旧黑开口、喉黑线、V领尖色块关闭。
- `neck-continuous/guard-1.5m-comparison.png`、`turn-1.5m-comparison.png`：正常1.5m无旧黑线/尖片。
- `posed-review/`48图含idle/walk/turn/三攻@1、0.8/1.5/3m；`guard-review/`18图为三方向attack@0；`stress-review/`6图补上劈.8另一侧/正面/背面。
- `diagnostics-initial/`与`diagnostics-corrected/`分别有PBR、albedo-only、clay、normal、mesh-normal。初版细黑线/尖色块只在albedo存在，证实是贴图采样，不用黑材遮盖。

42个真实曲线采样、181组接口距离均为0，仍记录上劈.8后颈内部面656受压（面积比.0018769）；已补应力图，正常1.5m和背面未见开口，不宣称所有面无压缩。当前guard入口须从实际EnemyAnimator确认：此前静止/guard用attackProfile.clip@0，不能把walk/turn冒称guard；最新v3图像QA已使用Root实际组合的attack_overhead@0。近距后颈仍有小的皮肤色调接合差异，不作为完整皮肤真实感已完成。

## 本轮PBR纹理实物

唯一入口：`skin-bake/skin-material-delta.json`，角色base，**仅候选，不默认发布**。

| 槽位 | PNG | SHA |
| --- | --- | --- |
| Base Color | `skin-bake/weathered-basecolor.png` | `a92fefa6554383daa5a46142f42c6128d24201b2f6c74a0a10f6bf5b4146bf82` |
| Metallic/Roughness | `skin-bake/weathered-mr.png` | `146d03559ddc6b12f8edae09d492aa0f551fc77f06c00ccff21a6c7ff5e77a3e` |

均4096²。局部下颌吸收色、双颊暖色与额头日晒色是内在肤色变化，不烘焙方向性光影；面颊/下颌/额头/鼻部粗糙度分区，清理皮肤金属通道。眼唇、头发、遮罩外像素与原normal保护；新颈桥材质未改。数据与保护检查在`weathered-report.json`、`weathered-mask.png`。

独立目视复核：**安全、温和改善**。中性0.8m变化细微，1.5m几乎不可辨；额外同灯小面光斜射检查可减弱额头蜡感、保持鼻部较窄高光。仍缺可信中/细尺度皮肤细节，**不是完整写实皮肤或native通过**。

当前QA已切到Root新schema3实物PNG：

- 原文件`ArtSource/tripo-warrior/library/base_prepared_png.glb`，本次参考SHA `b732929ed6bd9ded6ce00de3564b8c446aa7ab59f83495d95cdfabfd9310af09`。
- 只读快照`skin-bake/native-v3-source.glb`；原三张头部图像payload与作者低模逐像素一致，见`native-v3-input.json`。
- 私有图像替换对照副本`v3-weathered-preview.glb`仅image4/5改变；mesh/accessor/nodes/skin/animation/material/texture/sampler与原b732一致，原binary前缀不变，image数量不变。没有调用producer或改曲线。
- `material-v3-neutral-comparison.png`、`material-v3-0.8m-comparison.png`为同灯同guard@0前后；`material-v3-grazing-comparison.png`为额外材质高光检查，非原生截图。
- 实际新native图`artifacts/canonical-native/reset-controller-view.png`已查看：成熟眉鼻/束髻/领口远距可读；皮肤仍偏平整，头发仍呈雕塑化发束和较宽高光。该远图不足判断毛孔、发际细毛、耳侧压力和角膜排序；先处理切线输入风险后由Root近距验证。

**原normal不替换。** 自动笼和显式同位笼高低模烘焙都在额头产生不自然刻线；物理微孔法线在正常距离收益不可辨，均标为拒绝。显式笼数学连续并不等于目视通过。相关失败图/报告保留供审计，重复QA模型已清理，不把这些PNG当当前推荐。

纹理工具：`author_skin_material.py`、`apply_skin_normal.py --role basecolor|metallicRoughness`。按图像角色、已使用tripo_头皮材质和原payload SHA选择，原图像索引内替换；不能只排除body就把Grip武器法线误选为头部。Root在新v3 PNG/KTX流程中合入delta，**不把历史QA模型当producer source**。

## native切线告警：已定位、未宣称解决

日志：`artifacts/canonical-native/startup.log`，20:23:40.420、pid15914附近，`FindInvalidDataProcess fails on mesh tangents: Found zero-length vector`。模型后续attached不等于法线响应已通过。

审计：`tangent-audit/tangent-audit.json`、`skin-bake/formal-tangent-audit.json`。本次正式PNG b732与runtime base `722ffe6e9d3d498629b257e88aaeaf3b0ad368e5c5a37be87ccb85d63a6cf83e`的全部属性/索引流一致。

| 范围 | 事实 |
| --- | --- |
| P1头皮 | 2个实际被索引使用的零TANGENT，ID13576/23845；源自2414低头导出，raw34/正式组合沿用，非新v3 gait或KTX产生 |
| P2/3眼睑 | 复用旧头T流，同2零值存在但未使用；不是6个独立缺陷 |
| 新斜切顶点 | 44个使用中的T与N不够正交，最大约.01346 |
| 其余图元 | 21个缺少T；body既有7个退化UV面，眼球新844个，武器784个；缺少T不等于编码零T，仍可能在native生成阶段出现异常 |

局部修复只交`build_tangent_delta.py`与`tangent-delta.json`。以正式PNG b732为参考，按旧T流SHA/原值匹配，已交叉验证raw34：两组T流共48行、实际380字节；清理已知零向量并正交化44行，W和其他属性/JSON不变，没有写出GLB。修复行最大|N·T|约3.44e-8，全部使用行≤1e-3；没有擅自重算约27k个原量化误差行。

该delta仅证明已知编码缺陷在内存修复后消失；日志没有mesh ID，眼球/身体等生成阶段风险仍列出。**Root原生A/B启动前不得写成告警已解决。** 优先在新v3 PNG合成副本应用局部T候选，再做材质PNG/KTX对照；raw34不直接修改。

## 验证、冻结与后续

- 本地资产测试：原头脸46、连续颈10、皮肤/PBR47、切线9，共112项；不替代画面或原生验收。
- `verify_frozen_candidate.py`校验34ce与82验收文件；`skin-bake/delivery-freeze.json`冻结本轮两PNG、遮罩、材质delta和切线delta。
- 全过程保留其他并行修改，不调用旧v2 producer、不加fallback、不写Root公共Python/app/正式library、不运行共享构建或设备、不操作Git。
- 下一项由Root执行新v3实际组合下的切线日志对照、近距/转头/三攻压力、原生光照和SpacePro性能；本轮微表面实物已收束，不继续诊断已关闭颈几何。
