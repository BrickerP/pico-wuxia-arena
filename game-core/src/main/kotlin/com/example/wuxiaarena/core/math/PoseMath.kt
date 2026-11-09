package com.example.wuxiaarena.core.math

import kotlin.math.abs
import kotlin.math.sqrt

/** Stage coordinates are in metres; initial forward is -Z. */
data class Vector3(val x: Double, val y: Double, val z: Double) {
    fun isFinite(): Boolean = x.isFinite() && y.isFinite() && z.isFinite()
}

/** Rotation components are ordered x, y, z, w. */
data class Quaternion(val x: Double, val y: Double, val z: Double, val w: Double) {
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
