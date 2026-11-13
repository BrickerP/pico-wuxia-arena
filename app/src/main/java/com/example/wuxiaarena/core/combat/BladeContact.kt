package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import kotlin.math.abs

/** A capsule axis and its radius, in stage metres. A zero-length axis is a sphere. */
data class BladeSegment(val base: Vector3, val tip: Vector3, val radiusMeters: Double) {
    init {
        require(base.isFinite() && tip.isFinite()) { "Blade endpoints must be finite" }
        require(radiusMeters.isFinite() && radiusMeters >= 0.0) { "Blade radius must be finite and nonnegative" }
    }
}

/** Endpoints and radius move linearly over fraction 0..1. Rotation arcs require caller subdivision. */
data class BladeSweep(val previous: BladeSegment, val current: BladeSegment)

data class BladeContact(
    val fraction: Double,
    val playerPoint: Vector3,
    val enemyPoint: Vector3,
    /** Unit direction from the enemy axis toward the player axis. */
    val normal: Vector3,
    /** Material-point displacement over the whole sweep, player minus enemy; not metres/second. */
    val relativeDisplacement: Vector3,
    val playerAxisFraction: Double,
    val enemyAxisFraction: Double,
    /** Signed axis distance minus the interpolated radius sum. Initial penetration can be negative. */
    val separationMeters: Double,
    /** Maximum positive separation accepted by this spatially conservative query. */
    val errorBoundMeters: Double,
)

/** A bounded query could not prove either contact or separation; callers must not treat this as a miss. */
class BladeContactUncertainException(val earliestUnresolvedFraction: Double, message: String) : IllegalStateException(message)

/**
 * Earliest conservative capsule contact for two linearly moving segments.
 *
 * The distance function is Lipschitz with the maximum of the four relative endpoint
 * displacements. Intervals are visited in time order and discarded only with a distance
 * lower bound or a separating-plane certificate. The final interval spans at most 0.1 µm
 * of relative motion (plus roundoff); its start is returned. Consequently a real crossing
 * cannot tunnel between samples, but a near miss within [BladeContact.errorBoundMeters]
 * can report contact. This is a spatial bound, not a time-error bound at tangency.
 * Exceeding the distance-evaluation budget or floating-point resolution throws
 * [BladeContactUncertainException]; an unresolved interval never becomes a miss.
 */
fun firstBladeContact(playerSweep: BladeSweep, enemySweep: BladeSweep): BladeContact? {
    val playerBaseDelta = playerSweep.current.base - playerSweep.previous.base
    val playerTipDelta = playerSweep.current.tip - playerSweep.previous.tip
    val enemyBaseDelta = enemySweep.current.base - enemySweep.previous.base
    val enemyTipDelta = enemySweep.current.tip - enemySweep.previous.tip
    val relativeDeltas = listOf(
        playerBaseDelta - enemyBaseDelta, playerBaseDelta - enemyTipDelta,
        playerTipDelta - enemyBaseDelta, playerTipDelta - enemyTipDelta,
    )
    val radiusDelta = (playerSweep.current.radiusMeters - playerSweep.previous.radiusMeters) +
        (enemySweep.current.radiusMeters - enemySweep.previous.radiusMeters)
    val lipschitz = relativeDeltas.maxOf { it.length() } + abs(radiusDelta)
    require(lipschitz.isFinite()) { "Blade relative motion exceeds finite geometry range" }
    val endpoints = listOf(playerSweep.previous, playerSweep.current, enemySweep.previous, enemySweep.current)
    val coordinateScale = endpoints.maxOf { maxOf(
        abs(it.base.x), abs(it.base.y), abs(it.base.z),
        abs(it.tip.x), abs(it.tip.y), abs(it.tip.z), it.radiusMeters, 1.0,
    ) }
    val roundoff = 64.0 * Math.ulp(coordinateScale)
    val spatialError = maxOf(CONTACT_SPATIAL_ERROR_METERS, roundoff)
    val errorBound = spatialError + 3.0 * roundoff
    var evaluations = 0
    var earliestUnresolvedFraction = 0.0

    fun sample(fraction: Double): BladeSample {
        if (evaluations++ >= MAX_DISTANCE_EVALUATIONS) {
            throw BladeContactUncertainException(earliestUnresolvedFraction, "Blade contact distance-evaluation budget exhausted")
        }
        val player = playerSweep.at(fraction)
        val enemy = enemySweep.at(fraction)
        val (playerAxis, enemyAxis) = requireNotNull(
            closestSegmentPoints(player.base, player.tip, enemy.base, enemy.tip),
        ) { "Blade geometry exceeds finite distance range" }
        val distance = playerAxis.distanceTo(enemyAxis)
        val gap = distance - player.radiusMeters - enemy.radiusMeters
        require(gap.isFinite()) { "Blade separation exceeds finite geometry range" }
        return BladeSample(fraction, player, enemy, playerAxis, enemyAxis, gap)
    }

    fun contact(sample: BladeSample): BladeContact {
        val alongPlayer = axisFraction(sample.playerAxis, sample.player)
        val alongEnemy = axisFraction(sample.enemyAxis, sample.enemy)
        val relative = lerp(playerBaseDelta, playerTipDelta, alongPlayer) -
            lerp(enemyBaseDelta, enemyTipDelta, alongEnemy)
        val normal = (sample.playerAxis - sample.enemyAxis).normalizedOrNull()
            ?: perpendicular(sample.player.tip - sample.player.base, sample.enemy.tip - sample.enemy.base, relative)
        if (sample.gap > errorBound) {
            throw BladeContactUncertainException(sample.fraction, "Blade contact exceeds its spatial uncertainty bound")
        }
        return BladeContact(
            sample.fraction,
            sample.playerAxis - normal * sample.player.radiusMeters,
            sample.enemyAxis + normal * sample.enemy.radiusMeters,
            normal, relative, alongPlayer, alongEnemy, sample.gap, errorBound,
        )
    }

    val first = sample(0.0)
    if (first.gap <= roundoff) return contact(first)
    if (lipschitz == 0.0) return null
    val pending = ArrayDeque<BladeInterval>()
    pending.addLast(BladeInterval(first, sample(1.0)))
    while (pending.isNotEmpty()) {
        val (left, right) = pending.removeLast()
        earliestUnresolvedFraction = left.fraction
        val width = right.fraction - left.fraction
        val middleFraction = left.fraction + width * 0.5
        // At adjacent representable times, accepting the unresolved boundary preserves
        // contact instead of treating arithmetic exhaustion as proof of separation.
        if (middleFraction == left.fraction || middleFraction == right.fraction) {
            if (left.gap > errorBound) {
                throw BladeContactUncertainException(left.fraction, "Blade contact cannot be resolved at Double time precision")
            }
            return contact(left)
        }
        val middle = sample(middleFraction)
        if (middle.gap - lipschitz * width * 0.5 > roundoff) continue
        val separatingNormal = (middle.playerAxis - middle.enemyAxis).normalizedOrNull()
        if (separatingNormal != null && separatedThroughout(left, right, separatingNormal, roundoff)) continue
        if (lipschitz * width <= spatialError) return contact(left)
        // LIFO: visit the earlier half first, even when only a later sample overlaps.
        pending.addLast(BladeInterval(middle, right))
        pending.addLast(BladeInterval(left, middle))
    }
    return null
}

