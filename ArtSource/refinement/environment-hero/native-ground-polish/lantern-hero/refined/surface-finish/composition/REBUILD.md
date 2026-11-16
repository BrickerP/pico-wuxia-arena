# 灯笼纸罩表面完整私有组合

此目录是唯一完整私有组合输出。输入正式湿石KTX庭院 `bd5d21ef…`、灯笼表面模块 `c2ae86e…` 和一张纸纤维图，输出完整PNG复核场景及完整KTX原生候选。它们不覆盖app、正式资源或Root公共producer。

```sh
python3 ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/compose_lantern.py
python3 ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/verify_composition.py
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_png.glb ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/review/png_gltf_validator.json
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/courtyard_lantern_surface_ktx.glb ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/review/ktx_gltf_validator.json
```

The formal KTX source remains immutable. For each output the composer removes exactly 2,936 old wood, 504 bronze and 960 paper triangles inside only the two front-lantern envelopes. It appends the same four module meshes once and references those meshes from two distinct parent nodes at the source translations `[-2.15,2.70,-4.78]` and `[2.15,2.70,-4.78]`; no geometry is duplicated for the second instance.

Material10 changes are precise: baseColorTexture index becomes 41, emissiveTexture stays/index becomes 41, image41 payload is replaced by the new fiber map, while MR texture39 and normal texture40 do not change. The PNG output embeds the source fiber PNG; the KTX output embeds its UASTC/Zstd KTX2 counterpart, 1024×512 with 11 mips. Texture41 is migrated from PNG `source` to the existing `KHR_texture_basisu` extension in the KTX output. Materials remain 32; images and textures remain 50; no material/image table entries are appended.

`courtyard_lantern_surface_png.glb` is the actual full-scene offline render candidate. Blender cannot import the formal KTX extension, so render it against the original PNG-equivalent source in a fixed normal eye view:

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/render_composition.py -- before
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-ground-polish/lantern-hero/refined/surface-finish/composition/render_composition.py -- after
```

This is not a KTX load or device test. Actor assets changed during Root's motion reimport, so both render phases exclude actor geometry rather than mix identities.

The verifier includes normal input identity plus negative wrong-identity guards; it checks all non-target meshes/nodes, source texture/image payloads excluding image41, material10-only binding changes, exact removal counts, new tangent geometry, no lights/cameras/animation and the 249,958 expanded triangle cap. It does not prove PICO KTX loading, native lights, reflection, performance, memory, collision, navigation or Space Pro behavior.
