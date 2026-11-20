package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.BladeContact
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.combat.playerBladeAxis
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
    @Test fun releasedSteelOutsideReachResumesWalkingAfterASlowWithdrawal() {
        val fixture = Fixture(-1.677393948)
        val idle = fixture.session.viewState
        val midpoint = (requireNotNull(idle.enemyBladeBase) + requireNotNull(idle.enemyBladeTip)) * .5
        val local = playerBlade(WeaponGrip(Vector3(0.0, 0.0, 0.0), fixture.rotation)).maxBy { it.base.distanceTo(it.tip) }
        fixture.hand = midpoint - (local.base + local.tip) * .5
        fixture.start()
        for (name in listOf("steelContactLatched", "steelGuardReleased")) {
            ArenaSession::class.java.getDeclaredField(name).apply { isAccessible = true }.setBoolean(fixture.session, true)
        }
        val origin = fixture.session.viewState.enemyPosition
        repeat(40) { fixture.tick(10_000_000) }
        assertEquals("Walking into the stationary blade must be vetoed", origin, fixture.session.viewState.enemyPosition)
        assertEquals(false, fixture.session.viewState.targetInRange)
        assertTrue(fixture.events.none { it is CombatImpact })
        repeat(160) {
            fixture.hand += Vector3(0.0, 0.0, .002)
            fixture.tick(10_000_000)
            if (fixture.session.viewState.phase == EnemyPhase.PREPARING) {
                assertEquals(true, fixture.session.viewState.targetInRange)
                assertEquals(fixture.hand, fixture.session.viewState.playerWeaponGrip?.position)
                assertTrue(fixture.events.none { it is CombatImpact })
                return
            }
        }
        throw AssertionError("A released opponent never re-entered reach of the stationary head")
    }
    @Test
    fun startupGuardRequiresTheContactedPartOfTheEnemyBladeToAdvance() {
        val before = arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD).samples.first()
        val inward = Vector3(.01, 0.0, 0.0)
        val after = before.copy(bladeBase = before.bladeBase + inward, bladeTip = before.bladeTip - inward)
        val normal = Vector3(1.0, 0.0, 0.0)
        val touch = BladeContact(.5, before.bladeBase, before.bladeBase,
            normal, inward * -1.0, .5, .1, 0.0, 0.0)
        assertTrue(startupBladeClosesOnGuard(before, after, touch))
        assertFalse(startupBladeClosesOnGuard(before, after, touch.copy(enemyAxisFraction = .9)))
        assertFalse(startupBladeClosesOnGuard(before, after, touch.copy(relativeDisplacement = inward)))
        assertFalse(startupBladeClosesOnGuard(before, before, touch))
    }

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
        assertTrue(fixture.events.filterIsInstance<CombatImpact>().none { it.kind.isSteelContact() })
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
        val blade = playerBladeAxis(held)
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
        val impact = fixture.crossCurrentEnemyBlade()
        val afterImpact = fixture.session.viewState
        assertEquals(if (impact.kind == CombatImpactKind.PARRY) 94 else 72, afterImpact.playerStamina)
        val count = fixture.events.filterIsInstance<CombatImpact>().count { it.kind.isSteelContact() }
        assertEquals(1, count)
        repeat(5) { fixture.session.onTick(fixture.now) }
        assertEquals(afterImpact.playerStamina, fixture.session.viewState.playerStamina)
        assertEquals(count, fixture.events.filterIsInstance<CombatImpact>().count { it.kind.isSteelContact() })
        assertEquals(1, fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().count { it.attackId == attackId })
    }

    @Test
    fun lateSteelContactFinishesTheCurrentRecoveryBeforeReturningToIdle() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.RECOVERING && requireNotNull(it.phaseRemainingNanos) <= 260_000_000L }
        val attackId = requireNotNull(fixture.session.viewState.attackId)
        val profile = arenaOpponents.first().attackProfile(requireNotNull(fixture.session.viewState.attackDirection))
        val impact = fixture.crossCurrentEnemyBlade()
        assertEquals(CombatImpactKind.STEEL_TOUCH, impact.kind)
        assertEquals(0, impact.appliedDamage)
        var last = fixture.session.viewState
        assertFalse(last.hitStop)
        assertEquals(100, last.playerStamina)
        assertFalse(last.feedback == CombatFeedback.BLOCK)
        assertEquals(EnemyPhase.RECOVERING, last.phase)
        assertTrue(requireNotNull(last.phaseRemainingNanos) < 260_000_000L)
        repeat(600) {
            fixture.tick(5_000_000L)
            val next = fixture.session.viewState
            if (next.phase == EnemyPhase.IDLE) {
                assertEquals("The last visible attack sample must be within one 5ms tick of guard",
                    profile.sourcePhaseSeconds.last(), requireNotNull(last.enemyPoseSourceSeconds), .015)
                assertEquals(1, fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().count { it.attackId == attackId })
                return
            }
            assertEquals(EnemyPhase.RECOVERING, next.phase)
            last = next
        }
        throw AssertionError("The late contact did not release the recovering attack")
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
    fun contactKeepsExactSourcePoseThenRetreatsContinuouslyAfterPlayerWithdrawal() {
        val fixture = Fixture()
        fixture.start()
        fixture.seek { it.phase == EnemyPhase.ACTIVE }
        val impact = fixture.crossCurrentEnemyBlade()
        val contact = fixture.session.viewState
        val source = requireNotNull(contact.enemyPoseSourceSeconds)
        val direction = requireNotNull(contact.enemyPoseDirection)
        val profile = arenaOpponents[contact.roundNumber - 1].attackProfile(direction)
        assertTrue("Contact must occur inside the actual active source interval",
            source > profile.sourcePhaseSeconds[2] && source < profile.sourcePhaseSeconds[3])
        assertTrue("The source witness must exercise interpolation between authored keys",
            profile.samples.none { kotlin.math.abs(it.sourceSeconds - source) < 1e-9 })
        fun assertSourcePose(state: ArenaViewState) {
            assertEquals(contact.enemyPoseClip, state.enemyPoseClip)
            val expected = profile.sample(requireNotNull(state.enemyPoseSourceSeconds)).inStage(
                requireNotNull(state.enemyPosition) + state.enemyRecoilOffset, state.enemyYawRadians)
            assertTrue(expected.bladeBase.distanceTo(requireNotNull(state.enemyBladeBase)) < 1e-8)
            assertTrue(expected.bladeTip.distanceTo(requireNotNull(state.enemyBladeTip)) < 1e-8)
        }
        assertSourcePose(contact)

        fixture.tick(CombatFeedbackProfile.hitStopNanos(impact) + 10_000_000L)
        assertEquals(source, requireNotNull(fixture.session.viewState.enemyPoseSourceSeconds), 1e-9)
        // Continuous nonpenetration may hold a recovery that still presses into the dao.
        // Withdraw the real raw target along the witnessed separating normal before
        // asserting that the same clip can unload and continue from its actual TOI.
        fixture.hand = requireNotNull(contact.playerWeaponGrip).position + impact.normal * 0.15
        fixture.tick(35_000_000L)
        var retreated = fixture.session.viewState
        var elapsedAfterHitStop = 45_000_000L
        var previousSource = requireNotNull(retreated.enemyPoseSourceSeconds)
        val step = 5_000_000L
        val holdLimit = 220_000_000L
        val contactStop = 35_000_000L
        val maximumSourceStep = .06 * step /
            ((requireNotNull(contact.phaseRemainingNanos) - contactStop) * .18)
        fun advanceRecovery() {
            fixture.tick(step)
            elapsedAfterHitStop += step
            retreated = fixture.session.viewState
            assertSourcePose(retreated)
            val currentSource = requireNotNull(retreated.enemyPoseSourceSeconds)
            assertTrue("Recovery cannot jump away from the real TOI witness",
                currentSource <= previousSource + 1e-9 && currentSource >= source - .06 - 1e-9)
            assertTrue("The original recovery must retreat continuously at its authored source rate",
                previousSource - currentSource <= maximumSourceStep + 1e-9)
            previousSource = currentSource
            assertEquals("One overlap cannot replay a steel impact", 1,
                fixture.events.filterIsInstance<CombatImpact>().count { it.kind.isSteelContact() })
            assertEquals(contact.health, retreated.health)
            assertEquals(contact.playerHealth, retreated.playerHealth)
        }
        // A whole-face chain can make the immediate actor exit unprovable. The
        // existing 220 ms return must then release the hand before the same clip
        // resumes its original 35 ms contact stop and continuous retreat.
        while (elapsedAfterHitStop < holdLimit) advanceRecovery()
        val released = requireNotNull(retreated.playerWeaponGrip)
        assertEquals("Unprovable contact must return the real hand within 220 ms", fixture.hand, released.position)
        val trackedRotation = requireNotNull(fixture.rotation.normalizedOrNull())
        val releasedRotation = requireNotNull(released.rotation.normalizedOrNull())
        assertEquals("Returning the hand must also preserve its tracked orientation", 1.0, kotlin.math.abs(
            trackedRotation.x * releasedRotation.x + trackedRotation.y * releasedRotation.y +
                trackedRotation.z * releasedRotation.z + trackedRotation.w * releasedRotation.w), 1e-12)
        val resumeDeadline = holdLimit + contactStop + step
        while (previousSource >= source && elapsedAfterHitStop < resumeDeadline) advanceRecovery()
        assertTrue("Recovery must resume from the actual witness within the bounded return, not freeze forever",
            previousSource < source)
        assertTrue(source - previousSource <= 0.06)
        assertSourcePose(retreated)
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

    private class Fixture(private val spawnZ: Double = -1.3) {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val events = mutableListOf<EnemyCombatEvent>()
        val tracking = TrackingState(Hand.RIGHT)
        var now = 1_000_000_000L
        var hand = Vector3(2.0, 1.3, 0.0)
        var rotation = Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5))
        private var sequence = 0L

        init {
            session.setArenaPresenter { _, batch -> events.addAll(batch) }
            session.setEnemyGeometry(Vector3(0.0, 0.0, spawnZ), 1.55)
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
            val selectPose = ArenaSession::class.java.getDeclaredMethod("enemyAttackPose", java.lang.Long.TYPE)
                .apply { isAccessible = true }
            val setupPose = selectPose.invoke(session, 80_000_000L) as AttackPoseSample
            val base = setupPose.bladeBase
            val tip = setupPose.bladeTip
            val midpoint = (base + tip) * 0.5
            val localParts = playerBlade(WeaponGrip(Vector3(0.0, 0.0, 0.0), rotation))
            val reference = localParts.maxBy { it.base.distanceTo(it.tip) }
            val localMidpoint = (reference.base + reference.tip) * 0.5
            val playerAxis = reference.tip - reference.base
            val normal = requireNotNull((tip - base).cross(playerAxis).normalizedOrNull())
            val centerGrip = midpoint - localMidpoint
            // Establish a valid history outside steel before crossing it at normal controller speed.
            hand = centerGrip + normal * 0.20
            tick(80_000_000L)
            events.filterIsInstance<CombatImpact>().lastOrNull { it.kind.isSteelContact() }?.let { return it }
            // Aim the raw endpoint at the next real source sample. The overhead dao
            // descends substantially during these 20 ms; an old midpoint would be a miss.
            val nextPose = selectPose.invoke(session, 20_000_000L) as AttackPoseSample
            hand = (nextPose.bladeBase + nextPose.bladeTip) * 0.5 - localMidpoint
            tick(20_000_000L)
            return events.filterIsInstance<CombatImpact>().lastOrNull { it.kind.isSteelContact() }
                ?: throw AssertionError("No real steel contact; state=${session.viewState}; impacts=${events.filterIsInstance<CombatImpact>()}")
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

private fun CombatImpactKind.isSteelContact() =
    this == CombatImpactKind.BLOCK || this == CombatImpactKind.PARRY || this == CombatImpactKind.STEEL_TOUCH
