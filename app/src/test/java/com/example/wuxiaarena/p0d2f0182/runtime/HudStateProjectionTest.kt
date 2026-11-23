package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.p0d2f0182.ui.ArenaHudScales
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HudStateProjectionTest {
    @Test fun fightingControlsOnlyRedrawForTheirOwnStateChanges() {
        val fight = state.copy(result = TrialResult.FIGHTING, inputReady = true, pauseReason = null)
        val strike = fight.copy(score = fight.score + 25, health = fight.health - 25, feedback = CombatFeedback.HIT)
        assertTrue(shouldPublishHudState(fight, strike))
        assertFalse(shouldPublishControlState(fight, strike))
        assertTrue(shouldPublishControlState(fight, strike.copy(result = TrialResult.VICTORY)))
        assertTrue(shouldPublishControlState(fight, strike.copy(roundGeneration = fight.roundGeneration + 1)))
        assertTrue(shouldPublishControlState(fight, strike.copy(inputReady = false)))
        assertTrue(shouldPublishControlState(fight, strike.copy(pauseReason = PauseReason.USER)))
    }

    private val state = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error }).viewState.copy(
        result = TrialResult.FIGHTING, pauseReason = null, inputReady = true,
        phase = EnemyPhase.PREPARING, attackDirection = AttackDirection.OVERHEAD,
        phaseElapsedNanos = 0L,
    )

    @Test fun theExtendedWindupAdvancesTheSealWithoutPublishingPanelContent() {
        val scales = ArenaHudScales()
        val start = state.copy(phaseRemainingNanos = 1_200_000_000L)
        for (step in 0..30) {
            val elapsed = 40_000_000L * step
            val next = start.copy(phaseElapsedNanos = elapsed, phaseRemainingNanos = 1_200_000_000L - elapsed)
            scales.update(next)
            assertFalse(shouldPublishHudState(start, next))
            assertEquals(0.94f + 0.06f * step / 30, scales.telegraph, 1e-6f)
        }
        assertTrue(shouldPublishHudState(start, start.copy(attackDirection = AttackDirection.LEFT)))
    }

    @Test fun hitEmphasisSettlesInItsLayerAndPausingClearsItImmediately() {
        val scales = ArenaHudScales()
        for (feedback in listOf(CombatFeedback.HIT, CombatFeedback.HEADSHOT, CombatFeedback.GUARDED_HIT, CombatFeedback.PARRY)) {
            val hit = state.copy(phase = EnemyPhase.HIT, feedback = feedback)
            for ((elapsed, expected) in listOf(0L to 1.04f, 80_000_000L to 1.02f, 160_000_000L to 1f, 500_000_000L to 1f)) {
                val next = hit.copy(phaseElapsedNanos = elapsed)
                scales.update(next)
                assertFalse(shouldPublishHudState(hit, next))
                assertEquals(expected, scales.feedback, 1e-6f)
            }
            scales.update(hit)
            val paused = hit.copy(pauseReason = PauseReason.USER)
            scales.update(paused)
            assertEquals(1f, scales.feedback, 0f)
            assertTrue(shouldPublishHudState(hit, paused))
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

    @Test fun finalGripAndEffectiveEnemyPoseChangesDoNotPublishHudState() {
        val rendered = state.copy(
            playerWeaponGrip = WeaponGrip(Vector3(0.3, 1.2, -0.4), Quaternion(0.0, 0.0, 0.0, 1.0)),
            enemyPoseClip = "attack_overhead", enemyPoseSourceSeconds = 0.5,
            enemyPoseDirection = AttackDirection.OVERHEAD,
        )
        val samples = listOf(
            rendered.copy(playerWeaponGrip = WeaponGrip(Vector3(0.31, 1.2, -0.4), Quaternion(0.0, 0.0, 0.0, 1.0))),
            rendered.copy(playerWeaponGrip = WeaponGrip(Vector3(0.3, 1.2, -0.4), Quaternion(0.0, 0.1, 0.0, 1.0))),
            rendered.copy(playerWeaponGrip = null),
            rendered.copy(enemyPoseClip = "attack_left"),
            rendered.copy(enemyPoseSourceSeconds = 0.52),
            rendered.copy(enemyPoseDirection = AttackDirection.LEFT),
            rendered.copy(enemyPoseClip = null, enemyPoseSourceSeconds = null, enemyPoseDirection = null),
        )
        assertFalse(shouldPublishHudState(state, rendered))
        for (sample in samples) {
            assertFalse(shouldPublishHudState(rendered, sample))
            assertFalse(shouldPublishHudState(sample, rendered))
        }
    }

    @Test fun visibleHudChangesStillPublishAlongsideFinalGripAndEnemySourceSamples() {
        val pose = state.copy(
            playerWeaponGrip = WeaponGrip(Vector3(0.3, 1.2, -0.4), Quaternion(0.0, 0.0, 0.0, 1.0)),
            enemyPoseClip = "attack_overhead", enemyPoseSourceSeconds = 0.52,
            enemyPoseDirection = AttackDirection.OVERHEAD,
        )
        for (visibleChange in listOf(
            pose.copy(score = state.score + 10),
            pose.copy(health = state.health - 1),
            pose.copy(feedback = CombatFeedback.BLOCK),
            pose.copy(phase = EnemyPhase.STARTUP),
            pose.copy(pauseReason = PauseReason.USER),
            pose.copy(inputReady = false),
            pose.copy(counterOpen = true),
        )) assertTrue(shouldPublishHudState(state, visibleChange))
    }

    @Test fun receiptProvenanceDoesNotForceHudPublication() {
        val diagnostic = state.copy(
            diagnosticUiFrameNanos = 8_000_000_000L,
            diagnosticPublishSource = "tracking_controllers",
            diagnosticHandStamp = ObservationStamp(12L, 7_999_000_000L, 2L, InputOrigin.DESKTOP),
        )
        assertFalse(shouldPublishHudState(state, diagnostic))
        assertTrue(shouldPublishHudState(state, diagnostic.copy(score = state.score + 10)))
        assertTrue(shouldPublishHudState(state, diagnostic.copy(phase = EnemyPhase.STARTUP)))
    }
}
