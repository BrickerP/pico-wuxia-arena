package com.example.wuxiaarena.p0d2f0182.content

import org.junit.Assert.*
import org.junit.Test

class ContactEventTimingTest {
    private val family = ContactEffectFamily.WET_CLOTH
    @Test fun duplicateDeliveryDuringHitstopDoesNotRestartEvent() {
        val gate = ResolvedSurfaceEventGate().also { it.reset(1) }
        assertTrue(gate.consume(2, 1, family, 900, 1000, true))
        assertFalse(gate.consume(2, 1, family, 900, 1000, true))
    }
    @Test fun pausedEventIsConsumedAndCannotReplayOnResume() {
        val gate = ResolvedSurfaceEventGate().also { it.reset(1) }
        assertFalse(gate.consume(2, 1, family, 900, 1000, false))
        assertFalse(gate.consume(2, 1, family, 900, 1000, true))
    }
    @Test fun roundResetAcceptsNewIdsAndRejectsDelayedPreviousRound() {
        val gate = ResolvedSurfaceEventGate().also { it.reset(1) }
        assertTrue(gate.consume(2, 1, family, 900, 1000, true))
        gate.reset(2)
        assertFalse(gate.consume(3, 1, family, 900, 1000, true))
        assertTrue(gate.consume(2, 2, family, 900, 1000, true))
    }
    @Test fun expiredAndFutureEventsNeverQueueForLater() {
        val gate = ResolvedSurfaceEventGate().also { it.reset(1) }
        assertFalse(gate.consume(2, 1, family, 0, 120_000_001, true))
        assertFalse(gate.consume(3, 1, family, 120_000_002, 120_000_001, true))
        assertFalse(gate.consume(3, 1, family, 120_000_002, 120_000_002, true))
    }
}
