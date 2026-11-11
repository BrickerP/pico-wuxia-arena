package com.example.wuxiaarena.p0d2f0182.runtime

import android.content.pm.ApplicationInfo
import android.os.Build
import android.util.Log
import androidx.annotation.MainThread
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingControlOverflowException
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.p0d2f0182.input.PicoTrackingAdapter
import com.pico.spatial.tracking.DataProvider
import com.pico.spatial.tracking.controller.ControllerTrackingProvider
import com.pico.spatial.tracking.hmd.HMDTrackingProvider
import kotlinx.coroutines.isActive
import kotlin.coroutines.coroutineContext

private const val TAG = "ArenaTracking"
// Initial bound for the prototype; device measurements will inform tuning.
private const val BUFFER_CAPACITY = 256
private const val STATUS_POLL_NANOS = 100_000_000L
private const val STOP_ATTEMPTS = 4

enum class InputControlResult { APPLIED, PENDING, UNAVAILABLE }

interface TrackingControls {
    @MainThread fun pause(): InputControlResult
    @MainThread fun resume(confirmedPauseId: Long): Boolean
    @MainThread fun resetRound(): InputControlResult
}

private class TrackingSession(
    private val diagnosticsEnabled: Boolean,
    private val inputOrigin: InputOrigin,
    private val onObservation: (TrackingEvent, Boolean, TrackingSnapshot) -> Unit,
    private val onControlsChanged: (TrackingControls?) -> Unit,
    private val onResumeRequested: (Long) -> Boolean,
    private val onTick: (Long) -> Unit,
) {
    private enum class PendingControl { PAUSE, ROUND_RESET }

    private val buffer = TrackingEventBuffer(BUFFER_CAPACITY)
    private val headProvider = HMDTrackingProvider()
    private val controllerProvider = ControllerTrackingProvider()
    private val adapter = PicoTrackingAdapter(
        buffer, headProvider, controllerProvider,
        inputOrigin = inputOrigin,
        diagnosticsEnabled = diagnosticsEnabled,
    )
    private val processor = TrackingProcessor()
    private var attempted = false
    private var active = false
    private var lastPollFrame: Long? = null
    private var observedReady = false
    private var sawHead = false
    private var sawControllers = false
    private var reportedFailure: Throwable? = null
    private var pendingControlRecovery = false
    private var lastHeadStatus: Pair<DataProvider.State, DataProvider.SupportState>? = null
    private var lastControllerStatus: Pair<DataProvider.State, DataProvider.SupportState>? = null
    private var newestHeadObservation: TrackingEvent.Head? = null
    private var lastLoggedHeadPose: ObservedPose? = null
    private var controlGeneration = 0L
    private var publishedControls: TrackingControls? = null
    private var pendingControl: PendingControl? = null
    private var pendingControlEnqueued = false
    private var controlInProgress = false
    private var stopRequested = false
    private var stopInProgress = false

    fun start() {
        if (active) return
        if (attempted || stopRequested) stop()
        if (attempted || stopRequested) return
        attempted = true
        try {
            if (diagnosticsEnabled) {
                Log.i(TAG, "Input source mode=SDK_NATIVE origin=$inputOrigin")
                lastHeadStatus = null
                lastControllerStatus = null
            }
            adapter.start()
            if (diagnosticsEnabled) {
                Log.i(TAG, "Provider start results head=${adapter.lastHmdStartResult}, controllers=${adapter.lastControllerStartResult}, receivedAtNanos=${System.nanoTime()}")
                logProviderStatus()
            }
            active = true
            lastPollFrame = null
            sawHead = false
            sawControllers = false
            newestHeadObservation = null
            lastLoggedHeadPose = null
            reportedFailure = null
            pendingControlRecovery = false
            Log.i(TAG, "Tracking provider start requested")
            publishControls()
        } catch (error: Exception) {
            if (diagnosticsEnabled) {
                Log.i(TAG, "Provider start interrupted head=${adapter.lastHmdStartResult}, controllers=${adapter.lastControllerStartResult}, receivedAtNanos=${System.nanoTime()}")
                logProviderStatus()
            }
            Log.e(TAG, "Unable to start tracking", error)
        }
    }

    fun onFrame(frameNanos: Long) {
        if (!active) {
            if (stopRequested) stop()
            return
        }
        try {
            val previous = lastPollFrame
            val pollDue = previous == null || frameNanos < previous || frameNanos - previous >= STATUS_POLL_NANOS
            if (pollDue) {
                adapter.pollAvailability()
                if (diagnosticsEnabled) logProviderStatus()
                lastPollFrame = frameNanos
            }
            adapter.pollDiagnostics(System.nanoTime())
            drain()
            if (diagnosticsEnabled && pollDue) logObservedHeadMovement()
            val failure = adapter.lastProviderFailure
            if (failure != null && failure.cause !== reportedFailure) {
                reportedFailure = failure.cause
                pendingControlRecovery = failure.cause is TrackingControlOverflowException
                Log.w(TAG, "Tracking provider reported ${failure.target}", failure.cause)
            }
            if (pendingControl != null) finishPendingControl()
            if (pendingControlRecovery) {
                pendingControlRecovery = !adapter.recoverControlOverflow()
                drain()
            }
            if (active) onTick(System.nanoTime())
        } catch (error: Exception) {
            Log.e(TAG, "Tracking update failed", error)
            stop()
        }
    }

    fun stop() {
        active = false
        revokeControls()
        stopRequested = true
        if (controlInProgress || stopInProgress) return
        stopInProgress = true
        try {
            stopProviders()
        } finally {
            if (pendingControl != null) {
                Log.w(TAG, "APP_PAUSED closed an unfinished UI control: $pendingControl; enqueued=$pendingControlEnqueued")
            }
            pendingControl = null
            pendingControlEnqueued = false
            pendingControlRecovery = false
            stopInProgress = false
        }
    }

    private fun stopProviders() {
        if (pendingControl != null) {
            try {
                if (!finishPendingControl()) {
                    Log.e(TAG, "Unable to finish input control before stop: $pendingControl; enqueued=$pendingControlEnqueued")
                }
            } catch (error: Exception) {
                Log.e(TAG, "Unable to deliver input control before stop: $pendingControl", error)
            }
        }
        if (!attempted) {
            stopRequested = false
            return
        }
        if (observedReady) {
            observedReady = false
            Log.i(TAG, "Required observations present=false; tracking stopped")
        }
        var failure: Exception? = null
        var stopped = false
        for (attempt in 0 until STOP_ATTEMPTS) {
            try {
                adapter.stop()
                stopped = true
                failure = null
                break
            } catch (error: Exception) {
                failure = error
                drainDuringStop()
                if (error is TrackingControlOverflowException) {
                    try {
                        adapter.recoverControlOverflow()
                    } catch (recoveryError: Exception) {
                        error.addSuppressed(recoveryError)
                    }
                }
            }
        }
        drainDuringStop()
        if (diagnosticsEnabled) logProviderStatus()
        if (stopped) {
            attempted = false
            stopRequested = false
            Log.i(TAG, "Tracking providers stopped")
        } else {
            Log.e(TAG, "Unable to stop tracking cleanly; pendingControl=$pendingControl", failure)
        }
    }

    private fun drainDuringStop() {
        try {
            drain()
        } catch (error: Exception) {
            // An application callback failure must not prevent provider cleanup/retry.
            Log.e(TAG, "Unable to deliver tracking observations during APP_PAUSED", error)
        }
    }

    private fun publishControls() {
        val token = ++controlGeneration
        val controls = object : TrackingControls {
            override fun pause(): InputControlResult = requestControl(token, PendingControl.PAUSE)
            override fun resetRound(): InputControlResult = requestControl(token, PendingControl.ROUND_RESET)
            override fun resume(confirmedPauseId: Long): Boolean = requestResume(token, confirmedPauseId)
        }
        publishedControls = controls
        notifyControls(controls)
    }

    private fun revokeControls() {
        controlGeneration++
        if (publishedControls == null) return
        publishedControls = null
        notifyControls(null)
    }

    private fun notifyControls(controls: TrackingControls?) {
        try {
            onControlsChanged(controls)
        } catch (error: Exception) {
            Log.e(TAG, "Unable to publish tracking controls", error)
        }
    }

    private fun controlsAreCurrent(token: Long): Boolean = active && token == controlGeneration

    private fun requestControl(token: Long, request: PendingControl): InputControlResult {
        if (!controlsAreCurrent(token)) return InputControlResult.UNAVAILABLE
        val pending = pendingControl
        if (pending != null) {
            return if (pending == request) InputControlResult.PENDING else InputControlResult.UNAVAILABLE
        }
        if (controlInProgress) return InputControlResult.UNAVAILABLE
        pendingControl = request
        pendingControlEnqueued = false
        return try {
            val completed = finishPendingControl()
            if (!controlsAreCurrent(token)) InputControlResult.UNAVAILABLE
            else if (completed) InputControlResult.APPLIED
            else InputControlResult.PENDING
        } catch (error: Exception) {
            Log.e(TAG, "Unable to apply input control $request", error)
            stop()
            InputControlResult.UNAVAILABLE
        }
    }

    /** Retries the same bounded control barrier; observation callbacks keep their queue order. */
    private fun finishPendingControl(): Boolean {
        if (pendingControl == null) return true
        if (controlInProgress) return false
        controlInProgress = true
        try {
            for (attempt in 0 until STOP_ATTEMPTS) {
                val request = pendingControl ?: return true
                if (!pendingControlEnqueued) {
                    try {
                        when (request) {
                            PendingControl.PAUSE -> adapter.markUserPause()
                            PendingControl.ROUND_RESET -> buffer.discontinuity(
                                inputOrigin,
                                TrackingTarget.ALL,
                                DiscontinuityReason.ROUND_RESET,
                            )
                        }
                        pendingControlEnqueued = true
                    } catch (_: TrackingControlOverflowException) {
                        drain()
                        pendingControlRecovery = !adapter.recoverControlOverflow()
                        drain()
                        continue
                    }
                }
                drain()
                pendingControlRecovery = !adapter.recoverControlOverflow()
                drain()
                if (!pendingControlRecovery) {
                    pendingControl = null
                    pendingControlEnqueued = false
                    return true
                }
            }
            return false
        } finally {
            controlInProgress = false
            if (stopRequested && !stopInProgress) stop()
        }
    }

    private fun requestResume(token: Long, confirmedPauseId: Long): Boolean {
        if (!controlsAreCurrent(token) || controlInProgress || pendingControl != null) return false
        controlInProgress = true
        try {
            for (attempt in 0 until STOP_ATTEMPTS) {
                drain()
                pendingControlRecovery = !adapter.recoverControlOverflow()
                drain()
                if (!pendingControlRecovery) {
                    if (!controlsAreCurrent(token)) return false
                    // An unready/stale confirmation is returned immediately and is never stored.
                    val resumed = onResumeRequested(confirmedPauseId)
                    return controlsAreCurrent(token) && resumed
                }
            }
            return false
        } catch (error: Exception) {
            Log.e(TAG, "Unable to request resume", error)
            return false
        } finally {
            controlInProgress = false
            if (stopRequested && !stopInProgress) stop()
        }
    }

    private fun drain() {
        val batch = buffer.drain()
        if (batch.droppedEvents > 0) Log.w(TAG, "Tracking queue dropped ${batch.droppedEvents} observations")
        processor.process(batch, ::onEvent)
    }

    private fun logProviderStatus() {
        try {
            val head = headProvider.state to headProvider.supportState
            val controllers = controllerProvider.state to controllerProvider.supportState
            if (head != lastHeadStatus) {
                Log.i(TAG, "Head provider state=${head.first}, supportState=${head.second}, receivedAtNanos=${System.nanoTime()}")
                lastHeadStatus = head
            }
            if (controllers != lastControllerStatus) {
                Log.i(TAG, "Controller provider state=${controllers.first}, supportState=${controllers.second}, receivedAtNanos=${System.nanoTime()}")
                lastControllerStatus = controllers
            }
        } catch (error: Exception) {
            Log.w(TAG, "Unable to read diagnostic provider state", error)
        }
    }

    private fun onEvent(event: TrackingEvent, accepted: Boolean, snapshot: TrackingSnapshot) {
        if (!accepted) Log.w(TAG, "Rejected tracking observation ${event.stamp.sequence}")
        if (diagnosticsEnabled && accepted && event is TrackingEvent.Head) {
            newestHeadObservation = event
        }
        if (accepted && event is TrackingEvent.Discontinuity) {
            Log.i(TAG, "Tracking discontinuity: target=${event.target}, reason=${event.reason}")
        }
        if (accepted && event is TrackingEvent.Head && !sawHead) {
            sawHead = true
            Log.i(TAG, "First head pose observed; origin=${event.stamp.origin}")
        }
        if (accepted && event is TrackingEvent.Controllers && !sawControllers) {
            sawControllers = true
            Log.i(TAG, "First controller snapshot observed; left=${event.left != null}, right=${event.right != null}, origin=${event.stamp.origin}, source=SDK_NATIVE")
        }
        if (snapshot.hasRequiredObservations != observedReady) {
            observedReady = snapshot.hasRequiredObservations
            Log.i(TAG, "Required observations present=$observedReady; hardware tracking quality remains unknown")
        }
        onObservation(event, accepted, snapshot)
    }

    private fun logObservedHeadMovement() {
        val observation = newestHeadObservation ?: return
        if (observation.pose == lastLoggedHeadPose) return
        lastLoggedHeadPose = observation.pose
        Log.i(
            TAG,
            "Head observation sequence=${observation.stamp.sequence}, " +
                "receivedAtNanos=${observation.stamp.receivedAtNanos}, " +
                "origin=${observation.stamp.origin}, " +
                "position=${observation.pose?.position}, rotation=${observation.pose?.rotation}",
        )
    }
}

