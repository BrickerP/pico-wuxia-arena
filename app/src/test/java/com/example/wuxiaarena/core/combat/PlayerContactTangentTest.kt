package com.example.wuxiaarena.core.combat

import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.input.ObservationStamp
import com.example.wuxiaarena.core.input.ObservedPose
import com.example.wuxiaarena.core.input.PoseObservation
import com.example.wuxiaarena.core.input.TrackingSnapshot
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.acos
import kotlin.math.ceil
import kotlin.math.floor

class PlayerContactTangentTest {
    private val enemy = Vector3(0.0, 0.0, -1.2)
    private val identity = Quaternion(0.0, 0.0, 0.0, 1.0)

    @Test
    fun lateralContactKeepsItsOwnSweepDirectionAfterLaterMotionReverses() {
        val resolver = PlayerCombatResolver()
        resolver.observe(snapshot(1, 0L, Vector3(-0.35, 0.95, -0.25)), enemy)
        val frame = requireNotNull(resolver.observe(snapshot(3, 100_000_000L, Vector3(0.35, 0.95, -0.25)), enemy))
        val contact = requireNotNull(frame.strike).contact
        assertDirection(Vector3(1.0, 0.0, 0.0), contact.tangent)

        resolver.observe(snapshot(5, 200_000_000L, Vector3(0.10, 0.95, -0.25)), enemy)

        assertDirection(Vector3(1.0, 0.0, 0.0), contact.tangent)
        assertDirection(Vector3(1.0, 0.0, 0.0), resolver.targetContact(frame, enemy, HitZone.BODY).tangent)
    }

    @Test
    fun rotationAroundStationaryTipStillHasMotionAtTheContactBladeSegment() {
        val resolver = PlayerCombatResolver()
        val hand = Vector3(0.0, 0.95, 0.0)
        val enemy = Vector3(0.0, 0.0, -0.4)
        val first = requireNotNull(resolver.observe(snapshot(1, 0L, hand), enemy))
        val turn = Quaternion(0.0, sin(0.05), 0.0, cos(0.05))
        val localTip = first.bladeTip - hand
        val adjustedHand = first.bladeTip - requireNotNull(turn.rotate(localTip))
        val frame = requireNotNull(resolver.observe(snapshot(3, 100_000_000L, adjustedHand, turn), enemy))

        assertEquals(0.0, frame.bladeTipSpeed, 1e-9)
        val target = requireNotNull(resolver.targetContact(frame, enemy, HitZone.BODY).tangent)
        val blade = playerBladeAxis(requireNotNull(first.weaponGrip))
        val steel = BladeSegment((blade.base + blade.tip) * 0.5, (blade.base + blade.tip) * 0.5, 0.012)
        val guard = requireNotNull(firstRigidBladeContact(requireNotNull(first.weaponGrip),
            requireNotNull(frame.weaponGrip), BladeSweep(steel, steel))?.relativeDisplacement?.normalizedOrNull())
        assertTrue(target.x > 0.9)
        assertTrue(guard.x > 0.9)
        assertEquals(1.0, target.length(), 1e-9)
    }

    @Test
    fun rotatingSweepUsesTheContactSubstepRatherThanTheWholeFramesFinalDirection() {
        val resolver = PlayerCombatResolver()
        val enemy = Vector3(0.0, 0.0, -0.4)
        val hand = Vector3(0.0, 0.95, 0.0)
        val first = requireNotNull(resolver.observe(snapshot(1, 0L, hand), enemy))
        val turn = Quaternion(0.0, sin(0.15), 0.0, cos(0.15))
        val adjustedHand = first.bladeTip - requireNotNull(turn.rotate(first.bladeTip - hand))

        val frame = requireNotNull(resolver.observe(snapshot(3, 100_000_000L, adjustedHand, turn), enemy))
        val contact = requireNotNull(frame.strike).contact
        val tangent = requireNotNull(contact.tangent)

        val from = requireNotNull(first.weaponGrip)
        val to = requireNotNull(frame.weaponGrip)
        val body = requireNotNull(frame.targetPose)
        val target = if (contact.zone == HitZone.HEAD) BladeSegment(body.head, body.head, 0.16)
            else BladeSegment(body.bodyBottom, body.bodyTop, 0.24)
        val witness = requireNotNull(firstRigidBladeContact(from, to, BladeSweep(target, target)))
        // This fixture starts touching the body, so its first valid witness may
        // be t=0; motion at that material point still uses the first substep.
        assertTrue(witness.fraction >= 0.0 && witness.fraction < 1.0)
        assertTrue(witness.enemyPoint.distanceTo(contact.point) < 1e-10)

        // Independently place a material point using the fixture's analytic
        // 0.3-radian Y rotation and linear hand path. The actual TOI identifies
        // its source substep; its tangent is not the whole observation chord.
        val pieces = ceil(0.3 / (2.0 * acos(1.0 - 0.0005 / PlayerBladeShape.gripRadius))).toInt()
        val piece = floor(witness.fraction * pieces).toInt().coerceAtMost(pieces - 1)
        val start = piece.toDouble() / pieces
        val end = (piece + 1).toDouble() / pieces
        val fraction = witness.fraction * pieces - piece
        val sagitta = PlayerBladeShape.gripRadius * (1.0 - cos(0.3 / pieces / 2.0))
        fun place(point: Vector3, time: Double): Vector3 {
            val angle = 0.3 * time
            return from.position * (1.0 - time) + to.position * time + Vector3(
                cos(angle) * point.x + sin(angle) * point.z, point.y,
                -sin(angle) * point.x + cos(angle) * point.z)
        }
        val candidates = PlayerBladeShape.capsules.map { part ->
            val localPoint = part.base * (1.0 - witness.playerAxisFraction) + part.tip * witness.playerAxisFraction
            val chordPoint = place(localPoint, start) * (1.0 - fraction) + place(localPoint, end) * fraction
            val witnessAxis = witness.playerPoint + witness.normal * (part.radiusMeters + sagitta)
            localPoint to chordPoint.distanceTo(witnessAxis)
        }
        val matched = requireNotNull(candidates.minByOrNull { it.second })
        assertTrue("The TOI must identify a material point on an actual chain part", matched.second < 1e-9)
        val expected = requireNotNull((place(matched.first, end) - place(matched.first, start)).normalizedOrNull())
        val whole = requireNotNull((place(matched.first, 1.0) - place(matched.first, 0.0)).normalizedOrNull())
        assertDirection(expected, tangent)
        assertTrue("A whole-frame direction must not replace the real TOI substep material motion",
            tangent.distanceTo(whole) > 0.001)
        println("CHAIN_CONTACT_TANGENT toi=${witness.fraction} piece=$piece/$pieces local=${matched.first} " +
            "actual=$tangent expected=$expected whole=$whole")
        assertEquals(1.0, tangent.length(), 1e-9)
    }

