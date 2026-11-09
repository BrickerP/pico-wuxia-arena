package com.example.wuxiaarena.p0d2f0182.runtime

import android.util.Log
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.DiscontinuityReason
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.hypot

/** Owns the common tracking-to-combat readiness path for the current arena. */
internal class ArenaSession {
    private val combat = EnemyCombatStateMachine()
    private var enemyPosition: Vector3? = null
    private var enemyReachMeters = 0.0
    private var lastInputTime: Long? = null
    private var lastReportTime: Long? = null
    private var hadReadyInput = false
    private var reportedWaiting = false

    fun setEnemyGeometry(position: Vector3?, reachMeters: Double) {
        enemyPosition = position?.takeIf { it.isFinite() && reachMeters.isFinite() && reachMeters > 0.0 }
        enemyReachMeters = if (enemyPosition == null) 0.0 else reachMeters
        Log.i("ArenaCombat", "Enemy geometry available=${enemyPosition != null}; boundsReachMeters=$enemyReachMeters")
    }

    fun onTrackingEvent(event: TrackingEvent, accepted: Boolean, snapshot: TrackingSnapshot) {
        if (accepted && event is TrackingEvent.Discontinuity && event.reason == DiscontinuityReason.ROUND_RESET) {
            combat.resetRound()
            lastInputTime = null
            lastReportTime = null
            hadReadyInput = false
        }
        if (!snapshot.hasRequiredObservations) {
            lastInputTime = null
            if (hadReadyInput) {
                combat.interruptTracking()
                hadReadyInput = false
            }
            if (!reportedWaiting) {
                reportedWaiting = true
                Log.i("ArenaCombat", "Combat input waiting for head and dominant-hand observations; sequence=${event.stamp.sequence}")
            }
            return
        }
        if (!accepted) return
        if (event !is TrackingEvent.Controllers) return
        val enemy = enemyPosition ?: return
        val head = snapshot.head ?: return
        val headPosition = head.pose?.position ?: return
        val hand = if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right
        val handPosition = hand?.pose?.position ?: return
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
        if (lastReport == null || now < lastReport || now - lastReport >= 100_000_000L) {
            lastReportTime = now
            Log.i(
                "ArenaCombat",
                "Combat input evaluated origin=${event.stamp.origin}, sequence=${event.stamp.sequence}, " +
                    "headSequence=${head.stamp.sequence}, handSequence=${hand.stamp.sequence}, " +
                    "head=$headPosition, hand=$handPosition, distanceMeters=$distance, " +
                    "targetInRange=$targetInRange, canStartAttack=$canStartAttack, phase=${combat.phase}",
            )
        }
    }
}
