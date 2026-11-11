# PICO 07 light look-development review

These images render the actual currently packaged GLBs in Blender. The paired views keep all model bytes, imported idle pose at source 1.0 s, asset placements, camera, resolution, exposure and AgX transform unchanged. They compare only the current lighting values with the target native-light profile. They are **offline direction evidence**, not PICO runtime or visual acceptance.

Target light values: moon 650 lux; amber lantern 1500 lm; warm face bounce **900 lm**; cool edge 900 lm. All light positions/colors and the artistic Blender intensity transfer are in `provenance.json`. The face bounce was raised from the initial 420 lm after inspection found the face too dark. No model materials are edited to achieve that change.

- `offline_current_player.png` and `offline_target_player.png`: player camera, enemy Stage Z −2.4 m.
- `offline_current_fighter_1_5m.png` and `offline_target_fighter_1_5m.png`: same character at 1.5 m camera-to-enemy depth.
- `offline_target_with_mesh_weather_player.png`: a separate integration view of the actual delivered rain tiles, low side haze strips and 30 m unlit sky mesh at time 0.6 s. It is not part of the lighting-only control pair. Haze is mesh alpha, not volumetric fog; rain is mesh geometry, not an SDK particle system.
- `lighting_compare_player.png` and `lighting_compare_fighter_1_5m.png`: labeled current/target contact sheets.

The original assets are read-only. Filtered active environment scenes are stored under `inputs/`; original inactive/orphan nodes are excluded using the existing environment review helper. The opponent is imported directly without rescaling or rotation and uses its imported `idle` NLA at source 1.0 s.

The native-to-Blender point transfer is an explicitly artistic 25 lumens per Blender watt; the sun transfer is 683 lux per Blender sun energy unit. The fixed scale is shared by both profiles and does not establish photometric equivalence with PICO. Native cutoff radii are recorded rather than emulated. Both profiles disable sun and point shadow casting; SDK GroundShadow is not reproduced. The blue world is an offline ambient approximation, and no IBL KTX interoperability is proved. Weather objects are hidden from indirect light paths, so Blender's unlit sky shader does not accidentally illuminate the model.

Reproduce from the repository root:

```sh
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender \
  -b --factory-startup --threads 4 \
  --python ArtSource/refinement/lookdev/render_lookdev.py -- --size 960 --samples 8
```

Root owns packaging, HomeStage connection, build, PICO loading and same-camera runtime capture. Face/dao clarity, alpha sorting, shadow grounding and final headset exposure remain to be checked there.
