package com.example.wuxiaarena.p0d2f0182.platform

import android.content.pm.ApplicationInfo
import android.os.Build
import android.util.Log
import android.view.KeyEvent
import com.pico.spatial.ui.platform.stub.SpatialLaunchActivity

class LaunchActivity : SpatialLaunchActivity() {
    override fun dispatchKeyEvent(event: KeyEvent): Boolean {
        if (Build.HARDWARE == "ranchu" &&
            (applicationInfo.flags and ApplicationInfo.FLAG_DEBUGGABLE) != 0 &&
            event.keyCode == KeyEvent.KEYCODE_W &&
            (event.action == KeyEvent.ACTION_DOWN || event.action == KeyEvent.ACTION_UP)
        ) {
            Log.i(
                "ArenaKeyboard",
                "Android key event action=${event.action} repeatCount=${event.repeatCount} " +
                    "eventTimeUptimeMillis=${event.eventTime} receivedAtNanos=${System.nanoTime()} " +
                    "keyCode=${event.keyCode} deviceId=${event.deviceId} source=${event.source} " +
                    "scanCode=${event.scanCode} flags=${event.flags}",
            )
        }
        return super.dispatchKeyEvent(event)
    }
}
