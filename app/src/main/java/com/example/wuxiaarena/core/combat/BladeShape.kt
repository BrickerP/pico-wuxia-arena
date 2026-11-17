package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.ceil
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.atan2
import kotlin.math.hypot
import kotlin.math.PI
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.closestSegmentPoints

/** Common Grip local capsules, fixed 6 groups of 3. Semantic blade axes remain separate. */
class BladeShape(parts: List<BladeSegment>) {
    val parts = parts.toList()
    init { require(this.parts.size == 18) }
    val gripRadius = this.parts.maxOf { maxOf(it.base.length(), it.tip.length()) }.also { require(it.isFinite()) }
    fun at(grip: WeaponGrip): List<BladeSegment> = parts.map { part -> at(part,grip) }
    internal fun partAt(index: Int, grip: WeaponGrip): BladeSegment = at(parts[index],grip)
    private fun at(part: BladeSegment, grip: WeaponGrip) =
        BladeSegment(grip.position + checkNotNull(grip.rotation.rotate(part.base)),
            grip.position + checkNotNull(grip.rotation.rotate(part.tip)), part.radiusMeters)
}

/** Required error receipt bounds true source FK versus this rigid SLERP path throughout interval. */
data class BladeShapeSweep(val shape: BladeShape, val previous: WeaponGrip, val current: WeaponGrip,
    val pathErrorMeters: Double) {
    init { require(pathErrorMeters.isFinite() && pathErrorMeters >= 0.0) }
}

data class BladeShapeContact(val contact: BladeContact, val playerPartIndex: Int, val enemyPartIndex: Int)
class BladeQueryStats {
    var wholeBounds = 0L
    var groupBounds = 0L
    var capsuleQueries = 0L
    var angularIntervals = 0L
}

private data class Bounds(val lowX: Double, val lowY: Double, val lowZ: Double,
    val highX: Double, val highY: Double, val highZ: Double) {
    fun intersects(other: Bounds): Boolean = lowX <= other.highX && highX >= other.lowX &&
        lowY <= other.highY && highY >= other.lowY && lowZ <= other.highZ && highZ >= other.lowZ
}
private fun bounds(sweep: BladeSweep): Bounds {
    val a=sweep.previous; val b=sweep.current
    // Add the same numerical broadphase pad before subtracting each endpoint radius.
    val ar=a.radiusMeters+1e-7; val br=b.radiusMeters+1e-7
    return Bounds(minOf(minOf(a.base.x,a.tip.x)-ar,minOf(b.base.x,b.tip.x)-br),
        minOf(minOf(a.base.y,a.tip.y)-ar,minOf(b.base.y,b.tip.y)-br),
        minOf(minOf(a.base.z,a.tip.z)-ar,minOf(b.base.z,b.tip.z)-br),
        maxOf(maxOf(a.base.x,a.tip.x)+ar,maxOf(b.base.x,b.tip.x)+br),
        maxOf(maxOf(a.base.y,a.tip.y)+ar,maxOf(b.base.y,b.tip.y)+br),
        maxOf(maxOf(a.base.z,a.tip.z)+ar,maxOf(b.base.z,b.tip.z)+br))
}
private fun bounds(parts: List<Bounds>, start: Int = 0, end: Int = parts.size): Bounds {
    var lowX=Double.POSITIVE_INFINITY; var lowY=lowX; var lowZ=lowX
    var highX=Double.NEGATIVE_INFINITY; var highY=highX; var highZ=highX
    for(i in start until end) {
        val b=parts[i]
        lowX=minOf(lowX,b.lowX); lowY=minOf(lowY,b.lowY); lowZ=minOf(lowZ,b.lowZ)
        highX=maxOf(highX,b.highX); highY=maxOf(highY,b.highY); highZ=maxOf(highZ,b.highZ)
    }
    return Bounds(lowX,lowY,lowZ,highX,highY,highZ)
}
private fun angle(sweep: BladeShapeSweep): Double {
    val a = checkNotNull(sweep.previous.rotation.normalizedOrNull())
    val b = checkNotNull(sweep.current.rotation.normalizedOrNull())
    return 2.0 * acos(abs(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w).coerceIn(0.0,1.0))
}
private fun steps(sweep: BladeShapeSweep, rotationAngle: Double): Int {
    val maximumAngle = 2.0 * acos((1.0-ARC_ERROR/sweep.shape.gripRadius).coerceIn(-1.0,1.0))
    return if(sweep.shape.gripRadius == 0.0) 1 else ceil(rotationAngle/maximumAngle).toInt().coerceAtLeast(1)
}
private fun BladeSweep.atTime(t: Double) = BladeSegment(previous.base*(1-t)+current.base*t,
    previous.tip*(1-t)+current.tip*t, previous.radiusMeters*(1-t)+current.radiusMeters*t)
