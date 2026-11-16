package com.example.wuxiaarena.prototype.withdrawal

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.math.*
import java.io.File
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.*

/** Independent capsule/CCD replay. It neither changes the player's blade nor fixes source FK. */
class ActorWithdrawalFixtureTest {
    private val origin=Vector3(0.0,0.0,-1.3)
    private val normal=Vector3(-.0414133948866612,-.29143511918023224,.9556937281537247)
    private val grip=Vector3(-.7639676407546181,2.0267245198048953,-1.111081183234188)
    private val rotation=Quaternion(0.0,-sqrt(.5),0.0,sqrt(.5))
    private val player=BladeSegment(grip+rotation.rotate(Vector3(.022,0.0,-.129))!!,
        grip+rotation.rotate(Vector3(.0532,0.0,-.849))!!,.012)

    @Test fun realHeldBladeWithdrawalAndEveryRecoverySweepAreClear() {
        val lines=File(checkNotNull(System.getenv("PICO_ACTOR_FIXTURE"))).readLines().filter { it.isNotBlank() }
        val header=lines.first().split(',')
        val rows=lines.drop(1).map { line -> Row(header.zip(line.split(',')).toMap()) }
        assertEquals(90,rows.size)
        val held=rows.first { it.mode=="reverse" && it.elapsed==0.0 }.localBlade(origin)
        val ordered=rows.sortedBy { it.source }.distinctBy { it.source }.map { it.localBlade(origin) }
        val plan=ActorWithdrawalPlan.create(origin,0.0,held,player,normal,ordered)
        val report=linkedMapOf<String,Any?>("status" to "FAILED_NO_CERTIFIED_PLAN","sdk_verified" to false,
            "fixture_rows" to rows.size,"planner_source_poses" to ordered.size,
            "player_base_m" to vec(player.base),"player_tip_m" to vec(player.tip),
            "player_raw_displacement_m" to 0.0,"player_held_displacement_m" to 0.0,
            "limitations" to listOf("Actual prepared FK fixture capsule axes; not a live controller recording.",
                "Actor curve sampled every 10ms; CCD proves straight endpoint sweeps, not intervening analytic rotation arcs.",
                "Source recovery uses the 90 supplied FK poses and adjacent endpoint-linear sweeps; not full skin/body collision."))
        if(plan==null) {
            write(report)
            fail("Planner returned null for actual 90-row recovery; inspect result, do not integrate")
            return
        }
        val failures=mutableListOf<String>()
        val samples=mutableListOf<Map<String,Any?>>()
        val times=(0..floor(plan.durationSeconds/.01).toInt()).map { it*.01 }.toMutableList()
        if(times.last()!=plan.durationSeconds)times+=plan.durationSeconds
        var previous:Pair<Double,ActorWithdrawalPose>?=null
        var previousBlade:BladeSegment?=null
        var minGap=Double.POSITIVE_INFINITY;var maxSpeed=0.0;var maxYawSpeed=0.0
        var certificates=0;var sweepChecks=0;var contactCount=0
        for(t in times) {
            val pose=plan.at(t);val blade=world(held,pose)
            val g=gap(player,blade);minGap=min(minGap,g)
            if(g < -1e-9)failures+="withdrawal penetration at $t: $g"
            var speed=0.0;var yawSpeed=0.0;var contact:BladeContact?=null;var separatedCertificate=false
            previous?.let { (beforeTime,before) ->
                val dt=t-beforeTime
                speed=pose.position.distanceTo(before.position)/dt
                yawSpeed=abs(pose.yawRadians-before.yawRadians)/dt
                maxSpeed=max(maxSpeed,speed);maxYawSpeed=max(maxYawSpeed,yawSpeed)
                val prior=checkNotNull(previousBlade)
                sweepChecks++
                try {contact=firstBladeContact(BladeSweep(player,player),BladeSweep(prior,blade))}
                catch(e:BladeContactUncertainException){failures+="withdrawal uncertain at $beforeTime..$t: ${e.message}"}
                if(contact!=null) {
                    // The complete endpoint hull is on the original enemy side at BOTH ends.
                    // This proves the entire linear sweep separates, including t0 tangent contact.
                    val a=supportGap(player,prior,normal);val b=supportGap(player,blade,normal)
                    separatedCertificate=contact!!.fraction==0.0 && a>=-1e-12 && b>=a-1e-12 && b>0.0
                    if(separatedCertificate)certificates++ else {contactCount++;failures+="withdrawal CCD at $beforeTime..$t f=${contact!!.fraction}"}
                }
            }
            samples+=linkedMapOf("elapsed_s" to t,"position_m" to vec(pose.position),"yaw_radians" to pose.yawRadians,
                "linear_speed_m_s" to speed,"yaw_speed_radians_s" to yawSpeed,"capsule_gap_m" to g,
                "support_gap_m" to supportGap(player,blade,normal),"ccd_contact_fraction" to contact?.fraction,
                "t0_pure_separation_support_certificate" to separatedCertificate)
            previous=t to pose;previousBlade=blade
        }
        val final=plan.at(plan.durationSeconds)
        val modeReports=mutableListOf<Map<String,Any?>>()
        for((mode,group) in rows.groupBy { it.mode }) {
            val frames=mutableListOf<Map<String,Any?>>()
            var before:BladeSegment?=null;var beforeTime=0.0
            var modeMin=Double.POSITIVE_INFINITY;var modeContacts=0
            for(row in group.sortedBy { it.elapsed }) {
                val blade=world(row.localBlade(origin),final);val g=gap(player,blade)
                modeMin=min(modeMin,g)
                if(g< -1e-9)failures+="$mode recovery penetration ${row.elapsed}: $g"
                var c:BladeContact?=null
                before?.let { prior ->
                    sweepChecks++
                    try {c=firstBladeContact(BladeSweep(player,player),BladeSweep(prior,blade))}
                    catch(e:BladeContactUncertainException){failures+="$mode recovery uncertain $beforeTime..${row.elapsed}: ${e.message}"}
                    if(c!=null){modeContacts++;contactCount++;failures+="$mode recovery CCD $beforeTime..${row.elapsed} f=${c!!.fraction}"}
                }
                frames+=linkedMapOf("elapsed_s" to row.elapsed,"source_s" to row.source,"capsule_gap_m" to g,
                    "base_m" to vec(blade.base),"tip_m" to vec(blade.tip),"ccd_contact_fraction" to c?.fraction)
                before=blade;beforeTime=row.elapsed
            }
            minGap=min(minGap,modeMin)
            modeReports+=linkedMapOf("mode" to mode,"rows" to group.size,"minimum_gap_m" to modeMin,
                "ccd_contacts" to modeContacts,"frames" to frames)
        }
        if(abs(plan.yawDeltaRadians)>PI/2+1e-12)failures+="yaw exceeds 90 degrees"
        if(plan.retreatMeters>.35+1e-12)failures+="retreat exceeds .35m"
        if(maxSpeed>.65+1e-9)failures+="linear speed $maxSpeed exceeds .65m/s"
        if(maxYawSpeed>1.0+1e-9)failures+="yaw speed $maxYawSpeed exceeds 1rad/s"
        if(plan.at(0.0).position!=origin || plan.at(0.0).yawRadians!=0.0)failures+="initial pose changed"
        if(plan.at(plan.durationSeconds+1.0)!=final)failures+="plan does not settle"
        report.putAll(linkedMapOf("status" to if(failures.isEmpty())"CAPSULE_FIXTURE_PASS_PENDING_SKIN_AND_RUNTIME" else "FAILED_GEOMETRY_OR_CONTRACT",
            "duration_s" to plan.durationSeconds,"yaw_delta_radians" to plan.yawDeltaRadians,
            "yaw_delta_degrees" to Math.toDegrees(plan.yawDeltaRadians),"retreat_m" to plan.retreatMeters,
            "exit_side" to plan.exitSide,"final_position_m" to vec(final.position),"minimum_capsule_gap_m" to minGap,
            "maximum_linear_speed_m_s" to maxSpeed,"maximum_yaw_speed_radians_s" to maxYawSpeed,
            "ccd_sweep_checks" to sweepChecks,"ccd_contacts" to contactCount,"initial_separation_certificates" to certificates,
            "failures" to failures,"withdrawal_frames" to samples,"recovery_modes" to modeReports))
        write(report)
        println("ACTOR_WITHDRAWAL duration=${plan.durationSeconds} retreat=${plan.retreatMeters} yawDeg=${Math.toDegrees(plan.yawDeltaRadians)} gap=$minGap sweeps=$sweepChecks contacts=$contactCount speed=$maxSpeed yawSpeed=$maxYawSpeed")
        assertTrue(failures.joinToString("\n"),failures.isEmpty())
    }

