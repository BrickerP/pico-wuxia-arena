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
        val player = playerBlade(grip)
        val midpoint = (player.base + player.tip) * 0.5
        val enemy = BladeSegment(midpoint + Vector3(0.0, -0.2, 0.0), midpoint + Vector3(0.0, 0.2, 0.0), 0.012)
        val contact = requireNotNull(firstBladeContact(BladeSweep(player, player), BladeSweep(enemy, enemy)))
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

        fun observe(now: Long, position: Vector3): PlayerMotionFrame {
            fun stamp() = ObservationStamp(sequence++, now, 1L, InputOrigin.PICO)
            assertTrue(tracking.accept(TrackingEvent.Head(stamp(),
                ObservedPose(Vector3(0.0, 1.6, 0.0), Quaternion(0.0, 0.0, 0.0, 1.0)))))
            assertTrue(tracking.accept(TrackingEvent.Controllers(stamp(), null, ObservedPose(position, rotation))))
            return requireNotNull(resolver.observe(tracking.snapshot, enemy))
        }
    }
}