private fun BladeShapeSweep.chords(a: List<BladeSegment>, b: List<BladeSegment>,
    rotationAngle: Double, start: Double, end: Double): List<BladeSweep> {
    val inflation=shape.gripRadius*(1.0-cos(rotationAngle*(end-start)*0.5))+pathErrorMeters
    return a.zip(b) { x,y -> BladeSweep(x.copy(radiusMeters=x.radiusMeters+inflation),y.copy(radiusMeters=y.radiusMeters+inflation)) }
}

/**
 * Rigid shape against rigid shape; broadphase bounds include both angular sagittae and
 * producer FK error. Original capsule CCD supplies every narrowphase witness.
 * Earlier uncertain pairs dominate later contact. No uncertain pair is a MISS.
 */
fun firstBladeShapeContact(player: BladeShapeSweep, enemy: BladeShapeSweep,
    stats: BladeQueryStats = BladeQueryStats()): BladeShapeContact? = shapeQuery(player,enemy,null,stats)

/** Body proxy still uses the same complete steel shape and the same clock. */
fun firstBladeShapeBodyContact(player: BladeShapeSweep, body: BladeSweep,
    stats: BladeQueryStats = BladeQueryStats()): BladeShapeContact? = shapeQuery(player,null,body,stats)

private fun shapeQuery(player: BladeShapeSweep, enemy: BladeShapeSweep?, body: BladeSweep?, stats: BladeQueryStats): BladeShapeContact? {
    if(player.pathErrorMeters > MAX_SOURCE_ERROR || (enemy?.pathErrorMeters ?: 0.0) > MAX_SOURCE_ERROR)
        throw BladeContactUncertainException(0.0,"Source FK path bound exceeds 2mm admission budget")
    val playerAngle=angle(player); val enemyAngle=enemy?.let(::angle)
    val count=maxOf(steps(player,playerAngle),enemy?.let {steps(it,checkNotNull(enemyAngle))} ?: 1)
    var playerStart=player.shape.at(interpolateGrip(player.previous,player.current,0.0))
    var enemyStart=enemy?.let {it.shape.at(interpolateGrip(it.previous,it.current,0.0))}
    for(step in 0 until count) {
        val start=step.toDouble()/count; val end=(step+1.0)/count
        stats.angularIntervals++
        val playerEnd=player.shape.at(interpolateGrip(player.previous,player.current,end))
        val enemyEnd=enemy?.let {it.shape.at(interpolateGrip(it.previous,it.current,end))}
        val p=player.chords(playerStart,playerEnd,playerAngle,start,end)
        val e=enemy?.chords(checkNotNull(enemyStart),checkNotNull(enemyEnd),checkNotNull(enemyAngle),start,end)
            ?: listOf(BladeSweep(checkNotNull(body).atTime(start),body.atTime(end)))
        playerStart=playerEnd; enemyStart=enemyEnd
        val pBounds=p.map(::bounds); val eBounds=e.map(::bounds)
        stats.wholeBounds++
        if(!bounds(pBounds).intersects(bounds(eBounds))) continue
        val order=ShapeContactOrder()
        val pGroups=List(6) {bounds(pBounds,it*3,it*3+3)}
        val eGroups=if(enemy==null) listOf(eBounds[0]) else List(6) {bounds(eBounds,it*3,it*3+3)}
        for(pg in pGroups.indices) for(eg in eGroups.indices) {
            stats.groupBounds++
            if(!pGroups[pg].intersects(eGroups[eg]))continue
            for(pi in 0 until 3) for(ei in 0 until (if(enemy==null)1 else 3)) {
                val part=pg*3+pi; val other=if(enemy==null) 0 else eg*3+ei
                if(!pBounds[part].intersects(eBounds[other]))continue
                stats.capsuleQueries++
                val result=try { firstBladeContact(p[part],e[other]) }
                catch(uncertain: BladeContactUncertainException) {
                    order.uncertain(uncertain.earliestUnresolvedFraction); continue
                } ?: continue
                order.contact(BladeShapeContact(result,part,if(enemy==null)-1 else other))
            }
        }
        val best=try {order.result()} catch(uncertain:BladeContactUncertainException) {
            throw BladeContactUncertainException(start+uncertain.earliestUnresolvedFraction/count,"Earlier shape pair unresolved")
        }
        if(best!=null) {
            val fraction=start+best.contact.fraction/count
            val pp=player.shape.partAt(best.playerPartIndex,interpolateGrip(player.previous,player.current,fraction))
            val ep=if(enemy==null) checkNotNull(body).atTime(fraction)
                else enemy.shape.partAt(best.enemyPartIndex,interpolateGrip(enemy.previous,enemy.current,fraction))
            val witness=best.contact
            val pa=pp.base*(1-witness.playerAxisFraction)+pp.tip*witness.playerAxisFraction
            val ea=ep.base*(1-witness.enemyAxisFraction)+ep.tip*witness.enemyAxisFraction
            val inflation=p[best.playerPartIndex].previous.radiusMeters-pp.radiusMeters+
                e[if(enemy==null)0 else best.enemyPartIndex].previous.radiusMeters-ep.radiusMeters
            return best.copy(contact=witness.copy(fraction=fraction,
                playerPoint=pa-witness.normal*pp.radiusMeters,enemyPoint=ea+witness.normal*ep.radiusMeters,
                separationMeters=pa.distanceTo(ea)-pp.radiusMeters-ep.radiusMeters,
                relativeDisplacement=witness.relativeDisplacement*count.toDouble(),
                errorBoundMeters=witness.errorBoundMeters+inflation))
        }
    }
    return null
}

