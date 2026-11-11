# Character library production contract

The sole executable entry is `prepare_character_library.py --manifest`, using Blender 4.5 Python. Relative input paths resolve from this directory. `prepare_rigged_warrior.py` is an internal module; its standalone entry and implicit clip defaults are retired. Historical Tripo generation commands and earlier prepared assets establish source provenance only.

## Current published group

The formal binding is `b03f55e6ee89e551ff2a3933a351a96fff077f8b6ad42adf441d40dcfab4a79f`. The sole formal input is [motion_library.json](motion_library.json). Root has published this group to the library and app, including matching runtime profile identities.

| Runtime output | SHA-256 |
| --- | --- |
| `base.glb` | `722ffe6e9d3d498629b257e88aaeaf3b0ad368e5c5a37be87ccb85d63a6cf83e` |
| `indigo.glb` | `94773349741af7cdd2616bb3f5970c5c9fa16f16199c1d0ce5bf6fde6ee0c54e` |
| `veteran.glb` | `cabf24597a83d46495ad67b451867aaf5e1dad1bbb5df21cae286513af9a17a5` |
| `dao_grip.glb` | `db28d4269cacb45db2cedf4f564d03538484d6471f7b20966b9399ba697f69d0` |

The local `7e1368fe…` APK has shown the first opponent with the new head, eyes and continuous neck, canonical idle, the player weapon and the scene in emulator Full Stage. The scene and opponent attached in approximately 27 seconds in this emulator observation, without NO_MEMORY. Compared with the preceding `767bc0af…` APK, only the two control-panel pose lines changed; the new native image shows the complete panel without covering the enemy face or blade. The 311-test regression preceded that pose edit; only assembly and native visual verification were repeated afterward. This is first-round preparation evidence, not headset performance evidence. Three-round swapping, actual attacks and contacts, close-range material response, GPU bytes and Space Pro performance remain open. See [acceptance](../../docs/acceptance.md) for versioned evidence; the public release is still the earlier APK.

## Required schema 3 inputs

Use the complete [formal manifest](motion_library.json) as the executable input and default test source. A production manifest requires the following fields; a partial illustration is not an executable manifest.

| Field | Contract |
| --- | --- |
| `schema_version` | Exactly `3`. |
| `motion_source` | `contract: motion41`, pinned 41-joint rig and exactly `fall`, `turn`, `hit_body`, `hit_head`, `hit_side`. |
| `locomotion_source` | `contract: locomotion78`, pinned 78-joint rig, frozen `authoring_manifest`, and exactly `idle`／`walk`. |
| `attack_source` | `contract: attack78`, pinned 78-joint rig, frozen `authoring_manifest`, phase markers and distinct OVERHEAD／LEFT／RIGHT descriptors. |
| `characters` | Unique IDs and GLB output names; each target rig, native `grip_source` with sample time, height, reviewed grip frame and right-finger offsets. |
| `weapon_source` | Explicit source path and SHA-256 of the reviewed opponent dao. |
| `player_weapon_source` | Explicit source path and SHA-256 of the reviewed player grip GLB, emitted as `dao_grip.glb`. |
| `body_coverage_calibration` | Pinned calibration JSON for the same target IDs, in prepared actor-root space. |
| `runtime_texture_encoding` | Fixed encoding settings plus pinned `helper`, `encoder`, `release_identity` and `host_python` identities. |
| `production_review` | Required for formal publication: Root approval of the current complete binding and output identities. Private candidate generation produces the review request first. |

Every source must exist and match its declared SHA-256. Locomotion and attack descriptors must identify `stage: authored_raw` and `right_calibration_baked: false`. Missing mandatory inputs, changed source/tool identities, retired schema versions and stale production approval are rejected.

## Ten clips and source timing

The five `motion41` clips, two `locomotion78` clips and three `attack78` clips produce exactly ten runtime animations per character.

Locomotion uses the stage10 `locked_locomotion_inputs.json` family: idle has 91 keys and walk has 185 keys over 0–1.5 seconds. Constant TRS tracks remain STEP. Only the six walk thigh/calf/foot rotation tracks are LINEAR. The producer verifies the canonical guard markers and the locked head ancestor chain at source keys and midpoints. Each attack retains its separate 106-key, 0–1.75-second contract; its contact marker is 1.0 second.

Walk loops from source 1/3 to 1.5 seconds, with duration 7/6 seconds. One 1.45m carrier stride contains six physical steps, three pairs and 1.45/6m per step. Consumers use the same distance-driven gait clock and the exported source contact phases. The source itself does not accumulate forward root travel.

World-space rest rotation and position deltas transfer motion to each target bind frame through the animated target parents. `Root` maps to `BoneRoot` for `motion41`; elbow/knee share bones blend adjacent segment deltas. The existing world-rest transfer also handles both explicit 78-joint families. Each target retains its geometry, local bone lengths, skin weights and inverse binds, under one shared metric normalization.

The right fingers use the target's native grip sample, followed by its reviewed right-finger offsets once across all ten clips. Native slash files are grip provenance, not additional runtime clips. Left-hand policy is authored per legacy motion clip or transferred from the authored 78-joint source family. Opponent dao geometry is rigidly skinned to `R_Hand` inside the same mesh and skin.

