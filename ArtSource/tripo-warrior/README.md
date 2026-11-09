# Tripo swordsman

The character was generated in Tripo Studio using the prompt saved in
`generation-prompt.txt`. The selected delivery is a free static GLB.

- `tripo_warrior.glb` contains the character and named placement markers in metres.
- `tripo_warrior_with_dao.glb` adds the existing dao at the static installation candidate.
- `tripo_warrior.blend` preserves the editable placement hierarchy.
- `source/tripo_warrior_static.glb` is the original Tripo download.
- `source/generation.json` records the generation settings, source ID, hashes,
  credit use and export restrictions.
- `alignment.json` records the scale and marker positions for integration.

## Generation and export

The source was generated on 2026-11-09 with H2.5 Legacy, a target of 40,000
triangles, 2K textures, PBR materials and a neutral T-pose. Generation consumed
30 existing credits. Tripo's Mixamo humanoid auto-rig consumed another 20
credits, and its `slash` preset played in Studio. The account's export dialog
labels Export Skeleton as Subscribers Only. The user selected free static
GLB delivery. The local files therefore contain zero skins and zero animations.
[Source model](https://studio.tripo3d.ai/workspace/generate/94b2c7c4-0125-4ae8-8923-476a16fcdf73)

## Placement

The original character has a height of approximately 0.999817 m. Its feet
already lie on Y=0, its XZ bounds are centred and its face points along glTF
+Z. The prepared body is uniformly scaled to 1.78 m including the topknot.
The imported dao retains its original metre scale. Exact scale and positions
are in `alignment.json`.

The hierarchy begins at `TripoWarrior_Root`. `TripoBody_Metric` contains the
scaled character, and `HandGrip_R` carries the dao's `DAO_Root` in the alignment variant. `Grip`,
`Blade_Base` and `Blade_Tip` retain their existing weapon meanings.
`HandGrip_R` is a static palm-side installation candidate. The source hand is
open in a T-pose with largely connected finger geometry. Natural grasp and
animated attachment require further source capability and visual review.

The Tripo source cloth has strong specular highlights in offline inspection.
A rough blue-cloth pixel mask gives a median G roughness of approximately
0.106. Source material content is preserved for runtime inspection.

## Source permission and review

Tripo's official sources conflict about free-model commercial rights. Terms
section 5.2.1 and the commercial-use help page reserve rights or mark Free
commercial use as unavailable. The Pricing & Credits product document says
free commercial use is available with attribution. Commercial, competition
and platform distribution permission remains unresolved for this asset.
[Terms](https://www.tripo3d.ai/terms), [commercial-use help](https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially), [Pricing & Credits](https://www.tripo3d.ai/product-doc/getting-started/pricing-credits)

The dao's editable source and provenance are in `../dao/README.md`. The main
coordinator owns Full Stage integration and emulator or Space Pro observations.

## Asset checks

Blender 4.5.15 reimport and an independent read of both GLBs confirmed a
body height of 1.779999971 m, feet on Y=0 and forward +Z. All three Tripo
texture payloads and material bindings are preserved. In the dao variant,
Grip and HandGrip_R differ by less than 0.00001 m, the blade marker segment
is 0.720675775 m, and the weapon retains its original scale.

The final static pose yields zero detected triangle-surface intersections
between the dao meshes and the body. The nearest measured handle vertex is about
2.686 mm from the body. The mounting point is 50 mm along the measured
open-palm outward normal. Animated grip, general collision behaviour and
runtime material appearance remain for subsequent review.
