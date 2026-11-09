package com.example.wuxiaarena.core.math

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

class PoseMathTest {
    @Test
    fun normalizesFiniteQuaternionsWithoutOverflow() {
        val rotation = Quaternion(Double.MAX_VALUE, Double.MAX_VALUE, 0.0, 0.0).normalizedOrNull()

        assertNotNull(rotation)
        assertEquals(1.0 / sqrt(2.0), rotation!!.x, 1e-12)
        assertEquals(1.0 / sqrt(2.0), rotation.y, 1e-12)
        assertEquals(0.0, rotation.z, 0.0)
        assertEquals(0.0, rotation.w, 0.0)
    }

    @Test
    fun rejectsZeroAndNonFiniteQuaternions() {
        assertNull(Quaternion(0.0, 0.0, 0.0, 0.0).normalizedOrNull())
        assertNull(Quaternion(Double.NaN, 0.0, 0.0, 1.0).normalizedOrNull())
        assertNull(Quaternion(0.0, Double.POSITIVE_INFINITY, 0.0, 1.0).normalizedOrNull())
    }

    @Test
    fun checksAllPositionComponentsForFiniteValues() {
        assertTrue(Vector3(0.2, 1.6, -0.3).isFinite())
        assertFalse(Vector3(0.2, 1.6, Double.NaN).isFinite())
        assertFalse(Vector3(Double.NEGATIVE_INFINITY, 1.6, -0.3).isFinite())
    }
}
