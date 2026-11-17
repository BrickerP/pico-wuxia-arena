package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test

internal object NativeDdacFixture {
    const val sourceSeconds=1.076918782
    val origin=Vector3(0.0,0.02800000086426735,-1.7143233036696164)
    val localEnemy=WeaponGrip(Vector3(-0.16946602852730444,1.22885301170023,0.2673110985322013),
        Quaternion(0.6379390737440933,-0.6379685080585878,0.30495151036566764,0.3050155688513718))
    const val sourceError=2.3045287372084896e-6
    val held=WeaponGrip(Vector3(0.27800002694129944,1.399999976158142,-0.4499998390674591),
        Quaternion(0.13058502476480985,0.32231457798199725,2.9802324809239934e-8,0.9375824572417406))
    val normal=Vector3(0.21543877667565026,-0.6357243392589679,0.7412426714499429)
}

class NativeDdacGeometryTest {
    @Test fun exactCachedBossGeometryClassifiesTheActualFreezeBeforeAnyRepair() {
        val f=NativeDdacFixture;val opponent=arenaOpponents[2]
        val local=opponent.locomotionProfile().idle.sample(f.sourceSeconds)
        assertTrue(local.bladeGrip.position.distanceTo(f.localEnemy.position)<1e-12)
        val a=checkNotNull(local.bladeGrip.rotation.normalizedOrNull());val b=checkNotNull(f.localEnemy.rotation.normalizedOrNull())
        assertTrue(kotlin.math.abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w)>1-1e-14)
        assertEquals(f.sourceError,local.bladeGripInterpolationErrorToNextMeters,1e-16)
        val idle=local.inStage(f.origin,0f)
        val walk=opponent.locomotionProfile().walk.sample(.75).inStage(f.origin,0f)
        val shape=DaoBladeShape.shape
        fun gap(enemy:WeaponGrip)=shape.at(f.held).flatMapIndexed {i,p->shape.at(enemy).mapIndexed {j,e->
            val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip))
            Triple(pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters,i,j)
        }}.minBy {it.first}
        val now=gap(idle.bladeGrip);val old=gap(walk.bladeGrip)
        val player=shape.at(f.held)[now.second];val enemy=shape.at(idle.bladeGrip)[now.third]
        val pair=checkNotNull(closestSegmentPoints(player.base,player.tip,enemy.base,enemy.tip))
        val closest=checkNotNull((pair.first-pair.second).normalizedOrNull())
        val delta=shape.at(walk.bladeGrip).indices.maxOf {i->maxOf(shape.at(walk.bladeGrip)[i].base.distanceTo(shape.at(idle.bladeGrip)[i].base),shape.at(walk.bladeGrip)[i].tip.distanceTo(shape.at(idle.bladeGrip)[i].tip))}
        println("DDAC_GEOMETRY cachedIdleGapM=${now.first} correctedGapM=${now.first-f.sourceError} playerPart=${now.second} enemyPart=${now.third} normalDot=${closest.dot(f.normal)} sameActorWalkGapM=${old.first} walkErrorM=${walk.bladeGripInterpolationErrorToNextMeters} walkToIdleEndpointChangeM=$delta")
        assertTrue("The actual cached IDLE starts penetrated",now.first < -1e-4)
        assertTrue("The same exact held Grip is clear against actual WALK",old.first >1e-4)
        assertEquals(1.0,closest.dot(f.normal),1e-12)
    }
    @Test fun theReconstructedObservedHoldHasASafeWalkExitAtTheSameCachedActor() {
        val f=NativeDdacFixture
        val walk=arenaOpponents[2].locomotionProfile().walk.sample(.75).inStage(f.origin,0f)
        // Known fixed Grip origin plus two non-collinear virtual anchors, not
        // the distinct raw quaternion printed in the same observation.
        val old=WeaponGrip(f.held.position,Quaternion(0.1299625774289305,0.32062102030323847,-5.351478253851258e-8,0.9382493750638669))
        val axis=playerBlade(old)
        assertTrue(axis.base.distanceTo(Vector3(0.2178647260761975,1.4332932278994446,-0.5613564957088738))<1e-13)
        assertTrue(axis.tip.distanceTo(Vector3(-0.19053420862299003,1.6114831006447217,-1.127776939714553))<1e-13)
        val shape=DaoBladeShape.shape
        val closest=shape.at(old).flatMap {p->shape.at(walk.bladeGrip).map {e->
            val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip))
            (pair.first.distanceTo(pair.second)-p.radiusMeters-e.radiusMeters) to checkNotNull((pair.first-pair.second).normalizedOrNull())
        }}.minBy {it.first}
        val sweep=BladeShapeSweep(shape,walk.bladeGrip,walk.bladeGrip,walk.bladeGripInterpolationErrorToNextMeters)
        val proof=separatingBladeShapePairs(BladeShapeSweep(shape,old,f.held,0.0),sweep,closest.second)
        println("DDAC_REAL_WRIST oldWalkGapM=${closest.first} sourceE=${walk.bladeGripInterpolationErrorToNextMeters} routeCertified=$proof")
        assertTrue("At this cached actor transform the observed virtual→raw movement has a full-chain safe route",proof)
        val constraint=WeaponContactConstraint();constraint.lock(old,old,closest.second)
        assertTrue(constraint.releaseForPlayerWithdrawal(sweep,f.held))
        assertFalse(constraint.constrained)
    }
    @Test fun recordedClearRawTargetsCannotTurnTheActualPenetratedIdleStartIntoAProvedExit() {
        val f=NativeDdacFixture;val shape=DaoBladeShape.shape
        val idle=arenaOpponents[2].locomotionProfile().idle.sample(f.sourceSeconds).inStage(f.origin,0f)
        val enemy=BladeShapeSweep(shape,idle.bladeGrip,idle.bladeGrip,idle.bladeGripInterpolationErrorToNextMeters)
        var targetClear=0;var certified=0;var released=0
        for(row in NativeDdacTrace.frozenRaw) {
            val raw=row.grip
            if(firstBladeShapeContact(BladeShapeSweep(shape,raw,raw,0.0),enemy)==null)targetClear++
            if(separatingBladeShapePairs(BladeShapeSweep(shape,f.held,raw,0.0),enemy,f.normal))certified++
            val constraint=WeaponContactConstraint();constraint.lock(f.held,f.held,f.normal)
            if(constraint.releaseForPlayerWithdrawal(enemy,raw))released++
        }
        println("DDAC_RAW_ROUTES rows=${NativeDdacTrace.frozenRaw.size} targetClear=$targetClear certified=$certified released=$released")
        assertTrue(targetClear>0)
        assertEquals(0,certified);assertEquals(0,released)
    }
}
