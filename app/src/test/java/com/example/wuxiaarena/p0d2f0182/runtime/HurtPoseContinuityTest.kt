package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
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
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

/** Coordinator-only synthetic inputs; native blend timing and visual quality need device evidence. */
class HurtPoseContinuityTest {
    @Test
    fun bodyAndHeadKeepTheirContactPoseDuringExistingShortStopThenUseTheActualHurtSource() {
        for (zone in listOf(HitZone.BODY, HitZone.HEAD)) {
            val fixture = Fixture()
            fixture.start()
            val y = if (zone == HitZone.HEAD) 1.55 else .70
            // Cut the low torso below the held dao. For the head, use a horizontal
            // blade behind its guard plane so this is a real unshielded hurt fixture.
            if (zone == HitZone.HEAD) {
                val turn = sqrt(.5)
                fixture.rotation = Quaternion(0.0, -turn, 0.0, turn)
            }
            val from = if (zone == HitZone.HEAD) Vector3(-1.35, y, -1.26) else Vector3(-.35, y, -.4)
            val to = if (zone == HitZone.HEAD) Vector3(-.35, y, -1.26) else Vector3(.35, y, -.4)
            fixture.tick(20_000_000L, from)
            val idle = fixture.pose()
            fixture.tick(100_000_000L, to)
            val impacts = fixture.events.filterIsInstance<CombatImpact>()
            assertTrue("Expected unshielded $zone contact; impacts=$impacts", impacts.any { it.appliedDamage > 0 })
            val impact = impacts.single { it.appliedDamage > 0 }
            assertEquals(zone, impact.zone)
            assertEquals(EnemyPhase.HIT, fixture.session.viewState.phase)
            val hold = CombatFeedbackProfile.hitStopNanos(impact)
            assertEquals(if (zone == HitZone.HEAD) 90_000_000L else 70_000_000L, hold)
            assertEquals(idle, fixture.pose())
            fixture.tick(hold / 2)
            assertTrue(fixture.session.viewState.hitStop)
            assertEquals(idle, fixture.pose())
            assertEquals(0L, fixture.session.viewState.phaseElapsedNanos)
            fixture.tick(hold - hold / 2 + 100_000_000L)
            assertTrue(!fixture.session.viewState.hitStop)
            assertEquals(EnemyPhase.HIT, fixture.session.viewState.phase)
            val state = fixture.session.viewState
            assertEquals(zone, state.enemyHitZone)
            val expected = arenaOpponents[0].reactionProfiles().frame(state.hitReaction, zone,
                state.phaseElapsedNanos, state.phaseRemainingNanos)
            assertEquals(if (zone == HitZone.HEAD) "hit_head" else "hit_body", expected.clip)
            assertEquals(expected.pose.inStage(requireNotNull(state.enemyPosition) + state.enemyRecoilOffset,
                state.enemyYawRadians), fixture.pose())
            assertNotEquals(idle.contact, fixture.pose().contact)
        }
    }

    @Test
    fun parryKeepsActualIncomingSourceDuring95msThenRetreatsInTheSameClip() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.STARTUP }
        val turn = sqrt(.5)
        fixture.rotation = Quaternion(0.0, -turn, 0.0, turn)
        fixture.hand = Vector3(-.4, 1.6, .05)
        fixture.observe()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        fixture.tick(20_000_000L, Vector3(-.4, 1.6, -.35))
        fixture.tick(20_000_000L)
        fixture.seek { fixture.events.any { event -> event is CombatImpact && event.kind == CombatImpactKind.PARRY } }
        val impact = fixture.events.filterIsInstance<CombatImpact>().single { it.kind == CombatImpactKind.PARRY }
        val hold = CombatFeedbackProfile.hitStopNanos(impact)
        assertEquals(95_000_000L, hold)
        val stateAtContact = fixture.session.viewState
        val profile = arenaOpponents[0].attackProfile(AttackDirection.OVERHEAD)
        val incoming = profile.sample(requireNotNull(stateAtContact.enemyPoseSourceSeconds))
            .inStage(requireNotNull(stateAtContact.enemyPosition), stateAtContact.enemyYawRadians)
        assertEquals(incoming, fixture.pose())
        fixture.tick(hold / 2)
        assertTrue(fixture.session.viewState.hitStop)
        assertEquals(incoming, fixture.pose())
        fixture.tick(hold - hold / 2 + 100_000_000L)
        val state = fixture.session.viewState
        assertEquals(EnemyPhase.HIT, state.phase)
        assertEquals(profile.clip, state.enemyPoseClip)
        assertTrue(requireNotNull(state.enemyPoseSourceSeconds) < incoming.sourceSeconds)
        assertEquals(profile.sample(requireNotNull(state.enemyPoseSourceSeconds)).inStage(requireNotNull(state.enemyPosition) + state.enemyRecoilOffset,
            state.enemyYawRadians), fixture.pose())
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val events = mutableListOf<EnemyCombatEvent>()
        var hand = Vector3(.3, 1.0, 0.0)
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
            send(TrackingEvent.Controllers(stamp(), ObservedPose(Vector3(.9, .6, .2), Quaternion(0.0, 0.0, 0.0, 1.0)),
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
            throw AssertionError("Expected normal combat phase/event was not reached")
        }
        fun pose(): AttackPoseSample = ArenaSession::class.java.getDeclaredMethod("enemyAttackPose", Long::class.javaPrimitiveType)
            .apply { isAccessible = true }.invoke(session, 0L) as AttackPoseSample
    }
}
