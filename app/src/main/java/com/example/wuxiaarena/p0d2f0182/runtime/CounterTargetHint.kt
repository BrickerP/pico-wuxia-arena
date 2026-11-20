package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.core.math.closestSegmentPoints

internal enum class CounterTargetHint { WITHDRAW, LEFT_SHOULDER, RIGHT_SHOULDER, SHOULDER_LINE }

internal fun lessonCounterTarget(head: Vector3, rotation: Quaternion, pose: AttackPoseSample): CounterTargetHint? {
    val eyeRight = rotation.rotate(Vector3(1.0, 0.0, 0.0)) ?: return null
    val right = Vector3(eyeRight.x, 0.0, eyeRight.z).normalizedOrNull() ?: return null
    val target = pose.contact.bodyTop
    if ((target - head).dot(Vector3(right.z, 0.0, -right.x)) <= 0.0) return null
    fun clearance(side: Double): Double {
        val nearest = closestSegmentPoints(head + right * (.28 * side), target + right * (.16 * side),
            pose.bladeBase, pose.bladeTip) ?: return 0.0
        return nearest.first.distanceTo(nearest.second)
    }
    val leftGap = clearance(-1.0)
    val rightGap = clearance(1.0)
    return when {
        minOf(leftGap, rightGap) >= .28 -> CounterTargetHint.SHOULDER_LINE
        leftGap >= .14 && leftGap - rightGap >= .12 -> CounterTargetHint.LEFT_SHOULDER
        rightGap >= .14 && rightGap - leftGap >= .12 -> CounterTargetHint.RIGHT_SHOULDER
        minOf(leftGap, rightGap) >= .14 -> CounterTargetHint.SHOULDER_LINE
        else -> null
    }
}
