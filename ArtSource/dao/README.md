# Dao study, revision 2

Editable original weapon geometry with a curved tip, fuller, aged fittings,
and uneven wrapped grip. The reference for approximate historical proportions
and material combinations is the [Metropolitan Museum's Qing saber](https://www.metmuseum.org/art/collection/search/31110):
its catalogue lists a 72.4 cm blade and steel, iron, silk, leather and wood.
The object is a reference; no museum image or geometry is included here.

- `dao_study.blend` is editable. `dao_study.fbx` is the Unity interchange
  candidate; `dao_study.glb` is a second portable copy. All three contain the
  proposed named anchors; the two preview PNGs are offline Blender renders.
- `dao_steel_color.png`, `dao_leather_color.png`, and `dao_cord_color.png` are
  generated for this project and packed in the Blender source. The materials
  and surface wear remain a work in progress, not a final real-time look.
- In Blender coordinates, +Z runs from the handle towards the blade, +X points
  toward the cutting edge near the guard and Y is thickness. The origin and
  `Grip` and `Blade_Base` positions match the previous study. To follow the new
  curvature, `Blade_Tip` moved from X=0.0122 m to X=0.0532 m (both Z=0.735 m).
  The blade segment remains approximately 0.721 m. Coordinate conversion,
  grip pose and these endpoints still need agreement with the combat team.
- No Unity prefab or `.meta` files are included because the Unity baseline was
  not present in this branch. The offline studio is excluded from exports.

To rebuild and verify on the current machine, run from this directory:

```sh
BLENDER=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$BLENDER" -b --factory-startup --python-exit-code 1 --python build_dao.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python verify_dao.py
```

Use another Blender 4.5 LTS executable path on other machines. The build
overwrites the generated assets in this directory. The verifier reopens the
source and both exports, checks scale, geometry, materials and anchors, and
rejects missing or off-edge anchors. Unity import, real-time appearance, actual
draw calls, PICO performance and interaction are not covered by this check.
