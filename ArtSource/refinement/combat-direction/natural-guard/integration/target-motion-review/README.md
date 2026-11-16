# 目标待机微动数学验收

在仓库根目录使用已有 Python 3.9+、NumPy 环境运行：

```sh
python3 ArtSource/refinement/combat-direction/natural-guard/integration/target-motion-review/measure_blade_drift.py
```

脚本按自身位置定位仓库，不依赖当前工作目录、Blender、设备或 `artifacts/`。运行会重新计算并覆盖本目录的 `measurement.json`，不会改动模型、manifest、profile、Kotlin 或其它资源。

报告绑定实际执行脚本的 SHA，以及当前源 RAW／rig、正式 bank、三个模型和三个 profile 的 SHA。它是本目录独立运行的新工程产物；旧 ignored 诊断未作为输入，也未把旧报告复制为新验收。

manifest 通过现有 `production_binding` 投影校验，并核对与正式 bank 一致；该投影明确排除 `production_review`。因此 Root 可以让批准文件引用本报告，不会形成“批准文件 → 报告 → manifest → 批准文件”的哈希循环。其余输入文件均记录真实文件 SHA 与字节数。

检查覆盖 181 个 RAW 键和 361 个 profile 时点：

- 独立 FK 预测、实际腕／刀段位移、Hand-local mount、骨长和刀长。
- 五锚 exact 闭环，以及 Root 接受的 2 mm 目标自然微动制作预算；原 root／foot `1e-6` 门不变。
- 三个目标各运行两个内存负例：时变握点局部平移、前臂骨段 offset 伸长，共六个拒绝案例；源文件不被篡改。

2 mm 约为 72 cm 刀长的 0.2775%，低于约 4.5–5 mm 的头部呼吸幅度。该预算允许异体型、保骨长 FK 的自然微动，不是浮点误差容差。报告保留推导、完整采样和两种方案的取舍；Root 选择保留现 FK。

计算使用 float64，profile 数值单独作为已发布数据记录。不同平台的数值库可能产生末位差异，报告同时记录 Python／NumPy 版本；应复核输入身份、预算、不变量和六个拒绝案例。此数学验收不证明静态握持人体工学、网格净空或原生设备观感。
