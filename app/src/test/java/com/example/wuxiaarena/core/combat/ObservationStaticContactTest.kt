package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test
import java.util.Random
import kotlin.math.*

/** Independent zero-tolerance reference to the existing complete static shape CCD. */
class ObservationStaticContactTest {
    private val identity=Quaternion(0.0,0.0,0.0,1.0)
    private val baseLocal=Vector3(.022,0.0,-.129)
    private val far=Vector3(8.0,8.0,8.0)
    private val sampleClass=Class.forName("com.example.wuxiaarena.core.combat.PlayerCombatResolver\$BladeSample")
    private val sampleConstructor=sampleClass.declaredConstructors.single {it.parameterCount==4}.apply {isAccessible=true}
    private val staticMethod by lazy {PlayerCombatResolver::class.java.declaredMethods.single {it.name=="staticContact" && it.parameterCount==2}.apply {isAccessible=true}}
    private data class Sample(val opaque:Any,val reconstructed:WeaponGrip)
    private fun sample(grip:WeaponGrip):Sample {
        val blade=playerBlade(grip)
        val reconstructed=WeaponGrip(blade.base-checkNotNull(grip.rotation.rotate(baseLocal)),grip.rotation)
        return Sample(sampleConstructor.newInstance(ObservationStamp(1,0,0,InputOrigin.SYNTHETIC),blade.base,blade.tip,grip.rotation),reconstructed)
    }
    private fun actual(resolver:PlayerCombatResolver,sample:Sample,pose:EnemyContactPose):MotionContact? =
        staticMethod.invoke(resolver,sample.opaque,pose) as MotionContact?
    private fun reference(grip:WeaponGrip,pose:EnemyContactPose):MotionContact? {
        val shape=BladeShapeSweep(DaoBladeShape.shape,grip,grip,0.0)
        fun hit(zone:HitZone,start:Vector3,end:Vector3,radius:Double):Pair<BladeContact,HitZone>? {
            val body=BladeSegment(start,end,radius)
            return firstBladeShapeBodyContact(shape,BladeSweep(body,body))?.let {it.contact to zone}
        }
        val first=listOfNotNull(hit(HitZone.HEAD,pose.head,pose.head,.16),hit(HitZone.BODY,pose.bodyBottom,pose.bodyTop,.24))
            .minByOrNull {it.first.fraction} ?: return null
        return MotionContact(first.second,first.first.enemyPoint,first.first.normal,first.first.relativeDisplacement.normalizedOrNull())
    }
    private fun bits(v:Double)=java.lang.Double.doubleToRawLongBits(v)
    private fun same(label:String,expected:MotionContact?,actual:MotionContact?) {
        if(expected==null || actual==null) {assertEquals(label,expected,actual);return}
        assertEquals(label+" zone",expected.zone,actual.zone)
        fun vector(name:String,a:Vector3,b:Vector3) {
            assertEquals(label+" "+name+".x",bits(a.x),bits(b.x));assertEquals(label+" "+name+".y",bits(a.y),bits(b.y));assertEquals(label+" "+name+".z",bits(a.z),bits(b.z))
        }
        vector("point",expected.point,actual.point);vector("normal",expected.normal,actual.normal)
        val expectedTangent=expected.tangent;val actualTangent=actual.tangent
        if(expectedTangent==null || actualTangent==null)assertEquals(label+" tangent",expectedTangent,actualTangent)
        else vector("tangent",expectedTangent,actualTangent)
    }
    private fun checked(label:String,resolver:PlayerCombatResolver,s:Sample,pose:EnemyContactPose):MotionContact? {
        val expected=reference(s.reconstructed,pose);val result=actual(resolver,s,pose)
        same(label,expected,result);same(label+" repeat",expected,actual(resolver,s,pose));return result
    }
    private fun randomRotation(random:Random):Quaternion {
        val axis=checkNotNull(Vector3(random.nextDouble()-.5,random.nextDouble()-.5,random.nextDouble()-.5).normalizedOrNull())
        val half=(random.nextDouble()*2-1)*PI
        return checkNotNull(Quaternion(axis.x*sin(half),axis.y*sin(half),axis.z*sin(half),cos(half)).normalizedOrNull())
    }

    @Test fun staticWitnessMatchesExistingCcdAtUlpNeighboursOfTangencyForBothZones() {
        val random=Random(0x535441544943L);var belowUnitSelfDots=0;var hits=0;var misses=0
        val offsets=listOf(-512,-128,-65,-64,-63,-2,-1,0,1,2,63,64,65,128,512)
        repeat(32) {i->
            val q=if(i==0)identity else randomRotation(random)
            val s=sample(WeaponGrip(Vector3(.13,1.1,-.17),q));val normalized=checkNotNull(q.normalizedOrNull())
            if(normalized.x*normalized.x+normalized.y*normalized.y+normalized.z*normalized.z+normalized.w*normalized.w<1.0)belowUnitSelfDots++
            val parts=DaoBladeShape.shape.at(s.reconstructed)
            for(axis in listOf(Vector3(1.0,0.0,0.0),Vector3(0.0,1.0,0.0),Vector3(0.0,0.0,1.0))) {
                val support=parts.flatMap {p->listOf(p.base to p.radiusMeters,p.tip to p.radiusMeters)}.maxBy {it.first.dot(axis)+it.second}
                for(zone in HitZone.entries)for(offset in offsets) {
                    val radius=if(zone==HitZone.HEAD).16 else .24
                    val distance=support.second+radius+offset*Math.ulp(1.0)
                    val point=support.first+axis*distance
                    val pose=if(zone==HitZone.HEAD)EnemyContactPose(point,far,far) else EnemyContactPose(far,point,point)
                    val result=checked("tangent $i $axis $zone $offset",PlayerCombatResolver(),s,pose)
                    if(result==null)misses++ else hits++
                }
            }
        }
        assertTrue("exercise a self quaternion dot below one",belowUnitSelfDots>0)
        assertTrue("exercise accepted tangent neighbours",hits>0);assertTrue("exercise separated tangent neighbours",misses>0)
    }

