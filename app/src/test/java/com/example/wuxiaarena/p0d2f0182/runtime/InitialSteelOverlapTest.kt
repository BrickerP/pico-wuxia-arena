package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

/** Unknown collision origin must re-arm safely; there is no invented previous safe Grip. */
class InitialSteelOverlapTest {
    @Test fun countdownEndingInsideWholeEnemySteelCanRecoverAfterRealWithdrawalWithoutFarming()=exercise(false)
    @Test fun pauseReacquisitionInsideWholeEnemySteelCanRecoverAfterRealWithdrawalWithoutFarming()=exercise(true)
    @Test fun aProvedSafePendingBaselineStillAdmitsARealCrossingBeforeFirstPhysicsTick() {
        val f=Fixture(true);f.start()
        f.now+=100_000_000L;f.raw=f.enemy().bladeGrip;f.observe()
        @Suppress("UNCHECKED_CAST") val queue=ArenaSession::class.java.getDeclaredField("pendingMotion").apply {isAccessible=true}.get(f.session) as ArrayDeque<PlayerMotionFrame>
        assertTrue("The earlier clear controller pose remains an available safe origin",queue.size>=2)
        f.session.onTick(f.now)
        assertEquals(1,f.events.filterIsInstance<CombatImpact>().count {it.kind==CombatImpactKind.BLOCK || it.kind==CombatImpactKind.PARRY})
        assertTrue(f.events.none {it is EnemyCombatEvent.EnemyDamaged})
        assertNotEquals(f.raw.position,checkNotNull(f.session.viewState.playerWeaponGrip).position)
    }
    private fun exercise(reacquire:Boolean) {
        val f=Fixture(reacquire);f.start()
        if(reacquire) {
            f.send(TrackingEvent.Discontinuity(f.stamp(),TrackingTarget.ALL,DiscontinuityReason.USER_PAUSED))
            val paused=checkNotNull(f.session.viewState.pauseId)
            f.raw=f.enemy().bladeGrip
            f.observe();assertFalse("Unsafe reacquisition cannot establish an action baseline",f.session.confirmResume(paused))
            assertEquals(paused,f.session.viewState.pauseId)
            f.pendingResume=paused
        }
        repeat(6){f.tick(10_000_000L)}
        assertTrue("This is a genuinely deep initial full-chain overlap",gap(DaoBladeShape.shape.at(f.raw),DaoBladeShape.shape.at(f.enemy().bladeGrip))<-.01)
        val impacts=f.events.filterIsInstance<CombatImpact>().size
        f.raw=f.raw.copy(position=f.raw.position+Vector3(.35,0.0,0.0))
        f.tick(100_000_000L)
        f.pendingResume?.let {id->assertTrue(f.session.viewState.resumeReady);assertTrue(f.session.confirmResume(id));f.session.onTick(f.now)}
        repeat(8){f.tick(10_000_000L)}
        assertTrue("The actual new raw pose is fully clear",gap(DaoBladeShape.shape.at(f.raw),DaoBladeShape.shape.at(f.enemy().bladeGrip))>.025)
        val recognizer=ArenaSession::class.java.getDeclaredField("motion").apply {isAccessible=true}.get(f.session) as PlayerCombatResolver
        assertFalse("An unproved starting penetration must not lock the player's real withdrawal forever",recognizer.weaponConstrained)
        assertTrue(f.session.viewState.actionReady)
        val virtual=checkNotNull(f.session.viewState.playerWeaponGrip)
        assertEquals(f.raw.position,virtual.position)
        val expected=checkNotNull(f.raw.rotation.normalizedOrNull());val actual=checkNotNull(virtual.rotation.normalizedOrNull())
        assertTrue(kotlin.math.abs(expected.x*actual.x+expected.y*actual.y+expected.z*actual.z+expected.w*actual.w)>1.0-1e-12)
        assertEquals(f.raw.position,f.tracking.snapshot.right?.pose?.position)
        assertEquals(f.raw.rotation,f.tracking.snapshot.right?.pose?.rotation)
        assertEquals(100,f.session.viewState.health);assertEquals(100,f.session.viewState.playerHealth)
        assertTrue(f.events.none {it is EnemyCombatEvent.EnemyDamaged})
        repeat(20){f.tick(10_000_000L)}
        assertEquals("No new steel impact may be farmed by egress or repeated clear observations",impacts,f.events.filterIsInstance<CombatImpact>().size)
    }
    private fun gap(a:List<BladeSegment>,b:List<BladeSegment>)=a.minOf {x->b.minOf {y->
        val p=checkNotNull(closestSegmentPoints(x.base,x.tip,y.base,y.tip));p.first.distanceTo(p.second)-x.radiusMeters-y.radiusMeters
    }}
    private class Fixture(safeStart:Boolean) {
        val events=mutableListOf<EnemyCombatEvent>()
        val session=ArenaSession(logMessage={},logFailure={_,e->throw e})
        val tracking=TrackingState(Hand.RIGHT)
        var now=1_000_000_000L;private var sequence=0L
        var pendingResume:Long?=null
        private val overlap=arenaOpponents.first().locomotionProfile().idle.samples.first().inStage(Vector3(0.0,0.0,-1.3),0f).bladeGrip
        var raw=if(safeStart)overlap.copy(position=overlap.position+Vector3(.35,0.0,0.0)) else overlap
        init {session.setArenaPresenter {_,batch->events.addAll(batch)};session.setEnemyGeometry(Vector3(0.0,0.0,-1.3),2.0);observe()}
        fun stamp()=ObservationStamp(sequence++,now,1L,InputOrigin.PICO)
        fun send(event:TrackingEvent) {val accepted=tracking.accept(event);assertTrue(accepted);session.onTrackingEvent(event,accepted,tracking.snapshot)}
        fun observe() {send(TrackingEvent.Head(stamp(),ObservedPose(Vector3(0.0,1.6,0.0),Quaternion(0.0,0.0,0.0,1.0))));send(TrackingEvent.Controllers(stamp(),null,ObservedPose(raw.position,raw.rotation)))}
        fun tick(delta:Long){now+=delta;observe();session.onTick(now)}
        fun start(){assertTrue(session.startTrial());session.onTick(now);tick(3_000_000_000L);assertEquals(TrialResult.FIGHTING,session.viewState.result)}
        fun enemy()=ArenaSession::class.java.getDeclaredMethod("enemyAttackPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(session,0L) as AttackPoseSample
    }
}
