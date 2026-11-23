package com.example.wuxiaarena.p0d2f0182.content

import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.input.TrackingQuality
import com.example.wuxiaarena.core.math.Vector3
import com.example.wuxiaarena.p0d2f0182.runtime.ArenaSession
import com.example.wuxiaarena.p0d2f0182.runtime.TrialResult
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DefeatRetreatTest {
    private val head = Vector3(0.0, 1.695, 0.0)
    private val loss = ArenaSession(logMessage = {}).viewState.copy(
        roundGeneration = 3L, result = TrialResult.DEFEAT, playerHeadPosition = head,
        enemyPosition = Vector3(0.0, 0.1, -1.20), enemyRecoilOffset = Vector3(0.0, 0.0, -0.10),
    )
    private val retreat = DefeatRetreat()

    @Test
    fun startsAtTheVisibleRecoilPoseAndEasesToAStationaryBreathingDistance() {
        val start = requireNotNull(retreat.update(loss, 0))
        assertEquals(Vector3(0.0, 0.1, -1.30), start.position)
        assertFalse(start.moving)
        var last = start
        val steps = ArrayList<Double>()
        for (tick in 1..120) {
            val current = requireNotNull(retreat.update(loss, tick * 20_000_000L))
            val displacement = last.position.z - current.position.z
            steps += displacement
            assertTrue(displacement in 0.0..0.018)
            assertEquals(last.position.y, current.position.y, 0.0)
            assertEquals(start.position.distanceTo(current.position), current.distanceMeters, 1e-12)
            last = current
        }
        assertTrue(steps.first() < steps.max() / 10)
        assertTrue(steps.last { it > 0.0 } < steps.max() / 10)
        assertEquals(-2.4, last.position.z, 1e-12)
        assertFalse(last.moving)
        val lean = loss.copy(playerHeadPosition = Vector3(0.6, 1.5, -0.3))
        val idle = requireNotNull(retreat.update(lean, 2_480_000_000))
        assertEquals(last.position, idle.position)
        assertTrue(idle.elapsedNanos > last.elapsedNanos)
    }

    @Test
    fun headMovementDoesNotTurnTheCapturedPathOrAllowAPlayerToBeWalkedThrough() {
        retreat.update(loss, 0)
        val lean = loss.copy(playerHeadPosition = Vector3(0.3, 1.62, 0.0))
        val stepping = requireNotNull(retreat.update(lean, 80_000_000))
        assertTrue(stepping.moving)
        assertEquals(0.0, stepping.position.x, 0.0)
        val obstructed = loss.copy(playerHeadPosition = stepping.position.copy(y = head.y, z = stepping.position.z - 0.02))
        val stopped = requireNotNull(retreat.update(obstructed, 160_000_000))
        assertEquals(stepping.position, stopped.position)
        assertFalse(stopped.moving)
        assertEquals(stopped.position, retreat.update(loss, 240_000_000)?.position)
    }

    @Test
    fun missingTrackingAndLongFramesDoNotTeleportTheCharacter() {
        assertNull(retreat.update(loss.copy(playerHeadPosition = null), 0))
        retreat.update(loss, 80_000_000)
        val current = requireNotNull(retreat.update(loss, 160_000_000))
        val unavailable = loss.copy(headQuality = TrackingQuality.SOURCE_REPORTED_INVALID)
        assertEquals(current, retreat.update(unavailable, 41_000_000_000))
        val restored = requireNotNull(retreat.update(loss, 51_000_000_000))
        assertTrue(current.position.distanceTo(restored.position) <= 0.9 * 0.08)
        assertEquals(restored, retreat.update(loss, 50_000_000_000))
    }

    @Test
    fun victoryAndInstantRetryLeaveCombatUntouchedAndAFreshLossStartsAtItsOwnPose() {
        retreat.update(loss, 0)
        retreat.update(loss, 80_000_000)
        for (result in TrialResult.entries.filter { it != TrialResult.DEFEAT }) {
            assertNull(retreat.update(loss.copy(result = result), 100_000_000))
        }
        assertNull(retreat.update(loss.copy(phase = EnemyPhase.DEAD), 110_000_000))
        val far = loss.copy(roundGeneration = 4, enemyPosition = Vector3(1.0, 0.2, -3.0))
        val reset = requireNotNull(retreat.update(far, 400_000_000))
        assertEquals(requireNotNull(far.enemyPosition) + far.enemyRecoilOffset, reset.position)
        assertEquals(0L, reset.elapsedNanos)
        assertEquals(reset.position, retreat.update(far, 480_000_000)?.position)
        assertFalse(requireNotNull(retreat.update(far, 560_000_000)).moving)
        assertEquals(0L, retreat.update(loss.copy(roundGeneration = 5), 600_000_000)?.elapsedNanos)
    }
}
