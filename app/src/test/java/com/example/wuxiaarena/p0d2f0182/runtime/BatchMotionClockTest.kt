package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BatchMotionClockTest {
    @Test
    fun queuedReceiptsUseTheSameContactClockAsTicksAtEachReceipt() {
        assertSameContactClock(3_010_000_000L)
    }

    @Test
    fun baselineAtPreviousTickTimeDoesNotCompressTheNextQueuedInterval() {
        val atBoundary = assertSameContactClock(3_000_000_000L)
        val afterBoundary = assertSameContactClock(3_010_000_000L)
        // With a motionless actor and the identical 200 ms motion, translating both
        // receipts by 10 ms must translate the actual witness time by exactly 10 ms.
        assertEquals(10_000_000L, afterBoundary.atNanos - atBoundary.atNanos)
    }

    private fun assertSameContactClock(firstReceipt: Long): CombatImpact {
        val secondReceipt = firstReceipt + 200_000_000L
        val batch = Fixture()
        batch.observe(firstReceipt, 0.0)
        batch.observe(secondReceipt, -0.35)
        batch.session.onTick(3_250_000_000L)

        val incremental = Fixture()
        incremental.observe(firstReceipt, 0.0)
        incremental.session.onTick(firstReceipt)
        incremental.observe(secondReceipt, -0.35)
        incremental.session.onTick(secondReceipt)

        val batchImpact = batch.damageImpact()
        val incrementalImpact = incremental.damageImpact()
        assertEquals(incrementalImpact.atNanos, batchImpact.atNanos)
        assertTrue(incrementalImpact.point.distanceTo(batchImpact.point) < 1e-10)
        assertTrue(incrementalImpact.normal.distanceTo(batchImpact.normal) < 1e-10)
        assertEquals(incrementalImpact.appliedDamage, batchImpact.appliedDamage)
        assertEquals(incremental.session.viewState.health, batch.session.viewState.health)
        assertEquals(HitZone.BODY, batchImpact.zone)
        assertFalse(batchImpact.fatal)
        // The blade reaches the torso during the full 200 ms receipt interval.
        // Cutting at internal 100 ms boundaries used to hold the old pose until
        // simulation 200 ms, then squeeze the full motion into the final 10 ms.
        assertTrue("The true contact must precede that artificial final interval", batchImpact.atNanos < 200_000_000L)
        assertTrue(batchImpact.atNanos > 10_000_000L)
        return batchImpact
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        private val events = mutableListOf<EnemyCombatEvent>()
        private val tracking = TrackingState(Hand.RIGHT)
        private var sequence = 0L
        private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

        init {
            session.setArenaPresenter { _, batch -> events.addAll(batch) }
            session.setEnemyGeometry(Vector3(0.0, 0.0, -1.3), 1.55)
            observe(0L, 0.0)
            assertTrue(session.startTrial())
            session.onTick(0L)
            session.onTick(3_000_000_000L)
            assertEquals(TrialResult.FIGHTING, session.viewState.result)
        }

        fun observe(now: Long, handZ: Double) {
            fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
            fun send(event: TrackingEvent) {
                val accepted = tracking.accept(event)
                assertTrue(accepted)
                session.onTrackingEvent(event, accepted, tracking.snapshot)
            }
            send(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, 1.6, 0.0), rotation)))
            send(TrackingEvent.Controllers(stamp(), null, ObservedPose(Vector3(0.0, 0.7, handZ), rotation)))
        }

        fun damageImpact(): CombatImpact = events.filterIsInstance<CombatImpact>().single {
            it.kind == CombatImpactKind.SOFT_HIT && it.appliedDamage > 0
        }
    }
}
