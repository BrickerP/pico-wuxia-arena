package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.MAX_HAND_SAMPLE_AGE_NANOS
import com.example.wuxiaarena.core.math.Vector3

/** Body motion has its own receipt clock. Looking up a head sample never splits a hand sweep. */
internal class PlayerHeadPath {
    private data class Sample(val time: Long, val position: Vector3)
    private val samples = ArrayDeque<Sample>()

    fun clear() = samples.clear()

    fun record(time: Long, position: Vector3): Boolean {
        // TrackingState already rejected time regressions and coordinate discontinuities.
        val last = samples.lastOrNull()
        if (last != null && time - last.time > MAX_HAND_SAMPLE_AGE_NANOS && last.position != position) {
            return false // A reacquired head cannot sweep through the missing interval.
        }
        if (last?.time == time) samples.removeLast()
        if (samples.size >= 2 && samples.last().position == position && samples[samples.lastIndex - 1].position == position) {
            samples.removeLast() // Keep both ends of a stationary interval.
        }
        if (samples.size >= 64) return false
        samples.addLast(Sample(time, position))
        return true
    }

    fun discardBefore(time: Long) {
        while (samples.size >= 2 && samples[1].time <= time) samples.removeFirst()
    }

    fun step(time: Long, maximum: Long): Long {
        for (sample in samples) {
            if (sample.time > time) return minOf(maximum, sample.time - time)
        }
        return maximum
    }

    fun positionAt(time: Long, fallback: Vector3): Vector3 {
        var prior = samples.firstOrNull() ?: return fallback
        if (time < prior.time) return fallback
        for (i in 1 until samples.size) {
            val next = samples[i]
            if (time < next.time) {
                if (prior.position == next.position || time == prior.time) return prior.position
                val fraction = (time - prior.time).toDouble() / (next.time - prior.time)
                return prior.position * (1 - fraction) + next.position * fraction
            }
            prior = next
        }
        return prior.position
    }
}
