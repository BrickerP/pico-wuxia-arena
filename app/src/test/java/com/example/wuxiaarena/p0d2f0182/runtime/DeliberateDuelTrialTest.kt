package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyPhase
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
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs
import kotlin.math.acos

/** Positive companion to RepeatedSweepTrialTest. Synthetic tracking exercises the real rules, not native input or feel. */
class DeliberateDuelTrialTest {
    private val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
    private val tracking = TrackingState(Hand.RIGHT)
    private val spawn = Vector3(0.0, .028, -2.4)
    private val eye = Vector3(0.0, 1.70625, 0.0)
    private val facing = Quaternion(0.0, 0.0, 0.0, 1.0)
    private var head = eye
    private var time = 1_000_000_000L
    private var sequence = 0L

    private data class HandPose(val offsetFromHead: Vector3, val rotation: Quaternion)
    private data class HandMove(val end: HandPose, val durationMillis: Int, val counterCut: Boolean = false)

    private val highGuard = HandPose(Vector3(.158, -.031, -.20), Quaternion(.052354, .31380, 0.0, .94804))
    private val moves = ArrayDeque<HandMove>()
    private var pose = highGuard
    private var moveStart = pose
    private var moveAgeMillis = 0
    private var lastHand = head + pose.offsetFromHead
    private var lastRotation = highGuard.rotation
    private var lastHead = head
    private var loadedRound = 1
    private var nextSide = 1
    private var waitingForFirstDefense = true
    private var counterQueued = false

    @Test
    fun guardReturnCutAndAimedThrustsCanWinAndRestartTheThreeOpponentTrial() {
        val defeated = mutableSetOf<Int>()
        var blockedOpeningAttack = false
        var landedFirstRoundCounter = false
        var bossDamage = 0
        session.setArenaPresenter { state, events ->
            for (impact in events.filterIsInstance<CombatImpact>()) {
                if (state.roundNumber == 1 && state.counterOpen &&
                    (impact.kind == CombatImpactKind.BLOCK || impact.kind == CombatImpactKind.PARRY)
                ) blockedOpeningAttack = true
                if (state.roundNumber == 1 && blockedOpeningAttack && moves.firstOrNull()?.counterCut == true &&
                    impact.appliedDamage > 0
                ) landedFirstRoundCounter = true
                if (state.roundNumber == 3) bossDamage += impact.appliedDamage
                if (impact.fatal && state.health == 0) defeated.add(state.roundNumber)
            }
        }
        session.setEnemyGeometry(spawn, 1.55)
        sample()
        assertTrue(session.startTrial())
        var elapsedMillis = 0
        while (elapsedMillis < 195_000 && session.viewState.result !in terminalStates) {
            time += tickMillis * 1_000_000L
            elapsedMillis += tickMillis
            val state = session.viewState
            if (state.roundNumber != loadedRound) {
                loadedRound = state.roundNumber
                moves.clear()
                moveAgeMillis = 0
                counterQueued = false
                assertTrue(session.beginOpponentChange(state.roundGeneration, loadedRound))
                session.setEnemyGeometry(spawn, 1.55)
            }
            if (state.result == TrialResult.FIGHTING) readOpponent(state)
            else if (moves.isEmpty()) moves.add(HandMove(highGuard, 360))
            playNextSample()
        }

        val result = session.viewState
        assertTrue("No first-round steel defense opened a counter", blockedOpeningAttack)
        assertTrue("The shoulder-line counter never dealt damage", landedFirstRoundCounter)
        assertEquals(setOf(1, 2, 3), defeated)
        assertEquals(TrialResult.VICTORY, result.result)
        assertEquals(result.initialHealth, bossDamage)
        assertEquals(0, result.health)

        time += tickMillis * 1_000_000L
        send(TrackingEvent.Discontinuity(stamp(), TrackingTarget.ALL, DiscontinuityReason.ROUND_RESET))
        time += tickMillis * 1_000_000L
        sample()
        assertEquals(TrialResult.READY, session.viewState.result)
        assertTrue(session.startTrial())
        assertEquals(TrialResult.COUNTDOWN, session.viewState.result)
        assertEquals(1, session.viewState.roundNumber)
    }

