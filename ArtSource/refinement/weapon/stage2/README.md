# Dao 几何与表面第二轮

**阶段结束，等待 Root review。** 本轮交付真实几何、PBR 贴图、双入口与三角色私有装配。结构验证通过，接触审核待修，当前为制作候选。刀槽和刃脊分光在独立刀具同机位图中可辨，角色正面在当前 slash 姿态下仍有背光、侧缘和遮挡限制。

## 实物与来源

| 项目 | 文件 | SHA-256 |
| --- | --- | --- |
| 原 NPC 刀 | `ArtSource/dao/dao_study.glb` | `0855a39e9851222a8976f36b2722fdde8d1f2e42cb2e813cf4057dc1257ef616` |
| NPC 候选 | `dao_refined.glb` | `4834a555d70f80151bbe19358c0a94c11e1c3f76ab2e501bf6e70c2860bcf452` |
| 玩家候选 | `dao_grip_refined.glb` | `a09ba1f7f857d099effe6dd44c0970cbf9cf030fb4397b50007502e3e197b637` |
| 可编辑源 | `dao_refined.blend` | `1573ea1df19bc92be8e3eb528058047b804a97e74cdfb94bdc3f9d667bf3d92b` |

[geometry_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/geometry_manifest.json)给出每部件旧／新面数、局部表面采样差、原坐标与候选边界。NPC 约 2.889 MB、玩家约 2.891 MB，13 个部件，3,722→8,702 三角形，8 个原名材质，18 张嵌入式 1024² 图像。

三角色使用本轮开始时正式模型的私有快照。base 源 SHA `53b80e71fbc986fc6021ac910a57fe11ba2d60d521ee371796ea1fb8b2d00641`，indigo 源 `7c79d70cbe6bea4eae58759e1faab04f57609a6851b532a24c98a54e90d2b1c6`，veteran 源 `03e02d53470d41f94355b27e765e86579a02879e2ad30d40c1444bc764ec50a7`。三者均含原八段动作。完整输出 SHA、挂点、部件 primitive 映射与矩阵见 [actor_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/actor_manifest.json)。

本轮收口时，Root 已将正式库升级为十段动作并替换 `slash` 为三方向攻击。以上八段动作快照作为历史制作证据保留，新库适配在 `ArtSource/refinement/weapon/current-bank/` 独立进行。正式组合需使用新库的身体和曲线。

## 实际制作

刀身由原九个轴向站位细化为 66 个站位、每环 21 点。原独立窄条改为连续实体凹槽，槽宽随截面约 5–7 mm，往刀尖渐收，槽底和主刃有实际法线转折。原外刃九站位轮廓与刀根／刀尖语义作为固定边界。刀身 86→2,252 面、刀槽 10→520 面。尖端初版的退化小面已通过端盖扇形拓扑及站位去重修复。

护手增加多级铸造过渡和压边，主体 316→1,404 面、外缘 252→764 面。端帽增加约 1.4 mm 凹面，316→1,020 面。旧磨痕面随新刀面重贴。局部采样差最大约为刀身 0.612 mm、护手 0.854 mm、压边 1.022 mm、端帽 1.4 mm。刀槽组件的 61.512 mm 数值来自原窄条长度较短及新槽底拆分映射，整体刀长需以锚点和外刃核对。

[surface_manifest.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/surfaces/surface_manifest.json)记录实际 UV、种子、纹理角色、尺寸和 SHA。共生成 26 张图，其中 8 张独立 roughness 为审计图，实际 GLB 绑定 18 张颜色、组合 MR 及缠柄／皮革 normal 图。内容包括纵向打磨、稀疏交叉磨痕、近护手暗氧化、黄铜层次、柄绳织纹与皮革压痕。部分磨损按部件和 UV 设计，尚未烘焙实际指面接触或曲率。

颜色与 MR 使用绝对值贴图，导出因子均为 1。MR 为 R=255、G=roughness、B=metallic。法线使用 glTF/OpenGL +Y。每个受光 primitive 具 NORMAL，贴图对应有效 UV。候选无 TANGENT，按 glTF 规范由客户端从位置、法线和 UV 生成 MikkTSpace 切线，PICO 实际生成及法线显示仍待验收。[glTF 2.0 规范](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)

## 三角色装配与接触

私有装配复用原 `R_Hand → HandGrip_R → Weapon_Root` 关系，分别使用三人的挂点矩阵。身体 primitive、skin、rest、IBM、权重和八段动作的保真检查通过。15 个新刀 primitive 与 canonical 刀按各自 bake 矩阵吻合，独立最大 POSITION 差约 0.000101 mm。原柄核、缠绳、护箍和柄环的接触表面位置差为 0，重导的 cord NORMAL 最大差约 0.000615，已按位置／UV 及有向三角映射复核。

