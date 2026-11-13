# 九窗静态合批原生候选

## 锁定验证器依赖

新checkout在仓库根先执行：

```sh
npm ci --prefix ArtSource/refinement/pbr-compression/tooling/gltf-validator
```

使用随仓库package-lock锁定的`gltf-validator@2.0.0-dev.3.10`；不提交node_modules。本候选仍需NumPy、Pillow、Blender4.5.15；拼图字体使用macOS现有Songti.ttc。该环境准备不代表设备性能通过。

输入为冻结64da，输出仅在static-batch。无需运行场景producer，不操作app或设备。

```bash
python3 ArtSource/refinement/environment-hero/facade-polish/static-batch/build_static_batch.py
python3 ArtSource/refinement/environment-hero/facade-polish/static-batch/verify_static_batch.py
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/facade-polish/static-batch/courtyard_static_batch.glb ArtSource/refinement/environment-hero/facade-polish/static-batch/review/gltf-validator.json
```

仅如需重建本次唯一一组图，再执行一次：

```bash
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/facade-polish/static-batch/render_equivalence.py
python3 ArtSource/refinement/environment-hero/facade-polish/static-batch/make_board.py
```

按真实material及原attribute layout分7组。地层木/端纹/纸无T，上层已有T，保持这种差异；铁31布局一致合1组。没有补切线、删切线、重算法线或改UV，唯一位置误差为world烘焙到float32的舍入。32材质、texture/sampler结构及50张图片顺序、mime、原始payload完全保留。四个legacy图槽也属于这次明确保留合同，不声称纹理预载降低。

节点41–49保留名称、父链和transform，但不再引用mesh。新identity批次位于同一root。完整重建活跃mesh→accessor→view及全部image保留根；逐索引压紧所有活跃几何，不保留旧BIN或被替代mesh32/33。验证确认无unused mesh/accessor/view，BIN只有存活数据与最多3字节对齐。

109→80是primitive×node估算，不是实际SDK drawcall。唯一属性VB增加5.547MB、文件增加5.355MB；实例展开本来就会增加几何存储。它是提交成本A/B备选，不是已证内存优化或LMK解决方案。更大的整面batch也使逐窗culling变粗，真实帧时、PSS和启动行为仍由Root在原生APK中核对。

Root采用时替换唯一courtyard资源、原点identity；不把本文件叠加到64da。当前正式64da未由06改动。设备因watermark/swap触发LMK的原因未归到本候选或场景，模拟器重启与场景A/B属于Root分开的操作。
