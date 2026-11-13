package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ArenaPresentationProvenanceTest {
    @Test fun observationsAndTheFollowingTickCarryTheActualUiBatchAndHandReceipt() {
        val states = mutableListOf<ArenaViewState>()
        val arena = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        arena.setArenaPresenter { state, _ -> states += state }
        assertEquals("presenter_bind", states.last().diagnosticPublishSource)
        assertNull(states.last().diagnosticUiFrameNanos)
        val tracking = TrackingState(Hand.RIGHT)
        val head = TrackingEvent.Head(ObservationStamp(1, 1_000, 0, InputOrigin.DESKTOP),
            ObservedPose(Vector3(0.0, 1.65, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0)))
        val handStamp = ObservationStamp(2, 2_000, 0, InputOrigin.DESKTOP)
        val hands = TrackingEvent.Controllers(handStamp, null,
            ObservedPose(Vector3(0.2, 1.3, -0.4), Quaternion(0.0, 0.0, 0.0, 1.0)))
        // These are the exact callback shapes used by Main's existing method references.
        val observe: (TrackingEvent, Boolean, com.example.wuxiaarena.core.input.TrackingSnapshot, Long?) -> Unit = arena::onTrackingEvent
        val tick: (Long, Long?) -> Unit = arena::onTick
        for (event in listOf(head, hands)) {
            observe(event, tracking.accept(event), tracking.snapshot, 9_000)
        }
        assertEquals("tracking_controllers", states.last().diagnosticPublishSource)
        assertEquals(9_000L, states.last().diagnosticUiFrameNanos)
        assertEquals(handStamp, states.last().diagnosticHandStamp)
        tick(10_000, 9_000)
        assertEquals("tick", states.last().diagnosticPublishSource)
        assertEquals(9_000L, states.last().diagnosticUiFrameNanos)
        assertEquals(handStamp, states.last().diagnosticHandStamp)
        // A new head receipt retains the real preceding hand stamp rather than inventing one.
        val nextHead = TrackingEvent.Head(ObservationStamp(3, 11_000, 0, InputOrigin.DESKTOP), head.pose)
        arena.onTrackingEvent(nextHead, tracking.accept(nextHead), tracking.snapshot, uiFrameNanos = 12_000)
        assertEquals("tracking_head", states.last().diagnosticPublishSource)
        assertEquals(handStamp, states.last().diagnosticHandStamp)
    }

    @Test fun AUiBatchIsNeverRetainedByLaterSceneCallsOrDirectSnapshots() {
        val states = mutableListOf<ArenaViewState>()
        val arena = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        arena.setArenaPresenter { state, _ -> states += state }
        arena.onTick(100, uiFrameNanos = 90)
        assertEquals(90L, states.last().diagnosticUiFrameNanos)
        assertNull(arena.viewState.diagnosticUiFrameNanos)
        assertEquals("snapshot", arena.viewState.diagnosticPublishSource)
        assertTrue(arena.beginOpponentChange(0, 1))
        assertEquals("opponent_change", states.last().diagnosticPublishSource)
        assertNull(states.last().diagnosticUiFrameNanos)
        arena.onTick(200)
        assertEquals("tick", states.last().diagnosticPublishSource)
        assertNull(states.last().diagnosticUiFrameNanos)
        arena.setEnemyGeometry(Vector3(0.0, 0.028, -2.4), 1.55)
        assertEquals("enemy_geometry", states.last().diagnosticPublishSource)
        assertNull(states.last().diagnosticUiFrameNanos)
    }
}
