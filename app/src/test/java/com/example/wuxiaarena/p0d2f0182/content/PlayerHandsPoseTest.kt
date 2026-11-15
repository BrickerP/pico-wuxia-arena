package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.fail
import org.junit.Test

class PlayerHandsPoseTest {
    private val identity = Quaternion(0.0, 0.0, 0.0, 1.0)

    @Test
    fun rawGripPoseNormalizesRotationWithoutChangingPosition() {
        val position = Vector3(0.25, 1.15, -0.4)
        val mapped = checkNotNull(playerHandTransform(ObservedPose(position, Quaternion(0.0, 2.0, 0.0, 2.0))))
        assertEquals(position, mapped.position)
        assertVector(Vector3(-1.0, 0.0, 0.0), checkNotNull(mapped.rotation.rotate(Vector3(0.0, 0.0, -1.0))))
    }

    @Test
    fun eachOffhandUsesItsOwnRawCommonGripPose() {
        val left = ObservedPose(Vector3(-0.3, 1.1, -0.2), Quaternion(0.1, 0.2, -0.4, 0.7))
        val right = ObservedPose(Vector3(0.3, 1.1, -0.2), Quaternion(-0.2, 0.4, 0.3, 0.7))
        val axes = listOf(Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0), Vector3(0.0, 0.0, 1.0))
        for (equipped in Hand.entries) {
            val offHand = if (equipped == Hand.RIGHT) Hand.LEFT else Hand.RIGHT
            val state = snapshot(equipped).let {
                it.copy(left = it.left?.copy(pose = left), right = it.right?.copy(pose = right))
            }
            val expected = if (offHand == Hand.LEFT) left else right
            val mapped = checkNotNull(presentedPlayerHandTransform(state, null, offHand))
            assertVector(checkNotNull(expected.position), mapped.position)
            for (axis in axes) {
                assertVector(checkNotNull(expected.rotation?.rotate(axis)), checkNotNull(mapped.rotation.rotate(axis)))
            }
        }
    }

    @Test
    fun bothEquippedRootsUseTheCommonGripWithoutAssetOffsets() {
        val position = Vector3(-0.2, 1.25, -0.35)
        val axes = listOf(Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0), Vector3(0.0, 0.0, 1.0))
        for (rotation in listOf(identity, Quaternion(0.2, 0.3, -0.4, 0.7), Quaternion(0.0, 2.0, 0.0, 2.0))) {
            val grip = WeaponGrip(position, rotation)
            for (hand in Hand.entries) {
                val mapped = checkNotNull(presentedPlayerHandTransform(snapshot(hand), grip, hand))
                assertVector(position, mapped.position)
                for (axis in axes) {
                    assertVector(checkNotNull(rotation.rotate(axis)), checkNotNull(mapped.rotation.rotate(axis)))
                }
            }
        }
    }

    @Test
    fun equipmentSideSelectsTheGripEndpoint() {
        assertEquals(1f, playerHandGripTime(Hand.RIGHT, Hand.RIGHT), 0f)
        assertEquals(0f, playerHandGripTime(Hand.LEFT, Hand.RIGHT), 0f)
        assertEquals(0f, playerHandGripTime(Hand.RIGHT, Hand.LEFT), 0f)
        assertEquals(1f, playerHandGripTime(Hand.LEFT, Hand.LEFT), 0f)
    }

    @Test
    fun missingInvalidAndUnrepresentableInputNeverProducesAHandPose() {
        val good = ObservedPose(Vector3(0.0, 1.2, -0.3), identity)
        val invalid = listOf(null, good.copy(position = null), good.copy(rotation = null),
            good.copy(quality = TrackingQuality.SOURCE_REPORTED_INVALID),
            good.copy(position = Vector3(Double.NaN, 0.0, 0.0)),
            good.copy(position = Vector3(Double.POSITIVE_INFINITY, 0.0, 0.0)),
            good.copy(position = Vector3(Double.MAX_VALUE, 0.0, 0.0)),
            good.copy(rotation = Quaternion(0.0, 0.0, 0.0, 0.0)),
            good.copy(rotation = Quaternion(0.0, Double.NaN, 0.0, 1.0)))
        for (pose in invalid) assertNull(playerHandTransform(pose))
        assertNotNull(playerHandTransform(good))
    }

    @Test
    fun unknownQualityUsesTheExistingPresenceContract() {
        val pose = ObservedPose(Vector3(0.0, 1.1, -0.2), identity, TrackingQuality.UNKNOWN)
        assertNotNull(playerHandTransform(pose))
        assertNull(playerHandTransform(null))
        assertNull(playerHandTransform(pose.copy(quality = TrackingQuality.SOURCE_REPORTED_INVALID)))
    }

    @Test
    fun equippedHandUsesFinalGripWhileOffHandKeepsItsRawObservation() {
        val solved = WeaponGrip(Vector3(0.35, 1.2, -0.4), Quaternion(0.0, 1.0, 0.0, 1.0))
        for (equipped in Hand.entries) {
            val snapshot = snapshot(equipped)
            val rawCopy = snapshot.copy()
            val offHand = if (equipped == Hand.RIGHT) Hand.LEFT else Hand.RIGHT
            assertEquals(playerHandTransform(ObservedPose(solved.position, solved.rotation)),
                presentedPlayerHandTransform(snapshot, solved, equipped))
            val offPose = (if (offHand == Hand.LEFT) snapshot.left else snapshot.right)?.pose
            assertEquals(playerHandTransform(offPose), presentedPlayerHandTransform(snapshot, solved, offHand))
            assertEquals(rawCopy, snapshot)
        }
    }

    @Test
    fun absentFinalGripAndLostRequiredInputHideEquippedHandWithoutAStaleRawFallback() {
        val solved = WeaponGrip(Vector3(0.35, 1.2, -0.4), identity)
        val unrepresentable = WeaponGrip(Vector3(Double.MAX_VALUE, 0.0, 0.0), identity)
        for (equipped in Hand.entries) {
            val snapshot = snapshot(equipped)
            assertNull(presentedPlayerHandTransform(snapshot, null, equipped))
            assertNull(presentedPlayerHandTransform(snapshot, unrepresentable, equipped))
            assertNull(presentedPlayerHandTransform(snapshot.copy(head = null), solved, equipped))
            assertNull(presentedPlayerHandTransform(snapshot.copy(requiredSinceSequence = 2L), solved, equipped))
            assertNull(presentedPlayerHandTransform(null, solved, equipped))
        }
    }

    @Test
    fun invalidOffhandHidesOnlyThatSideWhileTheEquippedHandKeepsItsFinalGrip() {
        val grip = WeaponGrip(Vector3(-0.1, 1.2, -0.5), Quaternion(0.1, 0.3, -0.4, 0.7))
        for (equipped in Hand.entries) {
            val offHand = if (equipped == Hand.RIGHT) Hand.LEFT else Hand.RIGHT
            val state = snapshot(equipped)
            val invalid = ObservedPose(Vector3(0.0, 0.0, 0.0), identity, TrackingQuality.SOURCE_REPORTED_INVALID)
            val withoutOffhand = if (offHand == Hand.LEFT) state.copy(left = null) else state.copy(right = null)
            val invalidOffhand = if (offHand == Hand.LEFT) state.copy(left = state.left?.copy(pose = invalid))
                else state.copy(right = state.right?.copy(pose = invalid))
            for (sample in listOf(withoutOffhand, invalidOffhand)) {
                assertNull(presentedPlayerHandTransform(sample, grip, offHand))
                val held = checkNotNull(presentedPlayerHandTransform(sample, grip, equipped))
                assertVector(grip.position, held.position)
            }
        }
    }

    @Test
    fun changingEquipmentRequiresFreshTrackingBeforeShowingTheNewEquippedHand() {
        val tracking = TrackingState(Hand.RIGHT)
        fun stamp(sequence: Long) = ObservationStamp(sequence, sequence, 0L, InputOrigin.PICO)
        val head = ObservedPose(Vector3(0.0, 1.6, 0.0), identity)
        val left = ObservedPose(Vector3(-0.3, 1.1, -0.2), identity)
        val right = ObservedPose(Vector3(0.3, 1.1, -0.2), identity)
        val oldGrip = WeaponGrip(Vector3(0.25, 1.2, -0.5), identity)
        tracking.accept(TrackingEvent.Head(stamp(1L), head))
        tracking.accept(TrackingEvent.Controllers(stamp(2L), left, right))
        assertNotNull(presentedPlayerHandTransform(tracking.snapshot, oldGrip, Hand.RIGHT))

        tracking.accept(TrackingEvent.DominantHandChanged(stamp(3L), Hand.LEFT))
        assertNull(presentedPlayerHandTransform(tracking.snapshot, oldGrip, Hand.LEFT))
        assertNull(presentedPlayerHandTransform(tracking.snapshot, oldGrip, Hand.RIGHT))
        tracking.accept(TrackingEvent.Head(stamp(4L), head))
        assertNull(presentedPlayerHandTransform(tracking.snapshot, oldGrip, Hand.LEFT))
        tracking.accept(TrackingEvent.Controllers(stamp(5L), left, right))

        val newGrip = WeaponGrip(Vector3(-0.25, 1.2, -0.5), Quaternion(0.2, 0.3, -0.4, 0.7))
        val held = checkNotNull(presentedPlayerHandTransform(tracking.snapshot, newGrip, Hand.LEFT))
        assertVector(newGrip.position, held.position)
        val offhand = checkNotNull(presentedPlayerHandTransform(tracking.snapshot, newGrip, Hand.RIGHT))
        assertVector(checkNotNull(right.position), offhand.position)
    }

    private fun snapshot(equippedHand: Hand): TrackingSnapshot {
        val stamp = ObservationStamp(1L, 1L, 0L, InputOrigin.PICO)
        return TrackingSnapshot(
            PoseObservation(stamp, ObservedPose(Vector3(0.0, 1.6, 0.0), identity)),
            PoseObservation(stamp, ObservedPose(Vector3(-0.3, 1.1, -0.2), identity)),
            PoseObservation(stamp, ObservedPose(Vector3(0.3, 1.1, -0.2), identity)),
            equippedHand, 0L, 0L, 0L,
        )
    }

    @Test
    fun cleanupClosesEveryHandleAndRetainsBothFailureCauses() {
        val closed = mutableListOf<Int>()
        val first = IllegalStateException("controller close")
        val last = IllegalArgumentException("model destroy")
        try {
            closePlayerHandResources(listOf(
                AutoCloseable { closed += 1; throw first },
                AutoCloseable { closed += 2 },
                AutoCloseable { closed += 3; throw last },
            ))
            fail("Expected cleanup failure")
        } catch (error: IllegalStateException) {
            assertSame(first, error)
            assertEquals(listOf(last), error.suppressed.toList())
        }
        assertEquals(listOf(1, 2, 3), closed)
    }

    @Test
    fun emptyAndSuccessfulCleanupReleaseTheirWholeLists() {
        closePlayerHandResources(emptyList())
        var released = 0
        closePlayerHandResources(List(4) { AutoCloseable { released++ } })
        assertEquals(4, released)
    }

    private fun assertVector(expected: Vector3, actual: Vector3) {
        assertEquals(expected.x, actual.x, 1e-9)
        assertEquals(expected.y, actual.y, 1e-9)
        assertEquals(expected.z, actual.z, 1e-9)
    }
}
