package com.example.wuxiaarena.integration

import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingBatch
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import java.util.concurrent.atomic.AtomicLong
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/** Synthetic input-boundary regressions; these do not exercise a device or combat scene. */
class TrackingPipelineRegressionTest {
    private val head = ObservedPose(Vector3(0.0, 1.60, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))
    private val left = ObservedPose(Vector3(-0.20, 1.25, -0.35), Quaternion(0.0, 0.0, 0.0, 1.0))
    private val right = ObservedPose(Vector3(0.25, 1.25, -0.35), Quaternion(0.0, 0.0, 0.0, 1.0))

    @Test
    fun coalescedControllerBurstCannotTurnATrackingTeleportIntoAStrike() {
        val receipts = ArrayDeque(listOf(0L, 1L, 100_000_000L, 100_050_000L, 120_000_000L))
        val buffer = TrackingEventBuffer(capacity = 8) { receipts.removeFirst() }
        val state = TrackingState(Hand.RIGHT)
        val resolver = PlayerCombatResolver()
        val enemy = Vector3(2.0, 0.0, -0.8)
        assertTrue(buffer.offerHead(InputOrigin.DESKTOP, head))
        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, right.copy(position = Vector3(0.0, 1.25, -0.35))))
        accept(state, buffer.drain())
        val baseline = requireNotNull(resolver.observe(state.snapshot, enemy))

        val teleported = right.copy(position = Vector3(4.0, 1.25, -0.35))
        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, right.copy(position = Vector3(0.0, 1.25, -0.35))))
        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, teleported))
        val burst = buffer.drain()
        assertEquals(1, burst.events.size)
        accept(state, burst)
        val rejected = requireNotNull(resolver.observe(state.snapshot, enemy))
        assertTrue(rejected.motionGeneration > baseline.motionGeneration)
        assertNull(rejected.strike)

        assertTrue(buffer.offerControllers(InputOrigin.DESKTOP, null, teleported))
        accept(state, buffer.drain())
        val stable = requireNotNull(resolver.observe(state.snapshot, enemy))
        assertEquals(rejected.motionGeneration, stable.motionGeneration)
        assertEquals(0.0, stable.bladeTipSpeed, 0.0)
        assertNull(stable.strike)
    }

    @Test
    fun saturatedControlsPreserveResetAndRequireFreshSelectedHandBeforeObservingReady() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(capacity = 1) { clock.getAndIncrement() }
        val state = TrackingState(Hand.RIGHT)

        assertTrue(buffer.offerHead(InputOrigin.PICO, head))
        assertFalse(buffer.offerControllers(InputOrigin.PICO, left, right))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        assertThrows(IllegalStateException::class.java) {
            buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        }

        val first = buffer.drain()
        assertEquals(2L, first.droppedEvents)
        assertEquals(
            listOf(
                DiscontinuityReason.QUEUE_GAP,
                DiscontinuityReason.ROUND_RESET,
                DiscontinuityReason.PROVIDER_UNAVAILABLE,
            ),
            first.events.map { (it as TrackingEvent.Discontinuity).reason },
        )
        assertEquals(listOf(0L, 1L, 1L), first.events.map { it.stamp.coordinateEpoch })
        accept(state, first)
        assertFalse(state.snapshot.hasRequiredObservations)

        // A pose arriving before the rejected hand-change is retried must not pass it.
        assertFalse(buffer.offerHead(InputOrigin.PICO, head))
        buffer.changeDominantHand(InputOrigin.PICO, Hand.LEFT)
        val retry = buffer.drain()
        assertEquals(1L, retry.droppedEvents)
        assertEquals(DiscontinuityReason.QUEUE_GAP, (retry.events[0] as TrackingEvent.Discontinuity).reason)
        assertEquals(Hand.LEFT, (retry.events[1] as TrackingEvent.DominantHandChanged).hand)
        accept(state, retry)
        assertEquals(Hand.LEFT, state.snapshot.dominantHand)
        assertFalse(state.snapshot.hasRequiredObservations)

        assertTrue(buffer.offerHead(InputOrigin.PICO, head))
        accept(state, buffer.drain())
        assertFalse(state.snapshot.hasRequiredObservations)
        assertTrue(buffer.offerControllers(InputOrigin.PICO, left, null))
        accept(state, buffer.drain())

        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(1L, requireNotNull(state.snapshot.head).stamp.coordinateEpoch)
        assertEquals(1L, requireNotNull(state.snapshot.left).stamp.coordinateEpoch)
        assertEquals(TrackingQuality.UNKNOWN, requireNotNull(state.snapshot.left?.pose).quality)
        assertNull(state.snapshot.right?.pose)
    }

    @Test
    fun resetBeforeOverflowStaysBeforeGapAndRecoveryNeedsBothSources() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(capacity = 2) { clock.getAndIncrement() }
        val state = TrackingState(Hand.RIGHT)

        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET)
        assertTrue(buffer.offerHead(InputOrigin.PICO, head))
        assertFalse(buffer.offerControllers(InputOrigin.PICO, null, right))
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)

        val batch = buffer.drain()
        assertEquals(
            listOf(
                DiscontinuityReason.ROUND_RESET,
                DiscontinuityReason.QUEUE_GAP,
                DiscontinuityReason.PROVIDER_UNAVAILABLE,
            ),
            batch.events.map { (it as TrackingEvent.Discontinuity).reason },
        )
        assertEquals(listOf(0L, 2L, 3L), batch.events.map { it.stamp.sequence })
        assertEquals(2L, batch.droppedEvents)
        accept(state, batch)
        assertFalse(state.snapshot.hasRequiredObservations)

        assertTrue(buffer.offerHead(InputOrigin.PICO, head))
        accept(state, buffer.drain())
        assertFalse(state.snapshot.hasRequiredObservations)
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, right))
        accept(state, buffer.drain())
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(1L, requireNotNull(state.snapshot.right).stamp.coordinateEpoch)
        assertEquals(TrackingQuality.UNKNOWN, requireNotNull(state.snapshot.right?.pose).quality)
    }

    @Test
    fun oldEpochReplayCannotRestoreTheRecenteredState() {
        val clock = AtomicLong()
        val buffer = TrackingEventBuffer(capacity = 8) { clock.getAndIncrement() }
        val state = TrackingState(Hand.RIGHT)

        assertTrue(buffer.offerHead(InputOrigin.PICO, head))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, right))
        accept(state, buffer.drain())
        assertTrue(state.snapshot.hasRequiredObservations)

        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.RECENTERED)
        assertTrue(buffer.offerHead(InputOrigin.PICO, head))
        assertTrue(buffer.offerControllers(InputOrigin.PICO, null, right))
        accept(state, buffer.drain())
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(1L, requireNotNull(state.snapshot.head).stamp.coordinateEpoch)

        // Replay is deliberately injected at the public consumer boundary; its sequence
        // remains increasing while its coordinate epoch is stale.
        assertFalse(state.accept(TrackingEvent.Head(stamp(5, 0), head)))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertFalse(state.accept(TrackingEvent.Controllers(stamp(6, 0), null, right)))
        assertFalse(state.snapshot.hasRequiredObservations)

        assertTrue(state.accept(TrackingEvent.Head(stamp(7, 1), head)))
        assertFalse(state.snapshot.hasRequiredObservations)
        assertTrue(state.accept(TrackingEvent.Controllers(stamp(8, 1), null, right)))
        assertTrue(state.snapshot.hasRequiredObservations)
        assertEquals(1L, requireNotNull(state.snapshot.head).stamp.coordinateEpoch)
        assertEquals(1L, requireNotNull(state.snapshot.right).stamp.coordinateEpoch)
        assertEquals(TrackingQuality.UNKNOWN, requireNotNull(state.snapshot.right?.pose).quality)
    }

    private fun stamp(sequence: Long, epoch: Long) =
        ObservationStamp(sequence, sequence, epoch, InputOrigin.PICO)

    private fun accept(state: TrackingState, batch: TrackingBatch) {
        for (event in batch.events) {
            assertTrue("rejected ordered event: $event", state.accept(event))
        }
    }
}
