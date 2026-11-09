package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import kotlin.math.abs
import kotlin.math.acos
import kotlin.math.ceil
import kotlin.math.sin

enum class HitZone { BODY, HEAD }

data class MotionStrike(val id: Long, val zone: HitZone, val power: Double)

data class PlayerMotionFrame(
    val receivedAtNanos: Long,
    val bladeBase: Vector3,
    val bladeTip: Vector3,
    val bladeTipSpeed: Double,
    val strike: MotionStrike?,
    val skillGesture: Boolean,
    val headPosition: Vector3,
    val guardDirection: AttackDirection? = null,
    val chargeProgress: Float = 0f,
)

/**
 * One-thread motion recognizer shared by device input and desktop pose rehearsal.
 * Its body capsules are gameplay hit volumes calibrated to the 1.78 m character.
 * They describe the trial's contact rules independently of the rendered skin.
 */
class PlayerCombatResolver {
    private data class Identity(
        val hand: Hand,
        val epoch: Long,
        val headContinuity: Long,
        val handContinuity: Long,
        val requiredSinceSequence: Long,
    )

    private data class BladeSample(
        val stamp: ObservationStamp,
        val base: Vector3,
        val tip: Vector3,
        val rotation: Quaternion,
    )

    private var identity: Identity? = null
    private var previous: BladeSample? = null
    private var latestFrame: PlayerMotionFrame? = null
    private var lastHeadStamp: ObservationStamp? = null
    private var strokeOrigin: BladeSample? = null
    private var strokeTravel = 0.0
    private var strokeHasHit = false
    private var previousDirection: Vector3? = null
    private var quietSince: Long? = null
    private var outsideSince: Long? = null
    private var lastStrikeAt: Long? = null
    private var nextStrikeId = 1L
    private var currentGuard: AttackDirection? = null
    private var guardEnteredAt: Long? = null
    private var fastGuardAt: Long? = null
    private var attackId: Long? = null
    private var attackHeadBaseline: Vector3? = null
    private var resolvedAttackId: Long? = null
    private var resolvedOutcome = AttackOutcome.MISSED
    private var chargeStartedAt: Long? = null
    private var chargeOrigin: Vector3? = null
    private var chargeForward: Vector3? = null
    private var previousHandsOffset: Vector3? = null
    private var previousHandsAt: Long? = null
    private var skillLatched = false
    private var lastSkillAt: Long? = null
    private var skillHandContinuity: Long? = null

