package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.Quaternion
import kotlin.math.hypot

/** One stable container-space anchor for the existing full-height terminal controls. */
internal data class TerminalControlPose(
    val generation: Long,
    val position: Vector3,
    val capturedHead: Vector3,
    val fullHeightMeters: Double,
)

internal class TerminalControlPlacement {
    private var generation = Long.MIN_VALUE
    var pose: TerminalControlPose? = null
        private set

    fun update(
        generation: Long,
        terminal: Boolean,
        inputReady: Boolean,
        head: Vector3?,
        headRotation: Quaternion?,
        fullHeightMeters: Double,
    ): TerminalControlPose? {
        // A late old state must not clear or replace a newer terminal anchor.
        if (generation < 0L || generation < this.generation) return pose
        if (generation != this.generation) {
            this.generation = generation
            pose = null
        }
        if (!terminal || !inputReady || head == null || headRotation == null ||
            !head.isFinite() || !fullHeightMeters.isFinite() || fullHeightMeters <= 0.0
        ) {
            pose = null
            return null
        }
        val gaze = headRotation.rotate(Vector3(0.0, 0.0, -1.0))
        if (gaze == null) {
            pose = null
            return null
        }
        pose?.let { return it }
        val horizontal = hypot(gaze.x, gaze.z)
        val forward = if (horizontal > 1e-6) {
            Vector3(gaze.x / horizontal, 0.0, gaze.z / horizontal)
        } else {
            val right = headRotation.rotate(Vector3(1.0, 0.0, 0.0)) ?: return null
            Vector3(right.z, 0.0, -right.x).normalizedOrNull() ?: return null
        }
        val position = head + forward * 0.85 +
            Vector3(0.0, -(fullHeightMeters / 2.0 + 0.08), 0.0)
        if (!position.isFinite() || !listOf(position.x, position.y, position.z).all { it.toFloat().isFinite() }) {
            return null
        }
        return TerminalControlPose(generation, position, head, fullHeightMeters).also { pose = it }
    }

    fun clear() {
        generation = Long.MIN_VALUE
        pose = null
    }
}
