# 02 · 刀具造型材质与握持

## Root已成对接入与原生右持收件（2026-11-17）

199c Right／0295 Left已进入app既有资源入口；Root重哈52收据条目，审三列与paired oblique，接受闭握局部关节弧面改善。Right16＋Left33制作测试通过，完整467测试及构建通过；c5c28446 APK设备SHA核对，实际Right已显示在 `presentation/native-hand-joints-right-2026-11-17.png`。Left仅装包和制作检查通过，原生显示/切换仍待Root，不把镜像等价当全局零穿入；整体手与shader品质仍未过。

本路正补最小production文件闭包，Root统一Git。模型写入封口，不再为当前首件改Right/Left/handoff；之后材质与手姿任务须基于已采用这一对，不覆盖回a980/ecc。技能world-hands误触修复已由Root接入并过467总suite，阈值/guard/HP/伤害未改。

## Root 当前收件与合入边界（2026-11-17）

`finger-surface/joint-loops/right_hand_joint.glb`（`199c228c…`，6222三角）已交，16项私有测试及四态几何检查通过；169原位置／权重与192原法线改动有保护边界证据。旧109对映射自交保留，不能称无自交。它尚未进入app；Root须看三列原材质对照，确认收益后使用同一输入派生匹配左手，并验证真实握刀。当前APK仍为a980右／ecc左，不把私有新手计作当前画面。

双手技能头部后退误触修复另在 `native-steel-release/skill-motion-correction/`，候选7项回归通过但未装入APK。下一步由Root评审、整合，外部02保持封口，不重复旧粗糙度材质结论或自行覆盖正式手模型。

## Root实物审核：48e指侧首件与下一步关节形体（2026-11-17）

外部02连续两次新任务只读后复述旧材质结论，未创建finger-surface产物，Root已停止该轮写入并改由fresh专项实际制作。现 `finger-surface/right_hand_finger.glb` 为48e99daf、5536tri，13项独立检查与四态接触通过；仅合法Pinky指侧1475 normal约4°调整，原位置/UV/骨权及其余normal保持。旧109父面交叉完整保留，不能因细分raw计数129而当新增或改善。Root已实际看open/closed原材质与neutral对照：轮廓略圆顺，PIP/DIP大片折面仍显著，因此只收为技术基线，**不作为整体手部品质通过，也暂不装正式左右手**。

下一阶段由Root同一专项执行 `finger-surface/joint-loops/`：以冻结a980为父源、48e作对照，重建真实MCP/PIP/DIP背侧/侧面的关节环线与曲率过渡，不再只给旧三角边添小PN中点。允许移动真实非保护指背/侧原点并更新必要normal/局部插值骨权，保真实指骨长度和关节体积；内掌/握柄指腹、拇指支撑、14点掌背与腕口的既定保护不动，78骨/IBM/Grip/原动画/UV语义不变。不能把关节磨成圆管。Right预算<=12000tri，实际必要曲率可以用预算，不能只拿省面数当成果。

先20分钟一个可看的完整首件，0.3m open/mid/closed原材质与neutral，Root看PIP/DIP轮廓与弯折后再完整验。四态几何/normal/父面交叉/DAO新问题继续不允许；有具体因果时完成必要修复，不因人为一次次数空停、不做无依据参数扫。新骨权/原点/normal改动须精确列出与解剖证据，不能沿用48e“原点全零”的旧结论。Root接受才统一Left派生/装包；不碰formal/app/SDK/Git/设备。

## Root审核与指部表面重建合同（2026-11-17）

skin-material首件技术成立但无可见收益，封存不进正式手；原4K源已1:1进入hand atlas，停止放大图或只调roughness。Root已在原生近手图确认偏亮、指节棱角仍明显；原生视口恢复/交战证据见presentation/native-hand-input-2026-11-17.json。灯光A/B归Root，02不改配光或SDK坐标。

新Ownership仅 `grip-refinement/finger-surface/` 与02。以冻结a980 Right为唯一源，只制作指背/指侧轮廓与真实关节表面：先结合MCP/PIP/DIP实际骨位、表面拓扑、剖面确认棱角来源，不按dominant权重冒充解剖ROI。可以局部重构必要环线/新增采样并由原面插值得到UV/权重，保真实关节起伏，不能把手指磨成圆管。保持内掌/握柄指腹、拇指支撑与腕口已通过修复；原点/米制/骨架IBM/Grip/原贴图/原动画不变，不额外改14点掌背权重。Right总三角<=9000，新增几何必须在0.3m原材质及neutral同机位可辨收益；这不是设备性能放行。

45分钟单一首件、最多一次实际定位修正，交真实完整GLB、open/mid/closed原材质与neutral近景对照、ROI与保护点/握柄/新增自交检查及可复建入口，含一个保护区越界负例。闭握旧109对及open/mid旧DAO问题保留为基线，不能藏起；新增手指扭曲/碰柄必须拒绝。先交Right供Root看图，Root接受才统一Left派生/装包。不得写正式资源/app/坐标代码/公共producer/Git/设备，你不独自在仓库，保留他人修改。

## 当前交付：Right 皮肤材质首件无可见收益（2026-11-17）

**本阶段结束，等待 Root review。** [候选、真实来源量化与四图对照](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/skin-material/README.md)已完成。候选 SHA `2d78819b379ee67928fef760803a30a8b2138cb76d535d1457e2a78c929e4b64`，技术装配与 KTX 验证通过，但原材质／中性材质的固定 0.3 m 对照都没有可辨改善，不能替换正式 Right 或单侧发布。

当前 Tripo 4K 是最高真实源，但 1536 hand atlas 已按 1:1 source texel density 裁切，放大不增加皮肤细节。本候选仅以 1 张1024 MR 衍生图调整 hand／finger 三角粗糙度：2,213 skin triangles 用新材质，2,550 袖口／混合 triangles 保原材质；base color／normal、指甲和袖口语义保留。四图显示它未实质改善统一发白／塑料感或低面数指节，继续加重粗糙度只会压平高光，故停止，不伪造皱纹或贴图细节。

triangle partition、原顶点／UV／权重／78骨／IBM／动画／Grip、closure 和三张现有 KTX 均检查保持；新 KTX 通过验证。Root 的 native main viewport 已确认左右手加载和手位移动，但肤色偏亮、指节低面数仍是原生后续质量项，本候选不覆盖该事实。正式 app、公共 producer、设备、构建和 Git 未动。

## 新交付：MCP前掌背混权修复 a980（2026-11-16）

**本阶段结束，待 Root 实物 review、左右同步派生与原生验收。** 新首件仅在 `production-patch/anatomical-crease/`，完整入口为该目录 `handoff.json`。Right GLB为 `a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862`，仍5,018三角，保健康3000腕口/面流；3000旧GLB未改，也未沿687/9f叠层。

Root已明确授权实际MCP之前的掌背混权皮面修复。新制仅14个源掌背控制点：原631/546/37/364被finger spill随卷指拉动10–14.8mm，造成长V沟；将这一经独立MCP/背侧/一环证实的源区少量混权平滑回投到R_Hand并保持实际open表面，主要点卷指位移降至约0.61–0.89mm。原材质与neutral同机位0.3m真实GLB图均显示主长沟消失，未靠贴图遮盖；图在 `anatomical-crease/renders/`，README列四图。

独立15项正/坏例及完整default/open/mid/closed通过：14点均从源实际MCP骨位与皮面重新证明在关节之前至少3mm、背侧depth<-10mm及source1101/1075必要一环内；真正远端指体/指腹与内掌保持保护。无新增geometry/normal/seam/self/Dao问题，保护LBS误差0；self仍109/0/0/109，继承bad-normal角34/13/19/34→33/13/19/33。UV、骨架/IBM/动画/Grip与3KTX保持。本新阶段首件通过源检查，未使用定位返修；此前次数限制不用于拒绝本新授权。

尚未证明连续时间、SDK TBN或PICO端内观感；源低面数指节/远袖口与肤色纹理仍在。Root需看图后才派生Left及装APK。本路未改正式app、Left、刀、公共producer、Gradle、设备或Git。下方9f/3000等均是已结束的历史阶段，不覆盖当前a980实物。

## 当前交付：production-patch 前置 crease-remesh BLOCK（2026-11-16）

**本轮一次定位修正阶段结束，等待 Root review。** [失败候选与完整定位](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/crease-remesh/README.md)已冻结。候选 `9f946add…` 为 7,496 面，未超过预算，未扩指部、掌内握柄、Grip、78 骨／IBM、动画、UV、权重或 KTX；不能替换 Right 或派生 Left。

一轮局部共形重拓扑在 687 的同一掌背／第一腕带范围内执行。动态检查发现 candidate face3570（source parent1886）在 default／mid／closed 存在新法线与面绕序反向。一次按所有相邻面、三姿态 inverse-LBS 的局部回投仍无法满足共享角；继续需拆 normal seam 或更深的面重投影，超出本轮一次修正合同，故停止。687 与正式资源不动，现有 687 图不作为 9f 通过证据。

此失败不掩盖：候选顶点／ROI／脚本／失败验证和固定收件均已写入。等待 Root 明确是否授权下一轮对 source face1886 邻域做 normal seam／重投影；本路不再扩域、渲染或参数扫描。

## Root 当前审核与执行合同（2026-11-16，已执行）

已收9f946add crease-remesh失败包，确认不能进入正式Right或派生Left。原face1886的新子面出现默认/中/闭姿态法线反向，不能并入源13个坏角限制，也不以增加面数作为收益。687与9f候选封存。

下一实物从可信Right v2 3a1be1dd重新制作，不能在687/9f上累加细分。Ownership仅palm-wrist-surface/production-patch/及02。允许在必要掌背/腕袖ROI重建有解剖曲率的局部面片、重投射UV/权重，并按需要拆分per-corner normal/UV seam。先区分几何真翻折/退化和共享法线冲突：几何不合法就修面/权重，只有几何健康时才拆法线缝；不能反转整面、关背剔除或翻normal去掩盖。

保护指部、掌内握柄、Grip、78骨/IBM/所有动画与三张原KTX；原109对指间交叉继续披露。允许重建而不是仅细分，面数<=8000；位置焊接后的接缝闭合，原UV/权重在保护域逐值不变。先过default/open/mid/closed实际几何与normal/winding，再交0.3m同机位无材质/原材质各一对，必须去掉长斜折沟、腕口有顺畅过渡。60分钟单首件，最多一次定位修正；不改app/公共producer/formal/设备/Git，不派生Left，不复制仓库。你不是独占工作树，保他人修改。

## Root实物评审与下一步（2026-11-16）

已实际看掌背before／after和修后腕口0.3m图。候选687aea63有轻微轮廓圆顺收益，但掌背长斜折痕、掌骨大平面与腕口生硬收口仍明显。不作整体手部质量通过，暂不替换正式Right／派生Left。35项制作检查与保护区域零差值只证明声明范围保全，不代表外观精致；正式Right3a1be1dd／Leftd8e9c3cb保持。

