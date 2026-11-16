# Right v2 掌背／腕口新曲面首件：技术通过，视觉未通过

**阶段结束，等待 Root review。不建议替换正式 Right，不派生 Left。**

本件从正式 Right v2 `3a1be1dd…` 重新制作，没有把 687／9f 作为源。新 GLB `right_hand_patch.glb` 为 `3000b6be1abdfb9b003f8d67048fae39a63a3400eb48d4b37adf4b3e46a5d01c`，总计 5,018 三角（主 primitive 4,763，原收口 255）；2,867 顶点。36 个源控制点更新，80 个必要的 normal seam 拆点。

## 实际制作

掌背采用原手开握解剖坐标中的 robust 二次曲面重建，腕口第一带做局部周向轮廓重建。一轮共形支撑分割只提供面流密度，实际位置来自源 barycentric 点与新拟合曲面；没有沿用 687 的细分变形。法线约束联合 default／open／mid／closed 的实际 inverse-LBS 变换，合法几何存在共享角冲突时才复制该角的全部位置／UV／骨权重属性并拆 normal。没有翻整面、关剔除或改动画。

首件 `b1bade29…` 的 mid 子面 1244（源 1226）变得过瘦并跨过原面半球，故拒绝。唯一定位修正把该腕口薄扇区及一环完整保留为源几何、不在其中插值或移动；验证仍覆盖这些面，没有新增豁免。首件 GLB、源码、失败诊断在 `attempt1/`。首轮渲染发现 studio 默认 ORTHO，已标为无效取景；最终图明确使用 PERSP，并在更新依赖图后记录实际相机矩阵。

## 可以看的实际图

相同源 ROI、closed grip@1、0.3m、相同镜头／四盏物理灯／原点与骨架：

- 掌背原材质：[before](renders/dorsal_original_before.png) · [after](renders/dorsal_original_after.png)
- 掌背中性材质：[before](renders/dorsal_neutral_before.png) · [after](renders/dorsal_neutral_after.png)
- 腕口原材质：[before](renders/cuff_original_before.png) · [after](renders/cuff_original_after.png)
- 腕口中性材质：[before](renders/cuff_neutral_before.png) · [after](renders/cuff_neutral_after.png)

PNG companion 从候选实际 KTX 像素重新派生，候选拥有自己的全部非图像数据。中性材质只用于分辨几何／法线问题，没有写入候选。不是 PICO 图像或 SDK TBN 读回。

## 技术验证

`verify_patch.py` 对真实源与候选做完整四姿态检查；12 项 happy／坏例测试通过。候选无新增相对源几何反转、normal/winding 反向或蒙皮缝；保护域实际蒙皮误差为 0。骨架／节点／REST／IBM／动画／Grip 和三张 1536² KTX 保持。self 为 default/open/mid/closed `109/0/0/109`，映射回源面后新增交叉为 0；真实 Dao 没有新增表面交叉或 ROI 入内／加深。

继承的 posed 坏法线角数为 `34/13/19/34`，逐姿态相同，不把 bind-space 的 13 个当所有姿态结果。验证只覆盖有限姿态和现有非共面求交判据，不能证明连续时间、SDK 切线或原生观感。完整结果在 `verification.json`。

## 为什么视觉未通过

主长斜沟仍存在，腕口收益小，中性图还可见局部硬平面，不能把绿色技术检查当精致度通过。原材质与中性材质都保留这条沟，说明它并非只由 normal 贴图产生。

本轮补做了从真实源相机像素到源表面的射线定位：沟的两侧主要命中 source face1101 `[631,106,546]` 和1075 `[106,37,364]`，解剖 forward 约0.088–0.090m；实际 MCP 骨在0.101–0.116m。这里是掌背混权皮面，平均 R_Hand 仍为约0.59/0.64，但 Mid/Index spill 约0.4。沿用的 digit-spill 0.18 保护上限过保守，遗漏了主缺陷区域。射线与权重定位不单独证明几何、原法线和混权中哪一项是主要成因。

下一轮应按图中缺陷与 MCP 实际位置定义掌背 ROI，检查该处 finger spill 与 authored normal 连续性，再做局部皮面／权重联合修复；不能继续仅在腕口加面，也不能单凭骨权重比例把掌背当成手指保护。本件不自行开启第二个几何返修。

## 复建

在本仓库根目录运行：

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/build_patch.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/verify_patch.py
python3 -B -m unittest discover -s ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch -p test_verify_patch.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/make_companion_patch.py
python3 ArtSource/refinement/hand-poses/run_blender.py --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/render_patch.py
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/diagnose_visual_roi.py
```

Root 独占正式资源、左右同步派生、APK、设备和 Git。本路均未改。
