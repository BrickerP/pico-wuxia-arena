package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.sin

/** A virtual Stage grip. SDK observations remain separate and are never modified. */
data class WeaponGrip(val position: Vector3, val rotation: Quaternion) {
    init {
        require(position.isFinite() && rotation.normalizedOrNull() != null) { "Weapon grip must be finite" }
    }
}

/** The dao's authored cutting span, in metres from its controller/hand grip. */
fun playerBlade(grip: WeaponGrip): BladeSegment = BladeSegment(
    grip.position + checkNotNull(grip.rotation.rotate(PLAYER_BLADE_BASE)),
    grip.position + checkNotNull(grip.rotation.rotate(PLAYER_BLADE_TIP)),
    PLAYER_BLADE_RADIUS_METERS,
)

fun interpolateGrip(from: WeaponGrip, to: WeaponGrip, fraction: Double): WeaponGrip {
    require(fraction.isFinite() && fraction in 0.0..1.0)
    if (fraction == 0.0) return from
    if (fraction == 1.0) return to
    val a = checkNotNull(from.rotation.normalizedOrNull())
    val b = checkNotNull(to.rotation.normalizedOrNull())
    val dot = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w
    val sign = if (dot < 0.0) -1.0 else 1.0
    val angle = acos(abs(dot).coerceIn(0.0, 1.0))
    val denominator = sin(angle)
    val aWeight = if (denominator < 1e-8) 1.0 - fraction else sin((1.0 - fraction) * angle) / denominator
    val bWeight = if (denominator < 1e-8) fraction else sin(fraction * angle) / denominator
    val rotation = checkNotNull(Quaternion(
        a.x * aWeight + b.x * bWeight * sign,
        a.y * aWeight + b.y * bWeight * sign,
        a.z * aWeight + b.z * bWeight * sign,
        a.w * aWeight + b.w * bWeight * sign,
    ).normalizedOrNull())
    return WeaponGrip(from.position * (1.0 - fraction) + to.position * fraction, rotation)
}

/**
 * A hard unilateral stop for the virtual hand and dao together. Raw tracking continues
 * unchanged. The caller locks the actual contact pose once, after choosing the earliest
 * steel/body contact. A withdrawal toward the contact normal releases the grip; when
 * the other blade has withdrawn, [releaseIfSeparated] releases it as well.
 */
class WeaponContactConstraint {
    private data class Stop(val grip: WeaponGrip, val normal: Vector3)
    private var stop: Stop? = null
    val constrained: Boolean get() = stop != null
    fun lock(rawGrip: WeaponGrip, contactGrip: WeaponGrip, normal: Vector3): WeaponGrip {
        DaoBladeShape.shape.at(rawGrip)
        stop=Stop(contactGrip,requireNotNull(normal.normalizedOrNull()))
        return contactGrip
    }
    // Release requires the other complete shape and a safe route, unavailable at observation time.
    fun apply(rawGrip: WeaponGrip): WeaponGrip = stop?.grip ?: rawGrip
    /** Natural translation or rotation exit; the raw whole blade and its route must clear. */
    fun releaseForPlayerWithdrawal(enemy:BladeShapeSweep,rawGrip:WeaponGrip?):Boolean {
        val held=stop ?: return false;val raw=rawGrip ?: return false
        val a=DaoBladeShape.shape.at(held.grip);val b=DaoBladeShape.shape.at(raw)
        // A changed real hand may naturally leave contact in any direction. Do not
        // reinterpret 25mm of one-normal retreat as a prerequisite for a proved clear path.
        // Stationary enemy-driven catchup retains its existing 25mm hysteresis below.
        if(a.indices.maxOf {i->maxOf(a[i].base.distanceTo(b[i].base),a[i].tip.distanceTo(b[i].tip))}<=ACTIVE_EXIT_SPATIAL_TOLERANCE)return false
        return releaseIfSeparated(enemy,clearanceMeters=ACTIVE_EXIT_SPATIAL_TOLERANCE,rawGrip=raw)
    }
    fun releaseIfSeparated(enemy:BladeShapeSweep,clearanceMeters:Double=RELEASE_WITHDRAWAL_METERS,rawGrip:WeaponGrip?=null):Boolean {
        require(clearanceMeters.isFinite() && clearanceMeters>=0.0)
        val held=stop ?: return false;val raw=rawGrip ?: return false
        val player=DaoBladeShape.shape;val rawParts=player.at(raw);val enemyParts=enemy.shape.at(enemy.current)
        val rawClear=rawParts.all {p->enemyParts.all {e->
            val pair=checkNotNull(closestSegmentPoints(p.base,p.tip,e.base,e.tip))
            pair.first.distanceTo(pair.second)>p.radiusMeters+e.radiusMeters+clearanceMeters+enemy.pathErrorMeters
        }}
        if(!rawClear)return false
        val catchup=BladeShapeSweep(player,held.grip,raw,0.0);val stationaryEnemy=enemy.copy(previous=enemy.current)
        // t=0 contact is retained as contact. Only an all-time nonpenetration certificate
        // permits catchup; a clear target alone never permits crossing either whole blade.
        if(!separatingBladeShapePairs(catchup,stationaryEnemy,held.normal))return false
        reset();return true
    }
    fun reset() { stop=null }
}


private val PLAYER_BLADE_BASE = Vector3(0.022, 0.0, -0.129)
private val PLAYER_BLADE_TIP = Vector3(0.0532, 0.0, -0.849)
private const val PLAYER_BLADE_RADIUS_METERS = 0.012
private const val RELEASE_WITHDRAWAL_METERS = 0.025

// Same numerical spatial tolerance as the capsule CCD/separating certificates, not a new motion-grade gate.
private const val ACTIVE_EXIT_SPATIAL_TOLERANCE=1e-7
