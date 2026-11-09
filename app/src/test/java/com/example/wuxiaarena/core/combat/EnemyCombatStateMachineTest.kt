package com.example.wuxiaarena.core.combat

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class EnemyCombatStateMachineTest {
    private fun ms(value: Long) = value * 1_000_000L

    private data class Timing(
        val direction: AttackDirection,
        val prepareMs: Long,
        val startupMs: Long,
        val activeMs: Long,
        val recoveryMs: Long,
    )

    private fun start(machine: EnemyCombatStateMachine, direction: AttackDirection = AttackDirection.LEFT) {
        machine.advanceBy(ms(800), true)
        assertTrue(machine.tryStartAttack(direction, true).any { it is EnemyCombatEvent.AttackStarted })
    }

    private fun resolve(machine: EnemyCombatStateMachine, outcome: AttackOutcome) =
        machine.resolveActiveAttack(checkNotNull(machine.currentAttackId), outcome)

    @Test
    fun allThreeAttacksFollowTheirBoundariesAndMissOnlyAfterTheActiveWindow() {
        val timings = listOf(
            Timing(AttackDirection.LEFT, 550, 180, 200, 600),
            Timing(AttackDirection.RIGHT, 550, 180, 200, 600),
            Timing(AttackDirection.OVERHEAD, 650, 250, 200, 650),
        )
        for (entry in timings) {
            val machine = EnemyCombatStateMachine()
            val direction = entry.direction
            val prepare = ms(entry.prepareMs)
            val startup = ms(entry.startupMs)
            val active = ms(entry.activeMs)
            val recovery = ms(entry.recoveryMs)
            start(machine, direction)
            assertEquals(prepare, machine.nanosUntilPhaseTransition)

            machine.advanceBy(prepare - 1, true)
            assertEquals(EnemyPhase.PREPARING, machine.phase)
            assertEquals(1L, machine.nanosUntilPhaseTransition)
            machine.advanceBy(1, true)
            assertEquals(EnemyPhase.STARTUP, machine.phase)
            assertEquals(startup, machine.nanosUntilPhaseTransition)
            machine.advanceBy(startup - 1, true)
            assertEquals(EnemyPhase.STARTUP, machine.phase)
            machine.advanceBy(1, true)
            assertEquals(EnemyPhase.ACTIVE, machine.phase)
            assertEquals(direction, machine.currentAttackDirection)
            machine.advanceBy(active - 1, true)
            assertEquals(EnemyPhase.ACTIVE, machine.phase)
            val miss = machine.advanceBy(1, true).filterIsInstance<EnemyCombatEvent.AttackResolved>().single()
            assertEquals(AttackOutcome.MISSED, miss.outcome)
            assertEquals(ms(800) + prepare + startup + active, miss.atNanos)
            assertEquals(EnemyPhase.RECOVERING, machine.phase)
            machine.advanceBy(recovery - 1, true)
            assertEquals(EnemyPhase.RECOVERING, machine.phase)
            machine.advanceBy(1, true)
            assertEquals(EnemyPhase.IDLE, machine.phase)
            assertNull(machine.currentAttackId)
        }
    }

    @Test
    fun oneLargeStepAndSeveralSmallStepsProduceTheSameTimedEvents() {
        val large = EnemyCombatStateMachine()
        val small = EnemyCombatStateMachine()
        start(large)
        start(small)

        val largeEvents = large.advanceBy(ms(1530), true)
        val smallEvents = listOf(550L, 180L, 200L, 600L).flatMap { small.advanceBy(ms(it), true) }

        assertEquals(smallEvents, largeEvents)
        assertEquals(EnemyPhase.IDLE, large.phase)
        assertEquals(ms(2330), large.simulationNanos)
        assertEquals(small.simulationNanos, large.simulationNanos)
    }

    @Test
    fun anAttackNeedsAnIdleDelayAndAnInRangeTarget() {
        val machine = EnemyCombatStateMachine()
        machine.advanceBy(ms(799), true)
        assertTrue(machine.tryStartAttack(AttackDirection.LEFT, true).isEmpty())
        machine.advanceBy(ms(1), true)
        assertTrue(machine.tryStartAttack(AttackDirection.LEFT, false).isEmpty())
        assertTrue(machine.tryStartAttack(AttackDirection.RIGHT, true).any { it is EnemyCombatEvent.AttackStarted })
        assertEquals(EnemyPhase.PREPARING, machine.phase)
    }

    @Test
    fun manualPauseFreezesTheActionAndRequiresAllResumeGates() {
        val machine = EnemyCombatStateMachine()
        start(machine)
        machine.advanceBy(ms(830), true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(ms(100), machine.phaseElapsedNanos)
        val beforePause = machine.simulationNanos
        val attackId = machine.currentAttackId

        machine.pauseByPlayer()
        val pauseId = machine.currentPauseId
        assertEquals(ms(100), machine.nanosUntilPhaseTransition)
        assertTrue(machine.advanceBy(ms(5000), true).isEmpty())
        assertTrue(machine.receivePlayerHit().isEmpty())
        assertTrue(resolve(machine, AttackOutcome.BLOCKED).isEmpty())
        assertEquals(beforePause, machine.simulationNanos)
        assertEquals(ms(100), machine.nanosUntilPhaseTransition)
        assertTrue(machine.tryResume(false, true, pauseId).isEmpty())
        assertTrue(machine.tryResume(true, false, pauseId).isEmpty())
        assertTrue(machine.tryResume(true, true, null).isEmpty())
        assertEquals(PauseReason.USER, machine.pauseReason)

        machine.tryResume(true, true, pauseId)
        assertNull(machine.pauseReason)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(ms(100), machine.phaseElapsedNanos)
        assertEquals(attackId, machine.currentAttackId)
        val events = machine.advanceBy(ms(100), true)
        assertEquals(AttackOutcome.MISSED, events.filterIsInstance<EnemyCombatEvent.AttackResolved>().single().outcome)
        assertEquals(EnemyPhase.RECOVERING, machine.phase)
    }

    @Test
    fun interruptionDuringManualPauseCancelsTheOldAttackOnlyAfterSafeResume() {
        val machine = EnemyCombatStateMachine()
        start(machine)
        machine.advanceBy(ms(200), true)
        val oldAttack = machine.currentAttackId
        val pausedAt = machine.simulationNanos

        machine.pauseByPlayer()
        val oldPauseId = machine.currentPauseId
        val interruption = machine.interruptTracking().filterIsInstance<EnemyCombatEvent.PauseChanged>().single()
        assertEquals(PauseReason.USER, interruption.previous)
        assertEquals(PauseReason.TRACKING_INTERRUPTION, interruption.current)
        assertTrue(machine.tryResume(true, true, oldPauseId).isEmpty())
        assertTrue(machine.tryResume(true, true, null).isEmpty())
        assertEquals(EnemyPhase.PREPARING, machine.phase)

        val resumed = machine.tryResume(true, true, machine.currentPauseId)
        val cancelled = resumed.filterIsInstance<EnemyCombatEvent.AttackCancelled>().single()
        assertEquals(oldAttack, cancelled.attackId)
        assertEquals(AttackCancelReason.TRACKING_INTERRUPTION, cancelled.reason)
        assertEquals(pausedAt, cancelled.atNanos)
        assertEquals(EnemyPhase.IDLE, machine.phase)
        assertEquals(0L, machine.phaseElapsedNanos)
        assertNull(machine.currentAttackId)
        assertTrue(machine.tryStartAttack(AttackDirection.LEFT, true).isEmpty())
        machine.advanceBy(ms(800), true)
        assertTrue(machine.tryStartAttack(AttackDirection.LEFT, true).isNotEmpty())
    }

    @Test
    fun newInterruptionsAndRoundsCannotReuseAnOldResumeConfirmation() {
        val machine = EnemyCombatStateMachine()
        machine.interruptTracking()
        val firstId = machine.currentPauseId
        machine.interruptTracking()
        val secondId = machine.currentPauseId
        assertTrue(machine.tryResume(true, true, firstId).isEmpty())
        assertTrue(machine.tryResume(true, true, secondId).isNotEmpty())

        machine.resetRound()
        machine.pauseByPlayer()
        val thirdId = machine.currentPauseId
        assertTrue(machine.tryResume(true, true, secondId).isEmpty())
        assertTrue(machine.tryResume(true, true, thirdId).isNotEmpty())
        assertNull(machine.pauseReason)
    }

    @Test
    fun repeatedHitsCauseVisibleGuardAndAnUninterruptedCounterattack() {
        val machine = EnemyCombatStateMachine()
        val first = machine.receivePlayerHit().filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single()
        assertEquals(25, first.appliedDamage)
        assertFalse(first.guarded)
        assertEquals(75, machine.health)

        machine.advanceBy(ms(200), true)
        val second = machine.receivePlayerHit()
        assertTrue(second.any { it is EnemyCombatEvent.GuardChanged && it.active })
        assertEquals(10, second.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
        assertEquals(ms(200), machine.phaseElapsedNanos)
        machine.advanceBy(ms(100), true)
        assertEquals(EnemyPhase.PREPARING, machine.phase)
        assertTrue(machine.guarding)
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit()
        machine.advanceBy(ms(200), true)
        machine.receivePlayerHit()
        assertEquals(45, machine.health)
        assertEquals(EnemyPhase.PREPARING, machine.phase)

        machine.advanceBy(ms(430), true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(ms(1030), machine.simulationNanos)
        machine.advanceBy(ms(200), true)
        assertEquals(EnemyPhase.RECOVERING, machine.phase)
        assertFalse(machine.guarding)
        assertEquals(25, machine.receivePlayerHit().filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
    }

    @Test
    fun guardDoesNotPreventDeathOrAllowACancelledCounterattackToContinue() {
        val machine = EnemyCombatStateMachine(initialHealth = 55)
        machine.receivePlayerHit()
        machine.advanceBy(ms(200), true)
        machine.receivePlayerHit()
        machine.advanceBy(ms(200), true)
        machine.receivePlayerHit()
        machine.advanceBy(ms(200), true)
        val lethal = machine.receivePlayerHit()

        assertEquals(0, machine.health)
        assertEquals(EnemyPhase.DEAD, machine.phase)
        assertTrue(lethal.any { it is EnemyCombatEvent.AttackCancelled && it.reason == AttackCancelReason.ENEMY_DEFEATED })
        assertTrue(machine.advanceBy(ms(5000), true).isEmpty())
        assertNull(machine.currentAttackId)
    }

    @Test
    fun fastIndependentHitsCanStillDefeatTheEnemyBeforeTheCounterIsActive() {
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit()
        repeat(8) {
            machine.advanceBy(ms(100), true)
            machine.receivePlayerHit()
        }

        assertEquals(ms(800), machine.simulationNanos)
        assertEquals(0, machine.health)
        assertEquals(EnemyPhase.DEAD, machine.phase)
    }

    @Test
    fun parryEndsGuardAndTheFirstCounterHitKeepsTheRemainingStagger() {
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit()
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit()
        machine.advanceBy(ms(930), true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertTrue(machine.guarding)

        val parry = resolve(machine, AttackOutcome.PARRIED)
        assertTrue(parry.any { it is EnemyCombatEvent.GuardChanged && !it.active })
        assertEquals(HitReaction.PARRIED, machine.hitReaction)
        machine.advanceBy(ms(100), true)
        val hit = machine.receivePlayerHit()
        assertEquals(25, hit.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
        assertEquals(ms(450), hit.filterIsInstance<EnemyCombatEvent.HitReactionStarted>().single().durationNanos)
        machine.advanceBy(ms(450) - 1, true)
        assertEquals(EnemyPhase.HIT, machine.phase)
        machine.advanceBy(1, true)
        assertEquals(EnemyPhase.IDLE, machine.phase)
    }

    @Test
    fun aPlayerHitAtTheSameSimulationTimeAsAParryKeepsTheFullParryStagger() {
        val machine = EnemyCombatStateMachine()
        start(machine)
        machine.advanceBy(ms(730), true)
        val parry = resolve(machine, AttackOutcome.PARRIED)
        val hit = machine.receivePlayerHit()

        assertEquals(parry.first().atNanos, hit.first().atNanos)
        assertEquals(25, hit.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
        assertEquals(ms(550), hit.filterIsInstance<EnemyCombatEvent.HitReactionStarted>().single().durationNanos)
    }

    @Test
    fun resolvedParriesAreAcceptedThroughoutTheActiveWindowButNotAfterIt() {
        for (offset in listOf(0L, 119L, 120L, 150L, 199L)) {
            val machine = EnemyCombatStateMachine()
            start(machine)
            machine.advanceBy(ms(730 + offset), true)
            val result = resolve(machine, AttackOutcome.PARRIED)
            assertEquals(AttackOutcome.PARRIED, result.filterIsInstance<EnemyCombatEvent.AttackResolved>().single().outcome)
            assertEquals(EnemyPhase.HIT, machine.phase)
        }
        val afterWindow = EnemyCombatStateMachine()
        start(afterWindow)
        afterWindow.advanceBy(ms(930), true)
        assertEquals(EnemyPhase.RECOVERING, afterWindow.phase)
        assertTrue(resolve(afterWindow, AttackOutcome.PARRIED).isEmpty())
    }

    @Test
    fun anInterruptionAtTheContactTimePreventsNewCombatResults() {
        val machine = EnemyCombatStateMachine()
        start(machine)
        machine.advanceBy(ms(730), true)
        val interruptedAt = machine.simulationNanos
        machine.interruptTracking()

        assertTrue(resolve(machine, AttackOutcome.PARRIED).isEmpty())
        assertTrue(machine.receivePlayerHit().isEmpty())
        assertEquals(interruptedAt, machine.simulationNanos)
        assertEquals(100, machine.health)
    }

    @Test
    fun delayedResultsCannotResolveANewAttackAfterInterruptionOrRestart() {
        val machine = EnemyCombatStateMachine()
        start(machine)
        machine.advanceBy(ms(730), true)
        val firstAttack = checkNotNull(machine.currentAttackId)
        machine.interruptTracking()
        machine.tryResume(true, true, machine.currentPauseId)

        start(machine)
        machine.advanceBy(ms(730), true)
        val secondAttack = checkNotNull(machine.currentAttackId)
        assertTrue(firstAttack != secondAttack)
        assertTrue(machine.resolveActiveAttack(firstAttack, AttackOutcome.PARRIED).isEmpty())
        assertEquals(EnemyPhase.ACTIVE, machine.phase)

        machine.resetRound()
        start(machine)
        machine.advanceBy(ms(730), true)
        val thirdAttack = checkNotNull(machine.currentAttackId)
        assertTrue(secondAttack != thirdAttack)
        assertTrue(machine.resolveActiveAttack(secondAttack, AttackOutcome.BLOCKED).isEmpty())
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(1, machine.resolveActiveAttack(thirdAttack, AttackOutcome.BLOCKED)
            .filterIsInstance<EnemyCombatEvent.AttackResolved>().size)
    }

    @Test
    fun aGuardedHitWithNoTargetReturnsToIdleWithoutAForcedAttack() {
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit()
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit()
        val events = machine.advanceBy(ms(200), false)

        assertEquals(EnemyPhase.IDLE, machine.phase)
        assertFalse(machine.guarding)
        assertTrue(events.none { it is EnemyCombatEvent.AttackStarted })
    }

    @Test
    fun deathIsTerminalUntilRoundReset() {
        val machine = EnemyCombatStateMachine(initialHealth = 25)
        start(machine)
        machine.receivePlayerHit()
        assertEquals(EnemyPhase.DEAD, machine.phase)
        assertTrue(machine.interruptTracking().isEmpty())
        assertTrue(machine.tryResume(true, true, 1L).isEmpty())
        assertTrue(machine.receivePlayerHit().isEmpty())
        assertEquals(EnemyPhase.DEAD, machine.phase)

        assertEquals(listOf(EnemyCombatEvent.RoundReset()), machine.resetRound())
        assertEquals(25, machine.health)
        assertEquals(0L, machine.simulationNanos)
        assertEquals(EnemyPhase.IDLE, machine.phase)
        assertNull(machine.pauseReason)
    }

    @Test
    fun invalidTimeAndPrematureOrDuplicateResolutionAreRejected() {
        assertThrows(IllegalArgumentException::class.java) { EnemyCombatStateMachine(initialHealth = 0) }
        val machine = EnemyCombatStateMachine()
        assertThrows(IllegalArgumentException::class.java) { machine.advanceBy(-1, true) }
        assertThrows(IllegalArgumentException::class.java) { machine.resolveActiveAttack(1L, AttackOutcome.MISSED) }
        assertTrue(machine.resolveActiveAttack(1L, AttackOutcome.PARRIED).isEmpty())
        start(machine)
        machine.advanceBy(ms(730), true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(1, resolve(machine, AttackOutcome.BLOCKED).filterIsInstance<EnemyCombatEvent.AttackResolved>().size)
        assertTrue(resolve(machine, AttackOutcome.PARRIED).isEmpty())

        val overflow = EnemyCombatStateMachine()
        overflow.advanceBy(Long.MAX_VALUE, true)
        assertThrows(IllegalArgumentException::class.java) { overflow.advanceBy(1, true) }
    }
}
