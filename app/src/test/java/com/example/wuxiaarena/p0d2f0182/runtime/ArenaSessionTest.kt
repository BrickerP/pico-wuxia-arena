package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
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
import org.junit.Assert.assertTrue
import org.junit.Test

class ArenaSessionTest {
    private val headPose = ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))
    private val leftPose = ObservedPose(Vector3(-0.25, 1.2, -0.35), Quaternion(0.0, 0.0, 0.0, 1.0))
    private val rightPose = ObservedPose(Vector3(0.25, 1.2, -0.35), Quaternion(0.0, 0.0, 0.0, 1.0))
    private val headEvent = TrackingEvent.Head(ObservationStamp(0, 10, 1, InputOrigin.PICO), headPose)
    private val handEvent = TrackingEvent.Controllers(ObservationStamp(1, 20, 1, InputOrigin.PICO), leftPose, rightPose)

    @Test
    fun latePresenterImmediatelyReceivesCurrentDominantHandPose() {
        val state = TrackingState(Hand.LEFT)
        val session = ArenaSession(logMessage = {})
        for (event in listOf(headEvent, handEvent)) {
            val accepted = state.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, state.snapshot)
        }
        assertTrue(state.snapshot.hasRequiredObservations)

        val presented = mutableListOf<ObservedPose?>()
        session.setPlayerHandPresenter { presented += it }

        assertEquals(listOf(leftPose), presented)
    }

    @Test
    fun presenterRegisteredAfterTrackingLossDoesNotReplayOldPose() {
        val interruptions = listOf(
            TrackingEvent.Discontinuity(
                ObservationStamp(2, 30, 1, InputOrigin.PICO),
                TrackingTarget.ALL,
                DiscontinuityReason.APP_PAUSED,
            ),
            TrackingEvent.Discontinuity(
                ObservationStamp(2, 30, 1, InputOrigin.PICO),
                TrackingTarget.HEAD,
                DiscontinuityReason.PROVIDER_UNAVAILABLE,
            ),
            TrackingEvent.Discontinuity(
                ObservationStamp(2, 30, 2, InputOrigin.PICO),
                TrackingTarget.ALL,
                DiscontinuityReason.RECENTERED,
            ),
            TrackingEvent.Head(ObservationStamp(2, 19, 1, InputOrigin.PICO), headPose),
            TrackingEvent.Head(ObservationStamp(2, 30, 0, InputOrigin.PICO), headPose),
        )
        for (interruption in interruptions) {
            val state = TrackingState(Hand.RIGHT)
            val session = ArenaSession(logMessage = {})
            for (event in listOf(headEvent, handEvent)) {
                val accepted = state.accept(event)
                assertTrue(accepted)
                session.onTrackingEvent(event, accepted, state.snapshot)
            }
            val originalPresenter = mutableListOf<ObservedPose?>()
            session.setPlayerHandPresenter { originalPresenter += it }
            assertEquals(listOf(rightPose), originalPresenter)

            val accepted = state.accept(interruption)
            session.onTrackingEvent(interruption, accepted, state.snapshot)
            assertFalse(state.snapshot.hasRequiredObservations)
            assertEquals(listOf(rightPose, null), originalPresenter)
            session.setPlayerHandPresenter(null)

            val newPresenter = mutableListOf<ObservedPose?>()
            session.setPlayerHandPresenter { newPresenter += it }

            assertEquals(listOf<ObservedPose?>(null), newPresenter)

            val newHandEvent = TrackingEvent.Controllers(
                ObservationStamp(3, 40, 2, InputOrigin.PICO), leftPose, rightPose,
            )
            val acceptedHand = state.accept(newHandEvent)
            session.onTrackingEvent(newHandEvent, acceptedHand, state.snapshot)
            assertFalse(state.snapshot.hasRequiredObservations)
            assertEquals(listOf<ObservedPose?>(null, null), newPresenter)

            val newHeadEvent = TrackingEvent.Head(ObservationStamp(4, 50, 2, InputOrigin.PICO), headPose)
            val acceptedHead = state.accept(newHeadEvent)
            session.onTrackingEvent(newHeadEvent, acceptedHead, state.snapshot)
            assertTrue(state.snapshot.hasRequiredObservations)
            assertEquals(listOf(null, null, rightPose), newPresenter)
        }
    }

    @Test
    fun trialStartPublishesPhasesAndLatePresenterReceivesOnlyCurrentState() {
        val state = TrackingState(Hand.RIGHT)
        val session = ArenaSession(logMessage = {})
        session.setEnemyGeometry(Vector3(0.0, 0.0, -1.0), 2.0)
        for (event in listOf(headEvent, handEvent)) {
            val accepted = state.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, state.snapshot)
        }
        assertTrue(session.viewState.inputReady)
        assertTrue(session.viewState.actionReady)
        assertFalse(session.viewState.trialStarted)
        session.onTick(1_000_000_000L)
        session.onTick(2_000_000_000L)
        assertEquals(0L, session.viewState.simulationNanos)

        val presentations = mutableListOf<Pair<ArenaViewState, List<EnemyCombatEvent>>>()
        session.setArenaPresenter { view, events -> presentations += view to events }
        assertTrue(session.startTrial())
        assertTrue(session.viewState.trialStarted)
        assertEquals(TrialResult.COUNTDOWN, session.viewState.result)
        session.onTick(3_000_000_000L)
        assertEquals(0L, session.viewState.simulationNanos)
        session.onTick(3_800_000_000L)
        assertEquals(TrialResult.COUNTDOWN, session.viewState.result)
        assertEquals(0L, session.viewState.simulationNanos)
        assertEquals(null, session.viewState.attackId)
        session.onTick(6_000_000_000L)
        assertEquals(TrialResult.FIGHTING, session.viewState.result)
        assertEquals(0L, session.viewState.simulationNanos)
        val attackStartedAt = 6_800_000_000L
        session.onTick(attackStartedAt)
        val preparing = session.viewState
        val attackId = requireNotNull(preparing.attackId)
        assertEquals(EnemyPhase.PREPARING, preparing.phase)
        assertEquals(AttackDirection.OVERHEAD, preparing.attackDirection)
        assertEquals(800_000_000L, preparing.simulationNanos)
        assertEquals(0L, preparing.phaseElapsedNanos)
        assertEquals(AttackDirection.OVERHEAD.preparationNanos, preparing.phaseRemainingNanos)
        assertEquals(preparing, presentations.last().first)
        assertEquals(
            listOf(
                EnemyCombatEvent.AttackStarted(attackId, AttackDirection.OVERHEAD, false, preparing.simulationNanos),
                EnemyCombatEvent.PhaseChanged(EnemyPhase.IDLE, EnemyPhase.PREPARING, preparing.simulationNanos),
            ),
            presentations.last().second,
        )
        assertFalse(session.startTrial())
        assertEquals(preparing, session.viewState)

        val replay = mutableListOf<Pair<ArenaViewState, List<EnemyCombatEvent>>>()
        session.setArenaPresenter { view, events -> replay += view to events }
        assertEquals(preparing, replay.single().first)
        assertTrue(replay.single().second.isEmpty())
        session.onTick(attackStartedAt + AttackDirection.OVERHEAD.preparationNanos)
        assertEquals(EnemyPhase.STARTUP, replay.last().first.phase)
        assertEquals(attackId, replay.last().first.attackId)
        assertEquals(
            listOf(
                EnemyCombatEvent.PhaseChanged(
                    EnemyPhase.PREPARING, EnemyPhase.STARTUP, session.viewState.simulationNanos,
                ),
            ),
            replay.last().second,
        )
    }

    @Test
    fun userPauseRequiresFreshObservationsAndCurrentConfirmationWithoutClockCatchUp() {
        val state = TrackingState(Hand.RIGHT)
        val session = ArenaSession(logMessage = {})
        session.setEnemyGeometry(Vector3(0.0, 0.0, -1.0), 2.0)
        for (event in listOf(headEvent, handEvent)) {
            val accepted = state.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, state.snapshot)
        }
        val events = mutableListOf<EnemyCombatEvent>()
        session.setArenaPresenter { _, batch -> events.addAll(batch) }
        assertTrue(session.startTrial())
        session.onTick(1_000_000_000L)
        session.onTick(4_000_000_000L)
        assertEquals(TrialResult.FIGHTING, session.viewState.result)
        assertEquals(0L, session.viewState.simulationNanos)
        session.onTick(4_800_000_000L)
        session.onTick(4_900_000_000L)
        val beforePause = session.viewState
        assertEquals(EnemyPhase.PREPARING, beforePause.phase)

        val pause = TrackingEvent.Discontinuity(
            ObservationStamp(2, 4_900_000_001L, 1, InputOrigin.PICO),
            TrackingTarget.ALL,
            DiscontinuityReason.USER_PAUSED,
        )
        assertTrue(state.accept(pause))
        session.onTrackingEvent(pause, true, state.snapshot)
        val pauseId = requireNotNull(session.viewState.pauseId)
        assertEquals(PauseReason.USER, session.viewState.pauseReason)
        assertFalse(session.viewState.inputReady)
        assertFalse(session.viewState.resumeReady)
        assertFalse(session.confirmResume(pauseId))
        session.onTick(50_000_000_000L)
        assertEquals(beforePause.simulationNanos, session.viewState.simulationNanos)

        val newHand = handEvent.copy(stamp = ObservationStamp(3, 50_000_000_001L, 1, InputOrigin.PICO))
        assertTrue(state.accept(newHand))
        session.onTrackingEvent(newHand, true, state.snapshot)
        assertFalse(session.viewState.resumeReady)
        assertFalse(session.confirmResume(pauseId))
        val newHead = headEvent.copy(stamp = ObservationStamp(4, 50_000_000_002L, 1, InputOrigin.PICO))
        assertTrue(state.accept(newHead))
        session.onTrackingEvent(newHead, true, state.snapshot)
        assertTrue(session.viewState.inputReady)
        assertTrue(session.viewState.actionReady)
        assertTrue(session.viewState.resumeReady)
        assertEquals(PauseReason.USER, session.viewState.pauseReason)
        assertEquals(pauseId, session.viewState.pauseId)
        assertFalse(session.confirmResume(pauseId + 1))
        assertEquals(PauseReason.USER, session.viewState.pauseReason)
        assertTrue(session.confirmResume(pauseId))
        assertEquals(null, session.viewState.pauseReason)
        assertFalse(session.confirmResume(pauseId))

        session.onTick(100_000_000_000L)
        assertEquals(beforePause.simulationNanos, session.viewState.simulationNanos)
        assertEquals(beforePause.phaseElapsedNanos, session.viewState.phaseElapsedNanos)
        session.onTick(100_100_000_000L)
        assertEquals(beforePause.simulationNanos + 100_000_000L, session.viewState.simulationNanos)
        assertEquals(beforePause.phaseElapsedNanos + 100_000_000L, session.viewState.phaseElapsedNanos)
        assertEquals(beforePause.attackId, session.viewState.attackId)
        assertEquals(
            listOf(
                EnemyCombatEvent.PauseChanged(null, PauseReason.USER, pauseId, beforePause.simulationNanos),
                EnemyCombatEvent.PauseChanged(PauseReason.USER, null, pauseId, beforePause.simulationNanos),
            ),
            events.filterIsInstance<EnemyCombatEvent.PauseChanged>(),
        )
    }

    @Test
    fun presenterFailuresPreserveCausesWithoutReplayingResetOrBlockingProgress() {
        val state = TrackingState(Hand.RIGHT)
        val failures = mutableListOf<Pair<String, Throwable>>()
        val session = ArenaSession(
            logMessage = {},
            logFailure = { context, error -> failures += context to error },
        )
        session.setEnemyGeometry(Vector3(0.0, 0.0, -1.0), 2.0)
        for (event in listOf(headEvent, handEvent)) {
            val accepted = state.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, state.snapshot)
        }
        val handCause = IllegalArgumentException("hand resource unavailable")
        val handFailure = IllegalStateException("hand presenter failed", handCause)
        val arenaCause = IllegalArgumentException("arena resource unavailable")
        val arenaFailure = IllegalStateException("arena presenter failed", arenaCause)
        var failNextHandPresentation = false
        session.setPlayerHandPresenter {
            if (failNextHandPresentation) {
                failNextHandPresentation = false
                throw handFailure
            }
        }
        val events = mutableListOf<EnemyCombatEvent>()
        session.setArenaPresenter { _, batch ->
            events.addAll(batch)
            if (batch.any { it is EnemyCombatEvent.RoundReset }) throw arenaFailure
        }
        assertTrue(session.startTrial())
        val generationBeforeReset = session.viewState.roundGeneration

        val reset = TrackingEvent.Discontinuity(
            ObservationStamp(2, 30, 2, InputOrigin.PICO),
            TrackingTarget.ALL,
            DiscontinuityReason.ROUND_RESET,
        )
        failNextHandPresentation = true
        assertTrue(state.accept(reset))
        session.onTrackingEvent(reset, true, state.snapshot)
        assertEquals(generationBeforeReset + 1, session.viewState.roundGeneration)
        assertFalse(session.viewState.trialStarted)
        assertFalse(session.viewState.inputReady)
        assertEquals(0L, session.viewState.simulationNanos)
        assertEquals(
            listOf("Player-hand presentation failed", "Arena presentation failed"),
            failures.map { it.first },
        )
        assertTrue(failures[0].second === handFailure)
        assertTrue(failures[0].second.cause === handCause)
        assertTrue(failures[1].second === arenaFailure)
        assertTrue(failures[1].second.cause === arenaCause)

        val newHead = headEvent.copy(stamp = ObservationStamp(3, 40, 2, InputOrigin.PICO))
        val newHands = handEvent.copy(stamp = ObservationStamp(4, 50, 2, InputOrigin.PICO))
        for (event in listOf(newHead, newHands)) {
            val accepted = state.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, state.snapshot)
        }
        assertTrue(session.startTrial())
        session.onTick(1_000_000_000L)
        session.onTick(4_000_000_000L)
        assertEquals(TrialResult.FIGHTING, session.viewState.result)
        assertEquals(0L, session.viewState.simulationNanos)
        session.onTick(4_800_000_000L)
        assertEquals(EnemyPhase.PREPARING, session.viewState.phase)
        assertEquals(800_000_000L, session.viewState.simulationNanos)
        assertEquals(generationBeforeReset + 1, session.viewState.roundGeneration)
        assertEquals(1, events.filterIsInstance<EnemyCombatEvent.RoundReset>().size)
        assertEquals(1, events.filterIsInstance<EnemyCombatEvent.AttackStarted>().size)
        assertEquals(2, failures.size)
    }
}