[contact_audit.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/contact_audit.json)覆盖每角色 13 个离散姿态、前后和左右手的实际三角面。右手握柄指标沿原结果，源中指柄相交仍存在。2.117 秒三角色左手均无交叉，距刀约 52.84／57.41／55.50 mm。

早段 slash 有原生左手穿刀，当前候选还增加了部分受影响手面，故 `contact_clearance_accepted=false`。

| 角色及时间 | 相交手面 | 受影响手面面积 | 新增 body face ID |
| --- | --- | --- | --- |
| base 1.3167 s | 17→19 | 1019.314→1113.313 mm² | 58792、58823 |
| veteran 1.367 s | 30→32 | 3303.844→3489.241 mm² | 19607、19789 |
| veteran 1.500 s | 43→45 | 3460.628→3582.143 mm² | 15568、15569 |

面积为完整受影响手三角面之和。它不能表示实际交叠面积或穿透深度。仅有交叉配对数增加的姿态受新刀细分影响，已另看面集合和面积。新增面与具体姿态必须继续处理，当前结构 PASS 不构成接触放行。

## 前后图与验证

固定 900²、Cycles 24 samples、AgX、相同源姿态和机位。正常距离使用约 2.2 m、28 mm 透视。图像、机位、输入与板图哈希见 [previews 目录](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews)。最终共 25 张成对板，独立刀具 5 张、玩家实际 Grip 帧 2 张、三角色正／斜与双持刀近景 12 张、三个新增接触风险姿态的左手双面 6 张。原后方握柄机位穿入躯干的问题已改为右侧外部机位并重渲，文件名仍为 `grip_back`。

- [刀槽与刃脊](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_blade_oblique_before_after.png)、[2.2 m 独立刀具](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_normal_distance_before_after.png)、[护手与柄](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/dao_guard_grip_before_after.png)。
- [玩家 Grip 帧](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/player_grip_held_frame_before_after.png)、[base 正常距离](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_normal_distance_before_after.png)。角色当前正面刃面偏暗，游戏距离下的收益仍依赖姿态与正式光照组合，需 Root 在场景中评审。
- [base 斜角](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_normal_oblique_before_after.png)、[veteran 右侧握柄](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/veteran_grip_back_before_after.png)。仍有部分前景衣袖和手掌遮挡，当前只覆盖固定姿态。
- [base 1.3167 秒左手](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/base_risk_1317_left_front_before_after.png)、[veteran 1.5 秒左手](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/previews/veteran_risk_1500_left_front_before_after.png)。源与候选均可见穿刀，实图不足以消除表中新增相交手面，接触审核继续待修。

[verification.json](/Users/yupeng/projects/personal/pico-wuxia-arena/ArtSource/refinement/weapon/stage2/verification.json)中双入口与三角色结构通过。锚点、NaN、索引三类负例，以及装配的错 SHA、动画误指刀尾资源、TANGENT、normal map 缺 UV、Grip 移动、错材质六类边界输入均已运行并拒绝。三份实际 GLB 已在 Blender 导入，源身份冻结。

## 接入点与后续

玩家正式入口为 `HomeStage.kt` 的 `asset://models/dao_grip.glb`。NPC 从 `ArenaOpponents.kt` 的三个 `asset://models/opponents/*.glb` 载入，统一 producer 的 `append_dao` 负责刀具烘焙。候选组件和命名映射已交付，Root负责源身份复审、校准重签及正式组合。武器材质均保持 Steel／Brass／Grip 名称，身体白闪所用 `tripo_` 前缀仅属于身体。

下一项先修早段左手接触扩张，联合 01 的最新正劈姿态核对刀面与空手，随后继续正常场景光照下的刀刃可读性。PICO 实时加载、MikkTSpace 生成、动态高光、连续补间、Space Pro 观感与性能尚未验证。本轮费用为 0。

```sh
python3 -B ArtSource/refinement/weapon/stage2/surfaces/build_surfaces.py
BLENDER=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$BLENDER" -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/weapon/stage2/build_geometry.py -- --surface-manifest ArtSource/refinement/weapon/stage2/surfaces/surface_manifest.json
```

具体装配和验证参数以各脚本 `--help` 为准。复建会更新本目录候选身份，审核现有冻结证据时使用以上 SHA。
