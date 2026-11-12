# 原生第一人称双手／前臂候选

**阶段结束，等待 Root review。** 独立四遍 review 为 `APPROVE_OFFLINE_ASSET_CANDIDATE`，资产终验通过，九张实际 KTX 解码图已核对身份。正式发布、Spatial Entity 与 SDK 输入接线、原生运行时验收由 Root 负责。

[固定收件索引](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/handoff.json) · [独立终验](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/verification.json) · [四遍 review](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/review.json)

默认装备实际图：[0.3 m](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_0.3m.png) · [1 m 正面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_1.0m.png) · [1 m 反面](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/native-first-person/previews_ktx/hands_dao_equipped_default_1.0m_reverse.png)。其余六张开闭边界图见 `previews_ktx/render_manifest.json`。

## 交付与绑定

`right_hand.glb`、`left_hand.glb` 为各自独立的 `KHR_texture_basisu` 候选；`*_hand_png.glb` 是制作输入，不是运行时 PNG 回退。完整身份见 `rig_manifest.json`、`compression_manifest.json`，最终收件以 `handoff.json` 为准。

固定版本 `71c39091c0859a357ed6`：右手 SHA `5fbde4a7d432768fb3b0cbd77a7846e5cd49b221acb829616e7b3051a46c1a1d`，2,515,388 B；左手 SHA `cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541`，2,959,296 B。两 GLB 合计 5,474,684 B。
| 资产 | 唯一场景根 | 根语义 | 原源面 | 新增衣料收口面 | 合计 |
| --- | --- | --- | ---: | ---: | ---: |
| Right | `RightGripRoot` | 实际 dao Grip，米制，+Y 上／−Z 刀前 | 4,681 | 255 | 4,936 |
| Left | `LeftAnatomicalWristRoot` | 实际 `L_Hand` 腕原点，+Y 手背／−Z 指向 | 5,392 | 250 | 5,642 |

两手合计 **10,578 面**，没有减面。两个场景根均为 identity，可以分别绑定对应的跟踪目标；Right 是握点，Left 是腕点，不能把两者当作同一种 SDK 原点。78 骨、原 IBM、原选中顶点的 POSITION／NORMAL／JOINTS／WEIGHTS 逐字节保留。源约 1.819813 的人体归一化保留，只有额外刚体坐标转换，不通过反向缩放缩小手部。

原生 NPC 刀的刀前是 +Y，玩家正式 dao 的刀前是 −Z，实际映射为 `p_player=(x,z,-(y+0.114))`。右手使用 `Rx(-90°) × inverse(rigid(source-rest HandGrip_R))`；原内部 `HandGrip_R` 仍是 native 轴，转换后的逻辑握点才是玩家 Grip identity。锚点复核要同时检查此轴映射及真正的 `Blade_Base`／`Blade_Tip`，不能只比较同名节点的位置。

正式玩家刀的 `Blade_Base=(0.022,0,-0.129)`、`Blade_Tip=(0.0532,0,-0.849)` m，两标记段长约 0.720676 m，包含源刀实际轻微弯曲。此候选没有把刀轴拉伸成网页旧交互段的长度。

独立实际矩阵复核：R 转换后 Grip 原点误差 `1.7188663e-7 m`，Base `1.5137325e-7 m`，Tip `9.4379766e-8 m`；完整轴矩阵最大分量误差 `2.3050027e-7`。这是 GLB 局部坐标和浮点精度的离线误差，不是头显追踪精度。

## 抓松与来源

每只手只有一个 `grip` 骨骼动画：0 秒为 open，1 秒为 closed，十五条对应侧指骨 rotation 通道以 LINEAR 插值，0.5 秒可取中间形变。非指骨保持源 default/rest，不播放全身 idle 的祖先肢体运动。

按 Root 最新装备语义，资产默认 **R 握柄 closed、L 放松 open**；已装备侧保持握柄，架刀／攻击意图不等于是否持有。`grip` 的 0／1 仍是独立形变端点，open 从只读 source rest 固定，不因 R 默认闭合而丢失。本路不修改识别规则。Root 接入时应按装备状态选择显示姿态，不能直接把 guard boolean 当作开闭手。

R closed 来自正式源 `idle@0` 的实际指骨 local quaternion。L closed 是将 R curl 在实际左右 rest 骨基中镜像后的派生，**不是作者校准的左手握刀姿态**。本候选不提供闭合左手与某件武器的接触保证。

来源身份：

- 正式 `ArtSource/tripo-warrior/library/base.glb`：`ac7dfbc606cb968dc8e4ca4e50f877bff431ad18b1a23526197dfc4edc14da20`。
- 同源 `base_prepared_png.glb`：`b3fbfe66727d0dd90bd741420937a6c57dbb9e083d76ecd983cd9383ab5bbf96`。两者非图像 JSON、2,587 个非图像 bufferView 与归一化纹理语义精确一致。
- 正式 `dao_grip.glb`：`db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0`；PNG 制作同源为 stage2 `dao_grip_refined.glb`：`a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637`。非图像数据已独立核对一致。

`selection.json/npz` 保留原 primitive、face、vertex ID 与 compact 映射。首次原样提取的开放袖腔在 1 m 明显可见，拒收版本与四图固定在 `before/`。修整增加独立 primitive 和衣料材质，原手／袖三角不动。源截边轴向参差 R 61.18／L 46.80 mm；新增过渡实际轴向长度 R 4–65.18／L 4–50.80 mm，并有 1.5 mm 卷边及闭合衣料截面，不称为仅 4 mm 的窄边。闭合统计是跨 primitive **按位置焊接后的组合边界为 0**；原 primitive 自身仍保留 51／50 条源开边。

