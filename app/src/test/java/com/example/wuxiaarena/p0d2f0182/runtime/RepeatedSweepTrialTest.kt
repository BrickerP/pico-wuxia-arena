package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RepeatedSweepTrialTest {
    @Test fun fixedWristSweepsCannotClearThreeOpponents() = runRepeatedSweep(0.0)

    @Test fun addingArmTravelToTheSameSweepsDoesNotDefeatTheGuard() = runRepeatedSweep(.32)

    private fun runRepeatedSweep(armTravel: Double) {
        val session = ArenaSession(logMessage = {}, logFailure = { _, cause -> throw cause })
        val tracking = TrackingState(Hand.RIGHT)
        val impacts = mutableListOf<CombatImpact>()
        var previous = session.viewState
        var cleanDeflections = 0
        session.setArenaPresenter { state, events ->
            val batch = events.filterIsInstance<CombatImpact>()
            impacts.addAll(batch)
            val only = batch.singleOrNull()
            if (only?.kind == CombatImpactKind.GUARDED_HIT && only.appliedDamage == 0) {
                assertEquals(previous.score, state.score)
                assertEquals(previous.focus, state.focus)
                assertTrue(state.combo <= previous.combo)
                cleanDeflections++
            }
            previous = state
        }
        val spawn = Vector3(0.0, .028, -2.4)
        session.setEnemyGeometry(spawn, 1.55)
        val facing = Quaternion(0.0, 0.0, 0.0, 1.0)
        val head = ObservedPose(Vector3(0.0, 1.70625, 0.0), facing)
        val left = ObservedPose(Vector3(.11075, 1.65, .005), facing)
        val grip = Vector3(.278, 1.39625, -.45)
        val start = Quaternion(.133429, .321183, 0.0, .937571)
        val end = Quaternion(-.013068, -.075954, 0.0, .997026)
        var sequence = 0L
        var now = 1_000_000_000L
        var loadedRound = 1
        fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.SYNTHETIC)
        fun send(event: TrackingEvent) {
            val accepted = tracking.accept(event)
            assertTrue(accepted)
            session.onTrackingEvent(event, accepted, tracking.snapshot)
        }
        fun sample(fraction: Double) {
            val rotation = requireNotNull(Quaternion(
                start.x + (end.x - start.x) * fraction,
                start.y + (end.y - start.y) * fraction,
                0.0, start.w + (end.w - start.w) * fraction,
            ).normalizedOrNull())
            val hand = ObservedPose(grip + Vector3(armTravel * (fraction - .5), 0.0, 0.0), rotation)
            send(TrackingEvent.Head(stamp(), head))
            send(TrackingEvent.Controllers(stamp(), left, hand))
        }
        sample(0.0)
        assertTrue(session.startTrial())
        session.onTick(now)
        for (elapsedMillis in 20..200_000 step 20) {
            val strokeTime = (elapsedMillis - 4_000).coerceAtLeast(0)
            val stroke = strokeTime / 835
            val fraction = ((strokeTime % 835) / 450.0).coerceAtMost(1.0)
            now += 20_000_000L
            sample(if (stroke % 2 == 0) fraction else 1.0 - fraction)
            session.onTick(now)
            val state = session.viewState
            if (state.result == TrialResult.VICTORY || state.result == TrialResult.DEFEAT) break
            if (state.roundNumber != loadedRound) {
                loadedRound = state.roundNumber
                assertTrue(session.beginOpponentChange(state.roundGeneration, loadedRound))
                session.setEnemyGeometry(spawn, 1.55)
            }
        }
        val state = session.viewState
        val outcomes = impacts.groupingBy { it.kind }.eachCount()
        val summary = "arm=$armTravel, round=${state.roundNumber}, result=${state.result}, HP=${state.health}, cleanDeflections=$cleanDeflections, impacts=$outcomes"
        println(summary)
        assertEquals(summary, TrialResult.DEFEAT, state.result)
        if (armTravel == 0.0) {
            assertTrue("The rotating blade must physically graze the opponent: $summary",
                impacts.any { it.kind == CombatImpactKind.GRAZE })
            assertTrue(summary, impacts.none { it.appliedDamage > 0 })
            assertEquals(summary, 100, state.health)
        } else {
            assertTrue("Committed cuts can still deal damage: $summary", impacts.any { it.appliedDamage > 0 })
            assertTrue("The opponent must guard against repeated committed cuts: $summary", cleanDeflections > 0)
        }
    }
}
