package com.example.wuxiaarena.core.math

import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.sqrt

/** Stage coordinates are in metres; initial forward is -Z. */
data class Vector3(val x: Double, val y: Double, val z: Double) {
    fun isFinite(): Boolean = x.isFinite() && y.isFinite() && z.isFinite()

    operator fun plus(other: Vector3) = Vector3(x + other.x, y + other.y, z + other.z)
    operator fun minus(other: Vector3) = Vector3(x - other.x, y - other.y, z - other.z)
    operator fun times(scale: Double) = Vector3(x * scale, y * scale, z * scale)
    fun dot(other: Vector3): Double = x * other.x + y * other.y + z * other.z
    fun cross(other: Vector3) = Vector3(
        y * other.z - z * other.y,
        z * other.x - x * other.z,
        x * other.y - y * other.x,
    )
    fun length(): Double = hypot(hypot(x, y), z)
    fun distanceTo(other: Vector3): Double = hypot(hypot(x - other.x, y - other.y), z - other.z)

    fun normalizedOrNull(): Vector3? {
        if (!isFinite()) return null
        val length = length()
        if (!length.isFinite() || length == 0.0) return null
        return this * (1.0 / length)
    }
}

/** Rotation components are ordered x, y, z, w. */
data class Quaternion(val x: Double, val y: Double, val z: Double, val w: Double) {
    /** Composition applies [other] first, followed by this rotation. */
    operator fun times(other: Quaternion) = Quaternion(
        w * other.x + x * other.w + y * other.z - z * other.y,
        w * other.y - x * other.z + y * other.w + z * other.x,
        w * other.z + x * other.y - y * other.x + z * other.w,
        w * other.w - x * other.x - y * other.y - z * other.z,
    )

    /** Invalid rotations remain unavailable at the tracking boundary. */
    fun rotate(vector: Vector3): Vector3? {
        val rotation = normalizedOrNull() ?: return null
        if (!vector.isFinite()) return null
        return rotation.rotateUnit(vector).takeIf { it.isFinite() }
    }

    internal fun rotateUnit(vector: Vector3): Vector3 {
        val twiceCrossX = (y * vector.z - z * vector.y) * 2.0
        val twiceCrossY = (z * vector.x - x * vector.z) * 2.0
        val twiceCrossZ = (x * vector.y - y * vector.x) * 2.0
        return Vector3(
            vector.x + twiceCrossX * w + (y * twiceCrossZ - z * twiceCrossY),
            vector.y + twiceCrossY * w + (z * twiceCrossX - x * twiceCrossZ),
            vector.z + twiceCrossZ * w + (x * twiceCrossY - y * twiceCrossX),
        )
    }

    fun normalizedOrNull(): Quaternion? {
        if (!x.isFinite() || !y.isFinite() || !z.isFinite() || !w.isFinite()) return null

        val scale = maxOf(abs(x), abs(y), abs(z), abs(w))
        if (scale == 0.0) return null

        val sx = x / scale
        val sy = y / scale
        val sz = z / scale
        val sw = w / scale
        val length = sqrt(sx * sx + sy * sy + sz * sz + sw * sw)
        return Quaternion(sx / length, sy / length, sz / length, sw / length)
    }
}
