# Dao study

First-pass, original weapon asset for artistic and integration review. The
`.blend` is editable; `.fbx` is the intended Unity interchange candidate, and
`.glb` is a second portable interchange copy. The two PNGs are **offline Blender
studio renders**, not screenshots of Unity or a PICO headset.

- Unit scale is metres. Overall length is approximately 0.97 m; the proposed
  blade segment from `Blade_Base` to `Blade_Tip` is approximately 0.72 m.
- `DAO_Root` is at the guard; `Grip`, `Blade_Base` and `Blade_Tip` are named
  empties. Blade endpoints lie on the cutting edge rather than the centre of
  the blade. Their final orientation and use must be agreed with the combat team.
- In Blender coordinates, +Z points from the handle towards the tip and +X
  points toward the sharpened edge near the guard; Y is blade thickness.
  The exported files preserve the proposed points when re-imported in Blender;
  Unity axis conversion is still unverified.
- Geometry and the brushed-steel colour map were made for this project. No
  third-party asset or texture is included. The material and surface wear are
  a first study, not a final textured hero prop.
- No Unity scene, prefab or `.meta` files are included: those can only be
  produced and reviewed against the actual Unity baseline. Blender's studio
  lights and cameras are deliberately excluded from both exports.

To rebuild or verify with Blender 4.5 LTS, run from this directory. On the
current machine the isolated installation is used because the existing
Homebrew `blender` launcher points to a missing app; on another machine, set
`BLENDER` to its Blender executable instead.

```sh
BLENDER=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$BLENDER" -b --factory-startup --python-exit-code 1 --python build_dao.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python verify_dao.py
```

The build overwrites the six generated files in this directory. The check
opens both interchange formats again, checks their named anchors, scale,
geometry and materials, and rejects a missing anchor or an off-edge tip. Unity
import, visual material fidelity, interaction, device performance and the
full art slice remain to be verified separately.
