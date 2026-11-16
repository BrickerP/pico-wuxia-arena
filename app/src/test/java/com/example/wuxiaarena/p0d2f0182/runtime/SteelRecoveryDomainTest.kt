package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.ActorWithdrawalPlan
import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.BladeSegment
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/** The exit certificate must cover exactly the future recovery, with its true interpolation edges. */
class SteelRecoveryDomainTest {
    private val direction=AttackDirection.OVERHEAD
    private val profile get()=arenaOpponents.first().attackProfile(direction)
    private val contactSeconds=5.0/6.0
    private val origin=Vector3(0.0,0.0,-1.3)

    @Test fun recoveryIncludesExactRetreatNonKeyCurrentAndEveryVisitedKeyOnly() {
        val p=profile
        val retreat=contactSeconds-.06
        assertEquals(.7733333333333333,retreat,1e-15)
        assertFalse("The lower edge must exercise interpolation, not accidentally be an authored key",
            p.samples.any { it.sourceSeconds==retreat })
        val time=contactSeconds+.002137
        assertFalse(p.samples.any { it.sourceSeconds==time })
        val current=p.sample(time).copy(bladeBase=p.sample(time).bladeBase+Vector3(.000123,0.0,0.0))
        val selected=select(p,current)
        assertEquals(p.sample(retreat),selected.first())
        assertEquals(current,selected.single { it.sourceSeconds==time })
        assertEquals(p.sample(p.sourcePhaseSeconds.last()),selected.last())
        assertTrue(selected.all { it.sourceSeconds>=retreat && it.sourceSeconds<=p.sourcePhaseSeconds.last() })
        val expected=(listOf(current,p.sample(retreat))+p.samples.filter {
            it.sourceSeconds>=retreat && it.sourceSeconds<=p.sourcePhaseSeconds.last()
        }).map { it.sourceSeconds }.toSet()
        assertEquals("No visited key or interpolated endpoint may disappear",expected,selected.map { it.sourceSeconds }.toSet())
        assertEquals(selected.size,selected.map { it.sourceSeconds }.toSet().size)
        val nonKeyEnd=p.sourcePhaseSeconds.last()-.002137
        assertFalse(p.samples.any { it.sourceSeconds==nonKeyEnd })
        val ended=AttackProfile(p.clip,p.sourcePhaseSeconds.dropLast(1)+nonKeyEnd,p.contactSourceSeconds,p.samples)
        assertEquals("A legal non-key recovery end also needs its exact interpolated witness",
            ended.sample(nonKeyEnd),select(ended,current).last())
        assertTrue(selected.zipWithNext().all { (a,b)->a.sourceSeconds<b.sourceSeconds })
        val stored=p.samples.first { it.sourceSeconds>retreat }
        val measured=stored.copy(bladeTip=stored.bladeTip+Vector3(0.0,.000321,0.0))
        assertEquals("An actual equal-time TOI witness wins over a stored key",measured,
            select(p,measured).single { it.sourceSeconds==measured.sourceSeconds })
    }

    @Test fun unvisitedWindupCannotChangeRecoveryOrTheCertifiedActorExit() {
        val p=profile;val current=p.sample(contactSeconds)
        val retreat=contactSeconds-.06
        val interpolationSupport=p.samples.last { it.sourceSeconds<retreat }.sourceSeconds
        val untouchedSupport=p.samples.single { it.sourceSeconds==interpolationSupport }
        val changed=p.samples.map { sample ->
            // Keep the lower interpolation support intact. Only truly unvisited keys are corrupted.
            if(sample.sourceSeconds<interpolationSupport)sample.copy(
                bladeBase=sample.bladeBase+Vector3(800.0,-500.0,900.0),
                bladeTip=sample.bladeTip+Vector3(-700.0,400.0,-600.0)) else sample
        }
        assertTrue(changed.zip(p.samples).any { (a,b)->a!=b })
        val mutated=copyProfile(p,changed)
        assertEquals(untouchedSupport,mutated.samples.single { it.sourceSeconds==interpolationSupport })
        val before=select(p,current);val after=select(mutated,current)
        assertEquals("Unplayed windup geometry must not leak into the future recovery hull",before,after)
        val f=contactFixture(current)
        val a=checkNotNull(plan(current,before,f))
        val b=checkNotNull(plan(current,after,f))
        val oldFull=(p.samples+current).sortedBy { it.sourceSeconds }.distinctBy { it.sourceSeconds }
        val old=checkNotNull(plan(current,oldFull,f))
        println("STEEL_DOMAIN_PAIRED oldSamples=${oldFull.size} futureSamples=${before.size} " +
            "oldYawDegrees=${Math.toDegrees(old.yawDeltaRadians)} newYawDegrees=${Math.toDegrees(a.yawDeltaRadians)} " +
            "oldSeconds=${old.durationSeconds} newSeconds=${a.durationSeconds} " +
            "oldRetreatMm=${old.retreatMeters*1000} newRetreatMm=${a.retreatMeters*1000}")
        assertEquals(a.yawDeltaRadians,b.yawDeltaRadians,0.0)
        assertEquals(a.retreatMeters,b.retreatMeters,0.0)
        assertEquals(a.durationSeconds,b.durationSeconds,0.0)
        assertEquals(a.exitSide,b.exitSide)
        assertEquals(a.at(a.durationSeconds),b.at(b.durationSeconds))
    }

