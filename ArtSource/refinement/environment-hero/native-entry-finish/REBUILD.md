# 主门实木入口首件

本目录只交现竞技场的完整私有场景。源为正式 c7 KTX 的 d935 PNG 对照；门扇、门框、纸窗、铜件、原石座、台阶、灯笼、碰撞地面、场地尺寸、所有锚点以及材质/图全部保留。只替换主门前两根立柱和两组三件式斜撑，新增厚实曲形牛腿、承托、榫槽、方向木纹和实际细小磨损。不是新场景、孤立模块或概念网页。

## 原始输入与建模

- 完整 PNG：`ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_png.glb`，SHA `d935d8185dff6750838bc1d5d98c0b1f07bdce4b0a25249e42957bc501fbe06d`。
- 固定 KTX 源：同一 `composition/` 目录中的 `courtyard_lantern_surface_ktx.glb`，SHA `c7f2e2b2833cdd84fbc73918fdcd2f9036dee582a46c29d8db67df806e77fc78`。该文件已在仓库；生产默认读取此固定源，不读取未来会被替换的 `app/src/main/assets/models/courtyard_hero.glb`。
- 仅复用既有 material29方向木纹及material30端纹，图/纹理不增加、不重编码；KTX版直接保留全部原 KHR_texture_basisu payload。新物件的贴图/法线框架复用原管线。

两根木柱底脚 .230×.290m，仍接入原 .242×.302m 石座开口；柱身保持原 .230m 宽和4.615m高，深度随高度在 .290–.360m 变化。真实穿枋槽按原2.85/3.15/4.80m横枋体积开出；牛腿本体厚 .190m，背榫 .110×.194×.220m 接入每边约1mm间隙的柱槽，顶承托接原廊梁Y=3.02m。侧面为实际凹槽，不是贴图；柱边有两处有限磨损。十个新增实木部件均检查闭合、有正体积。

源主柱精确拆76三角，旧括臂方向木纹550及端纹20三角；原索引顺序的其余部分完整保留。只改 mesh22/primitive0 与 mesh36/primitive0、1 的索引，保所有旧顶点流；原BIN有效字节作为候选的完整前缀保留，不做全场Blender往返。

## 唯一复建命令

在 `/Users/yupeng/projects/personal/pico-wuxia-arena`：

```bash
python3 ArtSource/refinement/hand-poses/run_blender.py --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-entry-finish/build_entry.py
python3 ArtSource/refinement/environment-hero/native-entry-finish/verify_entry.py
node ArtSource/refinement/environment-hero/native-entry-finish/validate_entry.mjs
python3 ArtSource/refinement/environment-hero/native-entry-finish/finalize_entry.py
```

需要 Blender 4.5.15（共享锁包装器已固定路径）、系统 Python 的现有 NumPy/Pillow、现有 glTF validator；没有安装新依赖。一个 Blender 进程先做部件、再调用只读原场景的组合脚本，最后导入完整候选取图并保存可编辑完整 `.blend`。首件返修时用过 `-- --after-only`，复用已固定的原before图；从头复建使用上面无参数命令产生完整两阶段。

布尔磨损与倒角交接会生成亚微米短边，在 glTF float32 中塌缩。不能因“原BMesh闭合”就跳过装包精度检查。本产线仅对新十件用10µm merge、1µm退化溶解及三角化，复核闭合/体积；导出后由既有 `create_candidate.tangents` 在最终三角形上生成显式TBN。不会更改原几何、不放宽退化门，也不依赖SDK自动生成切线来验收。

## 画面、预算与边界

`review/player_1p65_comparison.png` 为相同1.65m玩家机位前后；`joint_oblique_comparison.png` 显示厚度和梁柱承托，`foot_oblique_comparison.png` 显示原石座接合。所有图是完整PNG场景、相同继承stage2夜景灯光、相同曝光/相机的离线Cycles图；两边都排除角色/UI/手，避免混不同人物。它们不冒作原生截图或7f环境标定。

主视角变化克制，明显收益集中于局部木纹、柱的有体积转折和曲形承托；不是整场“纸壳儿”问题已经解决。Root应实际看正常/侧向图，再决定是否装包。最终几何、属性VB、索引、提交估算、32材质/50图的精确数值和SHA见 `composition.json` / `handoff.json`；≤270k只是本首件制作上限，不构成终端性能证明。

需要另验原生KTX加载、SDK TBN与材质、实际7f配光、战斗中观感及Space Pro性能/内存/舒适度。本路未改正式app/assets、原场景、公共producer、Git或设备。

## 发布与采用闭包

`production-closure.json` 列出7份最小制作源码/说明、11份已被Git跟踪的共享源/工具锁文件、两个完整交付GLB及审核收据的SHA和大小。默认输入都是仓内固定文件，不依赖 `artifacts/`、临时渲染文件、当前敌人或将来替换后的app模型。`entry_module.glb`和完整`.blend`是生成/编辑产物，不是从头复建的额外输入。现有glTF validator可用其仓内package-lock执行`npm ci --prefix ArtSource/refinement/pbr-compression/tooling/gltf-validator`恢复，无需提交node_modules；本次没有安装或更新工具。

Root采用时只替换正式 `app/src/main/assets/models/courtyard_hero.glb`：前置身份c7f2e2b2，交付身份8c44106f。先运行上面的9项保护与glTF校验，再确认目标/候选SHA，复制唯一KTX，最后由Root核实际APK装包SHA及原生画面。不要把PNG或孤立module装为正式场景。`size-anchor-proof.json`给出按实际引用三角计算的源/候选尺寸完全相同，以及全部64个原节点、12个无mesh锚点的世界变换exact；这属于离线相对保护，不冒作SDK bounds读回。正式灯/IBL、场地和地面判定入口不改。
