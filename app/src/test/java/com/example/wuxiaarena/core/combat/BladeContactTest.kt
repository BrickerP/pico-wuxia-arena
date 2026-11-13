package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestPoint
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

class BladeContactTest {
    @Test
    fun highSpeedThinBladesCrossBetweenSeparatedFrameEndpoints() {
        val player = BladeSweep(horizontal(-2.0), horizontal(2.0))
        val enemy = stationary(vertical(0.0))

        val contact = requireNotNull(firstBladeContact(player, enemy))

        assertEquals((2.0 - 0.005) / 4.0, contact.fraction, 3e-8)
        assertTrue(contact.normal.z < -0.999999)
        assertEquals(4.0, contact.relativeDisplacement.z, 1e-12)
        assertEquals(0.5, contact.playerAxisFraction, 1e-9)
        assertEquals(0.5, contact.enemyAxisFraction, 1e-9)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun bothBladesMoveAndContactUsesRelativeMaterialDisplacement() {
        val player = BladeSweep(horizontal(-2.0), horizontal(2.0))
        val enemy = BladeSweep(vertical(2.0), vertical(-2.0))

        val contact = requireNotNull(firstBladeContact(player, enemy))

        assertEquals((4.0 - 0.005) / 8.0, contact.fraction, 2e-8)
        assertEquals(8.0, contact.relativeDisplacement.z, 1e-12)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun commonTranslationHasNoRelativeMotionAndCannotCreateContact() {
        val player = BladeSweep(horizontal(0.0), horizontal(0.0, x = 30.0))
        val enemy = BladeSweep(vertical(0.1), vertical(0.1, x = 30.0))
        assertNull(firstBladeContact(player, enemy))
    }

    @Test
    fun initialTouchAndRecedingMotionReturnFractionZero() {
        val player = BladeSweep(horizontal(-0.005), horizontal(-2.0))
        val enemy = stationary(vertical(0.0))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(0.0, contact.fraction, 0.0)
        assertEquals(0.0, contact.separationMeters, 1e-12)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun coincidentAxesWithAxialMotionStillReturnRealCapsuleSurfaceWitnesses() {
        val blade = BladeSegment(Vector3(-1.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), 0.01)
        val player = BladeSweep(blade, blade.copy(base = blade.base + Vector3(0.2, 0.0, 0.0), tip = blade.tip + Vector3(0.2, 0.0, 0.0)))
        val enemy = stationary(blade)

        val contact = requireNotNull(firstBladeContact(player, enemy))

        assertEquals(0.0, contact.fraction, 0.0)
        assertEquals(0.0, contact.normal.x, 1e-12)
        assertEquals(-0.02, contact.separationMeters, 1e-12)
        assertSurfaceWitnesses(contact, player, enemy)
    }

    @Test
    fun stationaryCoincidentPointsHaveFiniteDeterministicUnitNormal() {
        val player = stationary(point(Vector3(0.0, 0.0, 0.0), 0.01))
        val enemy = stationary(point(Vector3(0.0, 0.0, 0.0), 0.02))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(Vector3(0.0, 1.0, 0.0), contact.normal)
        assertSurfaceWitnesses(contact, player, enemy)
    }

    @Test
    fun degeneratePointCapsulesHaveAnalyticTimeOfImpact() {
        val player = BladeSweep(point(Vector3(-1.0, 0.0, 0.0), 0.01), point(Vector3(1.0, 0.0, 0.0), 0.01))
        val enemy = stationary(point(Vector3(0.0, 0.0, 0.0), 0.02))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(0.485, contact.fraction, 6e-8)
        assertEquals(0.0, contact.playerAxisFraction, 0.0)
        assertEquals(0.0, contact.enemyAxisFraction, 0.0)
        assertContactGeometry(contact, player, enemy)
    }

    @Test(timeout = 1000L)
    fun parallelAxialSlidingWithTinyPositiveGapIsProvenSeparated() {
        val blade = BladeSegment(Vector3(-1.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), 0.001)
        val delta = Vector3(1000.0, 0.0, 0.0)
        val player = BladeSweep(blade, blade.copy(base = blade.base + delta, tip = blade.tip + delta))
        val enemy = stationary(blade.copy(base = Vector3(-1.0, 0.0020002, 0.0), tip = Vector3(1.0, 0.0020002, 0.0)))
        assertNull(firstBladeContact(player, enemy))
    }

    @Test
    fun almostParallelBladesRetainInteriorClosestPoints() {
        val player = stationary(BladeSegment(Vector3(-0.5, 0.0, 0.0), Vector3(0.5, 0.0, 0.0), 0.01))
        val enemy = stationary(BladeSegment(Vector3(-0.5, -5e-11, 0.02), Vector3(0.5, 5e-11, 0.02), 0.01))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(0.5, contact.playerAxisFraction, 1e-7)
        assertEquals(0.5, contact.enemyAxisFraction, 1e-7)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun antiparallelSegmentsAndOnePointAxisHaveFiniteWitnesses() {
        val player = stationary(BladeSegment(Vector3(1.0, 0.0, 0.0), Vector3(-1.0, 0.0, 0.0), 0.01))
        val enemy = stationary(point(Vector3(0.2, 0.015, 0.0), 0.005))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(0.4, contact.playerAxisFraction, 1e-9)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun zeroRadiusSegmentsCanCrossWithoutSamplingTheExactInstant() {
        val player = BladeSweep(horizontal(-1.0).copy(radiusMeters = 0.0), horizontal(2.0).copy(radiusMeters = 0.0))
        val enemy = stationary(vertical(0.0).copy(radiusMeters = 0.0))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(1.0 / 3.0, contact.fraction, 5e-8)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun linearlyChangingRadiiParticipateInTheConservativeDistanceBound() {
        val origin = point(Vector3(0.0, 0.0, 0.0), 0.1)
        val player = BladeSweep(origin, origin.copy(radiusMeters = 1.0))
        val enemy = stationary(point(Vector3(1.0, 0.0, 0.0), 0.1))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(8.0 / 9.0, contact.fraction, 2e-7)
        assertContactGeometry(contact, player, enemy)
    }

    @Test
    fun invalidEndpointsAndRadiiAreRejectedExplicitly() {
        val zero = Vector3(0.0, 0.0, 0.0)
        listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY).forEach { invalid ->
            assertThrows(IllegalArgumentException::class.java) { BladeSegment(Vector3(invalid, 0.0, 0.0), zero, 0.0) }
            assertThrows(IllegalArgumentException::class.java) { BladeSegment(zero, Vector3(0.0, invalid, 0.0), 0.0) }
            assertThrows(IllegalArgumentException::class.java) { BladeSegment(zero, zero, invalid) }
        }
        assertThrows(IllegalArgumentException::class.java) { BladeSegment(zero, zero, -0.01) }
    }

    @Test
    fun coincidentDiagonalAxesDoNotNormalizeAxialProjectionRoundoff() {
        val blade = BladeSegment(Vector3(-1.0, -1.0, -1.0), Vector3(1.0, 1.0, 1.0), 0.01)
        val delta = Vector3(0.2, 0.2, 0.2)
        val player = BladeSweep(blade, blade.copy(base = blade.base + delta, tip = blade.tip + delta))
        val enemy = stationary(blade)
        val contact = requireNotNull(firstBladeContact(player, enemy))
        assertEquals(0.0, requireNotNull((blade.tip - blade.base).normalizedOrNull()).dot(contact.normal), 1e-9)
        assertSurfaceWitnesses(contact, player, enemy)
    }

    @Test
    fun endpointsWithDifferentVelocitiesSweepTheWholeSegment() {
        val player = BladeSweep(
            BladeSegment(Vector3(-1.0, -1.0, 0.0), Vector3(-1.0, 1.0, 0.0), 0.01),
            BladeSegment(Vector3(1.0, -1.0, 0.0), Vector3(-1.0, 1.0, 0.0), 0.01),
        )
        val enemy = stationary(point(Vector3(0.0, -0.5, 0.0), 0.01))
        val contact = requireNotNull(firstBladeContact(player, enemy))
        val expected = (12.0 - sqrt(144.0 - 4.0 * 8.9984 * 3.9984)) / (2.0 * 8.9984)
        assertEquals(expected, contact.fraction, 1e-7)
        assertEquals(2.0 * (1.0 - contact.playerAxisFraction), contact.relativeDisplacement.x, 1e-9)
        assertContactGeometry(contact, player, enemy)
    }

    @Test(timeout = 1000L)
    fun grazingTangencyIsResolvedWithinABoundedRuntime() {
        val player = BladeSweep(point(Vector3(-1.0, 0.03, 0.0), 0.01), point(Vector3(1.0, 0.03, 0.0), 0.01))
        val enemy = stationary(point(Vector3(0.0, 0.0, 0.0), 0.02))
        repeat(100) {
            val contact = requireNotNull(firstBladeContact(player, enemy))
            assertTrue(contact.fraction <= 0.5)
            assertTrue(contact.fraction > 0.499)
            assertContactGeometry(contact, player, enemy)
        }
    }

    private fun assertContactGeometry(contact: BladeContact, player: BladeSweep, enemy: BladeSweep) {
        assertTrue(contact.separationMeters <= contact.errorBoundMeters)
        assertTrue(contact.playerPoint.distanceTo(contact.enemyPoint) <= contact.errorBoundMeters + 1e-9)
        assertSurfaceWitnesses(contact, player, enemy)
    }

    private fun assertSurfaceWitnesses(contact: BladeContact, player: BladeSweep, enemy: BladeSweep) {
        assertTrue(contact.fraction in 0.0..1.0)
        assertTrue(contact.normal.isFinite())
        assertTrue(contact.relativeDisplacement.isFinite())
        assertEquals(1.0, contact.normal.length(), 1e-9)
        assertTrue(contact.playerAxisFraction in 0.0..1.0)
        assertTrue(contact.enemyAxisFraction in 0.0..1.0)
        listOf(contact.playerPoint to at(player, contact.fraction), contact.enemyPoint to at(enemy, contact.fraction)).forEach { (surface, blade) ->
            assertNotNull(surface)
            assertEquals(blade.radiusMeters, surface.distanceTo(closestPoint(surface, blade.base, blade.tip)), 1e-8)
        }
    }

    private fun at(sweep: BladeSweep, t: Double) = BladeSegment(
        sweep.previous.base * (1.0 - t) + sweep.current.base * t,
        sweep.previous.tip * (1.0 - t) + sweep.current.tip * t,
        sweep.previous.radiusMeters * (1.0 - t) + sweep.current.radiusMeters * t,
    )

    private fun horizontal(z: Double, x: Double = 0.0) = BladeSegment(Vector3(x - 1.0, 0.0, z), Vector3(x + 1.0, 0.0, z), 0.002)
    private fun vertical(z: Double, x: Double = 0.0) = BladeSegment(Vector3(x, -1.0, z), Vector3(x, 1.0, z), 0.003)
    private fun point(point: Vector3, radius: Double) = BladeSegment(point, point, radius)
    private fun stationary(blade: BladeSegment) = BladeSweep(blade, blade)
}
