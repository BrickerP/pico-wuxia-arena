package com.example.wuxiaarena.core.combat
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.*
import org.junit.Test
import java.io.File
import kotlin.math.sqrt
class QuickPlanTest {
 @Test fun actualPlanExists() {
  val root=File(System.getenv("PICO_ACTOR_ROOT"));val csv=File(root,"ArtSource/refinement/combat-direction/native-steel-release/enemy-arm-prototype/fixture/recovery.csv").readLines();val keys=csv.first().split(',')
  val rows=csv.drop(1).map{keys.zip(it.split(',')).toMap()};fun Map<String,String>.d(s:String)=getValue(s).toDouble()
  fun local(r:Map<String,String>,p:String)=Vector3(r.d(p+"x")-r.d("actor_dx"),r.d(p+"y"),r.d(p+"z")+1.3-r.d("actor_dz"))
  val all=rows.sortedBy{it.d("source_s")}.distinctBy{it.d("source_s")}.map{BladeSegment(local(it,"b"),local(it,"t"),.0125)}
  val held=rows.first().let{BladeSegment(local(it,"b"),local(it,"t"),.0125)}
  val q=com.example.wuxiaarena.core.math.Quaternion(0.0,-sqrt(.5),0.0,sqrt(.5));val g=Vector3(-.7639676407546181,2.0267245198048953,-1.111081183234188)
  val player=BladeSegment(g+q.rotate(Vector3(.022,0.0,-.129))!!,g+q.rotate(Vector3(.0532,0.0,-.849))!!,.012)
  val plan=ActorWithdrawalPlan.create(Vector3(0.0,0.0,-1.3),0.0,held,player,Vector3(-.0414133948866612,-.29143511918023224,.9556937281537247),all)
  assertNotNull("Actual full recovery needs a bounded finite route",plan)
  println("ACTOR_PLAN duration=${plan!!.durationSeconds} yaw=${Math.toDegrees(plan.yawDeltaRadians)} retreat=${plan.retreatMeters} side=${plan.exitSide} end=${plan.at(plan.durationSeconds)}")
 }
}
