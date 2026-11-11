package com.example.wuxiaarena.p0d2f0182.ui

import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import com.example.wuxiaarena.p0d2f0182.runtime.CombatFeedback
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ArenaPresentationTest {
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
