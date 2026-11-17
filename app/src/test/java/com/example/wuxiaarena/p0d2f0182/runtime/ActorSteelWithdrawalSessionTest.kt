package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.abs
import kotlin.math.sqrt

/** Regression for the archived real OVERHEAD contact that previously never left RECOVERING. */
class ActorSteelWithdrawalSessionTest {
    @Test fun blockedOverheadWithdrawsAsOneActorThenFinishesRecoveryWithoutMovingThePlayer() {
        val f=ActiveFixture()
        f.contact()
        val initial=f.session.viewState
        val source=ArenaSession::class.java.getDeclaredMethod("effectiveEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(f.session,0L) as EnemyPoseFrame
        @Suppress("UNCHECKED_CAST") val domain=ArenaSession::class.java.getDeclaredMethod("steelRecoverySamples",AttackPoseSample::class.java).apply {isAccessible=true}.invoke(f.session,source.pose) as List<AttackPoseSample>
        BladePlanBenchmark.record("actual_overhead_pressure",checkNotNull(initial.enemyPosition),initial.enemyYawRadians.toDouble(),source.pose,f.grip,f.impacts().single().normal,domain)
        val initialPosition=requireNotNull(initial.enemyPosition)
        val initialSource=initial.enemyPoseSourceSeconds
        val withdrawal=requireNotNull(field(f.session,"steelWithdrawal"))
        val plan=withdrawal.javaClass.getDeclaredField("plan").apply { isAccessible=true }.get(withdrawal) as ActorWithdrawalPlan
        println("ACTOR_FUTURE_DOMAIN_PLAN contactSource=$initialSource yawDegrees=${Math.toDegrees(plan.yawDeltaRadians)} durationSeconds=${plan.durationSeconds} retreatMm=${plan.retreatMeters*1000}")
        assertEquals(EnemyPhase.RECOVERING,initial.phase)
        assertTrue("The original impact must still have hit stop",initial.hitStop)
        assertEquals(1,f.impacts().size)
        assertEquals(1,f.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().size)
        var previous=initial
        var sourceResumedMillis:Int?=null
        var settledMillis:Int?=null
        var bodyMoved=false
        var maximumRetreat=0.0
        var maximumYawStep=0.0
        var minimumGap=Double.POSITIVE_INFINITY
        var maxVirtualOffset=0.0
        repeat(300) { index ->
            f.advance(10_000_000L)
            val state=f.session.viewState
            val position=requireNotNull(state.enemyPosition)
            val held=requireNotNull(state.playerWeaponGrip)
            val player=playerBlade(held)
            val raw=playerBlade(f.grip)
            val stagePose=ArenaSession::class.java.getDeclaredMethod("enemyAttackPose",java.lang.Long.TYPE)
                .apply { isAccessible=true }.invoke(f.session,0L) as AttackPoseSample
            val pp=DaoBladeShape.shape.at(held);val ee=DaoBladeShape.shape.at(stagePose.bladeGrip)
            val gap=pp.minOf { p -> ee.minOf { e ->
                val pair=requireNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip))
                pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters
            } }
            minimumGap=minOf(minimumGap,gap)
            assertTrue("Native capsule penetrated at ${(index+1)*10}ms; gap=$gap",gap>=-.0006)
            val step=position.distanceTo(requireNotNull(previous.enemyPosition))
            assertTrue("Actor root exceeded .65m/s at ${(index+1)*10}ms: step=$step",step<=.0065+1e-9)
            val yawStep=abs(state.enemyYawRadians.toDouble()-previous.enemyYawRadians.toDouble())
            maximumYawStep=maxOf(maximumYawStep,yawStep)
            assertTrue("Actor root exceeded 1rad/s at ${(index+1)*10}ms: step=$yawStep",yawStep<=.01+1e-6)
            val retreat=position.distanceTo(initialPosition)
            maximumRetreat=maxOf(maximumRetreat,retreat)
            bodyMoved=bodyMoved || retreat>.001 || abs(state.enemyYawRadians-initial.enemyYawRadians)>.001f
            assertTrue("A single withdrawal must remain finite",retreat<=.35+1e-9)
            assertTrue("One withdrawal cannot rotate more than 90 degrees",
                abs(state.enemyYawRadians.toDouble()-initial.enemyYawRadians.toDouble())<=Math.PI/2+1e-6)
            assertEquals("Raw player pose must remain fixed",f.grip,f.frame.rawWeaponGrip)
            assertEquals("Held player grip must not be projected",f.grip.position,held.position)
            assertTrue(raw.base.distanceTo(player.base)<1e-12)
            assertTrue(raw.tip.distanceTo(player.tip)<1e-12)
            maxVirtualOffset=maxOf(maxVirtualOffset,held.position.distanceTo(f.grip.position))
            if(index<3) {
                assertEquals("The first 30ms retain original hit stop",initialPosition,position)
                assertEquals(initial.enemyYawRadians,state.enemyYawRadians)
                assertEquals(initialSource,state.enemyPoseSourceSeconds)
            }
            if(sourceResumedMillis==null && state.enemyPoseSourceSeconds!=initialSource)sourceResumedMillis=(index+1)*10
            if(settledMillis==null && state.phase==EnemyPhase.IDLE && field(f.session,"contactRecovery")==null)settledMillis=(index+1)*10
            assertEquals("Static steel cannot issue duplicate impacts",1,f.impacts().size)
            assertEquals("The blocked attack resolves only once",1,f.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().size)
            assertEquals(100,state.health)
            assertEquals(100,state.playerHealth)
            previous=state
        }
        println("ACTOR_STEEL_SESSION sourceResumedMs=$sourceResumedMillis guardMs=$settledMillis retreatMm=${maximumRetreat*1000} yawDegrees=${Math.toDegrees(previous.enemyYawRadians.toDouble()-initial.enemyYawRadians.toDouble())} maxYawStep=$maximumYawStep minimumGapMm=${minimumGap*1000} maxPlayerOffsetMm=${maxVirtualOffset*1000}")
        assertTrue("Enemy body must move while its contact source is held",bodyMoved)
        assertNotNull("Attack source must resume within three seconds",sourceResumedMillis)
        assertNotNull("Actor withdrawal and the original recovery must finish within three seconds",settledMillis)
        assertEquals(EnemyPhase.IDLE,previous.phase)
        assertNull(field(f.session,"contactRecovery"))
        assertEquals(0.0,maxVirtualOffset,0.0)
    }

    @Test fun combatPauseDoesNotConsumeWithdrawalMotionOrReemitTheContact() {
        val f=ActiveFixture();f.contact();f.advance(200_000_000L)
        f.combat.pauseByPlayer()
        val before=f.session.viewState
        f.advance(1_000_000_000L)
        val after=f.session.viewState
        assertEquals(before.enemyPosition,after.enemyPosition)
        assertEquals(before.enemyYawRadians,after.enemyYawRadians)
        assertEquals(before.enemyPoseSourceSeconds,after.enemyPoseSourceSeconds)
        assertEquals(before.simulationNanos,after.simulationNanos)
        assertEquals(1,f.impacts().size)
    }

    @Test fun steelConsumesTheStrokeAndCannotApplyItsDelayedDamageTwice() {
        val f=ActiveFixture(7);f.contact()
        assertEquals(7L,field(f.session,"consumedStrikeId"))
        val contact=MotionContact(HitZone.BODY,Vector3(0.0,1.2,-1.3),Vector3(0.0,0.0,1.0))
        val delayed=f.frame.copy(strike=MotionStrike(7,HitZone.BODY,1.0,contact))
        val apply=ArenaSession::class.java.getDeclaredMethod("applyPlayerMotion",PlayerMotionFrame::class.java,MutableList::class.java).apply { isAccessible=true }
        repeat(3) { apply.invoke(f.session,delayed,f.events) }
        assertEquals(100,f.combat.health)
        assertEquals(1,f.impacts().size)
        assertTrue(f.events.none { it is EnemyCombatEvent.EnemyDamaged })
    }

    @Test fun aFreshAcceptedHitInterruptsTheOlderSteelRecovery() {
        val f=ActiveFixture(7);f.contact();f.advance(200_000_000L)
        val hit=MotionContact(HitZone.BODY,Vector3(0.0,1.2,-1.3),Vector3(0.0,0.0,1.0))
        val next=f.frame.copy(strike=MotionStrike(8,HitZone.BODY,1.0,hit))
        ArenaSession::class.java.getDeclaredMethod("applyPlayerMotion",PlayerMotionFrame::class.java,MutableList::class.java)
            .apply { isAccessible=true }.invoke(f.session,next,f.events)
        assertTrue(f.combat.health<100)
        assertNull(field(f.session,"steelWithdrawal"));assertNull(field(f.session,"contactRecovery"))
        assertEquals(EnemyPhase.HIT,f.combat.phase)
        assertTrue(f.session.viewState.hitStop)
    }

    @Test fun expiredReceiptCannotRearmOrDamageDuringWithdrawal() {
        val f=ActiveFixture(7);f.contact();f.advance(200_000_000L)
        @Suppress("UNCHECKED_CAST") val queue=field(f.session,"pendingMotion") as ArrayDeque<PlayerMotionFrame>
        queue.addLast(f.frame.copy(receivedAtNanos=0L,swing=QualifiedSwing(8,1.0)))
        ArenaSession::class.java.getDeclaredMethod("advanceFight",java.lang.Long.TYPE,java.lang.Long.TYPE,MutableList::class.java)
            .apply { isAccessible=true }.invoke(f.session,10_000_000L,1_000_000_000L,f.events)
        assertTrue(queue.isEmpty());assertEquals(7L,field(f.session,"consumedStrikeId"))
        assertEquals(1,f.impacts().size);assertEquals(100,f.combat.health)
    }

    @Test fun killingDuringWithdrawalClearsTheActorPlanAndPlayerConstraint() {
        val f=ActiveFixture();f.contact();f.advance(200_000_000L)
        assertNotNull(field(f.session,"steelWithdrawal"))
        val death=f.combat.receivePlayerHit(150,breakGuard=true)
        ArenaSession::class.java.getDeclaredMethod("collect",List::class.java,MutableList::class.java)
            .apply { isAccessible=true }.invoke(f.session,death,f.events)
        assertEquals(TrialResult.ROUND_CLEAR,f.session.viewState.result)
        assertNull(field(f.session,"steelWithdrawal"))
        assertFalse((field(f.session,"motion") as PlayerCombatResolver).weaponConstrained)
        assertFalse(field(f.session,"steelContactLatched") as Boolean)
        f.advance(1_000_000_000L);assertEquals(0,f.combat.health);assertEquals(1,f.impacts().size)
    }

    @Test fun aNewEnemyAttackRearmsItsOwnContactIdentityAfterRecovery() {
        val f=ActiveFixture();f.contact();repeat(300) { f.advance(10_000_000L) }
        assertEquals(EnemyPhase.IDLE,f.combat.phase)
        f.combat.advanceBy(800_000_000L,true)
        val started=f.combat.tryStartAttack(AttackDirection.LEFT,true)
        assertEquals(1,started.filterIsInstance<EnemyCombatEvent.AttackStarted>().size)
        ArenaSession::class.java.getDeclaredMethod("collect",List::class.java,MutableList::class.java)
            .apply { isAccessible=true }.invoke(f.session,started,f.events)
        assertFalse(field(f.session,"steelContactLatched") as Boolean)
        assertNull(field(f.session,"steelWithdrawal"))
        assertNotEquals(f.events.filterIsInstance<EnemyCombatEvent.AttackResolved>().first().attackId,
            f.events.filterIsInstance<EnemyCombatEvent.AttackStarted>().last().attackId)
    }

    private class ActiveFixture(swingId:Long?=null) {
        val events=mutableListOf<EnemyCombatEvent>()
        val session=ArenaSession(logMessage={},logFailure={_,e->throw e})
        val combat=EnemyCombatStateMachine().also {
            it.advanceBy(800_000_000L,true)
            it.tryStartAttack(AttackDirection.OVERHEAD,true)
            it.advanceBy(AttackDirection.OVERHEAD.preparationNanos+AttackDirection.OVERHEAD.startupNanos,true)
        }
        val grip:WeaponGrip
        var frame:PlayerMotionFrame
            private set
        private var now=0L
        private val advance=ArenaSession::class.java.getDeclaredMethod("advanceEnemy",java.lang.Long.TYPE,
            MutableList::class.java,java.lang.Long.TYPE,PlayerMotionFrame::class.java).apply { isAccessible=true }
        init {
            val origin=Vector3(0.0,0.0,-1.3)
            session.setEnemyGeometry(origin,2.0)
            set(session,"result",TrialResult.FIGHTING)
            set(session,"combat",combat)
            val profile=arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD)
            val source=profile.sample(profile.sourcePhaseSeconds[2])
            // This fixture injects an already-ACTIVE timeline; retain the corresponding
            // real accepted source rather than an unrelated IDLE frame from scene setup.
            set(session,"acceptedEnemySource",EnemyPoseFrame(profile.clip,source))
            val pose=source.inStage(origin,0f)
            val rotation=Quaternion(0.0,-sqrt(.5),0.0,sqrt(.5))
            val local=playerBlade(WeaponGrip(Vector3(0.0,0.0,0.0),rotation))
            var normal=requireNotNull((local.tip-local.base).cross(pose.bladeTip-pose.bladeBase).normalizedOrNull())
            if(normal.z<0.0)normal=normal*-1.0
            val target=WeaponGrip((pose.bladeBase+pose.bladeTip-local.base-local.tip)*.5+
                normal*(local.radiusMeters+.0125-1e-9),rotation)
            val clear=target.copy(position=target.position+normal*.15)
            val chain=DaoBladeShape.shape
            val witness=checkNotNull(firstBladeShapeContact(BladeShapeSweep(chain,clear,target,0.0),
                BladeShapeSweep(chain,pose.bladeGrip,pose.bladeGrip,pose.bladeGripInterpolationErrorToNextMeters)))
            // Same real OH pose and transverse direction. Locate the full-chain TOI instead
            // of starting at the old single-axis stop, which can already penetrate new steel.
            grip=interpolateGrip(clear,target,(witness.contact.fraction+2*(witness.contact.errorBoundMeters-pose.bladeGripInterpolationErrorToNextMeters)/clear.position.distanceTo(target.position)).coerceAtMost(1.0))
            val blade=playerBlade(grip)
            frame=PlayerMotionFrame(0L,blade.base,blade.tip,0.0,null,false,Vector3(0.0,1.6,0.0),rawWeaponGrip=grip,weaponGrip=grip,swing=swingId?.let { QualifiedSwing(it,1.0) })
            set(session,"simulationMotion",frame);set(session,"latestMotion",frame)
            assertEquals(EnemyPhase.ACTIVE,combat.phase)
        }
        fun contact() {
            advance.invoke(session,0L,events,now,frame)
            session.setArenaPresenter { _,_-> }
            assertEquals(CombatImpactKind.BLOCK,impacts().single().kind)
        }
        fun advance(delta:Long) {
            frame=frame.copy(receivedAtNanos=now+delta,
                motionGeneration=(field(session,"motion") as PlayerCombatResolver).motionGeneration)
            advance.invoke(session,delta,events,now,frame)
            now+=delta
        }
        fun impacts()=events.filterIsInstance<CombatImpact>()
    }
}
private fun field(session:ArenaSession,name:String):Any?=ArenaSession::class.java.getDeclaredField(name).apply { isAccessible=true }.get(session)
private fun set(session:ArenaSession,name:String,value:Any)=ArenaSession::class.java.getDeclaredField(name).apply { isAccessible=true }.set(session,value)
