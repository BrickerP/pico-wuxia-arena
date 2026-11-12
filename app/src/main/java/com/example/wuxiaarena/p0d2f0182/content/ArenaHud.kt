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
import androidx.compose.runtime.key
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import com.example.wuxiaarena.p0d2f0182.ui.ArenaUiPalette
import com.example.wuxiaarena.p0d2f0182.ui.arenaShowsEmulatorGuide
import com.example.wuxiaarena.p0d2f0182.ui.arenaShowsIncomingStrike
import com.example.wuxiaarena.p0d2f0182.ui.arenaShowsCombo
import com.example.wuxiaarena.p0d2f0182.ui.arenaIncomingSealScale
import com.example.wuxiaarena.p0d2f0182.ui.arenaHitFeedbackScale
import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.p0d2f0182.R
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

private val HudTextShadow = Shadow(ArenaUiPalette.inkBlack, Offset(0f, 1f), 3f)

internal fun arenaControlsAreCompact(result: TrialResult, pauseReason: PauseReason?): Boolean =
    pauseReason == null && when (result) {
        TrialResult.COUNTDOWN, TrialResult.FIGHTING, TrialResult.ROUND_CLEAR -> true
        TrialResult.READY, TrialResult.VICTORY, TrialResult.DEFEAT -> false
    }

internal fun arenaControlPanelHeightDp(result: TrialResult, pauseReason: PauseReason?): Int =
    if (arenaControlsAreCompact(result, pauseReason)) 160 else 400

