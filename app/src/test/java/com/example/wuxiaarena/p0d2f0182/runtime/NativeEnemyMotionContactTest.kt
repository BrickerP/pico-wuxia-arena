package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

class NativeEnemyMotionContactTest {
    @Test
    fun idleEnemySteelStopsAtActualImpactThenWithdrawsWithoutAnInfiniteMotionFreeze() {
        val fixture = Fixture()
        fixture.start()
        var observedContact = false
        repeat(40) {
            if (observedContact) return@repeat
            val before = fixture.session.viewState
            val beforePosition = requireNotNull(before.enemyPosition)
            val fullEndpoint = beforePosition.z + 0.65 * 0.1
            val previousImpacts = fixture.impacts().size
            fixture.tick(100_000_000L)
            val impacts = fixture.impacts()
            if (impacts.size > previousImpacts) {
                val contact = fixture.session.viewState
                val impact = impacts.last()
                assertEquals(CombatImpactKind.BLOCK, impact.kind)
                assertEquals(EnemyPhase.IDLE, contact.phase)
                val contactPosition = requireNotNull(contact.enemyPosition)
                assertTrue("Actor must advance toward the stationary blade", contactPosition.z >= beforePosition.z)
                assertTrue("Actor origin must stop at TOI before the unchecked frame endpoint",
                    contactPosition.z < fullEndpoint - 1e-6)
                val held = requireNotNull(contact.playerWeaponGrip)
                assertEquals(fixture.rawGrip.position, held.position)
                assertTrue(playerBlade(fixture.rawGrip).base.distanceTo(playerBlade(held).base) < 1e-12)
                assertTrue(playerBlade(fixture.rawGrip).tip.distanceTo(playerBlade(held).tip) < 1e-12)
                assertEquals(fixture.rawGrip.position, fixture.tracking.snapshot.right?.pose?.position)
                assertEquals(0.0, contact.playerBladeTipSpeed, 0.0)
                assertTrue(contact.playerBladeAtRest)
                assertEquals(100, contact.playerHealth)
                assertEquals(100, contact.health)
                assertFalse(fixture.events.any { it is EnemyCombatEvent.AttackStarted })
                observedContact = true
            }
        }
        assertTrue("The moving prepared enemy blade must contact a motionless player blade", observedContact)
        val firstContact = fixture.session.viewState
        val heldBlade = playerBlade(requireNotNull(firstContact.playerWeaponGrip))
        val firstImpact = fixture.impacts().single()
        val originSide = (requireNotNull(firstContact.enemyPosition) - firstImpact.point).dot(firstImpact.normal)
        val geometryTolerance = 0.0006 // 0.5 mm actor-curve envelope plus contact roundoff.
        var sourceAdvanced = false
        var actorWithdrew = false
        var maximumVirtualOffset = 0.0
        var sourceResumedMillis: Int? = null
        var previousState = firstContact
        repeat(300) { index ->
            fixture.tick(10_000_000L)
            val state = fixture.session.viewState
            val player = playerBlade(requireNotNull(state.playerWeaponGrip))
            val (playerAxis, enemyAxis) = requireNotNull(closestSegmentPoints(player.base, player.tip,
                requireNotNull(state.enemyBladeBase), requireNotNull(state.enemyBladeTip)))
            val separation = playerAxis.distanceTo(enemyAxis) - player.radiusMeters - 0.0125
            assertTrue("Persistent steel must not overlap after ${(index + 1) * 10} ms; signed gap=$separation",
                separation >= -geometryTolerance)
            val origin = requireNotNull(state.enemyPosition)
            val currentSide = (origin - firstImpact.point).dot(firstImpact.normal)
            assertTrue("Enemy origin must remain on its original side of the held blade",
                if (originSide < 0.0) currentSide <= geometryTolerance else currentSide >= -geometryTolerance)
            assertTrue("Walking actor must not cross the fixed transverse blade plane",
                origin.z <= heldBlade.base.z + geometryTolerance)
            maximumVirtualOffset = maxOf(maximumVirtualOffset, requireNotNull(state.playerWeaponGrip).position.distanceTo(fixture.rawGrip.position))
            if (sourceResumedMillis == null && state.enemyPoseSourceSeconds != firstContact.enemyPoseSourceSeconds) sourceResumedMillis = (index+1)*10
            assertEquals("Actor withdrawal must not move the held player grip", fixture.rawGrip.position,
                requireNotNull(state.playerWeaponGrip).position)
            assertTrue("The held player blade base must remain at the raw tracked pose",
                player.base.distanceTo(playerBlade(fixture.rawGrip).base) < 1e-12)
            assertTrue("The held player blade tip must remain at the raw tracked pose",
                player.tip.distanceTo(playerBlade(fixture.rawGrip).tip) < 1e-12)
            val stepDistance = origin.distanceTo(requireNotNull(previousState.enemyPosition))
            assertTrue("Actor withdrawal must obey .65 m/s: $stepDistance m per 10ms",
                stepDistance <= .65 * .01 + 1e-9)
            val yawStep = kotlin.math.abs(state.enemyYawRadians.toDouble() - previousState.enemyYawRadians.toDouble())
            assertTrue("Actor withdrawal must obey 1 rad/s: $yawStep rad per 10ms", yawStep <= .01 + 1e-6)
            previousState = state
            assertEquals(fixture.rawGrip.position, fixture.tracking.snapshot.right?.pose?.position)
            assertEquals(fixture.rawGrip.rotation, fixture.tracking.snapshot.right?.pose?.rotation)
            assertEquals(100, state.playerHealth)
            assertEquals(100, state.health)
            assertEquals("Sustained contact must not emit another impact", 1, fixture.impacts().size)
            val retreat = origin.distanceTo(requireNotNull(firstContact.enemyPosition))
            assertTrue("One pressure response must not keep backing the actor away", retreat <= .35 + geometryTolerance)
            actorWithdrew = actorWithdrew || retreat > .001
            sourceAdvanced = sourceAdvanced || (state.enemyPoseSourceSeconds != firstContact.enemyPoseSourceSeconds)
        }
        val afterPressure = fixture.session.viewState
        assertTrue("Weapon pressure must not freeze the simulation clock",
            afterPressure.simulationNanos - firstContact.simulationNanos >= 2_900_000_000L)
        assertTrue("Idle readiness must accrue during the contact hold",
            afterPressure.phaseElapsedNanos - firstContact.phaseElapsedNanos >= 2_900_000_000L)
        assertTrue("The actor must make a finite withdrawal within three seconds", actorWithdrew)
        assertTrue("The displayed/query source must advance within three seconds", sourceAdvanced)
        println("STEEL_RELEASE idle sourceResumedMs=$sourceResumedMillis retreatMm=${requireNotNull(afterPressure.enemyPosition).distanceTo(requireNotNull(firstContact.enemyPosition))*1000} maximumVirtualOffsetMm=${maximumVirtualOffset*1000}")
        assertEquals("Player grip must never be projected to make room for the enemy", 0.0, maximumVirtualOffset, 0.0)
        val withdrawn = requireNotNull(afterPressure.enemyPosition)
        repeat(200) {
            fixture.tick(10_000_000L)
            assertEquals("A static latch cannot farm impacts", 1, fixture.impacts().size)
            assertEquals(100, fixture.session.viewState.health)
            assertEquals(100, fixture.session.viewState.playerHealth)
            assertTrue("Retreat is a single response, not a repeating step",
                requireNotNull(fixture.session.viewState.enemyPosition).distanceTo(withdrawn) <= geometryTolerance)
        }
    }

