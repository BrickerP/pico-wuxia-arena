package com.example.wuxiaarena.p0d2f0182.content

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.example.wuxiaarena.p0d2f0182.R
import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.pico.spatial.ui.design.Badge
import com.pico.spatial.ui.design.BadgeDefaults
import com.pico.spatial.ui.design.Button
import com.pico.spatial.ui.design.ButtonColors
import com.pico.spatial.ui.design.ButtonDefaults
import com.pico.spatial.ui.design.Chip
import com.pico.spatial.ui.design.ChipsDefaults
import com.pico.spatial.ui.design.CircularProgressDefaults
import com.pico.spatial.ui.design.CircularProgressIndicator
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.design.Text
import com.pico.spatial.ui.design.windows.AlertDialog
import com.pico.spatial.ui.foundation.layout.offset

// App-owned stage-panel colors preserve contrast independently of the system window palette.
private val ArenaPanelSurface = Color(0xFF101010) // design-style: fixed-figma-color .scratch/design-spec.json theme.brandColors
private val ArenaPanelControl = Color(0xFF49443F) // design-style: fixed-figma-color .scratch/design-spec.json theme.brandColors
private val ArenaPanelText = Color(0xFFF6F0E6) // design-style: fixed-figma-color .scratch/design-spec.json theme.brandColors
private val ArenaPanelSecondary = Color(0xFFD3CDC4) // design-style: fixed-figma-color .scratch/design-spec.json theme.brandColors

@Composable
internal fun ArenaControlPanel(
    state: ArenaViewState,
    controlsAvailable: Boolean,
    controlPending: Boolean,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onRestart: () -> Unit,
) {
    PicoTheme {
        ArenaControlPanelContent(
            state = state,
            controlsAvailable = controlsAvailable,
            controlPending = controlPending,
            onStart = onStart,
            onPause = onPause,
            onResume = onResume,
            onRestart = onRestart,
        )
    }
}

@Composable
private fun ArenaControlPanelContent(
    state: ArenaViewState,
    controlsAvailable: Boolean,
    controlPending: Boolean,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onRestart: () -> Unit,
) {
    var showRestartConfirmation by rememberSaveable { mutableStateOf(false) }
    val controlsEnabled = controlsAvailable && !controlPending
    val isDefeated = state.phase == EnemyPhase.DEAD
    val panelButtonColors = ButtonDefaults.buttonColors(
        containerColor = ArenaPanelControl,
        contentColor = ArenaPanelText,
    )

    Box(
        modifier = Modifier
            .size(width = 360.dp, height = 176.dp)
            .clip(RoundedCornerShape(32.dp))
            // design-style: design-surface control-surface
            .background(ArenaPanelSurface),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = stringResource(R.string.arena_control_title),
                style = PicoTheme.typography.titleLarge,
                color = ArenaPanelSecondary,
                maxLines = 1,
            )
            Text(
                text = controlStateLabel(state),
                style = PicoTheme.typography.bodyLarge,
                color = ArenaPanelText,
                maxLines = 1,
            )
            Text(
                text = if (controlPending) {
                    stringResource(R.string.arena_control_processing)
                } else {
                    inputSummary(state)
                },
                style = PicoTheme.typography.labelLarge,
                color = ArenaPanelSecondary,
                maxLines = 1,
            )
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                when {
                    isDefeated -> {
                        Button(
                            onClick = { showRestartConfirmation = true },
                            enabled = controlsEnabled,
                            size = ButtonDefaults.Regular,
                            colors = panelButtonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_retry))
                        }
                    }

                    state.pauseReason != null -> {
                        Button(
                            onClick = onResume,
                            enabled = controlsEnabled && state.pauseId != null && state.resumeReady,
                            size = ButtonDefaults.Regular,
                            colors = panelButtonColors,
                        ) {
                            Text(
                                text = when {
                                    state.resumeReady -> stringResource(R.string.arena_action_resume)
                                    state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> {
                                        stringResource(R.string.arena_action_wait_tracking)
                                    }
                                    else -> stringResource(R.string.arena_action_wait_ready)
                                },
                            )
                        }
                        RestartButton(
                            enabled = controlsEnabled,
                            colors = panelButtonColors,
                            onClick = { showRestartConfirmation = true },
                        )
                    }

                    !state.trialStarted -> {
                        Button(
                            onClick = onStart,
                            enabled = controlsEnabled && state.sceneReady && state.inputReady,
                            size = ButtonDefaults.Regular,
                            colors = panelButtonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_start))
                        }
                    }

                    else -> {
                        Button(
                            onClick = onPause,
                            enabled = controlsEnabled,
                            size = ButtonDefaults.Regular,
                            colors = panelButtonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_pause))
                        }
                        RestartButton(
                            enabled = controlsEnabled,
                            colors = panelButtonColors,
                            onClick = { showRestartConfirmation = true },
                        )
                    }
                }
            }
        }
    }

    if (showRestartConfirmation) {
        RestartConfirmationDialog(
            defeated = isDefeated,
            confirmEnabled = controlsEnabled,
            onDismiss = { showRestartConfirmation = false },
            onConfirm = {
                showRestartConfirmation = false
                onRestart()
            },
        )
    }
}

