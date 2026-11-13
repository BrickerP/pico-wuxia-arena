package com.example.wuxiaarena.p0d2f0182.runtime

import android.util.Log
import com.example.wuxiaarena.core.combat.BladeContact
import com.example.wuxiaarena.core.combat.BladeContactUncertainException
import com.example.wuxiaarena.core.combat.BladeSegment
import com.example.wuxiaarena.core.combat.BladeSweep
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.firstBladeContact
import com.example.wuxiaarena.core.combat.firstRigidBladeContact
import com.example.wuxiaarena.core.combat.interpolateGrip
import com.example.wuxiaarena.core.combat.playerBlade
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
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.MotionStrike
import com.example.wuxiaarena.core.combat.MotionContact
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.input.TrackingTarget
import com.example.wuxiaarena.core.math.closestSegmentPoints
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.atan2
import kotlin.math.hypot
import kotlin.math.roundToInt

typealias HandPosePresenter = (TrackingSnapshot?) -> Unit

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
    val enemyName: String = "刀客",
    val enemyTravelMeters: Double = 0.0,
    val enemyGaitMeters: Double = 0.0,
    val enemyMoveDirection: Float = 0f,
    val motionCharge: Float = 0f,
    val playerBladeBase: Vector3? = null,
    val playerBladeTip: Vector3? = null,
    val playerHeadPosition: Vector3? = null,
    val motionReleaseRequired: Boolean = false,
    val enemyHitZone: HitZone? = null,
    val enemyRecoilOffset: Vector3 = Vector3(0.0, 0.0, 0.0),
    val playerBladeTipSpeed: Double = 0.0,
    val playerBladeAtRest: Boolean = true,
    val playerMotionGeneration: Long = 0L,
    val enemyBladeBase: Vector3? = null,
    val enemyBladeTip: Vector3? = null,
    val enemyRecoveryFromContact: Boolean = false,
    val playerWeaponGrip: WeaponGrip? = null,
    val enemyPoseClip: String? = null,
    val enemyPoseSourceSeconds: Double? = null,
    val enemyPoseDirection: AttackDirection? = null,
    /** Read-only receipt provenance. UI batches and application hand receipts are not GPU/device sample clocks. */
    val diagnosticUiFrameNanos: Long? = null,
    val diagnosticPublishSource: String = "snapshot",
    val diagnosticHandStamp: ObservationStamp? = null,
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
    private var simulationMotion: PlayerMotionFrame? = null
    private var contactRecovery: ContactRecovery? = null
    private var enemyMotionNanos = 0L
    private var steelContactLatched = false
    private var contactQueryFailures = 0
    private var contactUncertainReceipt: Long? = null
    private data class ContactRecovery(val profile: AttackProfile, val direction: AttackDirection,
        val sourceSeconds: Double, val startedAtNanos: Long, val durationNanos: Long)

    private var consumedStrikeId = -1L
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
    private var hitStopAwaitingPresentation = false
    private var deathHitStopNanos = 0L
    private var nextImpactId = 1L
    private var recoilElapsedNanos = 0L
    private var recoilVector = Vector3(0.0, 0.0, 0.0)
    private var heldEnemyPoseFrame: EnemyPoseFrame? = null
    private var heldEnemyAttackOffsets: AttackPoseSample? = null
    private var staggerUntil = 0L
    private var feedback: CombatFeedback? = null
    private var enemyHitZone: HitZone? = null
    private var feedbackUntil = 0L
    private var feedbackSequence = 0L
    private var sceneAvailable = false
    private var enemySpawn: Vector3? = null
    private var enemyYaw = 0f
    private var enemyTravelMeters = 0.0
    private var enemyGaitMeters = 0.0
    private var enemyMoveDirection = 0f
    private var observedAttackId: Long? = null
    private var attackSequenceIndex = 0
    private var enemyRecoveryFromContact = false
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
    private var lastNativeMotionLogNanos: Long? = null
    private var lastNativeMotionPoses: Triple<ObservedPose?, ObservedPose?, ObservedPose?>? = null
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
            val motionReady = result == TrialResult.FIGHTING && combat.pauseReason == null && actionReady
            val releaseRequired = motionReady && latestMotion?.releaseRequired == true
            val selectedPose = effectiveEnemyPose()
            val enemyAttackPose = enemyAttackPose()
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
                roundCount = arenaOpponents.size,
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
                deathElapsedSeconds = if (combat.phase == EnemyPhase.DEAD) {
                    (CombatFeedbackProfile.deathElapsedNanos(
                        (intermissionNanos - deathHitStopNanos).coerceAtLeast(0L),
                    ) / 1_000_000_000.0).toFloat()
                } else 0f,
                dominantHand = snapshot?.dominantHand ?: Hand.RIGHT,
                enemyName = arenaOpponents[roundNumber - 1].name,
                enemyTravelMeters = enemyTravelMeters,
                enemyGaitMeters = enemyGaitMeters,
                enemyMoveDirection = enemyMoveDirection,
                motionCharge = if (motionReady && !releaseRequired) latestMotion?.chargeProgress ?: 0f else 0f,
                playerBladeBase = latestMotion?.bladeBase,
                playerBladeTip = latestMotion?.bladeTip,
                playerBladeTipSpeed = latestMotion?.bladeTipSpeed ?: 0.0,
                playerBladeAtRest = latestMotion?.bladeAtRest ?: true,
                playerMotionGeneration = latestMotion?.motionGeneration ?: motion.motionGeneration,
                playerHeadPosition = snapshot?.head?.pose?.position,
                motionReleaseRequired = releaseRequired,
                enemyHitZone = if (combat.phase == EnemyPhase.HIT) enemyHitZone else null,
                enemyRecoilOffset = currentRecoilOffset(),
                enemyBladeBase = enemyAttackPose?.bladeBase,
                enemyBladeTip = enemyAttackPose?.bladeTip,
                enemyRecoveryFromContact = enemyRecoveryFromContact,
                playerWeaponGrip = latestMotion?.weaponGrip,
                enemyPoseClip = selectedPose?.clip,
                enemyPoseSourceSeconds = selectedPose?.pose?.sourceSeconds,
                enemyPoseDirection = contactRecovery?.direction ?: combat.currentAttackDirection,
                diagnosticHandStamp = hand?.stamp,
            )
        }

    fun setArenaPresenter(presenter: ArenaPresenter?) {
        arenaPresenter = presenter
        publish(source = "presenter_bind")
    }

    fun startTrial(): Boolean {
        val state = viewState
        if (result != TrialResult.READY || trialStarted || !state.sceneReady || !state.inputReady || state.pauseReason != null) return false
        trialStarted = true
        result = TrialResult.COUNTDOWN
        countdownNanos = 0L
        lastTickTime = null
        publish(source = "start_trial")
        return true
    }

    /** Called after the input owner drains pending controls and observations. */
    fun confirmResume(pauseId: Long): Boolean {
        if (result == TrialResult.VICTORY || result == TrialResult.DEFEAT) return false
        val state = viewState
        if (state.pauseId != pauseId || !state.resumeReady) return false
        val events = combat.tryResume(state.inputReady, state.actionReady, pauseId)
        if (combat.pauseReason != null) return false
        if (combat.phase != EnemyPhase.HIT) enemyHitZone = null
        clearMotion()
        if (combat.phase == EnemyPhase.IDLE) clearEnemyContactPlayback()
        lastTickTime = null
        publish(events, source = "resume")
        return true
    }

    /** The input owner calls this once after all drains, using its receipt clock. */
    fun onTick(nowNanos: Long, uiFrameNanos: Long? = null) {
        val targetInRange = currentTargetInRange()
        val terminal = result == TrialResult.VICTORY || result == TrialResult.DEFEAT
        val canAdvance = if (result == TrialResult.ROUND_CLEAR) {
            val state = viewState
            combat.pauseReason == null && state.inputReady && state.sceneReady
        } else {
            targetInRange != null && combat.pauseReason == null && viewState.actionReady
        }
        if (!trialStarted || terminal || !canAdvance) {
            lastTickTime = null
            publish(source = "tick", uiFrameNanos = uiFrameNanos)
            return
        }
        val previous = lastTickTime
        lastTickTime = nowNanos
        if (previous == null || nowNanos < previous) {
            publish(source = "tick", uiFrameNanos = uiFrameNanos)
            return
        }
        val delta = nowNanos - previous
        if (delta < 0L || delta > Long.MAX_VALUE - combat.simulationNanos) {
            logMessage("Trial clock interval is unavailable; rebuilding its baseline")
            publish(source = "tick", uiFrameNanos = uiFrameNanos)
            return
        }
        val events = mutableListOf<EnemyCombatEvent>()
        var remaining = delta
        var intervalEnd = previous
        while (remaining > 0L) {
            // An already-known hand interval must not be shortened by an arbitrary
            // outer tick slice: advanceEnemy performs the geometry/source subdivisions.
            val nextReceipt = pendingMotion.firstOrNull()?.receivedAtNanos
            if (result == TrialResult.FIGHTING && nextReceipt != null && nextReceipt <= intervalEnd) {
                advanceFight(0L, intervalEnd, events)
                continue
            }
            val receiptInterval = nextReceipt?.minus(intervalEnd)?.takeIf { it > 0L }
            val step = if (result == TrialResult.FIGHTING && receiptInterval != null)
                minOf(remaining, receiptInterval) else minOf(remaining, 100_000_000L)
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
                    if (hitStopAwaitingPresentation) continue
                    val frozen = minOf(hitStopNanos, step)
                    hitStopNanos -= frozen
                    recoilElapsedNanos = (recoilElapsedNanos + step - frozen).coerceAtMost(RECOIL_DURATION)
                    intermissionNanos += step
                    if (intermissionNanos >= intermissionDuration()) {
                        if (roundNumber == arenaOpponents.size) {
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
        publish(events, source = "tick", uiFrameNanos = uiFrameNanos)
    }

    private fun advanceFight(delta: Long, now: Long, events: MutableList<EnemyCombatEvent>) {
        val available = (MATCH_DURATION - matchNanos).coerceAtLeast(0L)
        val interval = minOf(delta, available)
        val frameStart = now - delta
        val playableUntil = frameStart + interval
        if (contactUncertainReceipt?.let { it >= frameStart } == true) {
            contactUncertainReceipt = null
            pendingMotion.clear()
            return
        }
        matchNanos += interval
        val regeneration = if (latestMotion?.guardDirection != null) 4.0 else 14.0
        stamina = (stamina + interval / 1_000_000_000.0 * regeneration).coerceAtMost(100.0)
        if (feedback != null && matchNanos >= feedbackUntil) feedback = null
        if (lastHitAt >= 0L && matchNanos - lastHitAt > COMBO_WINDOW) combo = 0
        var advanced = 0L
        while (pendingMotion.isNotEmpty()) {
            if (pendingMotion.first().receivedAtNanos > playableUntil) break
            val frame = pendingMotion.removeFirst()
            if (now.toDouble() - frame.receivedAtNanos.toDouble() > 250_000_000.0) continue
            val offset = (frame.receivedAtNanos - frameStart).coerceIn(advanced, interval)
            val stopped = advanceEnemy(offset - advanced, events, receiptStartNanos = frameStart + advanced, endFrame = frame)
            advanced = offset
            if (result != TrialResult.FIGHTING) break
            if (hitStopNanos == 0L && !stopped && frame.skillGesture) applyPlayerMotion(simulationMotion ?: frame, events)
        }
        if (result == TrialResult.FIGHTING) advanceEnemy(interval - advanced, events, receiptStartNanos = frameStart + advanced)
        if (result == TrialResult.FIGHTING && matchNanos >= MATCH_DURATION) finishDefeat(CombatFeedback.TIMEOUT, events)
    }

    /** Query before advancing: contacts are inserted on this same simulation/source clock. */
    private fun advanceEnemy(delta: Long, events: MutableList<EnemyCombatEvent>, receiptStartNanos: Long, endFrame: PlayerMotionFrame? = null): Boolean {
        val initial = simulationMotion ?: endFrame ?: latestMotion
        if (initial == null) {
            enemyMotionNanos += delta
            collect(combat.advanceBy(delta, currentTargetInRange() == true, nextAttackDirection()), events)
            collect(combat.tryStartAttack(nextAttackDirection(), currentTargetInRange() == true), events)
            return false
        }
        val target = endFrame?.let(motion::applyWeaponConstraint) ?: initial
        if (target.motionGeneration != initial.motionGeneration) {
            simulationMotion = target
            latestMotion = target
            return true
        }
        var remaining = delta
        var consumed = 0L
        var stopped = false
        fun frameAt(fraction: Double, receiptNanos: Long): PlayerMotionFrame =
            interpolateMotionFrame(initial, target, fraction, receiptNanos)
        // Zero-time observations still need steel-before-body ordering.
        var zeroQuery = delta == 0L && endFrame != null
        while ((remaining > 0L || zeroQuery) && result == TrialResult.FIGHTING && combat.pauseReason == null) {
            if (hitStopAwaitingPresentation) return true
            val frozen = minOf(remaining, hitStopNanos)
            hitStopNanos -= frozen
            remaining -= frozen
            consumed += frozen
            if (remaining == 0L && !zeroQuery) break
            synchronizeAttackBaseline()
            val maximum = minOf(remaining, combat.nanosUntilPhaseTransition ?: remaining, 10_000_000L)
            val interval = nextPoseInterval(maximum)
            val fromFrame = simulationMotion ?: initial
            val toFrame = if (stopped) fromFrame else frameAt(if (delta == 0L) 1.0 else (consumed + interval).toDouble() / delta, receiptStartNanos + consumed + interval)
            val actorBefore = captureEnemyLocomotion()
            val before = enemyAttackPose()
            moveEnemy(interval, toFrame.headPosition)
            val after = enemyAttackPose(interval)
            val candidate = try {
                queryContact(fromFrame, toFrame, before, after)
            } catch (uncertain: BladeContactUncertainException) {
                // Never turn an unproved interval into a miss or apply its pending damage.
                restoreEnemyLocomotion(actorBefore)
                if (contactQueryFailures++ < 4) logMessage("Contact query held previous pose: ${uncertain.message}")
                latestMotion = fromFrame.copy(strike = null, skillGesture = false)
                simulationMotion = latestMotion
                return true
            }
            zeroQuery = false
            if (candidate != null) {
                val advance = (interval * candidate.contact.fraction).toLong().coerceIn(0L, interval)
                restoreEnemyLocomotion(actorBefore)
                if (advance > 0L) moveEnemy(advance, fromFrame.headPosition * (1.0 - candidate.contact.fraction) + toFrame.headPosition * candidate.contact.fraction)
                collect(combat.advanceBy(advance, currentTargetInRange() == true, nextAttackDirection()), events)
                recoilElapsedNanos = (recoilElapsedNanos + advance).coerceAtMost(RECOIL_DURATION)
                enemyMotionNanos += advance
                consumed += advance
                remaining -= advance
                val fraction = candidate.contact.fraction
                val atContact = interpolateMotionFrame(fromFrame, toFrame, fraction, receiptStartNanos + consumed)
                val grip = atContact.weaponGrip
                if (candidate.steel && steelContactLatched && grip != null) {
                    // The constraint is an ongoing unilateral stop, not just a one-shot
                    // effect. Keep the enemy's actor/source clock at this TOI while its
                    // proposed motion presses into the held dao; only a proven separating
                    // sweep may advance. Raw head/hand observations remain available.
                    val held = motion.constrainWeapon(atContact, grip, candidate.contact).copy(
                        receivedAtNanos = receiptStartNanos + delta, headPosition = target.headPosition,
                        strike = null, swing = null, skillGesture = false)
                    latestMotion = held
                    simulationMotion = held
                    combat.advanceWhileWeaponStopped(remaining)
                    return true
                }
                if (candidate.steel && grip != null) {
                    steelContactLatched = true
                    val held = motion.constrainWeapon(atContact, grip, candidate.contact)
                    latestMotion = held
                    simulationMotion = held
                    resolveSteelContact(candidate.contact, held, events)
                } else if (candidate.playerAttack) {
                    val blade = grip?.let(::playerBlade)
                    val witness = MotionContact(candidate.zone, candidate.contact.enemyPoint, candidate.contact.normal,
                        candidate.contact.relativeDisplacement.normalizedOrNull())
                    val striking = atContact.copy(weaponGrip = grip,
                        bladeBase = blade?.base ?: atContact.bladeBase, bladeTip = blade?.tip ?: atContact.bladeTip,
                        strike = atContact.swing?.let { MotionStrike(it.id, candidate.zone, it.power, witness) })
                    latestMotion = striking
                    simulationMotion = striking
                    applyPlayerMotion(striking, events)
                } else {
                    latestMotion = atContact
                    simulationMotion = atContact
                    resolveBodyContact(candidate.contact, candidate.zone, events)
                }
                stopped = true
                // Contacts transition the attack or start hit stop; cannot repeatedly consume t=0.
                if (hitStopNanos > 0L || hitStopAwaitingPresentation) break
            } else {
                collect(combat.advanceBy(interval, currentTargetInRange() == true, nextAttackDirection()), events)
                recoilElapsedNanos = (recoilElapsedNanos + interval).coerceAtMost(RECOIL_DURATION)
                enemyMotionNanos += interval
                consumed += interval
                remaining -= interval
                simulationMotion = toFrame
                latestMotion = toFrame
                try { after?.let { motion.releaseWeaponIfSeparated(it.blade()) } }
                catch (uncertain: BladeContactUncertainException) {
                    if (contactQueryFailures++ < 4) logMessage("Weapon catchup held: ${uncertain.message}")
                }
                if (!motion.weaponConstrained && after != null) {
                    val pair = closestSegmentPoints(toFrame.bladeBase, toFrame.bladeTip, after.bladeBase, after.bladeTip)
                    if (pair != null && pair.first.distanceTo(pair.second) > 0.012 + 0.0125 + 0.025)
                        steelContactLatched = false
                }
            }
            if (result == TrialResult.FIGHTING)
                collect(combat.tryStartAttack(nextAttackDirection(), currentTargetInRange() == true), events)
            if (interval == 0L) break
        }
        return stopped
    }

    // Split at source sample keys and the piecewise ACTIVE clock bend. Both blade endpoints
    // are linear inside these intervals; rigid player rotations have their own sagitta bound.
    private fun nextPoseInterval(maximum: Long): Long {
        if (maximum == 0L) return maximum
        val recovery = contactRecovery
        if (recovery != null) {
            val elapsed = enemyMotionNanos - recovery.startedAtNanos
            val bend = CONTACT_STOP_NANOS + ((recovery.durationNanos - CONTACT_STOP_NANOS) * 0.18).toLong()
            var result = if (elapsed < CONTACT_STOP_NANOS) minOf(maximum, CONTACT_STOP_NANOS - elapsed)
                else if (elapsed < bend) minOf(maximum, bend - elapsed) else maximum
            val start = checkNotNull(effectiveEnemyPose()).pose.sourceSeconds
            val end = checkNotNull(effectiveEnemyPose(result)).pose.sourceSeconds
            val keys = recovery.profile.samples.map { it.sourceSeconds }.filter {
                it > minOf(start, end) + 1e-12 && it < maxOf(start, end) - 1e-12
            }
            val key = if (end > start) keys.minOrNull() else keys.maxOrNull()
            if (key != null && end != start) result = maxOf(1L, (result * (key - start) / (end - start)).toLong())
            return result
        }
        if (combat.phase == EnemyPhase.IDLE) {
            val actor = captureEnemyLocomotion()
            moveEnemy(maximum)
            val gaitDelta = enemyGaitMeters - actor.gait
            restoreEnemyLocomotion(actor)
            if (gaitDelta == 0.0) return maximum
            val locomotion = arenaOpponents[roundNumber - 1].locomotionProfile()
            val start = locomotion.sourceSeconds(true, actor.gait)
            val span = locomotion.loopEndSeconds - locomotion.loopStartSeconds
            val nextKey = if (gaitDelta > 0.0) locomotion.walk.samples.firstOrNull {
                it.sourceSeconds > start + 1e-12 && it.sourceSeconds <= locomotion.loopEndSeconds
            }?.sourceSeconds ?: locomotion.loopEndSeconds else locomotion.walk.samples.lastOrNull {
                it.sourceSeconds < start - 1e-12 && it.sourceSeconds >= locomotion.loopStartSeconds
            }?.sourceSeconds ?: locomotion.loopStartSeconds
            val sourceDistance = kotlin.math.abs(nextKey - start)
            if (sourceDistance <= 1e-12) return minOf(maximum, 1L)
            val gaitToKey = sourceDistance / span * locomotion.strideMeters
            return minOf(maximum, maxOf(1L, (maximum * gaitToKey / kotlin.math.abs(gaitDelta)).toLong()))
        }
        if (combat.currentAttackDirection == null) return maximum
        val profile = arenaOpponents[roundNumber - 1].attackProfile(checkNotNull(combat.currentAttackDirection))
        val elapsed = combat.phaseElapsedNanos
        val remaining = combat.nanosUntilPhaseTransition ?: return maximum
        var result = maximum
        if (combat.phase == EnemyPhase.ACTIVE) {
            val half = checkNotNull(combat.currentAttackDirection).activeNanos / 2L
            if (elapsed < half) result = minOf(result, half - elapsed)
        }
        val start = profile.sourceSeconds(combat.phase, elapsed, remaining)
        val end = profile.sourceSeconds(combat.phase, elapsed + result, remaining - result)
        val key = profile.samples.firstOrNull { it.sourceSeconds > start + 1e-12 && it.sourceSeconds < end - 1e-12 }
        if (key != null && end > start) result = maxOf(1L, (result * (key.sourceSeconds - start) / (end - start)).toLong())
        return result
    }

    /** Every contact consumer receives the same rigid pose and receipt-clock witness. */
    internal fun interpolateMotionFrame(from: PlayerMotionFrame, to: PlayerMotionFrame,
        fraction: Double, receiptNanos: Long): PlayerMotionFrame {
        val amount = fraction.coerceIn(0.0, 1.0)
        val grip = if (from.weaponGrip != null && to.weaponGrip != null)
            interpolateGrip(from.weaponGrip, to.weaponGrip, amount) else to.weaponGrip ?: from.weaponGrip
        val blade = grip?.let(::playerBlade)
        val evidence = if (to.guardEnteredAtNanos?.let { it <= receiptNanos } == true) to else from
        val fast = to.fastGuardAtNanos?.takeIf { to.guardDirection == evidence.guardDirection && it <= receiptNanos }
            ?: from.fastGuardAtNanos?.takeIf { from.guardDirection == evidence.guardDirection && it <= receiptNanos }
        return to.copy(receivedAtNanos = receiptNanos, weaponGrip = grip,
            bladeBase = blade?.base ?: from.bladeBase * (1.0 - amount) + to.bladeBase * amount,
            bladeTip = blade?.tip ?: from.bladeTip * (1.0 - amount) + to.bladeTip * amount,
            headPosition = from.headPosition * (1.0 - amount) + to.headPosition * amount,
            guardDirection = evidence.guardDirection,
            guardEnteredAtNanos = evidence.guardEnteredAtNanos?.takeIf { it <= receiptNanos },
            fastGuardAtNanos = fast)
    }

    private fun separatingSteelSweep(from: WeaponGrip, to: WeaponGrip, enemy: BladeSweep, normal: Vector3): Boolean {
        // The enemy endpoint support is linear within a source interval. Certify
        // withdrawal against a fixed contact plane, including the rigid player's
        // rotation curvature, instead of ignoring every latched steel sweep.
        val a = checkNotNull(from.rotation.normalizedOrNull())
        val b = checkNotNull(to.rotation.normalizedOrNull())
        val angle = 2.0 * kotlin.math.acos(kotlin.math.abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w).coerceIn(0.0, 1.0))
        val first = playerBlade(from)
        val last = playerBlade(to)
        val gripRadius = maxOf(first.base.distanceTo(from.position), first.tip.distanceTo(from.position))
        // The projection of a rigid endpoint has |second derivative| <= r*angle^2.
        // Thus its chord error is <= K*t*(1-t), K=r*angle^2/2. Requiring
        // one end's support gap to cover K proves separation for a rotating withdrawal.
        val curvatureBound = gripRadius * angle * angle * 0.5
        fun gap(player: BladeSegment, other: BladeSegment): Double = minOf(
            (player.base - other.base).dot(normal), (player.base - other.tip).dot(normal),
            (player.tip - other.base).dot(normal), (player.tip - other.tip).dot(normal),
        ) - player.radiusMeters - other.radiusMeters
        val start = gap(first, enemy.previous)
        val end = gap(last, enemy.current)
        return start >= -1e-7 && end >= curvatureBound || start >= curvatureBound && end >= -1e-7
    }

    private data class IncomingContact(val contact: BladeContact, val steel: Boolean, val zone: HitZone, val playerAttack: Boolean = false)

    private fun queryContact(from: PlayerMotionFrame, to: PlayerMotionFrame,
        before: AttackPoseSample?, after: AttackPoseSample?): IncomingContact? {
        if (before == null || after == null || combat.phase == EnemyPhase.DEAD) return null
        val enemySweep = BladeSweep(before.blade(), after.blade())
        val gripBefore = from.weaponGrip
        val gripAfter = to.weaponGrip
        val steel = if (gripBefore != null && gripAfter != null)
            firstRigidBladeContact(gripBefore, gripAfter, enemySweep)?.takeUnless { contact ->
                contact.fraction <= 1e-9 && separatingSteelSweep(gripBefore, gripAfter, enemySweep, contact.normal)
            } else null
        val candidates = mutableListOf<IncomingContact>()
        // Enemy damage is live only during ACTIVE, but both visible weapons remain solid.
        if (combat.phase == EnemyPhase.ACTIVE && resolvedContactId != combat.currentAttackId) {
            fun body(zone: HitZone): BladeContact? {
                fun capsule(head: Vector3) = if (zone == HitZone.HEAD) BladeSegment(head, head, 0.16)
                    else BladeSegment(head + Vector3(0.0, -1.05, 0.0), head + Vector3(0.0, -0.23, 0.0), 0.24)
                return firstBladeContact(enemySweep, BladeSweep(capsule(from.headPosition), capsule(to.headPosition)))?.let {
                    it.copy(playerPoint = it.enemyPoint, enemyPoint = it.playerPoint, normal = it.normal * -1.0,
                        relativeDisplacement = it.relativeDisplacement * -1.0)
                }
            }
            for (zone in HitZone.values()) body(zone)?.let { candidates += IncomingContact(it, false, zone) }
        }
        // Outgoing damage uses the same moving body proxy and clock as the steel query.
        if (to.swing?.id?.let { it > consumedStrikeId } == true && gripBefore != null && gripAfter != null) {
            for (zone in HitZone.values()) {
                fun capsule(pose: EnemyContactPose) = if (zone == HitZone.HEAD) BladeSegment(pose.head, pose.head, 0.16)
                    else BladeSegment(pose.bodyBottom, pose.bodyTop, 0.24)
                firstRigidBladeContact(gripBefore, gripAfter, BladeSweep(capsule(before.contact), capsule(after.contact)))?.let {
                    candidates += IncomingContact(it, false, zone, playerAttack = true)
                }
            }
        }
        val body = candidates.minByOrNull { it.contact.fraction }
        return when {
            steel != null && (body == null || steel.fraction <= body.contact.fraction + 1e-9) -> IncomingContact(steel, true, HitZone.BODY)
            else -> body
        }
    }

    // 12 mm dao proxy plus 0.5 mm actor yaw/translation chord envelope. Actor yaw
    // is bounded to 1 rad/s and intervals to 10 ms; authored source keys split separately.
    private fun AttackPoseSample.blade() = BladeSegment(bladeBase, bladeTip, 0.0125)

    private fun nextAttackDirection(): AttackDirection = ATTACK_SEQUENCE[attackSequenceIndex]

    private fun synchronizeAttackBaseline() {
        val id = combat.currentAttackId ?: return
        if (observedAttackId != id) {
            observedAttackId = id
            resolvedContactId = null
        }
        motion.beginEnemyAttack(id)
    }

    private fun resolveSteelContact(contact: BladeContact, frame: PlayerMotionFrame, events: MutableList<EnemyCombatEvent>) {
        val id = combat.currentAttackId
        val direction = combat.currentAttackDirection
        val target = enemyPosition ?: return
        val active = combat.phase in setOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE) && id != null && direction != null
        val outcome = if (active && combat.phase == EnemyPhase.ACTIVE) motion.resolveDefense(checkNotNull(id), checkNotNull(direction), target,
            frame.receivedAtNanos, contact) else AttackOutcome.BLOCKED
        resolveContactOutcome(outcome, contact, HitZone.BODY, frame.hand, events, active)
    }

    private fun resolveBodyContact(contact: BladeContact, zone: HitZone, events: MutableList<EnemyCombatEvent>) {
        resolveContactOutcome(AttackOutcome.HIT_PLAYER, contact, zone,
            simulationMotion?.hand ?: Hand.RIGHT, events, true)
    }

    private fun resolveContactOutcome(initialOutcome: AttackOutcome, contact: BladeContact, zone: HitZone,
        hand: Hand, events: MutableList<EnemyCombatEvent>, active: Boolean) {
        val outcome = initialOutcome
        val id = combat.currentAttackId
        if (active && (id == null || resolvedContactId == id)) return
        if (outcome == AttackOutcome.BLOCKED) {
            // Steel still arrests the weapons at zero stamina; it cannot create an unobserved body hit.
            stamina = (stamina - 28.0).coerceAtLeast(0.0)
            focus = (focus + 10.0).coerceAtMost(100.0)
            score += 5
            notifyFeedback(CombatFeedback.BLOCK)
        } else if (outcome == AttackOutcome.PARRIED) {
            stamina = (stamina - 6.0).coerceAtLeast(0.0)
            focus = (focus + 30.0).coerceAtMost(100.0)
            score += 30
            notifyFeedback(CombatFeedback.PARRY)
        }
        val direction = contactRecovery?.direction ?: combat.currentAttackDirection
        val pose = enemyAttackPose()
        val poseFrame = effectiveEnemyPose()
        val attackOffsets = captureAttackOffsets()
        if (active) {
            resolvedContactId = id
            collect(combat.resolveActiveAttack(checkNotNull(id), outcome), events)
        }
        // Same clip returns from the actual source witness; never jump to a preset contact key.
        if (direction != null && pose != null) {
            contactRecovery = ContactRecovery(arenaOpponents[roundNumber - 1].attackProfile(direction), direction,
                pose.sourceSeconds, enemyMotionNanos,
                if (outcome == AttackOutcome.PARRIED) 550_000_000L else direction.recoveryNanos)
            enemyRecoveryFromContact = true
        }
        heldEnemyPoseFrame = poseFrame
        heldEnemyAttackOffsets = attackOffsets
        val kind = when (outcome) {
            AttackOutcome.BLOCKED -> CombatImpactKind.BLOCK
            AttackOutcome.PARRIED -> CombatImpactKind.PARRY
            AttackOutcome.HIT_PLAYER -> CombatImpactKind.PLAYER_HIT
            AttackOutcome.MISSED -> return
        }
        val motionContact = MotionContact(zone, if (outcome == AttackOutcome.HIT_PLAYER) contact.enemyPoint
            else (contact.playerPoint + contact.enemyPoint) * 0.5,
            contact.normal, (contact.relativeDisplacement * -1.0).normalizedOrNull())
        emitImpact(kind, motionContact, if (outcome == AttackOutcome.PARRIED) 1.0 else 0.65, hand, events)
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
                dealDamage(combat.health, true, CombatFeedback.EXECUTION, 80, events,
                    motion.targetContact(frame, enemy, HitZone.BODY), frame.hand)
            } else if (focus >= 100.0) {
                focus = 0.0
                dealDamage(55, true, CombatFeedback.SKILL, 35, events,
                    motion.targetContact(frame, enemy, HitZone.BODY), frame.hand)
            } else {
                notifyFeedback(CombatFeedback.LOW_FOCUS)
            }
            return
        }
        val strike = frame.strike ?: return
        if (strike.id <= consumedStrikeId) return
        consumedStrikeId = strike.id
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
        val kind = if (headshot) CombatFeedback.HEADSHOT else CombatFeedback.HIT
        dealDamage(damage, headshot && combo >= 3, kind, (if (headshot) 15 else 10) * combo,
            events, strike.contact, frame.hand, zone = strike.zone)
        focus = (focus + 12.0).coerceAtMost(100.0)
    }

    private fun dealDamage(
        damage: Int,
        breakGuard: Boolean,
        kind: CombatFeedback,
        points: Int,
        events: MutableList<EnemyCombatEvent>,
        contact: MotionContact,
        hand: Hand,
        zone: HitZone = HitZone.BODY,
    ) {
        val normal = kind == CombatFeedback.HIT || kind == CombatFeedback.HEADSHOT
        val poseFrame = effectiveEnemyPose()
        val attackOffsets = captureAttackOffsets()
        val outcome = combat.receivePlayerHit(
            damage, breakGuard, armGuard = normal && combo >= 2 && !breakGuard,
            counterDirection = nextAttackDirection(),
        )
        if (outcome.none { it is EnemyCombatEvent.EnemyDamaged }) return
        heldEnemyPoseFrame = poseFrame
        heldEnemyAttackOffsets = attackOffsets
        if (outcome.any { it is EnemyCombatEvent.HitReactionStarted && it.reaction == HitReaction.PLAYER_HIT }) {
            enemyHitZone = zone
        }
        score += points
        if (kind == CombatFeedback.SKILL) {
            val enemy = enemyPosition
            val head = latestTrackingSnapshot?.head?.pose?.position
            if (enemy != null && head != null) {
                val away = Vector3(enemy.x - head.x, 0.0, enemy.z - head.z).normalizedOrNull()
                if (away != null) enemyPosition = enemy + away * 0.35
            }
        }
        val damageResult = outcome.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().single()
        val guarded = damageResult.guarded
        notifyFeedback(if (normal && guarded) CombatFeedback.GUARDED_HIT else kind)
        collect(outcome, events)
        val impactKind = when {
            kind == CombatFeedback.SKILL -> CombatImpactKind.SKILL
            kind == CombatFeedback.EXECUTION -> CombatImpactKind.EXECUTION
            guarded -> CombatImpactKind.GUARDED_HIT
            kind == CombatFeedback.HEADSHOT -> CombatImpactKind.SOFT_HIT
            else -> arenaOpponents[roundNumber - 1].bodyImpact
        }
        val strength = when (impactKind) {
            CombatImpactKind.SKILL, CombatImpactKind.EXECUTION -> 1.0
            else -> (outcome.filterIsInstance<EnemyCombatEvent.EnemyDamaged>().sumOf { it.appliedDamage } / 40.0)
                .coerceIn(0.25, 1.0)
        }
        emitImpact(impactKind, contact, strength, hand, events,
            damageResult.appliedDamage, zone, damageResult.healthAfter == 0)
    }

    private fun emitImpact(
        kind: CombatImpactKind, contact: MotionContact, strength: Double, hand: Hand,
        events: MutableList<EnemyCombatEvent>,
        appliedDamage: Int = 0, zone: HitZone? = null, fatal: Boolean = false,
    ) {
        check(nextImpactId < Long.MAX_VALUE) { "impact id overflow" }
        val impact = CombatImpact(nextImpactId++, kind, contact.point, contact.normal, strength, hand,
            atNanos = combat.simulationNanos, appliedDamage = appliedDamage, zone = zone,
            fatal = fatal, tangent = contact.tangent)
        events += impact
        val stop = CombatFeedbackProfile.hitStopNanos(impact)
        hitStopNanos = maxOf(hitStopNanos, stop)
        if (stop > 0L) hitStopAwaitingPresentation = true
        if (fatal) deathHitStopNanos = hitStopNanos
        if (kind == CombatImpactKind.PLAYER_HIT || kind == CombatImpactKind.BLOCK) return
        val away = contact.normal * -1.0
        val awayFromPlayer = latestTrackingSnapshot?.head?.pose?.position?.let { head -> enemyPosition?.minus(head) }
        val direction = Vector3(away.x, 0.0, away.z).normalizedOrNull()
            ?: awayFromPlayer?.let { Vector3(it.x, 0.0, it.z).normalizedOrNull() }
            ?: Vector3(-kotlin.math.sin(enemyYaw.toDouble()), 0.0, -kotlin.math.cos(enemyYaw.toDouble()))
        recoilElapsedNanos = 0L
        recoilVector = direction * (0.025 + strength * 0.055)
    }

    private fun currentRecoilOffset(aheadNanos: Long = 0L): Vector3 {
        val progress = (recoilElapsedNanos + aheadNanos).coerceAtMost(RECOIL_DURATION).toDouble() / RECOIL_DURATION
        return recoilVector * (4.0 * progress * (1.0 - progress))
    }

    private fun effectiveEnemyPose(aheadNanos: Long = 0L): EnemyPoseFrame? {
        if (hitStopNanos > 0L && heldEnemyPoseFrame != null) return heldEnemyPoseFrame
        val recovery = contactRecovery
        if (recovery != null) {
            val elapsed = (enemyMotionNanos + aheadNanos - recovery.startedAtNanos - CONTACT_STOP_NANOS).coerceAtLeast(0L)
            val progress = (elapsed.toDouble() / (recovery.durationNanos - CONTACT_STOP_NANOS)).coerceIn(0.0, 1.0)
            val retreat = maxOf(recovery.profile.sourcePhaseSeconds.first(), recovery.sourceSeconds - 0.06)
            val source = if (progress < 0.18) recovery.sourceSeconds + (retreat - recovery.sourceSeconds) * progress / 0.18
                else retreat + (recovery.profile.sourcePhaseSeconds.last() - retreat) * (progress - 0.18) / 0.82
            return EnemyPoseFrame(recovery.profile.clip, recovery.profile.sample(source))
        }
        return arenaOpponents[roundNumber - 1].poseFrame(combat.phase, combat.phaseElapsedNanos + aheadNanos,
            combat.nanosUntilPhaseTransition?.minus(aheadNanos)?.coerceAtLeast(0L),
            combat.currentAttackDirection ?: AttackDirection.OVERHEAD, combat.guarding,
            enemyMoveDirection != 0f, enemyRecoveryFromContact, enemyGaitMeters, combat.hitReaction, enemyHitZone)
    }

    private fun enemyContactPose(): EnemyContactPose? = enemyAttackPose()?.contact ?: enemyPosition?.let(EnemyContactPose::standing)

    private fun enemyAttackPose(aheadNanos: Long = 0L): AttackPoseSample? {
        val origin = enemyPosition?.plus(currentRecoilOffset(aheadNanos)) ?: return null
        val held = heldEnemyAttackOffsets
        if (hitStopNanos > 0L && held != null) return held.inStage(origin, 0f)
        return effectiveEnemyPose(aheadNanos)?.pose?.inStage(origin, enemyYaw)
    }

    private fun captureAttackOffsets(): AttackPoseSample? {
        val origin = enemyPosition?.plus(currentRecoilOffset()) ?: return null
        return enemyAttackPose()?.inStage(origin * -1.0, 0f)
    }

    private fun collect(incoming: List<EnemyCombatEvent>, events: MutableList<EnemyCombatEvent>) {
        events += incoming
        for (event in incoming) {
            when (event) {
                is EnemyCombatEvent.AttackStarted -> {
                    contactRecovery = null
                    attackSequenceIndex = (attackSequenceIndex + 1) % ATTACK_SEQUENCE.size
                    enemyRecoveryFromContact = false
                    heldEnemyPoseFrame = null
                    heldEnemyAttackOffsets = null
                    observedAttackId = event.attackId
                    resolvedContactId = null
                            motion.beginEnemyAttack(event.attackId)
                }
                is EnemyCombatEvent.AttackResolved -> {
                    enemyRecoveryFromContact = event.outcome != AttackOutcome.MISSED
                    if (event.outcome == AttackOutcome.HIT_PLAYER) {
                        playerHealth = (playerHealth - if (matchNanos < staggerUntil) 30 else 20).coerceAtLeast(0)
                        combo = 0
                        if (feedback != CombatFeedback.GUARD_BREAK) notifyFeedback(CombatFeedback.PLAYER_HIT)
                        if (playerHealth == 0) finishDefeat(CombatFeedback.PLAYER_HIT, events)
                    }
                }
                is EnemyCombatEvent.HitReactionStarted -> if (event.reaction == HitReaction.PARRIED) {
                    enemyHitZone = null
                }
                is EnemyCombatEvent.AttackCancelled -> enemyRecoveryFromContact = false
                is EnemyCombatEvent.PhaseChanged -> {
                    if (event.current == EnemyPhase.IDLE || event.current == EnemyPhase.DEAD) {
                        contactRecovery = null
                        enemyRecoveryFromContact = false
                    }
                    if (event.current != EnemyPhase.HIT) enemyHitZone = null
                    if (event.current == EnemyPhase.DEAD && result == TrialResult.FIGHTING) {
                        result = TrialResult.ROUND_CLEAR
                        intermissionNanos = 0L
                        combo = 0
                        pendingMotion.clear()
                        score += 100
                    }
                }
                else -> Unit
            }
        }
    }

    private fun finishDefeat(kind: CombatFeedback, events: MutableList<EnemyCombatEvent>) {
        result = TrialResult.DEFEAT
        pendingMotion.clear()
        events += combat.pauseByPlayer()
        bestScore = maxOf(bestScore, score)
        notifyFeedback(kind)
    }

    private data class EnemyLocomotion(val position: Vector3?, val yaw: Float,
        val travel: Double, val gait: Double, val direction: Float)
    private fun captureEnemyLocomotion() = EnemyLocomotion(enemyPosition, enemyYaw, enemyTravelMeters, enemyGaitMeters, enemyMoveDirection)
    private fun restoreEnemyLocomotion(value: EnemyLocomotion) {
        enemyPosition = value.position
        enemyYaw = value.yaw
        enemyTravelMeters = value.travel
        enemyGaitMeters = value.gait
        enemyMoveDirection = value.direction
    }

    private fun moveEnemy(delta: Long, headPosition: Vector3? = simulationMotion?.headPosition ?: latestTrackingSnapshot?.head?.pose?.position) {
        if (delta == 0L) return
        enemyMoveDirection = 0f
        val head = headPosition ?: return
        val enemy = enemyPosition ?: return
        if (hitStopNanos > 0L || combat.phase != EnemyPhase.IDLE) return
        val toward = Vector3(head.x - enemy.x, 0.0, head.z - enemy.z)
        val distance = toward.length()
        if (distance > 0.01) {
            val desiredYaw = atan2(toward.x, toward.z)
            val turn = atan2(kotlin.math.sin(desiredYaw - enemyYaw), kotlin.math.cos(desiredYaw - enemyYaw))
            enemyYaw += turn.coerceIn(-delta / 1_000_000_000.0, delta / 1_000_000_000.0).toFloat()
        }
        val direction = toward.normalizedOrNull() ?: return
        // Native slash reaches about 1.2 m from the actor. Leave the remaining contact allowance to the body volume.
        val desired = 1.30
        val difference = distance - desired
        val travel = (delta / 1_000_000_000.0 * 0.65).coerceAtMost(kotlin.math.abs(difference))
        if (kotlin.math.abs(difference) > 0.05 && travel > 0.0) {
            enemyMoveDirection = if (difference > 0.0) 1f else -1f
            enemyPosition = enemy + direction * (travel * enemyMoveDirection)
            enemyTravelMeters += travel
            enemyGaitMeters += travel * enemyMoveDirection
        }
    }

    private fun beginNextRound(events: MutableList<EnemyCombatEvent>) {
        val resumeRequired = combat.pauseReason != null || !viewState.actionReady
        roundNumber++
        clearEnemyContactPlayback()
        attackSequenceIndex = 0
        enemyRecoveryFromContact = false
        check(roundGeneration < Long.MAX_VALUE) { "round generation overflow" }
        roundGeneration++
        initialHealth = 100 + (roundNumber - 1) * 25
        combat = EnemyCombatStateMachine(initialHealth, 800_000_000L - (roundNumber - 1) * 100_000_000L)
        enemyHitZone = null
        enemyPosition = enemySpawn
        enemyYaw = 0f
        enemyTravelMeters = 0.0
        enemyGaitMeters = 0.0
        enemyMoveDirection = 0f
        executionActive = false
        hitStopNanos = 0L
        hitStopAwaitingPresentation = false
        deathHitStopNanos = 0L
        intermissionNanos = 0L
        recoilElapsedNanos = 0L
        recoilVector = Vector3(0.0, 0.0, 0.0)
        heldEnemyPoseFrame = null
        heldEnemyAttackOffsets = null
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
    private fun intermissionDuration(): Long =
        (if (executionActive) 5_000_000_000L else 3_200_000_000L) +
            deathHitStopNanos + CombatFeedbackProfile.DEATH_SLOWDOWN_DELAY_NANOS

    private fun clearEnemyContactPlayback() {
        enemyMotionNanos = 0L
        contactRecovery = null
        heldEnemyAttackOffsets = null
        heldEnemyPoseFrame = null
    }

    private fun clearMotion() {
        motion.reset()
        latestMotion = null
        simulationMotion = null
        steelContactLatched = false
        contactUncertainReceipt = null
        pendingMotion.clear()
        observedAttackId = null
        resolvedContactId = null
        consumedStrikeId = -1L
    }

    private companion object {
        val ATTACK_SEQUENCE = listOf(AttackDirection.OVERHEAD, AttackDirection.LEFT, AttackDirection.RIGHT)
        const val SECOND = 1_000_000_000L
        const val MATCH_DURATION = 180L * SECOND
        const val COUNTDOWN_DURATION = 3L * SECOND
        const val COMBO_WINDOW = 1_600_000_000L
        const val RECOIL_DURATION = 220_000_000L
        const val CONTACT_STOP_NANOS = 35_000_000L
    }

    fun setPlayerHandPresenter(presenter: HandPosePresenter?) {
        playerHandPresenter = presenter
        presentHand(latestTrackingSnapshot)
    }

    /** Expected visual replacement freezes action and clocks without impersonating lost tracking. */
    fun beginOpponentChange(expectedGeneration: Long, expectedRoundNumber: Int): Boolean {
        if (expectedGeneration != roundGeneration || expectedRoundNumber != roundNumber) return false
        sceneAvailable = false
        enemyReachMeters = 0.0
        revokeActionBaseline(lastAcceptedStamp?.sequence ?: -1L)
        lastReportedHead = null
        publish(source = "opponent_change")
        return true
    }

    fun setEnemyGeometry(position: Vector3?, reachMeters: Double) {
        val wasAvailable = sceneAvailable
        clearEnemyContactPlayback()
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
        publish(events, source = "enemy_geometry")
    }

    fun onTrackingEvent(event: TrackingEvent, accepted: Boolean, snapshot: TrackingSnapshot, uiFrameNanos: Long? = null) {
        val publishSource = when (event) {
            is TrackingEvent.Head -> "tracking_head"
            is TrackingEvent.Controllers -> "tracking_controllers"
            is TrackingEvent.Discontinuity -> "tracking_control_${event.reason}"
            is TrackingEvent.DominantHandChanged -> "tracking_dominant_hand"
        }
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
                clearEnemyContactPlayback()
                combat = EnemyCombatStateMachine()
                enemyHitZone = null
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
                attackSequenceIndex = 0
                enemyRecoveryFromContact = false
                matchNanos = 0L
                countdownNanos = 0L
                intermissionNanos = 0L
                executionActive = false
                hitStopNanos = 0L
                hitStopAwaitingPresentation = false
                deathHitStopNanos = 0L
                recoilElapsedNanos = 0L
                recoilVector = Vector3(0.0, 0.0, 0.0)
                heldEnemyPoseFrame = null
                heldEnemyAttackOffsets = null
                staggerUntil = 0L
                feedback = null
                enemyPosition = enemySpawn
                enemyYaw = 0f
                enemyTravelMeters = 0.0
                enemyGaitMeters = 0.0
                enemyMoveDirection = 0f
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
        // Visual hands consume both accepted sides, including invalidation snapshots.
        presentHand(snapshot)
        if (!snapshot.hasRequiredObservations) {
            lastTickTime = null
            lastReportedHead = null
            if (!reportedWaiting) {
                reportedWaiting = true
                logMessage("Combat input waiting for head and dominant-hand observations; sequence=${event.stamp.sequence}")
            }
            publish(events, source = publishSource, uiFrameNanos = uiFrameNanos)
            return
        }
        if (!newlyAccepted) {
            publish(events, source = publishSource, uiFrameNanos = uiFrameNanos)
            return
        }
        establishActionBaseline()
        val target = enemyPosition
        if (sceneAvailable && target != null && viewState.actionReady) {
            val frame = try { motion.observe(snapshot, target, checkNotNull(enemyContactPose())) }
                catch (uncertain: BladeContactUncertainException) {
                    if (contactQueryFailures++ < 4) logMessage("Player contact query held: ${uncertain.message}")
                    contactUncertainReceipt = event.stamp.receivedAtNanos
                    null
                }
            logNativeMotion(event, snapshot, frame)
            if (result != TrialResult.FIGHTING || simulationMotion == null) latestMotion = frame
            if (frame != null && result == TrialResult.FIGHTING && combat.pauseReason == null) {
                fun sameSample(other: PlayerMotionFrame?) = other?.observationSequence == frame.observationSequence &&
                    other.motionGeneration == frame.motionGeneration
                if (!sameSample(pendingMotion.lastOrNull()) && !sameSample(simulationMotion)) {
                    if (pendingMotion.size >= 64) {
                        events += combat.interruptTracking()
                        revokeActionBaseline(event.stamp.sequence)
                    } else {
                        pendingMotion.addLast(frame)
                    }
                }
            }
        }
        reportedWaiting = false
        logInput(event, snapshot)
        publish(events, source = publishSource, uiFrameNanos = uiFrameNanos)
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
        lastNativeMotionLogNanos = null
        lastNativeMotionPoses = null
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

    /** Observe the resolver's real output without authoring or changing any motion. */
    private fun logNativeMotion(event: TrackingEvent, snapshot: TrackingSnapshot, frame: PlayerMotionFrame?) {
        if (event.stamp.origin != InputOrigin.DESKTOP) return
        val poses = Triple(snapshot.head?.pose, snapshot.left?.pose, snapshot.right?.pose)
        if (poses == lastNativeMotionPoses) return
        val now = event.stamp.receivedAtNanos
        val previous = lastNativeMotionLogNanos
        if (previous != null && now - previous < 200_000_000L) return
        lastNativeMotionLogNanos = now
        lastNativeMotionPoses = poses
        logMessage(
            "Native motion observed source=SDK_NATIVE origin=${event.stamp.origin} " +
                "sequence=${event.stamp.sequence} coordinateEpoch=${event.stamp.coordinateEpoch} " +
                "receivedAtNanos=$now roundGeneration=$roundGeneration " +
                "headSequence=${snapshot.head?.stamp?.sequence} leftSequence=${snapshot.left?.stamp?.sequence} " +
                "rightSequence=${snapshot.right?.stamp?.sequence} " +
                "head=${poses.first} left=${poses.second} right=${poses.third} " +
                "motionResult={frameAvailable=${frame != null} receivedAtNanos=${frame?.receivedAtNanos} " +
                "bladeBase=${frame?.bladeBase} bladeTip=${frame?.bladeTip} bladeTipSpeed=${frame?.bladeTipSpeed} " +
                "strike=${frame?.strike} guard=${frame?.guardDirection} skill=${frame?.skillGesture} " +
                "release=${frame?.releaseRequired} motionGeneration=${frame?.motionGeneration}}",
        )
    }

    private fun presentHand(snapshot: TrackingSnapshot?) {
        try {
            playerHandPresenter?.invoke(snapshot)
        } catch (error: Exception) {
            logFailure("Player-hand presentation failed", error)
        }
    }

    private fun publish(events: List<EnemyCombatEvent> = emptyList(), source: String, uiFrameNanos: Long? = null) {
        try {
            val state = viewState.copy(diagnosticUiFrameNanos = uiFrameNanos, diagnosticPublishSource = source)
            arenaPresenter?.invoke(state, events.toList())
        } catch (error: Exception) {
            logFailure("Arena presentation failed", error)
        } finally {
            // Presentation failure must not leave combat permanently waiting for a callback.
            hitStopAwaitingPresentation = false
        }
    }
}
