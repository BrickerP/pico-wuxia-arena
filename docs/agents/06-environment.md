# 06 · 雨夜酒馆庭院整体场景

## 当前下一任务：主门实木入口首件已交，等待Root审图

实物交接 `ArtSource/refinement/environment-hero/native-entry-finish/handoff.json`。完整私有KTX为 `8c44106f40bf1225e82c46b32c439abeeb0e88c67ab5d232f202b26e291ce151`，PNG为 `dfc6cf82ff58f4f845305eefb9180cf5a9868741b667fe89dec8e9e2cb6db04c`。已实际看1.65m正常前后、侧向梁柱与柱脚图：原细斜撑换为190mm厚曲形实木牛腿/承托与榫槽，两根柱的方向木纹和转角/接石座可辨；正常视距收益较克制，不当整场美术通过。

只拆原主门两根柱76tri和两组括臂550＋20tri，门扇/框、纸窗、铜件、石座、灯笼、台阶、地面和所有锚点保持。十件新增实木闭合且正体积；仅新件做10µm浮点安全焊接/退化溶解、显式三角化和canonical TBN，消除布尔倒角微边在float32中塌缩，未放宽退化检查。9项整场/非目标保护/错误输入/PBR检查全过；两版glTF均0错误，PNG旧4与KTX旧10警告逐项指纹exact，新木构无缺TBN。

整场253296展开tri（原249958，净＋3338），属性VB14868624B、索引1269084B，提交估算121（原119），仍32材质/50图；无新增/改画贴图，不凭≤270k或面数称终端过。`review/{player_1p65,joint_oblique,foot_oblique}_comparison.png`、完整PNG/KTX、可编辑full-scene.blend、复建脚本/输入输出身份/9项保护都在同一目录，非孤立模块。

本路未写正式app/assets/原场景/公共producer/Git/设备；Blender任务已结束，无空转等待。Root下一步实际看图决定是否在统一组合包采用；仍须原生KTX/TBN/7f配光、战斗观感及Space Pro性能/内存/舒适度验收，不扩大到新场景或玩法。

## 当前环境评审与主门木构续派（2026-11-17）

7d970ca4 IBL/7f已真实进入ddac准备态与前两轮/Boss。此前三朝向完整头/双手pos+quat exact对照：2f几乎无可读收益未过；8f有梁柱/石阶层次但灰亮、夜间对比不足且刀面窗格不可读。7f随组合可见，不代表整体配光/材质/Space Pro通过。

native-entry-finish正在同c7/d935完整场景做主门立柱/括臂真实体积、槽口/曲面牛腿/柱脚，门扇/窗/台阶/灯笼/地面/尺寸/锚点/图/光/IBL不动。首件253568tri、32材质/50图、提交估算121（原119），正常视角收益克制、局部190mm曲木厚度可辨；Root未合入，不凭面数过关。

第三个3.5mm细槽导致float32的8个退化三角已被拒绝；作者删除该低价值槽、补显式TBN和非目标保护，只重渲终版after三图，交完整PNG/KTX。不能只交孤立模块或概念HTML，不改正式场景。当前P0仍是Boss架刀，整体场景/动作/特效/音画与终端舒适性均待验。

## Root 当前收件与原生验收边界（2026-11-17）

灯笼完整庭院c7f2e2b2已在当前组合APK实际显示。新 `scene-reflections/scene_reflections_ibl.ktx`（`7d970ca4…`）私有环境反射候选及同条件金属球对照已交，正式IBL未改。源包含实际庭院门窗／灯笼反射结构，尚待Root核线性×4与现有环境强度的配对，再验证原生面向、曝光和实际刀身效果；不能仅凭离线金属球称原生湿石／金属材质已达标。

06本阶段保持封口，Root统一做候选加载和同视角A/B；不新增灯光、场景或布局，不覆盖当前正式庭院。整场视觉与Space Pro性能／舒适性仍未通过。

## 下一制作：实际庭院的反射环境源（2026-11-17）

c7f2e2b2灯笼庭院已获Root实际原生加载审核，旧组合冻结，不再重做灯笼。当前刀面偏黑、湿石高光缺少环境形状，Root确认SceneLighting的StageEnvironmentLighting已实际接入；不能再以“IBL未开启/节点兄弟关系”当根因。实时加灯/阴影会带来新运行成本，本轮选择为同一全局IBL制作真实静态庭院环境源，先证明反射形状收益。

Ownership仅 `environment-hero/native-ground-polish/scene-reflections/` 与06。用固定完整PNG d935d818庭院（与正式c7 KTX已验证等价）和既有夜间灯位，在实际战斗中心约Stage(0,1.4,-1.1)捕获静态环境；不含敌人/玩家手/UI，不加新灯、不改材质/布局/湿石或app。复用当前 `app/src/main/assets/textures/rain_night_ibl.ktx` 的真实格式、轴向/面顺序/mips及仓内 `lookdev/ibl/`、`lighting/stage3/ibl/` 已验证生成链，先核输出模板身份；不造Web预览入口，不把单反射源说成实时镜面或有视差的反射。

45分钟交一个真实场景HDR/最终私有KTX与可复建脚本、线性色彩/亮度分布/面向/头格式/mip检查及输入输出身份。用同相机/材质/曝光/灯对比既有IBL与新IBL的金属球或现dao，需读到门窗/灯色等真实环境形状，不只整体提亮或烘固定高光。不得将显示变换/AgX烘进线性辐射，不用新增补光制造收益。Root另做实际APK A/B与强度选择；本路不写正式IBL/SceneLighting/代码产线/Git/设备。你不独自在仓库，保留他人修改，Blender仍走共享锁与有界队列。

## 实际庭院反射环境源：私有KTX候选已交（2026-11-17）

本合同已完成并封口，唯一目录 `environment-hero/native-ground-polish/scene-reflections/`。私有候选 `scene_reflections_ibl.ktx`，SHA256 `7d970ca40ea1660d5514b632b9b3e2e234fe471ac60f13711d486b6174489312`，状态 `private_scene_ibl_candidate_for_root_native_ab`；正式 `app/src/main/assets/textures/rain_night_ibl.ktx` 与SceneLighting/app均未改。

- **真实来源/线性边界：** 固定完整d935 PNG庭院在Stage `(0,1.4,-1.1)` equirectangular 1024×512捕获；静态GLB且没有NPC/手/UI，复用既有stage2夜灯/原灯笼位置、不加捕获灯。原始EXR保留，Standard/None/exposure0/gamma1输出32bit线性EXR。原HDR峰值1.027在cmgen预滤后落到严格KTX阈值以下，故另存一个严格线性×4单位归一化HDR以保方向/色彩比例；不是AgX/显示变换、固定高光、补灯或最终原生强度选择，Root仍控制IBL exponent。
- **KTX/面向：** 复用正式模板格式和已验证cmgen链：KTX1规范头、128方形面、六面、四级预滤mip、SH元数据、packed11/11/10 HDR。cmgen原始产物仅重写三个模板既有头字段，offset64后的SH/mip payload逐字节不变。默认mirror未关闭，面向仍交Root原生A/B。所有线性值有限、峰值3.1875；截断KTX错误输入被验证器拒绝。
- **真实形状收益：** [旧IBL金属球](../../ArtSource/refinement/environment-hero/native-ground-polish/scene-reflections/review/metal_probe_old.png)只有宽暖/冷光斑；[新场景IBL金属球](../../ArtSource/refinement/environment-hero/native-ground-polish/scene-reflections/review/metal_probe_new.png)出现真实门窗格、暖灯色与庭院明暗形状。两图相同金属球/相机/显示/exposure、无动态灯，显示变换只用于探针图且没写进HDR。因此证明的是环境方向/形状，不是单纯整体提亮。
- **验证/收件：** 5项捕获/头格式/六面mip/线性统计/面向模板/探针及负例检查通过。`capture_scene_hdr.py`、`generate_scene_ibl.py`、`render_reflection_probe.py`、`verify_scene_reflections.py`、`REBUILD.md`和`capture_manifest.json`、`generation_manifest.json`、`review/{verification,probe_manifest,visual_gate}.json`、`delivery_manifest.json`完整记录输入/输出/工具身份。Root下一步做私有KTX原生加载、面向与强度A/B；06不再改候选或正式IBL，等待review。

## Root 当前审核与执行合同（2026-11-17）

本节由2026-11-17 Root实物复审更新。Root已核完整组合15项产物身份并采用c7f2e2b2到正式开发场景，在新原生包实际加载并取图；两盏圆润纸罩、连续肋/收口和穗已可见，正式32材质/50图及249958tri保持。完整画面为 `artifacts/native-right-lantern-2026-11-17/native-stage.png`。这只证明加载/显示；湿石反射、整体夜间配光、帧率/内存与Space Pro品质仍未通过。

下一轮Ownership仅 `lantern-hero/refined/surface-finish/composition/` 与06：用不可变bd5d21ef庭院和c2ae86e模块，按清单精确拆旧、原两实例矩阵和材质映射组合完整私有PNG/KTX GLB。复用既有正式KTX编码链；material10只更新指定纸图绑定，32材质/50图，<=250k展开tri，非灯笼几何、湿石图、所有锚点、布局和灯不变。输出可复建脚本、输入/输出身份、结构/预算与非目标不变检查（正常及错误输入负例）、1.65m正常前后图；不要再修改单件外形或表面参数。

30分钟首件。不得写app/正式GLB/公共producer/Git/设备，Root审核后统一装包。几何预算与离线PNG不能声称原生反射、流畅度或Space Pro性能通过。你不独自在仓库，保留其他人的修改。

## 灯笼纸罩表面：完整私有PNG/KTX组合已交（2026-11-17）

组合合同已完成并封口，唯一输出在 `lantern-hero/refined/surface-finish/composition/`。私有KTX完整候选 `courtyard_lantern_surface_ktx.glb`，SHA256 `c7f2e2b2833cdd84fbc73918fdcd2f9036dee582a46c29d8db67df806e77fc78`；同像素PNG完整复核场景 `courtyard_lantern_surface_png.glb`，SHA256 `d935d8185dff6750838bc1d5d98c0b1f07bdce4b0a25249e42957bc501fbe06d`。状态 `private_full_composition_candidate_for_root_review`，不是正式app替换或设备通过。