@Composable
internal fun ArenaStatusPanel(state: ArenaViewState) {
    PicoTheme {
        ArenaStatusPanelContent(state = state)
    }
}

@Composable
private fun ArenaStatusPanelContent(state: ArenaViewState) {
    val healthFraction = if (state.initialHealth > 0) {
        (state.health.toFloat() / state.initialHealth.toFloat()).coerceIn(0f, 1f)
    } else {
        0f
    }

    Box(
        modifier = Modifier
            .size(width = 440.dp, height = 156.dp)
            .clip(RoundedCornerShape(32.dp))
            // design-style: design-surface status-surface
            .background(ArenaPanelSurface),
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = stringResource(R.string.arena_status_title),
                    style = PicoTheme.typography.titleLarge,
                    color = ArenaPanelSecondary,
                    maxLines = 1,
                )
                Chip(
                    label = {
                        Text(text = phaseLabel(state), color = ArenaPanelText)
                    },
                    onClick = {},
                    enabled = false,
                    chipSize = ChipsDefaults.Small,
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    CircularProgressIndicator(
                        progress = { healthFraction },
                        progressSize = CircularProgressDefaults.Regular,
                    )
                    Text(
                        text = stringResource(
                            R.string.arena_health_format,
                            state.health,
                            state.initialHealth,
                        ),
                        style = PicoTheme.typography.labelLarge,
                        color = ArenaPanelText,
                        maxLines = 1,
                    )
                }
                Text(
                    text = stringResource(
                        if (state.guarding) R.string.arena_guard_active else R.string.arena_guard_inactive,
                    ),
                    style = PicoTheme.typography.labelLarge,
                    color = ArenaPanelSecondary,
                    maxLines = 1,
                )
                AttackDirectionSeal(direction = state.attackDirection)
            }
            Text(
                text = combatStatusLabel(state),
                style = PicoTheme.typography.labelLarge,
                color = ArenaPanelSecondary,
                maxLines = 1,
            )
        }
    }
}

@Composable
private fun RestartButton(
    enabled: Boolean,
    colors: ButtonColors,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        size = ButtonDefaults.Small,
        colors = colors,
    ) {
        Text(text = stringResource(R.string.arena_action_restart))
    }
}

@Composable
private fun RestartConfirmationDialog(
    defeated: Boolean,
    confirmEnabled: Boolean,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = stringResource(
                    if (defeated) R.string.arena_restart_defeated_title else R.string.arena_restart_title,
                ),
            )
        },
        content = {
            Text(text = stringResource(R.string.arena_restart_body))
        },
        buttons = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
            ) {
                Button(
                    modifier = Modifier.weight(1f),
                    onClick = onDismiss,
                ) {
                    Text(text = stringResource(R.string.arena_restart_cancel))
                }
                Button(
                    modifier = Modifier.weight(1f),
                    onClick = onConfirm,
                    enabled = confirmEnabled,
                ) {
                    Text(
                        text = stringResource(
                            if (defeated) R.string.arena_action_retry else R.string.arena_action_restart,
                        ),
                    )
                }
            }
        },
    )
}

