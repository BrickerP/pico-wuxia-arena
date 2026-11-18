package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Test

class ExtremeGripRotationTest {
    @Test fun signedNonUnitGripRotationsPlaceTheRealCapsuleChain() {
        val position = Vector3(-1.7, 0.24, -0.81)
        for (magnitude in listOf(1e-290, -1e-290, 1e250, -1e250)) {
            val rotation = Quaternion(magnitude, -.3 * magnitude, .7 * magnitude, -.2 * magnitude)
            val unit = requireNotNull(rotation.normalizedOrNull())
            val imaginary = Vector3(unit.x, unit.y, unit.z)
            fun expected(point: Vector3): Vector3 {
                val twiceCross = imaginary.cross(point) * 2.0
                return position + (point + twiceCross * unit.w + imaginary.cross(twiceCross))
            }
            val placed = playerBlade(WeaponGrip(position, rotation))
            for ((index, local) in PlayerBladeShape.capsules.withIndex()) {
                assertEquals(expected(local.base), placed[index].base)
                assertEquals(expected(local.tip), placed[index].tip)
            }
        }
    }
}
