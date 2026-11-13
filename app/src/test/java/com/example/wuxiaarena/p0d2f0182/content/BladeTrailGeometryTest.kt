package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.*
import org.junit.Test
import kotlin.math.cos
import kotlin.math.sin

/** Geometry contracts use declared test poses, not an offline substitute for native pixel evidence. */
class BladeTrailGeometryTest {
    private val geometry = BladeTrailGeometry()

    @Test fun measuredTipBandHasTransparentEdgesAndFiniteTriangles() {
        assertNull(sample(0.0, 0L))
        val ribbon = requireNotNull(sample(0.1, 10_000_000L))
        assertEquals(listOf(0, 1, 3, 3, 1, 4, 1, 2, 4, 4, 2, 5), ribbon.triangleIndices.take(12))
        assertEquals(-0.94, ribbon.positions[0].z, 1e-12)
        assertEquals(-0.97, ribbon.positions[1].z, 1e-12)
        assertEquals(-1.0, ribbon.positions[2].z, 1e-12)
        assertEquals((2.0 / 3.0).toFloat(), ribbon.alphas[4], 0f)
        assertTrue(ribbon.alphas[1] < ribbon.alphas[4])
        checkRibbon(ribbon)
    }

    @Test fun sixCentimetreTailAndOneCentimetreCoreShareTheActualBladeCentre() {
        sample(0.0, 0L)
        val ribbon = requireNotNull(sample(0.1, 10_000_000L))
        val tail = ribbon.positions.take(ribbon.coreVertexOffset)
        val core = ribbon.positions.drop(ribbon.coreVertexOffset)
        assertEquals(0.06, tail[0].distanceTo(tail[2]), 1e-12)
        assertEquals(0.01, core[0].distanceTo(core[2]), 1e-12)
        assertEquals(tail[1], core[1])
        assertEquals(tail[4], core[4])
        checkRibbon(ribbon)
    }

