package com.example.wuxiaarena.p0d2f0182.platform

import android.app.Application
import com.pico.spatial.ui.foundation.dsl.launch
import com.example.wuxiaarena.p0d2f0182.mainApp

class SpatialApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        launch(::mainApp)
    }
}
