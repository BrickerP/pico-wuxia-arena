package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import org.junit.Assert.*
import org.junit.Test

class BladeTrailFrameReceiptTest {
    private fun sample(frame: Long?, outcome: String, sequence: Long = 10L, rest: Boolean = false) =
        BladeTrailFrameSample(frame, "tracking_controllers", ObservationStamp(sequence, sequence * 100, 2, InputOrigin.DESKTOP),
            sequence * 1000, outcome, rest, 4, 1, 2, Hand.RIGHT, InputOrigin.DESKTOP, "FIGHTING", true, true)

    @Test fun sameBatchHideRetainsTheActualFirstSourcePairAndDoesNotCountRepeatedHide() {
        val tracker = BladeTrailFrameReceipt()
        val before = sample(100L, "submitted")
        val after = sample(100L, "geometry_null", 11L, rest = true).copy(publishSource = "tick")
        tracker.observe(before)
        tracker.observe(after)
        tracker.observe(after.copy(wallNanos = 12000L))
        assertEquals(1L, tracker.sameUiBatchHides)
        assertEquals(1L, tracker.sameUiBatchRestHides)
        assertEquals(1L, tracker.sameUiBatchNullHides)
        assertEquals(before, tracker.firstPair?.submitted)
        assertEquals(after, tracker.firstPair?.hidden)
        assertTrue(tracker.receiptFields().contains("publishSource=tick"))
        assertTrue(tracker.receiptFields().contains("receivedAtNanos=1100"))
    }

    @Test fun absentFrameAndDifferentFrameNeverAttributeAHideToThePreviousBatch() {
        for (middle in listOf(null, 101L)) {
            val tracker = BladeTrailFrameReceipt()
            tracker.observe(sample(100L, "submitted"))
            tracker.observe(sample(middle, "geometry_null", rest = true))
            tracker.observe(sample(100L, "geometry_null", rest = true))
            assertEquals(0L, tracker.sameUiBatchHides)
            assertNull(tracker.firstPair)
        }
    }

    @Test fun rejectedOwnerIsNotAHideOperationAndNewSubmissionCanStartAnotherEdge() {
        val tracker = BladeTrailFrameReceipt()
        tracker.observe(sample(100L, "submitted"))
        tracker.observe(sample(100L, "owner_rejected", rest = true))
        assertEquals(0L, tracker.sameUiBatchHides)
        tracker.observe(sample(100L, "inactive_or_missing", 11L))
        val first = tracker.firstPair
        tracker.observe(sample(100L, "submitted", 12L))
        tracker.observe(sample(100L, "geometry_null", 13L))
        assertEquals(2L, tracker.sameUiBatchHides)
        assertEquals(1L, tracker.sameUiBatchNullHides)
        assertSame(first, tracker.firstPair)
    }

    @Test fun identityChangesAreExplicitEvidenceRatherThanAnUnlabelledStaleClaim() {
        val tracker = BladeTrailFrameReceipt()
        tracker.observe(sample(100L, "submitted"))
        tracker.observe(sample(100L, "geometry_null", rest = true).copy(motionGeneration = 5))
        assertEquals(1L, tracker.identityBoundaryHides)
        assertTrue(requireNotNull(tracker.firstPair).identityBoundary)
    }
}
