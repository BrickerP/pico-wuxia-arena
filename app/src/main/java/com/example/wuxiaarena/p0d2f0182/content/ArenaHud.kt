package com.example.wuxiaarena.p0d2f0182.content

import androidx.compose.foundation.background
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.p0d2f0182.R
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatAction
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaViewState
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.pico.spatial.ui.design.Badge
import com.pico.spatial.ui.design.BadgeDefaults
import com.pico.spatial.ui.design.Button
import com.pico.spatial.ui.design.ButtonColors
import com.pico.spatial.ui.design.ButtonDefaults
import com.pico.spatial.ui.design.LinearProgressDefaults
import com.pico.spatial.ui.design.LinearProgressIndicator
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.design.Text
import com.pico.spatial.ui.design.windows.AlertDialog

// Panel-owned colors keep Stage content readable without changing the system palette.
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
    onDesktopAction: (DesktopCombatAction) -> Unit = {},
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
            onDesktopAction = onDesktopAction,
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
    onDesktopAction: (DesktopCombatAction) -> Unit,
) {
    var showRestartConfirmation by rememberSaveable { mutableStateOf(false) }
    val controlsEnabled = controlsAvailable && !controlPending
    val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
    val desktop = DesktopCombatInput.enabled || state.inputOrigin == InputOrigin.DESKTOP
    val buttonColors = ButtonDefaults.buttonColors(
        containerColor = ArenaPanelControl,
        contentColor = ArenaPanelText,
    )

    Box(
        modifier = Modifier
            .size(width = 400.dp, height = 400.dp)
            .clip(RoundedCornerShape(32.dp))
            // design-style: design-surface control-surface
            .background(ArenaPanelSurface),
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                text = stringResource(R.string.arena_control_title),
                style = PicoTheme.typography.bodyLarge,
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
                text = if (controlPending) stringResource(R.string.arena_control_processing) else inputSummary(state),
                style = PicoTheme.typography.labelSmall,
                color = ArenaPanelSecondary,
                maxLines = 1,
            )
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                when {
                    terminal -> {
                        Button(
                            onClick = onRestart,
                            enabled = controlsEnabled,
                            size = ButtonDefaults.Regular,
                            colors = buttonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_challenge_again))
                        }
                    }
                    state.pauseReason != null -> {
                        Button(
                            onClick = onResume,
                            enabled = controlsEnabled && state.pauseId != null && state.resumeReady,
                            size = ButtonDefaults.Regular,
                            colors = buttonColors,
                        ) {
                            Text(
                                text = stringResource(
                                    if (state.resumeReady) R.string.arena_action_resume else R.string.arena_action_wait_tracking,
                                ),
                            )
                        }
                        RestartButton(controlsEnabled, buttonColors) { showRestartConfirmation = true }
                    }
                    state.result == TrialResult.READY -> {
                        Button(
                            onClick = onStart,
                            enabled = controlsEnabled && state.sceneReady && state.inputReady,
                            size = ButtonDefaults.Regular,
                            colors = buttonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_start))
                        }
                    }
                    else -> {
                        Button(
                            onClick = onPause,
                            enabled = controlsEnabled,
                            size = ButtonDefaults.Regular,
                            colors = buttonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_pause))
                        }
                        RestartButton(controlsEnabled, buttonColors) { showRestartConfirmation = true }
                    }
                }
            }
            Column(
                modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                if (terminal) {
                    MatchSummary(state)
                } else if (desktop) {
                    Text(
                        text = stringResource(R.string.arena_preview_instruction),
                        style = PicoTheme.typography.labelSmall,
                        color = ArenaPanelSecondary,
                        maxLines = 2,
                    )
                } else {
                    Text(
                        text = stringResource(R.string.arena_play_instruction),
                        style = PicoTheme.typography.labelMedium,
                        color = ArenaPanelText,
                        maxLines = 3,
                    )
                    Text(
                        text = stringResource(R.string.arena_skill_instruction),
                        style = PicoTheme.typography.labelSmall,
                        color = ArenaPanelSecondary,
                        maxLines = 2,
                    )
                }
                if (desktop && !terminal) {
                    DesktopActions(
                        state = state,
                        enabled = controlsEnabled && state.pauseReason == null &&
                            state.result == TrialResult.FIGHTING && state.inputReady && state.actionReady,
                        colors = buttonColors,
                        onAction = onDesktopAction,
                    )
                    Text(
                        text = stringResource(R.string.arena_keyboard_help),
                        style = PicoTheme.typography.labelSmall,
                        color = ArenaPanelSecondary,
                        maxLines = 3,
                    )
                }
            }
        }
    }

    if (showRestartConfirmation) {
        RestartConfirmationDialog(
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
private fun MatchSummary(state: ArenaViewState) {
    Text(
        text = stringResource(R.string.arena_settlement_score, state.score, state.bestScore),
        style = PicoTheme.typography.bodyLarge,
        color = ArenaPanelText,
        maxLines = 2,
    )
    Text(
        text = stringResource(
            R.string.arena_settlement_detail,
            state.roundNumber.coerceIn(1, state.roundCount.coerceAtLeast(1)),
            state.roundCount,
            state.playerHealth.coerceAtLeast(0),
        ),
        style = PicoTheme.typography.labelMedium,
        color = ArenaPanelSecondary,
        maxLines = 2,
    )
    Text(
        text = stringResource(
            if (state.result == TrialResult.VICTORY) R.string.arena_victory_detail else R.string.arena_defeat_detail,
        ),
        style = PicoTheme.typography.labelMedium,
        color = ArenaPanelText,
        maxLines = 3,
    )
}

@Composable
private fun DesktopActions(
    state: ArenaViewState,
    enabled: Boolean,
    colors: ButtonColors,
    onAction: (DesktopCombatAction) -> Unit,
) {
    val rows = listOf(
        listOf(
            DesktopCombatAction.SLASH to R.string.arena_preview_slash,
            DesktopCombatAction.THRUST to R.string.arena_preview_thrust,
            DesktopCombatAction.GUARD_OVERHEAD to R.string.arena_preview_guard,
        ),
        listOf(
            DesktopCombatAction.DODGE_LEFT to R.string.arena_preview_dodge,
            DesktopCombatAction.SKILL to R.string.arena_preview_skill,
        ),
    )
    rows.forEach { actions ->
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            actions.forEach { (action, label) ->
                val actionEnabled = enabled && when (action) {
                    DesktopCombatAction.SKILL -> state.focus >= 100 || state.executionAvailable
                    else -> true
                }
                Button(
                    modifier = Modifier.weight(1f),
                    onClick = { onAction(action) },
                    enabled = actionEnabled,
                    colors = colors,
                    size = ButtonDefaults.Small,
                ) {
                    Text(text = stringResource(label), maxLines = 1)
                }
            }
        }
    }
}

@Composable
internal fun ArenaStatusPanel(state: ArenaViewState) {
    PicoTheme {
        Box(
            modifier = Modifier
                .size(width = 500.dp, height = 260.dp)
                .clip(RoundedCornerShape(32.dp))
                // design-style: design-surface status-surface
                .background(ArenaPanelSurface),
        ) {
            Column(
                modifier = Modifier.fillMaxSize().padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = stringResource(R.string.arena_status_title),
                        style = PicoTheme.typography.bodyLarge,
                        color = ArenaPanelSecondary,
                        maxLines = 1,
                    )
                    Text(
                        text = stringResource(
                            R.string.arena_round_time,
                            state.roundNumber,
                            state.roundCount,
                            state.remainingSeconds.coerceAtLeast(0) / 60,
                            state.remainingSeconds.coerceAtLeast(0) % 60,
                        ),
                        style = PicoTheme.typography.labelMedium,
                        color = ArenaPanelText,
                        maxLines = 1,
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    ResourceMeter(
                        label = stringResource(R.string.arena_resource_enemy),
                        value = state.health,
                        maximum = state.initialHealth,
                        color = PicoTheme.colorScheme.interaction,
                        modifier = Modifier.weight(1f),
                    )
                    ResourceMeter(
                        label = stringResource(R.string.arena_resource_player),
                        value = state.playerHealth,
                        maximum = 100,
                        color = PicoTheme.colorScheme.passable,
                        modifier = Modifier.weight(1f),
                    )
                }
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    ResourceMeter(
                        label = stringResource(R.string.arena_resource_stamina),
                        value = state.playerStamina,
                        maximum = 100,
                        color = PicoTheme.colorScheme.alert,
                        modifier = Modifier.weight(1f),
                    )
                    ResourceMeter(
                        label = stringResource(R.string.arena_resource_focus),
                        value = state.focus,
                        maximum = 100,
                        color = PicoTheme.colorScheme.interaction,
                        modifier = Modifier.weight(1f),
                    )
                }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = phaseLabel(state),
                        style = PicoTheme.typography.labelMedium,
                        color = ArenaPanelText,
                        maxLines = 1,
                    )
                    AttackDirectionSeal(state.attackDirection)
                }
                Text(
                    text = feedbackLabel(state),
                    style = PicoTheme.typography.labelMedium,
                    color = ArenaPanelText,
                    maxLines = 1,
                )
                Text(
                    text = stringResource(R.string.arena_score_combo, state.score, state.combo, state.bestScore),
                    style = PicoTheme.typography.labelSmall,
                    color = ArenaPanelSecondary,
                    maxLines = 1,
                )
            }
        }
    }
}

