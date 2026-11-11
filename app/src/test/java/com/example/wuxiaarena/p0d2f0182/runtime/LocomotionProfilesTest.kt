package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/** Synthetic changing poses exercise the sampling contract; these are not final actor data. */
class LocomotionProfilesTest {
    private fun pose(time: Double, offset: Double = 4.0 * time) = AttackPoseSample(
        time,
        EnemyContactPose(
            Vector3(1.0 + offset, 2.0 + offset, 3.0 + offset),
            Vector3(4.0 + offset, 5.0 + offset, 6.0 + offset),
            Vector3(7.0 + offset, 8.0 + offset, 9.0 + offset),
        ),
        Vector3(10.0 + offset, 11.0 + offset, 12.0 + offset),
        Vector3(13.0 + offset, 14.0 + offset, 15.0 + offset),
    )

    private fun idle() = PoseClipProfile("idle", listOf(pose(0.125, 50.0), pose(1.5, 50.0)))
    private fun walk() = PoseClipProfile("walk", listOf(
        pose(0.0, 0.0), pose(1.0 / 3.0, 0.0), pose(11.0 / 12.0, 4.0), pose(1.5, 0.0),
    ))
    private fun events(count: Int = 6) = (0 until count).map { index ->
        GaitStepEvent(
            index / count.toDouble(),
            if (index % 2 == 0) EnemyFoot.LEFT else EnemyFoot.RIGHT,
            if (index % 2 == 0) EnemyFoot.RIGHT else EnemyFoot.LEFT,
        )
    }

    private fun profile(
        idle: PoseClipProfile = idle(),
        walk: PoseClipProfile = walk(),
        start: Double = 1.0 / 3.0,
        end: Double = 1.5,
        stride: Double = 1.45,
        events: List<GaitStepEvent> = events(),
    ) = LocomotionProfile(idle, walk, start, end, stride, events)

    @Test
    fun idleUsesItsActualFirstSampleAndClipInsteadOfAWalkOrStandingConstant() {
        val profile = profile()
        for (gait in listOf(0.0, 0.725, -0.725, 1.45, -2.9)) {
            assertEquals("idle", profile.clip(false))
            assertEquals(0.125, profile.sourceSeconds(false, gait), 0.0)
            assertSame(profile.idle.samples.first(), profile.sample(false, gait))
        }
        assertEquals("walk", profile.clip(true))
    }

    @Test
    fun signedGaitMapsZeroPositiveNegativeAndCompleteLoopsToTheSameWalkClock() {
        val profile = profile()
        val start = profile.loopStartSeconds
        val span = profile.loopEndSeconds - start
        for (gait in listOf(0.0, 1.45, -1.45, 2.9, -2.9)) {
            assertEquals(start, profile.sourceSeconds(true, gait), 0.0)
        }
        assertEquals(start + span * 0.25, profile.sourceSeconds(true, 1.45 * 0.25), 1e-12)
        assertEquals(start + span * 0.75, profile.sourceSeconds(true, -1.45 * 0.25), 1e-12)
        assertEquals(start + span * 0.5, profile.sourceSeconds(true, 1.45 * 0.5), 1e-12)
        assertEquals(start + span * 0.5, profile.sourceSeconds(true, -1.45 * 0.5), 1e-12)
        assertEquals(profile.sourceSeconds(true, 0.2), profile.sourceSeconds(true, 1.65), 1e-12)
        assertEquals(profile.sourceSeconds(true, -0.2), profile.sourceSeconds(true, -1.65), 1e-12)
    }

    @Test
    fun crossingTheLoopSeamNeverSamplesTheExclusiveEndKey() {
        val profile = profile()
        val before = profile.sourceSeconds(true, Math.nextDown(profile.strideMeters))
        val after = profile.sourceSeconds(true, Math.nextUp(profile.strideMeters))
        assertTrue(before >= profile.loopStartSeconds && before < profile.loopEndSeconds)
        assertTrue(after >= profile.loopStartSeconds && after < profile.loopEndSeconds)
        assertTrue(before > profile.sourceSeconds(true, 0.725))
        assertTrue(after < profile.sourceSeconds(true, 0.725))
        assertTrue(profile.sourceSeconds(true, -Double.MIN_VALUE) < profile.loopEndSeconds)
    }

