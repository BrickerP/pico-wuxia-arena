package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

class WeaponContactConstraintTest {
    @Test
    fun noContactPreservesRawGripExactly() {
        val constraint = WeaponContactConstraint()
        val raw = grip(1.0)
        assertSame(raw, constraint.apply(raw))
        assertFalse(constraint.constrained)
    }

    @Test
    fun highSpeedRigidTranslationFindsSteelBetweenClearEndpoints() {
        val before = grip(-1.0)
        val after = grip(1.0)
        val enemy = vertical(0.0)
        val contact = requireNotNull(firstRigidBladeContact(before, after, BladeSweep(enemy, enemy)))
        assertTrue(contact.fraction > 0.0 && contact.fraction < 1.0)
        assertEarliestTranslatedContact(before, after, enemy, contact)
        assertEquals(1.0, contact.normal.length(), 1e-9)
        assertTrue(contact.normal.z < 0.0)
        assertEquals(2.0, contact.relativeDisplacement.z, 1e-10)
    }

    @Test
    fun bothBladeDirectionsParticipateInRelativeSweep() {
        val before = grip(-1.0)
        val after = grip(1.0)
        val enemy = BladeSweep(vertical(1.0), vertical(-1.0))
        val contact = requireNotNull(firstRigidBladeContact(before, after, enemy))
        assertTrue(contact.fraction > 0.0 && contact.fraction < 1.0)
        val prior = (contact.fraction - 1e-4).coerceAtLeast(0.0)
        val priorEnemy = vertical(1.0 - 2.0 * prior)
        assertTrue(gap(playerBlade(interpolateGrip(before, after, prior)), priorEnemy) > contact.errorBoundMeters)
        assertEquals(4.0, contact.relativeDisplacement.z, 1e-10)
    }

    @Test
    fun aRotationArcHitsWhenItsEndpointChordMisses() {
        val before = WeaponGrip(ZERO, IDENTITY)
        val after = WeaponGrip(ZERO, Quaternion(0.0, 1.0, 0.0, 0.0))
        val enemy = BladeSegment(Vector3(-0.8, -0.2, 0.0), Vector3(-0.8, 0.2, 0.0), 0.002)
        for ((a, b) in playerBlade(before).zip(playerBlade(after))) {
            assertNull(firstBladeContact(BladeSweep(a, b), BladeSweep(enemy, enemy)))
        }
        val contact = requireNotNull(firstRigidBladeContact(before, after, BladeSweep(enemy, enemy)))
        assertTrue(contact.fraction in 0.4..0.6)
        assertTrue(contact.errorBoundMeters <= 0.000501)
        assertTrue(contact.separationMeters <= contact.errorBoundMeters)
    }

    @Test
    fun geometricallySeparatedBladesDoNotGenerateContact() {
        val enemy = vertical(0.0).copy(base = Vector3(2.0, -0.2, 0.0), tip = Vector3(2.0, 0.2, 0.0))
        assertNull(firstRigidBladeContact(grip(-1.0), grip(1.0), BladeSweep(enemy, enemy)))
    }

    @Test
    fun earliestContactComesFromTheRightLaneRatherThanTheFirstListedTouchingLane() {
        val from = WeaponGrip(Vector3(-0.2, 0.0, 0.0), IDENTITY)
        val to = WeaponGrip(Vector3(0.2, 0.0, 0.0), IDENTITY)
        val enemy = BladeSegment(Vector3(0.0, -0.2, -0.75), Vector3(0.0, 0.2, -0.75), 0.002)
        val local = playerBlade(WeaponGrip(ZERO, IDENTITY))
        assertEquals(7, local.size)
        assertEquals(0.052, local.last().base.x, 2e-9)
        assertTrue(-0.75 in local.last().tip.z..local.last().base.z)
        // The last lane's axis starts at -.2 + .052 = -.148 m. It reaches
        // the radius-sum plane x=-.008 after .140/.400 = .350 of the sweep.
        val contact = requireNotNull(firstRigidBladeContact(from, to, BladeSweep(enemy, enemy)))
        assertEquals(0.350, contact.fraction, 3e-7)
        assertTrue(gap(playerBlade(interpolateGrip(from, to, contact.fraction)), enemy) <= contact.errorBoundMeters)
        // Lane 2 is the first listed span reaching z=-.75. An implementation
        // returning that first hit would report about .465, demonstrably late.
        val listed = requireNotNull(firstBladeContact(
            BladeSweep(playerBlade(from)[2], playerBlade(to)[2]), BladeSweep(enemy, enemy)))
        assertTrue(listed.fraction > 0.46)
        assertTrue(contact.fraction < listed.fraction - 0.1)
    }

    @Test
    fun contactStopsVirtualHandAndBladeWhileRawTargetKeepsMoving() {
        val constraint = WeaponContactConstraint()
        val before = grip(-1.0)
        val raw = grip(1.0)
        val enemy = vertical(0.0)
        val contact = requireNotNull(firstRigidBladeContact(before, raw, BladeSweep(enemy, enemy)))
        val atContact = interpolateGrip(before, raw, contact.fraction)
        constraint.lock(raw, atContact, contact.normal, contact.playerPoint)

        val fartherRaw = grip(2.0)
        val virtual = constraint.apply(fartherRaw)
        assertEquals(atContact, virtual)
        assertEquals(playerBlade(atContact), playerBlade(virtual))
        assertEquals(2.0, fartherRaw.position.z, 0.0)
        assertTrue(constraint.constrained)

        val withdrawn = grip(-0.25)
        assertSame(withdrawn, constraint.apply(withdrawn))
        assertFalse(constraint.constrained)
    }

