package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3

/** Short Stage-space history for a ribbon swept by the visible end of the real blade. */
internal class BladeTrailGeometry {
    data class Ribbon(
        val positions: List<Vector3>,
        val triangleIndices: List<Int>,
        val alphas: List<Float>,
        /** Tail vertices precede this offset; the short hot edge follows it in the same mesh. */
        val coreVertexOffset: Int,
    )

    private data class Sample(
        val near: Vector3,
        val far: Vector3,
        val atNanos: Long,
        val intensity: Double,
    )

    private val samples = ArrayDeque<Sample>()
    private var lastTime: Long? = null
    private var generation: Long? = null

    fun sample(
        base: Vector3,
        tip: Vector3,
        nowNanos: Long,
        tipSpeed: Double,
        atRest: Boolean,
        motionGeneration: Long,
    ): Ribbon? {
        val blade = tip - base
        if (atRest || !tipSpeed.isFinite() || tipSpeed < 0.0 ||
            !base.isFinite() || !tip.isFinite() || !blade.isFinite() ||
            blade.length() <= GEOMETRY_EPSILON
        ) {
            clear()
            return null
        }
        val near = base + blade * 0.35
        val far = base + blade * 0.98
        if (!near.isFinite() || !far.isFinite()) {
            clear()
            return null
        }

        val previousTime = lastTime
        if (generation != motionGeneration || (previousTime != null && nowNanos < previousTime)) clear()
        val repeatedTime = lastTime == nowNanos
        generation = motionGeneration
        lastTime = nowNanos
        while (samples.isNotEmpty() && ageNanos(samples.first().atNanos, nowNanos) >= HISTORY_NANOS) {
            samples.removeFirst()
        }
        val latest = samples.lastOrNull()
        if (!repeatedTime && (latest == null || latest.near != near || latest.far != far)) {
            samples.addLast(Sample(near, far, nowNanos, tipSpeed / (1.0 + tipSpeed)))
            if (samples.size > MAX_SAMPLES) samples.removeFirst()
        }
        return ribbon(nowNanos)
    }

    fun clear() {
        samples.clear()
        lastTime = null
        generation = null
    }

    private fun ribbon(nowNanos: Long): Ribbon? {
        if (samples.size < 2) return null
        val positions = mutableListOf<Vector3>()
        val indices = mutableListOf<Int>()
        val alphas = mutableListOf<Float>()
        fun append(before: Sample, after: Sample, hotCore: Boolean) {
            // The hot edge occupies the outer half of the sampled blade, never a preset arc.
            val beforeNear = if (hotCore) before.near + (before.far - before.near) * 0.5 else before.near
            val afterNear = if (hotCore) after.near + (after.far - after.near) * 0.5 else after.near
            val firstTriangle = hasArea(beforeNear, before.far, afterNear)
            val secondTriangle = hasArea(afterNear, before.far, after.far)
            if (!firstTriangle && !secondTriangle) return
            val offset = positions.size
            positions.addAll(listOf(beforeNear, before.far, afterNear, after.far))
            val lifetime = if (hotCore) CORE_NANOS else HISTORY_NANOS
            val beforeAlpha = alpha(before, nowNanos, lifetime)
            val afterAlpha = alpha(after, nowNanos, lifetime)
            alphas.addAll(listOf(beforeAlpha, beforeAlpha, afterAlpha, afterAlpha))
            if (firstTriangle) indices.addAll(listOf(offset, offset + 1, offset + 2))
            if (secondTriangle) indices.addAll(listOf(offset + 2, offset + 1, offset + 3))
        }
        for (index in 1 until samples.size) append(samples[index - 1], samples[index], hotCore = false)
        val coreVertexOffset = positions.size
        for (index in 1 until samples.size) {
            val before = samples[index - 1]
            val after = samples[index]
            val afterAge = ageNanos(after.atNanos, nowNanos)
            if (afterAge >= CORE_NANOS) continue
            val beforeAge = ageNanos(before.atNanos, nowNanos)
            val clipped = if (beforeAge > CORE_NANOS) {
                // Clip along the measured segment at the hot-edge age, including sparse frames.
                val fraction = (beforeAge - CORE_NANOS).toDouble() / (beforeAge - afterAge)
                Sample(
                    before.near + (after.near - before.near) * fraction,
                    before.far + (after.far - before.far) * fraction,
                    nowNanos - CORE_NANOS,
                    before.intensity + (after.intensity - before.intensity) * fraction,
                )
            } else before
            append(clipped, after, hotCore = true)
        }
        return if (indices.isEmpty()) null else Ribbon(positions, indices, alphas, coreVertexOffset)
    }

    private fun alpha(sample: Sample, nowNanos: Long, lifetimeNanos: Long): Float =
        ((1.0 - ageNanos(sample.atNanos, nowNanos).toDouble() / lifetimeNanos)
            .coerceIn(0.0, 1.0) * sample.intensity).toFloat()

    private fun hasArea(a: Vector3, b: Vector3, c: Vector3): Boolean {
        val area = (b - a).cross(c - a).length()
        return area.isFinite() && area > GEOMETRY_EPSILON
    }

    private fun ageNanos(atNanos: Long, nowNanos: Long): Long =
        (nowNanos - atNanos).takeIf { it >= 0L } ?: Long.MAX_VALUE

    private companion object {
        const val HISTORY_NANOS = 65_000_000L
        const val CORE_NANOS = 12_000_000L
        const val MAX_SAMPLES = 8
        const val GEOMETRY_EPSILON = 1e-12
    }
}
