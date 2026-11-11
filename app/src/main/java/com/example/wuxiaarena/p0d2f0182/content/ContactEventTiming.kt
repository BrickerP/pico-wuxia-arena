package com.example.wuxiaarena.p0d2f0182.content

/** Consume even inactive events once. Resume/hitstop must never restart their presentation clock. */
internal class ResolvedSurfaceEventGate {
    private var generation = Long.MIN_VALUE
    private val seen = mutableSetOf<Pair<ContactEffectFamily, Long>>()

    fun reset(roundGeneration: Long) {
        if (generation == roundGeneration) return
        generation = roundGeneration
        seen.clear()
    }

    fun consume(
        id: Long, roundGeneration: Long, family: ContactEffectFamily,
        atNanos: Long, simulationNanos: Long, active: Boolean,
    ): Boolean {
        if (id < 0L || roundGeneration != generation || !seen.add(family to id)) return false
        return active && atNanos >= 0L && atNanos <= simulationNanos && simulationNanos - atNanos <= 120_000_000L
    }
}
