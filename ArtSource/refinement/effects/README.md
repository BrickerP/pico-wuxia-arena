# 接触效果生产资产

四个静态GLB使用同一网格层合同。根节点的直接子节点为 `core`、`debris`、`scar`，每层一个mesh、一个material、一个primitive。坐标为米制XY接触面，+Z朝接触表面外侧。初始缩放均为1，资源没有animations、骨架、纹理或扩展依赖。

| 资源 | 层次与材质 | 建议保持时间 |
| --- | --- | --- |
| soft_contact.glb | 暖色局部冲击核心，棕灰布尘和少量纤维，暗暖刀痕与细亮边 | 0.62秒 |
| metal_contact.glb | 白热核心，金色长短火星与颗粒，短暂冷硬刮痕 | 0.44秒 |
| force_contact.glb | 暖灰破碎冲击环、碎屑和较宽刀痕 | 0.72秒 |
| ground_dust.glb | 低亮土灰核心、碎尘及短地面擦痕 | 0.65秒 |

材质沿用现有glTF PBR、emissiveFactor、顶点颜色与alphaMode BLEND，双面显示。颜色与自发光因子均在0到1范围，亮核心与低亮尘屑分开。源资源与生产资源内容相同，尺寸、三角数、层级与SHA-256记录于 `contact_effects_manifest.json`。

Kotlin持有预加载实例池，通过Entity变换和Opacity驱动包络。接触位置与旋转由CombatImpact的Stage点和法线决定。资源以接触点为原点，细节朝+Z外突约2到75毫米，实例整体再沿法线偏移避免贴面闪烁。生成器不含运行时动画通路。

## 制作与离线核对

在项目根目录执行以下命令。当前机器Blender安装位于用户Applications目录。

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --python ArtSource/refinement/effects/build_contact_effects.py
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --python ArtSource/refinement/effects/render_contact_effects.py
```

`build_contact_effects.py` 复用旧效果生成器的网格编码与项目GLB发布函数。旧资源保留在ArtSource/effects作为对比源，旧动画GLB已从运行目录移除。现有命中特效最终入口使用本目录四个静态资源。

`contact_materials_comparison.png` 和 `contact_materials_preview.mp4` 直接导入已生成GLB，以同一米制比例、相同哑光背景、相同灯光渲染。旧普通命中的刃光显示其资源理论峰值，新的三类接触效果放在同一接触点。短片逐帧复现运行代码提供的层缩放与透明包络，Blender导入轴转换已按glTF +Y映射到Blender +Z处理。

短片为30fps、25帧、0.833秒。额外两帧 `contact_materials_267ms.png`、`contact_materials_467ms.png` 分别对应第8和14帧，用于检查冲击核心退去后的尘屑与刀痕保持。

图与短片属于离线素材观感。PICO的实际透明混合、近距离视野、接触点朝向与同帧多接触需要主控在应用中核对。