    @Test
    fun enemyWithdrawalReleasesConstraintAndResetClearsTrackingHistory() {
        val constraint = WeaponContactConstraint()
        val raw = grip(1.0)
        val held = grip(0.1)
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0), playerBlade(held).last().tip)
        assertTrue(constraint.releaseIfSeparated(vertical(-2.0)))
        assertSame(raw, constraint.apply(raw))
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0), playerBlade(held).last().tip)
        constraint.reset()
        assertSame(raw, constraint.apply(raw))
        assertFalse(constraint.constrained)
    }

    @Test
    fun nearbyEnemyBladeDoesNotReleaseContactStop() {
        val constraint = WeaponContactConstraint()
        val held = grip(0.1)
        val blade = playerBlade(held).last()
        constraint.lock(grip(1.0), held, Vector3(0.0, 0.0, -1.0), blade.tip)
        assertFalse(constraint.releaseIfSeparated(blade))
        assertNotNull(constraint.apply(grip(1.1)))
        assertTrue(constraint.constrained)
    }

    @Test
    fun enemySeparationCannotReleaseThroughAnOccupiedRawCatchupPath() {
        val constraint = WeaponContactConstraint()
        val held = grip(-1.0)
        val raw = grip(1.0)
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0), playerBlade(held).last().tip)
        assertFalse(constraint.releaseIfSeparated(vertical(0.0), rawGrip = raw))
        assertTrue(constraint.constrained)
    }

    @Test
    fun aLateralSteelLaneCannotReleaseJustBecauseTheOldCenterAxisIsClear() {
        val held = grip(0.0)
        val chain = playerBlade(held)
        val reference = playerBladeAxis(held)
        fun referenceDistance(point: Vector3): Double = requireNotNull(
            closestSegmentPoints(reference.base, reference.tip, point, point),
        ).let { it.first.distanceTo(it.second) }
        val edge = chain.flatMap { listOf(it.base, it.tip) }.maxByOrNull(::referenceDistance)!!
        val enemy = BladeSegment(edge, edge, 0.001)
        // This is the old proxy's separation criterion, used only as a negative
        // control. Actual locking/release receives the entire rendered dao chain.
        assertTrue(referenceDistance(edge) - 0.012 - enemy.radiusMeters > 0.025)
        assertTrue(gap(chain, enemy) < 0.0)
        val constraint = WeaponContactConstraint()
        constraint.lock(held, held, Vector3(0.0, 1.0, 0.0), edge)
        assertFalse(constraint.releaseIfSeparated(enemy))
        assertTrue(constraint.constrained)
        assertEquals(held, constraint.apply(held))
    }

    @Test
    fun theWideSteelFaceParticipatesInStaticContact() {
        val held = grip(0.0)
        val reference = playerBladeAxis(held)
        val edge = playerBlade(held).flatMap { listOf(it.base, it.tip) }.maxByOrNull { point ->
            val nearest = requireNotNull(closestSegmentPoints(reference.base, reference.tip, point, point))
            nearest.first.distanceTo(nearest.second)
        }!!
        val enemy = BladeSegment(edge, edge, 0.001)
        val contact = requireNotNull(firstRigidBladeContact(held, held, BladeSweep(enemy, enemy)))
        assertEquals(0.0, contact.fraction, 0.0)
        assertTrue(gap(playerBlade(held), enemy) <= 0.0)
        assertEquals(0.0, contact.relativeDisplacement.length(), 0.0)
    }

    private fun assertEarliestTranslatedContact(from: WeaponGrip, to: WeaponGrip, enemy: BladeSegment, contact: BladeContact) {
        val atContact = playerBlade(interpolateGrip(from, to, contact.fraction))
        assertTrue(gap(atContact, enemy) <= contact.errorBoundMeters)
        val before = (contact.fraction - 1e-4).coerceAtLeast(0.0)
        assertTrue("The whole chain is still clear immediately before its first witness",
            gap(playerBlade(interpolateGrip(from, to, before)), enemy) > contact.errorBoundMeters)
    }

    private fun gap(chain: List<BladeSegment>, enemy: BladeSegment): Double = chain.minOf { player ->
        val pair = requireNotNull(closestSegmentPoints(player.base, player.tip, enemy.base, enemy.tip))
        pair.first.distanceTo(pair.second) - player.radiusMeters - enemy.radiusMeters
    }

    private fun grip(z: Double) = WeaponGrip(Vector3(0.0, 0.0, z), IDENTITY)
    private fun vertical(z: Double) = BladeSegment(Vector3(0.03, -0.2, z), Vector3(0.03, 0.2, z), 0.012)

    private companion object {
        val ZERO = Vector3(0.0, 0.0, 0.0)
        val IDENTITY = Quaternion(0.0, 0.0, 0.0, 1.0)
    }
}