- **精确组合：** 从bd5d21ef正式湿石KTX庭院拆旧前门木2936、铜504、纸960三角，只在两份相同module mesh上建立左/右实例矩阵。material10仅变更baseColorTexture/emissiveTexture为texture41，image41替换为新增纸纤维图；MR39与normal40保持。KTX texture41正确迁入KHR_texture_basisu，图/texture表均仍50、材料32；非目标mesh、node变换、湿石图、锚点、布局和灯经检查保持。
- **预算/验证：** 展开249958tri（≤250k）、唯一182694tri、属性VB14499504B、索引1208868B、提交估算119。5项组合检查含正常输入与错误sha负例、材料/图像绑定、非目标字节/节点不变、精确拆旧/新增、tangent/退化/无灯检查，全部通过。PNG/KTX GLB validator均0错误；KTX10条提示来自KHR扩展/继承资源，不是阻断错误。KTX fiber为1024×512 UASTC/Zstd、11mips，既有官方编码链与实际map hash在 `composition_manifest.json`。
- **图与边界：** [1.65m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/review/eye_before.png)、[后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/review/eye_after.png)。PNG预览是完整组合场景；正式bd5 KTX无法由Blender导入，故预览输入为已验PNG等价5619，不证明KTX加载、原生反射/照明、性能、内存、碰撞或Space Pro。当前角色身份变化，双方图均不加载角色，避免混旧actor。
- **Root收件/停止：** `compose_lantern.py`、`verify_composition.py`、`render_composition.py`、`REBUILD.md`、`composition_manifest.json`、`review/{verification,png_gltf_validator,ktx_gltf_validator,render_manifest,visual_gate}.json`及`delivery_manifest.json`完整钉输入、输出和边界。Root后续仅需私有KTX候选原生加载与灯光检查后决定；06不再改该组合、模块、湿石或正式源，等待review。

## 灯笼纸罩表面首件：离线可评审，等待Root材质绑定/组合（2026-11-17）

本合同已完成并阶段结束，唯一新目录 `lantern-hero/refined/surface-finish/`。模块 `lantern_surface_module.glb`，SHA256 `c2ae86e490ef4fb56a6111ff1bbc6ee693262c1e44ab2a4e890d472062d89c4a`，状态 `offline_surface_finish_candidate_for_root_composition_review`。正式bd5d/app/湿石KTX、灯位、Stage和0268模块均未改。

- **表面实际变化：** 纸罩沿环向48段、纵向17圈重建并启用平滑法线，消除0268局部图中明显的纵向硬折；12根连续竹肋/圈帽仍锐边。新图仅一张程序派生的1024×512中性纤维图，来自既有纸baseColor image38，纵向微纤维和低频透光不均因子0.979–1.020，无AI/外部下载、固定高光、反射或全局发光。
- **Root组合要求：** 以相同两实例/拆旧范围组合，并在material10中把baseColorTexture与emissiveTexture绑定这张图、替换既有image41 payload；MR/normal保持。不得把模块预览材质新增为第33个材质。正式材质计数/图片计数保持32/50，纹理绑定细节在 `module_manifest.json` 与 `delivery_manifest.json`。
- **预算/检查：** 单件5500tri、双实例11000；替旧4400，净+6600，计划组合249958展开tri，低于250k。3项结构/法线/UV/tangent/材质/预算检查通过，模块validator0错误/0警告。正式bd5为KHR_texture_basisu，Blender不能导入，所以同机位图采用验证过的PNG等价场景5619，明确不是KTX加载或设备证据。
- **图与收件：** [1.65m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/review/eye_before.png)、[后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/review/eye_after.png)、[0.5m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/review/close_before.png)、[后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/review/close_after.png)。当前角色身份在Root重导期间变化，双方图均排除角色而不混旧版本。`make_paper_fiber.py`、`build_surface_finish.py`、`verify_surface_finish.py`、`render_surface_finish.py`、`lantern_surface_editable.blend`、`REBUILD.md`和`review/{verification,module_gltf_validator,render_manifest,visual_gate}.json`可复建/审核。Root验实际KTX、材质绑定和端内配光后再定；本路不再改参或重渲。

## 正门灯笼圆润精修：离线可评审，等待Root组合（2026-11-16）

本合同已完成并阶段结束。唯一新目录 `native-ground-polish/lantern-hero/refined/`，正式bd5d21ef/app不改。模块 `lantern_refined_module.glb`，SHA256 `0268b056a20422ce439a9bb8720776a0760e733a09193d19a43c87db37ddd3e2`，状态 `offline_refined_module_candidate_for_root_composition_review`；不自行组合或替换正式庭院。

- **构造与限制：** 48段连续曲率纸罩、12根连续扫掠竹肋、四圈收口、顶/底帽、闭合挂耳、短悬绳、穗结/五束流苏；肋端实际接入圈体，没有尖刺悬空。无新图或材质，复用paper10/wood0/bronze7/rope24，不加灯/透射/全局发光。模块按现有两实例/灯锚原位：左/右Stage `[-2.15,2.70,-4.78]`与`[2.15,2.70,-4.78]`。
- **预算/拆旧：** 单件3748tri，双实例7496tri；精确替旧前门木2936、铜504、纸960，共4400tri，净+3096，计划组合展开246454tri，低于250k。32材质/50图不变。正式KTX场景当前为bd5d；Blender不能导入KHR_texture_basisu，离线预览只用同湿石map、非图像语义对应的PNG场景5619，明确不作为KTX加载证明。
- **视觉与验证：** [1.65m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/review/eye_before.png)、[后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/review/eye_after.png)、[0.5m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/review/close_before.png)、[后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/review/close_after.png)。正常距离可读圆润轮廓/肋，局部可读帽、圈、肋、底收口和穗；挂耳/短绳保在原前檐下，部分被梁遮挡，不用移位或加灯强显。当前角色重导使身份变化，图中双方均排除角色，未混旧actor。4项结构/预算/UV/tangent检查通过，模块validator0错误/0警告。
- **Root收件：** `module_manifest.json`有矩阵、材料映射、包络和拆旧选择；`lantern_refined_editable.blend`、`build_refined_lantern.py`、`verify_refined_lantern.py`、`render_refined_lantern.py`、`REBUILD.md`可复建；`review/{verification,module_gltf_validator,render_manifest,visual_gate}.json`与`delivery_manifest.json`钉全部身份和边界。Root后续组合bd5d并验实际KTX/端内照明；本路不再改参、重渲或造第二版。

## 正门灯笼模块首件：离线可评审，等待Root组合（2026-11-16）

湿石KTX候选继续冻结，Root另验APK；本轮只交一件可复用正门灯笼模块，不改正式96c554/app/公共producer/设备/构建/Git，不扩场景、不加灯、不做全场替换。目录唯一为 `ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/`。

模块 `lantern_hero_module.glb`，SHA256 `178d1bfc1d68461be6aa6deb33507214d2179bef6d7b0d37c719bd3eed0f283b`，状态 `offline_module_candidate_for_root_composition_review`。它不是第二庭院，Root只能按 `module_manifest.json` 的identity矩阵在正式96c554中各实例一次：左 `[-2.15,2.70,-4.78]`、右 `[2.15,2.70,-4.78]`。

- **实体构造：** 纸壳、十根三段木肋、四道顶/底收口圈、顶底帽、闭合挂耳、短悬绳、穗绳和五束流苏均为实体。只复用material10纸、material0木、material7铜、material24绳；没有新图、材质种类、全局发光、透射扩展或灯。模块局部包络X/Z±.267m、Y[-.626,.739]m，保原吊挂位置和原灯色/光源锚点。
- **拆旧/预算：** Root组合时只移除node7/mesh6的前门木/铜组件和node8/mesh7的两片前门纸罩，保持其他两盏。旧前门组件4400tri，模块双实例2856tri，净−1544；预览组合展开241814tri，低于250k。32材质/50图与Stage/净空不变。实际source选择范围、源材质索引与矩阵均写入 `module_manifest.json`，不允许按近似AABB误删其他灯笼。
- **同机位证据：** [1.65m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/review/eye_before.png)、[1.65m后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/review/eye_after.png)、[0.5m前](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/review/close_before.png)、[0.5m后](../../ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/review/close_after.png)。后图仅在内存中以正式96c554删除两盏旧件、导入模块两次，未输出或替换整景。正常距离能读肋/收口；局部图在一次取景修正后可读顶帽、圈边、肋、底部和穗。挂耳/短绳实体存在但被保留前檐部分遮挡，未为强显另加灯或移位。
- **验证/边界：** 5项模块检查通过，finite/退化/UV/tangent、既有材质绑定、局部包络、双实例预算和原灯锚点均核对；validator0错误/0警告。`lantern_hero_editable.blend` 与 `build_lantern_module.py` 可复建；`REBUILD.md`、`review/{verification,module_gltf_validator,render_manifest,visual_gate}.json` 和 `delivery_manifest.json`完整记录输入/模块/预览身份。离线图不等于设备显示，不证明纸透射、原生点灯、性能/内存/Space Pro、碰撞或正式合入；等待Root组合和原生review，不再参数扫或制作第二版。

## 湿石材质首件：离线接受，待Root原生KTX复核（2026-11-16）

本轮是材料首件，不恢复11月15日的2mm地形/积水实验；绿斑候选 `b0bf…` 继续冻结且不得整合。当前正式庭院仍为96c554，Root独占app/正式GLB、构建、设备与Git。本路只写 `ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/` 和本交接，未动其他资源。

完整私有KTX候选 `courtyard_wet_stone_ktx.glb`，SHA256 `bd5d21efc71799cabe85681bc8ca5d32856c5604158bc19919da6c617a259667`；完整PNG复核场景 `courtyard_wet_stone_png.glb`，SHA256 `5619ce1cc910622da40d2a53ef3341a06aced58b2b94b148fd96bee5f7b63392`。状态是 `offline_candidate_for_root_native_material_review`，不是正式替换或原生放行。

