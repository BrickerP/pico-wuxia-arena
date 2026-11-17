package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.Quaternion
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.*

class BladeShapeTest {
    private val shape=DaoBladeShape.shape
    private val identity=WeaponGrip(Vector3(0.0,0.0,0.0),Quaternion(0.0,0.0,0.0,1.0))
    private fun sweep(a:WeaponGrip=identity,b:WeaponGrip=a,error:Double=0.0)=BladeShapeSweep(shape,a,b,error)
    private fun sphere(point:Vector3,r:Double=.0001)=BladeSegment(point,point,r).let { BladeSweep(it,it) }
    @Test fun frozenDescriptorHas18Parts6GroupsAndSub10mmRadii() {
        assertEquals(18,shape.parts.size);assertTrue(shape.parts.all { it.radiusMeters in .0089..0.009584 })
        assertTrue(shape.gripRadius>.84)
    }
    @Test fun actualVertex2046OutsideOldAxisBy44994mmIsCoveredByChain() {
        val point=Vector3(-.014000000432133675,-.0018720000516624373,-.6140000000596048)
        assertNull(firstRigidBladeContact(identity,identity,sphere(point)))
        val contact=checkNotNull(firstBladeShapeBodyContact(sweep(),sphere(point)))
        assertTrue(contact.playerPartIndex in 0..17);assertEquals(-1,contact.enemyPartIndex)
        assertEquals(0.0,contact.contact.fraction,0.0)
    }
    @Test fun farAirSwingIsCulledBeforeAnyCapsuleCCD() {
        val stats=BladeQueryStats();val enemy=identity.copy(position=Vector3(4.0,0.0,0.0))
        assertNull(firstBladeShapeContact(sweep(),sweep(enemy),stats));assertEquals(0L,stats.capsuleQueries)
        assertEquals(1L,stats.wholeBounds)
    }
    @Test fun earliestPartWinsInsteadOfDescriptorOrder() {
        val body=sphere(Vector3(0.0,0.0,-.614),.005)
        val from=identity.copy(position=Vector3(-.3,0.0,0.0));val to=identity.copy(position=Vector3(.3,0.0,0.0))
        val hit=checkNotNull(firstBladeShapeBodyContact(sweep(from,to),body))
        assertTrue(hit.contact.fraction in .2..0.6)
        assertTrue(hit.contact.separationMeters<=hit.contact.errorBoundMeters+1e-7)
    }
    @Test fun rigidRotationArcHitsWhereLinearEndpointsMiss() {
        val q0=Quaternion(0.0,sin(-PI/4),0.0,cos(-PI/4));val q1=Quaternion(0.0,sin(PI/4),0.0,cos(PI/4))
        val a=identity.copy(rotation=q0);val b=identity.copy(rotation=q1)
        val body=sphere(Vector3(.052,0.0,-.83),.002)
        val linearHits=shape.at(a).zip(shape.at(b)).any { (x,y)->firstBladeContact(BladeSweep(x,y),body)!=null }
        assertFalse(linearHits)
        val stats=BladeQueryStats();assertNotNull(firstBladeShapeBodyContact(sweep(a,b),body,stats))
        assertTrue(stats.angularIntervals>1)
    }
    @Test fun rollIsRequiredAndChangesThinSideContact() {
        val body=sphere(Vector3(-.014000000432133675,-.0018720000516624373,-.6140000000596048),.0001)
        val rolled=identity.copy(rotation=Quaternion(0.0,0.0,sin(PI/4),cos(PI/4)))
        assertNotEquals(firstBladeShapeBodyContact(sweep(),body)!=null,
            firstBladeShapeBodyContact(sweep(rolled),body)!=null)
    }
    @Test fun excessiveOrMissingSourceEnvelopeFailsExplicitly() {
        try { firstBladeShapeContact(sweep(error=.002001),sweep());fail("must not become MISS") }
        catch(e:BladeContactUncertainException){assertEquals(0.0,e.earliestUnresolvedFraction,0.0)}
        try {sweep(error=Double.NaN);fail("finite bound required")}catch(_:IllegalArgumentException){}
    }
    @Test fun fullChainCatchupCannotPassThroughEnemy() {
        val constraint=WeaponContactConstraint()
        val held=identity.copy(position=Vector3(-.3,0.0,0.0));val raw=identity.copy(position=Vector3(.3,0.0,0.0))
        constraint.lock(held,held,Vector3(-1.0,0.0,0.0))
        assertFalse(constraint.releaseIfSeparated(sweep(),clearanceMeters=.025,rawGrip=raw))
        assertTrue(constraint.constrained);assertEquals(held,constraint.apply(raw))
    }
    @Test fun fullChainClearCatchupReleasesAndRawTrackingIsUntouched() {
        val constraint=WeaponContactConstraint();val raw=identity.copy(position=Vector3(.02,0.0,0.0))
        constraint.lock(identity,identity,Vector3(1.0,0.0,0.0))
        assertEquals(identity,constraint.apply(raw))
        assertTrue(constraint.releaseIfSeparated(sweep(identity.copy(position=Vector3(3.0,0.0,0.0))),rawGrip=raw))
        assertEquals(raw,constraint.apply(raw))
    }
    @Test fun withdrawalRejectsInitiallyEmbeddedWholeChain() {
        val far=identity.copy(position=Vector3(0.0,0.0,1.0))
        assertNull(ActorWithdrawalPlan.create(Vector3(0.0,0.0,0.0),0.0,identity,identity,
            Vector3(0.0,0.0,-1.0),0.0,listOf(identity to 0.0)))
    }
    @Test fun badShapeCountAndNonfiniteRadiusAreRejected() {
        try {BladeShape(shape.parts.dropLast(1));fail()}catch(_:IllegalArgumentException){}
        try {BladeSegment(Vector3(0.0,0.0,0.0),Vector3(0.0,0.0,1.0),Double.NaN);fail()}catch(_:IllegalArgumentException){}
    }
    @Test fun unresolvedEarlierThanBestNeverBecomesMissOrLaterHit() {
        val hit=checkNotNull(firstBladeShapeBodyContact(sweep(),sphere(Vector3(-.014,-.0018,-.614))))
        val order=ShapeContactOrder();order.contact(hit.copy(contact=hit.contact.copy(fraction=.7)));order.uncertain(.2)
        try {order.result();fail("earlier uncertainty must dominate")}catch(e:BladeContactUncertainException){assertEquals(.2,e.earliestUnresolvedFraction,0.0)}
        val later=ShapeContactOrder();later.contact(hit.copy(contact=hit.contact.copy(fraction=.1)));later.uncertain(.8)
        assertEquals(.1,checkNotNull(later.result()).contact.fraction,0.0)
        val miss=ShapeContactOrder();miss.uncertain(.4)
        try {miss.result();fail("uncertainty is not MISS")}catch(_:BladeContactUncertainException){}
    }

