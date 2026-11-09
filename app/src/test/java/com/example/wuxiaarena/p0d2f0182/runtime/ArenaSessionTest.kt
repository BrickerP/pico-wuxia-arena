package com.example.wuxiaarena.p0d2f0182.runtime

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
}