- **实际更改：** 只替换material8 `EH Stone | walked granite` 的嵌入baseColor和MR两张图为各1024²；原法线仍保持，R/B通道保持，MR仅改G粗糙度。中性潮湿暗化和连续粗糙度分区来自现有Granite Tile纹理，未烘焙固定灯/反射、未画绿色斑、未做镜面塑料；正常/近景能读出非均匀潮湿、现有石粒和浅沟缝。无新灯、布局、几何、水面、材质种类、节点或路径变动。
- **同机位证据：** [1.65m前](../../ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/review/eye_before.png)、[1.65m后](../../ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/review/eye_after.png)、[0.5m前](../../ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/review/close_before.png)、[0.5m后](../../ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/review/close_after.png)。实际完整PNG GLB重导入、同相机同既有stage2夜灯，当前6649302a PNG／f6bc15d6正式v5/commonGrip对手idle@0、Stage(0,.028,-2.4)。离线PNG图不是KTX已在PICO加载的证据；KTX与PNG使用同两张map，KTX需要Root实际APK加载再验。
- **纹理来源/压缩：** 现有material8嵌入图来自Poly Haven Granite Tile（Charlotte Baglioni，CC0），本地出处在 `ArtSource/tavern/README.md`第22–25行；无新下载。两张新图、源图hash、算法、像素统计和许可写在 `texture_provenance.json`。KTX复用仓库官方KTX-Software4.4.2 Darwin arm64链：UASTC quality3、Zstd18、2线程、11层完整mip；两图均经 `ktx validate --gltf-basisu --warnings-as-errors`。`KHR_texture_basisu`只用于texture10/11；其余48图仍为原PNG。
- **验证与预算：** 五项独立测试通过：正式96c554输入、所有node/mesh/geometry/布局逐字节不变、只两张image/texture绑定可变、32材质/50图、原法线不变、1024map非均匀/中性/roughness边界、KTX header/mip和无运行时内容。PNG GLB validator0错误/4继承切线警告；KTX GLB validator0错误/8条警告（含KHR_texture_basisu的工具不支持提示与既有切线提示）。展开243358tri、唯一181594tri、属性VB14113296B、索引1175868B、提交估算111均和96c554完全相同；PNG文件38,774,920B，KTX文件39,413,100B。文件/纹理字节不是PICO GPU内存或性能实测。
- **明确边界：** 当前既有离线灯没有可靠的亮反射，不能从roughness数值或PNG推断端内湿石高光。Root下一步仅需KTX候选实际APK加载、近地面材质/切线/IBL检查及内存日志；不要加新灯来制造离线收益。没有碰撞/navmesh、Stage/战斗净空或Space Pro性能通过结论。
- **复建/清单：** `build_wet_stone.py`、`verify_wet_stone.py`、`render_wet_stone.py`、`REBUILD.md`；实际校验在 `review/{verification,png_gltf_validator,ktx_gltf_validator,render_manifest,visual_gate}.json`，完整输入/输出/许可/依赖hash在 `delivery_manifest.json`。等待Root review，不再做参数扫或第二版本。

## Root实物评审与下一步（2026-11-16）

已实际看1.65m新路面图，认可b0bf视觉拒绝：两处绿斑没有形成可信浅水，2mm微起伏在正常距离收益不足。正式96c554不变，技术13项通过不转为采用许可，拒绝件封存。

已续派wet-stone-material单一材质首件：几何／布局／Stage不变，在现material8石材上制作有纹理依据的非均匀潮湿／粗糙度／微法线，允许最多两张1024新图及mips，复用现KTX链；不加叠水面、新灯或烘焙固定反射。完整私有GLB及同机位前后图供Root选择，Root另验端内材质配光。45分钟单首件，最多一次定位修正，不参数扫。

## 湿石路首件：视觉收益不足，停止（2026-11-15）

本轮已在单一首件窗口内完成完整GLB、同机位1.65m眼高/0.5m近景、一次定位修正及自审。结论为 **不建议采用，停止制作，正式96c554不变**。不再重复路面返修、立面、合批或渲染。下方Root规划是本次已执行的输入，不是继续迭代指令。

唯一制作目录 `ArtSource/refinement/environment-hero/native-ground-polish/`。完整失败首件 `courtyard_ground_polish.glb`，SHA256 `b0bf9fe79487aae1c4159be3e54bf93c721153dd9b3a5d5c1264745d7332e880`。`delivery_manifest.json` 的状态为 `visually_rejected_stop`，采用建议 `do_not_integrate_keep_formal_96c554`。这不是正式资源或原生放行件。

- **视觉门槛未达：** 原路面本已有6mm倒角。新2.05mm顶面微起伏、边缘变化在正常眼高收益过弱；复用现有不透明浅水材质形成绿色均色色块，不能据低roughness数值声称有可信浅水反光。初版锯齿水斑已拒绝；唯一一次修正将水缩为两处约0.051m²小洼地、轮廓按几何等高线平滑、移向现有灯的反射位置，最终仍像硬色斑，因此不继续。
- **直接对照：** [1.65m前](../../ArtSource/refinement/environment-hero/native-ground-polish/review/eye_before.png)、[1.65m后](../../ArtSource/refinement/environment-hero/native-ground-polish/review/eye_after.png)、[0.5m前](../../ArtSource/refinement/environment-hero/native-ground-polish/review/close_before.png)、[0.5m后](../../ArtSource/refinement/environment-hero/native-ground-polish/review/close_after.png)。实际完整GLB重导入、同相机同既有灯、当前6649302a PNG／f6bc15d6正式对手idle@0，Stage(0,.028,-2.4)。非PICO截图，未混用13日旧1cc/6ca角色；原生手刀/UI/另挂武器不参与。
- **几何/来源：** 原路10整砖，保错缝与位置，范围2.09×1.99m（X[-1.195,.895]、Z[-2.295,-.305]）；每块拆原上表面/上倒角14tri，共拆140tri。原侧底30tri/砖、未选路石、非地面、全部原node及变换、receiver/anchors/战斗净空保持。新水石共边界分割、无旧top或水面叠面，水高.55mm、最高石面2.05mm。原material8石材/0.65m UV与material12浅水复用，32mat/50图/texture表及50图payload完全相同，无新图/材质/灯/地图/依赖。
- **技术通过不等于视觉采用：** 13项测试通过（含错误水高/非法索引/截断GLB/重叠拒绝等负例），官方validator0错误、4条继承切线警告。原StageY0/NPC+.028与原生代码未改，没有碰撞/navmesh/通行或Space Pro性能证明。Root独占正式app/资源、设备、构建和Git，本路均未改。
- **复核材料：** `build_ground.py`、`verify_ground.py`、`render_ground.py`、`save_editable.py`、`courtyard_ground_editable.blend`、`REBUILD.md`；`audit.json` 和 `review/{verification,gltf-validator,render_manifest,visual_gate}.json`。初版拒绝图名为 `review/rejected_water_paint_*`，只作失败证据。完整清单与依赖SHA在 `delivery_manifest.json`；只保留一个最终失败首件GLB，不推荐Root切换正式资源。

| 完整GLB统计 | 96c554正式源 | 本轮拒绝首件 | 净变化 |
| --- | ---: | ---: | ---: |
| 节点展开三角 | 243358 | 246242 | +2884 |
| 唯一mesh三角 | 181594 | 184478 | +2884 |
| 唯一属性VB字节 | 14113296 | 14548752 | +435456 |
| 唯一索引字节 | 1175868 | 1236348 | +60480 |
| primitive×node估算 | 111 | 112 | +1 |
| 材质 / 图片 | 32 / 50 | 32 / 50 | 0 / 0 |
| 文件字节 | 38212212 | 39187436 | +975224 |

保留源BIN中未活跃旧数据，不声称做了GC；统计不是设备VRAM/drawcall实测。`review/visual_gate.json` 已绑定实际仍为96c554的正式app资源SHA，明确停止状态。

## Root下一阶段规划（2026-11-15）

下一单一首件为现庭院前方2×2m近景湿石路倒角／接缝／浅水层次，保布局／米制／战斗净空，最高0–3mm，≤250k/32材质/50图。 45分钟单一首件，最多一次定位返修；仅各自制作目录／本交接，Root统一正式资源、构建、设备与Git。

## Root本轮整合review（2026-11-15）

本轮courtyard仍为已批准96c554，无新环境改动。Root已在新713532c0…角色动作／commonGrip左手组合的PICO Emulator场景中再次看到同一酒馆、地面和立面；环境成本／Space Pro与整体品质仍待实测。保持已交单一courtyard与制作源冻结，下一轮按实际战斗片的近景木作／石材可读性再定向续派，不扩地图。

## Root收件：96c554进入原生开发整合（2026-11-13）

Root已实际看正常眼高整景与入口近景：门框退让、门扇边挺横档/止口、环把手、柱础与门槛有可见体积收益。接受96c554替换唯一正式开发courtyard，已在8ac1a78源码对应d1b61cb APK的实际Full Stage图显示；图与身份在ArtSource/refinement/presentation/native-blade-contact-stage-2026-11-13.png/json。切线细观、终端成本与整体品质仍未通过。保持StageY0、NPC+.028、原9窗与32材质50图；没有新增门交互/navmesh或承诺可通行。06冻结本件，不重复渲染/合批；后续据Root原生真实问题继续。

## 当前原生任务：中央入口真实构造（2026-11-13）

用户/Root最新授权覆盖旧阶段冻结，但不重开静态合批实验。唯一新工作目录 `ArtSource/refinement/environment-hero/native-fight-entrance/` 与本交接；以正式64da为输入，保九窗、原点、门洞路线、地面receiver、StageY0、NPC+.028及战斗净空。只重建中央双门/门框/门槛/柱础/檐下连接，移除被替代旧盒/贴片，不叠壳；材质≤32、图≤50，展开≤250k。不新增灯/地点/NPC/Web。Root独占正式app/producer/构建/设备/Git，其他编辑保留。

本轮已交完整庭院候选、可编辑分件源与同机位图；首交超过45分钟目标，耗时在整景装配及接合/截面修复。只做入口授权范围，未重开静态合批、未改正式app/producer/构建/设备/Git。Root可直接核下面同一包，随后决定是否替换唯一庭院并做原生验证。

### 当前入口收件：96c554（离线通过，未原生放行）

前缀 `ArtSource/refinement/environment-hero/native-fight-entrance/`。完整单一庭院 `courtyard_native_entrance.glb`，SHA256 `96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d`，38,212,212B。冻结输入64da保持；制作模块SHA `15af03d653db4e6906236dfbc8f36cbba4cf01dd15882adbb18a03df2d6dc264` 只用于复建，不能作为第二运行场景。

