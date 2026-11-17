# Private image-only PBR compression candidates

These GLBs are offline candidates. They are not formal library/app assets. Root owns native loading, visual comparison, final producer integration and publication. No device, Gradle or paid generation was used here.

| Candidate | SHA256 | File bytes |
| --- | --- | ---: |
| `candidates/base-uastc.glb` | `55f782d00949fd01f973e9b41dcb698ee4f2e2932665ab3c9dc5f6e10909dbd1` | 46,688,000 |
| `candidates/dao-grip-uastc.glb` | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` | 4,332,212 |

The table and validation files above document the earlier full-resolution baseline; new outputs use the material-limited policy below. `candidates/offline-validation.json` aggregates the baseline checks: 21 tests passed; all 39 image records passed the official KTX2 glTF Basis validator; each candidate has zero core-validator errors and the same core geometry findings as its original. New image/extension warnings reflect the glTF validator limitation explained below. `*.quality.json` records full-resolution decoded top-mip error by channel; this measures offline compression error, not native appearance.

`compress_pbr.py` replaces embedded PNG/JPEG payloads with embedded KTX2 UASTC. Runtime images have a default maximum dimension of 1024, with explicit material-prefix overrides allowing 2048; smaller source images are never upscaled. The source GLB and its 4K images remain unchanged. All non-image JSON semantics and every non-image bufferView byte are checked against the pinned source. This covers geometry, indices, UVs, skin/inverse binds, node rest transforms, animation channels/interpolation, and anchor extras. bufferView offsets and buffer length change when repacked. In the runtime output, PNG/JPEG payloads are removed, texture `source` fallback is absent, and `KHR_texture_basisu` is both used and required.

All image roles and resize budgets are derived from actual material texture slots. Every override prefix must match a rendered material; a shared image referenced by materials with conflicting 1024/2048 budgets is rejected rather than silently changing another material's budget. Base color/emissive use sRGB + BT709; normal/MR/occlusion use linear + unspecified primaries. Every image must have a classified role. Mixed sRGB/linear images, conflicting wrap pairs for one image, unsupported glTF extensions, external images and image/accessor bufferView sharing fail closed. Normal maps stay RGB XYZ; `--normal-mode`, normalization, swizzles and RDO are deliberately absent. Mips preserve each sampler's S/T wrap behavior, including glTF's default REPEAT. Only REPEAT and CLAMP_TO_EDGE are supported; MIRRORED_REPEAT is explicitly rejected.

For differing S/T modes, the helper supplies explicit, legal mip images to `ktx create --levels N`, ordered from the runtime-sized top level to 1×1, without `--generate-mipmap` or resizing flags. Lower levels use separable, antialiased Lanczos4 with half-pixel centers, periodic indices on repeat axes, and edge extension on clamp axes. Filtering is recursive float64 without byte-quantization feedback, clipping after each complete 2D level. Color RGB is decoded to linear light and encoded back to sRGB; alpha stays linear. PNG inputs are rounded half up. Top-level resizing uses the same color-domain and sampler-boundary rules; its runtime-sized pixels become mip level zero. Existing NumPy 2.0.2 is reused; no new dependency was installed. Uniform repeat/clamp continues using the official CLI mip generator.

The per-axis extension passed 29 tests, including independent official-CLI single-axis boundary references in both orientations, the analytic sRGB black/white mean (188 versus linear 128), alpha, original top pixels, legal rectangular chains, real UASTC all-level readback, and GLB non-image preservation. `candidates/per-axis-validation.json` records the final helper identity, SETTINGS, and all four actual publisher input sampler inventories; none contains MIRRORED_REPEAT. Per-image manifests record mip source, generator source SHA/version, axis modes, dependency versions and every explicit mip input pixel hash. Cache keys include this provenance.

Fixed settings: official KTX-Software v4.4.2 Darwin arm64, UASTC quality 3 of 0–4, 2 threads, Zstd 18, complete Lanczos4 mip pyramid, top-left orientation, and material-limited top-level resizing before mip generation. Quality 4 was too slow for the first native baseline; quality 3 keeps all maps UASTC and does not change the 4×4 block footprint. UASTC is lossy; Zstd is lossless. Native close-up comparison still decides visual acceptance.

The official release package was downloaded, checked against its GitHub asset SHA256, and extracted locally without installing globally. Both encoder and libktx binaries are SHA-pinned. `tooling/download-identity.json` records release/package identity; CLI help snapshots are in `tooling/`. Each output `.manifest.json` records source/output SHA, image/pixel hashes, dimensions, color roles, all encoder settings/commands, KTX2 header facts and preservation results. Cache keys include decoded pixel hash, full command and binary identity.

Run from the repository root, with new output filenames:

```sh
python3 ArtSource/refinement/pbr-compression/compress_pbr.py \
  --input ArtSource/tripo-warrior/library/base_prepared_png.glb \
  --sha256 057c6ea9b8a7671689da1040623db68761ed3c37e31b6366def6329b77b902a6 \
  --output ArtSource/refinement/pbr-compression/candidates/base-1024-uastc.glb \
  --encoder ArtSource/refinement/pbr-compression/tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx

