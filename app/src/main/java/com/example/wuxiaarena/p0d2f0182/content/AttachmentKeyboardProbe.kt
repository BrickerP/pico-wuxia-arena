package com.example.wuxiaarena.p0d2f0182.content

import android.content.pm.ApplicationInfo
import android.os.Build
import android.util.Log
import android.view.View
import android.view.ViewTreeObserver
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput

/** Temporary passive probe on the existing attachment's own Compose input owner. */
@Composable
internal fun Modifier.attachmentKeyboardProbe(label: String): Modifier {
    val context = LocalContext.current
    val debugEmulator = (context.applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0 &&
        Build.HARDWARE == "ranchu"
    if (!debugEmulator) return this
    val view = LocalView.current
    DisposableEffect(view, label) {
        val observer = view.viewTreeObserver
        val listener = ViewTreeObserver.OnWindowFocusChangeListener { focused ->
            if (DesktopCombatInput.enabled) {
                Log.i(KEY_PROBE_TAG, "owner label=$label windowFocusChanged=$focused ${ownerInfo(view)}")
            }
        }
        observer.addOnWindowFocusChangeListener(listener)
        if (DesktopCombatInput.enabled) Log.i(KEY_PROBE_TAG, "owner label=$label attached=${view.isAttachedToWindow} ${ownerInfo(view)}")
        onDispose {
            if (observer.isAlive) observer.removeOnWindowFocusChangeListener(listener)
        }
    }
    return onPreviewKeyEvent { event ->
        if (DesktopCombatInput.enabled) {
            val native = event.nativeKeyEvent
            Log.i(KEY_PROBE_TAG, "key label=$label code=${native.keyCode} action=${native.action} " +
                "repeat=${native.repeatCount} source=${native.source} deviceId=${native.deviceId} ${ownerInfo(view)}")
        }
        false
    }
}

private const val KEY_PROBE_TAG = "ArenaAttachmentKeys"

private fun ownerInfo(view: View): String =
    "view=${view.javaClass.simpleName} displayId=${view.display?.displayId} " +
        "hasFocus=${view.hasFocus()} hasWindowFocus=${view.hasWindowFocus()} windowToken=${view.windowToken}"
