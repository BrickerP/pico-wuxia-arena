package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.BladeSegment
import com.example.wuxiaarena.core.combat.BladeSweep
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.firstRigidBladeContact
import com.example.wuxiaarena.core.combat.playerBladeAxis
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class OpeningGuardTraceTest {
    private val head = Vector3(0.0, 1.6949999332427979, 0.0)
    private val enemy = Vector3(0.0, .028, -1.5455358)
    private val forwardGuard = WeaponGrip(
        Vector3(.15799996256828308, 1.6749999523162842, -.30999991297721863),
        Quaternion(.053226113131682705, .31902593261740403, -.00000017881393369554295, .946250196934435),
    )
    private val closeGuard = forwardGuard.copy(position = forwardGuard.position.copy(z = -.20))
    private val overhead = arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD)

    @Test fun returningTheGripChangesTheFirstContactFromAWithdrawingWindupToTheIncomingStrike() {
        val early = firstContact(forwardGuard)
        assertEquals(.17616525, early.sourceTime, .0001)
        assertTrue(early.sourceTime < overhead.sourcePhaseSeconds[1])
        assertTrue(early.displacement.z < 0.0)
        assertTrue(early.displacement.dot(head - early.axisPoint) < 0.0)

        val incoming = firstContact(closeGuard)
        assertEquals(.89714, incoming.sourceTime, .0001)
        assertTrue(incoming.sourceTime in overhead.sourcePhaseSeconds[2]..overhead.sourcePhaseSeconds[3])
        assertTrue(incoming.displacement.z > 0.0)
        assertTrue(incoming.displacement.dot(head - incoming.axisPoint) > 0.0)
    }

    @Test fun highGuardAdviceDistinguishesReachFromPointingAcrossTheBrowInStageSpace() {
        for (transform in listOf<(Vector3) -> Vector3>({ it }, { Vector3(2.0 - it.z, it.y + .35, it.x - 4.0) })) {
            fun needsCorrection(grip: WeaponGrip, tip: Vector3) = lessonHighGuardOverextended(
                transform(head), transform(enemy), transform(grip.position), transform(tip),
            )
            assertTrue(needsCorrection(forwardGuard, playerBladeAxis(forwardGuard).tip))
            assertFalse(needsCorrection(closeGuard, playerBladeAxis(closeGuard).tip))
            assertFalse(needsCorrection(forwardGuard, forwardGuard.position + Vector3(-.85, 0.0, 0.0)))
        }
    }

    private data class Witness(val sourceTime: Double, val axisPoint: Vector3, val displacement: Vector3)

    private fun firstContact(grip: WeaponGrip): Witness {
        fun blade(pose: AttackPoseSample) = BladeSegment(pose.bladeBase, pose.bladeTip, .0125)
        val frames = overhead.samples.map { it.inStage(enemy, 0f) }
        val initial = blade(frames.first())
        assertNull(firstRigidBladeContact(grip, grip, BladeSweep(initial, initial)))
        for ((previous, next) in frames.zipWithNext()) {
            val hit = firstRigidBladeContact(grip, grip, BladeSweep(blade(previous), blade(next))) ?: continue
            val along = hit.enemyAxisFraction
            val start = previous.bladeBase * (1 - along) + previous.bladeTip * along
            val end = next.bladeBase * (1 - along) + next.bladeTip * along
            return Witness(previous.sourceSeconds + hit.fraction * (next.sourceSeconds - previous.sourceSeconds),
                start + (end - start) * hit.fraction, end - start)
        }
        error("The overhead attack never touched the stationary player blade")
    }
}
