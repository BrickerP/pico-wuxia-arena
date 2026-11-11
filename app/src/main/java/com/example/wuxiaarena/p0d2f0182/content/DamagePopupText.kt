package com.example.wuxiaarena.p0d2f0182.content

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.text.font.FontWeight
import com.example.wuxiaarena.p0d2f0182.ui.ArenaUiPalette
import androidx.compose.ui.unit.sp
import com.example.wuxiaarena.p0d2f0182.R
import com.pico.spatial.ui.design.PicoTheme
import com.pico.spatial.ui.design.Text

/** Content changes recompose the label; fading is read only by its graphics layer. */
internal class DamagePopupTextState {
    var content by mutableStateOf<DamagePopupContent?>(null)
    var opacity by mutableFloatStateOf(0f)
}

@Composable
internal fun DamagePopupText(state: DamagePopupTextState) {
    PicoTheme {
        Box(
            modifier = Modifier.size(128.dp, 80.dp).graphicsLayer { alpha = state.opacity },
            contentAlignment = Alignment.Center,
        ) {
            val content = state.content
            if (content != null) {
                val description = stringResource(
                    when {
                        content.fatal -> R.string.arena_damage_fatal_description
                        content.guarded -> R.string.arena_damage_guarded_description
                        content.headHit -> R.string.arena_damage_head_description
                        else -> R.string.arena_damage_description
                    },
                    content.amount,
                )
                Column(
                    modifier = Modifier.clearAndSetSemantics { contentDescription = description },
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    val accent = when {
                        content.fatal -> ArenaUiPalette.antiqueGold
                        content.guarded -> ArenaUiPalette.paleAsh
                        content.headHit -> ArenaUiPalette.antiqueGold
                        else -> ArenaUiPalette.paperIvory
                    }
                    Text(
                        text = stringResource(R.string.arena_damage_value, content.amount),
                        color = accent,
                        style = PicoTheme.typography.displaySmall.copy(
                            fontSize = 44.sp, lineHeight = 48.sp, fontWeight = FontWeight.Bold,
                            shadow = Shadow(ArenaUiPalette.inkBlack, Offset(0f, 2f), 4f),
                        ),
                        maxLines = 1,
                    )
                    val label = when {
                        content.fatal -> R.string.arena_ui_damage_fatal
                        content.guarded -> R.string.arena_ui_damage_guarded
                        content.headHit -> R.string.arena_ui_damage_head
                        else -> null
                    }
                    if (label != null) {
                        Text(text = stringResource(label), color = accent,
                            style = PicoTheme.typography.labelLarge.copy(
                                fontSize = 18.sp, lineHeight = 22.sp,
                                shadow = Shadow(ArenaUiPalette.inkBlack, Offset(0f, 1f), 3f),
                            ), maxLines = 1)
                    }
                }
            }
        }
    }
}
