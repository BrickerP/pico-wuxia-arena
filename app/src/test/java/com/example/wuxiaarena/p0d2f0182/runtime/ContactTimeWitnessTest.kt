package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.AttackDirection
import com.example.wuxiaarena.core.combat.AttackOutcome
import com.example.wuxiaarena.core.combat.BladeContact
import com.example.wuxiaarena.core.combat.BladeSegment
import com.example.wuxiaarena.core.combat.BladeSweep
import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.EnemyCombatEvent
import com.example.wuxiaarena.core.combat.EnemyCombatStateMachine
import com.example.wuxiaarena.core.combat.EnemyPhase
import com.example.wuxiaarena.core.combat.PlayerCombatResolver
import com.example.wuxiaarena.core.combat.PlayerMotionFrame
import com.example.wuxiaarena.core.combat.WeaponGrip
import com.example.wuxiaarena.core.combat.firstBladeContact
import com.example.wuxiaarena.core.combat.playerBlade
import com.example.wuxiaarena.core.math.Quaternion
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import kotlin.math.sqrt

class ContactTimeWitnessTest {
    @Test
    fun trueContactAt170msRetainsParryEvenWhenEndpointReceiptIs220ms() {
        val session = session()
        val from = guardFrame(0L, 0L)
        val to = guardFrame(220_000_000L, 0L)
        val atContact = session.interpolateMotionFrame(from, to, 170.0 / 220.0, 170_000_000L)
        assertEquals(170_000_000L, atContact.receivedAtNanos)
        val contact = realGuardContact(requireNotNull(atContact.weaponGrip))
        assertEquals(AttackOutcome.PARRIED, resolve(atContact, contact))
        assertEquals(AttackOutcome.BLOCKED, resolve(to, contact))
    }

    @Test
    fun guardEvidenceFrom220msCannotGradeAnEarlier170msContact() {
        val session = session()
        val from = guardFrame(0L, null).copy(guardDirection = null)
        val to = guardFrame(220_000_000L, 220_000_000L)
        val atContact = session.interpolateMotionFrame(from, to, 170.0 / 220.0, 170_000_000L)
        assertNull(atContact.guardEnteredAtNanos)
        assertNull(atContact.fastGuardAtNanos)
        assertEquals(AttackOutcome.BLOCKED, resolve(atContact, realGuardContact(requireNotNull(atContact.weaponGrip))))
    }

    @Test
    fun futureFastMotionCannotEraseTheEarlierValidFastGuardWitness() {
        val session = session()
        val from = guardFrame(0L, 0L)
        val to = guardFrame(220_000_000L, 0L).copy(fastGuardAtNanos = 220_000_000L)
        val witness = session.interpolateMotionFrame(from, to, 170.0 / 220.0, 170_000_000L)
        assertEquals(0L, witness.fastGuardAtNanos)
        assertEquals(AttackOutcome.PARRIED, resolve(witness, realGuardContact(requireNotNull(witness.weaponGrip))))
    }

