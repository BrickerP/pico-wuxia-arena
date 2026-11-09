package com.example.wuxiaarena.p0d2f0182

import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import com.example.wuxiaarena.p0d2f0182.content.ArenaControlPanel
import com.example.wuxiaarena.p0d2f0182.content.ArenaStatusPanel
import com.example.wuxiaarena.p0d2f0182.content.HomeStage
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaPresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ObserveTracking
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaSession
import com.example.wuxiaarena.p0d2f0182.runtime.InputControlResult
import com.example.wuxiaarena.p0d2f0182.runtime.TrackingControls
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.foundation.dsl.DefaultStage
import com.pico.spatial.ui.foundation.dsl.SpatialAppScope

private enum class PendingControlKind { PAUSE, RESTART }

private data class PendingControlRequest(
    val kind: PendingControlKind,
    val roundGeneration: Long,
)

fun mainApp(scope: SpatialAppScope) =
    with(scope) {
        DefaultStage {
            PicoTheme {
                val arena = remember { ArenaSession() }
                val viewState = remember { mutableStateOf(arena.viewState) }
                val trackingControls = remember { mutableStateOf<TrackingControls?>(null) }
                val enemyPresenter = remember { mutableStateOf<ArenaPresenter?>(null) }
                val pendingControl = remember { mutableStateOf<PendingControlRequest?>(null) }

                DisposableEffect(arena) {
                    arena.setArenaPresenter { state, events ->
                        val previous = viewState.value
                        // Animation receives every clock sample. HUD only observes its visible fields.
                        val hudComparable = state.copy(
                            simulationNanos = previous.simulationNanos,
                            phaseElapsedNanos = previous.phaseElapsedNanos,
                            phaseRemainingNanos = previous.phaseRemainingNanos,
                        )
                        if (hudComparable != previous) viewState.value = state
                        val pending = pendingControl.value
                        val completed = when (pending?.kind) {
                            PendingControlKind.PAUSE -> state.pauseReason != null
                            PendingControlKind.RESTART -> state.roundGeneration != pending.roundGeneration
                            null -> false
                        }
                        if (completed) pendingControl.value = null
                        enemyPresenter.value?.invoke(state, events)
                    }
                    onDispose { arena.setArenaPresenter(null) }
                }

                ObserveTracking(
                    onEvent = arena::onTrackingEvent,
                    emulatorPreview = true,
                    onControlsChanged = { controls ->
                        trackingControls.value = controls
                        if (controls == null) pendingControl.value = null
                    },
                    onResumeRequested = arena::confirmResume,
                    onTick = arena::onTick,
                )
                HomeStage(
                    onEnemyGeometry = arena::setEnemyGeometry,
                    onPlayerHandPresenter = arena::setPlayerHandPresenter,
                    onEnemyPresenter = { presenter ->
                        enemyPresenter.value = presenter
                        presenter?.invoke(arena.viewState, emptyList())
                    },
                    controlsPanel = {
                        ArenaControlPanel(
                            state = viewState.value,
                            controlsAvailable = trackingControls.value != null,
                            controlPending = pendingControl.value != null,
                            onStart = { arena.startTrial() },
                            onPause = {
                                val round = viewState.value.roundGeneration
                                val result = trackingControls.value?.pause()
                                pendingControl.value = if (result == InputControlResult.PENDING) {
                                    PendingControlRequest(PendingControlKind.PAUSE, round)
                                } else {
                                    null
                                }
                            },
                            onResume = {
                                viewState.value.pauseId?.let { trackingControls.value?.resume(it) }
                            },
                            onRestart = {
                                val round = viewState.value.roundGeneration
                                val result = trackingControls.value?.resetRound()
                                pendingControl.value = if (result == InputControlResult.PENDING) {
                                    PendingControlRequest(PendingControlKind.RESTART, round)
                                } else {
                                    null
                                }
                            },
                        )
                    },
                    statusPanel = { ArenaStatusPanel(viewState.value) },
                )
            }
        }
    }