    @Test fun tangentSyntheticHeldBladeHasFiniteClearWithdrawal() {
        val p=BladeSegment(Vector3(-1.0,1.0,0.0),Vector3(1.0,1.0,0.0),.012)
        val h=BladeSegment(Vector3(-.5,1.0,-.0245),Vector3(.5,1.0,-.0245),.0125)
        val o=Vector3(0.0,0.0,0.0)
        val plan=checkNotNull(ActorWithdrawalPlan.create(o,0.0,h,p,Vector3(0.0,0.0,1.0),listOf(h)))
        assertEquals(o,plan.at(0.0).position)
        assertTrue(plan.durationSeconds.isFinite() && plan.durationSeconds>0.0)
        assertTrue(abs(plan.yawDeltaRadians)<=PI/2)
        assertTrue(gap(p,world(h,plan.at(plan.durationSeconds)))>0.0)
    }

    @Test fun badNormalPenetrationAndDegenerateGeometryCannotCreatePlan() {
        val p=BladeSegment(Vector3(-1.0,1.0,0.0),Vector3(1.0,1.0,0.0),.012)
        val h=BladeSegment(Vector3(-.5,1.0,-.0245),Vector3(.5,1.0,-.0245),.0125)
        val o=Vector3(0.0,0.0,0.0);val n=Vector3(0.0,0.0,1.0)
        assertNull(ActorWithdrawalPlan.create(o,0.0,h,p,Vector3(0.0,0.0,0.0),listOf(h)))
        assertNull(ActorWithdrawalPlan.create(o,0.0,h,p,Vector3(Double.NaN,0.0,1.0),listOf(h)))
        assertNull(ActorWithdrawalPlan.create(Vector3(0.0,0.0,.001),0.0,h,p,n,listOf(h)))
        assertNull(ActorWithdrawalPlan.create(o,0.0,BladeSegment(h.base,h.base,h.radiusMeters),p,n,listOf(h)))
        assertNull(ActorWithdrawalPlan.create(o,0.0,h,BladeSegment(p.base,p.base,p.radiusMeters),n,listOf(h)))
        assertNull(ActorWithdrawalPlan.create(o,0.0,h,p,n,emptyList()))
    }

