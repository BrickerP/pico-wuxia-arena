package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

class NativeDdacSourceAuthorityTest {
    private val f=NativeDdacFixture

    @Test fun actualBossWalkStopCannotCommitTheIdlePoseBeyondItsMicroSeamToi() {
        for(inputOrigin in listOf(InputOrigin.DESKTOP,InputOrigin.PICO)) {
            val s=scene(inputOrigin)
            val events=mutableListOf<EnemyCombatEvent>()
            assertTrue(gap(f.held,stage(s).bladeGrip)>1e-4)
            advance(s,1_000_000L,events)
            assertTrue("The true old WALK source is clear; stopping may not publish the already-penetrating IDLE target",gap(f.held,stage(s).bladeGrip)>=-1e-7)
            assertEquals("walk",s.viewState.enemyPoseClip)
            assertNotNull("A source seam blocked beyond its first contact uses the existing finite actor plan",field(s,"steelWithdrawal"))
            var resumed=false
            repeat(200) {
                if(!resumed) {
                    advance(s,5_000_000L,events)
                    assertTrue("Every rendered/query whole-blade pose remains nonpenetrating",gap(f.held,stage(s).bladeGrip)>=-1e-7)
                    resumed=field(s,"heldEnemySourceJoin")==null && s.viewState.enemyPoseClip=="idle"
                }
            }
            assertTrue("Finite actor withdrawal resumes actual IDLE without trapping a safe player wrist",resumed)
            assertEquals(150,s.viewState.health);assertEquals(100,s.viewState.playerHealth)
            assertTrue(events.none {it is CombatImpact || it is EnemyCombatEvent.EnemyDamaged})
        }
    }

    @Test fun equalWalkAndIdleTimesRemainDifferentFullFutureDomainPoses() {
        val s=scene(InputOrigin.PICO)
        val current=arenaOpponents[2].locomotionProfile().walk.sample(.75)
        @Suppress("UNCHECKED_CAST")
        val domain=ArenaSession::class.java.getDeclaredMethod("steelRecoverySamples",AttackPoseSample::class.java)
            .apply {isAccessible=true}.invoke(s,current) as List<AttackPoseSample>
        val future=arenaOpponents[2].locomotionProfile().idle.sample(.75)
        assertTrue(current.bladeGrip.position.distanceTo(future.bladeGrip.position)>.001)
        assertTrue("Current WALK witness remains",domain.any {it.sourceSeconds==.75 && it.bladeGrip==current.bladeGrip})
        assertTrue("The distinct IDLE maximum may not be deduplicated by the WALK time",domain.any {it.sourceSeconds==.75 && it.bladeGrip==future.bladeGrip})
    }

