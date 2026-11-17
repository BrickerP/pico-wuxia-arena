package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.ceil

class SourceReturnBodyContinuityTest {
    private val origin=Vector3(0.0,0.0,-1.3)
    private val far=WeaponGrip(Vector3(3.0,1.4,0.0),Quaternion(0.0,0.0,0.0,1.0))

    @Test fun aRealWeaponCoincidenceStillReturnsTheRemainingActualWholeBodySource() {
        val reactions=arenaOpponents.first().reactionProfiles()
        val time=1.1661457940936089
        val from=EnemyPoseFrame("hit_side",reactions.side.sample(time))
        val target=EnemyPoseFrame("hit_body",reactions.body.sample(.05))
        val a=DaoBladeShape.shape.at(from.pose.bladeGrip);val b=DaoBladeShape.shape.at(target.pose.bladeGrip)
        val steel=a.indices.maxOf {maxOf(a[it].base.distanceTo(b[it].base),a[it].tip.distanceTo(b[it].tip))}
        assertTrue(steel<=from.pose.bladeGripInterpolationErrorToNextMeters+target.pose.bladeGripInterpolationErrorToNextMeters+1e-7)
        val head=from.pose.contact.head.distanceTo(target.pose.contact.head)
        assertTrue("The measured whole body is still different, not a millimeter-scale jump: $head",head in 5e-6..1e-5)
        val route=checkNotNull(makeEnemySourceReturn(from,target,reactions.side.samples,listOf(.05,1.18)))
        assertEquals(1.18,route.guardSeconds,0.0)
        assertEquals(ceil((1.18-time)*1e9).toLong(),route.returnNanos)
        assertEquals(from,route.frame(0L))
        val middle=route.frame(route.returnNanos/2)
        assertEquals(reactions.side.sample(middle.pose.sourceSeconds),middle.pose)
        assertNull(makeEnemySourceReturn(route.frame(route.returnNanos),target,reactions.side.samples,listOf(.05,1.18)))
        assertNull(makeEnemySourceReturn(from,from,reactions.side.samples,listOf(.05,1.18)))
    }

    @Test fun everyActualActorCanLeaveBreathingIdleAndReallyAdvanceAllThreeAttacks() {
        for(round in 1..3)for(direction in AttackDirection.entries) {
            val s=scene(round);val combat=EnemyCombatStateMachine();combat.advanceBy(800_000_000L,true)
            set(s,"combat",combat);set(s,"enemyMotionNanos",750_000_000L)
            acceptCurrent(s)
            val events=mutableListOf<EnemyCombatEvent>()
            collect(s,combat.tryStartAttack(direction,true),events)
            s.setArenaPresenter {_,_->}
            assertEquals(EnemyPhase.PREPARING,combat.phase)
            assertEquals("Actual actor $round must not be held at idle by a 0.4/1.05mm guard drift","attack_${direction.name.lowercase()}",s.viewState.enemyPoseClip)
            assertNull(field(s,"heldEnemySourceJoin"))
            advance(s,50_000_000L)
            assertTrue(checkNotNull(s.viewState.enemyPoseSourceSeconds)>0.0)
            assertEquals(100,combat.health)
        }
    }

    @Test fun actualWalkingToStandingUsesTheSameGuardEnvelopeForEveryActor() {
        for(round in 1..3) {
            val s=scene(round);val locomotion=arenaOpponents[round-1].locomotionProfile()
            set(s,"enemyMotionNanos",750_000_000L)
            set(s,"enemyMoveDirection",1f)
            set(s,"enemyGaitMeters",(.75-locomotion.loopStartSeconds)/(locomotion.loopEndSeconds-locomotion.loopStartSeconds)*locomotion.strideMeters)
            acceptCurrent(s)
            // The actual locomotion controller settles at its 1.30m desired range.
            ArenaSession::class.java.getDeclaredMethod("moveEnemy",java.lang.Long.TYPE,Vector3::class.java)
                .apply {isAccessible=true}.invoke(s,10_000_000L,Vector3(0.0,1.65,0.0))
            s.setArenaPresenter {_,_->}
            assertEquals(0f,s.viewState.enemyMoveDirection,0f)
            assertEquals("idle",s.viewState.enemyPoseClip)
            assertEquals(.75,checkNotNull(s.viewState.enemyPoseSourceSeconds),1e-12)
            assertNull(field(s,"heldEnemySourceJoin"))
        }
    }

    @Test fun guardedHitWithAnActualReturnStillPlaysTheEntireHurtAfterItsReturn() {
        val s=guardedReturn()
        val combat=field(s,"combat") as EnemyCombatStateMachine
        val stop=field(s,"hitStopNanos") as Long
        advance(s,stop+400_000_000L)
        assertEquals(500_000_000L,combat.phaseElapsedNanos)
        assertTrue(combat.guarding)
        assertEquals("hit_body",s.viewState.enemyPoseClip)
        assertEquals(.05,checkNotNull(s.viewState.enemyPoseSourceSeconds),1e-12)
        advance(s,100_000_000L)
        assertEquals("hit_body",s.viewState.enemyPoseClip)
        assertEquals(.05+(.72-.05)/3,checkNotNull(s.viewState.enemyPoseSourceSeconds),1e-9)
        assertEquals(64,combat.health)
    }