    /** First samples and duplicate hand observations cannot produce a strike. */
    fun observe(snapshot: TrackingSnapshot, enemyPosition: Vector3): PlayerMotionFrame? {
        if (!snapshot.hasRequiredObservations || !enemyPosition.isFinite()) return clearUnavailable()
        val head = snapshot.head ?: return clearUnavailable()
        val hand = (if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right)
            ?: return clearUnavailable()
        val headPosition = head.positionOrNull() ?: return clearUnavailable()
        val handPosition = hand.positionOrNull() ?: return clearUnavailable()
        val rotation = hand.pose?.rotation?.normalizedOrNull() ?: return clearUnavailable()
        if (abs(secondsBetween(head.stamp.receivedAtNanos, hand.stamp.receivedAtNanos)) > MAX_SAMPLE_GAP) {
            return clearUnavailable()
        }
        val headStamp = lastHeadStamp
        if (headStamp != null && (head.stamp.sequence < headStamp.sequence ||
                head.stamp.receivedAtNanos < headStamp.receivedAtNanos)) {
            return clearUnavailable()
        }
        val currentIdentity = Identity(
            snapshot.dominantHand,
            hand.stamp.coordinateEpoch,
            snapshot.headContinuity,
            if (snapshot.dominantHand == Hand.LEFT) snapshot.leftContinuity else snapshot.rightContinuity,
            snapshot.requiredSinceSequence,
        )
        if (head.stamp.coordinateEpoch != hand.stamp.coordinateEpoch) return clearUnavailable()
        if (identity != currentIdentity) {
            reset()
            identity = currentIdentity
        }
        lastHeadStamp = head.stamp
        val base = rotation.rotate(BLADE_BASE)?.plus(handPosition) ?: return clearUnavailable()
        val tip = rotation.rotate(BLADE_TIP)?.plus(handPosition) ?: return clearUnavailable()
        if (!base.isFinite() || !tip.isFinite() || base.distanceTo(tip) !in 0.70..0.74) {
            return clearUnavailable()
        }
        val sample = BladeSample(hand.stamp, base, tip, rotation)
        val old = previous
        if (old == null) return establish(sample, headPosition, enemyPosition)
        if (sample.stamp.sequence == old.stamp.sequence) {
            val frame = latestFrame?.copy(headPosition = headPosition, strike = null, skillGesture = false)
            latestFrame = frame
            return frame
        }
        val elapsed = secondsBetween(sample.stamp.receivedAtNanos, old.stamp.receivedAtNanos)
        if (sample.stamp.sequence < old.stamp.sequence || elapsed <= 0.0 || elapsed > MAX_SAMPLE_GAP ||
            rotationDistance(old.rotation, rotation) > MAX_ROTATION_STEP) {
            reset()
            identity = currentIdentity
            lastHeadStamp = head.stamp
            return establish(sample, headPosition, enemyPosition)
        }

        val tipMovement = tip - old.tip
        val baseMovement = base - old.base
        val tipDistance = tipMovement.length()
        val baseDistance = baseMovement.length()
        val movement = if (tipDistance >= baseDistance) tipMovement else baseMovement
        val distance = maxOf(tipDistance, baseDistance)
        val speed = distance / elapsed
        if (!speed.isFinite() || speed > MAX_PLAUSIBLE_TIP_SPEED) {
            reset()
            identity = currentIdentity
            lastHeadStamp = head.stamp
            return establish(sample, headPosition, enemyPosition)
        }
        val zone = contactZone(sample, old, enemyPosition)
        val inside = contactZone(sample, null, enemyPosition) != null
        val direction = movement.normalizedOrNull()
        updateStroke(sample, speed, direction, inside)
        strokeTravel += distance
        val displacement = strokeOrigin?.let { maxOf(it.tip.distanceTo(tip), it.base.distanceTo(base)) } ?: 0.0
        val strike = if (!strokeHasHit && zone != null && speed >= MIN_STRIKE_SPEED &&
            strokeTravel >= MIN_STRIKE_TRAVEL && displacement >= MIN_STRIKE_DISPLACEMENT &&
            elapsedSince(sample.stamp.receivedAtNanos, lastStrikeAt) >= STRIKE_COOLDOWN &&
            nextStrikeId < Long.MAX_VALUE) {
            strokeHasHit = true
            lastStrikeAt = sample.stamp.receivedAtNanos
            MotionStrike(nextStrikeId++, zone, (speed / 2.2).coerceIn(1.0, 1.4))
        } else {
            null
        }
        updateGuard(sample, headPosition, enemyPosition, speed, true)
        val skill = updateSkill(snapshot, headPosition, enemyPosition, sample.stamp.receivedAtNanos)
        previous = sample
        previousDirection = direction ?: previousDirection
        val channeling = chargeStartedAt != null || chargeOrigin != null || skillLatched ||
            elapsedSince(sample.stamp.receivedAtNanos, lastSkillAt) < 0.45
        val chargeProgress = when {
            chargeOrigin != null -> 1f
            chargeStartedAt != null -> (elapsedSince(sample.stamp.receivedAtNanos, chargeStartedAt) / SKILL_CHARGE).coerceIn(0.0, 1.0).toFloat()
            else -> 0f
        }
        val frame = PlayerMotionFrame(sample.stamp.receivedAtNanos, base, tip, tipDistance / elapsed,
            if (channeling) null else strike, skill, headPosition, currentGuard, chargeProgress)
        latestFrame = frame
        return frame
    }