    @Test fun endingASourceOverrideDoesNotChangeTheCurrentReadBeforeAdmission() {
        val s=scene(InputOrigin.PICO)
        set(s,"enemyMoveDirection",0f)
        val desired=ArenaSession::class.java.getDeclaredMethod("selectedEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as EnemyPoseFrame
        assertEquals("idle",desired.clip)
        assertTrue(gap(f.held,desired.pose.inStage(f.origin,0f).bladeGrip)< -1e-4)
        assertTrue("Current authority remains the actually accepted clear WALK source",gap(f.held,stage(s).bladeGrip)>1e-4)
        s.setArenaPresenter {_,_->}
        assertTrue("The publisher also cannot promote an unproved source",gap(f.held,stage(s).bladeGrip)>1e-4)
        assertEquals("walk",s.viewState.enemyPoseClip)
    }

    @Test fun aheadPeeksAndKeySplitsFollowTheOwnedIdleCurveWithoutMutatingIt() {
        val s=scene(InputOrigin.PICO)
        set(s,"enemyMoveDirection",0f)
        val idle=arenaOpponents[2].locomotionProfile().idle
        val source=EnemyPoseFrame("idle",idle.sample(.013))
        set(s,"acceptedEnemySource",source)
        val peek=ArenaSession::class.java.getDeclaredMethod("effectiveEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}
        val future=peek.invoke(s,5_000_000L) as EnemyPoseFrame
        assertEquals(.018,future.pose.sourceSeconds,1e-12)
        assertEquals(idle.sample(.018).bladeGrip,future.pose.bladeGrip)
        assertEquals(source,peek.invoke(s,0L))
        assertEquals(1_076_918_782L,field(s,"enemyMotionNanos"))
        val interval=ArenaSession::class.java.getDeclaredMethod("nextPoseInterval",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,10_000_000L) as Long
        val after=peek.invoke(s,interval) as EnemyPoseFrame
        assertTrue("Forecast keeps every actual outgoing source interval",idle.samples.none {it.sourceSeconds>.013+1e-12 && it.sourceSeconds<after.pose.sourceSeconds-1e-12})
        assertEquals(source,peek.invoke(s,0L))
    }

    @Test fun futureHeadReversalChoosesWalkKeysForTheActualMovementStep() {
        val s=scene(InputOrigin.PICO);val loco=arenaOpponents[2].locomotionProfile()
        val sourceTime=.7500001
        set(s,"acceptedEnemySource",EnemyPoseFrame("walk",loco.walk.sample(sourceTime)))
        set(s,"enemyGaitMeters",(sourceTime-loco.loopStartSeconds)/(loco.loopEndSeconds-loco.loopStartSeconds)*loco.strideMeters)
        set(s,"steelContactLatched",false)
        val start=f.origin+Vector3(0.0,1.65,1.4);val end=f.origin+Vector3(0.0,1.65,.3)
        val frame=field(s,"simulationMotion") as PlayerMotionFrame
        set(s,"simulationMotion",frame.copy(headPosition=start))
        val headAt:(Long)->Vector3={t->start+(end-start)*(t/10_000_000.0)}
        val capture=ArenaSession::class.java.getDeclaredMethod("captureEnemyLocomotion").apply {isAccessible=true}
        val move=ArenaSession::class.java.getDeclaredMethod("moveEnemy",java.lang.Long.TYPE,Vector3::class.java).apply {isAccessible=true}
        val projected=ArenaSession::class.java.getDeclaredMethod("projectedEnemySource",java.lang.Long.TYPE,java.lang.Double.TYPE).apply {isAccessible=true}
        fun keysInsideStep(nanos:Long):Int {
            val before=capture.invoke(s);val gait=field(s,"enemyGaitMeters") as Double
            move.invoke(s,nanos,headAt(nanos))
            val delta=(field(s,"enemyGaitMeters") as Double)-gait
            val after=projected.invoke(s,nanos,delta) as EnemyPoseFrame
            ArenaSession::class.java.getDeclaredMethod("restoreEnemyLocomotion",before.javaClass).apply {isAccessible=true}.invoke(s,before)
            return loco.walk.samples.count {it.sourceSeconds>minOf(sourceTime,after.pose.sourceSeconds)+1e-12 && it.sourceSeconds<maxOf(sourceTime,after.pose.sourceSeconds)-1e-12}
        }
        // Synthetic fast but valid future-head movement exposes the old preview
        // direction mismatch. It is not claimed to occur in the native ddac trace.
        val oldInterval=ArenaSession::class.java.getDeclaredMethod("nextPoseInterval",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,10_000_000L) as Long
        assertTrue("Current-head-only preview really skips an opposite-direction source key",keysInsideStep(oldInterval)>0)
        val actual=ArenaSession::class.java.getDeclaredMethod("nextQueryPoseInterval",java.lang.Long.TYPE,kotlin.jvm.functions.Function1::class.java)
            .apply {isAccessible=true}.invoke(s,10_000_000L,headAt) as Long
        assertTrue(actual>0L)
        assertEquals("Actual future-head movement stays within its owned key interval",0,keysInsideStep(actual))
        assertEquals(sourceTime,(field(s,"acceptedEnemySource") as EnemyPoseFrame).pose.sourceSeconds,0.0)
    }

    private fun scene(inputOrigin:InputOrigin):ArenaSession {
        val s=ArenaSession(logMessage={},logFailure={_,e->throw e})
        set(s,"roundNumber",3);s.setEnemyGeometry(f.origin,1.55)
        val tracking=TrackingState(Hand.RIGHT)
        val input=listOf(TrackingEvent.Head(ObservationStamp(0L,0L,0L,inputOrigin),ObservedPose(Vector3(0.0,1.649999976158142,0.0),Quaternion(0.0,0.0,0.0,1.0))),
            TrackingEvent.Controllers(ObservationStamp(1L,0L,0L,inputOrigin),null,ObservedPose(f.held.position,f.held.rotation)))
        for(e in input){val accepted=tracking.accept(e);assertTrue(accepted);s.onTrackingEvent(e,accepted,tracking.snapshot)}
        val c=EnemyCombatStateMachine(150,600_000_000L)
        set(s,"combat",c);set(s,"initialHealth",150);set(s,"result",TrialResult.FIGHTING);set(s,"trialStarted",true)
        set(s,"simulationMotion",checkNotNull(field(s,"latestMotion")))
        set(s,"enemyMotionNanos",1_076_918_782L);set(s,"enemyMoveDirection",1f)
        val loco=arenaOpponents[2].locomotionProfile()
        set(s,"enemyGaitMeters",(.75-loco.loopStartSeconds)/(loco.loopEndSeconds-loco.loopStartSeconds)*loco.strideMeters)
        set(s,"steelContactLatched",true)
        set(s,"acceptedEnemySource",EnemyPoseFrame("walk",loco.walk.sample(.75)))
        set(s,"acceptedSourceEpoch",field(s,"sourceEpoch") as Long)
        set(s,"recoilElapsedNanos",220_000_000L)
        s.setArenaPresenter {_,_->}
        return s
    }
    private fun advance(s:ArenaSession,delta:Long,events:MutableList<EnemyCombatEvent>) {
        val frame=field(s,"simulationMotion") as PlayerMotionFrame
        ArenaSession::class.java.getDeclaredMethod("advanceEnemy",java.lang.Long.TYPE,MutableList::class.java,java.lang.Long.TYPE,PlayerMotionFrame::class.java)
            .apply {isAccessible=true}.invoke(s,delta,events,frame.receivedAtNanos,frame.copy(receivedAtNanos=frame.receivedAtNanos+delta))
        s.setArenaPresenter {_,_->}
    }
    private fun stage(s:ArenaSession)=ArenaSession::class.java.getDeclaredMethod("enemyAttackPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as AttackPoseSample
    private fun gap(player:WeaponGrip,enemy:WeaponGrip)=DaoBladeShape.shape.at(player).minOf {p->DaoBladeShape.shape.at(enemy).minOf {e->val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip));pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters}}
    private fun field(s:ArenaSession,name:String)=ArenaSession::class.java.getDeclaredField(name).apply {isAccessible=true}.get(s)
    private fun set(s:ArenaSession,name:String,value:Any)=ArenaSession::class.java.getDeclaredField(name).apply {isAccessible=true}.set(s,value)
}
