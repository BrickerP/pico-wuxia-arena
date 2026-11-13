package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestPoint
import com.example.wuxiaarena.core.math.closestSegmentPoints
import kotlin.math.abs
import kotlin.math.acos

enum class HitZone { BODY, HEAD }

data class MotionContact(
    val zone: HitZone,
    val point: Vector3,
    val normal: Vector3,
    /** Unit Stage direction of the blade at the contact witness, before surface-plane projection. */
    val tangent: Vector3? = null,
)

data class EnemyContactPose(val head: Vector3, val bodyBottom: Vector3, val bodyTop: Vector3) {
    fun isFinite(): Boolean = head.isFinite() && bodyBottom.isFinite() && bodyTop.isFinite()
    fun translated(offset: Vector3) = EnemyContactPose(head + offset, bodyBottom + offset, bodyTop + offset)

    companion object {
        fun standing(origin: Vector3) = EnemyContactPose(
            origin + Vector3(0.0, 1.62, 0.0),
            origin + Vector3(0.0, 0.55, 0.0),
            origin + Vector3(0.0, 1.40, 0.0),
        )
    }
}

data class QualifiedSwing(val id: Long, val power: Double)

data class MotionStrike(val id: Long, val zone: HitZone, val power: Double, val contact: MotionContact)

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
    val releaseRequired: Boolean = false,
    val hand: Hand = Hand.RIGHT,
    val targetPose: EnemyContactPose? = null,
    val bladeAtRest: Boolean = true,
    val motionGeneration: Long = 0L,
    /** Endpoint displacements from this frame's accepted observation interval, in Stage metres. */
    val bladeBaseDelta: Vector3? = null,
    val bladeTipDelta: Vector3? = null,
    val rawWeaponGrip: WeaponGrip? = null,
    val weaponGrip: WeaponGrip? = null,
    val swing: QualifiedSwing? = null,
    val guardEnteredAtNanos: Long? = null,
    val fastGuardAtNanos: Long? = null,
    val observationSequence: Long = -1L,
)

/**
 * One-thread motion recognizer shared by device input and desktop pose rehearsal.
 * Its body capsules are gameplay hit volumes calibrated to the 1.78 m character.
 * They describe the trial's contact rules independently of the rendered skin.
 */
class PlayerCombatResolver {
    /** Changes whenever motion history is discarded or a new baseline is established. */
    var motionGeneration: Long = 0L
        private set

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

