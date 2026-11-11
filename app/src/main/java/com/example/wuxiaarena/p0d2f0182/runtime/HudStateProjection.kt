package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.EnemyPhase

/** Suppress pose-only HUD updates while preserving the simulation clock used by visible accents. */
internal fun shouldPublishHudState(previous: ArenaViewState, state: ArenaViewState): Boolean {
    val visible = state.result == TrialResult.FIGHTING && state.pauseReason == null && state.inputReady
    val usesPhaseClock = visible && when (state.phase) {
        EnemyPhase.PREPARING -> (state.attackDirection?.preparationNanos ?: 0L) > 0L
        EnemyPhase.HIT -> when (state.feedback) {
            CombatFeedback.HIT, CombatFeedback.HEADSHOT, CombatFeedback.GUARDED_HIT, CombatFeedback.PARRY -> true
            else -> false
        }
        else -> false
    }
    val hudComparable = state.copy(
        simulationNanos = previous.simulationNanos,
        phaseElapsedNanos = if (usesPhaseClock) state.phaseElapsedNanos else previous.phaseElapsedNanos,
        phaseRemainingNanos = previous.phaseRemainingNanos,
        enemyPosition = previous.enemyPosition,
        enemyYawRadians = previous.enemyYawRadians,
        hitStop = previous.hitStop,
        deathElapsedSeconds = previous.deathElapsedSeconds,
        enemyTravelMeters = previous.enemyTravelMeters,
        enemyGaitMeters = previous.enemyGaitMeters,
        enemyMoveDirection = previous.enemyMoveDirection,
        playerBladeBase = previous.playerBladeBase,
        playerBladeTip = previous.playerBladeTip,
        playerBladeTipSpeed = previous.playerBladeTipSpeed,
        playerBladeAtRest = previous.playerBladeAtRest,
        playerMotionGeneration = previous.playerMotionGeneration,
        playerHeadPosition = previous.playerHeadPosition,
        enemyRecoilOffset = previous.enemyRecoilOffset,
        enemyBladeBase = previous.enemyBladeBase,
        enemyBladeTip = previous.enemyBladeTip,
    )
    return hudComparable != previous
}
