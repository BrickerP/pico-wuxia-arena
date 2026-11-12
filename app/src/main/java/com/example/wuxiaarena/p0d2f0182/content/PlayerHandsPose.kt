package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3

internal data class PlayerHandTransform(val position: Vector3, val rotation: Quaternion)

/**
 * The right asset already uses the player's dao grip origin and -Z blade axis.
 * The left asset uses an anatomical wrist root, with +Y dorsal and -Z fingers.
 * Its controller-to-wrist transform is inverse(DerivedHandGrip_L * Rx(+90deg)),
 * extracted from left_hand.glb cf3203e0ed8e09f279405014c53906f0f457b6a73ebeebea49749d60cd8de541.
 * This preserves the existing controller-as-dao-grip convention. It is an
 * asset-derived mapping, not a measurement of the user's anatomical wrist.
 */
internal fun playerHandTransform(pose: ObservedPose?, hand: Hand): PlayerHandTransform? {
    if (pose == null || pose.quality == TrackingQuality.SOURCE_REPORTED_INVALID) return null
    val position = pose.position?.takeIf { it.isFinite() } ?: return null
    val rotation = pose.rotation?.normalizedOrNull() ?: return null
    val transformed = if (hand == Hand.RIGHT) {
        PlayerHandTransform(position, rotation)
    } else {
        val offset = rotation.rotate(LEFT_CONTROLLER_TO_WRIST_POSITION) ?: return null
        PlayerHandTransform(position + offset,
            (rotation * LEFT_CONTROLLER_TO_WRIST_ROTATION).normalizedOrNull() ?: return null)
    }
    // SDK transforms are float-valued; finite doubles may still overflow on conversion.
    return transformed.takeIf {
        it.position.x.toFloat().isFinite() && it.position.y.toFloat().isFinite() &&
            it.position.z.toFloat().isFinite()
    }
}

/** Grip and guard input are action intent; the equipped hand keeps holding its dao. */
internal fun playerHandGripTime(hand: Hand, equippedHand: Hand): Float =
    if (hand == equippedHand) 1f else 0f

private val LEFT_CONTROLLER_TO_WRIST_POSITION = Vector3(
    -0.07659299626489029, -0.03611927411734743, 0.015453077800029198,
)
private val LEFT_CONTROLLER_TO_WRIST_ROTATION = Quaternion(
    0.618749841086593, -0.04408467375520302, -0.7842483000710747, 0.012640392827866855,
)

/** Close every acquired handle even when an earlier native close fails. */
internal fun closePlayerHandResources(resources: List<AutoCloseable>) {
    var failure: Exception? = null
    for (resource in resources) {
        try {
            resource.close()
        } catch (error: Exception) {
            if (failure == null) failure = error else if (failure !== error) failure.addSuppressed(error)
        }
    }
    failure?.let { throw it }
}