先封存现有首件身份与检查，不重渲。下一轮应围绕掌背解剖曲面和腕袖过渡做局部重拓扑／权重投射，保闭握、Grip与指部保护域；不只加细分或全局平滑，不将UV／肤色问题称为几何解决。先有正常距离可见收益，再由Root原子整合左右手。模型账号错误已处理，本次续现有收件。

## 当前交付：crease-remesh 一次定位修正 BLOCK（2026-11-16）

**本轮阶段结束，等待 review。** [失败候选、ROI 映射与动态法线证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/crease-remesh/README.md)已冻结。候选 SHA `9f946addb905de04051883d3a1cd6bee7d56aac1ec39a37ed9064d1b7f491eaa`，7,496 面，未超预算；不替换 Right，也不派生 Left。

687 为源的一次局部共形重拓扑保留掌背／第一腕带范围与三姿态混权边预检，但新增 child face3570（source face1886）在 default／mid／closed 有动态法线与面绕序反向。联合所有相邻面后的单次法线回投仍不能同时解除该共享角矛盾。继续需拆法线或更深面重投影，已超出本轮一次定位修正，故停止，不把“细分与面数增加”包装为质量通过。现有 687 四图不复用于此候选验收。

正式 app、公共 producer、构建、设备、Git、Right v2、左重建和 687 收件未动。等待 Root 决定是否授权下一轮更深的局部 normal seam／重投影；本路不继续扩域、渲染或参数扫描。

## 已封存：687 现候选，续派 crease-remesh（2026-11-16）

Root 已看 687 的 0.3 m 实物：掌背／腕口收益过小，暂不换 Right 或派生 Left。现候选连同[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/handoff.json)封存，不再渲染、调参或改其身份。

新首件只在 `ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/crease-remesh/` 制作，目标是掌背长斜折沟及腕袖交界的大平面／锯齿轮廓。先区分实际几何折沟、UV／法线缝或蒙皮混权根因，再按根因局部重拓扑、重投射权重或连续法线；不再全局细分，也不只平滑 64 个控制点。允许扩掌背／腕口必要 ROI，必须记录保护映射；禁动指部、掌内握柄区、Grip、78 骨／IBM、动画键和刀。

总面数不超过 8,000。优先重投射原 UV／三张 1536² KTX；若纹理必须改变，报告而不把它包装为几何解决。default／open／mid／closed 保护区不得新增核心侵入或自交，旧 109 对继承面交叉继续披露。交无材质法线与有材质的同机位前后各一对，0.3 m 必须有可见曲面收益；最多一次定位修正、60 分钟，不参数扫描或新增镜头。Root 接受 Right 后才统一派生 Left 和整合原生包，本路不改 app、公共 producer、正式资源、构建、设备、Git。

## 已封存交付：Right 掌背／腕口表面候选 687（2026-11-16）

**本阶段结束，等待 review。** [完整候选、ROI 映射、三姿态验证与四图对照](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/README.md)已冻结。Right 候选 SHA `687aea63eabfd4c08401a0a207f23e3740b9dad6348e9ebd6b7cce61f1c31e9e`，5,598 面；源 Right v2 `3a1be1dd…` 保留，正式 app 未替换。本轮只改掌背硬脊和手邻第一袖口带，64 个原顶点与 352 个新增点都具映射，掌腹／指腹、握姿、腕／Grip、78 IBM、贴图和三张 1536² KTX 未动。

四张固定机位图显示掌背折角减弱、腕口第一带更圆顺，但收益有限；掌背长脊、腕口硬边、低多边形折面及远端收口仍可见，不能包装为整体手部质量通过。35 项检查通过，非 ROI 动态皮肤无变化，ROI 造型位移已列；开／中／闭不新增 dao 或 self face-pair，旧 open／mid 穿入和 closed 109 对继承表面交叉仍明确保留。源无 TANGENT，运行端 MikkTSpace 与原生观感待验。

Root 决定是否接受这份 Right 形体后，才从其统一静态重建 Left；当前不派生 Left，不再生成或渲染。本路不改正式 app、公共 producer、构建、设备或 Git。

## Root本轮整合review（2026-11-15）

Root已看闭握三视图并完成独立14项数学复核，接受d8e9c3cb…左手与删除旧C补偿同次整合。实际原生准备页已点击LEFT，先撤销旧观察、再收真实左手并显示左手持刀；随后RIGHT选择及开局已通过。持刀侧经真实buffer/reducer/Arena，满载手选择失败不锁存，436组合通过。腕口／掌背折面及继承指间交面未作最终质量通过。新asset与验证冻结；下一轮围绕正常距离原生手背／腕口观感，不继续单指参数循环。

## 当前交付：common Grip 静态左手重建检查完成（2026-11-15）

**本阶段结束，等待对应 Root review。** 从已有实物续做，没有重建或改变 common Grip 契约。[完整 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/left_hand_rebuilt.glb) 仍为 SHA `d8e9c3cb034f465e4527c13aad84e7ba283c3efcc537ab254c6295717cd1bbfd`、2,627,980 B；[复建脚本／变换映射](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/README.md)／[独立实际检查](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/verification.json)／[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/handoff.json)。

主线程已看实际 KTX＋未镜像 dao 的[正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/previews/left_closed_front.png)／[背面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/previews/left_closed_back.png)／[斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-rebuild/previews/left_closed_oblique.png)：左手手性、拇指侧、包柄弧线和虎口体积可读，旧左手横切进柄的薄片未再出现；掌背／腕口粗糙、低多边形折面和源前臂收口仍保留，不声称最终手部质量通过。

28 项核验／坏例全部通过；真实 default 及 grip@0／0.5／1 的全部 primitive LBS、法线、绕序和 78 骨镜像等价误差均为 0，最外 `LeftGripRoot` identity，所有节点正 determinant／无负 scale，完整 R_↔L_ 双向换名且 palette/node ID 不变。实际 source 无 TANGENT，T.xyz 反射／w 反号用合成夹具验证，MikkTSpace 仍待运行端；权重／UV／三 KTX 字节与可信 Right 保持。

实际 db28 的全部部件逐一核拓扑，不假设刀护手对称：closed Left 仅 Index 两浅样本，最大 **0.093440 mm**（Right 0.092522）；Thumb／Mid／Ring／Pinky 核内为 0，护手／collar／ferrule／pommel 等闭合 solid 无入内或 surface-cross。cord 有 1,442 开边，只报表面交叉 Left33／Right38，不假称体积穿入。全手 self open／mid 均 0，closed Left／Right 同为继承 **109 对**（Thumb–Index47、Mid–Ring62），新增 0。固定刀的旧 open／mid Thumb 穿入仍在，Left 约 11.0676／4.87569 mm；不得隐去或宣称整 clip 清核。

**必须原子整合，不能单独换模型。** 新左手 root 直接消费 G，没有旧 C/B 或 DerivedHandGrip_L。当前 app 代码仍有旧左腕偏移；Root 应在同一次切换中换左 GLB并删除旧 `LEFT_WRIST_FROM_GRIP`／派生 marker 转换，使左右均直接 G。本路未改正式 app、右手、刀、公共 producer、设备或 Git；同级 `left-rebuild-math-review.py` 由 Root 独立复审，未触碰。SDK ControllerPose 生理约定和新组合包的原生画面仍待 Root 验证。

## Root方法修正：common Grip坐标中的静态左手重建（2026-11-13）

前一轮两次局部摆指虽将核内最大深度降到.03mm，却新增自交，候选不合入。继续在错误闭握上调单指的风险已由实物确认。下一轮复用已接受右手v2的完整几何／grip曲线，**静态烘焙为真正左手资产**，重建rig／IBM／法线切线／面绕序。这是有解剖与真实握持依据的资产重建，不对SDK朝向盲翻转，不使用运行时负scale。

**最终只保一套common Grip坐标。** 令S=diag(-1,1,1,1)。最外GLB根identity；节点／IBM以S*M*S共轭，mesh POSITION／NORMAL反射，TANGENT.xyz反射且w反号，三角绕序反转；动画translation反射、quaternion共轭、scale保留。Right源保留完整78-joint双侧rig，须在原node ID／palette稳定前提下双向交换R_↔L_骨语义，避免同名；渲染／grip的原R目标成为L。最终pL=S*pR。新左手原点／轴直接与右手／dao的Grip一致；不加B=C^-1帧，也不保旧DerivedHandGrip_L补偿。Root在资产接受后同一整合中删除旧LEFT_WRIST_FROM_GRIP及派生marker转换，左右handRoot都直接消费G，不能只换代码或只换资产，也不留兼容路径。

本轮允许新左手geometry／open姿态改变，覆盖旧保open@0字节及无依据镜像的制作限制；须验证实际左手手性、骨节点det>0、全skin／IBM镜像等价、真正DAO闭握和三视图，不仅检查锚点。所有反射烘入mesh与rig数据，节点不得遗留负scale。保持grip0/1与文件入口契约，图片／材质复用。披露保留掌背／腕口问题。

02仅在grip-refinement/left-rebuild/产完整候选、复建脚本、变换说明、开中闭检查及同机位图；不改Kotlin。Root独立数学复审后统一换资产／转换代码，反射等价不等于SDK实测。45分钟实物阶段、最多一次有定位返修；不碰app、公共producer、右手、刀、设备、Git，保其它会话编辑。

## 当前实物：左拇指／虎口两次修正首件 BLOCK（2026-11-13）

**本轮限定尝试阶段结束，等待对应 Root review；没有修好，不可替换正式左手。** 已交[完整左 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/left_hand_refined.glb)，SHA `645d153b1afb151ee430843d11b8f64454a680e71a56a8d673d2f8a092e93419`；[三骨 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/pose_delta.json)／[说明与失败定位](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/README.md)／[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/verification.json)／[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/handoff.json)。结构合同 PASS、12 测通过，但实际质量守门 BLOCK。

同机位实际 KTX＋正式刀[原 closed](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/transform-diagnostic-2026-11-13/renders/L_held1.png)／[候选 closed](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/previews/after_closed1.png)／[候选 mid](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/left-thumb-refinement-2026-11-13/previews/after_mid0.5.png)已由主线程逐图核对。原拇指薄片从柄面退开有局部收益，但拇指挤入食指并新增自身折叠，虎口仍有折面，不符合自然对向夹持，不能据清核数字通过。

在同一原 508 Thumb 顶点／面心样本中，93 核内／最深 11.3766 mm→1／0.0312435 mm；额外 563 边中样本从 91 核内／最深 11.6290 mm→0。**但新增 17 对 Thumb 自交，旧 50 对 Thumb／Index 被移除后换成 75 个全新交面**，不是净增 25 即可忽略。非 Thumb 原 77 核内／最深 9.4184 mm 保留，未改其它指追全手零值。

