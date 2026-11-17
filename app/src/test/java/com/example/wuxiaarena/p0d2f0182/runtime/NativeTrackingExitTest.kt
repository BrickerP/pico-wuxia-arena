package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

/** Recorded a88 freeze values through the real TrackingState/observe/coordinator consumer. */
class NativeTrackingExitTest {
    @Test fun recordedSafeWristExitReleasesTheNativeFreezeForDesktopAndPicoIdentically() {
        val desktop=exercise(InputOrigin.DESKTOP)
        val pico=exercise(InputOrigin.PICO)
        assertEquals(desktop,pico)
    }
    private fun exercise(origin:InputOrigin):List<Any> {
        val f=NativeFreezeFixture
        val events=mutableListOf<EnemyCombatEvent>()
        val session=ArenaSession(logMessage={},logFailure={_,e->throw e})
        session.setEnemyGeometry(f.origin,2.0)
        val impactSwingIds=mutableListOf<Long>()
        session.setArenaPresenter {_,batch->
            events.addAll(batch)
            if(batch.any {it is CombatImpact})impactSwingIds+=field(session,"consumedStrikeId") as Long
        }
        val tracking=TrackingState(Hand.RIGHT)
        var now=0L;var sequence=0L
        fun stamp()=ObservationStamp(sequence++,now,0L,origin)
        fun send(e:TrackingEvent) {val accepted=tracking.accept(e);assertTrue(accepted);session.onTrackingEvent(e,accepted,tracking.snapshot)}
        fun observe(grip:WeaponGrip) {
            send(TrackingEvent.Head(stamp(),ObservedPose(Vector3(0.0,1.649999976158142,0.0),Quaternion(0.0,0.0,0.0,1.0))))
            send(TrackingEvent.Controllers(stamp(),null,ObservedPose(grip.position,grip.rotation)))
        }
        // This fixture starts from the already accepted BLOCK id8 recorded on native,
        // not an invented collision-safe baseline. The independent 3-point reconstruction
        // and JDWP full Grip match to <4e-16m, including roll.
        observe(f.held)
        val motion=field(session,"motion") as PlayerCombatResolver
        val frame=field(session,"latestMotion") as PlayerMotionFrame
        val constraint=field(motion,"weaponConstraint") as WeaponContactConstraint
        constraint.lock(checkNotNull(frame.rawWeaponGrip),f.held,f.normal)
        set(motion,"strokeHasHit",true)
        val held=motion.applyWeaponConstraint(frame)
        val combat=EnemyCombatStateMachine()
        combat.advanceBy(800_000_000L,true);combat.tryStartAttack(AttackDirection.RIGHT,true)
        combat.advanceBy(AttackDirection.RIGHT.preparationNanos+AttackDirection.RIGHT.startupNanos+AttackDirection.RIGHT.activeNanos,true)
        combat.javaClass.getDeclaredField("health").apply {isAccessible=true}.setInt(combat,3)
        set(session,"combat",combat);set(session,"result",TrialResult.FIGHTING);set(session,"trialStarted",true)
        set(session,"enemyYaw",f.yaw.toFloat());set(session,"playerHealth",80)
        set(session,"steelContactLatched",true);set(session,"simulationMotion",held);set(session,"latestMotion",held)
        set(session,"observedAttackId",checkNotNull(combat.currentAttackId));set(session,"resolvedContactId",checkNotNull(combat.currentAttackId))
        val profile=arenaOpponents.first().attackProfile(AttackDirection.RIGHT)
        val expected=profile.sample(f.sourceSeconds)
        assertTrue(expected.bladeGrip.position.distanceTo(f.localEnemy.position)<1e-12)
        val recoveryType=ArenaSession::class.java.declaredClasses.single {it.simpleName=="ContactRecovery"}
        val recovery=recoveryType.declaredConstructors.single {it.parameterTypes.size==5}.apply {isAccessible=true}
            .newInstance(profile,AttackDirection.RIGHT,.5073453745454546,907211557663L,600_000_000L)
        set(session,"contactRecovery",recovery);set(session,"enemyMotionNanos",907264579797L)
        // The recorded a88 state already accepted this exact recovery source.
        val clockFrame=ArenaSession::class.java.getDeclaredMethod("selectedEnemyPose",java.lang.Long.TYPE)
            .apply {isAccessible=true}.invoke(session,0L) as EnemyPoseFrame
        // The old JDI source witness has sub-nanosecond TOI interpolation precision;
        // this injected runtime clock is integer nanoseconds. Keep the original
        // exact witness assertion above and certify their numerical equivalence.
        // Nearest integer-nanosecond clock uncertainty mapped through the actual
        // recorded retreat formula; no runtime time/geometry tolerance is widened.
        val sourceQuantum=.5e-9*.06/(.18*((600_000_000L-35_000_000L)/1e9))
        assertTrue(kotlin.math.abs(clockFrame.pose.sourceSeconds-f.sourceSeconds)<=sourceQuantum)
        val lo=profile.samples.last {it.sourceSeconds<=f.sourceSeconds}
        val hi=profile.samples.first {it.sourceSeconds>f.sourceSeconds}
        assertTrue(clockFrame.pose.sourceSeconds in lo.sourceSeconds..hi.sourceSeconds)
        val qa=checkNotNull(lo.bladeGrip.rotation.normalizedOrNull());val qb=checkNotNull(hi.bladeGrip.rotation.normalizedOrNull())
        val angle=2*kotlin.math.acos(kotlin.math.abs(qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w).coerceIn(0.0,1.0))
        val radius=DaoBladeShape.shape.gripRadius+DaoBladeShape.shape.parts.maxOf {it.radiusMeters}
        val velocity=(lo.bladeGrip.position.distanceTo(hi.bladeGrip.position)+radius*angle)/(hi.sourceSeconds-lo.sourceSeconds)
        val quantizedPointBound=velocity*sourceQuantum+64*Math.ulp(2.0)
        val oldSteel=DaoBladeShape.shape.at(expected.bladeGrip)
        val clockSteel=DaoBladeShape.shape.at(clockFrame.pose.bladeGrip)
        assertTrue(oldSteel.indices.all {i->maxOf(oldSteel[i].base.distanceTo(clockSteel[i].base),oldSteel[i].tip.distanceTo(clockSteel[i].tip))<=quantizedPointBound})
        set(session,"acceptedEnemySource",clockFrame)
        session.onTick(now)
        val beforeHealth=session.viewState.health;val beforePlayer=session.viewState.playerHealth
        val raw=f.raw[7]
        assertTrue("This actual native low-angle turn was clear by 10.82mm, below the old 25mm gate",raw.position==f.held.position)
        now+=20_000_000L;observe(raw);session.onTick(now)
        assertFalse("A certified actual native wrist exit must release the virtual whole dao",motion.weaponConstrained)
        val released=checkNotNull(session.viewState.playerWeaponGrip)
        assertEquals(raw.position,released.position)
        assertEquals(beforeHealth,session.viewState.health);assertEquals(beforePlayer,session.viewState.playerHealth)
        assertTrue(events.none {it is CombatImpact || it is EnemyCombatEvent.EnemyDamaged})
        // Holding the released real pose must not farm another contact or damage.
        repeat(8) {now+=10_000_000L;observe(raw);session.onTick(now)}
        assertTrue(events.none {it is CombatImpact || it is EnemyCombatEvent.EnemyDamaged})
        var escaped=false;var previousRaw=raw
        replay@for(target in f.raw.drop(8)) {
            val qa=checkNotNull(previousRaw.rotation.normalizedOrNull());val qb=checkNotNull(target.rotation.normalizedOrNull())
            val angle=2*kotlin.math.acos(kotlin.math.abs(qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w).coerceIn(0.0,1.0))
            val steps=kotlin.math.ceil(angle/.02).toInt().coerceAtLeast(1)
            for(index in 1..steps) {
                val pose=interpolateGrip(previousRaw,target,index.toDouble()/steps)
                now+=10_000_000L;observe(pose);session.onTick(now)
                if(session.viewState.phase!=EnemyPhase.RECOVERING && field(session,"contactRecovery")==null) {escaped=true;break@replay}
                if(now>=3_000_000_000L)break@replay
            }
            previousRaw=target
        }
        assertTrue("The recorded outward turns and finite NPC response must leave the original frozen recovery within 3s",escaped)
        assertEquals(beforeHealth,session.viewState.health);assertEquals(beforePlayer,session.viewState.playerHealth)
        assertTrue(events.none {it is EnemyCombatEvent.EnemyDamaged})
        assertEquals("Each real new contact during moving replay consumes a distinct admitted Swing",impactSwingIds.size,impactSwingIds.distinct().size)
        assertTrue(impactSwingIds.all {it>=0})
        println("NATIVE_TRACKING_EXIT origin=$origin released=true escapedOriginalRecovery=true elapsedMs=${now/1e6} enemyHP=$beforeHealth playerHP=$beforePlayer")
        return listOf(released.position,released.rotation,session.viewState.health,session.viewState.playerHealth,events.size)
    }
    private fun field(o:Any,n:String)=o.javaClass.getDeclaredField(n).apply {isAccessible=true}.get(o)
    private fun set(o:Any,n:String,value:Any)=o.javaClass.getDeclaredField(n).apply {isAccessible=true}.set(o,value)
}
