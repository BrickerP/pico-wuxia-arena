package com.example.wuxiaarena.p0d2f0182.runtime

import android.content.pm.ApplicationInfo
import android.os.Build
import android.util.Log
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.example.wuxiaarena.core.input.TrackingControlOverflowException
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingSnapshot
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
private const val ACTION_DIAGNOSTIC_CAPACITY = 64

private class TrackingSession(private val diagnosticsEnabled: Boolean) {
    private val buffer = TrackingEventBuffer(BUFFER_CAPACITY)
    private val headProvider = HMDTrackingProvider()
    private val controllerProvider = ControllerTrackingProvider()
    private val adapter = PicoTrackingAdapter(buffer, headProvider, controllerProvider)
    private val processor = TrackingProcessor()
    private var attempted = false
    private var active = false
    private var lastPollFrame: Long? = null
    private var observedReady = false
    private var sawHead = false
    private var sawControllers = false
    private var reportedFailure: Throwable? = null
    private var pendingControlRecovery = false
    private val actionGate = Any()
    private val actionChanges = ArrayDeque<ActionObservation>()
    private var actionListener: ControllerTrackingProvider.ControllerActionListener? = null
    private var actionGeneration = 0L
    private var acceptingActions = false
    private var actionCallbacks = 0L
    private var droppedActionChanges = 0L
    private var lastActionValues: ActionValues? = null
    private var lastHeadStatus: Pair<DataProvider.State, DataProvider.SupportState>? = null
    private var lastControllerStatus: Pair<DataProvider.State, DataProvider.SupportState>? = null
    private var newestHeadObservation: TrackingEvent.Head? = null
    private var lastLoggedHeadPose: ObservedPose? = null

    private data class ActionValues(
        val leftX: Float,
        val leftY: Float,
        val rightX: Float,
        val rightY: Float,
        val rightA: Boolean,
    )

    private data class ActionObservation(val values: ActionValues, val count: Long, val receivedAtNanos: Long)