新虎口异常为 native face4279／source body49233，native vertices1064／1072／1033→source6491／6570／6238；混合 Index1、Thumb1／2 权重使固定 Index 与变化 Thumb 差异拉扯，normal／face signed dot +0.6544→-0.5062。该面面积为原 1.346 倍、未塌为零，不能将其误称面积塌陷。精确权重、UV、实际位置与新增完整 face sets 均已交。

只改 Thumb1／2／3 的 closed 三条旋转，default open、15open@0、其它12指、腕／DerivedHandGrip_L／刀／整体坐标尺度、骨长／IBM、原几何／权重／NORMAL／UV／材质／KTX 和右 v2 保持。没有以保持字节为理由把失败候选宣称修复；本轮两次定向修正后停止，未在未验证 open 保持的前提下继续第三轮网格／权重变体。open 实际 LBS 保留；mid 的原拇指穿入降低且无新增交面或法线异常，closed 的新增交面及折面则明确导致 BLOCK。

本轮不改正式 app、公共 producer、设备、Gradle、Git 或整体手向。完整失败实物已冻结，Root 决定下一步局部真实皮面／权重与骨姿的联合修复；本地试验不等于原生完工。

## Root review与续派：修左闭握拇指根部（2026-11-13）

Root已实际查看本轮`L_held1.png`与`R_held1.png`：左手掌拇根拉成薄片并切进刀柄，右手未出现同类问题；接受“局部闭握／握点组合不匹配”的诊断，不把它升级成SDK整体反手根因。六图与有限指标支持继续修该真实资产缺陷，整体朝向仍须运行验证。

02下一实物只修左手closed@1的拇指／虎口：保持腕、现有DerivedHandGrip_L、刀及整体坐标不动，先检查Thumb1/2/3闭握局部旋转；如必须改局部权重或原皮面，允许明确修改并给vertex/face IDs、理由与变化，不能为保持原字节而留下可见薄片。open@0保留，检查中间姿态过渡，不改变右手及其它已接受指姿。目标是自然绕柄、虎口有体积、无新增可见指间／掌面穿插；核内样本深度是证据之一，不单凭计数放行。

在既有grip-refinement下交一个左手完整GLB、delta/映射、同机位前后图及开／中／闭有限检查，45分钟阶段期限，最多两次有明确根因的修正，避免盲目参数扫描。Root继续独占正式app模型、公共producer、构建、设备与Git；保持其它编辑。原手诊断与右手v2保持冻结，下一首件结束即写入本交接等待Root实物review。

## 当前执行合同：仅交付原生 APK（2026-11-13）

02 原生工作的唯一产品交付是 **Kotlin + PICO Spatial SDK 6.1.9 的 APK**，在 PICO Emulator 验证，目标终端 Space Pro／OS6。唯一工作仓库为 `/Users/yupeng/projects/personal/pico-wuxia-arena`。本节约束当前原生分工；独立 Web 线按 `docs/collaboration-boundaries.md` 保留并维护，本路不因而切回 Web。

本路不做 HTML／Web／Three.js 游戏开发、浏览器试玩、网页材质／光照调试及新 HTML mock 页面。已有 HTML 文件和他人工作保留、不覆盖或删除；浏览器仅用于必要的官方资料／账号服务，不作为原生游戏验收。禁止新建仓库、分支或页面，不修改 `/Users/yupeng/projects/personal/pico` 或网站仓库。

02 后续只执行 Root 已授权、能进入现有原生 APK 的源码补丁、GLB／贴图／动作／原生 UI 资源，并给出明确接入点。不能接入的研究、报告和重复渲染停止。Root 统一构建、模拟器／设备、Git 提交与发布，其他责任方的代码和资产保持各自所有权。

Root 已完成 v2 开发整合，本轮续派的原生手模型变换诊断已交实物与结论，阶段结束，等待对应 review。旧 v2 源与证据继续冻结；不恢复本路旧网页队列。下文浏览器证据不代表原生 APK 通过。

## 当前交付：按实际 PlayerHandsPose 的双手三视图诊断（2026-11-13）

**45 分钟内的实物诊断阶段结束，等待对应 Root review。** [六张同机位实际 3D 图及说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/transform-diagnostic-2026-11-13/README.md)／[数值核验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/transform-diagnostic-2026-11-13/verification.json)／[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/transform-diagnostic-2026-11-13/handoff.json)。主线程已逐张查看最终 R/L 掌心、掌背、握刀六图，未复现整体手性反转／镜像或无效 skin／IBM；实际拇指侧和腕指方向互补。手性指标 R `+0.959660`、L `-0.960006`，两侧都是 proper rotation，骨／皮面对应实际各侧，不仅比较名字。

**确定复现的是左闭握局部质量问题。** [左 held@1](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/transform-diagnostic-2026-11-13/renders/L_held1.png)有拇指掌根拉薄／柄面相交；当前代码映射到共同 Grip 后，左拇指实际 vertex＋face-centroid 508 样本中 **93 样本核内**，最大约 **11.3766 mm**、核内 P95 9.9204 mm；右拇指同类 516 样本均在核外。左手全手 3,272 样本中 170 核内。原掌背硬脊、腕口硬边／低多边形折面仍可见。刚体 Offset 不会改变三角面积或制造局部拉扯，但会决定相对刀的位置；本轮定位为“左派生闭握／皮面与既有握点组合不匹配”，不唯一归咎 IBM、权重或 SDK。

本轮没有改模型、没有发整体翻转候选：整体反手未复现，不能盲转 180°／镜像／负 scale。10 项实际资产／损坏／有符号接触测试和渲染工具 4 项 guard 通过；最终六图使用统一诊断补光，左右同机位／同材质／同映射，实际 KTX 像素，未用旧右手5fb companion。只作一次掌背可读性补光修正，未做姿态参数扫描。SDK 原始 ControllerPose 与 daoGrip 生理约定、实际 PICO skinning 及站姿仍待 Root 运行证明，代数锚点重建不代表解剖通过。

Root 确认用户问题发生于 PICO Emulator 原生。本轮仅用当前正式 R `3a1be1dd…`、L `cf3203e0…` 与 dao `db28d426…`，按 `content/PlayerHandsPose.kt` 的实际变换生成左右各掌心／掌背／握刀的同机位 3D 图，核真实 skin／IBM、拇指侧、腕指轴与手性。先判断能否复现资产自身反手／扭曲；有确定资产问题才在自有精修目录产候选，不能盲转 180°、镜像、负 scale 或改 app 姿态。

本轮产物限 `ArtSource/refinement/weapon/native-first-person/grip-refinement/transform-diagnostic-2026-11-13/` 与本交接；不动正式模型、公共 producer、Gradle、设备、Git 或他人修改。只读资料／代码／图像判定由本路主线程自行核查；当前可用子任务模型未提供 DeepSeek，未将只读任务换成其他模型。并行任务仅实现可执行的渲染／验证代码，不代替主线程只读诊断。

已从当前 Kotlin 解析 Rroot＝G、Lroot＝G×资产派生腕偏移，保其精确平移和 quaternion；复现统一声明的 neutral G，左右每种视图相机／光照／镜头一致。掌心／掌背用 open@0 检查解剖结构，握刀用各侧分别装备的 closed@1；不是声称游戏同时双持，也不是 SDK 原始 ControllerPose 的实测记录。输入和代码 SHA 绑定于 `runtime_mapping.json`。Root 仍需运行证明 ControllerPose 与 daoGrip 的生理约定，代数锚点重建不能当作解剖通过。

本轮实际六图、工具与核验均已完成并冻结；未改正式模型、公共 producer、app、Gradle、设备、Git 或 Web，等待对应 review 再推进获派的局部修复。

## Root review：v2已进入开发资源，等待原生验收（2026-11-13）

Root与独立复审实际看过正／反／斜三图，接受小指绕柄与清楚指缝，闭握骨姿本轮不再退回。正式 app 右手现为 `3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0`、2,517,124 B；源收件与历史基线冻结，左手／dao／角色producer／attack binding未变。总审核入口为 `ArtSource/refinement/weapon/native-first-person/root_integration_review.json`。

已有运行时只 seek grip 0或1，默认右持刀是closed@1，未消费mid@0.5；离线固定dao的open／mid旧侵入不可隐去，也不直接当默认闭握失败。closed仍有2个最大0.092522mm浅样本。旧掌背硬脊、腕口硬边未解决，完整手部品质未通过。02冻结v2与三视图，不追加闭握参数扫描；Root负责下一包实际装备路由、亮度和腕口／裁边检查，再据具体原生画面续派。

## 当前交付：Ring／Pinky 指缝与末端支撑 v2（2026-11-13）

**v2源审已通过开发整合，原生待验。** [完整 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined_v2.glb) SHA `3a1be1dd9b46a9baed21914006c2a48d0fe63651b5a0f8174e509584ce3599a0`，2,517,124 B；[骨姿 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/pose_delta_v2.json)／[接入说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/README_v2.md)／[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/handoff_v2.json)。[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/verification_v2.json) PASS、errors／blocking 均为空；[四遍终审](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/review_v2.json)为 **`APPROVE_FOR_ROOT_NATIVE_REVIEW`**，可交主控原生接入评审，Root已换入正式开发资源，尚未构建与端内验收。

本轮只联动 Pinky1／2／3 闭握骨姿，先分开中节，再让中节承担主要弯曲、末节配合顺柄收回。原 Ring／Pinky 10 对真实新增交面 **10→0**，其余指间交面完整集合不变，小指与掌面没有新增交叉。固定 24 个真实掌侧样本由 0／24 增为 **17／24 距绳面≤3 mm**，最近 1.392 mm、中位 2.216 mm；不是只追单个最小距离，也不把全 P3 指背都称接触面。独立三视图确认指缝清晰、绕柄自然，没有折钩、融合或黑三角。

保留已认可的拇指／食指实际皮面及原 24 个近 1 mm 支撑样本。纯骨姿已解决返修目标，**没有改网格或权重**，POSITION／NORMAL／UV／JOINTS／WEIGHTS、骨长／IBM、尺度／父级、腕／Grip／刀 Base／Tip、材质／1536² KTX 和左手均保持。非 Pinky 12 指骨曲线不变；原混合 Pinky 权重使 Ring／Mid 主导皮面局部随动最多 1.5602／0.004541 mm，已明确披露。默认 closed＝新 `grip@1`，15 指 `grip@0` 原字节保持。

