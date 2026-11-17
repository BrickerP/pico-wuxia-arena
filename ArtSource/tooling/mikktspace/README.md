# Prepared character tangent operation

Copy this directory as `ArtSource/tooling/mikktspace/` after Root review. There are no npm installs or cross-repository runtime dependencies. `mikktspace.mjs` is the exact self-contained module already shipped by Three 0.185.1 (including embedded WASM); its SHA256 is enforced before import. The original MikkTSpace zlib notice, mikktspace-wasm MIT and Three MIT licenses are in `licenses/`.

Run from any working directory:

```sh
node ArtSource/tooling/mikktspace/build_tangents.mjs INPUT.glb OUTPUT.glb REPORT_DIRECTORY
node --test ArtSource/tooling/mikktspace/test_tangents.mjs
```

The input is the prepared, embedded-PNG GLB immediately after wrist authoring and before texture encoding. Input/output must differ. The geometry contract is a reviewed static artifact, never automatically learned or replaced by a production run. Its hash covers actual triangle corners for every non-TANGENT attribute, static node/skin topology and IBM, materials, images, textures and scene placement. It ignores animation payloads, unused vertex rows and storage index identities so newer authored clips and necessary tangent seam splits do not create false geometry changes. Strict preservation independently checks the original BIN prefix, original accessors/views, every indexed original attribute byte, non-target primitives and all animation sampler bytes before publishing output.

Only body primitives 0–4 receive Mikk tangents. Each different float32 tangent/sign group at a shared vertex gets a copied original attribute row; tangents are never seam-averaged. Original unused vertex rows remain present. glTF W is negated once according to the existing Mikk API convention. The original 78 bones, all source clips, node transforms and weapon primitives are retained. Existing DAO missing tangent warnings are intentionally outside this operation.

`degenerate_policy.json` admits only the reviewed primitive0/corner12326 exact P/N/UV witness. A mismatched witness, any other invalid tangent corner, unstable +U projection or more than 30 bad corners fails. The one admitted exact-zero UV face uses the maximum-|dU| source edge projected onto its original normal, preserving W. This is MikkTSpace plus one explicit repair, not pure Mikk.

The CLI writes `generation.json` and `vertex_origin.json` into the specified report directory. `generation.preservation` contains the before-publication gates; source/output path strings are informational and the caller must normalize them before hashing a relocatable production receipt. The command itself neither changes the input nor writes into historical audit directories.

Tangent portability is established by these checks. Native visual quality and runtime performance still require Root's same-model PICO review; no quality gain is implied by removing five missing-tangent warnings.