    @Test fun actualRetreatAndReturnBoundaryGeometryCannotBeOmittedFromCertification() {
        val p=profile;val current=p.sample(contactSeconds);val f=contactFixture(current)
        val original=checkNotNull(plan(current,select(p,current),f))
        val final=original.at(original.durationSeconds)
        val overlapBase=rotate(f.player.base-final.position,-final.yawRadians)
        val overlapTip=rotate(f.player.tip-final.position,-final.yawRadians)
        for(edge in listOf(contactSeconds-.06,p.sourcePhaseSeconds.last())) {
            val bad=p.sample(edge).copy(bladeBase=overlapBase,bladeTip=overlapTip)
            val samples=(p.samples.filter { it.sourceSeconds!=edge }+bad).sortedBy { it.sourceSeconds }
            val changed=copyProfile(p,samples)
            val selected=select(changed,current)
            assertEquals("The exact recovery boundary must survive selection at $edge",bad,
                selected.single { it.sourceSeconds==edge })
            val oldWorld=world(bad,final.position,final.yawRadians)
            assertTrue("The deliberately changed boundary must invalidate the old plan",gap(f.player,oldWorld)<-.024)
            val replacement=plan(current,selected,f)
            if(replacement!=null) {
                assertFalse("Boundary corruption cannot retain the old certificate at $edge",
                    replacement.yawDeltaRadians==original.yawDeltaRadians &&
                        replacement.retreatMeters==original.retreatMeters && replacement.durationSeconds==original.durationSeconds)
                val exit=replacement.at(replacement.durationSeconds)
                assertTrue("A replacement certificate must actually clear the changed boundary at $edge",
                    gap(f.player,world(bad,exit.position,exit.yawRadians))>=0.0)
            }
        }
    }

    @Test fun noAttackRecoveryStillCertifiesTheFullIdleLoopAndItsCurrentWitness() {
        val session=ArenaSession(logMessage={},logFailure={_,e->throw e})
        val idle=arenaOpponents.first().locomotionProfile().idle
        val time=(idle.samples[0].sourceSeconds+idle.samples[1].sourceSeconds)*.5
        val current=idle.sample(time).copy(bladeTip=idle.sample(time).bladeTip+Vector3(.00017,0.0,0.0))
        val selected=invokeSelection(session,current)
        assertEquals(current,selected.single { it.sourceSeconds==time })
        for(sample in idle.samples)assertEquals("Idle key ${sample.sourceSeconds} must remain in its full loop",
            sample,selected.single { it.sourceSeconds==sample.sourceSeconds })
        assertEquals(idle.samples.size+1,selected.size)
        assertEquals(idle.samples.first(),selected.first())
        assertEquals(idle.samples.last(),selected.last())
    }

    private data class ContactFixture(val player:BladeSegment,val normal:Vector3)
    private fun contactFixture(current:AttackPoseSample):ContactFixture {
        val pose=current.inStage(origin,0f)
        val rotation=Quaternion(0.0,-sqrt(.5),0.0,sqrt(.5))
        val local=playerBlade(WeaponGrip(Vector3(0.0,0.0,0.0),rotation))
        var n=requireNotNull((local.tip-local.base).cross(pose.bladeTip-pose.bladeBase).normalizedOrNull())
        if(n.z<0.0)n=n*-1.0
        val grip=WeaponGrip((pose.bladeBase+pose.bladeTip-local.base-local.tip)*.5+
            n*(local.radiusMeters+.0125-1e-9),rotation)
        return ContactFixture(playerBlade(grip),n)
    }
    private fun plan(current:AttackPoseSample,samples:List<AttackPoseSample>,f:ContactFixture)=
        ActorWithdrawalPlan.create(origin,0.0,BladeSegment(current.bladeBase,current.bladeTip,.0125),f.player,f.normal,
            samples.map { BladeSegment(it.bladeBase,it.bladeTip,.0125) })
    private fun copyProfile(p:AttackProfile,samples:List<AttackPoseSample>)=
        AttackProfile(p.clip,p.sourcePhaseSeconds,p.contactSourceSeconds,samples)
    private fun select(profile:AttackProfile,current:AttackPoseSample):List<AttackPoseSample> {
        val session=ArenaSession(logMessage={},logFailure={_,e->throw e})
        val clazz=ArenaSession::class.java.declaredClasses.single { it.simpleName=="ContactRecovery" }
        val constructor=clazz.declaredConstructors.single { it.parameterTypes.size==5 }.apply { isAccessible=true }
        val recovery=constructor.newInstance(profile,direction,contactSeconds,0L,direction.recoveryNanos)
        ArenaSession::class.java.getDeclaredField("contactRecovery").apply { isAccessible=true }.set(session,recovery)
        return invokeSelection(session,current)
    }
    @Suppress("UNCHECKED_CAST")
    private fun invokeSelection(session:ArenaSession,current:AttackPoseSample):List<AttackPoseSample> =
        ArenaSession::class.java.getDeclaredMethod("steelRecoverySamples",AttackPoseSample::class.java)
            .apply { isAccessible=true }.invoke(session,current) as List<AttackPoseSample>
}
private fun rotate(v:Vector3,yaw:Double)=Vector3(v.x*cos(yaw)+v.z*sin(yaw),v.y,-v.x*sin(yaw)+v.z*cos(yaw))
private fun world(sample:AttackPoseSample,position:Vector3,yaw:Double)=BladeSegment(
    position+rotate(sample.bladeBase,yaw),position+rotate(sample.bladeTip,yaw),.0125)
private fun gap(a:BladeSegment,b:BladeSegment):Double {
    val pair=checkNotNull(closestSegmentPoints(a.base,a.tip,b.base,b.tip))
    return pair.first.distanceTo(pair.second)-a.radiusMeters-b.radiusMeters
}
