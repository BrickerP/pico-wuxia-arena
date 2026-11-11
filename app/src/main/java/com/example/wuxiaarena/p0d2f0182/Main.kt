package com.example.wuxiaarena.p0d2f0182

import android.content.Context
import android.util.Log
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.platform.LocalContext
import com.example.wuxiaarena.p0d2f0182.content.ArenaControlPanel
import com.example.wuxiaarena.p0d2f0182.content.ArenaStatusPanel
import com.example.wuxiaarena.p0d2f0182.content.HomeStage
import com.example.wuxiaarena.p0d2f0182.content.arenaControlPanelHeightDp
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaPresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ObserveTracking
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaSession
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedbackProfile
import com.example.wuxiaarena.p0d2f0182.runtime.shouldPublishHudState
import com.example.wuxiaarena.p0d2f0182.runtime.CombatHapticContacts
import com.example.wuxiaarena.p0d2f0182.runtime.InputControlResult
import com.example.wuxiaarena.p0d2f0182.runtime.TrackingControls
import com.example.wuxiaarena.p0d2f0182.runtime.CombatAudio
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.Hand
import com.pico.spatial.ui.platform.LocalHandControllerHaptic
import com.pico.spatial.ui.platform.HandController
import com.pico.spatial.ui.platform.HandControllerHapticType
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
                val context = LocalContext.current
                val preferences = remember(context) { context.getSharedPreferences("arena_progress", Context.MODE_PRIVATE) }
                val arena = remember { ArenaSession(savedBestScore = preferences.getInt("best_score", 0)) }
                val audio = remember(context) { CombatAudio(context) }
                val haptics = rememberUpdatedState(LocalHandControllerHaptic.current)
                val hapticContacts = remember(arena) { CombatHapticContacts() }
                val viewState = remember { mutableStateOf(arena.viewState) }
                val trackingControls = remember { mutableStateOf<TrackingControls?>(null) }
                val enemyPresenter = remember { mutableStateOf<ArenaPresenter?>(null) }
                val pendingControl = remember { mutableStateOf<PendingControlRequest?>(null) }

                DisposableEffect(arena, audio) {
                    arena.setArenaPresenter { state, events ->
                        val previous = viewState.value
                        if (shouldPublishHudState(previous, state)) viewState.value = state
                        val pending = pendingControl.value
                        val completed = when (pending?.kind) {
                            PendingControlKind.PAUSE -> state.pauseReason != null
                            PendingControlKind.RESTART -> state.roundGeneration != pending.roundGeneration
                            null -> false
                        }
                        if (completed) pendingControl.value = null
                        try {
                            enemyPresenter.value?.invoke(state, events)
                        } catch (error: Exception) {
                            Log.w("ArenaFeedback", "Scene presentation is unavailable", error)
                        }
                        audio.present(state, events)
                        for (cue in hapticContacts.select(state, events)) {
                            val accent = CombatFeedbackProfile.accent(cue.impact)
                            val type = HandControllerHapticType.custom(
                                accent.hapticLevel, accent.hapticFrequency, accent.hapticDurationMillis,
                            )
                            val hand = if (cue.hand == Hand.LEFT) HandController.Left else HandController.Right
                            try {
                                haptics.value.feedback(type, hand)
                            } catch (error: Exception) {
                                Log.w("ArenaFeedback", "Controller impact feedback is unavailable", error)
                            }
                        }
                        if (state.bestScore > preferences.getInt("best_score", 0)) {
                            preferences.edit().putInt("best_score", state.bestScore).apply()
                        }
                    }
                    onDispose {
                        arena.setArenaPresenter(null)
                        audio.close()
                    }
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
                    onOpponentChange = arena::beginOpponentChange,
                    onPlayerHandPresenter = arena::setPlayerHandPresenter,
                    onEnemyPresenter = { presenter ->
                        enemyPresenter.value = presenter
                        presenter?.invoke(arena.viewState, emptyList())
                    },
                    controlsHeightDp = arenaControlPanelHeightDp(
                        viewState.value.result, viewState.value.pauseReason,
                        DesktopCombatInput.enabled || viewState.value.inputOrigin == InputOrigin.DESKTOP,
                    ),
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
                            onDesktopAction = DesktopCombatInput::trigger,
                        )
                    },
                    statusPanel = { ArenaStatusPanel(viewState.value) },
                )
            }
        }
    }