@Composable
internal fun ArenaControlPanel(
    state: ArenaViewState,
    controlsAvailable: Boolean,
    controlPending: Boolean,
    isRanchuHost: Boolean,
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
            isRanchuHost = isRanchuHost,
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
    isRanchuHost: Boolean,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onRestart: () -> Unit,
) {
    var showRestartConfirmation by rememberSaveable { mutableStateOf(false) }
    val controlsEnabled = controlsAvailable && !controlPending
    val terminal = state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT
    val compact = arenaControlsAreCompact(state.result, state.pauseReason)
    val showEmulatorGuide = arenaShowsEmulatorGuide(state.inputOrigin, isRanchuHost)
    val surfaceText = ArenaUiPalette.inkBlack
    val secondaryText = ArenaUiPalette.mutedInk
    val buttonColors = ButtonDefaults.buttonColors(
        containerColor = ArenaUiPalette.cinnabar,
        contentColor = ArenaUiPalette.paperIvory,
    )

    Box(
        modifier = Modifier
            .size(width = 400.dp, height = arenaControlPanelHeightDp(state.result, state.pauseReason).dp),
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(4.dp)
                .then(
                    if (compact) Modifier else Modifier
                        .clip(RoundedCornerShape(8.dp))
                        // design-style: design-surface control-surface
                        .background(ArenaUiPalette.paperIvory),
                )
                .padding(if (compact) 12.dp else 16.dp),
            verticalArrangement = if (compact) Arrangement.spacedBy(8.dp, Alignment.CenterVertically) else Arrangement.spacedBy(8.dp),
        ) {
            if (compact && (state.result != TrialResult.FIGHTING || !state.sceneReady)) {
                Text(
                    text = controlStateLabel(state),
                    style = PicoTheme.typography.titleSmall.copy(fontSize = 20.sp, lineHeight = 24.sp, shadow = HudTextShadow),
                    color = ArenaUiPalette.paperIvory,
                    maxLines = 1,
                )
            }
            if (compact && (controlPending || !state.inputReady)) {
                Text(
                    text = if (controlPending) stringResource(R.string.arena_control_processing) else inputSummary(state),
                    style = PicoTheme.typography.labelSmall.copy(fontSize = 14.sp, lineHeight = 18.sp, shadow = HudTextShadow),
                    color = ArenaUiPalette.paleAsh,
                    maxLines = 1,
                )
            }
            if (!compact) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(modifier = Modifier.weight(1f), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        TrialSeal()
                        Text(
                            text = stringResource(R.string.arena_control_title),
                            modifier = Modifier.weight(1f),
                            style = PicoTheme.typography.titleSmall.copy(
                                fontSize = 28.sp,
                                lineHeight = 34.sp,
                                fontFamily = FontFamily.Serif,
                                fontWeight = FontWeight.SemiBold,
                            ),
                            color = surfaceText,
                            maxLines = 1,
                        )
                    }
                    Text(
                        text = stringResource(R.string.arena_control_round, state.roundNumber, state.roundCount),
                        style = PicoTheme.typography.labelMedium.copy(fontSize = 14.sp, lineHeight = 18.sp),
                        color = secondaryText,
                        maxLines = 1,
                    )
                }
                Text(
                    text = controlStateLabel(state),
                    style = PicoTheme.typography.bodyLarge.copy(fontSize = 24.sp, lineHeight = 28.sp),
                    color = surfaceText,
                    maxLines = 1,
                )
                Text(
                    text = when {
                        controlPending -> stringResource(R.string.arena_control_processing)
                        terminal -> stringResource(R.string.arena_trial_finished)
                        !state.inputReady || state.pauseReason == PauseReason.TRACKING_INTERRUPTION -> inputSummary(state)
                        else -> stringResource(R.string.arena_trial_objective)
                    },
                    style = PicoTheme.typography.labelSmall.copy(fontSize = 14.sp, lineHeight = 18.sp),
                    color = secondaryText,
                    maxLines = 1,
                )
            }
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                if (compact) TrialSeal(compact = true)
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
                            size = ButtonDefaults.Small,
                            colors = buttonColors,
                        ) {
                            Text(text = stringResource(R.string.arena_action_pause))
                        }
                        RestartButton(
                            controlsEnabled,
                            ButtonDefaults.buttonColors(
                                containerColor = ArenaUiPalette.inkVeil,
                                contentColor = ArenaUiPalette.paperIvory,
                            ),
                        ) { showRestartConfirmation = true }
                    }
                }
            }
            if (!compact) {
                if (terminal) {
                    Column(
                        modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()),
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        MatchSummary(state)
                    }
                } else {
                    TechniqueGuide(showEmulatorGuide = showEmulatorGuide, modifier = Modifier.weight(1f).fillMaxWidth())
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
private fun TechniqueGuide(showEmulatorGuide: Boolean, modifier: Modifier = Modifier) {
    val lessons = remember(showEmulatorGuide) {
        if (showEmulatorGuide) {
            listOf(
                R.string.arena_ui_emulator_setup_title to R.string.arena_ui_emulator_setup_detail,
                R.string.arena_ui_emulator_hand_title to R.string.arena_ui_emulator_hand_detail,
                R.string.arena_ui_emulator_motion_title to R.string.arena_ui_emulator_motion_detail,
                R.string.arena_ui_emulator_head_title to R.string.arena_ui_emulator_head_detail,
            )
        } else {
            listOf(
                R.string.arena_technique_strike to R.string.arena_technique_strike_detail,
                R.string.arena_technique_guard to R.string.arena_technique_guard_detail,
                R.string.arena_technique_dodge to R.string.arena_technique_dodge_detail,
                R.string.arena_technique_skill to R.string.arena_technique_skill_detail,
            )
        }
    }
    var selectedLesson by rememberSaveable(showEmulatorGuide) { mutableStateOf(0) }
    val page = selectedLesson.coerceIn(lessons.indices)
    val (title, description) = lessons[page]
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = stringResource(if (showEmulatorGuide) R.string.arena_ui_emulator_guide else R.string.arena_technique_title),
                style = PicoTheme.typography.labelMedium.copy(fontSize = 14.sp, lineHeight = 18.sp),
                color = ArenaUiPalette.mutedInk,
                maxLines = 1,
            )
            Text(
                text = stringResource(title),
                modifier = Modifier.weight(1f),
                style = PicoTheme.typography.titleSmall.copy(fontSize = 20.sp, lineHeight = 24.sp),
                color = ArenaUiPalette.inkBlack,
                maxLines = 1,
            )
            Text(
                text = stringResource(R.string.arena_ui_technique_page, page + 1, lessons.size),
                style = PicoTheme.typography.labelMedium.copy(fontSize = 14.sp, lineHeight = 18.sp),
                color = ArenaUiPalette.mutedInk,
                maxLines = 1,
            )
        }
        // Only the current lesson body scrolls. Start/resume and lesson navigation stay visible.
        // A fresh key also resets a long lesson's scroll position when changing pages.
        key(showEmulatorGuide, page) {
            Column(
                modifier = Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = stringResource(description),
                    style = PicoTheme.typography.bodyMedium.copy(fontSize = 16.sp, lineHeight = 22.sp),
                    color = ArenaUiPalette.inkBlack,
                )

            }
        }
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            val colors = ButtonDefaults.buttonColors(
                containerColor = ArenaUiPalette.cinnabar,
                contentColor = ArenaUiPalette.paperIvory,
            )
            Button(
                onClick = { selectedLesson = (page - 1).coerceAtLeast(0) },
                modifier = Modifier.weight(1f),
                enabled = page > 0,
                size = ButtonDefaults.Small,
                colors = colors,
            ) {
                Text(text = stringResource(R.string.arena_ui_technique_previous))
            }
            Button(
                onClick = { selectedLesson = (page + 1).coerceAtMost(lessons.lastIndex) },
                modifier = Modifier.weight(1f),
                enabled = page < lessons.lastIndex,
                size = ButtonDefaults.Small,
                colors = colors,
            ) {
                Text(text = stringResource(R.string.arena_ui_technique_next))
            }
        }
    }
}