- **直接看图：** [正常眼高前](../../ArtSource/refinement/environment-hero/native-fight-entrance/review/eye_before.png)、[正常眼高后](../../ArtSource/refinement/environment-hero/native-fight-entrance/review/eye_after.png)、[同一处入口近景](../../ArtSource/refinement/environment-hero/native-fight-entrance/review/close_after.png)。均为实际完整GLB重导入的离线图，主眼高Stage1.65m、同灯同相机，包含当前base对手1cc9 PNG／正式6ca对应，idle@0、Stage(0,.028,-2.4)、scale1。没有混用旧ac7/b3角色；未冒充PICO截图、未补旧刀/UI/玩家手刀。相机与全SHA见 `review/render_manifest.json`。
- **真实构造：** 上芯纸后无满门板；实体框梃/横档/五块下芯板、棂条半搭接、左右镜像止口、右梃开槽与左门压缝、贴框环把手、内退门套、斜顶窄槛、收分柱础与插口、实心斜撑承托。门槛在内退门正下，最大65mm，门中心净缝14.19mm。斜撑木纹方向8面抽检dot最低0.999999999999972；主木纹0.8m/端纹0.25m。
- **已拆旧：** 旧两门/上格/纸芯/把手1976tri及旧压条/局部corbel/brace/pad/caps/keys，旧两柱础、埋没两踏步；只裁指定长台基中央段、低横梁中央段及两主柱底端。台基两处可见裁口补8点原倒角截面，消除黑洞。酒字、九窗、墙体、地面receiver、锚点、原点、原有node变换与战斗净空经最终GLB比对保持。
- **可复建：** `entrance_editable.blend`保留命名分件；`build_entrance_module.py`→`build_candidate.py`→`verify_entrance.py`。完整命令及既有helper依赖见 `REBUILD.md`，文件/源码/输入/图片身份清单见 `delivery_manifest.json`，实际拆旧选择见 `audit.json`。只有既有材料与图复用，无新依赖。源BIN保留部分已不引用的旧数据，未把未活跃旧字节说成已做GC。
- **最终验证：** builder裁剪/全移除/严格边界自测通过；7项独立整景检查通过；官方validator0错误，4条均为原场景继承的运行时切线警告。新增四个需法线贴图的primitive在合景时补T，最终新几何无退化面/非有限属性。50图payload逐字节相等，32材质与texture表完全相同。证据在 `review/verification.json`、`review/module_audit.json`、`review/gltf-validator.json`。

| 完整GLB预算 | 64da | 96c554 | 净变化 |
| --- | ---: | ---: | ---: |
| 节点展开三角 | 235746 | 243358 | +7612 |
| 唯一mesh三角 | 173982 | 181594 | +7612 |
| 唯一属性VB字节 | 13808688 | 14113296 | +304608 |
| 唯一索引字节 | 1136412 | 1175868 | +39456 |
| primitive×node提交估算 | 109 | 111 | +2 |
| 材质 / 图像 | 32 / 50 | 32 / 50 | 0 / 0 |
| 文件字节 | 36954180 | 38212212 | +1258032 |

预算符合≤250k/32/50；VB与提交为GLB统计，不是VRAM或SDK实际drawcall。`optional_blocker_bounds.json`只交Root参考：门仍是关闭视觉门，没有添加碰撞/navmesh/门交互，不能据造型宣称通行通过。StageY0与NPC+.028保持；APK实际显示、切线观感、碰撞/路线、Space Pro性能仍未由本路验证。


---

## 前阶段收件（原冻结只约束其原件；不覆盖当前入口授权）

### 已结束合批阶段：Root保留64da，备选冻结（2026-11-13）

Root本轮已实际验证正式64da＋v9/手v2三轮通关，干净6.1模拟器未重现前台LMK；目前没有提交瓶颈证据。因此正式courtyard继续保持 `64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605`，不采用静态合批作为本轮正式资源，也不把109→80估算当性能通过。

静态合批 `2f9a877437c19dd23e6c3389a7c9df9f222ed09701dca65801838ef3fd66f96b` 已收为有源、有等价证据的A/B备选，候选及producer/输入保持冻结。唯一属性VB增加5,546,816B（约5.55MB）、文件增加5,355,332B的交换明确保留。未证明LMK来自场景，也未证明此备选改善内存；既有LMK机制与资源压力根因不混同。

本阶段结束，06停止进一步合批、新渲染与新几何，不修改app/producer/设备/构建/Git，也不等待“所有品质通过”才收口。后续仅在实际Space Pro提交或内存瓶颈出现、且Root明确指定时再做A/B。唯一产品仍为Kotlin＋PICO Spatial SDK6.1.9原生APK，PICO Emulator验证，目标Space Pro/OS6；正式发布与Git收口由Root处理。

### 供Root Git收口的精简清单（既有文件，不重建）

前缀：`ArtSource/refinement/environment-hero/facade-polish/`。输入64da及父级helper源码沿既有收件保留，下面是static-batch备选的最小复建/核对链；临时`.log`不作为必要收件。

| 用途 | 文件 |
| --- | --- |
| 冻结输入 | `courtyard_facade_polish.glb`（64da）；既有父级producer/helper来源见本级`delivery_manifest.json` |
| 可复建源码 | `static-batch/build_static_batch.py`、`verify_static_batch.py`、`REBUILD.md` |
| A/B候选与身份 | `static-batch/courtyard_static_batch.glb`、`candidate_manifest.json`、`delivery_manifest.json` |
| 世界/属性/50图字节等价、格式 | `static-batch/review/equivalence.json`、`gltf-validator.json` |
| 唯一一组对照及可复建来源 | `static-batch/render_equivalence.py`、`make_board.py`；`static-batch/review/comparison.png`、`before_static_environment.png`、`after_static_environment.png`、`render_evidence.json`、`board_receipt.json` |

### 已完成备选证据与预算（冻结，不作为继续制作指令）

完整私有候选：`facade-polish/static-batch/courtyard_static_batch.glb`，SHA `2f9a877437c19dd23e6c3389a7c9df9f222ed09701dca65801838ef3fd66f96b`。九窗36项按真实材质和原属性布局合成7primitive，整景提交估算109→80；235746个世界三角逐corner核对，position最大误差2.3835e-7m，NORMAL/UV/已有T及缺失T状态保持。旧窗节点留empty/原变换，旧mesh32/33及无引用accessor/view/旧BIN已清理重打包；32材质、50图原始payload逐图相等。

实际代价：唯一属性VB 13,808,688→19,355,504B（+5.547MB），索引1,136,412→1,640,616B，文件36,954,180→42,309,512B（+5.355MB）。这是提交降低换几何存储增加，不是已证明的内存优化；不能作为LMK根因或解决证据。50图合同包含4个legacy图槽，按要求全部保留，不声称纹理预载减少。Root已决定本轮正式资源保持64da；该备选冻结，正式资源与app未由06改动。

本件完整收件已齐：`static-batch/delivery_manifest.json`、`REBUILD.md`、`review/equivalence.json`、`review/gltf-validator.json`和唯一一组既有机位 `review/comparison.png`。格式0错误、4条原有运行时切线警告；独立审计通过九窗与非窗world几何、node41父链、全部receiver/anchors、50图bytes及资源清理。没有unused mesh/accessor/view，BIN只含存活几何和明确保留的50图及对齐字节，不是向旧BIN追加新批次。

唯一一组实际GLB同灯图未见变形；它只显示静态环境等价，NPC/手刀是APK另载资源，不参与此批次。新合批会损失逐窗culling，且唯一VB/文件增长，所以此件定位提交成本A/B备选；Root已据干净模拟器结果与当前缺少提交瓶颈证据决定本轮不切换；只有实际Space Pro瓶颈且Root明确指定时才重启A/B。当前没有扩窗、降画质或正式发布动作。

## 本次原生检查卡

`ArtSource/refinement/environment-hero/facade-polish/native-review/check_card.png` 与 `check_card.json` 已备。仅用冻结64da的整面/1.5m离线原图加审核框，不新增渲染，不把它当新原生证据。检查仅三项：

1. **远看层次：** 同一稳定READY/guard机位下，九窗内退、分扇、窗台形成整面层次，门洞与人物仍为主，不被重复横带抢走。
2. **瓦口轮廓：** 薄壁瓦口贴屋面，滴水在瓦沟；慢转头无圆钮串、浮缝、闪裂或穿瓦。
3. **贴图/切线接缝：** 灰泥连续、木纹顺构件、转角高光稳定；矩形色块、凹凸反转或视角跳亮需单独记录。4条继承的运行时切线警告保留为观察项。

原生对照需绑定新APK/环境SHA，固定观察路径、眼高、灯光和曝光；避开HIT闪白等瞬态帧。hands/HIT变化不能归为立面收益。

## 当前已交实物与预算（2026-11-13）

路径前缀 `ArtSource/refinement/environment-hero/facade-polish/`。完整单一庭院 `courtyard_facade_polish.glb`，SHA256 `64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605`。图为 `review/comparison_facade.png`、`comparison_near_1p5m.png`（仅两个机位、同灯、当前clean-coat guard准确对应源，离线GLB重导入，非端内图）。复建/来源/预算见 `REBUILD.md`、`candidate_manifest.json`、`delivery_manifest.json`。

1. **整体收益：** 四地层窗＋五上层窗形成统一内退框口、分扇和窗台层次，主体仍优先。上层只调整构件长度，框截面、棂条厚度、止口和半搭接带宽保留，节点scale均1。初版灰色“圆钮串”已回撤，改为贴合原瓦的薄壁半圆口和居间滴水；没有添加地点/NPC/雕像。
2. **共享与零增图：** 四地层节点指同一原核心mesh，五上层节点指同一宽矮mesh。材质/图片/texture三表与9b完全相同：32材质、50图片，零新增贴图和材质。八片墙合为一批，整排59瓦口＋58滴水合为一批；旧112窗件/4928三角、前檐190三角精准替换，门洞/门五金、柱梁、地面receiver、灯位、原点及战斗净空保留。
3. **验证与边界：** 资产结构/共享/裁墙检查通过，格式0错误、4条继承的运行时切线警告。新上层最终float32退化面已清理，切线正交；抽查搭接和闭扇间隙正常。滴水背面顶角逐点与实际源瓦面核对，有约5mm接触余量。独立复核接受最终整图作为Root原生审核候选，不宣称SDK真实合批或Space Pro预算通过。

