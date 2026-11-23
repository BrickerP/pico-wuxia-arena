package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult

internal data class PlayerHandTransform(val position: Vector3, val rotation: Quaternion)

/** The result panel still uses real tracking while the game's hand and weapon models are hidden. */
internal class PlayerModelInput {
    var tracking: TrackingSnapshot? = null
    var result = TrialResult.READY
    val showingResults get() = result == TrialResult.VICTORY || result == TrialResult.DEFEAT
    val modelSnapshot get() = tracking.takeUnless { showingResults }
}

/**
 * Both baked hand assets use the dao's common grip origin and axes.
 * Their geometry and rigs own hand chirality; the same Stage pose places either root.
 */
internal fun playerHandTransform(pose: ObservedPose?): PlayerHandTransform? {
    if (pose == null || pose.quality == TrackingQuality.SOURCE_REPORTED_INVALID) return null
    val position = pose.position?.takeIf { it.isFinite() } ?: return null
    val rotation = pose.rotation?.normalizedOrNull() ?: return null
    // SDK transforms are float-valued; finite doubles may still overflow on conversion.
    return PlayerHandTransform(position, rotation).takeIf {
        it.position.x.toFloat().isFinite() && it.position.y.toFloat().isFinite() &&
            it.position.z.toFloat().isFinite()
    }
}

/** The equipped hand consumes the final virtual grip; the other hand keeps its SDK pose. */
internal fun presentedPlayerHandTransform(
    snapshot: TrackingSnapshot?,
    grip: WeaponGrip?,
    hand: Hand,
): PlayerHandTransform? {
    val equippedHand = snapshot?.dominantHand ?: return null
    return if (hand == equippedHand) {
        if (!snapshot.hasRequiredObservations || grip == null) return null
        playerHandTransform(ObservedPose(grip.position, grip.rotation))
    } else {
        playerHandTransform((if (hand == Hand.LEFT) snapshot.left else snapshot.right)?.pose)
    }
}

/** Grip and guard input are action intent; the equipped hand keeps holding its dao. */
internal fun playerHandGripTime(hand: Hand, equippedHand: Hand): Float =
    if (hand == equippedHand) 1f else 0f

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
