package com.example.wuxiaarena.core.input

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Test

class TrackingEventBufferTest {
    private val pose = ObservedPose(Vector3(0.0, 1.0, -0.5), Quaternion(0.0, 0.0, 0.0, 1.0))

    @Test
    fun adjacentControllerBurstKeepsLatestPosesAndTimeAtOneSequence() {
        val clock = AtomicLong(10)
        val buffer = TrackingEventBuffer(8) { clock.getAndIncrement() }
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
        repeat(5) { index ->
            val latest = pose.copy(position = Vector3(index.toDouble(), 1.0, -0.5))
            assertTrue(buffer.offerControllers(InputOrigin.PICO, null, latest))
        }

        val batch = buffer.drain()
        assertEquals(0, batch.droppedEvents)
        assertEquals(listOf(0L, 1L), batch.events.map { it.stamp.sequence })
        assertEquals(listOf(10L, 15L), batch.events.map { it.stamp.receivedAtNanos })
        val controllers = batch.events.last() as TrackingEvent.Controllers
        assertEquals(4.0, requireNotNull(controllers.right?.position).x, 0.0)
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
        assertEquals(2L, buffer.drain().events.single().stamp.sequence)
    }

    @Test
    fun headOriginAndControlsAreHardControllerCoalescingBoundaries() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(8) { clock.getAndIncrement() }
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, pose))
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, pose))
        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, pose))
        buffer.changeDominantHand(InputOrigin.DESKTOP, Hand.LEFT)
        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, pose))
        buffer.discontinuity(InputOrigin.DESKTOP, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, pose))

        val events = buffer.drain().events
        assertEquals(8, events.size)
        assertEquals((0L..7L).toList(), events.map { it.stamp.sequence })
        assertEquals(1L, events.last().stamp.coordinateEpoch)
    }

    @Test
    fun handAvailabilityAndPoseValidityChangesAreNeverCoalesced() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(8) { clock.getAndIncrement() }
        val invalidPosition = pose.copy(position = null)
        val invalidRotation = pose.copy(rotation = Quaternion(0.0, 0.0, 0.0, 0.0))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, null))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, pose, pose))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, invalidPosition, pose))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, pose, invalidRotation))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, pose,
            pose.copy(quality = TrackingQuality.SOURCE_REPORTED_INVALID)))

        assertEquals(5, buffer.drain().events.size)
    }

    @Test
    fun coalescingChecksTheLatestReceiptClockBeforeChangingTheQueuedEvent() {
        val receipts = ArrayDeque(listOf(10L, 9L))
        val buffer = TrackingEventBuffer(2) { receipts.removeFirst() }
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, pose))

        assertThrows(IllegalStateException::class.java) {
            buffer.offerControllers(InputOrigin.PICO, null, pose)
        }

        val retained = buffer.drain().events.single() as TrackingEvent.Controllers
        assertEquals(10L, retained.stamp.receivedAtNanos)
        assertEquals(0L, retained.stamp.sequence)
    }

    @Test
    fun adjacentControllerBurstCanCoalesceAtCapacityWithoutCreatingAGap() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, pose))
        val latest = pose.copy(position = Vector3(0.4, 1.0, -0.5))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, latest))

        val batch = buffer.drain()
        assertEquals(0L, batch.droppedEvents)
        assertEquals(0L, batch.events.single().stamp.sequence)
        assertEquals(0.4, requireNotNull((batch.events.single() as TrackingEvent.Controllers).right?.position).x, 0.0)
    }

    @Test
    fun overflowReportsGapBeforeNewDataAndKeepsLatestControlState() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(2) { clock.getAndIncrement() }
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, pose))
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.APP_PAUSED)
        assertFalse(buffer.offerControllers(InputOrigin.PICO, null, pose))

        val gap = buffer.drain()
        assertEquals(4, gap.droppedEvents)
        assertEquals(3, gap.events.size)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (gap.events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(Hand.LEFT, (gap.events[1] as TrackingEvent.DominantHandChanged).hand)
        assertEquals(DiscontinuityReason.APP_PAUSED, (gap.events[2] as TrackingEvent.Discontinuity).reason)
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
        assertTrue(buffer.drain().events.single().stamp.sequence > gap.events.last().stamp.sequence)
    }

    @Test
    fun recenterDuringOverflowChangesEpochBeforeNewSamples() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.offerHead(InputOrigin.PICO, pose)
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)

        val events = buffer.drain().events
        assertEquals(DiscontinuityReason.QUEUE_GAP, (events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(1, events.last().stamp.coordinateEpoch)
        buffer.offerHead(InputOrigin.PICO, pose)
        assertEquals(1, buffer.drain().events.single().stamp.coordinateEpoch)
    }

    @Test
    fun overflowPreservesAHandSelectionBeforeTheGap() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))

        val batch = buffer.drain()
        val state = TrackingState(Hand.RIGHT)
        batch.events.forEach(state::accept)
        assertEquals(Hand.LEFT, (batch.events.first() as TrackingEvent.DominantHandChanged).hand)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (batch.events.last() as TrackingEvent.Discontinuity).reason)
        assertEquals(Hand.LEFT, state.snapshot.dominantHand)
        assertFalse(state.snapshot.hasRequiredObservations)
    }

    @Test
    fun roundResetCannotBeOverwrittenByALaterProviderFailure() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.offerHead(InputOrigin.PICO, pose)
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)

        val reasons = buffer.drain().events.filterIsInstance<TrackingEvent.Discontinuity>().map { it.reason }
        assertEquals(
            listOf(DiscontinuityReason.QUEUE_GAP, DiscontinuityReason.ROUND_RESET, DiscontinuityReason.PROVIDER_UNAVAILABLE),
            reasons,
        )
    }

    @Test
    fun resetThatCausesOverflowIsDeliveredAfterTheGap() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        val batch = buffer.drain()
        assertEquals(1, batch.droppedEvents)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (batch.events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(DiscontinuityReason.ROUND_RESET, (batch.events[1] as TrackingEvent.Discontinuity).reason)
        assertEquals(1, batch.events[1].stamp.coordinateEpoch)
    }

    @Test
    fun controlsBeforeAndAfterAResetKeepTheirOrderAcrossOverflow() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(4) { clock.getAndIncrement() }
        repeat(4) { buffer.offerHead(InputOrigin.PICO, pose) }
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.RIGHT_HAND, DiscontinuityReason.PROVIDER_UNAVAILABLE)

        val events = buffer.drain().events
        assertEquals(5, events.size)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(TrackingTarget.HEAD, (events[1] as TrackingEvent.Discontinuity).target)
        assertEquals(DiscontinuityReason.ROUND_RESET, (events[2] as TrackingEvent.Discontinuity).reason)
        assertEquals(Hand.LEFT, (events[3] as TrackingEvent.DominantHandChanged).hand)
        assertEquals(TrackingTarget.RIGHT_HAND, (events[4] as TrackingEvent.Discontinuity).target)
        assertEquals(events.map { it.stamp.sequence }.sorted(), events.map { it.stamp.sequence })
    }

    @Test
    fun repeatedTrackingFailuresOnBothSidesOfResetAreNotCoalesced() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(3) { clock.getAndIncrement() }
        repeat(4) { buffer.offerHead(InputOrigin.PICO, pose) }
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        val reasons = buffer.drain().events.filterIsInstance<TrackingEvent.Discontinuity>().map { it.reason }
        assertEquals(
            listOf(
                DiscontinuityReason.QUEUE_GAP,
                DiscontinuityReason.PROVIDER_UNAVAILABLE,
                DiscontinuityReason.ROUND_RESET,
                DiscontinuityReason.PROVIDER_UNAVAILABLE,
            ),
            reasons,
        )
    }

    @Test
    fun controlsAlreadyQueuedAreNotMovedPastTheOverflowGap() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(2) { clock.getAndIncrement() }
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)

        val events = buffer.drain().events
        assertEquals(DiscontinuityReason.ROUND_RESET, (events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(Hand.LEFT, (events[1] as TrackingEvent.DominantHandChanged).hand)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (events[2] as TrackingEvent.Discontinuity).reason)
        assertEquals(TrackingTarget.HEAD, (events[3] as TrackingEvent.Discontinuity).target)
    }

    @Test
    fun controlSaturationRejectsTheNewEventWithoutChangingItsEpoch() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        assertThrows(TrackingControlOverflowException::class.java) {
            buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        }

        val events = buffer.drain().events
        assertEquals(DiscontinuityReason.ROUND_RESET, (events[1] as TrackingEvent.Discontinuity).reason)
        assertEquals(1, events.last().stamp.coordinateEpoch)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        assertEquals(2, buffer.drain().events.single().stamp.coordinateEpoch)
    }

    @Test
    fun rejectedControlBlocksNewSamplesAndOtherControlsUntilItIsRetried() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        assertThrows(TrackingControlOverflowException::class.java) {
            buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        }
        buffer.drain()
        assertThrows(TrackingControlOverflowException::class.java) {
            buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        }
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        val retried = buffer.drain()
        assertEquals(1, retried.droppedEvents)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (retried.events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(DiscontinuityReason.RECENTERED, (retried.events[1] as TrackingEvent.Discontinuity).reason)
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        assertEquals(Hand.LEFT, (buffer.drain().events.single() as TrackingEvent.DominantHandChanged).hand)
    }

    @Test
    fun rejectedRoundResetMustBeRetriedBeforeSamplesCanResume() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        assertThrows(TrackingControlOverflowException::class.java) {
            buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        }
        assertTrue(buffer.drain().events.all { it.stamp.coordinateEpoch == 0L })
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        val retry = buffer.drain()
        assertEquals(DiscontinuityReason.QUEUE_GAP, (retry.events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(DiscontinuityReason.ROUND_RESET, (retry.events[1] as TrackingEvent.Discontinuity).reason)
        assertEquals(1, retry.events.last().stamp.coordinateEpoch)
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
    }

    @Test
    fun concurrentCallbacksReceiveOneMonotonicApplicationOrder() {
        val count = 400
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(count) { clock.getAndIncrement() }
        val start = CountDownLatch(1)
        val pool = Executors.newFixedThreadPool(4)
        try {
            val tasks = (0 until 4).map {
                pool.submit {
                    start.await()
                    repeat(100) { assertTrue(buffer.offerHead(InputOrigin.PICO, pose)) }
                }
            }
            start.countDown()
            tasks.forEach { it.get(10, TimeUnit.SECONDS) }
        } finally {
            pool.shutdownNow()
        }
        val batch = buffer.drain()
        assertEquals(0, batch.droppedEvents)
        assertEquals((0L until count.toLong()).toList(), batch.events.map { it.stamp.sequence })
        assertEquals((0L until count.toLong()).toList(), batch.events.map { it.stamp.receivedAtNanos })
    }

    @Test
    fun rejectsAnUnboundedOrBackwardsClockConfiguration() {
        assertThrows(IllegalArgumentException::class.java) { TrackingEventBuffer(0) }
        val values = ArrayDeque(listOf(10L, 9L))
        val buffer = TrackingEventBuffer(2) { values.removeFirst() }
        buffer.offerHead(InputOrigin.PICO, pose)
        assertThrows(IllegalStateException::class.java) { buffer.offerHead(InputOrigin.PICO, pose) }
    }
}
