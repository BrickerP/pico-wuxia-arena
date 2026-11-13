# 中央入口构造替换

本目录只替换正式64da庭院的中央门组、门框、门槛、两柱础与两处檐下支承。完整交付为 `courtyard_native_entrance.glb`；`entrance_module.glb` 是制作中间件，不能作为第二运行场景。材质、50图原始payload、九窗、地面receiver、锚点、Stage原点与既有节点变换保持。旧门及被替代的局部构件从绘制索引中移除；不是把新物件盖在旧盒前。

在仓库根 `/Users/yupeng/projects/personal/pico-wuxia-arena` 运行：

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-fight-entrance/build_entrance_module.py
python3 ArtSource/refinement/environment-hero/native-fight-entrance/build_candidate.py
python3 ArtSource/refinement/environment-hero/native-fight-entrance/verify_entrance.py
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/native-fight-entrance/courtyard_native_entrance.glb ArtSource/refinement/environment-hero/native-fight-entrance/review/gltf-validator.json
```

依赖复用仓库已有 NumPy、Pillow、Blender4.5.15和已锁定的 gltf-validator。输入为 `../facade-polish/courtyard_facade_polish.glb`（SHA256 `64da27985ac4692c3610ef5c6066fa6f9a7775654fe3fd394966c5021cf51605`）。脚本复用 `../method-study-2026-11-12/build_window_sample.py` 的实体建模/米制UV工具、`../single-window-integration-2026-11-12/build_courtyard.py` 的GLB写入与资源合并，以及既有几何读取和统计工具；不会执行它们的旧场景制作入口。

`entrance_editable.blend` 保留命名分件：左右框扇、五块下芯板、实体压条/半搭接窗棂、薄纸芯、环拉手、带止口的门套、收分柱础及真实插口、实心斜撑/承托。所有新增木件按0.8m长纹、0.25m端纹进行物理UV映射。门闭合姿态保持，纸材质复用原件，不据离线渲染声称纸的真实透光能力。

完整合并脚本按已审计connected-components删除旧件，仅对指定低横梁、长台基和两主柱底端做局部裁剪。不会把共享墙或石构primitive整片按包围盒删除；两处朝向入口的台基裁口按原4mm倒角截面封闭，并独立检查覆盖面积及朝向。入口的宽台基中央段和埋没踏步移除后，接近区域回到既有StageY0，只有窄门槛升至最高65mm；NPC偏移仍由原生端维持+.028，本目录不改角色。

离线对照复建（串行执行，每次最多一个Blender、2线程）：

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-fight-entrance/render_entrance.py -- before
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-fight-entrance/render_entrance.py -- after
```

整景相机使用Stage `(0,1.65,0)`；对手是当前正式base角色的PNG等价版本，固定idle@0、Stage `(0,.028,-2.4)`、scale1。相机/光照/曝光与角色源身份见 `review/render_manifest.json`。这些是实际GLB重导入的离线对照，不是PICO Emulator截图，也不证明Space Pro运行性能。

`audit.json` 与 `review/verification.json` 记录实际完整GLB预算。节点展开三角与唯一mesh三角分开统计；唯一属性VB按被活跃mesh引用的属性bufferView并集计，不等于设备VRAM；primitive×node仅为提交估算。旧源BIN中的未引用历史数据未作为活跃几何统计，本件不重开静态合批或全资源重打包。

`optional_blocker_bounds.json` 只是Stage坐标下的几何参考；未加入任何原生碰撞、navmesh或门交互。Root负责正式资源替换、APK构建、原生截图与通行/性能验证。门仍是关闭的视觉门，模型构造升级不构成“可走通”的证明。
