package com.example.wuxiaarena.p0d2f0182.input

import androidx.annotation.MainThread
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservedPose
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

    val lastProviderFailure: PicoProviderFailure?
        get() = synchronized(gate) { providerFailure }

    @MainThread
    fun start() {
        synchronized(gate) { if (active) return }
        if (hmdRegistered || controllerRegistered || hmdStartAttempted || controllerStartAttempted) cleanup()
        val token = synchronized(gate) {
            if (active) return
            active = true
            generation++
            clearHeadComponents()
            clearControllerComponents()
            providerFailure = null
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
        try {
            hmdRegistered = true
            hmd.addListener(headListener)
            controllerRegistered = true
            controllers.addListener(handsListener)
            hmdStartAttempted = true
            hmd.start()
            controllerStartAttempted = true
            controllers.start()
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
            if (!active) return
            generation
        }
        val headStatus = readAvailability(hmd)
        val handsStatus = readAvailability(controllers)
        synchronized(gate) {
            if (!active || token != generation) return
            headStatus.error?.let { providerFailure = PicoProviderFailure(TrackingTarget.HEAD, it) }
            handsStatus.error?.let { providerFailure = PicoProviderFailure(TrackingTarget.BOTH_HANDS, it) }
            hmdStatusKnown = true
            controllerStatusKnown = true
            updateHeadAvailability(headStatus.reason)
            updateControllerAvailability(handsStatus.reason)
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
        if (active) buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, DiscontinuityReason.USER_PAUSED)
    }

    private fun onHead(token: Long, data: HMDTrackingData) {
        synchronized(gate) {
            if (!active || token != generation) return
            if (!hmdStatusKnown) {
                if (!hmdPreStatusGap) {
                    buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.QUEUE_GAP)
                    hmdPreStatusGap = true
                }
                return
            }
            if (hmdUnavailable != null) return
            val pose = observe(data.hmdPose.position, data.hmdPose.rotation)
            val position = pose.position != null
            val rotation = pose.rotation != null
            if ((headPosition && !position) || (headRotation && !rotation)) {
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, DiscontinuityReason.PROVIDER_UNAVAILABLE)
            }
            headPosition = position
            headRotation = rotation
            buffer.offerHead(InputOrigin.PICO, pose)
        }
    }

    private fun onControllers(token: Long, data: ControllerTrackingData) {
        synchronized(gate) {
            if (!active || token != generation) return
            if (!controllerStatusKnown) {
                if (!controllerPreStatusGap) {
                    buffer.discontinuity(InputOrigin.PICO, TrackingTarget.BOTH_HANDS, DiscontinuityReason.QUEUE_GAP)
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
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.LEFT_HAND, DiscontinuityReason.PROVIDER_UNAVAILABLE)
            }
            if ((rightPosition && !rightPos) || (rightRotation && !rightRot)) {
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.RIGHT_HAND, DiscontinuityReason.PROVIDER_UNAVAILABLE)
            }
            leftPosition = leftPos
            leftRotation = leftRot
            rightPosition = rightPos
            rightRotation = rightRot
            buffer.offerControllers(InputOrigin.PICO, left, right)
        }
    }

    private fun updateHeadAvailability(reason: DiscontinuityReason?) {
        if (reason != hmdUnavailable) {
            if (reason != null) {
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.HEAD, reason)
                clearHeadComponents()
            }
            hmdUnavailable = reason
        }
    }

    private fun updateControllerAvailability(reason: DiscontinuityReason?) {
        if (reason != controllersUnavailable) {
            if (reason != null) {
                buffer.discontinuity(InputOrigin.PICO, TrackingTarget.BOTH_HANDS, reason)
                clearControllerComponents()
            }
            controllersUnavailable = reason
        }
    }

    private fun deactivate(reason: DiscontinuityReason): Boolean = synchronized(gate) {
        if (!active) return false
        active = false
        generation++
        buffer.discontinuity(InputOrigin.PICO, TrackingTarget.ALL, reason)
        true
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
