package com.example.wuxiaarena.p0d2f0182.runtime

import android.content.pm.ApplicationInfo
import android.os.Build
import android.os.Process
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
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatAction
import com.pico.spatial.tracking.DataProvider
import com.pico.spatial.tracking.controller.ControllerActionData
import com.pico.spatial.tracking.controller.ControllerTrackingProvider
import com.pico.spatial.tracking.hmd.HMDTrackingProvider
import kotlinx.coroutines.isActive
import kotlin.coroutines.coroutineContext

private const val TAG = "ArenaTracking"
// Initial bound for the prototype; device measurements will inform tuning.
private const val BUFFER_CAPACITY = 256
private const val STATUS_POLL_NANOS = 100_000_000L
private const val STOP_ATTEMPTS = 4
private const val ACTION_QUEUE_CAPACITY = 64
private const val ACTION_MAX_AGE_NANOS = 250_000_000L
private const val ACTION_PROBE_TAG = "ArenaActionProbe"
private const val ACTION_PROBE_CAPACITY = 16
private const val ACTION_PROBE_HEARTBEAT_NANOS = 1_000_000_000L

internal data class ControllerActionObservation(
    val generation: Long,
    val rightA: Boolean,
    val count: Long,
    val receivedAtNanos: Long,
)

internal data class ControllerActionBatch(
    val changes: List<ControllerActionObservation>,
    val presses: List<ControllerActionObservation>,
    val droppedChanges: Long,
)

/** SDK callbacks cache snapshots here. Only the Stage thread drains and acts on edges. */
internal class ControllerActionQueue(private val capacity: Int = ACTION_QUEUE_CAPACITY) {
    init { require(capacity > 0) }

    private val gate = Any()
    private val changes = ArrayDeque<ControllerActionObservation>()
    private var accepting = false
    private var generation = 0L
    private var callbacks = 0L
    private var dropped = 0L
    private var lastQueuedRightA: Boolean? = null
    private var previousRightA: Boolean? = null
    private var previousReceipt: Long? = null

    fun start(): Long = synchronized(gate) {
        generation++
        accepting = true
        callbacks = 0L
        clearHistory()
        generation
    }

    fun stop() = synchronized(gate) {
        accepting = false
        generation++
        clearHistory()
    }

    fun reset() = synchronized(gate) { clearHistory() }

    fun offer(token: Long, rightA: Boolean, receivedAtNanos: Long) = synchronized(gate) {
        if (!accepting || token != generation) return
        callbacks++
        if (lastQueuedRightA == rightA) return
        if (changes.size == capacity) {
            val lost = changes.size + 1L
            clearHistory()
            dropped += lost
            return
        }
        changes.addLast(ControllerActionObservation(token, rightA, callbacks, receivedAtNanos))
        lastQueuedRightA = rightA
    }

    fun drain(nowNanos: Long, enabled: Boolean): ControllerActionBatch = synchronized(gate) {
        val batch = changes.toList()
        val lost = dropped
        changes.clear()
        dropped = 0L
        if (!accepting || !enabled) {
            clearHistory()
            return ControllerActionBatch(batch, emptyList(), lost)
        }
        val presses = mutableListOf<ControllerActionObservation>()
        for (observation in batch) {
            val age = nowNanos - observation.receivedAtNanos
            val previous = previousReceipt
            if (observation.generation != generation || age < 0L || age > ACTION_MAX_AGE_NANOS ||
                previous != null && observation.receivedAtNanos < previous) {
                clearHistory()
                return ControllerActionBatch(batch, emptyList(), lost + batch.size)
            }
            if (previousRightA == false && observation.rightA) presses += observation
            previousRightA = observation.rightA
            previousReceipt = observation.receivedAtNanos
        }
        ControllerActionBatch(batch, presses, lost)
    }

    private fun clearHistory() {
        changes.clear()
        dropped = 0L
        lastQueuedRightA = null
        previousRightA = null
        previousReceipt = null
    }
}

enum class InputControlResult { APPLIED, PENDING, UNAVAILABLE }

interface TrackingControls {
    @MainThread fun pause(): InputControlResult
    @MainThread fun resume(confirmedPauseId: Long): Boolean
    @MainThread fun resetRound(): InputControlResult
}

