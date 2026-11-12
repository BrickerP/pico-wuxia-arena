package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedbackProfile

/** Values feed the existing single contact light; this policy never overrides actor PBR. */
internal data class NativeImpactLight(
    val red: Float, val green: Float, val blue: Float,
    val intensity: Float, val attenuationRadius: Float, val durationNanos: Long,
)

/** Ordinary BODY feedback belongs to the real-contact core and dry fragments alone. */
internal fun nativeImpactLight(impact: CombatImpact): NativeImpactLight? {
    if (impact.kind == CombatImpactKind.PLAYER_HIT) return null
    if (!impact.strength.isFinite()) return null
    val accent = CombatFeedbackProfile.accent(impact)
    val strength = accent.strength.toFloat()
    return when {
        impact.fatal -> NativeImpactLight(1f, 0.82f, 0.56f,
            120f + 40f * strength, 0.45f, 90_000_000L)
        impact.kind == CombatImpactKind.SOFT_HIT && impact.zone == HitZone.BODY -> null
        impact.kind == CombatImpactKind.SOFT_HIT && impact.zone != HitZone.HEAD -> null
        impact.kind == CombatImpactKind.PARRY -> NativeImpactLight(1f, 0.82f, 0.46f,
            80f + 40f * strength, 0.35f, 70_000_000L)
        impact.kind == CombatImpactKind.HARD_HIT || impact.kind == CombatImpactKind.GUARDED_HIT ||
            impact.kind == CombatImpactKind.BLOCK -> NativeImpactLight(1f, 0.82f, 0.46f,
            30f + 30f * strength, 0.22f, 45_000_000L)
        impact.kind == CombatImpactKind.SOFT_HIT -> NativeImpactLight(1f, 0.86f, 0.66f,
            20f + 20f * strength, 0.18f, 45_000_000L)
        else -> NativeImpactLight(1f, 0.82f, 0.56f,
            80f + 40f * strength, 0.35f, 60_000_000L)
    }
}

/** Late delivery samples the existing pulse's true age; it must not restart a shorter flash. */
internal fun remainingNativeImpactLightNanos(impact: CombatImpact, simulationNanos: Long): Long {
    if (impact.atNanos < 0L || impact.atNanos > simulationNanos) return 0L
    val light = nativeImpactLight(impact) ?: return 0L
    val age = simulationNanos - impact.atNanos
    return (light.durationNanos - age).coerceAtLeast(0L)
}