@Composable
private fun MatchSummary(state: ArenaViewState) {
    Text(
        text = stringResource(R.string.arena_ui_score),
        style = PicoTheme.typography.labelMedium.copy(fontSize = 14.sp, lineHeight = 18.sp),
        color = ArenaUiPalette.mutedInk,
    )
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalAlignment = Alignment.Bottom) {
        Text(text = stringResource(R.string.arena_ui_score_value, state.score),
            style = PicoTheme.typography.displaySmall.copy(fontSize = 44.sp, lineHeight = 48.sp,
                fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Serif),
            color = ArenaUiPalette.inkBlack, maxLines = 1)
        Text(text = stringResource(R.string.arena_ui_best, state.bestScore),
            style = PicoTheme.typography.labelMedium.copy(fontSize = 16.sp, lineHeight = 24.sp),
            color = ArenaUiPalette.mutedInk, maxLines = 1)
    }
    Text(
        text = stringResource(R.string.arena_settlement_detail,
            state.roundNumber.coerceIn(1, state.roundCount.coerceAtLeast(1)), state.roundCount,
            state.playerHealth.coerceAtLeast(0)),
        style = PicoTheme.typography.labelMedium.copy(fontSize = 16.sp, lineHeight = 22.sp),
        color = ArenaUiPalette.mutedInk,
        maxLines = 2,
    )
    Text(
        text = stringResource(if (state.result == TrialResult.VICTORY) R.string.arena_victory_detail else R.string.arena_defeat_detail),
        style = PicoTheme.typography.labelMedium.copy(fontSize = 16.sp, lineHeight = 22.sp),
        color = ArenaUiPalette.inkBlack,
        maxLines = 3,
    )
}

