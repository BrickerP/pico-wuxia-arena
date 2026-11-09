# Wuxia swordsman candidate

This is an **editable, stylized character and motion study**, not an accepted
photorealistic enemy. The dark crossed jacket, sash, sleeves, hair, face wrap
and trousers are project-authored geometry and materials, fitted to the existing
65-bone Quaternius greybox rig. The mannequin body and source motion are still
visible in the face, hands, joints and movements; replacing or improving them
will be necessary to meet the intended realistic visual direction.

`warrior_candidate.blend` contains the working rig, garment, original dao and
review studio. `warrior_candidate.glb` contains the rig, the two skinned body
and garment meshes, the actual dao, its three markers and ten motion clips.
The dao root is parented to `hand_r`; `Grip` is aligned to that bone's tail.
This point alignment does not prove that fingers wrap the handle naturally or
that the PICO runtime preserves the attachment. No PICO application or combat
controller is included.

The four `warrior_review_*.png` images and `warrior_review_sequence.mp4` are
**offline Blender reviews**. The video samples the existing clips at 15 fps,
adds four interpolated poses at each transition, and labels the active segment.
It is a review experiment, not a newly exported GLB animation, a gameplay timing
contract or a recording from the PICO emulator.

## Source and permission

- Quaternius, [Universal Animation Library 2 Standard](https://opengameart.org/content/universal-animation-library-2): CC0 1.0; the original Standard GLB and distributed license are preserved in `../graybox/source/`. See `../graybox/README.md` for source hash, clip origins and modifications.
- Poly Haven, [Rough Linen](https://polyhaven.com/a/rough_linen): CC0; photography by colormass, processing by Rico Cilliers. The original 1K color, roughness and OpenGL normal maps are in `textures/`. `warrior_linen_indigo.png` is a colorized derivative; `warrior_jacket_color.png` adds a project-painted crossed lapel.
- The project dao is imported from `../dao/dao_study.glb`; its editable source and provenance are described in `../dao/README.md`.
- CC0 permits commercial reuse; the competition's originality rules and VibeLab distribution terms are separate and have not been verified.

## Motion, coordinates and limits

All clips use the existing greybox skeleton. On the authoring rig's X axis,
which is also glTF X, the sampled `Sword_A_InPlace` tip moves from X = -1.261 m
at frame 7 to +0.031 m at frame 13; `Sword_B_InPlace` moves from +0.687 m at
frame 7 to -1.535 m at frame 9. These are opposite horizontal directions in
the source clips, not accepted player-relative attack labels. They depend on
the actor being placed and oriented as intended in PICO Stage; the timing and
strike windows still need choreography and gameplay validation. The overhead
candidate comes from a tree-chopping loop and is not yet a final combat chop.

At the checked guard, hit, slash A/B and overhead integer frames, and all 152
frames of the review sequence, the Grip-to-`hand_r`-tail distance is below
0.002 m. A discrete triangle-surface overlap test found no contacts between
the blade and body/garment faces weighted mainly to pelvis, spine, neck or
head at those samples. It does **not** check the whole body, finger contact,
cloth self-intersection, blade containment, continuous swept collisions
between samples, arbitrary transitions or runtime physics.

The GLB currently contains 4 meshes, 16 material primitives, 15 materials,
7 images, 1 skin and 10 animations; source and GLB contain 22,263 triangles
across the body, garments and dao. These are inventory figures, not proof of
rendering cost, draw calls, frame rate or Space Pro suitability.

## Rebuild and verify

Run from the project root with Blender 4.5 LTS and ffmpeg available:

```sh
PICO_ART_BLENDER=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$PICO_ART_BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python ArtSource/warrior/build_warrior.py
"$PICO_ART_BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python ArtSource/warrior/verify_warrior.py
"$PICO_ART_BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python ArtSource/warrior/preview_warrior.py
"$PICO_ART_BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python ArtSource/warrior/preview_warrior.py -- --glb
"$PICO_ART_BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python ArtSource/warrior/preview_warrior.py -- --render
```

The build overwrites generated assets. The verifier compares blade geometry and
markers with the original dao GLB, checks normalized skin weights and ten
clips, samples joint and attachment transforms in Blender and after GLB
reimport, and exercises missing-guard, moved-tip and shifted-grip rejection.
The preview script separately checks every sampled clip/transition pose and can
render the MP4. None of these tests runs the PICO app, proves character quality,
or measures physical-device performance or comfort.
