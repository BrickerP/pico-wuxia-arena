"""Create a review-only patch from locked source snapshots. Never writes app/ or uses Git."""
from pathlib import Path
import difflib
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = 'app/src/main/java/com/example/wuxiaarena/p0d2f0182/content/'
TEST = 'app/src/test/java/com/example/wuxiaarena/p0d2f0182/content/'
CANDIDATE = HERE / 'candidate'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    sources = {name: (ROOT / name).read_bytes() for name in [
        BASE + 'HomeStage.kt', BASE + 'EnemyHitFlash.kt', BASE + 'BodyFlashMaterial.kt',
        TEST + 'EnemyHitFlashPulseTest.kt', TEST + 'BodyFlashMaterialTest.kt',
        BASE + 'CombatEffects.kt', BASE + 'ContactParticleEmitter.kt', BASE + 'SoftContactEnvelope.kt',
        BASE + 'ContactParticleMotion.kt', BASE + 'ContactParticlePresets.kt',
        'app/src/main/java/com/example/wuxiaarena/p0d2f0182/runtime/CombatFeedbackProfile.kt',
    ]}
    home = sources[BASE + 'HomeStage.kt'].decode()
    for old in [
        'import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedbackProfile\n',
        'import com.example.wuxiaarena.core.combat.CombatImpactKind\n',
        '        var flash: EnemyHitFlash? = null\n',
        '            flash?.close()\n            flash = null\n',
        '        loaded.flash?.present(state, events)\n',
        '                    loaded.flash = EnemyHitFlash(entity)\n',
    ]:
        assert home.count(old) == 1, old
        home = home.replace(old, '')
    home = home.replace('    private var lastImpact = Long.MIN_VALUE', '    private val seenImpactLights = mutableSetOf<Long>()')
    home = home.replace('            lastImpact = Long.MIN_VALUE', '            seenImpactLights.clear()')
    old_fresh = '        val fresh = events.filterIsInstance<CombatImpact>().filter { it.id > lastImpact }\n        if (fresh.isNotEmpty()) lastImpact = fresh.maxOf { it.id }'
    assert old_fresh in home
    home = home.replace(old_fresh, '        val fresh = events.filterIsInstance<CombatImpact>().filter { seenImpactLights.add(it.id) }')
    start = home.index('        val impact = currentContactImpacts(fresh, state.simulationNanos).firstOrNull()')
    end = home.index('\n        val terminal =', start)
    home = home[:start] + '''        val impact = currentContactImpacts(fresh, state.simulationNanos).firstOrNull {
            remainingNativeImpactLightNanos(it, state.simulationNanos) > 0L
        }
        if (impact != null) {
            val cue = checkNotNull(nativeImpactLight(impact))
            val remaining = remainingNativeImpactLightNanos(impact, state.simulationNanos)
            val direction = impact.normal.normalizedOrNull() ?: TrackingVector3(0.0, 0.0, 1.0)
            val point = impact.point + direction * 0.035
            val position = Vector3(point.x.toFloat(), point.y.toFloat(), point.z.toFloat())
            if (position.x.isFinite() && position.y.isFinite() && position.z.isFinite()) {
                light.components.set(PointLightComponent(
                    Color4(cue.red, cue.green, cue.blue, 1f), cue.intensity, cue.attenuationRadius,
                ))
                checkNotNull(light.components[TransformComponent::class.java]).setPosition(parent.convertPositionFrom(position, null))
                pulseUntil = now + remaining
            }
        }''' + home[end:]
    target = CANDIDATE / 'src/main/java/com/example/wuxiaarena/p0d2f0182/content/HomeStage.kt'
    target.write_text(home)
    assert 'EnemyHitFlash' not in home
    assert '110f + 180f * strength' not in home
    changes = {BASE + 'HomeStage.kt': home}
    for path in [BASE + 'EnemyHitFlash.kt', BASE + 'BodyFlashMaterial.kt', TEST + 'EnemyHitFlashPulseTest.kt', TEST + 'BodyFlashMaterialTest.kt']:
        changes[path] = None
    for folder, target_prefix, name in [('main', BASE, 'NativeImpactLight.kt'), ('test', TEST, 'NativeImpactLightTest.kt')]:
        changes[target_prefix + name] = (CANDIDATE / f'src/{folder}/java/com/example/wuxiaarena/p0d2f0182/content/{name}').read_text()
    patch = []
    for name, after in changes.items():
        before = sources[name].decode() if name in sources else ''
        patch.extend(difflib.unified_diff(before.splitlines(True), [] if after is None else after.splitlines(True),
            fromfile='a/' + name if before else '/dev/null', tofile='b/' + name if after is not None else '/dev/null'))
    output = HERE / '01-local-native-impact.patch'
    output.write_text(''.join(patch))
    lock = {'scope': 'App files are input only. Patch/candidate not installed or applied.',
            'input_source_sha256': {k: sha(v) for k, v in sources.items()},
            'candidate_sha256': {k: None if v is None else sha(v.encode()) for k, v in changes.items()},
            'patch': {'file': output.name, 'sha256': sha(output.read_bytes())},
            'app_source_stable_after_prepare': all((ROOT/k).read_bytes() == v for k, v in sources.items())}
    assert lock['app_source_stable_after_prepare']
    (HERE / 'source_lock.json').write_text(json.dumps(lock, indent=2) + '\n')
    print(json.dumps({'patch': output.name, 'changed_paths': len(changes), 'actor_unlit_path_deleted': True, 'locked_sources_untouched': True}))

if __name__ == '__main__': main()
