package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.TrackingTarget
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
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

/** Real prepared attack samples and normal tracking receipts exercise the native session. */
class NativeBladeInteractionTest {
    @Test
    fun correctlyOrientedGuardWithoutSteelContactCannotParry() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.PREPARING }
        fixture.rotation = Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5))
        fixture.hand = Vector3(-1.2, 1.6, -0.35)
        fixture.tick(50_000_000L)
        val recognizer = PlayerCombatResolver()
        val observed = requireNotNull(recognizer.observe(fixture.tracking.snapshot,
            requireNotNull(fixture.session.viewState.enemyPosition)))
        assertEquals(AttackDirection.OVERHEAD, observed.guardDirection)

        val id = requireNotNull(fixture.session.viewState.attackId)
        fixture.seek { fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().any { e -> e.attackId == id } }
        val outcome = fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().single { it.attackId == id }.outcome
        assertFalse(outcome == AttackOutcome.PARRIED || outcome == AttackOutcome.BLOCKED)
        assertTrue(fixture.events.filterIsInstance<CombatImpact>().none {
            it.kind == CombatImpactKind.PARRY || it.kind == CombatImpactKind.BLOCK
        })
    }

    @Test
    fun actualSteelContactStopsWeaponsWithoutPlayerDamageAndKeepsRawTracking() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        val priorHealth = fixture.session.viewState.playerHealth
        val impact = fixture.crossCurrentEnemyBlade()
        assertTrue(impact.kind == CombatImpactKind.BLOCK || impact.kind == CombatImpactKind.PARRY)
        assertEquals(priorHealth, fixture.session.viewState.playerHealth)
        val held = requireNotNull(fixture.session.viewState.playerWeaponGrip)
        val blade = playerBlade(held)
        assertEquals(blade.base, fixture.session.viewState.playerBladeBase)
        assertEquals(blade.tip, fixture.session.viewState.playerBladeTip)
        assertNotEquals(fixture.hand, held.position)
        assertEquals(fixture.hand, fixture.tracking.snapshot.right?.pose?.position)
        assertEquals(fixture.rotation, fixture.tracking.snapshot.right?.pose?.rotation)
    }

    @Test
    fun steelContactHasOneImpactAndOneAttackResolutionAcrossDuplicateTicks() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        val attackId = requireNotNull(fixture.session.viewState.attackId)
        fixture.crossCurrentEnemyBlade()
        val count = fixture.events.filterIsInstance<CombatImpact>().count {
            it.kind == CombatImpactKind.BLOCK || it.kind == CombatImpactKind.PARRY
        }
        repeat(5) { fixture.session.onTick(fixture.now) }
        assertEquals(count, fixture.events.filterIsInstance<CombatImpact>().count {
            it.kind == CombatImpactKind.BLOCK || it.kind == CombatImpactKind.PARRY
        })
        assertEquals(1, fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().count { it.attackId == attackId })
    }

    @Test
    fun lostRequiredHandClearsVirtualGripAndCannotReplayContact() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        fixture.crossCurrentEnemyBlade()
        assertTrue(fixture.session.viewState.playerWeaponGrip != null)
        val impacts = fixture.events.filterIsInstance<CombatImpact>().size
        fixture.loseRightHand()
        assertNull(fixture.session.viewState.playerWeaponGrip)
        assertNull(fixture.session.viewState.playerBladeBase)
        assertNull(fixture.session.viewState.playerBladeTip)
        assertFalse(fixture.session.viewState.actionReady)
        fixture.session.onTick(fixture.now + 50_000_000L)
        assertEquals(impacts, fixture.events.filterIsInstance<CombatImpact>().size)
    }

    @Test
    fun contactKeepsExactSourcePoseThenRetreatsContinuouslyInTheSameClip() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        val impact = fixture.crossCurrentEnemyBlade()
        val contact = fixture.session.viewState
        val source = requireNotNull(contact.enemyPoseSourceSeconds)
        val direction = requireNotNull(contact.enemyPoseDirection)
        val profile = arenaOpponents[contact.roundNumber - 1].attackProfile(direction)
        val expected = profile.sample(source).inStage(requireNotNull(contact.enemyPosition) + contact.enemyRecoilOffset,
            contact.enemyYawRadians)
        assertTrue(expected.bladeBase.distanceTo(requireNotNull(contact.enemyBladeBase)) < 1e-8)
        assertTrue(expected.bladeTip.distanceTo(requireNotNull(contact.enemyBladeTip)) < 1e-8)
        assertTrue(contact.enemyRecoveryFromContact)

        fixture.tick(CombatFeedbackProfile.hitStopNanos(impact) + 10_000_000L)
        assertEquals(source, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 1e-9)
        fixture.tick(35_000_000L)
        val retreated = fixture.session.viewState
        assertEquals(contact.enemyPoseClip, retreated.enemyPoseClip)
        val nextSource = requireNotNull(retreated.enemyPoseSourceSeconds)
        assertTrue("Recovery must start from the actual witness, not a preset key", nextSource < source)
        assertTrue(source - nextSource <= 0.06)
        val nextExpected = profile.sample(nextSource).inStage(requireNotNull(retreated.enemyPosition) + retreated.enemyRecoilOffset,
            retreated.enemyYawRadians)
        assertTrue(nextExpected.bladeBase.distanceTo(requireNotNull(retreated.enemyBladeBase)) < 1e-8)
        assertTrue(nextExpected.bladeTip.distanceTo(requireNotNull(retreated.enemyBladeTip)) < 1e-8)
    }

    @Test
    fun userPauseClearsVirtualWeaponButPreservesExactEnemySourcePose() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        fixture.crossCurrentEnemyBlade()
        val atContact = fixture.session.viewState
        fixture.pause()
        val paused = fixture.session.viewState
        assertNull(paused.playerWeaponGrip)
        assertNull(paused.playerBladeBase)
        assertEquals(atContact.enemyPoseClip, paused.enemyPoseClip)
        assertEquals(atContact.enemyPoseSourceSeconds, paused.enemyPoseSourceSeconds)
        fixture.session.onTick(fixture.now + 500_000_000L)
        assertEquals(paused.enemyPoseSourceSeconds, fixture.session.viewState.enemyPoseSourceSeconds)
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val events = mutableListOf<EnemyCombatEvent>()
        val tracking = TrackingState(Hand.RIGHT)
        var now = 1_000_000_000L
        var hand = Vector3(2.0, 1.3, 0.0)
        var rotation = Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5))
        private var sequence = 0L

        init {
            session.setArenaPresenter { _, batch -> events.addAll(batch) }
            session.setEnemyGeometry(Vector3(0.0, 0.0, -1.3), 1.55)
            observe()
        }

        private fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
        private fun send(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }

        fun observe() {
            send(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))))
            send(TrackingEvent.Controllers(stamp(), ObservedPose(Vector3(-0.9, 0.6, 0.2), Quaternion(0.0, 0.0, 0.0, 1.0)),
                ObservedPose(hand, rotation)))
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

        fun seek(condition: (ArenaViewState) -> Boolean) {
            repeat(500) {
                if (condition(session.viewState)) return
                tick(10_000_000L)
            }
            throw AssertionError("Native attack state was not reached: ${session.viewState}")
        }

        fun crossCurrentEnemyBlade(): CombatImpact {
            val state = session.viewState
            requireNotNull(state.enemyBladeBase)
            requireNotNull(state.enemyBladeTip)
            val setupDirection = requireNotNull(state.attackDirection)
            val setupProfile = arenaOpponents[state.roundNumber - 1].attackProfile(setupDirection)
            val setupTime = setupProfile.sourceSeconds(state.phase, state.phaseElapsedNanos + 80_000_000L,
                requireNotNull(state.phaseRemainingNanos) - 80_000_000L)
            val setupPose = setupProfile.sample(setupTime).inStage(requireNotNull(state.enemyPosition), state.enemyYawRadians)
            val base = setupPose.bladeBase
            val tip = setupPose.bladeTip
            val midpoint = (base + tip) * 0.5
            val localMidpoint = (playerBlade(WeaponGrip(Vector3(0.0, 0.0, 0.0), rotation)).let { it.base + it.tip }) * 0.5
            val playerAxis = requireNotNull(rotation.rotate(Vector3(0.0312, 0.0, -0.72)))
            val normal = requireNotNull((tip - base).cross(playerAxis).normalizedOrNull())
            val centerGrip = midpoint - localMidpoint
            // Establish a valid history outside steel before crossing it at normal controller speed.
            hand = centerGrip + normal * 0.20
            tick(80_000_000L)
            events.filterIsInstance<CombatImpact>().lastOrNull {
                it.kind == CombatImpactKind.BLOCK || it.kind == CombatImpactKind.PARRY
            }?.let { return it }
            // Aim the raw endpoint at the next real source sample. The overhead dao
            // descends substantially during these 20 ms; an old midpoint would be a miss.
            val beforeCrossing = session.viewState
            val direction = requireNotNull(beforeCrossing.attackDirection)
            val profile = arenaOpponents[beforeCrossing.roundNumber - 1].attackProfile(direction)
            val nextTime = profile.sourceSeconds(beforeCrossing.phase,
                beforeCrossing.phaseElapsedNanos + 20_000_000L,
                requireNotNull(beforeCrossing.phaseRemainingNanos) - 20_000_000L)
            val nextPose = profile.sample(nextTime).inStage(requireNotNull(beforeCrossing.enemyPosition), beforeCrossing.enemyYawRadians)
            hand = (nextPose.bladeBase + nextPose.bladeTip) * 0.5 - localMidpoint
            tick(20_000_000L)
            return events.filterIsInstance<CombatImpact>().lastOrNull {
                it.kind == CombatImpactKind.BLOCK || it.kind == CombatImpactKind.PARRY
            } ?: throw AssertionError("No real steel contact; state=${session.viewState}; impacts=${events.filterIsInstance<CombatImpact>()}")
        }

        fun pause() {
            now += 1_000_000L
            send(TrackingEvent.Discontinuity(stamp(), TrackingTarget.ALL, DiscontinuityReason.USER_PAUSED))
        }

        fun loseRightHand() {
            now += 1_000_000L
            send(TrackingEvent.Controllers(stamp(), ObservedPose(Vector3(-0.9, 0.6, 0.2), rotation), null))
        }
    }
}