| GLB资产预算（定义见REBUILD） | 9b | 本候选 |
| --- | ---: | ---: |
| 节点展开三角 | 162206 | 235746 |
| 唯一mesh三角 | 162206 | 173982 |
| 引用的唯一POSITION流顶点数 | 297165 | 332980 |
| 唯一属性VB字节 | 12094176 | 13808688 |
| 唯一索引buffer字节 | 934656 | 1136412 |
| 活跃唯一mesh | 32 | 36 |
| primitive×node提交估算 | 75 | 109 |
| 文件字节 | 34423280 | 36954180 |

几何实例展开增加73540三角，但唯一mesh只增加11776三角；唯一属性VB增加约1.715MB，文件增加2.531MB。以上是GLB数据统计，不是设备VRAM或实际drawcall实测，节点共享mesh不能据此承诺硬件实例化。原生9b输入及正式app未由本路改写；当前人物正式ac7d/PNG对应b3fb双SHA与idle@0均记录在图像收据。Root负责后续正式发布与原生验证，本路保持已交文件冻结。

---

## 历史证据区（以下原合同/限制均已过期，不作为当前执行指令）

保留来源与验收链；当前执行范围只看文件最前的64da合同。

### 历史｜2026-11-13 收口前制作合同（已完成）

Root已原生验证9b在首敌/交战/重开可显示且启动无NO_MEMORY，现解除仅一窗的局部冻结。06仅拥有 `ArtSource/refinement/environment-hero/facade-polish/` 与本交接，沿完整唯一9b院落升级正立面多处窗/木构，并可补近檐瓦当轮廓；旧“不扩第二窗”不覆盖本次续派。正式app/公共producer/其它模型/SDK/Git/设备/共享构建仍由Root维护，多人共仓保留他人编辑，不复制仓库或另开场景。

本轮采用地层四窗共享已审核心（含现有9b窗）、上层五窗共享保持框截面的宽矮变体，零新增贴图；各墙片精确裁洞，保留门洞、柱梁、原点、地面receiver和战斗净空。近檐仅补薄壁筒瓦口/瓦沟滴水并合为一批，避免大量重复节点。先交正常站立眼高整立面同灯前后与1.5m局部、完整GLB及三角/唯一VB/材质/图像/预计绘制预算。构造与少量有效图先行，不以未借到Space Pro停止离线制作，也不将其预算宣称通过。

### 历史｜Root当前原生收件

单窗整景9b已进入正式app资源，并由Root实际安装的1b905包显示，见 [原生准备态](../../ArtSource/refinement/presentation/clean-coat-one-window-2026-11-12.png) 与同名JSON。首敌附着阶段未报NO_MEMORY或新增切线警告。只接受一个结构窗进入唯一courtyard的开发整合；不等于整景美术、全局运行预算或Space Pro硬件通过。保留此件，暂不扩第二窗，不另开场景。


### 历史｜Root整景收件与原生接力（2026-11-12）

Root已实际看comparison_player，完整guard构图中窗框/内退与窗台改进仍成立但较局部克制。9b259812整景接受development integration，Root现在核SHA后替换唯一app courtyard并原生取图。仍不代表整院最终美术或Space Pro通过，不扩第二窗。

本路冻结9b及producer/输入，暂不再造新场景或修未证实故障；可准备该一窗实际材质/法线的对照检查点，Root取到新原生图后按证据接力。主控已恢复active；所有正式资源、构建和设备仍由Root维护。

原生检查卡已备：`ArtSource/refinement/environment-hero/single-window-integration-2026-11-12/native-review/checkpoints.png`与同名JSON。只标注已交9b离线原图，未新增渲染；9b、producer、manifest和取景收据SHA均保持。仅追三点：①墙窗连接/窗台投影可辨且灰泥连续，无矩形色块、亮缝或闪线；②竖框与横框转角的纹理方向、倒角高光在小幅换角时连续，运行时切线的4条警告仍作为原生观察项；③纸复用8b材质4，分扇/遮挡收益出现，人物脸/手/刀仍优先。以同一观察路径、机位、灯光/曝光及绑定9b的新APK图对照，不把旧8b或不同相机单帧当本版结论。

### 历史｜Root review and next production contract (2026-11-12)

用户本次要求继续。Root已实际看图收件：12研究完成；05发髻变光滑蛋形，拒绝；03袖口像深色短筒加浅色粗壳且极限姿态穿插，拒绝；06木窗同光clay有真实进深收益，只接受结构方向，尚未原生放行。本轮正式游戏没有获得有效的人物升级。

下一节点是一个完整刀客上半身。比较三路：旧小补丁收益已不足；反复整人重生成会重置身份/绑定且无质量保证；选择现有Tripo高模、固定身份和明确参考下的完整部件造型。最大风险是缺少造型输入时再把发髻做成球、袖子做成管，所以先形体、再动态、再材质、最后原生。

唯一仓库 /Users/yupeng/projects/personal/pico-wuxia-arena，Kotlin+PICO Spatial SDK6.1.9，Space Pro/OS6。正式b03f人物与8b1098场景仍为基线。你不独占仓库，不回滚他人，不复制仓库，不改pico/BrickerP.github.io。Root独占正式producer/manifest/library/app、Kotlin、共享构建、设备和Git。本轮具体制作继续，不等同恢复24小时自动监控。只改本路范围，研究已交部分不反复写长报告。

Root审核：接受一窗结构方向，整景/原生仍未通过。已实际看1.5m同光clay/PBR，真实洞口、内退框扇和窗台有收益；不代表整院美术达标。

1. 沿当前build_window_sample.py、replacement_recipe.json与8b1098，只做一扇主视窗的完整courtyard候选。移除对应旧14件并精确裁切共享墙，保外侧、其他窗、柱梁、地面receiver、灯位与战斗净空。不要贴回实墙，不新增运行场景。
2. 交一个完整单一庭院GLB及可复建来源，不覆盖正式app/8b输入。合并相同材质/图像，给实际新增三角、材质、贴图与文件成本，避免孤立模块重复带资源。
3. 首交整景含当前人物guard的同机位前后图和1.5m局部。Root亲自替换唯一正式资源、取正常眼高原生图；你不碰设备/Gradle/Git。
4. 单窗在原生正常游戏视距确有收益且预算可接受，才复制到第二扇。如果整景看不出或代价不值，停止扩窗，把资源回到刀客。

本轮交已装配整景候选，不再停在孤立方法样件；只一窗，不整院重做。

#### 整景首件收件（2026-11-12）

路径前缀：`ArtSource/refinement/environment-hero/single-window-integration-2026-11-12/`。

- **完整唯一庭院已到：** `courtyard_one_window.glb`，SHA256 `9b259812a46f07e95dab6b4e4c414521c05118366ed09fca9632bebc51c27dd5`。`build_courtyard.py`可从冻结8b与已接受2fb模块复建；只移除目标窗4框/9棂/1纸及对应墙片，源BIN前缀保留，不新增第二运行场景。正式app和8b输入未改。
- **有效图已到：** `review/comparison_player.png`、`comparison_slight_oblique.png`为完整庭院含当前正式人物对应源的同机位前后；`comparison_window_1p5m.png`为1.5m局部。人物采用与正式722ffe KTX配对的PNG源b732929e…，当前锁定guard为 `idle@0.0s`，Stage `(0,.028,-2.4)`；没有沿用旧e7或attack_overhead待战。图为实际整景GLB重导入的离线对照，不是原生放行。
- **成本与接力：** 153838→162206三角（+8368），31.733→34.423MB（+2.690MB），+1mesh/+3材质/+5图。灰墙/纸直接重用25/4材质，7张墙纸图及1张木normal重用；其余窗、柱梁、地面receiver、灯位与战斗净空保持。Root可对完整单一资源实际装包取图；本轮不扩第二窗，原生收益/预算门槛仍OPEN。

收件校验已齐：`review/verification.json`独立核对原BIN前31657160字节、原accessor/view/material前缀、原节点/变换保持，仅4个源primitive改变；旧窗176/396/44三角按完整14件精确移除，老墙前后各4.4325㎡裁除，中央射线无旧墙残皮。float32边界细线在2e-6m裁切容差内；没有通过放大删除区掩盖接缝。正式PNG对应源与KTX人物的geometry/skin/animation已直接比对一致。完整身份在`delivery_manifest.json`，复建步骤在`REBUILD.md`。

官方`review/gltf-validator.json`为0错误、4条`MESH_PRIMITIVE_GENERATED_TANGENT_SPACE`警告，均指向已接受2fb模块未显式TANGENT的4个normal材质primitive；本候选保留该模块运行时切线生成合同，不将格式检查通过当原生normal保证。Root装包时需看该窗法线/材质响应。完整图中框口、中央分扇和窗台仍可辨，但收益比1.5m局部克制，尚不支持扩窗。图像、候选、当前guard来源与收据SHA一致；本轮只交这一个完整单一courtyard供Root实际取图，正式资源、Kotlin、共享构建、设备和Git均未由本路修改。

---

> 以下为历史交付原文，不构成当前执行指令。

### 历史｜当前状态

2026-11-11 Root已将stage2环境8b109801…df3db7b发布到唯一正式courtyard资源，56bb源与旧producer输入保留冻结。新版native暖纸与灯笼已可见；一次Reset观察图中纸组消失，后续settled与forward帧恢复，有限只读归因未发现可证实资产错误，当前保留8b、不生成correction。实际原生主流程、Space Pro与checkpoint继续由Root负责。

### 历史｜目标

把当前黑背景、平直墙面和大黑缝石块的院落提升为有构图、空间层次和生活痕迹的中式雨后酒馆。参考《黑神话》的建筑与材质，《天国拯救》《骑马与砍杀》的可信空间尺度。以现短场景形成探索片段与战斗区域，玩家站立区和对砍视线清楚。

### 历史｜所有权

负责 ArtSource/refinement/environment-hero/ 与本文件。原场景和03已有environment候选只读作输入，整个环境新方向由你主导。07负责照明／天气运行，10负责UI，你交几何与材质可组合场景，不改HomeStage或正式app资产。

### 历史｜制作队列