    fun beginEnemyAttack(attackId: Long, headPosition: Vector3) {
        if (this.attackId == attackId) return
        this.attackId = attackId
        attackHeadBaseline = headPosition.takeIf { it.isFinite() }
        resolvedAttackId = null
    }

    /** The caller resolves at the current attack's contact point, before advancing past ACTIVE. */
    fun resolveDefense(attackId: Long, direction: AttackDirection, enemyPosition: Vector3, receivedAtNanos: Long): AttackOutcome {
        if (resolvedAttackId == attackId) return resolvedOutcome
        val frame = latestFrame
        val baseline = attackHeadBaseline
        val result = when {
            this.attackId != attackId || frame == null || baseline == null || !enemyPosition.isFinite() -> {
                AttackOutcome.HIT_PLAYER
            }
            isDodge(frame.headPosition, baseline, enemyPosition) -> AttackOutcome.MISSED
            guardDirection(frame.bladeBase, frame.bladeTip, frame.headPosition, enemyPosition) != direction -> {
                AttackOutcome.HIT_PLAYER
            }
            elapsedSince(receivedAtNanos, guardEnteredAt) <= PARRY_WINDOW &&
                elapsedSince(receivedAtNanos, fastGuardAt) <= PARRY_WINDOW -> AttackOutcome.PARRIED
            else -> AttackOutcome.BLOCKED
        }
        resolvedAttackId = attackId
        resolvedOutcome = result
        return result
    }

    fun reset() {
        identity = null
        previous = null
        latestFrame = null
        lastHeadStamp = null
        strokeOrigin = null
        strokeTravel = 0.0
        strokeHasHit = false
        previousDirection = null
        quietSince = null
        outsideSince = null
        lastStrikeAt = null
        currentGuard = null
        guardEnteredAt = null
        fastGuardAt = null
        attackId = null
        attackHeadBaseline = null
        resolvedAttackId = null
        clearCharge()
        skillLatched = false
        lastSkillAt = null
        skillHandContinuity = null
    }

    private fun clearUnavailable(): PlayerMotionFrame? {
        reset()
        return null
    }

    private fun establish(sample: BladeSample, head: Vector3, enemy: Vector3): PlayerMotionFrame {
        previous = sample
        startStroke(sample)
        updateGuard(sample, head, enemy, 0.0, false)
        return PlayerMotionFrame(sample.stamp.receivedAtNanos, sample.base, sample.tip, 0.0, null, false, head, currentGuard)
            .also { latestFrame = it }
    }

    private fun updateStroke(sample: BladeSample, speed: Double, direction: Vector3?, inside: Boolean) {
        val now = sample.stamp.receivedAtNanos
        quietSince = if (speed <= REST_SPEED) quietSince ?: now else null
        outsideSince = if (!inside) outsideSince ?: now else null
        val reversed = direction != null && previousDirection?.dot(direction)?.let { it < -0.35 } == true
        val released = (quietSince != null && elapsedSince(now, quietSince) >= REST_RELEASE) ||
            (strokeHasHit && outsideSince != null && elapsedSince(now, outsideSince) >= OUTSIDE_RELEASE) || reversed
        if (released && elapsedSince(now, lastStrikeAt) >= STRIKE_COOLDOWN) {
            startStroke(previous ?: sample)
        }
    }

    private fun startStroke(sample: BladeSample) {
        strokeOrigin = sample
        strokeTravel = 0.0
        strokeHasHit = false
        quietSince = null
        outsideSince = null
    }

    private fun updateGuard(sample: BladeSample, head: Vector3, enemy: Vector3, speed: Double, moving: Boolean) {
        val direction = guardDirection(sample.base, sample.tip, head, enemy)
        if (direction != currentGuard) {
            currentGuard = direction
            guardEnteredAt = if (direction == null) null else sample.stamp.receivedAtNanos
            fastGuardAt = null
        }
        if (direction != null && moving && speed >= MIN_PARRY_SPEED) fastGuardAt = sample.stamp.receivedAtNanos
    }

