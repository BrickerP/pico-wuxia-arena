package com.example.wuxiaarena.p0d2f0182.runtime

import android.util.Log
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.hypot

typealias HandPosePresenter = (ObservedPose?) -> Unit

/** Owns the common tracking-to-combat readiness path for the current arena. */
internal class ArenaSession(
    private val logMessage: (String) -> Unit = { message -> Log.i("ArenaCombat", message) },
) {
    private val combat = EnemyCombatStateMachine()
    private var enemyPosition: Vector3? = null
    private var enemyReachMeters = 0.0
    private var lastInputTime: Long? = null
    private var lastReportTime: Long? = null
    private var lastReportedHead: Vector3? = null
    private var lastReportedHand: Vector3? = null
    private var lastReportedEligibility: Boolean? = null
    private var hadReadyInput = false
    private var reportedWaiting = false
    private var playerHandPresenter: HandPosePresenter? = null
    private var latestTrackingSnapshot: TrackingSnapshot? = null

    fun setPlayerHandPresenter(presenter: HandPosePresenter?) {
        playerHandPresenter = presenter
        val snapshot = latestTrackingSnapshot
        val handPose = if (snapshot?.hasRequiredObservations == true) {
            val hand = if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right
            hand?.pose
        } else {
            null
        }
        presenter?.invoke(handPose)
    }

    fun setEnemyGeometry(position: Vector3?, reachMeters: Double) {
        enemyPosition = position?.takeIf { it.isFinite() && reachMeters.isFinite() && reachMeters > 0.0 }
        enemyReachMeters = if (enemyPosition == null) 0.0 else reachMeters
        if (enemyPosition == null) lastInputTime = null
        lastReportedHead = null
        logMessage("Enemy geometry available=${enemyPosition != null}; boundsReachMeters=$enemyReachMeters")
    }

    fun onTrackingEvent(event: TrackingEvent, accepted: Boolean, snapshot: TrackingSnapshot) {
        latestTrackingSnapshot = snapshot
        if (accepted && event is TrackingEvent.Discontinuity && event.reason == DiscontinuityReason.ROUND_RESET) {
            combat.resetRound()
            lastInputTime = null
            lastReportTime = null
            lastReportedHead = null
            hadReadyInput = false
        }
        if (!snapshot.hasRequiredObservations) {
            playerHandPresenter?.invoke(null)
            lastInputTime = null
            lastReportedHead = null
            if (hadReadyInput) {
                combat.interruptTracking()
                hadReadyInput = false
            }
            if (!reportedWaiting) {
                reportedWaiting = true
                logMessage("Combat input waiting for head and dominant-hand observations; sequence=${event.stamp.sequence}")
            }
            return
        }
        if (!accepted) return
        val head = snapshot.head ?: return
        val headPosition = head.pose?.position ?: return
        val hand = if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right
        val handPose = hand?.pose ?: return
        val handPosition = handPose.position ?: return
        playerHandPresenter?.invoke(handPose)
        if (event !is TrackingEvent.Controllers) return
        val enemy = enemyPosition ?: return
        val distance = hypot(headPosition.x - enemy.x, headPosition.z - enemy.z)
        // This conservative bounds radius controls attack eligibility, not contact or damage.
        val targetInRange = distance <= enemyReachMeters
        val now = event.stamp.receivedAtNanos
        lastInputTime?.let { previous ->
            if (now >= previous) combat.advanceBy(now - previous, targetInRange)
        }
        lastInputTime = now
        hadReadyInput = true
        reportedWaiting = false
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
}