1. 读取真实端内图 ArtSource/refinement/presentation/combat-feedback-outcome.png 和 artifacts/ui-input/current-scene.png，确定主视角构图。建立酒馆门楼、瓦檐、木柱基座、石路、墙根、排水与积水的连续结构。
2. 用Blender和现制作逻辑完成真实GLB升级。石板厚度／倒角／缝宽、木构榫接／门槛／瓦片层次要在正常视距可见。纹理采用原有资产或可核对授权来源，给物理尺度、baseColor／normal／roughness。
3. 构建前景灯笼与屋檐、中景对手与门楼、远景雨雾／小镇轮廓。可在侧面加入池水或小桥一角形成记忆点，景观服务同一庭院风格。
4. 湿润、苔痕、污渍和破损有位置原因，低处积水、檐下干区和脚步路径不同。战斗地面以Y=0作为公共基准。
5. 场景按少量有名mesh／material分组，地面receiver与重要灯位给明确节点名。交本地包围盒、米制坐标、实体装配点和可用Root接入说明，远近层分清。

### 历史｜首轮交付

一个明显改善构图和材质层次的真实场景GLB，以及主战斗视角／侧向探索视角各一张前后图。首轮集中做好一段石路和门楼，随后扩相邻屋檐、墙角和水面。

### 历史｜共同执行合同

唯一工程为 /Users/yupeng/projects/personal/pico-wuxia-arena。每次终端调用显式指定该workdir，首先核对git根目录。当前会话所在Home分组只是入口。禁止修改 /Users/yupeng/projects/personal/pico、BrickerP.github.io 或其他仓库，禁止复制仓库、建worktree、切分支、提交或推送。

技术栈为Kotlin + PICO Spatial SDK 6.1.9、Space Pro／OS6、Full Stage。沿用现有GLB、Tripo CLI和Blender制作链。SDK API先查Context7，当前无此工具时查本机官方6.1文档与6.1.9类型。容器、Gradle与SDK版本由Root维护。

其他会话共享同一工作树。只编辑责任范围，保留他人修改。Root统一正式角色producer、manifest、library/app正式资源发布、Main/HomeStage最终接线、构建、设备、截图录制与Git。源资产与候选目录分开，Root按部件或补丁合成。

首轮45分钟内交真实资产、可运行源码或正常游戏视距的可见画面。每路本机最多1个Blender进程，重渲遇资源争用先交模型和已有图，继续可独立的制作。阶段回填本文件的交付区，包含来源SHA、产物路径、可见变化、接入点、限制与下一项。阶段完成后继续本合同已授权队列，不等重复批准，不无限等待其他会话。

判定依据是0.8m／1.5m／3m正常视距下的整体效果。每次给同机位前后图或短片，单独高光图和极端放大近景只能作为补充。构建／导入／面数与参数通过不能代替视觉验收。当前整体效果粗糙、保守，需要正常视距下明显可见的进步。

先开发和专项制作检查，整局自玩后置。Root负责实际输入到共享判定、三轮流程与Space Pro实测。模拟器只作为其实际可证明范围的证据。

### 历史｜阶段交付

#### 2026-11-11 · stage2窗纸、木构与灯笼候选已交

**来源与冻结：** Root指定稳定代码节点 `6b407acc4507812b99d1315e58c8a2c588719fd0`，实际执行开始观察HEAD为 `193d0f6dcc859168b8f7c00669c185a3863e1a8d`；未切换分支或修改Git。任务实图为 `ArtSource/refinement/presentation/integrated-2026-11-11.png`，SHA `c23a267ed6b634a07d22b7193211f05d8420770b1f281830df4ea59216b33f6d`。唯一输入庭院仍为正式 `56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`；候选、正式app文件、旧producer SHA及全部旧贴图SHA均核对未变。

**新文件与显式新SHA：** `ArtSource/refinement/environment-hero/stage2/courtyard_materials_stage2.glb`，SHA256 `8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b`。本轮仅编辑stage2私有目录与本交接；没有运行旧producer，没有覆盖56bb源、旧输入或正式app文件，没有修改HomeStage/SceneLighting/SDK/Gradle，没有构建、设备或提交推送。

**正常距离可见收益：**

1. 23幅独立窗纸（11正面、8侧廊、4远楼）绑定2×2原创atlas，包含细纤维、纸幅接缝、边缘受潮、压框暗边、少数叠纸修补和局部暖斑；不会增加窗格。远楼单独降亮。3m图可读暖斑与纸层差异，细纤维主要在0.8m／1.5m图验证。表面反射factor `[.38,.30,.21,1]`、emissiveFactor `[.42,.27,.10]`，降低反射填光洗平暖斑的风险。
2. 木材沿现有梁柱长轴增强颜色／roughness／normal方向性，原长轴UV保持。为现有18处托木前端补独立端纹，12个锁键嵌入柱面，门内侧3段压边补进深；只加1个命名mesh `EH_S2_TimberJointFaces`，没有扩场景或重复窗格。原全局深色窗棂／灯笼骨架材质3保持字节语义不变，仅主木构局部使用独立浅一档接缝材质。
3. 灯笼使用原创纸面baseColor／normal／roughness及独立emissive图，中腹较亮、上下口压暗、轻微纸厚与贴纸缝变化，既有暗肋保持。emissiveFactor `[.75,.65,.50]`，U首尾逐像素周期一致。夜景图中灯笼从暗红实心感转为暖橙纸腹，和周围暖窗协调。

**文件入口（均在 `ArtSource/refinement/environment-hero/stage2/`）：**

| 用途 | 文件 |
| --- | --- |
| 完整接入候选 | `courtyard_materials_stage2.glb` |
| 资产／UV／新几何／输入身份 | `candidate_manifest.json`、`handoff.json` |
| 私有GLB加工 | `create_candidate.py` |
| 原创纸／灯笼与木材生成 | `make_paper_maps.py`、`make_wood_maps.py` |
| 贴图身份／色彩空间／atlas矩形 | `textures/paper_maps_manifest.json`、`textures/wood_maps_manifest.json` |
| 正常主视角／探索前后对照 | `review/comparison_player.png`、`review/comparison_explore.png` |
| 3m窗纸／灯笼搭接夜景对照 | `review/comparison_paper_3m.png`、`review/comparison_lantern_joinery.png` |
| 1.5m／0.8m纸幅对照 | `review/comparison_paper_1p5m.png`、`review/comparison_paper_0p8m.png` |
| 三距离总览／中性光主视角 | `review/distance_review.png`、`review/comparison_neutral_player.png` |
| GLB与图片专项证据 | `review/validation.json`、`validation.log`、`neutral_evidence.json`、`night_evidence.json`、`board_receipt.json` |
| 07原生点灯接口事实 | `light_contract.json` |

**Root／07接入合同：** 接受时按新SHA选择这份完整候选替换统一场景资源，不与56bb叠加；原点identity、米制、原命名receivers与所有灯位保持。旧BIN前18619512字节、原POSITION/NORMAL/indices、全部原节点变换均保持。PBR仍走core glTF，图片均内嵌；baseColor和emissive为sRGB，normal/MR为linear，切线已按新UV补算。没有引入材质透射扩展、运行灯光或假光池贴片。发光贴图只表现美术亮度变化，不是物理透射，不会代替真实照明。

07当前四灯线性RGB `(1,.49,.20)`：主门 `(-2.15,2.7,-4.7)`／`(2.15,2.7,-4.7)` 为1500lm、半径3.8m；侧灯 `(-4.03,2.25,.56)`／`(4.03,2.25,-1.32)` 为1100lm、半径3.4m。均距纸壳中心向玩家侧约8cm，候选没有移动它们。真实光池与阴影由Root/07用原生点灯验证；GLB emissive值与lm不在同一单位，不能直接按数值比例承诺亮度。夜景离线图优先保留人物脸与手高于大面积门纸的视觉层次。

**验证：** `python3 ArtSource/refinement/environment-hero/stage2/verify_candidate.py`，10项全通过。覆盖冻结输入与正式app不变、候选身份与原BIN精确保留、旧几何/transform/anchors不变、Y=0与战斗净空、23纸幅atlas/米制尺度/V方向、normal材质显式TANGENT的有限/单位/正交/handedness、opaque/core emissive、未增加窗格、灯笼周期接缝、错误或缺失源输入的实际拒绝路径。

自我review与独立复核修复了两个实际问题：纸倒角退化UV原fallback使dot(N,T)=.707，现最大约1.49e-7；原12个锁键距柱面2mm，已改为嵌入4mm。灯笼新normal图对应1100顶点切线全部有效，最大正交误差1.19e-7、handedness与UV导数一致。最终夜景复核确认纸层暖斑、木纹方向／托木端纹和灯笼纸腹均有可见收益，人物脸、手和持刀姿态仍为视觉焦点。

候选39节点、31mesh、29材质、45张内嵌图、153838三角，相对56bb增加2244三角、1mesh、3材质；大小约30MB。地图新增包含2K纸幅atlas，实际头显纹理内存及加载／帧率仍需Root核对，当前没有端内性能结论。

所有before/after均导入实际GLB，使用相同正式 `opponents/base.glb` SHA `e7f3de3d8c7e202999b2d456ae85257b89a01e7c21792f332c4b273c77b60cbc`、`attack_overhead @0.0s`、Stage `(0,.028,-2.4)`、同一机位/灯光。离线眼高1.6m是制作机位，不冒称设备实测HMD位置。中性光与夜景均有完整图像SHA；并列图仅加边框/文字，三距离总览仅缩排版尺寸，没有修补渲染像素。Blender灯功率是受控对照配方，不冒称与PICO流明数值等价。

**剩余验证与下一步：** 正式场景仍为56bb，stage2只交Root选择。需要Root/07接入后检查PICO实际emissive/normal响应、灯笼纸面与真实光池、人物/门洞亮度层次、侧向遮挡与Space Pro性能。收到实际端内问题再以独立新文件和新SHA续修；当前stage2交付签名及图像身份保持一致。

#### 2026-11-11 · 首张PICO集成图只读评审

输入为Root实际取得的 `artifacts/integrated-polish/ready-scene.png`，2160×2158，SHA256 `c5a7a7d23c9f99b66fc418bffe01d8fcdc00a8e87a674d723905bbd0cb40186c`。候选与正式app模型只读复核仍为 `56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`。Root反馈原点装配、receiver、天气、IBL及角色10clip已加载；本图能直接证明新建筑与石路已进入PICO画面，不能仅凭单图证明所有角色/动作或运行性能。

