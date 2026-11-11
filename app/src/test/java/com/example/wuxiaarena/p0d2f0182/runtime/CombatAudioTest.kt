package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.R
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Exercises the production consumer against an output recorder, never a second event policy. */
class CombatAudioTest {
    @Test
    fun firstBatchConsumesUnorderedIdsAndDeduplicatesEachContact() {
        val f = Fixture()
        val batch = listOf(contact(9), contact(2, CombatImpactKind.BLOCK), contact(9), contact(4, CombatImpactKind.PARRY))
        f.present(events = batch)
        f.present(events = batch.reversed())
        assertEquals(listOf(R.raw.arena_hit, R.raw.arena_block, R.raw.arena_parry), f.output.contacts.map { it.sample })
    }

    @Test
    fun nextRoundConsumesItsFirstBatchAndRejectsLateOlderRoundCallbacks() {
        val f = Fixture()
        f.present(events = listOf(contact(1)))
        val original = f.output.contacts.single().stream
        f.present(f.state.copy(roundGeneration = 2), listOf(contact(1, CombatImpactKind.HARD_HIT)))
        f.present(f.state, listOf(contact(2, CombatImpactKind.BLOCK)))
        assertEquals(listOf(R.raw.arena_hit, R.raw.arena_hard_hit), f.output.contacts.map { it.sample })
        assertTrue(original in f.output.stopped)
    }

    @Test
    fun loadingContactCanPlayAtTheFreshnessBoundary() {
        val f = Fixture(ready = false)
        f.present(events = listOf(contact(1)))
        f.now += 120_000_000L
        f.output.ready(R.raw.arena_hit)
        f.present()
        assertEquals(1, f.output.contacts.size)
    }

    @Test
    fun loadingContactIsDiscardedAfterTheFreshnessBoundary() {
        val f = Fixture(ready = false)
        f.present(events = listOf(contact(1)))
        f.now += 120_000_001L
        f.output.ready(R.raw.arena_hit)
        f.present()
        assertTrue(f.output.contacts.isEmpty())
    }

    @Test
    fun failedSampleDoesNotDelayAReadyDifferentMaterial() {
        val f = Fixture(ready = false)
        f.present(events = listOf(contact(1), contact(2, CombatImpactKind.PARRY)))
        f.output.ready(R.raw.arena_hit, status = 1)
        f.output.ready(R.raw.arena_parry)
        f.present()
        assertEquals(listOf(R.raw.arena_parry), f.output.contacts.map { it.sample })
        assertEquals(1, f.warnings.size)
        assertTrue(f.warnings.single().contains("status=1"))
    }

    @Test
    fun unloadedBurstHasAtMostTwentyFourFreshPendingContacts() {
        val f = Fixture(ready = false)
        f.present(events = (1L..50L).map(::contact))
        f.output.ready(R.raw.arena_hit)
        f.present()
        assertEquals(24, f.output.contacts.size)
    }

    @Test
    fun saturatedQueueRetainsParryAndExecutionOverOrdinaryHits() {
        val f = Fixture(ready = false)
        f.present(events = (1L..24L).map(::contact))
        f.present(events = listOf(contact(30, CombatImpactKind.PARRY), contact(31, CombatImpactKind.EXECUTION)))
        f.output.readyAll()
        f.present()
        assertEquals(24, f.output.contacts.size)
        assertEquals(1, f.output.contacts.count { it.sample == R.raw.arena_parry })
        assertEquals(1, f.output.contacts.count { it.sample == R.raw.arena_execution })
    }

    @Test
    fun lowPriorityContactCannotEvictAFullQueueOfParries() {
        val f = Fixture(ready = false)
        f.present(events = (1L..24L).map { contact(it, CombatImpactKind.PARRY) })
        f.present(events = listOf(contact(30)))
        f.output.readyAll()
        f.present()
        assertEquals(24, f.output.contacts.size)
        assertTrue(f.output.contacts.all { it.sample == R.raw.arena_parry })
    }

    @Test
    fun fatalArmorHitKeepsItsMetalContactAndAddsOneQuieterExecutionLayer() {
        val f = Fixture()
        f.present(events = listOf(contact(1, CombatImpactKind.HARD_HIT).copy(appliedDamage = 6, fatal = true)))
        assertEquals(listOf(R.raw.arena_hard_hit, R.raw.arena_execution), f.output.contacts.map { it.sample })
        val (metal, accent) = f.output.contacts
        assertTrue(accent.left < metal.left)
        assertTrue(accent.priority > metal.priority)
        assertTrue(metal.rate < 1f)
    }

