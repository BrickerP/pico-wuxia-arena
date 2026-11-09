# Greybox character and motion candidates

This is a **temporary, stylized mannequin**, not the final wuxia character. It
uses the skinned mannequin and selected actions from Quaternius's Universal
Animation Library 2 Standard. `graybox_candidate.blend` is editable;
`graybox_candidate.glb` is an asset candidate for the PICO Spatial pipeline.
The source rig has 65 joints and a `hand_r` bone that is only a proposed weapon
attachment location. Its mapping to a runtime entity and the grip of the real
dao have not been validated.

The preview PNGs are offline Blender renders. The pale blade pointer shown in
those images is a review-only prop, deliberately excluded from the GLB; it is
not the actual dao or a validated hand pose. No application scene or runtime
controller is included.

The candidate GLB uses glTF's Y-up coordinates. `../verify_glb_axes.py` checks
its container, skin and animation presence. Its apparent facing direction and
the `hand_r` attachment must still be checked in the PICO Stage coordinate
system; a mannequin with no facial features cannot establish facing by itself.

## Source and license

- Original work: [Universal Animation Library 2 Standard, uploaded by Quaternius](https://opengameart.org/content/universal-animation-library-2), CC0 1.0.
- `source/UAL2_Standard.glb` is the original Standard GLB from the publisher's
  archive, dated 2026-01-23. SHA-256:
  `0815dd05531cae9bc313fc9c0ba81330bc72f8e19ec45f73738e74ddc5796a43`.
- `source/LICENSE.txt` is the license text shipped in that archive. The source
  may be redistributed and used commercially under CC0. Competition
  originality and VibeLab conditions are separate and remain unconfirmed.

## Clips and limitations

All ten exported clips use the same skeleton. The `Sword_A/B` clips and their
recovery clips are successive stages of a source combo; their mapping to the
player's left/right attack directions is **not** yet established. The original
root location channels are set to zero for fixed-position greybox use. For the
two combo attacks and recoveries, pelvis and leg channels are additionally held
at the source idle pose to avoid the original lunge. This alters the intent of
the source movement; transitions, PICO runtime and playtesting are required
before adoption.

| Clip | Origin and intended use |
| --- | --- |
| `Graybox_Idle_Shield` | Source shield-oriented idle; a temporary idle, not a final sword-ready pose. |
| `Sword_A_InPlace`, `Sword_B_InPlace` | Source combo upper-body attacks with root translation removed and lower body held; direction and transitions need calibration. |
| `Sword_A_Recovery_InPlace`, `Sword_B_Recovery_InPlace` | Source upper-body recovery candidates with the same lower-body treatment. |
| `Overhead_Chop_Candidate` | Source `TreeChopping_Loop` used as a grounded overhead-motion study; weapon grip, attack windup and one-shot timing need choreography. |
| `Sword_Block_InPlace` | Source block candidate with root translation removed. |
| `Graybox_Guard_Hold` | Project-authored hold sampled from the source block pose; visual stand-in for sustained guard. |
| `Graybox_Hit_Recoil`, `Graybox_Parry_Stagger` | Project-authored simple torso reactions based on the same rig and idle pose. |

The source also contains a jumping combo and a fall. They are omitted because
they do not satisfy the current grounded, fixed-position greybox assumptions.
These are raw motion candidates: no attack windows, animation events, damage,
weapon collision or gameplay behavior are encoded.

## Rebuild and checks

```sh
BLENDER=/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender
"$BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python build_graybox.py
"$BLENDER" -b --factory-startup --disable-autoexec --python-exit-code 1 --python verify_graybox.py
```

Run from this directory. The build overwrites generated files. The verifier
reopens the Blender source and the GLB, binds each action slot, checks rig and
skin weights, checks each integer frame's action movement, root displacement
and both feet, compares clip durations and all joint transforms after reimport,
and rejects a missing guard action. It does not test
PICO loading, skeletal playback, sword attachment, combat timing, draw calls,
physical comfort or device performance.
