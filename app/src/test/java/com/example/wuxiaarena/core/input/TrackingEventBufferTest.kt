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
    fun keepsEveryReceivedSampleInOrderBetweenConsumerFrames() {
        val clock = AtomicLong(10)
        val buffer = TrackingEventBuffer(8) { clock.getAndIncrement() }
        assertTrue(buffer.offerHead(InputOrigin.PICO, pose))
        repeat(5) { assertTrue(buffer.offerControllers(InputOrigin.PICO, null, pose)) }

        val batch = buffer.drain()
        assertEquals(0, batch.droppedEvents)
        assertEquals((0L..5L).toList(), batch.events.map { it.stamp.sequence })
        assertEquals((10L..15L).toList(), batch.events.map { it.stamp.receivedAtNanos })
        assertEquals(5, batch.events.count { it is TrackingEvent.Controllers })
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
    fun overflowRetainsTheLatestHandSelectionFromDiscardedEvents() {
        val clock = AtomicLong(0)
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        assertFalse(buffer.offerHead(InputOrigin.PICO, pose))

        val batch = buffer.drain()
        val state = TrackingState(Hand.RIGHT)
        batch.events.forEach(state::accept)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (batch.events.first() as TrackingEvent.Discontinuity).reason)
        assertEquals(Hand.LEFT, state.snapshot.dominantHand)
        assertFalse(state.snapshot.hasRequiredObservations)
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