python3 ArtSource/refinement/pbr-compression/compress_pbr.py \
  --input ArtSource/refinement/character/veteran-head-refinement/model/veteran_head_raw.glb \
  --sha256 ec67ae3c649752e9e6a2f1f676e7d3e74dc94e9607f721a6440af20e5f52d776 \
  --output ArtSource/refinement/pbr-compression/candidates/veteran-head-2048-uastc.glb \
  --encoder ArtSource/refinement/pbr-compression/tooling/extracted/KTX-Software-4.4.2-Darwin-arm64-tools.pkg/Payload/usr/local/bin/ktx \
  --material-overrides-json '{"HeroHead_":2048}'

python3 -m unittest discover -s ArtSource/refinement/pbr-compression -p test_compress_pbr.py -v

node ArtSource/refinement/pbr-compression/tooling/validate-glb.cjs \
  ArtSource/refinement/pbr-compression/candidates/base-1024-uastc.glb \
  ArtSource/refinement/pbr-compression/candidates/base-1024-uastc.gltf-validation.json
```

Every image is independently checked by `ktx validate --gltf-basisu --warnings-as-errors`. The official glTF validator 2.0.0-dev.3.10 does **not** support `KHR_texture_basisu`; its extra `image/ktx2` MIME warnings, unsupported extension and unused-image messages are expected limitations. Compare its core geometry findings with the original baseline reports in `tooling/`; do not treat this validator as a KTX2 validator. Unit fixtures test preservation and encoder channel behavior; they are not native-loading proof.

Native gate for Root: load compressed enemy plus compressed player dao via the existing `Entity.loadSuspend` path with one active enemy; verify all clips, near-face/eye/neck, normal/MR appearance, one enemy switch and old-entity disposal, and inspect native fatal/NO_MEMORY logs. The final prepared head/locomotion GLB must be compressed afresh with its own source SHA. These baseline files must not replace the final producer output by filename alone.

GLB size and UASTC mip/block bytes are **not** native GPU memory measurements. PICO supporting this extension does not prove a particular runtime transcode format, successful native loading or resolution of OOM.

Official references:

- [KHR_texture_basisu](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_texture_basisu)
- [KTX-Software v4.4.2 release](https://github.com/KhronosGroup/KTX-Software/releases/tag/v4.4.2)
- [KTX CLI create](https://github.khronos.org/KTX-Software/ktxtools/ktx_create.html)
- [KTX CLI validate](https://github.khronos.org/KTX-Software/ktxtools/ktx_validate.html)
- PICO official installed 6.1 docs: `/Users/yupeng/Library/PICO/sdk/6.1/agent-vault/spatial/documentation/spatial-sdk_resource-management_model.md` and `spatial-sdk_resource-management_texture.md`.