    @Test
    fun explicitExecutionDoesNotDoubleItsOwnLethalLayer() {
        val f = Fixture()
        f.present(events = listOf(contact(1, CombatImpactKind.EXECUTION).copy(appliedDamage = 6, fatal = true)))
        assertEquals(listOf(R.raw.arena_execution), f.output.contacts.map { it.sample })
    }

    @Test
    fun actualDamageAddsWeightWithoutTurningZeroDamageDefenseIntoAHit() {
        val f = Fixture()
        f.present(events = listOf(contact(1).copy(appliedDamage = 1), contact(2).copy(appliedDamage = 40)))
        assertTrue(f.output.contacts[1].left > f.output.contacts[0].left)
        f.present(events = listOf(contact(3, CombatImpactKind.BLOCK)))
        assertEquals(R.raw.arena_block, f.output.contacts.last().sample)
    }

    @Test
    fun pauseStopsPlayingSoundsAndConsumesMutedContactsWithoutReplay() {
        val f = Fixture()
        f.present(events = listOf(contact(1)))
        val oldStreams = f.output.active.keys.toSet()
        f.present(f.state.copy(pauseReason = PauseReason.USER), listOf(contact(2)))
        assertTrue(f.output.active.isEmpty())
        assertTrue(f.output.stopped.containsAll(oldStreams))
        f.present(events = listOf(contact(2)))
        assertEquals(1, f.output.contacts.size)
    }

    @Test
    fun unavailableSceneDropsPendingAndCurrentContacts() {
        val f = Fixture(ready = false)
        f.present(events = listOf(contact(1)))
        f.present(f.state.copy(sceneReady = false), listOf(contact(2)))
        f.output.readyAll()
        f.present(events = listOf(contact(2)))
        assertTrue(f.output.contacts.isEmpty())
    }

    @Test
    fun changingRoundClearsUnloadedContacts() {
        val f = Fixture(ready = false)
        f.present(events = listOf(contact(1)))
        f.present(f.state.copy(roundGeneration = 2))
        f.output.readyAll()
        f.present(f.state.copy(roundGeneration = 2))
        assertTrue(f.output.contacts.isEmpty())
    }

    @Test
    fun finalDefeatContactSurvivesTheSessionsTerminalUserPauseButMotionSoundsStop() {
        val f = Fixture()
        f.present()
        val rain = f.output.plays.single { it.sample == R.raw.arena_rain }.stream
        f.present(f.state.copy(
            result = TrialResult.DEFEAT, pauseReason = PauseReason.USER, inputReady = false,
            enemyGaitMeters = 0.6, playerBladeTipSpeed = 3.0, playerBladeAtRest = false,
            phase = EnemyPhase.STARTUP, attackId = 4,
        ), listOf(contact(1, CombatImpactKind.PLAYER_HIT)))
        assertEquals(listOf(R.raw.arena_hurt), f.output.contacts.map { it.sample })
        assertTrue(rain in f.output.stopped)
        assertFalse(f.output.plays.any { it.sample == R.raw.arena_whoosh || it.sample == R.raw.arena_step })
    }

    @Test
    fun terminalContactStillRequiresAnAvailableScene() {
        val f = Fixture()
        f.present(f.state.copy(result = TrialResult.DEFEAT, sceneReady = false, inputReady = false),
            listOf(contact(1, CombatImpactKind.PLAYER_HIT)))
        assertTrue(f.output.plays.isEmpty())
    }

    @Test
    fun playerWhooshNeedsObservedRestThenARealSpeedCrossing() {
        val f = Fixture()
        fun moving(speed: Double) = f.state.copy(playerBladeAtRest = false, playerBladeTipSpeed = speed)
        f.present(moving(3.0))
        assertEquals(0, f.output.count(R.raw.arena_whoosh))
        f.present()
        f.present(moving(1.44))
        assertEquals(0, f.output.count(R.raw.arena_whoosh))
        f.present(moving(1.45))
        f.present(moving(4.0))
        assertEquals(1, f.output.count(R.raw.arena_whoosh))
    }

