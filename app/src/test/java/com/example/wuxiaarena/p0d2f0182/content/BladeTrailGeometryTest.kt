package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class BladeTrailGeometryTest {
    private val geometry = BladeTrailGeometry()

    @Test
    fun realBladeSamplesProduceFiniteTrianglesWithFadingVertexAlpha() {
        assertNull(sample(0.0, 0L))
        val ribbon = requireNotNull(sample(0.1, 10_000_000L))

        assertEquals(listOf(0, 1, 2, 2, 1, 3), ribbon.triangleIndices.take(6))
        assertEquals(Vector3(0.0, 1.0, -0.35), ribbon.positions[0])
        assertEquals(Vector3(0.0, 1.0, -0.98), ribbon.positions[1])
        assertEquals(Vector3(0.1, 1.0, -0.35), ribbon.positions[2])
        assertEquals(ribbon.positions.size, ribbon.alphas.size)
        assertTrue(ribbon.positions.all { it.isFinite() })
        assertTrue(ribbon.alphas.first() < ribbon.alphas.last())
        assertEquals((2.0 / 3.0).toFloat(), ribbon.alphas.last(), 0f)
        assertNonDegenerate(ribbon)
    }

    @Test
    fun aStationaryBladeOnlyFadesExistingHistoryAndThenDisappears() {
        assertNull(sample(0.0, 0L))
        val first = requireNotNull(sample(0.1, 10_000_000L))
        val fading = requireNotNull(sample(0.1, 20_000_000L))

        assertEquals(first.positions.take(first.coreVertexOffset), fading.positions.take(fading.coreVertexOffset))
        assertEquals(first.triangleIndices.filter { it < first.coreVertexOffset },
            fading.triangleIndices.filter { it < fading.coreVertexOffset })
        assertTrue(fading.alphas[fading.coreVertexOffset - 1] < first.alphas[first.coreVertexOffset - 1])
        assertNull(sample(0.1, 75_000_000L))
        assertNull(sample(0.1, 85_000_000L))
    }

    @Test
    fun repeatedTimestampCannotCreateAnotherSegment() {
        assertNull(sample(0.0, 10_000_000L))
        assertNull(sample(0.2, 10_000_000L))
        val ribbon = requireNotNull(sample(0.2, 20_000_000L))

        assertEquals(4, ribbon.coreVertexOffset)
        assertNonDegenerate(ribbon)
    }

    @Test
    fun collinearMovementDoesNotEmitZeroAreaTriangles() {
        val base = Vector3(0.0, 1.0, 0.0)
        val tip = Vector3(0.0, 1.0, -1.0)
        assertNull(geometry.sample(base, tip, 0L, 2.0, false, 1L))
        assertNull(geometry.sample(base + Vector3(0.0, 0.0, -0.1), tip + Vector3(0.0, 0.0, -0.1),
            10L, 2.0, false, 1L))
    }

    @Test
    fun anExpiredIntervalAndTimeReversalEachStartANewBaseline() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10_000_000L))
        assertNull(sample(0.2, 100_000_000L))
        requireNotNull(sample(0.3, 110_000_000L))
        assertNull(sample(0.4, 1L))
        assertEquals(4, requireNotNull(sample(0.5, 2L)).coreVertexOffset)
    }

    @Test
    fun invalidOrZeroLengthBladesClearAllPreviousHistory() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10L))
        assertNull(geometry.sample(Vector3(Double.NaN, 1.0, 0.0), Vector3(0.0, 1.0, -1.0),
            20L, 2.0, false, 1L))
        assertNull(sample(0.2, 30L))
        requireNotNull(sample(0.3, 40L))
        assertNull(geometry.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, 0.0),
            50L, 2.0, false, 1L))
        assertNull(sample(0.4, 60L))
    }

    @Test
    fun historyIsBoundedAndExplicitClearDropsItsGeometry() {
        var ribbon: BladeTrailGeometry.Ribbon? = null
        repeat(20) { index -> ribbon = sample(index * 0.01, index * 1_000_000L) }

        assertEquals(7 * 4, requireNotNull(ribbon).coreVertexOffset)
        assertTrue(requireNotNull(ribbon).positions.size <= 7 * 8)
        assertTrue(requireNotNull(ribbon).triangleIndices.all { it < requireNotNull(ribbon).positions.size })
        geometry.clear()
        assertNull(sample(0.3, 21_000_000L))
    }

    @Test
    fun aTimestampDifferenceOverflowExpiresHistory() {
        sample(0.0, Long.MIN_VALUE)
        requireNotNull(sample(0.1, Long.MIN_VALUE + 1L))

        assertNull(sample(0.2, Long.MAX_VALUE))
    }

    @Test
    fun resolverRestBoundaryClearsHistoryAndJustAboveItCanProduceARibbon() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10_000_000L))
        assertNull(geometry.sample(Vector3(0.2, 1.0, 0.0), Vector3(0.2, 1.0, -1.0),
            20_000_000L, 0.30, true, 1L))
        assertNull(geometry.sample(Vector3(0.3, 1.0, 0.0), Vector3(0.3, 1.0, -1.0),
            30_000_000L, 0.300001, false, 1L))
        val ribbon = requireNotNull(geometry.sample(Vector3(0.4, 1.0, 0.0), Vector3(0.4, 1.0, -1.0),
            40_000_000L, 0.300001, false, 1L))

        assertTrue(ribbon.positions.all { it.x >= 0.3 })
        assertEquals((0.300001 / 1.300001).toFloat(), ribbon.alphas.last(), 0f)
    }

    @Test
    fun lowSpeedTrackingJitterMarkedAtRestNeverEmitsGeometry() {
        repeat(20) { index ->
            val x = if (index % 2 == 0) 0.0001 else -0.0001
            assertNull(geometry.sample(Vector3(x, 1.0, 0.0), Vector3(x, 1.0, -1.0),
                index * 1_000_000L, 0.08, true, 1L))
        }
        assertNull(sample(0.1, 30_000_000L))
    }

    @Test
    fun aMotionGenerationChangeStartsANewBaselineWithoutJoiningTheOldPose() {
        sample(0.0, 0L)
        requireNotNull(sample(0.1, 10_000_000L))
        assertNull(geometry.sample(Vector3(10.0, 1.0, 0.0), Vector3(10.0, 1.0, -1.0),
            20_000_000L, 2.0, false, 2L))
        val ribbon = requireNotNull(geometry.sample(Vector3(10.1, 1.0, 0.0), Vector3(10.1, 1.0, -1.0),
            30_000_000L, 2.0, false, 2L))

        assertEquals(4, ribbon.coreVertexOffset)
        assertTrue(ribbon.positions.all { it.x >= 10.0 })
    }

    @Test
    fun invalidSpeedsClearHistoryAndZeroSpeedRemainsTransparent() {
        for (speed in listOf(Double.NaN, Double.POSITIVE_INFINITY, -0.01)) {
            sample(0.0, 0L)
            requireNotNull(sample(0.1, 10L))
            assertNull(geometry.sample(Vector3(0.2, 1.0, 0.0), Vector3(0.2, 1.0, -1.0),
                20L, speed, false, 1L))
            assertNull(sample(0.3, 30L))
            geometry.clear()
        }
        assertNull(geometry.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, -1.0),
            0L, 0.0, false, 1L))
        val ribbon = requireNotNull(geometry.sample(Vector3(0.1, 1.0, 0.0), Vector3(0.1, 1.0, -1.0),
            10L, 0.0, false, 1L))
        assertTrue(ribbon.alphas.all { it == 0f })
    }

    @Test
    fun hotCoreClipsToTwelveMillisecondsOfTheActualSweep() {
        sample(0.0, 0L)
        val ribbon = requireNotNull(sample(0.3, 30_000_000L))
        val core = ribbon.positions.drop(ribbon.coreVertexOffset)
        val coreAlpha = ribbon.alphas.drop(ribbon.coreVertexOffset)

        // The leading edge starts 60% through this real 30ms sweep, at x=0.18m.
        assertEquals(4, core.size)
        assertEquals(0.18, core[0].x, 1e-12)
        assertEquals(-0.665, core[0].z, 1e-12)
        assertEquals(0.3, core[2].x, 1e-12)
        assertEquals(0f, coreAlpha[0], 0f)
        assertEquals((2.0 / 3.0).toFloat(), coreAlpha[2], 0f)
        assertNonDegenerate(ribbon)
    }

    @Test
    fun hotCoreExpiresWhileTheMeasuredTailKeepsFading() {
        sample(0.0, 0L)
        val contact = requireNotNull(sample(0.1, 10_000_000L))
        assertTrue(contact.positions.size > contact.coreVertexOffset)
        val afterCore = requireNotNull(sample(0.1, 22_000_000L))

        assertEquals(afterCore.coreVertexOffset, afterCore.positions.size)
        assertTrue(afterCore.alphas.any { it > 0f })
        assertEquals(contact.positions.take(contact.coreVertexOffset), afterCore.positions)
    }

    @Test
    fun hotCoreFollowsAChangedBladeOrientationWithoutInventingAnArc() {
        geometry.sample(Vector3(0.0, 1.0, 0.0), Vector3(0.0, 1.0, -1.0), 0L, 2.0, false, 1L)
        val ribbon = requireNotNull(geometry.sample(
            Vector3(0.2, 1.1, 0.0), Vector3(0.8, 1.9, 0.0), 30_000_000L, 2.0, false, 1L))
        val core = ribbon.positions.drop(ribbon.coreVertexOffset)

        assertEquals(0.599, core[2].x, 1e-12)
        assertEquals(1.632, core[2].y, 1e-12)
        assertEquals(0.0, core[2].z, 0.0)
        assertEquals(0.788, core[3].x, 1e-12)
        assertEquals(1.884, core[3].y, 1e-12)
        assertEquals(0.0, core[3].z, 0.0)
        assertTrue(core.all { it.isFinite() })
        assertNonDegenerate(ribbon)
    }

    private fun sample(x: Double, atNanos: Long): BladeTrailGeometry.Ribbon? =
        geometry.sample(Vector3(x, 1.0, 0.0), Vector3(x, 1.0, -1.0), atNanos, 2.0, false, 1L)

    private fun assertNonDegenerate(ribbon: BladeTrailGeometry.Ribbon) {
        ribbon.triangleIndices.chunked(3).forEach { triangle ->
            val a = ribbon.positions[triangle[0]]
            val b = ribbon.positions[triangle[1]]
            val c = ribbon.positions[triangle[2]]
            assertTrue((b - a).cross(c - a).length() > 0.0)
        }
    }
}
