package com.example.wuxiaarena.p0d2f0182.content

import org.junit.Assert.*
import org.junit.Test

class BladeTrailReceiptBudgetTest {
    @Test fun readyOrIneligiblePoseCannotSpendTheFutureRoundWindow() {
        val budget = BladeTrailReceiptBudget()
        repeat(600) { index ->
            val now = index * 1_000_000_000L
            assertFalse(budget.collecting(now, false))
            assertNull(budget.next(now, false))
        }
        val fight = 600_000_000_000L
        assertTrue(budget.collecting(fight, true))
        assertEquals("summary", budget.next(fight, false))
        assertEquals("first_submit", budget.next(fight + 1L, true))
    }

    @Test fun sixSecondBoundaryDoesNotRearmForLaterActionsOrRounds() {
        val budget = BladeTrailReceiptBudget()
        assertTrue(budget.collecting(100L, true))
        assertTrue(budget.collecting(6_000_000_099L, true))
        assertFalse(budget.collecting(6_000_000_100L, true))
        assertNull(budget.next(6_000_000_100L, true))
        assertFalse(budget.collecting(600_000_000_000L, true))
        assertNull(budget.next(600_000_000_000L, true))
    }

    @Test fun totalsReserveOneLateFirstPairAndStayWithinNineIncludingOwnerReceipts() {
        val budget = BladeTrailReceiptBudget()
        val receipts = mutableListOf<String>()
        for (ms in 0..7000) {
            val now = ms * 1_000_000L
            budget.collecting(now, true)
            budget.next(now, ms >= 5900, hasFirstPair = ms >= 5901)?.let { receipts.add(it) }
        }
        assertEquals(5, receipts.count { it == "summary" })
        assertEquals(1, receipts.count { it == "first_submit" })
        assertEquals(1, receipts.count { it == "first_ui_batch_hide" })
        // The owner emits exactly one constructor and one first-present receipt separately.
        assertEquals(9, receipts.size + 2)
    }

    @Test fun aFirstPairAtOrAfterSixSecondsCannotExtendTheBudget() {
        val budget = BladeTrailReceiptBudget()
        budget.collecting(0L, true)
        assertEquals("first_submit", budget.next(0L, true))
        assertNull(budget.next(6_000_000_000L, false, hasFirstPair = true))
        assertNull(budget.next(7_000_000_000L, false, hasFirstPair = true))
    }

    @Test fun firstSubmitIsNotLostBehindTheSummaryInterval() {
        val budget = BladeTrailReceiptBudget()
        budget.collecting(0L, true)
        assertEquals("summary", budget.next(0L, false))
        assertNull(budget.next(10L, false))
        assertEquals("first_submit", budget.next(11L, true))
        assertNull(budget.next(12L, true))
        assertEquals("summary", budget.next(1_000_000_000L, true))
    }

    @Test fun oldReceiptTimesDoNotGenerateExtraLogs() {
        val budget = BladeTrailReceiptBudget()
        budget.collecting(100L, true)
        assertEquals("summary", budget.next(100L, false))
        assertFalse(budget.collecting(99L, true))
        assertNull(budget.next(99L, false))
        assertNull(budget.next(101L, false))
    }
    @Test fun getterFailureCannotDiscardTheCoreSubmissionReceipt() {
        val core = "receipt=first_submit operation=create create=1 replace=0 enable=1"
        for ((failOpacity, failAlpha) in listOf(true to false, false to true, true to true)) {
            var opacityReads = 0
            var alphaReads = 0
            val lines = mutableListOf<String>()
            lines += bladeTrailReceiptLine(core,
                { opacityReads++; if (failOpacity) throw IllegalStateException("opacity") else "1.0" },
                { alphaReads++; if (failAlpha) throw IllegalArgumentException("alpha") else "0.75" })
            assertEquals(1, lines.size)
            assertTrue(lines.single().startsWith(core))
            assertTrue(lines.single().contains(if (failOpacity) "materialOpacity=read_unavailable:IllegalStateException" else "materialOpacity=1.0"))
            assertTrue(lines.single().contains(if (failAlpha) "materialBaseAlpha=read_unavailable:IllegalArgumentException" else "materialBaseAlpha=0.75"))
            assertEquals(1, opacityReads)
            assertEquals(1, alphaReads)
        }
    }

}
