package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitReaction
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Test

class EnemyPoseSelectionTest {
    private fun sample(time: Double, offset: Double) = AttackPoseSample(time,
        EnemyContactPose(Vector3(offset, 1.6, 0.0), Vector3(offset, 0.55, 0.0), Vector3(offset, 1.4, 0.0)),
        Vector3(offset + 0.2, 1.0, 0.3), Vector3(offset + 0.3, 1.3, 1.0))

    private val attack = AttackProfile("attack_left", listOf(0.0, 0.65, 0.90, 1.10, 1.75), 1.0,
        listOf(sample(0.0, 10.0), sample(1.75, 11.75)))
    private val locomotion = LocomotionProfile(
        PoseClipProfile("idle", listOf(sample(0.0, 1.0), sample(1.5, 1.0))),
        PoseClipProfile("walk", listOf(sample(0.0, 2.0), sample(1.0 / 3.0, 2.0), sample(0.9, 3.5), sample(1.5, 2.0))),
        1.0 / 3.0, 1.5, 1.45,
        (0..5).map { GaitStepEvent(it / 6.0,
            if (it % 2 == 0) EnemyFoot.LEFT else EnemyFoot.RIGHT,
            if (it % 2 == 0) EnemyFoot.RIGHT else EnemyFoot.LEFT) },
    )

    private val reactions = ReactionProfiles(
        body = PoseClipProfile("hit_body", listOf(sample(0.0, 20.0), sample(2.0, 22.0))),
        head = PoseClipProfile("hit_head", listOf(sample(0.0, 30.0), sample(2.0, 32.0))),
        side = PoseClipProfile("hit_side", listOf(sample(0.0, 40.0), sample(2.0, 42.0))),
    )

    @Test
    fun staticIdleSelectsItsActualClipAndPoseInsteadOfAttackStartOrStandingConstants() {
        val frame = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.IDLE, 0L, null,
            guarding = false, moving = false, gaitMeters = 0.0))
        assertEquals("idle", frame.clip)
        assertEquals(locomotion.idle.sample(0.0), frame.pose)
        assertNotEquals(attack.sample(0.0).contact, frame.pose.contact)
        assertNotEquals(EnemyContactPose.standing(Vector3(0.0, 0.0, 0.0)), frame.pose.contact)
    }

    @Test
    fun movingIdleUsesTheSameSignedGaitClockForItsClipBodyAndBlade() {
        for (gait in listOf(0.0, 1.45 / 4.0, -1.45 / 4.0, 1.45, -1.45, 10.0)) {
            val frame = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.IDLE, 777L, null,
                guarding = false, moving = true, gaitMeters = gait))
            assertEquals("walk", frame.clip)
            assertEquals(locomotion.sourceSeconds(true, gait), frame.pose.sourceSeconds, 0.0)
            assertEquals(locomotion.sample(true, gait), frame.pose)
        }
    }

    @Test
    fun changingPhaseElapsedWithoutGaitTravelCannotAdvanceWalkingProxies() {
        val first = selectEnemyPose(attack, locomotion, reactions, EnemyPhase.IDLE, 0L, null, false, true, 0.4)
        val later = selectEnemyPose(attack, locomotion, reactions, EnemyPhase.IDLE, Long.MAX_VALUE, null, false, true, 0.4)
        assertEquals(first, later)
    }

    @Test
    fun guardedHitUsesCanonicalIdleEvenIfThePreviousMovementFlagIsStillSet() {
        val frame = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.HIT, 200L, 100L,
            guarding = true, moving = true, gaitMeters = -0.5))
        assertEquals("idle", frame.clip)
        assertEquals(locomotion.idle.sample(0.0), frame.pose)
    }

    @Test
    fun attacksKeepTheirActualMidpointAndSuccessfulRecoveryClock() {
        val contact = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.ACTIVE,
            100_000_000L, 100_000_000L, false, false, 0.4))
        val recovery = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.RECOVERING,
            0L, 600_000_000L, false, true, 0.9, recoveryFromContact = true))
        assertEquals("attack_left", contact.clip)
        assertEquals(1.0, contact.pose.sourceSeconds, 0.0)
        assertEquals(contact.pose, recovery.pose)
    }

    @Test
    fun oneStageTransformMovesBothBodyAndBladeByTheSameOriginYawAndRecoil() {
        val frame = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.IDLE, 0L, null, false, true, 0.4))
        val base = Vector3(0.0, 0.028, -1.3)
        val recoil = Vector3(-0.03, 0.0, -0.04)
        val nominal = frame.pose.inStage(base, 0.7f)
        val actual = frame.pose.inStage(base + recoil, 0.7f)
        assertTrue((actual.contact.head - nominal.contact.head).distanceTo(recoil) < 1e-12)
        assertTrue((actual.bladeBase - nominal.bladeBase).distanceTo(recoil) < 1e-12)
        assertTrue((actual.bladeTip - nominal.bladeTip).distanceTo(recoil) < 1e-12)
        assertEquals(frame.pose.contact.head.y + 0.028, actual.contact.head.y, 1e-12)
    }

    @Test
    fun allThreeHurtKindsSelectTheSameSourceClipAndTimeForBodyAndBlade() {
        for ((reaction, zone, profile) in listOf(
            Triple(HitReaction.PLAYER_HIT, HitZone.BODY, reactions.body),
            Triple(HitReaction.PLAYER_HIT, HitZone.HEAD, reactions.head),
            Triple(HitReaction.PARRIED, HitZone.HEAD, reactions.side),
        )) {
            val duration = if (reaction == HitReaction.PARRIED) 550_000_000L else 300_000_000L
            val end = if (reaction == HitReaction.PARRIED) 1.18 else .72
            for (elapsed in listOf(0L, duration / 2, duration)) {
                val frame = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.HIT,
                    elapsed, duration - elapsed, false, true, .4, hitReaction = reaction, hitZone = zone))
                val time = .05 + (end - .05) * elapsed.toDouble() / duration
                assertEquals(profile.clip, frame.clip)
                assertEquals(time, frame.pose.sourceSeconds, 1e-12)
                assertEquals(profile.sample(time).contact, frame.pose.contact)
                assertEquals(profile.sample(time).bladeTip, frame.pose.bladeTip)
                assertNotEquals(EnemyContactPose.standing(Vector3(0.0, 0.0, 0.0)), frame.pose.contact)
            }
        }
    }

    @Test
    fun guardedHitDoesNotBorrowBodyHeadOrParryMotion() {
        val frame = requireNotNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.HIT,
            200_000_000L, 100_000_000L, true, true, .4,
            hitReaction = HitReaction.PARRIED, hitZone = HitZone.HEAD))
        assertEquals("idle", frame.clip)
        assertEquals(locomotion.idle.sample(0.0), frame.pose)
    }

    @Test
    fun malformedHurtCoverageAndNegativeClocksFailWithoutAStandingFallback() {
        assertThrows(IllegalArgumentException::class.java) {
            ReactionProfiles(reactions.body, reactions.head,
                PoseClipProfile("hit_side", listOf(sample(.1, 40.0), sample(1.0, 41.0))))
        }
        assertThrows(IllegalArgumentException::class.java) {
            reactions.frame(HitReaction.PLAYER_HIT, HitZone.BODY, -1L, 300_000_000L)
        }
        assertEquals(.385, reactions.frame(HitReaction.PLAYER_HIT, HitZone.BODY,
            Long.MAX_VALUE, Long.MAX_VALUE).pose.sourceSeconds, 1e-12)
        assertNull(selectEnemyPose(attack, locomotion, reactions, EnemyPhase.DEAD, 0L, null, false, false, 0.0))
    }
}
