package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

class NativeDdacBaselineFreshnessTest {
    @Test fun exactlyTheExisting250msReceiptBoundaryCanRebaseWithoutAStroke() {
        val f=Fixture();f.confirm()
        f.s.onTick(252_000_000L)
        val baseline=field(f.s,"simulationMotion") as PlayerMotionFrame
        assertEquals(f.grip,baseline.rawWeaponGrip)
        assertNull(baseline.strike);assertNull(baseline.swing);assertFalse(baseline.skillGesture)
        assertEquals(f.source,source(f.s),1e-12)
        f.s.onTick(262_000_000L)
        assertTrue("An established baseline has no added expiry clock",source(f.s)>f.source)
        assertEquals(100,f.combat.health)
    }

    @Test fun oneNanosecondPastTheExistingDeadlineCannotRebuildFromTheOldSnapshot() {
        val f=Fixture();f.confirm()
        f.s.onTick(252_000_001L);f.s.onTick(262_000_001L)
        assertNull(field(f.s,"simulationMotion"));assertNull(field(f.s,"latestMotion"))
        assertFalse(f.s.viewState.actionReady)
        assertEquals(f.source,source(f.s),0.0)
        f.now=300_000_000L;f.observe()
        f.s.onTick(f.now)
        assertEquals("First fresh tick cannot catch up the missing source interval",f.source,source(f.s),1e-12)
        f.s.onTick(f.now+10_000_000L)
        assertTrue(source(f.s)>f.source)
        assertNull(field(f.s,"heldEnemySourceJoin"))
        assertEquals(100,f.combat.health)
    }

    @Test fun aFutureDatedSnapshotCannotBecomeTheCurrentCollisionBaseline() {
        val f=Fixture();f.confirm()
        f.s.onTick(1_999_999L)
        assertNull(field(f.s,"simulationMotion"));assertNull(field(f.s,"latestMotion"))
        assertEquals(f.source,source(f.s),0.0)
        assertFalse(f.s.viewState.actionReady)
    }

    @Test fun aNewTrackingPauseStillRequiresItsOwnFreshCurrentConfirmation() {
        val f=Fixture()
        val first=checkNotNull(f.combat.currentPauseId)
        f.s.onTick(3_000_000L)
        assertEquals(f.source,source(f.s),0.0)
        assertFalse(f.s.confirmResume(first+1L))
        f.now=4_000_000L
        f.send(TrackingEvent.Discontinuity(f.stamp(),TrackingTarget.ALL,DiscontinuityReason.QUEUE_GAP))
        val current=checkNotNull(f.combat.currentPauseId)
        assertNotEquals(first,current)
        f.now=5_000_000L;f.observe()
        assertFalse(f.s.confirmResume(first))
        f.s.onTick(6_000_000L)
        assertEquals(PauseReason.TRACKING_INTERRUPTION,f.combat.pauseReason)
        assertEquals(f.source,source(f.s),0.0)
        assertTrue(f.s.confirmResume(current))
        f.s.onTick(7_000_000L)
        assertNotNull(field(f.s,"simulationMotion"))
        assertNull(f.combat.hitReaction)
        assertEquals(100,f.combat.health)
    }

    @Test fun missingRequiredRotationCannotRebuildARealGripOrBypassReconfirmation() {
        val f=Fixture();f.confirm()
        f.now=3_000_000L
        f.send(TrackingEvent.Controllers(f.stamp(),null,ObservedPose(f.grip.position,null)))
        val pause=checkNotNull(f.combat.currentPauseId)
        f.s.onTick(4_000_000L)
        assertFalse(f.s.viewState.inputReady)
        assertNull(field(f.s,"simulationMotion"))
        assertFalse(f.s.confirmResume(pause))
        assertEquals(f.source,source(f.s),0.0)
        assertEquals(100,f.combat.health)
    }

    private class Fixture {
        val s=ArenaSession(logMessage={},logFailure={_,e->throw e})
        val tracking=TrackingState(Hand.RIGHT)
        val grip=WeaponGrip(Vector3(2.0,1.4,-.45),Quaternion(0.0,0.0,0.0,1.0))
        val combat=EnemyCombatStateMachine()
        var now=0L;private var sequence=0L
        val source:Double
        init {
            s.setEnemyGeometry(Vector3(0.0,.028,-2.0),1.55);observe()
            combat.advanceBy(800_000_000L,true);combat.tryStartAttack(AttackDirection.RIGHT,true);combat.advanceBy(423_076_923L,true)
            set(s,"combat",combat);set(s,"result",TrialResult.FIGHTING);set(s,"trialStarted",true)
            set(s,"simulationMotion",checkNotNull(field(s,"latestMotion")))
            val frame=ArenaSession::class.java.getDeclaredMethod("selectedEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as EnemyPoseFrame
            source=frame.pose.sourceSeconds
            set(s,"acceptedEnemySource",frame);set(s,"acceptedSourceEpoch",field(s,"sourceEpoch") as Long)
            s.setArenaPresenter {_,_->}
            now=1_000_000L;send(TrackingEvent.Discontinuity(stamp(),TrackingTarget.ALL,DiscontinuityReason.USER_PAUSED))
            now=2_000_000L;observe()
        }
        fun stamp()=ObservationStamp(sequence++,now,0L,InputOrigin.PICO)
        fun send(e:TrackingEvent){val accepted=tracking.accept(e);assertTrue(accepted);s.onTrackingEvent(e,accepted,tracking.snapshot)}
        fun observe(){send(TrackingEvent.Head(stamp(),ObservedPose(Vector3(0.0,1.65,0.0),Quaternion(0.0,0.0,0.0,1.0))));send(TrackingEvent.Controllers(stamp(),null,ObservedPose(grip.position,grip.rotation)))}
        fun confirm(){assertTrue(s.confirmResume(checkNotNull(combat.currentPauseId)));assertNull(field(s,"simulationMotion"))}
    }
    companion object {
        private fun source(s:ArenaSession)=checkNotNull(s.viewState.enemyPoseSourceSeconds)
        private fun field(s:ArenaSession,name:String)=s.javaClass.getDeclaredField(name).apply {isAccessible=true}.get(s)
        private fun set(s:ArenaSession,name:String,value:Any)=s.javaClass.getDeclaredField(name).apply {isAccessible=true}.set(s,value)
    }
}
