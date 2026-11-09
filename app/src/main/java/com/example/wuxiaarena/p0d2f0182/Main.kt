package com.example.wuxiaarena.p0d2f0182

import androidx.compose.runtime.remember
import com.example.wuxiaarena.p0d2f0182.content.HomeStage
import com.example.wuxiaarena.p0d2f0182.runtime.ObserveTracking
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaSession
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.foundation.dsl.DefaultStage
import com.pico.spatial.ui.foundation.dsl.SpatialAppScope

fun mainApp(scope: SpatialAppScope) =
    with(scope) {
        DefaultStage {
            PicoTheme {
                val arena = remember { ArenaSession() }
                ObserveTracking(onEvent = arena::onTrackingEvent, emulatorPreview = true)
                HomeStage(
                    onEnemyGeometry = arena::setEnemyGeometry,
                    onPlayerHandPresenter = arena::setPlayerHandPresenter,
                )
            }
        }
    }