    private fun readOpponent(state: ArenaViewState) {
        val opponent = requireNotNull(state.enemyPosition)
        val raisingOverhead = state.phase == EnemyPhase.PREPARING && state.attackDirection == AttackDirection.OVERHEAD
        val holdGuard = state.roundNumber == 1 && waitingForFirstDefense &&
            !(state.phase == EnemyPhase.ACTIVE && state.attackDirection != AttackDirection.OVERHEAD)
        if (!state.counterOpen) counterQueued = false
        if (moves.isEmpty()) {
            when {
                state.counterOpen && !counterQueued -> {
                    counterQueued = true
                    waitingForFirstDefense = false
                    aimAndStrike(state, counter = true)
                }
                holdGuard -> {
                    if (state.feedback == CombatFeedback.PLAYER_HIT) waitingForFirstDefense = false
                    moves.add(HandMove(highGuard, 160))
                }
                state.frontArmored && state.attackDirection != null && !raisingOverhead && !state.counterOpen ->
                    moves.add(HandMove(highGuard, 180))
                state.playerStamina >= 27 && head.distanceTo(opponent + Vector3(0.0, eye.y, 0.0)) < 1.58 ->
                    aimAndStrike(state, counter = false)
                else -> moves.add(HandMove(highGuard, 180))
            }
        }
        if (holdGuard) return
        val avoidBlade = state.frontArmored && !raisingOverhead &&
            state.phase in setOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE)
        val stepAside = if (!avoidBlade) 0.0 else if (state.attackDirection == AttackDirection.LEFT) .32 else -.32
        val destination = Vector3((opponent.x + stepAside).coerceIn(-.52, .52), eye.y,
            (opponent.z + 1.04).coerceIn(-.65, .12))
        val walk = destination - head
        val step = .80 * tickSeconds
        head = if (walk.length() <= step) destination else head + walk * (step / walk.length())
    }

    private fun aimAndStrike(state: ArenaViewState, counter: Boolean) {
        val side = when (state.counterTargetHint) {
            CounterTargetHint.LEFT_SHOULDER -> -1
            CounterTargetHint.RIGHT_SHOULDER -> 1
            else -> nextSide
        }
        val targetHeight = when {
            counter -> 1.34
            state.frontArmored -> 1.65
            nextSide == 1 -> 1.53
            else -> 1.25
        }
        val target = requireNotNull(state.enemyPosition) + Vector3(if (counter) .10 * side else 0.0, targetHeight, 0.0)
        val drawnHand = Vector3(.19 + .09 * side, targetHeight - eye.y + .10, -.20)
        val extendedHand = Vector3(.08 - .09 * side, targetHeight - eye.y - .07, -.60)
        val thrust = state.frontArmored && !counter
        val windup = aim(drawnHand, if (thrust) target else target + Vector3(.52 * side, .35, 0.0))
        val finish = aim(extendedHand, if (thrust) target else target + Vector3(-.32 * side, -.13, 0.0))
        moves.add(HandMove(windup, if (thrust) 300 else 320))
        moves.add(HandMove(windup, 140))
        moves.add(HandMove(finish, if (thrust) 320 else 340, counterCut = counter))
        moves.add(HandMove(finish, 100))
        nextSide = -nextSide
    }

    private fun aim(hand: Vector3, target: Vector3): HandPose {
        val direction = requireNotNull((target - (head + hand)).normalizedOrNull())
        val rotation = Quaternion(direction.y, -direction.x, 0.0, 1.0 - direction.z)
        return HandPose(hand, requireNotNull(rotation.normalizedOrNull()))
    }

    private fun playNextSample() {
        val move = moves.first()
        if (moveAgeMillis == 0) moveStart = pose
        moveAgeMillis += tickMillis
        val progress = (moveAgeMillis.toDouble() / move.durationMillis).coerceAtMost(1.0)
        val weight = progress * progress * (3.0 - 2.0 * progress)
        val from = moveStart.rotation
        val to = move.end.rotation
        val rotation = Quaternion(from.x + (to.x - from.x) * weight, from.y + (to.y - from.y) * weight,
            from.z + (to.z - from.z) * weight, from.w + (to.w - from.w) * weight)
        pose = HandPose(moveStart.offsetFromHead * (1.0 - weight) + move.end.offsetFromHead * weight,
            requireNotNull(rotation.normalizedOrNull()))
        sample()
        if (moveAgeMillis >= move.durationMillis) {
            moves.removeFirst()
            moveAgeMillis = 0
        }
    }

    private fun sample() {
        val hand = head + pose.offsetFromHead
        val shoulder = head + Vector3(.16, -.18, 0.0)
        val dot = abs(lastRotation.x * pose.rotation.x + lastRotation.y * pose.rotation.y +
            lastRotation.z * pose.rotation.z + lastRotation.w * pose.rotation.w)
        assertTrue("Hand beyond arm's reach", shoulder.distanceTo(hand) <= .75)
        assertTrue("Implausible hand translation", lastHand.distanceTo(hand) / tickSeconds <= 4.5)
        assertTrue("Implausible wrist rotation", 2.0 * acos(dot.coerceIn(0.0, 1.0)) / tickSeconds <= 6.5)
        assertTrue("Implausible head movement", lastHead.distanceTo(head) / tickSeconds <= .81)
        lastHand = hand
        lastHead = head
        lastRotation = pose.rotation
        send(TrackingEvent.Head(stamp(), ObservedPose(head, facing)))
        send(TrackingEvent.Controllers(stamp(), ObservedPose(head + Vector3(-.28, -.27, -.32), facing),
            ObservedPose(hand, pose.rotation)))
        session.onTick(time)
    }

    private fun stamp() = ObservationStamp(sequence++, time, 1L, InputOrigin.SYNTHETIC)

    private fun send(event: TrackingEvent) {
        val accepted = tracking.accept(event)
        assertTrue(accepted)
        session.onTrackingEvent(event, accepted, tracking.snapshot)
    }

    private companion object {
        const val tickMillis = 20
        const val tickSeconds = tickMillis / 1_000.0
        val terminalStates = setOf(TrialResult.VICTORY, TrialResult.DEFEAT)
    }
}
