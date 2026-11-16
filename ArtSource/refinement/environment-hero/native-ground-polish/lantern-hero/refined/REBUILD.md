# 正门灯笼圆润精修模块

本目录只交一个可复用模块，供Root合入当前湿石KTX正式庭院 `bd5d21ef…`。不创建第二庭院、不覆盖app资源、不改Root灯光/位置/构建/设备/Git。Blender无法导入当前正式GLB的 `KHR_texture_basisu`，因此建模和离线预览只读取已验证的PNG等价庭院 `5619ce1c…` 来复用同名既有材料；模块清单始终钉住正式bd5d哈希。PNG预览不验证KTX加载。

根目录 `/Users/yupeng/projects/personal/pico-wuxia-arena`：

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/build_refined_lantern.py
python3 ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/verify_refined_lantern.py
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/lantern_refined_module.glb ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/review/module_gltf_validator.json
```

`lantern_refined_module.glb` has local identity root and uses existing material bindings only: paper10, wood0, bronze7 and rope24. It has a 48-segment smooth paper shell, 12 continuous swept six-sided bamboo ribs, four physical collar rings, caps, closed hanging eye, short suspension cord, tassel cord/knot and five tassel strands. Exported normal-mapped meshes include UVs and tangents. No paper map, emissive extension, transmission, light or new material is added.

Root composes two instances using `module_manifest.json`:

| instance | Stage translation | rotation | scale |
| --- | --- | --- | --- |
| front_left | `[-2.15,2.70,-4.78]` | identity | `[1,1,1]` |
| front_right | `[2.15,2.70,-4.78]` | identity | `[1,1,1]` |

Remove only the same audited two old front lantern envelopes before attaching this module. The refined module is 3,748 triangles, two instances 7,496; audited old components are 4,400 triangles, yielding +3,096 and planned expanded budget 246,454. It remains under the formal 250k cap. Material/image counts stay 32/50 after semantic mapping to existing source materials.

Preview images are in-memory composition only: source old faces within the two exact envelopes are removed, the module imports twice, and the scene renders with the existing 1.65m camera/light and a 0.5m local camera. The local framing received the one allowed correction to reveal the whole cap/ring/rib/tassel chain; geometry and normal-eye view were not altered. Current actor assets changed during Root's action reimport, so the renderer excluded actors in both images rather than show a mismatched identity. This is not a device screenshot or a KTX/native lighting result.

`verify_refined_lantern.py` checks formal bd5d identity, 48 segment/12 continuous rib contract, existing material bindings, finite nondegenerate UV/tangent geometry, local envelope, old-envelope selection, source anchors and planned composition budget. It does not prove the actual formal composition, KTX load, lighting, collision, navigation, performance, memory or Space Pro behavior.
