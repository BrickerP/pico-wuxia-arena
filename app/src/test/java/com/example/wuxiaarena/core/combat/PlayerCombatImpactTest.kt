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

class PlayerCombatImpactTest {
    private val enemy = Vector3(0.0, 0.0, -1.2)
    private val rotation = Quaternion(0.0, 0.0, 0.0, 1.0)

    @Test
    fun acceptedLeftHandStrokeRetainsTheTargetSurfaceWitness() {
        val resolver = PlayerCombatResolver()
        val first = requireNotNull(resolver.observe(snapshot(1, 0L, 0.0), enemy))
        assertNull(first.strike)

        val frame = requireNotNull(resolver.observe(snapshot(3, 100_000_000L, -0.2), enemy))
        val strike = requireNotNull(frame.strike)
        val contact = strike.contact

        assertEquals(Hand.LEFT, frame.hand)
        assertEquals(HitZone.BODY, strike.zone)
        assertEquals(strike.zone, contact.zone)
        assertTrue(contact.point.isFinite())
        assertTrue(contact.normal.isFinite())
        assertEquals(1.0, contact.normal.length(), 1e-9)
        // The body axis spans Y=.55..1.40 and its unchanged radius is .24 m.
        val axisPoint = Vector3(enemy.x, contact.point.y.coerceIn(0.55, 1.40), enemy.z)
        assertEquals(0.24, contact.point.distanceTo(axisPoint), 1e-9)
        assertTrue(contact.point.distanceTo(frame.bladeBase) > 0.4)
        assertTrue(contact.normal.z > 0.0)
    }

    @Test
    fun duplicateHandPacketAndContinuedStrokeDoNotProduceAnotherStrike() {
        val resolver = PlayerCombatResolver()
        resolver.observe(snapshot(1, 0L, 0.0), enemy)
        val hitSnapshot = snapshot(3, 100_000_000L, -0.2)
        val firstHit = requireNotNull(resolver.observe(hitSnapshot, enemy)?.strike)

        val updatedHead = PoseObservation(
            ObservationStamp(4, 150_000_000L, 1, InputOrigin.SYNTHETIC),
            ObservedPose(Vector3(0.0, 1.6, 0.0), rotation),
        )
        val duplicate = requireNotNull(resolver.observe(hitSnapshot.copy(head = updatedHead), enemy))
        assertNull(duplicate.strike)
        assertEquals(Hand.LEFT, duplicate.hand)

        val continued = requireNotNull(resolver.observe(snapshot(5, 200_000_000L, -0.4), enemy))
        assertNull(continued.strike)
        assertTrue(firstHit.contact.point.isFinite())
    }

    @Test
    fun anExpiredMotionIntervalOnlyEstablishesANewBaseline() {
        val resolver = PlayerCombatResolver()
        resolver.observe(snapshot(1, 0L, 0.0), enemy)

        val afterGap = requireNotNull(resolver.observe(snapshot(3, 400_000_000L, -0.2), enemy))

        assertNull(afterGap.strike)
        assertEquals(0.0, afterGap.bladeTipSpeed, 0.0)
        assertEquals(Hand.LEFT, afterGap.hand)
    }

    @Test
    fun aProvidedAnimationPoseMovesTheContactVolumeWithoutExpandingIt() {
        val resolver = PlayerCombatResolver()
        val shifted = EnemyContactPose.standing(enemy).translated(Vector3(0.5, 0.0, 0.0))
        resolver.observe(snapshot(1, 0L, 0.0), enemy, shifted)
        assertNull(resolver.observe(snapshot(3, 100_000_000L, -0.2), enemy, shifted)?.strike)
        val next = snapshot(5, 200_000_000L, -0.2)
        val left = requireNotNull(next.left)
        val pose = requireNotNull(left.pose)
        val moved = next.copy(left = left.copy(pose = pose.copy(position = Vector3(0.5, 0.95, -0.2))))
        val contact = requireNotNull(resolver.observe(moved, enemy, shifted)?.strike).contact
        val axis = Vector3(0.5, contact.point.y.coerceIn(0.55, 1.40), enemy.z)
        assertEquals(0.24, contact.point.distanceTo(axis), 1e-9)
    }

    @Test
    fun invalidAnimationGeometryCannotProduceAContact() {
        val resolver = PlayerCombatResolver()
        val invalid = EnemyContactPose.standing(enemy).copy(head = Vector3(Double.NaN, 1.62, 0.0))
        assertNull(resolver.observe(snapshot(1, 0L, 0.0), enemy, invalid))
        assertNull(resolver.observe(snapshot(3, 100_000_000L, -0.2), enemy)?.strike)
    }

    private fun snapshot(sequence: Long, time: Long, handZ: Double): TrackingSnapshot {
        val headStamp = ObservationStamp(sequence - 1, time, 1, InputOrigin.SYNTHETIC)
        val handStamp = ObservationStamp(sequence, time, 1, InputOrigin.SYNTHETIC)
        return TrackingSnapshot(
            head = PoseObservation(headStamp, ObservedPose(Vector3(0.0, 1.6, 0.0), rotation)),
            left = PoseObservation(handStamp, ObservedPose(Vector3(0.0, 0.95, handZ), rotation)),
            right = PoseObservation(handStamp, ObservedPose(Vector3(0.7, 1.2, 0.0), rotation)),
            dominantHand = Hand.LEFT,
            headContinuity = 0,
            leftContinuity = 0,
            rightContinuity = 0,
        )
    }
}
