package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.abs

/** Contract clocks use the real enum durations; no body/profile fixture decides those durations. */
class AttackPhaseClockTest {
    private val phases = listOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE, EnemyPhase.RECOVERING)
    private val sideTimes = listOf(0.0, 0.65, 0.9, 1.1, 1.75)
    private val overheadTimes = listOf(0.0, 0.65, 5.0 / 6.0, 31.0 / 30.0, 1.75)

    private fun durations(direction: AttackDirection) = listOf(direction.preparationNanos,
        direction.startupNanos, direction.activeNanos, direction.recoveryNanos)

    private fun profile(direction: AttackDirection, cue: Double = 1.0): AttackProfile {
        fun sample(time: Double) = AttackPoseSample(time,
            EnemyContactPose(Vector3(time, 1.6, 0.0), Vector3(time, .55, 0.0), Vector3(time, 1.4, 0.0)),
            Vector3(time, 1.0, .2), Vector3(time, 1.5, 1.0))
        return AttackProfile("attack_${direction.name.lowercase()}",
            if (direction == AttackDirection.OVERHEAD) overheadTimes else sideTimes,
            cue, listOf(sample(0.0), sample(1.75)))
    }

    @Test
    fun eachDirectionUsesItsOwnLinearPhaseEndpointsAndActualEnumDurations() {
        for (direction in AttackDirection.entries) {
            val profile = profile(direction)
            val source = if (direction == AttackDirection.OVERHEAD) overheadTimes else sideTimes
            for ((index, duration) in durations(direction).withIndex()) {
                assertEquals(source[index], profile.sourceSeconds(phases[index], 0L, duration), 0.0)
                assertEquals(source[index + 1], profile.sourceSeconds(phases[index], duration, 0L), 0.0)
                val elapsed = duration / 3L
                val expected = source[index] + (source[index + 1] - source[index]) * elapsed.toDouble() / duration
                assertEquals(expected, profile.sourceSeconds(phases[index], elapsed, duration - elapsed), 1e-12)
            }
        }
    }

    @Test
    fun overheadSourceTracksItsWhole1750msRuntimeWithinOneNanosecond() {
        val direction = AttackDirection.OVERHEAD
        val profile = profile(direction)
        var accumulated = 0L
        for ((index, duration) in durations(direction).withIndex()) {
            for (elapsed in listOf(0L, 1L, duration / 3L, duration / 2L, duration - 1L, duration)) {
                val sourceNanos = profile.sourceSeconds(phases[index], elapsed, duration - elapsed) * 1_000_000_000.0
                assertTrue("$index/$elapsed: source clock must stay within 1ns of runtime",
                    abs(sourceNanos - (accumulated + elapsed).toDouble()) <= 1.0)
            }
            accumulated += duration
        }
        assertEquals(1_750_000_000L, accumulated)
    }

    @Test
    fun sideAttacksKeepTheirExistingDurationsAndSourceMapping() {
        for (direction in listOf(AttackDirection.LEFT, AttackDirection.RIGHT)) {
            assertEquals(listOf(550_000_000L, 180_000_000L, 200_000_000L, 600_000_000L), durations(direction))
            val profile = profile(direction)
            assertEquals(.95, profile.sourceSeconds(EnemyPhase.ACTIVE, 50_000_000L, 150_000_000L), 1e-12)
            assertEquals(1.0, profile.sourceSeconds(EnemyPhase.ACTIVE, 100_000_000L, 100_000_000L), 1e-12)
            assertEquals(1.05, profile.sourceSeconds(EnemyPhase.ACTIVE, 150_000_000L, 50_000_000L), 1e-12)
        }
    }

    @Test
    fun changingOnlyTheCueCannotBendAnyPhaseOrMoveTheActiveMidpoint() {
        for (direction in AttackDirection.entries) {
            val earlier = profile(direction, .95)
            val later = profile(direction, 1.02)
            for ((index, duration) in durations(direction).withIndex()) {
                for (elapsed in listOf(0L, duration / 4L, duration / 2L, duration * 3L / 4L, duration)) {
                    assertEquals(earlier.sourceSeconds(phases[index], elapsed, duration - elapsed),
                        later.sourceSeconds(phases[index], elapsed, duration - elapsed), 0.0)
                }
            }
            if (direction == AttackDirection.OVERHEAD) {
                val midpoint = earlier.sourceSeconds(EnemyPhase.ACTIVE, direction.activeNanos / 2L, direction.activeNanos / 2L)
                assertEquals(14.0 / 15.0, midpoint, 1e-12)
                assertNotEquals(earlier.contactSourceSeconds, midpoint)
                assertNotEquals(later.contactSourceSeconds, midpoint)
            }
        }
    }

    @Test
    fun actualContactRecoveryStartsAtItsToiAndIgnoresBothPossibleCues() {
        val direction = AttackDirection.OVERHEAD
        val atContact = .946713
        val earlier = recoveredSources(profile(direction, .95), direction, atContact)
        val later = recoveredSources(profile(direction, 1.02), direction, atContact)
        assertEquals(earlier, later)
        assertEquals(atContact, earlier.first(), 0.0)
        assertTrue(earlier[2] < atContact)
        assertEquals(1.75, earlier.last(), 0.0)
    }

    @Test
    fun clearingRealRecoveryForNewGeometrySelectsThePhaseBoundaryWithoutAStaleCueFlag() {
        val session = ArenaSession(logMessage = {})
        val combat = EnemyCombatStateMachine().also {
            it.advanceBy(800_000_000L, true)
            it.tryStartAttack(AttackDirection.OVERHEAD, true)
            it.advanceBy(AttackDirection.OVERHEAD.preparationNanos + AttackDirection.OVERHEAD.startupNanos, true)
            it.resolveActiveAttack(requireNotNull(it.currentAttackId), AttackOutcome.BLOCKED)
        }
        field(session, "combat", combat)
        installRecovery(session, profile(AttackDirection.OVERHEAD, 1.02), AttackDirection.OVERHEAD, .946713)
        assertEquals(.946713, session.viewState.enemyPoseSourceSeconds)
        session.setEnemyGeometry(Vector3(0.0, 0.0, -1.3), 1.55)
        val normal = arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD)
        assertEquals(normal.sourcePhaseSeconds[3], session.viewState.enemyPoseSourceSeconds)
        assertNotEquals(normal.contactSourceSeconds, session.viewState.enemyPoseSourceSeconds)
    }

    private fun recoveredSources(profile: AttackProfile, direction: AttackDirection, source: Double): List<Double> {
        val session = ArenaSession(logMessage = {})
        installRecovery(session, profile, direction, source)
        val select = ArenaSession::class.java.getDeclaredMethod("effectiveEnemyPose", java.lang.Long.TYPE)
            .apply { isAccessible = true }
        return listOf(0L, 35_000_000L, 70_000_000L, 140_000_000L, direction.recoveryNanos).map {
            (select.invoke(session, it) as EnemyPoseFrame).pose.sourceSeconds
        }
    }

    private fun installRecovery(session: ArenaSession, profile: AttackProfile, direction: AttackDirection, source: Double) {
        val type = ArenaSession::class.java.declaredClasses.single { it.simpleName == "ContactRecovery" }
        val constructor = type.declaredConstructors.single { it.parameterCount == 4 }.apply { isAccessible = true }
        field(session, "contactRecovery", constructor.newInstance(profile, direction, source, direction.recoveryNanos))
    }

    private fun field(session: ArenaSession, name: String, value: Any) {
        ArenaSession::class.java.getDeclaredField(name).apply { isAccessible = true }.set(session, value)
    }
}
