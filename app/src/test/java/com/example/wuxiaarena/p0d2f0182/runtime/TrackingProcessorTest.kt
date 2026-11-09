package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import java.util.concurrent.atomic.AtomicLong
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TrackingProcessorTest {
    private val pose = ObservedPose(Vector3(0.0, 1.6, -0.3), Quaternion(0.0, 0.0, 0.0, 1.0))

    @Test
    fun deliversOrderedObservationsWithTheirIntermediateReadiness() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(8) { clock.getAndIncrement() }
        val processor = TrackingProcessor()
        val observed = mutableListOf<Pair<Long, Boolean>>()
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.offerControllers(InputOrigin.PICO, null, pose)

        processor.process(buffer.drain()) { event, accepted, snapshot ->
            assertTrue(accepted)
            observed += event.stamp.sequence to snapshot.hasRequiredObservations
        }

        assertEquals(listOf(0L to false, 1L to true), observed)
    }

    @Test
    fun trackingLossRequiresNewHeadAndDominantHandObservations() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(8) { clock.getAndIncrement() }
        val processor = TrackingProcessor()
        val readiness = mutableListOf<Boolean>()
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.offerControllers(InputOrigin.PICO, null, pose)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        buffer.offerHead(InputOrigin.PICO, pose)
        buffer.offerControllers(InputOrigin.PICO, null, pose)

        processor.process(buffer.drain()) { _, accepted, snapshot ->
            assertTrue(accepted)
            readiness += snapshot.hasRequiredObservations
        }

        assertEquals(listOf(false, true, false, false, true), readiness)
    }

    @Test
    fun overflowIsDeliveredAsAGapBeforeAnyNewObservation() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(1) { clock.getAndIncrement() }
        val processor = TrackingProcessor()
        buffer.offerHead(InputOrigin.PICO, pose)
        assertFalse(buffer.offerControllers(InputOrigin.PICO, null, pose))
        val batch = buffer.drain()
        val delivered = mutableListOf<TrackingEvent>()

        processor.process(batch) { event, accepted, snapshot ->
            assertTrue(accepted)
            assertFalse(snapshot.hasRequiredObservations)
            delivered += event
        }

        assertEquals(2L, batch.droppedEvents)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (delivered.single() as TrackingEvent.Discontinuity).reason)
    }
}