    @Test fun aShortBladeNeverGrowsALargerThanMeasuredGlowBand() {
        geometry.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, -0.02), 0L, 2.0, false, 1L)
        val ribbon = requireNotNull(geometry.sample(Vector3(0.1, 1.0, 0.0), Vector3(0.1, 1.0, -0.02),
            10_000_000L, 2.0, false, 1L))
        assertTrue(ribbon.positions.all { it.z in -0.020000001..0.000000001 })
        assertEquals(0.02, ribbon.positions[0].distanceTo(ribbon.positions[2]), 1e-12)
        checkRibbon(ribbon)
    }

    @Test fun stationarySamplesFadeAndHistoryExpiresAt65ms() {
        sample(0.0, 0L)
        val first = requireNotNull(sample(0.1, 10_000_000L))
        val fading = requireNotNull(sample(0.1, 20_000_000L))
        assertEquals(first.positions.take(first.coreVertexOffset), fading.positions.take(fading.coreVertexOffset))
        assertTrue(fading.alphas[4] < first.alphas[4])
        assertNull(sample(0.1, 75_000_000L))
    }

    @Test fun repeatedTimestampCannotCreateAnotherSegment() {
        assertNull(sample(0.0, 10_000_000L))
        assertNull(sample(0.2, 10_000_000L))
        val ribbon = requireNotNull(sample(0.2, 20_000_000L))
        assertEquals(6, ribbon.coreVertexOffset)
        checkRibbon(ribbon)
    }

    @Test fun pureAxialThrustDoesNotInventASidewaysArc() {
        val base = Vector3(0.0, 1.0, 0.0)
        val tip = Vector3(0.0, 1.0, -1.0)
        assertNull(geometry.sample(base, tip, 0L, 2.0, false, 1L))
        assertNull(geometry.sample(base + Vector3(0.0, 0.0, -0.1), tip + Vector3(0.0, 0.0, -0.1),
            10_000_000L, 2.0, false, 1L))
    }

    @Test fun presentationGapAndTimeReversalCreateNewBaselines() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10_000_000L))
        assertNull(sample(0.2, 100_000_000L))
        requireNotNull(sample(0.3, 110_000_000L))
        assertNull(sample(0.4, 1L))
        assertEquals(6, requireNotNull(sample(0.5, 2L)).coreVertexOffset)
    }

    @Test fun aFastSameGenerationSweepKeepsItsMeasuredFeedback() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10_000_000L))
        val ribbon = requireNotNull(sample(0.701, 33_000_000L))
        assertTrue(ribbon.positions.any { it.x == 0.0 })
        assertTrue(ribbon.positions.any { it.x == 0.701 })
        for (section in ribbon.positions.chunked(3)) {
            assertTrue(section[0].distanceTo(section[2]) <= 0.060000000001)
        }
        checkRibbon(ribbon)
    }

    @Test fun normalThirtyFpsPresentationStillConnectsMeasuredPoses() {
        sample(0.0, 0L)
        val ribbon = requireNotNull(sample(0.15, 33_000_000L))
        assertEquals(6, ribbon.coreVertexOffset)
        checkRibbon(ribbon)
    }

    @Test fun invalidOrZeroLengthBladeClearsAllHistory() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10L))
        assertNull(geometry.sample(Vector3(Double.NaN, 1.0, 0.0), Vector3(0.0, 1.0, -1.0), 20L, 2.0, false, 1L))
        assertNull(sample(0.2, 30L))
        requireNotNull(sample(0.3, 40L))
        assertNull(geometry.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, 0.0), 50L, 2.0, false, 1L))
        assertNull(sample(0.4, 60L))
    }

    @Test fun eightSampleBudgetRemainsBoundedWithFeatherRows() {
        var ribbon: BladeTrailGeometry.Ribbon? = null
        repeat(20) { index -> ribbon = sample(index * 0.01, index * 1_000_000L) }
        val result = requireNotNull(ribbon)
        assertEquals(7 * 6, result.coreVertexOffset)
        assertTrue(result.positions.size <= 84)
        assertTrue(result.triangleIndices.size / 3 <= 56)
        checkRibbon(result)
        geometry.clear()
        assertNull(sample(0.3, 21_000_000L))
    }

    @Test fun timestampDifferenceOverflowExpiresHistory() {
        sample(0.0, Long.MIN_VALUE)
        requireNotNull(sample(0.1, Long.MIN_VALUE + 1L))
        assertNull(sample(0.2, Long.MAX_VALUE))
    }

    @Test fun resolverRestAndGenerationStillOwnContinuity() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10_000_000L))
        assertNull(geometry.sample(Vector3(0.2, 1.0, 0.0), Vector3(0.2, 1.0, -1.0),
            20_000_000L, 0.30, true, 1L))
        assertNull(geometry.sample(Vector3(0.3, 1.0, 0.0), Vector3(0.3, 1.0, -1.0),
            30_000_000L, 0.300001, false, 1L))
        checkRibbon(requireNotNull(sample(0.4, 40_000_000L)))
        assertNull(geometry.sample(Vector3(10.0, 1.0, 0.0), Vector3(10.0, 1.0, -1.0),
            50_000_000L, 2.0, false, 2L))
        val next = requireNotNull(geometry.sample(Vector3(10.1, 1.0, 0.0), Vector3(10.1, 1.0, -1.0),
            60_000_000L, 2.0, false, 2L))
        assertTrue(next.positions.all { it.x >= 10.0 })
    }

    @Test fun invalidSpeedsClearAndZeroSpeedIsFullyTransparent() {
        for (speed in listOf(Double.NaN, Double.POSITIVE_INFINITY, -0.01)) {
            sample(0.0, 0L)
            requireNotNull(sample(0.1, 10L))
            assertNull(geometry.sample(Vector3(0.2, 1.0, 0.0), Vector3(0.2, 1.0, -1.0), 20L, speed, false, 1L))
            assertNull(sample(0.3, 30L))
            geometry.clear()
        }
        geometry.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, -1.0), 0L, 0.0, false, 1L)
        val ribbon = requireNotNull(geometry.sample(Vector3(0.1, 1.0, 0.0), Vector3(0.1, 1.0, -1.0), 10L, 0.0, false, 1L))
        assertTrue(ribbon.alphas.all { it == 0f })
    }

    @Test fun hotCoreUsesOnlyLast12msOfTheMeasuredSegment() {
        sample(0.0, 0L)
        val ribbon = requireNotNull(sample(0.3, 30_000_000L))
        val core = ribbon.positions.drop(ribbon.coreVertexOffset)
        val alpha = ribbon.alphas.drop(ribbon.coreVertexOffset)
        assertEquals(0.18, core[1].x, 1e-12)
        assertEquals(-0.97, core[1].z, 1e-12)
        assertEquals(0.3, core[4].x, 1e-12)
        assertEquals(0f, alpha[1], 0f)
        assertEquals((2.0 / 3.0).toFloat(), alpha[4], 0f)
        checkRibbon(ribbon)
    }

    @Test fun coreExpiresAt12msWhileTheTailFades() {
        sample(0.0, 0L)
        val first = requireNotNull(sample(0.1, 10_000_000L))
        assertTrue(first.positions.size > first.coreVertexOffset)
        val result = requireNotNull(sample(0.1, 22_000_000L))
        assertEquals(result.coreVertexOffset, result.positions.size)
        assertTrue(result.alphas.any { it > 0f })
        checkRibbon(result)
    }

    @Test fun measuredBladeRotationDoesNotExpandTheFeatherBand() {
        sample(0.0, 0L)
        val angle = Math.toRadians(8.0)
        val base = Vector3(0.05, 1.0, 0.0)
        val tip = base + Vector3(sin(angle), 0.0, -cos(angle))
        val result = requireNotNull(geometry.sample(base, tip, 30_000_000L, 2.0, false, 1L))
        val lastTail = result.positions.take(result.coreVertexOffset).takeLast(3)
        assertEquals(tip, lastTail[2])
        assertEquals(0.06, lastTail[0].distanceTo(lastTail[2]), 1e-12)
        assertEquals(0.0, (tip - lastTail[1]).cross(tip - base).length(), 1e-12)
        checkRibbon(result)
    }

    @Test fun distanceAloneDoesNotResetAValidSameGenerationTrail() {
        for (distance in listOf(0.30, Math.nextUp(0.30), 0.60)) {
            val trail = BladeTrailGeometry()
            trail.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, -1.0), 0L, 20.0, false, 1L)
            val ribbon = requireNotNull(trail.sample(Vector3(distance, 1.0, 0.0), Vector3(distance, 1.0, -1.0),
                33_000_000L, 20.0, false, 1L))
            assertTrue(ribbon.positions.any { it.x == 0.0 })
            assertTrue(ribbon.positions.any { it.x == distance })
            checkRibbon(ribbon)
        }
    }

    @Test fun expiryBoundaryIsExactlySixtyFiveMilliseconds() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 33_000_000L))
        assertTrue(sample(0.1, 64_999_999L) != null)
        assertNull(sample(0.1, 65_000_000L))
    }

    private fun sample(x: Double, time: Long) = geometry.sample(
        Vector3(x, 1.0, 0.0), Vector3(x, 1.0, -1.0), time, 2.0, false, 1L)

    private fun checkRibbon(ribbon: BladeTrailGeometry.Ribbon) {
        assertEquals(ribbon.positions.size, ribbon.alphas.size)
        assertTrue(ribbon.positions.all { it.isFinite() })
        assertTrue(ribbon.alphas.all { it in 0f..1f })
        for (section in ribbon.alphas.chunked(3)) {
            assertEquals(0f, section[0], 0f)
            assertEquals(0f, section[2], 0f)
        }
        for (triangle in ribbon.triangleIndices.chunked(3)) {
            assertTrue(triangle.all { it in ribbon.positions.indices })
            val (a, b, c) = triangle.map { ribbon.positions[it] }
            assertTrue((b - a).cross(c - a).length() > 0.0)
        }
    }
}
