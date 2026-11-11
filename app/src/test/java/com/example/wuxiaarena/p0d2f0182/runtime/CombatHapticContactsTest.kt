package com.example.wuxiaarena.p0d2f0182.runtime

import com.example.wuxiaarena.core.combat.CombatImpact
import com.example.wuxiaarena.core.combat.CombatImpactKind
import com.example.wuxiaarena.core.combat.PauseReason
import com.example.wuxiaarena.core.input.Hand
import com.example.wuxiaarena.core.input.InputOrigin
import com.example.wuxiaarena.core.math.Vector3
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CombatHapticContactsTest {
    @Test
    fun unorderedContactsAreConsumedOnceAndTheStrongestResultWinsEachHand() {
        val contacts = CombatHapticContacts()
        val parry = impact(2).copy(kind = CombatImpactKind.PARRY, strength = 0.8)
        val left = impact(1).copy(hand = Hand.LEFT)
        val cues = contacts.select(state, listOf(impact(4), parry, left, parry))
        assertEquals(2, cues.size)
        assertEquals(parry, cues.single { it.hand == Hand.RIGHT }.impact)
        assertEquals(left, cues.single { it.hand == Hand.LEFT }.impact)
        assertTrue(contacts.select(state, listOf(left, parry, impact(4))).isEmpty())
    }

    @Test
    fun aLowerIdInALaterBatchIsStillARealUnseenContact() {
        val contacts = CombatHapticContacts()
        contacts.select(state, listOf(impact(5)))
        assertEquals(2L, contacts.select(state, listOf(impact(2))).single().impact.id)
    }

    @Test
    fun fatalAndExecutionHavePriorityAndExecutionAffectsBothHands() {
        val contacts = CombatHapticContacts()
        val execution = impact(1).copy(kind = CombatImpactKind.EXECUTION, appliedDamage = 5, fatal = true)
        val parry = impact(2).copy(kind = CombatImpactKind.PARRY)
        val cues = contacts.select(state, listOf(execution, parry))
        assertEquals(setOf(Hand.LEFT, Hand.RIGHT), cues.map { it.hand }.toSet())
        assertTrue(cues.all { it.impact == execution })
    }

    @Test
    fun pauseConsumesEventsAndResumeCannotReplayThem() {
        val contacts = CombatHapticContacts()
        assertTrue(contacts.select(state.copy(pauseReason = PauseReason.USER), listOf(impact(1))).isEmpty())
        assertTrue(contacts.select(state, listOf(impact(1))).isEmpty())
        assertEquals(2L, contacts.select(state, listOf(impact(2))).single().impact.id)
    }

    @Test
    fun resettingAllowsNewRoundIdentityButStaleRoundsCannotReplay() {
        val contacts = CombatHapticContacts()
        contacts.select(state, listOf(impact(1)))
        assertEquals(1, contacts.select(state.copy(roundGeneration = 2), listOf(impact(1))).size)
        assertTrue(contacts.select(state, listOf(impact(2))).isEmpty())
    }

    @Test
    fun theLastPlayerHitSurvivesTerminalPauseButDesktopHasNoHardwarePulse() {
        val hurt = impact(1).copy(kind = CombatImpactKind.PLAYER_HIT)
        val terminal = state.copy(result = TrialResult.DEFEAT, pauseReason = PauseReason.USER)
        assertEquals(hurt, CombatHapticContacts().select(terminal, listOf(hurt)).single().impact)
        assertTrue(CombatHapticContacts().select(state.copy(inputOrigin = InputOrigin.DESKTOP), listOf(hurt)).isEmpty())
    }

    private val state = ArenaSession(logMessage = {}, logFailure = { _, error -> throw error }).viewState.copy(
        roundGeneration = 1, inputOrigin = InputOrigin.PICO, sceneReady = true, inputReady = true,
        result = TrialResult.FIGHTING, pauseReason = null,
    )

    private fun impact(id: Long) = CombatImpact(
        id, CombatImpactKind.SOFT_HIT, Vector3(0.0, 1.0, -1.0),
        Vector3(0.0, 0.0, 1.0), 0.9, Hand.RIGHT, 0L,
    )
}
