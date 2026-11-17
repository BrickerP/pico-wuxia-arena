package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

class RotationExitInvariantTest {
    private val shape = DaoBladeShape.shape
    private val zero = Vector3(0.0, 0.0, 0.0)
    private val normal = Vector3(0.0, 1.0, 0.0)
    private val identity = WeaponGrip(zero, Quaternion(0.0, 0.0, 0.0, 1.0))

    @Test
    fun fixedGripYawHasExactSupportingPlaneInvariantDespiteInitialCcdContact() {
        val enemy = supportingContactEnemy()
        val initial = shape.at(identity)
        val enemyParts = shape.at(enemy.current)
        val plane = lowerSupport(initial)
        assertEquals(plane, upperSupport(enemyParts), 1e-17)
        assertEquals(0.0, minimumGap(identity, enemy.current), 1e-15)

        // A Y-axis rotation has exactly zero Y displacement for every authored endpoint.
        // The supporting plane therefore proves the entire continuous arc, not only samples.
        for (degrees in 0..90) {
            val current = shape.at(yaw(degrees.toDouble()))
            for (i in initial.indices) {
                assertEquals("base Y at part $i, yaw $degrees", initial[i].base.y, current[i].base.y, 0.0)
                assertEquals("tip Y at part $i, yaw $degrees", initial[i].tip.y, current[i].tip.y, 0.0)
                assertEquals(initial[i].radiusMeters, current[i].radiusMeters, 0.0)
            }
            assertEquals("whole-chain support at yaw $degrees", plane, lowerSupport(current), 0.0)
        }

        val raw = yaw(90.0)
        assertEquals(identity.position, raw.position)
        assertTrue("the complete target steel must clear 25 mm", minimumGap(raw, enemy.current) > .025)
        val path = sweep(identity, raw)
        val contact = requireNotNull(firstBladeShapeContact(path, enemy))
        assertEquals("initial tangency must remain CCD contact, never MISS", 0.0, contact.contact.fraction, 0.0)
        assertTrue("rotation about a constant supporting-plane normal cannot penetrate", separatingBladeShapePairs(path, enemy))
    }

    @Test
    fun actualRotationAtUnchangedGripNaturallyReleasesTheLockedHandAndDao() {
        val enemy = supportingContactEnemy()
        val raw = yaw(90.0)
        val constraint = locked(identity, normal)
        assertSame(identity, constraint.apply(raw))
        assertEquals(identity.position, raw.position)
        assertTrue(minimumGap(raw, enemy.current) > .025)

        assertTrue("the player can withdraw by wrist rotation without translating Grip", constraint.releaseForPlayerWithdrawal(enemy, raw))
        assertFalse(constraint.constrained)
        assertSame(raw, constraint.apply(raw))
        assertEquals(shape.at(raw), shape.at(constraint.apply(raw)))
    }

    @Test
    fun clearRotationEndpointsCannotHidePenetrationDuringTheFullArc() {
        val held = yaw(-90.0)
        val raw = yaw(90.0)
        val enemy = sweep(identity)
        assertEquals(held.position, raw.position)
        assertTrue(minimumGap(held, identity) > .025)
        assertTrue(minimumGap(raw, identity) > .025)
        val middle = interpolateGrip(held, raw, .5)
        assertTrue("the actual full chains overlap midway", minimumGap(middle, identity) < -.018)
        val path = sweep(held, raw)
        val contact = requireNotNull(firstBladeShapeContact(path, enemy))
        assertTrue(contact.contact.fraction > 0.0 && contact.contact.fraction < .5)
        assertFalse(separatingBladeShapePairs(path, enemy))

        val constraint = locked(held, normal)
        assertFalse(constraint.releaseForPlayerWithdrawal(enemy, raw))
        assertFalse(constraint.releaseIfSeparated(enemy, rawGrip = raw))
        assertTrue(constraint.constrained)
        assertSame(held, constraint.apply(raw))
    }

    @Test
    fun stationarySupportingContactDoesNotPrematurelyUnlockPressure() {
        val enemy = supportingContactEnemy()
        val constraint = locked(identity, normal)
        assertEquals(0.0, minimumGap(identity, enemy.current), 1e-15)
        assertFalse(constraint.releaseForPlayerWithdrawal(enemy, identity))
        assertFalse(constraint.releaseIfSeparated(enemy, rawGrip = identity))
        assertTrue(constraint.constrained)
        assertSame(identity, constraint.apply(identity))
    }

    @Test
    fun ordinaryCatchupKeeps25mmHysteresisButActiveClearTranslationCanExit() {
        val enemy = supportingContactEnemy()
        val raw = identity.copy(position = normal * .024)
        val constraint = locked(identity, normal)
        assertEquals(.024, minimumGap(raw, enemy.current), 1e-12)
        assertFalse(constraint.releaseIfSeparated(enemy, rawGrip = raw))
        assertTrue(constraint.constrained)
        assertTrue("A real player-driven clear route need not wait for enemy-withdrawal hysteresis",constraint.releaseForPlayerWithdrawal(enemy,raw))
        assertFalse(constraint.constrained)
        assertSame(raw,constraint.apply(raw))
    }

