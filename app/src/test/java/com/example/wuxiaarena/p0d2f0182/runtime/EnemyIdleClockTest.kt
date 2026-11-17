package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.EnemyPhase
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
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class EnemyIdleClockTest {
    private class Fixture(ready: Boolean = true) {
        val tracking = TrackingState(Hand.RIGHT)
        val session = ArenaSession(logMessage = {})
        private var sequence = 0L
        private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

        init {
            session.setEnemyGeometry(Vector3(0.0, .028, -2.4), 2.0)
            if (ready) observe(10L)
        }

        fun observe(at: Long) {
            deliver(TrackingEvent.Head(stamp(at), ObservedPose(Vector3(0.0, 1.65, 0.0), rotation)))
            deliver(TrackingEvent.Controllers(stamp(at + 1L),
                ObservedPose(Vector3(-.2, 1.35, -.35), rotation),
                ObservedPose(Vector3(.27, 1.4, -.45), rotation)))
        }

        fun interrupt(reason: DiscontinuityReason, at: Long) =
            deliver(TrackingEvent.Discontinuity(stamp(at), TrackingTarget.ALL, reason))

        private fun stamp(at: Long) = ObservationStamp(sequence++, at, 1L, InputOrigin.PICO)

        private fun deliver(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }
    }

    @Test
    fun readyIdleAdvancesThePresentedPoseAndContactTogetherWithoutStartingTheTrial() {
        val session = Fixture().session
        session.onTick(1_000_000_000L)
        val initial = session.viewState
        session.onTick(1_400_000_000L)
        val state = session.viewState
        assertFalse(state.trialStarted)
        assertEquals(TrialResult.READY, state.result)
        assertEquals(EnemyPhase.IDLE, state.phase)
        assertEquals(0L, state.simulationNanos)
        assertEquals(0L, state.phaseElapsedNanos)
        assertEquals(null, state.attackId)
        assertEquals("idle", state.enemyPoseClip)
        assertNotEquals(initial.enemyPoseSourceSeconds, state.enemyPoseSourceSeconds)
        assertEquals(.4, requireNotNull(state.enemyPoseSourceSeconds), 1e-9)
        val local = arenaOpponents.first().locomotionProfile().idle.sample(requireNotNull(state.enemyPoseSourceSeconds))
        val stage = local.inStage(requireNotNull(state.enemyPosition) + state.enemyRecoilOffset, state.enemyYawRadians)
        assertEquals(stage.bladeBase, state.enemyBladeBase)
        assertEquals(stage.bladeTip, state.enemyBladeTip)
    }

    @Test
    fun missingInputCannotAdvanceIdleAndTheFirstFreshTickOnlyEstablishesItsBaseline() {
        val fixture = Fixture(ready = false)
        fixture.session.onTick(1_000_000_000L)
        fixture.session.onTick(50_000_000_000L)
        assertEquals(0.0, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 0.0)
        fixture.observe(50_000_000_001L)
        fixture.session.onTick(100_000_000_000L)
        assertEquals(0.0, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 0.0)
        fixture.session.onTick(100_200_000_000L)
        assertEquals(.2, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 1e-9)
    }

    @Test
    fun readyPauseAndConfirmedResumePreserveMotionTimeWithoutResetOrCatchUp() {
        val fixture = Fixture()
        fixture.session.onTick(1_000_000_000L)
        fixture.session.onTick(1_400_000_000L)
        val before = fixture.session.viewState.enemyPoseSourceSeconds
        fixture.interrupt(DiscontinuityReason.USER_PAUSED, 1_400_000_001L)
        val pause = requireNotNull(fixture.session.viewState.pauseId)
        fixture.session.onTick(50_000_000_000L)
        assertEquals(before, fixture.session.viewState.enemyPoseSourceSeconds)
        fixture.observe(50_000_000_001L)
        assertTrue(fixture.session.confirmResume(pause))
        assertEquals(before, fixture.session.viewState.enemyPoseSourceSeconds)
        // Resume cannot rebuild physics from a 50s-old pose. Supply real accepted
        // observations just before the baseline tick; it still cannot catch up.
        fixture.observe(99_999_999_999L)
        fixture.session.onTick(100_000_000_000L)
        assertEquals(before, fixture.session.viewState.enemyPoseSourceSeconds)
        fixture.session.onTick(100_100_000_000L)
        assertEquals(.5, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 1e-9)
        assertEquals(0L, fixture.session.viewState.simulationNanos)
    }

    @Test
    fun countdownKeepsTheSameMotionClockWithoutAdvancingAttackReadiness() {
        val session = Fixture().session
        session.onTick(1_000_000_000L)
        session.onTick(1_400_000_000L)
        assertTrue(session.startTrial())
        session.onTick(2_000_000_000L)
        session.onTick(2_100_000_000L)
        assertEquals(TrialResult.COUNTDOWN, session.viewState.result)
        assertEquals(.5, requireNotNull(session.viewState.enemyPoseSourceSeconds), 1e-9)
        assertEquals(0L, session.viewState.simulationNanos)
        assertEquals(0L, session.viewState.phaseElapsedNanos)
    }

    @Test
    fun actualRetryResetsTheIdleLoopAndWaitsForNewRequiredObservations() {
        val fixture = Fixture()
        fixture.session.onTick(1_000_000_000L)
        fixture.session.onTick(1_400_000_000L)
        fixture.interrupt(DiscontinuityReason.ROUND_RESET, 1_400_000_001L)
        assertFalse(fixture.session.viewState.inputReady)
        assertEquals(0.0, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 0.0)
        fixture.session.onTick(50_000_000_000L)
        fixture.observe(50_000_000_001L)
        fixture.session.onTick(100_000_000_000L)
        assertEquals(0.0, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 0.0)
        fixture.session.onTick(100_200_000_000L)
        assertEquals(.2, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 1e-9)
    }

    @Test
    fun longReadyIntervalsRemainFiniteAndDoNotIterateTheCombatClock() {
        val session = Fixture().session
        session.onTick(1_000_000_000L)
        session.onTick(Long.MAX_VALUE)
        val state = session.viewState
        assertEquals(TrialResult.READY, state.result)
        assertEquals(0L, state.simulationNanos)
        assertTrue(requireNotNull(state.enemyPoseSourceSeconds).isFinite())
        assertTrue(requireNotNull(state.enemyPoseSourceSeconds) >= 0.0)
        assertTrue(requireNotNull(state.enemyPoseSourceSeconds) < 1.5)
        session.onTick(1L)
        assertEquals(state.enemyPoseSourceSeconds, session.viewState.enemyPoseSourceSeconds)
    }
}
