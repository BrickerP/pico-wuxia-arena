package com.example.wuxiaarena.core.combat
import com.example.wuxiaarena.core.math.*
import org.junit.Test
import org.junit.Assert.*
import kotlin.math.*

class NativeRouteProbeTest {
    @Test fun actualNativeFreezeContainsSafeFixedOriginRotationExit() {
        val f=NativeFreezeFixture;val shape=DaoBladeShape.shape
        val held=shape.at(f.held);val enemy=shape.at(f.enemy)
        fun gap(parts:List<BladeSegment>)=parts.minOf {p->enemy.minOf {e->
            val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip));pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters
        }}
        val initialGap=gap(held)
        var clear=0;var trulyClear=0;var certified=0;var released=0;var oldNormalAccepted=0
        val rows=mutableListOf<String>();var firstSafe=-1
        for((index,raw) in f.raw.withIndex()) {
            assertEquals(f.held.position,raw.position)
            val parts=shape.at(raw);val rawGap=gap(parts)
            val minNormal=held.indices.minOf {i->minOf((parts[i].base-held[i].base).dot(f.normal),(parts[i].tip-held[i].tip).dot(f.normal))}
            val maxTravel=held.indices.maxOf {i->maxOf(parts[i].base.distanceTo(held[i].base),parts[i].tip.distanceTo(held[i].tip))}
            val path=BladeShapeSweep(shape,f.held,raw,0.0)
            val routeSafe=if(rawGap>1e-7+f.sourceError)separatingBladeShapePairs(path,f.enemySweep) else false
            val constraint=WeaponContactConstraint();constraint.lock(raw,f.held,f.normal)
            val release=constraint.releaseForPlayerWithdrawal(f.enemySweep,raw)
            if(rawGap>.025+f.sourceError)clear++
            if(rawGap>1e-7+f.sourceError)trulyClear++
            if(routeSafe){certified++;if(firstSafe<0)firstSafe=index}
            if(release)released++
            if(minNormal>=.025)oldNormalAccepted++
            rows+="{\"index\":$index,\"raw_gap_m\":$rawGap,\"minimum_original_normal_travel_m\":$minNormal,\"maximum_material_travel_m\":$maxTravel,\"route_certified\":$routeSafe,\"released\":$release}"
        }
        val globalLimit=held.minOf {minOf(it.base.dot(f.normal),it.tip.dot(f.normal))-it.radiusMeters}
        val globalSupport=enemy.maxOf {maxOf(it.base.dot(f.normal),it.tip.dot(f.normal))+it.radiusMeters+f.sourceError}
        val away=checkNotNull(Vector3(-f.normal.x,0.0,-f.normal.z).normalizedOrNull())
        val globalRetreat=maxOf(.0495,(globalSupport-globalLimit+.025)/(-f.normal.dot(away)))
        val output="{\"initial_nominal_gap_m\":$initialGap,\"source_error_m\":${f.sourceError},\"global_initial_retreat_m_for_current_stop_normal\":$globalRetreat,\"normal_is_cached_attempt_normal\":false,\"clear_raw_count\":$clear,\"certified_raw_count\":$certified,\"released_raw_count\":$released,\"old_normal_gate_count\":$oldNormalAccepted,\"first_certified_index\":$firstSafe,\"rows\":[${rows.joinToString(",")}] }"
        println("NATIVE_EXIT_RECEIPT $output")
        println("NATIVE_EXIT_PROBE nominalGap=$initialGap sourceError=${f.sourceError} rawClear25=$clear trueClear=$trulyClear certified=$certified released=$released oldNormalPass=$oldNormalAccepted firstSafe=$firstSafe globalStepUsingStopNormal=$globalRetreat")
        assertTrue("Recorded raw turns contain a fully clear whole dao",trulyClear>0)
        assertTrue("A recorded natural rotation path is certifiably nonpenetrating",certified>0)
        assertTrue("The same native raw pose can release without moving the Grip origin",released>0)
    }
}
