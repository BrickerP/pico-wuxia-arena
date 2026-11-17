package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.*
import com.example.wuxiaarena.core.math.Vector3

internal enum class EnemySourceJoinStatus { ADMITTED, WAITING_FOR_INPUT, CONTACT_BLOCKED, NEEDS_AUTHORED_TRANSITION }

internal data class EnemySourceJoinReceipt(
    val status: EnemySourceJoinStatus,
    val maximumSteelEndpointChangeMeters: Double,
    val sourceUncertaintyMeters: Double,
    val blockedContact: BladeContact?,
)

// Existing production pose budget, applied only to the displayed guard seam.
// It is never a collision tolerance or an addition to the source/FK envelope.
private const val MAX_GUARD_POSE_COMMIT_METERS = 0.002

internal fun sameEnemySourceInstant(from: EnemyPoseFrame, to: EnemyPoseFrame): Boolean =
    from.clip == to.clip && kotlin.math.abs(from.pose.sourceSeconds-to.pose.sourceSeconds) <= 1e-12

/** Authored common-guard endpoints; arbitrary mid-clip weapon coincidences do not qualify. */
internal fun canonicalGuardSource(frame: EnemyPoseFrame): Boolean {
    val time=frame.pose.sourceSeconds
    return when(frame.clip) {
        "idle","walk" -> time in 0.0..1.5
        "attack_overhead","attack_left","attack_right" -> time==0.0 || time==1.75
        "hit_body","hit_head" -> time==.05 || time==.72
        "hit_side" -> time==.05 || time==1.18
        else -> false
    }
}

internal fun canonicalGuardSourceBoundary(from: EnemyPoseFrame, to: EnemyPoseFrame): Boolean =
    canonicalGuardSource(from) && canonicalGuardSource(to)

internal fun boundedGuardPoseJoin(from: EnemyPoseFrame, to: EnemyPoseFrame, guardSamples: List<AttackPoseSample>): Boolean {
    if (!canonicalGuardSourceBoundary(from,to) || guardSamples.isEmpty()) return false
    val a = from.pose
    val b = to.pose
    if (a.bladeGrip.position.distanceTo(b.bladeGrip.position) > MAX_GUARD_POSE_COMMIT_METERS) return false
    fun anchors(p: AttackPoseSample) = listOf(p.contact.head, p.contact.bodyBottom, p.contact.bodyTop)
    val keys = guardSamples.map(::anchors)
    val endpoints = anchors(a) + anchors(b)
    for (i in 0..2) {
        val points = keys.map { it[i] }
        val low = Vector3(points.minOf { it.x },points.minOf { it.y },points.minOf { it.z })
        val high = Vector3(points.maxOf { it.x },points.maxOf { it.y },points.maxOf { it.z })
        for (point in listOf(endpoints[i],endpoints[i+3])) {
            if (point.x < low.x-1e-7 || point.x > high.x+1e-7 ||
                point.y < low.y-1e-7 || point.y > high.y+1e-7 ||
                point.z < low.z-1e-7 || point.z > high.z+1e-7) return false
        }
    }
    val start = DaoBladeShape.shape.at(a.bladeGrip)
    val end = DaoBladeShape.shape.at(b.bladeGrip)
    val qa = checkNotNull(a.bladeGrip.rotation.normalizedOrNull())
    val qb = checkNotNull(b.bladeGrip.rotation.normalizedOrNull())
    val dot = kotlin.math.abs(qa.x*qb.x + qa.y*qb.y + qa.z*qb.z + qa.w*qb.w).coerceIn(0.0,1.0)
    val radialChange = 2.0*kotlin.math.sqrt((1.0-dot*dot).coerceAtLeast(0.0))
    // A steel point lies in one certified capsule. Its endpoint displacement plus
    // radius*|R1-R0| bounds every point of that capsule, including its rounded support.
    return start.indices.all { i ->
        maxOf(start[i].base.distanceTo(end[i].base), start[i].tip.distanceTo(end[i].tip)) +
            start[i].radiusMeters*radialChange + a.bladeGripInterpolationErrorToNextMeters +
            b.bladeGripInterpolationErrorToNextMeters <= MAX_GUARD_POSE_COMMIT_METERS
    }
}

/**
 * Admit actual continuous source-boundary Grips within their offline uncertainty.
 * An arbitrary pose change requires a source-consistent route; a clear target alone
 * cannot certify it. The old on-screen clip/source remains authoritative on failure.
 * A certified canonical-guard seam may commit one bounded displayed pose within the existing 2mm
 * production Steel/Grip budget, with body anchors inside the actual guard key
 * envelope, still requiring the complete route's nonpenetration proof. This permits
 * the reviewed breathing pose to collect into an authored living-clip guard endpoint.
 * This does not synthesize a skeletal blend or claim to certify SDK blend semantics.
 */
internal fun admitEnemySourceJoin(
    from: EnemyPoseFrame,
    to: EnemyPoseFrame,
    player: WeaponGrip?,
    actorOrigin: Vector3,
    actorYaw: Float,
    guardSamples: List<AttackPoseSample>,
): EnemySourceJoinReceipt {
    val shape = DaoBladeShape.shape
    val start = shape.at(from.pose.bladeGrip)
    val end = shape.at(to.pose.bladeGrip)
    val change = start.indices.maxOf { i ->
        maxOf(start[i].base.distanceTo(end[i].base), start[i].tip.distanceTo(end[i].tip))
    }
    val uncertainty = from.pose.bladeGripInterpolationErrorToNextMeters +
        to.pose.bladeGripInterpolationErrorToNextMeters + 1e-7
    val guardBoundary = canonicalGuardSourceBoundary(from,to)
    if ((guardBoundary && !boundedGuardPoseJoin(from,to,guardSamples)) ||
        (!guardBoundary && !sameEnemySourceInstant(from,to))) return EnemySourceJoinReceipt(EnemySourceJoinStatus.NEEDS_AUTHORED_TRANSITION, change, uncertainty, null)
    if (player == null) return EnemySourceJoinReceipt(EnemySourceJoinStatus.WAITING_FOR_INPUT, change, uncertainty, null)
    val stageStart = from.pose.inStage(actorOrigin, actorYaw)
    val stageEnd = to.pose.inStage(actorOrigin, actorYaw)
    val playerSweep = BladeShapeSweep(shape, player, player, 0.0)
    val enemySweep = BladeShapeSweep(shape, stageStart.bladeGrip, stageEnd.bladeGrip,
        maxOf(from.pose.bladeGripInterpolationErrorToNextMeters, to.pose.bladeGripInterpolationErrorToNextMeters))
    val contact = firstBladeShapeContact(playerSweep, enemySweep)
    val allowed = contact == null || separatingBladeShapePairs(playerSweep, enemySweep, contact.contact.normal)
    return EnemySourceJoinReceipt(
        if (allowed) EnemySourceJoinStatus.ADMITTED else EnemySourceJoinStatus.CONTACT_BLOCKED, change, uncertainty,
        if(allowed)null else contact?.contact)
}
