package com.example.wuxiaarena.p0d2f0182.content

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SceneWeatherMotionTest {
    @Test fun rainTilesRemainContiguousAcrossWrapAndLongUptime() {
        for (now in listOf(Long.MIN_VALUE, -1L, 0L, 1L, 833_333_333L, 2_499_999_999L, 2_500_000_000L, Long.MAX_VALUE)) {
            val heights = (0..2).map { weatherTileHeight(it, now) }.sorted()
            assertTrue(heights.all { it >= -2f && it <= 4f })
            assertEquals(2f, heights[1] - heights[0], 0.000001f)
            assertEquals(2f, heights[2] - heights[1], 0.000001f)
        }
        assertEquals(weatherTileHeight(1, 0), weatherTileHeight(1, 2_500_000_000L), 0f)
        assertTrue(weatherTileHeight(1, 250_000_000L) < weatherTileHeight(1, 0))
    }

    @Test fun hazeStaysInItsSideLaneAndHasNoUnboundedElapsedFloat() {
        for (now in listOf(Long.MIN_VALUE, -1L, 0L, 10_000_000_000L, 30_000_000_000L, Long.MAX_VALUE)) {
            val left = weatherHazeDrift(0, now)
            val right = weatherHazeDrift(1, now)
            assertTrue(kotlin.math.abs(left) <= 0.12f)
            assertEquals(-left, right, 0.000001f)
            assertEquals(left, weatherHazeDrift(0, Math.floorMod(now, 40_000_000_000L)), 0f)
        }
    }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsInvalidRainTile() { weatherTileHeight(3, 0) }

    @Test(expected = IllegalArgumentException::class)
    fun rejectsInvalidHazeSide() { weatherHazeDrift(2, 0) }
}
