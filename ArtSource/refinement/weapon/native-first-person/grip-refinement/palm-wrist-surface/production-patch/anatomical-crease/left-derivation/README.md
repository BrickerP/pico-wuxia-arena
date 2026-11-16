# Anatomical Right → common-Grip Left

Input is the actual `anatomical-crease/right_hand_patch.glb`, SHA `a9809a4515c4448033797847c7b42f2dfe556d323e33b2a185facffc4ac1f862`. Its technical verification and delta identify the accepted anatomical edit, including the 14 authorized metacarpal weight rows. The earlier `3000…` candidate and `3a1be1dd…` geometry are not production inputs.

From the repository root, using the existing Python/NumPy environment:

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/left-derivation/derive_left.py
```

To regenerate the expected bytes in RAM and re-audit the existing GLB without writing model bytes:

```sh
python3 -B ArtSource/refinement/weapon/native-first-person/grip-refinement/palm-wrist-surface/production-patch/anatomical-crease/left-derivation/derive_left.py --verify-only
```

The thin adapter loads the pinned original `left-rebuild/build_left.py` generic data functions and independent `verify_left_rebuild.py` math. It never calls the old hardcoded build entry point, edits that frozen package, or copies its d8 model. The old d8 model is read only as a rejected negative fixture. All reused code hashes are recorded in `handoff.json` and `verification.json`.

Reflection is baked as `S=diag(-1,1,1,1)`: positions/normals reflect X, indexed triangle winding reverses, node/IBM transforms use `S*M*S`, rotation/translation animation outputs are transformed, and R_/L_ semantics swap in both directions. The complete 78-joint palette and its ordering remain. UV, texture bytes and all weight values—including the authorized 14 rows—are retained. The new root is identity in common Grip; there is no C/B frame, extra offset, negative scale or SDK transform change.

`verification.json` independently checks default and grip 0/0.5/1 actual LBS, normals, winding, rig/IBM/animation/appearance preservation and the protected domain. The reused 28 controls run against the current a980 source and derived Left, including negative mutations and synthetic tangent xyz/w checks. The actual source has no TANGENT; no runtime tangent-generation claim is made.

Full-hand self crossings are inherited equally: open/mid 0, closed 109, added 0. The real dao remains unreflected and is checked by component topology. Closed Left has the existing approximately 0.09344 mm shallow index sample; fixed-dao open/mid thumb penetrations around 11.0676/4.8757 mm remain disclosed. This mirror operation does not repair those inherited states or establish continuous-time clearance.

Outputs are private `left_hand_anatomical.glb`, `mapping.json`, `verification.json` and `handoff.json`. Root must integrate Right and Left together and inspect actual native rendering/physiology. No app/formal asset, runtime API, device, Git or Blender work is performed here.
