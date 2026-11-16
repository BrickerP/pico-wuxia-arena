# 正门灯笼纸罩表面首件

本件只在圆润精修模块上修正纸罩纵向折面和均匀塑料感。正式输入是当前湿石KTX庭院 `bd5d21ef…`，保持不写；Blender无法读取它的 `KHR_texture_basisu`，建模/离线预览只用已验证的PNG等价场景 `5619ce1c…`。PNG预览不代表KTX加载、原生灯光或设备效果。

唯一新增栅格为 `textures/paper_fiber_1024x512.png`：从已有灯笼baseColor image38派生，seeded中性纵向纤维和低频透光不均，因子范围0.979–1.020；不含固定灯位、反射、AI生成或外部下载。正式组合时Root在material10中把baseColorTexture和emissiveTexture绑定到此一张图，并以现有image41作为被替换payload；MR/normal保持原绑定。因此正式材质数仍32、图仍50，不要把模块中的预览材质另行追加为第33个材质。

从仓库根执行：

```sh
python3 ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/make_paper_fiber.py
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/build_surface_finish.py
python3 ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/verify_surface_finish.py
```

The module uses 48 circumferential paper segments, 17 longitudinal rings with smooth normals, 12 continuous swept bamboo ribs, four hard collar rings, caps, hanging eye/cord and tassel. The hard wood/rib edges remain faceted; only paper is smooth. Module `lantern_surface_module.glb` has identity local root; compose at the same two existing Stage translations in `module_manifest.json`.

Module is 5,500 triangles; two instances 11,000. Removing the audited old front components (4,400) gives a planned 249,958 expanded triangles, under the 250k cap. It is not a full-scene output. `render_surface_finish.py` is an in-memory preview only, removing the same old envelopes before importing the module twice. Current actor identity changed during Root's action reimport, so both views exclude it instead of mixing an old actor. The sole local camera framing correction was inherited from the preceding refined review; this surface task does not alter camera geometry, layout or lighting.

`verify_surface_finish.py` checks formal/PNG/module identity, one fiber-map provenance, 48/17 smooth-paper contract, finite UV/tangent geometry, existing material mapping and planned budget. Formal KTX composition, native lighting, collision, performance, memory and Space Pro still require Root.
