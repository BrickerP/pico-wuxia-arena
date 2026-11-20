package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.BladeSegment
import com.example.wuxiaarena.core.combat.BladeSweep
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.firstBladeContact
import com.example.wuxiaarena.core.combat.firstRigidBladeContact
import com.example.wuxiaarena.core.combat.playerBladeAxis
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class IndigoSideGuardTest {
    private val head = Vector3(0.0, 1.6949999332427979, 0.0)
    private val enemy = Vector3(0.0, .028, -1.348750234017417)
    private val leftRotation = Quaternion(.3129054252775328, .12636875883485926, -2.9802321862308304e-8, .9413400722493559)
    private val rightRotation = Quaternion(.30384564644079903, -.06476807646387507, -3.725290328421679e-8, .9505171852260964)
    private val body = listOf(BladeSegment(head, head, .16), BladeSegment(head + Vector3(0.0,-1.05,0.0), head + Vector3(0.0,-.23,0.0), .24))

    @Test fun theRecordedHighLeftGuardLeavesTheRibsExposedDuringTheIncomingStrike() {
        val grip = WeaponGrip(Vector3(-.13199985027313232, 1.524999976158142, -.2999997138977051), leftRotation)
        val axis = playerBladeAxis(grip)
        assertFalse(indigoGuardCoversRibs(AttackDirection.LEFT, head, enemy, axis.base, axis.tip))
        val contact = trace(AttackDirection.LEFT, grip, .90, .99)
        assertNull(contact.steel)
        assertEquals(.9895093, requireNotNull(contact.body), .0001)
    }

    @Test fun eitherRibGuardCanCatchTheCorrespondingCommittedCutBeforeItReachesTheBody() {
        for ((direction, grip) in listOf(
            AttackDirection.LEFT to WeaponGrip(Vector3(-.32, 1.20, -.24), leftRotation),
            AttackDirection.RIGHT to WeaponGrip(Vector3(.30, 1.14, -.02), rightRotation),
        )) {
            val axis = playerBladeAxis(grip)
            assertTrue(indigoGuardCoversRibs(direction, head, enemy, axis.base, axis.tip))
            val contact = trace(direction, grip, 0.0, 1.10)
            val steelTime = requireNotNull(contact.steel)
            assertTrue(steelTime in .90..1.10)
            assertTrue(contact.closingOnGuard)
            assertTrue(steelTime + .04 < requireNotNull(contact.body))
        }
    }

    private data class Contacts(val steel: Double?, val body: Double?, val closingOnGuard: Boolean)

    private fun trace(direction: AttackDirection, grip: WeaponGrip, start: Double, end: Double): Contacts {
        val profile = arenaOpponents[1].attackProfile(direction)
        val times = (listOf(start, end, profile.sourcePhaseSeconds[2]) + profile.samples.map { it.sourceSeconds })
            .filter { it in start..end }.distinct().sorted()
        var firstSteel: Double? = null
        var firstBody: Double? = null
        var closes = false
        fun blade(pose: AttackPoseSample) = BladeSegment(pose.bladeBase, pose.bladeTip, .0125)
        for ((from, to) in times.zipWithNext()) {
            val a = profile.sample(from).inStage(enemy, 0f)
            val b = profile.sample(to).inStage(enemy, 0f)
            val sweep = BladeSweep(blade(a), blade(b))
            if (firstSteel == null) firstRigidBladeContact(grip, grip, sweep)?.let { hit ->
                firstSteel = from + hit.fraction * (to - from)
                closes = startupBladeClosesOnGuard(a, b, hit)
            }
            if (firstBody == null && from >= profile.sourcePhaseSeconds[2]) {
                firstBody = body.mapNotNull { firstBladeContact(sweep, BladeSweep(it, it))?.fraction }
                    .minOrNull()?.let { from + it * (to - from) }
            }
        }
        return Contacts(firstSteel, firstBody, closes)
    }
}