复用原三个精确机位、同光照材质与比例，一次单 Blender／两线程出 [0.3 m 正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews_v2/grip_0.3m_front.png)／[反面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews_v2/grip_0.3m_back.png)／[斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews_v2/grip_0.3m_oblique.png)，实际 KTX level 0＋正式 dao，未整体转动手刀。开／中／闭均无新增或加深 core 样本、无新增指间／掌面交叉、退化或法线回归。固定带刀对照中原 open 11.0776 mm／187 样本、mid 4.88092 mm／45 样本，以及 closed Index 0.092522 mm／2 浅样本保留，不能称整 clip 绝对清核。

Root 接入点仍为 `app/src/main/assets/models/player_hands/right_hand.glb`，由 `PlayerHands.kt` 消费，根／骨架／唯一 `grip` 0→1 秒契约不变，无需 Kotlin 改动。本路未改正式资源、SDK、手势、构建、Emulator 或 Git。Root 仍须验实际装备路由、肤色／光照、原腕口边与连续手姿／裁边；本轮不追加参数扫描或重复渲染。

Root 已收件并认可 0c44 的拇指压靠／整体包握收益，正式闭握继续返修，尚未换入 app。下一首件先消除 Ring2／Pinky2 中节 10 对新增交面，再联动 Pinky1／2／3 收回约 5 mm 末端悬空，恢复清楚指缝，不能仅把 Pinky3 折成钩。自然绕柄及无新指间穿插为验收目标，穿柄数字单独改善不算通过。

仍仅拥有 `ArtSource/refinement/weapon/native-first-person/grip-refinement/` 与本交接。保已认可的 Thumb1／2／3 闭握及拇指收益、腕／Grip／刀 Base／Tip、坐标尺度父级、其余手和左手不动。优先纯骨姿分步修正；若明确证实骨姿不足，可最小调整局部 Pinky／Ring 原网格或权重，须列原 vertex／face IDs、原因、幅度及 NORMAL／TANGENT／UV／贴图影响，并实际验证开／中／闭。若几何改变则明确放弃旧“几何不变”声明，不能为守字节指标保留可见穿插，也不扩到掌腕／前臂或整体手刀。

v1 GLB／delta／三图及审计保持冻结；v2 同目录完整 GLB、delta、实际验证与新三图均已交，阶段结束。Root 统一正式源、构建、Emulator 与 Git；等待对应 review 再推进获派的下一轮。

## 上轮首件：原生默认右手握柄修复（2026-11-13，Root 已返修）

**可见首件阶段结束，等待对应 Root review。** [完整 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/right_hand_refined.glb) SHA `0c44cd30bb405e5cf3b05cfae53ce73b732278933f6c3e5b82602139772cfaef`；[骨姿 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/pose_delta.json)／[固定收件](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/handoff.json)／[说明与接入点](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/README.md)。结构契约 PASS，四遍 review 为 **`REQUEST_CHANGES_FOR_FINAL_GRIP`**，允许交 Root 原生首件评审，有可见收益，但最终握持质量未通过、未获正式发布批准。

Root 可选择替换的现有入口为 `app/src/main/assets/models/player_hands/right_hand.glb`，由 `PlayerHands.kt` 加载 `asset://models/player_hands/right_hand.glb`；无需改 Kotlin。候选只改 9 个右指的闭握 rotation，默认 Rclosed＝新 `grip@1`，15 指 `grip@0` 数据原样；原 BIN 前缀、几何／UV／权重／IBM／骨长、腕／Grip、材质和三张 1536² KTX 字节不变，左侧及正式文件均未动。

只运行一个 Blender 进程、两线程，已交 0.3 m 实际 KTX＋正式 dao [正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews/grip_0.3m_front.png)／[反面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews/grip_0.3m_back.png)／[拇指侧斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/previews/grip_0.3m_oblique.png)，没有整体旋转手刀或改比例。新姿态相较原生基线明显收回长直指，拇指与食指形成对向近接触；腕口原有不规则边和源折面保留，近端 cap 部分出画，不能视为连续裁边通过。

[实际同组 7,167 表面样本核验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/grip-refinement/verification.json)：核内样本 277→2，最大深度 11.486→0.0925 mm，深于 0.25 mm 的 256 个样本全部清除；剩余为原 Index 极浅入。拇指末节到 Index 最近约 0.0438 mm，有 24 样本在 1 mm 内。**未解决项**：Pinky3 到 cord 最近仍 5.061 mm、到 Ring 3.841 mm，均无 3 mm 内支撑样本；真实位置焊接排除合法邻接后，Ring2／Pinky2 带新增 **0→10 对交面**（不是 Pinky3 末节导致），不能声称握持质量或无自交通过。Root 决定原生接入评审与下一轮修派，本路冻结单首件，不继续参数扫描或重复渲染。

Root 已将原生 UI／命中反馈与三角色换入 APK `ca26f4a9…`，本轮直接修 source 闭握，不再停在时间读数／SDK 探针。输入为已发布 `right_hand.glb` SHA `5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d` 和正式 dao SHA `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0`；实际待修观感见 Root 的 `artifacts/native-ui-impact-2026-11-13/combat-final.png`、`current-terminal.png`。

唯一制作所有权是 `ArtSource/refinement/weapon/native-first-person/grip-refinement/` 与本交接。只调 R 的 15 指闭握骨姿，重点为长指末两节和拇指压柄；默认 Rclosed 与 `grip@1` 一致，`grip@0` 原样。腕／握点／刀 Base／Tip、骨长／IBM、几何／UV／材质及三张 1536² KTX 字节均保持，不整体旋转手刀，不改左手、SDK 或识别。Root 统一正式资产、构建、Emulator、Git；他人修改保留。

本轮要求在 45 分钟内交一个可接现有 PlayerHands 的同契约完整 GLB、骨姿 delta 和 0.3 m 正／反／斜视各一张实际 KTX＋正式刀图；首件与检查已在该窗口内完成。最多一个 Blender 进程、两线程；不做参数大扫描或重复渲染，当前阶段已结束，等待对应 review。

## 上轮只读复核：原生已显示，握柄视觉待 review（2026-11-13）

**原生 Full Stage 已显示手／刀；握柄视觉仍待 Root review，尚不能判为实际 closed@1 合格。** 本次仅查看 Root 的[修复后窗口图](/Users/yupeng/projects/personal/pico-wuxia-arena/artifacts/native-hands-hit-2026-11-13/fixed-ready-window.png)，对照候选[默认握刀近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_0.3m.png)及[反面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_1.0m_reverse.png)。窗口标题为 PICO Emulator 6.1.0，因此这是原生模拟器呈现证据，不是头显实测。所审窗口图 SHA 为 `31d138493e8773e7dc4a101841416a6e29cd451c56c7be264f47fc230ff448c8`。

据 Root 接入反馈，初版在 `model.enabled=false` 后调用 `playAnimation` 被 SDK 拒绝并黑屏，已调整为先构建 paused grip 再 hide，修复包 `a8907a…` 已显示场景。本路未复跑该包或验证 SDK 调用顺序。

本次具体可见结论：

1. **闭合时刻不能由此单帧确认。** 右手不是全张掌，几根手指已卷曲，但靠柄尾、画面最右的一根长指仍明显伸出，末段未形成清楚的绕柄包覆。单视角无骨标注，不把它硬判成食指或小指。源 `closed@1` 的小指末两节本来也较直，不能据这根指便断言 SDK 停在 open；反过来，`getTime()==1` 也不能证明实际蒙皮已求值到正确握姿。
2. **手柄接触仍未通过。** 柄穿过可见卷握区，前中段几指与柄接近；长指、拇指及背侧指尖的完整接触被遮挡，无法排除局部悬空或穿柄。离线 Grip／Blade 标记对齐误差不能代替本次运行画面的接触验收。
3. **肤色明显偏亮、层次偏浅。** 相较同场 NPC 脸部及候选图，实际右手呈浅亮暖色，指节／皮肤细节弱，和暗刀身反差大。仅凭该图不能定位是光照／曝光、色域还是材质读取问题，也不据此改源贴图。
4. **前臂近端切口未被覆盖。** 大部分前臂和近端闭合截面已出右边框，不能据“没看到黑腔”判裁边通过。右掌根与袖口接口可见深色不规则边，单帧不能区分阴影和缝隙／穿插；不要将这个腕口边误当近端 cap。

当前 source 契约保持不变：`grip@0` 为只读 source finger rest/open，`grip@1` 为 source `idle@0` 的 R 指骨闭合，单动画只驱动对应侧 15 条 finger rotation，非指骨维持源 rest。默认 **Rclosed／Lopen**；R 默认 15 指骨姿与 `grip@1` 一致，因此即使当前画面卷握，也不能证明动画时间控制已生效。L closed 仍为左右 rest 骨基镜像派生。源 R 小指中／末节两端 local quaternion 夹角约 13.82°／9.35°，这是 open→closed 旋转差，不是生理解剖屈曲角；自然握柄仍须依实际接触画面判断。装备侧保持握柄，guard／攻击意图不等于是否持有。

Root 后续最小补证为同一手／刀位姿和机位下的实际 `grip@0`、`grip@1` 对照，再补一个能看见柄尾长指与拇指接触、腕口和前臂近端截面的斜视角。由实际指端形变判断 0→1 是否生效，再区分 source closed 本身不自然与运行时姿态问题；截图身份应同时绑定所用模型和修复包。光照问题在同一场景复核，当前不以离线 APPROVE 代替原生握柄通过。

**本次只读复核阶段结束，等待 Root review／补图。** 仅更新本交接；未重做模型，未运行 Blender、设备、Gradle 或 Git，未重跑测试套件，未改正式 source、资产和运行代码。

## 已交候选：原生 PICO 第一人称双手（2026-11-12）

**原生双手资产候选阶段结束，等待 Root review。** [固定收件索引](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/handoff.json)／[完整说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/README.md)／[独立终验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/verification.json)／[四遍 review](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/review.json)。离线终验 `passed=true`、错误与 pending 均为 0，独立 review 为 `APPROVE_OFFLINE_ASSET_CANDIDATE`。仅接入现有单院落短竞技场；不扩城堡、敌群或浏览器试玩。

最终版本 `71c39091c0859a357ed6`：Right GLB SHA `5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d`，Left GLB SHA `cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541`；两文件合计 5,474,684 B。

该候选阶段的制作目录为 `ArtSource/refinement/weapon/native-first-person/`，交接为本文件；候选已交 Root。后续原生修改须有明确获派事项与接入点，当前不继续制作。正式资源、公共 producer、Kotlin、Git、设备与构建由 Root 或原责任方处理，网页维护已停止。

交付约束：米制、+Y 向上／−Z 向前；Right 独立根为实际 dao 握点，Left 独立根为解剖腕点；保留有效蒙皮，用真实指骨动画表达抓松。两手合计不超过 20,000 三角面，手部贴图独立裁切／受控烘焙至常规 2K 以内，再复用现有 `KHR_texture_basisu` 压缩工具，不复制全身 8K atlas。UV 岛不旋转／翻转，核实 normal／tangent 契约。

