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
        val enemy = enemy(0.0)
        val contact = requireNotNull(firstBladeShapeContact(sweep(before,after),enemy)?.contact)
        assertTrue(contact.fraction > 0.5 && contact.fraction < 0.7)
        // The short base endpoint arrives first, 8 mm sideways from the enemy axis.
        assertTrue(contact.normal.z < -.9)
        assertEquals(1.0,contact.normal.length(),1e-9)
        assertEquals(2.0, contact.relativeDisplacement.z, 1e-10)
    }

    @Test
    fun bothBladeDirectionsParticipateInRelativeSweep() {
        val before = grip(-1.0)
        val after = grip(1.0)
        val enemy = enemy(1.0).copy(current=enemy(-1.0).current)
        val contact = requireNotNull(firstBladeShapeContact(sweep(before,after),enemy)?.contact)
        assertTrue(contact.fraction > 0.5 && contact.fraction < 0.6)
        assertEquals(4.0, contact.relativeDisplacement.z, 1e-10)
    }

    @Test
    fun aRotationArcHitsWhenItsEndpointChordMisses() {
        val before = WeaponGrip(ZERO, IDENTITY)
        val after = WeaponGrip(ZERO, Quaternion(0.0, 1.0, 0.0, 0.0))
        val enemy = enemy(0.0).let { it.copy(previous=it.previous.copy(position=it.previous.position+Vector3(-.8,0.0,0.0)),current=it.current.copy(position=it.current.position+Vector3(-.8,0.0,0.0))) }
        assertTrue(DaoBladeShape.shape.at(before).zip(DaoBladeShape.shape.at(after)).all { (a,b)->DaoBladeShape.shape.at(enemy.previous).all {e->firstBladeContact(BladeSweep(a,b),BladeSweep(e,e))==null} })
        val contact = requireNotNull(firstBladeShapeContact(sweep(before,after),enemy)?.contact)
        assertTrue(contact.fraction in 0.4..0.6)
        assertTrue(contact.errorBoundMeters <= 0.000501)
        assertTrue(contact.separationMeters <= contact.errorBoundMeters)
    }

    @Test
    fun geometricallySeparatedBladesDoNotGenerateContact() {
        val enemy=enemy(0.0).let {it.copy(previous=it.previous.copy(position=it.previous.position+Vector3(2.0,0.0,0.0)),current=it.current.copy(position=it.current.position+Vector3(2.0,0.0,0.0)))}
        assertNull(firstBladeShapeContact(sweep(grip(-1.0),grip(1.0)),enemy))
    }

    @Test
    fun contactStopsVirtualHandAndBladeWhileRawTargetKeepsMoving() {
        val constraint = WeaponContactConstraint()
        val before = grip(-1.0)
        val raw = grip(1.0)
        val enemy = enemy(0.0)
        val contact = requireNotNull(firstBladeShapeContact(sweep(before,raw),enemy)?.contact)
        val atContact = interpolateGrip(before, raw, contact.fraction)
        constraint.lock(raw,atContact,contact.normal)

        val fartherRaw = grip(2.0)
        val virtual = constraint.apply(fartherRaw)
        assertEquals(atContact, virtual)
        assertEquals(playerBlade(atContact), playerBlade(virtual))
        assertEquals(2.0, fartherRaw.position.z, 0.0)
        assertTrue(constraint.constrained)

        val withdrawn = grip(-0.25)
        assertTrue(constraint.releaseIfSeparated(enemy,rawGrip=withdrawn))
        assertSame(withdrawn,constraint.apply(withdrawn))
        assertFalse(constraint.constrained)
    }

    @Test
    fun enemyWithdrawalReleasesConstraintAndResetClearsTrackingHistory() {
        val constraint = WeaponContactConstraint()
        val raw = grip(1.0)
        val held = grip(0.1)
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0))
        assertTrue(constraint.releaseIfSeparated(enemy(-2.0),rawGrip=raw))
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
        assertFalse(constraint.releaseIfSeparated(sweep(held,held),rawGrip=grip(1.1)))
        assertNotNull(constraint.apply(grip(1.1)))
        assertTrue(constraint.constrained)
    }

    @Test
    fun enemySeparationCannotReleaseThroughAnOccupiedRawCatchupPath() {
        val constraint = WeaponContactConstraint()
        val held = grip(-1.0)
        val raw = grip(1.0)
        constraint.lock(raw, held, Vector3(0.0, 0.0, -1.0))
        assertFalse(constraint.releaseIfSeparated(enemy(0.0), rawGrip = raw))
        assertTrue(constraint.constrained)
    }

    private fun grip(z: Double) = WeaponGrip(Vector3(0.0, 0.0, z), IDENTITY)
    private fun sweep(a:WeaponGrip,b:WeaponGrip)=BladeShapeSweep(DaoBladeShape.shape,a,b,0.0)
    private fun enemy(z:Double):BladeShapeSweep {
        val g=WeaponGrip(Vector3(0.0,-.4,z),Quaternion(sqrt(.5),0.0,0.0,sqrt(.5)))
        return sweep(g,g)
    }

    private companion object {
        val ZERO = Vector3(0.0, 0.0, 0.0)
        val IDENTITY = Quaternion(0.0, 0.0, 0.0, 1.0)
    }
}