    @Test
    fun baselineRestAndInvalidIntervalCannotReuseAnEarlierCuttingDirection() {
        val resolver = PlayerCombatResolver()
        val initial = requireNotNull(resolver.observe(snapshot(1, 0L, Vector3(-0.25, 0.95, -0.25)), enemy))
        assertNull(resolver.targetContact(initial, enemy, HitZone.BODY).tangent)
        assertNull(initial.bladeBaseDelta)
        val moving = requireNotNull(resolver.observe(snapshot(3, 100_000_000L, Vector3(0.0, 0.95, -0.25)), enemy))
        assertTrue(resolver.targetContact(moving, enemy, HitZone.BODY).tangent != null)

        val resting = requireNotNull(resolver.observe(snapshot(5, 200_000_000L, Vector3(0.001, 0.95, -0.25)), enemy))
        assertNull(resolver.targetContact(resting, enemy, HitZone.BODY).tangent)
        val still = playerBlade(requireNotNull(resting.weaponGrip))
        for (part in still) assertNull(firstBladeContact(BladeSweep(part, part), BladeSweep(part, part))
            ?.relativeDisplacement?.normalizedOrNull())
        assertNull(resting.bladeBaseDelta)
        assertNull(resting.bladeTipDelta)

        val afterGap = requireNotNull(resolver.observe(snapshot(7, 600_000_000L, Vector3(0.25, 0.95, -0.25)), enemy))
        assertNull(resolver.targetContact(afterGap, enemy, HitZone.BODY).tangent)
        assertNull(afterGap.bladeBaseDelta)
        assertNull(afterGap.bladeTipDelta)
    }

    @Test
    fun duplicateHandObservationKeepsTheSameMotionIntervalWithoutCreatingAnotherStrike() {
        val resolver = PlayerCombatResolver()
        resolver.observe(snapshot(1, 0L, Vector3(-0.35, 0.95, -0.25)), enemy)
        val observation = snapshot(3, 100_000_000L, Vector3(0.35, 0.95, -0.25))
        val first = requireNotNull(resolver.observe(observation, enemy))
        val head = requireNotNull(observation.head).copy(stamp = ObservationStamp(4, 150_000_000L, 1, InputOrigin.SYNTHETIC))

        val duplicate = requireNotNull(resolver.observe(observation.copy(head = head), enemy))

        assertNull(duplicate.strike)
        assertEquals(first.receivedAtNanos, duplicate.receivedAtNanos)
        assertEquals(first.bladeBaseDelta, duplicate.bladeBaseDelta)
        assertEquals(first.bladeTipDelta, duplicate.bladeTipDelta)
    }

    @Test
    fun anIncomingBodyContactKeepsTheEnemyBladeMotion() {
        val head = BladeSegment(Vector3(0.0, 1.6, 0.0), Vector3(0.0, 1.6, 0.0), 0.16)
        val incoming = BladeSweep(
            BladeSegment(Vector3(-0.3, 1.6, -1.0), Vector3(0.3, 1.6, -1.0), 0.012),
            BladeSegment(Vector3(-0.3, 1.6, 1.0), Vector3(0.3, 1.6, 1.0), 0.012))
        val contact = requireNotNull(firstBladeContact(incoming, BladeSweep(head, head)))
        assertDirection(Vector3(0.0, 0.0, 1.0), contact.relativeDisplacement.normalizedOrNull())
        assertTrue(contact.fraction in 0.4..0.5)
    }

    private fun assertDirection(expected: Vector3, actual: Vector3?) {
        val direction = requireNotNull(actual)
        assertEquals(expected.x, direction.x, 1e-9)
        assertEquals(expected.y, direction.y, 1e-9)
        assertEquals(expected.z, direction.z, 1e-9)
    }

    private fun snapshot(sequence: Long, time: Long, hand: Vector3, rotation: Quaternion = identity) = TrackingSnapshot(
        head = PoseObservation(ObservationStamp(sequence - 1L, time, 1L, InputOrigin.SYNTHETIC),
            ObservedPose(Vector3(0.0, 1.6, 0.0), identity)),
        left = PoseObservation(ObservationStamp(sequence, time, 1L, InputOrigin.SYNTHETIC), ObservedPose(hand, rotation)),
        right = PoseObservation(ObservationStamp(sequence, time, 1L, InputOrigin.SYNTHETIC),
            ObservedPose(Vector3(0.7, 1.2, 0.0), identity)),
        dominantHand = Hand.LEFT,
        headContinuity = 0L,
        leftContinuity = 0L,
        rightContinuity = 0L,
    )
}
