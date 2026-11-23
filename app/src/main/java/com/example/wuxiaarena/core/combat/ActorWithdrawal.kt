package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.*

data class ActorWithdrawalPose(val position: Vector3, val yawRadians: Double)

/** One finite, C1 actor escape. It never changes a player grip or a skeletal joint. */
class ActorWithdrawalPlan private constructor(
    private val origin: Vector3, private val yaw: Double, private val away: Vector3,
    val yawDeltaRadians: Double, private val sinRetreat: Double, private val cosRetreat: Double,
    val exitSide: String,
) {
    private val firstDuration=motionDuration(INITIAL_RETREAT,LINEAR_SPEED)
    private val turnSpeed=minOf(YAW_SPEED,if(hypot(sinRetreat,cosRetreat)==0.0)YAW_SPEED else LINEAR_SPEED/hypot(sinRetreat,cosRetreat))
    private val turnDuration=motionDuration(abs(yawDeltaRadians),turnSpeed)
    val durationSeconds: Double get()=firstDuration+turnDuration
    val retreatMeters: Double get()=distance(abs(yawDeltaRadians))
    fun at(elapsedSeconds: Double): ActorWithdrawalPose {
        require(elapsedSeconds.isFinite() && elapsedSeconds>=0)
        if(elapsedSeconds<firstDuration) return ActorWithdrawalPose(origin+away*(travel(elapsedSeconds,INITIAL_RETREAT,LINEAR_SPEED)),yaw)
        val magnitude=travel((elapsedSeconds-firstDuration).coerceAtLeast(0.0),abs(yawDeltaRadians),turnSpeed)
        val angle=if(yawDeltaRadians<0)-magnitude else magnitude
        return ActorWithdrawalPose(origin+away*distance(abs(angle)),yaw+angle)
    }
    private fun distance(angle: Double)=INITIAL_RETREAT+sinRetreat*sin(angle)+cosRetreat*(1-cos(angle))
    companion object {
        const val INITIAL_RETREAT=.0495
        const val LINEAR_SPEED=.65
        const val YAW_SPEED=1.0
        private const val CLEARANCE=.025
        private const val MAX_YAW=PI/2
        private const val MAX_RETREAT=.35
        private data class Range(val lo:Double,val hi:Double)
        private val fullYaw = listOf(Range(0.0, MAX_YAW))
        fun create(origin:Vector3,yawRadians:Double,heldLocalBlade:BladeSegment,playerBlade:List<BladeSegment>,
            normal:Vector3,recoveryLocalBlades:List<BladeSegment>):ActorWithdrawalPlan? {
            if(!origin.isFinite() || !yawRadians.isFinite() || !normal.isFinite() || normal.length()<1e-9 || recoveryLocalBlades.isEmpty() || playerBlade.isEmpty())return null
            val n=normal.normalizedOrNull() ?: return null
            val playerAxis=playerBlade.map { it.tip-it.base }.reduce { a,b->a+b }.normalizedOrNull() ?: return null
            if((heldLocalBlade.tip-heldLocalBlade.base).length()<1e-9)return null
            val held=listOf(rotate(heldLocalBlade.base,yawRadians),rotate(heldLocalBlade.tip,yawRadians))
            // Support planes enclose the complete capsule union, not a replacement
            // centre capsule. Each part contributes its actual radius.
            val initialLimit=playerBlade.minOf { minOf(it.base.dot(n),it.tip.dot(n))-it.radiusMeters }-heldLocalBlade.radiusMeters
            if(initialLimit-maxOf((origin+held[0]).dot(n),(origin+held[1]).dot(n))< -1e-6)return null
            val horizontal=Vector3(n.x,0.0,n.z)
            val away=horizontal.normalizedOrNull()?.times(-1.0) ?: rotate(Vector3(0.0,0.0,-1.0),yawRadians)
            val normalRetreat=-n.dot(away)
            val hulls=mutableListOf<List<Vector3>>()
            val yLow=playerBlade.minOf { minOf(it.base.y,it.tip.y)-it.radiusMeters }-heldLocalBlade.radiusMeters-CLEARANCE-origin.y
            val yHigh=playerBlade.maxOf { maxOf(it.base.y,it.tip.y)+it.radiusMeters }+heldLocalBlade.radiusMeters+CLEARANCE-origin.y
            val ordered=recoveryLocalBlades
            for(i in ordered.indices) {
                val a=ordered[i];val b=ordered[minOf(i+1,ordered.lastIndex)]
                val clipped=clipSlab(listOf(a.base,a.tip,b.base,b.tip),yLow,yHigh).map { rotate(it,yawRadians) }
                if(clipped.isNotEmpty())hulls+=clipped
            }
            val choices=mutableListOf<ActorWithdrawalPlan>()
            for(sign in listOf(-1.0,1.0)) {
                val a=held.maxOf { sign*(n.x*it.z-n.z*it.x) }.coerceAtLeast(0.0)
                val b=held.maxOf { -(n.x*it.x+n.z*it.z) }.coerceAtLeast(0.0)
                if(normalRetreat<1e-9 && (a>1e-9 || b>1e-9))continue
                val k=if(normalRetreat<1e-9)0.0 else a/normalRetreat
                val h=if(normalRetreat<1e-9)0.0 else b/normalRetreat
                // Choose a finite endpoint side from the actual rotating blade motion.
                for(exitSign in listOf(-1.0,1.0)) {
                    val t=playerAxis*exitSign
                    val exitLimit=playerBlade.maxOf { maxOf(it.base.dot(t),it.tip.dot(t))+it.radiusMeters }+
                        heldLocalBlade.radiusMeters+CLEARANCE
                    val tu=t.dot(away)
                    var allowed=fullYaw
                    for(hull in hulls) {
                        var behind=fullYaw;var beyond=fullYaw
                        for(p in hull) {
                            if (behind.isEmpty() && beyond.isEmpty()) break
                            if (behind.isNotEmpty()) {
                                val c=n.x*p.x+n.z*p.z
                                val s=sign*(n.x*p.z-n.z*p.x)
                                val constant=n.dot(origin)-normalRetreat*(INITIAL_RETREAT+h)+n.y*p.y
                                behind=intersect(behind,trig(-(c+normalRetreat*h),-(s-normalRetreat*k),constant-(initialLimit-CLEARANCE)))
                            }
                            if (beyond.isNotEmpty()) {
                                val tc=t.x*p.x+t.z*p.z-tu*h
                                val ts=sign*(t.x*p.z-t.z*p.x)+tu*k
                                val constantExit=t.dot(origin)+tu*(INITIAL_RETREAT+h)+t.y*p.y
                                beyond=intersect(beyond,trig(tc,ts,exitLimit-constantExit))
                            }
                        }
                        val hullYaw = when {
                            behind === fullYaw || beyond === fullYaw -> fullYaw
                            behind.isEmpty() -> beyond
                            beyond.isEmpty() -> behind
                            else -> merge(behind + beyond)
                        }
                        allowed=intersect(allowed,hullYaw)
                        if(allowed.isEmpty())break
                    }
                    val angle=allowed.firstOrNull()?.lo ?: continue
                    // A tiny analytic interior offset avoids selecting a floating root;
                    // clearance is already a physical25mm, not a tuned angle search.
                    val interior=minOf(angle+1e-7,allowed.first().hi)
                    val candidate=ActorWithdrawalPlan(origin,yawRadians,away,sign*interior,k,h,if(exitSign>0)"PLAYER_TIP" else "PLAYER_BASE")
                    if(candidate.retreatMeters<=MAX_RETREAT+1e-9)choices+=candidate
                }
            }
            return choices.minWithOrNull(compareBy<ActorWithdrawalPlan> { it.retreatMeters }.thenBy { abs(it.yawDeltaRadians) })
        }
        // Existing contact-stop duration supplies short, continuous speed ramps;
        // the middle phase uses the original actor's translation/turn rates.
        private const val SPEED_RAMP_SECONDS=.035
        private fun motionDuration(distance:Double,speed:Double):Double {
            if(distance==0.0)return 0.0
            return if(distance<speed*SPEED_RAMP_SECONDS)2*sqrt(distance*SPEED_RAMP_SECONDS/speed)
                else distance/speed+SPEED_RAMP_SECONDS
        }
        private fun travel(time:Double,distance:Double,speed:Double):Double {
            if(distance==0.0)return 0.0
            val duration=motionDuration(distance,speed)
            if(time>=duration)return distance
            val ramp=minOf(SPEED_RAMP_SECONDS,duration*.5)
            val peak=distance/(duration-ramp)
            return when {
                time<ramp -> .5*peak*time*time/ramp
                time>duration-ramp -> distance-.5*peak*(duration-time)*(duration-time)/ramp
                else -> peak*(time-.5*ramp)
            }
        }
        fun rotate(v:Vector3,yaw:Double)=Vector3(v.x*cos(yaw)+v.z*sin(yaw),v.y,-v.x*sin(yaw)+v.z*cos(yaw))
        private fun clipSlab(points:List<Vector3>,low:Double,high:Double):List<Vector3> {
            val out=points.filter { it.y>=low && it.y<=high }.toMutableList()
            for(i in points.indices)for(j in i+1 until points.size)for(y in listOf(low,high)) {
                val a=points[i];val b=points[j];val d=b.y-a.y
                if(abs(d)<1e-12)continue
                val t=(y-a.y)/d
                if(t in 0.0..1.0)out+=a+(b-a)*t
            }
            return out
        }
        private fun trig(a:Double,b:Double,c:Double):List<Range> {
            val r=hypot(a,b)
            if(r<1e-12)return if(c<=1e-10)fullYaw else emptyList()
            if(c>r+1e-10)return emptyList()
            if(c< -r)return fullYaw
            val phase=atan2(b,a);val offset=acos((c/r).coerceIn(-1.0,1.0))
            val cuts=mutableListOf(0.0,MAX_YAW)
            for(k in -1..1) {
                val low = phase-offset+2*PI*k
                val high = phase+offset+2*PI*k
                if(low>0 && low<MAX_YAW)cuts+=low
                if(high>0 && high<MAX_YAW)cuts+=high
            }
            if(cuts.size==2) {
                val mid=MAX_YAW*.5
                return if(a*cos(mid)+b*sin(mid)>=c-1e-10) fullYaw else emptyList()
            }
            cuts.sort();val out=mutableListOf<Range>()
            for(i in 0 until cuts.lastIndex){val lo=cuts[i];val hi=cuts[i+1];val mid=(lo+hi)*.5;if(a*cos(mid)+b*sin(mid)>=c-1e-10)out+=Range(lo,hi)}
            return merge(out)
        }
        private fun intersect(a:List<Range>,b:List<Range>):List<Range> {
            if(a.isEmpty() || b.isEmpty())return emptyList()
            if(a === fullYaw)return b
            if(b === fullYaw)return a
            if(a.size==1 && b.size==1) {
                val x=a[0];val y=b[0]
                val lo=maxOf(x.lo,y.lo);val hi=minOf(x.hi,y.hi)
                return when {
                    hi<lo-1e-12 -> emptyList()
                    lo==x.lo && hi==x.hi -> a
                    lo==y.lo && hi==y.hi -> b
                    else -> listOf(Range(lo,hi.coerceAtLeast(lo)))
                }
            }
            val out=mutableListOf<Range>();for(x in a)for(y in b){val lo=maxOf(x.lo,y.lo);val hi=minOf(x.hi,y.hi);if(hi>=lo-1e-12)out+=Range(lo,hi.coerceAtLeast(lo))};return merge(out)
        }
        private fun merge(input:List<Range>):List<Range> {
            if(input.size<2)return input
            val out=mutableListOf<Range>();for(r in input.sortedBy { it.lo }){val p=out.lastOrNull();if(p!=null && r.lo<=p.hi+1e-12)out[out.lastIndex]=Range(p.lo,maxOf(p.hi,r.hi))else out+=r};return out
        }
    }
}
