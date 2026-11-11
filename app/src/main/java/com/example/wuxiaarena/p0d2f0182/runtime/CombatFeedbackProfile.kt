package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.HitZone
import kotlin.math.roundToInt

internal data class ImpactAccent(
    val strength: Double,
    val soundRate: Float,
    val visualScale: Float,
    val lightDurationNanos: Long,
    val hapticLevel: Int,
    val hapticFrequency: Int,
    val hapticDurationMillis: Int,
)

/** Presentation times use real nanoseconds and never scale tracked head or hand poses. */
internal object CombatFeedbackProfile {
    private const val SLOW_HOLD_NANOS = 220_000_000L
    private const val SLOW_RECOVERY_NANOS = 180_000_000L
    private const val SLOW_SPEED = 0.35

    // Integral of the slowdown deficit, including the smoothstep recovery.
    const val DEATH_SLOWDOWN_DELAY_NANOS = 201_500_000L

    /** Material chooses the contact texture. Anatomical and lethal results add emphasis. */
    fun accent(impact: CombatImpact): ImpactAccent {
        val (peak, frequency, duration) = when (impact.kind) {
            CombatImpactKind.SOFT_HIT -> Triple(160, 100, 26)
            CombatImpactKind.HARD_HIT -> Triple(205, 240, 12)
            CombatImpactKind.GUARDED_HIT -> Triple(165, 165, 20)
            CombatImpactKind.BLOCK -> Triple(190, 150, 28)
            CombatImpactKind.PARRY -> Triple(245, 300, 14)
            CombatImpactKind.PLAYER_HIT -> Triple(185, 85, 40)
            CombatImpactKind.SKILL -> Triple(210, 140, 42)
            CombatImpactKind.EXECUTION -> Triple(240, 75, 58)
        }
        val headHit = impact.appliedDamage > 0 && impact.zone == HitZone.HEAD
        val strength = if (impact.strength.isFinite()) impact.strength.coerceIn(0.0, 1.0) else 0.0
        val emphasizedStrength = when {
            impact.fatal -> 1.0
            headHit -> maxOf(strength, 0.75)
            else -> strength
        }
        val soundRate = when {
            impact.fatal -> 0.90f
            headHit -> 1.08f
            else -> 1f
        }
        val visualScale = when {
            impact.fatal -> 1.30f
            headHit -> 1.12f
            else -> 1f
        }
        val lightDuration = when {
            impact.fatal -> 100_000_000L
            impact.kind == CombatImpactKind.PARRY -> 90_000_000L
            headHit -> 75_000_000L
            else -> 60_000_000L
        }
        return ImpactAccent(
            emphasizedStrength, soundRate, visualScale, lightDuration,
            if (impact.fatal) 245 else (emphasizedStrength * peak).roundToInt(),
            if (headHit && !impact.fatal) frequency + 20 else frequency,
            when {
                impact.fatal -> 72
                headHit -> maxOf(duration, 38)
                else -> duration
            },
        )
    }

    fun hitStopNanos(impact: CombatImpact): Long = when {
        impact.fatal -> 150_000_000L
        else -> when (impact.kind) {
            CombatImpactKind.SOFT_HIT -> if (impact.zone == HitZone.HEAD) 90_000_000L else 70_000_000L
            CombatImpactKind.HARD_HIT -> 85_000_000L
            CombatImpactKind.GUARDED_HIT -> 30_000_000L
            CombatImpactKind.BLOCK -> 35_000_000L
            CombatImpactKind.PARRY -> 95_000_000L
            CombatImpactKind.SKILL -> 100_000_000L
            CombatImpactKind.EXECUTION -> 150_000_000L
            CombatImpactKind.PLAYER_HIT -> 0L
        }
    }

    /** Integrates 0.35x for 220ms, then smoothly recovers to 1x over 180ms. */
    fun deathElapsedNanos(elapsedAfterStop: Long): Long {
        require(elapsedAfterStop >= 0L) { "death presentation time must be non-negative" }
        if (elapsedAfterStop <= SLOW_HOLD_NANOS) return (elapsedAfterStop * SLOW_SPEED).toLong()
        if (elapsedAfterStop >= SLOW_HOLD_NANOS + SLOW_RECOVERY_NANOS) {
            return elapsedAfterStop - DEATH_SLOWDOWN_DELAY_NANOS
        }
        val recovery = elapsedAfterStop - SLOW_HOLD_NANOS
        val progress = recovery.toDouble() / SLOW_RECOVERY_NANOS
        val smoothstepIntegral = progress * progress * progress * (1.0 - 0.5 * progress)
        return (SLOW_HOLD_NANOS * SLOW_SPEED + recovery * SLOW_SPEED +
            SLOW_RECOVERY_NANOS * (1.0 - SLOW_SPEED) * smoothstepIntegral).toLong()
    }
}