    @Test fun guardingDuringTheReturnCannotRemoveFutureHurtFromTheActorCertificate() {
        val s=guardedReturn()
        val current=local(s).pose
        @Suppress("UNCHECKED_CAST")
        val domain=ArenaSession::class.java.getDeclaredMethod("steelRecoverySamples",AttackPoseSample::class.java)
            .apply {isAccessible=true}.invoke(s,current) as List<AttackPoseSample>
        val body=arenaOpponents.first().reactionProfiles().body
        for(row in body.samples.filter {it.sourceSeconds in .05.. .72})
            assertTrue("Guard rules cannot hide future hurt source ${row.sourceSeconds}",domain.any {it.bladeGrip==row.bladeGrip && it.contact==row.contact})
    }

    @Test fun trackingReturnCompletionChecksTheSameClipClockJumpAndWithdrawsWithoutAPosePenetration() {
        val round=3;val opponent=arenaOpponents[round-1];val idle=opponent.locomotionProfile().idle
        val old=idle.sample(0.0).inStage(origin,0f)
        val wanted=idle.sample(.9).inStage(origin,0f)
        val player=obstructedGuard(old,wanted)
        assertTrue(gap(player,old.bladeGrip)>old.bladeGripInterpolationErrorToNextMeters)
        assertTrue(gap(player,wanted.bladeGrip)< -1e-7)
        val s=scene(round,player)
        val combat=EnemyCombatStateMachine();combat.advanceBy(800_000_000L,true);combat.tryStartAttack(AttackDirection.RIGHT,true);combat.advanceBy(423_076_923L,true)
        val profile=opponent.attackProfile(AttackDirection.RIGHT)
        val route=checkNotNull(makeEnemySourceReturn(EnemyPoseFrame(profile.clip,profile.sample(.5)),EnemyPoseFrame("idle",idle.sample(0.0)),profile.samples,listOf(0.0,1.75)))
        combat.interruptTracking();combat.tryResume(true,true,combat.currentPauseId,route.returnNanos)
        combat.advanceBy(route.returnNanos-1L,true)
        set(s,"combat",combat);set(s,"enemySourceReturn",route);set(s,"enemyMotionNanos",899_999_999L)
        acceptCurrent(s)
        val events=mutableListOf<EnemyCombatEvent>();s.setArenaPresenter {_,batch->events.addAll(batch)}
        advance(s,1L)
        assertEquals(EnemyPhase.IDLE,combat.phase)
        assertTrue("Same clip name cannot bypass the .0→.9 source-clock seam",gap(player,stage(s).bladeGrip)>=-1e-7)
        assertNotNull("A real pending source contact has a finite actor response",field(s,"steelWithdrawal"))
        var resumed=false
        repeat(100) {
            if(!resumed) {
                advance(s,5_000_000L)
                assertTrue("Actor response cannot penetrate the retained or newly admitted source",gap(player,stage(s).bladeGrip)>=-1e-7)
                resumed=field(s,"heldEnemySourceJoin")==null
            }
        }
        assertTrue("The source seam must resume after finite actor withdrawal",resumed)
        assertEquals(100,combat.health)
        assertTrue(events.none {it is CombatImpact || it is EnemyCombatEvent.EnemyDamaged})
    }

    private fun obstructedGuard(old:AttackPoseSample,wanted:AttackPoseSample):WeaponGrip {
        val shape=DaoBladeShape.shape;val a=shape.at(old.bladeGrip);val b=shape.at(wanted.bladeGrip)
        val directions=(a.indices.flatMap {listOf(b[it].base-a[it].base,b[it].tip-a[it].tip)}+
            (wanted.bladeGrip.position-old.bladeGrip.position)).mapNotNull {it.normalizedOrNull()}
        val playerParts=shape.at(WeaponGrip(Vector3(0.0,0.0,0.0),old.bladeGrip.rotation))
        for(n in directions) {
            val first=a.flatMap {p->listOf(p.base to p.radiusMeters,p.tip to p.radiusMeters)}.maxBy {(p,r)->p.dot(n)+r}
            val last=b.maxOf {p->maxOf(p.base.dot(n),p.tip.dot(n))+p.radiusMeters}
            val travel=last-(first.first.dot(n)+first.second)
            if(travel<20e-6)continue
            val facing=playerParts.flatMap {p->listOf(p.base to p.radiusMeters,p.tip to p.radiusMeters)}.minBy {(p,r)->p.dot(n)-r}
            val candidate=WeaponGrip(first.first+n*(first.second+facing.second+travel*.5)-facing.first,old.bladeGrip.rotation)
            if(gap(candidate,old.bladeGrip)>old.bladeGripInterpolationErrorToNextMeters*2 && gap(candidate,wanted.bladeGrip)< -1e-7)return candidate
        }
        error("Actual idle drift needs a real full-chain obstruction witness")
    }

