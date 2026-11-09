package com.example.wuxiaarena.p0d2f0182.runtime

import android.util.Log
import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.combat.PlayerMotionFrame
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.input.DesktopCombatInput
import kotlin.math.atan2
import kotlin.math.hypot
import kotlin.math.roundToInt

typealias HandPosePresenter = (ObservedPose?) -> Unit

internal enum class TrialResult { READY, COUNTDOWN, FIGHTING, ROUND_CLEAR, VICTORY, DEFEAT }
internal enum class CombatFeedback {
    HIT, HEADSHOT, GUARDED_HIT, BLOCK, PARRY, DODGE, PLAYER_HIT,
    GUARD_BREAK, SKILL, EXECUTION, LOW_STAMINA, LOW_FOCUS, OUT_OF_RANGE, TIMEOUT,
}

internal data class ArenaViewState(
    val roundGeneration: Long,
    val trialStarted: Boolean,
    val sceneReady: Boolean,
    val simulationNanos: Long,
    val phase: EnemyPhase,
    val phaseElapsedNanos: Long,
    val phaseRemainingNanos: Long?,
    val attackId: Long?,
    val attackDirection: AttackDirection?,
    val health: Int,
    val initialHealth: Int,
    val guarding: Boolean,
    val hitReaction: HitReaction?,
    val pauseReason: PauseReason?,
    val pauseId: Long?,
    val inputReady: Boolean,
    val actionReady: Boolean,
    val resumeReady: Boolean,
    val inputOrigin: InputOrigin?,
    val headQuality: TrackingQuality?,
    val dominantHandQuality: TrackingQuality?,
    val targetInRange: Boolean?,
    val canStartAttack: Boolean?,
    val result: TrialResult = TrialResult.READY,
    val playerHealth: Int = 100,
    val playerStamina: Int = 100,
    val focus: Int = 50,
    val score: Int = 0,
    val bestScore: Int = 0,
    val combo: Int = 0,
    val roundNumber: Int = 1,
    val roundCount: Int = 3,
    val remainingSeconds: Int = 180,
    val countdownSeconds: Int = 0,
    val feedback: CombatFeedback? = null,
    val feedbackSequence: Long = 0,
    val enemyPosition: Vector3? = null,
    val enemyYawRadians: Float = 0f,
    val hitStop: Boolean = false,
    val executionAvailable: Boolean = false,
    val executing: Boolean = false,
    val deathElapsedSeconds: Float = 0f,
    val dominantHand: Hand = Hand.RIGHT,
)

internal typealias ArenaPresenter = (ArenaViewState, List<EnemyCombatEvent>) -> Unit

