package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
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
        fixture.observe(Vector3(0.0, 1.6, 0.0))
        fixture.events.clear()
        fixture.start()
        repeat(20) { fixture.tick(50_000_000L) }
        assertEquals(AttackDirection.OVERHEAD, fixture.events.filterIsInstance<EnemyCombatEvent.AttackStarted>().single().direction)
    }

    @Test
    fun resolvedNormalAttacksKeepCurrentBodyBladeAndContactFeedbackOnTheSameSourceClock() {
        val fixture = Fixture()
        fixture.start()
        repeat(3) {
            fixture.seek { it.phase == EnemyPhase.ACTIVE }
            fixture.crossCurrentEnemyBlade()
            fixture.seek { it.phase == EnemyPhase.IDLE }
        }
        val contacts = fixture.contactsAtResolution.take(3)
        assertEquals(3, contacts.size)
        for ((state, batch, body) in contacts) {
            assertTrue(state.enemyRecoveryFromContact)
            assertTrue(state.phaseElapsedNanos >= 0L)
            val profile = arenaOpponents[state.roundNumber - 1].attackProfile(requireNotNull(state.enemyPoseDirection))
            val origin = requireNotNull(state.enemyPosition) + state.enemyRecoilOffset
            val sourceSeconds = requireNotNull(state.enemyPoseSourceSeconds)
            assertEquals(profile.clip, state.enemyPoseClip)
            val expected = profile.sample(sourceSeconds).inStage(origin, state.enemyYawRadians)
            assertEquals(expected.contact, body)
            assertEquals(expected.bladeBase, state.enemyBladeBase)
            assertEquals(expected.bladeTip, state.enemyBladeTip)
            val point = batch.filterIsInstance<CombatImpact>().single().point
            assertTrue("${state.enemyPoseDirection}: distance=${expected.nearestBladePoint(point).distanceTo(point)} source=$sourceSeconds impact=${batch.filterIsInstance<CombatImpact>().single()}", expected.nearestBladePoint(point).distanceTo(point) <= 0.013)
        }
    }

    private class Fixture(position: Vector3 = Vector3(0.0, 0.0, -1.3)) {
        val session = ArenaSession(logMessage = {})
        val events = mutableListOf<EnemyCombatEvent>()
        val contactsAtResolution = mutableListOf<Triple<ArenaViewState, List<EnemyCombatEvent>, EnemyContactPose?>>()
        private val tracking = TrackingState(Hand.RIGHT)
        private var now = 1_000_000_000L
        private var sequence = 0L
        private var rotation = Quaternion(0.0, 0.0, 0.0, 1.0)
        private var playerHead = Vector3(0.0, 1.6, 0.0)
        private var playerHand = Vector3(2.0, 1.3, 0.0)

        init {
            session.setArenaPresenter { state, batch ->
                events.addAll(batch)
                if (batch.any { it is EnemyCombatEvent.AttackResolved } && batch.any { it is CombatImpact }) {
                    val method = ArenaSession::class.java.getDeclaredMethod("enemyContactPose").apply { isAccessible = true }
                    contactsAtResolution += Triple(state, batch, method.invoke(session) as EnemyContactPose?)
                }
            }
            session.setEnemyGeometry(position, 1.55)
            observe()
        }

        fun seek(condition: (ArenaViewState) -> Boolean) {
            repeat(500) {
                if (condition(session.viewState)) return
                tick(10_000_000L)
            }
            throw AssertionError("Native attack state was not reached")
        }
        fun crossCurrentEnemyBlade() {
            val turn = kotlin.math.sqrt(0.5)
            rotation = Quaternion(0.0, -turn, 0.0, turn)
            val state = session.viewState
            val profile = arenaOpponents[state.roundNumber - 1].attackProfile(requireNotNull(state.attackDirection))
            val future = profile.sourceSeconds(state.phase, state.phaseElapsedNanos + 80_000_000L,
                requireNotNull(state.phaseRemainingNanos) - 80_000_000L)
            val pose = profile.sample(future).inStage(requireNotNull(state.enemyPosition), state.enemyYawRadians)
            val local = playerBlade(WeaponGrip(Vector3(0.0, 0.0, 0.0), rotation))
            val mid = (local.base + local.tip) * 0.5
            val normal = requireNotNull((pose.bladeTip - pose.bladeBase).cross(local.tip - local.base).normalizedOrNull())
            val before = contactsAtResolution.size
            playerHand = (pose.bladeBase + pose.bladeTip) * 0.5 - mid + normal * 0.20
            tick(80_000_000L)
            if (contactsAtResolution.size > before) return
            val current = session.viewState
            val source = profile.sourceSeconds(current.phase, current.phaseElapsedNanos + 20_000_000L,
                requireNotNull(current.phaseRemainingNanos) - 20_000_000L)
            val next = profile.sample(source).inStage(requireNotNull(current.enemyPosition), current.enemyYawRadians)
            playerHand = (next.bladeBase + next.bladeTip) * 0.5 - mid
            tick(20_000_000L)
            assertEquals(before + 1, contactsAtResolution.size)
            playerHand = Vector3(2.0, 1.3, 0.0)
        }

        fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
        fun send(event: TrackingEvent) = session.onTrackingEvent(event, tracking.accept(event), tracking.snapshot)
        fun observe(head: Vector3 = playerHead) {
            playerHead = head
            send(TrackingEvent.Head(stamp(), ObservedPose(head, rotation)))
            send(TrackingEvent.Controllers(stamp(),
                ObservedPose(Vector3(-0.25, 1.2, -0.35), rotation),
                ObservedPose(playerHand, rotation)))
        }
        fun start() {
            assertTrue(session.startTrial())
            session.onTick(now)
            tick(3_000_000_000L)
        }
        fun tick(delta: Long) {
            now += delta
            observe()
            session.onTick(now)
        }
    }
}