Root 补充默认装备语义：R 已装备 dao 时保持 closed 握柄，L 默认放松 open；guard／grips／攻击意图不能充当“是否持有”。本路只调整资产默认姿态与交接，保留 `grip` 动画 0=open／1=closed，不改识别规则。

首件需给双手与正式 dao 的 0.3 m／1 m 实际候选图、网格／纹理预算、根与刀实际锚点误差、开闭与无效输入边界、来源 SHA。左闭合若来自现有左右 rest 派生，必须明确标注，不作为作者已校准左手。候选证明不替代 PICO 实机输入与呈现验收。

正式输入为 `ArtSource/tripo-warrior/library/base.glb`，SHA `ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20`；同源可读图版本 `base_prepared_png.glb` SHA `b3fbfe66727d0dd90bd741420937a6c57dbb9e083d76ecd983cd9383ab5bbf96`。两者非图像数据需先核验等价。

最终双手共 **10,578 面**：源 R 4,681／L 5,392 面逐字节保留，另加独立真实衣料收口 255／250 面；原有 78 骨、IBM 和约 1.819813 的人体归一化保留。单 `grip` 动画各 15 指真实开闭，默认 Rclosed／Lopen；左闭合仍为左右 rest 骨基镜像派生。两侧各三张 1536² 图裁切重排后源采样区域逐像素保留，KTX 纹理载荷 5,009,771 B，全 mip UASTC 块约 18 MiB，未实测 GPU 占用。

最终[0.3 m 默认握刀图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_0.3m.png)、[1 m 正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_1.0m.png)、[1 m 反面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_1.0m_reverse.png)均使用最终双手和正式 dao 的实际 KTX level 0 解码像素。另有双手全开／全闭六张边界图，[九图身份与实际相机距离](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/render_manifest.json)已固定。R Grip 原点误差约 `1.72e-7 m`，实际 Base／Tip 为 `1.51e-7／9.44e-8 m`。这是离线局部坐标精度，不是头显精度。

首次提取的黑色开放袖腔／锯齿边已修为真实有厚度收口，开闭时按位置焊接后的组合开放边、非流形、绕序冲突和新增交叉均为 0。[修前四图与输入](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/before/render_manifest.json)保留对照。八次资产契约负例、几何／存储控制、图集五测、压缩共享二十九测与 driver 四测通过。SDK 丢追踪／过期／恢复等输入闭环未由这些制作测试证明。

剩余限制明确保留：近端灰色收口在 1 m 仍偏硬，不能称自然全臂；源手部硬折面／小尖刺、L 三个原 normal 问题面和三个零面积 UV 面仍在，源无 TANGENT。Root 接入后验 SDK 姿态与装备路由、动画控制、MikkTSpace、实际 KTX mip／光照、连续头手姿裁边与性能。本路未改正式资源、公共 producer、Kotlin、浏览器、Git、构建或设备。

## 最新用户目标与执行队列

2026-11-11扩展分工已生效，完整地图见[并行制作入口](README.md)。你主责现有dao的明显几何与材质升级及三角色握持。03收服装结构，05收头脸，08接实际攻击特效。

最新一轮不能只改roughness和金属factor。制作有实际倒角与截面的刀脊／刃口、刀尖过渡、护手铸造边、柄绳编织、端帽与有因果磨损。保持公共刀长和握点语义，握持接触区优先保护，确需变化给明确映射和可见对照，由Root重签。正常游戏视距的刀身反射和轮廓必须有可辨改进。现袖口微小候选与限制交03，继续武器队列，不等待其回复。

Root已开发接收 stage2 实体刀槽／刃脊方向，公共 producer 候选与新刀身份 pin 由 Root 统一处理。当前续项为右手握持 147／55／85 个既有相交手面的实际可见程度与柄核穿透深度，允许只交局部原指骨增量或手部接触几何修正。正常距离、近景、原始 IDs 与真实深度共同验收，保护当前三方向左手与 05 头脸／03 服装组合。

## 当前状态

**右手局部修复阶段结束，等待 Root review。** 已交真实闭合柄核深度、正常距离／手部近景及轴向截面。base 和 indigo 两候选通过本轮局部制作复核，最深采样分别降到约 0.092／0.209 mm。veteran 残留约 1.305 mm、自交增加且实图松握，明确 BLOCKED。当前三角色整体仍为 REQUEST_CHANGES，Root统一选择部件组合与继续派修。

袖口结构后续交 03。[袖口现有实物及限制](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/README.md)和[机读 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/vertex_delta.json)可作为局部组件，当前只完成左侧灰棱约 1.5 mm 径向收细。12 mm 退腕、真实开口和布／皮边界仍待服装结构制作，保护集合也需要按实际手部语义细化。

## 上一轮成果与Root review

三角色握持和非持刀侧局部包络已进入统一producer。主角指面覆盖改善，仍有8.333mm峰值径向代理、深样本增加及源段外交叉。只调挂点和指骨不足以解决衣物／关节变形，本轮补部位级语义和权重审查。

## 文件所有权

负责 ArtSource/refinement/weapon/、现有ArtSource/dao内你明确新增的候选制作源与本文件。正式dao资源、角色producer与挂点校准由Root统一维护。衣物、头脸和其它会话目录保持。

## 本轮任务

1. 冻结 `current-bank` 新刀三角色、alignment、profiles 与原始 SHA。核验当前右指校准已单次烘焙，后续只使用明确增量。
2. 对真实闭合 `Handle core` 做内外分类与最近三角面深度，包含顶点、边中点和面心，报告最坏姿态、原 face／vertex IDs、骨支持与实际截面。开放缠绳单独记录表面交叉。
3. 优先每角色独立静态右指骨旋转，统一作用十段动作。若小范围残留来自接触表面，可试同拓扑局部 POSITION／NORMAL 修正，并保留完整 seam 组及机读 delta。
4. 复核真实柄核深度、各指残留、外绳或相邻指的自然贴靠、非邻接指面自交和可见闭合，保护左手／刀路／腕／挂点及非手部数据。
5. 交正常距离与手部正侧近景前后、柄轴截面、局部修正候选和独立验证。原 producer、正式资源及最终合成由 Root 维护。

## 审核产物

真实几何与纹理候选、正常视距和持刀近景、来源 SHA、部件和材质映射、玩家 Grip 入口、三角色装配及接触检查。量测区分结构合法、表面接触与实际可见收益，运行时观感由 Root 统一验收。

## 下游

Root 审核后统一更新刀具输入、装配身份和挂点校准，再组合 01 动作、03 服装、05 头脸与 07 光照。候选保留各自来源，按部件和数据映射交付。

## 共同执行约束

唯一工作仓库为 /Users/yupeng/projects/personal/pico-wuxia-arena。当前模型基线为main的cc12bf1，base.glb SHA为53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641。运行栈为Kotlin + PICO Spatial SDK6.1.9，终端Space Pro／OS6。

其他会话正在同一仓库并行。各自只修改责任范围，保留其他人的编辑。Git提交、分支、合入、共享构建、设备操作、实际截图与正式模型发布由Root统一负责。候选输出留在各自目录，library、app角色与公共manifest由Root发布。

本轮允许离线资产生成、渲染及专项制作检查。游戏整局自测继续后置。30分钟内交付首阶段实物，写明“阶段结束”、输入SHA、文件、效果、剩余问题与下一步建议后结束当前回合。遇到阻塞先交已做出的部分并写明具体阻塞，继续能独立完成的工作。用当前模型和已安装依赖推进，不为等审批或等待其他线程维持空转。

## 阶段回报

待执行会话填写。

### 部位分区与左腋首阶段交付

**阶段结束，交 Root review，本回合直接结束。** 已在 [deformation 产物目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/README.md)交付分区、缺陷清单、raw body-only 派生 rig、动画展示副本及可复建脚本。当前权重试验明确标为 **`blocked_cross_pose_strain_regression`**，结构合法但动态质量未过门槛，暂不接入正式 producer。

输入完整 SHA 为当前动画 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`、raw rig `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。raw／prepared 的 35,308 顶点、60,006 面同 ID，对应 POSITION、NORMAL、UV、索引、JOINTS、WEIGHTS 完全一致，重排为 identity。归一化矩阵、逐顶点／face 语义和来源身份见 [regions.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/regions.json)与[regions.npz](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/regions.npz)。

### 分区与实际诊断

已建立 14 个解剖区域和 5 类衣物假设，提供 [衣物覆盖正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_base_native_front.png)、[背面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_base_native_back.png)及[解剖中立正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_anatomy_neutral_front.png)、[背面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_anatomy_neutral_back.png)。解剖标签参考已有权重，衣物标签是空间假设，置信度与歧义另记，需结合实际画面复核，不能当作独立真值。

[缺陷清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/defects.json)包含原生 slash、左右迈步、受击、turn 及单独合成转头检查。4740 组重合点均涉及 UV 拆分，16 组有法线拆分，权重不一致为 0，位姿接缝间距为 0；远端手指与 Hand 影响在本次阈值下均为 0。手部保持诊断范围。

首个局部目标选左侧躯干腋下过渡，种子边 `[32080,32220]` 的 rest 长为 23.801 mm，`hit_side 0.35s` 达 63.865 mm。原因实验显示 `L_Upperarm` 的局部影响与该边伸长有关，但孤立转移也会影响周边应变，因此只保留有限拓扑邻域并锁定外圈作试验。

### 派生 rig 与前后实物

- [candidate_rig.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/candidate_rig.glb) 为原 raw body-only 派生，单一 skinned body mesh、原 PBR／UV、78 骨 rest／骨长与逆绑定保持，无 DAO、归一化包装或动作；SHA `66ebbb7513ec70672af6d48f3efb5bd0a81da55bfd42f61dc5b1ed40aaa3eeac`。
- [candidate_base.glb](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/candidate_base.glb) 仅用于原动画同姿态比较，SHA `b1d8c11a2e0cae1406bc2bbbdad1e29c0545bd18da6155f056a9d5832e49fa01`。
- [candidate.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/candidate.json) 记录 5 个被改顶点 `29361、30818、32220、33044、33493` 的部位、原／新 palette、骨名与权重；仅把局部原 L_Upperarm 质量按最轻 25% 衰减转移到原有 Spine01，包含完整重合组，手部改动 0。
- 受击 [PBR 背侧对比](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/hit_side_0350_left_armpit_back_before_after.png)、[线框背侧对比](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/hit_side_0350_left_armpit_back_wire_before_after.png)，以及 [slash 2.117 秒 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/slash_2117_left_armpit_front_before_after.png)、[线框](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/slash_2117_left_armpit_front_wire_before_after.png)均为同姿态／同机位。

### 数值收益、回归与验证边界

