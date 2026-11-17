package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.p0d2f0182.runtime.*
import com.example.wuxiaarena.core.math.*
import org.junit.Assert.*
import org.junit.Test
import java.lang.reflect.InvocationTargetException

class BladeShapeArenaTest {
    private val identity=Quaternion(0.0,0.0,0.0,1.0)
    private fun grip(x:Double,y:Double=1.2)=WeaponGrip(Vector3(x,y,0.0),identity)
    private fun frame(x:Double,swing:Boolean=false):PlayerMotionFrame {
        val g=grip(x);val axis=playerBlade(g)
        return PlayerMotionFrame(1L,axis.base,axis.tip,2.0,null,false,Vector3(0.0,1.6,3.0),
            weaponGrip=g,rawWeaponGrip=g,swing=if(swing)QualifiedSwing(1L,1.0) else null)
    }
    private fun pose(steelX:Double,bodyX:Double,error:Double=0.0):AttackPoseSample {
        val g=grip(steelX);val axis=playerBlade(g)
        return AttackPoseSample(0.0,EnemyContactPose(Vector3(bodyX,2.4,-.4),Vector3(bodyX,.5,-.4),Vector3(bodyX,1.4,-.4)),axis.base,axis.tip,g,error)
    }
    private fun session()=ArenaSession(logMessage={},logFailure={_,e->throw e})
    private fun query(s:ArenaSession,a:PlayerMotionFrame,b:PlayerMotionFrame,p:AttackPoseSample,q:AttackPoseSample):Any? =
        ArenaSession::class.java.getDeclaredMethod("queryContact",PlayerMotionFrame::class.java,PlayerMotionFrame::class.java,
            AttackPoseSample::class.java,AttackPoseSample::class.java,java.lang.Long.TYPE).apply{isAccessible=true}.invoke(s,a,b,p,q,10_000_000L)
    private fun field(o:Any,n:String)=o.javaClass.getDeclaredField(n).apply{isAccessible=true}.get(o)
    @Test fun sessionOrdersFullChainSteelBeforeLaterBody() {
        val p=pose(0.0,.6);val hit=checkNotNull(query(session(),frame(-1.0),frame(1.0,true),p,p))
        assertEquals(true,field(hit,"steel"));assertTrue(field(hit,"playerPartIndex") as Int in 0..17)
        assertTrue(field(hit,"enemyPartIndex") as Int in 0..17)
    }
    @Test fun sessionOrdersEarlierBodyBeforeLaterChainSteel() {
        val p=pose(0.0,-.6);val hit=checkNotNull(query(session(),frame(-1.0),frame(1.0,true),p,p))
        assertEquals(false,field(hit,"steel"));assertEquals(true,field(hit,"playerAttack"))
    }
    @Test fun noSwingAdmissionMeansNoOutgoingDamageFromShapeContact() {
        val p=pose(3.0,-.6);assertNull(query(session(),frame(-1.0),frame(1.0),p,p))
    }
    @Test fun sessionPropagatesBadPoseEnvelopeBeforeApplyingDamage() {
        val p=pose(0.0,-.6,.00201)
        try {query(session(),frame(-1.0),frame(1.0,true),p,p);fail("must hold")}
        catch(e:InvocationTargetException){assertTrue(e.cause is BladeContactUncertainException)}
    }
    @Test fun storedGripInterpolationAndStageCompositionPreserveRoll() {
        val q=Quaternion(0.0,0.0,kotlin.math.sin(.7),kotlin.math.cos(.7))
        val a=pose(0.0,2.0).copy(bladeGrip=grip(0.0).copy(rotation=q))
        val b=a.copy(sourceSeconds=1.0,bladeGrip=grip(1.0).copy(rotation=q))
        val mid=samplePose(listOf(a,b),.5)
        assertEquals(interpolateGrip(a.bladeGrip,b.bladeGrip,.5),mid.bladeGrip)
        val stage=mid.inStage(Vector3(0.0,0.0,-1.0),.8f)
        val yaw=Quaternion(0.0,kotlin.math.sin(.8f.toDouble()/2),0.0,kotlin.math.cos(.8f.toDouble()/2))
        val localPoint=DaoBladeShape.shape.parts[2].tip
        val expected=Vector3(0.0,0.0,-1.0)+checkNotNull(yaw.rotate(mid.bladeGrip.position+checkNotNull(q.rotate(localPoint))))
        assertTrue(DaoBladeShape.shape.at(stage.bladeGrip)[2].tip.distanceTo(expected)<1e-10)
    }
    @Test fun incomingDamageUsesWholeMovingChainAndRetainsActivePhaseGate() {
        val s=session()
        val from=frame(5.0).copy(headPosition=Vector3(0.0,1.6,-.5))
        val a=pose(-2.0,10.0).let { p ->
            val g=grip(-2.0,1.6);val axis=playerBlade(g)
            p.copy(bladeGrip=g,bladeGripSource=g,bladeBase=axis.base,bladeTip=axis.tip)
        }
        val b=pose(2.0,10.0).let { p ->
            val g=grip(2.0,1.6);val axis=playerBlade(g)
            p.copy(bladeGrip=g,bladeGripSource=g,bladeBase=axis.base,bladeTip=axis.tip)
        }
        assertNull("Inactive steel remains solid but cannot damage a distant weapon's owner",query(s,from,from,a,b))
        val combat=EnemyCombatStateMachine().also {
            it.advanceBy(800_000_000L,true);it.tryStartAttack(AttackDirection.OVERHEAD,true)
            it.advanceBy(AttackDirection.OVERHEAD.preparationNanos+AttackDirection.OVERHEAD.startupNanos,true)
        }
        ArenaSession::class.java.getDeclaredField("combat").apply {isAccessible=true}.set(s,combat)
        val hit=checkNotNull(query(s,from,from,a,b))
        assertEquals(false,field(hit,"steel"));assertEquals(false,field(hit,"playerAttack"))
        assertEquals(HitZone.HEAD,field(hit,"zone"));assertTrue(field(hit,"enemyPartIndex") as Int in 0..17)
    }

}
