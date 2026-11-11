# Dry soft-contact candidate

`soft_contact_polish.glb` is derived from the current `app/src/main/assets/models/effects/soft_contact.glb`. This directory is a candidate only; the app resource is not overwritten.

The existing amber/tan dry-contact materials and every selected source vertex RGBA are retained. The source core is 1.85× wider in its contact plane and lasts 65ms; the source cut accent is 1.25× wider and lasts 85ms. The accent is a transient contact cue, not a persistent mark attached to skin. No water, blood, new texture, emissive boost, or inferred wetness is added.

The source `debris` mesh contains fifteen separate puff/streak pairs. Twelve pairs are selected deterministically and each is recentered at its own puff origin, producing `chip_00` through `chip_11`. Their individual initial velocities, local initial positions, lifetimes (180–290ms), and opacity keys are in `motion.json`. Source particle shape, normals and RGBA are preserved. Each mesh keeps its contact-plane orientation; this is soft debris, not a steel spark that must align its long axis to velocity.

Runtime uses the real contact point, projected actual cutting tangent T, outward normal N, and B=N×T. The common anchor is offset by 8mm along N exactly once by its owner. The motion's local p0 does not contain that offset. Stage gravity remains (0,−9.81,0) regardless of contact orientation. Sample the true current presentation age; before birth and at or beyond lifetime the particle is hidden. Missing/invalid tangent must not create a guessed directional spray.

## Rebuild and validate

Run from the repository root:

```bash
python3 ArtSource/refinement/effects/runtime-polish/soft/build_soft.py
python3 ArtSource/refinement/effects/runtime-polish/soft/verify_soft.py
```

The transformation uses only Python's standard library and the existing source GLB; it has no Blender runtime dependency. `provenance.json` records the exact input/output identities and component selection. Six independent checks cover source material/RGBA/geometry preservation, node/index validity, per-particle motion, gravity frame, expired/invalid inputs, and bounded core lifetimes. `verification.json` records the observed result.

## Offline visual comparison

`render_soft_review.py` imports the actual runtime first-opponent actor read-only and resolves a front-facing torso surface. It uses one actual surface point and one fixed camera for each before/after pair, at 0.8m, 1.5m and 3m; perspective horizontal field of view is 80°. Every imported mesh uses an independent material opacity control through the existing `offline_opacity.py` helper.

The before side reproduces current `CombatEffects` SOFT core (50ms), debris scale and falloff, and 100ms cut. The after side samples the candidate's independent node motion and opacity at a fixed 1.019 node scale. The consumer's additional core growth/accent multiplier is not included here; these frames compare raw candidate envelopes rather than the final SDK consumer. Times are 33ms, 100ms and 233ms. The example tangent is synthetic, explicitly not recorded game input. Images and their actor/effect input hashes are written to `../review/soft_render_manifest.json`; they are production previews, not PICO screenshots or proof that gameplay selected clothing.

```bash
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender \
  --background --factory-startup --threads 2 \
  --python ArtSource/refinement/effects/runtime-polish/soft/render_soft_review.py
```

PICO opacity hierarchy, transparency sorting, actual view-distance readability, trigger timing and performance remain for Root's shared integration and device review.
