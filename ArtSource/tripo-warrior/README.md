# CLI runtime swordsman

The runtime candidate uses the approved baked reduction and biped re-rig of the
overseas Tripo CLI character. Its original download is preserved at
`tripo-out/f2a5c5b3-rig-bb23cd4c/model.glb`.
The source is 2,390,360 bytes with SHA-256
`6e2ddd38982a5dc3baee45f7db8f545988e493ba994c29c40fb4ee1cff7cb3c9`.

The geometry originated from `v3.1-20260211`, followed by PBR texturing,
approved 20k-target baked reduction and a new biped rig. Generation consumed
55 API credits and the reduction/re-rig chain consumed 60, totalling 115.
The provider task records are `cli-generation-result.json` and
`cli-runtime-20k-result.json`. The high-detail original remains in
`tripo-out/adult-chinese-male-swordsman-rea-3-4f577636/model.glb` as source
reference.

## Prepared assets

- `tripo_warrior_rigged.glb` contains the metre-scaled body and skeleton.
- `tripo_warrior_rigged_with_dao.glb` adds the existing dao under the actual
  right-hand joint.
- `rigged_alignment.json` records source/output hashes, normalization and the
  static right-hand mounting frame.
- `prepare_rigged_warrior.py` reproduces the outputs with Blender 4.5 Python.

The outer root is `TripoWarrior_Root`. `TripoBody_Root` contains the normalized
source scene. Read **`TripoBody_Mesh`** for body-only bounds. The weapon is
labelled `Weapon_Root` and belongs to `HandGrip_R`, directly under `R_Hand`.
The skeleton branch in the dao variant also contains this weapon subtree.

The runtime source faces +X and is approximately 0.998047024 m high. A common
parent frame rotates it -90 degrees around Y, uniformly scales it to 1.78 m,
centres XZ and sets the foot plane to Y=0. Prepared facing is +Z. Source joint
TRS, skin definition, weights, inverse bind matrices and PBR payload remain
intact. Applying the same parent frame to mesh and joints preserves their
relative skinning transforms under glTF's scene and skin rules.
[Khronos nodes and transforms](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_004_ScenesNodes.html), [Khronos skinning](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_020_Skins.html)

The runtime source contains **10,734 vertices, 18,833 triangles, 1 skin,
78 joints**. The raw rig has zero clips, and the prepared assets contain the
four clips listed below. Basecolor is 2048 square. Normal and metallic-roughness are 1024 square. All are embedded. Existing topology and
source image bytes are preserved. Main owns runtime loading, memory and
rendering measurements on the emulator and Space Pro.

The dao keeps its original metre scale through compensation in the hand
mounting frame. The bind hand is open in a T-pose. The mounting candidate has approximately
3 mm measured handle-vertex clearance in that bind pose. The motion review
below records the curled-finger fit during slash.
The main coordinator owns motion generation, Full Stage integration, project
builds, device input and captures.

## Packed actions and motion review

Both prepared GLBs contain one body, one skin and four named clips targeting
the existing 78 joints. The base geometry, weights, inverse binds and PBR
payload are preserved. Animation target indices are remapped by verified joint
names and full parent chains. Original time/value arrays and LINEAR/STEP
interpolation are copied without resampling. Only referenced animation
accessors are added, with aligned buffer views.
[Khronos animations](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_007_Animations.html), [Khronos buffers and accessors](https://github.khronos.org/glTF-Tutorials/gltfTutorial/gltfTutorial_005_BuffersBufferViewsAccessors.html)

| Clip | Source keyframe range in seconds | Channels |
| --- | --- | --- |
| idle | 0.033333–15.366667 | 234 |
| slash | 0.033333–6.600000 | 234 |
| hurt | 0.033333–13.866667 | 234 |
| fall | 0.033333–3.033333 | 234 |

Blender 4.5 checked all 1166 integer frames. Each clip deforms the mesh, with
maximum difference from its normalized original below 0.0021 mm. DAO follows
R_Hand throughout, and maximum Grip marker error is below 0.000001 m.
The source curves and full interpolation modes match byte-for-byte.
Validation evidence is in review/four_clip_validation.json and
review/four_clip_frames.csv. The generator stages both GLBs and alignment
metadata together and restores the previous files on publication errors.

The 30 fps front/side review in review/slash_offline.mp4 uses source frames
1–198 and the existing mounting frame. Source time is frame/30. The main
cut occupies frames 62–65, approximately 2.067–2.167 s. Peak tip speed is
14.256 m/s at frame 63. Scene target contact and playback range/speed belong
to runtime alignment by the main coordinator.

The current mount requires further grip review. Slash frames 39–45 intersect
the left hand with the blade. In sampled source frames 1/42/63/198, 25 of 567
right-hand vertices enter the handle core, with maximum measured depth about
11.19 mm. The preset holds a curled-finger pose. Close-ups and measurements
are in review/slash_left_hand_f42.png, review/slash_grip_f63_front.png,
review/slash_grip_f63_back.png and review/slash_metrics.json. The package
retains the reviewed mounting frame and source curves for the next grip review.

## Source permission

This batch uses the international Tripo API. Its developer terms have distinct
commercial-use and output-rights provisions. Sections 3.2 and 5.2 describe
permitted uses and distinguish Paid Users from Free Users. Account-specific commercial, competition and distribution permissions require
confirmation through the applicable terms and billing status.
[ov API terms](https://developers.tripo3d.ai/en/terms), [API billing](https://developers.tripo3d.ai/en/docs/billing)

The dao's editable source and provenance are in `../dao/README.md`.

## Earlier delivered artifacts

`tripo_warrior.glb`, `tripo_warrior_with_dao.glb` and `tripo_warrior.blend`
preserve the earlier H2.5 Studio static study. Its original file, prompt,
settings and hashes are in `source/`, `generation-prompt.txt` and
`source/generation.json`. The Studio study contains zero skins and zero clips.
Its free-plan permission review remains recorded separately in that provenance.

`mixamo_input.fbx` preserves a local FBX Binary 7.4 conversion of the earlier
1.78 m static body. It embeds the original basecolor and normal media, with
39,964 triangles and one UV set. Packed roughness/metallic data remain in its
source GLB. The file records the earlier conversion work. The active rigged
asset route is the approved Tripo CLI chain above.
