package com.example.wuxiaarena.p0d2f0182.input

import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class NativeControllerPoseProbeCacheTest {
    private fun pose(x: Double) = ObservedPose(Vector3(x, 1.2, -0.4), Quaternion(0.0, 0.0, 0.0, 1.0))

    private fun recordAccepted(
        cache: NativeControllerPoseProbeCache,
        token: Long,
        left: ObservedPose?,
        right: ObservedPose?,
        receivedAtNanos: Long,
    ) {
        cache.recordRaw(token, left, right, receivedAtNanos)
        cache.recordOutcome(token, NativeControllerPoseProbeOutcome.ACCEPTED_TO_BUFFER)
    }

    @Test
    fun reportsLatestImmutablePoseAndThrottlesChangesToFiveHertz() {
        val cache = NativeControllerPoseProbeCache()
        cache.start(7L)
        recordAccepted(cache, 7L, pose(-0.2), pose(0.2), 10L)
        val first = requireNotNull(cache.poll(20L))
        assertEquals(7L, first.generation)
        assertEquals(1L, first.rawCallbacks)
        assertEquals(1L, first.acceptedToBuffer)
        assertEquals(10L, first.rawReceivedAtNanos)
        assertEquals(TrackingQuality.UNKNOWN, first.rawRight?.quality)
        assertEquals("changed", first.reason)

        recordAccepted(cache, 7L, null, pose(0.5), 30L)
        recordAccepted(cache, 7L, null, pose(0.8), 40L)
        assertNull(cache.poll(200_000_019L))
        val latest = requireNotNull(cache.poll(200_000_020L))
        assertEquals(3L, latest.rawCallbacks)
        assertEquals(3L, latest.acceptedToBuffer)
        assertEquals(40L, latest.rawReceivedAtNanos)
        assertNull(latest.rawLeft)
        assertEquals(pose(0.8), latest.rawRight)
        assertTrue(latest.message().contains("rawLeft={available=false positionValid=false rotationValid=false"))
        assertTrue(latest.message().contains("rawRight={available=true positionValid=true rotationValid=true quality=UNKNOWN"))
    }

    @Test
    fun unchangedOrMissingPosesStillProduceAtMostOneHeartbeatPerSecond() {
        val cache = NativeControllerPoseProbeCache()
        cache.start(1L)
        val initial = requireNotNull(cache.poll(0L))
        assertEquals(0L, initial.rawCallbacks)
        assertNull(initial.rawReceivedAtNanos)
        assertEquals("heartbeat", initial.reason)
        assertNull(cache.poll(999_999_999L))
        assertEquals("heartbeat", requireNotNull(cache.poll(1_000_000_000L)).reason)

        recordAccepted(cache, 1L, pose(-0.2), null, 1_000_000_010L)
        assertNull(cache.poll(1_199_999_999L))
        val firstPose = requireNotNull(cache.poll(1_200_000_000L))
        assertEquals("changed", firstPose.reason)
        recordAccepted(cache, 1L, pose(-0.2), null, 1_500_000_000L)
        assertNull(cache.poll(2_199_999_999L))
        val heartbeat = requireNotNull(cache.poll(2_200_000_000L))
        assertEquals("heartbeat", heartbeat.reason)
        assertEquals(2L, heartbeat.rawCallbacks)
        assertEquals(1_500_000_000L, heartbeat.rawReceivedAtNanos)
    }

    @Test
    fun clearAndRestartRejectOldCallbacksAndErasePreviousValues() {
        val cache = NativeControllerPoseProbeCache()
        cache.start(1L)
        recordAccepted(cache, 1L, pose(-0.2), pose(0.2), 10L)
        cache.poll(20L)
        cache.clear()
        recordAccepted(cache, 1L, pose(-9.0), pose(9.0), 30L)
        assertNull(cache.poll(1_000_000_000L))

        cache.start(3L)
        recordAccepted(cache, 1L, pose(-9.0), pose(9.0), 40L)
        val restarted = requireNotNull(cache.poll(50L))
        assertEquals(3L, restarted.generation)
        assertEquals(0L, restarted.rawCallbacks)
        assertEquals(0L, restarted.acceptedToBuffer)
        assertEquals(0L, restarted.droppedControlFault)
        assertEquals(0L, restarted.droppedStatusUnknown)
        assertEquals(0L, restarted.droppedUnavailable)
        assertEquals(0L, restarted.droppedBufferRejected)
        assertNull(restarted.lastOutcome)
        assertNull(restarted.rawReceivedAtNanos)
        assertNull(restarted.rawLeft)
        assertNull(restarted.rawRight)
        assertFalse(restarted.message().contains("9.0"))

        recordAccepted(cache, 3L, null, pose(0.4), 60L)
        val accepted = requireNotNull(cache.poll(200_000_050L))
        assertEquals(1L, accepted.rawCallbacks)
        assertEquals(pose(0.4), accepted.rawRight)
    }

    @Test
    fun rawCallbacksAndMutuallyExclusiveOutcomesRemainDistinct() {
        val cache = NativeControllerPoseProbeCache()
        cache.start(5L)
        NativeControllerPoseProbeOutcome.entries.forEachIndexed { index, outcome ->
            cache.recordRaw(5L, null, pose(index.toDouble()), index.toLong())
            cache.recordOutcome(5L, outcome)
        }
        val report = requireNotNull(cache.poll(20L))
        assertEquals(5L, report.rawCallbacks)
        assertEquals(1L, report.acceptedToBuffer)
        assertEquals(1L, report.droppedControlFault)
        assertEquals(1L, report.droppedStatusUnknown)
        assertEquals(1L, report.droppedUnavailable)
        assertEquals(1L, report.droppedBufferRejected)
        assertEquals(report.rawCallbacks, report.acceptedToBuffer + report.droppedControlFault +
            report.droppedStatusUnknown + report.droppedUnavailable + report.droppedBufferRejected)
        assertEquals(NativeControllerPoseProbeOutcome.BUFFER_REJECTED, report.lastOutcome)
        assertEquals(pose(4.0), report.rawRight)
    }
}