    @Test
    fun pureTranslationBeyond25mmStillReleasesInitialWholeChainContact() {
        val enemy = supportingContactEnemy()
        val raw = identity.copy(position = normal * .026)
        assertEquals(.026, minimumGap(raw, enemy.current), 1e-12)
        val path = sweep(identity, raw)
        assertEquals(0.0, requireNotNull(firstBladeShapeContact(path, enemy)).contact.fraction, 0.0)
        assertTrue(separatingBladeShapePairs(path, enemy))

        val constraint = locked(identity, normal)
        assertTrue(constraint.releaseForPlayerWithdrawal(enemy, raw))
        assertFalse(constraint.constrained)
        assertSame(raw, constraint.apply(raw))
    }

    @Test
    fun pureTranslationWithClearEndpointsStillRejectsAnOccupiedCatchupPath() {
        val held = identity.copy(position = Vector3(-.3, 0.0, 0.0))
        val raw = identity.copy(position = Vector3(.3, 0.0, 0.0))
        val enemy = sweep(identity)
        assertTrue(minimumGap(held, identity) > .025)
        assertTrue(minimumGap(raw, identity) > .025)
        assertTrue(minimumGap(interpolateGrip(held, raw, .5), identity) < -.018)
        val path = sweep(held, raw)
        val contact = requireNotNull(firstBladeShapeContact(path, enemy))
        assertTrue(contact.contact.fraction > 0.0 && contact.contact.fraction < .5)
        assertFalse(separatingBladeShapePairs(path, enemy))

        val constraint = locked(held, Vector3(1.0, 0.0, 0.0))
        assertFalse(constraint.releaseForPlayerWithdrawal(enemy, raw))
        assertFalse(constraint.releaseIfSeparated(enemy, rawGrip = raw))
        assertTrue(constraint.constrained)
        assertSame(held, constraint.apply(raw))
    }

    @Test
    fun enemyWithdrawalStillReleasesAWholeChainClearCatchupPath() {
        val enemyGrip = identity.copy(position = Vector3(0.0, -.5, 0.0))
        val enemy = sweep(enemyGrip)
        val raw = identity.copy(position = Vector3(.01, 0.0, 0.0))
        assertTrue(minimumGap(identity, enemyGrip) > .025)
        assertTrue(minimumGap(raw, enemyGrip) > .025)
        assertNull(firstBladeShapeContact(sweep(identity, raw), enemy))

        val constraint = locked(identity, normal)
        assertTrue(constraint.releaseIfSeparated(enemy, rawGrip = raw))
        assertFalse(constraint.constrained)
        assertSame(raw, constraint.apply(raw))
    }

    /** Tangency of two complete frozen dao envelopes, with a global supporting +Y plane. */
    private fun supportingContactEnemy(): BladeShapeSweep {
        assertEquals("1da878534abd84c464fe101d7326a03168186d275587863676343372ee723614", DaoBladeShape.DESCRIPTOR_SHA256)
        assertEquals(18, shape.parts.size)
        val lowerIndex = shape.parts.indices.minBy { lowerSupport(listOf(shape.parts[it])) }
        val upperIndex = shape.parts.indices.maxBy { upperSupport(listOf(shape.parts[it])) }
        assertEquals(4, lowerIndex)
        assertEquals(5, upperIndex)
        val player = shape.parts[lowerIndex]
        val enemy = shape.parts[upperIndex]
        val playerPoint = if (player.base.y <= player.tip.y) player.base else player.tip
        val enemyPoint = if (enemy.base.y >= enemy.tip.y) enemy.base else enemy.tip
        // Align actual support endpoints in X/Z as well, so this plane is real contact.
        val enemyGrip = identity.copy(position = Vector3(
            playerPoint.x - enemyPoint.x,
            lowerSupport(shape.parts) - upperSupport(shape.parts),
            playerPoint.z - enemyPoint.z,
        ))
        return sweep(enemyGrip)
    }

    private fun yaw(degrees: Double): WeaponGrip {
        val halfAngle = degrees * PI / 360.0
        return identity.copy(rotation = Quaternion(0.0, sin(halfAngle), 0.0, cos(halfAngle)))
    }

    private fun sweep(from: WeaponGrip, to: WeaponGrip = from) = BladeShapeSweep(shape, from, to, 0.0)

    private fun locked(held: WeaponGrip, contactNormal: Vector3) = WeaponContactConstraint().also {
        assertSame(held, it.lock(held, held, contactNormal))
    }

    private fun lowerSupport(parts: List<BladeSegment>) = parts.minOf {
        minOf(it.base.dot(normal), it.tip.dot(normal)) - it.radiusMeters
    }

    private fun upperSupport(parts: List<BladeSegment>) = parts.maxOf {
        maxOf(it.base.dot(normal), it.tip.dot(normal)) + it.radiusMeters
    }

    /** Minimum capsule surface gap across all 18 x 18 actual authored pairs. */
    private fun minimumGap(player: WeaponGrip, enemy: WeaponGrip): Double {
        val playerParts = shape.at(player)
        val enemyParts = shape.at(enemy)
        return playerParts.minOf { p ->
            enemyParts.minOf { e ->
                val pair = requireNotNull(closestSegmentPoints(p.base, p.tip, e.base, e.tip))
                pair.first.distanceTo(pair.second) - p.radiusMeters - e.radiusMeters
            }
        }
    }
}
