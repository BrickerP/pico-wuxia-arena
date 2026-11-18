package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.TrackingEvent
import com.example.wuxiaarena.core.input.TrackingState
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

class PlayerDefenseSnapshotTest {
    @Test fun aSettledGuardAllowsOneWristCutAndCannotArmTheNextReversal() {
        val fixture = Fixture()
        val grip = Vector3(-.22, 1.6, -.50)
        val start = fixture.observe(0L, grip)
        assertEquals(AttackDirection.OVERHEAD, start.guardDirection)
        for (time in listOf(60L, 120L, 180L)) fixture.observe(time * 1_000_000L, grip)
        fun yaw(radians: Double) = Quaternion(0.0, kotlin.math.sin(radians / 2), 0.0, kotlin.math.cos(radians / 2))
        val wristCut = fixture.observe(260_000_000L, grip, yaw(-.38))
        val first = requireNotNull(wristCut.swing)
        assertTrue(first.fromGuard)
        assertTrue(first.committedAt(requireNotNull(wristCut.weaponGrip)))
        fixture.observe(340_000_000L, grip, yaw(0.0))
        for (time in listOf(420L, 500L, 580L, 660L)) {
            assertNull(fixture.observe(time * 1_000_000L, grip, yaw(0.0)).guardDirection)
        }
        val reversal = fixture.observe(740_000_000L, grip, yaw(-.7))
        val next = requireNotNull(reversal.swing)
        assertTrue(next.id > first.id)
        assertEquals(false, next.fromGuard)
        assertEquals(false, next.committedAt(requireNotNull(reversal.weaponGrip)))
    }

    @Test
    fun laterQueuedGuardEntryCannotUpgradeAnEarlierStaticGuardToParry() {
        val fixture = Fixture()
        val guard = Vector3(-0.4, 1.6, -0.35)
        fixture.observe(1_000_000_000L, guard)
        fixture.resolver.beginEnemyAttack(1L)
        fixture.observe(1_100_000_000L, guard)
        fixture.observe(1_200_000_000L, guard)
        val earlier = fixture.observe(1_300_000_000L, guard)
        assertEquals(AttackDirection.OVERHEAD, earlier.guardDirection)
        assertEquals(1_000_000_000L, earlier.guardEnteredAtNanos)
        assertNull(earlier.fastGuardAtNanos)

        fixture.observe(1_350_000_000L, guard + Vector3(0.0, 0.0, 0.5))
        val future = fixture.observe(1_400_000_000L, guard)
        assertEquals(1_400_000_000L, future.guardEnteredAtNanos)
        assertEquals(1_400_000_000L, future.fastGuardAtNanos)

        // Replaying an earlier real contact after future observations must use that
        // earlier frame's immutable grading data, not the recognizer's newest guard.
        val grip = requireNotNull(earlier.weaponGrip)
        val player = playerBladeAxis(grip)
        val midpoint = (player.base + player.tip) * 0.5
        val enemy = BladeSegment(midpoint + Vector3(0.0, -0.2, 0.0), midpoint + Vector3(0.0, 0.2, 0.0), 0.012)
        val contact = requireNotNull(firstRigidBladeContact(grip, grip, BladeSweep(enemy, enemy)))
        fixture.resolver.constrainWeapon(earlier, grip, contact)
        assertEquals(AttackOutcome.BLOCKED, fixture.resolver.resolveDefense(1L, AttackDirection.OVERHEAD,
            fixture.enemy, earlier.receivedAtNanos, contact))
    }

    @Test
    fun qualifiedSwingExistsWithoutAnyOldStaticBodyContact() {
        val fixture = Fixture()
        fixture.observe(1_000_000_000L, Vector3(3.0, 1.2, 0.0))
        val swung = fixture.observe(1_100_000_000L, Vector3(3.3, 1.2, 0.0))
        assertNull(swung.strike)
        assertNotNull(swung.swing)
        assertTrue(requireNotNull(swung.swing).power >= 1.0)
        assertTrue(swung.bladeTipSpeed > 0.85)
    }

    private class Fixture {
        val resolver = PlayerCombatResolver()
        val enemy = Vector3(0.0, 0.0, -1.3)
        private val tracking = TrackingState(Hand.RIGHT)
        private var sequence = 0L
        private val rotation = Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5))

        fun observe(now: Long, position: Vector3, handRotation: Quaternion = rotation): PlayerMotionFrame {
            fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
            assertTrue(tracking.accept(TrackingEvent.Head(stamp(),
                ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0)))))
            assertTrue(tracking.accept(TrackingEvent.Controllers(stamp(), null, ObservedPose(position, handRotation))))
            return requireNotNull(resolver.observe(tracking.snapshot, enemy))
        }
    }
}
