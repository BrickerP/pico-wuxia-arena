package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
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
    fun idleEnemyWalkingIntoStillPlayerSteelStopsAtActualTimeOfImpact() {
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
        repeat(100) { index ->
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
            assertEquals(fixture.rawGrip.position, state.playerWeaponGrip?.position)
            assertEquals(100, state.playerHealth)
            assertEquals(100, state.health)
            assertEquals("Sustained contact must not emit another impact", 1, fixture.impacts().size)
            assertTrue("Weapon pressure must arrest the actor", origin.distanceTo(requireNotNull(firstContact.enemyPosition)) < 1e-10)
            assertEquals(firstContact.enemyPoseClip, state.enemyPoseClip)
            assertEquals(firstContact.enemyPoseSourceSeconds, state.enemyPoseSourceSeconds)
            assertEquals(firstContact.enemyGaitMeters, state.enemyGaitMeters, 1e-12)
        }
        val afterPressure = fixture.session.viewState
        assertTrue("Weapon pressure must not freeze the simulation clock",
            afterPressure.simulationNanos - firstContact.simulationNanos >= 900_000_000L)
        assertTrue("Idle readiness must accrue during the contact hold",
            afterPressure.phaseElapsedNanos - firstContact.phaseElapsedNanos >= 900_000_000L)
        val combat = ArenaSession::class.java.getDeclaredField("combat").apply { isAccessible = true }
            .get(fixture.session) as EnemyCombatStateMachine
        assertTrue(combat.canStartAttack(true))
        assertFalse(afterPressure.canStartAttack == true) // This fixture's held actor is still outside real attack range.
    }

    private class Fixture {
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        val tracking = TrackingState(Hand.RIGHT)
        val events = mutableListOf<EnemyCombatEvent>()
        private var now = 1_000_000_000L
        private var sequence = 0L
        val rawGrip: WeaponGrip

        init {
            // Fix the player's transverse dao where the walking actor's true sampled
            // blade will arrive after 0.75 m of locomotion, well before attack range.
            val arriving = arenaOpponents.first().locomotionProfile().sample(true, 0.75)
                .inStage(Vector3(0.0, 0.0, -2.25), 0f)
            val rotation = Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5))
            val localBlade = playerBlade(WeaponGrip(Vector3(0.0, 0.0, 0.0), rotation))
            rawGrip = WeaponGrip((arriving.bladeBase + arriving.bladeTip - localBlade.base - localBlade.tip) * 0.5, rotation)
            session.setArenaPresenter { _, batch -> events.addAll(batch) }
            session.setEnemyGeometry(Vector3(0.0, 0.0, -3.0), 1.55)
            observe()
        }

        fun impacts() = events.filterIsInstance<CombatImpact>()

        private fun observe() {
            fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
            fun send(event: TrackingEvent) {
                val accepted = tracking.accept(event)
                assertTrue(accepted)
                session.onTrackingEvent(event, accepted, tracking.snapshot)
            }
            send(TrackingEvent.Head(stamp(), ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0))))
            send(TrackingEvent.Controllers(stamp(), null, ObservedPose(rawGrip.position, rawGrip.rotation)))
        }

        fun start() {
            assertTrue(session.startTrial())
            session.onTick(now)
            tick(3_000_000_000L)
            assertEquals(TrialResult.FIGHTING, session.viewState.result)
        }

        fun tick(delta: Long) {
            now += delta
            observe()
            session.onTick(now)
        }
    }
}
