# Slash 非持刀侧局部修正候选

本阶段以已审核的上一阶段 `grip/candidates/indigo.glb` 和 `veteran.glb` 固定哈希为输入，输出仅在本子目录。上阶段候选、校准文件、公共 producer、library 和 app 保持各自发布所有权。

## 最终参数

| 角色 | 唯一修改轨道 | 局部旋转 | 起点／全幅起点／全幅终点／终点 |
| --- | --- | --- | --- |
| 青衫 | slash / L_Hand / rotation | X +8° | 1.80 / 2.00 / 3.40 / 3.60 秒 |
| 玄甲 V2 | slash / L_Forearm / rotation | Z +4° | 1.50 / 1.55 / 1.72 / 1.95 秒 |

校正由原生 `q(t)` 右乘余弦包络控制的轴角四元数。保留全部原时间点，在局部窗口内增加 60 Hz 与四分之一抬升点关键帧。源 slash 的 0.033333–6.6 秒范围保留，其他七个动作完全相同。原生运动继续播放，窗外校正为零。最终 GLB 使用 LINEAR 四元数插值，是 C0 连续的采样近似，导出边界单侧斜率记录于审计，解析余弦函数的零端点导数不作为导出轨道的 C1 保证。

玄甲最初的 +12° 左手腕方案在 1.3–1.5 秒增加交叉，已被退回。其报告保留为 `rejected_wrist_audit.json`，最终仅采用上述前臂 V2，其他时刻沿原曲线。原始 rest、骨长、网格、skin、权重、逆绑定和右手／刀具轨道均保留。玄甲允许的左腕世界位置变化峰值为 15.833 mm。

## 验收结果

独立审计覆盖 1–4 秒的 120 Hz、四分之一抬升点和接缝 ±1 ms。青衫 370 个姿态、玄甲 373 个姿态均未增加确认交叉。完整区间仍有原生交叉，见 `audit.json`。

| 指定 1.55–3.4 秒范围 | 青衫 | 玄甲 V2 |
| --- | --- | --- |
| 采样数 | 229 | 230 |
| 累计确认非共面三角形交叉对 | 1100→0 | 44→0 |
| 采样左手顶点到实际刀面最小无符号距离 | 2.428 mm | 4.589 mm |
| 距刀面 3 mm 内顶点累计数 | 748→19 | 38→0 |

以上是离散表面检查，顶点距离不等于两完整表面的严格最短距离。完整动作、连续时间和共面交叠继续存在验证边界。青衫约 1.325–1.408 秒、玄甲约 1.142–1.533 秒及 3.65–4 秒仍有原生交叉，本阶段不宣称整段动作完全清除。

## 复建与主控接入

从唯一主仓库运行。

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/offhand/build_offhand.py
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/offhand/test_offhand.py
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender -b --factory-startup --python-exit-code 1 --python ArtSource/refinement/grip/offhand/verify_offhand.py
```

`test_offhand.py` 以当前校准记录的固定候选 SHA 作内存确定性回放，已执行 2 个角色回放、2 组包络检查、6 个边界拒绝，覆盖右手范围、源时间范围、无效起止和源哈希漂移。`verify_offhand.py` 独立核对实际输出、旋转公式和密集表面检查。

主控已在唯一producer的指姿阶段之后接入本包络，并实际生成发布。24份动作语义与审核candidate逐项相等，生产身份见production_receipt.json。正式发布预期保留 22 个完整动作，另外两个 slash 仅修改表中一个非持刀侧旋转轨道，右手与刀具保持原语义。源文件 SHA 与最终候选 SHA 均在 `calibration.json`，当前 library 已更新时仍使用这里固定的上一阶段候选作审计基线。主控统一做正式发布、最终哈希与运行画面验收。

## 制作近景

`previews/` 包含 37 张 before、37 张 after、17 张近景／左臂对比、两张身体姿态板与两个十帧 slash GIF，覆盖 1.25–3.55 秒及关键目标时刻。V2 另增加 1.516667／1.533333 秒的左臂过渡图。相机、源时间和候选哈希记录在 `previews/render_manifest.json`，玄甲均已按最终 V2 重渲。

本轮费用为 0。模型护手自然度和设备画面交主控审核，阶段结束。
