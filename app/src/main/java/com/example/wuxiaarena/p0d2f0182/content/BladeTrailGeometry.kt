package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3

/** Short Stage-space history of the real blade tip, with transparent cross-section edges. */
internal class BladeTrailGeometry {
    data class Ribbon(
        val positions: List<Vector3>,
        val triangleIndices: List<Int>,
        val alphas: List<Float>,
        /** Tail vertices precede this offset; the narrow hot edge follows in the same mesh. */
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
        val bladeLength = blade.length()
        if (atRest || !tipSpeed.isFinite() || tipSpeed < 0.0 ||
            !base.isFinite() || !tip.isFinite() || !blade.isFinite() ||
            !bladeLength.isFinite() || bladeLength <= GEOMETRY_EPSILON
        ) {
            clear()
            return null
        }
        // Six centimetres at most, instead of filling most of the measured blade length.
        val near = tip - blade * (minOf(TAIL_WIDTH_METRES, bladeLength) / bladeLength)
        val far = tip
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

        fun section(sample: Sample, hotCore: Boolean): List<Vector3> {
            val center = (sample.near + sample.far) * 0.5
            if (!hotCore) return listOf(sample.near, center, sample.far)
            val span = sample.far - sample.near
            val length = span.length()
            if (length <= GEOMETRY_EPSILON) return listOf(center, center, center)
            val half = span * (minOf(CORE_WIDTH_METRES, length) * 0.5 / length)
            return listOf(center - half, center, center + half)
        }

        fun append(before: Sample, after: Sample, hotCore: Boolean) {
            val sectionA = section(before, hotCore)
            val sectionB = section(after, hotCore)
            if ((sectionA + sectionB).any { !it.isFinite() }) return
            val vertices = sectionA + sectionB
            val local = listOf(0, 1, 3, 3, 1, 4, 1, 2, 4, 4, 2, 5)
                .chunked(3).filter { (a, b, c) -> hasArea(vertices[a], vertices[b], vertices[c]) }
            if (local.isEmpty()) return
            val offset = positions.size
            positions.addAll(vertices)
            val lifetime = if (hotCore) CORE_NANOS else HISTORY_NANOS
            // Both cross-section edges are exactly transparent; only the measured centre glows.
            alphas.addAll(listOf(0f, alpha(before, nowNanos, lifetime), 0f,
                0f, alpha(after, nowNanos, lifetime), 0f))
            for (triangle in local) indices.addAll(triangle.map { it + offset })
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
                // Clip only on this already-measured segment; never invent a preset swing curve.
                val fraction = (beforeAge - CORE_NANOS).toDouble() / (beforeAge - afterAge)
                Sample(before.near + (after.near - before.near) * fraction,
                    before.far + (after.far - before.far) * fraction,
                    nowNanos - CORE_NANOS,
                    before.intensity + (after.intensity - before.intensity) * fraction)
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
        const val TAIL_WIDTH_METRES = 0.06
        const val CORE_WIDTH_METRES = 0.01
        const val MAX_SAMPLES = 8
        const val GEOMETRY_EPSILON = 1e-12
    }
}
