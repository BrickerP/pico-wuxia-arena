package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.PI
import kotlin.math.sqrt

class IncomingBladeContactTest {
    private val zero = Vector3(0.0, 0.0, 0.0)
    private val body = EnemyContactPose(Vector3(0.0, 1.6, 0.0), zero, Vector3(0.0, 1.2, 0.0))

    @Test
    fun exactContactKeyUsesArrivingMotionEvenWhenTheNextKeyRecoils() {
        val attack = profile(listOf(
            pose(0.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
            pose(1.0, Vector3(1.0, 0.0, 0.0), Vector3(1.0, 1.0, 0.0)),
            pose(2.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
        ))
        assertDirection(Vector3(1.0, 0.0, 0.0), attack.bladeTangentAt(1.0, Vector3(1.0, 0.5, 0.0), zero, 0f))
        val origin = Vector3(3.0, 0.2, -4.0)
        val yaw = (PI / 2.0).toFloat()
        val rotated = attack.sample(1.0).inStage(origin, yaw)
        val tangent = requireNotNull(attack.bladeTangentAt(1.0, (rotated.bladeBase + rotated.bladeTip) * 0.5, origin, yaw))
        assertTrue(tangent.z < -0.999999)
        assertTrue(kotlin.math.abs(tangent.x) < 1e-6)
    }

    @Test
    fun contactWitnessUsesItsOwnBladeFractionWhenTheTipStaysStill() {
        val attack = profile(listOf(
            pose(0.0, Vector3(-1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
            pose(1.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
            pose(2.0, Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
        ))
        assertDirection(Vector3(1.0, 0.0, 0.0), attack.bladeTangentAt(1.0, Vector3(0.0, 0.5, 0.0), zero, 0f))
        assertDirection(Vector3(1.0, 0.0, 0.0), attack.bladeTangentAt(1.0, Vector3(0.0, -5.0, 0.0), zero, 0f))
        assertNull(attack.bladeTangentAt(1.0, Vector3(0.0, 1.0, 0.0), zero, 0f))
        assertNull(attack.bladeTangentAt(1.0, Vector3(0.0, 5.0, 0.0), zero, 0f))
    }

    @Test
    fun missingIntervalsRestAndDegenerateBladesCannotInventASparkDirection() {
        val still = profile(listOf(pose(0.0, zero, Vector3(0.0, 1.0, 0.0)),
            pose(2.0, zero, Vector3(0.0, 1.0, 0.0))))
        assertNull(still.bladeTangentAt(0.0, zero, zero, 0f))
        assertNull(still.bladeTangentAt(-0.1, zero, zero, 0f))
        assertNull(still.bladeTangentAt(2.1, zero, zero, 0f))
        assertNull(still.bladeTangentAt(1.0, zero, zero, 0f))
        val collapsed = profile(listOf(pose(0.0, zero, zero), pose(2.0, Vector3(1.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0))))
        assertNull(collapsed.bladeTangentAt(1.0, zero, zero, 0f))
        assertThrows(IllegalArgumentException::class.java) { still.bladeTangentAt(Double.NaN, zero, zero, 0f) }
    }

    @Test
    fun everyCurrentActorAndAttackHasIncomingMotionAtItsActualContactKey() {
        for (opponent in arenaOpponents) for (direction in AttackDirection.values()) {
            val attack = opponent.attackProfile(direction)
            val time = attack.contactSourceSeconds
            val origin = Vector3(2.0, 0.0, -3.0)
            val yaw = 0.7f
            val current = attack.sample(time).inStage(origin, yaw)
            val witness = current.bladeBase * 0.65 + current.bladeTip * 0.35
            val tangent = requireNotNull(attack.bladeTangentAt(time, witness, origin, yaw))
            val prior = attack.sample(time - 1e-6).inStage(origin, yaw)
            val incoming = requireNotNull((witness - (prior.bladeBase * 0.65 + prior.bladeTip * 0.35)).normalizedOrNull())
            assertEquals(1.0, tangent.length(), 1e-9)
            assertTrue("${opponent.name}/$direction must use incoming source motion", tangent.dot(incoming) > 0.999)
        }
    }

    @Test
    fun fastGuardThenRestStillEmitsParryWithIncomingTangentForAllThreeDirections() {
        for (direction in AttackDirection.values()) {
            val fixture = Fixture()
            fixture.start()
            fixture.seek { it.phase == EnemyPhase.STARTUP && it.attackDirection == direction }
            val turn = sqrt(0.5)
            val rotation = if (direction == AttackDirection.OVERHEAD) Quaternion(0.0, -turn, 0.0, turn)
                else Quaternion(turn, 0.0, 0.0, turn)
            val guard = when (direction) {
                AttackDirection.OVERHEAD -> Vector3(-0.4, 1.6, -0.35)
                AttackDirection.LEFT -> Vector3(-0.3, 1.0, -0.35)
                AttackDirection.RIGHT -> Vector3(0.3, 1.0, -0.35)
            }
            // Establish the same orientation out of guard; the later entry is translation, not a tracking jump.
            fixture.hand = guard + Vector3(0.0, 0.0, 0.4)
            fixture.rotation = rotation
            fixture.observe()
            fixture.seek { it.phase == EnemyPhase.ACTIVE && it.attackDirection == direction }
            val id = requireNotNull(fixture.session.viewState.attackId)
            fixture.tick(20_000_000L, guard)
            assertTrue(!fixture.session.viewState.playerBladeAtRest)
            fixture.tick(20_000_000L, guard)
            assertTrue(fixture.session.viewState.playerBladeAtRest)
            fixture.seek { fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().any { e -> e.attackId == id } }
            val resolved = fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().single { it.attackId == id }
            assertEquals(direction.toString(), AttackOutcome.PARRIED, resolved.outcome)
            val impact = fixture.events.filterIsInstance<CombatImpact>().single { it.kind == CombatImpactKind.PARRY }
            assertTrue(fixture.session.viewState.playerBladeAtRest)
            assertEquals(0, impact.appliedDamage)
            assertDirection(Vector3(0.0, 0.0, -1.0), impact.normal)
            assertEquals(1.0, requireNotNull(impact.tangent).length(), 1e-9)
        }
    }

    private fun pose(time: Double, base: Vector3, tip: Vector3) = AttackPoseSample(time, body, base, tip)
    private fun profile(samples: List<AttackPoseSample>) = AttackProfile("attack", listOf(0.0, 0.2, 0.8, 1.2, 2.0), 1.0, samples)
    private fun assertDirection(expected: Vector3, actual: Vector3?) {
        val value = requireNotNull(actual)
        assertEquals(expected.x, value.x, 1e-9)
        assertEquals(expected.y, value.y, 1e-9)
        assertEquals(expected.z, value.z, 1e-9)
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val events = mutableListOf<EnemyCombatEvent>()
        var hand = Vector3(0.3, 1.0, 0.0)
        var rotation = Quaternion(0.0, 0.0, 0.0, 1.0)
        private val tracking = TrackingState(Hand.RIGHT)
        private var now = 1_000_000_000L
        private var sequence = 0L
        init {
            session.setArenaPresenter { _, batch -> events.addAll(batch) }
            session.setEnemyGeometry(Vector3(0.0, 0.0, -1.3), 1.55)
            observe()
        }
        fun observe() {
            fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
            fun send(event: TrackingEvent) {
                val accepted = tracking.accept(event)
                assertTrue(accepted)
                session.onTrackingEvent(event, accepted, tracking.snapshot)
            }
            send(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))))
            send(TrackingEvent.Controllers(stamp(), ObservedPose(Vector3(0.9, 0.6, 0.2), Quaternion(0.0, 0.0, 0.0, 1.0)),
                ObservedPose(hand, rotation)))
        }
        fun start() {
            assertTrue(session.startTrial())
            session.onTick(now)
            tick(3_000_000_000L)
        }
        fun tick(delta: Long, position: Vector3 = hand) {
            now += delta
            hand = position
            observe()
            session.onTick(now)
        }
        fun seek(condition: (ArenaViewState) -> Boolean) {
            repeat(500) {
                if (condition(session.viewState)) return
                tick(25_000_000L)
            }
            throw AssertionError("Expected existing attack phase/event was not reached")
        }
    }
}
