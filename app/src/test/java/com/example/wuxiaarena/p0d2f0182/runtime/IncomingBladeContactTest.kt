package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
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
import com.example.wuxiaarena.core.math.closestPoint
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
        val q=Quaternion(0.0,0.0,0.0,1.0);val chain=DaoBladeShape.shape
        val before=WeaponGrip(Vector3(-1.0,0.0,0.0),q);val key=WeaponGrip(zero,q)
        val target=chain.at(key)[7].let { BladeSegment((it.base+it.tip)*.5,(it.base+it.tip)*.5,.001) }
        val arriving=checkNotNull(firstBladeShapeBodyContact(BladeShapeSweep(chain,before,key,0.0),BladeSweep(target,target)))
        val recoil=checkNotNull(firstBladeShapeBodyContact(BladeShapeSweep(chain,key,before,0.0),BladeSweep(target,target)))
        assertDirection(Vector3(1.0,0.0,0.0),arriving.contact.relativeDisplacement.normalizedOrNull())
        assertDirection(Vector3(-1.0,0.0,0.0),recoil.contact.relativeDisplacement.normalizedOrNull())
        val yaw=Quaternion(0.0,kotlin.math.sin(PI/4),0.0,kotlin.math.cos(PI/4));val origin=Vector3(3.0,.2,-4.0)
        fun stage(g:WeaponGrip)=WeaponGrip(origin+checkNotNull(yaw.rotate(g.position)),yaw*g.rotation)
        val point=origin+checkNotNull(yaw.rotate(target.base));val sphere=BladeSegment(point,point,.001)
        val rotated=checkNotNull(firstBladeShapeBodyContact(BladeShapeSweep(chain,stage(before),stage(key),0.0),BladeSweep(sphere,sphere)))
        assertTrue(checkNotNull(rotated.contact.relativeDisplacement.normalizedOrNull()).z<-.999999)
    }
    @Test
    fun contactWitnessUsesItsOwnBladeFractionWhenTheTipStaysStill() {
        val chain=DaoBladeShape.shape;val before=WeaponGrip(zero,Quaternion(0.0,0.0,0.0,1.0))
        val tip=playerBlade(before).tip;val q=Quaternion(0.0,kotlin.math.sin(.05),0.0,kotlin.math.cos(.05))
        val after=WeaponGrip(tip-checkNotNull(q.rotate(tip)),q)
        assertTrue(playerBlade(after).tip.distanceTo(tip)<1e-12)
        val part=chain.at(before)[12];val point=(part.base+part.tip)*.5;val sphere=BladeSegment(point,point,.001)
        val hit=checkNotNull(firstBladeShapeBodyContact(BladeShapeSweep(chain,before,after,0.0),BladeSweep(sphere,sphere)))
        assertTrue(checkNotNull(hit.contact.relativeDisplacement.normalizedOrNull()).x>.9)
        assertTrue(hit.playerPartIndex in 0..17);assertTrue(hit.contact.playerAxisFraction in 0.0..1.0)
    }
    @Test
    fun missingIntervalsRestAndDegenerateBladesCannotInventASparkDirection() {
        val g=WeaponGrip(zero,Quaternion(0.0,0.0,0.0,1.0));val chain=DaoBladeShape.shape
        val point=chain.at(g)[12].base;val sphere=BladeSegment(point,point,.001)
        val still=checkNotNull(firstBladeShapeBodyContact(BladeShapeSweep(chain,g,g,0.0),BladeSweep(sphere,sphere)))
        assertNull(still.contact.relativeDisplacement.normalizedOrNull())
        assertNull(checkNotNull(firstBladeContact(BladeSweep(sphere,sphere),BladeSweep(sphere,sphere))).relativeDisplacement.normalizedOrNull())
        assertThrows(IllegalArgumentException::class.java) {BladeShapeSweep(chain,g,g,Double.NaN)}
    }
    @Test
    fun everyCurrentActorAndAttackHasIncomingMotionAtItsActualContactKey() {
        val chain=DaoBladeShape.shape;val origin=Vector3(2.0,0.0,-3.0)
        for(opponent in arenaOpponents)for(direction in AttackDirection.entries) {
            val profile=opponent.attackProfile(direction);val time=profile.contactSourceSeconds
            val prior=profile.sample(time-1e-6).inStage(origin,.7f);val current=profile.sample(time).inStage(origin,.7f)
            val p=chain.at(current.bladeGrip)[10];val point=(p.base+p.tip)*.5;val sphere=BladeSegment(point,point,.001)
            val hit=checkNotNull(firstBladeShapeBodyContact(BladeShapeSweep(chain,prior.bladeGrip,current.bladeGrip,
                maxOf(prior.bladeGripInterpolationErrorToNextMeters,current.bladeGripInterpolationErrorToNextMeters)),BladeSweep(sphere,sphere)))
            val a=chain.at(prior.bladeGrip)[hit.playerPartIndex];val b=chain.at(current.bladeGrip)[hit.playerPartIndex]
            val u=hit.contact.playerAxisFraction
            val incoming=checkNotNull(((b.base-a.base)*(1-u)+(b.tip-a.tip)*u).normalizedOrNull())
            val tangent=checkNotNull(hit.contact.relativeDisplacement.normalizedOrNull())
            assertEquals(1.0,tangent.length(),1e-9);assertTrue(tangent.dot(incoming)>.999)
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
            // Establish orientation first, then record the fast guard admission before
            // contact. Its receipt must not be borrowed backward from the colliding frame.
            val staging = (guard + Vector3(0.0, 0.0, 0.23)).let {
                if (direction == AttackDirection.RIGHT) it.copy(y = 0.0) else it
            }
            fixture.hand = if (direction == AttackDirection.OVERHEAD) staging + Vector3(0.0, -0.4, 0.0)
                else staging.copy(x = 0.0)
            fixture.rotation = rotation
            fixture.observe()
            fixture.seek { it.phase == EnemyPhase.STARTUP && it.attackDirection == direction &&
                requireNotNull(it.phaseRemainingNanos) <= 60_000_000L }
            fixture.tick(20_000_000L, staging)
            fixture.seek { it.phase == EnemyPhase.ACTIVE && it.attackDirection == direction }
            val id = requireNotNull(fixture.session.viewState.attackId)
            fixture.tick(if (direction == AttackDirection.RIGHT) 40_000_000L else 20_000_000L, guard)
            fixture.tick(20_000_000L, guard)
            assertTrue(fixture.session.viewState.playerBladeAtRest)
            fixture.seek { fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().any { e -> e.attackId == id } }
            val resolved = fixture.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().single { it.attackId == id }
            assertEquals(direction.toString(), AttackOutcome.PARRIED, resolved.outcome)
            val impact = fixture.events.filterIsInstance<CombatImpact>().single { it.kind == CombatImpactKind.PARRY }
            assertTrue(fixture.session.viewState.playerBladeAtRest)
            assertEquals(0, impact.appliedDamage)
            // The contact normal is the actual steel separation, rather than the old
            // fabricated head-to-enemy direction. Both rendered blades must witness it.
            val state = fixture.session.viewState
            assertEquals(1.0, impact.normal.length(), 1e-9)
            val stagePose=ArenaSession::class.java.getDeclaredMethod("enemyAttackPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(fixture.session,0L) as AttackPoseSample
            fun gap(grip:WeaponGrip)=DaoBladeShape.shape.at(grip).minOf {part->impact.point.distanceTo(closestPoint(impact.point,part.base,part.tip))-part.radiusMeters}
            val envelope=stagePose.bladeGripInterpolationErrorToNextMeters+.000501
            assertTrue(gap(checkNotNull(state.playerWeaponGrip))<=envelope)
            assertTrue(gap(stagePose.bladeGrip)<=envelope)
            assertEquals(1.0, requireNotNull(impact.tangent).length(), 1e-9)
        }
    }

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
                // Reach each phase boundary exactly. A fixed 25ms step can skip the
                // first incoming steel crossing before the fixture raises its guard.
                val untilTransition = session.viewState.phaseRemainingNanos?.coerceAtLeast(1L)
                    ?: 25_000_000L
                tick(minOf(25_000_000L, untilTransition))
            }
            throw AssertionError("Expected existing attack phase/event was not reached")
        }
    }
}
