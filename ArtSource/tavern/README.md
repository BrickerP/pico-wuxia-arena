# Tavern entrance study

An editable, modular entrance vignette: timber structure and roof, left and
right doors, individual flagstones and a hanging paper lantern. The geometry,
plaster map, and hand-built `酒` sign were made for this project. Blender
coordinates use metres, +Z up, X across the entrance, and -Y toward the front.
The overall structure is roughly 4.3 m wide and 3.3 m high.

`tavern_slice.blend` is the editable source. The `Structure_Root`,
`Door_Left_Root`, `Door_Right_Root`, `Paving_Root`, and `Lantern_Root` children
are separate modules in the source and interchange files; stone pieces inside
the paving mesh remain separable as loose parts. The two door roots are at their
outer hinge edges and the lantern root is at its suspension point; door motion
has not been implemented. `tavern_slice.fbx` is a Unity
import candidate and `tavern_slice.glb` is a portable comparison. The two
preview PNGs use an offline Blender studio; they are **not** Unity or PICO
screenshots. Studio cameras and lights are excluded from both exports.

## Texture sources

Six 1K JPEGs in `textures/` come from Poly Haven and are provided under its
[CC0 license](https://polyhaven.com/license); source files are included so the
Blender project is reproducible. Credit is recorded even though CC0 does not
require attribution:

- [Fine Grained Wood](https://polyhaven.com/a/fine_grained_wood), Rob Tuytel:
  colour, roughness and OpenGL normal maps, used on timber.
- [Granite Tile](https://polyhaven.com/a/granite_tile), Charlotte Baglioni:
  colour, roughness and OpenGL normal maps, used on flagstones and bases. Each
  stone samples a portion of the source image to avoid repeating its tile grid.
- `tavern_plaster_color.png` is generated locally by `build_tavern.py`.

CC0 permits commercial use and redistribution of the above texture files; the
competition's separate originality requirement and VibeLab conditions still
need confirmation before the eventual submission.

To rebuild and verify on this machine, run from this directory:

```sh
BLENDER=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$BLENDER" -b --factory-startup --python-exit-code 1 --python build_tavern.py
"$BLENDER" -b --factory-startup --python-exit-code 1 --python verify_tavern.py
```

Use another Blender 4.5 LTS executable path on other machines. The build
overwrites its generated files. The verifier opens all three formats and checks
module hierarchy, geometry, scale and texture availability, including a
missing-module failure case. It does not validate Unity's importer, materials,
lighting, draw calls, colliders, or PICO device performance.
