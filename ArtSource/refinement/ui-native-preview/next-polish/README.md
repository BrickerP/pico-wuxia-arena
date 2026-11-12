# Native arena UI patch

Product target: the existing Kotlin + PICO Spatial SDK 6.1.9 APK. Root owns application merge, build, PICO Emulator/device verification, Git and publishing. This folder does not change application source.

Apply target: `app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt` only. Base SHA-256: `e9711f73a6578fbfe9c3cf413dfe43257dcdadb7814b3db475eae6fc30ba6a12`. Candidate source: `candidate/src/app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/ArenaHud.kt`. Unified patch: `ui-polish.patch` (Python difflib, no Git operation).

The patch keeps current public signatures, 400x160/400 and 500x260 slots, actions, readiness gates, restart confirmation, all event mappings, phase hints, player charge/release/execution states and terminal combo rule. Normal fighting controls become transparent and retain the original Pause/Restart components; the large status background is removed, with native number Badges and small text shadows for local contrast. Only repeated fighting title/objective/round and the final default in-range footer are omitted.

Isolated Kotlin/Compose compilation: PASS. Design-style scan: 0 errors / 0 warnings, using candidate source and unchanged palette snapshot. No new full design IR was supplied, so R10 IR trace was not claimed. Root still must check live contrast, numeric Badge fit, extreme status capacity, click/hover/haptics and actual combat occlusion in the native APK.

`candidate/candidate-report.json` records immutable source blocks and SHA checks. Public PicoTheme roles, palette, runtime state, timing and input rules remain unchanged. No Gradle or device operation was performed.

The earlier `mock/` files are historical design illustrations. HTML/Web work is stopped: keep existing files, do not maintain them, and do not use them as game acceptance evidence. The native Kotlin patch is the deliverable.
