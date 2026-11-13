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
    val maximumStep = 2.0 * acos(1.0 - RIGID_ARC_ERROR_METERS / PLAYER_GRIP_RADIUS_METERS)
    val steps = ceil(angle / maximumStep).toInt().coerceAtLeast(1)
    val sagitta = PLAYER_GRIP_RADIUS_METERS * (1.0 - cos(angle / steps / 2.0))
    var previousBlade = playerBlade(previousGrip)
    for (index in 0 until steps) {
        val start = index.toDouble() / steps
        val end = (index + 1).toDouble() / steps
        val currentBlade = playerBlade(interpolateGrip(previousGrip, currentGrip, end))
        val playerSweep = BladeSweep(
            previousBlade.copy(radiusMeters = previousBlade.radiusMeters + sagitta),
            currentBlade.copy(radiusMeters = currentBlade.radiusMeters + sagitta),
        )
        val contact = try {
            firstBladeContact(playerSweep, BladeSweep(enemySweep.atFraction(start), enemySweep.atFraction(end)))
        } catch (uncertain: BladeContactUncertainException) {
            throw BladeContactUncertainException(start + uncertain.earliestUnresolvedFraction / steps,
                "Rigid blade interval unresolved: ${uncertain.message}")
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
    private data class Stop(val grip: WeaponGrip, val normal: Vector3, val axisFraction: Double)
    private var stop: Stop? = null

    val constrained: Boolean get() = stop != null

    fun lock(rawGrip: WeaponGrip, contactGrip: WeaponGrip, normal: Vector3, playerAxisFraction: Double = 0.5): WeaponGrip {
        // Validate both values; raw is intentionally not replaced or returned as the SDK pose.
        playerBlade(rawGrip)
        require(playerAxisFraction.isFinite() && playerAxisFraction in 0.0..1.0)
        stop = Stop(contactGrip, requireNotNull(normal.normalizedOrNull()), playerAxisFraction)
        return contactGrip
    }

    fun apply(rawGrip: WeaponGrip): WeaponGrip {
        val held = stop ?: return rawGrip
        val heldBlade = playerBlade(held.grip)
        val rawBlade = playerBlade(rawGrip)
        val heldPoint = heldBlade.base * (1.0 - held.axisFraction) + heldBlade.tip * held.axisFraction
        val rawPoint = rawBlade.base * (1.0 - held.axisFraction) + rawBlade.tip * held.axisFraction
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
        val pair = requireNotNull(closestSegmentPoints(player.base, player.tip, enemyBlade.base, enemyBlade.tip))
        if (pair.first.distanceTo(pair.second) <= player.radiusMeters + enemyBlade.radiusMeters + clearanceMeters) return false
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
private const val PLAYER_BLADE_RADIUS_METERS = 0.012
// Authored tip length is 0.850665 m; bound the complete rigid span from the grip.
private const val PLAYER_GRIP_RADIUS_METERS = 0.851
private const val RIGID_ARC_ERROR_METERS = 0.0005
private const val RELEASE_WITHDRAWAL_METERS = 0.025
