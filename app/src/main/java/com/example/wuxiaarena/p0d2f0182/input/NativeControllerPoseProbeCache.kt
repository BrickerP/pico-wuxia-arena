package com.example.wuxiaarena.p0d2f0182.input

import com.example.wuxiaarena.core.input.ObservedPose

internal enum class NativeControllerPoseProbeOutcome {
    ACCEPTED_TO_BUFFER, CONTROL_FAULT, STATUS_UNKNOWN, UNAVAILABLE, BUFFER_REJECTED,
}

/** One copied raw pose and gate counters for passive diagnostics; never feeds combat input. */
internal class NativeControllerPoseProbeCache {
    private var generation: Long? = null
    private var rawCallbacks = 0L
    private var acceptedToBuffer = 0L
    private var droppedControlFault = 0L
    private var droppedStatusUnknown = 0L
    private var droppedUnavailable = 0L
    private var droppedBufferRejected = 0L
    private var rawReceivedAtNanos: Long? = null
    private var rawLeft: ObservedPose? = null
    private var rawRight: ObservedPose? = null
    private var lastOutcome: NativeControllerPoseProbeOutcome? = null
    private var lastReport: NativeControllerPoseProbeReport? = null

    @Synchronized
    fun start(token: Long) {
        clear()
        generation = token
    }

    @Synchronized
    fun clear() {
        generation = null
        rawCallbacks = 0L
        acceptedToBuffer = 0L
        droppedControlFault = 0L
        droppedStatusUnknown = 0L
        droppedUnavailable = 0L
        droppedBufferRejected = 0L
        rawReceivedAtNanos = null
        rawLeft = null
        rawRight = null
        lastOutcome = null
        lastReport = null
    }

    /** Arguments contain only immutable application-owned values, never SDK frame objects. */
    @Synchronized
    fun recordRaw(token: Long, left: ObservedPose?, right: ObservedPose?, receivedAtNanos: Long) {
        if (generation != token) return
        rawCallbacks++
        rawLeft = left
        rawRight = right
        rawReceivedAtNanos = receivedAtNanos
    }

    /** The adapter records exactly one outcome per active-generation callback. */
    @Synchronized
    fun recordOutcome(token: Long, outcome: NativeControllerPoseProbeOutcome) {
        if (generation != token) return
        when (outcome) {
            NativeControllerPoseProbeOutcome.ACCEPTED_TO_BUFFER -> acceptedToBuffer++
            NativeControllerPoseProbeOutcome.CONTROL_FAULT -> droppedControlFault++
            NativeControllerPoseProbeOutcome.STATUS_UNKNOWN -> droppedStatusUnknown++
            NativeControllerPoseProbeOutcome.UNAVAILABLE -> droppedUnavailable++
            NativeControllerPoseProbeOutcome.BUFFER_REJECTED -> droppedBufferRejected++
        }
        lastOutcome = outcome
    }

    /** Called by the existing main-thread frame loop, even if no HMD frame is available. */
    @Synchronized
    fun poll(nowNanos: Long): NativeControllerPoseProbeReport? {
        val token = generation ?: return null
        val previous = lastReport
        val elapsed = previous?.let { nowNanos - it.polledAtNanos }
        if (elapsed != null && elapsed < 200_000_000L) return null
        val changed = rawCallbacks > 0 && (previous == null || previous.rawCallbacks == 0L ||
            previous.rawLeft != rawLeft || previous.rawRight != rawRight || previous.lastOutcome != lastOutcome)
        if (previous != null && !changed && requireNotNull(elapsed) < 1_000_000_000L) return null
        return NativeControllerPoseProbeReport(
            generation = token,
            rawCallbacks = rawCallbacks,
            acceptedToBuffer = acceptedToBuffer,
            droppedControlFault = droppedControlFault,
            droppedStatusUnknown = droppedStatusUnknown,
            droppedUnavailable = droppedUnavailable,
            droppedBufferRejected = droppedBufferRejected,
            rawReceivedAtNanos = rawReceivedAtNanos,
            polledAtNanos = nowNanos,
            rawLeft = rawLeft,
            rawRight = rawRight,
            lastOutcome = lastOutcome,
            reason = if (changed) "changed" else "heartbeat",
        ).also { lastReport = it }
    }
}

internal data class NativeControllerPoseProbeReport(
    val generation: Long,
    val rawCallbacks: Long,
    val acceptedToBuffer: Long,
    val droppedControlFault: Long,
    val droppedStatusUnknown: Long,
    val droppedUnavailable: Long,
    val droppedBufferRejected: Long,
    val rawReceivedAtNanos: Long?,
    val polledAtNanos: Long,
    val rawLeft: ObservedPose?,
    val rawRight: ObservedPose?,
    val lastOutcome: NativeControllerPoseProbeOutcome?,
    val reason: String,
) {
    fun message(): String =
        "generation=$generation rawCallbacks=$rawCallbacks acceptedToBuffer=$acceptedToBuffer " +
            "droppedControlFault=$droppedControlFault droppedStatusUnknown=$droppedStatusUnknown " +
            "droppedUnavailable=$droppedUnavailable droppedBufferRejected=$droppedBufferRejected " +
            "rawReceivedAtNanos=$rawReceivedAtNanos lastOutcome=$lastOutcome " +
            "polledAtNanos=$polledAtNanos reason=$reason " +
            "rawLeft={${describe(rawLeft)}} rawRight={${describe(rawRight)}}"

    private fun describe(pose: ObservedPose?): String =
        "available=${pose != null} positionValid=${pose?.position != null} " +
            "rotationValid=${pose?.rotation != null} quality=${pose?.quality} " +
            "position=${pose?.position} rotation=${pose?.rotation}"
}