    @Test
    fun sixStepMarkersSharePositiveAndReverseSourcePhaseWithoutConsumingState() {
        val profile = profile()
        for ((index, event) in profile.stepEvents.withIndex()) {
            val positive = profile.strideMeters * event.phase
            val expected = profile.loopStartSeconds + (profile.loopEndSeconds - profile.loopStartSeconds) * event.phase
            assertEquals(expected, profile.sourceSeconds(true, positive), 1e-12)
            assertEquals(expected, profile.sourceSeconds(true, positive - profile.strideMeters), 1e-12)
            assertEquals(if (index % 2 == 0) EnemyFoot.LEFT else EnemyFoot.RIGHT, event.forwardFoot)
            assertEquals(if (index % 2 == 0) EnemyFoot.RIGHT else EnemyFoot.LEFT, event.reverseFoot)
        }
        val gait = 0.731
        val beforePause = profile.sample(true, gait)
        repeat(3) {
            assertEquals(beforePause, profile.sample(true, gait))
            profile.sample(false, gait)
        }
        assertEquals(beforePause, profile.sample(true, gait))
        assertEquals(0.24166666666666667, profile.strideMeters / profile.stepEvents.size, 0.0)
    }

    @Test
    fun movingSamplesInterpolateActualHeadBodyAndBladeTogether() {
        val profile = profile()
        for (gait in listOf(0.0, 0.2175, 0.725, 1.2, -0.2175, -1.2)) {
            val source = profile.sourceSeconds(true, gait)
            val actual = profile.sample(true, gait)
            val phase = (source - profile.loopStartSeconds) / (profile.loopEndSeconds - profile.loopStartSeconds)
            val offset = if (phase <= 0.5) phase * 8.0 else (1.0 - phase) * 8.0
            assertEquals(source, actual.sourceSeconds, 0.0)
            assertPose(pose(source, offset), actual)
        }
        assertTrue(profile.sample(true, 0.0).contact != profile.sample(true, 0.725).contact)
        assertTrue(profile.sample(true, 0.0).bladeTip != profile.sample(true, 0.725).bladeTip)
    }

    @Test
    fun lockedIdleRejectsAnyChangedBodyOrBladeAnchorWhileIgnoringSampleTime() {
        val first = idle().samples.first()
        assertEquals(50.0, first.contact.head.x - 1.0, 0.0)
        for (anchor in 0 until 5) {
            val changed = changedAnchor(first.copy(sourceSeconds = 1.5), anchor)
            assertThrows(IllegalArgumentException::class.java) {
                profile(idle = PoseClipProfile("idle", listOf(first, changed)))
            }
        }
        val profile = profile()
        assertSame(profile.idle.samples.first(), profile.sample(false, 0.725))
    }

    @Test
    fun walkLoopRejectsEvenOneUlpOfMismatchInAnyEndpointAnchor() {
        val samples = walk().samples
        for (anchor in 0 until 5) {
            val changed = changedAnchor(samples.last(), anchor)
            assertThrows(IllegalArgumentException::class.java) {
                profile(walk = PoseClipProfile("walk", samples.dropLast(1) + changed))
            }
        }
        val profile = profile()
        val first = profile.walk.sample(profile.loopStartSeconds)
        val last = profile.walk.sample(profile.loopEndSeconds)
        assertEquals(first.contact, last.contact)
        assertEquals(first.bladeBase, last.bladeBase)
        assertEquals(first.bladeTip, last.bladeTip)
        assertTrue(profile.sample(true, 0.725).contact != first.contact)
    }