    @Test fun routeCertificateRejectsAnyDifferentSourcePlayerActorOrTime() {
        val origin=Vector3(0.0,0.0,-1.0)
        val plan=checkNotNull(ActorWithdrawalPlan.create(origin,0.0,identity,identity,Vector3(0.0,0.0,1.0),0.0,listOf(identity to 0.0)))
        val end=minOf(.005,plan.durationSeconds)
        fun cert(player:WeaponGrip=identity,source:WeaponGrip=identity,actor:ActorWithdrawalPose=plan.at(end),time:Double=end)=
            plan.certifiesInterval(0.0,time,identity,player,identity,source,plan.at(0.0),actor)
        assertTrue(cert())
        assertFalse(cert(player=identity.copy(position=Vector3(.001,0.0,0.0))))
        assertFalse(cert(source=identity.copy(rotation=Quaternion(0.0,0.0,sin(.001),cos(.001)))))
        assertFalse(cert(actor=plan.at(end).copy(position=origin+Vector3(.001,0.0,0.0))))
        assertFalse(cert(time=plan.durationSeconds+.001))
    }
    @Test fun hugeFiniteCoordinatesWithInfiniteGripRadiusAreRejected() {
        val huge=BladeSegment(Vector3(1.7e308,1.7e308,0.0),Vector3(1.7e308,1.7e308,0.0),0.0)
        try {BladeShape(List(18){huge});fail("must not produce billions of angular subdivisions")}catch(_:IllegalArgumentException){}
    }

}
