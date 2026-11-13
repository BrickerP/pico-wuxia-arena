package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3
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
        enemy: Vector3?,
        fullHeightMeters: Double,
    ): TerminalControlPose? {
        // A late old state must not clear or replace a newer terminal anchor.
        if (generation < 0L || generation < this.generation) return pose
        if (generation != this.generation) {
            this.generation = generation
            pose = null
        }
        if (!terminal || !inputReady || head == null || enemy == null ||
            !head.isFinite() || !enemy.isFinite() || !fullHeightMeters.isFinite() || fullHeightMeters <= 0.0
        ) {
            pose = null
            return null
        }
        val dx = enemy.x - head.x
        val dz = enemy.z - head.z
        val distance = hypot(dx, dz)
        if (!distance.isFinite() || distance <= 1e-6) {
            pose = null
            return null
        }
        pose?.let { return it }
        val forward = Vector3(dx / distance, 0.0, dz / distance)
        val right = Vector3(-forward.z, 0.0, forward.x)
        val position = head + forward * 0.85 - right * 0.18 +
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