    private fun write(report:Map<String,Any?>)=File(checkNotNull(System.getenv("PICO_ACTOR_RESULT"))).writeText(json(report)+"\n")
    private data class Row(val values:Map<String,String>) {
        val mode get()=values.getValue("mode")
        val elapsed get()=values.getValue("elapsed_s").toDouble()
        val source get()=values.getValue("source_s").toDouble()
        fun v(prefix:String)=Vector3(values.getValue(prefix+"x").toDouble(),values.getValue(prefix+"y").toDouble(),values.getValue(prefix+"z").toDouble())
        fun localBlade(origin:Vector3):BladeSegment {
            val offset=Vector3(values.getValue("actor_dx").toDouble(),values.getValue("actor_dy").toDouble(),values.getValue("actor_dz").toDouble())
            return BladeSegment(v("b")-offset-origin,v("t")-offset-origin,.0125)
        }
    }
}
private fun rotate(v:Vector3,yaw:Double)=Vector3(v.x*cos(yaw)+v.z*sin(yaw),v.y,-v.x*sin(yaw)+v.z*cos(yaw))
private fun world(blade:BladeSegment,pose:ActorWithdrawalPose)=BladeSegment(pose.position+rotate(blade.base,pose.yawRadians),pose.position+rotate(blade.tip,pose.yawRadians),blade.radiusMeters)
private fun gap(a:BladeSegment,b:BladeSegment):Double {val pair=checkNotNull(closestSegmentPoints(a.base,a.tip,b.base,b.tip));return pair.first.distanceTo(pair.second)-a.radiusMeters-b.radiusMeters}
private fun supportGap(p:BladeSegment,e:BladeSegment,n:Vector3)=minOf(p.base.dot(n),p.tip.dot(n))-maxOf(e.base.dot(n),e.tip.dot(n))-p.radiusMeters-e.radiusMeters
private fun vec(v:Vector3)=listOf(v.x,v.y,v.z)
private fun json(v:Any?):String=when(v){
    null->"null";is String->"\""+v.replace("\\","\\\\").replace("\"","\\\"").replace("\n","\\n")+"\""
    is Boolean->v.toString();is Number->if(v.toDouble().isFinite())v.toString() else "null"
    is Map<*,*>->v.entries.joinToString(",","{","}"){json(it.key.toString())+":"+json(it.value)}
    is Iterable<*>->v.joinToString(",","[","]"){json(it)}
    else->error("Unexpected report value")
}
