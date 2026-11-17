package com.example.wuxiaarena.p0d2f0182.runtime
import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.math.*
import org.junit.Test
import org.junit.Assert.*
import kotlin.math.*

class NativeActorProbeTest {
    @Test fun quantifyProvidedStopNormalWithoutMislabelingItAsMissingCachedNormal() {
        val f=NativeFreezeFixture;val profile=arenaOpponents.first().attackProfile(AttackDirection.RIGHT)
        val current=profile.sample(f.sourceSeconds)
        val retreat=.5073453745454546-.06
        val recovery=(listOf(current,profile.sample(retreat),profile.sample(profile.sourcePhaseSeconds.last()))+profile.samples.filter {it.sourceSeconds>=retreat})
            .sortedBy {it.sourceSeconds}.distinctBy {it.sourceSeconds}
        val player=DaoBladeShape.shape.at(f.held);val enemy=DaoBladeShape.shape.at(f.enemy)
        val n=f.normal;val away=checkNotNull(Vector3(-n.x,0.0,-n.z).normalizedOrNull())
        val limit=player.minOf {minOf(it.base.dot(n),it.tip.dot(n))-it.radiusMeters}
        val support=enemy.maxOf {maxOf(it.base.dot(n),it.tip.dot(n))+it.radiusMeters+f.sourceError}
        val step=maxOf(.0495,(support-limit+.025)/(-n.dot(away)))
        var minStart=Double.POSITIVE_INFINITY;var minEnd=Double.POSITIVE_INFINITY
        for(p in player)for(e in enemy) {
            val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip));val plane=checkNotNull((pair.first-pair.second).normalizedOrNull())
            val gap=minOf(p.base.dot(plane),p.tip.dot(plane))-maxOf(e.base.dot(plane),e.tip.dot(plane))-p.radiusMeters-e.radiusMeters-f.sourceError
            minStart=minOf(minStart,gap);minEnd=minOf(minEnd,gap-plane.dot(away)*step)
        }
        val plan=ActorWithdrawalPlan.create(f.origin,f.yaw,current.bladeGrip,f.held,n,f.sourceError,
            recovery.map {it.bladeGrip to it.bladeGripInterpolationErrorToNextMeters})
        val moved=f.enemy.copy(position=f.enemy.position+away*step)
        val initialRoute=separatingBladeShapePairs(BladeShapeSweep(DaoBladeShape.shape,f.enemy,moved,f.sourceError),
            BladeShapeSweep(DaoBladeShape.shape,f.held,f.held,0.0))
        println("NATIVE_ACTOR_PROBE stopNormalNotCachedNormal=true globalInitialStep=$step minInitialPairPlane=$minStart minFinalOldPairPlane=$minEnd fullInitialRouteCertified=$initialRoute finitePlan=${plan!=null} retreat=${plan?.retreatMeters} yaw=${plan?.yawDeltaRadians} duration=${plan?.durationSeconds} recoveryRows=${recovery.size}")
        assertTrue("The provided Stop normal does not trigger the >35cm early gate",step<.35)
        assertTrue("The actual whole initial route is nonpenetrating despite the old initial-plane rejection",initialRoute)
        assertNotNull("This real held source/whole-chain recovery has a finite certified actor escape",plan)
        assertTrue(checkNotNull(plan).retreatMeters<=.35)
        assertTrue(kotlin.math.abs(plan.yawDeltaRadians)<=PI/2)
    }
}
