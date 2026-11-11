package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatAction
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ControllerActionQueueTest {
    @Test
    fun anAcceptedButtonEdgeAuthorsDesktopPosesConsumedByTheSharedStrikeRecognizer() {
        val queue = ControllerActionQueue()
        val token = queue.start()
        DesktopCombatInput.configure(true)
        DesktopCombatInput.reset()
        try {
            val baselineAt = System.nanoTime()
            queue.offer(token, false, baselineAt)
            queue.drain(baselineAt, true)
            val pressAt = System.nanoTime()
            queue.offer(token, true, pressAt)
            assertTrue(queue.drain(pressAt, true).presses.single().rightA)
            DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
            // Sampling follows trigger(), matching the Stage owner's clock ordering.
            val firstSample = System.nanoTime()
            val resolver = PlayerCombatResolver()
            val sourceHead = ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))
            var hits = 0
            for (sample in 0..33) {
                val at = firstSample + sample * 20_000_000L
                val poses = requireNotNull(DesktopCombatInput.frame(sourceHead, at))
                val stamp = ObservationStamp(sample * 2L + 1L, at, 1L, InputOrigin.DESKTOP)
                val snapshot = TrackingSnapshot(
                    PoseObservation(stamp.copy(sequence = stamp.sequence - 1L), poses.head),
                    PoseObservation(stamp, poses.left), PoseObservation(stamp, poses.right),
                    Hand.RIGHT, 0L, 0L, 0L,
                )
                if (resolver.observe(snapshot, Vector3(0.0, 0.0, -1.3))?.strike != null) hits++
            }
            assertTrue(hits > 0)
        } finally {
            DesktopCombatInput.configure(false)
        }
    }

    @Test
    fun aReleasedBaselineThenPressEmitsOneEdgeAndHoldingDoesNotRepeat() {
        val queue = ControllerActionQueue()
        val token = queue.start()
        queue.offer(token, false, 10L)
        assertTrue(queue.drain(10L, true).presses.isEmpty())
        queue.offer(token, true, 20L)
        val press = queue.drain(20L, true).presses.single()
        assertEquals(token, press.generation)
        assertEquals(20L, press.receivedAtNanos)
        repeat(5) { queue.offer(token, true, 21L + it) }
        assertTrue(queue.drain(30L, true).presses.isEmpty())
        queue.offer(token, false, 40L)
        queue.offer(token, true, 50L)
        assertEquals(1, queue.drain(50L, true).presses.size)
    }

    @Test
    fun anInitiallyHeldButtonMustBeReleasedAndPressed() {
        val queue = ControllerActionQueue()
        val token = queue.start()
        queue.offer(token, true, 10L)
        assertTrue(queue.drain(10L, true).presses.isEmpty())
        queue.offer(token, true, 20L)
        assertTrue(queue.drain(20L, true).presses.isEmpty())
        queue.offer(token, false, 30L)
        queue.offer(token, true, 40L)
        assertEquals(1, queue.drain(40L, true).presses.size)
    }

    @Test
    fun resetAndDisabledDrainsDiscardEdgesAndRequireAnotherRelease() {
        val queue = ControllerActionQueue()
        val token = queue.start()
        queue.offer(token, false, 10L)
        queue.drain(10L, true)
        queue.offer(token, true, 20L)
        queue.reset()
        assertTrue(queue.drain(20L, true).presses.isEmpty())
        queue.offer(token, true, 30L)
        assertTrue(queue.drain(30L, true).presses.isEmpty())
        queue.offer(token, false, 40L)
        queue.offer(token, true, 50L)
        assertTrue(queue.drain(50L, false).presses.isEmpty())
        queue.offer(token, true, 60L)
        assertTrue(queue.drain(60L, true).presses.isEmpty())
        queue.offer(token, false, 70L)
        queue.offer(token, true, 80L)
        assertEquals(1, queue.drain(80L, true).presses.size)
    }

    @Test
    fun stoppingAndRestartingRejectsOldListenerGenerations() {
        val queue = ControllerActionQueue()
        val old = queue.start()
        queue.offer(old, false, 10L)
        queue.stop()
        queue.offer(old, true, 20L)
        assertTrue(queue.drain(20L, true).presses.isEmpty())
        val current = queue.start()
        assertNotEquals(old, current)
        queue.offer(current, false, 30L)
        queue.drain(30L, true)
        queue.offer(old, true, 40L)
        assertTrue(queue.drain(40L, true).presses.isEmpty())
        queue.offer(current, true, 50L)
        assertEquals(1, queue.drain(50L, true).presses.size)
    }

    @Test
    fun overflowDropsTheWholeChainAndHeldSnapshotsCannotBecomePresses() {
        val queue = ControllerActionQueue(capacity = 2)
        val token = queue.start()
        queue.offer(token, false, 10L)
        queue.offer(token, true, 20L)
        queue.offer(token, false, 30L)
        queue.offer(token, true, 40L)
        val overflow = queue.drain(40L, true)
        assertTrue(overflow.presses.isEmpty())
        assertEquals(3L, overflow.droppedChanges)
        queue.offer(token, false, 50L)
        queue.offer(token, true, 60L)
        assertEquals(1, queue.drain(60L, true).presses.size)
    }

    @Test
    fun expiryDropsTheWholeBatchAndDoesNotReplayARecentPressFromTheBrokenChain() {
        val queue = ControllerActionQueue()
        val token = queue.start()
        queue.offer(token, false, 1L)
        queue.offer(token, true, 300_000_000L)
        val stale = queue.drain(300_000_000L, true)
        assertTrue(stale.presses.isEmpty())
        assertEquals(2L, stale.droppedChanges)
        queue.offer(token, true, 300_000_001L)
        assertTrue(queue.drain(300_000_001L, true).presses.isEmpty())
        queue.offer(token, false, 300_000_002L)
        queue.offer(token, true, 300_000_003L)
        assertEquals(1, queue.drain(300_000_003L, true).presses.size)
    }

    @Test
    fun futureAndRegressingReceiptsRequireANewBaseline() {
        val queue = ControllerActionQueue()
        val token = queue.start()
        queue.offer(token, false, 10L)
        queue.drain(10L, true)
        queue.offer(token, true, 9L)
        assertTrue(queue.drain(20L, true).presses.isEmpty())
        queue.offer(token, true, 30L)
        assertTrue(queue.drain(29L, true).presses.isEmpty())
        queue.offer(token, true, 40L)
        assertTrue(queue.drain(40L, true).presses.isEmpty())
        queue.offer(token, false, 50L)
        queue.offer(token, true, 60L)
        assertEquals(1, queue.drain(60L, true).presses.size)
    }

    @Test(expected = IllegalArgumentException::class)
    fun anEmptyQueueCapacityIsRejected() {
        ControllerActionQueue(0)
    }
}
