package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class EnemyHitFlashPulseTest {
    @Test
    fun bodyDamageFlashesFor28Milliseconds() {
        val pulse = EnemyHitFlashPulse()
        assertTrue(pulse.update(1L, true, listOf(hit(1L)), 0L))
        assertTrue(pulse.update(1L, true, emptyList(), 27_999_999L))
        assertFalse(pulse.update(1L, true, emptyList(), 28_000_000L))
    }

    @Test
    fun fatalDamageWinsTheBatchAndCannotBeShortenedByANormalHit() {
        val pulse = EnemyHitFlashPulse()
        assertTrue(pulse.update(1L, true, listOf(hit(1L), hit(2L, fatal = true)), 0L))
        assertTrue(pulse.update(1L, true, listOf(hit(3L)), 10_000_000L))
        assertTrue(pulse.update(1L, true, emptyList(), 39_999_999L))
        assertFalse(pulse.update(1L, true, emptyList(), 40_000_000L))
    }

    @Test
    fun zeroDamageAndPlayerOrBladeDefenseContactsDoNotFlashTheEnemy() {
        val pulse = EnemyHitFlashPulse()
        for (kind in CombatImpactKind.entries) {
            assertFalse(pulse.update(1L, true, listOf(hit(kind.ordinal.toLong(), kind, damage = 0)), 0L))
        }
        assertFalse(pulse.update(1L, true, listOf(hit(20L, CombatImpactKind.PLAYER_HIT)), 0L))
        assertFalse(pulse.update(1L, true, listOf(hit(21L, CombatImpactKind.BLOCK)), 0L))
        assertFalse(pulse.update(1L, true, listOf(hit(22L, CombatImpactKind.PARRY)), 0L))
    }

    @Test
    fun duplicatesDoNotRestartAndMutedContactsCannotReplayAfterResume() {
        val pulse = EnemyHitFlashPulse()
        val first = hit(1L)
        pulse.update(1L, true, listOf(first), 0L)
        assertFalse(pulse.update(1L, true, listOf(first), 28_000_000L))
        val paused = hit(2L)
        assertFalse(pulse.update(1L, false, listOf(paused), 30_000_000L))
        assertFalse(pulse.update(1L, true, listOf(paused), 31_000_000L))
    }

    @Test
    fun newRoundAndClockRollbackClearTheOldPulse() {
        val pulse = EnemyHitFlashPulse()
        pulse.update(1L, true, listOf(hit(1L)), 100_000_000L)
        assertFalse(pulse.update(1L, true, emptyList(), 90_000_000L))
        assertTrue(pulse.update(2L, true, listOf(hit(1L)), 110_000_000L))
        assertFalse(pulse.update(3L, true, emptyList(), 111_000_000L))
    }

    @Test
    fun suspendingEndsThePulseWithoutMakingAnOldImpactFresh() {
        val pulse = EnemyHitFlashPulse()
        val impact = hit(1L)
        assertTrue(pulse.update(1L, true, listOf(impact), 0L))
        pulse.suspend()
        assertFalse(pulse.update(1L, true, listOf(impact), 1L))
        assertTrue(pulse.update(1L, true, listOf(hit(2L)), 2L))
    }

    private fun hit(
        id: Long,
        kind: CombatImpactKind = CombatImpactKind.SOFT_HIT,
        damage: Int = 25,
        fatal: Boolean = false,
    ) = CombatImpact(id, kind, Vector3(0.0, 1.0, -1.0), Vector3(0.0, 0.0, 1.0),
        0.8, Hand.RIGHT, 0L, appliedDamage = damage, fatal = fatal)
}
