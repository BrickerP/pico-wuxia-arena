# Ground visibility v2 · 单次材质与Alpha候选

本阶段按Root只读实图review修正v1尘层难以辨认的问题。本目录保留同样的8个mesh、底部原点、2–2.8厘米高度及22.2／32.9厘米轨迹包络，原v1资产与FAIL图仍为只读对照。

## 精确变化

- 材质baseColorFactor由 `(0.46,0.44,0.38,0.28)` 调为低饱和湿泥色 `(0.35,0.32,0.28,1)`，roughness=1、metallic=0、alphaMode=BLEND、自发光0等其他材质字段保持。
- COLOR_0只改Alpha，`alpha2=min(alpha1×1.8,0.65)`，原0仍为0。实际v1只有中心0.70和边缘0，所以中心被cap为0.65，边缘0保持。每个asset共208个颜色顶点，16个中心Alpha变化，192个零边缘保持。RGB完全一致。
- motion的所有透明度值按原峰值等比例调整到0.85上限，关键点时间、寿命及全部非opacity字段保持。普通dodge峰值由0.55变0.85，landing由0.64变0.85。

材质Alpha与motion提升是主要浓度来源。单张card中心有效峰值由约0.108／0.125到0.5525，约为v1的5.13／4.40倍。两张cross-card的覆盖结果依视角与透明排序变化，数据不能代替实际观感。

## 资产与不可变项

| 资源 | 字节数 | SHA-256 |
| --- | ---: | --- |
| dodge_ground_polish.glb | 22332 | cfca84cc04b880031f6ba0e0e8279bd9ba1a10d54d92060e4405e0f1b12f184c |
| landing_ground_polish.glb | 22424 | f802ca73ff953432e6afb9a3951247fc236292198414e4f1aeda37d7d600218b |

`visibility_patch.json`逐项记录v1输入SHA、candidate SHA、材料前后值、颜色Alpha统计及motion每节点关键点前后值。原BIN前缀保持，只追加新的COLOR_0数据并改对应accessor引用。POSITION／NORMAL／indices及全部节点变换保持，未通过Blender重导出。

Root唯一制作入口调用 `build_visibility.build(output_dir)`。本模块无独立main，不写v1、app或共享源码。验证入口 `verify_visibility.py`实际比较两个GLB的几何流、索引、原BIN前缀、RGB／Alpha、材质字段及运动合同，两个正常／边界测试已通过。

## 视觉边界

这是唯一一版材质／Alpha修正候选。Root要求先看同相机同灯100毫秒帧，visibility-v2的独立renderer与review由contact_effect_assets所有。当前源码检查通过，实际可见性／遮挡由Root根据该帧判断；SDK透明混合与设备表现继续由Root统一验证。

## 已发现的离线基准问题

读取100ms对比图后检查renderer，发现原 `alpha_controls` 对8个mesh共用的material连续添加8个Alpha乘法节点。实际Blender导入也确认8个mesh共享同一个材质，这种共享是合法GLB数据。逐mesh不隔离可变材质时，透明度会变成多个粒子的乘积，例如0.6的8次方约0.0168，足以解释尘层被压没。

正确离线做法是先在每个对象slot复制材质，再只添加该对象一个独立opacity乘法节点。源GLB维持共享材质，SDK接线继续用实体独立Opacity。检查记录在 `material_sharing_check.json`，已同时交Root和renderer负责人。当前旧FAIL图的素材强度判断需要用修正renderer后同机位图重新核对。
