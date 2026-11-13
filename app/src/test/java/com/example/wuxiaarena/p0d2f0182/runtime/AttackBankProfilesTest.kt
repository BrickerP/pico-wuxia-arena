package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class AttackBankProfilesTest {
    private val assets = listOf("base", "indigo", "veteran").map { "asset://models/opponents/$it.glb" }
    private val phaseTimes = listOf(0.0, 0.65, 0.90, 1.10, 1.75)
    private val phases = listOf(EnemyPhase.PREPARING, EnemyPhase.STARTUP, EnemyPhase.ACTIVE, EnemyPhase.RECOVERING)

    private fun ms(value: Long) = value * 1_000_000L

    private fun pose(time: Double, offset: Double = 0.0) = AttackPoseSample(
        time,
        EnemyContactPose(
            Vector3(1.0 + offset, 2.0, 3.0),
            Vector3(4.0 + offset, 5.0, 6.0),
            Vector3(7.0 + offset, 8.0, 9.0),
        ),
        Vector3(10.0 + offset, 11.0, 12.0),
        Vector3(13.0 + offset, 14.0, 15.0),
    )

    private fun profile(
        clip: String = "attack_overhead",
        times: List<Double> = phaseTimes,
        contact: Double = 1.0,
        samples: List<AttackPoseSample> = listOf(pose(0.0), pose(1.75, 7.0)),
    ) = AttackProfile(clip, times, contact, samples)

    @Test
    fun generatedDataMatchesThePublishedCanonicalBankIdentity() {
        assertEquals("365578d497f3a592e08cbe158f90777fe326211f8d9593bab85ff807c0ac07ac", AttackBankProfileData.bindingSha256)
        assertEquals("6ca12659ef6705b2fba43ace092fb8eb567df090c55849b87869e79a9031df24", AttackBankProfileData.characters.getValue("asset://models/opponents/base.glb").modelSha256)
        assertEquals("c21a05e697ec1a9aba8fc45d5099d148ad61737059efe8c5e4118afa3eaddeff", AttackBankProfileData.characters.getValue("asset://models/opponents/base.glb").profileSha256)
        assertEquals("27782bbe11bfff327d4635a1c5276053dda012c12bf2911047fbe880653121df", AttackBankProfileData.characters.getValue("asset://models/opponents/indigo.glb").modelSha256)
        assertEquals("d73ad19f7ac1504c0fb51e9696c14def6e320ebdae1bf9f76723be2f7edf8651", AttackBankProfileData.characters.getValue("asset://models/opponents/indigo.glb").profileSha256)
        assertEquals("6d4211c8ed07dffb3f683748688120c581e2ee82b12559941b68a6d7170fcee2", AttackBankProfileData.characters.getValue("asset://models/opponents/veteran.glb").modelSha256)
        assertEquals("dcdc496c877f2643e745e4c20d6b05cec3374ac3a7c0d04dc9a38c21f7024d20", AttackBankProfileData.characters.getValue("asset://models/opponents/veteran.glb").profileSha256)
    }

    @Test
    fun allActorsUsePlayerViewDirectionClipsAndCompleteSourceSamples() {
        val clips = mapOf(
            AttackDirection.LEFT to "attack_left",
            AttackDirection.RIGHT to "attack_right",
            AttackDirection.OVERHEAD to "attack_overhead",
        )
        assertEquals(assets.toSet(), AttackBankProfileData.characters.keys)
        for (asset in assets) {
            val character = AttackBankProfileData.characters.getValue(asset)
            assertTrue(character.modelSha256.matches(Regex("[0-9a-f]{64}")))
            assertTrue(character.profileSha256.matches(Regex("[0-9a-f]{64}")))
            assertEquals(AttackDirection.entries.toSet(), character.attacks.keys)
            for ((direction, clip) in clips) {
                val profile = AttackBankProfiles.forAsset(asset, direction)
                assertSame(character.attacks.getValue(direction), profile)
                assertEquals(clip, profile.clip)
                assertEquals(phaseTimes, profile.sourcePhaseSeconds)
                assertEquals(if (direction == AttackDirection.OVERHEAD) 211 else 106, profile.samples.size)
                assertEquals(0.0, profile.samples.first().sourceSeconds, 0.0)
                assertEquals(1.75, profile.samples.last().sourceSeconds, 0.0)
                assertTrue(profile.samples.zipWithNext().all { (before, after) -> before.sourceSeconds < after.sourceSeconds })
                assertTrue(profile.samples.all { it.contact.isFinite() && it.bladeBase.isFinite() && it.bladeTip.isFinite() })
            }
        }
    }

    @Test
    fun everyActorDirectionMapsPhaseBoundariesAndContactAtTheActualActiveMidpoint() {
        for (asset in assets) for (direction in AttackDirection.entries) {
            val profile = AttackBankProfiles.forAsset(asset, direction)
            val durations = listOf(direction.preparationNanos, direction.startupNanos, direction.activeNanos, direction.recoveryNanos)
            for ((index, phase) in phases.withIndex()) {
                val duration = durations[index]
                assertEquals(phaseTimes[index], profile.sourceSeconds(phase, 0L, duration), 0.0)
                assertEquals(phaseTimes[index + 1], profile.sourceSeconds(phase, duration, 0L), 0.0)
            }
            assertEquals(1.0, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(100), ms(100)), 0.0)
            assertEquals(profile.contactSourceSeconds, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(100), ms(100)), 0.0)
            assertEquals(0.95, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(50), ms(150)), 1e-12)
            assertEquals(1.05, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(150), ms(50)), 1e-12)
            val contact = profile.samples.single { it.sourceSeconds == profile.contactSourceSeconds }
            assertSame(contact, profile.sample(profile.sourceSeconds(EnemyPhase.ACTIVE, ms(100), ms(100))))
        }
    }

    @Test
    fun asymmetricActiveSourceTimingStillContactsExactlyAtTheGameMidpoint() {
        val profile = profile(contact = 0.97)
        assertEquals(0.97, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(100), ms(100)), 0.0)
        assertEquals(0.935, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(50), ms(150)), 1e-12)
        assertEquals(1.035, profile.sourceSeconds(EnemyPhase.ACTIVE, ms(150), ms(50)), 1e-12)
    }

    @Test
    fun idleHitAndDeadSelectTheSameStartPoseUsedForGuardAcrossAllActorsAndDirections() {
        for (asset in assets) for (direction in AttackDirection.entries) {
            val profile = AttackBankProfiles.forAsset(asset, direction)
            for (phase in listOf(EnemyPhase.IDLE, EnemyPhase.HIT, EnemyPhase.DEAD)) {
                val seconds = profile.sourceSeconds(phase, ms(700), null)
                assertEquals(0.0, seconds, 0.0)
                assertSame(profile.samples.first(), profile.sample(seconds))
            }
            assertSame(profile.samples.first(), profile.sample(-100.0))
            assertSame(profile.samples.last(), profile.sample(100.0))
        }
    }

    @Test
    fun interpolationUsesOneTimeForAllBodyAndBladePoints() {
        val profile = profile()
        val sample = profile.sample(0.875)
        val expected = pose(0.875, 3.5)
        assertEquals(expected, sample)
        assertSame(profile.samples.first(), profile.sample(0.0))
        assertSame(profile.samples.last(), profile.sample(1.75))
    }

    @Test
    fun stageYawAndRootTranslationAreSharedByBodyAndBlade() {
        val local = pose(1.0)
        val origin = Vector3(0.35, 0.028, -1.50)
        val stage = local.inStage(origin, (Math.PI / 2.0).toFloat())
        val localPoints = listOf(local.contact.head, local.contact.bodyBottom, local.contact.bodyTop, local.bladeBase, local.bladeTip)
        val stagePoints = listOf(stage.contact.head, stage.contact.bodyBottom, stage.contact.bodyTop, stage.bladeBase, stage.bladeTip)
        for ((point, transformed) in localPoints.zip(stagePoints)) {
            assertPoint(Vector3(origin.x + point.z, origin.y + point.y, origin.z - point.x), transformed, 1e-6)
        }
        assertEquals(local.sourceSeconds, stage.sourceSeconds, 0.0)
        val recoil = Vector3(-0.04, 0.0, -0.16)
        val recoiled = local.inStage(origin + recoil, (Math.PI / 2.0).toFloat())
        assertPoint(stage.contact.head + recoil, recoiled.contact.head)
        assertPoint(stage.contact.bodyBottom + recoil, recoiled.contact.bodyBottom)
        assertPoint(stage.contact.bodyTop + recoil, recoiled.contact.bodyTop)
        assertPoint(stage.bladeBase + recoil, recoiled.bladeBase)
        assertPoint(stage.bladeTip + recoil, recoiled.bladeTip)
    }

    @Test
    fun generatedContactPosesStayInTheSameStageFrameForAllActorsAndDirections() {
        val origin = Vector3(-0.4, 0.028, -1.5)
        for (asset in assets) for (direction in AttackDirection.entries) {
            val profile = AttackBankProfiles.forAsset(asset, direction)
            val local = profile.sample(profile.contactSourceSeconds)
            val stage = local.inStage(origin, 0.0f)
            assertEquals(local.contact.translated(origin), stage.contact)
            assertEquals(local.bladeBase + origin, stage.bladeBase)
            assertEquals(local.bladeTip + origin, stage.bladeTip)
        }
    }

    @Test
    fun invalidPhaseAndSampleTimesAreRejectedAtConstruction() {
        assertThrows(IllegalArgumentException::class.java) { profile(clip = " ") }
        assertThrows(IllegalArgumentException::class.java) { profile(times = emptyList()) }
        assertThrows(IllegalArgumentException::class.java) { profile(times = listOf(0.0, 0.65, 0.9, 1.1)) }
        assertThrows(IllegalArgumentException::class.java) { profile(times = listOf(0.0, 0.65, 0.65, 1.1, 1.75)) }
        assertThrows(IllegalArgumentException::class.java) { profile(times = listOf(0.0, 0.9, 0.65, 1.1, 1.75)) }
        assertThrows(IllegalArgumentException::class.java) { profile(times = listOf(-0.1, 0.65, 0.9, 1.1, 1.75)) }
        for (invalid in listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY)) {
            assertThrows(IllegalArgumentException::class.java) { profile(times = listOf(0.0, 0.65, invalid, 1.1, 1.75)) }
            assertThrows(IllegalArgumentException::class.java) { profile(contact = invalid) }
            assertThrows(IllegalArgumentException::class.java) { pose(invalid) }
        }
        for (contact in listOf(0.89, 0.9, 1.1, 1.11)) {
            assertThrows(IllegalArgumentException::class.java) { profile(contact = contact) }
        }
        assertThrows(IllegalArgumentException::class.java) { pose(-0.1) }
        assertThrows(IllegalArgumentException::class.java) { profile(samples = emptyList()) }
        assertThrows(IllegalArgumentException::class.java) { profile(samples = listOf(pose(0.0))) }
        assertThrows(IllegalArgumentException::class.java) { profile(samples = listOf(pose(0.0), pose(0.0))) }
        assertThrows(IllegalArgumentException::class.java) { profile(samples = listOf(pose(1.75), pose(0.0))) }
        assertThrows(IllegalArgumentException::class.java) { profile(samples = listOf(pose(0.1), pose(1.75))) }
        assertThrows(IllegalArgumentException::class.java) { profile(samples = listOf(pose(0.0), pose(1.7))) }
    }

    @Test
    fun nonFinitePointsTransformsAndRequestsAreRejected() {
        val local = pose(1.0)
        val profile = profile()
        for (invalid in listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY)) {
            val point = Vector3(invalid, 0.0, 0.0)
            assertThrows(IllegalArgumentException::class.java) { local.copy(bladeBase = point) }
            assertThrows(IllegalArgumentException::class.java) { local.copy(bladeTip = point) }
            assertThrows(IllegalArgumentException::class.java) { local.copy(contact = local.contact.copy(head = point)) }
            assertThrows(IllegalArgumentException::class.java) { local.copy(contact = local.contact.copy(bodyBottom = point)) }
            assertThrows(IllegalArgumentException::class.java) { local.copy(contact = local.contact.copy(bodyTop = point)) }
            assertThrows(IllegalArgumentException::class.java) { local.inStage(point, 0.0f) }
            assertThrows(IllegalArgumentException::class.java) { local.inStage(Vector3(0.0, 0.0, 0.0), invalid.toFloat()) }
            assertThrows(IllegalArgumentException::class.java) { profile.sample(invalid) }
        }
        assertThrows(IllegalArgumentException::class.java) { profile.sourceSeconds(EnemyPhase.ACTIVE, -1L, 0L) }
        assertThrows(IllegalArgumentException::class.java) { profile.sourceSeconds(EnemyPhase.ACTIVE, 0L, -1L) }
    }

    @Test
    fun emptyAndLongPhaseClocksHaveDefinedFiniteResultsAndInputCollectionsAreCopied() {
        val times = phaseTimes.toMutableList()
        val samples = mutableListOf(pose(0.0), pose(1.75))
        val profile = profile(times = times, samples = samples)
        times[2] = Double.NaN
        samples.clear()
        assertEquals(phaseTimes, profile.sourcePhaseSeconds)
        assertEquals(2, profile.samples.size)
        assertEquals(0.90, profile.sourceSeconds(EnemyPhase.ACTIVE, 0L, 0L), 0.0)
        assertEquals(0.90, profile.sourceSeconds(EnemyPhase.ACTIVE, 0L, null), 0.0)
        assertEquals(1.10, profile.sourceSeconds(EnemyPhase.ACTIVE, 1L, null), 0.0)
        assertEquals(1.0, profile.sourceSeconds(EnemyPhase.ACTIVE, Long.MAX_VALUE, Long.MAX_VALUE), 0.0)
        assertThrows(NoSuchElementException::class.java) { AttackBankProfiles.forAsset("asset://missing.glb", AttackDirection.LEFT) }
    }

    @Test
    fun successfulContactsContinueFromContactWhileMissesUseTheFullActiveExit() {
        for (asset in assets) for (direction in AttackDirection.entries) {
            val profile = AttackBankProfiles.forAsset(asset, direction)
            assertEquals(1.0, profile.sourceSeconds(EnemyPhase.RECOVERING, 0L, direction.recoveryNanos, true), 0.0)
            assertEquals(1.10, profile.sourceSeconds(EnemyPhase.RECOVERING, 0L, direction.recoveryNanos, false), 0.0)
            assertEquals(1.75, profile.sourceSeconds(EnemyPhase.RECOVERING, direction.recoveryNanos, 0L, true), 0.0)
            val origin = Vector3(0.15, 0.028, -1.3)
            val opponent = arenaOpponents.single { it.asset == asset }
            val recovered = requireNotNull(opponent.attackPose(EnemyPhase.RECOVERING, 0L, direction.recoveryNanos,
                origin, 0.5f, direction, guarding = false, recoveryFromContact = true, gaitMeters = 0.0))
            assertEquals(profile.sample(1.0).inStage(origin, 0.5f), recovered)
        }
    }

    @Test
    fun actualOpponentConsumersUseNewGuardAndThePlayerViewIncomingBladeDirection() {
        val origin = Vector3(0.0, 0.028, -1.3)
        for (opponent in arenaOpponents) for (direction in AttackDirection.entries) {
            val profile = opponent.attackProfile(direction)
            val guard = opponent.locomotionProfile().sample(false, 0.0).inStage(origin, 0.3f)
            assertEquals(guard.contact, opponent.contactPose(EnemyPhase.IDLE, 0L, null, origin, 0.3f, direction, false, gaitMeters = 0.0))
            assertEquals(guard.contact, opponent.contactPose(EnemyPhase.HIT, ms(200), ms(100), origin, 0.3f, direction, true, gaitMeters = 0.0))
            val walk = opponent.locomotionProfile().sample(true, 0.4).inStage(origin, 0.3f)
            assertEquals(walk.contact, opponent.contactPose(EnemyPhase.IDLE, 0L, null,
                origin, 0.3f, direction, false, moving = true, gaitMeters = 0.4))
            if (direction != AttackDirection.OVERHEAD) {
                val delta = profile.sample(1.1).bladeTip.x - profile.sample(0.9).bladeTip.x
                assertTrue(if (direction == AttackDirection.LEFT) delta > 0.0 else delta < 0.0)
            }
        }
    }

    @Test
    fun defenseFeedbackProjectsToTheRealEnemyBladeAndClampsToItsEndpoints() {
        val sample = pose(1.0)
        assertEquals(Vector3(11.0, 12.0, 13.0), sample.nearestBladePoint(Vector3(10.0, 14.0, 12.0)))
        assertEquals(sample.bladeBase, sample.nearestBladePoint(Vector3(0.0, 0.0, 0.0)))
        assertEquals(sample.bladeTip, sample.nearestBladePoint(Vector3(100.0, 100.0, 100.0)))
        val collapsed = sample.copy(bladeTip = sample.bladeBase)
        assertEquals(sample.bladeBase, collapsed.nearestBladePoint(Vector3(0.0, 0.0, 0.0)))
    }

    @Test
    fun finalLocomotionProfilesDriveActualIdleWalkAndAllProxyConsumers() {
        val origin = Vector3(0.2, 0.028, -1.3) + Vector3(-0.03, 0.0, -0.04)
        for (opponent in arenaOpponents) {
            val locomotion = opponent.locomotionProfile()
            assertEquals(185, locomotion.idle.samples.size)
            assertEquals(369, locomotion.walk.samples.size)
            assertEquals(6, locomotion.stepEvents.size)
            assertEquals(1.45, locomotion.strideMeters, 0.0)
            for (moving in listOf(false, true)) for (gait in listOf(-2.9, -0.4, 0.0, 0.4, 1.45, 2.9)) {
                val frame = requireNotNull(opponent.poseFrame(EnemyPhase.IDLE, 0L, null,
                    AttackDirection.OVERHEAD, false, moving, false, gait))
                val expected = locomotion.sample(moving, gait)
                assertEquals(if (moving) "walk" else "idle", frame.clip)
                assertEquals(expected, frame.pose)
                val actual = requireNotNull(opponent.attackPose(EnemyPhase.IDLE, 0L, null,
                    origin, 0.7f, AttackDirection.OVERHEAD, false, moving = moving, gaitMeters = gait))
                assertEquals(expected.inStage(origin, 0.7f), actual)
                assertEquals(actual.contact, opponent.contactPose(EnemyPhase.IDLE, 0L, null,
                    origin, 0.7f, AttackDirection.OVERHEAD, false, moving = moving, gaitMeters = gait))
            }
        }
    }

    @Test
    fun actualCanonicalIdleWalkAndAttackEntriesShareTheFinalCalibratedBodyAndBlade() {
        for (opponent in arenaOpponents) {
            val locomotion = opponent.locomotionProfile()
            val idle = locomotion.sample(false, 0.0)
            for (gait in listOf(-0.4, 0.0, 0.4, 1.45)) {
                val walk = locomotion.sample(true, gait)
                assertEquals(idle.contact, walk.contact)
                assertEquals(idle.bladeBase, walk.bladeBase)
                assertEquals(idle.bladeTip, walk.bladeTip)
            }
            for (direction in AttackDirection.entries) {
                val attack = opponent.attackProfile(direction).sample(0.0)
                assertPoint(idle.contact.head, attack.contact.head, 1e-6)
                assertPoint(idle.contact.bodyBottom, attack.contact.bodyBottom, 1e-6)
                assertPoint(idle.contact.bodyTop, attack.contact.bodyTop, 1e-6)
                assertPoint(idle.bladeBase, attack.bladeBase, 1e-6)
                assertPoint(idle.bladeTip, attack.bladeTip, 1e-6)
            }
        }
    }

    private fun assertPoint(expected: Vector3, actual: Vector3, tolerance: Double = 1e-12) {
        assertEquals(expected.x, actual.x, tolerance)
        assertEquals(expected.y, actual.y, tolerance)
        assertEquals(expected.z, actual.z, tolerance)
    }
}