@Composable
private fun ResourceMeter(
    label: String,
    value: Int,
    maximum: Int,
    color: Color,
    modifier: Modifier = Modifier,
) {
    val fraction = if (maximum > 0) (value.toFloat() / maximum).coerceIn(0f, 1f) else 0f
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(3.dp)) {
        Text(
            text = stringResource(R.string.arena_resource_value, label, value.coerceAtLeast(0), maximum.coerceAtLeast(0)),
            style = PicoTheme.typography.labelSmall,
            color = ArenaPanelSecondary,
            maxLines = 1,
        )
        LinearProgressIndicator(
            progress = { fraction },
            modifier = Modifier.fillMaxWidth().height(6.dp),
            colors = LinearProgressDefaults.linearProgressColors(
                indicatorColor = color,
                backgroundColor = ArenaPanelControl,
            ),
            height = LinearProgressDefaults.linearProgressHeight(6.dp),
        )
    }
}

@Composable
private fun RestartButton(enabled: Boolean, colors: ButtonColors, onClick: () -> Unit) {
    Button(onClick = onClick, enabled = enabled, size = ButtonDefaults.Small, colors = colors) {
        Text(text = stringResource(R.string.arena_action_restart))
    }
}

@Composable
private fun RestartConfirmationDialog(
    confirmEnabled: Boolean,
    onDismiss: () -> Unit,
    onConfirm: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(text = stringResource(R.string.arena_restart_title)) },
        content = { Text(text = stringResource(R.string.arena_restart_body)) },
        buttons = {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.CenterHorizontally),
            ) {
                Button(modifier = Modifier.weight(1f), onClick = onDismiss) {
                    Text(text = stringResource(R.string.arena_restart_cancel))
                }
                Button(modifier = Modifier.weight(1f), onClick = onConfirm, enabled = confirmEnabled) {
                    Text(text = stringResource(R.string.arena_action_restart))
                }
            }
        },
    )
}

