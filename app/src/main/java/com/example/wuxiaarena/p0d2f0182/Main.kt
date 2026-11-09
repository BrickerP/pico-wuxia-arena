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
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaPresenter
import com.example.wuxiaarena.p0d2f0182.runtime.ObserveTracking
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaSession
import com.example.wuxiaarena.p0d2f0182.runtime.InputControlResult
import com.example.wuxiaarena.p0d2f0182.runtime.TrackingControls
import com.example.wuxiaarena.p0d2f0182.runtime.CombatAudio
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback
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
                val hapticSequence = remember { mutableStateOf<Long?>(null) }
                val viewState = remember { mutableStateOf(arena.viewState) }
                val trackingControls = remember { mutableStateOf<TrackingControls?>(null) }
                val enemyPresenter = remember { mutableStateOf<ArenaPresenter?>(null) }
                val pendingControl = remember { mutableStateOf<PendingControlRequest?>(null) }

                DisposableEffect(arena, audio) {
                    arena.setArenaPresenter { state, events ->
                        val previous = viewState.value
                        // Animation receives every clock sample. HUD only observes its visible fields.
                        val hudComparable = state.copy(
                            simulationNanos = previous.simulationNanos,
                            phaseElapsedNanos = previous.phaseElapsedNanos,
                            phaseRemainingNanos = previous.phaseRemainingNanos,
                            enemyPosition = previous.enemyPosition,
                            enemyYawRadians = previous.enemyYawRadians,
                            hitStop = previous.hitStop,
                            deathElapsedSeconds = previous.deathElapsedSeconds,
                            enemyTravelMeters = previous.enemyTravelMeters,
                            enemyGaitMeters = previous.enemyGaitMeters,
                            enemyMoveDirection = previous.enemyMoveDirection,
                            playerBladeBase = previous.playerBladeBase,
                            playerBladeTip = previous.playerBladeTip,
                            playerHeadPosition = previous.playerHeadPosition,
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
                        audio.present(state)
                        val oldSequence = hapticSequence.value
                        hapticSequence.value = state.feedbackSequence
                        if (oldSequence != null && oldSequence != state.feedbackSequence &&
                            state.inputOrigin == InputOrigin.PICO && state.pauseReason == null && state.feedback != null
                        ) {
                            val type = when (state.feedback) {
                                CombatFeedback.HIT, CombatFeedback.HEADSHOT, CombatFeedback.GUARDED_HIT,
                                CombatFeedback.BLOCK, CombatFeedback.PARRY, CombatFeedback.PLAYER_HIT,
                                CombatFeedback.GUARD_BREAK, CombatFeedback.SKILL, CombatFeedback.EXECUTION -> HandControllerHapticType.Press
                                CombatFeedback.DODGE -> HandControllerHapticType.Step
                                else -> HandControllerHapticType.None
                            }
                            try {
                                haptics.value.feedback(type, if (state.dominantHand == Hand.LEFT) HandController.Left else HandController.Right)
                                if (state.feedback == CombatFeedback.SKILL || state.feedback == CombatFeedback.EXECUTION) {
                                    haptics.value.feedback(type, if (state.dominantHand == Hand.LEFT) HandController.Right else HandController.Left)
                                }
                            } catch (error: Exception) {
                                Log.w("ArenaFeedback", "Controller feedback is unavailable", error)
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
                            onDesktopAction = DesktopCombatInput::trigger,
                        )
                    },
                    statusPanel = { ArenaStatusPanel(viewState.value) },
                )
            }
        }
    }
