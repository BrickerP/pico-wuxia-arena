package com.example.wuxiaarena.core.combat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ArmoredOpponentTest {
    private fun boss() = EnemyCombatStateMachine(150, frontArmored = true)

    private fun start(machine: EnemyCombatStateMachine, direction: AttackDirection = AttackDirection.LEFT): Long {
        machine.advanceBy(800_000_000L, true)
        return machine.tryStartAttack(direction, true).filterIsInstance<EnemyCombatEvent.AttackStarted>().single().attackId
    }

    private fun active(machine: EnemyCombatStateMachine, direction: AttackDirection = AttackDirection.LEFT): Long {
        val id = start(machine, direction)
        machine.advanceBy(direction.preparationNanos + direction.startupNanos, true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        return id
    }

    private fun cut(machine: EnemyCombatStateMachine, line: CutLine? = CutLine.CROSS, thrust: Boolean = false): Int {
        val before = machine.health
        machine.receivePlayerHit(cutLine = line, breakGuard = line == null, openingThrust = thrust)
        return before - machine.health
    }

    @Test fun unwitnessedRecoveryAndPassiveBladeContactsDoNotExposeTheFront() {
        for (route in listOf("early", "miss", "trade", "incidental")) {
            val machine = boss()
            if (route == "early") {
                val id = start(machine)
                machine.resolveActiveAttack(id, AttackOutcome.BLOCKED, matchedGuard = true)
            } else {
                val id = active(machine)
                when (route) {
                    "miss" -> machine.advanceBy(AttackDirection.LEFT.activeNanos, true)
                    "trade" -> {
                        machine.recordEvadedBlade(id)
                        machine.resolveActiveAttack(id, AttackOutcome.HIT_PLAYER)
                    }
                    "incidental" -> machine.resolveActiveAttack(id, AttackOutcome.BLOCKED, matchedGuard = false)
                }
            }
            assertEquals(route, EnemyPhase.RECOVERING, machine.phase)
            for (line in CutLine.entries) assertEquals("unearned recovery: $route/$line", 0, cut(machine, line))
        }
    }

    @Test fun attackingIntoAnActiveBladeOrChangingCutLinesCannotGrindThroughArmor() {
        val machine = boss()
        val id = active(machine)
        for (line in CutLine.entries) assertEquals(0, cut(machine, line))
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(id, machine.currentAttackId)
        machine.advanceBy(AttackDirection.LEFT.activeNanos, true)
        repeat(12) { assertEquals(0, cut(machine, CutLine.entries[it % CutLine.entries.size])) }
        assertEquals(150, machine.health)
    }

    @Test fun alignedDefenseAndParryEachAllowOneFullCounterCut() {
        for (outcome in listOf(AttackOutcome.BLOCKED, AttackOutcome.PARRIED)) {
            val machine = boss()
            val id = active(machine)
            machine.resolveActiveAttack(id, outcome, matchedGuard = outcome == AttackOutcome.BLOCKED)
            assertEquals(outcome.name, 25, cut(machine))
            assertEquals("Opportunity is spent even on a different follow-up", 0, cut(machine, CutLine.VERTICAL))
            machine.resolveActiveAttack(id, outcome, matchedGuard = true)
            assertEquals("A duplicate resolution must not issue another opening", 0, cut(machine))
        }
    }

    @Test fun evasionOnlyOpensTheSameAttackWhenItActuallyMisses() {
        val machine = boss()
        val id = active(machine)
        machine.recordEvadedBlade(id)
        assertEquals("Evidence alone cannot open the armor mid-attack", 0, cut(machine))
        machine.advanceBy(AttackDirection.LEFT.activeNanos, true)
        assertEquals(25, cut(machine))
        assertEquals(0, cut(machine))

        val stale = boss()
        val previous = active(stale)
        stale.advanceBy(AttackDirection.LEFT.activeNanos + AttackDirection.LEFT.recoveryNanos, true)
        val next = active(stale)
        assertTrue(next != previous)
        stale.recordEvadedBlade(previous)
        stale.advanceBy(AttackDirection.LEFT.activeNanos, true)
        assertEquals(0, cut(stale))
    }

    @Test fun unusedCounterExpiresAtRecoveryEndAndOnRestart() {
        val machine = boss()
        val first = active(machine)
        machine.resolveActiveAttack(first, AttackOutcome.BLOCKED, matchedGuard = true)
        machine.advanceBy(AttackDirection.LEFT.recoveryNanos, true)
        assertEquals(EnemyPhase.IDLE, machine.phase)
        assertEquals(0, cut(machine))
        val restarted = boss()
        val previous = active(restarted)
        restarted.resolveActiveAttack(previous, AttackOutcome.PARRIED)
        restarted.resetRound()
        assertEquals(150, restarted.health)
        assertEquals(0, cut(restarted))
    }

    @Test fun committedFrontalThrustRequiresTheOverheadTellButFlanksRemainOpen() {
        val overhead = boss()
        start(overhead, AttackDirection.OVERHEAD)
        assertEquals(0, cut(overhead, CutLine.THRUST, thrust = false))
        assertEquals(0, cut(overhead, CutLine.CROSS, thrust = true))
        assertEquals(25, cut(overhead, CutLine.THRUST, thrust = true))
        for (direction in listOf(AttackDirection.LEFT, AttackDirection.RIGHT)) {
            val machine = boss()
            start(machine, direction)
            assertEquals(0, cut(machine, CutLine.THRUST, thrust = true))
            assertNotNull(machine.currentAttackId)
            assertEquals(25, cut(machine, line = null))
        }
    }
}