    private fun guardDirection(base: Vector3, tip: Vector3, head: Vector3, enemy: Vector3): AttackDirection? {
        val forward = horizontal(enemy - head).normalizedOrNull() ?: return null
        val right = forward.cross(UP)
        val axis = (tip - base).normalizedOrNull() ?: return null
        val point = closestPoint(head + forward * 0.32, base, tip)
        val offset = point - head
        if (offset.dot(forward) !in 0.08..1.0 || offset.length() > 0.85) return null
        if (offset.y >= -0.12 && abs(axis.dot(right)) >= 0.55 && abs(axis.y) <= 0.65) {
            return AttackDirection.OVERHEAD
        }
        if (abs(axis.y) < 0.5) return null
        val side = offset.dot(right)
        return when {
            side < -0.08 -> AttackDirection.LEFT
            side > 0.08 -> AttackDirection.RIGHT
            else -> null
        }
    }

    private fun isDodge(head: Vector3, baseline: Vector3, enemy: Vector3): Boolean {
        if (horizontal(head - enemy).length() > ENEMY_REACH) return true
        val forward = horizontal(enemy - baseline).normalizedOrNull() ?: return true
        val right = forward.cross(UP)
        return abs((head - baseline).dot(right)) >= DODGE_TRAVEL || baseline.y - head.y >= DUCK_TRAVEL
    }

    private fun updateSkill(snapshot: TrackingSnapshot, head: Vector3, enemy: Vector3, now: Long): Boolean {
        val otherContinuity = if (snapshot.dominantHand == Hand.LEFT) snapshot.rightContinuity else snapshot.leftContinuity
        if (skillHandContinuity != otherContinuity) {
            clearCharge()
            skillLatched = false
            skillHandContinuity = otherContinuity
        }
        val leftObservation = snapshot.left
        val rightObservation = snapshot.right
        val left = leftObservation?.positionOrNull()
        val right = rightObservation?.positionOrNull()
        val leftTime = leftObservation?.stamp?.receivedAtNanos
        val rightTime = rightObservation?.stamp?.receivedAtNanos
        if (leftObservation == null || rightObservation == null ||
            left == null || right == null || leftTime == null || rightTime == null ||
            abs(secondsBetween(now, leftTime)) > MAX_SAMPLE_GAP ||
            abs(secondsBetween(now, rightTime)) > MAX_SAMPLE_GAP || left.distanceTo(right) > 0.28 ||
            leftObservation.stamp.coordinateEpoch != rightObservation.stamp.coordinateEpoch ||
            leftObservation.stamp.coordinateEpoch != snapshot.head?.stamp?.coordinateEpoch ||
            leftObservation.stamp.sequence < snapshot.requiredSinceSequence ||
            rightObservation.stamp.sequence < snapshot.requiredSinceSequence) {
            clearCharge()
            skillLatched = false
            return false
        }
        val offset = (left + right) * 0.5 - head
        val forward = horizontal(enemy - head).normalizedOrNull() ?: return false
        val previousOffset = previousHandsOffset
        val previousTime = previousHandsAt
        val pairElapsed = previousTime?.let { secondsBetween(now, it) } ?: 0.0
        val forwardSpeed = if (previousOffset != null && pairElapsed > 0.0) {
            (offset - previousOffset).dot(forward) / pairElapsed
        } else {
            0.0
        }
        previousHandsOffset = offset
        previousHandsAt = now
        val origin = chargeOrigin
        val heading = chargeForward
        if (origin != null && heading != null) {
            val extension = (offset - origin).dot(heading)
            if (skillLatched && extension < 0.08) {
                clearCharge()
                skillLatched = false
            } else if (!skillLatched && extension >= SKILL_THRUST && forwardSpeed >= 0.6 &&
                elapsedSince(now, lastSkillAt) >= SKILL_COOLDOWN) {
                skillLatched = true
                lastSkillAt = now
                return true
            }
            return false
        }
        val chestPose = offset.y in -0.65..0.1 && offset.dot(forward) in 0.1..0.65
        if (!chestPose) {
            chargeStartedAt = null
            return false
        }
        if (chargeStartedAt == null) chargeStartedAt = now
        if (elapsedSince(now, chargeStartedAt) >= SKILL_CHARGE) {
            chargeOrigin = offset
            chargeForward = forward
        }
        return false
    }

