package com.example.wuxiaarena.core.combat
import com.example.wuxiaarena.p0d2f0182.runtime.*
import com.example.wuxiaarena.core.math.*
import org.junit.Test
import org.junit.Assert.*
import kotlin.math.*
class BladeShapeWithdrawalBenchmarkTest {
    @Test fun actualOHFullRecoveryDomainHasFiniteCertifiedPlan() {
        val profile=arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD)
        val source=profile.sourcePhaseSeconds[2]
        val origin=Vector3(0.0,0.0,-1.3);val local=profile.sample(source);val pose=local.inStage(origin,0f)
        val rotation=Quaternion(0.0,-sqrt(.5),0.0,sqrt(.5));val axis=playerBlade(WeaponGrip(Vector3(0.0,0.0,0.0),rotation))
        var n=checkNotNull((axis.tip-axis.base).cross(pose.bladeTip-pose.bladeBase).normalizedOrNull());if(n.z<0)n=n*-1.0
        val target=WeaponGrip((pose.bladeBase+pose.bladeTip-axis.base-axis.tip)*.5+n*(axis.radiusMeters+.0125-1e-9),rotation)
        val clear=target.copy(position=target.position+n*.15);val shape=DaoBladeShape.shape
        val c=checkNotNull(firstBladeShapeContact(BladeShapeSweep(shape,clear,target,0.0),BladeShapeSweep(shape,pose.bladeGrip,pose.bladeGrip,local.bladeGripInterpolationErrorToNextMeters)))
        val numerical=c.contact.errorBoundMeters-local.bladeGripInterpolationErrorToNextMeters
        val grip=interpolateGrip(clear,target,(c.contact.fraction+2*numerical/clear.position.distanceTo(target.position)).coerceAtMost(1.0))
        val retreat=maxOf(profile.sourcePhaseSeconds.first(),source-.06)
        val recovery=(listOf(local,profile.sample(retreat),profile.sample(profile.sourcePhaseSeconds.last()))+profile.samples.filter {it.sourceSeconds>=retreat})
            .sortedBy {it.sourceSeconds}.distinctBy {it.sourceSeconds}.map {it.bladeGrip to it.bladeGripInterpolationErrorToNextMeters}
        val plan=ActorWithdrawalPlan.create(origin,0.0,local.bladeGrip,grip,c.contact.normal,local.bladeGripInterpolationErrorToNextMeters,recovery)
        assertNotNull(plan)

    }
}

internal object BladePlanBenchmark {
    fun record(category:String,origin:Vector3,yaw:Double,source:AttackPoseSample,grip:WeaponGrip,
        normal:Vector3,recovery:List<AttackPoseSample>) {
        val domain=recovery.map {it.bladeGrip to it.bladeGripInterpolationErrorToNextMeters}
        for((label,n) in listOf(category to normal,(category+"_opposed_direction_no_solution") to normal*-1.0)) {
            repeat(4) {ActorWithdrawalPlan.create(origin,yaw,source.bladeGrip,grip,n,source.bladeGripInterpolationErrorToNextMeters,domain)}
            var solved=0;val times=mutableListOf<Double>()
            repeat(7) {
                val start=System.nanoTime()
                val plan=ActorWithdrawalPlan.create(origin,yaw,source.bladeGrip,grip,n,source.bladeGripInterpolationErrorToNextMeters,domain)
                times+=(System.nanoTime()-start)/1e6;if(plan!=null)solved++
            }
            val ordered=times.sorted()
            println("BLADE_PLAN_BENCH {\"category\":\"$label\",\"calls\":7,\"warmup_calls\":4,\"solved\":$solved,\"source_rows\":${domain.size},\"median_wall_ms\":${ordered[3]},\"max_wall_ms\":${ordered.last()},\"wall_ms\":${times.joinToString(prefix="[",postfix="]")}}")
        }
    }
}