| 度量 | 基线 | 最轻候选 |
| --- | --- | --- |
| hit_side 0.35s 种子边长度 | 63.865 mm | 56.283 mm |
| hit_side 区域最大伸长 | 40.064 mm | 35.078 mm |
| hit_side 区域 P95 伸长 | 33.292 mm | 31.152 mm |
| slash 2.117s 区域最大伸长 | 22.523 mm | 25.009 mm |
| slash 2.117s 区域 P95 伸长 | 22.175 mm | 24.263 mm |

四个试算强度均未通过跨姿态门槛，只保留最轻实物供审查。独立 [verification.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/verification.json)覆盖 179 个姿态，最大新增伸长为 **4.402 mm**。数据可证明局部受击拉伸减轻，也证明应变转移导致 slash 邻边恶化。PBR 正视存在前臂遮挡，观感改善细微，线框用于核对几何差异，当前不宣称衣物整体修复或可见品质已达到发布要求。

独立验证的结构部分通过，raw／prepared 权重数组一致、3483 个手部影响顶点保持、未选顶点保持、权重合法，接缝最大间距仍为 0，rest 蒙皮偏差约 0.00000696 mm，未新增源姿态相对翻面或零面积面。正常源检查及变更 rest／POSITION 的拒绝测试通过，分区源哈希漂移拒绝也已执行。动态部分明确失败并阻止发布，完整脚本、映射和拒绝证据均保留。

制作图的限制已核对，当前语义正背图有部分鞋端裁切，可用[带图例板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/previews/semantic_base_neutral_legend.png)复核颜色和部位，足部视觉覆盖仍需补齐。前伸／抬臂／迈步及合成转头的基线检查已保留，完整候选 stress 短片本阶段尚未制作。`stage_rest_positions` 字段实际为归一化 GLB 场景根的模型静止坐标，米制，未包含运行时 Entity 的场景放置变换。

下一阶段建议以多姿态整片应变为约束求解衣物过渡权重，在确认连续衣物结构后再评估更宽邻域，而不是仅追求单边缩短。本会话费用 0，公共脚本、源模型、library、app 和其他会话文件保持各自所有权，正式整合由 Root 选择后执行。

## Root合入前审查补充

派生正式输入保持raw body-only格式，单一带蒙皮body mesh、原PBR／UV、78骨rest／骨长／inverse binds。文件不带DAO、全局归一化包装或动作。分色模型仅用于诊断，顶点变化提供新旧映射。

首阶段手部语义区域的权重改动为0，缺陷只诊断。每个实际修改顶点记录部位、源／目标权重与位置，交Root组合后复核。

Root以派生rig加01手姿统一重建。新target SHA触发旧校准时由Root复审重签，01随后复核实际手柄接触。

## Root首阶段review与续派

分区和缺陷定位接受，首权重候选因跨姿态回归及可见改善不足退回。阶段2补齐脚端分区图，以多姿态区域应变和语义影响为依据，最多三个定向候选，实际可见的尖刺／裂缝／拉花直接拦截。数值变化与可见性共同评审。当前状态为阶段2执行中，失败候选保留为研究证据。

## 阶段2回报

**阶段结束，交 Root review，本回合直接结束。** 实物、参数及剩余根因见 [stage2 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/README.md)。当前三个权重候选均为 **BLOCKED**，未进入公共模型或 app。

### 鞋端裁切已修复

已补齐 [衣物正背分区板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/semantic_base_full_neutral_legend.png)和[解剖正背分区板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/semantic_anatomy_full_neutral_legend.png)。实际 body 包围盒驱动相机，排除 DAO 并加 14% 留白，头、双手和靴端均完整。投影纵向约 0.0614–0.9386，[相机证据](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/full_body_camera_manifest.json)已记录。

### 有依据的部位选择与候选

[纹理／空间复核](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/source_defects.json)确认，旧腰胯和侧腿种子实际属于蓝色裤子，连续裤裆跨腿影响不能直接认定错误。本次只对实际灰色前衣摆 659 个顶点／504 个重合组做定向试验，没有删除对侧腿影响。

使用真实表面拓扑、锁定两圈边界、保留原关节支持集的区域图平均，仅生成 0.2／0.4／0.6 三种强度。每个候选改 251 个顶点，手部权重改动为 0，无新增关节影响或最终 top4 质量裁剪。源 raw／final 哈希分别仍为 `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6` 与 `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`，同 ID 映射、raw body-only 格式与原 PBR／UV、78 骨 rest 合同继续满足。

- [候选清单与固定哈希](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/candidates.json)。三个子目录均有 `candidate_rig.glb`、`candidate_base.glb` 与逐顶点 `weight_changes.json`。
- [0.2 侧面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_020/slash_2117_side_before_after.png)、[0.4 正面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_040/slash_2117_front_before_after.png)，其余前／侧／后及 walk 对照位于 [制作图目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews)。

### 数据与真实可见性分开评审

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/verification.json)覆盖每个候选 579 个姿态。区域平均正伸长 RMS 为 1.5337→1.4879／1.4605／1.4518 mm，平均 P95 为 3.2823→3.1926／3.1526／3.1059 mm，最大 P95 增长仅 0.060／0.066／0.083 mm。这里没有以每条边完全不增作唯一门槛。

实际主要缺陷边 `[34287,34481]` 的两端都在锁定边界，三个候选均未编辑目标本身；slash 2.117 秒仍为 60.349 mm 长、19.248 mm 伸长。内部平滑的数字小幅改善不足以支持主要轮廓已修复，目检仍未证明足够可见收益。该边界／目标不一致是当前试验的明确剩余原因，不能以平均小数字宣布通过。

三个候选还分别有 1／2／5 个最大单姿态法线反向信号，0.2 相关面并非无穷小，0.6 最大源面约 47.5 mm²，并有新增拉普拉斯尖刺候选。它们需要具体 pose 图确认，当前不宣布已看见裂缝，也不据此放行。结构与动态分别记录，raw／prepared 权重一致、手部及未选区域不变、原支持集保持、rest／skin／逆绑定／动画保持，重合组接缝为 0，未新增零面积面；正常与变更输入拒绝检查通过。

最终实图已完成每候选六张同机位 PBR 对照，共 18 张；[0.6 正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_060/slash_2117_front_before_after.png)与[0.6 侧面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage2/previews/harmonic_060/slash_2117_side_before_after.png)也基本不变，较大侧腰鼓包仍在。0.6 的最低相对三角面积比仅 3.54%，需保留挤压风险。纹理与空间选区尚未证明它对应实际相机可见折痕，`gray_front_hem` 仅作为本次数据标识；后续应先从实际问题视图拾取 face ID 与可见性，再重定编辑内部和锁边。新增最坏风险姿态未扩展渲染，当前不提供发布通过结论。

本阶段保留三个有限试验并结束。下一步应先把实际可见目标纳入经确认的连续衣物内部、重新定义锁定边界，再做区域多姿态求解，并区分源网格／纹理折痕与蒙皮变形。本会话费用 0，公共代码、library、app 和其他会话产物由各自负责人维护。

## 阶段3回报

**阶段结束，交 Root review，本回合直接结束。** 完整产物与边界见 [stage3 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/README.md)。实际图像光线拾取、目标内圈证明、最多三个新支持集候选和 bind 几何证据已交付，三个候选均保持 **BLOCKED**。

### 实际图像拾取与目标修改

[target.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/target.json)固定当前 final `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641` 与 raw `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`。侧视像素 `(400,320)` 实际命中灰衣面 **43900**、顶点 **31463／32012／30406**，重投影误差低于 1 像素；旧边 **34287／34481** 也已纳入核心。新 ROI 为 513 组／667 顶点，五个目标均在可编辑核心且 fade=1，锁边移到外圈，冲突为 0。

本轮只生成 [contra_half、pelvis_025、pelvis_045 三个候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/candidates.json)，分别减弱对侧腿跟随、转移 25%／45% 双腿质量到 Pelvis／Waist。它们是衣物支持集实验，未把跨腿影响自动定性为错误。新增 Waist 仍在原 78 骨内，每顶点最多四影响、归一化，手部语义权重改动 0。每个目录提供 raw body-only rig、同权重的原动画预览及新增／移除影响、部位和 pose 依据的 `weight_changes.json`。

三个候选实际改 316／466／466 顶点，全部五个要求目标都已变。主面三个顶点分别移动约 **2–4／34–38／62–68 mm**，已排除上轮“目标本身没改”的情况。

### 动态失败与轮廓覆盖仍不足

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/verification.json)覆盖每个候选 179 姿态，结构、原 rest／IBM／UV／拓扑、合法新支持集、手部与接缝检查通过。区域平均 RMS 为 **1.966→2.021／2.550／4.168 mm**，平均 P95 为 **4.223→4.573／5.411／8.299 mm**，最大新增伸长为 **5.345／7.421／38.546 mm**。法线相对反向峰值为 11／24／45，存在显著面积缩小，不能因命中面已经移动就宣布改善。

补充轮廓拾取发现，实际外沿像素 455／456 对应灰衣面 **26875／25779**，控制点 **35019／34731／35089／34795** 在三个候选均未改，原因是位于主面 0.18 m 图距离外或锁边。第 320 行右侧轮廓均为 **457→457**。因此当前尝试尚未覆盖完整的轮廓控制面，不能把它解释成权重方法原则上无法改变该轮廓。

### 已定位的 bind 几何与最小后续范围

已交付真正 bind 与原生姿态的 [clay 同面板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/bind_vs_native_clay_targets.png)、[PBR 板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/bind_vs_native_pbr_targets.png)、[wire 板](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/bind_vs_native_wire_targets.png)及[跟踪主面近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/stage3/previews/side_bulge_tracked_bind_vs_native.png)。Bind 已关闭 NLA 并将骨骼 basis 归零，非 idle 帧；同面邻域凸起在 bind 已有 **9.521 mm**，slash 为 **6.787 mm**。静止几何本身确有凸面，不能简单当作错误权重，艺术形状是否需改仍由 Root 判断。

若要改变 bind 凸面，最小新增范围是：按实际轮廓面 26875／25779 与主面 43900 重新选连续衣片，先测衣物／腿的间隙，再以同拓扑局部 POSITION 修形或姿态形状修正处理，保留 seam 组一致并重核 NORMAL／TANGENT、多姿态碰撞。此几何修改本轮未实施，需另派明确范围。若继续权重实验，则必须先完整覆盖轮廓控制面，再评审边界和骨影响，避免重复只移动内部点。

纹理／空间独立核查已排除蓝裤控制点，bind 的 pinch 面还存在约 14.95 mm 叠层遮挡，均记录于 target。其他 14 区未追加全面重扫。当前三个候选只保留研究证据，费用 0，公共代码、library、app 及其他会话产物未由本会话改动。

## 当前阶段3执行项