@Composable
fun ObserveTracking(
    onEvent: (TrackingEvent, Boolean, TrackingSnapshot) -> Unit,
    onControlsChanged: (TrackingControls?) -> Unit = {},
    onResumeRequested: (Long) -> Boolean = { false },
    onTick: (Long) -> Unit = {},
) {
    val lifecycleOwner = LocalLifecycleOwner.current
    val context = LocalContext.current
    val isEmulator = Build.HARDWARE == "ranchu"
    val inputOrigin = if (isEmulator) InputOrigin.DESKTOP else InputOrigin.PICO
    val diagnosticsEnabled = (context.applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0 && isEmulator
    val currentOnEvent = rememberUpdatedState(onEvent)
    val currentOnControlsChanged = rememberUpdatedState(onControlsChanged)
    val currentOnResumeRequested = rememberUpdatedState(onResumeRequested)
    val currentOnTick = rememberUpdatedState(onTick)
    val session = remember(diagnosticsEnabled, inputOrigin) {
        TrackingSession(
            diagnosticsEnabled,
            inputOrigin,
            onObservation = { event, accepted, snapshot -> currentOnEvent.value(event, accepted, snapshot) },
            onControlsChanged = { currentOnControlsChanged.value(it) },
            onResumeRequested = { currentOnResumeRequested.value(it) },
            onTick = { currentOnTick.value(it) },
        )
    }

    DisposableEffect(lifecycleOwner, session) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> session.start()
                Lifecycle.Event.ON_PAUSE -> session.stop()
                else -> Unit
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose {
            lifecycleOwner.lifecycle.removeObserver(observer)
            session.stop()
        }
    }

    LaunchedEffect(session) {
        while (coroutineContext.isActive) {
            val frameNanos = withFrameNanos { it }
            session.onFrame(frameNanos)
        }
    }
}