**本图结论：** 石板相对鞋长、人物和门洞的物理尺度可信，横向错缝与窄缝可辨，没有证据要求整体缩放铺地。廊檐暗带较厚，但没有遮住对手头部、躯干或门洞；举刀上缘进入暗檐背景，需要后续举刀/侧向图继续确认视线。灯笼骨架已可见。实际瓦片上表面、完整屋脊、远景整体、侧廊进深、池沿和踏步未在本图中充分显示，不能据此宣布它们已完成端内视觉验收。

**只保留两个待选改进，均未实施：**

1. **檐口瓦当／滴水轮廓。** 主视角的连续平直蓝灰边目前比瓦片端头更醒目，建筑细节容易读成一条整齐横带。侧向图确认这是当前檐口几何的表现后，可在保留承重梁、现有檐深和中央净空的前提下，为筒瓦端部和滴水瓦增加可读端面、轻微不齐和局部磨损。只处理檐边可见轮廓，不凭这张图重做未入镜的整片屋顶。
2. **地面湿度过渡与亮缝一致性。** 当前地面仍有较连续、均匀的蓝亮边，远处读成规则网格。先让07完成曝光/IBL/高光收口；若同机位仍如此，再考虑在独立材质候选中为步行中带、边沟低处和檐下干区设置连续roughness过渡及少量逐石变化，减少所有边线同亮的感受。保留现有石板尺度、浅床和窄缝，不通过重新加大接缝或整体改尺寸解决受光问题。

当前没有本图足以证实、必须立即修改几何的阻断项。06本轮仅做图片与源码只读审核、回填本交接，没有修改模型、manifest、贴图、producer、运行代码或正常视距图，没有启动Blender、构建或设备操作。等待Root提供侧向探索图及07完成后的同机位图，再由Root选择是否制作独立新候选；若制作，明确新文件路径和新SHA，冻结56bb签名继续保留。

#### 2026-11-11 · Root已接入，签名冻结

Root通知已将 `courtyard_hero.glb` 发布到 `app/src/main/assets/models/`，HomeStage改为原点identity单加载，旧三场景的运行加载路径和包内资源已移除，原ArtSource源保留；07按本模型灯位继续对齐。本会话只读核对了候选与正式app GLB，两者SHA256均为 `56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`。HomeStage源码已包含 `EH_GroundReceiver`、`EH_MortarAndDrain` 接收节点绑定。

**冻结边界：** 保持上述模型字节、现有manifest及图像身份不变。06不再运行会覆盖 `courtyard_hero.glb` 的producer，不改Root正式资源或接线。后续新几何必须写入独立候选文件／目录，并同时列出显式新SHA及相对已冻结版本的可见变化，再交Root选择；禁止在旧文件名下悄然覆盖已接入签名。当前没有新几何候选。

主视角、侧向探索前后图及0.8m／1.5m／3m常规眼高图均已完成。`candidate_manifest.json`、`after_evidence.json`、`board_receipt.json`、`validation.json` 的模型身份一致；这些图仍是冻结GLB的离线对照，不是本次Root接线后的端内验收图。当前06只完成文档和既有图像完整性核对，没有重生成资产、启动Blender、共享构建或操作设备。

下一步由Root取得实际集成画面，确认原生材质、灯光、阴影、脚底高度及Space Pro性能。06收到定向视觉问题后可继续只读分析；需要新几何时遵守上述独立候选与新SHA边界。

#### 2026-11-11 · 首轮完整候选与专项自检

本轮没有修改正式producer、app资源、HomeStage、Main、Gradle、Manifest或其它会话目录；没有共享构建、设备操作、Git提交或推送。所有实物在 `ArtSource/refinement/environment-hero/`。来源代码节点 `562449af40ee984ddd8ef61be5c339ac9bea2de5`，旧酒馆来源SHA `af3adf8b15bb5aa6f34a9a5240e18bc2534bc977db4a05089a0c3a1ee1bbdc69`。

**可见结果：** 单片门墙已形成双层酒馆与两翼围廊，真实柱脚、木托、木椽和层叠瓦片构成进深；连续薄缝石路覆盖站立与战斗范围，灰缝有浅床，侧边有排水槽、苔痕及低处湿石。门前保留对砍净空，池角以湿石砌边、三块踏石和水面形成侧向记忆点。四只纸灯笼有暗色竹肋和独立灯位；茶桌、酒坛、青瓷与石盆复用旧场景已制作的精细道具。较高的相邻镇屋檐在主视角与侧视角可见，不再完全藏在主楼后。

| 产物 | 路径（相对本工程） |
| --- | --- |
| 真实GLB | `ArtSource/refinement/environment-hero/courtyard_hero.glb` |
| 可编辑源 | `ArtSource/refinement/environment-hero/courtyard_hero.blend` |
| 私有producer／PBR图生成 | `ArtSource/refinement/environment-hero/build_environment.py`、`make_textures.py` |
| 坐标、模块、灯位、SHA | `ArtSource/refinement/environment-hero/candidate_manifest.json` |
| 纹理来源、物理UV尺度、SHA | `ArtSource/refinement/environment-hero/texture_manifest.json` |
| 主视角同机位前后图 | `ArtSource/refinement/environment-hero/review/comparison_player.png` |
| 侧向探索同机位前后图 | `ArtSource/refinement/environment-hero/review/comparison_explore.png` |
| 0.8m／1.5m／3m常规眼高检查 | `ArtSource/refinement/environment-hero/review/distance_review.png` |
| 实际GLB检查 | `ArtSource/refinement/environment-hero/review/validation.json`、`validation.log` |
| 原道具选择与装配证据 | `ArtSource/refinement/environment-hero/review/props_provenance.json` |
| 前后相机／输入身份 | `ArtSource/refinement/environment-hero/review/before_evidence.json`、`after_evidence.json`、`board_receipt.json` |

候选SHA256：`56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8`。最终GLB含38个活跃节点、30个mesh、151594三角、26个材质与31张内嵌图；这些是装配成本信息，不能代替可见画面或设备性能。

**Root接入：** 本候选是三份旧环境资产的整体替代方案，不是叠加补丁。加载 `EnvironmentHero_Root` 于 SDK `(0,0,0)`，identity旋转、scale=1；移除旧 `tavern_slice.glb`、`forecourt.glb`、`courtyard_details.glb` 的对应场景实例。不能继续给候选平移Z=-4，也不要再同时叠03的旧门套/铺地候选。旧道具已选择性合进新GLB，不会再需要旧details全体。

- SDK为米制、+Y向上、初始视线朝-Z；完整局部/装配包围盒 `min(-10.867,-0.120,-13.2175)`、`max(11.185,11.1773,2.917)`。高处与远处两座屋体属于远景层，中央实际铺地约10.8×9m。
- 战斗石路顶面Y=0，几何专项确认中央 `X[-1.35,1.35]、Z[-3.0,.8]、Y[.05,2.4]` 无装饰三角侵入。现角色脚底Y=.028由Root决定同步归零或保留并注明间隙；06没有改角色落脚量。
- 主地面receiver节点是 `EH_GroundReceiver`，浅床/排水是 `EH_MortarAndDrain`。它们替换旧 `Paving`、`SidePaving_Geometry` 的receiver选择。raised侧廊可按需另选 `EH_SideGalleryWalls`。
- `EH_Light_Lantern_01..04` 为07/Root原生暖点光装配点；精确位置见manifest。主门两灯 Stage `(-2.15,2.7,-4.7)`、`(2.15,2.7,-4.7)`；侧廊两灯 `(-4.03,2.25,.56)`、`(4.03,2.25,-1.32)`。`EH_Light_CourtMoon` 是冷色高位光参考，`EH_CombatClearCenter` 是地面判定参考。GLB不携带运行灯光和相机。
- baseColor／normal／roughness可直接随GLB使用。花岗岩和木材来自项目现有Poly Haven CC0扫描图；屋瓦、灰墙、苔痕为本项目原始烘图，旧酒坛/茶具/灯笼纸图来源继承 `ArtSource/tavern/README.md`，没有新外部素材或付费生成。木纹沿梁柱长轴，墙根潮痕使用有高度含义的UV，法线为OpenGL切线空间。

**验证与自我review：** `python3 ArtSource/refinement/environment-hero/verify_environment.py`，7项全部通过：身份与无孤儿节点、Y=0覆盖、战斗净空、筒瓦外法线、可移植PBR及有限坐标、无运行灯光/相机/动画、截断GLB拒绝路径。前后均使用同一1.6m眼高、18mm/36mm镜头、1200方图、同一受控灯光；after由交付GLB重新导入后渲染，未使用仅存在于.blend的材质。两张并列图只加文字边框，没有修图。旧forecourt的孤儿节点通过既有active-scene过滤排除。

四轮review已覆盖：正确性（修复筒瓦反面并加GLB检查、地面基准、净空）；可维护性（候选只一条producer路径、重用已有道具与过滤器）；体验/i18n（正常站立图、中文“酒”牌、近侧廊光线视线）；漂移（无新依赖、SDK/配置/schema/正式资源变更）。审查指出的远景遮挡、石池误用木材、灯笼椭球、木纹方向已在最终候选中实际修正。

**当前限制：** 图是离线资产对照，不是PICO端内图。原生IBL、水面反射、阴影receiver、生效材质、帧率/发热、Space Pro双眼舒适度尚未验证。水面采用不透明低roughness薄面，未加入折射或依赖特殊透明排序。场景无碰撞或新导航系统；当前固定近身交战入口保持Root现有链路。部分瓦面为薄壳双面材质，筒瓦受光法线已经专项核对。

**已继续的队列与下一步：** 首轮石路/门楼后已继续完成两翼屋檐、墙根排水、池角水面、远景屋檐及三档距离图；当前06制作队列的可独立部分已产出。Root可按上面的互斥替换说明实际装配；07使用命名灯位做原生夜雨光色。下一项有意义的证据是Root接线后的同眼位端内图，06随后据实际光照修材质与遮挡，不以离线图宣称VR体验已完成。

### 历史｜Root组合审核与下一步