private const val ARC_ERROR=0.0005
private const val MAX_SOURCE_ERROR=0.002

/**
 * A nonpenetration certificate, including a t=0 sliding contact; this is not a CCD MISS.
 * Each capsule pair may use a different fixed support plane in each angular interval.
 * Curvature is projected onto that plane using the actual SLERP rotation axis. A turn
 * about the plane normal therefore has exactly zero projected curvature. A stationary
 * other shape also permits an exact sinusoidal projection-extrema certificate.
 * Unproved intervals are subdivided; exhausting this bounded proof returns false.
 */
fun separatingBladeShapePairs(player:BladeShapeSweep,enemy:BladeShapeSweep,normalHint:Vector3?=null):Boolean {
    if(player.pathErrorMeters>MAX_SOURCE_ERROR || enemy.pathErrorMeters>MAX_SOURCE_ERROR)return false
    val pt=turn(player);val et=turn(enemy)
    val count=maxOf(steps(player,pt.angle),steps(enemy,et.angle))
    val pending=ArrayDeque<SeparationInterval>()
    for(i in count-1 downTo 0)pending.addLast(SeparationInterval(i.toDouble()/count,(i+1.0)/count,0))
    val errors=player.pathErrorMeters+enemy.pathErrorMeters
    val hint=normalHint?.normalizedOrNull()
    var visited=0
    var pairEvaluations=0
    while(pending.isNotEmpty()) {
        if(visited++>=MAX_SEPARATION_INTERVALS)return false
        val interval=pending.removeLast();val start=interval.start;val end=interval.end;val middle=(start+end)*.5
        val p0=player.shape.at(interpolateGrip(player.previous,player.current,start))
        val p1=player.shape.at(interpolateGrip(player.previous,player.current,end))
        val e0=enemy.shape.at(interpolateGrip(enemy.previous,enemy.current,start))
        val e1=enemy.shape.at(interpolateGrip(enemy.previous,enemy.current,end))
        val pBounds=player.chords(p0,p1,pt.angle,start,end).map(::bounds)
        val eBounds=enemy.chords(e0,e1,et.angle,start,end).map(::bounds)
        if(!bounds(pBounds).intersects(bounds(eBounds)))continue
        val pm=player.shape.at(interpolateGrip(player.previous,player.current,middle))
        val em=enemy.shape.at(interpolateGrip(enemy.previous,enemy.current,middle))
        var proved=true
        pairLoop@for(i in p0.indices)for(j in e0.indices) {
            if(!pBounds[i].intersects(eBounds[j]))continue
            if(pairEvaluations++>=MAX_SEPARATION_PAIR_EVALUATIONS)return false
            val midpoint=checkNotNull(closestSegmentPoints(pm[i].base,pm[i].tip,em[j].base,em[j].tip))
            if(midpoint.first.distanceTo(midpoint.second)-pm[i].radiusMeters-em[j].radiusMeters-errors < -SEPARATION_ROUNDOFF)return false
            fun planeProves(normal:Vector3?):Boolean {
                val n=normal?.normalizedOrNull() ?: return false
                fun gap(p:BladeSegment,e:BladeSegment)=minOf(p.base.dot(n),p.tip.dot(n))-p.radiusMeters-
                    maxOf(e.base.dot(n),e.tip.dot(n))-e.radiusMeters-errors
                val a=gap(p0[i],e0[j]);val b=gap(p1[i],e1[j])
                val curvature=(projectedAcceleration(player,pt,i,n)+projectedAcceleration(enemy,et,j,n))*(end-start)*(end-start)*.5
                val t=if(curvature==0.0)0.0 else ((a+curvature-b)/(2*curvature)).coerceIn(0.0,1.0)
                if(minOf(a,b,a*(1-t)+b*t-curvature*t*(1-t))>=-SEPARATION_ROUNDOFF)return true
                if(et.angle==0.0 && enemy.previous.position==enemy.current.position) {
                    val local=player.shape.parts[i]
                    val lower=minOf(minimumProjection(player,pt,local.base,n,start,end),minimumProjection(player,pt,local.tip,n,start,end))
                    return lower-maxOf(e0[j].base.dot(n),e0[j].tip.dot(n))-p0[i].radiusMeters-e0[j].radiusMeters-errors>=-SEPARATION_ROUNDOFF
                }
                if(pt.angle==0.0 && player.previous.position==player.current.position) {
                    val local=enemy.shape.parts[j];val minus=n*-1.0
                    val upper=-minOf(minimumProjection(enemy,et,local.base,minus,start,end),minimumProjection(enemy,et,local.tip,minus,start,end))
                    return minOf(p0[i].base.dot(n),p0[i].tip.dot(n))-upper-p0[i].radiusMeters-e0[j].radiusMeters-errors>=-SEPARATION_ROUNDOFF
                }
                return false
            }
            val atStart=checkNotNull(closestSegmentPoints(p0[i].base,p0[i].tip,e0[j].base,e0[j].tip))
            if(planeProves(hint) || planeProves(midpoint.first-midpoint.second) || planeProves(atStart.first-atStart.second))continue
            proved=false;break@pairLoop
        }
        if(proved)continue
        if(interval.depth>=MAX_SEPARATION_DEPTH || middle==start || middle==end)return false
        pending.addLast(SeparationInterval(middle,end,interval.depth+1))
        pending.addLast(SeparationInterval(start,middle,interval.depth+1))
    }
    return true
}
private data class SeparationInterval(val start:Double,val end:Double,val depth:Int)
private data class GripTurn(val axis:Vector3,val angle:Double)
private fun turn(sweep:BladeShapeSweep):GripTurn {
    val a=checkNotNull(sweep.previous.rotation.normalizedOrNull());var b=checkNotNull(sweep.current.rotation.normalizedOrNull())
    if(a.x*b.x+a.y*b.y+a.z*b.z+a.w*b.w<0)b=Quaternion(-b.x,-b.y,-b.z,-b.w)
    val relative=checkNotNull((b*Quaternion(-a.x,-a.y,-a.z,a.w)).normalizedOrNull())
    val imaginary=Vector3(relative.x,relative.y,relative.z);val length=imaginary.length()
    return if(length==0.0)GripTurn(Vector3(0.0,1.0,0.0),0.0)
        else GripTurn(imaginary*(1.0/length),2*atan2(length,relative.w.coerceAtLeast(0.0)))
}
private fun projectedAcceleration(sweep:BladeShapeSweep,turn:GripTurn,index:Int,n:Vector3):Double {
    if(turn.angle==0.0)return 0.0
    val part=sweep.shape.parts[index]
    val radius=maxOf(checkNotNull(sweep.previous.rotation.rotate(part.base)).cross(turn.axis).length(),
        checkNotNull(sweep.previous.rotation.rotate(part.tip)).cross(turn.axis).length())
    return turn.angle*turn.angle*n.cross(turn.axis).length()*radius
}
/** Exact extrema of translation + one rigid-axis sinusoid, over the requested fraction interval. */
private fun minimumProjection(sweep:BladeShapeSweep,turn:GripTurn,point:Vector3,n:Vector3,start:Double,end:Double):Double {
    val v=checkNotNull(sweep.previous.rotation.rotate(point))
    val slope=(sweep.current.position-sweep.previous.position).dot(n)
    if(turn.angle==0.0)return minOf((sweep.previous.position+v).dot(n)+slope*start,(sweep.previous.position+v).dot(n)+slope*end)
    val axial=turn.axis*v.dot(turn.axis);val radial=v-axial
    val constant=(sweep.previous.position+axial).dot(n);val a=radial.dot(n);val b=turn.axis.cross(radial).dot(n)
    fun at(t:Double)=constant+slope*t+a*cos(turn.angle*t)+b*sin(turn.angle*t)
    var minimum=minOf(at(start),at(end))
    val c=turn.angle*b;val d=-turn.angle*a;val amplitude=hypot(c,d)
    if(amplitude==0.0 || abs(slope)>amplitude)return minimum
    val phase=atan2(d,c);val offset=acos((-slope/amplitude).coerceIn(-1.0,1.0))
    for(k in -1..1)for(x in listOf(phase-offset+2*PI*k,phase+offset+2*PI*k)) {
        val t=x/turn.angle
        if(t in start..end)minimum=minOf(minimum,at(t))
    }
    return minimum
}
private const val SEPARATION_ROUNDOFF=1e-7
private const val MAX_SEPARATION_INTERVALS=4096
private const val MAX_SEPARATION_DEPTH=16
private const val MAX_SEPARATION_PAIR_EVALUATIONS=16_384

/** Shared query reduction: only an earlier proven contact can dominate uncertainty. */
internal class ShapeContactOrder {
    private var best:BladeShapeContact?=null
    private var unresolved=Double.POSITIVE_INFINITY
    fun contact(value:BladeShapeContact) { if(best==null || value.contact.fraction<checkNotNull(best).contact.fraction)best=value }
    fun uncertain(fraction:Double) { unresolved=minOf(unresolved,fraction) }
    fun result():BladeShapeContact? {
        if(unresolved <= (best?.contact?.fraction ?: 1.0))throw BladeContactUncertainException(unresolved,"Earlier shape pair unresolved")
        return best
    }
}