    private fun clearCharge() {
        chargeStartedAt = null
        chargeOrigin = null
        chargeForward = null
        previousHandsOffset = null
        previousHandsAt = null
    }

    private fun contactZone(current: BladeSample, old: BladeSample?, enemy: Vector3): HitZone? {
        val head = enemy + Vector3(0.0, 1.62, 0.0)
        val bottom = enemy + Vector3(0.0, 0.55, 0.0)
        val top = enemy + Vector3(0.0, 1.40, 0.0)
        val origin = old ?: current
        val travel = maxOf(origin.base.distanceTo(current.base), origin.tip.distanceTo(current.tip))
        val steps = ceil(maxOf(travel / 0.06, rotationDistance(origin.rotation, current.rotation) / 0.10))
            .toInt().coerceIn(1, 160)
        val oldHand = origin.base - checkNotNull(origin.rotation.rotate(BLADE_BASE))
        val currentHand = current.base - checkNotNull(current.rotation.rotate(BLADE_BASE))
        var bodyContact = false
        // Reconstruct intermediate rigid blades so the rotating blade's middle also sweeps the target.
        for (index in 0..steps) {
            val fraction = index.toDouble() / steps
            val rotation = interpolateRotation(origin.rotation, current.rotation, fraction)
            val hand = oldHand + (currentHand - oldHand) * fraction
            val base = hand + checkNotNull(rotation.rotate(BLADE_BASE))
            val tip = hand + checkNotNull(rotation.rotate(BLADE_TIP))
            if (segmentDistance(base, tip, head, head) <= HEAD_RADIUS + BLADE_RADIUS) return HitZone.HEAD
            if (!bodyContact && segmentDistance(base, tip, bottom, top) <= BODY_RADIUS + BLADE_RADIUS) {
                bodyContact = true
            }
        }
        return if (bodyContact) HitZone.BODY else null
    }

    private fun interpolateRotation(from: Quaternion, to: Quaternion, fraction: Double): Quaternion {
        val dot = from.x * to.x + from.y * to.y + from.z * to.z + from.w * to.w
        val sign = if (dot < 0.0) -1.0 else 1.0
        val angle = acos(abs(dot).coerceIn(0.0, 1.0))
        val denominator = sin(angle)
        val fromWeight = if (denominator < 1e-6) 1.0 - fraction else sin((1.0 - fraction) * angle) / denominator
        val toWeight = if (denominator < 1e-6) fraction else sin(fraction * angle) / denominator
        return checkNotNull(Quaternion(
            from.x * fromWeight + to.x * toWeight * sign,
            from.y * fromWeight + to.y * toWeight * sign,
            from.z * fromWeight + to.z * toWeight * sign,
            from.w * fromWeight + to.w * toWeight * sign,
        ).normalizedOrNull())
    }

    private fun PoseObservation.positionOrNull(): Vector3? =
        pose?.takeIf { it.quality != TrackingQuality.SOURCE_REPORTED_INVALID }?.position?.takeIf { it.isFinite() }

    private fun rotationDistance(a: Quaternion, b: Quaternion): Double =
        2.0 * acos(abs(a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w).coerceIn(0.0, 1.0))

    private fun horizontal(vector: Vector3) = Vector3(vector.x, 0.0, vector.z)

