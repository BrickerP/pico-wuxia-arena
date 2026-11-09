# 酒馆院落与前院铺地

场景为本项目制作的可编辑酒馆入口，包括木结构、屋檐、左右门扇、石铺地、手工“酒”字牌与纸灯笼。Blender采用米制、+Z向上、X横向、-Y朝入口前方，整体约4.3m宽、3.3m高。

glTF转换为+Y向上，Blender `(X,Y,Z)` 对应glTF `(X,Z,-Y)`，入口朝+Z。当前PICO入口使用 `tavern_slice.glb`，原始模块仍为Structure_Root、Door_Left_Root、Door_Right_Root、Paving_Root及Lantern_Root。

## 前院复用

`extend_forecourt.py`从现有GLB中取Paving模块，按模块实际深度向玩家侧平移，生成 `forecourt.glb`。它复用原几何、材质、UV与贴图，补充近身交战区域的脚下铺地。运行文件同时放入 `app/src/main/assets/models/forecourt.glb`，由HomeStage与酒馆同基点加载。

在仓库根目录通过Blender Python生成生产资产。

```bash
BLENDER=/path/to/Blender
"$BLENDER" --background --python ArtSource/tavern/extend_forecourt.py
```

`build_tavern.py`可重建酒馆及其离线预览。离线预览只作为资产制作参考，本轮没有生成新的PICO设备验收画面。门扇动作仍非本轮交战链路的一部分。

## 纹理来源

`textures/`中的六张1K JPEG来自Poly Haven，来源采用其[CC0许可](https://polyhaven.com/license)，原文件保留用于重建。

- [Fine Grained Wood](https://polyhaven.com/a/fine_grained_wood)，Rob Tuytel，颜色、粗糙度及OpenGL法线，用于木结构。
- [Granite Tile](https://polyhaven.com/a/granite_tile)，Charlotte Baglioni，颜色、粗糙度及OpenGL法线，用于石材。
- `tavern_wood_wet_rough.png`、`tavern_stone_wet_rough.png`由上述粗糙度图派生。灰泥与灯笼颜色图为本项目原始生成资源。

门套和层叠屋檐的结构参考来自[UNESCO西递宏村说明](https://whc.unesco.org/en/list/1002/)与[黄山市徽派建筑介绍](https://www.huangshan.gov.cn/zjhs/rwhz/hpjz/8294054.html)，项目未包含来源照片。

## 当前交付边界

本轮复用前院铺地已生成并进入场景代码，主控已完成整体编译。按用户要求没有执行本轮自测、铺地检查脚本或设备验收。实际拼接、脚下覆盖、近景材质、光照、碰撞与终端性能继续按主控验收清单核对。
