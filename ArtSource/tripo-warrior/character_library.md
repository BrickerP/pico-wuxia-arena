# Character motion library production

`prepare_character_library.py` prepares independently generated characters for
the existing PICO runtime. The input manifest lives beside this document and
all source paths resolve from this directory.

```json
{
  "motion_source": {
    "source": "expanded/base/tripo-out/rig-folder/model.glb",
    "source_sha256": "SHA-256 of the 41-joint rig",
    "clips": [
      {
        "name": "walk",
        "source": "expanded/base/tripo-out/walk-folder/model.glb",
        "source_sha256": "SHA-256 of the original motion GLB"
      }
    ]
  },
  "characters": [
    {
      "id": "base",
      "name": "试刀客",
      "source": "tripo-out/f2a5c5b3-rig-bb23cd4c/model.glb",
      "source_sha256": "SHA-256 of this target's 78-joint rig",
      "height_metres": 1.78,
      "grip_source": {
        "source": "tripo-out/bb23cd4c-retarget-a65f688a/model.glb",
        "source_sha256": "SHA-256 of this target's native slash",
        "time_seconds": 2.117
      },
      "output": "base.glb"
    }
  ]
}
```

The shape above illustrates one clip entry. A production manifest includes
`idle`, `walk`, `turn`, `hit_body`, `hit_head`, `hit_side` and `fall`, with
unique character IDs and output filenames. Every source must exist and match
its declared hash before publication.

Run with the project's Blender 4.5 Python environment.

```sh
"$BLENDER" --background --factory-startup --python-exit-code 1 \
  --python ArtSource/tripo-warrior/prepare_character_library.py -- \
  --manifest ArtSource/tripo-warrior/motion_library.json
```

## Motion processing

The source 41-joint biped and target 78-joint biped have different local rest
frames. For each original key time, the producer samples source world poses,
computes each mapped joint's world rotation delta from its bind frame and
applies that delta to the target bind rotation. The resulting world rotations
are converted back through the animated target parents. Target local bone
lengths, geometry, skin weights and inverse binds remain intact.

`Root` maps to `BoneRoot`. Root and Hip translations use scaled world-space
position deltas. Elbow and knee share bones blend the adjacent segment motion
deltas. The target's 30 finger joints use the local pose sampled from its own
native slash, holding the authored curled grip during the transferred motions.

The runtime `slash` uses each target's native animation and original channels.
Its existing contact marker remains 2.117 seconds. The remaining clips are
resampled retargeted curves. Full original CLI GLBs remain source assets.

The mounting frame transfers the reviewed wrist-to-grip offset in metre space
to each target's rest axes. DAO geometry remains rigidly skinned to `R_Hand`
inside the same mesh and skin.

## Outputs and completion boundary

`library/` contains each named runtime GLB, body-only GLB, alignment metadata,
retargeted source clips and `characters.json`. Per-character body, weapon and
alignment files use the existing grouped publication path. The index is
published after all requested characters are prepared. Root owns copying the
completed runtime GLBs into `models/opponents/`.

Alignment records include source/output hashes, clip time ranges, retarget
sample counts, normalization, joint counts and weapon binding. They establish
asset provenance and processing identity. Foot planting, anatomy-specific grip
clearance, skin deformation and transition quality remain visual acceptance
items. This producer preserves source motion timing and target limb lengths,
with world-space motion retargeting and finger-pose preservation.

Root performs production export with the completed manifest and copies the
completed assets into the runtime directory. Application builds and device
acceptance use the game's main delivery process.