@Composable
private fun AttackDirectionSeal(direction: AttackDirection?) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(5.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        val directions = listOf(
            AttackDirection.LEFT to stringResource(R.string.arena_direction_left),
            AttackDirection.OVERHEAD to stringResource(R.string.arena_direction_overhead),
            AttackDirection.RIGHT to stringResource(R.string.arena_direction_right),
        )
        directions.forEach { (candidate, label) ->
            val active = direction == candidate
            val description = if (active) stringResource(R.string.arena_direction_active_description, label) else label
            Badge(
                modifier = Modifier.size(30.dp).semantics { contentDescription = description },
                badgeColor = BadgeDefaults.badgeColors(
                    backgroundColor = if (active) PicoTheme.colorScheme.interaction else ArenaPanelControl,
                    contentColor = if (active) ArenaPanelText else ArenaPanelSecondary,
                ),
                badgeSize = BadgeDefaults.badgeSize(width = 30.dp, height = 30.dp),
                radius = 14.dp,
                contentPadding = PaddingValues(0.dp),
            ) {
                Text(text = label, style = PicoTheme.typography.labelSmall, maxLines = 1)
            }
        }
    }
}

@Composable
private fun controlStateLabel(state: ArenaViewState): String {
    val resource = when {
        state.result == TrialResult.VICTORY -> R.string.arena_state_victory
        state.result == TrialResult.DEFEAT -> R.string.arena_state_defeat
        !state.sceneReady -> R.string.arena_state_scene_waiting
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION && state.resumeReady -> R.string.arena_state_tracking_resume_ready
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> R.string.arena_state_tracking_lost
        state.pauseReason == PauseReason.USER -> R.string.arena_state_user_paused
        else -> when (state.result) {
            TrialResult.READY -> R.string.arena_state_not_started
            TrialResult.COUNTDOWN -> R.string.arena_state_countdown
            TrialResult.FIGHTING -> R.string.arena_state_fighting
            TrialResult.ROUND_CLEAR -> R.string.arena_state_round_clear
            TrialResult.VICTORY -> R.string.arena_state_victory
            TrialResult.DEFEAT -> R.string.arena_state_defeat
        }
    }
    return when {
        state.pauseReason != null || !state.sceneReady -> stringResource(resource)
        state.result == TrialResult.COUNTDOWN -> stringResource(resource, state.countdownSeconds.coerceAtLeast(0))
        state.result == TrialResult.ROUND_CLEAR && state.countdownSeconds > 0 -> {
            stringResource(R.string.arena_state_round_clear_countdown, state.countdownSeconds)
        }
        else -> stringResource(resource)
    }
}

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
        state.result == TrialResult.VICTORY -> R.string.arena_state_victory
        state.result == TrialResult.DEFEAT -> R.string.arena_state_defeat
        state.pauseReason == PauseReason.USER -> R.string.arena_phase_paused
        state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> R.string.arena_phase_interrupted
        state.result == TrialResult.COUNTDOWN -> R.string.arena_phase_countdown
        state.result == TrialResult.ROUND_CLEAR -> R.string.arena_phase_round_clear
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
private fun feedbackLabel(state: ArenaViewState): String {
    val feedback = state.feedback
    if (feedback != null) {
        return stringResource(
            when (feedback) {
                CombatFeedback.HIT -> R.string.arena_feedback_hit
                CombatFeedback.HEADSHOT -> R.string.arena_feedback_headshot
                CombatFeedback.GUARDED_HIT -> R.string.arena_feedback_guarded_hit
                CombatFeedback.BLOCK -> R.string.arena_feedback_block
                CombatFeedback.PARRY -> R.string.arena_feedback_parry
                CombatFeedback.DODGE -> R.string.arena_feedback_dodge
                CombatFeedback.PLAYER_HIT -> R.string.arena_feedback_player_hit
                CombatFeedback.GUARD_BREAK -> R.string.arena_feedback_guard_break
                CombatFeedback.SKILL -> R.string.arena_feedback_skill
                CombatFeedback.EXECUTION -> R.string.arena_feedback_execution
                CombatFeedback.LOW_STAMINA -> R.string.arena_feedback_low_stamina
                CombatFeedback.LOW_FOCUS -> R.string.arena_feedback_low_focus
                CombatFeedback.OUT_OF_RANGE -> R.string.arena_feedback_out_of_range
                CombatFeedback.TIMEOUT -> R.string.arena_feedback_timeout
            },
        )
    }
    return stringResource(
        when {
            state.result == TrialResult.VICTORY -> R.string.arena_victory_detail
            state.result == TrialResult.DEFEAT -> R.string.arena_defeat_detail
            state.pauseReason != null -> R.string.arena_status_clock_paused
            !state.inputReady -> R.string.arena_status_waiting_observations
            state.executing -> R.string.arena_status_executing
            state.executionAvailable -> R.string.arena_status_execution_ready
            state.focus >= 100 -> R.string.arena_status_skill_ready
            state.guarding -> R.string.arena_status_enemy_guard
            state.targetInRange == false -> R.string.arena_status_out_of_range
            state.result == TrialResult.COUNTDOWN -> R.string.arena_status_countdown
            state.result == TrialResult.ROUND_CLEAR -> R.string.arena_status_round_transition
            state.result == TrialResult.READY -> R.string.arena_status_not_started
            else -> R.string.arena_status_in_range
        },
    )
}
