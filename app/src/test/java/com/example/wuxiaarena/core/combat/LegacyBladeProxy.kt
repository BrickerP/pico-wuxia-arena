package com.example.wuxiaarena.core.combat

import kotlin.math.*

// Frozen original single-axis query retained only to compare against the new shape.
// Production source SHA256: 4a31380c5e073db9ed81a1f93b97557c46ef7318181480b1160ed55d5bed0d23
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

private fun BladeSweep.atFraction(fraction: Double) = BladeSegment(
    previous.base * (1.0 - fraction) + current.base * fraction,
    previous.tip * (1.0 - fraction) + current.tip * fraction,
    previous.radiusMeters * (1.0 - fraction) + current.radiusMeters * fraction,
)

private const val PLAYER_GRIP_RADIUS_METERS = 0.851
private const val RIGID_ARC_ERROR_METERS = 0.0005
