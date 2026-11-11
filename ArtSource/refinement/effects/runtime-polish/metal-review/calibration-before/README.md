# Metal ordinary/parry offline review

`metal_1_5m_timeline.png` compares old `metal_contact.glb`, ordinary independent `metal_contact_polish.glb`, and parry independent particles at 33ms, 67ms and 167ms. It uses the current runtime first-opponent actor and a front-facing evaluated steel surface point. Every column uses that same point, 1.5m perspective camera (80° horizontal field of view), light and actor pose.

The contact basis is explicitly synthetic: T=Stage+X, B=Stage+Y, N=Stage+Z. The true evaluated steel normal is recorded separately in `render_manifest.json`, and the example basis is not claimed to match it or recorded gameplay input. This is an offline visual study, not an SDK capture or Space Pro acceptance evidence.

The old column reproduces the prior ordinary METAL layer behavior: core `(0.7+age*3)*1.019`, 65ms core fade, 440ms whole-debris spread and falloff, and 100ms scar fade. No old hand-dependent roll is applied because all three columns intentionally use the same example basis.

Candidate ordinary core scale is `(.85+min(age,.09)*3)*1.019*1.15`; parry multiplies it by 1.7. Particle scale is `1.019*1.25` for ordinary and `1.019*1.65` for parry. Parry initial velocity is multiplied by 1.8; gravity remains Stage `(0,-9.81,0)` and is never scaled. Core opacity/lifetime and each individual particle opacity/lifetime come from the existing 04 `metal/motion.json`, with 65ms ordinary and 90ms parry cores. The particle's source local X aligns with its instantaneous Stage velocity. The common 8mm normal anchor offset is applied once.

Every imported mesh uses its own opacity material through the existing `offline_opacity.py` helper. The manifest records actual input GLB/motion hashes and material ownership counts. No candidate asset, app resource, runtime code or formal library is changed by this renderer.

Rebuild from the repository root:

```bash
/Users/yupeng/Applications/Blender-4.5.15-LTS.app/Contents/MacOS/Blender \
  --background --factory-startup --threads 2 \
  --python ArtSource/refinement/effects/runtime-polish/metal-review/render_metal.py
python3 ArtSource/refinement/effects/runtime-polish/metal-review/compose.py
```
