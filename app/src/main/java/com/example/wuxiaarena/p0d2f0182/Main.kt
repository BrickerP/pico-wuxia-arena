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
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedbackProfile
import com.example.wuxiaarena.p0d2f0182.runtime.InputControlResult
import com.example.wuxiaarena.p0d2f0182.runtime.TrackingControls
import com.example.wuxiaarena.p0d2f0182.runtime.CombatAudio
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
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
                val hapticRound = remember { mutableStateOf(-1L) }
                val hapticImpact = remember { mutableStateOf(Long.MIN_VALUE) }
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
                            playerBladeTipSpeed = previous.playerBladeTipSpeed,
                            playerBladeAtRest = previous.playerBladeAtRest,
                            playerMotionGeneration = previous.playerMotionGeneration,
                            playerHeadPosition = previous.playerHeadPosition,
                            enemyRecoilOffset = previous.enemyRecoilOffset,
                        )
                        if (hudComparable != previous) viewState.value = state
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
                        if (hapticRound.value != state.roundGeneration) {
                            hapticRound.value = state.roundGeneration
                            hapticImpact.value = Long.MIN_VALUE
                        }
                        val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
                        for (impact in events.filterIsInstance<CombatImpact>()) {
                            if (impact.id <= hapticImpact.value) continue
                            hapticImpact.value = impact.id
                            if (state.inputOrigin != InputOrigin.PICO || !state.sceneReady ||
                                (!terminal && (!state.inputReady || state.pauseReason != null)) || !impact.strength.isFinite()
                            ) continue
                            val accent = CombatFeedbackProfile.accent(impact)
                            val type = HandControllerHapticType.custom(
                                accent.hapticLevel, accent.hapticFrequency, accent.hapticDurationMillis,
                            )
                            val dominant = if (impact.hand == Hand.LEFT) HandController.Left else HandController.Right
                            try {
                                haptics.value.feedback(type, dominant)
                                if (impact.kind == CombatImpactKind.SKILL || impact.kind == CombatImpactKind.EXECUTION) {
                                    haptics.value.feedback(type, if (impact.hand == Hand.LEFT) HandController.Right else HandController.Left)
                                }
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
