# Wet visibility v3 · 正常战斗视距分层候选

本目录提供单一分层源资产，由Root唯一制作入口调用 `build_wet_v3.build(output_dir)`。制作模块无独立main，复用项目Effect／Layer／GLB写入函数。静态GLB由08按实际接触、真实切向和呈现年龄逐节点驱动。

## 实物与分层预算

`wet_cloth_contact.glb` 为48,128字节、596三角、23个独立mesh、3种普通PBR材质，SHA-256为 `a96623710d43a5e952a559153ce7cf1d0e75ca68636d5e9e98ff492040f15077`。

| 层 | 数量 | 身体尺寸 | 寿命 | priority |
| --- | ---: | --- | --- | ---: |
| hero近大滴 | 2 | 最大外包8.5／9mm，截面7.31／7.74mm | 180／220ms | 100 |
| main主滴 | 4 | 最大外包5.5–7mm | 220–270ms | 85 |
| stretched拉伸滴 | 4 | 长10–18mm、截面3.6–4.5mm | 240–300ms | 80 |
| fine细滴 | 8 | 最大外包3–4.5mm | 250–360ms | 45 |
| trailing纤维 | 5 | 长8–15mm、宽1.2–2.2mm | 290–400ms | 55 |

总数为18滴水加5条纤维。近大滴速度较快、先散；细滴补充扇形尾部，纤维稍后消失。尺寸均为源GLB真实米制，拉伸滴的长度与截面分别声明。

水滴主层baseColor为(0.74,0.86,0.92,0.88)、roughness为0.14；细滴为(0.57,0.70,0.78,0.72)、roughness为0.22。纤维为低饱和冷灰、roughness为0.82、Alpha为0.86。三者metallic和emissive均为0，沿用普通alpha-blended PBR，材质不带折射／transmission扩展。水滴每个32三角并给平滑外法线，纤维每个4三角。

## motion与08契约

`motion.json` 的schema为 `contact-particle-motion/v2`。23个mesh对应23项particles，cores与accents为空，所有mesh必须恰好覆盖。Root统一contract定义消费者接受的字段。未知schema或未驱动可见层需要明确拒发。

保留node／type／initial_position_local_m／initial_velocity_local_mps／lifetime_s／opacity_keys，新增shape、tier、priority与orientation_axis_local。round滴最长轴为局部Y，stretched滴及纤维为局部X；拉伸滴直接沿切向形成本体，08也可按真实速度定向。round滴保持源TBN即可。Root提供实际切向T和法线N，B=N×T，重力始终在Stage负Y。法线偏移8mm只在锚点加一次。

只在确认湿衣料接触时选择此层。裸头与SOFT分类本身不能证明湿衣。优先级只用于08的粒子预算，事件致命／弹反的整次优先级仍由Root管理。过期采样为空，不把历史接触重新开始。

## 正常视距与验证

`verify_wet_v3.py`实际读取GLB，检查全部23层精确覆盖、尺寸、法线／闭合滴面朝向、596三角、寿命和schema。三项正常／边界用例已通过，覆盖完整与缺失／重复mesh以及出生／过期边界。

1280像素、60°水平视场、画面中心的几何投影预算如下，数值仅表示物体占像素大小。

| 尺寸 | 1.5m | 2.5m |
| --- | ---: | ---: |
| 9mm hero滴 | 6.65px | 3.99px |
| 7mm主滴 | 5.17px | 3.10px |
| 3mm细滴 | 2.22px | 1.33px |
| 18mm拉伸长度 | 13.30px | 7.98px |
| 4.5mm拉伸截面 | 3.33px | 2.00px |

旧微点源主要落在约1像素级，本候选把有限预算分配给少量主滴和短拉伸形，再用细滴补层次。实际可读性依光照、Alpha排序、背景与正常视距实图判定，不能仅凭该几何预算宣布通过。统一renderer由metal／contact_effect_assets负责，离线材质的可变opacity使用已修正的每对象隔离规则。SDK／头显验收由Root及08执行。

本阶段仅写本目录，原wet源、正式app与共享SDK源码均保持只读。资产已交Root与统一renderer，阶段结束。
