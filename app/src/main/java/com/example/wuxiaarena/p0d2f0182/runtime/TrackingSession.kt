package com.example.wuxiaarena.p0d2f0182.runtime

import android.util.Log
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.runtime.withFrameNanos
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.example.wuxiaarena.core.input.TrackingControlOverflowException
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingEventBuffer
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.p0d2f0182.input.PicoTrackingAdapter
import kotlinx.coroutines.isActive
import kotlin.coroutines.coroutineContext

private const val TAG = "ArenaTracking"
// Initial bound for the prototype; device measurements will inform tuning.
private const val BUFFER_CAPACITY = 256
private const val STATUS_POLL_NANOS = 100_000_000L
private const val STOP_ATTEMPTS = 4

private class TrackingSession {
    private val buffer = TrackingEventBuffer(BUFFER_CAPACITY)
    private val adapter = PicoTrackingAdapter(buffer)
    private val processor = TrackingProcessor()
    private var attempted = false
    private var active = false
    private var lastPollFrame: Long? = null
    private var observedReady = false
    private var sawHead = false
    private var sawControllers = false
    private var reportedFailure: Throwable? = null
    private var pendingControlRecovery = false

    fun start() {
        if (active) return
        if (attempted) stop()
        if (attempted) return
        attempted = true
        try {
            adapter.start()
            active = true
            lastPollFrame = null
            sawHead = false
            sawControllers = false
            reportedFailure = null
            pendingControlRecovery = false
            Log.i(TAG, "Tracking provider start requested")
        } catch (error: Exception) {
            Log.e(TAG, "Unable to start tracking", error)
        }
    }

    fun onFrame(frameNanos: Long) {
        if (!active) return
        try {
            val previous = lastPollFrame
            if (previous == null || frameNanos < previous || frameNanos - previous >= STATUS_POLL_NANOS) {
                adapter.pollAvailability()
                lastPollFrame = frameNanos
            }
            drain()
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
        if (!attempted) return
        active = false
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

    private fun onEvent(event: TrackingEvent, accepted: Boolean, snapshot: TrackingSnapshot) {
        if (!accepted) Log.w(TAG, "Rejected tracking observation ${event.stamp.sequence}")
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
}

@Composable
fun ObserveTracking() {
    val lifecycleOwner = LocalLifecycleOwner.current
    val session = remember { TrackingSession() }

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