    @Test
    fun pauseAfterSustainedSteelFreezesBothClocksAndDoesNotReplayTheOldImpactOnResume() {
        val fixture = Fixture()
        fixture.contact()
        fixture.tick(250_000_000L)
        fixture.interrupt(DiscontinuityReason.USER_PAUSED)
        val paused = fixture.session.viewState
        val impacts = fixture.impacts().size
        fixture.tickWithoutObservation(1_000_000_000L)
        assertEquals(paused.simulationNanos, fixture.session.viewState.simulationNanos)
        assertEquals(paused.enemyPoseSourceSeconds, fixture.session.viewState.enemyPoseSourceSeconds)
        assertEquals(paused.enemyPosition, fixture.session.viewState.enemyPosition)
        assertEquals(impacts, fixture.impacts().size)
        fixture.observe()
        assertTrue(fixture.session.confirmResume(requireNotNull(paused.pauseId)))
        fixture.tickWithoutObservation(1_000_000_000L) // re-establish receipt baseline only
        assertEquals(paused.simulationNanos, fixture.session.viewState.simulationNanos)
        assertEquals(impacts, fixture.impacts().size)
        repeat(100) { fixture.tick(10_000_000L) }
        assertEquals("Resume cannot rearm a static already accepted steel episode", impacts, fixture.impacts().size)
    }

