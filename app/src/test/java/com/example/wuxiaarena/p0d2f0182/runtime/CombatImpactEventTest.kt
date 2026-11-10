package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.combat.PlayerMotionFrame
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Exercises the coordinator boundary with recognized frames, independently of device input. */
class CombatImpactEventTest {
    private val enemy = Vector3(0.0, 0.0, -1.2)
    private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

    @Test
    fun aLaterUiPromptCannotReplaceAnAcceptedContactInTheSameBatch() {
        val resolver = PlayerCombatResolver()
        val frame = recognizedStrike(resolver, 1, 0L, 1)
        val session = ArenaSession(logMessage = {}, logFailure = { _, failure -> throw failure })
        session.setEnemyGeometry(enemy, 2.0)
        val presentations = mutableListOf<Pair<ArenaViewState, List<EnemyCombatEvent>>>()
        session.setArenaPresenter { state, events -> presentations += state to events }
        val events = mutableListOf<EnemyCombatEvent>()

        applyMotion(session, frame, events)
        applyMotion(session, frame.copy(strike = null, skillGesture = true), events)
        publish(session, events)

        assertEquals(CombatFeedback.LOW_FOCUS, presentations.last().first.feedback)
        val impact = presentations.last().second.filterIsInstance<CombatImpact>().single()
        val strike = requireNotNull(frame.strike)
        assertEquals(CombatImpactKind.SOFT_HIT, impact.kind)
        assertEquals(Hand.LEFT, impact.hand)
        assertEquals(strike.contact.point, impact.point)
        assertEquals(strike.contact.normal, impact.normal)
        assertTrue(impact.strength in 0.0..1.0)
        assertEquals(1, events.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().size)

        val nextFrame = recognizedStrike(resolver, 5, 1_000_000_000L, 2)
        val nextEvents = mutableListOf<EnemyCombatEvent>()
        applyMotion(session, nextFrame, nextEvents)
        val nextImpact = nextEvents.filterIsInstance<CombatImpact>().single()
        assertTrue(nextImpact.id > impact.id)
    }

    @Test
    fun rejectedFocusRangeAndStaminaActionsDoNotEmitPhysicalContacts() {
        val frame = recognizedStrike(PlayerCombatResolver(), 1, 0L, 1)
        val session = ArenaSession(logMessage = {}, logFailure = { _, failure -> throw failure })
        session.setEnemyGeometry(enemy, 2.0)
        val events = mutableListOf<EnemyCombatEvent>()
        val healthBefore = session.viewState.health

        applyMotion(session, frame.copy(strike = null, skillGesture = true), events)
        assertEquals(CombatFeedback.LOW_FOCUS, session.viewState.feedback)
        applyMotion(session, frame.copy(strike = null, skillGesture = true,
            headPosition = Vector3(0.0, 1.6, 4.0)), events)
        assertEquals(CombatFeedback.OUT_OF_RANGE, session.viewState.feedback)
        ArenaSession::class.java.getDeclaredField("stamina").apply {
            isAccessible = true
            setDouble(session, 11.0)
        }
        applyMotion(session, frame, events)

        assertEquals(CombatFeedback.LOW_STAMINA, session.viewState.feedback)
        assertTrue(events.filterIsInstance<CombatImpact>().isEmpty())
        assertEquals(healthBefore, session.viewState.health)
    }

    private fun recognizedStrike(
        resolver: PlayerCombatResolver,
        firstSequence: Long,
        startAt: Long,
        epoch: Long,
    ): PlayerMotionFrame {
        resolver.observe(snapshot(firstSequence, startAt, epoch, 0.0), enemy)
        return requireNotNull(resolver.observe(
            snapshot(firstSequence + 2, startAt + 100_000_000L, epoch, -0.2), enemy,
        )).also { requireNotNull(it.strike) }
    }

    private fun snapshot(sequence: Long, time: Long, epoch: Long, handZ: Double): TrackingSnapshot {
        val headStamp = ObservationStamp(sequence - 1, time, epoch, InputOrigin.SYNTHETIC)
        val handStamp = ObservationStamp(sequence, time, epoch, InputOrigin.SYNTHETIC)
        return TrackingSnapshot(
            PoseObservation(headStamp, ObservedPose(Vector3(0.0, 1.6, 0.0), rotation)),
            PoseObservation(handStamp, ObservedPose(Vector3(0.0, 0.95, handZ), rotation)),
            PoseObservation(handStamp, ObservedPose(Vector3(0.7, 1.2, 0.0), rotation)),
            Hand.LEFT, 0, 0, 0,
        )
    }

    private fun applyMotion(session: ArenaSession, frame: PlayerMotionFrame, events: MutableList<EnemyCombatEvent>) {
        ArenaSession::class.java.getDeclaredMethod(
            "applyPlayerMotion", PlayerMotionFrame::class.java, List::class.java,
        ).apply { isAccessible = true }.invoke(session, frame, events)
    }

    private fun publish(session: ArenaSession, events: List<EnemyCombatEvent>) {
        ArenaSession::class.java.getDeclaredMethod("publish", List::class.java)
            .apply { isAccessible = true }.invoke(session, events)
    }
}
