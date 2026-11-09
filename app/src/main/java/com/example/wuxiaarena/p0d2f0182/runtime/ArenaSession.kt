package com.example.wuxiaarena.p0d2f0182.runtime

import android.util.Log
import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.PauseReason
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
import kotlin.math.hypot

typealias HandPosePresenter = (ObservedPose?) -> Unit

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
)

internal typealias ArenaPresenter = (ArenaViewState, List<EnemyCombatEvent>) -> Unit

/** One-thread owner of trial state, tracking gates and presentation delivery. */
internal class ArenaSession(
    private val logMessage: (String) -> Unit = { message -> Log.i("ArenaCombat", message) },
    private val logFailure: (String, Throwable) -> Unit = { context, error ->
        Log.e("ArenaCombat", context, error)
    },
) {
    private val combat = EnemyCombatStateMachine()
    private val initialHealth = combat.health
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
            val sceneReady = enemyPosition != null
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
            )
        }

    fun setArenaPresenter(presenter: ArenaPresenter?) {
        arenaPresenter = presenter
        publish()
    }

    fun startTrial(): Boolean {
        val state = viewState
        if (trialStarted || !state.sceneReady || !state.inputReady || state.pauseReason != null) return false
        trialStarted = true
        lastTickTime = null
        publish()
        return true
    }

    /** Called after the input owner drains pending controls and observations. */
    fun confirmResume(pauseId: Long): Boolean {
        val state = viewState
        if (state.pauseId != pauseId || !state.resumeReady) return false
        val events = combat.tryResume(state.inputReady, state.actionReady, pauseId)
        if (combat.pauseReason != null) return false
        lastTickTime = null
        publish(events)
        return true
    }

    /** The input owner calls this once after all drains, using its receipt clock. */
    fun onTick(nowNanos: Long) {
        val targetInRange = currentTargetInRange()
        if (!trialStarted || targetInRange == null || combat.pauseReason != null || !viewState.actionReady) {
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
        val events = combat.advanceBy(delta, targetInRange).toMutableList()
        events += combat.tryStartAttack(AttackDirection.OVERHEAD, targetInRange)
        publish(events)
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
        enemyPosition = position?.takeIf { it.isFinite() && reachMeters.isFinite() && reachMeters > 0.0 }
        enemyReachMeters = if (enemyPosition == null) 0.0 else reachMeters
        lastTickTime = null
        actionBaseline = null
        establishActionBaseline()
        lastReportedHead = null
        logMessage("Enemy geometry available=${enemyPosition != null}; boundsReachMeters=$enemyReachMeters")
        publish()
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
                events += combat.resetRound()
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
        reportedWaiting = false
        logInput(event, snapshot)
        publish(events)
    }

    private fun establishActionBaseline() {
        val snapshot = latestTrackingSnapshot ?: return
        if (enemyPosition == null || !snapshot.hasRequiredObservations) return
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