责任目录为deformation/stage3。由实际缺陷视图拾取face／vertex，主要目标应在编辑内圈，锁边不能把目标本身冻结。允许衣物ROI在现有78骨中改变合理vertex支持集合，新增／移除影响给部位与pose依据，max4归一化，骨架rest／IBM／UV／拓扑保持，手部语义权重改动0。最多三个定向候选，以真实可见改善和跨姿态风险共同判断，必要时明确几何／动作根因。

## Root阶段3 review与阶段4续派

Root已查看同面跟踪与bind／native PBR图。该处存在源衣物折层及自然凸面，三轮权重修改均没有足够可见收益，全部BLOCKED保持。当前不将此处普通布料体积作为必须抹平的缺陷，结束该目标的权重实验。

阶段4责任目录为deformation/cuff-refinement，独立于03的前领几何。围绕已接受的设计板落实袖口退腕与布／皮护腕边界，先交真实模型近景与量测，再做最小同拓扑几何修整。

1. 读取原raw rig与01已审slash_guard_raw曲线，在REST、slash 1.367／2.117秒及walk姿态查看左右袖口、裸露腕部与护腕。交同机位近景、原face／vertex ID和实际缝隙、厚度与腕褶位置。明确区分有意贴合与可见穿插，不用单纯边伸长替代画面问题。
2. 以窄布缠腕、薄旧皮固定带和袖口退腕12mm设计为方向，选择一个证据明确且能局部修复的袖口轮廓。允许局部POSITION／NORMAL修改，优先保原拓扑、UV与所有权重，手部语义顶点和权重保持。不得改骨架rest、IBM或01曲线。若源融合几何不支持该目标，交出具体面范围与最小拓扑修改提案，先完成可独立修正的一处。
3. 输出机读delta、来源SHA、raw body-only GLB和成对素模／PBR图，保留原材质。30分钟内交第一项可见实物，后续离线专项检查覆盖原slash和walk的袖口／手腕关系。Root负责与03领口、04材质组合及正式发布。

其他会话共享仓库，保持其编辑。公共producer、manifest、正式library/app、Git、共享构建和设备不在本会话范围。阶段交付后若Root正在集成，可独立测量另一侧袖口并给同规格候选，避免等待。

## 阶段4袖口首项交付

**本袖口阶段结束，交 Root review；按最新队列继续现有 dao，不等待重复批准。** 本次实物与完整限制见 [cuff-refinement 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/README.md)。当前只交左侧近端灰色外棱局部径向收细，**未完成 12 mm 袖口退腕、新开口及布／皮完整重制**。

输入为原 raw rig `43a34e3ab236e42a96510ccd07f72bab4090bad805c4d883cde21f395d2b81e6`，01 已审 raw 曲线 `43e0ca0b0501f4be4dc066e045d1b60092e3bd65aea228bc3a2a32405f826391`，同 ID 预览 `34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896`。01 raw 有 35,325 顶点，原 body 为 35,308，已避免误用 ID，实际袖口姿态使用 approved preview。

### 首项候选和实际图

- [raw body-only 候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/candidate_rig.glb)，SHA `9ccd0717ca850196accd8351dd4f8bf6f139957a9b86f4fbcbd4505c1910f5d4`。
- [机读局部 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/vertex_delta.json)，184 个 POSITION、277 个 NORMAL；最大模型空间径向收细 1.499966 mm，轴向位移近零。只按 delta 与其他会话合成，不整文件覆盖领口／材质。
- [REST A 面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/previews/rest_left_A_pbr_before_after.png)、[REST B 面素模](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/previews/rest_left_B_clay_before_after.png)、[guard 1.367 秒 B 面 PBR](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/previews/guard_1367_left_B_pbr_before_after.png)均同机位，共八张左侧对照。径向变化细微，B 角度较清楚，尚待 Root 判断是否接受为局部组件。

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/verification.json)通过，所有权重／UV／拓扑／rig/rest/IBM／原材质与已存在的 01 曲线保持；严格手／皮肤保护集合的 POSITION／NORMAL 未改。REST、guard 1.367／2.117 秒与 walk 四姿态无新增三角反向、零面积或衣物—保护面确认交叉。最近保护集合表面间距约 12.343 mm，这不是袖壁厚度或裸腕长度。完整补间及设备观感尚待后续。

### 退腕结构限制与后续最小范围

[measurement.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/deformation/cuff-refinement/measurement.json)定位到左侧布／皮肤过渡面 58422、58454、58485、58487、58488、58489、58522、58573、58615、58676。Hand 参考后 12 mm 截面穿 66 面、66 段，周长约 241.622 mm，是身体参考截面而非独立袖口。焊接开边为 0，但这个数字本身不能证明没有封闭衣壳或必需重拓扑。

当前保护集合包含所有 Hand/finger 影响，强于实际手语义，677 个左侧灰缠腕点因保守策略未动。后续应先通过实际材质、颜色和结构确认手与衣物；若有独立衣物环，验证同拓扑退移；若确认融合，则给袖侧环复制／重索引及最小内腕、布壁和局部 UV 方案，原手顶点保持。当前没有冒充实现真实 12 mm 开口，右侧候选与窄布／薄皮材料分工仍待后续。

本轮费用 0，实际发布由 Root 统一处理。当前有效阶段已收口，继续 `ArtSource/refinement/weapon/` 的独立 dao 候选。

## 刀具首轮材质响应交付

**本阶段结束，等待 Root review，当前回合结束。** 完整产物、固定 SHA、参数和限制见 [weapon 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/README.md)。本轮完成材质响应候选及几何量测基线，整体刀具精修仍有后续工作。后续按本文件顶部最新队列继续，避免因等待重复批准而空转。

### 双入口实物与三角色制作副本

- [NPC 刀具候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/dao_response.glb)，源 SHA `0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616`，候选 SHA `ed06ec82a709ce2e21d867e6d8d3cfd95557b92e58b9d8dc553e8fad9463496a`。
- [玩家 Grip 候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/dao_grip_response.glb)，源 SHA `a2a5eae94ef6f577697d6c91a5cd4d7fe22e09e2f8b8e4411cd53768751739fc`，候选 SHA `a579748a3edd4b378b896cd6c387c222f11bd107c2a740e1630600437f7cb48f`。玩家入口为 Grip identity、+Y 向上、−Z 刀轴。
- [机读材质 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/material_delta.json)记录七个粗糙度字段及刃口金属度。刃口粗糙度约 0.27→0.19、刀脊 0.40→0.45、旧黄铜 0.48→0.55，其他值见完整表。八个部件槽具明确原名，可供 Root 继续区分身体白闪与刀具。
- [三角色私有清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/actor_manifest.json)提供 base／indigo／veteran 前后 GLB。base 采用 01 已审 guard 预览 `34ced4fb666e17fa066e75c83baffbf8c3e37d5e6cfb15f49549a9bca6c98896`，尚待 Root 与领襟、袖口和其他材质组合。

### 实际图与效果边界

独立刀具两套固定灯光各有正／斜／背及护手柄近景，三角色各有正／侧／背及持刀近景，共 20 张前后板。

- [常规灯光正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/standalone/front_before_after.png)、[反射灯斜面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/reflection_test/oblique_before_after.png)、[反射灯护手柄近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/reflection_test/guard_grip_before_after.png)。常规灯下刀面偏暗，反射灯下亮面趋白，前后差异均较轻微，视觉收益待 Root 判断。
- [base 持刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/actors/base_before_after.png)、[indigo 持刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/actors/indigo_before_after.png)、[veteran 持刀](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/previews/actors/veteran_before_after.png)，全身三视图见 weapon 说明。头、靴与刀尖完整入画，部分刀面呈侧缘或被身体遮挡，前景空手也遮住部分刀柄。完整接触面与既有穿插仍需专项处理。

### 量测、验证与下一步

[实际量测](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/source_measurements.json)记录 13 mesh、3,722 面、8 材质，全刀约 104×967×39 mm、标记刀段 720.676 mm、护手轴向厚 18 mm、缠柄约 18 圈及五处刃／脊截面。本轮几何 delta 为零，新增倒角、护手减薄、缠绕造型及局部接触磨损继续作为后续制作项。

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/verification.json)已实际运行，NPC／玩家／三角色五个入口的完整 BIN 与非材质 JSON 一致性通过，涵盖几何、UV、节点、锚点、skin、rest 与动作。正常候选及锚点／网格／源 BIN 变更拒绝通过，生成器四类非法材质更新拒绝通过。当前验证支持有限材质补丁交付，现有手部接触问题仍需解决。

后续刀形与握持联合精修继续使用米制长度、Grip 和真实手表面约束。Root负责新文件身份复审、校准重签、正式组合与发布。玩家帧当前已验证结构与材质，独立玩家帧渲染仍待制作。现有低采样离线图适合首轮方向审查，PICO 实时加载、游戏 IBL、实际持刀输入、连续补间、完整三轮与 Space Pro 性能尚待验证。本阶段费用 0。

## 刀具第二轮真实几何与表面交付

**阶段结束，等待 Root review。结构 PASS，接触审核待修。** 完整实物、来源、装配、验证与限制见 [stage2 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/README.md)。本轮已交可见实体刀槽和截面分光，新增左手相交范围须继续处理。

### 实物和可见变化

- [NPC 候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/dao_refined.glb)，SHA `4834a555d70f80151bbe19358c0a94c11e1c3f76ab2e501bf6e70c2860bcf452`，源为 `0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616`。
- [玩家候选](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/dao_grip_refined.glb)，SHA `a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637`。另交 [可编辑 Blender 源](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/dao_refined.blend)及几何、表面生成脚本。
- 刀身细化为 66 轴向站位、21 点截面，原窄条改为约 5–7 mm 实体槽并向刀尖收束。护手铸造压边和端帽凹面已重建，总三角 3,722→8,702，13 部件、8 材质，NPC 约 2.889 MB。26 张实际 PBR 制作图中 18 张嵌入 GLB，涵盖打磨／磨痕、氧化、柄绳织纹和皮革压痕，部分磨损仍属部件／UV 假设。
- [刀槽近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_blade_oblique_before_after.png)、[2.2 m 刀具](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_normal_distance_before_after.png)、[玩家帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/player_grip_held_frame_before_after.png)、[base 斜角](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_normal_oblique_before_after.png)、[veteran 右侧握柄](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/veteran_grip_back_before_after.png)。共 25 张成对板，900²／24 samples，正常视距透视约 2.2 m，所有机位与来源 SHA 已固定。独立刀具的槽与反光可辨，角色当前正面刀面偏暗，正式场景可读性仍待与 07 光照共同评审。

### 三角色与真实接触门槛

[三角色清单](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/actor_manifest.json)使用当前正式 base／indigo／veteran 冻结输入，各含原八段动作。候选保留三人各自 `HandGrip_R` 与刚性蒙皮装配，身体／权重／skin/rest/IBM／动作保真通过，15 个刀 primitive 与 canonical 装配吻合，独立最大 POSITION 差约 0.000101 mm。原握柄保护表面位置差 0，重导 cord NORMAL 最大差约 0.000615，映射已记录。