    @Test
    fun playerSwingCooldownAndRearmPreventOneMotionFromRattling() {
        val f = Fixture()
        val fast = f.state.copy(playerBladeAtRest = false, playerBladeTipSpeed = 2.0)
        f.present()
        f.present(fast)
        f.present()
        f.now += 179_999_999L
        f.present(fast)
        assertEquals(1, f.output.count(R.raw.arena_whoosh))
        f.now += 1L
        f.present(fast)
        assertEquals(2, f.output.count(R.raw.arena_whoosh))
    }

    @Test
    fun resumedOrNewMotionGenerationDoesNotReplayAnAlreadyFastBlade() {
        val f = Fixture()
        val fast = f.state.copy(playerBladeAtRest = false, playerBladeTipSpeed = 3.0)
        f.present()
        f.present(f.state.copy(pauseReason = PauseReason.USER))
        f.present(fast)
        assertEquals(0, f.output.count(R.raw.arena_whoosh))
        f.present()
        f.present(fast.copy(playerMotionGeneration = 2))
        assertEquals(0, f.output.count(R.raw.arena_whoosh))
        f.present(f.state.copy(playerMotionGeneration = 2))
        f.present(fast.copy(playerMotionGeneration = 2))
        assertEquals(1, f.output.count(R.raw.arena_whoosh))
    }

    @Test
    fun nonFiniteOrMissingBladeCannotProduceAPlayerWhoosh() {
        val f = Fixture()
        f.present()
        f.present(f.state.copy(playerBladeAtRest = false, playerBladeTipSpeed = Double.NaN))
        f.present(f.state.copy(playerBladeAtRest = false, playerBladeTipSpeed = 3.0, playerBladeTip = null))
        assertEquals(0, f.output.count(R.raw.arena_whoosh))
    }

    @Test
    fun enemyStartupWhooshOccursOncePerAttack() {
        val f = Fixture()
        f.present(f.state.copy(phase = EnemyPhase.PREPARING, attackId = 1))
        val startup = f.state.copy(phase = EnemyPhase.STARTUP, attackId = 1)
        f.present(startup)
        f.present(startup)
        f.present(startup.copy(attackId = 2))
        assertEquals(2, f.output.count(R.raw.arena_whoosh))
    }

