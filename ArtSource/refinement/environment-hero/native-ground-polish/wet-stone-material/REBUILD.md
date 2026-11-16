# Wet-stone material first piece

This is an image-only material candidate based on the immutable authoring asset `ArtSource/refinement/environment-hero/native-fight-entrance/courtyard_native_entrance.glb`, SHA `96c554cc73bfe4b654cc9045e3d0f6464838c6a7517f59da0dd4bb8c65ab242d`. It replaces the embedded base-color and metallic-roughness payloads used by material8, `EH Stone | walked granite`. The normal map, all geometry, scene hierarchy, lights, layouts, Stage coordinates, combat clearance, materials count and texture count remain unchanged. The app runtime courtyard is a downstream deployment output and is never an authoring input; Root's promotion to `bd5d21ef…` does not change this source.

The review PNG GLB is `courtyard_wet_stone_png.glb`. It contains the exact two authoring PNGs and is used only because Blender can render the complete scene reliably. The private runtime candidate is `courtyard_wet_stone_ktx.glb`: those same two maps are embedded as KTX2 UASTC with full mips and `KHR_texture_basisu`; it is the file for Root's native material/loading review. PNG review is not evidence that PICO loads or transcodes the KTX candidate.

From the repository root:

```sh
python3 ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/build_wet_stone.py
python3 ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/verify_wet_stone.py
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_png.glb ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/review/png_gltf_validator.json
node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/courtyard_wet_stone_ktx.glb ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/review/ktx_gltf_validator.json
```

For a non-destructive rebuild, pass `--output-dir <private-directory>` to `build_wet_stone.py`. Compare both rebuilt GLBs and the two authoring PNGs byte-for-byte with this packet before replacing any candidate. The maintenance rebuild ran while the runtime was already `bd5d21ef…`; all four outputs matched `5619ce1c…` / `bd5d21ef…` and their original PNG identities. Existing candidates and all images stayed in place.

`texture_provenance.json.build_execution` records the current builder identity and immutable source. `delivery_manifest.json.original_authoring_execution` preserves the complete original packet/provenance and its historical code hashes, including the original runtime-path alias when it still contained `96c554`. The delivery `files` list records current maintained code. `maintenance` records the real byte-identical private rebuild and five checks, and explicitly states that no images were rerendered. Re-seal only after verification with `python3 ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/finalize_delivery.py`.

The only authored raster maps are `textures/wet_stone_basecolor_1024.png` and `textures/wet_stone_metallic_roughness_1024.png`. Both derive directly from the original embedded material8 Granite Tile maps: neutral low-frequency darkening creates nonuniform moisture without a green tint or painted reflection; only the MR green roughness channel changes, retaining red/blue channels. The pre-existing material8 normal map continues to carry the scan's stone grain and shallow grooves. No reflection is baked into albedo.

License provenance is local and reproducible: the prior portable source maps were cropped from Poly Haven's Granite Tile scan by Charlotte Baglioni, under CC0, recorded in `ArtSource/tavern/README.md` lines 22–25. No new external download is used. Exact input/output hashes, pixel statistics, original embedded-map hashes, authoring formula and compression commands are in `texture_provenance.json`.

KTX encoding reuses the repository's official KTX-Software 4.4.2 Darwin-arm64 chain: UASTC quality 3, 2 threads, Zstd18, full Lanczos4 mip chain, no resize inside the encoder. The source maps are authored at 1024² and the KTX maps have 11 mip levels. The existing KTX chain pins the encoder and libktx hashes; validation is run during `build_wet_stone.py` with `ktx validate --gltf-basisu --warnings-as-errors`.

`render_wet_stone.py` delegates to the original ground review's fixed 1.65m and 0.5m cameras and stage2 night lighting. Its actor inputs are the exact original `6649302a…` PNG / `f6bc15d6…` KTX pair and their encoding/alignment files already present in `ArtSource/refinement/combat-direction/native-weighted-overhead/integration/candidate-library-v5/`. They are historical authoring fixtures, not the current runtime actor. Missing or mismatched fixtures stop reproduction rather than silently excluding the actor. No asset copy or current/old input fallback is made. The comparison imports complete GLBs and records input hashes. It is an offline comparison, not a PICO screenshot; this maintenance did not run it. For a separately authorized rerender, use one Blender process and two threads:

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/render_wet_stone.py -- before
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python-exit-code 1 --python ArtSource/refinement/environment-hero/native-ground-polish/wet-stone-material/render_wet_stone.py -- after
```

The retained visual gate is the original offline review: normal eye and close views showed neutral, nonuniform dampness without green water patches or mirror-plastic highlights. Fixed offline lighting did not prove bright wet reflections. Root owns downstream runtime promotion and native KTX/IBL/performance review; this source-path maintenance neither revokes that promotion nor claims new native quality acceptance.

`verify_wet_stone.py` checks source identity, exact scene/geometry/node identity, only two image payload/texture binding changes, 32 materials/50 images, source normal-map identity, generated-map size/neutrality/roughness bounds, KTX headers/mips and no runtime lights/cameras/animation. Its GLB metrics remain exactly 243,358 expanded triangles, 181,594 unique triangles, 14,113,296 unique attribute bytes and 1,175,868 index bytes. These are GLB data metrics, not PICO GPU-memory or performance measurements.