[结构验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/verification.json)双入口及三角色通过，三类几何与六类装配边界拒绝通过，实际 GLB 导入通过。原材质名和身体 `tripo_` 白闪命名合同满足。GLB 具有有效 NORMAL／UV，无 TANGENT，客户端 MikkTSpace 生成和 PICO 法线显示待 Root 端内验收。

[接触审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/contact_audit.json)覆盖每角色 13 离散姿态、前后和左右手。右手握柄指标沿原结果，既有指柄相交仍存在。2.117 秒左手三人均无交叉，但早段原生左手穿刀仍在，候选增加部分受影响面，因此 `contact_clearance_accepted=false`。

- base 1.3167 秒相交手面 17→19，完整受影响手面面积 1019.314→1113.313 mm²，新增 58792／58823。
- veteran 1.367 秒 30→32，3303.844→3489.241 mm²，新增 19607／19789。1.5 秒 43→45，3460.628→3582.143 mm²，新增 15568／15569。
- [base 风险实图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_risk_1317_left_front_before_after.png)、[veteran 风险实图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/veteran_risk_1500_left_front_before_after.png)及反面均已补齐。源与候选均可见穿刀，新增面证据仍保留。面积是完整手三角面之和，穿透深度及真实重叠面积尚未量化。

下一项先修左手接触扩张，结合 01 最新动作核对早段空手与刀面，再交正常场景高光与连续补间。Root负责正式 producer、挂点身份重签、模型组合和发布。袖口结构已交 03 的现有实物与限制入口。实际输入、PICO 实时加载、Space Pro 观感与性能仍待验证，本轮费用 0。


## 当前十段动作库适配

**阶段结束，等待 Root review。** Root 在几何阶段收口时发布 `attack_overhead/attack_left/attack_right` 三方向，正式角色由八段变为十段。本会话继续完成新库装配、检查和实图，完整说明见 [current-bank 交付](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/README.md)。旧阶段接触限制和来源保留，新库结果独立记录。

### 最新输入、输出与接入

[actor_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/actor_manifest.json)记录当前十段动作输入、私有 profiles、各自 `HandGrip_R`、新刀部件和完整 SHA。

- base 源 `0c2a4801aaa6b89866303a9c783b524a88b6440633f0c9348041a6239af7d48a`，候选 `e7f3de3d8c7e202999b2d456ae85257b89a01e7c21792f332c4b273c77b60cbc`。
- indigo 源 `c980b18ef19190bf682604a43b730c3a0188829db8ea1c7c9e5d819d1959fed2`，候选 `448d46394743018aff3165e0e49e5c07480b617664c072c14ab6ae186cc87ef3`。
- veteran 源 `63b92ac8edda1ab7ad56e2d3196522788fec8a43a04c0d665deef08028d82e83`，候选 `0c0b57a4f3684a25603a6875b2fd9188096755dc4b3688d921a7de8776f1e9c2`。

独立新刀仍为 NPC `4834a555…`／玩家 `a09ba1f7…`。复用同一装配入口的 `--output` 参数，十段动作、身体、skin/rest/IBM、权重、各人挂点和原身体白闪材质保真通过。实际 GLB 导入通过。profiles 冻结并核验原模型签名，候选发布身份需 Root 重新生成／重签。

### 三方向接触与实图

[结构验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/verification.json)通过。[接触审计](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/contact_audit.json)按实际 0–1.75 秒键域采样，每方向 9 个等距离时刻及关键 .65／.9／1／1.1 秒，共 13 姿态，再加 walk 中点，每角色每版本 40 姿态。

三角色左手全部无确认交叉、无新增受影响手面，最近间距约 106.455／90.375／54.947 mm。右手握柄相关指标前后相同，既存受影响面峰值 147／55／85。整体握持仍保留人工验收状态，连续补间与实际穿透深度尚待验证。

最终交 18 张三方向成对板、36 张单图，包括约 2.2 m／20 mm 正常视距与握柄近景。[base 正劈](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/previews/base_attack_overhead_normal_oblique_before_after.png)可见刀槽和截面分光，[indigo 左斩](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/previews/indigo_attack_left_normal_oblique_before_after.png)的侧缘材质变化较小，[veteran 右斩握柄](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/previews/veteran_attack_right_grip_back_before_after.png)可复核原指面与新柄、护手、端帽关系。全部同机位与输入／图像 SHA 已核对。

离线预览器已修正新短动作的 NLA 完整区间平移及 0 秒起键采样，三角色×三方向 1 秒 R_Hand 对纯 GLTF 最大差约 0.000897 mm，首批偏差图已重出。旧长 slash 三组另外核对，最大差约 0.01604 mm，旧 25 图的标注时刻继续有效。[姿态验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/pose_validation.json)与[旧库校验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/legacy_pose_validation.json)均留实际数值。

[相机投影验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/current-bank/camera_validation.json)覆盖实际蒙皮后全身和刀具顶点，18 张正常距离单图均有至少 1.5% 留白，头、靴及刀尖完整。PICO MikkTSpace、法线显示、正式 IBL、动态高光、真机画质与性能仍待验收。下一项为 Root 复审部件与新库装配后重签模型／profile 身份，再结合 07 光照核正常交锋可读性。本轮费用 0。

## 右手柄核深度与局部修复交付

**阶段结束，等待 Root review。** 完整方法、实物、局部合同和限制见 [right-grip 说明](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/README.md)，选定文件及完整 SHA 见 [handoff.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/handoff.json)。base 与 indigo 可供局部组合审核，veteran 只保留失败取证。

### 实际深度与可见程度

[baseline_depth.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/baseline_depth.json)检查真实闭合 `Handle core`，先验证焊接流形／定向，再用射线奇偶、实际世界蒙皮三角最近距与 winding 独立复核。顶点、边中点、面心按同一原 ID／重心表比较，每角色覆盖三攻击六关键时刻及 idle／walk，共 20 姿态。开放 cord 单独记录表面交叉。

| 角色 | 原最大采样深度 | 最终最大采样深度 | 最坏姿态核内样本 | 结论 |
| --- | ---: | ---: | ---: | --- |
| base | 11.486 mm | 0.092 mm | 276→1 | 局部候选通过制作复核 |
| indigo | 2.926 mm | 0.209 mm | 66→10 | 指骨＋局部几何候选通过制作复核 |
| veteran | 11.509 mm | 1.305 mm | 174→5 | BLOCKED，自交与松握未解决 |

0.25 mm 为本会话暂用工作判定阈值，待 Root 确认，数值不是工具精度／误差条。实际负值与有限采样限制均保留，未宣称严格零穿透。仅测顶点会把原 base／veteran 低估为 7.926／6.070 mm，不能代替手三角面量测。

[base 正面前后](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/previews/candidate2/base_grip_front_before_after.png)可见拳孔缩小、拇指跨到食指外侧形成较清楚的 power grip，[正常距离图](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/previews/candidate2/base_normal_oblique_before_after.png)和[实际截面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/sections/candidate2/base.png)一并提供。拇指可由邻指支撑，整指距柄最小值或旧贴柄点集合均不足以判断是否自然握持。

[indigo 近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/previews/contact_geometry/indigo_grip_front_before_after.png)变化较细微，未见明显新增塌陷，接触区仍有部分遮挡。[截面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/sections/contact_geometry/indigo.png)展示原最深小指样本已到核外，其他部位残留由全手深度报告给出。

[veteran 失败近景](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/previews/candidate2/veteran_grip_front_before_after.png)显示四指与柄的关系变松，拇食指严格非邻接三角交叉由原 23 对增至 57 对。其核深度虽减少，整体握持回归，保留 BLOCKED。[失败截面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/sections/candidate2/veteran.png)不能作为可用修复证明。

### 局部补丁与组合合同

- base [候选 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/candidate2/base.glb)，SHA `1656ddc663ec6d11114c7cf4b404a926fab25001b50290a2cd38663ef1bf6064`。只改八根右指骨在十段动作中的 80 条旋转输出，其余 2260 条及身体、刀具保护数据精确。20 姿态自交峰值 52→51，个别 `attack_right@.65` 为 50→51，完整限制保留。
- indigo [最终 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/contact_geometry/indigo.glb)，SHA `51ee34eda9ef3b81eb30cfff8d169279e6c87d13611cad4dbb12a4cf33ef22c2`。先应用 Pinky1／2 增量得到 13ef 源，再组合 [几何 delta](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/geometry_delta.json)中的 101 POSITION／212 NORMAL。最大实际世界位移约 2.251 mm，UV／权重／拓扑／曲线／rest／IBM 保持，0 翻面。同位缝和法线组误差 0。局部射线弦长 5.621→4.247 mm 仅为邻折层代理，真实厚度尚待审。
- veteran [失败 GLB](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/candidate2/veteran.glb)，SHA `7f37b80b5c4725c01109b95d8cf0b63865163bc1846221d848cc75868363cc4e`，身份绑定的失败参数、原 IDs 及耦合试验见其 manifest，仅用于派修取证。

现有右指旧偏移已经烘焙一次。对本轮 prepared 源使用 `prepared_q @ q_delta_post`，fresh native 重建使用已组合的 `native_q @ combined_existing_offset`。绝对目标四元数另外提供核对。Root复用原 `prepare_character_library`／`apply_finger_rotation_offsets` 及局部几何组合步骤，按选定局部数据处理，重签模型和 profiles 身份。

[独立验证](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/candidate_verification.json)完成 base／indigo 全 20 姿态同表复核、保护数据、左手／非右指体点／R_Hand／刀姿测得变化 0，以及四元数单次重放、实际加载和非法输入拒绝。veteran 的失败身份与最坏姿态另行独立确认。[四遍 review](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/review.json)结论为两局部通过、三角色整体 REQUEST_CHANGES。

最终共九张正常距离／手部正侧成对板、三张前后固定截面图，均给来源与实际姿态。下一项为 veteran 改变拇指绕柄轨迹或局部接触结构，避免继续靠同一退出方向放大角度。连续表面最大深度、完整过渡、真机近距画质／性能及 Root 最终组合仍待验收。本轮费用 0。

另已检查连续三角面凸半空间探针，实际柄核为非凸体，最大外违约约 0.133 mm，方法 [明确 unavailable](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/right-grip/surface_depth_probe.json)。本轮不以凸包替代真实柄核，有限采样限制保留。

## Root本轮组合审核与续派（2026-11-11）

审核：实体刀槽／刃脊与护手方向通过开发集成审核；weapon-only正式发布已执行，三角色动作和proxy坐标保持，玩家Grip一并替换。

下一步：量测右手真实可见穿透深度并交局部修正；现有面交叉计数不能代表实际深度，保护新三攻左手。
