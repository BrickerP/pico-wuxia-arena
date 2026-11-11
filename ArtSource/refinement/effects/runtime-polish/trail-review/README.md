# 真实刀路离线网格对照

此处只证明生产代码生成的几何与顶点透明度差异。它不是 PICO SDK 截图，也不是手柄实录或 VR 观感验收。

`ExportTrail.kt` 实际执行 `DesktopCombatInput.LEFT_SLASH → TrackingState → PlayerCombatResolver`，以 90Hz 采样，保留解析器的 bladeBase／bladeTip／tipSpeed／atRest／motionGeneration。两份几何消费相同 fixture：`562449a` 原始 Geometry 与当前候选 Geometry。没有另画弧线。

`meshes.json` 包含49帧输入结果和逐帧两份真实 triangle mesh；比较帧固定为第24帧（266.7ms），当时刀尖速度约6.56m/s。基准与候选尾迹的位置、索引、顶点Alpha逐项相同；候选新增12ms亮芯，颜色与全局Alpha采用对应 PlayerBladeTrail 值。

- `trail_compare_0.8m.png`
- `trail_compare_1.5m.png`
- `trail_compare_3.0m.png`

每张左右两栏使用相同相机、90°水平视角和同一背景，无单独放大。距离为相机到完整尾迹包围盒中心，方向沿真实head到该中心的方向。10cm标尺位于同一目标平面。软件按实际三角索引顺序做透视校正Alpha混合，2倍采样后缩小。

目视：0.8m和1.5m候选可分辨暖白短亮芯与冷白尾迹；3m整体角尺寸较小，亮芯仍是局部亮点，不能据此确认实际场景的远距辨识度。没有加入Bloom、自发光光晕、曝光、遮挡物或SDK色调映射，RGB直接映射显示值。候选同一mesh内透明三角排序与实机场景遮挡仍由Root确认。

复建（工程根目录）：

```sh
python3 ArtSource/refinement/effects/runtime-polish/trail-review/build_review.py
```

此脚本仅编译明确源码子集到本目录临时目录，完成后清理classes，不调用共享Gradle、Blender或设备。它依赖本机已安装JDK、Kotlin缓存、Android35公有android.jar及Pillow／NumPy。来源SHA、相机与输入／输出哈希见 `review.json`；编译与执行结果见 `compile.log`／`export.log`。
