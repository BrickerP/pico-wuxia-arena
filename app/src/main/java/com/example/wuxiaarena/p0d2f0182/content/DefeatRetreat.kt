package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import kotlin.math.cos
import kotlin.math.hypot
import kotlin.math.sin

internal data class DefeatRetreatFrame(
    val position: Vector3,
    val distanceMeters: Double,
    val moving: Boolean,
    val elapsedNanos: Long,
)

/** Presentation clock for the surviving opponent while the retry controls are already live. */
internal class DefeatRetreat {
    private class Retreat(
        val generation: Long,
        val origin: Vector3,
        val direction: Vector3,
        val length: Double,
        var lastNanos: Long,
    ) {
        // The smoothstep derivative peaks at 1.5. Bound the actual walk to 0.9 m/s.
        val durationSeconds = maxOf(0.38, 1.5 * length / 0.9)
        var settled = length == 0.0
        var frame = DefeatRetreatFrame(origin, 0.0, false, 0L)
    }

    private var retreat: Retreat? = null

    fun reset() {
        retreat = null
    }

    fun update(state: ArenaViewState, nowNanos: Long): DefeatRetreatFrame? {
        if (state.result != TrialResult.DEFEAT || state.phase == EnemyPhase.DEAD) {
            reset()
            return null
        }
        if (retreat?.generation != state.roundGeneration) reset()
        val head = state.playerHeadPosition
        if (head == null || !head.isFinite() || state.headQuality == TrackingQuality.SOURCE_REPORTED_INVALID) {
            // Preserve the visible position across tracking loss without banking time for the next frame.
            retreat?.let { it.lastNanos = maxOf(it.lastNanos, nowNanos) }
            return retreat?.frame
        }
        val current = retreat
        if (current == null) {
            val origin = state.enemyPosition?.plus(state.enemyRecoilOffset) ?: return null
            if (!origin.isFinite()) return null
            val dx = origin.x - head.x
            val dz = origin.z - head.z
            val range = hypot(dx, dz)
            val direction = if (range > 1e-6) {
                Vector3(dx / range, 0.0, dz / range)
            } else {
                val yaw = state.enemyYawRadians.toDouble()
                if (!yaw.isFinite()) return null
                Vector3(-sin(yaw), 0.0, -cos(yaw))
            }
            val length = (2.4 - range).coerceAtLeast(0.0)
            val start = Retreat(state.roundGeneration, origin, direction, length, nowNanos)
            retreat = start
            return start.frame
        }

        val previous = current.frame
        val step = (nowNanos - current.lastNanos).coerceIn(0L, 80_000_000L)
        if (step == 0L) return previous
        current.lastNanos = nowNanos
        val elapsed = previous.elapsedNanos + step
        // Keep the original world-space path. If the player walks onto its far side,
        // stop here instead of moving towards or through the player.
        if ((previous.position - head).dot(current.direction) < 0.0) current.settled = true
        val progress = (elapsed * 1e-9 / current.durationSeconds).coerceAtMost(1.0)
        val distance = if (current.settled) previous.distanceMeters
            else current.length * progress * progress * (3.0 - 2.0 * progress)
        if (progress >= 1.0) current.settled = true
        return DefeatRetreatFrame(
            current.origin + current.direction * distance, distance, !current.settled, elapsed,
        ).also { current.frame = it }
    }
}