/** One-thread owner of trial state, tracking gates and presentation delivery. */
internal class ArenaSession(
    private val logMessage: (String) -> Unit = { message -> Log.i("ArenaCombat", message) },
    private val logFailure: (String, Throwable) -> Unit = { context, error ->
        Log.e("ArenaCombat", context, error)
    },
    savedBestScore: Int = 0,
) {
    private var combat = EnemyCombatStateMachine()
    private var initialHealth = combat.health
    private val motion = PlayerCombatResolver()
    private val pendingMotion = ArrayDeque<PlayerMotionFrame>()
    private var latestMotion: PlayerMotionFrame? = null
    private var queuedStrikeId = -1L
    private var lastSkillReceipt = Long.MIN_VALUE
    private var result = TrialResult.READY
    private var playerHealth = 100
    private var stamina = 100.0
    private var focus = 50.0
    private var score = 0
    private var bestScore = savedBestScore.coerceAtLeast(0)
    private var combo = 0
    private var lastHitAt = -1L
    private var roundNumber = 1
    private var matchNanos = 0L
    private var countdownNanos = 0L
    private var intermissionNanos = 0L
    private var executionActive = false
    private var hitStopNanos = 0L
    private var staggerUntil = 0L
    private var feedback: CombatFeedback? = null
    private var feedbackUntil = 0L
    private var feedbackSequence = 0L
    private var sceneAvailable = false
    private var enemySpawn: Vector3? = null
    private var enemyYaw = 0f
    private var observedAttackId: Long? = null
    private var attackHeadBaseline: Vector3? = null
    private var resolvedContactId: Long? = null
    private var roundGeneration = 0L
    private var trialStarted = false
    private var enemyPosition: Vector3? = null
    private var enemyReachMeters = 0.0
    private var lastTickTime: Long? = null
    private var lastReportTime: Long? = null
    private var lastReportedHead: Vector3? = null
    private var lastReportedHand: Vector3? = null
    private var lastReportedEligibility: Boolean? = null
    private var hadReadyInput = false
    private var reportedWaiting = false
    private var playerHandPresenter: HandPosePresenter? = null
    private var arenaPresenter: ArenaPresenter? = null
    private var latestTrackingSnapshot: TrackingSnapshot? = null
    private var lastAcceptedStamp: ObservationStamp? = null
    private var actionRequiredAfterSequence = -1L
    private var actionBaseline: ActionBaseline? = null

    private data class ActionBaseline(
        val hand: Hand,
        val coordinateEpoch: Long,
        val headContinuity: Long,
        val handContinuity: Long,
    )

    val viewState: ArenaViewState
        get() {
            val snapshot = latestTrackingSnapshot
            val hand = snapshot?.let { if (it.dominantHand == Hand.LEFT) it.left else it.right }
            val inputReady = snapshot?.hasRequiredObservations == true
            val sceneReady = sceneAvailable && enemyPosition != null
            val actionReady = sceneReady && inputReady && actionBaseline != null &&
                actionBaseline == snapshot?.actionIdentity()
            val targetInRange = currentTargetInRange()
            return ArenaViewState(
                roundGeneration = roundGeneration,
                trialStarted = trialStarted,
                sceneReady = sceneReady,
                simulationNanos = combat.simulationNanos,
                phase = combat.phase,
                phaseElapsedNanos = combat.phaseElapsedNanos,
                phaseRemainingNanos = combat.nanosUntilPhaseTransition,
                attackId = combat.currentAttackId,
                attackDirection = combat.currentAttackDirection,
                health = combat.health,
                initialHealth = initialHealth,
                guarding = combat.guarding,
                hitReaction = combat.hitReaction,
                pauseReason = combat.pauseReason,
                pauseId = combat.currentPauseId,
                inputReady = inputReady,
                actionReady = actionReady,
                resumeReady = combat.currentPauseId != null && actionReady,
                inputOrigin = hand?.stamp?.origin,
                headQuality = snapshot?.head?.pose?.quality,
                dominantHandQuality = hand?.pose?.quality,
                targetInRange = targetInRange,
                canStartAttack = targetInRange?.let(combat::canStartAttack),
                result = result,
                playerHealth = playerHealth,
                playerStamina = stamina.roundToInt(),
                focus = focus.roundToInt(),
                score = score,
                bestScore = bestScore,
                combo = combo,
                roundNumber = roundNumber,
                remainingSeconds = ((MATCH_DURATION - matchNanos).coerceAtLeast(0L) + SECOND - 1L).div(SECOND).toInt(),
                countdownSeconds = when (result) {
                    TrialResult.COUNTDOWN -> ((COUNTDOWN_DURATION - countdownNanos).coerceAtLeast(0L) + SECOND - 1L).div(SECOND).toInt()
                    TrialResult.ROUND_CLEAR -> ((intermissionDuration() - intermissionNanos).coerceAtLeast(0L) + SECOND - 1L).div(SECOND).toInt()
                    else -> 0
                },
                feedback = feedback,
                feedbackSequence = feedbackSequence,
                enemyPosition = enemyPosition,
                enemyYawRadians = enemyYaw,
                hitStop = hitStopNanos > 0L,
                executionAvailable = result == TrialResult.FIGHTING && combat.health in 1..executionThreshold(),
                executing = executionActive,
                deathElapsedSeconds = ((intermissionNanos - 110_000_000L).coerceAtLeast(0L) / 1_000_000_000.0 *
                    if (executionActive) 0.65 else 1.0).toFloat(),
                dominantHand = snapshot?.dominantHand ?: Hand.RIGHT,
            )
        }

    fun setArenaPresenter(presenter: ArenaPresenter?) {
        arenaPresenter = presenter
        publish()
    }

    fun startTrial(): Boolean {
        val state = viewState
        if (result != TrialResult.READY || trialStarted || !state.sceneReady || !state.inputReady || state.pauseReason != null) return false
        trialStarted = true
        result = TrialResult.COUNTDOWN
        countdownNanos = 0L
        lastTickTime = null
        publish()
        return true
    }

    /** Called after the input owner drains pending controls and observations. */
    fun confirmResume(pauseId: Long): Boolean {
        if (result == TrialResult.VICTORY || result == TrialResult.DEFEAT) return false
        val state = viewState
        if (state.pauseId != pauseId || !state.resumeReady) return false
        val events = combat.tryResume(state.inputReady, state.actionReady, pauseId)
        if (combat.pauseReason != null) return false
        clearMotion()
        lastTickTime = null
        publish(events)
        return true
    }

    /** The input owner calls this once after all drains, using its receipt clock. */
    fun onTick(nowNanos: Long) {
        val targetInRange = currentTargetInRange()
        val terminal = result == TrialResult.VICTORY || result == TrialResult.DEFEAT
        val canAdvance = if (result == TrialResult.ROUND_CLEAR) {
            combat.pauseReason != PauseReason.USER
        } else {
            targetInRange != null && combat.pauseReason == null && viewState.actionReady
        }
        if (!trialStarted || terminal || !canAdvance) {
            lastTickTime = null
            publish()
            return
        }
        val previous = lastTickTime
        lastTickTime = nowNanos
        if (previous == null || nowNanos < previous) {
            publish()
            return
        }
        val delta = nowNanos - previous
        if (delta < 0L || delta > Long.MAX_VALUE - combat.simulationNanos) {
            logMessage("Trial clock interval is unavailable; rebuilding its baseline")
            publish()
            return
        }
        val events = mutableListOf<EnemyCombatEvent>()
        var remaining = delta
        var intervalEnd = previous
        while (remaining > 0L) {
            val step = minOf(remaining, 100_000_000L)
            intervalEnd += step
            remaining -= step
            when (result) {
                TrialResult.COUNTDOWN -> {
                    countdownNanos += step
                    if (countdownNanos >= COUNTDOWN_DURATION) {
                        result = TrialResult.FIGHTING
                        clearMotion()
                        break
                    }
                }
                TrialResult.ROUND_CLEAR -> {
                    hitStopNanos = (hitStopNanos - step).coerceAtLeast(0L)
                    intermissionNanos += step
                    if (intermissionNanos >= intermissionDuration()) {
                        if (roundNumber == 3) {
                            result = TrialResult.VICTORY
                            score += 100 + playerHealth + viewState.remainingSeconds
                            bestScore = maxOf(bestScore, score)
                        } else {
                            beginNextRound(events)
                        }
                        break
                    }
                }
                TrialResult.FIGHTING -> advanceFight(step, intervalEnd, events)
                TrialResult.READY, TrialResult.VICTORY, TrialResult.DEFEAT -> break
            }
            if (combat.pauseReason != null && result != TrialResult.ROUND_CLEAR) break
        }
        publish(events)
    }

    private fun advanceFight(delta: Long, now: Long, events: MutableList<EnemyCombatEvent>) {
        val available = (MATCH_DURATION - matchNanos).coerceAtLeast(0L)
        val interval = minOf(delta, available)
        val frameStart = now - delta
        val playableUntil = frameStart + interval
        matchNanos += interval
        val regeneration = if (latestMotion?.guardDirection != null) 4.0 else 14.0
        stamina = (stamina + interval / 1_000_000_000.0 * regeneration).coerceAtMost(100.0)
        if (feedback != null && matchNanos >= feedbackUntil) feedback = null
        if (lastHitAt >= 0L && matchNanos - lastHitAt > COMBO_WINDOW) combo = 0
        moveEnemy(interval)
        var advanced = 0L
        while (pendingMotion.isNotEmpty()) {
            if (pendingMotion.first().receivedAtNanos > playableUntil) break
            val frame = pendingMotion.removeFirst()
            if (now.toDouble() - frame.receivedAtNanos.toDouble() > 250_000_000.0) continue
            val offset = (frame.receivedAtNanos - frameStart).coerceIn(advanced, interval)
            advanceEnemy(offset - advanced, events, deferEndContact = true)
            advanced = offset
            if (result != TrialResult.FIGHTING) break
            applyPlayerMotion(frame, events)
            resolveEnemyContact(events)
        }
        if (result == TrialResult.FIGHTING) advanceEnemy(interval - advanced, events, deferEndContact = false)
        if (result == TrialResult.FIGHTING && matchNanos >= MATCH_DURATION) finishDefeat(CombatFeedback.TIMEOUT, events)
    }

    private fun advanceEnemy(delta: Long, events: MutableList<EnemyCombatEvent>, deferEndContact: Boolean) {
        var remaining = delta
        val frozen = minOf(remaining, hitStopNanos)
        hitStopNanos -= frozen
        remaining -= frozen
        while (remaining > 0L && result == TrialResult.FIGHTING && combat.pauseReason == null) {
            synchronizeAttackBaseline()
            if (contactDue()) resolveEnemyContact(events)
            if (result != TrialResult.FIGHTING || combat.pauseReason != null) break
            val untilContact = if (combat.phase == EnemyPhase.ACTIVE && resolvedContactId != combat.currentAttackId) {
                (checkNotNull(combat.currentAttackDirection).activeNanos / 2L - combat.phaseElapsedNanos).coerceAtLeast(0L)
            } else {
                Long.MAX_VALUE
            }
            val interval = minOf(remaining, combat.nanosUntilPhaseTransition ?: remaining, untilContact)
            if (interval == 0L) {
                resolveEnemyContact(events)
                continue
            }
            collect(combat.advanceBy(interval, currentTargetInRange() == true, AttackDirection.OVERHEAD), events)
            remaining -= interval
            if (contactDue() && (remaining > 0L || !deferEndContact)) resolveEnemyContact(events)
            if (result == TrialResult.FIGHTING) {
                collect(combat.tryStartAttack(AttackDirection.OVERHEAD, currentTargetInRange() == true), events)
            }
        }
        if (delta == 0L && !deferEndContact) resolveEnemyContact(events)
    }

    private fun contactDue(): Boolean = combat.phase == EnemyPhase.ACTIVE &&
        resolvedContactId != combat.currentAttackId &&
        combat.phaseElapsedNanos >= checkNotNull(combat.currentAttackDirection).activeNanos / 2L

    private fun synchronizeAttackBaseline() {
        val id = combat.currentAttackId ?: return
        if (observedAttackId != id) {
            observedAttackId = id
            resolvedContactId = null
            attackHeadBaseline = latestTrackingSnapshot?.head?.pose?.position
        }
        attackHeadBaseline?.let { motion.beginEnemyAttack(id, it) }
    }

    private fun resolveEnemyContact(events: MutableList<EnemyCombatEvent>) {
        if (!contactDue()) return
        val id = checkNotNull(combat.currentAttackId)
        val target = enemyPosition ?: return
        val frame = latestMotion
        val receiptNow = lastTickTime ?: return
        synchronizeAttackBaseline()
        // Availability changes come from the tracking owner. Missing combat data cannot grant invulnerability.
        var outcome = if (frame == null) AttackOutcome.HIT_PLAYER else {
            motion.resolveDefense(id, checkNotNull(combat.currentAttackDirection), target, receiptNow)
        }
        resolvedContactId = id
        if (outcome == AttackOutcome.MISSED) {
            stamina = (stamina - 15.0).coerceAtLeast(0.0)
            focus = (focus + 12.0).coerceAtMost(100.0)
            score += 15
            notifyFeedback(CombatFeedback.DODGE)
            return
        }
        if (outcome == AttackOutcome.BLOCKED) {
            if (stamina >= 28.0) {
                stamina -= 28.0
                focus = (focus + 10.0).coerceAtMost(100.0)
                score += 5
                notifyFeedback(CombatFeedback.BLOCK)
                hitStopNanos = 35_000_000L
            } else {
                stamina = 0.0
                staggerUntil = matchNanos + 700_000_000L
                outcome = AttackOutcome.HIT_PLAYER
                notifyFeedback(CombatFeedback.GUARD_BREAK)
            }
        } else if (outcome == AttackOutcome.PARRIED) {
            stamina = (stamina - 6.0).coerceAtLeast(0.0)
            focus = (focus + 30.0).coerceAtMost(100.0)
            score += 30
            notifyFeedback(CombatFeedback.PARRY)
            hitStopNanos = 90_000_000L
        }
        collect(combat.resolveActiveAttack(id, outcome), events)
    }

    private fun applyPlayerMotion(frame: PlayerMotionFrame, events: MutableList<EnemyCombatEvent>) {
        if (matchNanos < staggerUntil || combat.phase == EnemyPhase.DEAD) return
        val enemy = enemyPosition ?: return
        val distance = hypot(frame.headPosition.x - enemy.x, frame.headPosition.z - enemy.z)
        if (frame.skillGesture) {
            if (distance > 1.75) {
                notifyFeedback(CombatFeedback.OUT_OF_RANGE)
            } else if (combat.health <= executionThreshold()) {
                executionActive = true
                dealDamage(combat.health, true, CombatFeedback.EXECUTION, 80, events)
            } else if (focus >= 100.0) {
                focus = 0.0
                dealDamage(55, true, CombatFeedback.SKILL, 35, events)
            } else {
                notifyFeedback(CombatFeedback.LOW_FOCUS)
            }
            return
        }
        val strike = frame.strike ?: return
        if (stamina < 12.0) {
            notifyFeedback(CombatFeedback.LOW_STAMINA)
            return
        }
        stamina -= 12.0
        combo = if (lastHitAt >= 0L && matchNanos - lastHitAt <= COMBO_WINDOW) minOf(combo + 1, 5) else 1
        lastHitAt = matchNanos
        val headshot = strike.zone == HitZone.HEAD
        val base = if (headshot) 30.0 else 25.0
        val damage = (base * strike.power * (1.0 + (combo - 1) * 0.10)).roundToInt()
        val kind = if (combat.guarding) CombatFeedback.GUARDED_HIT else if (headshot) CombatFeedback.HEADSHOT else CombatFeedback.HIT
        dealDamage(damage, headshot && combo >= 3, kind, (if (headshot) 15 else 10) * combo, events)
        focus = (focus + 12.0).coerceAtMost(100.0)
    }

    private fun dealDamage(damage: Int, breakGuard: Boolean, kind: CombatFeedback, points: Int, events: MutableList<EnemyCombatEvent>) {
        val normal = kind == CombatFeedback.HIT || kind == CombatFeedback.HEADSHOT || kind == CombatFeedback.GUARDED_HIT
        val outcome = combat.receivePlayerHit(damage, breakGuard, armGuard = normal && combo >= 2 && !breakGuard)
        if (outcome.none { it is EnemyCombatEvent.EnemyDamaged }) return
        score += points
        hitStopNanos = if (kind == CombatFeedback.SKILL || kind == CombatFeedback.EXECUTION) 110_000_000L else 45_000_000L
        if (kind == CombatFeedback.SKILL) {
            val enemy = enemyPosition
            val head = latestTrackingSnapshot?.head?.pose?.position
            if (enemy != null && head != null) {
                val away = Vector3(enemy.x - head.x, 0.0, enemy.z - head.z).normalizedOrNull()
                if (away != null) enemyPosition = enemy + away * 0.35
            }
        }
        val guarded = outcome.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().any { it.guarded }
        notifyFeedback(if (normal && guarded) CombatFeedback.GUARDED_HIT else kind)
        collect(outcome, events)
    }

    private fun collect(incoming: List<EnemyCombatEvent>, events: MutableList<EnemyCombatEvent>) {
        events += incoming
        for (event in incoming) {
            when (event) {
                is EnemyCombatEvent.AttackStarted -> {
                    observedAttackId = event.attackId
                    resolvedContactId = null
                    attackHeadBaseline = latestTrackingSnapshot?.head?.pose?.position
                    attackHeadBaseline?.let { motion.beginEnemyAttack(event.attackId, it) }
                }
                is EnemyCombatEvent.AttackResolved -> if (event.outcome == AttackOutcome.HIT_PLAYER) {
                    playerHealth = (playerHealth - if (matchNanos < staggerUntil) 30 else 20).coerceAtLeast(0)
                    combo = 0
                    if (feedback != CombatFeedback.GUARD_BREAK) notifyFeedback(CombatFeedback.PLAYER_HIT)
                    if (playerHealth == 0) finishDefeat(CombatFeedback.PLAYER_HIT, events)
                }
                is EnemyCombatEvent.PhaseChanged -> if (event.current == EnemyPhase.DEAD && result == TrialResult.FIGHTING) {
                    result = TrialResult.ROUND_CLEAR
                    intermissionNanos = 0L
                    combo = 0
                    pendingMotion.clear()
                    DesktopCombatInput.reset()
                    score += 100
                }
                else -> Unit
            }
        }
    }

    private fun finishDefeat(kind: CombatFeedback, events: MutableList<EnemyCombatEvent>) {
        result = TrialResult.DEFEAT
        pendingMotion.clear()
        DesktopCombatInput.reset()
        events += combat.pauseByPlayer()
        bestScore = maxOf(bestScore, score)
        notifyFeedback(kind)
    }

    private fun moveEnemy(delta: Long) {
        val head = latestTrackingSnapshot?.head?.pose?.position ?: return
        val enemy = enemyPosition ?: return
        if (combat.phase != EnemyPhase.IDLE) return
        val toward = Vector3(head.x - enemy.x, 0.0, head.z - enemy.z)
        val distance = toward.length()
        if (distance > 0.01) enemyYaw = atan2(toward.x, toward.z).toFloat()
        val direction = toward.normalizedOrNull() ?: return
        val desired = 1.45
        val difference = distance - desired
        val travel = (delta / 1_000_000_000.0 * 0.65).coerceAtMost(kotlin.math.abs(difference))
        if (kotlin.math.abs(difference) > 0.05) enemyPosition = enemy + direction * (if (difference > 0) travel else -travel)
    }

    private fun beginNextRound(events: MutableList<EnemyCombatEvent>) {
        val resumeRequired = combat.pauseReason != null || !viewState.actionReady
        roundNumber++
        check(roundGeneration < Long.MAX_VALUE) { "round generation overflow" }
        roundGeneration++
        initialHealth = 100 + (roundNumber - 1) * 25
        combat = EnemyCombatStateMachine(initialHealth, 800_000_000L - (roundNumber - 1) * 100_000_000L)
        enemyPosition = enemySpawn
        enemyYaw = 0f
        executionActive = false
        hitStopNanos = 0L
        playerHealth = (playerHealth + 20).coerceAtMost(100)
        stamina = (stamina + 35.0).coerceAtMost(100.0)
        focus = (focus + 20.0).coerceAtMost(100.0)
        result = TrialResult.COUNTDOWN
        countdownNanos = 0L
        feedback = null
        events += EnemyCombatEvent.RoundReset()
        if (resumeRequired) events += combat.interruptTracking()
        revokeActionBaseline(lastAcceptedStamp?.sequence ?: -1L)
    }

    private fun notifyFeedback(kind: CombatFeedback) {
        feedback = kind
        feedbackUntil = matchNanos + 900_000_000L
        feedbackSequence++
    }

    private fun executionThreshold(): Int = maxOf(25, initialHealth / 4)
    private fun intermissionDuration(): Long = if (executionActive) 5_000_000_000L else 3_200_000_000L

    private fun clearMotion() {
        motion.reset()
        latestMotion = null
        pendingMotion.clear()
        observedAttackId = null
        attackHeadBaseline = null
        resolvedContactId = null
        queuedStrikeId = -1L
        lastSkillReceipt = Long.MIN_VALUE
    }

    private companion object {
        const val SECOND = 1_000_000_000L
        const val MATCH_DURATION = 180L * SECOND
        const val COUNTDOWN_DURATION = 3L * SECOND
        const val COMBO_WINDOW = 1_600_000_000L
    }

    fun setPlayerHandPresenter(presenter: HandPosePresenter?) {
        playerHandPresenter = presenter
        val snapshot = latestTrackingSnapshot
        val handPose = if (snapshot?.hasRequiredObservations == true) {
            val hand = if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right
            hand?.pose
        } else {
            null
        }
        presentHand(handPose)
    }

    fun setEnemyGeometry(position: Vector3?, reachMeters: Double) {
        val wasAvailable = sceneAvailable
        val valid = position?.takeIf { it.isFinite() && reachMeters.isFinite() && reachMeters > 0.0 }
        sceneAvailable = valid != null
        if (valid != null) {
            enemySpawn = valid
            if (enemyPosition == null || result == TrialResult.READY) enemyPosition = valid
        }
        enemyReachMeters = if (sceneAvailable) maxOf(reachMeters, 1.55) else 0.0
        lastTickTime = null
        revokeActionBaseline(lastAcceptedStamp?.sequence ?: -1L)
        establishActionBaseline()
        lastReportedHead = null
        logMessage("Enemy geometry available=${enemyPosition != null}; boundsReachMeters=$enemyReachMeters")
        val events = if (wasAvailable && !sceneAvailable && trialStarted &&
            result != TrialResult.VICTORY && result != TrialResult.DEFEAT) {
            combat.interruptTracking()
        } else {
            emptyList()
        }
        publish(events)
    }

    fun onTrackingEvent(event: TrackingEvent, accepted: Boolean, snapshot: TrackingSnapshot) {
        val previousSnapshot = latestTrackingSnapshot
        val previousStamp = lastAcceptedStamp
        latestTrackingSnapshot = snapshot
        val newlyAccepted = accepted && (previousStamp == null || event.stamp.sequence > previousStamp.sequence)
        if (newlyAccepted) lastAcceptedStamp = event.stamp
        val events = mutableListOf<EnemyCombatEvent>()
        val control = event as? TrackingEvent.Discontinuity
        when {
            newlyAccepted && control?.reason == DiscontinuityReason.ROUND_RESET -> {
                check(roundGeneration < Long.MAX_VALUE) { "round generation overflow" }
                roundGeneration++
                trialStarted = false
                combat = EnemyCombatStateMachine()
                initialHealth = combat.health
                events += combat.resetRound()
                result = TrialResult.READY
                playerHealth = 100
                stamina = 100.0
                focus = 50.0
                score = 0
                combo = 0
                lastHitAt = -1L
                roundNumber = 1
                matchNanos = 0L
                countdownNanos = 0L
                intermissionNanos = 0L
                executionActive = false
                hitStopNanos = 0L
                staggerUntil = 0L
                feedback = null
                enemyPosition = enemySpawn
                enemyYaw = 0f
                revokeActionBaseline(event.stamp.sequence)
                lastReportTime = null
                lastReportedHead = null
                lastReportedHand = null
                lastReportedEligibility = null
                reportedWaiting = false
            }
            newlyAccepted && control?.reason == DiscontinuityReason.USER_PAUSED -> {
                events += combat.pauseByPlayer()
                revokeActionBaseline(event.stamp.sequence)
            }
            else -> {
                val requiredControl = newlyAccepted && control != null && control.target.affects(snapshot.dominantHand)
                val changedContinuity = previousSnapshot != null && (
                    previousSnapshot.dominantHand != snapshot.dominantHand ||
                        previousSnapshot.headContinuity != snapshot.headContinuity ||
                        previousSnapshot.handContinuity() != snapshot.handContinuity() ||
                        previousSnapshot.requiredSinceSequence != snapshot.requiredSinceSequence
                    )
                val changedEpoch = newlyAccepted && previousStamp != null &&
                    previousStamp.coordinateEpoch != event.stamp.coordinateEpoch
                val lostRequiredInput = hadReadyInput && !snapshot.hasRequiredObservations
                if (requiredControl || changedContinuity || changedEpoch || lostRequiredInput) {
                    val boundary = maxOf(event.stamp.sequence, previousStamp?.sequence ?: -1L, snapshot.requiredSinceSequence)
                    revokeActionBaseline(boundary)
                    if (hadReadyInput || trialStarted || combat.pauseReason != null) {
                        events += combat.interruptTracking()
                    }
                }
            }
        }
        hadReadyInput = snapshot.hasRequiredObservations
        if (!snapshot.hasRequiredObservations) {
            presentHand(null)
            lastTickTime = null
            lastReportedHead = null
            if (!reportedWaiting) {
                reportedWaiting = true
                logMessage("Combat input waiting for head and dominant-hand observations; sequence=${event.stamp.sequence}")
            }
            publish(events)
            return
        }
        if (!newlyAccepted) {
            publish(events)
            return
        }
        establishActionBaseline()
        val handPose = (if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right)?.pose
        presentHand(handPose)
        val target = enemyPosition
        if (sceneAvailable && target != null && viewState.actionReady) {
            val frame = motion.observe(snapshot, target)
            latestMotion = frame
            if (frame != null && result == TrialResult.FIGHTING && combat.pauseReason == null) {
                val strikeIsNew = frame.strike?.id?.let { it > queuedStrikeId } == true
                val skillIsNew = frame.skillGesture && frame.receivedAtNanos != lastSkillReceipt
                if (strikeIsNew || skillIsNew) {
                    if (pendingMotion.size >= 16) {
                        events += combat.interruptTracking()
                        revokeActionBaseline(event.stamp.sequence)
                    } else {
                        pendingMotion.addLast(frame)
                        if (strikeIsNew) queuedStrikeId = checkNotNull(frame.strike).id
                        if (skillIsNew) lastSkillReceipt = frame.receivedAtNanos
                    }
                }
            }
        }
        reportedWaiting = false
        logInput(event, snapshot)
        publish(events)
    }

    private fun establishActionBaseline() {
        val snapshot = latestTrackingSnapshot ?: return
        if (!sceneAvailable || enemyPosition == null || !snapshot.hasRequiredObservations) return
        val head = snapshot.head ?: return
        val hand = (if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right) ?: return
        if (head.stamp.sequence <= actionRequiredAfterSequence || hand.stamp.sequence <= actionRequiredAfterSequence ||
            head.stamp.coordinateEpoch != hand.stamp.coordinateEpoch ||
            hand.stamp.coordinateEpoch != lastAcceptedStamp?.coordinateEpoch
        ) return
        actionBaseline = snapshot.actionIdentity()
    }

    private fun revokeActionBaseline(sequence: Long) {
        actionBaseline = null
        actionRequiredAfterSequence = maxOf(actionRequiredAfterSequence, sequence)
        lastTickTime = null
        clearMotion()
        DesktopCombatInput.reset()
        combo = 0
        lastHitAt = -1L
    }

    private fun TrackingSnapshot.handContinuity(): Long =
        if (dominantHand == Hand.LEFT) leftContinuity else rightContinuity

    private fun TrackingSnapshot.actionIdentity(): ActionBaseline? {
        val hand = (if (dominantHand == Hand.LEFT) left else right) ?: return null
        return ActionBaseline(dominantHand, hand.stamp.coordinateEpoch, headContinuity, handContinuity())
    }

    private fun TrackingTarget.affects(hand: Hand): Boolean =
        this == TrackingTarget.ALL || this == TrackingTarget.HEAD || this == TrackingTarget.BOTH_HANDS ||
            (this == TrackingTarget.LEFT_HAND && hand == Hand.LEFT) ||
            (this == TrackingTarget.RIGHT_HAND && hand == Hand.RIGHT)

    private fun currentTargetInRange(): Boolean? {
        if (!sceneAvailable) return null
        val snapshot = latestTrackingSnapshot ?: return null
        if (!snapshot.hasRequiredObservations) return null
        val head = snapshot.head?.pose?.position ?: return null
        val enemy = enemyPosition ?: return null
        // Keep the existing conservative range rule separate from contact and damage.
        return hypot(head.x - enemy.x, head.z - enemy.z) <= enemyReachMeters
    }

    private fun logInput(event: TrackingEvent, snapshot: TrackingSnapshot) {
        val head = snapshot.head ?: return
        val headPosition = head.pose?.position ?: return
        val hand = (if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right) ?: return
        val handPosition = hand.pose?.position ?: return
        val enemy = enemyPosition ?: return
        val distance = hypot(headPosition.x - enemy.x, headPosition.z - enemy.z)
        val targetInRange = currentTargetInRange() ?: return
        val now = event.stamp.receivedAtNanos
        val canStartAttack = combat.canStartAttack(targetInRange)
        val lastReport = lastReportTime
        val changed = headPosition != lastReportedHead || handPosition != lastReportedHand ||
            canStartAttack != lastReportedEligibility
        if (changed && (lastReport == null || now < lastReport || now - lastReport >= 100_000_000L)) {
            lastReportTime = now
            lastReportedHead = headPosition
            lastReportedHand = handPosition
            lastReportedEligibility = canStartAttack
            logMessage(
                "Combat input evaluated origin=${event.stamp.origin}, sequence=${event.stamp.sequence}, " +
                    "headSequence=${head.stamp.sequence}, handSequence=${hand.stamp.sequence}, " +
                    "head=$headPosition, hand=$handPosition, distanceMeters=$distance, " +
                    "targetInRange=$targetInRange, canStartAttack=$canStartAttack, phase=${combat.phase}",
            )
        }
    }

    private fun presentHand(pose: ObservedPose?) {
        try {
            playerHandPresenter?.invoke(pose)
        } catch (error: Exception) {
            logFailure("Player-hand presentation failed", error)
        }
    }

    private fun publish(events: List<EnemyCombatEvent> = emptyList()) {
        val presenter = arenaPresenter ?: return
        val state = viewState
        try {
            presenter(state, events.toList())
        } catch (error: Exception) {
            logFailure("Arena presentation failed", error)
        }
    }
}