已核对完整courtyard_hero SHA56bbd7e4f6f371a9a7d8dbcf10f55777c0b6ec445e0ca0bf1b10c1f47d9af6b8，离线主视角显示建筑体量、连续细缝铺地和庭院层次有可见升级，接受开发集成。Root已发布单一courtyard_hero入口并删除旧三份运行场景，原ArtSource保持。两个实际receiver已绑定，灯位由07按新anchors适配。原生构建与250项组合回归通过，实际画面尚待本轮取图。随后优先按原生图修正材质尺度、瓦檐薄弱处和探索侧景，不再增加同类随机道具。

### 历史｜Root本轮组合审核与续派（2026-11-11）

审核：courtyard_hero已作为唯一主场景实际启动，旧三运行资源已移除；两层酒馆与连续石路可见。

下一步：根据relight-ready-scene实际图集中建筑材质尺度、窗纸与人物亮度层次的最多3个可见改进；不增开放世界或再造并行院落。


### 历史｜Root stage2 开发集成审核（2026-11-11）

Root已实际看主战机位与灯笼搭接两组同机位图，接受8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b作为下一构建来源。仅替换唯一app/models/courtyard_hero.glb，stage1 source56bb与stage2重建输入保留；不叠加场景实例。窗纸暖斑、方向木纹与灯笼纸腹渐层已有离线可见改善，native材质响应、人物亮度层次、实际光池与预算仍OPEN。工程收件在stage2/root_integration_review.json。

### 历史｜06续轮优先级 · Root接受stage2开发集成后（2026-11-11）

Root已实际审核stage2的player与lantern_joinery两张前后板，接受 `8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b` 为development integration候选，接下来由Root统一替换唯一courtyard资源并取得新native图。06从此冻结stage2模型、producer、贴图、manifest及已有图像身份；本轮仅追加本节，没有运行生成器、Blender、构建、设备或Git，没有修改正式资源。开发集成接受不等于PICO画质、Space Pro性能或实机通过。

只读输入为 `artifacts/input-native/aim-post-move.png`，1882×1938，SHA `f0e65d571b7f82a6b5aa9e9044750e8110930f10c7efb3617f7fb1dd2d4beb4b`。它是带模拟器窗口边框和工具栏的原生画面截帧；未取得绑定8b1098的新APK／资源收据，读取时正式app文件仍为56bb。因此该图用于说明已有立面观察点，不用它判stage2成功或失败。目标维度沿用12的现有bench：《黑神话》的建筑材质与构造层次、《天国拯救》《骑马与砍杀》的可信空间尺度；没有新增未经查看的游戏截图或视频结论。

最多保留以下3项优先级，均等Root本次新native证据后才定具体delta：

1. **P1 · 验证stage2材质在实际照明下的可见收益。** 本帧纸面仍是均匀褐片、灯笼暗红，梁柱／托木／椽底较多并成黑带；这三项已有stage2定向制作，不重复新开一套贴图。先用Root的新同机位帧确认局部暖斑、灯笼中腹/口部明暗及顺构件木纹/托木端纹在正常游戏视距出现，同时保持人物脸、手和动作轮廓优先。若效果被原生填光洗平，由06/07只定位现有baseColor、emissive、roughness及灯位的实际贡献，再决定局部参数或贴图delta；不先整体抬亮院落，不增加大贴图。验收关注“纸幅有受光原因、木构能读连接、灯笼纸面与真实光池一致”，不以数值上调当可见通过。
2. **P2 · 可见檐口的端头／滴水层次。** 当前画面里连续冷蓝直边比瓦端构造更易辨认，主檐下方有体量但端头轮廓较弱。先在新native轻微仰视/侧向图分清材质暗部与几何实际轮廓；若仍读成贯穿的平直横板，下一候选只处理现有檐边的筒瓦端面、滴水瓦断续轮廓、局部磨损或受潮roughness，优先复用现有瓦面图与材质。保留檐深、承重关系、已交木椽及举刀净空，不据这张主要显示檐底的图重做未入镜的瓦面和整片屋脊。
3. **P3 · 侧向探索的廊柱—湿石—池沿层次。** 本帧主要是正立面，侧廊深度、石池踏步、水面与远景屋檐未充分展示，暂不判它们失败。等Root在正常眼高取得左右侧向探索图，先检查柱间通透、托木接触、池沿接地、水面亮度与近/中/远材质尺度。若平面感仍在，优先修现有湿石/干檐/墙根的连续roughness与接触层次，或有限可见面的UV/法线；不添重复坛罐/窗格、不扩庭院、不增加第三套院落或大贴图。侧景应继续服务清楚的战斗视线与同一酒馆风格。

本轮没有新增候选或新SHA。stage2的10项检查与对照图是发布前制作证据；其中“正式app仍为56bb”的输入冻结断言属于当时状态，Root将正式app切换为已接受8b1098后，不把这一旧app基线断言当作接入失败。冻结源56bb与已交stage2文件身份仍分别保留，后续实际delta使用独立文件和显式新SHA。

### 历史｜06 native纸面消失有限归因 · 保留8b1098（2026-11-11）

**结论与处理：** 已实际看loaded、Reset后异常、settled恢复及两张forward-controls图。当前没有可证实的资产alpha、背面、法线或包围盒错误；恢复帧阻止把一次观察窗口异常直接判为持续资产缺陷。保持已发布 `8b109801cc268e8194820e22575d6b1415a2b65bcfc52e2bc0a9b415fdf3db7b`，本轮不生成correction，不修改模型、producer、源纹理、manifest或正式资源。确需后续修复时，仅在同stage2下的新private correction子目录交独立delta和新SHA，不覆盖checkpoint来源。

**绑定与时序：** `artifacts/canonical-native/build-identity.json`绑定APK `767bc0afecd9bb40377a736da0466126665e4f03cf52d646b21cb0a9d285c9f2`与环境8b1098；Root报告Android PID15914一致，startup.log亦记录此PID。候选与当前正式app GLB只读SHA均仍为8b1098。以下时间为文件mtime（北京时间），不是GPU帧时间：

| 图 | mtime | SHA256 | 实际可见事实 |
| --- | --- | --- | --- |
| `loaded-head-native.png` | 20:24:17 | `24fd202c2919a081ea41cb21adead1c25784c9b6100853026f96ffc44d552c13` | 模拟器窗口中暖纸、亮斑与完整灯笼纸壳可见 |
| `reset-controller-view.png` | 20:24:57 | `027e56110fa387be050a9727e23386b5209fd78a0920689fa293a80cd984048d` | 视点变化后纸组未显现，可见窗后的蓝灰墙，灯笼独立骨架仍在；不是仅整体变暗 |
| `full-stage-settled.png` | 20:26:43 | `4a04be2b73480dc01c52574ace61fdfd9c347a1d84f9e0ad0c7daf260ffcdb7d` | ordinary2D应用画面中暖纸、亮斑和完整灯笼恢复 |
| `forward-controls-full-stage.png` | 20:39:48 | `395c891c23baf2a1669ec0fcfb4edb737d8475a7dc9125d808182f3e40711ebf` | 等待场景时暖纸/灯笼已可见；此帧没有对手，不将它说成完整游戏加载完成 |
| `forward-controls-loaded.png` | 20:45:11 | `530fcc425a1d0a9cb4477e3cab54fc6c705198cb2444209ad042d78303e39bd7` | 人物与暖纸/灯笼同框正常 |

图均位于 `artifacts/canonical-native/`。模拟器窗口图与ordinary2D图的取景和尺寸不同。reset元数据记录桌面点击、窗口focus和截图，没有HMD/观察相机pose、渲染帧标记或同视点成对捕获；未取得官方证据证明两种捕获相机具体如何关联。不能因此直接认定“Reset Camera渲染瞬态”或“不同观察相机”已是根因。相同PID也不能单独证明SpatialView没有重建。

**只读资产排除：**

- 窗纸mat4、灯笼mat10、远楼窗纸mat26均为 `doubleSided=true`，未指定透明模式/透明扩展，baseColor alpha=1，相关PNG为RGB、没有alpha通道。glTF缺省OPAQUE；无资产级depth override，实际渲染深度状态本轮未采集。
- 相关原POSITION/NORMAL/indices与旧BIN前缀保持，POSITION bounds与真实顶点误差为0。纸面几何法线与顶点法线最小点积约1，灯笼约.91，没有发现反向面；新切线有限、单位、正交，最大误差约1.49e-7，未见反向UV basis。
- 额外CPU几何射线检查选择一幅正面窗纸与一盏灯笼纸壳，各覆盖距离0.8/1.5/3m、眼高0.8/1.6/2.2m、yaw -60/-30/0/30/60/180度，共108样本均命中纸几何。该检查只排除代表性几何在这些角度缺面，不是PICO渲染或全场景遮挡稳定性的保证。

**只读应用调用链排除：** HomeStage.kt:490的SpatialView.update只更新HUD锚点；:550初始化唯一庭院并绑定两个地面receiver，没有按视角、相机或追踪修改纸面材质/alpha/depth/culling/visibility。唯一model.materials写入位于EnemyHitFlash.kt:91，输入仅HomeStage.kt:201的对手实体，BodyFlashMaterial.kt:4又按tripo_身体材质过滤，未触环境。SceneLighting.kt:46的IBL初始化、SceneWeather.kt:40的天气rig及TrackingSession.kt:434的采样生命周期均无环境纸面角度分支。Main.kt:42使用DefaultStage，没有应用自建相机或Reset Camera处理。上述行号对应本轮只读源码，不把它推断为SDK内部实现证据。

startup.log在20:23:38记录Tavern attached，20:23:40出现Assimp `mesh tangents: Found zero-length vector`，20:23:44记录Tripo enemy attached。该警告没有携带可绑定的资产/mesh身份，且环境相关切线实测正常，不能直接归因给纸面；也未据此修改新头或环境。

**剩余证据边界：** 目前支持“有一次观察窗口异常，后续多个应用帧正常”，不支持“已证明alpha/backface故障”或“已修复Reset Camera内部问题”。Root当前主流程和checkpoint继续，06不占GUI/Gradle/设备、不启动Blender、不做大渲染。若后续稳定重现，再有限取同一观察相机的Reset前/后立即/稳定后帧，并同期配ordinary2D、资源SHA、PID及pose/时间标记；只有可重复证据指向材质通道时才做最小隔离delta。
