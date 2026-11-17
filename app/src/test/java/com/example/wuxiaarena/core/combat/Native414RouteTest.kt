package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.math.closestSegmentPoints
import org.junit.Assert.*
import org.junit.Test

class Native414RouteTest {
    @Test fun recordedPenetratingStartCannotBecomeASafeReleaseFromClearTargets() {
        val f = Native414Fixture
        val shape = DaoBladeShape.shape
        val enemy = shape.at(f.enemy)
        fun gap(grip: WeaponGrip) = shape.at(grip).minOf { p ->
            enemy.minOf { e ->
                val pair = checkNotNull(closestSegmentPoints(p.base, p.tip, e.base, e.tip))
                pair.first.distanceTo(pair.second) - p.radiusMeters - e.radiusMeters
            }
        }
        val initial = gap(f.held)
        var clear = 0
        var safe = 0
        var released = 0
        var penetrating = 0
        for (raw in f.raw) {
            val targetGap = gap(raw)
            val path = BladeShapeSweep(shape, f.held, raw, 0.0)
            val cert = targetGap > f.error + 1e-7 &&
                separatingBladeShapePairs(path, f.enemySweep, f.normal)
            val constraint = WeaponContactConstraint()
            constraint.lock(raw, f.held, f.normal)
            if (constraint.releaseForPlayerWithdrawal(f.enemySweep, raw)) released++
            if (targetGap > f.error + 1e-7) clear++
            if (cert) safe++
            if (targetGap > f.error + 1e-7 && !cert) {
                for (k in 1 until 64) {
                    if (gap(interpolateGrip(f.held, raw, k / 64.0)) < -f.error - 1e-6) {
                        penetrating++
                        break
                    }
                }
            }
        }
        println("NATIVE414_ROUTES heldGap=$initial sourceError=${f.error} raw=${f.raw.size} targetClear=$clear certified=$safe released=$released robustInteriorIntrusion=$penetrating")
        assertTrue("Recorded held pose already penetrates beyond source uncertainty", initial < -f.error - 1e-6)
        assertTrue("Some real raw targets clear the enemy", clear > 0)
        assertTrue("Robust intermediate penetration witnesses remain", penetrating > 0)
        assertEquals("An already-penetrating start cannot certify nonpenetration", 0, safe)
        assertEquals("A clear target alone cannot release this unsafe old state", 0, released)
    }
}
