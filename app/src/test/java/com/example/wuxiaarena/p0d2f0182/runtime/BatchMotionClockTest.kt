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
        // Compare identical receipts/target motion across batching strategies at
        // both origins. Breathing makes the target physically different 10 ms
        // later, so a translated witness need not differ by exactly 10 ms.
        assertSameContactClock(3_000_000_000L)
        assertSameContactClock(3_010_000_000L)
    }

    @Test
    fun interleavedHeadReceiptsAndSameTimeDeliveryOrderPreserveTheRealHandStroke() {
        fun run(handFirst: Boolean, intermediateHeights: List<Double>): Fixture {
            val fixture = Fixture()
            val start = 3_010_000_000L
            // A head observation is already available when the next native pair arrives.
            fixture.head(start - 4_000_000L)
            fixture.observe(start, 0.0, handFirst)
            intermediateHeights.forEachIndexed { index, height ->
                fixture.head(start + (index + 1) * 40_000_000L, height)
            }
            fixture.observe(start + 200_000_000L, -0.35, handFirst)
            fixture.session.onTick(3_250_000_000L)
            return fixture
        }

        val reference = run(false, emptyList())
        val hit = reference.damageImpact()
        assertEquals(HitZone.BODY, hit.zone)
        assertEquals(1, reference.impacts.size)
        for (heights in listOf(emptyList(), List(4) { 1.6 }, listOf(1.605, 1.596, 1.604, 1.6))) {
            for (handFirst in listOf(true, false)) {
                val replay = run(handFirst, heights)
                val actual = replay.impacts.single()
                assertEquals(hit.kind, actual.kind)
                assertEquals(hit.zone, actual.zone)
                assertEquals(hit.appliedDamage, actual.appliedDamage)
                assertEquals(hit.atNanos, actual.atNanos)
                assertEquals(reference.session.viewState.health, replay.session.viewState.health)
            }
        }
    }

    @Test
    fun headReceiptsAfterOneRealHitCannotReplayTheHeldBladesContact() {
        val fixture = Fixture()
        fixture.observe(3_010_000_000L, 0.0)
        fixture.observe(3_210_000_000L, -0.35)
        fixture.session.onTick(3_250_000_000L)
        val hit = fixture.damageImpact()
        val health = fixture.session.viewState.health
        val focus = fixture.session.viewState.focus

        for (index in 1..8) {
            val t = 3_250_000_000L + index * 20_000_000L
            fixture.head(t, if (index % 2 == 0) 1.62 else 1.6)
            fixture.session.onTick(t)
        }
        assertEquals(listOf(hit), fixture.impacts)
        assertEquals(health, fixture.session.viewState.health)
        assertEquals(focus, fixture.session.viewState.focus)
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

        private fun stamp(now: Long) = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)

        private fun send(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }

        fun head(now: Long, height: Double = 1.6) {
            send(TrackingEvent.Head(stamp(now), ObservedPose(Vector3(0.0, height, 0.0), rotation)))
        }

        fun observe(now: Long, handZ: Double, handFirst: Boolean = false) {
            if (!handFirst) head(now)
            send(TrackingEvent.Controllers(stamp(now), null, ObservedPose(Vector3(0.0, 0.7, handZ), rotation)))
            if (handFirst) head(now)
        }

        val impacts get() = events.filterIsInstance<CombatImpact>()

        fun damageImpact(): CombatImpact = impacts.single {
            it.kind == CombatImpactKind.SOFT_HIT && it.appliedDamage > 0
        }
    }
}
