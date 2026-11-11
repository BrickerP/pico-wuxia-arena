package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HudStateProjectionTest {
    private val state = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error }).viewState.copy(
        result = TrialResult.FIGHTING, pauseReason = null, inputReady = true,
        phase = EnemyPhase.PREPARING, attackDirection = AttackDirection.OVERHEAD,
        phaseElapsedNanos = 0L,
    )

    @Test fun preparationAndContactAccentsReceiveTheirSimulationClock() {
        assertTrue(shouldPublishHudState(state, state.copy(phaseElapsedNanos = 80_000_000L)))
        for (feedback in listOf(CombatFeedback.HIT, CombatFeedback.HEADSHOT, CombatFeedback.GUARDED_HIT, CombatFeedback.PARRY)) {
            val hit = state.copy(phase = EnemyPhase.HIT, feedback = feedback)
            assertTrue(shouldPublishHudState(hit, hit.copy(phaseElapsedNanos = 80_000_000L)))
        }
    }

    @Test fun staticAndHiddenAccentsDoNotPublishClockOnlyChanges() {
        val cases = listOf(
            state.copy(phase = EnemyPhase.STARTUP), state.copy(phase = EnemyPhase.ACTIVE),
            state.copy(attackDirection = null), state.copy(phase = EnemyPhase.HIT, feedback = CombatFeedback.OUT_OF_RANGE),
            state.copy(pauseReason = PauseReason.USER), state.copy(inputReady = false),
            state.copy(result = TrialResult.READY),
        )
        for (previous in cases) assertFalse(shouldPublishHudState(previous, previous.copy(phaseElapsedNanos = 80_000_000L)))
    }

    @Test fun poseOnlyUpdatesStayOffTheComposeStateWhilePhaseChangesPublish() {
        val pose = state.copy(enemyPosition = Vector3(1.0, 0.0, -2.0), enemyYawRadians = 0.4f,
            playerBladeTip = Vector3(0.1, 1.0, -1.0), enemyBladeBase = Vector3(0.2, 1.2, -1.0),
            simulationNanos = 100_000_000L, phaseRemainingNanos = 200_000_000L)
        assertFalse(shouldPublishHudState(state, pose))
        assertTrue(shouldPublishHudState(state, state.copy(phase = EnemyPhase.STARTUP)))
        assertTrue(shouldPublishHudState(state, state.copy(pauseReason = PauseReason.USER)))
    }
}