    fun start() {
        if (active) return
        if (attempted) stop()
        if (attempted) return
        attempted = true
        try {
            if (diagnosticsEnabled) {
                try {
                    startActionDiagnostics()
                } catch (error: Exception) {
                    Log.w(TAG, "Unable to register controller action diagnostics", error)
                    stopActionDiagnostics()
                }
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
        } catch (error: Exception) {
            if (diagnosticsEnabled) {
                Log.i(TAG, "Provider start interrupted head=${adapter.lastHmdStartResult}, controllers=${adapter.lastControllerStartResult}, receivedAtNanos=${System.nanoTime()}")
                logProviderStatus()
                stopActionDiagnostics()
            }
            Log.e(TAG, "Unable to start tracking", error)
        }
    }

    fun onFrame(frameNanos: Long) {
        if (!active) return
        try {
            val previous = lastPollFrame
            val pollDue = previous == null || frameNanos < previous || frameNanos - previous >= STATUS_POLL_NANOS
            if (pollDue) {
                adapter.pollAvailability()
                if (diagnosticsEnabled) logProviderStatus()
                lastPollFrame = frameNanos
            }
            drain()
            if (diagnosticsEnabled) {
                drainActionDiagnostics()
                if (pollDue) logObservedHeadMovement()
            }
            val failure = adapter.lastProviderFailure
            if (failure != null && failure.cause !== reportedFailure) {
                reportedFailure = failure.cause
                pendingControlRecovery = failure.cause is TrackingControlOverflowException
                Log.w(TAG, "Tracking provider reported ${failure.target}", failure.cause)
            }
            if (pendingControlRecovery && adapter.recoverControlOverflow()) {
                pendingControlRecovery = false
                drain()
            }
        } catch (error: Exception) {
            Log.e(TAG, "Tracking update failed", error)
            stop()
        }
    }

    fun stop() {
        if (!attempted) {
            if (diagnosticsEnabled) stopActionDiagnostics()
            return
        }
        active = false
        if (diagnosticsEnabled) stopActionDiagnostics()
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
                drain()
                if (error is TrackingControlOverflowException) {
                    try {
                        adapter.recoverControlOverflow()
                    } catch (recoveryError: Exception) {
                        error.addSuppressed(recoveryError)
                    }
                }
            }
        }
        drain()
        if (diagnosticsEnabled) logProviderStatus()
        if (stopped) {
            attempted = false
            Log.i(TAG, "Tracking providers stopped")
        } else {
            Log.e(TAG, "Unable to stop tracking cleanly", failure)
        }
    }

    private fun drain() {
        val batch = buffer.drain()
        if (batch.droppedEvents > 0) Log.w(TAG, "Tracking queue dropped ${batch.droppedEvents} observations")
        processor.process(batch, ::onEvent)
    }

    private fun startActionDiagnostics() {
        if (actionListener != null) stopActionDiagnostics()
        check(actionListener == null) { "controller action listener removal must finish before restarting diagnostics" }
        val token = synchronized(actionGate) {
            actionGeneration++
            acceptingActions = true
            actionCallbacks = 0
            droppedActionChanges = 0
            lastActionValues = null
            actionChanges.clear()
            actionGeneration
        }
        lastHeadStatus = null
        lastControllerStatus = null
        val listener = ControllerTrackingProvider.ControllerActionListener { action ->
            synchronized(actionGate) {
                if (!acceptingActions || actionGeneration != token) return@ControllerActionListener
                actionCallbacks++
                val values = ActionValues(
                    action.left.thumbstickValue.x, action.left.thumbstickValue.y,
                    action.right.thumbstickValue.x, action.right.thumbstickValue.y,
                    action.right.aButtonPressed,
                )
                if (values != lastActionValues) {
                    lastActionValues = values
                    if (actionChanges.size < ACTION_DIAGNOSTIC_CAPACITY) {
                        actionChanges.addLast(ActionObservation(values, actionCallbacks, System.nanoTime()))
                    } else {
                        droppedActionChanges++
                    }
                }
            }
        }
        // Keep the reference even if SDK registration fails partway, for paired cleanup.
        actionListener = listener
        controllerProvider.addControllerActionListener(listener)
        Log.i(TAG, "Controller action diagnostics registered; callbackCount=0, receivedAtNanos=${System.nanoTime()}")
    }

    private fun stopActionDiagnostics() {
        val listener = actionListener ?: return
        synchronized(actionGate) {
            acceptingActions = false
            actionGeneration++
        }
        try {
            controllerProvider.removeControllerActionListener(listener)
            actionListener = null
        } catch (error: Exception) {
            Log.w(TAG, "Unable to remove controller action diagnostic listener", error)
        }
        drainActionDiagnostics()
        val count = synchronized(actionGate) { actionCallbacks }
        Log.i(TAG, "Controller action diagnostics stopped; callbackCount=$count, receivedAtNanos=${System.nanoTime()}")
    }

    private fun drainActionDiagnostics() {
        val (changes, dropped) = synchronized(actionGate) {
            val result = actionChanges.toList() to droppedActionChanges
            actionChanges.clear()
            droppedActionChanges = 0
            result
        }
        for (observation in changes) {
            val values = observation.values
            Log.i(TAG, "Controller action left=(${values.leftX},${values.leftY}), right=(${values.rightX},${values.rightY}), rightA=${values.rightA}, callbackCount=${observation.count}, receivedAtNanos=${observation.receivedAtNanos}")
        }
        if (dropped > 0) Log.w(TAG, "Controller action diagnostic gap; droppedChanges=$dropped, receivedAtNanos=${System.nanoTime()}")
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
            Log.i(TAG, "First head pose observed")
        }
        if (accepted && event is TrackingEvent.Controllers && !sawControllers) {
            sawControllers = true
            Log.i(TAG, "First controller snapshot observed; left=${event.left != null}, right=${event.right != null}")
        }
        if (snapshot.hasRequiredObservations != observedReady) {
            observedReady = snapshot.hasRequiredObservations
            Log.i(TAG, "Required observations present=$observedReady; hardware tracking quality remains unknown")
        }
    }

    private fun logObservedHeadMovement() {
        val observation = newestHeadObservation ?: return
        if (observation.pose == lastLoggedHeadPose) return
        lastLoggedHeadPose = observation.pose
        Log.i(
            TAG,
            "Head observation sequence=${observation.stamp.sequence}, " +
                "receivedAtNanos=${observation.stamp.receivedAtNanos}, " +
                "position=${observation.pose?.position}, rotation=${observation.pose?.rotation}",
        )
    }
}

@Composable
fun ObserveTracking() {
    val lifecycleOwner = LocalLifecycleOwner.current
    val context = LocalContext.current
    val diagnosticsEnabled = (context.applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0 && Build.HARDWARE == "ranchu"
    val session = remember(diagnosticsEnabled) { TrackingSession(diagnosticsEnabled) }

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