    @Test fun staticWitnessMatchesCompleteCcdForRandomCapsulesAndRotations() {
        val random=Random(0x43415053554c45L);val resolver=PlayerCombatResolver()
        fun point()=Vector3((random.nextDouble()-.5)*1.5,.5+random.nextDouble()*1.4,(random.nextDouble()-.5)*1.5)
        repeat(256) {i->
            val s=sample(WeaponGrip(point(),randomRotation(random)))
            val pose=EnemyContactPose(point(),point(),point())
            checked("random $i",resolver,s,pose)
        }
    }

    @Test fun staticHeadWinsCoincidentHeadAndBodyAndMemoTracksTheEntirePose() {
        val resolver=PlayerCombatResolver();val s=sample(WeaponGrip(Vector3(0.0,1.0,0.0),identity))
        val p=DaoBladeShape.shape.at(s.reconstructed)[8].base
        assertEquals(HitZone.HEAD,checked("both",resolver,s,EnemyContactPose(p,p,p))?.zone)
        assertEquals(HitZone.BODY,checked("body only",resolver,s,EnemyContactPose(far,p,p))?.zone)
        assertNull(checked("neither",resolver,s,EnemyContactPose(far,far,far)))
        assertEquals(HitZone.HEAD,checked("head only",resolver,s,EnemyContactPose(p,far,far))?.zone)
        resolver.reset()
        assertNull(checked("reset no contact",resolver,s,EnemyContactPose(far,far,far)))
    }

    @Test fun observeRetainsHeadPriorityAndRearmsAfterACompleteOutsideInterval() {
        val resolver=PlayerCombatResolver();val enemy=Vector3(0.0,0.0,-.5)
        val center=Vector3(.022,.95,-.5);val pose=EnemyContactPose(center,center,center)
        assertNull(resolver.observe(snapshot(1,0,0.0),enemy,pose)?.strike)
        val first=checkNotNull(resolver.observe(snapshot(3,100_000_000,-.15),enemy,pose)?.strike)
        assertEquals(HitZone.HEAD,first.zone)
        resolver.observe(snapshot(5,200_000_000,-.6),enemy,pose)
        resolver.observe(snapshot(7,300_000_000,-.6),enemy,pose)
        assertNull(resolver.observe(snapshot(9,400_000_000,-.6),enemy,pose)?.strike)
        val next=checkNotNull(resolver.observe(snapshot(11,500_000_000,0.0),enemy,pose)?.strike)
        assertTrue(next.id>first.id)
    }

    @Test fun invalidRequiredGeometryAndMissingTrackingStillInvalidateMotionHistory() {
        val enemy=Vector3(0.0,0.0,-1.2)
        val good=snapshot(3,100_000_000,0.0)
        val invalid=listOf(good.copy(left=null),good.copy(head=null),
            good.copy(left=good.left?.copy(pose=ObservedPose(Vector3(Double.NaN,1.0,0.0),identity))),
            good.copy(left=good.left?.copy(pose=ObservedPose(Vector3(0.0,1.0,0.0),Quaternion(0.0,0.0,0.0,0.0)))),
            good.copy(left=good.left?.copy(pose=ObservedPose(Vector3(0.0,1.0,0.0),identity,TrackingQuality.SOURCE_REPORTED_INVALID))))
        for((i,input)in invalid.withIndex()) {
            val resolver=PlayerCombatResolver();val first=checkNotNull(resolver.observe(snapshot(1,0,0.0),enemy))
            assertNull("invalid tracking $i",resolver.observe(input,enemy));assertTrue(resolver.motionGeneration>first.motionGeneration)
        }
        val resolver=PlayerCombatResolver();val first=checkNotNull(resolver.observe(snapshot(1,0,0.0),enemy))
        val invalidPose=EnemyContactPose.standing(enemy).copy(head=Vector3(Double.POSITIVE_INFINITY,1.62,0.0))
        assertNull(resolver.observe(good,enemy,invalidPose));assertTrue(resolver.motionGeneration>first.motionGeneration)
    }

    private fun snapshot(sequence:Long,time:Long,x:Double):TrackingSnapshot {
        val stamp=ObservationStamp(sequence,time,1,InputOrigin.SYNTHETIC)
        return TrackingSnapshot(PoseObservation(stamp.copy(sequence=sequence-1),ObservedPose(Vector3(0.0,1.6,0.0),identity)),
            PoseObservation(stamp,ObservedPose(Vector3(x,.95,0.0),identity)),
            PoseObservation(stamp,ObservedPose(Vector3(.7,1.2,0.0),identity)),Hand.LEFT,0,0,0)
    }
}
