package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class EnemyCombatStateMachineTest {
    @Test
    fun aReadCrossCutStopsDuringPreparationButLandsAfterACommittedStroke() {
        val machine = EnemyCombatStateMachine()
        fun cut() = machine.receivePlayerHit(cutLine = CutLine.CROSS)
            .filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage
        assertEquals(25, cut())
        machine.advanceBy(ms(300), true)
        assertEquals(0, cut())
        assertEquals(EnemyPhase.PREPARING, machine.phase)
        val direction = requireNotNull(machine.currentAttackDirection)
        machine.advanceBy(direction.preparationNanos + direction.startupNanos + direction.activeNanos, true)
        assertEquals(EnemyPhase.RECOVERING, machine.phase)
        assertEquals(25, cut())
    }

    @Test
    fun parryingOrFlankingBeatsAReadGuardWithoutChangingTheCut() {
        val cross = Vector3(.25, -.04, .05)
        for (sign in listOf(1.0, -1.0)) {
            assertEquals(CutLine.CROSS, frontalCutLine(cross * sign, Vector3(0.0, 0.0, 1.0), 0f))
        }
        val flank = frontalCutLine(cross, Vector3(1.0, 0.0, 0.0), 0f)
        assertNull(flank)
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(300), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        val flankHit = machine.receivePlayerHit(breakGuard = flank == null, cutLine = flank)
            .filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single()
        assertEquals(25, flankHit.appliedDamage)
        machine.advanceBy(ms(300), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(300), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        val direction = requireNotNull(machine.currentAttackDirection)
        machine.advanceBy(direction.preparationNanos + direction.startupNanos, true)
        resolve(machine, AttackOutcome.PARRIED)
        assertEquals(HitReaction.PARRIED, machine.hitReaction)
        val riposte = machine.receivePlayerHit(cutLine = CutLine.CROSS)
            .filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single()
        assertEquals(25, riposte.appliedDamage)
    }

    private fun ms(value: Long) = value * 1_000_000L

    private fun start(machine: EnemyCombatStateMachine, direction: AttackDirection = AttackDirection.LEFT) {
        machine.advanceBy(ms(800), true)
        assertTrue(machine.tryStartAttack(direction, true).any { it is EnemyCombatEvent.AttackStarted })
    }

    private fun resolve(machine: EnemyCombatStateMachine, outcome: AttackOutcome) =
        machine.resolveActiveAttack(checkNotNull(machine.currentAttackId), outcome)

    @Test
    fun allThreeAttacksFollowTheirBoundariesAndMissOnlyAfterTheActiveWindow() {
        for (direction in AttackDirection.entries) {
            val machine = EnemyCombatStateMachine()
            val prepare = direction.preparationNanos
            val startup = direction.startupNanos
            val active = direction.activeNanos
            val recovery = direction.recoveryNanos
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
        assertTrue(machine.receivePlayerHit(cutLine = CutLine.CROSS).isEmpty())
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
        val first = machine.receivePlayerHit(cutLine = CutLine.CROSS).filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single()
        assertEquals(25, first.appliedDamage)
        assertFalse(first.guarded)
        assertEquals(75, machine.health)

        machine.advanceBy(ms(200), true)
        val second = machine.receivePlayerHit(cutLine = CutLine.CROSS)
        assertFalse(machine.guarding)
        assertEquals(25, second.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
        assertEquals(ms(200), machine.phaseElapsedNanos)
        machine.advanceBy(ms(100), true)
        assertEquals(EnemyPhase.PREPARING, machine.phase)
        assertTrue(machine.guarding)
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(200), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        assertEquals(50, machine.health)
        assertEquals(EnemyPhase.PREPARING, machine.phase)

        machine.advanceBy(ms(430), true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertEquals(ms(1030), machine.simulationNanos)
        machine.advanceBy(ms(200), true)
        assertEquals(EnemyPhase.RECOVERING, machine.phase)
        assertFalse(machine.guarding)
        assertEquals(25, machine.receivePlayerHit(cutLine = CutLine.CROSS).filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
    }

    private fun readyGuardedIdle(machine: EnemyCombatStateMachine) {
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(300), true, AttackDirection.LEFT)
        assertEquals(EnemyPhase.PREPARING, machine.phase)
        val direction = requireNotNull(machine.currentAttackDirection)
        machine.advanceBy(direction.preparationNanos + direction.startupNanos +
            direction.activeNanos + direction.recoveryNanos, true)
        assertEquals(EnemyPhase.IDLE, machine.phase)
        assertTrue(machine.guarding)
    }

    @Test
    fun anArmedIdleGuardStartsExactlyOneCounterInTheSuppliedDirection() {
        for (direction in AttackDirection.entries) {
            val machine = EnemyCombatStateMachine()
            readyGuardedIdle(machine)
            val began = machine.simulationNanos
            val events = machine.receivePlayerHit(cutLine = CutLine.CROSS, counterDirection = direction)
            val started = events.filterIsInstance<EnemyCombatEvent.AttackStarted>().single()

            assertEquals(direction, started.direction)
            assertTrue(started.counterattack)
            assertEquals(began, started.atNanos)
            assertEquals(direction, machine.currentAttackDirection)
            assertEquals(EnemyPhase.PREPARING, machine.phase)
            assertEquals(75, machine.health)
            assertTrue(machine.guarding)

            val repeated = machine.receivePlayerHit(cutLine = CutLine.CROSS, counterDirection = AttackDirection.OVERHEAD)
            assertTrue(repeated.none { it is EnemyCombatEvent.AttackStarted })
            assertEquals(started.attackId, machine.currentAttackId)
            assertEquals(direction, machine.currentAttackDirection)
        }
    }

    @Test
    fun delayedGuardCounterUsesTheDirectionAtTheHitBoundary() {
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS, counterDirection = AttackDirection.LEFT)

        val beforeBoundary = machine.advanceBy(ms(200) - 1, true, AttackDirection.LEFT)
        assertTrue(beforeBoundary.none { it is EnemyCombatEvent.AttackStarted })
        assertEquals(EnemyPhase.HIT, machine.phase)
        val boundary = machine.advanceBy(1, true, AttackDirection.RIGHT)
            .filterIsInstance<EnemyCombatEvent.AttackStarted>().single()

        assertEquals(AttackDirection.RIGHT, boundary.direction)
        assertTrue(boundary.counterattack)
        assertEquals(ms(300), boundary.atNanos)
    }

    @Test
    fun aLethalOrPausedArmedGuardDoesNotStartACounterattack() {
        val lethal = EnemyCombatStateMachine(initialHealth = 35)
        readyGuardedIdle(lethal)
        val death = lethal.receivePlayerHit(cutLine = CutLine.VERTICAL, counterDirection = AttackDirection.RIGHT)
        assertEquals(EnemyPhase.DEAD, lethal.phase)
        assertNull(lethal.currentAttackDirection)
        assertTrue(death.none { it is EnemyCombatEvent.AttackStarted })

        val paused = EnemyCombatStateMachine()
        readyGuardedIdle(paused)
        paused.pauseByPlayer()
        assertTrue(paused.receivePlayerHit(cutLine = CutLine.CROSS, counterDirection = AttackDirection.RIGHT).isEmpty())
        assertEquals(75, paused.health)
        assertTrue(paused.guarding)
        assertNull(paused.currentAttackId)
    }

    @Test
    fun anArmedIdleGuardKeepsTheExistingDefaultCounterDirection() {
        val machine = EnemyCombatStateMachine()
        readyGuardedIdle(machine)
        val started = machine.receivePlayerHit(cutLine = CutLine.CROSS)
            .filterIsInstance<EnemyCombatEvent.AttackStarted>().single()

        assertEquals(AttackDirection.OVERHEAD, started.direction)
        assertTrue(started.counterattack)
    }

    @Test
    fun guardDoesNotPreventDeathOrAllowACancelledCounterattackToContinue() {
        val machine = EnemyCombatStateMachine(initialHealth = 55)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(200), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(200), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(200), true)
        val lethal = machine.receivePlayerHit(cutLine = CutLine.VERTICAL)

        assertEquals(0, machine.health)
        assertEquals(EnemyPhase.DEAD, machine.phase)
        assertTrue(lethal.any { it is EnemyCombatEvent.AttackCancelled && it.reason == AttackCancelReason.ENEMY_DEFEATED })
        assertTrue(machine.advanceBy(ms(5000), true).isEmpty())
        assertNull(machine.currentAttackId)
    }

    @Test
    fun repeatedIdenticalHitsDoNotDefeatTheCounterBeforeItIsActive() {
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        repeat(8) {
            machine.advanceBy(ms(100), true)
            machine.receivePlayerHit(cutLine = CutLine.CROSS)
        }

        assertEquals(ms(800), machine.simulationNanos)
        assertEquals(25, machine.health)
        assertEquals(EnemyPhase.PREPARING, machine.phase)
    }

    @Test
    fun parryEndsGuardAndTheFirstCounterHitKeepsTheRemainingStagger() {
        val machine = EnemyCombatStateMachine()
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(930), true)
        assertEquals(EnemyPhase.ACTIVE, machine.phase)
        assertTrue(machine.guarding)

        val parry = resolve(machine, AttackOutcome.PARRIED)
        assertTrue(parry.any { it is EnemyCombatEvent.GuardChanged && !it.active })
        assertEquals(HitReaction.PARRIED, machine.hitReaction)
        machine.advanceBy(ms(100), true)
        val hit = machine.receivePlayerHit(cutLine = CutLine.CROSS)
        assertEquals(25, hit.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single().appliedDamage)
        assertEquals(ms(450), hit.filterIsInstance<EnemyCombatEvent.HitReactionStarted>().single().durationNanos)
        machine.advanceBy(ms(450) - 1, true)
        assertEquals(EnemyPhase.HIT, machine.phase)
        machine.advanceBy(1, true)
        assertEquals(EnemyPhase.PREPARING, machine.phase)
    }

    @Test
    fun aPlayerHitAtTheSameSimulationTimeAsAParryKeepsTheFullParryStagger() {
        val machine = EnemyCombatStateMachine()
        start(machine)
        machine.advanceBy(ms(730), true)
        val parry = resolve(machine, AttackOutcome.PARRIED)
        val hit = machine.receivePlayerHit(cutLine = CutLine.CROSS)

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
        assertTrue(machine.receivePlayerHit(cutLine = CutLine.CROSS).isEmpty())
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
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        machine.advanceBy(ms(100), true)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        val events = machine.advanceBy(ms(200), false)

        assertEquals(EnemyPhase.IDLE, machine.phase)
        assertFalse(machine.guarding)
        assertTrue(events.none { it is EnemyCombatEvent.AttackStarted })
    }

    @Test
    fun deathRemainsTerminalAcrossTrackingPauseUntilRoundReset() {
        val machine = EnemyCombatStateMachine(initialHealth = 25)
        start(machine)
        machine.receivePlayerHit(cutLine = CutLine.CROSS)
        assertEquals(EnemyPhase.DEAD, machine.phase)
        val stoppedAt = machine.simulationNanos
        val pause = machine.interruptTracking().filterIsInstance<EnemyCombatEvent.PauseChanged>().single()
        assertEquals(PauseReason.TRACKING_INTERRUPTION, pause.current)
        assertEquals(EnemyPhase.DEAD, machine.phase)
        assertTrue(machine.advanceBy(1_000_000_000L, true).isEmpty())
        val resumed = machine.tryResume(true, true, pause.pauseId)
            .filterIsInstance<EnemyCombatEvent.PauseChanged>().single()
        assertNull(resumed.current)
        assertEquals(stoppedAt, machine.simulationNanos)
        assertEquals(0, machine.health)
        assertTrue(machine.receivePlayerHit(cutLine = CutLine.CROSS).isEmpty())
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
