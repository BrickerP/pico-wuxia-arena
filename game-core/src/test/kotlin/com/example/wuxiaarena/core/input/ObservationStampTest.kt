package com.example.wuxiaarena.core.input

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ObservationStampTest {
    @Test
    fun preservesSignedMonotonicTimeWithoutTreatingItAsDeviceTime() {
        val stamp = ObservationStamp(0, -1, 0, InputOrigin.DESKTOP)

        assertEquals(-1L, stamp.receivedAtNanos)
    }

    @Test
    fun rejectsNegativeSequenceOrCoordinateEpoch() {
        assertThrows(IllegalArgumentException::class.java) {
            ObservationStamp(-1, 0, 0, InputOrigin.PICO)
        }
        assertThrows(IllegalArgumentException::class.java) {
            ObservationStamp(0, 0, -1, InputOrigin.PICO)
        }
    }
}
