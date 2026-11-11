package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class OpponentLoadingSessionTest {
    @Test fun expectedChangeFreezesTheCountdownAndFreshGeometryResumesWithoutConfirmation() {
        val fixture = Fixture()
        assertTrue(fixture.session.startTrial())
        fixture.session.onTick(0L)
        fixture.session.onTick(1_000_000_000L)
        val before = fixture.session.viewState
        assertEquals(TrialResult.COUNTDOWN, before.result)

        assertTrue(fixture.session.beginOpponentChange(before.roundGeneration, before.roundNumber))
        assertFalse(fixture.session.viewState.sceneReady)
        assertFalse(fixture.session.viewState.actionReady)
        assertNull(fixture.session.viewState.pauseReason)
        fixture.session.onTick(40_000_000_000L)
        assertEquals(before.countdownSeconds, fixture.session.viewState.countdownSeconds)

        fixture.session.setEnemyGeometry(fixture.spawn, 1.55)
        assertFalse(fixture.session.viewState.actionReady)
        fixture.observe()
        assertTrue(fixture.session.viewState.actionReady)
        fixture.session.onTick(50_000_000_000L)
        assertEquals(TrialResult.COUNTDOWN, fixture.session.viewState.result)
        fixture.session.onTick(52_000_000_000L)
        assertEquals(TrialResult.FIGHTING, fixture.session.viewState.result)
        assertNull(fixture.session.viewState.pauseReason)
    }

    @Test fun wrongRoundOrStaleGenerationCannotHideTheActiveScene() {
        val fixture = Fixture()
        val before = fixture.session.viewState
        assertFalse(fixture.session.beginOpponentChange(before.roundGeneration + 1L, before.roundNumber))
        assertFalse(fixture.session.beginOpponentChange(before.roundGeneration, before.roundNumber + 1))
        assertEquals(before, fixture.session.viewState)
    }

    @Test fun restartInvalidatesAnOldLoadingRequestAndReturnsToTheFirstOpponent() {
        val fixture = Fixture()
        val before = fixture.session.viewState
        assertTrue(fixture.session.beginOpponentChange(before.roundGeneration, before.roundNumber))
        fixture.discontinue(DiscontinuityReason.ROUND_RESET)
        val reset = fixture.session.viewState
        assertEquals(before.roundGeneration + 1L, reset.roundGeneration)
        assertEquals(1, reset.roundNumber)
        assertEquals(TrialResult.READY, reset.result)
        assertFalse(fixture.session.beginOpponentChange(before.roundGeneration, before.roundNumber))
        assertTrue(fixture.session.beginOpponentChange(reset.roundGeneration, reset.roundNumber))
        fixture.session.setEnemyGeometry(fixture.spawn, 1.55)
        fixture.observe()
        assertTrue(fixture.session.startTrial())
    }

    @Test fun expectedReplacementNeverClearsARealUserPause() {
        val fixture = Fixture()
        assertTrue(fixture.session.startTrial())
        fixture.discontinue(DiscontinuityReason.USER_PAUSED)
        val before = fixture.session.viewState
        val pauseId = requireNotNull(before.pauseId)
        assertEquals(PauseReason.USER, before.pauseReason)
        assertTrue(fixture.session.beginOpponentChange(before.roundGeneration, before.roundNumber))
        fixture.session.setEnemyGeometry(fixture.spawn, 1.55)
        fixture.observe()
        assertEquals(PauseReason.USER, fixture.session.viewState.pauseReason)
        assertEquals(pauseId, fixture.session.viewState.pauseId)
        assertTrue(fixture.session.confirmResume(pauseId))
    }

    @Test fun unexpectedSceneLossStillRequiresTrackingRecovery() {
        val fixture = Fixture()
        assertTrue(fixture.session.startTrial())
        fixture.session.onTick(0L)
        fixture.session.onTick(3_000_000_000L)
        assertEquals(TrialResult.FIGHTING, fixture.session.viewState.result)
        fixture.session.setEnemyGeometry(null, 0.0)
        assertEquals(PauseReason.TRACKING_INTERRUPTION, fixture.session.viewState.pauseReason)
        fixture.session.setEnemyGeometry(fixture.spawn, 1.55)
        fixture.observe()
        assertEquals(PauseReason.TRACKING_INTERRUPTION, fixture.session.viewState.pauseReason)
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val spawn = Vector3(0.0, 0.028, -1.3)
        private val tracking = TrackingState(Hand.RIGHT)
        private var sequence = 0L
        private var receipt = 1L
        private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

        init {
            session.setEnemyGeometry(spawn, 1.55)
            observe()
        }

        fun observe() {
            accept(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, 1.6, 0.0), rotation)))
            accept(TrackingEvent.Controllers(stamp(),
                ObservedPose(Vector3(-0.25, 1.2, -0.35), rotation),
                ObservedPose(Vector3(0.25, 1.2, -0.35), rotation)))
        }

        fun discontinue(reason: DiscontinuityReason) =
            accept(TrackingEvent.Discontinuity(stamp(), TrackingTarget.ALL, reason))

        private fun stamp() = ObservationStamp(sequence++, receipt++, 1L, InputOrigin.PICO)

        private fun accept(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }
    }
}
