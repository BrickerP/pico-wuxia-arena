# 单窗庭院：重建与核验

当前正式app只加载一个完整庭院。原8b庭院与2fb窗口模块是冻结输入，9b整景已进入开发整合；不加载叠加场景。

在工程根执行（Python需要numpy、Pillow）：

```bash
python3 ArtSource/refinement/environment-hero/single-window-integration-2026-11-12/build_courtyard.py
```

预期输出 `courtyard_one_window.glb` 的SHA256为 `9b259812a46f07e95dab6b4e4c414521c05118366ed09fca9632bebc51c27dd5`。构建仅需要仓库内的冻结输入及直接Python依赖，不需要网络、Blender或中间角色PNG。

构建输入为已跟踪的stage2/courtyard_materials_stage2.glb（8b）、method-study-2026-11-12/window_infill_candidate.glb（2fb）；直接复用verify_environment.py与stage2/create_candidate.py。原始BIN前缀、非目标节点、地面接收器与战斗空间保持不变，只替换一处旧窗并裁掉洞口旧墙皮。

完整保存性检查另有角色核验前置：先按ArtSource/tripo-warrior/motion_library.json运行唯一正式角色producer，得到library/base_prepared_png.glb及正式KTX2组。prepared PNG为可重建中间产物，不入仓；缺失时不能把验证脚本失败误报为场景构建失败。随后执行：

```bash
python3 ArtSource/refinement/environment-hero/single-window-integration-2026-11-12/verify_courtyard.py
```

核验脚本输出review/verification.json，并比较当前producer PNG与正式角色的geometry/skin/animation，不锁已过时的角色颜色版本。2fb模块已内嵌图像；如需作者级再制作，method-study-2026-11-12/build_window_sample.py和materials/make_materials.py、六张wood PNG及其manifest提供来源链。跨工具版本的作者级再生成未承诺逐字节相同；精确整景构建使用冻结2fb模块。

格式检查曾得到0错误、4条自动生成切线警告，均来自窗口模块未显式提供TANGENT的normal材质primitive。Root已将9b装入1b905包，在Full Stage实际显示；首敌加载阶段没有NO_MEMORY或新增切线告警。相关原生图和包身份见ArtSource/refinement/presentation/clean-coat-one-window-2026-11-12.*。这不代表Space Pro性能/舒适度或完整三轮通过，预算与硬件门未过前不复制第二窗。
