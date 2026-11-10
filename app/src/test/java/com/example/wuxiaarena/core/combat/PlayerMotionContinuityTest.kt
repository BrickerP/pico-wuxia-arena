package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PlayerMotionContinuityTest {
    private val enemy = Vector3(0.0, 0.0, -10.0)
    private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

    @Test
    fun continuousSamplesExposeRealTipSpeedAndTheExistingRestDecision() {
        val resolver = PlayerCombatResolver()
        val baseline = requireNotNull(resolver.observe(snapshot(1L, 0L, 0.0), enemy))
        val slow = requireNotNull(resolver.observe(snapshot(3L, 125_000_000L, 0.025), enemy))
        val moving = requireNotNull(resolver.observe(snapshot(5L, 250_000_000L, 0.0875), enemy))

        assertTrue(baseline.bladeAtRest)
        assertEquals(0.0, baseline.bladeTipSpeed, 0.0)
        assertTrue(baseline.motionGeneration > 0L)
        assertEquals(0.2, slow.bladeTipSpeed, 1e-9)
        assertTrue(slow.bladeAtRest)
        assertEquals(0.5, moving.bladeTipSpeed, 1e-9)
        assertFalse(moving.bladeAtRest)
        assertEquals(baseline.motionGeneration, moving.motionGeneration)
    }

    @Test
    fun duplicateHandPacketsKeepTheirOriginalMotionSampleAndGeneration() {
        val resolver = PlayerCombatResolver()
        resolver.observe(snapshot(1L, 0L, 0.0), enemy)
        val current = snapshot(3L, 100_000_000L, 0.05)
        val frame = requireNotNull(resolver.observe(current, enemy))
        val updatedHead = PoseObservation(ObservationStamp(4L, 150_000_000L, 1L, InputOrigin.SYNTHETIC),
            ObservedPose(Vector3(0.0, 1.6, 0.0), rotation))

        val duplicate = requireNotNull(resolver.observe(current.copy(head = updatedHead), enemy))

        assertEquals(frame.receivedAtNanos, duplicate.receivedAtNanos)
        assertEquals(frame.bladeTipSpeed, duplicate.bladeTipSpeed, 0.0)
        assertEquals(frame.bladeAtRest, duplicate.bladeAtRest)
        assertEquals(frame.motionGeneration, duplicate.motionGeneration)
        assertNull(duplicate.strike)
    }

    @Test
    fun rotatingTheBladeAroundItsStationaryTipKeepsTheExistingWholeBladeRestDecision() {
        val resolver = PlayerCombatResolver()
        val baseline = requireNotNull(resolver.observe(snapshot(1L, 0L, 0.0), enemy))
        val turn = Quaternion(0.0, kotlin.math.sin(0.05), 0.0, kotlin.math.cos(0.05))
        val localTip = baseline.bladeTip - Vector3(0.0, 0.95, 0.0)
        val handPosition = baseline.bladeTip - requireNotNull(turn.rotate(localTip))
        val next = snapshot(3L, 100_000_000L, 0.0, turn)
        val left = requireNotNull(next.left)
        val adjusted = next.copy(left = left.copy(pose = requireNotNull(left.pose).copy(position = handPosition)))

        val frame = requireNotNull(resolver.observe(adjusted, enemy))

        assertEquals(0.0, frame.bladeTipSpeed, 1e-9)
        assertFalse(frame.bladeAtRest)
        assertEquals(baseline.motionGeneration, frame.motionGeneration)
    }

    @Test
    fun aGapAnAbruptRotationAndImplausibleSpeedEachStartANewRestingBaseline() {
        val failures = listOf(
            snapshot(5L, 500_000_000L, 0.10),
            snapshot(5L, 200_000_000L, 0.10, Quaternion(0.0, 1.0, 0.0, 0.0)),
            snapshot(5L, 200_000_000L, 4.05),
        )
        for (invalidStep in failures) {
            val resolver = PlayerCombatResolver()
            resolver.observe(snapshot(1L, 0L, 0.0), enemy)
            val before = requireNotNull(resolver.observe(snapshot(3L, 100_000_000L, 0.05), enemy))

            val newBaseline = requireNotNull(resolver.observe(invalidStep, enemy))

            assertTrue(newBaseline.motionGeneration > before.motionGeneration)
            assertEquals(resolver.motionGeneration, newBaseline.motionGeneration)
            assertTrue(newBaseline.bladeAtRest)
            assertEquals(0.0, newBaseline.bladeTipSpeed, 0.0)
            assertNull(newBaseline.strike)
        }
    }

    @Test
    fun unavailableAndRegressingObservationsInvalidateTheGenerationEvenWithoutAFrame() {
        val invalidSnapshots = listOf(
            snapshot(5L, 200_000_000L, 0.10).copy(left = null),
            snapshot(5L, 90_000_000L, 0.10),
            snapshot(1L, 200_000_000L, 0.10),
        )
        for (invalid in invalidSnapshots) {
            val resolver = PlayerCombatResolver()
            resolver.observe(snapshot(1L, 0L, 0.0), enemy)
            val previous = requireNotNull(resolver.observe(snapshot(3L, 100_000_000L, 0.05), enemy))

            assertNull(resolver.observe(invalid, enemy))
            assertTrue(resolver.motionGeneration > previous.motionGeneration)

            val restored = requireNotNull(resolver.observe(snapshot(7L, 300_000_000L, 0.15), enemy))
            assertTrue(restored.motionGeneration > previous.motionGeneration)
            assertTrue(restored.bladeAtRest)
            assertEquals(0.0, restored.bladeTipSpeed, 0.0)
            assertNull(restored.strike)
        }
    }

    @Test
    fun changingTheTrackingIdentityOrExplicitlyResettingCannotReuseTheOldGeneration() {
        val resolver = PlayerCombatResolver()
        resolver.observe(snapshot(1L, 0L, 0.0), enemy)
        val before = requireNotNull(resolver.observe(snapshot(3L, 100_000_000L, 0.05), enemy))
        val changed = requireNotNull(resolver.observe(
            snapshot(5L, 200_000_000L, 0.10).copy(leftContinuity = 1L), enemy,
        ))
        assertTrue(changed.motionGeneration > before.motionGeneration)
        assertTrue(changed.bladeAtRest)

        resolver.reset()
        assertTrue(resolver.motionGeneration > changed.motionGeneration)
        val afterReset = requireNotNull(resolver.observe(snapshot(7L, 300_000_000L, 0.15), enemy))
        assertTrue(afterReset.motionGeneration > changed.motionGeneration)
        assertTrue(afterReset.bladeAtRest)
        assertEquals(0.0, afterReset.bladeTipSpeed, 0.0)
    }

    private fun snapshot(sequence: Long, atNanos: Long, handX: Double, handRotation: Quaternion = rotation) =
        TrackingSnapshot(
            PoseObservation(ObservationStamp(sequence - 1L, atNanos, 1L, InputOrigin.SYNTHETIC),
                ObservedPose(Vector3(0.0, 1.6, 0.0), rotation)),
            PoseObservation(ObservationStamp(sequence, atNanos, 1L, InputOrigin.SYNTHETIC),
                ObservedPose(Vector3(handX, 0.95, 0.0), handRotation)),
            PoseObservation(ObservationStamp(sequence, atNanos, 1L, InputOrigin.SYNTHETIC),
                ObservedPose(Vector3(0.7, 1.2, 0.0), rotation)),
            Hand.LEFT, 0L, 0L, 0L,
        )
}