## One canonical grounding and proxy frame

For each target, the producer measures the true LBS soles in canonical idle at source zero. It derives one constant world +Y `BoneRoot` shift to put the lowest sole at −0.028m, then applies that same shift to every key of idle, walk and all three attacks. Input times and STEP／LINEAR interpolation remain unchanged. The runtime entity applies +0.028m once.

Grounding does not recompute a separate shift per frame or per clip. Reports retain each foot's actual key/midpoint heights, same-guard endpoint differences and locked-chain evidence. Different target shapes can retain sole residuals; a zero relative head-chain difference does not establish absolute foot contact.

Profiles are generated by evaluating the final encoded GLB. All five canonical clips use the same target-specific bone-local head/body offsets. The head centre and torso XZ axis come from final idle LBS anatomical-region bounds, excluding dao primitives. Body coverage Y preserves the frozen prior bone-relative Y offsets, rebased onto the current canonical guard; it is distinct from the measured torso surface Y bounds. Damage radii and gameplay contact rules keep their existing contract.

The profile JSON is schema 3, retaining `attacks` and adding `locomotion.idle`, `locomotion.walk` and `source_contract`. It records loop timing, stride, six-step contact/stance/swing phases, real curve samples and animation semantic signatures. Each profile binds the complete final model SHA-256; alignment and the review request bind the complete profile SHA-256.

## Mandatory runtime texture encoding

`runtime_texture_encoding.format` is `KHR_texture_basisu`. Its exact `settings` are:

- `codec: uastc`, `uastc_quality: 3`, `threads: 2`, `zstd: 18`.
- `mipmap_filter: lanczos4`, `full_mips: true`, `orientation: top-left`.
- `normal_mode`, `normalize`, `rdo` and `pixel_resize` are all `false`.
- `mip_source.same_axis: ktx-cli-generate-mipmap`; `mip_source.different_axes: explicit-axis-lanczos4-v1`.
- `axis_mips`: `version: 1`, `precision: float64`, `support: 4`, `centers: half-pixel`, `antialias: support-scaled-by-source/target`, `sequence: S-then-T-recursive-unquantized-clipped-linear`, `color_filter: IEC-sRGB-EOTF-linear-filter-OETF`, `alpha_filter: linear-straight`, `quantization: clip-0-1-round-half-up-uint8`, `top: original-decoded-pixels`.

Sampler contracts record explicit `wrap_s` and `wrap_t`. Only REPEAT and CLAMP_TO_EDGE are supported; MIRRORED_REPEAT is rejected. Equal S/T wrap modes use KTX CLI Lanczos4 mip generation. Different S/T modes use explicit per-level Lanczos4 generation under `axis_mips`, filtering S then T recursively in linear float64 without quantized-level feedback, and retaining the original decoded top mip.

The manifest pins the image-only helper, official KTX-Software 4.4.2 encoder and libktx SHA, release identity, and host Python 3.9.6/Pillow 11.3.0/NumPy 2.0.2 identity. The producer checks preservation of non-image GLB fields and animation semantics after encoding.

The three final character GLBs and player `dao_grip.glb` require KTX2/BasisU and contain no PNG fallback. Original source GLBs, `*_body.glb` and `*_prepared_png.glb` remain offline provenance/review assets. Full source texture resolution and geometry are preserved.

## Candidate, approval and atomic publication

From the repository root, set `BLENDER` to the Blender 4.5 executable and generate a private candidate:

```sh
"$BLENDER" --background --factory-startup --python-exit-code 1 \
  --python ArtSource/tripo-warrior/prepare_character_library.py -- \
  --manifest ArtSource/tripo-warrior/motion_library.json \
  --candidate-dir ArtSource/tripo-warrior/review/character-library-candidate
```

The candidate contains final encoded character models, body/prepared PNG review GLBs, alignment, profiles, texture-encoding reports, `characters.json`, `production_review_request.json`, `dao_grip.glb` and its player-weapon/encoding manifests. Retargeted intermediate clips are temporary producer inputs; their identities are recorded in alignment.

Root reviews the full candidate group and approves its binding, character outputs, hand/clip semantic signatures, profiles and encoded player weapon. Root then supplies that approval in the schema 3 formal manifest and runs the same entry without `--candidate-dir`:

```sh
"$BLENDER" --background --factory-startup --python-exit-code 1 \
  --python ArtSource/tripo-warrior/prepare_character_library.py -- \
  --manifest ArtSource/tripo-warrior/motion_library.json
```

After every output passes validation, one grouped publication updates `library/`, runtime opponent models/profiles in `app/src/main/assets/models/opponents/`, and the player weapon at `app/src/main/assets/models/dao_grip.glb`. Root owns this publication; individual model/profile copies or hand-edited hashes do not establish a valid group.

Offline source, LBS and encoding checks establish asset identity and processing fidelity. SDK playback, transitions, actual entity lift, contacts, grip clearance and device memory/performance require acceptance using the final published group.