    @Test
    fun forwardWalkBindsAtZeroSilentlyAndEntersTheRightStanceAtTheFirstMarker() {
        val f = Fixture()
        f.walk(0.0)
        f.walk(f.stepMeters(1) - 0.001)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(1))
        assertStepFeet(f, EnemyFoot.RIGHT)
        f.walk(f.stepMeters(1))
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun reverseWalkBindsAtZeroSilentlyAndEntersTheLeftStanceFirst() {
        val f = Fixture()
        f.walk(0.0, direction = -1f)
        f.walk(-0.001, direction = -1f)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(5) - f.profile.strideMeters - 0.001, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun oneForwardLoopConsumesAllSixPreparedMarkersInTheirFootOrder() {
        val f = Fixture()
        f.walk(0.0)
        for (event in f.profile.stepEvents.drop(1)) f.walk(event.phase * f.profile.strideMeters + 0.001)
        f.walk(f.profile.strideMeters + 0.001)
        assertStepFeet(f, EnemyFoot.RIGHT, EnemyFoot.LEFT, EnemyFoot.RIGHT, EnemyFoot.LEFT, EnemyFoot.RIGHT, EnemyFoot.LEFT)
    }

    @Test
    fun negativeGaitTraversesSixReverseMarkersAcrossTheNegativeLoopSeam() {
        val f = Fixture()
        f.walk(0.0, direction = -1f)
        for (event in f.profile.stepEvents.drop(1).reversed()) {
            f.walk((event.phase - 1.0) * f.profile.strideMeters - 0.001, direction = -1f)
        }
        f.walk(-f.profile.strideMeters - 0.001, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT, EnemyFoot.RIGHT, EnemyFoot.LEFT, EnemyFoot.RIGHT, EnemyFoot.LEFT, EnemyFoot.RIGHT)
    }

    @Test
    fun repeatingAnExactLoopSeamDoesNotDuplicateTheFootContact() {
        val f = Fixture()
        val seam = f.profile.strideMeters
        f.walk(seam - 0.01)
        f.walk(seam)
        f.walk(seam)
        f.walk(seam + 0.01)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun forwardArrivalAtExactPositiveAndNegativeSeventhLoopSeamsPlaysOnlyOneLeftStep() {
        for (cycle in listOf(-7, 7)) {
            val f = Fixture()
            val seam = f.profile.strideMeters * cycle
            f.walk(seam - 0.01)
            f.walk(seam)
            f.walk(seam)
            f.walk(seam + 0.001)
            assertStepFeet(f, EnemyFoot.LEFT)
        }
    }

    @Test
    fun reverseArrivalAtExactPositiveAndNegativeSeventhLoopSeamsPlaysOnlyOneRightStep() {
        for (cycle in listOf(-7, 7)) {
            val f = Fixture()
            val seam = f.profile.strideMeters * cycle
            f.walk(seam + 0.01, direction = -1f)
            f.walk(seam, direction = -1f)
            f.walk(seam, direction = -1f)
            f.walk(seam - 0.001, direction = -1f)
            assertStepFeet(f, EnemyFoot.RIGHT)
        }
    }

    @Test
    fun tinyPositiveStrideSelectsTheLatestSharedClockStanceWithoutRecoveringAnOverflowingCycle() {
        val base = Fixture().profile
        val profile = LocomotionProfile(base.idle, base.walk, base.loopStartSeconds, base.loopEndSeconds,
            1e-200, base.stepEvents)
        assertEquals(EnemyFoot.LEFT, latestAudioFootfall(profile, 0.0, 0.1))
        assertEquals(profile.stepEvents[2].reverseFoot, latestAudioFootfall(profile, 0.0, -0.1))
    }

    @Test
    fun minimumPositiveStrideUsesTheSharedClockSeamInBothDirections() {
        val base = Fixture().profile
        val profile = LocomotionProfile(base.idle, base.walk, base.loopStartSeconds, base.loopEndSeconds,
            Double.MIN_VALUE, base.stepEvents)
        assertEquals(EnemyFoot.LEFT, latestAudioFootfall(profile, 0.0, 0.1))
        assertEquals(profile.stepEvents.first().reverseFoot, latestAudioFootfall(profile, 0.0, -0.1))
    }

    @Test
    fun exactFullLoopReverseArrivalIncludesTheSignedNegativeFirstMarker() {
        val base = Fixture().profile
        val profile = LocomotionProfile(base.idle, base.walk, base.loopStartSeconds, base.loopEndSeconds,
            0.1, base.stepEvents)
        val current = profile.strideMeters * (profile.stepEvents[1].phase - 1.0)
        assertEquals(profile.stepEvents[1].reverseFoot,
            latestAudioFootfall(profile, current + profile.strideMeters, current))
    }

    @Test
    fun exactFullLoopForwardArrivalIncludesTheSignedPositiveSecondMarker() {
        val base = Fixture().profile
        val profile = LocomotionProfile(base.idle, base.walk, base.loopStartSeconds, base.loopEndSeconds,
            0.1, base.stepEvents)
        val current = profile.strideMeters * (1.0 + profile.stepEvents[2].phase)
        assertEquals(profile.stepEvents[2].forwardFoot,
            latestAudioFootfall(profile, current - profile.strideMeters, current))
    }

    @Test
    fun reverseArrivalIncludesAnExactMarkerButDepartureAndRepeatedSamplesExcludeIt() {
        val f = Fixture()
        val marker = f.stepMeters(1)
        f.walk(marker + 0.01, direction = -1f)
        f.walk(marker, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT)
        f.walk(marker, direction = -1f)
        f.walk(marker - 0.01, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun reverseArrivalIncludesTheExactNegativeCycleFirstMarkerWithoutRepeatingIt() {
        val f = Fixture()
        val marker = f.profile.strideMeters * (f.profile.stepEvents[1].phase - 1.0)
        f.walk(marker + 0.01, direction = -1f)
        f.walk(marker, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT)
        f.walk(marker, direction = -1f)
        f.walk(marker - 0.001, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun forwardDepartureExcludesTheExactNegativeCycleSecondMarker() {
        val f = Fixture()
        val marker = f.profile.strideMeters * (f.profile.stepEvents[2].phase - 1.0)
        f.walk(marker)
        f.walk(marker + 0.001)
        f.walk(marker + 0.001)
        f.walk(marker + 0.01)
        assertTrue("The initial marker was already the binding position, so departure must not replay it", f.output.steps.isEmpty())
    }

    @Test
    fun reverseCrossingZeroUsesTheSeamMarkerAndDoesNotReplayItOnDeparture() {
        val f = Fixture()
        f.walk(0.01, direction = -1f)
        f.walk(0.0, direction = -1f)
        f.walk(0.0, direction = -1f)
        f.walk(-0.01, direction = -1f)
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun firstBindingAtAnArbitraryMarkerIsSilentAndOnlyTheNextMarkerPlays() {
        val f = Fixture()
        f.walk(f.stepMeters(2))
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(3) + 0.001)
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun stoppingAtAnArbitraryPhaseAdvancesTheCursorWithoutInventingSteps() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        f.walk(f.stepMeters(2) + 0.01, direction = 0f)
        f.walk(f.stepMeters(2) + 0.01)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(3) + 0.001)
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun attackPhasesAdvanceTheGaitCursorButDoNotSoundOrReplaySkippedSteps() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        f.walk(f.stepMeters(2) + 0.01, phase = EnemyPhase.STARTUP)
        f.walk(f.stepMeters(3) + 0.01, phase = EnemyPhase.ACTIVE)
        f.walk(f.stepMeters(3) + 0.02)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(4) + 0.001)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun changingPlayerMotionGenerationDoesNotResetTheEnemyGaitClock() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        f.present(f.walking(f.stepMeters(1) + 0.01).copy(playerMotionGeneration = 2))
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun pausedWalkingRebindsOnTheFirstResumedFrameWithoutCatchup() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        f.present(f.walking(f.stepMeters(2) + 0.01).copy(pauseReason = PauseReason.USER))
        f.walk(f.stepMeters(3) + 0.01)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(4) + 0.001)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun restoredSceneRebindsWithoutReplayingTheDistanceWhileItWasUnavailable() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        f.present(f.walking(f.stepMeters(2) + 0.01).copy(sceneReady = false))
        f.walk(f.stepMeters(3) + 0.01)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(4) + 0.001)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun newRoundRebindsItsFirstGaitFrameWithoutAnOldContact() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        f.present(f.walking(f.stepMeters(2) + 0.01).copy(roundGeneration = 2))
        assertTrue(f.output.steps.isEmpty())
        f.present(f.walking(f.stepMeters(3) + 0.001).copy(roundGeneration = 2))
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun changingOpponentRebindsEvenWhenItsPreparedLoopHasTheSameNumbers() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        val next = arenaOpponents[1].locomotionProfile()
        val bind = f.walking(next.strideMeters * next.stepEvents[2].phase + 0.01).copy(roundNumber = 2)
        f.present(bind)
        assertTrue(f.output.steps.isEmpty())
        f.present(bind.copy(enemyGaitMeters = next.strideMeters * next.stepEvents[3].phase + 0.001))
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun nonFiniteGaitClearsTheCursorAndCannotCauseAFutureCatchupContact() {
        for (bad in listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY)) {
            val f = Fixture()
            f.walk(f.stepMeters(1) - 0.01)
            f.walk(bad)
            f.walk(f.stepMeters(2) + 0.01)
            assertTrue(f.output.steps.isEmpty())
            f.walk(f.stepMeters(3) + 0.001)
            assertStepFeet(f, EnemyFoot.RIGHT)
        }
    }

    @Test
    fun nonFiniteMovementDirectionIsSilentAndStillAdvancesTheCursor() {
        for (bad in listOf(Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY)) {
            val f = Fixture()
            f.walk(f.stepMeters(1) - 0.01)
            f.walk(f.stepMeters(2) + 0.01, direction = bad)
            f.walk(f.stepMeters(2) + 0.02)
            assertTrue(f.output.steps.isEmpty())
            f.walk(f.stepMeters(3) + 0.001)
            assertStepFeet(f, EnemyFoot.RIGHT)
        }
    }

    @Test
    fun teleportDiscardsAllSkippedMarkersAndRebindsAtTheDestination() {
        val f = Fixture()
        f.walk(0.0)
        val destination = 5 * f.profile.strideMeters + f.stepMeters(2) + 0.01
        f.walk(destination)
        f.walk(destination)
        assertTrue(f.output.steps.isEmpty())
        f.walk(5 * f.profile.strideMeters + f.stepMeters(3) + 0.001)
        assertStepFeet(f, EnemyFoot.RIGHT)
    }

    @Test
    fun oneFrameCrossingMultipleMarkersPlaysOnlyTheMostRecentForwardContact() {
        val f = Fixture()
        f.walk(f.stepMeters(1) - 0.01)
        val destination = f.stepMeters(2) + 0.001
        f.walk(destination)
        assertStepFeet(f, EnemyFoot.LEFT)
        f.walk(destination)
        f.walk(destination + 0.01)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun oneFrameCrossingMultipleReverseMarkersUsesTheLastReverseStance() {
        val f = Fixture()
        f.walk(f.stepMeters(4) + 0.01, direction = -1f)
        val destination = f.stepMeters(3) - 0.001
        f.walk(destination, direction = -1f)
        f.walk(destination, direction = -1f)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun unloadedStepIsDroppedAndNeverQueuedAfterTheSampleBecomesReady() {
        val f = Fixture(ready = false)
        f.walk(0.0)
        val marker = f.stepMeters(1) + 0.001
        f.walk(marker)
        f.output.readyAll()
        f.walk(marker)
        f.walk(marker + 0.01)
        assertTrue(f.output.steps.isEmpty())
        f.walk(f.stepMeters(2) + 0.001)
        assertStepFeet(f, EnemyFoot.LEFT)
    }

    @Test
    fun rainLoopsOnceDucksForAContactAndRecoversInRealTime() {
        val f = Fixture()
        f.present()
        f.present()
        val rain = f.output.plays.single { it.sample == R.raw.arena_rain }
        assertEquals(-1, rain.loop)
        assertTrue(rain.priority < 1)
        f.present(events = listOf(contact(1)))
        val ducked = f.output.volumes.last { it.stream == rain.stream }.left
        assertTrue(ducked < rain.left)
        f.now += 180_000_001L
        f.present()
        assertEquals(rain.left, f.output.volumes.last { it.stream == rain.stream }.left, 0.0001f)
        assertEquals(1, f.output.count(R.raw.arena_rain))
    }

    @Test
    fun rainStopsOnPauseAndRestartsOneFreshLoopOnResume() {
        val f = Fixture()
        f.present()
        val first = f.output.plays.single { it.sample == R.raw.arena_rain }
        f.present(f.state.copy(pauseReason = PauseReason.USER))
        assertFalse(first.stream in f.output.active)
        f.present()
        f.present()
        assertEquals(2, f.output.count(R.raw.arena_rain))
        assertEquals(1, f.output.active.values.count { it.sample == R.raw.arena_rain })
    }

    @Test
    fun contactBurstKeepsAtMostTenShortStreamsAndDoesNotStealTheRainLoop() {
        val f = Fixture()
        f.present()
        val rain = f.output.plays.single { it.sample == R.raw.arena_rain }
        f.present(events = (1L..50L).map(::contact))
        assertTrue(f.output.active.values.count { it.loop == 0 } <= 10)
        assertTrue(rain.stream in f.output.active)
        assertFalse(rain.stream in f.output.stopped)
    }

    @Test
    fun ordinaryHitCannotStealAnActiveParryOrExecutionStream() {
        val f = Fixture()
        f.present(events = (1L..9L).map { contact(it, CombatImpactKind.PARRY) } +
            contact(10, CombatImpactKind.EXECUTION))
        val critical = f.output.contacts.map { it.stream }.toSet()
        f.present(events = listOf(contact(11)))
        assertTrue(f.output.active.keys.containsAll(critical))
        assertEquals(0, f.output.count(R.raw.arena_hit))
    }

    @Test
    fun closeStopsEveryStreamDetachesLoadsAndReleasesExactlyOnce() {
        val f = Fixture()
        f.present(events = listOf(contact(1)))
        val old = f.output.active.keys.toSet()
        f.audio.close()
        f.audio.close()
        f.output.readyAll()
        f.present(events = listOf(contact(2)))
        assertTrue(f.output.active.isEmpty())
        assertTrue(f.output.stopped.containsAll(old))
        assertEquals(1, f.output.releases)
        assertEquals(null, f.output.listener)
        assertEquals(1, f.output.contacts.size)
    }

    @Test
    fun missingAudioOutputStillConsumesLifecycleWithoutThrowing() {
        val state = Fixture().state
        val audio = CombatAudio(null) { 0L }
        audio.present(state, listOf(contact(1)))
        audio.present(state.copy(pauseReason = PauseReason.USER), emptyList())
        audio.close()
        audio.close()
    }

    private class Fixture(ready: Boolean = true) {
        var now = 1_000_000_000L
        val output = RecordingOutput()
        val warnings = mutableListOf<String>()
        val audio = CombatAudio(output, logWarning = warnings::add) { now }
        val state = ArenaSession(logMessage = {}, logFailure = { _, _ -> }).viewState.copy(
            roundGeneration = 1, sceneReady = true, inputReady = true, result = TrialResult.FIGHTING,
            pauseReason = null, phase = EnemyPhase.IDLE, playerMotionGeneration = 1,
            playerBladeTip = Vector3(0.2, 1.0, -0.5), playerHeadPosition = Vector3(0.0, 1.6, 0.0),
        )

        init { if (ready) output.readyAll() }

        val profile get() = arenaOpponents[state.roundNumber - 1].locomotionProfile()
        fun stepMeters(index: Int) = profile.stepEvents[index].phase * profile.strideMeters
        fun walking(gait: Double, direction: Float = 1f, phase: EnemyPhase = EnemyPhase.IDLE) =
            state.copy(enemyGaitMeters = gait, enemyMoveDirection = direction, phase = phase)
        fun walk(gait: Double, direction: Float = 1f, phase: EnemyPhase = EnemyPhase.IDLE) =
            present(walking(gait, direction, phase))

        fun present(state: ArenaViewState = this.state, events: List<EnemyCombatEvent> = emptyList()) =
            audio.present(state, events)
    }

    private data class Played(
        val stream: Int, val sample: Int, val left: Float, val right: Float,
        val priority: Int, val loop: Int, val rate: Float,
    )

    private data class Volume(val stream: Int, val left: Float, val right: Float)

    /** Records only backend effects. It deliberately does not implement bounds, expiry or priorities. */
    private class RecordingOutput : CombatAudioOutput {
        var listener: ((Int, Int) -> Unit)? = null
        val loaded = mutableListOf<Int>()
        val plays = mutableListOf<Played>()
        val active = mutableMapOf<Int, Played>()
        val stopped = mutableListOf<Int>()
        val volumes = mutableListOf<Volume>()
        var releases = 0
        private var nextStream = 1
        val contacts get() = plays.filter { it.priority >= 3 }
        val steps get() = plays.filter { it.sample == R.raw.arena_step }

        override fun onLoad(listener: ((Int, Int) -> Unit)?) { this.listener = listener }
        override fun load(resource: Int): Int { loaded += resource; return resource }
        fun ready(sample: Int, status: Int = 0) { listener?.invoke(sample, status) }
        fun readyAll() { loaded.forEach { ready(it) } }
        fun count(sample: Int) = plays.count { it.sample == sample }
        override fun play(sample: Int, left: Float, right: Float, priority: Int, loop: Int, rate: Float): Int {
            val value = Played(nextStream++, sample, left, right, priority, loop, rate)
            plays += value
            active[value.stream] = value
            return value.stream
        }
        override fun volume(stream: Int, left: Float, right: Float) { volumes += Volume(stream, left, right) }
        override fun stop(stream: Int) { stopped += stream; active.remove(stream) }
        override fun release() { releases++ }
    }

    private companion object {
        fun assertStepFeet(f: Fixture, vararg feet: EnemyFoot) {
            val played = f.output.steps
            assertEquals("One sound per crossed support-entry marker, without backlog", feet.size, played.size)
            for ((index, foot) in feet.withIndex()) {
                assertEquals("Prepared stance foot at step $index", if (foot == EnemyFoot.LEFT) 0.96f else 1.03f,
                    played[index].rate, 0f)
                assertTrue("Stereo accent follows the prepared stance foot at step $index",
                    if (foot == EnemyFoot.LEFT) played[index].left > played[index].right else played[index].right > played[index].left)
            }
        }

        fun contact(id: Long, kind: CombatImpactKind = CombatImpactKind.SOFT_HIT) = CombatImpact(
            id, kind, Vector3(0.0, 1.0, -1.0), Vector3(0.0, 0.0, 1.0), 0.7, Hand.RIGHT, 0L,
        )
    }
}
