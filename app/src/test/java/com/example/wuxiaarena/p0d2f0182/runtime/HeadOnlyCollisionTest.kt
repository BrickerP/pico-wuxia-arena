package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class HeadOnlyCollisionTest {
    @Test
    fun stationarySteelExpiresAtItsHandDeadlineEvenInsideOneSceneTick() {
        fun guardedDuel() = Duel(
            headY = 1.695,
            spawn = Vector3(0.0, 0.028, -2.4),
            hand = Vector3(0.158, 1.664, -0.20),
            handRotation = Quaternion(0.052354, 0.31380, 0.0, 0.94804),
        ).also { duel ->
            repeat(400) {
                if (duel.state.phase == EnemyPhase.PREPARING &&
                    requireNotNull(duel.state.phaseRemainingNanos) < 300_000_000L) return@also
                duel.tick()
            }
            throw AssertionError("The opponent never prepared the opening overhead")
        }
        val witness = guardedDuel()
        val start = witness.now
        while (witness.impacts().isEmpty() && witness.now - start < 800_000_000L) witness.tick(delta = 1_000_000L)
        assertEquals(CombatImpactKind.BLOCK, witness.impacts().first().kind)
        val contactTick = witness.now
        for (expiresBeforeHit in listOf(true, false)) {
            val cutoff = contactTick + if (expiresBeforeHit) -3_000_000L else 1_000_000L
            for (split in listOf(true, false)) {
                val duel = guardedDuel()
                val finalHand = cutoff - 250_000_000L
                while (duel.now < finalHand) duel.tick(delta = 1_000_000L)
                while (duel.now < cutoff - 6_000_000L) {
                    duel.tick(delta = minOf(10_000_000L, cutoff - 6_000_000L - duel.now), includeHands = false)
                }
                assertTrue(duel.impacts().isEmpty())
                if (split) duel.tick(delta = cutoff - duel.now, includeHands = false)
                duel.tick(delta = cutoff + 4_000_000L - duel.now, includeHands = false)
                assertEquals("deadlineBeforeHit=$expiresBeforeHit, splitAtDeadline=$split",
                    if (expiresBeforeHit) emptyList() else listOf(CombatImpactKind.BLOCK),
                    duel.impacts().filter { it.kind != CombatImpactKind.PLAYER_HIT }.map { it.kind })
            }
        }
    }

    @Test
    fun theSameStepBackEvadesTheOverheadWithOrWithoutAnUnchangedHandReceipt() {
        for (paired in listOf(false, true)) {
            val duel = Duel()
            duel.seekOverheadStartup()
            repeat(19) { step ->
                duel.headZ = minOf(0.45, (step + 1) * 0.045)
                duel.tick(includeHands = paired)
            }
            // Only the receipt order differs during the dangerous part of the swing.
            assertEquals(100, duel.state.playerHealth)
            repeat(10) { duel.tick() }
            assertEquals(AttackOutcome.MISSED, duel.resolved())
            assertEquals(CombatFeedback.DODGE, duel.state.feedback)
            assertTrue(duel.state.counterOpen)
            assertEquals(duel.state.initialHealth, duel.state.health)
            assertTrue(duel.impacts().isEmpty())
        }
    }

    @Test
    fun theSameOverheadStillHitsWhenTheHeadStaysPut() {
        val duel = Duel()
        duel.seekOverheadStartup()
        repeat(19) { duel.tick(includeHands = false) }
        assertEquals(AttackOutcome.HIT_PLAYER, duel.resolved())
        assertEquals(80, duel.state.playerHealth)
        assertEquals(CombatImpactKind.PLAYER_HIT, duel.impacts().single().kind)
        assertFalse(duel.state.counterOpen)
    }

    @Test
    fun staleHandDoesNotPauseFreshHeadMotionOrTurnReacquisitionIntoASwing() {
        val duel = Duel()
        duel.tick()
        repeat(26) {
            duel.headZ += 0.01
            duel.tick(includeHands = false)
        }
        assertNull(duel.state.pauseReason)
        assertEquals(duel.headZ, requireNotNull(duel.state.playerHeadPosition).z, 0.0)
        // A grip on the opposite side would sweep through the opponent if bridged to the expired hand.
        duel.hand = Vector3(-0.55, 1.05, -0.65)
        repeat(5) { duel.tick() }
        assertEquals(duel.hand, duel.state.playerWeaponGrip?.position)
        assertEquals(duel.state.initialHealth, duel.state.health)
        assertEquals(0, duel.state.score)
        assertTrue(duel.impacts().isEmpty())
    }

    @Test
    fun freshHandsCannotBridgeTheGapToAReacquiredHeadAtANewPosition() {
        val duel = Duel()
        duel.tick()
        repeat(26) { duel.tick(includeHead = false) }
        duel.headZ = 0.45
        duel.tick(includeHands = false)
        assertEquals(PauseReason.TRACKING_INTERRUPTION, duel.state.pauseReason)
        val id = requireNotNull(duel.state.pauseId)
        val stopped = duel.state.simulationNanos
        duel.tick(includeHead = false)
        assertFalse(duel.session.confirmResume(id))
        assertEquals(stopped, duel.state.simulationNanos)
        duel.tick(includeHands = false)
        assertTrue(duel.session.confirmResume(id))
        assertFalse(duel.state.counterOpen)
        assertNull(duel.state.feedback)
        assertEquals(100, duel.state.playerHealth)
        assertTrue(duel.impacts().isEmpty())
    }

    @Test
    fun newHeadAloneCannotResumeAPausedOrRecenteredSwing() {
        for (reason in listOf(DiscontinuityReason.USER_PAUSED, DiscontinuityReason.RECENTERED)) {
            val duel = Duel()
            duel.seekOverheadStartup()
            duel.interrupt(reason)
            val pauseId = requireNotNull(duel.state.pauseId)
            val stopped = duel.state.simulationNanos
            duel.headZ = 0.45
            repeat(10) { duel.tick(includeHands = false) }
            assertEquals(stopped, duel.state.simulationNanos)
            assertFalse(duel.session.confirmResume(pauseId))
            duel.tick()
            assertTrue(duel.session.confirmResume(pauseId))
            assertNull(duel.state.pauseId)
            assertEquals(100, duel.state.playerHealth)
            assertFalse(duel.state.counterOpen)
            assertTrue(duel.impacts().isEmpty())
        }
    }

    private class Duel(
        private val headY: Double = 1.6,
        spawn: Vector3 = Vector3(0.0, 0.0, -1.30),
        var hand: Vector3 = Vector3(0.70, 1.0, 0.12),
        private val handRotation: Quaternion = Quaternion(0.0, 0.0, 0.0, 1.0),
    ) {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val state get() = session.viewState
        private val tracking = TrackingState(Hand.RIGHT)
        private val events = mutableListOf<EnemyCombatEvent>()
        private var sequence = 0L
        private var epoch = 1L
        var now = 0L
            private set
        private val identity = Quaternion(0.0, 0.0, 0.0, 1.0)
        var headZ = 0.0

        init {
            session.setArenaPresenter { _, batch -> events += batch }
            session.setEnemyGeometry(spawn, 1.55)
            tick(delta = 0L)
            assertTrue(session.startTrial())
            session.onTick(now)
            tick(delta = 3_000_000_000L)
            assertEquals(TrialResult.FIGHTING, state.result)
        }

        fun impacts() = events.filterIsInstance<CombatImpact>()
        fun resolved() = events.filterIsInstance<EnemyCombatEvent.AttackResolved>().single().outcome

        fun seekOverheadStartup() {
            repeat(300) {
                if (state.phase == EnemyPhase.STARTUP && state.attackDirection == AttackDirection.OVERHEAD &&
                    requireNotNull(state.phaseRemainingNanos) <= 60_000_000L) return
                tick()
            }
            throw AssertionError("First overhead never reached its final startup interval")
        }

        fun tick(delta: Long = 10_000_000L, includeHead: Boolean = true, includeHands: Boolean = true) {
            now += delta
            if (includeHead) send(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, headY, headZ), identity)))
            if (includeHands) send(TrackingEvent.Controllers(stamp(), null, ObservedPose(hand, handRotation)))
            session.onTick(now)
        }

        fun interrupt(reason: DiscontinuityReason) {
            if (reason == DiscontinuityReason.RECENTERED) epoch++
            send(TrackingEvent.Discontinuity(stamp(), TrackingTarget.ALL, reason))
        }

        private fun stamp() = ObservationStamp(sequence++, now, epoch, InputOrigin.PICO)

        private fun send(event: TrackingEvent) {
            assertTrue(tracking.accept(event))
            session.onTrackingEvent(event, true, tracking.snapshot)
        }
    }
}
