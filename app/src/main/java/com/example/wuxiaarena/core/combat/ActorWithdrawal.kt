package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import kotlin.math.*


data class ActorWithdrawalPose(val position: Vector3, val yawRadians: Double)

/** One finite, C1 actor escape. It never changes a player grip or a skeletal joint. */
class ActorWithdrawalPlan private constructor(
    private val origin: Vector3, private val yaw: Double, private val away: Vector3,
    val yawDeltaRadians: Double, private val sinRetreat: Double, private val cosRetreat: Double,
    val exitSide: String, private val initialRetreat:Double,
    private val heldSource:WeaponGrip, private val heldPlayer:WeaponGrip,
) {
    private val firstDuration=motionDuration(initialRetreat,LINEAR_SPEED)
    private val turnSpeed=minOf(YAW_SPEED,if(hypot(sinRetreat,cosRetreat)==0.0)YAW_SPEED else LINEAR_SPEED/hypot(sinRetreat,cosRetreat))
    private val turnDuration=motionDuration(abs(yawDeltaRadians),turnSpeed)
    val durationSeconds: Double get()=firstDuration+turnDuration
    /** Actual C1 actor path versus the interval's linear origin/yaw model. */
    fun chordErrorMeters(intervalSeconds:Double,actorRadiusMeters:Double):Double {
        require(intervalSeconds.isFinite() && intervalSeconds>=0 && actorRadiusMeters.isFinite() && actorRadiusMeters>=0)
        val lever=hypot(sinRetreat,cosRetreat)
        val acceleration=LINEAR_SPEED/SPEED_RAMP_SECONDS+lever*turnSpeed*turnSpeed+
            actorRadiusMeters*turnSpeed/SPEED_RAMP_SECONDS
        return acceleration*intervalSeconds*intervalSeconds/8.0
    }
    /** Reuses the analytic full-route certificate only for the exact actor/source/player it proved. */
    fun certifiesInterval(startSeconds:Double,endSeconds:Double,playerBefore:WeaponGrip,playerAfter:WeaponGrip,
        sourceBefore:WeaponGrip,sourceAfter:WeaponGrip,actorBefore:ActorWithdrawalPose,actorAfter:ActorWithdrawalPose):Boolean {
        if(playerBefore!=heldPlayer || playerAfter!=heldPlayer || sourceBefore!=heldSource || sourceAfter!=heldSource)return false
        if(!startSeconds.isFinite() || !endSeconds.isFinite() || startSeconds<0 || endSeconds<startSeconds || endSeconds>durationSeconds+1e-9)return false
        fun matches(a:ActorWithdrawalPose,b:ActorWithdrawalPose)=a.position.distanceTo(b.position)<=1e-8 && abs(a.yawRadians-b.yawRadians)<=2e-7
        return matches(actorBefore,at(startSeconds)) && matches(actorAfter,at(endSeconds))
    }
    val retreatMeters: Double get()=distance(abs(yawDeltaRadians))
    fun at(elapsedSeconds: Double): ActorWithdrawalPose {
        require(elapsedSeconds.isFinite() && elapsedSeconds>=0)
        if(elapsedSeconds<firstDuration) return ActorWithdrawalPose(origin+away*(travel(elapsedSeconds,initialRetreat,LINEAR_SPEED)),yaw)
        val magnitude=travel((elapsedSeconds-firstDuration).coerceAtLeast(0.0),abs(yawDeltaRadians),turnSpeed)
        val angle=if(yawDeltaRadians<0)-magnitude else magnitude
        return ActorWithdrawalPose(origin+away*distance(abs(angle)),yaw+angle)
    }
    private fun distance(angle: Double)=initialRetreat+sinRetreat*sin(angle)+cosRetreat*(1-cos(angle))
    companion object {
        const val INITIAL_RETREAT=.0495
        const val LINEAR_SPEED=.65
        const val YAW_SPEED=1.0
        private const val CLEARANCE=.025
        private const val MAX_YAW=PI/2
        private const val MAX_RETREAT=.35
        private data class Range(val lo:Double,val hi:Double)
        /** Full chain extension of the existing finite yaw + retreat analytic plan. */
        fun create(origin:Vector3,yawRadians:Double,heldGrip:WeaponGrip,playerGrip:WeaponGrip,
            normal:Vector3,heldErrorMeters:Double,recovery:List<Pair<WeaponGrip,Double>>,shape:BladeShape=DaoBladeShape.shape):ActorWithdrawalPlan? {
            if(!origin.isFinite() || !yawRadians.isFinite() || recovery.isEmpty())return null
            if(recovery.any { !it.second.isFinite() || it.second<0 || it.second>.002 })return null
            if(!heldErrorMeters.isFinite() || heldErrorMeters<0 || heldErrorMeters>.002)return null
            val contactNormal=normal.normalizedOrNull() ?: return null
            val player=shape.at(playerGrip)
            val yawCos=cos(yawRadians); val yawSin=sin(yawRadians)
            val held=shape.at(heldGrip).map { it.copy(base=rotate(it.base,yawCos,yawSin),tip=rotate(it.tip,yawCos,yawSin),radiusMeters=it.radiusMeters+heldErrorMeters) }
            val away=Vector3(-contactNormal.x,0.0,-contactNormal.z).normalizedOrNull()
                ?: rotate(Vector3(0.0,0.0,-1.0),yawCos,yawSin)
            val normalRetreat=-contactNormal.dot(away)
            val globalLimit=player.minOf { minOf(it.base.dot(contactNormal),it.tip.dot(contactNormal))-it.radiusMeters }
            val globalSupport=held.maxOf { maxOf((origin+it.base).dot(contactNormal),(origin+it.tip).dot(contactNormal))+it.radiusMeters }
            val initialRetreat=if(normalRetreat>1e-9)maxOf(INITIAL_RETREAT,(globalSupport-globalLimit+CLEARANCE)/normalRetreat)
                else INITIAL_RETREAT
            if(initialRetreat>MAX_RETREAT)return null
            val globalTurnSafe=globalLimit-globalSupport+normalRetreat*initialRetreat>=-1e-7
            data class Plane(val n:Vector3,val limit:Double,val held:BladeSegment)
            var initialFixedPlanesProve=true
            val planes=player.map { p -> held.map { e ->
                val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,origin+e.base,origin+e.tip))
                val n=(pair.first-pair.second).normalizedOrNull() ?: return null
                val limit=minOf(p.base.dot(n),p.tip.dot(n))-p.radiusMeters-e.radiusMeters
                val start=limit-maxOf((origin+e.base).dot(n),(origin+e.tip).dot(n))
                val end=start-n.dot(away)*initialRetreat
                if(start< -1e-6)return null
                if(end< -1e-6)initialFixedPlanesProve=false
                Plane(n,limit,e)
            } }
            if(!initialFixedPlanesProve) {
                // An initial closest plane is sufficient, not necessary, for a long
                // tangential retreat. Certify the actual complete route before rejecting it.
                val yawRotation=com.example.wuxiaarena.core.math.Quaternion(0.0,sin(yawRadians*.5),0.0,cos(yawRadians*.5))
                val startGrip=WeaponGrip(origin+checkNotNull(yawRotation.rotate(heldGrip.position)),yawRotation*heldGrip.rotation)
                val endGrip=startGrip.copy(position=startGrip.position+away*initialRetreat)
                if(!separatingBladeShapePairs(BladeShapeSweep(shape,playerGrip,playerGrip,0.0),
                    BladeShapeSweep(shape,startGrip,endGrip,heldErrorMeters),contactNormal))return null
            }
            data class Hull(val playerIndex:Int,val partIndex:Int,val points:List<Vector3>,val radius:Double)
            data class Future(val partIndex:Int,val points:List<Vector3>,val radius:Double)
            data class Box(val lowX:Double,val lowY:Double,val lowZ:Double,val highX:Double,val highY:Double,val highZ:Double) {
                fun overlaps(b:Box)=lowX<=b.highX && highX>=b.lowX && lowY<=b.highY && highY>=b.lowY && lowZ<=b.highZ && highZ>=b.lowZ
            }
            val playerBoxes=player.map { p ->
                val radius=p.radiusMeters+CLEARANCE
                Box(minOf(p.base.x,p.tip.x)-radius,minOf(p.base.y,p.tip.y)-radius,minOf(p.base.z,p.tip.z)-radius,
                    maxOf(p.base.x,p.tip.x)+radius,maxOf(p.base.y,p.tip.y)+radius,maxOf(p.base.z,p.tip.z)+radius)
            }
            val playerGroups=playerBoxes.chunked(3).map { group -> Box(group.minOf {it.lowX},group.minOf {it.lowY},group.minOf {it.lowZ},
                group.maxOf {it.highX},group.maxOf {it.highY},group.maxOf {it.highZ}) }
            // Player axes are immutable within this plan; preserve lazy validation for
            // degenerate input that broadphase can prove disjoint without using an axis.
            val playerAxes=arrayOfNulls<Vector3>(player.size)
            fun playerAxis(index:Int):Vector3 = playerAxes[index] ?: checkNotNull((player[index].tip-player[index].base).normalizedOrNull()).also {playerAxes[index]=it}
            val future=mutableListOf<Future>()
            var recoveryShape=shape.at(recovery.first().first)
            var recoveryRotation=checkNotNull(recovery.first().first.rotation.normalizedOrNull())
            for(i in recovery.indices) {
                val a=recovery[i];val b=recovery[minOf(i+1,recovery.lastIndex)]
                val qa=recoveryRotation;val qb=checkNotNull(b.first.rotation.normalizedOrNull())
                val angle=2*acos(abs(qa.x*qb.x+qa.y*qb.y+qa.z*qb.z+qa.w*qb.w).coerceIn(0.0,1.0))
                val envelope=shape.gripRadius*(1-cos(angle*.5))+a.second
                val aa=recoveryShape;val bb=if(i==recovery.lastIndex)aa else shape.at(b.first)
                for(ei in aa.indices)future+=Future(ei,listOf(aa[ei].base,aa[ei].tip,bb[ei].base,bb[ei].tip).map {rotate(it,yawCos,yawSin)},aa[ei].radiusMeters+envelope)
                recoveryShape=bb;recoveryRotation=qb
            }
            // At a candidate actor angle, broadphase whole future capsule hulls against
            // six player groups before forming any per-pair clipped support constraint.
            // A disjoint expanded AABB certifies the entire source interval, not a sample.
            fun violation(sign:Double,angle:Double,k:Double,h:Double):Hull? {
                val offset=away*(initialRetreat+k*sin(angle)+h*(1-cos(angle)))
                val rotationCos=cos(sign*angle);val rotationSin=sin(sign*angle)
                val offsetX=origin.x+offset.x;val offsetY=origin.y+offset.y;val offsetZ=origin.z+offset.z
                for(f in future) {
                    // A scalar transformed AABB rejects distant interval hulls before
                    // allocating any candidate-angle points. Keep the original add order.
                    var lowX=Double.POSITIVE_INFINITY;var lowY=lowX;var lowZ=lowX
                    var highX=Double.NEGATIVE_INFINITY;var highY=highX;var highZ=highX
                    for(p in f.points) {
                        val x=offsetX+(p.x*rotationCos+p.z*rotationSin)
                        val y=offsetY+p.y
                        val z=offsetZ+(-p.x*rotationSin+p.z*rotationCos)
                        lowX=minOf(lowX,x);lowY=minOf(lowY,y);lowZ=minOf(lowZ,z)
                        highX=maxOf(highX,x);highY=maxOf(highY,y);highZ=maxOf(highZ,z)
                    }
                    val bounds=Box(lowX-f.radius,lowY-f.radius,lowZ-f.radius,highX+f.radius,highY+f.radius,highZ+f.radius)
                    for(group in playerGroups.indices) {
                        if(!bounds.overlaps(playerGroups[group]))continue
                        for(pi in group*3 until group*3+3) {
                            if(!bounds.overlaps(playerBoxes[pi]))continue
                            val p=player[pi];val radius=p.radiusMeters+f.radius
                            val low=minOf(p.base.y,p.tip.y)-radius-CLEARANCE-origin.y
                            val high=maxOf(p.base.y,p.tip.y)+radius+CLEARANCE-origin.y
                            val clipped=clipSlab(f.points,low,high)
                            if(clipped.isEmpty())continue
                            val points=clipped.map {origin+offset+rotate(it,rotationCos,rotationSin)}
                            val n=planes[pi][f.partIndex].n
                            val behind=points.maxOf {it.dot(n)}<=minOf(p.base.dot(n),p.tip.dot(n))-radius-CLEARANCE+1e-10
                            val globalBehind=points.maxOf {it.dot(contactNormal)}<=minOf(p.base.dot(contactNormal),p.tip.dot(contactNormal))-radius-CLEARANCE+1e-10
                            val axis=playerAxis(pi)
                            val beyond=points.minOf {it.dot(axis)}>=p.tip.dot(axis)+radius+CLEARANCE-1e-10 ||
                                points.maxOf {it.dot(axis)}<=p.base.dot(axis)-radius-CLEARANCE+1e-10
                            if(!behind && !globalBehind && !beyond)return Hull(pi,f.partIndex,clipped,radius)
                        }
                    }
                }
                return null
            }
            if(violation(1.0,0.0,0.0,0.0)==null)return ActorWithdrawalPlan(origin,yawRadians,away,0.0,0.0,0.0,"FULL_CHAIN_STRAIGHT",initialRetreat,heldGrip,playerGrip)
            val choices=mutableListOf<ActorWithdrawalPlan>()
            val endpoints=held.flatMap { listOf(it.base,it.tip) }
            for(sign in listOf(-1.0,1.0)) {
                val a=endpoints.maxOf { sign*(contactNormal.x*it.z-contactNormal.z*it.x) }.coerceAtLeast(0.0)
                val b=endpoints.maxOf { -(contactNormal.x*it.x+contactNormal.z*it.z) }.coerceAtLeast(0.0)
                if(normalRetreat<1e-9 && (a>1e-9 || b>1e-9))continue
                val k=if(normalRetreat<1e-9)0.0 else a/normalRetreat
                val h=if(normalRetreat<1e-9)0.0 else b/normalRetreat
                // Certify the complete held route, each capsule pair on its own plane.
                // Only the first feasible range containing zero can certify every prefix.
                var route=listOf(Range(0.0,MAX_YAW))
                if(!globalTurnSafe)for(row in planes)for(plane in row) {
                    val n=plane.n;val retreat=-n.dot(away)
                    for(p in listOf(plane.held.base,plane.held.tip)) {
                        val c=n.x*p.x+n.z*p.z;val v=sign*(n.x*p.z-n.z*p.x)
                        val constant=n.dot(origin)-retreat*(initialRetreat+h)+n.y*p.y
                        route=intersect(route,trig(-(c+retreat*h),-(v-retreat*k),constant-plane.limit))
                    }
                }
                val prefix=route.firstOrNull()?.takeIf { it.lo<=1e-10 } ?: continue
                var allowed=listOf(Range(0.0,prefix.hi))
                var certified=false
                while(allowed.isNotEmpty()) {
                    val trial=minOf(allowed.first().lo+1e-7,allowed.first().hi)
                    val hull=violation(sign,trial,k,h)
                    if(hull==null) { certified=true;break }
                    val playerPart=player[hull.playerIndex]
                    val axis=playerAxis(hull.playerIndex)
                    val n=planes[hull.playerIndex][hull.partIndex].n
                    val limit=minOf(playerPart.base.dot(n),playerPart.tip.dot(n))-hull.radius-CLEARANCE
                    val retreat=-n.dot(away)
                    var behind=listOf(Range(0.0,MAX_YAW))
                    for(p in hull.points) {
                        val c=n.x*p.x+n.z*p.z;val v=sign*(n.x*p.z-n.z*p.x)
                        val constant=n.dot(origin)-retreat*(initialRetreat+h)+n.y*p.y
                        behind=intersect(behind,trig(-(c+retreat*h),-(v-retreat*k),constant-limit))
                    }
                    var globalBehind=listOf(Range(0.0,MAX_YAW))
                    val globalLimit=minOf(playerPart.base.dot(contactNormal),playerPart.tip.dot(contactNormal))-hull.radius-CLEARANCE
                    for(p in hull.points) {
                        val n=contactNormal;val retreat=normalRetreat
                        val c=n.x*p.x+n.z*p.z;val v=sign*(n.x*p.z-n.z*p.x)
                        val constant=n.dot(origin)-retreat*(initialRetreat+h)+n.y*p.y
                        globalBehind=intersect(globalBehind,trig(-(c+retreat*h),-(v-retreat*k),constant-globalLimit))
                    }
                    var possible=merge(behind+globalBehind)
                    for(exitSign in listOf(-1.0,1.0)) {
                        val t=axis*exitSign;val endpoint=if(exitSign>0)playerPart.tip else playerPart.base
                        var beyond=listOf(Range(0.0,MAX_YAW))
                        for(p in hull.points) {
                            val tu=t.dot(away);val tc=t.x*p.x+t.z*p.z-tu*h
                            val ts=sign*(t.x*p.z-t.z*p.x)+tu*k
                            val constant=t.dot(origin)+tu*(initialRetreat+h)+t.y*p.y
                            beyond=intersect(beyond,trig(tc,ts,t.dot(endpoint)+hull.radius+CLEARANCE-constant))
                        }
                        possible=merge(possible+beyond)
                    }
                    allowed=intersect(allowed,possible)
                    if(allowed.isEmpty())break
                    val next=minOf(allowed.first().lo+1e-7,allowed.first().hi)
                    // Every rejected earlier angle is excluded analytically. Recheck all
                    // previous hulls only when a violated constraint moves the candidate.
                    if(next<=trial+1e-12) { allowed=emptyList();break }
                }
                if(!certified)continue
                val angle=allowed.firstOrNull()?.lo ?: continue
                val interior=minOf(angle+1e-7,allowed.first().hi)
                val candidate=ActorWithdrawalPlan(origin,yawRadians,away,sign*interior,k,h,"FULL_CHAIN_PAIR_PLANES",initialRetreat,heldGrip,playerGrip)
                if(candidate.retreatMeters<=MAX_RETREAT+1e-9)choices+=candidate
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
        fun rotate(v:Vector3,yaw:Double)=rotate(v,cos(yaw),sin(yaw))
        private fun rotate(v:Vector3,c:Double,s:Double)=Vector3(v.x*c+v.z*s,v.y,-v.x*s+v.z*c)
        private fun clipSlab(points:List<Vector3>,low:Double,high:Double):List<Vector3> {
            val out=points.filter { it.y>=low && it.y<=high }.toMutableList()
            for(i in points.indices)for(j in i+1 until points.size) {
                val a=points[i];val b=points[j];val d=b.y-a.y
                if(abs(d)<1e-12)continue
                for(side in 0..1) {
                    val y=if(side==0)low else high
                    val t=(y-a.y)/d
                    if(t in 0.0..1.0)out+=a+(b-a)*t
                }
            }
            return out
        }
        private fun trig(a:Double,b:Double,c:Double):List<Range> {
            val r=hypot(a,b)
            if(r<1e-12)return if(c<=1e-10)listOf(Range(0.0,MAX_YAW)) else emptyList()
            if(c>r+1e-10)return emptyList()
            if(c< -r)return listOf(Range(0.0,MAX_YAW))
            val phase=atan2(b,a);val offset=acos((c/r).coerceIn(-1.0,1.0))
            val cuts=mutableListOf(0.0,MAX_YAW)
            for(k in -1..1)for(x in listOf(phase-offset+2*PI*k,phase+offset+2*PI*k))if(x>0 && x<MAX_YAW)cuts+=x
            cuts.sort();val out=mutableListOf<Range>()
            for(i in 0 until cuts.lastIndex){val lo=cuts[i];val hi=cuts[i+1];val mid=(lo+hi)*.5;if(a*cos(mid)+b*sin(mid)>=c-1e-10)out+=Range(lo,hi)}
            return merge(out)
        }
        private fun intersect(a:List<Range>,b:List<Range>):List<Range> {
            val out=mutableListOf<Range>();for(x in a)for(y in b){val lo=maxOf(x.lo,y.lo);val hi=minOf(x.hi,y.hi);if(hi>=lo-1e-12)out+=Range(lo,hi.coerceAtLeast(lo))};return merge(out)
        }
        private fun merge(input:List<Range>):List<Range> {
            val out=mutableListOf<Range>();for(r in input.sortedBy { it.lo }){val p=out.lastOrNull();if(p!=null && r.lo<=p.hi+1e-12)out[out.lastIndex]=Range(p.lo,maxOf(p.hi,r.hi))else out+=r};return out
        }
    }
}
