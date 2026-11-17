package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.ceil
import kotlin.math.cos
import kotlin.math.sin

/** A virtual Stage grip. SDK observations remain separate and are never modified. */
data class WeaponGrip(val position: Vector3, val rotation: Quaternion) {
    init {
        require(position.isFinite() && rotation.normalizedOrNull() != null) { "Weapon grip must be finite" }
    }
}

/** The sole player contact shape, rigidly placed from the asset-derived local capsules. */
fun playerBlade(grip: WeaponGrip): List<BladeSegment> = PlayerBladeShape.capsules.map { local ->
    BladeSegment(grip.position + checkNotNull(grip.rotation.rotate(local.base)),
        grip.position + checkNotNull(grip.rotation.rotate(local.tip)), local.radiusMeters)
}

data class BladeAxis(val base: Vector3, val tip: Vector3)

/** Unchanged motion/trail landmarks only. This axis is never a collision capsule. */
fun playerBladeAxis(grip: WeaponGrip) = BladeAxis(
    grip.position + checkNotNull(grip.rotation.rotate(PLAYER_BLADE_BASE)),
    grip.position + checkNotNull(grip.rotation.rotate(PLAYER_BLADE_TIP)),
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
 * Sweeps a rigid player dao against a linearly moving enemy capsule. Angular steps come
 * from the farthest authored grip radius and a 0.5 mm maximum arc-to-chord error; they
 * do not depend on body hit-volume sampling. Inflating each chord by its sagitta makes
 * this conservative for the rigid arc. This remains capsule contact, not mesh contact.
 *
 * [BladeContact.fraction] is over the complete interval. Its spatial error also includes
 * the chord inflation. The relative displacement is the local chord velocity multiplied
 * by the complete interval duration. An unresolved child query propagates explicitly.
 */
fun firstRigidBladeContact(
    previousGrip: WeaponGrip,
    currentGrip: WeaponGrip,
    enemySweep: BladeSweep,
): BladeContact? {
    val a = checkNotNull(previousGrip.rotation.normalizedOrNull())
    val b = checkNotNull(currentGrip.rotation.normalizedOrNull())
    val angle = 2.0 * acos(abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w).coerceIn(0.0, 1.0))
    val gripRadius = PlayerBladeShape.gripRadius
    val maximumStep = 2.0 * acos(1.0 - RIGID_ARC_ERROR_METERS / gripRadius)
    val steps = ceil(angle / maximumStep).toInt().coerceAtLeast(1)
    val sagitta = gripRadius * (1.0 - cos(angle / steps / 2.0))
    var previousBlade = playerBlade(previousGrip)
    for (index in 0 until steps) {
        val start = index.toDouble() / steps
        val end = (index + 1).toDouble() / steps
        val currentBlade = playerBlade(interpolateGrip(previousGrip, currentGrip, end))
        val other = BladeSweep(enemySweep.atFraction(start), enemySweep.atFraction(end))
        var earliest: BladeContact? = null
        var unresolved: BladeContactUncertainException? = null
        for (part in previousBlade.indices) {
            val playerSweep = BladeSweep(
                previousBlade[part].copy(radiusMeters = previousBlade[part].radiusMeters + sagitta),
                currentBlade[part].copy(radiusMeters = currentBlade[part].radiusMeters + sagitta),
            )
            try {
                firstBladeContact(playerSweep, other)?.let { contact ->
                    if (earliest == null || contact.fraction < checkNotNull(earliest).fraction) earliest = contact
                }
            } catch (uncertain: BladeContactUncertainException) {
                if (unresolved == null || uncertain.earliestUnresolvedFraction < checkNotNull(unresolved).earliestUnresolvedFraction) {
                    unresolved = uncertain
                }
            }
        }
        val contact = earliest
        val uncertain = unresolved
        if (uncertain != null && (contact == null || uncertain.earliestUnresolvedFraction < contact.fraction)) {
            throw BladeContactUncertainException(start + uncertain.earliestUnresolvedFraction / steps,
                "Rigid blade chain interval unresolved: ${uncertain.message}")
        }
        if (contact != null) return contact.copy(
            fraction = start + contact.fraction / steps,
            relativeDisplacement = contact.relativeDisplacement * steps.toDouble(),
            separationMeters = contact.separationMeters + sagitta,
            errorBoundMeters = contact.errorBoundMeters + sagitta,
        )
        previousBlade = currentBlade
    }
    return null
}

