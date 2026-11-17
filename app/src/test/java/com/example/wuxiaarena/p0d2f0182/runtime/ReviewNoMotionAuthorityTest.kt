package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

class ReviewNoMotionAuthorityTest {
    @Test fun userResumeBeforeTheNextTrackingReceiptCannotPermanentlyOrphanTheOwnedAttackClock() {
        val s=ArenaSession(logMessage={},logFailure={_,e->throw e})
        s.setEnemyGeometry(Vector3(0.0,.028,-2.0),1.55)
        val tracking=TrackingState(Hand.RIGHT)
        var sequence=0L;var now=0L
        val grip=WeaponGrip(Vector3(2.0,1.4,-.45),Quaternion(0.0,0.0,0.0,1.0))
        fun stamp()=ObservationStamp(sequence++,now,0L,InputOrigin.PICO)
        fun send(event:TrackingEvent) {val accepted=tracking.accept(event);assertTrue(accepted);s.onTrackingEvent(event,accepted,tracking.snapshot)}
        fun observe() {
            send(TrackingEvent.Head(stamp(),ObservedPose(Vector3(0.0,1.65,0.0),Quaternion(0.0,0.0,0.0,1.0))))
            send(TrackingEvent.Controllers(stamp(),null,ObservedPose(grip.position,grip.rotation)))
        }
        observe()
        val c=EnemyCombatStateMachine();c.advanceBy(800_000_000L,true);c.tryStartAttack(AttackDirection.RIGHT,true);c.advanceBy(423_076_923L,true)
        set(s,"combat",c);set(s,"result",TrialResult.FIGHTING);set(s,"trialStarted",true)
        set(s,"simulationMotion",checkNotNull(field(s,"latestMotion")))
        val selected=ArenaSession::class.java.getDeclaredMethod("selectedEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}
        val initial=selected.invoke(s,0L) as EnemyPoseFrame
        set(s,"acceptedEnemySource",initial);set(s,"acceptedSourceEpoch",field(s,"sourceEpoch") as Long)
        s.setArenaPresenter {_,_->}
        now=1_000_000L
        send(TrackingEvent.Discontinuity(stamp(),TrackingTarget.ALL,DiscontinuityReason.USER_PAUSED))
        assertEquals(PauseReason.USER,c.pauseReason)
        now=2_000_000L;observe()
        assertTrue(s.viewState.resumeReady)
        assertTrue(s.confirmResume(checkNotNull(c.currentPauseId)))
        assertNull(field(s,"simulationMotion"));assertNull(field(s,"enemySourceReturn"))
        now=10_000_000L;s.onTick(now)
        now=20_000_000L;s.onTick(now)
        println("REVIEW_EMPTY_MOTION afterTick owner=${s.viewState.enemyPoseClip}@${s.viewState.enemyPoseSourceSeconds} wanted=${selected.invoke(s,0L)} join=${field(s,"heldEnemySourceJoinStatus")} phaseElapsed=${c.phaseElapsedNanos}")
        val beforeFresh=s.viewState.enemyPoseSourceSeconds
        repeat(30) {now+=10_000_000L;observe();s.onTick(now)}
        println("REVIEW_EMPTY_MOTION afterFresh owner=${s.viewState.enemyPoseClip}@${s.viewState.enemyPoseSourceSeconds} join=${field(s,"heldEnemySourceJoinStatus")} phaseElapsed=${c.phaseElapsedNanos}")
        assertNull("Fresh safe tracking must not leave a same-clip source-time gap permanently orphaned",field(s,"heldEnemySourceJoin"))
        assertTrue("The real owned attack must resume along its actual curve",checkNotNull(s.viewState.enemyPoseSourceSeconds)>checkNotNull(beforeFresh)+.05)
        assertEquals(100,c.health)
    }
    private fun field(s:ArenaSession,name:String)=s.javaClass.getDeclaredField(name).apply {isAccessible=true}.get(s)
    private fun set(s:ArenaSession,name:String,value:Any)=s.javaClass.getDeclaredField(name).apply {isAccessible=true}.set(s,value)
}