    private fun guardedReturn():ArenaSession {
        val s=scene(1);val c=EnemyCombatStateMachine();c.advanceBy(800_000_000L,true);c.tryStartAttack(AttackDirection.RIGHT,true);c.advanceBy(423_076_923L,true)
        set(s,"combat",c);acceptCurrent(s)
        damage(s,71L);assertEquals(75,c.health);advance(s,70_000_000L+100_000_000L)
        assertEquals(100_000_000L,c.phaseElapsedNanos)
        damage(s,72L)
        assertTrue(c.guarding);assertEquals(64,c.health)
        assertEquals(500_000_000L,(field(s,"enemySourceReturn") as EnemySourceReturn).returnNanos)
        return s
    }
    private fun damage(s:ArenaSession,id:Long) {
        val frame=(field(s,"simulationMotion") as PlayerMotionFrame).copy(strike=MotionStrike(id,HitZone.BODY,1.0,
            MotionContact(HitZone.BODY,Vector3(0.0,1.1,-1.3),Vector3(1.0,0.0,0.0))))
        ArenaSession::class.java.getDeclaredMethod("applyPlayerMotion",PlayerMotionFrame::class.java,MutableList::class.java)
            .apply {isAccessible=true}.invoke(s,frame,mutableListOf<EnemyCombatEvent>())
        s.setArenaPresenter {_,_->}
    }
    private fun scene(round:Int,player:WeaponGrip=far):ArenaSession {
        val s=ArenaSession(logMessage={},logFailure={_,e->throw e});set(s,"roundNumber",round);s.setEnemyGeometry(origin,2.0)
        val tracking=TrackingState(Hand.RIGHT)
        val input=listOf(TrackingEvent.Head(ObservationStamp(0,0L,0L,InputOrigin.PICO),ObservedPose(Vector3(0.0,1.65,0.0),Quaternion(0.0,0.0,0.0,1.0))),
            TrackingEvent.Controllers(ObservationStamp(1,0L,0L,InputOrigin.PICO),null,ObservedPose(player.position,player.rotation)))
        for(e in input){val accepted=tracking.accept(e);assertTrue(accepted);s.onTrackingEvent(e,accepted,tracking.snapshot)}
        set(s,"result",TrialResult.FIGHTING);set(s,"trialStarted",true);set(s,"simulationMotion",checkNotNull(field(s,"latestMotion")))
        set(s,"recoilElapsedNanos",220_000_000L)
        return s
    }
    private fun collect(s:ArenaSession,incoming:List<EnemyCombatEvent>,events:MutableList<EnemyCombatEvent>) {
        ArenaSession::class.java.getDeclaredMethod("collect",List::class.java,MutableList::class.java).apply {isAccessible=true}.invoke(s,incoming,events)
    }
    private fun local(s:ArenaSession)=ArenaSession::class.java.getDeclaredMethod("effectiveEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as EnemyPoseFrame
    private fun stage(s:ArenaSession)=ArenaSession::class.java.getDeclaredMethod("enemyAttackPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as AttackPoseSample
    private fun acceptCurrent(s:ArenaSession) {
        // This fixture injects a timeline; initialize its corresponding accepted
        // source rather than reading the previously rendered authority.
        val source=ArenaSession::class.java.getDeclaredMethod("selectedEnemyPose",java.lang.Long.TYPE).apply {isAccessible=true}.invoke(s,0L) as EnemyPoseFrame
        set(s,"acceptedEnemySource",source);set(s,"acceptedSourceEpoch",field(s,"sourceEpoch") as Long)
    }
    private fun advance(s:ArenaSession,delta:Long) {
        val frame=field(s,"simulationMotion") as PlayerMotionFrame
        ArenaSession::class.java.getDeclaredMethod("advanceEnemy",java.lang.Long.TYPE,MutableList::class.java,java.lang.Long.TYPE,PlayerMotionFrame::class.java)
            .apply {isAccessible=true}.invoke(s,delta,mutableListOf<EnemyCombatEvent>(),frame.receivedAtNanos,frame.copy(receivedAtNanos=frame.receivedAtNanos+delta))
        s.setArenaPresenter {_,_->}
    }
    private fun gap(player:WeaponGrip,enemy:WeaponGrip)=DaoBladeShape.shape.at(player).minOf {p->DaoBladeShape.shape.at(enemy).minOf {e->val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip));pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters}}
    private fun field(s:ArenaSession,name:String)=ArenaSession::class.java.getDeclaredField(name).apply {isAccessible=true}.get(s)
    private fun set(s:ArenaSession,name:String,value:Any)=ArenaSession::class.java.getDeclaredField(name).apply {isAccessible=true}.set(s,value)
}
