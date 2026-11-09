package com.example.wuxiaarena.core.input

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TrackingStateTest {
    private val pose = ObservedPose(Vector3(0.0, 1.0, -0.5), Quaternion(0.0, 0.0, 0.0, 1.0))

    private fun stamp(sequence: Long, time: Long = sequence, epoch: Long = 0, origin: InputOrigin = InputOrigin.PICO) =
        ObservationStamp(sequence, time, epoch, origin)

    @Test
    fun unknownQualityCanBeObservedWithoutClaimingHardwareReadiness() {
        val state = TrackingState(Hand.RIGHT)
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Head(stamp(0, 10), pose))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Controllers(stamp(1, 20), null, pose))

        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(TrackingQuality.UNKNOWN, state.snapshot.right?.pose?.quality)
        assertEquals(10L, state.snapshot.head?.stamp?.receivedAtNanos)
        assertEquals(20L, state.snapshot.right?.stamp?.receivedAtNanos)
        assertNull(state.snapshot.left?.pose)
    }

    @Test
    fun nonDominantLossDoesNotResetTheDominantHand() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0), pose))
        state.accept(TrackingEvent.Controllers(stamp(1), pose, pose))
        val rightRevision = state.snapshot.rightContinuity
        state.accept(TrackingEvent.Controllers(stamp(2), null, pose))

        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(1, state.snapshot.leftContinuity)
        assertEquals(rightRevision, state.snapshot.rightContinuity)
        assertNull(state.snapshot.left?.pose)
    }

    @Test
    fun changingHandRequiresNewHandObservations() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0), pose))
        state.accept(TrackingEvent.Controllers(stamp(1), pose, pose))
        state.accept(TrackingEvent.DominantHandChanged(stamp(2), Hand.LEFT))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertNull(state.snapshot.left)
        assertNull(state.snapshot.right)
        state.accept(TrackingEvent.Controllers(stamp(3), pose, null))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Head(stamp(4), pose))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(Hand.LEFT, state.snapshot.dominantHand)
    }

    @Test
    fun aGapAndCoordinateEpochPreventConnectingOldAndNewSamples() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0), pose))
        state.accept(TrackingEvent.Controllers(stamp(1), null, pose))
        state.accept(TrackingEvent.Discontinuity(stamp(4), TrackingTarget.ALL, DiscontinuityReason.QUEUE_GAP))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertNull(state.snapshot.head)
        assertNull(state.snapshot.right)
        assertEquals(1, state.snapshot.rightContinuity)

        state.accept(TrackingEvent.Head(stamp(5, epoch = 1), pose))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Controllers(stamp(6, epoch = 1), null, pose))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertTrue(state.snapshot.rightContinuity >= 2)
    }

    @Test
    fun staleSequenceIsIgnoredAndRegressingTimeInvalidatesHistory() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0, 10), pose))
        state.accept(TrackingEvent.Controllers(stamp(1, 20), null, pose))
        assertFalse(state.accept(TrackingEvent.Head(stamp(1, 30), null)))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertFalse(state.accept(TrackingEvent.Head(stamp(2, 19), pose)))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertNull(state.snapshot.head)
        assertNull(state.snapshot.right)
    }

    @Test
    fun recoveryNeedsBothRequiredSourcesObservedAfterTheInterruption() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0), pose))
        state.accept(TrackingEvent.Controllers(stamp(1), null, pose))
        assertTrue(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Discontinuity(stamp(2), TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE))
        state.accept(TrackingEvent.Head(stamp(3), pose))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Controllers(stamp(4), null, pose))
        assertTrue(state.snapshot.hasRequiredObservations)
    }

    @Test
    fun anOutOfOrderOlderEventInvalidatesTheCurrentBaseline() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0), pose))
        state.accept(TrackingEvent.Controllers(stamp(1), null, pose))
        state.accept(TrackingEvent.Head(stamp(2), pose))
        assertFalse(state.accept(TrackingEvent.Head(stamp(0), pose)))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertNull(state.snapshot.head)
        assertNull(state.snapshot.right)
    }

    @Test
    fun partialOrInvalidRequiredPoseCannotBeTreatedAsPresent() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0), pose.copy(rotation = null)))
        state.accept(TrackingEvent.Controllers(stamp(1), null, pose.copy(rotation = Quaternion(0.0, 0.0, 0.0, 0.0))))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Controllers(stamp(2), null, pose.copy(quality = TrackingQuality.SOURCE_REPORTED_INVALID)))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Controllers(stamp(3), null, pose))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Head(stamp(4), pose.copy(rotation = null)))
        assertTrue(state.snapshot.hasRequiredObservations)
    }

    @Test
    fun aRealZeroPositionIsNotMistakenForAnInitialPlaceholder() {
        val zero = pose.copy(position = Vector3(0.0, 0.0, 0.0))
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0, 0), zero))
        state.accept(TrackingEvent.Controllers(stamp(1, 0), null, zero))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(TrackingQuality.UNKNOWN, state.snapshot.head?.pose?.quality)
    }

    @Test
    fun mixedSourceObservationsRetainIndependentReceiptTimes() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0, 10, origin = InputOrigin.PICO), pose))
        state.accept(TrackingEvent.Controllers(stamp(1, 20, origin = InputOrigin.DESKTOP), null, pose))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(InputOrigin.PICO, state.snapshot.head?.stamp?.origin)
        assertEquals(InputOrigin.DESKTOP, state.snapshot.right?.stamp?.origin)
        assertEquals(10L, state.snapshot.head?.stamp?.receivedAtNanos)
    }

    @Test
    fun switchingTheRequiredSourceNeedsFreshSamplesFromBothSources() {
        val state = TrackingState(Hand.RIGHT)
        state.accept(TrackingEvent.Head(stamp(0, origin = InputOrigin.PICO), pose))
        state.accept(TrackingEvent.Controllers(stamp(1, origin = InputOrigin.PICO), null, pose))
        state.accept(TrackingEvent.Controllers(stamp(2, origin = InputOrigin.DESKTOP), null, pose))
        assertFalse(state.snapshot.hasRequiredObservations)
        state.accept(TrackingEvent.Head(stamp(3, origin = InputOrigin.PICO), pose))
        assertTrue(state.snapshot.hasRequiredObservations)
    }
}