    @Test
    fun activeIncomingHitPublishesTheInteriorGripBladeAndHeadWitness() {
        val session = session()
        val combat = activeCombat()
        set(session, "combat", combat)
        set(session, "result", TrialResult.FIGHTING)
        set(session, "trialStarted", true)
        set(session, "sceneAvailable", true)
        set(session, "enemyPosition", ENEMY)
        set(session, "enemySpawn", ENEMY)
        set(session, "playerHealth", 20) // Stop at this real incoming contact, before its remaining interval.

        val endEnemyPose = arenaOpponents.first().attackProfile(AttackDirection.OVERHEAD).sample(1.1).inStage(ENEMY, 0f)
        val targetHead = (endEnemyPose.bladeBase + endEnemyPose.bladeTip) * 0.5 + Vector3(0.0, 0.2, 0.0)
        val from = movingFrame(0L, WeaponGrip(Vector3(3.0, 1.0, 0.0), IDENTITY), targetHead + Vector3(-0.05, 0.0, 0.0))
        val to = movingFrame(200_000_000L, WeaponGrip(Vector3(3.35, 1.0, 0.0), IDENTITY), targetHead + Vector3(0.05, 0.0, 0.0))
        set(session, "simulationMotion", from)
        set(session, "latestMotion", from)
        val events = mutableListOf<EnemyCombatEvent>()
        val method = ArenaSession::class.java.getDeclaredMethod("advanceEnemy", java.lang.Long.TYPE,
            MutableList::class.java, java.lang.Long.TYPE, PlayerMotionFrame::class.java).apply { isAccessible = true }
        method.invoke(session, 200_000_000L, events, 0L, to)
        val impact = events.filterIsInstance<CombatImpact>().single { it.kind == CombatImpactKind.PLAYER_HIT }
        val witness = get(session, "simulationMotion") as PlayerMotionFrame
        val fraction = witness.receivedAtNanos.toDouble() / 200_000_000L
        assertTrue("The actual prepared blade must hit inside the input interval", fraction > 0.0 && fraction < 1.0)
        val expected = session.interpolateMotionFrame(from, to, fraction, witness.receivedAtNanos)
        assertTrue(expected.headPosition.distanceTo(witness.headPosition) < 1e-8)
        assertTrue(requireNotNull(expected.weaponGrip).position.distanceTo(requireNotNull(witness.weaponGrip).position) < 1e-8)
        assertTrue(expected.bladeBase.distanceTo(witness.bladeBase) < 1e-8)
        assertTrue(expected.bladeTip.distanceTo(witness.bladeTip) < 1e-8)
        assertNotEquals(to.weaponGrip, witness.weaponGrip)
        assertTrue(impact.appliedDamage == 0) // Player damage is represented by AttackResolved and player HP.
        var presented: ArenaViewState? = null
        session.setArenaPresenter { state, _ -> presented = state }
        val state = requireNotNull(presented)
        assertEquals(TrialResult.DEFEAT, state.result)
        assertEquals(0, state.playerHealth)
        assertEquals(witness.weaponGrip, state.playerWeaponGrip)
        assertEquals(witness.bladeBase, state.playerBladeBase)
        assertEquals(witness.bladeTip, state.playerBladeTip)
    }

    private fun resolve(frame: PlayerMotionFrame, contact: BladeContact): AttackOutcome {
        val resolver = PlayerCombatResolver()
        resolver.beginEnemyAttack(1L)
        resolver.constrainWeapon(frame, requireNotNull(frame.weaponGrip), contact)
        return resolver.resolveDefense(1L, AttackDirection.OVERHEAD, ENEMY, frame.receivedAtNanos, contact)
    }

    private fun realGuardContact(grip: WeaponGrip): BladeContact {
        val player = playerBlade(grip)
        val midpoint = (player.base + player.tip) * 0.5
        val enemy = BladeSegment(midpoint + Vector3(0.0, -0.2, 0.0), midpoint + Vector3(0.0, 0.2, 0.0), 0.0125)
        return requireNotNull(firstBladeContact(BladeSweep(player, player), BladeSweep(enemy, enemy)))
    }

    private fun guardFrame(receipt: Long, enteredAt: Long?): PlayerMotionFrame {
        val grip = WeaponGrip(Vector3(-0.4, 1.6, -0.35), Quaternion(0.0, -sqrt(0.5), 0.0, sqrt(0.5)))
        return movingFrame(receipt, grip, Vector3(0.0, 1.6, 0.0)).copy(guardDirection = AttackDirection.OVERHEAD,
            guardEnteredAtNanos = enteredAt, fastGuardAtNanos = enteredAt)
    }

    private fun movingFrame(receipt: Long, grip: WeaponGrip, head: Vector3): PlayerMotionFrame {
        val blade = playerBlade(grip)
        return PlayerMotionFrame(receipt, blade.base, blade.tip, 2.0, null, false, head,
            rawWeaponGrip = grip, weaponGrip = grip)
    }

    private fun activeCombat(): EnemyCombatStateMachine = EnemyCombatStateMachine().also {
        it.advanceBy(800_000_000L, true)
        it.tryStartAttack(AttackDirection.OVERHEAD, true)
        it.advanceBy(AttackDirection.OVERHEAD.preparationNanos + AttackDirection.OVERHEAD.startupNanos, true)
        assertEquals(EnemyPhase.ACTIVE, it.phase)
    }

    private fun session() = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error })
    private fun set(session: ArenaSession, name: String, value: Any) {
        ArenaSession::class.java.getDeclaredField(name).apply { isAccessible = true }.set(session, value)
    }
    private fun get(session: ArenaSession, name: String): Any? =
        ArenaSession::class.java.getDeclaredField(name).apply { isAccessible = true }.get(session)

    private companion object {
        val IDENTITY = Quaternion(0.0, 0.0, 0.0, 1.0)
        val ENEMY = Vector3(0.0, 0.0, -1.3)
    }
}