@Composable
private fun AttackDirectionSeal(direction: AttackDirection?) {
    val title = stringResource(
        if (direction == null) R.string.arena_direction_observe else R.string.arena_direction_title,
    )
    val directions = listOf(
        AttackDirection.LEFT to stringResource(R.string.arena_direction_left),
        AttackDirection.OVERHEAD to stringResource(R.string.arena_direction_overhead),
        AttackDirection.RIGHT to stringResource(R.string.arena_direction_right),
    )

    Row(
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = title,
            style = PicoTheme.typography.labelSmall,
            color = ArenaPanelSecondary,
            maxLines = 1,
        )
        directions.forEach { (candidate, label) ->
            val active = direction == candidate
            val contentDescription = if (active) {
                stringResource(R.string.arena_direction_active_description, label)
            } else {
                label
            }
            Badge(
                modifier = Modifier
                    .offset(z = if (active) 12.dp else 0.dp)
                    .size(34.dp)
                    .semantics { this.contentDescription = contentDescription },
                badgeColor = BadgeDefaults.badgeColors(
                    backgroundColor = if (active) {
                        PicoTheme.colorScheme.interaction
                    } else {
                        ArenaPanelControl
                    },
                    contentColor = if (active) {
                        ArenaPanelText
                    } else {
                        ArenaPanelSecondary
                    },
                ),
                badgeSize = BadgeDefaults.badgeSize(width = 34.dp, height = 34.dp),
                radius = 16.dp,
                contentPadding = PaddingValues(0.dp),
            ) {
                Text(
                    text = label,
                    style = PicoTheme.typography.labelMedium,
                    maxLines = 1,
                )
            }
        }
    }
}

@Composable
private fun controlStateLabel(state: ArenaViewState): String = stringResource(
    when {
        !state.sceneReady -> R.string.arena_state_scene_waiting
        state.phase == EnemyPhase.DEAD -> R.string.arena_state_defeated
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION && state.resumeReady -> {
            R.string.arena_state_tracking_resume_ready
        }
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> R.string.arena_state_tracking_lost
        state.pauseReason == PauseReason.USER -> R.string.arena_state_user_paused
        state.trialStarted -> R.string.arena_state_fighting
        else -> R.string.arena_state_not_started
    },
)

@Composable
private fun inputSummary(state: ArenaViewState): String {
    val source = stringResource(
        when (state.inputOrigin) {
            InputOrigin.DESKTOP -> R.string.arena_input_desktop
            InputOrigin.PICO -> R.string.arena_input_pico
            InputOrigin.SYNTHETIC -> R.string.arena_input_synthetic
            null -> R.string.arena_input_unknown
        },
    )
    val readiness = stringResource(
        when {
            state.resumeReady -> R.string.arena_observation_resume_ready
            state.inputReady && state.actionReady -> R.string.arena_observation_ready
            state.inputReady -> R.string.arena_observation_baseline_wait
            else -> R.string.arena_observation_wait
        },
    )
    return stringResource(R.string.arena_input_summary, source, readiness)
}

@Composable
private fun phaseLabel(state: ArenaViewState): String = stringResource(
    when {
        state.pauseReason == PauseReason.USER -> R.string.arena_phase_paused
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION && state.resumeReady -> {
            R.string.arena_phase_confirmation_required
        }
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> R.string.arena_phase_interrupted
        state.phase == EnemyPhase.IDLE -> R.string.arena_phase_idle
        state.phase == EnemyPhase.PREPARING -> R.string.arena_phase_preparing
        state.phase == EnemyPhase.STARTUP -> R.string.arena_phase_startup
        state.phase == EnemyPhase.ACTIVE -> R.string.arena_phase_active
        state.phase == EnemyPhase.RECOVERING -> R.string.arena_phase_recovering
        state.phase == EnemyPhase.HIT -> R.string.arena_phase_hit
        else -> R.string.arena_phase_dead
    },
)

@Composable
private fun combatStatusLabel(state: ArenaViewState): String {
    val status = stringResource(
        when {
            !state.sceneReady -> R.string.arena_status_scene_unavailable
            state.phase == EnemyPhase.DEAD -> R.string.arena_status_round_ended
            state.pauseReason == PauseReason.USER -> R.string.arena_status_clock_paused
            state.pauseReason == PauseReason.TRACKING_INTERRUPTION && state.resumeReady -> {
                R.string.arena_status_resume_confirmation
            }
            state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> R.string.arena_status_tracking_interrupted
            !state.inputReady -> R.string.arena_status_waiting_observations
            state.targetInRange == true -> R.string.arena_status_in_range
            state.targetInRange == false -> R.string.arena_status_out_of_range
            else -> R.string.arena_status_not_started
        },
    )
    val direction = state.attackDirection ?: return status
    val directionLabel = stringResource(
        when (direction) {
            AttackDirection.LEFT -> R.string.arena_direction_left
            AttackDirection.OVERHEAD -> R.string.arena_direction_overhead
            AttackDirection.RIGHT -> R.string.arena_direction_right
        },
    )
    return stringResource(R.string.arena_status_direction_format, directionLabel, status)
}