private class TrackingSession(
    private val diagnosticsEnabled: Boolean,
    private val emulatorPreview: Boolean,
    private val onObservation: (TrackingEvent, Boolean, TrackingSnapshot) -> Unit,
    private val onControlsChanged: (TrackingControls?) -> Unit,
    private val onResumeRequested: (Long) -> Boolean,
    private val onTick: (Long) -> Unit,
) {
    private enum class PendingControl { PAUSE, ROUND_RESET }

    private val buffer = TrackingEventBuffer(BUFFER_CAPACITY)
    private val headProvider = HMDTrackingProvider()
    private val controllerProvider = ControllerTrackingProvider()
    private val adapter = PicoTrackingAdapter(buffer, headProvider, controllerProvider, emulatorPreview)
    private val processor = TrackingProcessor()
    private var attempted = false
    private var active = false
    private var lastPollFrame: Long? = null
    private var observedReady = false
    private var sawHead = false
    private var sawControllers = false
    private var reportedFailure: Throwable? = null
    private var pendingControlRecovery = false
    private val actionQueue = ControllerActionQueue()
    private var actionListener: ControllerTrackingProvider.ControllerActionListener? = null
    private var controllerActionsAvailable = false
    private var controllerActionsPaused = false
    private var lastControllerActionLog: Triple<Long, Boolean, Boolean>? = null
    private val actionProbeGate = Any()
    private val actionProbeChanges = ArrayDeque<ActionProbeSnapshot>()
    private var actionProbeGeneration: Long? = null
    private var actionProbeLatest: ActionProbeSnapshot? = null
    private var actionProbeLastValues: ControllerActionData? = null
    private var actionProbeDropped = 0L
    private var lastActionProbeHeartbeat: Long? = null
    private var lastHeadStatus: Pair<DataProvider.State, DataProvider.SupportState>? = null
    private var lastControllerStatus: Pair<DataProvider.State, DataProvider.SupportState>? = null
    private var newestHeadObservation: TrackingEvent.Head? = null
    private var lastLoggedHeadPose: ObservedPose? = null
    private var newestControllerObservation: TrackingEvent.Controllers? = null
    private var lastLoggedControllerPoses: Pair<ObservedPose?, ObservedPose?>? = null
    private var controlGeneration = 0L
    private var publishedControls: TrackingControls? = null
    private var pendingControl: PendingControl? = null
    private var pendingControlEnqueued = false
    private var controlInProgress = false
    private var stopRequested = false
    private var stopInProgress = false

    private data class ActionProbeSnapshot(
        val generation: Long,
        val values: ControllerActionData,
        val count: Long,
        val receivedAtNanos: Long,
    )

    fun start() {
        if (active) return
        if (attempted || stopRequested) stop()
        if (attempted || stopRequested) return
        attempted = true
        try {
            if (diagnosticsEnabled) {
                Log.i(TAG, "Input source mode=${if (emulatorPreview) "HMD_DERIVED_DESKTOP_PREVIEW" else "PICO_HARDWARE"}")
            }
            if (emulatorPreview) startControllerActions()
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
            newestControllerObservation = null
            lastLoggedControllerPoses = null
            reportedFailure = null
            pendingControlRecovery = false
            Log.i(TAG, "Tracking provider start requested")
            publishControls()
        } catch (error: Exception) {
            if (diagnosticsEnabled) {
                Log.i(TAG, "Provider start interrupted head=${adapter.lastHmdStartResult}, controllers=${adapter.lastControllerStartResult}, receivedAtNanos=${System.nanoTime()}")
                logProviderStatus()
            }
            stopControllerActions()
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
                if (emulatorPreview) refreshControllerActionAvailability()
                if (diagnosticsEnabled) logProviderStatus()
                lastPollFrame = frameNanos
            }
            val receiptNow = System.nanoTime()
            if (emulatorPreview) drainControllerActions(receiptNow)
            // trigger() timestamps its path while draining, so sample after those triggers.
            adapter.pollDesktopPreview(System.nanoTime())
            drain()
            if (diagnosticsEnabled) {
                if (pollDue) {
                    logObservedHeadMovement()
                    if (emulatorPreview) logObservedPreviewHands()
                }
            }
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
        controllerActionsPaused = true
        actionQueue.reset()
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
            stopControllerActions()
            stopRequested = false
            return
        }
        stopControllerActions()
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
        if (emulatorPreview) {
            actionQueue.reset()
            controllerActionsPaused = request == PendingControl.PAUSE
        }
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
                                if (emulatorPreview) InputOrigin.DESKTOP else InputOrigin.PICO,
                                TrackingTarget.ALL,
                                DiscontinuityReason.ROUND_RESET,
                            )
                        }
                        pendingControlEnqueued = true
                        if (emulatorPreview && request == PendingControl.ROUND_RESET) DesktopCombatInput.reset()
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
                    if (resumed && emulatorPreview) {
                        actionQueue.reset()
                        DesktopCombatInput.reset()
                        controllerActionsPaused = false
                    }
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

    private fun startControllerActions() {
        if (actionListener != null) stopControllerActions()
        check(actionListener == null) { "controller action listener removal must finish before restarting" }
        val token = actionQueue.start()
        controllerActionsAvailable = false
        controllerActionsPaused = false
        lastControllerActionLog = null
        synchronized(actionProbeGate) {
            actionProbeGeneration = token
            actionProbeLatest = null
            actionProbeLastValues = null
            actionProbeChanges.clear()
            actionProbeDropped = 0L
        }
        lastActionProbeHeartbeat = null
        lastHeadStatus = null
        lastControllerStatus = null
        val listener = ControllerTrackingProvider.ControllerActionListener { action ->
            val receivedAt = System.nanoTime()
            actionQueue.offer(token, action.right.aButtonPressed, receivedAt)
            if (diagnosticsEnabled) synchronized(actionProbeGate) {
                if (actionProbeGeneration == token) {
                    val snapshot = ActionProbeSnapshot(token, action,
                        (actionProbeLatest?.count ?: 0L) + 1L, receivedAt)
                    actionProbeLatest = snapshot
                    if (action != actionProbeLastValues) {
                        actionProbeLastValues = action
                        if (actionProbeChanges.size == ACTION_PROBE_CAPACITY) {
                            actionProbeChanges.removeFirst()
                            actionProbeDropped++
                        }
                        actionProbeChanges.addLast(snapshot)
                    }
                }
            }
        }
        // Retain the listener after partial registration so stop can remove it.
        actionListener = listener
        controllerProvider.addControllerActionListener(listener)
        Log.i(TAG, "Controller preview actions registered; generation=$token")
    }

    private fun stopControllerActions() {
        actionQueue.stop()
        controllerActionsAvailable = false
        controllerActionsPaused = true
        lastControllerActionLog = null
        synchronized(actionProbeGate) {
            actionProbeGeneration = null
            actionProbeLatest = null
            actionProbeLastValues = null
            actionProbeChanges.clear()
            actionProbeDropped = 0L
        }
        lastActionProbeHeartbeat = null
        val listener = actionListener ?: return
        try {
            controllerProvider.removeControllerActionListener(listener)
            actionListener = null
        } catch (error: Exception) {
            Log.w(TAG, "Unable to remove controller action listener", error)
        }
    }

    private fun refreshControllerActionAvailability() {
        controllerActionsAvailable = try {
            controllerProvider.state == DataProvider.State.STARTED &&
                controllerProvider.supportState == DataProvider.SupportState.SUPPORTED
        } catch (error: Exception) {
            Log.w(TAG, "Unable to read controller action availability", error)
            false
        }
        if (!controllerActionsAvailable) actionQueue.reset()
    }

    private fun drainControllerActions(nowNanos: Long) {
        val usable = active && observedReady && controllerActionsAvailable && !controllerActionsPaused &&
            pendingControl == null && !pendingControlRecovery && DesktopCombatInput.enabled
        val batch = actionQueue.drain(nowNanos, usable)
        if (diagnosticsEnabled) {
            for (observation in batch.changes) {
                val identity = Triple(observation.generation, observation.rightA, usable)
                if (identity != lastControllerActionLog) {
                    lastControllerActionLog = identity
                    Log.i(TAG, "Controller action generation=${observation.generation}, rightA=${observation.rightA}, " +
                        "callbackCount=${observation.count}, receivedAtNanos=${observation.receivedAtNanos}, usable=$usable")
                }
            }
            if (batch.droppedChanges > 0L) Log.w(TAG, "Controller action gap; droppedChanges=${batch.droppedChanges}")
            logControllerActionProbe(nowNanos, usable)
        }
        for (press in batch.presses) {
            DesktopCombatInput.trigger(DesktopCombatAction.SLASH)
            Log.i(TAG, "Controller rightA rising edge -> DESKTOP SLASH; generation=${press.generation}, " +
                "callbackCount=${press.count}, receivedAtNanos=${press.receivedAtNanos}")
        }
    }

    private fun logControllerActionProbe(nowNanos: Long, usable: Boolean) {
        val (changes, latest, dropped) = synchronized(actionProbeGate) {
            val result = Triple(actionProbeChanges.toList(), actionProbeLatest, actionProbeDropped)
            actionProbeChanges.clear()
            actionProbeDropped = 0L
            result
        }
        for (snapshot in changes) {
            Log.i(ACTION_PROBE_TAG, "snapshot generation=${snapshot.generation} count=${snapshot.count} " +
                "receivedAtNanos=${snapshot.receivedAtNanos} " +
                "left=${snapshot.values.left} right=${snapshot.values.right}")
        }
        if (dropped > 0L) Log.w(ACTION_PROBE_TAG, "snapshot gap dropped=$dropped")
        val previous = lastActionProbeHeartbeat
        if (previous == null || nowNanos < previous || nowNanos - previous >= ACTION_PROBE_HEARTBEAT_NANOS) {
            lastActionProbeHeartbeat = nowNanos
            Log.i(ACTION_PROBE_TAG, "heartbeat pid=${Process.myPid()} nowNanos=$nowNanos " +
                "generation=${latest?.generation} callbackCount=${latest?.count ?: 0L} " +
                "lastReceiptNanos=${latest?.receivedAtNanos} available=$controllerActionsAvailable " +
                "paused=$controllerActionsPaused observedReady=$observedReady usable=$usable")
        }
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
        if (diagnosticsEnabled && emulatorPreview && accepted && event is TrackingEvent.Controllers) {
            newestControllerObservation = event
        }
        if (accepted && event is TrackingEvent.Discontinuity) {
            if (emulatorPreview) {
                actionQueue.reset()
                DesktopCombatInput.reset()
                if (event.reason == DiscontinuityReason.ROUND_RESET) controllerActionsPaused = false
                else if (observedReady || event.reason == DiscontinuityReason.USER_PAUSED) controllerActionsPaused = true
            }
            Log.i(TAG, "Tracking discontinuity: target=${event.target}, reason=${event.reason}")
        }
        if (accepted && event is TrackingEvent.Head && !sawHead) {
            sawHead = true
            Log.i(TAG, "First head pose observed; origin=${event.stamp.origin}")
        }
        if (accepted && event is TrackingEvent.Controllers && !sawControllers) {
            sawControllers = true
            Log.i(TAG, "First controller snapshot observed; left=${event.left != null}, right=${event.right != null}, origin=${event.stamp.origin}, synthetic=$emulatorPreview")
        }
        if (snapshot.hasRequiredObservations != observedReady) {
            if (emulatorPreview && !snapshot.hasRequiredObservations) {
                actionQueue.reset()
                if (event !is TrackingEvent.Discontinuity || event.reason != DiscontinuityReason.ROUND_RESET) {
                    controllerActionsPaused = true
                }
            }
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

    private fun logObservedPreviewHands() {
        val observation = newestControllerObservation ?: return
        val poses = observation.left to observation.right
        if (poses == lastLoggedControllerPoses) return
        lastLoggedControllerPoses = poses
        Log.i(
            TAG,
            "Hand observation source=HMD_DERIVED, synthetic=true, origin=${observation.stamp.origin}, " +
                "sequence=${observation.stamp.sequence}, receivedAtNanos=${observation.stamp.receivedAtNanos}, " +
                "left=${observation.left}, right=${observation.right}",
        )
    }
}

@Composable
fun ObserveTracking(
    onEvent: (TrackingEvent, Boolean, TrackingSnapshot) -> Unit,
    emulatorPreview: Boolean = false,
    onControlsChanged: (TrackingControls?) -> Unit = {},
    onResumeRequested: (Long) -> Boolean = { false },
    onTick: (Long) -> Unit = {},
) {
    val lifecycleOwner = LocalLifecycleOwner.current
    val context = LocalContext.current
    val diagnosticsEnabled = (context.applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0 && Build.HARDWARE == "ranchu"
    val previewEnabled = emulatorPreview && diagnosticsEnabled
    val currentOnEvent = rememberUpdatedState(onEvent)
    val currentOnControlsChanged = rememberUpdatedState(onControlsChanged)
    val currentOnResumeRequested = rememberUpdatedState(onResumeRequested)
    val currentOnTick = rememberUpdatedState(onTick)
    val session = remember(diagnosticsEnabled, previewEnabled) {
        TrackingSession(
            diagnosticsEnabled,
            previewEnabled,
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