    @Test
    fun trackingLossDuringSteelCannotAdvanceOrRepeatThePreviousContact() {
        val fixture = Fixture()
        fixture.contact()
        fixture.loseRequiredHand()
        val paused = fixture.session.viewState
        val impacts = fixture.impacts().size
        assertFalse(paused.inputReady)
        assertEquals(null, paused.playerWeaponGrip)
        fixture.tickWithoutObservation(1_000_000_000L)
        assertEquals(paused.simulationNanos, fixture.session.viewState.simulationNanos)
        assertEquals(paused.enemyPoseSourceSeconds, fixture.session.viewState.enemyPoseSourceSeconds)
        assertEquals(impacts, fixture.impacts().size)
    }

    @Test
    fun slowStaticSeparationDoesNotRearmButAFreshQualifiedSwingCanMakeANewSteelContact() {
        val fixture = Fixture()
        fixture.contact()
        repeat(300) { fixture.tick(10_000_000L) }
        val first = fixture.impacts().single()
        val original = fixture.rawGrip
        repeat(10) { step ->
            fixture.tick(50_000_000L, original.copy(position = original.position + first.normal * ((step + 1) * .01)))
        }
        repeat(10) { step ->
            fixture.tick(50_000_000L, original.copy(position = original.position + first.normal * ((9 - step) * .01)))
        }
        assertEquals("Slow pull-away/return cannot rearm the same stationary pressure", 1, fixture.impacts().size)
        assertEquals(100, fixture.session.viewState.health)
        val state = fixture.session.viewState
        val enemyMiddle = (requireNotNull(state.enemyBladeBase) + requireNotNull(state.enemyBladeTip)) * .5
        val local = playerBlade(original.copy(position = Vector3(0.0, 0.0, 0.0)))
        val center = enemyMiddle - (local.base + local.tip) * .5
        val start = fixture.rawGrip.position
        val outside = center + first.normal * .20
        repeat(20) { step -> fixture.tick(50_000_000L,
            original.copy(position = start + (outside - start) * ((step + 1) / 20.0))) }
        fixture.tick(300_000_000L)
        fixture.tick(40_000_000L, original.copy(position = center - first.normal * .06))
        assertEquals("A real new swing must be eligible for one new steel impact", 2, fixture.impacts().size)
        assertTrue(fixture.impacts().last().kind in setOf(CombatImpactKind.BLOCK, CombatImpactKind.PARRY))
        assertEquals(100, fixture.session.viewState.health)
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val tracking = TrackingState(Hand.RIGHT)
        val events = mutableListOf<EnemyCombatEvent>()
        private var now = 1_000_000_000L
        private var sequence = 0L
        var rawGrip: WeaponGrip
            private set

        init {
            // Fix the player's transverse dao where the walking actor's true sampled
            // blade will arrive after 0.75 m of locomotion, well before attack range.
            val arriving = arenaOpponents.first().locomotionProfile().sample(true, 0.75, 0L)
                .inStage(Vector3(0.0, 0.0, -2.25), 0f)
            val rotation = Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5))
            val localBlade = playerBlade(WeaponGrip(Vector3(0.0, 0.0, 0.0), rotation))
            rawGrip = WeaponGrip((arriving.bladeBase + arriving.bladeTip - localBlade.base - localBlade.tip) * 0.5, rotation)
            session.setArenaPresenter { _, batch -> events.addAll(batch) }
            session.setEnemyGeometry(Vector3(0.0, 0.0, -3.0), 1.55)
            observe()
        }

        fun impacts() = events.filterIsInstance<CombatImpact>()

        private fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)

        private fun send(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }

        fun observe() {
            send(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))))
            send(TrackingEvent.Controllers(stamp(), null, ObservedPose(rawGrip.position, rawGrip.rotation)))
        }

        fun start() {
            assertTrue(session.startTrial())
            session.onTick(now)
            tick(3_000_000_000L)
            assertEquals(TrialResult.FIGHTING, session.viewState.result)
        }

        fun tick(delta: Long, grip: WeaponGrip = rawGrip) {
            now += delta
            rawGrip = grip
            observe()
            session.onTick(now)
        }

        fun tickWithoutObservation(delta: Long) {
            now += delta
            session.onTick(now)
        }

        fun contact() {
            start()
            repeat(40) {
                if (impacts().isNotEmpty()) return
                tick(100_000_000L)
            }
            throw AssertionError("A real approaching blade contact was not reached")
        }

        fun interrupt(reason: DiscontinuityReason) {
            now += 1_000_000L
            send(TrackingEvent.Discontinuity(stamp(), TrackingTarget.ALL, reason))
        }

        fun loseRequiredHand() {
            now += 1_000_000L
            send(TrackingEvent.Controllers(stamp(), null, null))
        }
    }
}