    @Test
    fun lockedWalkRequiresSixUniformAlternatingFootEvents() {
        for (count in listOf(1, 2, 7)) {
            assertThrows(IllegalArgumentException::class.java) { profile(events = events(count)) }
        }
        for (index in 0 until 6) {
            val wrongFoot = events().toMutableList()
            wrongFoot[index] = wrongFoot[index].let {
                it.copy(forwardFoot = it.reverseFoot, reverseFoot = it.forwardFoot)
            }
            assertThrows(IllegalArgumentException::class.java) { profile(events = wrongFoot) }
        }
        val nonUniform = events().toMutableList()
        nonUniform[3] = nonUniform[3].copy(phase = 0.5 + 1e-8)
        assertThrows(IllegalArgumentException::class.java) { profile(events = nonUniform) }
        val withinProducerTolerance = events().toMutableList()
        withinProducerTolerance[3] = withinProducerTolerance[3].copy(phase = 0.5 + 5e-10)
        assertEquals(6, profile(events = withinProducerTolerance).stepEvents.size)
    }

    @Test
    fun sampledBodyAndBladeReceiveStageYawLiftAndRecoilExactlyOnce() {
        val profile = profile()
        val origin = Vector3(0.35, 0.028, -1.5)
        val recoil = Vector3(-0.04, 0.0, -0.16)
        for (moving in listOf(false, true)) {
            val local = profile.sample(moving, -0.2175)
            val stage = local.inStage(origin + recoil, (Math.PI / 2.0).toFloat())
            val localPoints = listOf(local.contact.head, local.contact.bodyBottom, local.contact.bodyTop, local.bladeBase, local.bladeTip)
            val stagePoints = listOf(stage.contact.head, stage.contact.bodyBottom, stage.contact.bodyTop, stage.bladeBase, stage.bladeTip)
            for ((point, actual) in localPoints.zip(stagePoints)) {
                assertPoint(Vector3(origin.x + recoil.x + point.z, point.y + 0.028, origin.z + recoil.z - point.x), actual, 1e-5)
                assertEquals(point.y + 0.028, actual.y, 1e-12)
            }
            assertEquals(local.sourceSeconds, stage.sourceSeconds, 0.0)
        }
    }

    @Test
    fun poseClipsClampEndpointsAndCopyTheirSampleLists() {
        val samples = mutableListOf(pose(0.0), pose(1.5))
        val clip = PoseClipProfile("walk", samples)
        samples.clear()
        assertEquals(2, clip.samples.size)
        assertSame(clip.samples.first(), clip.sample(-1.0))
        assertSame(clip.samples.last(), clip.sample(100.0))
        assertPose(pose(0.5), clip.sample(0.5))
        val steps = events().toMutableList()
        val profile = profile(events = steps)
        steps.clear()
        assertEquals(6, profile.stepEvents.size)
    }

    @Test
    fun invalidClipNamesSamplesAndIncompleteWalkCoverageAreRejected() {
        assertThrows(IllegalArgumentException::class.java) { PoseClipProfile(" ", listOf(pose(0.0), pose(1.5))) }
        assertThrows(IllegalArgumentException::class.java) { PoseClipProfile("walk", emptyList()) }
        assertThrows(IllegalArgumentException::class.java) { PoseClipProfile("walk", listOf(pose(0.0))) }
        assertThrows(IllegalArgumentException::class.java) { PoseClipProfile("walk", listOf(pose(0.0), pose(0.0))) }
        assertThrows(IllegalArgumentException::class.java) { PoseClipProfile("walk", listOf(pose(1.5), pose(0.0))) }
        assertThrows(IllegalArgumentException::class.java) { profile(idle = walk()) }
        assertThrows(IllegalArgumentException::class.java) { profile(walk = idle()) }
        assertThrows(IllegalArgumentException::class.java) {
            profile(walk = PoseClipProfile("walk", listOf(pose(0.5), pose(1.5))))
        }
        assertThrows(IllegalArgumentException::class.java) {
            profile(walk = PoseClipProfile("walk", listOf(pose(0.0), pose(1.4))))
        }
    }

