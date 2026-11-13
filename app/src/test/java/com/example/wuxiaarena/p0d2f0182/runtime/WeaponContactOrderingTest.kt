package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.BladeContact
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyContactPose
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.HitZone
import com.example.wuxiaarena.core.combat.PlayerMotionFrame
import com.example.wuxiaarena.core.combat.QualifiedSwing
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Deterministic Stage geometry exercises the actual session candidate ordering. */
class WeaponContactOrderingTest {
    @Test
    fun steelEarlierThanEnemyBodyArrestsTheStrike() {
        val fixture = Fixture()
        val pose = pose(bodyAt(0.6), 0.0)
        val result = requireNotNull(fixture.query(frame(-1.0), frame(1.0, swing()), pose, pose))
        assertTrue(result.steel)
        assertFalse(result.playerAttack)
        assertTrue(result.contact.fraction in 0.45..0.50)
    }

    @Test
    fun enemyBodyEarlierThanSteelReceivesTheRealOutgoingContact() {
        val fixture = Fixture()
        val pose = pose(bodyAt(-0.6), 0.0)
        val result = requireNotNull(fixture.query(frame(-1.0), frame(1.0, swing()), pose, pose))
        assertFalse(result.steel)
        assertTrue(result.playerAttack)
        assertEquals(HitZone.BODY, result.zone)
        assertTrue(result.contact.fraction in 0.05..0.10)
        assertTrue(result.contact.enemyPoint.distanceTo(Vector3(-0.84, 1.2, -0.4)) < 0.03)
    }

    @Test
    fun oppositeMovingBladesStillResolveSteelBeforeTheLaterBody() {
        val fixture = Fixture()
        val before = pose(bodyAt(0.6), 0.5)
        val after = pose(bodyAt(0.6), -0.5)
        val result = requireNotNull(fixture.query(frame(-1.0), frame(1.0, swing()), before, after))
        assertTrue(result.steel)
        assertFalse(result.playerAttack)
        assertTrue(result.contact.fraction in 0.45..0.50)
        assertEquals(3.0, result.contact.relativeDisplacement.x, 1e-10)
    }

    @Test
    fun incomingBladeCrossesTheHeadBetweenSeparatedEndpoints() {
        val fixture = Fixture(active = true)
        val body = bodyAt(10.0)
        val before = incoming(body, -2.0, 1.65, 1.85)
        val after = incoming(body, 2.0, 1.65, 1.85)
        val from = distantWeaponFrame(Vector3(0.0, 1.6, 0.0))
        val result = requireNotNull(fixture.query(from, from, before, after))
        assertFalse(result.steel)
        assertFalse(result.playerAttack)
        assertEquals(HitZone.HEAD, result.zone)
        assertTrue(result.contact.fraction in 0.4..0.5)
    }

    @Test
    fun incomingBladeCrossesTheTorsoAndMovingHmdCanAvoidIt() {
        val fixture = Fixture(active = true)
        val body = bodyAt(10.0)
        val before = incoming(body, -2.0, 0.8, 1.1)
        val after = incoming(body, 2.0, 0.8, 1.1)
        val centered = distantWeaponFrame(Vector3(0.0, 1.6, 0.0))
        val result = requireNotNull(fixture.query(centered, centered, before, after))
        assertEquals(HitZone.BODY, result.zone)
        assertFalse(result.steel)
        assertFalse(result.playerAttack)
        val away = distantWeaponFrame(Vector3(1.0, 1.6, 0.0))
        assertNull(fixture.query(away, away, before, after))
        assertNull(fixture.query(centered, away, before, after))
    }

    @Test
    fun inactiveEnemyBladeCannotDamagePlayerWithoutAnySteelContact() {
        val fixture = Fixture()
        val body = bodyAt(10.0)
        val before = incoming(body, -2.0, 0.8, 1.1)
        val after = incoming(body, 2.0, 0.8, 1.1)
        val frame = distantWeaponFrame(Vector3(0.0, 1.6, 0.0))
        assertNull(fixture.query(frame, frame, before, after))
    }

    @Test
    fun qualifiedSwingHitsMovingBodyThatWasOutsideTheOldStaticHitVolume() {
        val fixture = Fixture()
        val before = pose(bodyAt(2.0), 5.0)
        val after = pose(bodyAt(0.6), 5.0)
        val from = frame(-1.0)
        val to = frame(1.0, swing())
        assertNull(to.strike)
        // The old static body cannot be touched anywhere along this player's sweep.
        assertNull(fixture.query(from, to, before, before))
        val movingBody = requireNotNull(fixture.query(from, to, before, after))
        assertTrue(movingBody.playerAttack)
        assertFalse(movingBody.steel)
        assertEquals(HitZone.BODY, movingBody.zone)
        assertTrue(movingBody.contact.fraction in 0.7..0.9)
    }

    private data class Result(val contact: BladeContact, val steel: Boolean, val zone: HitZone, val playerAttack: Boolean)

    private class Fixture(active: Boolean = false) {
        private val session = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
        private val query = ArenaSession::class.java.getDeclaredMethod("queryContact", PlayerMotionFrame::class.java,
            PlayerMotionFrame::class.java, AttackPoseSample::class.java, AttackPoseSample::class.java).apply { isAccessible = true }

        init {
            if (active) {
                val field = ArenaSession::class.java.getDeclaredField("combat").apply { isAccessible = true }
                val combat = field.get(session) as EnemyCombatStateMachine
                combat.advanceBy(800_000_000L, true)
                combat.tryStartAttack(AttackDirection.OVERHEAD, true)
                combat.advanceBy(AttackDirection.OVERHEAD.preparationNanos + AttackDirection.OVERHEAD.startupNanos, true)
                assertEquals(EnemyPhase.ACTIVE, combat.phase)
            }
        }

        fun query(from: PlayerMotionFrame, to: PlayerMotionFrame, before: AttackPoseSample, after: AttackPoseSample): Result? {
            val value = query.invoke(session, from, to, before, after) ?: return null
            fun field(name: String): Any = requireNotNull(value.javaClass.getDeclaredField(name).apply { isAccessible = true }.get(value))
            return Result(field("contact") as BladeContact, field("steel") as Boolean,
                field("zone") as HitZone, field("playerAttack") as Boolean)
        }
    }

    private fun frame(x: Double, swing: QualifiedSwing? = null): PlayerMotionFrame {
        val grip = WeaponGrip(Vector3(x, 1.2, 0.0), IDENTITY)
        val blade = playerBlade(grip)
        return PlayerMotionFrame(1L, blade.base, blade.tip, 2.0, null, false,
            Vector3(0.0, 1.6, 3.0), weaponGrip = grip, rawWeaponGrip = grip, swing = swing)
    }

    private fun distantWeaponFrame(head: Vector3): PlayerMotionFrame = frame(5.0).copy(headPosition = head)

    private fun swing() = QualifiedSwing(1L, 1.0)

    private fun bodyAt(x: Double) = EnemyContactPose(Vector3(x, 2.4, -0.4),
        Vector3(x, 0.5, -0.4), Vector3(x, 1.4, -0.4))

    private fun pose(body: EnemyContactPose, steelX: Double) = AttackPoseSample(0.0, body,
        Vector3(steelX, 1.0, -0.4), Vector3(steelX, 1.4, -0.4))

    private fun incoming(body: EnemyContactPose, z: Double, bottom: Double, top: Double) = AttackPoseSample(0.0, body,
        Vector3(0.0, bottom, z), Vector3(0.0, top, z))

    private companion object {
        val IDENTITY = Quaternion(0.0, 0.0, 0.0, 1.0)
    }
}
