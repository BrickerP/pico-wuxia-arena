package com.example.wuxiaarena.p0d2f0182.input

import androidx.annotation.MainThread
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingControlOverflowException
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.pico.spatial.tracking.DataProvider
import com.pico.spatial.tracking.controller.ControllerPose
import com.pico.spatial.tracking.controller.ControllerTrackingData
import com.pico.spatial.tracking.controller.ControllerTrackingProvider
import com.pico.spatial.tracking.hmd.HMDTrackingData
import com.pico.spatial.tracking.hmd.HMDTrackingProvider

data class PicoProviderFailure(val target: TrackingTarget, val cause: Exception)

/**
 * The Stage owner starts/stops this adapter and calls [pollAvailability] while active.
 * A player pause uses [markUserPause] and keeps tracking active so later losses are observable.
 * No hardware sampling time or component-level tracking quality is exposed by this SDK.
 */
class PicoTrackingAdapter(
    private val buffer: TrackingEventBuffer,
    private val hmd: DataProvider<HMDTrackingData> = HMDTrackingProvider(),
    private val controllers: DataProvider<ControllerTrackingData> = ControllerTrackingProvider(),
) {
    private val gate = Any()
    private var active = false
    private var generation = 0L
    private var hmdListener: DataProvider.DataListener<HMDTrackingData>? = null
    private var controllerListener: DataProvider.DataListener<ControllerTrackingData>? = null
    private var hmdRegistered = false
    private var controllerRegistered = false
    private var hmdStartAttempted = false
    private var controllerStartAttempted = false
    private var hmdUnavailable: DiscontinuityReason? = null
    private var controllersUnavailable: DiscontinuityReason? = null
    private var hmdStatusKnown = false
    private var controllerStatusKnown = false
    private var hmdPreStatusGap = false
    private var controllerPreStatusGap = false
    private var headPosition = false
    private var headRotation = false
    private var leftPosition = false
    private var leftRotation = false
    private var rightPosition = false
    private var rightRotation = false
    private var providerFailure: PicoProviderFailure? = null
    private var controlFaulted = false
    private var pendingStopReason: DiscontinuityReason? = null
    private var pendingUserPause = false
    private var pendingProviderControl: PendingProviderControl? = null
    private var skippedCallbacks = 0L

    var lastHmdStartResult: DataProvider.StartResult? = null
        private set
    var lastControllerStartResult: DataProvider.StartResult? = null
        private set

    val lastProviderFailure: PicoProviderFailure?
        get() = synchronized(gate) { providerFailure }

    /** Application callbacks skipped while a control-overflow fault is unresolved. */
    val droppedCallbacksDuringControlFault: Long
        get() = synchronized(gate) { skippedCallbacks }

    /** Drain the buffer before retrying; recovery emits a gap for callbacks skipped during the fault. */
    @MainThread
    fun recoverControlOverflow(): Boolean = synchronized(gate) {
        if (!controlFaulted) return true
        val providerControl = pendingProviderControl
        var emittedGap = false
        if (providerControl != null) {
            try {
                buffer.discontinuity(InputOrigin.PICO, providerControl.target, providerControl.reason)
                emittedGap = providerControl.target == TrackingTarget.ALL &&
                    providerControl.reason == DiscontinuityReason.QUEUE_GAP
                pendingProviderControl = null
            } catch (_: TrackingControlOverflowException) {
                return false
            }
        }
        if (pendingStopReason != null || pendingUserPause) return false
        if (!emittedGap) {
            try {
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.QUEUE_GAP)
            } catch (_: TrackingControlOverflowException) {
                pendingProviderControl = PendingProviderControl(TrackingTarget.ALL, DiscontinuityReason.QUEUE_GAP)
                return false
            }
        }
        controlFaulted = false
        hmdStatusKnown = false
        controllerStatusKnown = false
        hmdPreStatusGap = false
        controllerPreStatusGap = false
        clearHeadComponents()
        clearControllerComponents()
        true
    }

    @MainThread
    fun start() {
        synchronized(gate) {
            if (active) return
            check(pendingStopReason == null && !pendingUserPause) { "retry the failed lifecycle control after draining the buffer" }
        }
        if (hmdRegistered || controllerRegistered || hmdStartAttempted || controllerStartAttempted) cleanup()
        val token = synchronized(gate) {
            if (active) return
            if (controlFaulted) {
                check(recoverControlOverflow()) { "drain the buffer and retry the rejected control" }
            }
            active = true
            generation++
            clearHeadComponents()
            clearControllerComponents()
            providerFailure = null
            skippedCallbacks = 0
            hmdUnavailable = null
            controllersUnavailable = null
            hmdStatusKnown = false
            controllerStatusKnown = false
            hmdPreStatusGap = false
            controllerPreStatusGap = false
            generation
        }
        val headListener = DataProvider.DataListener<HMDTrackingData> { data -> onHead(token, data) }
        val handsListener = DataProvider.DataListener<ControllerTrackingData> { data -> onControllers(token, data) }
        hmdListener = headListener
        controllerListener = handsListener
        lastHmdStartResult = null
        lastControllerStartResult = null
        try {
            hmdRegistered = true
            hmd.addListener(headListener)
            controllerRegistered = true
            controllers.addListener(handsListener)
            hmdStartAttempted = true
            lastHmdStartResult = hmd.start()
            controllerStartAttempted = true
            lastControllerStartResult = controllers.start()
            pollAvailability()
        } catch (error: Exception) {
            try {
                deactivate(DiscontinuityReason.PROVIDER_UNAVAILABLE)
            } catch (deactivateError: Exception) {
                error.addSuppressed(deactivateError)
            }
            try {
                cleanup()
            } catch (cleanupError: Exception) {
                error.addSuppressed(cleanupError)
            }
            throw error
        }
    }

    /** The SDK does not document a state-change listener; the owner must call this while active. */
    @MainThread
    fun pollAvailability() {
        val token = synchronized(gate) {
            if (!active || controlFaulted) return
            generation
        }
        val headStatus = readAvailability(hmd)
        val handsStatus = readAvailability(controllers)
        synchronized(gate) {
            if (!active || token != generation || controlFaulted) return
            headStatus.error?.let { providerFailure = PicoProviderFailure(TrackingTarget.HEAD, it) }
            handsStatus.error?.let { providerFailure = PicoProviderFailure(TrackingTarget.BOTH_HANDS, it) }
            hmdStatusKnown = true
            controllerStatusKnown = true
            try {
                updateHeadAvailability(headStatus.reason)
            } catch (_: TrackingControlOverflowException) {
                return
            }
            try {
                updateControllerAvailability(handsStatus.reason)
            } catch (_: TrackingControlOverflowException) {
                return
            }
        }
    }

    @MainThread
    fun stop(reason: DiscontinuityReason = DiscontinuityReason.APP_PAUSED) {
        require(reason != DiscontinuityReason.USER_PAUSED) { "user pause must keep tracking active" }
        var failure: Exception? = null
        val wasActive = try {
            deactivate(reason)
        } catch (error: Exception) {
            failure = error
            true
        }
        if (!wasActive && !hmdRegistered && !controllerRegistered && !hmdStartAttempted && !controllerStartAttempted) return
        try {
            cleanup()
        } catch (error: Exception) {
            if (failure == null) failure = error else failure.addSuppressed(error)
        }
        failure?.let { throw it }
    }

    @MainThread
    fun markUserPause() = synchronized(gate) {
        if (active || pendingUserPause) {
            if (controlFaulted && (!pendingUserPause || pendingProviderControl != null)) {
                pendingUserPause = true
                throw TrackingControlOverflowException()
            }
            try {
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.USER_PAUSED)
                pendingUserPause = false
            } catch (error: TrackingControlOverflowException) {
                pendingUserPause = true
                recordControlFault(TrackingTarget.ALL, error)
                throw error
            }
        }
    }

    private fun onHead(token: Long, data: HMDTrackingData) {
        synchronized(gate) {
            if (!active || token != generation) return
            if (controlFaulted) {
                skippedCallbacks++
                return
            }
            try {
                captureHead(data)
            } catch (_: TrackingControlOverflowException) {
                return
            }
        }
    }

    private fun captureHead(data: HMDTrackingData) {
        if (!hmdStatusKnown) {
            if (!hmdPreStatusGap) {
                emitProviderControl(TrackingTarget.HEAD, DiscontinuityReason.QUEUE_GAP)
                hmdPreStatusGap = true
            }
            return
        }
        if (hmdUnavailable != null) return
        val pose = observe(data.hmdPose.position, data.hmdPose.rotation)
        val position = pose.position != null
        val rotation = pose.rotation != null
        if ((headPosition && !position) || (headRotation && !rotation)) {
            emitProviderControl(TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        }
        headPosition = position
        headRotation = rotation
        buffer.offerHead(InputOrigin.PICO, pose)
    }

    private fun onControllers(token: Long, data: ControllerTrackingData) {
        synchronized(gate) {
            if (!active || token != generation) return
            if (controlFaulted) {
                skippedCallbacks++
                return
            }
            try {
                captureControllers(data)
            } catch (_: TrackingControlOverflowException) {
                return
            }
        }
    }

    private fun captureControllers(data: ControllerTrackingData) {
        if (!controllerStatusKnown) {
            if (!controllerPreStatusGap) {
                emitProviderControl(TrackingTarget.BOTH_HANDS, DiscontinuityReason.QUEUE_GAP)
                controllerPreStatusGap = true
            }
            return
        }
        if (controllersUnavailable != null) return
        val left = data.left?.toObservation()
        val right = data.right?.toObservation()
        val leftPos = left?.position != null
        val leftRot = left?.rotation != null
        val rightPos = right?.position != null
        val rightRot = right?.rotation != null
        if ((leftPosition && !leftPos) || (leftRotation && !leftRot)) {
            emitProviderControl(TrackingTarget.LEFT_HAND, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        }
        if ((rightPosition && !rightPos) || (rightRotation && !rightRot)) {
            emitProviderControl(TrackingTarget.RIGHT_HAND, DiscontinuityReason.PROVIDER_UNAVAILABLE)
        }
        leftPosition = leftPos
        leftRotation = leftRot
        rightPosition = rightPos
        rightRotation = rightRot
        buffer.offerControllers(InputOrigin.PICO, left, right)
    }

    private fun updateHeadAvailability(reason: DiscontinuityReason?) {
        if (reason != hmdUnavailable) {
            if (reason != null) {
                emitProviderControl(TrackingTarget.HEAD, reason)
                clearHeadComponents()
            }
            hmdUnavailable = reason
        }
    }

    private fun updateControllerAvailability(reason: DiscontinuityReason?) {
        if (reason != controllersUnavailable) {
            if (reason != null) {
                emitProviderControl(TrackingTarget.BOTH_HANDS, reason)
                clearControllerComponents()
            }
            controllersUnavailable = reason
        }
    }

    private fun deactivate(reason: DiscontinuityReason): Boolean = synchronized(gate) {
        if (!active) {
            val pending = pendingStopReason ?: return false
            require(reason == pending) { "retry the failed stop with the same reason" }
            if (pendingProviderControl != null || pendingUserPause) throw TrackingControlOverflowException()
            buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, pending)
            pendingStopReason = null
            return true
        }
        active = false
        generation++
        try {
            if (pendingProviderControl != null || pendingUserPause) throw TrackingControlOverflowException()
            buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, reason)
        } catch (error: Exception) {
            pendingStopReason = reason
            if (error is TrackingControlOverflowException) recordControlFault(TrackingTarget.ALL, error)
            throw error
        }
        true
    }

    private data class PendingProviderControl(val target: TrackingTarget, val reason: DiscontinuityReason)

    private fun emitProviderControl(target: TrackingTarget, reason: DiscontinuityReason) {
        try {
            buffer.discontinuity(InputOrigin.PICO, target, reason)
        } catch (error: TrackingControlOverflowException) {
            if (pendingProviderControl == null) pendingProviderControl = PendingProviderControl(target, reason)
            recordControlFault(target, error)
            throw error
        }
    }

    private fun recordControlFault(target: TrackingTarget, error: TrackingControlOverflowException) {
        controlFaulted = true
        providerFailure = PicoProviderFailure(target, error)
    }

    private fun clearHeadComponents() {
        headPosition = false
        headRotation = false
    }

    private fun clearControllerComponents() {
        leftPosition = false
        leftRotation = false
        rightPosition = false
        rightRotation = false
    }

    private fun cleanup() {
        var failure: Exception? = null
        fun attempt(action: () -> Unit) {
            try {
                action()
            } catch (error: Exception) {
                if (failure == null) failure = error else failure?.addSuppressed(error)
            }
        }
        if (hmdRegistered) attempt {
            hmdListener?.let(hmd::removeListener)
            hmdRegistered = false
            hmdListener = null
        }
        if (controllerRegistered) attempt {
            controllerListener?.let(controllers::removeListener)
            controllerRegistered = false
            controllerListener = null
        }
        if (hmdStartAttempted) attempt {
            hmd.stop()
            hmdStartAttempted = false
        }
        if (controllerStartAttempted) attempt {
            controllers.stop()
            controllerStartAttempted = false
        }
        failure?.let { throw it }
    }

    private data class ProviderStatus(val reason: DiscontinuityReason?, val error: Exception? = null)

    private fun readAvailability(provider: DataProvider<*>): ProviderStatus {
        return try {
            val support = provider.supportState
            val state = provider.state
            val reason = when {
                support == DataProvider.SupportState.NOT_IN_FULL_SPACE -> DiscontinuityReason.NOT_IN_FULL_SPACE
                state != DataProvider.State.STARTED || support != DataProvider.SupportState.SUPPORTED ->
                    DiscontinuityReason.PROVIDER_UNAVAILABLE
                else -> null
            }
            ProviderStatus(reason)
        } catch (error: Exception) {
            ProviderStatus(DiscontinuityReason.PROVIDER_UNAVAILABLE, error)
        }
    }

    private fun ControllerPose.toObservation(): ObservedPose = observe(position, rotation)

    private fun observe(
        position: com.pico.spatial.core.math.Vector3,
        rotation: com.pico.spatial.core.math.Quat,
    ): ObservedPose {
        val p = Vector3(position.x.toDouble(), position.y.toDouble(), position.z.toDouble())
        val q = Quaternion(rotation.x.toDouble(), rotation.y.toDouble(), rotation.z.toDouble(), rotation.w.toDouble())
        return ObservedPose(p.takeIf { it.isFinite() }, q.normalizedOrNull(), TrackingQuality.UNKNOWN)
    }
}