    private fun secondsBetween(newer: Long, older: Long): Double =
        (newer.toDouble() - older.toDouble()) / 1_000_000_000.0

    private fun elapsedSince(now: Long, timestamp: Long?): Double =
        timestamp?.let { secondsBetween(now, it).coerceAtLeast(0.0) } ?: Double.POSITIVE_INFINITY

    private fun closestPoint(point: Vector3, start: Vector3, end: Vector3): Vector3 {
        val segment = end - start
        val lengthSquared = segment.dot(segment)
        if (!lengthSquared.isFinite() || lengthSquared <= GEOMETRY_EPSILON) return start
        val fraction = ((point - start).dot(segment) / lengthSquared).coerceIn(0.0, 1.0)
        return start + segment * fraction
    }

    /** Closest distance between finite segments, including point and parallel cases. */
    private fun segmentDistance(a0: Vector3, a1: Vector3, b0: Vector3, b1: Vector3): Double {
        val a = a1 - a0
        val b = b1 - b0
        val offset = a0 - b0
        val aa = a.dot(a)
        val bb = b.dot(b)
        val ab = a.dot(b)
        val ao = a.dot(offset)
        val bo = b.dot(offset)
        if (!listOf(aa, bb, ab, ao, bo).all { it.isFinite() }) return Double.POSITIVE_INFINITY
        if (aa <= GEOMETRY_EPSILON && bb <= GEOMETRY_EPSILON) return a0.distanceTo(b0)
        if (aa <= GEOMETRY_EPSILON) return a0.distanceTo(closestPoint(a0, b0, b1))
        if (bb <= GEOMETRY_EPSILON) return b0.distanceTo(closestPoint(b0, a0, a1))
        val denominator = aa * bb - ab * ab
        var alongA = if (denominator > GEOMETRY_EPSILON) {
            ((ab * bo - ao * bb) / denominator).coerceIn(0.0, 1.0)
        } else {
            0.0
        }
        var alongB = (ab * alongA + bo) / bb
        if (alongB < 0.0) {
            alongB = 0.0
            alongA = (-ao / aa).coerceIn(0.0, 1.0)
        } else if (alongB > 1.0) {
            alongB = 1.0
            alongA = ((ab - ao) / aa).coerceIn(0.0, 1.0)
        }
        return ((a0 + a * alongA) - (b0 + b * alongB)).length().takeIf { it.isFinite() }
            ?: Double.POSITIVE_INFINITY
    }

    private companion object {
        val BLADE_BASE = Vector3(0.022, 0.0, -0.129)
        val BLADE_TIP = Vector3(0.0532, 0.0, -0.849)
        val UP = Vector3(0.0, 1.0, 0.0)
        const val MAX_SAMPLE_GAP = 0.25
        const val MAX_ROTATION_STEP = 1.25
        const val MAX_PLAUSIBLE_TIP_SPEED = 35.0
        const val MIN_STRIKE_SPEED = 0.85
        const val MIN_STRIKE_TRAVEL = 0.12
        const val MIN_STRIKE_DISPLACEMENT = 0.10
        const val STRIKE_COOLDOWN = 0.28
        const val REST_SPEED = 0.30
        const val REST_RELEASE = 0.12
        const val OUTSIDE_RELEASE = 0.08
        const val BODY_RADIUS = 0.24
        const val HEAD_RADIUS = 0.16
        const val BLADE_RADIUS = 0.012
        const val ENEMY_REACH = 1.60
        const val DODGE_TRAVEL = 0.30
        const val DUCK_TRAVEL = 0.25
        const val MIN_PARRY_SPEED = 0.90
        const val PARRY_WINDOW = 0.18
        const val SKILL_CHARGE = 0.40
        const val SKILL_THRUST = 0.25
        const val SKILL_COOLDOWN = 1.0
        const val GEOMETRY_EPSILON = 1e-12
    }
}