    private val weaponConstraint = WeaponContactConstraint()
    val weaponConstrained: Boolean get() = weaponConstraint.constrained
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
    private var qualifiedSwing: QualifiedSwing? = null
    private var currentGuard: AttackDirection? = null
    private var guardEnteredAt: Long? = null
    private var fastGuardAt: Long? = null
    private var attackId: Long? = null
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
    fun observe(
        snapshot: TrackingSnapshot,
        enemyPosition: Vector3,
        contactPose: EnemyContactPose = EnemyContactPose.standing(enemyPosition),
    ): PlayerMotionFrame? {
        if (!snapshot.hasRequiredObservations || !enemyPosition.isFinite() || !contactPose.isFinite()) return clearUnavailable()
        val head = snapshot.head ?: return clearUnavailable()
        val hand = (if (snapshot.dominantHand == Hand.LEFT) snapshot.left else snapshot.right)
            ?: return clearUnavailable()
        val headPosition = head.positionOrNull() ?: return clearUnavailable()
        val handPosition = hand.positionOrNull() ?: return clearUnavailable()
        val rawRotation = hand.pose?.rotation?.normalizedOrNull() ?: return clearUnavailable()
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
        val rawGrip = WeaponGrip(handPosition, rawRotation)
        val grip = weaponConstraint.apply(rawGrip)
        val rotation = grip.rotation
        val base = rotation.rotate(BLADE_BASE)?.plus(grip.position) ?: return clearUnavailable()
        val tip = rotation.rotate(BLADE_TIP)?.plus(grip.position) ?: return clearUnavailable()
        if (!base.isFinite() || !tip.isFinite() || base.distanceTo(tip) !in 0.70..0.74) {
            return clearUnavailable()
        }
        val sample = BladeSample(hand.stamp, base, tip, rotation)
        val old = previous
        if (old == null) return establish(sample, headPosition, enemyPosition, contactPose, rawGrip)
        if (sample.stamp.sequence == old.stamp.sequence) {
            val frame = latestFrame?.copy(headPosition = headPosition, strike = null, skillGesture = false, targetPose = contactPose)
            latestFrame = frame
            return frame
        }
        val elapsed = secondsBetween(sample.stamp.receivedAtNanos, old.stamp.receivedAtNanos)
        if (sample.stamp.sequence < old.stamp.sequence || elapsed <= 0.0 || elapsed > MAX_SAMPLE_GAP ||
            rotationDistance(old.rotation, rotation) > MAX_ROTATION_STEP) {
            reset()
            identity = currentIdentity
            lastHeadStamp = head.stamp
            return establish(sample, headPosition, enemyPosition, contactPose, rawGrip)
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
            return establish(sample, headPosition, enemyPosition, contactPose, rawGrip)
        }
        val contact = contactZone(sample, old, contactPose)
        val inside = contactZone(sample, null, contactPose) != null
        val direction = movement.normalizedOrNull()
        updateStroke(sample, speed, direction, inside)
        strokeTravel += distance
        val displacement = strokeOrigin?.let { maxOf(it.tip.distanceTo(tip), it.base.distanceTo(base)) } ?: 0.0
        if (qualifiedSwing == null && speed >= MIN_STRIKE_SPEED && strokeTravel >= MIN_STRIKE_TRAVEL &&
            displacement >= MIN_STRIKE_DISPLACEMENT &&
            elapsedSince(sample.stamp.receivedAtNanos, lastStrikeAt) >= STRIKE_COOLDOWN && nextStrikeId < Long.MAX_VALUE) {
            qualifiedSwing = QualifiedSwing(nextStrikeId++, (speed / 2.2).coerceIn(1.0, 1.4))
            lastStrikeAt = sample.stamp.receivedAtNanos
        }
        val swing = qualifiedSwing?.takeIf { speed >= MIN_STRIKE_SPEED }
            ?.copy(power = (speed / 2.2).coerceIn(1.0, 1.4))
        // Optional contact evidence is for input diagnostics and pose rehearsal. The
        // session consumes swing, whose admission is independent of this static body.
        val strike = if (!strokeHasHit && contact != null && swing != null) {
            strokeHasHit = true
            MotionStrike(swing.id, contact.zone, swing.power, contact)
        } else null
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
            if (channeling) null else strike, skill, headPosition, currentGuard, chargeProgress,
            releaseRequired = skillLatched, hand = snapshot.dominantHand, targetPose = contactPose,
            bladeAtRest = speed <= REST_SPEED, motionGeneration = motionGeneration,
            bladeBaseDelta = baseMovement.takeIf { speed > REST_SPEED },
            bladeTipDelta = tipMovement.takeIf { speed > REST_SPEED }, rawWeaponGrip = rawGrip, weaponGrip = grip,
            swing = if (channeling) null else swing, guardEnteredAtNanos = guardEnteredAt, fastGuardAtNanos = fastGuardAt, observationSequence = sample.stamp.sequence)
        latestFrame = frame
        return frame
    }

    fun beginEnemyAttack(attackId: Long) {
        if (this.attackId == attackId) return
        this.attackId = attackId
        resolvedAttackId = null
    }

    /** Surface witness on the same gameplay capsule used by the accepted action. */
    fun targetContact(frame: PlayerMotionFrame, enemyPosition: Vector3, zone: HitZone): MotionContact {
        val pose = frame.targetPose ?: EnemyContactPose.standing(enemyPosition)
        val start = if (zone == HitZone.HEAD) pose.head else pose.bodyBottom
        val end = if (zone == HitZone.HEAD) start else pose.bodyTop
        return surfaceContact(frame.bladeBase, frame.bladeTip, start, end,
            if (zone == HitZone.HEAD) HEAD_RADIUS else BODY_RADIUS, zone, frame.headPosition - enemyPosition,
            frame.bladeBaseDelta.takeUnless { frame.bladeAtRest }, frame.bladeTipDelta.takeUnless { frame.bladeAtRest })
    }

    /** Geometry is mandatory; guard timing only grades an actual steel witness. */
    fun resolveDefense(attackId: Long, direction: AttackDirection, enemyPosition: Vector3,
        receivedAtNanos: Long, contact: BladeContact? = null): AttackOutcome {
        if (contact == null || this.attackId != attackId || latestFrame == null) return AttackOutcome.MISSED
        if (resolvedAttackId == attackId) return resolvedOutcome
        val frame = checkNotNull(latestFrame)
        val aligned = frame.guardDirection == direction &&
            guardDirection(frame.bladeBase, frame.bladeTip, frame.headPosition, enemyPosition) == direction
        val result = if (aligned && frame.guardEnteredAtNanos?.let { it <= receivedAtNanos && elapsedSince(receivedAtNanos, it) <= PARRY_WINDOW } == true &&
            frame.fastGuardAtNanos?.let { it <= receivedAtNanos && elapsedSince(receivedAtNanos, it) <= PARRY_WINDOW } == true) AttackOutcome.PARRIED else AttackOutcome.BLOCKED
        resolvedAttackId = attackId
        resolvedOutcome = result
        return result
    }

    /** Keep tracking untouched; replace the simulation/render hand and blade together. */
    fun constrainWeapon(frame: PlayerMotionFrame, grip: WeaponGrip, contact: BladeContact): PlayerMotionFrame {
        val raw = frame.rawWeaponGrip ?: grip
        weaponConstraint.lock(raw, grip, contact.normal, contact.playerAxisFraction)
        val blade = playerBlade(grip)
        previous = previous?.copy(base = blade.base, tip = blade.tip, rotation = grip.rotation)
        strokeHasHit = true
        return frame.copy(bladeBase = blade.base, bladeTip = blade.tip, weaponGrip = grip,
            strike = null, swing = null, bladeBaseDelta = null, bladeTipDelta = null, bladeAtRest = true, bladeTipSpeed = 0.0)
            .also { latestFrame = it }
    }

    fun applyWeaponConstraint(frame: PlayerMotionFrame): PlayerMotionFrame {
        val raw = frame.rawWeaponGrip ?: return frame
        val grip = weaponConstraint.apply(raw)
        if (!weaponConstraint.constrained) return frame
        val blade = playerBlade(grip)
        return frame.copy(weaponGrip = grip, bladeBase = blade.base, bladeTip = blade.tip,
            strike = null, swing = null, skillGesture = false, bladeAtRest = true, bladeTipSpeed = 0.0,
            bladeBaseDelta = null, bladeTipDelta = null)
    }

    fun releaseWeaponIfSeparated(enemyBlade: BladeSegment) {
        weaponConstraint.releaseIfSeparated(enemyBlade, rawGrip = latestFrame?.rawWeaponGrip)
    }

    fun reset() {
        check(motionGeneration < Long.MAX_VALUE) { "motion generation overflow" }
        motionGeneration++
        weaponConstraint.reset()
        identity = null
        previous = null
        latestFrame = null
        lastHeadStamp = null
        strokeOrigin = null
        qualifiedSwing = null
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

    private fun establish(sample: BladeSample, head: Vector3, enemy: Vector3, contactPose: EnemyContactPose, rawGrip: WeaponGrip): PlayerMotionFrame {
        check(motionGeneration < Long.MAX_VALUE) { "motion generation overflow" }
        motionGeneration++
        previous = sample
        startStroke(sample)
        updateGuard(sample, head, enemy, 0.0, false)
        return PlayerMotionFrame(sample.stamp.receivedAtNanos, sample.base, sample.tip, 0.0, null, false, head, currentGuard,
            hand = checkNotNull(identity).hand, targetPose = contactPose,
            bladeAtRest = true, motionGeneration = motionGeneration, rawWeaponGrip = rawGrip,
            weaponGrip = WeaponGrip(sample.base - checkNotNull(sample.rotation.rotate(BLADE_BASE)), sample.rotation),
            guardEnteredAtNanos = guardEnteredAt, fastGuardAtNanos = fastGuardAt, observationSequence = sample.stamp.sequence)
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
        qualifiedSwing = null
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

    private fun contactZone(current: BladeSample, old: BladeSample?, pose: EnemyContactPose): MotionContact? {
        val origin = old ?: current
        fun grip(sample: BladeSample) = WeaponGrip(sample.base - checkNotNull(sample.rotation.rotate(BLADE_BASE)), sample.rotation)
        val previousGrip = grip(origin)
        val currentGrip = grip(current)
        fun contact(zone: HitZone, start: Vector3, end: Vector3, radius: Double): Pair<BladeContact, HitZone>? {
            val capsule = BladeSegment(start, end, radius)
            return firstRigidBladeContact(previousGrip, currentGrip, BladeSweep(capsule, capsule))?.let { it to zone }
        }
        val first = listOfNotNull(contact(HitZone.HEAD, pose.head, pose.head, HEAD_RADIUS),
            contact(HitZone.BODY, pose.bodyBottom, pose.bodyTop, BODY_RADIUS)).minByOrNull { it.first.fraction }
            ?: return null
        val witness = first.first
        return MotionContact(first.second, witness.enemyPoint, witness.normal,
            witness.relativeDisplacement.normalizedOrNull())
    }

    private fun surfaceContact(
        base: Vector3, tip: Vector3, start: Vector3, end: Vector3,
        radius: Double, zone: HitZone, fallback: Vector3,
        baseDelta: Vector3? = null, tipDelta: Vector3? = null,
    ): MotionContact {
        val (bladePoint, axisPoint) = checkNotNull(closestSegmentPoints(base, tip, start, end))
        val normal = (bladePoint - axisPoint).normalizedOrNull() ?: fallback.normalizedOrNull() ?: UP
        return MotionContact(zone, axisPoint + normal * radius, normal,
            bladeTangent(bladePoint, base, tip, baseDelta, tipDelta))
    }

    private fun bladeTangent(
        point: Vector3, base: Vector3, tip: Vector3, baseDelta: Vector3?, tipDelta: Vector3?,
    ): Vector3? {
        if (baseDelta == null || tipDelta == null || !baseDelta.isFinite() || !tipDelta.isFinite()) return null
        val axis = tip - base
        val lengthSquared = axis.dot(axis)
        if (!lengthSquared.isFinite() || lengthSquared <= GEOMETRY_EPSILON) return null
        val along = ((point - base).dot(axis) / lengthSquared).coerceIn(0.0, 1.0)
        val displacement = baseDelta + (tipDelta - baseDelta) * along
        if (displacement.dot(displacement) <= GEOMETRY_EPSILON) return null
        return displacement.normalizedOrNull()
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
        const val MIN_PARRY_SPEED = 0.90
        const val PARRY_WINDOW = 0.18
        const val SKILL_CHARGE = 0.40
        const val SKILL_THRUST = 0.25
        const val SKILL_COOLDOWN = 1.0
        const val GEOMETRY_EPSILON = 1e-12
    }
}
