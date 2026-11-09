# Tavern entrance study

An editable, modular entrance vignette: timber structure and roof, left and
right doors, individual flagstones and a hanging paper lantern. The geometry,
plaster map, and hand-built `酒` sign were made for this project. Blender
coordinates use metres, +Z up, X across the entrance, and -Y toward the front.
The overall structure is roughly 4.3 m wide and 3.3 m high.

The GLB uses +Y up and maps Blender `(X,Y,Z)` to `(X,Z,-Y)`: the entrance front
is on the GLB's +Z side, toward the user when facing the entrance in Stage.
`../verify_glb_axes.py` checks native node coordinates; placement, materials
and visibility still need to be verified in the actual PICO application.

`tavern_slice.blend` is the editable source. The `Structure_Root`,
`Door_Left_Root`, `Door_Right_Root`, `Paving_Root`, and `Lantern_Root` children
are separate modules in the source and interchange files; stone pieces inside
the paving mesh remain separable as loose parts. The two door roots are at their
outer hinge edges and the lantern root is at its suspension point; door motion
has not been implemented. `tavern_slice.glb` is the candidate interchange
for the PICO Spatial pipeline. The previous `tavern_slice.fbx` is retained as
an older research snapshot; it is not regenerated or used by this pipeline. The
three preview PNGs use an offline Blender studio; they are **not** PICO device
or emulator screenshots. Studio cameras and lights are excluded from the GLB.

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
- `tavern_wood_wet_rough.png` and `tavern_stone_wet_rough.png` are generated
  from the respective CC0 roughness maps with uneven wetness. The original
  source maps remain in `textures/`. `tavern_plaster_color.png` and
  `tavern_lantern_color.png` are original generated maps.

The shallow stone gate surround and layered eaves are informed by the
[UNESCO description of Xidi and Hongcun](https://whc.unesco.org/en/list/1002/)
and the [Huangshan government's description of Hui architecture](https://www.huangshan.gov.cn/zjhs/rwhz/hpjz/8294054.html).
These are structural references; no source photographs are included.

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
overwrites its generated files. The verifier opens the source and GLB and checks
module hierarchy, geometry, scale and texture availability, compares wetness
maps to their source roughness, and exercises a missing-module failure case.
It does not validate the PICO loader, materials,
lighting, draw calls, colliders, or PICO device performance.
