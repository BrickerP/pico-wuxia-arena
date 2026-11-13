package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

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
        assertTrue(contact.fraction > 0.5 && contact.fraction < 0.7)
        // The short base endpoint arrives first, 8 mm sideways from the enemy axis.
        assertEquals(-sqrt(8.0 / 9.0), contact.normal.z, 1e-5)
        assertEquals(2.0, contact.relativeDisplacement.z, 1e-10)
    }

    @Test
    fun bothBladeDirectionsParticipateInRelativeSweep() {
        val before = grip(-1.0)
        val after = grip(1.0)
        val enemy = BladeSweep(vertical(1.0), vertical(-1.0))
        val contact = requireNotNull(firstRigidBladeContact(before, after, enemy))
        assertTrue(contact.fraction > 0.5 && contact.fraction < 0.6)
        assertEquals(4.0, contact.relativeDisplacement.z, 1e-10)
    }

    @Test
    fun aRotationArcHitsWhenItsEndpointChordMisses() {
        val before = WeaponGrip(ZERO, IDENTITY)
        val after = WeaponGrip(ZERO, Quaternion(0.0, 1.0, 0.0, 0.0))
        val enemy = BladeSegment(Vector3(-0.8, -0.2, 0.0), Vector3(-0.8, 0.2, 0.0), 0.002)
        assertNull(firstBladeContact(BladeSweep(playerBlade(before), playerBlade(after)), BladeSweep(enemy, enemy)))
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
    fun contactStopsVirtualHandAndBladeWhileRawTargetKeepsMoving() {
        val constraint = WeaponContactConstraint()
        val before = grip(-1.0)
        val raw = grip(1.0)
        val enemy = vertical(0.0)
        val contact = requireNotNull(firstRigidBladeContact(before, raw, BladeSweep(enemy, enemy)))
        val atContact = interpolateGrip(before, raw, contact.fraction)
        constraint.lock(raw, atContact, contact.normal, contact.playerAxisFraction)

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
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0))
        assertTrue(constraint.releaseIfSeparated(vertical(-2.0)))
        assertSame(raw, constraint.apply(raw))
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0))
        constraint.reset()
        assertSame(raw, constraint.apply(raw))
        assertFalse(constraint.constrained)
    }

    @Test
    fun nearbyEnemyBladeDoesNotReleaseContactStop() {
        val constraint = WeaponContactConstraint()
        val held = grip(0.1)
        val blade = playerBlade(held)
        constraint.lock(grip(1.0), held, Vector3(0.0, 0.0, -1.0))
        assertFalse(constraint.releaseIfSeparated(blade))
        assertNotNull(constraint.apply(grip(1.1)))
        assertTrue(constraint.constrained)
    }

    @Test
    fun enemySeparationCannotReleaseThroughAnOccupiedRawCatchupPath() {
        val constraint = WeaponContactConstraint()
        val held = grip(-1.0)
        val raw = grip(1.0)
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0))
        assertFalse(constraint.releaseIfSeparated(vertical(0.0), rawGrip = raw))
        assertTrue(constraint.constrained)
    }

    private fun grip(z: Double) = WeaponGrip(Vector3(0.0, 0.0, z), IDENTITY)
    private fun vertical(z: Double) = BladeSegment(Vector3(0.03, -0.2, z), Vector3(0.03, 0.2, z), 0.012)

    private companion object {
        val ZERO = Vector3(0.0, 0.0, 0.0)
        val IDENTITY = Quaternion(0.0, 0.0, 0.0, 1.0)
    }
}
