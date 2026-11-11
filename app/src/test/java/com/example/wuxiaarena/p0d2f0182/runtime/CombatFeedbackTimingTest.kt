package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CombatFeedbackTimingTest {
    @Test
    fun aTrackedStrikeCarriesItsActualDamageAndTheFirstPresentationRetainsTheHold() {
        val fixture = Fixture()
        fixture.strike()

        val impact = fixture.impacts.single()
        val damaged = fixture.events.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single()
        assertEquals(damaged.appliedDamage, impact.appliedDamage)
        assertEquals(100 - fixture.session.viewState.health, impact.appliedDamage)
        assertEquals(HitZone.BODY, impact.zone)
        assertFalse(impact.fatal)
        assertEquals(70_000_000L, CombatFeedbackProfile.hitStopNanos(impact))
        assertTrue(fixture.presentations.last().first.hitStop)
        assertEquals(EnemyPhase.HIT, fixture.session.viewState.phase)
        assertEquals(0L, fixture.session.viewState.phaseElapsedNanos)

        fixture.tickBy(35_000_000L)
        assertTrue(fixture.session.viewState.hitStop)
        assertEquals(0L, fixture.session.viewState.phaseElapsedNanos)
        fixture.tickBy(35_000_000L)
        assertFalse(fixture.session.viewState.hitStop)
        assertEquals(0L, fixture.session.viewState.phaseElapsedNanos)
        fixture.tickBy(1_000_000L)
        assertEquals(1_000_000L, fixture.session.viewState.phaseElapsedNanos)
        assertEquals(1, fixture.impacts.size)
    }

    @Test
    fun overkillUsesRemainingHealthAndAFatalHoldBeforeTheDeathSlowdown() {
        val fixture = Fixture(enemyHealth = 6)
        fixture.strike()

        val impact = fixture.impacts.single()
        assertEquals(6, impact.appliedDamage)
        assertTrue(impact.fatal)
        assertEquals(150_000_000L, CombatFeedbackProfile.hitStopNanos(impact))
        assertEquals(TrialResult.ROUND_CLEAR, fixture.session.viewState.result)
        assertTrue(fixture.session.viewState.hitStop)
        assertEquals(0f, fixture.session.viewState.deathElapsedSeconds, 0f)

        fixture.tickBy(100_000_000L)
        assertTrue(fixture.session.viewState.hitStop)
        assertEquals(0f, fixture.session.viewState.deathElapsedSeconds, 0f)
        fixture.tickBy(50_000_000L)
        assertFalse(fixture.session.viewState.hitStop)
        assertEquals(0f, fixture.session.viewState.deathElapsedSeconds, 0f)
        fixture.tickBy(220_000_000L)
        assertEquals(0.077f, fixture.session.viewState.deathElapsedSeconds, 0.000001f)
        fixture.tickBy(180_000_000L)
        assertEquals(0.1985f, fixture.session.viewState.deathElapsedSeconds, 0.000001f)
        fixture.tickBy(100_000_000L)
        assertEquals(0.2985f, fixture.session.viewState.deathElapsedSeconds, 0.000001f)
        assertEquals(TrialResult.ROUND_CLEAR, fixture.session.viewState.result)
    }

    @Test
    fun defenseContactsHaveNoEnemyDamageAndUseTheirOwnHold() {
        val block = impact(CombatImpactKind.BLOCK)
        val parry = impact(CombatImpactKind.PARRY)
        assertEquals(0, block.appliedDamage)
        assertEquals(null, block.zone)
        assertFalse(block.fatal)
        assertEquals(35_000_000L, CombatFeedbackProfile.hitStopNanos(block))
        assertEquals(95_000_000L, CombatFeedbackProfile.hitStopNanos(parry))
        assertEquals(0L, CombatFeedbackProfile.hitStopNanos(impact(CombatImpactKind.PLAYER_HIT)))
    }

    @Test
    fun theNextOpponentWaitsForTheUnscaledFallDurationAndStartsWithoutOldFeedbackTime() {
        val fixture = Fixture(enemyHealth = 6)
        fixture.strike()
        val deathDuration = 3_200_000_000L + 150_000_000L +
            CombatFeedbackProfile.DEATH_SLOWDOWN_DELAY_NANOS
        fixture.tickBy(deathDuration - 1L)
        assertEquals(TrialResult.ROUND_CLEAR, fixture.session.viewState.result)
        assertEquals(3.2f, fixture.session.viewState.deathElapsedSeconds, 0.000001f)

        fixture.tickBy(1L)
        val next = fixture.session.viewState
        assertEquals(TrialResult.COUNTDOWN, next.result)
        assertEquals(2, next.roundNumber)
        assertEquals(125, next.health)
        assertFalse(next.hitStop)
        assertEquals(0f, next.deathElapsedSeconds, 0f)
        assertEquals(Vector3(0.0, 0.0, 0.0), next.enemyRecoilOffset)
    }

    @Test
    fun theProfileDistinguishesHeadArmorGuardSkillAndExecution() {
        assertEquals(90_000_000L, CombatFeedbackProfile.hitStopNanos(
            impact(CombatImpactKind.SOFT_HIT).copy(zone = HitZone.HEAD),
        ))
        assertEquals(85_000_000L, CombatFeedbackProfile.hitStopNanos(impact(CombatImpactKind.HARD_HIT)))
        assertEquals(30_000_000L, CombatFeedbackProfile.hitStopNanos(impact(CombatImpactKind.GUARDED_HIT)))
        assertEquals(100_000_000L, CombatFeedbackProfile.hitStopNanos(impact(CombatImpactKind.SKILL)))
        assertEquals(150_000_000L, CombatFeedbackProfile.hitStopNanos(impact(CombatImpactKind.EXECUTION)))
        assertEquals(150_000_000L, CombatFeedbackProfile.hitStopNanos(
            impact(CombatImpactKind.HARD_HIT).copy(appliedDamage = 1, fatal = true),
        ))
    }

    @Test
    fun deathPresentationIsContinuousMonotonicAndReturnsToRealTimeSpeed() {
        val times = listOf(0L, 1L, 219_999_999L, 220_000_000L, 220_000_001L,
            399_999_999L, 400_000_000L, 400_000_001L, 900_000_000L)
        val positions = times.map(CombatFeedbackProfile::deathElapsedNanos)
        assertTrue(positions.zipWithNext().all { (before, after) -> after >= before })
        assertEquals(77_000_000L, CombatFeedbackProfile.deathElapsedNanos(220_000_000L))
        assertEquals(198_500_000L, CombatFeedbackProfile.deathElapsedNanos(400_000_000L))
        assertEquals(698_500_000L, CombatFeedbackProfile.deathElapsedNanos(900_000_000L))
        assertEquals(500_000_000L, positions.last() - positions[6])
        assertTrue(positions[4] - positions[2] <= 2L)
        assertTrue(positions[7] - positions[5] <= 2L)
    }

    @Test
    fun pausingAndResumingDeathDoesNotCatchUpThePresentationClock() {
        val fixture = Fixture(enemyHealth = 6)
        fixture.strike()
        fixture.tickBy(250_000_000L)
        val before = fixture.session.viewState.deathElapsedSeconds
        fixture.control(DiscontinuityReason.USER_PAUSED, fixture.now + 1L)
        val pauseId = requireNotNull(fixture.session.viewState.pauseId)
        fixture.tickBy(10_000_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)

        fixture.observe(fixture.now + 1L, -0.2)
        assertTrue(fixture.session.confirmResume(pauseId))
        fixture.tickBy(1_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)
        fixture.tickBy(10_000_000L)
        assertTrue(fixture.session.viewState.deathElapsedSeconds > before)
    }

    @Test
    fun resettingDuringAFatalHoldClearsDeathRecoilAndStopState() {
        val fixture = Fixture(enemyHealth = 6)
        fixture.strike()
        fixture.control(DiscontinuityReason.ROUND_RESET, fixture.now + 1L)

        val reset = fixture.session.viewState
        assertEquals(TrialResult.READY, reset.result)
        assertEquals(100, reset.health)
        assertFalse(reset.hitStop)
        assertEquals(0f, reset.deathElapsedSeconds, 0f)
        assertEquals(Vector3(0.0, 0.0, 0.0), reset.enemyRecoilOffset)
    }

    @Test
    fun theViewExposesRecognizedSpeedRestAndTheGenerationChangeOnReset() {
        val fixture = Fixture()
        fixture.strike()
        val moving = fixture.session.viewState
        assertEquals(2.0, moving.playerBladeTipSpeed, 0.000001)
        assertFalse(moving.playerBladeAtRest)
        assertTrue(moving.playerMotionGeneration > 0L)
        assertTrue(moving.playerBladeTip != null)

        fixture.control(DiscontinuityReason.ROUND_RESET, fixture.now + 1L)
        val reset = fixture.session.viewState
        assertEquals(0.0, reset.playerBladeTipSpeed, 0.0)
        assertTrue(reset.playerBladeAtRest)
        assertTrue(reset.playerMotionGeneration > moving.playerMotionGeneration)
        assertEquals(null, reset.playerBladeTip)
    }

    @Test
    fun trackingInterruptionFreezesDeathUntilFreshInputAndConfirmedResume() {
        val fixture = Fixture(enemyHealth = 6)
        fixture.strike()
        fixture.tickBy(250_000_000L)
        val before = fixture.session.viewState.deathElapsedSeconds
        fixture.control(DiscontinuityReason.PROVIDER_UNAVAILABLE, fixture.now + 1L)
        val pauseId = requireNotNull(fixture.session.viewState.pauseId)
        fixture.tickBy(10_000_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)
        assertFalse(fixture.session.viewState.inputReady)

        fixture.observe(fixture.now + 1L, -0.2)
        fixture.tickBy(1_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)
        assertTrue(fixture.session.confirmResume(pauseId))
        fixture.tickBy(1_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)
        fixture.tickBy(10_000_000L)
        assertTrue(fixture.session.viewState.deathElapsedSeconds > before)
    }

    @Test
    fun removingTheSceneFreezesDeathUntilTheSceneAndInputAreReestablished() {
        val fixture = Fixture(enemyHealth = 6)
        fixture.strike()
        fixture.tickBy(250_000_000L)
        val before = fixture.session.viewState.deathElapsedSeconds
        fixture.session.setEnemyGeometry(null, 0.0)
        fixture.tickBy(10_000_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)
        assertFalse(fixture.session.viewState.sceneReady)

        fixture.session.setEnemyGeometry(Vector3(0.0, 0.0, -1.2), 2.0)
        fixture.observe(fixture.now + 1L, -0.2)
        val pauseId = requireNotNull(fixture.session.viewState.pauseId)
        assertTrue(fixture.session.confirmResume(pauseId))
        fixture.tickBy(1_000_000L)
        assertEquals(before, fixture.session.viewState.deathElapsedSeconds, 0f)
        fixture.tickBy(10_000_000L)
        assertTrue(fixture.session.viewState.deathElapsedSeconds > before)
    }

    @Test
    fun anAbsentPresenterDoesNotPermanentlyFreezeCombatOrReplayTheContactLater() {
        val fixture = Fixture()
        fixture.session.setArenaPresenter(null)
        fixture.strike()
        assertTrue(fixture.session.viewState.hitStop)
        val healthAfterHit = fixture.session.viewState.health

        fixture.tickBy(70_000_000L)
        assertFalse(fixture.session.viewState.hitStop)
        fixture.tickBy(1_000_000L)
        assertEquals(1_000_000L, fixture.session.viewState.phaseElapsedNanos)
        val recoveredEvents = mutableListOf<EnemyCombatEvent>()
        fixture.session.setArenaPresenter { _, batch -> recoveredEvents += batch }
        assertTrue(recoveredEvents.isEmpty())
        assertEquals(healthAfterHit, fixture.session.viewState.health)
    }

    @Test
    fun aFailingPresenterReportsTheFailureAndDeathCanStillMakeFiniteProgress() {
        val fixture = Fixture(enemyHealth = 6)
        val failure = IllegalStateException("contact presentation unavailable")
        var receivedHold = false
        fixture.session.setArenaPresenter { state, batch ->
            if (batch.any { it is CombatImpact }) {
                receivedHold = state.hitStop
                throw failure
            }
        }
        fixture.strike()
        assertTrue(receivedHold)
        assertEquals(listOf(failure), fixture.failures)
        assertTrue(fixture.session.viewState.hitStop)

        fixture.tickBy(150_000_000L)
        assertFalse(fixture.session.viewState.hitStop)
        fixture.tickBy(400_000_000L)
        assertEquals(0.1985f, fixture.session.viewState.deathElapsedSeconds, 0.000001f)
        assertEquals(listOf(failure), fixture.failures)
        val recoveredEvents = mutableListOf<EnemyCombatEvent>()
        fixture.session.setArenaPresenter { _, batch -> recoveredEvents += batch }
        assertTrue(recoveredEvents.isEmpty())
    }

    @Test(expected = IllegalArgumentException::class)
    fun negativeDeathTimeIsRejected() {
        CombatFeedbackProfile.deathElapsedNanos(-1L)
    }

    @Test(expected = IllegalArgumentException::class)
    fun fatalContactsWithoutActualDamageAreRejected() {
        impact(CombatImpactKind.SOFT_HIT).copy(fatal = true)
    }

    @Test(expected = IllegalArgumentException::class)
    fun negativeActualDamageIsRejected() {
        impact(CombatImpactKind.SOFT_HIT).copy(appliedDamage = -1)
    }

    private fun impact(kind: CombatImpactKind) = CombatImpact(
        1L, kind, Vector3(0.0, 1.0, -1.0), Vector3(0.0, 0.0, 1.0), 0.7, Hand.LEFT, 0L,
    )

    private class Fixture(enemyHealth: Int = 100) {
        val failures = mutableListOf<Throwable>()
        val session = ArenaSession(logMessage = {}, logFailure = { _, error -> failures += error })
        val events = mutableListOf<EnemyCombatEvent>()
        val presentations = mutableListOf<Pair<ArenaViewState, List<EnemyCombatEvent>>>()
        val impacts get() = events.filterIsInstance<CombatImpact>()
        var now = 0L
            private set
        private var sequence = 0L
        private val tracking = TrackingState(Hand.LEFT)
        private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

        init {
            session.setEnemyGeometry(Vector3(0.0, 0.0, -1.2), 2.0)
            observe(0L, 0.0)
            session.setArenaPresenter { state, batch ->
                presentations += state to batch
                events += batch
            }
            assertTrue(session.startTrial())
            session.onTick(0L)
            tickBy(3_000_000_000L)
            assertEquals(TrialResult.FIGHTING, session.viewState.result)
            if (enemyHealth != 100) {
                // Seed remaining health, then exercise the normal tracking and tick entry points.
                ArenaSession::class.java.getDeclaredField("combat").apply {
                    isAccessible = true
                    set(session, EnemyCombatStateMachine(enemyHealth))
                }
            }
        }

        fun strike() {
            observe(now + 10_000_000L, 0.0)
            observe(now + 110_000_000L, -0.2)
            // The remainder exceeds the entire ordinary hold inside this single tick.
            tickBy(250_000_000L)
        }

        fun observe(at: Long, handZ: Double) {
            accept(TrackingEvent.Head(stamp(at), ObservedPose(Vector3(0.0, 1.6, 0.0), rotation)))
            accept(TrackingEvent.Controllers(stamp(at + 1L),
                // Aim through the new canonical guard torso, authored about 0.25 m left of the legacy idle proxy.
                ObservedPose(Vector3(-0.25, 0.95, handZ), rotation),
                ObservedPose(Vector3(0.7, 1.2, 0.0), rotation)))
        }

        fun control(reason: DiscontinuityReason, at: Long) {
            accept(TrackingEvent.Discontinuity(stamp(at), TrackingTarget.ALL, reason))
        }

        fun tickBy(delta: Long) {
            now += delta
            session.onTick(now)
        }

        private fun stamp(at: Long) = ObservationStamp(sequence++, at, 1L, InputOrigin.SYNTHETIC)

        private fun accept(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }
    }
}