九张实际图中旧黑腔与锯齿开放裁口已消除。1 m 尤其反面仍能辨认新灰色锥面／圆盘是资产近端收口，质感比原布面偏硬，不能称为自然全臂。连续头手姿和实际第一人称裁边继续由 Root 验收。

## 贴图与预算

每手三张 1536² 图，保留 baseColor／normal／metallicRoughness。源三张 4096² 不是全量复制；逐 UV 岛按原像素密度裁切重排，没有旋转、翻转或重采样，正向统一比例和平移保留 UV 导数方向。原采样 footprint 逐像素精确，外加 16 px 扩边，Clamp 两轴；实际双线性抽样最大差为 0.004477/255，来自 float32 UV 舍入。

六 PNG 共 3,589,582 B；原始 RGB 展开 40.5 MiB，完整 mip 的 RGB 理论约 54 MiB。六图 KTX 共 5,009,771 B；完整 mip 的 UASTC 4×4 块合计 18,874,656 B（约 18 MiB），**不是 PICO GPU 实测显存**。新增收口使用邻衣实际采样的实色粗糙布料 PBR，不加黑色遮挡片，不改六张图。

压缩直接复用现有 `pbr-compression/compress_pbr.py` 和官方 KTX-Software 4.4.2：UASTC q3／Zstd18／完整 Lanczos4 mip，normal／MR 为 linear，baseColor 为 sRGB；输出只有 required `KHR_texture_basisu`，无 PNG fallback。实际编码命令、工具 SHA、mip、逐图验证及新 GLB 身份见 `compression_manifest.json`。

源 body 无 TANGENT，本候选也不伪造。Root 需确认 PICO 从实际 NORMAL／UV 生成 MikkTSpace；新增实色收口没有 normal map。L 的原 face 50347、50348、50349 属于两个零面积 UV 岛，保留并明确标注；这些面不能被算作 TBN 已保证。

L 原 source face 48751、50091、50092 另有继承的法线／几何面方向问题，未混作本轮新增错误。新增衣料所有面法线与实际绕序的 signed-average 点积均为正，独立最小值 R 0.901240／L 0.904999。源手部近景仍有硬折面和小尖刺，本轮不称为手部精修完成。

## 验收证据与范围

`previews_ktx/` 的最终图从最终 KTX **level 0 实际解码像素**的双手与正式 dao companion 渲染，非预压缩图代替。默认 Rclosed／Lopen、两手 open、两手 closed 各有 camera 到实际 R Grip 的 0.3 m 近景、1 m 正面和 1 m 反面。默认图明确按装备姿态采样，另两组是动画边界研究，不是张掌持刀的正常显示规则。近景有意裁去刀尖；没有改变模型比例。它们使用 Blender 过滤，不是头显截图，也不验证 PICO 对 KTX mip 链／各向异性的实际选择。`before/` 是开放袖口的旧 PNG 同源图，比较时也应区分压缩像素来源。

最终 renderer 禁用 Blender 自动生成的隐藏骨骼显示球，按可渲染、被面引用的顶点统计手部 bounds。首次 renderer 曾把隐藏的 1 m 半径／42 点骨骼辅助球计入量测，旧 manifest 已明确标记该 bbox 无效；旧图片未渲染此球。

独立检查以导出 GLB 实际读取值复核：源数据／根及 dao 实际轴点、15 指 0／0.5／1 秒形变、原属性子集、衣料新面及位置焊接闭合、权重与自交、UV 岛与实际采样、PNG→KTX 非图像保持。新增属性还校验 descriptor 与 payload 的实际 dtype／字节覆盖，防止 JOINTS 写 u16 却声明 u8；错误的中间身份已作废。空 clip、根偏移、NaN 位置、越界索引与错误属性存储的负例属于资产／制作契约验证。

SDK 输入的 NaN／丢追踪／过期／恢复、动画时间控制、手刀隐藏与释放、实际光照、前臂裁口在连续头手姿下的可见性和持续性能，均由 Root 接线后验收。本候选不将静态场景图、制作负例或离线动画等同于真实 SDK 输入闭环。

## 复建入口

在唯一仓库根目录执行，Blender 使用本机 4.5 LTS：

```sh
BLENDER_BIN=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/weapon/native-first-person/build_hands.py -- --selection-only
python3 -B ArtSource/refinement/weapon/native-first-person/bake_hand_atlas.py --self-test
python3 -B ArtSource/refinement/weapon/native-first-person/bake_hand_atlas.py
```

冻结 `atlas_manifest.json`／`uv_remap.npz` 与六张 PNG 后，同一 Blender 命令去掉 `-- --selection-only` 生成两只完整 PNG GLB；此 producer 内含实际写后类型、蒙皮、收口拓扑与法线检查。先独立审核 PNG；`verify_hands.py` 的 `PNG_assets_passed` 可用于本阶段判定，未重建 KTX 时全局报告仍会保留 pending。确认本次 PNG 通过再发布压缩候选：

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/compress_hands.py --right-sha256 <已审核R的SHA> --left-sha256 <已审核L的SHA> --publish
```

省略 `--publish` 只生成该 source SHA 的私有版本，不覆盖收件别名。实际图由 `render_hands.py -- --decoded` 在 Blender 后台渲染，必须先存在与本次最终身份对应的 `compression/decoded/*_decoded.glb`。

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/verify_hands.py
"$BLENDER_BIN" -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/weapon/native-first-person/render_hands.py -- --decoded
```

本轮独立负例为左右各四类共八次（空动画、逻辑根偏移、NaN 位置、越界索引），另有七个几何控制与三个属性存储控制（含 u16 payload／u8 声明错配）。图集五项夹具、共享压缩工具原有二十九项测试均已执行通过。