/**
 * A hard unilateral stop for the virtual hand and dao together. Raw tracking continues
 * unchanged. The caller locks the actual contact pose once, after choosing the earliest
 * steel/body contact. A withdrawal toward the contact normal releases the grip; when
 * the other blade has withdrawn, [releaseIfSeparated] releases it as well.
 */
class WeaponContactConstraint {
    private data class Stop(val grip: WeaponGrip, val normal: Vector3, val localPoint: Vector3)
    private var stop: Stop? = null

    val constrained: Boolean get() = stop != null

    fun lock(rawGrip: WeaponGrip, contactGrip: WeaponGrip, normal: Vector3, contactPoint: Vector3): WeaponGrip {
        // Validate both values; raw is intentionally not replaced or returned as the SDK pose.
        playerBlade(rawGrip)
        require(contactPoint.isFinite())
        val placed = playerBlade(contactGrip)
        var closest = Double.POSITIVE_INFINITY
        var localPoint: Vector3? = null
        for ((index, part) in placed.withIndex()) {
            val axis = part.tip - part.base
            val fraction = if (axis.dot(axis) == 0.0) 0.0 else
                ((contactPoint - part.base).dot(axis) / axis.dot(axis)).coerceIn(0.0, 1.0)
            val point = part.base + axis * fraction
            val gap = point.distanceTo(contactPoint) - part.radiusMeters
            if (gap < closest) {
                closest = gap
                val local = PlayerBladeShape.capsules[index]
                localPoint = local.base * (1.0 - fraction) + local.tip * fraction
            }
        }
        stop = Stop(contactGrip, requireNotNull(normal.normalizedOrNull()), checkNotNull(localPoint))
        return contactGrip
    }

    fun apply(rawGrip: WeaponGrip): WeaponGrip {
        val held = stop ?: return rawGrip
        val heldPoint = held.grip.position + checkNotNull(held.grip.rotation.rotate(held.localPoint))
        val rawPoint = rawGrip.position + checkNotNull(rawGrip.rotation.rotate(held.localPoint))
        if ((rawPoint - heldPoint).dot(held.normal) >= RELEASE_WITHDRAWAL_METERS) {
            reset()
            return rawGrip
        }
        return held.grip
    }

    fun releaseIfSeparated(enemyBlade: BladeSegment, clearanceMeters: Double = RELEASE_WITHDRAWAL_METERS, rawGrip: WeaponGrip? = null): Boolean {
        require(clearanceMeters.isFinite() && clearanceMeters >= 0.0)
        val held = stop ?: return false
        val player = playerBlade(held.grip)
        if (player.any { part ->
            val pair = requireNotNull(closestSegmentPoints(part.base, part.tip, enemyBlade.base, enemyBlade.tip))
            pair.first.distanceTo(pair.second) <= part.radiusMeters + enemyBlade.radiusMeters + clearanceMeters
        }) return false
        // Catching the real hand must itself be collision-free; a separated held blade
        // does not prove the raw hand's route has cleared the withdrawing enemy dao.
        if (rawGrip != null && firstRigidBladeContact(held.grip, rawGrip, BladeSweep(enemyBlade, enemyBlade)) != null) return false
        reset()
        return true
    }

    fun reset() { stop = null }
}

private fun BladeSweep.atFraction(fraction: Double) = BladeSegment(
    previous.base * (1.0 - fraction) + current.base * fraction,
    previous.tip * (1.0 - fraction) + current.tip * fraction,
    previous.radiusMeters * (1.0 - fraction) + current.radiusMeters * fraction,
)

private val PLAYER_BLADE_BASE = Vector3(0.022, 0.0, -0.129)
private val PLAYER_BLADE_TIP = Vector3(0.0532, 0.0, -0.849)
private const val RIGID_ARC_ERROR_METERS = 0.0005
private const val RELEASE_WITHDRAWAL_METERS = 0.025
