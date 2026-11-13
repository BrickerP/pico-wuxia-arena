package com.example.wuxiaarena.core.math

/** Closest axis witnesses, including exactly degenerate and parallel segments. */
internal fun closestSegmentPoints(a0: Vector3, a1: Vector3, b0: Vector3, b1: Vector3): Pair<Vector3, Vector3>? {
    if (!a0.isFinite() || !a1.isFinite() || !b0.isFinite() || !b1.isFinite()) return null
    val a = a1 - a0
    val b = b1 - b0
    val offset = a0 - b0
    val aLength = a.length()
    val bLength = b.length()
    if (!aLength.isFinite() || !bLength.isFinite() || !offset.isFinite()) return null
    if (aLength == 0.0 && bLength == 0.0) return a0 to b0
    val aUnit = if (aLength == 0.0) Vector3(0.0, 0.0, 0.0) else a * (1.0 / aLength)
    val bUnit = if (bLength == 0.0) Vector3(0.0, 0.0, 0.0) else b * (1.0 / bLength)
    val bo = bUnit.dot(offset)
    val ao = aUnit.dot(offset)
    val ab = aUnit.dot(bUnit)
    if (!listOf(bo, ao, ab).all { it.isFinite() }) return null
    if (aLength == 0.0) return a0 to (b0 + bUnit * bo.coerceIn(0.0, bLength))
    if (bLength == 0.0) return (a0 + aUnit * (-ao).coerceIn(0.0, aLength)) to b0
    // The cross-product form avoids aa*bb-ab*ab cancellation for thin, almost parallel blades.
    val cross = aUnit.cross(bUnit)
    val crossLength = cross.length()
    var alongA = if (crossLength > 0.0) {
        (bUnit.cross(offset).dot(cross * (1.0 / crossLength)) / crossLength).coerceIn(0.0, aLength)
    } else {
        0.0
    }
    var alongB = ab * alongA + bo
    if (alongB < 0.0) {
        alongB = 0.0
        alongA = (-ao).coerceIn(0.0, aLength)
    } else if (alongB > bLength) {
        alongB = bLength
        alongA = (ab * bLength - ao).coerceIn(0.0, aLength)
    }
    val pointA = a0 * (1.0 - alongA / aLength) + a1 * (alongA / aLength)
    val pointB = b0 * (1.0 - alongB / bLength) + b1 * (alongB / bLength)
    return (pointA to pointB).takeIf { pointA.isFinite() && pointB.isFinite() }
}

/** Orthogonal projection clamped to a finite segment; a zero-length segment is a point. */
internal fun closestPoint(point: Vector3, start: Vector3, end: Vector3): Vector3 {
    val axis = end - start
    val length = axis.length()
    if (length == 0.0 || !length.isFinite()) return start
    val unit = axis * (1.0 / length)
    val along = (point - start).dot(unit).coerceIn(0.0, length)
    return start * (1.0 - along / length) + end * (along / length)
}
