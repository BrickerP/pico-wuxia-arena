package com.example.wuxiaarena.p0d2f0182.runtime

import kotlin.math.abs

/** Actual actor-local samples for one prepared idle or walk clip. */
internal class PoseClipProfile(val clip: String, samples: List<AttackPoseSample>) {
    val samples: List<AttackPoseSample> = samples.toList()

    init {
        require(clip.isNotBlank()) { "Pose clip must have a name" }
        require(this.samples.size >= 2 && this.samples.zipWithNext().all { (before, after) ->
            before.sourceSeconds < after.sourceSeconds
        }) { "Pose clips require at least two strictly increasing sample times" }
    }

    fun sample(sourceSeconds: Double): AttackPoseSample = samplePose(samples, sourceSeconds)
}

internal enum class EnemyFoot { LEFT, RIGHT }

/** A loop-relative support-entry marker; reverse playback enters the other foot's stance. */
internal data class GaitStepEvent(
    val phase: Double,
    val forwardFoot: EnemyFoot,
    val reverseFoot: EnemyFoot,
) {
    init {
        require(phase.isFinite() && phase >= 0.0 && phase < 1.0) { "Step phase must be finite and in [0, 1)" }
        require(forwardFoot != reverseFoot) { "Forward and reverse support-entry feet must differ" }
    }
}

/** Signed distance is the shared clock for playback, body/blade samples and foot markers. */
internal class LocomotionProfile(
    val idle: PoseClipProfile,
    val walk: PoseClipProfile,
    val loopStartSeconds: Double,
    val loopEndSeconds: Double,
    val strideMeters: Double,
    stepEvents: List<GaitStepEvent>,
) {
    val stepEvents: List<GaitStepEvent> = stepEvents.toList()

    init {
        require(idle.clip == "idle" && walk.clip == "walk") { "Locomotion requires the prepared idle and walk clips" }
        require(loopStartSeconds.isFinite() && loopStartSeconds >= 0.0 &&
            loopEndSeconds.isFinite() && loopEndSeconds > loopStartSeconds) {
            "Walk loop requires finite increasing non-negative source times"
        }
        require(strideMeters.isFinite() && strideMeters > 0.0) { "Walk stride must be finite and positive" }
        require(walk.samples.first().sourceSeconds <= loopStartSeconds &&
            walk.samples.last().sourceSeconds >= loopEndSeconds) { "Walk samples must cover the complete loop" }
        require(idle.samples.all { sameAnchors(it, idle.samples.first()) }) {
            "Locked idle must preserve the first sample's body and blade anchors"
        }
        require(sameAnchors(walk.sample(loopStartSeconds), walk.sample(loopEndSeconds))) {
            "Walk loop endpoints must have exactly matching body and blade anchors"
        }
        require(this.stepEvents.size == 6 && this.stepEvents.zipWithNext().all { (before, after) ->
            before.phase < after.phase
        }) { "Locked walk requires exactly six strictly increasing step phases" }
        require(this.stepEvents.withIndex().all { (index, event) ->
            val forward = if (index % 2 == 0) EnemyFoot.LEFT else EnemyFoot.RIGHT
            abs(event.phase - index / 6.0) <= 1e-9 && event.forwardFoot == forward && event.reverseFoot != forward
        }) { "Locked walk steps must use uniform sixths with alternating forward and opposite reverse feet" }
    }

    fun clip(moving: Boolean): String = if (moving) walk.clip else idle.clip

    fun sourceSeconds(moving: Boolean, gaitMeters: Double): Double {
        require(gaitMeters.isFinite()) { "Gait distance must be finite" }
        if (!moving) return idle.samples.first().sourceSeconds
        // Take the remainder first: a finite distance divided by a tiny stride can overflow.
        val signedPhase = (gaitMeters % strideMeters) / strideMeters
        val phase = if (signedPhase < 0.0) signedPhase + 1.0 else signedPhase
        val seconds = loopStartSeconds + (loopEndSeconds - loopStartSeconds) * phase
        // Rounding just below the loop seam must not select the exclusive end key.
        return if (seconds >= loopEndSeconds) Math.nextDown(loopEndSeconds) else seconds
    }

    fun sample(moving: Boolean, gaitMeters: Double): AttackPoseSample =
        (if (moving) walk else idle).sample(sourceSeconds(moving, gaitMeters))

    private fun sameAnchors(first: AttackPoseSample, second: AttackPoseSample): Boolean =
        first.contact == second.contact && first.bladeBase == second.bladeBase && first.bladeTip == second.bladeTip
}
