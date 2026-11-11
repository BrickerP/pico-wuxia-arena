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
    fun generatedDataMatchesThePublishedWeaponBankIdentity() {
        assertEquals(
            "7373f5937cd19d1306b861ca0e1654e040977eafb3af6685618742e3e0716cff",
            AttackBankProfileData.bindingSha256,
        )
        val expected = mapOf(
            "asset://models/opponents/base.glb" to (
                "e7f3de3d8c7e202999b2d456ae85257b89a01e7c21792f332c4b273c77b60cbc" to
                    "f4b2d918bdb63cfd9436708822dc262df9c5e94ec357f1dc6b5a0ee01a114450"
                ),
            "asset://models/opponents/indigo.glb" to (
                "448d46394743018aff3165e0e49e5c07480b617664c072c14ab6ae186cc87ef3" to
                    "4633e2a7e3d8173f09e2c1e7ff98e713b11cacb6b01979055dbe4ba469d44a3a"
                ),
            "asset://models/opponents/veteran.glb" to (
                "0c0b57a4f3684a25603a6875b2fd9188096755dc4b3688d921a7de8776f1e9c2" to
                    "c6822e9f07ca94af850ded93c7a2d175bd10df4a4cb73be4f08d024cc9dd2c88"
                ),
        )
        assertEquals(expected.keys, AttackBankProfileData.characters.keys)
        for ((asset, hashes) in expected) {
            val character = AttackBankProfileData.characters.getValue(asset)
            assertEquals("Model identity for $asset", hashes.first, character.modelSha256)
            assertEquals("Profile identity for $asset", hashes.second, character.profileSha256)
        }
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
                assertEquals(106, profile.samples.size)
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
                origin, 0.5f, direction, guarding = false, recoveryFromContact = true))
            assertEquals(profile.sample(1.0).inStage(origin, 0.5f), recovered)
        }
    }

    @Test
    fun actualOpponentConsumersUseNewGuardAndThePlayerViewIncomingBladeDirection() {
        val origin = Vector3(0.0, 0.028, -1.3)
        for (opponent in arenaOpponents) for (direction in AttackDirection.entries) {
            val profile = opponent.attackProfile(direction)
            val guard = profile.sample(0.0).inStage(origin, 0.3f)
            assertEquals(guard.contact, opponent.contactPose(EnemyPhase.IDLE, 0L, null, origin, 0.3f, direction, false))
            assertEquals(guard.contact, opponent.contactPose(EnemyPhase.HIT, ms(200), ms(100), origin, 0.3f, direction, true))
            assertEquals(EnemyContactPose.standing(origin), opponent.contactPose(EnemyPhase.IDLE, 0L, null,
                origin, 0.3f, direction, false, moving = true))
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

    private fun assertPoint(expected: Vector3, actual: Vector3, tolerance: Double = 1e-12) {
        assertEquals(expected.x, actual.x, tolerance)
        assertEquals(expected.y, actual.y, tolerance)
        assertEquals(expected.z, actual.z, tolerance)
    }
}