@Composable
internal fun ArenaStatusPanel(state: ArenaViewState) {
    PicoTheme {
        // The Attachment remains 500 x 260; its outer region stays transparent.
        Box(modifier = Modifier.size(width = 500.dp, height = 260.dp)) {
            Column(
                modifier = Modifier.fillMaxWidth().padding(4.dp).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = state.enemyName,
                        modifier = Modifier.weight(1f),
                        style = PicoTheme.typography.titleSmall.copy(fontSize = 24.sp, lineHeight = 28.sp, fontFamily = FontFamily.Serif, shadow = HudTextShadow),
                        color = ArenaUiPalette.paperIvory,
                        maxLines = 1,
                    )
                    Text(
                        text = stringResource(R.string.arena_round_time, state.roundNumber, state.roundCount,
                            state.remainingSeconds.coerceAtLeast(0) / 60, state.remainingSeconds.coerceAtLeast(0) % 60),
                        style = PicoTheme.typography.labelLarge.copy(fontSize = 16.sp, lineHeight = 20.sp, shadow = HudTextShadow),
                        color = ArenaUiPalette.paleAsh,
                        maxLines = 1,
                    )
                }
                ResourceMeter(
                    label = stringResource(R.string.arena_ui_enemy_health),
                    value = state.health,
                    maximum = state.initialHealth,
                    color = ArenaUiPalette.ember,
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(
                        text = phaseLabel(state),
                        style = PicoTheme.typography.titleSmall.copy(fontSize = 22.sp, lineHeight = 26.sp, shadow = HudTextShadow),
                        color = if (arenaShowsIncomingStrike(state.result, state.pauseReason, state.inputReady, state.phase))
                            ArenaUiPalette.ember else ArenaUiPalette.paperIvory,
                        maxLines = 1,
                    )
                    if (arenaShowsIncomingStrike(state.result, state.pauseReason, state.inputReady, state.phase)) {
                        AttackDirectionSeal(
                            state.attackDirection,
                            arenaIncomingSealScale(state.phase, state.phaseElapsedNanos,
                                state.attackDirection?.preparationNanos ?: 0L),
                        )
                    }
                }
                if (state.result == TrialResult.FIGHTING && state.pauseReason == null && state.inputReady &&
                    (state.motionReleaseRequired || state.motionCharge.isFinite() && state.motionCharge > 0f)) {
                    MotionChargeHint(state)
                } else {
                    Text(text = phaseHint(state), style = PicoTheme.typography.labelMedium.copy(fontSize = 16.sp, lineHeight = 20.sp, shadow = HudTextShadow),
                        color = ArenaUiPalette.paleAsh, maxLines = 1)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    ResourceMeter(stringResource(R.string.arena_resource_player), state.playerHealth, 100,
                        if (state.playerHealth <= 25) ArenaUiPalette.ember else ArenaUiPalette.paperIvory, Modifier.weight(1f))
                    ResourceMeter(stringResource(R.string.arena_resource_stamina), state.playerStamina, 100,
                        ArenaUiPalette.jade, Modifier.weight(1f))
                    ResourceMeter(stringResource(R.string.arena_resource_focus), state.focus, 100,
                        ArenaUiPalette.antiqueGold, Modifier.weight(1f))
                }
                val feedbackText = feedbackLabel(state)
                val showCombo = arenaShowsCombo(state.result, state.combo)
                if (feedbackText != null || showCombo) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        if (feedbackText != null) {
                            Text(
                                text = feedbackText,
                                modifier = Modifier.weight(1f).graphicsLayer {
                                    val emphasis = if (state.result == TrialResult.FIGHTING &&
                                        state.pauseReason == null && state.inputReady) {
                                        arenaHitFeedbackScale(state.phase, state.phaseElapsedNanos, state.feedback)
                                    } else 1f
                                    scaleX = emphasis
                                    scaleY = emphasis
                                },
                                style = PicoTheme.typography.labelLarge.copy(fontSize = 16.sp, lineHeight = 20.sp, shadow = HudTextShadow),
                                color = when (state.feedback) {
                                    CombatFeedback.PARRY, CombatFeedback.EXECUTION, CombatFeedback.HEADSHOT -> ArenaUiPalette.antiqueGold
                                    CombatFeedback.PLAYER_HIT, CombatFeedback.GUARD_BREAK, CombatFeedback.LOW_STAMINA -> ArenaUiPalette.ember
                                    else -> ArenaUiPalette.paperIvory
                                },
                                maxLines = 2,
                            )
                        } else {
                            Box(modifier = Modifier.weight(1f))
                        }
                        if (showCombo) {
                            Text(
                                text = stringResource(R.string.arena_combo, state.combo),
                                style = PicoTheme.typography.labelMedium.copy(fontSize = 16.sp, lineHeight = 20.sp, shadow = HudTextShadow),
                                color = ArenaUiPalette.antiqueGold,
                                maxLines = 1,
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun TrialSeal(compact: Boolean = false) {
    val diameter = if (compact) 28.dp else 40.dp
    Badge(
        modifier = Modifier.size(diameter),
        badgeColor = BadgeDefaults.badgeColors(backgroundColor = ArenaUiPalette.cinnabar, contentColor = ArenaUiPalette.paperIvory),
        badgeSize = BadgeDefaults.badgeSize(width = diameter, height = diameter),
        radius = 3.dp,
        contentPadding = PaddingValues(0.dp),
    ) {
        Text(text = stringResource(R.string.arena_ui_seal),
            style = PicoTheme.typography.titleSmall.copy(fontFamily = FontFamily.Serif, fontSize = if (compact) 18.sp else 24.sp))
    }
}

@Composable
private fun MotionChargeHint(state: ArenaViewState) {
    val progress = state.motionCharge.coerceIn(0f, 1f)
    val label = when {
        state.motionReleaseRequired -> stringResource(R.string.arena_charge_release)
        progress < 1f -> stringResource(R.string.arena_charge_progress, (progress * 100f).toInt())
        state.executionAvailable -> stringResource(R.string.arena_charge_execution)
        state.focus >= 100 -> stringResource(R.string.arena_charge_skill)
        else -> stringResource(R.string.arena_charge_low_focus)
    }
    Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
        Text(
            text = label,
            style = PicoTheme.typography.labelSmall.copy(fontSize = 16.sp, lineHeight = 20.sp, shadow = HudTextShadow),
            color = ArenaUiPalette.paperIvory,
            maxLines = 1,
        )
        if (!state.motionReleaseRequired) {
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier.fillMaxWidth().height(4.dp),
                colors = LinearProgressDefaults.linearProgressColors(
                    indicatorColor = ArenaUiPalette.antiqueGold,
                    backgroundColor = ArenaUiPalette.mutedInk,
                ),
                height = LinearProgressDefaults.linearProgressHeight(4.dp),
            )
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
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = label,
                style = PicoTheme.typography.labelMedium.copy(fontSize = 14.sp, lineHeight = 18.sp, shadow = HudTextShadow),
                color = ArenaUiPalette.paleAsh,
                maxLines = 1,
            )
            Badge(
                badgeColor = BadgeDefaults.badgeColors(
                    backgroundColor = ArenaUiPalette.inkVeil,
                    contentColor = ArenaUiPalette.paperIvory,
                ),
                badgeSize = BadgeDefaults.badgeSize(width = 76.dp, height = 22.dp),
                radius = 3.dp,
                contentPadding = PaddingValues(horizontal = 4.dp),
            ) {
                Text(
                    text = stringResource(R.string.arena_resource_amount, value.coerceAtLeast(0), maximum.coerceAtLeast(0)),
                    style = PicoTheme.typography.labelMedium.copy(fontSize = 14.sp, lineHeight = 18.sp),
                    maxLines = 1,
                )
            }
        }
        LinearProgressIndicator(
            progress = { fraction },
            modifier = Modifier.fillMaxWidth().height(6.dp),
            colors = LinearProgressDefaults.linearProgressColors(
                indicatorColor = color,
                backgroundColor = ArenaUiPalette.mutedInk,
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
private fun AttackDirectionSeal(direction: AttackDirection?, scale: Float) {
    if (direction == null) return
    val label = stringResource(when (direction) {
        AttackDirection.LEFT -> R.string.arena_direction_left
        AttackDirection.OVERHEAD -> R.string.arena_direction_overhead
        AttackDirection.RIGHT -> R.string.arena_direction_right
    })
    val description = stringResource(R.string.arena_direction_active_description, label)
    Badge(
        modifier = Modifier.size(width = 42.dp, height = 34.dp).graphicsLayer { scaleX = scale; scaleY = scale }.semantics { contentDescription = description },
        badgeColor = BadgeDefaults.badgeColors(
            backgroundColor = ArenaUiPalette.cinnabar,
            contentColor = ArenaUiPalette.paperIvory,
        ),
        badgeSize = BadgeDefaults.badgeSize(width = 42.dp, height = 34.dp),
        radius = 3.dp,
        contentPadding = PaddingValues(0.dp),
    ) {
        Text(text = label, style = PicoTheme.typography.labelLarge.copy(fontSize = 20.sp), maxLines = 1)
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
            stringResource(
                if (state.roundNumber >= state.roundCount) R.string.arena_state_final_clear_countdown else R.string.arena_state_round_clear_countdown,
                state.countdownSeconds,
            )
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
        state.executing -> R.string.arena_status_executing
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
private fun phaseHint(state: ArenaViewState): String = stringResource(
    when {
        state.result == TrialResult.VICTORY -> R.string.arena_hint_victory
        state.result == TrialResult.DEFEAT -> R.string.arena_hint_defeat
        state.pauseReason != null -> R.string.arena_hint_paused
        !state.inputReady -> R.string.arena_status_waiting_observations
        state.result == TrialResult.READY -> R.string.arena_hint_ready
        state.result == TrialResult.COUNTDOWN -> R.string.arena_hint_countdown
        state.executing -> R.string.arena_hint_executing
        state.result == TrialResult.ROUND_CLEAR && state.roundNumber >= state.roundCount -> R.string.arena_hint_final_clear
        state.result == TrialResult.ROUND_CLEAR -> R.string.arena_hint_round_clear
        state.phase == EnemyPhase.PREPARING -> R.string.arena_hint_preparing
        state.phase == EnemyPhase.STARTUP -> R.string.arena_hint_startup
        state.phase == EnemyPhase.ACTIVE -> R.string.arena_hint_active
        state.phase == EnemyPhase.RECOVERING -> R.string.arena_hint_recovering
        state.phase == EnemyPhase.HIT && state.hitReaction == HitReaction.PARRIED -> R.string.arena_hint_parried
        state.phase == EnemyPhase.HIT -> R.string.arena_hint_hit
        else -> R.string.arena_hint_idle
    },
)

@Composable
private fun feedbackLabel(state: ArenaViewState): String? {
    val status = when {
        state.result == TrialResult.VICTORY -> R.string.arena_victory_detail
        state.result == TrialResult.DEFEAT && state.feedback == CombatFeedback.TIMEOUT -> R.string.arena_feedback_timeout
        state.result == TrialResult.DEFEAT -> R.string.arena_defeat_detail
        state.pauseReason != null -> R.string.arena_status_clock_paused
        !state.inputReady -> R.string.arena_status_waiting_observations
        state.executing -> R.string.arena_status_executing
        state.result == TrialResult.ROUND_CLEAR && state.roundNumber >= state.roundCount -> R.string.arena_hint_final_clear
        state.result == TrialResult.ROUND_CLEAR -> R.string.arena_status_round_transition
        state.result == TrialResult.COUNTDOWN -> R.string.arena_status_countdown
        state.result == TrialResult.READY -> R.string.arena_status_not_started
        else -> null
    }
    if (status != null) return stringResource(status)
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
    val resource = when {
        state.executionAvailable -> R.string.arena_status_execution_ready
        state.focus >= 100 -> R.string.arena_status_skill_ready
        state.guarding -> R.string.arena_status_enemy_guard
        state.targetInRange == false -> R.string.arena_status_out_of_range
        else -> null
    }
    return if (resource == null) null else stringResource(resource)
}
