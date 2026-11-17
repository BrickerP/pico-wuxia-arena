package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.DaoBladeShape
import kotlin.math.abs
import kotlin.math.ceil

/** Actual prepared source routing, accounted by the existing HIT/RECOVERING clocks. */
internal data class EnemySourceReturn(
    val clip: String,
    val samples: List<AttackPoseSample>,
    val fromSeconds: Double,
    val guardSeconds: Double,
    val returnNanos: Long,
) {
    fun frame(elapsedNanos: Long): EnemyPoseFrame {
        val progress = (elapsedNanos.toDouble() / returnNanos).coerceIn(0.0, 1.0)
        return EnemyPoseFrame(clip, samplePose(samples, fromSeconds + (guardSeconds - fromSeconds) * progress))
    }
}

internal fun makeEnemySourceReturn(
    from: EnemyPoseFrame,
    targetStart: EnemyPoseFrame,
    samples: List<AttackPoseSample>,
    guardSources: List<Double>,
): EnemySourceReturn? {
    fun compatible(a: AttackPoseSample, b: AttackPoseSample): Boolean {
        val shape = DaoBladeShape.shape
        val start = shape.at(a.bladeGrip)
        val end = shape.at(b.bladeGrip)
        val change = start.indices.maxOf { i ->
            maxOf(start[i].base.distanceTo(end[i].base), start[i].tip.distanceTo(end[i].tip))
        }
        return change <= a.bladeGripInterpolationErrorToNextMeters + b.bladeGripInterpolationErrorToNextMeters + 1e-7
    }
    val guardBoundary=canonicalGuardSourceBoundary(from,targetStart)
    if (guardBoundary && (from.clip=="idle" || from.clip=="walk") && boundedGuardPoseJoin(from,targetStart,samples)) return null
    // A coincident weapon does not identify the chest/head/feet pose. Only the
    // same source instant or an authored common-guard endpoint can skip return.
    if (sameEnemySourceInstant(from,targetStart)) return null
    val guard = guardSources
        .filter { it in samples.first().sourceSeconds..samples.last().sourceSeconds }
        .filter { compatible(samplePose(samples, it), targetStart.pose) }
        .minByOrNull { abs(it - from.pose.sourceSeconds) } ?: return null
    if (from.pose.sourceSeconds==guard) return null
    // Preserve the actual prepared source's one-second/second rhythm. HIT accounts
    // the return before the full hurt; tracking cancellation uses RECOVERING alone.
    val duration = ceil(abs(guard - from.pose.sourceSeconds) * 1e9).toLong().coerceAtLeast(1L)
    return EnemySourceReturn(from.clip, samples, from.pose.sourceSeconds, guard, duration)
}