    @Test
    fun invalidLoopStrideStepEventsAndNonFiniteClocksAreRejected() {
        assertThrows(IllegalArgumentException::class.java) { profile(start = -0.1) }
        assertThrows(IllegalArgumentException::class.java) { profile(end = -0.1) }
        assertThrows(IllegalArgumentException::class.java) { profile(start = 1.5) }
        assertThrows(IllegalArgumentException::class.java) { profile(start = 1.6) }
        assertThrows(IllegalArgumentException::class.java) { profile(stride = 0.0) }
        assertThrows(IllegalArgumentException::class.java) { profile(stride = -1.45) }
        assertThrows(IllegalArgumentException::class.java) { profile(events = emptyList()) }
        assertThrows(IllegalArgumentException::class.java) { profile(events = listOf(events()[0], events()[0])) }
        assertThrows(IllegalArgumentException::class.java) { profile(events = events().reversed()) }
        assertThrows(IllegalArgumentException::class.java) { GaitStepEvent(0.0, EnemyFoot.LEFT, EnemyFoot.LEFT) }
        for (phase in listOf(-0.1, 1.0, 1.1)) {
            assertThrows(IllegalArgumentException::class.java) { GaitStepEvent(phase, EnemyFoot.LEFT, EnemyFoot.RIGHT) }
        }
        for (invalid in listOf(Double.NaN, Double.POSITIVE_INFINITY, Double.NEGATIVE_INFINITY)) {
            assertThrows(IllegalArgumentException::class.java) { profile(start = invalid) }
            assertThrows(IllegalArgumentException::class.java) { profile(end = invalid) }
            assertThrows(IllegalArgumentException::class.java) { profile(stride = invalid) }
            assertThrows(IllegalArgumentException::class.java) { GaitStepEvent(invalid, EnemyFoot.LEFT, EnemyFoot.RIGHT) }
            assertThrows(IllegalArgumentException::class.java) { walk().sample(invalid) }
            for (moving in listOf(false, true)) {
                assertThrows(IllegalArgumentException::class.java) { profile().sourceSeconds(moving, invalid) }
                assertThrows(IllegalArgumentException::class.java) { profile().sample(moving, invalid) }
            }
        }
    }

    @Test
    fun finiteExtremeGaitAndStrideValuesStillProduceAnInRangeSourceTime() {
        for (stride in listOf(Double.MIN_VALUE, 1e-200, 1.45, Double.MAX_VALUE)) {
            val profile = profile(stride = stride)
            for (gait in listOf(-Double.MAX_VALUE, -Double.MIN_VALUE, 0.0, Double.MIN_VALUE, Double.MAX_VALUE)) {
                val source = profile.sourceSeconds(true, gait)
                assertTrue(source.isFinite())
                assertTrue(source >= profile.loopStartSeconds && source < profile.loopEndSeconds)
            }
        }
    }

    private fun assertPose(expected: AttackPoseSample, actual: AttackPoseSample) {
        assertEquals(expected.sourceSeconds, actual.sourceSeconds, 0.0)
        assertPoint(expected.contact.head, actual.contact.head)
        assertPoint(expected.contact.bodyBottom, actual.contact.bodyBottom)
        assertPoint(expected.contact.bodyTop, actual.contact.bodyTop)
        assertPoint(expected.bladeBase, actual.bladeBase)
        assertPoint(expected.bladeTip, actual.bladeTip)
    }

    private fun changedAnchor(sample: AttackPoseSample, index: Int): AttackPoseSample {
        fun shifted(point: Vector3) = point.copy(x = Math.nextUp(point.x))
        return when (index) {
            0 -> sample.copy(contact = sample.contact.copy(head = shifted(sample.contact.head)))
            1 -> sample.copy(contact = sample.contact.copy(bodyBottom = shifted(sample.contact.bodyBottom)))
            2 -> sample.copy(contact = sample.contact.copy(bodyTop = shifted(sample.contact.bodyTop)))
            3 -> sample.copy(bladeBase = shifted(sample.bladeBase))
            else -> sample.copy(bladeTip = shifted(sample.bladeTip))
        }
    }

    private fun assertPoint(expected: Vector3, actual: Vector3, tolerance: Double = 1e-12) {
        assertEquals(expected.x, actual.x, tolerance)
        assertEquals(expected.y, actual.y, tolerance)
        assertEquals(expected.z, actual.z, tolerance)
    }
}
