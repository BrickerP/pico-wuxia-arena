package com.example.wuxiaarena.core.combat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WeaponStoppedClockTest {
    @Test
    fun stoppedIdleAccruesSimulationTimeAndAttackReadiness() {
        val combat = EnemyCombatStateMachine()
        combat.advanceBy(500_000_000L, true)
        assertFalse(combat.canStartAttack(true))
        combat.advanceWhileWeaponStopped(300_000_000L)
        assertEquals(800_000_000L, combat.simulationNanos)
        assertEquals(800_000_000L, combat.phaseElapsedNanos)
        assertEquals(EnemyPhase.IDLE, combat.phase)
        assertTrue(combat.canStartAttack(true))
        assertTrue(combat.tryStartAttack(AttackDirection.OVERHEAD, true).any { it is EnemyCombatEvent.AttackStarted })
    }

    @Test
    fun stoppedAttackPhasesHoldMotionTimeWhileSimulationContinues() {
        val direction = AttackDirection.OVERHEAD
        val offsets = mapOf(
            EnemyPhase.PREPARING to 0L,
            EnemyPhase.STARTUP to direction.preparationNanos,
            EnemyPhase.ACTIVE to direction.preparationNanos + direction.startupNanos,
            EnemyPhase.RECOVERING to direction.preparationNanos + direction.startupNanos + direction.activeNanos,
        )
        for ((phase, offset) in offsets) {
            val combat = EnemyCombatStateMachine()
            combat.advanceBy(800_000_000L, true)
            combat.tryStartAttack(direction, true)
            combat.advanceBy(offset + 10_000_000L, true)
            assertEquals(phase, combat.phase)
            val beforeSimulation = combat.simulationNanos
            val beforePhase = combat.phaseElapsedNanos
            combat.advanceWhileWeaponStopped(300_000_000L)
            assertEquals(phase, combat.phase)
            assertEquals(beforeSimulation + 300_000_000L, combat.simulationNanos)
            assertEquals(beforePhase, combat.phaseElapsedNanos)
            combat.advanceBy(5_000_000L, true)
            assertEquals(beforeSimulation + 305_000_000L, combat.simulationNanos)
            assertEquals(beforePhase + 5_000_000L, combat.phaseElapsedNanos)
        }
    }
}