private data class BladeSample(
    val fraction: Double,
    val player: BladeSegment,
    val enemy: BladeSegment,
    val playerAxis: Vector3,
    val enemyAxis: Vector3,
    val gap: Double,
)

private data class BladeInterval(val left: BladeSample, val right: BladeSample)

private fun separatedThroughout(left: BladeSample, right: BladeSample, normal: Vector3, error: Double): Boolean {
    // At a fixed material-point pair, projection minus radius is linear in time.
    // Checking every endpoint pair at both interval ends certifies the whole interval.
    fun projectedGap(sample: BladeSample): Double {
        val radius = sample.player.radiusMeters + sample.enemy.radiusMeters
        return minOf(
            (sample.player.base - sample.enemy.base).dot(normal),
            (sample.player.base - sample.enemy.tip).dot(normal),
            (sample.player.tip - sample.enemy.base).dot(normal),
            (sample.player.tip - sample.enemy.tip).dot(normal),
        ) - radius
    }
    return projectedGap(left) > error && projectedGap(right) > error
}

private fun BladeSweep.at(fraction: Double) = BladeSegment(
    lerp(previous.base, current.base, fraction),
    lerp(previous.tip, current.tip, fraction),
    previous.radiusMeters * (1.0 - fraction) + current.radiusMeters * fraction,
)

private fun lerp(from: Vector3, to: Vector3, fraction: Double): Vector3 =
    from * (1.0 - fraction) + to * fraction

private fun axisFraction(point: Vector3, blade: BladeSegment): Double {
    val axis = blade.tip - blade.base
    val length = axis.length()
    if (length == 0.0) return 0.0
    return ((point - blade.base).dot(axis * (1.0 / length)) / length).coerceIn(0.0, 1.0)
}

private fun perpendicular(playerAxis: Vector3, enemyAxis: Vector3, relative: Vector3): Vector3 {
    val playerDirection = playerAxis.normalizedOrNull()
    val enemyDirection = enemyAxis.normalizedOrNull()
    if (playerDirection != null && enemyDirection != null) {
        playerDirection.cross(enemyDirection).normalizedOrNull()?.let {
            return if (it.dot(relative) > 0.0) it * -1.0 else it
        }
    }
    val axis = playerDirection ?: enemyDirection ?: return (relative * -1.0).normalizedOrNull() ?: Vector3(0.0, 1.0, 0.0)
    val perpendicularMotion = axis.cross(relative).cross(axis) * -1.0
    // Projecting exactly axial motion can leave roundoff; normalizing that residual
    // would incorrectly turn it into an axial surface normal.
    if (perpendicularMotion.length() > 64.0 * Math.ulp(relative.length())) {
        perpendicularMotion.normalizedOrNull()?.let { return it }
    }
    val reference = if (abs(axis.x) < abs(axis.y)) Vector3(1.0, 0.0, 0.0) else Vector3(0.0, 1.0, 0.0)
    return checkNotNull(axis.cross(reference).normalizedOrNull())
}

private const val CONTACT_SPATIAL_ERROR_METERS = 1e-7
private const val MAX_DISTANCE_EVALUATIONS = 16_384
