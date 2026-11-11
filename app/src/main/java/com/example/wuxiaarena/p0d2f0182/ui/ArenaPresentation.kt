package com.example.wuxiaarena.p0d2f0182.ui

import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback

/** A retained attack direction during recovery is history, not a new incoming strike. */
internal fun arenaShowsIncomingStrike(result: TrialResult, pauseReason: PauseReason?, inputReady: Boolean, phase: EnemyPhase): Boolean =
    result == TrialResult.FIGHTING && pauseReason == null && inputReady &&
        (phase == EnemyPhase.PREPARING || phase == EnemyPhase.STARTUP || phase == EnemyPhase.ACTIVE)

/** Uses the simulation clock, so no independent UI animation can continue after a pause. */
internal fun arenaIncomingSealScale(phase: EnemyPhase, elapsedNanos: Long, preparationNanos: Long): Float {
    if (phase != EnemyPhase.PREPARING || preparationNanos <= 0L) return 1f
    val progress = (elapsedNanos.coerceAtLeast(0L).toDouble() / preparationNanos).coerceIn(0.0, 1.0)
    return 0.94f + 0.06f * progress.toFloat()
}

internal fun arenaHitFeedbackScale(phase: EnemyPhase, elapsedNanos: Long, feedback: CombatFeedback?): Float {
    if (phase != EnemyPhase.HIT) return 1f
    when (feedback) {
        CombatFeedback.HIT, CombatFeedback.HEADSHOT, CombatFeedback.GUARDED_HIT, CombatFeedback.PARRY -> Unit
        else -> return 1f
    }
    val progress = (elapsedNanos.coerceAtLeast(0L).toDouble() / 160_000_000L).coerceIn(0.0, 1.0)
    return 1f + 0.04f * (1f - progress.toFloat())
}
