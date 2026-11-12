package com.example.wuxiaarena.p0d2f0182.content

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
    fun rightHandKeepsTheExactExistingDaoGripAndNormalizesRotation() {
        val position = Vector3(0.25, 1.15, -0.4)
        val mapped = checkNotNull(playerHandTransform(ObservedPose(position, Quaternion(0.0, 2.0, 0.0, 2.0)), Hand.RIGHT))
        assertEquals(position, mapped.position)
        assertVector(Vector3(-1.0, 0.0, 0.0), checkNotNull(mapped.rotation.rotate(Vector3(0.0, 0.0, -1.0))))
    }

    @Test
    fun leftDerivedGripReconstructsControllerPoseForIdentityAndTurnedControllers() {
        // Independently extracted root_to_player_grip_corrected, left candidate cf3203e0.
        val markerPosition = Vector3(-0.005627550009326868, -0.03993754136808973, -0.07604742022880186)
        val markerAxes = listOf(
            Vector3(-0.23397770924894626, -0.034728356585801964, -0.9716215172707247),
            Vector3(-0.07438118293574267, -0.995793524018109, 0.05350417879638239),
            Vector3(-0.9693925268949081, 0.0847891430104413, 0.2304103513904264),
        )
        val axes = listOf(Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0), Vector3(0.0, 0.0, 1.0))
        for (rotation in listOf(identity, Quaternion(0.2, 0.3, -0.4, 0.7), Quaternion(0.0, 1.0, 0.0, 0.0))) {
            val position = Vector3(-0.2, 1.25, -0.35)
            val mapped = checkNotNull(playerHandTransform(ObservedPose(position, rotation), Hand.LEFT))
            assertVector(position, mapped.position + checkNotNull(mapped.rotation.rotate(markerPosition)))
            for (i in axes.indices) {
                assertVector(checkNotNull(rotation.rotate(axes[i])), checkNotNull(mapped.rotation.rotate(markerAxes[i])))
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
        for (hand in Hand.entries) for (pose in invalid) assertNull(playerHandTransform(pose, hand))
        assertNotNull(playerHandTransform(good, Hand.LEFT))
        assertNotNull(playerHandTransform(good, Hand.RIGHT))
    }

    @Test
    fun unknownQualityUsesTheExistingPresenceContractAndEachSideIsIndependent() {
        val pose = ObservedPose(Vector3(0.0, 1.1, -0.2), identity, TrackingQuality.UNKNOWN)
        assertNotNull(playerHandTransform(pose, Hand.LEFT))
        assertNull(playerHandTransform(null, Hand.RIGHT))
        assertNotNull(playerHandTransform(pose, Hand.RIGHT))
        assertNull(playerHandTransform(pose.copy(quality = TrackingQuality.SOURCE_REPORTED_INVALID), Hand.LEFT))
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
