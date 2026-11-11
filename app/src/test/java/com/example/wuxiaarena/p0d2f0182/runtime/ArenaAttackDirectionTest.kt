package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.CombatImpact
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
import org.junit.Assert.assertTrue
import org.junit.Test

class ArenaAttackDirectionTest {
    @Test
    fun normalEntryUsesAllThreeDirectionsAndResolvesEachAttackOnlyOnce() {
        val fixture = Fixture()
        fixture.start()
        repeat(150) { fixture.tick(50_000_000L) }

        val started = fixture.events.filterIsInstance<EnemyCombatEvent.AttackStarted>().take(3)
        assertEquals(listOf(AttackDirection.OVERHEAD, AttackDirection.LEFT, AttackDirection.RIGHT), started.map { it.direction })
        val resolved = fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>()
        for (attack in started) assertEquals(1, resolved.count { it.attackId == attack.attackId })
        assertTrue(started.none { it.counterattack })
    }

    @Test
    fun unsuccessfulAttemptsAndRepeatedPresentationDoNotConsumeDirectionsAndResetRestartsSequence() {
        val fixture = Fixture(Vector3(0.0, 0.0, -100.0))
        fixture.start()
        repeat(40) {
            fixture.tick(50_000_000L)
            fixture.session.setArenaPresenter { _, batch -> fixture.events.addAll(batch) }
        }
        assertTrue(fixture.events.none { it is EnemyCombatEvent.AttackStarted })

        val enemy = requireNotNull(fixture.session.viewState.enemyPosition)
        fixture.observe(Vector3(enemy.x, 1.6, enemy.z + 1.3))
        repeat(25) { fixture.tick(50_000_000L) }
        assertEquals(AttackDirection.OVERHEAD, fixture.events.filterIsInstance<EnemyCombatEvent.AttackStarted>().single().direction)

        fixture.send(TrackingEvent.Discontinuity(
            fixture.stamp(), TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET,
        ))
        fixture.session.setEnemyGeometry(Vector3(0.0, 0.0, -1.3), 1.55)
        fixture.observe()
        fixture.events.clear()
        fixture.start()
        repeat(20) { fixture.tick(50_000_000L) }
        assertEquals(AttackDirection.OVERHEAD, fixture.events.filterIsInstance<EnemyCombatEvent.AttackStarted>().single().direction)
    }

    @Test
    fun resolvedNormalAttacksKeepCurrentBodyBladeAndContactFeedbackOnTheSameSourceClock() {
        val fixture = Fixture()
        fixture.start()
        repeat(150) { fixture.tick(50_000_000L) }
        val contacts = fixture.contactsAtResolution.take(3)
        assertEquals(3, contacts.size)
        for ((state, batch, body) in contacts) {
            assertTrue(state.enemyRecoveryFromContact)
            assertTrue(state.phaseElapsedNanos >= 0L)
            val profile = arenaOpponents[state.roundNumber - 1].attackProfile(requireNotNull(state.attackDirection))
            val origin = requireNotNull(state.enemyPosition) + state.enemyRecoilOffset
            val sourceSeconds = profile.sourceSeconds(state.phase, state.phaseElapsedNanos,
                state.phaseRemainingNanos, state.enemyRecoveryFromContact)
            val expected = profile.sample(sourceSeconds).inStage(origin, state.enemyYawRadians)
            assertEquals(expected.contact, body)
            assertEquals(expected.bladeBase, state.enemyBladeBase)
            assertEquals(expected.bladeTip, state.enemyBladeTip)
            val point = batch.filterIsInstance<CombatImpact>().single().point
            val contactPose = profile.sample(1.0).inStage(origin, state.enemyYawRadians)
            assertTrue(contactPose.nearestBladePoint(point).distanceTo(point) < 1e-9)
        }
    }

    private class Fixture(position: Vector3 = Vector3(0.0, 0.0, -1.3)) {
        val session = ArenaSession(logMessage = {})
        val events = mutableListOf<EnemyCombatEvent>()
        val contactsAtResolution = mutableListOf<Triple<ArenaViewState, List<EnemyCombatEvent>, EnemyContactPose?>>()
        private val tracking = TrackingState(Hand.RIGHT)
        private var now = 1_000_000_000L
        private var sequence = 0L
        private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

        init {
            session.setArenaPresenter { state, batch ->
                events.addAll(batch)
                if (batch.any { it is EnemyCombatEvent.AttackResolved }) {
                    val method = ArenaSession::class.java.getDeclaredMethod("enemyContactPose").apply { isAccessible = true }
                    contactsAtResolution += Triple(state, batch, method.invoke(session) as EnemyContactPose?)
                }
            }
            session.setEnemyGeometry(position, 1.55)
            observe()
        }

        fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
        fun send(event: TrackingEvent) = session.onTrackingEvent(event, tracking.accept(event), tracking.snapshot)
        fun observe(head: Vector3 = Vector3(0.0, 1.6, 0.0)) {
            send(TrackingEvent.Head(stamp(), ObservedPose(head, rotation)))
            send(TrackingEvent.Controllers(stamp(),
                ObservedPose(Vector3(-0.25, 1.2, -0.35), rotation),
                ObservedPose(Vector3(0.25, 1.2, -0.35), rotation)))
        }
        fun start() {
            assertTrue(session.startTrial())
            session.onTick(now)
            tick(3_000_000_000L)
        }
        fun tick(delta: Long) {
            now += delta
            session.onTick(now)
        }
    }
}
