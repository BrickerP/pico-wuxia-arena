package com.example.wuxiaarena.p0d2f0182.ui

import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ArenaPresentationTest {
    @Test
    fun ranchuShowsSetupHelpBeforeAnyInputSourceIsKnown() {
        assertTrue(arenaShowsEmulatorGuide(null, isRanchuHost = true))
    }

    @Test
    fun observedDesktopSourceShowsHelpIndependentlyOfHostHint() {
        assertTrue(arenaShowsEmulatorGuide(InputOrigin.DESKTOP, isRanchuHost = false))
        assertTrue(arenaShowsEmulatorGuide(InputOrigin.DESKTOP, isRanchuHost = true))
    }

    @Test
    fun ranchuDoesNotOverrideAnExplicitHardwareOrSyntheticSource() {
        for (origin in listOf(InputOrigin.PICO, InputOrigin.SYNTHETIC)) {
            assertFalse(arenaShowsEmulatorGuide(origin, isRanchuHost = true))
            assertFalse(arenaShowsEmulatorGuide(origin, isRanchuHost = false))
        }
    }

    @Test
    fun anUnknownSourceOnAnUnknownHostKeepsGenericHelp() {
        assertFalse(arenaShowsEmulatorGuide(null, isRanchuHost = false))
    }

    @Test
    fun combatCombosRemainVisibleFromTheirFirstChain() {
        assertTrue(arenaShowsCombo(TrialResult.FIGHTING, 2))
        assertTrue(arenaShowsCombo(TrialResult.FIGHTING, 5))
        assertTrue(arenaShowsCombo(TrialResult.ROUND_CLEAR, 5))
    }

    @Test
    fun terminalResultsHideRetainedComboHistory() {
        for (result in listOf(TrialResult.VICTORY, TrialResult.DEFEAT)) {
            for (combo in listOf(0, 1, 2, 5, Int.MAX_VALUE)) {
                assertFalse(arenaShowsCombo(result, combo))
            }
        }
    }

    @Test
    fun singleOrInvalidComboDoesNotShowAChain() {
        for (result in TrialResult.entries) {
            for (combo in listOf(Int.MIN_VALUE, -1, 0, 1)) {
                assertFalse(arenaShowsCombo(result, combo))
            }
        }
    }

    @Test
    fun incomingDirectionCoversReadableWindupThroughContact() {
        for (phase in listOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE)) {
            assertTrue(arenaShowsIncomingStrike(TrialResult.FIGHTING, null, true, phase))
        }
    }

    @Test
    fun retainedDirectionIsHiddenAfterStrikeAndWhilePausedOrUntracked() {
        for (phase in listOf(EnemyPhase.IDLE, EnemyPhase.RECOVERING, EnemyPhase.HIT, EnemyPhase.DEAD)) {
            assertFalse(arenaShowsIncomingStrike(TrialResult.FIGHTING, null, true, phase))
        }
        for (pause in PauseReason.entries) {
            assertFalse(arenaShowsIncomingStrike(TrialResult.FIGHTING, pause, true, EnemyPhase.ACTIVE))
        }
        assertFalse(arenaShowsIncomingStrike(TrialResult.FIGHTING, null, false, EnemyPhase.ACTIVE))
        for (result in TrialResult.entries.filter { it != TrialResult.FIGHTING }) {
            assertFalse(arenaShowsIncomingStrike(result, null, true, EnemyPhase.ACTIVE))
        }
    }
    @Test
    fun telegraphGrowsOnlyWithinItsActualPreparationWindow() {
        assertEquals(0.94f, arenaIncomingSealScale(EnemyPhase.PREPARING, 0L, 650_000_000L), 0.0001f)
        assertEquals(0.97f, arenaIncomingSealScale(EnemyPhase.PREPARING, 325_000_000L, 650_000_000L), 0.0001f)
        assertEquals(1f, arenaIncomingSealScale(EnemyPhase.PREPARING, Long.MAX_VALUE, 650_000_000L), 0.0001f)
        assertEquals(0.94f, arenaIncomingSealScale(EnemyPhase.PREPARING, -1L, 650_000_000L), 0.0001f)
        assertEquals(1f, arenaIncomingSealScale(EnemyPhase.PREPARING, 0L, 0L), 0.0001f)
        assertEquals(1f, arenaIncomingSealScale(EnemyPhase.ACTIVE, 0L, 650_000_000L), 0.0001f)
    }

    @Test
    fun realHitEmphasisSettlesAndDoesNotPulseErrorsOrUnrelatedPhases() {
        assertEquals(1.04f, arenaHitFeedbackScale(EnemyPhase.HIT, 0L, CombatFeedback.PARRY), 0.0001f)
        assertEquals(1.02f, arenaHitFeedbackScale(EnemyPhase.HIT, 80_000_000L, CombatFeedback.HEADSHOT), 0.0001f)
        assertEquals(1f, arenaHitFeedbackScale(EnemyPhase.HIT, 160_000_000L, CombatFeedback.HIT), 0.0001f)
        assertEquals(1f, arenaHitFeedbackScale(EnemyPhase.HIT, Long.MAX_VALUE, CombatFeedback.HIT), 0.0001f)
        assertEquals(1.04f, arenaHitFeedbackScale(EnemyPhase.HIT, -1L, CombatFeedback.HIT), 0.0001f)
        assertEquals(1f, arenaHitFeedbackScale(EnemyPhase.HIT, 0L, CombatFeedback.OUT_OF_RANGE), 0.0001f)
        assertEquals(1f, arenaHitFeedbackScale(EnemyPhase.HIT, 0L, null), 0.0001f)
        assertEquals(1f, arenaHitFeedbackScale(EnemyPhase.ACTIVE, 0L, CombatFeedback.HIT), 0.0001f)
    }

}
